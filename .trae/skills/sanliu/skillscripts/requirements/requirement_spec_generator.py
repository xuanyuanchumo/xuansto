#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
需求规格文档生成器
生成标准化的需求规格说明书
"""

import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import os

from .requirement_parser import (
    ParsedRequirement, UserStory, FunctionalPoint, 
    DataModel, AcceptanceCriteria, RequirementType
)
from .business_rule_extractor import BusinessRule, RuleType


class DocumentFormat(Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    PDF = "pdf"


@dataclass
class DocumentSection:
    id: str
    title: str
    content: str
    subsections: List['DocumentSection'] = field(default_factory=list)
    level: int = 1
    
    def to_markdown(self) -> str:
        prefix = "#" * self.level
        lines = [f"{prefix} {self.title}", "", self.content, ""]
        
        for subsection in self.subsections:
            lines.append(subsection.to_markdown())
        
        return '\n'.join(lines)


@dataclass
class RequirementSpecification:
    project_name: str
    version: str
    author: str
    date: str
    requirements: List[ParsedRequirement]
    business_rules: List[BusinessRule]
    glossary: Dict[str, str] = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "version": self.version,
            "author": self.author,
            "date": self.date,
            "requirements": [r.to_dict() for r in self.requirements],
            "business_rules": [r.to_dict() for r in self.business_rules],
            "glossary": self.glossary,
            "assumptions": self.assumptions,
            "constraints": self.constraints
        }


class SpecificationGenerator:
    TEMPLATE_VERSION = "1.0"
    
    def __init__(self, project_name: str, author: str = "系统生成"):
        self.project_name = project_name
        self.author = author
        self.requirements: List[ParsedRequirement] = []
        self.business_rules: List[BusinessRule] = []
        self.glossary: Dict[str, str] = {}
        self.assumptions: List[str] = []
        self.constraints: List[str] = []
    
    def add_requirement(self, requirement: ParsedRequirement):
        self.requirements.append(requirement)
    
    def add_business_rule(self, rule: BusinessRule):
        self.business_rules.append(rule)
    
    def add_glossary_term(self, term: str, definition: str):
        self.glossary[term] = definition
    
    def add_assumption(self, assumption: str):
        self.assumptions.append(assumption)
    
    def add_constraint(self, constraint: str):
        self.constraints.append(constraint)
    
    def _generate_cover_section(self) -> DocumentSection:
        content = f"""
**项目名称**: {self.project_name}

**文档版本**: {self.TEMPLATE_VERSION}

**作者**: {self.author}

**创建日期**: {datetime.now().strftime('%Y年%m月%d日')}

**文档状态**: 初稿

---

## 文档修订历史

| 版本 | 日期 | 作者 | 修改说明 |
|------|------|------|----------|
| 1.0 | {datetime.now().strftime('%Y-%m-%d')} | {self.author} | 初始版本 |
"""
        return DocumentSection(
            id="cover",
            title="封面",
            content=content.strip(),
            level=1
        )
    
    def _generate_toc_section(self) -> DocumentSection:
        toc_items = [
            "1. 引言",
            "   1.1 目的",
            "   1.2 范围",
            "   1.3 术语定义",
            "2. 总体描述",
            "   2.1 产品概述",
            "   2.2 用户特征",
            "   2.3 假设与约束",
            "3. 功能需求",
            "   3.1 用户故事",
            "   3.2 功能点列表",
            "   3.3 验收标准",
            "4. 非功能需求",
            "5. 数据需求",
            "   5.1 数据模型",
            "   5.2 数据字典",
            "6. 业务规则",
            "7. 接口需求",
            "8. 附录"
        ]
        
        content = '\n'.join(toc_items)
        return DocumentSection(
            id="toc",
            title="目录",
            content=content,
            level=1
        )
    
    def _generate_introduction_section(self) -> DocumentSection:
        purpose_content = f"""
