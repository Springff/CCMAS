import csv
import numpy as np
from scipy.spatial import Delaunay

def read_spatial_data(file_path):
    """
    Read the spatial data from CSV file.
    Returns coordinates and cell labels.
    """
    coords = []
    labels = []
    ids = []

    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ids.append(int(row['id']))
            coords.append([float(row['X']), float(row['Y'])])
            labels.append(row['label'])

    return np.array(coords), labels, ids

def build_delaunay_graph(coords, labels, ids):
    """
    Build a graph using Delaunay triangulation.
    Returns edges and node information.
    """
    # Perform Delaunay triangulation
    tri = Delaunay(coords)

    # Create a set to store unique edges
    edges = set()

    # Extract edges from the triangulation
    for simplex in tri.simplices:
        # Each simplex is a triangle with 3 points
        # Add all edges of the triangle
        for i in range(3):
            p1_idx = simplex[i]
            p2_idx = simplex[(i + 1) % 3]
            # Create edge as a sorted tuple to avoid duplicates
            edge = tuple(sorted((p1_idx, p2_idx)))
            edges.add(edge)

    # Convert to list of edges
    edge_list = list(edges)

    return edge_list, coords, labels, ids

def save_to_gml(edge_list, coords, labels, ids, output_file):
    """
    Save the graph to GML format that conforms to igraph specifications.
    """
    with open(output_file, 'w') as f:
        f.write("graph [\n")
        f.write("  directed 0\n")  # Undirected graph

        # Write nodes
        for i in range(len(coords)):
            f.write(f"  node [\n")
            f.write(f"    id {ids[i]}\n")
            f.write(f"    label \"{labels[i]}\"\n")
            f.write(f"    x {coords[i][0]}\n")
            f.write(f"    y {coords[i][1]}\n")
            f.write(f"  ]\n")

        # Write edges
        for edge in edge_list:
            f.write(f"  edge [\n")
            f.write(f"    source {edge[0]}\n")
            f.write(f"    target {edge[1]}\n")
            f.write(f"  ]\n")

        f.write("]\n")

def main():
    # File paths
    input_file = "T2b5_spatial.csv"
    output_file = "cell_graph.gml"

    print("Reading spatial data...")
    coords, labels, ids = read_spatial_data(input_file)
    print(f"Loaded {len(coords)} cells")

    print("Building Delaunay triangulation graph...")
    edge_list, coords, labels, ids = build_delaunay_graph(coords, labels, ids)
    print(f"Created {len(edge_list)} edges")

    print("Saving to GML format...")
    save_to_gml(edge_list, coords, labels, ids, output_file)

    print(f"Graph saved to {output_file}")
    print(f"Graph contains {len(coords)} nodes and {len(edge_list)} edges")

if __name__ == "__main__":
    main()