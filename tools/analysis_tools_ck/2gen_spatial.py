import pandas as pd

data = pd.read_csv("D:\Desktop\GLM\新数据\PDAC\obs-denoisy.csv")
filtered_df = data[data.iloc[:, 0].str.startswith("c_4_5")]

# 查看结果
print(filtered_df)
print(len(filtered_df))
filtered_df.to_csv("D:\Desktop\GLM\新数据\PDAC\\T2b5\spatial.csv", index=False)
