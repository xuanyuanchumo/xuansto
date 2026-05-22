#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能健康度评估器 - Skill Health Assessor

功能：
1. 文档完整性检查：检查 SKILL.md 和所有子技能文档的完整性
2. 脚本可用性检查：检查所有脚本文件是否存在且可执行
3. 配置一致性检查：检查配置文件的一致性和有效性
4. 健康度评分算法：基于多个维度计算技能健康度评分（0-100分）
5. 生成健康度报告：输出详细的评估结果和改进建议

支持：
- 多种评估维度（文档、脚本、配置、路径等）
- 健康度评分和详细分析
- JSON 和 Markdown 格式的报告
- 命令行接口
- 可集成到持续演化系统中
"""

import argparse
import ast
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

PROJECT_ROOT = get_path_config().SKILL_ROOT
SKILLSCRIPTS_DIR = Path(__file__).parent
CORE_DIR = get_path_config().SCRIPTS_DIR / "core"


class HealthLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class AssessmentCategory(Enum):
    DOCUMENTATION = "documentation"
    SCRIPTS = "scripts"
    CONFIGURATION = "configuration"
    PATH_STRUCTURE = "path_structure"
    DEPENDENCIES = "dependencies"
    METADATA = "metadata"


@dataclass
class AssessmentItem:
    name: str
    category: AssessmentCategory
    score: float
    max_score: float
    status: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    
    @property
    def percentage(self) -> float:
        return (self.score / self.max_score * 100) if self.max_score > 0 else 0


@dataclass
class CategoryResult:
    category: AssessmentCategory
    score: float
    max_score: float
    items: List[AssessmentItem]
    weight: float
    
    @property
    def percentage(self) -> float:
        return (self.score / self.max_score * 100) if self.max_score > 0 else 0


@dataclass
class HealthAssessmentReport:
    timestamp: str
    overall_score: float
    health_level: HealthLevel
    category_results: List[CategoryResult]
    summary: Dict[str, Any]
    recommendations: List[str]
    duration_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "overall_score": self.overall_score,
            "health_level": self.health_level.value,
            "category_results": [
                {
                    "category": cr.category.value,
                    "score": cr.score,
                    "max_score": cr.max_score,
                    "percentage": round(cr.percentage, 2),
                    "weight": cr.weight,
                    "items": [
                        {
                            "name": item.name,
                            "score": item.score,
                            "max_score": item.max_score,
                            "percentage": round(item.percentage, 2),
                            "status": item.status,
                            "message": item.message,
                            "details": item.details,
                            "suggestions": item.suggestions
                        }
                        for item in cr.items
                    ]
                }
                for cr in self.category_results
            ],
            "summary": self.summary,
            "recommendations": self.recommendations,
            "duration_ms": self.duration_ms
        }


class DocumentationChecker:
    REQUIRED_SKILL_MD_SECTIONS = [
        "触发条件",
        "快速开始",
        "工作流程",
        "核心功能"
    ]
    
    REQUIRED_SUBSKILL_FRONTMATTER = ["name", "description"]
    
    OPTIONAL_SKILL_MD_SECTIONS = [
        "API",
        "配置",
        "示例",
        "故障排除",
        "更新日志"
    ]
    
    def __init__(self, skill_root: Path):
        self.skill_root = skill_root
        self.skill_md_path = skill_root / "SKILL.md"
        self.subskills_dir = skill_root / "subskills"
    
    def check(self) -> CategoryResult:
        items = []
        total_score = 0
        max_score = 0
        
        skill_md_item = self._check_skill_md()
        items.append(skill_md_item)
        total_score += skill_md_item.score
        max_score += skill_md_item.max_score
        
        subskills_item = self._check_subskills()
        items.append(subskills_item)
        total_score += subskills_item.score
        max_score += subskills_item.max_score
        
        readme_item = self._check_readme()
        items.append(readme_item)
        total_score += readme_item.score
        max_score += readme_item.max_score
        
        return CategoryResult(
            category=AssessmentCategory.DOCUMENTATION,
            score=total_score,
            max_score=max_score,
            items=items,
            weight=0.25
        )
    
    def _check_skill_md(self) -> AssessmentItem:
        if not self.skill_md_path.exists():
            return AssessmentItem(
                name="SKILL.md 主文档",
                category=AssessmentCategory.DOCUMENTATION,
                score=0,
                max_score=40,
                status="missing",
                message="SKILL.md 文件不存在",
                suggestions=["创建 SKILL.md 文件，包含技能的基本描述和使用说明"]
            )
        
        try:
            content = self.skill_md_path.read_text(encoding='utf-8')
        except Exception as e:
            return AssessmentItem(
                name="SKILL.md 主文档",
                category=AssessmentCategory.DOCUMENTATION,
                score=5,
                max_score=40,
                status="error",
                message=f"读取 SKILL.md 失败: {e}",
                suggestions=["检查文件编码和权限"]
            )
        
        score = 10
        found_sections = []
        missing_sections = []
        
        for section in self.REQUIRED_SKILL_MD_SECTIONS:
            if section in content:
                found_sections.append(section)
                score += 5
            else:
                missing_sections.append(section)
        
        optional_found = 0
        for section in self.OPTIONAL_SKILL_MD_SECTIONS:
            if section in content:
                optional_found += 1
                score += 2
        
        score = min(score, 40)
        
        suggestions = []
        if missing_sections:
            suggestions.append(f"添加缺失的必要章节: {', '.join(missing_sections)}")
        
        status = "excellent" if score >= 35 else "good" if score >= 28 else "fair" if score >= 20 else "poor"
        
        return AssessmentItem(
            name="SKILL.md 主文档",
            category=AssessmentCategory.DOCUMENTATION,
            score=score,
            max_score=40,
            status=status,
            message=f"找到 {len(found_sections)}/{len(self.REQUIRED_SKILL_MD_SECTIONS)} 必要章节",
            details={
                "found_sections": found_sections,
                "missing_sections": missing_sections,
                "optional_sections_found": optional_found,
                "content_length": len(content)
            },
            suggestions=suggestions
        )
    
    def _check_subskills(self) -> AssessmentItem:
        if not self.subskills_dir.exists():
            return AssessmentItem(
                name="子技能文档",
                category=AssessmentCategory.DOCUMENTATION,
                score=0,
                max_score=40,
                status="missing",
                message="subskills 目录不存在",
                suggestions=["创建 subskills 目录并添加子技能文档"]
            )
        
        subskill_files = list(self.subskills_dir.glob("*.md"))
        
        if not subskill_files:
            return AssessmentItem(
                name="子技能文档",
                category=AssessmentCategory.DOCUMENTATION,
                score=5,
                max_score=40,
                status="poor",
                message="未找到子技能文档",
                suggestions=["添加子技能文档以完善技能体系"]
            )
        
        valid_count = 0
        invalid_files = []
        missing_frontmatter = []
        
        for sf in subskill_files:
            try:
                content = sf.read_text(encoding='utf-8')
                if content.startswith('---'):
                    end_idx = content.find('---', 3)
                    if end_idx != -1:
                        frontmatter = content[3:end_idx].strip()
                        has_name = 'name:' in frontmatter or 'name =' in frontmatter
                        has_desc = 'description:' in frontmatter or 'description =' in frontmatter
                        
                        if has_name and has_desc:
                            valid_count += 1
                        else:
                            missing_frontmatter.append(sf.name)
                    else:
                        invalid_files.append(sf.name)
                else:
                    invalid_files.append(sf.name)
            except Exception:
                invalid_files.append(sf.name)
        
        total = len(subskill_files)
        score = min(40, valid_count * 3 + 10)
        
        suggestions = []
        if invalid_files:
            suggestions.append(f"修复格式错误的文档: {', '.join(invalid_files[:5])}")
        if missing_frontmatter:
            suggestions.append(f"添加缺失的 frontmatter 字段: {', '.join(missing_frontmatter[:5])}")
        
        status = "excellent" if valid_count == total else "good" if valid_count >= total * 0.8 else "fair" if valid_count >= total * 0.5 else "poor"
        
        return AssessmentItem(
            name="子技能文档",
            category=AssessmentCategory.DOCUMENTATION,
            score=score,
            max_score=40,
            status=status,
            message=f"有效文档 {valid_count}/{total}",
            details={
                "total_files": total,
                "valid_files": valid_count,
                "invalid_files": invalid_files,
                "missing_frontmatter": missing_frontmatter
            },
            suggestions=suggestions
        )
    
    def _check_readme(self) -> AssessmentItem:
        readme_path = self.skill_root / "README.md"
        
        if not readme_path.exists():
            return AssessmentItem(
                name="README 文档",
                category=AssessmentCategory.DOCUMENTATION,
                score=5,
                max_score=20,
                status="missing",
                message="README.md 文件不存在",
                suggestions=["创建 README.md 文件，提供项目概述和快速入门指南"]
            )
        
        try:
            content = readme_path.read_text(encoding='utf-8')
        except Exception:
            return AssessmentItem(
                name="README 文档",
                category=AssessmentCategory.DOCUMENTATION,
                score=5,
                max_score=20,
                status="error",
                message="读取 README.md 失败",
                suggestions=["检查文件编码和权限"]
            )
        
        score = 10
        readme_sections = ["安装", "使用", "配置", "示例", "贡献", "许可"]
        found = sum(1 for s in readme_sections if s in content)
        score += found * 2
        score = min(score, 20)
        
        status = "good" if score >= 15 else "fair" if score >= 10 else "poor"
        
        return AssessmentItem(
            name="README 文档",
            category=AssessmentCategory.DOCUMENTATION,
            score=score,
            max_score=20,
            status=status,
            message=f"内容长度: {len(content)} 字符",
            details={
                "content_length": len(content),
                "sections_found": found
            }
        )


class ScriptChecker:
    CORE_SCRIPTS = [
        "unified_script_entry.py",
        "start_services.py",
        "stop_services.py",
        "init_db.py",
        "health_check.py",
        "check_environment.py"
    ]
    
    SCRIPT_CATEGORIES = ["core", "analysis", "pipeline", "test", "utils", "monitoring", "optimization", "requirements"]
    
    def __init__(self, skillscripts_dir: Path):
        self.skillscripts_dir = skillscripts_dir
    
    def check(self) -> CategoryResult:
        items = []
        total_score = 0
        max_score = 0
        
        core_item = self._check_core_scripts()
        items.append(core_item)
        total_score += core_item.score
        max_score += core_item.max_score
        
        all_item = self._check_all_scripts()
        items.append(all_item)
        total_score += all_item.score
        max_score += all_item.max_score
        
        syntax_item = self._check_syntax()
        items.append(syntax_item)
        total_score += syntax_item.score
        max_score += syntax_item.max_score
        
        return CategoryResult(
            category=AssessmentCategory.SCRIPTS,
            score=total_score,
            max_score=max_score,
            items=items,
            weight=0.30
        )
    
    def _check_core_scripts(self) -> AssessmentItem:
        core_dir = self.skillscripts_dir / "core"
        missing = []
        available = []
        
        for script in self.CORE_SCRIPTS:
            script_path = core_dir / script
            if script_path.exists():
                available.append(script)
            else:
                missing.append(script)
        
        total = len(self.CORE_SCRIPTS)
        score = len(available) * 5
        max_score = total * 5
        
        suggestions = []
        if missing:
            suggestions.append(f"恢复缺失的核心脚本: {', '.join(missing)}")
        
        status = "excellent" if len(available) == total else "good" if len(available) >= total * 0.8 else "fair" if len(available) >= total * 0.5 else "critical"
        
        return AssessmentItem(
            name="核心脚本检查",
            category=AssessmentCategory.SCRIPTS,
            score=score,
            max_score=max_score,
            status=status,
            message=f"可用: {len(available)}/{total}",
            details={
                "available": available,
                "missing": missing
            },
            suggestions=suggestions
        )
    
    def _check_all_scripts(self) -> AssessmentItem:
        all_scripts = list(self.skillscripts_dir.rglob("*.py"))
        test_scripts = [s for s in all_scripts if "test" in str(s).lower() or s.name.startswith("test_")]
        main_scripts = [s for s in all_scripts if s not in test_scripts]
        
        categories_found = set()
        for script in main_scripts:
            for cat in self.SCRIPT_CATEGORIES:
                if cat in str(script).lower():
                    categories_found.add(cat)
        
        score = min(30, len(main_scripts) * 0.5 + len(categories_found) * 3)
        max_score = 30
        
        status = "excellent" if len(categories_found) >= 6 else "good" if len(categories_found) >= 4 else "fair"
        
        return AssessmentItem(
            name="脚本覆盖度",
            category=AssessmentCategory.SCRIPTS,
            score=score,
            max_score=max_score,
            status=status,
            message=f"主脚本: {len(main_scripts)}, 测试脚本: {len(test_scripts)}, 分类: {len(categories_found)}/{len(self.SCRIPT_CATEGORIES)}",
            details={
                "total_scripts": len(all_scripts),
                "main_scripts": len(main_scripts),
                "test_scripts": len(test_scripts),
                "categories_found": list(categories_found)
            }
        )
    
    def _check_syntax(self) -> AssessmentItem:
        all_scripts = list(self.skillscripts_dir.rglob("*.py"))
        syntax_errors = []
        checked = 0
        
        for script in all_scripts[:100]:
            try:
                content = script.read_text(encoding='utf-8')
                ast.parse(content)
                checked += 1
            except SyntaxError as e:
                syntax_errors.append({
                    "file": str(script.relative_to(self.skillscripts_dir)),
                    "line": e.lineno,
                    "message": str(e.msg)
                })
            except Exception:
                pass
        
        total = min(len(all_scripts), 100)
        error_count = len(syntax_errors)
        score = max(0, (total - error_count) * 0.3)
        max_score = 30
        
        suggestions = []
        if syntax_errors:
            for err in syntax_errors[:3]:
                suggestions.append(f"修复语法错误: {err['file']}:{err['line']} - {err['message']}")
        
        status = "excellent" if error_count == 0 else "good" if error_count <= 2 else "fair" if error_count <= 5 else "poor"
        
        return AssessmentItem(
            name="语法检查",
            category=AssessmentCategory.SCRIPTS,
            score=score,
            max_score=max_score,
            status=status,
            message=f"检查: {checked}, 错误: {error_count}",
            details={
                "checked": checked,
                "errors": syntax_errors[:10]
            },
            suggestions=suggestions
        )


class ConfigurationChecker:
    REQUIRED_CONFIG_KEYS = {
        "database": ["host", "port", "name"],
        "backend": ["host", "port"],
        "frontend": ["host", "port"]
    }
    
    def __init__(self, skill_root: Path):
        self.skill_root = skill_root
        self.config_dir = skill_root / "config"
        self.env_file = skill_root / ".env"
        self.env_example = skill_root / ".env.example"
        self.docker_compose = skill_root / "docker-compose.yml"
    
    def check(self) -> CategoryResult:
        items = []
        total_score = 0
        max_score = 0
        
        env_item = self._check_env_files()
        items.append(env_item)
        total_score += env_item.score
        max_score += env_item.max_score
        
        docker_item = self._check_docker_config()
        items.append(docker_item)
        total_score += docker_item.score
        max_score += docker_item.max_score
        
        consistency_item = self._check_config_consistency()
        items.append(consistency_item)
        total_score += consistency_item.score
        max_score += consistency_item.max_score
        
        return CategoryResult(
            category=AssessmentCategory.CONFIGURATION,
            score=total_score,
            max_score=max_score,
            items=items,
            weight=0.20
        )
    
    def _check_env_files(self) -> AssessmentItem:
        score = 0
        max_score = 35
        details = {}
        suggestions = []
        
        if self.env_example.exists():
            score += 10
            details["env_example_exists"] = True
            try:
                content = self.env_example.read_text(encoding='utf-8')
                details["env_example_lines"] = len(content.strip().split('\n'))
            except Exception:
                pass
        else:
            details["env_example_exists"] = False
            suggestions.append("创建 .env.example 文件作为环境变量模板")
        
        if self.env_file.exists():
            score += 10
            details["env_exists"] = True
            try:
                content = self.env_file.read_text(encoding='utf-8')
                details["env_lines"] = len(content.strip().split('\n'))
            except Exception:
                pass
        else:
            details["env_exists"] = False
            suggestions.append("创建 .env 文件配置环境变量")
        
        if self.env_example.exists() and self.env_file.exists():
            try:
                example_vars = self._parse_env_file(self.env_example)
                env_vars = self._parse_env_file(self.env_file)
                
                missing = example_vars - env_vars
                if not missing:
                    score += 15
                else:
                    score += 10
                    details["missing_env_vars"] = list(missing)
                    suggestions.append(f"在 .env 中添加缺失的环境变量: {', '.join(list(missing)[:5])}")
            except Exception:
                score += 5
        
        status = "excellent" if score >= 30 else "good" if score >= 20 else "fair" if score >= 10 else "poor"
        
        return AssessmentItem(
            name="环境配置文件",
            category=AssessmentCategory.CONFIGURATION,
            score=score,
            max_score=max_score,
            status=status,
            message=f"得分: {score}/{max_score}",
            details=details,
            suggestions=suggestions
        )
    
    def _parse_env_file(self, path: Path) -> Set[str]:
        variables = set()
        try:
            content = path.read_text(encoding='utf-8')
            for line in content.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    var_name = line.split('=')[0].strip()
                    variables.add(var_name)
        except Exception:
            pass
        return variables
    
    def _check_docker_config(self) -> AssessmentItem:
        score = 0
        max_score = 30
        details = {}
        suggestions = []
        
        if self.docker_compose.exists():
            score += 15
            details["docker_compose_exists"] = True
            
            try:
                import yaml
                content = self.docker_compose.read_text(encoding='utf-8')
                config = yaml.safe_load(content)
                
                services = config.get('services', {})
                details["services"] = list(services.keys())
                score += min(15, len(services) * 5)
            except ImportError:
                details["yaml_parse"] = "PyYAML not installed"
                score += 5
            except Exception as e:
                details["yaml_error"] = str(e)
                suggestions.append("修复 docker-compose.yml 格式错误")
        else:
            details["docker_compose_exists"] = False
            suggestions.append("创建 docker-compose.yml 以简化服务部署")
        
        status = "excellent" if score >= 25 else "good" if score >= 15 else "fair" if score >= 10 else "poor"
        
        return AssessmentItem(
            name="Docker 配置",
            category=AssessmentCategory.CONFIGURATION,
            score=score,
            max_score=max_score,
            status=status,
            message=f"得分: {score}/{max_score}",
            details=details,
            suggestions=suggestions
        )
    
    def _check_config_consistency(self) -> AssessmentItem:
        score = 20
        max_score = 35
        details = {}
        suggestions = []
        
        backend_path = self.skill_root / "backend"
        frontend_path = self.skill_root / "frontend"
        
        if backend_path.exists():
            requirements = backend_path / "requirements.txt"
            if requirements.exists():
                details["backend_requirements"] = True
                try:
                    content = requirements.read_text(encoding='utf-8')
                    details["backend_deps_count"] = len([l for l in content.strip().split('\n') if l.strip()])
                except Exception:
                    pass
            else:
                details["backend_requirements"] = False
                suggestions.append("添加 backend/requirements.txt")
                score -= 5
        
        if frontend_path.exists():
            package_json = frontend_path / "package.json"
            if package_json.exists():
                details["frontend_package_json"] = True
                try:
                    content = package_json.read_text(encoding='utf-8')
                    pkg = json.loads(content)
                    deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                    details["frontend_deps_count"] = len(deps)
                except Exception:
                    pass
            else:
                details["frontend_package_json"] = False
                suggestions.append("添加 frontend/package.json")
                score -= 5
        
        score = max(0, score)
        status = "good" if score >= 20 else "fair" if score >= 10 else "poor"
        
        return AssessmentItem(
            name="配置一致性",
            category=AssessmentCategory.CONFIGURATION,
            score=score,
            max_score=max_score,
            status=status,
            message=f"得分: {score}/{max_score}",
            details=details,
            suggestions=suggestions
        )


class PathStructureChecker:
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

    def __init__(self, skill_root: Path):
        self.skill_root = skill_root
        self.scripts_dir = get_path_config().SCRIPTS_DIR

    def check(self) -> CategoryResult:
        items = []
        total_score = 0
        max_score = 0

        dirs_item = self._check_required_directories()
        items.append(dirs_item)
        total_score += dirs_item.score
        max_score += dirs_item.max_score

        reports_item = self._check_reports_structure()
        items.append(reports_item)
        total_score += reports_item.score
        max_score += reports_item.max_score

        return CategoryResult(
            category=AssessmentCategory.PATH_STRUCTURE,
            score=total_score,
            max_score=max_score,
            items=items,
            weight=0.15
        )

    def _check_required_directories(self) -> AssessmentItem:
        existing = []
        missing = []

        for dir_path in self.REQUIRED_DIRECTORIES:
            if dir_path in ["subskills", "backend", "frontend"]:
                full_path = self.skill_root / dir_path
            else:
                full_path = self.scripts_dir / dir_path
            if full_path.exists() and full_path.is_dir():
                existing.append(dir_path)
            else:
                missing.append(dir_path)

        total = len(self.REQUIRED_DIRECTORIES)
        score = len(existing) * 5
        max_score = total * 5

        suggestions = []
        if missing:
            suggestions.append(f"创建缺失目录: {', '.join(missing[:5])}")

        status = "excellent" if len(existing) == total else "good" if len(existing) >= total * 0.8 else "fair" if len(existing) >= total * 0.5 else "critical"

        return AssessmentItem(
            name="目录结构检查",
            category=AssessmentCategory.PATH_STRUCTURE,
            score=score,
            max_score=max_score,
            status=status,
            message=f"存在: {len(existing)}/{total}",
            details={
                "existing": existing,
                "missing": missing
            },
            suggestions=suggestions
        )

    def _check_reports_structure(self) -> AssessmentItem:
        reports_dirs = [
            self.scripts_dir / "core" / "reports",
            self.scripts_dir / "analysis" / "reports"
        ]
        
        existing = []
        for dir_path in reports_dirs:
            full_path = self.skill_root / dir_path
            if full_path.exists():
                existing.append(dir_path)
        
        score = len(existing) * 10
        max_score = 20
        
        status = "good" if score >= 20 else "fair" if score >= 10 else "poor"
        
        return AssessmentItem(
            name="报告目录结构",
            category=AssessmentCategory.PATH_STRUCTURE,
            score=score,
            max_score=max_score,
            status=status,
            message=f"存在: {len(existing)}/{len(reports_dirs)}",
            details={
                "existing": existing
            }
        )


class MetadataChecker:
    def __init__(self, skill_root: Path):
        self.skill_root = skill_root
        self.skill_md_path = skill_root / "SKILL.md"
    
    def check(self) -> CategoryResult:
        items = []
        total_score = 0
        max_score = 0
        
        frontmatter_item = self._check_frontmatter()
        items.append(frontmatter_item)
        total_score += frontmatter_item.score
        max_score += frontmatter_item.max_score
        
        version_item = self._check_version_info()
        items.append(version_item)
        total_score += version_item.score
        max_score += version_item.max_score
        
        return CategoryResult(
            category=AssessmentCategory.METADATA,
            score=total_score,
            max_score=max_score,
            items=items,
            weight=0.10
        )
    
    def _check_frontmatter(self) -> AssessmentItem:
        if not self.skill_md_path.exists():
            return AssessmentItem(
                name="SKILL.md Frontmatter",
                category=AssessmentCategory.METADATA,
                score=0,
                max_score=50,
                status="missing",
                message="SKILL.md 不存在",
                suggestions=["创建 SKILL.md 文件"]
            )
        
        try:
            content = self.skill_md_path.read_text(encoding='utf-8')
        except Exception:
            return AssessmentItem(
                name="SKILL.md Frontmatter",
                category=AssessmentCategory.METADATA,
                score=0,
                max_score=50,
                status="error",
                message="读取 SKILL.md 失败",
                suggestions=["检查文件编码"]
            )
        
        if not content.startswith('---'):
            return AssessmentItem(
                name="SKILL.md Frontmatter",
                category=AssessmentCategory.METADATA,
                score=10,
                max_score=50,
                status="poor",
                message="缺少 YAML frontmatter",
                suggestions=["添加 YAML frontmatter 头部，包含 name 和 description"]
            )
        
        end_idx = content.find('---', 3)
        if end_idx == -1:
            return AssessmentItem(
                name="SKILL.md Frontmatter",
                category=AssessmentCategory.METADATA,
                score=10,
                max_score=50,
                status="poor",
                message="Frontmatter 格式错误",
                suggestions=["修复 frontmatter 格式，确保以 --- 结尾"]
            )
        
        frontmatter = content[3:end_idx].strip()
        score = 20
        
        has_name = 'name:' in frontmatter or 'name =' in frontmatter
        has_desc = 'description:' in frontmatter or 'description =' in frontmatter
        
        if has_name:
            score += 15
        if has_desc:
            score += 15
        
        suggestions = []
        if not has_name:
            suggestions.append("在 frontmatter 中添加 name 字段")
        if not has_desc:
            suggestions.append("在 frontmatter 中添加 description 字段")
        
        status = "excellent" if score >= 45 else "good" if score >= 30 else "fair" if score >= 20 else "poor"
        
        return AssessmentItem(
            name="SKILL.md Frontmatter",
            category=AssessmentCategory.METADATA,
            score=score,
            max_score=50,
            status=status,
            message=f"name: {'✓' if has_name else '✗'}, description: {'✓' if has_desc else '✗'}",
            details={
                "has_name": has_name,
                "has_description": has_desc
            },
            suggestions=suggestions
        )
    
    def _check_version_info(self) -> AssessmentItem:
        score = 0
        max_score = 50
        details = {}
        suggestions = []
        
        version_files = [
            self.skill_root / "VERSION",
            self.skill_root / "version.txt",
            self.skill_root / "pyproject.toml",
            self.skill_root / "setup.py"
        ]
        
        for vf in version_files:
            if vf.exists():
                details[str(vf.name)] = True
                score += 15
        
        if self.skill_md_path.exists():
            try:
                content = self.skill_md_path.read_text(encoding='utf-8')
                if re.search(r'version|版本', content, re.IGNORECASE):
                    score += 10
                    details["version_in_skill_md"] = True
            except Exception:
                pass
        
        score = min(score, max_score)
        status = "good" if score >= 30 else "fair" if score >= 15 else "poor"
        
        if score < 30:
            suggestions.append("添加版本信息文件或在文档中声明版本")
        
        return AssessmentItem(
            name="版本信息",
            category=AssessmentCategory.METADATA,
            score=score,
            max_score=max_score,
            status=status,
            message=f"得分: {score}/{max_score}",
            details=details,
            suggestions=suggestions
        )


class SkillHealthAssessor:
    def __init__(self, skill_root: Optional[Path] = None, verbose: bool = True):
        self.skill_root = skill_root or PROJECT_ROOT / ".trae" / "skills" / "sanliu"
        self.skillscripts_dir = self.skill_root / "skillscripts"
        self.verbose = verbose
        self._setup_logging()
    
    def _setup_logging(self):
        level = logging.DEBUG if self.verbose else logging.WARNING
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _log(self, message: str, level: str = "info"):
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
    
    def assess(self) -> HealthAssessmentReport:
        start_time = time.time()
        self._log("开始技能健康度评估...")
        
        category_results = []
        
        self._log("检查文档完整性...")
        doc_checker = DocumentationChecker(self.skill_root)
        category_results.append(doc_checker.check())
        
        self._log("检查脚本可用性...")
        script_checker = ScriptChecker(self.skillscripts_dir)
        category_results.append(script_checker.check())
        
        self._log("检查配置一致性...")
        config_checker = ConfigurationChecker(self.skill_root)
        category_results.append(config_checker.check())
        
        self._log("检查路径结构...")
        path_checker = PathStructureChecker(self.skill_root)
        category_results.append(path_checker.check())
        
        self._log("检查元数据...")
        metadata_checker = MetadataChecker(self.skill_root)
        category_results.append(metadata_checker.check())
        
        overall_score = self._calculate_overall_score(category_results)
        health_level = self._determine_health_level(overall_score)
        
        summary = self._generate_summary(category_results)
        recommendations = self._generate_recommendations(category_results)
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        self._log(f"评估完成，健康度评分: {overall_score:.2f}/100", "success")
        
        return HealthAssessmentReport(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            overall_score=overall_score,
            health_level=health_level,
            category_results=category_results,
            summary=summary,
            recommendations=recommendations,
            duration_ms=duration_ms
        )
    
    def _calculate_overall_score(self, category_results: List[CategoryResult]) -> float:
        weighted_sum = 0
        total_weight = 0
        
        for cr in category_results:
            percentage = cr.percentage
            weighted_sum += percentage * cr.weight
            total_weight += cr.weight
        
        return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0
    
    def _determine_health_level(self, score: float) -> HealthLevel:
        if score >= 90:
            return HealthLevel.EXCELLENT
        elif score >= 75:
            return HealthLevel.GOOD
        elif score >= 60:
            return HealthLevel.FAIR
        elif score >= 40:
            return HealthLevel.POOR
        else:
            return HealthLevel.CRITICAL
    
    def _generate_summary(self, category_results: List[CategoryResult]) -> Dict[str, Any]:
        summary = {
            "total_categories": len(category_results),
            "categories": {}
        }
        
        for cr in category_results:
            summary["categories"][cr.category.value] = {
                "score": cr.score,
                "max_score": cr.max_score,
                "percentage": round(cr.percentage, 2),
                "weight": cr.weight,
                "item_count": len(cr.items)
            }
        
        return summary
    
    def _generate_recommendations(self, category_results: List[CategoryResult]) -> List[str]:
        all_recommendations = []
        
        for cr in category_results:
            for item in cr.items:
                if item.score < item.max_score * 0.8:
                    all_recommendations.extend(item.suggestions)
        
        seen = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:15]
    
    def generate_json_report(self, report: HealthAssessmentReport) -> str:
        return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
    
    def generate_markdown_report(self, report: HealthAssessmentReport) -> str:
        lines = [
            "# 技能健康度评估报告",
            "",
            f"**评估时间**: {report.timestamp}",
            f"**健康度评分**: {report.overall_score}/100",
            f"**健康等级**: {self._get_health_level_display(report.health_level)}",
            f"**评估耗时**: {report.duration_ms}ms",
            "",
            "---",
            "",
            "## 📊 分类评估结果",
            ""
        ]
        
        for cr in report.category_results:
            category_name = self._get_category_display(cr.category)
            lines.extend([
                f"### {category_name}",
                "",
                f"| 指标 | 得分 | 满分 | 完成度 | 状态 |",
                f"|------|------|------|--------|------|"
            ])
            
            for item in cr.items:
                status_icon = self._get_status_icon(item.status)
                lines.append(
                    f"| {item.name} | {item.score:.1f} | {item.max_score:.1f} | {item.percentage:.1f}% | {status_icon} |"
                )
            
            lines.extend([
                "",
                f"**分类得分**: {cr.score:.1f}/{cr.max_score:.1f} ({cr.percentage:.1f}%)",
                ""
            ])
        
        lines.extend([
            "---",
            "",
            "## 📈 评估摘要",
            ""
        ])
        
        for cat_name, cat_data in report.summary["categories"].items():
            lines.append(f"- **{cat_name}**: {cat_data['percentage']:.1f}%")
        
        if report.recommendations:
            lines.extend([
                "",
                "---",
                "",
                "## 💡 改进建议",
                ""
            ])
            
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")
        
        lines.extend([
            "",
            "---",
            "",
            "*报告由技能健康度评估器自动生成*"
        ])
        
        return "\n".join(lines)
    
    def _get_health_level_display(self, level: HealthLevel) -> str:
        displays = {
            HealthLevel.EXCELLENT: "🌟 优秀 (Excellent)",
            HealthLevel.GOOD: "✅ 良好 (Good)",
            HealthLevel.FAIR: "⚠️ 一般 (Fair)",
            HealthLevel.POOR: "❌ 较差 (Poor)",
            HealthLevel.CRITICAL: "🚨 严重 (Critical)"
        }
        return displays.get(level, str(level.value))
    
    def _get_category_display(self, category: AssessmentCategory) -> str:
        displays = {
            AssessmentCategory.DOCUMENTATION: "📚 文档完整性",
            AssessmentCategory.SCRIPTS: "🔧 脚本可用性",
            AssessmentCategory.CONFIGURATION: "⚙️ 配置一致性",
            AssessmentCategory.PATH_STRUCTURE: "📁 路径结构",
            AssessmentCategory.DEPENDENCIES: "📦 依赖管理",
            AssessmentCategory.METADATA: "📋 元数据"
        }
        return displays.get(category, category.value)
    
    def _get_status_icon(self, status: str) -> str:
        icons = {
            "excellent": "🌟",
            "good": "✅",
            "fair": "⚠️",
            "poor": "❌",
            "critical": "🚨",
            "missing": "❓",
            "error": "💥"
        }
        return icons.get(status, "❓")


def print_console_report(report: HealthAssessmentReport):
    print("\n" + "=" * 70)
    print("🏥 技能健康度评估报告")
    print("=" * 70)
    print(f"⏰ 评估时间: {report.timestamp}")
    print(f"⏱️ 评估耗时: {report.duration_ms}ms")
    print(f"💯 健康度评分: {report.overall_score}/100")
    
    level_displays = {
        HealthLevel.EXCELLENT: "🌟 优秀",
        HealthLevel.GOOD: "✅ 良好",
        HealthLevel.FAIR: "⚠️ 一般",
        HealthLevel.POOR: "❌ 较差",
        HealthLevel.CRITICAL: "🚨 严重"
    }
    print(f"📊 健康等级: {level_displays.get(report.health_level, report.health_level.value)}")
    
    print("-" * 70)
    print("📋 分类评估:")
    
    for cr in report.category_results:
        status = "✅" if cr.percentage >= 80 else "⚠️" if cr.percentage >= 60 else "❌"
        print(f"   {status} {cr.category.value}: {cr.percentage:.1f}%")
    
    if report.recommendations:
        print("-" * 70)
        print("💡 改进建议:")
        for i, rec in enumerate(report.recommendations[:5], 1):
            print(f"   {i}. {rec}")
    
    print("=" * 70)
    
    if report.health_level in (HealthLevel.EXCELLENT, HealthLevel.GOOD):
        print("🎉 技能健康状态良好！")
    elif report.health_level == HealthLevel.FAIR:
        print("⚠️ 技能健康状态一般，建议优化。")
    else:
        print("❌ 技能健康状态较差，请尽快修复问题。")
    
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="技能健康度评估器 - 评估技能系统的整体健康状态",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python skill_health_assessor.py                    # 运行完整评估
  python skill_health_assessor.py --json             # JSON 格式输出
  python skill_health_assessor.py --markdown         # Markdown 格式输出
  python skill_health_assessor.py -v                 # 详细输出
  python skill_health_assessor.py --output report.md --markdown  # 保存 Markdown 报告

评估维度:
  documentation  - 文档完整性检查
  scripts        - 脚本可用性检查
  configuration  - 配置一致性检查
  path_structure - 路径结构检查
  metadata       - 元数据检查
        """
    )
    
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--markdown", action="store_true", help="输出 Markdown 格式")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--output", "-o", type=str, help="输出报告文件路径")
    parser.add_argument("--skill-root", type=str, help="技能根目录路径")
    
    args = parser.parse_args()
    
    skill_root = Path(args.skill_root) if args.skill_root else None
    
    assessor = SkillHealthAssessor(skill_root=skill_root, verbose=args.verbose and not args.json)
    report = assessor.assess()
    
    if args.json:
        output = assessor.generate_json_report(report)
        print(output)
    elif args.markdown:
        output = assessor.generate_markdown_report(report)
        print(output)
    else:
        print_console_report(report)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if args.json or args.output.endswith('.json'):
            content = assessor.generate_json_report(report)
        else:
            content = assessor.generate_markdown_report(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if not args.json and not args.markdown:
            print(f"\n📄 报告已保存至: {args.output}")
    
    return 0 if report.health_level in (HealthLevel.EXCELLENT, HealthLevel.GOOD, HealthLevel.FAIR) else 1


if __name__ == "__main__":
    sys.exit(main())
