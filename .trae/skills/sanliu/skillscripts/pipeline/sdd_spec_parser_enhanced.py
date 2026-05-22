#!/usr/bin/env python3
"""
SDD规范解析器增强版 v2.1

支持功能：
1. 复杂规范解析（嵌套结构、条件规则、状态机定义、复杂类型系统）
2. 规范到测试用例自动转换功能（智能测试骨架生成）
3. 测试覆盖率映射报告生成（详细覆盖率分析）
4. 规范完整性验证（多维度验证机制）
5. CLI命令行接口

增强功能：
- 支持复杂类型系统：泛型、联合类型、可选类型、映射类型
- 智能测试用例生成：边界值、异常场景、数据驱动测试
- 多维度覆盖率分析：语句、分支、条件、路径覆盖
- 完整性验证：依赖关系、版本兼容性、语义一致性

作者: SDD Pipeline Team
版本: 2.1.0
"""

import json
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, Generic, TypeVar
import yaml
import hashlib
import copy


# ============================================================================
# 枚举类型定义
# ============================================================================

class SpecFormat(Enum):
    """规范文件格式枚举"""
    MARKDOWN = "markdown"
    YAML = "yaml"
    JSON = "json"


class SpecType(Enum):
    """规范类型枚举"""
    ENTITY = "EntitySpec"
    INTERFACE = "InterfaceSpec"
    API = "ApiSpec"
    BUSINESS_RULE = "BusinessRuleSpec"
    CONSTRAINT = "ConstraintSpec"
    ACCEPTANCE = "AcceptanceSpec"
    FUNCTION = "FunctionSpec"
    STATE_MACHINE = "StateMachineSpec"
    CONDITIONAL = "ConditionalSpec"
    DATA_MODEL = "DataModelSpec"
    WORKFLOW = "WorkflowSpec"


class ValidationSeverity(Enum):
    """验证问题严重程度枚举"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class CoverageStatus(Enum):
    """覆盖率状态枚举"""
    COVERED = "covered"
    PARTIAL = "partial"
    NOT_COVERED = "not_covered"
    EXCLUDED = "excluded"


class TestType(Enum):
    """测试类型枚举"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    API = "api"
    ACCEPTANCE = "acceptance"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CONTRACT = "contract"


class ComplexTypeKind(Enum):
    """复杂类型种类枚举"""
    GENERIC = "generic"
    UNION = "union"
    OPTIONAL = "optional"
    MAPPED = "mapped"
    TUPLE = "tuple"
    RECORD = "record"
    LITERAL = "literal"
    INTERSECTION = "intersection"


class CoverageMetricType(Enum):
    """覆盖率度量类型枚举"""
    STATEMENT = "statement"
    BRANCH = "branch"
    CONDITION = "condition"
    PATH = "path"
    FUNCTION = "function"
    LINE = "line"


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class ValidationError:
    """
    验证错误数据类
    
    用于记录规范验证过程中发现的问题，包括错误路径、消息、严重程度和建议。
    """
    path: str
    message: str
    severity: ValidationSeverity
    suggestion: str = ""
    code: str = ""
    line_number: Optional[int] = None
    context: Optional[str] = None


