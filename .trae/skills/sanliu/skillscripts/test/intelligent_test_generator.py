#!/usr/bin/env python3
"""
Intelligent Test Generator - 智能测试用例生成器

TDD红阶段智能增强组件，支持：
1. 基于需求分析自动生成测试用例
2. 多种测试类型支持（单元测试、集成测试、E2E测试）
3. 智能边界条件分析
4. 测试数据自动生成
5. 测试意图记录

使用示例：
    python intelligent_test_generator.py --spec specs/user_auth.yaml --type all --output tests/
    python intelligent_test_generator.py --spec specs/api.yaml --type integration --analyze-boundaries
"""

import argparse
import ast
import inspect
import json
import os
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union
import yaml


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ALL = "all"


class Priority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestStatus(Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestIntent:
    test_id: str
    purpose: str
    expected_behavior: str
    boundary_conditions: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    related_requirements: List[str] = field(default_factory=list)
    risk_level: str = "medium"
    coverage_target: float = 100.0


@dataclass
class BoundaryCondition:
    name: str
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    valid_values: List[Any] = field(default_factory=list)
    invalid_values: List[Any] = field(default_factory=list)
    edge_cases: List[Any] = field(default_factory=list)


@dataclass
class TestData:
    name: str
    data_type: str
    value: Any
    is_valid: bool = True
    description: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class TestCase:
    id: str
    name: str
    test_type: TestType
    priority: Priority
    intent: TestIntent
    test_data: List[TestData] = field(default_factory=list)
    arrange_code: str = ""
    act_code: str = ""
    assert_code: str = ""
    cleanup_code: str = ""
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    estimated_time_ms: int = 100
    status: TestStatus = TestStatus.PENDING


@dataclass
class Requirement:
    id: str
    name: str
    description: str
    type: str
    priority: Priority = Priority.MEDIUM
    acceptance_criteria: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    related_requirements: List[str] = field(default_factory=list)


@dataclass
class TestSuite:
    name: str
    test_type: TestType
    test_cases: List[TestCase] = field(default_factory=list)
    setup_code: str = ""
    teardown_code: str = ""
    fixtures: Dict[str, Any] = field(default_factory=dict)


class BoundaryAnalyzer:
    """边界条件分析器"""
    
    TYPE_BOUNDARIES = {
        "integer": {
            "min": -2147483648,
            "max": 2147483647,
            "edge_cases": [0, 1, -1, 255, 256, 65535, 65536]
        },
        "bigint": {
            "min": -9223372036854775808,
            "max": 9223372036854775807,
            "edge_cases": [0, 1, -1]
        },
        "float": {
            "min": -1.7976931348623157e308,
            "max": 1.7976931348623157e308,
            "edge_cases": [0.0, -0.0, 1.0, -1.0, 1e-10, 1e10]
        },
        "string": {
            "min_length": 0,
            "max_length": 65535,
            "edge_cases": ["", " ", "a", "  ", "\n", "\t", "中文", "🎉"]
        },
        "boolean": {
            "valid": [True, False],
            "invalid": [None, 0, 1, "", "true", "false"]
        },
        "date": {
            "edge_cases": ["1970-01-01", "2000-01-01", "2099-12-31", "1900-02-29"]
        },
        "datetime": {
            "edge_cases": [
                "1970-01-01T00:00:00Z",
                "2000-01-01T00:00:00Z",
                "2099-12-31T23:59:59Z"
            ]
        },
        "email": {
            "valid": ["test@example.com", "user.name@domain.org"],
            "invalid": ["", "invalid", "@domain.com", "user@", "user@.com"]
        },
        "url": {
            "valid": ["http://example.com", "https://domain.org/path"],
            "invalid": ["", "invalid", "ftp://file.com", "://no-protocol.com"]
        }
    }
    
    def analyze(self, param_name: str, param_type: str, constraints: Dict[str, Any] = None) -> BoundaryCondition:
        constraints = constraints or {}
        type_boundaries = self.TYPE_BOUNDARIES.get(param_type, {})
        
        boundary = BoundaryCondition(name=param_name)
        
        if param_type in ["integer", "bigint", "float"]:
            boundary.min_value = constraints.get("min", type_boundaries.get("min"))
            boundary.max_value = constraints.get("max", type_boundaries.get("max"))
            boundary.valid_values = self._generate_numeric_valid_values(boundary, param_type)
            boundary.invalid_values = self._generate_numeric_invalid_values(boundary, param_type)
            boundary.edge_cases = type_boundaries.get("edge_cases", [])
        
        elif param_type == "string":
            min_len = constraints.get("minLength", 0)
            max_len = constraints.get("maxLength", 65535)
            pattern = constraints.get("pattern")
            
            boundary.min_value = min_len
            boundary.max_value = max_len
            boundary.valid_values = self._generate_string_valid_values(min_len, max_len, pattern)
            boundary.invalid_values = self._generate_string_invalid_values(min_len, max_len, pattern)
            boundary.edge_cases = type_boundaries.get("edge_cases", [])
        
        elif param_type == "boolean":
            boundary.valid_values = type_boundaries.get("valid", [True, False])
            boundary.invalid_values = type_boundaries.get("invalid", [])
        
        elif param_type in ["email", "url"]:
            boundary.valid_values = type_boundaries.get("valid", [])
            boundary.invalid_values = type_boundaries.get("invalid", [])
        
        return boundary
    
    def _generate_numeric_valid_values(self, boundary: BoundaryCondition, param_type: str) -> List[Any]:
        values = []
        if boundary.min_value is not None:
            values.append(boundary.min_value)
            values.append(boundary.min_value + 1)
        if boundary.max_value is not None:
            values.append(boundary.max_value)
            values.append(boundary.max_value - 1)
        values.append(0)
        return list(set(values))
    
    def _generate_numeric_invalid_values(self, boundary: BoundaryCondition, param_type: str) -> List[Any]:
        values = []
        if boundary.min_value is not None:
            values.append(boundary.min_value - 1)
        if boundary.max_value is not None:
            values.append(boundary.max_value + 1)
        if param_type in ["integer", "bigint"]:
            values.extend([1.5, "string", None, [], {}])
        return values
    
    def _generate_string_valid_values(self, min_len: int, max_len: int, pattern: str = None) -> List[str]:
        values = []
        if min_len > 0:
            values.append("a" * min_len)
        if min_len < max_len:
            values.append("a" * (min_len + 1))
        if max_len < 1000:
            values.append("a" * max_len)
        values.append("valid_string")
        return values
    
    def _generate_string_invalid_values(self, min_len: int, max_len: int, pattern: str = None) -> List[Any]:
        values = []
        if min_len > 0:
            values.append("")
            values.append("a" * (min_len - 1))
        if max_len < 10000:
            values.append("a" * (max_len + 1))
        values.extend([None, 123, [], {}])
        return values


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self):
        self.boundary_analyzer = BoundaryAnalyzer()
        self._counter = 0
    
    def generate_for_parameter(
        self,
        param_name: str,
        param_type: str,
        constraints: Dict[str, Any] = None,
        include_boundary: bool = True
    ) -> List[TestData]:
        constraints = constraints or {}
        test_data_list = []
        
        if include_boundary:
            boundary = self.boundary_analyzer.analyze(param_name, param_type, constraints)
            
            for value in boundary.valid_values:
                self._counter += 1
                test_data_list.append(TestData(
                    name=f"{param_name}_valid_{self._counter}",
                    data_type=param_type,
                    value=value,
                    is_valid=True,
                    description=f"有效值测试数据: {value}",
                    tags=["valid", "boundary"]
                ))
            
            for value in boundary.invalid_values:
                self._counter += 1
                test_data_list.append(TestData(
                    name=f"{param_name}_invalid_{self._counter}",
                    data_type=param_type,
                    value=value,
                    is_valid=False,
                    description=f"无效值测试数据: {value}",
                    tags=["invalid", "boundary"]
                ))
            
            for value in boundary.edge_cases:
                self._counter += 1
                test_data_list.append(TestData(
                    name=f"{param_name}_edge_{self._counter}",
                    data_type=param_type,
                    value=value,
                    is_valid=True,
                    description=f"边界值测试数据: {value}",
                    tags=["edge_case"]
                ))
        
        return test_data_list
    
    def generate_for_entity(self, entity_def: Dict[str, Any]) -> Dict[str, List[TestData]]:
        result = {}
        attributes = entity_def.get("attributes", [])
        
        for attr in attributes:
            attr_name = attr.get("name", "")
            attr_type = attr.get("type", "string")
            constraints = attr.get("validation", {})
            
            result[attr_name] = self.generate_for_parameter(
                attr_name, attr_type, constraints
            )
        
        return result


