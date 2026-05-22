#!/usr/bin/env python3
"""
SDD规范代码骨架生成器

从SDD规范自动生成多种编程语言的代码骨架：
1. Python (FastAPI, SQLAlchemy, Pydantic)
2. TypeScript (Express, TypeORM, Zod)
3. Java (Spring Boot, JPA)
4. Go (Gin, GORM)

功能：
- 生成数据模型/实体类
- 生成API路由/控制器
- 生成服务层骨架
- 生成接口定义
- 生成数据传输对象(DTO)
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
from skillscripts.core.path_config_center import get_path_config

sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from pipeline.sdd_spec_parser import (
    SDDSpecification,
    SpecAttribute,
    SpecEndpoint,
    SpecScenario,
    SpecType,
)


class ProgrammingLanguage(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"


class CodeArtifactType(Enum):
    MODEL = "model"
    ENTITY = "entity"
    DTO = "dto"
    CONTROLLER = "controller"
    SERVICE = "service"
    REPOSITORY = "repository"
    INTERFACE = "interface"
    ROUTER = "router"


@dataclass
class GeneratedCode:
    filename: str
    content: str
    artifact_type: CodeArtifactType
    language: ProgrammingLanguage
    dependencies: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)


@dataclass
class GeneratedProject:
    language: ProgrammingLanguage
    files: List[GeneratedCode] = field(default_factory=list)
    structure: Dict[str, str] = field(default_factory=dict)


class BaseCodeGenerator(ABC):
    """代码生成器基类"""
    
    @abstractmethod
    def get_language(self) -> ProgrammingLanguage:
        pass
    
    @abstractmethod
    def generate_model(self, spec: SDDSpecification) -> GeneratedCode:
        pass
    
    @abstractmethod
    def generate_service(self, spec: SDDSpecification) -> GeneratedCode:
        pass
    
    @abstractmethod
    def generate_router(self, spec: SDDSpecification) -> GeneratedCode:
        pass
    
    def _to_snake_case(self, name: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_camel_case(self, name: str) -> str:
        components = name.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    def _to_pascal_case(self, name: str) -> str:
        components = re.split(r'[_\s-]', name)
        return ''.join(x.title() for x in components if x)
    
    def _to_kebab_case(self, name: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()


class PythonCodeGenerator(BaseCodeGenerator):
    """Python代码生成器"""
    
    def get_language(self) -> ProgrammingLanguage:
        return ProgrammingLanguage.PYTHON
    
    def generate_model(self, spec: SDDSpecification) -> GeneratedCode:
        class_name = self._to_pascal_case(spec.metadata.name)
        table_name = self._to_snake_case(spec.metadata.name)
        
        lines = [
            '"""',
            f'{spec.metadata.name} 数据模型',
            "",
            f"规范ID: {spec.metadata.id}",
            f"规范版本: {spec.metadata.version}",
            f"生成时间: {datetime.now().isoformat()}",
            '"""',
            "",
            "from datetime import date, datetime",
            "from typing import Optional, List, Any, Dict",
            "from sqlalchemy import Column, String, Integer, BigInteger, Float, Boolean, DateTime, Date, Text, JSON, ForeignKey",
            "from sqlalchemy.orm import relationship, Mapped, mapped_column",
            "from pydantic import BaseModel, Field, field_validator, ConfigDict",
            "from database import Base",
            "",
            "",
            f"class {class_name}Model(Base):",
            f'    """{spec.metadata.name} 数据库实体"""',
            f'    __tablename__ = "{table_name}"',
            "",
            "    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)",
        ]
        
        for attr in spec.attributes:
            column_def = self._get_sqlalchemy_column(attr)
            lines.append(f"    {attr.name}: Mapped[{self._get_python_type(attr)}] = {column_def}")
        
        lines.extend([
            "    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)",
            "    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)",
            "",
        ])
        
        for rel in spec.relationships:
            rel_name = rel.get("name", "")
            target = rel.get("target", "")
            rel_type = rel.get("type", "one_to_many")
            
            if rel_type == "one_to_many":
                lines.append(
                    f"    {self._to_snake_case(rel_name)}: Mapped[List['{self._to_pascal_case(target)}Model']] = relationship('{self._to_pascal_case(target)}Model', back_populates='{table_name}')"
                )
            elif rel_type == "many_to_one":
                lines.append(
                    f"    {self._to_snake_case(rel_name)}_id: Mapped[Optional[int]] = mapped_column(ForeignKey('{self._to_snake_case(target)}.id'), nullable=True)"
                )
                lines.append(
                    f"    {self._to_snake_case(rel_name)}: Mapped[Optional['{self._to_pascal_case(target)}Model']] = relationship('{self._to_pascal_case(target)}Model', back_populates='{table_name}s')"
                )
        
        lines.extend([
            "",
            "",
            f"class {class_name}Base(BaseModel):",
            f'    """{spec.metadata.name} 基础Schema"""',
            "    model_config = ConfigDict(from_attributes=True)",
            "",
        ])
        
        for attr in spec.attributes:
            py_type = self._get_python_type(attr)
            field_args = []
            
            if attr.description:
                field_args.append(f'description="{attr.description}"')
            
            if attr.default is not None:
                field_args.append(f"default={repr(attr.default)}")
            elif not attr.required:
                field_args.append("default=None")
            
            if attr.constraints:
                for constraint_name, constraint_value in attr.constraints.items():
                    if constraint_name == "minLength":
                        field_args.append(f"min_length={constraint_value}")
                    elif constraint_name == "maxLength":
                        field_args.append(f"max_length={constraint_value}")
                    elif constraint_name == "minimum":
                        field_args.append(f"ge={constraint_value}")
                    elif constraint_name == "maximum":
                        field_args.append(f"le={constraint_value}")
                    elif constraint_name == "pattern":
                        field_args.append(f'pattern=r"{constraint_value}"')
            
            if attr.required:
                if field_args:
                    lines.append(f"    {attr.name}: {py_type} = Field({', '.join(field_args)})")
                else:
                    lines.append(f"    {attr.name}: {py_type}")
            else:
                if field_args:
                    lines.append(f"    {attr.name}: Optional[{py_type}] = Field({', '.join(field_args)})")
                else:
                    lines.append(f"    {attr.name}: Optional[{py_type}] = None")
        
        lines.extend([
            "",
            "",
            f"class {class_name}Create({class_name}Base):",
            f'    """{spec.metadata.name} 创建Schema"""',
            "    pass",
            "",
            "",
            f"class {class_name}Update(BaseModel):",
            f'    """{spec.metadata.name} 更新Schema"""',
        ])
        
        for attr in spec.attributes:
            py_type = self._get_python_type(attr)
            lines.append(f"    {attr.name}: Optional[{py_type}] = None")
        
        lines.extend([
            "",
            "",
            f"class {class_name}Response({class_name}Base):",
            f'    """{spec.metadata.name} 响应Schema"""',
            "    id: int",
            "    created_at: datetime",
            "    updated_at: datetime",
            "",
        ])
        
        filename = f"{self._to_snake_case(spec.metadata.name)}_model.py"
        
        return GeneratedCode(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.MODEL,
            language=self.get_language(),
            dependencies=["sqlalchemy", "pydantic"],
        )
    
    def _get_sqlalchemy_column(self, attr: SpecAttribute) -> str:
        type_mapping = {
            "string": f"mapped_column(String({attr.constraints.get('maxLength', 255)}), nullable={not attr.required})",
            "text": "mapped_column(Text, nullable=False)",
            "integer": "mapped_column(Integer, nullable=False)",
            "bigint": "mapped_column(BigInteger, nullable=False)",
            "float": "mapped_column(Float, nullable=False)",
            "boolean": "mapped_column(Boolean, default=False)",
            "date": "mapped_column(Date, nullable=True)",
            "datetime": "mapped_column(DateTime, nullable=True)",
            "json": "mapped_column(JSON, nullable=True)",
        }
        
        base = type_mapping.get(attr.type, f"mapped_column(String(255), nullable={not attr.required})")
        
        if attr.unique:
            base = base.replace(")", ", unique=True)")
        
        return base
    
    def _get_python_type(self, attr: SpecAttribute) -> str:
        type_mapping = {
            "string": "str",
            "text": "str",
            "integer": "int",
            "bigint": "int",
            "float": "float",
            "boolean": "bool",
            "date": "date",
            "datetime": "datetime",
            "json": "Dict[str, Any]",
            "array": "List[Any]",
            "enum": "str",
        }
        return type_mapping.get(attr.type, "str")
    
    def generate_service(self, spec: SDDSpecification) -> GeneratedCode:
        class_name = self._to_pascal_case(spec.metadata.name)
        model_name = f"{class_name}Model"
        
        lines = [
            '"""',
            f'{spec.metadata.name} 服务层',
            "",
            f"规范ID: {spec.metadata.id}",
            f"生成时间: {datetime.now().isoformat()}",
            '"""',
            "",
            "from typing import List, Optional, Dict, Any",
            "from sqlalchemy.orm import Session",
            "from fastapi import HTTPException, status",
            "",
            f"from models.{self._to_snake_case(spec.metadata.name)}_model import (",
            f"    {model_name},",
            f"    {class_name}Create,",
            f"    {class_name}Update,",
            f"    {class_name}Response,",
            ")",
            "",
            "",
            f"class {class_name}Service:",
            f'    """{spec.metadata.name} 服务类"""',
            "",
            "    def __init__(self, db: Session):",
            "        self.db = db",
            "",
            f"    def create(self, data: {class_name}Create) -> {class_name}Response:",
            f'        """创建{spec.metadata.name}"""',
            f"        entity = {model_name}(**data.model_dump())",
            "        self.db.add(entity)",
            "        self.db.commit()",
            "        self.db.refresh(entity)",
            f"        return {class_name}Response.model_validate(entity)",
            "",
            f"    def get_by_id(self, entity_id: int) -> Optional[{class_name}Response]:",
            f'        """根据ID获取{spec.metadata.name}"""',
            f"        entity = self.db.query({model_name}).filter({model_name}.id == entity_id).first()",
            f"        return {class_name}Response.model_validate(entity) if entity else None",
            "",
            f"    def get_list(self, skip: int = 0, limit: int = 100) -> List[{class_name}Response]:",
            f'        """获取{spec.metadata.name}列表"""',
            f"        entities = self.db.query({model_name}).offset(skip).limit(limit).all()",
            f"        return [{class_name}Response.model_validate(e) for e in entities]",
            "",
            f"    def update(self, entity_id: int, data: {class_name}Update) -> Optional[{class_name}Response]:",
            f'        """更新{spec.metadata.name}"""',
            f"        entity = self.db.query({model_name}).filter({model_name}.id == entity_id).first()",
            "        if not entity:",
            "            return None",
            "        for key, value in data.model_dump(exclude_unset=True).items():",
            "            setattr(entity, key, value)",
            "        self.db.commit()",
            "        self.db.refresh(entity)",
            f"        return {class_name}Response.model_validate(entity)",
            "",
            "    def delete(self, entity_id: int) -> bool:",
            f'        """删除{spec.metadata.name}"""',
            f"        entity = self.db.query({model_name}).filter({model_name}.id == entity_id).first()",
            "        if not entity:",
            "            return False",
            "        self.db.delete(entity)",
            "        self.db.commit()",
            "        return True",
            "",
        ]
        
        filename = f"{self._to_snake_case(spec.metadata.name)}_service.py"
        
        return GeneratedCode(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.SERVICE,
            language=self.get_language(),
            dependencies=["sqlalchemy", "fastapi"],
        )
    
    def generate_router(self, spec: SDDSpecification) -> GeneratedCode:
        class_name = self._to_pascal_case(spec.metadata.name)
        router_name = f"{self._to_snake_case(spec.metadata.name)}_router"
        
        lines = [
            '"""',
            f'{spec.metadata.name} API路由',
            "",
            f"规范ID: {spec.metadata.id}",
            f"生成时间: {datetime.now().isoformat()}",
            '"""',
            "",
            "from typing import List",
            "from fastapi import APIRouter, Depends, HTTPException, status, Query",
            "from sqlalchemy.orm import Session",
            "",
            "from database import get_db",
            f"from services.{self._to_snake_case(spec.metadata.name)}_service import {class_name}Service",
            f"from models.{self._to_snake_case(spec.metadata.name)}_model import (",
            f"    {class_name}Create,",
            f"    {class_name}Update,",
            f"    {class_name}Response,",
            ")",
            "",
            f'router = APIRouter(prefix="/api/v1/{self._to_snake_case(spec.metadata.name)}s", tags=["{spec.metadata.name}"])',
            "",
            "",
        ]
        
        if spec.endpoints:
            for endpoint in spec.endpoints:
                lines.extend(self._generate_endpoint_handler(endpoint, class_name))
        else:
            lines.extend(self._generate_crud_endpoints(class_name))
        
        filename = f"{self._to_snake_case(spec.metadata.name)}_router.py"
        
        return GeneratedCode(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.ROUTER,
            language=self.get_language(),
            dependencies=["fastapi", "sqlalchemy"],
        )
    
    def _generate_crud_endpoints(self, class_name: str) -> List[str]:
        snake_name = self._to_snake_case(class_name)
        
        return [
            f"@router.post(\"/\", response_model={class_name}Response, status_code=status.HTTP_201_CREATED)",
            f"async def create_{snake_name}(",
            f"    data: {class_name}Create,",
            "    db: Session = Depends(get_db)",
            f"):",
            f'    """创建{class_name}"""',
            f"    service = {class_name}Service(db)",
            f"    return service.create(data)",
            "",
            "",
            f"@router.get(\"/{{entity_id}}\", response_model={class_name}Response)",
            f"async def get_{snake_name}(",
            "    entity_id: int,",
            "    db: Session = Depends(get_db)",
            "):",
            f'    """根据ID获取{class_name}"""',
            f"    service = {class_name}Service(db)",
            f"    entity = service.get_by_id(entity_id)",
            "    if not entity:",
            '        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")',
            "    return entity",
            "",
            "",
            f"@router.get(\"/\", response_model=List[{class_name}Response])",
            f"async def list_{snake_name}s(",
            "    skip: int = Query(0, ge=0),",
            "    limit: int = Query(100, ge=1, le=1000),",
            "    db: Session = Depends(get_db)",
            "):",
            f'    """获取{class_name}列表"""',
            f"    service = {class_name}Service(db)",
            f"    return service.get_list(skip, limit)",
            "",
            "",
            f"@router.put(\"/{{entity_id}}\", response_model={class_name}Response)",
            f"async def update_{snake_name}(",
            "    entity_id: int,",
            f"    data: {class_name}Update,",
            "    db: Session = Depends(get_db)",
            "):",
            f'    """更新{class_name}"""',
            f"    service = {class_name}Service(db)",
            f"    entity = service.update(entity_id, data)",
            "    if not entity:",
            '        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")',
            "    return entity",
            "",
            "",
            f"@router.delete(\"/{{entity_id}}\", status_code=status.HTTP_204_NO_CONTENT)",
            f"async def delete_{snake_name}(",
            "    entity_id: int,",
            "    db: Session = Depends(get_db)",
            "):",
            f'    """删除{class_name}"""',
            f"    service = {class_name}Service(db)",
            "    success = service.delete(entity_id)",
            "    if not success:",
            '        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")',
            "",
        ]
    
    def _generate_endpoint_handler(self, endpoint: SpecEndpoint, class_name: str) -> List[str]:
        method = endpoint.method.lower()
        path = endpoint.path
        
        lines = [
            f'@router.{method}("{path}")',
            f"async def {endpoint.name}(",
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
            "    db: Session = Depends(get_db)",
            "):",
            f'    """{endpoint.description}"""',
            f"    service = {class_name}Service(db)",
            "    # TODO: 实现业务逻辑",
            '    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")',
            "",
            "",
        ])
        
        return lines