本文档是{self.project_name}项目的软件需求规格说明书（SRS），旨在详细描述系统的功能需求、非功能需求、数据需求和业务规则。

本文档的主要读者包括：
- 项目经理
- 系统架构师
- 开发工程师
- 测试工程师
- 产品经理
"""
        
        scope_content = """
本系统旨在提供完整的业务解决方案，包括但不限于以下功能模块：
- 用户管理
- 权限控制
- 业务处理
- 数据分析
"""
        
        glossary_content = ""
        if self.glossary:
            glossary_content = "| 术语 | 定义 |\n|------|------|\n"
            for term, definition in self.glossary.items():
                glossary_content += f"| {term} | {definition} |\n"
        else:
            glossary_content = "暂无术语定义。"
        
        purpose_section = DocumentSection(
            id="purpose",
            title="目的",
            content=purpose_content.strip(),
            level=2
        )
        
        scope_section = DocumentSection(
            id="scope",
            title="范围",
            content=scope_content.strip(),
            level=2
        )
        
        glossary_section = DocumentSection(
            id="glossary",
            title="术语定义",
            content=glossary_content.strip(),
            level=2
        )
        
        return DocumentSection(
            id="introduction",
            title="引言",
            content="",
            level=1,
            subsections=[purpose_section, scope_section, glossary_section]
        )
    
    def _generate_overview_section(self) -> DocumentSection:
        overview_content = f"""
{self.project_name}是一个综合性的业务管理系统，旨在提高业务处理效率，优化用户体验，并提供可靠的数据支持。

**主要目标**：
- 提供直观易用的用户界面
- 确保数据安全和系统稳定性
- 支持高并发访问
- 提供灵活的扩展能力
"""
        
        user_content = """
系统的主要用户群体包括：

| 用户类型 | 描述 | 主要职责 |
|----------|------|----------|
| 系统管理员 | 负责系统维护和配置 | 用户管理、权限分配、系统配置 |
| 普通用户 | 使用系统日常功能 | 数据录入、查询、报表生成 |
| 审核人员 | 负责业务审核 | 审批流程、数据校验 |
"""
        
        assumptions_content = ""
        if self.assumptions:
            assumptions_content = "**假设**：\n"
            for i, assumption in enumerate(self.assumptions, 1):
                assumptions_content += f"{i}. {assumption}\n"
        else:
            assumptions_content = "暂无特殊假设。"
        
        constraints_content = ""
        if self.constraints:
            constraints_content = "\n**约束**：\n"
            for i, constraint in enumerate(self.constraints, 1):
                constraints_content += f"{i}. {constraint}\n"
        else:
            constraints_content = "\n暂无特殊约束。"
        
        overview_section = DocumentSection(
            id="product_overview",
            title="产品概述",
            content=overview_content.strip(),
            level=2
        )
        
        user_section = DocumentSection(
            id="user_characteristics",
            title="用户特征",
            content=user_content.strip(),
            level=2
        )
        
        assumptions_section = DocumentSection(
            id="assumptions_constraints",
            title="假设与约束",
            content=(assumptions_content + constraints_content).strip(),
            level=2
        )
        
        return DocumentSection(
            id="overview",
            title="总体描述",
            content="",
            level=1,
            subsections=[overview_section, user_section, assumptions_section]
        )
    
    def _generate_functional_requirements_section(self) -> DocumentSection:
        user_stories_content = ""
        all_stories: List[UserStory] = []
        
        for req in self.requirements:
            all_stories.extend(req.user_stories)
        
        if all_stories:
            for story in all_stories:
                user_stories_content += f"""
#### {story.id}: {story.title}

**用户故事**：作为 **{story.role}**，我希望 **{story.action}**，以便 **{story.benefit}**。

**优先级**：{story.priority}

