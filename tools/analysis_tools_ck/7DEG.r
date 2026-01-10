library(Matrix)
library(DESeq2)

mtf = 'mnmm'
region = 'original'
gene_mtx <- paste0('D:/Desktop/GLM/新数据/PDAC/T2b5/sparse_matrix.mtx')
mtx <- readMM(gene_mtx)


gene <- read.csv('D:/Desktop/GLM/新数据/PDAC/T2b5/gene_names.txt',header=FALSE)

group <- read.csv(paste0('D:/Desktop/GLM/新数据/PDAC/T2b5/extracted_matrix/',region,'/',mtf,'/label.txt'))
colnames(group) <- "V1"
group$V1 <- factor(group$V1)
rownames(mtx) <- gene$V1
CCC_dense <- as.matrix(mtx)
CCC_dense <- CCC_dense + 1
# 筛选出group中值为1和 -1的行索引
idx <- which(group$V1 %in% c(1, -1))

# 根据筛选出的行索引，从group中提取对应的数据
group_subset <- group[idx, ]
group_subset <- data.frame(group_subset)
colnames(group_subset) <- "V1"
# 同样根据筛选出的行索引，从CCC_dense中提取对应列的数据（假设CCC_dense的列对应样本，与group的行对应）
CCC_dense_subset <- CCC_dense[, idx]

#DEG
# 检查数据结构ncol(CCC_dense) == nrow(group)
if (ncol(CCC_dense_subset) == nrow(group_subset)) {
  #DEG分析
  dds <- DESeqDataSetFromMatrix(countData = CCC_dense_subset,
                                colData = group_subset,
                                design = ~ V1)
  dds <- DESeq(dds)
  res <- results(dds)
  
  # 保存结果
  path <- paste0("D:/Desktop/GLM/新数据/PDAC/T2b5/output/",mtf,"/DEG/", region, '/')
  if (!file.exists(path)) {
    dir.create(path, recursive = TRUE)
  }
  write.csv(as.data.frame(res), file = paste0(path, mtf, '-Endothelial.csv'))
} else {
  stop("countData 的列数与 colData 的行数不一致。请检查数据文件。")
}


