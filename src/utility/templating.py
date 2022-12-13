import yaml
import logging
import yaml

from jinja2 import Environment, FileSystemLoader

from src.utility.constants import TEMPLATE_DIR
from src.utility.utils import get_url_content

logger = logging.getLogger(__name__)

def to_nice_yaml(a, indent=2, *args, **kw):
    """
    This is a j2 filter which allows you from dictionary to print nice human
    readable yaml.
    Args:
        a (dict): dictionary with data to print as yaml
        indent (int): number of spaces for indent to be applied for whole
            dumped yaml. First line is not indented! (default: 2)
        *args: Other positional arguments which will be passed to yaml.dump
        *args: Other keywords arguments which will be passed to yaml.dump
    Returns:
        str: transformed yaml data in string format
    """
    transformed = yaml.dump(
        a,
        Dumper=yaml.Dumper,
        indent=indent,
        allow_unicode=True,
        default_flow_style=False,
        **kw,
    )
    return

def load_yaml(file, multi_document=False):
    """
    Load yaml file (local or from URL) and convert it to dictionary
    Args:
        file (str): Path to the file or URL address
        multi_document (bool): True if yaml contains more documents
    Returns:
        dict: If multi_document == False, returns loaded data from yaml file
            with one document.
        generator: If multi_document == True, returns generator which each
            iteration returns dict from one loaded document from a file.
    """
    loader = yaml.safe_load_all if multi_document else yaml.safe_load
    if file.startswith("http"):
        return loader(get_url_content(file))
    else:
        with open(file, "r") as fs:
            return loader(fs.read())

def dump_data_to_temp_yaml(data, temp_yaml):
    """
    Dump data to temporary yaml file
    Args:
        data (dict or list): dict or list (in case of multi_document) with
            data to dump to the yaml file.
        temp_yaml (str): file path of yaml file
    Returns:
        str: dumped yaml data
    """
    dumper = yaml.dump if isinstance(data, dict) else yaml.dump_all
    yaml_data = dumper(data)
    with open(temp_yaml, "w") as yaml_file:
        yaml_file.write(yaml_data)
    logger.info(yaml_data)
    return yaml_data

class Templating:
    """
    Class which provides all functionality for templating
    """

    def __init__(self, base_path=TEMPLATE_DIR):
        """
        Constructor for Templating class
        Args:
            base_path (str): path from which should read the jinja2 templates
                default(OCS_CI_ROOT_DIR/templates)
        """
        self._base_path = base_path

    def render_template(self, template_path, data):
        """
        Render a template with the given data.
        Args:
            template_path (str): location of the j2 template from the
                self._base_path
            data (dict): the data to be formatted into the template
        Returns: rendered template
        """
        j2_env = Environment(loader=FileSystemLoader(self._base_path), trim_blocks=True)
        j2_env.filters["to_nice_yaml"] = to_nice_yaml
        j2_template = j2_env.get_template(template_path)
        return j2_template.render(**data)

    @property
    def base_path(self):
        """
        Setter for self._base_path property
        """
        return self._base_path

    @base_path.setter
    def base_path(self, path):
        """
        Setter for self._base_path property
        Args:
            path (str): Base path from which look for templates
        """
        self._base_path = path