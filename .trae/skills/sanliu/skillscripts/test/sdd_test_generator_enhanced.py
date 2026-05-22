#!/usr/bin/env python3
"""
SDD规范测试用例生成器增强版 v2.0

支持多种测试框架的测试用例自动生成：
1. pytest (Python)
2. jest (JavaScript/TypeScript)
3. playwright (E2E测试)
4. unittest (Python标准库)

增强功能：
- 从SDD规范自动生成测试用例
- 根据实体定义生成实体测试
- 根据业务规则生成业务逻辑测试
- 根据约束条件生成边界条件测试
- 根据接口契约生成API测试
- 测试覆盖率验证
- 集成兵部测试先行流程
- 支持多种测试框架输出
- 生成测试数据模板
- 生成测试夹具(Fixtures)
- 支持参数化测试
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import sys
import os
from skillscripts.core.path_config_center import get_path_config

sys.path.insert(0, str(get_path_config().SKILL_ROOT))
sys.path.insert(0, str(get_path_config().SKILL_ROOT.parent))

try:
    from pipeline.sdd_spec_parser import (
        SDDSpecification,
        SpecAttribute,
        SpecEndpoint,
        SpecScenario,
        SpecType,
    )
except ImportError:
    from skillscripts.pipeline.sdd_spec_parser import (
        SDDSpecification,
        SpecAttribute,
        SpecEndpoint,
        SpecScenario,
        SpecType,
    )


class TestFramework(Enum):
    PYTEST = "pytest"
    JEST = "jest"
    PLAYWRIGHT = "playwright"
    UNITTEST = "unittest"
    VITEST = "vitest"


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    API = "api"
    ACCEPTANCE = "acceptance"


@dataclass
class TestCase:
    id: str
    name: str
    description: str
    test_type: TestType
    spec_element: str
    arrange: str = ""
    act: str = ""
    assert_: str = ""
    test_data: Dict[str, Any] = field(default_factory=dict)
    markers: List[str] = field(default_factory=list)
    timeout: int = 30000
    skip: bool = False
    skip_reason: str = ""


@dataclass
class TestSuite:
    name: str
    description: str
    test_cases: List[TestCase] = field(default_factory=list)
    fixtures: Dict[str, str] = field(default_factory=dict)
    setup: str = ""
    teardown: str = ""
    imports: List[str] = field(default_factory=list)


@dataclass
class GeneratedTestFile:
    filename: str
    content: str
    framework: TestFramework
    test_count: int
    dependencies: List[str] = field(default_factory=list)


class BaseTestGenerator(ABC):
    """测试生成器基类"""
    
    @abstractmethod
    def generate(self, spec: SDDSpecification) -> GeneratedTestFile:
        pass
    
    @abstractmethod
    def get_framework(self) -> TestFramework:
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        pass
    
    def _to_snake_case(self, name: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_camel_case(self, name: str) -> str:
        components = name.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    def _to_pascal_case(self, name: str) -> str:
        components = name.split('_')
        return ''.join(x.title() for x in components)
    
    def _sanitize_name(self, name: str) -> str:
        sanitized = re.sub(r'[^\w\u4e00-\u9fff]', '_', name)
        return re.sub(r'_+', '_', sanitized).strip('_')


class PytestGenerator(BaseTestGenerator):
    """Pytest测试框架生成器"""
    
    def get_framework(self) -> TestFramework:
        return TestFramework.PYTEST
    
    def get_file_extension(self) -> str:
        return ".py"
    
    def generate(self, spec: SDDSpecification) -> GeneratedTestFile:
        test_suite = self._build_test_suite(spec)
        content = self._generate_content(test_suite, spec)
        
        filename = f"test_{self._to_snake_case(spec.metadata.name)}{self.get_file_extension()}"
        
        return GeneratedTestFile(
            filename=filename,
            content=content,
            framework=self.get_framework(),
            test_count=len(test_suite.test_cases),
            dependencies=["pytest", "pydantic"],
        )
    
    def _build_test_suite(self, spec: SDDSpecification) -> TestSuite:
        test_cases = []
        
        if spec.kind == SpecType.ENTITY:
            test_cases.extend(self._generate_entity_tests(spec))
        elif spec.kind in [SpecType.INTERFACE, SpecType.API]:
            test_cases.extend(self._generate_api_tests(spec))
        elif spec.kind == SpecType.ACCEPTANCE:
            test_cases.extend(self._generate_acceptance_tests(spec))
        elif spec.kind == SpecType.FUNCTION:
            test_cases.extend(self._generate_function_tests(spec))
        
        if hasattr(spec, 'conditional_rules') and spec.conditional_rules:
            test_cases.extend(self._generate_business_rule_tests(spec))
        
        if hasattr(spec, 'constraints') and spec.constraints:
            test_cases.extend(self._generate_constraint_tests(spec))
        
        if hasattr(spec, 'state_machines') and spec.state_machines:
            test_cases.extend(self._generate_state_machine_tests(spec))
        
        fixtures = self._generate_fixtures(spec)
        
        return TestSuite(
            name=f"Test{self._to_pascal_case(spec.metadata.name)}",
            description=f"{spec.metadata.name} 测试套件",
            test_cases=test_cases,
            fixtures=fixtures,
        )
    
    def _generate_entity_tests(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-{spec.metadata.id}"
        
        for idx, attr in enumerate(spec.attributes):
            tc_id = f"{base_id}-ATTR-{idx+1:03d}"
            
            test_cases.append(TestCase(
                id=tc_id,
                name=f"test_{attr.name}_required_validation",
                description=f"测试{attr.name}属性必填验证",
                test_type=TestType.UNIT,
                spec_element=attr.name,
                arrange=f"# 准备测试数据，{attr.name}为空",
                act=f"# 创建实体",
                assert_=f"# 验证抛出验证错误",
                markers=["validation", "unit"],
            ))
            
            if attr.constraints:
                for constraint_name, constraint_value in attr.constraints.items():
                    test_cases.append(TestCase(
                        id=f"{tc_id}-{constraint_name}",
                        name=f"test_{attr.name}_{constraint_name}_constraint",
                        description=f"测试{attr.name}的{constraint_name}约束",
                        test_type=TestType.UNIT,
                        spec_element=attr.name,
                        arrange=f"# 准备违反{constraint_name}约束的数据",
                        act=f"# 创建实体",
                        assert_=f"# 验证约束生效",
                        test_data={"constraint_value": constraint_value},
                        markers=["validation", "constraint"],
                    ))
            
            if attr.enum_values:
                test_cases.append(TestCase(
                    id=f"{tc_id}-enum",
                    name=f"test_{attr.name}_enum_values",
                    description=f"测试{attr.name}枚举值验证",
                    test_type=TestType.UNIT,
                    spec_element=attr.name,
                    arrange=f"# 准备枚举值测试数据",
                    act=f"# 验证枚举值",
                    assert_=f"# 确认枚举值有效",
                    test_data={"enum_values": attr.enum_values},
                    markers=["validation", "enum"],
                ))
        
        for rel in spec.relationships:
            test_cases.append(TestCase(
                id=f"{base_id}-REL-{len(test_cases)+1:03d}",
                name=f"test_{rel.get('name', 'relationship')}_relationship",
                description=f"测试{rel.get('name', '')}关系",
                test_type=TestType.UNIT,
                spec_element=rel.get('name', ''),
                arrange=f"# 准备关系测试数据",
                act=f"# 验证关系",
                assert_=f"# 确认关系正确",
                markers=["relationship"],
            ))
        
        return test_cases
    
    def _generate_api_tests(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-{spec.metadata.id}"
        
        for idx, endpoint in enumerate(spec.endpoints):
            tc_id = f"{base_id}-EP-{idx+1:03d}"
            
            test_cases.append(TestCase(
                id=f"{tc_id}-success",
                name=f"test_{endpoint.name}_success",
                description=f"测试{endpoint.name}成功场景",
                test_type=TestType.API,
                spec_element=endpoint.name,
                arrange=f"# 准备有效请求数据",
                act=f"# 发送{endpoint.method}请求到{endpoint.path}",
                assert_=f"# 验证响应状态码为200",
                markers=["api", "success"],
            ))
            
            test_cases.append(TestCase(
                id=f"{tc_id}-unauthorized",
                name=f"test_{endpoint.name}_unauthorized",
                description=f"测试{endpoint.name}未授权场景",
                test_type=TestType.API,
                spec_element=endpoint.name,
                arrange=f"# 准备无认证令牌的请求",
                act=f"# 发送{endpoint.method}请求到{endpoint.path}",
                assert_=f"# 验证响应状态码为401",
                markers=["api", "security"],
            ))
            
            for err_idx, error in enumerate(endpoint.errors):
                test_cases.append(TestCase(
                    id=f"{tc_id}-error-{err_idx+1}",
                    name=f"test_{endpoint.name}_error_{error.get('code', err_idx)}",
                    description=f"测试{endpoint.name}错误场景: {error.get('message', '')}",
                    test_type=TestType.API,
                    spec_element=endpoint.name,
                    arrange=f"# 准备触发错误的数据",
                    act=f"# 发送{endpoint.method}请求到{endpoint.path}",
                    assert_=f"# 验证响应状态码为{error.get('statusCode', 400)}",
                    test_data={"expected_error": error},
                    markers=["api", "error"],
                ))
            
            for param in endpoint.parameters:
                if param.get("required", False):
                    test_cases.append(TestCase(
                        id=f"{tc_id}-param-{param.get('name', 'missing')}",
                        name=f"test_{endpoint.name}_missing_{param.get('name', 'param')}",
                        description=f"测试{endpoint.name}缺少必填参数{param.get('name', '')}",
                        test_type=TestType.API,
                        spec_element=endpoint.name,
                        arrange=f"# 准备缺少{param.get('name', '')}参数的请求",
                        act=f"# 发送{endpoint.method}请求到{endpoint.path}",
                        assert_=f"# 验证响应状态码为400",
                        markers=["api", "validation"],
                    ))
        
        return test_cases
    
    def _generate_acceptance_tests(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-{spec.metadata.id}"
        
        for idx, scenario in enumerate(spec.scenarios):
            test_cases.append(TestCase(
                id=f"{base_id}-SCENE-{idx+1:03d}",
                name=f"test_{self._to_snake_case(scenario.name)}",
                description=f"验收测试场景: {scenario.name}",
                test_type=TestType.ACCEPTANCE,
                spec_element=scenario.name,
                arrange=f"# Given: {scenario.given}",
                act=f"# When: {scenario.when}",
                assert_=f"# Then: {scenario.then}",
                test_data=scenario.test_data,
                markers=["acceptance", "bdd"],
            ))
        
        return test_cases
    
    def _generate_function_tests(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-{spec.metadata.id}"
        
        spec_content = spec.spec
        inputs = spec_content.get("inputs", spec_content.get("attributes", []))
        outputs = spec_content.get("outputs", [])
        exceptions = spec_content.get("exceptions", spec_content.get("errors", []))
        
        for idx, inp in enumerate(inputs):
            test_cases.append(TestCase(
                id=f"{base_id}-IN-{idx+1:03d}",
                name=f"test_{inp.get('name', f'input_{idx}')}_valid",
                description=f"测试有效输入: {inp.get('name', '')}",
                test_type=TestType.UNIT,
                spec_element=inp.get('name', ''),
                arrange=f"# 准备有效的{inp.get('name', '')}",
                act=f"# 执行功能",
                assert_=f"# 验证执行成功",
                markers=["input", "happy_path"],
            ))
            
            if inp.get("constraints") or inp.get("validation"):
                test_cases.append(TestCase(
                    id=f"{base_id}-IN-{idx+1:03d}-invalid",
                    name=f"test_{inp.get('name', f'input_{idx}')}_invalid",
                    description=f"测试无效输入: {inp.get('name', '')}",
                    test_type=TestType.UNIT,
                    spec_element=inp.get('name', ''),
                    arrange=f"# 准备无效的{inp.get('name', '')}",
                    act=f"# 执行功能",
                    assert_=f"# 验证抛出异常",
                    markers=["input", "error_path"],
                ))
        
        for idx, exc in enumerate(exceptions):
            test_cases.append(TestCase(
                id=f"{base_id}-EXC-{idx+1:03d}",
                name=f"test_exception_{exc.get('name', exc.get('type', f'exception_{idx}'))}",
                description=f"测试异常处理: {exc.get('name', exc.get('type', ''))}",
                test_type=TestType.UNIT,
                spec_element=exc.get('name', exc.get('type', '')),
                arrange=f"# 准备触发异常的条件",
                act=f"# 执行功能",
                assert_=f"# 验证抛出{exc.get('name', exc.get('type', ''))}异常",
                markers=["exception", "error_handling"],
            ))
        
        return test_cases
    
    def _generate_business_rule_tests(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-{spec.metadata.id}"
        
        for idx, rule in enumerate(spec.conditional_rules):
            rule_id = f"{base_id}-RULE-{idx+1:03d}"
            
            test_cases.append(TestCase(
                id=f"{rule_id}-positive",
                name=f"test_business_rule_{self._to_snake_case(rule.name)}_satisfied",
                description=f"测试业务规则: {rule.name} - 条件满足场景",
                test_type=TestType.UNIT,
                spec_element=rule.name,
                arrange=f"# Given: 准备满足条件 '{rule.condition}' 的数据",
                act=f"# When: 执行业务逻辑",
                assert_=f"# Then: 验证执行 '{rule.then_branch}' 分支",
                test_data={
                    "condition": rule.condition,
                    "then_branch": rule.then_branch,
                },
                markers=["business_rule", "positive"],
            ))
            
            test_cases.append(TestCase(
                id=f"{rule_id}-negative",
                name=f"test_business_rule_{self._to_snake_case(rule.name)}_not_satisfied",
                description=f"测试业务规则: {rule.name} - 条件不满足场景",
                test_type=TestType.UNIT,
                spec_element=rule.name,
                arrange=f"# Given: 准备不满足条件 '{rule.condition}' 的数据",
                act=f"# When: 执行业务逻辑",
                assert_=f"# Then: 验证执行 '{rule.else_branch if rule.else_branch else '默认分支'}'",
                test_data={
                    "condition": rule.condition,
                    "else_branch": rule.else_branch,
                },
                markers=["business_rule", "negative"],
            ))
            
            if rule.dependencies:
                test_cases.append(TestCase(
                    id=f"{rule_id}-dependencies",
                    name=f"test_business_rule_{self._to_snake_case(rule.name)}_dependencies",
                    description=f"测试业务规则: {rule.name} - 依赖项验证",
                    test_type=TestType.UNIT,
                    spec_element=rule.name,
                    arrange=f"# Given: 准备依赖项 {rule.dependencies}",
                    act=f"# When: 验证依赖项可用性",
                    assert_=f"# Then: 确认所有依赖项满足",
                    test_data={"dependencies": rule.dependencies},
                    markers=["business_rule", "dependency"],
                ))
        
        return test_cases
    
    def _generate_constraint_tests(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-{spec.metadata.id}"
        
        for idx, constraint in enumerate(spec.constraints):
            constraint_id = f"{base_id}-CONST-{idx+1:03d}"
            constraint_name = constraint.get("name", f"constraint_{idx}")
            constraint_type = constraint.get("type", "validation")
            constraint_value = constraint.get("value", constraint.get("condition", ""))
            
            test_cases.append(TestCase(
                id=f"{constraint_id}-valid",
                name=f"test_constraint_{self._to_snake_case(constraint_name)}_valid",
                description=f"测试约束条件: {constraint_name} - 有效值",
                test_type=TestType.UNIT,
                spec_element=constraint_name,
                arrange=f"# Given: 准备符合约束 '{constraint_value}' 的数据",
                act=f"# When: 验证约束",
                assert_=f"# Then: 确认数据有效",
                test_data={"constraint": constraint},
                markers=["constraint", "validation", "positive"],
            ))
            
            test_cases.append(TestCase(
                id=f"{constraint_id}-invalid",
                name=f"test_constraint_{self._to_snake_case(constraint_name)}_invalid",
                description=f"测试约束条件: {constraint_name} - 无效值",
                test_type=TestType.UNIT,
                spec_element=constraint_name,
                arrange=f"# Given: 准备违反约束 '{constraint_value}' 的数据",
                act=f"# When: 验证约束",
                assert_=f"# Then: 确认抛出验证错误",
                test_data={"constraint": constraint},
                markers=["constraint", "validation", "negative"],
            ))
            
            if constraint_type in ["range", "boundary"]:
                test_cases.append(TestCase(
                    id=f"{constraint_id}-boundary",
                    name=f"test_constraint_{self._to_snake_case(constraint_name)}_boundary",
                    description=f"测试约束条件: {constraint_name} - 边界值",
                    test_type=TestType.UNIT,
                    spec_element=constraint_name,
                    arrange=f"# Given: 准备边界值数据",
                    act=f"# When: 验证边界约束",
                    assert_=f"# Then: 确认边界处理正确",
                    test_data={"constraint": constraint},
                    markers=["constraint", "boundary"],
                ))
        
        for attr in spec.attributes:
            if attr.constraints:
                for constraint_name, constraint_value in attr.constraints.items():
                    test_cases.extend(self._generate_attribute_constraint_tests(
                        base_id, attr, constraint_name, constraint_value
                    ))
        
        return test_cases
    
    def _generate_attribute_constraint_tests(
        self, base_id: str, attr: SpecAttribute, constraint_name: str, constraint_value: Any
    ) -> List[TestCase]:
        test_cases = []
        constraint_id = f"{base_id}-ATTR-{attr.name}-{constraint_name}"
        
        if constraint_name == "minLength":
            test_cases.append(TestCase(
                id=f"{constraint_id}-below",
                name=f"test_{attr.name}_min_length_below",
                description=f"测试{attr.name}最小长度约束 - 低于最小值",
                test_type=TestType.UNIT,
                spec_element=attr.name,
                arrange=f"# Given: 准备长度为 {max(0, constraint_value - 1)} 的字符串",
                act=f"# When: 验证属性",
                assert_=f"# Then: 确认验证失败",
                test_data={"min_length": constraint_value},
                markers=["constraint", "boundary", "negative"],
            ))
            test_cases.append(TestCase(
                id=f"{constraint_id}-exact",
                name=f"test_{attr.name}_min_length_exact",
                description=f"测试{attr.name}最小长度约束 - 等于最小值",
                test_type=TestType.UNIT,
                spec_element=attr.name,
                arrange=f"# Given: 准备长度为 {constraint_value} 的字符串",
                act=f"# When: 验证属性",
                assert_=f"# Then: 确认验证通过",
                test_data={"min_length": constraint_value},
                markers=["constraint", "boundary"],
            ))
        
        elif constraint_name == "maxLength":
            test_cases.append(TestCase(
                id=f"{constraint_id}-above",
                name=f"test_{attr.name}_max_length_above",
                description=f"测试{attr.name}最大长度约束 - 超过最大值",
                test_type=TestType.UNIT,
                spec_element=attr.name,
                arrange=f"# Given: 准备长度为 {constraint_value + 1} 的字符串",
                act=f"# When: 验证属性",
                assert_=f"# Then: 确认验证失败",
                test_data={"max_length": constraint_value},
                markers=["constraint", "boundary", "negative"],
            ))
            test_cases.append(TestCase(
                id=f"{constraint_id}-exact",
                name=f"test_{attr.name}_max_length_exact",
                description=f"测试{attr.name}最大长度约束 - 等于最大值",
                test_type=TestType.UNIT,
                spec_element=attr.name,
                arrange=f"# Given: 准备长度为 {constraint_value} 的字符串",
                act=f"# When: 验证属性",
                assert_=f"# Then: 确认验证通过",
                test_data={"max_length": constraint_value},
                markers=["constraint", "boundary"],
            ))
        
        elif constraint_name == "minimum":
            test_cases.append(TestCase(
                id=f"{constraint_id}-below",
                name=f"test_{attr.name}_minimum_below",
                description=f"测试{attr.name}最小值约束 - 低于最小值",
                test_type=TestType.UNIT,
                spec_element=attr.name,
                arrange=f"# Given: 准备值为 {constraint_value - 1}",
                act=f"# When: 验证属性",
                assert_=f"# Then: 确认验证失败",
                test_data={"minimum": constraint_value},
                markers=["constraint", "boundary", "negative"],
            ))
            test_cases.append(TestCase(
                id=f"{constraint_id}-exact",
                name=f"test_{attr.name}_minimum_exact",
                description=f"测试{attr.name}最小值约束 - 等于最小值",
                test_type=TestType.UNIT,
                spec_element=attr.name,
                arrange=f"# Given: 准备值为 {constraint_value}",
                act=f"# When: 验证属性",
                assert_=f"# Then: 确认验证通过",
                test_data={"minimum": constraint_value},
                markers=["constraint", "boundary"],
            ))
        
        elif constraint_name == "maximum":
            test_cases.append(TestCase(
                id=f"{constraint_id}-above",
                name=f"test_{attr.name}_maximum_above",
                description=f"测试{attr.name}最大值约束 - 超过最大值",
                test_type=TestType.UNIT,
                spec_element=attr.name,
                arrange=f"# Given: 准备值为 {constraint_value + 1}",
                act=f"# When: 验证属性",
                assert_=f"# Then: 确认验证失败",
                test_data={"maximum": constraint_value},
                markers=["constraint", "boundary", "negative"],
            ))
            test_cases.append(TestCase(
                id=f"{constraint_id}-exact",
                name=f"test_{attr.name}_maximum_exact",
                description=f"测试{attr.name}最大值约束 - 等于最大值",
                test_type=TestType.UNIT,
                spec_element=attr.name,
                arrange=f"# Given: 准备值为 {constraint_value}",
                act=f"# When: 验证属性",
                assert_=f"# Then: 确认验证通过",
                test_data={"maximum": constraint_value},
                markers=["constraint", "boundary"],
            ))
        
        elif constraint_name == "pattern":
            test_cases.append(TestCase(
                id=f"{constraint_id}-match",
                name=f"test_{attr.name}_pattern_match",
                description=f"测试{attr.name}正则模式约束 - 匹配",
                test_type=TestType.UNIT,
                spec_element=attr.name,
                arrange=f"# Given: 准备符合模式 '{constraint_value}' 的数据",
                act=f"# When: 验证属性",
                assert_=f"# Then: 确认验证通过",
                test_data={"pattern": constraint_value},
                markers=["constraint", "pattern"],
            ))
            test_cases.append(TestCase(
                id=f"{constraint_id}-no_match",
                name=f"test_{attr.name}_pattern_no_match",
                description=f"测试{attr.name}正则模式约束 - 不匹配",
                test_type=TestType.UNIT,
                spec_element=attr.name,
                arrange=f"# Given: 准备不符合模式 '{constraint_value}' 的数据",
                act=f"# When: 验证属性",
                assert_=f"# Then: 确认验证失败",
                test_data={"pattern": constraint_value},
                markers=["constraint", "pattern", "negative"],
            ))
        
        return test_cases
    
    def _generate_state_machine_tests(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-{spec.metadata.id}"
        
        for idx, sm in enumerate(spec.state_machines):
            sm_id = f"{base_id}-SM-{idx+1:03d}"
            
            test_cases.append(TestCase(
                id=f"{sm_id}-initial",
                name=f"test_state_machine_{self._to_snake_case(sm.name)}_initial_state",
                description=f"测试状态机: {sm.name} - 初始状态",
                test_type=TestType.UNIT,
                spec_element=sm.name,
                arrange=f"# Given: 创建新的状态机实例",
                act=f"# When: 检查初始状态",
                assert_=f"# Then: 确认状态为 '{sm.initial_state}'",
                test_data={"initial_state": sm.initial_state},
                markers=["state_machine", "initial"],
            ))
            
            for trans_idx, transition in enumerate(sm.transitions):
                test_cases.append(TestCase(
                    id=f"{sm_id}-TRANS-{trans_idx+1:03d}",
                    name=f"test_state_machine_{self._to_snake_case(sm.name)}_transition_{trans_idx+1}",
                    description=f"测试状态机: {sm.name} - 转换 {transition.from_state} -> {transition.to_state}",
                    test_type=TestType.UNIT,
                    spec_element=sm.name,
                    arrange=f"# Given: 状态机处于 '{transition.from_state}' 状态",
                    act=f"# When: 触发 '{transition.trigger}' 事件",
                    assert_=f"# Then: 确认状态转换为 '{transition.to_state}'",
                    test_data={
                        "from_state": transition.from_state,
                        "to_state": transition.to_state,
                        "trigger": transition.trigger,
                    },
                    markers=["state_machine", "transition"],
                ))
            
            for final_state in sm.final_states:
                test_cases.append(TestCase(
                    id=f"{sm_id}-FINAL-{final_state}",
                    name=f"test_state_machine_{self._to_snake_case(sm.name)}_final_state_{final_state}",
                    description=f"测试状态机: {sm.name} - 最终状态 {final_state}",
                    test_type=TestType.UNIT,
                    spec_element=sm.name,
                    arrange=f"# Given: 状态机处于 '{final_state}' 状态",
                    act=f"# When: 检查是否为最终状态",
                    assert_=f"# Then: 确认状态机已终止",
                    test_data={"final_state": final_state},
                    markers=["state_machine", "final"],
                ))
        
        return test_cases
    
    def _generate_fixtures(self, spec: SDDSpecification) -> Dict[str, str]:
        fixtures = {}
        
        if spec.attributes:
            fixtures["sample_entity"] = self._generate_sample_entity_fixture(spec)
        
        if spec.endpoints:
            fixtures["api_client"] = "client = TestClient(app)"
            fixtures["auth_headers"] = "headers = {'Authorization': 'Bearer test_token'}"
        
        return fixtures
    
    def _generate_sample_entity_fixture(self, spec: SDDSpecification) -> str:
        fixture_data = {}
        for attr in spec.attributes:
            if attr.default is not None:
                fixture_data[attr.name] = attr.default
            elif attr.example is not None:
                fixture_data[attr.name] = attr.example
            elif attr.enum_values:
                fixture_data[attr.name] = attr.enum_values[0]
            elif attr.type == "string":
                fixture_data[attr.name] = f"test_{attr.name}"
            elif attr.type in ["integer", "bigint"]:
                fixture_data[attr.name] = 1
            elif attr.type == "float":
                fixture_data[attr.name] = 1.0
            elif attr.type == "boolean":
                fixture_data[attr.name] = True
            elif attr.type == "date":
                fixture_data[attr.name] = "2024-01-01"
            elif attr.type == "datetime":
                fixture_data[attr.name] = "2024-01-01T00:00:00"
        
        return f"sample_data = {json.dumps(fixture_data, ensure_ascii=False, indent=8)}"
    
    def _generate_content(self, test_suite: TestSuite, spec: SDDSpecification) -> str:
        lines = [
            '"""',
            f'{spec.metadata.name} 测试文件',
            "",
            f"规范ID: {spec.metadata.id}",
            f"规范版本: {spec.metadata.version}",
            f"生成时间: {datetime.now().isoformat()}",
            "",
            "此文件由SDD规范测试生成器自动生成",
            '"""',
            "",
            "import pytest",
            "from datetime import date, datetime",
            "from typing import Optional, Any, Dict",
            "from pydantic import ValidationError",
            "",
        ]
        
        if spec.kind in [SpecType.INTERFACE, SpecType.API]:
            lines.extend([
                "from fastapi.testclient import TestClient",
                "from http import HTTPStatus",
                "",
            ])
        
        lines.extend([
            "",
            f"class {test_suite.name}:",
            f'    """{test_suite.description}"""',
            "",
        ])
        
        for fixture_name, fixture_code in test_suite.fixtures.items():
            lines.extend([
                f"    @pytest.fixture",
                f"    def {fixture_name}(self):",
                f"        {fixture_code}",
                "",
            ])
        
        for tc in test_suite.test_cases:
            lines.extend(self._generate_test_method(tc))
        
        return "\n".join(lines)
    
    def _generate_test_method(self, tc: TestCase) -> List[str]:
        lines = []
        
        decorators = []
        for marker in tc.markers:
            decorators.append(f"    @pytest.mark.{marker}")
        if tc.skip:
            decorators.append(f'    @pytest.mark.skip(reason="{tc.skip_reason}")')
        
        lines.extend(decorators)
        
        params = []
        if tc.test_data:
            params.append("test_data")
        
        lines.extend([
            f"    def {tc.name}(self{', ' + ', '.join(params) if params else ''}):",
            f'        """{tc.description}"""',
            f"        # Arrange",
            f"        {tc.arrange}",
            "",
            f"        # Act",
            f"        {tc.act}",
            "",
            f"        # Assert",
            f"        {tc.assert_}",
            "        pass",
            "",
        ])
        
        return lines


