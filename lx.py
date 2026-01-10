import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd

# =========================
# 1) Matplotlib 设置（字体 & PDF字体）
# =========================
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42

# =========================
# 2) 读取 GML 图
# =========================
gml_path = r'D:\Desktop\Agent\BioInfoMAS\input\T2b5_graph.gml'
G = nx.read_gml(gml_path, label='id')

# =========================
# 3) 从节点属性中提取坐标 pos
# =========================
pos = {}
for node in G.nodes():
    pos[node] = (float(G.nodes[node]['X']), float(G.nodes[node]['Y']))

# =========================
# 4) 读取 motif_ids.csv，提取所有三角形节点 & 三角形边
# =========================
motif_csv_path = r'D:\Desktop\Agent\BioInfoMAS\input\Cellchat\CAF_CAF_CAF\motif_ids.csv'
df_motif = pd.read_csv(motif_csv_path)

triangle_nodes = set()
triangle_edges = set()  # 用 set 去重边

for ids_str in df_motif['vertex_ids']:
    ids = [x.strip() for x in str(ids_str).split(',')]
    if len(ids) != 3:
        continue

    a, b, c = ids
    triangle_nodes.update([a, b, c])

    triangle_edges.add(tuple(sorted((a, b))))
    triangle_edges.add(tuple(sorted((b, c))))
    triangle_edges.add(tuple(sorted((a, c))))

print(f"[INFO] motif记录数: {len(df_motif)}")
print(f"[INFO] triangle nodes: {len(triangle_nodes)}")
print(f"[INFO] triangle edges(理论): {len(triangle_edges)}")

# =========================
# 5) 提取 Malignant 节点（从label属性）
# =========================
labels = nx.get_node_attributes(G, 'label')
malignant_nodes = {str(node) for node, lab in labels.items() if lab == 'Malignant'}

print(f"[INFO] Malignant nodes: {len(malignant_nodes)}")

# =========================
# 6) 将 G 的边分成 “三角形边” 和 “普通边”
# =========================
highlight_edges = []
other_edges = []

for u, v in G.edges():
    edge_key = tuple(sorted((str(u), str(v))))
    if edge_key in triangle_edges:
        highlight_edges.append((u, v))
    else:
        other_edges.append((u, v))

print(f"[INFO] motif edges(存在于图中): {len(highlight_edges)}")
print(f"[INFO] other edges: {len(other_edges)}")

# =========================
# 7) 颜色设置（优先级：Triangle > Malignant > Other）
# =========================
triangle_color = '#E57373'   # 红色：triangle motif nodes/edges
malignant_color = '#4DB6AC'  # 绿色：Malignant nodes
other_color = '#CCCCCC'      # 灰色：其它节点#E57373 #4DB6AC

# =========================
# 8) 将节点分组（用于分层绘制：灰 → 绿 → 红）
# =========================
triangle_nodes_in_graph = [n for n in G.nodes() if str(n) in triangle_nodes]
malignant_only_nodes = [n for n in G.nodes() if (str(n) in malignant_nodes and str(n) not in triangle_nodes)]
other_nodes = [n for n in G.nodes() if (str(n) not in triangle_nodes and str(n) not in malignant_nodes)]

print(f"[INFO] Triangle nodes(in graph): {len(triangle_nodes_in_graph)}")
print(f"[INFO] Malignant-only nodes: {len(malignant_only_nodes)}")
print(f"[INFO] Other nodes: {len(other_nodes)}")

# =========================
# 9) 绘制网络（分层绘制）
# =========================
fig, ax = plt.subplots(figsize=(20, 16))

# --- 9.1 普通边（灰）
nx.draw_networkx_edges(
    G, pos,
    edgelist=other_edges,
    alpha=0.20, width=1.2,
    edge_color='gray',
    ax=ax
)

# --- 9.2 三角形边（红，高亮）
nx.draw_networkx_edges(
    G, pos,
    edgelist=highlight_edges,
    alpha=0.9, width=2.0,
    edge_color=triangle_color,
    ax=ax
)

# --- 9.3 普通节点（灰）
nx.draw_networkx_nodes(
    G, pos,
    nodelist=other_nodes,
    node_color=other_color,
    node_size=45,
    alpha=0.55,
    ax=ax
)

# --- 9.4 Malignant 节点（绿）
nx.draw_networkx_nodes(
    G, pos,
    nodelist=malignant_only_nodes,
    node_color=malignant_color,
    node_size=60,
    alpha=0.9,
    edgecolors='black',
    linewidths=0.5,
    ax=ax
)

# --- 9.5 Triangle motif 节点（红，最上层）
nx.draw_networkx_nodes(
    G, pos,
    nodelist=triangle_nodes_in_graph,
    node_color=triangle_color,
    node_size=75,
    alpha=0.95,
    edgecolors='black',
    linewidths=0.8,
    ax=ax
)

# =========================
# 10) 图例
# =========================
legend_elements = [
    plt.Line2D([0], [0], marker='o', color='w',
               markerfacecolor=triangle_color,
               markersize=12,
               label='Triangle motif nodes',
               markeredgewidth=1.5, markeredgecolor='black'),
    plt.Line2D([0], [0], color=triangle_color,
               lw=2.5, label='Triangle motif edges'),
    plt.Line2D([0], [0], marker='o', color='w',
               markerfacecolor=malignant_color,
               markersize=11,
               label='Malignant nodes',
               markeredgewidth=1.2, markeredgecolor='black'),
    plt.Line2D([0], [0], marker='o', color='w',
               markerfacecolor=other_color,
               markersize=9,
               label='Other nodes', alpha=0.7),
    plt.Line2D([0], [0], color='gray',
               lw=2, label='Other edges'),
]

ax.legend(handles=legend_elements, loc='upper left',
          bbox_to_anchor=(1.02, 1), fontsize=11)

# =========================
# 11) 标题、坐标轴、统计信息
# =========================
ax.set_title('T2b5 Cell Network Graph (Triangle Motif + Malignant Highlighted)',
             fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel('X coordinate', fontsize=12)
ax.set_ylabel('Y coordinate', fontsize=12)

stats_text = (
    # f"Nodes: {G.number_of_nodes()}\n"
    # f"Edges: {G.number_of_edges()}\n\n"
    # f"Triangle nodes: {len(triangle_nodes_in_graph)}\n"
    # f"Triangle edges: {len(highlight_edges)}\n"
    # f"Malignant nodes (total): {len(malignant_nodes)}\n"
    # f"Malignant-only nodes: {len(malignant_only_nodes)}"
)

ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
        fontsize=10, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()

# =========================
# 12) 保存 PDF + PNG
# =========================
output_pdf_path = r'D:\Desktop\ETAI\Result2\T2b5_graph_triangle_malignant_highlight.pdf'
output_png_path = r'D:\Desktop\ETAI\Result2\T2b5_graph_triangle_malignant_highlight.png'

with PdfPages(output_pdf_path) as pdf:
    pdf.savefig(fig, bbox_inches='tight', dpi=300)
    d = pdf.infodict()
    d['Title'] = 'T2b5 Cell Network Graph (Triangle motif + Malignant)'
    d['Author'] = 'NetworkX Visualization'
    d['Subject'] = 'Triangle motif + Malignant highlighting'
    d['Keywords'] = 'Cell Network, Triangle motif, Malignant'

plt.savefig(output_png_path, bbox_inches='tight', dpi=300)

print(f"\n[OK] PDF saved to: {output_pdf_path}")
print(f"[OK] PNG saved to: {output_png_path}")

plt.close()
