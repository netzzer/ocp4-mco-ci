import logging
from src.framework import config
from src.utility.exceptions import CommandFailed
from src.ocs.ocp import OCP
from src.ocs.ocs import OCS
from src.utility.constants import WORKER_MACHINE, OPERATOR_NODE_LABEL

logger = logging.getLogger(__name__)


def get_nodes(node_type=WORKER_MACHINE, num_of_nodes=None):
    """
    Get cluster's nodes according to the node type (e.g. worker, master) and the
    number of requested nodes from that type
    Args:
        node_type (str): The node type (e.g. worker, master)
        num_of_nodes (int): The number of nodes to be returned
    Returns:
        list: The nodes OCP instances
    """
    typed_nodes = [
        node
        for node in get_node_objs()
        if node_type in node.ocp.get_resource(resource_name=node.name, column="ROLES")
    ]
    if num_of_nodes:
        typed_nodes = typed_nodes[:num_of_nodes]
    return typed_nodes


def get_node_status(node_obj):
    """
    Get the node status.
    Args:
        node_obj (ocs_ci.ocs.resources.ocs.OCS): The node object
    Return:
        str: The node status. If the command failed, it returns None.
    """
    return node_obj.ocp.get_resource_status(node_obj.name)


def get_node_objs(node_names=None):
    """
    Get node objects by node names
    Args:
        node_names (list): The node names to get their objects for.
            If None, will return all cluster nodes
    Returns:
        list: Cluster node OCP objects
    """
    nodes_obj = OCP(kind="node")
    node_dicts = nodes_obj.get()["items"]
    if not node_names:
        nodes = [OCS(**node_obj) for node_obj in node_dicts]
    else:
        nodes = [
            OCS(**node_obj)
            for node_obj in node_dicts
            if (node_obj.get("metadata").get("name") in node_names)
        ]
    assert nodes, "Failed to get the nodes OCS objects"
    return nodes


def get_nodes_in_statuses(statuses, node_objs=None):
    """
    Get all nodes in specific statuses
    Args:
        statuses (list): List of the statuses to search for the nodes
        node_objs (list): The node objects to check their statues. If not specified,
            it gets all the nodes.
    Returns:
        list: OCP objects representing the nodes in the specific statuses
    """
    if not node_objs:
        node_objs = get_node_objs()

    nodes_in_statuses = []
    for n in node_objs:
        try:
            node_status = get_node_status(n)
        except CommandFailed as e:
            logger.warning(f"Failed to get the node status due to the error: {str(e)}")
            continue

        if node_status in statuses:
            nodes_in_statuses.append(n)

    return nodes_in_statuses


def get_typed_worker_nodes(os_id="rhcos"):
    """
    Get worker nodes with specific OS
    Args:
        os_id (str): OS type like rhcos, RHEL etc...
    Returns:
        list: list of worker nodes instances having specified os
    """
    worker_nodes = get_nodes(node_type="worker")
    return [
        node
        for node in worker_nodes
        if node.get().get("metadata").get("labels").get("node.openshift.io/os_id")
        == os_id
    ]


def label_nodes(nodes, label=OPERATOR_NODE_LABEL):
    """
    Label nodes
    Args:
        nodes (list): list of node objects need to label
        label (str): New label to be assigned for these nodes.
            Default value is the OCS label
    """
    node_obj = OCP(kind="node")
    for new_node_to_label in nodes:
        node_obj.add_label(resource_name=new_node_to_label.name, label=label)
        logger.info(
            f"Successfully labeled {new_node_to_label.name} " f"with OCS storage label"
        )
