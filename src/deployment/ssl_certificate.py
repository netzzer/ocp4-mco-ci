import tempfile
import logging
import yaml
from yaml.loader import SafeLoader
from src.utility.cmd import exec_cmd
from src.utility import templating
from src.utility import constants

logger = logging.getLogger(__name__)


class SSLCertificate(object):
    def __init__(self):
        self.ssl_certificate = ""
        self.ssl_certificate_path = ""

    def get_certificate(self):
        result = exec_cmd(
            "oc get cm default-ingress-cert -n openshift-config-managed -o jsonpath=\"{['data']['ca-bundle\.crt']}\""
        )
        self.ssl_certificate += result.stdout.decode("utf-8")

    def get_certificate_file_path(self):
        cert_file = tempfile.NamedTemporaryFile(
            mode="w+", prefix="ssl_cert", delete=False
        )
        f = open(constants.SSL_CERTIFICATE_YAML, "r")
        ssl_certificate = yaml.load(f, Loader=SafeLoader)
        ssl_certificate["data"]["ca-bundle.crt"] = self.ssl_certificate
        templating.dump_data_to_temp_yaml(ssl_certificate, cert_file.name)
        self.ssl_certificate_path = cert_file.name

    def exchange_certificate(self):
        exec_cmd(f"oc create -f {self.ssl_certificate_path}")
        exec_cmd(
            'oc patch proxy cluster --type=merge  --patch=\'{"spec":{"trustedCA":{"name":"user-ca-bundle"}}}\''
        )
