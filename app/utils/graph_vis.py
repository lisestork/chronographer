# -*- coding: utf-8 -*-
""" Visualisation helpers for graph """

from pyvis.network import Network

def pre_process(node):
    """ URI > more human-readable """
    return node.split("/")[-1].replace('_', ' ')


def get_single_color(row, col_of_interest, gs_nodes, max_iter):
    """ Colors of row[col_of_interest] in the graph """
    if row.type_df == 'ingoing' and row[col_of_interest] in gs_nodes:
        return 'green'
    if row.type_df == 'ingoing' and row[col_of_interest] not in gs_nodes:
        return 'orange'
    if row.iteration == max_iter:
        return 'blue'
    return 'yellow'


def get_node_color(subgraph, ground_truth, nodes_expanded):
    """ Color of nodes in graph, different options:
    - green: true positive
    - orange: false positive
    - blue: newly expanded nodes
    - yellow: other """
    correct_ingoing = set(subgraph[subgraph.type_df == 'ingoing'].subject.values) \
        .intersection(ground_truth)
    correct_outgoing = set(subgraph[subgraph.type_df == 'outgoing'].object.values) \
        .intersection(ground_truth)

    nodes = []
    colors = []
    max_iter = max(nodes_expanded.iteration.values)

    for _, row in subgraph.iterrows():
        if row.subject not in nodes:
            nodes.append(row.subject)
            colors.append(get_single_color(row=row, col_of_interest="subject",
                                           gs_nodes=correct_ingoing, max_iter=max_iter))

        if row.object not in nodes:
            nodes.append(row.object)
            colors.append(get_single_color(row=row, col_of_interest="object",
                                           gs_nodes=correct_outgoing, max_iter=max_iter))

    for _, row in nodes_expanded.iterrows():
        iteration = row.iteration
        color = 'blue' if iteration == max_iter else 'yellow'
        for node in [x for x in row.node_expanded if x not in nodes]:
            colors.append(color)
            nodes.append(node)

    return [(nodes[i], colors[i]) for i in range(len(nodes))]


def extract_triples(path_expanded, nodes):
    """ Extract triples for graph vis"""
    triples = []
    for iteration in range(min(path_expanded.iteration.values),
                           max(path_expanded.iteration.values)+1):
        curr_path = path_expanded[path_expanded.iteration==iteration].path_expanded.values[0]
        curr_nodes = nodes[nodes.node_expanded==iteration].node_expanded.values
        if 'ingoing' in curr_path:
            [predicate_t, object_t] = curr_path.split("ingoing-")[1].split(';')
            triples += [(node, predicate_t, object_t) for node in curr_nodes]
        else:
            [subject_t, predicate_t] = curr_path.split("outgoing-")[1].split(';')
            triples += [(subject_t, predicate_t, node) for node in curr_nodes]
    return triples


def build_complete_network(subgraph, nodes_expanded, path_expanded, save_file, ground_truth):
    """ Build html network after one iteration """
    nt_subgraph = Network("680px", "680px",
                           notebook=False, directed=True)
    nodes_color = get_node_color(subgraph=subgraph, ground_truth=ground_truth,
                                 nodes_expanded=nodes_expanded)

    for node, color in nodes_color:
        nt_subgraph.add_node(node, label=pre_process(node), color=color)
    for _, row in subgraph.iterrows():
        nt_subgraph.add_edge(row.subject, row.object,
                             label=pre_process(row.predicate))

    triples = extract_triples(path_expanded=path_expanded, nodes=nodes_expanded)
    for subject_t, predicate_t, object_t in triples:
        nt_subgraph.add_edge(subject_t, object_t,
                             label=pre_process(predicate_t))
    nt_subgraph.repulsion(node_distance=600, spring_length=340,
                          spring_strength=0.4)
    nt_subgraph.show(save_file)
