import os

# Directories
TOP_DIR = os.path.abspath('.')
TEMPLATE_DIR = os.path.join(TOP_DIR, "src", "templates")
CATALOG_SOURCE_YAML = os.path.join(TEMPLATE_DIR, "catalog-source.yaml")
EMAIL_NOTIFICATION_HTML = os.path.join(TEMPLATE_DIR, "result-email-template.html")
LOG_FORMAT = "%(asctime)s - %(threadName)s - %(name)s - %(levelname)s %(clusterctx)s - %(message)s"
BASIC_FORMAT = "%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s"
OPERATOR_CATALOG_SOURCE_NAME = "redhat-operators"
PATCH_SPECIFIC_SOURCES_CMD = (
    "oc patch operatorhub.config.openshift.io/cluster -p="
    '\'{{"spec":{{"sources":[{{"disabled":{disable},"name":"{source_name}"'
    "}}]}}}}' --type=merge"
)
CATALOG_SOURCE_YAML = os.path.join(TEMPLATE_DIR, "catalog-source.yaml")
MARKETPLACE_NAMESPACE = "openshift-marketplace"
