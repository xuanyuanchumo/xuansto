#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档自动修复器 - Document Auto Fixer

专门针对文档问题的自动修复器，包括：
- 链接自动修复：检测断裂的Markdown链接，自动定位正确路径
- 格式自动修复：检测格式问题（乱码、编码问题），自动修复格式
- 文档一致性维护

使用示例:
    from doc_auto_fixer import DocumentAutoFixer
    
    fixer = DocumentAutoFixer()
    result = fixer.fix_document("README.md")
"""

from __future__ import annotations

import os
import re
import json
import logging
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import defaultdict
import difflib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocIssueType(Enum):
    BROKEN_LINK = auto()
    MISSING_FILE_REFERENCE = auto()
    ENCODING_ERROR = auto()
    FORMAT_ERROR = auto()
    MARKDOWN_SYNTAX_ERROR = auto()
    INCONSISTENT_FORMAT = auto()
    BROKEN_IMAGE_LINK = auto()
    INVALID_ANCHOR = auto()
    DUPLICATE_HEADER = auto()
    MISSING_ALT_TEXT = auto()


class FixStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"
    NEEDS_MANUAL_REVIEW = "needs_manual_review"


@dataclass
class DocIssue:
    issue_id: str
    issue_type: DocIssueType
    file_path: str
    line_number: int
    message: str
    severity: str
    original_content: str
    context: str = ""
    suggested_fix: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "issue_type": self.issue_type.name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "message": self.message,
            "severity": self.severity,
            "original_content": self.original_content,
            "context": self.context,
            "suggested_fix": self.suggested_fix,
            "metadata": self.metadata
        }


@dataclass
class DocFixResult:
    result_id: str
    issue_id: str
    issue_type: DocIssueType
    status: FixStatus
    original_content: str
    fixed_content: str
    line_number: int
    confidence: float
    execution_time_ms: float
    message: str = ""
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "issue_id": self.issue_id,
            "issue_type": self.issue_type.name,
            "status": self.status.value,
            "original_content": self.original_content,
            "fixed_content": self.fixed_content,
            "line_number": self.line_number,
            "confidence": self.confidence,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "message": self.message,
            "warnings": self.warnings,
            "metadata": self.metadata
        }


@dataclass
class DocumentFixReport:
    report_id: str
    file_path: str
    total_issues: int
    fixed_issues: int
    failed_issues: int
    skipped_issues: int
    results: List[DocFixResult]
    execution_time_ms: float
    created_at: str
    original_content: str = ""
    fixed_content: str = ""
    diff: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "file_path": self.file_path,
            "total_issues": self.total_issues,
            "fixed_issues": self.fixed_issues,
            "failed_issues": self.failed_issues,
            "skipped_issues": self.skipped_issues,
            "results": [r.to_dict() for r in self.results],
            "execution_time_ms": round(self.execution_time_ms, 2),
            "created_at": self.created_at,
            "diff": self.diff
        }


class LinkFixer:
    """链接修复器"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self._file_cache: Dict[str, Set[str]] = {}
        self._build_file_cache()

    def _build_file_cache(self) -> None:
        logger.info(f"构建文件缓存，根目录: {self.project_root}")
        
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            rel_root = root_path.relative_to(self.project_root)
            
            for file in files:
                if not file.startswith('.'):
                    rel_path = str(rel_root / file) if str(rel_root) != '.' else file
                    cache_key = str(root_path / file)
                    self._file_cache[cache_key] = {file, rel_path, rel_path.replace('\\', '/')}

    def detect_broken_links(self, content: str, file_path: str) -> List[DocIssue]:
        issues = []
        lines = content.split('\n')
        
        link_patterns = [
            (r'\[([^\]]+)\]\(([^)]+)\)', 'markdown_link'),
            (r'!\[([^\]]*)\]\(([^)]+)\)', 'image_link'),
            (r'href=["\']([^"\']+)["\']', 'html_link'),
            (r'src=["\']([^"\']+)["\']', 'html_src'),
        ]

        for line_num, line in enumerate(lines, 1):
            for pattern, link_type in link_patterns:
                matches = re.finditer(pattern, line)
                
                for match in matches:
                    if link_type in ['markdown_link', 'image_link']:
                        link_text = match.group(1)
                        link_url = match.group(2)
                    else:
                        link_url = match.group(1)
                        link_text = ""

                    if link_url.startswith(('http://', 'https://', '#', 'mailto:')):
                        continue

                    if self._is_broken_link(link_url, file_path):
                        issue = DocIssue(
                            issue_id=self._generate_issue_id(),
                            issue_type=DocIssueType.BROKEN_LINK if link_type != 'image_link' else DocIssueType.BROKEN_IMAGE_LINK,
                            file_path=file_path,
                            line_number=line_num,
                            message=f"断裂的链接: {link_url}",
                            severity="high",
                            original_content=match.group(0),
                            context=line.strip(),
                            metadata={
                                "link_type": link_type,
                                "link_url": link_url,
                                "link_text": link_text
                            }
                        )
                        
                        suggested_fix = self._find_correct_path(link_url, file_path)
                        if suggested_fix:
                            issue.suggested_fix = suggested_fix
                            issue.metadata["suggested_path"] = suggested_fix
                        
                        issues.append(issue)

        return issues

    def _is_broken_link(self, link_url: str, current_file: str) -> bool:
        if link_url.startswith('#'):
            return False

        current_dir = Path(current_file).parent
        
        if link_url.startswith('/'):
            target_path = self.project_root / link_url.lstrip('/')
        else:
            target_path = current_dir / link_url

        target_path = target_path.resolve()

        if target_path.exists():
            return False

        if target_path.suffix == '':
            for ext in ['.md', '.html', '.py', '.txt']:
                if (target_path.with_suffix(ext)).exists():
                    return False

        return True

    def _find_correct_path(self, broken_url: str, current_file: str) -> Optional[str]:
        filename = Path(broken_url).name
        
        if '#' in filename:
            filename = filename.split('#')[0]

        if not filename:
            return None

        candidates = []
        
        for cached_path, aliases in self._file_cache.items():
            for alias in aliases:
                if alias.endswith(filename) or filename in alias:
                    cached_file = Path(cached_path)
                    if cached_file.exists():
                        rel_path = cached_file.relative_to(self.project_root)
                        candidates.append(str(rel_path).replace('\\', '/'))

        if not candidates:
            return None

        current_dir = Path(current_file).parent
        
        def path_similarity(path: str) -> int:
            path_obj = Path(path)
            try:
                rel = path_obj.relative_to(current_dir)
                return len(str(rel).split('/'))
            except ValueError:
                return 1000

        candidates.sort(key=path_similarity)
        
        best_match = candidates[0]
        
        try:
            target_path = Path(best_match)
            current_path = Path(current_file)
            rel_path = os.path.relpath(target_path, current_path.parent)
            return rel_path.replace('\\', '/')
        except:
            return best_match

    def fix_link(self, issue: DocIssue) -> DocFixResult:
        start_time = time.perf_counter()
        
        suggested_path = issue.metadata.get("suggested_path")
        
        if not suggested_path:
            return DocFixResult(
                result_id=self._generate_result_id(),
                issue_id=issue.issue_id,
                issue_type=issue.issue_type,
                status=FixStatus.FAILED,
                original_content=issue.original_content,
                fixed_content=issue.original_content,
                line_number=issue.line_number,
                confidence=0.0,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                message="无法找到正确的路径"
            )

        original = issue.original_content
        link_text = issue.metadata.get("link_text", "")
        link_url = issue.metadata.get("link_url", "")

        if issue.issue_type == DocIssueType.BROKEN_LINK:
            fixed = f"[{link_text}]({suggested_path})"
        elif issue.issue_type == DocIssueType.BROKEN_IMAGE_LINK:
            fixed = f"![{link_text}]({suggested_path})"
        else:
            fixed = original.replace(link_url, suggested_path)

        return DocFixResult(
            result_id=self._generate_result_id(),
            issue_id=issue.issue_id,
            issue_type=issue.issue_type,
            status=FixStatus.SUCCESS,
            original_content=original,
            fixed_content=fixed,
            line_number=issue.line_number,
            confidence=0.9,
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
            message=f"链接已修复: {link_url} -> {suggested_path}",
            metadata={"old_path": link_url, "new_path": suggested_path}
        )

    def _generate_issue_id(self) -> str:
        return f"DOC_ISSUE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(time.time()) % 10000:04d}"

    def _generate_result_id(self) -> str:
        return f"DOC_FIX_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(time.time()) % 10000:04d}"


