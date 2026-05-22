"""
OpenClaude Orchestrator - Agent编排增强系统
理念来源：OpenClaude项目的"Agent编排即代码"和"上下文感知"核心理念

核心功能：
1. YAML声明式工作流DSL - 用YAML定义多Agent协作流程
2. 工作流引擎 - 条件分支/并行执行/循环迭代/错误恢复/变量传递/状态持久化
3. 上下文感知注入 - 自动识别技术栈并注入最佳实践
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any


class StepStatus(Enum):
    """工作流步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class WorkflowStatus(Enum):
    """工作流整体状态"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """工作流步骤定义"""
    step_id: str
    agent: str
    action: str
    input_vars: list[str] | dict[str, Any] | None = None
    output_var: str | None = None
    depends_on: list[str] = field(default_factory=list)
    condition: str | None = None
    type: str = "sequential"
    parallel_steps: list[WorkflowStep] | None = None
    retry_config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "step_id": self.step_id,
            "agent": self.agent,
            "action": self.action,
            "input": self.input_vars,
            "output": self.output_var,
            "depends_on": self.depends_on,
            "condition": self.condition,
            "type": self.type,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class WorkflowDefinition:
    """工作流定义（从YAML解析）"""
    name: str
    version: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    error_handling: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式（用于序列化）"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "variables": self.variables,
            "error_handling": self.error_handling,
            "metadata": self.metadata,
        }


@dataclass
class WorkflowExecution:
    """工作流执行实例"""
    execution_id: str
    workflow_def: WorkflowDefinition
    status: WorkflowStatus = WorkflowStatus.INITIALIZED
    current_step_index: int = 0
    variables: dict[str, Any] = field(default_factory=dict)
    completed_steps: list[str] = field(default_factory=list)
    failed_steps: list[str] = field(default_factory=list)
    step_results: dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    error_log: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ProjectContext:
    """项目上下文信息"""
    project_name: str = ""
    tech_stack: list[str] = field(default_factory=list)
    framework: str = ""
    language: str = ""
    package_manager: str = ""
    build_tool: str = ""
    test_framework: str = ""
    best_practices: list[str] = field(default_factory=list)
    code_examples: dict[str, str] = field(default_factory=dict)
    summary: str = ""


class ContextInjector:
    """
    上下文感知注入器
    
    自动识别项目技术栈并根据技术栈注入相关的最佳实践和代码示例
    """

    TECH_STACK_PATTERNS = {
        "package.json": {"language": "JavaScript", "package_manager": "npm"},
        "yarn.lock": {"language": "JavaScript", "package_manager": "yarn"},
        "pnpm-lock.yaml": {"language": "JavaScript", "package_manager": "pnpm"},
        "requirements.txt": {"language": "Python", "package_manager": "pip"},
        "pyproject.toml": {"language": "Python", "package_manager": "pip/poetry"},
        "Pipfile": {"language": "Python", "package_manager": "pipenv"},
        "pom.xml": {"language": "Java", "build_tool": "Maven"},
        "build.gradle": {"language": "Java/Kotlin", "build_tool": "Gradle"},
        "Cargo.toml": {"language": "Rust", "package_manager": "cargo"},
        "go.mod": {"language": "Go", "package_manager": "go modules"},
        "Gemfile": {"language": "Ruby", "package_manager": "bundler"},
        "composer.json": {"language": "PHP", "package_manager": "composer"},
    }

    FRAMEWORK_PATTERNS = {
        "react": ["React", "Next.js", "Vue", "Angular"],
        "vue": ["Vue", "Nuxt"],
        "angular": ["Angular"],
        "django": ["Django", "Flask", "FastAPI"],
        "flask": ["Flask", "Django"],
        "fastapi": ["FastAPI", "Starlette"],
        "spring": ["Spring Boot", "Spring Cloud"],
        "express": ["Express.js", "Koa", "NestJS"],
        "next": ["Next.js", "React"],
        "rails": ["Ruby on Rails"],
        "laravel": ["Laravel"],
        "gin": ["Gin (Go)", "Echo (Go)"],
        "actix": ["Actix-web (Rust)"],
        "axios": ["Axios", "Fetch API"],
        "pytest": ["Pytest", "unittest"],
        "jest": ["Jest", "Mocha", "Vitest"],
    }

    BEST_PRACTICES_BY_STACK = {
        "Python": [
            "使用类型注解提高代码可读性",
            "遵循PEP 8编码规范",
            "使用virtualenv或poetry管理依赖",
            "编写docstring文档",
            "使用logging而非print进行日志记录",
        ],
        "JavaScript": [
            "使用ESLint和Prettier保持代码风格一致",
            "优先使用const和let，避免var",
            "使用async/await处理异步操作",
            "编写JSDoc注释",
            "模块化代码，避免全局变量",
        ],
        "Java": [
            "遵循Google Java Style Guide",
            "使用Lombok减少样板代码",
            "正确使用Optional处理空值",
            "编写JUnit 5测试",
            "使用SLF4J进行日志记录",
        ],
        "Go": [
            "遵循Effective Go最佳实践",
            "使用go fmt格式化代码",
            "正确处理error返回值",
            "使用interface设计抽象",
            "编写table-driven测试",
        ],
        "Rust": [
            "遵循Rust API Guidelines",
            "正确使用Result和Option",
            "利用所有权系统保证内存安全",
            "使用clippy进行lint检查",
            "编写文档测试(doc tests)",
        ],
    }

    def __init__(self, project_root: Path | str | None = None):
        """
        初始化上下文注入器
        
        Args:
            project_root: 项目根目录路径
        """
        if isinstance(project_root, str):
            project_root = Path(project_root)
        self.project_root = project_root or Path.cwd()
        self._context: ProjectContext | None = None

    def detect_tech_stack(self) -> ProjectContext:
        """
        自动检测项目技术栈
        
        Returns:
            包含项目上下文信息的ProjectContext对象
        """
        context = ProjectContext()
        context.project_name = self.project_root.name
        
        detected_info = {}
        
        for file_pattern, info in self.TECH_STACK_PATTERNS.items():
            file_path = self.project_root / file_pattern
            if file_path.exists():
                for key, value in info.items():
                    if key not in detected_info:
                        detected_info[key] = value
        
        context.language = detected_info.get("language", "Unknown")
        context.package_manager = detected_info.get("package_manager", "")
        context.build_tool = detected_info.get("build_tool", "")
        
        context.tech_stack = self._detect_frameworks()
        if context.tech_stack:
            context.framework = context.tech_stack[0]
        
        context.test_framework = self._detect_test_framework()
        
        context.best_practices = self.BEST_PRACTICES_BY_STACK.get(context.language, [])
        
        context.code_examples = self._generate_code_examples(context.language)
        
        context.summary = self._generate_summary(context)
        
        self._context = context
        return context

    def _detect_frameworks(self) -> list[str]:
        """检测使用的框架"""
        frameworks = set()
        
        for pattern, fw_list in self.FRAMEWORK_PATTERNS.items():
            search_patterns = [
                f"package.json",
                f"requirements.txt",
                f"pyproject.toml",
                f"pom.xml",
                f"build.gradle",
                f"go.mod",
                f"Cargo.toml",
            ]
            
            for sp in search_patterns:
                file_path = self.project_root / sp
                if file_path.exists():
                    content = file_path.read_text(encoding="utf-8", errors="ignore").lower()
                    if pattern.lower() in content:
                        frameworks.update(fw_list)
                        break
        
        return sorted(list(frameworks))

    def _detect_test_framework(self) -> str:
        """检测测试框架"""
        test_indicators = {
            "pytest": ["pytest.ini", "conftest.py", "pyproject.toml"],
            "unittest": ["test_", "_test.py"],
            "jest": ["jest.config", "jest.config.js"],
            "mocha": [".mocharc"],
            "junit": ["pom.xml", "build.gradle"],
            "go test": ["*_test.go"],
        }
        
        for framework, indicators in test_indicators.items():
            for indicator in indicators:
                if "*" in indicator:
                    base_pattern = indicator.replace("*", "")
                    if any(f.name.startswith(base_pattern) or f.name.endswith(base_pattern)
                           for f in self.project_root.rglob("*") if f.is_file()):
                        return framework
                else:
                    if (self.project_root / indicator).exists():
                        content = (self.project_root / indicator).read_text(encoding="utf-8", errors="ignore")
                        if framework.lower() in content.lower() or indicator.endswith(".py") or indicator.endswith(".go"):
                            return framework
        
        return ""

    def _generate_code_examples(self, language: str) -> dict[str, str]:
        """根据语言生成代码示例"""
        examples = {}
        
        if language == "Python":
            examples["async_example"] = '''
import asyncio

async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def main():
    data = await fetch_data("https://api.example.com")
    print(data)

if __name__ == "__main__":
    asyncio.run(main())
'''
            examples["type_hints"] = '''
from typing import Optional, List, Dict

def process_items(
    items: List[Dict[str, Any]],
    filter_fn: Optional[callable] = None
) -> List[Dict[str, Any]]:
    """Process and optionally filter items."""
    if filter_fn:
        items = [item for item in items if filter_fn(item)]
    return items
'''
        
        elif language == "JavaScript":
            examples["async_example"] = '''
async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Error fetching data:", error);
        throw error;
    }
}

async function main() {
    const data = await fetchData("https://api.example.com");
    console.log(data);
}
'''
            examples["module_pattern"] = '''
// ES Module pattern
export class DataService {
    #baseUrl;
    
    constructor(baseUrl) {
        this.#baseUrl = baseUrl;
    }
    
    async getData(endpoint) {
        const response = await fetch(`${this.#baseUrl}${endpoint}`);
        return response.json();
    }
}
'''
        
        elif language == "Java":
            examples["service_pattern"] = '''
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    
    public User createUser(UserDto dto) {
        User user = User.builder()
            .username(dto.getUsername())
            .password(passwordEncoder.encode(dto.getPassword()))
            .email(dto.getEmail())
            .build();
        return userRepository.save(user);
    }
    
    public Optional<User> findById(Long id) {
        return userRepository.findById(id);
    }
}
'''
        
        elif language == "Go":
            examples["handler_pattern"] = '''
package handler

import (
    "encoding/json"
    "net/http"
)

type Handler struct {
    service ServiceInterface
}

func NewHandler(svc ServiceInterface) *Handler {
    return &Handler{service: svc}
}

func (h *Handler) HandleRequest(w http.ResponseWriter, r *http.Request) {
    var req RequestBody
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    
    result, err := h.service.Process(r.Context(), req)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(result)
}
'''
        
        return examples

    def _generate_summary(self, context: ProjectContext) -> str:
        """生成项目上下文摘要"""
        parts = [
            f"项目名称: {context.project_name}",
            f"主要语言: {context.language}",
        ]
        
        if context.framework:
            parts.append(f"框架: {', '.join(context.tech_stack[:3])}")
        if context.package_manager:
            parts.append(f"包管理器: {context.package_manager}")
        if context.build_tool:
            parts.append(f"构建工具: {context.build_tool}")
        if context.test_framework:
            parts.append(f"测试框架: {context.test_framework}")
        
        return "\n".join(parts)

    def get_context(self) -> ProjectContext:
        """获取已检测的项目上下文"""
        if self._context is None:
            return self.detect_tech_stack()
        return self._context

    def inject_context_to_prompt(self, base_prompt: str) -> str:
        """
        将项目上下文注入到提示词中
        
        Args:
            base_prompt: 原始提示词
            
        Returns:
            注入上下文后的提示词
        """
        context = self.get_context()
        
        injected = f"""## 项目上下文信息

