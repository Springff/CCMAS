import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

# 设置matplotlib支持中文和解决PDF字体问题
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['pdf.fonttype'] = 42  # TrueType字体
plt.rcParams['ps.fonttype'] = 42   # 防止PDF中出现Type 3字体

# 读取GML文件
G = nx.read_gml(r'D:\Desktop\Agent\BioInfoMAS\input\T2b5_graph.gml', label='id')

# 创建图形
fig, ax = plt.subplots(figsize=(20, 16))

# 从节点属性中提取位置信息
pos = {}
for node in G.nodes():
    pos[node] = (float(G.nodes[node]['X']), float(G.nodes[node]['Y']))

# 提取节点标签(细胞类型)
labels = nx.get_node_attributes(G, 'label')

# 为不同的细胞类型分配颜色
unique_labels = set(labels.values())

# 高亮CAF和Malignant细胞，其他细胞变灰色
highlight_types = ['CAF', 'Malignant']
color_map = {}
for label in unique_labels:
    if label in highlight_types:
        if label == 'CAF':
            color_map[label] = '#FF6B6B'  # 红色
        elif label == 'Malignant':
            color_map[label] = '#4ECDC4'  # 青色
    else:
        color_map[label] = '#CCCCCC'  # 灰色

# 为每个节点分配颜色
node_colors = [color_map[labels[node]] for node in G.nodes()]

# 绘制网络
nx.draw_networkx_edges(G, pos, alpha=0.2, width=0.5, edge_color='gray', ax=ax)
nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=50, 
                       alpha=0.8, ax=ax)

# 添加图例 - 将高亮的细胞类型放在前面
highlight_types = ['CAF', 'Malignant']
sorted_labels = sorted(highlight_types) + sorted([l for l in unique_labels if l not in highlight_types])

legend_elements = []
for label in sorted_labels:
    if label in highlight_types:
        # 高亮细胞类型使用较大的标记和加粗标签
        legend_elements.append(
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=color_map[label], 
                      markersize=12, label=f'{label} (highlighted)',
                      markeredgewidth=2, markeredgecolor='black')
        )
    else:
        legend_elements.append(
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=color_map[label], 
                      markersize=8, label=label, alpha=0.6)
        )

ax.legend(handles=legend_elements, loc='upper left', 
         bbox_to_anchor=(1.02, 1), fontsize=10)

# 设置标题和坐标轴
ax.set_title('T2b5 Cell Network Graph', fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel('X coordinate', fontsize=12)
ax.set_ylabel('Y coordinate', fontsize=12)

# 添加网络统计信息
caf_count = sum(1 for v in labels.values() if v == 'CAF')
malignant_count = sum(1 for v in labels.values() if v == 'Malignant')
stats_text = (f"Nodes: {G.number_of_nodes()}\n"
             f"Edges: {G.number_of_edges()}\n"
             f"Cell types: {len(unique_labels)}\n\n"
             f"Highlighted:\n"
             f"CAF: {caf_count}\n"
             f"Malignant: {malignant_count}")
ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
        fontsize=10, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()

# 保存为PDF
output_path = r'D:\Desktop\Agent\BioInfoMAS\input\T2b5_graph.pdf'
with PdfPages(output_path) as pdf:
    pdf.savefig(fig, bbox_inches='tight', dpi=300)
    
    # 添加PDF元数据
    d = pdf.infodict()
    d['Title'] = 'T2b5 Cell Network Graph'
    d['Author'] = 'NetworkX Visualization'
    d['Subject'] = 'Cell Network Analysis'
    d['Keywords'] = 'Cell Network, Graph Visualization'
    
print(f"图形已成功保存为 '{output_path}'")
print(f"网络包含 {G.number_of_nodes()} 个节点和 {G.number_of_edges()} 条边")
print(f"包含 {len(unique_labels)} 种细胞类型:")
print(f"\n高亮细胞类型:")
print(f"  - CAF: {caf_count} 个细胞")
print(f"  - Malignant: {malignant_count} 个细胞")
print(f"\n其他细胞类型 (灰色显示):")
for label in sorted(unique_labels):
    if label not in highlight_types:
        count = sum(1 for v in labels.values() if v == label)
        print(f"  - {label}: {count} 个细胞")

plt.close()

# 同时保存为PNG格式作为备份
print("\n同时保存PNG格式...")
fig2, ax2 = plt.subplots(figsize=(20, 16))
nx.draw_networkx_edges(G, pos, alpha=0.2, width=0.5, edge_color='gray', ax=ax2)
nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=50, 
                       alpha=0.8, ax=ax2)

# 重建图例
legend_elements2 = []
for label in sorted_labels:
    if label in highlight_types:
        legend_elements2.append(
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=color_map[label], 
                      markersize=12, label=f'{label} (highlighted)',
                      markeredgewidth=2, markeredgecolor='black')
        )
    else:
        legend_elements2.append(
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=color_map[label], 
                      markersize=8, label=label, alpha=0.6)
        )

ax2.legend(handles=legend_elements2, loc='upper left', 
          bbox_to_anchor=(1.02, 1), fontsize=10)
ax2.set_title('T2b5 Cell Network Graph', fontsize=16, fontweight='bold', pad=20)
ax2.set_xlabel('X coordinate', fontsize=12)
ax2.set_ylabel('Y coordinate', fontsize=12)
ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, 
        fontsize=10, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
plt.tight_layout()
png_path = r'D:\Desktop\Agent\BioInfoMAS\input\T2b5_graph.png'
plt.savefig(png_path, bbox_inches='tight', dpi=300)
print(f"PNG格式已保存为 '{png_path}'")
plt.close()