class FormatFixer:
    """格式修复器"""

    def __init__(self):
        self.encoding_issues = {
            'â€™': "'",
            'â€œ': '"',
            'â€': '"',
            'â€"': '—',
            'â€"': '–',
            'â€¦': '...',
            'Ã©': 'é',
            'Ã¨': 'è',
            'Ã ': 'à',
            'Ã¹': 'ù',
            'Ã¢': 'â',
            'Ãª': 'ê',
            'Ã®': 'î',
            'Ã´': 'ô',
            'Ã»': 'û',
            'Ã§': 'ç',
        }

    def detect_format_issues(self, content: str, file_path: str) -> List[DocIssue]:
        issues = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            encoding_issues = self._detect_encoding_issues(line, line_num, file_path)
            issues.extend(encoding_issues)

            markdown_issues = self._detect_markdown_issues(line, line_num, file_path)
            issues.extend(markdown_issues)

        return issues

    def _detect_encoding_issues(self, line: str, line_num: int, file_path: str) -> List[DocIssue]:
        issues = []

        for wrong, correct in self.encoding_issues.items():
            if wrong in line:
                matches = list(re.finditer(re.escape(wrong), line))
                
                for match in matches:
                    issue = DocIssue(
                        issue_id=self._generate_issue_id(),
                        issue_type=DocIssueType.ENCODING_ERROR,
                        file_path=file_path,
                        line_number=line_num,
                        message=f"编码问题: '{wrong}' 应为 '{correct}'",
                        severity="medium",
                        original_content=match.group(0),
                        context=line.strip(),
                        suggested_fix=correct,
                        metadata={"wrong_char": wrong, "correct_char": correct}
                    )
                    issues.append(issue)

        return issues

    def _detect_markdown_issues(self, line: str, line_num: int, file_path: str) -> List[DocIssue]:
        issues = []

        if re.match(r'^#+[^#\s]', line):
            issue = DocIssue(
                issue_id=self._generate_issue_id(),
                issue_type=DocIssueType.MARKDOWN_SYNTAX_ERROR,
                file_path=file_path,
                line_number=line_num,
                message="标题后缺少空格",
                severity="low",
                original_content=line,
                context=line.strip(),
                suggested_fix=re.sub(r'^(#+)', r'\1 ', line),
                metadata={"error_type": "header_spacing"}
            )
            issues.append(issue)

        list_match = re.match(r'^(\s*)(\d+\.)([^\s])', line)
        if list_match:
            issue = DocIssue(
                issue_id=self._generate_issue_id(),
                issue_type=DocIssueType.MARKDOWN_SYNTAX_ERROR,
                file_path=file_path,
                line_number=line_num,
                message="列表项后缺少空格",
                severity="low",
                original_content=line,
                context=line.strip(),
                suggested_fix=f"{list_match.group(1)}{list_match.group(2)} {list_match.group(3)}{line[list_match.end():]}",
                metadata={"error_type": "list_spacing"}
            )
            issues.append(issue)

        if re.search(r'!\[[^\]]*\]\([^)]+\)', line):
            if not re.search(r'!\[[^\]]+\]\([^)]+\)', line):
                issue = DocIssue(
                    issue_id=self._generate_issue_id(),
                    issue_type=DocIssueType.MISSING_ALT_TEXT,
                    file_path=file_path,
                    line_number=line_num,
                    message="图片缺少alt文本",
                    severity="medium",
                    original_content=line,
                    context=line.strip(),
                    metadata={"error_type": "missing_alt_text"}
                )
                issues.append(issue)

        return issues

    def fix_format(self, issue: DocIssue) -> DocFixResult:
        start_time = time.perf_counter()

        if issue.issue_type == DocIssueType.ENCODING_ERROR:
            return self._fix_encoding_issue(issue, start_time)
        elif issue.issue_type == DocIssueType.MARKDOWN_SYNTAX_ERROR:
            return self._fix_markdown_issue(issue, start_time)
        elif issue.issue_type == DocIssueType.MISSING_ALT_TEXT:
            return self._fix_missing_alt_text(issue, start_time)
        else:
            return DocFixResult(
                result_id=self._generate_result_id(),
                issue_id=issue.issue_id,
                issue_type=issue.issue_type,
                status=FixStatus.SKIPPED,
                original_content=issue.original_content,
                fixed_content=issue.original_content,
                line_number=issue.line_number,
                confidence=0.0,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                message="不支持的格式问题类型"
            )

    def _fix_encoding_issue(self, issue: DocIssue, start_time: float) -> DocFixResult:
        wrong_char = issue.metadata.get("wrong_char")
        correct_char = issue.metadata.get("correct_char")

        if not wrong_char or not correct_char:
            return DocFixResult(
                result_id=self._generate_result_id(),
                issue_id=issue.issue_id,
                issue_type=issue.issue_type,
                status=FixStatus.FAILED,
                original_content=issue.original_content,
                fixed_content=issue.original_content,
                line_number=issue.line_number,
                confidence=0.0,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                message="缺少编码修复信息"
            )

        return DocFixResult(
            result_id=self._generate_result_id(),
            issue_id=issue.issue_id,
            issue_type=issue.issue_type,
            status=FixStatus.SUCCESS,
            original_content=issue.original_content,
            fixed_content=correct_char,
            line_number=issue.line_number,
            confidence=1.0,
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
            message=f"编码已修复: '{wrong_char}' -> '{correct_char}'"
        )

    def _fix_markdown_issue(self, issue: DocIssue, start_time: float) -> DocFixResult:
        if issue.suggested_fix:
            return DocFixResult(
                result_id=self._generate_result_id(),
                issue_id=issue.issue_id,
                issue_type=issue.issue_type,
                status=FixStatus.SUCCESS,
                original_content=issue.original_content,
                fixed_content=issue.suggested_fix,
                line_number=issue.line_number,
                confidence=0.95,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                message="Markdown格式已修复"
            )
        else:
            return DocFixResult(
                result_id=self._generate_result_id(),
                issue_id=issue.issue_id,
                issue_type=issue.issue_type,
                status=FixStatus.FAILED,
                original_content=issue.original_content,
                fixed_content=issue.original_content,
                line_number=issue.line_number,
                confidence=0.0,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                message="无法生成修复建议"
            )

    def _fix_missing_alt_text(self, issue: DocIssue, start_time: float) -> DocFixResult:
        img_match = re.search(r'!\[([^\]]*)\]\(([^)]+)\)', issue.original_content)
        
        if not img_match:
            return DocFixResult(
                result_id=self._generate_result_id(),
                issue_id=issue.issue_id,
                issue_type=issue.issue_type,
                status=FixStatus.FAILED,
                original_content=issue.original_content,
                fixed_content=issue.original_content,
                line_number=issue.line_number,
                confidence=0.0,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                message="无法解析图片标签"
            )

        img_url = img_match.group(2)
        filename = Path(img_url).stem
        alt_text = filename.replace('-', ' ').replace('_', ' ').title()

        fixed = f"![{alt_text}]({img_url})"

        return DocFixResult(
            result_id=self._generate_result_id(),
            issue_id=issue.issue_id,
            issue_type=issue.issue_type,
            status=FixStatus.SUCCESS,
            original_content=issue.original_content,
            fixed_content=fixed,
            line_number=issue.line_number,
            confidence=0.7,
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
            message=f"已添加alt文本: '{alt_text}'",
            warnings=["自动生成的alt文本可能需要人工审查"],
            metadata={"generated_alt_text": alt_text}
        )

    def _generate_issue_id(self) -> str:
        return f"DOC_ISSUE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(time.time()) % 10000:04d}"

    def _generate_result_id(self) -> str:
        return f"DOC_FIX_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(time.time()) % 10000:04d}"


