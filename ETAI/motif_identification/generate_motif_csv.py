import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import itertools
from typing import Dict, List, Tuple
import os
import csv

def load_graph_from_gml(file_path: str) -> nx.Graph:
    """
    Load graph from GML file
    """
    G = nx.read_gml(file_path, label='id')
    return G

def identify_three_node_motifs_optimized(G: nx.Graph) -> Dict[str, Dict]:
    """
    Identify all three-node motifs in the graph using an optimized approach
    """
    motifs = defaultdict(lambda: {'instances': [], 'topologies': defaultdict(int)})

    # Get all edges in the graph
    edges = list(G.edges())

    # For each edge, find all nodes that connect to either of the edge's nodes
    processed_combinations = set()

    for i, (u, v) in enumerate(edges):
        if i % 1000 == 0:  # Progress indicator
            print(f"Processing edge {i}/{len(edges)}")

        # Look for all nodes that connect to either u or v
        neighbors_u = set(G.neighbors(u))
        neighbors_v = set(G.neighbors(v))

        # Find all possible third nodes that would make a 3-node subgraph
        possible_third_nodes = neighbors_u.union(neighbors_v)

        for w in possible_third_nodes:
            if w != u and w != v:
                # Create sorted node combination to avoid duplicates
                node_combo = tuple(sorted([u, v, w]))

                if node_combo not in processed_combinations:
                    processed_combinations.add(node_combo)

                    # Get the subgraph
                    subgraph = G.subgraph(node_combo)

                    if nx.is_connected(subgraph):
                        # Get the labels of the three nodes
                        node_labels = tuple(sorted([G.nodes[n]['label'] for n in node_combo]))

                        # Identify topology
                        edge_count = subgraph.number_of_edges()
                        if edge_count == 3:  # Triangle
                            topology = "triangle"
                        elif edge_count == 2:  # Path of length 2 or V-shape
                            topology = "path_2_or_v_shape"
                        else:
                            topology = f"{edge_count}_edges"

                        # Store the instance and topology
                        motifs[node_labels]['instances'].append(node_combo)
                        motifs[node_labels]['topologies'][topology] += 1

    return motifs

def save_motif_results_csv(motifs: Dict[str, Dict], output_dir: str):
    """
    Save motif analysis results to a CSV file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Prepare data for CSV
    csv_data = []
    for motif, data in sorted(motifs.items(), key=lambda x: len(x[1]['instances']), reverse=True):
        csv_data.append([str(motif), len(data['instances'])])

    # Write to CSV file
    csv_file_path = os.path.join(output_dir, "motif_counts.csv")
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["pattern", "Number of occurrences"])  # Header
        writer.writerows(csv_data)

    print(f"CSV file saved to: {csv_file_path}")

def main():
    # Load the graph
    input_file = r"D:\Desktop\Agent\BioInfoMAS\input\T2b5_graph.gml"
    print("Loading graph from GML file...")
    G = load_graph_from_gml(input_file)

    print(f"Graph loaded. Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    # Analyze motifs with optimized approach
    print("Analyzing three-node motifs (optimized approach)...")
    motifs = identify_three_node_motifs_optimized(G)

    print(f"Found {len(motifs)} unique motif types")

    # Calculate statistics
    total_instances = sum(len(data['instances']) for data in motifs.values())
    print(f"Total motif instances: {total_instances}")

    # Save results as CSV
    output_dir = r"D:\Desktop\Agent\BioInfoMAS\ETAI\motif_identification"
    save_motif_results_csv(motifs, output_dir)

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