"""
AnalysisAgent - 数据分析智能体
负责运行各种生物信息学分析（差异表达、变异检测、通路富集等）
"""

from autogen import ConversableAgent
from typing import Dict, Any, List, Callable
import logging
import json

logger = logging.getLogger(__name__)


class AnalysisAgent:
    """分析智能体"""

    SYSTEM_PROMPT = """你是一个高度专业的计算生物学分析专家。你的职责是：

1. **差异表达分析**：调用工具识别差异表达的基因
2. **细胞通讯分析**：基于细胞类型及基因表达信息，调用CellChat等工具进行细胞通讯分析

你具备以下专业知识：
- 深入理解各种生物信息学分析方法的原理和适用场景
- 熟悉主流生物信息学方法的参数设置和所需数据
- 能够选择合适的分析方法处理不同类型的数据

当执行分析任务时，你应该：
1. 选择多个可能的motifs
2. 调用工具对每个motif执行分析

你是发现生物学规律的引擎，通过严谨的分析揭示隐藏在数据中的生物学真相。"""

    def __init__(self, llm_config: Dict[str, Any]):
        """初始化分析智能体"""
        self.agent = ConversableAgent(
            name="AnalysisAgent",
            system_message=self.SYSTEM_PROMPT,
            llm_config=llm_config,
            is_termination_msg=lambda x: "COMPLETE" in str(x.get("content", "")),
        )

    def get_agent(self) -> ConversableAgent:
        """获取AutoGen Agent对象"""
        return self.agent

    def register_tools(self, tools: List[Dict[str, Any]] = None):
        """为智能体注册分析工具：筛选相关工具并注册，同时将工具列表写入系统提示。"""
        source_tools = tools if tools else self._get_tools_for_autogen()

        # 把可用工具写入系统提示
        try:
            tools_text = "\n".join(
                [f"- {t.get('function') or {}}" for t in source_tools]
            )
            tools_section = "\n\n可用工具（AnalysisAgent）:\n" + (
                tools_text or "- 无可用工具"
            )
            new_prompt = self.SYSTEM_PROMPT + tools_section

            self.agent.update_system_message(new_prompt)
        except Exception:
            logger.debug("无法将工具写入 AnalysisAgent 系统提示", exc_info=True)

        # 注册到 LLM
        try:
            if "tools" not in self.agent.llm_config:
                self.agent.llm_config["tools"] = []
            self.agent.llm_config["tools"].extend(source_tools)
        except Exception:
            logger.warning("为 AnalysisAgent 注册工具时失败", exc_info=True)

        logger.info(f"✓ 为 AnalysisAgent 注册 {len(source_tools)} 个分析工具")

    def _get_tools_for_autogen(self) -> List[Dict[str, Any]]:
        """
        获取所有工具定义，用于AutoGen的function_map
        返回工具函数列表供LLM调用
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "cellchat",
                    "description": "在细胞图中定位特定motif的位置，提取motif中细胞的基因表达信息信息，使用CellChat工具，对motifs中的细胞进行细胞通讯分析",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "gml_file": {
                                "type": "string",
                                "description": "输入细胞图的GML文件路径",
                            },
                            "target_labels": {
                                "type": "array",
                                "description": "目标motif的节点标签列表",
                            },
                             "spatial_csv": {
                                "type": "string",
                                "description": "包含细胞类型和空间坐标的输入文件路径(CSV格式)",
                            },
                            "gene_matrix_txt": {
                                "type": "string",
                                "description": "基因表达信息文件路径（TXT格式）",
                            },
                            "gene_names_csv": {
                                "type": "string",
                                "description": "基因名称文件路径（CSV格式）",
                            },
                            "output_paths": {
                                "type": "string",
                                "description": "输出文件保存地址（文件夹路径，末尾需包含斜杠/）",
                            },
                            # "edges": {
                            #     "type": "array",
                            #     "description": "目标motif的边列表，格式为[(source1, target1), (source2, target2), ...]",
                            # },
                        },
                        "required": ["gml_file", "target_labels", "spatial_csv", "gene_matrix_txt", "gene_names_csv", "output_paths"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "DE_analysis",
                    "description": "在细胞图中定位特定motif的位置，标记细胞是否存在于motif中，对motifs中的细胞与不在motifs中的同一类型细胞进行差异表达分析",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_cell": {
                                "type": "string",
                                "description": "目标细胞类型",
                            },
                            "gml_file": {
                                "type": "string",
                                "description": "输入细胞图的GML文件路径",
                            },
                            "target_labels": {
                                "type": "array",
                                "description": "目标motif的节点标签列表",
                            },
                             "spatial_csv": {
                                "type": "string",
                                "description": "包含细胞类型和空间坐标的输入文件路径(CSV格式)",
                            },
                            "gene_matrix_txt": {
                                "type": "string",
                                "description": "基因表达信息文件路径（TXT格式）",
                            },
                            "gene_names_csv": {
                                "type": "string",
                                "description": "基因名称文件路径（CSV格式）",
                            },
                            "output_paths": {
                                "type": "string",
                                "description": "输出文件保存地址（文件夹路径，末尾需包含斜杠/）",
                            },
                            # "edges": {
                            #     "type": "array",
                            #     "description": "目标motif的边列表，格式为[(source1, target1), (source2, target2), ...]",
                            # },
                        },
                        "required": ["target_cell","gml_file", "target_labels", "spatial_csv", "gene_matrix_txt", "gene_names_csv", "output_paths"],
                    },
                },
            },
        ]

    