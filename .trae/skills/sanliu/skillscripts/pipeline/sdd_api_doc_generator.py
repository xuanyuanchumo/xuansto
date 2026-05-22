#!/usr/bin/env python3
"""
SDD规范API文档生成器

从SDD规范自动生成API文档：
1. OpenAPI 3.0/Swagger规范
2. API使用示例
3. Postman Collection
4. Markdown API文档

功能：
- 生成OpenAPI 3.0规范文件
- 生成Swagger UI可用的文档
- 生成Postman Collection
- 生成API使用示例代码
- 支持多种编程语言的示例代码生成
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import sys
from skillscripts.core.path_config_center import get_path_config

sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from pipeline.sdd_spec_parser import (
    SDDSpecification,
    SpecAttribute,
    SpecEndpoint,
    SpecType,
)


class DocFormat(Enum):
    OPENAPI = "openapi"
    SWAGGER = "swagger"
    POSTMAN = "postman"
    MARKDOWN = "markdown"
    HTML = "html"


@dataclass
class APIParameter:
    name: str
    location: str
    description: str
    required: bool
    schema: Dict[str, Any]
    example: Any = None


@dataclass
class APIResponse:
    status_code: int
    description: str
    content_type: str
    schema: Dict[str, Any]
    example: Any = None


@dataclass
class APIEndpoint:
    path: str
    method: str
    operation_id: str
    summary: str
    description: str
    tags: List[str]
    parameters: List[APIParameter]
    request_body: Optional[Dict[str, Any]]
    responses: List[APIResponse]
    security: List[Dict[str, Any]] = field(default_factory=list)
    deprecated: bool = False


@dataclass
class GeneratedDocument:
    filename: str
    content: str
    format: DocFormat
    content_type: str


class OpenAPIGenerator:
    """OpenAPI 3.0规范生成器"""
    
    OPENAPI_VERSION = "3.0.3"
    
    def generate(self, spec: SDDSpecification) -> GeneratedDocument:
        openapi_doc = {
            "openapi": self.OPENAPI_VERSION,
            "info": self._generate_info(spec),
            "servers": self._generate_servers(spec),
            "paths": self._generate_paths(spec),
            "components": self._generate_components(spec),
            "tags": self._generate_tags(spec),
        }
        
        content = json.dumps(openapi_doc, ensure_ascii=False, indent=2)
        filename = f"{self._to_kebab_case(spec.metadata.name)}-openapi.json"
        
        return GeneratedDocument(
            filename=filename,
            content=content,
            format=DocFormat.OPENAPI,
            content_type="application/json",
        )
    
    def _generate_info(self, spec: SDDSpecification) -> Dict[str, Any]:
        return {
            "title": spec.metadata.name,
            "description": spec.spec.get("description", ""),
            "version": spec.metadata.version,
            "contact": {
                "name": spec.metadata.author or "API Support",
            },
            "license": {
                "name": "MIT",
            },
        }
    
    def _generate_servers(self, spec: SDDSpecification) -> List[Dict[str, Any]]:
        servers = spec.spec.get("servers", [])
        if not servers:
            servers = [
                {
                    "url": "http://localhost:8000",
                    "description": "Development server",
                },
                {
                    "url": "https://api.example.com",
                    "description": "Production server",
                },
            ]
        return servers
    
    def _generate_paths(self, spec: SDDSpecification) -> Dict[str, Any]:
        paths = {}
        
        for endpoint in spec.endpoints:
            path = endpoint.path
            if path not in paths:
                paths[path] = {}
            
            method = endpoint.method.lower()
            paths[path][method] = self._generate_operation(endpoint, spec)
        
        if not paths and spec.kind == SpecType.ENTITY:
            paths = self._generate_crud_paths(spec)
        
        return paths
    
    def _generate_crud_paths(self, spec: SDDSpecification) -> Dict[str, Any]:
        base_path = f"/api/v1/{self._to_kebab_case(spec.metadata.name)}s"
        entity_name = self._to_pascal_case(spec.metadata.name)
        
        paths = {
            base_path: {
                "get": {
                    "summary": f"获取{spec.metadata.name}列表",
                    "operationId": f"list{entity_name}",
                    "tags": [spec.metadata.name],
                    "parameters": [
                        {
                            "name": "skip",
                            "in": "query",
                            "schema": {"type": "integer", "default": 0},
                            "description": "跳过的记录数",
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 100, "maximum": 1000},
                            "description": "返回的记录数",
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "成功返回列表",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": f"#/components/schemas/{entity_name}"},
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": f"创建{spec.metadata.name}",
                    "operationId": f"create{entity_name}",
                    "tags": [spec.metadata.name],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/Create{entity_name}"},
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "创建成功",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": f"#/components/schemas/{entity_name}"},
                                }
                            }
                        }
                    }
                }
            },
            f"{base_path}/{{id}}": {
                "get": {
                    "summary": f"根据ID获取{spec.metadata.name}",
                    "operationId": f"get{entity_name}ById",
                    "tags": [spec.metadata.name],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                            "description": f"{spec.metadata.name} ID",
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "成功返回",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": f"#/components/schemas/{entity_name}"},
                                }
                            }
                        },
                        "404": {"description": "未找到"},
                    }
                },
                "put": {
                    "summary": f"更新{spec.metadata.name}",
                    "operationId": f"update{entity_name}",
                    "tags": [spec.metadata.name],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/Update{entity_name}"},
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "更新成功",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": f"#/components/schemas/{entity_name}"},
                                }
                            }
                        }
                    }
                },
                "delete": {
                    "summary": f"删除{spec.metadata.name}",
                    "operationId": f"delete{entity_name}",
                    "tags": [spec.metadata.name],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "204": {"description": "删除成功"},
                        "404": {"description": "未找到"},
                    }
                }
            }
        }
        
        return paths
    
    def _generate_operation(self, endpoint: SpecEndpoint, spec: SDDSpecification) -> Dict[str, Any]:
        operation = {
            "summary": endpoint.description or endpoint.name,
            "operationId": endpoint.name,
            "tags": [spec.metadata.name],
            "parameters": self._generate_parameters(endpoint),
            "responses": self._generate_responses(endpoint),
        }
        
        if endpoint.request_body:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": endpoint.request_body,
                    }
                }
            }
        
        if endpoint.authentication:
            operation["security"] = [{"bearerAuth": []}]
        
        return operation
    
    def _generate_parameters(self, endpoint: SpecEndpoint) -> List[Dict[str, Any]]:
        parameters = []
        
        for param in endpoint.parameters:
            parameter = {
                "name": param.get("name", ""),
                "in": param.get("location", "query"),
                "required": param.get("required", False),
                "description": param.get("description", ""),
                "schema": self._get_schema_for_type(param.get("type", "string")),
            }
            parameters.append(parameter)
        
        return parameters
    
    def _generate_responses(self, endpoint: SpecEndpoint) -> Dict[str, Any]:
        responses = {}
        
        success_code = "200" if endpoint.method.upper() != "POST" else "201"
        responses[success_code] = {
            "description": "成功响应",
            "content": {
                "application/json": {
                    "schema": endpoint.response or {"type": "object"},
                }
            }
        }
        
        for error in endpoint.errors:
            status_code = str(error.get("statusCode", 400))
            responses[status_code] = {
                "description": error.get("message", "错误"),
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "error": {"type": "string"},
                                "message": {"type": "string"},
                                "code": {"type": "string", "example": error.get("code", "")},
                            }
                        }
                    }
                }
            }
        
        return responses
    
    def _generate_components(self, spec: SDDSpecification) -> Dict[str, Any]:
        components = {
            "schemas": {},
            "securitySchemes": {},
        }
        
        entity_name = self._to_pascal_case(spec.metadata.name)
        
        components["schemas"][entity_name] = self._generate_schema(spec)
        components["schemas"][f"Create{entity_name}"] = self._generate_create_schema(spec)
        components["schemas"][f"Update{entity_name}"] = self._generate_update_schema(spec)
        
        components["securitySchemes"]["bearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
        
        return components
    
    def _generate_schema(self, spec: SDDSpecification) -> Dict[str, Any]:
        schema = {
            "type": "object",
            "required": [],
            "properties": {},
        }
        
        schema["properties"]["id"] = {"type": "integer", "description": "唯一标识符"}
        schema["properties"]["createdAt"] = {"type": "string", "format": "date-time"}
        schema["properties"]["updatedAt"] = {"type": "string", "format": "date-time"}
        
        for attr in spec.attributes:
            schema["properties"][attr.name] = self._get_property_schema(attr)
            if attr.required:
                schema["required"].append(attr.name)
        
        return schema
    
    def _generate_create_schema(self, spec: SDDSpecification) -> Dict[str, Any]:
        schema = {
            "type": "object",
            "required": [],
            "properties": {},
        }
        
        for attr in spec.attributes:
            schema["properties"][attr.name] = self._get_property_schema(attr)
            if attr.required:
                schema["required"].append(attr.name)
        
        return schema
    
    def _generate_update_schema(self, spec: SDDSpecification) -> Dict[str, Any]:
        schema = {
            "type": "object",
            "properties": {},
        }
        
        for attr in spec.attributes:
            schema["properties"][attr.name] = self._get_property_schema(attr)
        
        return schema
    
    def _get_property_schema(self, attr: SpecAttribute) -> Dict[str, Any]:
        schema = self._get_schema_for_type(attr.type)
        
        if attr.description:
            schema["description"] = attr.description
        
        if attr.enum_values:
            schema["enum"] = attr.enum_values
        
        if attr.example is not None:
            schema["example"] = attr.example
        
        if attr.constraints:
            if "minLength" in attr.constraints:
                schema["minLength"] = attr.constraints["minLength"]
            if "maxLength" in attr.constraints:
                schema["maxLength"] = attr.constraints["maxLength"]
            if "minimum" in attr.constraints:
                schema["minimum"] = attr.constraints["minimum"]
            if "maximum" in attr.constraints:
                schema["maximum"] = attr.constraints["maximum"]
            if "pattern" in attr.constraints:
                schema["pattern"] = attr.constraints["pattern"]
            if "format" in attr.constraints:
                schema["format"] = attr.constraints["format"]
        
        return schema
    
    def _get_schema_for_type(self, type_name: str) -> Dict[str, Any]:
        type_mapping = {
            "string": {"type": "string"},
            "text": {"type": "string"},
            "integer": {"type": "integer"},
            "bigint": {"type": "integer", "format": "int64"},
            "float": {"type": "number", "format": "float"},
            "boolean": {"type": "boolean"},
            "date": {"type": "string", "format": "date"},
            "datetime": {"type": "string", "format": "date-time"},
            "json": {"type": "object"},
            "array": {"type": "array", "items": {"type": "object"}},
            "enum": {"type": "string"},
        }
        return type_mapping.get(type_name, {"type": "string"})
    
    def _generate_tags(self, spec: SDDSpecification) -> List[Dict[str, Any]]:
        return [
            {
                "name": spec.metadata.name,
                "description": spec.spec.get("description", f"{spec.metadata.name}相关操作"),
            }
        ]
    
    def _to_kebab_case(self, name: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
    
    def _to_pascal_case(self, name: str) -> str:
        components = re.split(r'[_\s-]', name)
        return ''.join(x.title() for x in components if x)


class PostmanCollectionGenerator:
    """Postman Collection生成器"""
    
    def generate(self, spec: SDDSpecification) -> GeneratedDocument:
        collection = {
            "info": {
                "name": f"{spec.metadata.name} API",
                "description": spec.spec.get("description", ""),
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": self._generate_items(spec),
            "variable": [
                {
                    "key": "base_url",
                    "value": "http://localhost:8000",
                    "type": "string",
                },
                {
                    "key": "api_version",
                    "value": "v1",
                    "type": "string",
                },
            ],
        }
        
        content = json.dumps(collection, ensure_ascii=False, indent=2)
        filename = f"{self._to_kebab_case(spec.metadata.name)}-postman.json"
        
        return GeneratedDocument(
            filename=filename,
            content=content,
            format=DocFormat.POSTMAN,
            content_type="application/json",
        )
    
    def _generate_items(self, spec: SDDSpecification) -> List[Dict[str, Any]]:
        items = []
        
        for endpoint in spec.endpoints:
            items.append(self._generate_item(endpoint, spec))
        
        if not items and spec.kind == SpecType.ENTITY:
            items = self._generate_crud_items(spec)
        
        return items
    
    def _generate_crud_items(self, spec: SDDSpecification) -> List[Dict[str, Any]]:
        base_path = "{{base_url}}/api/{{api_version}}/{self._to_kebab_case(spec.metadata.name)}s"
        entity_name = self._to_pascal_case(spec.metadata.name)
        
        return [
            {
                "name": f"List {spec.metadata.name}",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": f"{base_path}?skip=0&limit=100",
                        "query": [
                            {"key": "skip", "value": "0"},
                            {"key": "limit", "value": "100"},
                        ],
                    },
                },
            },
            {
                "name": f"Create {spec.metadata.name}",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps(self._generate_example_data(spec), ensure_ascii=False, indent=2),
                    },
                    "url": {"raw": base_path},
                },
            },
            {
                "name": f"Get {spec.metadata.name} by ID",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {"raw": f"{base_path}/1"},
                },
            },
            {
                "name": f"Update {spec.metadata.name}",
                "request": {
                    "method": "PUT",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps(self._generate_example_data(spec), ensure_ascii=False, indent=2),
                    },
                    "url": {"raw": f"{base_path}/1"},
                },
            },
            {
                "name": f"Delete {spec.metadata.name}",
                "request": {
                    "method": "DELETE",
                    "header": [],
                    "url": {"raw": f"{base_path}/1"},
                },
            },
        ]
    
    def _generate_item(self, endpoint: SpecEndpoint, spec: SDDSpecification) -> Dict[str, Any]:
        base_path = "{{base_url}}"
        
        item = {
            "name": endpoint.name,
            "request": {
                "method": endpoint.method.upper(),
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "url": {
                    "raw": f"{base_path}{endpoint.path}",
                    "path": endpoint.path.strip("/").split("/"),
                },
                "description": endpoint.description,
            },
        }
        
        if endpoint.request_body:
            item["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(endpoint.request_body, ensure_ascii=False, indent=2),
            }
        
        return item
    
    def _generate_example_data(self, spec: SDDSpecification) -> Dict[str, Any]:
        data = {}
        for attr in spec.attributes:
            if attr.example is not None:
                data[attr.name] = attr.example
            elif attr.default is not None:
                data[attr.name] = attr.default
            elif attr.enum_values:
                data[attr.name] = attr.enum_values[0]
            elif attr.type == "string":
                data[attr.name] = f"example_{attr.name}"
            elif attr.type in ["integer", "bigint"]:
                data[attr.name] = 1
            elif attr.type == "float":
                data[attr.name] = 1.0
            elif attr.type == "boolean":
                data[attr.name] = True
        return data
    
    def _to_kebab_case(self, name: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
    
    def _to_pascal_case(self, name: str) -> str:
        components = re.split(r'[_\s-]', name)
        return ''.join(x.title() for x in components if x)


class MarkdownDocGenerator:
    """Markdown API文档生成器"""
    
    def generate(self, spec: SDDSpecification) -> GeneratedDocument:
        lines = [
            f"# {spec.metadata.name} API 文档",
            "",
            f"**版本**: {spec.metadata.version}",
            f"**规范ID**: {spec.metadata.id}",
            f"**生成时间**: {datetime.now().isoformat()}",
            "",
            "## 概述",
            "",
            spec.spec.get("description", ""),
            "",
            "## 基础URL",
            "",
            "```\nhttp://localhost:8000/api/v1\n```",
            "",
            "## 认证",
            "",
            "本API使用Bearer Token进行认证。请在请求头中添加：",
            "",
            "```\nAuthorization: Bearer <your_token>\n```",
            "",
        ]
        
        if spec.endpoints:
            lines.extend(self._generate_endpoints_section(spec))
        elif spec.kind == SpecType.ENTITY:
            lines.extend(self._generate_crud_section(spec))
        
        lines.extend(self._generate_models_section(spec))
        lines.extend(self._generate_examples_section(spec))
        
        content = "\n".join(lines)
        filename = f"{self._to_kebab_case(spec.metadata.name)}-api.md"
        
        return GeneratedDocument(
            filename=filename,
            content=content,
            format=DocFormat.MARKDOWN,
            content_type="text/markdown",
        )
    
    def _generate_endpoints_section(self, spec: SDDSpecification) -> List[str]:
        lines = ["## API端点", ""]
        
        for endpoint in spec.endpoints:
            lines.extend([
                f"### {endpoint.name}",
                "",
                f"**{endpoint.method.upper()}** `{endpoint.path}`",
                "",
                f"{endpoint.description}",
                "",
            ])
            
            if endpoint.parameters:
                lines.extend([
                    "#### 参数",
                    "",
                    "| 名称 | 位置 | 类型 | 必填 | 描述 |",
                    "|------|------|------|------|------|",
                ])
                for param in endpoint.parameters:
                    lines.append(
                        f"| {param.get('name', '')} | {param.get('location', 'query')} | "
                        f"{param.get('type', 'string')} | {'是' if param.get('required') else '否'} | "
                        f"{param.get('description', '')} |"
                    )
                lines.append("")
            
            if endpoint.errors:
                lines.extend([
                    "#### 错误响应",
                    "",
                    "| 状态码 | 描述 |",
                    "|--------|------|",
                ])
                for error in endpoint.errors:
                    lines.append(f"| {error.get('statusCode', 400)} | {error.get('message', '')} |")
                lines.append("")
        
        return lines
    
    def _generate_crud_section(self, spec: SDDSpecification) -> List[str]:
        base_path = f"/{self._to_kebab_case(spec.metadata.name)}s"
        
        return [
            "## API端点",
            "",
            f"### 获取{spec.metadata.name}列表",
            "",
            f"**GET** `{base_path}`",
            "",
            "#### 参数",
            "",
            "| 名称 | 位置 | 类型 | 必填 | 描述 |",
            "|------|------|------|------|------|",
            "| skip | query | integer | 否 | 跳过的记录数，默认0 |",
            "| limit | query | integer | 否 | 返回的记录数，默认100 |",
            "",
            f"### 创建{spec.metadata.name}",
            "",
            f"**POST** `{base_path}`",
            "",
            f"### 获取{spec.metadata.name}详情",
            "",
            f"**GET** `{base_path}/{{id}}`",
            "",
            f"### 更新{spec.metadata.name}",
            "",
            f"**PUT** `{base_path}/{{id}}`",
            "",
            f"### 删除{spec.metadata.name}",
            "",
            f"**DELETE** `{base_path}/{{id}}`",
            "",
        ]
    
    def _generate_models_section(self, spec: SDDSpecification) -> List[str]:
        lines = [
            "## 数据模型",
            "",
            f"### {spec.metadata.name}",
            "",
            "| 字段 | 类型 | 必填 | 描述 |",
            "|------|------|------|------|",
        ]
        
        lines.append("| id | integer | 是 | 唯一标识符 |")
        
        for attr in spec.attributes:
            lines.append(
                f"| {attr.name} | {attr.type} | {'是' if attr.required else '否'} | {attr.description or '-'} |"
            )
        
        lines.extend([
            "| createdAt | datetime | 是 | 创建时间 |",
            "| updatedAt | datetime | 是 | 更新时间 |",
            "",
        ])
        
        return lines
    
    def _generate_examples_section(self, spec: SDDSpecification) -> List[str]:
        example_data = {}
        for attr in spec.attributes:
            if attr.example is not None:
                example_data[attr.name] = attr.example
            elif attr.type == "string":
                example_data[attr.name] = f"example_{attr.name}"
            elif attr.type in ["integer", "bigint"]:
                example_data[attr.name] = 1
            elif attr.type == "float":
                example_data[attr.name] = 1.0
            elif attr.type == "boolean":
                example_data[attr.name] = True
        
        return [
            "## 示例",
            "",
            "### 请求示例",
            "",
            "```json",
            json.dumps(example_data, ensure_ascii=False, indent=2),
            "```",
            "",
            "### 响应示例",
            "",
            "```json",
            json.dumps({
                "id": 1,
                **example_data,
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
            }, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    
    def _to_kebab_case(self, name: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()


class APIDocGenerator:
    """API文档生成器主类"""
    
    def __init__(self):
        self.generators = {
            DocFormat.OPENAPI: OpenAPIGenerator(),
            DocFormat.POSTMAN: PostmanCollectionGenerator(),
            DocFormat.MARKDOWN: MarkdownDocGenerator(),
        }
    
    def generate(
        self,
        spec: SDDSpecification,
        formats: List[DocFormat] = None,
        output_dir: str = "docs/api"
    ) -> List[GeneratedDocument]:
        if formats is None:
            formats = [DocFormat.OPENAPI, DocFormat.MARKDOWN]
        
        results = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for doc_format in formats:
            generator = self.generators.get(doc_format)
            if not generator:
                print(f"警告: 不支持的文档格式 {doc_format}")
                continue
            
            doc = generator.generate(spec)
            
            file_path = output_path / doc.filename
            file_path.write_text(doc.content, encoding="utf-8")
            
            results.append(doc)
            print(f"生成API文档: {file_path}")
        
        return results
    
    def generate_from_spec_file(
        self,
        spec_path: str,
        formats: List[DocFormat] = None,
        output_dir: str = "docs/api"
    ) -> List[GeneratedDocument]:
        from sdd_spec_parser import SDDSpecParserEnhanced
        
        parser = SDDSpecParserEnhanced()
        spec, validation_result = parser.parse_file(spec_path)
        
        if not validation_result.is_valid:
            print("规范验证失败:")
            for err in validation_result.errors:
                print(f"  - [{err.path}] {err.message}")
            return []
        
        return self.generate(spec, formats, output_dir)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="SDD规范API文档生成器")
    parser.add_argument("spec_file", help="规范文件路径")
    parser.add_argument(
        "--format",
        "-f",
        choices=["openapi", "postman", "markdown", "all"],
        default="all",
        help="文档格式 (默认: all)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="docs/api",
        help="输出目录 (默认: docs/api)"
    )
    
    args = parser.parse_args()
    
    if args.format == "all":
        formats = [DocFormat.OPENAPI, DocFormat.POSTMAN, DocFormat.MARKDOWN]
    else:
        format_map = {
            "openapi": DocFormat.OPENAPI,
            "postman": DocFormat.POSTMAN,
            "markdown": DocFormat.MARKDOWN,
        }
        formats = [format_map[args.format]]
    
    generator = APIDocGenerator()
    
    try:
        results = generator.generate_from_spec_file(args.spec_file, formats, args.output)
        
        print(f"\n生成完成:")
        for result in results:
            print(f"  - {result.filename} ({result.format.value})")
    
    except FileNotFoundError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"生成错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
