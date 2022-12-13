import logging
import tempfile

from src.framework import config
from src.ocs.resources.catalog_source import disable_specific_source
from src.utility import constants
from src.utility import templating
from src.utility.cmd import exec_cmd
from src.ocs.resources.catalog_source import CatalogSource
from src.utility.utils import get_kube_config_path

logger = logging.getLogger(__name__)

class OCSDeployment():
    def __init__(self):
        pass

    def deploy_prereq(self):
        # create OCS catalog source
        self.create_catalog_source()

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

    def ocs_subscription(self):
        pass

    def create_config(self):
        pass

    @staticmethod
    def deploy_ocs(log_cli_level="INFO"):
        pass
