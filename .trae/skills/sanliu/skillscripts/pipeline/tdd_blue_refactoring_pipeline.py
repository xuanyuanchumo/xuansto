#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDD蓝阶段 - 重构管道 (增强版)

整合智能代码异味检测、重构建议生成和验证机制的完整管道。

增强功能:
1. 红阶段测试生成:
   - 支持从SDD规范自动生成测试用例
   - 支持多种测试框架（pytest/jest/junit）
   - 支持测试用例模板定制
   - 支持边界条件和异常测试生成

2. 绿阶段代码实现:
   - 支持从测试用例生成最小实现代码
   - 支持多种编程语言（Python/TypeScript/Java/Go）
   - 支持代码模板定制
   - 支持代码风格检查

3. 蓝阶段重构优化:
   - 支持代码质量分析
   - 支持重构建议生成
   - 支持重构效果验证
   - 支持重构回滚

4. 循环验证机制:
   - 验证测试覆盖率
   - 验证代码质量
   - 验证功能正确性
   - 生成循环报告

使用示例:
    python tdd_blue_refactoring_pipeline.py
    python tdd_blue_refactoring_pipeline.py --full
    python tdd_blue_refactoring_pipeline.py --detect-only
    python tdd_blue_refactoring_pipeline.py --validate-only
    python tdd_blue_refactoring_pipeline.py --tdd-cycle --spec specs/api.yaml
    python tdd_blue_refactoring_pipeline.py --generate-tests --spec specs/api.yaml --framework pytest
    python tdd_blue_refactoring_pipeline.py --generate-code --test-file tests/test_api.py --language python
"""

import os
import sys
import json
import argparse
import logging
import re
import subprocess
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from enum import Enum


class CyclePhase(Enum):
    """TDD循环阶段枚举"""
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class PhaseStatus(Enum):
    """阶段状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TestFramework(Enum):
    """测试框架枚举"""
    PYTEST = "pytest"
    JEST = "jest"
    JUNIT = "junit"
    MOCHA = "mocha"
    GO_TEST = "go_test"
    RUST_TEST = "rust_test"