class RequirementAnalyzer:
    """需求分析器"""
    
    def __init__(self):
        self._requirement_counter = 0
    
    def analyze_from_spec(self, spec: Dict[str, Any]) -> List[Requirement]:
        requirements = []
        
        spec_kind = spec.get("kind", "")
        spec_content = spec.get("spec", {})
        metadata = spec.get("metadata", {})
        
        if spec_kind == "EntitySpec":
            requirements.extend(self._analyze_entity_spec(spec_content, metadata))
        elif spec_kind == "InterfaceSpec":
            requirements.extend(self._analyze_interface_spec(spec_content, metadata))
        elif spec_kind == "AcceptanceSpec":
            requirements.extend(self._analyze_acceptance_spec(spec_content, metadata))
        elif spec_kind == "RuleSpec":
            requirements.extend(self._analyze_rule_spec(spec_content, metadata))
        else:
            requirements.extend(self._analyze_generic_spec(spec_content, metadata))
        
        return requirements
    
    def _analyze_entity_spec(self, spec_content: Dict, metadata: Dict) -> List[Requirement]:
        requirements = []
        entity_name = metadata.get("name", "Unknown")
        
        for attr in spec_content.get("attributes", []):
            self._requirement_counter += 1
            attr_name = attr.get("name", "")
            attr_type = attr.get("type", "string")
            required = attr.get("required", True)
            
            req = Requirement(
                id=f"REQ-{entity_name}-ATTR-{self._requirement_counter:03d}",
                name=f"{entity_name}.{attr_name}属性验证",
                description=f"验证{entity_name}实体的{attr_name}属性（类型: {attr_type}）",
                type="attribute_validation",
                priority=Priority.CRITICAL if required else Priority.MEDIUM,
                acceptance_criteria=[
                    f"属性类型必须为{attr_type}",
                    f"属性{'必填' if required else '可选'}",
                ],
                constraints=attr.get("validation", {})
            )
            requirements.append(req)
        
        for constraint in spec_content.get("constraints", []):
            self._requirement_counter += 1
            req = Requirement(
                id=f"REQ-{entity_name}-CONST-{self._requirement_counter:03d}",
                name=f"{entity_name}约束验证",
                description=constraint.get("description", ""),
                type="constraint_validation",
                priority=Priority.HIGH,
                acceptance_criteria=constraint.get("rules", []),
                constraints=constraint
            )
            requirements.append(req)
        
        return requirements
    
    def _analyze_interface_spec(self, spec_content: Dict, metadata: Dict) -> List[Requirement]:
        requirements = []
        api_name = metadata.get("name", "Unknown")
        
        for endpoint in spec_content.get("endpoints", []):
            self._requirement_counter += 1
            ep_name = endpoint.get("name", "")
            method = endpoint.get("method", "GET")
            path = endpoint.get("path", "/")
            
            req = Requirement(
                id=f"REQ-{api_name}-API-{self._requirement_counter:03d}",
                name=f"{api_name}.{ep_name}接口验证",
                description=f"验证{method} {path}接口",
                type="api_validation",
                priority=Priority.HIGH,
                acceptance_criteria=[
                    f"接口应响应{endpoint.get('response', {}).get('statusCode', 200)}状态码",
                    f"响应时间应小于{endpoint.get('response', {}).get('maxLatencyMs', 1000)}ms",
                ],
                constraints={
                    "method": method,
                    "path": path,
                    "parameters": endpoint.get("parameters", [])
                }
            )
            requirements.append(req)
            
            for error in endpoint.get("errors", []):
                self._requirement_counter += 1
                error_req = Requirement(
                    id=f"REQ-{api_name}-ERR-{self._requirement_counter:03d}",
                    name=f"{api_name}.{ep_name}错误处理",
                    description=f"验证{error.get('code')}错误处理",
                    type="error_handling",
                    priority=Priority.MEDIUM,
                    acceptance_criteria=[
                        f"应返回{error.get('statusCode')}状态码",
                        f"错误消息应为: {error.get('message')}"
                    ]
                )
                requirements.append(error_req)
        
        return requirements
    
    def _analyze_acceptance_spec(self, spec_content: Dict, metadata: Dict) -> List[Requirement]:
        requirements = []
        spec_name = metadata.get("name", "Unknown")
        
        for idx, scenario in enumerate(spec_content.get("scenarios", [])):
            self._requirement_counter += 1
            scenario_name = scenario.get("name", f"scenario_{idx}")
            
            req = Requirement(
                id=f"REQ-{spec_name}-SCENARIO-{self._requirement_counter:03d}",
                name=f"{spec_name}.{scenario_name}场景验证",
                description=scenario.get("description", ""),
                type="acceptance_criteria",
                priority=Priority.HIGH,
                acceptance_criteria=[
                    f"Given: {scenario.get('given', '')}",
                    f"When: {scenario.get('when', '')}",
                    f"Then: {scenario.get('then', '')}"
                ]
            )
            requirements.append(req)
        
        return requirements
    
    def _analyze_rule_spec(self, spec_content: Dict, metadata: Dict) -> List[Requirement]:
        requirements = []
        rule_name = metadata.get("name", "Unknown")
        
        self._requirement_counter += 1
        req = Requirement(
            id=f"REQ-{rule_name}-RULE-{self._requirement_counter:03d}",
            name=f"{rule_name}业务规则验证",
            description=spec_content.get("description", ""),
            type="business_rule",
            priority=Priority.HIGH,
            acceptance_criteria=spec_content.get("conditions", []),
            constraints=spec_content.get("parameters", {})
        )
        requirements.append(req)
        
        return requirements
    
    def _analyze_generic_spec(self, spec_content: Dict, metadata: Dict) -> List[Requirement]:
        requirements = []
        spec_name = metadata.get("name", "Unknown")
        
        self._requirement_counter += 1
        req = Requirement(
            id=f"REQ-{spec_name}-GEN-{self._requirement_counter:03d}",
            name=f"{spec_name}通用需求验证",
            description=spec_content.get("description", ""),
            type="generic",
            priority=Priority.MEDIUM,
            acceptance_criteria=spec_content.get("criteria", [])
        )
        requirements.append(req)
        
        return requirements


