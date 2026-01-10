"""
BioInfoMAS - 生产级多智能体系统
具有完整工具调用能力的LLM驱动生物信息学分析平台
"""

import os
import json
import logging
from typing import Dict, List, Any, Callable, Optional
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


class BioInfoMASProduction:

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None, verbose: bool = False):
        self.verbose = verbose
        self.llm_config = llm_config or self._setup_llm_config()
        self.tools = create_function_map()
        self._init_agents()
        self.register_tools_to_agents()
        
        self.task_history = []
        self.current_task = None
        
        logger.info("✓ BioInfoMAS 生产级系统初始化完成")

    def _setup_llm_config(self) -> Dict[str, Any]:
        api_key = os.getenv("LLM_API_KEY")
        if not api_key:
            raise ValueError(
                "LLM_API_KEY environment variable not set. "
                "Please configure your LLM API key."
            )
        
        config = {
            "config_list": [
                {
                    "model": os.getenv("LLM_MODEL_ID", "gpt-4"),
                    "api_key": api_key,
                    "base_url": os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
                }
            ],
            "timeout": int(os.getenv("AUTOGEN_TIMEOUT", "300")),
            "cache_seed": int(os.getenv("AUTOGEN_CACHE_SEED", "40")),
            "temperature": 0.7,
        }
        
        logger.info(f"LLM Config: {config['config_list'][0]['model']}")
        return config

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
        
        # # 6. VisualizationAgent - 可视化和报告
        # self.visualization_agent = VisualizationAgent(self.llm_config)
        
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

        # try:
        #     self.visualization_agent.register_tools()
        # except Exception:
        #     logger.warning("为 VisualizationAgent 注册工具失败", exc_info=True)

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
            # 步骤1: 规划智能体分析需求
            logger.info("[步骤1] 规划智能体分析需求...")
            workflow_plan = self._plan_workflow(research_goal)
            self.current_task["workflow_plan"] = workflow_plan
            
            # 步骤2: 执行多智能体工作流
            logger.info("[步骤2] 执行多智能体协作分析...")
            results = self._execute_multi_agent_workflow(
                research_goal,
                workflow_plan
            )

            # 步骤3: 分析完成，生成报告
            logger.info("[步骤3] 生成分析报告...")
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


    def _plan_workflow(self, research_goal: str) -> Dict[str, Any]:
        """
        使用规划智能体规划工作流 
        """
        plan_agent = self.plan_agent.get_agent()
        
        # 构建规划提示
        planning_prompt = f"""
        用户的研究目标：{research_goal}
        
        请分析这个需求，并提出详细的分析工作流方案：
        1. 具体的分析步骤
        2. 需要调用哪些工具和智能体（每个步骤可调用一个智能体）
        
        返回JSON格式的工作流计划，包含以下字段：
        - goal: 研究目标
        - stages: 阶段列表，每个阶段包含 stage, agent, description
        """
        
        try:
            # 调用LLM进行工作流规划
            logger.info("调用 PlanAgent 进行工作流规划...")
            
            response = plan_agent.generate_reply(
                messages=[{"role": "user", "content": planning_prompt}],
                sender=plan_agent,
            )
            
            logger.info(f"LLM规划响应: {response}")
            
            try:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    workflow_plan = json.loads(json_match.group())
                    logger.info(f"✓ 成功解析工作流计划: {len(workflow_plan.get('stages', []))} 个阶段")
                    return workflow_plan
            except json.JSONDecodeError:
                logger.warning("无法解析LLM返回的JSON")
        
        except Exception as e:
            logger.warning(f"LLM调用失败 ({str(e)})")

        return workflow_plan

    def _execute_multi_agent_workflow(
        self,
        research_goal: str,
        workflow_plan: Dict[str, Any]
    ) -> Dict[str, Any]:   
             
        results = {}
        history = ""
        
        for stage in workflow_plan["stages"]:
            stage_name = stage["stage"]
            agent_name = stage["agent"]
            stage_description = stage.get("description", "")
            logger.info(f"执行阶段: {stage_name} (使用 {agent_name})")
            
            stage_task = self._execute_stage(
                agent_name,
                stage_name,
                workflow_plan["stages"],
                research_goal,
                stage_description,
                history
            )
            
            history += f"阶段 {stage_name} 使用 {agent_name} \n结果: {stage_task}\n\n"
            results[stage_name] = stage_task
        
        return results

    def _execute_stage(
        self,
        agent_name: str,
        stage_name: str,
        workflow_plan: str,
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
  
        task_prompt = self._build_stage_prompt(history, workflow_plan, research_goal, stage_description)
        
        logger.info(f"[LLM调用] 发送任务给 {agent_name}...")
        logger.debug(f"任务提示:\n{task_prompt}")
        
        stage_result = {
            "agent": agent_name,
            "stage": stage_name,
        }
        
        messages = [{"role": "user", "content": task_prompt}]

        final_response = None
        max_rounds = 10
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
            print("当前轮次使用",agent_name,"的响应：", resp)
            
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

                    logger.info(f"{agent_name} 请求函数调用: {fname} args={fargs}")

                    func = self.tools.get(fname)
                    if not func:
                        err_msg = f"工具未找到: {fname}"
                        logger.warning(err_msg)
                        messages.append({"role": "user", "content": json.dumps({"error": err_msg}, ensure_ascii=False)})
                        continue

                    try:
                        if isinstance(fargs, dict):
                            result = func(**fargs)
                        else:
                            result = func(fargs)
                    except Exception as e:
                        logger.error(f"执行工具 {fname} 时出错: {str(e)}", exc_info=True)
                        messages.append({"role": "user", "content": json.dumps({"error": str(e)}, ensure_ascii=False)})
                        continue

                    try:
                        func_content = json.dumps({"result": result}, ensure_ascii=False)
                    except Exception:
                        func_content = str(result)

                    # 把函数执行结果回传给 agent
                    messages.append({"role": "user", "content": fname +"已执行完毕。结果："+func_content})
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

        # 尝试解析结构化输出
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
        
        return stage_result

    
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
        workflow_plan: Dict[str, Any],
        research_goal: str,
        stage_description: List[str]
    ) -> str:
        """构建阶段任务提示"""
        
        prompts = f"""用户研究目标: {research_goal}

# 完整计划:
{workflow_plan}

# 历史步骤与结果:
{history if history else "无"}

# 当前步骤:
{stage_description}

请仅输出针对"当前步骤"的回答:
"""
        
        instruction = (
            "\n\n请注意：返回必须为 JSON 格式。若需要调用本地工具，请在 JSON 中包含 `function_calls` 字段，"
            "它应为数组，数组元素为 {\"name\": 工具名, \"arguments\": {...}}。"
            "一旦工具被执行，系统会将工具执行结果回传给你，之后你可以基于结果继续生成最终的 `final_output` 字段。"
        )

        return prompts + instruction


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
        import re
        
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

    # def save_results(self, output_dir: str = "./results") -> str:
    #     os.makedirs(output_dir, exist_ok=True)

    #     if self.current_task:
    #         task_file = os.path.join(output_dir, f"task_{self.current_task['id']}.json")
    #         with open(task_file, 'w', encoding='utf-8') as f:
    #             json.dump(self.current_task, f, ensure_ascii=False, indent=2)
    #         logger.info(f"✓ 任务结果已保存: {task_file}")
        
    #     # 保存历史记录
    #     if self.task_history:
    #         history_file = os.path.join(output_dir, "task_history.json")
    #         with open(history_file, 'w', encoding='utf-8') as f:
    #             json.dump(self.task_history, f, ensure_ascii=False, indent=2)
    #         logger.info(f"✓ 任务历史已保存: {history_file}")
        
    #     return output_dir

    def get_task_history(self) -> List[Dict[str, Any]]:
        """获取任务历史"""
        return self.task_history

    def get_current_task(self) -> Optional[Dict[str, Any]]:
        """获取当前任务"""
        return self.current_task


    def _function_call(self, messages, Agent):
        max_rounds = 5
        for _ in range(max_rounds):
            try:            
                response = Agent.generate_reply(
                    messages = messages,
                    sender=Agent,
                ) 
                logger.info(f"LLM响应: {response}")
            except Exception as e:
                logger.warning(f"LLM调用失败 ({str(e)})")
            
            func_call = None
            parsed_resp_text = None

            if isinstance(response, dict):
                func_call = response.get("function_call") or response.get("function_calls")
                parsed_resp_text = response.get("content")
            else:
                parsed_resp_text = str(response or "")
                try:
                    import re
                    json_match = re.search(r'\{.*\}', parsed_resp_text, re.DOTALL)
                    if json_match:
                        parsed_json = json.loads(json_match.group())
                        func_call = parsed_json.get("function_call") or parsed_json.get("function_calls")
                except Exception:
                    func_call = None

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

                    logger.info(f"请求函数调用: {fname} args={fargs}")
                    func = self.tools.get(fname)
                    if not func:
                        err_msg = f"工具未找到: {fname}"
                        messages.append({"role": "user", "content": json.dumps({"error": err_msg}, ensure_ascii=False)})
                        logger.warning(err_msg)
                        continue

                    try:
                        if isinstance(fargs, dict):
                            result = func(**fargs)
                        else:
                            result = func(fargs)
                    except Exception as e:
                        logger.error(f"执行工具 {fname} 时出错: {str(e)}", exc_info=True)
                        messages.append({"role": "user", "content": json.dumps({"error": str(e)}, ensure_ascii=False)})
                        continue

                    try:
                        func_content = json.dumps({"result": result}, ensure_ascii=False)
                    except Exception:
                        func_content = str(result)
                    messages.append({"role": "user", "content": fname +"已执行完毕。结果："+func_content})
                    continue
            else:
                break
        return response
        

    # def construct_graph(self, research_goal) :
    #     """
    #     使用数据处理智能体构建细胞图
    #     """
    #     Agent = self.data_agent.get_agent()
    #     instruction = (
    #         "\n\n请注意：返回必须为 JSON 格式。若需要调用本地工具，请在 JSON 中包含 `function_calls` 字段，"
    #         "它应为数组，数组元素为 {\"name\": 工具名, \"arguments\": {...}}。"
    #         "一旦工具被执行，系统会将工具执行结果回传给你，之后你可以基于结果继续生成最终的 `final_output` 字段。"
    #     )
    #     prompt = research_goal + instruction
    #     messages = [{"role": "user", "content": prompt}]
    #     response = self._function_call(messages, Agent)
    #     return response


    def motif_identification(self, research_goal) :
        """
        使用模体识别智能体进行模体识别
        """
        Agent = self.motif_agent.get_agent()
        instruction = (
            "\n\n请注意：返回必须为 JSON 格式。若需要调用本地工具，请在 JSON 中包含 `function_calls` 字段，"
            "它应为数组，数组元素为 {\"name\": 工具名, \"arguments\": {...}}。"
            "一旦工具被执行，系统会将工具执行结果回传给你，之后你可以基于结果继续生成最终的 `final_output` 字段。"
        )
        prompt = research_goal + instruction
        messages = [{"role": "user", "content": prompt}]
        response = self._function_call(messages, Agent)
        return response
    

    def agent_demonstration(self, agent_name, research_goal) :
        agent_map = {
            "DataAgent": self.data_agent,
            "MotifAgent": self.motif_agent,
            "AnalysisAgent": self.analysis_agent,
            "KnowledgeAgent": self.biomedknowledge_agent,
            # "VisualizationAgent": self.visualization_agent,
        }
        agent_instance = agent_map.get(agent_name)
        Agent = agent_instance.get_agent()
        instruction = (
            "\n\n请注意：返回必须为 JSON 格式。若需要调用本地工具，请在 JSON 中包含 `function_calls` 字段，"
            "它应为数组，数组元素为 {\"name\": 工具名, \"arguments\": {...}}。"
            "一旦工具被执行，系统会将工具执行结果回传给你，之后你可以基于结果继续生成最终的 `final_output` 字段。"
        )
        prompt = research_goal + instruction
        messages = [{"role": "user", "content": prompt}]
        response = self._function_call(messages, Agent)
        return response