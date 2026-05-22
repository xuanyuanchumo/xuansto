#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API一致性验证器 - Sanliu 技能（增强版）

提供全面的API一致性验证功能，包括：
- 前后端API自动比对
- 不一致接口智能识别
- 类型兼容性检查
- 安全性验证
- RESTful规范检查
- 版本兼容性检查
- 多格式报告生成

使用示例:
    python api_consistency_validator.py --frontend ./frontend --backend ./backend
    python api_consistency_validator.py --swagger ./api/swagger.json --backend ./backend
    python api_consistency_validator.py --output html --report-dir ./reports
"""

import ast
import difflib
import hashlib
import json
import logging
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


class InconsistencyType(Enum):
    """不一致类型枚举"""
    MISSING_ENDPOINT = "missing_endpoint"
    PARAMETER_MISMATCH = "parameter_mismatch"
    RETURN_TYPE_MISMATCH = "return_type_mismatch"
    HTTP_METHOD_MISMATCH = "http_method_mismatch"
    PATH_MISMATCH = "path_mismatch"
    MISSING_PARAMETER = "missing_parameter"
    EXTRA_PARAMETER = "extra_parameter"
    TYPE_MISMATCH = "type_mismatch"
    REQUIRED_MISMATCH = "required_mismatch"
    RESPONSE_SCHEMA_MISMATCH = "response_schema_mismatch"
    AUTH_MISMATCH = "auth_mismatch"
    VERSION_MISMATCH = "version_mismatch"
    NAMING_VIOLATION = "naming_violation"
    RESTFUL_VIOLATION = "restful_violation"
    DEPRECATED_API = "deprecated_api"
    SECURITY_ISSUE = "security_issue"
    DOCUMENTATION_MISSING = "documentation_missing"


class Severity(Enum):
    """严重程度枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class APISourceType(Enum):
    """API来源类型"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    SWAGGER = "swagger"
    OPENAPI = "openapi"


class ValidationRuleType(Enum):
    """验证规则类型"""
    TYPE_COMPATIBILITY = "type_compatibility"
    SECURITY_CHECK = "security_check"
    RESTFUL_COMPLIANCE = "restful_compliance"
    NAMING_CONVENTION = "naming_convention"
    VERSION_COMPATIBILITY = "version_compatibility"
    DOCUMENTATION = "documentation"


@dataclass
class APIParameter:
    """API参数"""
    name: str
    param_type: str
    required: bool = True
    default: Optional[Any] = None
    description: str = ""
    location: str = "body"
    validation_rules: List[str] = field(default_factory=list)
    deprecated: bool = False
    example: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.param_type,
            "required": self.required,
            "default": self.default,
            "description": self.description,
            "location": self.location,
            "validation_rules": self.validation_rules,
            "deprecated": self.deprecated,
            "example": self.example
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, APIParameter):
            return False
        return (
            self.name == other.name
            and self.param_type == other.param_type
            and self.required == other.required
        )

    def is_type_compatible(self, other: "APIParameter") -> Tuple[bool, str]:
        """检查类型兼容性"""
        type_compatibility = {
            "str": ["string", "str", "text"],
            "int": ["integer", "int", "number"],
            "float": ["float", "double", "number"],
            "bool": ["boolean", "bool"],
            "list": ["array", "list", "List"],
            "dict": ["object", "dict", "Dict"],
            "any": ["any", "Any", "*"]
        }
        
        self_type = self.param_type.lower()
        other_type = other.param_type.lower()
        
        if self_type == other_type:
            return True, ""
        
        for base_type, compatible_types in type_compatibility.items():
            if self_type in compatible_types and other_type in compatible_types:
                return True, f"类型兼容: {self.param_type} <-> {other.param_type}"
        
        return False, f"类型不兼容: {self.param_type} vs {other.param_type}"


@dataclass
class APIResponse:
    """API响应"""
    status_code: int
    content_type: str = "application/json"
    schema: Optional[Dict[str, Any]] = None
    description: str = ""
    headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status_code": self.status_code,
            "content_type": self.content_type,
            "schema": self.schema,
            "description": self.description,
            "headers": self.headers
        }


@dataclass
class APIEndpoint:
    """API端点"""
    path: str
    method: str
    parameters: List[APIParameter] = field(default_factory=list)
    responses: List[APIResponse] = field(default_factory=list)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    source_file: str = ""
    line_number: Optional[int] = None
    auth_required: bool = False
    auth_type: str = ""
    deprecated: bool = False
    version: str = ""
    rate_limit: Optional[int] = None
    cache_enabled: bool = False

    @property
    def normalized_path(self) -> str:
        normalized = self.path.strip("/")
        normalized = re.sub(r'\{(\w+)\}', r':\1', normalized)
        return f"/{normalized}"

    @property
    def signature(self) -> str:
        return f"{self.method.upper()} {self.normalized_path}"

    @property
    def path_params(self) -> List[str]:
        return re.findall(r'\{(\w+)\}|:(\w+)', self.path)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "method": self.method,
            "parameters": [p.to_dict() for p in self.parameters],
            "responses": [r.to_dict() for r in self.responses],
            "description": self.description,
            "tags": self.tags,
            "source_file": self.source_file,
            "line_number": self.line_number,
            "signature": self.signature,
            "auth_required": self.auth_required,
            "auth_type": self.auth_type,
            "deprecated": self.deprecated,
            "version": self.version
        }

    def get_similarity_score(self, other: "APIEndpoint") -> float:
        """计算与另一个端点的相似度"""
        scores = []
        
        path_score = SequenceMatcher(None, self.normalized_path.lower(), other.normalized_path.lower()).ratio()
        scores.append(path_score * 0.5)
        
        method_match = 1.0 if self.method.upper() == other.method.upper() else 0.0
        scores.append(method_match * 0.3)
        
        self_params = set(p.name for p in self.parameters)
        other_params = set(p.name for p in other.parameters)
        if self_params or other_params:
            param_score = len(self_params & other_params) / max(len(self_params | other_params), 1)
            scores.append(param_score * 0.2)
        
        return sum(scores)


@dataclass
class Inconsistency:
    """不一致问题"""
    inconsistency_type: InconsistencyType
    severity: Severity
    frontend_endpoint: Optional[APIEndpoint]
    backend_endpoint: Optional[APIEndpoint]
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    fix_suggestion: str = ""
    auto_fixable: bool = False
    impact_analysis: Dict[str, Any] = field(default_factory=dict)
    related_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.inconsistency_type.value,
            "severity": self.severity.value,
            "frontend_endpoint": self.frontend_endpoint.to_dict() if self.frontend_endpoint else None,
            "backend_endpoint": self.backend_endpoint.to_dict() if self.backend_endpoint else None,
            "description": self.description,
            "details": self.details,
            "fix_suggestion": self.fix_suggestion,
            "auto_fixable": self.auto_fixable,
            "impact_analysis": self.impact_analysis,
            "related_issues": self.related_issues
        }


@dataclass
class ValidationResult:
    """验证结果"""
    is_consistent: bool
    total_endpoints: int
    matched_endpoints: int
    inconsistencies: List[Inconsistency]
    frontend_only: List[APIEndpoint]
    backend_only: List[APIEndpoint]
    similarity_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    validation_rules_applied: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_consistent": self.is_consistent,
            "total_endpoints": self.total_endpoints,
            "matched_endpoints": self.matched_endpoints,
            "inconsistencies": [i.to_dict() for i in self.inconsistencies],
            "frontend_only": [e.to_dict() for e in self.frontend_only],
            "backend_only": [e.to_dict() for e in self.backend_only],
            "similarity_matrix": self.similarity_matrix,
            "validation_rules_applied": self.validation_rules_applied
        }


@dataclass
class ValidationReport:
    """验证报告"""
    timestamp: str
    frontend_source: str
    backend_source: str
    validation_result: ValidationResult
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "frontend_source": self.frontend_source,
            "backend_source": self.backend_source,
            "validation_result": self.validation_result.to_dict(),
            "summary": self.summary,
            "recommendations": self.recommendations,
            "statistics": self.statistics,
            "quality_metrics": self.quality_metrics
        }


class ValidationRule:
    """验证规则基类"""
    
    def __init__(self, rule_type: ValidationRuleType, description: str):
        self.rule_type = rule_type
        self.description = description
        self.enabled = True
    
    def validate(self, frontend: Optional[APIEndpoint], backend: Optional[APIEndpoint]) -> List[Inconsistency]:
        raise NotImplementedError


class TypeCompatibilityRule(ValidationRule):
    """类型兼容性验证规则"""
    
    TYPE_HIERARCHY = {
        "any": 0,
        "object": 1, "dict": 1,
        "array": 1, "list": 1,
        "string": 2, "str": 2,
        "number": 2, "int": 2, "float": 2,
        "boolean": 2, "bool": 2
    }
    
    def __init__(self):
        super().__init__(
            ValidationRuleType.TYPE_COMPATIBILITY,
            "验证前后端参数类型的兼容性"
        )
    
    def validate(self, frontend: Optional[APIEndpoint], backend: Optional[APIEndpoint]) -> List[Inconsistency]:
        inconsistencies = []
        
        if not frontend or not backend:
            return inconsistencies
        
        fe_params = {p.name: p for p in frontend.parameters}
        be_params = {p.name: p for p in backend.parameters}
        
        for name, fe_param in fe_params.items():
            if name in be_params:
                be_param = be_params[name]
                is_compatible, message = fe_param.is_type_compatible(be_param)
                
                if not is_compatible:
                    inconsistencies.append(Inconsistency(
                        inconsistency_type=InconsistencyType.TYPE_MISMATCH,
                        severity=Severity.MEDIUM,
                        frontend_endpoint=frontend,
                        backend_endpoint=backend,
                        description=f"参数 '{name}' 类型不兼容: {message}",
                        details={
                            "frontend_type": fe_param.param_type,
                            "backend_type": be_param.param_type,
                            "parameter_name": name
                        },
                        fix_suggestion=f"统一参数 '{name}' 的类型定义，建议使用: {fe_param.param_type}",
                        auto_fixable=False
                    ))
        
        return inconsistencies


class SecurityValidationRule(ValidationRule):
    """安全性验证规则"""
    
    SENSITIVE_PARAMS = ["password", "token", "secret", "key", "credential", "auth"]
    UNSAFE_METHODS = ["POST", "PUT", "DELETE", "PATCH"]
    
    def __init__(self):
        super().__init__(
            ValidationRuleType.SECURITY_CHECK,
            "验证API安全性配置"
        )
    
    def validate(self, frontend: Optional[APIEndpoint], backend: Optional[APIEndpoint]) -> List[Inconsistency]:
        inconsistencies = []
        
        endpoint = backend or frontend
        if not endpoint:
            return inconsistencies
        
        for param in endpoint.parameters:
            if any(sensitive in param.name.lower() for sensitive in self.SENSITIVE_PARAMS):
                if param.location == "query":
                    inconsistencies.append(Inconsistency(
                        inconsistency_type=InconsistencyType.SECURITY_ISSUE,
                        severity=Severity.HIGH,
                        frontend_endpoint=frontend,
                        backend_endpoint=backend,
                        description=f"敏感参数 '{param.name}' 不应在URL查询参数中传递",
                        details={"parameter": param.name, "location": param.location},
                        fix_suggestion="将敏感参数移至请求体或使用Header传递",
                        auto_fixable=False
                    ))
        
        if endpoint.method.upper() in self.UNSAFE_METHODS:
            if not endpoint.auth_required and frontend and frontend.auth_required:
                inconsistencies.append(Inconsistency(
                    inconsistency_type=InconsistencyType.AUTH_MISMATCH,
                    severity=Severity.HIGH,
                    frontend_endpoint=frontend,
                    backend_endpoint=backend,
                    description=f"端点 {endpoint.signature} 缺少认证保护",
                    details={"method": endpoint.method, "auth_required": endpoint.auth_required},
                    fix_suggestion="为该端点添加认证要求",
                    auto_fixable=False
                ))
        
        return inconsistencies


class RESTfulComplianceRule(ValidationRule):
    """RESTful规范验证规则"""
    
    RESTFUL_PATTERNS = {
        "GET": {"should_have_body": False, "should_be_idempotent": True},
        "POST": {"should_have_body": True, "should_be_idempotent": False},
        "PUT": {"should_have_body": True, "should_be_idempotent": True},
        "PATCH": {"should_have_body": True, "should_be_idempotent": False},
        "DELETE": {"should_have_body": False, "should_be_idempotent": True}
    }
    
    RESOURCE_NAMING_PATTERN = re.compile(r'^/[a-z][a-z0-9-]*(?:/[a-z][a-z0-9-]*|/\{[a-zA-Z]+\})*$')
    
    def __init__(self):
        super().__init__(
            ValidationRuleType.RESTFUL_COMPLIANCE,
            "验证API是否符合RESTful规范"
        )
    
    def validate(self, frontend: Optional[APIEndpoint], backend: Optional[APIEndpoint]) -> List[Inconsistency]:
        inconsistencies = []
        
        endpoint = backend or frontend
        if not endpoint:
            return inconsistencies
        
        if not self.RESOURCE_NAMING_PATTERN.match(endpoint.normalized_path):
            inconsistencies.append(Inconsistency(
                inconsistency_type=InconsistencyType.RESTFUL_VIOLATION,
                severity=Severity.LOW,
                frontend_endpoint=frontend,
                backend_endpoint=backend,
                description=f"路径 '{endpoint.path}' 不符合RESTful命名规范",
                details={"path": endpoint.path},
                fix_suggestion="使用小写字母、连字符和路径参数，如: /users/{id}/posts",
                auto_fixable=False
            ))
        
        method_config = self.RESTFUL_PATTERNS.get(endpoint.method.upper())
        if method_config:
            has_body = any(p.location == "body" for p in endpoint.parameters)
            
            if method_config["should_have_body"] and not has_body:
                inconsistencies.append(Inconsistency(
                    inconsistency_type=InconsistencyType.RESTFUL_VIOLATION,
                    severity=Severity.INFO,
                    frontend_endpoint=frontend,
                    backend_endpoint=backend,
                    description=f"{endpoint.method} 请求通常应包含请求体",
                    details={"method": endpoint.method},
                    fix_suggestion="考虑添加请求体参数",
                    auto_fixable=False
                ))
        
        return inconsistencies


class NamingConventionRule(ValidationRule):
    """命名规范验证规则"""
    
    CAMEL_CASE = re.compile(r'^[a-z][a-zA-Z0-9]*$')
    SNAKE_CASE = re.compile(r'^[a-z][a-z0-9_]*$')
    PASCAL_CASE = re.compile(r'^[A-Z][a-zA-Z0-9]*$')
    
    def __init__(self, preferred_style: str = "snake_case"):
        super().__init__(
            ValidationRuleType.NAMING_CONVENTION,
            "验证API命名规范"
        )
        self.preferred_style = preferred_style
    
    def validate(self, frontend: Optional[APIEndpoint], backend: Optional[APIEndpoint]) -> List[Inconsistency]:
        inconsistencies = []
        
        endpoint = backend or frontend
        if not endpoint:
            return inconsistencies
        
        for param in endpoint.parameters:
            if not self._check_naming_style(param.name):
                inconsistencies.append(Inconsistency(
                    inconsistency_type=InconsistencyType.NAMING_VIOLATION,
                    severity=Severity.LOW,
                    frontend_endpoint=frontend,
                    backend_endpoint=backend,
                    description=f"参数 '{param.name}' 不符合命名规范 ({self.preferred_style})",
                    details={"parameter": param.name, "expected_style": self.preferred_style},
                    fix_suggestion=f"将参数名改为 {self.preferred_style} 格式",
                    auto_fixable=False
                ))
        
        return inconsistencies
    
    def _check_naming_style(self, name: str) -> bool:
        if self.preferred_style == "snake_case":
            return bool(self.SNAKE_CASE.match(name))
        elif self.preferred_style == "camelCase":
            return bool(self.CAMEL_CASE.match(name))
        elif self.preferred_style == "PascalCase":
            return bool(self.PASCAL_CASE.match(name))
        return True


class VersionCompatibilityRule(ValidationRule):
    """版本兼容性验证规则"""
    
    def __init__(self):
        super().__init__(
            ValidationRuleType.VERSION_COMPATIBILITY,
            "验证API版本兼容性"
        )
    
    def validate(self, frontend: Optional[APIEndpoint], backend: Optional[APIEndpoint]) -> List[Inconsistency]:
        inconsistencies = []
        
        if not frontend or not backend:
            return inconsistencies
        
        if frontend.version and backend.version:
            if frontend.version != backend.version:
                inconsistencies.append(Inconsistency(
                    inconsistency_type=InconsistencyType.VERSION_MISMATCH,
                    severity=Severity.MEDIUM,
                    frontend_endpoint=frontend,
                    backend_endpoint=backend,
                    description=f"API版本不匹配: 前端 {frontend.version} vs 后端 {backend.version}",
                    details={"frontend_version": frontend.version, "backend_version": backend.version},
                    fix_suggestion="确保前后端使用相同的API版本",
                    auto_fixable=False
                ))
        
        if backend and backend.deprecated:
            inconsistencies.append(Inconsistency(
                inconsistency_type=InconsistencyType.DEPRECATED_API,
                severity=Severity.HIGH,
                frontend_endpoint=frontend,
                backend_endpoint=backend,
                description=f"API {backend.signature} 已被标记为废弃",
                details={"deprecated": True},
                fix_suggestion="迁移到新的API版本",
                auto_fixable=False
            ))
        
        return inconsistencies


class FrontendAPIExtractor:
    """前端API提取器"""

    API_PATTERNS = {
        'fetch': r'fetch\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        'axios_get': r'axios\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        'axios_request': r'axios\s*\(\s*\{[^}]*url\s*:\s*[\'"`]([^\'"`]+)[\'"`]',
        'http_client': r'httpClient\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        'api_service': r'apiService\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        'request': r'request\s*\(\s*\{[^}]*url\s*:\s*[\'"`]([^\'"`]+)[\'"`]',
        'http': r'http\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
    }

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.endpoints: List[APIEndpoint] = []

    def extract(self, frontend_path: Path) -> List[APIEndpoint]:
        """提取前端API调用"""
        self.logger.info(f"开始提取前端API: {frontend_path}")
        self.endpoints = []

        js_files = list(frontend_path.rglob("*.js")) + \
                   list(frontend_path.rglob("*.jsx")) + \
                   list(frontend_path.rglob("*.ts")) + \
                   list(frontend_path.rglob("*.tsx")) + \
                   list(frontend_path.rglob("*.vue"))

        for js_file in js_files:
            self._extract_from_file(js_file)

        self.logger.info(f"前端API提取完成: {len(self.endpoints)} 个端点")
        return self.endpoints

    def _extract_from_file(self, file_path: Path) -> None:
        """从文件提取API"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self._extract_with_regex(file_path, content)

            if file_path.suffix in ['.ts', '.tsx']:
                self._extract_typescript_api(file_path, content)

            self._extract_auth_info(file_path, content)

        except Exception as e:
            self.logger.warning(f"提取文件失败 {file_path}: {e}")

    def _extract_with_regex(self, file_path: Path, content: str) -> None:
        """使用正则表达式提取API"""
        for pattern_name, pattern in self.API_PATTERNS.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if pattern_name == 'fetch':
                    path = match.group(1)
                    method = self._infer_method_from_context(content, match.start())
                elif pattern_name in ['axios_get', 'http_client', 'api_service', 'http']:
                    method = match.group(1).upper()
                    path = match.group(2)
                else:
                    path = match.group(1)
                    method = self._infer_method_from_context(content, match.start())

                if self._is_api_path(path):
                    auth_required = self._check_auth_in_context(content, match.start())
                    
                    endpoint = APIEndpoint(
                        path=path,
                        method=method,
                        source_file=str(file_path),
                        line_number=content[:match.start()].count('\n') + 1,
                        auth_required=auth_required
                    )
                    self._add_endpoint(endpoint)

    def _infer_method_from_context(self, content: str, position: int) -> str:
        """从上下文推断HTTP方法"""
        context_start = max(0, position - 200)
        context = content[context_start:position].lower()
        
        if 'post' in context or 'create' in context or 'add' in context:
            return 'POST'
        elif 'put' in context or 'update' in context:
            return 'PUT'
        elif 'delete' in context or 'remove' in context:
            return 'DELETE'
        elif 'patch' in context:
            return 'PATCH'
        
        return 'GET'

    def _check_auth_in_context(self, content: str, position: int) -> bool:
        """检查上下文中是否有认证信息"""
        context_start = max(0, position - 500)
        context_end = min(len(content), position + 500)
        context = content[context_start:context_end].lower()
        
        auth_indicators = ['authorization', 'bearer', 'token', 'x-auth', 'auth-header', 'withcredentials']
        return any(indicator in context for indicator in auth_indicators)

    def _extract_typescript_api(self, file_path: Path, content: str) -> None:
        """提取TypeScript API定义"""
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    self._extract_api_from_call(file_path, node)
        except SyntaxError:
            pass

    def _extract_api_from_call(self, file_path: Path, node: ast.Call) -> None:
        """从函数调用提取API"""
        if isinstance(node.func, ast.Attribute):
            method_map = {
                'get': 'GET', 'post': 'POST', 'put': 'PUT',
                'delete': 'DELETE', 'patch': 'PATCH'
            }
            method = method_map.get(node.func.attr.lower())
            if method and node.args:
                path = self._extract_string_value(node.args[0])
                if path and self._is_api_path(path):
                    endpoint = APIEndpoint(
                        path=path,
                        method=method,
                        source_file=str(file_path),
                        line_number=node.lineno
                    )
                    self._add_endpoint(endpoint)

    def _extract_auth_info(self, file_path: Path, content: str) -> None:
        """提取认证信息"""
        auth_patterns = [
            r'headers\s*:\s*\{[^}]*[\'"]Authorization[\'"]\s*:',
            r'Bearer\s+\w+',
            r'x-auth-token\s*:',
        ]
        
        for pattern in auth_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                for endpoint in self.endpoints:
                    if endpoint.source_file == str(file_path):
                        endpoint.auth_required = True

    def _extract_string_value(self, node: ast.AST) -> Optional[str]:
        """提取字符串值"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.JoinedStr):
            parts = []
            for value in node.values:
                if isinstance(value, ast.Constant):
                    parts.append(str(value.value))
            return ''.join(parts)
        return None

    def _is_api_path(self, path: str) -> bool:
        """判断是否是API路径"""
        if not path:
            return False
        api_indicators = ['/api/', '/v1/', '/v2/', '/rest/', '/graphql', '/backend/']
        return any(ind in path for ind in api_indicators) or path.startswith('/')

    def _add_endpoint(self, endpoint: APIEndpoint) -> None:
        """添加端点（去重）"""
        existing = next(
            (e for e in self.endpoints if e.signature == endpoint.signature),
            None
        )
        if not existing:
            self.endpoints.append(endpoint)


class BackendAPIExtractor:
    """后端API提取器"""

    FRAMEWORK_DECORATORS = {
        'flask': ['route', 'get', 'post', 'put', 'delete', 'patch'],
        'fastapi': ['get', 'post', 'put', 'delete', 'patch', 'api_route'],
        'django': ['route', 'path', 'url'],
        'tornado': ['route'],
    }

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.endpoints: List[APIEndpoint] = []

    def extract(self, backend_path: Path) -> List[APIEndpoint]:
        """提取后端API定义"""
        self.logger.info(f"开始提取后端API: {backend_path}")
        self.endpoints = []

        py_files = list(backend_path.rglob("*.py"))

        for py_file in py_files:
            self._extract_from_file(py_file)

        self.logger.info(f"后端API提取完成: {len(self.endpoints)} 个端点")
        return self.endpoints

    def _extract_from_file(self, file_path: Path) -> None:
        """从文件提取API"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)
            self._extract_decorators(file_path, tree, source)
            self._extract_function_definitions(file_path, tree)

        except Exception as e:
            self.logger.warning(f"提取文件失败 {file_path}: {e}")

    def _extract_decorators(self, file_path: Path, tree: ast.AST, source: str) -> None:
        """提取装饰器定义的API"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    endpoint = self._parse_decorator(file_path, decorator, node, source)
                    if endpoint:
                        self._add_endpoint(endpoint)

    def _parse_decorator(
        self,
        file_path: Path,
        decorator: ast.expr,
        func_node: ast.FunctionDef,
        source: str
    ) -> Optional[APIEndpoint]:
        """解析装饰器"""
        decorator_name = self._get_decorator_name(decorator)
        if not decorator_name:
            return None

        method = self._get_http_method(decorator_name)
        if not method:
            return None

        path = self._extract_decorator_path(decorator)
        if not path:
            return None

        parameters = self._extract_parameters(func_node)
        responses = self._extract_responses(func_node)
        
        auth_required, auth_type = self._extract_auth_info(func_node, source)

        return APIEndpoint(
            path=path,
            method=method,
            parameters=parameters,
            responses=responses,
            source_file=str(file_path),
            line_number=decorator.lineno,
            description=ast.get_docstring(func_node) or "",
            auth_required=auth_required,
            auth_type=auth_type
        )

    def _get_decorator_name(self, decorator: ast.expr) -> Optional[str]:
        """获取装饰器名称"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        return None

    def _get_http_method(self, decorator_name: str) -> Optional[str]:
        """获取HTTP方法"""
        method_map = {
            'get': 'GET', 'post': 'POST', 'put': 'PUT',
            'delete': 'DELETE', 'patch': 'PATCH', 'route': None
        }

        lower_name = decorator_name.lower()
        if lower_name in method_map:
            return method_map[lower_name]

        for framework, decorators in self.FRAMEWORK_DECORATORS.items():
            if lower_name in [d.lower() for d in decorators]:
                return method_map.get(lower_name)

        return None

    def _extract_decorator_path(self, decorator: ast.expr) -> Optional[str]:
        """提取装饰器中的路径"""
        if isinstance(decorator, ast.Call):
            if decorator.args:
                return self._extract_string_value(decorator.args[0])
            for keyword in decorator.keywords:
                if keyword.arg in ['path', 'url', 'route']:
                    return self._extract_string_value(keyword.value)
        return None

    def _extract_string_value(self, node: ast.AST) -> Optional[str]:
        """提取字符串值"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def _extract_parameters(self, func_node: ast.FunctionDef) -> List[APIParameter]:
        """提取函数参数"""
        parameters = []

        for arg in func_node.args.args:
            if arg.arg in ['self', 'cls', 'request']:
                continue

            param_type = "any"
            if arg.annotation:
                param_type = self._extract_type_name(arg.annotation)

            location = self._determine_param_location(arg.arg, func_node)

            parameters.append(APIParameter(
                name=arg.arg,
                param_type=param_type,
                required=True,
                location=location
            ))

        return parameters

    def _determine_param_location(self, param_name: str, func_node: ast.FunctionDef) -> str:
        """确定参数位置"""
        source = ast.unparse(func_node) if hasattr(ast, 'unparse') else ""
        
        if 'Path' in source or param_name in ['id', 'pk']:
            return 'path'
        elif 'Query' in source or param_name in ['page', 'limit', 'offset', 'search']:
            return 'query'
        elif 'Header' in source:
            return 'header'
        elif 'Cookie' in source:
            return 'cookie'
        
        return 'body'

    def _extract_responses(self, func_node: ast.FunctionDef) -> List[APIResponse]:
        """提取响应信息"""
        responses = []
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return) and node.value:
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        if node.value.func.id in ['JSONResponse', 'Response']:
                            responses.append(APIResponse(
                                status_code=200,
                                content_type="application/json"
                            ))
        
        if not responses:
            responses.append(APIResponse(status_code=200))
        
        return responses

    def _extract_auth_info(self, func_node: ast.FunctionDef, source: str) -> Tuple[bool, str]:
        """提取认证信息"""
        auth_required = False
        auth_type = ""
        
        for decorator in func_node.decorator_list:
            decorator_name = self._get_decorator_name(decorator)
            if decorator_name and decorator_name.lower() in ['requires_auth', 'login_required', 'authenticated']:
                auth_required = True
                auth_type = "bearer"
        
        if 'Depends(' in source and 'get_current_user' in source:
            auth_required = True
            auth_type = "bearer"
        
        if 'HTTPAuthorizationCredentials' in source:
            auth_required = True
            auth_type = "bearer"
        
        return auth_required, auth_type

    def _extract_type_name(self, annotation: ast.expr) -> str:
        """提取类型名称"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif hasattr(ast, 'unparse'):
            return ast.unparse(annotation)
        return "any"

    def _extract_function_definitions(self, file_path: Path, tree: ast.AST) -> None:
        """提取函数定义中的API"""
        pass

    def _add_endpoint(self, endpoint: APIEndpoint) -> None:
        """添加端点（去重）"""
        existing = next(
            (e for e in self.endpoints if e.signature == endpoint.signature),
            None
        )
        if not existing:
            self.endpoints.append(endpoint)


