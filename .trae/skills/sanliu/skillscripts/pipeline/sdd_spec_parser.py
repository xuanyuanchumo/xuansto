#!/usr/bin/env python3
"""
SDD规范解析器增强版

支持多种规范格式的解析、验证和转换：
1. Markdown格式规范
2. YAML格式规范
3. JSON格式规范

功能：
- 多格式规范解析
- 规范结构验证
- 规范语义验证
- 规范转换（格式互转）
- 规范元数据提取
"""

import copy
import json
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import yaml


class SpecFormat(Enum):
    MARKDOWN = "markdown"
    YAML = "yaml"
    JSON = "json"


class SpecType(Enum):
    ENTITY = "EntitySpec"
    INTERFACE = "InterfaceSpec"
    API = "ApiSpec"
    BUSINESS_RULE = "BusinessRuleSpec"
    CONSTRAINT = "ConstraintSpec"
    ACCEPTANCE = "AcceptanceSpec"
    FUNCTION = "FunctionSpec"


class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    path: str
    message: str
    severity: ValidationSeverity
    suggestion: str = ""


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    
    def add_error(self, path: str, message: str, suggestion: str = ""):
        self.errors.append(ValidationError(path, message, ValidationSeverity.ERROR, suggestion))
        self.is_valid = False
    
    def add_warning(self, path: str, message: str, suggestion: str = ""):
        self.warnings.append(ValidationError(path, message, ValidationSeverity.WARNING, suggestion))


@dataclass
class SpecReference:
    ref_path: str
    target_spec_id: str
    target_field: str = ""
    resolved: bool = False
    resolved_value: Any = None


@dataclass
class SpecInheritance:
    parent_spec_id: str
    merge_strategy: str = "override"
    excluded_fields: List[str] = field(default_factory=list)
    parent_spec: Optional['SDDSpecification'] = None


@dataclass
class NestedAttribute:
    name: str
    type: str
    nested_attributes: List['NestedAttribute'] = field(default_factory=list)
    is_array: bool = False
    description: str = ""
    required: bool = True


@dataclass
class TestCase:
    id: str
    name: str
    description: str
    scenario_id: str
    test_type: str
    priority: str
    preconditions: List[str] = field(default_factory=list)
    test_steps: List[Dict[str, str]] = field(default_factory=list)
    expected_results: List[str] = field(default_factory=list)
    test_data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    coverage_items: List[str] = field(default_factory=list)


@dataclass
class CoverageMapping:
    spec_id: str
    spec_name: str
    total_requirements: int
    covered_requirements: int
    coverage_percentage: float
    test_cases: List[str] = field(default_factory=list)
    uncovered_items: List[str] = field(default_factory=list)
    coverage_details: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class CoverageReport:
    report_id: str
    generated_at: str
    spec_id: str
    overall_coverage: float
    coverage_by_type: Dict[str, CoverageMapping] = field(default_factory=dict)
    coverage_by_priority: Dict[str, float] = field(default_factory=dict)
    missing_coverage: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class CompletenessCheck:
    spec_id: str
    check_time: str
    completeness_score: float
    missing_elements: Dict[str, List[str]] = field(default_factory=dict)
    quality_issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)


@dataclass
class SpecAttribute:
    name: str
    type: str
    description: str = ""
    required: bool = True
    unique: bool = False
    default: Any = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    enum_values: List[str] = field(default_factory=list)
    example: Any = None


@dataclass
class SpecEndpoint:
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


@dataclass
class SpecScenario:
    name: str
    given: str
    when: str
    then: str
    test_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpecMetadata:
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


@dataclass
class SDDSpecification:
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
    
    nested_attributes: List[NestedAttribute] = field(default_factory=list)
    references: List[SpecReference] = field(default_factory=list)
    inheritance: Optional[SpecInheritance] = None
    imported_specs: Dict[str, 'SDDSpecification'] = field(default_factory=dict)
    
    test_cases: List[TestCase] = field(default_factory=list)
    coverage_report: Optional[CoverageReport] = None
    completeness_check: Optional[CompletenessCheck] = None