@dataclass
class ValidationResult:
    """
    验证结果数据类
    
    汇总所有验证错误、警告和信息，提供合并和添加问题的方法。
    """
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    info: List[ValidationError] = field(default_factory=list)
    hints: List[ValidationError] = field(default_factory=list)

    def add_error(self, path: str, message: str, suggestion: str = "", code: str = "", 
                  line_number: Optional[int] = None, context: Optional[str] = None):
        """添加错误级别的验证问题"""
        self.errors.append(ValidationError(
            path, message, ValidationSeverity.ERROR, suggestion, code, line_number, context
        ))
        self.is_valid = False

    def add_warning(self, path: str, message: str, suggestion: str = "", code: str = "",
                    line_number: Optional[int] = None, context: Optional[str] = None):
        """添加警告级别的验证问题"""
        self.warnings.append(ValidationError(
            path, message, ValidationSeverity.WARNING, suggestion, code, line_number, context
        ))

    def add_info(self, path: str, message: str, suggestion: str = "", code: str = "",
                 line_number: Optional[int] = None, context: Optional[str] = None):
        """添加信息级别的验证问题"""
        self.info.append(ValidationError(
            path, message, ValidationSeverity.INFO, suggestion, code, line_number, context
        ))

    def add_hint(self, path: str, message: str, suggestion: str = "", code: str = "",
                 line_number: Optional[int] = None, context: Optional[str] = None):
        """添加提示级别的验证问题"""
        self.hints.append(ValidationError(
            path, message, ValidationSeverity.HINT, suggestion, code, line_number, context
        ))

    def merge(self, other: "ValidationResult"):
        """合并另一个验证结果到当前结果"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info.extend(other.info)
        self.hints.extend(other.hints)
        if not other.is_valid:
            self.is_valid = False

    def get_summary(self) -> Dict[str, int]:
        """获取验证结果摘要统计"""
        return {
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "info": len(self.info),
            "hints": len(self.hints),
            "total_issues": len(self.errors) + len(self.warnings) + len(self.info) + len(self.hints)
        }


@dataclass
class ComplexType:
    """
    复杂类型定义数据类
    
    支持泛型、联合类型、可选类型、映射类型等复杂类型定义。
    """
    kind: ComplexTypeKind
    name: str
    type_params: List[str] = field(default_factory=list)
    type_args: List["ComplexType"] = field(default_factory=list)
    base_type: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_type_string(self) -> str:
        """将复杂类型转换为类型字符串表示"""
        if self.kind == ComplexTypeKind.GENERIC:
            if self.type_args:
                args = ", ".join(arg.to_type_string() for arg in self.type_args)
                return f"{self.name}<{args}>"
            return self.name
        elif self.kind == ComplexTypeKind.UNION:
            return " | ".join(arg.to_type_string() for arg in self.type_args)
        elif self.kind == ComplexTypeKind.OPTIONAL:
            if self.type_args:
                return f"Optional[{self.type_args[0].to_type_string()}]"
            return "Optional[Any]"
        elif self.kind == ComplexTypeKind.MAPPED:
            if len(self.type_args) >= 2:
                return f"Dict[{self.type_args[0].to_type_string()}, {self.type_args[1].to_type_string()}]"
            return "Dict[str, Any]"
        elif self.kind == ComplexTypeKind.TUPLE:
            elements = ", ".join(arg.to_type_string() for arg in self.type_args)
            return f"Tuple[{elements}]"
        elif self.kind == ComplexTypeKind.RECORD:
            return f"Record[{self.name}]"
        elif self.kind == ComplexTypeKind.LITERAL:
            return f"Literal[{self.name}]"
        elif self.kind == ComplexTypeKind.INTERSECTION:
            return " & ".join(arg.to_type_string() for arg in self.type_args)
        return self.name


@dataclass
class NestedStructure:
    """
    嵌套结构数据类
    
    用于表示规范中的嵌套数据结构，支持多层级嵌套。
    """
    name: str
    type: str
    description: str = ""
    children: List["NestedStructure"] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    depth: int = 0
    complex_type: Optional[ComplexType] = None
    is_recursive: bool = False
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ConditionalRule:
    """
    条件规则数据类
    
    表示规范中的条件判断规则，支持复杂的条件表达式。
    """
    id: str
    name: str
    condition: str
    then_branch: Dict[str, Any]
    else_branch: Optional[Dict[str, Any]] = None
    priority: int = 0
    description: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class StateTransition:
    """
    状态转换数据类
    
    表示状态机中的状态转换规则。
    """
    from_state: str
    to_state: str
    trigger: str
    guard: Optional[str] = None
    action: Optional[str] = None
    description: str = ""
    priority: int = 0
    side_effects: List[str] = field(default_factory=list)


@dataclass
class StateDefinition:
    """
    状态定义数据类
    
    表示状态机中的单个状态定义。
    """
    name: str
    type: str = "normal"
    entry_action: Optional[str] = None
    exit_action: Optional[str] = None
    description: str = ""
    sub_states: List["StateDefinition"] = field(default_factory=list)
    on_enter_events: List[str] = field(default_factory=list)
    on_exit_events: List[str] = field(default_factory=list)


@dataclass
class StateMachine:
    """
    状态机数据类
    
    完整的状态机定义，包含状态、转换和事件。
    """
    id: str
    name: str
    initial_state: str
    states: List[StateDefinition] = field(default_factory=list)
    transitions: List[StateTransition] = field(default_factory=list)
    final_states: List[str] = field(default_factory=list)
    description: str = ""
    events: List[str] = field(default_factory=list)
    history_states: List[str] = field(default_factory=list)


@dataclass
class SpecAttribute:
    """
    规范属性数据类
    
    表示实体或接口中的属性定义，支持复杂类型。
    """
    name: str
    type: str
    description: str = ""
    required: bool = True
    unique: bool = False
    default: Any = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    enum_values: List[str] = field(default_factory=list)
    example: Any = None
    nested: Optional[NestedStructure] = None
    complex_type: Optional[ComplexType] = None
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    deprecated: bool = False
    deprecation_message: str = ""
    since_version: str = ""


@dataclass
class SpecEndpoint:
    """
    规范端点数据类
    
    表示API接口的端点定义。
    """
    name: str
    method: str
    path: str
    description: str = ""
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)
    authentication: bool = False
    rate_limit: Optional[int] = None
    deprecated: bool = False
    version_added: str = ""
    version_deprecated: str = ""
    tags: List[str] = field(default_factory=list)
    security_schemes: List[str] = field(default_factory=list)


@dataclass
class SpecScenario:
    """
    规范场景数据类
    
    表示验收测试场景定义（BDD风格）。
    """
    name: str
    given: str
    when: str
    then: str
    test_data: Dict[str, Any] = field(default_factory=dict)
    priority: str = "medium"
    tags: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    background: Optional[str] = None


@dataclass
class SpecMetadata:
    """
    规范元数据数据类
    
    包含规范的基本信息。
    """
    id: str
    name: str
    version: str
    namespace: str = "default"
    status: str = "draft"
    author: str = ""
    created: str = ""
    modified: str = ""
    tags: List[str] = field(default_factory=list)
    annotations: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    extends: Optional[str] = None
    compatibility_version: str = ""


@dataclass
class CoverageMapping:
    """
    覆盖率映射数据类
    
    记录规范元素与测试用例的映射关系。
    """
    spec_element: str
    spec_element_type: str
    test_cases: List[str] = field(default_factory=list)
    coverage_status: CoverageStatus = CoverageStatus.NOT_COVERED
    coverage_percentage: float = 0.0
    coverage_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoverageMetric:
    """
    覆盖率度量数据类
    
    记录特定类型的覆盖率统计。
    """
    metric_type: CoverageMetricType
    total: int
    covered: int
    percentage: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCase:
    """
    测试用例数据类
    
    表示自动生成的测试用例。
    """
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
    priority: str = "medium"
    expected_result: Optional[str] = None
    assertions: List[Dict[str, Any]] = field(default_factory=list)
    test_code: Optional[str] = None
    parameterized: bool = False
    parameter_values: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TestSuite:
    """
    测试套件数据类
    
    包含一组相关的测试用例。
    """
    name: str
    description: str
    test_cases: List[TestCase] = field(default_factory=list)
    fixtures: Dict[str, str] = field(default_factory=dict)
    setup: str = ""
    teardown: str = ""
    imports: List[str] = field(default_factory=list)
    conftest: str = ""
    shared_fixtures: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoverageReport:
    """
    覆盖率报告数据类
    
    完整的覆盖率分析报告。
    """
    spec_id: str
    spec_name: str
    generated_at: str
    total_elements: int
    covered_elements: int
    partial_elements: int
    not_covered_elements: int
    overall_coverage: float
    mappings: List[CoverageMapping] = field(default_factory=list)
    test_suites: List[TestSuite] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metrics: List[CoverageMetric] = field(default_factory=list)
    trends: Dict[str, Any] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SDDSpecification:
    """
    SDD规范数据类
    
    完整的规范定义，包含所有规范元素。
    """
    api_version: str
    kind: SpecType
    metadata: SpecMetadata
    spec: Dict[str, Any]
    raw_content: str = ""
    source_format: SpecFormat = SpecFormat.YAML
    source_path: str = ""

    attributes: List[SpecAttribute] = field(default_factory=list)
    endpoints: List[SpecEndpoint] = field(default_factory=list)
    scenarios: List[SpecScenario] = field(default_factory=list)
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    nested_structures: List[NestedStructure] = field(default_factory=list)
    conditional_rules: List[ConditionalRule] = field(default_factory=list)
    state_machines: List[StateMachine] = field(default_factory=list)
    type_definitions: List[ComplexType] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)


# ============================================================================
# 复杂类型解析器
# ============================================================================

class ComplexTypeParser:
    """
    复杂类型解析器
    
    支持解析泛型、联合类型、可选类型、映射类型等复杂类型定义。
    提供类型验证和类型兼容性检查功能。
    """
    
    # 支持的基础类型映射
    PRIMITIVE_TYPES = {
        "string": str, "str": str,
        "integer": int, "int": int, "bigint": int,
        "float": float, "double": float, "number": float,
        "boolean": bool, "bool": bool,
        "null": type(None), "none": type(None),
        "any": object,
    }
    
    # 支持的容器类型
    CONTAINER_TYPES = {
        "array": list, "list": list,
        "object": dict, "dict": dict, "map": dict,
        "set": set,
        "tuple": tuple,
    }
    
    def __init__(self):
        """初始化复杂类型解析器"""
        self.type_registry: Dict[str, ComplexType] = {}
        self._register_builtin_types()
    
    def _register_builtin_types(self):
        """注册内置类型定义"""
        builtin_types = [
            ComplexType(ComplexTypeKind.GENERIC, "Array", type_params=["T"]),
            ComplexType(ComplexTypeKind.GENERIC, "List", type_params=["T"]),
            ComplexType(ComplexTypeKind.GENERIC, "Dict", type_params=["K", "V"]),
            ComplexType(ComplexTypeKind.GENERIC, "Map", type_params=["K", "V"]),
            ComplexType(ComplexTypeKind.GENERIC, "Set", type_params=["T"]),
            ComplexType(ComplexTypeKind.GENERIC, "Optional", type_params=["T"]),
            ComplexType(ComplexTypeKind.GENERIC, "Promise", type_params=["T"]),
            ComplexType(ComplexTypeKind.GENERIC, "Result", type_params=["T", "E"]),
        ]
        for t in builtin_types:
            self.type_registry[t.name.lower()] = t
    
    def parse_type_string(self, type_str: str) -> ComplexType:
        """
        解析类型字符串为复杂类型对象
        
        支持的格式：
        - 基础类型: "string", "integer", "boolean"
        - 泛型: "List<string>", "Dict<string, integer>"
        - 联合类型: "string | integer", "string | null"
        - 可选类型: "string?", "Optional<string>"
        - 元组: "[string, integer, boolean]"
        - 映射类型: "{[key: string]: integer}"
        
        Args:
            type_str: 类型字符串
            
        Returns:
            ComplexType: 解析后的复杂类型对象
        """
        type_str = type_str.strip()
        
        # 处理可选类型简写 (string?)
        if type_str.endswith("?"):
            inner_type = self.parse_type_string(type_str[:-1])
            return ComplexType(
                kind=ComplexTypeKind.OPTIONAL,
                name="Optional",
                type_args=[inner_type]
            )
        
        # 处理联合类型 (string | integer)
        if "|" in type_str:
            union_parts = [p.strip() for p in type_str.split("|")]
            type_args = [self.parse_type_string(p) for p in union_parts]
            return ComplexType(
                kind=ComplexTypeKind.UNION,
                name="Union",
                type_args=type_args
            )
        
        # 处理交叉类型 (TypeA & TypeB)
        if "&" in type_str and not type_str.startswith("{"):
            intersection_parts = [p.strip() for p in type_str.split("&")]
            type_args = [self.parse_type_string(p) for p in intersection_parts]
            return ComplexType(
                kind=ComplexTypeKind.INTERSECTION,
                name="Intersection",
                type_args=type_args
            )
        
        # 处理泛型类型 (List<string>)
        generic_match = re.match(r"^(\w+)<(.+)>$", type_str)
        if generic_match:
            type_name = generic_match.group(1)
            type_params_str = generic_match.group(2)
            type_args = self._parse_type_args(type_params_str)
            return ComplexType(
                kind=ComplexTypeKind.GENERIC,
                name=type_name,
                type_args=type_args
            )
        
        # 处理元组类型 ([string, integer])
        if type_str.startswith("[") and type_str.endswith("]"):
            elements_str = type_str[1:-1]
            type_args = self._parse_type_args(elements_str)
            return ComplexType(
                kind=ComplexTypeKind.TUPLE,
                name="Tuple",
                type_args=type_args
            )
        
        # 处理映射类型 ({[key: string]: integer})
        if type_str.startswith("{") and type_str.endswith("}"):
            map_match = re.match(r"\{\s*\[key:\s*(\w+)\]\s*:\s*(.+)\s*\}", type_str)
            if map_match:
                key_type = self.parse_type_string(map_match.group(1))
                value_type = self.parse_type_string(map_match.group(2))
                return ComplexType(
                    kind=ComplexTypeKind.MAPPED,
                    name="Record",
                    type_args=[key_type, value_type]
                )
        
        # 处理字面量类型 ("value" | 'value')
        if (type_str.startswith('"') and type_str.endswith('"')) or \
           (type_str.startswith("'") and type_str.endswith("'")):
            return ComplexType(
                kind=ComplexTypeKind.LITERAL,
                name=type_str[1:-1]
            )
        
        # 处理基础类型
        return ComplexType(
            kind=ComplexTypeKind.GENERIC,
            name=type_str,
            base_type=type_str
        )
    
    def _parse_type_args(self, args_str: str) -> List[ComplexType]:
        """
        解析类型参数列表
        
        正确处理嵌套的泛型和复杂的类型参数。
        
        Args:
            args_str: 类型参数字符串
            
        Returns:
            List[ComplexType]: 解析后的类型参数列表
        """
        args = []
        current = []
        depth = 0
        
        for char in args_str:
            if char in "<[{":
                depth += 1
                current.append(char)
            elif char in ">]}":
                depth -= 1
                current.append(char)
            elif char == "," and depth == 0:
                if current:
                    args.append(self.parse_type_string("".join(current)))
                    current = []
            else:
                current.append(char)
        
        if current:
            args.append(self.parse_type_string("".join(current)))
        
        return args
    
    def register_type(self, type_def: ComplexType):
        """
        注册自定义类型
        
        Args:
            type_def: 类型定义
        """
        self.type_registry[type_def.name.lower()] = type_def
    
    def validate_type(self, value: Any, expected_type: ComplexType) -> Tuple[bool, Optional[str]]:
        """
        验证值是否符合预期类型
        
        Args:
            value: 要验证的值
            expected_type: 预期的类型
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误消息)
        """
        try:
            return self._validate_value_against_type(value, expected_type)
        except Exception as e:
            return False, f"类型验证异常: {str(e)}"
    
    def _validate_value_against_type(self, value: Any, expected_type: ComplexType) -> Tuple[bool, Optional[str]]:
        """内部类型验证实现"""
        if expected_type.kind == ComplexTypeKind.OPTIONAL:
            if value is None:
                return True, None
            if expected_type.type_args:
                return self._validate_value_against_type(value, expected_type.type_args[0])
            return True, None
        
        if expected_type.kind == ComplexTypeKind.UNION:
            for type_arg in expected_type.type_args:
                is_valid, _ = self._validate_value_against_type(value, type_arg)
                if is_valid:
                    return True, None
            type_strs = [t.to_type_string() for t in expected_type.type_args]
            return False, f"值 {value} 不匹配联合类型 {' | '.join(type_strs)}"
        
        if expected_type.kind == ComplexTypeKind.LITERAL:
            if value == expected_type.name:
                return True, None
            return False, f"值 {value} 不等于字面量 {expected_type.name}"
        
        if expected_type.kind == ComplexTypeKind.GENERIC:
            type_name = expected_type.name.lower()
            
            # 检查基础类型
            if type_name in self.PRIMITIVE_TYPES:
                python_type = self.PRIMITIVE_TYPES[type_name]
                if python_type is object:  # any type
                    return True, None
                if isinstance(value, python_type):
                    return True, None
                return False, f"值 {value} 不是 {expected_type.name} 类型"
            
            # 检查容器类型
            if type_name in ["array", "list"]:
                if not isinstance(value, list):
                    return False, f"值 {value} 不是列表类型"
                if expected_type.type_args:
                    element_type = expected_type.type_args[0]
                    for idx, item in enumerate(value):
                        is_valid, err = self._validate_value_against_type(item, element_type)
                        if not is_valid:
                            return False, f"索引 {idx} 的元素: {err}"
                return True, None
            
            if type_name in ["dict", "map", "object"]:
                if not isinstance(value, dict):
                    return False, f"值 {value} 不是字典类型"
                if len(expected_type.type_args) >= 2:
                    key_type = expected_type.type_args[0]
                    value_type = expected_type.type_args[1]
                    for k, v in value.items():
                        is_valid, err = self._validate_value_against_type(k, key_type)
                        if not is_valid:
                            return False, f"键 '{k}': {err}"
                        is_valid, err = self._validate_value_against_type(v, value_type)
                        if not is_valid:
                            return False, f"键 '{k}' 的值: {err}"
                return True, None
            
            # 检查注册的自定义类型
            if type_name in self.type_registry:
                registered_type = self.type_registry[type_name]
                return self._validate_value_against_type(value, registered_type)
        
        if expected_type.kind == ComplexTypeKind.TUPLE:
            if not isinstance(value, (list, tuple)):
                return False, f"值 {value} 不是元组类型"
            if len(value) != len(expected_type.type_args):
                return False, f"元组长度不匹配，预期 {len(expected_type.type_args)}，实际 {len(value)}"
            for idx, (item, expected) in enumerate(zip(value, expected_type.type_args)):
                is_valid, err = self._validate_value_against_type(item, expected)
                if not is_valid:
                    return False, f"元组索引 {idx}: {err}"
            return True, None
        
        return True, None
    
    def get_type_compatibility(self, source_type: ComplexType, target_type: ComplexType) -> bool:
        """
        检查类型兼容性
        
        判断源类型是否可以安全地赋值给目标类型。
        
        Args:
            source_type: 源类型
            target_type: 目标类型
            
        Returns:
            bool: 是否兼容
        """
        # 相同类型总是兼容
        if source_type.to_type_string() == target_type.to_type_string():
            return True
        
        # any 类型兼容所有类型
        if target_type.name.lower() == "any":
            return True
        
        # 可选类型兼容性
        if target_type.kind == ComplexTypeKind.OPTIONAL:
            if source_type.kind == ComplexTypeKind.OPTIONAL:
                if source_type.type_args and target_type.type_args:
                    return self.get_type_compatibility(source_type.type_args[0], target_type.type_args[0])
            # 非空类型可以赋值给可选类型
            if target_type.type_args:
                return self.get_type_compatibility(source_type, target_type.type_args[0])
        
        # 联合类型兼容性
        if target_type.kind == ComplexTypeKind.UNION:
            for type_arg in target_type.type_args:
                if self.get_type_compatibility(source_type, type_arg):
                    return True
            return False
        
        return False


# ============================================================================
# 嵌套结构解析器
# ============================================================================

class NestedStructureParser:
    """
    嵌套结构解析器
    
    支持解析多层级嵌套的数据结构，自动检测递归引用，
    并生成完整的结构树。
    """
    
    MAX_DEPTH = 15  # 最大嵌套深度限制
    
    def __init__(self):
        """初始化嵌套结构解析器"""
        self.type_parser = ComplexTypeParser()
        self.structure_registry: Dict[str, NestedStructure] = {}
        self.recursion_detector: Set[str] = set()
    
    def parse(self, data: Dict[str, Any], parent_name: str = "", depth: int = 0) -> List[NestedStructure]:
        """
        解析嵌套结构
        
        Args:
            data: 要解析的数据字典
            parent_name: 父结构名称
            depth: 当前嵌套深度
            
        Returns:
            List[NestedStructure]: 解析后的嵌套结构列表
        """
        if depth > self.MAX_DEPTH:
            return []
        
        structures = []
        
        for key, value in data.items():
            # 检测递归引用
            structure_id = f"{parent_name}.{key}" if parent_name else key
            if structure_id in self.recursion_detector:
                continue
            
            self.recursion_detector.add(structure_id)
            
            try:
                if isinstance(value, dict):
                    structure = self._parse_dict_structure(key, value, depth, structure_id)
                    structures.append(structure)
                    self.structure_registry[structure_id] = structure
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    structure = NestedStructure(
                        name=key,
                        type="array",
                        description=f"数组类型，包含 {len(value)} 个元素",
                        children=self._parse_array_items(key, value, depth, structure_id),
                        depth=depth
                    )
                    structures.append(structure)
                    self.structure_registry[structure_id] = structure
            finally:
                self.recursion_detector.discard(structure_id)
        
        return structures
    
    def _parse_dict_structure(
        self, 
        name: str, 
        data: Dict[str, Any], 
        depth: int,
        structure_id: str
    ) -> NestedStructure:
        """
        解析字典类型结构
        
        Args:
            name: 结构名称
            data: 字典数据
            depth: 当前深度
            structure_id: 结构唯一标识
            
        Returns:
            NestedStructure: 解析后的结构
        """
        children = []
        attributes = {}
        validation_rules = []
        complex_type = None
        
        # 提取类型信息
        if "$type" in data:
            complex_type = self.type_parser.parse_type_string(data["$type"])
        
        # 提取验证规则
        if "$validation" in data:
            validation_rules = data["$validation"]
        
        for key, value in data.items():
            # 跳过元数据字段
            if key.startswith("$"):
                continue
                
            if isinstance(value, dict):
                child_id = f"{structure_id}.{key}"
                if child_id not in self.recursion_detector:
                    child = self._parse_dict_structure(key, value, depth + 1, child_id)
                    children.append(child)
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    child_id = f"{structure_id}.{key}"
                    child = NestedStructure(
                        name=key,
                        type="array",
                        children=self._parse_array_items(key, value, depth + 1, child_id),
                        depth=depth + 1
                    )
                    children.append(child)
                else:
                    attributes[key] = {
                        "type": "array", 
                        "items": self._infer_type(value[0]) if value else "any",
                        "length": len(value)
                    }
            else:
                attributes[key] = {
                    "type": self._infer_type(value), 
                    "value": value,
                    "example": value
                }
        
        # 检测是否为递归结构
        is_recursive = self._detect_recursion(structure_id, children)
        
        return NestedStructure(
            name=name,
            type="object",
            children=children,
            attributes=attributes,
            depth=depth,
            complex_type=complex_type,
            is_recursive=is_recursive,
            validation_rules=validation_rules,
            description=data.get("$description", "")
        )
    
    def _parse_array_items(
        self, 
        name: str, 
        items: List[Dict[str, Any]], 
        depth: int,
        parent_id: str
    ) -> List[NestedStructure]:
        """
        解析数组元素结构
        
        Args:
            name: 数组名称
            items: 数组元素列表
            depth: 当前深度
            parent_id: 父结构ID
            
        Returns:
            List[NestedStructure]: 解析后的结构列表
        """
        if not items:
            return []
        
        first_item = items[0]
        if isinstance(first_item, dict):
            item_id = f"{parent_id}.item"
            return [self._parse_dict_structure(f"{name}_item", first_item, depth + 1, item_id)]
        
        return []
    
    def _infer_type(self, value: Any) -> str:
        """
        推断值的类型
        
        Args:
            value: 要推断类型的值
            
        Returns:
            str: 类型名称
        """
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        return "any"
    
    def _detect_recursion(self, structure_id: str, children: List[NestedStructure]) -> bool:
        """
        检测结构是否存在递归引用
        
        Args:
            structure_id: 当前结构ID
            children: 子结构列表
            
        Returns:
            bool: 是否存在递归
        """
        for child in children:
            if self._contains_reference(child, structure_id):
                return True
        return False
    
    def _contains_reference(self, structure: NestedStructure, target_id: str) -> bool:
        """检查结构是否包含对目标ID的引用"""
        if structure.name == target_id.split(".")[-1]:
            return True
        for child in structure.children:
            if self._contains_reference(child, target_id):
                return True
        return False
    
    def get_structure_by_id(self, structure_id: str) -> Optional[NestedStructure]:
        """
        根据ID获取已解析的结构
        
        Args:
            structure_id: 结构ID
            
        Returns:
            Optional[NestedStructure]: 找到的结构，如果不存在返回None
        """
        return self.structure_registry.get(structure_id)
    
    def flatten_structure(self, structure: NestedStructure) -> Dict[str, Any]:
        """
        将嵌套结构展平为字典形式
        
        Args:
            structure: 要展平的结构
            
        Returns:
            Dict[str, Any]: 展平后的字典
        """
        result = {
            "name": structure.name,
            "type": structure.type,
            "depth": structure.depth,
            "attributes": structure.attributes,
            "is_recursive": structure.is_recursive,
        }
        
        if structure.children:
            result["children"] = [
                self.flatten_structure(child) for child in structure.children
            ]
        
        if structure.complex_type:
            result["complex_type"] = structure.complex_type.to_type_string()
        
        return result


# ============================================================================
# 条件规则解析器
# ============================================================================

class ConditionalRuleParser:
    """
    条件规则解析器
    
    支持解析复杂的条件表达式，包括逻辑运算、比较运算和函数调用。
    提供条件求值和规则优先级排序功能。
    """
    
    # 支持的比较运算符
    OPERATORS = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        "in": lambda a, b: a in b,
        "not_in": lambda a, b: a not in b,
        "contains": lambda a, b: b in a,
        "not_contains": lambda a, b: b not in a,
        "starts_with": lambda a, b: str(a).startswith(str(b)),
        "ends_with": lambda a, b: str(a).endswith(str(b)),
        "matches": lambda a, b: bool(re.match(b, str(a))),
        "is_empty": lambda a, b: not a,
        "is_not_empty": lambda a, b: bool(a),
        "is_null": lambda a, b: a is None,
        "is_not_null": lambda a, b: a is not None,
        "between": lambda a, b: b[0] <= a <= b[1] if isinstance(b, (list, tuple)) and len(b) == 2 else False,
    }
    
    # 支持的逻辑运算符
    LOGICAL_OPERATORS = {
        "and": all,
        "or": any,
        "not": lambda x: not x[0] if x else True,
        "xor": lambda x: sum(bool(i) for i in x) == 1,
    }
    
    def __init__(self):
        """初始化条件规则解析器"""
        self.custom_functions: Dict[str, Callable] = {}
    
    def register_function(self, name: str, func: Callable):
        """
        注册自定义函数
        
        Args:
            name: 函数名称
            func: 函数实现
        """
        self.custom_functions[name] = func
    
    def parse(self, data: List[Dict[str, Any]]) -> List[ConditionalRule]:
        """
        解析条件规则列表
        
        Args:
            data: 规则数据列表
            
        Returns:
            List[ConditionalRule]: 解析后的规则列表（按优先级排序）
        """
        rules = []
        
        for idx, rule_data in enumerate(data):
            rule = self._parse_rule(rule_data, idx)
            if rule:
                rules.append(rule)
        
        return sorted(rules, key=lambda r: r.priority, reverse=True)
    
    def _parse_rule(self, data: Dict[str, Any], idx: int) -> Optional[ConditionalRule]:
        """
        解析单个规则
        
        Args:
            data: 规则数据
            idx: 规则索引
            
        Returns:
            Optional[ConditionalRule]: 解析后的规则
        """
        if not data:
            return None
        
        return ConditionalRule(
            id=data.get("id", f"RULE-{idx+1:03d}"),
            name=data.get("name", f"规则{idx+1}"),
            condition=data.get("condition", data.get("when", "")),
            then_branch=data.get("then", data.get("actions", {})),
            else_branch=data.get("else"),
            priority=data.get("priority", 0),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            dependencies=data.get("dependencies", []),
        )
    
    def evaluate(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        求值条件表达式
        
        Args:
            condition: 条件表达式字符串
            context: 求值上下文
            
        Returns:
            bool: 条件结果
        """
        try:
            return self._eval_condition(condition, context)
        except Exception as e:
            raise ValueError(f"条件求值失败: {condition}, 错误: {str(e)}")
    
    def _eval_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        内部条件求值实现
        
        支持嵌套的逻辑表达式和复杂的比较运算。
        """
        condition = condition.strip()
        
        # 处理逻辑运算符
        for logical_op, func in self.LOGICAL_OPERATORS.items():
            pattern = rf"^{logical_op}\((.+)\)$"
            match = re.match(pattern, condition, re.IGNORECASE)
            if match:
                inner = match.group(1)
                sub_conditions = self._split_conditions(inner)
                results = [self._eval_condition(sc.strip(), context) for sc in sub_conditions]
                return func(results)
        
        # 处理括号分组
        if condition.startswith("(") and condition.endswith(")"):
            return self._eval_condition(condition[1:-1], context)
        
        # 处理比较运算符
        for op_name, op_func in self.OPERATORS.items():
            pattern = r"(\w+(?:\.\w+)*)\s+" + re.escape(op_name) + r"\s+(.+)"
            match = re.match(pattern, condition, re.IGNORECASE)
            if match:
                left_path = match.group(1)
                right_raw = match.group(2).strip()
                
                left_value = self._get_value(left_path, context)
                right_value = self._parse_right_value(right_raw, context)
                
                return op_func(left_value, right_value)
        
        # 处理自定义函数调用
        func_match = re.match(r"(\w+)\((.+)\)$", condition)
        if func_match:
            func_name = func_match.group(1)
            args_str = func_match.group(2)
            
            if func_name in self.custom_functions:
                args = self._parse_function_args(args_str, context)
                return bool(self.custom_functions[func_name](*args))
        
        # 处理布尔值
        if condition.lower() == "true":
            return True
        if condition.lower() == "false":
            return False
        
        # 处理上下文中的布尔值
        if condition in context:
            return bool(context[condition])
        
        return bool(condition)
    
    def _split_conditions(self, text: str) -> List[str]:
        """
        分割条件表达式列表
        
        正确处理嵌套括号内的逗号。
        """
        conditions = []
        current = []
        depth = 0
        
        for char in text:
            if char == "(":
                depth += 1
                current.append(char)
            elif char == ")":
                depth -= 1
                current.append(char)
            elif char == "," and depth == 0:
                conditions.append("".join(current).strip())
                current = []
            else:
                current.append(char)
        
        if current:
            conditions.append("".join(current).strip())
        
        return conditions
    
    def _get_value(self, path: str, context: Dict[str, Any]) -> Any:
        """
        从上下文中获取路径对应的值
        
        支持点号分隔的嵌套路径访问。
        """
        keys = path.split(".")
        value = context
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list):
                try:
                    idx = int(key)
                    if 0 <= idx < len(value):
                        value = value[idx]
                    else:
                        return None
                except ValueError:
                    return None
            else:
                return None
        
        return value
    
    def _parse_right_value(self, value: str, context: Dict[str, Any]) -> Any:
        """
        解析右侧值
        
        支持变量引用、字符串、数字、布尔值、列表等。
        """
        value = value.strip()
        
        # 变量引用 ${var}
        if value.startswith("${") and value.endswith("}"):
            return self._get_value(value[2:-1], context)
        
        # 字符串字面量
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        if value.startswith("'") and value.endswith("'"):
            return value[1:-1]
        
        # 列表字面量
        if value.startswith("[") and value.endswith("]"):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [v.strip() for v in value[1:-1].split(",")]
        
        # 布尔值
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        if value.lower() == "null" or value.lower() == "none":
            return None
        
        # 数字
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        return value
    
    def _parse_function_args(self, args_str: str, context: Dict[str, Any]) -> List[Any]:
        """
        解析函数参数列表
        """
        args = []
        for arg in self._split_conditions(args_str):
            args.append(self._parse_right_value(arg, context))
        return args
    
    def validate_condition_syntax(self, condition: str) -> Tuple[bool, Optional[str]]:
        """
        验证条件表达式语法
        
        Args:
            condition: 条件表达式
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误消息)
        """
        try:
            # 检查括号匹配
            depth = 0
            for char in condition:
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth < 0:
                        return False, "括号不匹配：多余的右括号"
            
            if depth != 0:
                return False, f"括号不匹配：缺少 {depth} 个右括号"
            
            # 尝试空上下文求值
            self._eval_condition(condition, {})
            return True, None
            
        except Exception as e:
            return False, str(e)


# ============================================================================
# 状态机解析器
# ============================================================================

class StateMachineParser:
    """
    状态机解析器
    
    支持解析复杂的状态机定义，包括嵌套状态、历史状态、并行状态等。
    提供状态机验证和可达性分析功能。
    """
    
    def parse(self, data: Dict[str, Any]) -> StateMachine:
        """
        解析状态机定义
        
        Args:
            data: 状态机数据
            
        Returns:
            StateMachine: 解析后的状态机
        """
        sm_id = data.get("id", f"SM-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        states = self._parse_states(data.get("states", []))
        transitions = self._parse_transitions(data.get("transitions", []))
        final_states = data.get("finalStates", data.get("final_states", []))
        events = data._extract_events(transitions) if hasattr(data, '_extract_events') else []
        
        return StateMachine(
            id=sm_id,
            name=data.get("name", "未命名状态机"),
            initial_state=data.get("initialState", data.get("initial_state", "")),
            states=states,
            transitions=transitions,
            final_states=final_states,
            description=data.get("description", ""),
            events=list(set(events)),
            history_states=data.get("historyStates", []),
        )
    
    def _parse_states(self, states_data: List[Dict[str, Any]]) -> List[StateDefinition]:
        """
        解析状态列表
        
        支持简单字符串形式和复杂对象形式的状态定义。
        """
        states = []
        
        for state_data in states_data:
            if isinstance(state_data, str):
                states.append(StateDefinition(name=state_data))
            else:
                state = StateDefinition(
                    name=state_data.get("name", ""),
                    type=state_data.get("type", "normal"),
                    entry_action=state_data.get("entryAction", state_data.get("entry")),
                    exit_action=state_data.get("exitAction", state_data.get("exit")),
                    description=state_data.get("description", ""),
                    sub_states=self._parse_states(state_data.get("states", [])),
                    on_enter_events=state_data.get("onEnter", []),
                    on_exit_events=state_data.get("onExit", []),
                )
                states.append(state)
        
        return states
    
    def _parse_transitions(self, transitions_data: List[Dict[str, Any]]) -> List[StateTransition]:
        """
        解析状态转换列表
        """
        transitions = []
        
        for trans_data in transitions_data:
            transition = StateTransition(
                from_state=trans_data.get("from", trans_data.get("source", "")),
                to_state=trans_data.get("to", trans_data.get("target", "")),
                trigger=trans_data.get("trigger", trans_data.get("event", "")),
                guard=trans_data.get("guard", trans_data.get("condition")),
                action=trans_data.get("action"),
                description=trans_data.get("description", ""),
                priority=trans_data.get("priority", 0),
                side_effects=trans_data.get("sideEffects", []),
            )
            transitions.append(transition)
        
        return transitions
    
    def _extract_events(self, transitions: List[StateTransition]) -> List[str]:
        """从转换中提取所有事件"""
        return [t.trigger for t in transitions if t.trigger]
    
    def validate(self, state_machine: StateMachine) -> ValidationResult:
        """
        验证状态机定义
        
        检查初始状态、状态可达性、转换完整性等。
        
        Args:
            state_machine: 要验证的状态机
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)
        
        # 验证初始状态
        if not state_machine.initial_state:
            result.add_error(
                "stateMachine.initialState", 
                "缺少初始状态定义",
                "添加 initialState 字段指定初始状态"
            )
        
        state_names = self._get_all_state_names(state_machine.states)
        
        # 验证初始状态是否存在
        if state_machine.initial_state and state_machine.initial_state not in state_names:
            result.add_error(
                "stateMachine.initialState",
                f"初始状态 '{state_machine.initial_state}' 未在状态列表中定义",
                f"可用状态: {', '.join(state_names)}"
            )
        
        # 验证转换的源状态和目标状态
        for trans in state_machine.transitions:
            if trans.from_state not in state_names:
                result.add_warning(
                    "stateMachine.transitions",
                    f"转换源状态 '{trans.from_state}' 未定义",
                    f"添加状态定义或检查拼写"
                )
            if trans.to_state not in state_names:
                result.add_warning(
                    "stateMachine.transitions",
                    f"转换目标状态 '{trans.to_state}' 未定义",
                    f"添加状态定义或检查拼写"
                )
        
        # 检查可达性
        reachable = self._get_reachable_states(state_machine)
        unreachable = state_names - reachable
        
        if unreachable:
            result.add_warning(
                "stateMachine.states",
                f"存在不可达状态: {', '.join(unreachable)}",
                "检查是否缺少转换或移除无用状态"
            )
        
        # 验证最终状态
        for final_state in state_machine.final_states:
            if final_state not in state_names:
                result.add_warning(
                    "stateMachine.finalStates",
                    f"最终状态 '{final_state}' 未在状态列表中定义"
                )
        
        # 检查是否有死锁状态（没有出边的非最终状态）
        deadlock_states = self._find_deadlock_states(state_machine)
        if deadlock_states:
            result.add_warning(
                "stateMachine.states",
                f"存在潜在的死锁状态: {', '.join(deadlock_states)}",
                "添加转换或将其标记为最终状态"
            )
        
        # 检查转换冲突
        conflicts = self._find_transition_conflicts(state_machine)
        if conflicts:
            for conflict in conflicts:
                result.add_info(
                    "stateMachine.transitions",
                    f"存在转换冲突: {conflict}",
                    "考虑添加 guard 条件区分"
                )
        
        return result
    
    def _get_all_state_names(self, states: List[StateDefinition]) -> Set[str]:
        """获取所有状态名称（包括嵌套状态）"""
        names = set()
        for state in states:
            names.add(state.name)
            if state.sub_states:
                names.update(self._get_all_state_names(state.sub_states))
        return names
    
    def _get_reachable_states(self, state_machine: StateMachine) -> Set[str]:
        """计算从初始状态可达的所有状态"""
        reachable = {state_machine.initial_state}
        changed = True
        
        while changed:
            changed = False
            for trans in state_machine.transitions:
                if trans.from_state in reachable and trans.to_state not in reachable:
                    reachable.add(trans.to_state)
                    changed = True
        
        return reachable
    
    def _find_deadlock_states(self, state_machine: StateMachine) -> List[str]:
        """查找死锁状态（没有出边的非最终状态）"""
        state_names = self._get_all_state_names(state_machine.states)
        states_with_exits = {t.from_state for t in state_machine.transitions}
        
        deadlock = []
        for state_name in state_names:
            if state_name not in states_with_exits and state_name not in state_machine.final_states:
                deadlock.append(state_name)
        
        return deadlock
    
    def _find_transition_conflicts(self, state_machine: StateMachine) -> List[str]:
        """查找转换冲突（同一源状态和触发器的多个转换）"""
        conflicts = []
        transition_map: Dict[Tuple[str, str], List[StateTransition]] = {}
        
        for trans in state_machine.transitions:
            key = (trans.from_state, trans.trigger)
            if key not in transition_map:
                transition_map[key] = []
            transition_map[key].append(trans)
        
        for key, trans_list in transition_map.items():
            if len(trans_list) > 1:
                # 检查是否都有 guard 条件
                unguarded = [t for t in trans_list if not t.guard]
                if unguarded:
                    conflicts.append(
                        f"状态 '{key[0]}' 在事件 '{key[1]}' 上有 {len(trans_list)} 个转换"
                    )
        
        return conflicts
    
    def generate_state_diagram(self, state_machine: StateMachine) -> str:
        """
        生成状态机的Mermaid图
        
        Args:
            state_machine: 状态机
            
        Returns:
            str: Mermaid图代码
        """
        lines = ["stateDiagram-v2"]
        
        # 添加状态
        for state in state_machine.states:
            if state.description:
                lines.append(f"    {state.name} : {state.description}")
        
        # 添加初始状态标记
        lines.append(f"    [*] --> {state_machine.initial_state}")
        
        # 添加转换
        for trans in state_machine.transitions:
            label = trans.trigger
            if trans.guard:
                label += f" [{trans.guard}]"
            if trans.action:
                label += f" / {trans.action}"
            lines.append(f"    {trans.from_state} --> {trans.to_state} : {label}")
        
        # 添加最终状态标记
        for final_state in state_machine.final_states:
            lines.append(f"    {final_state} --> [*]")
        
        return "\n".join(lines)


# ============================================================================
# 规范完整性验证器
# ============================================================================

