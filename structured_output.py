"""
Structured Output - 结构化输出约束
强制 Agent 输出结构化格式，每个字段都必须标注来源
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)

# 字段名映射：支持中英文字段名
FIELD_NAME_MAPPING = {
    # 英文 -> 中文
    "num_nodes": "节点数",
    "num_edges": "边数",
    "num_cell_types": "节点类型数",
    "node_count": "节点数",
    "edge_count": "边数",
    "cell_type_count": "节点类型数",
    "p_value": "p_value",
    "p_adj": "p_adj",
    "log2fc": "log2fc",
    # 中文 -> 英文
    "节点数": "num_nodes",
    "边数": "num_edges",
    "节点类型数": "num_cell_types",
}


class Claim(BaseModel):
    """声明：每个数值声明都必须标注来源"""
    statement: str = Field(..., description="声明内容")
    value: Optional[float] = Field(None, description="数值")
    unit: Optional[str] = Field(None, description="单位")
    source: str = Field(..., description="来源：工具名、rule、constant")
    source_field: Optional[str] = Field(None, description="来源字段")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度")
    rule: Optional[str] = Field(None, description="如果来源是rule，说明规则")

    @validator('source')
    def validate_source(cls, v):
        """验证来源是否合法"""
        valid_sources = {
            'construct_cell_graph', 'extract_representative_subgraphs',
            'candidate_trangle_motifs', 'calculate_motifs_numbers',
            'identify_motif', 'cellchat', 'DE_analysis',
            'load_deg_results', 'extract_cellchat_info',
            'rule', 'constant'
        }
        if v not in valid_sources:
            raise ValueError(f"无效的来源: {v}，必须是以下之一: {valid_sources}")
        return v

    @validator('source_field')
    def validate_source_field(cls, v, values):
        """验证来源字段"""
        source = values.get('source')
        if source not in ['rule', 'constant'] and not v:
            raise ValueError(f"来源为 {source} 时，必须提供 source_field")
        return v


class StructuredOutput(BaseModel):
    """结构化输出"""
    reasoning: str = Field(..., description="推理过程")
    claims: List[Claim] = Field(default_factory=list, description="声明列表")
    final_output: str = Field(..., description="最终结论")


class StructuredOutputValidator:
    """结构化输出验证器"""

    def __init__(self, tool_results: Dict[str, Any]):
        self.tool_results = tool_results

    def validate(self, output: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证结构化输出"""
        try:
            # 1. 解析 JSON
            structured = StructuredOutput(**output)

            # 2. 验证每个声明
            for claim in structured.claims:
                valid, error = self._validate_claim(claim)
                if not valid:
                    return False, f"声明验证失败: {claim.statement} - {error}"

            return True, None
        except Exception as e:
            return False, f"结构化输出验证失败: {str(e)}"

    def _validate_claim(self, claim: Claim) -> tuple[bool, Optional[str]]:
        """验证单个声明"""
        # 如果来源是工具，验证数值是否匹配
        if claim.source in self.tool_results:
            tool_result = self.tool_results[claim.source]

            # 检查 source_field 是否存在（支持字段名映射）
            if claim.source_field:
                # 尝试直接匹配
                if claim.source_field in tool_result:
                    expected_value = tool_result.get(claim.source_field)
                    if claim.value is not None and expected_value != claim.value:
                        return False, f"数值不匹配: 期望 {expected_value}, 实际 {claim.value}"
                else:
                    # 尝试通过映射匹配
                    mapped_field = FIELD_NAME_MAPPING.get(claim.source_field)
                    if mapped_field and mapped_field in tool_result:
                        expected_value = tool_result.get(mapped_field)
                        if claim.value is not None and expected_value != claim.value:
                            return False, f"数值不匹配: 期望 {expected_value}, 实际 {claim.value}"
                    else:
                        # 列出可用字段
                        available_fields = list(tool_result.keys())
                        return False, f"工具 {claim.source} 没有字段 {claim.source_field}，可用字段: {available_fields}"

        # 如果来源是 rule，验证规则是否正确
        if claim.source == 'rule' and claim.rule:
            # 这里可以实现规则验证逻辑
            pass

        return True, None

    def extract_claims(self, output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取声明列表"""
        try:
            structured = StructuredOutput(**output)
            return [claim.dict() for claim in structured.claims]
        except Exception as e:
            logger.warning(f"提取声明失败: {e}")
            return []


class StructuredOutputParser:
    """结构化输出解析器"""

    @staticmethod
    def parse(text: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """解析文本为结构化输出"""
        import json
        import re

        # 尝试直接解析 JSON
        try:
            output = json.loads(text)
            return output, None
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 代码块
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                output = json.loads(json_match.group(1))
                return output, None
            except json.JSONDecodeError:
                pass

        # 尝试提取 JSON 对象
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                output = json.loads(json_match.group())
                return output, None
            except json.JSONDecodeError:
                pass

        return None, "无法解析为有效的 JSON 格式"

    @staticmethod
    def is_structured_output(text: str) -> bool:
        """检查是否为结构化输出"""
        output, _ = StructuredOutputParser.parse(text)
        if output is None:
            return False

        # 检查是否包含必需字段
        required_fields = ['reasoning', 'final_output']
        return all(field in output for field in required_fields)