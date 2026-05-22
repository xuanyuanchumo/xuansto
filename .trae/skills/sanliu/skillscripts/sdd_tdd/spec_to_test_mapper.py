#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规范到测试用例的自动映射器

实现从SDD规范自动生成测试用例的功能：
1. 规范元素到测试用例的智能映射
2. 支持多种测试策略（正向、逆向、边界、异常）
3. 支持多种测试框架（pytest、jest、junit等）
4. 测试用例模板定制
5. 测试覆盖率分析
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from .enhanced_spec_parser import (
        SDDSpecification,
        SpecAttribute,
        SpecEndpoint,
        SpecScenario,
        SpecConstraint,
        SpecBusinessRule,
        SpecType,
    )
except ImportError:
    from enhanced_spec_parser import (
        SDDSpecification,
        SpecAttribute,
        SpecEndpoint,
        SpecScenario,
        SpecConstraint,
        SpecBusinessRule,
        SpecType,
    )


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    BOUNDARY = "boundary"
    EXCEPTION = "exception"
    PERFORMANCE = "performance"
    SECURITY = "security"
    FUNCTIONAL = "functional"
    ACCEPTANCE = "acceptance"
    E2E = "e2e"
    CONDITIONAL = "conditional"
    RECOVERY = "recovery"


class TestFramework(Enum):
    PYTEST = "pytest"
    JEST = "jest"
    JUNIT = "junit"
    MOCHA = "mocha"
    GO_TEST = "go_test"
    RUST_TEST = "rust_test"


class TestGenerationStrategy(Enum):
    EXHAUSTIVE = "exhaustive"
    SAMPLING = "sampling"
    PRIORITY_BASED = "priority_based"
    COVERAGE_DRIVEN = "coverage_driven"


@dataclass
class TestCaseStep:
    step_number: int
    action: str
    expected_result: str
    test_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCaseMapping:
    id: str
    name: str
    spec_id: str
    spec_element: str
    spec_element_type: str
    test_type: TestType
    priority: str
    description: str = ""
    preconditions: List[str] = field(default_factory=list)
    test_steps: List[TestCaseStep] = field(default_factory=list)
    expected_results: List[str] = field(default_factory=list)
    test_data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    coverage_items: List[str] = field(default_factory=list)
    generated_code: str = ""
    file_path: str = ""


@dataclass
class TestGenerationResult:
    spec_id: str
    spec_name: str
    test_cases: List[TestCaseMapping] = field(default_factory=list)
    coverage_report: Dict[str, Any] = field(default_factory=dict)
    generation_metadata: Dict[str, Any] = field(default_factory=dict)


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
''',
            "e2e": '''import pytest
from playwright.sync_api import Page, expect

def test_{test_name}_e2e(page: Page):
    """E2E测试: {description}"""
    # Arrange
    {arrange}
    
    # Act
    {act}
    
    # Assert
    {assert_}
''',
            "performance": '''import pytest
import time

def test_{test_name}_performance():
    """性能测试: {description}"""
    # Arrange
    {arrange}
    
    # Act
    start_time = time.time()
    {act}
    elapsed_time = time.time() - start_time
    
    # Assert
    assert elapsed_time < {threshold}, f"响应时间 {elapsed_time}ms 超过阈值 {threshold}ms"
''',
            "security": '''import pytest

def test_{test_name}_security():
    """安全测试: {description}"""
    # Arrange
    {arrange}
    
    # Act
    {act}
    
    # Assert
    {assert_}
''',
            "conditional": '''import pytest

def test_{test_name}_conditional():
    """条件分支测试: {description}"""
    # Arrange
    {arrange}
    
    # Act & Assert
    {act}
''',
            "recovery": '''import pytest

def test_{test_name}_recovery():
    """恢复测试: {description}"""
    # Arrange
    {arrange}
    
    # Act - 触发异常
    {act}
    
    # Assert - 验证恢复行为
    {assert_}
