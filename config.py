"""
CCMAS Configuration - 配置管理模块
解决硬编码问题，提供统一的配置接口
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
from pathlib import Path


@dataclass
class CCMASConfig:
    """CCMAS 配置类"""

    # LLM 配置
    llm_api_key: str
    llm_model_id: str
    llm_base_url: str
    llm_timeout: int = 300
    llm_cache_seed: int = 40
    llm_temperature: float = 0.7

    # 工具配置
    tool_timeout: int = 60
    max_tool_retries: int = 3

    # 幻觉约束配置
    hallucination_threshold: float = 0.6
    enable_hallucination_interception: bool = True
    enable_llm_verification: bool = False  # LLM 验证器（可选，成本较高）

    # 规划配置
    max_stages: int = 8
    max_agent_rounds: int = 10

    # 路径配置
    results_dir: str = "./outputs"
    input_dir: str = "./input"

    # R 脚本路径配置（解决硬编码问题）
    r_scripts_dir: str = "./tools/analysis_tools"

    # 工具注册表配置
    enable_tool_registry: bool = True
    track_tool_success_rate: bool = True

    # 参数验证配置
    enable_parameter_validation: bool = True

    # 工具选择优化配置
    enable_tool_selection: bool = True
    tool_success_rate_threshold: float = 0.5

    # 多步规划配置
    enable_planning_rules: bool = True
    retry_threshold_hallucination: float = 0.5
    retry_threshold_medical: float = 0.6
    max_consecutive_failures: int = 3

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def from_env(cls) -> "CCMASConfig":
        """从环境变量加载配置"""
        load_dotenv()

        return cls(
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_model_id=os.getenv("LLM_MODEL_ID", "gpt-5.1"),
            llm_base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            llm_timeout=int(os.getenv("AUTOGEN_TIMEOUT", "300")),
            llm_cache_seed=int(os.getenv("AUTOGEN_CACHE_SEED", "40")),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            tool_timeout=int(os.getenv("TOOL_TIMEOUT", "60")),
            max_tool_retries=int(os.getenv("MAX_TOOL_RETRIES", "3")),
            hallucination_threshold=float(os.getenv("HALLUCINATION_THRESHOLD", "0.6")),
            enable_hallucination_interception=os.getenv("ENABLE_HALLUCINATION_INTERCEPTION", "true").lower() == "true",
            enable_llm_verification=os.getenv("ENABLE_LLM_VERIFICATION", "false").lower() == "true",
            max_stages=int(os.getenv("MAX_STAGES", "8")),
            max_agent_rounds=int(os.getenv("MAX_AGENT_ROUNDS", "10")),
            results_dir=os.getenv("RESULTS_DIR", "./outputs"),
            input_dir=os.getenv("INPUT_DIR", "./input"),
            r_scripts_dir=os.getenv("R_SCRIPTS_DIR", "./tools/analysis_tools"),
            enable_tool_registry=os.getenv("ENABLE_TOOL_REGISTRY", "true").lower() == "true",
            track_tool_success_rate=os.getenv("TRACK_TOOL_SUCCESS_RATE", "true").lower() == "true",
            enable_parameter_validation=os.getenv("ENABLE_PARAMETER_VALIDATION", "true").lower() == "true",
            enable_tool_selection=os.getenv("ENABLE_TOOL_SELECTION", "true").lower() == "true",
            tool_success_rate_threshold=float(os.getenv("TOOL_SUCCESS_RATE_THRESHOLD", "0.5")),
            enable_planning_rules=os.getenv("ENABLE_PLANNING_RULES", "true").lower() == "true",
            retry_threshold_hallucination=float(os.getenv("RETRY_THRESHOLD_HALLUCINATION", "0.5")),
            retry_threshold_medical=float(os.getenv("RETRY_THRESHOLD_MEDICAL", "0.6")),
            max_consecutive_failures=int(os.getenv("MAX_CONSECUTIVE_FAILURES", "3")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        )

    def get_r_script_path(self, script_name: str) -> str:
        """获取 R 脚本完整路径"""
        return str(Path(self.r_scripts_dir) / script_name)

    def validate(self) -> tuple[bool, Optional[str]]:
        """验证配置是否有效"""
        if not self.llm_api_key:
            return False, "LLM_API_KEY 未设置"

        if self.llm_timeout <= 0:
            return False, "LLM_TIMEOUT 必须大于 0"

        if not 0.0 <= self.hallucination_threshold <= 1.0:
            return False, "HALLUCINATION_THRESHOLD 必须在 0.0 到 1.0 之间"

        if not 0.0 <= self.tool_success_rate_threshold <= 1.0:
            return False, "TOOL_SUCCESS_RATE_THRESHOLD 必须在 0.0 到 1.0 之间"

        if not 0.0 <= self.retry_threshold_hallucination <= 1.0:
            return False, "RETRY_THRESHOLD_HALLUCINATION 必须在 0.0 到 1.0 之间"

        if not 0.0 <= self.retry_threshold_medical <= 1.0:
            return False, "RETRY_THRESHOLD_MEDICAL 必须在 0.0 到 1.0 之间"

        # 检查 R 脚本目录是否存在
        r_scripts_path = Path(self.r_scripts_dir)
        if not r_scripts_path.exists():
            return False, f"R 脚本目录不存在: {self.r_scripts_dir}"

        return True, None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "llm_api_key": "***" if self.llm_api_key else "",
            "llm_model_id": self.llm_model_id,
            "llm_base_url": self.llm_base_url,
            "llm_timeout": self.llm_timeout,
            "llm_cache_seed": self.llm_cache_seed,
            "llm_temperature": self.llm_temperature,
            "tool_timeout": self.tool_timeout,
            "max_tool_retries": self.max_tool_retries,
            "hallucination_threshold": self.hallucination_threshold,
            "enable_hallucination_interception": self.enable_hallucination_interception,
            "enable_llm_verification": self.enable_llm_verification,
            "max_stages": self.max_stages,
            "max_agent_rounds": self.max_agent_rounds,
            "results_dir": self.results_dir,
            "input_dir": self.input_dir,
            "r_scripts_dir": self.r_scripts_dir,
            "enable_tool_registry": self.enable_tool_registry,
            "track_tool_success_rate": self.track_tool_success_rate,
            "enable_parameter_validation": self.enable_parameter_validation,
            "enable_tool_selection": self.enable_tool_selection,
            "tool_success_rate_threshold": self.tool_success_rate_threshold,
            "enable_planning_rules": self.enable_planning_rules,
            "retry_threshold_hallucination": self.retry_threshold_hallucination,
            "retry_threshold_medical": self.retry_threshold_medical,
            "max_consecutive_failures": self.max_consecutive_failures,
            "log_level": self.log_level,
        }