class BaseSpecParser(ABC):
    """规范解析器基类"""
    
    @abstractmethod
    def parse(self, content: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def serialize(self, spec: Dict[str, Any]) -> str:
        pass
    
    @abstractmethod
    def get_format(self) -> SpecFormat:
        pass


class MarkdownSpecParser(BaseSpecParser):
    """Markdown格式规范解析器"""
    
    def get_format(self) -> SpecFormat:
        return SpecFormat.MARKDOWN
    
    def parse(self, content: str) -> Dict[str, Any]:
        spec = {
            "apiVersion": "sdd/v1",
            "kind": self._detect_kind(content),
            "metadata": self._extract_metadata(content),
            "spec": self._extract_spec(content)
        }
        return spec
    
    def serialize(self, spec: Dict[str, Any]) -> str:
        lines = []
        
        metadata = spec.get("metadata", {})
        lines.append(f"# {metadata.get('name', '未命名规范')}")
        lines.append("")
        lines.append(f"规范ID: {metadata.get('id', 'UNKNOWN')}")
        lines.append(f"版本: {metadata.get('version', 'v1.0')}")
        lines.append("")
        
        spec_content = spec.get("spec", {})
        
        if "description" in spec_content:
            lines.append("## 功能描述")
            lines.append("")
            lines.append(spec_content["description"])
            lines.append("")
        
        if "attributes" in spec_content:
            lines.append("## 属性定义")
            lines.append("")
            for attr in spec_content["attributes"]:
                required = "必填" if attr.get("required", True) else "可选"
                unique = ", 唯一" if attr.get("unique", False) else ""
                lines.append(f"- {attr['name']}: {attr.get('description', '')}, {required}{unique}, 类型: {attr.get('type', 'string')}")
            lines.append("")
        
        if "endpoints" in spec_content:
            lines.append("## 接口定义")
            lines.append("")
            for ep in spec_content["endpoints"]:
                lines.append(f"### {ep['name']}")
                lines.append(f"- 方法: {ep.get('method', 'GET')}")
                lines.append(f"- 路径: {ep.get('path', '/')}")
                lines.append(f"- 描述: {ep.get('description', '')}")
                lines.append("")
        
        if "scenarios" in spec_content:
            lines.append("## 测试场景")
            lines.append("")
            for scenario in spec_content["scenarios"]:
                lines.append(f"### {scenario.get('name', '未命名场景')}")
                lines.append(f"- Given: {scenario.get('given', '')}")
                lines.append(f"- When: {scenario.get('when', '')}")
                lines.append(f"- Then: {scenario.get('then', '')}")
                lines.append("")
        
        if "constraints" in spec_content:
            lines.append("## 约束条件")
            lines.append("")
            for constraint in spec_content["constraints"]:
                lines.append(f"- {constraint.get('name', '')}: {constraint.get('description', '')}")
            lines.append("")
        
        if "exceptions" in spec_content or "errors" in spec_content:
            lines.append("## 异常处理")
            lines.append("")
            exceptions = spec_content.get("exceptions", spec_content.get("errors", []))
            for exc in exceptions:
                lines.append(f"- {exc.get('name', exc.get('type', ''))}: {exc.get('description', exc.get('message', ''))}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _detect_kind(self, content: str) -> str:
        if "接口路径" in content or "API" in content or "endpoints" in content.lower():
            return SpecType.INTERFACE.value
        elif "属性定义" in content or "attributes" in content.lower():
            return SpecType.ENTITY.value
        elif "场景" in content or "Given" in content or "When" in content:
            return SpecType.ACCEPTANCE.value
        elif "约束" in content or "constraint" in content.lower():
            return SpecType.CONSTRAINT.value
        elif "业务规则" in content or "规则编号" in content:
            return SpecType.BUSINESS_RULE.value
        else:
            return SpecType.FUNCTION.value
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        metadata = {}
        
        id_match = re.search(r"规范ID[：:]\s*(\S+)", content)
        metadata["id"] = id_match.group(1) if id_match else f"SPC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        metadata["name"] = title_match.group(1).strip() if title_match else "未命名规范"
        
        version_match = re.search(r"版本[：:]\s*(\S+)", content)
        metadata["version"] = version_match.group(1) if version_match else "v1.0"
        
        author_match = re.search(r"作者[：:]\s*(.+)$", content, re.MULTILINE)
        metadata["author"] = author_match.group(1).strip() if author_match else ""
        
        status_match = re.search(r"状态[：:]\s*(\S+)", content)
        metadata["status"] = status_match.group(1) if status_match else "draft"
        
        return metadata
    
    def _extract_spec(self, content: str) -> Dict[str, Any]:
        spec = {}
        
        desc_match = re.search(r"##\s*功能描述\s*\n(.+?)(?=\n##|\Z)", content, re.DOTALL)
        if desc_match:
            spec["description"] = desc_match.group(1).strip()
        
        spec["attributes"] = self._extract_attributes(content)
        spec["endpoints"] = self._extract_endpoints(content)
        spec["scenarios"] = self._extract_scenarios(content)
        spec["constraints"] = self._extract_constraints(content)
        spec["exceptions"] = self._extract_exceptions(content)
        
        return spec
    
    def _extract_attributes(self, content: str) -> List[Dict[str, Any]]:
        attributes = []
        
        attr_pattern = r"##\s*(?:属性定义|输入条件)\s*\n((?:\s*[-*]\s*.+\n?)+)"
        for match in re.finditer(attr_pattern, content):
            lines = match.group(1).strip().split("\n")
            for line in lines:
                line = line.strip("- *").strip()
                if not line:
                    continue
                
                attr = {}
                if ":" in line:
                    parts = line.split(":", 1)
                    attr["name"] = parts[0].strip()
                    attr_desc = parts[1].strip() if len(parts) > 1 else ""
                    
                    type_match = re.search(r"类型[：:]\s*(\w+)", attr_desc)
                    attr["type"] = type_match.group(1) if type_match else "string"
                    
                    attr["required"] = "必填" in attr_desc or "required" in attr_desc.lower()
                    attr["unique"] = "唯一" in attr_desc or "unique" in attr_desc.lower()
                    attr["description"] = re.sub(r"[，,]?\s*(必填|可选|唯一|类型[：:]\s*\w+)", "", attr_desc).strip()
                else:
                    attr["name"] = line
                    attr["type"] = "string"
                    attr["required"] = True
                
                attributes.append(attr)
        
        return attributes
    
    def _extract_endpoints(self, content: str) -> List[Dict[str, Any]]:
        endpoints = []
        
        ep_pattern = r"###\s*(.+?)\s*\n((?:.+\n)*?)(?=\n###|\n##|\Z)"
        for match in re.finditer(ep_pattern, content):
            ep = {}
            ep["name"] = match.group(1).strip()
            ep_body = match.group(2)
            
            method_match = re.search(r"方法[：:]\s*(\w+)", ep_body)
            ep["method"] = method_match.group(1).upper() if method_match else "GET"
            
            path_match = re.search(r"路径[：:]\s*(\S+)", ep_body)
            ep["path"] = path_match.group(1) if path_match else "/"
            
            desc_match = re.search(r"描述[：:]\s*(.+)$", ep_body, re.MULTILINE)
            ep["description"] = desc_match.group(1).strip() if desc_match else ""
            
            endpoints.append(ep)
        
        return endpoints
    
    def _extract_scenarios(self, content: str) -> List[Dict[str, Any]]:
        scenarios = []
        
        scenario_pattern = r"###\s*(?:场景[：:]?\s*)?(.+?)\s*\n((?:.+\n)*?)(?=\n###|\n##|\Z)"
        for match in re.finditer(scenario_pattern, content):
            scenario = {}
            scenario["name"] = match.group(1).strip()
            scenario_body = match.group(2)
            
            given_match = re.search(r"Given[：:]\s*(.+)$", scenario_body, re.MULTILINE)
            scenario["given"] = given_match.group(1).strip() if given_match else ""
            
            when_match = re.search(r"When[：:]\s*(.+)$", scenario_body, re.MULTILINE)
            scenario["when"] = when_match.group(1).strip() if when_match else ""
            
            then_match = re.search(r"Then[：:]\s*(.+)$", scenario_body, re.MULTILINE)
            scenario["then"] = then_match.group(1).strip() if then_match else ""
            
            if scenario["given"] or scenario["when"] or scenario["then"]:
                scenarios.append(scenario)
        
        return scenarios
    
    def _extract_constraints(self, content: str) -> List[Dict[str, Any]]:
        constraints = []
        
        constraint_pattern = r"##\s*约束条件\s*\n((?:\s*[-*]\s*.+\n?)+)"
        for match in re.finditer(constraint_pattern, content):
            lines = match.group(1).strip().split("\n")
            for line in lines:
                line = line.strip("- *").strip()
                if not line:
                    continue
                
                constraint = {}
                if ":" in line:
                    parts = line.split(":", 1)
                    constraint["name"] = parts[0].strip()
                    constraint["description"] = parts[1].strip() if len(parts) > 1 else ""
                else:
                    constraint["name"] = line
                    constraint["description"] = ""
                
                constraints.append(constraint)
        
        return constraints
    
    def _extract_exceptions(self, content: str) -> List[Dict[str, Any]]:
        exceptions = []
        
        exc_pattern = r"##\s*异常处理\s*\n((?:\s*[-*]\s*.+\n?)+)"
        for match in re.finditer(exc_pattern, content):
            lines = match.group(1).strip().split("\n")
            for line in lines:
                line = line.strip("- *").strip()
                if not line:
                    continue
                
                exc = {}
                if ":" in line:
                    parts = line.split(":", 1)
                    exc["name"] = parts[0].strip()
                    exc["description"] = parts[1].strip() if len(parts) > 1 else ""
                else:
                    exc["name"] = line
                    exc["description"] = ""
                
                exceptions.append(exc)
        
        return exceptions


class YAMLSpecParser(BaseSpecParser):
    """YAML格式规范解析器"""
    
    def get_format(self) -> SpecFormat:
        return SpecFormat.YAML
    
    def parse(self, content: str) -> Dict[str, Any]:
        return yaml.safe_load(content)
    
    def serialize(self, spec: Dict[str, Any]) -> str:
        return yaml.dump(spec, allow_unicode=True, default_flow_style=False, sort_keys=False)


class JSONSpecParser(BaseSpecParser):
    """JSON格式规范解析器"""
    
    def get_format(self) -> SpecFormat:
        return SpecFormat.JSON
    
    def parse(self, content: str) -> Dict[str, Any]:
        return json.loads(content)
    
    def serialize(self, spec: Dict[str, Any]) -> str:
        return json.dumps(spec, ensure_ascii=False, indent=2)


class ComplexSpecParser:
    """复杂规范解析器 - 处理嵌套结构、引用和继承"""
    
    def __init__(self):
        self.spec_registry: Dict[str, SDDSpecification] = {}
        self.reference_cache: Dict[str, Any] = {}
    
    def parse_nested_attributes(self, attr_dict: Dict[str, Any], parent_path: str = "") -> NestedAttribute:
        nested = NestedAttribute(
            name=attr_dict.get("name", ""),
            type=attr_dict.get("type", "object"),
            is_array=attr_dict.get("isArray", False) or attr_dict.get("type", "").endswith("[]"),
            description=attr_dict.get("description", ""),
            required=attr_dict.get("required", True)
        )
        
        if "attributes" in attr_dict or "properties" in attr_dict:
            sub_attrs = attr_dict.get("attributes", attr_dict.get("properties", []))
            for sub_attr in sub_attrs:
                nested.nested_attributes.append(
                    self.parse_nested_attributes(sub_attr, f"{parent_path}.{nested.name}")
                )
        
        return nested
    
    def resolve_reference(self, ref_path: str, current_spec: SDDSpecification) -> SpecReference:
        ref = SpecReference(
            ref_path=ref_path,
            target_spec_id="",
            target_field=""
        )
        
        if ref_path.startswith("#/"):
            ref.target_spec_id = current_spec.metadata.id
            ref.target_field = ref_path[2:]
            ref.resolved_value = self._resolve_local_ref(ref.target_field, current_spec)
            ref.resolved = ref.resolved_value is not None
        elif ref_path.startswith("$ref:"):
            parts = ref_path[5:].split("#", 1)
            ref.target_spec_id = parts[0].strip()
            ref.target_field = parts[1].lstrip("/") if len(parts) > 1 else ""
            
            if ref.target_spec_id in current_spec.imported_specs:
                parent_spec = current_spec.imported_specs[ref.target_spec_id]
                ref.resolved_value = self._resolve_local_ref(ref.target_field, parent_spec)
                ref.resolved = ref.resolved_value is not None
        elif "/" in ref_path:
            parts = ref_path.split("#", 1)
            ref.target_spec_id = parts[0]
            ref.target_field = parts[1].lstrip("/") if len(parts) > 1 else ""
        
        return ref
    
    def _resolve_local_ref(self, path: str, spec: SDDSpecification) -> Any:
        if not path:
            return None
        
        parts = path.split("/")
        current = spec.spec
        
        for part in parts:
            if isinstance(current, dict):
                if part.isdigit():
                    current = current.get(int(part))
                else:
                    current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    def process_inheritance(self, spec: SDDSpecification, spec_registry: Dict[str, 'SDDSpecification']) -> SDDSpecification:
        if "extends" not in spec.spec and "inheritance" not in spec.spec:
            return spec
        
        inheritance_config = spec.spec.get("extends", spec.spec.get("inheritance", {}))
        
        if isinstance(inheritance_config, str):
            parent_id = inheritance_config
            inheritance = SpecInheritance(parent_spec_id=parent_id)
        else:
            inheritance = SpecInheritance(
                parent_spec_id=inheritance_config.get("specId", inheritance_config.get("parent", "")),
                merge_strategy=inheritance_config.get("strategy", "override"),
                excluded_fields=inheritance_config.get("exclude", [])
            )
        
        if inheritance.parent_spec_id in spec_registry:
            parent_spec = spec_registry[inheritance.parent_spec_id]
            inheritance.parent_spec = parent_spec
            spec = self._merge_specs(spec, parent_spec, inheritance)
        
        spec.inheritance = inheritance
        return spec
    
    def _merge_specs(
        self,
        child_spec: SDDSpecification,
        parent_spec: SDDSpecification,
        inheritance: SpecInheritance
    ) -> SDDSpecification:
        merged_spec = copy.deepcopy(parent_spec)
        
        if inheritance.merge_strategy == "override":
            for key, value in child_spec.spec.items():
                if key not in inheritance.excluded_fields:
                    if key in merged_spec.spec and isinstance(merged_spec.spec[key], dict) and isinstance(value, dict):
                        merged_spec.spec[key] = {**merged_spec.spec[key], **value}
                    elif key in merged_spec.spec and isinstance(merged_spec.spec[key], list) and isinstance(value, list):
                        merged_spec.spec[key] = merged_spec.spec[key] + value
                    else:
                        merged_spec.spec[key] = value
            merged_spec.attributes = parent_spec.attributes + child_spec.attributes
            merged_spec.endpoints = parent_spec.endpoints + child_spec.endpoints
            merged_spec.scenarios = parent_spec.scenarios + child_spec.scenarios
            
        elif inheritance.merge_strategy == "replace":
            for key, value in child_spec.spec.items():
                if key not in inheritance.excluded_fields:
                    merged_spec.spec[key] = value
            merged_spec.attributes = child_spec.attributes
            merged_spec.endpoints = child_spec.endpoints
            merged_spec.scenarios = child_spec.scenarios
            
        elif inheritance.merge_strategy == "merge":
            for key, value in child_spec.spec.items():
                if key not in inheritance.excluded_fields:
                    merged_spec.spec[key] = value
            merged_spec.attributes = self._merge_attributes(parent_spec.attributes, child_spec.attributes)
            merged_spec.endpoints = parent_spec.endpoints + child_spec.endpoints
            merged_spec.scenarios = parent_spec.scenarios + child_spec.scenarios
        
        merged_spec.metadata = child_spec.metadata
        merged_spec.kind = child_spec.kind
        merged_spec.api_version = child_spec.api_version
        
        return merged_spec
    
    def _merge_attributes(self, parent_attrs: List[SpecAttribute], child_attrs: List[SpecAttribute]) -> List[SpecAttribute]:
        merged = {attr.name: attr for attr in parent_attrs}
        for attr in child_attrs:
            merged[attr.name] = attr
        return list(merged.values())
    
    def extract_references(self, spec_dict: Dict[str, Any], path: str = "") -> List[Tuple[str, str]]:
        references = []
        
        if isinstance(spec_dict, dict):
            for key, value in spec_dict.items():
                current_path = f"{path}/{key}" if path else key
                
                if key == "$ref" and isinstance(value, str):
                    references.append((current_path, value))
                elif isinstance(value, (dict, list)):
                    references.extend(self.extract_references(value, current_path))
        
        elif isinstance(spec_dict, list):
            for idx, item in enumerate(spec_dict):
                current_path = f"{path}/{idx}"
                references.extend(self.extract_references(item, current_path))
        
        return references
    
    def resolve_all_references(self, spec: SDDSpecification) -> SDDSpecification:
        refs = self.extract_references(spec.spec)
        
        for ref_path, ref_value in refs:
            ref = self.resolve_reference(ref_value, spec)
            spec.references.append(ref)
            
            if ref.resolved and ref.resolved_value is not None:
                self._apply_resolved_reference(spec.spec, ref_path, ref.resolved_value)
        
        return spec
    
    def _apply_resolved_reference(self, spec_dict: Dict[str, Any], path: str, value: Any):
        parts = path.split("/")[:-1]
        current = spec_dict
        
        for part in parts:
            if part.isdigit():
                current = current[int(part)]
            else:
                current = current.get(part)
            
            if current is None:
                return
        
        last_part = path.split("/")[-1]
        if last_part == "$ref":
            parent_path = path.split("/")[:-1]
            parent = spec_dict
            for part in parent_path:
                if part.isdigit():
                    parent = parent[int(part)]
                else:
                    parent = parent.get(part)
            
            if isinstance(parent, dict) and "$ref" in parent:
                ref_key = parent.get("refKey", "value")
                parent.clear()
                if isinstance(value, dict):
                    parent.update(value)
                else:
                    parent[ref_key] = value


class TestCaseGenerator:
    """测试用例生成器 - 从规范自动生成测试用例"""
    
    TEST_TYPE_MAP = {
        "positive": "正常流程测试",
        "negative": "异常流程测试",
        "boundary": "边界值测试",
        "security": "安全测试",
        "performance": "性能测试",
        "integration": "集成测试"
    }
    
    PRIORITY_MAP = {
        "P0": "critical",
        "P1": "high",
        "P2": "medium",
        "P3": "low"
    }
    
    def generate_test_cases(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        
        for idx, scenario in enumerate(spec.scenarios):
            test_case = self._generate_from_scenario(spec, scenario, idx)
            test_cases.append(test_case)
        
        for endpoint in spec.endpoints:
            endpoint_tests = self._generate_endpoint_tests(spec, endpoint)
            test_cases.extend(endpoint_tests)
        
        for attr in spec.attributes:
            attr_tests = self._generate_attribute_tests(spec, attr)
            test_cases.extend(attr_tests)
        
        constraint_tests = self._generate_constraint_tests(spec)
        test_cases.extend(constraint_tests)
        
        return test_cases
    
    def _generate_from_scenario(self, spec: SDDSpecification, scenario: SpecScenario, idx: int) -> TestCase:
        test_id = f"TC-{spec.metadata.id}-{idx+1:03d}"
        
        test_type = self._determine_test_type(scenario)
        priority = self._determine_priority(scenario)
        
        test_steps = self._generate_test_steps(scenario)
        expected_results = self._generate_expected_results(scenario)
        
        return TestCase(
            id=test_id,
            name=f"验证: {scenario.name}",
            description=f"测试场景: {scenario.given} -> {scenario.when} -> {scenario.then}",
            scenario_id=scenario.name,
            test_type=test_type,
            priority=priority,
            preconditions=self._extract_preconditions(scenario),
            test_steps=test_steps,
            expected_results=expected_results,
            test_data=scenario.test_data,
            tags=[spec.kind.value, test_type],
            coverage_items=[scenario.name]
        )
    
    def _determine_test_type(self, scenario: SpecScenario) -> str:
        then_lower = scenario.then.lower()
        given_lower = scenario.given.lower()
        
        if any(kw in then_lower for kw in ["异常", "错误", "失败", "error", "fail", "exception"]):
            return "negative"
        elif any(kw in then_lower for kw in ["边界", "极限", "最大", "最小", "boundary", "limit", "max", "min"]):
            return "boundary"
        elif any(kw in then_lower for kw in ["安全", "权限", "认证", "security", "auth", "permission"]):
            return "security"
        elif any(kw in then_lower for kw in ["性能", "响应时间", "吞吐", "performance", "latency"]):
            return "performance"
        else:
            return "positive"
    
    def _determine_priority(self, scenario: SpecScenario) -> str:
        if hasattr(scenario, 'priority'):
            return self.PRIORITY_MAP.get(scenario.priority, "medium")
        
        then_lower = scenario.then.lower()
        if any(kw in then_lower for kw in ["核心", "关键", "critical", "core"]):
            return "critical"
        elif any(kw in then_lower for kw in ["重要", "主要", "important", "major"]):
            return "high"
        elif any(kw in then_lower for kw in ["次要", "optional", "minor"]):
            return "low"
        return "medium"
    
    def _generate_test_steps(self, scenario: SpecScenario) -> List[Dict[str, str]]:
        steps = []
        
        if scenario.given:
            steps.append({
                "step": "准备",
                "action": scenario.given,
                "expected": "前置条件满足"
            })
        
        if scenario.when:
            steps.append({
                "step": "执行",
                "action": scenario.when,
                "expected": "操作执行完成"
            })
        
        if scenario.then:
            steps.append({
                "step": "验证",
                "action": f"验证结果: {scenario.then}",
                "expected": scenario.then
            })
        
        return steps
    
    def _generate_expected_results(self, scenario: SpecScenario) -> List[str]:
        results = []
        
        if scenario.then:
            results.append(scenario.then)
        
        return results
    
    def _extract_preconditions(self, scenario: SpecScenario) -> List[str]:
        preconditions = []
        
        if scenario.given:
            preconditions.append(scenario.given)
        
        return preconditions
    
    def _generate_endpoint_tests(self, spec: SDDSpecification, endpoint: SpecEndpoint) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-{spec.metadata.id}-API-{endpoint.name[:20]}"
        
        test_cases.append(TestCase(
            id=f"{base_id}-001",
            name=f"API测试: {endpoint.name} - 正常调用",
            description=f"测试 {endpoint.method} {endpoint.path} 正常调用",
            scenario_id=f"API-{endpoint.name}",
            test_type="positive",
            priority="high",
            preconditions=["系统正常运行", "用户已认证"] if endpoint.authentication else ["系统正常运行"],
            test_steps=[
                {"step": "准备", "action": "构造请求参数", "expected": "参数构造完成"},
                {"step": "执行", "action": f"发送 {endpoint.method} 请求到 {endpoint.path}", "expected": "请求发送成功"},
                {"step": "验证", "action": "验证响应状态码和内容", "expected": "响应符合预期"}
            ],
            expected_results=["响应状态码正确", "响应数据结构正确"],
            test_data={"method": endpoint.method, "path": endpoint.path},
            tags=["API", endpoint.method],
            coverage_items=[endpoint.name]
        ))
        
        if endpoint.authentication:
            test_cases.append(TestCase(
                id=f"{base_id}-002",
                name=f"API测试: {endpoint.name} - 未认证访问",
                description=f"测试 {endpoint.method} {endpoint.path} 未认证访问被拒绝",
                scenario_id=f"API-{endpoint.name}-auth",
                test_type="security",
                priority="critical",
                preconditions=["系统正常运行", "用户未认证"],
                test_steps=[
                    {"step": "准备", "action": "构造无认证信息的请求", "expected": "请求构造完成"},
                    {"step": "执行", "action": f"发送 {endpoint.method} 请求到 {endpoint.path}", "expected": "请求发送成功"},
                    {"step": "验证", "action": "验证返回401未授权", "expected": "返回401状态码"}
                ],
                expected_results=["返回401 Unauthorized"],
                test_data={"method": endpoint.method, "path": endpoint.path},
                tags=["API", "Security"],
                coverage_items=[f"{endpoint.name}-auth"]
            ))
        
        for error in endpoint.errors:
            error_code = error.get("code", error.get("status", "500"))
            test_cases.append(TestCase(
                id=f"{base_id}-ERR-{error_code}",
                name=f"API测试: {endpoint.name} - 错误处理 {error_code}",
                description=f"测试 {endpoint.method} {endpoint.path} 错误场景: {error.get('description', error.get('message', ''))}",
                scenario_id=f"API-{endpoint.name}-error-{error_code}",
                test_type="negative",
                priority="high",
                preconditions=["系统正常运行"],
                test_steps=[
                    {"step": "准备", "action": "构造触发错误的请求", "expected": "请求构造完成"},
                    {"step": "执行", "action": f"发送 {endpoint.method} 请求", "expected": "请求发送成功"},
                    {"step": "验证", "action": f"验证返回错误码 {error_code}", "expected": f"返回 {error_code} 错误"}
                ],
                expected_results=[f"返回错误码 {error_code}", "错误信息格式正确"],
                test_data={"method": endpoint.method, "path": endpoint.path, "trigger_error": error},
                tags=["API", "Error"],
                coverage_items=[f"{endpoint.name}-error-{error_code}"]
            ))
        
        return test_cases
    
    def _generate_attribute_tests(self, spec: SDDSpecification, attr: SpecAttribute) -> List[TestCase]:
        test_cases = []
        base_id = f"TC-{spec.metadata.id}-ATTR-{attr.name}"
        
        if attr.required:
            test_cases.append(TestCase(
                id=f"{base_id}-required",
                name=f"属性测试: {attr.name} - 必填验证",
                description=f"验证属性 {attr.name} 必填约束",
                scenario_id=f"ATTR-{attr.name}-required",
                test_type="negative",
                priority="high",
                preconditions=["系统就绪"],
                test_steps=[
                    {"step": "准备", "action": f"构造不包含 {attr.name} 的数据", "expected": "数据构造完成"},
                    {"step": "执行", "action": "提交数据", "expected": "提交执行"},
                    {"step": "验证", "action": "验证返回必填错误", "expected": "返回必填字段错误"}
                ],
                expected_results=[f"返回 {attr.name} 必填错误"],
                test_data={"attribute": attr.name, "value": None},
                tags=["Attribute", "Validation"],
                coverage_items=[f"{attr.name}-required"]
            ))
        
        if attr.constraints:
            for constraint_name, constraint_value in attr.constraints.items():
                test_cases.append(TestCase(
                    id=f"{base_id}-{constraint_name}",
                    name=f"属性测试: {attr.name} - {constraint_name}约束",
                    description=f"验证属性 {attr.name} 的 {constraint_name} 约束: {constraint_value}",
                    scenario_id=f"ATTR-{attr.name}-{constraint_name}",
                    test_type="boundary" if constraint_name in ["minLength", "maxLength", "min", "max"] else "negative",
                    priority="medium",
                    preconditions=["系统就绪"],
                    test_steps=[
                        {"step": "准备", "action": f"构造违反{constraint_name}约束的数据", "expected": "数据构造完成"},
                        {"step": "执行", "action": "提交数据", "expected": "提交执行"},
                        {"step": "验证", "action": f"验证返回{constraint_name}约束错误", "expected": "返回约束违反错误"}
                    ],
                    expected_results=[f"返回 {constraint_name} 约束错误"],
                    test_data={"attribute": attr.name, "constraint": constraint_name, "value": constraint_value},
                    tags=["Attribute", "Constraint"],
                    coverage_items=[f"{attr.name}-{constraint_name}"]
                ))
        
        if attr.type == "enum" and attr.enum_values:
            test_cases.append(TestCase(
                id=f"{base_id}-enum",
                name=f"属性测试: {attr.name} - 枚举值验证",
                description=f"验证属性 {attr.name} 枚举值: {attr.enum_values}",
                scenario_id=f"ATTR-{attr.name}-enum",
                test_type="negative",
                priority="medium",
                preconditions=["系统就绪"],
                test_steps=[
                    {"step": "准备", "action": "构造无效枚举值", "expected": "数据构造完成"},
                    {"step": "执行", "action": "提交数据", "expected": "提交执行"},
                    {"step": "验证", "action": "验证返回枚举值错误", "expected": "返回无效枚举值错误"}
                ],
                expected_results=["返回无效枚举值错误"],
                test_data={"attribute": attr.name, "valid_values": attr.enum_values},
                tags=["Attribute", "Enum"],
                coverage_items=[f"{attr.name}-enum"]
            ))
        
        return test_cases
    
    def _generate_constraint_tests(self, spec: SDDSpecification) -> List[TestCase]:
        test_cases = []
        
        for idx, constraint in enumerate(spec.constraints):
            constraint_name = constraint.get("name", f"constraint-{idx}")
            test_cases.append(TestCase(
                id=f"TC-{spec.metadata.id}-CONST-{idx+1:02d}",
                name=f"约束测试: {constraint_name}",
                description=f"验证约束: {constraint.get('description', constraint_name)}",
                scenario_id=f"CONST-{constraint_name}",
                test_type="negative",
                priority="high",
                preconditions=["系统就绪"],
                test_steps=[
                    {"step": "准备", "action": f"构造违反约束的数据", "expected": "数据构造完成"},
                    {"step": "执行", "action": "执行操作", "expected": "操作执行"},
                    {"step": "验证", "action": "验证约束被触发", "expected": "约束验证失败"}
                ],
                expected_results=[f"约束 {constraint_name} 被正确验证"],
                test_data={"constraint": constraint},
                tags=["Constraint"],
                coverage_items=[constraint_name]
            ))
        
        return test_cases


class CoverageAnalyzer:
    """覆盖率分析器 - 生成测试覆盖率映射报告"""
    
    def analyze_coverage(self, spec: SDDSpecification) -> CoverageReport:
        report_id = f"COV-{spec.metadata.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        coverage_by_type: Dict[str, CoverageMapping] = {}
        
        attr_coverage = self._analyze_attribute_coverage(spec)
        coverage_by_type["attributes"] = attr_coverage
        
        endpoint_coverage = self._analyze_endpoint_coverage(spec)
        coverage_by_type["endpoints"] = endpoint_coverage
        
        scenario_coverage = self._analyze_scenario_coverage(spec)
        coverage_by_type["scenarios"] = scenario_coverage
        
        constraint_coverage = self._analyze_constraint_coverage(spec)
        coverage_by_type["constraints"] = constraint_coverage
        
        total_requirements = sum(m.total_requirements for m in coverage_by_type.values())
        total_covered = sum(m.covered_requirements for m in coverage_by_type.values())
        overall_coverage = (total_covered / total_requirements * 100) if total_requirements > 0 else 0
        
        coverage_by_priority = self._calculate_coverage_by_priority(spec.test_cases)
        
        missing_coverage = self._identify_missing_coverage(coverage_by_type)
        
        recommendations = self._generate_recommendations(coverage_by_type, overall_coverage)
        
        return CoverageReport(
            report_id=report_id,
            generated_at=datetime.now().isoformat(),
            spec_id=spec.metadata.id,
            overall_coverage=round(overall_coverage, 2),
            coverage_by_type=coverage_by_type,
            coverage_by_priority=coverage_by_priority,
            missing_coverage=missing_coverage,
            recommendations=recommendations
        )
    
    def _analyze_attribute_coverage(self, spec: SDDSpecification) -> CoverageMapping:
        total = len(spec.attributes)
        covered = 0
        coverage_details = {}
        uncovered_items = []
        
        for attr in spec.attributes:
            is_covered = any(
                attr.name in tc.coverage_items or f"{attr.name}-required" in tc.coverage_items
                for tc in spec.test_cases
            )
            
            if is_covered:
                covered += 1
                covering_tests = [
                    tc.id for tc in spec.test_cases
                    if attr.name in tc.coverage_items or f"{attr.name}-required" in tc.coverage_items
                ]
                coverage_details[attr.name] = {
                    "covered": True,
                    "test_cases": covering_tests,
                    "coverage_type": "attribute"
                }
            else:
                uncovered_items.append(attr.name)
                coverage_details[attr.name] = {
                    "covered": False,
                    "reason": "缺少属性测试用例"
                }
        
        return CoverageMapping(
            spec_id=spec.metadata.id,
            spec_name="属性覆盖率",
            total_requirements=total,
            covered_requirements=covered,
            coverage_percentage=round((covered / total * 100) if total > 0 else 0, 2),
            test_cases=[tc.id for tc in spec.test_cases if "Attribute" in tc.tags],
            uncovered_items=uncovered_items,
            coverage_details=coverage_details
        )
    
    def _analyze_endpoint_coverage(self, spec: SDDSpecification) -> CoverageMapping:
        total = len(spec.endpoints)
        covered = 0
        coverage_details = {}
        uncovered_items = []
        
        for endpoint in spec.endpoints:
            is_covered = any(
                endpoint.name in tc.coverage_items
                for tc in spec.test_cases
            )
            
            if is_covered:
                covered += 1
                covering_tests = [
                    tc.id for tc in spec.test_cases
                    if endpoint.name in tc.coverage_items
                ]
                coverage_details[endpoint.name] = {
                    "covered": True,
                    "test_cases": covering_tests,
                    "coverage_type": "endpoint"
                }
            else:
                uncovered_items.append(endpoint.name)
                coverage_details[endpoint.name] = {
                    "covered": False,
                    "reason": "缺少API测试用例"
                }
        
        return CoverageMapping(
            spec_id=spec.metadata.id,
            spec_name="接口覆盖率",
            total_requirements=total,
            covered_requirements=covered,
            coverage_percentage=round((covered / total * 100) if total > 0 else 0, 2),
            test_cases=[tc.id for tc in spec.test_cases if "API" in tc.tags],
            uncovered_items=uncovered_items,
            coverage_details=coverage_details
        )
    
    def _analyze_scenario_coverage(self, spec: SDDSpecification) -> CoverageMapping:
        total = len(spec.scenarios)
        covered = 0
        coverage_details = {}
        uncovered_items = []
        
        for scenario in spec.scenarios:
            is_covered = any(
                scenario.name in tc.coverage_items or tc.scenario_id == scenario.name
                for tc in spec.test_cases
            )
            
            if is_covered:
                covered += 1
                covering_tests = [
                    tc.id for tc in spec.test_cases
                    if scenario.name in tc.coverage_items or tc.scenario_id == scenario.name
                ]
                coverage_details[scenario.name] = {
                    "covered": True,
                    "test_cases": covering_tests,
                    "coverage_type": "scenario"
                }
            else:
                uncovered_items.append(scenario.name)
                coverage_details[scenario.name] = {
                    "covered": False,
                    "reason": "缺少场景测试用例"
                }
        
        return CoverageMapping(
            spec_id=spec.metadata.id,
            spec_name="场景覆盖率",
            total_requirements=total,
            covered_requirements=covered,
            coverage_percentage=round((covered / total * 100) if total > 0 else 0, 2),
            test_cases=[tc.id for tc in spec.test_cases if "positive" in tc.tags or "negative" in tc.tags],
            uncovered_items=uncovered_items,
            coverage_details=coverage_details
        )
    
    def _analyze_constraint_coverage(self, spec: SDDSpecification) -> CoverageMapping:
        total = len(spec.constraints)
        covered = 0
        coverage_details = {}
        uncovered_items = []
        
        for idx, constraint in enumerate(spec.constraints):
            constraint_name = constraint.get("name", f"constraint-{idx}")
            is_covered = any(
                constraint_name in tc.coverage_items
                for tc in spec.test_cases
            )
            
            if is_covered:
                covered += 1
                covering_tests = [
                    tc.id for tc in spec.test_cases
                    if constraint_name in tc.coverage_items
                ]
                coverage_details[constraint_name] = {
                    "covered": True,
                    "test_cases": covering_tests,
                    "coverage_type": "constraint"
                }
            else:
                uncovered_items.append(constraint_name)
                coverage_details[constraint_name] = {
                    "covered": False,
                    "reason": "缺少约束测试用例"
                }
        
        return CoverageMapping(
            spec_id=spec.metadata.id,
            spec_name="约束覆盖率",
            total_requirements=total,
            covered_requirements=covered,
            coverage_percentage=round((covered / total * 100) if total > 0 else 0, 2),
            test_cases=[tc.id for tc in spec.test_cases if "Constraint" in tc.tags],
            uncovered_items=uncovered_items,
            coverage_details=coverage_details
        )
    
    def _calculate_coverage_by_priority(self, test_cases: List[TestCase]) -> Dict[str, float]:
        priority_counts: Dict[str, int] = defaultdict(int)
        
        for tc in test_cases:
            priority_counts[tc.priority] += 1
        
        total = len(test_cases)
        if total == 0:
            return {}
        
        return {
            priority: round(count / total * 100, 2)
            for priority, count in priority_counts.items()
        }
    
    def _identify_missing_coverage(self, coverage_by_type: Dict[str, CoverageMapping]) -> List[Dict[str, Any]]:
        missing = []
        
        for type_name, mapping in coverage_by_type.items():
            for item_name in mapping.uncovered_items:
                missing.append({
                    "type": type_name,
                    "item": item_name,
                    "reason": mapping.coverage_details.get(item_name, {}).get("reason", "未覆盖"),
                    "priority": "high" if type_name in ["scenarios", "endpoints"] else "medium"
                })
        
        return missing
    
    def _generate_recommendations(self, coverage_by_type: Dict[str, CoverageMapping], overall: float) -> List[str]:
        recommendations = []
        
        if overall < 50:
            recommendations.append("覆盖率严重不足，建议优先补充核心功能的测试用例")
        elif overall < 80:
            recommendations.append("覆盖率有待提高，建议补充缺失的测试用例")
        else:
            recommendations.append("覆盖率良好，建议关注边界场景和异常处理")
        
        for type_name, mapping in coverage_by_type.items():
            if mapping.coverage_percentage < 50:
                recommendations.append(f"{mapping.spec_name}较低({mapping.coverage_percentage}%)，建议优先补充")
            
            if mapping.uncovered_items:
                recommendations.append(f"{type_name}未覆盖项: {', '.join(mapping.uncovered_items[:5])}")
        
        return recommendations


class CompletenessValidator:
    """规范完整性验证器"""
    
    REQUIRED_ENTITY_ELEMENTS = ["attributes"]
    REQUIRED_INTERFACE_ELEMENTS = ["endpoints"]
    REQUIRED_ACCEPTANCE_ELEMENTS = ["scenarios"]
    
    QUALITY_CHECKS = {
        "description_quality": {
            "min_length": 10,
            "message": "描述内容过短，建议补充详细说明"
        },
        "attribute_description": {
            "check": True,
            "message": "属性缺少描述说明"
        },
        "example_data": {
            "check": True,
            "message": "缺少示例数据"
        }
    }
    
    def validate_completeness(self, spec: SDDSpecification) -> CompletenessCheck:
        check_time = datetime.now().isoformat()
        missing_elements: Dict[str, List[str]] = defaultdict(list)
        quality_issues: List[Dict[str, Any]] = []
        suggestions: List[str] = []
        passed_checks: List[str] = []
        failed_checks: List[str] = []
        
        self._check_required_elements(spec, missing_elements, passed_checks, failed_checks)
        self._check_metadata_completeness(spec, missing_elements, passed_checks, failed_checks)
        self._check_spec_content_quality(spec, quality_issues, passed_checks, failed_checks)
        self._check_test_coverage_readiness(spec, missing_elements, suggestions)
        self._check_cross_references(spec, quality_issues, passed_checks, failed_checks)
        
        total_checks = len(passed_checks) + len(failed_checks)
        completeness_score = (len(passed_checks) / total_checks * 100) if total_checks > 0 else 0
        
        suggestions.extend(self._generate_completeness_suggestions(missing_elements, quality_issues))
        
        return CompletenessCheck(
            spec_id=spec.metadata.id,
            check_time=check_time,
            completeness_score=round(completeness_score, 2),
            missing_elements=dict(missing_elements),
            quality_issues=quality_issues,
            suggestions=suggestions,
            passed_checks=passed_checks,
            failed_checks=failed_checks
        )
    
    def _check_required_elements(
        self,
        spec: SDDSpecification,
        missing: Dict[str, List[str]],
        passed: List[str],
        failed: List[str]
    ):
        kind = spec.kind.value
        
        if kind == SpecType.ENTITY.value:
            if not spec.attributes:
                missing["entity"].append("attributes")
                failed.append("实体缺少属性定义")
            else:
                passed.append("实体属性定义完整")
        
        elif kind in [SpecType.INTERFACE.value, SpecType.API.value]:
            if not spec.endpoints:
                missing["interface"].append("endpoints")
                failed.append("接口缺少端点定义")
            else:
                passed.append("接口端点定义完整")
        
        elif kind == SpecType.ACCEPTANCE.value:
            if not spec.scenarios:
                missing["acceptance"].append("scenarios")
                failed.append("验收规范缺少场景定义")
            else:
                passed.append("验收场景定义完整")
        
        if not spec.spec.get("description"):
            missing["spec"].append("description")
            failed.append("规范缺少功能描述")
        else:
            passed.append("规范功能描述存在")
    
    def _check_metadata_completeness(
        self,
        spec: SDDSpecification,
        missing: Dict[str, List[str]],
        passed: List[str],
        failed: List[str]
    ):
        required_metadata = ["id", "name", "version"]
        
        for field_name in required_metadata:
            value = getattr(spec.metadata, field_name, None)
            if not value:
                missing["metadata"].append(field_name)
                failed.append(f"元数据缺少{field_name}")
            else:
                passed.append(f"元数据{field_name}存在")
        
        if not spec.metadata.author:
            missing["metadata"].append("author")
        
        if not spec.metadata.tags:
            missing["metadata"].append("tags")
    
    def _check_spec_content_quality(
        self,
        spec: SDDSpecification,
        issues: List[Dict[str, Any]],
        passed: List[str],
        failed: List[str]
    ):
        description = spec.spec.get("description", "")
        if len(description) < self.QUALITY_CHECKS["description_quality"]["min_length"]:
            issues.append({
                "type": "description_quality",
                "path": "spec.description",
                "message": self.QUALITY_CHECKS["description_quality"]["message"],
                "severity": "warning"
            })
            failed.append("描述质量检查未通过")
        else:
            passed.append("描述质量检查通过")
        
        attrs_without_desc = [attr for attr in spec.attributes if not attr.description]
        if attrs_without_desc:
            issues.append({
                "type": "attribute_description",
                "path": "spec.attributes",
                "message": f"{len(attrs_without_desc)}个属性缺少描述: {[a.name for a in attrs_without_desc[:5]]}",
                "severity": "warning"
            })
            failed.append("属性描述检查未通过")
        else:
            passed.append("属性描述检查通过")
        
        has_example = any(attr.example is not None for attr in spec.attributes)
        if spec.attributes and not has_example:
            issues.append({
                "type": "example_data",
                "path": "spec.attributes",
                "message": self.QUALITY_CHECKS["example_data"]["message"],
                "severity": "info"
            })
    
    def _check_test_coverage_readiness(
        self,
        spec: SDDSpecification,
        missing: Dict[str, List[str]],
        suggestions: List[str]
    ):
        if spec.scenarios:
            scenarios_without_data = [s for s in spec.scenarios if not s.test_data]
            if scenarios_without_data:
                missing["test_readiness"].append("test_data")
                suggestions.append(f"{len(scenarios_without_data)}个场景缺少测试数据")
        
        if spec.endpoints:
            endpoints_without_response = [e for e in spec.endpoints if not e.response]
            if endpoints_without_response:
                missing["test_readiness"].append("response_definition")
                suggestions.append(f"{len(endpoints_without_response)}个端点缺少响应定义")
    
    def _check_cross_references(
        self,
        spec: SDDSpecification,
        issues: List[Dict[str, Any]],
        passed: List[str],
        failed: List[str]
    ):
        unresolved_refs = [ref for ref in spec.references if not ref.resolved]
        
        if unresolved_refs:
            issues.append({
                "type": "unresolved_references",
                "path": "spec.references",
                "message": f"{len(unresolved_refs)}个引用未解析",
                "severity": "error",
                "details": [{"path": r.ref_path, "target": r.target_spec_id} for r in unresolved_refs]
            })
            failed.append("引用解析检查未通过")
        else:
            passed.append("引用解析检查通过")
        
        if spec.inheritance and spec.inheritance.parent_spec_id and not spec.inheritance.parent_spec:
            issues.append({
                "type": "unresolved_inheritance",
                "path": "spec.inheritance",
                "message": f"父规范未找到: {spec.inheritance.parent_spec_id}",
                "severity": "error"
            })
            failed.append("继承解析检查未通过")
        else:
            passed.append("继承解析检查通过")
    
    def _generate_completeness_suggestions(
        self,
        missing: Dict[str, List[str]],
        issues: List[Dict[str, Any]]
    ) -> List[str]:
        suggestions = []
        
        for category, items in missing.items():
            if items:
                suggestions.append(f"建议补充{category}中的: {', '.join(items)}")
        
        error_issues = [i for i in issues if i.get("severity") == "error"]
        if error_issues:
            suggestions.append(f"发现{len(error_issues)}个严重问题需要修复")
        
        warning_issues = [i for i in issues if i.get("severity") == "warning"]
        if warning_issues:
            suggestions.append(f"发现{len(warning_issues)}个警告建议处理")
        
        return suggestions


class SpecValidator:
    """规范验证器"""
    
    REQUIRED_METADATA_FIELDS = ["id", "name", "version"]
    VALID_SPEC_TYPES = [t.value for t in SpecType]
    VALID_DATA_TYPES = ["string", "integer", "bigint", "float", "boolean", "date", "datetime", "json", "array", "enum", "text"]
    VALID_HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
    
    def validate(self, spec: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        self._validate_api_version(spec, result)
        self._validate_kind(spec, result)
        self._validate_metadata(spec, result)
        self._validate_spec_content(spec, result)
        
        return result
    
    def _validate_api_version(self, spec: Dict[str, Any], result: ValidationResult):
        api_version = spec.get("apiVersion", "")
        if not api_version:
            result.add_error("apiVersion", "缺少apiVersion字段", "添加apiVersion: sdd/v1")
        elif not api_version.startswith("sdd/"):
            result.add_warning("apiVersion", f"非标准apiVersion: {api_version}", "建议使用sdd/v1格式")
    
    def _validate_kind(self, spec: Dict[str, Any], result: ValidationResult):
        kind = spec.get("kind", "")
        if not kind:
            result.add_error("kind", "缺少kind字段", f"添加kind字段，可选值: {', '.join(self.VALID_SPEC_TYPES)}")
        elif kind not in self.VALID_SPEC_TYPES:
            result.add_error("kind", f"无效的kind值: {kind}", f"可选值: {', '.join(self.VALID_SPEC_TYPES)}")
    
    def _validate_metadata(self, spec: Dict[str, Any], result: ValidationResult):
        metadata = spec.get("metadata", {})
        
        if not metadata:
            result.add_error("metadata", "缺少metadata字段", "添加metadata对象")
            return
        
        for field_name in self.REQUIRED_METADATA_FIELDS:
            if field_name not in metadata:
                result.add_error(f"metadata.{field_name}", f"缺少必填字段: {field_name}", f"添加{field_name}字段")
        
        if "version" in metadata:
            version = metadata["version"]
            if not re.match(r"^v?\d+\.\d+(\.\d+)?$", str(version)):
                result.add_warning("metadata.version", f"非标准版本号格式: {version}", "建议使用语义化版本号，如v1.0.0")
        
        if "status" in metadata:
            valid_statuses = ["draft", "review", "approved", "deprecated", "retired"]
            if metadata["status"] not in valid_statuses:
                result.add_warning("metadata.status", f"非标准状态值: {metadata['status']}", f"建议使用: {', '.join(valid_statuses)}")
    
    def _validate_spec_content(self, spec: Dict[str, Any], result: ValidationResult):
        spec_content = spec.get("spec", {})
        
        if not spec_content:
            result.add_error("spec", "缺少spec字段", "添加spec对象定义规范内容")
            return
        
        kind = spec.get("kind", "")
        
        if kind == SpecType.ENTITY.value:
            self._validate_entity_spec(spec_content, result)
        elif kind == SpecType.INTERFACE.value or kind == SpecType.API.value:
            self._validate_interface_spec(spec_content, result)
        elif kind == SpecType.ACCEPTANCE.value:
            self._validate_acceptance_spec(spec_content, result)
    
    def _validate_entity_spec(self, spec_content: Dict[str, Any], result: ValidationResult):
        attributes = spec_content.get("attributes", [])
        
        if not attributes:
            result.add_warning("spec.attributes", "实体规范缺少属性定义", "添加attributes数组定义实体属性")
            return
        
        for idx, attr in enumerate(attributes):
            path = f"spec.attributes[{idx}]"
            
            if "name" not in attr:
                result.add_error(f"{path}.name", f"属性{idx}缺少name字段")
            
            if "type" in attr:
                attr_type = attr["type"]
                if attr_type not in self.VALID_DATA_TYPES:
                    result.add_warning(f"{path}.type", f"非标准数据类型: {attr_type}", f"建议使用: {', '.join(self.VALID_DATA_TYPES)}")
            
            if attr.get("type") == "enum":
                if not attr.get("enumValues"):
                    result.add_error(f"{path}.enumValues", "枚举类型缺少enumValues定义")
    
    def _validate_interface_spec(self, spec_content: Dict[str, Any], result: ValidationResult):
        endpoints = spec_content.get("endpoints", [])
        
        if not endpoints:
            result.add_warning("spec.endpoints", "接口规范缺少端点定义", "添加endpoints数组定义API端点")
            return
        
        for idx, ep in enumerate(endpoints):
            path = f"spec.endpoints[{idx}]"
            
            if "name" not in ep:
                result.add_error(f"{path}.name", f"端点{idx}缺少name字段")
            
            if "method" in ep:
                method = ep["method"].upper()
                if method not in self.VALID_HTTP_METHODS:
                    result.add_error(f"{path}.method", f"无效的HTTP方法: {method}", f"可选值: {', '.join(self.VALID_HTTP_METHODS)}")
            
            if "path" in ep:
                path_val = ep["path"]
                if not path_val.startswith("/"):
                    result.add_warning(f"{path}.path", f"路径应以/开头: {path_val}")
    
    def _validate_acceptance_spec(self, spec_content: Dict[str, Any], result: ValidationResult):
        scenarios = spec_content.get("scenarios", [])
        
        if not scenarios:
            result.add_warning("spec.scenarios", "验收规范缺少场景定义", "添加scenarios数组定义测试场景")
            return
        
        for idx, scenario in enumerate(scenarios):
            path = f"spec.scenarios[{idx}]"
            
            if "name" not in scenario:
                result.add_error(f"{path}.name", f"场景{idx}缺少name字段")
            
            if not scenario.get("given") and not scenario.get("when") and not scenario.get("then"):
                result.add_warning(f"{path}", f"场景{idx}缺少Given/When/Then定义")


class SDDSpecParserEnhanced:
    """SDD规范解析器增强版"""
    
    def __init__(self):
        self.parsers = {
            SpecFormat.MARKDOWN: MarkdownSpecParser(),
            SpecFormat.YAML: YAMLSpecParser(),
            SpecFormat.JSON: JSONSpecParser(),
        }
        self.validator = SpecValidator()
        self.complex_parser = ComplexSpecParser()
        self.test_generator = TestCaseGenerator()
        self.coverage_analyzer = CoverageAnalyzer()
        self.completeness_validator = CompletenessValidator()
        self.spec_registry: Dict[str, SDDSpecification] = {}
    
    def parse_file(self, file_path: str) -> Tuple[SDDSpecification, ValidationResult]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"规范文件不存在: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        source_format = self._detect_format(path)
        return self.parse_content(content, source_format, str(path))
    
    def parse_content(
        self,
        content: str,
        source_format: SpecFormat,
        source_path: str = ""
    ) -> Tuple[SDDSpecification, ValidationResult]:
        parser = self.parsers.get(source_format)
        if not parser:
            raise ValueError(f"不支持的格式: {source_format}")
        
        parsed = parser.parse(content)
        validation_result = self.validator.validate(parsed)
        
        spec = self._build_spec(parsed, content, source_format, source_path)
        
        spec = self._process_complex_features(spec)
        
        spec.test_cases = self.test_generator.generate_test_cases(spec)
        
        spec.coverage_report = self.coverage_analyzer.analyze_coverage(spec)
        
        spec.completeness_check = self.completeness_validator.validate_completeness(spec)
        
        self.spec_registry[spec.metadata.id] = spec
        
        return spec, validation_result
    
    def _detect_format(self, path: Path) -> SpecFormat:
        suffix = path.suffix.lower()
        if suffix in [".yaml", ".yml"]:
            return SpecFormat.YAML
        elif suffix == ".json":
            return SpecFormat.JSON
        elif suffix == ".md":
            return SpecFormat.MARKDOWN
        else:
            raise ValueError(f"无法识别的文件格式: {suffix}")
    
    def _build_spec(
        self,
        parsed: Dict[str, Any],
        raw_content: str,
        source_format: SpecFormat,
        source_path: str
    ) -> SDDSpecification:
        metadata_dict = parsed.get("metadata", {})
        metadata = SpecMetadata(
            id=metadata_dict.get("id", f"SPC-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            name=metadata_dict.get("name", "未命名规范"),
            version=metadata_dict.get("version", "v1.0"),
            namespace=metadata_dict.get("namespace", "default"),
            status=metadata_dict.get("status", "draft"),
            author=metadata_dict.get("author", ""),
            created=metadata_dict.get("created", ""),
            modified=metadata_dict.get("modified", ""),
            tags=metadata_dict.get("tags", []),
            annotations=metadata_dict.get("annotations", {}),
        )
        
        try:
            kind = SpecType(parsed.get("kind", SpecType.FUNCTION.value))
        except ValueError:
            kind = SpecType.FUNCTION
        
        spec = SDDSpecification(
            api_version=parsed.get("apiVersion", "sdd/v1"),
            kind=kind,
            metadata=metadata,
            spec=parsed.get("spec", {}),
            raw_content=raw_content,
            source_format=source_format,
            source_path=source_path,
        )
        
        spec_content = parsed.get("spec", {})
        spec.attributes = self._parse_attributes(spec_content)
        spec.endpoints = self._parse_endpoints(spec_content)
        spec.scenarios = self._parse_scenarios(spec_content)
        spec.constraints = spec_content.get("constraints", [])
        spec.relationships = spec_content.get("relationships", [])
        
        return spec
    
    def _process_complex_features(self, spec: SDDSpecification) -> SDDSpecification:
        spec.nested_attributes = self._parse_nested_attributes(spec.spec)
        
        spec = self.complex_parser.resolve_all_references(spec)
        
        spec = self.complex_parser.process_inheritance(spec, self.spec_registry)
        
        return spec
    
    def _parse_nested_attributes(self, spec_content: Dict[str, Any]) -> List[NestedAttribute]:
        nested_attrs = []
        
        for attr_dict in spec_content.get("attributes", []):
            if "attributes" in attr_dict or "properties" in attr_dict:
                nested = self.complex_parser.parse_nested_attributes(attr_dict)
                nested_attrs.append(nested)
        
        return nested_attrs
    
    def _parse_attributes(self, spec_content: Dict[str, Any]) -> List[SpecAttribute]:
        attributes = []
        for attr_dict in spec_content.get("attributes", []):
            attr = SpecAttribute(
                name=attr_dict.get("name", ""),
                type=attr_dict.get("type", "string"),
                description=attr_dict.get("description", ""),
                required=attr_dict.get("required", True),
                unique=attr_dict.get("unique", False),
                default=attr_dict.get("defaultValue") or attr_dict.get("default"),
                constraints=attr_dict.get("validation", {}) or attr_dict.get("constraints", {}),
                enum_values=attr_dict.get("enumValues", []),
                example=attr_dict.get("example"),
            )
            attributes.append(attr)
        return attributes
    
    def _parse_endpoints(self, spec_content: Dict[str, Any]) -> List[SpecEndpoint]:
        endpoints = []
        for ep_dict in spec_content.get("endpoints", []):
            ep = SpecEndpoint(
                name=ep_dict.get("name", ""),
                method=ep_dict.get("method", "GET"),
                path=ep_dict.get("path", "/"),
                description=ep_dict.get("description", ""),
                parameters=ep_dict.get("parameters", []),
                request_body=ep_dict.get("request", {}).get("body") or ep_dict.get("requestBody"),
                response=ep_dict.get("response", {}).get("body") or ep_dict.get("responseBody"),
                errors=ep_dict.get("errors", []),
                authentication=ep_dict.get("authentication", False),
                rate_limit=ep_dict.get("rateLimit"),
            )
            endpoints.append(ep)
        return endpoints
    
    def _parse_scenarios(self, spec_content: Dict[str, Any]) -> List[SpecScenario]:
        scenarios = []
        for scenario_dict in spec_content.get("scenarios", []):
            scenario = SpecScenario(
                name=scenario_dict.get("name", ""),
                given=scenario_dict.get("given", ""),
                when=scenario_dict.get("when", ""),
                then=scenario_dict.get("then", ""),
                test_data=scenario_dict.get("testData", {}) or scenario_dict.get("test_data", {}),
            )
            scenarios.append(scenario)
        return scenarios
    
    def convert_format(
        self,
        spec: SDDSpecification,
        target_format: SpecFormat
    ) -> str:
        parser = self.parsers.get(target_format)
        if not parser:
            raise ValueError(f"不支持的目标格式: {target_format}")
        
        spec_dict = {
            "apiVersion": spec.api_version,
            "kind": spec.kind.value,
            "metadata": {
                "id": spec.metadata.id,
                "name": spec.metadata.name,
                "version": spec.metadata.version,
                "namespace": spec.metadata.namespace,
                "status": spec.metadata.status,
                "author": spec.metadata.author,
                "created": spec.metadata.created,
                "modified": spec.metadata.modified,
                "tags": spec.metadata.tags,
                "annotations": spec.metadata.annotations,
            },
            "spec": spec.spec,
        }
        
        return parser.serialize(spec_dict)
    
    def validate_spec(self, spec: SDDSpecification) -> ValidationResult:
        spec_dict = {
            "apiVersion": spec.api_version,
            "kind": spec.kind.value,
            "metadata": {
                "id": spec.metadata.id,
                "name": spec.metadata.name,
                "version": spec.metadata.version,
                "namespace": spec.metadata.namespace,
                "status": spec.metadata.status,
                "author": spec.metadata.author,
                "tags": spec.metadata.tags,
                "annotations": spec.metadata.annotations,
            },
            "spec": spec.spec,
        }
        return self.validator.validate(spec_dict)
    
    def generate_test_cases(self, spec: SDDSpecification) -> List[TestCase]:
        return self.test_generator.generate_test_cases(spec)
    
    def analyze_coverage(self, spec: SDDSpecification) -> CoverageReport:
        return self.coverage_analyzer.analyze_coverage(spec)
    
    def validate_completeness(self, spec: SDDSpecification) -> CompletenessCheck:
        return self.completeness_validator.validate_completeness(spec)
    
    def export_test_cases(self, spec: SDDSpecification, format: str = "json") -> str:
        test_cases_data = []
        for tc in spec.test_cases:
            tc_dict = {
                "id": tc.id,
                "name": tc.name,
                "description": tc.description,
                "scenario_id": tc.scenario_id,
                "test_type": tc.test_type,
                "priority": tc.priority,
                "preconditions": tc.preconditions,
                "test_steps": tc.test_steps,
                "expected_results": tc.expected_results,
                "test_data": tc.test_data,
                "tags": tc.tags,
                "coverage_items": tc.coverage_items
            }
            test_cases_data.append(tc_dict)
        
        if format == "json":
            return json.dumps(test_cases_data, ensure_ascii=False, indent=2)
        elif format == "yaml":
            return yaml.dump(test_cases_data, allow_unicode=True, default_flow_style=False)
        else:
            return self._export_test_cases_markdown(test_cases_data)
    
    def _export_test_cases_markdown(self, test_cases: List[Dict[str, Any]]) -> str:
        lines = ["# 测试用例列表\n"]
        
        for tc in test_cases:
            lines.append(f"## {tc['id']}: {tc['name']}\n")
            lines.append(f"- **类型**: {tc['test_type']}")
            lines.append(f"- **优先级**: {tc['priority']}")
            lines.append(f"- **描述**: {tc['description']}\n")
            
            if tc['preconditions']:
                lines.append("### 前置条件")
                for pre in tc['preconditions']:
                    lines.append(f"- {pre}")
                lines.append("")
            
            if tc['test_steps']:
                lines.append("### 测试步骤")
                for idx, step in enumerate(tc['test_steps'], 1):
                    lines.append(f"{idx}. **{step['step']}**: {step['action']}")
                    lines.append(f"   - 预期: {step['expected']}")
                lines.append("")
            
            if tc['expected_results']:
                lines.append("### 预期结果")
                for result in tc['expected_results']:
                    lines.append(f"- {result}")
                lines.append("")
            
            lines.append("---\n")
        
        return "\n".join(lines)
    
    def export_coverage_report(self, spec: SDDSpecification, format: str = "json") -> str:
        if not spec.coverage_report:
            spec.coverage_report = self.coverage_analyzer.analyze_coverage(spec)
        
        report = spec.coverage_report
        
        report_dict = {
            "report_id": report.report_id,
            "generated_at": report.generated_at,
            "spec_id": report.spec_id,
            "overall_coverage": report.overall_coverage,
            "coverage_by_type": {},
            "coverage_by_priority": report.coverage_by_priority,
            "missing_coverage": report.missing_coverage,
            "recommendations": report.recommendations
        }
        
        for type_name, mapping in report.coverage_by_type.items():
            report_dict["coverage_by_type"][type_name] = {
                "spec_name": mapping.spec_name,
                "total_requirements": mapping.total_requirements,
                "covered_requirements": mapping.covered_requirements,
                "coverage_percentage": mapping.coverage_percentage,
                "test_cases": mapping.test_cases,
                "uncovered_items": mapping.uncovered_items
            }
        
        if format == "json":
            return json.dumps(report_dict, ensure_ascii=False, indent=2)
        elif format == "yaml":
            return yaml.dump(report_dict, allow_unicode=True, default_flow_style=False)
        else:
            return self._export_coverage_markdown(report)
    
    def _export_coverage_markdown(self, report: CoverageReport) -> str:
        lines = [
            f"# 测试覆盖率报告\n",
            f"- **报告ID**: {report.report_id}",
            f"- **生成时间**: {report.generated_at}",
            f"- **规范ID**: {report.spec_id}",
            f"- **总体覆盖率**: {report.overall_coverage}%\n",
            "## 各类型覆盖率\n"
        ]
        
        for type_name, mapping in report.coverage_by_type.items():
            lines.append(f"### {mapping.spec_name}")
            lines.append(f"- 总需求: {mapping.total_requirements}")
            lines.append(f"- 已覆盖: {mapping.covered_requirements}")
            lines.append(f"- 覆盖率: {mapping.coverage_percentage}%")
            if mapping.uncovered_items:
                lines.append(f"- 未覆盖项: {', '.join(mapping.uncovered_items)}")
            lines.append("")
        
        if report.missing_coverage:
            lines.append("## 缺失覆盖\n")
            for item in report.missing_coverage:
                lines.append(f"- [{item['priority']}] {item['type']}: {item['item']} - {item['reason']}")
            lines.append("")
        
        if report.recommendations:
            lines.append("## 建议\n")
            for rec in report.recommendations:
                lines.append(f"- {rec}")
        
        return "\n".join(lines)
    
    def export_completeness_report(self, spec: SDDSpecification, format: str = "json") -> str:
        if not spec.completeness_check:
            spec.completeness_check = self.completeness_validator.validate_completeness(spec)
        
        check = spec.completeness_check
        
        check_dict = {
            "spec_id": check.spec_id,
            "check_time": check.check_time,
            "completeness_score": check.completeness_score,
            "missing_elements": check.missing_elements,
            "quality_issues": check.quality_issues,
            "suggestions": check.suggestions,
            "passed_checks": check.passed_checks,
            "failed_checks": check.failed_checks
        }
        
        if format == "json":
            return json.dumps(check_dict, ensure_ascii=False, indent=2)
        elif format == "yaml":
            return yaml.dump(check_dict, allow_unicode=True, default_flow_style=False)
        else:
            return self._export_completeness_markdown(check)
    
    def _export_completeness_markdown(self, check: CompletenessCheck) -> str:
        lines = [
            f"# 规范完整性检查报告\n",
            f"- **规范ID**: {check.spec_id}",
            f"- **检查时间**: {check.check_time}",
            f"- **完整性得分**: {check.completeness_score}%\n"
        ]
        
        if check.passed_checks:
            lines.append(f"## 通过检查 ({len(check.passed_checks)})\n")
            for item in check.passed_checks:
                lines.append(f"- ✅ {item}")
            lines.append("")
        
        if check.failed_checks:
            lines.append(f"## 未通过检查 ({len(check.failed_checks)})\n")
            for item in check.failed_checks:
                lines.append(f"- ❌ {item}")
            lines.append("")
        
        if check.missing_elements:
            lines.append("## 缺失元素\n")
            for category, items in check.missing_elements.items():
                if items:
                    lines.append(f"- **{category}**: {', '.join(items)}")
            lines.append("")
        
        if check.quality_issues:
            lines.append("## 质量问题\n")
            for issue in check.quality_issues:
                severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(issue.get("severity", "info"), "⚪")
                lines.append(f"- {severity_icon} [{issue['type']}] {issue['message']}")
                if "path" in issue:
                    lines.append(f"  - 路径: {issue['path']}")
            lines.append("")
        
        if check.suggestions:
            lines.append("## 改进建议\n")
            for suggestion in check.suggestions:
                lines.append(f"- 💡 {suggestion}")
        
        return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="SDD规范解析器增强版")
    parser.add_argument("spec_file", help="规范文件路径")
    parser.add_argument("--validate", action="store_true", help="验证规范")
    parser.add_argument("--convert", choices=["yaml", "json", "markdown"], help="转换格式")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--generate-tests", action="store_true", help="生成测试用例")
    parser.add_argument("--coverage", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--completeness", action="store_true", help="检查规范完整性")
    parser.add_argument("--export-format", choices=["json", "yaml", "markdown"], default="json", help="导出格式")
    parser.add_argument("--all", action="store_true", help="执行所有分析和导出")
    
    args = parser.parse_args()
    
    spec_parser = SDDSpecParserEnhanced()
    
    try:
        spec, validation_result = spec_parser.parse_file(args.spec_file)
        
        print(f"规范解析成功:")
        print(f"  ID: {spec.metadata.id}")
        print(f"  名称: {spec.metadata.name}")
        print(f"  版本: {spec.metadata.version}")
        print(f"  类型: {spec.kind.value}")
        print(f"  属性数量: {len(spec.attributes)}")
        print(f"  端点数量: {len(spec.endpoints)}")
        print(f"  场景数量: {len(spec.scenarios)}")
        print(f"  嵌套属性数量: {len(spec.nested_attributes)}")
        print(f"  引用数量: {len(spec.references)}")
        print(f"  测试用例数量: {len(spec.test_cases)}")
        
        if args.validate or validation_result.errors or validation_result.warnings:
            print(f"\n验证结果:")
            print(f"  有效: {validation_result.is_valid}")
            
            if validation_result.errors:
                print(f"\n  错误 ({len(validation_result.errors)}):")
                for err in validation_result.errors:
                    print(f"    - [{err.path}] {err.message}")
                    if err.suggestion:
                        print(f"      建议: {err.suggestion}")
            
            if validation_result.warnings:
                print(f"\n  警告 ({len(validation_result.warnings)}):")
                for warn in validation_result.warnings:
                    print(f"    - [{warn.path}] {warn.message}")
        
        if args.completeness or args.all:
            print(f"\n完整性检查:")
            if spec.completeness_check:
                check = spec.completeness_check
                print(f"  完整性得分: {check.completeness_score}%")
                print(f"  通过检查: {len(check.passed_checks)}")
                print(f"  未通过检查: {len(check.failed_checks)}")
                print(f"  质量问题: {len(check.quality_issues)}")
                
                if check.suggestions:
                    print(f"\n  改进建议:")
                    for suggestion in check.suggestions[:5]:
                        print(f"    - {suggestion}")
        
        if args.coverage or args.all:
            print(f"\n覆盖率分析:")
            if spec.coverage_report:
                report = spec.coverage_report
                print(f"  总体覆盖率: {report.overall_coverage}%")
                
                for type_name, mapping in report.coverage_by_type.items():
                    print(f"  {mapping.spec_name}: {mapping.coverage_percentage}% ({mapping.covered_requirements}/{mapping.total_requirements})")
                
                if report.missing_coverage:
                    print(f"\n  缺失覆盖 ({len(report.missing_coverage)}项):")
                    for item in report.missing_coverage[:5]:
                        print(f"    - [{item['priority']}] {item['type']}: {item['item']}")
        
        if args.generate_tests or args.all:
            print(f"\n测试用例生成:")
            print(f"  总数: {len(spec.test_cases)}")
            
            type_counts = {}
            for tc in spec.test_cases:
                type_counts[tc.test_type] = type_counts.get(tc.test_type, 0) + 1
            
            for test_type, count in type_counts.items():
                print(f"  {test_type}: {count}")
        
        if args.convert:
            format_map = {
                "yaml": SpecFormat.YAML,
                "json": SpecFormat.JSON,
                "markdown": SpecFormat.MARKDOWN,
            }
            target_format = format_map[args.convert]
            converted = spec_parser.convert_format(spec, target_format)
            
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(converted)
                print(f"\n已转换并保存到: {args.output}")
            else:
                print(f"\n转换结果 ({args.convert}):")
                print(converted)
        
        if args.generate_tests and args.output:
            test_output = spec_parser.export_test_cases(spec, args.export_format)
            output_path = args.output.replace(".", "_tests.") if "." in args.output else f"{args.output}_tests"
            if args.export_format != "markdown":
                output_path = f"{output_path}.{args.export_format}"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(test_output)
            print(f"\n测试用例已导出到: {output_path}")
        
        if args.coverage and args.output:
            coverage_output = spec_parser.export_coverage_report(spec, args.export_format)
            output_path = args.output.replace(".", "_coverage.") if "." in args.output else f"{args.output}_coverage"
            if args.export_format != "markdown":
                output_path = f"{output_path}.{args.export_format}"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(coverage_output)
            print(f"\n覆盖率报告已导出到: {output_path}")
        
        if args.completeness and args.output:
            completeness_output = spec_parser.export_completeness_report(spec, args.export_format)
            output_path = args.output.replace(".", "_completeness.") if "." in args.output else f"{args.output}_completeness"
            if args.export_format != "markdown":
                output_path = f"{output_path}.{args.export_format}"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(completeness_output)
            print(f"\n完整性报告已导出到: {output_path}")
    
    except FileNotFoundError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"解析错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