''',
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
            "e2e": '''describe('{suite_name} E2E', () => {{
    test('{test_name}', async () => {{
        // Arrange
        {arrange}
        
        // Act
        {act}
        
        // Assert
        {assert_}
    }});
}});
''',
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
        },
    }
    
    @classmethod
    def get_template(cls, framework: TestFramework, test_type: str) -> str:
        return cls.TEMPLATES.get(framework, {}).get(test_type, cls.TEMPLATES[TestFramework.PYTEST]["unit"])
    
    @classmethod
    def register_template(cls, framework: TestFramework, test_type: str, template: str):
        if framework not in cls.TEMPLATES:
            cls.TEMPLATES[framework] = {}
        cls.TEMPLATES[framework][test_type] = template


class SpecToTestMapper:
    """规范到测试用例的映射器"""
    
    MAPPING_RULES = {
        SpecType.ENTITY: {
            "min_test_cases": 3,
            "must_cover": ["create", "read", "update", "delete", "validation"],
            "test_types": [TestType.UNIT, TestType.BOUNDARY, TestType.EXCEPTION],
        },
        SpecType.INTERFACE: {
            "min_test_cases": 5,
            "must_cover": ["valid_request", "invalid_request", "unauthorized", "forbidden", "error_response"],
            "test_types": [TestType.INTEGRATION, TestType.SECURITY, TestType.EXCEPTION],
        },
        SpecType.API: {
            "min_test_cases": 5,
            "must_cover": ["valid_request", "invalid_request", "unauthorized", "forbidden", "error_response"],
            "test_types": [TestType.INTEGRATION, TestType.SECURITY, TestType.EXCEPTION],
        },
        SpecType.BUSINESS_RULE: {
            "min_test_cases": 2,
            "must_cover": ["rule_triggered", "rule_not_triggered"],
            "test_types": [TestType.UNIT, TestType.FUNCTIONAL],
        },
        SpecType.ACCEPTANCE: {
            "min_test_cases": 1,
            "must_cover": ["scenario_validation"],
            "test_types": [TestType.ACCEPTANCE, TestType.FUNCTIONAL],
        },
        SpecType.FUNCTION: {
            "min_test_cases": 3,
            "must_cover": ["happy_path", "error_path", "boundary"],
            "test_types": [TestType.UNIT, TestType.BOUNDARY, TestType.EXCEPTION],
        },
    }
    
    def __init__(
        self,
        framework: TestFramework = TestFramework.PYTEST,
        strategy: TestGenerationStrategy = TestGenerationStrategy.EXHAUSTIVE,
        output_dir: Optional[Path] = None,
    ):
        self.framework = framework
        self.strategy = strategy
        self.output_dir = output_dir or Path("tests/generated")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.template_manager = TestTemplateManager()
        self._test_counter = 0
    
    def generate_tests_from_spec(self, spec: SDDSpecification) -> TestGenerationResult:
        """从规范生成测试用例"""
        result = TestGenerationResult(
            spec_id=spec.metadata.id,
            spec_name=spec.metadata.name,
        )
        
        rules = self.MAPPING_RULES.get(spec.kind, self.MAPPING_RULES[SpecType.FUNCTION])
        
        for attr in spec.attributes:
            tests = self._generate_attribute_tests(spec, attr, rules)
            result.test_cases.extend(tests)
        
        for endpoint in spec.endpoints:
            tests = self._generate_endpoint_tests(spec, endpoint, rules)
            result.test_cases.extend(tests)
        
        for scenario in spec.scenarios:
            tests = self._generate_scenario_tests(spec, scenario, rules)
            result.test_cases.extend(tests)
        
        for constraint in spec.constraints:
            tests = self._generate_constraint_tests(spec, constraint, rules)
            result.test_cases.extend(tests)
        
        for rule in spec.business_rules:
            tests = self._generate_business_rule_tests(spec, rule, rules)
            result.test_cases.extend(tests)
        
        for branch in spec.conditional_branches:
            tests = self._generate_conditional_branch_tests(spec, branch, rules)
            result.test_cases.extend(tests)
        
        for handler in spec.exception_handlers:
            tests = self._generate_exception_handler_tests(spec, handler, rules)
            result.test_cases.extend(tests)
        
        for perf_constraint in spec.performance_constraints:
            tests = self._generate_performance_tests(spec, perf_constraint, rules)
            result.test_cases.extend(tests)
        
        for sec_constraint in spec.security_constraints:
            tests = self._generate_security_tests(spec, sec_constraint, rules)
            result.test_cases.extend(tests)
        
        e2e_tests = self._generate_e2e_tests(spec, rules)
        result.test_cases.extend(e2e_tests)
        
        result.coverage_report = self._generate_coverage_report(spec, result.test_cases)
        result.generation_metadata = {
            "generated_at": datetime.now().isoformat(),
            "framework": self.framework.value,
            "strategy": self.strategy.value,
            "total_test_cases": len(result.test_cases),
        }
        
        return result
    
    def _generate_attribute_tests(
        self,
        spec: SDDSpecification,
        attr: SpecAttribute,
        rules: Dict[str, Any]
    ) -> List[TestCaseMapping]:
        tests = []
        
        if attr.required:
            tests.append(self._create_required_test(spec, attr))
        
        if attr.constraints:
            tests.extend(self._create_constraint_tests(spec, attr))
        
        if attr.type == "enum" and attr.enum_values:
            tests.append(self._create_enum_test(spec, attr))
        
        if attr.unique:
            tests.append(self._create_unique_test(spec, attr))
        
        if attr.validation_rules:
            tests.extend(self._create_validation_tests(spec, attr))
        
        return tests
    
    def _create_required_test(self, spec: SDDSpecification, attr: SpecAttribute) -> TestCaseMapping:
        self._test_counter += 1
        
        test_case = TestCaseMapping(
            id=f"TC-{spec.metadata.id}-ATTR-{self._test_counter:03d}",
            name=f"test_{attr.name}_required_validation",
            spec_id=spec.metadata.id,
            spec_element=attr.name,
            spec_element_type="attribute",
            test_type=TestType.EXCEPTION,
            priority="high",
            description=f"验证属性 {attr.name} 必填约束",
            preconditions=["系统就绪"],
            test_steps=[
                TestCaseStep(1, f"构造不包含 {attr.name} 的数据", "数据构造完成"),
                TestCaseStep(2, "提交数据", "提交执行"),
                TestCaseStep(3, "验证返回必填错误", "返回必填字段错误"),
            ],
            expected_results=[f"返回 {attr.name} 必填错误"],
            test_data={"attribute": attr.name, "value": None},
            tags=["Attribute", "Validation", "Required"],
            coverage_items=[f"{attr.name}-required"],
        )
        
        test_case.generated_code = self._generate_test_code(test_case)
        return test_case
    
    def _create_constraint_tests(self, spec: SDDSpecification, attr: SpecAttribute) -> List[TestCaseMapping]:
        tests = []
        
        for constraint_name, constraint_value in attr.constraints.items():
            self._test_counter += 1
            
            test_type = TestType.BOUNDARY if constraint_name in ["minLength", "maxLength", "min", "max"] else TestType.EXCEPTION
            
            test_case = TestCaseMapping(
                id=f"TC-{spec.metadata.id}-ATTR-{self._test_counter:03d}",
                name=f"test_{attr.name}_{constraint_name}_constraint",
                spec_id=spec.metadata.id,
                spec_element=attr.name,
                spec_element_type="attribute",
                test_type=test_type,
                priority="medium",
                description=f"验证属性 {attr.name} 的 {constraint_name} 约束: {constraint_value}",
                preconditions=["系统就绪"],
                test_steps=[
                    TestCaseStep(1, f"构造违反{constraint_name}约束的数据", "数据构造完成"),
                    TestCaseStep(2, "提交数据", "提交执行"),
                    TestCaseStep(3, f"验证返回{constraint_name}约束错误", "返回约束违反错误"),
                ],
                expected_results=[f"返回 {constraint_name} 约束错误"],
                test_data={"attribute": attr.name, "constraint": constraint_name, "value": constraint_value},
                tags=["Attribute", "Constraint", constraint_name],
                coverage_items=[f"{attr.name}-{constraint_name}"],
            )
            
            test_case.generated_code = self._generate_test_code(test_case)
            tests.append(test_case)
        
        return tests
    
    def _create_enum_test(self, spec: SDDSpecification, attr: SpecAttribute) -> TestCaseMapping:
        self._test_counter += 1
        
        test_case = TestCaseMapping(
            id=f"TC-{spec.metadata.id}-ATTR-{self._test_counter:03d}",
            name=f"test_{attr.name}_enum_validation",
            spec_id=spec.metadata.id,
            spec_element=attr.name,
            spec_element_type="attribute",
            test_type=TestType.EXCEPTION,
            priority="medium",
            description=f"验证属性 {attr.name} 枚举值: {attr.enum_values}",
            preconditions=["系统就绪"],
            test_steps=[
                TestCaseStep(1, "构造无效枚举值", "数据构造完成"),
                TestCaseStep(2, "提交数据", "提交执行"),
                TestCaseStep(3, "验证返回枚举值错误", "返回无效枚举值错误"),
            ],
            expected_results=["返回无效枚举值错误"],
            test_data={"attribute": attr.name, "valid_values": attr.enum_values},
            tags=["Attribute", "Enum"],
            coverage_items=[f"{attr.name}-enum"],
        )
        
        test_case.generated_code = self._generate_test_code(test_case)
        return test_case
    
    def _create_unique_test(self, spec: SDDSpecification, attr: SpecAttribute) -> TestCaseMapping:
        self._test_counter += 1
        
        test_case = TestCaseMapping(
            id=f"TC-{spec.metadata.id}-ATTR-{self._test_counter:03d}",
            name=f"test_{attr.name}_unique_constraint",
            spec_id=spec.metadata.id,
            spec_element=attr.name,
            spec_element_type="attribute",
            test_type=TestType.EXCEPTION,
            priority="high",
            description=f"验证属性 {attr.name} 唯一性约束",
            preconditions=["系统就绪", "已存在一条记录"],
            test_steps=[
                TestCaseStep(1, "构造重复的{attr.name}值", "数据构造完成"),
                TestCaseStep(2, "提交数据", "提交执行"),
                TestCaseStep(3, "验证返回唯一性错误", "返回重复值错误"),
            ],
            expected_results=["返回唯一性约束错误"],
            test_data={"attribute": attr.name},
            tags=["Attribute", "Unique"],
            coverage_items=[f"{attr.name}-unique"],
        )
        
        test_case.generated_code = self._generate_test_code(test_case)
        return test_case
    
    def _create_validation_tests(self, spec: SDDSpecification, attr: SpecAttribute) -> List[TestCaseMapping]:
        tests = []
        
        for idx, rule in enumerate(attr.validation_rules):
            self._test_counter += 1
            
            rule_type = rule.get("type", "custom")
            
            test_case = TestCaseMapping(
                id=f"TC-{spec.metadata.id}-ATTR-{self._test_counter:03d}",
                name=f"test_{attr.name}_validation_rule_{idx+1}",
                spec_id=spec.metadata.id,
                spec_element=attr.name,
                spec_element_type="attribute",
                test_type=TestType.UNIT,
                priority="medium",
                description=f"验证属性 {attr.name} 的验证规则: {rule_type}",
                preconditions=["系统就绪"],
                test_steps=[
                    TestCaseStep(1, f"构造违反{rule_type}规则的数据", "数据构造完成"),
                    TestCaseStep(2, "提交数据", "提交执行"),
                    TestCaseStep(3, "验证返回验证错误", "返回验证失败"),
                ],
                expected_results=["验证规则生效"],
                test_data={"attribute": attr.name, "rule": rule},
                tags=["Attribute", "Validation", rule_type],
                coverage_items=[f"{attr.name}-validation-{idx+1}"],
            )
            
            test_case.generated_code = self._generate_test_code(test_case)
            tests.append(test_case)
        
        return tests
    
    def _generate_endpoint_tests(
        self,
        spec: SDDSpecification,
        endpoint: SpecEndpoint,
        rules: Dict[str, Any]
    ) -> List[TestCaseMapping]:
        tests = []
        
        tests.append(self._create_endpoint_success_test(spec, endpoint))
        
        if endpoint.authentication:
            tests.append(self._create_endpoint_auth_test(spec, endpoint))
        
        for error in endpoint.errors:
            tests.append(self._create_endpoint_error_test(spec, endpoint, error))
        
        return tests
    
    def _create_endpoint_success_test(self, spec: SDDSpecification, endpoint: SpecEndpoint) -> TestCaseMapping:
        self._test_counter += 1
        
        test_case = TestCaseMapping(
            id=f"TC-{spec.metadata.id}-API-{self._test_counter:03d}",
            name=f"test_{endpoint.name}_success",
            spec_id=spec.metadata.id,
            spec_element=endpoint.name,
            spec_element_type="endpoint",
            test_type=TestType.INTEGRATION,
            priority="high",
            description=f"测试 {endpoint.method} {endpoint.path} 正常调用",
            preconditions=["系统正常运行"] + (["用户已认证"] if endpoint.authentication else []),
            test_steps=[
                TestCaseStep(1, "构造请求参数", "参数构造完成"),
                TestCaseStep(2, f"发送 {endpoint.method} 请求到 {endpoint.path}", "请求发送成功"),
                TestCaseStep(3, "验证响应状态码和内容", "响应符合预期"),
            ],
            expected_results=["响应状态码正确", "响应数据结构正确"],
            test_data={"method": endpoint.method, "path": endpoint.path},
            tags=["API", endpoint.method],
            coverage_items=[endpoint.name],
        )
        
        test_case.generated_code = self._generate_test_code(test_case)
        return test_case
    
    def _create_endpoint_auth_test(self, spec: SDDSpecification, endpoint: SpecEndpoint) -> TestCaseMapping:
        self._test_counter += 1
        
        test_case = TestCaseMapping(
            id=f"TC-{spec.metadata.id}-API-{self._test_counter:03d}",
            name=f"test_{endpoint.name}_unauthorized",
            spec_id=spec.metadata.id,
            spec_element=endpoint.name,
            spec_element_type="endpoint",
            test_type=TestType.SECURITY,
            priority="critical",
            description=f"测试 {endpoint.method} {endpoint.path} 未认证访问被拒绝",
            preconditions=["系统正常运行", "用户未认证"],
            test_steps=[
                TestCaseStep(1, "构造无认证信息的请求", "请求构造完成"),
                TestCaseStep(2, f"发送 {endpoint.method} 请求到 {endpoint.path}", "请求发送成功"),
                TestCaseStep(3, "验证返回401未授权", "返回401状态码"),
            ],
            expected_results=["返回401 Unauthorized"],
            test_data={"method": endpoint.method, "path": endpoint.path},
            tags=["API", "Security"],
            coverage_items=[f"{endpoint.name}-auth"],
        )
        
        test_case.generated_code = self._generate_test_code(test_case)
        return test_case
    
    def _create_endpoint_error_test(
        self,
        spec: SDDSpecification,
        endpoint: SpecEndpoint,
        error: Dict[str, Any]
    ) -> TestCaseMapping:
        self._test_counter += 1
        
        error_code = error.get("code", error.get("status", "500"))
        
        test_case = TestCaseMapping(
            id=f"TC-{spec.metadata.id}-API-{self._test_counter:03d}",
            name=f"test_{endpoint.name}_error_{error_code}",
            spec_id=spec.metadata.id,
            spec_element=endpoint.name,
            spec_element_type="endpoint",
            test_type=TestType.EXCEPTION,
            priority="high",
            description=f"测试 {endpoint.method} {endpoint.path} 错误场景: {error.get('description', error.get('message', ''))}",
            preconditions=["系统正常运行"],
            test_steps=[
                TestCaseStep(1, "构造触发错误的请求", "请求构造完成"),
                TestCaseStep(2, f"发送 {endpoint.method} 请求", "请求发送成功"),
                TestCaseStep(3, f"验证返回错误码 {error_code}", f"返回 {error_code} 错误"),
            ],
            expected_results=[f"返回错误码 {error_code}", "错误信息格式正确"],
            test_data={"method": endpoint.method, "path": endpoint.path, "trigger_error": error},
            tags=["API", "Error"],
            coverage_items=[f"{endpoint.name}-error-{error_code}"],
        )
        
        test_case.generated_code = self._generate_test_code(test_case)
        return test_case
    
    def _generate_scenario_tests(
        self,
        spec: SDDSpecification,
        scenario: SpecScenario,
        rules: Dict[str, Any]
    ) -> List[TestCaseMapping]:
        tests = []
        
        test_type = self._determine_test_type(scenario)
        priority = self._determine_priority(scenario)
        
        self._test_counter += 1
        
        test_case = TestCaseMapping(
            id=f"TC-{spec.metadata.id}-SCENARIO-{self._test_counter:03d}",
            name=f"test_{scenario.name.lower().replace(' ', '_')}",
            spec_id=spec.metadata.id,
            spec_element=scenario.name,
            spec_element_type="scenario",
            test_type=test_type,
            priority=priority,
            description=f"测试场景: {scenario.given} -> {scenario.when} -> {scenario.then}",
            preconditions=scenario.preconditions if scenario.preconditions else [scenario.given] if scenario.given else [],
            test_steps=[
                TestCaseStep(1, scenario.given, "前置条件满足"),
                TestCaseStep(2, scenario.when, "操作执行完成"),
                TestCaseStep(3, f"验证结果: {scenario.then}", scenario.then),
            ],
            expected_results=[scenario.then],
            test_data=scenario.test_data,
            tags=["Scenario", test_type.value] + scenario.tags,
            coverage_items=[scenario.name],
        )
        
        test_case.generated_code = self._generate_test_code(test_case)
        tests.append(test_case)
        
        return tests
    
    def _generate_constraint_tests(
        self,
        spec: SDDSpecification,
        constraint: SpecConstraint,
        rules: Dict[str, Any]
    ) -> List[TestCaseMapping]:
        tests = []
        
        self._test_counter += 1
        
        test_case = TestCaseMapping(
            id=f"TC-{spec.metadata.id}-CONST-{self._test_counter:03d}",
            name=f"test_constraint_{constraint.name.lower().replace(' ', '_')}",
            spec_id=spec.metadata.id,
            spec_element=constraint.name,
            spec_element_type="constraint",
            test_type=TestType.EXCEPTION,
            priority="high" if constraint.severity == "error" else "medium",
            description=f"验证约束: {constraint.description}",
            preconditions=["系统就绪"],
            test_steps=[
                TestCaseStep(1, "构造违反约束的数据", "数据构造完成"),
                TestCaseStep(2, "执行操作", "操作执行"),
                TestCaseStep(3, "验证约束被触发", "约束验证失败"),
            ],
            expected_results=[f"约束 {constraint.name} 被正确验证"],
            test_data={"constraint": constraint.name, "rule": constraint.rule},
            tags=["Constraint", constraint.type],
            coverage_items=[constraint.name],
        )
        
        test_case.generated_code = self._generate_test_code(test_case)
        tests.append(test_case)
        
        return tests
    
    def _generate_business_rule_tests(
        self,
        spec: SDDSpecification,
        rule: SpecBusinessRule,
        rules: Dict[str, Any]
    ) -> List[TestCaseMapping]:
        tests = []
        
        self._test_counter += 1
        
        test_case = TestCaseMapping(
            id=f"TC-{spec.metadata.id}-RULE-{self._test_counter:03d}",
            name=f"test_rule_{rule.id.lower()}",
            spec_id=spec.metadata.id,
            spec_element=rule.name,
            spec_element_type="business_rule",
            test_type=TestType.FUNCTIONAL,
            priority="high" if rule.priority == 1 else "medium",
            description=f"验证业务规则: {rule.description}",
            preconditions=["系统就绪"],
            test_steps=[
                TestCaseStep(1, f"准备条件: {rule.condition}", "条件准备完成"),
                TestCaseStep(2, "执行操作", "操作执行"),
                TestCaseStep(3, f"验证动作: {rule.action}", "规则正确触发"),
            ],
            expected_results=[f"业务规则 {rule.name} 正确执行"],
            test_data={"rule_id": rule.id, "condition": rule.condition, "action": rule.action},
            tags=["BusinessRule"] + rule.tags,
            coverage_items=[rule.id],
        )
        
        test_case.generated_code = self._generate_test_code(test_case)
        tests.append(test_case)
        
        return tests
    
    def _generate_conditional_branch_tests(
        self,
        spec: SDDSpecification,
        branch,
        rules: Dict[str, Any]
    ) -> List[TestCaseMapping]:
        tests = []
        
        self._test_counter += 1
        
        test_case = TestCaseMapping(
            id=f"TC-{spec.metadata.id}-COND-{self._test_counter:03d}",
            name=f"test_conditional_{branch.condition[:30].lower().replace(' ', '_')}",
            spec_id=spec.metadata.id,
            spec_element=branch.condition,
            spec_element_type="conditional_branch",
            test_type=TestType.CONDITIONAL,
            priority="high",
            description=f"验证条件分支: {branch.description or branch.condition}",
            preconditions=["系统就绪"],
            test_steps=[
                TestCaseStep(1, f"设置条件: {branch.condition}", "条件设置完成"),
                TestCaseStep(2, "执行操作", "操作执行"),
                TestCaseStep(3, f"验证动作: {', '.join(branch.actions)}", "分支正确执行"),
            ],
            expected_results=branch.actions,
            test_data={"condition": branch.condition, "actions": branch.actions},
            tags=["Conditional", "Branch"],
            coverage_items=[branch.condition],
        )
        
        test_case.generated_code = self._generate_test_code(test_case)
        tests.append(test_case)
        
        if branch.else_branch:
            self._test_counter += 1
            else_test = TestCaseMapping(
                id=f"TC-{spec.metadata.id}-COND-{self._test_counter:03d}",
                name=f"test_conditional_else_{branch.condition[:20].lower().replace(' ', '_')}",
                spec_id=spec.metadata.id,
                spec_element=f"else: {branch.condition}",
                spec_element_type="conditional_branch",
                test_type=TestType.CONDITIONAL,
                priority="high",
                description=f"验证条件分支的Else: {branch.else_branch.description or branch.else_branch.condition}",
                preconditions=["系统就绪"],
                test_steps=[
                    TestCaseStep(1, f"设置条件不满足: {branch.condition}", "条件设置完成"),
                    TestCaseStep(2, "执行操作", "操作执行"),
                    TestCaseStep(3, f"验证Else动作: {', '.join(branch.else_branch.actions)}", "Else分支正确执行"),
                ],
                expected_results=branch.else_branch.actions,
                test_data={"condition": f"NOT {branch.condition}", "actions": branch.else_branch.actions},
                tags=["Conditional", "Else"],
                coverage_items=[f"else-{branch.condition}"],
            )
            else_test.generated_code = self._generate_test_code(else_test)
            tests.append(else_test)
        
        for nested in branch.nested_conditions:
            nested_tests = self._generate_conditional_branch_tests(spec, nested, rules)
            tests.extend(nested_tests)
        
        return tests
    
    def _generate_exception_handler_tests(
        self,
        spec: SDDSpecification,
        handler,
        rules: Dict[str, Any]
    ) -> List[TestCaseMapping]:
        tests = []
        
        self._test_counter += 1
        
        test_case = TestCaseMapping(
            id=f"TC-{spec.metadata.id}-EXC-{self._test_counter:03d}",
            name=f"test_exception_{handler.exception_type.lower()}",
            spec_id=spec.metadata.id,
            spec_element=handler.exception_type,
            spec_element_type="exception_handler",
            test_type=TestType.RECOVERY,
            priority="critical",
            description=f"验证异常处理: {handler.description or handler.exception_type}",
            preconditions=["系统就绪"],
            test_steps=[
                TestCaseStep(1, f"触发异常: {handler.exception_type}", "异常触发"),
                TestCaseStep(2, f"验证HTTP状态码: {handler.http_status}", f"返回 {handler.http_status}"),
                TestCaseStep(3, f"验证错误码: {handler.error_code}", f"错误码 {handler.error_code}"),
                TestCaseStep(4, f"验证恢复行为: {handler.recovery_action}", "恢复执行"),
            ],
            expected_results=[f"HTTP状态码 {handler.http_status}", f"错误码 {handler.error_code}", handler.message],
            test_data={
                "exception_type": handler.exception_type,
                "http_status": handler.http_status,
                "error_code": handler.error_code,
                "recovery_action": handler.recovery_action,
                "retry_policy": handler.retry_policy,
            },
            tags=["Exception", "Recovery", handler.exception_type],
            coverage_items=[handler.exception_type],
        )
        
        test_case.generated_code = self._generate_test_code(test_case)
        tests.append(test_case)
        
        if handler.retry_policy:
            self._test_counter += 1
            retry_test = TestCaseMapping(
                id=f"TC-{spec.metadata.id}-RETRY-{self._test_counter:03d}",
                name=f"test_retry_{handler.exception_type.lower()}",
                spec_id=spec.metadata.id,
                spec_element=f"retry: {handler.exception_type}",
                spec_element_type="exception_handler",
                test_type=TestType.RECOVERY,
                priority="high",
                description=f"验证重试策略: {handler.exception_type}",
                preconditions=["系统就绪"],
                test_steps=[
                    TestCaseStep(1, f"触发可重试异常: {handler.exception_type}", "异常触发"),
                    TestCaseStep(2, f"验证重试策略: {handler.retry_policy}", "重试执行"),
                    TestCaseStep(3, "验证最终结果", "重试完成"),
                ],
                expected_results=["重试策略正确执行"],
                test_data={"retry_policy": handler.retry_policy},
                tags=["Exception", "Retry"],
                coverage_items=[f"retry-{handler.exception_type}"],
            )
            retry_test.generated_code = self._generate_test_code(retry_test)
            tests.append(retry_test)
        
        return tests
    
    def _generate_performance_tests(
        self,
        spec: SDDSpecification,
        perf_constraint,
        rules: Dict[str, Any]
    ) -> List[TestCaseMapping]:
        tests = []
        
        self._test_counter += 1
        
        test_case = TestCaseMapping(
            id=f"TC-{spec.metadata.id}-PERF-{self._test_counter:03d}",
            name=f"test_performance_{perf_constraint.name.lower().replace(' ', '_')}",
            spec_id=spec.metadata.id,
            spec_element=perf_constraint.name,
            spec_element_type="performance_constraint",
            test_type=TestType.PERFORMANCE,
            priority=perf_constraint.priority,
            description=f"验证性能约束: {perf_constraint.description or perf_constraint.name}",
            preconditions=["系统就绪"] + perf_constraint.conditions,
            test_steps=[
                TestCaseStep(1, f"准备测试环境", "环境准备完成"),
                TestCaseStep(2, f"执行 {perf_constraint.sample_size} 次请求", "请求执行完成"),
                TestCaseStep(3, f"验证 {perf_constraint.metric} <= {perf_constraint.threshold}{perf_constraint.unit}", "性能验证"),
            ],
            expected_results=[f"{perf_constraint.metric} <= {perf_constraint.threshold}{perf_constraint.unit}"],
            test_data={
                "metric": perf_constraint.metric,
                "threshold": perf_constraint.threshold,
                "unit": perf_constraint.unit,
                "sample_size": perf_constraint.sample_size,
                "measurement_method": perf_constraint.measurement_method,
                "percentiles": perf_constraint.percentiles,
            },
            tags=["Performance", perf_constraint.metric],
            coverage_items=[perf_constraint.name],
        )
        
        template = self.template_manager.get_template(self.framework, "performance")
        arrange = f"# 准备性能测试数据，样本数: {perf_constraint.sample_size}"
        act = f"# 执行操作并测量 {perf_constraint.metric}"
        assert_ = f"assert result <= {perf_constraint.threshold}, f'{perf_constraint.metric} 超过阈值'"
        
        test_case.generated_code = template.format(
            test_name=test_case.name,
            description=test_case.description,
            arrange=arrange,
            act=act,
            assert_=assert_,
            threshold=perf_constraint.threshold / 1000 if perf_constraint.unit == "ms" else perf_constraint.threshold,
        )
        tests.append(test_case)
        
        return tests
    
    def _generate_security_tests(
        self,
        spec: SDDSpecification,
        sec_constraint,
        rules: Dict[str, Any]
    ) -> List[TestCaseMapping]:
        tests = []
        
        if sec_constraint.authentication_required:
            self._test_counter += 1
            auth_test = TestCaseMapping(
                id=f"TC-{spec.metadata.id}-SEC-{self._test_counter:03d}",
                name=f"test_security_auth_{sec_constraint.name.lower().replace(' ', '_')}",
                spec_id=spec.metadata.id,
                spec_element=sec_constraint.name,
                spec_element_type="security_constraint",
                test_type=TestType.SECURITY,
                priority="critical",
                description=f"验证认证要求: {sec_constraint.description or sec_constraint.name}",
                preconditions=["系统就绪", "用户未认证"],
                test_steps=[
                    TestCaseStep(1, "构造无认证信息的请求", "请求构造完成"),
                    TestCaseStep(2, "发送请求", "请求发送"),
                    TestCaseStep(3, "验证返回401未授权", "返回401"),
                ],
                expected_results=["返回401 Unauthorized"],
                test_data={"auth_required": True},
                tags=["Security", "Authentication"],
                coverage_items=[f"{sec_constraint.name}-auth"],
            )
            auth_test.generated_code = self._generate_test_code(auth_test)
            tests.append(auth_test)
        
        if sec_constraint.authorization_roles:
            self._test_counter += 1
            role_test = TestCaseMapping(
                id=f"TC-{spec.metadata.id}-SEC-{self._test_counter:03d}",
                name=f"test_security_roles_{sec_constraint.name.lower().replace(' ', '_')}",
                spec_id=spec.metadata.id,
                spec_element=sec_constraint.name,
                spec_element_type="security_constraint",
                test_type=TestType.SECURITY,
                priority="critical",
                description=f"验证角色授权: {', '.join(sec_constraint.authorization_roles)}",
                preconditions=["系统就绪", "用户已认证但无权限"],
                test_steps=[
                    TestCaseStep(1, "构造无权限用户的请求", "请求构造完成"),
                    TestCaseStep(2, "发送请求", "请求发送"),
                    TestCaseStep(3, "验证返回403禁止访问", "返回403"),
                ],
                expected_results=["返回403 Forbidden"],
                test_data={"required_roles": sec_constraint.authorization_roles},
                tags=["Security", "Authorization"],
                coverage_items=[f"{sec_constraint.name}-roles"],
            )
            role_test.generated_code = self._generate_test_code(role_test)
            tests.append(role_test)
        
        if sec_constraint.rate_limit:
            self._test_counter += 1
            rate_test = TestCaseMapping(
                id=f"TC-{spec.metadata.id}-SEC-{self._test_counter:03d}",
                name=f"test_security_rate_limit_{sec_constraint.name.lower().replace(' ', '_')}",
                spec_id=spec.metadata.id,
                spec_element=sec_constraint.name,
                spec_element_type="security_constraint",
                test_type=TestType.SECURITY,
                priority="high",
                description=f"验证速率限制: {sec_constraint.rate_limit}次/{sec_constraint.rate_limit_window}秒",
                preconditions=["系统就绪"],
                test_steps=[
                    TestCaseStep(1, f"发送 {sec_constraint.rate_limit + 1} 次请求", "请求发送完成"),
                    TestCaseStep(2, "验证速率限制生效", "返回429"),
                ],
                expected_results=[f"第{sec_constraint.rate_limit + 1}次请求返回429 Too Many Requests"],
                test_data={"rate_limit": sec_constraint.rate_limit, "window": sec_constraint.rate_limit_window},
                tags=["Security", "RateLimit"],
                coverage_items=[f"{sec_constraint.name}-ratelimit"],
            )
            rate_test.generated_code = self._generate_test_code(rate_test)
            tests.append(rate_test)
        
        if sec_constraint.ip_whitelist or sec_constraint.ip_blacklist:
            self._test_counter += 1
            ip_test = TestCaseMapping(
                id=f"TC-{spec.metadata.id}-SEC-{self._test_counter:03d}",
                name=f"test_security_ip_filter_{sec_constraint.name.lower().replace(' ', '_')}",
                spec_id=spec.metadata.id,
                spec_element=sec_constraint.name,
                spec_element_type="security_constraint",
                test_type=TestType.SECURITY,
                priority="high",
                description=f"验证IP过滤: 白名单{len(sec_constraint.ip_whitelist)}个, 黑名单{len(sec_constraint.ip_blacklist)}个",
                preconditions=["系统就绪"],
                test_steps=[
                    TestCaseStep(1, "从非白名单IP发送请求", "请求发送"),
                    TestCaseStep(2, "验证请求被拒绝", "返回403"),
                ],
                expected_results=["非白名单IP请求被拒绝"],
                test_data={"whitelist": sec_constraint.ip_whitelist, "blacklist": sec_constraint.ip_blacklist},
                tags=["Security", "IPFilter"],
                coverage_items=[f"{sec_constraint.name}-ipfilter"],
            )
            ip_test.generated_code = self._generate_test_code(ip_test)
            tests.append(ip_test)
        
        return tests
    
    def _generate_e2e_tests(
        self,
        spec: SDDSpecification,
        rules: Dict[str, Any]
    ) -> List[TestCaseMapping]:
        tests = []
        
        if not spec.scenarios and not spec.endpoints:
            return tests
        
        for idx, scenario in enumerate(spec.scenarios):
            self._test_counter += 1
            
            test_case = TestCaseMapping(
                id=f"TC-{spec.metadata.id}-E2E-{self._test_counter:03d}",
                name=f"test_e2e_{scenario.name.lower().replace(' ', '_')}",
                spec_id=spec.metadata.id,
                spec_element=scenario.name,
                spec_element_type="e2e_scenario",
                test_type=TestType.E2E,
                priority="critical",
                description=f"E2E测试: {scenario.given} -> {scenario.when} -> {scenario.then}",
                preconditions=["系统部署完成", "浏览器就绪"] + scenario.preconditions,
                test_steps=[
                    TestCaseStep(1, f"Given: {scenario.given}", "前置条件满足"),
                    TestCaseStep(2, f"When: {scenario.when}", "操作执行完成"),
                    TestCaseStep(3, f"Then: {scenario.then}", "结果验证完成"),
                ],
                expected_results=[scenario.then],
                test_data=scenario.test_data,
                tags=["E2E", "Acceptance"] + scenario.tags,
                coverage_items=[f"e2e-{scenario.name}"],
            )
            
            template = self.template_manager.get_template(self.framework, "e2e")
            arrange = f"# 导航到页面并准备环境\n    page.goto('/')"
            act = f"# {scenario.when}"
            assert_ = f"# {scenario.then}"
            
            test_case.generated_code = template.format(
                test_name=test_case.name,
                description=test_case.description,
                arrange=arrange,
                act=act,
                assert_=assert_,
            )
            tests.append(test_case)
        
        if spec.endpoints:
            self._test_counter += 1
            
            flow_steps = []
            for endpoint in spec.endpoints[:5]:
                flow_steps.append(f"{endpoint.method} {endpoint.path}")
            
            test_case = TestCaseMapping(
                id=f"TC-{spec.metadata.id}-E2E-{self._test_counter:03d}",
                name=f"test_e2e_api_flow",
                spec_id=spec.metadata.id,
                spec_element="api_flow",
                spec_element_type="e2e_flow",
                test_type=TestType.E2E,
                priority="high",
                description=f"E2E API流程测试: {' -> '.join(flow_steps)}",
                preconditions=["系统部署完成", "API服务就绪"],
                test_steps=[
                    TestCaseStep(idx + 1, f"调用 {step}", "请求成功") 
                    for idx, step in enumerate(flow_steps)
                ],
                expected_results=["所有API调用成功"],
                test_data={"endpoints": [{"method": e.method, "path": e.path} for e in spec.endpoints[:5]]},
                tags=["E2E", "API"],
                coverage_items=["e2e-api-flow"],
            )
            
            test_case.generated_code = self._generate_test_code(test_case)
            tests.append(test_case)
        
        return tests
    
    def _determine_test_type(self, scenario: SpecScenario) -> TestType:
        then_lower = scenario.then.lower()
        
        if any(kw in then_lower for kw in ["异常", "错误", "失败", "error", "fail", "exception"]):
            return TestType.EXCEPTION
        elif any(kw in then_lower for kw in ["边界", "极限", "最大", "最小", "boundary", "limit", "max", "min"]):
            return TestType.BOUNDARY
        elif any(kw in then_lower for kw in ["安全", "权限", "认证", "security", "auth", "permission"]):
            return TestType.SECURITY
        elif any(kw in then_lower for kw in ["性能", "响应时间", "吞吐", "performance", "latency"]):
            return TestType.PERFORMANCE
        else:
            return TestType.FUNCTIONAL
    
    def _determine_priority(self, scenario: SpecScenario) -> str:
        if hasattr(scenario, 'priority'):
            return scenario.priority
        
        then_lower = scenario.then.lower()
        if any(kw in then_lower for kw in ["核心", "关键", "critical", "core"]):
            return "critical"
        elif any(kw in then_lower for kw in ["重要", "主要", "important", "major"]):
            return "high"
        elif any(kw in then_lower for kw in ["次要", "optional", "minor"]):
            return "low"
        return "medium"
    
    def _generate_test_code(self, test_case: TestCaseMapping) -> str:
        test_type_str = test_case.test_type.value
        if test_type_str == "exception":
            test_type_str = "exception"
        elif test_type_str == "boundary":
            test_type_str = "boundary"
        else:
            test_type_str = "unit"
        
        template = self.template_manager.get_template(self.framework, test_type_str)
        
        arrange = "\n    ".join([f"# {step.action}" for step in test_case.test_steps if "构造" in step.action or "准备" in step.action])
        act = "\n    ".join([f"# {step.action}" for step in test_case.test_steps if "执行" in step.action or "发送" in step.action or "提交" in step.action])
        assert_ = "\n    ".join([f"# {step.expected_result}" for step in test_case.test_steps if "验证" in step.action])
        
        code = template.format(
            test_name=test_case.name,
            description=test_case.description,
            arrange=arrange or "# 准备测试数据",
            act=act or "# 执行测试操作",
            assert_=assert_ or "assert True",
            exception_type="Exception",
            suite_name=test_case.id,
            parametrize_data="",
        )
        
        return code
    
    def _generate_coverage_report(
        self,
        spec: SDDSpecification,
        test_cases: List[TestCaseMapping]
    ) -> Dict[str, Any]:
        total_elements = (
            len(spec.attributes) +
            len(spec.endpoints) +
            len(spec.scenarios) +
            len(spec.constraints) +
            len(spec.business_rules)
        )
        
        covered_elements = set()
        for tc in test_cases:
            covered_elements.add(tc.spec_element)
        
        coverage_percentage = (len(covered_elements) / total_elements * 100) if total_elements > 0 else 0
        
        return {
            "total_elements": total_elements,
            "covered_elements": len(covered_elements),
            "coverage_percentage": round(coverage_percentage, 2),
            "by_type": {
                "attributes": {
                    "total": len(spec.attributes),
                    "covered": len([tc for tc in test_cases if tc.spec_element_type == "attribute"]),
                },
                "endpoints": {
                    "total": len(spec.endpoints),
                    "covered": len([tc for tc in test_cases if tc.spec_element_type == "endpoint"]),
                },
                "scenarios": {
                    "total": len(spec.scenarios),
                    "covered": len([tc for tc in test_cases if tc.spec_element_type == "scenario"]),
                },
                "constraints": {
                    "total": len(spec.constraints),
                    "covered": len([tc for tc in test_cases if tc.spec_element_type == "constraint"]),
                },
                "business_rules": {
                    "total": len(spec.business_rules),
                    "covered": len([tc for tc in test_cases if tc.spec_element_type == "business_rule"]),
                },
            },
        }
    
    def save_test_file(self, result: TestGenerationResult) -> Path:
        """保存测试文件"""
        extension = self._get_file_extension()
        filename = f"test_{result.spec_name.lower().replace(' ', '_')}.{extension}"
        filepath = self.output_dir / filename
        
        content = self._generate_file_header(result)
        
        for tc in result.test_cases:
            content += f"\n{tc.generated_code}\n"
            tc.file_path = str(filepath)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return filepath
    
    def _generate_file_header(self, result: TestGenerationResult) -> str:
        if self.framework == TestFramework.PYTEST:
            return f'''#!/usr/bin/env python3
