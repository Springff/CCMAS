"""
MedicalReviewer - 生物医学分析质量评估与安全门控
针对空间转录组 motif 分析场景，对 Agent 输出进行多维加权评分与合规检查
"""

import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# 分析严谨性规则：针对本系统场景（motif 分析 / DEG / CellChat）
# 检测 Agent 输出中常见的不严谨表述
SAFETY_RULES = [
    (r'(?:证明|证实)\s*了?\s*\S+(?:导致|引起|造成)',
     "相关性分析不等于因果关系，应使用'提示/关联'而非'证明/导致'"),
    (r'(?:所有|全部)\s*(?:模体|motif|细胞)\s*(?:都|均)',
     "应避免对分析结果做全称断言，需注明统计置信度"),
    (r'(?:显著|significant)\S*(?:差异|变化|富集)(?!.*(?:p[_\-]?val|阈值|<|=))',
     "声称'显著'但未给出统计检验依据（如 p 值或阈值）"),
]


class MedicalReviewer:
    """
    生物医学分析质量评估器（针对空间转录组 motif 分析场景）。

    评估维度与权重：
    - 分析严谨性 (analytical_rigor):   0.4  — motif 统计结论是否有数据支撑
    - 表述合规性 (safety_compliance):   0.3  — 是否存在不严谨表述
    - 证据锚定  (evidence_anchoring):   0.3  — 数值声明是否可追溯到工具输出
    """

    DIMENSIONS = {
        "analytical_rigor": 0.4,
        "safety_compliance": 0.3,
        "evidence_anchoring": 0.3,
    }

    def __init__(self):
        self._rules = [(re.compile(p), msg) for p, msg in SAFETY_RULES]

    def review(
        self,
        agent_output: str,
        hallucination_score: float = 1.0,
        agent_name: str = "",
    ) -> Dict[str, Any]:
        """
        对 Agent 输出进行医学维度评估。

        Args:
            agent_output: Agent 的文本输出
            hallucination_score: 来自 HallucinationGuard 的锚定得分 (0~1)
            agent_name: Agent 名称（用于日志）

        Returns:
            {
                "total_score": float,
                "dimensions": {维度: 分数},
                "safety_gate": {"passed": bool, "violations": list},
                "process_reward": float,  # CoT 过程奖励
            }
        """
        # 1. 安全门控检查
        safety = self._check_safety(agent_output)

        # 2. 各维度评分
        rigor = self._score_analytical_rigor(agent_output)
        evidence = hallucination_score
        safety_score = 1.0 if safety["passed"] else 0.5

        # 3. CoT 过程奖励
        process = self._score_cot_quality(agent_output)

        # 4. 加权融合（结果分 α=0.7 + 过程分 β=0.3）
        result_score = (
            rigor * self.DIMENSIONS["analytical_rigor"]
            + safety_score * self.DIMENSIONS["safety_compliance"]
            + evidence * self.DIMENSIONS["evidence_anchoring"]
        )
        total = result_score * 0.7 + process * 0.3

        dimensions = {
            "analytical_rigor": round(rigor, 4),
            "safety_compliance": round(safety_score, 4),
            "evidence_anchoring": round(evidence, 4),
        }

        logger.info(
            f"[医学评估] {agent_name} 总分: {total:.2f} "
            f"(结果={result_score:.2f}, 过程={process:.2f}) "
            f"维度: {dimensions} "
            f"安全门控: {'通过' if safety['passed'] else '触发'}"
        )

        return {
            "total_score": round(total, 4),
            "dimensions": dimensions,
            "safety_gate": safety,
            "process_reward": round(process, 4),
        }

    def _check_safety(self, text: str) -> Dict[str, Any]:
        """严谨性检查：检测 Agent 输出中的不严谨表述"""
        violations = []

        for pattern, msg in self._rules:
            if pattern.search(text):
                violations.append({"rule": msg})

        return {
            "passed": len(violations) == 0,
            "violations": violations,
        }

    def _score_analytical_rigor(self, text: str) -> float:
        """
        分析严谨性评分（针对空间转录组 motif 分析）。
        检查输出是否包含本系统各阶段应有的关键分析要素，
        而非泛泛的生物学关键词。
        """
        # 各阶段应产出的核心要素（缺失则扣分）
        rigor_indicators = [
            r'(?:motif|模体)\S*\s*(?:\d|频率|出现|显著)',   # motif 有量化描述
            r'(?:节点|边|node|edge)\S*\s*\d',               # 图结构有具体数值
            r'(?:p[_-]?val|显著|significant|阈值)',          # 有统计检验依据
            r'(?:工具|tool|函数|function)\S*(?:返回|结果|输出)', # 明确引用工具结果
        ]
        matches = sum(1 for p in rigor_indicators if re.search(p, text, re.IGNORECASE))
        return min(matches / 2.0, 1.0)

    def _score_cot_quality(self, text: str) -> float:
        """
        CoT 推理过程奖励（针对本系统的 JSON 输出格式）。
        不依赖 <think> 标签，而是检测输出中是否体现了结构化推理：
        - 框架完整性：是否包含分析依据和结论
        - 逻辑稳健性：是否有因果/条件推理连接词
        - 探索深度：是否考虑了多种可能性或备选方案
        """
        score = 0.0

        # 框架完整性：有明确的"依据→结论"结构
        has_basis = bool(re.search(r'(?:根据|基于|由于|因为|结果显示|工具返回)', text))
        has_conclusion = bool(re.search(r'(?:因此|所以|综上|结论|表明|说明)', text))
        if has_basis and has_conclusion:
            score += 0.5
        elif has_basis or has_conclusion:
            score += 0.25

        # 逻辑稳健性：推理步骤间有逻辑连接
        logic_connectors = len(re.findall(
            r'(?:首先|其次|然后|接下来|进一步|此外|同时)', text
        ))
        score += min(logic_connectors / 3.0, 1.0) * 0.25

        # 探索深度：是否考虑多种可能
        if re.search(r'(?:也可能|或者|备选|另一种|不排除|需要进一步)', text):
            score += 0.25

        return min(score, 1.0)
