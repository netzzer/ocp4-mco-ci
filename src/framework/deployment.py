import logging
import sys
import multiprocessing as mp

from src.deployment.ocp import OCPDeployment
from src.deployment.ocs import OCSDeployment
from src.deployment.mco import MCODeployment
from src.deployment.acm import ACMDeployment
from src.deployment.submariner import Submariner
from src.deployment.import_managed_cluster import ImportManagedCluster
from src import framework
from src.framework.logger_factory import set_log_record_factory
from src.utility.constants import LOG_FORMAT
from src.utility.utils import (is_cluster_running, email_reports, get_non_acm_cluster_config)

log = logging.getLogger(__name__)
current_factory = logging.getLogRecordFactory()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(LOG_FORMAT))
log.addHandler(handler)

def set_log_level(log_cli_level):
    """
            Set the log level of this module based on the pytest.ini log_cli_level
            Args:
                config (pytest.config): Pytest config object
            """
    level = log_cli_level or "INFO"
    log.setLevel(logging.getLevelName(level))

class Deployment(object):
    def __init__(self):
        set_log_record_factory()
        set_log_level(framework.config.RUN['log_level'])

    def deploy_ocp(self, log_cli_level):
        # OCP Deployment
        processes = []
        for i in range(framework.config.nclusters):
            try:
                framework.config.switch_ctx(i)
                cluster_path = framework.config.ENV_DATA["cluster_path"]
                cluster_name = framework.config.ENV_DATA["cluster_name"]
                if not framework.config.ENV_DATA.get("skip_ocp_deployment", True):
                    if is_cluster_running(cluster_path):
                        log.warning("OCP cluster is already running, skipping installation")
                    else:
                        log.info(f'Deploying OCP cluster for {cluster_name}')
                        ocp_deployment = OCPDeployment(cluster_name, cluster_path)
                        ocp_deployment.deploy_prereq()
                        p = mp.Process(
                            target=OCPDeployment.deploy_ocp,
                            args=(ocp_deployment.installer_binary_path, ocp_deployment.cluster_path, log_cli_level,)
                        )
                        processes.append(p)
                else:
                    log.warning("OCP deployment will be skipped")
            except Exception:
                log.error("Unable to deploy OCP cluster !")
        framework.config.switch_default_cluster_ctx()
        if len(processes) > 0:
            [proc.start() for proc in processes]
            # complete the processes
            for proc in processes:
                proc.join()

    def deploy_ocs(self, log_cli_level):
        # OCS Deployment
        processes = []
        for i in range(framework.config.nclusters):
            try:
                framework.config.switch_ctx(i)
                if not framework.config.ENV_DATA["skip_ocs_deployment"]:
                    if framework.config.multicluster and framework.config.get_acm_index() == i and not framework.config.MULTICLUSTER["primary_cluster"]:
                        continue
                    log.info(f'Deploying OCS Operator on {framework.config.ENV_DATA["cluster_name"]}')
                    ocs_deployment = OCSDeployment()
                    ocs_deployment.deploy_prereq()
                    log.info(f'Deploying OCS cluster on {framework.config.ENV_DATA["cluster_name"]}')
                    p = mp.Process(
                        target=OCSDeployment.deploy_ocs,
                        args=(framework.config.RUN["kubeconfig_location"], framework.config.ENV_DATA['skip_ocs_cluster_creation'],)
                    )
                    processes.append(p)
                else:
                    log.warning("OCS deployment will be skipped")
            except Exception as ex:
                log.error("Unable to deploy OCS cluster", ex)
        framework.config.switch_default_cluster_ctx()
        if len(processes) > 0:
            [proc.start() for proc in processes]
            # complete the processes
            for proc in processes:
                proc.join()

    def deploy_mco(self):
        # MCO Deployment
        for i in range(framework.config.nclusters):
            try:
                framework.config.switch_ctx(i)
                if framework.config.multicluster and framework.config.get_acm_index() == i:
                    if not framework.config.MULTICLUSTER["skip_mco_deployment"]:
                        log.info(f'Deploying MCO Operator on {framework.config.ENV_DATA["cluster_name"]}')
                        mco_deployment = MCODeployment()
                        mco_deployment.deploy_prereq()
                        MCODeployment.deploy_mco()
                    else:
                        log.warning("MCO deployment will be skipped")
            except Exception as ex:
                log.error("Unable to deploy MCO operator", ex)
        framework.config.switch_default_cluster_ctx()

    def deploy_acm(self):
        # ACM Deployment
        for i in range(framework.config.nclusters):
            try:
                framework.config.switch_ctx(i)
                if framework.config.multicluster and framework.config.get_acm_index() == i:
                    if framework.config.MULTICLUSTER["deploy_acm_hub_cluster"]:
                        log.info(f'Deploying ACM Operator on {framework.config.ENV_DATA["cluster_name"]}')
                        acm_deployment = ACMDeployment()
                        acm_deployment.deploy_acm_hub_unreleased()
                    else:
                        log.warning("ACM deployment will be skipped")
            except Exception as ex:
                log.error("Unable to deploy ACM hub operator", ex)
        framework.config.switch_default_cluster_ctx()

    def configure_submariner(self):
        try:
            for i in range(framework.config.nclusters):
                framework.config.switch_ctx(i)
                if framework.config.multicluster and framework.config.get_acm_index() == i:
                    if framework.config.MULTICLUSTER["configure_submariner"]:
                        log.info("Configuring submariner")
                        submariner = Submariner()
                        submariner.deploy()
                    else:
                        log.warning("Submariner configuration will be skipped")
        except Exception as ex:
            log.error("Unable to configure submariner", ex)

    def aws_import_cluster(self):
        try:
            for i in range(framework.config.nclusters):
                framework.config.switch_ctx(i)
                if framework.config.multicluster and framework.config.get_acm_index() == i:
                    for cluster in get_non_acm_cluster_config():
                        if cluster.MULTICLUSTER['import_as_managed_cluster']:
                            log.info(f"Importing cluster {cluster.ENV_DATA['cluster_name']} into ACM")
                            import_managed_cluster = ImportManagedCluster(cluster.ENV_DATA['cluster_name'], cluster.ENV_DATA['cluster_path'])
                            import_managed_cluster.import_cluster()
                        else:
                            log.warning(f"Skipping managed cluster import for {cluster.ENV_DATA['cluster_name']}")
        except Exception as ex:
            log.error("Unable to import cluster", ex)


    def send_email(self):
        # send email notification
        for i in range(framework.config.nclusters):
            framework.config.switch_ctx(i)
            skip_notification = framework.config.REPORTING['email']['skip_notification']
            if not skip_notification:
                email_reports()
            else:
                log.warning("Email notification will be skipped")
        framework.config.switch_default_cluster_ctx()