class TypeScriptCodeGenerator(BaseCodeGenerator):
    """TypeScript代码生成器"""
    
    def get_language(self) -> ProgrammingLanguage:
        return ProgrammingLanguage.TYPESCRIPT
    
    def generate_model(self, spec: SDDSpecification) -> GeneratedCode:
        class_name = self._to_pascal_case(spec.metadata.name)
        
        lines = [
            f"/**",
            f" * {spec.metadata.name} 数据模型",
            f" *",
            f" * 规范ID: {spec.metadata.id}",
            f" * 规范版本: {spec.metadata.version}",
            f" * 生成时间: {datetime.now().isoformat()}",
            f" */",
            "",
            "import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn } from 'typeorm';",
            "import { IsString, IsNumber, IsBoolean, IsDate, IsOptional, IsEmail, Min, Max, MinLength, MaxLength, validate } from 'class-validator';",
            "",
            "",
            f"@Entity('{self._to_snake_case(spec.metadata.name)}')",
            f"export class {class_name} {{",
            "    @PrimaryGeneratedColumn()",
            "    id!: number;",
            "",
        ]
        
        for attr in spec.attributes:
            decorators = self._get_typeorm_decorators(attr)
            validation_decorators = self._get_validation_decorators(attr)
            
            for decorator in decorators:
                lines.append(f"    {decorator}")
            for decorator in validation_decorators:
                lines.append(f"    {decorator}")
            
            ts_type = self._get_typescript_type(attr)
            optional = "" if attr.required else "?"
            lines.append(f"    {attr.name}{optional}: {ts_type};")
            lines.append("")
        
        lines.extend([
            "    @CreateDateColumn()",
            "    createdAt!: Date;",
            "",
            "    @UpdateDateColumn()",
            "    updatedAt!: Date;",
            "}",
            "",
        ])
        
        lines.extend(self._generate_dto_classes(spec, class_name))
        
        filename = f"{self._to_snake_case(spec.metadata.name)}.entity.ts"
        
        return GeneratedCode(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.ENTITY,
            language=self.get_language(),
            dependencies=["typeorm", "class-validator"],
        )
    
    def _get_typeorm_decorators(self, attr: SpecAttribute) -> List[str]:
        decorators = []
        
        type_mapping = {
            "string": f"String",
            "text": "Text",
            "integer": "Integer",
            "bigint": "BigInt",
            "float": "Float",
            "boolean": "Boolean",
            "date": "Date",
            "datetime": "Datetime",
            "json": "Json",
        }
        
        column_type = type_mapping.get(attr.type, "String")
        
        options = []
        if not attr.required:
            options.append("nullable: true")
        if attr.unique:
            options.append("unique: true")
        
        if attr.constraints.get("maxLength"):
            options.append(f"length: {attr.constraints['maxLength']}")
        
        if options:
            decorators.append(f"@Column({{ type: '{column_type.lower()}', {', '.join(options)} }})")
        else:
            decorators.append(f"@Column()")
        
        return decorators
    
    def _get_validation_decorators(self, attr: SpecAttribute) -> List[str]:
        decorators = []
        
        if attr.required:
            pass
        
        type_validators = {
            "string": "@IsString()",
            "integer": "@IsNumber()",
            "bigint": "@IsNumber()",
            "float": "@IsNumber()",
            "boolean": "@IsBoolean()",
            "date": "@IsDate()",
            "datetime": "@IsDate()",
        }
        
        if attr.type in type_validators:
            decorators.append(type_validators[attr.type])
        
        if attr.constraints.get("minLength"):
            decorators.append(f"@MinLength({attr.constraints['minLength']})")
        if attr.constraints.get("maxLength"):
            decorators.append(f"@MaxLength({attr.constraints['maxLength']})")
        if attr.constraints.get("minimum"):
            decorators.append(f"@Min({attr.constraints['minimum']})")
        if attr.constraints.get("maximum"):
            decorators.append(f"@Max({attr.constraints['maximum']})")
        
        if not attr.required:
            decorators.append("@IsOptional()")
        
        return decorators
    
    def _get_typescript_type(self, attr: SpecAttribute) -> str:
        type_mapping = {
            "string": "string",
            "text": "string",
            "integer": "number",
            "bigint": "number",
            "float": "number",
            "boolean": "boolean",
            "date": "Date",
            "datetime": "Date",
            "json": "Record<string, any>",
            "array": "any[]",
            "enum": "string",
        }
        return type_mapping.get(attr.type, "string")
    
    def _generate_dto_classes(self, spec: SDDSpecification, class_name: str) -> List[str]:
        lines = []
        
        lines.extend([
            f"export class Create{class_name}Dto {{",
        ])
        
        for attr in spec.attributes:
            ts_type = self._get_typescript_type(attr)
            optional = "" if attr.required else "?"
            lines.append(f"    {attr.name}{optional}: {ts_type};")
        
        lines.extend([
            "}",
            "",
            "",
            f"export class Update{class_name}Dto {{",
        ])
        
        for attr in spec.attributes:
            ts_type = self._get_typescript_type(attr)
            lines.append(f"    {attr.name}?: {ts_type};")
        
        lines.extend([
            "}",
            "",
            "",
            f"export class {class_name}ResponseDto {{",
            "    id!: number;",
        ])
        
        for attr in spec.attributes:
            ts_type = self._get_typescript_type(attr)
            lines.append(f"    {attr.name}!: {ts_type};")
        
        lines.extend([
            "    createdAt!: Date;",
            "    updatedAt!: Date;",
            "}",
            "",
        ])
        
        return lines
    
    def generate_service(self, spec: SDDSpecification) -> GeneratedCode:
        class_name = self._to_pascal_case(spec.metadata.name)
        snake_name = self._to_snake_case(spec.metadata.name)
        
        lines = [
            f"/**",
            f" * {spec.metadata.name} 服务层",
            f" */",
            "",
            f"import {{ Injectable }} from '@nestjs/common';",
            f"import {{ InjectRepository }} from '@nestjs/typeorm';",
            f"import {{ Repository }} from 'typeorm';",
            f"import {{ {class_name}, Create{class_name}Dto, Update{class_name}Dto, {class_name}ResponseDto }} from './{snake_name}.entity';",
            "",
            "",
            f"@Injectable()",
            f"export class {class_name}Service {{",
            "    constructor(",
            f"        @InjectRepository({class_name})",
            f"        private repository: Repository<{class_name}>,",
            "    ) {}",
            "",
            f"    async create(dto: Create{class_name}Dto): Promise<{class_name}ResponseDto> {{",
            f"        const entity = this.repository.create(dto);",
            f"        return await this.repository.save(entity);",
            "    }",
            "",
            f"    async findById(id: number): Promise<{class_name}ResponseDto | null> {{",
            f"        return await this.repository.findOne({{ where: {{ id }} }});",
            "    }",
            "",
            f"    async findAll(skip: number = 0, limit: number = 100): Promise<{class_name}ResponseDto[]> {{",
            f"        return await this.repository.find({{ skip, take: limit }});",
            "    }",
            "",
            f"    async update(id: number, dto: Update{class_name}Dto): Promise<{class_name}ResponseDto | null> {{",
            f"        const entity = await this.findById(id);",
            "        if (!entity) return null;",
            f"        Object.assign(entity, dto);",
            f"        return await this.repository.save(entity);",
            "    }",
            "",
            "    async delete(id: number): Promise<boolean> {",
            f"        const result = await this.repository.delete(id);",
            "        return result.affected > 0;",
            "    }",
            "}",
            "",
        ]
        
        filename = f"{snake_name}.service.ts"
        
        return GeneratedCode(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.SERVICE,
            language=self.get_language(),
            dependencies=["@nestjs/common", "@nestjs/typeorm", "typeorm"],
        )
    
    def generate_router(self, spec: SDDSpecification) -> GeneratedCode:
        class_name = self._to_pascal_case(spec.metadata.name)
        snake_name = self._to_snake_case(spec.metadata.name)
        
        lines = [
            f"/**",
            f" * {spec.metadata.name} 控制器",
            f" */",
            "",
            f"import {{ Controller, Get, Post, Put, Delete, Body, Param, Query }} from '@nestjs/common';",
            f"import {{ {class_name}Service }} from './{snake_name}.service';",
            f"import {{ Create{class_name}Dto, Update{class_name}Dto, {class_name}ResponseDto }} from './{snake_name}.entity';",
            "",
            "",
            f"@Controller('{snake_name}s')",
            f"export class {class_name}Controller {{",
            "    constructor(private readonly service: {class_name}Service) {}",
            "",
            f"    @Post()",
            f"    async create(@Body() dto: Create{class_name}Dto): Promise<{class_name}ResponseDto> {{",
            "        return await this.service.create(dto);",
            "    }",
            "",
            f"    @Get(':id')",
            f"    async findById(@Param('id') id: string): Promise<{class_name}ResponseDto | null> {{",
            "        return await this.service.findById(Number(id));",
            "    }",
            "",
            f"    @Get()",
            f"    async findAll(",
            "        @Query('skip') skip?: string,",
            "        @Query('limit') limit?: string,",
            f"    ): Promise<{class_name}ResponseDto[]> {{",
            "        return await this.service.findAll(Number(skip) || 0, Number(limit) || 100);",
            "    }",
            "",
            f"    @Put(':id')",
            f"    async update(",
            "        @Param('id') id: string,",
            f"        @Body() dto: Update{class_name}Dto,",
            f"    ): Promise<{class_name}ResponseDto | null> {{",
            "        return await this.service.update(Number(id), dto);",
            "    }",
            "",
            f"    @Delete(':id')",
            "    async delete(@Param('id') id: string): Promise<boolean> {",
            "        return await this.service.delete(Number(id));",
            "    }",
            "}",
            "",
        ]
        
        filename = f"{snake_name}.controller.ts"
        
        return GeneratedCode(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.CONTROLLER,
            language=self.get_language(),
            dependencies=["@nestjs/common"],
        )


