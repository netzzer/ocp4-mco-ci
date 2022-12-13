import logging
import os
from shutil import which

from kubernetes import config

from src.utility.utils import get_openshift_client
from src.utility.cmd import exec_cmd
from src.utility.exceptions  import CommandFailed


log = logging.getLogger(__name__)

class OpenshiftOps(object):
    """
    Class which contains various utility functions for interacting
    with OpenShift
    """

    def __init__(self):
        k8s_client = config.new_client_from_config()

    @staticmethod
    def set_kubeconfig(kubeconfig_path):
        """
        Export environment variable KUBECONFIG for future calls of OC commands
        or other API calls
        Args:
            kubeconfig_path (str): path to kubeconfig file to be exported
        Returns:
            boolean: True if successfully connected to cluster, False otherwise
        """
        # Test cluster access
        log.info("Testing access to cluster with %s", kubeconfig_path)
        if not os.path.isfile(kubeconfig_path):
            log.warning("The kubeconfig file %s doesn't exist!", kubeconfig_path)
            return False
        os.environ["KUBECONFIG"] = kubeconfig_path
        if not which("oc"):
            get_openshift_client()
        try:
            exec_cmd("oc cluster-info")
        except CommandFailed as ex:
            log.error("Cluster is not ready to use: %s", ex)
            return False
        log.info("Access to cluster is OK!")
        return True