"""
Data Flow Tracker - 数据流追踪器
追踪每个数值从工具输出到 Agent 输出的完整路径
"""

from typing import Dict, Any, List, Set, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataFlowTracker:
    """数据流追踪器"""

    def __init__(self):
        self.tool_outputs: Dict[str, Any] = {}
        self.agent_claims: List[Dict[str, Any]] = []
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.claim_sources: Dict[str, str] = {}  # 声明 -> 来源映射

    def record_tool_output(self, tool_name: str, output: Any):
        """记录工具输出"""
        self.tool_outputs[tool_name] = output
        self.dependency_graph[tool_name] = set()
        logger.debug(f"[数据流] 记录工具输出: {tool_name}")

    def record_agent_claim(self, claim: Dict[str, Any]):
        """记录 Agent 声明"""
        claim_id = f"claim_{len(self.agent_claims)}"
        claim['id'] = claim_id
        self.agent_claims.append(claim)

        # 构建依赖关系
        source = claim.get('source')
        if source:
            if source not in self.dependency_graph:
                self.dependency_graph[source] = set()
            self.dependency_graph[source].add(claim_id)
            self.claim_sources[claim_id] = source

        logger.debug(f"[数据流] 记录声明: {claim.get('statement')} -> 来源: {source}")

    def verify_claim(self, claim: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证声明是否可追溯到工具输出"""
        source = claim.get('source')

        if not source:
            return False, "声明没有标注来源"

        if source not in self.tool_outputs:
            return False, f"来源 {source} 不在工具输出中"

        # 验证数值
        if claim.get('value') is not None:
            tool_output = self.tool_outputs[source]
            source_field = claim.get('source_field')

            if source_field:
                if source_field not in tool_output:
                    return False, f"工具 {source} 没有字段 {source_field}"

                expected_value = tool_output[source_field]
                if expected_value != claim['value']:
                    return False, f"数值不匹配: 期望 {expected_value}, 实际 {claim['value']}"

        return True, None

    def verify_all_claims(self) -> tuple[bool, List[Dict[str, Any]]]:
        """验证所有声明"""
        all_valid = True
        invalid_claims = []

        for claim in self.agent_claims:
            valid, error = self.verify_claim(claim)
            if not valid:
                all_valid = False
                invalid_claims.append({
                    'claim': claim,
                    'error': error
                })

        return all_valid, invalid_claims

    def get_dependency_graph(self) -> Dict[str, Set[str]]:
        """获取依赖图"""
        return self.dependency_graph

    def visualize_dependencies(self) -> str:
        """可视化依赖关系"""
        lines = ["数据流依赖图:"]
        for source, dependents in self.dependency_graph.items():
            if dependents:
                lines.append(f"  {source} -> {', '.join(dependents)}")
        return '\n'.join(lines)

    def get_claim_trace(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """获取声明的完整追踪信息"""
        for claim in self.agent_claims:
            if claim.get('id') == claim_id:
                source = claim.get('source')
                tool_output = self.tool_outputs.get(source) if source else None

                return {
                    'claim': claim,
                    'source': source,
                    'tool_output': tool_output,
                    'verified': self.verify_claim(claim)[0]
                }
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_claims = len(self.agent_claims)
        verified_claims = sum(1 for claim in self.agent_claims if self.verify_claim(claim)[0])

        return {
            'total_tools': len(self.tool_outputs),
            'total_claims': total_claims,
            'verified_claims': verified_claims,
            'unverified_claims': total_claims - verified_claims,
            'verification_rate': verified_claims / total_claims if total_claims > 0 else 1.0
        }

    def reset(self):
        """重置追踪器"""
        self.tool_outputs.clear()
        self.agent_claims.clear()
        self.dependency_graph.clear()
        self.claim_sources.clear()
        logger.debug("[数据流] 追踪器已重置")

    def export_to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            'tool_outputs': self.tool_outputs,
            'agent_claims': self.agent_claims,
            'dependency_graph': {k: list(v) for k, v in self.dependency_graph.items()},
            'statistics': self.get_statistics()
        }

    def import_from_dict(self, data: Dict[str, Any]):
        """从字典导入"""
        self.tool_outputs = data.get('tool_outputs', {})
        self.agent_claims = data.get('agent_claims', [])
        self.dependency_graph = {k: set(v) for k, v in data.get('dependency_graph', {}).items()}
        self.claim_sources = {claim.get('id'): claim.get('source') for claim in self.agent_claims if claim.get('id')}
        logger.debug("[数据流] 追踪器已从字典导入")