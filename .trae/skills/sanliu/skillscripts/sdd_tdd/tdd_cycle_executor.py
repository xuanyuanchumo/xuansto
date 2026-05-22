#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDD红绿蓝循环执行器

实现完整的TDD红绿蓝循环：
1. 红阶段：生成测试用例（预期失败）
2. 绿阶段：生成代码实现（使测试通过）
3. 蓝阶段：重构优化代码
4. 循环完整性验证
"""

import ast
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class TDDCyclePhase(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class CodeLanguage(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"


class RefactoringType(Enum):
    EXTRACT_METHOD = "extract_method"
    EXTRACT_VARIABLE = "extract_variable"
    RENAME = "rename"
    REMOVE_DUPLICATION = "remove_duplication"
    SIMPLIFY_CONDITIONAL = "simplify_conditional"
    INTRODUCE_PARAMETER = "introduce_parameter"
    ENCAPSULATE_FIELD = "encapsulate_field"
    OPTIMIZE_IMPORTS = "optimize_imports"
    IMPROVE_NAMING = "improve_naming"


@dataclass
class TestTemplate:
    name: str
    test_type: str
    template_code: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImplementationSuggestion:
    code_snippet: str
    description: str
    language: CodeLanguage
    confidence: float = 0.8
    dependencies: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)


@dataclass
class RefactoringSuggestion:
    refactoring_type: RefactoringType
    description: str
    original_code: str
    refactored_code: str
    line_start: int
    line_end: int
    impact: str = "medium"
    rationale: str = ""


@dataclass
class CodeQualityMetrics:
    cyclomatic_complexity: int = 0
    lines_of_code: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    maintainability_index: float = 0.0
    duplication_percentage: float = 0.0
    test_coverage: float = 0.0
    issues: List[Dict[str, Any]] = field(default_factory=list)
    coupling_score: float = 0.0
    cohesion_score: float = 0.0
    testability_score: float = 0.0
    security_risk_score: float = 0.0
    technical_debt_score: float = 0.0
    solid_compliance: Dict[str, float] = field(default_factory=dict)
    code_smells: List[Dict[str, Any]] = field(default_factory=list)
    complexity_hotspots: List[Dict[str, Any]] = field(default_factory=list)
    dependency_metrics: Dict[str, Any] = field(default_factory=dict)
    documentation_coverage: float = 0.0
    type_hint_coverage: float = 0.0
    error_handling_score: float = 0.0


@dataclass
class RedPhaseResult:
    test_file: str
    test_cases: List[str]
    test_status: TestStatus
    failure_count: int
    error_message: str = ""
    duration: float = 0.0
    test_output: str = ""
    expected_failures: List[str] = field(default_factory=list)
    generated_test_code: str = ""
    test_templates_used: List[str] = field(default_factory=list)
    coverage_estimate: float = 0.0


@dataclass
class GreenPhaseResult:
    implementation_file: str
    code_generated: bool
    test_status: TestStatus
    passed_count: int
    failed_count: int
    error_message: str = ""
    duration: float = 0.0
    test_output: str = ""
    implementation_code: str = ""
    implementation_suggestions: List[ImplementationSuggestion] = field(default_factory=list)
    language: CodeLanguage = CodeLanguage.PYTHON
    iterations: int = 1
    min_implementation: bool = True


@dataclass
class BluePhaseResult:
    refactored_files: List[str]
    improvements: List[Dict[str, Any]]
    test_status: TestStatus
    code_metrics_before: CodeQualityMetrics = field(default_factory=CodeQualityMetrics)
    code_metrics_after: CodeQualityMetrics = field(default_factory=CodeQualityMetrics)
    error_message: str = ""
    duration: float = 0.0
    refactoring_log: List[str] = field(default_factory=list)
    refactoring_suggestions: List[RefactoringSuggestion] = field(default_factory=list)
    performance_improvements: List[Dict[str, Any]] = field(default_factory=list)
    quality_improvements: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CycleState:
    phase: TDDCyclePhase
    status: str
    start_time: str
    end_time: str = ""
    duration: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class CycleExecutionTrace:
    cycle_id: str
    states: List[CycleState] = field(default_factory=list)
    transitions: List[Dict[str, Any]] = field(default_factory=list)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    rollback_points: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TDDCycleResult:
    spec_id: str
    cycle_id: str
    start_time: str
    end_time: str = ""
    current_phase: TDDCyclePhase = TDDCyclePhase.RED
    red_result: Optional[RedPhaseResult] = None
    green_result: Optional[GreenPhaseResult] = None
    blue_result: Optional[BluePhaseResult] = None
    is_complete: bool = False
    success: bool = False
    cycle_number: int = 1
    total_duration: float = 0.0
    error_message: str = ""
    execution_trace: Optional[CycleExecutionTrace] = None
    phase_metrics: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0


class TDDCycleExecutor:
    """TDD红绿蓝循环执行器"""
    
    TEST_TEMPLATES = {
        "unit_test": TestTemplate(
            name="unit_test",
            test_type="unit",
            template_code='''def test_{test_name}():
    """{description}"""
    # Arrange
    {arrange_code}
    
    # Act
    {act_code}
    
    # Assert
    {assert_code}
''',
            description="标准单元测试模板",
            parameters={"test_name": "", "description": "", "arrange_code": "", "act_code": "", "assert_code": ""}
        ),
        "boundary_test": TestTemplate(
            name="boundary_test",
            test_type="boundary",
            template_code='''@pytest.mark.parametrize("input_value,expected", [
    {test_data}
])
def test_{test_name}_boundary(input_value, expected):
    """边界测试: {description}"""
    # Arrange & Act
    result = {function_call}
    
    # Assert
    assert result == expected
''',
            description="边界值测试模板",
            parameters={"test_name": "", "description": "", "test_data": "", "function_call": ""}
        ),
        "exception_test": TestTemplate(
            name="exception_test",
            test_type="exception",
            template_code='''def test_{test_name}_exception():
    """异常测试: {description}"""
    # Arrange
    {arrange_code}
    
    # Act & Assert
    with pytest.raises({exception_type}) as exc_info:
        {act_code}
    
    assert str(exc_info.value) == "{expected_message}"
''',
            description="异常测试模板",
            parameters={"test_name": "", "description": "", "arrange_code": "", "act_code": "", "exception_type": "Exception", "expected_message": ""}
        ),
        "integration_test": TestTemplate(
            name="integration_test",
            test_type="integration",
            template_code='''def test_{test_name}_integration():
    """集成测试: {description}"""
    # Setup
    {setup_code}
    
    # Exercise
    {exercise_code}
    
    # Verify
    {verify_code}
    
    # Teardown
    {teardown_code}
''',
            description="集成测试模板",
            parameters={"test_name": "", "description": "", "setup_code": "", "exercise_code": "", "verify_code": "", "teardown_code": ""}
        ),
        "e2e_test": TestTemplate(
            name="e2e_test",
            test_type="e2e",
            template_code='''def test_{test_name}_e2e():
    """E2E测试: {description}"""
    # Setup - 准备端到端测试环境
    {setup_code}
    
    # Exercise - 执行用户流程
    {exercise_code}
    
    # Verify - 验证最终状态
    {verify_code}
    
    # Teardown - 清理测试数据
    {teardown_code}
''',
            description="端到端测试模板",
            parameters={"test_name": "", "description": "", "setup_code": "", "exercise_code": "", "verify_code": "", "teardown_code": ""}
        ),
        "performance_test": TestTemplate(
            name="performance_test",
            test_type="performance",
            template_code='''import time

def test_{test_name}_performance():
    """性能测试: {description}"""
    # Arrange
    {arrange_code}
    
    # Act - 测量执行时间
    start_time = time.perf_counter()
    {act_code}
    elapsed_time = time.perf_counter() - start_time
    
    # Assert - 验证性能指标
    assert elapsed_time < {threshold_seconds}, f"执行时间 {{elapsed_time:.3f}}秒 超过阈值 {threshold_seconds}秒"
    {additional_assertions}
''',
            description="性能测试模板",
            parameters={"test_name": "", "description": "", "arrange_code": "", "act_code": "", "threshold_seconds": "1.0", "additional_assertions": ""}
        ),
        "security_test": TestTemplate(
            name="security_test",
            test_type="security",
            template_code='''def test_{test_name}_security():
    """安全测试: {description}"""
    # Arrange - 准备安全测试场景
    {arrange_code}
    
    # Act - 执行安全测试
    {act_code}
    
    # Assert - 验证安全约束
    {assert_code}
''',
            description="安全测试模板",
            parameters={"test_name": "", "description": "", "arrange_code": "", "act_code": "", "assert_code": ""}
        ),
        "contract_test": TestTemplate(
            name="contract_test",
            test_type="contract",
            template_code='''def test_{test_name}_contract():
    """契约测试: {description}"""
    # Arrange - 准备契约验证数据
    {arrange_code}
    
    # Act - 调用服务
    response = {act_code}
    
    # Assert - 验证契约符合性
    assert response.status_code == {expected_status}
    {schema_validation}
''',
            description="契约测试模板",
            parameters={"test_name": "", "description": "", "arrange_code": "", "act_code": "", "expected_status": "200", "schema_validation": ""}
        ),
    }
    
    IMPLEMENTATION_PATTERNS = {
        CodeLanguage.PYTHON: {
            "getter": '''def get_{field}(self) -> {type}:
    return self._{field}''',
            "setter": '''def set_{field}(self, value: {type}) -> None:
    self._{field} = value''',
            "validator": '''def validate_{field}(self, value: {type}) -> bool:
    if not value:
        raise ValueError("{field} is required")
    return True''',
            "crud_create": '''def create(self, data: {model}Create) -> {model}Response:
    entity = {model}Model(**data.model_dump())
    self.db.add(entity)
    self.db.commit()
    self.db.refresh(entity)
    return {model}Response.model_validate(entity)''',
            "crud_read": '''def get_by_id(self, entity_id: int) -> Optional[{model}Response]:
    entity = self.db.query({model}Model).filter({model}Model.id == entity_id).first()
    return {model}Response.model_validate(entity) if entity else None''',
            "crud_update": '''def update(self, entity_id: int, data: {model}Update) -> Optional[{model}Response]:
    entity = self.db.query({model}Model).filter({model}Model.id == entity_id).first()
    if not entity:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(entity, key, value)
    self.db.commit()
    self.db.refresh(entity)
    return {model}Response.model_validate(entity)''',
            "crud_delete": '''def delete(self, entity_id: int) -> bool:
    entity = self.db.query({model}Model).filter({model}Model.id == entity_id).first()
    if not entity:
        return False
    self.db.delete(entity)
    self.db.commit()
    return True''',
            "singleton": '''class {class_name}:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True''',
            "factory": '''class {factory_name}Factory:
    @staticmethod
    def create({params}) -> {product_type}:
        if {condition}:
            return {concrete_product_a}()
        else:
            return {concrete_product_b}()''',
            "strategy": '''class {strategy_name}Strategy:
    def execute(self, {params}) -> {return_type}:
        raise NotImplementedError

class {concrete_strategy_a}(Strategy):
    def execute(self, {params}) -> {return_type}:
        {implementation_a}

class {concrete_strategy_b}(Strategy):
    def execute(self, {params}) -> {return_type}:
        {implementation_b}''',
            "observer": '''class {subject_name}:
    def __init__(self):
        self._observers: List[Observer] = []
    
    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)
    
    def notify(self, {event_params}) -> None:
        for observer in self._observers:
            observer.update(self, {event_params})''',
            "decorator": '''def {decorator_name}(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        {before_logic}
        result = func(*args, **kwargs)
        {after_logic}
        return result
    return wrapper''',
            "adapter": '''class {adapter_name}:
    def __init__(self, adaptee: {adaptee_type}):
        self._adaptee = adaptee
    
    def {method_name}(self, {params}) -> {return_type}:
        return self._adaptee.{adaptee_method}({adaptee_params})''',
            "repository": '''class {entity_name}Repository:
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_id(self, id: int) -> Optional[{entity_name}]:
        return self.db.query({entity_name}Model).filter({entity_name}Model.id == id).first()
    
    def find_all(self) -> List[{entity_name}]:
        return self.db.query({entity_name}Model).all()
    
    def save(self, entity: {entity_name}) -> {entity_name}:
        self.db.add(entity)
        self.db.commit()
        return entity
    
    def delete(self, entity: {entity_name}) -> None:
        self.db.delete(entity)
        self.db.commit()''',
            "service_layer": '''class {service_name}Service:
    def __init__(self, repository: {repository_type}):
        self.repository = repository
    
    def {method_name}(self, {params}) -> {return_type}:
        {business_logic}
        return self.repository.{repository_method}({repository_params})''',
            "builder": '''class {product_name}Builder:
    def __init__(self):
        self._product = {product_name}()
    
    def with_{field_a}(self, value: {type_a}) -> Self:
        self._product.{field_a} = value
        return self
    
    def with_{field_b}(self, value: {type_b}) -> Self:
        self._product.{field_b} = value
        return self
    
    def build(self) -> {product_name}:
        return self._product''',
            "chain_of_responsibility": '''class {handler_name}:
    def __init__(self):
        self._next_handler: Optional[Handler] = None
    
    def set_next(self, handler: Handler) -> Handler:
        self._next_handler = handler
        return handler
    
    def handle(self, request) -> Optional[Response]:
        if self._next_handler:
            return self._next_handler.handle(request)
        return None''',
            "template_method": '''class {abstract_class_name}:
    def template_method(self) -> None:
        self.step_one()
        self.step_two()
        self.hook()
    
    def step_one(self) -> None:
        raise NotImplementedError
    
    def step_two(self) -> None:
        raise NotImplementedError
    
    def hook(self) -> None:
        pass''',
            "state": '''class {context_name}:
    def __init__(self):
        self._state: State = None
    
    def transition_to(self, state: State) -> None:
        self._state = state
        self._state.set_context(self)
    
    def {action_name}(self) -> None:
        self._state.handle()''',
            "command": '''class {command_name}:
    def __init__(self, receiver: {receiver_type}):
        self._receiver = receiver
    
    def execute(self) -> None:
        self._receiver.{action_method}()''',
            "mediator": '''class {mediator_name}:
    def __init__(self):
        self._colleagues: List[Colleague] = []
    
    def register(self, colleague: Colleague) -> None:
        self._colleagues.append(colleague)
    
    def notify(self, sender: Colleague, event: str) -> None:
        for colleague in self._colleagues:
            if colleague != sender:
                colleague.receive(event)''',
            "async_operation": '''async def {operation_name}(self, {params}) -> {return_type}:
    async with asyncio.timeout({timeout}):
        result = await self._{internal_method}({internal_params})
        return result''',
            "cache_pattern": '''def {method_name}(self, {params}) -> {return_type}:
    cache_key = f"{cache_prefix}:{key_params}"
    cached = self._cache.get(cache_key)
    if cached is not None:
        return cached
    
    result = self._{data_fetch_method}({fetch_params})
    self._cache.set(cache_key, result, ttl={cache_ttl})
    return result''',
            "retry_pattern": '''def {method_name}(self, {params}) -> {return_type}:
    for attempt in range({max_retries}):
        try:
            return self._{internal_method}({internal_params})
        except {exception_type} as e:
            if attempt == {max_retries} - 1:
                raise
            time.sleep({retry_delay} * (2 ** attempt))''',
            "circuit_breaker": '''class {circuit_name}CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time = None
        self._state = "closed"
    
    def call(self, func, *args, **kwargs):
        if self._state == "open":
            if time.time() - self._last_failure_time > self._recovery_timeout:
                self._state = "half-open"
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise''',
        }
    }
    
    def __init__(
        self,
        test_command: str = "pytest",
        test_dir: Path = Path("tests"),
        source_dir: Path = Path("src"),
        coverage_threshold: float = 80.0,
        language: CodeLanguage = CodeLanguage.PYTHON,
    ):
        self.test_command = test_command
        self.test_dir = test_dir
        self.source_dir = source_dir
        self.coverage_threshold = coverage_threshold
        self.language = language
        self._cycle_counter = 0
        self._test_templates_used: List[str] = []
        self._current_trace: Optional[CycleExecutionTrace] = None
        self._state_history: List[CycleState] = []
        self._auto_rollback_enabled: bool = True
        self._max_phase_retries: int = 3
    
    def _initialize_trace(self, cycle_id: str) -> None:
        self._current_trace = CycleExecutionTrace(cycle_id=cycle_id)
        self._state_history = []
    
    def _record_state(
        self,
        phase: TDDCyclePhase,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> CycleState:
        state = CycleState(
            phase=phase,
            status=status,
            start_time=datetime.now().isoformat(),
            details=details or {}
        )
        
        if self._current_trace:
            self._current_trace.states.append(state)
        
        self._state_history.append(state)
        
        return state
    
    def _finalize_state(self, state: CycleState, errors: List[str] = None, warnings: List[str] = None) -> None:
        state.end_time = datetime.now().isoformat()
        
        start = datetime.fromisoformat(state.start_time)
        end = datetime.fromisoformat(state.end_time)
        state.duration = (end - start).total_seconds()
        
        if errors:
            state.errors.extend(errors)
        if warnings:
            state.warnings.extend(warnings)
    
    def _record_transition(
        self,
        from_phase: TDDCyclePhase,
        to_phase: TDDCyclePhase,
        reason: str
    ) -> None:
        transition = {
            "from": from_phase.value,
            "to": to_phase.value,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        if self._current_trace:
            self._current_trace.transitions.append(transition)
    
    def _create_checkpoint(self, name: str, data: Dict[str, Any]) -> None:
        checkpoint = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        if self._current_trace:
            self._current_trace.checkpoints.append(checkpoint)
    
    def _create_rollback_point(self, phase: TDDCyclePhase, files: Dict[str, str]) -> None:
        rollback_point = {
            "phase": phase.value,
            "timestamp": datetime.now().isoformat(),
            "files": files.copy()
        }
        
        if self._current_trace:
            self._current_trace.rollback_points.append(rollback_point)
    
    def _calculate_phase_metrics(self, result: TDDCycleResult) -> Dict[str, Any]:
        metrics = {
            "red_phase": {},
            "green_phase": {},
            "blue_phase": {},
            "overall": {}
        }
        
        if result.red_result:
            metrics["red_phase"] = {
                "duration": result.red_result.duration,
                "failure_count": result.red_result.failure_count,
                "test_cases": len(result.red_result.test_cases),
                "coverage_estimate": result.red_result.coverage_estimate
            }
        
        if result.green_result:
            metrics["green_phase"] = {
                "duration": result.green_result.duration,
                "iterations": result.green_result.iterations,
                "passed_count": result.green_result.passed_count,
                "failed_count": result.green_result.failed_count,
                "min_implementation": result.green_result.min_implementation
            }
        
        if result.blue_result:
            metrics["blue_phase"] = {
                "duration": result.blue_result.duration,
                "improvements": len(result.blue_result.improvements),
                "refactoring_suggestions": len(result.blue_result.refactoring_suggestions),
                "quality_improvements": len(result.blue_result.quality_improvements)
            }
        
        metrics["overall"] = {
            "total_duration": result.total_duration,
            "phases_completed": sum([
                1 if result.red_result else 0,
                1 if result.green_result else 0,
                1 if result.blue_result else 0
            ]),
            "success_rate": 1.0 if result.success else 0.0
        }
        
        return metrics
    
    def _calculate_quality_score(self, result: TDDCycleResult) -> float:
        score = 100.0
        
        if result.red_result:
            if result.red_result.test_status != TestStatus.FAILED:
                score -= 30
        
        if result.green_result:
            if result.green_result.test_status != TestStatus.PASSED:
                score -= 40
            if result.green_result.iterations > 3:
                score -= (result.green_result.iterations - 3) * 5
        
        if result.blue_result:
            if result.blue_result.test_status != TestStatus.PASSED:
                score -= 20
            
            metrics_before = result.blue_result.code_metrics_before
            metrics_after = result.blue_result.code_metrics_after
            
            if metrics_after.maintainability_index < metrics_before.maintainability_index:
                score -= 10
        
        if not result.is_complete:
            score -= 20
        
        return max(0.0, round(score, 2))
    
    def execute_automated_cycle(
        self,
        spec,
        test_file: Path,
        implementation_file: Path,
        test_cases: List[str],
        implementation_code: str = "",
        test_template: str = "unit_test",
        auto_fix: bool = True
    ) -> TDDCycleResult:
        self._cycle_counter += 1
        cycle_id = f"CYCLE-{self._cycle_counter:03d}"
        start_time = datetime.now()
        
        self._initialize_trace(cycle_id)
        
        result = TDDCycleResult(
            spec_id=spec.metadata.id if hasattr(spec, 'metadata') else "unknown",
            cycle_id=cycle_id,
            start_time=start_time.isoformat(),
            cycle_number=self._cycle_counter,
            execution_trace=self._current_trace
        )
        
        try:
            result.red_result = self._execute_red_phase_with_tracking(
                test_file, test_cases, spec, test_template
            )
            result.current_phase = TDDCyclePhase.GREEN
            
            if result.red_result.test_status != TestStatus.FAILED:
                result.error_message = "红阶段失败：测试未按预期失败"
                self._finalize_cycle_result(result, start_time)
                return result
            
            self._record_transition(TDDCyclePhase.RED, TDDCyclePhase.GREEN, "Red phase completed")
            
            result.green_result = self._execute_green_phase_with_tracking(
                test_file, implementation_file, implementation_code, spec, auto_fix
            )
            result.current_phase = TDDCyclePhase.BLUE
            
            if result.green_result.test_status != TestStatus.PASSED:
                result.error_message = f"绿阶段失败：{result.green_result.failed_count}个测试未通过"
                self._finalize_cycle_result(result, start_time)
                return result
            
            self._record_transition(TDDCyclePhase.GREEN, TDDCyclePhase.BLUE, "Green phase completed")
            
            result.blue_result = self._execute_blue_phase_with_tracking(
                implementation_file, test_file
            )
            result.current_phase = TDDCyclePhase.BLUE
            
            if result.blue_result.test_status == TestStatus.PASSED:
                result.is_complete = True
                result.success = True
            
            self._finalize_cycle_result(result, start_time)
            
        except Exception as e:
            result.error_message = f"循环执行异常: {str(e)}"
            self._finalize_cycle_result(result, start_time)
        
        return result
    
    def _execute_red_phase_with_tracking(
        self,
        test_file: Path,
        test_cases: List[str],
        spec,
        test_template: str
    ) -> RedPhaseResult:
        state = self._record_state(
            TDDCyclePhase.RED,
            "in_progress",
            {"test_file": str(test_file), "test_cases": test_cases}
        )
        
        self._create_checkpoint("red_phase_start", {
            "test_file": str(test_file),
            "test_cases_count": len(test_cases)
        })
        
        result = self.execute_red_phase(test_file, test_cases, spec, test_template)
        
        errors = []
        warnings = []
        
        if result.test_status == TestStatus.ERROR:
            errors.append(result.error_message)
        elif result.test_status == TestStatus.PASSED:
            warnings.append("测试不应在红阶段通过")
        
        self._finalize_state(state, errors, warnings)
        
        return result
    
    def _execute_green_phase_with_tracking(
        self,
        test_file: Path,
        implementation_file: Path,
        implementation_code: str,
        spec,
        auto_fix: bool
    ) -> GreenPhaseResult:
        state = self._record_state(
            TDDCyclePhase.GREEN,
            "in_progress",
            {"test_file": str(test_file), "implementation_file": str(implementation_file)}
        )
        
        if implementation_file.exists():
            original_code = implementation_file.read_text(encoding="utf-8")
            self._create_rollback_point(TDDCyclePhase.GREEN, {
                str(implementation_file): original_code
            })
        
        self._create_checkpoint("green_phase_start", {
            "implementation_file": str(implementation_file)
        })
        
        result = self.execute_green_phase(
            test_file, implementation_file, implementation_code, spec
        )
        
        errors = []
        warnings = []
        
        if result.test_status == TestStatus.ERROR:
            errors.append(result.error_message)
        elif result.test_status == TestStatus.FAILED:
            if auto_fix and result.iterations < self._max_phase_retries:
                warnings.append(f"尝试自动修复（{result.iterations}次迭代）")
        
        self._finalize_state(state, errors, warnings)
        
        return result
    
    def _execute_blue_phase_with_tracking(
        self,
        implementation_file: Path,
        test_file: Path
    ) -> BluePhaseResult:
        state = self._record_state(
            TDDCyclePhase.BLUE,
            "in_progress",
            {"implementation_file": str(implementation_file)}
        )
        
        if implementation_file.exists():
            original_code = implementation_file.read_text(encoding="utf-8")
            self._create_rollback_point(TDDCyclePhase.BLUE, {
                str(implementation_file): original_code
            })
        
        self._create_checkpoint("blue_phase_start", {
            "implementation_file": str(implementation_file)
        })
        
        result = self.execute_blue_phase(implementation_file, test_file)
        
        errors = []
        warnings = []
        
        if result.test_status == TestStatus.ERROR:
            errors.append(result.error_message)
        elif result.test_status == TestStatus.FAILED:
            errors.append("重构后测试失败")
        
        self._finalize_state(state, errors, warnings)
        
        return result
    
    def _finalize_cycle_result(self, result: TDDCycleResult, start_time: datetime) -> None:
        end_time = datetime.now()
        result.end_time = end_time.isoformat()
        result.total_duration = (end_time - start_time).total_seconds()
        
        result.phase_metrics = self._calculate_phase_metrics(result)
        result.quality_score = self._calculate_quality_score(result)
        
        if self._current_trace:
            result.execution_trace = self._current_trace
    
    def execute_red_phase(
        self,
        test_file: Path,
        test_cases: List[str],
        spec=None,
        test_template: str = "unit_test"
    ) -> RedPhaseResult:
        start_time = datetime.now()
        
        if not test_file.exists():
            generated_code = self._generate_test_file(test_file, test_cases, spec, test_template)
            if not generated_code:
                return RedPhaseResult(
                    test_file=str(test_file),
                    test_cases=test_cases,
                    test_status=TestStatus.ERROR,
                    failure_count=len(test_cases),
                    error_message=f"无法生成测试文件: {test_file}"
                )
        
        try:
            result = subprocess.run(
                [self.test_command, str(test_file), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            output = result.stdout + "\n" + result.stderr
            
            if result.returncode != 0:
                failure_count = output.count("FAILED")
                error_count = output.count("ERROR")
                total_failures = failure_count + error_count
                
                test_code = test_file.read_text(encoding="utf-8") if test_file.exists() else ""
                
                return RedPhaseResult(
                    test_file=str(test_file),
                    test_cases=test_cases,
                    test_status=TestStatus.FAILED,
                    failure_count=total_failures,
                    duration=duration,
                    test_output=output,
                    expected_failures=test_cases,
                    generated_test_code=test_code,
                    test_templates_used=self._test_templates_used.copy(),
                    coverage_estimate=self._estimate_coverage(test_cases, spec)
                )
            else:
                return RedPhaseResult(
                    test_file=str(test_file),
                    test_cases=test_cases,
                    test_status=TestStatus.PASSED,
                    failure_count=0,
                    duration=duration,
                    test_output=output,
                    error_message="红阶段测试不应通过 - 测试应该在实现前失败",
                    generated_test_code=test_file.read_text(encoding="utf-8") if test_file.exists() else "",
                    test_templates_used=self._test_templates_used.copy()
                )
        
        except subprocess.TimeoutExpired:
            return RedPhaseResult(
                test_file=str(test_file),
                test_cases=test_cases,
                test_status=TestStatus.ERROR,
                failure_count=len(test_cases),
                error_message="测试执行超时（60秒）"
            )
        except Exception as e:
            return RedPhaseResult(
                test_file=str(test_file),
                test_cases=test_cases,
                test_status=TestStatus.ERROR,
                failure_count=len(test_cases),
                error_message=f"执行异常: {str(e)}"
            )
    
    def _generate_test_file(
        self,
        test_file: Path,
        test_cases: List[str],
        spec=None,
        template_name: str = "unit_test"
    ) -> str:
        try:
            test_file.parent.mkdir(parents=True, exist_ok=True)
            
            template = self.TEST_TEMPLATES.get(template_name, self.TEST_TEMPLATES["unit_test"])
            self._test_templates_used.append(template_name)
            
            lines = [
                '"""',
                f'自动生成的测试文件',
                f'生成时间: {datetime.now().isoformat()}',
                f'测试框架: {self.test_command}',
                '"""',
                'import pytest',
                'from typing import Optional, List, Dict, Any',
                '',
                '',
            ]
            
            for test_case in test_cases:
                test_code = self._generate_test_case(test_case, template, spec)
                lines.append(test_code)
                lines.append('')
            
            content = '\n'.join(lines)
            test_file.write_text(content, encoding="utf-8")
            return content
            
        except Exception as e:
            print(f"生成测试文件失败: {e}")
            return ""
    
    def _generate_test_case(
        self,
        test_name: str,
        template: TestTemplate,
        spec=None
    ) -> str:
        params = {
            "test_name": test_name,
            "description": f"测试用例: {test_name}",
            "arrange_code": "# TODO: 准备测试数据",
            "act_code": "# TODO: 执行测试操作",
            "assert_code": "assert False  # 红阶段：预期失败",
            "setup_code": "# TODO: 设置测试环境",
            "exercise_code": "# TODO: 执行测试",
            "verify_code": "# TODO: 验证结果",
            "teardown_code": "# TODO: 清理测试环境",
            "test_data": "# TODO: 参数化测试数据",
            "function_call": "# TODO: 函数调用",
            "exception_type": "NotImplementedError",
            "expected_message": "Not implemented",
        }
        
        if spec:
            params = self._customize_test_params(test_name, spec, params)
        
        return template.template_code.format(**params)
    
    def _customize_test_params(
        self,
        test_name: str,
        spec,
        base_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        params = base_params.copy()
        
        if hasattr(spec, 'metadata'):
            params["description"] = f"测试 {spec.metadata.name}: {test_name}"
        
        if "create" in test_name.lower():
            params["arrange_code"] = "data = {}  # TODO: 填充测试数据"
            params["act_code"] = "result = service.create(data)"
            params["assert_code"] = "assert result is not None\n    assert result.id is not None"
        elif "get" in test_name.lower() or "read" in test_name.lower():
            params["arrange_code"] = "entity_id = 1"
            params["act_code"] = "result = service.get_by_id(entity_id)"
            params["assert_code"] = "assert result is not None\n    assert result.id == entity_id"
        elif "update" in test_name.lower():
            params["arrange_code"] = "entity_id = 1\ndata = {}  # TODO: 更新数据"
            params["act_code"] = "result = service.update(entity_id, data)"
            params["assert_code"] = "assert result is not None"
        elif "delete" in test_name.lower():
            params["arrange_code"] = "entity_id = 1"
            params["act_code"] = "success = service.delete(entity_id)"
            params["assert_code"] = "assert success is True"
        
        return params
    
    def _estimate_coverage(self, test_cases: List[str], spec) -> float:
        if not spec:
            return 0.0
        
        total_elements = 0
        if hasattr(spec, 'attributes'):
            total_elements += len(spec.attributes)
        if hasattr(spec, 'endpoints'):
            total_elements += len(spec.endpoints)
        if hasattr(spec, 'scenarios'):
            total_elements += len(spec.scenarios)
        
        if total_elements == 0:
            return 0.0
        
        coverage = min(100.0, (len(test_cases) / total_elements) * 100)
        return round(coverage, 2)
    
    def execute_green_phase(
        self,
        test_file: Path,
        implementation_file: Path,
        implementation_code: str,
        spec=None,
        max_iterations: int = 3
    ) -> GreenPhaseResult:
        start_time = datetime.now()
        
        suggestions = self._generate_implementation_suggestions(test_file, implementation_file, spec)
        
        for iteration in range(1, max_iterations + 1):
            try:
                implementation_file.parent.mkdir(parents=True, exist_ok=True)
                
                if iteration == 1 and implementation_code:
                    code_to_write = implementation_code
                else:
                    code_to_write = self._refine_implementation(
                        implementation_file,
                        test_file,
                        suggestions,
                        iteration
                    )
                
                implementation_file.write_text(code_to_write, encoding="utf-8")
                
                result = subprocess.run(
                    [self.test_command, str(test_file), "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                duration = (datetime.now() - start_time).total_seconds()
                output = result.stdout + "\n" + result.stderr
                
                passed_count = output.count("PASSED")
                failed_count = output.count("FAILED")
                error_count = output.count("ERROR")
                
                if result.returncode == 0:
                    return GreenPhaseResult(
                        implementation_file=str(implementation_file),
                        code_generated=True,
                        test_status=TestStatus.PASSED,
                        passed_count=passed_count,
                        failed_count=0,
                        duration=duration,
                        test_output=output,
                        implementation_code=code_to_write,
                        implementation_suggestions=suggestions,
                        language=self.language,
                        iterations=iteration,
                        min_implementation=True
                    )
                else:
                    if iteration < max_iterations:
                        continue
                    
                    return GreenPhaseResult(
                        implementation_file=str(implementation_file),
                        code_generated=True,
                        test_status=TestStatus.FAILED,
                        passed_count=passed_count,
                        failed_count=failed_count + error_count,
                        duration=duration,
                        test_output=output,
                        implementation_code=code_to_write,
                        implementation_suggestions=suggestions,
                        language=self.language,
                        iterations=iteration,
                        min_implementation=False
                    )
            
            except subprocess.TimeoutExpired:
                return GreenPhaseResult(
                    implementation_file=str(implementation_file),
                    code_generated=False,
                    test_status=TestStatus.ERROR,
                    passed_count=0,
                    failed_count=0,
                    error_message="测试执行超时（60秒）",
                    iterations=iteration,
                    language=self.language
                )
            except Exception as e:
                return GreenPhaseResult(
                    implementation_file=str(implementation_file),
                    code_generated=False,
                    test_status=TestStatus.ERROR,
                    passed_count=0,
                    failed_count=0,
                    error_message=f"执行异常: {str(e)}",
                    iterations=iteration,
                    language=self.language
                )
        
        return GreenPhaseResult(
            implementation_file=str(implementation_file),
            code_generated=False,
            test_status=TestStatus.ERROR,
            passed_count=0,
            failed_count=0,
            error_message=f"达到最大迭代次数 {max_iterations}，测试仍未通过",
            implementation_suggestions=suggestions,
            language=self.language,
            iterations=max_iterations
        )
    
    def _generate_implementation_suggestions(
        self,
        test_file: Path,
        implementation_file: Path,
        spec=None
    ) -> List[ImplementationSuggestion]:
        suggestions = []
        
        if not test_file.exists():
            return suggestions
        
        test_code = test_file.read_text(encoding="utf-8")
        
        test_names = re.findall(r'def (test_\w+)\(', test_code)
        
        for test_name in test_names:
            suggestion = self._create_suggestion_for_test(test_name, spec)
            if suggestion:
                suggestions.append(suggestion)
        
        if spec and hasattr(spec, 'attributes'):
            for attr in spec.attributes:
                if attr.required:
                    suggestions.append(ImplementationSuggestion(
                        code_snippet=f'self.{attr.name} = {attr.name}  # Required field',
                        description=f"实现必填字段 {attr.name} 的赋值",
                        language=self.language,
                        confidence=0.9
                    ))
        
        return suggestions
    
    def _create_suggestion_for_test(
        self,
        test_name: str,
        spec=None
    ) -> Optional[ImplementationSuggestion]:
        patterns = self.IMPLEMENTATION_PATTERNS.get(self.language, {})
        
        if "create" in test_name.lower():
            pattern = patterns.get("crud_create", "")
            if spec and hasattr(spec, 'metadata'):
                pattern = pattern.format(
                    model=spec.metadata.name.replace(' ', ''),
                    model_lower=spec.metadata.name.lower().replace(' ', '_')
                )
            return ImplementationSuggestion(
                code_snippet=pattern,
                description="实现创建功能",
                language=self.language,
                confidence=0.85,
                imports=["from typing import Optional"]
            )
        
        elif "get" in test_name.lower() or "read" in test_name.lower():
            pattern = patterns.get("crud_read", "")
            if spec and hasattr(spec, 'metadata'):
                pattern = pattern.format(model=spec.metadata.name.replace(' ', ''))
            return ImplementationSuggestion(
                code_snippet=pattern,
                description="实现读取功能",
                language=self.language,
                confidence=0.85,
                imports=["from typing import Optional"]
            )
        
        elif "update" in test_name.lower():
            pattern = patterns.get("crud_update", "")
            if spec and hasattr(spec, 'metadata'):
                pattern = pattern.format(model=spec.metadata.name.replace(' ', ''))
            return ImplementationSuggestion(
                code_snippet=pattern,
                description="实现更新功能",
                language=self.language,
                confidence=0.85
            )
        
        elif "delete" in test_name.lower():
            pattern = patterns.get("crud_delete", "")
            return ImplementationSuggestion(
                code_snippet=pattern,
                description="实现删除功能",
                language=self.language,
                confidence=0.85
            )
        
        return None
    
    def _refine_implementation(
        self,
        implementation_file: Path,
        test_file: Path,
        suggestions: List[ImplementationSuggestion],
        iteration: int
    ) -> str:
        if implementation_file.exists():
            current_code = implementation_file.read_text(encoding="utf-8")
        else:
            current_code = self._generate_minimal_implementation(test_file, suggestions)
        
        if iteration > 1:
            current_code = self._apply_suggestions(current_code, suggestions, iteration)
        
        return current_code
    
    def _generate_minimal_implementation(
        self,
        test_file: Path,
        suggestions: List[ImplementationSuggestion]
    ) -> str:
        lines = [
            '"""',
            f'最小实现 - 生成时间: {datetime.now().isoformat()}',
            '"""',
            'from typing import Optional, List, Dict, Any',
            '',
            '',
        ]
        
        if suggestions:
            for suggestion in suggestions[:3]:
                lines.append(f'# {suggestion.description}')
                lines.append(suggestion.code_snippet)
                lines.append('')
        
        if not suggestions:
            lines.extend([
                'class MinimalImplementation:',
                '    """最小实现类"""',
                '    ',
                '    def __init__(self):',
                '        pass',
                '    ',
                '    def placeholder_method(self):',
                '        """占位方法"""',
                '        raise NotImplementedError("待实现")',
                '',
            ])
        
        return '\n'.join(lines)
    
    def _apply_suggestions(
        self,
        current_code: str,
        suggestions: List[ImplementationSuggestion],
        iteration: int
    ) -> str:
        lines = current_code.split('\n')
        
        suggestion_index = min(iteration - 1, len(suggestions) - 1)
        if suggestion_index >= 0 and suggestion_index < len(suggestions):
            suggestion = suggestions[suggestion_index]
            
            if suggestion.code_snippet not in current_code:
                lines.append('')
                lines.append(f'# 迭代 {iteration}: {suggestion.description}')
                lines.append(suggestion.code_snippet)
        
        return '\n'.join(lines)
    
    def execute_blue_phase(
        self,
        implementation_file: Path,
        test_file: Path,
        refactoring_rules: Optional[List[Dict[str, Any]]] = None
    ) -> BluePhaseResult:
        start_time = datetime.now()
        
        try:
            if not implementation_file.exists():
                return BluePhaseResult(
                    refactored_files=[],
                    improvements=[],
                    test_status=TestStatus.ERROR,
                    error_message=f"实现文件不存在: {implementation_file}"
                )
            
            code = implementation_file.read_text(encoding="utf-8")
            metrics_before = self._calculate_code_metrics(code)
            
            refactoring_suggestions = self._analyze_refactoring_opportunities(code)
            
            refactored_code, improvements = self._apply_refactoring(code, refactoring_rules, refactoring_suggestions)
            
            if refactored_code != code:
                implementation_file.write_text(refactored_code, encoding="utf-8")
                
                result = subprocess.run(
                    [self.test_command, str(test_file), "-v"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                duration = (datetime.now() - start_time).total_seconds()
                
                if result.returncode == 0:
                    metrics_after = self._calculate_code_metrics(refactored_code)
                    
                    performance_improvements = self._analyze_performance_improvements(code, refactored_code)
                    quality_improvements = self._analyze_quality_improvements(metrics_before, metrics_after)
                    
                    return BluePhaseResult(
                        refactored_files=[str(implementation_file)],
                        improvements=improvements,
                        test_status=TestStatus.PASSED,
                        code_metrics_before=metrics_before,
                        code_metrics_after=metrics_after,
                        duration=duration,
                        refactoring_log=[imp["description"] for imp in improvements],
                        refactoring_suggestions=refactoring_suggestions,
                        performance_improvements=performance_improvements,
                        quality_improvements=quality_improvements
                    )
                else:
                    implementation_file.write_text(code, encoding="utf-8")
                    return BluePhaseResult(
                        refactored_files=[],
                        improvements=[],
                        test_status=TestStatus.FAILED,
                        error_message="重构后测试失败，已回滚代码",
                        code_metrics_before=metrics_before
                    )
            else:
                duration = (datetime.now() - start_time).total_seconds()
                return BluePhaseResult(
                    refactored_files=[],
                    improvements=[],
                    test_status=TestStatus.PASSED,
                    code_metrics_before=metrics_before,
                    code_metrics_after=metrics_before,
                    duration=duration,
                    refactoring_log=["代码已是最优状态，无需重构"],
                    refactoring_suggestions=refactoring_suggestions
                )
        
        except Exception as e:
            return BluePhaseResult(
                refactored_files=[],
                improvements=[],
                test_status=TestStatus.ERROR,
                error_message=f"重构执行异常: {str(e)}"
            )
    
    def _analyze_refactoring_opportunities(self, code: str) -> List[RefactoringSuggestion]:
        suggestions = []
        
        suggestions.extend(self._detect_duplicate_code(code))
        
        suggestions.extend(self._detect_long_methods(code))
        
        suggestions.extend(self._detect_complex_conditionals(code))
        
        suggestions.extend(self._detect_poor_naming(code))
        
        suggestions.extend(self._detect_code_smells(code))
        
        return suggestions
    
    def _detect_duplicate_code(self, code: str) -> List[RefactoringSuggestion]:
        suggestions = []
        lines = code.split('\n')
        
        code_blocks = {}
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                if stripped not in code_blocks:
                    code_blocks[stripped] = []
                code_blocks[stripped].append(i + 1)
        
        for code_line, line_numbers in code_blocks.items():
            if len(line_numbers) > 2:
                suggestions.append(RefactoringSuggestion(
                    refactoring_type=RefactoringType.REMOVE_DUPLICATION,
                    description=f"检测到重复代码（出现{len(line_numbers)}次）: {code_line[:50]}...",
                    original_code=code_line,
                    refactored_code="# 提取为独立方法",
                    line_start=min(line_numbers),
                    line_end=max(line_numbers),
                    impact="medium",
                    rationale="重复代码应提取为独立方法以提高可维护性"
                ))
        
        return suggestions
    
    def _detect_long_methods(self, code: str) -> List[RefactoringSuggestion]:
        suggestions = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_lines = node.end_lineno - node.lineno + 1
                    if method_lines > 30:
                        suggestions.append(RefactoringSuggestion(
                            refactoring_type=RefactoringType.EXTRACT_METHOD,
                            description=f"方法 '{node.name}' 过长（{method_lines}行），建议拆分",
                            original_code=f"def {node.name}(...):",
                            refactored_code="# 拆分为多个小方法",
                            line_start=node.lineno,
                            line_end=node.end_lineno,
                            impact="high",
                            rationale="长方法难以理解和维护，应拆分为多个职责单一的小方法"
                        ))
        except SyntaxError:
            pass
        
        return suggestions
    
    def _detect_complex_conditionals(self, code: str) -> List[RefactoringSuggestion]:
        suggestions = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            if 'if ' in line or 'elif ' in line:
                condition_count = line.count(' and ') + line.count(' or ')
                if condition_count >= 3:
                    suggestions.append(RefactoringSuggestion(
                        refactoring_type=RefactoringType.SIMPLIFY_CONDITIONAL,
                        description=f"复杂条件表达式（包含{condition_count}个逻辑运算符）",
                        original_code=line.strip(),
                        refactored_code="# 提取条件为独立方法或变量",
                        line_start=i + 1,
                        line_end=i + 1,
                        impact="medium",
                        rationale="复杂条件表达式应提取为有意义的方法或变量"
                    ))
        
        return suggestions
    
    def _detect_poor_naming(self, code: str) -> List[RefactoringSuggestion]:
        suggestions = []
        
        poor_names = []
        for match in re.finditer(r'\b([a-z]|[a-z][a-z\d]|[a-z]{6,})\s*=', code):
            name = match.group(1)
            if len(name) <= 2 and name not in ['i', 'j', 'k', 'x', 'y', 'z', 'id']:
                poor_names.append((name, match.start()))
        
        for name, pos in poor_names:
            line_num = code[:pos].count('\n') + 1
            suggestions.append(RefactoringSuggestion(
                refactoring_type=RefactoringType.IMPROVE_NAMING,
                description=f"变量名 '{name}' 不够描述性",
                original_code=name,
                refactored_code="# 使用更具描述性的名称",
                line_start=line_num,
                line_end=line_num,
                impact="low",
                rationale="变量名应清晰表达其用途"
            ))
        
        return suggestions
    
    def _detect_code_smells(self, code: str) -> List[RefactoringSuggestion]:
        suggestions = []
        
        if 'TODO' in code or 'FIXME' in code or 'XXX' in code:
            suggestions.append(RefactoringSuggestion(
                refactoring_type=RefactoringType.EXTRACT_METHOD,
                description="代码中存在待办事项标记",
                original_code="# TODO/FIXME/XXX",
                refactored_code="# 解决待办事项",
                line_start=1,
                line_end=code.count('\n'),
                impact="low",
                rationale="应解决代码中的待办事项"
            ))
        
        if code.count('print(') > 3:
            suggestions.append(RefactoringSuggestion(
                refactoring_type=RefactoringType.EXTRACT_METHOD,
                description="过多print语句，建议使用日志框架",
                original_code="print(...)",
                refactored_code="logger.info(...)",
                line_start=1,
                line_end=code.count('\n'),
                impact="medium",
                rationale="生产代码应使用日志框架而非print语句"
            ))
        
        return suggestions
    
    def _calculate_code_metrics(self, code: str) -> CodeQualityMetrics:
        lines = code.split("\n")
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith("#")]
        comment_lines = [line for line in lines if line.strip().startswith("#")]
        blank_lines = [line for line in lines if not line.strip()]
        
        complexity = self._calculate_cyclomatic_complexity(code)
        
        maintainability = self._calculate_maintainability_index(code, len(code_lines), complexity)
        
        duplication = self._calculate_duplication_percentage(code)
        
        issues = self._detect_code_issues(code)
        
        coupling_score = self._calculate_coupling_score(code)
        
        cohesion_score = self._calculate_cohesion_score(code)
        
        testability_score = self._calculate_testability_score(code, complexity, coupling_score)
        
        security_risk_score = self._calculate_security_risk_score(code)
        
        technical_debt_score = self._calculate_technical_debt_score(code, complexity, duplication, issues)
        
        solid_compliance = self._calculate_solid_compliance(code)
        
        code_smells = self._detect_code_smells_detailed(code)
        
        complexity_hotspots = self._identify_complexity_hotspots(code)
        
        dependency_metrics = self._analyze_dependencies(code)
        
        documentation_coverage = self._calculate_documentation_coverage(code)
        
        type_hint_coverage = self._calculate_type_hint_coverage(code)
        
        error_handling_score = self._calculate_error_handling_score(code)
        
        return CodeQualityMetrics(
            cyclomatic_complexity=complexity,
            lines_of_code=len(lines),
            code_lines=len(code_lines),
            comment_lines=len(comment_lines),
            blank_lines=len(blank_lines),
            maintainability_index=maintainability,
            duplication_percentage=duplication,
            test_coverage=0.0,
            issues=issues,
            coupling_score=coupling_score,
            cohesion_score=cohesion_score,
            testability_score=testability_score,
            security_risk_score=security_risk_score,
            technical_debt_score=technical_debt_score,
            solid_compliance=solid_compliance,
            code_smells=code_smells,
            complexity_hotspots=complexity_hotspots,
            dependency_metrics=dependency_metrics,
            documentation_coverage=documentation_coverage,
            type_hint_coverage=type_hint_coverage,
            error_handling_score=error_handling_score
        )
    
    def _calculate_coupling_score(self, code: str) -> float:
        coupling_indicators = 0
        total_indicators = 0
        
        coupling_indicators += code.count('import ')
        coupling_indicators += code.count('from ')
        coupling_indicators += len(re.findall(r'self\.\w+\s*=', code))
        
        total_indicators = max(1, coupling_indicators)
        
        score = max(0, 100 - (coupling_indicators * 2))
        return round(min(100, score), 2)
    
    def _calculate_cohesion_score(self, code: str) -> float:
        try:
            tree = ast.parse(code)
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            if not classes:
                return 100.0
            
            total_cohesion = 0.0
            for cls in classes:
                methods = [node for node in cls.body if isinstance(node, ast.FunctionDef)]
                if not methods:
                    continue
                
                instance_vars = set()
                for method in methods:
                    for node in ast.walk(method):
                        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                            if node.value.id == 'self':
                                instance_vars.add(node.attr)
                
                method_count = len(methods)
                if method_count > 0 and instance_vars:
                    cohesion = len(instance_vars) / (method_count * len(instance_vars))
                    total_cohesion += cohesion * 100
                else:
                    total_cohesion += 100
            
            return round(total_cohesion / len(classes), 2)
        except SyntaxError:
            return 50.0
    
    def _calculate_testability_score(self, code: str, complexity: int, coupling: float) -> float:
        score = 100.0
        
        if complexity > 10:
            score -= (complexity - 10) * 3
        
        if coupling < 50:
            score -= (50 - coupling) * 0.5
        
        dependency_injection = code.count('__init__') > 0 and code.count('self.') > 0
        if dependency_injection:
            score += 10
        
        pure_functions = len(re.findall(r'def \w+\([^)]*\)\s*->\s*\w+:', code))
        score += min(10, pure_functions * 2)
        
        return round(max(0, min(100, score)), 2)
    
    def _calculate_security_risk_score(self, code: str) -> float:
        risk_score = 100.0
        
        dangerous_patterns = [
            (r'eval\s*\(', 20),
            (r'exec\s*\(', 20),
            (r'__import__\s*\(', 15),
            (r'subprocess\.(call|run|Popen)', 10),
            (r'os\.system', 15),
            (r'pickle\.loads', 15),
            (r'sql.*\+', 10),
            (r'f".*{.*}.*".*execute', 8),
            (r'password\s*=\s*["\']', 12),
            (r'secret\s*=\s*["\']', 12),
            (r'api_key\s*=\s*["\']', 12),
        ]
        
        for pattern, penalty in dangerous_patterns:
            matches = len(re.findall(pattern, code, re.IGNORECASE))
            risk_score -= matches * penalty
        
        return round(max(0, risk_score), 2)
    
    def _calculate_technical_debt_score(
        self, 
        code: str, 
        complexity: int, 
        duplication: float,
        issues: List[Dict[str, Any]]
    ) -> float:
        debt_score = 0.0
        
        if complexity > 15:
            debt_score += (complexity - 15) * 2
        
        debt_score += duplication * 0.5
        
        debt_score += len([i for i in issues if i.get('severity') == 'high']) * 5
        debt_score += len([i for i in issues if i.get('severity') == 'medium']) * 2
        
        debt_score += code.count('TODO') * 1
        debt_score += code.count('FIXME') * 2
        debt_score += code.count('XXX') * 3
        debt_score += code.count('HACK') * 4
        
        return round(debt_score, 2)
    
    def _calculate_solid_compliance(self, code: str) -> Dict[str, float]:
        compliance = {
            "single_responsibility": 0.0,
            "open_closed": 0.0,
            "liskov_substitution": 0.0,
            "interface_segregation": 0.0,
            "dependency_inversion": 0.0
        }
        
        try:
            tree = ast.parse(code)
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            if classes:
                sr_scores = []
                for cls in classes:
                    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)]
                    public_methods = [m for m in methods if not m.name.startswith('_')]
                    
                    if len(public_methods) <= 5:
                        sr_scores.append(100)
                    elif len(public_methods) <= 10:
                        sr_scores.append(70)
                    else:
                        sr_scores.append(max(0, 100 - (len(public_methods) - 10) * 5))
                
                compliance["single_responsibility"] = round(sum(sr_scores) / len(sr_scores), 2)
            
            inheritance_count = len(re.findall(r'class\s+\w+\s*\([^)]*\):', code))
            if inheritance_count > 0:
                compliance["liskov_substitution"] = 80.0
            
            abstract_patterns = len(re.findall(r'@abstractmethod|ABC|abstract', code))
            if abstract_patterns > 0:
                compliance["open_closed"] = min(100, 50 + abstract_patterns * 10)
                compliance["dependency_inversion"] = min(100, 50 + abstract_patterns * 10)
            
            interface_patterns = len(re.findall(r'Protocol|Interface|ABC', code))
            if interface_patterns > 0:
                compliance["interface_segregation"] = min(100, 60 + interface_patterns * 10)
            
        except SyntaxError:
            pass
        
        return compliance
    
    def _detect_code_smells_detailed(self, code: str) -> List[Dict[str, Any]]:
        smells = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    params = len(node.args.args)
                    if params > 5:
                        smells.append({
                            "type": "long_parameter_list",
                            "location": f"function {node.name}",
                            "line": node.lineno,
                            "severity": "medium" if params <= 7 else "high",
                            "description": f"函数 {node.name} 有 {params} 个参数，建议不超过5个"
                        })
                    
                    if node.body and len(node.body) > 20:
                        smells.append({
                            "type": "long_method",
                            "location": f"function {node.name}",
                            "line": node.lineno,
                            "severity": "medium",
                            "description": f"函数 {node.name} 过长，建议拆分"
                        })
                
                if isinstance(node, ast.ClassDef):
                    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                    if len(methods) > 15:
                        smells.append({
                            "type": "large_class",
                            "location": f"class {node.name}",
                            "line": node.lineno,
                            "severity": "high",
                            "description": f"类 {node.name} 有 {len(methods)} 个方法，建议拆分"
                        })
        
        except SyntaxError:
            pass
        
        if code.count('print(') > 3:
            smells.append({
                "type": "print_statements",
                "location": "multiple",
                "line": 0,
                "severity": "low",
                "description": "发现多个print语句，建议使用日志框架"
            })
        
        nested_ifs = len(re.findall(r'if.*:.*if.*:', code, re.DOTALL))
        if nested_ifs > 2:
            smells.append({
                "type": "nested_conditionals",
                "location": "multiple",
                "line": 0,
                "severity": "medium",
                "description": f"发现 {nested_ifs} 处嵌套条件，建议提取方法或使用卫语句"
            })
        
        return smells
    
    def _identify_complexity_hotspots(self, code: str) -> List[Dict[str, Any]]:
        hotspots = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    local_complexity = 1
                    for child in ast.walk(node):
                        if isinstance(child, ast.If):
                            local_complexity += 1
                        elif isinstance(child, ast.For):
                            local_complexity += 1
                        elif isinstance(child, ast.While):
                            local_complexity += 1
                        elif isinstance(child, ast.ExceptHandler):
                            local_complexity += 1
                    
                    if local_complexity > 10:
                        hotspots.append({
                            "name": node.name,
                            "line": node.lineno,
                            "complexity": local_complexity,
                            "severity": "high" if local_complexity > 20 else "medium",
                            "recommendation": "考虑拆分此函数或简化逻辑"
                        })
        
        except SyntaxError:
            pass
        
        return hotspots
    
    def _analyze_dependencies(self, code: str) -> Dict[str, Any]:
        imports = []
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")
        
        except SyntaxError:
            pass
        
        stdlib_modules = {'os', 'sys', 're', 'json', 'time', 'datetime', 'collections', 'itertools', 'functools', 'typing', 'pathlib', 'subprocess', 'threading', 'asyncio'}
        
        external = [imp for imp in imports if imp.split('.')[0] not in stdlib_modules]
        
        return {
            "total_imports": len(imports),
            "standard_library": len([imp for imp in imports if imp.split('.')[0] in stdlib_modules]),
            "external_dependencies": len(external),
            "dependency_list": imports,
            "external_list": external
        }
    
    def _calculate_documentation_coverage(self, code: str) -> float:
        try:
            tree = ast.parse(code)
            
            total_elements = 0
            documented_elements = 0
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    total_elements += 1
                    if ast.get_docstring(node):
                        documented_elements += 1
            
            if total_elements == 0:
                return 100.0
            
            return round((documented_elements / total_elements) * 100, 2)
        
        except SyntaxError:
            return 0.0
    
    def _calculate_type_hint_coverage(self, code: str) -> float:
        try:
            tree = ast.parse(code)
            
            total_params = 0
            typed_params = 0
            total_returns = 0
            typed_returns = 0
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for arg in node.args.args:
                        total_params += 1
                        if arg.annotation:
                            typed_params += 1
                    
                    total_returns += 1
                    if node.returns:
                        typed_returns += 1
            
            if total_params + total_returns == 0:
                return 100.0
            
            param_coverage = (typed_params / total_params * 100) if total_params > 0 else 100
            return_coverage = (typed_returns / total_returns * 100) if total_returns > 0 else 100
            
            return round((param_coverage + return_coverage) / 2, 2)
        
        except SyntaxError:
            return 0.0
    
    def _calculate_error_handling_score(self, code: str) -> float:
        score = 100.0
        
        try:
            tree = ast.parse(code)
            
            function_count = 0
            try_count = 0
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    function_count += 1
                    for child in ast.walk(node):
                        if isinstance(child, ast.Try):
                            try_count += 1
                            break
            
            if function_count > 0:
                coverage = (try_count / function_count) * 100
                score = min(100, coverage + 20)
            
            bare_except = len(re.findall(r'except\s*:', code))
            score -= bare_except * 15
            
            generic_except = len(re.findall(r'except\s+Exception\s*:', code))
            score -= generic_except * 5
        
        except SyntaxError:
            pass
        
        return round(max(0, score), 2)
    
    def _calculate_cyclomatic_complexity(self, code: str) -> int:
        complexity = 1
        
        complexity += code.count('if ')
        complexity += code.count('elif ')
        complexity += code.count('for ')
        complexity += code.count('while ')
        complexity += code.count(' and ')
        complexity += code.count(' or ')
        complexity += code.count('except ')
        
        return complexity
    
    def _calculate_maintainability_index(self, code: str, loc: int, complexity: int) -> float:
        if loc == 0:
            return 100.0
        
        import math
        
        volume = len(code) * math.log2(len(set(code.split())) + 1) if code else 0
        
        mi = max(0, (171 - 5.2 * math.log(volume + 1) - 0.23 * complexity - 16.2 * math.log(loc + 1)) * 100 / 171)
        
        return round(mi, 2)
    
    def _calculate_duplication_percentage(self, code: str) -> float:
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        if not lines:
            return 0.0
        
        unique_lines = set(lines)
        duplication = (1 - len(unique_lines) / len(lines)) * 100
        
        return round(duplication, 2)
    
    def _detect_code_issues(self, code: str) -> List[Dict[str, Any]]:
        issues = []
        
        if len(code) > 0 and not code.startswith('"""') and not code.startswith("'''"):
            issues.append({
                "type": "missing_docstring",
                "message": "文件缺少模块文档字符串",
                "severity": "low"
            })
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not ast.get_docstring(node):
                        issues.append({
                            "type": "missing_docstring",
                            "message": f"方法 '{node.name}' 缺少文档字符串",
                            "severity": "low",
                            "line": node.lineno
                        })
        except SyntaxError:
            pass
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if len(line) > 100:
                issues.append({
                    "type": "line_too_long",
                    "message": f"行 {i+1} 过长（{len(line)}字符）",
                    "severity": "low",
                    "line": i + 1
                })
        
        return issues
    
    def _analyze_performance_improvements(self, original_code: str, refactored_code: str) -> List[Dict[str, Any]]:
        improvements = []
        
        if 'for ' in original_code and 'for ' not in refactored_code:
            improvements.append({
                "type": "loop_optimization",
                "description": "优化了循环结构",
                "impact": "medium"
            })
        
        if original_code.count('import ') > refactored_code.count('import '):
            improvements.append({
                "type": "import_optimization",
                "description": "优化了导入语句",
                "impact": "low"
            })
        
        return improvements
    
    def _analyze_quality_improvements(
        self,
        metrics_before: CodeQualityMetrics,
        metrics_after: CodeQualityMetrics
    ) -> List[Dict[str, Any]]:
        improvements = []
        
        if metrics_after.cyclomatic_complexity < metrics_before.cyclomatic_complexity:
            reduction = metrics_before.cyclomatic_complexity - metrics_after.cyclomatic_complexity
            improvements.append({
                "type": "complexity_reduction",
                "description": f"降低了圈复杂度（减少{reduction}）",
                "before": metrics_before.cyclomatic_complexity,
                "after": metrics_after.cyclomatic_complexity,
                "impact": "high"
            })
        
        if metrics_after.maintainability_index > metrics_before.maintainability_index:
            increase = metrics_after.maintainability_index - metrics_before.maintainability_index
            improvements.append({
                "type": "maintainability_improvement",
                "description": f"提高了可维护性指数（提高{increase:.2f}）",
                "before": metrics_before.maintainability_index,
                "after": metrics_after.maintainability_index,
                "impact": "high"
            })
        
        if metrics_after.duplication_percentage < metrics_before.duplication_percentage:
            reduction = metrics_before.duplication_percentage - metrics_after.duplication_percentage
            improvements.append({
                "type": "duplication_reduction",
                "description": f"降低了代码重复率（减少{reduction:.2f}%）",
                "before": metrics_before.duplication_percentage,
                "after": metrics_after.duplication_percentage,
                "impact": "medium"
            })
        
        return improvements
    
    def _apply_refactoring(
        self,
        code: str,
        rules: Optional[List[Dict[str, Any]]] = None,
        suggestions: Optional[List[RefactoringSuggestion]] = None
    ) -> tuple[str, List[Dict[str, Any]]]:
        improvements = []
        refactored_code = code
        
        refactored_code, improvement = self._remove_duplicate_code(refactored_code)
        if improvement:
            improvements.append(improvement)
        
        refactored_code, improvement = self._optimize_imports(refactored_code)
        if improvement:
            improvements.append(improvement)
        
        refactored_code, improvement = self._improve_code_formatting(refactored_code)
        if improvement:
            improvements.append(improvement)
        
        refactored_code, improvement = self._add_missing_docstrings(refactored_code)
        if improvement:
            improvements.append(improvement)
        
        return refactored_code, improvements
    
    def _remove_duplicate_code(self, code: str) -> tuple[str, Optional[Dict[str, Any]]]:
        return code, None
    
    def _optimize_imports(self, code: str) -> tuple[str, Optional[Dict[str, Any]]]:
        lines = code.split('\n')
        
        import_lines = []
        other_lines = []
        in_import_section = True
        
        for line in lines:
            if in_import_section:
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    import_lines.append(line)
                elif line.strip() == '':
                    continue
                else:
                    in_import_section = False
                    other_lines.append(line)
            else:
                other_lines.append(line)
        
        import_lines.sort()
        
        optimized_imports = []
        prev_import = ""
        for imp in import_lines:
            if imp != prev_import:
                optimized_imports.append(imp)
                prev_import = imp
        
        if len(optimized_imports) < len(import_lines):
            new_code = '\n'.join(optimized_imports + [''] + other_lines)
            return new_code, {
                "type": "optimize_imports",
                "description": "优化导入语句（去重和排序）",
                "impact": "low"
            }
        
        return code, None
    
    def _improve_code_formatting(self, code: str) -> tuple[str, Optional[Dict[str, Any]]]:
        lines = code.split('\n')
        formatted_lines = []
        
        improvements_made = False
        
        for i, line in enumerate(lines):
            if line.rstrip() != line:
                formatted_lines.append(line.rstrip())
                improvements_made = True
            else:
                formatted_lines.append(line)
        
        if improvements_made:
            return '\n'.join(formatted_lines), {
                "type": "format_improvement",
                "description": "移除行尾空白字符",
                "impact": "low"
            }
        
        return code, None
    
    def _add_missing_docstrings(self, code: str) -> tuple[str, Optional[Dict[str, Any]]]:
        return code, None
    
    def execute_full_cycle(
        self,
        spec,
        test_file: Path,
        implementation_file: Path,
        test_cases: List[str],
        implementation_code: str,
        test_template: str = "unit_test"
    ) -> TDDCycleResult:
        self._cycle_counter += 1
        cycle_id = f"CYCLE-{self._cycle_counter:03d}"
        start_time = datetime.now()
        
        result = TDDCycleResult(
            spec_id=spec.metadata.id if hasattr(spec, 'metadata') else "unknown",
            cycle_id=cycle_id,
            start_time=start_time.isoformat(),
            cycle_number=self._cycle_counter
        )
        
        result.red_result = self.execute_red_phase(test_file, test_cases, spec, test_template)
        result.current_phase = TDDCyclePhase.GREEN
        
        if result.red_result.test_status != TestStatus.FAILED:
            result.error_message = "红阶段失败：测试未按预期失败（测试应该先失败）"
            result.end_time = datetime.now().isoformat()
            result.total_duration = (datetime.now() - start_time).total_seconds()
            return result
        
        result.green_result = self.execute_green_phase(
            test_file, implementation_file, implementation_code, spec
        )
        result.current_phase = TDDCyclePhase.BLUE
        
        if result.green_result.test_status != TestStatus.PASSED:
            result.error_message = f"绿阶段失败：{result.green_result.failed_count}个测试未通过"
            result.end_time = datetime.now().isoformat()
            result.total_duration = (datetime.now() - start_time).total_seconds()
            return result
        
        result.blue_result = self.execute_blue_phase(implementation_file, test_file)
        result.current_phase = TDDCyclePhase.BLUE
        
        if result.blue_result.test_status == TestStatus.PASSED:
            result.is_complete = True
            result.success = True
        
        result.end_time = datetime.now().isoformat()
        result.total_duration = (datetime.now() - start_time).total_seconds()
        
        return result
    
    def verify_cycle_integrity(self, cycle_result: TDDCycleResult) -> Dict[str, Any]:
        verification = {
            "is_valid": True,
            "checks": [],
            "issues": [],
            "phase_status": {},
            "recommendations": [],
            "quality_gates": {},
            "tdd_principles": {},
            "metrics_validation": {}
        }
        
        red_valid = self._verify_red_phase(cycle_result, verification)
        green_valid = self._verify_green_phase(cycle_result, verification)
        blue_valid = self._verify_blue_phase(cycle_result, verification)
        
        self._verify_tdd_principles(cycle_result, verification)
        
        self._verify_quality_gates(cycle_result, verification)
        
        self._verify_metrics_progression(cycle_result, verification)
        
        if cycle_result.is_complete and cycle_result.success:
            verification["checks"].append("✓ 循环完整性验证通过")
            verification["checks"].append(f"  - 总耗时: {cycle_result.total_duration:.2f}秒")
            verification["checks"].append(f"  - 循环编号: {cycle_result.cycle_number}")
        else:
            verification["is_valid"] = False
            verification["issues"].append("TDD循环未完整执行")
        
        if not verification["is_valid"]:
            verification["recommendations"].extend([
                "建议：确保严格遵循TDD红-绿-蓝循环",
                "1. 红阶段：先编写失败的测试",
                "2. 绿阶段：编写最小实现使测试通过",
                "3. 蓝阶段：重构代码并确保测试仍然通过"
            ])
        
        verification["overall_score"] = self._calculate_cycle_score(verification)
        
        return verification
    
    def _verify_red_phase(self, cycle_result: TDDCycleResult, verification: Dict[str, Any]) -> bool:
        if not cycle_result.red_result:
            verification["is_valid"] = False
            verification["issues"].append("缺少红阶段结果")
            verification["phase_status"]["red"] = "missing"
            return False
        
        if cycle_result.red_result.test_status != TestStatus.FAILED:
            verification["is_valid"] = False
            verification["issues"].append("红阶段测试应失败（测试先行原则）")
            verification["phase_status"]["red"] = "invalid"
            return False
        
        verification["checks"].append("✓ 红阶段验证通过：测试正确失败")
        verification["phase_status"]["red"] = "passed"
        
        if cycle_result.red_result.coverage_estimate > 0:
            verification["checks"].append(
                f"  - 测试覆盖率估计: {cycle_result.red_result.coverage_estimate}%"
            )
        
        if cycle_result.red_result.test_templates_used:
            verification["checks"].append(
                f"  - 使用测试模板: {', '.join(cycle_result.red_result.test_templates_used)}"
            )
        
        if cycle_result.red_result.failure_count == 0:
            verification["issues"].append("红阶段应有测试失败")
            return False
        
        if len(cycle_result.red_result.test_cases) == 0:
            verification["issues"].append("红阶段应至少有一个测试用例")
            return False
        
        return True
    
    def _verify_green_phase(self, cycle_result: TDDCycleResult, verification: Dict[str, Any]) -> bool:
        if not cycle_result.green_result:
            verification["is_valid"] = False
            verification["issues"].append("缺少绿阶段结果")
            verification["phase_status"]["green"] = "missing"
            return False
        
        if cycle_result.green_result.test_status != TestStatus.PASSED:
            verification["is_valid"] = False
            verification["issues"].append(f"绿阶段测试应通过（{cycle_result.green_result.failed_count}个测试失败）")
            verification["phase_status"]["green"] = "failed"
            return False
        
        verification["checks"].append("✓ 绿阶段验证通过：所有测试通过")
        verification["phase_status"]["green"] = "passed"
        
        verification["checks"].append(
            f"  - 通过测试数: {cycle_result.green_result.passed_count}"
        )
        verification["checks"].append(
            f"  - 迭代次数: {cycle_result.green_result.iterations}"
        )
        
        if cycle_result.green_result.min_implementation:
            verification["checks"].append("  - 实现了最小可行代码")
        
        if cycle_result.green_result.implementation_suggestions:
            verification["checks"].append(
                f"  - 实现建议数: {len(cycle_result.green_result.implementation_suggestions)}"
            )
        
        if cycle_result.green_result.iterations > 5:
            verification["issues"].append("绿阶段迭代次数过多，可能实现过于复杂")
        
        if cycle_result.green_result.passed_count < len(cycle_result.red_result.test_cases) if cycle_result.red_result else 0:
            verification["issues"].append("绿阶段通过的测试数少于红阶段定义的测试数")
        
        return True
    
    def _verify_blue_phase(self, cycle_result: TDDCycleResult, verification: Dict[str, Any]) -> bool:
        if not cycle_result.blue_result:
            verification["issues"].append("缺少蓝阶段结果")
            verification["phase_status"]["blue"] = "missing"
            return False
        
        if cycle_result.blue_result.test_status == TestStatus.PASSED:
            verification["checks"].append("✓ 蓝阶段验证通过：重构后测试仍通过")
            verification["phase_status"]["blue"] = "passed"
            
            if cycle_result.blue_result.improvements:
                verification["checks"].append(
                    f"  - 重构改进数: {len(cycle_result.blue_result.improvements)}"
                )
            
            if cycle_result.blue_result.refactoring_suggestions:
                verification["checks"].append(
                    f"  - 重构建议数: {len(cycle_result.blue_result.refactoring_suggestions)}"
                )
            
            if cycle_result.blue_result.quality_improvements:
                verification["checks"].append(
                    f"  - 质量改进数: {len(cycle_result.blue_result.quality_improvements)}"
                )
            
            metrics_before = cycle_result.blue_result.code_metrics_before
            metrics_after = cycle_result.blue_result.code_metrics_after
            
            if metrics_after.maintainability_index > metrics_before.maintainability_index:
                verification["checks"].append(
                    f"  - 可维护性提升: {metrics_before.maintainability_index:.2f} → {metrics_after.maintainability_index:.2f}"
                )
            
            if metrics_after.cyclomatic_complexity < metrics_before.cyclomatic_complexity:
                verification["checks"].append(
                    f"  - 复杂度降低: {metrics_before.cyclomatic_complexity} → {metrics_after.cyclomatic_complexity}"
                )
        else:
            verification["issues"].append("蓝阶段测试应保持通过")
            verification["phase_status"]["blue"] = "failed"
            return False
        
        return True
    
    def _verify_tdd_principles(self, cycle_result: TDDCycleResult, verification: Dict[str, Any]) -> None:
        principles = {
            "test_first": False,
            "minimal_implementation": False,
            "refactor_safety": False,
            "fast_feedback": False,
            "single_responsibility": False
        }
        
        if cycle_result.red_result and cycle_result.green_result:
            if cycle_result.red_result.duration < cycle_result.green_result.duration:
                principles["test_first"] = True
        
        if cycle_result.green_result and cycle_result.green_result.min_implementation:
            principles["minimal_implementation"] = True
        
        if cycle_result.blue_result and cycle_result.blue_result.test_status == TestStatus.PASSED:
            principles["refactor_safety"] = True
        
        if cycle_result.total_duration < 300:
            principles["fast_feedback"] = True
        
        if cycle_result.blue_result:
            metrics = cycle_result.blue_result.code_metrics_after
            if metrics.cyclomatic_complexity < 15:
                principles["single_responsibility"] = True
        
        verification["tdd_principles"] = principles
        
        failed_principles = [p for p, v in principles.items() if not v]
        if failed_principles:
            verification["issues"].append(f"TDD原则未完全遵循: {', '.join(failed_principles)}")
    
    def _verify_quality_gates(self, cycle_result: TDDCycleResult, verification: Dict[str, Any]) -> None:
        gates = {
            "complexity_gate": False,
            "coverage_gate": False,
            "maintainability_gate": False,
            "security_gate": False,
            "duplication_gate": False
        }
        
        if cycle_result.blue_result:
            metrics = cycle_result.blue_result.code_metrics_after
            
            if metrics.cyclomatic_complexity <= 15:
                gates["complexity_gate"] = True
            
            if metrics.test_coverage >= self.coverage_threshold:
                gates["coverage_gate"] = True
            
            if metrics.maintainability_index >= 65:
                gates["maintainability_gate"] = True
            
            if metrics.security_risk_score >= 80:
                gates["security_gate"] = True
            
            if metrics.duplication_percentage <= 10:
                gates["duplication_gate"] = True
        
        verification["quality_gates"] = gates
        
        failed_gates = [g for g, v in gates.items() if not v]
        if failed_gates:
            for gate in failed_gates:
                verification["recommendations"].append(f"质量门禁未通过: {gate}")
    
    def _verify_metrics_progression(self, cycle_result: TDDCycleResult, verification: Dict[str, Any]) -> None:
        metrics_validation = {
            "complexity_improved": False,
            "maintainability_improved": False,
            "duplication_reduced": False,
            "testability_improved": False,
            "technical_debt_reduced": False
        }
        
        if cycle_result.blue_result:
            before = cycle_result.blue_result.code_metrics_before
            after = cycle_result.blue_result.code_metrics_after
            
            if after.cyclomatic_complexity <= before.cyclomatic_complexity:
                metrics_validation["complexity_improved"] = True
            
            if after.maintainability_index >= before.maintainability_index:
                metrics_validation["maintainability_improved"] = True
            
            if after.duplication_percentage <= before.duplication_percentage:
                metrics_validation["duplication_reduced"] = True
            
            if after.testability_score >= before.testability_score:
                metrics_validation["testability_improved"] = True
            
            if after.technical_debt_score <= before.technical_debt_score:
                metrics_validation["technical_debt_reduced"] = True
        
        verification["metrics_validation"] = metrics_validation
    
    def _calculate_cycle_score(self, verification: Dict[str, Any]) -> float:
        score = 100.0
        
        score -= len(verification.get("issues", [])) * 10
        
        if verification.get("tdd_principles"):
            failed_principles = len([p for p, v in verification["tdd_principles"].items() if not v])
            score -= failed_principles * 5
        
        if verification.get("quality_gates"):
            failed_gates = len([g for g, v in verification["quality_gates"].items() if not v])
            score -= failed_gates * 8
        
        if verification.get("metrics_validation"):
            failed_metrics = len([m for m, v in verification["metrics_validation"].items() if not v])
            score -= failed_metrics * 3
        
        return round(max(0, score), 2)
    
    def generate_cycle_report(self, cycle_result: TDDCycleResult) -> Dict[str, Any]:
        report = {
            "report_id": f"REPORT-{cycle_result.cycle_id}",
            "generated_at": datetime.now().isoformat(),
            "cycle_summary": {
                "cycle_id": cycle_result.cycle_id,
                "spec_id": cycle_result.spec_id,
                "success": cycle_result.success,
                "is_complete": cycle_result.is_complete,
                "total_duration": cycle_result.total_duration,
                "start_time": cycle_result.start_time,
                "end_time": cycle_result.end_time,
                "quality_score": cycle_result.quality_score,
            },
            "red_phase": {},
            "green_phase": {},
            "blue_phase": {},
            "verification": {},
            "metrics_summary": {},
            "execution_trace": {},
            "phase_metrics": cycle_result.phase_metrics,
            "recommendations": []
        }
        
        if cycle_result.red_result:
            report["red_phase"] = {
                "test_file": cycle_result.red_result.test_file,
                "test_cases_count": len(cycle_result.red_result.test_cases),
                "expected_failures": len(cycle_result.red_result.expected_failures),
                "duration": cycle_result.red_result.duration,
                "coverage_estimate": cycle_result.red_result.coverage_estimate,
                "templates_used": cycle_result.red_result.test_templates_used,
                "status": cycle_result.red_result.test_status.value,
                "test_cases": cycle_result.red_result.test_cases[:10],
            }
        
        if cycle_result.green_result:
            report["green_phase"] = {
                "implementation_file": cycle_result.green_result.implementation_file,
                "passed_count": cycle_result.green_result.passed_count,
                "failed_count": cycle_result.green_result.failed_count,
                "iterations": cycle_result.green_result.iterations,
                "duration": cycle_result.green_result.duration,
                "language": cycle_result.green_result.language.value,
                "min_implementation": cycle_result.green_result.min_implementation,
                "suggestions_count": len(cycle_result.green_result.implementation_suggestions),
                "status": cycle_result.green_result.test_status.value,
            }
        
        if cycle_result.blue_result:
            report["blue_phase"] = {
                "refactored_files": cycle_result.blue_result.refactored_files,
                "improvements_count": len(cycle_result.blue_result.improvements),
                "refactoring_suggestions_count": len(cycle_result.blue_result.refactoring_suggestions),
                "quality_improvements_count": len(cycle_result.blue_result.quality_improvements),
                "performance_improvements_count": len(cycle_result.blue_result.performance_improvements),
                "duration": cycle_result.blue_result.duration,
                "status": cycle_result.blue_result.test_status.value,
                "metrics": {
                    "before": {
                        "cyclomatic_complexity": cycle_result.blue_result.code_metrics_before.cyclomatic_complexity,
                        "maintainability_index": cycle_result.blue_result.code_metrics_before.maintainability_index,
                        "lines_of_code": cycle_result.blue_result.code_metrics_before.lines_of_code,
                        "duplication_percentage": cycle_result.blue_result.code_metrics_before.duplication_percentage,
                    },
                    "after": {
                        "cyclomatic_complexity": cycle_result.blue_result.code_metrics_after.cyclomatic_complexity,
                        "maintainability_index": cycle_result.blue_result.code_metrics_after.maintainability_index,
                        "lines_of_code": cycle_result.blue_result.code_metrics_after.lines_of_code,
                        "duplication_percentage": cycle_result.blue_result.code_metrics_after.duplication_percentage,
                    }
                }
            }
        
        report["verification"] = self.verify_cycle_integrity(cycle_result)
        
        if cycle_result.blue_result:
            metrics_before = cycle_result.blue_result.code_metrics_before
            metrics_after = cycle_result.blue_result.code_metrics_after
            
            report["metrics_summary"] = {
                "complexity_change": metrics_after.cyclomatic_complexity - metrics_before.cyclomatic_complexity,
                "maintainability_change": metrics_after.maintainability_index - metrics_before.maintainability_index,
                "duplication_change": metrics_after.duplication_percentage - metrics_before.duplication_percentage,
                "lines_change": metrics_after.lines_of_code - metrics_before.lines_of_code,
            }
        
        if not cycle_result.success:
            report["recommendations"].append("TDD循环未成功完成，请检查错误信息")
            if cycle_result.error_message:
                report["recommendations"].append(f"错误: {cycle_result.error_message}")
        
        if cycle_result.blue_result and cycle_result.blue_result.refactoring_suggestions:
            high_priority = [
                s for s in cycle_result.blue_result.refactoring_suggestions
                if s.impact == "high"
            ]
            if high_priority:
                report["recommendations"].append(
                    f"建议优先处理{len(high_priority)}个高优先级重构项"
                )
        
        if cycle_result.execution_trace:
            report["execution_trace"] = {
                "cycle_id": cycle_result.execution_trace.cycle_id,
                "total_states": len(cycle_result.execution_trace.states),
                "total_transitions": len(cycle_result.execution_trace.transitions),
                "total_checkpoints": len(cycle_result.execution_trace.checkpoints),
                "total_rollback_points": len(cycle_result.execution_trace.rollback_points),
                "states": [
                    {
                        "phase": state.phase.value,
                        "status": state.status,
                        "duration": state.duration,
                        "errors": state.errors,
                        "warnings": state.warnings,
                    }
                    for state in cycle_result.execution_trace.states
                ],
                "transitions": cycle_result.execution_trace.transitions,
                "checkpoints": [
                    {
                        "name": cp["name"],
                        "timestamp": cp["timestamp"],
                    }
                    for cp in cycle_result.execution_trace.checkpoints
                ],
            }
        
        return report
    
    def save_cycle_report(
        self,
        cycle_result: TDDCycleResult,
        output_dir: Optional[Path] = None
    ) -> Path:
        if output_dir is None:
            output_dir = Path("reports")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report = self.generate_cycle_report(cycle_result)
        
        import json
        report_file = output_dir / f"tdd_cycle_report_{cycle_result.cycle_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report_file


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="TDD红绿蓝循环执行器")
    parser.add_argument("--test-file", required=True, help="测试文件路径")
    parser.add_argument("--impl-file", required=True, help="实现文件路径")
    parser.add_argument("--impl-code", help="实现代码（可选，从文件读取）")
    parser.add_argument("--phase", choices=["red", "green", "blue", "full"], default="full", help="执行阶段")
    parser.add_argument("--template", default="unit_test", help="测试模板类型")
    parser.add_argument("--report-dir", default="reports", help="报告输出目录")
    parser.add_argument("--language", choices=["python", "typescript", "java", "go"], default="python", help="编程语言")
    
    args = parser.parse_args()
    
    language_map = {
        "python": CodeLanguage.PYTHON,
        "typescript": CodeLanguage.TYPESCRIPT,
        "java": CodeLanguage.JAVA,
        "go": CodeLanguage.GO,
    }
    
    executor = TDDCycleExecutor(language=language_map[args.language])
    
    test_file = Path(args.test_file)
    impl_file = Path(args.impl_file)
    
    if args.impl_code:
        impl_code = args.impl_code
    elif impl_file.exists():
        impl_code = impl_file.read_text(encoding="utf-8")
    else:
        impl_code = ""
    
    test_cases = ["test_example"]
    
    if args.phase == "red":
        result = executor.execute_red_phase(test_file, test_cases, test_template=args.template)
        print(f"\n{'='*60}")
        print("红阶段执行结果")
        print(f"{'='*60}")
        print(f"状态: {result.test_status.value}")
        print(f"失败数: {result.failure_count}")
        print(f"耗时: {result.duration:.2f}秒")
        if result.coverage_estimate > 0:
            print(f"覆盖率估计: {result.coverage_estimate}%")
        if result.test_templates_used:
            print(f"使用模板: {', '.join(result.test_templates_used)}")
        if result.error_message:
            print(f"错误: {result.error_message}")
    
    elif args.phase == "green":
        result = executor.execute_green_phase(test_file, impl_file, impl_code)
        print(f"\n{'='*60}")
        print("绿阶段执行结果")
        print(f"{'='*60}")
        print(f"状态: {result.test_status.value}")
        print(f"通过: {result.passed_count}, 失败: {result.failed_count}")
        print(f"迭代次数: {result.iterations}")
        print(f"耗时: {result.duration:.2f}秒")
        print(f"最小实现: {'是' if result.min_implementation else '否'}")
        if result.implementation_suggestions:
            print(f"实现建议数: {len(result.implementation_suggestions)}")
        if result.error_message:
            print(f"错误: {result.error_message}")
    
    elif args.phase == "blue":
        result = executor.execute_blue_phase(impl_file, test_file)
        print(f"\n{'='*60}")
        print("蓝阶段执行结果")
        print(f"{'='*60}")
        print(f"状态: {result.test_status.value}")
        print(f"改进项: {len(result.improvements)}")
        print(f"重构建议: {len(result.refactoring_suggestions)}")
        print(f"质量改进: {len(result.quality_improvements)}")
        print(f"耗时: {result.duration:.2f}秒")
        
        if result.code_metrics_before and result.code_metrics_after:
            print(f"\n代码质量指标:")
            print(f"  圈复杂度: {result.code_metrics_before.cyclomatic_complexity} → {result.code_metrics_after.cyclomatic_complexity}")
            print(f"  可维护性指数: {result.code_metrics_before.maintainability_index:.2f} → {result.code_metrics_after.maintainability_index:.2f}")
            print(f"  代码重复率: {result.code_metrics_before.duplication_percentage:.2f}% → {result.code_metrics_after.duplication_percentage:.2f}%")
        
        if result.error_message:
            print(f"错误: {result.error_message}")
    
    else:
        print("完整TDD循环需要规范文件，请使用SDD-TDD集成模块")
        print("或使用 --phase 参数指定单独阶段")


if __name__ == "__main__":
    main()
