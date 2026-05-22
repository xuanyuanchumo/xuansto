#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能文档路径验证器 - Sanliu 技能

功能：
- 从 markdown 文档中提取所有脚本调用路径
- 检查提取的路径是否存在且可执行
- 自动更正错误的路径（如 scripts/ -> skillscripts/）
- 生成详细的验证结果和修复建议报告
"""

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from .enhanced_path_config_manager import (
        create_path_manager, PathKey, EnhancedSkillPathManager
    )
except ImportError:
    from enhanced_path_config_manager import (
        create_path_manager, PathKey, EnhancedSkillPathManager
    )


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PathStatus(Enum):
    """路径状态枚举"""
    VALID = "valid"
    MISSING = "missing"
    WRONG_PREFIX = "wrong_prefix"
    INVALID_FORMAT = "invalid_format"


class FixAction(Enum):
    """修复动作枚举"""
    NONE = "none"
    FIX_PREFIX = "fix_prefix"
    CREATE_FILE = "create_file"
    MANUAL_FIX = "manual_fix"


@dataclass
class ExtractedPath:
    """提取的路径信息"""
    raw_path: str
    script_name: str
    script_type: str
    line_number: int
    context: str
    source_file: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PathValidationResult:
    """路径验证结果"""
    extracted_path: ExtractedPath
    status: PathStatus
    actual_path: Optional[Path] = None
    exists: bool = False
    fix_action: FixAction = FixAction.NONE
    suggested_fix: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_path": self.extracted_path.raw_path,
            "script_name": self.extracted_path.script_name,
            "script_type": self.extracted_path.script_type,
            "line_number": self.extracted_path.line_number,
            "source_file": self.extracted_path.source_file,
            "status": self.status.value,
            "actual_path": str(self.actual_path) if self.actual_path else None,
            "exists": self.exists,
            "fix_action": self.fix_action.value,
            "suggested_fix": self.suggested_fix,
            "error_message": self.error_message
        }


@dataclass
class DocumentValidationReport:
    """文档验证报告"""
    source_file: str
    total_paths: int
    valid_paths: int
    invalid_paths: int
    wrong_prefix_paths: int
    results: List[PathValidationResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_file": self.source_file,
            "total_paths": self.total_paths,
            "valid_paths": self.valid_paths,
            "invalid_paths": self.invalid_paths,
            "wrong_prefix_paths": self.wrong_prefix_paths,
            "results": [r.to_dict() for r in self.results]
        }


@dataclass
class ValidationSummary:
    """验证汇总报告"""
    timestamp: str
    skill_root: str
    documents_scanned: int
    total_paths_found: int
    valid_paths: int
    invalid_paths: int
    wrong_prefix_paths: int
    health_score: float
    document_reports: List[DocumentValidationReport] = field(default_factory=list)
    fix_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "skill_root": self.skill_root,
            "documents_scanned": self.documents_scanned,
            "total_paths_found": self.total_paths_found,
            "valid_paths": self.valid_paths,
            "invalid_paths": self.invalid_paths,
            "wrong_prefix_paths": self.wrong_prefix_paths,
            "health_score": self.health_score,
            "document_reports": [r.to_dict() for r in self.document_reports],
            "fix_suggestions": self.fix_suggestions
        }


class ScriptPathExtractor:
    """脚本路径提取器"""
    
    PATH_PATTERNS = [
        re.compile(r'python\s+(skillscripts/[^\s\'"`]+\.py)', re.IGNORECASE),
        re.compile(r'python\s+(scripts/[^\s\'"`]+\.py)', re.IGNORECASE),
    ]
    
    SCRIPT_TYPE_MAPPING = {
        "core": "core",
        "pipeline": "pipeline",
        "test": "test",
        "tests": "test",
        "analysis": "analysis",
        "optimization": "optimization",
        "requirements": "requirements",
        "utils": "utils",
        "utility": "utils",
        "monitoring": "monitoring",
    }
    
    def __init__(self, path_manager: EnhancedSkillPathManager):
        self.path_manager = path_manager
    
    def extract_from_file(self, file_path: Path) -> List[ExtractedPath]:
        """
        从 markdown 文件中提取所有脚本路径
        
        Args:
            file_path: markdown 文件路径
            
        Returns:
            提取的路径列表
        """
        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return []
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, 错误: {e}")
            return []
        
        return self.extract_from_content(content, str(file_path))
    
    def extract_from_content(self, content: str, source_file: str) -> List[ExtractedPath]:
        """
        从内容中提取所有脚本路径
        
        Args:
            content: 文档内容
            source_file: 源文件路径
            
        Returns:
            提取的路径列表
        """
        extracted = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern in self.PATH_PATTERNS:
                matches = pattern.finditer(line)
                for match in matches:
                    raw_path = match.group(1)
                    
                    extracted_path = self._parse_path(
                        raw_path, line_num, line.strip(), source_file
                    )
                    if extracted_path:
                        extracted.append(extracted_path)
        
        return extracted
    
    def _parse_path(
        self, 
        raw_path: str, 
        line_number: int, 
        context: str, 
        source_file: str
    ) -> Optional[ExtractedPath]:
        """解析路径信息"""
        parts = raw_path.split('/')
        
        if len(parts) < 2:
            return None
        
        prefix = parts[0].lower()
        script_type = "utils"
        
        if len(parts) >= 3:
            script_type = self.SCRIPT_TYPE_MAPPING.get(parts[1].lower(), "utils")
        
        script_name = parts[-1].replace('.py', '')
        
        return ExtractedPath(
            raw_path=raw_path,
            script_name=script_name,
            script_type=script_type,
            line_number=line_number,
            context=context,
            source_file=source_file
        )


class PathValidator:
    """路径验证器"""
    
    VALID_PREFIX = "skillscripts"
    INVALID_PREFIX = "scripts"
    
    def __init__(self, path_manager: EnhancedSkillPathManager):
        self.path_manager = path_manager
    
    def validate_path(self, extracted: ExtractedPath) -> PathValidationResult:
        """
        验证单个路径
        
        Args:
            extracted: 提取的路径信息
            
        Returns:
            验证结果
        """
        raw_path = extracted.raw_path
        prefix = raw_path.split('/')[0].lower()
        
        if prefix == self.INVALID_PREFIX:
            corrected_path = self._fix_prefix(raw_path)
            actual_path = self._resolve_corrected_path(corrected_path, extracted.script_type)
            
            return PathValidationResult(
                extracted_path=extracted,
                status=PathStatus.WRONG_PREFIX,
                actual_path=actual_path,
                exists=actual_path.exists() if actual_path else False,
                fix_action=FixAction.FIX_PREFIX,
                suggested_fix=corrected_path,
                error_message=f"路径前缀错误: '{prefix}' 应为 '{self.VALID_PREFIX}'"
            )
        
        if prefix == self.VALID_PREFIX:
            actual_path = self._resolve_path(raw_path, extracted.script_type)
            
            if actual_path and actual_path.exists():
                return PathValidationResult(
                    extracted_path=extracted,
                    status=PathStatus.VALID,
                    actual_path=actual_path,
                    exists=True,
                    fix_action=FixAction.NONE
                )
            else:
                return PathValidationResult(
                    extracted_path=extracted,
                    status=PathStatus.MISSING,
                    actual_path=actual_path,
                    exists=False,
                    fix_action=FixAction.CREATE_FILE,
                    error_message=f"脚本文件不存在: {actual_path}"
                )
        
        return PathValidationResult(
            extracted_path=extracted,
            status=PathStatus.INVALID_FORMAT,
            fix_action=FixAction.MANUAL_FIX,
            error_message=f"无法识别的路径格式: {raw_path}"
        )
    
    def _fix_prefix(self, raw_path: str) -> str:
        """修复路径前缀"""
        parts = raw_path.split('/')
        parts[0] = self.VALID_PREFIX
        return '/'.join(parts)
    
    def _resolve_path(self, raw_path: str, script_type: str) -> Optional[Path]:
        """解析路径到实际文件系统路径"""
        try:
            parts = raw_path.split('/')
            if len(parts) < 2:
                return None
            
            script_name = parts[-1].replace('.py', '')
            return self.path_manager.get_script_path(script_name, script_type)
        except Exception as e:
            logger.debug(f"解析路径失败: {raw_path}, 错误: {e}")
            return None
    
    def _resolve_corrected_path(self, corrected_path: str, script_type: str) -> Optional[Path]:
        """解析修复后的路径"""
        return self._resolve_path(corrected_path, script_type)


class DocumentPathFixer:
    """文档路径修复器"""
    
    def __init__(self, path_manager: EnhancedSkillPathManager):
        self.path_manager = path_manager
        self.validator = PathValidator(path_manager)
    
    def fix_document(
        self, 
        file_path: Path, 
        dry_run: bool = True,
        backup: bool = True
    ) -> Dict[str, Any]:
        """
        修复文档中的路径
        
        Args:
            file_path: 文档文件路径
            dry_run: 是否只预览不实际修改
            backup: 是否创建备份
            
        Returns:
            修复结果
        """
        result = {
            "file": str(file_path),
            "dry_run": dry_run,
            "backup_created": False,
            "fixes_applied": [],
            "errors": []
        }
        
        if not file_path.exists():
            result["errors"].append(f"文件不存在: {file_path}")
            return result
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            result["errors"].append(f"读取文件失败: {e}")
            return result
        
        extractor = ScriptPathExtractor(self.path_manager)
        extracted_paths = extractor.extract_from_file(file_path)
        
        fixes = {}
        for extracted in extracted_paths:
            validation = self.validator.validate_path(extracted)
            
            if validation.status == PathStatus.WRONG_PREFIX and validation.suggested_fix:
                old_path = extracted.raw_path
                new_path = validation.suggested_fix
                fixes[old_path] = new_path
                result["fixes_applied"].append({
                    "line": extracted.line_number,
                    "old": old_path,
                    "new": new_path
                })
        
        if not fixes:
            return result
        
        new_content = content
        for old_path, new_path in fixes.items():
            new_content = new_content.replace(old_path, new_path)
        
        if dry_run:
            return result
        
        if backup:
            backup_path = file_path.with_suffix(f'.bak.{datetime.now().strftime("%Y%m%d%H%M%S")}')
            try:
                backup_path.write_text(content, encoding='utf-8')
                result["backup_created"] = True
                result["backup_path"] = str(backup_path)
            except Exception as e:
                result["errors"].append(f"创建备份失败: {e}")
                return result
        
        try:
            file_path.write_text(new_content, encoding='utf-8')
        except Exception as e:
            result["errors"].append(f"写入文件失败: {e}")
        
        return result


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, path_manager: EnhancedSkillPathManager):
        self.path_manager = path_manager
    
    def generate_json_report(
        self, 
        summary: ValidationSummary, 
        output_path: Path
    ) -> None:
        """生成 JSON 格式报告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"JSON 报告已生成: {output_path}")
    
    def generate_markdown_report(
        self, 
        summary: ValidationSummary, 
        output_path: Path
    ) -> None:
        """生成 Markdown 格式报告"""
        lines = [
            "# 技能文档路径验证报告",
            "",
            f"> 生成时间: {summary.timestamp}",
            f"> 技能根目录: {summary.skill_root}",
            "",
            "## 验证概览",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 扫描文档数 | {summary.documents_scanned} |",
            f"| 发现路径数 | {summary.total_paths_found} |",
            f"| 有效路径 | {summary.valid_paths} |",
            f"| 无效路径 | {summary.invalid_paths} |",
            f"| 前缀错误 | {summary.wrong_prefix_paths} |",
            f"| 健康分数 | {summary.health_score:.1%} |",
            "",
        ]
        
        if summary.wrong_prefix_paths > 0:
            lines.extend([
                "## 路径前缀错误修复建议",
                "",
                "以下路径需要将 `scripts/` 修正为 `skillscripts/`：",
                "",
                "| 文件 | 行号 | 原路径 | 建议修复 |",
                "|------|------|--------|----------|",
            ])
            
            for report in summary.document_reports:
                for result in report.results:
                    if result.status == PathStatus.WRONG_PREFIX:
                        lines.append(
                            f"| {Path(result.extracted_path.source_file).name} | "
                            f"{result.extracted_path.line_number} | "
                            f"`{result.extracted_path.raw_path}` | "
                            f"`{result.suggested_fix}` |"
                        )
            
            lines.append("")
        
        if summary.invalid_paths > 0:
            lines.extend([
                "## 缺失脚本文件",
                "",
                "以下脚本文件不存在：",
                "",
                "| 文件 | 行号 | 脚本路径 |",
                "|------|------|----------|",
            ])
            
            for report in summary.document_reports:
                for result in report.results:
                    if result.status == PathStatus.MISSING:
                        lines.append(
                            f"| {Path(result.extracted_path.source_file).name} | "
                            f"{result.extracted_path.line_number} | "
                            f"`{result.actual_path}` |"
                        )
            
            lines.append("")
        
        if summary.fix_suggestions:
            lines.extend([
                "## 批量修复命令",
                "",
                "```bash",
            ])
            
            for suggestion in summary.fix_suggestions:
                lines.append(f"# {suggestion['description']}")
                lines.append(suggestion['command'])
                lines.append("")
            
            lines.extend([
                "```",
                "",
            ])
        
        lines.extend([
            "## 详细验证结果",
            "",
        ])
        
        for report in summary.document_reports:
            lines.extend([
                f"### {Path(report.source_file).name}",
                "",
                f"- 总路径数: {report.total_paths}",
                f"- 有效: {report.valid_paths}",
                f"- 无效: {report.invalid_paths}",
                f"- 前缀错误: {report.wrong_prefix_paths}",
                "",
            ])
            
            if report.results:
                lines.extend([
                    "| 行号 | 路径 | 状态 | 修复建议 |",
                    "|------|------|------|----------|",
                ])
                
                for result in report.results:
                    status_emoji = {
                        PathStatus.VALID: "✅",
                        PathStatus.MISSING: "❌",
                        PathStatus.WRONG_PREFIX: "⚠️",
                        PathStatus.INVALID_FORMAT: "❓"
                    }.get(result.status, "❓")
                    
                    fix = result.suggested_fix if result.suggested_fix else "-"
                    lines.append(
                        f"| {result.extracted_path.line_number} | "
                        f"`{result.extracted_path.raw_path}` | "
                        f"{status_emoji} {result.status.value} | "
                        f"{fix} |"
                    )
                
                lines.append("")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Markdown 报告已生成: {output_path}")


