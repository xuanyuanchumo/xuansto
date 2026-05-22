"""
技能文档更新器模块
实现 SKILL.md 自动更新、版本管理、变更日志生成和文档验证功能

功能:
- SKILL.md 自动更新（解析文档结构、更新内容、保持格式一致性）
- 版本信息自动更新（读取 version.json、自动升级版本号、生成变更摘要）
- 变更日志自动生成（收集变更、分类整理、追加到 CHANGELOG.md）
- 文档验证机制（格式验证、版本一致性、链接有效性）
- 回滚更新支持
"""

import hashlib
import json
import logging
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ChangeType(Enum):
    NEW = "新增"
    MODIFIED = "修改"
    DELETED = "删除"
    FIXED = "修复"
    REFACTOR = "重构"
    DOCS = "文档"
    PERFORMANCE = "性能"
    SECURITY = "安全"
    DEPENDENCY = "依赖"


class VersionBumpType(Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class ValidationLevel(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class DocSection:
    title: str
    content: str
    level: int
    children: List['DocSection'] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "level": self.level,
            "children": [c.to_dict() for c in self.children],
            "line_start": self.line_start,
            "line_end": self.line_end
        }
    
    def find_section(self, title_pattern: str) -> Optional['DocSection']:
        if re.search(title_pattern, self.title, re.IGNORECASE):
            return self
        for child in self.children:
            result = child.find_section(title_pattern)
            if result:
                return result
        return None


@dataclass
class VersionInfo:
    version: str
    release_date: datetime
    changes: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    author: str = ""
    
    def __post_init__(self):
        if isinstance(self.release_date, str):
            self.release_date = datetime.fromisoformat(self.release_date)
    
    @classmethod
    def parse(cls, version_str: str) -> Tuple[int, int, int]:
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version_str)
        if match:
            return int(match.group(1)), int(match.group(2)), int(match.group(3))
        return 0, 0, 1
    
    @classmethod
    def bump(cls, version_str: str, bump_type: VersionBumpType) -> str:
        major, minor, patch = cls.parse(version_str)
        if bump_type == VersionBumpType.MAJOR:
            return f"{major + 1}.0.0"
        elif bump_type == VersionBumpType.MINOR:
            return f"{major}.{minor + 1}.0"
        else:
            return f"{major}.{minor}.{patch + 1}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "release_date": self.release_date.isoformat(),
            "changes": self.changes,
            "breaking_changes": self.breaking_changes,
            "author": self.author
        }


@dataclass
class ChangeRecord:
    change_type: ChangeType
    scope: str
    description: str
    details: str = ""
    files_affected: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_type": self.change_type.value,
            "scope": self.scope,
            "description": self.description,
            "details": self.details,
            "files_affected": self.files_affected,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ValidationError:
    level: ValidationLevel
    message: str
    location: str
    suggestion: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "message": self.message,
            "location": self.location,
            "suggestion": self.suggestion
        }


@dataclass
class UpdateResult:
    success: bool
    updated_sections: List[str] = field(default_factory=list)
    new_version: str = ""
    changelog_entries: List[str] = field(default_factory=list)
    validation_errors: List[ValidationError] = field(default_factory=list)
    rollback_path: str = ""
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "updated_sections": self.updated_sections,
            "new_version": self.new_version,
            "changelog_entries": self.changelog_entries,
            "validation_errors": [e.to_dict() for e in self.validation_errors],
            "rollback_path": self.rollback_path,
            "message": self.message
        }


