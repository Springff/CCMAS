import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import itertools
from typing import Dict, List, Tuple
import os

def load_graph_from_gml(file_path: str) -> nx.Graph:
    """
    Load graph from GML file
    """
    G = nx.read_gml(file_path, label='id')
    return G

def identify_three_node_motifs(G: nx.Graph) -> Dict[str, List[Tuple]]:
    """
    Identify all three-node motifs in the graph
    """
    motifs = defaultdict(list)
    nodes = list(G.nodes())

    # Generate all possible 3-node combinations
    for node_combo in itertools.combinations(nodes, 3):
        subgraph = G.subgraph(node_combo)

        # Get the labels of the three nodes
        node_labels = [G.nodes[n]['label'] for n in node_combo]

        # Sort the labels to create a canonical representation
        sorted_labels = tuple(sorted(node_labels))

        # Check if subgraph is connected
        if nx.is_connected(subgraph):
            # Create a unique identifier for the motif based on node labels
            motif_id = sorted_labels
            motifs[motif_id].append(node_combo)

    return motifs

def count_motif_frequency(motifs: Dict[str, List[Tuple]]) -> Dict[str, int]:
    """
    Count the frequency of each motif type
    """
    motif_counts = {}
    for motif, instances in motifs.items():
        motif_counts[motif] = len(instances)
    return motif_counts

def identify_motif_topology(subgraph: nx.Graph) -> str:
    """
    Identify the topology of a 3-node subgraph
    """
    edge_count = subgraph.number_of_edges()
    # Create a canonical representation based on connectivity
    if edge_count == 3:  # Triangle
        return "triangle"
    elif edge_count == 2:  # Path of length 2
        return "path_2"
    elif edge_count == 1:  # Two nodes connected, one isolated in subgraph context
        return "single_edge"
    else:
        return "unconnected"

def analyze_motifs_with_topology(G: nx.Graph) -> Dict[str, Dict]:
    """
    Analyze motifs considering both labels and topology
    """
    motifs = defaultdict(lambda: {'instances': [], 'topologies': defaultdict(int)})
    nodes = list(G.nodes())

    for node_combo in itertools.combinations(nodes, 3):
        subgraph = G.subgraph(node_combo)

        if nx.is_connected(subgraph):
            # Get the labels of the three nodes
            node_labels = tuple(sorted([G.nodes[n]['label'] for n in node_combo]))

            # Identify topology
            topology = identify_motif_topology(subgraph)

            # Store the instance and topology
            motifs[node_labels]['instances'].append(node_combo)
            motifs[node_labels]['topologies'][topology] += 1

    return motifs

def save_motif_results(motifs: Dict[str, Dict], output_dir: str):
    """
    Save motif analysis results to files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Save motif counts
    with open(os.path.join(output_dir, "motif_counts.txt"), 'w') as f:
        f.write("Motif Analysis Results\n")
        f.write("="*50 + "\n")
        f.write(f"Total unique motif types: {len(motifs)}\n\n")

        for motif, data in sorted(motifs.items(), key=lambda x: len(x[1]['instances']), reverse=True):
            f.write(f"Motif: {motif}\n")
            f.write(f"  Total instances: {len(data['instances'])}\n")
            f.write(f"  Topologies: {dict(data['topologies'])}\n")
            f.write(f"  Sample instances: {data['instances'][:3]}{'...' if len(data['instances']) > 3 else ''}\n")
            f.write("\n")

    # Save top frequent motifs
    sorted_motifs = sorted(motifs.items(), key=lambda x: len(x[1]['instances']), reverse=True)
    with open(os.path.join(output_dir, "top_motifs.txt"), 'w') as f:
        f.write("Top Frequent Motifs\n")
        f.write("="*30 + "\n")
        for i, (motif, data) in enumerate(sorted_motifs[:20]):  # Top 20
            f.write(f"{i+1:2d}. {motif}: {len(data['instances'])} instances\n")
            f.write(f"     Topologies: {dict(data['topologies'])}\n")

def main():
    # Load the graph
    input_file = r"D:\Desktop\Agent\BioInfoMAS\input\T2b5_graph.gml"
    print("Loading graph from GML file...")
    G = load_graph_from_gml(input_file)

    print(f"Graph loaded. Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    # Analyze motifs
    print("Analyzing three-node motifs...")
    motifs = analyze_motifs_with_topology(G)

    print(f"Found {len(motifs)} unique motif types")

    # Calculate statistics
    total_instances = sum(len(data['instances']) for data in motifs.values())
    print(f"Total motif instances: {total_instances}")

    # Save results
    output_dir = r"D:\Desktop\Agent\BioInfoMAS\ETAI\motif_identification"
    save_motif_results(motifs, output_dir)

    # Print top 10 motifs
    print("\nTop 10 most frequent motifs:")
    print("-" * 40)
    sorted_motifs = sorted(motifs.items(), key=lambda x: len(x[1]['instances']), reverse=True)
    for i, (motif, data) in enumerate(sorted_motifs[:10]):
        print(f"{i+1:2d}. {motif}: {len(data['instances'])} instances")
        print(f"    Topologies: {dict(data['topologies'])}")

    print(f"\nResults saved to: {output_dir}")

if __name__ == "__main__":
    main()