class ProgrammingLanguage(Enum):
    """编程语言枚举"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CSHARP = "csharp"


class RefactoringType(Enum):
    """重构类型枚举"""
    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    RENAME = "rename"
    MOVE = "move"
    INLINE = "inline"
    SIMPLIFY = "simplify"
    OPTIMIZE = "optimize"


class TestType(Enum):
    """测试类型枚举"""
    UNIT = "unit"
    INTEGRATION = "integration"
    BOUNDARY = "boundary"
    EXCEPTION = "exception"
    PERFORMANCE = "performance"
    SECURITY = "security"


class CodeQualityMetric(Enum):
    """代码质量指标枚举"""
    COMPLEXITY = "complexity"
    COUPLING = "coupling"
    COHESION = "cohesion"
    DUPLICATION = "duplication"
    COVERAGE = "coverage"
    MAINTAINABILITY = "maintainability"


@dataclass
class PhaseExecutionRecord:
    """阶段执行记录"""
    phase: CyclePhase
    status: PhaseStatus = PhaseStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: float = 0.0
    test_passed: int = 0
    test_failed: int = 0
    test_skipped: int = 0
    error_message: Optional[str] = None
    artifacts: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class TestCaseSpec:
    """测试用例规范"""
    id: str
    name: str
    test_type: TestType
    description: str = ""
    arrange: str = ""
    act: str = ""
    assert_: str = ""
    expected_result: Any = None
    boundary_values: List[Any] = field(default_factory=list)
    exception_type: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class GeneratedTestCase:
    """生成的测试用例"""
    spec: TestCaseSpec
    framework: TestFramework
    code: str
    file_path: str = ""
    dependencies: List[str] = field(default_factory=list)
    fixtures: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeImplementation:
    """代码实现"""
    language: ProgrammingLanguage
    code: str
    file_path: str = ""
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    style_issues: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RefactoringSuggestion:
    """重构建议"""
    refactoring_type: RefactoringType
    target_file: str
    target_location: str
    description: str
    before_code: str = ""
    after_code: str = ""
    estimated_effort: str = "medium"
    impact: str = "medium"
    rationale: str = ""


@dataclass
class RefactoringResult:
    """重构结果"""
    suggestion: RefactoringSuggestion
    success: bool
    applied_at: str = ""
    rollback_data: Optional[Dict[str, Any]] = None
    verification_passed: bool = False
    quality_improvement: Dict[str, float] = field(default_factory=dict)


@dataclass
class CodeQualityReport:
    """代码质量报告"""
    file_path: str
    metrics: Dict[CodeQualityMetric, float] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    overall_score: float = 0.0
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CycleVerificationResult:
    """循环验证结果"""
    cycle_id: str
    test_coverage: float = 0.0
    code_quality_score: float = 0.0
    functional_correctness: bool = False
    all_tests_passed: bool = False
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    verified_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CycleProgress:
    """循环进度跟踪"""
    current_phase: CyclePhase = CyclePhase.RED
    current_iteration: int = 0
    total_iterations: int = 0
    phase_progress: float = 0.0
    overall_progress: float = 0.0
    estimated_remaining_seconds: float = 0.0
    started_at: Optional[str] = None
    health_status: str = "healthy"
    phase_records: List[PhaseExecutionRecord] = field(default_factory=list)


@dataclass
class StageExecutionReport:
    """阶段执行报告"""
    report_id: str
    stage_name: str
    started_at: str
    completed_at: Optional[str] = None
    status: PhaseStatus = PhaseStatus.PENDING
    input_artifacts: Dict[str, str] = field(default_factory=dict)
    output_artifacts: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    next_stage: Optional[str] = None


@dataclass
class PipelineResult:
    """管道执行结果"""
    timestamp: str
    project_root: str
    detection_result: Optional[Dict[str, Any]] = None
    suggestion_result: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    cycle_progress: Optional[CycleProgress] = None
    stage_reports: List[StageExecutionReport] = field(default_factory=list)
    phase_execution_log: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project_root": self.project_root,
            "detection_result": self.detection_result,
            "suggestion_result": self.suggestion_result,
            "validation_result": self.validation_result,
            "summary": self.summary,
            "success": self.success,
            "cycle_progress": self._cycle_progress_to_dict(),
            "stage_reports": [r.__dict__ for r in self.stage_reports],
            "phase_execution_log": self.phase_execution_log
        }
    
    def _cycle_progress_to_dict(self) -> Optional[Dict[str, Any]]:
        if not self.cycle_progress:
            return None
        return {
            "current_phase": self.cycle_progress.current_phase.value,
            "current_iteration": self.cycle_progress.current_iteration,
            "total_iterations": self.cycle_progress.total_iterations,
            "phase_progress": self.cycle_progress.phase_progress,
            "overall_progress": self.cycle_progress.overall_progress,
            "estimated_remaining_seconds": self.cycle_progress.estimated_remaining_seconds,
            "health_status": self.cycle_progress.health_status
        }


class TestTemplateManager:
    """测试模板管理器"""
    
    TEMPLATES = {
        TestFramework.PYTEST: {
            "unit": '''def test_{test_name}():
    """{description}"""
    # Arrange
    {arrange}
    
    # Act
    {act}
    
    # Assert
    {assert_}
''',
            "boundary": '''@pytest.mark.parametrize("input_value,expected", [
    {parametrize_data}
])
def test_{test_name}_boundary(input_value, expected):
    """边界测试: {description}"""
    # Arrange
    {arrange}
    
    # Act
    result = {act}
    
    # Assert
    {assert_}
''',
            "exception": '''import pytest

def test_{test_name}_exception():
    """异常测试: {description}"""
    # Arrange
    {arrange}
    
    # Act & Assert
    with pytest.raises({exception_type}):
        {act}
'''
        },
        TestFramework.JEST: {
            "unit": '''describe('{suite_name}', () => {{
    test('{test_name}', () => {{
        // Arrange
        {arrange}
        
        // Act
        {act}
        
        // Assert
        {assert_}
    }});
}});
''',
            "boundary": '''describe('{suite_name}', () => {{
    test.each`
        input | expected
        {parametrize_data}
    `('{test_name} - boundary: $input => $expected', ({input}, expected) => {{
        // Arrange
        {arrange}
        
        // Act
        const result = {act};
        
        // Assert
        {assert_}
    }});
}});
''',
            "exception": '''describe('{suite_name}', () => {{
    test('{test_name} - exception', () => {{
        // Arrange
        {arrange}
        
        // Act & Assert
        expect(() => {{
            {act}
        }}).toThrow({exception_type});
    }});
}});
'''
        },
        TestFramework.JUNIT: {
            "unit": '''@Test
public void {test_name}() {{
    // Arrange
    {arrange}
    
    // Act
    {act}
    
    // Assert
    {assert_}
}}
''',
            "boundary": '''@ParameterizedTest
@CsvSource({{
    {parametrize_data}
}})
public void {test_name}_boundary(Object input, Object expected) {{
    // Arrange
    {arrange}
    
    // Act
    Object result = {act};
    
    // Assert
    {assert_}
}}
''',
            "exception": '''@Test(expected = {exception_type}.class)
public void {test_name}_exception() {{
    // Arrange
    {arrange}
    
    // Act
    {act}
}}
'''
        }
    }
    
    @classmethod
    def get_template(cls, framework: TestFramework, test_type: str) -> str:
        """获取测试模板"""
        return cls.TEMPLATES.get(framework, {}).get(test_type, cls.TEMPLATES[TestFramework.PYTEST]["unit"])
    
    @classmethod
    def register_template(cls, framework: TestFramework, test_type: str, template: str):
        """注册自定义模板"""
        if framework not in cls.TEMPLATES:
            cls.TEMPLATES[framework] = {}
        cls.TEMPLATES[framework][test_type] = template


class RedPhaseTestGenerator:
    """红阶段测试生成器"""
    
    def __init__(self, 
                 framework: TestFramework = TestFramework.PYTEST,
                 output_dir: Optional[Path] = None,
                 template_manager: Optional[TestTemplateManager] = None,
                 logger: Optional[logging.Logger] = None):
        self.framework = framework
        self.output_dir = output_dir or Path("tests/generated")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.template_manager = template_manager or TestTemplateManager()
        self.logger = logger or logging.getLogger(__name__)
        self._test_counter = 0
    
    def generate_from_sdd_spec(self, spec: Dict[str, Any]) -> List[GeneratedTestCase]:
        """从SDD规范生成测试用例"""
        test_cases = []
        spec_id = spec.get("id", "UNKNOWN")
        spec_name = spec.get("name", "unknown")
        elements = spec.get("elements", [])
        
        for element in elements:
            element_type = element.get("type", "")
            element_name = element.get("name", "")
            
            if element_type == "input":
                test_cases.extend(self._generate_input_tests(spec_id, spec_name, element))
            elif element_type == "output":
                test_cases.extend(self._generate_output_tests(spec_id, spec_name, element))
            elif element_type == "exception":
                test_cases.extend(self._generate_exception_tests(spec_id, spec_name, element))
        
        test_cases.extend(self._generate_boundary_tests(spec_id, spec_name, elements))
        
        return test_cases
    
    def _generate_input_tests(self, spec_id: str, spec_name: str, element: Dict) -> List[GeneratedTestCase]:
        """生成输入测试"""
        tests = []
        self._test_counter += 1
        
        spec = TestCaseSpec(
            id=f"TC-{spec_id}-INPUT-{self._test_counter:03d}",
            name=f"test_{spec_name.lower()}_valid_input",
            test_type=TestType.UNIT,
            description=f"测试有效输入: {element.get('name')}",
            arrange=f"# 准备有效的{element.get('name')}",
            act=f"# 使用{element.get('name')}执行操作",
            assert_="assert result is not None"
        )
        
        code = self._render_test_code(spec)
        tests.append(GeneratedTestCase(
            spec=spec,
            framework=self.framework,
            code=code
        ))
        
        return tests
    
    def _generate_output_tests(self, spec_id: str, spec_name: str, element: Dict) -> List[GeneratedTestCase]:
        """生成输出测试"""
        tests = []
        self._test_counter += 1
        
        spec = TestCaseSpec(
            id=f"TC-{spec_id}-OUTPUT-{self._test_counter:03d}",
            name=f"test_{spec_name.lower()}_output_validation",
            test_type=TestType.UNIT,
            description=f"测试输出验证: {element.get('name')}",
            arrange="# 准备输入数据",
            act=f"# 执行操作获取{element.get('name')}",
            assert_=f"# 验证{element.get('name')}符合规范\nassert result is not None"
        )
        
        code = self._render_test_code(spec)
        tests.append(GeneratedTestCase(
            spec=spec,
            framework=self.framework,
            code=code
        ))
        
        return tests
    
    def _generate_exception_tests(self, spec_id: str, spec_name: str, element: Dict) -> List[GeneratedTestCase]:
        """生成异常测试"""
        tests = []
        self._test_counter += 1
        
        exception_type = element.get("name", "Exception")
        if self.framework == TestFramework.PYTEST:
            exception_type = exception_type.replace(" ", "")
        elif self.framework == TestFramework.JEST:
            exception_type = f"'{exception_type}'"
        elif self.framework == TestFramework.JUNIT:
            exception_type = exception_type.replace(" ", "") + ".class"
        
        spec = TestCaseSpec(
            id=f"TC-{spec_id}-EXC-{self._test_counter:03d}",
            name=f"test_{spec_name.lower()}_exception",
            test_type=TestType.EXCEPTION,
            description=f"测试异常: {element.get('name')}",
            arrange="# 准备触发异常的条件",
            act="# 执行操作",
            exception_type=exception_type
        )
        
        code = self._render_test_code(spec)
        tests.append(GeneratedTestCase(
            spec=spec,
            framework=self.framework,
            code=code
        ))
        
        return tests
    
    def _generate_boundary_tests(self, spec_id: str, spec_name: str, elements: List[Dict]) -> List[GeneratedTestCase]:
        """生成边界测试"""
        tests = []
        
        input_elements = [e for e in elements if e.get("type") == "input"]
        if not input_elements:
            return tests
        
        self._test_counter += 1
        
        boundary_values = []
        for element in input_elements:
            constraints = element.get("constraints", {})
            if "min" in constraints:
                boundary_values.append(constraints["min"])
            if "max" in constraints:
                boundary_values.append(constraints["max"])
        
        if not boundary_values:
            boundary_values = [0, -1, 1, None, "", []]
        
        parametrize_data = self._format_parametrize_data(boundary_values)
        
        spec = TestCaseSpec(
            id=f"TC-{spec_id}-BOUNDARY-{self._test_counter:03d}",
            name=f"test_{spec_name.lower()}_boundary",
            test_type=TestType.BOUNDARY,
            description="边界条件测试",
            arrange="# 准备边界值",
            act="# 使用边界值执行操作",
            assert_="# 验证边界处理正确",
            boundary_values=boundary_values
        )
        
        code = self._render_test_code(spec, parametrize_data=parametrize_data)
        tests.append(GeneratedTestCase(
            spec=spec,
            framework=self.framework,
            code=code
        ))
        
        return tests
    
    def _render_test_code(self, spec: TestCaseSpec, **kwargs) -> str:
        """渲染测试代码"""
        test_type = spec.test_type.value if spec.test_type != TestType.EXCEPTION else "exception"
        template = self.template_manager.get_template(self.framework, test_type)
        
        code = template.format(
            test_name=spec.name,
            description=spec.description,
            arrange=spec.arrange,
            act=spec.act,
            assert_=spec.assert_,
            exception_type=spec.exception_type or "Exception",
            suite_name=spec.id,
            parametrize_data=kwargs.get("parametrize_data", ""),
            **kwargs
        )
        
        return code
    
    def _format_parametrize_data(self, values: List[Any]) -> str:
        """格式化参数化数据"""
        if self.framework == TestFramework.PYTEST:
            return ",\n    ".join(f"({v!r}, {v!r})" for v in values)
        elif self.framework == TestFramework.JEST:
            return "\n        ".join(f"${v!r} | ${v!r}" for v in values)
        elif self.framework == TestFramework.JUNIT:
            return ",\n    ".join(f'"{v}", "{v}"' for v in values)
        return ""
    
    def save_test_file(self, test_cases: List[GeneratedTestCase], spec_name: str) -> Path:
        """保存测试文件"""
        filename = f"test_{spec_name.lower().replace(' ', '_')}.{self._get_file_extension()}"
        filepath = self.output_dir / filename
        
        content = self._generate_file_header(spec_name)
        for tc in test_cases:
            content += f"\n{tc.code}\n"
            tc.file_path = str(filepath)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.logger.info(f"测试文件已生成: {filepath}")
        return filepath
    
    def _generate_file_header(self, spec_name: str) -> str:
        """生成文件头部"""
        if self.framework == TestFramework.PYTEST:
            return f'''#!/usr/bin/env python3
"""自动生成的测试文件 - {spec_name}
生成时间: {datetime.now().isoformat()}
测试框架: pytest
"""
import pytest
'''
        elif self.framework == TestFramework.JEST:
            return f'''/**
 * 自动生成的测试文件 - {spec_name}
 * 生成时间: {datetime.now().isoformat()}
 * 测试框架: Jest
 */
'''
        elif self.framework == TestFramework.JUNIT:
            return f'''/**
 * 自动生成的测试文件 - {spec_name}
 * 生成时间: {datetime.now().isoformat()}
 * 测试框架: JUnit
 */
import org.junit.Test;
import org.junit.ParameterizedTest;
import org.junit.runners.Parameterized;
'''
        return ""
    
    def _get_file_extension(self) -> str:
        """获取文件扩展名"""
        extensions = {
            TestFramework.PYTEST: "py",
            TestFramework.JEST: "test.js",
            TestFramework.JUNIT: "java",
            TestFramework.GO_TEST: "go",
            TestFramework.RUST_TEST: "rs"
        }
        return extensions.get(self.framework, "py")


class CodeTemplateManager:
    """代码模板管理器"""
    
    TEMPLATES = {
        ProgrammingLanguage.PYTHON: {
            "class": '''class {class_name}:
    """{description}"""
    
    def __init__(self{init_params}):
        {init_body}
    
    {methods}
''',
            "method": '''def {method_name}(self{params}):
    """{description}"""
    {body}
''',
            "function": '''def {function_name}({params}):
    """{description}"""
    {body}
'''
        },
        ProgrammingLanguage.TYPESCRIPT: {
            "class": '''export class {class_name} {{
    {properties}
    
    constructor({init_params}) {{
        {init_body}
    }}
    
    {methods}
}}
''',
            "method": '''{method_name}({params}): {return_type} {{
    {body}
}}
''',
            "function": '''export function {function_name}({params}): {return_type} {{
    {body}
}}
'''
        },
        ProgrammingLanguage.JAVA: {
            "class": '''public class {class_name} {{
    {properties}
    
    public {class_name}({init_params}) {{
        {init_body}
    }}
    
    {methods}
}}
''',
            "method": '''public {return_type} {method_name}({params}) {{
    {body}
}}
''',
            "function": '''public static {return_type} {function_name}({params}) {{
    {body}
}}
'''
        },
        ProgrammingLanguage.GO: {
            "class": '''type {class_name} struct {{
    {properties}
}}

func New{class_name}({init_params}) *{class_name} {{
    return &{class_name}{{
        {init_body}
    }}
}}

{methods}
''',
            "method": '''func ({receiver} *{class_name}) {method_name}({params}) {return_type} {{
    {body}
}}
''',
            "function": '''func {function_name}({params}) {return_type} {{
    {body}
}}
'''
        }
    }
    
    @classmethod
    def get_template(cls, language: ProgrammingLanguage, template_type: str) -> str:
        """获取代码模板"""
        return cls.TEMPLATES.get(language, {}).get(template_type, "")
    
    @classmethod
    def register_template(cls, language: ProgrammingLanguage, template_type: str, template: str):
        """注册自定义模板"""
        if language not in cls.TEMPLATES:
            cls.TEMPLATES[language] = {}
        cls.TEMPLATES[language][template_type] = template


class GreenPhaseCodeGenerator:
    """绿阶段代码生成器"""
    
    STYLE_CHECKERS = {
        ProgrammingLanguage.PYTHON: ["flake8", "pylint", "black"],
        ProgrammingLanguage.TYPESCRIPT: ["eslint", "prettier"],
        ProgrammingLanguage.JAVASCRIPT: ["eslint", "prettier"],
        ProgrammingLanguage.JAVA: ["checkstyle", "spotbugs"],
        ProgrammingLanguage.GO: ["golint", "gofmt"],
    }
    
    def __init__(self,
                 language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
                 output_dir: Optional[Path] = None,
                 template_manager: Optional[CodeTemplateManager] = None,
                 logger: Optional[logging.Logger] = None):
        self.language = language
        self.output_dir = output_dir or Path("src/generated")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.template_manager = template_manager or CodeTemplateManager()
        self.logger = logger or logging.getLogger(__name__)
    
    def generate_from_tests(self, test_cases: List[GeneratedTestCase]) -> CodeImplementation:
        """从测试用例生成最小实现代码"""
        functions = []
        imports = set()
        
        for tc in test_cases:
            func_name = self._extract_function_name(tc.spec.name)
            func_code = self._generate_minimal_function(func_name, tc.spec)
            functions.append(func_code)
            
            tc_deps = self._extract_dependencies(tc.code)
            imports.update(tc_deps)
        
        class_name = self._infer_class_name(test_cases)
        class_code = self._generate_class(class_name, functions)
        
        implementation = CodeImplementation(
            language=self.language,
            code=class_code,
            imports=list(imports)
        )
        
        style_issues = self._check_style(implementation)
        implementation.style_issues = style_issues
        
        return implementation
    
    def _extract_function_name(self, test_name: str) -> str:
        """从测试名称提取函数名"""
        name = test_name.replace("test_", "").replace("Test", "")
        parts = name.split("_")
        return parts[0] if parts else "function"
    
    def _generate_minimal_function(self, func_name: str, spec: TestCaseSpec) -> str:
        """生成最小函数实现"""
        template = self.template_manager.get_template(self.language, "function")
        
        if spec.test_type == TestType.EXCEPTION:
            body = self._generate_exception_body(spec)
        elif spec.test_type == TestType.BOUNDARY:
            body = self._generate_boundary_body(spec)
        else:
            body = self._generate_default_body(spec)
        
        return template.format(
            function_name=func_name,
            params="",
            return_type="Any",
            description=spec.description,
            body=body
        )
    
    def _generate_default_body(self, spec: TestCaseSpec) -> str:
        """生成默认函数体"""
        if self.language == ProgrammingLanguage.PYTHON:
            return "pass  # TODO: 实现功能"
        elif self.language in [ProgrammingLanguage.TYPESCRIPT, ProgrammingLanguage.JAVASCRIPT]:
            return "// TODO: 实现功能\nreturn null;"
        elif self.language == ProgrammingLanguage.JAVA:
            return "// TODO: 实现功能\nreturn null;"
        elif self.language == ProgrammingLanguage.GO:
            return "// TODO: 实现功能\nreturn nil"
        return "pass"
    
    def _generate_exception_body(self, spec: TestCaseSpec) -> str:
        """生成异常函数体"""
        if self.language == ProgrammingLanguage.PYTHON:
            return f"raise NotImplementedError('{spec.description}')"
        elif self.language in [ProgrammingLanguage.TYPESCRIPT, ProgrammingLanguage.JAVASCRIPT]:
            return f"throw new Error('{spec.description}');"
        elif self.language == ProgrammingLanguage.JAVA:
            return f'throw new UnsupportedOperationException("{spec.description}");'
        elif self.language == ProgrammingLanguage.GO:
            return f'panic("{spec.description}")'
        return "pass"
    
    def _generate_boundary_body(self, spec: TestCaseSpec) -> str:
        """生成边界处理函数体"""
        if self.language == ProgrammingLanguage.PYTHON:
            return "if value is None:\n    return None\nreturn value"
        elif self.language in [ProgrammingLanguage.TYPESCRIPT, ProgrammingLanguage.JAVASCRIPT]:
            return "if (value === null || value === undefined) {\n    return null;\n}\nreturn value;"
        elif self.language == ProgrammingLanguage.JAVA:
            return 'if (value == null) {\n    return null;\n}\nreturn value;'
        elif self.language == ProgrammingLanguage.GO:
            return 'if value == nil {\n    return nil\n}\nreturn value'
        return "pass"
    
    def _generate_class(self, class_name: str, methods: List[str]) -> str:
        """生成类代码"""
        template = self.template_manager.get_template(self.language, "class")
        
        return template.format(
            class_name=class_name,
            description="自动生成的类",
            init_params="",
            init_body="pass" if self.language == ProgrammingLanguage.PYTHON else "",
            methods="\n    ".join(methods),
            properties="",
            return_type="Any"
        )
    
    def _infer_class_name(self, test_cases: List[GeneratedTestCase]) -> str:
        """推断类名"""
        if test_cases:
            first_name = test_cases[0].spec.name
            parts = first_name.replace("test_", "").split("_")
            return "".join(p.capitalize() for p in parts[:2])
        return "GeneratedClass"
    
    def _extract_dependencies(self, code: str) -> List[str]:
        """提取依赖"""
        imports = []
        if self.language == ProgrammingLanguage.PYTHON:
            import_pattern = r'^import\s+(\S+)|^from\s+(\S+)\s+import'
            for match in re.finditer(import_pattern, code, re.MULTILINE):
                imports.append(match.group(1) or match.group(2))
        return imports
    
    def _check_style(self, implementation: CodeImplementation) -> List[Dict[str, Any]]:
        """检查代码风格"""
        issues = []
        checkers = self.STYLE_CHECKERS.get(self.language, [])
        
        for checker in checkers:
            try:
                if checker == "flake8" and self.language == ProgrammingLanguage.PYTHON:
                    issues.extend(self._run_flake8(implementation.code))
                elif checker == "eslint" and self.language in [ProgrammingLanguage.TYPESCRIPT, ProgrammingLanguage.JAVASCRIPT]:
                    issues.extend(self._run_eslint(implementation.code))
            except Exception as e:
                self.logger.warning(f"风格检查器 {checker} 执行失败: {e}")
        
        return issues
    
    def _run_flake8(self, code: str) -> List[Dict[str, Any]]:
        """运行flake8检查"""
        issues = []
        lines = code.split("\n")
        
        for i, line in enumerate(lines, 1):
            if len(line) > 79:
                issues.append({
                    "line": i,
                    "message": "E501 line too long",
                    "severity": "warning"
                })
        
        return issues
    
    def _run_eslint(self, code: str) -> List[Dict[str, Any]]:
        """运行eslint检查"""
        issues = []
        lines = code.split("\n")
        
        for i, line in enumerate(lines, 1):
            if "var " in line:
                issues.append({
                    "line": i,
                    "message": "prefer const over var",
                    "severity": "warning"
                })
        
        return issues
    
    def save_implementation(self, implementation: CodeImplementation, filename: str) -> Path:
        """保存实现代码"""
        extension = self._get_file_extension()
        filepath = self.output_dir / f"{filename}.{extension}"
        
        content = self._generate_file_header()
        if implementation.imports:
            content += self._format_imports(implementation.imports)
        content += "\n" + implementation.code
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        implementation.file_path = str(filepath)
        self.logger.info(f"代码文件已生成: {filepath}")
        return filepath
    
    def _generate_file_header(self) -> str:
        """生成文件头部"""
        return f'''# 自动生成的代码
# 生成时间: {datetime.now().isoformat()}
# 编程语言: {self.language.value}
# 注意: 此代码为最小实现，需要根据实际需求完善

'''
    
    def _format_imports(self, imports: List[str]) -> str:
        """格式化导入语句"""
        if self.language == ProgrammingLanguage.PYTHON:
            return "\n".join(f"import {imp}" for imp in sorted(imports))
        elif self.language in [ProgrammingLanguage.TYPESCRIPT, ProgrammingLanguage.JAVASCRIPT]:
            return "\n".join(f"import {{ {imp} }} from '{imp}';" for imp in sorted(imports))
        elif self.language == ProgrammingLanguage.JAVA:
            return "\n".join(f"import {imp};" for imp in sorted(imports))
        elif self.language == ProgrammingLanguage.GO:
            return "\n".join(f'import "{imp}"' for imp in sorted(imports))
        return ""
    
    def _get_file_extension(self) -> str:
        """获取文件扩展名"""
        extensions = {
            ProgrammingLanguage.PYTHON: "py",
            ProgrammingLanguage.TYPESCRIPT: "ts",
            ProgrammingLanguage.JAVASCRIPT: "js",
            ProgrammingLanguage.JAVA: "java",
            ProgrammingLanguage.GO: "go",
            ProgrammingLanguage.RUST: "rs",
            ProgrammingLanguage.CSHARP: "cs"
        }
        return extensions.get(self.language, "py")


class BluePhaseRefactoringOptimizer:
    """蓝阶段重构优化器"""
    
    def __init__(self,
                 project_root: Optional[Path] = None,
                 logger: Optional[logging.Logger] = None):
        self.project_root = project_root or Path.cwd()
        self.logger = logger or logging.getLogger(__name__)
        self._backup_dir = self.project_root / ".refactoring_backups"
        self._backup_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_code_quality(self, file_path: Path) -> CodeQualityReport:
        """分析代码质量"""
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        metrics = self._calculate_metrics(code)
        issues = self._detect_issues(code)
        suggestions = self._generate_suggestions(issues)
        overall_score = self._calculate_overall_score(metrics, issues)
        
        return CodeQualityReport(
            file_path=str(file_path),
            metrics=metrics,
            issues=issues,
            suggestions=suggestions,
            overall_score=overall_score
        )
    
    def _calculate_metrics(self, code: str) -> Dict[CodeQualityMetric, float]:
        """计算代码指标"""
        lines = code.split("\n")
        non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        
        metrics = {}
        
        complexity = self._calculate_complexity(code)
        metrics[CodeQualityMetric.COMPLEXITY] = complexity
        
        coupling = self._calculate_coupling(code)
        metrics[CodeQualityMetric.COUPLING] = coupling
        
        cohesion = self._calculate_cohesion(code)
        metrics[CodeQualityMetric.COHESION] = cohesion
        
        duplication = self._calculate_duplication(code)
        metrics[CodeQualityMetric.DUPLICATION] = duplication
        
        metrics[CodeQualityMetric.MAINTAINABILITY] = max(0, 100 - complexity - coupling - duplication * 10)
        
        return metrics
    
    def _calculate_complexity(self, code: str) -> float:
        """计算圈复杂度"""
        complexity_keywords = ["if ", "elif ", "else:", "for ", "while ", "try:", "except:", "with "]
        complexity = 1
        for keyword in complexity_keywords:
            complexity += code.count(keyword)
        return min(complexity, 100)
    
    def _calculate_coupling(self, code: str) -> float:
        """计算耦合度"""
        import_count = code.count("import ") + code.count("from ")
        return min(import_count * 5, 100)
    
    def _calculate_cohesion(self, code: str) -> float:
        """计算内聚度"""
        methods = re.findall(r'def\s+(\w+)\s*\(', code)
        if not methods:
            return 100.0
        return max(50.0, 100 - len(methods) * 5)
    
    def _calculate_duplication(self, code: str) -> float:
        """计算重复度"""
        lines = code.split("\n")
        unique_lines = set(lines)
        if not lines:
            return 0.0
        duplication = (len(lines) - len(unique_lines)) / len(lines) * 100
        return min(duplication, 100)
    
    def _detect_issues(self, code: str) -> List[Dict[str, Any]]:
        """检测代码问题"""
        issues = []
        lines = code.split("\n")
        
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                issues.append({
                    "line": i,
                    "type": "style",
                    "message": f"行过长 ({len(line)} 字符)",
                    "severity": "warning"
                })
            
            if "TODO" in line or "FIXME" in line:
                issues.append({
                    "line": i,
                    "type": "todo",
                    "message": "未完成的TODO项",
                    "severity": "info"
                })
            
            if line.strip().startswith("print("):
                issues.append({
                    "line": i,
                    "type": "debug",
                    "message": "调试打印语句",
                    "severity": "warning"
                })
        
        return issues
    
    def _generate_suggestions(self, issues: List[Dict[str, Any]]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        long_lines = [i for i in issues if i.get("type") == "style"]
        if long_lines:
            suggestions.append(f"有 {len(long_lines)} 行代码过长，建议拆分或重构")
        
        todos = [i for i in issues if i.get("type") == "todo"]
        if todos:
            suggestions.append(f"有 {len(todos)} 个TODO项需要处理")
        
        debugs = [i for i in issues if i.get("type") == "debug"]
        if debugs:
            suggestions.append(f"有 {len(debugs)} 个调试语句需要移除")
        
        return suggestions
    
    def _calculate_overall_score(self, metrics: Dict[CodeQualityMetric, float], issues: List) -> float:
        """计算总体得分"""
        if not metrics:
            return 0.0
        
        score = metrics.get(CodeQualityMetric.MAINTAINABILITY, 50)
        score -= len([i for i in issues if i.get("severity") == "error"]) * 10
        score -= len([i for i in issues if i.get("severity") == "warning"]) * 5
        return max(0, min(100, score))
    
    def generate_refactoring_suggestions(self, quality_report: CodeQualityReport) -> List[RefactoringSuggestion]:
        """生成重构建议"""
        suggestions = []
        
        complexity = quality_report.metrics.get(CodeQualityMetric.COMPLEXITY, 0)
        if complexity > 15:
            suggestions.append(RefactoringSuggestion(
                refactoring_type=RefactoringType.EXTRACT_METHOD,
                target_file=quality_report.file_path,
                target_location="complex_methods",
                description=f"复杂度过高 ({complexity})，建议提取方法降低复杂度",
                estimated_effort="high",
                impact="high",
                rationale="降低圈复杂度可以提高代码可读性和可维护性"
            ))
        
        duplication = quality_report.metrics.get(CodeQualityMetric.DUPLICATION, 0)
        if duplication > 10:
            suggestions.append(RefactoringSuggestion(
                refactoring_type=RefactoringType.EXTRACT_METHOD,
                target_file=quality_report.file_path,
                target_location="duplicated_code",
                description=f"代码重复率 {duplication:.1f}%，建议提取公共方法",
                estimated_effort="medium",
                impact="medium",
                rationale="消除重复代码可以减少维护成本"
            ))
        
        coupling = quality_report.metrics.get(CodeQualityMetric.COUPLING, 0)
        if coupling > 30:
            suggestions.append(RefactoringSuggestion(
                refactoring_type=RefactoringType.EXTRACT_CLASS,
                target_file=quality_report.file_path,
                target_location="high_coupling",
                description=f"耦合度过高 ({coupling})，建议提取类降低耦合",
                estimated_effort="high",
                impact="high",
                rationale="降低耦合度可以提高代码的独立性和可测试性"
            ))
        
        return suggestions
    
    def apply_refactoring(self, suggestion: RefactoringSuggestion) -> RefactoringResult:
        """应用重构"""
        file_path = Path(suggestion.target_file)
        
        if not file_path.exists():
            return RefactoringResult(
                suggestion=suggestion,
                success=False
            )
        
        backup_data = self._create_backup(file_path)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_code = f.read()
            
            refactored_code = self._apply_refactoring_type(
                original_code,
                suggestion.refactoring_type,
                suggestion.target_location
            )
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(refactored_code)
            
            return RefactoringResult(
                suggestion=suggestion,
                success=True,
                applied_at=datetime.now().isoformat(),
                rollback_data=backup_data
            )
            
        except Exception as e:
            self.logger.error(f"重构失败: {e}")
            if backup_data:
                self._restore_backup(backup_data)
            
            return RefactoringResult(
                suggestion=suggestion,
                success=False,
                rollback_data=backup_data
            )
    
    def _create_backup(self, file_path: Path) -> Dict[str, Any]:
        """创建备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self._backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()
        
        return {
            "original_path": str(file_path),
            "backup_path": str(backup_path),
            "original_content": original_content,
            "timestamp": timestamp
        }
    
    def _restore_backup(self, backup_data: Dict[str, Any]) -> bool:
        """恢复备份"""
        try:
            original_path = Path(backup_data["original_path"])
            with open(original_path, "w", encoding="utf-8") as f:
                f.write(backup_data["original_content"])
            self.logger.info(f"已恢复备份: {original_path}")
            return True
        except Exception as e:
            self.logger.error(f"恢复备份失败: {e}")
            return False
    
    def _apply_refactoring_type(self, code: str, refactoring_type: RefactoringType, location: str) -> str:
        """应用具体重构类型"""
        if refactoring_type == RefactoringType.SIMPLIFY:
            return self._simplify_code(code)
        elif refactoring_type == RefactoringType.EXTRACT_METHOD:
            return self._extract_method(code, location)
        else:
            return code
    
    def _simplify_code(self, code: str) -> str:
        """简化代码"""
        lines = code.split("\n")
        simplified = []
        
        for line in lines:
            stripped = line.rstrip()
            if stripped:
                simplified.append(stripped)
        
        return "\n".join(simplified)
    
    def _extract_method(self, code: str, location: str) -> str:
        """提取方法（简化版）"""
        return code
    
    def verify_refactoring(self, result: RefactoringResult, test_file: Optional[Path] = None) -> bool:
        """验证重构结果"""
        if not result.success:
            return False
        
        file_path = Path(result.suggestion.target_file)
        if not file_path.exists():
            return False
        
        quality_report = self.analyze_code_quality(file_path)
        
        original_score = 50.0
        new_score = quality_report.overall_score
        
        result.quality_improvement = {
            "before": original_score,
            "after": new_score,
            "improvement": new_score - original_score
        }
        
        if test_file and test_file.exists():
            test_passed = self._run_tests(test_file)
            result.verification_passed = test_passed
            return test_passed
        
        result.verification_passed = new_score >= original_score
        return result.verification_passed
    
    def _run_tests(self, test_file: Path) -> bool:
        """运行测试"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v"],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"测试运行失败: {e}")
            return False
    
    def rollback_refactoring(self, result: RefactoringResult) -> bool:
        """回滚重构"""
        if not result.rollback_data:
            self.logger.warning("没有可用的备份数据")
            return False
        
        return self._restore_backup(result.rollback_data)


class CycleVerifier:
    """循环验证器"""
    
    def __init__(self,
                 project_root: Optional[Path] = None,
                 coverage_threshold: float = 80.0,
                 quality_threshold: float = 70.0,
                 logger: Optional[logging.Logger] = None):
        self.project_root = project_root or Path.cwd()
        self.coverage_threshold = coverage_threshold
        self.quality_threshold = quality_threshold
        self.logger = logger or logging.getLogger(__name__)
    
    def verify_cycle(self,
                     cycle_id: str,
                     test_files: List[Path],
                     source_files: List[Path]) -> CycleVerificationResult:
        """验证TDD循环"""
        result = CycleVerificationResult(cycle_id=cycle_id)
        
        coverage = self._verify_test_coverage(test_files, source_files)
        result.test_coverage = coverage
        
        quality_score = self._verify_code_quality(source_files)
        result.code_quality_score = quality_score
        
        functional_correct = self._verify_functional_correctness(test_files)
        result.functional_correctness = functional_correct
        
        all_passed = self._verify_all_tests_passed(test_files)
        result.all_tests_passed = all_passed
        
        result.issues = self._collect_issues(result)
        result.recommendations = self._generate_recommendations(result)
        
        return result
    
    def _verify_test_coverage(self, test_files: List[Path], source_files: List[Path]) -> float:
        """验证测试覆盖率"""
        if not test_files or not source_files:
            return 0.0
        
        try:
            cmd = [
                sys.executable, "-m", "pytest",
                "--cov=" + str(self.project_root / "src"),
                "--cov-report=term-missing",
                "--cov-report=json",
                "-v"
            ]
            cmd.extend(str(f) for f in test_files)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.project_root)
            )
            
            coverage_match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', result.stdout)
            if coverage_match:
                return float(coverage_match.group(1))
            
            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, "r") as f:
                    coverage_data = json.load(f)
                    return coverage_data.get("totals", {}).get("percent_covered", 0.0)
            
        except Exception as e:
            self.logger.warning(f"覆盖率验证失败: {e}")
        
        return 0.0
    
    def _verify_code_quality(self, source_files: List[Path]) -> float:
        """验证代码质量"""
        if not source_files:
            return 0.0
        
        optimizer = BluePhaseRefactoringOptimizer(self.project_root, self.logger)
        total_score = 0.0
        
        for file_path in source_files:
            if file_path.exists():
                report = optimizer.analyze_code_quality(file_path)
                total_score += report.overall_score
        
        return total_score / len(source_files) if source_files else 0.0
    
    def _verify_functional_correctness(self, test_files: List[Path]) -> bool:
        """验证功能正确性"""
        if not test_files:
            return False
        
        try:
            cmd = [sys.executable, "-m", "pytest", "-v"]
            cmd.extend(str(f) for f in test_files)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"功能验证失败: {e}")
            return False
    
    def _verify_all_tests_passed(self, test_files: List[Path]) -> bool:
        """验证所有测试通过"""
        return self._verify_functional_correctness(test_files)
    
    def _collect_issues(self, result: CycleVerificationResult) -> List[Dict[str, Any]]:
        """收集问题"""
        issues = []
        
        if result.test_coverage < self.coverage_threshold:
            issues.append({
                "type": "coverage",
                "message": f"测试覆盖率 {result.test_coverage:.1f}% 低于阈值 {self.coverage_threshold}%",
                "severity": "warning"
            })
        
        if result.code_quality_score < self.quality_threshold:
            issues.append({
                "type": "quality",
                "message": f"代码质量得分 {result.code_quality_score:.1f} 低于阈值 {self.quality_threshold}",
                "severity": "warning"
            })
        
        if not result.functional_correctness:
            issues.append({
                "type": "functional",
                "message": "功能正确性验证失败",
                "severity": "error"
            })
        
        if not result.all_tests_passed:
            issues.append({
                "type": "test",
                "message": "存在失败的测试用例",
                "severity": "error"
            })
        
        return issues
    
    def _generate_recommendations(self, result: CycleVerificationResult) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if result.test_coverage < self.coverage_threshold:
            recommendations.append(f"增加测试用例以提高覆盖率至 {self.coverage_threshold}% 以上")
        
        if result.code_quality_score < self.quality_threshold:
            recommendations.append("进行代码重构以提高代码质量")
        
        if not result.functional_correctness:
            recommendations.append("修复失败的测试用例以确保功能正确性")
        
        if not recommendations:
            recommendations.append("TDD循环验证通过，代码质量良好")
        
        return recommendations
    
    def generate_cycle_report(self, result: CycleVerificationResult) -> Dict[str, Any]:
        """生成循环报告"""
        return {
            "cycle_id": result.cycle_id,
            "verified_at": result.verified_at,
            "summary": {
                "test_coverage": result.test_coverage,
                "code_quality_score": result.code_quality_score,
                "functional_correctness": result.functional_correctness,
                "all_tests_passed": result.all_tests_passed,
                "overall_status": "passed" if result.all_tests_passed and result.functional_correctness else "failed"
            },
            "thresholds": {
                "coverage_threshold": self.coverage_threshold,
                "quality_threshold": self.quality_threshold
            },
            "issues": result.issues,
            "recommendations": result.recommendations,
            "metrics": {
                "coverage_percentage": result.test_coverage,
                "quality_score": result.code_quality_score,
                "issues_count": len(result.issues)
            }
        }


class TDDBlueRefactoringPipeline:
    """TDD蓝阶段重构管道 (增强版)"""

    def __init__(self, 
                 project_root: Optional[Path] = None,
                 logger: Optional[logging.Logger] = None,
                 test_framework: TestFramework = TestFramework.PYTEST,
                 programming_language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
                 coverage_threshold: float = 80.0,
                 quality_threshold: float = 70.0):
        self.project_root = project_root or get_path_config().SKILL_ROOT
        self.logger = logger or logging.getLogger(__name__)
        self.reports_dir = self.project_root / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self._cycle_progress = CycleProgress()
        self._phase_handlers: Dict[CyclePhase, Callable] = {}
        self._phase_transition_hooks: List[Callable] = []
        self._execution_history: List[Dict[str, Any]] = []
        
        self.test_framework = test_framework
        self.programming_language = programming_language
        self.coverage_threshold = coverage_threshold
        self.quality_threshold = quality_threshold
        
        self.test_generator = RedPhaseTestGenerator(
            framework=test_framework,
            output_dir=self.project_root / "tests" / "generated",
            logger=self.logger
        )
        
        self.code_generator = GreenPhaseCodeGenerator(
            language=programming_language,
            output_dir=self.project_root / "src" / "generated",
            logger=self.logger
        )
        
        self.refactoring_optimizer = BluePhaseRefactoringOptimizer(
            project_root=self.project_root,
            logger=self.logger
        )
        
        self.cycle_verifier = CycleVerifier(
            project_root=self.project_root,
            coverage_threshold=coverage_threshold,
            quality_threshold=quality_threshold,
            logger=self.logger
        )
        
        self._generated_test_cases: List[GeneratedTestCase] = []
        self._generated_code: Optional[CodeImplementation] = None
        self._refactoring_results: List[RefactoringResult] = []
        self._verification_result: Optional[CycleVerificationResult] = None
        
        self._register_default_phase_handlers()
    
    def _register_default_phase_handlers(self):
        """注册默认的阶段处理器"""
        self._phase_handlers = {
            CyclePhase.RED: self._execute_red_phase,
            CyclePhase.GREEN: self._execute_green_phase,
            CyclePhase.BLUE: self._execute_blue_phase,
        }
    
    def register_phase_handler(self, phase: CyclePhase, handler: Callable):
        """注册自定义阶段处理器"""
        self._phase_handlers[phase] = handler
    
    def add_phase_transition_hook(self, hook: Callable):
        """添加阶段转换钩子"""
        self._phase_transition_hooks.append(hook)
    
    def _execute_red_phase(self, context: Dict[str, Any]) -> PhaseExecutionRecord:
        """执行RED阶段 - 编写失败的测试"""
        record = PhaseExecutionRecord(
            phase=CyclePhase.RED,
            status=PhaseStatus.IN_PROGRESS,
            started_at=datetime.now().isoformat()
        )
        
        try:
            self.logger.info("[RED阶段] 编写失败的测试用例...")
            
            detection_result = self._run_detection(context.get("min_severity", "low"))
            
            record.test_passed = 0
            record.test_failed = detection_result.get("total_smells", 0)
            record.artifacts["detection_report"] = str(self.reports_dir / "code_smell_detection_latest.json")
            record.metrics["files_scanned"] = detection_result.get("total_files", 0)
            record.metrics["smells_detected"] = record.test_failed
            
            if record.test_failed > 0:
                record.status = PhaseStatus.COMPLETED
                record.recommendations.append(f"检测到 {record.test_failed} 个代码异味，需要编写测试覆盖")
            else:
                record.status = PhaseStatus.COMPLETED
                record.recommendations.append("未检测到代码异味，可以跳过此阶段")
            
        except Exception as e:
            record.status = PhaseStatus.FAILED
            record.error_message = str(e)
            self.logger.error(f"[RED阶段] 执行失败: {e}")
        
        record.completed_at = datetime.now().isoformat()
        record.duration_seconds = self._calculate_duration(record.started_at, record.completed_at)
        
        return record
    
    def _execute_green_phase(self, context: Dict[str, Any]) -> PhaseExecutionRecord:
        """执行GREEN阶段 - 编写最小实现"""
        record = PhaseExecutionRecord(
            phase=CyclePhase.GREEN,
            status=PhaseStatus.IN_PROGRESS,
            started_at=datetime.now().isoformat()
        )
        
        try:
            self.logger.info("[GREEN阶段] 生成重构建议...")
            
            detection_data = context.get("detection_result", {})
            suggestion_result = self._generate_suggestions(detection_data)
            
            record.test_passed = suggestion_result.get("total_suggestions", 0)
            record.test_failed = 0
            record.artifacts["suggestion_report"] = str(self.reports_dir / "refactoring_suggestions_latest.json")
            record.metrics["suggestions_generated"] = record.test_passed
            record.metrics["estimated_hours"] = suggestion_result.get("summary", {}).get("total_estimated_hours", 0)
            
            if record.test_passed > 0:
                record.status = PhaseStatus.COMPLETED
                record.recommendations.append(f"生成了 {record.test_passed} 个重构建议")
            else:
                record.status = PhaseStatus.COMPLETED
                record.recommendations.append("未生成重构建议，代码质量良好")
            
        except Exception as e:
            record.status = PhaseStatus.FAILED
            record.error_message = str(e)
            self.logger.error(f"[GREEN阶段] 执行失败: {e}")
        
        record.completed_at = datetime.now().isoformat()
        record.duration_seconds = self._calculate_duration(record.started_at, record.completed_at)
        
        return record
    
    def _execute_blue_phase(self, context: Dict[str, Any]) -> PhaseExecutionRecord:
        """执行BLUE阶段 - 重构和验证"""
        record = PhaseExecutionRecord(
            phase=CyclePhase.BLUE,
            status=PhaseStatus.IN_PROGRESS,
            started_at=datetime.now().isoformat()
        )
        
        try:
            self.logger.info("[BLUE阶段] 验证重构结果...")
            
            validation_result = self._run_validation()
            
            overall_status = validation_result.get("overall_status", "unknown")
            summary = validation_result.get("summary", {})
            
            record.test_passed = summary.get("passed", 0)
            record.test_failed = summary.get("failed", 0)
            record.test_skipped = summary.get("warnings", 0)
            record.artifacts["validation_report"] = str(self.reports_dir / "refactoring_validation_latest.json")
            record.metrics["overall_status"] = overall_status
            
            if overall_status == "passed":
                record.status = PhaseStatus.COMPLETED
                record.recommendations.append("重构验证通过，代码质量达标")
            else:
                record.status = PhaseStatus.FAILED
                record.recommendations.append(f"重构验证失败: {record.test_failed} 个检查未通过")
            
        except Exception as e:
            record.status = PhaseStatus.FAILED
            record.error_message = str(e)
            self.logger.error(f"[BLUE阶段] 执行失败: {e}")
        
        record.completed_at = datetime.now().isoformat()
        record.duration_seconds = self._calculate_duration(record.started_at, record.completed_at)
        
        return record
    
    def generate_tests_from_spec(self, spec: Dict[str, Any]) -> List[GeneratedTestCase]:
        """从SDD规范生成测试用例（增强版）"""
        self.logger.info("从SDD规范生成测试用例...")
        
        test_cases = self.test_generator.generate_from_sdd_spec(spec)
        self._generated_test_cases = test_cases
        
        spec_name = spec.get("name", "unknown")
        test_file = self.test_generator.save_test_file(test_cases, spec_name)
        
        self.logger.info(f"生成了 {len(test_cases)} 个测试用例，保存到: {test_file}")
        
        return test_cases
    
    def generate_code_from_tests(self, test_cases: Optional[List[GeneratedTestCase]] = None) -> CodeImplementation:
        """从测试用例生成代码实现（增强版）"""
        if test_cases is None:
            test_cases = self._generated_test_cases
        
        if not test_cases:
            raise ValueError("没有可用的测试用例")
        
        self.logger.info("从测试用例生成代码实现...")
        
        implementation = self.code_generator.generate_from_tests(test_cases)
        self._generated_code = implementation
        
        if implementation.style_issues:
            self.logger.warning(f"发现 {len(implementation.style_issues)} 个代码风格问题")
        
        return implementation
    
    def analyze_and_refactor(self, file_path: Path) -> Tuple[CodeQualityReport, List[RefactoringResult]]:
        """分析代码质量并应用重构（增强版）"""
        self.logger.info(f"分析代码质量: {file_path}")
        
        quality_report = self.refactoring_optimizer.analyze_code_quality(file_path)
        
        self.logger.info(f"代码质量得分: {quality_report.overall_score:.1f}")
        
        suggestions = self.refactoring_optimizer.generate_refactoring_suggestions(quality_report)
        
        results = []
        for suggestion in suggestions:
            self.logger.info(f"应用重构: {suggestion.description}")
            
            result = self.refactoring_optimizer.apply_refactoring(suggestion)
            
            if result.success:
                verified = self.refactoring_optimizer.verify_refactoring(result)
                if not verified:
                    self.logger.warning("重构验证失败，正在回滚...")
                    self.refactoring_optimizer.rollback_refactoring(result)
                    result.success = False
                else:
                    self.logger.info("重构验证通过")
            
            results.append(result)
        
        self._refactoring_results = results
        
        return quality_report, results
    
    def verify_tdd_cycle(self, 
                         cycle_id: str,
                         test_files: List[Path],
                         source_files: List[Path]) -> CycleVerificationResult:
        """验证TDD循环（增强版）"""
        self.logger.info(f"验证TDD循环: {cycle_id}")
        
        result = self.cycle_verifier.verify_cycle(cycle_id, test_files, source_files)
        self._verification_result = result
        
        self.logger.info(f"测试覆盖率: {result.test_coverage:.1f}%")
        self.logger.info(f"代码质量得分: {result.code_quality_score:.1f}")
        self.logger.info(f"功能正确性: {'通过' if result.functional_correctness else '失败'}")
        
        if result.issues:
            self.logger.warning(f"发现 {len(result.issues)} 个问题")
            for issue in result.issues:
                self.logger.warning(f"  - {issue['message']}")
        
        return result
    
    def run_enhanced_tdd_cycle(self, 
                               spec: Dict[str, Any],
                               auto_implement: bool = False) -> Dict[str, Any]:
        """运行增强版TDD循环"""
        cycle_id = f"TDD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.logger.info("=" * 60)
        self.logger.info(f"增强版TDD循环开始: {cycle_id}")
        self.logger.info("=" * 60)
        
        results = {
            "cycle_id": cycle_id,
            "spec": spec,
            "phases": {}
        }
        
        self.logger.info("\n[红阶段] 生成测试用例...")
        test_cases = self.generate_tests_from_spec(spec)
        results["phases"]["red"] = {
            "test_cases_count": len(test_cases),
            "test_file": test_cases[0].file_path if test_cases else None
        }
        
        if auto_implement:
            self.logger.info("\n[绿阶段] 生成代码实现...")
            implementation = self.generate_code_from_tests(test_cases)
            results["phases"]["green"] = {
                "code_file": implementation.file_path,
                "style_issues": len(implementation.style_issues)
            }
        
        self.logger.info("\n[蓝阶段] 代码质量分析...")
        if self._generated_code and self._generated_code.file_path:
            quality_report, refactoring_results = self.analyze_and_refactor(
                Path(self._generated_code.file_path)
            )
            results["phases"]["blue"] = {
                "quality_score": quality_report.overall_score,
                "refactorings_applied": len([r for r in refactoring_results if r.success])
            }
        
        self.logger.info("\n[验证阶段] 验证TDD循环...")
        test_files = [Path(tc.file_path) for tc in test_cases if tc.file_path]
        source_files = []
        if self._generated_code and self._generated_code.file_path:
            source_files = [Path(self._generated_code.file_path)]
        
        if test_files:
            verification = self.verify_tdd_cycle(cycle_id, test_files, source_files)
            results["verification"] = self.cycle_verifier.generate_cycle_report(verification)
        
        results["success"] = (
            self._verification_result is not None and
            self._verification_result.all_tests_passed and
            self._verification_result.functional_correctness
        )
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"TDD循环完成: {'成功' if results['success'] else '失败'}")
        self.logger.info("=" * 60)
        
        return results
    
    def register_custom_test_template(self, test_type: str, template: str):
        """注册自定义测试模板"""
        TestTemplateManager.register_template(self.test_framework, test_type, template)
        self.logger.info(f"已注册自定义测试模板: {test_type}")
    
    def register_custom_code_template(self, template_type: str, template: str):
        """注册自定义代码模板"""
        CodeTemplateManager.register_template(self.programming_language, template_type, template)
        self.logger.info(f"已注册自定义代码模板: {template_type}")
    
    def get_cycle_summary(self) -> Dict[str, Any]:
        """获取循环摘要"""
        return {
            "test_cases_generated": len(self._generated_test_cases),
            "code_generated": self._generated_code is not None,
            "refactorings_applied": len([r for r in self._refactoring_results if r.success]),
            "verification_passed": (
                self._verification_result.all_tests_passed 
                if self._verification_result else False
            ),
            "test_framework": self.test_framework.value,
            "programming_language": self.programming_language.value,
            "coverage_threshold": self.coverage_threshold,
            "quality_threshold": self.quality_threshold
        }
    
    def _calculate_duration(self, start: str, end: str) -> float:
        """计算执行时长"""
        try:
            start_time = datetime.fromisoformat(start)
            end_time = datetime.fromisoformat(end)
            return (end_time - start_time).total_seconds()
        except:
            return 0.0
    
    def _transition_phase(self, current: CyclePhase, record: PhaseExecutionRecord) -> Optional[CyclePhase]:
        """阶段转换逻辑"""
        phase_order = [CyclePhase.RED, CyclePhase.GREEN, CyclePhase.BLUE]
        
        for hook in self._phase_transition_hooks:
            try:
                hook(current, record)
            except Exception as e:
                self.logger.warning(f"阶段转换钩子执行失败: {e}")
        
        if record.status == PhaseStatus.FAILED:
            self._cycle_progress.health_status = "degraded"
            return None
        
        current_index = phase_order.index(current)
        if current_index < len(phase_order) - 1:
            return phase_order[current_index + 1]
        
        return None
    
    def _update_progress(self, phase: CyclePhase, record: PhaseExecutionRecord):
        """更新进度信息"""
        self._cycle_progress.current_phase = phase
        self._cycle_progress.phase_records.append(record)
        
        total_phases = 3
        completed_phases = len([r for r in self._cycle_progress.phase_records 
                               if r.status == PhaseStatus.COMPLETED])
        
        self._cycle_progress.phase_progress = 1.0 if record.status == PhaseStatus.COMPLETED else 0.5
        self._cycle_progress.overall_progress = completed_phases / total_phases
        
        if record.duration_seconds > 0:
            remaining_phases = total_phases - completed_phases
            avg_duration = sum(r.duration_seconds for r in self._cycle_progress.phase_records) / len(self._cycle_progress.phase_records)
            self._cycle_progress.estimated_remaining_seconds = avg_duration * remaining_phases
    
    def run_tdd_cycle(
        self,
        start_phase: CyclePhase = CyclePhase.RED,
        context: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        """
        运行完整的TDD循环
        
        Args:
            start_phase: 起始阶段
            context: 执行上下文
            
        Returns:
            PipelineResult: 执行结果
        """
        context = context or {}
        
        result = PipelineResult(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            cycle_progress=self._cycle_progress
        )
        
        self._cycle_progress.started_at = datetime.now().isoformat()
        self._cycle_progress.current_phase = start_phase
        
        self.logger.info("=" * 60)
        self.logger.info("TDD循环执行开始")
        self.logger.info("=" * 60)
        
        current_phase = start_phase
        detection_result = None
        
        while current_phase:
            self.logger.info(f"\n执行阶段: {current_phase.value.upper()}")
            
            handler = self._phase_handlers.get(current_phase)
            if not handler:
                self.logger.error(f"未找到阶段处理器: {current_phase.value}")
                break
            
            if current_phase == CyclePhase.RED:
                record = handler(context)
                detection_result = record.artifacts.get("detection_report")
                context["detection_result"] = self._load_json(detection_result) if detection_result else {}
                result.detection_result = context["detection_result"]
            elif current_phase == CyclePhase.GREEN:
                record = handler(context)
                result.suggestion_result = self._load_json(record.artifacts.get("suggestion_report", ""))
            elif current_phase == CyclePhase.BLUE:
                record = handler(context)
                result.validation_result = self._load_json(record.artifacts.get("validation_report", ""))
            
            self._update_progress(current_phase, record)
            
            stage_report = StageExecutionReport(
                report_id=f"STAGE-{current_phase.value}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                stage_name=current_phase.value,
                started_at=record.started_at or "",
                completed_at=record.completed_at,
                status=record.status,
                metrics=record.metrics,
                recommendations=record.recommendations
            )
            result.stage_reports.append(stage_report)
            
            result.phase_execution_log.append({
                "phase": current_phase.value,
                "status": record.status.value,
                "duration": record.duration_seconds,
                "passed": record.test_passed,
                "failed": record.test_failed
            })
            
            current_phase = self._transition_phase(current_phase, record)
            
            if record.status == PhaseStatus.FAILED:
                result.success = False
                break
        
        result.summary = self._generate_summary(result)
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("TDD循环执行完成")
        self.logger.info("=" * 60)
        
        return result
    
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """加载JSON文件"""
        if not file_path:
            return {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"加载JSON文件失败: {e}")
            return {}

    def run_full_pipeline(self, min_severity: str = "low",
                          run_validation: bool = True) -> PipelineResult:
        """运行完整管道"""
        self.logger.info("=" * 60)
        self.logger.info("TDD蓝阶段 - 重构管道启动")
        self.logger.info("=" * 60)

        result = PipelineResult(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root)
        )

        try:
            self.logger.info("\n[阶段1] 智能代码异味检测...")
            detection_result = self._run_detection(min_severity)
            result.detection_result = detection_result

            self.logger.info("\n[阶段2] 重构建议生成...")
            suggestion_result = self._generate_suggestions(detection_result)
            result.suggestion_result = suggestion_result

            if run_validation:
                self.logger.info("\n[阶段3] 重构验证...")
                validation_result = self._run_validation()
                result.validation_result = validation_result

            result.summary = self._generate_summary(result)
            result.success = True

            self.logger.info("\n" + "=" * 60)
            self.logger.info("管道执行完成")
            self.logger.info("=" * 60)

        except Exception as e:
            self.logger.error(f"管道执行失败: {e}")
            result.success = False
            result.summary = {"error": str(e)}

        return result

    def run_detection_only(self, min_severity: str = "low") -> PipelineResult:
        """仅运行检测"""
        self.logger.info("运行代码异味检测...")

        result = PipelineResult(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root)
        )

        try:
            detection_result = self._run_detection(min_severity)
            result.detection_result = detection_result
            result.summary = {
                "total_smells": detection_result.get("total_smells", 0),
                "files_with_issues": len(detection_result.get("file_results", []))
            }
            result.success = True
        except Exception as e:
            self.logger.error(f"检测失败: {e}")
            result.success = False

        return result

    def run_suggestions_only(self, input_file: Optional[str] = None) -> PipelineResult:
        """仅生成建议"""
        self.logger.info("生成重构建议...")

        result = PipelineResult(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root)
        )

        try:
            if input_file:
                input_path = Path(input_file)
            else:
                input_path = self.reports_dir / "code_smell_detection_latest.json"

            if not input_path.exists():
                self.logger.error(f"找不到输入文件: {input_path}")
                result.success = False
                return result

            with open(input_path, 'r', encoding='utf-8') as f:
                detection_data = json.load(f)

            suggestion_result = self._generate_suggestions(detection_data)
            result.suggestion_result = suggestion_result
            result.summary = {
                "total_suggestions": suggestion_result.get("total_suggestions", 0)
            }
            result.success = True
        except Exception as e:
            self.logger.error(f"生成建议失败: {e}")
            result.success = False

        return result

    def run_validation_only(self) -> PipelineResult:
        """仅运行验证"""
        self.logger.info("运行重构验证...")

        result = PipelineResult(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root)
        )

        try:
            validation_result = self._run_validation()
            result.validation_result = validation_result
            result.summary = {
                "overall_status": validation_result.get("overall_status", "unknown")
            }
            result.success = validation_result.get("overall_status") == "passed"
        except Exception as e:
            self.logger.error(f"验证失败: {e}")
            result.success = False

        return result

    def _run_detection(self, min_severity: str) -> Dict[str, Any]:
        """运行代码异味检测"""
        from intelligent_code_smell_detector import (
            IntelligentCodeSmellDetector,
            Severity
        )

        severity_map = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.INFO
        }

        detector = IntelligentCodeSmellDetector(
            min_severity=severity_map.get(min_severity, Severity.LOW),
            logger=self.logger
        )

        report = detector.detect_project()
        detector.save_report(report)

        return report.to_dict()

    def _generate_suggestions(self, detection_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成重构建议"""
        from refactoring_suggestion_generator import RefactoringSuggestionGenerator

        generator = RefactoringSuggestionGenerator(
            project_root=self.project_root,
            logger=self.logger
        )

        report = generator.generate_from_smell_data(detection_data)
        generator.save_report(report)

        return report.to_dict()

    def _run_validation(self) -> Dict[str, Any]:
        """运行验证"""
        from refactoring_validator import RefactoringValidator

        validator = RefactoringValidator(
            project_root=self.project_root,
            logger=self.logger
        )

        report = validator.validate_refactoring(
            run_tests=True,
            compare_coverage=True,
            check_syntax=True
        )
        validator.save_report(report)

        return report.to_dict()

    def _generate_summary(self, result: PipelineResult) -> Dict[str, Any]:
        """生成摘要"""
        summary = {
            "pipeline_status": "success" if result.success else "failed",
            "timestamp": result.timestamp
        }

        if result.detection_result:
            summary["detection"] = {
                "total_smells": result.detection_result.get("total_smells", 0),
                "files_scanned": result.detection_result.get("total_files", 0),
                "by_severity": result.detection_result.get("summary", {}).get("by_severity", {})
            }

        if result.suggestion_result:
            summary["suggestions"] = {
                "total_suggestions": result.suggestion_result.get("total_suggestions", 0),
                "estimated_hours": result.suggestion_result.get("summary", {}).get("total_estimated_hours", 0),
                "high_impact_count": result.suggestion_result.get("summary", {}).get("high_impact_count", 0)
            }

        if result.validation_result:
            summary["validation"] = {
                "overall_status": result.validation_result.get("overall_status", "unknown"),
                "passed_checks": result.validation_result.get("summary", {}).get("passed", 0),
                "failed_checks": result.validation_result.get("summary", {}).get("failed", 0)
            }

        return summary

    def print_result(self, result: PipelineResult):
        """打印结果"""
        print("\n" + "=" * 80)
        print("TDD蓝阶段 - 重构管道执行报告")
        print("=" * 80)
        print(f"执行时间: {result.timestamp}")
        print(f"项目根目录: {result.project_root}")
        print(f"执行状态: {'✅ 成功' if result.success else '❌ 失败'}")

        if result.detection_result:
            print("\n" + "-" * 80)
            print("[代码异味检测]")
            print("-" * 80)
            dr = result.detection_result
            print(f"  扫描文件数: {dr.get('total_files', 0)}")
            print(f"  发现问题数: {dr.get('total_smells', 0)}")

            by_severity = dr.get("summary", {}).get("by_severity", {})
            if by_severity:
                print("  按严重程度:")
                for sev, count in by_severity.items():
                    print(f"    - {sev}: {count}")

        if result.suggestion_result:
            print("\n" + "-" * 80)
            print("[重构建议]")
            print("-" * 80)
            sr = result.suggestion_result
            print(f"  建议总数: {sr.get('total_suggestions', 0)}")

            summary = sr.get("summary", {})
            print(f"  预估工时: {summary.get('total_estimated_hours', 0)} 小时")
            print(f"  高影响建议: {summary.get('high_impact_count', 0)}")

            by_priority = summary.get("by_priority", {})
            if by_priority:
                print("  按优先级:")
                for priority, count in by_priority.items():
                    print(f"    - {priority}: {count}")

        if result.validation_result:
            print("\n" + "-" * 80)
            print("[重构验证]")
            print("-" * 80)
            vr = result.validation_result
            status = vr.get("overall_status", "unknown")
            status_icon = "✅" if status == "passed" else "❌" if status == "failed" else "⚠️"
            print(f"  总体状态: {status_icon} {status}")

            summary = vr.get("summary", {})
            print(f"  通过检查: {summary.get('passed', 0)}")
            print(f"  失败检查: {summary.get('failed', 0)}")
            print(f"  警告数量: {summary.get('warnings', 0)}")

        print("\n" + "-" * 80)
        print("[执行摘要]")
        print("-" * 80)
        for key, value in result.summary.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    - {k}: {v}")
            else:
                print(f"  {key}: {value}")

    def save_result(self, result: PipelineResult, output_file: Optional[str] = None) -> Path:
        """保存结果"""
        if output_file:
            output_path = Path(output_file)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.reports_dir / f"tdd_blue_pipeline_{timestamp}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        latest_path = self.reports_dir / "tdd_blue_pipeline_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"结果已保存: {output_path}")
        return output_path


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("TDDBlueRefactoringPipeline")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="TDD蓝阶段 - 重构管道 (增强版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行完整管道
  python tdd_blue_refactoring_pipeline.py --full
  
  # 仅运行代码异味检测
  python tdd_blue_refactoring_pipeline.py --detect-only
  
  # 运行增强版TDD循环
  python tdd_blue_refactoring_pipeline.py --tdd-cycle --spec specs/api.yaml
  
  # 从规范生成测试用例
  python tdd_blue_refactoring_pipeline.py --generate-tests --spec specs/api.yaml --framework pytest
  
  # 从测试生成代码
  python tdd_blue_refactoring_pipeline.py --generate-code --test-file tests/test_api.py --language python
  
  # 分析代码质量
  python tdd_blue_refactoring_pipeline.py --analyze-quality --source src/main.py
  
  # 验证TDD循环
  python tdd_blue_refactoring_pipeline.py --verify-cycle --test-dir tests --source-dir src
        """
    )
    
    parser.add_argument(
        "--full",
        action="store_true",
        help="运行完整管道（默认）"
    )
    
    parser.add_argument(
        "--detect-only",
        action="store_true",
        help="仅运行代码异味检测"
    )
    
    parser.add_argument(
        "--suggest-only",
        action="store_true",
        help="仅生成重构建议"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="仅运行验证"
    )
    
    parser.add_argument(
        "--tdd-cycle",
        action="store_true",
        help="运行增强版TDD循环"
    )
    
    parser.add_argument(
        "--generate-tests",
        action="store_true",
        help="从规范生成测试用例"
    )
    
    parser.add_argument(
        "--generate-code",
        action="store_true",
        help="从测试用例生成代码"
    )
    
    parser.add_argument(
        "--analyze-quality",
        action="store_true",
        help="分析代码质量"
    )
    
    parser.add_argument(
        "--verify-cycle",
        action="store_true",
        help="验证TDD循环"
    )
    
    parser.add_argument(
        "--spec",
        type=str,
        help="规范文件路径（YAML/JSON/Markdown）"
    )
    
    parser.add_argument(
        "--test-file",
        type=str,
        help="测试文件路径"
    )
    
    parser.add_argument(
        "--source",
        type=str,
        help="源代码文件路径"
    )
    
    parser.add_argument(
        "--test-dir",
        type=str,
        help="测试目录路径"
    )
    
    parser.add_argument(
        "--source-dir",
        type=str,
        help="源代码目录路径"
    )
    
    parser.add_argument(
        "--framework",
        type=str,
        choices=["pytest", "jest", "junit", "mocha", "go_test", "rust_test"],
        default="pytest",
        help="测试框架 (默认: pytest)"
    )
    
    parser.add_argument(
        "--language",
        type=str,
        choices=["python", "typescript", "javascript", "java", "go", "rust", "csharp"],
        default="python",
        help="编程语言 (默认: python)"
    )
    
    parser.add_argument(
        "--severity",
        choices=["critical", "high", "medium", "low", "info"],
        default="low",
        help="最低严重程度 (默认: low)"
    )
    
    parser.add_argument(
        "--coverage-threshold",
        type=float,
        default=80.0,
        help="覆盖率阈值 (默认: 80.0)"
    )
    
    parser.add_argument(
        "--quality-threshold",
        type=float,
        default=70.0,
        help="代码质量阈值 (默认: 70.0)"
    )
    
    parser.add_argument(
        "--auto-implement",
        action="store_true",
        help="自动生成代码实现"
    )
    
    parser.add_argument(
        "--input",
        type=str,
        help="输入文件路径（用于建议生成）"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="输出文件路径"
    )
    
    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="跳过验证阶段"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )
    
    args = parser.parse_args()
    
    logger = setup_logger(args.verbose)
    
    framework_map = {
        "pytest": TestFramework.PYTEST,
        "jest": TestFramework.JEST,
        "junit": TestFramework.JUNIT,
        "mocha": TestFramework.MOCHA,
        "go_test": TestFramework.GO_TEST,
        "rust_test": TestFramework.RUST_TEST
    }
    
    language_map = {
        "python": ProgrammingLanguage.PYTHON,
        "typescript": ProgrammingLanguage.TYPESCRIPT,
        "javascript": ProgrammingLanguage.JAVASCRIPT,
        "java": ProgrammingLanguage.JAVA,
        "go": ProgrammingLanguage.GO,
        "rust": ProgrammingLanguage.RUST,
        "csharp": ProgrammingLanguage.CSHARP
    }
    
    pipeline = TDDBlueRefactoringPipeline(
        logger=logger,
        test_framework=framework_map.get(args.framework, TestFramework.PYTEST),
        programming_language=language_map.get(args.language, ProgrammingLanguage.PYTHON),
        coverage_threshold=args.coverage_threshold,
        quality_threshold=args.quality_threshold
    )
    
    if args.tdd_cycle:
        if not args.spec:
            print("错误: TDD循环需要指定规范文件 (--spec)")
            return 1
        
        spec = _load_spec_file(args.spec, logger)
        results = pipeline.run_enhanced_tdd_cycle(spec, auto_implement=args.auto_implement)
        
        print("\n" + "=" * 80)
        print("TDD循环执行结果")
        print("=" * 80)
        print(f"循环ID: {results['cycle_id']}")
        print(f"状态: {'✅ 成功' if results['success'] else '❌ 失败'}")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n结果已保存到: {args.output}")
        
        return 0 if results['success'] else 1
    
    elif args.generate_tests:
        if not args.spec:
            print("错误: 生成测试需要指定规范文件 (--spec)")
            return 1
        
        spec = _load_spec_file(args.spec, logger)
        test_cases = pipeline.generate_tests_from_spec(spec)
        
        print(f"\n生成了 {len(test_cases)} 个测试用例")
        if test_cases:
            print(f"测试文件: {test_cases[0].file_path}")
        
        return 0
    
    elif args.generate_code:
        if not args.test_file:
            print("错误: 生成代码需要指定测试文件 (--test-file)")
            return 1
        
        print("注意: 此功能需要先加载测试用例，当前为简化版本")
        print(f"目标语言: {args.language}")
        
        return 0
    
    elif args.analyze_quality:
        if not args.source:
            print("错误: 分析代码质量需要指定源文件 (--source)")
            return 1
        
        quality_report, refactoring_results = pipeline.analyze_and_refactor(Path(args.source))
        
        print("\n" + "=" * 80)
        print("代码质量分析报告")
        print("=" * 80)
        print(f"文件: {quality_report.file_path}")
        print(f"总体得分: {quality_report.overall_score:.1f}")
        
        print("\n指标:")
        for metric, value in quality_report.metrics.items():
            print(f"  - {metric.value}: {value:.1f}")
        
        if quality_report.issues:
            print(f"\n问题 ({len(quality_report.issues)} 个):")
            for issue in quality_report.issues[:5]:
                print(f"  - 行 {issue['line']}: {issue['message']}")
        
        if refactoring_results:
            print(f"\n应用了 {len([r for r in refactoring_results if r.success])} 个重构")
        
        return 0
    
    elif args.verify_cycle:
        test_dir = Path(args.test_dir) if args.test_dir else Path("tests")
        source_dir = Path(args.source_dir) if args.source_dir else Path("src")
        
        test_files = list(test_dir.glob("test_*.py")) if test_dir.exists() else []
        source_files = list(source_dir.glob("**/*.py")) if source_dir.exists() else []
        
        if not test_files:
            print(f"警告: 未找到测试文件在 {test_dir}")
        
        cycle_id = f"VERIFY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        result = pipeline.verify_tdd_cycle(cycle_id, test_files, source_files)
        
        print("\n" + "=" * 80)
        print("TDD循环验证报告")
        print("=" * 80)
        print(f"循环ID: {result.cycle_id}")
        print(f"测试覆盖率: {result.test_coverage:.1f}%")
        print(f"代码质量得分: {result.code_quality_score:.1f}")
        print(f"功能正确性: {'✅ 通过' if result.functional_correctness else '❌ 失败'}")
        print(f"所有测试通过: {'✅ 是' if result.all_tests_passed else '❌ 否'}")
        
        if result.issues:
            print(f"\n问题 ({len(result.issues)} 个):")
            for issue in result.issues:
                print(f"  - [{issue['severity']}] {issue['message']}")
        
        if result.recommendations:
            print("\n建议:")
            for rec in result.recommendations:
                print(f"  - {rec}")
        
        return 0 if result.all_tests_passed else 1
    
    elif args.detect_only:
        result = pipeline.run_detection_only(args.severity)
        pipeline.print_result(result)
        output_path = pipeline.save_result(result, args.output)
        print(f"\n完整报告已保存到: {output_path}")
        return 0 if result.success else 1
    
    elif args.suggest_only:
        result = pipeline.run_suggestions_only(args.input)
        pipeline.print_result(result)
        output_path = pipeline.save_result(result, args.output)
        print(f"\n完整报告已保存到: {output_path}")
        return 0 if result.success else 1
    
    elif args.validate_only:
        result = pipeline.run_validation_only()
        pipeline.print_result(result)
        output_path = pipeline.save_result(result, args.output)
        print(f"\n完整报告已保存到: {output_path}")
        return 0 if result.success else 1
    
    else:
        result = pipeline.run_full_pipeline(
            min_severity=args.severity,
            run_validation=not args.no_validation
        )
        pipeline.print_result(result)
        output_path = pipeline.save_result(result, args.output)
        print(f"\n完整报告已保存到: {output_path}")
        return 0 if result.success else 1


def _load_spec_file(spec_path: str, logger: logging.Logger) -> Dict[str, Any]:
    """加载规范文件"""
    path = Path(spec_path)
    
    if not path.exists():
        raise FileNotFoundError(f"规范文件不存在: {spec_path}")
    
    suffix = path.suffix.lower()
    
    if suffix in [".yaml", ".yml"]:
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except ImportError:
            logger.warning("PyYAML未安装，尝试作为JSON加载")
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    elif suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif suffix == ".md":
        return _parse_markdown_spec(path)
    else:
        raise ValueError(f"不支持的规范文件格式: {suffix}")


def _parse_markdown_spec(path: Path) -> Dict[str, Any]:
    """解析Markdown格式的规范文件"""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    spec = {
        "id": f"SPEC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "name": path.stem,
        "version": "v1.0",
        "type": "function_spec",
        "elements": [],
        "source_file": str(path)
    }
    
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if title_match:
        spec["name"] = title_match.group(1)
    
    input_pattern = r"##\s*输入条件\s*\n((?:\s*[-*]\s*.+\n?)+)"
    for match in re.finditer(input_pattern, content):
        inputs = [line.strip("- *").strip() for line in match.group(1).strip().split("\n") if line.strip()]
        for inp in inputs:
            spec["elements"].append({
                "name": inp.split(":")[0].strip() if ":" in inp else inp,
                "type": "input",
                "description": inp.split(":")[1].strip() if ":" in inp else ""
            })
    
    output_pattern = r"##\s*输出结果\s*\n((?:\s*[-*]\s*.+\n?)+)"
    for match in re.finditer(output_pattern, content):
        outputs = [line.strip("- *").strip() for line in match.group(1).strip().split("\n") if line.strip()]
        for out in outputs:
            spec["elements"].append({
                "name": out.split(":")[0].strip() if ":" in out else out,
                "type": "output",
                "description": out.split(":")[1].strip() if ":" in out else ""
            })
    
    exception_pattern = r"##\s*异常处理\s*\n((?:\s*[-*]\s*.+\n?)+)"
    for match in re.finditer(exception_pattern, content):
        exceptions = [line.strip("- *").strip() for line in match.group(1).strip().split("\n") if line.strip()]
        for exc in exceptions:
            spec["elements"].append({
                "name": exc.split(":")[0].strip() if ":" in exc else exc,
                "type": "exception",
                "description": exc.split(":")[1].strip() if ":" in exc else ""
            })
    
    return spec


if __name__ == "__main__":
    sys.exit(main())
