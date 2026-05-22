#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规范到代码骨架生成器

实现从SDD规范自动生成代码骨架，支持：
1. 多种编程语言（Python、TypeScript、Java、Go）
2. 多种代码类型（Model、Service、Controller、DTO）
3. 代码风格检查
4. 依赖注入
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class CodeLanguage(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    CSHARP = "csharp"
    RUST = "rust"


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
class CodeSkeleton:
    filename: str
    content: str
    artifact_type: CodeArtifactType
    language: CodeLanguage
    dependencies: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    style_issues: List[Dict[str, Any]] = field(default_factory=list)


class BaseCodeGenerator(ABC):
    """代码生成器基类"""
    
    @abstractmethod
    def get_language(self) -> CodeLanguage:
        pass
    
    @abstractmethod
    def generate_model(self, spec) -> CodeSkeleton:
        pass
    
    @abstractmethod
    def generate_service(self, spec) -> CodeSkeleton:
        pass
    
    @abstractmethod
    def generate_controller(self, spec) -> CodeSkeleton:
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
    
    def get_language(self) -> CodeLanguage:
        return CodeLanguage.PYTHON
    
    def generate_model(self, spec) -> CodeSkeleton:
        class_name = self._to_pascal_case(spec.metadata.name)
        table_name = self._to_snake_case(spec.metadata.name)
        
        lines = [
            '"""',
            f'{spec.metadata.name} 数据模型',
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
        
        return CodeSkeleton(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.MODEL,
            language=self.get_language(),
            dependencies=["sqlalchemy", "pydantic"],
        )
    
    def _get_sqlalchemy_column(self, attr) -> str:
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
    
    def _get_python_type(self, attr) -> str:
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
    
    def generate_service(self, spec) -> CodeSkeleton:
        class_name = self._to_pascal_case(spec.metadata.name)
        model_name = f"{class_name}Model"
        
        lines = [
            '"""',
            f'{spec.metadata.name} 服务层',
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
        
        return CodeSkeleton(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.SERVICE,
            language=self.get_language(),
            dependencies=["sqlalchemy", "fastapi"],
        )
    
    def generate_controller(self, spec) -> CodeSkeleton:
        class_name = self._to_pascal_case(spec.metadata.name)
        router_name = f"{self._to_snake_case(spec.metadata.name)}_router"
        
        lines = [
            '"""',
            f'{spec.metadata.name} API路由',
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
        
        return CodeSkeleton(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.CONTROLLER,
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
    
    def _generate_endpoint_handler(self, endpoint, class_name: str) -> List[str]:
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
    
    def get_language(self) -> CodeLanguage:
        return CodeLanguage.TYPESCRIPT
    
    def generate_model(self, spec) -> CodeSkeleton:
        class_name = self._to_pascal_case(spec.metadata.name)
        
        lines = [
            '/**',
            f' * {spec.metadata.name} 数据模型',
            f' * 规范ID: {spec.metadata.id}',
            f' * 规范版本: {spec.metadata.version}',
            f' * 生成时间: {datetime.now().isoformat()}',
            ' */',
            '',
            'import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn } from "typeorm";',
            'import { IsString, IsNumber, IsBoolean, IsDate, IsOptional, IsEnum, MinLength, MaxLength, Min, Max } from "class-validator";',
            '',
            '',
            f'@Entity("{self._to_snake_case(spec.metadata.name)}")',
            f'export class {class_name} {{',
            '    @PrimaryGeneratedColumn()',
            '    id: number;',
            '',
        ]
        
        for attr in spec.attributes:
            ts_type = self._get_typescript_type(attr)
            decorators = self._get_typeorm_decorators(attr)
            
            lines.append(f'    @Column({{ nullable: {str(not attr.required).lower()} }})')
            if attr.constraints:
                validation_decorators = self._get_validation_decorators(attr)
                for vd in validation_decorators:
                    lines.append(f'    {vd}')
            lines.append(f'    {attr.name}: {ts_type};')
            lines.append('')
        
        lines.extend([
            '    @CreateDateColumn()',
            '    createdAt: Date;',
            '',
            '    @UpdateDateColumn()',
            '    updatedAt: Date;',
            '}',
            '',
        ])
        
        lines.extend([
            '/**',
            f' * {spec.metadata.name} DTO',
            ' */',
            f'export class Create{class_name}Dto {{',
        ])
        
        for attr in spec.attributes:
            ts_type = self._get_typescript_type(attr)
            optional = '?' if not attr.required else ''
            lines.append(f'    {attr.name}{optional}: {ts_type};')
        
        lines.extend([
            '}',
            '',
            f'export class Update{class_name}Dto {{',
        ])
        
        for attr in spec.attributes:
            ts_type = self._get_typescript_type(attr)
            lines.append(f'    {attr.name}?: {ts_type};')
        
        lines.extend([
            '}',
            '',
            f'export class {class_name}Response {{',
            '    id: number;',
        ])
        
        for attr in spec.attributes:
            ts_type = self._get_typescript_type(attr)
            lines.append(f'    {attr.name}: {ts_type};')
        
        lines.extend([
            '    createdAt: Date;',
            '    updatedAt: Date;',
            '}',
            '',
        ])
        
        filename = f"{self._to_kebab_case(spec.metadata.name)}.entity.ts"
        
        return CodeSkeleton(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.MODEL,
            language=self.get_language(),
            dependencies=["typeorm", "class-validator"],
        )
    
    def _get_typescript_type(self, attr) -> str:
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
    
    def _get_typeorm_decorators(self, attr) -> List[str]:
        decorators = ['@Column()']
        return decorators
    
    def _get_validation_decorators(self, attr) -> List[str]:
        decorators = []
        
        if attr.required:
            decorators.append('@IsNotEmpty()')
        
        if attr.type in ["string", "text"]:
            decorators.append('@IsString()')
            if "minLength" in attr.constraints:
                decorators.append(f'@MinLength({attr.constraints["minLength"]})')
            if "maxLength" in attr.constraints:
                decorators.append(f'@MaxLength({attr.constraints["maxLength"]})')
        elif attr.type in ["integer", "bigint", "float"]:
            decorators.append('@IsNumber()')
            if "min" in attr.constraints:
                decorators.append(f'@Min({attr.constraints["min"]})')
            if "max" in attr.constraints:
                decorators.append(f'@Max({attr.constraints["max"]})')
        elif attr.type == "boolean":
            decorators.append('@IsBoolean()')
        elif attr.type == "date":
            decorators.append('@IsDate()')
        
        return decorators
    
    def generate_service(self, spec) -> CodeSkeleton:
        class_name = self._to_pascal_case(spec.metadata.name)
        kebab_name = self._to_kebab_case(spec.metadata.name)
        
        lines = [
            '/**',
            f' * {spec.metadata.name} 服务层',
            f' * 规范ID: {spec.metadata.id}',
            f' * 生成时间: {datetime.now().isoformat()}',
            ' */',
            '',
            'import { Injectable, NotFoundException } from "@nestjs/common";',
            'import { InjectRepository } from "@nestjs/typeorm";',
            'import { Repository } from "typeorm";',
            f'import {{ {class_name}, Create{class_name}Dto, Update{class_name}Dto, {class_name}Response }} from "../entities/{kebab_name}.entity";',
            '',
            '',
            '@Injectable()',
            f'export class {class_name}Service {{',
            '    constructor(',
            f'        @InjectRepository({class_name})',
            f'        private repository: Repository<{class_name}>,',
            '    ) {}',
            '',
            f'    async create(dto: Create{class_name}Dto): Promise<{class_name}Response> {{',
            f'        const entity = this.repository.create(dto);',
            '        const saved = await this.repository.save(entity);',
            '        return this.toResponse(saved);',
            '    }',
            '',
            f'    async findById(id: number): Promise<{class_name}Response | null> {{',
            f'        const entity = await this.repository.findOne({{ where: {{ id }} }});',
            '        return entity ? this.toResponse(entity) : null;',
            '    }',
            '',
            f'    async findAll(skip: number = 0, limit: number = 100): Promise<{class_name}Response[]> {{',
            '        const entities = await this.repository.find({ skip, take: limit });',
            '        return entities.map(this.toResponse);',
            '    }',
            '',
            f'    async update(id: number, dto: Update{class_name}Dto): Promise<{class_name}Response | null> {{',
            f'        const entity = await this.repository.findOne({{ where: {{ id }} }});',
            '        if (!entity) return null;',
            '        Object.assign(entity, dto);',
            '        const saved = await this.repository.save(entity);',
            '        return this.toResponse(saved);',
            '    }',
            '',
            '    async delete(id: number): Promise<boolean> {',
            f'        const entity = await this.repository.findOne({{ where: {{ id }} }});',
            '        if (!entity) return false;',
            '        await this.repository.remove(entity);',
            '        return true;',
            '    }',
            '',
            f'    private toResponse(entity: {class_name}): {class_name}Response {{',
            '        return {',
            '            id: entity.id,',
        ]
        
        for attr in spec.attributes:
            lines.append(f'            {attr.name}: entity.{attr.name},')
        
        lines.extend([
            '            createdAt: entity.createdAt,',
            '            updatedAt: entity.updatedAt,',
            '        };',
            '    }',
            '}',
            '',
        ])
        
        filename = f"{kebab_name}.service.ts"
        
        return CodeSkeleton(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.SERVICE,
            language=self.get_language(),
            dependencies=["@nestjs/common", "@nestjs/typeorm", "typeorm"],
        )
    
    def generate_controller(self, spec) -> CodeSkeleton:
        class_name = self._to_pascal_case(spec.metadata.name)
        kebab_name = self._to_kebab_case(spec.metadata.name)
        
        lines = [
            '/**',
            f' * {spec.metadata.name} API控制器',
            f' * 规范ID: {spec.metadata.id}',
            f' * 生成时间: {datetime.now().isoformat()}',
            ' */',
            '',
            'import { Controller, Get, Post, Put, Delete, Body, Param, Query, NotFoundException } from "@nestjs/common";',
            f'import {{ {class_name}Service }} from "../services/{kebab_name}.service";',
            f'import {{ Create{class_name}Dto, Update{class_name}Dto, {class_name}Response }} from "../entities/{kebab_name}.entity";',
            '',
            '',
            f'@Controller("{kebab_name}s")',
            f'export class {class_name}Controller {{',
            f'    constructor(private readonly service: {class_name}Service) {{}}',
            '',
            f'    @Post()',
            f'    async create(@Body() dto: Create{class_name}Dto): Promise<{class_name}Response> {{',
            '        return this.service.create(dto);',
            '    }',
            '',
            '    @Get(":id")',
            f'    async findById(@Param("id") id: string): Promise<{class_name}Response> {{',
            '        const result = await this.service.findById(Number(id));',
            '        if (!result) throw new NotFoundException();',
            '        return result;',
            '    }',
            '',
            '    @Get()',
            f'    async findAll(',
            '        @Query("skip") skip?: string,',
            '        @Query("limit") limit?: string,',
            f'    ): Promise<{class_name}Response[]> {{',
            '        return this.service.findAll(Number(skip) || 0, Number(limit) || 100);',
            '    }',
            '',
            '    @Put(":id")',
            f'    async update(',
            '        @Param("id") id: string,',
            f'        @Body() dto: Update{class_name}Dto,',
            f'    ): Promise<{class_name}Response> {{',
            '        const result = await this.service.update(Number(id), dto);',
            '        if (!result) throw new NotFoundException();',
            '        return result;',
            '    }',
            '',
            '    @Delete(":id")',
            '    async delete(@Param("id") id: string): Promise<void> {',
            '        const success = await this.service.delete(Number(id));',
            '        if (!success) throw new NotFoundException();',
            '    }',
            '}',
            '',
        ]
        
        filename = f"{kebab_name}.controller.ts"
        
        return CodeSkeleton(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.CONTROLLER,
            language=self.get_language(),
            dependencies=["@nestjs/common"],
        )


class JavaCodeGenerator(BaseCodeGenerator):
    """Java代码生成器"""
    
    def get_language(self) -> CodeLanguage:
        return CodeLanguage.JAVA
    
    def generate_model(self, spec) -> CodeSkeleton:
        class_name = self._to_pascal_case(spec.metadata.name)
        table_name = self._to_snake_case(spec.metadata.name)
        
        lines = [
            '/**',
            f' * {spec.metadata.name} 数据模型',
            f' * 规范ID: {spec.metadata.id}',
            f' * 规范版本: {spec.metadata.version}',
            f' * 生成时间: {datetime.now().isoformat()}',
            ' */',
            '',
            'package com.example.entity;',
            '',
            'import jakarta.persistence.*;',
            'import jakarta.validation.constraints.*;',
            'import java.time.LocalDateTime;',
            'import java.util.Date;',
            '',
            '',
            f'@Entity',
            f'@Table(name = "{table_name}")',
            f'public class {class_name} {{',
            '',
            '    @Id',
            '    @GeneratedValue(strategy = GenerationType.IDENTITY)',
            '    private Long id;',
            '',
        ]
        
        for attr in spec.attributes:
            java_type = self._get_java_type(attr)
            
            lines.append(f'    @Column(nullable = {str(not attr.required).lower()})')
            
            if attr.constraints:
                if "minLength" in attr.constraints:
                    lines.append(f'    @Size(min = {attr.constraints["minLength"]})')
                if "maxLength" in attr.constraints:
                    lines.append(f'    @Size(max = {attr.constraints["maxLength"]})')
                if "min" in attr.constraints:
                    lines.append(f'    @Min({attr.constraints["min"]})')
                if "max" in attr.constraints:
                    lines.append(f'    @Max({attr.constraints["max"]})')
            
            if attr.required:
                lines.append('    @NotNull')
            
            lines.append(f'    private {java_type} {attr.name};')
            lines.append('')
        
        lines.extend([
            '    @Column(name = "created_at")',
            '    private LocalDateTime createdAt;',
            '',
            '    @Column(name = "updated_at")',
            '    private LocalDateTime updatedAt;',
            '',
        ])
        
        lines.append('    // Getters and Setters')
        lines.append('')
        
        for attr in spec.attributes:
            java_type = self._get_java_type(attr)
            getter_name = f"get{self._to_pascal_case(attr.name)}"
            setter_name = f"set{self._to_pascal_case(attr.name)}"
            
            lines.append(f'    public {java_type} {getter_name}() {{')
            lines.append(f'        return this.{attr.name};')
            lines.append('    }')
            lines.append('')
            lines.append(f'    public void {setter_name}({java_type} {attr.name}) {{')
            lines.append(f'        this.{attr.name} = {attr.name};')
            lines.append('    }')
            lines.append('')
        
        lines.extend([
            '    @PrePersist',
            '    protected void onCreate() {',
            '        createdAt = LocalDateTime.now();',
            '        updatedAt = LocalDateTime.now();',
            '    }',
            '',
            '    @PreUpdate',
            '    protected void onUpdate() {',
            '        updatedAt = LocalDateTime.now();',
            '    }',
            '}',
            '',
        ])
        
        filename = f"{class_name}.java"
        
        return CodeSkeleton(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.MODEL,
            language=self.get_language(),
            dependencies=["jakarta.persistence", "jakarta.validation"],
        )
    
    def _get_java_type(self, attr) -> str:
        type_mapping = {
            "string": "String",
            "text": "String",
            "integer": "Integer",
            "bigint": "Long",
            "float": "Double",
            "boolean": "Boolean",
            "date": "Date",
            "datetime": "LocalDateTime",
            "json": "String",
            "array": "String",
        }
        return type_mapping.get(attr.type, "String")
    
    def generate_service(self, spec) -> CodeSkeleton:
        class_name = self._to_pascal_case(spec.metadata.name)
        
        lines = [
            '/**',
            f' * {spec.metadata.name} 服务层',
            f' * 规范ID: {spec.metadata.id}',
            f' * 生成时间: {datetime.now().isoformat()}',
            ' */',
            '',
            'package com.example.service;',
            '',
            'import org.springframework.beans.factory.annotation.Autowired;',
            'import org.springframework.stereotype.Service;',
            'import org.springframework.transaction.annotation.Transactional;',
            'import com.example.entity.*;',
            'import com.example.repository.*;',
            'import java.util.List;',
            'import java.util.Optional;',
            '',
            '',
            '@Service',
            '@Transactional',
            f'public class {class_name}Service {{',
            '',
            '    @Autowired',
            f'    private {class_name}Repository repository;',
            '',
            f'    public {class_name} create({class_name} entity) {{',
            '        return repository.save(entity);',
            '    }',
            '',
            f'    public Optional<{class_name}> findById(Long id) {{',
            '        return repository.findById(id);',
            '    }',
            '',
            f'    public List<{class_name}> findAll(int skip, int limit) {{',
            '        return repository.findAll()',
            '            .stream()',
            '            .skip(skip)',
            '            .limit(limit)',
            '            .toList();',
            '    }',
            '',
            f'    public Optional<{class_name}> update(Long id, {class_name} entity) {{',
            '        return repository.findById(id)',
            '            .map(existing -> {',
            '                // TODO: Update fields',
            '                return repository.save(existing);',
            '            });',
            '    }',
            '',
            '    public boolean delete(Long id) {',
            '        if (repository.existsById(id)) {',
            '            repository.deleteById(id);',
            '            return true;',
            '        }',
            '        return false;',
            '    }',
            '}',
            '',
        ]
        
        filename = f"{class_name}Service.java"
        
        return CodeSkeleton(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.SERVICE,
            language=self.get_language(),
            dependencies=["spring-boot-starter-data-jpa"],
        )
    
    def generate_controller(self, spec) -> CodeSkeleton:
        class_name = self._to_pascal_case(spec.metadata.name)
        kebab_name = self._to_kebab_case(spec.metadata.name)
        
        lines = [
            '/**',
            f' * {spec.metadata.name} API控制器',
            f' * 规范ID: {spec.metadata.id}',
            f' * 生成时间: {datetime.now().isoformat()}',
            ' */',
            '',
            'package com.example.controller;',
            '',
            'import org.springframework.beans.factory.annotation.Autowired;',
            'import org.springframework.http.HttpStatus;',
            'import org.springframework.http.ResponseEntity;',
            'import org.springframework.web.bind.annotation.*;',
            'import com.example.entity.*;',
            'import com.example.service.*;',
            'import java.util.List;',
            'import java.util.Optional;',
            '',
            '',
            f'@RestController',
            f'@RequestMapping("/api/v1/{kebab_name}s")',
            f'public class {class_name}Controller {{',
            '',
            '    @Autowired',
            f'    private {class_name}Service service;',
            '',
            '    @PostMapping',
            f'    public ResponseEntity<{class_name}> create(@RequestBody {class_name} entity) {{',
            f'        {class_name} created = service.create(entity);',
            '        return ResponseEntity.status(HttpStatus.CREATED).body(created);',
            '    }',
            '',
            '    @GetMapping("/{id}")',
            f'    public ResponseEntity<{class_name}> findById(@PathVariable Long id) {{',
            f'        Optional<{class_name}> result = service.findById(id);',
            '        return result',
            '            .map(ResponseEntity::ok)',
            '            .orElse(ResponseEntity.notFound().build());',
            '    }',
            '',
            '    @GetMapping',
            f'    public List<{class_name}> findAll(',
            '        @RequestParam(defaultValue = "0") int skip,',
            '        @RequestParam(defaultValue = "100") int limit',
            '    ) {',
            '        return service.findAll(skip, limit);',
            '    }',
            '',
            '    @PutMapping("/{id}")',
            f'    public ResponseEntity<{class_name}> update(@PathVariable Long id, @RequestBody {class_name} entity) {{',
            f'        Optional<{class_name}> result = service.update(id, entity);',
            '        return result',
            '            .map(ResponseEntity::ok)',
            '            .orElse(ResponseEntity.notFound().build());',
            '    }',
            '',
            '    @DeleteMapping("/{id}")',
            '    public ResponseEntity<Void> delete(@PathVariable Long id) {',
            '        boolean success = service.delete(id);',
            '        return success',
            '            ? ResponseEntity.noContent().build()',
            '            : ResponseEntity.notFound().build();',
            '    }',
            '}',
            '',
        ]
        
        filename = f"{class_name}Controller.java"
        
        return CodeSkeleton(
            filename=filename,
            content="\n".join(lines),
            artifact_type=CodeArtifactType.CONTROLLER,
            language=self.get_language(),
            dependencies=["spring-boot-starter-web"],
        )


class SpecToCodeGenerator:
    """规范到代码生成器"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("generated")
        self.generators = {
            CodeLanguage.PYTHON: PythonCodeGenerator(),
            CodeLanguage.TYPESCRIPT: TypeScriptCodeGenerator(),
            CodeLanguage.JAVA: JavaCodeGenerator(),
        }
    
    def generate(
        self,
        spec,
        languages: Optional[List[CodeLanguage]] = None,
        output_dir: Optional[Path] = None
    ) -> List[CodeSkeleton]:
        if languages is None:
            languages = [CodeLanguage.PYTHON]
        
        if output_dir is None:
            output_dir = self.output_dir
        
        skeletons = []
        
        for language in languages:
            generator = self.generators.get(language)
            if not generator:
                print(f"警告: 不支持的编程语言 {language}")
                continue
            
            lang_dir = output_dir / language.value
            lang_dir.mkdir(parents=True, exist_ok=True)
            
            if spec.kind.value in ["EntitySpec", "ENTITY"]:
                model = generator.generate_model(spec)
                model_path = lang_dir / "models" / model.filename
                model_path.parent.mkdir(parents=True, exist_ok=True)
                model_path.write_text(model.content, encoding="utf-8")
                skeletons.append(model)
                print(f"生成模型文件: {model_path}")
                
                service = generator.generate_service(spec)
                service_path = lang_dir / "services" / service.filename
                service_path.parent.mkdir(parents=True, exist_ok=True)
                service_path.write_text(service.content, encoding="utf-8")
                skeletons.append(service)
                print(f"生成服务文件: {service_path}")
            
            if spec.kind.value in ["EntitySpec", "InterfaceSpec", "ApiSpec", "INTERFACE", "API"]:
                controller = generator.generate_controller(spec)
                controller_path = lang_dir / "routers" / controller.filename
                controller_path.parent.mkdir(parents=True, exist_ok=True)
                controller_path.write_text(controller.content, encoding="utf-8")
                skeletons.append(controller)
                print(f"生成路由文件: {controller_path}")
        
        return skeletons


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="规范到代码骨架生成器")
    parser.add_argument("spec_file", help="规范文件路径")
    parser.add_argument("--language", "-l", choices=["python", "typescript", "java", "all"], default="python", help="目标编程语言")
    parser.add_argument("--output", "-o", default="generated", help="输出目录")
    
    args = parser.parse_args()
    
    if args.language == "all":
        languages = [CodeLanguage.PYTHON, CodeLanguage.TYPESCRIPT, CodeLanguage.JAVA]
    else:
        language_map = {
            "python": CodeLanguage.PYTHON,
            "typescript": CodeLanguage.TYPESCRIPT,
            "java": CodeLanguage.JAVA,
        }
        languages = [language_map[args.language]]
    
    generator = SpecToCodeGenerator(output_dir=Path(args.output))
    
    try:
        from enhanced_spec_parser import EnhancedSDDSpecParser
        
        spec_parser = EnhancedSDDSpecParser()
        spec, validation_result = spec_parser.parse_file(args.spec_file)
        
        if not validation_result.is_valid:
            print("规范验证失败:")
            for err in validation_result.errors:
                print(f"  - [{err.path}] {err.message}")
            return
        
        skeletons = generator.generate(spec, languages, Path(args.output))
        
        print(f"\n生成完成:")
        print(f"  语言: {languages[0].value}")
        print(f"  文件数: {len(skeletons)}")
        for skeleton in skeletons:
            print(f"    - {skeleton.filename} ({skeleton.artifact_type.value})")
    
    except FileNotFoundError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"生成错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
