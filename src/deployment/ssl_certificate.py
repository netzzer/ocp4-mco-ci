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
        self.ssl_certificate = ''
        self.ssl_certificate_path = ''

    def get_certificate(self):
        certificate_path =  f"{constants.EXTERNAL_DIR}/certificate.crt"
        exec_cmd("oc get cm default-ingress-cert -n openshift-config-managed -o jsonpath=\"{['data']['ca-bundle\.crt']}\" > " + certificate_path)
        with open(certificate_path, "r") as f:
            ssl_cert = f.read()
            self.ssl_certificate += ssl_cert

    def get_certificate_file_path(self):
        cert_file = tempfile.NamedTemporaryFile(
            mode="w+", prefix="ssl_cert", delete=False
        )
        ssl_certificate = yaml.load(constants.SSL_CERTIFICATE_YAML,  Loader=SafeLoader)
        ssl_certificate['data']['ca-bundle.crt'] = self.ssl_certificate
        templating.dump_data_to_temp_yaml(ssl_certificate, cert_file.name)
        self.ssl_certificate_path = cert_file.name

    def exchange_certificate(self):
        exec_cmd(f"oc create -f {self.ssl_certificate_path}")
        exec_cmd("oc patch proxy cluster --type=merge  --patch='{\"spec\":{\"trustedCA\":{\"name\":\"user-ca-bundle\"}}}'")