{context.summary}

### 推荐的最佳实践
{chr(10).join(f'- {bp}' for bp in context.best_practices)}

---
{base_prompt}
"""
        return injected


class WorkflowEngine:
    """
    YAML声明式工作流引擎
    
    支持以下特性：
    - 条件分支执行（基于变量条件）
    - 并行步骤执行（并行块与汇合点）
    - 循环迭代（批量处理的for/while循环）
    - 错误处理与恢复（try/catch/retry/fallback）
    - 变量传递与替换（${variable}语法）
    - 工作流状态持久化（可中断恢复）
    """

    VARIABLE_PATTERN = re.compile(r'\$\{([^}]+)\}')

    def __init__(self, workflows_dir: Path | str | None = None):
        """
        初始化工作流引擎
        
        Args:
            workflows_dir: 工作流定义文件目录
        """
        if isinstance(workflows_dir, str):
            workflows_dir = Path(workflows_dir)
        self.workflows_dir = workflows_dir or Path.cwd() / "configs" / "workflows"
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        
        self._workflow_definitions: dict[str, WorkflowDefinition] = {}
        self._executions: dict[str, WorkflowExecution] = {}
        self._state_file = self.workflows_dir.parent / "workflow_state.json"

    def load_workflow_from_yaml(self, yaml_content: str | Path) -> WorkflowDefinition:
        """
        从YAML内容或文件加载工作流定义
        
        Args:
            yaml_content: YAML字符串或文件路径
            
        Returns:
            解析后的WorkflowDefinition对象
            
        Raises:
            ImportError: 如果未安装PyYAML库
        """
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required to parse workflow definitions. "
                "Install it with: pip install pyyaml"
            )
        
        if isinstance(yaml_content, Path):
            yaml_content = yaml_content.read_text(encoding="utf-8")
        
        data = yaml.safe_load(yaml_content)
        return self._parse_workflow_definition(data)

    def _parse_workflow_definition(self, data: dict[str, Any]) -> WorkflowDefinition:
        """解析YAML数据为WorkflowDefinition对象"""
        workflow_def = WorkflowDefinition(
            name=data.get("name", "unnamed_workflow"),
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            variables=data.get("variables", {}),
            error_handling=data.get("error_handling", {}),
            metadata=data.get("metadata", {}),
        )
        
        steps_data = data.get("steps", [])
        workflow_def.steps = self._parse_steps(steps_data)
        
        return workflow_def

    def _parse_steps(self, steps_data: list[dict]) -> list[WorkflowStep]:
        """递归解析步骤列表"""
        steps = []
        
        for step_data in steps_data:
            step_type = step_data.get("type", "sequential")
            
            if step_type == "parallel":
                parallel_steps = self._parse_steps(step_data.get("steps", []))
                step = WorkflowStep(
                    step_id=step_data.get("id", f"parallel_{uuid.uuid4().hex[:6]}"),
                    agent="parallel_executor",
                    action="execute_parallel",
                    type="parallel",
                    parallel_steps=parallel_steps,
                    depends_on=step_data.get("depends_on", []),
                    condition=step_data.get("condition"),
                )
            else:
                step = WorkflowStep(
                    step_id=step_data.get("id", f"step_{uuid.uuid4().hex[:6]}"),
                    agent=step_data.get("agent", "default_agent"),
                    action=step_data.get("action", "default_action"),
                    input_vars=step_data.get("input"),
                    output_var=step_data.get("output"),
                    depends_on=step_data.get("depends_on", []),
                    condition=step_data.get("condition"),
                    retry_config=step_data.get("retry", {}),
                    metadata=step_data.get("metadata", {}),
                )
            
            steps.append(step)
        
        return steps

    def save_workflow_definition(self, workflow: WorkflowDefinition, filename: str | None = None) -> Path:
        """
        保存工作流定义为YAML文件
        
        Args:
            workflow: 工作流定义对象
            filename: 文件名，默认为 {name}_v{version}.yaml
            
        Returns:
            保存的文件路径
        """
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required. Install with: pip install pyyaml")
        
        if filename is None:
            safe_name = re.sub(r'[^\w\-]', '_', workflow.name.lower())
            filename = f"{safe_name}_v{workflow.version.replace('.', '_')}.yaml"
        
        filepath = self.workflows_dir / filename
        
        yaml_dict = workflow.to_dict()
        yaml_content = yaml.dump(yaml_dict, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        filepath.write_text(yaml_content, encoding="utf-8")
        
        self._workflow_definitions[workflow.name] = workflow
        return filepath

    def create_execution(self, workflow: WorkflowDefinition, initial_vars: dict[str, Any] | None = None) -> WorkflowExecution:
        """
        创建工作流执行实例
        
        Args:
            workflow: 要执行的工作流定义
            initial_vars: 初始变量值
            
        Returns:
            WorkflowExecution执行实例
        """
        execution_id = f"exec-{uuid.uuid4().hex[:10]}"
        
        variables = {**workflow.variables}
        if initial_vars:
            variables.update(initial_vars)
        
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_def=workflow,
            variables=variables,
        )
        
        self._executions[execution_id] = execution
        return execution

    def execute_step(self, execution: WorkflowExecution, step: WorkflowStep) -> bool:
        """
        执行单个工作流步骤
        
        Args:
            execution: 执行实例
            step: 要执行的步骤
            
        Returns:
            步骤是否成功完成
        """
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now(timezone.utc)
        
        try:
            resolved_input = self._resolve_variables(execution.variables, step.input_vars)
            
            if step.type == "parallel" and step.parallel_steps:
                results = []
                for parallel_step in step.parallel_steps:
                    success = self.execute_step(execution, parallel_step)
                    if success:
                        results.append(parallel_step.result)
                    else:
                        raise RuntimeError(f"Parallel step {parallel_step.step_id} failed")
                
                step.result = results
            else:
                step.result = self._simulate_agent_action(step.agent, step.action, resolved_input)
            
            if step.output_var:
                execution.variables[step.output_var] = step.result
                execution.step_results[step.step_id] = step.result
            
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now(timezone.utc)
            execution.completed_steps.append(step.step_id)
            
            return True
            
        except Exception as e:
            step.error = str(e)
            step.status = StepStatus.FAILED
            execution.failed_steps.append(step.step_id)
            execution.error_log.append({
                "step_id": step.step_id,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            
            retry_config = step.retry_config or execution.workflow_def.error_handling
            max_retries = retry_config.get("max_retries", 0)
            
            if max_retries > 0 and step.metadata.get("retry_count", 0) < max_retries:
                step.metadata["retry_count"] = step.metadata.get("retry_count", 0) + 1
                step.status = StepStatus.RETRYING
                return self.execute_step(execution, step)
            
            fallback_agent = retry_config.get("fallback_agent")
            if fallback_agent:
                step.agent = fallback_agent
                return self.execute_step(execution, step)
            
            return False

    def _simulate_agent_action(self, agent: str, action: str, input_data: Any) -> Any:
        """
        模拟Agent动作执行（实际应用中替换为真实的Agent调用）
        
        Args:
            agent: Agent标识
            action: 动作名称
            input_data: 输入数据
            
        Returns:
            模拟的执行结果
        """
        return {
            "agent": agent,
            "action": action,
            "status": "completed",
            "result": f"[Simulated] {agent} executed {action}",
            "input_summary": str(input_data)[:100] if input_data else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _resolve_variables(self, variables: dict[str, Any], template: Any) -> Any:
        """
        解析模板中的变量引用（${variable}语法）
        
        Args:
            variables: 变量字典
            template: 可能包含变量引用的模板（字符串、列表或字典）
            
        Returns:
            变量替换后的结果
        """
        if isinstance(template, str):
            def replace_var(match):
                var_name = match.group(1)
                nested_match = self.VARIABLE_PATTERN.match(var_name)
                if nested_match:
                    return str(self._resolve_variables(variables, var_name))
                return str(variables.get(var_name, match.group(0)))
            
            return self.VARIABLE_PATTERN.sub(replace_var, template)
        
        elif isinstance(template, list):
            return [self._resolve_variables(variables, item) for item in template]
        
        elif isinstance(template, dict):
            return {k: self._resolve_variables(variables, v) for k, v in template.items()}
        
        return template

    def evaluate_condition(self, condition: str, variables: dict[str, Any]) -> bool:
        """
        评估条件表达式
        
        Args:
            condition: 条件表达式字符串
            variables: 变量上下文
            
        Returns:
            条件是否为真
        """
        if not condition:
            return True
        
        resolved_condition = self._resolve_variables(variables, condition)
        
        safe_globals = {"__builtins__": {}}
        safe_locals = {**variables}
        
        try:
            result = eval(resolved_condition, safe_globals, safe_locals)
            return bool(result)
        except Exception:
            return True

    def run_workflow(self, execution: WorkflowExecution) -> WorkflowExecution:
        """
        运行完整的工作流
        
        Args:
            execution: 工作流执行实例
            
        Returns:
            完成后的执行实例
        """
        execution.status = WorkflowStatus.RUNNING
        
        for step in execution.workflow_def.steps:
            if step.depends_on:
                dependencies_met = all(
                    dep in execution.completed_steps for dep in step.depends_on
                )
                if not dependencies_met:
                    step.status = StepStatus.SKIPPED
                    continue
            
            if step.condition and not self.evaluate_condition(step.condition, execution.variables):
                step.status = StepStatus.SKIPPED
                continue
            
            success = self.execute_step(execution, step)
            
            if not success:
                error_handler = execution.workflow_def.error_handling.get("on_failure")
                if error_handler == "stop":
                    execution.status = WorkflowStatus.FAILED
                    break
                elif error_handler == "continue":
                    continue
        
        if execution.status != WorkflowStatus.FAILED:
            execution.status = WorkflowStatus.COMPLETED
        
        execution.completed_at = datetime.now(timezone.utc)
        self._persist_state()
        
        return execution

    def pause_workflow(self, execution_id: str) -> bool:
        """暂停指定的工作流执行"""
        if execution_id in self._executions:
            self._executions[execution_id].status = WorkflowStatus.PAUSED
            self._persist_state()
            return True
        return False

    def resume_workflow(self, execution_id: str) -> WorkflowExecution | None:
        """恢复暂停的工作流执行"""
        if execution_id in self._executions:
            execution = self._executions[execution_id]
            if execution.status == WorkflowStatus.PAUSED:
                return self.run_workflow(execution)
        return None

    def cancel_workflow(self, execution_id: str) -> bool:
        """取消指定的工作流执行"""
        if execution_id in self._executions:
            self._executions[execution_id].status = WorkflowStatus.CANCELLED
            self._persist_state()
            return True
        return False

    def _persist_state(self) -> None:
        """持久化工作流状态到JSON文件"""
        state_data = {
            "executions": {},
        }
        
        for exec_id, execution in self._executions.items():
            state_data["executions"][exec_id] = {
                "execution_id": execution.execution_id,
                "workflow_name": execution.workflow_def.name,
                "status": execution.status.value,
                "variables": execution.variables,
                "completed_steps": execution.completed_steps,
                "failed_steps": execution.failed_steps,
                "step_results": {k: str(v) for k, v in execution.step_results.items()},
                "started_at": execution.started_at.isoformat(),
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            }
        
        self._state_file.write_text(json.dumps(state_data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_execution_status(self, execution_id: str) -> dict[str, Any]:
        """获取工作流执行状态"""
        if execution_id not in self._executions:
            return {"error": "Execution not found"}
        
        execution = self._executions[execution_id]
        return {
            "execution_id": execution.execution_id,
            "workflow": execution.workflow_def.name,
            "status": execution.status.value,
            "progress": f"{len(execution.completed_steps)}/{len(execution.workflow_def.steps)}",
            "variables": execution.variables,
            "errors": len(execution.error_log),
        }

    def generate_sample_workflow(self) -> WorkflowDefinition:
        """生成示例工作流定义"""
        sample_yaml = """