class JestGenerator(BaseTestGenerator):
    """Jest测试框架生成器"""
    
    def get_framework(self) -> TestFramework:
        return TestFramework.JEST
    
    def get_file_extension(self) -> str:
        return ".test.ts"
    
    def generate(self, spec: SDDSpecification) -> GeneratedTestFile:
        test_suite = self._build_test_suite(spec)
        content = self._generate_content(test_suite, spec)
        
        filename = f"{self._to_snake_case(spec.metadata.name)}{self.get_file_extension()}"
        
        return GeneratedTestFile(
            filename=filename,
            content=content,
            framework=self.get_framework(),
            test_count=len(test_suite.test_cases),
            dependencies=["jest", "@types/jest"],
        )
    
    def _build_test_suite(self, spec: SDDSpecification) -> TestSuite:
        test_cases = []
        
        if spec.kind == SpecType.ENTITY:
            test_cases.extend(self._generate_entity_tests(spec))
        elif spec.kind in [SpecType.INTERFACE, SpecType.API]:
            test_cases.extend(self._generate_api_tests(spec))
        elif spec.kind == SpecType.ACCEPTANCE:
            test_cases.extend(self._generate_acceptance_tests(spec))
        
        return TestSuite(
            name=self._to_pascal_case(spec.metadata.name),
            description=f"{spec.metadata.name} 测试套件",
            test_cases=test_cases,
        )
    
    def _generate_entity_tests(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-{spec.metadata.id}"
        
        for idx, attr in enumerate(spec.attributes):
            test_cases.append(TestCase(
                id=f"{base_id}-ATTR-{idx+1:03d}",
                name=f"should validate {attr.name} is {'required' if attr.required else 'optional'}",
                description=f"测试{attr.name}属性验证",
                test_type=TestType.UNIT,
                spec_element=attr.name,
                arrange=f"// 准备测试数据",
                act=f"// 验证属性",
                assert_=f"// 断言结果",
                markers=[],
            ))
        
        return test_cases
    
    def _generate_api_tests(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-{spec.metadata.id}"
        
        for idx, endpoint in enumerate(spec.endpoints):
            test_cases.append(TestCase(
                id=f"{base_id}-EP-{idx+1:03d}",
                name=f"should {endpoint.name} return success",
                description=f"测试{endpoint.name}成功场景",
                test_type=TestType.API,
                spec_element=endpoint.name,
                arrange=f"// 准备请求数据",
                act=f"// 发送{endpoint.method}请求",
                assert_=f"// 断言响应",
                markers=[],
            ))
        
        return test_cases
    
    def _generate_acceptance_tests(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-{spec.metadata.id}"
        
        for idx, scenario in enumerate(spec.scenarios):
            test_cases.append(TestCase(
                id=f"{base_id}-SCENE-{idx+1:03d}",
                name=f"should {scenario.name}",
                description=f"验收测试: {scenario.name}",
                test_type=TestType.ACCEPTANCE,
                spec_element=scenario.name,
                arrange=f"// Given: {scenario.given}",
                act=f"// When: {scenario.when}",
                assert_=f"// Then: {scenario.then}",
                test_data=scenario.test_data,
                markers=[],
            ))
        
        return test_cases
    
    def _generate_content(self, test_suite: TestSuite, spec: SDDSpecification) -> str:
        lines = [
            f"/**",
            f" * {spec.metadata.name} 测试文件",
            f" *",
            f" * 规范ID: {spec.metadata.id}",
            f" * 规范版本: {spec.metadata.version}",
            f" * 生成时间: {datetime.now().isoformat()}",
            f" */",
            "",
            f"import {{ describe, it, expect, beforeEach, afterEach }} from '@jest/globals';",
            "",
        ]
        
        if spec.attributes:
            lines.extend([
                f"import {{ {self._to_pascal_case(spec.metadata.name)} }} from '../models/{self._to_snake_case(spec.metadata.name)}';",
                "",
            ])
        
        lines.extend([
            f"describe('{test_suite.name}', () => {{",
            "",
        ])
        
        for tc in test_suite.test_cases:
            lines.extend(self._generate_test_case(tc))
        
        lines.append("});")
        
        return "\n".join(lines)
    
    def _generate_test_case(self, tc: TestCase) -> List[str]:
        lines = [
            f"  it('{tc.name}', () => {{",
            f"    // Arrange",
            f"    {tc.arrange}",
            "",
            f"    // Act",
            f"    {tc.act}",
            "",
            f"    // Assert",
            f"    {tc.assert_}",
            f"    expect(true).toBe(true);",
            f"  }});",
            "",
        ]
        return lines


class PlaywrightGenerator(BaseTestGenerator):
    """Playwright E2E测试框架生成器"""
    
    def get_framework(self) -> TestFramework:
        return TestFramework.PLAYWRIGHT
    
    def get_file_extension(self) -> str:
        return ".spec.ts"
    
    def generate(self, spec: SDDSpecification) -> GeneratedTestFile:
        test_suite = self._build_test_suite(spec)
        content = self._generate_content(test_suite, spec)
        
        filename = f"{self._to_snake_case(spec.metadata.name)}.e2e{self.get_file_extension()}"
        
        return GeneratedTestFile(
            filename=filename,
            content=content,
            framework=self.get_framework(),
            test_count=len(test_suite.test_cases),
            dependencies=["@playwright/test"],
        )
    
    def _build_test_suite(self, spec: SDDSpecification) -> TestSuite:
        test_cases = []
        
        if spec.kind in [SpecType.INTERFACE, SpecType.API]:
            test_cases.extend(self._generate_e2e_api_tests(spec))
        elif spec.kind == SpecType.ACCEPTANCE:
            test_cases.extend(self._generate_e2e_acceptance_tests(spec))
        else:
            test_cases.extend(self._generate_e2e_functional_tests(spec))
        
        return TestSuite(
            name=self._to_pascal_case(spec.metadata.name),
            description=f"{spec.metadata.name} E2E测试套件",
            test_cases=test_cases,
        )
    
    def _generate_e2e_api_tests(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-E2E-{spec.metadata.id}"
        
        for idx, endpoint in enumerate(spec.endpoints):
            test_cases.append(TestCase(
                id=f"{base_id}-EP-{idx+1:03d}",
                name=f"should successfully call {endpoint.name} API",
                description=f"E2E测试: {endpoint.name} API",
                test_type=TestType.E2E,
                spec_element=endpoint.name,
                arrange=f"// 准备API请求",
                act=f"// 发送{endpoint.method}请求到{endpoint.path}",
                assert_=f"// 验证响应",
                timeout=60000,
                markers=["e2e", "api"],
            ))
        
        return test_cases
    
    def _generate_e2e_acceptance_tests(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-E2E-{spec.metadata.id}"
        
        for idx, scenario in enumerate(spec.scenarios):
            test_cases.append(TestCase(
                id=f"{base_id}-SCENE-{idx+1:03d}",
                name=f"should complete {scenario.name} user flow",
                description=f"E2E验收测试: {scenario.name}",
                test_type=TestType.E2E,
                spec_element=scenario.name,
                arrange=f"// Given: {scenario.given}",
                act=f"// When: {scenario.when}",
                assert_=f"// Then: {scenario.then}",
                test_data=scenario.test_data,
                timeout=60000,
                markers=["e2e", "acceptance"],
            ))
        
        return test_cases
    
    def _generate_e2e_functional_tests(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-E2E-{spec.metadata.id}"
        
        test_cases.append(TestCase(
            id=f"{base_id}-SMOKE-001",
            name=f"should load {spec.metadata.name} page successfully",
            description=f"冒烟测试: {spec.metadata.name}页面加载",
            test_type=TestType.E2E,
            spec_element="page_load",
            arrange=f"// 打开浏览器",
            act=f"// 导航到页面",
            assert_=f"// 验证页面加载成功",
            timeout=30000,
            markers=["e2e", "smoke"],
        ))
        
        return test_cases
    
    def _generate_content(self, test_suite: TestSuite, spec: SDDSpecification) -> str:
        lines = [
            f"/**",
            f" * {spec.metadata.name} E2E测试文件",
            f" *",
            f" * 规范ID: {spec.metadata.id}",
            f" * 规范版本: {spec.metadata.version}",
            f" * 生成时间: {datetime.now().isoformat()}",
            f" */",
            "",
            f"import {{ test, expect }} from '@playwright/test';",
            "",
        ]
        
        if spec.endpoints:
            lines.extend([
                f"const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';",
                "",
            ])
        
        for tc in test_suite.test_cases:
            lines.extend(self._generate_test_case(tc))
        
        return "\n".join(lines)
    
    def _generate_test_case(self, tc: TestCase) -> List[str]:
        lines = [
            f"test('{tc.name}', async ({{ page, request }}) => {{",
            f"  // Arrange",
            f"  {tc.arrange}",
            "",
            f"  // Act",
            f"  {tc.act}",
            "",
            f"  // Assert",
            f"  {tc.assert_}",
            f"  expect(true).toBeTruthy();",
            f"}});",
            "",
        ]
        return lines


class MultiFrameworkTestGenerator:
    """多框架测试生成器"""
    
    def __init__(self):
        self.generators = {
            TestFramework.PYTEST: PytestGenerator(),
            TestFramework.JEST: JestGenerator(),
            TestFramework.PLAYWRIGHT: PlaywrightGenerator(),
        }
    
    def generate(
        self,
        spec: SDDSpecification,
        frameworks: List[TestFramework] = None,
        output_dir: str = "tests/generated"
    ) -> List[GeneratedTestFile]:
        if frameworks is None:
            frameworks = [TestFramework.PYTEST]
        
        results = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for framework in frameworks:
            generator = self.generators.get(framework)
            if not generator:
                print(f"警告: 不支持的测试框架 {framework}")
                continue
            
            generated = generator.generate(spec)
            
            file_path = output_path / generated.filename
            file_path.write_text(generated.content, encoding="utf-8")
            
            results.append(generated)
            print(f"生成测试文件: {file_path} ({generated.test_count} 个测试用例)")
        
        return results
    
    def generate_from_spec_file(
        self,
        spec_path: str,
        frameworks: List[TestFramework] = None,
        output_dir: str = "tests/generated"
    ) -> List[GeneratedTestFile]:
        try:
            from pipeline.sdd_spec_parser_enhanced import EnhancedSDDSpecParser
            parser_class = EnhancedSDDSpecParser
        except ImportError:
            from skillscripts.pipeline.sdd_spec_parser_enhanced import EnhancedSDDSpecParser
            parser_class = EnhancedSDDSpecParser
        
        with open(spec_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        parser = parser_class()
        spec, validation_result = parser.parse(
            content=content,
            source_format="yaml",
            source_path=str(spec_path)
        )
        
        if not validation_result.is_valid:
            print("规范验证失败:")
            for err in validation_result.errors:
                print(f"  - [{err.path}] {err.message}")
            return []
        
        return self.generate(spec, frameworks, output_dir)


@dataclass
class CoverageReport:
    """测试覆盖率报告"""
    spec_id: str
    spec_name: str
    total_elements: int
    covered_elements: int
    coverage_percentage: float
    element_coverage: Dict[str, bool] = field(default_factory=dict)
    uncovered_elements: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class TestCoverageValidator:
    """测试覆盖率验证器"""
    
    def __init__(self):
        self.coverage_thresholds = {
            "entity": 0.85,
            "api": 0.80,
            "business_rule": 0.90,
            "constraint": 0.85,
            "state_machine": 0.80,
        }
    
    def validate_coverage(
        self,
        spec: SDDSpecification,
        test_cases: List[TestCase]
    ) -> CoverageReport:
        element_coverage = {}
        total_elements = 0
        covered_elements = 0
        
        if spec.attributes:
            for attr in spec.attributes:
                element_key = f"attribute.{attr.name}"
                total_elements += 1
                is_covered = any(
                    tc.spec_element == attr.name or attr.name in tc.name
                    for tc in test_cases
                )
                element_coverage[element_key] = is_covered
                if is_covered:
                    covered_elements += 1
        
        if spec.endpoints:
            for endpoint in spec.endpoints:
                element_key = f"endpoint.{endpoint.name}"
                total_elements += 1
                is_covered = any(
                    tc.spec_element == endpoint.name or endpoint.name in tc.name
                    for tc in test_cases
                )
                element_coverage[element_key] = is_covered
                if is_covered:
                    covered_elements += 1
        
        if hasattr(spec, 'conditional_rules') and spec.conditional_rules:
            for rule in spec.conditional_rules:
                element_key = f"business_rule.{rule.name}"
                total_elements += 1
                is_covered = any(
                    tc.spec_element == rule.name or rule.name in tc.name
                    for tc in test_cases
                )
                element_coverage[element_key] = is_covered
                if is_covered:
                    covered_elements += 1
        
        if hasattr(spec, 'constraints') and spec.constraints:
            for idx, constraint in enumerate(spec.constraints):
                constraint_name = constraint.get("name", f"constraint_{idx}")
                element_key = f"constraint.{constraint_name}"
                total_elements += 1
                is_covered = any(
                    tc.spec_element == constraint_name or constraint_name in tc.name
                    for tc in test_cases
                )
                element_coverage[element_key] = is_covered
                if is_covered:
                    covered_elements += 1
        
        if hasattr(spec, 'state_machines') and spec.state_machines:
            for sm in spec.state_machines:
                element_key = f"state_machine.{sm.name}"
                total_elements += 1
                is_covered = any(
                    tc.spec_element == sm.name or sm.name in tc.name
                    for tc in test_cases
                )
                element_coverage[element_key] = is_covered
                if is_covered:
                    covered_elements += 1
        
        coverage_percentage = (covered_elements / total_elements * 100) if total_elements > 0 else 0
        
        uncovered_elements = [
            key for key, covered in element_coverage.items()
            if not covered
        ]
        
        recommendations = self._generate_recommendations(
            uncovered_elements, coverage_percentage
        )
        
        return CoverageReport(
            spec_id=spec.metadata.id,
            spec_name=spec.metadata.name,
            total_elements=total_elements,
            covered_elements=covered_elements,
            coverage_percentage=coverage_percentage,
            element_coverage=element_coverage,
            uncovered_elements=uncovered_elements,
            recommendations=recommendations,
        )
    
    def _generate_recommendations(
        self,
        uncovered_elements: List[str],
        coverage_percentage: float
    ) -> List[str]:
        recommendations = []
        
        if coverage_percentage < 80:
            recommendations.append("测试覆盖率低于80%，建议补充测试用例")
        
        for element in uncovered_elements:
            element_type = element.split('.')[0]
            if element_type == "business_rule":
                recommendations.append(f"业务规则 '{element}' 未被测试覆盖，建议添加业务逻辑测试")
            elif element_type == "constraint":
                recommendations.append(f"约束条件 '{element}' 未被测试覆盖，建议添加边界条件测试")
            elif element_type == "attribute":
                recommendations.append(f"属性 '{element}' 未被测试覆盖，建议添加属性验证测试")
            elif element_type == "endpoint":
                recommendations.append(f"接口 '{element}' 未被测试覆盖，建议添加API测试")
            elif element_type == "state_machine":
                recommendations.append(f"状态机 '{element}' 未被测试覆盖，建议添加状态转换测试")
        
        return recommendations
    
    def check_threshold(
        self,
        report: CoverageReport,
        spec_type: str
    ) -> Tuple[bool, str]:
        threshold = self.coverage_thresholds.get(spec_type, 0.80)
        coverage_decimal = report.coverage_percentage / 100
        
        if coverage_decimal >= threshold:
            return True, f"覆盖率达标: {report.coverage_percentage:.2f}% >= {threshold*100:.2f}%"
        else:
            return False, f"覆盖率不达标: {report.coverage_percentage:.2f}% < {threshold*100:.2f}%"


class BingbuTestFirstIntegration:
    """兵部测试先行流程集成"""
    
    def __init__(self):
        self.generator = MultiFrameworkTestGenerator()
        self.validator = TestCoverageValidator()
    
    def execute_test_first_workflow(
        self,
        spec_path: str,
        output_dir: str = "tests/generated",
        frameworks: List[TestFramework] = None
    ) -> Dict[str, Any]:
        if frameworks is None:
            frameworks = [TestFramework.PYTEST]
        
        workflow_result = {
            "workflow_id": f"TF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "spec_path": spec_path,
            "timestamp": datetime.now().isoformat(),
            "stages": {},
            "success": False,
            "errors": [],
        }
        
        try:
            workflow_result["stages"]["parse_spec"] = {
                "status": "in_progress",
                "message": "解析SDD规范文件",
            }
            
            from pipeline.sdd_spec_parser_enhanced import EnhancedSDDSpecParser
            parser = EnhancedSDDSpecParser()
            
            with open(spec_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            spec, validation_result = parser.parse(
                content,
                source_format="yaml",
                source_path=spec_path
            )
            
            if not validation_result.is_valid:
                workflow_result["stages"]["parse_spec"] = {
                    "status": "failed",
                    "message": "规范验证失败",
                    "errors": [err.message for err in validation_result.errors],
                }
                workflow_result["errors"].append("规范验证失败")
                return workflow_result
            
            workflow_result["stages"]["parse_spec"] = {
                "status": "completed",
                "message": "规范解析成功",
                "spec_id": spec.metadata.id,
                "spec_name": spec.metadata.name,
            }
            
            workflow_result["stages"]["generate_tests"] = {
                "status": "in_progress",
                "message": "生成测试用例",
            }
            
            generated_files = self.generator.generate(spec, frameworks, output_dir)
            
            workflow_result["stages"]["generate_tests"] = {
                "status": "completed",
                "message": f"生成 {len(generated_files)} 个测试文件",
                "files": [
                    {
                        "filename": f.filename,
                        "test_count": f.test_count,
                        "framework": f.framework.value,
                    }
                    for f in generated_files
                ],
            }
            
            workflow_result["stages"]["validate_coverage"] = {
                "status": "in_progress",
                "message": "验证测试覆盖率",
            }
            
            all_test_cases = []
            for framework in frameworks:
                gen = self.generator.generators.get(framework)
                if gen:
                    test_suite = gen._build_test_suite(spec)
                    all_test_cases.extend(test_suite.test_cases)
            
            coverage_report = self.validator.validate_coverage(spec, all_test_cases)
            
            spec_type = spec.kind.value.lower().replace("spec", "")
            passed, message = self.validator.check_threshold(coverage_report, spec_type)
            
            workflow_result["stages"]["validate_coverage"] = {
                "status": "completed" if passed else "warning",
                "message": message,
                "coverage_report": {
                    "total_elements": coverage_report.total_elements,
                    "covered_elements": coverage_report.covered_elements,
                    "coverage_percentage": coverage_report.coverage_percentage,
                    "uncovered_elements": coverage_report.uncovered_elements,
                    "recommendations": coverage_report.recommendations,
                },
            }
            
            workflow_result["stages"]["generate_report"] = {
                "status": "in_progress",
                "message": "生成测试报告",
            }
            
            report_path = Path(output_dir) / f"test_report_{spec.metadata.id}.json"
            self._save_test_report(workflow_result, coverage_report, report_path)
            
            workflow_result["stages"]["generate_report"] = {
                "status": "completed",
                "message": f"测试报告已保存: {report_path}",
                "report_path": str(report_path),
            }
            
            workflow_result["success"] = True
            
        except Exception as e:
            workflow_result["success"] = False
            workflow_result["errors"].append(str(e))
            import traceback
            workflow_result["traceback"] = traceback.format_exc()
        
        return workflow_result
    
    def _save_test_report(
        self,
        workflow_result: Dict[str, Any],
        coverage_report: CoverageReport,
        report_path: Path
    ):
        report = {
            "workflow": workflow_result,
            "coverage": {
                "spec_id": coverage_report.spec_id,
                "spec_name": coverage_report.spec_name,
                "total_elements": coverage_report.total_elements,
                "covered_elements": coverage_report.covered_elements,
                "coverage_percentage": coverage_report.coverage_percentage,
                "uncovered_elements": coverage_report.uncovered_elements,
                "recommendations": coverage_report.recommendations,
                "timestamp": coverage_report.timestamp,
            },
        }
        
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def generate_test_cases_for_bingbu(
        self,
        spec_path: str,
        output_dir: str = "tests/generated"
    ) -> Dict[str, Any]:
        return self.execute_test_first_workflow(
            spec_path=spec_path,
            output_dir=output_dir,
            frameworks=[TestFramework.PYTEST]
        )


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="SDD规范多框架测试生成器 v2.0")
    parser.add_argument("spec_file", help="规范文件路径")
    parser.add_argument(
        "--framework",
        "-f",
        choices=["pytest", "jest", "playwright", "all"],
        default="pytest",
        help="测试框架 (默认: pytest)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="tests/generated",
        help="输出目录 (默认: tests/generated)"
    )
    parser.add_argument(
        "--test-first",
        action="store_true",
        help="启用兵部测试先行流程"
    )
    parser.add_argument(
        "--validate-coverage",
        action="store_true",
        help="验证测试覆盖率"
    )
    
    args = parser.parse_args()
    
    if args.framework == "all":
        frameworks = [TestFramework.PYTEST, TestFramework.JEST, TestFramework.PLAYWRIGHT]
    else:
        framework_map = {
            "pytest": TestFramework.PYTEST,
            "jest": TestFramework.JEST,
            "playwright": TestFramework.PLAYWRIGHT,
        }
        frameworks = [framework_map[args.framework]]
    
    if args.test_first:
        integration = BingbuTestFirstIntegration()
        result = integration.execute_test_first_workflow(
            spec_path=args.spec_file,
            output_dir=args.output,
            frameworks=frameworks
        )
        
        print(f"\n{'='*60}")
        print(f"兵部测试先行流程执行结果")
        print(f"{'='*60}")
        print(f"工作流ID: {result['workflow_id']}")
        print(f"执行状态: {'成功' if result['success'] else '失败'}")
        print(f"\n执行阶段:")
        
        for stage_name, stage_info in result['stages'].items():
            status_emoji = {
                "completed": "✓",
                "in_progress": "⏳",
                "failed": "✗",
                "warning": "⚠",
            }.get(stage_info['status'], "?")
            print(f"  {status_emoji} {stage_name}: {stage_info['message']}")
            
            if stage_name == "generate_tests" and "files" in stage_info:
                for file_info in stage_info['files']:
                    print(f"      - {file_info['filename']}: {file_info['test_count']} 个测试用例")
            
            if stage_name == "validate_coverage" and "coverage_report" in stage_info:
                report = stage_info['coverage_report']
                print(f"      覆盖率: {report['coverage_percentage']:.2f}%")
                print(f"      覆盖元素: {report['covered_elements']}/{report['total_elements']}")
                if report['uncovered_elements']:
                    print(f"      未覆盖元素: {', '.join(report['uncovered_elements'][:3])}")
        
        if result['errors']:
            print(f"\n错误信息:")
            for error in result['errors']:
                print(f"  - {error}")
        
        print(f"{'='*60}\n")
        
    elif args.validate_coverage:
        generator = MultiFrameworkTestGenerator()
        
        try:
            from pipeline.sdd_spec_parser_enhanced import EnhancedSDDSpecParser
            parser_obj = EnhancedSDDSpecParser()
            spec, validation_result = parser_obj.parse_file(args.spec_file)
            
            if not validation_result.is_valid:
                print("规范验证失败:")
                for err in validation_result.errors:
                    print(f"  - [{err.path}] {err.message}")
                return
            
            all_test_cases = []
            for framework in frameworks:
                gen = generator.generators.get(framework)
                if gen:
                    test_suite = gen._build_test_suite(spec)
                    all_test_cases.extend(test_suite.test_cases)
            
            validator = TestCoverageValidator()
            report = validator.validate_coverage(spec, all_test_cases)
            
            print(f"\n{'='*60}")
            print(f"测试覆盖率报告")
            print(f"{'='*60}")
            print(f"规范ID: {report.spec_id}")
            print(f"规范名称: {report.spec_name}")
            print(f"总元素数: {report.total_elements}")
            print(f"已覆盖元素: {report.covered_elements}")
            print(f"覆盖率: {report.coverage_percentage:.2f}%")
            
            if report.uncovered_elements:
                print(f"\n未覆盖元素:")
                for element in report.uncovered_elements:
                    print(f"  - {element}")
            
            if report.recommendations:
                print(f"\n建议:")
                for rec in report.recommendations:
                    print(f"  - {rec}")
            
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        generator = MultiFrameworkTestGenerator()
        
        try:
            results = generator.generate_from_spec_file(args.spec_file, frameworks, args.output)
            
            print(f"\n生成完成:")
            for result in results:
                print(f"  - {result.filename}: {result.test_count} 个测试用例 ({result.framework.value})")
        
        except FileNotFoundError as e:
            print(f"错误: {e}")
        except Exception as e:
            print(f"生成错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
