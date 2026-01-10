"""
Common Utilities and Tool Base Classes
通用工具函数和工具基类
"""

from typing import Any, Dict, List, Optional, Callable
from functools import wraps
import time
import json
import hashlib
from abc import ABC, abstractmethod


def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 重试延迟时间（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_attempts - 1:
                        print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        raise
            return None
        return wrapper
    return decorator


def timer(func: Callable) -> Callable:
    """
    计时装饰器
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper


class ToolRegistry:
    """工具注册表 - 管理所有可用工具"""
    
    def __init__(self):
        self.tools: Dict[str, "BaseTool"] = {}
    
    def register(self, tool: "BaseTool") -> None:
        """注册工具"""
        self.tools[tool.name] = tool
        print(f"Tool '{tool.name}' registered successfully")
    
    def get_tool(self, tool_name: str) -> Optional["BaseTool"]:
        """获取工具"""
        return self.tools.get(tool_name)
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行工具"""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        return tool.execute(**kwargs)
    
    def list_tools(self) -> List[str]:
        """列出所有已注册的工具"""
        return list(self.tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """获取工具信息"""
        tool = self.get_tool(tool_name)
        if not tool:
            return {}
        return tool.get_info()


class BaseTool(ABC):
    """工具基类"""
    
    def __init__(self, name: str, description: str = "", version: str = "1.0"):
        self.name = name
        self.description = description
        self.version = version
        self.parameters: Dict[str, Dict[str, Any]] = {}
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """执行工具"""
        pass
    
    @abstractmethod
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取工具信息"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "parameters": self.parameters
        }
    
    def __repr__(self) -> str:
        return f"Tool(name={self.name}, version={self.version})"


class TaskQueue:
    """任务队列管理"""
    
    def __init__(self, max_size: int = 1000):
        self.queue: List[Dict[str, Any]] = []
        self.max_size = max_size
    
    def enqueue(self, task: Dict[str, Any]) -> bool:
        """入队"""
        if len(self.queue) >= self.max_size:
            return False
        self.queue.append(task)
        return True
    
    def dequeue(self) -> Optional[Dict[str, Any]]:
        """出队"""
        return self.queue.pop(0) if self.queue else None
    
    def size(self) -> int:
        """获取队列大小"""
        return len(self.queue)
    
    def is_empty(self) -> bool:
        """检查队列是否为空"""
        return len(self.queue) == 0
    
    def clear(self) -> None:
        """清空队列"""
        self.queue.clear()


class ResultCache:
    """结果缓存 - 避免重复计算"""
    
    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
    
    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, *args, **kwargs) -> Optional[Any]:
        """获取缓存"""
        key = self._generate_key(*args, **kwargs)
        return self.cache.get(key)
    
    def set(self, result: Any, *args, **kwargs) -> None:
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            # 移除最早的缓存项
            self.cache.pop(next(iter(self.cache)))
        
        key = self._generate_key(*args, **kwargs)
        self.cache[key] = result
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)


def parse_json_response(response: str) -> Dict[str, Any]:
    """解析 JSON 响应"""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # 尝试清理响应
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                return {"raw_response": response}
        return {"raw_response": response}


def dict_to_markdown_table(data: List[Dict[str, Any]]) -> str:
    """将字典列表转换为Markdown表格"""
    if not data:
        return ""
    
    keys = list(data[0].keys())
    table = "| " + " | ".join(keys) + " |\n"
    table += "|" + "|".join(["-" * 10 for _ in keys]) + "|\n"
    
    for row in data:
        table += "| " + " | ".join([str(row.get(key, "")) for key in keys]) + " |\n"
    
    return table


# 全局工具注册表
global_tool_registry = ToolRegistry()
