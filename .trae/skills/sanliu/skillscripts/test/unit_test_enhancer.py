"""
单元测试智能增强框架

提供智能测试发现、未覆盖代码分析、增强测试覆盖率报告等功能
支持配置文件、失败诊断、HTML报告生成
"""

import os
import sys
import ast
import json
import importlib
import inspect
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import re
import traceback

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class TestDiscoveryStrategy(Enum):
    NAME_PATTERN = "name_pattern"
    DECORATOR = "decorator"
    DOCSTRING = "docstring"
    INHERITANCE = "inheritance"
    CONFIGURATION = "configuration"
    DEPENDENCY_GRAPH = "dependency_graph"
    MUTATION_SCORE = "mutation_score"
    CODE_SMELL = "code_smell"


class TestPattern(Enum):
    PARAMETRIZED = "parametrized"
    MOCK = "mock"
    ASYNC = "async"
    EXCEPTION = "exception"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"
    PROPERTY_BASED = "property_based"
    FUZZ = "fuzz"
    SNAPSHOT = "snapshot"
    CONTRACT = "contract"


class CoverageGapType(Enum):
    MISSING_FUNCTION = "missing_function"
    MISSING_CLASS = "missing_class"
    MISSING_BRANCH = "missing_branch"
    MISSING_LINE = "missing_line"
    MISSING_EXCEPTION = "missing_exception"
    MISSING_BOUNDARY = "missing_boundary"
    MISSING_PARAMETER = "missing_parameter"
    MISSING_RETURN_PATH = "missing_return_path"


class FailureCategory(Enum):
    ASSERTION_ERROR = "assertion_error"
    IMPORT_ERROR = "import_error"
    ATTRIBUTE_ERROR = "attribute_error"
    TYPE_ERROR = "type_error"
    VALUE_ERROR = "value_error"
    TIMEOUT_ERROR = "timeout_error"
    FIXTURE_ERROR = "fixture_error"
    DEPENDENCY_ERROR = "dependency_error"
    UNKNOWN = "unknown"


@dataclass
class CodeElement:
    name: str
    type: str
    file_path: str
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    is_tested: bool = False
    complexity: int = 0


@dataclass
class CoverageGap:
    element: CodeElement
    gap_type: CoverageGapType
    impact_score: float
    suggestion: str
    priority: int


@dataclass
class TestSuggestion:
    target_file: str
    target_element: str
    suggested_test_name: str
    test_type: str
    priority: int
    template: str
    reasoning: str


@dataclass
class BoundaryTestCase:
    parameter_name: str
    boundary_type: str
    test_value: Any
    expected_behavior: str
    description: str


@dataclass
class ParametrizedTestCase:
    test_name: str
    parameters: List[str]
    test_data: List[Tuple]
    expected_results: List[Any]
    description: str


@dataclass
class MockConfiguration:
    target_module: str
    target_class: str
    method_name: str
    return_value: Any
    side_effect: Optional[Any] = None
    auto_spec: bool = True


@dataclass
class PerformanceTestCase:
    test_name: str
    max_duration_ms: float
    iterations: int
    warmup_iterations: int = 3
    memory_limit_mb: Optional[float] = None


@dataclass
class ExceptionTestCase:
    test_name: str
    exception_type: type
    exception_message_pattern: str
    trigger_conditions: List[str]


@dataclass
class BranchCoverage:
    file_path: str
    line_number: int
    branch_type: str
    is_covered: bool
    test_cases: List[str]


@dataclass
class CoverageTrend:
    date: str
    line_coverage: float
    branch_coverage: float
    function_coverage: float
    total_lines: int
    covered_lines: int


@dataclass
class TestMaintainabilityScore:
    test_file: str
    score: float
    factors: Dict[str, float]
    issues: List[str]
    recommendations: List[str]


@dataclass
class DependencyNode:
    name: str
    dependencies: List[str]
    dependents: List[str]
    test_priority: int
    is_tested: bool


@dataclass
class FailureDiagnosis:
    test_name: str
    category: FailureCategory
    root_cause: str
    fix_suggestion: str
    related_code: List[str]
    confidence: float


@dataclass
class UnitTestConfig:
    source_dirs: List[str] = field(default_factory=lambda: ["backend/app"])
    test_dirs: List[str] = field(default_factory=lambda: ["backend/tests"])
    coverage_threshold: float = 80.0
    complexity_threshold: int = 10
    output_dir: str = None
    output_formats: List[str] = field(default_factory=lambda: ["json", "html"])
    exclude_patterns: List[str] = field(default_factory=lambda: ["__pycache__", ".venv", "venv", "node_modules"])
    priority_decorators: List[str] = field(default_factory=lambda: ["api_route", "router", "get", "post", "put", "delete"])
    fail_on_coverage_gap: bool = False
    generate_missing_tests: bool = True
    diagnose_failures: bool = True
    
    def __post_init__(self):
        if self.output_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                self.output_dir = str(_path_mgr.get_output_path(OutputType.REPORT, subdirectory="unit"))
            except Exception:
                self.output_dir = "docs/reports"


