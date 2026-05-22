#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML工作流DSL引擎 - OpenClaude Agent编排即代码理念内化

功能：
1. YAML工作流定义解析与验证
2. 多种执行模式（parallel/sequential/conditional）
3. Agent资源管理与调度
4. 工作流状态追踪与错误处理
5. 超时管理与重试机制
"""

import copy
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)


class StepType(Enum):
    """步骤类型枚举"""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    CONDITIONAL = "conditional"
    SINGLE = "single"


class StepStatus(Enum):
    """步骤状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class WorkflowStatus(Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentDefinition:
    """Agent定义"""
    id: str
    role: str
    capabilities: List[str] = field(default_factory=list)
    resources_required: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_id: str
    step_type: StepType
    agents: List[str] = field(default_factory=list)
    agent: Optional[str] = None
    actions: List[str] = field(default_factory=list)
    timeout: Optional[int] = None
    condition: Optional[Dict[str, Any]] = None
    depends_on: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0


@dataclass
class StepResult:
    """步骤执行结果"""
    step_id: str
    status: StepStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    agent_id: Optional[str] = None
    logs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    name: str
    version: str
    description: str = ""
    agents: List[AgentDefinition] = field(default_factory=list)
    workflow: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    error_handling: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


@dataclass
class WorkflowExecutionResult:
    """工作流执行结果"""
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_seconds: float = 0.0
    step_results: List[StepResult] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        d = asdict(self)
        d["status"] = self.status.value
        if self.completed_at:
            d["completed_at"] = self.completed_at.isoformat()
        d["started_at"] = self.started_at.isoformat()
        d["step_results"] = [sr.to_dict() for sr in self.step_results]
        return d


class WorkflowDSLEngine:
    """YAML工作流DSL引擎 - OpenClaude Agent编排即代码理念内化"""

    def __init__(
        self,
        agent_executor: Optional[Callable[[str, str, Dict], Any]] = None,
        max_workers: int = 4,
        default_timeout: int = 300,
    ):
        """
        初始化引擎

        参数:
            agent_executor: Agent执行器函数 (agent_id, action, context) -> result
            max_workers: 并行执行最大Worker数
            default_timeout: 默认超时时间（秒）
        """
        self.agent_executor = agent_executor or self._default_agent_executor
        self.max_workers = max_workers
        self.default_timeout = default_timeout
        self._execution_history: List[WorkflowExecutionResult] = []

    def _default_agent_executor(self, agent_id: str, action: str, context: Dict) -> Any:
        """默认Agent执行器（模拟实现）"""
        logger.info("[模拟执行] Agent=%s 执行动作=%s", agent_id, action)
        return {
            "agent_id": agent_id,
            "action": action,
            "status": "simulated",
            "timestamp": datetime.now().isoformat(),
            "context_keys": list(context.keys()),
        }

    def parse_workflow(self, yaml_path: str) -> WorkflowDefinition:
        """
        解析YAML工作流定义

        参数:
            yaml_path: YAML文件路径

        返回:
            WorkflowDefinition 对象

        异常:
            FileNotFoundError: 文件不存在
            ValueError: YAML格式无效或缺少必要字段
        """
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"工作流文件不存在: {yaml_path}")

        if yaml is None:
            raw_content = path.read_text(encoding="utf-8")
            return self._parse_yaml_fallback(raw_content, yaml_path)

        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict):
            raise ValueError("YAML根元素必须是对象/映射")

        required_fields = ["name", "version"]
        for field_name in required_fields:
            if field_name not in raw:
                raise ValueError(f"缺少必要字段: {field_name}")

        agents = []
        for agent_data in raw.get("agents", []):
            agents.append(AgentDefinition(
                id=agent_data.get("id", ""),
                role=agent_data.get("role", ""),
                capabilities=agent_data.get("capabilities", []),
                resources_required=agent_data.get("resources_required", {}),
                metadata=agent_data.get("metadata", {}),
            ))

        definition = WorkflowDefinition(
            name=raw["name"],
            version=raw["version"],
            description=raw.get("description", ""),
            agents=agents,
            workflow=raw.get("workflow", {}),
            variables=raw.get("variables", {}),
            error_handling=raw.get("error_handling", {}),
            metadata=raw.get("metadata", {}),
        )

        logger.info("工作流解析成功: %s v%s", definition.name, definition.version)
        return definition

    def _parse_yaml_fallback(self, content: str, source_path: str) -> WorkflowDefinition:
        """无PyYAML时的简易解析后备方案"""
        import ast
        try:
            data = ast.literal_eval(content.strip())
        except (ValueError, SyntaxError):
            raise ValueError("需要安装PyYAML库才能解析此工作流文件: pip install pyyaml")

        return WorkflowDefinition(
            name=data.get("name", "unknown"),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            workflow=data.get("workflow", {}),
            error_handling=data.get("error_handling", {}),
        )

    def validate_workflow(self, workflow: WorkflowDefinition) -> ValidationResult:
        """
        验证工作流定义完整性

        参数:
            workflow: WorkflowDefinition 对象

        返回:
            ValidationResult 对象
        """
        errors = []
        warnings = []
        info = []

        if not workflow.name or not workflow.name.strip():
            errors.append("工作流名称不能为空")

        if not re.match(r"^\d+\.\d+\.\d+$", workflow.version):
            warnings.append(f"版本号格式建议使用语义化版本: {workflow.version}")

        agent_ids = {a.id for a in workflow.agents}
        if len(agent_ids) != len(workflow.agents):
            errors.append("存在重复的Agent ID")

        for agent in workflow.agents:
            if not agent.id.strip():
                errors.append("发现Agent ID为空")
            if not agent.role.strip():
                warnings.append(f"Agent '{agent.id}' 缺少角色定义")
            if not agent.capabilities:
                warnings.append(f"Agent '{agent.id}' 未声明任何能力")

        steps = workflow.workflow
        if not steps:
            errors.append("工作流未定义任何步骤")
        else:
            for step_id, step_config in steps.items():
                step_errors, step_warnings = self._validate_step(step_id, step_config, agent_ids)
                errors.extend(step_errors)
                warnings.extend(step_warnings)

        eh = workflow.error_handling
        if eh:
            on_failure = eh.get("on_agent_failure")
            valid_strategies = [
                "retry_with_backoff", "fail_fast", "skip_and_continue",
                "escalate_to_human", "use_cache_result",
            ]
            if on_failure and on_failure not in valid_strategies:
                warnings.append(f"未知错误处理策略: {on_failure}")

            max_retries = eh.get("max_retries", 0)
            if not isinstance(max_retries, int) or max_retries < 0:
                errors.append(f"max_retries 必须是非负整数: {max_retries}")

        total_agents = len(workflow.agents)
        total_steps = len(steps)
        info.append(f"工作流包含 {total_agents} 个Agent和 {total_steps} 个步骤")

        is_valid = len(errors) == 0

        result = ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            info=info,
        )

        level = "INFO" if is_valid else "WARNING" if warnings else "ERROR"
        logger.log(
            getattr(logging, level),
            "工作流验证完成: %s (有效=%s, 错误=%d, 警告=%d)",
            workflow.name, is_valid, len(errors), len(warnings),
        )
        return result

    def _validate_step(
        self, step_id: str, config: Any, valid_agent_ids: set
    ) -> Tuple[List[str], List[str]]:
        """验证单个步骤配置"""
        errors = []
        warnings = []

        if not isinstance(config, dict):
            errors.append(f"步骤 '{step_id}' 配置必须是对象")
            return errors, warnings

        step_type = config.get("type", "single")
        valid_types = ["parallel", "sequential", "conditional", "single"]
        if step_type not in valid_types:
            errors.append(f"步骤 '{step_id}' 类型无效: {step_type}, 有效值: {valid_types}")

        agents_in_step = config.get("agents", [])
        single_agent = config.get("agent")

        if step_type == "parallel":
            if not agents_in_step:
                errors.append(f"并行步骤 '{step_id}' 必须指定agents列表")
            for aid in agents_in_step:
                if aid not in valid_agent_ids:
                    warnings.append(f"步骤 '{step_id}' 引用了未注册的Agent: {aid}")

        elif step_type in ("sequential", "single"):
            if single_agent and single_agent not in valid_agent_ids:
                warnings.append(f"步骤 '{step_id}' 引用了未注册的Agent: {single_agent}")
            if not single_agent and step_type == "single":
                warnings.append(f"单步 '{step_id}' 建议指定agent")

        timeout = config.get("timeout")
        if timeout is not None:
            timeout_str = str(timeout)
            if not re.match(r"^(\d+[smh])?$", timeout_str):
                try:
                    int(timeout_str)
                except ValueError:
                    warnings.append(f"步骤 '{step_id}' 的timeout格式异常: {timeout}")

        actions = config.get("actions", [])
        if step_type in ("sequential", "single") and not actions:
            warnings.append(f"顺序/单步 '{step_id}' 未定义actions")

        condition = config.get("condition")
        if step_type == "conditional" and not condition:
            errors.append(f"条件步骤 '{step_id}' 必须定义condition")

        return errors, warnings

    def _parse_timeout(self, timeout_value: Any) -> int:
        """解析超时值为秒数"""
        if timeout_value is None:
            return self.default_timeout
        if isinstance(timeout_value, int):
            return timeout_value
        s = str(timeout_value).lower().strip()
        match = re.match(r"^(\d+)([smh])?$", s)
        if match:
            val = int(match.group(1))
            unit = match.group(2) or "s"
            multipliers = {"s": 1, "m": 60, "h": 3600}
            return val * multipliers[unit]
        return self.default_timeout

    def execute_step(self, step: WorkflowStep, context: Dict) -> StepResult:
        """
        执行单个步骤（支持parallel/sequential/conditional）

        参数:
            step: WorkflowStep 对象
            context: 执行上下文

        返回:
            StepResult 对象
        """
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        start_time = time.time()

        logs = [f"[{step.step_id}] 开始执行 (类型: {step.step_type.value})"]

        try:
            if step.step_type == StepType.PARALLEL:
                result = self._execute_parallel(step, context, logs)
            elif step.step_type == StepType.SEQUENTIAL:
                result = self._execute_sequential(step, context, logs)
            elif step.step_type == StepType.CONDITIONAL:
                result = self._execute_conditional(step, context, logs)
            else:
                result = self._execute_single(step, context, logs)

            step.result = result
            step.status = StepStatus.SUCCESS
            logs.append(f"[{step.step_id}] 执行成功")

        except TimeoutError as e:
            step.status = StepStatus.TIMEOUT
            step.error = str(e)
            logs.append(f"[{step.step_id}] 执行超时: {e}")
            result = {"error": "timeout", "message": str(e)}

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            logs.append(f"[{step.step_id}] 执行失败: {e}")
            result = {"error": type(e).__name__, "message": str(e)}
            logger.exception("步骤执行异常: %s", step.step_id)

        finally:
            step.completed_at = datetime.now()
            step.duration_seconds = time.time() - start_time

        return StepResult(
            step_id=step.step_id,
            status=step.status,
            result=result,
            error=step.error,
            duration_seconds=step.duration_seconds,
            logs=logs,
        )

    def _execute_parallel(self, step: WorkflowStep, context: Dict, logs: List[str]) -> Any:
        """并行执行多个Agent"""
        results = []
        timeout_secs = self._parse_timeout(step.timeout)

        def run_agent(agent_id: str):
            return self.agent_executor(agent_id, f"parallel_task_{step.step_id}", context)

        with ThreadPoolExecutor(max_workers=min(len(step.agents), self.max_workers)) as executor:
            futures: Dict[Future, str] = {
                executor.submit(run_agent, aid): aid for aid in step.agents
            }
            done_futures = {}
            try:
                for future in as_completed(futures, timeout=timeout_secs):
                    aid = futures[future]
                    try:
                        done_futures[aid] = future.result()
                        logs.append(f"  [{aid}] 并行任务完成")
                    except Exception as e:
                        done_futures[aid] = {"error": str(e)}
                        logs.append(f"  [{agent}] 并行任务失败: {e}")

            except Exception as e:
                for f, aid in futures.items():
                    if aid not in done_futures:
                        done_futures[aid] = {"error": f"cancelled: {e}"}

        results = [{"agent_id": aid, "result": res} for aid, res in done_futures.items()]
        context[f"{step.step_id}_results"] = results
        return results

    def _execute_sequential(self, step: WorkflowStep, context: Dict, logs: List[str]) -> Any:
        """按顺序执行一系列动作"""
        results = []
        agent_id = step.agent or "default"

        for i, action in enumerate(step.actions):
            logs.append(f"  [{agent_id}] 执行动作[{i+1}/{len(step.actions)}]: {action}")
            action_result = self.agent_executor(agent_id, action, context)
            results.append({
                "action": action,
                "result": action_result,
                "index": i,
            })
            context[f"{step.step_id}_action_{i}_result"] = action_result

        context[f"{step.step_id}_results"] = results
        return results

    def _execute_conditional(self, step: WorkflowStep, context: Dict, logs: List[str]) -> Any:
        """根据条件决定是否/如何执行"""
        condition = step.condition or {}

        var_name = condition.get("variable")
        operator = condition.get("operator", "equals")
        expected_value = condition.get("value")

        actual_value = context.get(var_name)

        passed = self._evaluate_condition(actual_value, operator, expected_value)

        logs.append(f"  条件判断: {var_name} {operator} {expected_value} => 实际={actual_value} => {'通过' if passed else '不通过'}")

        if passed:
            then_actions = condition.get("then_actions", step.actions)
            if then_actions:
                return self._execute_sequential(
                    WorkflowStep(
                        step_id=f"{step.step_id}_then",
                        step_type=StepType.SEQUENTIAL,
                        agent=step.agent,
                        actions=then_actions,
                    ),
                    context,
                    logs,
                )
            return {"condition_met": True, "actual_value": actual_value}
        else:
            else_actions = condition.get("else_actions", [])
            if else_actions:
                return self._execute_sequential(
                    WorkflowStep(
                        step_id=f"{step.step_id}_else",
                        step_type=StepType.SEQUENTIAL,
                        agent=step.agent,
                        actions=else_actions,
                    ),
                    context,
                    logs,
                )
            step.status = StepStatus.SKIPPED
            return {"condition_met": False, "actual_value": actual_value, "skipped": True}

    def _execute_single(self, step: WorkflowStep, context: Dict, logs: List[str]) -> Any:
        """执行单个Agent的单个操作"""
        agent_id = step.agent or "default"
        action = step.actions[0] if step.actions else f"task_{step.step_id}"
        logs.append(f"  [{agent_id}] 执行: {action}")
        result = self.agent_executor(agent_id, action, context)
        context[f"{step.step_id}_result"] = result
        return result

    def _evaluate_condition(self, actual: Any, operator: str, expected: Any) -> bool:
        """评估条件表达式"""
        ops = {
            "equals": lambda a, e: a == e,
            "not_equals": lambda a, e: a != e,
            "contains": lambda a, e: e in str(a) if a else False,
            "not_contains": lambda a, e: e not in str(a) if a else True,
            "greater_than": lambda a, e: (a or 0) > (e or 0),
            "less_than": lambda a, e: (a or 0) < (e or 0),
            "exists": lambda a, e: a is not None,
            "is_empty": lambda a, e: not a if isinstance(a, (list, dict, str)) else False,
            "matches": lambda a, e: bool(re.search(str(e), str(a))) if a else False,
        }
        func = ops.get(operator, ops["equals"])
        try:
            return func(actual, expected)
        except Exception:
            return False

    def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExecutionResult:
        """
        执行完整工作流

        参数:
            workflow: 已解析的工作流定义
            initial_context: 初始上下文变量

        返回:
            WorkflowExecutionResult 对象
        """
        workflow_id = f"{workflow.name}_{workflow.version}"
        started_at = datetime.now()
        start_time = time.time()

        context = dict(initial_context or {})
        context.update(workflow.variables)
        context["_workflow_name"] = workflow.name
        context["_workflow_version"] = workflow.version
        context["_started_at"] = started_at.isoformat()

        step_results: List[StepResult] = []
        overall_status = WorkflowStatus.COMPLETED
        error_msg = None

        validation = self.validate_workflow(workflow)
        if not validation.is_valid:
            return WorkflowExecutionResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(),
                total_duration_seconds=time.time() - start_time,
                error=f"工作流验证失败: {'; '.join(validation.errors)}",
                context=context,
            )

        logger.info("开始执行工作流: %s (%d 个步骤)", workflow_id, len(workflow.workflow))

        step_order = list(workflow.workflow.keys())

        for step_key in step_order:
            step_config = workflow.workflow[step_key]
            step_type_str = step_config.get("type", "single")

            try:
                step_type = StepType(step_type_str)
            except ValueError:
                step_type = StepType.SINGLE

            step = WorkflowStep(
                step_id=step_key,
                step_type=step_type,
                agents=step_config.get("agents", []),
                agent=step_config.get("agent"),
                actions=step_config.get("actions", []),
                timeout=step_config.get("timeout"),
                condition=step_config.get("condition"),
                depends_on=step_config.get("depends_on", []),
                config=step_config,
            )

            dep_failed = any(
                sr.status in (StepStatus.FAILED, StepStatus.TIMEOUT)
                for sr in step_results
                if sr.step_id in step.depends_on
            )
            if dep_failed:
                step.status = StepStatus.SKIPPED
                step_results.append(StepResult(
                    step_id=step.step_id,
                    status=StepStatus.SKIPPED,
                    error="依赖步骤失败，跳过执行",
                    logs=[f"[{step.step_id}] 因依赖失败而跳过"],
                ))
                continue

            result = self.execute_step(step, context)
            step_results.append(result)

            if result.status == StepStatus.FAILED:
                eh_strategy = workflow.error_handling.get("on_agent_failure", "fail_fast")
                max_retries = workflow.error_handling.get("max_retries", 0)

                if eh_strategy == "retry_with_backoff" and max_retries > 0:
                    for attempt in range(1, max_retries + 1):
                        wait = min(2 ** attempt, 30)
                        logger.info("重试 %s (第%d次, 等待%ds)", step.step_id, attempt, wait)
                        time.sleep(wait)
                        retry_result = self.execute_step(step, context)
                        step_results[-1] = retry_result
                        if retry_result.status == StepStatus.SUCCESS:
                            break
                elif eh_strategy == "fail_fast":
                    overall_status = WorkflowStatus.FAILED
                    error_msg = f"步骤 '{step.step_id}' 执行失败: {result.error}"
                    logger.error("工作流中断: %s", error_msg)
                    break
                elif eh_strategy == "skip_and_continue":
                    logger.warning("步骤 '%s' 失败但继续执行", step.step_id)
                elif eh_strategy == "escalate_to_human":
                    overall_status = WorkflowStatus.FAILED
                    error_msg = f"步骤 '{step.step_id}' 失败，需要人工介入: {result.error}"
                    break

        completed_at = datetime.now()
        total_duration = time.time() - start_time

        execution_result = WorkflowExecutionResult(
            workflow_id=workflow_id,
            status=overall_status,
            started_at=started_at,
            completed_at=completed_at,
            total_duration_seconds=total_duration,
            step_results=step_results,
            context=context,
            error=error_msg,
        )

        self._execution_history.append(execution_result)
        logger.info(
            "工作流执行完成: %s 状态=%s 耗时=%.2fs 步骤=%d/%d",
            workflow_id, overall_status.value, total_duration,
            sum(1 for r in step_results if r.status != StepStatus.PENDING),
            len(step_results),
        )
        return execution_result

    def get_execution_history(self, limit: int = 10) -> List[WorkflowExecutionResult]:
        """获取最近的工作流执行历史"""
        return self._execution_history[-limit:]


