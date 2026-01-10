"""
MotifAgent - 模体识别智能体
负责识别频繁出现的子图等
"""

from autogen import ConversableAgent
from typing import Dict, Any, List, Callable
import logging
import json


logger = logging.getLogger(__name__)


class MotifAgent:
    """模体识别智能体"""

    SYSTEM_PROMPT = """你是一位计算生物学与图论领域的顶尖专家，专注于**细胞图的模体识别**，你可以识别一个细胞图中的motifs，也可以识别在两个细胞图中差异出现motifs。你的核心任务是利用计算工具，从复杂的细胞空间分布数据或互作网络中挖掘频繁子图和具有统计显著性的网络模体。

你具备调用外部工具的能力。在回答涉及数据处理、图算法运算、统计检验的问题时，**必须优先调用工具**，严禁依靠内心猜测生成数值结果。

# Constraints & Rules (约束与准则)
*   **No Hallucination:** 绝对不要编造节点连接关系、频率计数或 P 值。所有定量结果必须来自工具输出。
*   **Robustness:** 如果工具执行报错（如内存溢出、格式错误），请分析错误原因，修正代码或参数后重试，而不是直接放弃。

你是发现细胞空间组织规律的引擎，通过模体识别揭示隐藏在细胞图中的生物学真相。"""


    def __init__(self, llm_config: Dict[str, Any]):
        """初始化数据智能体"""
        self.agent = ConversableAgent(
            name="MotifAgent",
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
        # 如果传入了全局工具定义则优先使用，否则回退到本地定义
        source_tools = tools if tools else self._get_tools_for_autogen()
        # 把可用工具写入系统提示
        try:
            tools_text = "\n".join(
                [f"- {t.get('function') or {}}" for t in source_tools]
            )
            tools_section = "\n\n可用工具（MotifAgent）:\n" + (
                tools_text or "- 无可用工具"
            )
            new_prompt = self.SYSTEM_PROMPT + tools_section

            self.agent.update_system_message(new_prompt)
        except Exception:
            logger.debug("无法将工具写入 MotifAgent 系统提示", exc_info=True)
        # 注册到 LLM
        try:
            if "tools" not in self.agent.llm_config:
                self.agent.llm_config["tools"] = []
            self.agent.llm_config["tools"].extend(source_tools)
        except Exception:
            logger.warning("为 MotifAgent 注册工具时失败", exc_info=True)

        logger.info(f"✓ 为 MotifAgent 注册 {len(source_tools)} 个数据工具")


    def _get_tools_for_autogen(self) -> List[Dict[str, Any]]:
        """
        获取所有工具定义，用于AutoGen的function_map
        返回工具函数列表供LLM调用
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "candidate_trangle_motifs",
                    "description": "生成所有可能的的候选三节点模体组合",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "input_graph_gml": {
                                "type": "integer",
                                "description": "细胞图的保存路径（GML格式）",
                            },
                            "motif_pkl": {
                                "type": "string",
                                "description": "保存候选模体的文件路径（PKL格式）",
                            },
                        },
                        "required": ["input_graph_gml", "motif_pkl"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_motifs_numbers",
                    "description": "计算各个模体在数据集中出现的次数",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "motif_pkl": {
                                "type": "string",
                                "description": "候选模体文件路径（PKL格式）",
                            },
                            "dataset_path": {
                                "type": "string",
                                "description": "细胞图（GML格式）或代表性子图（PKL格式）的文件路径",
                            },
                            "output_csv": {
                                "type": "string",
                                "description": "保存结果的输出文件路径（CSV格式）",
                            },
                        },
                        "required": ["motif_pkl", "dataset_path", "output_csv"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "identify_motif",
                    "description": "识别在单一数据集中出现频率最高的模体，或者在对比数据集中差异出现的模体",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "single_label": {
                                "type": "boolean",
                                "description": "是否在单个数据集上识别motifs，若是则为True，否则为False。默认为True",
                            },
                            "motif_path1": {
                                "type": "string",
                                "description": "模体频率结果文件路径",
                            },
                            "motif_path2": {
                                "type": "string",
                                "description": "备用模体文件路径（可选）",
                            },
                        },
                        "required": ["motif_path1"],
                    },
                },
            },
        ]
