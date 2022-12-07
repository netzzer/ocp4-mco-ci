import logging
import argparse
import os
import multiprocessing as mp

from src.utility.constants import BASIC_FORMAT
from src.framework import config
from src.utility import utils
from src.exceptions.cmd_exceptions import CommandFailed

logging.basicConfig(format=BASIC_FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)


def destroy_ocp(installer_binary_path, cluster_path, log_cli_level="INFO"):
    # Do not access framework.config directly inside deploy_ocp, it is not thread safe
    try:
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
        "--cluster-paths", nargs='+', required=True, help="cluster install directory paths with space"
    )
    args = parser.parse_args()
    processes = []
    for cluster_path in args.cluster_paths:
        bin_dir = os.path.expanduser(config.RUN["bin_dir"])
        oc_bin = os.path.join(bin_dir, "openshift-install")
        p = mp.Process(
            target=destroy_ocp,
            args=(oc_bin, cluster_path)
        )
        processes.append(p)
    if len(processes) > 0:
        [proc.start() for proc in processes]
        # complete the processes
        for proc in processes:
            proc.join()


