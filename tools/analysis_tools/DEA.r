# ==============================================================================
# Wilcoxon Rank Sum Test
# 适用场景：同类型细胞内部比较，非参数检验，稳健性强
# ==============================================================================
args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 5) {
  stop("Usage: Rscript DE_analysis.r <label_path> <counts_path> <gene_path> <output_dir> <target_cell>")
}

label_path      <- args[1]
counts_path     <- args[2]
gene_path       <- args[3]
output_dir      <- args[4]
target_cell     <- args[5]
# 1. 加载必要的库
library(Matrix)
library(data.table)

# 创建输出目录
if (!dir.exists(output_dir)) dir.create(output_dir, recursive = TRUE)

# 2. 加载数据
cat("=== 1. Loading Data ===\n")
counts_mat <- readMM(counts_path)
gene_names <- as.character(read.csv(gene_path, header = FALSE)$V1)
labels_vec <- read.csv(label_path, header = FALSE)$V1

# 3. 维度校验与预处理
cat("=== 2. Preprocessing ===\n")
if (ncol(counts_mat) != length(labels_vec)) {
  stop("Number of columns in matrix != number of labels")
}

rownames(counts_mat) <- make.unique(gene_names)
colnames(counts_mat) <- paste0("Cell_", 1:ncol(counts_mat))

# 筛选 Label 为 -1 和 1 的细胞
valid_idx <- which(labels_vec %in% c(-1, 1))
if (length(valid_idx) == 0) stop("Error: No cells found with label -1 or 1")

counts_sub <- counts_mat[, valid_idx]
labels_sub <- labels_vec[valid_idx]

# 定义分组
group_vec <- ifelse(labels_sub == 1, "In_motif", "Out_motif")
cat(sprintf("Cells: %d In_motif vs %d Out_motif\n", sum(group_vec == "In_motif"), sum(group_vec == "Out_motif")))

# 4. 数据标准化 (LogNormalize)
cat("=== 3. Normalizing ===\n")
lib_size <- colSums(counts_sub)
norm_mat <- t(t(counts_sub) / lib_size * 10000)
norm_mat@x <- log1p(norm_mat@x) # log(x+1)

# 5. 基因过滤 (加速计算)
# 仅保留在至少 5% 的细胞中表达的基因，剔除无意义的噪音
cat("=== 4. Filtering Genes ===\n")
n_cells <- ncol(norm_mat)
gene_detect_rate <- rowSums(norm_mat > 0) / n_cells
genes_to_keep <- names(which(gene_detect_rate > 0.05)) # 阈值可调，0.05表示5%
cat(sprintf("Testing %d genes (filtered out low expression genes)\n", length(genes_to_keep)))

norm_sub <- norm_mat[genes_to_keep, ]

# 6. 执行 Wilcoxon 检验 (循环计算)
cat("=== 5. Running Wilcoxon Test (This may take a minute) ===\n")

out_cells <- colnames(norm_sub)[group_vec == "Out_motif"]
in_cells  <- colnames(norm_sub)[group_vec == "In_motif"]

# 将稀疏矩阵转为普通矩阵以便快速访问
dense_val <- as.matrix(norm_sub) 

results_list <- lapply(rownames(dense_val), function(gene) {
  val_out <- dense_val[gene, out_cells]
  val_in  <- dense_val[gene, in_cells]
  
  # 核心检验
  test_res <- wilcox.test(val_out, val_in, alternative = "two.sided")
  
  # 计算 Log2 Fold Change (基于 Expm1 还原均值)
  mean_high <- mean(expm1(val_out))
  mean_low  <- mean(expm1(val_in))
  logfc <- log2((mean_high + 1) / (mean_low + 1))
  
  # 计算表达比例
  pct_1 <- sum(val_out > 0) / length(val_out)
  pct_2 <- sum(val_in > 0) / length(val_in)
  
  return(list(
    gene = gene,
    p_val = test_res$p.value,
    avg_log2FC = logfc,
    pct.1 = pct_1,
    pct.2 = pct_2
  ))
})

# 7. 整理结果与保存
cat("=== 6. Saving Results ===\n")
deg_df <- rbindlist(results_list)

# BH 校正
deg_df[, p_adj := p.adjust(p_val, method = "BH")]
# 按 P adj 排序
setorder(deg_df, p_adj)

output_file <- paste0(output_dir, "DEG_Wilcoxon_", target_cell, ".csv")
write.csv(deg_df, output_file, row.names = FALSE)

cat("✅ Success! Results saved to:", output_file, "\n")
cat("Significant genes (adj.p < 0.05):", sum(deg_df$p_adj < 0.05, na.rm=TRUE), "\n")