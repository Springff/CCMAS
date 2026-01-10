"""
Data Acquisition and Preprocessing Tools
数据获取和预处理工具
"""

import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
import igraph as ig
import os
import random
import pickle
from pathlib import Path


def construct_cell_graph(
    spatial_data_csv,
    output_graph_gml,
    method="delaunay",
    k_neighbors=None,
    radius_cutoff=None
):
    """
    Construct a spatial neighborhood graph (cell graph) based on cell physical coordinates from spatial transcriptomics data.

    Parameters:
    spatial_data_csv (str): Path to the input file containing cell gene expression matrix and spatial coordinates.
    spatial_data_gml (str): Path to save the constructed cell graph.
    method (str): Algorithm to construct the graph: K-nearest neighbors (knn), fixed radius (radius), or Delaunay triangulation.
    k_neighbors (int, optional): If using KNN algorithm, specify the number of neighbors per cell (e.g., 6).
    radius_cutoff (float, optional): If using Radius algorithm, specify the maximum Euclidean distance to connect cells.

    Returns:
    graph: A constructed spatial neighborhood graph object.
    """
    output_path = Path(output_graph_gml)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if method == "delaunay":
        df = pd.read_csv(spatial_data_csv)
        if not all(col in df.columns for col in ["id", "X", "Y", "label"]):
            raise ValueError("CSV file must contain columns: 'id', 'X', 'Y', 'label'")
        points = np.column_stack((df["X"], df["Y"]))
        tri = Delaunay(points)
        graph = ig.Graph()
        graph.add_vertices(df["id"].astype(str).tolist())  
        graph.vs["label"] = df["label"].tolist()
        graph.vs["X"] = df["X"].tolist()
        graph.vs["Y"] = df["Y"].tolist()
        edges = []
        for simplex in tri.simplices:
            for i in range(3):
                for j in range(i + 1, 3):
                    node_id1 = str(df["id"][simplex[i]])  
                    node_id2 = str(df["id"][simplex[j]])  
                    if (node_id1, node_id2) not in edges and (
                        node_id2,
                        node_id1,
                    ) not in edges:  
                        edges.append((node_id1, node_id2))
        unique_labels = set(df["label"])
        graph.add_edges(edges)
        del graph.vs["name"]
        graph.write_gml(output_graph_gml)
        return {
            "status": "success",
            "节点数": graph.vcount(),
            "节点类型数": len(unique_labels),
            "边数": graph.ecount(),
            "gml_file": output_graph_gml,
        }


def _snowball_sampling(graph, start_node, target_size):
    """
    从指定的起始节点开始进行雪球采样，直到子图包含目标数量的节点。

    参数：
    - graph: 原始图 (igraph.Graph)
    - start_node: 采样的起始节点（索引）
    - target_size: 目标子图节点数量

    返回：
    - subgraph: 采样得到的子图 (igraph.Graph)
    """
    sampled_nodes = set([start_node])
    frontier = set([start_node])
    while len(sampled_nodes) < target_size:
        next_frontier = set()
        for node in frontier:
            neighbors = set(graph.neighbors(node))
            next_frontier.update(neighbors - sampled_nodes)
        if not next_frontier:
            break
        sampled_nodes.update(next_frontier)
        frontier = next_frontier
    sampled_nodes = list(sampled_nodes)
    subgraph = graph.subgraph(sampled_nodes)
    return subgraph


def _save_pickle(data, filename):
    with open(filename, "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


def extract_representative_subgraphs(
    input_graph_gml,
    output_data_pkl,
    subgraph_size=32,
    num_subgraphs=100,
):
    """
    For excessively large cell graphs, extract representative subgraphs through sampling strategies to reduce computational complexity.

    Parameters:
    input_graph_gml (str): The constructed complete large graph data file path.
    output_data_pkl (str): Path to save the extracted subgraphs in pickle format.
    subgraph_size (int): Desired number of nodes in each extracted subgraph.
    num_subgraphs (int): Number of subgraphs to extract.

    Returns:
    list: A list of extracted representative subgraphs.
    """
    output_path = Path(output_data_pkl)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    G = ig.read(input_graph_gml)
    data = []   
    for _ in range(num_subgraphs):
        start_node = random.choice(range(G.vcount()))
        subgraph = _snowball_sampling(G, start_node, subgraph_size)
        data.append(subgraph)

    _save_pickle(data, output_data_pkl)
    return {
        "status": "success",
        "num_extracted_subgraphs": num_subgraphs,
        "subgraph_node_size": subgraph_size,
        "output_pkl_path": output_data_pkl
    }
