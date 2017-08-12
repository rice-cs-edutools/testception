def validate_directed_graph(args):
    """
    Checks that the 0th arg is a valid directed graph.
    """
    graph = args[0]

    ## All nodes in the edge set must be nodes in the graph
    for node, nbrs in graph.items():

        ## Check for validity of the existing copy
        for nbr in nbrs:

            if nbr not in graph:
                ## All neighbors must first be nodes
                return False

            elif nbr == node:
                ## Reject self-loops
                return False

    return True

def mutate_directed_graph(args):
    """
    Mutating version of validate_directed_graph, which guarantees that the
    result is valid.

    Checks that the 0th arg is a valid directed graph.
    """
    graph = args[0]

    ## All nodes in the edge set must be nodes in the graph
    new_graph = {}
    for node, nbrs in graph.items():

        ## First, update our valid copy
        if node not in new_graph:
            new_graph[node] = set(nbrs)
        else:
            new_graph[node].update(nbrs)

        ## Second, check for validity of the existing copy
        for nbr in nbrs:

            if nbr not in graph:
                ## All neighbors must first be nodes
                if nbr not in new_graph:
                    new_graph[nbr] = set([node])

            elif nbr == node:
                ## Remove self-loops
                new_graph[node].remove(node)

    ## Technically the clearing is unnecessary, since we're just changing
    ## the valuds of all of the existing keys
    graph.clear()
    for node, nbrs in new_graph.items():
        graph[node] = nbrs

    return True

def validate_undirected_graph(args):
    """
    Checks that the 0th arg is a valid undirected graph.
    """
    graph = args[0]

    ## All nodes in the edge set must be nodes in the graph;
    ## edge sets must be symmetric
    for node, nbrs in graph.items():

        ## Check for validity of the existing copy
        for nbr in nbrs:

            if nbr not in graph:
                ## All neighbors must first be nodes
                return False

            elif nbr == node:
                ## Reject self-loops
                return False

            elif node not in graph[nbr]:
                ## Reject asymmetric relationships
                return False

    return True

def mutate_undirected_graph(args):
    """
    Mutating version of validate_undirected_graph, which guarantees that the
    result is valid.

    Checks that the 0th arg is a valid undirected graph.
    """
    graph = args[0]

    ## All nodes in the edge set must be nodes in the graph;
    ## edge sets must be symmetric
    new_graph = {}
    for node, nbrs in graph.items():

        ## First, update our valid copy
        if node not in new_graph:
            new_graph[node] = set(nbrs)
        else:
            new_graph[node].update(nbrs)

        ## Second, check for validity of the existing copy
        for nbr in nbrs:

            if nbr not in graph:
                ## All neighbors must first be nodes
                if nbr not in new_graph:
                    new_graph[nbr] = set([node])

            elif nbr == node:
                ## Remove self-loops
                new_graph[node].remove(node)

            elif node not in graph[nbr]:
                ## Fix asymmetric relationships
                if nbr not in new_graph:
                    new_graph[nbr] = set([])
                new_graph[nbr].add(node)

    ## Technically the clearing is unnecessary, since we're just changing
    ## the values of all of the existing keys, but it makes me feel better 
    graph.clear()
    for node, nbrs in new_graph.items():
        graph[node] = nbrs
    
    return True

def validate_bfs(args):
    """
    Checks that the 0th arg is a valid undirected graph, and the 1st arg is
    a node in that graph.
    """
    retval = validate_undirected_graph(args)
    if retval:
        retval = (args[1] in args[0])
    return retval

def mutate_bfs(args):
    """
    Mutating version of validate_bfs, which guarantees that the resultant
    graph is valid, but doesn't necessarily guarantee that the start node is
    in the graph, since I can't mutate ints.

    Checks that the 0th arg is a valid undirected graph, and the 1st arg is
    a node in that graph.
    """
    retval = mutate_undirected_graph(args)
    if retval:
        retval = (args[1] in args[0])
    return retval

def validate_resilience(args):
    """
    Checks that the 0th arg is a valid undirected graph, and the 1st arg is
    a list of unique nodes in that graph.
    """
    retval = validate_undirected_graph(args)
    if retval:
        retval = not bool(len(filter(lambda x: x not in args[0], args[1]))) \
            and list(set(args[1])) == args[1]
    return retval

def mutate_resilience(args):
    """
    Mutating version of validate_resilience, which guarantees that the
    resultant graph is valid, but doesn't necessarily guarantee that the list
    of nodes is valid.

    Checks that the 0th arg is a valid undirected graph, and the 1st arg is
    a list of unique nodes in that graph.
    """
    retval = mutate_undirected_graph(args)
    if retval:
        retval = not bool(len(filter(lambda x: x not in args[0], args[1]))) \
            and list(set(args[1])) == args[1]
    return retval