class SwaggerParser:
    """Swagger/OpenAPI解析器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.endpoints: List[APIEndpoint] = []

    def parse(self, swagger_path: Path) -> List[APIEndpoint]:
        """解析Swagger/OpenAPI文件"""
        self.logger.info(f"开始解析Swagger文件: {swagger_path}")
        self.endpoints = []

        try:
            with open(swagger_path, 'r', encoding='utf-8') as f:
                spec = json.load(f)

            self._parse_spec(spec)

        except Exception as e:
            self.logger.error(f"解析Swagger文件失败: {e}")

        self.logger.info(f"Swagger解析完成: {len(self.endpoints)} 个端点")
        return self.endpoints

    def _parse_spec(self, spec: Dict[str, Any]) -> None:
        """解析规范"""
        paths = spec.get('paths', {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    continue

                endpoint = self._create_endpoint(path, method, details)
                self.endpoints.append(endpoint)

    def _create_endpoint(
        self,
        path: str,
        method: str,
        details: Dict[str, Any]
    ) -> APIEndpoint:
        """创建端点"""
        parameters = self._parse_parameters(details.get('parameters', []))
        responses = self._parse_responses(details.get('responses', {}))
        
        security = details.get('security', [])
        auth_required = len(security) > 0
        auth_type = ""
        if security:
            for sec in security:
                if 'bearerAuth' in sec:
                    auth_type = "bearer"
                elif 'apiKey' in sec:
                    auth_type = "apiKey"
        
        deprecated = details.get('deprecated', False)

        return APIEndpoint(
            path=path,
            method=method.upper(),
            parameters=parameters,
            responses=responses,
            description=details.get('summary', ''),
            tags=details.get('tags', []),
            auth_required=auth_required,
            auth_type=auth_type,
            deprecated=deprecated
        )

    def _parse_parameters(self, params: List[Dict[str, Any]]) -> List[APIParameter]:
        """解析参数"""
        parameters = []

        for param in params:
            parameters.append(APIParameter(
                name=param.get('name', ''),
                param_type=param.get('schema', {}).get('type', 'any'),
                required=param.get('required', False),
                description=param.get('description', ''),
                location=param.get('in', 'body'),
                deprecated=param.get('deprecated', False),
                example=param.get('example')
            ))

        return parameters

    def _parse_responses(self, responses: Dict[str, Any]) -> List[APIResponse]:
        """解析响应"""
        result = []

        for code, details in responses.items():
            try:
                status_code = int(code)
            except ValueError:
                continue

            result.append(APIResponse(
                status_code=status_code,
                description=details.get('description', ''),
                schema=details.get('schema'),
                content_type=details.get('content', {}).get('application/json', {}).get('schema', {})
            ))

        return result


class IntelligentAPIComparator:
    """智能API比较器"""

    PATH_PARAM_PATTERN = re.compile(r'\{(\w+)\}|:(\w+)')
    
    SIMILARITY_THRESHOLD = 0.7

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.inconsistencies: List[Inconsistency] = []
        self.similarity_matrix: Dict[str, Dict[str, float]] = {}
        self.validation_rules: List[ValidationRule] = []

    def add_validation_rule(self, rule: ValidationRule) -> None:
        """添加验证规则"""
        self.validation_rules.append(rule)

    def compare(
        self,
        frontend_apis: List[APIEndpoint],
        backend_apis: List[APIEndpoint]
    ) -> ValidationResult:
        """比较前后端API"""
        self.logger.info("开始智能比较前后端API...")
        self.inconsistencies = {}
        self.similarity_matrix = {}

        frontend_map = self._build_api_map(frontend_apis)
        backend_map = self._build_api_map(backend_apis)

        matched = []
        frontend_only = []
        backend_only = []
        rules_applied = []

        for sig, fe_endpoint in frontend_map.items():
            matched_be = self._find_matching_backend(sig, backend_map)

            if matched_be:
                matched.append(fe_endpoint)
                self._compare_endpoints(fe_endpoint, matched_be)
            else:
                similar_endpoints = self._find_similar_endpoints(fe_endpoint, backend_map)
                if similar_endpoints:
                    self._add_similarity_suggestion(fe_endpoint, similar_endpoints)
                else:
                    frontend_only.append(fe_endpoint)
                    self._add_missing_backend_inconsistency(fe_endpoint)

        for sig, be_endpoint in backend_map.items():
            if not self._has_frontend_match(sig, frontend_map):
                backend_only.append(be_endpoint)

        for rule in self.validation_rules:
            if rule.enabled:
                rules_applied.append(rule.description)
                for fe in frontend_map.values():
                    matched_be = self._find_matching_backend(fe.signature, backend_map)
                    rule_inconsistencies = rule.validate(fe, matched_be)
                    for inc in rule_inconsistencies:
                        inc_key = self._get_inconsistency_key(inc)
                        if inc_key not in self.inconsistencies:
                            self.inconsistencies[inc_key] = inc

        is_consistent = len(self.inconsistencies) == 0
        inconsistencies_list = list(self.inconsistencies.values())

        return ValidationResult(
            is_consistent=is_consistent,
            total_endpoints=len(frontend_map) + len(backend_map),
            matched_endpoints=len(matched),
            inconsistencies=inconsistencies_list,
            frontend_only=frontend_only,
            backend_only=backend_only,
            similarity_matrix=self.similarity_matrix,
            validation_rules_applied=rules_applied
        )

    def _get_inconsistency_key(self, inc: Inconsistency) -> str:
        """生成不一致问题的唯一键"""
        fe_sig = inc.frontend_endpoint.signature if inc.frontend_endpoint else "none"
        be_sig = inc.backend_endpoint.signature if inc.backend_endpoint else "none"
        return f"{inc.inconsistency_type.value}:{fe_sig}:{be_sig}"

    def _build_api_map(self, apis: List[APIEndpoint]) -> Dict[str, APIEndpoint]:
        """构建API映射"""
        return {api.signature: api for api in apis}

    def _find_matching_backend(
        self,
        frontend_sig: str,
        backend_map: Dict[str, APIEndpoint]
    ) -> Optional[APIEndpoint]:
        """查找匹配的后端API"""
        fe_method, fe_path = frontend_sig.split(' ', 1)

        for be_sig, be_endpoint in backend_map.items():
            be_method, be_path = be_sig.split(' ', 1)

            if fe_method == be_method and self._paths_match(fe_path, be_path):
                return be_endpoint

        return None

    def _find_similar_endpoints(
        self,
        frontend: APIEndpoint,
        backend_map: Dict[str, APIEndpoint]
    ) -> List[Tuple[APIEndpoint, float]]:
        """查找相似的端点"""
        similar = []
        
        for be_sig, be_endpoint in backend_map.items():
            score = frontend.get_similarity_score(be_endpoint)
            if score >= self.SIMILARITY_THRESHOLD:
                similar.append((be_endpoint, score))
                self.similarity_matrix[frontend.signature] = {
                    be_endpoint.signature: score
                }
        
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar[:3]

    def _add_similarity_suggestion(
        self,
        frontend: APIEndpoint,
        similar_endpoints: List[Tuple[APIEndpoint, float]]
    ) -> None:
        """添加相似性建议"""
        suggestions = []
        for endpoint, score in similar_endpoints:
            suggestions.append(f"{endpoint.signature} (相似度: {score:.0%})")
        
        inc = Inconsistency(
            inconsistency_type=InconsistencyType.MISSING_ENDPOINT,
            severity=Severity.MEDIUM,
            frontend_endpoint=frontend,
            backend_endpoint=None,
            description=f"前端API {frontend.signature} 在后端未找到精确匹配，但存在相似端点",
            details={"similar_endpoints": suggestions},
            fix_suggestion=f"检查是否应该使用以下端点之一: {', '.join(suggestions)}",
            auto_fixable=False
        )
        inc_key = self._get_inconsistency_key(inc)
        self.inconsistencies[inc_key] = inc

    def _paths_match(self, path1: str, path2: str) -> bool:
        """比较路径是否匹配"""
        normalized1 = self._normalize_path_for_comparison(path1)
        normalized2 = self._normalize_path_for_comparison(path2)
        return normalized1 == normalized2

    def _normalize_path_for_comparison(self, path: str) -> str:
        """规范化路径用于比较"""
        normalized = self.PATH_PARAM_PATTERN.sub(':param', path)
        return normalized.rstrip('/').lower()

    def _has_frontend_match(
        self,
        backend_sig: str,
        frontend_map: Dict[str, APIEndpoint]
    ) -> bool:
        """检查是否有前端匹配"""
        be_method, be_path = backend_sig.split(' ', 1)

        for fe_sig in frontend_map:
            fe_method, fe_path = fe_sig.split(' ', 1)
            if fe_method == be_method and self._paths_match(fe_path, be_path):
                return True

        return False

    def _compare_endpoints(
        self,
        frontend: APIEndpoint,
        backend: APIEndpoint
    ) -> None:
        """比较端点详情"""
        self._compare_parameters(frontend, backend)
        self._compare_responses(frontend, backend)
        self._compare_auth(frontend, backend)

    def _compare_parameters(
        self,
        frontend: APIEndpoint,
        backend: APIEndpoint
    ) -> None:
        """比较参数"""
        fe_params = {p.name: p for p in frontend.parameters}
        be_params = {p.name: p for p in backend.parameters}

        for name, fe_param in fe_params.items():
            if name not in be_params:
                inc = Inconsistency(
                    inconsistency_type=InconsistencyType.MISSING_PARAMETER,
                    severity=Severity.HIGH,
                    frontend_endpoint=frontend,
                    backend_endpoint=backend,
                    description=f"后端缺少参数: {name}",
                    details={"parameter": fe_param.to_dict()},
                    fix_suggestion=f"在后端API中添加参数 '{name}'",
                    auto_fixable=False
                )
                inc_key = self._get_inconsistency_key(inc)
                self.inconsistencies[inc_key] = inc
            else:
                be_param = be_params[name]
                if fe_param.param_type != be_param.param_type:
                    is_compatible, _ = fe_param.is_type_compatible(be_param)
                    if not is_compatible:
                        inc = Inconsistency(
                            inconsistency_type=InconsistencyType.TYPE_MISMATCH,
                            severity=Severity.MEDIUM,
                            frontend_endpoint=frontend,
                            backend_endpoint=backend,
                            description=f"参数类型不匹配: {name}",
                            details={
                                "frontend_type": fe_param.param_type,
                                "backend_type": be_param.param_type
                            },
                            fix_suggestion=f"统一参数 '{name}' 的类型",
                            auto_fixable=False
                        )
                        inc_key = self._get_inconsistency_key(inc)
                        self.inconsistencies[inc_key] = inc

                if fe_param.required != be_param.required:
                    inc = Inconsistency(
                        inconsistency_type=InconsistencyType.REQUIRED_MISMATCH,
                        severity=Severity.MEDIUM,
                        frontend_endpoint=frontend,
                        backend_endpoint=backend,
                        description=f"参数必填性不匹配: {name}",
                        details={
                            "frontend_required": fe_param.required,
                            "backend_required": be_param.required
                        },
                        fix_suggestion=f"统一参数 '{name}' 的必填性",
                        auto_fixable=False
                    )
                    inc_key = self._get_inconsistency_key(inc)
                    self.inconsistencies[inc_key] = inc

        for name in be_params:
            if name not in fe_params:
                inc = Inconsistency(
                    inconsistency_type=InconsistencyType.EXTRA_PARAMETER,
                    severity=Severity.LOW,
                    frontend_endpoint=frontend,
                    backend_endpoint=backend,
                    description=f"后端有额外参数: {name}",
                    details={"parameter": be_params[name].to_dict()},
                    fix_suggestion=f"确认参数 '{name}' 是否需要在前端使用",
                    auto_fixable=False
                )
                inc_key = self._get_inconsistency_key(inc)
                self.inconsistencies[inc_key] = inc

    def _compare_responses(
        self,
        frontend: APIEndpoint,
        backend: APIEndpoint
    ) -> None:
        """比较响应"""
        if not frontend.responses and backend.responses:
            return

        fe_status_codes = {r.status_code for r in frontend.responses}
        be_status_codes = {r.status_code for r in backend.responses}

        missing_codes = fe_status_codes - be_status_codes
        if missing_codes:
            inc = Inconsistency(
                inconsistency_type=InconsistencyType.RESPONSE_SCHEMA_MISMATCH,
                severity=Severity.MEDIUM,
                frontend_endpoint=frontend,
                backend_endpoint=backend,
                description=f"后端缺少响应状态码: {missing_codes}",
                details={"missing_status_codes": list(missing_codes)},
                fix_suggestion="在后端添加对应的响应状态码处理",
                auto_fixable=False
            )
            inc_key = self._get_inconsistency_key(inc)
            self.inconsistencies[inc_key] = inc

    def _compare_auth(
        self,
        frontend: APIEndpoint,
        backend: APIEndpoint
    ) -> None:
        """比较认证配置"""
        if frontend.auth_required != backend.auth_required:
            inc = Inconsistency(
                inconsistency_type=InconsistencyType.AUTH_MISMATCH,
                severity=Severity.HIGH,
                frontend_endpoint=frontend,
                backend_endpoint=backend,
                description="前后端认证配置不一致",
                details={
                    "frontend_auth": frontend.auth_required,
                    "backend_auth": backend.auth_required
                },
                fix_suggestion="统一前后端的认证配置",
                auto_fixable=False
            )
            inc_key = self._get_inconsistency_key(inc)
            self.inconsistencies[inc_key] = inc

    def _add_missing_backend_inconsistency(self, frontend: APIEndpoint) -> None:
        """添加缺少后端的不一致"""
        inc = Inconsistency(
            inconsistency_type=InconsistencyType.MISSING_ENDPOINT,
            severity=Severity.CRITICAL,
            frontend_endpoint=frontend,
            backend_endpoint=None,
            description=f"后端缺少API端点: {frontend.signature}",
            details={},
            fix_suggestion=f"在后端实现API端点: {frontend.method} {frontend.path}",
            auto_fixable=False
        )
        inc_key = self._get_inconsistency_key(inc)
        self.inconsistencies[inc_key] = inc


class FixSuggestionGenerator:
    """修复建议生成器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def generate(self, inconsistencies: List[Inconsistency]) -> List[str]:
        """生成修复建议"""
        suggestions = []

        grouped = self._group_by_type(inconsistencies)

        for inc_type, incs in grouped.items():
            suggestion = self._generate_type_suggestion(inc_type, incs)
            if suggestion:
                suggestions.append(suggestion)

        critical = [i for i in inconsistencies if i.severity == Severity.CRITICAL]
        if critical:
            suggestions.insert(0, f"【紧急】发现 {len(critical)} 个严重问题需要立即处理")

        auto_fixable = [i for i in inconsistencies if i.auto_fixable]
        if auto_fixable:
            suggestions.append(f"💡 {len(auto_fixable)} 个问题可以自动修复")

        return suggestions

    def _group_by_type(
        self,
        inconsistencies: List[Inconsistency]
    ) -> Dict[InconsistencyType, List[Inconsistency]]:
        """按类型分组"""
        grouped: Dict[InconsistencyType, List[Inconsistency]] = defaultdict(list)
        for inc in inconsistencies:
            grouped[inc.inconsistency_type].append(inc)
        return grouped

    def _generate_type_suggestion(
        self,
        inc_type: InconsistencyType,
        inconsistencies: List[Inconsistency]
    ) -> Optional[str]:
        """生成类型建议"""
        count = len(inconsistencies)

        suggestions_map = {
            InconsistencyType.MISSING_ENDPOINT: (
                f"🔴 需要实现 {count} 个缺失的后端API端点"
            ),
            InconsistencyType.PARAMETER_MISMATCH: (
                f"🟠 需要修复 {count} 个参数不匹配的问题"
            ),
            InconsistencyType.TYPE_MISMATCH: (
                f"🟡 需要统一 {count} 个参数的类型定义"
            ),
            InconsistencyType.REQUIRED_MISMATCH: (
                f"🟡 需要统一 {count} 个参数的必填性设置"
            ),
            InconsistencyType.MISSING_PARAMETER: (
                f"🟠 后端需要添加 {count} 个缺失的参数"
            ),
            InconsistencyType.EXTRA_PARAMETER: (
                f"🔵 需要确认 {count} 个额外参数的使用情况"
            ),
            InconsistencyType.RESPONSE_SCHEMA_MISMATCH: (
                f"🟠 需要修复 {count} 个响应模式不匹配的问题"
            ),
            InconsistencyType.AUTH_MISMATCH: (
                f"🔴 需要统一 {count} 个端点的认证配置"
            ),
            InconsistencyType.SECURITY_ISSUE: (
                f"🔴 发现 {count} 个安全问题需要修复"
            ),
            InconsistencyType.RESTFUL_VIOLATION: (
                f"🔵 发现 {count} 个RESTful规范违反"
            ),
            InconsistencyType.NAMING_VIOLATION: (
                f"🔵 发现 {count} 个命名规范违反"
            ),
            InconsistencyType.DEPRECATED_API: (
                f"🟠 发现 {count} 个已废弃的API需要迁移"
            ),
        }

        return suggestions_map.get(inc_type)