"""
                if story.acceptance_criteria:
                    user_stories_content += "**验收标准**：\n\n```gherkin\n"
                    for ac in story.acceptance_criteria:
                        user_stories_content += ac.to_gherkin() + "\n\n"
                    user_stories_content += "```\n\n"
        else:
            user_stories_content = "暂无用户故事。"
        
        functional_points_content = ""
        all_features: List[FunctionalPoint] = []
        
        for req in self.requirements:
            all_features.extend(req.functional_points)
        
        if all_features:
            functional_points_content = "| ID | 功能名称 | 描述 | 优先级 | 状态 |\n"
            functional_points_content += "|-----|----------|------|--------|------|\n"
            for fp in all_features:
                functional_points_content += f"| {fp.id} | {fp.name} | {fp.description[:50]}... | {fp.priority} | {fp.status} |\n"
        else:
            functional_points_content = "暂无功能点。"
        
        acceptance_content = ""
        all_criteria: List[AcceptanceCriteria] = []
        
        for req in self.requirements:
            all_criteria.extend(req.acceptance_criteria)
        
        if all_criteria:
            for i, ac in enumerate(all_criteria, 1):
                acceptance_content += f"""
**场景 {i}**: {ac.scenario}

```gherkin
Given {ac.given}
When {ac.when}
Then {ac.then}
```

"""
        else:
            acceptance_content = "暂无验收标准。"
        
        stories_section = DocumentSection(
            id="user_stories",
            title="用户故事",
            content=user_stories_content.strip(),
            level=2
        )
        
        features_section = DocumentSection(
            id="functional_points",
            title="功能点列表",
            content=functional_points_content.strip(),
            level=2
        )
        
        acceptance_section = DocumentSection(
            id="acceptance_criteria",
            title="验收标准",
            content=acceptance_content.strip(),
            level=2
        )
        
        return DocumentSection(
            id="functional_requirements",
            title="功能需求",
            content="",
            level=1,
            subsections=[stories_section, features_section, acceptance_section]
        )
    
    def _generate_non_functional_requirements_section(self) -> DocumentSection:
        non_functional_reqs = [
            req for req in self.requirements 
            if req.requirement_type == RequirementType.NON_FUNCTIONAL
        ]
        
        content = """
### 性能需求

| 指标 | 要求 |
|------|------|
| 响应时间 | 页面加载时间不超过3秒 |
| 并发用户 | 支持至少1000并发用户 |
| 吞吐量 | 每秒处理至少100个请求 |

### 安全需求

- 用户认证：支持用户名密码认证
- 权限控制：基于角色的访问控制（RBAC）
- 数据加密：敏感数据传输使用HTTPS加密
- 审计日志：记录所有关键操作日志

### 可用性需求

- 系统可用性：99.9%
- 故障恢复时间：不超过30分钟
- 数据备份：每日自动备份

### 兼容性需求

- 浏览器支持：Chrome、Firefox、Safari、Edge最新版本
- 操作系统：Windows 10+、macOS 10.15+、Linux
- 移动端：支持响应式设计
"""
        
        if non_functional_reqs:
            content += "\n### 其他非功能需求\n\n"
            for req in non_functional_reqs:
                content += f"- {req.title}: {req.description}\n"
        
        return DocumentSection(
            id="non_functional_requirements",
            title="非功能需求",
            content=content.strip(),
            level=1
        )
    
    def _generate_data_requirements_section(self) -> DocumentSection:
        all_models: List[DataModel] = []
        
        for req in self.requirements:
            all_models.extend(req.data_models)
        
        models_content = ""
        if all_models:
            for model in all_models:
                models_content += f"""
### {model.name} ({model.type})

