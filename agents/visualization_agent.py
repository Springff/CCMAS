"""
VisualizationAgent - 可视化与报告智能体
负责数据可视化、报告生成和结果展示
生产级实现，支持完整工具调用
"""

from autogen import ConversableAgent
from typing import Dict, Any, List, Callable
import logging
import json

logger = logging.getLogger(__name__)


class VisualizationAgent:
    """可视化智能体 - 生产级实现，支持完整工具调用"""

    SYSTEM_PROMPT = """你是一个创意的数据可视化专家和技术文档撰写者。你的职责是：

1. **数据可视化**：创建清晰、专业的图表和图形表示分析结果
   - 火山图展示差异表达基因
   - 热图展示基因表达模式
   - PCA图展示样本聚类
   - 曼哈顿图展示关联分析结果
   - 通路富集气泡图

2. **交互式仪表板**：创建可交互的网页版仪表板
3. **综合报告生成**：撰写专业的分析报告，包含：
   - 研究背景和目标
   - 方法和参数说明
   - 结果展示和图表
   - 结论和讨论
   - 参考文献

4. **结果总结**：为非专业人士总结关键发现

你具备以下技能：
- 对数据可视化设计原则的深入理解
- 掌握多种可视化工具：Plotly、ggplot2、Seaborn等
- 优秀的科技文写作能力
- 能够将复杂的数据转化为直观的视觉呈现
- 理解不同受众的信息需求

当生成可视化和报告时，你应该：
1. 根据数据特性选择最合适的可视化方式
2. 确保图表清晰易读，包含必要的图例和标签
3. 撰写清晰的图表说明和结果解释
4. 遵循科学论文的规范格式
5. 生成可直接用于发表的高质量输出

你是数据与世界沟通的艺术家，通过美观有效的可视化将分析成果呈现给世界。"""

    def __init__(self, llm_config: Dict[str, Any]):
        """初始化可视化智能体"""
        self.agent = ConversableAgent(
            name="VisualizationAgent",
            system_message=self.SYSTEM_PROMPT,
            llm_config=llm_config,
            is_termination_msg=lambda x: "COMPLETE" in str(x.get("content", "")),
        )

    def get_agent(self) -> ConversableAgent:
        """获取AutoGen Agent对象"""
        return self.agent

    def register_tools(self, tools: List[Dict[str, Any]] = None):
        """为智能体注册可视化工具：筛选、写入系统提示并注册到模型层。"""
        source_tools = tools or []
        if not source_tools and hasattr(self, "_get_tools_for_autogen"):
            source_tools = self._get_tools_for_autogen()

        try:
            tools_text = "\n".join(
                [f"- {t.get('function') or {}}" for t in source_tools]
            )
            tools_section = "\n\n可用工具（VisualizationAgent）:\n" + (
                tools_text or "- 无可用工具"
            )
            new_prompt = self.SYSTEM_PROMPT + tools_section

            self.agent.update_system_message(new_prompt)
        except Exception:
            logger.debug("无法将工具写入 VisualizationAgent 系统提示", exc_info=True)

        # 注册到 LLM
        try:
            if "tools" not in self.agent.llm_config:
                self.agent.llm_config["tools"] = []
            self.agent.llm_config["tools"].extend(source_tools)
        except Exception:
            logger.warning("为 VisualizationAgent 注册工具时失败", exc_info=True)

        logger.info(f"✓ 为 VisualizationAgent 注册 {len(source_tools)} 个可视化工具")

    def _get_tools_for_autogen(self) -> List[Dict[str, Any]]:
        """
        获取所有工具定义，用于AutoGen的function_map
        返回工具函数列表供LLM调用
        """
        return [
            # 可视化工具
            {
                "type": "function",
                "function": {
                    "name": "generate_volcano_plot",
                    "description": "生成差异表达分析的火山图",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "deg_results": {
                                "type": "object",
                                "description": "差异表达分析结果",
                            }
                        },
                        "required": ["deg_results"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_heatmap",
                    "description": "生成基因表达热图",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression_data": {
                                "type": "string",
                                "description": "表达数据文件",
                            }
                        },
                        "required": ["expression_data"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_pca_plot",
                    "description": "生成PCA降维分析图",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression_data": {
                                "type": "string",
                                "description": "表达数据文件",
                            }
                        },
                        "required": ["expression_data"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_report",
                    "description": "生成综合分析报告",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "report_title": {
                                "type": "string",
                                "description": "报告标题",
                            },
                            "sections": {
                                "type": "array",
                                "description": "报告章节列表",
                            },
                            "output_format": {
                                "type": "string",
                                "description": "输出格式 (markdown, pdf, html)",
                            },
                        },
                        "required": ["report_title", "sections"],
                    },
                },
            },
        ]
