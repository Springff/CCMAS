"""
BioInfoMAS - 生产级多智能体系统
具有完整工具调用能力的LLM驱动生物信息学分析平台
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import re
import ast
from pathlib import Path

from agents.plan_agent import PlanAgent
from agents.data_agent import DataAgent
from agents.motif_agent import MotifAgent
from agents.analysis_agent import AnalysisAgent
from agents.bioknowledge_agent import BioKnowledgeAgent
from autogen_framework import create_function_map
from hallucination_guard import HallucinationGuard
from medical_reviewer import MedicalReviewer
from config import CCMASConfig
from tool_registry import ToolRegistry
from structured_output import StructuredOutputValidator, StructuredOutputParser
from data_flow_tracker import DataFlowTracker
from planning_rules import PlanningRules

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BioInfoMASProduction:

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None, verbose: bool = False, config: Optional[CCMASConfig] = None):
        self.verbose = verbose
        self.config = config or CCMASConfig.from_env()

        # 验证配置
        valid, error = self.config.validate()
        if not valid:
            raise ValueError(f"配置验证失败: {error}")

        # 设置 LLM 配置
        self.llm_config = llm_config or self._setup_llm_config()

        # 初始化工具注册表
        self.tool_registry = ToolRegistry(track_success_rate=self.config.track_tool_success_rate)
        self._register_tools_to_registry()

        # 初始化工具映射（兼容旧代码）
        self.tools = {name: self.tool_registry.get(name) for name in self.tool_registry.list_tools()}

        # 初始化 Agent
        self._init_agents()
        self.register_tools_to_agents()

        # 初始化评估模块
        self.hallucination_guard = HallucinationGuard()
        self.medical_reviewer = MedicalReviewer()

        # 任务历史
        self.task_history = []
        self.current_task = None

        logger.info("✓ BioInfoMAS 生产级系统初始化完成")
        logger.info(f"✓ 配置: {json.dumps(self.config.to_dict(), ensure_ascii=False)}")

    def _setup_llm_config(self) -> Dict[str, Any]:
        """设置 LLM 配置"""
        config = {
            "config_list": [
                {
                    "model": self.config.llm_model_id,
                    "api_key": self.config.llm_api_key,
                    "base_url": self.config.llm_base_url,
                }
            ],
            "timeout": self.config.llm_timeout,
            "cache_seed": self.config.llm_cache_seed,
            "temperature": self.config.llm_temperature,
        }

        logger.info(f"LLM Config: {config['config_list'][0]['model']}")
        return config

    def _register_tools_to_registry(self):
        """注册工具到工具注册表"""
        from tools.data_tools import construct_cell_graph, extract_representative_subgraphs
        from tools.motif_tools import candidate_trangle_motifs, calculate_motifs_numbers, identify_motif
        from tools.analysis_tools import cellchat, DE_analysis
        from tools.biomedknowledge_tools import load_deg_results, load_motif_counts, extract_cellchat_info

        # 数据工具
        self.tool_registry.register(
            "construct_cell_graph",
            construct_cell_graph,
            "构建细胞空间邻接图",
            category="data"
        )
        self.tool_registry.register(
            "extract_representative_subgraphs",
            extract_representative_subgraphs,
            "提取代表性子图",
            category="data"
        )

        # 模体工具
        self.tool_registry.register(
            "candidate_trangle_motifs",
            candidate_trangle_motifs,
            "生成候选三角模体",
            category="motif"
        )
        self.tool_registry.register(
            "calculate_motifs_numbers",
            calculate_motifs_numbers,
            "计算模体数量",
            category="motif"
        )
        self.tool_registry.register(
            "identify_motif",
            identify_motif,
            "识别模体",
            category="motif"
        )

        # 分析工具
        self.tool_registry.register(
            "cellchat",
            cellchat,
            "细胞通讯分析",
            category="analysis"
        )
        self.tool_registry.register(
            "DE_analysis",
            DE_analysis,
            "差异表达分析",
            category="analysis"
        )

        # 知识工具
        self.tool_registry.register(
            "load_deg_results",
            load_deg_results,
            "加载差异表达结果",
            category="knowledge"
        )
        self.tool_registry.register(
            "load_motif_counts",
            load_motif_counts,
            "加载模体频次统计",
            category="knowledge"
        )
        self.tool_registry.register(
            "extract_cellchat_info",
            extract_cellchat_info,
            "提取细胞通讯信息",
            category="knowledge"
        )

        logger.info(f"✓ 已注册 {len(self.tool_registry.list_tools())} 个工具到注册表")

        # 初始化规划规则
        self.planning_rules = PlanningRules(self.config) if self.config.enable_planning_rules else None

    def _init_agents(self):
        
        # 1. PlanAgent - 任务规划
        self.plan_agent = PlanAgent(self.llm_config)        
        
        # 2. DataAgent - 数据获取和预处理
        self.data_agent = DataAgent(self.llm_config)
        
        # 3. MotifAgent - 网络模体识别
        self.motif_agent = MotifAgent(self.llm_config)

        # 4. AnalysisAgent - 数据分析
        self.analysis_agent = AnalysisAgent(self.llm_config)
        
        # 5. BioKnowledgeAgent - 结果解读
        self.biomedknowledge_agent = BioKnowledgeAgent(self.llm_config)

        logger.info("✓ 5个专业化智能体已初始化")

    def register_tools_to_agents(self):

        try:
            self.data_agent.register_tools()
        except Exception:
            logger.warning("为 DataAgent 注册工具失败", exc_info=True)

        try:
            self.motif_agent.register_tools()
        except Exception:
            logger.warning("为 MotifAgent 注册工具失败", exc_info=True)

        try:
            self.analysis_agent.register_tools()
        except Exception:
            logger.warning("为 AnalysisAgent 注册工具失败", exc_info=True)

        try:
            self.biomedknowledge_agent.register_tools()
        except Exception:
            logger.warning("为 BioKnowledgeAgent 注册工具失败", exc_info=True)

        logger.info("✓ 已为各智能体按需注册工具")
        

    def run_analysis(
        self,
        research_goal: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        
        logger.info(f"开始新任务: {research_goal}")
        
        self.current_task = {
            "id": len(self.task_history) + 1,
            "goal": research_goal,
            "parameters": parameters or {},
            "status": "running",
            "results": {}
        }
        
        try:
            # 步骤1: 多步规划 + 执行（每步由 PlanAgent 根据当前状态决定下一步）
            logger.info("[步骤1] 启动多步规划与执行...")
            results = self._execute_adaptive_workflow(research_goal)

            # 步骤2: 分析完成，生成报告
            logger.info("[步骤2] 生成分析报告...")
            self._generate_report(research_goal, results)
            
            self.current_task["results"] = results
            self.current_task["status"] = "completed"
            logger.info("✓ 任务完成")
            
            self.task_history.append(self.current_task)
            
            return {
                "status": "success",
                "task_id": self.current_task["id"],
                "goal": research_goal,
                "results": results
            }
        
        except Exception as e:
            self.current_task["status"] = "error"
            self.current_task["error"] = str(e)
            self.current_task["end_time"] = datetime.now().isoformat()
            
            self.task_history.append(self.current_task)
            
            logger.error(f"❌ 任务错误: {str(e)}", exc_info=True)
            
            return {
                "status": "error",
                "task_id": self.current_task["id"],
                "goal": research_goal,
                "error": str(e)
            }


    def _plan_next_stage(
        self, research_goal: str, history: str, reward: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        多步规划：基于当前状态和奖励信号，让 PlanAgent 决定下一步。
        每次只规划一步，实现 RL 意义上的逐步决策。

        Returns:
            {"agent": str, "stage": str, "description": str} 或 None（表示分析完成）
        """
        plan_agent = self.plan_agent.get_agent()
        valid_agents = {"DataAgent", "MotifAgent", "AnalysisAgent", "BioKnowledgeAgent"}

        reward_text = ""
        if reward:
            hal_score = reward.get('hallucination_score', 'N/A')
            med_score = reward.get('medical_score', 'N/A')

            reward_text = (
                f"\n上一步评分反馈：\n"
                f"- 证据锚定得分: {hal_score}\n"
                f"- 分析质量得分: {med_score}\n"
            )

            # 如果分数太低，PlanAgent 的 prompt 里明确要求它考虑重试策略
            if hal_score != 'N/A' and isinstance(hal_score, float) and hal_score < self.config.retry_threshold_hallucination:
                logger.info(f"[多步规划] 检测到低分 (幻觉={hal_score:.2f})，PlanAgent 将考虑重试策略")
            if med_score != 'N/A' and isinstance(med_score, float) and med_score < self.config.retry_threshold_medical:
                logger.info(f"[多步规划] 检测到低分 (医学={med_score:.2f})，PlanAgent 将考虑重试策略")

        # 增强 prompt：明确要求 PlanAgent 关注分数
        prompt = f"""用户研究目标：{research_goal}

已完成的步骤与结果：
{history if history else "无（尚未开始）"}
{reward_text}
可用智能体：{', '.join(valid_agents)}

【重要决策规则】：
1. 如果证据锚定得分 < {self.config.retry_threshold_hallucination}，建议让当前 Agent 重试
2. 如果分析质量得分 < {self.config.retry_threshold_medical} 且安全门控触发，建议跳过该 Agent
3. 如果连续 {self.config.max_consecutive_failures} 次工具调用失败，建议跳过该 Agent

请根据当前进展和决策规则决定下一步：
- 如果需要重试当前 Agent，返回：{{"agent": "当前Agent名", "stage": "重试", "description": "重试原因"}}
- 如果分析尚未完成，返回：{{"agent": "智能体名", "stage": "阶段名", "description": "任务描述"}}
- 如果所有分析已完成，返回：{{"done": true}}

只返回 JSON，不要其他内容。"""

        try:
            logger.info("[多步规划] 请求 PlanAgent 决定下一步...")
            response = plan_agent.generate_reply(
                messages=[{"role": "user", "content": prompt}],
                sender=plan_agent,
            )
            logger.info(f"[多步规划] PlanAgent 响应: {response}")

            json_match = re.search(r'\{.*\}', str(response), re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
                if decision.get("done"):
                    logger.info("[多步规划] PlanAgent 判断分析已完成")
                    return None
                agent = decision.get("agent", "")
                if agent not in valid_agents:
                    logger.warning(f"[多步规划] 未知 Agent '{agent}'，跳过")
                    return None
                logger.info(f"[多步规划] 下一步: {agent} -> {decision.get('description', '')}")
                return decision
        except Exception as e:
            logger.warning(f"[多步规划] PlanAgent 调用失败: {e}")

        return None

    def _execute_adaptive_workflow(self, research_goal: str) -> Dict[str, Any]:
        """多步规划执行：每步由 PlanAgent 根据当前状态 + 奖励信号决定下一步"""
        results = {}
        history = ""
        reward = None
        max_stages = self.config.max_stages  # 使用配置中的 max_stages

        for step_idx in range(max_stages):
            # 规划：PlanAgent 基于 history + reward 决定下一步
            stage = self._plan_next_stage(research_goal, history, reward)
            if stage is None:
                logger.info(f"[多步规划] 在第 {step_idx + 1} 步结束，PlanAgent 判断分析完成")
                break

            agent_name = stage["agent"]
            stage_name = stage.get("stage", f"step_{step_idx + 1}")
            description = stage.get("description", "")
            logger.info(f"[多步规划] 第 {step_idx + 1} 步: {agent_name} -> {description}")

            # 执行
            stage_result = self._execute_stage(
                agent_name, stage_name, research_goal, description, history
            )
            results[stage_name] = stage_result

            # 应用规划规则（如果启用）
            if self.planning_rules:
                # 评估阶段质量
                quality = self.planning_rules.evaluate_stage_quality(stage_result)
                stage_result["quality_evaluation"] = quality

                # 获取下一步行动建议
                next_action = self.planning_rules.get_next_action(stage_result, agent_name)
                stage_result["next_action"] = next_action

                logger.info(f"[规划规则] {agent_name} 质量评估: {quality['quality_level']} (得分: {quality['quality_score']:.2f})")
                logger.info(f"[规划规则] 下一步行动: {next_action['action']} - {next_action['suggestion']}")

                # 如果建议跳过，记录到 history
                if next_action["action"] == "skip":
                    history += (
                        f"阶段 {stage_name} 使用 {agent_name}\n"
                        f"结果: {stage_result}\n"
                        f"质量评估: {quality}\n"
                        f"规划规则建议: {next_action['suggestion']}\n\n"
                    )
                    continue

            # 构建奖励信号，传递给下一轮规划
            reward = {
                "hallucination_score": stage_result.get(
                    "hallucination_check", {}
                ).get("score", "N/A"),
                "medical_score": stage_result.get(
                    "medical_review", {}
                ).get("total_score", "N/A"),
            }

            history += (
                f"阶段 {stage_name} 使用 {agent_name}\n"
                f"结果: {stage_result}\n"
                f"评分: {reward}\n\n"
            )

        # 检查是否应该终止整个分析流程
        if self.planning_rules:
            should_terminate, terminate_reason = self.planning_rules.should_terminate(results)
            if should_terminate:
                logger.warning(f"[规划规则] {terminate_reason}，提前终止分析")
                results["termination_reason"] = terminate_reason

        return results

    def _execute_stage(
        self,
        agent_name: str,
        stage_name: str,
        research_goal: str,
        stage_description: str = "",
        history: str = ""
    ) -> Dict[str, Any]:
        
        agent_map = {
            "DataAgent": self.data_agent,
            "MotifAgent": self.motif_agent,
            "AnalysisAgent": self.analysis_agent,
            "BioKnowledgeAgent": self.biomedknowledge_agent,
            # "VisualizationAgent": self.visualization_agent
        }
        
        agent_instance = agent_map.get(agent_name)
        if not agent_instance:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        agent = agent_instance.get_agent()
  
        task_prompt = self._build_stage_prompt(history, research_goal, stage_description)
        
        logger.info(f"[LLM调用] 发送任务给 {agent_name}...")
        logger.debug(f"任务提示:\n{task_prompt}")
        
        stage_result = {
            "agent": agent_name,
            "stage": stage_name,
        }
        
        messages = [{"role": "user", "content": task_prompt}]

        final_response = None
        tool_evidence = []  # 收集工具执行结果，用于幻觉检测
        max_rounds = self.config.max_agent_rounds  # 使用配置中的 max_agent_rounds
        tool_failures = 0  # 工具失败计数

        for round_idx in range(max_rounds):
            logger.info(f"[Agent 调用] 轮次 {round_idx+1} -> 使用 {agent_name}.generate_reply()")

            try:
                resp = agent.generate_reply(
                    messages=messages,
                    sender=agent,
                )
            except Exception as e:
                logger.warning(f"agent.generate_reply 调用失败 ({e})", exc_info=True)
                resp = None
            logger.debug(f"[Agent 响应] {agent_name} 原始响应: {resp}")
            
            # 解析工具函数调用请求
            func_call = self._extract_func_calls(resp)

            if func_call:
                calls = func_call if isinstance(func_call, list) else [func_call]
                for call in calls:
                    fname = call.get("name")
                    raw_args = call.get("arguments") or call.get("args") or {}
                    try:
                        if isinstance(raw_args, str):
                            fargs = json.loads(raw_args) if raw_args.strip() else {}
                        else:
                            fargs = raw_args or {}
                    except Exception:
                        fargs = {}

                    logger.info(f"[Thought] {agent_name} 决定调用工具 {fname}")
                    logger.info(f"[Action]  {fname}({fargs})")

                    func = self.tools.get(fname)
                    if not func:
                        available = list(self.tools.keys())
                        error_feedback = {
                            "tool_name": fname,
                            "status": "error",
                            "error_type": "ToolNotFound",
                            "error_message": f"工具 '{fname}' 不存在",
                            "available_tools": available,
                            "hint": f"请从可用工具中选择: {available}"
                        }
                        logger.warning(f"[Self-Heal] 工具未找到: {fname}, 可用: {available}")
                        messages.append({"role": "user", "content": json.dumps(error_feedback, ensure_ascii=False)})
                        continue

                    # 参数验证（如果启用）
                    if self.config.enable_parameter_validation:
                        valid, error = self.tool_registry.validate_parameters(fname, fargs)
                        if not valid:
                            error_feedback = {
                                "tool_name": fname,
                                "status": "error",
                                "error_type": "ParameterValidationError",
                                "error_message": error,
                                "attempted_args": fargs,
                                "hint": f"请检查参数: {error}"
                            }
                            logger.warning(f"[参数验证] {fname} 参数验证失败: {error}")
                            messages.append({"role": "user", "content": json.dumps(error_feedback, ensure_ascii=False)})
                            continue

                    try:
                        if isinstance(fargs, dict):
                            result = func(**fargs)
                        else:
                            result = func(fargs)

                        # 记录工具成功
                        self.tool_registry.record_success(fname)
                    except Exception as e:
                        # 记录工具失败
                        self.tool_registry.record_failure(fname)
                        tool_failures += 1

                        import traceback
                        tb_lines = traceback.format_exc().strip().split('\n')
                        hint_map = {
                            "TypeError": "请检查参数类型和格式是否与工具定义一致",
                            "FileNotFoundError": "请检查文件路径是否正确",
                            "KeyError": "请检查是否缺少必要的参数字段",
                            "ValueError": "请检查参数值是否在有效范围内",
                        }
                        error_feedback = {
                            "tool_name": fname,
                            "status": "error",
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "traceback_summary": tb_lines[-3:],
                            "attempted_args": fargs,
                            "hint": hint_map.get(type(e).__name__, f"请检查参数后重新调用 {fname}")
                        }
                        logger.warning(f"[Self-Heal] {fname} 抛出 {type(e).__name__}: {e}, 结构化反馈已回传给 Agent")
                        messages.append({"role": "user", "content": json.dumps(error_feedback, ensure_ascii=False, default=str)})
                        continue

                    try:
                        func_content = json.dumps({"result": result}, ensure_ascii=False)
                    except Exception:
                        func_content = str(result)

                    # 把函数执行结果回传给 agent
                    logger.info(f"[Observation] {fname} 返回结果 (长度: {len(func_content)})")
                    tool_evidence.append(func_content)

                    # 检测工具返回的错误状态，构造结构化反馈引导 Agent 自我修正
                    if isinstance(result, dict) and result.get("status") == "error":
                        # 记录工具失败
                        self.tool_registry.record_failure(fname)
                        tool_failures += 1

                        error_detail = result.get("details", "")
                        error_feedback = {
                            "tool_name": fname,
                            "status": "error",
                            "error_detail": error_detail,
                            "attempted_args": fargs,
                            "hint": (
                                f"工具 {fname} 返回错误状态。"
                                + ("错误信息为空，可能是底层环境问题或输入数据格式不匹配。" if not error_detail else f"错误信息: {error_detail}。")
                                + "建议：1) 检查输入参数是否正确；2) 确认所需文件存在且格式正确；3) 可尝试调整参数后重试。"
                            )
                        }
                        logger.warning(f"[Self-Heal] {fname} 返回错误状态 (details={'空' if not error_detail else '有'}), 结构化反馈已回传给 Agent")
                        messages.append({"role": "user", "content": json.dumps(error_feedback, ensure_ascii=False, default=str)})
                    else:
                        # 记录工具成功
                        self.tool_registry.record_success(fname)
                        messages.append({"role": "user", "content": fname + "已执行完毕。结果：" + func_content})
                    # 继续下一轮循环，让 agent 基于工具结果决定后续动作
                    continue
            else:
                # agent 未请求函数调用，或 agent 返回为最终文本
                final_response = resp
                logger.info(f"[Agent 响应] {agent_name} 完成 {stage_name} (无更多函数调用请求)")
                break

        if final_response is None:
            final_response = resp

        stage_result["status"] = "completed"
        stage_result["tool_failures"] = tool_failures  # 记录工具失败次数

        # 初始化数据流追踪器
        data_flow_tracker = DataFlowTracker()

        # 记录工具输出到数据流追踪器
        for evidence in tool_evidence:
            try:
                if isinstance(evidence, str):
                    # 解析 JSON 格式的证据
                    data = json.loads(evidence)
                    if isinstance(data, dict) and "result" in data:
                        tool_result = data["result"]
                        tool_name = self._extract_tool_name_from_result(tool_result)
                        if tool_name:
                            data_flow_tracker.record_tool_output(tool_name, tool_result)
            except Exception as e:
                logger.debug(f"[数据流] 解析工具证据失败: {e}")

        # 解析和验证结构化输出
        structured_output = None
        if final_response:
            # 尝试解析结构化输出
            parsed_output, parse_error = StructuredOutputParser.parse(str(final_response))

            if parsed_output:
                # 验证结构化输出
                validator = StructuredOutputValidator(data_flow_tracker.tool_outputs)
                valid, validation_error = validator.validate(parsed_output)

                if valid:
                    structured_output = parsed_output
                    stage_result["structured_output"] = structured_output

                    # 记录声明到数据流追踪器
                    for claim in structured_output.get("claims", []):
                        data_flow_tracker.record_agent_claim(claim)

                    # 验证所有声明
                    all_valid, invalid_claims = data_flow_tracker.verify_all_claims()
                    stage_result["data_flow_verification"] = {
                        "all_valid": all_valid,
                        "invalid_claims": invalid_claims,
                        "statistics": data_flow_tracker.get_statistics()
                    }

                    if not all_valid:
                        logger.warning(f"[数据流验证] {agent_name} 发现 {len(invalid_claims)} 个无效声明")
                else:
                    logger.warning(f"[结构化输出验证] {agent_name} 验证失败: {validation_error}")
                    stage_result["structured_output_error"] = validation_error
            else:
                logger.warning(f"[结构化输出解析] {agent_name} 解析失败: {parse_error}")
                stage_result["structured_output_parse_error"] = parse_error

        # 幻觉检测：验证 Agent 输出是否锚定于工具证据
        if tool_evidence and final_response:
            hal_result = self.hallucination_guard.validate(
                agent_output=str(final_response),
                tool_results=tool_evidence,
                agent_name=agent_name,
            )
            stage_result["hallucination_check"] = hal_result

            # 幻觉拦截（如果启用）
            if self.config.enable_hallucination_interception:
                hal_score = hal_result.get("score", 1.0)
                if hal_score < self.config.hallucination_threshold:
                    logger.warning(f"[幻觉拦截] {agent_name} 幻觉得分 {hal_score:.2f} < {self.config.hallucination_threshold}，触发拦截")
                    # 这里可以添加拦截逻辑，例如重试或跳过
                    # 暂时只记录警告

        # 医学领域多维评估 + 安全门控
        if final_response:
            hal_score = stage_result.get("hallucination_check", {}).get("score", 1.0)
            med_result = self.medical_reviewer.review(
                agent_output=str(final_response),
                hallucination_score=hal_score,
                agent_name=agent_name,
            )
            stage_result["medical_review"] = med_result

        # 尝试解析结构化输出（兼容旧代码）
        try:
            # 如果 final_response 是 dict（raw），把它处理为字符串然后解析
            if isinstance(final_response, dict):
                parsed_final = final_response
            else:
                parsed_final = self._parse_llm_output(final_response, stage_name)
            stage_result["output"] = parsed_final
        except Exception as e:
            logger.warning(f"无法解析LLM输出: {str(e)}")
            stage_result["output"] = {"raw_response": final_response}

        # 保存数据流追踪结果
        stage_result["data_flow"] = data_flow_tracker.export_to_dict()

        return stage_result

    def _extract_tool_name_from_result(self, result: Dict[str, Any]) -> Optional[str]:
        """从工具结果中提取工具名称"""
        if not isinstance(result, dict):
            return None

        # 根据返回的字段推断工具名称
        # construct_cell_graph
        if "节点数" in result or "num_nodes" in result or "节点类型数" in result or "num_cell_types" in result:
            return "construct_cell_graph"
        # extract_representative_subgraphs
        elif "num_extracted_subgraphs" in result:
            return "extract_representative_subgraphs"
        # candidate_trangle_motifs
        elif "候选模体" in result or "candidate_motifs" in result:
            return "candidate_trangle_motifs"
        # calculate_motifs_numbers
        elif "模体频次统计" in result or "motif_counts" in result:
            return "calculate_motifs_numbers"
        # identify_motif
        elif "显著模体" in result or "significant_motifs" in result:
            return "identify_motif"
        # cellchat
        elif "细胞通讯受配体对详细信息保存在" in result or "communication_weight" in result:
            return "cellchat"
        # DE_analysis
        elif "差异表达基因分析结果保存在" in result or "deg_results" in result:
            return "DE_analysis"
        # load_deg_results
        elif "significant_genes" in result and "summary" in result:
            return "load_deg_results"
        # load_motif_counts
        elif "top_motifs" in result and "total_motifs" in result:
            return "load_motif_counts"
        # extract_cellchat_info
        elif "communication_weight" in result and "top_ligand_receptor_pairs" in result:
            return "extract_cellchat_info"

        return None

    
    def _generate_report(self, research_goal, results):
        prompts = f"""用户研究目标: {research_goal}

# 历史步骤与结果:
{results}

请根据以上信息，生成一份详细的研究报告。返回必须为 Markdown 格式。
"""
        agent = self.biomedknowledge_agent.get_agent()
        messages = [{"role": "user", "content": prompts}]
        response = agent.generate_reply(
                        messages=messages,
                        sender=agent,
                    )
        
        report_content = response
        path = os.getenv("RESULTS_DIR", "./outputs")
        filename = path + f"/biomedical_research_report.md"
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"报告已保存至：{os.path.abspath(filename)}")


    def _build_stage_prompt(
        self,
        history: str,
        research_goal: str,
        stage_description: str
    ) -> str:
        """构建阶段任务提示"""

        prompts = f"""用户研究目标: {research_goal}

# 已完成步骤与结果:
{history if history else "无（首个步骤）"}

# 当前步骤:
{stage_description}

请仅输出针对"当前步骤"的回答。
"""

        # 强制结构化输出
        structured_output_instruction = """
# 输出格式要求（重要）

你必须以 JSON 格式输出，包含以下字段：

{
  "reasoning": "你的推理过程，详细说明你的思考步骤",
  "claims": [
    {
      "statement": "你的声明",
      "value": 数值（如果有）,
      "unit": "单位（如果有）",
      "source": "来源（工具名、rule、constant）",
      "source_field": "来源字段（如果来源是工具）",
      "confidence": 0.0-1.0,
      "rule": "规则（如果来源是rule）"
    }
  ],
  "final_output": "最终结论"
}

重要规则：
1. 每个数值声明都必须标注 source
2. 如果数值来自工具，source 必须是工具名，source_field 必须是工具返回的字段名
3. 如果数值来自规则，source 必须是 "rule"，rule 字段说明规则
4. 如果数值是常量，source 必须是 "constant"
5. reasoning 字段必须详细说明你的推理过程
6. claims 列表包含所有数值声明，每个声明都必须有明确的来源

示例：
{
  "reasoning": "1.理解：需要构建细胞图 2.知识：Delaunay三角剖分适用于空间邻域建模 3.推理：节点数1572<5000，无需子图提取 4.结论：调用construct_cell_graph",
  "claims": [
    {
      "statement": "细胞图包含1572个节点",
      "value": 1572,
      "unit": "个节点",
      "source": "construct_cell_graph",
      "source_field": "节点数",
      "confidence": 1.0
    },
    {
      "statement": "不需要降采样",
      "value": null,
      "unit": null,
      "source": "rule",
      "rule": "节点数 < 5000",
      "confidence": 1.0
    }
  ],
  "final_output": "已成功构建细胞图，包含1572个节点和4691条边。由于节点数小于5000，无需进行子图提取。"
}
"""

        cot_instruction = (
            "\n\n# 思维链要求 (Chain-of-Thought)\n"
            "在 JSON 输出中包含 `reasoning` 字段，记录你的推理过程，遵循四阶段结构：\n"
            "1. **理解问题**：明确当前步骤的输入、目标和约束\n"
            "2. **知识回忆**：回忆相关的生物医学领域知识（如细胞类型特征、空间分布规律等）\n"
            "3. **推理分析**：基于数据和知识进行逻辑推理，考虑多种可能性\n"
            "4. **结论**：给出最终决策（调用工具或输出结果）\n"
        )

        tool_instruction = (
            "\n\n# 工具调用\n"
            "如果需要调用工具，在 JSON 中添加 `function_calls` 字段：\n"
            "{\n"
            "  \"reasoning\": \"...\",\n"
            "  \"function_calls\": [\n"
            "    {\"name\": \"工具名\", \"arguments\": {...}}\n"
            "  ],\n"
            "  \"claims\": [...],\n"
            "  \"final_output\": \"...\"\n"
            "}\n\n"
            "工具执行后，系统会将结果回传给你，你需要基于工具结果重新生成完整的 JSON 输出。\n"
            "注意：重新生成时，必须包含完整的 reasoning、claims 和 final_output 字段。"
        )

        return prompts + structured_output_instruction + cot_instruction + tool_instruction


    def _parse_partial_json_field(self, text, field_names):
        for field in field_names:
            pattern = re.compile(rf'([\"\']){field}\1\s*:', re.IGNORECASE)
            match = pattern.search(text)
            if not match:
                continue
            start_search_index = match.end()
            cursor = start_search_index
            list_start = text.find('[', cursor)
            dict_start = text.find('{', cursor)
            start_char = ''
            start_index = -1
            
            if list_start != -1 and (dict_start == -1 or list_start < dict_start):
                start_char = '['
                end_char = ']'
                start_index = list_start
            elif dict_start != -1:
                start_char = '{'
                end_char = '}'
                start_index = dict_start
            else:
                continue 

            balance = 0
            in_string = False
            escape = False
            quote_char = None
            extracted_str = ""
            
            for i, char in enumerate(text[start_index:]):
                current_char = char

                if in_string:
                    if current_char == '\\' and not escape:
                        escape = True
                    elif current_char == quote_char and not escape:
                        in_string = False
                        quote_char = None
                    elif escape:
                        escape = False
                else:
                    if current_char in ['"', "'"]:
                        in_string = True
                        quote_char = current_char
                    elif current_char == start_char:
                        balance += 1
                    elif current_char == end_char:
                        balance -= 1
                
                if balance == 0 and not in_string:
                    extracted_str = text[start_index : start_index + i + 1]
                    break
            
            if extracted_str:
                try:
                    return json.loads(extracted_str)
                except:
                    try:
                        return ast.literal_eval(extracted_str)
                    except:
                        pass
        return None

    def _normalize_arguments(self, args):
        if isinstance(args, dict):
            return args
        if isinstance(args, str):
            try:
                return json.loads(args)
            except:
                try:
                    return ast.literal_eval(args)
                except:
                    return args 
        return args

    def _extract_func_calls(self, resp):
        # 从各种格式的LLM响应中统一提取函数/工具调用信息，支持多种响应格式，确保后续处理能获得一致的函数调用数据结构
        content_text = ""
        extracted_data = None
        final_calls = []

        if isinstance(resp, dict):
            extracted_data = resp
            content_text = str(resp.get("content", "")) 
        elif hasattr(resp, 'content') or hasattr(resp, 'tool_calls'):
            content_text = str(getattr(resp, 'content', '') or "")
            tool_calls = getattr(resp, 'tool_calls', None)
            func_call = getattr(resp, 'function_call', None)
            if tool_calls:
                extracted_data = {"tool_calls": [t.model_dump() if hasattr(t, 'model_dump') else t for t in tool_calls]}
            elif func_call:
                extracted_data = {"function_call": func_call}
        else:
            content_text = str(resp)

        if not extracted_data and content_text:
            clean_text = re.sub(r'^```(json)?\s*', '', content_text, flags=re.MULTILINE)
            clean_text = re.sub(r'\s*```$', '', clean_text, flags=re.MULTILINE).strip()
            
            try:
                extracted_data = json.loads(clean_text)
            except json.JSONDecodeError:
                try:
                    extracted_data = ast.literal_eval(clean_text)
                except:
                    partial_res = self._parse_partial_json_field(clean_text, ["tool_calls", "function_calls", "function_call"])
                    if partial_res:
                        if isinstance(partial_res, list):
                            extracted_data = {"function_calls": partial_res}
                        else:
                            extracted_data = {"function_call": partial_res}

        if extracted_data and isinstance(extracted_data, dict):
            raw_tools = extracted_data.get("tool_calls")
            if raw_tools and isinstance(raw_tools, list):
                for item in raw_tools:
                    func = item.get("function", {})
                    if func:
                        final_calls.append({
                            "name": func.get("name"),
                            "arguments": self._normalize_arguments(func.get("arguments"))
                        })
            
            if not final_calls:
                raw_funcs = extracted_data.get("function_calls")
                if raw_funcs and isinstance(raw_funcs, list):
                    for item in raw_funcs:
                        final_calls.append({
                            "name": item.get("name"),
                            "arguments": self._normalize_arguments(item.get("arguments"))
                        })

            if not final_calls:
                raw_func = extracted_data.get("function_call")
                if raw_func and isinstance(raw_func, dict):
                    final_calls.append({
                        "name": raw_func.get("name"),
                        "arguments": self._normalize_arguments(raw_func.get("arguments"))
                    })

        return final_calls


    def _parse_llm_output(self, response: str, stage_name: str) -> Dict[str, Any]:
        """
        解析LLM输出为结构化数据
        """
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                logger.info(f"✓ 成功解析 {stage_name} 的LLM输出")
                return parsed
        except:
            pass
        
        return {
            "response": response
        }


    def get_task_history(self) -> List[Dict[str, Any]]:
        """获取任务历史"""
        return self.task_history

    def get_current_task(self) -> Optional[Dict[str, Any]]:
        """获取当前任务"""
        return self.current_task