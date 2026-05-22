#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
需求结构化解析器
支持自然语言、Markdown、用户故事格式的需求解析
"""

import re
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from datetime import datetime
import hashlib


class RequirementType(Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    BUSINESS = "business"
    CONSTRAINT = "constraint"
    INTERFACE = "interface"


class RequirementFormat(Enum):
    NATURAL_LANGUAGE = "natural_language"
    MARKDOWN = "markdown"
    USER_STORY = "user_story"
    USE_CASE = "use_case"
    GHERKIN = "gherkin"


@dataclass
class AcceptanceCriteria:
    scenario: str
    given: str
    when: str
    then: str
    
    def to_dict(self) -> Dict[str, str]:
        return asdict(self)
    
    def to_gherkin(self) -> str:
        return f"""Scenario: {self.scenario}
    Given {self.given}
    When {self.when}
    Then {self.then}"""


@dataclass
class UserStory:
    id: str
    title: str
    role: str
    action: str
    benefit: str
    acceptance_criteria: List[AcceptanceCriteria] = field(default_factory=list)
    priority: str = "medium"
    story_points: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "role": self.role,
            "action": self.action,
            "benefit": self.benefit,
            "acceptance_criteria": [ac.to_dict() for ac in self.acceptance_criteria],
            "priority": self.priority,
            "story_points": self.story_points
        }
    
    def to_standard_format(self) -> str:
        return f"作为 {self.role}，我希望 {self.action}，以便 {self.benefit}"


@dataclass
class FunctionalPoint:
    id: str
    name: str
    description: str
    priority: str = "medium"
    status: str = "pending"
    related_requirements: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DataField:
    name: str
    type: str
    required: bool = False
    primary_key: bool = False
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StateTransition:
    from_state: str
    to_state: str
    action: str
    condition: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DataModel:
    name: str
    type: str = "Entity"
    fields: List[DataField] = field(default_factory=list)
    state_transitions: List[StateTransition] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "fields": [f.to_dict() for f in self.fields],
            "state_transitions": [st.to_dict() for st in self.state_transitions]
        }


@dataclass
class ParsedRequirement:
    id: str
    title: str
    description: str
    requirement_type: RequirementType
    source_format: RequirementFormat
    user_stories: List[UserStory] = field(default_factory=list)
    functional_points: List[FunctionalPoint] = field(default_factory=list)
    data_models: List[DataModel] = field(default_factory=list)
    acceptance_criteria: List[AcceptanceCriteria] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "requirement_type": self.requirement_type.value,
            "source_format": self.source_format.value,
            "user_stories": [us.to_dict() for us in self.user_stories],
            "functional_points": [fp.to_dict() for fp in self.functional_points],
            "data_models": [dm.to_dict() for dm in self.data_models],
            "acceptance_criteria": [ac.to_dict() for ac in self.acceptance_criteria],
            "metadata": self.metadata,
            "created_at": self.created_at
        }


class RequirementParser:
    USER_STORY_PATTERNS = [
        re.compile(r'作为\s*(.+?)\s*，?\s*我希望\s*(.+?)\s*，?\s*以便\s*(.+?)(?:\n|$)', re.DOTALL),
        re.compile(r'As\s+an?\s+(.+?)\s*,?\s*I\s+want\s+to\s+(.+?)\s*,?\s*so\s+that\s+(.+?)(?:\n|$)', re.IGNORECASE | re.DOTALL),
        re.compile(r'作为\s*(.+?)\s*[，,]\s*我想要\s*(.+?)\s*[，,]\s*目的是\s*(.+?)(?:\n|$)', re.DOTALL),
    ]
    
    GHERKIN_PATTERN = re.compile(
        r'Scenario:\s*(.+?)\n'
        r'\s*Given\s+(.+?)\n'
        r'\s*When\s+(.+?)\n'
        r'\s*Then\s+(.+?)(?:\n|$)',
        re.DOTALL | re.IGNORECASE
    )
    
    MARKDOWN_HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    MARKDOWN_LIST_PATTERN = re.compile(r'^[\*\-\+]\s+(.+)$', re.MULTILINE)
    MARKDOWN_CODE_BLOCK = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
    
    PRIORITY_KEYWORDS = {
        "high": ["必须", "关键", "核心", "紧急", "高优先级", "critical", "must", "high", "urgent"],
        "medium": ["应该", "重要", "中优先级", "should", "medium", "important"],
        "low": ["可以", "可选", "低优先级", "nice to have", "low", "optional"]
    }
    
    TYPE_KEYWORDS = {
        RequirementType.FUNCTIONAL: ["功能", "操作", "流程", "functional", "feature", "operation"],
        RequirementType.NON_FUNCTIONAL: ["性能", "安全", "可用性", "可靠性", "non-functional", "performance", "security"],
        RequirementType.BUSINESS: ["业务", "规则", "计算", "business", "rule", "calculation"],
        RequirementType.CONSTRAINT: ["约束", "限制", "constraint", "limitation"],
        RequirementType.INTERFACE: ["接口", "API", "界面", "interface", "UI"]
    }
    
    def __init__(self):
        self.requirement_counter = 0
        self.story_counter = 0
        self.feature_counter = 0
    
    def _generate_id(self, prefix: str = "REQ") -> str:
        self.requirement_counter += 1
        return f"{prefix}-{datetime.now().strftime('%Y%m%d')}-{self.requirement_counter:04d}"
    
    def _generate_story_id(self) -> str:
        self.story_counter += 1
        return f"US-{self.story_counter:03d}"
    
    def _generate_feature_id(self) -> str:
        self.feature_counter += 1
        return f"FP-{self.feature_counter:03d}"
    
    def detect_format(self, content: str) -> RequirementFormat:
        if self.GHERKIN_PATTERN.search(content):
            return RequirementFormat.GHERKIN
        
        for pattern in self.USER_STORY_PATTERNS:
            if pattern.search(content):
                return RequirementFormat.USER_STORY
        
        if self.MARKDOWN_HEADER_PATTERN.search(content):
            return RequirementFormat.MARKDOWN
        
        return RequirementFormat.NATURAL_LANGUAGE
    
    def _extract_priority(self, text: str) -> str:
        text_lower = text.lower()
        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return priority
        return "medium"
    
    def _detect_requirement_type(self, text: str) -> RequirementType:
        text_lower = text.lower()
        scores = {rt: 0 for rt in RequirementType}
        
        for rt, keywords in self.TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    scores[rt] += 1
        
        max_score = max(scores.values())
        if max_score == 0:
            return RequirementType.FUNCTIONAL
        
        for rt, score in scores.items():
            if score == max_score:
                return rt
        
        return RequirementType.FUNCTIONAL
    
    def parse_user_story(self, content: str) -> List[UserStory]:
        stories = []
        
        for pattern in self.USER_STORY_PATTERNS:
            matches = pattern.findall(content)
            for match in matches:
                if len(match) == 3:
                    role, action, benefit = [m.strip() for m in match]
                    story = UserStory(
                        id=self._generate_story_id(),
                        title=f"{role} - {action}",
                        role=role,
                        action=action,
                        benefit=benefit,
                        priority=self._extract_priority(content)
                    )
                    stories.append(story)
        
        gherkin_matches = self.GHERKIN_PATTERN.findall(content)
        for match in gherkin_matches:
            if len(match) == 4:
                scenario, given, when, then = [m.strip() for m in match]
                ac = AcceptanceCriteria(
                    scenario=scenario,
                    given=given,
                    when=when,
                    then=then
                )
                if stories:
                    stories[-1].acceptance_criteria.append(ac)
                else:
                    story = UserStory(
                        id=self._generate_story_id(),
                        title=scenario,
                        role="系统用户",
                        action=when,
                        benefit=then,
                        acceptance_criteria=[ac]
                    )
                    stories.append(story)
        
        return stories
    
    def parse_markdown(self, content: str) -> Tuple[str, List[FunctionalPoint], List[DataModel]]:
        title = ""
        functional_points = []
        data_models = []
        
        headers = self.MARKDOWN_HEADER_PATTERN.findall(content)
        if headers:
            first_header = headers[0]
            title = first_header[1].strip()
        
        sections = re.split(r'^#{1,6}\s+.+$', content, flags=re.MULTILINE)
        
        for section in sections[1:]:
            lines = section.strip().split('\n')
            if not lines:
                continue
            
            list_items = self.MARKDOWN_LIST_PATTERN.findall(section)
            
            if list_items:
                fp = FunctionalPoint(
                    id=self._generate_feature_id(),
                    name=lines[0] if lines else "未命名功能",
                    description='\n'.join(list_items),
                    priority=self._extract_priority(section)
                )
                functional_points.append(fp)
        
        code_blocks = self.MARKDOWN_CODE_BLOCK.findall(content)
        for lang, code in code_blocks:
            if lang.lower() in ['json', 'typescript', 'python']:
                model = self._parse_data_model_from_code(code, lang)
                if model:
                    data_models.append(model)
        
        return title, functional_points, data_models
    
    def _parse_data_model_from_code(self, code: str, lang: str) -> Optional[DataModel]:
        fields = []
        
        if lang.lower() == 'json':
            try:
                data = json.loads(code)
                if isinstance(data, dict):
                    if 'fields' in data:
                        for f in data['fields']:
                            field = DataField(
                                name=f.get('name', ''),
                                type=f.get('type', 'string'),
                                required=f.get('required', False),
                                primary_key=f.get('primaryKey', False),
                                description=f.get('description')
                            )
                            fields.append(field)
                        
                        return DataModel(
                            name=data.get('name', 'Unknown'),
                            type=data.get('type', 'Entity'),
                            fields=fields
                        )
            except json.JSONDecodeError:
                pass
        
        field_pattern = re.compile(r'(\w+)\s*:\s*(\w+)(?:\s*\|\s*null)?')
        matches = field_pattern.findall(code)
        if matches:
            for name, ftype in matches:
                if name not in ['id', 'created_at', 'updated_at']:
                    fields.append(DataField(name=name, type=ftype))
            
            if fields:
                name_match = re.search(r'(?:class|interface|type)\s+(\w+)', code)
                model_name = name_match.group(1) if name_match else "DataModel"
                return DataModel(name=model_name, fields=fields)
        
        return None
    
    def parse_natural_language(self, content: str) -> Tuple[str, List[FunctionalPoint], List[AcceptanceCriteria]]:
        title = ""
        functional_points = []
        acceptance_criteria = []
        
        sentences = re.split(r'[。！？\n]', content)
        if sentences:
            title = sentences[0][:100] if len(sentences[0]) > 100 else sentences[0]
        
        action_patterns = [
            re.compile(r'系统(应当|应该|必须|可以|需要)(.+?)(?:，|。|$)'),
            re.compile(r'用户(可以|能够|需要)(.+?)(?:，|。|$)'),
            re.compile(r'(?:当|如果)(.+?)时[，,]?(.+?)(?:，|。|$)'),
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            for pattern in action_patterns:
                match = pattern.search(sentence)
                if match:
                    fp = FunctionalPoint(
                        id=self._generate_feature_id(),
                        name=sentence[:50],
                        description=sentence,
                        priority=self._extract_priority(sentence)
                    )
                    functional_points.append(fp)
                    break
        
        condition_pattern = re.compile(
            r'(?:如果|当|若)(.+?)(?:时|情况下)[，,]?(?:则|那么)?(.+?)(?:，|。|$)'
        )
        condition_matches = condition_pattern.findall(content)
        for i, (condition, result) in enumerate(condition_matches):
            ac = AcceptanceCriteria(
                scenario=f"场景{i+1}",
                given=condition.strip(),
                when="执行操作",
                then=result.strip()
            )
            acceptance_criteria.append(ac)
        
        return title, functional_points, acceptance_criteria
    
    def parse(self, content: str, requirement_type: Optional[RequirementType] = None) -> ParsedRequirement:
        source_format = self.detect_format(content)
        
        if requirement_type is None:
            requirement_type = self._detect_requirement_type(content)
        
        user_stories = []
        functional_points = []
        data_models = []
        acceptance_criteria = []
        title = ""
        description = content
        
        if source_format == RequirementFormat.USER_STORY:
            user_stories = self.parse_user_story(content)
            if user_stories:
                title = user_stories[0].title
            for story in user_stories:
                acceptance_criteria.extend(story.acceptance_criteria)
        
        elif source_format == RequirementFormat.GHERKIN:
            gherkin_matches = self.GHERKIN_PATTERN.findall(content)
            for match in gherkin_matches:
                if len(match) == 4:
                    scenario, given, when, then = [m.strip() for m in match]
                    ac = AcceptanceCriteria(scenario=scenario, given=given, when=when, then=then)
                    acceptance_criteria.append(ac)
                    
                    story = UserStory(
                        id=self._generate_story_id(),
                        title=scenario,
                        role="系统用户",
                        action=when,
                        benefit=then,
                        acceptance_criteria=[ac]
                    )
                    user_stories.append(story)
            if acceptance_criteria:
                title = acceptance_criteria[0].scenario
        
        elif source_format == RequirementFormat.MARKDOWN:
            title, functional_points, data_models = self.parse_markdown(content)
        
        else:
            title, functional_points, acceptance_criteria = self.parse_natural_language(content)
        
        return ParsedRequirement(
            id=self._generate_id(),
            title=title,
            description=description,
            requirement_type=requirement_type,
            source_format=source_format,
            user_stories=user_stories,
            functional_points=functional_points,
            data_models=data_models,
            acceptance_criteria=acceptance_criteria,
            metadata={
                "content_hash": hashlib.md5(content.encode()).hexdigest(),
                "word_count": len(content.split()),
                "char_count": len(content)
            }
        )
    
    def parse_file(self, file_path: str) -> ParsedRequirement:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse(content)
    
    def to_json(self, requirement: ParsedRequirement) -> str:
        return json.dumps(requirement.to_dict(), ensure_ascii=False, indent=2)
    
    def to_markdown(self, requirement: ParsedRequirement) -> str:
        md_lines = [
            f"# {requirement.title}",
            "",
            f"**需求ID**: {requirement.id}",
            f"**类型**: {requirement.requirement_type.value}",
            f"**格式**: {requirement.source_format.value}",
            f"**创建时间**: {requirement.created_at}",
            "",
            "## 描述",
            "",
            requirement.description,
            ""
        ]
        
        if requirement.user_stories:
            md_lines.extend([
                "## 用户故事",
                ""
            ])
            for story in requirement.user_stories:
                md_lines.extend([
                    f"### {story.id}: {story.title}",
                    "",
                    f"作为 **{story.role}**，我希望 **{story.action}**，以便 **{story.benefit}**",
                    "",
                    f"**优先级**: {story.priority}",
                    ""
                ])
                if story.acceptance_criteria:
                    md_lines.append("**验收标准**:")
                    md_lines.append("")
                    for ac in story.acceptance_criteria:
                        md_lines.extend([
                            "```gherkin",
                            ac.to_gherkin(),
                            "```",
                            ""
                        ])
        
        if requirement.functional_points:
            md_lines.extend([
                "## 功能点",
                ""
            ])
            for fp in requirement.functional_points:
                md_lines.extend([
                    f"- **{fp.id}**: {fp.name}",
                    f"  - 描述: {fp.description}",
                    f"  - 优先级: {fp.priority}",
                    ""
                ])
        
        if requirement.data_models:
            md_lines.extend([
                "## 数据模型",
                ""
            ])
            for model in requirement.data_models:
                md_lines.extend([
                    f"### {model.name} ({model.type})",
                    "",
                    "| 字段名 | 类型 | 必填 | 主键 |",
                    "|--------|------|------|------|"
                ])
                for field in model.fields:
                    required = "✓" if field.required else ""
                    pk = "✓" if field.primary_key else ""
                    md_lines.append(f"| {field.name} | {field.type} | {required} | {pk} |")
                md_lines.append("")
        
        return '\n'.join(md_lines)


def main():
    parser = RequirementParser()
    
    test_cases = [
        {
            "name": "用户故事格式",
            "content": """
