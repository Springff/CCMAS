import pandas as pd
from scipy.spatial import Delaunay
from scipy.sparse import csr_matrix
import csv
import numpy as np
import ast
import os


# This function is to extract the gene expression matrix of the specific pattern and the labels for DEGs analysis.
# The output will be original pattern regions and 3-hop extended regions
def extract_motifs_id(file, gene_file, id_file, name):
    # file: spatial.csv
    # gene_file: matrix_raw.txt
    # id_file: motif_ids.csv
    # name: motif name

    def iterate_hop(flag, iterate, mtf_simplices, tri):
        if iterate == flag:
            return
        for it_tri_sim in tri.simplices:
            # sim_name = [df['NAME'][tmp] for tmp in it_tri_sim]
            if mtf_simplices in it_tri_sim:
                for j in range(3):
                    if it_tri_sim[j] not in mtf_hop_list:
                        mtf_hop_list.append(it_tri_sim[j])
                        iterate_hop(flag, iterate + 1, it_tri_sim[j], tri)

    id_df = pd.read_csv(id_file)
    id_df = id_df["vertex_ids"]
    df_gene = pd.read_csv(gene_file, header=None)
    df_gene[0] = df_gene[0].str.replace("\t", " ", regex=False)
    gene = [row[0].split(" ") for row in df_gene.values]
    # print(gene)
    df = pd.read_csv(file)
    points = np.stack((df["CenterX_local_px"], df["CenterY_local_px"]), axis=-1)
    tri = Delaunay(points)

    # orginal
    allcell_label = {}  # 原始motif-id
    # for i in df['NAME']:
    for i in df.index.tolist():
        allcell_label[i] = 0
    for i in range(len(id_df)):
        for j in ast.literal_eval(id_df[i]):
            allcell_label[j] = 1
    #     print(allcell_label[394])
    #     print(allcell_label[425])
    #     print(allcell_label[358])
    mtf_list = [i[0] for i in allcell_label.items() if i[1] == 1]
    #     print(mtf_list)#从0开始的索引
    # print(df['top_level_cell_type'][mtf_list[0]])
    # print(df['top_level_cell_type'][mtf_list[2]])
    # print(len(mtf_list))
    mtf_gene = [g for g in gene if int(g[1]) in mtf_list]
    # print(mtf_gene[0])
    # print(mtf_gene[1])
    # print(mtf_gene[2])
    a = mtf_list
    ag = gene
    # print(gene)
    # print(mtf_list)

    df_mtf_gene = pd.DataFrame(
        mtf_gene, columns=["gene_name", "cell_id", "expression_value"]
    )  # 这里的列名是示例，可以按实际情况替换

    # 指定保存的文件路径和文件名
    output_file_path = "D:/Desktop/GLM/新数据/PDAC/T2b5/extracted_matrix/1.csv"

    # 使用to_csv方法保存为CSV文件
    df_mtf_gene.to_csv(output_file_path, index=False)

    # row_num = len(np.unique([row[0] for row in mtf_gene]))
    row_num = len(np.unique([row[0] for row in gene]))
    col_num = len(np.unique([row[1] for row in mtf_gene]))

    mtf_ids = sorted(np.unique([int(row[1]) for row in mtf_gene]))
    filtered_df = df.loc[mtf_list]
    cell_types = filtered_df["annotation_majortypes"]
    print(cell_types)
    path = f"D:/Desktop/GLM/新数据/PDAC/T2b5/extracted_matrix/original/{name}/"
    if not os.path.exists(path):
        os.makedirs(path)

    with open(f"{path}cell_types.txt", "w") as f:
        for item in cell_types:
            f.write(f"{item}\n")
    print(mtf_gene)

    # reindex cell ids
    cell_reindex = {str(k): v for v, k in zip(range(1, col_num + 1), mtf_ids)}
    for i in range(len(mtf_gene)):
        mtf_gene[i][1] = str(cell_reindex[mtf_gene[i][1]])
        mtf_gene[i][0] = str(int(mtf_gene[i][0]) + 1)
    print(mtf_gene)
    motif_gene_3_cols = [" ".join(i) for i in mtf_gene]
    nonzero_num = len(mtf_gene)

    all_cell_id = sorted(allcell_label.keys())
    all_label = [allcell_label[i] for i in all_cell_id]  # 展开为单行列表

    with open(f"{path}mtf&non-motif_label.txt", "w") as f:
        for label in all_label:
            f.write(f"{label}\n")  # 每个值写入一行

    with open(f"{path}matrix.txt", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["%%MatrixMarket matrix coordinate real general"])
        writer.writerow([f"{row_num} {col_num} {nonzero_num}"])
        for i in motif_gene_3_cols:
            writer.writerow([i])

    # 3hop
    mtf_tri = []

    motif_list = [i[0] for i in allcell_label.items() if i[1] == 1]
    # print(motif_list)
    # print(len(motif_list))
    for sim in tri.simplices:
        if len(set(sim) & set(motif_list)) > 1:
            mtf_tri.append(sim)
    """
    for i in range(len(id_df)):
         mtf_tri.append(sorted([ast.literal_eval(id_df[0][i])[j] for j in [0,1,2]]))
         mtf_tri.append(sorted([ast.literal_eval(id_df[0][i])[j] for j in [0,1,3]]))
    """

    """
    for simplice in tri.simplices:
         if sorted(list(simplice)) in mtf_tri:
              mtf_count += 1
    """
    mtf_hop_list = []
    for i in motif_list:
        mtf_hop_list.append(i)
    # print(mtf_hop_list)
    # print(len(mtf_hop_list))
    for i, mtf in enumerate(motif_list):
        # print(i)
        # print(mtf)
        iterate_hop(3, 0, mtf, tri)
    # print(mtf_hop_list)
    # print(len(mtf_hop_list))

    for i in mtf_hop_list:
        allcell_label[i] = 1

    if name.startswith("non"):
        allcell_label = {k: 0 if i == 1 else 1 for k, i in allcell_label.items()}
        mtf_hop_list = [k for k, i in allcell_label.items() if i == 1]

    df_gene = pd.read_csv(gene_file, header=None)
    df_gene[0] = df_gene[0].str.replace("\t", " ", regex=False)
    ag = [row[0].split(" ") for row in df_gene.values]
    # print(ag)

    mtf_gene = [g for g in ag if int(g[1]) in mtf_hop_list]

    df_mtf_gene = pd.DataFrame(
        mtf_gene, columns=["gene_name", "cell_id", "expression_value"]
    )  # 这里的列名是示例，可以按实际情况替换

    # 指定保存的文件路径和文件名
    output_file_path = "D:/Desktop/GLM/新数据/PDAC/下游分析/pattern_analysis_pipeline/AD-disease/extracted_matrix/2.csv"

    # 使用to_csv方法保存为CSV文件
    #     df_mtf_gene.to_csv(output_file_path, index=False)

    print(len(mtf_gene))
    row_num = len(np.unique([row[0] for row in mtf_gene]))
    col_num = len(np.unique([row[1] for row in mtf_gene]))
    # print(row_num)
    # print(col_num)

    mtf_ids = sorted(np.unique([int(row[1]) for row in mtf_gene]))
    mtf_hop_list = sorted(mtf_hop_list)
    filtered_df = df.loc[mtf_hop_list]
    cell_types = filtered_df["annotation_majortypes"]
    print(cell_types)
    path = f"D:/Desktop/GLM/新数据/PDAC/T2b5/extracted_matrix/3hop/{name}/"
    if not os.path.exists(path):
        os.makedirs(path)

    with open(f"{path}cell_types.txt", "w") as f:
        for item in cell_types:
            f.write(f"{item}\n")

    # reindex cell ids
    cell_reindex = {str(k): v for v, k in zip(range(col_num), mtf_ids)}
    for i in range(len(mtf_gene)):
        mtf_gene[i][1] = str(cell_reindex[mtf_gene[i][1]])

    motif_gene_3_cols = [" ".join(i) for i in mtf_gene]
    nonzero_num = len(mtf_gene)

    all_cell_id = sorted(allcell_label.keys())
    all_label = [allcell_label[i] for i in all_cell_id]  # 展开为单行列表

    with open(f"{path}mtf&non-motif_label.txt", "w") as f:
        for label in all_label:
            f.write(f"{label}\n")  # 每个值写入一行

    with open(f"{path}matrix.txt", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["%%MatrixMarket matrix coordinate real general"])
        writer.writerow([f"{row_num} {col_num} {nonzero_num}"])
        for i in motif_gene_3_cols:
            writer.writerow([i])
    return


mtf = "mcpp"
spatial_file = f"D:/Desktop/GLM/新数据/PDAC/T2b5/spatial.csv"
gene_file = f"D:/Desktop/GLM/新数据/PDAC/T2b5/sparse_matrix.txt"
id_file = f"D:/Desktop/GLM/新数据/PDAC/T2b5/matching_subgraphs_with_911515.csv"

# change the motif name based on the motif you found


extract_motifs_id(spatial_file, gene_file, id_file, mtf)
# change_idx(m,mtf)
