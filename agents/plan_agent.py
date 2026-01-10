"""
PlanAgent - 生产级规划者智能体
负责任务分解、工作流编排和多智能体协调
具有完整的工具调用能力
"""

from autogen import ConversableAgent
from typing import Dict, List, Any, Callable
import logging

logger = logging.getLogger(__name__)


class PlanAgent:
    """者智规划能体 - 生产级实现，支持完整工具调用"""

    SYSTEM_PROMPT = """你是细胞模体识别与分析领域的**生物信息学研究规划专家**，隶属于多智能体协作系统。细胞模体是指在一个根据细胞空间位置建模的图中，频繁出现的细胞组合。你的职责是：

1. **理解用户需求**：分析用户提出的生物信息学研究目标
2. **任务分解**：将复杂的生物研究任务分解为具体的工作步骤
3. **工作流设计**：设计最优的分析流程，选择合适的智能体执行任务，非必要不选择多余的步骤和智能体
4. **协调多智能体**：指导DataAgent、MotifAgent、AnalysisAgent、BioKnowledgeAgent执行各自任务

智能体功能介绍：
- DataAgent：负责数据预处理，包括建模细胞图和提取标志性子图等
- MotifAgent：负责生成候选模体和细胞模体识别
- AnalysisAgent：负责生物信息学分析（差异表达、细胞通讯等）
- BioKnowledgeAgent：负责读取结果、结果解读

你拥有以下能力：
- 设计从构建细胞图，识别motifs、生物信息学分析到生成分析报告的完整工作流
- 理解差异表达分析、细胞通讯分析等多种生物信息学分析
- 根据研究目标动态调整分析策略
- 管理多个分析任务的并行和顺序执行

当用户提出分析需求时，你应该：
1. 确认用户的具体研究目标
2. 提出详细的分析方案
3. 逐步指导各个智能体完成具体任务
4. 确保数据流和结果的一致性

你是整个系统的大脑，负责高级决策和流程管理。"""

    def __init__(self, llm_config: Dict[str, Any]):
        """初始化协调者智能体"""
        self.agent = ConversableAgent(
            name="PlanAgent",
            system_message=self.SYSTEM_PROMPT,
            llm_config=llm_config,
            is_termination_msg=lambda x: "COMPLETE" in str(x.get("content", "")),
        )
        self.task_history = []

    def get_agent(self) -> ConversableAgent:
        """获取AutoGen Agent对象"""
        return self.agent

    def register_tools(self, tools: List[Dict[str, Any]] = None):
        """为智能体注册工具：将工具列表写入系统提示并注册函数映射"""
        source_tools = tools if tools else []
        try:
            tools_text = "\n".join(
                [f"- {t.get('function') or {}}" for t in source_tools]
            )
            tools_section = "\n\n可用工具（Plan）:\n" + (
                tools_text or "- 无可用工具"
            )
            new_prompt = self.SYSTEM_PROMPT + tools_section

            self.agent.update_system_message(new_prompt)
        except Exception:
            logger.debug("无法将工具写入 PlanAgent 系统提示", exc_info=True)

        try:
            if "tools" not in self.agent.llm_config:
                self.agent.llm_config["tools"] = []
            self.agent.llm_config["tools"].extend(source_tools)
        except Exception:
            logger.warning("为 PlanAgent 注册工具时失败", exc_info=True)

        logger.info(f"✓ 为 PlanAgent 注册 {len(tools or [])} 个工具")