def main():
    sample_workflow_yaml = """
name: code_review_multi_agent
version: "1.0.0"
description: "多Agent协同代码审查"

agents:
  - id: frontend_reviewer
    role: Frontend Developer Expert
    capabilities: [react_code_review, css_accessibility, performance_optimization]
    resources_required:
      file_lock: "src/frontend/**"
      api_calls: 10

  - id: security_reviewer
    role: Security Expert
    capabilities: [owasp_top10, auth_review, injection_detection]
    resources_required:
      file_lock: "src/**"
      api_calls: 5

  - id: performance_reviewer
    role: Performance Engineer
    capabilities: [profiling, bottleneck_analysis, optimization]
    resources_required:
      compute_quota: "high"
      api_calls: 8

  - id: orchestrator
    role: Review Orchestrator
    capabilities: [finding_merge, conflict_resolution, prioritization]

variables:
  target_branch: "main"
  review_deadline: "24h"
  severity_threshold: "medium"

workflow:
  step_1_parallel_review:
    type: parallel
    agents: [frontend_reviewer, security_reviewer, performance_reviewer]
    timeout: "10min"

  step_2_aggregation:
    type: sequential
    agent: orchestrator
    actions: [merge_findings, resolve_conflicts, prioritize_issues]
    timeout: "5min"

error_handling:
  on_agent_failure: retry_with_backoff
  max_retries: 2
"""

    engine = WorkflowDSLEngine(max_workers=4)

    import tempfile
    tmp_file = Path(tempfile.mktemp(suffix=".yml"))
    tmp_file.write_text(sample_workflow_yaml, encoding="utf-8")

    print("=" * 60)
    print("1. 解析工作流")
    print("=" * 60)
    workflow = engine.parse_workflow(str(tmp_file))
    print(f"  名称: {workflow.name}")
    print(f"  版本: {workflow.version}")
    print(f"  描述: {workflow.description}")
    print(f"  Agent数量: {len(workflow.agents)}")
    for agent in workflow.agents:
        print(f"    - {agent.id}: {agent.role} ({', '.join(agent.capabilities)})")

    print("\n" + "=" * 60)
    print("2. 验证工作流")
    print("=" * 60)
    validation = engine.validate_workflow(workflow)
    print(f"  有效: {validation.is_valid}")
    if validation.errors:
        print(f"  错误: {validation.errors}")
    if validation.warnings:
        print(f"  警告: {validation.warnings}")
    if validation.info:
        print(f"  信息: {validation.info}")

    print("\n" + "=" * 60)
    print("3. 执行工作流")
    print("=" * 60)
    result = engine.execute_workflow(workflow)
    print(f"  状态: {result.status.value}")
    print(f"  总耗时: {result.total_duration_seconds:.2f}s")
    print(f"  步骤结果:")
    for sr in result.step_results:
        status_icon = "✅" if sr.status.value in ("success", "skipped") else "❌"
        print(f"    {status_icon} [{sr.step_id}] {sr.status.value} ({sr.duration_seconds:.2f}s)")

    tmp_file.unlink(missing_ok=True)
    print("\n工作流引擎演示完成!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    main()
