import logging
import argparse
import os
import multiprocessing as mp

from src.utility.constants import BASIC_FORMAT
from src.framework import config
from src.utility import utils
from src.utility.exceptions import CommandFailed
from src.deployment.submariner import remove_aws_policy

logging.basicConfig(format=BASIC_FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)


def destroy_ocp(
    installer_binary_path, cluster_path, log_cli_level="INFO", is_managed_cluster=False
):
    try:
        cluster_name = utils.get_cluster_metadata(cluster_path)['clusterName']
        if is_managed_cluster:
            remove_aws_policy(cluster_name)
        utils.exec_cmd(
            cmd="{bin_dir} destroy cluster --dir {cluster_dir} --log-level={log_level}".format(
                bin_dir=installer_binary_path,
                cluster_dir=cluster_path,
                log_level=log_cli_level,
            ),
            timeout=3600,
        )
    except CommandFailed as ex:
        logger.error("Unable to destroy ocp cluster.")


def cluster_cleanup():
    parser = argparse.ArgumentParser(description="Cleanup AWS Resource")
    parser.add_argument(
        "--is-managed-cluster", required=False, help="whether the cluster is managed by ACM or not"
    )
    parser.add_argument(
        "--cluster-paths", nargs='+', required=True, help="cluster install directory paths with space"
    )
    args, _ = parser.parse_known_args()
    cluster_paths = args.cluster_paths
    is_managed_cluster = args.is_managed_cluster
    bin_dir = os.path.expanduser(config.RUN["bin_dir"])
    oc_bin = os.path.join(bin_dir, "openshift-install")
    processes = []
    for cluster_path in cluster_paths:
        p = mp.Process(
            target=destroy_ocp,
            args=(oc_bin, cluster_path, is_managed_cluster)
        )
        processes.append(p)
    if len(processes) > 0:
        [proc.start() for proc in processes]
        # complete the processes
        for proc in processes:
            proc.join()