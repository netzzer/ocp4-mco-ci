import os
import logging
import tempfile

from src.framework import config
from src.utility.cmd import exec_cmd
from src.utility import (constants, templating)
from src.ocs.resources.catalog_source import disable_specific_source
from src.ocs.resources.catalog_source import CatalogSource
from src.utility.utils import (
    get_kube_config_path,
    create_directory_path,
    wait_for_machineconfigpool_status
)
from src.utility.timeout import TimeoutSampler
from src.utility.exceptions import CommandFailed
from src.ocs import ocp

logger = logging.getLogger(__name__)

def get_and_apply_icsp_from_catalog(apply=True):
    """
    Args:
        apply (bool): controls if the ICSP should be applied or not
            (default: true)
    """
    if apply:
        exec_cmd(f"oc apply -f {constants.ODF_ICSP_YAML}")
        wait_for_machineconfigpool_status("all")

class OperatorDeployment(object):
    def __init__(self, namespace):
        self.namespace = namespace
    def create_catalog_source(self, image=None):
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
        image = image or config.ENV_DATA.get("ocs_registry_image", "")
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
        # apply icsp
        get_and_apply_icsp_from_catalog()
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
        Wait for th e CSV to appear
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

    def enable_console_plugin(self, name, enable_console=True):
        """
        Enables console plugin for ODF
        """
        if enable_console:
            try:
                logger.info("Enabling console plugin")
                ocp_obj = ocp.OCP()
                patch = '\'[{"op": "add", "path": "/spec/plugins/-", "value": "$name"}]\''
                patch = patch.replace("$name", name)
                patch_cmd = (
                    f"patch console.operator cluster -n {self.namespace}"
                    f" --type json -p {patch}"
                )
                ocp_obj.exec_oc_cmd(command=patch_cmd)
            except CommandFailed:
                patch = '\'[{"op": "add", "path": "/spec/plugins", "value": ["$name"]}]\''
                patch = patch.replace("$name", name)
                patch_cmd = (
                    f"patch console.operator cluster -n {self.namespace}"
                    f" --type json -p {patch}"
                )
                ocp_obj.exec_oc_cmd(command=patch_cmd)
        else:
            logger.debug(f"Skipping console plugin for {name} operator ")