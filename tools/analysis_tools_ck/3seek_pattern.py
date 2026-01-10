import igraph as ig
import pandas as pd
from tqdm import tqdm


def load_graph_from_gml(gml_file):
    """
    读取GML文件并返回图对象
    """
    try:
        graph = ig.Graph.Read_GML(gml_file)
        print(f"成功加载图，节点数: {graph.vcount()}, 边数: {graph.ecount()}")
        return graph
    except Exception as e:
        print(f"读取GML文件时出错: {e}")
        return None


# 'D:\\Desktop\\GLM\\新数据\\PDAC\\gml\\U7-a-25.gml'


def find_specific_topology_with_labels_v4(graph, target_labels):
    """
    查找符合特定拓扑结构和节点标签的子图
    拓扑结构: [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3)]
    """
    # 目标拓扑结构的边
    target_edges = [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3)]
    matching_subgraphs = []

    # 将图的顶点按标签分组
    vertices_by_label = {label: [] for label in target_labels}
    for v in range(graph.vcount()):
        if graph.vs[v]["label"] in vertices_by_label:
            vertices_by_label[graph.vs[v]["label"]].append(v)
    edges = set((e.source, e.target) for e in graph.es())
    # 遍历标签组合并检查拓扑
    for v0 in tqdm(vertices_by_label[target_labels[0]]):
        for v1 in vertices_by_label[target_labels[1]]:
            if v0 == v1:
                continue
            for v2 in vertices_by_label[target_labels[2]]:
                if v2 in {v0, v1}:
                    continue
                for v3 in vertices_by_label[target_labels[3]]:
                    if v3 in {v0, v1, v2}:
                        continue

                    if (
                        ((v1, v0) in edges or (v0, v1) in edges)
                        and ((v2, v0) in edges or (v0, v2) in edges)
                        and ((v2, v1) in edges or (v1, v2) in edges)
                        and ((v2, v3) in edges or (v3, v2) in edges)
                        and ((v3, v1) in edges or (v1, v3) in edges)
                    ):
                        matching_subgraphs.append(
                            {
                                "vertices": [v0, v1, v2, v3],
                                "labels": [
                                    graph.vs[v]["label"] for v in [v0, v1, v2, v3]
                                ],
                            }
                        )

    return matching_subgraphs


def main():
    # 加载图
    gml_file = "D:\Desktop\下游分析\PDAC\gml\T2-b-5.gml"
    graph = load_graph_from_gml(gml_file)

    if graph is None:
        return

    # 用户定义的节点标签顺序
    target_labels = [9, 1, 15, 15]

    # 查找符合拓扑结构的子图
    matching_subgraphs = find_specific_topology_with_labels_v4(graph, target_labels)

    # 打印结果
    print(f"找到 {len(matching_subgraphs)} 个匹配的子图:")
    for subgraph in matching_subgraphs[:3]:  # 只打印前3个结果
        print(f"子图顶点: {subgraph['vertices']}, 标签: {subgraph['labels']}")
    basic_data = []
    for i, t in enumerate(matching_subgraphs):

        basic_data.append(
            {
                "triangle_index": i,
                "vertex_ids": ",".join(map(str, t["vertices"])),
                "vertex_labels": ",".join(map(str, t["labels"])),
            }
        )

    pd.DataFrame(basic_data).to_csv(
        f"D:\\Desktop\\GLM\\新数据\\PDAC\\T2b5\\matching_subgraphs_with_911515.csv",
        index=False,
    )


if __name__ == "__main__":
    main()

# nohup python D:/Desktop/GLM/新数据/PDAC/T2b5/3seek_pattern.py > D:/Desktop/GLM/新数据/PDAC/T2b5/output.txt 2> D:/Desktop/GLM/新数据/PDAC/T2b5/error.txt &
