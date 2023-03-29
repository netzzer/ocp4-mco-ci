import logging
import argparse
import os
import multiprocessing as mp

from src.utility.constants import BASIC_FORMAT
from src.framework import config
from src.utility import utils
from src.utility.exceptions  import CommandFailed
from src.deployment.submariner  import remove_aws_policy

logging.basicConfig(format=BASIC_FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)


def destroy_ocp(installer_binary_path, cluster_name, cluster_path, log_cli_level="INFO"):
    try:
        remove_aws_policy(cluster_name)
        utils.exec_cmd(
            cmd="{bin_dir} destroy cluster --dir {cluster_dir} --log-level={log_level}".format(
                bin_dir=installer_binary_path,
                cluster_dir=cluster_path,
                log_level=log_cli_level
            ),
            timeout=3600,
        )
    except CommandFailed as ex:
        logger.error("Unable to destroy ocp cluster.")

def cluster_cleanup():
    parser = argparse.ArgumentParser(description="Cleanup AWS Resource")
    parser.add_argument(
        "--cluster-name", required=True, help="cluster name to destroy"
    )
    parser.add_argument(
        "--cluster-path", required=True, help="cluster install directory path"
    )
    args, _ = parser.parse_known_args()
    cluster_name = args.cluster_name
    cluster_path = args.cluster_path
    bin_dir = os.path.expanduser(config.RUN["bin_dir"])
    oc_bin = os.path.join(bin_dir, "openshift-install")
    destroy_ocp(oc_bin, cluster_name, cluster_path)


