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


library(clusterProfiler)
library(org.Hs.eg.db) 
library(ggplot2)

# 1. 从显著互作结果(df.net)中提取基因
# df.net 是 subsetCommunication 的结果，包含显著的 ligand 和 receptor
if (nrow(df.net) > 0) {
  
  message("Running GO enrichment analysis on significant LR pairs...")
  
  # 提取配体和受体基因，合并并去重
  gene_list <- unique(c(df.net$ligand, df.net$receptor))
  
  # 2. 基因 ID 转换 (Symbol -> Entrez ID)
  # clusterProfiler 需要 Entrez ID
  # 如果是小鼠，请将 OrgDb 改为 org.Mm.eg.db
  eg <- bitr(gene_list, 
             fromType = "SYMBOL", 
             toType = "ENTREZID", 
             OrgDb = "org.Hs.eg.db")
  
  if (nrow(eg) > 0) {
    
    # 3. 运行 GO 富集分析 (Biological Process)
    # 这一步会计算 Gene Ratio 和 q-value
    go_result <- enrichGO(gene = eg$ENTREZID,
                          OrgDb = org.Hs.eg.db,
                          ont = "BP",           # BP: 生物学过程
                          pAdjustMethod = "BH",
                          pvalueCutoff = 0.05,
                          qvalueCutoff = 0.2,
                          readable = TRUE)      # 结果自动转回 Symbol
    
    # 4. 绘制并保存气泡图
    if (!is.null(go_result) && nrow(go_result) > 0) {
      
      go_filename <- paste0("GO_Enrichment_Bubble_", motifs, ".pdf")
      go_filepath <- file.path(output_path, go_filename)
      
      pdf(go_filepath, width = 8, height = 10)
      
      # dotplot 是 clusterProfiler 的标准绘图函数
      # 会自动显示 GeneRatio (横轴) 和 p.adjust/q-value (颜色)
      p <- dotplot(go_result, showCategory = 20) + 
           ggtitle(paste0("GO Enrichment of LR pairs in ", motifs))
      
      print(p)
      dev.off()
      
      message(paste0("GO enrichment plot saved to: ", go_filepath))
      
      # 顺便保存富集结果表格
      write.csv(as.data.frame(go_result), 
                file.path(output_path, paste0("GO_Result_", motifs, ".csv")))
      
    } else {
      message("No significant GO terms enriched.")
    }
    
  } else {
    message("Could not map gene symbols to Entrez IDs.")
  }
  
} else {
  message("No significant interactions to enrich.")
}