class MultiLanguageCodeGenerator:
    """多语言代码生成器"""
    
    def __init__(self):
        self.generators = {
            ProgrammingLanguage.PYTHON: PythonCodeGenerator(),
            ProgrammingLanguage.TYPESCRIPT: TypeScriptCodeGenerator(),
        }
    
    def generate(
        self,
        spec: SDDSpecification,
        languages: List[ProgrammingLanguage] = None,
        output_dir: str = None
    ) -> GeneratedProject:
        if languages is None:
            languages = [ProgrammingLanguage.PYTHON]
        
        if output_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                output_dir = str(_path_mgr.get_output_path(OutputType.REPORT, subdirectory="generated"))
            except Exception:
                output_dir = "generated"
        
        project = GeneratedProject(language=languages[0])
        output_path = Path(output_dir)
        
        for language in languages:
            generator = self.generators.get(language)
            if not generator:
                print(f"警告: 不支持的编程语言 {language}")
                continue
            
            lang_dir = output_path / language.value
            lang_dir.mkdir(parents=True, exist_ok=True)
            
            if spec.kind == SpecType.ENTITY:
                model = generator.generate_model(spec)
                model_path = lang_dir / "models" / model.filename
                model_path.parent.mkdir(parents=True, exist_ok=True)
                model_path.write_text(model.content, encoding="utf-8")
                project.files.append(model)
                print(f"生成模型文件: {model_path}")
                
                service = generator.generate_service(spec)
                service_path = lang_dir / "services" / service.filename
                service_path.parent.mkdir(parents=True, exist_ok=True)
                service_path.write_text(service.content, encoding="utf-8")
                project.files.append(service)
                print(f"生成服务文件: {service_path}")
            
            if spec.kind in [SpecType.ENTITY, SpecType.INTERFACE, SpecType.API]:
                router = generator.generate_router(spec)
                router_path = lang_dir / "routers" / router.filename
                router_path.parent.mkdir(parents=True, exist_ok=True)
                router_path.write_text(router.content, encoding="utf-8")
                project.files.append(router)
                print(f"生成路由文件: {router_path}")
        
        project.structure = self._generate_project_structure(project)
        
        return project
    
    def _generate_project_structure(self, project: GeneratedProject) -> Dict[str, str]:
        structure = {}
        for file in project.files:
            structure[file.filename] = f"{file.language.value}/{file.artifact_type.value}"
        return structure
    
    def generate_from_spec_file(
        self,
        spec_path: str,
        languages: List[ProgrammingLanguage] = None,
        output_dir: str = "generated"
    ) -> GeneratedProject:
        from sdd_spec_parser import SDDSpecParserEnhanced
        
        parser = SDDSpecParserEnhanced()
        spec, validation_result = parser.parse_file(spec_path)
        
        if not validation_result.is_valid:
            print("规范验证失败:")
            for err in validation_result.errors:
                print(f"  - [{err.path}] {err.message}")
            return GeneratedProject(language=ProgrammingLanguage.PYTHON)
        
        return self.generate(spec, languages, output_dir)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="SDD规范多语言代码生成器")
    parser.add_argument("spec_file", help="规范文件路径")
    parser.add_argument(
        "--language",
        "-l",
        choices=["python", "typescript", "all"],
        default="python",
        help="目标编程语言 (默认: python)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="generated",
        help="输出目录 (默认: generated)"
    )
    
    args = parser.parse_args()
    
    if args.language == "all":
        languages = [ProgrammingLanguage.PYTHON, ProgrammingLanguage.TYPESCRIPT]
    else:
        language_map = {
            "python": ProgrammingLanguage.PYTHON,
            "typescript": ProgrammingLanguage.TYPESCRIPT,
        }
        languages = [language_map[args.language]]
    
    generator = MultiLanguageCodeGenerator()
    
    try:
        project = generator.generate_from_spec_file(args.spec_file, languages, args.output)
        
        print(f"\n生成完成:")
        print(f"  语言: {project.language.value}")
        print(f"  文件数: {len(project.files)}")
        for file in project.files:
            print(f"    - {file.filename} ({file.artifact_type.value})")
    
    except FileNotFoundError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"生成错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