| 字段名 | 类型 | 必填 | 主键 | 描述 |
|--------|------|------|------|------|
"""
                for field in model.fields:
                    required = "✓" if field.required else ""
                    pk = "✓" if field.primary_key else ""
                    desc = field.description or ""
                    models_content += f"| {field.name} | {field.type} | {required} | {pk} | {desc} |\n"
                
                if model.state_transitions:
                    models_content += "\n**状态变更图**：\n\n"
                    for trans in model.state_transitions:
                        models_content += f"- {trans.from_state} → [{trans.action}] → {trans.to_state}\n"
                
                models_content += "\n"
        else:
            models_content = "暂无数据模型定义。"
        
        data_dict_content = """
数据字典定义了系统中使用的所有数据元素。

| 数据项 | 类型 | 长度 | 格式 | 说明 |
|--------|------|------|------|------|
| 用户ID | String | 36 | UUID | 用户唯一标识 |
| 用户名 | String | 50 | - | 用户登录名 |
| 创建时间 | DateTime | - | ISO 8601 | 记录创建时间 |
| 更新时间 | DateTime | - | ISO 8601 | 记录更新时间 |
"""
        
        models_section = DocumentSection(
            id="data_models",
            title="数据模型",
            content=models_content.strip(),
            level=2
        )
        
        dict_section = DocumentSection(
            id="data_dictionary",
            title="数据字典",
            content=data_dict_content.strip(),
            level=2
        )
        
        return DocumentSection(
            id="data_requirements",
            title="数据需求",
            content="",
            level=1,
            subsections=[models_section, dict_section]
        )
    
    def _generate_business_rules_section(self) -> DocumentSection:
        content = ""
        
        if self.business_rules:
            rules_by_type: Dict[str, List[BusinessRule]] = {}
            for rule in self.business_rules:
                rt = rule.rule_type.value
                if rt not in rules_by_type:
                    rules_by_type[rt] = []
                rules_by_type[rt].append(rule)
            
            for rule_type, rules in rules_by_type.items():
                content += f"### {rule_type}\n\n"
                
                for rule in rules:
                    content += f"#### {rule.id}: {rule.name}\n\n"
                    content += f"**描述**：{rule.description}\n\n"
                    content += f"**优先级**：{rule.priority.value}\n\n"
                    
                    if rule.conditions:
                        content += "**条件**：\n"
                        for cond in rule.conditions:
                            content += f"- `{cond.to_expression()}`\n"
                        content += "\n"
                    
                    if rule.actions:
                        content += "**动作**：\n"
                        for action in rule.actions:
                            content += f"- {action.action_type}: {action.target}\n"
                        content += "\n"
                    
                    if rule.validation_rules:
                        content += "**验证规则**：\n"
                        for v in rule.validation_rules:
                            content += f"- {v.field}: {v.validation_type}\n"
                        content += "\n"
                    
                    if rule.calculation_rules:
                        content += "**计算规则**：\n"
                        for c in rule.calculation_rules:
                            content += f"- {c.result_field} = {c.formula}\n"
                        content += "\n"
        else:
            content = "暂无业务规则定义。"
        
        return DocumentSection(
            id="business_rules",
            title="业务规则",
            content=content.strip(),
            level=1
        )
    
    def _generate_interface_requirements_section(self) -> DocumentSection:
        interface_reqs = [
            req for req in self.requirements 
            if req.requirement_type == RequirementType.INTERFACE
        ]
        
        content = """
### 用户接口

- Web界面：基于HTML5的响应式Web应用
- 移动端：支持iOS和Android的移动Web访问

### 软件接口

| 接口名称 | 类型 | 协议 | 描述 |
|----------|------|------|------|
| REST API | HTTP | HTTPS | 系统主要API接口 |
| WebSocket | 实时通信 | WSS | 实时消息推送 |

### 硬件接口

- 无特殊硬件接口需求

### 通信接口

- 支持HTTP/HTTPS协议
- 支持WebSocket协议
"""
        
        if interface_reqs:
            content += "\n### 其他接口需求\n\n"
            for req in interface_reqs:
                content += f"- {req.title}: {req.description}\n"
        
        return DocumentSection(
            id="interface_requirements",
            title="接口需求",
            content=content.strip(),
            level=1
        )
    
    def _generate_appendix_section(self) -> DocumentSection:
        content = f"""
