#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
External Skill Integrator - 外部技能集成器

用于优化外部技能调用体验，统一管理 skill-creator、ui-ux-pro-max 和 mcp-builder 的调用。

使用方法:
    python external_skill_integrator.py [command] [options]

命令:
    skill        - 技能创建和管理
    ui           - UI/UX 设计和生成
    mcp          - MCP 服务构建和管理
    status       - 查看集成状态
    config       - 配置管理

示例:
    python external_skill_integrator.py skill create --name=my-skill --template=basic
    python external_skill_integrator.py ui design --type=page --name=dashboard --framework=react
    python external_skill_integrator.py mcp build --name=my-server --language=python
    python external_skill_integrator.py status --all
"""

import os
import sys
import json
import logging
import argparse
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from abc import ABC, abstractmethod
from skillscripts.utils.path_config_manager import PathConfigManager


_path_manager = PathConfigManager()
LOGS_DIR = _path_manager.get_skillscripts_path() / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / 'external_skill_integrator.log', encoding='utf-8', mode='a')
    ]
)
logger = logging.getLogger(__name__)


class SkillType(Enum):
    BASIC = "basic"
    ADVANCED = "advanced"
    AGENT = "agent"
    PIPELINE = "pipeline"
    INTEGRATION = "integration"


class UIFramework(Enum):
    REACT = "react"
    VUE = "vue"
    SVELTE = "svelte"
    NEXT_JS = "next.js"
    ANGULAR = "angular"


class MCPLanguage(Enum):
    PYTHON = "python"
    NODE_TYPESCRIPT = "node_typescript"


class MCPTransport(Enum):
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"


class IntegrationStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    RUNNING = "running"


@dataclass
class IntegrationResult:
    status: IntegrationStatus
    message: str
    data: Dict[str, Any] = None
    output_files: List[str] = None
    errors: List[str] = None
    warnings: List[str] = None
    duration_ms: int = 0
    timestamp: str = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.output_files is None:
            self.output_files = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_json(self) -> str:
        result = asdict(self)
        result['status'] = self.status.value
        return json.dumps(result, ensure_ascii=False, indent=2)


@dataclass
class SkillTemplate:
    name: str
    description: str
    skill_type: SkillType
    structure: Dict[str, Any]
    required_files: List[str]
    optional_files: List[str]
    config_template: Dict[str, Any]


@dataclass
class UIComponentSpec:
    name: str
    component_type: str
    framework: UIFramework
    props: Dict[str, Any]
    styles: Dict[str, str]
    accessibility: Dict[str, Any]
    responsive: bool = True


@dataclass
class MCPServerConfig:
    name: str
    language: MCPLanguage
    transport: MCPTransport
    tools: List[Dict[str, Any]]
    resources: List[Dict[str, Any]]
    prompts: List[Dict[str, Any]]
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ExternalSkillIntegrator:
    """外部技能集成器主类"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.path_manager = PathConfigManager()
        self._init_paths()
        self._init_templates()
        logger.info(f"ExternalSkillIntegrator initialized at {self.project_root}")
    
    def _init_paths(self):
        self.skill_creator_path = self.project_root / ".trae" / "skills" / "skill-creator"
        self.ui_ux_path = self.project_root / ".trae" / "skills" / "ui-ux-pro-max"
        self.mcp_builder_path = self.project_root / ".trae" / "skills" / "mcp-builder"
        
        self.output_dir = self.path_manager.get_skillscripts_path() / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_templates(self):
        self.skill_templates = {
            SkillType.BASIC: SkillTemplate(
                name="basic",
                description="基础技能模板，包含 SKILL.md 和基本结构",
                skill_type=SkillType.BASIC,
                structure={
                    "SKILL.md": True,
                    "scripts/": True,
                    "assets/": False
                },
                required_files=["SKILL.md"],
                optional_files=["scripts/", "assets/", "references/"],
                config_template={
                    "name": "",
                    "description": "",
                    "version": "1.0.0"
                }
            ),
            SkillType.ADVANCED: SkillTemplate(
                name="advanced",
                description="高级技能模板，包含完整的项目结构",
                skill_type=SkillType.ADVANCED,
                structure={
                    "SKILL.md": True,
                    "scripts/": True,
                    "agents/": True,
                    "references/": True,
                    "assets/": True
                },
                required_files=["SKILL.md", "scripts/"],
                optional_files=["agents/", "references/", "assets/", "evals/"],
                config_template={
                    "name": "",
                    "description": "",
                    "version": "1.0.0",
                    "dependencies": [],
                    "agents": []
                }
            ),
            SkillType.AGENT: SkillTemplate(
                name="agent",
                description="Agent 技能模板，专注于智能代理功能",
                skill_type=SkillType.AGENT,
                structure={
                    "SKILL.md": True,
                    "agents/": True,
                    "scripts/": True,
                    "references/": True
                },
                required_files=["SKILL.md", "agents/"],
                optional_files=["scripts/", "references/"],
                config_template={
                    "name": "",
                    "description": "",
                    "version": "1.0.0",
                    "agent_type": "assistant",
                    "capabilities": []
                }
            ),
            SkillType.PIPELINE: SkillTemplate(
                name="pipeline",
                description="流水线技能模板，用于自动化工作流",
                skill_type=SkillType.PIPELINE,
                structure={
                    "SKILL.md": True,
                    "scripts/": True,
                    "pipeline/": True,
                    "references/": True
                },
                required_files=["SKILL.md", "scripts/", "pipeline/"],
                optional_files=["references/", "assets/"],
                config_template={
                    "name": "",
                    "description": "",
                    "version": "1.0.0",
                    "stages": [],
                    "triggers": []
                }
            ),
            SkillType.INTEGRATION: SkillTemplate(
                name="integration",
                description="集成技能模板，用于外部服务集成",
                skill_type=SkillType.INTEGRATION,
                structure={
                    "SKILL.md": True,
                    "scripts/": True,
                    "references/": True,
                    "assets/": True
                },
                required_files=["SKILL.md", "scripts/"],
                optional_files=["references/", "assets/"],
                config_template={
                    "name": "",
                    "description": "",
                    "version": "1.0.0",
                    "integrations": [],
                    "webhooks": []
                }
            )
        }
        
        self.ui_framework_templates = {
            UIFramework.REACT: {
                "extension": ".tsx",
                "style_extension": ".module.css",
                "import_pattern": "import React from 'react';",
                "component_pattern": "export const {name}: React.FC<{name}Props> = (props) => {{ ... }}"
            },
            UIFramework.VUE: {
                "extension": ".vue",
                "style_extension": ".css",
                "import_pattern": "",
                "component_pattern": "<template>...</template><script setup lang=\"ts\">...</script>"
            },
            UIFramework.SVELTE: {
                "extension": ".svelte",
                "style_extension": ".css",
                "import_pattern": "",
                "component_pattern": "<script>...</script><template>...</template><style>...</style>"
            },
            UIFramework.NEXT_JS: {
                "extension": ".tsx",
                "style_extension": ".module.css",
                "import_pattern": "import React from 'react';\nimport Head from 'next/head';",
                "component_pattern": "export default function {name}() {{ ... }}"
            },
            UIFramework.ANGULAR: {
                "extension": ".component.ts",
                "style_extension": ".component.css",
                "import_pattern": "import { Component } from '@angular/core';",
                "component_pattern": "@Component({{ ... }}) export class {name}Component {{ ... }}"
            }
        }
        
        self.mcp_templates = {
            MCPLanguage.PYTHON: {
                "file_extension": ".py",
                "package_manager": "pip",
                "dependencies": ["mcp"],
                "server_template": "fastmcp_server.py.j2"
            },
            MCPLanguage.NODE_TYPESCRIPT: {
                "file_extension": ".ts",
                "package_manager": "npm",
                "dependencies": ["@modelcontextprotocol/sdk"],
                "server_template": "mcp_server.ts.j2"
            }
        }
    
    def create_skill(self, name: str, template_type: SkillType = SkillType.BASIC,
                     output_dir: str = None, description: str = "",
                     validate: bool = True) -> IntegrationResult:
        """
        创建新技能
        
        Args:
            name: 技能名称
            template_type: 模板类型
            output_dir: 输出目录
            description: 技能描述
            validate: 是否验证
            
        Returns:
            IntegrationResult
        """
        start_time = datetime.now()
        logger.info(f"Creating skill: {name} with template: {template_type.value}")
        
        try:
            template = self.skill_templates.get(template_type)
            if not template:
                return IntegrationResult(
                    status=IntegrationStatus.FAILED,
                    message=f"未找到模板类型: {template_type.value}"
                )
            
            skill_output_dir = Path(output_dir) if output_dir else self.output_dir / "skills" / name
            skill_output_dir.mkdir(parents=True, exist_ok=True)
            
            skill_md_content = self._generate_skill_md(name, description, template)
            skill_md_path = skill_output_dir / "SKILL.md"
            skill_md_path.write_text(skill_md_content, encoding='utf-8')
            
            for dir_name in template.structure:
                if template.structure[dir_name]:
                    dir_path = skill_output_dir / dir_name.rstrip('/')
                    dir_path.mkdir(parents=True, exist_ok=True)
                    if dir_name == "scripts/":
                        (dir_path / "__init__.py").write_text("", encoding='utf-8')
            
            config = template.config_template.copy()
            config["name"] = name
            config["description"] = description or f"{name} 技能"
            config_path = skill_output_dir / "skill_config.json"
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
            
            output_files = [str(skill_md_path), str(config_path)]
            
            validation_result = None
            if validate:
                validation_result = self._validate_skill(skill_output_dir)
                if not validation_result["valid"]:
                    return IntegrationResult(
                        status=IntegrationStatus.FAILED,
                        message="技能验证失败",
                        errors=validation_result["errors"],
                        output_files=output_files
                    )
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return IntegrationResult(
                status=IntegrationStatus.SUCCESS,
                message=f"技能 '{name}' 创建成功",
                data={
                    "skill_path": str(skill_output_dir),
                    "template": template_type.value,
                    "validation": validation_result
                },
                output_files=output_files,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.error(f"Failed to create skill: {e}")
            return IntegrationResult(
                status=IntegrationStatus.FAILED,
                message=f"创建技能失败: {str(e)}",
                errors=[str(e)]
            )
    
    def _generate_skill_md(self, name: str, description: str, template: SkillTemplate) -> str:
        """生成 SKILL.md 内容"""
        return f"""# {name}

{description or f'{name} 技能'}

## 概述

本技能基于 {template.name} 模板创建。

## 功能

- 功能 1: 待描述
- 功能 2: 待描述

## 使用方法

```
# 使用示例
```

## 配置

| 参数 | 类型 | 描述 | 默认值 |
|------|------|------|--------|
| param1 | string | 参数描述 | - |

## 注意事项

- 注意事项 1
- 注意事项 2

## 版本历史

- v1.0.0 ({datetime.now().strftime('%Y-%m-%d')}): 初始版本
"""
    
    def _validate_skill(self, skill_path: Path) -> Dict[str, Any]:
        """验证技能配置"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            result["valid"] = False
            result["errors"].append("缺少 SKILL.md 文件")
        else:
            content = skill_md.read_text(encoding='utf-8')
            if len(content) < 50:
                result["warnings"].append("SKILL.md 内容过短，建议添加更详细的描述")
            if "# " not in content:
                result["warnings"].append("SKILL.md 缺少标题")
        
        config_file = skill_path / "skill_config.json"
        if config_file.exists():
            try:
                config = json.loads(config_file.read_text(encoding='utf-8'))
                if "name" not in config:
                    result["warnings"].append("配置文件缺少 name 字段")
                if "version" not in config:
                    result["warnings"].append("配置文件缺少 version 字段")
            except json.JSONDecodeError:
                result["valid"] = False
                result["errors"].append("skill_config.json 格式错误")
        
        return result
    
    def design_ui(self, name: str, component_type: str, framework: UIFramework,
                  output_dir: str = None, props: Dict[str, Any] = None,
                  styles: Dict[str, str] = None, responsive: bool = True,
                  accessibility: bool = True) -> IntegrationResult:
        """
        设计 UI 组件
        
        Args:
            name: 组件名称
            component_type: 组件类型 (page, component, layout)
            framework: UI 框架
            output_dir: 输出目录
            props: 组件属性
            styles: 样式配置
            responsive: 是否响应式
            accessibility: 是否包含可访问性支持
            
        Returns:
            IntegrationResult
        """
        start_time = datetime.now()
        logger.info(f"Designing UI: {name} for {framework.value}")
        
        try:
            framework_config = self.ui_framework_templates.get(framework)
            if not framework_config:
                return IntegrationResult(
                    status=IntegrationStatus.FAILED,
                    message=f"不支持的 UI 框架: {framework.value}"
                )
            
            ui_output_dir = Path(output_dir) if output_dir else self.output_dir / "ui" / name
            ui_output_dir.mkdir(parents=True, exist_ok=True)
            
            component_code = self._generate_component_code(
                name, component_type, framework, framework_config, 
                props or {}, styles or {}, responsive, accessibility
            )
            
            extension = framework_config["extension"]
            component_file = ui_output_dir / f"{name}{extension}"
            component_file.write_text(component_code, encoding='utf-8')
            
            style_code = self._generate_component_styles(name, styles or {}, framework, responsive)
            style_file = ui_output_dir / f"{name}{framework_config['style_extension']}"
            style_file.write_text(style_code, encoding='utf-8')
            
            spec_file = ui_output_dir / f"{name}.spec.json"
            spec = UIComponentSpec(
                name=name,
                component_type=component_type,
                framework=framework,
                props=props or {},
                styles=styles or {},
                accessibility={"enabled": accessibility},
                responsive=responsive
            )
            spec_file.write_text(json.dumps(asdict(spec), ensure_ascii=False, indent=2), encoding='utf-8')
            
            output_files = [str(component_file), str(style_file), str(spec_file)]
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return IntegrationResult(
                status=IntegrationStatus.SUCCESS,
                message=f"UI 组件 '{name}' 设计成功",
                data={
                    "component_path": str(ui_output_dir),
                    "framework": framework.value,
                    "component_type": component_type
                },
                output_files=output_files,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.error(f"Failed to design UI: {e}")
            return IntegrationResult(
                status=IntegrationStatus.FAILED,
                message=f"UI 设计失败: {str(e)}",
                errors=[str(e)]
            )
    
    def _generate_component_code(self, name: str, component_type: str, 
                                  framework: UIFramework, framework_config: Dict,
                                  props: Dict, styles: Dict, 
                                  responsive: bool, accessibility: bool) -> str:
        """生成组件代码"""
        props_lines = [f"  {k}: {v};" for k, v in props.items()] if props else ["  // Add props here"]
        props_str = "\n".join(props_lines)
        
        if framework in [UIFramework.REACT, UIFramework.NEXT_JS]:
            accessibility_props = ""
            if accessibility:
                accessibility_props = "\n  // Accessibility\n  role?: string;\n  aria-label?: string;\n  aria-describedby?: string;"
            
            responsive_classes = ""
            if responsive:
                responsive_classes = " sm:px-6 md:px-8 lg:px-10"
            
            if props:
                props_param = ", ".join(props.keys()) + ", ...props"
            else:
                props_param = "...props"
            
            code = "import React from 'react';\n"
            code += framework_config['import_pattern'] + "\n\n"
            code += f"interface {name}Props {{\n"
            code += props_str + accessibility_props + "\n"
            code += "}\n\n"
            code += f"export const {name}: React.FC<{name}Props> = ({{\n"
            code += f"  {props_param}\n"
            code += "}) => {\n"
            code += "  return (\n"
            code += "    <div \n"
            code += f"      className=\"{name.lower()}{responsive_classes}\"\n"
            code += "      {...props}\n"
            code += "    >\n"
            code += f"      /* {name} content */\n"
            code += f"      <h1>{name} Component</h1>\n"
            code += "    </div>\n"
            code += "  );\n"
            code += "};\n\n"
            code += f"export default {name};\n"
            return code
        
        elif framework == UIFramework.VUE:
            props_def = "".join([f"{k}?: {v}; " for k, v in props.items()]) if props else "// Add props here"
            
            code = "<template>\n"
            code += f"  <div class=\"{name.lower()}\" v-bind=\"$attrs\">\n"
            code += f"    <!-- {name} content -->\n"
            code += f"    <h1>{name} Component</h1>\n"
            code += "    <slot></slot>\n"
            code += "  </div>\n"
            code += "</template>\n\n"
            code += "<script setup lang=\"ts\">\n"
            code += "interface Props {\n"
            code += f"  {props_def}\n"
            code += "}\n\n"
            code += "const props = defineProps<Props>();\n"
            code += "</script>\n\n"
            code += "<style scoped>\n"
            code += f".{name.lower()} {{\n"
            code += "  /* Component styles */\n"
            code += "}\n"
            code += "</style>\n"
            return code
        
        elif framework == UIFramework.SVELTE:
            props_def = "".join([f"{k}?: {v}; " for k, v in props.items()]) if props else "// Add props here"
            
            code = "<script lang=\"ts\">\n"
            code += "  interface Props {\n"
            code += f"    {props_def}\n"
            code += "  }\n"
            code += "  \n"
            code += "  export let {...rest}: Props = {};\n"
            code += "</script>\n\n"
            code += f"<div class=\"{name.lower()}\" "
            code = code + "{...rest}>\n"
            code += f"  <!-- {name} content -->\n"
            code += f"  <h1>{name} Component</h1>\n"
            code += "  <slot />\n"
            code += "</div>\n\n"
            code += "<style>\n"
            code += f".{name.lower()} {{\n"
            code += "  /* Component styles */\n"
            code += "}\n"
            code += "</style>\n"
            return code
        
        elif framework == UIFramework.ANGULAR:
            inputs_def = "".join([f"@Input() {k}: {v}; " for k, v in props.items()]) if props else "// Add inputs here"
            
            code = "import { Component, Input } from '@angular/core';\n\n"
            code += "@Component({\n"
            code += f"  selector: 'app-{name.lower()}',\n"
            code += f"  templateUrl: './{name.lower()}.component.html',\n"
            code += f"  styleUrls: ['./{name.lower()}.component.css']\n"
            code += "})\n"
            code += f"export class {name}Component {{\n"
            code += f"  {inputs_def}\n"
            code += "}\n"
            return code
        
        return f"<!-- Unsupported framework: {framework.value} -->"
    
    def _generate_component_styles(self, name: str, styles: Dict, 
                                    framework: UIFramework, responsive: bool) -> str:
        """生成组件样式"""
        base_styles = f".{name.lower()} {{\n"
        base_styles += "  display: block;\n"
        base_styles += "  padding: 1rem;\n"
        
        for key, value in styles.items():
            base_styles += f"  {key}: {value};\n"
        
        base_styles += "}\n"
        
        if responsive:
            base_styles += "\n/* Responsive styles */\n"
            base_styles += "@media (max-width: 768px) {\n"
            base_styles += f"  .{name.lower()} {{\n"
            base_styles += "    padding: 0.5rem;\n"
            base_styles += "  }\n"
            base_styles += "}\n\n"
            base_styles += "@media (max-width: 480px) {\n"
            base_styles += f"  .{name.lower()} {{\n"
            base_styles += "    padding: 0.25rem;\n"
            base_styles += "  }\n"
            base_styles += "}\n"
        
        return base_styles
    
    def build_mcp_server(self, name: str, language: MCPLanguage,
                         transport: MCPTransport = MCPTransport.STDIO,
                         output_dir: str = None, tools: List[Dict] = None,
                         resources: List[Dict] = None, prompts: List[Dict] = None) -> IntegrationResult:
        """
        构建 MCP 服务
        
        Args:
            name: 服务名称
            language: 编程语言
            transport: 传输类型
            output_dir: 输出目录
            tools: 工具列表
            resources: 资源列表
            prompts: 提示列表
            
        Returns:
            IntegrationResult
        """
        start_time = datetime.now()
        logger.info(f"Building MCP server: {name} with {language.value}")
        
        try:
            language_config = self.mcp_templates.get(language)
            if not language_config:
                return IntegrationResult(
                    status=IntegrationStatus.FAILED,
                    message=f"不支持的语言: {language.value}"
                )
            
            mcp_output_dir = Path(output_dir) if output_dir else self.output_dir / "mcp" / name
            mcp_output_dir.mkdir(parents=True, exist_ok=True)
            
            server_config = MCPServerConfig(
                name=name,
                language=language,
                transport=transport,
                tools=tools or [],
                resources=resources or [],
                prompts=prompts or [],
                dependencies=language_config["dependencies"]
            )
            
            if language == MCPLanguage.PYTHON:
                server_code = self._generate_python_mcp_server(server_config)
                server_file = mcp_output_dir / f"{name}_server.py"
            else:
                server_code = self._generate_typescript_mcp_server(server_config)
                server_file = mcp_output_dir / f"{name}_server.ts"
            
            server_file.write_text(server_code, encoding='utf-8')
            
            config_file = mcp_output_dir / "mcp_config.json"
            config_file.write_text(json.dumps(asdict(server_config), ensure_ascii=False, indent=2), encoding='utf-8')
            
            if language == MCPLanguage.PYTHON:
                requirements = mcp_output_dir / "requirements.txt"
                requirements.write_text("\n".join(language_config["dependencies"]) + "\n", encoding='utf-8')
            else:
                package_json = mcp_output_dir / "package.json"
                package_json.write_text(json.dumps({
                    "name": name,
                    "version": "1.0.0",
                    "type": "module",
                    "dependencies": {
                        "@modelcontextprotocol/sdk": "latest"
                    }
                }, indent=2), encoding='utf-8')
            
            output_files = [str(server_file), str(config_file)]
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return IntegrationResult(
                status=IntegrationStatus.SUCCESS,
                message=f"MCP 服务 '{name}' 构建成功",
                data={
                    "server_path": str(mcp_output_dir),
                    "language": language.value,
                    "transport": transport.value
                },
                output_files=output_files,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.error(f"Failed to build MCP server: {e}")
            return IntegrationResult(
                status=IntegrationStatus.FAILED,
                message=f"MCP 服务构建失败: {str(e)}",
                errors=[str(e)]
            )
    
    def _generate_python_mcp_server(self, config: MCPServerConfig) -> str:
        """生成 Python MCP 服务代码"""
        tools_code = ""
        for tool in config.tools:
            tool_name = tool.get('name', 'tool_name')
            tool_params = tool.get('params', '')
            tool_desc = tool.get('description', 'Tool description')
            tools_code += f"""
@mcp.tool()
def {tool_name}({tool_params}):
    \"\"\"
    {tool_desc}
    \"\"\"
    # Tool implementation
    return {{"result": "success"}}
"""
        
        resources_code = ""
        for resource in config.resources:
            res_uri = resource.get('uri', 'resource://example')
            res_name = resource.get('name', 'resource_name')
            res_desc = resource.get('description', 'Resource description')
            resources_code += f"""
@mcp.resource("{res_uri}")
def {res_name}():
    \"\"\"
    {res_desc}
    \"\"\"
    return {{"content": "resource content"}}
"""
        
        prompts_code = ""
        for prompt in config.prompts:
            prompt_name = prompt.get('name', 'prompt_name')
            prompt_desc = prompt.get('description', 'Prompt description')
            prompt_template = prompt.get('template', 'Prompt template')
            prompts_code += f"""
@mcp.prompt()
def {prompt_name}():
    \"\"\"
    {prompt_desc}
    \"\"\"
    return \"{prompt_template}\"
"""
        
        code = f'''#!/usr/bin/env python3
"""
{config.name} MCP Server

Generated by External Skill Integrator
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("{config.name}")

{tools_code}

{resources_code}

{prompts_code}

if __name__ == "__main__":
    mcp.run()
'''
        return code
    
    def _generate_typescript_mcp_server(self, config: MCPServerConfig) -> str:
        """生成 TypeScript MCP 服务代码"""
        tools_code = ""
        for tool in config.tools:
            tool_name = tool.get('name', 'tool_name')
            tool_desc = tool.get('description', 'Tool description')
            tools_code += f'''
server.setRequestHandler(ListToolsRequestSchema, async () => ({{
  tools: [
    {{
      name: "{tool_name}",
      description: "{tool_desc}",
      inputSchema: {{
        type: "object",
        properties: {{
          // Add properties here
        }}
      }}
    }}
  ]
}}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {{
  if (request.params.name === "{tool_name}") {{
    // Tool implementation
    return {{
      content: [{{ type: "text", text: "Tool result" }}]
    }};
  }}
}});
'''
        
        code = f'''#!/usr/bin/env node
/**
 * {config.name} MCP Server
 * 
 * Generated by External Skill Integrator
 */

import {{ Server }} from "@modelcontextprotocol/sdk/server/index.js";
import {{ StdioServerTransport }} from "@modelcontextprotocol/sdk/server/stdio.js";
import {{
  ListToolsRequestSchema,
  CallToolRequestSchema,
}} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  {{
    name: "{config.name}",
    version: "1.0.0",
  }},
  {{
    capabilities: {{
      tools: {{}},
    }},
  }}
);

{tools_code}

async function main() {{
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("{config.name} MCP server running on stdio");
}}

main().catch(console.error);
'''
        return code
    
    def get_status(self, component: str = "all") -> Dict[str, Any]:
        """获取集成状态"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        if component in ["all", "skill-creator"]:
            status["components"]["skill-creator"] = {
                "available": self.skill_creator_path.exists(),
                "path": str(self.skill_creator_path),
                "scripts": [str(p) for p in (self.skill_creator_path / "scripts").glob("*.py")] if (self.skill_creator_path / "scripts").exists() else []
            }
        
        if component in ["all", "ui-ux-pro-max"]:
            status["components"]["ui-ux-pro-max"] = {
                "available": self.ui_ux_path.exists(),
                "path": str(self.ui_ux_path)
            }
        
        if component in ["all", "mcp-builder"]:
            status["components"]["mcp-builder"] = {
                "available": self.mcp_builder_path.exists(),
                "path": str(self.mcp_builder_path),
                "scripts": [str(p) for p in (self.mcp_builder_path / "scripts").glob("*.py")] if (self.mcp_builder_path / "scripts").exists() else []
            }
        
        return status
    
    def list_templates(self, template_type: str = "all") -> Dict[str, Any]:
        """列出可用模板"""
        templates = {}
        
        if template_type in ["all", "skill"]:
            templates["skill"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "type": t.skill_type.value,
                    "required_files": t.required_files
                }
                for t in self.skill_templates.values()
            ]
        
        if template_type in ["all", "ui"]:
            templates["ui"] = [
                {
                    "name": f.value,
                    "extension": self.ui_framework_templates[f]["extension"]
                }
                for f in UIFramework
            ]
        
        if template_type in ["all", "mcp"]:
            templates["mcp"] = {
                "languages": [l.value for l in MCPLanguage],
                "transports": [t.value for t in MCPTransport]
            }
        
        return templates


def main():
    parser = argparse.ArgumentParser(
        description="External Skill Integrator - 外部技能集成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 创建技能
  python external_skill_integrator.py skill create --name=my-skill --template=basic
  
  # 设计 UI 组件
  python external_skill_integrator.py ui design --name=Button --type=component --framework=react
  
  # 构建 MCP 服务
  python external_skill_integrator.py mcp build --name=my-server --language=python
  
  # 查看状态
  python external_skill_integrator.py status --all
  
  # 列出模板
  python external_skill_integrator.py templates --type=skill
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    skill_parser = subparsers.add_parser("skill", help="技能创建和管理")
    skill_parser.add_argument("action", choices=["create", "validate", "package"], help="操作类型")
    skill_parser.add_argument("--name", required=True, help="技能名称")
    skill_parser.add_argument("--template", choices=[t.value for t in SkillType], default="basic", help="模板类型")
    skill_parser.add_argument("--output", help="输出目录")
    skill_parser.add_argument("--description", default="", help="技能描述")
    skill_parser.add_argument("--no-validate", action="store_true", help="跳过验证")
    
    ui_parser = subparsers.add_parser("ui", help="UI/UX 设计和生成")
    ui_parser.add_argument("action", choices=["design", "validate", "generate"], help="操作类型")
    ui_parser.add_argument("--name", required=True, help="组件名称")
    ui_parser.add_argument("--type", choices=["page", "component", "layout"], default="component", help="组件类型")
    ui_parser.add_argument("--framework", choices=[f.value for f in UIFramework], default="react", help="UI 框架")
    ui_parser.add_argument("--output", help="输出目录")
    ui_parser.add_argument("--props", help="组件属性 (JSON 格式)")
    ui_parser.add_argument("--styles", help="样式配置 (JSON 格式)")
    ui_parser.add_argument("--no-responsive", action="store_true", help="禁用响应式")
    ui_parser.add_argument("--no-accessibility", action="store_true", help="禁用可访问性")
    
    mcp_parser = subparsers.add_parser("mcp", help="MCP 服务构建和管理")
    mcp_parser.add_argument("action", choices=["build", "validate", "run"], help="操作类型")
    mcp_parser.add_argument("--name", required=True, help="服务名称")
    mcp_parser.add_argument("--language", choices=[l.value for l in MCPLanguage], default="python", help="编程语言")
    mcp_parser.add_argument("--transport", choices=[t.value for t in MCPTransport], default="stdio", help="传输类型")
    mcp_parser.add_argument("--output", help="输出目录")
    mcp_parser.add_argument("--tools", help="工具列表 (JSON 格式)")
    mcp_parser.add_argument("--resources", help="资源列表 (JSON 格式)")
    mcp_parser.add_argument("--prompts", help="提示列表 (JSON 格式)")
    
    status_parser = subparsers.add_parser("status", help="查看集成状态")
    status_parser.add_argument("--component", choices=["all", "skill-creator", "ui-ux-pro-max", "mcp-builder"], default="all", help="组件")
    
    templates_parser = subparsers.add_parser("templates", help="列出可用模板")
    templates_parser.add_argument("--type", choices=["all", "skill", "ui", "mcp"], default="all", help="模板类型")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    integrator = ExternalSkillIntegrator()
    
    if args.command == "skill":
        if args.action == "create":
            result = integrator.create_skill(
                name=args.name,
                template_type=SkillType(args.template),
                output_dir=args.output,
                description=args.description,
                validate=not args.no_validate
            )
            print(result.to_json())
        
        elif args.action == "validate":
            skill_path = Path(args.output) if args.output else integrator.output_dir / "skills" / args.name
            validation = integrator._validate_skill(skill_path)
            print(json.dumps(validation, ensure_ascii=False, indent=2))
    
    elif args.command == "ui":
        if args.action == "design":
            props = json.loads(args.props) if args.props else {}
            styles = json.loads(args.styles) if args.styles else {}
            
            result = integrator.design_ui(
                name=args.name,
                component_type=args.type,
                framework=UIFramework(args.framework),
                output_dir=args.output,
                props=props,
                styles=styles,
                responsive=not args.no_responsive,
                accessibility=not args.no_accessibility
            )
            print(result.to_json())
    
    elif args.command == "mcp":
        if args.action == "build":
            tools = json.loads(args.tools) if args.tools else []
            resources = json.loads(args.resources) if args.resources else []
            prompts = json.loads(args.prompts) if args.prompts else []
            
            result = integrator.build_mcp_server(
                name=args.name,
                language=MCPLanguage(args.language),
                transport=MCPTransport(args.transport),
                output_dir=args.output,
                tools=tools,
                resources=resources,
                prompts=prompts
            )
            print(result.to_json())
    
    elif args.command == "status":
        status = integrator.get_status(args.component)
        print(json.dumps(status, ensure_ascii=False, indent=2))
    
    elif args.command == "templates":
        templates = integrator.list_templates(args.type)
        print(json.dumps(templates, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
