import pandas as pd
from scipy.sparse import csr_matrix
import numpy as np

matrix = pd.read_csv(
    "D:\\Desktop\\GLM\\新数据\\PDAC\\T2b5\\selected_rows.csv", index_col=0
)

print(matrix.iloc[:5, :5])
matrix_T = matrix.T


column_names = matrix.columns
# print(column_names)
# 将列名保存到 txt 文件，每行一个列名

# with open('D:\\Desktop\\GLM\\新数据\\PDAC\\T2b5\\gene_names.txt', 'w') as f:
#     for col in column_names:
#         f.write(col + '\n')

# print("列名已成功保存到 column_names.txt 文件中")


# matrix_T.to_csv('D:\\Desktop\\GLM\\新数据\\PDAC\\T2b5\\selected_rows_T.csv')
result = matrix_T

# 转换为稀疏矩阵
sparse_matrix = csr_matrix(result.values)

# 获取稀疏矩阵的行、列和数据
rows, cols = sparse_matrix.nonzero()
values = sparse_matrix.data

valid_mask = ~np.isnan(values)

# 同步过滤rows、cols和values
rows = rows[valid_mask]
cols = cols[valid_mask]
values = values[valid_mask]

# 检查None值
has_none = None in values
print("是否存在None值:", has_none)

# 检查NaN值
import numpy as np

has_nan = np.isnan(values).any()
print("是否存在NaN值:", has_nan)

# 打印包含空值的位置(如果有)
if has_nan:
    nan_indices = np.where(np.isnan(values))[0]
    print("NaN值的索引位置:", nan_indices)

print(len(rows))
print(len(cols))
print(len(values))
# print(values)
# 创建一个 DataFrame 保存稀疏矩阵的行、列和数据（行和列从 1 开始计数）
sparse_df = pd.DataFrame({"row": rows, "col": cols, "value": values})

# 保存到 txt 文件
sparse_df.to_csv(
    "D:\\Desktop\\GLM\\新数据\\PDAC\\T2b5\\sparse_matrix.txt",
    sep="\t",
    index=False,
    header=False,
)