class TestCaseGeneratorStrategy(ABC):
    """测试用例生成策略基类"""
    
    @abstractmethod
    def generate(self, requirement: Requirement, context: Dict[str, Any]) -> List[TestCase]:
        pass
    
    @abstractmethod
    def get_test_type(self) -> TestType:
        pass


class UnitTestCaseGenerator(TestCaseGeneratorStrategy):
    """单元测试用例生成器"""
    
    def __init__(self):
        self.test_counter = 0
        self.data_generator = TestDataGenerator()
    
    def get_test_type(self) -> TestType:
        return TestType.UNIT
    
    def generate(self, requirement: Requirement, context: Dict[str, Any]) -> List[TestCase]:
        test_cases = []
        
        if requirement.type == "attribute_validation":
            test_cases.extend(self._generate_attribute_tests(requirement, context))
        elif requirement.type == "constraint_validation":
            test_cases.extend(self._generate_constraint_tests(requirement, context))
        elif requirement.type == "business_rule":
            test_cases.extend(self._generate_rule_tests(requirement, context))
        else:
            test_cases.extend(self._generate_generic_tests(requirement, context))
        
        return test_cases
    
    def _generate_attribute_tests(self, requirement: Requirement, context: Dict) -> List[TestCase]:
        test_cases = []
        constraints = requirement.constraints
        
        self.test_counter += 1
        valid_test = TestCase(
            id=f"TC-UNIT-{self.test_counter:04d}",
            name=f"test_{requirement.name.lower().replace(' ', '_')}_valid",
            test_type=TestType.UNIT,
            priority=requirement.priority,
            intent=TestIntent(
                test_id=f"TC-UNIT-{self.test_counter:04d}",
                purpose=f"验证{requirement.name}的有效输入",
                expected_behavior="属性应正确接受并存储有效值",
                related_requirements=[requirement.id]
            ),
            arrange_code=f"# 准备有效的测试数据",
            act_code=f"# 设置属性值",
            assert_code=f"# 验证属性值正确",
            tags=["unit", "attribute", "valid"]
        )
        test_cases.append(valid_test)
        
        if constraints:
            self.test_counter += 1
            invalid_test = TestCase(
                id=f"TC-UNIT-{self.test_counter:04d}",
                name=f"test_{requirement.name.lower().replace(' ', '_')}_invalid",
                test_type=TestType.UNIT,
                priority=requirement.priority,
                intent=TestIntent(
                    test_id=f"TC-UNIT-{self.test_counter:04d}",
                    purpose=f"验证{requirement.name}的无效输入处理",
                    expected_behavior="属性应拒绝无效值并抛出验证错误",
                    boundary_conditions=list(constraints.keys()),
                    related_requirements=[requirement.id]
                ),
                arrange_code=f"# 准备无效的测试数据",
                act_code=f"# 尝试设置无效属性值",
                assert_code=f"# 验证抛出验证错误",
                tags=["unit", "attribute", "invalid"]
            )
            test_cases.append(invalid_test)
        
        return test_cases
    
    def _generate_constraint_tests(self, requirement: Requirement, context: Dict) -> List[TestCase]:
        test_cases = []
        constraints = requirement.constraints
        
        for rule in requirement.acceptance_criteria:
            self.test_counter += 1
            test = TestCase(
                id=f"TC-UNIT-{self.test_counter:04d}",
                name=f"test_{requirement.name.lower().replace(' ', '_')}_{self.test_counter}",
                test_type=TestType.UNIT,
                priority=requirement.priority,
                intent=TestIntent(
                    test_id=f"TC-UNIT-{self.test_counter:04d}",
                    purpose=f"验证约束规则: {rule}",
                    expected_behavior="约束规则应被正确执行",
                    related_requirements=[requirement.id]
                ),
                arrange_code=f"# 准备测试数据",
                act_code=f"# 执行约束检查",
                assert_code=f"# 验证约束结果: {rule}",
                tags=["unit", "constraint"]
            )
            test_cases.append(test)
        
        return test_cases
    
    def _generate_rule_tests(self, requirement: Requirement, context: Dict) -> List[TestCase]:
        test_cases = []
        
        self.test_counter += 1
        trigger_test = TestCase(
            id=f"TC-UNIT-{self.test_counter:04d}",
            name=f"test_{requirement.name.lower().replace(' ', '_')}_triggered",
            test_type=TestType.UNIT,
            priority=requirement.priority,
            intent=TestIntent(
                test_id=f"TC-UNIT-{self.test_counter:04d}",
                purpose=f"验证{requirement.name}规则触发",
                expected_behavior="规则应在满足条件时正确触发",
                related_requirements=[requirement.id]
            ),
            arrange_code=f"# 准备触发规则的条件",
            act_code=f"# 执行规则检查",
            assert_code=f"# 验证规则已触发",
            tags=["unit", "rule", "trigger"]
        )
        test_cases.append(trigger_test)
        
        self.test_counter += 1
        not_trigger_test = TestCase(
            id=f"TC-UNIT-{self.test_counter:04d}",
            name=f"test_{requirement.name.lower().replace(' ', '_')}_not_triggered",
            test_type=TestType.UNIT,
            priority=requirement.priority,
            intent=TestIntent(
                test_id=f"TC-UNIT-{self.test_counter:04d}",
                purpose=f"验证{requirement.name}规则未触发",
                expected_behavior="规则应在不满足条件时不触发",
                related_requirements=[requirement.id]
            ),
            arrange_code=f"# 准备不触发规则的条件",
            act_code=f"# 执行规则检查",
            assert_code=f"# 验证规则未触发",
            tags=["unit", "rule", "no-trigger"]
        )
        test_cases.append(not_trigger_test)
        
        return test_cases
    
    def _generate_generic_tests(self, requirement: Requirement, context: Dict) -> List[TestCase]:
        test_cases = []
        
        for criterion in requirement.acceptance_criteria:
            self.test_counter += 1
            test = TestCase(
                id=f"TC-UNIT-{self.test_counter:04d}",
                name=f"test_{requirement.name.lower().replace(' ', '_')}_{self.test_counter}",
                test_type=TestType.UNIT,
                priority=requirement.priority,
                intent=TestIntent(
                    test_id=f"TC-UNIT-{self.test_counter:04d}",
                    purpose=f"验证验收标准: {criterion}",
                    expected_behavior="验收标准应被满足",
                    related_requirements=[requirement.id]
                ),
                arrange_code=f"# 准备测试环境",
                act_code=f"# 执行测试操作",
                assert_code=f"# 验证: {criterion}",
                tags=["unit", "generic"]
            )
            test_cases.append(test)
        
        return test_cases


