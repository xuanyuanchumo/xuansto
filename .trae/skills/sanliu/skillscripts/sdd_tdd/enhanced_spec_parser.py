#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的SDD规范解析器

支持更丰富的规范语法定义，包括：
1. 多格式规范解析（YAML、JSON、Markdown、DSL）
2. 规范语义验证
3. 规范引用和继承
4. 规范元数据提取
5. 规范扩展机制
"""

import json
import re
import yaml
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class SpecFormat(Enum):
    YAML = "yaml"
    JSON = "json"
    MARKDOWN = "markdown"
    DSL = "dsl"
    GHERKIN = "gherkin"
    OPENAPI = "openapi"


class SpecType(Enum):
    ENTITY = "EntitySpec"
    INTERFACE = "InterfaceSpec"
    API = "ApiSpec"
    BUSINESS_RULE = "BusinessRuleSpec"
    CONSTRAINT = "ConstraintSpec"
    ACCEPTANCE = "AcceptanceSpec"
    FUNCTION = "FunctionSpec"
    SERVICE = "ServiceSpec"
    MODULE = "ModuleSpec"


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
    line_number: Optional[int] = None


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    
    def add_error(self, path: str, message: str, suggestion: str = "", line_number: Optional[int] = None):
        self.errors.append(ValidationError(path, message, ValidationSeverity.ERROR, suggestion, line_number))
        self.is_valid = False
    
    def add_warning(self, path: str, message: str, suggestion: str = "", line_number: Optional[int] = None):
        self.warnings.append(ValidationError(path, message, ValidationSeverity.WARNING, suggestion, line_number))


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
    dependencies: List[str] = field(default_factory=list)


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
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    nested_attributes: List['SpecAttribute'] = field(default_factory=list)


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
    timeout: Optional[int] = None
    middleware: List[str] = field(default_factory=list)


@dataclass
class SpecScenario:
    name: str
    given: str
    when: str
    then: str
    test_data: Dict[str, Any] = field(default_factory=dict)
    priority: str = "medium"
    tags: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)


@dataclass
class SpecConstraint:
    name: str
    type: str
    description: str = ""
    rule: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    severity: str = "error"


@dataclass
class SpecConditionalBranch:
    condition: str
    description: str = ""
    actions: List[str] = field(default_factory=list)
    else_branch: Optional['SpecConditionalBranch'] = None
    nested_conditions: List['SpecConditionalBranch'] = field(default_factory=list)


@dataclass
class SpecExceptionHandler:
    exception_type: str
    description: str = ""
    error_code: str = ""
    http_status: int = 500
    message: str = ""
    recovery_action: str = ""
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    fallback_behavior: str = ""


@dataclass
class SpecPerformanceConstraint:
    name: str
    metric: str
    threshold: float
    unit: str = "ms"
    description: str = ""
    priority: str = "medium"
    conditions: List[str] = field(default_factory=list)
    measurement_method: str = "average"
    sample_size: int = 100
    percentiles: List[float] = field(default_factory=list)


@dataclass
class SpecSecurityConstraint:
    name: str
    type: str
    description: str = ""
    authentication_required: bool = False
    authorization_roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    rate_limit: Optional[int] = None
    rate_limit_window: int = 60
    encryption_required: bool = False
    encryption_algorithm: str = ""
    data_classification: str = "public"
    audit_logging: bool = True
    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)


@dataclass
class SpecBusinessRule:
    id: str
    name: str
    description: str = ""
    condition: str = ""
    action: str = ""
    priority: int = 1
    enabled: bool = True
    tags: List[str] = field(default_factory=list)


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
    constraints: List[SpecConstraint] = field(default_factory=list)
    business_rules: List[SpecBusinessRule] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    
    conditional_branches: List[SpecConditionalBranch] = field(default_factory=list)
    exception_handlers: List[SpecExceptionHandler] = field(default_factory=list)
    performance_constraints: List[SpecPerformanceConstraint] = field(default_factory=list)
    security_constraints: List[SpecSecurityConstraint] = field(default_factory=list)
    
    references: List[SpecReference] = field(default_factory=list)
    inheritance: Optional[SpecInheritance] = None
    imported_specs: Dict[str, 'SDDSpecification'] = field(default_factory=dict)
    
    extensions: Dict[str, Any] = field(default_factory=dict)
    custom_fields: Dict[str, Any] = field(default_factory=dict)


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
        elif "服务" in content or "service" in content.lower():
            return SpecType.SERVICE.value
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
        spec["businessRules"] = self._extract_business_rules(content)
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
    
    def _extract_business_rules(self, content: str) -> List[Dict[str, Any]]:
        rules = []
        
        rule_pattern = r"##\s*业务规则\s*\n((?:\s*[-*]\s*.+\n?)+)"
        for match in re.finditer(rule_pattern, content):
            lines = match.group(1).strip().split("\n")
            for idx, line in enumerate(lines, 1):
                line = line.strip("- *").strip()
                if not line:
                    continue
                
                rule = {}
                rule["id"] = f"BR-{idx:03d}"
                if ":" in line:
                    parts = line.split(":", 1)
                    rule["name"] = parts[0].strip()
                    rule["description"] = parts[1].strip() if len(parts) > 1 else ""
                else:
                    rule["name"] = line
                    rule["description"] = ""
                
                rules.append(rule)
        
        return rules
    
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


class DSLSpecParser(BaseSpecParser):
    """DSL格式规范解析器（自定义领域特定语言）"""
    
    def get_format(self) -> SpecFormat:
        return SpecFormat.DSL
    
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
        lines.append(f"spec {metadata.get('name', 'unnamed')} {{")
        lines.append(f"  id: {metadata.get('id', 'UNKNOWN')}")
        lines.append(f"  version: {metadata.get('version', 'v1.0')}")
        lines.append("")
        
        spec_content = spec.get("spec", {})
        
        if "description" in spec_content:
            lines.append(f"  description: {spec_content['description']}")
            lines.append("")
        
        if "attributes" in spec_content:
            lines.append("  attributes {")
            for attr in spec_content["attributes"]:
                required = "required" if attr.get("required", True) else "optional"
                lines.append(f"    {attr['name']}: {attr.get('type', 'string')} ({required})")
            lines.append("  }")
            lines.append("")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _detect_kind(self, content: str) -> str:
        if "endpoint" in content or "api" in content:
            return SpecType.API.value
        elif "entity" in content:
            return SpecType.ENTITY.value
        elif "service" in content:
            return SpecType.SERVICE.value
        else:
            return SpecType.FUNCTION.value
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        metadata = {}
        
        spec_match = re.search(r"spec\s+(\w+)\s*\{", content)
        metadata["name"] = spec_match.group(1) if spec_match else "unnamed"
        
        id_match = re.search(r"id:\s*(\S+)", content)
        metadata["id"] = id_match.group(1) if id_match else f"SPC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        version_match = re.search(r"version:\s*(\S+)", content)
        metadata["version"] = version_match.group(1) if version_match else "v1.0"
        
        return metadata
    
    def _extract_spec(self, content: str) -> Dict[str, Any]:
        spec = {}
        
        desc_match = re.search(r"description:\s*(.+)$", content, re.MULTILINE)
        if desc_match:
            spec["description"] = desc_match.group(1).strip()
        
        spec["attributes"] = self._extract_attributes(content)
        
        return spec
    
    def _extract_attributes(self, content: str) -> List[Dict[str, Any]]:
        attributes = []
        
        attr_pattern = r"attributes\s*\{([^}]+)\}"
        match = re.search(attr_pattern, content, re.DOTALL)
        
        if match:
            attr_content = match.group(1)
            attr_lines = [line.strip() for line in attr_content.split("\n") if line.strip()]
            
            for line in attr_lines:
                if ":" in line:
                    parts = line.split(":")
                    name = parts[0].strip()
                    type_info = parts[1].strip() if len(parts) > 1 else "string"
                    
                    attr = {
                        "name": name,
                        "type": type_info.split("(")[0].strip(),
                        "required": "required" in type_info
                    }
                    attributes.append(attr)
        
        return attributes


class GherkinSpecParser(BaseSpecParser):
    """Gherkin风格规范解析器（BDD场景测试）"""
    
    def get_format(self) -> SpecFormat:
        return SpecFormat.GHERKIN
    
    def parse(self, content: str) -> Dict[str, Any]:
        spec = {
            "apiVersion": "sdd/v1",
            "kind": SpecType.ACCEPTANCE.value,
            "metadata": self._extract_metadata(content),
            "spec": self._extract_spec(content)
        }
        return spec
    
    def serialize(self, spec: Dict[str, Any]) -> str:
        lines = []
        
        metadata = spec.get("metadata", {})
        lines.append(f"Feature: {metadata.get('name', '未命名功能')}")
        lines.append(f"  规范ID: {metadata.get('id', 'UNKNOWN')}")
        lines.append(f"  版本: {metadata.get('version', 'v1.0')}")
        lines.append("")
        
        spec_content = spec.get("spec", {})
        
        if "description" in spec_content:
            lines.append(f"  {spec_content['description']}")
            lines.append("")
        
        for scenario in spec_content.get("scenarios", []):
            lines.append(f"  Scenario: {scenario.get('name', '未命名场景')}")
            
            if scenario.get("given"):
                lines.append(f"    Given {scenario['given']}")
            if scenario.get("when"):
                lines.append(f"    When {scenario['when']}")
            if scenario.get("then"):
                lines.append(f"    Then {scenario['then']}")
            
            for example in scenario.get("examples", []):
                lines.append(f"    And {example}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        metadata = {}
        
        feature_match = re.search(r"Feature:\s*(.+)$", content, re.MULTILINE)
        metadata["name"] = feature_match.group(1).strip() if feature_match else "未命名功能"
        
        id_match = re.search(r"规范ID[：:]\s*(\S+)", content)
        metadata["id"] = id_match.group(1) if id_match else f"SPC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        version_match = re.search(r"版本[：:]\s*(\S+)", content)
        metadata["version"] = version_match.group(1) if version_match else "v1.0"
        
        return metadata
    
    def _extract_spec(self, content: str) -> Dict[str, Any]:
        spec = {}
        
        lines = content.split("\n")
        description_lines = []
        for line in lines[1:]:
            line = line.strip()
            if line.startswith("Scenario:") or line.startswith("规则ID") or line.startswith("版本"):
                break
            if line and not line.startswith("规范ID"):
                description_lines.append(line)
        
        if description_lines:
            spec["description"] = " ".join(description_lines)
        
        spec["scenarios"] = self._extract_scenarios(content)
        spec["background"] = self._extract_background(content)
        spec["rules"] = self._extract_rules(content)
        
        return spec
    
    def _extract_scenarios(self, content: str) -> List[Dict[str, Any]]:
        scenarios = []
        
        scenario_pattern = r"Scenario(?:\s+Outline)?:\s*(.+?)\n((?:(?:Given|When|Then|And|But)\s+.+\n?)+)"
        
        for match in re.finditer(scenario_pattern, content, re.MULTILINE):
            scenario = {
                "name": match.group(1).strip(),
                "given": "",
                "when": "",
                "then": "",
                "examples": []
            }
            
            scenario_content = match.group(2)
            
            given_match = re.search(r"Given\s+(.+)$", scenario_content, re.MULTILINE)
            if given_match:
                scenario["given"] = given_match.group(1).strip()
            
            when_match = re.search(r"When\s+(.+)$", scenario_content, re.MULTILINE)
            if when_match:
                scenario["when"] = when_match.group(1).strip()
            
            then_match = re.search(r"Then\s+(.+)$", scenario_content, re.MULTILINE)
            if then_match:
                scenario["then"] = then_match.group(1).strip()
            
            and_matches = re.findall(r"And\s+(.+)$", scenario_content, re.MULTILINE)
            scenario["examples"] = [m.strip() for m in and_matches]
            
            scenarios.append(scenario)
        
        return scenarios
    
    def _extract_background(self, content: str) -> Dict[str, Any]:
        background = {}
        
        bg_pattern = r"Background:\s*\n((?:(?:Given|When|Then|And|But)\s+.+\n?)+)"
        match = re.search(bg_pattern, content)
        
        if match:
            bg_content = match.group(1)
            
            given_match = re.search(r"Given\s+(.+)$", bg_content, re.MULTILINE)
            if given_match:
                background["given"] = given_match.group(1).strip()
            
            when_match = re.search(r"When\s+(.+)$", bg_content, re.MULTILINE)
            if when_match:
                background["when"] = when_match.group(1).strip()
        
        return background
    
    def _extract_rules(self, content: str) -> List[Dict[str, Any]]:
        rules = []
        
        rule_pattern = r"Rule:\s*(.+?)\n((?:(?:Given|When|Then|And|But|Scenario).+\n?)+)"
        
        for match in re.finditer(rule_pattern, content):
            rule = {
                "name": match.group(1).strip(),
                "scenarios": self._extract_scenarios(match.group(2))
            }
            rules.append(rule)
        
        return rules


class OpenAPISpecParser(BaseSpecParser):
    """OpenAPI风格规范解析器"""
    
    def get_format(self) -> SpecFormat:
        return SpecFormat.OPENAPI
    
    def parse(self, content: str) -> Dict[str, Any]:
        parsed = yaml.safe_load(content)
        
        if not isinstance(parsed, dict):
            raise ValueError("OpenAPI规范必须是有效的YAML/JSON对象")
        
        openapi_version = parsed.get("openapi", "")
        swagger_version = parsed.get("swagger", "")
        
        if not openapi_version and not swagger_version:
            raise ValueError("未找到OpenAPI/Swagger版本声明")
        
        spec = {
            "apiVersion": "sdd/v1",
            "kind": SpecType.API.value,
            "metadata": self._extract_metadata(parsed),
            "spec": self._extract_spec(parsed)
        }
        
        return spec
    
    def serialize(self, spec: Dict[str, Any]) -> str:
        openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": spec.get("metadata", {}).get("name", "API"),
                "version": spec.get("metadata", {}).get("version", "1.0.0"),
                "description": spec.get("spec", {}).get("description", ""),
            },
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {}
            }
        }
        
        spec_content = spec.get("spec", {})
        
        for endpoint in spec_content.get("endpoints", []):
            path = endpoint.get("path", "/")
            method = endpoint.get("method", "get").lower()
            
            if path not in openapi_spec["paths"]:
                openapi_spec["paths"][path] = {}
            
            openapi_spec["paths"][path][method] = {
                "summary": endpoint.get("description", ""),
                "operationId": endpoint.get("name", ""),
                "responses": {
                    "200": {
                        "description": "成功响应",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            }
            
            if endpoint.get("parameters"):
                openapi_spec["paths"][path][method]["parameters"] = endpoint["parameters"]
            
            if endpoint.get("requestBody"):
                openapi_spec["paths"][path][method]["requestBody"] = endpoint["requestBody"]
            
            if endpoint.get("authentication"):
                openapi_spec["paths"][path][method]["security"] = [{"bearerAuth": []}]
        
        for attr in spec_content.get("attributes", []):
            schema_name = attr.get("name", "Entity")
            openapi_spec["components"]["schemas"][schema_name] = self._attr_to_schema(attr)
        
        return yaml.dump(openapi_spec, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    def _extract_metadata(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        info = parsed.get("info", {})
        
        return {
            "id": f"SPC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": info.get("title", "未命名API"),
            "version": info.get("version", "1.0.0"),
            "author": info.get("contact", {}).get("name", ""),
            "status": "approved" if parsed.get("openapi", "").startswith("3") else "draft"
        }
    
    def _extract_spec(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        spec = {}
        
        info = parsed.get("info", {})
        if "description" in info:
            spec["description"] = info["description"]
        
        spec["endpoints"] = self._extract_endpoints(parsed)
        spec["attributes"] = self._extract_schemas(parsed)
        spec["security_constraints"] = self._extract_security(parsed)
        spec["performance_constraints"] = self._extract_performance(parsed)
        
        return spec
    
    def _extract_endpoints(self, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        endpoints = []
        paths = parsed.get("paths", {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "patch", "delete"]:
                    endpoint = {
                        "name": details.get("operationId", f"{method}_{path}"),
                        "method": method.upper(),
                        "path": path,
                        "description": details.get("summary", ""),
                        "parameters": details.get("parameters", []),
                        "requestBody": details.get("requestBody"),
                        "authentication": "security" in details,
                        "errors": []
                    }
                    
                    responses = details.get("responses", {})
                    for status_code, response in responses.items():
                        if str(status_code).startswith(("4", "5")):
                            endpoint["errors"].append({
                                "code": status_code,
                                "description": response.get("description", "")
                            })
                    
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_schemas(self, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        attributes = []
        schemas = parsed.get("components", {}).get("schemas", {})
        
        for schema_name, schema_def in schemas.items():
            attr = {
                "name": schema_name,
                "type": "object",
                "description": schema_def.get("description", ""),
                "nested_attributes": []
            }
            
            properties = schema_def.get("properties", {})
            required = schema_def.get("required", [])
            
            for prop_name, prop_def in properties.items():
                nested_attr = {
                    "name": prop_name,
                    "type": prop_def.get("type", "string"),
                    "required": prop_name in required,
                    "description": prop_def.get("description", ""),
                    "constraints": {}
                }
                
                if "minLength" in prop_def:
                    nested_attr["constraints"]["minLength"] = prop_def["minLength"]
                if "maxLength" in prop_def:
                    nested_attr["constraints"]["maxLength"] = prop_def["maxLength"]
                if "minimum" in prop_def:
                    nested_attr["constraints"]["min"] = prop_def["minimum"]
                if "maximum" in prop_def:
                    nested_attr["constraints"]["max"] = prop_def["maximum"]
                if "enum" in prop_def:
                    nested_attr["enumValues"] = prop_def["enum"]
                
                attr["nested_attributes"].append(nested_attr)
            
            attributes.append(attr)
        
        return attributes
    
    def _extract_security(self, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        security_constraints = []
        
        security_schemes = parsed.get("components", {}).get("securitySchemes", {})
        for scheme_name, scheme_def in security_schemes.items():
            constraint = {
                "name": scheme_name,
                "type": scheme_def.get("type", ""),
                "description": scheme_def.get("description", ""),
                "authentication_required": True
            }
            
            if scheme_def.get("type") == "oauth2":
                constraint["authorization_roles"] = list(
                    scheme_def.get("flows", {}).get("implicit", {}).get("scopes", {}).keys()
                )
            
            security_constraints.append(constraint)
        
        return security_constraints
    
    def _extract_performance(self, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        performance_constraints = []
        
        extensions = parsed.get("x-performance", {})
        if extensions:
            for name, details in extensions.items():
                constraint = {
                    "name": name,
                    "metric": details.get("metric", "response_time"),
                    "threshold": details.get("threshold", 1000),
                    "unit": details.get("unit", "ms"),
                    "description": details.get("description", "")
                }
                performance_constraints.append(constraint)
        
        return performance_constraints
    
    def _attr_to_schema(self, attr: Dict[str, Any]) -> Dict[str, Any]:
        schema = {
            "type": attr.get("type", "object"),
            "description": attr.get("description", "")
        }
        
        if attr.get("type") == "enum":
            schema["enum"] = attr.get("enumValues", [])
        
        constraints = attr.get("constraints", {})
        if "minLength" in constraints:
            schema["minLength"] = constraints["minLength"]
        if "maxLength" in constraints:
            schema["maxLength"] = constraints["maxLength"]
        if "min" in constraints:
            schema["minimum"] = constraints["min"]
        if "max" in constraints:
            schema["maximum"] = constraints["max"]
        
        return schema


class SpecValidator:
    """规范验证器"""
    
    REQUIRED_METADATA_FIELDS = ["id", "name", "version"]
    VALID_SPEC_TYPES = [t.value for t in SpecType]
    VALID_DATA_TYPES = ["string", "integer", "bigint", "float", "boolean", "date", "datetime", "json", "array", "enum", "text", "object"]
    VALID_HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
    
    def validate(self, spec: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        self._validate_api_version(spec, result)
        self._validate_kind(spec, result)
        self._validate_metadata(spec, result)
        self._validate_spec_content(spec, result)
        self._validate_extensions(spec, result)
        
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
        elif kind in [SpecType.INTERFACE.value, SpecType.API.value]:
            self._validate_interface_spec(spec_content, result)
        elif kind == SpecType.ACCEPTANCE.value:
            self._validate_acceptance_spec(spec_content, result)
        elif kind == SpecType.SERVICE.value:
            self._validate_service_spec(spec_content, result)
    
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
            
            if "validationRules" in attr:
                self._validate_validation_rules(attr["validationRules"], f"{path}.validationRules", result)
    
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
    
    def _validate_service_spec(self, spec_content: Dict[str, Any], result: ValidationResult):
        if not spec_content.get("description"):
            result.add_warning("spec.description", "服务规范缺少描述", "添加description字段描述服务功能")
        
        endpoints = spec_content.get("endpoints", [])
        if not endpoints:
            result.add_warning("spec.endpoints", "服务规范缺少端点定义", "添加endpoints数组定义服务接口")
    
    def _validate_validation_rules(self, rules: List[Dict[str, Any]], path: str, result: ValidationResult):
        valid_rules = ["minLength", "maxLength", "pattern", "minimum", "maximum", "enum", "custom"]
        
        for idx, rule in enumerate(rules):
            rule_type = rule.get("type", "")
            if rule_type not in valid_rules:
                result.add_warning(f"{path}[{idx}].type", f"非标准验证规则: {rule_type}", f"建议使用: {', '.join(valid_rules)}")
    
    def _validate_extensions(self, spec: Dict[str, Any], result: ValidationResult):
        extensions = spec.get("extensions", {})
        
        if extensions:
            for ext_name, ext_value in extensions.items():
                if not isinstance(ext_value, dict):
                    result.add_warning(f"extensions.{ext_name}", "扩展字段应为对象类型")


class EnhancedSDDSpecParser:
    """增强的SDD规范解析器"""
    
    def __init__(self):
        self.parsers = {
            SpecFormat.YAML: YAMLSpecParser(),
            SpecFormat.JSON: JSONSpecParser(),
            SpecFormat.MARKDOWN: MarkdownSpecParser(),
            SpecFormat.DSL: DSLSpecParser(),
            SpecFormat.GHERKIN: GherkinSpecParser(),
            SpecFormat.OPENAPI: OpenAPISpecParser(),
        }
        self.validator = SpecValidator()
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
        
        self.spec_registry[spec.metadata.id] = spec
        
        return spec, validation_result
    
    def _detect_format(self, path: Path) -> SpecFormat:
        suffix = path.suffix.lower()
        if suffix in [".yaml", ".yml"]:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read(500)
                if "openapi:" in content or "swagger:" in content:
                    return SpecFormat.OPENAPI
            return SpecFormat.YAML
        elif suffix == ".json":
            with open(path, "r", encoding="utf-8") as f:
                content = f.read(500)
                if '"openapi"' in content or '"swagger"' in content:
                    return SpecFormat.OPENAPI
            return SpecFormat.JSON
        elif suffix == ".md":
            return SpecFormat.MARKDOWN
        elif suffix == ".dsl":
            return SpecFormat.DSL
        elif suffix in [".feature", ".gherkin"]:
            return SpecFormat.GHERKIN
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
            dependencies=metadata_dict.get("dependencies", []),
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
        spec.constraints = self._parse_constraints(spec_content)
        spec.business_rules = self._parse_business_rules(spec_content)
        spec.relationships = spec_content.get("relationships", [])
        spec.extensions = parsed.get("extensions", {})
        spec.custom_fields = parsed.get("customFields", {})
        
        spec.conditional_branches = self._parse_conditional_branches(spec_content)
        spec.exception_handlers = self._parse_exception_handlers(spec_content)
        spec.performance_constraints = self._parse_performance_constraints(spec_content)
        spec.security_constraints = self._parse_security_constraints(spec_content)
        
        return spec
    
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
                validation_rules=attr_dict.get("validationRules", []),
                nested_attributes=self._parse_attributes(attr_dict) if "attributes" in attr_dict or "properties" in attr_dict else [],
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
                timeout=ep_dict.get("timeout"),
                middleware=ep_dict.get("middleware", []),
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
                priority=scenario_dict.get("priority", "medium"),
                tags=scenario_dict.get("tags", []),
                preconditions=scenario_dict.get("preconditions", []),
                postconditions=scenario_dict.get("postconditions", []),
            )
            scenarios.append(scenario)
        return scenarios
    
    def _parse_constraints(self, spec_content: Dict[str, Any]) -> List[SpecConstraint]:
        constraints = []
        for const_dict in spec_content.get("constraints", []):
            constraint = SpecConstraint(
                name=const_dict.get("name", ""),
                type=const_dict.get("type", "business"),
                description=const_dict.get("description", ""),
                rule=const_dict.get("rule", ""),
                parameters=const_dict.get("parameters", {}),
                error_message=const_dict.get("errorMessage", ""),
                severity=const_dict.get("severity", "error"),
            )
            constraints.append(constraint)
        return constraints
    
    def _parse_business_rules(self, spec_content: Dict[str, Any]) -> List[SpecBusinessRule]:
        rules = []
        for rule_dict in spec_content.get("businessRules", []):
            rule = SpecBusinessRule(
                id=rule_dict.get("id", ""),
                name=rule_dict.get("name", ""),
                description=rule_dict.get("description", ""),
                condition=rule_dict.get("condition", ""),
                action=rule_dict.get("action", ""),
                priority=rule_dict.get("priority", 1),
                enabled=rule_dict.get("enabled", True),
                tags=rule_dict.get("tags", []),
            )
            rules.append(rule)
        return rules
    
    def _parse_conditional_branches(self, spec_content: Dict[str, Any]) -> List[SpecConditionalBranch]:
        branches = []
        for branch_dict in spec_content.get("conditionalBranches", spec_content.get("conditional_branches", [])):
            branch = self._parse_single_conditional_branch(branch_dict)
            branches.append(branch)
        return branches
    
    def _parse_single_conditional_branch(self, branch_dict: Dict[str, Any]) -> SpecConditionalBranch:
        return SpecConditionalBranch(
            condition=branch_dict.get("condition", ""),
            description=branch_dict.get("description", ""),
            actions=branch_dict.get("actions", []),
            else_branch=self._parse_single_conditional_branch(branch_dict["else"]) if branch_dict.get("else") else None,
            nested_conditions=[self._parse_single_conditional_branch(n) for n in branch_dict.get("nestedConditions", branch_dict.get("nested_conditions", []))],
        )
    
    def _parse_exception_handlers(self, spec_content: Dict[str, Any]) -> List[SpecExceptionHandler]:
        handlers = []
        for handler_dict in spec_content.get("exceptionHandlers", spec_content.get("exception_handlers", spec_content.get("exceptions", []))):
            handler = SpecExceptionHandler(
                exception_type=handler_dict.get("exceptionType", handler_dict.get("type", "Exception")),
                description=handler_dict.get("description", ""),
                error_code=handler_dict.get("errorCode", handler_dict.get("code", "")),
                http_status=handler_dict.get("httpStatus", handler_dict.get("status", 500)),
                message=handler_dict.get("message", ""),
                recovery_action=handler_dict.get("recoveryAction", handler_dict.get("recovery", "")),
                retry_policy=handler_dict.get("retryPolicy", handler_dict.get("retry", {})),
                fallback_behavior=handler_dict.get("fallbackBehavior", handler_dict.get("fallback", "")),
            )
            handlers.append(handler)
        return handlers
    
    def _parse_performance_constraints(self, spec_content: Dict[str, Any]) -> List[SpecPerformanceConstraint]:
        constraints = []
        for const_dict in spec_content.get("performanceConstraints", spec_content.get("performance_constraints", spec_content.get("performance", []))):
            constraint = SpecPerformanceConstraint(
                name=const_dict.get("name", ""),
                metric=const_dict.get("metric", "response_time"),
                threshold=const_dict.get("threshold", 1000),
                unit=const_dict.get("unit", "ms"),
                description=const_dict.get("description", ""),
                priority=const_dict.get("priority", "medium"),
                conditions=const_dict.get("conditions", []),
                measurement_method=const_dict.get("measurementMethod", const_dict.get("method", "average")),
                sample_size=const_dict.get("sampleSize", const_dict.get("sample", 100)),
                percentiles=const_dict.get("percentiles", []),
            )
            constraints.append(constraint)
        return constraints
    
    def _parse_security_constraints(self, spec_content: Dict[str, Any]) -> List[SpecSecurityConstraint]:
        constraints = []
        for const_dict in spec_content.get("securityConstraints", spec_content.get("security_constraints", spec_content.get("security", []))):
            constraint = SpecSecurityConstraint(
                name=const_dict.get("name", ""),
                type=const_dict.get("type", "authentication"),
                description=const_dict.get("description", ""),
                authentication_required=const_dict.get("authenticationRequired", const_dict.get("auth_required", False)),
                authorization_roles=const_dict.get("authorizationRoles", const_dict.get("roles", [])),
                permissions=const_dict.get("permissions", []),
                rate_limit=const_dict.get("rateLimit", const_dict.get("rate_limit")),
                rate_limit_window=const_dict.get("rateLimitWindow", const_dict.get("window", 60)),
                encryption_required=const_dict.get("encryptionRequired", const_dict.get("encryption", False)),
                encryption_algorithm=const_dict.get("encryptionAlgorithm", const_dict.get("algorithm", "")),
                data_classification=const_dict.get("dataClassification", const_dict.get("classification", "public")),
                audit_logging=const_dict.get("auditLogging", const_dict.get("audit", True)),
                ip_whitelist=const_dict.get("ipWhitelist", const_dict.get("whitelist", [])),
                ip_blacklist=const_dict.get("ipBlacklist", const_dict.get("blacklist", [])),
            )
            constraints.append(constraint)
        return constraints
    
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
                "dependencies": spec.metadata.dependencies,
            },
            "spec": spec.spec,
            "extensions": spec.extensions,
            "customFields": spec.custom_fields,
        }
        
        return parser.serialize(spec_dict)
    
    def get_spec_by_id(self, spec_id: str) -> Optional[SDDSpecification]:
        return self.spec_registry.get(spec_id)
    
    def list_specs(self) -> List[str]:
        return list(self.spec_registry.keys())


class BusinessRuleExtractor:
    """业务规则自动提取器"""
    
    RULE_PATTERNS = {
        "validation": [
            r"必须|必填|required",
            r"不能为空|不能为|null",
            r"长度[为在]?\s*(\d+)\s*到\s*(\d+)",
            r"最小长度[为:：]\s*(\d+)",
            r"最大长度[为:：]\s*(\d+)",
            r"范围[为:：]\s*(\d+)\s*[-~到]\s*(\d+)",
            r"格式[为:：]\s*(\S+)",
            r"只能[是为]\s*(.+)",
            r"枚举值[为:：]\s*(.+)",
        ],
        "calculation": [
            r"等于\s*(.+)",
            r"计算公式[为:：]\s*(.+)",
            r"自动计算\s*(.+)",
            r"根据\s*(.+)\s*计算",
            r"累加|求和|总计",
        ],
        "constraint": [
            r"唯一|unique",
            r"不能重复|不可重复",
            r"必须存在|必须包含",
            r"外键|关联",
            r"参照|引用",
        ],
        "state_transition": [
            r"当\s*(.+)\s*时",
            r"如果\s*(.+)\s*则",
            r"状态从\s*(.+)\s*变为\s*(.+)",
            r"流转到|转换为",
        ],
        "permission": [
            r"只有\s*(.+)\s*可以",
            r"需要\s*(.+)\s*权限",
            r"仅\s*(.+)\s*可见",
            r"角色\s*(.+)\s*才能",
        ],
        "timing": [
            r"在\s*(.+)\s*之后",
            r"在\s*(.+)\s*之前",
            r"有效期[为:：]\s*(.+)",
            r"超时[为:：]\s*(\d+)",
            r"定时|周期|定期",
        ]
    }
    
    CONDITION_KEYWORDS = [
        "如果", "当", "若", "假如", "只要", "一旦",
        "if", "when", "whenever", "given"
    ]
    
    ACTION_KEYWORDS = [
        "则", "那么", "就", "需要", "必须", "应该",
        "then", "should", "must", "will"
    ]
    
    def extract_business_rules(self, spec: SDDSpecification) -> List[SpecBusinessRule]:
        rules = []
        
        rules.extend(self._extract_from_description(spec))
        rules.extend(self._extract_from_attributes(spec))
        rules.extend(self._extract_from_constraints(spec))
        rules.extend(self._extract_from_scenarios(spec))
        rules.extend(self._extract_from_endpoints(spec))
        rules.extend(self._extract_from_conditional_branches(spec))
        
        rules.extend(spec.business_rules)
        
        seen = set()
        unique_rules = []
        for rule in rules:
            rule_key = (rule.name, rule.condition)
            if rule_key not in seen:
                seen.add(rule_key)
                unique_rules.append(rule)
        
        return unique_rules
    
    def _extract_from_description(self, spec: SDDSpecification) -> List[SpecBusinessRule]:
        rules = []
        description = spec.spec.get("description", "")
        
        if not description:
            return rules
        
        sentences = re.split(r'[。\n]', description)
        
        for idx, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            rule = self._parse_rule_from_text(sentence, f"DESC-{idx+1:03d}")
            if rule:
                rules.append(rule)
        
        return rules
    
    def _extract_from_attributes(self, spec: SDDSpecification) -> List[SpecBusinessRule]:
        rules = []
        
        for attr in spec.attributes:
            if attr.required:
                rules.append(SpecBusinessRule(
                    id=f"BR-ATTR-{attr.name}-required",
                    name=f"{attr.name}必填验证",
                    description=f"属性 {attr.name} 为必填项",
                    condition=f"创建或更新时",
                    action=f"{attr.name} 不能为空",
                    priority=1,
                    enabled=True,
                    tags=["validation", "attribute"]
                ))
            
            if attr.unique:
                rules.append(SpecBusinessRule(
                    id=f"BR-ATTR-{attr.name}-unique",
                    name=f"{attr.name}唯一性验证",
                    description=f"属性 {attr.name} 必须唯一",
                    condition=f"创建或更新时",
                    action=f"{attr.name} 不能与已有记录重复",
                    priority=1,
                    enabled=True,
                    tags=["constraint", "attribute"]
                ))
            
            if attr.constraints:
                for constraint_name, constraint_value in attr.constraints.items():
                    rules.append(SpecBusinessRule(
                        id=f"BR-ATTR-{attr.name}-{constraint_name}",
                        name=f"{attr.name}{constraint_name}约束",
                        description=f"属性 {attr.name} 的 {constraint_name} 约束",
                        condition=f"验证 {attr.name} 时",
                        action=f"{constraint_name} 必须满足 {constraint_value}",
                        priority=2,
                        enabled=True,
                        tags=["validation", "constraint"]
                    ))
            
            if attr.type == "enum" and attr.enum_values:
                rules.append(SpecBusinessRule(
                    id=f"BR-ATTR-{attr.name}-enum",
                    name=f"{attr.name}枚举值验证",
                    description=f"属性 {attr.name} 的枚举值约束",
                    condition=f"设置 {attr.name} 时",
                    action=f"值必须是 {', '.join(attr.enum_values)} 之一",
                    priority=1,
                    enabled=True,
                    tags=["validation", "enum"]
                ))
            
            if attr.description:
                desc_rules = self._parse_rule_from_text(attr.description, f"ATTR-{attr.name}")
                if desc_rules:
                    rules.append(desc_rules)
        
        return rules
    
    def _extract_from_constraints(self, spec: SDDSpecification) -> List[SpecBusinessRule]:
        rules = []
        
        for idx, constraint in enumerate(spec.constraints):
            const_name = constraint.get("name", f"constraint-{idx}")
            
            rules.append(SpecBusinessRule(
                id=f"BR-CONST-{idx+1:03d}",
                name=const_name,
                description=constraint.get("description", ""),
                condition=constraint.get("rule", ""),
                action=f"执行约束检查: {const_name}",
                priority=1,
                enabled=True,
                tags=["constraint", constraint.get("type", "business")]
            ))
        
        return rules
    
    def _extract_from_scenarios(self, spec: SDDSpecification) -> List[SpecBusinessRule]:
        rules = []
        
        for idx, scenario in enumerate(spec.scenarios):
            if scenario.given:
                condition = scenario.given
                if scenario.when:
                    condition += f" 并且 {scenario.when}"
                
                rules.append(SpecBusinessRule(
                    id=f"BR-SCENE-{idx+1:03d}",
                    name=f"场景规则: {scenario.name}",
                    description=f"测试场景: {scenario.given} -> {scenario.when} -> {scenario.then}",
                    condition=condition,
                    action=scenario.then,
                    priority=2,
                    enabled=True,
                    tags=["scenario", "acceptance"]
                ))
        
        return rules
    
    def _extract_from_endpoints(self, spec: SDDSpecification) -> List[SpecBusinessRule]:
        rules = []
        
        for endpoint in spec.endpoints:
            if endpoint.authentication:
                rules.append(SpecBusinessRule(
                    id=f"BR-API-{endpoint.name}-auth",
                    name=f"{endpoint.name}认证规则",
                    description=f"端点 {endpoint.method} {endpoint.path} 需要认证",
                    condition="访问该端点时",
                    action="必须提供有效的认证信息",
                    priority=1,
                    enabled=True,
                    tags=["security", "api"]
                ))
            
            if endpoint.rate_limit:
                rules.append(SpecBusinessRule(
                    id=f"BR-API-{endpoint.name}-rate",
                    name=f"{endpoint.name}限流规则",
                    description=f"端点 {endpoint.method} {endpoint.path} 限流",
                    condition="访问该端点时",
                    action=f"每分钟最多 {endpoint.rate_limit} 次请求",
                    priority=2,
                    enabled=True,
                    tags=["performance", "api"]
                ))
            
            for error in endpoint.errors:
                error_code = error.get("code", error.get("status", "500"))
                rules.append(SpecBusinessRule(
                    id=f"BR-API-{endpoint.name}-err-{error_code}",
                    name=f"{endpoint.name}错误处理{error_code}",
                    description=error.get("description", error.get("message", "")),
                    condition=f"发生 {error_code} 错误时",
                    action=f"返回错误响应: {error.get('description', '')}",
                    priority=2,
                    enabled=True,
                    tags=["error-handling", "api"]
                ))
        
        return rules
    
    def _extract_from_conditional_branches(self, spec: SDDSpecification) -> List[SpecBusinessRule]:
        rules = []
        
        def process_branch(branch: SpecConditionalBranch, path: str, depth: int = 0):
            rule_id = f"BR-BRANCH-{path}"
            actions_text = "; ".join(branch.actions) if branch.actions else branch.description
            
            rules.append(SpecBusinessRule(
                id=rule_id,
                name=f"条件分支规则 {path}",
                description=branch.description,
                condition=branch.condition,
                action=actions_text,
                priority=2,
                enabled=True,
                tags=["conditional", "branch"]
            ))
            
            if branch.else_branch:
                process_branch(branch.else_branch, f"{path}-else", depth + 1)
            
            for idx, nested in enumerate(branch.nested_conditions):
                process_branch(nested, f"{path}-{idx}", depth + 1)
        
        for idx, branch in enumerate(spec.conditional_branches):
            process_branch(branch, f"{idx+1:02d}")
        
        return rules
    
    def _parse_rule_from_text(self, text: str, prefix: str) -> Optional[SpecBusinessRule]:
        condition = ""
        action = ""
        rule_type = "business"
        
        for keyword in self.CONDITION_KEYWORDS:
            if keyword in text.lower():
                parts = re.split(rf'{keyword}|则|那么|就', text, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) == 2:
                    condition = parts[0].strip()
                    action = parts[1].strip()
                    break
        
        if not condition:
            for pattern_type, patterns in self.RULE_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        rule_type = pattern_type
                        condition = f"验证时"
                        action = text
                        break
                if condition:
                    break
        
        if condition or action:
            return SpecBusinessRule(
                id=f"BR-{prefix}",
                name=text[:50] + ("..." if len(text) > 50 else ""),
                description=text,
                condition=condition,
                action=action,
                priority=2,
                enabled=True,
                tags=[rule_type]
            )
        
        return None
    
    def extract_rule_dependencies(self, rules: List[SpecBusinessRule]) -> Dict[str, List[str]]:
        dependencies = {}
        
        for rule in rules:
            deps = []
            
            for other_rule in rules:
                if other_rule.id == rule.id:
                    continue
                
                if other_rule.name in rule.condition or other_rule.name in rule.action:
                    deps.append(other_rule.id)
                
                if rule.name in other_rule.condition or rule.name in other_rule.action:
                    if other_rule.id not in deps:
                        deps.append(other_rule.id)
            
            if deps:
                dependencies[rule.id] = deps
        
        return dependencies
    
    def categorize_rules(self, rules: List[SpecBusinessRule]) -> Dict[str, List[SpecBusinessRule]]:
        categories = {
            "validation": [],
            "calculation": [],
            "constraint": [],
            "state_transition": [],
            "permission": [],
            "timing": [],
            "other": []
        }
        
        for rule in rules:
            categorized = False
            for tag in rule.tags:
                if tag in categories:
                    categories[tag].append(rule)
                    categorized = True
                    break
            
            if not categorized:
                categories["other"].append(rule)
        
        return categories


class EnhancedCompletenessValidator:
    """增强的规范完整性验证器"""
    
    REQUIRED_ENTITY_ELEMENTS = ["attributes"]
    REQUIRED_INTERFACE_ELEMENTS = ["endpoints"]
    REQUIRED_ACCEPTANCE_ELEMENTS = ["scenarios"]
    REQUIRED_SERVICE_ELEMENTS = ["description", "endpoints"]
    
    QUALITY_CHECKS = {
        "description_quality": {
            "min_length": 20,
            "message": "描述内容过短，建议补充详细说明"
        },
        "attribute_description": {
            "check": True,
            "message": "属性缺少描述说明"
        },
        "example_data": {
            "check": True,
            "message": "缺少示例数据"
        },
        "security_constraints": {
            "check": True,
            "message": "缺少安全约束定义"
        },
        "performance_constraints": {
            "check": True,
            "message": "缺少性能约束定义"
        },
        "exception_handling": {
            "check": True,
            "message": "缺少异常处理定义"
        },
        "business_rules": {
            "check": True,
            "message": "缺少业务规则定义"
        },
        "test_scenarios": {
            "check": True,
            "message": "缺少测试场景定义"
        }
    }
    
    def validate_completeness(self, spec) -> 'EnhancedCompletenessReport':
        check_time = datetime.now().isoformat()
        missing_elements: Dict[str, List[str]] = {}
        quality_issues: List[Dict[str, Any]] = []
        suggestions: List[str] = []
        passed_checks: List[str] = []
        failed_checks: List[str] = []
        
        self._check_required_elements(spec, missing_elements, passed_checks, failed_checks)
        self._check_metadata_completeness(spec, missing_elements, passed_checks, failed_checks)
        self._check_spec_content_quality(spec, quality_issues, passed_checks, failed_checks)
        self._check_test_coverage_readiness(spec, missing_elements, suggestions)
        self._check_cross_references(spec, quality_issues, passed_checks, failed_checks)
        
        security_analysis = self._check_security_constraints(spec, quality_issues, passed_checks, failed_checks)
        performance_analysis = self._check_performance_constraints(spec, quality_issues, passed_checks, failed_checks)
        exception_analysis = self._check_exception_handlers(spec, quality_issues, passed_checks, failed_checks)
        conditional_analysis = self._check_conditional_branches(spec, quality_issues, passed_checks, failed_checks)
        business_rule_analysis = self._check_business_rules(spec, quality_issues, passed_checks, failed_checks)
        
        total_checks = len(passed_checks) + len(failed_checks)
        completeness_score = (len(passed_checks) / total_checks * 100) if total_checks > 0 else 0
        
        suggestions.extend(self._generate_completeness_suggestions(missing_elements, quality_issues))
        
        if completeness_score >= 90:
            level = CompletenessLevel.COMPLETE
        elif completeness_score >= 60:
            level = CompletenessLevel.PARTIAL
        else:
            level = CompletenessLevel.INCOMPLETE
        
        detailed_metrics = self._calculate_detailed_metrics(spec)
        
        return EnhancedCompletenessReport(
            spec_id=spec.metadata.id,
            spec_name=spec.metadata.name,
            spec_kind=spec.kind.value,
            check_time=check_time,
            completeness_score=round(completeness_score, 2),
            level=level,
            missing_elements=dict(missing_elements),
            quality_issues=quality_issues,
            suggestions=suggestions,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            security_analysis=security_analysis,
            performance_analysis=performance_analysis,
            exception_handling_analysis=exception_analysis,
            conditional_branch_analysis=conditional_analysis,
            business_rule_analysis=business_rule_analysis,
            detailed_metrics=detailed_metrics
        )
    
    def _check_required_elements(self, spec, missing: Dict, passed: List, failed: List):
        kind = spec.kind.value
        
        if kind == "EntitySpec":
            if not spec.attributes:
                missing["entity"] = ["attributes"]
                failed.append("实体缺少属性定义")
            else:
                passed.append("实体属性定义完整")
                self._check_attribute_quality(spec.attributes, missing, passed, failed)
        
        elif kind in ["InterfaceSpec", "ApiSpec"]:
            if not spec.endpoints:
                missing["interface"] = ["endpoints"]
                failed.append("接口缺少端点定义")
            else:
                passed.append("接口端点定义完整")
                self._check_endpoint_quality(spec.endpoints, missing, passed, failed)
        
        elif kind == "AcceptanceSpec":
            if not spec.scenarios:
                missing["acceptance"] = ["scenarios"]
                failed.append("验收规范缺少场景定义")
            else:
                passed.append("验收场景定义完整")
                self._check_scenario_quality(spec.scenarios, missing, passed, failed)
        
        elif kind == "ServiceSpec":
            if not spec.spec.get("description"):
                missing["service"] = ["description"]
                failed.append("服务缺少描述")
            else:
                passed.append("服务描述存在")
            
            if not spec.endpoints:
                missing["service"] = missing.get("service", []) + ["endpoints"]
                failed.append("服务缺少端点定义")
            else:
                passed.append("服务端点定义完整")
        
        if not spec.spec.get("description"):
            missing["spec"] = ["description"]
            failed.append("规范缺少功能描述")
        else:
            passed.append("规范功能描述存在")
    
    def _check_attribute_quality(self, attributes, missing: Dict, passed: List, failed: List):
        attrs_without_type = [a for a in attributes if not a.type or a.type == "string"]
        if len(attrs_without_type) > len(attributes) * 0.5:
            failed.append("多数属性缺少明确类型定义")
        else:
            passed.append("属性类型定义完整")
        
        attrs_without_desc = [a for a in attributes if not a.description]
        if len(attrs_without_desc) > len(attributes) * 0.3:
            failed.append(f"{len(attrs_without_desc)}个属性缺少描述")
        else:
            passed.append("属性描述覆盖良好")
    
    def _check_endpoint_quality(self, endpoints, missing: Dict, passed: List, failed: List):
        endpoints_without_response = [e for e in endpoints if not e.response]
        if endpoints_without_response:
            failed.append(f"{len(endpoints_without_response)}个端点缺少响应定义")
        else:
            passed.append("端点响应定义完整")
        
        endpoints_without_errors = [e for e in endpoints if not e.errors]
        if len(endpoints_without_errors) > len(endpoints) * 0.5:
            failed.append("多数端点缺少错误处理定义")
        else:
            passed.append("端点错误处理定义良好")
    
    def _check_scenario_quality(self, scenarios, missing: Dict, passed: List, failed: List):
        scenarios_incomplete = [s for s in scenarios if not (s.given and s.when and s.then)]
        if scenarios_incomplete:
            failed.append(f"{len(scenarios_incomplete)}个场景缺少完整的Given/When/Then")
        else:
            passed.append("场景定义完整")
        
        scenarios_without_data = [s for s in scenarios if not s.test_data]
        if len(scenarios_without_data) > len(scenarios) * 0.5:
            failed.append("多数场景缺少测试数据")
        else:
            passed.append("场景测试数据覆盖良好")
    
    def _check_metadata_completeness(self, spec, missing: Dict, passed: List, failed: List):
        required_metadata = ["id", "name", "version"]
        
        for field_name in required_metadata:
            value = getattr(spec.metadata, field_name, None)
            if not value:
                missing.setdefault("metadata", []).append(field_name)
                failed.append(f"元数据缺少{field_name}")
            else:
                passed.append(f"元数据{field_name}存在")
        
        if not spec.metadata.author:
            missing.setdefault("metadata", []).append("author")
        
        if not spec.metadata.tags:
            missing.setdefault("metadata", []).append("tags")
        
        if spec.metadata.status not in ["approved", "review"]:
            missing.setdefault("metadata", []).append("status_review")
    
    def _check_spec_content_quality(self, spec, issues: List, passed: List, failed: List):
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
    
    def _check_test_coverage_readiness(self, spec, missing: Dict, suggestions: List):
        if spec.scenarios:
            scenarios_without_data = [s for s in spec.scenarios if not s.test_data]
            if scenarios_without_data:
                missing.setdefault("test_readiness", []).append("test_data")
                suggestions.append(f"{len(scenarios_without_data)}个场景缺少测试数据")
        
        if spec.endpoints:
            endpoints_without_response = [e for e in spec.endpoints if not e.response]
            if endpoints_without_response:
                missing.setdefault("test_readiness", []).append("response_definition")
                suggestions.append(f"{len(endpoints_without_response)}个端点缺少响应定义")
    
    def _check_cross_references(self, spec, issues: List, passed: List, failed: List):
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
    
    def _check_security_constraints(self, spec, issues: List, passed: List, failed: List) -> Dict[str, Any]:
        analysis = {
            "has_security_constraints": len(spec.security_constraints) > 0,
            "total_constraints": len(spec.security_constraints),
            "auth_required_count": 0,
            "authorization_defined": False,
            "rate_limit_defined": False,
            "encryption_defined": False,
            "audit_defined": False,
            "issues": []
        }
        
        if not spec.security_constraints:
            endpoints_with_auth = [e for e in spec.endpoints if e.authentication]
            if endpoints_with_auth:
                issues.append({
                    "type": "security_constraints",
                    "path": "spec.security_constraints",
                    "message": "存在需要认证的端点但缺少安全约束定义",
                    "severity": "warning"
                })
            failed.append("安全约束检查未通过")
            return analysis
        
        for constraint in spec.security_constraints:
            if constraint.authentication_required:
                analysis["auth_required_count"] += 1
            if constraint.authorization_roles:
                analysis["authorization_defined"] = True
            if constraint.rate_limit:
                analysis["rate_limit_defined"] = True
            if constraint.encryption_required:
                analysis["encryption_defined"] = True
            if constraint.audit_logging:
                analysis["audit_defined"] = True
        
        if analysis["auth_required_count"] > 0:
            passed.append("认证约束已定义")
        else:
            analysis["issues"].append("未定义认证要求")
        
        if analysis["authorization_defined"]:
            passed.append("授权约束已定义")
        
        if analysis["rate_limit_defined"]:
            passed.append("速率限制已定义")
        
        if analysis["encryption_defined"]:
            passed.append("加密要求已定义")
        
        if analysis["audit_defined"]:
            passed.append("审计日志已定义")
        
        return analysis
    
    def _check_performance_constraints(self, spec, issues: List, passed: List, failed: List) -> Dict[str, Any]:
        analysis = {
            "has_performance_constraints": len(spec.performance_constraints) > 0,
            "total_constraints": len(spec.performance_constraints),
            "response_time_defined": False,
            "throughput_defined": False,
            "latency_defined": False,
            "percentiles_defined": False,
            "issues": []
        }
        
        if not spec.performance_constraints:
            issues.append({
                "type": "performance_constraints",
                "path": "spec.performance_constraints",
                "message": "缺少性能约束定义",
                "severity": "warning"
            })
            failed.append("性能约束检查未通过")
            return analysis
        
        for constraint in spec.performance_constraints:
            if constraint.metric in ["response_time", "responseTime"]:
                analysis["response_time_defined"] = True
            if constraint.metric in ["throughput", "rps", "qps"]:
                analysis["throughput_defined"] = True
            if constraint.metric in ["latency", "delay"]:
                analysis["latency_defined"] = True
            if constraint.percentiles:
                analysis["percentiles_defined"] = True
        
        if analysis["response_time_defined"]:
            passed.append("响应时间约束已定义")
        else:
            analysis["issues"].append("未定义响应时间要求")
        
        if analysis["throughput_defined"]:
            passed.append("吞吐量约束已定义")
        
        if analysis["latency_defined"]:
            passed.append("延迟约束已定义")
        
        return analysis
    
    def _check_exception_handlers(self, spec, issues: List, passed: List, failed: List) -> Dict[str, Any]:
        analysis = {
            "has_exception_handlers": len(spec.exception_handlers) > 0,
            "total_handlers": len(spec.exception_handlers),
            "has_retry_policy": False,
            "has_fallback": False,
            "covered_exceptions": [],
            "issues": []
        }
        
        if not spec.exception_handlers:
            issues.append({
                "type": "exception_handling",
                "path": "spec.exception_handlers",
                "message": "缺少异常处理定义",
                "severity": "warning"
            })
            failed.append("异常处理检查未通过")
            return analysis
        
        for handler in spec.exception_handlers:
            analysis["covered_exceptions"].append(handler.exception_type)
            if handler.retry_policy:
                analysis["has_retry_policy"] = True
            if handler.fallback_behavior:
                analysis["has_fallback"] = True
        
        passed.append(f"异常处理已定义 ({len(spec.exception_handlers)}个)")
        
        if analysis["has_retry_policy"]:
            passed.append("重试策略已定义")
        
        if analysis["has_fallback"]:
            passed.append("降级策略已定义")
        
        return analysis
    
    def _check_conditional_branches(self, spec, issues: List, passed: List, failed: List) -> Dict[str, Any]:
        analysis = {
            "has_conditional_branches": len(spec.conditional_branches) > 0,
            "total_branches": len(spec.conditional_branches),
            "has_else_branches": False,
            "max_nesting_depth": 0,
            "issues": []
        }
        
        if not spec.conditional_branches:
            passed.append("无复杂条件分支")
            return analysis
        
        def count_nesting(branch, depth=1):
            max_depth = depth
            if branch.else_branch:
                analysis["has_else_branches"] = True
            for nested in branch.nested_conditions:
                nested_depth = count_nesting(nested, depth + 1)
                max_depth = max(max_depth, nested_depth)
            return max_depth
        
        for branch in spec.conditional_branches:
            nesting = count_nesting(branch)
            analysis["max_nesting_depth"] = max(analysis["max_nesting_depth"], nesting)
        
        passed.append(f"条件分支已定义 ({len(spec.conditional_branches)}个)")
        
        if analysis["max_nesting_depth"] > 3:
            issues.append({
                "type": "complex_conditional",
                "path": "spec.conditional_branches",
                "message": f"条件分支嵌套深度过深 ({analysis['max_nesting_depth']}层)",
                "severity": "warning"
            })
            analysis["issues"].append("条件分支嵌套过深")
        
        return analysis
    
    def _check_business_rules(self, spec, issues: List, passed: List, failed: List) -> Dict[str, Any]:
        analysis = {
            "has_business_rules": len(spec.business_rules) > 0,
            "total_rules": len(spec.business_rules),
            "enabled_rules": 0,
            "rules_by_category": {},
            "rules_with_conditions": 0,
            "rules_with_actions": 0,
            "issues": []
        }
        
        if not spec.business_rules:
            issues.append({
                "type": "business_rules",
                "path": "spec.business_rules",
                "message": "缺少业务规则定义",
                "severity": "warning"
            })
            failed.append("业务规则检查未通过")
            return analysis
        
        for rule in spec.business_rules:
            if rule.enabled:
                analysis["enabled_rules"] += 1
            if rule.condition:
                analysis["rules_with_conditions"] += 1
            if rule.action:
                analysis["rules_with_actions"] += 1
            
            for tag in rule.tags:
                analysis["rules_by_category"][tag] = analysis["rules_by_category"].get(tag, 0) + 1
        
        passed.append(f"业务规则已定义 ({len(spec.business_rules)}个)")
        
        if analysis["rules_with_conditions"] < len(spec.business_rules) * 0.5:
            analysis["issues"].append("多数业务规则缺少条件定义")
        
        if analysis["rules_with_actions"] < len(spec.business_rules) * 0.5:
            analysis["issues"].append("多数业务规则缺少动作定义")
        
        return analysis
    
    def _calculate_detailed_metrics(self, spec) -> Dict[str, Any]:
        metrics = {
            "attributes": {
                "total": len(spec.attributes),
                "with_description": sum(1 for a in spec.attributes if a.description),
                "with_validation": sum(1 for a in spec.attributes if a.constraints or a.validation_rules),
                "with_examples": sum(1 for a in spec.attributes if a.example is not None),
                "required_count": sum(1 for a in spec.attributes if a.required),
                "unique_count": sum(1 for a in spec.attributes if a.unique),
            },
            "endpoints": {
                "total": len(spec.endpoints),
                "with_auth": sum(1 for e in spec.endpoints if e.authentication),
                "with_errors": sum(1 for e in spec.endpoints if e.errors),
                "with_response": sum(1 for e in spec.endpoints if e.response),
                "with_rate_limit": sum(1 for e in spec.endpoints if e.rate_limit),
            },
            "scenarios": {
                "total": len(spec.scenarios),
                "with_test_data": sum(1 for s in spec.scenarios if s.test_data),
                "complete_gwt": sum(1 for s in spec.scenarios if s.given and s.when and s.then),
            },
            "constraints": {
                "total": len(spec.constraints),
                "business": sum(1 for c in spec.constraints if c.type == "business"),
                "validation": sum(1 for c in spec.constraints if c.type == "validation"),
            },
            "business_rules": {
                "total": len(spec.business_rules),
                "enabled": sum(1 for r in spec.business_rules if r.enabled),
                "with_conditions": sum(1 for r in spec.business_rules if r.condition),
                "with_actions": sum(1 for r in spec.business_rules if r.action),
            },
            "security": {
                "total": len(spec.security_constraints),
                "auth_required": sum(1 for s in spec.security_constraints if s.authentication_required),
                "with_encryption": sum(1 for s in spec.security_constraints if s.encryption_required),
                "with_audit": sum(1 for s in spec.security_constraints if s.audit_logging),
            },
            "performance": {
                "total": len(spec.performance_constraints),
            },
            "exceptions": {
                "total": len(spec.exception_handlers),
                "with_retry": sum(1 for h in spec.exception_handlers if h.retry_policy),
                "with_fallback": sum(1 for h in spec.exception_handlers if h.fallback_behavior),
            },
            "conditional_branches": {
                "total": len(spec.conditional_branches),
            },
        }
        
        return metrics
    
    def _generate_completeness_suggestions(self, missing: Dict, issues: List) -> List[str]:
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


@dataclass
class EnhancedCompletenessReport:
    spec_id: str
    spec_name: str
    spec_kind: str
    check_time: str
    completeness_score: float
    level: CompletenessLevel
    missing_elements: Dict[str, List[str]] = field(default_factory=dict)
    quality_issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    test_coverage: Optional[Dict[str, Any]] = None
    security_analysis: Optional[Dict[str, Any]] = None
    performance_analysis: Optional[Dict[str, Any]] = None
    exception_handling_analysis: Optional[Dict[str, Any]] = None
    conditional_branch_analysis: Optional[Dict[str, Any]] = None
    business_rule_analysis: Optional[Dict[str, Any]] = None
    detailed_metrics: Dict[str, Any] = field(default_factory=dict)


class CoverageReportGenerator:
    """覆盖率报告生成器"""
    
    def generate_coverage_report(self, spec, test_cases: List = None) -> 'DetailedCoverageReport':
        report_id = f"COV-{spec.metadata.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        coverage_by_type: Dict[str, 'CoverageMapping'] = {}
        
        attr_coverage = self._analyze_attribute_coverage(spec)
        coverage_by_type["attributes"] = attr_coverage
        
        endpoint_coverage = self._analyze_endpoint_coverage(spec)
        coverage_by_type["endpoints"] = endpoint_coverage
        
        scenario_coverage = self._analyze_scenario_coverage(spec)
        coverage_by_type["scenarios"] = scenario_coverage
        
        constraint_coverage = self._analyze_constraint_coverage(spec)
        coverage_by_type["constraints"] = constraint_coverage
        
        business_rule_coverage = self._analyze_business_rule_coverage(spec)
        coverage_by_type["business_rules"] = business_rule_coverage
        
        security_coverage = self._analyze_security_coverage(spec)
        coverage_by_type["security"] = security_coverage
        
        exception_coverage = self._analyze_exception_coverage(spec)
        coverage_by_type["exceptions"] = exception_coverage
        
        total_requirements = sum(m.total_requirements for m in coverage_by_type.values())
        total_covered = sum(m.covered_requirements for m in coverage_by_type.values())
        overall_coverage = (total_covered / total_requirements * 100) if total_requirements > 0 else 0
        
        coverage_by_priority = self._calculate_coverage_by_priority(spec)
        
        missing_coverage = self._identify_missing_coverage(coverage_by_type)
        
        recommendations = self._generate_recommendations(coverage_by_type, overall_coverage)
        
        risk_assessment = self._assess_coverage_risks(coverage_by_type, missing_coverage)
        
        return DetailedCoverageReport(
            report_id=report_id,
            generated_at=datetime.now().isoformat(),
            spec_id=spec.metadata.id,
            spec_name=spec.metadata.name,
            overall_coverage=round(overall_coverage, 2),
            coverage_by_type=coverage_by_type,
            coverage_by_priority=coverage_by_priority,
            missing_coverage=missing_coverage,
            recommendations=recommendations,
            risk_assessment=risk_assessment
        )
    
    def _analyze_attribute_coverage(self, spec) -> 'CoverageMapping':
        total = len(spec.attributes)
        covered = 0
        coverage_details = {}
        uncovered_items = []
        
        for attr in spec.attributes:
            coverage_score = 0
            coverage_reasons = []
            
            if attr.required:
                coverage_score += 20
                coverage_reasons.append("必填验证")
            
            if attr.constraints:
                coverage_score += 30
                coverage_reasons.append("约束验证")
            
            if attr.description:
                coverage_score += 10
                coverage_reasons.append("有描述")
            
            if attr.example is not None:
                coverage_score += 20
                coverage_reasons.append("有示例")
            
            if attr.validation_rules:
                coverage_score += 20
                coverage_reasons.append("有验证规则")
            
            is_covered = coverage_score >= 50
            
            if is_covered:
                covered += 1
                coverage_details[attr.name] = {
                    "covered": True,
                    "coverage_score": coverage_score,
                    "coverage_reasons": coverage_reasons,
                    "coverage_type": "attribute"
                }
            else:
                uncovered_items.append(attr.name)
                coverage_details[attr.name] = {
                    "covered": False,
                    "coverage_score": coverage_score,
                    "reason": "覆盖率不足"
                }
        
        return CoverageMapping(
            spec_id=spec.metadata.id,
            spec_name="属性覆盖率",
            total_requirements=total,
            covered_requirements=covered,
            coverage_percentage=round((covered / total * 100) if total > 0 else 0, 2),
            test_cases=[],
            uncovered_items=uncovered_items,
            coverage_details=coverage_details
        )
    
    def _analyze_endpoint_coverage(self, spec) -> 'CoverageMapping':
        total = len(spec.endpoints)
        covered = 0
        coverage_details = {}
        uncovered_items = []
        
        for endpoint in spec.endpoints:
            coverage_score = 0
            coverage_reasons = []
            
            if endpoint.description:
                coverage_score += 15
                coverage_reasons.append("有描述")
            
            if endpoint.parameters:
                coverage_score += 15
                coverage_reasons.append("有参数定义")
            
            if endpoint.request_body:
                coverage_score += 15
                coverage_reasons.append("有请求体定义")
            
            if endpoint.response:
                coverage_score += 20
                coverage_reasons.append("有响应定义")
            
            if endpoint.errors:
                coverage_score += 15
                coverage_reasons.append("有错误处理")
            
            if endpoint.authentication:
                coverage_score += 10
                coverage_reasons.append("有认证要求")
            
            if endpoint.rate_limit:
                coverage_score += 10
                coverage_reasons.append("有限流配置")
            
            is_covered = coverage_score >= 50
            
            if is_covered:
                covered += 1
                coverage_details[endpoint.name] = {
                    "covered": True,
                    "coverage_score": coverage_score,
                    "coverage_reasons": coverage_reasons,
                    "coverage_type": "endpoint"
                }
            else:
                uncovered_items.append(endpoint.name)
                coverage_details[endpoint.name] = {
                    "covered": False,
                    "coverage_score": coverage_score,
                    "reason": "覆盖率不足"
                }
        
        return CoverageMapping(
            spec_id=spec.metadata.id,
            spec_name="接口覆盖率",
            total_requirements=total,
            covered_requirements=covered,
            coverage_percentage=round((covered / total * 100) if total > 0 else 0, 2),
            test_cases=[],
            uncovered_items=uncovered_items,
            coverage_details=coverage_details
        )
    
    def _analyze_scenario_coverage(self, spec) -> 'CoverageMapping':
        total = len(spec.scenarios)
        covered = 0
        coverage_details = {}
        uncovered_items = []
        
        for scenario in spec.scenarios:
            coverage_score = 0
            coverage_reasons = []
            
            if scenario.given:
                coverage_score += 25
                coverage_reasons.append("有Given定义")
            
            if scenario.when:
                coverage_score += 25
                coverage_reasons.append("有When定义")
            
            if scenario.then:
                coverage_score += 25
                coverage_reasons.append("有Then定义")
            
            if scenario.test_data:
                coverage_score += 15
                coverage_reasons.append("有测试数据")
            
            if scenario.preconditions:
                coverage_score += 5
                coverage_reasons.append("有前置条件")
            
            if scenario.postconditions:
                coverage_score += 5
                coverage_reasons.append("有后置条件")
            
            is_covered = coverage_score >= 60
            
            if is_covered:
                covered += 1
                coverage_details[scenario.name] = {
                    "covered": True,
                    "coverage_score": coverage_score,
                    "coverage_reasons": coverage_reasons,
                    "coverage_type": "scenario"
                }
            else:
                uncovered_items.append(scenario.name)
                coverage_details[scenario.name] = {
                    "covered": False,
                    "coverage_score": coverage_score,
                    "reason": "场景定义不完整"
                }
        
        return CoverageMapping(
            spec_id=spec.metadata.id,
            spec_name="场景覆盖率",
            total_requirements=total,
            covered_requirements=covered,
            coverage_percentage=round((covered / total * 100) if total > 0 else 0, 2),
            test_cases=[],
            uncovered_items=uncovered_items,
            coverage_details=coverage_details
        )
    
    def _analyze_constraint_coverage(self, spec) -> 'CoverageMapping':
        total = len(spec.constraints)
        covered = 0
        coverage_details = {}
        uncovered_items = []
        
        for idx, constraint in enumerate(spec.constraints):
            constraint_name = constraint.get("name", f"constraint-{idx}")
            coverage_score = 0
            coverage_reasons = []
            
            if constraint.get("description"):
                coverage_score += 30
                coverage_reasons.append("有描述")
            
            if constraint.get("rule"):
                coverage_score += 40
                coverage_reasons.append("有规则定义")
            
            if constraint.get("parameters"):
                coverage_score += 15
                coverage_reasons.append("有参数")
            
            if constraint.get("error_message"):
                coverage_score += 15
                coverage_reasons.append("有错误消息")
            
            is_covered = coverage_score >= 50
            
            if is_covered:
                covered += 1
                coverage_details[constraint_name] = {
                    "covered": True,
                    "coverage_score": coverage_score,
                    "coverage_reasons": coverage_reasons,
                    "coverage_type": "constraint"
                }
            else:
                uncovered_items.append(constraint_name)
                coverage_details[constraint_name] = {
                    "covered": False,
                    "coverage_score": coverage_score,
                    "reason": "约束定义不完整"
                }
        
        return CoverageMapping(
            spec_id=spec.metadata.id,
            spec_name="约束覆盖率",
            total_requirements=total,
            covered_requirements=covered,
            coverage_percentage=round((covered / total * 100) if total > 0 else 0, 2),
            test_cases=[],
            uncovered_items=uncovered_items,
            coverage_details=coverage_details
        )
    
    def _analyze_business_rule_coverage(self, spec) -> 'CoverageMapping':
        total = len(spec.business_rules)
        covered = 0
        coverage_details = {}
        uncovered_items = []
        
        for rule in spec.business_rules:
            coverage_score = 0
            coverage_reasons = []
            
            if rule.description:
                coverage_score += 20
                coverage_reasons.append("有描述")
            
            if rule.condition:
                coverage_score += 30
                coverage_reasons.append("有条件定义")
            
            if rule.action:
                coverage_score += 30
                coverage_reasons.append("有动作定义")
            
            if rule.tags:
                coverage_score += 10
                coverage_reasons.append("有标签分类")
            
            if rule.enabled:
                coverage_score += 10
                coverage_reasons.append("已启用")
            
            is_covered = coverage_score >= 50
            
            if is_covered:
                covered += 1
                coverage_details[rule.name] = {
                    "covered": True,
                    "coverage_score": coverage_score,
                    "coverage_reasons": coverage_reasons,
                    "coverage_type": "business_rule"
                }
            else:
                uncovered_items.append(rule.name)
                coverage_details[rule.name] = {
                    "covered": False,
                    "coverage_score": coverage_score,
                    "reason": "业务规则定义不完整"
                }
        
        return CoverageMapping(
            spec_id=spec.metadata.id,
            spec_name="业务规则覆盖率",
            total_requirements=total,
            covered_requirements=covered,
            coverage_percentage=round((covered / total * 100) if total > 0 else 0, 2),
            test_cases=[],
            uncovered_items=uncovered_items,
            coverage_details=coverage_details
        )
    
    def _analyze_security_coverage(self, spec) -> 'CoverageMapping':
        total = len(spec.security_constraints)
        covered = 0
        coverage_details = {}
        uncovered_items = []
        
        for constraint in spec.security_constraints:
            coverage_score = 0
            coverage_reasons = []
            
            if constraint.description:
                coverage_score += 20
                coverage_reasons.append("有描述")
            
            if constraint.authentication_required:
                coverage_score += 20
                coverage_reasons.append("有认证要求")
            
            if constraint.authorization_roles:
                coverage_score += 20
                coverage_reasons.append("有授权角色")
            
            if constraint.permissions:
                coverage_score += 15
                coverage_reasons.append("有权限定义")
            
            if constraint.encryption_required:
                coverage_score += 15
                coverage_reasons.append("有加密要求")
            
            if constraint.audit_logging:
                coverage_score += 10
                coverage_reasons.append("有审计日志")
            
            is_covered = coverage_score >= 50
            
            if is_covered:
                covered += 1
                coverage_details[constraint.name] = {
                    "covered": True,
                    "coverage_score": coverage_score,
                    "coverage_reasons": coverage_reasons,
                    "coverage_type": "security"
                }
            else:
                uncovered_items.append(constraint.name)
                coverage_details[constraint.name] = {
                    "covered": False,
                    "coverage_score": coverage_score,
                    "reason": "安全约束定义不完整"
                }
        
        return CoverageMapping(
            spec_id=spec.metadata.id,
            spec_name="安全覆盖率",
            total_requirements=total,
            covered_requirements=covered,
            coverage_percentage=round((covered / total * 100) if total > 0 else 0, 2),
            test_cases=[],
            uncovered_items=uncovered_items,
            coverage_details=coverage_details
        )
    
    def _analyze_exception_coverage(self, spec) -> 'CoverageMapping':
        total = len(spec.exception_handlers)
        covered = 0
        coverage_details = {}
        uncovered_items = []
        
        for handler in spec.exception_handlers:
            coverage_score = 0
            coverage_reasons = []
            
            if handler.description:
                coverage_score += 20
                coverage_reasons.append("有描述")
            
            if handler.error_code:
                coverage_score += 20
                coverage_reasons.append("有错误码")
            
            if handler.message:
                coverage_score += 20
                coverage_reasons.append("有错误消息")
            
            if handler.recovery_action:
                coverage_score += 20
                coverage_reasons.append("有恢复动作")
            
            if handler.retry_policy:
                coverage_score += 10
                coverage_reasons.append("有重试策略")
            
            if handler.fallback_behavior:
                coverage_score += 10
                coverage_reasons.append("有降级行为")
            
            is_covered = coverage_score >= 50
            
            if is_covered:
                covered += 1
                coverage_details[handler.exception_type] = {
                    "covered": True,
                    "coverage_score": coverage_score,
                    "coverage_reasons": coverage_reasons,
                    "coverage_type": "exception"
                }
            else:
                uncovered_items.append(handler.exception_type)
                coverage_details[handler.exception_type] = {
                    "covered": False,
                    "coverage_score": coverage_score,
                    "reason": "异常处理定义不完整"
                }
        
        return CoverageMapping(
            spec_id=spec.metadata.id,
            spec_name="异常处理覆盖率",
            total_requirements=total,
            covered_requirements=covered,
            coverage_percentage=round((covered / total * 100) if total > 0 else 0, 2),
            test_cases=[],
            uncovered_items=uncovered_items,
            coverage_details=coverage_details
        )
    
    def _calculate_coverage_by_priority(self, spec) -> Dict[str, float]:
        priority_counts: Dict[str, int] = {}
        
        for attr in spec.attributes:
            if attr.required:
                priority_counts["high"] = priority_counts.get("high", 0) + 1
            else:
                priority_counts["medium"] = priority_counts.get("medium", 0) + 1
        
        for endpoint in spec.endpoints:
            if endpoint.authentication:
                priority_counts["critical"] = priority_counts.get("critical", 0) + 1
            else:
                priority_counts["high"] = priority_counts.get("high", 0) + 1
        
        for scenario in spec.scenarios:
            priority = getattr(scenario, 'priority', 'medium')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        total = sum(priority_counts.values())
        if total == 0:
            return {}
        
        return {
            priority: round(count / total * 100, 2)
            for priority, count in priority_counts.items()
        }
    
    def _identify_missing_coverage(self, coverage_by_type: Dict) -> List[Dict[str, Any]]:
        missing = []
        
        for type_name, mapping in coverage_by_type.items():
            for item_name in mapping.uncovered_items:
                missing.append({
                    "type": type_name,
                    "item": item_name,
                    "reason": mapping.coverage_details.get(item_name, {}).get("reason", "未覆盖"),
                    "priority": "high" if type_name in ["scenarios", "endpoints", "security"] else "medium",
                    "coverage_score": mapping.coverage_details.get(item_name, {}).get("coverage_score", 0)
                })
        
        return sorted(missing, key=lambda x: x.get("coverage_score", 0))
    
    def _generate_recommendations(self, coverage_by_type: Dict, overall: float) -> List[str]:
        recommendations = []
        
        if overall < 50:
            recommendations.append("🔴 覆盖率严重不足，建议优先补充核心功能的定义")
        elif overall < 80:
            recommendations.append("🟡 覆盖率有待提高，建议补充缺失的定义项")
        else:
            recommendations.append("🟢 覆盖率良好，建议关注边界场景和异常处理")
        
        for type_name, mapping in coverage_by_type.items():
            if mapping.total_requirements == 0:
                continue
            
            if mapping.coverage_percentage < 50:
                recommendations.append(f"🔴 {mapping.spec_name}较低({mapping.coverage_percentage}%)，建议优先补充")
            elif mapping.coverage_percentage < 80:
                recommendations.append(f"🟡 {mapping.spec_name}中等({mapping.coverage_percentage}%)，建议完善")
            
            if mapping.uncovered_items:
                items_str = ', '.join(mapping.uncovered_items[:3])
                if len(mapping.uncovered_items) > 3:
                    items_str += f" 等{len(mapping.uncovered_items)}项"
                recommendations.append(f"📝 {type_name}未覆盖项: {items_str}")
        
        return recommendations
    
    def _assess_coverage_risks(self, coverage_by_type: Dict, missing_coverage: List) -> Dict[str, Any]:
        risks = {
            "high_risk": [],
            "medium_risk": [],
            "low_risk": [],
            "overall_risk_level": "low"
        }
        
        high_priority_missing = [m for m in missing_coverage if m.get("priority") == "high"]
        if high_priority_missing:
            risks["high_risk"] = [
                {"item": m["item"], "type": m["type"], "reason": m["reason"]}
                for m in high_priority_missing[:5]
            ]
        
        for type_name, mapping in coverage_by_type.items():
            if mapping.total_requirements > 0 and mapping.coverage_percentage < 50:
                risks["medium_risk"].append({
                    "type": type_name,
                    "coverage": mapping.coverage_percentage,
                    "reason": "覆盖率低于50%"
                })
        
        if len(risks["high_risk"]) > 3:
            risks["overall_risk_level"] = "high"
        elif len(risks["high_risk"]) > 0 or len(risks["medium_risk"]) > 2:
            risks["overall_risk_level"] = "medium"
        
        return risks


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
class DetailedCoverageReport:
    report_id: str
    generated_at: str
    spec_id: str
    spec_name: str
    overall_coverage: float
    coverage_by_type: Dict[str, CoverageMapping] = field(default_factory=dict)
    coverage_by_priority: Dict[str, float] = field(default_factory=dict)
    missing_coverage: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="增强的SDD规范解析器")
    parser.add_argument("spec_file", help="规范文件路径")
    parser.add_argument("--validate", action="store_true", help="验证规范")
    parser.add_argument("--convert", choices=["yaml", "json", "markdown", "dsl"], help="转换格式")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--extract-rules", action="store_true", help="提取业务规则")
    parser.add_argument("--completeness", action="store_true", help="检查规范完整性")
    parser.add_argument("--coverage", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--all", action="store_true", help="执行所有分析")
    parser.add_argument("--export-format", choices=["json", "yaml", "markdown"], default="json", help="导出格式")
    
    args = parser.parse_args()
    
    spec_parser = EnhancedSDDSpecParser()
    rule_extractor = BusinessRuleExtractor()
    completeness_validator = EnhancedCompletenessValidator()
    coverage_generator = CoverageReportGenerator()
    
    try:
        spec, validation_result = spec_parser.parse_file(args.spec_file)
        
        print(f"=" * 60)
        print(f"规范解析成功")
        print(f"=" * 60)
        print(f"  ID: {spec.metadata.id}")
        print(f"  名称: {spec.metadata.name}")
        print(f"  版本: {spec.metadata.version}")
        print(f"  类型: {spec.kind.value}")
        print(f"  属性数量: {len(spec.attributes)}")
        print(f"  端点数量: {len(spec.endpoints)}")
        print(f"  场景数量: {len(spec.scenarios)}")
        print(f"  约束数量: {len(spec.constraints)}")
        print(f"  业务规则数量: {len(spec.business_rules)}")
        
        if args.validate or validation_result.errors or validation_result.warnings:
            print(f"\n" + "=" * 60)
            print(f"验证结果")
            print(f"=" * 60)
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
        
        if args.extract_rules or args.all:
            print(f"\n" + "=" * 60)
            print(f"业务规则提取")
            print(f"=" * 60)
            
            rules = rule_extractor.extract_business_rules(spec)
            print(f"  提取到 {len(rules)} 条业务规则")
            
            categories = rule_extractor.categorize_rules(rules)
            for category, cat_rules in categories.items():
                if cat_rules:
                    print(f"\n  [{category}] ({len(cat_rules)}条):")
                    for rule in cat_rules[:5]:
                        print(f"    - {rule.name}")
                        if rule.condition:
                            print(f"      条件: {rule.condition[:50]}...")
                        if rule.action:
                            print(f"      动作: {rule.action[:50]}...")
            
            if args.output:
                rules_output = {
                    "total_rules": len(rules),
                    "categories": {k: len(v) for k, v in categories.items()},
                    "rules": [
                        {
                            "id": r.id,
                            "name": r.name,
                            "description": r.description,
                            "condition": r.condition,
                            "action": r.action,
                            "priority": r.priority,
                            "tags": r.tags
                        }
                        for r in rules
                    ]
                }
                output_path = args.output.replace(".", "_rules.") if "." in args.output else f"{args.output}_rules"
                output_path = f"{output_path}.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(rules_output, f, ensure_ascii=False, indent=2)
                print(f"\n  业务规则已导出到: {output_path}")
        
        if args.completeness or args.all:
            print(f"\n" + "=" * 60)
            print(f"完整性检查")
            print(f"=" * 60)
            
            report = completeness_validator.validate_completeness(spec)
            print(f"  完整性得分: {report.completeness_score}%")
            print(f"  完整性级别: {report.level.value}")
            print(f"  通过检查: {len(report.passed_checks)}")
            print(f"  未通过检查: {len(report.failed_checks)}")
            print(f"  质量问题: {len(report.quality_issues)}")
            
            if report.passed_checks:
                print(f"\n  通过的检查:")
                for check in report.passed_checks[:10]:
                    print(f"    ✅ {check}")
            
            if report.failed_checks:
                print(f"\n  未通过的检查:")
                for check in report.failed_checks[:10]:
                    print(f"    ❌ {check}")
            
            if report.suggestions:
                print(f"\n  改进建议:")
                for suggestion in report.suggestions[:5]:
                    print(f"    💡 {suggestion}")
            
            if args.output:
                completeness_output = {
                    "spec_id": report.spec_id,
                    "spec_name": report.spec_name,
                    "completeness_score": report.completeness_score,
                    "level": report.level.value,
                    "passed_checks": report.passed_checks,
                    "failed_checks": report.failed_checks,
                    "missing_elements": report.missing_elements,
                    "quality_issues": report.quality_issues,
                    "suggestions": report.suggestions,
                    "detailed_metrics": report.detailed_metrics
                }
                output_path = args.output.replace(".", "_completeness.") if "." in args.output else f"{args.output}_completeness"
                output_path = f"{output_path}.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(completeness_output, f, ensure_ascii=False, indent=2)
                print(f"\n  完整性报告已导出到: {output_path}")
        
        if args.coverage or args.all:
            print(f"\n" + "=" * 60)
            print(f"覆盖率报告")
            print(f"=" * 60)
            
            coverage_report = coverage_generator.generate_coverage_report(spec)
            print(f"  总体覆盖率: {coverage_report.overall_coverage}%")
            print(f"  风险等级: {coverage_report.risk_assessment.get('overall_risk_level', 'unknown')}")
            
            print(f"\n  各类型覆盖率:")
            for type_name, mapping in coverage_report.coverage_by_type.items():
                if mapping.total_requirements > 0:
                    status = "🟢" if mapping.coverage_percentage >= 80 else "🟡" if mapping.coverage_percentage >= 50 else "🔴"
                    print(f"    {status} {mapping.spec_name}: {mapping.coverage_percentage}% ({mapping.covered_requirements}/{mapping.total_requirements})")
            
            if coverage_report.missing_coverage:
                print(f"\n  缺失覆盖 ({len(coverage_report.missing_coverage)}项):")
                for item in coverage_report.missing_coverage[:5]:
                    print(f"    - [{item['priority']}] {item['type']}: {item['item']}")
            
            if coverage_report.recommendations:
                print(f"\n  建议:")
                for rec in coverage_report.recommendations[:5]:
                    print(f"    {rec}")
            
            if args.output:
                coverage_output = {
                    "report_id": coverage_report.report_id,
                    "spec_id": coverage_report.spec_id,
                    "overall_coverage": coverage_report.overall_coverage,
                    "risk_level": coverage_report.risk_assessment.get("overall_risk_level"),
                    "coverage_by_type": {
                        k: {
                            "spec_name": v.spec_name,
                            "total": v.total_requirements,
                            "covered": v.covered_requirements,
                            "percentage": v.coverage_percentage
                        }
                        for k, v in coverage_report.coverage_by_type.items()
                    },
                    "missing_coverage": coverage_report.missing_coverage,
                    "recommendations": coverage_report.recommendations
                }
                output_path = args.output.replace(".", "_coverage.") if "." in args.output else f"{args.output}_coverage"
                output_path = f"{output_path}.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(coverage_output, f, ensure_ascii=False, indent=2)
                print(f"\n  覆盖率报告已导出到: {output_path}")
        
        if args.convert:
            format_map = {
                "yaml": SpecFormat.YAML,
                "json": SpecFormat.JSON,
                "markdown": SpecFormat.MARKDOWN,
                "dsl": SpecFormat.DSL,
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
    
    except FileNotFoundError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"解析错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
