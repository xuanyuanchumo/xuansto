#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
子技能文档更新器 - Subskill Document Updater

提供子技能文档的检测、更新建议生成、自动更新执行和验证功能。

核心功能:
- 子技能内容检测：扫描所有子技能文档，检测内容变化
- 更新建议生成：分析内容变化，生成更新建议列表
- 自动更新执行：应用更新建议，更新文档内容
- 更新验证：验证更新后的文档格式、链接有效性和内容完整性

使用示例:
    from subskill_doc_updater import SubskillDocUpdater
    
    updater = SubskillDocUpdater(skill_dir='./')
    suggestions = updater.detect_and_suggest()
    
    for suggestion in suggestions:
        print(f"{suggestion.subskill_name}: {suggestion.description}")
    
    results = updater.apply_updates(suggestions)
"""

import hashlib
import json
import logging
import re
import shutil
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class UpdateType(Enum):
    CONTENT = auto()
    METADATA = auto()
    REFERENCE = auto()
    FORMAT = auto()


class Priority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class ValidationStatus(Enum):
    VALID = auto()
    INVALID = auto()
    WARNING = auto()


class ContentType(Enum):
    SECTION = "section"
    COMMAND = "command"
    TEMPLATE = "template"
    LINK = "link"
    METADATA_FIELD = "metadata_field"


@dataclass
class SubskillUpdateSuggestion:
    subskill_name: str
    update_type: UpdateType
    priority: Priority
    description: str
    old_content: Optional[str]
    suggested_content: str
    reason: str
    section_name: Optional[str] = None
    line_number: Optional[int] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subskill_name": self.subskill_name,
            "update_type": self.update_type.name,
            "priority": self.priority.name,
            "description": self.description,
            "old_content": self.old_content,
            "suggested_content": self.suggested_content,
            "reason": self.reason,
            "section_name": self.section_name,
            "line_number": self.line_number,
            "confidence": self.confidence,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubskillUpdateSuggestion':
        return cls(
            subskill_name=data['subskill_name'],
            update_type=UpdateType[data['update_type']],
            priority=Priority[data['priority']],
            description=data['description'],
            old_content=data.get('old_content'),
            suggested_content=data['suggested_content'],
            reason=data['reason'],
            section_name=data.get('section_name'),
            line_number=data.get('line_number'),
            confidence=data.get('confidence', 1.0),
            metadata=data.get('metadata', {})
        )


@dataclass
class SubskillUpdateResult:
    subskill_name: str
    success: bool
    applied_suggestions: List[SubskillUpdateSuggestion]
    skipped_suggestions: List[SubskillUpdateSuggestion]
    validation_errors: List[str]
    backup_path: Optional[Path]
    updated_at: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subskill_name": self.subskill_name,
            "success": self.success,
            "applied_suggestions": [s.to_dict() for s in self.applied_suggestions],
            "skipped_suggestions": [s.to_dict() for s in self.skipped_suggestions],
            "validation_errors": self.validation_errors,
            "backup_path": str(self.backup_path) if self.backup_path else None,
            "updated_at": self.updated_at.isoformat(),
            "duration_seconds": self.duration_seconds
        }


@dataclass
class ValidationResult:
    subskill_name: str
    status: ValidationStatus
    errors: List[str]
    warnings: List[str]
    checks_passed: int
    checks_failed: int
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subskill_name": self.subskill_name,
            "status": self.status.name,
            "errors": self.errors,
            "warnings": self.warnings,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "details": self.details
        }


@dataclass
class ContentChange:
    content_type: ContentType
    location: str
    old_value: Optional[str]
    new_value: Optional[str]
    change_description: str
    detected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_type": self.content_type.value,
            "location": self.location,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "change_description": self.change_description,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class SubskillDocument:
    name: str
    path: Path
    content: str
    metadata: Dict[str, Any]
    sections: Dict[str, str]
    commands: List[str]
    templates: List[str]
    links: List[Tuple[str, str]]
    hash_value: str
    last_modified: float
    parsed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "content_length": len(self.content),
            "metadata": self.metadata,
            "sections": list(self.sections.keys()),
            "commands_count": len(self.commands),
            "templates_count": len(self.templates),
            "links_count": len(self.links),
            "hash_value": self.hash_value,
            "last_modified": self.last_modified,
            "parsed_at": self.parsed_at.isoformat()
        }


class SubskillContentDetector:
    SECTION_PATTERN = re.compile(r'^##\s+(.+)$', re.MULTILINE)
    SUBSECTION_PATTERN = re.compile(r'^###\s+(.+)$', re.MULTILINE)
    COMMAND_PATTERN = re.compile(r'```(?:bash|shell|cmd|powershell)?\s*\n(.*?)```', re.DOTALL)
    TEMPLATE_PATTERN = re.compile(r'(?:调用|引用|参考)\s*[`\'"]?([^`\'"\s]+\.(?:md|yaml|json|txt))[`\'"]?', re.IGNORECASE)
    LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    YAML_FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    CODE_BLOCK_PATTERN = re.compile(r'```(\w*)\s*\n(.*?)```', re.DOTALL)

    REQUIRED_METADATA_FIELDS = ['name', 'description']
    REQUIRED_SECTIONS = []

    def __init__(self, skill_dir: Path):
        self._skill_dir = skill_dir
        self._subskills_dir = skill_dir / "subskills"
        self._cache: Dict[str, Tuple[str, SubskillDocument]] = {}
        self._logger = logging.getLogger('SubskillContentDetector')

    def scan_all_subskills(self, incremental: bool = True) -> Dict[str, SubskillDocument]:
        if not self._subskills_dir.exists():
            self._logger.warning(f"子技能目录不存在: {self._subskills_dir}")
            return {}

        documents: Dict[str, SubskillDocument] = {}

        for md_file in self._subskills_dir.glob("*.md"):
            try:
                doc = self.parse_subskill_document(md_file, incremental)
                if doc:
                    documents[doc.name] = doc
            except Exception as e:
                self._logger.error(f"解析子技能文档失败 {md_file}: {e}")

        return documents

    def parse_subskill_document(
        self,
        file_path: Path,
        use_cache: bool = True
    ) -> Optional[SubskillDocument]:
        if not file_path.exists():
            return None

        try:
            content = file_path.read_text(encoding='utf-8')
            stat = file_path.stat()
            current_hash = self._compute_hash(content)
            cache_key = str(file_path)

            if use_cache and cache_key in self._cache:
                cached_hash, cached_doc = self._cache[cache_key]
                if cached_hash == current_hash:
                    return cached_doc

            metadata = self._parse_frontmatter(content)
            sections = self._extract_sections(content)
            commands = self._extract_commands(content)
            templates = self._extract_templates(content)
            links = self._extract_links(content)

            name = metadata.get('name', file_path.stem)

            doc = SubskillDocument(
                name=name,
                path=file_path,
                content=content,
                metadata=metadata,
                sections=sections,
                commands=commands,
                templates=templates,
                links=links,
                hash_value=current_hash,
                last_modified=stat.st_mtime
            )

            self._cache[cache_key] = (current_hash, doc)
            return doc

        except Exception as e:
            self._logger.error(f"解析文档失败 {file_path}: {e}")
            return None

    def detect_content_changes(
        self,
        old_doc: Optional[SubskillDocument],
        new_doc: SubskillDocument
    ) -> List[ContentChange]:
        changes: List[ContentChange] = []

        if old_doc is None:
            changes.append(ContentChange(
                content_type=ContentType.SECTION,
                location="document",
                old_value=None,
                new_value=new_doc.content[:200],
                change_description="新增文档"
            ))
            return changes

        if old_doc.hash_value == new_doc.hash_value:
            return changes

        for section_name, new_section_content in new_doc.sections.items():
            old_section_content = old_doc.sections.get(section_name)
            if old_section_content is None:
                changes.append(ContentChange(
                    content_type=ContentType.SECTION,
                    location=f"section:{section_name}",
                    old_value=None,
                    new_value=new_section_content[:200],
                    change_description=f"新增章节: {section_name}"
                ))
            elif old_section_content != new_section_content:
                changes.append(ContentChange(
                    content_type=ContentType.SECTION,
                    location=f"section:{section_name}",
                    old_value=old_section_content[:200],
                    new_value=new_section_content[:200],
                    change_description=f"章节内容变化: {section_name}"
                ))

        for section_name in old_doc.sections:
            if section_name not in new_doc.sections:
                changes.append(ContentChange(
                    content_type=ContentType.SECTION,
                    location=f"section:{section_name}",
                    old_value=old_doc.sections[section_name][:200],
                    new_value=None,
                    change_description=f"删除章节: {section_name}"
                ))

        old_commands = set(old_doc.commands)
        new_commands = set(new_doc.commands)

        for cmd in new_commands - old_commands:
            changes.append(ContentChange(
                content_type=ContentType.COMMAND,
                location="commands",
                old_value=None,
                new_value=cmd[:100],
                change_description="新增命令"
            ))

        for cmd in old_commands - new_commands:
            changes.append(ContentChange(
                content_type=ContentType.COMMAND,
                location="commands",
                old_value=cmd[:100],
                new_value=None,
                change_description="删除命令"
            ))

        for key in self.REQUIRED_METADATA_FIELDS:
            old_val = old_doc.metadata.get(key)
            new_val = new_doc.metadata.get(key)
            if old_val != new_val:
                changes.append(ContentChange(
                    content_type=ContentType.METADATA_FIELD,
                    location=f"metadata:{key}",
                    old_value=str(old_val) if old_val else None,
                    new_value=str(new_val) if new_val else None,
                    change_description=f"元数据字段变化: {key}"
                ))

        return changes

    def detect_outdated_content(
        self,
        doc: SubskillDocument,
        reference_time: Optional[datetime] = None
    ) -> List[ContentChange]:
        changes: List[ContentChange] = []
        reference_time = reference_time or datetime.now()

        for link_text, link_target in doc.links:
            if link_target.startswith('http'):
                continue

            target_path = doc.path.parent / link_target
            if not target_path.exists():
                changes.append(ContentChange(
                    content_type=ContentType.LINK,
                    location=f"link:{link_target}",
                    old_value=link_target,
                    new_value=None,
                    change_description=f"无效链接: {link_target}"
                ))

        for template in doc.templates:
            template_path = doc.path.parent / template
            if not template_path.exists():
                changes.append(ContentChange(
                    content_type=ContentType.TEMPLATE,
                    location=f"template:{template}",
                    old_value=template,
                    new_value=None,
                    change_description=f"模板文件不存在: {template}"
                ))

        for field in self.REQUIRED_METADATA_FIELDS:
            if field not in doc.metadata or not doc.metadata[field]:
                changes.append(ContentChange(
                    content_type=ContentType.METADATA_FIELD,
                    location=f"metadata:{field}",
                    old_value=None,
                    new_value=None,
                    change_description=f"缺少必需的元数据字段: {field}"
                ))

        return changes

    def detect_inconsistent_references(
        self,
        doc: SubskillDocument,
        all_docs: Dict[str, SubskillDocument]
    ) -> List[ContentChange]:
        changes: List[ContentChange] = []

        for link_text, link_target in doc.links:
            if link_target.startswith('http'):
                continue

            if link_target.endswith('.md'):
                target_name = Path(link_target).stem
                if target_name not in all_docs and not (self._subskills_dir / link_target).exists():
                    changes.append(ContentChange(
                        content_type=ContentType.LINK,
                        location=f"reference:{link_target}",
                        old_value=link_target,
                        new_value=None,
                        change_description=f"引用的子技能不存在: {link_target}"
                    ))

        for template in doc.templates:
            if template.endswith('.md'):
                template_name = Path(template).stem
                if template_name not in all_docs and not (self._subskills_dir / template).exists():
                    changes.append(ContentChange(
                        content_type=ContentType.TEMPLATE,
                        location=f"reference:{template}",
                        old_value=template,
                        new_value=None,
                        change_description=f"引用的模板不存在: {template}"
                    ))

        return changes

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        match = self.YAML_FRONTMATTER_PATTERN.match(content)
        if not match:
            return {}

        frontmatter = match.group(1)
        metadata = {}

        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                if value.startswith('[') and value.endswith(']'):
                    value = [v.strip().strip('\'"') for v in value[1:-1].split(',')]
                metadata[key] = value

        return metadata

    def _extract_sections(self, content: str) -> Dict[str, str]:
        sections = {}
        lines = content.split('\n')
        current_section = None
        current_content = []

        for line in lines:
            section_match = self.SECTION_PATTERN.match(line)
            if section_match:
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = section_match.group(1).strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def _extract_commands(self, content: str) -> List[str]:
        commands = []
        for match in self.COMMAND_PATTERN.finditer(content):
            command = match.group(1).strip()
            if command and not command.startswith('#'):
                commands.append(command)
        return commands

    def _extract_templates(self, content: str) -> List[str]:
        templates = set()
        for match in self.TEMPLATE_PATTERN.finditer(content):
            template = match.group(1).strip()
            if template:
                templates.add(template)

        for match in self.LINK_PATTERN.finditer(content):
            link = match.group(2).strip()
            if link.endswith(('.md', '.yaml', '.json', '.txt')):
                templates.add(link)

        return list(templates)

    def _extract_links(self, content: str) -> List[Tuple[str, str]]:
        links = []
        for match in self.LINK_PATTERN.finditer(content):
            link_text = match.group(1).strip()
            link_target = match.group(2).strip()
            links.append((link_text, link_target))
        return links

    def _compute_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def clear_cache(self) -> None:
        self._cache.clear()


class UpdateSuggestionGenerator:
    UPDATE_TEMPLATES = {
        UpdateType.CONTENT: {
            "section_missing": "## {section_name}\n\n{content}",
            "section_empty": "## {section_name}\n\n请在此添加内容。",
        },
        UpdateType.METADATA: {
            "field_missing": "{field}: {value}",
            "field_update": "{field}: {new_value}",
        },
        UpdateType.REFERENCE: {
            "link_fix": "[{text}]({new_target})",
            "template_fix": "参考 `{template}`",
        },
        UpdateType.FORMAT: {
            "heading_fix": "## {heading}",
            "code_block_fix": "```{language}\n{code}\n```",
        }
    }

    PRIORITY_RULES = {
        "missing_metadata": Priority.HIGH,
        "broken_link": Priority.HIGH,
        "missing_section": Priority.MEDIUM,
        "content_change": Priority.MEDIUM,
        "format_issue": Priority.LOW,
    }

    def __init__(self):
        self._logger = logging.getLogger('UpdateSuggestionGenerator')

    def generate_suggestions(
        self,
        changes: List[ContentChange],
        doc: SubskillDocument
    ) -> List[SubskillUpdateSuggestion]:
        suggestions: List[SubskillUpdateSuggestion] = []

        for change in changes:
            suggestion = self._create_suggestion_from_change(change, doc)
            if suggestion:
                suggestions.append(suggestion)

        return suggestions

    def analyze_and_suggest(
        self,
        doc: SubskillDocument,
        all_docs: Dict[str, SubskillDocument]
    ) -> List[SubskillUpdateSuggestion]:
        suggestions: List[SubskillUpdateSuggestion] = []

        suggestions.extend(self._check_metadata(doc))
        suggestions.extend(self._check_sections(doc))
        suggestions.extend(self._check_links(doc, all_docs))
        suggestions.extend(self._check_format(doc))

        return suggestions

    def _create_suggestion_from_change(
        self,
        change: ContentChange,
        doc: SubskillDocument
    ) -> Optional[SubskillUpdateSuggestion]:
        if change.content_type == ContentType.METADATA_FIELD:
            return self._create_metadata_suggestion(change, doc)
        elif change.content_type == ContentType.SECTION:
            return self._create_section_suggestion(change, doc)
        elif change.content_type == ContentType.LINK:
            return self._create_link_suggestion(change, doc)
        elif change.content_type == ContentType.TEMPLATE:
            return self._create_template_suggestion(change, doc)
        return None

    def _check_metadata(self, doc: SubskillDocument) -> List[SubskillUpdateSuggestion]:
        suggestions: List[SubskillUpdateSuggestion] = []

        for field in SubskillContentDetector.REQUIRED_METADATA_FIELDS:
            if field not in doc.metadata or not doc.metadata.get(field):
                default_value = self._get_default_metadata_value(field, doc)
                suggestions.append(SubskillUpdateSuggestion(
                    subskill_name=doc.name,
                    update_type=UpdateType.METADATA,
                    priority=Priority.HIGH,
                    description=f"添加缺失的元数据字段: {field}",
                    old_content=None,
                    suggested_content=f"{field}: {default_value}",
                    reason=f"元数据字段 '{field}' 是必需的",
                    confidence=0.9
                ))

        return suggestions

    def _check_sections(self, doc: SubskillDocument) -> List[SubskillUpdateSuggestion]:
        suggestions: List[SubskillUpdateSuggestion] = []

        for section_name in SubskillContentDetector.REQUIRED_SECTIONS:
            if section_name not in doc.sections:
                template = self.UPDATE_TEMPLATES[UpdateType.CONTENT]["section_missing"]
                suggested = template.format(
                    section_name=section_name,
                    content="请在此添加相关内容。"
                )
                suggestions.append(SubskillUpdateSuggestion(
                    subskill_name=doc.name,
                    update_type=UpdateType.CONTENT,
                    priority=Priority.MEDIUM,
                    description=f"添加缺失的章节: {section_name}",
                    old_content=None,
                    suggested_content=suggested,
                    reason=f"章节 '{section_name}' 是推荐的",
                    section_name=section_name,
                    confidence=0.8
                ))

        for section_name, content in doc.sections.items():
            if not content.strip():
                template = self.UPDATE_TEMPLATES[UpdateType.CONTENT]["section_empty"]
                suggested = template.format(
                    section_name=section_name,
                    content="请在此添加相关内容。"
                )
                suggestions.append(SubskillUpdateSuggestion(
                    subskill_name=doc.name,
                    update_type=UpdateType.CONTENT,
                    priority=Priority.LOW,
                    description=f"填充空章节: {section_name}",
                    old_content=content,
                    suggested_content=suggested,
                    reason=f"章节 '{section_name}' 内容为空",
                    section_name=section_name,
                    confidence=0.7
                ))

        return suggestions

    def _check_links(
        self,
        doc: SubskillDocument,
        all_docs: Dict[str, SubskillDocument]
    ) -> List[SubskillUpdateSuggestion]:
        suggestions: List[SubskillUpdateSuggestion] = []

        for link_text, link_target in doc.links:
            if link_target.startswith('http'):
                continue

            target_path = doc.path.parent / link_target
            if not target_path.exists():
                new_target = self._find_alternative_target(link_target, all_docs)
                if new_target:
                    suggestions.append(SubskillUpdateSuggestion(
                        subskill_name=doc.name,
                        update_type=UpdateType.REFERENCE,
                        priority=Priority.HIGH,
                        description=f"修复无效链接: {link_target}",
                        old_content=f"[{link_text}]({link_target})",
                        suggested_content=f"[{link_text}]({new_target})",
                        reason=f"链接目标不存在，建议替换为: {new_target}",
                        confidence=0.8
                    ))
                else:
                    suggestions.append(SubskillUpdateSuggestion(
                        subskill_name=doc.name,
                        update_type=UpdateType.REFERENCE,
                        priority=Priority.HIGH,
                        description=f"移除无效链接: {link_target}",
                        old_content=f"[{link_text}]({link_target})",
                        suggested_content=link_text,
                        reason=f"链接目标不存在且无替代: {link_target}",
                        confidence=0.6
                    ))

        return suggestions

    def _check_format(self, doc: SubskillDocument) -> List[SubskillUpdateSuggestion]:
        suggestions: List[SubskillUpdateSuggestion] = []

        lines = doc.content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('#') and not line.startswith('# '):
                match = re.match(r'^(#{2,})([^#\s])', line)
                if match:
                    hashes = match.group(1)
                    rest = line[len(hashes):]
                    suggested = f"{hashes} {rest}"
                    suggestions.append(SubskillUpdateSuggestion(
                        subskill_name=doc.name,
                        update_type=UpdateType.FORMAT,
                        priority=Priority.LOW,
                        description="修复标题格式",
                        old_content=line,
                        suggested_content=suggested,
                        reason="标题后应有一个空格",
                        line_number=i + 1,
                        confidence=0.9
                    ))

        return suggestions

    def _create_metadata_suggestion(
        self,
        change: ContentChange,
        doc: SubskillDocument
    ) -> Optional[SubskillUpdateSuggestion]:
        if change.old_value is None and change.new_value is None:
            field = change.location.split(':')[1] if ':' in change.location else ''
            default_value = self._get_default_metadata_value(field, doc)
            return SubskillUpdateSuggestion(
                subskill_name=doc.name,
                update_type=UpdateType.METADATA,
                priority=Priority.HIGH,
                description=f"添加缺失的元数据字段: {field}",
                old_content=None,
                suggested_content=f"{field}: {default_value}",
                reason=f"元数据字段 '{field}' 是必需的",
                confidence=0.9
            )
        return None

    def _create_section_suggestion(
        self,
        change: ContentChange,
        doc: SubskillDocument
    ) -> Optional[SubskillUpdateSuggestion]:
        if change.old_value is None and change.new_value:
            section_name = change.location.split(':')[1] if ':' in change.location else ''
            return SubskillUpdateSuggestion(
                subskill_name=doc.name,
                update_type=UpdateType.CONTENT,
                priority=Priority.MEDIUM,
                description=f"新增章节: {section_name}",
                old_content=None,
                suggested_content=change.new_value,
                reason=change.change_description,
                section_name=section_name,
                confidence=0.8
            )
        return None

    def _create_link_suggestion(
        self,
        change: ContentChange,
        doc: SubskillDocument
    ) -> Optional[SubskillUpdateSuggestion]:
        if change.old_value and change.new_value is None:
            return SubskillUpdateSuggestion(
                subskill_name=doc.name,
                update_type=UpdateType.REFERENCE,
                priority=Priority.HIGH,
                description=f"修复无效链接: {change.old_value}",
                old_content=change.old_value,
                suggested_content="",
                reason=change.change_description,
                confidence=0.7
            )
        return None

    def _create_template_suggestion(
        self,
        change: ContentChange,
        doc: SubskillDocument
    ) -> Optional[SubskillUpdateSuggestion]:
        if change.old_value and change.new_value is None:
            return SubskillUpdateSuggestion(
                subskill_name=doc.name,
                update_type=UpdateType.REFERENCE,
                priority=Priority.MEDIUM,
                description=f"修复模板引用: {change.old_value}",
                old_content=change.old_value,
                suggested_content="",
                reason=change.change_description,
                confidence=0.7
            )
        return None

    def _get_default_metadata_value(self, field: str, doc: SubskillDocument) -> str:
        defaults = {
            'name': doc.name,
            'description': f"{doc.name} 子技能",
            'version': '1.0.0',
            'author': 'system',
            'created_at': datetime.now().strftime('%Y-%m-%d')
        }
        return defaults.get(field, '')

    def _find_alternative_target(
        self,
        original_target: str,
        all_docs: Dict[str, SubskillDocument]
    ) -> Optional[str]:
        target_name = Path(original_target).stem.lower()

        for doc_name in all_docs:
            if doc_name.lower() == target_name:
                return f"{doc_name}.md"

        for doc_name in all_docs:
            if target_name in doc_name.lower() or doc_name.lower() in target_name:
                return f"{doc_name}.md"

        return None

    def prioritize_suggestions(
        self,
        suggestions: List[SubskillUpdateSuggestion]
    ) -> List[SubskillUpdateSuggestion]:
        return sorted(suggestions, key=lambda s: s.priority.value)

    def filter_by_confidence(
        self,
        suggestions: List[SubskillUpdateSuggestion],
        min_confidence: float = 0.5
    ) -> List[SubskillUpdateSuggestion]:
        return [s for s in suggestions if s.confidence >= min_confidence]


class AutoUpdateExecutor:
    def __init__(self, backup_dir: Optional[Path] = None):
        self._backup_dir = backup_dir
        self._logger = logging.getLogger('AutoUpdateExecutor')
        self._update_hooks: Dict[str, List[Callable]] = {
            'pre_update': [],
            'post_update': [],
            'on_error': []
        }

    def add_hook(self, event: str, callback: Callable) -> None:
        if event in self._update_hooks:
            self._update_hooks[event].append(callback)

    def apply_updates(
        self,
        doc: SubskillDocument,
        suggestions: List[SubskillUpdateSuggestion],
        auto_backup: bool = True
    ) -> SubskillUpdateResult:
        start_time = datetime.now()
        applied: List[SubskillUpdateSuggestion] = []
        skipped: List[SubskillUpdateSuggestion] = []
        errors: List[str] = []
        backup_path: Optional[Path] = None

        self._execute_hooks('pre_update', doc, suggestions)

        try:
            if auto_backup:
                backup_path = self._create_backup(doc)

            content = doc.content
            metadata = doc.metadata.copy()

            for suggestion in self.prioritize_suggestions(suggestions):
                try:
                    updated_content, updated_metadata = self._apply_suggestion(
                        content, metadata, suggestion
                    )
                    if updated_content != content or updated_metadata != metadata:
                        content = updated_content
                        metadata = updated_metadata
                        applied.append(suggestion)
                    else:
                        skipped.append(suggestion)
                except Exception as e:
                    skipped.append(suggestion)
                    errors.append(f"应用更新失败: {suggestion.description} - {str(e)}")
                    self._logger.error(f"应用更新失败: {e}")

            if applied:
                content = self._rebuild_document(content, metadata)
                self._write_document(doc.path, content)

        except Exception as e:
            errors.append(f"更新过程失败: {str(e)}")
            self._execute_hooks('on_error', doc, e)

            if backup_path:
                self._restore_from_backup(doc.path, backup_path)
            raise

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        self._execute_hooks('post_update', doc, applied)

        return SubskillUpdateResult(
            subskill_name=doc.name,
            success=len(errors) == 0,
            applied_suggestions=applied,
            skipped_suggestions=skipped,
            validation_errors=errors,
            backup_path=backup_path,
            duration_seconds=duration
        )

    def batch_update(
        self,
        docs_with_suggestions: Dict[str, Tuple[SubskillDocument, List[SubskillUpdateSuggestion]]],
        auto_backup: bool = True
    ) -> Dict[str, SubskillUpdateResult]:
        results: Dict[str, SubskillUpdateResult] = {}

        for name, (doc, suggestions) in docs_with_suggestions.items():
            try:
                result = self.apply_updates(doc, suggestions, auto_backup)
                results[name] = result
            except Exception as e:
                results[name] = SubskillUpdateResult(
                    subskill_name=name,
                    success=False,
                    applied_suggestions=[],
                    skipped_suggestions=suggestions,
                    validation_errors=[str(e)],
                    backup_path=None
                )

        return results

    def rollback(self, doc: SubskillDocument, backup_path: Path) -> bool:
        try:
            if backup_path.exists():
                shutil.copy2(backup_path, doc.path)
                self._logger.info(f"已从备份恢复: {doc.name}")
                return True
            return False
        except Exception as e:
            self._logger.error(f"回滚失败: {e}")
            return False

    def _apply_suggestion(
        self,
        content: str,
        metadata: Dict[str, Any],
        suggestion: SubskillUpdateSuggestion
    ) -> Tuple[str, Dict[str, Any]]:
        if suggestion.update_type == UpdateType.METADATA:
            metadata = self._apply_metadata_update(metadata, suggestion)
        elif suggestion.update_type == UpdateType.CONTENT:
            content = self._apply_content_update(content, suggestion)
        elif suggestion.update_type == UpdateType.REFERENCE:
            content = self._apply_reference_update(content, suggestion)
        elif suggestion.update_type == UpdateType.FORMAT:
            content = self._apply_format_update(content, suggestion)

        return content, metadata

    def _apply_metadata_update(
        self,
        metadata: Dict[str, Any],
        suggestion: SubskillUpdateSuggestion
    ) -> Dict[str, Any]:
        if ':' in suggestion.suggested_content:
            field, value = suggestion.suggested_content.split(':', 1)
            metadata[field.strip()] = value.strip()
        return metadata

    def _apply_content_update(
        self,
        content: str,
        suggestion: SubskillUpdateSuggestion
    ) -> str:
        if suggestion.section_name:
            section_pattern = re.compile(
                rf'^##\s+{re.escape(suggestion.section_name)}.*?(?=^##|\Z)',
                re.MULTILINE | re.DOTALL
            )

            if section_pattern.search(content):
                if suggestion.old_content:
                    content = section_pattern.sub(suggestion.suggested_content, content)
            else:
                content = content.rstrip() + '\n\n' + suggestion.suggested_content

        return content

    def _apply_reference_update(
        self,
        content: str,
        suggestion: SubskillUpdateSuggestion
    ) -> str:
        if suggestion.old_content and suggestion.old_content in content:
            content = content.replace(suggestion.old_content, suggestion.suggested_content)
        return content

    def _apply_format_update(
        self,
        content: str,
        suggestion: SubskillUpdateSuggestion
    ) -> str:
        if suggestion.line_number:
            lines = content.split('\n')
            if 0 < suggestion.line_number <= len(lines):
                lines[suggestion.line_number - 1] = suggestion.suggested_content
                content = '\n'.join(lines)
        elif suggestion.old_content and suggestion.old_content in content:
            content = content.replace(suggestion.old_content, suggestion.suggested_content)

        return content

    def _rebuild_document(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> str:
        frontmatter_match = re.match(r'^---\s*\n.*?\n---\s*\n', content, re.DOTALL)

        frontmatter_lines = ['---']
        for key, value in metadata.items():
            if isinstance(value, list):
                formatted_value = '[' + ', '.join(f"'{v}'" for v in value) + ']'
                frontmatter_lines.append(f"{key}: {formatted_value}")
            else:
                frontmatter_lines.append(f"{key}: {value}")
        frontmatter_lines.append('---')
        new_frontmatter = '\n'.join(frontmatter_lines) + '\n'

        if frontmatter_match:
            content = new_frontmatter + content[frontmatter_match.end():]
        else:
            content = new_frontmatter + content

        return content

    def _create_backup(self, doc: SubskillDocument) -> Path:
        if self._backup_dir:
            backup_dir = self._backup_dir
        else:
            backup_dir = doc.path.parent / '.backups'

        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{doc.name}_{timestamp}.md"
        backup_path = backup_dir / backup_name

        shutil.copy2(doc.path, backup_path)
        self._logger.info(f"已创建备份: {backup_path}")

        return backup_path

    def _restore_from_backup(self, doc_path: Path, backup_path: Path) -> bool:
        try:
            if backup_path.exists():
                shutil.copy2(backup_path, doc_path)
                return True
            return False
        except Exception as e:
            self._logger.error(f"恢复备份失败: {e}")
            return False

    def _write_document(self, path: Path, content: str) -> None:
        path.write_text(content, encoding='utf-8')

    def _execute_hooks(self, event: str, *args, **kwargs) -> None:
        if event in self._update_hooks:
            for callback in self._update_hooks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    self._logger.error(f"钩子执行失败: {e}")

    def prioritize_suggestions(
        self,
        suggestions: List[SubskillUpdateSuggestion]
    ) -> List[SubskillUpdateSuggestion]:
        return sorted(suggestions, key=lambda s: s.priority.value)


class UpdateValidator:
    def __init__(self):
        self._logger = logging.getLogger('UpdateValidator')
        self._validators: Dict[str, Callable] = {
            'format': self._validate_format,
            'links': self._validate_links,
            'metadata': self._validate_metadata,
            'content': self._validate_content,
            'structure': self._validate_structure
        }

    def validate_document(
        self,
        doc: SubskillDocument,
        checks: Optional[Set[str]] = None
    ) -> ValidationResult:
        checks = checks or set(self._validators.keys())
        errors: List[str] = []
        warnings: List[str] = []
        checks_passed = 0
        checks_failed = 0
        details: Dict[str, Any] = {}

        for check_name in checks:
            if check_name not in self._validators:
                continue

            try:
                result = self._validators[check_name](doc)
                details[check_name] = result

                if result.get('passed', False):
                    checks_passed += 1
                else:
                    checks_failed += 1
                    errors.extend(result.get('errors', []))
                    warnings.extend(result.get('warnings', []))

            except Exception as e:
                checks_failed += 1
                errors.append(f"验证检查 '{check_name}' 失败: {str(e)}")

        status = ValidationStatus.VALID
        if errors:
            status = ValidationStatus.INVALID
        elif warnings:
            status = ValidationStatus.WARNING

        return ValidationResult(
            subskill_name=doc.name,
            status=status,
            errors=errors,
            warnings=warnings,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            details=details
        )

    def validate_batch(
        self,
        docs: Dict[str, SubskillDocument],
        checks: Optional[Set[str]] = None
    ) -> Dict[str, ValidationResult]:
        results: Dict[str, ValidationResult] = {}

        for name, doc in docs.items():
            results[name] = self.validate_document(doc, checks)

        return results

    def generate_validation_report(
        self,
        results: Dict[str, ValidationResult]
    ) -> Dict[str, Any]:
        total = len(results)
        valid_count = sum(1 for r in results.values() if r.status == ValidationStatus.VALID)
        warning_count = sum(1 for r in results.values() if r.status == ValidationStatus.WARNING)
        invalid_count = sum(1 for r in results.values() if r.status == ValidationStatus.INVALID)

        all_errors: List[str] = []
        all_warnings: List[str] = []

        for result in results.values():
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        return {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_documents": total,
                "valid": valid_count,
                "with_warnings": warning_count,
                "invalid": invalid_count,
                "total_errors": len(all_errors),
                "total_warnings": len(all_warnings)
            },
            "details": {name: r.to_dict() for name, r in results.items()},
            "errors_by_document": {
                name: r.errors for name, r in results.items() if r.errors
            },
            "warnings_by_document": {
                name: r.warnings for name, r in results.items() if r.warnings
            }
        }

    def _validate_format(self, doc: SubskillDocument) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        passed = True

        lines = doc.content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('#') and not line.startswith('# '):
                match = re.match(r'^(#{2,})([^#\s])', line)
                if match:
                    warnings.append(f"第 {i + 1} 行: 标题后缺少空格")
                    passed = False

        code_blocks = re.findall(r'```(\w*)', doc.content)
        open_count = code_blocks.count('```') + len([b for b in code_blocks if b])
        if open_count % 2 != 0:
            errors.append("代码块未正确闭合")
            passed = False

        return {
            "passed": passed,
            "errors": errors,
            "warnings": warnings
        }

    def _validate_links(self, doc: SubskillDocument) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        passed = True

        for link_text, link_target in doc.links:
            if link_target.startswith('http'):
                continue

            target_path = doc.path.parent / link_target
            if not target_path.exists():
                errors.append(f"无效链接: [{link_text}]({link_target})")
                passed = False

        return {
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "links_checked": len(doc.links)
        }

    def _validate_metadata(self, doc: SubskillDocument) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        passed = True

        for field in SubskillContentDetector.REQUIRED_METADATA_FIELDS:
            if field not in doc.metadata:
                errors.append(f"缺少必需的元数据字段: {field}")
                passed = False
            elif not doc.metadata.get(field):
                warnings.append(f"元数据字段为空: {field}")

        return {
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "metadata_fields": list(doc.metadata.keys())
        }

    def _validate_content(self, doc: SubskillDocument) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        passed = True

        if not doc.content.strip():
            errors.append("文档内容为空")
            return {"passed": False, "errors": errors, "warnings": warnings}

        if len(doc.content) < 50:
            warnings.append("文档内容过短")

        for section_name, content in doc.sections.items():
            if not content.strip():
                warnings.append(f"章节 '{section_name}' 内容为空")

        return {
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "content_length": len(doc.content),
            "sections_count": len(doc.sections)
        }

    def _validate_structure(self, doc: SubskillDocument) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        passed = True

        has_frontmatter = bool(re.match(r'^---\s*\n.*?\n---\s*\n', doc.content, re.DOTALL))
        if not has_frontmatter:
            warnings.append("文档缺少 YAML frontmatter")

        has_title = bool(re.search(r'^#\s+.+$', doc.content, re.MULTILINE))
        if not has_title:
            warnings.append("文档缺少一级标题")

        return {
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "has_frontmatter": has_frontmatter,
            "has_title": has_title
        }


class SubskillDocUpdater:
    def __init__(
        self,
        skill_dir: str,
        backup_dir: Optional[str] = None,
        auto_save_cache: bool = True
    ):
        self._skill_dir = Path(skill_dir)
        self._backup_dir = Path(backup_dir) if backup_dir else None

        self._detector = SubskillContentDetector(self._skill_dir)
        self._generator = UpdateSuggestionGenerator()
        self._executor = AutoUpdateExecutor(self._backup_dir)
        self._validator = UpdateValidator()

        self._auto_save_cache = auto_save_cache
        self._logger = logging.getLogger('SubskillDocUpdater')
        self._lock = threading.Lock()

        self._update_history: List[Dict[str, Any]] = []

    def detect_and_suggest(
        self,
        subskill_names: Optional[List[str]] = None
    ) -> List[SubskillUpdateSuggestion]:
        all_suggestions: List[SubskillUpdateSuggestion] = []
        all_docs = self._detector.scan_all_subskills()

        docs_to_check = all_docs
        if subskill_names:
            docs_to_check = {
                name: doc for name, doc in all_docs.items()
                if name in subskill_names
            }

        for name, doc in docs_to_check.items():
            suggestions = self._generator.analyze_and_suggest(doc, all_docs)
            all_suggestions.extend(suggestions)

        return self._generator.prioritize_suggestions(all_suggestions)

    def apply_updates(
        self,
        suggestions: List[SubskillUpdateSuggestion],
        auto_backup: bool = True,
        validate_after: bool = True
    ) -> Dict[str, SubskillUpdateResult]:
        all_docs = self._detector.scan_all_subskills(incremental=False)

        docs_with_suggestions: Dict[str, Tuple[SubskillDocument, List[SubskillUpdateSuggestion]]] = {}

        for suggestion in suggestions:
            name = suggestion.subskill_name
            if name not in all_docs:
                continue

            if name not in docs_with_suggestions:
                docs_with_suggestions[name] = (all_docs[name], [])
            docs_with_suggestions[name][1].append(suggestion)

        results = self._executor.batch_update(docs_with_suggestions, auto_backup)

        if validate_after:
            self._validate_after_update(results)

        self._record_update_history(results)

        return results

    def update_single_subskill(
        self,
        subskill_name: str,
        auto_backup: bool = True
    ) -> SubskillUpdateResult:
        suggestions = self.detect_and_suggest([subskill_name])
        all_docs = self._detector.scan_all_subscripts()

        if subskill_name not in all_docs:
            return SubskillUpdateResult(
                subskill_name=subskill_name,
                success=False,
                applied_suggestions=[],
                skipped_suggestions=[],
                validation_errors=[f"子技能不存在: {subskill_name}"],
                backup_path=None
            )

        doc = all_docs[subskill_name]
        return self._executor.apply_updates(doc, suggestions, auto_backup)

    def validate_all(
        self,
        checks: Optional[Set[str]] = None
    ) -> Dict[str, ValidationResult]:
        all_docs = self._detector.scan_all_subskills()
        return self._validator.validate_batch(all_docs, checks)

    def validate_subskill(
        self,
        subskill_name: str,
        checks: Optional[Set[str]] = None
    ) -> Optional[ValidationResult]:
        all_docs = self._detector.scan_all_subskills()

        if subskill_name not in all_docs:
            return None

        return self._validator.validate_document(all_docs[subskill_name], checks)

    def generate_report(
        self,
        format: str = 'json'
    ) -> Dict[str, Any]:
        all_docs = self._detector.scan_all_subskills()
        suggestions = self.detect_and_suggest()
        validation_results = self.validate_all()

        report = {
            "generated_at": datetime.now().isoformat(),
            "skill_dir": str(self._skill_dir),
            "summary": {
                "total_subskills": len(all_docs),
                "total_suggestions": len(suggestions),
                "suggestions_by_priority": self._count_by_priority(suggestions),
                "suggestions_by_type": self._count_by_type(suggestions)
            },
            "validation_summary": self._validator.generate_validation_report(validation_results),
            "suggestions": [s.to_dict() for s in suggestions[:100]],
            "update_history": self._update_history[-10:]
        }

        return report

    def rollback_subskill(
        self,
        subskill_name: str,
        backup_path: Path
    ) -> bool:
        all_docs = self._detector.scan_all_subskills()

        if subskill_name not in all_docs:
            return False

        return self._executor.rollback(all_docs[subskill_name], backup_path)

    def get_subskill_document(self, subskill_name: str) -> Optional[SubskillDocument]:
        all_docs = self._detector.scan_all_subskills()
        return all_docs.get(subskill_name)

    def list_subskills(self) -> List[str]:
        all_docs = self._detector.scan_all_subskills()
        return list(all_docs.keys())

    def clear_cache(self) -> None:
        self._detector.clear_cache()

    def _validate_after_update(self, results: Dict[str, SubskillUpdateResult]) -> None:
        for name, result in results.items():
            if result.success:
                validation = self.validate_subskill(name)
                if validation and validation.status != ValidationStatus.VALID:
                    result.validation_errors.extend(validation.warnings)

    def _record_update_history(self, results: Dict[str, SubskillUpdateResult]) -> None:
        with self._lock:
            record = {
                "timestamp": datetime.now().isoformat(),
                "total_updated": len(results),
                "successful": sum(1 for r in results.values() if r.success),
                "failed": sum(1 for r in results.values() if not r.success),
                "details": {name: r.to_dict() for name, r in results.items()}
            }
            self._update_history.append(record)

            if len(self._update_history) > 100:
                self._update_history = self._update_history[-100:]

    def _count_by_priority(
        self,
        suggestions: List[SubskillUpdateSuggestion]
    ) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for s in suggestions:
            key = s.priority.name
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _count_by_type(
        self,
        suggestions: List[SubskillUpdateSuggestion]
    ) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for s in suggestions:
            key = s.update_type.name
            counts[key] = counts.get(key, 0) + 1
        return counts


def main():
    import argparse

    parser = argparse.ArgumentParser(description="子技能文档更新器")
    parser.add_argument(
        '--skill-dir',
        type=str,
        default='.',
        help='技能目录路径'
    )
    parser.add_argument(
        '--backup-dir',
        type=str,
        default=None,
        help='备份目录路径'
    )
    parser.add_argument(
        '--detect',
        action='store_true',
        help='检测并生成更新建议'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='应用更新建议'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='验证文档'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='生成报告'
    )
    parser.add_argument(
        '--subskill',
        type=str,
        default=None,
        help='指定子技能名称'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='输出文件路径'
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
    )

    updater = SubskillDocUpdater(
        skill_dir=args.skill_dir,
        backup_dir=args.backup_dir
    )

    if args.detect:
        suggestions = updater.detect_and_suggest(
            [args.subskill] if args.subskill else None
        )
        print(f"\n检测到 {len(suggestions)} 个更新建议:")
        for s in suggestions[:20]:
            print(f"  [{s.priority.name}] {s.subskill_name}: {s.description}")

    if args.apply:
        suggestions = updater.detect_and_suggest(
            [args.subskill] if args.subskill else None
        )
        results = updater.apply_updates(suggestions)

        print(f"\n更新结果:")
        for name, result in results.items():
            status = "成功" if result.success else "失败"
            print(f"  {name}: {status} (应用 {len(result.applied_suggestions)} 个更新)")

    if args.validate:
        results = updater.validate_all()

        print(f"\n验证结果:")
        for name, result in results.items():
            print(f"  {name}: {result.status.name}")
            if result.errors:
                for err in result.errors[:3]:
                    print(f"    - 错误: {err}")

    if args.report:
        report = updater.generate_report()

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(
                json.dumps(report, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            print(f"\n报告已保存: {output_path}")
        else:
            print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