class IntegrationTestCaseGenerator(TestCaseGeneratorStrategy):
    """集成测试用例生成器"""
    
    def __init__(self):
        self.test_counter = 0
    
    def get_test_type(self) -> TestType:
        return TestType.INTEGRATION
    
    def generate(self, requirement: Requirement, context: Dict[str, Any]) -> List[TestCase]:
        test_cases = []
        
        if requirement.type == "api_validation":
            test_cases.extend(self._generate_api_tests(requirement, context))
        elif requirement.type == "error_handling":
            test_cases.extend(self._generate_error_tests(requirement, context))
        else:
            test_cases.extend(self._generate_integration_tests(requirement, context))
        
        return test_cases
    
    def _generate_api_tests(self, requirement: Requirement, context: Dict) -> List[TestCase]:
        test_cases = []
        constraints = requirement.constraints
        method = constraints.get("method", "GET")
        path = constraints.get("path", "/")
        
        self.test_counter += 1
        success_test = TestCase(
            id=f"TC-INT-{self.test_counter:04d}",
            name=f"test_{requirement.name.lower().replace(' ', '_')}_success",
            test_type=TestType.INTEGRATION,
            priority=requirement.priority,
            intent=TestIntent(
                test_id=f"TC-INT-{self.test_counter:04d}",
                purpose=f"验证{method} {path}成功响应",
                expected_behavior="接口应返回成功状态码和正确数据",
                related_requirements=[requirement.id]
            ),
            arrange_code=f"# 准备请求参数和认证",
            act_code=f"# 发送{method}请求到{path}",
            assert_code=f"# 验证响应状态码和数据",
            tags=["integration", "api", "success"]
        )
        test_cases.append(success_test)
        
        for param in constraints.get("parameters", []):
            if param.get("required", False):
                self.test_counter += 1
                missing_test = TestCase(
                    id=f"TC-INT-{self.test_counter:04d}",
                    name=f"test_{requirement.name.lower().replace(' ', '_')}_missing_{param.get('name', 'param')}",
                    test_type=TestType.INTEGRATION,
                    priority=Priority.HIGH,
                    intent=TestIntent(
                        test_id=f"TC-INT-{self.test_counter:04d}",
                        purpose=f"验证缺少必填参数{param.get('name')}的处理",
                        expected_behavior="接口应返回400错误",
                        related_requirements=[requirement.id]
                    ),
                    arrange_code=f"# 准备缺少{param.get('name')}的请求",
                    act_code=f"# 发送不完整的请求",
                    assert_code=f"# 验证返回400错误",
                    tags=["integration", "api", "validation"]
                )
                test_cases.append(missing_test)
        
        return test_cases
    
    def _generate_error_tests(self, requirement: Requirement, context: Dict) -> List[TestCase]:
        test_cases = []
        
        self.test_counter += 1
        test = TestCase(
            id=f"TC-INT-{self.test_counter:04d}",
            name=f"test_{requirement.name.lower().replace(' ', '_')}",
            test_type=TestType.INTEGRATION,
            priority=requirement.priority,
            intent=TestIntent(
                test_id=f"TC-INT-{self.test_counter:04d}",
                purpose=requirement.description,
                expected_behavior="错误应被正确处理并返回预期响应",
                related_requirements=[requirement.id]
            ),
            arrange_code=f"# 准备触发错误的条件",
            act_code=f"# 执行操作",
            assert_code=f"# 验证错误响应",
            tags=["integration", "error"]
        )
        test_cases.append(test)
        
        return test_cases
    
    def _generate_integration_tests(self, requirement: Requirement, context: Dict) -> List[TestCase]:
        test_cases = []
        
        self.test_counter += 1
        test = TestCase(
            id=f"TC-INT-{self.test_counter:04d}",
            name=f"test_{requirement.name.lower().replace(' ', '_')}_integration",
            test_type=TestType.INTEGRATION,
            priority=requirement.priority,
            intent=TestIntent(
                test_id=f"TC-INT-{self.test_counter:04d}",
                purpose=f"集成测试: {requirement.description}",
                expected_behavior="组件间交互应正常工作",
                related_requirements=[requirement.id]
            ),
            arrange_code=f"# 准备集成测试环境",
            act_code=f"# 执行集成操作",
            assert_code=f"# 验证集成结果",
            tags=["integration"]
        )
        test_cases.append(test)
        
        return test_cases


