# 0:无关节点
# 1：motif中的Endothelial
# -1：剩余Endothelial


import pandas as pd

label = [0] * 1572
data = pd.read_csv("D:\Desktop\GLM\新数据\PDAC\\T2b5\spatial.csv")
data = data["annotation_majortypes"]
mtf = pd.read_table(
    "D:\Desktop\GLM\新数据\PDAC\\T2b5/extracted_matrix/original/mnmm/mtf&non-motif_label.txt",
    sep="\t",
    header=None,
)
print(mtf[0])
print(mtf)

for i in range(1572):
    print(i)
    print(data[i])
    if data[i] == "Macrophage":
        if mtf[0][i] == 1:
            label[i] = 1
        else:
            label[i] = -1

    print(label[i])
print(label[1])

label = pd.DataFrame(label)
print(label[0][1])

label.to_csv(
    "D:\Desktop\GLM\新数据\PDAC\\T2b5/extracted_matrix/original/mnmm/label.txt",
    index=False,
    header=False,
)