class SkillDocPathValidator:
    """技能文档路径验证器主类"""
    
    def __init__(self, skill_root: Optional[Path] = None):
        self.path_manager = create_path_manager(skill_root)
        self.extractor = ScriptPathExtractor(self.path_manager)
        self.validator = PathValidator(self.path_manager)
        self.fixer = DocumentPathFixer(self.path_manager)
        self.report_generator = ReportGenerator(self.path_manager)
    
    def validate_document(self, doc_path: Path) -> DocumentValidationReport:
        """
        验证单个文档
        
        Args:
            doc_path: 文档路径
            
        Returns:
            文档验证报告
        """
        extracted_paths = self.extractor.extract_from_file(doc_path)
        results = []
        
        for extracted in extracted_paths:
            result = self.validator.validate_path(extracted)
            results.append(result)
        
        valid_count = sum(1 for r in results if r.status == PathStatus.VALID)
        invalid_count = sum(1 for r in results if r.status == PathStatus.MISSING)
        wrong_prefix_count = sum(1 for r in results if r.status == PathStatus.WRONG_PREFIX)
        
        return DocumentValidationReport(
            source_file=str(doc_path),
            total_paths=len(results),
            valid_paths=valid_count,
            invalid_paths=invalid_count,
            wrong_prefix_paths=wrong_prefix_count,
            results=results
        )
    
    def validate_subskills_dir(
        self, 
        subskills_dir: Optional[Path] = None
    ) -> ValidationSummary:
        """
        验证整个 subskills 目录
        
        Args:
            subskills_dir: 子技能目录，None 则使用默认路径
            
        Returns:
            验证汇总报告
        """
        if subskills_dir is None:
            subskills_dir = self.path_manager.resolve_path(PathKey.SUBSKILLS_DIR)
        
        if not subskills_dir.exists():
            logger.error(f"子技能目录不存在: {subskills_dir}")
            return ValidationSummary(
                timestamp=datetime.now().isoformat(),
                skill_root=str(self.path_manager.skill_root),
                documents_scanned=0,
                total_paths_found=0,
                valid_paths=0,
                invalid_paths=0,
                wrong_prefix_paths=0,
                health_score=0.0
            )
        
        document_reports = []
        all_results = []
        
        for md_file in sorted(subskills_dir.glob("*.md")):
            report = self.validate_document(md_file)
            document_reports.append(report)
            all_results.extend(report.results)
        
        total_paths = len(all_results)
        valid_paths = sum(1 for r in all_results if r.status == PathStatus.VALID)
        invalid_paths = sum(1 for r in all_results if r.status == PathStatus.MISSING)
        wrong_prefix_paths = sum(1 for r in all_results if r.status == PathStatus.WRONG_PREFIX)
        
        if total_paths > 0:
            health_score = valid_paths / total_paths
        else:
            health_score = 1.0
        
        fix_suggestions = self._generate_fix_suggestions(all_results)
        
        return ValidationSummary(
            timestamp=datetime.now().isoformat(),
            skill_root=str(self.path_manager.skill_root),
            documents_scanned=len(document_reports),
            total_paths_found=total_paths,
            valid_paths=valid_paths,
            invalid_paths=invalid_paths,
            wrong_prefix_paths=wrong_prefix_paths,
            health_score=health_score,
            document_reports=document_reports,
            fix_suggestions=fix_suggestions
        )
    
    def _generate_fix_suggestions(
        self, 
        results: List[PathValidationResult]
    ) -> List[Dict[str, Any]]:
        """生成修复建议"""
        suggestions = []
        
        wrong_prefix_files = set()
        for result in results:
            if result.status == PathStatus.WRONG_PREFIX:
                wrong_prefix_files.add(result.extracted_path.source_file)
        
        if wrong_prefix_files:
            files_str = ' '.join(f'"{f}"' for f in wrong_prefix_files)
            suggestions.append({
                "description": "修复路径前缀错误 (scripts/ -> skillscripts/)",
                "command": f"python skillscripts/utils/skill_doc_path_validator.py fix --files {files_str}"
            })
        
        return suggestions
    
    def fix_documents(
        self, 
        files: List[Path], 
        dry_run: bool = True,
        backup: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量修复文档
        
        Args:
            files: 文件列表
            dry_run: 是否只预览
            backup: 是否备份
            
        Returns:
            修复结果列表
        """
        results = []
        for file_path in files:
            result = self.fixer.fix_document(file_path, dry_run, backup)
            results.append(result)
        return results
    
    def generate_reports(
        self, 
        summary: ValidationSummary,
        output_dir: Optional[Path] = None,
        prefix: str = "path_validation"
    ) -> Tuple[Path, Path]:
        """
        生成报告
        
        Args:
            summary: 验证汇总
            output_dir: 输出目录
            prefix: 文件名前缀
            
        Returns:
            (JSON 报告路径, Markdown 报告路径)
        """
        if output_dir is None:
            output_dir = self.path_manager.resolve_path(PathKey.REPORTS_DIR)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        json_path = output_dir / f"{prefix}_{timestamp}.json"
        md_path = output_dir / f"{prefix}_{timestamp}.md"
        
        self.report_generator.generate_json_report(summary, json_path)
        self.report_generator.generate_markdown_report(summary, md_path)
        
        return json_path, md_path


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="技能文档路径验证器 - 验证和修复 markdown 文档中的脚本路径"
    )
    
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=None,
        help="技能根目录路径"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    validate_parser = subparsers.add_parser("validate", help="验证路径")
    validate_parser.add_argument(
        "--file", "-f",
        type=Path,
        default=None,
        help="验证单个文件"
    )
    validate_parser.add_argument(
        "--dir", "-d",
        type=Path,
        default=None,
        help="验证目录中的所有 markdown 文件"
    )
    validate_parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="报告输出目录"
    )
    validate_parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="报告格式"
    )
    
    fix_parser = subparsers.add_parser("fix", help="修复路径")
    fix_parser.add_argument(
        "--files",
        nargs="+",
        type=Path,
        required=True,
        help="要修复的文件列表"
    )
    fix_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只预览不实际修改"
    )
    fix_parser.add_argument(
        "--no-backup",
        action="store_true",
        help="不创建备份"
    )
    
    extract_parser = subparsers.add_parser("extract", help="提取路径")
    extract_parser.add_argument(
        "--file", "-f",
        type=Path,
        required=True,
        help="要提取路径的文件"
    )
    extract_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="输出格式"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    validator = SkillDocPathValidator(args.skill_root)
    
    if args.command == "validate":
        if args.file:
            report = validator.validate_document(args.file)
            summary = ValidationSummary(
                timestamp=datetime.now().isoformat(),
                skill_root=str(validator.path_manager.skill_root),
                documents_scanned=1,
                total_paths_found=report.total_paths,
                valid_paths=report.valid_paths,
                invalid_paths=report.invalid_paths,
                wrong_prefix_paths=report.wrong_prefix_paths,
                health_score=report.valid_paths / report.total_paths if report.total_paths > 0 else 1.0,
                document_reports=[report]
            )
        elif args.dir:
            summary = validator.validate_subskills_dir(args.dir)
        else:
            summary = validator.validate_subskills_dir()
        
        print(f"\n验证完成:")
        print(f"  - 扫描文档: {summary.documents_scanned}")
        print(f"  - 发现路径: {summary.total_paths_found}")
        print(f"  - 有效路径: {summary.valid_paths}")
        print(f"  - 无效路径: {summary.invalid_paths}")
        print(f"  - 前缀错误: {summary.wrong_prefix_paths}")
        print(f"  - 健康分数: {summary.health_score:.1%}")
        
        if args.format != "json":
            json_path, md_path = validator.generate_reports(summary, args.output)
            print(f"\n报告已生成:")
            print(f"  - JSON: {json_path}")
            print(f"  - Markdown: {md_path}")
        
        if args.format == "json":
            print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))
    
    elif args.command == "fix":
        results = validator.fix_documents(
            args.files, 
            dry_run=args.dry_run,
            backup=not args.no_backup
        )
        
        for result in results:
            print(f"\n文件: {result['file']}")
            print(f"  预览模式: {result['dry_run']}")
            print(f"  备份创建: {result['backup_created']}")
            
            if result['fixes_applied']:
                print(f"  修复数量: {len(result['fixes_applied'])}")
                for fix in result['fixes_applied']:
                    print(f"    行 {fix['line']}: {fix['old']} -> {fix['new']}")
            
            if result['errors']:
                print(f"  错误: {result['errors']}")
    
    elif args.command == "extract":
        extracted = validator.extractor.extract_from_file(args.file)
        
        if args.format == "json":
            print(json.dumps([e.to_dict() for e in extracted], ensure_ascii=False, indent=2))
        else:
            print(f"\n从 {args.file} 提取到 {len(extracted)} 个路径:")
            for e in extracted:
                print(f"  行 {e.line_number}: {e.raw_path}")
                print(f"    脚本名: {e.script_name}")
                print(f"    类型: {e.script_type}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
