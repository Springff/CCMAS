from autogen_framework import create_function_map
tools = create_function_map()
#################################################################################################
# fname = "construct_cell_graph"
# func = tools.get(fname)

# fargs = {
# "spatial_data_csv":r"D:\Desktop\Agent\BioInfoMAS\input\U7a25_spatial.csv",
# "output_graph_gml":r"D:\Desktop\Agent\BioInfoMAS\input\U7a25_graph.gml"
# }
# result = func(**fargs)

# print(result)

# fname = "extract_representative_subgraphs"
# func = tools.get(fname)

# fargs = {
# "input_graph_gml": "D:\Desktop\Agent\BioInfoMAS\input\T2b5_graph.gml", 
# "output_data_pkl": "D:\Desktop\Agent\BioInfoMAS\input\T2b5_graph_chaifen.pkl",
# "num_subgraphs":10
# }
# result = func(**fargs)

# print(result)

#################################################################################################

# fname = "candidate_trangle_motifs"
# func = tools.get(fname)

# fargs = {
# "input_graph_gml": r"D:\Desktop\Agent\BioInfoMAS\input\U7a25_graph.gml", 
# "motif_pkl": r"D:\Desktop\Agent\BioInfoMAS\input\U7a25_candidate_motif.pkl"
# }
# result = func(**fargs)

# print(result)

# fname = "calculate_motifs_numbers"
# func = tools.get(fname)

# fargs = {
# "motif_pkl": r"D:\Desktop\Agent\BioInfoMAS\input\U7a25_candidate_motif.pkl", 
# "dataset_path": r"D:\Desktop\Agent\BioInfoMAS\input\U7a25_graph.gml", 
# "output_csv": r"D:\Desktop\Agent\BioInfoMAS\input\U7a25_motif_num.csv", 
# }
# result = func(**fargs)

# print(result)

# fname = "identify_motif"
# func = tools.get(fname)

# fargs = {
# # "single_label": False,
# "motif_path1": r"D:\Desktop\Agent\BioInfoMAS\input\T2b5_motif_num.csv",
# # "motif_path2": r"D:\Desktop\Agent\BioInfoMAS\input\U7a25_motif_num.csv",
# }
# result = func(**fargs)

# print(result)

#################################################################################################

fname = "cellchat"
func = tools.get(fname)

fargs = {
"gml_file": "D:\Desktop\Agent\BioInfoMAS\input\T2b5_graph.gml",
"target_labels": ['CAF', 'CAF', 'CAF'],
"spatial_csv": "D:\Desktop\Agent\BioInfoMAS\input\T2b5_spatial.csv", 
"gene_matrix_txt": "D:\Desktop\Agent\BioInfoMAS\input\sparse_matrix.txt", 
"gene_names_csv": "D:\Desktop\Agent\BioInfoMAS\input\gene_names.txt", 
"output_paths": "D:\Desktop\Agent\BioInfoMAS\input\Cellchat\\CAF_CAF_CAF\\",
}
result = func(**fargs)

print(result)


# fname = "DE_analysis"
# func = tools.get(fname)

# fargs = {
# "target_cell": "CAF",
# "gml_file": "D:\Desktop\Agent\BioInfoMAS\input\T2b5_graph.gml",
# "target_labels": [ 'CAF', 'CAF', 'CAF'],
# "spatial_csv": "D:\Desktop\Agent\BioInfoMAS\input\T2b5_spatial.csv", 
# "gene_matrix_txt": "D:\Desktop\Agent\BioInfoMAS\input\sparse_matrix.txt", 
# "gene_names_csv": "D:\Desktop\Agent\BioInfoMAS\input\gene_names.txt", 
# "output_paths": "D:\Desktop\Agent\BioInfoMAS\input\DEA\\"
# }
# result = func(**fargs)

# print(result)

#################################################################################################

# fname = "load_deg_results"
# func = tools.get(fname)

# fargs = {
# "deg_file": "D:\Desktop\Agent\BioInfoMAS\input\DEA\DEG_Wilcoxon_Macrophage.csv",
# "p_adj_threshold": 0.05,
# "log2fc_threshold": 0.25
# }
# result = func(**fargs)

# print(result)


# fname = "extract_cellchat_info"
# func = tools.get(fname)

# fargs = {
# "weight_csv": "D:\Desktop\Agent\BioInfoMAS\input\Cellchat\weight_truncatedMean_CAF_CAF_Macrophage.csv",
# "count_csv": "D:\Desktop\Agent\BioInfoMAS\input\Cellchat\count_truncatedMean_CAF_CAF_Macrophage.csv",
# "lr_csv": "D:\Desktop\Agent\BioInfoMAS\input\Cellchat\LRs_CAF_CAF_Macrophage.csv"

# }
# result = func(**fargs)

# print(result)