import pickle
import itertools
import pandas as pd
import igraph as ig
from collections import Counter
from pathlib import Path


def candidate_trangle_motifs(input_graph_gml, motif_pkl):
    G = ig.read(input_graph_gml)
    node_types = G.vs["label"]
    type_counts = Counter(node_types)
    total_nodes = len(node_types)
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    cumulative = 0
    top_types = []
    for typ, count in sorted_types:
        proportion = count / total_nodes
        cumulative += proportion
        top_types.append(typ)
        if cumulative >= 0.8:
            break
    triangle = list(itertools.combinations_with_replacement(top_types, 3))
    output_path = Path(motif_pkl)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _save_pickle(triangle, motif_pkl)
    return {
        "status": "success",
        "候选motif的数量": len(triangle),
        "candidate_motifs_path": motif_pkl,
    }


def _load_pickle(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)


def _save_pickle(data, filename):
    with open(filename, "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


def find_subgraphs_vf2(target_graph, pattern_graph, label_attr="label"):
    """
    使用 VF2 算法查找子图同构。
    节点匹配基于指定的标签属性（如 "label"）。
    """
    t_labels = target_graph.vs[label_attr]
    p_labels = pattern_graph.vs[label_attr]

    unique_labels = sorted(list(set(t_labels) | set(p_labels)))
    label_to_int = {label: i for i, label in enumerate(unique_labels)}

    color1 = [label_to_int[x] for x in t_labels]
    color2 = [label_to_int[x] for x in p_labels]

    mappings = target_graph.get_subisomorphisms_vf2(
        pattern_graph, color1=color1, color2=color2
    )

    results = []
    for mapping in mappings:
        vertices_in_target = mapping
        labels = [target_graph.vs[v][label_attr] for v in vertices_in_target]
        results.append({"vertices": vertices_in_target, "labels": labels})
    return results


def calculate_motifs_numbers(motif_pkl, dataset_path, output_csv):
    motifs = _load_pickle(motif_pkl)
    output = []
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if dataset_path.endswith(".pkl"):
        dataset = _load_pickle(dataset_path)
        for j in range(len(motifs)):
            pattern = ig.Graph()
            pattern.add_vertices(len(motifs[j]))
            pattern.vs["label"] = motifs[j]
            pattern.add_edges([(0, 1), (0, 2), (1, 2)])
            for i in range(len(dataset)):
                matching_subgraphs = find_subgraphs_vf2(dataset[i], pattern)
                output.append(
                    {
                        "pattern": pattern.vs["label"],
                        "id": i,
                        "Number of occurrences": len(matching_subgraphs),
                    }
                )
        df = pd.DataFrame(output)
        df["pattern"] = df["pattern"].apply(tuple)
        summary = df.groupby("pattern", as_index=False)["Number of occurrences"].sum()
        summary.to_csv(output_csv, index=False)

    elif dataset_path.endswith(".gml"):
        data = ig.read(dataset_path)
        for j in range(len(motifs)):
            pattern = ig.Graph()
            pattern.add_vertices(len(motifs[j]))
            pattern.vs["label"] = motifs[j]
            pattern.add_edges([(0, 1), (0, 2), (1, 2)])
            matching_subgraphs = find_subgraphs_vf2(data, pattern)
            output.append(
                {
                    "pattern": pattern.vs["label"],
                    "Number of occurrences": len(matching_subgraphs),
                }
            )
        df = pd.DataFrame(output)
        df["pattern"] = df["pattern"].apply(tuple)
        df.to_csv(output_csv, index=False)
    else:
        return {
            "status": "error",
            "message": "路径不合法，既不是 .pkl 也不是 .gml 文件",
        }

    return {
        "status": "success",
        "模体出现次数保存在": output_csv,
    }


def identify_motif(motif_path1, motif_path2=None, single_label=True):
    if single_label:
        motifs = pd.read_csv(motif_path1)
        top10_motifs = motifs.nlargest(10, "Number of occurrences")
        motif_details = [
            {"cell_motifs": row["pattern"], "frequency": row["Number of occurrences"]}
            for _, row in top10_motifs.iterrows()
        ]
        return {"status": "success", "motifs": motif_details}
    else:
        if motif_path2 is None:
            return {
                "status": "error",
                "message": "Path to second motif file is missing.",
            }

        try:
            df1 = pd.read_csv(motif_path1)
            df2 = pd.read_csv(motif_path2)

            df1 = df1.rename(columns={"Number of occurrences": "count_1"})
            df2 = df2.rename(columns={"Number of occurrences": "count_2"})

            merged_df = pd.merge(
                df1[["pattern", "count_1"]],
                df2[["pattern", "count_2"]],
                on="pattern",
                how="outer",
            ).fillna(0)

            total_1 = merged_df["count_1"].sum()
            total_2 = merged_df["count_2"].sum()

            if total_1 == 0:
                total_1 = 1
            if total_2 == 0:
                total_2 = 1

            merged_df["freq_1"] = merged_df["count_1"] / total_1
            merged_df["freq_2"] = merged_df["count_2"] / total_2
            merged_df["diff_score"] = (merged_df["freq_1"] - merged_df["freq_2"]).abs()
            top10_diff = merged_df.nlargest(10, "diff_score")

            motif_details = []
            for _, row in top10_diff.iterrows():
                dominant = "file1" if row["freq_1"] > row["freq_2"] else "file2"
                motif_details.append(
                    {
                        "cell_motifs": row["pattern"],
                        "count_in_file1": int(row["count_1"]),
                        "count_in_file2": int(row["count_2"]),
                        "frequency_in_file1": row["freq_1"],
                        "frequency_in_file2": row["freq_2"],
                        "dominant_in": dominant, 
                    }
                )
            return {"status": "success", "motifs": motif_details}

        except Exception as e:
            return {"status": "error", "message": str(e)}