"""自动生成的测试文件 - {result.spec_name}
规范ID: {result.spec_id}
生成时间: {result.generation_metadata.get('generated_at', datetime.now().isoformat())}
测试框架: pytest

注意: 此文件由SDD-TDD工具自动生成
"""
import pytest


'''
        elif self.framework == TestFramework.JEST:
            return f'''/**
 * 自动生成的测试文件 - {result.spec_name}
 * 规范ID: {result.spec_id}
 * 生成时间: {result.generation_metadata.get('generated_at', datetime.now().isoformat())}
 * 测试框架: Jest
 */

'''
        elif self.framework == TestFramework.JUNIT:
            return f'''/**
 * 自动生成的测试文件 - {result.spec_name}
 * 规范ID: {result.spec_id}
 * 生成时间: {result.generation_metadata.get('generated_at', datetime.now().isoformat())}
 * 测试框架: JUnit
 */
import org.junit.Test;

'''
        return ""
    
    def _get_file_extension(self) -> str:
        extensions = {
            TestFramework.PYTEST: "py",
            TestFramework.JEST: "test.js",
            TestFramework.JUNIT: "java",
            TestFramework.GO_TEST: "go",
            TestFramework.RUST_TEST: "rs",
        }
        return extensions.get(self.framework, "py")


def main():
    import argparse
    import sys
    sys.path.insert(0, str(get_path_config().SKILL_ROOT))
    
    from sdd_tdd.enhanced_spec_parser import EnhancedSDDSpecParser
    
    parser = argparse.ArgumentParser(description="规范到测试用例映射器")
    parser.add_argument("spec_file", help="规范文件路径")
    parser.add_argument("--framework", choices=["pytest", "jest", "junit"], default="pytest", help="测试框架")
    parser.add_argument("--output", help="输出文件路径")
    
    args = parser.parse_args()
    
    spec_parser = EnhancedSDDSpecParser()
    spec, validation_result = spec_parser.parse_file(args.spec_file)
    
    framework_map = {
        "pytest": TestFramework.PYTEST,
        "jest": TestFramework.JEST,
        "junit": TestFramework.JUNIT,
    }
    
    mapper = SpecToTestMapper(framework=framework_map[args.framework])
    result = mapper.generate_tests_from_spec(spec)
    
    print(f"测试用例生成完成:")
    print(f"  规范ID: {result.spec_id}")
    print(f"  规范名称: {result.spec_name}")
    print(f"  测试用例数: {len(result.test_cases)}")
    print(f"  覆盖率: {result.coverage_report['coverage_percentage']:.2f}%")
    
    test_file = mapper.save_test_file(result)
    print(f"\n测试文件已保存: {test_file}")


if __name__ == "__main__":
    main()