作为 注册用户，我希望 能够修改我的个人信息，以便 保持我的资料最新。

Scenario: 用户修改个人信息
    Given 用户已登录系统
    When 用户点击"修改个人信息"并更新信息
    Then 系统保存更新后的信息并显示成功提示
"""
        },
        {
            "name": "Markdown格式",
            "content": """
# 用户认证功能

## 登录功能
- 用户可以使用用户名和密码登录
- 系统应验证用户凭证
- 登录失败时显示错误提示

## 注册功能
- 新用户可以注册账户
- 必须提供有效的邮箱地址
- 密码必须符合安全要求
"""
        },
        {
            "name": "自然语言格式",
            "content": """
系统必须提供用户认证功能。用户可以通过用户名和密码登录系统。
如果用户输入错误的密码超过3次，系统应该锁定账户。
用户可以重置密码，系统会发送重置链接到用户邮箱。
"""
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"测试: {test_case['name']}")
        print('='*60)
        
        result = parser.parse(test_case['content'])
        print(f"\n检测格式: {result.source_format.value}")
        print(f"需求类型: {result.requirement_type.value}")
        print(f"需求ID: {result.id}")
        print(f"标题: {result.title}")
        
        if result.user_stories:
            print(f"\n用户故事数量: {len(result.user_stories)}")
            for story in result.user_stories:
                print(f"  - {story.id}: {story.to_standard_format()}")
        
        if result.functional_points:
            print(f"\n功能点数量: {len(result.functional_points)}")
            for fp in result.functional_points:
                print(f"  - {fp.id}: {fp.name}")
        
        if result.acceptance_criteria:
            print(f"\n验收标准数量: {len(result.acceptance_criteria)}")
            for ac in result.acceptance_criteria:
                print(f"  - {ac.scenario}")


if __name__ == "__main__":
    main()
