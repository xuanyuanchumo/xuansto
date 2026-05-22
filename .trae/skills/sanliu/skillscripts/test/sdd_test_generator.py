#!/usr/bin/env python3
"""
SDD Test Generator - SDD规范驱动测试用例生成器

从SDD规范文件自动生成测试用例和代码骨架。

功能：
1. 解析SDD规范文件（YAML/JSON格式）
2. 生成测试用例（pytest格式）
3. 生成代码骨架（Python/TypeScript）
4. 支持验收标准到测试用例的转换
5. 支持约束条件到验证测试的转换

使用示例：
    python sdd_test_generator.py --spec specs/auth/user.entity.spec.yaml --output tests/
    python sdd_test_generator.py --spec specs/auth/api.spec.yaml --generate both --output generated/
"""

import argparse
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml


class SpecKind(Enum):
    ENTITY = "EntitySpec"
    INTERFACE = "InterfaceSpec"
    RULE = "RuleSpec"
    CONSTRAINT = "ConstraintSpec"
    ACCEPTANCE = "AcceptanceSpec"


class GenerateMode(Enum):
    TEST = "test"
    CODE = "code"
    BOTH = "both"


@dataclass
class Attribute:
    name: str
    type: str
    required: bool = True
    unique: bool = False
    default: Any = None
    description: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)
    enum_values: List[str] = field(default_factory=list)


@dataclass
class Entity:
    name: str
    description: str
    attributes: List[Attribute]
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Endpoint:
    name: str
    method: str
    path: str
    description: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AcceptanceCriteria:
    name: str
    description: str
    scenarios: List[Dict[str, str]] = field(default_factory=list)
    test_data: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SpecMetadata:
    name: str
    version: str
    namespace: str
    status: str = "draft"
    author: str = ""
    created: str = ""
    modified: str = ""


@dataclass
class SDDSpec:
    api_version: str
    kind: SpecKind
    metadata: SpecMetadata
    spec: Dict[str, Any]


