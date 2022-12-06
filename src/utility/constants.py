import os

# Directories
TOP_DIR = os.path.abspath('.')
TEMPLATE_DIR = os.path.join(TOP_DIR, "src", "templates")
LOG_FORMAT = "%(asctime)s - %(threadName)s - %(name)s - %(levelname)s %(clusterctx)s - %(message)s"
