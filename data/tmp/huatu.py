import igraph as ig
import matplotlib.pyplot as plt

# 读取.gml文件构建图
# graph_path = "/home/chaichunyang/InstructGLM/补充实验/Data/sample/T2b5/change_celltype/0.1_0/subgraph_32_nodes_0.gml"
for i in range(10):
    graph_path = "D:\Desktop\Agent\BioInfoMAS\data\\tmp\subgraph_32_nodes_"+str(i)+".gml"
    # graph_path = "/home/chaichunyang/InstructGLM/data/PDAC/graph/T2-b-5.gml"
    
    G = ig.Graph.Read_GML(graph_path)
    # print(G.vcount())
    # 进行可视化布局，这里使用FR布局（ForceAtlas2算法），你也可以选择其他布局算法，比如"kk"（Kamada-Kawai布局）等
    layout = G.layout_fruchterman_reingold()

    # 绘制图形
    visual_style = {}
    visual_style["vertex_size"] = 10
    # visual_style["vertex_label"] = G.vs["name"]  # 如果节点有名称属性，可以这样设置显示名称，若没有可适当调整
    visual_style["layout"] = layout
    visual_style["bbox"] = (800, 800)  # 设置图像尺寸，可根据需要调整
    visual_style["margin"] = 30  # 图像边距
    visual_style["edge_label"] = None

    ig.plot(G, target="D:\Desktop\Agent\BioInfoMAS\data\\tmp\subgraph_32_nodes_"+str(i)+".pdf", **visual_style)
# 如果你想先显示图像看看效果（可选），可以使用下面这行代码
# ig.plot(G, **visual_style).show()