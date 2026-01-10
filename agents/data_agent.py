"""
DataAgent - 数据获取与预处理智能体
负责数据下载、细胞图建模与标志性子图提取等
支持工具调用
"""

from autogen import ConversableAgent
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DataAgent:
    """
    数据处理智能体，支持完整工具调用
    """

    SYSTEM_PROMPT = """你是一个专业的生物信息学数据处理专家。你的职责是：

1. **建模细胞图**：根据空间转录组数据中细胞位置构建细胞图
2. **提取代表性子图**：如果细胞图过大，提取具有代表性的子图进行后续分析

你具备以下专业知识：
- 对不同生物学数据类型的理解：转录组数据、基因组数据、蛋白质组数据等
- 常见生物信息学工具的参数和用法
- 处理大规模高通量测序数据的经验

当需要你处理数据时，你应该：
1. 确认数据来源和类型
2. 制定数据处理方案
3. 构建细胞图，了解图的基本属性
4. 当图中节点数超过5000时，提取代表性子图

你是数据流水线的守门人，确保进入分析的数据质量可靠。"""


    def __init__(self, llm_config: Dict[str, Any]):
        """初始化数据智能体"""
        self.agent = ConversableAgent(
            name="DataAgent",
            system_message=self.SYSTEM_PROMPT,
            llm_config=llm_config,
            is_termination_msg=lambda x: "COMPLETE" in str(x.get("content", "")),
        )


    def get_agent(self) -> ConversableAgent:
        """获取AutoGen Agent对象"""
        return self.agent
    

    def register_tools(self, tools: List[Dict[str, Any]] = None):
        """为智能体注册数据处理工具：
        - 将可用工具写入系统提示，帮助模型决策
        - 把工具定义注册到 agent 的 LLM 配置注册
        """
        source_tools = tools if tools else self._get_tools_for_autogen()

        try:
            tools_text = "\n".join([
                f"- {t.get('function') or {}}"
                for t in source_tools
            ])
            tools_section = "\n\n可用工具（DataAgent）:\n" + (tools_text or "- 无可用工具")
            new_prompt = self.SYSTEM_PROMPT + tools_section

            self.agent.update_system_message(new_prompt)
        except Exception:
            logger.debug("无法将工具写入 DataAgent 系统提示", exc_info=True)

        try:
            if 'tools' not in self.agent.llm_config:
                self.agent.llm_config['tools'] = []
            self.agent.llm_config['tools'].extend(source_tools)
        except Exception:
            logger.warning("为 DataAgent 注册工具时失败", exc_info=True)

        logger.info(f"✓ 为 DataAgent 注册 {len(source_tools)} 个数据工具")


    def _get_tools_for_autogen(self) -> List[Dict[str, Any]]:
        """
        获取所有工具定义，用于AutoGen的function_map
        返回工具函数列表供LLM调用

        Aviable tools:
        - construct_cell_graph
        - extract_representative_subgraphs
    
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "construct_cell_graph",
                    "description": "根据空间转录组数据中的细胞物理坐标构建空间邻域图（细胞图）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spatial_data_csv": {
                                "type": "string",
                                "description": "包含细胞类型和空间坐标的输入文件路径(CSV格式)"
                            },
                            "output_graph_gml": {
                                "type": "string",
                                "description": "构建的细胞图保存路径(GML格式)"
                            },
                            "method": {
                                "type": "string",
                                "enum": ["delaunay"],
                                "description": "构建图的算法：Delaunay三角剖分（默认算法）"
                            },
                            # 、固定半径(radius)或K近邻(knn)
                            # "k_neighbors": {
                            #     "type": "integer",
                            #     "description": "如果使用KNN算法，指定每个细胞的邻居数量 (例如: 6)"
                            # },
                            # "radius_cutoff": {
                            #     "type": "number",
                            #     "description": "如果使用Radius算法，指定连接细胞的最大欧氏距离"
                            # }
                        },
                        "required": ["spatial_data_csv", "output_graph_gml"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_representative_subgraphs",
                    "description": "针对过大的细胞图(例如包含超过5000个以上节点的图)，通过采样策略提取具有代表性的子图以降低计算复杂度",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "input_graph_gml": {
                                "type": "string",
                                "description": "已构建的完整大图数据对象或文件路径(GML格式)"
                            },
                            "output_data_pkl": {
                                "type": "string",
                                "description": "提取的子图保存路径（Pickle格式）,所有子图将保存在该文件中"
                            },
                            "subgraph_size": {
                                "type": "integer",
                                "description": "每个子图包含的目标节点（细胞）数量"
                            },
                            "num_subgraphs": {
                                "type": "integer",
                                "description": "需要提取的子图总数量"
                            },
                        },
                        "required": ["input_graph_gml", "output_data_pkl"]
                    }
                }
            }
        ]

