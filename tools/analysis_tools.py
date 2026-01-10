import igraph as ig
import pandas as pd
import csv
import numpy as np
import ast
import os
import subprocess
from .motif_tools import find_subgraphs_vf2


def _seek_motifs(gml_file, target_labels, edges, output_paths):
    """
    在GML文件中查找符合特定拓扑结构和节点标签的子图
    """
    graph = ig.Graph.Read_GML(gml_file)
    pattern = ig.Graph()
    pattern.add_vertices(len(target_labels))
    pattern.vs["label"] = target_labels
    pattern.add_edges(edges)
    # 查找符合拓扑结构的子图
    matching_subgraphs = find_subgraphs_vf2(graph, pattern)

    print(f"找到 {len(matching_subgraphs)} 个匹配的子图:")
    for subgraph in matching_subgraphs[:3]:  # 只打印前3个结果
        print(f"子图顶点: {subgraph['vertices']}, 标签: {subgraph['labels']}")
    basic_data = []
    for i, t in enumerate(matching_subgraphs):
        basic_data.append(
            {
                "triangle_index": i,
                "vertex_ids": ",".join(map(str, t["vertices"])),
                "vertex_labels": ",".join(map(str, t["labels"])),
            }
        )
    if not os.path.exists(output_paths):
        os.makedirs(output_paths)
    output_csv = output_paths + "motif_ids.csv"
    
    pd.DataFrame(basic_data).to_csv(output_csv, index=False)
    return output_csv


def _extract_motif_genes(spatial_csv, gene_matrix_txt, motif_csv, output_paths):
    """
    提取motif相关基因表达数据（gene*cell）并保存

    输入：
    1.spatial_csv: spatial.csv，提供细胞类型信息
    2.gene_matrix_txt: matrix_raw.txt，提供基因表达信息
    3.motif_csv: motif_ids.csv，提供motif包含的细胞id信息
    4.output_paths: 输出文件保存地址（文件夹路径，末尾需包含斜杠/）

    输出三个文件：
    1. cell_types.txt: 对应细胞类型
    2. matrix.txt: 基因表达矩阵（Matrix Market格式），gene 和 cell id 都从1开始编号
    """
    id_df = pd.read_csv(motif_csv)
    id_df = id_df["vertex_ids"]
    df_gene = pd.read_csv(gene_matrix_txt, header=None)
    df_gene[0] = df_gene[0].str.replace("\t", " ", regex=False)
    gene = [row[0].split(" ") for row in df_gene.values]
    df = pd.read_csv(spatial_csv)

    allcell_label = {}
    for i in df.index.tolist():
        allcell_label[i] = 0
    for i in range(len(id_df)):
        for j in ast.literal_eval(id_df[i]):
            allcell_label[j] = 1

    mtf_list = [i[0] for i in allcell_label.items() if i[1] == 1]
    filtered_df = df.loc[mtf_list]
    cell_types = filtered_df["label"]
    
    motif_celltypes_txt = f"{output_paths}cell_types.txt"
    with open(motif_celltypes_txt, "w") as f:
        for item in cell_types:
            f.write(f"{item}\n")

    # reindex cell ids
    mtf_gene = [g for g in gene if int(g[1]) in mtf_list]
    mtf_ids = sorted(np.unique([int(row[1]) for row in mtf_gene]))
    # row_num = len(np.unique([row[0] for row in gene]))
    row_num = max(int(row[0]) for row in gene)+1
    col_num = len(np.unique([row[1] for row in mtf_gene]))
    cell_reindex = {str(k): v for v, k in zip(range(1, col_num + 1), mtf_ids)}
    for i in range(len(mtf_gene)):
        mtf_gene[i][1] = str(cell_reindex[mtf_gene[i][1]])
        mtf_gene[i][0] = str(int(mtf_gene[i][0]) + 1)
    motif_gene_3_cols = [" ".join(i) for i in mtf_gene]
    nonzero_num = len(mtf_gene)

    motifs_matrix_txt = f"{output_paths}matrix.txt"
    with open(motifs_matrix_txt, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["%%MatrixMarket matrix coordinate real general"])
        writer.writerow([f"{row_num} {col_num} {nonzero_num}"])
        for i in motif_gene_3_cols:
            writer.writerow([i])

    return motif_celltypes_txt, motifs_matrix_txt