name: full_stack_development_workflow
version: "1.0"
description: "全栈功能开发标准工作流"

steps:
  - id: step_1_requirements
    agent: Product Manager
    action: analyze_requirements
    input: "${user_request}"
    output: prd_document
    
  - id: step_2_architecture
    agent: Solution Architect
    action: design_architecture
    input: "${prd_document}"
    output: architecture_doc
    depends_on: [step_1_requirements]
    
  - id: step_3_frontend_backend_parallel
    type: parallel
    steps:
      - id: step_3a_frontend
        agent: Frontend Developer
        action: implement_ui
        input: "${architecture_doc}"
        output: frontend_code
        depends_on: [step_2_architecture]
        
      - id: step_3b_backend
        agent: Backend Developer
        action: implement_api
        input: "${architecture_doc}"
        output: backend_code
        depends_on: [step_2_architecture]
      
    - id: step_4_testing
      agent: QA Engineer
      action: test_integration
      input: ["${frontend_code}", "${backend_code}"]
      output: test_report
      depends_on: [step_3_frontend_backend_parallel]
      
    - id: step_5_review
      agent: Code Reviewer
      action: review_code
      input: ["${frontend_code}", "${backend_code}", "${test_report}"]
      output: review_report
      depends_on: [step_4_testing]
      condition: "${test_report.pass_rate} > 80%"

