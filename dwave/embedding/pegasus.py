from dwave_networkx.generators.chimera import chimera_graph
from dwave_networkx.generators.pegasus import (get_tuple_defragmentation_fn, get_tuple_fragmentation_fn,
    pegasus_coordinates, pegasus_graph)
from dwave.embedding.polynomialembedder import processor
import networkx as nx


#TODO: change function interface to more closely resemble chimera
@nx.utils.decorators.nodes_or_number(0)
def find_clique_embedding(k, m=None, target_graph=None):
    """Find an embedding of a k-sized clique on a Pegasus graph (target_graph).

    This clique is found by transforming the Pegasus graph into a K2,2 Chimera graph and then
    applying a Chimera clique finding algorithm. The results are then converted back in terms of
    Pegasus coordinates.

    Note: If target_graph is None, m will be used to generate a m-by-m Pegasus graph. Hence m and
    target_graph cannot both be None.

    Args:
        k (int): Number of members in the requested clique
        m (int): Number of tiles in a row of a square Pegasus graph
        target_graph (networkx.graph): A Pegasus graph

    Returns:
        A dictionary representing target_graphs's clique embedding. Each dictionary key represents a
        node in said clique. Each corresponding dictionary value is a list of pegasus coordinates
        that should be chained together to represent said node.
    """
    # Organize parameter values
    if target_graph is None:
        if m is None:
            raise ValueError("m and target_graph cannot both be None.")
        target_graph = pegasus_graph(m)

    m = target_graph.graph['rows']     # We only support square Pegasus graphs
    n_nodes, nodes = k

    # Break each Pegasus qubits into six Chimera fragments
    # Note: By breaking the graph in this way, you end up with a K2,2 Chimera graph
    coord_converter = pegasus_coordinates(m)
    pegasus_coords = map(coord_converter.tuple, target_graph.nodes)
    fragment_tuple = get_tuple_fragmentation_fn(target_graph)
    fragments = fragment_tuple(pegasus_coords)

    # Create a K2,2 Chimera graph
    # Note: 6 * m because Pegasus qubits split into six pieces, so the number of rows and columns
    #   get multiplied by six
    chim_m = 6 * m
    chim_graph = chimera_graph(chim_m, t=2, coordinates=True)

    # Determine valid fragment couplers in a K2,2 Chimera graph
    edges = chim_graph.subgraph(fragments).edges()

    # Find clique embedding in K2,2 Chimera graph
    embedding_processor = processor(edges, M=chim_m, N=chim_m, L=2, linear=False)
    chimera_clique_embedding = embedding_processor.tightestNativeClique(n_nodes)

    # Convert chimera fragment embedding in terms of Pegasus coordinates
    defragment_tuple = get_tuple_defragmentation_fn(target_graph)
    pegasus_clique_embedding = map(defragment_tuple, chimera_clique_embedding)

    #TODO: raise error for no embedding
    return dict(zip(nodes, pegasus_clique_embedding))