class E2ETestCaseGenerator(TestCaseGeneratorStrategy):
    """E2E测试用例生成器"""
    
    def __init__(self):
        self.test_counter = 0
    
    def get_test_type(self) -> TestType:
        return TestType.E2E
    
    def generate(self, requirement: Requirement, context: Dict[str, Any]) -> List[TestCase]:
        test_cases = []
        
        if requirement.type == "acceptance_criteria":
            test_cases.extend(self._generate_acceptance_tests(requirement, context))
        else:
            test_cases.extend(self._generate_e2e_tests(requirement, context))
        
        return test_cases
    
    def _generate_acceptance_tests(self, requirement: Requirement, context: Dict) -> List[TestCase]:
        test_cases = []
        
        for criterion in requirement.acceptance_criteria:
            self.test_counter += 1
            test = TestCase(
                id=f"TC-E2E-{self.test_counter:04d}",
                name=f"test_{requirement.name.lower().replace(' ', '_')}_{self.test_counter}",
                test_type=TestType.E2E,
                priority=requirement.priority,
                intent=TestIntent(
                    test_id=f"TC-E2E-{self.test_counter:04d}",
                    purpose=f"E2E验收测试: {criterion}",
                    expected_behavior="用户流程应按预期完成",
                    related_requirements=[requirement.id]
                ),
                arrange_code=f"# 准备E2E测试环境\n# {criterion}",
                act_code=f"# 执行用户操作流程",
                assert_code=f"# 验证最终结果",
                tags=["e2e", "acceptance"],
                estimated_time_ms=5000
            )
            test_cases.append(test)
        
        return test_cases
    
    def _generate_e2e_tests(self, requirement: Requirement, context: Dict) -> List[TestCase]:
        test_cases = []
        
        self.test_counter += 1
        test = TestCase(
            id=f"TC-E2E-{self.test_counter:04d}",
            name=f"test_{requirement.name.lower().replace(' ', '_')}_e2e",
            test_type=TestType.E2E,
            priority=requirement.priority,
            intent=TestIntent(
                test_id=f"TC-E2E-{self.test_counter:04d}",
                purpose=f"E2E测试: {requirement.description}",
                expected_behavior="端到端流程应正常工作",
                related_requirements=[requirement.id]
            ),
            arrange_code=f"# 准备完整的测试环境",
            act_code=f"# 执行完整的用户流程",
            assert_code=f"# 验证端到端结果",
            tags=["e2e"],
            estimated_time_ms=5000
        )
        test_cases.append(test)
        
        return test_cases


