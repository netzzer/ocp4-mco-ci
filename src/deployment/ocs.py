import logging
import tempfile
import time

from src.framework import config
from src.ocs.resources.catalog_source import disable_specific_source
from src.utility import (constants, templating, version, defaults)
from src.utility.cmd import exec_cmd
from src.ocs.resources.catalog_source import CatalogSource
from src.ocs.resources.package_manifest import PackageManifest
from src.ocs.resources.package_manifest import get_selector_for_ocs_operator
from src.utility.utils import get_kube_config_path
from src.utility.timeout import TimeoutSampler
from src.ocs import ocp

logger = logging.getLogger(__name__)

class OCSDeployment:
    def __init__(self):
        self.namespace = config.ENV_DATA["cluster_namespace"]

    def deploy_prereq(self):
        # create OCS catalog source
        self.create_catalog_source()
        # deploy ocs operator
        self.ocs_subscription()
        # enable odf-console plugin
        self.enable_console_plugin()

    def create_catalog_source(ignore_upgrade=False):
        """
        This prepare catalog source manifest for deploy OCS operator from
        quay registry.
        Args:
            image (str): Image of ocs registry.
            ignore_upgrade (bool): Ignore upgrade parameter.
        """
        # Because custom catalog source will be called: redhat-operators, we need to disable
        # default sources. This should not be an issue as OCS internal registry images
        # are now based on OCP registry image
        disable_specific_source(
            constants.OPERATOR_CATALOG_SOURCE_NAME,
            get_kube_config_path(config.ENV_DATA["cluster_path"])
        )
        logger.info("Adding CatalogSource")
        image = config.ENV_DATA.get("ocs_registry_image", "")
        if not ignore_upgrade:
            upgrade = config.UPGRADE.get("upgrade", False)
        else:
            upgrade = False
        image_and_tag = image.rsplit(":", 1)
        image = image_and_tag[0]
        image_tag = image_and_tag[1] if len(image_and_tag) == 2 else None
        catalog_source_data = templating.load_yaml(constants.CATALOG_SOURCE_YAML)
        cs_name = constants.OPERATOR_CATALOG_SOURCE_NAME
        change_cs_condition = (
                (image or image_tag)
                and catalog_source_data["kind"] == "CatalogSource"
                and catalog_source_data["metadata"]["name"] == cs_name
        )
        if change_cs_condition:
            default_image = config.ENV_DATA["default_ocs_registry_image"]
            image = image if image else default_image.rsplit(":", 1)[0]
            catalog_source_data["spec"][
                "image"
            ] = f"{image}:{image_tag if image_tag else 'latest'}"
        catalog_source_manifest = tempfile.NamedTemporaryFile(
            mode="w+", prefix="catalog_source_manifest", delete=False
        )
        templating.dump_data_to_temp_yaml(catalog_source_data, catalog_source_manifest.name)
        exec_cmd(f"oc apply -f {catalog_source_manifest.name}", timeout=2400)
        catalog_source = CatalogSource(
            resource_name=constants.OPERATOR_CATALOG_SOURCE_NAME,
            namespace=constants.MARKETPLACE_NAMESPACE,
        )
        # Wait for catalog source is ready
        catalog_source.wait_for_state("READY")

    def wait_for_subscription(self, subscription_name):
        """
        Wait for the subscription to appear
        Args:
            subscription_name (str): Subscription name pattern
        """

        resource_kind = constants.SUBSCRIPTION
        ocp.OCP(kind=resource_kind, namespace=self.namespace)
        for sample in TimeoutSampler(
                300, 10, ocp.OCP, kind=resource_kind, namespace=self.namespace
        ):
            subscriptions = sample.get().get("items", [])
            for subscription in subscriptions:
                found_subscription_name = subscription.get("metadata", {}).get(
                    "name", ""
                )
                if subscription_name in found_subscription_name:
                    logger.info(f"Subscription found: {found_subscription_name}")
                    return
                logger.debug(f"Still waiting for the subscription: {subscription_name}")

    def wait_for_csv(self, csv_name):
        """
        Wait for the CSV to appear
        Args:
            csv_name (str): CSV name pattern
        """
        ocp.OCP(kind="subscription", namespace=self.namespace)
        for sample in TimeoutSampler(
                300, 10, ocp.OCP, kind="csv", namespace=self.namespace
        ):
            csvs = sample.get().get("items", [])
            for csv in csvs:
                found_csv_name = csv.get("metadata", {}).get("name", "")
                if csv_name in found_csv_name:
                    logger.info(f"CSV found: {found_csv_name}")
                    return
                logger.debug(f"Still waiting for the CSV: {csv_name}")

    def enable_console_plugin(self):
        """
        Enables console plugin for ODF
        """
        ocs_version = version.get_semantic_ocs_version_from_config()
        if (
                ocs_version >= version.VERSION_4_9
                and config.ENV_DATA["enable_console_plugin"]
        ):
            logger.info("Enabling console plugin")
            ocp_obj = ocp.OCP()
            patch = '\'[{"op": "add", "path": "/spec/plugins", "value": ["odf-console"]}]\''
            patch_cmd = (
                f"patch console.operator cluster -n {constants.OPENSHIFT_STORAGE_NAMESPACE}"
                f" --type json -p {patch}"
            )
            ocp_obj.exec_oc_cmd(command=patch_cmd)

    def ocs_subscription(self):
        logger.info("Creating namespace and operator group.")
        exec_cmd(f"oc apply -f {constants.OLM_YAML}")
        operator_selector = get_selector_for_ocs_operator()
        # For OCS version >= 4.9, we have odf-operator
        ocs_version = version.get_semantic_ocs_version_from_config()
        if ocs_version >= version.VERSION_4_9:
            ocs_operator_name = defaults.ODF_OPERATOR_NAME
            subscription_file = constants.SUBSCRIPTION_ODF_YAML
        else:
            ocs_operator_name = defaults.OCS_OPERATOR_NAME
            subscription_file = constants.SUBSCRIPTION_YAML
        package_manifest = PackageManifest(
            resource_name=ocs_operator_name,
            selector=operator_selector,
        )
        # Wait for package manifest is ready
        package_manifest.wait_for_resource(timeout=300)
        default_channel = package_manifest.get_default_channel()
        subscription_yaml_data = templating.load_yaml(subscription_file)
        custom_channel = config.DEPLOYMENT.get("ocs_csv_channel")
        if custom_channel:
            logger.info(f"Custom channel will be used: {custom_channel}")
            subscription_yaml_data["spec"]["channel"] = custom_channel
        else:
            logger.info(f"Default channel will be used: {default_channel}")
            subscription_yaml_data["spec"]["channel"] = default_channel
        if config.DEPLOYMENT.get("stage"):
            subscription_yaml_data["spec"]["source"] = constants.OPERATOR_SOURCE_NAME
        subscription_manifest = tempfile.NamedTemporaryFile(
            mode="w+", prefix="subscription_manifest", delete=False
        )
        templating.dump_data_to_temp_yaml(
            subscription_yaml_data, subscription_manifest.name
        )
        exec_cmd(f"oc apply -f {subscription_manifest.name}")
        self.wait_for_subscription(ocs_operator_name)
        self.wait_for_csv(ocs_operator_name)
        logger.info("Sleeping for 30 seconds after CSV created")
        time.sleep(30)

    def create_config(self):
        pass

    @staticmethod
    def deploy_ocs(log_cli_level="INFO"):
        pass
