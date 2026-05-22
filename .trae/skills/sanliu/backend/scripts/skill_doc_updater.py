#!/usr/bin/env python3
"""
技能文档智能更新脚本
实现技能文档自动更新、版本信息同步、增强技能文档报告

功能:
- 技能文档自动更新（根据代码变更自动更新文档）
- 版本信息同步（同步版本号、更新日志）
- 增强技能文档报告（生成详细的文档状态报告）
"""

import os
import sys
import json
import re
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False


def detect_file_encoding(file_path: str, default_encoding: str = 'utf-8') -> str:
    if not CHARDET_AVAILABLE:
        return default_encoding
    
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)
        
        if not raw_data:
            return default_encoding
        
        result = chardet.detect(raw_data)
        detected_encoding = result.get('encoding', default_encoding)
        confidence = result.get('confidence', 0)
        
        if confidence < 0.7:
            return default_encoding
        
        if detected_encoding and detected_encoding.lower() in ['gb2312', 'gbk', 'gb18030']:
            return 'gb18030'
        
        return detected_encoding or default_encoding
    except Exception:
        return default_encoding


def safe_read_file(file_path: str, fallback_encodings: List[str] = None) -> Tuple[str, str]:
    if fallback_encodings is None:
        fallback_encodings = ['utf-8', 'gb18030', 'gbk', 'gb2312', 'latin1']
    
    detected_encoding = detect_file_encoding(file_path)
    
    encodings_to_try = [detected_encoding] + [e for e in fallback_encodings if e != detected_encoding]
    
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content, encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            continue
    
    try:
        with open(file_path, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
        return content, 'utf-8-ignore'
    except Exception:
        return '', 'failed'


class DocSection(Enum):
    OVERVIEW = "overview"
    FEATURES = "features"
    USAGE = "usage"
    API = "api"
    EXAMPLES = "examples"
    CHANGELOG = "changelog"
    CONFIGURATION = "configuration"
    TROUBLESHOOTING = "troubleshooting"
    DEPENDENCIES = "dependencies"
    PERFORMANCE = "performance"


class UpdateType(Enum):
    FEATURE_ADDED = "feature_added"
    FEATURE_MODIFIED = "feature_modified"
    FEATURE_REMOVED = "feature_removed"
    BUG_FIX = "bug_fix"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    DEPENDENCY = "dependency"
    SECURITY = "security"


class DocStatus(Enum):
    UP_TO_DATE = "up_to_date"
    NEEDS_UPDATE = "needs_update"
    OUTDATED = "outdated"
    MISSING = "missing"


@dataclass
class VersionInfo:
    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    @classmethod
    def parse(cls, version_str: str) -> 'VersionInfo':
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$'
        match = re.match(pattern, version_str)
        
        if not match:
            return cls(0, 0, 1)
        
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4) or "",
            build=match.group(5) or ""
        )
    
    def bump_major(self) -> 'VersionInfo':
        return VersionInfo(self.major + 1, 0, 0, timestamp=datetime.now().isoformat())
    
    def bump_minor(self) -> 'VersionInfo':
        return VersionInfo(self.major, self.minor + 1, 0, timestamp=datetime.now().isoformat())
    
    def bump_patch(self) -> 'VersionInfo':
        return VersionInfo(self.major, self.minor, self.patch + 1, timestamp=datetime.now().isoformat())


@dataclass
class ChangelogEntry:
    version: str
    date: str
    changes: List[Dict[str, Any]]
    
    def __post_init__(self):
        if not self.date:
            self.date = datetime.now().strftime('%Y-%m-%d')


