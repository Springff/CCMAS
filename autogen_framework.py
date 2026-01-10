"""
BioInfoMAS - LLM-Based Multi-Agent System
基于AutoGen框架的生物信息学多智能体系统
支持工具调用和智能协作
"""

from tools.data_tools import construct_cell_graph, extract_representative_subgraphs
from tools.motif_tools import candidate_trangle_motifs, calculate_motifs_numbers, identify_motif
from tools.analysis_tools import cellchat, DE_analysis
from tools.biomedknowledge_tools import load_deg_results, extract_cellchat_info




def create_function_map():
    """
    创建函数映射 - 连接工具定义和实际实现
    """
    return {
        "construct_cell_graph":construct_cell_graph,
        "extract_representative_subgraphs":extract_representative_subgraphs,
        "candidate_trangle_motifs": candidate_trangle_motifs,
        "calculate_motifs_numbers": calculate_motifs_numbers,
        "identify_motif": identify_motif,
        "cellchat": cellchat,
        "DE_analysis": DE_analysis,
        "load_deg_results": load_deg_results,
        "extract_cellchat_info": extract_cellchat_info,
        
    }