class DocumentAutoFixer:
    """文档自动修复器主类"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.link_fixer = LinkFixer(self.project_root)
        self.format_fixer = FormatFixer()
        self._report_counter = 0

    def detect_issues(self, file_path: str) -> List[DocIssue]:
        all_issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, {e}")
            return all_issues

        link_issues = self.link_fixer.detect_broken_links(content, file_path)
        all_issues.extend(link_issues)

        format_issues = self.format_fixer.detect_format_issues(content, file_path)
        all_issues.extend(format_issues)

        logger.info(f"检测到 {len(all_issues)} 个文档问题")
        return all_issues

    def fix_document(self, file_path: str, auto_apply: bool = False) -> DocumentFixReport:
        start_time = time.perf_counter()
        self._report_counter += 1

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, {e}")
            return self._create_error_report(file_path, f"读取文件失败: {e}")

        issues = self.detect_issues(file_path)
        
        if not issues:
            return DocumentFixReport(
                report_id=f"DOC_REPORT_{self._report_counter:04d}",
                file_path=file_path,
                total_issues=0,
                fixed_issues=0,
                failed_issues=0,
                skipped_issues=0,
                results=[],
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                created_at=datetime.now().isoformat(),
                original_content=original_content,
                fixed_content=original_content
            )

        results = []
        modified_content = original_content
        lines = modified_content.split('\n')

        for issue in issues:
            result = self._fix_issue(issue)
            results.append(result)

            if result.status == FixStatus.SUCCESS and auto_apply:
                if issue.line_number <= len(lines):
                    old_line = lines[issue.line_number - 1]
                    new_line = old_line.replace(result.original_content, result.fixed_content)
                    lines[issue.line_number - 1] = new_line

        modified_content = '\n'.join(lines)

        fixed_count = sum(1 for r in results if r.status == FixStatus.SUCCESS)
        failed_count = sum(1 for r in results if r.status == FixStatus.FAILED)
        skipped_count = sum(1 for r in results if r.status == FixStatus.SKIPPED)

        diff = self._generate_diff(original_content, modified_content)

        report = DocumentFixReport(
            report_id=f"DOC_REPORT_{self._report_counter:04d}",
            file_path=file_path,
            total_issues=len(issues),
            fixed_issues=fixed_count,
            failed_issues=failed_count,
            skipped_issues=skipped_count,
            results=results,
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
            created_at=datetime.now().isoformat(),
            original_content=original_content,
            fixed_content=modified_content,
            diff=diff
        )

        if auto_apply and fixed_count > 0:
            self._apply_fix(file_path, modified_content)

        return report

    def _fix_issue(self, issue: DocIssue) -> DocFixResult:
        if issue.issue_type in [DocIssueType.BROKEN_LINK, DocIssueType.BROKEN_IMAGE_LINK]:
            return self.link_fixer.fix_link(issue)
        elif issue.issue_type in [DocIssueType.ENCODING_ERROR, DocIssueType.MARKDOWN_SYNTAX_ERROR, DocIssueType.MISSING_ALT_TEXT]:
            return self.format_fixer.fix_format(issue)
        else:
            return DocFixResult(
                result_id=f"DOC_FIX_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(time.time()) % 10000:04d}",
                issue_id=issue.issue_id,
                issue_type=issue.issue_type,
                status=FixStatus.SKIPPED,
                original_content=issue.original_content,
                fixed_content=issue.original_content,
                line_number=issue.line_number,
                confidence=0.0,
                execution_time_ms=0.0,
                message="不支持的问题类型"
            )

    def _apply_fix(self, file_path: str, content: str) -> bool:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"修复已应用到文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"应用修复失败: {file_path}, {e}")
            return False

    def _generate_diff(self, original: str, modified: str) -> str:
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile='original',
            tofile='modified'
        )
        return ''.join(diff)

    def _create_error_report(self, file_path: str, error_message: str) -> DocumentFixReport:
        return DocumentFixReport(
            report_id=f"DOC_REPORT_{self._report_counter:04d}",
            file_path=file_path,
            total_issues=0,
            fixed_issues=0,
            failed_issues=0,
            skipped_issues=0,
            results=[],
            execution_time_ms=0.0,
            created_at=datetime.now().isoformat(),
            diff=""
        )

    def preview_fix(self, file_path: str) -> DocumentFixReport:
        return self.fix_document(file_path, auto_apply=False)

    def apply_fix(self, file_path: str) -> DocumentFixReport:
        return self.fix_document(file_path, auto_apply=True)

    def batch_fix(self, file_paths: List[str], auto_apply: bool = False) -> List[DocumentFixReport]:
        reports = []
        
        for file_path in file_paths:
            try:
                report = self.fix_document(file_path, auto_apply=auto_apply)
                reports.append(report)
            except Exception as e:
                logger.error(f"批量修复失败: {file_path}, {e}")
        
        return reports

    def generate_report_summary(self, report: DocumentFixReport) -> str:
        lines = [
            "=" * 80,
            "文档自动修复报告",
            "=" * 80,
            f"报告ID: {report.report_id}",
            f"文件路径: {report.file_path}",
            f"创建时间: {report.created_at}",
            "",
            "-" * 80,
            "修复统计",
            "-" * 80,
            f"检测到问题: {report.total_issues}",
            f"成功修复: {report.fixed_issues}",
            f"修复失败: {report.failed_issues}",
            f"跳过修复: {report.skipped_issues}",
            f"执行时间: {report.execution_time_ms:.2f}ms",
            "",
        ]

        if report.results:
            lines.extend([
                "-" * 80,
                "修复详情",
                "-" * 80,
            ])

            for result in report.results:
                status_emoji = {
                    FixStatus.SUCCESS: "✓",
                    FixStatus.PARTIAL: "◐",
                    FixStatus.FAILED: "✗",
                    FixStatus.SKIPPED: "○",
                    FixStatus.NEEDS_MANUAL_REVIEW: "!"
                }.get(result.status, "?")

                lines.append(f"{status_emoji} [{result.issue_type.name}] 行 {result.line_number}: {result.message}")
                
                if result.warnings:
                    for warning in result.warnings:
                        lines.append(f"  ⚠ {warning}")

        lines.append("=" * 80)

        return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="文档自动修复器")
    parser.add_argument("file_path", type=str, help="要修复的文件路径")
    parser.add_argument("--apply", action="store_true", help="自动应用修复")
    parser.add_argument("--preview", action="store_true", help="预览修复结果")
    parser.add_argument("--batch", type=str, help="批量修复文件列表（JSON格式）")

    args = parser.parse_args()

    fixer = DocumentAutoFixer()

    if args.batch:
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                file_paths = json.load(f)
            
            reports = fixer.batch_fix(file_paths, auto_apply=args.apply)
            
            for report in reports:
                print(fixer.generate_report_summary(report))
                print()
        except Exception as e:
            print(f"批量修复失败: {e}")
    else:
        if args.preview or not args.apply:
            report = fixer.preview_fix(args.file_path)
        else:
            report = fixer.apply_fix(args.file_path)

        print(fixer.generate_report_summary(report))
        
        if report.diff:
            print("\n修改差异:")
            print(report.diff)


if __name__ == "__main__":
    main()