class SpecCompletenessValidator:
    """
    规范完整性验证器
    
    提供多维度验证：
    - 元数据验证
    - 结构完整性验证
    - 交叉引用验证
    - 一致性验证
    - 依赖关系验证
    - 版本兼容性验证
    """
    
    # 各类型规范必需的元素
    REQUIRED_SPEC_ELEMENTS = {
        SpecType.ENTITY: ["attributes"],
        SpecType.INTERFACE: ["endpoints"],
        SpecType.API: ["endpoints"],
        SpecType.BUSINESS_RULE: ["rules", "conditions"],
        SpecType.ACCEPTANCE: ["scenarios"],
        SpecType.STATE_MACHINE: ["states", "transitions"],
        SpecType.FUNCTION: ["inputs", "outputs"],
        SpecType.DATA_MODEL: ["attributes"],
        SpecType.WORKFLOW: ["states"],
    }
    
    # 推荐的规范元素
    RECOMMENDED_ELEMENTS = {
        SpecType.ENTITY: ["constraints", "relationships"],
        SpecType.INTERFACE: ["authentication", "errors"],
        SpecType.API: ["authentication", "rateLimit", "errors"],
        SpecType.BUSINESS_RULE: ["priority", "description"],
        SpecType.ACCEPTANCE: ["testData", "priority"],
        SpecType.STATE_MACHINE: ["finalStates", "description"],
    }
    
    def __init__(self):
        """初始化验证器"""
        self.custom_validators: List[Callable] = []
    
    def register_validator(self, validator: Callable):
        """
        注册自定义验证器
        
        Args:
            validator: 验证函数，签名为 (SDDSpecification, ValidationResult) -> None
        """
        self.custom_validators.append(validator)
    
    def validate(self, spec: SDDSpecification) -> ValidationResult:
        """
        执行完整验证
        
        Args:
            spec: 要验证的规范
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)
        
        # 执行各项验证
        self._validate_metadata(spec.metadata, result)
        self._validate_spec_type_elements(spec, result)
        self._validate_cross_references(spec, result)
        self._validate_consistency(spec, result)
        self._validate_dependencies(spec, result)
        self._validate_version_compatibility(spec, result)
        self._validate_semantic_correctness(spec, result)
        
        # 执行自定义验证器
        for validator in self.custom_validators:
            try:
                validator(spec, result)
            except Exception as e:
                result.add_warning(
                    "custom_validation",
                    f"自定义验证器执行失败: {str(e)}"
                )
        
        return result
    
    def _validate_metadata(self, metadata: SpecMetadata, result: ValidationResult):
        """
        验证元数据完整性
        
        检查ID、名称、版本、状态等基本信息的有效性。
        """
        # 必需字段验证
        if not metadata.id:
            result.add_error(
                "metadata.id", 
                "规范ID不能为空",
                "添加唯一的规范ID，格式建议: SPC-{module}-{name}"
            )
        elif not self._is_valid_id(metadata.id):
            result.add_warning(
                "metadata.id",
                f"规范ID格式不规范: {metadata.id}",
                "建议格式: SPC-{module}-{name}，如 SPC-user-auth"
            )
        
        if not metadata.name:
            result.add_error(
                "metadata.name", 
                "规范名称不能为空",
                "添加描述性的规范名称"
            )
        
        if not metadata.version:
            result.add_warning(
                "metadata.version", 
                "缺少版本号",
                "建议添加语义化版本号，如 v1.0.0"
            )
        elif not self._is_valid_semantic_version(metadata.version):
            result.add_info(
                "metadata.version",
                f"版本号不符合语义化版本规范: {metadata.version}",
                "建议格式: major.minor.patch，如 1.0.0"
            )
        
        # 状态验证
        valid_statuses = ["draft", "review", "approved", "deprecated", "retired", "experimental"]
        if metadata.status not in valid_statuses:
            result.add_warning(
                "metadata.status",
                f"非标准状态值: {metadata.status}",
                f"建议使用: {', '.join(valid_statuses)}"
            )
        
        # 时间戳验证
        if metadata.created:
            if not self._is_valid_iso_datetime(metadata.created):
                result.add_info(
                    "metadata.created",
                    f"创建时间格式不正确: {metadata.created}",
                    "建议使用ISO 8601格式"
                )
        
        if metadata.modified:
            if not self._is_valid_iso_datetime(metadata.modified):
                result.add_info(
                    "metadata.modified",
                    f"修改时间格式不正确: {metadata.modified}",
                    "建议使用ISO 8601格式"
                )
        
        # 依赖验证
        if metadata.dependencies:
            for dep in metadata.dependencies:
                if not isinstance(dep, str):
                    result.add_warning(
                        "metadata.dependencies",
                        f"依赖项格式不正确: {dep}",
                        "依赖项应为字符串形式的规范ID"
                    )
    
    def _validate_spec_type_elements(self, spec: SDDSpecification, result: ValidationResult):
        """
        验证规范类型特定的元素
        
        根据规范类型检查必需和推荐的元素。
        """
        required_elements = self.REQUIRED_SPEC_ELEMENTS.get(spec.kind, [])
        recommended_elements = self.RECOMMENDED_ELEMENTS.get(spec.kind, [])
        
        for element in required_elements:
            self._check_required_element(spec, element, result)
        
        for element in recommended_elements:
            self._check_recommended_element(spec, element, result)
    
    def _check_required_element(self, spec: SDDSpecification, element: str, result: ValidationResult):
        """检查必需元素是否存在"""
        element_checks = {
            "attributes": (spec.attributes, "实体规范缺少属性定义", "添加attributes数组定义实体属性"),
            "endpoints": (spec.endpoints, "接口规范缺少端点定义", "添加endpoints数组定义API端点"),
            "scenarios": (spec.scenarios, "验收规范缺少测试场景", "添加scenarios数组定义测试场景"),
            "states": ([sm.states for sm in spec.state_machines], "状态机规范缺少状态定义", "添加states数组定义状态"),
            "transitions": ([sm.transitions for sm in spec.state_machines], "状态机规范缺少转换定义", "添加transitions数组定义状态转换"),
            "inputs": (spec.spec.get("inputs", []), "函数规范缺少输入定义", "添加inputs数组定义输入参数"),
            "outputs": (spec.spec.get("outputs", []), "函数规范缺少输出定义", "添加outputs数组定义输出"),
            "rules": (spec.conditional_rules, "业务规则规范缺少规则定义", "添加conditionalRules数组"),
            "conditions": (spec.conditional_rules, "业务规则规范缺少条件定义", "在规则中添加condition字段"),
        }
        
        if element in element_checks:
            value, message, suggestion = element_checks[element]
            if element in ["states", "transitions"]:
                # 特殊处理：检查是否有任何状态机包含该元素
                has_element = any(value) if value else False
            else:
                has_element = bool(value)
            
            if not has_element:
                result.add_warning(f"spec.{element}", message, suggestion)
    
    def _check_recommended_element(self, spec: SDDSpecification, element: str, result: ValidationResult):
        """检查推荐元素是否存在"""
        element_checks = {
            "constraints": (spec.constraints, "建议添加约束条件定义"),
            "relationships": (spec.relationships, "建议添加关系定义"),
            "authentication": (any(ep.authentication for ep in spec.endpoints), "建议明确定义认证要求"),
            "errors": (any(ep.errors for ep in spec.endpoints), "建议定义错误处理"),
            "rateLimit": (any(ep.rate_limit for ep in spec.endpoints), "建议定义速率限制"),
            "testData": (any(s.test_data for s in spec.scenarios), "建议为场景添加测试数据"),
            "priority": (any(s.priority for s in spec.scenarios), "建议为场景设置优先级"),
            "finalStates": (any(sm.final_states for sm in spec.state_machines), "建议定义最终状态"),
            "description": (spec.metadata.annotations.get("description") or spec.spec.get("description"), "建议添加描述信息"),
        }
        
        if element in element_checks:
            value, message = element_checks[element]
            if not value:
                result.add_hint(f"spec.{element}", message)
    
    def _validate_cross_references(self, spec: SDDSpecification, result: ValidationResult):
        """
        验证交叉引用
        
        检查规范中的引用是否都能正确解析。
        """
        ref_patterns = [
            (r"\$\{([^}]+)\}", "变量引用"),
            (r"@ref\[([^\]]+)\]", "元素引用"),
            (r"#([a-zA-Z_][a-zA-Z0-9_]*)", "锚点引用"),
        ]
        
        spec_content = json.dumps(spec.spec)
        
        for pattern, ref_type in ref_patterns:
            for match in re.finditer(pattern, spec_content):
                ref = match.group(1)
                if not self._resolve_reference(ref, spec):
                    result.add_warning(
                        "spec.references",
                        f"{ref_type}无法解析: {ref}",
                        "确保引用的目标元素存在"
                    )
    
    def _resolve_reference(self, ref: str, spec: SDDSpecification) -> bool:
        """
        解析引用路径
        
        支持点号分隔的路径和数组索引访问。
        """
        parts = ref.split(".")
        current = spec.spec
        
        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    return False
                current = current[part]
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    if idx < 0 or idx >= len(current):
                        return False
                    current = current[idx]
                except ValueError:
                    # 尝试按名称查找
                    found = False
                    for item in current:
                        if isinstance(item, dict) and item.get("name") == part:
                            current = item
                            found = True
                            break
                    if not found:
                        return False
            else:
                return False
        
        return True
    
    def _validate_consistency(self, spec: SDDSpecification, result: ValidationResult):
        """
        验证一致性
        
        检查命名冲突、重复定义和逻辑一致性。
        """
        self._check_naming_conflicts(spec, result)
        self._check_duplicate_definitions(spec, result)
        self._check_logical_consistency(spec, result)
    
    def _check_naming_conflicts(self, spec: SDDSpecification, result: ValidationResult):
        names = {}
        
        for attr in spec.attributes:
            name = attr.name.lower()
            if name in names:
                result.add_warning(
                    f"spec.attributes.{attr.name}",
                    f"属性名称 '{attr.name}' 与 '{names[name]}' 可能存在冲突",
                    "建议使用更具描述性的名称以避免混淆"
                )
            else:
                names[name] = attr.name
        
        for endpoint in spec.endpoints:
            key = f"{endpoint.method}:{endpoint.path}"
            if key in names:
                result.add_warning(
                    f"spec.endpoints.{endpoint.name}",
                    f"端点 '{endpoint.method} {endpoint.path}' 可能重复定义",
                    "检查是否需要合并或重命名端点"
                )
            names[key] = endpoint.name
    
    def _check_duplicate_definitions(self, spec: SDDSpecification, result: ValidationResult):
        state_names = set()
        for sm in spec.state_machines:
            for state in sm.states:
                if state.name in state_names:
                    result.add_info(
                        f"spec.stateMachines.{sm.id}",
                        f"状态 '{state.name}' 在多个状态机中定义",
                        "确保状态语义一致"
                    )
                state_names.add(state.name)
    
    def _check_logical_consistency(self, spec: SDDSpecification, result: ValidationResult):
        for rule in spec.conditional_rules:
            if rule.then_branch and not rule.condition:
                result.add_warning(
                    f"spec.conditionalRules.{rule.id}",
                    f"规则 '{rule.name}' 有执行分支但缺少条件",
                    "添加条件或检查规则逻辑"
                )


class AsyncOperationSpec:
    """
    异步操作规范数据类
    
    表示规范中的异步操作定义，支持Promise、async/await等异步模式。
    """
    operation_id: str
    name: str
    operation_type: str
    input_type: Optional[ComplexType] = None
    output_type: Optional[ComplexType] = None
    error_type: Optional[ComplexType] = None
    timeout: Optional[int] = None
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    cancellation_support: bool = False
    progress_reporting: bool = False
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    idempotent: bool = False
    concurrency_mode: str = "sequential"


@dataclass
class AsyncOperationSpec:
    operation_id: str
    name: str
    operation_type: str
    input_type: Optional[ComplexType] = None
    output_type: Optional[ComplexType] = None
    error_type: Optional[ComplexType] = None
    timeout: Optional[int] = None
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    cancellation_support: bool = False
    progress_reporting: bool = False
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    idempotent: bool = False
    concurrency_mode: str = "sequential"


class AsyncOperationParser:
    """
    异步操作规范解析器
    
    支持解析异步操作规范，包括：
    - Promise/async/await 模式
    - 回调函数模式
    - 事件驱动模式
    - 流式处理模式
    - 超时和重试策略
    - 取消和进度报告
    """
    
    ASYNC_PATTERNS = {
        "promise": r"Promise<(.+)>",
        "async_function": r"async\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*(.+))?",
        "callback": r"callback\s*:\s*\(([^)]*)\)\s*=>\s*(.+)",
        "observable": r"Observable<(.+)>",
        "stream": r"(?:Readable|Writable|Duplex|Transform)Stream(?:<(.+)>)?",
        "event_emitter": r"EventEmitter<(.+)>",
    }
    
    RETRY_STRATEGIES = {
        "fixed": "固定间隔重试",
        "exponential": "指数退避重试",
        "linear": "线性退避重试",
        "custom": "自定义重试策略"
    }
    
    CONCURRENCY_MODES = {
        "sequential": "顺序执行",
        "parallel": "并行执行",
        "race": "竞争执行",
        "all_settled": "全部完成"
    }
    
    def __init__(self):
        self.type_parser = ComplexTypeParser()
        self.operation_counter = 0
        self._operation_registry: Dict[str, AsyncOperationSpec] = {}
    
    def parse(self, data: List[Dict[str, Any]]) -> List[AsyncOperationSpec]:
        """
        解析异步操作规范列表
        
        Args:
            data: 异步操作数据列表
            
        Returns:
            List[AsyncOperationSpec]: 解析后的异步操作规范列表
        """
        operations = []
        
        for idx, op_data in enumerate(data):
            operation = self._parse_operation(op_data, idx)
            if operation:
                operations.append(operation)
                self._operation_registry[operation.operation_id] = operation
        
        return operations
    
    def _parse_operation(self, data: Dict[str, Any], idx: int) -> Optional[AsyncOperationSpec]:
        """解析单个异步操作"""
        if not data:
            return None
        
        self.operation_counter += 1
        operation_id = data.get("id", f"ASYNC-{self.operation_counter:03d}")
        
        operation_type = self._detect_operation_type(data)
        
        input_type = self._parse_io_type(data.get("input") or data.get("inputType"))
        output_type = self._parse_io_type(data.get("output") or data.get("outputType"))
        error_type = self._parse_io_type(data.get("error") or data.get("errorType"))
        
        retry_policy = self._parse_retry_policy(data.get("retryPolicy", {}))
        
        return AsyncOperationSpec(
            operation_id=operation_id,
            name=data.get("name", f"异步操作{idx + 1}"),
            operation_type=operation_type,
            input_type=input_type,
            output_type=output_type,
            error_type=error_type,
            timeout=data.get("timeout"),
            retry_policy=retry_policy,
            cancellation_support=data.get("cancellation", data.get("cancellable", False)),
            progress_reporting=data.get("progressReporting", data.get("progress", False)),
            description=data.get("description", ""),
            dependencies=data.get("dependencies", []),
            side_effects=data.get("sideEffects", []),
            idempotent=data.get("idempotent", False),
            concurrency_mode=data.get("concurrencyMode", "sequential")
        )
    
    def _detect_operation_type(self, data: Dict[str, Any]) -> str:
        """检测异步操作类型"""
        output_type = str(data.get("output", data.get("outputType", "")))
        name = data.get("name", "").lower()
        desc = data.get("description", "").lower()
        
        for pattern_name, pattern in self.ASYNC_PATTERNS.items():
            if re.search(pattern, output_type, re.IGNORECASE):
                return pattern_name
        
        if "stream" in name or "stream" in desc:
            return "stream"
        if "event" in name or "event" in desc:
            return "event_emitter"
        if "callback" in name or "callback" in desc:
            return "callback"
        if "observable" in output_type.lower():
            return "observable"
        
        return "promise"
    
    def _parse_io_type(self, type_data: Any) -> Optional[ComplexType]:
        """解析输入/输出类型"""
        if not type_data:
            return None
        
        if isinstance(type_data, str):
            return self.type_parser.parse_type_string(type_data)
        elif isinstance(type_data, dict):
            type_str = type_data.get("type", type_data.get("$type", "any"))
            return self.type_parser.parse_type_string(type_str)
        
        return None
    
    def _parse_retry_policy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析重试策略"""
        if not data:
            return {}
        
        return {
            "strategy": data.get("strategy", "exponential"),
            "max_retries": data.get("maxRetries", data.get("max_retries", 3)),
            "initial_delay": data.get("initialDelay", data.get("initial_delay", 1000)),
            "max_delay": data.get("maxDelay", data.get("max_delay", 30000)),
            "multiplier": data.get("multiplier", 2.0),
            "jitter": data.get("jitter", False),
            "retry_on": data.get("retryOn", data.get("retry_on", [])),
            "abort_on": data.get("abortOn", data.get("abort_on", []))
        }
    
    def validate(self, operation: AsyncOperationSpec) -> ValidationResult:
        """
        验证异步操作规范
        
        Args:
            operation: 要验证的异步操作规范
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)
        
        if not operation.operation_id:
            result.add_error(
                "asyncOperation.id",
                "异步操作缺少ID",
                "添加唯一的操作ID"
            )
        
        if not operation.name:
            result.add_warning(
                "asyncOperation.name",
                "异步操作缺少名称",
                "添加描述性的操作名称"
            )
        
        if operation.timeout is not None and operation.timeout <= 0:
            result.add_error(
                "asyncOperation.timeout",
                f"无效的超时值: {operation.timeout}",
                "超时值必须为正整数（毫秒）"
            )
        
        if operation.retry_policy:
            max_retries = operation.retry_policy.get("max_retries", 0)
            if max_retries < 0:
                result.add_error(
                    "asyncOperation.retryPolicy.maxRetries",
                    f"无效的最大重试次数: {max_retries}",
                    "最大重试次数必须为非负整数"
                )
            
            strategy = operation.retry_policy.get("strategy", "")
            if strategy and strategy not in self.RETRY_STRATEGIES:
                result.add_warning(
                    "asyncOperation.retryPolicy.strategy",
                    f"未知的重试策略: {strategy}",
                    f"支持的策略: {', '.join(self.RETRY_STRATEGIES.keys())}"
                )
        
        if operation.concurrency_mode not in self.CONCURRENCY_MODES:
            result.add_warning(
                "asyncOperation.concurrencyMode",
                f"未知的并发模式: {operation.concurrency_mode}",
                f"支持的模式: {', '.join(self.CONCURRENCY_MODES.keys())}"
            )
        
        if operation.dependencies:
            for dep in operation.dependencies:
                if dep not in self._operation_registry:
                    result.add_warning(
                        "asyncOperation.dependencies",
                        f"依赖的操作 '{dep}' 未定义",
                        "确保依赖的操作已定义或检查ID拼写"
                    )
        
        return result
    
    def generate_async_test_cases(self, operation: AsyncOperationSpec) -> List[Dict[str, Any]]:
        """
        为异步操作生成测试用例
        
        Args:
            operation: 异步操作规范
            
        Returns:
            List[Dict[str, Any]]: 生成的测试用例列表
        """
        test_cases = []
        
        test_cases.append({
            "name": f"test_{operation.name}_success",
            "type": "async_success",
            "description": f"测试 {operation.name} 成功场景",
            "arrange": f"准备有效的输入数据",
            "act": f"执行异步操作 {operation.name}",
            "assert": f"验证返回正确的输出类型",
            "timeout": operation.timeout or 30000
        })
        
        if operation.error_type:
            test_cases.append({
                "name": f"test_{operation.name}_error_handling",
                "type": "async_error",
                "description": f"测试 {operation.name} 错误处理",
                "arrange": f"准备触发错误的输入数据",
                "act": f"执行异步操作 {operation.name}",
                "assert": f"验证正确抛出 {operation.error_type.to_type_string() if operation.error_type else 'Error'}",
                "timeout": operation.timeout or 30000
            })
        
        if operation.timeout:
            test_cases.append({
                "name": f"test_{operation.name}_timeout",
                "type": "async_timeout",
                "description": f"测试 {operation.name} 超时处理",
                "arrange": f"准备导致超时的场景",
                "act": f"执行异步操作 {operation.name} 并等待超时",
                "assert": f"验证超时错误被正确处理",
                "timeout": operation.timeout + 5000
            })
        
        if operation.retry_policy and operation.retry_policy.get("max_retries", 0) > 0:
            test_cases.append({
                "name": f"test_{operation.name}_retry",
                "type": "async_retry",
                "description": f"测试 {operation.name} 重试机制",
                "arrange": f"准备间歇性失败的场景",
                "act": f"执行异步操作 {operation.name}",
                "assert": f"验证重试策略正确执行",
                "timeout": (operation.timeout or 30000) * operation.retry_policy.get("max_retries", 1)
            })
        
        if operation.cancellation_support:
            test_cases.append({
                "name": f"test_{operation.name}_cancellation",
                "type": "async_cancellation",
                "description": f"测试 {operation.name} 取消功能",
                "arrange": f"启动异步操作",
                "act": f"在操作完成前发送取消信号",
                "assert": f"验证操作被正确取消并清理资源",
                "timeout": operation.timeout or 30000
            })
        
        if operation.progress_reporting:
            test_cases.append({
                "name": f"test_{operation.name}_progress",
                "type": "async_progress",
                "description": f"测试 {operation.name} 进度报告",
                "arrange": f"订阅进度事件",
                "act": f"执行异步操作 {operation.name}",
                "assert": f"验证进度事件正确触发",
                "timeout": operation.timeout or 30000
            })
        
        return test_cases
    
    def get_operation_by_id(self, operation_id: str) -> Optional[AsyncOperationSpec]:
        """根据ID获取已解析的操作"""
        return self._operation_registry.get(operation_id)


class EnhancedErrorReporter:
    """
    增强的错误报告器
    
    提供详细的错误信息和修复建议，包括：
    - 错误上下文分析
    - 智能修复建议
    - 错误严重程度评估
    - 相关文档链接
    """
    
    ERROR_TEMPLATES = {
        "missing_required_field": {
            "message": "缺少必需字段 '{field}'",
            "suggestion": "添加 '{field}' 字段，参考文档: {doc_link}",
            "severity": ValidationSeverity.ERROR
        },
        "invalid_type": {
            "message": "字段 '{field}' 的类型无效: 期望 {expected}, 实际 {actual}",
            "suggestion": "将 '{field}' 的值修改为 {expected} 类型",
            "severity": ValidationSeverity.ERROR
        },
        "invalid_format": {
            "message": "字段 '{field}' 的格式无效: {detail}",
            "suggestion": "确保 '{field}' 符合格式要求: {format_desc}",
            "severity": ValidationSeverity.WARNING
        },
        "circular_reference": {
            "message": "检测到循环引用: {cycle_path}",
            "suggestion": "重构以消除循环依赖，考虑使用依赖注入或事件驱动架构",
            "severity": ValidationSeverity.ERROR
        },
        "undefined_reference": {
            "message": "引用未定义的元素: '{ref}'",
            "suggestion": "定义元素 '{ref}' 或检查引用路径是否正确",
            "severity": ValidationSeverity.WARNING
        },
        "conflict_definition": {
            "message": "定义冲突: {detail}",
            "suggestion": "统一冲突的定义或使用命名空间区分",
            "severity": ValidationSeverity.WARNING
        },
        "deprecated_usage": {
            "message": "使用了已废弃的特性: '{feature}'",
            "suggestion": "迁移到替代方案: {alternative}",
            "severity": ValidationSeverity.INFO
        }
    }
    
    def __init__(self):
        self.error_contexts: Dict[str, List[Dict[str, Any]]] = {}
        self.suggestion_cache: Dict[str, List[str]] = {}
    
    def create_enhanced_error(
        self,
        error_type: str,
        path: str,
        context: Dict[str, Any],
        source_content: Optional[str] = None
    ) -> ValidationError:
        """
        创建增强的错误信息
        
        Args:
            error_type: 错误类型
            path: 错误路径
            context: 错误上下文
            source_content: 源内容（用于提取上下文）
            
        Returns:
            ValidationError: 增强的验证错误
        """
        template = self.ERROR_TEMPLATES.get(error_type, {
            "message": f"未知错误类型: {error_type}",
            "suggestion": "请检查规范文档",
            "severity": ValidationSeverity.ERROR
        })
        
        message = self._format_message(template["message"], context)
        suggestion = self._format_message(template["suggestion"], context)
        
        line_number = context.get("line_number")
        if source_content and not line_number:
            line_number = self._find_line_number(path, source_content)
        
        code_snippet = ""
        if source_content and line_number:
            code_snippet = self._extract_code_snippet(source_content, line_number)
        
        error = ValidationError(
            path=path,
            message=message,
            severity=template["severity"],
            suggestion=suggestion,
            code=error_type,
            line_number=line_number,
            context=code_snippet
        )
        
        self._cache_error_context(error, context)
        
        return error
    
    def _format_message(self, template: str, context: Dict[str, Any]) -> str:
        """格式化错误消息"""
        try:
            return template.format(**context)
        except KeyError:
            return template
    
    def _find_line_number(self, path: str, content: str) -> Optional[int]:
        """在源内容中查找路径对应的行号"""
        path_parts = path.split(".")
        current_indent = 0
        
        for idx, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if not stripped:
                continue
            
            for part in path_parts:
                if part in stripped:
                    return idx
        
        return None
    
    def _extract_code_snippet(
        self, 
        content: str, 
        line_number: int,
        context_lines: int = 3
    ) -> str:
        """提取代码片段"""
        lines = content.split("\n")
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        snippet_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line_number - 1 else "    "
            snippet_lines.append(f"{prefix}{lines[i]}")
        
        return "\n".join(snippet_lines)
    
    def _cache_error_context(self, error: ValidationError, context: Dict[str, Any]):
        """缓存错误上下文"""
        error_key = f"{error.code}:{error.path}"
        if error_key not in self.error_contexts:
            self.error_contexts[error_key] = []
        self.error_contexts[error_key].append({
            "error": error,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
    
    def generate_fix_suggestions(
        self,
        errors: List[ValidationError],
        spec_content: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        根据错误列表生成修复建议
        
        Args:
            errors: 错误列表
            spec_content: 规范内容
            
        Returns:
            Dict[str, List[str]]: 按错误路径分组的修复建议
        """
        suggestions = {}
        
        for error in errors:
            path = error.path
            if path not in suggestions:
                suggestions[path] = []
            
            suggestions[path].append(error.suggestion)
            
            additional = self._generate_additional_suggestions(error, spec_content)
            suggestions[path].extend(additional)
        
        return suggestions
    
    def _generate_additional_suggestions(
        self,
        error: ValidationError,
        spec_content: Optional[str]
    ) -> List[str]:
        """生成额外的修复建议"""
        additional = []
        
        if error.code == "missing_required_field":
            additional.append("检查规范模板以确保所有必需字段都已填写")
        
        elif error.code == "invalid_type":
            additional.append("使用类型检查工具验证数据类型")
        
        elif error.code == "circular_reference":
            additional.append("考虑使用接口或抽象类解耦依赖关系")
        
        elif error.code == "undefined_reference":
            additional.append("检查拼写错误或大小写敏感问题")
        
        return additional
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        stats = {
            "total_errors": 0,
            "by_type": {},
            "by_severity": {},
            "most_common": []
        }
        
        for error_key, contexts in self.error_contexts.items():
            error_type = error_key.split(":")[0]
            stats["by_type"][error_type] = stats["by_type"].get(error_type, 0) + len(contexts)
            stats["total_errors"] += len(contexts)
            
            for ctx in contexts:
                severity = ctx["error"].severity.value
                stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
        
        sorted_types = sorted(
            stats["by_type"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        stats["most_common"] = sorted_types[:5]
        
        return stats


class SpecFormatValidator:
    """
    规范格式验证器
    
    支持多种规范格式的验证：
    - OpenAPI/Swagger
    - AsyncAPI
    - JSON Schema
    - GraphQL Schema
    - Protocol Buffers
    - 自定义格式
    """
    
    FORMAT_SIGNATURES = {
        "openapi": ["openapi", "swagger", "paths", "info"],
        "asyncapi": ["asyncapi", "channels", "components"],
        "json_schema": ["$schema", "type", "properties"],
        "graphql": ["type", "query", "mutation", "schema"],
        "protobuf": ["syntax", "message", "service", "rpc"],
        "sdd": ["apiVersion", "kind", "metadata", "spec"],
    }
    
    def __init__(self):
        self.detected_format: str = "unknown"
        self.format_confidence: float = 0.0
    
    def detect_format(self, content: str, source_format: str) -> Tuple[str, float]:
        """
        自动检测规范格式
        
        Args:
            content: 规范内容
            source_format: 源文件格式
            
        Returns:
            Tuple[str, float]: (检测到的格式, 置信度)
        """
        content_lower = content.lower()
        scores = {}
        
        for fmt, signatures in self.FORMAT_SIGNATURES.items():
            score = sum(1 for sig in signatures if sig in content_lower)
            scores[fmt] = score / len(signatures)
        
        if scores:
            best_format = max(scores, key=scores.get)
            confidence = scores[best_format]
            
            if confidence > 0.3:
                self.detected_format = best_format
                self.format_confidence = confidence
                return best_format, confidence
        
        return source_format, 0.5
    
    def validate_format_compliance(
        self,
        content: str,
        detected_format: str
    ) -> ValidationResult:
        """
        验证格式合规性
        
        Args:
            content: 规范内容
            detected_format: 检测到的格式
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)
        
        if detected_format == "openapi":
            result = self._validate_openapi_format(content)
        elif detected_format == "asyncapi":
            result = self._validate_asyncapi_format(content)
        elif detected_format == "json_schema":
            result = self._validate_json_schema_format(content)
        elif detected_format == "sdd":
            result = self._validate_sdd_format(content)
        
        return result
    
    def _validate_openapi_format(self, content: str) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            if field not in content:
                result.add_error(
                    f"openapi.{field}",
                    f"OpenAPI规范缺少必需字段: {field}",
                    f"添加 {field} 字段以符合OpenAPI规范"
                )
        
        return result
    
    def _validate_asyncapi_format(self, content: str) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        required_fields = ["asyncapi", "info", "channels"]
        for field in required_fields:
            if field not in content:
                result.add_error(
                    f"asyncapi.{field}",
                    f"AsyncAPI规范缺少必需字段: {field}",
                    f"添加 {field} 字段以符合AsyncAPI规范"
                )
        
        return result
    
    def _validate_json_schema_format(self, content: str) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        if "$schema" not in content:
            result.add_warning(
                "json_schema.$schema",
                "JSON Schema建议添加$schema字段",
                "添加$schema字段以明确Schema版本"
            )
        
        if "type" not in content:
            result.add_warning(
                "json_schema.type",
                "JSON Schema建议定义type字段",
                "添加type字段以明确数据类型"
            )
        
        return result
    
    def _validate_sdd_format(self, content: str) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        required_fields = ["apiVersion", "kind", "metadata"]
        for field in required_fields:
            if field not in content:
                result.add_error(
                    f"sdd.{field}",
                    f"SDD规范缺少必需字段: {field}",
                    f"添加 {field} 字段以符合SDD规范"
                )
        
        return result


class EnhancedValidationError(ValidationError):
    """
    增强的验证错误数据类
    
    扩展基础验证错误，添加更多上下文信息。
    """
    error_code: str = ""
    category: str = "general"
    fix_complexity: str = "simple"
    related_errors: List[str] = field(default_factory=list)
    documentation_links: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)


class EnhancedSDDSpecParser:
    """
    增强的SDD规范解析器
    
    整合所有增强功能：
    - 异步操作规范解析
    - 增强的错误报告
    - 嵌套结构深度解析
    - 条件逻辑智能解析
    - 多格式支持与自动检测
    - 规范验证功能
    """
    
    def __init__(self):
        self.nested_parser = NestedStructureParser()
        self.conditional_parser = ConditionalRuleParser()
        self.state_machine_parser = StateMachineParser()
        self.async_parser = AsyncOperationParser()
        self.type_parser = ComplexTypeParser()
        self.validator = SpecCompletenessValidator()
        self.error_reporter = EnhancedErrorReporter()
        self.format_validator = SpecFormatValidator()
        self._validation_cache: Dict[str, ValidationResult] = {}
    
    def parse_enhanced(
        self,
        content: str,
        source_format: str,
        source_path: str = ""
    ) -> Tuple[SDDSpecification, ValidationResult]:
        """
        执行增强的规范解析
        
        Args:
            content: 规范内容
            source_format: 源格式
            source_path: 源路径
            
        Returns:
            Tuple[SDDSpecification, ValidationResult]: 解析结果和验证结果
        """
        detected_format, confidence = self.format_validator.detect_format(content, source_format)
        
        if confidence > 0.7 and detected_format != source_format:
            self.error_reporter.logger.info(
                f"检测到规范格式可能为 {detected_format} (置信度: {confidence:.2f})"
            )
        
        parsed = self._parse_content(content, source_format)
        
        spec = self._build_enhanced_specification(parsed, content, source_format, source_path)
        
        validation_result = self._validate_enhanced(spec, content)
        
        format_validation = self.format_validator.validate_format_compliance(content, detected_format)
        validation_result.merge(format_validation)
        
        semantic_validation = self._validate_semantic_rules(spec, content)
        validation_result.merge(semantic_validation)
        
        cache_key = hashlib.md5(content.encode()).hexdigest()
        self._validation_cache[cache_key] = validation_result
        
        return spec, validation_result
    
    def _validate_semantic_rules(
        self,
        spec: SDDSpecification,
        content: str
    ) -> ValidationResult:
        """
        验证语义规则
        
        检查规范的语义一致性，包括：
        - 命名规范
        - 类型一致性
        - 引用完整性
        - 业务规则逻辑
        """
        result = ValidationResult(is_valid=True)
        
        self._validate_naming_conventions(spec, result)
        self._validate_type_consistency(spec, result)
        self._validate_reference_integrity(spec, result)
        self._validate_business_rule_logic(spec, result)
        
        return result
    
    def _validate_naming_conventions(
        self,
        spec: SDDSpecification,
        result: ValidationResult
    ):
        """验证命名规范"""
        naming_patterns = {
            "entity": r"^[A-Z][a-zA-Z0-9]*$",
            "attribute": r"^[a-z][a-zA-Z0-9_]*$",
            "method": r"^[a-z][a-zA-Z0-9_]*$",
            "constant": r"^[A-Z][A-Z0-9_]*$",
        }
        
        for attr in spec.attributes:
            if not re.match(naming_patterns["attribute"], attr.name):
                result.add_info(
                    f"spec.attributes.{attr.name}",
                    f"属性名称 '{attr.name}' 不符合驼峰命名规范",
                    "建议使用小驼峰命名法，如: userName, orderId"
                )
        
        for endpoint in spec.endpoints:
            if not re.match(r"^/[a-z0-9\-_/]*$", endpoint.path):
                result.add_info(
                    f"spec.endpoints.{endpoint.name}",
                    f"端点路径 '{endpoint.path}' 不符合RESTful规范",
                    "建议使用小写字母和连字符，如: /api/v1/user-orders"
                )
    
    def _validate_type_consistency(
        self,
        spec: SDDSpecification,
        result: ValidationResult
    ):
        """验证类型一致性"""
        defined_types = set()
        for type_def in spec.type_definitions:
            defined_types.add(type_def.name.lower())
        
        for attr in spec.attributes:
            if attr.complex_type:
                type_name = attr.complex_type.name.lower()
                if type_name not in defined_types and type_name not in self.type_parser.PRIMITIVE_TYPES:
                    is_builtin = type_name in ["array", "list", "dict", "map", "set", "optional", "promise"]
                    if not is_builtin:
                        result.add_warning(
                            f"spec.attributes.{attr.name}",
                            f"属性 '{attr.name}' 使用了未定义的类型: {attr.complex_type.to_type_string()}",
                            "在 typeDefinitions 中定义该类型或检查拼写"
                        )
    
    def _validate_reference_integrity(
        self,
        spec: SDDSpecification,
        result: ValidationResult
    ):
        """验证引用完整性"""
        defined_elements = set()
        
        for attr in spec.attributes:
            defined_elements.add(attr.name)
        for endpoint in spec.endpoints:
            defined_elements.add(endpoint.name)
        for sm in spec.state_machines:
            defined_elements.add(sm.id)
            for state in sm.states:
                defined_elements.add(state.name)
        
        for rule in spec.conditional_rules:
            for dep in rule.dependencies:
                if dep not in defined_elements:
                    result.add_warning(
                        f"spec.conditionalRules.{rule.id}",
                        f"规则 '{rule.name}' 引用了未定义的元素: {dep}",
                        "确保引用的目标元素已定义"
                    )
    
    def _validate_business_rule_logic(
        self,
        spec: SDDSpecification,
        result: ValidationResult
    ):
        """验证业务规则逻辑"""
        for rule in spec.conditional_rules:
            if not rule.condition:
                result.add_warning(
                    f"spec.conditionalRules.{rule.id}",
                    f"规则 '{rule.name}' 缺少条件定义",
                    "添加 condition 字段定义触发条件"
                )
                continue
            
            is_valid, error_msg = self.conditional_parser.validate_condition_syntax(rule.condition)
            if not is_valid:
                result.add_error(
                    f"spec.conditionalRules.{rule.id}.condition",
                    f"规则 '{rule.name}' 的条件语法无效: {error_msg}",
                    "检查条件表达式的语法正确性"
                )
            
            if not rule.then_branch:
                result.add_warning(
                    f"spec.conditionalRules.{rule.id}",
                    f"规则 '{rule.name}' 缺少执行分支",
                    "添加 then 字段定义条件满足时的行为"
                )
    
    def _parse_content(self, content: str, source_format: str) -> Dict[str, Any]:
        """解析内容"""
        if source_format == "yaml":
            return yaml.safe_load(content)
        elif source_format == "json":
            return json.loads(content)
        else:
            return self._parse_markdown_enhanced(content)
    
    def _parse_markdown_enhanced(self, content: str) -> Dict[str, Any]:
        """增强的Markdown解析"""
        spec = {
            "id": self._extract_id(content),
            "name": self._extract_name(content),
            "version": self._extract_version(content),
            "interfaces": self._extract_interfaces(content),
            "data_models": self._extract_data_models(content),
            "behavior_rules": self._extract_behavior_rules(content),
            "constraints": self._extract_constraints(content),
            "async_operations": self._extract_async_operations(content),
            "state_machines": self._extract_state_machines(content)
        }
        return spec
    
    def _extract_async_operations(self, content: str) -> List[Dict[str, Any]]:
        """从Markdown中提取异步操作定义"""
        operations = []
        
        async_pattern = r"##\s*(?:异步操作|Async\s*Operations?)[\s\S]*?(?=\n##|\Z)"
        for match in re.finditer(async_pattern, content, re.IGNORECASE):
            section = match.group(0)
            
            op_pattern = r"###\s*(.+?)\s*\n([\s\S]*?)(?=\n###|\n##|\Z)"
            for op_match in re.finditer(op_pattern, section):
                op_name = op_match.group(1).strip()
                op_content = op_match.group(2)
                
                operation = {
                    "name": op_name,
                    "description": self._extract_description(op_content),
                    "inputType": self._extract_type(op_content, "输入"),
                    "outputType": self._extract_type(op_content, "输出"),
                    "timeout": self._extract_timeout(op_content),
                    "retryPolicy": self._extract_retry_policy(op_content)
                }
                operations.append(operation)
        
        return operations
    
    def _extract_state_machines(self, content: str) -> List[Dict[str, Any]]:
        """从Markdown中提取状态机定义"""
        state_machines = []
        
        sm_pattern = r"##\s*(?:状态机|State\s*Machine)[\s\S]*?(?=\n##|\Z)"
        for match in re.finditer(sm_pattern, content, re.IGNORECASE):
            section = match.group(0)
            
            sm = {
                "name": self._extract_sm_name(section),
                "initialState": self._extract_initial_state(section),
                "states": self._extract_states(section),
                "transitions": self._extract_transitions(section),
                "finalStates": self._extract_final_states(section)
            }
            state_machines.append(sm)
        
        return state_machines
    
    def _extract_sm_name(self, section: str) -> str:
        match = re.search(r"###\s*(.+?)(?:\s*$|\n)", section)
        return match.group(1).strip() if match else "未命名状态机"
    
    def _extract_initial_state(self, section: str) -> str:
        match = re.search(r"(?:初始状态|Initial\s*State)[：:]\s*(\w+)", section, re.IGNORECASE)
        return match.group(1) if match else ""
    
    def _extract_states(self, section: str) -> List[str]:
        states = []
        state_pattern = r"[-*]\s*(?:状态\s*)?(\w+)"
        for match in re.finditer(state_pattern, section):
            states.append(match.group(1))
        return states
    
    def _extract_transitions(self, section: str) -> List[Dict[str, str]]:
        transitions = []
        trans_pattern = r"(\w+)\s*->\s*(\w+)\s*(?::\s*(.+))?"
        for match in re.finditer(trans_pattern, section):
            transitions.append({
                "from": match.group(1),
                "to": match.group(2),
                "trigger": match.group(3).strip() if match.group(3) else ""
            })
        return transitions
    
    def _extract_final_states(self, section: str) -> List[str]:
        match = re.search(r"(?:最终状态|Final\s*States?)[：:]\s*(.+)", section, re.IGNORECASE)
        if match:
            return [s.strip() for s in match.group(1).split(",")]
        return []
    
    def _extract_type(self, content: str, label: str) -> str:
        pattern = rf"(?:{label}|Input|Output)[：:]\s*(\w+(?:<[^>]+>)?)"
        match = re.search(pattern, content, re.IGNORECASE)
        return match.group(1) if match else "any"
    
    def _extract_timeout(self, content: str) -> Optional[int]:
        match = re.search(r"(?:超时|Timeout)[：:]\s*(\d+)\s*(?:ms|毫秒)?", content, re.IGNORECASE)
        return int(match.group(1)) if match else None
    
    def _extract_retry_policy(self, content: str) -> Dict[str, Any]:
        policy = {}
        
        max_retries = re.search(r"(?:最大重试|Max\s*Retries)[：:]\s*(\d+)", content, re.IGNORECASE)
        if max_retries:
            policy["max_retries"] = int(max_retries.group(1))
        
        strategy = re.search(r"(?:重试策略|Retry\s*Strategy)[：:]\s*(\w+)", content, re.IGNORECASE)
        if strategy:
            policy["strategy"] = strategy.group(1).lower()
        
        return policy
    
    def _extract_description(self, content: str) -> str:
        lines = content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith(("#", "-", "*", "|")):
                return line
        return ""
    
    def _extract_id(self, content: str) -> str:
        patterns = [
            r"规范ID[：:]\s*(\S+)",
            r"Spec\s*ID[：:]\s*(\S+)",
            r"id[：:]\s*(\S+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        return f"SPC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _extract_name(self, content: str) -> str:
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1).strip() if match else "未命名规范"
    
    def _extract_version(self, content: str) -> str:
        match = re.search(r"版本[：:]\s*(\S+)", content)
        return match.group(1) if match else "v1.0"
    
    def _extract_interfaces(self, content: str) -> List[Dict[str, Any]]:
        interfaces = []
        
        interface_pattern = r"##\s*(?:接口定义|Interface)[\s\S]*?(?=\n##|\Z)"
        for match in re.finditer(interface_pattern, content):
            section = match.group(0)
            
            method_pattern = r"###\s*(.+?)\s*\n([\s\S]*?)(?=\n###|\n##|\Z)"
            for method_match in re.finditer(method_pattern, section):
                interface = {
                    "name": method_match.group(1).strip(),
                    "methods": [],
                    "parameters": self._extract_parameters(method_match.group(2)),
                    "return_type": self._extract_return_type(method_match.group(2)),
                    "description": self._extract_description(method_match.group(2)),
                    "exceptions": self._extract_exceptions_from_section(method_match.group(2))
                }
                interfaces.append(interface)
        
        return interfaces
    
    def _extract_parameters(self, section: str) -> List[Dict[str, Any]]:
        parameters = []
        param_pattern = r"[-*]\s*(\w+)(?:\s*[\(（](\w+)[\)）])?(?:[：:]\s*(.+))?$"
        
        for line in section.split("\n"):
            match = re.match(param_pattern, line.strip())
            if match:
                parameters.append({
                    "name": match.group(1),
                    "type": match.group(2) or "any",
                    "description": match.group(3).strip() if match.group(3) else ""
                })
        
        return parameters
    
    def _extract_return_type(self, section: str) -> str:
        match = re.search(r"(?:返回|Return)[：:]\s*(\w+)", section)
        return match.group(1) if match else "void"
    
    def _extract_exceptions_from_section(self, section: str) -> List[str]:
        exceptions = []
        exc_pattern = r"(?:异常|Exception|错误|Error)[：:]\s*(\w+)"
        
        for match in re.finditer(exc_pattern, section):
            exceptions.append(match.group(1))
        
        return exceptions
    
    def _extract_data_models(self, content: str) -> List[Dict[str, Any]]:
        models = []
        
        model_pattern = r"##\s*(?:数据模型|Data\s*Model|实体定义)[\s\S]*?(?=\n##|\Z)"
        for match in re.finditer(model_pattern, content):
            section = match.group(0)
            
            attr_pattern = r"[-*]\s*(.+?)(?:[：:]\s*(.+))?$"
            attributes = []
            for line in section.split("\n"):
                attr_match = re.match(attr_pattern, line.strip())
                if attr_match:
                    attr_name = attr_match.group(1).strip()
                    attr_desc = attr_match.group(2).strip() if attr_match.group(2) else ""
                    
                    type_match = re.search(r"类型[：:]\s*(\w+)", attr_desc)
                    attr_type = type_match.group(1) if type_match else "string"
                    
                    attributes.append({
                        "name": attr_name,
                        "type": attr_type,
                        "description": re.sub(r"[，,]?\s*类型[：:]\s*\w+", "", attr_desc).strip(),
                        "required": "必填" in attr_desc or "required" in attr_desc.lower()
                    })
            
            if attributes:
                models.append({
                    "name": self._extract_model_name(section),
                    "attributes": attributes,
                    "relationships": [],
                    "constraints": []
                })
        
        return models
    
    def _extract_model_name(self, section: str) -> str:
        match = re.search(r"###\s*(.+?)(?:\s*$|\n)", section)
        return match.group(1).strip() if match else "未命名模型"
    
    def _extract_behavior_rules(self, content: str) -> List[Dict[str, Any]]:
        rules = []
        
        rule_pattern = r"##\s*(?:行为规则|Business\s*Rules?|业务规则)[\s\S]*?(?=\n##|\Z)"
        for match in re.finditer(rule_pattern, content):
            section = match.group(0)
            
            single_rule_pattern = r"[-*]\s*(?:规则\s*(\d+)[.：:])?\s*(.+?)(?:[：:]\s*(.+))?$"
            for line in section.split("\n"):
                rule_match = re.match(single_rule_pattern, line.strip())
                if rule_match:
                    rule_id = rule_match.group(1) or f"R{len(rules)+1:03d}"
                    rule_name = rule_match.group(2).strip()
                    rule_desc = rule_match.group(3).strip() if rule_match.group(3) else ""
                    
                    rules.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "condition": self._extract_condition(rule_desc),
                        "action": self._extract_action(rule_desc),
                        "description": rule_desc
                    })
        
        return rules
    
    def _extract_condition(self, text: str) -> str:
        match = re.search(r"(?:当|When|如果|If)[：:]\s*(.+?)(?=(?:则|Then|执行|Execute)|$)", text)
        return match.group(1).strip() if match else ""
    
    def _extract_action(self, text: str) -> str:
        match = re.search(r"(?:则|Then|执行|Execute)[：:]\s*(.+)$", text)
        return match.group(1).strip() if match else ""
    
    def _extract_constraints(self, content: str) -> List[Dict[str, Any]]:
        constraints = []
        
        constraint_pattern = r"##\s*(?:约束条件|Constraints?|限制)[\s\S]*?(?=\n##|\Z)"
        for match in re.finditer(constraint_pattern, content):
            section = match.group(0)
            
            single_constraint = r"[-*]\s*(.+?)(?:[：:]\s*(.+))?$"
            for line in section.split("\n"):
                c_match = re.match(single_constraint, line.strip())
                if c_match:
                    constraints.append({
                        "name": c_match.group(1).strip(),
                        "description": c_match.group(2).strip() if c_match.group(2) else ""
                    })
        
        return constraints
    
    def _build_enhanced_specification(
        self,
        parsed: Dict[str, Any],
        raw_content: str,
        source_format: str,
        source_path: str
    ) -> SDDSpecification:
        """构建增强的规范对象"""
        metadata = self._build_metadata(parsed)
        
        nested_structures = self.nested_parser.parse(parsed.get("spec", parsed))
        
        conditional_rules = self.conditional_parser.parse(parsed.get("conditionalRules", parsed.get("conditional_rules", [])))
        
        async_operations = self.async_parser.parse(parsed.get("asyncOperations", parsed.get("async_operations", [])))
        
        state_machines = []
        for sm_data in parsed.get("stateMachines", parsed.get("state_machines", [])):
            sm = self.state_machine_parser.parse(sm_data)
            state_machines.append(sm)
        
        spec = SDDSpecification(
            api_version=parsed.get("apiVersion", parsed.get("api_version", "v1")),
            kind=SpecType(parsed.get("kind", "EntitySpec")),
            metadata=metadata,
            spec=parsed.get("spec", {}),
            raw_content=raw_content,
            source_format=SpecFormat(source_format),
            source_path=source_path,
            nested_structures=nested_structures,
            conditional_rules=conditional_rules,
            state_machines=state_machines
        )
        
        spec.type_definitions = self._extract_type_definitions(parsed)
        
        return spec
    
    def _build_metadata(self, parsed: Dict[str, Any]) -> SpecMetadata:
        """构建元数据"""
        meta = parsed.get("metadata", {})
        
        return SpecMetadata(
            id=parsed.get("id", meta.get("id", "")),
            name=parsed.get("name", meta.get("name", "未命名规范")),
            version=parsed.get("version", meta.get("version", "v1.0")),
            namespace=meta.get("namespace", "default"),
            status=meta.get("status", "draft"),
            author=meta.get("author", ""),
            created=meta.get("created", ""),
            modified=meta.get("modified", ""),
            tags=meta.get("tags", []),
            annotations=meta.get("annotations", {}),
            dependencies=meta.get("dependencies", []),
            extends=meta.get("extends"),
            compatibility_version=meta.get("compatibilityVersion", meta.get("compatibility_version", ""))
        )
    
    def _extract_type_definitions(self, parsed: Dict[str, Any]) -> List[ComplexType]:
        """提取类型定义"""
        type_defs = []
        
        for type_data in parsed.get("typeDefinitions", parsed.get("type_definitions", [])):
            if isinstance(type_data, str):
                type_def = self.type_parser.parse_type_string(type_data)
            elif isinstance(type_data, dict):
                type_str = type_data.get("type", type_data.get("$type", "any"))
                type_def = self.type_parser.parse_type_string(type_str)
            else:
                continue
            type_defs.append(type_def)
        
        return type_defs
    
    def _validate_enhanced(
        self,
        spec: SDDSpecification,
        content: str
    ) -> ValidationResult:
        """执行增强的验证"""
        result = self.validator.validate(spec)
        
        for sm in spec.state_machines:
            sm_validation = self.state_machine_parser.validate(sm)
            result.merge(sm_validation)
        
        for idx, operation in enumerate(self.async_parser._operation_registry.values()):
            async_validation = self.async_parser.validate(operation)
            for error in async_validation.errors:
                enhanced_error = self.error_reporter.create_enhanced_error(
                    error.code,
                    error.path,
                    {"operation": operation.name, "idx": idx},
                    content
                )
                result.errors.append(enhanced_error)
        
        for rule in spec.conditional_rules:
            is_valid, error_msg = self.conditional_parser.validate_condition_syntax(rule.condition)
            if not is_valid:
                enhanced_error = self.error_reporter.create_enhanced_error(
                    "invalid_format",
                    f"conditionalRules.{rule.id}.condition",
                    {"rule": rule.name, "detail": error_msg},
                    content
                )
                result.errors.append(enhanced_error)
        
        return result


# ============================================================================
# 增强的规范语法数据类
# ============================================================================

@dataclass
class MethodDefinition:
    """
    方法定义数据类
    
    表示接口中的方法定义，支持参数、返回值、异常等完整定义。
    """
    name: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: str = "void"
    description: str = ""
    exceptions: List[str] = field(default_factory=list)
    is_async: bool = False
    is_static: bool = False
    access_modifier: str = "public"
    deprecated: bool = False
    deprecation_message: str = ""
    examples: List[Dict[str, Any]] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    complexity: str = "O(1)"
    side_effects: List[str] = field(default_factory=list)


@dataclass
class InterfaceDefinition:
    """
    接口定义数据类
    
    表示完整的接口定义，包含方法、属性、事件等。
    """
    id: str
    name: str
    namespace: str = "default"
    description: str = ""
    methods: List[MethodDefinition] = field(default_factory=list)
    properties: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    extends: List[str] = field(default_factory=list)
    implements: List[str] = field(default_factory=list)
    generics: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    annotations: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    deprecated: bool = False
    author: str = ""
    since_version: str = ""


@dataclass
class DataModelProperty:
    """
    数据模型属性数据类
    
    表示数据模型中的属性定义。
    """
    name: str
    type: str
    description: str = ""
    required: bool = True
    unique: bool = False
    default: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum_values: List[Any] = field(default_factory=list)
    format: Optional[str] = None
    example: Any = None
    deprecated: bool = False
    read_only: bool = False
    write_only: bool = False
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    indexed: bool = False
    unique_index: bool = False


@dataclass
class DataModelDefinition:
    """
    数据模型定义数据类
    
    表示完整的数据模型定义，支持继承、组合、验证规则等。
    """
    id: str
    name: str
    namespace: str = "default"
    description: str = ""
    properties: List[DataModelProperty] = field(default_factory=list)
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    mixins: List[str] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    computed_properties: List[Dict[str, Any]] = field(default_factory=list)
    hooks: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    deprecated: bool = False


@dataclass
class BehaviorRuleDefinition:
    """
    行为规则定义数据类
    
    表示完整的业务行为规则定义。
    """
    id: str
    name: str
    description: str = ""
    category: str = "general"
    priority: int = 0
    condition: str = ""
    action: str = ""
    else_action: Optional[str] = None
    trigger: str = ""
    scope: str = "global"
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    error_handling: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[int] = None
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    audit_log: bool = False
    version: str = "1.0.0"


# ============================================================================
# 增强的规范语法解析器
# ============================================================================

class EnhancedSpecSyntaxParser:
    """
    增强的规范语法解析器
    
    支持解析更丰富的规范语法，包括：
    - 完整的接口定义（方法、属性、事件、泛型）
    - 复杂的数据模型（继承、组合、验证规则）
    - 丰富的行为规则（条件、动作、触发器）
    """
    
    def __init__(self):
        self.type_parser = ComplexTypeParser()
        self._interface_registry: Dict[str, InterfaceDefinition] = {}
        self._model_registry: Dict[str, DataModelDefinition] = {}
        self._rule_registry: Dict[str, BehaviorRuleDefinition] = {}
    
    def parse_interface(self, data: Dict[str, Any]) -> InterfaceDefinition:
        """
        解析接口定义
        
        Args:
            data: 接口数据字典
            
        Returns:
            InterfaceDefinition: 解析后的接口定义
        """
        interface_id = data.get("id", f"IF-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        methods = []
        for method_data in data.get("methods", []):
            method = self._parse_method(method_data)
            methods.append(method)
        
        interface = InterfaceDefinition(
            id=interface_id,
            name=data.get("name", "未命名接口"),
            namespace=data.get("namespace", "default"),
            description=data.get("description", ""),
            methods=methods,
            properties=data.get("properties", []),
            events=data.get("events", []),
            extends=data.get("extends", []) if isinstance(data.get("extends"), list) else [data.get("extends")] if data.get("extends") else [],
            implements=data.get("implements", []),
            generics=data.get("generics", data.get("typeParameters", [])),
            constraints=data.get("constraints", []),
            annotations=data.get("annotations", {}),
            version=data.get("version", "1.0.0"),
            deprecated=data.get("deprecated", False),
            author=data.get("author", ""),
            since_version=data.get("since", data.get("sinceVersion", ""))
        )
        
        self._interface_registry[interface_id] = interface
        return interface
    
    def _parse_method(self, data: Dict[str, Any]) -> MethodDefinition:
        """解析方法定义"""
        return MethodDefinition(
            name=data.get("name", "未命名方法"),
            parameters=data.get("parameters", data.get("params", [])),
            return_type=data.get("returnType", data.get("return", "void")),
            description=data.get("description", ""),
            exceptions=data.get("exceptions", data.get("throws", [])),
            is_async=data.get("async", data.get("isAsync", False)),
            is_static=data.get("static", data.get("isStatic", False)),
            access_modifier=data.get("access", data.get("visibility", "public")),
            deprecated=data.get("deprecated", False),
            deprecation_message=data.get("deprecationMessage", ""),
            examples=data.get("examples", []),
            preconditions=data.get("preconditions", data.get("requires", [])),
            postconditions=data.get("postconditions", data.get("ensures", [])),
            complexity=data.get("complexity", "O(1)"),
            side_effects=data.get("sideEffects", [])
        )
    
    def parse_data_model(self, data: Dict[str, Any]) -> DataModelDefinition:
        """
        解析数据模型定义
        
        Args:
            data: 数据模型字典
            
        Returns:
            DataModelDefinition: 解析后的数据模型定义
        """
        model_id = data.get("id", f"DM-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        properties = []
        for prop_data in data.get("properties", data.get("attributes", [])):
            prop = self._parse_property(prop_data)
            properties.append(prop)
        
        model = DataModelDefinition(
            id=model_id,
            name=data.get("name", "未命名模型"),
            namespace=data.get("namespace", "default"),
            description=data.get("description", ""),
            properties=properties,
            extends=data.get("extends", data.get("extendsModel")),
            implements=data.get("implements", []),
            mixins=data.get("mixins", []),
            indexes=data.get("indexes", data.get("indices", [])),
            relationships=self._parse_relationships(data.get("relationships", [])),
            constraints=data.get("constraints", []),
            computed_properties=data.get("computedProperties", data.get("computed", [])),
            hooks=data.get("hooks", {}),
            metadata=data.get("metadata", {}),
            version=data.get("version", "1.0.0"),
            deprecated=data.get("deprecated", False)
        )
        
        self._model_registry[model_id] = model
        return model
    
    def _parse_property(self, data: Dict[str, Any]) -> DataModelProperty:
        """解析属性定义"""
        if isinstance(data, str):
            return DataModelProperty(name=data, type="string")
        
        return DataModelProperty(
            name=data.get("name", "未命名属性"),
            type=data.get("type", "string"),
            description=data.get("description", ""),
            required=data.get("required", True),
            unique=data.get("unique", False),
            default=data.get("default"),
            min_value=data.get("minValue", data.get("min")),
            max_value=data.get("maxValue", data.get("max")),
            min_length=data.get("minLength", data.get("minLength")),
            max_length=data.get("maxLength", data.get("maxLength")),
            pattern=data.get("pattern", data.get("regex")),
            enum_values=data.get("enumValues", data.get("enum", [])),
            format=data.get("format"),
            example=data.get("example"),
            deprecated=data.get("deprecated", False),
            read_only=data.get("readOnly", data.get("readonly", False)),
            write_only=data.get("writeOnly", data.get("writeonly", False)),
            validation_rules=data.get("validationRules", []),
            indexed=data.get("indexed", False),
            unique_index=data.get("uniqueIndex", False)
        )
    
    def _parse_relationships(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """解析关系定义"""
        relationships = []
        for rel_data in data:
            relationship = {
                "name": rel_data.get("name", ""),
                "type": rel_data.get("type", "association"),
                "target": rel_data.get("target", rel_data.get("model", "")),
                "cardinality": rel_data.get("cardinality", "1:1"),
                "foreign_key": rel_data.get("foreignKey", rel_data.get("fk", "")),
                "through": rel_data.get("through"),
                "cascade": rel_data.get("cascade", False),
                "nullable": rel_data.get("nullable", True),
                "description": rel_data.get("description", "")
            }
            relationships.append(relationship)
        return relationships
    
    def parse_behavior_rule(self, data: Dict[str, Any]) -> BehaviorRuleDefinition:
        """
        解析行为规则定义
        
        Args:
            data: 行为规则字典
            
        Returns:
            BehaviorRuleDefinition: 解析后的行为规则定义
        """
        rule_id = data.get("id", data.get("ruleId", f"BR-{datetime.now().strftime('%Y%m%d%H%M%S')}"))
        
        rule = BehaviorRuleDefinition(
            id=rule_id,
            name=data.get("name", "未命名规则"),
            description=data.get("description", ""),
            category=data.get("category", "general"),
            priority=data.get("priority", 0),
            condition=data.get("condition", data.get("when", "")),
            action=data.get("action", data.get("then", "")),
            else_action=data.get("elseAction", data.get("else")),
            trigger=data.get("trigger", data.get("on", "")),
            scope=data.get("scope", "global"),
            enabled=data.get("enabled", True),
            tags=data.get("tags", []),
            dependencies=data.get("dependencies", []),
            conflicts=data.get("conflicts", []),
            parameters=data.get("parameters", {}),
            examples=data.get("examples", []),
            error_handling=data.get("errorHandling", {}),
            timeout=data.get("timeout"),
            retry_policy=data.get("retryPolicy", {}),
            audit_log=data.get("auditLog", False),
            version=data.get("version", "1.0.0")
        )
        
        self._rule_registry[rule_id] = rule
        return rule
    
    def parse_from_markdown(self, content: str) -> Dict[str, Any]:
        """
        从Markdown内容解析完整规范
        
        Args:
            content: Markdown内容
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        result = {
            "interfaces": [],
            "data_models": [],
            "behavior_rules": [],
            "constraints": []
        }
        
        result["interfaces"] = self._extract_interfaces_from_markdown(content)
        result["data_models"] = self._extract_data_models_from_markdown(content)
        result["behavior_rules"] = self._extract_behavior_rules_from_markdown(content)
        result["constraints"] = self._extract_constraints_from_markdown(content)
        
        return result
    
    def _extract_interfaces_from_markdown(self, content: str) -> List[InterfaceDefinition]:
        """从Markdown提取接口定义"""
        interfaces = []
        
        interface_pattern = r"##\s*(?:接口定义|Interface\s*Definition)[\s\S]*?(?=\n##|\Z)"
        for match in re.finditer(interface_pattern, content, re.IGNORECASE):
            section = match.group(0)
            
            interface_data = {
                "name": self._extract_interface_name(section),
                "description": self._extract_section_description(section),
                "methods": self._extract_methods_from_section(section),
                "properties": self._extract_properties_from_section(section),
                "extends": self._extract_extends(section),
                "generics": self._extract_generics(section)
            }
            
            interfaces.append(self.parse_interface(interface_data))
        
        return interfaces
    
    def _extract_interface_name(self, section: str) -> str:
        match = re.search(r"###\s*(?:interface\s+)?(\w+)", section, re.IGNORECASE)
        return match.group(1) if match else "未命名接口"
    
    def _extract_section_description(self, section: str) -> str:
        lines = section.strip().split("\n")
        for line in lines[1:]:
            line = line.strip()
            if line and not line.startswith(("#", "-", "*", "|", "```")):
                return line
        return ""
    
    def _extract_methods_from_section(self, section: str) -> List[Dict[str, Any]]:
        methods = []
        
        method_pattern = r"[-*]\s*(?:(public|private|protected)\s+)?(?:(async|static)\s+)?(\w+)\s*\(([^)]*)\)(?:\s*:\s*(\w+(?:<[^>]+>)?))?"
        
        for match in re.finditer(method_pattern, section):
            method = {
                "name": match.group(3),
                "access": match.group(1) or "public",
                "async": match.group(2) == "async",
                "static": match.group(2) == "static",
                "parameters": self._parse_parameters_string(match.group(4)),
                "returnType": match.group(5) or "void"
            }
            methods.append(method)
        
        return methods
    
    def _parse_parameters_string(self, params_str: str) -> List[Dict[str, Any]]:
        """解析参数字符串"""
        if not params_str.strip():
            return []
        
        parameters = []
        for param in params_str.split(","):
            param = param.strip()
            if not param:
                continue
            
            parts = param.split(":")
            name = parts[0].strip().lstrip("$")
            param_type = parts[1].strip() if len(parts) > 1 else "any"
            
            optional = param.endswith("?") or "?" in name
            name = name.rstrip("?")
            
            parameters.append({
                "name": name,
                "type": param_type.rstrip("?"),
                "optional": optional
            })
        
        return parameters
    
    def _extract_properties_from_section(self, section: str) -> List[Dict[str, Any]]:
        properties = []
        
        prop_pattern = r"[-*]\s*(\w+)\s*:\s*(\w+(?:<[^>]+>)?|\[[^\]]+\])(?:\s*(?:\/\/|#)\s*(.+))?$"
        
        for match in re.finditer(prop_pattern, section, re.MULTILINE):
            properties.append({
                "name": match.group(1),
                "type": match.group(2),
                "description": match.group(3).strip() if match.group(3) else ""
            })
        
        return properties
    
    def _extract_extends(self, section: str) -> List[str]:
        match = re.search(r"(?:extends|继承)[：:]\s*(\w+(?:\s*,\s*\w+)*)", section, re.IGNORECASE)
        if match:
            return [e.strip() for e in match.group(1).split(",")]
        return []
    
    def _extract_generics(self, section: str) -> List[str]:
        match = re.search(r"<(\w+(?:\s*,\s*\w+)*)>", section)
        if match:
            return [g.strip() for g in match.group(1).split(",")]
        return []
    
    def _extract_data_models_from_markdown(self, content: str) -> List[DataModelDefinition]:
        """从Markdown提取数据模型定义"""
        models = []
        
        model_pattern = r"##\s*(?:数据模型|Data\s*Model|实体定义|Entity)[\s\S]*?(?=\n##|\Z)"
        for match in re.finditer(model_pattern, content, re.IGNORECASE):
            section = match.group(0)
            
            model_data = {
                "name": self._extract_model_name_from_section(section),
                "description": self._extract_section_description(section),
                "properties": self._extract_model_properties(section),
                "extends": self._extract_extends(section),
                "relationships": self._extract_model_relationships(section),
                "indexes": self._extract_model_indexes(section)
            }
            
            models.append(self.parse_data_model(model_data))
        
        return models
    
    def _extract_model_name_from_section(self, section: str) -> str:
        match = re.search(r"###\s*(?:class\s+|model\s+)?(\w+)", section, re.IGNORECASE)
        return match.group(1) if match else "未命名模型"
    
    def _extract_model_properties(self, section: str) -> List[Dict[str, Any]]:
        properties = []
        
        table_pattern = r"\|(.+)\|\n\|[-|\s]+\|\n((?:\|.+\|\n?)+)"
        for match in re.finditer(table_pattern, section):
            headers = [h.strip() for h in match.group(1).split("|") if h.strip()]
            rows = match.group(2).strip().split("\n")
            
            for row in rows:
                cells = [c.strip() for c in row.split("|") if c.strip()]
                if cells and len(cells) >= 2:
                    prop = {"name": cells[0], "type": cells[1]}
                    if len(cells) > 2:
                        prop["description"] = cells[2]
                    if len(cells) > 3:
                        prop["required"] = cells[3].lower() in ["是", "yes", "true", "必填"]
                    properties.append(prop)
        
        list_pattern = r"[-*]\s*(\w+)(?:\s*[\(（](\w+)[\)）])?(?:\s*[：:]\s*(.+))?$"
        for line in section.split("\n"):
            match = re.match(list_pattern, line.strip())
            if match:
                prop = {
                    "name": match.group(1),
                    "type": match.group(2) or "string",
                    "description": match.group(3).strip() if match.group(3) else ""
                }
                if prop not in properties:
                    properties.append(prop)
        
        return properties
    
    def _extract_model_relationships(self, section: str) -> List[Dict[str, Any]]:
        relationships = []
        
        rel_pattern = r"(?:关系|Relationship)[：:]\s*\n((?:[-*].+\n?)+)"
        match = re.search(rel_pattern, section, re.IGNORECASE)
        if match:
            for line in match.group(1).strip().split("\n"):
                rel_match = re.match(r"[-*]\s*(\w+)\s*[-–—]\s*(\w+)\s*[-–—]\s*(\w+)", line.strip())
                if rel_match:
                    relationships.append({
                        "name": rel_match.group(1),
                        "type": rel_match.group(2),
                        "target": rel_match.group(3)
                    })
        
        return relationships
    
    def _extract_model_indexes(self, section: str) -> List[Dict[str, Any]]:
        indexes = []
        
        idx_pattern = r"(?:索引|Index)[：:]\s*\n((?:[-*].+\n?)+)"
        match = re.search(idx_pattern, section, re.IGNORECASE)
        if match:
            for line in match.group(1).strip().split("\n"):
                idx_match = re.match(r"[-*]\s*(\w+)(?:\s*\((\w+)\))?", line.strip())
                if idx_match:
                    indexes.append({
                        "fields": [idx_match.group(1)],
                        "type": idx_match.group(2) or "btree"
                    })
        
        return indexes
    
    def _extract_behavior_rules_from_markdown(self, content: str) -> List[BehaviorRuleDefinition]:
        """从Markdown提取行为规则定义"""
        rules = []
        
        rule_pattern = r"##\s*(?:行为规则|Business\s*Rules?|业务规则)[\s\S]*?(?=\n##|\Z)"
        for match in re.finditer(rule_pattern, content, re.IGNORECASE):
            section = match.group(0)
            
            single_rule_pattern = r"###\s*(?:规则\s*)?(\d+\.?\d*)?[.：:]?\s*(.+?)(?:\n|$)([\s\S]*?)(?=\n###|\n##|\Z)"
            for rule_match in re.finditer(single_rule_pattern, section):
                rule_id = rule_match.group(1) or f"R{len(rules)+1:03d}"
                rule_name = rule_match.group(2).strip()
                rule_content = rule_match.group(3)
                
                rule_data = {
                    "id": rule_id,
                    "name": rule_name,
                    "description": self._extract_section_description(rule_content),
                    "condition": self._extract_rule_condition(rule_content),
                    "action": self._extract_rule_action(rule_content),
                    "trigger": self._extract_rule_trigger(rule_content),
                    "priority": self._extract_rule_priority(rule_content),
                    "tags": self._extract_rule_tags(rule_content)
                }
                
                rules.append(self.parse_behavior_rule(rule_data))
        
        return rules
    
    def _extract_rule_condition(self, content: str) -> str:
        patterns = [
            r"(?:条件|Condition|当|When|如果|If)[：:]\s*(.+?)(?=\n[-*]|\n\n|\n(?:则|Then|执行|Action)|$)",
            r"WHEN\s+(.+?)(?:\s+THEN|$)"
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_rule_action(self, content: str) -> str:
        patterns = [
            r"(?:动作|Action|则|Then|执行)[：:]\s*(.+?)(?=\n[-*]|\n\n|\n(?:否则|Else)|$)",
            r"THEN\s+(.+?)(?:\s+ELSE|$)"
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_rule_trigger(self, content: str) -> str:
        match = re.search(r"(?:触发器|Trigger|事件|Event|On)[：:]\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
        return match.group(1).strip() if match else ""
    
    def _extract_rule_priority(self, content: str) -> int:
        match = re.search(r"(?:优先级|Priority)[：:]\s*(\d+)", content, re.IGNORECASE)
        return int(match.group(1)) if match else 0
    
    def _extract_rule_tags(self, content: str) -> List[str]:
        match = re.search(r"(?:标签|Tags)[：:]\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
        if match:
            return [t.strip() for t in match.group(1).split(",")]
        return []
    
    def _extract_constraints_from_markdown(self, content: str) -> List[Dict[str, Any]]:
        """从Markdown提取约束定义"""
        constraints = []
        
        constraint_pattern = r"##\s*(?:约束条件|Constraints?|限制)[\s\S]*?(?=\n##|\Z)"
        for match in re.finditer(constraint_pattern, content, re.IGNORECASE):
            section = match.group(0)
            
            single_constraint = r"[-*]\s*(.+?)(?:[：:]\s*(.+))?$"
            for line in section.split("\n"):
                c_match = re.match(single_constraint, line.strip())
                if c_match:
                    constraints.append({
                        "name": c_match.group(1).strip(),
                        "description": c_match.group(2).strip() if c_match.group(2) else ""
                    })
        
        return constraints
    
    def get_interface(self, interface_id: str) -> Optional[InterfaceDefinition]:
        """根据ID获取接口定义"""
        return self._interface_registry.get(interface_id)
    
    def get_data_model(self, model_id: str) -> Optional[DataModelDefinition]:
        """根据ID获取数据模型定义"""
        return self._model_registry.get(model_id)
    
    def get_behavior_rule(self, rule_id: str) -> Optional[BehaviorRuleDefinition]:
        """根据ID获取行为规则定义"""
        return self._rule_registry.get(rule_id)


# ============================================================================
# 测试用例骨架生成器
# ============================================================================

class TestCaseSkeletonGenerator:
    """
    测试用例骨架生成器
    
    根据规范自动生成测试用例骨架，支持：
    - 单元测试
    - 集成测试
    - API测试
    - 端到端测试
    - 性能测试
    - 安全测试
    """
    
    TEST_FRAMEWORKS = {
        "pytest": {
            "file_ext": ".py",
            "import": "import pytest",
            "test_decorator": "@pytest.mark.{marker}",
            "test_func": "def test_{name}():",
            "assertion": "assert {condition}",
            "fixture": "@pytest.fixture\ndef {name}():"
        },
        "jest": {
            "file_ext": ".test.js",
            "import": "",
            "test_decorator": "",
            "test_func": "test('{description}', () => {{",
            "assertion": "expect({actual}).{matcher}({expected});",
            "fixture": "const {name} = () => {{"
        },
        "junit": {
            "file_ext": "Test.java",
            "import": "import org.junit.*;",
            "test_decorator": "@Test",
            "test_func": "public void test{name}() {{",
            "assertion": "assert{type}({expected}, {actual});",
            "fixture": "@Before\npublic void setUp() {{"
        }
    }
    
    TEST_PATTERNS = {
        "happy_path": "正常流程测试",
        "edge_case": "边界条件测试",
        "error_handling": "错误处理测试",
        "negative": "负面测试",
        "security": "安全测试",
        "performance": "性能测试",
        "integration": "集成测试"
    }
    
    def __init__(self, framework: str = "pytest"):
        self.framework = framework
        self.syntax = self.TEST_FRAMEWORKS.get(framework, self.TEST_FRAMEWORKS["pytest"])
        self._generated_tests: Dict[str, TestSuite] = {}
    
    def generate_from_interface(self, interface: InterfaceDefinition) -> TestSuite:
        """
        从接口定义生成测试用例骨架
        
        Args:
            interface: 接口定义
            
        Returns:
            TestSuite: 生成的测试套件
        """
        test_cases = []
        
        for method in interface.methods:
            test_cases.extend(self._generate_method_tests(method, interface.name))
        
        for prop in interface.properties:
            test_cases.extend(self._generate_property_tests(prop, interface.name))
        
        suite = TestSuite(
            name=f"{interface.name}TestSuite",
            description=f"接口 {interface.name} 的测试套件",
            test_cases=test_cases,
            imports=[self.syntax["import"]],
            fixtures=self._generate_interface_fixtures(interface)
        )
        
        self._generated_tests[interface.id] = suite
        return suite
    
    def _generate_method_tests(self, method: MethodDefinition, interface_name: str) -> List[TestCase]:
        """为方法生成测试用例"""
        tests = []
        base_name = f"{interface_name}_{method.name}"
        
        tests.append(TestCase(
            id=f"TC-{base_name}-happy",
            name=f"test_{method.name}_success",
            description=f"测试 {method.name} 方法成功场景",
            test_type=TestType.UNIT,
            spec_element=f"{interface_name}.{method.name}",
            arrange=self._generate_arrange_for_method(method),
            act=f"result = instance.{method.name}({self._get_param_names(method.parameters)})",
            assert_=self._generate_assert_for_method(method),
            test_data=self._generate_test_data_for_method(method),
            markers=["unit", "happy_path"],
            priority="high"
        ))
        
        for param in method.parameters:
            if not param.get("optional", False):
                tests.append(TestCase(
                    id=f"TC-{base_name}-{param['name']}-missing",
                    name=f"test_{method.name}_missing_{param['name']}",
                    description=f"测试 {method.name} 缺少必需参数 {param['name']}",
                    test_type=TestType.UNIT,
                    spec_element=f"{interface_name}.{method.name}",
                    arrange=self._generate_arrange_for_method(method, exclude_param=param["name"]),
                    act=f"instance.{method.name}({self._get_param_names(method.parameters, exclude=param['name'])})",
                    assert_="assert exception is raised",
                    markers=["unit", "negative"],
                    priority="medium"
                ))
        
        for exception in method.exceptions:
            tests.append(TestCase(
                id=f"TC-{base_name}-{exception}",
                name=f"test_{method.name}_raises_{exception}",
                description=f"测试 {method.name} 抛出 {exception} 异常",
                test_type=TestType.UNIT,
                spec_element=f"{interface_name}.{method.name}",
                arrange=self._generate_arrange_for_exception(method, exception),
                act=f"instance.{method.name}({self._get_param_names(method.parameters)})",
                assert_=f"assert {exception} is raised",
                markers=["unit", "error_handling"],
                priority="medium"
            ))
        
        if method.is_async:
            tests.append(TestCase(
                id=f"TC-{base_name}-async",
                name=f"test_{method.name}_async_behavior",
                description=f"测试 {method.name} 异步行为",
                test_type=TestType.UNIT,
                spec_element=f"{interface_name}.{method.name}",
                arrange=self._generate_arrange_for_method(method),
                act=f"await instance.{method.name}({self._get_param_names(method.parameters)})",
                assert_="assert async operation completes",
                markers=["unit", "async"],
                priority="medium",
                timeout=5000
            ))
        
        return tests
    
    def _generate_property_tests(self, prop: Dict[str, Any], interface_name: str) -> List[TestCase]:
        """为属性生成测试用例"""
        tests = []
        prop_name = prop.get("name", "unknown")
        
        tests.append(TestCase(
            id=f"TC-{interface_name}-{prop_name}-get",
            name=f"test_{prop_name}_getter",
            description=f"测试 {prop_name} 属性获取",
            test_type=TestType.UNIT,
            spec_element=f"{interface_name}.{prop_name}",
            arrange="instance = create_instance()",
            act=f"value = instance.{prop_name}",
            assert_=f"assert value is not None",
            markers=["unit"],
            priority="low"
        ))
        
        if not prop.get("readOnly", False):
            tests.append(TestCase(
                id=f"TC-{interface_name}-{prop_name}-set",
                name=f"test_{prop_name}_setter",
                description=f"测试 {prop_name} 属性设置",
                test_type=TestType.UNIT,
                spec_element=f"{interface_name}.{prop_name}",
                arrange="instance = create_instance()",
                act=f"instance.{prop_name} = test_value",
                assert_=f"assert instance.{prop_name} == test_value",
                markers=["unit"],
                priority="low"
            ))
        
        return tests
    
    def generate_from_data_model(self, model: DataModelDefinition) -> TestSuite:
        """
        从数据模型生成测试用例骨架
        
        Args:
            model: 数据模型定义
            
        Returns:
            TestSuite: 生成的测试套件
        """
        test_cases = []
        
        for prop in model.properties:
            test_cases.extend(self._generate_property_validation_tests(prop, model.name))
        
        test_cases.extend(self._generate_model_crud_tests(model))
        test_cases.extend(self._generate_model_relationship_tests(model))
        
        suite = TestSuite(
            name=f"{model.name}TestSuite",
            description=f"数据模型 {model.name} 的测试套件",
            test_cases=test_cases,
            imports=[self.syntax["import"]],
            fixtures=self._generate_model_fixtures(model)
        )
        
        self._generated_tests[model.id] = suite
        return suite
    
    def _generate_property_validation_tests(self, prop: DataModelProperty, model_name: str) -> List[TestCase]:
        """为属性生成验证测试用例"""
        tests = []
        
        tests.append(TestCase(
            id=f"TC-{model_name}-{prop.name}-valid",
            name=f"test_{prop.name}_valid_value",
            description=f"测试 {prop.name} 有效值验证",
            test_type=TestType.UNIT,
            spec_element=f"{model_name}.{prop.name}",
            arrange=f"model = {model_name}()",
            act=f"model.{prop.name} = valid_value",
            assert_="assert no validation error",
            test_data={"valid_value": self._get_valid_example(prop)},
            markers=["unit", "validation"],
            priority="high"
        ))
        
        if prop.required:
            tests.append(TestCase(
                id=f"TC-{model_name}-{prop.name}-required",
                name=f"test_{prop.name}_required_validation",
                description=f"测试 {prop.name} 必填验证",
                test_type=TestType.UNIT,
                spec_element=f"{model_name}.{prop.name}",
                arrange=f"model = {model_name}()",
                act=f"model.{prop.name} = None",
                assert_="assert validation error for required field",
                markers=["unit", "validation", "negative"],
                priority="high"
            ))
        
        if prop.min_value is not None:
            tests.append(TestCase(
                id=f"TC-{model_name}-{prop.name}-min",
                name=f"test_{prop.name}_min_value",
                description=f"测试 {prop.name} 最小值验证",
                test_type=TestType.UNIT,
                spec_element=f"{model_name}.{prop.name}",
                arrange=f"model = {model_name}()",
                act=f"model.{prop.name} = {prop.min_value - 1}",
                assert_="assert validation error for below minimum",
                markers=["unit", "validation", "edge_case"],
                priority="medium"
            ))
        
        if prop.max_value is not None:
            tests.append(TestCase(
                id=f"TC-{model_name}-{prop.name}-max",
                name=f"test_{prop.name}_max_value",
                description=f"测试 {prop.name} 最大值验证",
                test_type=TestType.UNIT,
                spec_element=f"{model_name}.{prop.name}",
                arrange=f"model = {model_name}()",
                act=f"model.{prop.name} = {prop.max_value + 1}",
                assert_="assert validation error for above maximum",
                markers=["unit", "validation", "edge_case"],
                priority="medium"
            ))
        
        if prop.min_length is not None:
            tests.append(TestCase(
                id=f"TC-{model_name}-{prop.name}-minlen",
                name=f"test_{prop.name}_min_length",
                description=f"测试 {prop.name} 最小长度验证",
                test_type=TestType.UNIT,
                spec_element=f"{model_name}.{prop.name}",
                arrange=f"model = {model_name}()",
                act=f'model.{prop.name} = "x" * {prop.min_length - 1}',
                assert_="assert validation error for below min length",
                markers=["unit", "validation", "edge_case"],
                priority="medium"
            ))
        
        if prop.max_length is not None:
            tests.append(TestCase(
                id=f"TC-{model_name}-{prop.name}-maxlen",
                name=f"test_{prop.name}_max_length",
                description=f"测试 {prop.name} 最大长度验证",
                test_type=TestType.UNIT,
                spec_element=f"{model_name}.{prop.name}",
                arrange=f"model = {model_name}()",
                act=f'model.{prop.name} = "x" * {prop.max_length + 1}',
                assert_="assert validation error for above max length",
                markers=["unit", "validation", "edge_case"],
                priority="medium"
            ))
        
        if prop.pattern:
            tests.append(TestCase(
                id=f"TC-{model_name}-{prop.name}-pattern",
                name=f"test_{prop.name}_pattern_validation",
                description=f"测试 {prop.name} 格式验证",
                test_type=TestType.UNIT,
                spec_element=f"{model_name}.{prop.name}",
                arrange=f"model = {model_name}()",
                act=f'model.{prop.name} = "invalid_format"',
                assert_="assert validation error for pattern mismatch",
                markers=["unit", "validation"],
                priority="medium"
            ))
        
        if prop.enum_values:
            tests.append(TestCase(
                id=f"TC-{model_name}-{prop.name}-enum",
                name=f"test_{prop.name}_enum_validation",
                description=f"测试 {prop.name} 枚举值验证",
                test_type=TestType.UNIT,
                spec_element=f"{model_name}.{prop.name}",
                arrange=f"model = {model_name}()",
                act=f'model.{prop.name} = "invalid_enum_value"',
                assert_="assert validation error for invalid enum",
                markers=["unit", "validation", "negative"],
                priority="medium"
            ))
        
        return tests
    
    def _generate_model_crud_tests(self, model: DataModelDefinition) -> List[TestCase]:
        """生成CRUD测试用例"""
        tests = []
        
        tests.append(TestCase(
            id=f"TC-{model.name}-create",
            name=f"test_{model.name}_create",
            description=f"测试 {model.name} 创建操作",
            test_type=TestType.INTEGRATION,
            spec_element=model.name,
            arrange=f"data = create_valid_{model_name_lower(model.name)}_data()",
            act=f"result = repository.create(data)",
            assert_="assert result is not None and result.id is not None",
            markers=["integration", "crud"],
            priority="high"
        ))
        
        tests.append(TestCase(
            id=f"TC-{model.name}-read",
            name=f"test_{model.name}_read",
            description=f"测试 {model.name} 读取操作",
            test_type=TestType.INTEGRATION,
            spec_element=model.name,
            arrange=f"entity = create_and_save_{model_name_lower(model.name)}()",
            act=f"result = repository.find_by_id(entity.id)",
            assert_="assert result is not None and result.id == entity.id",
            markers=["integration", "crud"],
            priority="high"
        ))
        
        tests.append(TestCase(
            id=f"TC-{model.name}-update",
            name=f"test_{model.name}_update",
            description=f"测试 {model.name} 更新操作",
            test_type=TestType.INTEGRATION,
            spec_element=model.name,
            arrange=f"entity = create_and_save_{model_name_lower(model.name)}()",
            act=f"result = repository.update(entity.id, updated_data)",
            assert_="assert result is not None and updated fields are correct",
            markers=["integration", "crud"],
            priority="high"
        ))
        
        tests.append(TestCase(
            id=f"TC-{model.name}-delete",
            name=f"test_{model.name}_delete",
            description=f"测试 {model.name} 删除操作",
            test_type=TestType.INTEGRATION,
            spec_element=model.name,
            arrange=f"entity = create_and_save_{model_name_lower(model.name)}()",
            act=f"repository.delete(entity.id)",
            assert_="assert entity is deleted",
            markers=["integration", "crud"],
            priority="high"
        ))
        
        return tests
    
    def _generate_model_relationship_tests(self, model: DataModelDefinition) -> List[TestCase]:
        """生成关系测试用例"""
        tests = []
        
        for rel in model.relationships:
            rel_name = rel.get("name", "unknown")
            rel_type = rel.get("type", "association")
            target = rel.get("target", "")
            
            tests.append(TestCase(
                id=f"TC-{model.name}-{rel_name}-relation",
                name=f"test_{model_name_lower(model.name)}_{rel_name}_relationship",
                description=f"测试 {model.name} 与 {target} 的 {rel_name} 关系",
                test_type=TestType.INTEGRATION,
                spec_element=f"{model.name}.{rel_name}",
                arrange=f"entity = create_{model_name_lower(model.name)}_with_{rel_name}()",
                act=f"related = entity.{rel_name}",
                assert_=f"assert related is not None and relationship is valid",
                markers=["integration", "relationship"],
                priority="medium"
            ))
        
        return tests
    
    def generate_from_behavior_rule(self, rule: BehaviorRuleDefinition) -> TestSuite:
        """
        从行为规则生成测试用例骨架
        
        Args:
            rule: 行为规则定义
            
        Returns:
            TestSuite: 生成的测试套件
        """
        test_cases = []
        
        test_cases.append(TestCase(
            id=f"TC-{rule.id}-trigger",
            name=f"test_{rule.name}_trigger",
            description=f"测试规则 {rule.name} 触发条件",
            test_type=TestType.UNIT,
            spec_element=rule.id,
            arrange=self._generate_arrange_for_rule(rule),
            act=self._generate_act_for_rule(rule),
            assert_=self._generate_assert_for_rule(rule),
            test_data=rule.parameters,
            markers=["unit", "business_rule"],
            priority="high"
        ))
        
        test_cases.append(TestCase(
            id=f"TC-{rule.id}-not-trigger",
            name=f"test_{rule.name}_not_triggered",
            description=f"测试规则 {rule.name} 未触发场景",
            test_type=TestType.UNIT,
            spec_element=rule.id,
            arrange=self._generate_arrange_for_rule(rule, trigger=False),
            act=self._generate_act_for_rule(rule),
            assert_="assert rule action is not executed",
            markers=["unit", "business_rule", "negative"],
            priority="medium"
        ))
        
        if rule.else_action:
            test_cases.append(TestCase(
                id=f"TC-{rule.id}-else",
                name=f"test_{rule.name}_else_branch",
                description=f"测试规则 {rule.name} else分支",
                test_type=TestType.UNIT,
                spec_element=rule.id,
                arrange=self._generate_arrange_for_rule(rule, else_branch=True),
                act=self._generate_act_for_rule(rule),
                assert_="assert else action is executed",
                markers=["unit", "business_rule"],
                priority="medium"
            ))
        
        if rule.error_handling:
            test_cases.append(TestCase(
                id=f"TC-{rule.id}-error",
                name=f"test_{rule.name}_error_handling",
                description=f"测试规则 {rule.name} 错误处理",
                test_type=TestType.UNIT,
                spec_element=rule.id,
                arrange=self._generate_arrange_for_rule(rule, error=True),
                act=self._generate_act_for_rule(rule),
                assert_="assert error is handled correctly",
                markers=["unit", "business_rule", "error_handling"],
                priority="medium"
            ))
        
        suite = TestSuite(
            name=f"{rule.name}TestSuite",
            description=f"行为规则 {rule.name} 的测试套件",
            test_cases=test_cases,
            imports=[self.syntax["import"]],
            fixtures={}
        )
        
        self._generated_tests[rule.id] = suite
        return suite
    
    def generate_from_state_machine(self, state_machine: StateMachine) -> TestSuite:
        """
        从状态机生成测试用例骨架
        
        Args:
            state_machine: 状态机定义
            
        Returns:
            TestSuite: 生成的测试套件
        """
        test_cases = []
        
        test_cases.append(TestCase(
            id=f"TC-{state_machine.id}-initial",
            name=f"test_{state_machine.name}_initial_state",
            description=f"测试状态机 {state_machine.name} 初始状态",
            test_type=TestType.UNIT,
            spec_element=state_machine.id,
            arrange=f"sm = {state_machine.name}()",
            act="sm.initialize()",
            assert_=f"assert sm.current_state == '{state_machine.initial_state}'",
            markers=["unit", "state_machine"],
            priority="high"
        ))
        
        for trans in state_machine.transitions:
            test_cases.append(TestCase(
                id=f"TC-{state_machine.id}-{trans.from_state}-{trans.to_state}",
                name=f"test_{state_machine.name}_{trans.from_state}_to_{trans.to_state}",
                description=f"测试状态转换 {trans.from_state} -> {trans.to_state}",
                test_type=TestType.UNIT,
                spec_element=f"{state_machine.id}.{trans.from_state}->{trans.to_state}",
                arrange=f"sm = {state_machine.name}(state='{trans.from_state}')",
                act=f"sm.{trans.trigger}()",
                assert_=f"assert sm.current_state == '{trans.to_state}'",
                markers=["unit", "state_machine"],
                priority="high"
            ))
            
            if trans.guard:
                test_cases.append(TestCase(
                    id=f"TC-{state_machine.id}-{trans.from_state}-{trans.to_state}-guard",
                    name=f"test_{state_machine.name}_{trans.from_state}_to_{trans.to_state}_guard",
                    description=f"测试状态转换守卫条件 {trans.from_state} -> {trans.to_state}",
                    test_type=TestType.UNIT,
                    spec_element=f"{state_machine.id}.{trans.from_state}->{trans.to_state}",
                    arrange=f"sm = {state_machine.name}(state='{trans.from_state}')",
                    act=f"sm.{trans.trigger}()",
                    assert_="assert transition is blocked by guard",
                    markers=["unit", "state_machine", "negative"],
                    priority="medium"
                ))
        
        for final_state in state_machine.final_states:
            test_cases.append(TestCase(
                id=f"TC-{state_machine.id}-{final_state}-final",
                name=f"test_{state_machine.name}_{final_state}_final",
                description=f"测试最终状态 {final_state}",
                test_type=TestType.UNIT,
                spec_element=f"{state_machine.id}.{final_state}",
                arrange=f"sm = {state_machine.name}(state='{final_state}')",
                act="sm.is_final()",
                assert_="assert sm.is_final() == True",
                markers=["unit", "state_machine"],
                priority="medium"
            ))
        
        suite = TestSuite(
            name=f"{state_machine.name}TestSuite",
            description=f"状态机 {state_machine.name} 的测试套件",
            test_cases=test_cases,
            imports=[self.syntax["import"]],
            fixtures={}
        )
        
        self._generated_tests[state_machine.id] = suite
        return suite
    
    def generate_all_tests(self, spec: SDDSpecification) -> Dict[str, TestSuite]:
        """
        从完整规范生成所有测试用例
        
        Args:
            spec: SDD规范
            
        Returns:
            Dict[str, TestSuite]: 测试套件字典
        """
        suites = {}
        
        syntax_parser = EnhancedSpecSyntaxParser()
        
        for interface_data in spec.spec.get("interfaces", []):
            interface = syntax_parser.parse_interface(interface_data)
            suites[f"interface_{interface.name}"] = self.generate_from_interface(interface)
        
        for model_data in spec.spec.get("dataModels", spec.spec.get("data_models", [])):
            model = syntax_parser.parse_data_model(model_data)
            suites[f"model_{model.name}"] = self.generate_from_data_model(model)
        
        for rule_data in spec.spec.get("behaviorRules", spec.spec.get("behavior_rules", [])):
            rule = syntax_parser.parse_behavior_rule(rule_data)
            suites[f"rule_{rule.name}"] = self.generate_from_behavior_rule(rule)
        
        for sm in spec.state_machines:
            suites[f"statemachine_{sm.name}"] = self.generate_from_state_machine(sm)
        
        return suites
    
    def export_tests(self, suite: TestSuite, output_path: str) -> str:
        """
        导出测试套件到文件
        
        Args:
            suite: 测试套件
            output_path: 输出路径
            
        Returns:
            str: 生成的测试代码
        """
        lines = []
        
        for imp in suite.imports:
            lines.append(imp)
        lines.append("")
        
        if suite.conftest:
            lines.append(suite.conftest)
            lines.append("")
        
        for name, fixture_code in suite.fixtures.items():
            lines.append(f"# Fixture: {name}")
            lines.append(fixture_code)
            lines.append("")
        
        lines.append(f"class Test{suite.name.replace('TestSuite', '')}:")
        lines.append(f'    """{suite.description}"""')
        lines.append("")
        
        if suite.setup:
            lines.append("    def setUp(self):")
            for line in suite.setup.split("\n"):
                lines.append(f"        {line}")
            lines.append("")
        
        for test_case in suite.test_cases:
            lines.extend(self._export_test_case(test_case))
            lines.append("")
        
        if suite.teardown:
            lines.append("    def tearDown(self):")
            for line in suite.teardown.split("\n"):
                lines.append(f"        {line}")
            lines.append("")
        
        content = "\n".join(lines)
        
        if output_path:
            Path(output_path).write_text(content, encoding="utf-8")
        
        return content
    
    def _export_test_case(self, test_case: TestCase) -> List[str]:
        """导出单个测试用例"""
        lines = []
        
        markers = ", ".join(test_case.markers) if test_case.markers else "unit"
        lines.append(f"    @{self.syntax['test_decorator'].format(marker=markers.split(',')[0])}")
        
        func_def = self.syntax['test_func'].format(name=test_case.name)
        lines.append(f"    {func_def}")
        lines.append(f'        """{test_case.description}"""')
        lines.append("")
        
        if test_case.test_data:
            lines.append("        # Test data")
            for key, value in test_case.test_data.items():
                lines.append(f"        {key} = {repr(value)}")
            lines.append("")
        
        if test_case.arrange:
            lines.append("        # Arrange")
            for line in test_case.arrange.split("\n"):
                lines.append(f"        {line}")
            lines.append("")
        
        if test_case.act:
            lines.append("        # Act")
            for line in test_case.act.split("\n"):
                lines.append(f"        {line}")
            lines.append("")
        
        if test_case.assert_:
            lines.append("        # Assert")
            assertion = self.syntax['assertion'].format(condition=test_case.assert_)
            lines.append(f"        {assertion}")
        
        return lines
    
    def _generate_arrange_for_method(self, method: MethodDefinition, exclude_param: str = None) -> str:
        """生成方法的arrange代码"""
        lines = ["instance = create_mock_instance()"]
        
        for param in method.parameters:
            if exclude_param and param.get("name") == exclude_param:
                continue
            param_name = param.get("name", "param")
            param_type = param.get("type", "any")
            lines.append(f"{param_name} = create_{param_type}_value()")
        
        return "\n".join(lines)
    
    def _generate_arrange_for_exception(self, method: MethodDefinition, exception: str) -> str:
        """生成异常测试的arrange代码"""
        return f"instance = create_mock_instance()\n# Setup to trigger {exception}"
    
    def _generate_arrange_for_rule(self, rule: BehaviorRuleDefinition, trigger: bool = True, else_branch: bool = False, error: bool = False) -> str:
        """生成规则的arrange代码"""
        lines = ["context = create_test_context()"]
        
        if not trigger:
            lines.append("# Setup condition to NOT trigger rule")
        elif else_branch:
            lines.append("# Setup condition to trigger else branch")
        elif error:
            lines.append("# Setup to cause error during rule execution")
        
        return "\n".join(lines)
    
    def _generate_act_for_rule(self, rule: BehaviorRuleDefinition) -> str:
        """生成规则的act代码"""
        if rule.trigger:
            return f"engine.execute_rule('{rule.id}', context)"
        return f"engine.evaluate_condition('{rule.condition}', context)"
    
    def _generate_assert_for_rule(self, rule: BehaviorRuleDefinition) -> str:
        """生成规则的assert代码"""
        return f"assert rule '{rule.name}' executed correctly"
    
    def _generate_assert_for_method(self, method: MethodDefinition) -> str:
        """生成方法的assert代码"""
        if method.return_type and method.return_type != "void":
            return f"assert result is not None and isinstance(result, {method.return_type})"
        return "assert result is None or result is True"
    
    def _generate_test_data_for_method(self, method: MethodDefinition) -> Dict[str, Any]:
        """生成方法的测试数据"""
        data = {}
        for param in method.parameters:
            param_name = param.get("name", "param")
            param_type = param.get("type", "string")
            data[param_name] = self._get_default_value_for_type(param_type)
        return data
    
    def _get_param_names(self, parameters: List[Dict[str, Any]], exclude: str = None) -> str:
        """获取参数名列表"""
        names = [p.get("name", "param") for p in parameters if p.get("name") != exclude]
        return ", ".join(names)
    
    def _get_valid_example(self, prop: DataModelProperty) -> Any:
        """获取属性的有效示例值"""
        if prop.example:
            return prop.example
        if prop.enum_values:
            return prop.enum_values[0]
        if prop.default is not None:
            return prop.default
        
        type_examples = {
            "string": "test_string",
            "integer": 1,
            "int": 1,
            "float": 1.0,
            "boolean": True,
            "bool": True,
            "date": "2024-01-01",
            "datetime": "2024-01-01T00:00:00Z",
            "email": "test@example.com",
            "uuid": "00000000-0000-0000-0000-000000000000"
        }
        
        return type_examples.get(prop.type.lower(), "test_value")
    
    def _get_default_value_for_type(self, type_name: str) -> Any:
        """获取类型的默认值"""
        defaults = {
            "string": "",
            "integer": 0,
            "int": 0,
            "float": 0.0,
            "boolean": False,
            "bool": False,
            "list": [],
            "dict": {},
            "array": []
        }
        return defaults.get(type_name.lower(), None)
    
    def _generate_interface_fixtures(self, interface: InterfaceDefinition) -> Dict[str, str]:
        """生成接口的fixture代码"""
        fixtures = {}
        
        fixtures["mock_instance"] = """@pytest.fixture
def mock_instance():
    \"\"\"创建接口的模拟实例\"\"\"
    return Mock(spec={interface_name})""".format(interface_name=interface.name)
        
        return fixtures
    
    def _generate_model_fixtures(self, model: DataModelDefinition) -> Dict[str, str]:
        """生成模型的fixture代码"""
        fixtures = {}
        
        props_init = []
        for prop in model.properties:
            if prop.required:
                props_init.append(f"        {prop.name}={repr(self._get_valid_example(prop))}")
        
        fixtures[f"valid_{model_name_lower(model.name)}"] = f"""@pytest.fixture
def valid_{model_name_lower(model.name)}():
    \"\"\"创建有效的{model.name}实例\"\"\"
    return {model.name}(
{chr(10).join(props_init)}
    )"""
        
        return fixtures


def model_name_lower(name: str) -> str:
    """将模型名转换为小写下划线格式"""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            result.append('_')
        result.append(char.lower())
    return ''.join(result)


# ============================================================================
# 代码骨架生成器
# ============================================================================

class CodeSkeletonGenerator:
    """
    代码骨架生成器
    
    根据规范自动生成代码骨架，支持：
    - Python类/接口
    - TypeScript类/接口
    - Java类/接口
    - Go结构体/接口
    - REST API端点
    - 数据模型
    """
    
    LANGUAGE_SYNTAX = {
        "python": {
            "class_def": "class {name}{extends}{implements}:",
            "interface_def": "class {name}(Protocol{extends}):",
            "method_def": "    def {name}({params}) -> {return_type}:",
            "property_def": "    {name}: {type}",
            "constructor": "    def __init__(self{params}):",
            "file_ext": ".py",
            "indent": "    ",
            "comment": "#",
            "docstring": '"""{content}"""',
            "type_hint": ": {type}",
            "return_arrow": " -> {type}",
            "import": "from {module} import {name}",
            "decorator": "@{name}"
        },
        "typescript": {
            "class_def": "export class {name}{extends}{implements} {{",
            "interface_def": "export interface {name}{extends} {{",
            "method_def": "  {async}{name}({params}): {return_type} {{",
            "property_def": "  {readonly}{name}: {type};",
            "constructor": "  constructor({params}) {{",
            "file_ext": ".ts",
            "indent": "  ",
            "comment": "//",
            "docstring": "/**\n   * {content}\n   */",
            "type_hint": ": {type}",
            "return_arrow": ": {type}",
            "import": "import {{ {name} }} from '{module}';",
            "decorator": "@{name}"
        },
        "java": {
            "class_def": "public class {name}{extends}{implements} {{",
            "interface_def": "public interface {name}{extends} {{",
            "method_def": "  public {return_type} {name}({params}) {{",
            "property_def": "  private {type} {name};",
            "constructor": "  public {name}({params}) {{",
            "file_ext": ".java",
            "indent": "  ",
            "comment": "//",
            "docstring": "/**\n   * {content}\n   */",
            "type_hint": " {type} ",
            "return_arrow": " {type} ",
            "import": "import {module}.{name};",
            "decorator": "@{name}"
        },
        "go": {
            "class_def": "type {name} struct {{",
            "interface_def": "type {name} interface {{",
            "method_def": "func ({receiver} {name}) {method}({params}) {return_type} {{",
            "property_def": "  {name} {type}",
            "constructor": "func New{name}({params}) *{name} {{",
            "file_ext": ".go",
            "indent": "\t",
            "comment": "//",
            "docstring": "// {content}",
            "type_hint": " {type}",
            "return_arrow": " {type}",
            "import": "import \"{module}\"",
            "decorator": ""
        }
    }
    
    def __init__(self, language: str = "python"):
        self.language = language
        self.syntax = self.LANGUAGE_SYNTAX.get(language, self.LANGUAGE_SYNTAX["python"])
        self._generated_files: Dict[str, str] = {}
    
    def generate_interface(self, interface: InterfaceDefinition) -> str:
        """
        生成接口代码骨架
        
        Args:
            interface: 接口定义
            
        Returns:
            str: 生成的代码
        """
        lines = []
        
        lines.append(f"{self.syntax['comment']} 自动生成的接口代码 - {interface.name}")
        lines.append(f"{self.syntax['comment']} 生成时间: {datetime.now().isoformat()}")
        lines.append("")
        
        if interface.description:
            lines.append(self.syntax['docstring'].format(content=interface.description))
            lines.append("")
        
        extends_str = ""
        if interface.extends:
            if self.language == "python":
                extends_str = f", {', '.join(interface.extends)}"
            elif self.language == "typescript":
                extends_str = f" extends {', '.join(interface.extends)}"
            elif self.language == "java":
                extends_str = f" extends {', '.join(interface.extends)}"
        
        implements_str = ""
        if interface.implements:
            if self.language == "java":
                implements_str = f" implements {', '.join(interface.implements)}"
            elif self.language == "typescript":
                implements_str = f" implements {', '.join(interface.implements)}"
        
        class_def = self.syntax['interface_def'].format(
            name=interface.name,
            extends=extends_str,
            implements=implements_str
        )
        lines.append(class_def)
        
        for prop in interface.properties:
            lines.extend(self._generate_property(prop))
        
        for method in interface.methods:
            lines.extend(self._generate_method(method))
            lines.append("")
        
        if self.language in ["typescript", "java", "go"]:
            lines.append("}")
        
        code = "\n".join(lines)
        self._generated_files[f"{interface.name}{self.syntax['file_ext']}"] = code
        return code
    
    def generate_data_model(self, model: DataModelDefinition) -> str:
        """
        生成数据模型代码骨架
        
        Args:
            model: 数据模型定义
            
        Returns:
            str: 生成的代码
        """
        lines = []
        
        lines.append(f"{self.syntax['comment']} 自动生成的数据模型代码 - {model.name}")
        lines.append(f"{self.syntax['comment']} 生成时间: {datetime.now().isoformat()}")
        lines.append("")
        
        imports = self._generate_model_imports(model)
        if imports:
            lines.extend(imports)
            lines.append("")
        
        if model.description:
            lines.append(self.syntax['docstring'].format(content=model.description))
            lines.append("")
        
        extends_str = ""
        if model.extends:
            if self.language == "python":
                extends_str = f"({model.extends})"
            elif self.language in ["typescript", "java"]:
                extends_str = f" extends {model.extends}"
        
        class_def = self.syntax['class_def'].format(
            name=model.name,
            extends=extends_str,
            implements=""
        )
        lines.append(class_def)
        
        lines.extend(self._generate_model_constructor(model))
        lines.append("")
        
        for prop in model.properties:
            lines.extend(self._generate_model_property(prop))
        
        lines.append("")
        lines.extend(self._generate_model_methods(model))
        
        if self.language in ["typescript", "java", "go"]:
            lines.append("}")
        
        code = "\n".join(lines)
        self._generated_files[f"{model.name}{self.syntax['file_ext']}"] = code
        return code
    
    def generate_api_endpoint(self, endpoint: SpecEndpoint) -> str:
        """
        生成API端点代码骨架
        
        Args:
            endpoint: API端点定义
            
        Returns:
            str: 生成的代码
        """
        lines = []
        
        lines.append(f"{self.syntax['comment']} API端点: {endpoint.method} {endpoint.path}")
        lines.append(f"{self.syntax['comment']} {endpoint.description}")
        lines.append("")
        
        handler_name = self._get_handler_name(endpoint)
        
        if self.language == "python":
            lines.extend(self._generate_flask_endpoint(endpoint, handler_name))
        elif self.language == "typescript":
            lines.extend(self._generate_express_endpoint(endpoint, handler_name))
        elif self.language == "java":
            lines.extend(self._generate_spring_endpoint(endpoint, handler_name))
        
        code = "\n".join(lines)
        self._generated_files[f"{handler_name}{self.syntax['file_ext']}"] = code
        return code
    
    def generate_behavior_rule(self, rule: BehaviorRuleDefinition) -> str:
        """
        生成行为规则代码骨架
        
        Args:
            rule: 行为规则定义
            
        Returns:
            str: 生成的代码
        """
        lines = []
        
        lines.append(f"{self.syntax['comment']} 行为规则: {rule.name}")
        lines.append(f"{self.syntax['comment']} {rule.description}")
        lines.append("")
        
        if self.language == "python":
            lines.extend(self._generate_python_rule(rule))
        elif self.language == "typescript":
            lines.extend(self._generate_typescript_rule(rule))
        
        code = "\n".join(lines)
        self._generated_files[f"rule_{rule.name}{self.syntax['file_ext']}"] = code
        return code
    
    def generate_state_machine(self, state_machine: StateMachine) -> str:
        """
        生成状态机代码骨架
        
        Args:
            state_machine: 状态机定义
            
        Returns:
            str: 生成的代码
        """
        lines = []
        
        lines.append(f"{self.syntax['comment']} 状态机: {state_machine.name}")
        lines.append(f"{self.syntax['comment']} {state_machine.description}")
        lines.append("")
        
        if self.language == "python":
            lines.extend(self._generate_python_state_machine(state_machine))
        elif self.language == "typescript":
            lines.extend(self._generate_typescript_state_machine(state_machine))
        
        code = "\n".join(lines)
        self._generated_files[f"{state_machine.name}{self.syntax['file_ext']}"] = code
        return code
    
    def generate_all(self, spec: SDDSpecification) -> Dict[str, str]:
        """
        从完整规范生成所有代码骨架
        
        Args:
            spec: SDD规范
            
        Returns:
            Dict[str, str]: 文件名到代码的映射
        """
        files = {}
        
        syntax_parser = EnhancedSpecSyntaxParser()
        
        for interface_data in spec.spec.get("interfaces", []):
            interface = syntax_parser.parse_interface(interface_data)
            filename = f"{interface.name}{self.syntax['file_ext']}"
            files[filename] = self.generate_interface(interface)
        
        for model_data in spec.spec.get("dataModels", spec.spec.get("data_models", [])):
            model = syntax_parser.parse_data_model(model_data)
            filename = f"{model.name}{self.syntax['file_ext']}"
            files[filename] = self.generate_data_model(model)
        
        for endpoint in spec.endpoints:
            filename = f"endpoint_{endpoint.name}{self.syntax['file_ext']}"
            files[filename] = self.generate_api_endpoint(endpoint)
        
        for rule_data in spec.spec.get("behaviorRules", spec.spec.get("behavior_rules", [])):
            rule = syntax_parser.parse_behavior_rule(rule_data)
            filename = f"rule_{rule.name}{self.syntax['file_ext']}"
            files[filename] = self.generate_behavior_rule(rule)
        
        for sm in spec.state_machines:
            filename = f"{sm.name}{self.syntax['file_ext']}"
            files[filename] = self.generate_state_machine(sm)
        
        self._generated_files.update(files)
        return files
    
    def export_to_directory(self, output_dir: str) -> List[str]:
        """
        导出生成的代码到目录
        
        Args:
            output_dir: 输出目录
            
        Returns:
            List[str]: 生成的文件路径列表
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = []
        for filename, content in self._generated_files.items():
            file_path = output_path / filename
            file_path.write_text(content, encoding="utf-8")
            exported_files.append(str(file_path))
        
        return exported_files
    
    def _generate_method(self, method: MethodDefinition) -> List[str]:
        """生成方法代码"""
        lines = []
        
        indent = self.syntax['indent']
        
        if method.description:
            lines.append(f"{indent}{self.syntax['docstring'].format(content=method.description)}")
        
        params_str = self._format_parameters(method.parameters)
        return_type = method.return_type or "void"
        
        if self.language == "python":
            return_type = return_type if return_type != "void" else "None"
            method_def = f"{indent}def {method.name}(self{params_str}) -> {return_type}:"
            lines.append(method_def)
            lines.append(f"{indent}{indent}pass  # TODO: 实现方法逻辑")
        
        elif self.language == "typescript":
            async_kw = "async " if method.is_async else ""
            return_type = return_type if return_type != "void" else "void"
            method_def = f"{indent}{async_kw}{method.name}({params_str}): {return_type} {{"
            lines.append(method_def)
            lines.append(f"{indent}{indent}// TODO: 实现方法逻辑")
            lines.append(f"{indent}}}")
        
        elif self.language == "java":
            return_type = return_type if return_type != "void" else "void"
            method_def = f"{indent}public {return_type} {method.name}({params_str}) {{"
            lines.append(method_def)
            lines.append(f"{indent}{indent}// TODO: 实现方法逻辑")
            lines.append(f"{indent}}}")
        
        return lines
    
    def _generate_property(self, prop: Dict[str, Any]) -> List[str]:
        """生成属性代码"""
        lines = []
        indent = self.syntax['indent']
        
        name = prop.get("name", "property")
        prop_type = prop.get("type", "any")
        description = prop.get("description", "")
        
        if self.language == "python":
            lines.append(f"{indent}{name}: {prop_type}")
            if description:
                lines.append(f'{indent}"""{description}"""')
        
        elif self.language == "typescript":
            readonly = "readonly " if prop.get("readOnly") else ""
            lines.append(f"{indent}{readonly}{name}: {prop_type};")
        
        elif self.language == "java":
            lines.append(f"{indent}private {prop_type} {name};")
        
        return lines
    
    def _format_parameters(self, parameters: List[Dict[str, Any]]) -> str:
        """格式化参数列表"""
        if not parameters:
            return ""
        
        params = []
        for param in parameters:
            name = param.get("name", "param")
            param_type = param.get("type", "any")
            optional = param.get("optional", False)
            
            if self.language == "python":
                default = " = None" if optional else ""
                params.append(f", {name}: {param_type}{default}")
            elif self.language == "typescript":
                optional_marker = "?" if optional else ""
                params.append(f"{name}{optional_marker}: {param_type}")
            elif self.language == "java":
                params.append(f"{param_type} {name}")
        
        if self.language == "python":
            return "".join(params)
        else:
            return ", ".join(params)
    
    def _generate_model_imports(self, model: DataModelDefinition) -> List[str]:
        """生成模型导入语句"""
        imports = []
        
        if self.language == "python":
            imports.append("from dataclasses import dataclass")
            imports.append("from typing import Optional, List, Dict, Any")
            if model.extends:
                imports.append(f"from .{model.extends.lower()} import {model.extends}")
        
        elif self.language == "typescript":
            if model.extends:
                imports.append(f"import {{ {model.extends} }} from './{model.extends}';")
        
        elif self.language == "java":
            imports.append("import java.util.*;")
            if model.extends:
                imports.append(f"import com.example.models.{model.extends};")
        
        return imports
    
    def _generate_model_constructor(self, model: DataModelDefinition) -> List[str]:
        """生成模型构造函数"""
        lines = []
        indent = self.syntax['indent']
        
        if self.language == "python":
            lines.append(f"{indent}def __init__(self):")
            for prop in model.properties:
                lines.append(f"{indent}{indent}self.{prop.name}: {prop.type} = {repr(prop.default) if prop.default is not None else 'None'}")
        
        elif self.language == "typescript":
            params = []
            for prop in model.properties:
                optional = "?" if not prop.required else ""
                params.append(f"{prop.name}{optional}: {prop.type}")
            
            lines.append(f"{indent}constructor({', '.join(params)}) {{")
            for prop in model.properties:
                lines.append(f"{indent}{indent}this.{prop.name} = {prop.name};")
            lines.append(f"{indent}}}")
        
        elif self.language == "java":
            params = []
            for prop in model.properties:
                params.append(f"{prop.type} {prop.name}")
            
            lines.append(f"{indent}public {model.name}({', '.join(params)}) {{")
            for prop in model.properties:
                lines.append(f"{indent}{indent}this.{prop.name} = {prop.name};")
            lines.append(f"{indent}}}")
        
        return lines
    
    def _generate_model_property(self, prop: DataModelProperty) -> List[str]:
        """生成模型属性"""
        lines = []
        indent = self.syntax['indent']
        
        if self.language == "python":
            lines.append(f"{indent}{prop.name}: {prop.type}")
        
        elif self.language == "typescript":
            readonly = "readonly " if prop.read_only else ""
            lines.append(f"{indent}{readonly}{prop.name}: {prop.type};")
        
        elif self.language == "java":
            access = "private" if not prop.read_only else "private final"
            lines.append(f"{indent}{access} {prop.type} {prop.name};")
        
        return lines
    
    def _generate_model_methods(self, model: DataModelDefinition) -> List[str]:
        """生成模型方法"""
        lines = []
        indent = self.syntax['indent']
        
        if self.language == "python":
            lines.append(f"{indent}def to_dict(self) -> Dict[str, Any]:")
            lines.append(f"{indent}{indent}\"\"\"转换为字典\"\"\"")
            lines.append(f"{indent}{indent}return {{}}  # TODO: 实现")
            lines.append("")
            lines.append(f"{indent}@classmethod")
            lines.append(f"{indent}def from_dict(cls, data: Dict[str, Any]) -> '{model.name}':")
            lines.append(f"{indent}{indent}\"\"\"从字典创建实例\"\"\"")
            lines.append(f"{indent}{indent}return cls()  # TODO: 实现")
        
        elif self.language == "typescript":
            lines.append(f"{indent}toJSON(): any {{")
            lines.append(f"{indent}{indent}return {{}};  // TODO: 实现")
            lines.append(f"{indent}}}")
            lines.append("")
            lines.append(f"{indent}static fromJSON(data: any): {model.name} {{")
            lines.append(f"{indent}{indent}return new {model.name}();  // TODO: 实现")
            lines.append(f"{indent}}}")
        
        return lines
    
    def _get_handler_name(self, endpoint: SpecEndpoint) -> str:
        """获取处理器名称"""
        path_parts = endpoint.path.strip("/").split("/")
        name_parts = [p.replace("{", "").replace("}", "").replace("-", "_") for p in path_parts if p]
        return f"{endpoint.method.lower()}_{'_'.join(name_parts)}"
    
    def _generate_flask_endpoint(self, endpoint: SpecEndpoint, handler_name: str) -> List[str]:
        """生成Flask端点代码"""
        lines = []
        
        lines.append(f"@app.route('{endpoint.path}', methods=['{endpoint.method}'])")
        lines.append(f"def {handler_name}():")
        lines.append(f'    """{endpoint.description}"""')
        lines.append("")
        
        if endpoint.parameters:
            lines.append("    # 获取请求参数")
            for param in endpoint.parameters:
                param_name = param.get("name", "param")
                lines.append(f"    {param_name} = request.args.get('{param_name}')")
            lines.append("")
        
        if endpoint.request_body:
            lines.append("    # 获取请求体")
            lines.append("    data = request.get_json()")
            lines.append("")
        
        lines.append("    # TODO: 实现业务逻辑")
        lines.append("")
        
        if endpoint.response:
            lines.append("    return jsonify({})")
        else:
            lines.append("    return '', 204")
        
        return lines
    
    def _generate_express_endpoint(self, endpoint: SpecEndpoint, handler_name: str) -> List[str]:
        """生成Express端点代码"""
        lines = []
        
        lines.append(f"router.{endpoint.method.lower()}('{endpoint.path}', async (req, res) => {{")
        lines.append(f"  // {endpoint.description}")
        lines.append("")
        
        if endpoint.parameters:
            lines.append("  // 获取请求参数")
            for param in endpoint.parameters:
                param_name = param.get("name", "param")
                lines.append(f"  const {param_name} = req.query.{param_name};")
            lines.append("")
        
        if endpoint.request_body:
            lines.append("  // 获取请求体")
            lines.append("  const data = req.body;")
            lines.append("")
        
        lines.append("  // TODO: 实现业务逻辑")
        lines.append("")
        lines.append("  res.json({});")
        lines.append("});")
        
        return lines
    
    def _generate_spring_endpoint(self, endpoint: SpecEndpoint, handler_name: str) -> List[str]:
        """生成Spring端点代码"""
        lines = []
        
        mapping = {
            "GET": "GetMapping",
            "POST": "PostMapping",
            "PUT": "PutMapping",
            "DELETE": "DeleteMapping",
            "PATCH": "PatchMapping"
        }
        
        annotation = mapping.get(endpoint.method.upper(), "RequestMapping")
        lines.append(f"@{annotation}(\"{endpoint.path}\")")
        lines.append(f"public ResponseEntity<?> {handler_name}() {{")
        lines.append(f"    // {endpoint.description}")
        lines.append("")
        lines.append("    // TODO: 实现业务逻辑")
        lines.append("")
        lines.append("    return ResponseEntity.ok().build();")
        lines.append("}")
        
        return lines
    
    def _generate_python_rule(self, rule: BehaviorRuleDefinition) -> List[str]:
        """生成Python规则代码"""
        lines = []
        
        lines.append(f"def {rule.name.lower().replace(' ', '_')}(context: Dict[str, Any]) -> Any:")
        lines.append(f'    """{rule.description}"""')
        lines.append("")
        lines.append(f"    # 条件: {rule.condition}")
        lines.append(f"    if {self._convert_condition_to_python(rule.condition)}:")
        lines.append(f"        # 动作: {rule.action}")
        lines.append(f"        pass  # TODO: 实现 {rule.action}")
        
        if rule.else_action:
            lines.append(f"    else:")
            lines.append(f"        # 否则动作: {rule.else_action}")
            lines.append(f"        pass  # TODO: 实现 {rule.else_action}")
        
        return lines
    
    def _generate_typescript_rule(self, rule: BehaviorRuleDefinition) -> List[str]:
        """生成TypeScript规则代码"""
        lines = []
        
        function_name = rule.name.lower().replace(' ', '_')
        lines.append(f"export function {function_name}(context: any): any {{")
        lines.append(f"  // {rule.description}")
        lines.append("")
        lines.append(f"  // 条件: {rule.condition}")
        lines.append(f"  if ({self._convert_condition_to_typescript(rule.condition)}) {{")
        lines.append(f"    // 动作: {rule.action}")
        lines.append(f"    // TODO: 实现 {rule.action}")
        lines.append(f"  }}")
        
        if rule.else_action:
            lines.append(f"  else {{")
            lines.append(f"    // 否则动作: {rule.else_action}")
            lines.append(f"    // TODO: 实现 {rule.else_action}")
            lines.append(f"  }}")
        
        lines.append("}")
        
        return lines
    
    def _convert_condition_to_python(self, condition: str) -> str:
        """将条件转换为Python代码"""
        condition = condition.replace("==", "==")
        condition = condition.replace("!=", "!=")
        condition = condition.replace(" and ", " and ")
        condition = condition.replace(" or ", " or ")
        condition = condition.replace(" not ", " not ")
        return condition or "True"
    
    def _convert_condition_to_typescript(self, condition: str) -> str:
        """将条件转换为TypeScript代码"""
        condition = condition.replace(" and ", " && ")
        condition = condition.replace(" or ", " || ")
        condition = condition.replace(" not ", " !")
        return condition or "true"
    
    def _generate_python_state_machine(self, sm: StateMachine) -> List[str]:
        """生成Python状态机代码"""
        lines = []
        
        lines.append(f"class {sm.name}:")
        lines.append(f'    """{sm.description}"""')
        lines.append("")
        
        lines.append("    # 状态定义")
        for state in sm.states:
            lines.append(f"    {state.name.upper()} = '{state.name}'")
        lines.append("")
        
        lines.append(f"    def __init__(self):")
        lines.append(f"        self._state = '{sm.initial_state}'")
        lines.append("")
        
        lines.append("    @property")
        lines.append("    def current_state(self) -> str:")
        lines.append("        return self._state")
        lines.append("")
        
        for trans in sm.transitions:
            lines.append(f"    def {trans.trigger.lower()}(self):")
            lines.append(f'        """转换: {trans.from_state} -> {trans.to_state}"""')
            lines.append(f"        if self._state == '{trans.from_state}':")
            if trans.guard:
                lines.append(f"            if {trans.guard}:")
                lines.append(f"                self._state = '{trans.to_state}'")
            else:
                lines.append(f"            self._state = '{trans.to_state}'")
            lines.append("")
        
        return lines
    
    def _generate_typescript_state_machine(self, sm: StateMachine) -> List[str]:
        """生成TypeScript状态机代码"""
        lines = []
        
        lines.append(f"export class {sm.name} {{")
        lines.append(f"  // {sm.description}")
        lines.append("")
        
        lines.append("  // 状态定义")
        for state in sm.states:
            lines.append(f"  static readonly {state.name.toUpperCase()} = '{state.name}';")
        lines.append("")
        
        lines.append(f"  private _state: string = '{sm.initial_state}';")
        lines.append("")
        lines.append("  get currentState(): string {")
        lines.append("    return this._state;")
        lines.append("  }")
        lines.append("")
        
        for trans in sm.transitions:
            lines.append(f"  {trans.trigger.toLowerCase()}(): void {{")
            lines.append(f"    // 转换: {trans.from_state} -> {trans.to_state}")
            lines.append(f"    if (this._state === '{trans.from_state}') {{")
            if trans.guard:
                lines.append(f"      if ({trans.guard}) {{")
                lines.append(f"        this._state = '{trans.to_state}';")
                lines.append("      }")
            else:
                lines.append(f"      this._state = '{trans.to_state}';")
            lines.append("    }")
            lines.append("  }")
            lines.append("")
        
        lines.append("}")
        
        return lines


# ============================================================================
# 增强的规范完整性验证器
# ============================================================================

class EnhancedSpecCompletenessValidator(SpecCompletenessValidator):
    """
    增强的规范完整性验证器
    
    扩展基础验证器，添加更多验证维度：
    - 接口完整性验证
    - 数据模型完整性验证
    - 行为规则完整性验证
    - API端点完整性验证
    - 安全性验证
    - 性能约束验证
    """
    
    def __init__(self):
        super().__init__()
        self.syntax_parser = EnhancedSpecSyntaxParser()
    
    def validate_interface(self, interface: InterfaceDefinition) -> ValidationResult:
        """
        验证接口完整性
        
        Args:
            interface: 接口定义
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)
        
        if not interface.name:
            result.add_error("interface.name", "接口名称不能为空")
        
        if not interface.methods and not interface.properties:
            result.add_warning(
                "interface.members",
                f"接口 {interface.name} 没有定义任何方法或属性",
                "建议至少定义一个成员"
            )
        
        for method in interface.methods:
            self._validate_method(method, interface.name, result)
        
        for prop in interface.properties:
            self._validate_property(prop, interface.name, result)
        
        for ext in interface.extends:
            if ext not in self.syntax_parser._interface_registry:
                result.add_warning(
                    f"interface.extends.{ext}",
                    f"接口 {interface.name} 继承的接口 {ext} 未定义"
                )
        
        return result
    
    def _validate_method(self, method: MethodDefinition, interface_name: str, result: ValidationResult):
        """验证方法定义"""
        method_path = f"interface.{interface_name}.{method.name}"
        
        if not method.name:
            result.add_error(f"{method_path}.name", "方法名称不能为空")
        
        for param in method.parameters:
            if not param.get("name"):
                result.add_error(f"{method_path}.parameters", "参数名称不能为空")
        
        if method.deprecated and not method.deprecation_message:
            result.add_warning(
                f"{method_path}.deprecated",
                f"方法 {method.name} 已废弃但缺少废弃说明",
                "添加 deprecationMessage 说明替代方案"
            )
    
    def _validate_property(self, prop: Dict[str, Any], interface_name: str, result: ValidationResult):
        """验证属性定义"""
        prop_path = f"interface.{interface_name}.{prop.get('name', 'unknown')}"
        
        if not prop.get("name"):
            result.add_error(f"{prop_path}.name", "属性名称不能为空")
        
        if not prop.get("type"):
            result.add_warning(f"{prop_path}.type", "属性缺少类型定义")
    
    def validate_data_model(self, model: DataModelDefinition) -> ValidationResult:
        """
        验证数据模型完整性
        
        Args:
            model: 数据模型定义
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)
        
        if not model.name:
            result.add_error("model.name", "模型名称不能为空")
        
        if not model.properties:
            result.add_warning(
                "model.properties",
                f"模型 {model.name} 没有定义任何属性",
                "建议至少定义一个属性"
            )
        
        for prop in model.properties:
            self._validate_model_property(prop, model.name, result)
        
        if model.extends and model.extends not in self.syntax_parser._model_registry:
            result.add_warning(
                f"model.extends.{model.extends}",
                f"模型 {model.name} 继承的模型 {model.extends} 未定义"
            )
        
        for rel in model.relationships:
            self._validate_relationship(rel, model.name, result)
        
        for idx in model.indexes:
            self._validate_index(idx, model.name, result)
        
        return result
    
    def _validate_model_property(self, prop: DataModelProperty, model_name: str, result: ValidationResult):
        """验证模型属性"""
        prop_path = f"model.{model_name}.{prop.name}"
        
        if not prop.name:
            result.add_error(f"{prop_path}.name", "属性名称不能为空")
        
        if not prop.type:
            result.add_warning(f"{prop_path}.type", "属性缺少类型定义")
        
        if prop.min_value is not None and prop.max_value is not None:
            if prop.min_value > prop.max_value:
                result.add_error(
                    f"{prop_path}.range",
                    f"属性 {prop.name} 的最小值大于最大值"
                )
        
        if prop.min_length is not None and prop.max_length is not None:
            if prop.min_length > prop.max_length:
                result.add_error(
                    f"{prop_path}.length",
                    f"属性 {prop.name} 的最小长度大于最大长度"
                )
        
        if prop.pattern:
            try:
                re.compile(prop.pattern)
            except re.error as e:
                result.add_error(
                    f"{prop_path}.pattern",
                    f"属性 {prop.name} 的正则表达式无效: {e}"
                )
        
        if prop.deprecated and not prop.deprecation_message:
            result.add_warning(
                f"{prop_path}.deprecated",
                f"属性 {prop.name} 已废弃但缺少废弃说明"
            )
    
    def _validate_relationship(self, rel: Dict[str, Any], model_name: str, result: ValidationResult):
        """验证关系定义"""
        rel_path = f"model.{model_name}.relationship.{rel.get('name', 'unknown')}"
        
        if not rel.get("name"):
            result.add_warning(f"{rel_path}.name", "关系缺少名称")
        
        if not rel.get("target"):
            result.add_error(f"{rel_path}.target", "关系缺少目标模型")
        
        valid_cardinalities = ["1:1", "1:N", "N:1", "N:N", "1:0..1", "0..1:1", "0..1:N"]
        if rel.get("cardinality") and rel.get("cardinality") not in valid_cardinalities:
            result.add_warning(
                f"{rel_path}.cardinality",
                f"关系基数格式不标准: {rel.get('cardinality')}",
                f"建议使用: {', '.join(valid_cardinalities)}"
            )
    
    def _validate_index(self, idx: Dict[str, Any], model_name: str, result: ValidationResult):
        """验证索引定义"""
        idx_path = f"model.{model_name}.index"
        
        if not idx.get("fields"):
            result.add_error(f"{idx_path}.fields", "索引缺少字段定义")
    
    def validate_behavior_rule(self, rule: BehaviorRuleDefinition) -> ValidationResult:
        """
        验证行为规则完整性
        
        Args:
            rule: 行为规则定义
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)
        
        if not rule.name:
            result.add_error("rule.name", "规则名称不能为空")
        
        if not rule.condition:
            result.add_warning(
                "rule.condition",
                f"规则 {rule.name} 缺少条件定义",
                "添加 condition 字段定义触发条件"
            )
        
        if not rule.action:
            result.add_warning(
                "rule.action",
                f"规则 {rule.name} 缺少动作定义",
                "添加 action 字段定义执行动作"
            )
        
        for dep in rule.dependencies:
            if dep not in self.syntax_parser._rule_registry:
                result.add_warning(
                    f"rule.dependencies.{dep}",
                    f"规则 {rule.name} 依赖的规则 {dep} 未定义"
                )
        
        for conflict in rule.conflicts:
            if conflict not in self.syntax_parser._rule_registry:
                result.add_info(
                    f"rule.conflicts.{conflict}",
                    f"规则 {rule.name} 冲突的规则 {conflict} 未定义"
                )
        
        if rule.timeout is not None and rule.timeout <= 0:
            result.add_error(
                "rule.timeout",
                f"规则 {rule.name} 的超时时间无效: {rule.timeout}"
            )
        
        return result
    
    def validate_api_endpoint(self, endpoint: SpecEndpoint) -> ValidationResult:
        """
        验证API端点完整性
        
        Args:
            endpoint: API端点定义
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)
        
        if not endpoint.name:
            result.add_error("endpoint.name", "端点名称不能为空")
        
        if not endpoint.path:
            result.add_error("endpoint.path", "端点路径不能为空")
        elif not endpoint.path.startswith("/"):
            result.add_warning(
                "endpoint.path",
                f"端点路径应以 / 开头: {endpoint.path}"
            )
        
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        if endpoint.method.upper() not in valid_methods:
            result.add_error(
                "endpoint.method",
                f"无效的HTTP方法: {endpoint.method}",
                f"支持的方法: {', '.join(valid_methods)}"
            )
        
        for param in endpoint.parameters:
            if not param.get("name"):
                result.add_error("endpoint.parameters", "参数名称不能为空")
        
        if endpoint.authentication and not endpoint.security_schemes:
            result.add_warning(
                "endpoint.security",
                f"端点 {endpoint.name} 需要认证但未定义安全方案"
            )
        
        if endpoint.deprecated and not endpoint.version_deprecated:
            result.add_warning(
                "endpoint.deprecated",
                f"端点 {endpoint.name} 已废弃但缺少废弃版本信息"
            )
        
        return result
    
    def validate_security(self, spec: SDDSpecification) -> ValidationResult:
        """
        验证安全性
        
        Args:
            spec: SDD规范
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)
        
        auth_endpoints = [ep for ep in spec.endpoints if ep.authentication]
        if auth_endpoints:
            result.add_info(
                "security.authentication",
                f"发现 {len(auth_endpoints)} 个需要认证的端点"
            )
        
        for endpoint in spec.endpoints:
            if endpoint.method.upper() in ["POST", "PUT", "PATCH"]:
                if not endpoint.request_body:
                    result.add_warning(
                        f"security.{endpoint.name}",
                        f"端点 {endpoint.method} {endpoint.path} 可能缺少请求体验证"
                    )
        
        sensitive_patterns = ["password", "secret", "token", "key", "credential"]
        for attr in spec.attributes:
            attr_lower = attr.name.lower()
            if any(pattern in attr_lower for pattern in sensitive_patterns):
                if not attr.constraints.get("encrypted") and not attr.constraints.get("hashed"):
                    result.add_warning(
                        f"security.{attr.name}",
                        f"敏感字段 {attr.name} 建议添加加密约束"
                    )
        
        return result
    
    def validate_performance(self, spec: SDDSpecification) -> ValidationResult:
        """
        验证性能约束
        
        Args:
            spec: SDD规范
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)
        
        for endpoint in spec.endpoints:
            if endpoint.rate_limit:
                result.add_info(
                    f"performance.{endpoint.name}",
                    f"端点 {endpoint.name} 设置了速率限制: {endpoint.rate_limit}"
                )
        
        for sm in spec.state_machines:
            if len(sm.states) > 20:
                result.add_warning(
                    f"performance.{sm.name}",
                    f"状态机 {sm.name} 状态数量过多 ({len(sm.states)})，可能影响性能"
                )
        
        for rule in spec.conditional_rules:
            if rule.timeout and rule.timeout > 30000:
                result.add_warning(
                    f"performance.{rule.id}",
                    f"规则 {rule.name} 超时时间过长: {rule.timeout}ms"
                )
        
        return result
    
    def validate_complete(self, spec: SDDSpecification) -> ValidationResult:
        """
        执行完整的规范验证
        
        Args:
            spec: SDD规范
            
        Returns:
            ValidationResult: 验证结果
        """
        result = super().validate(spec)
        
        syntax_parser = EnhancedSpecSyntaxParser()
        
        for interface_data in spec.spec.get("interfaces", []):
            interface = syntax_parser.parse_interface(interface_data)
            interface_result = self.validate_interface(interface)
            result.merge(interface_result)
        
        for model_data in spec.spec.get("dataModels", spec.spec.get("data_models", [])):
            model = syntax_parser.parse_data_model(model_data)
            model_result = self.validate_data_model(model)
            result.merge(model_result)
        
        for rule_data in spec.spec.get("behaviorRules", spec.spec.get("behavior_rules", [])):
            rule = syntax_parser.parse_behavior_rule(rule_data)
            rule_result = self.validate_behavior_rule(rule)
            result.merge(rule_result)
        
        for endpoint in spec.endpoints:
            endpoint_result = self.validate_api_endpoint(endpoint)
            result.merge(endpoint_result)
        
        security_result = self.validate_security(spec)
        result.merge(security_result)
        
        performance_result = self.validate_performance(spec)
        result.merge(performance_result)
        
        return result


def main():
    """CLI入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SDD规范解析器增强版 v3.0")
    parser.add_argument("command", choices=["parse", "validate", "generate-tests", "generate-code", "complete"])
    parser.add_argument("--spec", required=True, help="规范文件路径")
    parser.add_argument("--output", help="输出目录")
    parser.add_argument("--format", choices=["json", "yaml", "markdown"], help="输出格式")
    parser.add_argument("--language", choices=["python", "typescript", "java", "go"], default="python", help="代码生成语言")
    parser.add_argument("--framework", choices=["pytest", "jest", "junit"], default="pytest", help="测试框架")
    
    args = parser.parse_args()
    
    enhanced_parser = EnhancedSDDSpecParser()
    
    with open(args.spec, "r", encoding="utf-8") as f:
        content = f.read()
    
    source_format = Path(args.spec).suffix.lstrip(".")
    if source_format == "yml":
        source_format = "yaml"
    elif source_format == "md":
        source_format = "markdown"
    
    spec, validation = enhanced_parser.parse_enhanced(content, source_format, args.spec)
    
    if args.command == "parse":
        print(f"规范ID: {spec.metadata.id}")
        print(f"规范名称: {spec.metadata.name}")
        print(f"版本: {spec.metadata.version}")
        print(f"嵌套结构数: {len(spec.nested_structures)}")
        print(f"条件规则数: {len(spec.conditional_rules)}")
        print(f"状态机数: {len(spec.state_machines)}")
    
    elif args.command == "validate":
        enhanced_validator = EnhancedSpecCompletenessValidator()
        complete_result = enhanced_validator.validate_complete(spec)
        
        print(f"验证结果: {'通过' if complete_result.is_valid else '失败'}")
        print(f"错误数: {len(complete_result.errors)}")
        print(f"警告数: {len(complete_result.warnings)}")
        print(f"信息数: {len(complete_result.info)}")
        
        for error in complete_result.errors[:10]:
            print(f"  - [{error.severity.value}] {error.path}: {error.message}")
            if error.suggestion:
                print(f"    建议: {error.suggestion}")
    
    elif args.command == "generate-tests":
        test_generator = TestCaseSkeletonGenerator(framework=args.framework)
        suites = test_generator.generate_all_tests(spec)
        
        output_dir = args.output or "./generated_tests"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for name, suite in suites.items():
            output_path = Path(output_dir) / f"test_{name}{test_generator.syntax['file_ext']}"
            test_generator.export_tests(suite, str(output_path))
            print(f"生成测试文件: {output_path}")
    
    elif args.command == "generate-code":
        code_generator = CodeSkeletonGenerator(language=args.language)
        files = code_generator.generate_all(spec)
        
        output_dir = args.output or "./generated_code"
        exported = code_generator.export_to_directory(output_dir)
        
        for file_path in exported:
            print(f"生成代码文件: {file_path}")
    
    elif args.command == "complete":
        enhanced_validator = EnhancedSpecCompletenessValidator()
        complete_result = enhanced_validator.validate_complete(spec)
        
        test_generator = TestCaseSkeletonGenerator(framework=args.framework)
        test_suites = test_generator.generate_all_tests(spec)
        
        code_generator = CodeSkeletonGenerator(language=args.language)
        code_files = code_generator.generate_all(spec)
        
        output_dir = args.output or "./generated"
        
        test_dir = Path(output_dir) / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        for name, suite in test_suites.items():
            output_path = test_dir / f"test_{name}{test_generator.syntax['file_ext']}"
            test_generator.export_tests(suite, str(output_path))
        
        code_dir = Path(output_dir) / "src"
        code_generator.export_to_directory(str(code_dir))
        
        print(f"验证结果: {'通过' if complete_result.is_valid else '失败'}")
        print(f"生成测试文件数: {len(test_suites)}")
        print(f"生成代码文件数: {len(code_files)}")
        print(f"输出目录: {output_dir}")


if __name__ == "__main__":
    main()