class SpecParser:
    """SDD规范解析器"""
    
    def __init__(self):
        self.type_mapping = {
            "string": "str",
            "integer": "int",
            "bigint": "int",
            "float": "float",
            "boolean": "bool",
            "date": "date",
            "datetime": "datetime",
            "json": "dict",
            "array": "list",
            "enum": "str",
        }
    
    def parse_file(self, file_path: str) -> SDDSpec:
        """解析规范文件"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"规范文件不存在: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in [".yaml", ".yml"]:
                content = yaml.safe_load(f)
            elif path.suffix == ".json":
                content = json.load(f)
            else:
                raise ValueError(f"不支持的文件格式: {path.suffix}")
        
        return self._parse_spec(content)
    
    def _parse_spec(self, content: Dict[str, Any]) -> SDDSpec:
        """解析规范内容"""
        api_version = content.get("apiVersion", "sdd/v1")
        kind = SpecKind(content.get("kind", "EntitySpec"))
        
        metadata_dict = content.get("metadata", {})
        metadata = SpecMetadata(
            name=metadata_dict.get("name", "Unknown"),
            version=metadata_dict.get("version", "1.0.0"),
            namespace=metadata_dict.get("namespace", "default"),
            status=metadata_dict.get("status", "draft"),
            author=metadata_dict.get("annotations", {}).get("author", ""),
            created=metadata_dict.get("annotations", {}).get("created", ""),
            modified=metadata_dict.get("annotations", {}).get("modified", ""),
        )
        
        return SDDSpec(
            api_version=api_version,
            kind=kind,
            metadata=metadata,
            spec=content.get("spec", {}),
        )
    
    def parse_entity(self, spec: SDDSpec) -> Entity:
        """解析实体规范"""
        spec_content = spec.spec
        attributes = []
        
        for attr_dict in spec_content.get("attributes", []):
            attr = Attribute(
                name=attr_dict.get("name", ""),
                type=attr_dict.get("type", "string"),
                required=attr_dict.get("required", True),
                unique=attr_dict.get("unique", False),
                default=attr_dict.get("defaultValue"),
                description=attr_dict.get("description", ""),
                constraints=attr_dict.get("validation", {}),
                enum_values=attr_dict.get("enumValues", []),
            )
            attributes.append(attr)
        
        return Entity(
            name=spec.metadata.name,
            description=spec_content.get("description", ""),
            attributes=attributes,
            relationships=spec_content.get("relationships", []),
            constraints=spec_content.get("constraints", []),
        )
    
    def parse_interface(self, spec: SDDSpec) -> List[Endpoint]:
        """解析接口规范"""
        endpoints = []
        spec_content = spec.spec
        
        for ep_dict in spec_content.get("endpoints", []):
            endpoint = Endpoint(
                name=ep_dict.get("name", ""),
                method=ep_dict.get("method", "GET"),
                path=ep_dict.get("path", "/"),
                description=ep_dict.get("description", ""),
                parameters=ep_dict.get("parameters", []),
                request_body=ep_dict.get("request", {}).get("body"),
                response=ep_dict.get("response", {}).get("body"),
                errors=ep_dict.get("errors", []),
            )
            endpoints.append(endpoint)
        
        return endpoints
    
    def parse_acceptance(self, spec: SDDSpec) -> AcceptanceCriteria:
        """解析验收标准规范"""
        spec_content = spec.spec
        
        return AcceptanceCriteria(
            name=spec.metadata.name,
            description=spec_content.get("description", ""),
            scenarios=spec_content.get("scenarios", []),
            test_data=spec_content.get("testData", []),
        )


class TestCaseGenerator:
    """测试用例生成器"""
    
    def __init__(self):
        self.indent = "    "
    
    def generate_entity_tests(self, entity: Entity, metadata: SpecMetadata) -> str:
        """生成实体测试用例"""
        test_class_name = f"Test{entity.name}"
        
        lines = [
            '"""',
            f'{entity.name} 实体测试',
            "",
            f"规范版本: {metadata.version}",
            f"命名空间: {metadata.namespace}",
            f"生成时间: {datetime.now().isoformat()}",
            '"""',
            "",
            "import pytest",
            "from datetime import date, datetime",
            "from typing import Optional",
            "from pydantic import ValidationError",
            "",
            "",
            f"class {test_class_name}:",
            f'    """{entity.description} 测试类"""',
            "",
        ]
        
        lines.extend(self._generate_attribute_tests(entity))
        lines.extend(self._generate_constraint_tests(entity))
        lines.extend(self._generate_relationship_tests(entity))
        
        return "\n".join(lines)
    
    def _generate_attribute_tests(self, entity: Entity) -> List[str]:
        """生成属性测试"""
        lines = []
        
        for attr in entity.attributes:
            test_name = f"test_{attr.name}_attribute"
            lines.extend([
                f"{self.indent}def {test_name}(self):",
                f'{self.indent*2}"""测试 {attr.name} 属性"""',
            ])
            
            if attr.required:
                lines.extend([
                    f"{self.indent*2}with pytest.raises(ValidationError):",
                    f"{self.indent*3}pass",
                ])
            
            if attr.enum_values:
                lines.extend([
                    f"{self.indent*2}valid_values = {attr.enum_values}",
                    f"{self.indent*2}for value in valid_values:",
                    f"{self.indent*3}assert value in valid_values",
                ])
            
            if attr.unique:
                lines.extend([
                    f"{self.indent*2}pass",
                ])
            
            lines.append("")
        
        return lines
    
    def _generate_constraint_tests(self, entity: Entity) -> List[str]:
        """生成约束测试"""
        lines = []
        
        for attr in entity.attributes:
            if attr.constraints:
                for constraint_name, constraint_value in attr.constraints.items():
                    test_name = f"test_{attr.name}_{constraint_name}_constraint"
                    lines.extend([
                        f"{self.indent}def {test_name}(self):",
                        f'{self.indent*2}"""测试 {attr.name} 的 {constraint_name} 约束"""',
                    ])
                    
                    if constraint_name == "pattern":
                        lines.extend([
                            f'{self.indent*2}import re',
                            f'{self.indent*2}pattern = r"{constraint_value}"',
                            f'{self.indent*2}assert re.match(pattern, "valid_value")',
                        ])
                    elif constraint_name == "format":
                        lines.extend([
                            f'{self.indent*2}pass',
                        ])
                    elif constraint_name in ["minLength", "maxLength"]:
                        lines.extend([
                            f'{self.indent*2}pass',
                        ])
                    
                    lines.append("")
        
        return lines
    
    def _generate_relationship_tests(self, entity: Entity) -> List[str]:
        """生成关系测试"""
        lines = []
        
        for rel in entity.relationships:
            test_name = f"test_{rel.get('name', 'relationship')}_relationship"
            lines.extend([
                f"{self.indent}def {test_name}(self):",
                f'{self.indent*2}"""测试 {rel.get("name", "")} 关系"""',
                f"{self.indent*2}pass",
                "",
            ])
        
        return lines
    
    def generate_api_tests(self, endpoints: List[Endpoint], metadata: SpecMetadata) -> str:
        """生成API测试用例"""
        test_class_name = f"Test{metadata.name}"
        
        lines = [
            '"""',
            f'{metadata.name} API测试',
            "",
            f"规范版本: {metadata.version}",
            f"命名空间: {metadata.namespace}",
            f"生成时间: {datetime.now().isoformat()}",
            '"""',
            "",
            "import pytest",
            "from fastapi.testclient import TestClient",
            "from http import HTTPStatus",
            "",
            "",
            f"class {test_class_name}:",
            f'    """{metadata.name} API测试类"""',
            "",
        ]
        
        for endpoint in endpoints:
            lines.extend(self._generate_endpoint_tests(endpoint))
        
        return "\n".join(lines)
    
    def _generate_endpoint_tests(self, endpoint: Endpoint) -> List[str]:
        """生成端点测试"""
        lines = []
        
        test_name = f"test_{endpoint.name}_success"
        lines.extend([
            f"{self.indent}def {test_name}(self, client: TestClient):",
            f'{self.indent*2}"""测试 {endpoint.name} 成功场景"""',
            f'{self.indent*2}response = client.{endpoint.method.lower()}("{endpoint.path}")',
            f"{self.indent*2}assert response.status_code == HTTPStatus.OK",
            "",
        ])
        
        for error in endpoint.errors:
            test_name = f"test_{endpoint.name}_error_{error.get('code', 'unknown')}"
            lines.extend([
                f"{self.indent}def {test_name}(self, client: TestClient):",
                f'{self.indent*2}"""测试 {endpoint.name} 错误场景: {error.get("message", "")}"""',
                f'{self.indent*2}response = client.{endpoint.method.lower()}("{endpoint.path}")',
                f"{self.indent*2}assert response.status_code == {error.get('statusCode', 400)}",
                "",
            ])
        
        return lines
    
    def generate_acceptance_tests(self, acceptance: AcceptanceCriteria, metadata: SpecMetadata) -> str:
        """生成验收测试用例"""
        test_class_name = f"Test{acceptance.name}"
        
        lines = [
            '"""',
            f'{acceptance.name} 验收测试',
            "",
            f"规范版本: {metadata.version}",
            f"生成时间: {datetime.now().isoformat()}",
            '"""',
            "",
            "import pytest",
            "from typing import Any",
            "",
            "",
            f"class {test_class_name}:",
            f'    """{acceptance.description}"""',
            "",
        ]
        
        for idx, scenario in enumerate(acceptance.scenarios):
            scenario_name = scenario.get("name", f"scenario_{idx}")
            given = scenario.get("given", "")
            when = scenario.get("when", "")
            then = scenario.get("then", "")
            
            test_name = f"test_{self._to_snake_case(scenario_name)}"
            lines.extend([
                f"{self.indent}def {test_name}(self):",
                f'{self.indent*2}"""',
                f"{self.indent*2}场景: {scenario_name}",
                f"{self.indent*2}Given: {given}",
                f"{self.indent*2}When: {when}",
                f"{self.indent*2}Then: {then}",
                f'{self.indent*2}"""',
                f"{self.indent*2}pass",
                "",
            ])
        
        return "\n".join(lines)
    
    def _to_snake_case(self, name: str) -> str:
        """转换为蛇形命名"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class CodeSkeletonGenerator:
    """代码骨架生成器"""
    
    def __init__(self):
        self.indent = "    "
    
    def generate_entity_model(self, entity: Entity, metadata: SpecMetadata) -> str:
        """生成实体模型代码"""
        class_name = entity.name
        
        lines = [
            '"""',
            f'{entity.description}',
            "",
            f"规范版本: {metadata.version}",
            f"命名空间: {metadata.namespace}",
            f"生成时间: {datetime.now().isoformat()}",
            '"""',
            "",
            "from datetime import date, datetime",
            "from typing import Optional, List",
            "from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey",
            "from sqlalchemy.orm import relationship",
            "from pydantic import BaseModel, Field, validator",
            "from database import Base",
            "",
            "",
            f"class {class_name}(Base):",
            f'    """{entity.description} 数据库模型"""',
            f'    __tablename__ = "{self._to_snake_case(entity.name)}"',
            "",
        ]
        
        for attr in entity.attributes:
            column_type = self._get_sqlalchemy_type(attr)
            column_args = []
            
            if attr.required:
                column_args.append("nullable=False")
            else:
                column_args.append("nullable=True")
            
            if attr.unique:
                column_args.append("unique=True")
            
            lines.append(
                f"    {attr.name} = Column({column_type}, {', '.join(column_args)})"
            )
        
        lines.extend(["", ""])
        
        for rel in entity.relationships:
            rel_name = rel.get("name", "")
            target = rel.get("target", "")
            rel_type = rel.get("type", "one_to_many")
            
            if rel_type == "one_to_many":
                lines.append(
                    f"    {self._to_snake_case(rel_name)} = relationship('{target}', back_populates='{entity.name.lower()}')"
                )
            elif rel_type == "many_to_one":
                lines.append(
                    f"    {self._to_snake_case(rel_name)} = relationship('{target}')"
                )
        
        lines.extend(["", ""])
        lines.extend(self._generate_pydantic_model(entity))
        
        return "\n".join(lines)
    
    def _get_sqlalchemy_type(self, attr: Attribute) -> str:
        """获取SQLAlchemy类型"""
        type_mapping = {
            "string": f"String({attr.constraints.get('length', 255)})",
            "text": "Text",
            "integer": "Integer",
            "bigint": "BigInteger",
            "float": "Float",
            "boolean": "Boolean",
            "date": "Date",
            "datetime": "DateTime",
            "json": "JSON",
        }
        return type_mapping.get(attr.type, "String(255)")
    
    def _generate_pydantic_model(self, entity: Entity) -> List[str]:
        """生成Pydantic模型"""
        class_name = f"{entity.name}Base"
        lines = [
            f"class {class_name}(BaseModel):",
            f'    """{entity.description} Pydantic模型"""',
        ]
        
        for attr in entity.attributes:
            py_type = self._get_python_type(attr)
            if attr.required:
                lines.append(f"    {attr.name}: {py_type}")
            else:
                lines.append(f"    {attr.name}: Optional[{py_type}] = None")
        
        lines.extend([
            "",
            "    class Config:",
            "        from_attributes = True",
        ])
        
        return lines
    
    def _get_python_type(self, attr: Attribute) -> str:
        """获取Python类型"""
        type_mapping = {
            "string": "str",
            "text": "str",
            "integer": "int",
            "bigint": "int",
            "float": "float",
            "boolean": "bool",
            "date": "date",
            "datetime": "datetime",
            "json": "dict",
            "array": "list",
            "enum": "str",
        }
        return type_mapping.get(attr.type, "str")
    
    def generate_api_router(self, endpoints: List[Endpoint], metadata: SpecMetadata) -> str:
        """生成API路由代码"""
        router_name = f"{metadata.name.lower()}_router"
        
        lines = [
            '"""',
            f'{metadata.name} API路由',
            "",
            f"规范版本: {metadata.version}",
            f"生成时间: {datetime.now().isoformat()}",
            '"""',
            "",
            "from fastapi import APIRouter, Depends, HTTPException, status",
            "from typing import List, Optional",
            "from pydantic import BaseModel",
            "",
            f'router = APIRouter(prefix="{metadata.spec.get("baseUrl", "")}", tags=["{metadata.name}"])',
            "",
            "",
        ]
        
        for endpoint in endpoints:
            lines.extend(self._generate_endpoint_handler(endpoint))
        
        return "\n".join(lines)
    
    def _generate_endpoint_handler(self, endpoint: Endpoint) -> List[str]:
        """生成端点处理函数"""
        handler_name = endpoint.name
        
        lines = [
            f'@router.{endpoint.method.lower()}("{endpoint.path}")',
            f"async def {handler_name}(",
        ]
        
        params = []
        for param in endpoint.parameters:
            param_name = param.get("name", "")
            param_type = param.get("type", "str")
            required = param.get("required", True)
            
            if required:
                params.append(f"    {param_name}: {param_type}")
            else:
                params.append(f"    {param_name}: Optional[{param_type}] = None")
        
        lines.extend(params)
        lines.extend([
            "):",
            f'    """{endpoint.description}"""',
        ])
        
        if endpoint.errors:
            lines.extend([
                "    # TODO: 实现业务逻辑",
                "    # 错误处理:",
            ])
            for error in endpoint.errors:
                lines.append(f"    # - {error.get('code')}: {error.get('message')}")
        
        lines.extend([
            "    raise HTTPException(",
            '        status_code=status.HTTP_501_NOT_IMPLEMENTED,',
            '        detail="Not implemented"',
            "    )",
            "",
            "",
        ])
        
        return lines
    
    def generate_service_skeleton(self, entity: Entity, metadata: SpecMetadata) -> str:
        """生成服务层骨架"""
        service_name = f"{entity.name}Service"
        
        lines = [
            '"""',
            f'{entity.name} 服务层',
            "",
            f"规范版本: {metadata.version}",
            f"生成时间: {datetime.now().isoformat()}",
            '"""',
            "",
            "from typing import List, Optional",
            "from sqlalchemy.orm import Session",
            "from models import Base",
            f"from models.{entity.name.lower()} import {entity.name}",
            "",
            "",
            f"class {service_name}:",
            f'    """{entity.description} 服务"""',
            "",
            f"    def __init__(self, db: Session):",
            f"        self.db = db",
            "",
            f"    def create(self, data: dict) -> {entity.name}:",
            f'        """创建{entity.description}"""',
            f"        entity = {entity.name}(**data)",
            f"        self.db.add(entity)",
            f"        self.db.commit()",
            f"        self.db.refresh(entity)",
            f"        return entity",
            "",
            f"    def get_by_id(self, id: int) -> Optional[{entity.name}]:",
            f'        """根据ID获取{entity.description}"""',
            f"        return self.db.query({entity.name}).filter({entity.name}.id == id).first()",
            "",
            f"    def get_list(self, skip: int = 0, limit: int = 100) -> List[{entity.name}]:",
            f'        """获取{entity.description}列表"""',
            f"        return self.db.query({entity.name}).offset(skip).limit(limit).all()",
            "",
            f"    def update(self, id: int, data: dict) -> Optional[{entity.name}]:",
            f'        """更新{entity.description}"""',
            f"        entity = self.get_by_id(id)",
            f"        if entity:",
            f"            for key, value in data.items():",
            f"                setattr(entity, key, value)",
            f"            self.db.commit()",
            f"            self.db.refresh(entity)",
            f"        return entity",
            "",
            f"    def delete(self, id: int) -> bool:",
            f'        """删除{entity.description}"""',
            f"        entity = self.get_by_id(id)",
            f"        if entity:",
            f"            self.db.delete(entity)",
            f"            self.db.commit()",
            f"            return True",
            f"        return False",
            "",
        ]
        
        return "\n".join(lines)
    
    def _to_snake_case(self, name: str) -> str:
        """转换为蛇形命名"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class SDDTestGenerator:
    """SDD测试生成器主类"""
    
    def __init__(self):
        self.parser = SpecParser()
        self.test_generator = TestCaseGenerator()
        self.code_generator = CodeSkeletonGenerator()
    
    def generate(
        self,
        spec_path: str,
        output_dir: str,
        mode: GenerateMode = GenerateMode.BOTH,
    ) -> Dict[str, str]:
        """
        生成测试用例和代码骨架
        
        Args:
            spec_path: 规范文件路径
            output_dir: 输出目录
            mode: 生成模式（test/code/both）
        
        Returns:
            生成的文件路径字典
        """
        spec = self.parser.parse_file(spec_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        result = {}
        
        if spec.kind == SpecKind.ENTITY:
            entity = self.parser.parse_entity(spec)
            
            if mode in [GenerateMode.TEST, GenerateMode.BOTH]:
                test_content = self.test_generator.generate_entity_tests(entity, spec.metadata)
                test_file = output_path / f"test_{entity.name.lower()}.py"
                test_file.write_text(test_content, encoding="utf-8")
                result["test"] = str(test_file)
            
            if mode in [GenerateMode.CODE, GenerateMode.BOTH]:
                model_content = self.code_generator.generate_entity_model(entity, spec.metadata)
                model_file = output_path / f"{entity.name.lower()}.py"
                model_file.write_text(model_content, encoding="utf-8")
                result["model"] = str(model_file)
                
                service_content = self.code_generator.generate_service_skeleton(entity, spec.metadata)
                service_file = output_path / f"{entity.name.lower()}_service.py"
                service_file.write_text(service_content, encoding="utf-8")
                result["service"] = str(service_file)
        
        elif spec.kind == SpecKind.INTERFACE:
            endpoints = self.parser.parse_interface(spec)
            
            if mode in [GenerateMode.TEST, GenerateMode.BOTH]:
                test_content = self.test_generator.generate_api_tests(endpoints, spec.metadata)
                test_file = output_path / f"test_{spec.metadata.name.lower()}_api.py"
                test_file.write_text(test_content, encoding="utf-8")
                result["test"] = str(test_file)
            
            if mode in [GenerateMode.CODE, GenerateMode.BOTH]:
                router_content = self.code_generator.generate_api_router(endpoints, spec.metadata)
                router_file = output_path / f"{spec.metadata.name.lower()}_router.py"
                router_file.write_text(router_content, encoding="utf-8")
                result["router"] = str(router_file)
        
        elif spec.kind == SpecKind.ACCEPTANCE:
            acceptance = self.parser.parse_acceptance(spec)
            
            if mode in [GenerateMode.TEST, GenerateMode.BOTH]:
                test_content = self.test_generator.generate_acceptance_tests(acceptance, spec.metadata)
                test_file = output_path / f"test_{acceptance.name.lower()}_acceptance.py"
                test_file.write_text(test_content, encoding="utf-8")
                result["test"] = str(test_file)
        
        return result
    
    def generate_from_directory(
        self,
        spec_dir: str,
        output_dir: str,
        mode: GenerateMode = GenerateMode.BOTH,
    ) -> Dict[str, Dict[str, str]]:
        """
        从目录批量生成
        
        Args:
            spec_dir: 规范文件目录
            output_dir: 输出目录
            mode: 生成模式
        
        Returns:
            每个规范文件的生成结果
        """
        spec_path = Path(spec_dir)
        results = {}
        
        for spec_file in spec_path.glob("**/*.spec.yaml"):
            try:
                relative_path = spec_file.relative_to(spec_path)
                output_subdir = Path(output_dir) / relative_path.parent
                result = self.generate(str(spec_file), str(output_subdir), mode)
                results[str(spec_file)] = result
            except Exception as e:
                results[str(spec_file)] = {"error": str(e)}
        
        for spec_file in spec_path.glob("**/*.spec.json"):
            try:
                relative_path = spec_file.relative_to(spec_path)
                output_subdir = Path(output_dir) / relative_path.parent
                result = self.generate(str(spec_file), str(output_subdir), mode)
                results[str(spec_file)] = result
            except Exception as e:
                results[str(spec_file)] = {"error": str(e)}
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="SDD规范驱动测试用例生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从单个规范文件生成测试用例
  python sdd_test_generator.py --spec specs/auth/user.entity.spec.yaml --output tests/
  
  # 生成代码骨架
  python sdd_test_generator.py --spec specs/auth/user.entity.spec.yaml --generate code --output generated/
  
  # 同时生成测试和代码
  python sdd_test_generator.py --spec specs/auth/ --output generated/ --generate both
  
  # 批量处理目录
  python sdd_test_generator.py --spec specs/ --output generated/ --batch
        """
    )
    
    parser.add_argument(
        "--spec",
        required=True,
        help="规范文件或目录路径"
    )
    
    parser.add_argument(
        "--output",
        required=True,
        help="输出目录路径"
    )
    
    parser.add_argument(
        "--generate",
        choices=["test", "code", "both"],
        default="both",
        help="生成模式: test(仅测试), code(仅代码), both(全部)"
    )
    
    parser.add_argument(
        "--batch",
        action="store_true",
        help="批量处理目录下的所有规范文件"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细输出"
    )
    
    args = parser.parse_args()
    
    generator = SDDTestGenerator()
    mode = GenerateMode(args.generate)
    
    if args.batch:
        results = generator.generate_from_directory(args.spec, args.output, mode)
        print(f"批量生成完成，共处理 {len(results)} 个规范文件")
        
        if args.verbose:
            for spec_file, result in results.items():
                print(f"\n{spec_file}:")
                if "error" in result:
                    print(f"  错误: {result['error']}")
                else:
                    for key, path in result.items():
                        print(f"  {key}: {path}")
    else:
        result = generator.generate(args.spec, args.output, mode)
        print(f"生成完成:")
        for key, path in result.items():
            print(f"  {key}: {path}")


if __name__ == "__main__":
    main()