### 附录A：需求清单

| 需求ID | 标题 | 类型 | 状态 |
|--------|------|------|------|
"""
        for req in self.requirements:
            content += f"| {req.id} | {req.title} | {req.requirement_type.value} | 活跃 |\n"
        
        content += f"""
### 附录B：参考文档

1. 软件需求规格说明书标准（IEEE 830）
2. 用户故事地图
3. 业务流程图

### 附录C：变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
| {datetime.now().strftime('%Y-%m-%d')} | 1.0 | 初始版本 | {self.author} |
"""
        
        return DocumentSection(
            id="appendix",
            title="附录",
            content=content.strip(),
            level=1
        )
    
    def generate_markdown(self) -> str:
        sections = [
            self._generate_cover_section(),
            self._generate_toc_section(),
            self._generate_introduction_section(),
            self._generate_overview_section(),
            self._generate_functional_requirements_section(),
            self._generate_non_functional_requirements_section(),
            self._generate_data_requirements_section(),
            self._generate_business_rules_section(),
            self._generate_interface_requirements_section(),
            self._generate_appendix_section()
        ]
        
        document_lines = []
        for section in sections:
            document_lines.append(section.to_markdown())
        
        return '\n'.join(document_lines)
    
    def generate_json(self) -> str:
        spec = RequirementSpecification(
            project_name=self.project_name,
            version=self.TEMPLATE_VERSION,
            author=self.author,
            date=datetime.now().isoformat(),
            requirements=self.requirements,
            business_rules=self.business_rules,
            glossary=self.glossary,
            assumptions=self.assumptions,
            constraints=self.constraints
        )
        return json.dumps(spec.to_dict(), ensure_ascii=False, indent=2)
    
    def save_document(self, output_path: str, format: DocumentFormat = DocumentFormat.MARKDOWN):
        if format == DocumentFormat.MARKDOWN:
            content = self.generate_markdown()
            file_path = f"{output_path}.md"
        elif format == DocumentFormat.JSON:
            content = self.generate_json()
            file_path = f"{output_path}.json"
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path


def main():
    from requirement_parser import RequirementParser
    from business_rule_extractor import BusinessRuleExtractor
    
    parser = RequirementParser()
    extractor = BusinessRuleExtractor()
    generator = SpecificationGenerator(
        project_name="用户管理系统",
        author="需求分析团队"
    )
    
    test_requirement = """
作为 注册用户，我希望 能够修改我的个人信息，以便 保持我的资料最新。

Scenario: 用户修改个人信息
    Given 用户已登录系统
    When 用户点击"修改个人信息"并更新信息
    Then 系统保存更新后的信息并显示成功提示

## 密码管理功能
- 用户可以修改密码
- 密码长度必须大于8位
- 新密码不能与最近5次使用的密码相同

如果用户连续登录失败超过3次，则锁定账户24小时。
"""
    
    parsed_req = parser.parse(test_requirement)
    generator.add_requirement(parsed_req)
    
    rules = extractor.extract_all_rules(test_requirement)
    for rule in rules:
        generator.add_business_rule(rule)
    
    generator.add_glossary_term("用户", "使用系统的注册人员")
    generator.add_glossary_term("认证", "验证用户身份的过程")
    
    generator.add_assumption("用户具备基本的计算机操作能力")
    generator.add_assumption("网络环境稳定可靠")
    
    generator.add_constraint("系统需在3秒内响应用户请求")
    generator.add_constraint("支持至少1000并发用户")
    
    md_content = generator.generate_markdown()
    print(md_content)
    
    print("\n" + "="*60)
    print("JSON格式输出（部分）:")
    print("="*60)
    json_content = generator.generate_json()
    print(json_content[:2000] + "...")


if __name__ == "__main__":
    main()