@dataclass
class DocUpdateRecord:
    update_id: str
    skill_name: str
    timestamp: str
    update_type: UpdateType
    sections_updated: List[str]
    changes_summary: str
    version_before: str
    version_after: str
    files_modified: List[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DocSectionStatus:
    section: DocSection
    status: DocStatus
    last_updated: str
    content_hash: str
    issues: List[str] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []


@dataclass
class SkillDocReport:
    skill_name: str
    skill_path: str
    version: str
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    overall_status: DocStatus = DocStatus.MISSING
    sections: List[DocSectionStatus] = field(default_factory=list)
    completeness_score: float = 0.0
    quality_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    missing_sections: List[str] = field(default_factory=list)
    outdated_sections: List[str] = field(default_factory=list)


class VersionManager:
    """版本管理器"""
    
    def __init__(self, skill_path: str):
        self.skill_path = Path(skill_path)
        self.version_file = self.skill_path / "docs" / "version.json"
        self.changelog_file = self.skill_path / "docs" / "CHANGELOG.md"
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('VersionManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def get_current_version(self) -> VersionInfo:
        if self.version_file.exists():
            try:
                content, encoding = safe_read_file(str(self.version_file))
                if content:
                    data = json.loads(content)
                    return VersionInfo(
                        major=data.get('major', 0),
                        minor=data.get('minor', 0),
                        patch=data.get('patch', 1),
                        prerelease=data.get('prerelease', ''),
                        build=data.get('build', ''),
                        timestamp=data.get('timestamp', '')
                    )
            except Exception as e:
                self.logger.warning(f"读取版本文件失败: {e}")
        
        return VersionInfo(0, 0, 1)
    
    def set_version(self, version: VersionInfo) -> None:
        self.version_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'major': version.major,
            'minor': version.minor,
            'patch': version.patch,
            'prerelease': version.prerelease,
            'build': version.build,
            'timestamp': version.timestamp,
            'version_string': str(version)
        }
        
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"版本已更新: {version}")
    
    def bump_version(self, update_type: UpdateType) -> VersionInfo:
        current = self.get_current_version()
        
        if update_type in [UpdateType.FEATURE_ADDED, UpdateType.FEATURE_REMOVED]:
            new_version = current.bump_minor()
        elif update_type in [UpdateType.FEATURE_MODIFIED, UpdateType.BUG_FIX, 
                             UpdateType.PERFORMANCE, UpdateType.SECURITY]:
            new_version = current.bump_patch()
        else:
            new_version = current.bump_patch()
        
        self.set_version(new_version)
        return new_version
    
    def add_changelog_entry(self, entry: ChangelogEntry) -> None:
        self.changelog_file.parent.mkdir(parents=True, exist_ok=True)
        
        entry_md = self._format_changelog_entry(entry)
        
        if self.changelog_file.exists():
            content, encoding = safe_read_file(str(self.changelog_file))
            
            if not content:
                self.logger.warning(f"无法读取变更日志文件")
                return
            
            if entry.version in content:
                self.logger.warning(f"版本 {entry.version} 已存在于变更日志中")
                return
            
            lines = content.split('\n')
            insert_pos = 0
            
            for i, line in enumerate(lines):
                if line.startswith('## '):
                    insert_pos = i
                    break
            
            lines.insert(insert_pos, entry_md)
            new_content = '\n'.join(lines)
        else:
            header = "# 变更日志\n\n本文档记录技能的所有重要变更。\n\n"
            new_content = header + entry_md
        
        self.changelog_file.write_text(new_content, encoding='utf-8')
        self.logger.info(f"变更日志已更新: {entry.version}")
    
    def _format_changelog_entry(self, entry: ChangelogEntry) -> str:
        lines = [
            f"## [{entry.version}] - {entry.date}",
            ""
        ]
        
        changes_by_type = defaultdict(list)
        for change in entry.changes:
            change_type = change.get('type', 'other')
            changes_by_type[change_type].append(change)
        
        type_labels = {
            'feature_added': '### 新增功能',
            'feature_modified': '### 功能变更',
            'feature_removed': '### 移除功能',
            'bug_fix': '### 问题修复',
            'performance': '### 性能优化',
            'documentation': '### 文档更新',
            'security': '### 安全更新',
            'dependency': '### 依赖更新',
            'other': '### 其他'
        }
        
        for change_type, changes in changes_by_type.items():
            label = type_labels.get(change_type, '### 其他')
            lines.append(label)
            lines.append("")
            
            for change in changes:
                description = change.get('description', '')
                scope = change.get('scope', '')
                
                if scope:
                    lines.append(f"- **{scope}**: {description}")
                else:
                    lines.append(f"- {description}")
            
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        return '\n'.join(lines)
    
    def get_changelog(self, limit: int = 10) -> List[ChangelogEntry]:
        if not self.changelog_file.exists():
            return []
        
        content, encoding = safe_read_file(str(self.changelog_file))
        if not content:
            return []
        
        entries = []
        
        pattern = r'## \[([^\]]+)\] - (\d{4}-\d{2}-\d{2})'
        matches = re.findall(pattern, content)
        
        for version, date in matches[:limit]:
            entries.append(ChangelogEntry(version=version, date=date, changes=[]))
        
        return entries


class DocAnalyzer:
    """文档分析器"""
    
    REQUIRED_SECTIONS = [
        DocSection.OVERVIEW,
        DocSection.FEATURES,
        DocSection.USAGE,
    ]
    
    RECOMMENDED_SECTIONS = [
        DocSection.API,
        DocSection.EXAMPLES,
        DocSection.CONFIGURATION,
    ]
    
    def __init__(self):
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('DocAnalyzer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def analyze_skill_doc(self, skill_path: str) -> SkillDocReport:
        path = Path(skill_path)
        skill_md = path / "SKILL.md"
        
        if not skill_md.exists():
            return SkillDocReport(
                skill_name=path.name,
                skill_path=str(skill_path),
                version="0.0.0",
                overall_status=DocStatus.MISSING,
                sections=[],
                completeness_score=0.0,
                quality_score=0.0,
                recommendations=["创建 SKILL.md 文件"],
                missing_sections=[s.value for s in self.REQUIRED_SECTIONS],
                outdated_sections=[]
            )
        
        content, encoding = safe_read_file(str(skill_md))
        if not content:
            return SkillDocReport(
                skill_name=path.name,
                skill_path=str(skill_path),
                version="0.0.0",
                overall_status=DocStatus.MISSING,
                sections=[],
                completeness_score=0.0,
                quality_score=0.0,
                recommendations=["无法读取 SKILL.md 文件"],
                missing_sections=[s.value for s in self.REQUIRED_SECTIONS],
                outdated_sections=[]
            )
        
        sections = self._extract_sections(content)
        
        version = self._extract_version(content)
        
        section_statuses = self._analyze_sections(sections, content)
        
        completeness = self._calculate_completeness(section_statuses)
        quality = self._calculate_quality(content, sections)
        
        missing = self._identify_missing_sections(section_statuses)
        outdated = self._identify_outdated_sections(section_statuses)
        recommendations = self._generate_recommendations(section_statuses, content)
        
        overall = self._determine_overall_status(section_statuses)
        
        return SkillDocReport(
            skill_name=path.name,
            skill_path=str(skill_path),
            version=version,
            overall_status=overall,
            sections=section_statuses,
            completeness_score=completeness,
            quality_score=quality,
            recommendations=recommendations,
            missing_sections=missing,
            outdated_sections=outdated
        )
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        sections = {}
        
        section_patterns = {
            DocSection.OVERVIEW: r'##?\s*(概述|Overview|简介|介绍)',
            DocSection.FEATURES: r'##?\s*(功能|Features|特性|功能特性)',
            DocSection.USAGE: r'##?\s*(使用|Usage|使用方法|使用说明)',
            DocSection.API: r'##?\s*(API|接口|API参考)',
            DocSection.EXAMPLES: r'##?\s*(示例|Examples|使用示例|代码示例)',
            DocSection.CHANGELOG: r'##?\s*(变更|Changelog|更新日志|版本历史)',
            DocSection.CONFIGURATION: r'##?\s*(配置|Configuration|配置说明|配置选项)',
            DocSection.TROUBLESHOOTING: r'##?\s*(故障|Troubleshooting|常见问题|FAQ)',
            DocSection.DEPENDENCIES: r'##?\s*(依赖|Dependencies|依赖项)',
            DocSection.PERFORMANCE: r'##?\s*(性能|Performance|性能优化)',
        }
        
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            header_match = re.match(r'^#+\s+(.+)$', line)
            
            if header_match:
                if current_section and current_content:
                    sections[current_section.value] = '\n'.join(current_content)
                
                current_content = []
                header_text = header_match.group(1)
                
                for section, pattern in section_patterns.items():
                    if re.search(pattern, header_text, re.IGNORECASE):
                        current_section = section
                        break
                else:
                    current_section = None
            else:
                if current_section:
                    current_content.append(line)
        
        if current_section and current_content:
            sections[current_section.value] = '\n'.join(current_content)
        
        return sections
    
    def _extract_version(self, content: str) -> str:
        patterns = [
            r'版本[：:]\s*(\d+\.\d+\.\d+)',
            r'Version[：:]\s*(\d+\.\d+\.\d+)',
            r'v(\d+\.\d+\.\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "0.0.0"
    
    def _analyze_sections(self, sections: Dict[str, str], 
                          full_content: str) -> List[DocSectionStatus]:
        statuses = []
        
        for section in DocSection:
            content = sections.get(section.value, "")
            
            if not content:
                status = DocStatus.MISSING
                issues = ["缺少该章节"]
            elif len(content.strip()) < 50:
                status = DocStatus.NEEDS_UPDATE
                issues = ["内容过短，需要补充"]
            else:
                status = DocStatus.UP_TO_DATE
                issues = self._check_section_issues(section, content)
                
                if issues:
                    status = DocStatus.NEEDS_UPDATE
            
            content_hash = str(hash(content) % 1000000)
            
            statuses.append(DocSectionStatus(
                section=section,
                status=status,
                last_updated=datetime.now().isoformat(),
                content_hash=content_hash,
                issues=issues
            ))
        
        return statuses
    
    def _check_section_issues(self, section: DocSection, content: str) -> List[str]:
        issues = []
        
        if section == DocSection.OVERVIEW:
            if '功能' not in content and 'feature' not in content.lower():
                issues.append("概述中缺少功能描述")
        
        elif section == DocSection.USAGE:
            if '```' not in content:
                issues.append("使用说明中缺少代码示例")
        
        elif section == DocSection.API:
            if '参数' not in content and 'parameter' not in content.lower():
                issues.append("API文档中缺少参数说明")
        
        elif section == DocSection.EXAMPLES:
            if '```' not in content:
                issues.append("示例章节中缺少代码块")
        
        return issues
    
    def _calculate_completeness(self, sections: List[DocSectionStatus]) -> float:
        required_present = 0
        recommended_present = 0
        
        section_map = {s.section: s for s in sections}
        
        for section in self.REQUIRED_SECTIONS:
            if section_map.get(section, DocSectionStatus(section, DocStatus.MISSING, "", "")).status != DocStatus.MISSING:
                required_present += 1
        
        for section in self.RECOMMENDED_SECTIONS:
            if section_map.get(section, DocSectionStatus(section, DocStatus.MISSING, "", "")).status != DocStatus.MISSING:
                recommended_present += 1
        
        required_score = required_present / len(self.REQUIRED_SECTIONS) * 0.7
        recommended_score = recommended_present / len(self.RECOMMENDED_SECTIONS) * 0.3
        
        return required_score + recommended_score
    
    def _calculate_quality(self, content: str, sections: Dict[str, str]) -> float:
        score = 0.5
        
        code_blocks = content.count('```')
        score += min(code_blocks * 0.05, 0.2)
        
        links = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))
        score += min(links * 0.02, 0.1)
        
        word_count = len(content.split())
        if word_count > 500:
            score += 0.1
        if word_count > 1000:
            score += 0.1
        
        return min(score, 1.0)
    
    def _identify_missing_sections(self, sections: List[DocSectionStatus]) -> List[str]:
        return [
            s.section.value for s in sections 
            if s.status == DocStatus.MISSING and s.section in self.REQUIRED_SECTIONS
        ]
    
    def _identify_outdated_sections(self, sections: List[DocSectionStatus]) -> List[str]:
        return [
            s.section.value for s in sections 
            if s.status == DocStatus.OUTDATED
        ]
    
    def _generate_recommendations(self, sections: List[DocSectionStatus], 
                                   content: str) -> List[str]:
        recommendations = []
        
        for section_status in sections:
            if section_status.status == DocStatus.MISSING:
                if section_status.section in self.REQUIRED_SECTIONS:
                    recommendations.append(f"添加必需章节: {section_status.section.value}")
                elif section_status.section in self.RECOMMENDED_SECTIONS:
                    recommendations.append(f"建议添加章节: {section_status.section.value}")
            elif section_status.issues:
                for issue in section_status.issues:
                    recommendations.append(f"{section_status.section.value}: {issue}")
        
        if '```' not in content:
            recommendations.append("添加代码示例以提高文档质量")
        
        return recommendations
    
    def _determine_overall_status(self, sections: List[DocSectionStatus]) -> DocStatus:
        has_missing = any(
            s.status == DocStatus.MISSING and s.section in self.REQUIRED_SECTIONS
            for s in sections
        )
        
        if has_missing:
            return DocStatus.OUTDATED
        
        has_needs_update = any(s.status == DocStatus.NEEDS_UPDATE for s in sections)
        
        if has_needs_update:
            return DocStatus.NEEDS_UPDATE
        
        return DocStatus.UP_TO_DATE