def _extract_target_cells(target_cell, spatial_csv, gene_matrix_txt, motif_csv, output_paths):
    """
    提取motif相关基因表达数据（gene*cell）并保存

    输入：
    1.target_cell: 目标细胞类型，如 'CAF'
    2.spatial_csv: spatial.csv，提供细胞类型信息
    3.gene_matrix_txt: matrix_raw.txt，提供基因表达信息
    4.motif_csv: motif_ids.csv，提供motif包含的细胞id信息
    5.path: 输出文件保存地址（文件夹路径，末尾需包含斜杠/）

    输出：
    mtf&non-motif_label.txt: 每个细胞是否属于motif范围内的标签
    """
    id_df = pd.read_csv(motif_csv)
    id_df = id_df["vertex_ids"]
    df_gene = pd.read_csv(gene_matrix_txt, header=None)
    df_gene[0] = df_gene[0].str.replace("\t", " ", regex=False)
    df = pd.read_csv(spatial_csv)

    allcell_label = {i: 0 for i in df.index}
    seen_indices = set()
    for i in range(len(id_df)):
        indices = ast.literal_eval(id_df[i])
        seen_indices.update(indices)

    for j in df.index:
        if df.loc[j, "label"] == target_cell:
            if j in seen_indices:
                allcell_label[j] = 1
            else:
                allcell_label[j] = -1
    
    all_cell_id = sorted(allcell_label.keys())
    all_label = [allcell_label[i] for i in all_cell_id] 
    
    label_csv = f"{output_paths}target_cell_label.csv"
    pd.DataFrame(all_label).to_csv(label_csv, index=False, header=False)

    return label_csv


def cellchat(
    gml_file, 
    target_labels, 
    spatial_csv, 
    gene_matrix_txt, 
    gene_names_csv, 
    output_paths, 
    edges=[(0, 1), (0, 2), (1, 2)]
):
    motif_ids_csv = _seek_motifs(gml_file, target_labels, edges, output_paths)
    motif_celltypes_txt, motifs_matrix_txt = _extract_motif_genes(
        spatial_csv,
        gene_matrix_txt,
        motif_ids_csv,
        output_paths
    )

    motifs = "_".join(target_labels)
    r_script = r"D:\Desktop\Agent\BioInfoMAS\tools\analysis_tools\cellchat.r"
    result = subprocess.run(
        [
            "Rscript",
            r_script,
            motifs_matrix_txt,
            motif_celltypes_txt,
            gene_names_csv,
            output_paths,
            motifs
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode == 0:
        return {
            "status": "success",
            "细胞通讯受配体对详细信息保存在": output_paths + "LRs_" + motifs + ".csv",
            "细胞通讯网络信息保存在": output_paths + "count_truncatedMean_" + motifs + ".csv",
            "细胞通讯网络权重": output_paths + "weight_truncatedMean_" + motifs + ".csv",
        }
    else:
        return {
            "status": "error",
            "details": result.stderr,
        }


def DE_analysis(
    target_cell,
    gml_file, 
    target_labels, 
    spatial_csv, 
    gene_matrix_txt, 
    gene_names_csv,
    output_paths,
    
):
    motif_csv = _seek_motifs(gml_file, target_labels, [(0, 1), (0, 2), (1, 2)], output_paths)
    label_csv = _extract_target_cells(target_cell, spatial_csv, gene_matrix_txt, motif_csv, output_paths)

    r_script = r"D:\Desktop\Agent\BioInfoMAS\tools\analysis_tools\txt2mtx.r"
    result = subprocess.run(
        [
            "Rscript",
            r_script,
            gene_matrix_txt
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    counts_mtx = gene_matrix_txt.replace(".txt", ".mtx")

    r_script = r"D:\Desktop\Agent\BioInfoMAS\tools\analysis_tools\DEA.r"
    result = subprocess.run(
        [
            "Rscript",
            r_script,
            label_csv,
            counts_mtx,
            gene_names_csv,
            output_paths,
            str(target_cell)
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.returncode == 0:
        return {
            "status": "success",
            "差异表达基因分析结果保存在": output_paths + "DEG_Wilcoxon_" + target_cell + ".csv"
            }
    else:
        return {
            "status": "error",
            "details": result.stderr,
        }
