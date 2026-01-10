# run_cellchat.R
args <- commandArgs(trailingOnly = TRUE)

# 构造路径
input_matrix_path <- args[1]
cell_types_path   <- args[2]
gene_names_path   <- args[3]
output_path       <- args[4]
motifs            <- args[5]

# 创建输出目录
if (!dir.exists(output_path)) {
  dir.create(output_path, recursive = TRUE)
}

# 加载必要的包
library(CellChat)
library(Matrix)

# 读取数据
data.input <- readMM(input_matrix_path)
gene_name  <- read.csv(gene_names_path, header = FALSE)$V1
celltype   <- read.csv(cell_types_path, header = FALSE)$V1

# 构建 meta
meta <- data.frame(labels = celltype, row.names = NULL)

# 设置 Dimnames（确保维度匹配）
if (length(gene_name) != nrow(data.input)) {
  stop("Number of genes in gene_names.txt does not match matrix rows")
}
colnames(data.input) <- 1:ncol(data.input)
rownames(data.input) <- gene_name

# CellChat pipeline
cellchat <- createCellChat(object = data.input, meta = meta, group.by = "labels")
cellchat@DB <- CellChatDB.human
cellchat <- subsetData(cellchat)
cellchat <- identifyOverExpressedGenes(cellchat)
cellchat <- identifyOverExpressedInteractions(cellchat)

# Compute communication probability
cellchat_truncatedMean <- computeCommunProb(cellchat, type = "truncatedMean", trim = 0.1)
cellchat_truncatedMean <- computeCommunProbPathway(cellchat_truncatedMean)
cellchat_truncatedMean <- aggregateNet(cellchat_truncatedMean)

# Save results
df.net <- subsetCommunication(cellchat_truncatedMean)
filename <- paste0("LRs_", motifs, ".csv")
write.csv(df.net, file.path(output_path, filename), row.names = FALSE)
filename <- paste0("weight_truncatedMean_", motifs, ".csv")
write.csv(cellchat_truncatedMean@net$weight, file.path(output_path, filename), row.names = TRUE)
filename <- paste0("count_truncatedMean_", motifs, ".csv")
write.csv(cellchat_truncatedMean@net$count,  file.path(output_path, filename), row.names = TRUE)

