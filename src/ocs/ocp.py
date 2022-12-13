import logging
import os
import yaml
import time

from src.framework import config
from src.utility.exceptions  import (
    ResourceNameNotSpecifiedException,
    CommandFailed
)
from src.utility.cmd import exec_cmd

log = logging.getLogger(__name__)


class OCP(object):
    """
    A basic OCP object to run basic 'oc' commands
    """
    def __init__(
            self,
            api_version="v1",
            kind="Service",
            namespace=None,
            resource_name="",
            selector=None,
            field_selector=None,
            cluster_kubeconfig="",
            threading_lock=None,
            silent=False,
    ):
        """
        Initializer function
        Args:
            api_version (str): TBD
            kind (str): TBD
            namespace (str): The name of the namespace to use
            resource_name (str): Resource name
            selector (str): The label selector to look for. It has higher
                priority than resource_name and is used instead of the name.
            field_selector (str): Selector (field query) to filter on, supports
                '=', '==', and '!='. (e.g. status.phase=Running)
            cluster_kubeconfig (str): Path to the cluster kubeconfig file. Useful in a multicluster configuration
            threading_lock (threading.Lock): threading.Lock object that is used
                for handling concurrent oc commands
            silent (bool): If True will silent errors from the server, default false
        """
        self._api_version = api_version
        self._kind = kind
        self._namespace = namespace
        self._resource_name = resource_name
        self._data = {}
        self.selector = selector
        self.field_selector = field_selector
        self.cluster_kubeconfig = cluster_kubeconfig
        self.threading_lock = threading_lock
        self.silent = silent

    @property
    def api_version(self):
        return self._api_version

    @property
    def kind(self):
        return self._kind

    @property
    def namespace(self):
        return self._namespace

    @property
    def resource_name(self):
        return self._resource_name

    @property
    def data(self, silent=False):
        if self._data:
            return self._data
        if self.silent:
            silent = True
        self._data = self.get(silent=silent)
        return self._data


    def check_name_is_specified(self, resource_name=""):
        """
        Check if the name of the resource is specified in class level and
        if not raise the exception.
        Raises:
            ResourceNameNotSpecifiedException: in case the name is not
                specified.
        """
        resource_name = resource_name if resource_name else self.resource_name
        if not resource_name:
            raise ResourceNameNotSpecifiedException(
                "Resource name has to be specified in class!"
            )

    def get(
            self,
            resource_name="",
            out_yaml_format=True,
            selector=None,
            all_namespaces=False,
            retry=0,
            wait=3,
            dont_raise=False,
            silent=False,
            field_selector=None,
    ):
        """
        Get command - 'oc get <resource>'
        Args:
            resource_name (str): The resource name to fetch
            out_yaml_format (bool): Adding '-o yaml' to oc command
            selector (str): The label selector to look for.
            all_namespaces (bool): Equal to oc get <resource> -A
            retry (int): Number of attempts to retry to get resource
            wait (int): Number of seconds to wait between attempts for retry
            dont_raise (bool): If True will raise when get is not found
            field_selector (str): Selector (field query) to filter on, supports
                '=', '==', and '!='. (e.g. status.phase=Running)
        Example:
            get('my-pv1')
        Returns:
            dict: Dictionary represents a returned yaml file
            None: Incase dont_raise is True and get is not found
        """
        resource_name = resource_name if resource_name else self.resource_name
        selector = selector if selector else self.selector
        field_selector = field_selector if field_selector else self.field_selector
        if selector or field_selector:
            resource_name = ""
        command = f"get {self.kind} {resource_name}"
        if all_namespaces and not self.namespace:
            command += " -A"
        elif self.namespace:
            command += f" -n {self.namespace}"
        if selector is not None:
            command += f" --selector={selector}"
        if field_selector is not None:
            command += f" --field-selector={field_selector}"
        if out_yaml_format:
            command += " -o yaml"
        retry += 1
        while retry:
            try:
                return self.exec_oc_cmd(command, silent=silent)
            except CommandFailed as ex:
                if not silent:
                    log.warning(
                        f"Failed to get resource: {resource_name} of kind: "
                        f"{self.kind}, selector: {selector}, Error: {ex}"
                    )
                retry -= 1
                if not retry:
                    if not silent:
                        log.warning("Number of attempts to get resource reached!")
                    if not dont_raise:
                        raise
                    else:
                        return None
                else:
                    log.info(
                        f"Number of attempts: {retry} to get resource: "
                        f"{resource_name}, selector: {selector}, remain! "
                        f"Trying again in {wait} sec."
                    )
                    time.sleep(wait if wait else 1)

    def exec_oc_cmd(
            self,
            command,
            out_yaml_format=True,
            timeout=600,
            ignore_error=False,
            silent=False,
            **kwargs,
    ):
        """
        Executing 'oc' command
        Args:
            command (str): The command to execute (e.g. create -f file.yaml)
                without the initial 'oc' at the beginning
            out_yaml_format (bool): whether to return  yaml loaded python
                object or raw output
            secrets (list): A list of secrets to be masked with asterisks
                This kwarg is popped in order to not interfere with
                subprocess.run(``**kwargs``)
            timeout (int): timeout for the oc_cmd, defaults to 600 seconds
            ignore_error (bool): True if ignore non zero return code and do not
                raise the exception.
            silent (bool): If True will silent errors from the server, default false
        Returns:
            dict: Dictionary represents a returned yaml file.
            str: If out_yaml_format is False.
        """
        oc_cmd = "oc "
        env_kubeconfig = os.getenv("KUBECONFIG")
        kubeconfig_path = (
            self.cluster_kubeconfig if os.path.exists(self.cluster_kubeconfig) else None
        )

        if kubeconfig_path or not env_kubeconfig or not os.path.exists(env_kubeconfig):
            cluster_dir_kubeconfig = kubeconfig_path or os.path.join(
                config.ENV_DATA["cluster_path"], config.RUN.get("kubeconfig_location")
            )
            if os.path.exists(cluster_dir_kubeconfig):
                oc_cmd += f"--kubeconfig {cluster_dir_kubeconfig} "

        if self.namespace:
            oc_cmd += f"-n {self.namespace} "

        oc_cmd += command
        out = exec_cmd(
            cmd=oc_cmd,
            timeout=timeout,
            ignore_error=ignore_error,
            threading_lock=self.threading_lock,
            silent=silent,
            **kwargs,
        )
        if out_yaml_format:
            return yaml.safe_load(out.stdout)
        return out
