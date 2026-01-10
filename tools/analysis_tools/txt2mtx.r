args <- commandArgs(trailingOnly = TRUE)

matrix_path <- args[1]

library(Matrix)

# 读取txt文件
data <- read.table(matrix_path, header = FALSE)
colnames(data) <- c("row", "col", "value")
data$row <- data$row + 1
data$col <- data$col + 1
# 转换为稀疏矩阵
n_rows <- max(data$row)
n_cols <- max(data$col)
sparse_matrix <- spMatrix(nrow = n_rows, ncol = n_cols, i = data$row, j = data$col, x = data$value)

output_path <- sub("\\.txt$", ".mtx", matrix_path)
# 保存为mtx格式
writeMM(sparse_matrix, output_path)
