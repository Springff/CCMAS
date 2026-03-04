"""
Tool Registry - 工具注册表
动态管理工具，追踪成功率，提供工具选择优化
"""

from typing import Dict, Any, Callable, Optional, List
import inspect
import logging
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class ToolMetadata:
    """工具元数据"""
    name: str
    func: Callable
    description: str
    parameters: Dict[str, Any]  # 参数定义：类型、范围、是否必需
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[str] = None
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    category: str = "general"  # 工具分类：data, motif, analysis, knowledge

    @property
    def total_calls(self) -> int:
        """总调用次数"""
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_calls == 0:
            return 1.0  # 默认 100%
        return self.success_count / self.total_calls


class ToolRegistry:
    """工具注册表：动态管理工具，追踪成功率"""

    def __init__(self, track_success_rate: bool = True):
        self._tools: Dict[str, ToolMetadata] = {}
        self._track_success_rate = track_success_rate
        self._categories: Dict[str, List[str]] = {
            "data": [],
            "motif": [],
            "analysis": [],
            "knowledge": [],
            "general": [],
        }

    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
        parameters: Dict[str, Any] = None,
        category: str = "general"
    ):
        """注册工具"""
        # 自动推断参数定义
        if parameters is None:
            parameters = self._infer_parameters(func)

        self._tools[name] = ToolMetadata(
            name=name,
            func=func,
            description=description,
            parameters=parameters,
            category=category
        )

        # 添加到分类
        if category in self._categories:
            self._categories[category].append(name)

        logger.info(f"[工具注册] 已注册工具: {name} (分类: {category})")

    def _infer_parameters(self, func: Callable) -> Dict[str, Any]:
        """从函数签名推断参数定义"""
        sig = inspect.signature(func)
        param_defs = {}

        for param_name, param in sig.parameters.items():
            param_defs[param_name] = {
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "any",
                "default": param.default if param.default != inspect.Parameter.empty else None,
                "required": param.default == inspect.Parameter.empty
            }

        return param_defs

    def get(self, name: str) -> Optional[Callable]:
        """获取工具函数"""
        tool = self._tools.get(name)
        return tool.func if tool else None

    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """获取工具元数据"""
        return self._tools.get(name)

    def get_all_tools(self) -> Dict[str, ToolMetadata]:
        """获取所有工具"""
        return self._tools.copy()

    def get_tools_by_category(self, category: str) -> List[str]:
        """获取指定分类的工具"""
        return self._categories.get(category, [])

    def record_success(self, name: str):
        """记录工具成功"""
        if name in self._tools and self._track_success_rate:
            self._tools[name].success_count += 1
            self._tools[name].last_success = datetime.now().isoformat()
            self._tools[name].last_used = datetime.now().isoformat()
            logger.debug(f"[工具统计] {name} 成功次数: {self._tools[name].success_count}")

    def record_failure(self, name: str):
        """记录工具失败"""
        if name in self._tools and self._track_success_rate:
            self._tools[name].failure_count += 1
            self._tools[name].last_failure = datetime.now().isoformat()
            self._tools[name].last_used = datetime.now().isoformat()
            logger.debug(f"[工具统计] {name} 失败次数: {self._tools[name].failure_count}")

    def get_success_rate(self, name: str) -> float:
        """获取工具成功率"""
        tool = self._tools.get(name)
        if not tool:
            return 1.0  # 默认 100%
        return tool.success_rate

    def suggest_alternative(self, name: str, category: str = None) -> Optional[str]:
        """推荐替代工具（基于成功率）"""
        if name not in self._tools:
            return None

        current_rate = self.get_success_rate(name)
        alternatives = []

        # 如果指定了分类，只在同一分类中查找
        if category:
            candidates = self._categories.get(category, [])
        else:
            candidates = list(self._tools.keys())

        for tool_name in candidates:
            if tool_name != name:
                rate = self.get_success_rate(tool_name)
                if rate > current_rate:
                    alternatives.append((tool_name, rate))

        if alternatives:
            # 返回成功率最高的替代工具
            alternatives.sort(key=lambda x: x[1], reverse=True)
            return alternatives[0][0]

        return None

    def validate_parameters(self, name: str, args: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证参数"""
        tool = self._tools.get(name)
        if not tool:
            return False, f"工具 {name} 不存在"

        for param_name, param_def in tool.parameters.items():
            if param_def.get("required", False) and param_name not in args:
                return False, f"缺少必需参数: {param_name}"

            if param_name in args:
                # 类型检查（简化版）
                expected_type = param_def.get("type", "any")
                if expected_type != "any":
                    # 这里可以添加更严格的类型检查
                    pass

        return True, None

    def get_statistics(self) -> Dict[str, Any]:
        """获取工具统计信息"""
        stats = {
            "total_tools": len(self._tools),
            "tools": {}
        }

        for name, tool in self._tools.items():
            stats["tools"][name] = {
                "success_count": tool.success_count,
                "failure_count": tool.failure_count,
                "success_rate": tool.success_rate,
                "total_calls": tool.total_calls,
                "last_used": tool.last_used,
                "category": tool.category
            }

        return stats

    def save_statistics(self, filepath: str):
        """保存统计信息到文件"""
        stats = self.get_statistics()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        logger.info(f"[工具统计] 统计信息已保存到: {filepath}")

    def load_statistics(self, filepath: str):
        """从文件加载统计信息"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                stats = json.load(f)

            for name, tool_stats in stats.get("tools", {}).items():
                if name in self._tools:
                    self._tools[name].success_count = tool_stats.get("success_count", 0)
                    self._tools[name].failure_count = tool_stats.get("failure_count", 0)
                    self._tools[name].last_used = tool_stats.get("last_used")

            logger.info(f"[工具统计] 统计信息已从 {filepath} 加载")
        except Exception as e:
            logger.warning(f"[工具统计] 加载统计信息失败: {e}")

    def reset_statistics(self):
        """重置统计信息"""
        for tool in self._tools.values():
            tool.success_count = 0
            tool.failure_count = 0
            tool.last_used = None
            tool.last_success = None
            tool.last_failure = None
        logger.info("[工具统计] 统计信息已重置")

    def get_tool_description(self, name: str) -> Optional[str]:
        """获取工具描述"""
        tool = self._tools.get(name)
        return tool.description if tool else None

    def get_tool_parameters(self, name: str) -> Optional[Dict[str, Any]]:
        """获取工具参数定义"""
        tool = self._tools.get(name)
        return tool.parameters if tool else None

    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools