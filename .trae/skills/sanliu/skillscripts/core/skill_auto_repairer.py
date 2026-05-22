#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能自动修复系统 - Skill Auto Repairer

功能：
1. 文档修复策略：修复缺失章节、格式错误、路径引用错误
2. 脚本修复策略：修复导入错误、语法错误、路径引用
3. 配置修复策略：修复配置文件格式、缺失配置项、配置冲突
4. 修复效果验证：验证修复后的文件可用性，生成修复报告

集成：
- 与 skill_health_assessor.py 集成，基于健康度评估结果触发修复
- 与 skill_doc_path_validator.py 集成，修复路径问题
- 与 enhanced_path_config_manager.py 集成，使用动态路径

命令行接口：
  python skillscripts/core/skill_auto_repairer.py --auto          # 自动修复所有问题
  python skillscripts/core/skill_auto_repairer.py --fix-docs      # 修复文档问题
  python skillscripts/core/skill_auto_repairer.py --fix-scripts   # 修复脚本问题
  python skillscripts/core/skill_auto_repairer.py --fix-config    # 修复配置问题
  python skillscripts/core/skill_auto_repairer.py --dry-run       # 预览修复（不实际修改）
"""

import argparse
import ast
import json
import logging
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

PROJECT_ROOT = get_path_config().SKILL_ROOT
SKILLSCRIPTS_DIR = get_path_config().SCRIPTS_DIR
CORE_DIR = get_path_config().SCRIPTS_DIR / "core"

sys.path.insert(0, str(SKILLSCRIPTS_DIR / "utils"))
sys.path.insert(0, str(CORE_DIR))

try:
    from skill_health_assessor import (
        SkillHealthAssessor, HealthAssessmentReport, AssessmentCategory,
        HealthLevel, CategoryResult, AssessmentItem
    )
except ImportError:
    pass

try:
    from skill_doc_path_validator import (
        SkillDocPathValidator, PathStatus, FixAction
    )
except ImportError:
    pass

try:
    from enhanced_path_config_manager import (
        create_path_manager, PathKey, EnhancedSkillPathManager
    )
except ImportError:
    pass


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RepairCategory(Enum):
    """修复类别枚举"""
    DOCUMENTATION = "documentation"
    SCRIPTS = "scripts"
    CONFIGURATION = "configuration"
    PATH_STRUCTURE = "path_structure"


class RepairStatus(Enum):
    """修复状态枚举"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"
    DRY_RUN = "dry_run"


class RepairAction(Enum):
    """修复动作枚举"""
    CREATE_FILE = "create_file"
    FIX_FORMAT = "fix_format"
    FIX_PATH = "fix_path"
    FIX_IMPORT = "fix_import"
    FIX_SYNTAX = "fix_syntax"
    ADD_SECTION = "add_section"
    ADD_CONFIG = "add_config"
    CREATE_DIR = "create_dir"
    BACKUP = "backup"
    RESTORE = "restore"


@dataclass
class RepairItem:
    """修复项数据类"""
    category: RepairCategory
    action: RepairAction
    target: str
    description: str
    status: RepairStatus
    original_content: Optional[str] = None
    fixed_content: Optional[str] = None
    error_message: Optional[str] = None
    backup_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "action": self.action.value,
            "target": self.target,
            "description": self.description,
            "status": self.status.value,
            "original_content": self.original_content[:500] if self.original_content else None,
            "fixed_content": self.fixed_content[:500] if self.fixed_content else None,
            "error_message": self.error_message,
            "backup_path": self.backup_path
        }


@dataclass
class RepairResult:
    """修复结果数据类"""
    category: RepairCategory
    total_issues: int
    fixed_issues: int
    failed_issues: int
    skipped_issues: int
    items: List[RepairItem] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        if self.total_issues == 0:
            return 100.0
        return (self.fixed_issues / self.total_issues) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "total_issues": self.total_issues,
            "fixed_issues": self.fixed_issues,
            "failed_issues": self.failed_issues,
            "skipped_issues": self.skipped_issues,
            "success_rate": round(self.success_rate, 2),
            "items": [item.to_dict() for item in self.items]
        }


@dataclass
class RepairReport:
    """修复报告数据类"""
    timestamp: str
    skill_root: str
    dry_run: bool
    total_issues: int
    total_fixed: int
    total_failed: int
    total_skipped: int
    overall_success_rate: float
    duration_ms: float
    category_results: List[RepairResult] = field(default_factory=list)
    health_before: Optional[Dict[str, Any]] = None
    health_after: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "skill_root": self.skill_root,
            "dry_run": self.dry_run,
            "total_issues": self.total_issues,
            "total_fixed": self.total_fixed,
            "total_failed": self.total_failed,
            "total_skipped": self.total_skipped,
            "overall_success_rate": round(self.overall_success_rate, 2),
            "duration_ms": round(self.duration_ms, 2),
            "category_results": [r.to_dict() for r in self.category_results],
            "health_before": self.health_before,
            "health_after": self.health_after
        }


class DocumentationRepairer:
    """文档修复器"""
    
    REQUIRED_SKILL_MD_SECTIONS = [
        ("触发条件", "## 触发条件\n\n描述技能的触发条件和入口。\n\n"),
        ("快速开始", "## 快速开始\n\n提供快速入门指南。\n\n"),
        ("工作流程", "## 工作流程\n\n描述技能的工作流程和执行步骤。\n\n"),
        ("核心功能", "## 核心功能\n\n列出技能的核心功能。\n\n")
    ]
    
    OPTIONAL_SECTIONS = [
        ("API", "## API\n\nAPI 接口说明。\n\n"),
        ("配置", "## 配置\n\n配置选项说明。\n\n"),
        ("示例", "## 示例\n\n使用示例。\n\n"),
        ("故障排除", "## 故障排除\n\n常见问题及解决方案。\n\n"),
        ("更新日志", "## 更新日志\n\n版本更新记录。\n\n")
    ]
    
    DEFAULT_FRONTMATTER = '''---
name: "{name}"
description: "{description}"
version: "1.0.0"
---

'''
    
    def __init__(self, skill_root: Path, path_manager=None):
        self.skill_root = skill_root
        self.path_manager = path_manager
        self.skill_md_path = skill_root / "SKILL.md"
        self.subskills_dir = skill_root / "subskills"
        self.backup_dir = skill_root / "backups" / "docs"
    
    def repair(self, dry_run: bool = True, backup: bool = True) -> RepairResult:
        """执行文档修复"""
        items = []
        total_issues = 0
        fixed_issues = 0
        failed_issues = 0
        skipped_issues = 0
        
        skill_md_result = self._repair_skill_md(dry_run, backup)
        items.extend(skill_md_result["items"])
        total_issues += skill_md_result["total"]
        fixed_issues += skill_md_result["fixed"]
        failed_issues += skill_md_result["failed"]
        skipped_issues += skill_md_result["skipped"]
        
        subskills_result = self._repair_subskills(dry_run, backup)
        items.extend(subskills_result["items"])
        total_issues += subskills_result["total"]
        fixed_issues += subskills_result["fixed"]
        failed_issues += subskills_result["failed"]
        skipped_issues += subskills_result["skipped"]
        
        paths_result = self._repair_doc_paths(dry_run, backup)
        items.extend(paths_result["items"])
        total_issues += paths_result["total"]
        fixed_issues += paths_result["fixed"]
        failed_issues += paths_result["failed"]
        skipped_issues += paths_result["skipped"]
        
        return RepairResult(
            category=RepairCategory.DOCUMENTATION,
            total_issues=total_issues,
            fixed_issues=fixed_issues,
            failed_issues=failed_issues,
            skipped_issues=skipped_issues,
            items=items
        )
    
    def _repair_skill_md(self, dry_run: bool, backup: bool) -> Dict[str, Any]:
        """修复 SKILL.md 主文档"""
        result = {"items": [], "total": 0, "fixed": 0, "failed": 0, "skipped": 0}
        
        if not self.skill_md_path.exists():
            result["total"] = 1
            item = self._create_skill_md(dry_run)
            result["items"].append(item)
            if item.status == RepairStatus.SUCCESS or item.status == RepairStatus.DRY_RUN:
                result["fixed"] += 1
            else:
                result["failed"] += 1
            return result
        
        try:
            content = self.skill_md_path.read_text(encoding='utf-8')
        except Exception as e:
            result["total"] = 1
            result["items"].append(RepairItem(
                category=RepairCategory.DOCUMENTATION,
                action=RepairAction.FIX_FORMAT,
                target=str(self.skill_md_path),
                description="读取 SKILL.md 失败",
                status=RepairStatus.FAILED,
                error_message=str(e)
            ))
            result["failed"] += 1
            return result
        
        issues_found = 0
        issues_fixed = 0
        
        frontmatter_result = self._fix_frontmatter(content, dry_run, backup)
        if frontmatter_result["has_issue"]:
            issues_found += 1
            result["items"].append(frontmatter_result["item"])
            if frontmatter_result["item"].status in (RepairStatus.SUCCESS, RepairStatus.DRY_RUN):
                issues_fixed += 1
                content = frontmatter_result.get("new_content", content)
        
        for section_name, section_content in self.REQUIRED_SKILL_MD_SECTIONS:
            if section_name not in content:
                issues_found += 1
                item = self._add_section(self.skill_md_path, section_name, section_content, dry_run, backup)
                result["items"].append(item)
                if item.status in (RepairStatus.SUCCESS, RepairStatus.DRY_RUN):
                    issues_fixed += 1
        
        result["total"] = issues_found
        result["fixed"] = issues_fixed
        result["failed"] = issues_found - issues_fixed
        
        return result
    
    def _create_skill_md(self, dry_run: bool) -> RepairItem:
        """创建 SKILL.md 文件"""
        default_content = '''---
name: "Sanliu Skill"
description: "A powerful skill system for automated development"
version: "1.0.0"
---

# Sanliu Skill

## 触发条件

描述技能的触发条件和入口。

## 快速开始

提供快速入门指南。

## 工作流程

描述技能的工作流程和执行步骤。

## 核心功能

列出技能的核心功能。

## 配置

配置选项说明。

## 示例

使用示例。

## 故障排除

常见问题及解决方案。

## 更新日志

版本更新记录。
'''
        
        if dry_run:
            return RepairItem(
                category=RepairCategory.DOCUMENTATION,
                action=RepairAction.CREATE_FILE,
                target=str(self.skill_md_path),
                description="创建 SKILL.md 主文档",
                status=RepairStatus.DRY_RUN,
                fixed_content=default_content
            )
        
        try:
            self.skill_md_path.parent.mkdir(parents=True, exist_ok=True)
            self.skill_md_path.write_text(default_content, encoding='utf-8')
            return RepairItem(
                category=RepairCategory.DOCUMENTATION,
                action=RepairAction.CREATE_FILE,
                target=str(self.skill_md_path),
                description="创建 SKILL.md 主文档",
                status=RepairStatus.SUCCESS,
                fixed_content=default_content
            )
        except Exception as e:
            return RepairItem(
                category=RepairCategory.DOCUMENTATION,
                action=RepairAction.CREATE_FILE,
                target=str(self.skill_md_path),
                description="创建 SKILL.md 主文档",
                status=RepairStatus.FAILED,
                error_message=str(e)
            )
    
    def _fix_frontmatter(self, content: str, dry_run: bool, backup: bool) -> Dict[str, Any]:
        """修复 frontmatter"""
        result = {"has_issue": False, "item": None, "new_content": content}
        
        if not content.strip().startswith('---'):
            result["has_issue"] = True
            new_content = self.DEFAULT_FRONTMATTER.format(
                name="Skill",
                description="Skill description"
            ) + content
            
            if dry_run:
                result["item"] = RepairItem(
                    category=RepairCategory.DOCUMENTATION,
                    action=RepairAction.FIX_FORMAT,
                    target=str(self.skill_md_path),
                    description="添加 YAML frontmatter",
                    status=RepairStatus.DRY_RUN,
                    original_content=content[:200],
                    fixed_content=new_content[:200]
                )
            else:
                if backup:
                    backup_path = self._create_backup(self.skill_md_path)
                try:
                    self.skill_md_path.write_text(new_content, encoding='utf-8')
                    result["item"] = RepairItem(
                        category=RepairCategory.DOCUMENTATION,
                        action=RepairAction.FIX_FORMAT,
                        target=str(self.skill_md_path),
                        description="添加 YAML frontmatter",
                        status=RepairStatus.SUCCESS,
                        original_content=content[:200],
                        fixed_content=new_content[:200]
                    )
                    result["new_content"] = new_content
                except Exception as e:
                    result["item"] = RepairItem(
                        category=RepairCategory.DOCUMENTATION,
                        action=RepairAction.FIX_FORMAT,
                        target=str(self.skill_md_path),
                        description="添加 YAML frontmatter",
                        status=RepairStatus.FAILED,
                        error_message=str(e)
                    )
        
        return result
    
    def _add_section(
        self, 
        file_path: Path, 
        section_name: str, 
        section_content: str,
        dry_run: bool,
        backup: bool
    ) -> RepairItem:
        """添加缺失章节"""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            return RepairItem(
                category=RepairCategory.DOCUMENTATION,
                action=RepairAction.ADD_SECTION,
                target=str(file_path),
                description=f"添加章节: {section_name}",
                status=RepairStatus.FAILED,
                error_message=str(e)
            )
        
        new_content = content + "\n\n" + section_content
        
        if dry_run:
            return RepairItem(
                category=RepairCategory.DOCUMENTATION,
                action=RepairAction.ADD_SECTION,
                target=str(file_path),
                description=f"添加章节: {section_name}",
                status=RepairStatus.DRY_RUN,
                original_content=content[:200],
                fixed_content=new_content[:200]
            )
        
        try:
            if backup:
                backup_path = self._create_backup(file_path)
            file_path.write_text(new_content, encoding='utf-8')
            return RepairItem(
                category=RepairCategory.DOCUMENTATION,
                action=RepairAction.ADD_SECTION,
                target=str(file_path),
                description=f"添加章节: {section_name}",
                status=RepairStatus.SUCCESS,
                original_content=content[:200],
                fixed_content=new_content[:200],
                backup_path=backup_path
            )
        except Exception as e:
            return RepairItem(
                category=RepairCategory.DOCUMENTATION,
                action=RepairAction.ADD_SECTION,
                target=str(file_path),
                description=f"添加章节: {section_name}",
                status=RepairStatus.FAILED,
                error_message=str(e)
            )
    
    def _repair_subskills(self, dry_run: bool, backup: bool) -> Dict[str, Any]:
        """修复子技能文档"""
        result = {"items": [], "total": 0, "fixed": 0, "failed": 0, "skipped": 0}
        
        if not self.subskills_dir.exists():
            return result
        
        for subskill_file in self.subskills_dir.glob("*.md"):
            try:
                content = subskill_file.read_text(encoding='utf-8')
            except Exception:
                continue
            
            if not content.strip().startswith('---'):
                result["total"] += 1
                new_content = self._create_subskill_frontmatter(subskill_file.stem) + content
                
                if dry_run:
                    result["items"].append(RepairItem(
                        category=RepairCategory.DOCUMENTATION,
                        action=RepairAction.FIX_FORMAT,
                        target=str(subskill_file),
                        description=f"添加子技能 frontmatter: {subskill_file.name}",
                        status=RepairStatus.DRY_RUN,
                        original_content=content[:200],
                        fixed_content=new_content[:200]
                    ))
                    result["fixed"] += 1
                else:
                    try:
                        if backup:
                            self._create_backup(subskill_file)
                        subskill_file.write_text(new_content, encoding='utf-8')
                        result["items"].append(RepairItem(
                            category=RepairCategory.DOCUMENTATION,
                            action=RepairAction.FIX_FORMAT,
                            target=str(subskill_file),
                            description=f"添加子技能 frontmatter: {subskill_file.name}",
                            status=RepairStatus.SUCCESS,
                            original_content=content[:200],
                            fixed_content=new_content[:200]
                        ))
                        result["fixed"] += 1
                    except Exception as e:
                        result["items"].append(RepairItem(
                            category=RepairCategory.DOCUMENTATION,
                            action=RepairAction.FIX_FORMAT,
                            target=str(subskill_file),
                            description=f"添加子技能 frontmatter: {subskill_file.name}",
                            status=RepairStatus.FAILED,
                            error_message=str(e)
                        ))
                        result["failed"] += 1
        
        return result
    
    def _create_subskill_frontmatter(self, name: str) -> str:
        """创建子技能 frontmatter"""
        return f'''---
name: "{name}"
description: "{name} subskill"
---

'''
    
    def _repair_doc_paths(self, dry_run: bool, backup: bool) -> Dict[str, Any]:
        """修复文档中的路径引用"""
        result = {"items": [], "total": 0, "fixed": 0, "failed": 0, "skipped": 0}
        
        if self.path_manager is None:
            return result
        
        try:
            validator = SkillDocPathValidator(self.skill_root)
        except Exception:
            return result
        
        md_files = []
        if self.skill_md_path.exists():
            md_files.append(self.skill_md_path)
        if self.subskills_dir.exists():
            md_files.extend(self.subskills_dir.glob("*.md"))
        
        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')
            except Exception:
                continue
            
            new_content = content
            fixes_made = 0
            
            wrong_prefix_pattern = re.compile(r'python\s+scripts/', re.IGNORECASE)
            matches = list(wrong_prefix_pattern.finditer(content))
            
            if matches:
                result["total"] += len(matches)
                new_content = wrong_prefix_pattern.sub('python skillscripts/', content)
                fixes_made = len(matches)
                
                if dry_run:
                    result["items"].append(RepairItem(
                        category=RepairCategory.DOCUMENTATION,
                        action=RepairAction.FIX_PATH,
                        target=str(md_file),
                        description=f"修复路径前缀 (scripts/ -> skillscripts/)",
                        status=RepairStatus.DRY_RUN,
                        original_content=content[:200],
                        fixed_content=new_content[:200]
                    ))
                    result["fixed"] += fixes_made
                else:
                    try:
                        if backup:
                            self._create_backup(md_file)
                        md_file.write_text(new_content, encoding='utf-8')
                        result["items"].append(RepairItem(
                            category=RepairCategory.DOCUMENTATION,
                            action=RepairAction.FIX_PATH,
                            target=str(md_file),
                            description=f"修复路径前缀 (scripts/ -> skillscripts/)",
                            status=RepairStatus.SUCCESS,
                            original_content=content[:200],
                            fixed_content=new_content[:200]
                        ))
                        result["fixed"] += fixes_made
                    except Exception as e:
                        result["items"].append(RepairItem(
                            category=RepairCategory.DOCUMENTATION,
                            action=RepairAction.FIX_PATH,
                            target=str(md_file),
                            description=f"修复路径前缀 (scripts/ -> skillscripts/)",
                            status=RepairStatus.FAILED,
                            error_message=str(e)
                        ))
                        result["failed"] += fixes_made
        
        return result
    
    def _create_backup(self, file_path: Path) -> str:
        """创建备份文件"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = self.backup_dir / f"{file_path.name}.bak.{timestamp}"
        shutil.copy2(file_path, backup_path)
        return str(backup_path)


class ScriptRepairer:
    """脚本修复器"""
    
    COMMON_IMPORT_FIXES = {
        "from skillscripts.": "from .",
        "import skillscripts.": "from . import ",
    }
    
    CORE_SCRIPTS = [
        "unified_script_entry.py",
        "start_services.py",
        "stop_services.py",
        "init_db.py",
        "health_check.py",
        "check_environment.py"
    ]
    
    def __init__(self, skillscripts_dir: Path, path_manager=None):
        self.skillscripts_dir = skillscripts_dir
        self.path_manager = path_manager
        self.backup_dir = skillscripts_dir.parent / "backups" / "scripts"
    
    def repair(self, dry_run: bool = True, backup: bool = True) -> RepairResult:
        """执行脚本修复"""
        items = []
        total_issues = 0
        fixed_issues = 0
        failed_issues = 0
        skipped_issues = 0
        
        syntax_result = self._fix_syntax_errors(dry_run, backup)
        items.extend(syntax_result["items"])
        total_issues += syntax_result["total"]
        fixed_issues += syntax_result["fixed"]
        failed_issues += syntax_result["failed"]
        skipped_issues += syntax_result["skipped"]
        
        import_result = self._fix_import_errors(dry_run, backup)
        items.extend(import_result["items"])
        total_issues += import_result["total"]
        fixed_issues += import_result["fixed"]
        failed_issues += import_result["failed"]
        skipped_issues += import_result["skipped"]
        
        missing_result = self._create_missing_core_scripts(dry_run)
        items.extend(missing_result["items"])
        total_issues += missing_result["total"]
        fixed_issues += missing_result["fixed"]
        failed_issues += missing_result["failed"]
        skipped_issues += missing_result["skipped"]
        
        return RepairResult(
            category=RepairCategory.SCRIPTS,
            total_issues=total_issues,
            fixed_issues=fixed_issues,
            failed_issues=failed_issues,
            skipped_issues=skipped_issues,
            items=items
        )
    
    def _fix_syntax_errors(self, dry_run: bool, backup: bool) -> Dict[str, Any]:
        """修复语法错误"""
        result = {"items": [], "total": 0, "fixed": 0, "failed": 0, "skipped": 0}
        
        all_scripts = list(self.skillscripts_dir.rglob("*.py"))
        
        for script in all_scripts[:50]:
            try:
                content = script.read_text(encoding='utf-8')
                ast.parse(content)
            except SyntaxError as e:
                result["total"] += 1
                item = self._attempt_syntax_fix(script, e, dry_run, backup)
                result["items"].append(item)
                if item.status == RepairStatus.SUCCESS:
                    result["fixed"] += 1
                elif item.status == RepairStatus.FAILED:
                    result["failed"] += 1
                else:
                    result["skipped"] += 1
            except Exception:
                pass
        
        return result
    
    def _attempt_syntax_fix(
        self, 
        script: Path, 
        error: SyntaxError, 
        dry_run: bool,
        backup: bool
    ) -> RepairItem:
        """尝试修复语法错误"""
        try:
            content = script.read_text(encoding='utf-8')
        except Exception as e:
            return RepairItem(
                category=RepairCategory.SCRIPTS,
                action=RepairAction.FIX_SYNTAX,
                target=str(script),
                description=f"修复语法错误 (行 {error.lineno})",
                status=RepairStatus.FAILED,
                error_message=f"无法读取文件: {e}"
            )
        
        fixes = []
        
        if "unmatched" in str(error.msg).lower() and error.lineno:
            lines = content.split('\n')
            if error.lineno <= len(lines):
                line = lines[error.lineno - 1]
                if line.rstrip().endswith(':') and not line.strip().startswith('#'):
                    pass
        
        fixes.extend(self._fix_common_syntax_issues(content))
        
        if not fixes:
            return RepairItem(
                category=RepairCategory.SCRIPTS,
                action=RepairAction.FIX_SYNTAX,
                target=str(script),
                description=f"修复语法错误 (行 {error.lineno}): {error.msg}",
                status=RepairStatus.SKIPPED,
                error_message="无法自动修复此语法错误"
            )
        
        new_content = content
        for old, new in fixes:
            new_content = new_content.replace(old, new)
        
        try:
            ast.parse(new_content)
        except SyntaxError:
            return RepairItem(
                category=RepairCategory.SCRIPTS,
                action=RepairAction.FIX_SYNTAX,
                target=str(script),
                description=f"修复语法错误 (行 {error.lineno}): {error.msg}",
                status=RepairStatus.PARTIAL,
                error_message="修复后仍存在语法错误，需要手动检查"
            )
        
        if dry_run:
            return RepairItem(
                category=RepairCategory.SCRIPTS,
                action=RepairAction.FIX_SYNTAX,
                target=str(script),
                description=f"修复语法错误 (行 {error.lineno}): {error.msg}",
                status=RepairStatus.DRY_RUN,
                original_content=content[:200],
                fixed_content=new_content[:200]
            )
        
        try:
            if backup:
                self._create_backup(script)
            script.write_text(new_content, encoding='utf-8')
            return RepairItem(
                category=RepairCategory.SCRIPTS,
                action=RepairAction.FIX_SYNTAX,
                target=str(script),
                description=f"修复语法错误 (行 {error.lineno}): {error.msg}",
                status=RepairStatus.SUCCESS,
                original_content=content[:200],
                fixed_content=new_content[:200]
            )
        except Exception as e:
            return RepairItem(
                category=RepairCategory.SCRIPTS,
                action=RepairAction.FIX_SYNTAX,
                target=str(script),
                description=f"修复语法错误 (行 {error.lineno}): {error.msg}",
                status=RepairStatus.FAILED,
                error_message=str(e)
            )
    
    def _fix_common_syntax_issues(self, content: str) -> List[Tuple[str, str]]:
        """修复常见语法问题"""
        fixes = []
        
        fixes.append(('\t', '    '))
        
        fixes.append(('\r\n', '\n'))
        
        fixes.append(('""" ', '"""\n'))
        fixes.append((' """', '\n"""'))
        
        return fixes
    
    def _fix_import_errors(self, dry_run: bool, backup: bool) -> Dict[str, Any]:
        """修复导入错误"""
        result = {"items": [], "total": 0, "fixed": 0, "failed": 0, "skipped": 0}
        
        all_scripts = list(self.skillscripts_dir.rglob("*.py"))
        
        for script in all_scripts[:50]:
            try:
                content = script.read_text(encoding='utf-8')
            except Exception:
                continue
            
            new_content = content
            fixes_made = 0
            
            for old_import, new_import in self.COMMON_IMPORT_FIXES.items():
                if old_import in content:
                    new_content = new_content.replace(old_import, new_import)
                    fixes_made += content.count(old_import)
            
            if fixes_made > 0:
                result["total"] += 1
                
                if dry_run:
                    result["items"].append(RepairItem(
                        category=RepairCategory.SCRIPTS,
                        action=RepairAction.FIX_IMPORT,
                        target=str(script),
                        description=f"修复导入路径",
                        status=RepairStatus.DRY_RUN,
                        original_content=content[:200],
                        fixed_content=new_content[:200]
                    ))
                    result["fixed"] += 1
                else:
                    try:
                        if backup:
                            self._create_backup(script)
                        script.write_text(new_content, encoding='utf-8')
                        result["items"].append(RepairItem(
                            category=RepairCategory.SCRIPTS,
                            action=RepairAction.FIX_IMPORT,
                            target=str(script),
                            description=f"修复导入路径",
                            status=RepairStatus.SUCCESS,
                            original_content=content[:200],
                            fixed_content=new_content[:200]
                        ))
                        result["fixed"] += 1
                    except Exception as e:
                        result["items"].append(RepairItem(
                            category=RepairCategory.SCRIPTS,
                            action=RepairAction.FIX_IMPORT,
                            target=str(script),
                            description=f"修复导入路径",
                            status=RepairStatus.FAILED,
                            error_message=str(e)
                        ))
                        result["failed"] += 1
        
        return result
    
    def _create_missing_core_scripts(self, dry_run: bool) -> Dict[str, Any]:
        """创建缺失的核心脚本"""
        result = {"items": [], "total": 0, "fixed": 0, "failed": 0, "skipped": 0}
        
        core_dir = self.skillscripts_dir / "core"
        
        for script_name in self.CORE_SCRIPTS:
            script_path = core_dir / script_name
            if not script_path.exists():
                result["total"] += 1
                item = self._create_placeholder_script(script_path, script_name, dry_run)
                result["items"].append(item)
                if item.status == RepairStatus.SUCCESS:
                    result["fixed"] += 1
                elif item.status == RepairStatus.DRY_RUN:
                    result["fixed"] += 1
                else:
                    result["failed"] += 1
        
        return result
    
    def _create_placeholder_script(
        self, 
        script_path: Path, 
        script_name: str,
        dry_run: bool
    ) -> RepairItem:
        """创建占位符脚本"""
        name_without_ext = script_name.replace('.py', '')
        
        content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{name_without_ext} - 自动生成的占位符脚本

此文件由 skill_auto_repairer.py 自动生成。
请根据实际需求完善此脚本的功能。
"""

import sys


def main():
    """主函数"""
    print("脚本 {script_name} 尚未实现")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
        
        if dry_run:
            return RepairItem(
                category=RepairCategory.SCRIPTS,
                action=RepairAction.CREATE_FILE,
                target=str(script_path),
                description=f"创建缺失的核心脚本: {script_name}",
                status=RepairStatus.DRY_RUN,
                fixed_content=content
            )
        
        try:
            script_path.parent.mkdir(parents=True, exist_ok=True)
            script_path.write_text(content, encoding='utf-8')
            return RepairItem(
                category=RepairCategory.SCRIPTS,
                action=RepairAction.CREATE_FILE,
                target=str(script_path),
                description=f"创建缺失的核心脚本: {script_name}",
                status=RepairStatus.SUCCESS,
                fixed_content=content
            )
        except Exception as e:
            return RepairItem(
                category=RepairCategory.SCRIPTS,
                action=RepairAction.CREATE_FILE,
                target=str(script_path),
                description=f"创建缺失的核心脚本: {script_name}",
                status=RepairStatus.FAILED,
                error_message=str(e)
            )
    
    def _create_backup(self, file_path: Path) -> str:
        """创建备份文件"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = self.backup_dir / f"{file_path.name}.bak.{timestamp}"
        shutil.copy2(file_path, backup_path)
        return str(backup_path)


class ConfigurationRepairer:
    """配置修复器"""
    
    REQUIRED_ENV_VARS = [
        "DATABASE_HOST",
        "DATABASE_PORT",
        "DATABASE_NAME",
        "BACKEND_HOST",
        "BACKEND_PORT"
    ]
    
    DEFAULT_ENV_CONTENT = '''# 数据库配置
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=skill_db

# 后端配置
BACKEND_HOST=localhost
BACKEND_PORT=8000

# 前端配置
FRONTEND_HOST=localhost
FRONTEND_PORT=3000
'''
    
    DEFAULT_DOCKER_COMPOSE = '''version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: skill_db
      POSTGRES_USER: skill_user
      POSTGRES_PASSWORD: skill_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
'''
    
    def __init__(self, skill_root: Path, path_manager=None):
        self.skill_root = skill_root
        self.path_manager = path_manager
        self.config_dir = skill_root / "config"
        self.env_file = skill_root / ".env"
        self.env_example = skill_root / ".env.example"
        self.docker_compose = skill_root / "docker-compose.yml"
        self.backup_dir = skill_root / "backups" / "config"
    
    def repair(self, dry_run: bool = True, backup: bool = True) -> RepairResult:
        """执行配置修复"""
        items = []
        total_issues = 0
        fixed_issues = 0
        failed_issues = 0
        skipped_issues = 0
        
        env_result = self._fix_env_files(dry_run, backup)
        items.extend(env_result["items"])
        total_issues += env_result["total"]
        fixed_issues += env_result["fixed"]
        failed_issues += env_result["failed"]
        skipped_issues += env_result["skipped"]
        
        docker_result = self._fix_docker_config(dry_run, backup)
        items.extend(docker_result["items"])
        total_issues += docker_result["total"]
        fixed_issues += docker_result["fixed"]
        failed_issues += docker_result["failed"]
        skipped_issues += docker_result["skipped"]
        
        consistency_result = self._fix_config_consistency(dry_run, backup)
        items.extend(consistency_result["items"])
        total_issues += consistency_result["total"]
        fixed_issues += consistency_result["fixed"]
        failed_issues += consistency_result["failed"]
        skipped_issues += consistency_result["skipped"]
        
        return RepairResult(
            category=RepairCategory.CONFIGURATION,
            total_issues=total_issues,
            fixed_issues=fixed_issues,
            failed_issues=failed_issues,
            skipped_issues=skipped_issues,
            items=items
        )
    
    def _fix_env_files(self, dry_run: bool, backup: bool) -> Dict[str, Any]:
        """修复环境配置文件"""
        result = {"items": [], "total": 0, "fixed": 0, "failed": 0, "skipped": 0}
        
        if not self.env_example.exists():
            result["total"] += 1
            item = self._create_file(self.env_example, self.DEFAULT_ENV_CONTENT, ".env.example", dry_run)
            result["items"].append(item)
            if item.status in (RepairStatus.SUCCESS, RepairStatus.DRY_RUN):
                result["fixed"] += 1
            else:
                result["failed"] += 1
        
        if not self.env_file.exists():
            result["total"] += 1
            item = self._create_file(self.env_file, self.DEFAULT_ENV_CONTENT, ".env", dry_run)
            result["items"].append(item)
            if item.status in (RepairStatus.SUCCESS, RepairStatus.DRY_RUN):
                result["fixed"] += 1
            else:
                result["failed"] += 1
        else:
            missing_vars = self._check_missing_env_vars()
            if missing_vars:
                result["total"] += 1
                item = self._add_missing_env_vars(missing_vars, dry_run, backup)
                result["items"].append(item)
                if item.status in (RepairStatus.SUCCESS, RepairStatus.DRY_RUN):
                    result["fixed"] += 1
                else:
                    result["failed"] += 1
        
        return result
    
    def _check_missing_env_vars(self) -> List[str]:
        """检查缺失的环境变量"""
        missing = []
        try:
            content = self.env_file.read_text(encoding='utf-8')
            for var in self.REQUIRED_ENV_VARS:
                if var not in content:
                    missing.append(var)
        except Exception:
            missing = self.REQUIRED_ENV_VARS.copy()
        return missing
    
    def _add_missing_env_vars(
        self, 
        missing_vars: List[str], 
        dry_run: bool,
        backup: bool
    ) -> RepairItem:
        """添加缺失的环境变量"""
        try:
            content = self.env_file.read_text(encoding='utf-8')
        except Exception as e:
            return RepairItem(
                category=RepairCategory.CONFIGURATION,
                action=RepairAction.ADD_CONFIG,
                target=str(self.env_file),
                description=f"添加缺失的环境变量: {', '.join(missing_vars)}",
                status=RepairStatus.FAILED,
                error_message=str(e)
            )
        
        new_vars = "\n\n# 自动添加的环境变量\n"
        for var in missing_vars:
            new_vars += f"{var}=\n"
        
        new_content = content + new_vars
        
        if dry_run:
            return RepairItem(
                category=RepairCategory.CONFIGURATION,
                action=RepairAction.ADD_CONFIG,
                target=str(self.env_file),
                description=f"添加缺失的环境变量: {', '.join(missing_vars)}",
                status=RepairStatus.DRY_RUN,
                original_content=content[:200],
                fixed_content=new_content[:200]
            )
        
        try:
            if backup:
                self._create_backup(self.env_file)
            self.env_file.write_text(new_content, encoding='utf-8')
            return RepairItem(
                category=RepairCategory.CONFIGURATION,
                action=RepairAction.ADD_CONFIG,
                target=str(self.env_file),
                description=f"添加缺失的环境变量: {', '.join(missing_vars)}",
                status=RepairStatus.SUCCESS,
                original_content=content[:200],
                fixed_content=new_content[:200]
            )
        except Exception as e:
            return RepairItem(
                category=RepairCategory.CONFIGURATION,
                action=RepairAction.ADD_CONFIG,
                target=str(self.env_file),
                description=f"添加缺失的环境变量: {', '.join(missing_vars)}",
                status=RepairStatus.FAILED,
                error_message=str(e)
            )
    
    def _fix_docker_config(self, dry_run: bool, backup: bool) -> Dict[str, Any]:
        """修复 Docker 配置"""
        result = {"items": [], "total": 0, "fixed": 0, "failed": 0, "skipped": 0}
        
        if not self.docker_compose.exists():
            result["total"] += 1
            item = self._create_file(
                self.docker_compose, 
                self.DEFAULT_DOCKER_COMPOSE, 
                "docker-compose.yml", 
                dry_run
            )
            result["items"].append(item)
            if item.status in (RepairStatus.SUCCESS, RepairStatus.DRY_RUN):
                result["fixed"] += 1
            else:
                result["failed"] += 1
        else:
            try:
                import yaml
                content = self.docker_compose.read_text(encoding='utf-8')
                config = yaml.safe_load(content)
                
                if not config.get('services'):
                    result["total"] += 1
                    result["items"].append(RepairItem(
                        category=RepairCategory.CONFIGURATION,
                        action=RepairAction.FIX_FORMAT,
                        target=str(self.docker_compose),
                        description="Docker Compose 配置缺少 services",
                        status=RepairStatus.SKIPPED,
                        error_message="需要手动检查 Docker Compose 配置"
                    ))
            except ImportError:
                pass
            except Exception as e:
                result["total"] += 1
                result["items"].append(RepairItem(
                    category=RepairCategory.CONFIGURATION,
                    action=RepairAction.FIX_FORMAT,
                    target=str(self.docker_compose),
                    description="修复 Docker Compose 配置格式",
                    status=RepairStatus.FAILED,
                    error_message=str(e)
                ))
                result["failed"] += 1
        
        return result
    
    def _fix_config_consistency(self, dry_run: bool, backup: bool) -> Dict[str, Any]:
        """修复配置一致性"""
        result = {"items": [], "total": 0, "fixed": 0, "failed": 0, "skipped": 0}
        
        backend_path = self.skill_root / "backend"
        if backend_path.exists():
            requirements = backend_path / "requirements.txt"
            if not requirements.exists():
                result["total"] += 1
                item = self._create_file(
                    requirements,
                    "# Python 依赖\nfastapi>=0.68.0\nuvicorn>=0.15.0\npydantic>=1.8.0\n",
                    "requirements.txt",
                    dry_run
                )
                result["items"].append(item)
                if item.status in (RepairStatus.SUCCESS, RepairStatus.DRY_RUN):
                    result["fixed"] += 1
                else:
                    result["failed"] += 1
        
        frontend_path = self.skill_root / "frontend"
        if frontend_path.exists():
            package_json = frontend_path / "package.json"
            if not package_json.exists():
                result["total"] += 1
                default_package = json.dumps({
                    "name": "skill-frontend",
                    "version": "1.0.0",
                    "scripts": {
                        "dev": "vite",
                        "build": "vite build"
                    },
                    "dependencies": {}
                }, indent=2)
                item = self._create_file(package_json, default_package, "package.json", dry_run)
                result["items"].append(item)
                if item.status in (RepairStatus.SUCCESS, RepairStatus.DRY_RUN):
                    result["fixed"] += 1
                else:
                    result["failed"] += 1
        
        return result
    
    def _create_file(
        self, 
        file_path: Path, 
        content: str, 
        description: str,
        dry_run: bool
    ) -> RepairItem:
        """创建文件"""
        if dry_run:
            return RepairItem(
                category=RepairCategory.CONFIGURATION,
                action=RepairAction.CREATE_FILE,
                target=str(file_path),
                description=f"创建 {description}",
                status=RepairStatus.DRY_RUN,
                fixed_content=content[:200]
            )
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            return RepairItem(
                category=RepairCategory.CONFIGURATION,
                action=RepairAction.CREATE_FILE,
                target=str(file_path),
                description=f"创建 {description}",
                status=RepairStatus.SUCCESS,
                fixed_content=content[:200]
            )
        except Exception as e:
            return RepairItem(
                category=RepairCategory.CONFIGURATION,
                action=RepairAction.CREATE_FILE,
                target=str(file_path),
                description=f"创建 {description}",
                status=RepairStatus.FAILED,
                error_message=str(e)
            )
    
    def _create_backup(self, file_path: Path) -> str:
        """创建备份文件"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = self.backup_dir / f"{file_path.name}.bak.{timestamp}"
        shutil.copy2(file_path, backup_path)
        return str(backup_path)


class PathStructureRepairer:
    """路径结构修复器"""

    REQUIRED_DIRECTORIES = [
        "core",
        "utils",
        "analysis",
        "pipeline",
        "test",
        "subskills",
        "backend",
        "frontend"
    ]

    def __init__(self, skill_root: Path, path_manager=None):
        self.skill_root = skill_root
        self.path_manager = path_manager
        self.scripts_dir = get_path_config().SCRIPTS_DIR

    def repair(self, dry_run: bool = True, backup: bool = True) -> RepairResult:
        """执行路径结构修复"""
        items = []
        total_issues = 0
        fixed_issues = 0
        failed_issues = 0
        skipped_issues = 0

        for dir_path in self.REQUIRED_DIRECTORIES:
            if dir_path in ["subskills", "backend", "frontend"]:
                full_path = self.skill_root / dir_path
            else:
                full_path = self.scripts_dir / dir_path
            if not full_path.exists():
                total_issues += 1
                item = self._create_directory(full_path, dry_run)
                items.append(item)
                if item.status in (RepairStatus.SUCCESS, RepairStatus.DRY_RUN):
                    fixed_issues += 1
                else:
                    failed_issues += 1
        
        return RepairResult(
            category=RepairCategory.PATH_STRUCTURE,
            total_issues=total_issues,
            fixed_issues=fixed_issues,
            failed_issues=failed_issues,
            skipped_issues=skipped_issues,
            items=items
        )
    
    def _create_directory(self, dir_path: Path, dry_run: bool) -> RepairItem:
        """创建目录"""
        if dry_run:
            return RepairItem(
                category=RepairCategory.PATH_STRUCTURE,
                action=RepairAction.CREATE_DIR,
                target=str(dir_path),
                description=f"创建目录: {dir_path.relative_to(self.skill_root)}",
                status=RepairStatus.DRY_RUN
            )
        
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            gitkeep = dir_path / ".gitkeep"
            gitkeep.touch()
            return RepairItem(
                category=RepairCategory.PATH_STRUCTURE,
                action=RepairAction.CREATE_DIR,
                target=str(dir_path),
                description=f"创建目录: {dir_path.relative_to(self.skill_root)}",
                status=RepairStatus.SUCCESS
            )
        except Exception as e:
            return RepairItem(
                category=RepairCategory.PATH_STRUCTURE,
                action=RepairAction.CREATE_DIR,
                target=str(dir_path),
                description=f"创建目录: {dir_path.relative_to(self.skill_root)}",
                status=RepairStatus.FAILED,
                error_message=str(e)
            )


class RepairValidator:
    """修复效果验证器"""
    
    def __init__(self, skill_root: Path):
        self.skill_root = skill_root
    
    def validate_repair(self, repair_result: RepairResult) -> Dict[str, Any]:
        """验证修复效果"""
        validation = {
            "category": repair_result.category.value,
            "total_items": len(repair_result.items),
            "validated": 0,
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        for item in repair_result.items:
            if item.status not in (RepairStatus.SUCCESS, RepairStatus.DRY_RUN):
                continue
            
            validation["validated"] += 1
            
            item_validation = self._validate_item(item)
            validation["details"].append(item_validation)
            
            if item_validation["valid"]:
                validation["passed"] += 1
            else:
                validation["failed"] += 1
        
        return validation
    
    def _validate_item(self, item: RepairItem) -> Dict[str, Any]:
        """验证单个修复项"""
        result = {
            "target": item.target,
            "action": item.action.value,
            "valid": False,
            "message": ""
        }
        
        target_path = Path(item.target)
        
        if item.action == RepairAction.CREATE_FILE:
            if target_path.exists():
                result["valid"] = True
                result["message"] = "文件创建成功"
            else:
                result["message"] = "文件不存在"
        
        elif item.action == RepairAction.CREATE_DIR:
            if target_path.exists() and target_path.is_dir():
                result["valid"] = True
                result["message"] = "目录创建成功"
            else:
                result["message"] = "目录不存在"
        
        elif item.action in (RepairAction.FIX_FORMAT, RepairAction.FIX_PATH, 
                            RepairAction.FIX_IMPORT, RepairAction.FIX_SYNTAX,
                            RepairAction.ADD_SECTION, RepairAction.ADD_CONFIG):
            if target_path.exists():
                try:
                    if target_path.suffix == '.py':
                        content = target_path.read_text(encoding='utf-8')
                        ast.parse(content)
                        result["valid"] = True
                        result["message"] = "Python 文件语法正确"
                    else:
                        result["valid"] = True
                        result["message"] = "文件已修改"
                except SyntaxError as e:
                    result["message"] = f"语法错误: {e}"
                except Exception as e:
                    result["message"] = f"验证失败: {e}"
            else:
                result["message"] = "文件不存在"
        
        else:
            result["valid"] = True
            result["message"] = "无需验证"
        
        return result


class SkillAutoRepairer:
    """技能自动修复系统主类"""
    
    def __init__(self, skill_root: Optional[Path] = None, verbose: bool = True):
        self.skill_root = skill_root or self._detect_skill_root()
        self.skillscripts_dir = self.skill_root / "skillscripts"
        self.verbose = verbose
        self._setup_logging()
        
        self.path_manager = None
        try:
            self.path_manager = create_path_manager(self.skill_root)
        except Exception:
            pass
        
        self.doc_repairer = DocumentationRepairer(self.skill_root, self.path_manager)
        self.script_repairer = ScriptRepairer(self.skillscripts_dir, self.path_manager)
        self.config_repairer = ConfigurationRepairer(self.skill_root, self.path_manager)
        self.path_repairer = PathStructureRepairer(self.skill_root, self.path_manager)
        self.validator = RepairValidator(self.skill_root)
    
    def _detect_skill_root(self) -> Path:
        """检测技能根目录"""
        current = Path(__file__).resolve()
        while current != current.parent:
            if (current / "SKILL.md").exists() or (current / "skillscripts").exists():
                return current
            current = current.parent
        return PROJECT_ROOT / ".trae" / "skills" / "sanliu"
    
    def _setup_logging(self):
        """设置日志"""
        level = logging.DEBUG if self.verbose else logging.WARNING
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _log(self, message: str, level: str = "info"):
        """输出日志"""
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "debug": "🔍"
        }
        icon = icons.get(level, "")
        if self.verbose:
            print(f"{icon} {message}")
        
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(message)
    
    def repair(
        self,
        fix_docs: bool = True,
        fix_scripts: bool = True,
        fix_config: bool = True,
        fix_paths: bool = True,
        dry_run: bool = False,
        backup: bool = True,
        validate: bool = True
    ) -> RepairReport:
        """
        执行自动修复
        
        Args:
            fix_docs: 是否修复文档
            fix_scripts: 是否修复脚本
            fix_config: 是否修复配置
            fix_paths: 是否修复路径结构
            dry_run: 是否预览模式
            backup: 是否备份
            validate: 是否验证修复效果
            
        Returns:
            修复报告
        """
        start_time = time.time()
        self._log(f"开始技能自动修复... (dry_run={dry_run})")
        
        health_before = None
        if validate:
            health_before = self._get_health_assessment()
        
        category_results = []
        
        if fix_docs:
            self._log("修复文档问题...")
            doc_result = self.doc_repairer.repair(dry_run, backup)
            category_results.append(doc_result)
            self._log(f"文档修复完成: {doc_result.fixed_issues}/{doc_result.total_issues}")
        
        if fix_scripts:
            self._log("修复脚本问题...")
            script_result = self.script_repairer.repair(dry_run, backup)
            category_results.append(script_result)
            self._log(f"脚本修复完成: {script_result.fixed_issues}/{script_result.total_issues}")
        
        if fix_config:
            self._log("修复配置问题...")
            config_result = self.config_repairer.repair(dry_run, backup)
            category_results.append(config_result)
            self._log(f"配置修复完成: {config_result.fixed_issues}/{config_result.total_issues}")
        
        if fix_paths:
            self._log("修复路径结构...")
            path_result = self.path_repairer.repair(dry_run, backup)
            category_results.append(path_result)
            self._log(f"路径修复完成: {path_result.fixed_issues}/{path_result.total_issues}")
        
        total_issues = sum(r.total_issues for r in category_results)
        total_fixed = sum(r.fixed_issues for r in category_results)
        total_failed = sum(r.failed_issues for r in category_results)
        total_skipped = sum(r.skipped_issues for r in category_results)
        
        overall_success_rate = (total_fixed / total_issues * 100) if total_issues > 0 else 100.0
        
        health_after = None
        if validate and not dry_run:
            health_after = self._get_health_assessment()
        
        duration_ms = (time.time() - start_time) * 1000
        
        report = RepairReport(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            skill_root=str(self.skill_root),
            dry_run=dry_run,
            total_issues=total_issues,
            total_fixed=total_fixed,
            total_failed=total_failed,
            total_skipped=total_skipped,
            overall_success_rate=overall_success_rate,
            duration_ms=duration_ms,
            category_results=category_results,
            health_before=health_before,
            health_after=health_after
        )
        
        self._log(f"修复完成: {total_fixed}/{total_issues} ({overall_success_rate:.1f}%)", "success")
        
        return report
    
    def _get_health_assessment(self) -> Optional[Dict[str, Any]]:
        """获取健康度评估"""
        try:
            assessor = SkillHealthAssessor(skill_root=self.skill_root, verbose=False)
            report = assessor.assess()
            return {
                "overall_score": report.overall_score,
                "health_level": report.health_level.value
            }
        except Exception:
            return None
    
    def generate_report(
        self, 
        report: RepairReport, 
        output_path: Optional[Path] = None,
        format: str = "markdown"
    ) -> str:
        """生成修复报告"""
        if format == "json":
            content = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
        else:
            content = self._generate_markdown_report(report)
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding='utf-8')
            self._log(f"报告已保存至: {output_path}")
        
        return content
    
    def _generate_markdown_report(self, report: RepairReport) -> str:
        """生成 Markdown 格式报告"""
        lines = [
            "# 技能自动修复报告",
            "",
            f"**修复时间**: {report.timestamp}",
            f"**技能根目录**: {report.skill_root}",
            f"**预览模式**: {'是' if report.dry_run else '否'}",
            f"**修复耗时**: {report.duration_ms:.2f}ms",
            "",
            "---",
            "",
            "## 修复概览",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 发现问题 | {report.total_issues} |",
            f"| 已修复 | {report.total_fixed} |",
            f"| 修复失败 | {report.total_failed} |",
            f"| 已跳过 | {report.total_skipped} |",
            f"| 成功率 | {report.overall_success_rate:.1f}% |",
            ""
        ]
        
        if report.health_before:
            lines.extend([
                "---",
                "",
                "## 健康度变化",
                "",
                f"- **修复前评分**: {report.health_before.get('overall_score', 'N/A')}/100",
                f"- **修复前等级**: {report.health_before.get('health_level', 'N/A')}"
            ])
            
            if report.health_after:
                lines.extend([
                    f"- **修复后评分**: {report.health_after.get('overall_score', 'N/A')}/100",
                    f"- **修复后等级**: {report.health_after.get('health_level', 'N/A')}"
                ])
            
            lines.append("")
        
        for result in report.category_results:
            lines.extend([
                "---",
                "",
                f"## {self._get_category_display(result.category)}",
                "",
                f"- 发现问题: {result.total_issues}",
                f"- 已修复: {result.fixed_issues}",
                f"- 修复失败: {result.failed_issues}",
                f"- 已跳过: {result.skipped_issues}",
                f"- 成功率: {result.success_rate:.1f}%",
                ""
            ])
            
            if result.items:
                lines.extend([
                    "### 修复详情",
                    "",
                    "| 目标 | 动作 | 描述 | 状态 |",
                    "|------|------|------|------|"
                ])
                
                for item in result.items:
                    status_icon = {
                        RepairStatus.SUCCESS: "✅",
                        RepairStatus.PARTIAL: "⚠️",
                        RepairStatus.FAILED: "❌",
                        RepairStatus.SKIPPED: "⏭️",
                        RepairStatus.DRY_RUN: "👁️"
                    }.get(item.status, "❓")
                    
                    target_name = Path(item.target).name
                    lines.append(
                        f"| {target_name} | {item.action.value} | {item.description} | {status_icon} |"
                    )
                
                lines.append("")
        
        lines.extend([
            "---",
            "",
            "*报告由技能自动修复系统生成*"
        ])
        
        return "\n".join(lines)
    
    def _get_category_display(self, category: RepairCategory) -> str:
        """获取分类显示名称"""
        displays = {
            RepairCategory.DOCUMENTATION: "📚 文档修复",
            RepairCategory.SCRIPTS: "🔧 脚本修复",
            RepairCategory.CONFIGURATION: "⚙️ 配置修复",
            RepairCategory.PATH_STRUCTURE: "📁 路径结构修复"
        }
        return displays.get(category, category.value)


def print_console_report(report: RepairReport):
    """打印控制台报告"""
    print("\n" + "=" * 70)
    print("🔧 技能自动修复报告")
    print("=" * 70)
    print(f"⏰ 修复时间: {report.timestamp}")
    print(f"📁 技能根目录: {report.skill_root}")
    print(f"👁️ 预览模式: {'是' if report.dry_run else '否'}")
    print(f"⏱️ 修复耗时: {report.duration_ms:.2f}ms")
    print("-" * 70)
    print("📊 修复统计:")
    print(f"   发现问题: {report.total_issues}")
    print(f"   已修复: {report.total_fixed}")
    print(f"   修复失败: {report.total_failed}")
    print(f"   已跳过: {report.total_skipped}")
    print(f"   成功率: {report.overall_success_rate:.1f}%")
    print("-" * 70)
    
    for result in report.category_results:
        status = "✅" if result.success_rate >= 80 else "⚠️" if result.success_rate >= 50 else "❌"
        print(f"   {status} {result.category.value}: {result.fixed_issues}/{result.total_issues}")
    
    if report.health_before and report.health_after:
        print("-" * 70)
        print("🏥 健康度变化:")
        print(f"   修复前: {report.health_before.get('overall_score', 'N/A')}/100")
        print(f"   修复后: {report.health_after.get('overall_score', 'N/A')}/100")
    
    print("=" * 70)
    
    if report.overall_success_rate >= 80:
        print("🎉 修复成功！")
    elif report.overall_success_rate >= 50:
        print("⚠️ 部分修复成功，请检查失败项。")
    else:
        print("❌ 修复失败较多，请手动检查。")
    
    print("=" * 70)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="技能自动修复系统 - 自动修复技能系统中的各类问题",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python skillscripts/core/skill_auto_repairer.py --auto          # 自动修复所有问题
  python skillscripts/core/skill_auto_repairer.py --fix-docs      # 只修复文档问题
  python skillscripts/core/skill_auto_repairer.py --fix-scripts   # 只修复脚本问题
  python skillscripts/core/skill_auto_repairer.py --fix-config    # 只修复配置问题
  python skillscripts/core/skill_auto_repairer.py --dry-run       # 预览修复（不实际修改）
  python skillscripts/core/skill_auto_repairer.py --output report.md  # 保存报告

修复类别:
  documentation  - 文档修复（缺失章节、格式错误、路径引用）
  scripts        - 脚本修复（导入错误、语法错误、缺失脚本）
  configuration  - 配置修复（配置文件格式、缺失配置项）
  path_structure - 路径结构修复（缺失目录）
        """
    )
    
    parser.add_argument("--auto", action="store_true", help="自动修复所有问题")
    parser.add_argument("--fix-docs", action="store_true", help="修复文档问题")
    parser.add_argument("--fix-scripts", action="store_true", help="修复脚本问题")
    parser.add_argument("--fix-config", action="store_true", help="修复配置问题")
    parser.add_argument("--fix-paths", action="store_true", help="修复路径结构")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际修改")
    parser.add_argument("--no-backup", action="store_true", help="不创建备份")
    parser.add_argument("--no-validate", action="store_true", help="不验证修复效果")
    parser.add_argument("--output", "-o", type=str, help="输出报告文件路径")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown", help="报告格式")
    parser.add_argument("--skill-root", type=str, help="技能根目录路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    fix_all = args.auto
    fix_docs = args.fix_docs or fix_all
    fix_scripts = args.fix_scripts or fix_all
    fix_config = args.fix_config or fix_all
    fix_paths = args.fix_paths or fix_all
    
    if not any([fix_docs, fix_scripts, fix_config, fix_paths]):
        fix_all = True
        fix_docs = fix_scripts = fix_config = fix_paths = True
    
    skill_root = Path(args.skill_root) if args.skill_root else None
    
    repairer = SkillAutoRepairer(skill_root=skill_root, verbose=args.verbose)
    
    report = repairer.repair(
        fix_docs=fix_docs,
        fix_scripts=fix_scripts,
        fix_config=fix_config,
        fix_paths=fix_paths,
        dry_run=args.dry_run,
        backup=not args.no_backup,
        validate=not args.no_validate
    )
    
    if args.format == "json":
        print(repairer.generate_report(report, format="json"))
    else:
        print_console_report(report)
    
    if args.output:
        output_path = Path(args.output)
        repairer.generate_report(report, output_path, args.format)
        if args.format != "json":
            print(f"\n📄 报告已保存至: {args.output}")
    
    return 0 if report.overall_success_rate >= 50 else 1


if __name__ == "__main__":
    sys.exit(main())
