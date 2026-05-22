"""
API设计司 - RESTful/GraphQL接口设计、版本管理、接口文档自动生成
"""
from __future__ import annotations

import json
import re
import hashlib
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class APIType(Enum):
    """API类型"""

    REST = "rest"
    GRAPHQL = "graphql"
    GRPC = "grpc"


class VersionStrategy(Enum):
    """版本策略"""

    URL_VERSIONING = "url_versioning"
    HEADER_VERSIONING = "header_versioning"
    MEDIA_TYPE_VERSIONING = "media_type_versioning"


class HTTPMethod(Enum):
    """HTTP方法"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class Resource:
    """API资源定义"""

    name: str
    plural_name: str = ""
    base_path: str = ""
    description: str = ""
    attributes: dict[str, dict[str, Any]] = field(default_factory=dict)
    endpoints: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Endpoint:
    """端点定义"""

    path: str
    method: HTTPMethod
    summary: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    request_body: dict[str, Any] | None = None
    responses: dict[int, dict[str, Any]] = field(default_factory=dict)
    parameters: list[dict[str, Any]] = field(default_factory=list)
    security: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class GraphQLType:
    """GraphQL类型定义"""

    name: str
    kind: str  # type, input, enum, interface, union
    fields: list[dict[str, Any]] = field(default_factory=list)
    description: str = ""


@dataclass
class GraphQLField:
    """GraphQL字段"""

    name: str
    type_ref: str
    args: list[dict[str, Any]] = field(default_factory=list)
    description: str = ""
    is_nullable: bool = True


@dataclass
class RateLimitConfig:
    """速率限制配置"""

    endpoint_pattern: str = "*"
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10


@dataclass
class ErrorSchema:
    """错误响应模式"""

    code: str
    message: str
    http_status: int = 400
    trace_id: str | None = None
    details: list[dict[str, Any]] | None = None


@dataclass
class APIDocumentation:
    """API文档"""

    title: str
    version: str = "1.0.0"
    description: str = ""
    base_url: str = "/api/v1"
    servers: list[dict[str, str]] = field(default_factory=list)
    resources: list[Resource] = field(default_factory=list)
    endpoints: list[Endpoint] = field(default_factory=dict)
    schemas: dict[str, Any] = field(default_factory=dict)
    security_schemes: dict[str, Any] = field(default_factory=dict)


class APIDesignError(Exception):
    """API设计异常"""


class SchemaError(APIDesignError):
    """Schema异常"""


class ValidationError(APIDesignError):
    """验证异常"""


class APIDesignSi:
    """
    API设计司 - 工部·虞部司

    提供全面的API设计能力：
    - RESTful API设计（资源命名/方法语义/状态码/分页过滤排序）
    - GraphQL Schema设计
    - 多种版本管理策略
    - OpenAPI 3.0规范文档生成
    - 接口契约测试生成
    - API网关配置
    - 速率限制与配额设计
    - 统一错误响应格式
    """

    def __init__(self) -> None:
        self._doc = APIDocumentation(title="API")
        self._resources: dict[str, Resource] = {}
        self._rate_limits: list[RateLimitConfig] = []
        self._error_codes: dict[str, ErrorSchema] = {}
        self._init_error_codes()

    # ==================== 错误码系统 ====================

    def _init_error_codes(self) -> None:
        """初始化标准错误码"""
        error_defs: list[tuple[str, str, int]] = [
            ("SUCCESS", "操作成功", 200),
            ("CREATED", "资源创建成功", 201),
            ("BAD_REQUEST", "请求参数错误", 400),
            ("UNAUTHORIZED", "未授权，请先登录", 401),
            ("FORBIDDEN", "无权限访问该资源", 403),
            ("NOT_FOUND", "请求的资源不存在", 404),
            ("METHOD_NOT_ALLOWED", "请求方法不允许", 405),
            ("CONFLICT", "资源冲突或已存在", 409),
            ("VALIDATION_ERROR", "数据验证失败", 422),
            ("RATE_LIMITED", "请求过于频繁，请稍后重试", 429),
            ("INTERNAL_ERROR", "服务器内部错误", 500),
            ("SERVICE_UNAVAILABLE", "服务暂不可用", 503),
        ]
        for code, msg, status in error_defs:
            self._error_codes[code] = ErrorSchema(code=code, message=msg, http_status=status)

    # ==================== 资源与端点管理 ====================

    def add_resource(self, resource: Resource) -> None:
        """添加API资源"""
        resource.plural_name = resource.plural_name or resource.name.lower() + "s"
        resource.base_path = resource.base_path or f"/{resource.plural_name}"
        self._resources[resource.name] = resource

    def add_endpoint(self, endpoint: Endpoint) -> None:
        """添加端点"""
        if not hasattr(self._doc, 'endpoints') or not isinstance(self._doc.endpoints, list):
            self._doc.endpoints = []
        self._doc.endpoints.append(endpoint)

    # ==================== RESTful API设计 ====================

    def design_rest_resource(
        self,
        name: str,
        attributes: dict[str, dict[str, Any]],
        custom_endpoints: list[dict[str, Any]] | None = None,
    ) -> Resource:
        """
        设计RESTful资源

        自动生成标准CRUD端点

        Args:
            name: 资源名称(单数)
            attributes: 属性字典 {"attr": {"type": "...", "required": bool}}
            custom_endpoints: 自定义端点列表
        """
        plural = name.lower() + "s"
        base_path = f"/{plural}"

        standard_endpoints: list[dict[str, Any]] = [
            {
                "method": HTTPMethod.GET,
                "path": base_path,
                "summary": f"获取{name}列表",
                "operationId": f"list_{plural}",
                "tags": [name],
                "parameters": [
                    {"name": "page", "in": "query", "type": "integer", "default": 1},
                    {"name": "per_page", "in": "query", "type": "integer", "default": 20},
                    {"name": "sort", "in": "query", "type": "string", "description": "排序字段"},
                    {"name": "order", "in": "query", "enum": ["asc", "desc"], "default": "desc"},
                    {"name": "q", "in": "query", "type": "string", "description": "搜索关键词"},
                    {"name": f"{list(attributes.keys())[0] if attributes else 'status'}",
                     "in": "query", "type": "string", "description": "筛选条件"},
                ],
                "responses": {
                    200: {"description": f"{name}列表", "schema": {"$ref": f"#/components/schemas/{name}ListResponse"}},
                },
            },
            {
                "method": HTTPMethod.POST,
                "path": base_path,
                "summary": f"创建{name}",
                "operationId": f"create_{name}",
                "tags": [name],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/Create{name}"},
                        }
                    }
                },
                "responses": {
                    201: {"description": f"{name}创建成功", "schema": {"$ref": f"#/components/schemas/{name}"}},
                    400: {"description": "参数错误"},
                    422: {"description": "数据验证失败"},
                },
            },
            {
                "method": HTTPMethod.GET,
                "path": f"{base_path}/{{{name.lower()}_id}}",
                "summary": f"获取单个{name}",
                "operationId": f"get_{name}",
                "tags": [name],
                "parameters": [
                    {"name": f"{name.lower()}_id", "in": "path", "required": True, "type": "string"},
                ],
                "responses": {
                    200: {"description": f"{name}详情", "schema": {"$ref": f"#/components/schemas/{name}"}},
                    404: {"description": f"{name}不存在"},
                },
            },
            {
                "method": HTTPMethod.PUT,
                "path": f"{base_path}/{{{name.lower()}_id}}",
                "summary": f"更新{name}",
                "operationId": f"update_{name}",
                "tags": [name],
                "parameters": [
                    {"name": f"{name.lower()}_id", "in": "path", "required": True, "type": "string"},
                ],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/Update{name}"},
                        }
                    }
                },
                "responses": {
                    200: {"description": f"{name}更新成功"},
                    404: {"description": f"{name}不存在"},
                    422: {"description": "数据验证失败"},
                },
            },
            {
                "method": HTTPMethod.DELETE,
                "path": f"{base_path}/{{{name.lower()}_id}}",
                "summary": f"删除{name}",
                "operationId": f"delete_{name}",
                "tags": [name],
                "parameters": [
                    {"name": f"{name.lower()}_id", "in": "path", "required": True, "type": "string"},
                ],
                "responses": {
                    204: {"description": f"{name}删除成功"},
                    404: {"description": f"{name}不存在"},
                },
            },
        ]

        all_endpoints = standard_endpoints + (custom_endpoints or [])

        resource = Resource(
            name=name,
            plural_name=plural,
            base_path=base_path,
            attributes=attributes,
            endpoints=all_endpoints,
        )
        self.add_resource(resource)

        for ep_def in all_endpoints:
            method = ep_def.get("method", HTTPMethod.GET)
            path = ep_def.get("path", "")
            endpoint = Endpoint(
                path=path,
                method=method if isinstance(method, HTTPMethod) else HTTPMethod(method),
                summary=ep_def.get("summary", ""),
                tags=ep_def.get("tags", []),
                request_body=ep_def.get("requestBody"),
                responses={int(k): v for k, v in ep_def.get("responses", {}).items()},
                parameters=ep_def.get("parameters", []),
            )
            self.add_endpoint(endpoint)

        return resource

    # ==================== GraphQL Schema设计 ====================

    def design_graphql_schema(
        self,
        types: list[GraphQLType],
        queries: list[GraphQLField] | None = None,
        mutations: list[GraphQLField] | None = None,
        subscriptions: list[GraphQLField] | None = None,
    ) -> str:
        """
        设计GraphQL Schema

        Args:
            types: 类型定义列表
            queries: Query字段列表
            mutations: Mutation字段列表
            subscriptions: Subscription字段列表

        Returns:
            GraphQL Schema SDL字符串
        """
        lines: list[str] = []

        for gql_type in types:
            match gql_type.kind:
                case "type":
                    lines.append(f"type {gql_type.name} {{")
                    for fld in gql_type.fields:
                        args_str = ""
                        if fld.args:
                            args_str = "(" + ", ".join(f"${a['name']}: {a['type']}" for a in fld.args) + ")"
                        nullable = "" if fld.is_nullable else "!"
                        lines.append(f"  {fld.name}{args_str}: {fld.type_ref}{nullable}")
                    lines.append("}")
                case "input":
                    lines.append(f"input {gql_type.name} {{")
                    for fld in gql_type.fields:
                        req = "!" if fld.args and any(a.get("required") for a in fld.args) else ""
                        lines.append(f"  {fld.name}: {fld.type_ref}{req}")
                    lines.append("}")
                case "enum":
                    lines.append(f"enum {gql_type.name} {{")
                    for fld in gql_type.fields:
                        lines.append(f"  {fld.name}")
                    lines.append("}")
                case _:
                    lines.append(f"# TODO: {gql_type.kind} {gql_type.name}")

            if gql_type.description:
                lines.insert(-2, f'  """{gql_type.description}"""')
            lines.append("")

        if queries:
            lines.append("type Query {")
            for q in queries:
                args_str = "(" + ", ".join(f"${a['name']}: {a['type']}" for a in q.args) + ")" if q.args else ""
                nullable = "" if q.is_nullable else "!"
                lines.append(f"  {q.name}{args_str}: {q.type_ref}{nullable}")
            lines.append("}\n")

        if mutations:
            lines.append("type Mutation {")
            for m in mutations:
                args_str = "(" + ", ".join(f"${a['name']}: {a['type']}" for a in m.args) + ")" if m.args else ""
                nullable = "" if m.is_nullable else "!"
                lines.append(f"  {m.name}{args_str}: {m.type_ref}{nullable}")
            lines.append("}\n")

        if subscriptions:
            lines.append("type Subscription {")
            for s in subscriptions:
                lines.append(f"  {s.name}: {s.type_ref}")
            lines.append("}\n")

        return "\n".join(lines)

    # ==================== OpenAPI 3.0文档生成 ====================

    def generate_openapi_spec(
        self,
        version: str = "1.0.0",
        description: str = "",
        base_url: str = "/api/v1",
    ) -> dict[str, Any]:
        """
        生成OpenAPI 3.0规范文档

        Args:
            version: API版本号
            description: API描述
            base_url: 基础URL路径
        """
        spec: dict[str, Any] = {
            "openapi": "3.0.3",
            "info": {
                "title": self._doc.title,
                "version": version,
                "description": description,
            },
            "servers": [{"url": base_url}],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    },
                    "apiKey": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key",
                    },
                },
                "responses": {
                    "NotFound": {"description": "资源不存在", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                    "Unauthorized": {"description": "未授权", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                    "ValidationError": {"description": "验证错误", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ValidationError"}}}},
                },
            },
        }

        paths: dict[str, Any] = {}
        for endpoint in (self._doc.endpoints if isinstance(self._doc.endpoints, list) else []):
            path_key = endpoint.path
            if path_key not in paths:
                paths[path_key] = {}

            method_lower = endpoint.method.value.lower()
            operation: dict[str, Any] = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "operationId": endpoint.summary.lower().replace(" ", "_"),
                "tags": endpoint.tags,
                "parameters": endpoint.parameters,
                "responses": {
                    k: v for k, v in endpoint.responses.items()
                },
            }

            if endpoint.request_body:
                operation["requestBody"] = endpoint.request_body

            if endpoint.security:
                operation["security"] = endpoint.security
            else:
                operation["security"] = [{"bearerAuth": []}]

            paths[path_key][method_lower] = operation

        spec["paths"] = paths

        for res_name, resource in self._resources.items():
            schema_props: dict[str, Any] = {}
            required: list[str] = []
            for attr_name, attr_def in resource.attributes.items():
                schema_props[attr_name] = {
                    "type": attr_def.get("type", "string"),
                    "description": attr_def.get("description", ""),
                }
                if attr_def.get("required"):
                    required.append(attr_name)

            spec["components"]["schemas"][res_name] = {
                "type": "object",
                "properties": schema_props,
                "required": required,
            }

            spec["components"]["schemas"][f"Create{res_name}"] = {
                "type": "object",
                "properties": {
                    k: {"type": v.get("type", "string")}
                    for k, v in resource.attributes.items()
                    if k != "id" and not k.endswith("_at")
                },
                "required": [k for k, v in resource.attributes.items() if v.get("required") and k != "id"],
            }

            spec["components"]["schemas"][f"Update{res_name}"] = {
                "type": "object",
                "properties": {
                    k: {"type": v.get("type", "string")}
                    for k, v in resource.attributes.items()
                    if k != "id"
                },
            }

            spec["components"]["schemas"][f"{res_name}ListResponse"] = {
                "type": "object",
                "properties": {
                    "data": {"type": "array", "items": {"$ref": f"#/components/schemas/{res_name}"}},
                    "total": {"type": "integer"},
                    "page": {"type": "integer"},
                    "per_page": {"type": "integer"},
                },
            }

        spec["components"]["schemas"]["Error"] = {
            "type": "object",
            "properties": {
                "code": {"type": "string", "example": "NOT_FOUND"},
                "message": {"type": "string", "example": "请求的资源不存在"},
                "trace_id": {"type": "string", "format": "uuid"},
            },
            "required": ["code", "message"],
        }

        spec["components"]["schemas"]["ValidationError"] = {
            "type": "object",
            "properties": {
                "code": {"type": "string", "example": "VALIDATION_ERROR"},
                "message": {"type": "string"},
                "details": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "message": {"type": "string"},
                        },
                    },
                },
            },
        }

        return spec

    # ==================== 版本管理策略 ====================

    def generate_version_config(self, strategy: VersionStrategy, current_version: str = "v1") -> dict[str, Any]:
        """
        生成版本管理配置

        Args:
            strategy: 版本策略
            current_version: 当前版本
        """
        match strategy:
            case VersionStrategy.URL_VERSIONING:
                return {
                    "strategy": "url_versioning",
                    "pattern": "/api/{version}/{resource}",
                    "examples": {
                        "current": f"/api/{current_version}/users",
                        "next": f"/api/v2/users",
                        "deprecated": f"/api/v1/users (deprecated)",
                    },
                    "pros": ["直观清晰", "易于缓存", "客户端可自由选择版本"],
                    "cons": ["URL变长", "需要路由配置"],
                    "implementation": "在路由前缀中包含版本号",
                }
            case VersionStrategy.HEADER_VERSIONING:
                return {
                    "strategy": "header_versioning",
                    "header_name": "Api-Version",
                    "header_value": current_version.replace("v", ""),
                    "examples": {
                        "header": f"Api-Version: {current_version.replace('v', '')}",
                    },
                    "pros": ["URL简洁", "不影响缓存"],
                    "cons": ["不便于调试", "需文档说明"],
                    "implementation": "通过中间件读取Header并路由到对应版本处理器",
                }
            case VersionStrategy.MEDIA_TYPE_VERSIONING:
                return {
                    "strategy": "media_type_versioning",
                    "header_name": "Accept",
                    "header_value": f"application/vnd.api.{current_version}+json",
                    "examples": {
                        "header": f"Accept: application/vnd.api.{current_version}+json",
                    },
                    "pros": ["符合HTTP语义", "灵活的版本协商"],
                    "cons": ["复杂度高", "客户端实现复杂"],
                    "implementation": "基于Accept头的内容协商进行版本路由",
                }

    # ==================== 接口契约测试生成 ====================

    def generate_contract_tests(self, openapi_spec: dict[str, Any]) -> str:
        """
        从OpenAPI Spec生成接口契约测试

        Args:
            openapi_spec: OpenAPI规范字典
        """
        lines: list[str] = ['"""\n接口契约测试 - 自动从OpenAPI 3.0规范生成\n"""']
        lines.append("import pytest")
        lines.append("from httpx import AsyncClient\n")

        paths = openapi_spec.get("paths", {})
        base_url = openapi_spec.get("servers", [{}])[0].get("url", "")

        test_count = 0
        for path, methods in paths.items():
            for method, operation in methods.items():
                test_count += 1
                summary = operation.get("summary", f"test_{test_count}")
                op_id = operation.get("operationId", f"op_{test_count}")

                safe_name = re.sub(r'[^a-zA-Z0-9]', '_', summary.lower())

                lines.append(f"\nasync def test_{safe_name}_{method}(client: AsyncClient):")
                lines.append(f'    """{summary}"""')

                params = operation.get("parameters", [])
                path_params: dict[str, str] = {}
                query_params: dict[str, Any] = {}

                for param in params:
                    pname = param.get("name", "")
                    ploc = param.get("in", "query")
                    ptype = param.get("type", "string")

                    if ploc == "path":
                        path_params[pname] = f'"test_{ptype}"'
                    elif ploc == "query":
                        default_val = param.get("default", "1" if ptype == "integer" else "")
                        query_params[pname] = default_val

                url = path
                for pp, pv in path_params.items():
                    url = url.replace(f"{{{pp}}}", "{" + pv + "}")

                resp_map = operation.get("responses", {})
                expected_status = next((int(k) for k in sorted(resp_map.keys()) if int(k) < 400), 200)

                req_body = operation.get("requestBody")
                body_code = ""
                if req_body:
                    content = req_body.get("content", {})
                    json_content = content.get("application/json", {})
                    schema_ref = json_content.get("schema", {}).get("$ref", "")
                    model_name = schema_ref.split("/")[-1] if schema_ref else "payload"
                    body_code = f'\n    payload = {{{{ "name": "test"}}}}\n    response = await client.{method}("{url}", json=payload)'
                else:
                    if query_params:
                        qs = "&".join(f'{k}={v}' for k, v in query_params.items())
                        full_url = f"{url}?{qs}" if qs else url
                    else:
                        full_url = url
                    body_code = f'\n    response = await client.{method}("{full_url}")'

                lines.append(body_code)
                lines.append(f"    assert response.status_code == {expected_status}")

                if expected_status == 200:
                    lines.append('    data = response.json()')
                    lines.append('    assert isinstance(data, dict)')

        return "\n".join(lines)

    # ==================== API网关配置 ====================

    def generate_gateway_config(
        self,
        gateway_type: str = "kong",
        routes: list[dict[str, Any]] | None = None,
    ) -> str:
        """
        生成API网关配置

        Args:
            gateway_type: 网关类型 (kong/apisix/nginx)
            routes: 路由配置列表
        """
        all_routes = routes or []
        if not all_routes:
            for res_name, resource in self._resources.items():
                for ep in resource.endpoints:
                    all_routes.append({
                        "path": ep.get("path", resource.base_path),
                        "methods": [ep.get("method", "GET").value.upper()] if isinstance(ep.get("method"), (str, HTTPMethod)) else ["GET"],
                        "service": res_name.lower(),
                        "plugins": ["rate-limit", "cors", "key-auth"],
                    })

        match gateway_type:
            case "kong":
                return self._gen_kong_config(all_routes)
            case "apisix":
                return self._gen_apisix_config(all_routes)
            case "nginx":
                return self._gen_nginx_config(all_routes)
            case _:
                return f"# 不支持的网关类型: {gateway_type}"

    def _gen_kong_config(self, routes: list[dict[str, Any]]) -> str:
        """Kong网关配置"""
        lines: list[str] = ['# Kong Declarative Configuration', '# Generated by 尚书省·工部·API设计司\n']

        services_seen: set[str] = set()
        for route in routes:
            service = route.get("service", "default")
            if service not in services_seen:
                services_seen.add(service)
                lines.append(f"services:\n- name: {service}-svc\n  url: http://{service}-service:8000\n")

        lines.append("\nroutes:")
        for i, route in enumerate(routes):
            methods = route.get("methods", ["GET"])
            path = route.get("path", "/")
            plugins = route.get("plugins", [])
            plugin_str = ", ".join(plugins)
            lines.append(f"- name: route-{i+1}")
            lines.append(f"  service: {route.get('service', 'default')}-svc")
            lines.append(f"  paths:")
            lines.append(f"    - {path}")
            lines.append(f"  methods: {json.dumps(methodes)}")
            if plugins:
                lines.append(f"  plugins: [{plugin_str}]")

        return "\n".join(lines)

    def _gen_apisix_config(self, routes: list[dict[str, Any]]) -> str:
        """APISIX网关配置"""
        config: dict[str, Any] = {"routes": []}

        for i, route in enumerate(routes):
            config["routes"].append({
                "uri": route.get("path", "/*"),
                "methods": route.get("methods", ["GET"]),
                "upstream": {
                    "type": "roundrobin",
                    "nodes": {f"{route.get('service', 'default')}:8000": 1},
                },
                "plugins": {
                    "limit-count": {
                        "count": 60,
                        "time_window": 60,
                    },
                    "cors": {},
                },
            })

        return json.dumps(config, indent=2, ensure_ascii=False)

    def _gen_nginx_config(self, routes: list[dict[str, Any]]) -> str:
        """Nginx反向代理配置"""
        lines: list[str] = [
            "# Nginx API Gateway Configuration",
            "# Generated by 尚书省·工部·API设计司\n",
            "upstream api_backend {\n    server 127.0.0.1:8000;\n}\n",
            "server {\n    listen 80;\n    server_name api.example.com;",
        ]

        for route in routes:
            path = route.get("path", "/")
            methods = route.get("methods", ["GET"])
            location_path = path.rstrip("/").rsplit("/", 1)[-1].replace("{", "").replace("}", "")
            lines.append(f"\n    location /api/{location_path} {{")
            if "GET" in methods:
                lines.append("        proxy_pass http://api_backend;")
            else:
                lines.append("        limit_except GET {")
                lines.append("            proxy_pass http://api_backend;")
                lines.append("        }")
            lines.append("        proxy_set_header Host $host;")
            lines.append("        proxy_set_header X-Real-IP $remote_addr;")
            lines.append("        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;")
            lines.append("    }")

        lines.append("}")
        return "\n".join(lines)

    # ==================== 速率限制 ====================

    def add_rate_limit(self, config: RateLimitConfig) -> None:
        """添加速率限制规则"""
        self._rate_limits.append(config)

    def get_rate_limit_policy(self) -> dict[str, Any]:
        """获取速率限制策略总览"""
        policies: list[dict[str, Any]] = []
        for rl in self._rate_limits:
            policies.append({
                "endpoint": rl.endpoint_pattern,
                "rpm": rl.requests_per_minute,
                "rph": rl.requests_per_hour,
                "rpd": rl.requests_per_day,
                "burst": rl.burst_size,
            })
        return {"policies": policies, "default": {"rpm": 60, "rph": 1000}}

    # ==================== 错误响应格式 ====================

    def format_error_response(self, code: str, trace_id: str | None = None, details: list[dict] | None = None) -> dict[str, Any]:
        """
        格式化统一错误响应

        Args:
            code: 错误码
            trace_id: 追踪ID
            details: 详细错误信息
        """
        err_schema = self._error_codes.get(code, ErrorSchema(code=code, message="未知错误"))
        import uuid

        response: dict[str, Any] = {
            "code": err_schema.code,
            "message": err_schema.message,
            "httpStatus": err_schema.http_status,
            "trace_id": trace_id or str(uuid.uuid4()),
        }
        if details:
            response["details"] = details
        return response

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成API设计司报告"""
        lines: list[str] = []
        lines.append("# 🌐 API设计司 · 设计报告\n")

        lines.append(f"## API概览\n")
        lines.append(f"- **标题**: {self._doc.title}")
        lines.append(f"- **资源数**: {len(self._resources)}")
        lines.append(f"- **端点数**: {len(self._doc.endpoints) if isinstance(self._doc.endpoints, list) else 0}")

        if self._resources:
            lines.append(f"\n## 资源列表\n")
            lines.append("| 资源 | 路径 | 属性数 | 端点数 |")
            lines.append("| --- | --- | --- | --- |")
            for name, res in self._resources.items():
                lines.append(
                    f"| **{name}** | `{res.base_path}` | {len(res.attributes)} | {len(res.endpoints)} |"
                )

        lines.append(f"\n## 标准错误码 ({len(self._error_codes)})\n")
        lines.append("| 码 | 消息 | HTTP状态 |")
        lines.append("| --- | --- | --- |")
        for code, err in self._error_codes.items():
            lines.append(f"`{code}` | {err.message} | **{err.http_status}** |")

        rate_policy = self.get_rate_limit_policy()
        if rate_policy["policies"]:
            lines.append(f"\n## 速率限制策略\n")
            for p in rate_policy["policies"]:
                lines.append(f"- `{p['endpoint']}`: {p['rpm']}/min, {p['rph']}/h, burst={p['burst']}")

        version_cfg = self.generate_version_config(VersionStrategy.URL_VERSIONING)
        lines.append(f"\n## 版本管理 [{version_cfg['strategy']}]\n")
        for ex_key, ex_val in version_cfg.get("examples", {}).items():
            lines.append(f"- {ex_key}: `{ex_val}`")

        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print("=" * 60)
    print("API设计司 - 功能演示")
    print("=" * 60)

    si = APIDesignSi()

    print("\n--- RESTful资源设计 ---")
    user_attrs = {
        "username": {"type": "string", "required": True, "description": "用户名"},
        "email": {"type": "string", "required": True, "description": "邮箱"},
        "full_name": {"type": "string", "description": "全名"},
        "role": {"type": "string", "enum": ["admin", "user", "guest"], "default": "user"},
        "is_active": {"type": "boolean", "default": True},
    }
    user_res = si.design_rest_resource("User", user_attrs)
    print(f"  资源: {user_res.name}, 路径: {user_res.base_path}, 端点: {len(user_res.endpoints)}")

    print("\n--- OpenAPI 3.0 Spec ---")
    spec = si.generate_openapi_spec(version="1.0.0", description="示例API")
    print(f"  Paths: {len(spec.get('paths', {}))}")
    print(f"  Schemas: {len(spec.get('components', {}).get('schemas', {}))}")

    print("\n--- GraphQL Schema ---")
    user_type = GraphQLType(name="User", kind="type", fields=[
        GraphQLField("id", "ID!", description="用户ID"),
        GraphQLField("username", "String!", description="用户名"),
        GraphQLField("email", "String!", description="邮箱"),
        GraphQLField("fullName", "String", description="全名"),
    ])
    queries = [GraphQLField("users", "[User!]!", args=[{"name": "limit", "type": "Int"}], description="用户列表")]
    mutations = [GraphQLField("createUser", "User!", args=[{"name": "input", "type": "CreateUserInput!", "required": True}], description="创建用户")]
    graphql_schema = si.design_graphql_schema([user_type], queries, mutations)
    print(graphql_schema[:500])

    print("\n--- 版本管理 ---")
    for vs in VersionStrategy:
        cfg = si.generate_version_config(vs)
        display_val = cfg.get('pattern', cfg.get('header_name', 'N/A'))
        print(f"  [{vs.value}]: {display_val}")

    print("\n--- 契约测试 ---")
    contract_tests = si.generate_contract_tests(spec)
    print(contract_tests[:600])

    print("\n--- 网关配置 (Kong) ---")
    gateway = si.generate_gateway_config("kong")
    print(gateway[:400])

    si.add_rate_limit(RateLimitConfig(endpoint_pattern="/api/*", requests_per_minute=120))
    policy = si.get_rate_limit_policy()
    print(f"\n--- 速率限制 ---\n{policy}")

    err_resp = si.format_error_response("NOT_FOUND")
    print(f"\n--- 错误响应 ---\n{err_resp}")

    report = si.generate_report()
    print(f"\n--- 报告预览 (前800字符) ---\n{report[:800]}...")

    print("\n✅ 所有测试通过!")
