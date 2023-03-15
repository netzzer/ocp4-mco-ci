import logging
import os
import tempfile

import yaml

from src.utility import templating
from src.utility.utils import (get_kube_config, exec_cmd)

logger = logging.getLogger(__name__)

class ImportManagedCluster(object):
    """
        Import as managed cluster for ACM
    """

    def __init__(self, cluster_name, cluster_path):
        self.cluster_name = cluster_name
        self.cluster_path = cluster_path

    def import_cluster(self):
        logger.info("Generating import-yaml")
        _templating = templating.Templating()
        aws_import_cluster_path = os.path.join("aws-import-cluster.yaml.j2")
        import_cluster_str = _templating.render_template(
            aws_import_cluster_path, {
                "cluster_name": self.cluster_name,
            }
        )
        import_cluster_obj = list(yaml.load_all(import_cluster_str, yaml.FullLoader))
        import_cluster_obj[1]["stringData"]["kubeconfig"] = get_kube_config(self.cluster_path)
        import_cluster_temp = tempfile.NamedTemporaryFile(
            mode="w+", prefix="aws_import_cluster", delete=False
        )
        templating.dump_data_to_temp_yaml(import_cluster_obj, import_cluster_temp.name)
        exec_cmd(f"oc apply -f {import_cluster_temp.name}", timeout=2400)