class IntelligentTestGenerator:
    """智能测试用例生成器主类"""
    
    def __init__(self):
        self.requirement_analyzer = RequirementAnalyzer()
        self.data_generator = TestDataGenerator()
        self.generators: Dict[TestType, TestCaseGeneratorStrategy] = {
            TestType.UNIT: UnitTestCaseGenerator(),
            TestType.INTEGRATION: IntegrationTestCaseGenerator(),
            TestType.E2E: E2ETestCaseGenerator(),
        }
        self.test_intents: Dict[str, TestIntent] = {}
    
    def generate_from_spec(
        self,
        spec_path: str,
        test_types: List[TestType] = None,
        output_dir: str = "tests/generated"
    ) -> Dict[str, Any]:
        spec = self._load_spec(spec_path)
        requirements = self.requirement_analyzer.analyze_from_spec(spec)
        
        test_types = test_types or [TestType.UNIT]
        
        all_test_cases = []
        test_suites = []
        
        for test_type in test_types:
            generator = self.generators.get(test_type)
            if generator:
                suite_cases = []
                for req in requirements:
                    cases = generator.generate(req, {"spec": spec})
                    suite_cases.extend(cases)
                    all_test_cases.extend(cases)
                    
                    for case in cases:
                        self.test_intents[case.id] = case.intent
                
                test_suites.append(TestSuite(
                    name=f"{spec.get('metadata', {}).get('name', 'Unknown')}_{test_type.value}_tests",
                    test_type=test_type,
                    test_cases=suite_cases
                ))
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        for suite in test_suites:
            file_content = self._generate_test_file(suite, spec)
            file_name = f"test_{suite.name.lower()}.py"
            file_path = output_path / file_name
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)
            
            generated_files.append(str(file_path))
        
        intent_file = output_path / "test_intents.json"
        with open(intent_file, "w", encoding="utf-8") as f:
            json.dump(
                {k: v.__dict__ for k, v in self.test_intents.items()},
                f,
                ensure_ascii=False,
                indent=2,
                default=str
            )
        
        return {
            "spec": spec.get("metadata", {}).get("name", "Unknown"),
            "requirements_count": len(requirements),
            "test_cases_count": len(all_test_cases),
            "test_suites": [
                {
                    "name": s.name,
                    "type": s.test_type.value,
                    "count": len(s.test_cases)
                }
                for s in test_suites
            ],
            "generated_files": generated_files,
            "intent_file": str(intent_file)
        }
    
    def _load_spec(self, spec_path: str) -> Dict[str, Any]:
        path = Path(spec_path)
        if not path.exists():
            raise FileNotFoundError(f"规范文件不存在: {spec_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in [".yaml", ".yml"]:
                return yaml.safe_load(f)
            elif path.suffix == ".json":
                return json.load(f)
            else:
                raise ValueError(f"不支持的文件格式: {path.suffix}")
    
    def _generate_test_file(self, suite: TestSuite, spec: Dict) -> str:
        metadata = spec.get("metadata", {})
        
        lines = [
            '"""',
            f'{suite.name} 测试套件',
            "",
            f"规范: {metadata.get('name', 'Unknown')}",
            f"版本: {metadata.get('version', '1.0.0')}",
            f"测试类型: {suite.test_type.value}",
            f"生成时间: {datetime.now().isoformat()}",
            "",
            "此文件由智能测试生成器自动生成",
            '"""',
            "",
        ]
        
        if suite.test_type == TestType.UNIT:
            lines.extend([
                "import pytest",
                "from pydantic import ValidationError",
                "",
            ])
        elif suite.test_type == TestType.INTEGRATION:
            lines.extend([
                "import pytest",
                "from fastapi.testclient import TestClient",
                "from http import HTTPStatus",
                "",
            ])
        elif suite.test_type == TestType.E2E:
            lines.extend([
                "import pytest",
                "from playwright.sync_api import Page, expect",
                "",
            ])
        
        lines.extend([
            f"class Test{suite.name.replace('_', '').title()}:",
            f'    """{suite.name} 测试类"""',
            "",
        ])
        
        for tc in suite.test_cases:
            lines.extend(self._generate_test_method(tc))
        
        return "\n".join(lines)
    
    def _generate_test_method(self, test_case: TestCase) -> List[str]:
        lines = [
            f"    def {test_case.name}(self):",
            f'        """',
            f"        测试目的: {test_case.intent.purpose}",
            f"        预期行为: {test_case.intent.expected_behavior}",
            f"        相关需求: {', '.join(test_case.intent.related_requirements)}",
            f'        """',
        ]
        
        if test_case.test_data:
            lines.append("        # 测试数据")
            for td in test_case.test_data:
                lines.append(f"        # {td.name}: {td.value} ({'有效' if td.is_valid else '无效'})")
        
        lines.extend([
            "",
            "        # Arrange",
            f"        {test_case.arrange_code}",
            "",
            "        # Act",
            f"        {test_case.act_code}",
            "",
            "        # Assert",
            f"        {test_case.assert_code}",
            "        pass",
            "",
        ])
        
        return lines
    
    def get_test_intent(self, test_id: str) -> Optional[TestIntent]:
        return self.test_intents.get(test_id)
    
    def get_all_intents(self) -> Dict[str, TestIntent]:
        return self.test_intents.copy()


def main():
    parser = argparse.ArgumentParser(
        description="智能测试用例生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成单元测试
  python intelligent_test_generator.py --spec specs/user.yaml --type unit --output tests/
  
  # 生成所有类型测试
  python intelligent_test_generator.py --spec specs/api.yaml --type all --output tests/
  
  # 生成集成测试和E2E测试
  python intelligent_test_generator.py --spec specs/feature.yaml --type integration --type e2e
        """
    )
    
    parser.add_argument(
        "--spec",
        required=True,
        help="规范文件路径"
    )
    
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "e2e", "all"],
        action="append",
        default=[],
        help="测试类型（可多次指定）"
    )
    
    parser.add_argument(
        "--output",
        default="tests/generated",
        help="输出目录"
    )
    
    parser.add_argument(
        "--analyze-boundaries",
        action="store_true",
        help="分析边界条件"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细输出"
    )
    
    args = parser.parse_args()
    
    test_types = []
    if "all" in args.type or not args.type:
        test_types = [TestType.UNIT, TestType.INTEGRATION, TestType.E2E]
    else:
        type_mapping = {
            "unit": TestType.UNIT,
            "integration": TestType.INTEGRATION,
            "e2e": TestType.E2E
        }
        test_types = [type_mapping[t] for t in args.type if t in type_mapping]
    
    generator = IntelligentTestGenerator()
    
    try:
        result = generator.generate_from_spec(
            args.spec,
            test_types,
            args.output
        )
        
        print(f"测试生成完成:")
        print(f"  规范: {result['spec']}")
        print(f"  需求数量: {result['requirements_count']}")
        print(f"  测试用例数量: {result['test_cases_count']}")
        print(f"  测试套件:")
        for suite in result['test_suites']:
            print(f"    - {suite['name']}: {suite['count']} 个测试")
        print(f"  生成文件:")
        for f in result['generated_files']:
            print(f"    - {f}")
        print(f"  测试意图文件: {result['intent_file']}")
        
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"执行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