class SkillDocParser:
    """SKILL.md 文档解析器"""
    
    SECTION_PATTERNS = {
        "overview": r"(概述|Overview|简介|介绍)",
        "features": r"(功能|Features|特性|功能特性)",
        "usage": r"(使用|Usage|使用方法|使用说明)",
        "api": r"(API|接口|API参考)",
        "examples": r"(示例|Examples|使用示例|代码示例)",
        "changelog": r"(变更|Changelog|更新日志|版本历史)",
        "configuration": r"(配置|Configuration|配置说明|配置选项)",
        "troubleshooting": r"(故障|Troubleshooting|常见问题|FAQ)",
        "dependencies": r"(依赖|Dependencies|依赖项)",
        "performance": r"(性能|Performance|性能优化)",
        "architecture": r"(架构|Architecture|系统架构)",
        "workflow": r"(工作流程|Workflow|流程)",
    }
    
    def __init__(self):
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SkillDocParser')
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def parse(self, content: str) -> List[DocSection]:
        lines = content.split('\n')
        sections: List[DocSection] = []
        section_stack: List[DocSection] = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                content_lines: List[str] = []
                start_line = i + 1
                
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if re.match(r'^#{1,6}\s+', next_line):
                        break
                    content_lines.append(next_line)
                    j += 1
                
                section = DocSection(
                    title=title,
                    content='\n'.join(content_lines).strip(),
                    level=level,
                    line_start=start_line,
                    line_end=j
                )
                
                while section_stack and section_stack[-1].level >= level:
                    section_stack.pop()
                
                if section_stack:
                    section_stack[-1].children.append(section)
                else:
                    sections.append(section)
                
                section_stack.append(section)
                i = j
            else:
                i += 1
        
        return sections
    
    def extract_metadata(self, content: str) -> Dict[str, Any]:
        metadata = {}
        
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
        
        version_patterns = [
            r'版本[：:]\s*(\d+\.\d+\.\d+)',
            r'Version[：:]\s*(\d+\.\d+\.\d+)',
            r'v(\d+\.\d+\.\d+)',
        ]
        for pattern in version_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                metadata['version'] = match.group(1)
                break
        
        return metadata
    
    def get_section_content(self, sections: List[DocSection], section_name: str) -> Optional[str]:
        pattern = self.SECTION_PATTERNS.get(section_name.lower(), section_name)
        for section in sections:
            if re.search(pattern, section.title, re.IGNORECASE):
                return section.content
            for child in section.children:
                result = self.get_section_content([child], section_name)
                if result:
                    return result
        return None
    
    def update_section_content(
        self, 
        content: str, 
        section_name: str, 
        new_content: str,
        preserve_format: bool = True
    ) -> str:
        sections = self.parse(content)
        lines = content.split('\n')
        
        pattern = self.SECTION_PATTERNS.get(section_name.lower(), section_name)
        
        for section in sections:
            if re.search(pattern, section.title, re.IGNORECASE):
                header_line = f"{'#' * section.level} {section.title}"
                
                for i, line in enumerate(lines):
                    if line.strip() == header_line:
                        end_idx = section.line_end
                        new_lines = lines[:i+1] + [new_content] + lines[end_idx:]
                        return '\n'.join(new_lines)
        
        header = f"\n\n## {section_name.title()}\n\n"
        return content + header + new_content + "\n"


class VersionManager:
    """版本管理器"""
    
    def __init__(self, skill_path: Path):
        self.skill_path = skill_path
        self.version_file = skill_path / "version.json"
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('VersionManager')
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def get_version_info(self) -> VersionInfo:
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return VersionInfo(
                    version=data.get('version', '0.0.1'),
                    release_date=datetime.fromisoformat(data.get('release_date', datetime.now().isoformat())),
                    changes=data.get('changes', []),
                    breaking_changes=data.get('breaking_changes', []),
                    author=data.get('author', '')
                )
            except Exception as e:
                self.logger.error(f"读取版本文件失败: {e}")
        
        return VersionInfo(
            version='0.0.1',
            release_date=datetime.now()
        )
    
    def update_version(
        self, 
        bump_type: VersionBumpType, 
        changes: List[str],
        breaking_changes: List[str] = None,
        author: str = ""
    ) -> VersionInfo:
        current = self.get_version_info()
        new_version_str = VersionInfo.bump(current.version, bump_type)
        
        new_version = VersionInfo(
            version=new_version_str,
            release_date=datetime.now(),
            changes=changes,
            breaking_changes=breaking_changes or [],
            author=author
        )
        
        self._save_version(new_version)
        self._append_version_history(current, new_version)
        
        self.logger.info(f"版本已更新: {current.version} -> {new_version_str}")
        return new_version
    
    def _save_version(self, version_info: VersionInfo) -> None:
        self.version_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = version_info.to_dict()
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _append_version_history(self, old_version: VersionInfo, new_version: VersionInfo) -> None:
        history_file = self.skill_path / "version_history.json"
        
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception:
                history = []
        
        history.append({
            "from_version": old_version.version,
            "to_version": new_version.version,
            "updated_at": datetime.now().isoformat(),
            "changes": new_version.changes,
            "breaking_changes": new_version.breaking_changes
        })
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def determine_bump_type(self, changes: List[ChangeRecord]) -> VersionBumpType:
        has_breaking = any(c.change_type in [ChangeType.DELETED] for c in changes)
        has_new_feature = any(c.change_type == ChangeType.NEW for c in changes)
        
        if has_breaking:
            return VersionBumpType.MAJOR
        elif has_new_feature:
            return VersionBumpType.MINOR
        else:
            return VersionBumpType.PATCH


class ChangelogGenerator:
    """变更日志生成器"""
    
    TYPE_ORDER = [
        ChangeType.NEW,
        ChangeType.MODIFIED,
        ChangeType.DELETED,
        ChangeType.FIXED,
        ChangeType.REFACTOR,
        ChangeType.PERFORMANCE,
        ChangeType.SECURITY,
        ChangeType.DEPENDENCY,
        ChangeType.DOCS,
    ]
    
    TYPE_LABELS = {
        ChangeType.NEW: "✨ 新增功能",
        ChangeType.MODIFIED: "🔧 功能变更",
        ChangeType.DELETED: "🗑️ 移除功能",
        ChangeType.FIXED: "🐛 问题修复",
        ChangeType.REFACTOR: "♻️ 代码重构",
        ChangeType.PERFORMANCE: "⚡ 性能优化",
        ChangeType.SECURITY: "🔒 安全更新",
        ChangeType.DEPENDENCY: "📦 依赖更新",
        ChangeType.DOCS: "📝 文档更新",
    }
    
    def __init__(self, skill_path: Path):
        self.skill_path = skill_path
        self.changelog_file = skill_path / "CHANGELOG.md"
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('ChangelogGenerator')
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def generate_entry(
        self, 
        version: str, 
        changes: List[ChangeRecord],
        breaking_changes: List[str] = None
    ) -> str:
        lines = [
            f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}",
            ""
        ]
        
        if breaking_changes:
            lines.extend([
                "### ⚠️ 破坏性变更",
                ""
            ])
            for bc in breaking_changes:
                lines.append(f"- {bc}")
            lines.append("")
        
        changes_by_type: Dict[ChangeType, List[ChangeRecord]] = {}
        for change in changes:
            if change.change_type not in changes_by_type:
                changes_by_type[change.change_type] = []
            changes_by_type[change.change_type].append(change)
        
        for change_type in self.TYPE_ORDER:
            if change_type in changes_by_type:
                type_changes = changes_by_type[change_type]
                label = self.TYPE_LABELS.get(change_type, "其他")
                
                lines.append(f"### {label}")
                lines.append("")
                
                for change in type_changes:
                    entry = f"- **{change.scope}**: {change.description}"
                    if change.details:
                        entry += f"\n  - {change.details}"
                    lines.append(entry)
                
                lines.append("")
        
        lines.append("---")
        lines.append("")
        
        return '\n'.join(lines)
    
    def append_to_changelog(self, entry: str) -> None:
        self.changelog_file.parent.mkdir(parents=True, exist_ok=True)
        
        if self.changelog_file.exists():
            content = self.changelog_file.read_text(encoding='utf-8')
            
            version_match = re.search(r'##\s*\[([^\]]+)\]', entry)
            if version_match:
                version = version_match.group(1)
                if f"[{version}]" in content:
                    self.logger.warning(f"版本 {version} 已存在于变更日志中")
                    return
            
            lines = content.split('\n')
            insert_pos = 0
            
            for i, line in enumerate(lines):
                if line.startswith('## '):
                    insert_pos = i
                    break
            
            lines.insert(insert_pos, entry)
            new_content = '\n'.join(lines)
        else:
            header = "# 变更日志\n\n本文档记录技能的所有重要变更。\n\n"
            new_content = header + entry
        
        self.changelog_file.write_text(new_content, encoding='utf-8')
        self.logger.info("变更日志已更新")
    
    def get_recent_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.changelog_file.exists():
            return []
        
        content = self.changelog_file.read_text(encoding='utf-8')
        entries = []
        
        pattern = r'##\s*\[([^\]]+)\]\s*-\s*(\d{4}-\d{2}-\d{2})'
        matches = re.findall(pattern, content)
        
        for version, date in matches[:limit]:
            entries.append({
                "version": version,
                "date": date
            })
        
        return entries


class DocValidator:
    """文档验证器"""
    
    REQUIRED_SECTIONS = ["overview", "features", "usage"]
    RECOMMENDED_SECTIONS = ["api", "examples", "configuration"]
    
    def __init__(self):
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('DocValidator')
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def validate(
        self, 
        content: str, 
        version_info: Optional[VersionInfo] = None,
        check_links: bool = True
    ) -> List[ValidationError]:
        errors: List[ValidationError] = []
        
        errors.extend(self._validate_structure(content))
        errors.extend(self._validate_sections(content))
        errors.extend(self._validate_format(content))
        
        if version_info:
            errors.extend(self._validate_version_consistency(content, version_info))
        
        if check_links:
            errors.extend(self._validate_links(content))
        
        return errors
    
    def _validate_structure(self, content: str) -> List[ValidationError]:
        errors = []
        
        if not content.strip():
            errors.append(ValidationError(
                level=ValidationLevel.ERROR,
                message="文档内容为空",
                location="整个文档",
                suggestion="添加文档内容"
            ))
            return errors
        
        if not re.match(r'^#\s+', content):
            errors.append(ValidationError(
                level=ValidationLevel.ERROR,
                message="文档缺少一级标题",
                location="文档开头",
                suggestion="在文档开头添加 # 技能名称"
            ))
        
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not frontmatter_match:
            errors.append(ValidationError(
                level=ValidationLevel.WARNING,
                message="文档缺少 YAML frontmatter",
                location="文档开头",
                suggestion="添加包含 name 和 description 的 frontmatter"
            ))
        
        return errors
    
    def _validate_sections(self, content: str) -> List[ValidationError]:
        errors = []
        parser = SkillDocParser()
        sections = parser.parse(content)
        
        section_titles = [s.title.lower() for s in sections]
        for child in sections:
            section_titles.extend([c.title.lower() for c in child.children])
        
        for required in self.REQUIRED_SECTIONS:
            found = False
            pattern = SkillDocParser.SECTION_PATTERNS.get(required, required)
            for title in section_titles:
                if re.search(pattern, title, re.IGNORECASE):
                    found = True
                    break
            
            if not found:
                errors.append(ValidationError(
                    level=ValidationLevel.ERROR,
                    message=f"缺少必需章节: {required}",
                    location="文档结构",
                    suggestion=f"添加 ## {required.title()} 章节"
                ))
        
        for recommended in self.RECOMMENDED_SECTIONS:
            found = False
            pattern = SkillDocParser.SECTION_PATTERNS.get(recommended, recommended)
            for title in section_titles:
                if re.search(pattern, title, re.IGNORECASE):
                    found = True
                    break
            
            if not found:
                errors.append(ValidationError(
                    level=ValidationLevel.WARNING,
                    message=f"建议添加章节: {recommended}",
                    location="文档结构",
                    suggestion=f"考虑添加 ## {recommended.title()} 章节"
                ))
        
        return errors
    
    def _validate_format(self, content: str) -> List[ValidationError]:
        errors = []
        
        code_blocks = re.findall(r'```', content)
        if len(code_blocks) % 2 != 0:
            errors.append(ValidationError(
                level=ValidationLevel.ERROR,
                message="代码块未正确闭合",
                location="代码块",
                suggestion="检查 ``` 标记是否成对出现"
            ))
        
        tables = re.findall(r'\|.*\|', content)
        if tables:
            separator_found = False
            for line in content.split('\n'):
                if re.match(r'^\|[\s\-:|]+\|$', line.strip()):
                    separator_found = True
                    break
            
            if not separator_found:
                errors.append(ValidationError(
                    level=ValidationLevel.WARNING,
                    message="表格可能缺少分隔行",
                    location="表格",
                    suggestion="确保表格有 |---|---| 格式的分隔行"
                ))
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if re.search(r'[^\x00-\x7F]', line) and re.search(r'[a-zA-Z]', line):
                mixed_ratio = len(re.findall(r'[^\x00-\x7F]', line)) / max(len(line), 1)
                if mixed_ratio > 0.3 and mixed_ratio < 0.7:
                    errors.append(ValidationError(
                        level=ValidationLevel.INFO,
                        message=f"第 {i+1} 行中英文混排较多",
                        location=f"第 {i+1} 行",
                        suggestion="考虑在中英文之间添加空格"
                    ))
        
        return errors
    
    def _validate_version_consistency(
        self, 
        content: str, 
        version_info: VersionInfo
    ) -> List[ValidationError]:
        errors = []
        
        parser = SkillDocParser()
        metadata = parser.extract_metadata(content)
        
        doc_version = metadata.get('version', '')
        if doc_version and doc_version != version_info.version:
            errors.append(ValidationError(
                level=ValidationLevel.ERROR,
                message=f"版本号不一致: 文档中为 {doc_version}，version.json 中为 {version_info.version}",
                location="版本信息",
                suggestion="更新文档中的版本号以保持一致"
            ))
        
        return errors
    
    def _validate_links(self, content: str) -> List[ValidationError]:
        errors = []
        
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        
        for text, url in links:
            if url.startswith('http'):
                continue
            
            if url.startswith('#'):
                anchor = url[1:]
                if anchor not in content.lower():
                    errors.append(ValidationError(
                        level=ValidationLevel.WARNING,
                        message=f"锚点链接可能无效: {url}",
                        location=f"链接 [{text}]",
                        suggestion="检查锚点是否存在"
                    ))
            elif not url.startswith('file:///'):
                errors.append(ValidationError(
                    level=ValidationLevel.INFO,
                    message=f"相对链接: {url}",
                    location=f"链接 [{text}]",
                    suggestion="确认链接目标存在"
                ))
        
        return errors
    
    def generate_validation_report(self, errors: List[ValidationError]) -> str:
        lines = [
            "# 文档验证报告",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"问题总数: {len(errors)}",
            ""
        ]
        
        by_level: Dict[ValidationLevel, List[ValidationError]] = {}
        for error in errors:
            if error.level not in by_level:
                by_level[error.level] = []
            by_level[error.level].append(error)
        
        for level in [ValidationLevel.ERROR, ValidationLevel.WARNING, ValidationLevel.INFO]:
            if level in by_level:
                level_errors = by_level[level]
                lines.append(f"## {level.value.upper()} ({len(level_errors)})")
                lines.append("")
                
                for error in level_errors:
                    lines.append(f"- **{error.location}**: {error.message}")
                    if error.suggestion:
                        lines.append(f"  - 建议: {error.suggestion}")
                lines.append("")
        
        return '\n'.join(lines)


class RollbackManager:
    """回滚管理器"""
    
    def __init__(self, skill_path: Path):
        self.skill_path = skill_path
        self.backup_dir = skill_path / ".doc_backups"
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('RollbackManager')
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def create_backup(self, files: List[Path]) -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / timestamp
        backup_path.mkdir(parents=True, exist_ok=True)
        
        for file_path in files:
            if file_path.exists():
                relative_path = file_path.relative_to(self.skill_path)
                dest_path = backup_path / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest_path)
        
        manifest = {
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat(),
            "files": [str(f.relative_to(self.skill_path)) for f in files if f.exists()]
        }
        
        manifest_path = backup_path / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"备份已创建: {backup_path}")
        return str(backup_path)
    
    def rollback(self, backup_path: str) -> bool:
        backup_dir = Path(backup_path)
        if not backup_dir.exists():
            self.logger.error(f"备份目录不存在: {backup_path}")
            return False
        
        manifest_path = backup_dir / "manifest.json"
        if not manifest_path.exists():
            self.logger.error("备份清单文件不存在")
            return False
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            for relative_file in manifest.get('files', []):
                src = backup_dir / relative_file
                dest = self.skill_path / relative_file
                if src.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
            
            self.logger.info(f"回滚成功: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"回滚失败: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        backups = []
        
        if not self.backup_dir.exists():
            return backups
        
        for backup_dir in sorted(self.backup_dir.iterdir(), reverse=True):
            if backup_dir.is_dir():
                manifest_path = backup_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                        backups.append({
                            "path": str(backup_dir),
                            "timestamp": manifest.get('timestamp', ''),
                            "created_at": manifest.get('created_at', ''),
                            "files": manifest.get('files', [])
                        })
                    except Exception:
                        pass
        
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        backups = self.list_backups()
        removed = 0
        
        for backup in backups[keep_count:]:
            backup_path = Path(backup['path'])
            if backup_path.exists():
                shutil.rmtree(backup_path)
                removed += 1
        
        if removed > 0:
            self.logger.info(f"已清理 {removed} 个旧备份")
        
        return removed


class SkillDocUpdater:
    """技能文档更新器主类"""
    
    def __init__(self, skill_path: str):
        self.skill_path = Path(skill_path)
        self.skill_md = self.skill_path / "SKILL.md"
        
        self.parser = SkillDocParser()
        self.version_manager = VersionManager(self.skill_path)
        self.changelog_generator = ChangelogGenerator(self.skill_path)
        self.validator = DocValidator()
        self.rollback_manager = RollbackManager(self.skill_path)
        
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SkillDocUpdater')
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def update(
        self,
        changes: List[ChangeRecord],
        sections_to_update: Optional[Dict[str, str]] = None,
        breaking_changes: List[str] = None,
        author: str = "",
        validate: bool = True,
        create_backup: bool = True
    ) -> UpdateResult:
        files_to_backup = [self.skill_md]
        if self.version_manager.version_file.exists():
            files_to_backup.append(self.version_manager.version_file)
        if self.changelog_generator.changelog_file.exists():
            files_to_backup.append(self.changelog_generator.changelog_file)
        
        backup_path = ""
        if create_backup:
            backup_path = self.rollback_manager.create_backup(files_to_backup)
        
        try:
            content = ""
            if self.skill_md.exists():
                content = self.skill_md.read_text(encoding='utf-8')
            else:
                content = self._create_default_doc()
            
            updated_sections: List[str] = []
            
            if sections_to_update:
                for section_name, new_content in sections_to_update.items():
                    content = self.parser.update_section_content(
                        content, section_name, new_content
                    )
                    updated_sections.append(section_name)
            
            bump_type = self.version_manager.determine_bump_type(changes)
            change_descriptions = [c.description for c in changes]
            
            new_version = self.version_manager.update_version(
                bump_type=bump_type,
                changes=change_descriptions,
                breaking_changes=breaking_changes,
                author=author
            )
            
            content = self._update_version_in_doc(content, new_version.version)
            
            changelog_entry = self.changelog_generator.generate_entry(
                version=new_version.version,
                changes=changes,
                breaking_changes=breaking_changes
            )
            self.changelog_generator.append_to_changelog(changelog_entry)
            
            self.skill_md.write_text(content, encoding='utf-8')
            
            validation_errors: List[ValidationError] = []
            if validate:
                validation_errors = self.validator.validate(
                    content, new_version, check_links=False
                )
            
            self.rollback_manager.cleanup_old_backups()
            
            return UpdateResult(
                success=True,
                updated_sections=updated_sections,
                new_version=new_version.version,
                changelog_entries=[changelog_entry],
                validation_errors=validation_errors,
                rollback_path=backup_path,
                message=f"文档更新成功: 版本 {new_version.version}"
            )
            
        except Exception as e:
            self.logger.error(f"文档更新失败: {e}")
            
            if backup_path:
                self.rollback_manager.rollback(backup_path)
            
            return UpdateResult(
                success=False,
                rollback_path=backup_path,
                message=f"文档更新失败: {str(e)}"
            )
    
    def rollback(self, backup_path: str) -> bool:
        return self.rollback_manager.rollback(backup_path)
    
    def validate_current_doc(self, check_links: bool = True) -> List[ValidationError]:
        if not self.skill_md.exists():
            return [ValidationError(
                level=ValidationLevel.ERROR,
                message="SKILL.md 文件不存在",
                location="文件系统",
                suggestion="创建 SKILL.md 文件"
            )]
        
        content = self.skill_md.read_text(encoding='utf-8')
        version_info = self.version_manager.get_version_info()
        
        return self.validator.validate(content, version_info, check_links)
    
    def get_doc_status(self) -> Dict[str, Any]:
        status = {
            "skill_path": str(self.skill_path),
            "skill_md_exists": self.skill_md.exists(),
            "version": None,
            "sections": [],
            "validation_errors": [],
            "last_backup": None
        }
        
        if self.skill_md.exists():
            content = self.skill_md.read_text(encoding='utf-8')
            sections = self.parser.parse(content)
            status["sections"] = [s.to_dict() for s in sections]
            
            metadata = self.parser.extract_metadata(content)
            status["version"] = metadata.get('version', 'unknown')
        
        version_info = self.version_manager.get_version_info()
        status["version_info"] = version_info.to_dict()
        
        backups = self.rollback_manager.list_backups()
        if backups:
            status["last_backup"] = backups[0]
        
        return status
    
    def _create_default_doc(self) -> str:
        skill_name = self.skill_path.name
        return f"""---
name: {skill_name}
description: 技能描述
---

# {skill_name}

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

参见 [CHANGELOG.md](CHANGELOG.md)
"""
    
    def _update_version_in_doc(self, content: str, version: str) -> str:
        patterns = [
            (r'版本[：:]\s*\d+\.\d+\.\d+', f'版本: {version}'),
            (r'Version[：:]\s*\d+\.\d+\.\d+', f'Version: {version}'),
            (r'v\d+\.\d+\.\d+', f'v{version}'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        return content


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='技能文档更新器')
    parser.add_argument('--skill-path', '-s', required=True, help='技能路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    update_parser = subparsers.add_parser('update', help='更新文档')
    update_parser.add_argument('--changes', required=True, help='变更记录(JSON格式)')
    update_parser.add_argument('--sections', help='要更新的章节(JSON格式)')
    update_parser.add_argument('--breaking', help='破坏性变更(JSON数组)')
    update_parser.add_argument('--author', default='', help='作者')
    update_parser.add_argument('--no-validate', action='store_true', help='跳过验证')
    update_parser.add_argument('--no-backup', action='store_true', help='跳过备份')
    
    validate_parser = subparsers.add_parser('validate', help='验证文档')
    validate_parser.add_argument('--check-links', action='store_true', help='检查链接')
    
    status_parser = subparsers.add_parser('status', help='获取文档状态')
    
    rollback_parser = subparsers.add_parser('rollback', help='回滚文档')
    rollback_parser.add_argument('--backup-path', required=True, help='备份路径')
    
    backups_parser = subparsers.add_parser('backups', help='列出备份')
    
    args = parser.parse_args()
    
    updater = SkillDocUpdater(args.skill_path)
    
    if args.command == 'update':
        changes = json.loads(args.changes)
        change_records = [
            ChangeRecord(
                change_type=ChangeType(c.get('type', 'modified')),
                scope=c.get('scope', ''),
                description=c.get('description', ''),
                details=c.get('details', ''),
                files_affected=c.get('files_affected', [])
            )
            for c in changes
        ]
        
        sections = json.loads(args.sections) if args.sections else None
        breaking = json.loads(args.breaking) if args.breaking else None
        
        result = updater.update(
            changes=change_records,
            sections_to_update=sections,
            breaking_changes=breaking,
            author=args.author,
            validate=not args.no_validate,
            create_backup=not args.no_backup
        )
        
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    
    elif args.command == 'validate':
        errors = updater.validate_current_doc(check_links=args.check_links)
        print(json.dumps([e.to_dict() for e in errors], indent=2, ensure_ascii=False))
    
    elif args.command == 'status':
        status = updater.get_doc_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    elif args.command == 'rollback':
        success = updater.rollback(args.backup_path)
        print(json.dumps({"success": success}, indent=2))
    
    elif args.command == 'backups':
        backups = updater.rollback_manager.list_backups()
        print(json.dumps(backups, indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
