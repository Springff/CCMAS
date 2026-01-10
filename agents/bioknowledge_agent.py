"""
BioKnowledgeAgent - 生物医学知识智能体
"""

from autogen import ConversableAgent
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class BioKnowledgeAgent:
    """生物医学知识智能体"""

    SYSTEM_PROMPT = """你是一个博学的生物信息学知识专家和文献研究员。你的职责是：

1. **读取结果**：调用工具读取之前生成的结果文件，
2. **解读结果**：用通俗易懂的语言解释数据分析结果的生物学意义
2. **知识整合**：将分析结果与现有的生物学知识相结合,提出深入见解
3. **生成报告**：撰写简明扼要的总结报告，突出关键发现和潜在影响

当执行任务时，你应该：
1. 阅读并理解数据分析结果
2. 解释分析发现的生物学机制
3. 明确区分确定的知识、公认的假设和推测

你是数据分析和生物学知识的桥梁，帮助将冷冰冰的数据转化为可理解的生物学洞见。"""

    def __init__(self, llm_config: Dict[str, Any]):
        """初始化知识智能体"""
        self.agent = ConversableAgent(
            name="KnowledgeAgent",
            system_message=self.SYSTEM_PROMPT,
            llm_config=llm_config,
            is_termination_msg=lambda x: "COMPLETE" in str(x.get("content", "")),
        )

    def get_agent(self) -> ConversableAgent:
        """获取AutoGen Agent对象"""
        return self.agent

    def register_tools(self, tools: List[Dict[str, Any]] = None):
        """为智能体注册知识工具：筛选相关工具并写入系统提示，然后注册到模型层。"""
        source_tools = tools or []
        if not source_tools:
            source_tools = (
                self._get_tools_for_autogen()
                if hasattr(self, "_get_tools_for_autogen")
                else []
            )
        try:
            tools_text = "\n".join(
                [f"- {t.get('function') or {}}" for t in source_tools]
            )
            tools_section = "\n\n可用工具（BioKnowledgeAgent）:\n" + (
                tools_text or "- 无可用工具"
            )
            new_prompt = self.SYSTEM_PROMPT + tools_section

            self.agent.update_system_message(new_prompt)
        except Exception:
            logger.debug("无法将工具写入 BioKnowledgeAgent 系统提示", exc_info=True)

        try:
            if "tools" not in self.agent.llm_config:
                self.agent.llm_config["tools"] = []
            self.agent.llm_config["tools"].extend(source_tools)
        except Exception:
            logger.warning("为 BioKnowledgeAgent 注册工具时失败", exc_info=True)

        logger.info(f"✓ 为 BioKnowledgeAgent 注册 {len(source_tools)} 个知识工具")

    def _get_tools_for_autogen(self) -> List[Dict[str, Any]]:
        """
        获取所有工具定义，用于AutoGen的function_map
        返回工具函数列表供LLM调用
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "load_deg_results",
                    "description": "读取差异表达分析结果，筛选显著差异基因",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "deg_csv": {
                                "type": "string",
                                "description": "差异表达结果文件路径（CSV格式）",
                            },
                            "p_adj_threshold": {
                                "type": "number",
                                "description": "调整后的p值阈值",
                            },
                            "log2fc_threshold": {
                                "type": "number",
                                "description": "log2FoldChange阈值",
                            },
                        },
                        "required": ["deg_csv", "p_adj_threshold", "log2fc_threshold"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_cellchat_info",
                    "description": "提取CellChat分析结果的关键信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "weight_csv": {
                                "type": "string",
                                "description": "CellChat通信权重文件路径（CSV格式）",
                            },
                            "count_csv": {
                                "type": "string",
                                "description": "CellChat通信计数文件路径（CSV格式）",
                            },
                            "lr_csv": {
                                "type": "string",
                                "description": "CellChat配体-受体对文件路径（CSV格式）",
                            },
                        },
                        "required": ["weight_csv", "count_csv", "lr_csv"],
                    },
                },
            },
        ]