error_handling:
  on_failure: retry_with_alternative_agent
  max_retries: 2
  fallback_agent: Senior Developer
"""
        return self.load_workflow_from_yaml(sample_yaml.strip())


class OpenClaudeOrchestrator:
    """
    OpenClaude Agent编排协调器主类
    
    整合工作流引擎和上下文注入能力，提供统一的Agent编排接口
    """

    def __init__(self, project_root: Path | str | None = None):
        """
        初始化编排器
        
        Args:
            project_root: 项目根目录
        """
        if isinstance(project_root, str):
            project_root = Path(project_root)
        self.project_root = project_root or Path.cwd()
        
        self.engine = WorkflowEngine(
            workflows_dir=self.project_root / "configs" / "workflows"
        )
        self.context_injector = ContextInjector(project_root=self.project_root)
        self._loaded_workflows: dict[str, WorkflowDefinition] = {}

    def initialize(self) -> dict[str, Any]:
        """
        初始化编排器（检测项目上下文并准备环境）
        
        Returns:
            初始化结果信息
        """
        context = self.context_injector.detect_tech_stack()
        
        return {
            "status": "initialized",
            "project_context": {
                "name": context.project_name,
                "language": context.language,
                "framework": context.framework,
                "tech_stack": context.tech_stack,
            },
            "workflows_dir": str(self.engine.workflows_dir),
            "available_workflows": len(self._loaded_workflows),
        }

    def load_workflow(self, workflow_source: str | Path) -> WorkflowDefinition:
        """
        加载工作流定义
        
        Args:
            workflow_source: YAML内容字符串或文件路径
            
        Returns:
            加载的工作流定义
        """
        workflow = self.engine.load_workflow_from_yaml(workflow_source)
        self._loaded_workflows[workflow.name] = workflow
        return workflow

    def execute_workflow(
        self,
        workflow_name: str,
        inputs: dict[str, Any] | None = None,
    ) -> WorkflowExecution:
        """
        执行指定的工作流
        
        Args:
            workflow_name: 工作流名称
            inputs: 输入变量
            
        Returns:
            执行结果
        """
        if workflow_name not in self._loaded_workflows:
            raise ValueError(f"Workflow '{workflow_name}' not loaded")
        
        workflow = self._loaded_workflows[workflow_name]
        execution = self.engine.create_execution(workflow, inputs)
        
        return self.engine.run_workflow(execution)

    def create_and_execute_workflow(
        self,
        yaml_definition: str,
        inputs: dict[str, Any] | None = None,
    ) -> WorkflowExecution:
        """
        从YAML定义创建并立即执行工作流
        
        Args:
            yaml_definition: YAML格式的完整工作流定义
            inputs: 输入变量
            
        Returns:
            执行结果
        """
        workflow = self.load_workflow(yaml_definition)
        return self.execute_workflow(workflow.name, inputs)

    def get_enhanced_prompt(self, base_prompt: str) -> str:
        """
        获取增强后的提示词（包含项目上下文）
        
        Args:
            base_prompt: 基础提示词
            
        Returns:
            注入上下文后的提示词
        """
        return self.context_injector.inject_context_to_prompt(base_prompt)

    def list_available_workflows(self) -> list[dict[str, str]]:
        """列出所有已加载的工作流"""
        return [
            {
                "name": w.name,
                "version": w.version,
                "description": w.description,
                "steps_count": len(w.steps),
            }
            for w in self._loaded_workflows.values()
        ]

    def get_project_context(self) -> ProjectContext:
        """获取当前项目上下文"""
        return self.context_injector.get_context()
