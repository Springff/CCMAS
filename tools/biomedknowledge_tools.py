import pandas as pd
from typing import Optional, Dict, Any

def extract_cellchat_info(
    weight_csv: str,
    count_csv: str,
    lr_csv: str
):
    """
    读取细胞通讯分析的结果文件
    """    
    weight_df = pd.read_csv(weight_csv, index_col=0)
    count_df = pd.read_csv(count_csv, index_col=0)

    # 获取所有非零的细胞对（发送者 → 接收者）
    cell_pairs = []
    for sender in weight_df.index:
        for receiver in weight_df.columns:
            w = weight_df.loc[sender, receiver]
            c = count_df.loc[sender, receiver]
            if w > 0 or c > 0:
                cell_pairs.append((sender, receiver, w, c))

    # 构建通讯概要
    comm_weight = {}
    comm_count = {}
    for sender, receiver, w, c in cell_pairs:
        key = f"{sender} → {receiver}"
        comm_weight[key] = float(w)
        comm_count[key] = int(c)

    # 2. 读取 L-R 对
    lr_df = pd.read_csv(lr_csv)

    # 添加 direction 列
    lr_df["direction"] = lr_df["source"] + " → " + lr_df["target"]

    # 按 prob 降序排序，取全部（或可加 .head(10)）
    lr_records = lr_df.sort_values("prob", ascending=False).to_dict(orient="records")

    top_lr_pairs = [
        {
            "direction": row["direction"],
            "ligand": row["ligand"],
            "receptor": row["receptor"],
            "pathway_name": row["pathway_name"],
            "prob": float(row["prob"]),
        }
        for row in lr_records
    ]

    # 3. 按 direction + pathway 汇总 prob
    pathway_summary = (
        lr_df.groupby(["direction", "pathway_name"])["prob"]
        .sum()
        .reset_index()
        .sort_values("prob", ascending=False)
        .to_dict(orient="records")
    )

    pathway_summary = [
        {
            "direction": row["direction"],
            "pathway_name": row["pathway_name"],
            "prob": float(row["prob"]),
        }
        for row in pathway_summary
    ]

    # 4. 返回结构化结果
    result = {
        "communication_weight": comm_weight,
        "communication_count": comm_count,
        "top_ligand_receptor_pairs": top_lr_pairs,
        "pathway_summary_by_direction": pathway_summary,
    }
    return result


def load_deg_results(
    deg_csv: str,
    p_adj_threshold: Optional[float] = None,
    log2fc_threshold: Optional[float] = None,
) -> Dict[str, Any]:
    """
    读取差异表达分析结果，可选筛选显著差异基因。

    注意：此工具仅适用于差异表达分析结果文件（包含 p_adj、avg_log2FC 等列）。
    如果文件是模体频次文件，请使用 load_motif_counts 工具。
    """
    df = pd.read_csv(deg_csv)

    # 检查是否为差异表达分析结果文件
    required_columns = ["p_adj", "avg_log2FC"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        # 如果缺少必需列，可能是模体频次文件
        if "pattern" in df.columns and "Number of occurrences" in df.columns:
            return {
                "status": "error",
                "error": "文件格式不匹配：检测到模体频次文件，请使用 load_motif_counts 工具",
                "details": f"缺少差异表达分析必需列: {missing_columns}，但发现模体频次列: pattern, Number of occurrences"
            }
        else:
            return {
                "status": "error",
                "error": "文件格式不匹配：缺少差异表达分析必需列",
                "details": f"缺少列: {missing_columns}，可用列: {list(df.columns)}"
            }

    significant_genes = []
    if p_adj_threshold is not None and log2fc_threshold is not None:
        sig_df = df[
            (df["p_adj"] < p_adj_threshold) &
            (df["avg_log2FC"].abs() > log2fc_threshold)
        ].copy()
        sig_df["regulation"] = sig_df["avg_log2FC"].apply(lambda x: "up" if x > 0 else "down")
        significant_genes = sig_df.to_dict(orient="records")
    else:
        raise ValueError("请提供 p_adj_threshold 和 log2fc_threshold 以筛选显著差异基因。")

    total = len(df)
    up_all = (df["avg_log2FC"] > 0).sum()
    down_all = total - up_all
    sig_count = len(significant_genes)

    result = {
        "status": "success",
        "significant_genes": significant_genes,
        "summary": {
            "total_genes": total,
            "up_genes": int(up_all),
            "down_genes": int(down_all),
            "significant_count": sig_count,
        }
    }
    return result


def load_motif_counts(
    motif_counts_csv: str,
    top_n: int = 10,
) -> Dict[str, Any]:
    """
    读取模体频次统计结果，返回高频模体列表。

    Args:
        motif_counts_csv: 模体频次文件路径（CSV格式）
        top_n: 返回前 N 个高频模体

    Returns:
        {
            "status": "success",
            "total_motifs": int,
            "top_motifs": [
                {"rank": int, "pattern": str, "count": int},
                ...
            ]
        }
    """
    df = pd.read_csv(motif_counts_csv)

    # 检查是否为模体频次文件
    if "pattern" not in df.columns or "Number of occurrences" not in df.columns:
        return {
            "status": "error",
            "error": "文件格式不匹配：不是模体频次文件",
            "details": f"缺少必需列: pattern, Number of occurrences，可用列: {list(df.columns)}"
        }

    # 按频次降序排序
    df_sorted = df.sort_values("Number of occurrences", ascending=False)

    # 提取前 N 个模体
    top_motifs = []
    for idx, row in df_sorted.head(top_n).iterrows():
        pattern = row["pattern"]
        count = row["Number of occurrences"]

        # 解析模式字符串（例如 "('CAF', 'CAF', 'CAF')"）
        try:
            import ast
            cell_types = ast.literal_eval(pattern)
            pattern_str = ", ".join(cell_types)
        except:
            pattern_str = pattern

        top_motifs.append({
            "rank": len(top_motifs) + 1,
            "pattern": pattern_str,
            "count": int(count)
        })

    result = {
        "status": "success",
        "total_motifs": len(df),
        "top_motifs": top_motifs
    }
    return result

