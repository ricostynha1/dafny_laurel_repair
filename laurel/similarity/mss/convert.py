"""
Convert the scipy linkage matrix to a tree structure.
"""
from scipy.cluster import hierarchy
from redbaron import RedBaron

from corexploration.analysis.string_collector import StatisticsAggregator


def convert_node(clustering, root, rbs, prompt: str):
    def convert_node_inner(node, id):
        child_nodes = node.pre_order(lambda x: x.id)
        rbs_subset = {k: rbs[k] for k in child_nodes}
        aggregator = StatisticsAggregator(prompt, rbs_subset)
        if node.is_leaf():
            return {
                "n": id + "--" + str(node.id),
                "id": str(node.id),
                "d": 0.0,
                "centroid_suggestion": node.id,
                "children": [],
                "stats": aggregator.get_most_common(),
            }
        else:
            avg_dist = lambda p: sum(clustering.dist[p, q] for q in child_nodes)
            ctr = min(child_nodes, key=avg_dist)
            return {
                "n": id,
                "d": node.dist,
                "centroid_suggestion": ctr,
                "children": [
                    convert_node_inner(node.left, id + "-0"),
                    convert_node_inner(node.right, id + "-1"),
                ],
                "stats": aggregator.get_most_common(),
            }

    return convert_node_inner(root, "0")


def convert_linkage_to_tree(clustering, rbs: dict[int, RedBaron], prompt):
    """
    input: linkage_matrix (cluster.hac_res)
    output: Tree of structure:
        - n: str (label)
        - d: float (distance)
        - c: List[Tree] (children, length 0 or 2)
    """
    root = hierarchy.to_tree(clustering.hac_res)
    return convert_node(clustering, root, rbs, prompt)