class ReportGenerator:
    """报告生成器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_report(self, report: ValidationReport, filename: str = "api_consistency_report.html") -> str:
        """生成HTML格式报告"""
        report_path = self.output_dir / filename
        
        html_content = self._build_html_report(report)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_path)

    def _build_html_report(self, report: ValidationReport) -> str:
        """构建HTML报告内容"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        severity_colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#17a2b8",
            "info": "#6c757d"
        }
        
        severity_icons = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵",
            "info": "⚪"
        }
        
        inconsistencies_html = ""
        for inc in report.validation_result.inconsistencies[:50]:
            severity = inc.severity.value
            color = severity_colors.get(severity, "#6c757d")
            icon = severity_icons.get(severity, "⚪")
            
            fe_info = ""
            if inc.frontend_endpoint:
                fe_info = f"<div class='endpoint-info'>前端: {inc.frontend_endpoint.signature}</div>"
            
            be_info = ""
            if inc.backend_endpoint:
                be_info = f"<div class='endpoint-info'>后端: {inc.backend_endpoint.signature}</div>"
            
            inconsistencies_html += f"""
            <div class="issue-item severity-{severity}">
                <div class="issue-header">
                    <span class="severity-badge" style="background-color: {color}">{icon} {severity.upper()}</span>
                    <span class="issue-type">{inc.inconsistency_type.value}</span>
                </div>
                {fe_info}
                {be_info}
                <div class="issue-message">{inc.description}</div>
                <div class="issue-suggestion">💡 {inc.fix_suggestion}</div>
            </div>
            """
        
        recommendations_html = ""
        for rec in report.recommendations:
            recommendations_html += f"<li>{rec}</li>"
        
        quality_score = report.quality_metrics.get('consistency_score', 0)
        quality_color = "#28a745" if quality_score >= 80 else "#ffc107" if quality_score >= 60 else "#dc3545"
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API一致性验证报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .timestamp {{ opacity: 0.8; }}
        .quality-score {{ text-align: center; padding: 20px; }}
        .quality-score .score {{ font-size: 48px; font-weight: bold; color: {quality_color}; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; }}
        .stat-card h3 {{ font-size: 14px; color: #666; margin-bottom: 10px; }}
        .stat-card .value {{ font-size: 32px; font-weight: bold; color: #333; }}
        .stat-card.danger .value {{ color: #dc3545; }}
        .stat-card.warning .value {{ color: #ffc107; }}
        .stat-card.success .value {{ color: #28a745; }}
        .section {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .section h2 {{ font-size: 20px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #eee; }}
        .issue-item {{ padding: 15px; margin-bottom: 10px; border-radius: 8px; background: #f8f9fa; border-left: 4px solid #ccc; }}
        .issue-item.severity-critical {{ border-left-color: #dc3545; background: #fff5f5; }}
        .issue-item.severity-high {{ border-left-color: #fd7e14; background: #fff8f0; }}
        .issue-item.severity-medium {{ border-left-color: #ffc107; background: #fffdf0; }}
        .issue-item.severity-low {{ border-left-color: #17a2b8; background: #f0faff; }}
        .issue-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
        .severity-badge {{ padding: 4px 12px; border-radius: 4px; color: white; font-size: 11px; font-weight: bold; }}
        .issue-type {{ font-family: monospace; font-size: 12px; color: #666; background: #e9ecef; padding: 2px 8px; border-radius: 4px; }}
        .endpoint-info {{ font-family: monospace; font-size: 12px; color: #666; margin: 5px 0; }}
        .issue-message {{ font-weight: 500; margin-bottom: 5px; }}
        .issue-suggestion {{ font-size: 14px; color: #666; }}
        .recommendations ul {{ list-style: none; }}
        .recommendations li {{ padding: 10px; margin-bottom: 8px; background: #e8f5e9; border-radius: 6px; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .chart-container {{ display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px; }}
        .chart {{ flex: 1; min-width: 300px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔌 API一致性验证报告</h1>
            <div class="timestamp">生成时间: {timestamp}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card quality-score">
                <h3>一致性评分</h3>
                <div class="score">{quality_score:.1f}%</div>
            </div>
            <div class="stat-card {'danger' if report.summary.get('total_inconsistencies', 0) > 10 else 'warning' if report.summary.get('total_inconsistencies', 0) > 0 else 'success'}">
                <h3>不一致问题</h3>
                <div class="value">{report.summary.get('total_inconsistencies', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>前端端点</h3>
                <div class="value">{report.summary.get('frontend_endpoint_count', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>后端端点</h3>
                <div class="value">{report.summary.get('backend_endpoint_count', 0)}</div>
            </div>
            <div class="stat-card success">
                <h3>匹配端点</h3>
                <div class="value">{report.validation_result.matched_endpoints}</div>
            </div>
            <div class="stat-card {'danger' if report.summary.get('unmatched_frontend', 0) > 0 else 'success'}">
                <h3>未匹配前端</h3>
                <div class="value">{report.summary.get('unmatched_frontend', 0)}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 不一致详情</h2>
            {inconsistencies_html if inconsistencies_html else '<p class="no-issues">✅ 未发现不一致问题</p>'}
        </div>
        
        {f'''<div class="section recommendations">
            <h2>💡 修复建议</h2>
            <ul>{recommendations_html}</ul>
        </div>''' if recommendations_html else ''}
        
        <div class="footer">
            由 API Consistency Validator 生成 | Sanliu 技能
        </div>
    </div>
</body>
</html>"""
        
        return html

    def generate_markdown_report(self, report: ValidationReport, filename: str = "api_consistency_report.md") -> str:
        """生成Markdown格式报告"""
        report_path = self.output_dir / filename
        
        md_content = self._build_markdown_report(report)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(report_path)

    def _build_markdown_report(self, report: ValidationReport) -> str:
        """构建Markdown报告内容"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        lines = [
            "# 🔌 API一致性验证报告",
            "",
            f"**生成时间**: {timestamp}",
            f"**前端源**: {report.frontend_source}",
            f"**后端源**: {report.backend_source}",
            "",
            "## 📊 概览",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 一致性评分 | {report.quality_metrics.get('consistency_score', 0):.1f}% |",
            f"| 总端点数 | {report.validation_result.total_endpoints} |",
            f"| 匹配端点 | {report.validation_result.matched_endpoints} |",
            f"| 不一致问题 | {report.summary.get('total_inconsistencies', 0)} |",
            f"| 前端端点 | {report.summary.get('frontend_endpoint_count', 0)} |",
            f"| 后端端点 | {report.summary.get('backend_endpoint_count', 0)} |",
            f"| 未匹配前端 | {report.summary.get('unmatched_frontend', 0)} |",
            f"| 未匹配后端 | {report.summary.get('unmatched_backend', 0)} |",
            ""
        ]
        
        severity_breakdown = report.summary.get('severity_breakdown', {})
        if severity_breakdown:
            lines.extend([
                "### 按严重程度分布",
                "",
                "| 严重程度 | 数量 |",
                "|----------|------|",
                f"| 🔴 Critical | {severity_breakdown.get('critical', 0)} |",
                f"| 🟠 High | {severity_breakdown.get('high', 0)} |",
                f"| 🟡 Medium | {severity_breakdown.get('medium', 0)} |",
                f"| 🔵 Low | {severity_breakdown.get('low', 0)} |",
                f"| ⚪ Info | {severity_breakdown.get('info', 0)} |",
                ""
            ])
        
        if report.validation_result.inconsistencies:
            lines.extend([
                "## 📋 不一致详情",
                ""
            ])
            
            for inc in report.validation_result.inconsistencies[:30]:
                severity_icons = {
                    "critical": "🔴", "high": "🟠", "medium": "🟡",
                    "low": "🔵", "info": "⚪"
                }
                icon = severity_icons.get(inc.severity.value, "⚪")
                
                lines.extend([
                    f"### {icon} {inc.inconsistency_type.value}",
                    "",
                    f"- **严重程度**: {inc.severity.value}",
                    f"- **描述**: {inc.description}",
                ])
                
                if inc.frontend_endpoint:
                    lines.append(f"- **前端端点**: `{inc.frontend_endpoint.signature}`")
                if inc.backend_endpoint:
                    lines.append(f"- **后端端点**: `{inc.backend_endpoint.signature}`")
                if inc.fix_suggestion:
                    lines.append(f"- **修复建议**: {inc.fix_suggestion}")
                
                lines.append("")
        
        if report.recommendations:
            lines.extend([
                "## 💡 修复建议",
                ""
            ])
            for rec in report.recommendations:
                lines.append(f"- {rec}")
            lines.append("")
        
        if report.validation_result.frontend_only:
            lines.extend([
                "## 🔴 仅前端存在的端点",
                ""
            ])
            for endpoint in report.validation_result.frontend_only[:20]:
                lines.append(f"- `{endpoint.signature}` - {endpoint.source_file}:{endpoint.line_number}")
            lines.append("")
        
        if report.validation_result.backend_only:
            lines.extend([
                "## 🔵 仅后端存在的端点",
                ""
            ])
            for endpoint in report.validation_result.backend_only[:20]:
                lines.append(f"- `{endpoint.signature}` - {endpoint.source_file}:{endpoint.line_number}")
            lines.append("")
        
        return "\n".join(lines)

    def generate_json_report(self, report: ValidationReport, filename: str = "api_consistency_report.json") -> str:
        """生成JSON格式报告"""
        report_path = self.output_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        
        return str(report_path)


class APIConsistencyValidator:
    """API一致性验证器主类"""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        self.logger = logger or self._setup_logger()

        self.frontend_extractor = FrontendAPIExtractor(self.logger)
        self.backend_extractor = BackendAPIExtractor(self.logger)
        self.swagger_parser = SwaggerParser(self.logger)
        self.comparator = IntelligentAPIComparator(self.logger)
        self.suggestion_generator = FixSuggestionGenerator(self.logger)
        self.report_generator: Optional[ReportGenerator] = None
        
        self._setup_validation_rules()

    def _setup_logger(self) -> logging.Logger:
        """配置日志记录器"""
        logger = logging.getLogger("APIConsistencyValidator")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _setup_validation_rules(self) -> None:
        """设置验证规则"""
        self.comparator.add_validation_rule(TypeCompatibilityRule())
        self.comparator.add_validation_rule(SecurityValidationRule())
        self.comparator.add_validation_rule(RESTfulComplianceRule())
        self.comparator.add_validation_rule(NamingConventionRule())
        self.comparator.add_validation_rule(VersionCompatibilityRule())

    def validate(
        self,
        frontend_path: Optional[Path] = None,
        backend_path: Optional[Path] = None,
        swagger_path: Optional[Path] = None,
        output_dir: Optional[Path] = None
    ) -> ValidationReport:
        """执行API一致性验证"""
        self.logger.info("开始API一致性验证...")

        frontend_apis: List[APIEndpoint] = []
        backend_apis: List[APIEndpoint] = []

        if swagger_path and swagger_path.exists():
            backend_apis = self.swagger_parser.parse(swagger_path)
        elif backend_path:
            backend_apis = self.backend_extractor.extract(backend_path)

        if frontend_path:
            frontend_apis = self.frontend_extractor.extract(frontend_path)

        result = self.comparator.compare(frontend_apis, backend_apis)

        suggestions = self.suggestion_generator.generate(result.inconsistencies)

        summary = self._build_summary(result)
        statistics = self._build_statistics(result)
        quality_metrics = self._calculate_quality_metrics(result)

        if output_dir:
            self.report_generator = ReportGenerator(output_dir)

        return ValidationReport(
            timestamp=datetime.now().isoformat(),
            frontend_source=str(frontend_path) if frontend_path else "",
            backend_source=str(backend_path) if backend_path else str(swagger_path) if swagger_path else "",
            validation_result=result,
            summary=summary,
            recommendations=suggestions,
            statistics=statistics,
            quality_metrics=quality_metrics
        )

    def _build_summary(self, result: ValidationResult) -> Dict[str, Any]:
        """构建摘要"""
        severity_counts = defaultdict(int)
        type_counts = defaultdict(int)

        for inc in result.inconsistencies:
            severity_counts[inc.severity.value] += 1
            type_counts[inc.inconsistency_type.value] += 1

        return {
            "total_inconsistencies": len(result.inconsistencies),
            "severity_breakdown": dict(severity_counts),
            "type_breakdown": dict(type_counts),
            "frontend_endpoint_count": len(result.frontend_only) + result.matched_endpoints,
            "backend_endpoint_count": len(result.backend_only) + result.matched_endpoints,
            "unmatched_frontend": len(result.frontend_only),
            "unmatched_backend": len(result.backend_only),
            "validation_rules_applied": result.validation_rules_applied
        }

    def _build_statistics(self, result: ValidationResult) -> Dict[str, Any]:
        """构建统计信息"""
        return {
            "total_endpoints": result.total_endpoints,
            "matched_endpoints": result.matched_endpoints,
            "match_rate": result.matched_endpoints / max(result.total_endpoints, 1) * 100,
            "frontend_coverage": len(result.frontend_only) + result.matched_endpoints,
            "backend_coverage": len(result.backend_only) + result.matched_endpoints,
            "similarity_matches": len(result.similarity_matrix)
        }

    def _calculate_quality_metrics(self, result: ValidationResult) -> Dict[str, float]:
        """计算质量指标"""
        consistency_score = 100.0
        if result.total_endpoints > 0:
            match_rate = result.matched_endpoints / max(len(result.frontend_only) + result.matched_endpoints, 1)
            
            severity_weights = {
                Severity.CRITICAL: 10,
                Severity.HIGH: 5,
                Severity.MEDIUM: 2,
                Severity.LOW: 1,
                Severity.INFO: 0.5
            }
            
            penalty = sum(
                severity_weights.get(inc.severity, 1)
                for inc in result.inconsistencies
            )
            
            consistency_score = max(0, match_rate * 100 - penalty)
        
        return {
            "consistency_score": round(consistency_score, 2),
            "match_rate": round(result.matched_endpoints / max(result.total_endpoints, 1) * 100, 2),
            "coverage_score": round((result.matched_endpoints / max(result.total_endpoints / 2, 1)) * 100, 2)
        }

    def print_report(self, report: ValidationReport) -> None:
        """打印报告"""
        print("\n" + "=" * 80)
        print("🔌 API一致性验证报告")
        print("=" * 80)
        print(f"验证时间: {report.timestamp}")
        print(f"前端源: {report.frontend_source}")
        print(f"后端源: {report.backend_source}")

        result = report.validation_result
        summary = report.summary

        print("\n" + "-" * 80)
        print("一致性评分")
        print("-" * 80)
        print(f"一致性得分: {report.quality_metrics.get('consistency_score', 0):.1f}%")
        print(f"匹配端点: {result.matched_endpoints}/{summary['frontend_endpoint_count']}")

        print("\n" + "-" * 80)
        print("不一致统计")
        print("-" * 80)

        severity_icons = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵",
            "info": "⚪"
        }

        for severity, count in summary['severity_breakdown'].items():
            icon = severity_icons.get(severity, "⚪")
            print(f"  {icon} {severity.upper()}: {count}")

        if result.inconsistencies:
            print("\n" + "-" * 80)
            print("不一致详情 (前10个)")
            print("-" * 80)

            for inc in result.inconsistencies[:10]:
                icon = severity_icons.get(inc.severity.value, "⚪")
                print(f"\n  {icon} [{inc.inconsistency_type.value}]")
                print(f"     描述: {inc.description}")
                if inc.fix_suggestion:
                    print(f"     建议: {inc.fix_suggestion}")

        if report.recommendations:
            print("\n" + "-" * 80)
            print("修复建议")
            print("-" * 80)
            for i, rec in enumerate(report.recommendations, 1):
                print(f"  {i}. {rec}")

    def save_report(self, report: ValidationReport, output_path: str, format: str = "json") -> None:
        """保存报告到文件"""
        if not self.report_generator:
            self.report_generator = ReportGenerator(Path(output_path).parent)
        
        if format == "html":
            self.report_generator.generate_html_report(report, Path(output_path).name)
        elif format == "markdown":
            self.report_generator.generate_markdown_report(report, Path(output_path).name)
        else:
            self.report_generator.generate_json_report(report, Path(output_path).name)

        self.logger.info(f"报告已保存: {output_path}")


def main() -> int:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="API一致性验证器（增强版）",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--frontend",
        type=str,
        help="前端代码路径"
    )
    parser.add_argument(
        "--backend",
        type=str,
        help="后端代码路径"
    )
    parser.add_argument(
        "--swagger",
        type=str,
        help="Swagger/OpenAPI规范文件路径"
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["console", "json", "html", "markdown", "all"],
        default="console",
        help="输出格式 (默认: console)"
    )
    parser.add_argument(
        "--report-dir",
        type=str,
        default=str(get_path_config().REPORTS_DIR / "api_consistency"),
        help="报告输出目录"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )

    args = parser.parse_args()

    logger = logging.getLogger("APIConsistencyValidator")
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    validator = APIConsistencyValidator(logger=logger)

    frontend_path = Path(args.frontend) if args.frontend else None
    backend_path = Path(args.backend) if args.backend else None
    swagger_path = Path(args.swagger) if args.swagger else None
    report_dir = Path(args.report_dir) if args.report_dir else None

    report = validator.validate(
        frontend_path=frontend_path,
        backend_path=backend_path,
        swagger_path=swagger_path,
        output_dir=report_dir
    )

    if args.output == "console":
        validator.print_report(report)
    elif args.output == "json":
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    elif args.output in ["html", "markdown", "all"]:
        if report_dir:
            if args.output in ["html", "all"]:
                path = validator.report_generator.generate_html_report(report)
                print(f"HTML报告: {path}")
            if args.output in ["markdown", "all"]:
                path = validator.report_generator.generate_markdown_report(report)
                print(f"Markdown报告: {path}")
            if args.output == "all":
                path = validator.report_generator.generate_json_report(report)
                print(f"JSON报告: {path}")

    return 0 if report.validation_result.is_consistent else 1


if __name__ == "__main__":
    sys.exit(main())
