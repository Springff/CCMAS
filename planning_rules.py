"""
Planning Rules - 多步规划硬规则层
提供程序化的决策逻辑，补充 LLM 的软决策
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PlanningRules:
    """多步规划的硬规则层"""

    def __init__(self, config):
        self.config = config

    def should_retry(self, stage_result: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """判断是否需要重试当前 Agent"""
        hal_score = stage_result.get("hallucination_check", {}).get("score", 1.0)
        med_score = stage_result.get("medical_review", {}).get("total_score", 1.0)
        safety_passed = stage_result.get("medical_review", {}).get("safety_gate", {}).get("passed", True)

        # 规则 1：幻觉得分 < 阈值，强制重试
        if isinstance(hal_score, float) and hal_score < self.config.retry_threshold_hallucination:
            reason = f"幻觉得分 {hal_score:.2f} < {self.config.retry_threshold_hallucination}"
            logger.warning(f"[规划规则] {reason}，触发重试")
            return True, reason

        # 规则 2：医学得分 < 阈值 且安全门控触发，跳过该 Agent
        if isinstance(med_score, float) and med_score < self.config.retry_threshold_medical and not safety_passed:
            reason = f"医学得分 {med_score:.2f} < {self.config.retry_threshold_medical} 且安全门控触发"
            logger.warning(f"[规划规则] {reason}，建议跳过")
            return False, reason  # 不重试，直接跳过

        return False, None

    def should_skip(self, stage_result: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """判断是否应该跳过当前 Agent"""
        # 规则：连续多次工具调用失败，跳过
        tool_failures = stage_result.get("tool_failures", 0)
        if tool_failures >= self.config.max_consecutive_failures:
            reason = f"工具失败次数 {tool_failures} >= {self.config.max_consecutive_failures}"
            logger.warning(f"[规划规则] {reason}，建议跳过")
            return True, reason

        return False, None

    def get_next_action(self, stage_result: Dict[str, Any], current_agent: str) -> Dict[str, Any]:
        """获取下一步行动建议"""
        should_retry, retry_reason = self.should_retry(stage_result)
        should_skip, skip_reason = self.should_skip(stage_result)

        if should_skip:
            return {
                "action": "skip",
                "reason": skip_reason,
                "suggestion": f"跳过 {current_agent}，尝试其他 Agent 或结束分析"
            }
        elif should_retry:
            return {
                "action": "retry",
                "reason": retry_reason,
                "suggestion": f"让 {current_agent} 重试当前任务"
            }
        else:
            return {
                "action": "continue",
                "reason": "当前阶段完成",
                "suggestion": "继续下一步"
            }

    def evaluate_stage_quality(self, stage_result: Dict[str, Any]) -> Dict[str, Any]:
        """评估阶段质量"""
        hal_score = stage_result.get("hallucination_check", {}).get("score", 1.0)
        med_score = stage_result.get("medical_review", {}).get("total_score", 1.0)
        safety_passed = stage_result.get("medical_review", {}).get("safety_gate", {}).get("passed", True)
        tool_failures = stage_result.get("tool_failures", 0)

        # 计算综合质量得分
        quality_score = 0.0

        # 幻觉检测得分（权重 0.4）
        if isinstance(hal_score, float):
            quality_score += hal_score * 0.4

        # 医学评估得分（权重 0.4）
        if isinstance(med_score, float):
            quality_score += med_score * 0.4

        # 工具成功率（权重 0.2）
        tool_success_rate = 1.0
        if tool_failures > 0:
            # 假设最多 10 次工具调用
            tool_success_rate = max(0.0, 1.0 - tool_failures / 10.0)
        quality_score += tool_success_rate * 0.2

        # 安全门控惩罚
        if not safety_passed:
            quality_score *= 0.5

        return {
            "quality_score": quality_score,
            "hallucination_score": hal_score,
            "medical_score": med_score,
            "safety_passed": safety_passed,
            "tool_failures": tool_failures,
            "tool_success_rate": tool_success_rate,
            "quality_level": self._get_quality_level(quality_score)
        }

    def _get_quality_level(self, score: float) -> str:
        """获取质量等级"""
        if score >= 0.8:
            return "优秀"
        elif score >= 0.6:
            return "良好"
        elif score >= 0.4:
            return "一般"
        else:
            return "较差"

    def should_terminate(self, results: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """判断是否应该终止整个分析流程"""
        # 检查是否有多个阶段质量较差
        poor_quality_stages = 0
        for stage_name, stage_result in results.items():
            quality = self.evaluate_stage_quality(stage_result)
            if quality["quality_score"] < 0.4:
                poor_quality_stages += 1

        # 如果超过一半的阶段质量较差，建议终止
        if poor_quality_stages > len(results) / 2:
            reason = f"{poor_quality_stages}/{len(results)} 个阶段质量较差"
            logger.warning(f"[规划规则] {reason}，建议终止分析")
            return True, reason

        return False, None