class DocUpdater:
    """文档更新器"""
    
    def __init__(self, skill_path: str):
        self.skill_path = Path(skill_path)
        self.version_manager = VersionManager(skill_path)
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('DocUpdater')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def update_doc(self, update_type: UpdateType, 
                   changes: List[Dict[str, Any]],
                   sections_to_update: List[str] = None) -> DocUpdateRecord:
        skill_md = self.skill_path / "SKILL.md"
        
        old_version = str(self.version_manager.get_current_version())
        
        new_version = self.version_manager.bump_version(update_type)
        
        if skill_md.exists():
            content, encoding = safe_read_file(str(skill_md))
            if not content:
                content = self._create_default_doc()
        else:
            content = self._create_default_doc()
        
        updated_sections = []
        
        if sections_to_update:
            for section in sections_to_update:
                content = self._update_section(content, section, update_type, changes)
                updated_sections.append(section)
        
        content = self._update_version_in_doc(content, str(new_version))
        
        skill_md.write_text(content, encoding='utf-8')
        
        changelog_entry = ChangelogEntry(
            version=str(new_version),
            date=datetime.now().strftime('%Y-%m-%d'),
            changes=changes
        )
        self.version_manager.add_changelog_entry(changelog_entry)
        
        changes_summary = self._summarize_changes(changes)
        
        record = DocUpdateRecord(
            update_id=f"DOC-UPDATE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            skill_name=self.skill_path.name,
            timestamp=datetime.now().isoformat(),
            update_type=update_type,
            sections_updated=updated_sections,
            changes_summary=changes_summary,
            version_before=old_version,
            version_after=str(new_version),
            files_modified=[str(skill_md)]
        )
        
        self._save_update_record(record)
        
        self.logger.info(f"文档已更新: {old_version} -> {new_version}")
        
        return record
    
    def _create_default_doc(self) -> str:
        return f"""# {self.skill_path.name}

版本: 0.0.1

## 概述

本技能提供自动化功能支持。

## 功能特性

- 功能待补充

## 使用方法

```bash
python scripts/main.py
```

## 配置

无特殊配置要求。

## 变更日志

参见 [CHANGELOG.md](docs/CHANGELOG.md)
"""
    
    def _update_section(self, content: str, section: str, 
                        update_type: UpdateType, 
                        changes: List[Dict[str, Any]]) -> str:
        section_headers = {
            'overview': ['## 概述', '## Overview', '## 简介'],
            'features': ['## 功能特性', '## Features', '## 功能'],
            'usage': ['## 使用方法', '## Usage', '## 使用说明'],
            'api': ['## API', '## 接口', '## API参考'],
            'examples': ['## 示例', '## Examples', '## 使用示例'],
            'changelog': ['## 变更日志', '## Changelog', '## 更新历史'],
        }
        
        headers = section_headers.get(section, [f'## {section}'])
        
        for header in headers:
            if header in content:
                lines = content.split('\n')
                section_start = -1
                section_end = len(lines)
                
                for i, line in enumerate(lines):
                    if line.strip() == header.strip():
                        section_start = i
                    elif section_start >= 0 and line.startswith('##') and i > section_start:
                        section_end = i
                        break
                
                if section_start >= 0:
                    new_section_content = self._generate_section_content(section, changes)
                    
                    new_lines = lines[:section_start+1] + [''] + new_section_content + [''] + lines[section_end:]
                    return '\n'.join(new_lines)
        
        return content
    
    def _generate_section_content(self, section: str, changes: List[Dict[str, Any]]) -> List[str]:
        lines = []
        
        if section == 'features':
            for change in changes:
                if change.get('type') in ['feature_added', 'feature_modified']:
                    lines.append(f"- {change.get('description', '新功能')}")
        
        elif section == 'changelog':
            for change in changes:
                lines.append(f"- {change.get('description', '变更')}")
        
        return lines if lines else ['内容待更新']
    
    def _update_version_in_doc(self, content: str, version: str) -> str:
        patterns = [
            (r'版本[：:]\s*\d+\.\d+\.\d+', f'版本: {version}'),
            (r'Version[：:]\s*\d+\.\d+\.\d+', f'Version: {version}'),
            (r'v\d+\.\d+\.\d+', f'v{version}'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        return content
    
    def _summarize_changes(self, changes: List[Dict[str, Any]]) -> str:
        if not changes:
            return "无变更描述"
        
        summaries = [c.get('description', '变更') for c in changes[:3]]
        return '; '.join(summaries)
    
    def _save_update_record(self, record: DocUpdateRecord) -> None:
        records_path = self.skill_path / "docs" / "update_records"
        records_path.mkdir(parents=True, exist_ok=True)
        
        record_file = records_path / f"{record.update_id}.json"
        record_file.write_text(json.dumps(asdict(record), ensure_ascii=False, indent=2), 
                               encoding='utf-8')


class SkillDocIntegrator:
    """技能文档集成管理器"""
    
    def __init__(self, skills_root: str):
        self.skills_root = Path(skills_root)
        self.analyzer = DocAnalyzer()
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SkillDocIntegrator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def sync_all_versions(self) -> Dict[str, str]:
        results = {}
        
        for skill_dir in self.skills_root.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                try:
                    version_manager = VersionManager(str(skill_dir))
                    version = version_manager.get_current_version()
                    results[skill_dir.name] = str(version)
                except Exception as e:
                    self.logger.error(f"同步 {skill_dir.name} 版本失败: {e}")
                    results[skill_dir.name] = "error"
        
        return results
    
    def generate_summary_report(self) -> str:
        reports = []
        
        for skill_dir in sorted(self.skills_root.iterdir()):
            if skill_dir.is_dir():
                report = self.analyzer.analyze_skill_doc(str(skill_dir))
                reports.append(report)
        
        lines = [
            "# 技能文档状态报告",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"技能总数: {len(reports)}",
            "",
            "## 概览",
            "",
            "| 技能名称 | 版本 | 状态 | 完整度 | 质量分 |",
            "|----------|------|------|--------|--------|",
        ]
        
        for report in reports:
            status_emoji = {
                DocStatus.UP_TO_DATE: "✅",
                DocStatus.NEEDS_UPDATE: "⚠️",
                DocStatus.OUTDATED: "❌",
                DocStatus.MISSING: "❓"
            }.get(report.overall_status, "❓")
            
            lines.append(
                f"| {report.skill_name} | {report.version} | {status_emoji} | "
                f"{report.completeness_score:.0%} | {report.quality_score:.0%} |"
            )
        
        lines.append("")
        
        needs_attention = [r for r in reports if r.overall_status != DocStatus.UP_TO_DATE]
        
        if needs_attention:
            lines.extend([
                "## 需要关注的技能",
                ""
            ])
            
            for report in needs_attention:
                lines.append(f"### {report.skill_name}")
                lines.append("")
                
                if report.missing_sections:
                    lines.append(f"**缺失章节**: {', '.join(report.missing_sections)}")
                    lines.append("")
                
                if report.recommendations:
                    lines.append("**建议**:")
                    for rec in report.recommendations[:5]:
                        lines.append(f"- {rec}")
                    lines.append("")
        
        return '\n'.join(lines)
    
    def batch_update_docs(self, updates: Dict[str, Dict[str, Any]]) -> List[DocUpdateRecord]:
        records = []
        
        for skill_name, update_info in updates.items():
            skill_path = self.skills_root / skill_name
            
            if skill_path.exists():
                try:
                    updater = DocUpdater(str(skill_path))
                    record = updater.update_doc(
                        update_type=UpdateType(update_info.get('type', 'documentation')),
                        changes=update_info.get('changes', []),
                        sections_to_update=update_info.get('sections')
                    )
                    records.append(record)
                except Exception as e:
                    self.logger.error(f"更新 {skill_name} 文档失败: {e}")
        
        return records


def main():
    parser = argparse.ArgumentParser(description='技能文档智能更新脚本')
    
    parser.add_argument('--skill-path', '-s', help='技能路径')
    parser.add_argument('--skills-root', '-r', default='.', help='技能根目录')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    analyze_parser = subparsers.add_parser('analyze', help='分析技能文档')
    analyze_parser.add_argument('--output', '-o', help='输出报告路径')
    
    update_parser = subparsers.add_parser('update', help='更新技能文档')
    update_parser.add_argument('--type', choices=[t.value for t in UpdateType], 
                               required=True, help='更新类型')
    update_parser.add_argument('--changes', required=True, help='变更描述(JSON格式)')
    update_parser.add_argument('--sections', help='要更新的章节(逗号分隔)')
    
    version_parser = subparsers.add_parser('version', help='版本管理')
    version_parser.add_argument('--action', choices=['get', 'bump'], required=True, help='操作类型')
    version_parser.add_argument('--type', choices=['major', 'minor', 'patch'], 
                               default='patch', help='版本类型')
    
    sync_parser = subparsers.add_parser('sync', help='同步所有技能版本')
    
    report_parser = subparsers.add_parser('report', help='生成汇总报告')
    report_parser.add_argument('--output', '-o', help='输出文件路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'analyze':
        if not args.skill_path:
            print("错误: 需要指定 --skill-path")
            return
        
        analyzer = DocAnalyzer()
        report = analyzer.analyze_skill_doc(args.skill_path)
        
        output = json.dumps(asdict(report), ensure_ascii=False, indent=2)
        
        if args.output:
            Path(args.output).write_text(output, encoding='utf-8')
            print(f"报告已保存: {args.output}")
        else:
            print(output)
    
    elif args.command == 'update':
        if not args.skill_path:
            print("错误: 需要指定 --skill-path")
            return
        
        try:
            changes = json.loads(args.changes)
        except json.JSONDecodeError:
            changes = [{"type": args.type, "description": args.changes}]
        
        sections = args.sections.split(',') if args.sections else None
        
        updater = DocUpdater(args.skill_path)
        record = updater.update_doc(
            update_type=UpdateType(args.type),
            changes=changes,
            sections_to_update=sections
        )
        
        print(f"文档已更新: {record.version_before} -> {record.version_after}")
        print(f"更新ID: {record.update_id}")
    
    elif args.command == 'version':
        if not args.skill_path:
            print("错误: 需要指定 --skill-path")
            return
        
        vm = VersionManager(args.skill_path)
        
        if args.action == 'get':
            version = vm.get_current_version()
            print(f"当前版本: {version}")
        
        elif args.action == 'bump':
            current = vm.get_current_version()
            
            if args.type == 'major':
                new_version = current.bump_major()
            elif args.type == 'minor':
                new_version = current.bump_minor()
            else:
                new_version = current.bump_patch()
            
            vm.set_version(new_version)
            print(f"版本已更新: {current} -> {new_version}")
    
    elif args.command == 'sync':
        integrator = SkillDocIntegrator(args.skills_root)
        results = integrator.sync_all_versions()
        
        print("\n=== 版本同步结果 ===")
        for skill, version in results.items():
            print(f"{skill}: {version}")
    
    elif args.command == 'report':
        integrator = SkillDocIntegrator(args.skills_root)
        report = integrator.generate_summary_report()
        
        if args.output:
            Path(args.output).write_text(report, encoding='utf-8')
            print(f"报告已保存: {args.output}")
        else:
            print(report)


if __name__ == '__main__':
    main()