class ConfigLoader:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def load(self, config_path: Optional[str] = None) -> UnitTestConfig:
        config = UnitTestConfig()
        
        if config_path:
            full_path = Path(self.base_path) / config_path
            if full_path.exists():
                try:
                    if full_path.suffix in [".yaml", ".yml"] and HAS_YAML:
                        with open(full_path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                    elif full_path.suffix == ".json":
                        with open(full_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                    else:
                        return config
                    
                    if data:
                        for key, value in data.items():
                            if hasattr(config, key):
                                setattr(config, key, value)
                except Exception as e:
                    print(f"加载配置文件失败: {e}")
        
        return config

    def save_template(self, output_path: str):
        template = {
            "source_dirs": ["backend/app", "src"],
            "test_dirs": ["backend/tests", "tests"],
            "coverage_threshold": 80.0,
            "complexity_threshold": 10,
            "output_dir": "docs/reports",
            "output_formats": ["json", "html"],
            "exclude_patterns": ["__pycache__", ".venv", "venv", "node_modules", "migrations"],
            "priority_decorators": ["api_route", "router", "get", "post", "put", "delete"],
            "fail_on_coverage_gap": False,
            "generate_missing_tests": True,
            "diagnose_failures": True
        }
        
        full_path = Path(self.base_path) / output_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            if HAS_YAML:
                yaml.dump(template, f, default_flow_style=False, allow_unicode=True)
            else:
                json.dump(template, f, indent=2, ensure_ascii=False)


class FailureDiagnostician:
    def __init__(self):
        self.diagnosis_patterns = {
            FailureCategory.ASSERTION_ERROR: [
                (r"AssertionError: assert (.+)", "断言失败"),
                (r"assert (.+) == (.+)", "值不相等"),
                (r"assert (.+) != (.+)", "值不应相等但相等了"),
            ],
            FailureCategory.IMPORT_ERROR: [
                (r"ImportError: (.+)", "导入错误"),
                (r"ModuleNotFoundError: (.+)", "模块未找到"),
            ],
            FailureCategory.ATTRIBUTE_ERROR: [
                (r"AttributeError: '(\w+)' object has no attribute '(\w+)'", "属性不存在"),
            ],
            FailureCategory.TYPE_ERROR: [
                (r"TypeError: (.+)", "类型错误"),
            ],
            FailureCategory.VALUE_ERROR: [
                (r"ValueError: (.+)", "值错误"),
            ],
            FailureCategory.TIMEOUT_ERROR: [
                (r"TimeoutError", "执行超时"),
                (r"timed out after", "操作超时"),
            ],
            FailureCategory.FIXTURE_ERROR: [
                (r"fixture '(\w+)' not found", "测试夹具未找到"),
                (r"ScopeMismatch", "夹具作用域不匹配"),
            ],
        }

    def diagnose(self, test_name: str, error_message: str, traceback_str: str = "") -> FailureDiagnosis:
        category = self._categorize_error(error_message)
        root_cause = self._analyze_root_cause(error_message, traceback_str)
        fix_suggestion = self._generate_fix_suggestion(category, root_cause, error_message)
        related_code = self._extract_related_code(traceback_str)
        confidence = self._calculate_confidence(category, error_message)
        
        return FailureDiagnosis(
            test_name=test_name,
            category=category,
            root_cause=root_cause,
            fix_suggestion=fix_suggestion,
            related_code=related_code,
            confidence=confidence
        )

    def _categorize_error(self, error_message: str) -> FailureCategory:
        for category, patterns in self.diagnosis_patterns.items():
            for pattern, _ in patterns:
                if re.search(pattern, error_message, re.IGNORECASE):
                    return category
        return FailureCategory.UNKNOWN

    def _analyze_root_cause(self, error_message: str, traceback_str: str) -> str:
        if "AssertionError" in error_message:
            match = re.search(r"assert (.+)", error_message)
            if match:
                return f"断言条件不满足: {match.group(1)[:100]}"
            return "断言失败，期望值与实际值不匹配"
        
        if "ImportError" in error_message or "ModuleNotFoundError" in error_message:
            match = re.search(r"No module named '([^']+)'", error_message)
            if match:
                return f"缺少模块: {match.group(1)}"
            return "导入依赖失败"
        
        if "AttributeError" in error_message:
            match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error_message)
            if match:
                return f"对象 {match.group(1)} 没有属性 {match.group(2)}"
            return "访问了不存在的属性"
        
        return error_message[:200] if error_message else "未知错误"

    def _generate_fix_suggestion(self, category: FailureCategory, root_cause: str, error_message: str) -> str:
        suggestions = {
            FailureCategory.ASSERTION_ERROR: [
                "检查期望值是否正确",
                "验证测试数据是否符合预期",
                "确认被测函数的返回值逻辑",
                "使用更精确的断言方法",
            ],
            FailureCategory.IMPORT_ERROR: [
                "检查模块是否已安装: pip install <module>",
                "确认导入路径是否正确",
                "检查 PYTHONPATH 配置",
                "验证 __init__.py 文件是否存在",
            ],
            FailureCategory.ATTRIBUTE_ERROR: [
                "检查对象类型是否正确",
                "确认属性名称拼写无误",
                "验证对象是否正确初始化",
                "检查是否需要 mock 该属性",
            ],
            FailureCategory.TYPE_ERROR: [
                "检查参数类型是否正确",
                "确认函数签名是否匹配",
                "验证参数数量是否正确",
            ],
            FailureCategory.VALUE_ERROR: [
                "检查输入值是否在有效范围内",
                "验证数据格式是否正确",
            ],
            FailureCategory.TIMEOUT_ERROR: [
                "增加测试超时时间",
                "优化被测代码性能",
                "检查是否存在死循环",
            ],
            FailureCategory.FIXTURE_ERROR: [
                "确认 fixture 是否已定义",
                "检查 fixture 名称拼写",
                "验证 fixture 导入路径",
            ],
        }
        
        category_suggestions = suggestions.get(category, ["请检查错误详情"])
        return "; ".join(category_suggestions[:3])

    def _extract_related_code(self, traceback_str: str) -> List[str]:
        related = []
        if traceback_str:
            lines = traceback_str.split("\n")
            for line in lines:
                if "File " in line and ".py" in line:
                    related.append(line.strip())
        return related[:5]

    def _calculate_confidence(self, category: FailureCategory, error_message: str) -> float:
        if category == FailureCategory.UNKNOWN:
            return 0.3
        if len(error_message) > 50:
            return 0.9
        if len(error_message) > 20:
            return 0.7
        return 0.5


class IntelligentTestDiscovery:
    def __init__(self, base_path: str, config: UnitTestConfig):
        self.base_path = base_path
        self.config = config
        self.dependency_graph: Dict[str, DependencyNode] = {}
        self.test_priorities: Dict[str, int] = {}

    def build_dependency_graph(self, source_dirs: List[str]) -> Dict[str, DependencyNode]:
        for source_dir in source_dirs:
            source_path = Path(self.base_path) / source_dir
            if source_path.exists():
                self._analyze_dependencies(source_path)
        return self.dependency_graph

    def _analyze_dependencies(self, directory: Path):
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            self._extract_dependencies(py_file)

    def _should_skip_file(self, file_path: Path) -> bool:
        return any(pattern in str(file_path) for pattern in self.config.exclude_patterns)

    def _extract_dependencies(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            imports = []
            exports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                elif isinstance(node, ast.FunctionDef):
                    exports.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    exports.append(node.name)

            relative_path = str(file_path.relative_to(self.base_path))
            self.dependency_graph[relative_path] = DependencyNode(
                name=relative_path,
                dependencies=imports,
                dependents=[],
                test_priority=self._calculate_test_priority(exports, imports),
                is_tested=False
            )
        except Exception as e:
            print(f"分析依赖失败 {file_path}: {e}")

    def _calculate_test_priority(self, exports: List[str], imports: List[str]) -> int:
        priority = 5
        if len(exports) > 10:
            priority += 2
        if len(imports) > 5:
            priority += 1
        return min(priority, 10)

    def calculate_test_order(self) -> List[str]:
        visited = set()
        order = []

        def visit(node_name: str):
            if node_name in visited:
                return
            visited.add(node_name)
            if node_name in self.dependency_graph:
                for dep in self.dependency_graph[node_name].dependencies:
                    dep_name = next((k for k in self.dependency_graph if dep in k), None)
                    if dep_name:
                        visit(dep_name)
            order.append(node_name)

        for node_name in self.dependency_graph:
            visit(node_name)

        return sorted(order, key=lambda x: self.dependency_graph.get(x, DependencyNode("", [], [], 0, False)).test_priority, reverse=True)

    def suggest_tests_for_untested_dependencies(self) -> List[TestSuggestion]:
        suggestions = []
        for name, node in self.dependency_graph.items():
            if not node.is_tested and node.test_priority >= 7:
                suggestions.append(TestSuggestion(
                    target_file=name,
                    target_element="module",
                    suggested_test_name=f"test_{Path(name).stem}",
                    test_type="unit",
                    priority=node.test_priority,
                    template=self._generate_module_test_template(name),
                    reasoning=f"高优先级模块({node.test_priority})未被测试，有{len(node.dependents)}个依赖项"
                ))
        return suggestions

    def _generate_module_test_template(self, module_path: str) -> str:
        return f'''
def test_module_imports():
    """测试模块导入"""
    try:
        import {Path(module_path).stem}
        assert True
    except ImportError as e:
        assert False, f"模块导入失败: {{e}}"

def test_module_functions():
    """测试模块函数"""
    pass
'''


class AdvancedTestGenerator:
    """
    高级测试生成器
    
    支持多种测试模式:
    - 参数化测试: 使用pytest.mark.parametrize生成多组测试数据
    - Mock测试: 自动识别需要mock的依赖并生成mock配置
    - 异步测试: 为async函数生成异步测试用例
    - 异常测试: 自动生成异常场景测试
    - 性能测试: 生成性能基准测试
    - 属性测试: 生成基于属性的测试
    """
    
    def __init__(self, base_path: str, config: UnitTestConfig):
        self.base_path = base_path
        self.config = config
        self.generated_patterns: Dict[str, List[TestPattern]] = {}
    
    def generate_parametrized_test(
        self, 
        element: CodeElement,
        test_data: Optional[List[Tuple]] = None
    ) -> ParametrizedTestCase:
        """
        生成参数化测试用例
        
        参数:
            element: 代码元素
            test_data: 自定义测试数据，如果为None则自动生成
        
        返回:
            ParametrizedTestCase对象
        """
        if test_data is None:
            test_data = self._generate_parametrized_data(element)
        
        param_names = element.parameters if element.parameters else ["input"]
        expected_results = [None] * len(test_data)
        
        return ParametrizedTestCase(
            test_name=f"test_{element.name}_parametrized",
            parameters=param_names,
            test_data=test_data,
            expected_results=expected_results,
            description=f"参数化测试 {element.name}，覆盖多种输入组合"
        )
    
    def _generate_parametrized_data(self, element: CodeElement) -> List[Tuple]:
        """根据参数类型自动生成参数化测试数据"""
        test_data = []
        
        if not element.parameters:
            return [()]
        
        param_combinations = []
        for param in element.parameters:
            param_type = self._infer_param_type(param)
            values = self._get_type_test_values(param_type)
            param_combinations.append(values)
        
        import itertools
        for combo in itertools.product(*param_combinations):
            test_data.append(combo)
            if len(test_data) >= 10:
                break
        
        return test_data
    
    def _infer_param_type(self, param_name: str) -> str:
        """推断参数类型"""
        type_hints = {
            "id": "int", "count": "int", "size": "int", "index": "int",
            "name": "str", "title": "str", "description": "str", "text": "str",
            "email": "str", "url": "str", "phone": "str",
            "price": "float", "amount": "float", "rate": "float",
            "enabled": "bool", "active": "bool", "visible": "bool",
            "items": "list", "data": "dict", "options": "dict",
            "user": "object", "model": "object",
        }
        param_lower = param_name.lower()
        for key, type_name in type_hints.items():
            if key in param_lower:
                return type_name
        return "str"
    
    def _get_type_test_values(self, param_type: str) -> List[Any]:
        """获取类型对应的测试值"""
        type_values = {
            "int": [0, 1, -1, 100, -100],
            "float": [0.0, 1.5, -1.5, 100.0],
            "str": ["", "test", "测试", "a" * 100],
            "bool": [True, False],
            "list": [[], [1], [1, 2, 3]],
            "dict": [{}, {"key": "value"}],
            "object": [None, Mock()],
        }
        return type_values.get(param_type, [None])
    
    def generate_mock_test(
        self, 
        element: CodeElement,
        dependencies: List[str]
    ) -> Tuple[str, List[MockConfiguration]]:
        """
        生成Mock测试配置
        
        参数:
            element: 代码元素
            dependencies: 依赖列表
        
        返回:
            (测试代码, Mock配置列表)
        """
        mock_configs = []
        
        for dep in dependencies:
            config = MockConfiguration(
                target_module=dep,
                target_class="",
                method_name="",
                return_value=Mock(),
                auto_spec=True
            )
            mock_configs.append(config)
        
        test_code = self._generate_mock_test_code(element, mock_configs)
        return test_code, mock_configs
    
    def _generate_mock_test_code(
        self, 
        element: CodeElement,
        mock_configs: List[MockConfiguration]
    ) -> str:
        """生成Mock测试代码"""
        decorators = []
        for config in mock_configs:
            decorators.append(f'@patch("{config.target_module}")')
        
        decorator_str = "\n".join(decorators)
        mock_params = ", ".join([f"mock_{i}" for i in range(len(mock_configs))])
        
        return f'''
{decorator_str}
def test_{element.name}_with_mocks({mock_params}):
    """测试 {element.name} 使用Mock依赖
    
    自动生成的Mock测试，隔离外部依赖
    """
    # Arrange - 配置Mock行为
    # mock_0.return_value = expected_value
    
    # Act - 执行测试
    # result = {element.name}()
    
    # Assert - 验证结果
    # assert result == expected
    # mock_0.assert_called_once()
    pass
'''
    
    def generate_async_test(self, element: CodeElement) -> str:
        """
        生成异步测试用例
        
        参数:
            element: 代码元素
        
        返回:
            异步测试代码
        """
        params_str = ", ".join([f"{p}=None" for p in element.parameters]) if element.parameters else ""
        
        return f'''
@pytest.mark.asyncio
async def test_{element.name}_async():
    """测试异步函数 {element.name}
    
    使用pytest-asyncio进行异步测试
    """
    # Arrange - 准备异步测试数据
    
    # Act - 执行异步操作
    # result = await {element.name}({params_str})
    
    # Assert - 验证异步结果
    # assert result is not None
    pass
'''
    
    def generate_exception_test(
        self, 
        element: CodeElement,
        exception_cases: Optional[List[ExceptionTestCase]] = None
    ) -> str:
        """
        生成异常测试用例
        
        参数:
            element: 代码元素
            exception_cases: 异常测试用例列表
        
        返回:
            异常测试代码
        """
        if exception_cases is None:
            exception_cases = self._infer_exception_cases(element)
        
        test_code = f'''
class Test{element.name.capitalize()}Exceptions:
    """测试 {element.name} 的异常处理"""
'''
        
        for case in exception_cases:
            test_code += f'''
    def test_{element.name}_{case.test_name}(self):
        """测试异常场景: {case.trigger_conditions}"""
        with pytest.raises({case.exception_type.__name__}) as exc_info:
            # 触发异常的条件
            # {element.name}(invalid_input)
            pass
        # assert str(exc_info.value) matches "{case.exception_message_pattern}"
'''
        
        return test_code
    
    def _infer_exception_cases(self, element: CodeElement) -> List[ExceptionTestCase]:
        """推断可能的异常场景"""
        cases = []
        
        if element.parameters:
            cases.append(ExceptionTestCase(
                test_name="invalid_type",
                exception_type=TypeError,
                exception_message_pattern=".*type.*",
                trigger_conditions=["传入错误类型的参数"]
            ))
            
            cases.append(ExceptionTestCase(
                test_name="invalid_value",
                exception_type=ValueError,
                exception_message_pattern=".*value.*",
                trigger_conditions=["传入无效值"]
            ))
        
        cases.append(ExceptionTestCase(
            test_name="none_input",
            exception_type=(ValueError, TypeError),
            exception_message_pattern=".*None.*",
            trigger_conditions=["传入None值"]
        ))
        
        return cases
    
    def generate_performance_test(
        self, 
        element: CodeElement,
        max_duration_ms: float = 100.0
    ) -> PerformanceTestCase:
        """
        生成性能测试配置
        
        参数:
            element: 代码元素
            max_duration_ms: 最大执行时间(毫秒)
        
        返回:
            PerformanceTestCase对象
        """
        return PerformanceTestCase(
            test_name=f"test_{element.name}_performance",
            max_duration_ms=max_duration_ms,
            iterations=100,
            warmup_iterations=10,
            memory_limit_mb=50.0
        )
    
    def generate_performance_test_code(
        self, 
        element: CodeElement,
        perf_case: PerformanceTestCase
    ) -> str:
        """生成性能测试代码"""
        return f'''
import time
import statistics

def {perf_case.test_name}():
    """性能测试 {element.name}
    
    最大执行时间: {perf_case.max_duration_ms}ms
    迭代次数: {perf_case.iterations}
    """
    durations = []
    
    # 预热
    for _ in range({perf_case.warmup_iterations}):
        # {element.name}()
        pass
    
    # 正式测试
    for _ in range({perf_case.iterations}):
        start = time.perf_counter()
        # result = {element.name}()
        end = time.perf_counter()
        durations.append((end - start) * 1000)
    
    avg_duration = statistics.mean(durations)
    max_duration = max(durations)
    min_duration = min(durations)
    
    print(f"平均执行时间: {{avg_duration:.2f}}ms")
    print(f"最大执行时间: {{max_duration:.2f}}ms")
    print(f"最小执行时间: {{min_duration:.2f}}ms")
    
    assert avg_duration < {perf_case.max_duration_ms}, \\
        f"性能测试失败: 平均执行时间{{avg_duration:.2f}}ms超过阈值{perf_case.max_duration_ms}ms"
'''
    
    def generate_property_test(self, element: CodeElement) -> str:
        """
        生成基于属性的测试
        
        参数:
            element: 代码元素
        
        返回:
            属性测试代码
        """
        return f'''
from hypothesis import given, strategies as st

class Test{element.name.capitalize()}Properties:
    """基于属性的测试 {element.name}"""
    
    @given(st.integers())
    def test_{element.name}_with_any_integer(self, value):
        """测试任意整数输入"""
        # result = {element.name}(value)
        # 验证属性: 结果应该满足某些不变量
        pass
    
    @given(st.text())
    def test_{element.name}_with_any_text(self, text):
        """测试任意文本输入"""
        # result = {element.name}(text)
        pass
    
    @given(st.lists(st.integers()))
    def test_{element.name}_with_any_list(self, items):
        """测试任意列表输入"""
        # result = {element.name}(items)
        pass
'''
    
    def generate_comprehensive_test(
        self, 
        element: CodeElement,
        patterns: Optional[List[TestPattern]] = None
    ) -> Dict[str, str]:
        """
        生成综合测试套件
        
        参数:
            element: 代码元素
            patterns: 要生成的测试模式列表
        
        返回:
            测试代码字典 {模式名: 代码}
        """
        if patterns is None:
            patterns = [
                TestPattern.PARAMETRIZED,
                TestPattern.MOCK,
                TestPattern.EXCEPTION,
                TestPattern.PERFORMANCE
            ]
        
        tests = {}
        
        for pattern in patterns:
            if pattern == TestPattern.PARAMETRIZED:
                param_case = self.generate_parametrized_test(element)
                tests["parametrized"] = self._parametrized_test_to_code(element, param_case)
            elif pattern == TestPattern.MOCK:
                test_code, _ = self.generate_mock_test(element, [])
                tests["mock"] = test_code
            elif pattern == TestPattern.ASYNC:
                tests["async"] = self.generate_async_test(element)
            elif pattern == TestPattern.EXCEPTION:
                tests["exception"] = self.generate_exception_test(element)
            elif pattern == TestPattern.PERFORMANCE:
                perf_case = self.generate_performance_test(element)
                tests["performance"] = self.generate_performance_test_code(element, perf_case)
            elif pattern == TestPattern.PROPERTY_BASED:
                tests["property"] = self.generate_property_test(element)
        
        self.generated_patterns[element.name] = patterns
        return tests
    
    def _parametrized_test_to_code(
        self, 
        element: CodeElement,
        param_case: ParametrizedTestCase
    ) -> str:
        """将参数化测试转换为代码"""
        params_str = ", ".join(param_case.parameters)
        test_data_str = "[\n"
        for data in param_case.test_data:
            test_data_str += f"    {data},\n"
        test_data_str += "]"
        
        return f'''
@pytest.mark.parametrize("{params_str}", {test_data_str})
def {param_case.test_name}({params_str}):
    """{param_case.description}"""
    # result = {element.name}({params_str})
    # assert result is not None
    pass
'''


class BoundaryTestAnalyzer:
    BOUNDARY_VALUES = {
        "int": [0, 1, -1, 2**31 - 1, -2**31, 2**63 - 1, -2**63],
        "float": [0.0, 1.0, -1.0, float('inf'), float('-inf'), float('nan'), 1e-10, 1e10],
        "str": ["", "a", " " * 1000, "特殊字符!@#$%", "unicode中文", None],
        "list": [[], [1], [None], list(range(1000))],
        "dict": [{}, {"key": "value"}, {"nested": {"deep": "value"}}],
        "bool": [True, False],
        "datetime": ["1970-01-01", "2099-12-31", None],
    }

    BOUNDARY_PATTERNS = {
        "email": ["", "a@b.c", "valid@email.com", "invalid-email", None, "a" * 100 + "@test.com"],
        "url": ["", "http://valid.com", "invalid-url", None, "http://" + "a" * 2000 + ".com"],
        "phone": ["", "123", "+86-13800138000", "invalid-phone", None],
        "password": ["", "a", "a" * 1000, "ValidPass123!", None, "中文密码"],
        "username": ["", "a", "valid_user", "user@name", None, "a" * 100],
        "id": [0, 1, -1, 2**63 - 1, None],
        "age": [0, 1, -1, 150, -150, None],
        "percentage": [0, 100, -1, 101, 50.5, None],
        "quantity": [0, 1, -1, 2**31 - 1, None],
    }

    def __init__(self):
        self.boundary_cases: List[BoundaryTestCase] = []
        self.detected_patterns: Dict[str, List[str]] = {}

    def analyze_function_boundaries(self, element: CodeElement) -> List[BoundaryTestCase]:
        cases = []
        self.detected_patterns = {}

        for param in element.parameters:
            param_lower = param.lower()
            param_type = self._infer_parameter_type(param)
            
            if self._is_special_param(param_lower):
                special_cases = self._generate_special_boundary_cases(param, param_lower)
                cases.extend(special_cases)
                self.detected_patterns[param] = param_lower
            else:
                boundary_values = self.BOUNDARY_VALUES.get(param_type, [None])
                for value in boundary_values[:5]:
                    cases.append(BoundaryTestCase(
                        parameter_name=param,
                        boundary_type=self._get_boundary_type(value),
                        test_value=value,
                        expected_behavior="should_handle_gracefully",
                        description=f"测试参数 {param} 的边界值 {self._format_value(value)}"
                    ))

        complexity_cases = self._analyze_complexity_boundaries(element)
        cases.extend(complexity_cases)

        return cases

    def _is_special_param(self, param_lower: str) -> bool:
        special_patterns = ["email", "url", "phone", "password", "username", "id", "age", "percentage", "quantity"]
        return any(pattern in param_lower for pattern in special_patterns)

    def _generate_special_boundary_cases(self, param: str, param_lower: str) -> List[BoundaryTestCase]:
        cases = []
        
        for pattern_name, values in self.BOUNDARY_PATTERNS.items():
            if pattern_name in param_lower:
                for value in values:
                    cases.append(BoundaryTestCase(
                        parameter_name=param,
                        boundary_type=f"{pattern_name}_boundary",
                        test_value=value,
                        expected_behavior=self._get_expected_behavior_for_pattern(pattern_name, value),
                        description=f"测试 {param} ({pattern_name}) 的边界值: {self._format_value(value)}"
                    ))
                break
        
        return cases

    def _get_expected_behavior_for_pattern(self, pattern: str, value: Any) -> str:
        if value is None or value == "":
            return "should_validate_or_reject"
        
        valid_patterns = {
            "email": "@" in str(value) and "." in str(value),
            "url": str(value).startswith("http"),
            "phone": len(str(value)) >= 3,
            "password": len(str(value)) >= 8 if value else False,
            "username": len(str(value)) >= 1 if value else False,
            "id": isinstance(value, int) and value > 0 if value is not None else False,
            "age": isinstance(value, int) and 0 <= value <= 150 if value is not None else False,
            "percentage": isinstance(value, (int, float)) and 0 <= value <= 100 if value is not None else False,
            "quantity": isinstance(value, int) and value >= 0 if value is not None else False,
        }
        
        return "should_accept" if valid_patterns.get(pattern, False) else "should_validate_or_reject"

    def _analyze_complexity_boundaries(self, element: CodeElement) -> List[BoundaryTestCase]:
        cases = []
        
        if element.complexity > 10:
            cases.append(BoundaryTestCase(
                parameter_name="__complexity__",
                boundary_type="high_complexity",
                test_value=element.complexity,
                expected_behavior="should_have_comprehensive_tests",
                description=f"函数复杂度为 {element.complexity}，建议添加更多测试覆盖分支"
            ))
        
        if len(element.parameters) > 5:
            cases.append(BoundaryTestCase(
                parameter_name="__param_count__",
                boundary_type="many_parameters",
                test_value=len(element.parameters),
                expected_behavior="should_test_all_combinations",
                description=f"参数数量为 {len(element.parameters)}，建议测试参数组合"
            ))
        
        return cases

    def _infer_parameter_type(self, param_name: str) -> str:
        type_hints = {
            "id": "int",
            "name": "str",
            "count": "int",
            "size": "int",
            "index": "int",
            "value": "float",
            "data": "dict",
            "items": "list",
            "text": "str",
            "url": "str",
            "email": "str",
            "enabled": "bool",
            "active": "bool",
            "created": "datetime",
            "updated": "datetime",
            "timestamp": "datetime",
        }
        return type_hints.get(param_name.lower(), "str")

    def _get_boundary_type(self, value: Any) -> str:
        if value is None:
            return "null"
        elif value == 0 or value == 0.0:
            return "zero"
        elif value == "":
            return "empty"
        elif isinstance(value, (int, float)) and value < 0:
            return "negative"
        elif isinstance(value, (int, float)) and value > 1000000:
            return "large"
        elif isinstance(value, str) and len(value) > 100:
            return "long_string"
        elif isinstance(value, float) and (value == float('inf') or value != value):
            return "special_float"
        return "normal"

    def _format_value(self, value: Any) -> str:
        if value is None:
            return "None"
        elif isinstance(value, str) and len(value) > 50:
            return f"{value[:50]}... (长度: {len(value)})"
        elif isinstance(value, float) and value != value:
            return "NaN"
        elif isinstance(value, float) and value == float('inf'):
            return "Infinity"
        elif isinstance(value, float) and value == float('-inf'):
            return "-Infinity"
        return repr(value)

    def generate_boundary_test_code(self, element: CodeElement, cases: List[BoundaryTestCase]) -> str:
        test_code = f'''
def test_{element.name}_boundary_conditions():
    """测试 {element.name} 的边界条件
    
    自动生成的边界条件测试，覆盖以下场景:
    - 空值/None值处理
    - 边界值处理
    - 特殊字符处理
    - 类型边界处理
    """
    test_results = []
'''
        for case in cases[:15]:
            if case.parameter_name.startswith("__"):
                test_code += f'''
    # {case.description}
    # 建议: {case.expected_behavior}
'''
            else:
                test_code += f'''
    # {case.description}
    try:
        result = {element.name}({case.parameter_name}={repr(case.test_value)})
        test_results.append({{"case": "{case.boundary_type}", "passed": True, "result": str(result)[:100]}})
    except (ValueError, TypeError) as e:
        test_results.append({{"case": "{case.boundary_type}", "passed": True, "handled": str(e)[:50]}})
    except Exception as e:
        test_results.append({{"case": "{case.boundary_type}", "passed": False, "error": str(e)[:50]}})
'''
        test_code += f'''
    failed_cases = [r for r in test_results if not r["passed"]]
    assert len(failed_cases) == 0, f"边界条件测试失败: {{failed_cases}}"
'''
        return test_code

    def get_boundary_summary(self, cases: List[BoundaryTestCase]) -> Dict[str, Any]:
        summary = {
            "total_cases": len(cases),
            "by_type": defaultdict(int),
            "by_parameter": defaultdict(int),
            "special_patterns": list(self.detected_patterns.keys()),
            "recommendations": []
        }
        
        for case in cases:
            summary["by_type"][case.boundary_type] += 1
            summary["by_parameter"][case.parameter_name] += 1
        
        if len(summary["by_parameter"]) > 5:
            summary["recommendations"].append("参数较多，建议使用参数化测试")
        
        if "null" in summary["by_type"] or "empty" in summary["by_type"]:
            summary["recommendations"].append("存在空值边界测试，确保异常处理完善")
        
        return dict(summary)


class TestGenerator:
    def __init__(self, base_path: str, config: UnitTestConfig):
        self.base_path = base_path
        self.config = config
        self.boundary_analyzer = BoundaryTestAnalyzer()
        self.generated_tests: Dict[str, str] = {}

    def generate_test_file(self, source_file: str, elements: List[CodeElement]) -> str:
        test_file_name = f"test_{Path(source_file).stem}.py"
        test_code = self._generate_file_header(source_file)
        
        for element in elements:
            if element.type == "function":
                test_code += self._generate_function_tests(element)
            elif element.type == "class":
                test_code += self._generate_class_tests(element)
        
        self.generated_tests[test_file_name] = test_code
        return test_code

    def _generate_file_header(self, source_file: str) -> str:
        return f'''"""
自动生成的单元测试文件
源文件: {source_file}
生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

注意: 此文件由测试增强框架自动生成，请根据实际需求调整测试用例
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(get_path_config().SKILL_ROOT))


'''

    def _generate_function_tests(self, element: CodeElement) -> str:
        test_code = f'''
class Test{element.name.capitalize()}:
    """测试 {element.name} 函数"""
    
'''
        test_code += self._generate_basic_test(element)
        test_code += self._generate_success_case_test(element)
        test_code += self._generate_error_case_test(element)
        test_code += self._generate_boundary_tests(element)
        
        return test_code

    def _generate_basic_test(self, element: CodeElement) -> str:
        params = ", ".join(element.parameters) if element.parameters else ""
        return f'''
    def test_{element.name}_exists(self):
        """测试函数是否存在且可调用"""
        try:
            from {Path(element.file_path).stem.replace('/', '.')} import {element.name}
            assert callable({element.name}), "{element.name} 应该是可调用的函数"
        except ImportError:
            pytest.skip("模块导入失败，请检查依赖")

    def test_{element.name}_signature(self):
        """测试函数签名"""
        try:
            from {Path(element.file_path).stem.replace('/', '.')} import {element.name}
            import inspect
            sig = inspect.signature({element.name})
            params = list(sig.parameters.keys())
            expected_params = {element.parameters}
            assert set(params) == set(expected_params), f"参数不匹配: 期望 {{expected_params}}, 实际 {{params}}"
        except ImportError:
            pytest.skip("模块导入失败")

'''

    def _generate_success_case_test(self, element: CodeElement) -> str:
        params_str = ", ".join([f"{p}=None" for p in element.parameters]) if element.parameters else ""
        return f'''
    def test_{element.name}_success_case(self):
        """测试正常执行场景"""
        try:
            from {Path(element.file_path).stem.replace('/', '.')} import {element.name}
            result = {element.name}({params_str})
            assert result is not None or True, "函数应返回有效结果"
        except Exception as e:
            pytest.fail(f"正常场景执行失败: {{e}}")

'''

    def _generate_error_case_test(self, element: CodeElement) -> str:
        return f'''
    def test_{element.name}_invalid_input(self):
        """测试无效输入处理"""
        try:
            from {Path(element.file_path).stem.replace('/', '.')} import {element.name}
            with pytest.raises((ValueError, TypeError, AttributeError)):
                {element.name}(None)
        except Exception:
            pass

    def test_{element.name}_edge_cases(self):
        """测试边界情况"""
        try:
            from {Path(element.file_path).stem.replace('/', '.')} import {element.name}
            result = {element.name}()
            assert result is not None or True
        except TypeError:
            pass

'''

    def _generate_boundary_tests(self, element: CodeElement) -> str:
        boundary_cases = self.boundary_analyzer.analyze_function_boundaries(element)
        return self.boundary_analyzer.generate_boundary_test_code(element, boundary_cases)

    def _generate_class_tests(self, element: CodeElement) -> str:
        return f'''
class Test{element.name.capitalize()}:
    """测试 {element.name} 类"""
    
    def test_class_instantiation(self):
        """测试类实例化"""
        try:
            from {Path(element.file_path).stem.replace('/', '.')} import {element.name}
            instance = {element.name}()
            assert instance is not None, "类应能正常实例化"
        except Exception as e:
            pytest.fail(f"实例化失败: {{e}}")
    
    def test_class_attributes(self):
        """测试类属性"""
        try:
            from {Path(element.file_path).stem.replace('/', '.')} import {element.name}
            instance = {element.name}()
            assert hasattr(instance, '__dict__'), "实例应有属性字典"
        except Exception:
            pass

'''

    def save_test_file(self, test_file_name: str, output_dir: str) -> str:
        if test_file_name not in self.generated_tests:
            return ""
        
        output_path = Path(self.base_path) / output_dir / test_file_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.generated_tests[test_file_name])
        
        return str(output_path)


class TestOptimizationSuggester:
    def __init__(self):
        self.optimization_rules = self._load_optimization_rules()

    def _load_optimization_rules(self) -> List[Dict]:
        return [
            {
                "name": "duplicate_assertion",
                "pattern": r"assert\s+\w+\s*==\s*\w+.*\n.*assert\s+\1\s*==\s*\2",
                "suggestion": "发现重复断言，建议合并或使用参数化测试",
                "severity": "low"
            },
            {
                "name": "missing_fixture",
                "pattern": r"def\s+test_\w+\([^)]*\):[^)]*setup\(",
                "suggestion": "建议使用pytest fixture替代手动setup",
                "severity": "medium"
            },
            {
                "name": "hardcoded_values",
                "pattern": r"assert\s+\w+\s*==\s*\d{4,}",
                "suggestion": "发现硬编码值，建议使用常量或配置",
                "severity": "low"
            },
            {
                "name": "sleep_in_test",
                "pattern": r"time\.sleep\(",
                "suggestion": "测试中使用sleep，建议使用mock或等待条件",
                "severity": "high"
            },
            {
                "name": "broad_exception",
                "pattern": r"except\s*:",
                "suggestion": "使用宽泛的异常捕获，建议捕获具体异常类型",
                "severity": "medium"
            },
            {
                "name": "missing_docstring",
                "pattern": r"def\s+test_\w+\([^)]*\):\s*\n\s+\w",
                "suggestion": "测试函数缺少文档字符串，建议添加测试说明",
                "severity": "low"
            },
            {
                "name": "complex_test",
                "pattern": r"def\s+test_\w+.*:\s*(\n.*\S){{20,}}",
                "suggestion": "测试函数过长，建议拆分为多个测试",
                "severity": "medium"
            }
        ]

    def analyze_test_file(self, file_path: str) -> List[Dict]:
        suggestions = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            for rule in self.optimization_rules:
                matches = list(re.finditer(rule["pattern"], content, re.MULTILINE))
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    suggestions.append({
                        "rule": rule["name"],
                        "line": line_num,
                        "severity": rule["severity"],
                        "suggestion": rule["suggestion"],
                        "code_snippet": match.group()[:100]
                    })
        
        except Exception as e:
            suggestions.append({
                "rule": "file_error",
                "line": 0,
                "severity": "high",
                "suggestion": f"无法分析文件: {str(e)}",
                "code_snippet": ""
            })
        
        return suggestions

    def suggest_improvements(self, test_results: List[Any]) -> List[Dict]:
        improvements = []
        
        slow_tests = [t for t in test_results if hasattr(t, 'duration') and t.duration > 1.0]
        if slow_tests:
            improvements.append({
                "type": "performance",
                "priority": "high",
                "suggestion": f"发现 {len(slow_tests)} 个耗时超过1秒的测试，建议优化或标记为慢测试",
                "details": [{"name": t.test_name if hasattr(t, 'test_name') else str(t), "duration": t.duration} for t in slow_tests[:5]]
            })
        
        failed_tests = [t for t in test_results if hasattr(t, 'status') and str(t.status) == "failed"]
        if failed_tests:
            improvements.append({
                "type": "reliability",
                "priority": "high",
                "suggestion": f"发现 {len(failed_tests)} 个失败测试，建议优先修复",
                "details": [{"name": t.test_name if hasattr(t, 'test_name') else str(t)} for t in failed_tests[:5]]
            })
        
        return improvements

    def generate_optimization_report(self, suggestions: List[Dict]) -> str:
        report = "# 测试优化建议报告\n\n"
        report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        by_severity = defaultdict(list)
        for s in suggestions:
            by_severity[s["severity"]].append(s)
        
        for severity in ["high", "medium", "low"]:
            if by_severity[severity]:
                report += f"## {severity.upper()} 优先级 ({len(by_severity[severity])} 条)\n\n"
                for s in by_severity[severity]:
                    report += f"- **{s['rule']}** (行 {s['line']}): {s['suggestion']}\n"
                    if s['code_snippet']:
                        report += f"  ```\n  {s['code_snippet']}\n  ```\n"
                report += "\n"
        
        return report


class MutationTestAnalyzer:
    MUTATION_OPERATORS = [
        "arithmetic_operator",
        "comparison_operator",
        "logical_operator",
        "conditional_operator",
        "return_value",
        "variable_assignment",
    ]

    def __init__(self):
        self.mutation_scores: Dict[str, float] = {}

    def estimate_mutation_score(self, element: CodeElement, test_count: int) -> float:
        base_score = 50.0

        if element.complexity > 10:
            base_score -= 10
        elif element.complexity > 5:
            base_score -= 5

        base_score += min(test_count * 5, 30)

        if element.docstring and "test" in element.docstring.lower():
            base_score += 5

        return min(max(base_score, 0), 100)

    def suggest_mutation_tests(self, element: CodeElement) -> List[str]:
        suggestions = []

        if element.complexity > 5:
            suggestions.append(f"建议为复杂函数 {element.name} 添加突变测试验证测试质量")

        for op in self.MUTATION_OPERATORS:
            suggestions.append(f"验证 {element.name} 对 {op} 突变的检测能力")

        return suggestions


class CodeAnalyzer:
    def __init__(self, base_path: str, config: UnitTestConfig):
        self.base_path = base_path
        self.config = config
        self.elements: Dict[str, CodeElement] = {}
        self.file_elements: Dict[str, List[CodeElement]] = defaultdict(list)

    def analyze_project(self, source_dirs: List[str]) -> Dict[str, List[CodeElement]]:
        for source_dir in source_dirs:
            source_path = Path(self.base_path) / source_dir
            if source_path.exists():
                self._analyze_directory(source_path)

        return dict(self.file_elements)

    def _analyze_directory(self, directory: Path):
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            self._analyze_file(py_file)

    def _should_skip_file(self, file_path: Path) -> bool:
        skip_patterns = self.config.exclude_patterns + ["test_", "_test.py", "conftest.py"]
        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _analyze_file(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            relative_path = str(file_path.relative_to(self.base_path))

            for node in ast.walk(tree):
                element = self._extract_element(node, relative_path)
                if element:
                    self.elements[element.name] = element
                    self.file_elements[relative_path].append(element)

        except Exception as e:
            print(f"分析文件失败 {file_path}: {e}")

    def _extract_element(self, node: ast.AST, file_path: str) -> Optional[CodeElement]:
        if isinstance(node, ast.FunctionDef):
            return CodeElement(
                name=node.name,
                type="function",
                file_path=file_path,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                docstring=ast.get_docstring(node),
                decorators=[d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list],
                parameters=[arg.arg for arg in node.args.args],
                complexity=self._calculate_complexity(node)
            )
        elif isinstance(node, ast.ClassDef):
            return CodeElement(
                name=node.name,
                type="class",
                file_path=file_path,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                docstring=ast.get_docstring(node),
                decorators=[d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list]
            )
        return None

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity


class TestDiscovery:
    def __init__(self, base_path: str, config: UnitTestConfig):
        self.base_path = base_path
        self.config = config
        self.strategies = [
            TestDiscoveryStrategy.NAME_PATTERN,
            TestDiscoveryStrategy.DECORATOR,
            TestDiscoveryStrategy.DOCSTRING,
        ]

    def discover_tests(self, test_dirs: List[str]) -> Dict[str, List[str]]:
        discovered = defaultdict(list)

        for test_dir in test_dirs:
            test_path = Path(self.base_path) / test_dir
            if test_path.exists():
                tests = self._discover_in_directory(test_path)
                discovered[test_dir].extend(tests)

        return dict(discovered)

    def _discover_in_directory(self, directory: Path) -> List[str]:
        tests = []

        for py_file in directory.rglob("*.py"):
            if self._is_test_file(py_file):
                test_cases = self._extract_test_cases(py_file)
                tests.extend(test_cases)

        return tests

    def _is_test_file(self, file_path: Path) -> bool:
        name = file_path.name
        return name.startswith("test_") or name.endswith("_test.py")

    def _extract_test_cases(self, file_path: Path) -> List[str]:
        test_cases = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    test_cases.append(node.name)
                elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                            test_cases.append(f"{node.name}::{item.name}")

        except Exception as e:
            print(f"提取测试用例失败 {file_path}: {e}")

        return test_cases

    def suggest_tests_for_element(self, element: CodeElement) -> TestSuggestion:
        test_name = f"test_{element.name}"

        template = self._generate_test_template(element)

        return TestSuggestion(
            target_file=element.file_path,
            target_element=element.name,
            suggested_test_name=test_name,
            test_type="unit",
            priority=self._calculate_priority(element),
            template=template,
            reasoning=self._generate_reasoning(element)
        )

    def _generate_test_template(self, element: CodeElement) -> str:
        if element.type == "function":
            params = ", ".join(element.parameters)
            return f'''
def test_{element.name}():
    """测试 {element.name}"""
    # Arrange
    # TODO: 准备测试数据
    
    # Act
    # result = {element.name}({params})
    
    # Assert
    # assert result == expected
    pass
'''
        elif element.type == "class":
            return f'''
class Test{element.name.capitalize()}:
    """测试 {element.name} 类"""
    
    def test_init(self):
        """测试初始化"""
        # instance = {element.name}()
        # assert instance is not None
        pass
    
    def test_methods(self):
        """测试方法"""
        pass
'''
        return ""

    def _calculate_priority(self, element: CodeElement) -> int:
        priority = 5

        if element.complexity > self.config.complexity_threshold:
            priority += 2
        elif element.complexity > 5:
            priority += 1

        if element.docstring and "important" in element.docstring.lower():
            priority += 2

        if any(d in element.decorators for d in self.config.priority_decorators):
            priority += 1

        return min(priority, 10)

    def _generate_reasoning(self, element: CodeElement) -> str:
        reasons = []

        if element.complexity > 5:
            reasons.append(f"复杂度为{element.complexity}，需要充分测试")

        if not element.docstring:
            reasons.append("缺少文档字符串，建议添加测试文档")

        if element.type == "function" and len(element.parameters) > 3:
            reasons.append(f"参数较多({len(element.parameters)}个)，需要测试各种参数组合")

        return "; ".join(reasons) if reasons else "建议添加单元测试"


class UncoveredCodeAnalyzer:
    def __init__(self, base_path: str, config: UnitTestConfig):
        self.base_path = base_path
        self.config = config
        self.coverage_data: Dict[str, Any] = {}

    def load_coverage_report(self, report_path: str) -> bool:
        full_path = Path(self.base_path) / report_path

        if full_path.suffix == ".json":
            return self._load_json_report(full_path)
        elif full_path.suffix == ".xml":
            return self._load_xml_report(full_path)

        return False

    def _load_json_report(self, path: Path) -> bool:
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.coverage_data = json.load(f)
            return True
        except Exception as e:
            print(f"加载JSON报告失败: {e}")
            return False

    def _load_xml_report(self, path: Path) -> bool:
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(path)
            root = tree.getroot()

            for package in root.findall(".//package"):
                package_name = package.get("name", "")
                for cls in package.findall("classes/class"):
                    filename = cls.get("filename", "")
                    line_rate = float(cls.get("line-rate", 0))

                    file_path = f"{package_name}/{filename}" if package_name else filename
                    self.coverage_data[file_path] = {
                        "line_rate": line_rate,
                        "lines": []
                    }

            return True
        except Exception as e:
            print(f"加载XML报告失败: {e}")
            return False

    def analyze_gaps(self, code_elements: Dict[str, List[CodeElement]]) -> List[CoverageGap]:
        gaps = []

        for file_path, elements in code_elements.items():
            file_coverage = self._get_file_coverage(file_path)

            for element in elements:
                if not self._is_element_covered(element, file_coverage):
                    gap = CoverageGap(
                        element=element,
                        gap_type=self._determine_gap_type(element),
                        impact_score=self._calculate_impact(element, file_coverage),
                        suggestion=self._generate_suggestion(element),
                        priority=self._calculate_gap_priority(element)
                    )
                    gaps.append(gap)

        return sorted(gaps, key=lambda g: g.priority, reverse=True)

    def _get_file_coverage(self, file_path: str) -> Dict[str, Any]:
        for key in self.coverage_data:
            if file_path in key or key in file_path:
                return self.coverage_data[key]
        return {}

    def _is_element_covered(self, element: CodeElement, coverage: Dict) -> bool:
        if not coverage:
            return False

        line_rate = coverage.get("line_rate", 0)
        if line_rate >= 0.9:
            return True

        lines = coverage.get("lines", [])
        if not lines:
            return line_rate > 0.8

        covered_in_range = sum(
            1 for line in lines
            if element.line_start <= line.get("number", 0) <= element.line_end
            and line.get("covered", False)
        )

        total_in_range = element.line_end - element.line_start + 1
        return covered_in_range / max(total_in_range, 1) > 0.8

    def _determine_gap_type(self, element: CodeElement) -> CoverageGapType:
        if element.type == "function":
            if element.complexity > 5:
                return CoverageGapType.MISSING_BRANCH
            return CoverageGapType.MISSING_FUNCTION
        elif element.type == "class":
            return CoverageGapType.MISSING_CLASS
        return CoverageGapType.MISSING_LINE

    def _calculate_impact(self, element: CodeElement, coverage: Dict) -> float:
        base_score = 10.0

        if element.complexity > 10:
            base_score *= 1.5
        elif element.complexity > 5:
            base_score *= 1.2

        if coverage:
            line_rate = coverage.get("line_rate", 0)
            base_score *= (1 - line_rate)

        return round(base_score, 2)

    def _generate_suggestion(self, element: CodeElement) -> str:
        suggestions = []

        if element.type == "function":
            suggestions.append(f"为函数 {element.name} 添加单元测试")
            if element.complexity > 5:
                suggestions.append("复杂度较高，建议测试所有分支")
            if len(element.parameters) > 2:
                suggestions.append("参数较多，建议测试各种参数组合")

        elif element.type == "class":
            suggestions.append(f"为类 {element.name} 添加测试类")
            suggestions.append("测试所有公共方法")

        return "; ".join(suggestions)

    def _calculate_gap_priority(self, element: CodeElement) -> int:
        priority = 5

        if element.complexity > 10:
            priority += 3
        elif element.complexity > 5:
            priority += 2

        if any(d in element.decorators for d in self.config.priority_decorators):
            priority += 2

        if element.docstring and any(kw in element.docstring.lower() for kw in ["重要", "important", "核心", "core"]):
            priority += 1

        return min(priority, 10)


class HTMLReportGenerator:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def generate(
        self,
        code_elements: Dict[str, List[CodeElement]],
        coverage_gaps: List[CoverageGap],
        test_suggestions: List[TestSuggestion],
        failure_diagnoses: List[FailureDiagnosis],
        output_path: str
    ) -> str:
        html_content = self._generate_html(
            code_elements,
            coverage_gaps,
            test_suggestions,
            failure_diagnoses
        )

        full_output_path = Path(self.base_path) / output_path
        full_output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(full_output_path)

    def _generate_html(
        self,
        code_elements: Dict[str, List[CodeElement]],
        coverage_gaps: List[CoverageGap],
        test_suggestions: List[TestSuggestion],
        failure_diagnoses: List[FailureDiagnosis]
    ) -> str:
        total_elements = sum(len(elements) for elements in code_elements.values())
        total_files = len(code_elements)
        total_gaps = len(coverage_gaps)
        estimated_coverage = round((total_elements - total_gaps) / max(total_elements, 1) * 100, 2)

        gaps_html = self._generate_gaps_table(coverage_gaps[:20])
        suggestions_html = self._generate_suggestions_table(test_suggestions[:20])
        diagnoses_html = self._generate_diagnoses_table(failure_diagnoses[:10])

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>单元测试智能增强报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .card h3 {{ color: #333; margin-bottom: 15px; font-size: 14px; text-transform: uppercase; }}
        .card .value {{ font-size: 32px; font-weight: bold; color: #667eea; }}
        .card .label {{ color: #666; font-size: 12px; margin-top: 5px; }}
        .section {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #667eea; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #333; }}
        .priority-high {{ color: #ef4444; font-weight: bold; }}
        .priority-medium {{ color: #f59e0b; }}
        .priority-low {{ color: #10b981; }}
        .tag {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-right: 5px; }}
        .tag-function {{ background: #dbeafe; color: #1e40af; }}
        .tag-class {{ background: #fce7f3; color: #9d174d; }}
        .tag-method {{ background: #d1fae5; color: #065f46; }}
        .progress-bar {{ height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; margin-top: 10px; }}
        .progress-fill {{ height: 100%; border-radius: 4px; transition: width 0.3s; }}
        .progress-fill.high {{ background: #10b981; }}
        .progress-fill.medium {{ background: #f59e0b; }}
        .progress-fill.low {{ background: #ef4444; }}
        .status-pass {{ color: #10b981; }}
        .status-fail {{ color: #ef4444; }}
        .diagnosis {{ background: #fef3c7; padding: 10px; border-radius: 5px; margin: 5px 0; }}
        pre {{ background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 单元测试智能增强报告</h1>
            <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div class="summary">
            <div class="card">
                <h3>分析文件数</h3>
                <div class="value">{total_files}</div>
                <div class="label">源代码文件</div>
            </div>
            <div class="card">
                <h3>代码元素数</h3>
                <div class="value">{total_elements}</div>
                <div class="label">函数/类/方法</div>
            </div>
            <div class="card">
                <h3>覆盖率缺口</h3>
                <div class="value">{total_gaps}</div>
                <div class="label">未覆盖元素</div>
            </div>
            <div class="card">
                <h3>预估覆盖率</h3>
                <div class="value">{estimated_coverage}%</div>
                <div class="label">测试覆盖</div>
                <div class="progress-bar">
                    <div class="progress-fill {'high' if estimated_coverage >= 80 else 'medium' if estimated_coverage >= 60 else 'low'}" style="width: {min(estimated_coverage, 100)}%"></div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🔴 覆盖率缺口分析</h2>
            <table>
                <thead>
                    <tr>
                        <th>元素名称</th>
                        <th>类型</th>
                        <th>文件</th>
                        <th>缺口类型</th>
                        <th>优先级</th>
                        <th>建议</th>
                    </tr>
                </thead>
                <tbody>
                    {gaps_html}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>💡 测试建议</h2>
            <table>
                <thead>
                    <tr>
                        <th>目标元素</th>
                        <th>建议测试名</th>
                        <th>优先级</th>
                        <th>理由</th>
                    </tr>
                </thead>
                <tbody>
                    {suggestions_html}
                </tbody>
            </table>
        </div>
        
        {f'''<div class="section">
            <h2>🔍 失败诊断</h2>
            <table>
                <thead>
                    <tr>
                        <th>测试名称</th>
                        <th>错误类型</th>
                        <th>根本原因</th>
                        <th>修复建议</th>
                        <th>置信度</th>
                    </tr>
                </thead>
                <tbody>
                    {diagnoses_html}
                </tbody>
            </table>
        </div>''' if failure_diagnoses else ''}
    </div>
</body>
</html>'''

    def _generate_gaps_table(self, gaps: List[CoverageGap]) -> str:
        rows = ""
        for gap in gaps:
            priority_class = "priority-high" if gap.priority >= 8 else "priority-medium" if gap.priority >= 5 else "priority-low"
            tag_class = f"tag-{gap.element.type}"
            rows += f'''
            <tr>
                <td><span class="tag {tag_class}">{gap.element.type}</span> {gap.element.name}</td>
                <td>{gap.element.type}</td>
                <td title="{gap.element.file_path}">{Path(gap.element.file_path).name}</td>
                <td>{gap.gap_type.value}</td>
                <td class="{priority_class}">{gap.priority}</td>
                <td>{gap.suggestion[:100]}...</td>
            </tr>'''
        return rows

    def _generate_suggestions_table(self, suggestions: List[TestSuggestion]) -> str:
        rows = ""
        for s in suggestions:
            priority_class = "priority-high" if s.priority >= 8 else "priority-medium" if s.priority >= 5 else "priority-low"
            rows += f'''
            <tr>
                <td>{s.target_element}</td>
                <td><code>{s.suggested_test_name}</code></td>
                <td class="{priority_class}">{s.priority}</td>
                <td>{s.reasoning}</td>
            </tr>'''
        return rows

    def _generate_diagnoses_table(self, diagnoses: List[FailureDiagnosis]) -> str:
        rows = ""
        for d in diagnoses:
            rows += f'''
            <tr>
                <td>{d.test_name}</td>
                <td>{d.category.value}</td>
                <td>{d.root_cause}</td>
                <td>{d.fix_suggestion[:100]}...</td>
                <td>{d.confidence * 100:.0f}%</td>
            </tr>'''
        return rows


class EnhancedCoverageReporter:
    def __init__(self, base_path: str, config: UnitTestConfig):
        self.base_path = base_path
        self.config = config
        self.reports: Dict[str, Any] = {}
        self.html_generator = HTMLReportGenerator(base_path)

    def generate_report(
        self,
        code_elements: Dict[str, List[CodeElement]],
        coverage_gaps: List[CoverageGap],
        test_suggestions: List[TestSuggestion],
        failure_diagnoses: List[FailureDiagnosis],
        output_path: str
    ) -> Dict[str, Any]:
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "config": {
                "coverage_threshold": self.config.coverage_threshold,
                "complexity_threshold": self.config.complexity_threshold,
                "source_dirs": self.config.source_dirs,
                "test_dirs": self.config.test_dirs
            },
            "summary": self._generate_summary(code_elements, coverage_gaps),
            "coverage_analysis": self._analyze_coverage_by_file(code_elements, coverage_gaps),
            "gap_analysis": self._analyze_gaps(coverage_gaps),
            "test_suggestions": [asdict(s) for s in test_suggestions],
            "failure_diagnoses": [asdict(d) for d in failure_diagnoses],
            "recommendations": self._generate_recommendations(coverage_gaps),
            "metrics": self._calculate_metrics(code_elements, coverage_gaps)
        }

        self.reports["latest"] = report

        full_output_path = Path(self.base_path) / output_path
        full_output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        if "html" in self.config.output_formats:
            html_path = str(full_output_path).replace(".json", ".html")
            self.html_generator.generate(
                code_elements,
                coverage_gaps,
                test_suggestions,
                failure_diagnoses,
                html_path
            )

        return report

    def _generate_summary(
        self,
        code_elements: Dict[str, List[CodeElement]],
        coverage_gaps: List[CoverageGap]
    ) -> Dict[str, Any]:
        total_elements = sum(len(elements) for elements in code_elements.values())
        total_files = len(code_elements)
        total_gaps = len(coverage_gaps)

        high_priority_gaps = sum(1 for g in coverage_gaps if g.priority >= 8)
        medium_priority_gaps = sum(1 for g in coverage_gaps if 5 <= g.priority < 8)
        low_priority_gaps = sum(1 for g in coverage_gaps if g.priority < 5)

        return {
            "total_files_analyzed": total_files,
            "total_code_elements": total_elements,
            "total_coverage_gaps": total_gaps,
            "high_priority_gaps": high_priority_gaps,
            "medium_priority_gaps": medium_priority_gaps,
            "low_priority_gaps": low_priority_gaps,
            "estimated_coverage": round((total_elements - total_gaps) / max(total_elements, 1) * 100, 2),
            "coverage_threshold_met": round((total_elements - total_gaps) / max(total_elements, 1) * 100, 2) >= self.config.coverage_threshold
        }

    def _analyze_coverage_by_file(
        self,
        code_elements: Dict[str, List[CodeElement]],
        coverage_gaps: List[CoverageGap]
    ) -> List[Dict[str, Any]]:
        file_analysis = []

        for file_path, elements in code_elements.items():
            file_gaps = [g for g in coverage_gaps if g.element.file_path == file_path]
            covered_count = len(elements) - len(file_gaps)
            coverage_rate = covered_count / max(len(elements), 1) * 100

            file_analysis.append({
                "file_path": file_path,
                "total_elements": len(elements),
                "covered_elements": covered_count,
                "coverage_rate": round(coverage_rate, 2),
                "gaps": [
                    {
                        "element": g.element.name,
                        "type": g.gap_type.value,
                        "priority": g.priority,
                        "suggestion": g.suggestion
                    }
                    for g in file_gaps[:5]
                ]
            })

        return sorted(file_analysis, key=lambda x: x["coverage_rate"])

    def _analyze_gaps(self, coverage_gaps: List[CoverageGap]) -> Dict[str, Any]:
        gap_by_type = defaultdict(list)
        for gap in coverage_gaps:
            gap_by_type[gap.gap_type.value].append(gap)

        return {
            "by_type": {
                gap_type: len(gaps)
                for gap_type, gaps in gap_by_type.items()
            },
            "by_priority": {
                "high": sum(1 for g in coverage_gaps if g.priority >= 8),
                "medium": sum(1 for g in coverage_gaps if 5 <= g.priority < 8),
                "low": sum(1 for g in coverage_gaps if g.priority < 5)
            },
            "top_gaps": [
                {
                    "element": g.element.name,
                    "file": g.element.file_path,
                    "type": g.gap_type.value,
                    "priority": g.priority,
                    "impact_score": g.impact_score,
                    "suggestion": g.suggestion
                }
                for g in coverage_gaps[:10]
            ]
        }

    def _generate_recommendations(self, coverage_gaps: List[CoverageGap]) -> List[str]:
        recommendations = []

        high_priority = [g for g in coverage_gaps if g.priority >= 8]
        if high_priority:
            recommendations.append(f"优先处理 {len(high_priority)} 个高优先级覆盖率缺口")

        complex_gaps = [g for g in coverage_gaps if g.element.complexity > 10]
        if complex_gaps:
            recommendations.append(f"有 {len(complex_gaps)} 个高复杂度函数缺少测试，建议优先覆盖")

        api_gaps = [g for g in coverage_gaps if any(
            d in g.element.decorators for d in self.config.priority_decorators
        )]
        if api_gaps:
            recommendations.append(f"有 {len(api_gaps)} 个API端点缺少测试，建议添加集成测试")

        if not recommendations:
            recommendations.append("覆盖率良好，继续保持")

        recommendations.extend([
            "建议定期运行覆盖率检查，防止覆盖率下降",
            "使用突变测试验证测试质量",
            "为边界条件添加测试用例"
        ])

        return recommendations

    def _calculate_metrics(
        self,
        code_elements: Dict[str, List[CodeElement]],
        coverage_gaps: List[CoverageGap]
    ) -> Dict[str, Any]:
        all_elements = [e for elements in code_elements.values() for e in elements]
        total_complexity = sum(e.complexity for e in all_elements)
        avg_complexity = total_complexity / max(len(all_elements), 1)

        return {
            "average_complexity": round(avg_complexity, 2),
            "max_complexity": max((e.complexity for e in all_elements), default=0),
            "total_lines_analyzed": sum(
                e.line_end - e.line_start + 1 for e in all_elements
            ),
            "element_types": {
                "functions": sum(1 for e in all_elements if e.type == "function"),
                "classes": sum(1 for e in all_elements if e.type == "class"),
                "methods": sum(1 for e in all_elements if e.type == "method")
            }
        }

    def print_report(self, report: Dict[str, Any]):
        print("\n" + "=" * 80)
        print("单元测试智能增强报告")
        print("=" * 80)

        summary = report["summary"]
        print(f"\n分析摘要:")
        print(f"  分析文件数: {summary['total_files_analyzed']}")
        print(f"  代码元素数: {summary['total_code_elements']}")
        print(f"  覆盖率缺口: {summary['total_coverage_gaps']}")
        print(f"  预估覆盖率: {summary['estimated_coverage']}%")

        print(f"\n缺口优先级分布:")
        print(f"  高优先级: {summary['high_priority_gaps']}")
        print(f"  中优先级: {summary['medium_priority_gaps']}")
        print(f"  低优先级: {summary['low_priority_gaps']}")

        print(f"\n建议:")
        for i, rec in enumerate(report["recommendations"][:5], 1):
            print(f"  {i}. {rec}")


class UnitTestEnhancer:
    def __init__(self, base_path: str, config: Optional[UnitTestConfig] = None):
        self.base_path = base_path
        self.config = config or UnitTestConfig()
        self.code_analyzer = CodeAnalyzer(base_path, self.config)
        self.test_discovery = TestDiscovery(base_path, self.config)
        self.uncovered_analyzer = UncoveredCodeAnalyzer(base_path, self.config)
        self.failure_diagnostician = FailureDiagnostician()
        self.reporter = EnhancedCoverageReporter(base_path, self.config)
        self.test_generator = TestGenerator(base_path, self.config)
        self.test_optimizer = TestOptimizationSuggester()
        self.boundary_analyzer = BoundaryTestAnalyzer()

    def enhance(
        self,
        coverage_report: Optional[str] = None,
        output_path: str = "docs/reports/unit_test_enhanced.json",
        diagnose_failures: bool = True,
        generate_tests: bool = True,
        optimize_tests: bool = True
    ) -> Dict[str, Any]:
        print("=" * 60)
        print("单元测试智能增强分析")
        print("=" * 60)

        print("\n1. 分析代码元素...")
        code_elements = self.code_analyzer.analyze_project(self.config.source_dirs)
        total_elements = sum(len(e) for e in code_elements.values())
        print(f"   发现 {len(code_elements)} 个文件，{total_elements} 个代码元素")

        print("\n2. 发现现有测试...")
        discovered_tests = self.test_discovery.discover_tests(self.config.test_dirs)
        total_tests = sum(len(t) for t in discovered_tests.values())
        print(f"   发现 {total_tests} 个测试用例")

        print("\n3. 加载覆盖率报告...")
        if coverage_report:
            loaded = self.uncovered_analyzer.load_coverage_report(coverage_report)
            print(f"   覆盖率报告加载{'成功' if loaded else '失败'}")
        else:
            print("   未提供覆盖率报告，将进行静态分析")

        print("\n4. 分析覆盖率缺口...")
        coverage_gaps = self.uncovered_analyzer.analyze_gaps(code_elements)
        print(f"   发现 {len(coverage_gaps)} 个覆盖率缺口")

        print("\n5. 分析边界条件...")
        boundary_analysis = self._analyze_all_boundaries(code_elements)
        print(f"   分析了 {len(boundary_analysis)} 个元素的边界条件")

        print("\n6. 生成测试建议...")
        test_suggestions = []
        for gap in coverage_gaps[:20]:
            suggestion = self.test_discovery.suggest_tests_for_element(gap.element)
            test_suggestions.append(suggestion)
        print(f"   生成 {len(test_suggestions)} 条测试建议")

        generated_test_files = []
        if generate_tests and self.config.generate_missing_tests:
            print("\n7. 自动生成测试文件...")
            generated_test_files = self._generate_missing_tests(code_elements, coverage_gaps)
            print(f"   生成了 {len(generated_test_files)} 个测试文件")

        optimization_suggestions = []
        if optimize_tests:
            print("\n8. 分析测试优化建议...")
            optimization_suggestions = self._analyze_test_optimization()
            print(f"   发现 {len(optimization_suggestions)} 条优化建议")

        failure_diagnoses = []
        if diagnose_failures and self.config.diagnose_failures:
            print("\n9. 诊断失败测试...")
            failure_diagnoses = self._diagnose_recent_failures()
            print(f"   诊断 {len(failure_diagnoses)} 个失败测试")

        print("\n10. 生成增强报告...")
        report = self.reporter.generate_report(
            code_elements,
            coverage_gaps,
            test_suggestions,
            failure_diagnoses,
            output_path
        )
        
        report["boundary_analysis"] = boundary_analysis
        report["generated_tests"] = generated_test_files
        report["optimization_suggestions"] = optimization_suggestions

        self.reporter.print_report(report)

        return report

    def _analyze_all_boundaries(self, code_elements: Dict[str, List[CodeElement]]) -> Dict[str, Any]:
        analysis = {}
        
        for file_path, elements in code_elements.items():
            file_analysis = {
                "file": file_path,
                "elements": []
            }
            
            for element in elements:
                if element.type == "function":
                    cases = self.boundary_analyzer.analyze_function_boundaries(element)
                    summary = self.boundary_analyzer.get_boundary_summary(cases)
                    file_analysis["elements"].append({
                        "name": element.name,
                        "type": element.type,
                        "boundary_cases": len(cases),
                        "summary": summary
                    })
            
            if file_analysis["elements"]:
                analysis[file_path] = file_analysis
        
        return analysis

    def _generate_missing_tests(
        self, 
        code_elements: Dict[str, List[CodeElement]], 
        coverage_gaps: List[CoverageGap]
    ) -> List[str]:
        generated_files = []
        
        gaps_by_file = defaultdict(list)
        for gap in coverage_gaps:
            gaps_by_file[gap.element.file_path].append(gap.element)
        
        for file_path, elements in gaps_by_file.items():
            if len(elements) >= 3:
                test_file = self.test_generator.generate_test_file(file_path, elements)
                saved_path = self.test_generator.save_test_file(
                    test_file, 
                    self.config.test_dirs[0] if self.config.test_dirs else "tests"
                )
                if saved_path:
                    generated_files.append(saved_path)
        
        return generated_files

    def _analyze_test_optimization(self) -> List[Dict]:
        suggestions = []
        
        for test_dir in self.config.test_dirs:
            test_path = Path(self.base_path) / test_dir
            if test_path.exists():
                for test_file in test_path.rglob("test_*.py"):
                    file_suggestions = self.test_optimizer.analyze_test_file(str(test_file))
                    suggestions.extend(file_suggestions)
        
        return suggestions[:50]

    def _diagnose_recent_failures(self) -> List[FailureDiagnosis]:
        diagnoses = []
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--tb=short", "-q", "--no-header"],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                output = result.stdout + result.stderr
                failed_tests = self._extract_failed_tests(output)
                
                for test_name, error_msg in failed_tests[:10]:
                    diagnosis = self.failure_diagnostician.diagnose(test_name, error_msg, output)
                    diagnoses.append(diagnosis)
                    
        except Exception as e:
            print(f"   诊断失败测试时出错: {e}")
            
        return diagnoses

    def _extract_failed_tests(self, output: str) -> List[Tuple[str, str]]:
        failed = []
        lines = output.split("\n")
        
        for i, line in enumerate(lines):
            if "FAILED" in line:
                parts = line.split()
                if parts:
                    test_name = parts[0] if parts else "unknown"
                    error_msg = ""
                    if i + 1 < len(lines):
                        error_msg = lines[i + 1]
                    failed.append((test_name, error_msg))
                    
        return failed


def main():
    parser = argparse.ArgumentParser(description="单元测试智能增强")
    parser.add_argument(
        "--config",
        help="配置文件路径 (YAML/JSON)"
    )
    parser.add_argument(
        "--source-dirs",
        nargs="+",
        help="源代码目录"
    )
    parser.add_argument(
        "--test-dirs",
        nargs="+",
        help="测试目录"
    )
    parser.add_argument(
        "--coverage-report",
        help="覆盖率报告路径"
    )
    parser.add_argument(
        "--output",
        default="docs/reports/unit_test_enhanced.json",
        help="输出报告路径"
    )
    parser.add_argument(
        "--generate-config",
        action="store_true",
        help="生成配置文件模板"
    )
    parser.add_argument(
        "--no-diagnose",
        action="store_true",
        help="跳过失败诊断"
    )

    args = parser.parse_args()

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    config_loader = ConfigLoader(base_path)
    
    if args.generate_config:
        config_loader.save_template("unit_test_config.yaml")
        print("配置文件模板已生成: unit_test_config.yaml")
        return 0
    
    config = config_loader.load(args.config)
    
    if args.source_dirs:
        config.source_dirs = args.source_dirs
    if args.test_dirs:
        config.test_dirs = args.test_dirs

    enhancer = UnitTestEnhancer(base_path, config)
    report = enhancer.enhance(
        args.coverage_report,
        args.output,
        diagnose_failures=not args.no_diagnose
    )

    if config.fail_on_coverage_gap and report["summary"]["high_priority_gaps"] > 0:
        return 1
    
    return 0 if report["summary"]["coverage_threshold_met"] else 1


if __name__ == "__main__":
    sys.exit(main())
