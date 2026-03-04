"""
HallucinationGuard - 幻觉检测与约束模块
对 Agent 输出进行证据锚定验证，检测未经工具证实的数值声明
"""

import re
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


class HallucinationGuard:
    """
    基于证据锚定（Evidence Anchoring）的幻觉检测器。
    核心思路：Agent 输出中的关键数值声明必须能在工具执行结果中找到来源，
    否则标记为潜在幻觉（ungrounded claim）。
    """

    # 医学/生物信息学场景中需要严格验证的数值模式
    CLAIM_PATTERNS = [
        r'(\d+)\s*个节点',
        r'(\d+)\s*个细胞',
        r'(\d+)\s*条边',
        r'(\d+)\s*种细胞类型',
        r'(\d+)\s*个模体',
        r'p[_\-]?(?:value|val|adj)\s*[=<>≤≥]\s*([\d.eE\-]+)',
        r'log2?[Ff]old[Cc]hange\s*[=<>≤≥]\s*([\d.]+)',
        r'出现\s*(\d+)\s*次',
        r'频率[为是]\s*([\d.]+)',
    ]

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self._compiled = [re.compile(p) for p in self.CLAIM_PATTERNS]

    def validate(
        self,
        agent_output: str,
        tool_results: List[str],
        agent_name: str = ""
    ) -> Dict[str, Any]:
        """
        验证 Agent 输出是否存在幻觉风险。

        Returns:
            {
                "grounded": bool,          # 是否全部有据可查
                "score": float,            # 0.0(全幻觉) ~ 1.0(全锚定)
                "total_claims": int,
                "grounded_claims": int,
                "ungrounded_claims": list  # 未锚定的声明
            }
        """
        claims = self._extract_claims(agent_output)
        if not claims:
            return {"grounded": True, "score": 1.0, "total_claims": 0,
                    "grounded_claims": 0, "ungrounded_claims": []}

        evidence_pool = " ".join(str(r) for r in tool_results)
        grounded, ungrounded = [], []

        for value, context in claims:
            # 数字边界匹配：避免 "15" 误匹配到 "1572"
            boundary = re.compile(r'(?<!\d)' + re.escape(value) + r'(?!\d)')
            if boundary.search(evidence_pool):
                grounded.append((value, context))
            else:
                ungrounded.append((value, context))

        total = len(claims)
        score = len(grounded) / total if total > 0 else 1.0

        if ungrounded:
            logger.warning(
                f"[幻觉检测] {agent_name} 发现 {len(ungrounded)} 个未锚定声明 "
                f"(得分: {score:.2f}): {[c for _, c in ungrounded]}"
            )
        else:
            logger.info(
                f"[幻觉检测] {agent_name} 全部 {total} 个数值声明已锚定 (得分: 1.00)"
            )

        return {
            "grounded": len(ungrounded) == 0,
            "score": round(score, 4),
            "total_claims": total,
            "grounded_claims": len(grounded),
            "ungrounded_claims": [c for _, c in ungrounded],
        }

    def _extract_claims(self, text: str) -> List[Tuple[str, str]]:
        """从文本中提取数值声明：返回 [(数值, 上下文片段), ...]

        过滤规则：
        1. 跳过 JSON 代码块中的内容（可能是工具输出）
        2. 跳过包含工具输出标记的内容
        3. 只提取 Agent 自己生成的声明
        """
        claims = []

        # 预处理：移除 JSON 代码块和工具输出片段
        filtered_text = self._filter_tool_outputs(text)

        for pattern in self._compiled:
            for m in pattern.finditer(filtered_text):
                value = m.group(1)
                start = max(0, m.start() - 15)
                end = min(len(filtered_text), m.end() + 15)
                context = filtered_text[start:end].strip()

                # 额外过滤：跳过看起来像工具输出的上下文
                if self._is_tool_output_context(context):
                    continue

                claims.append((value, context))
        return claims

    def _filter_tool_outputs(self, text: str) -> str:
        """过滤掉工具输出片段，只保留 Agent 自己生成的内容"""
        import re

        # 移除 JSON 代码块（可能是工具输出）
        text = re.sub(r'```(?:json)?\s*\{.*?\}\s*```', '', text, flags=re.DOTALL)

        # 移除包含工具输出标记的内容
        text = re.sub(r'工具调用结果：.*?(?=```json|当前轮次|$)', '', text, flags=re.DOTALL)

        # 移除包含 "Observation" 的内容（AutoGen 工具输出标记）
        text = re.sub(r'\[Observation\].*?(?=```json|当前轮次|$)', '', text, flags=re.DOTALL)

        # 移除包含 "result" 字段的 JSON 对象（可能是工具返回）
        text = re.sub(r'\{[^{}]*"result"[^{}]*\}', '', text)

        return text

    def _is_tool_output_context(self, context: str) -> bool:
        """判断上下文是否看起来像工具输出"""
        # 跳过包含工具输出特征的上下文
        tool_output_indicators = [
            '"result"',
            '"status"',
            '"output"',
            '"num_nodes"',
            '"num_edges"',
            '"num_cell_types"',
            '"motif"',
            '"频次"',
            '"出现"',
            '工具调用',
            'Observation',
            '返回结果',
        ]

        for indicator in tool_output_indicators:
            if indicator in context:
                return True

        return False
