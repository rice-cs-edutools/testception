"""
Students are required to submit (which will be machine graded):
    make_example_graph
    make_complete_graph
    compute_in_degrees
    in_degree_distribution

These functions are standalone and do not require any other code 
to be provided to the students. 
"""

import math

# Define three constant dictionaries corresponding to specified graphs
EX_GRAPH0 = {0 : set([1, 2]), 1 : set([]), 2 : set([])}

EX_GRAPH1 = {0 : set([1, 4, 5]), 1 : set([2, 6]), 2 : set([3]), 
                  3 : set([0]), 4 : set([1]), 5 : set([2]),
                  6 : set([])}

EX_GRAPH2 = {0 : set([1, 4, 5]), 1 : set([2, 6]), 2 : set([3, 7]), 
                  3 : set([7]), 4 : set([1]), 5 : set([2]),
                  6 : set([]), 7 : set([3]), 8 : set([1, 2]), 
                  9 : set([0, 3, 4, 5, 6, 7])}

def make_complete_graph(num_nodes):
    """
    Returns a complete graph containing num_nodes nodes.
        
    The nodes of the returned graph will be 0...(num_nodes-1) if
    num_nodes-1 is positive.  An empty graph will be returned in all
    other cases.  Note that self-loops are not allowed.
        
    Arguments:
    num_nodes -- The number of nodes in the returned graph.
        
    Returns:
    A complete graph in dictionary form.
    """
    result = { }
    
    for node_key in range(num_nodes):
        result[node_key] = set()
        for node_value in range(num_nodes):
            if node_key != node_value: # no loops allowed in AT
                result[node_key].add(node_value)
    
    return result

def compute_in_degrees(digraph):
    """
    Compute in_degree for all nodes in graph.

    Arguments:
    digraph -- dictionary modeling a graph

    Returns:
    Dictionary mapping nodes to their in_degree
    """
    degrees = {}
    for node in digraph:
        degrees[node] = 0

    for node in digraph:
        for nbr in digraph[node]:
            degrees[nbr] += 1

    return degrees

def in_degree_distribution(digraph):
    """
    Generate a dictionary with the in-degree distribution of g.

    Arguments:
    digraph -- dictionary modeling a graph

    Returns:
    A dictionary with in-degrees as keys and the number of nodes in
    g with that degree as values.
    """
    dist = {}
    in_degrees = compute_in_degrees(digraph)
    for node in in_degrees:
        node_degree = in_degrees[node] 
        if node_degree not in dist:
            dist[node_degree] = 1
        else:
            dist[node_degree] += 1

    return dist
