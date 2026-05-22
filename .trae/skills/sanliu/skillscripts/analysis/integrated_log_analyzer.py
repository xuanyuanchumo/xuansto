#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志分析和问题定位整合系统 - Integrated Log Analysis and Issue Localization System
整合日志分析、问题定位、自动修复建议的完整机制

功能:
1. 日志收集和聚合
2. 智能错误模式识别
3. 问题根因分析
4. 自动修复建议生成
5. 问题追踪和闭环验证
"""

import os
import sys
import json
import re
import logging
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, Counter
import hashlib
import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class IssueCategory(Enum):
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    DATABASE = "database"
    NETWORK = "network"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FixConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class LogEntry:
    timestamp: datetime
    level: LogLevel
    message: str
    source: str
    file_path: str = ""
    line_number: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    raw_line: str = ""


@dataclass
class ErrorPattern:
    pattern_id: str
    name: str
    regex: str
    category: IssueCategory
    severity: IssueSeverity
    description: str
    suggested_fix: str
    occurrence_count: int = 0
    affected_files: Set[str] = field(default_factory=set)


@dataclass
class RootCause:
    description: str
    category: IssueCategory
    confidence: float
    evidence: List[str] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)
    stack_trace: List[str] = field(default_factory=list)


@dataclass
class Issue:
    issue_id: str
    title: str
    description: str
    severity: IssueSeverity
    category: IssueCategory
    root_cause: Optional[RootCause]
    location: str
    file_path: str
    line_number: int
    suggested_fixes: List[str]
    status: str = "open"
    created_at: str = ""
    resolved_at: str = ""


@dataclass
class AnalysisReport:
    report_id: str
    generated_at: str
    log_files_analyzed: int
    total_entries: int
    error_count: int
    warning_count: int
    issues_found: List[Issue]
    patterns_detected: List[ErrorPattern]
    summary: Dict[str, Any]
    recommendations: List[str]


class LogCollector:
    
    LOG_PATTERNS = {
        "json": r'^\s*\{.*\}\s*$',
        "text_timestamp": r'^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}',
        "text_level": r'^\[(DEBUG|INFO|WARNING|ERROR|CRITICAL)\]',
        "python": r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+ - (\w+) -',
    }
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getcwd())
        self.entries: List[LogEntry] = []
    
    def collect_from_directory(self, log_dir: str, pattern: str = "*.log") -> int:
        log_path = self.base_path / log_dir
        if not log_path.exists():
            logger.warning(f"日志目录不存在: {log_path}")
            return 0
        
        files_processed = 0
        
        for log_file in log_path.rglob(pattern):
            try:
                self._parse_log_file(log_file)
                files_processed += 1
            except Exception as e:
                logger.warning(f"解析日志文件失败 {log_file}: {e}")
        
        return files_processed
    
    def collect_from_file(self, file_path: str) -> int:
        path = self.base_path / file_path
        if not path.exists():
            logger.warning(f"日志文件不存在: {path}")
            return 0
        
        self._parse_log_file(path)
        return 1
    
    def _parse_log_file(self, file_path: Path):
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.splitlines()
        
        log_format = self._detect_format(lines)
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            entry = self._parse_line(line, file_path, i + 1, log_format)
            if entry:
                self.entries.append(entry)
    
    def _detect_format(self, lines: List[str]) -> str:
        for line in lines[:10]:
            if not line.strip():
                continue
            
            for fmt, pattern in self.LOG_PATTERNS.items():
                if re.match(pattern, line, re.IGNORECASE):
                    return fmt
        
        return "text"
    
    def _parse_line(self, line: str, file_path: Path, line_num: int, 
                    log_format: str) -> Optional[LogEntry]:
        try:
            if log_format == "json":
                return self._parse_json_line(line, file_path, line_num)
            else:
                return self._parse_text_line(line, file_path, line_num)
        except Exception:
            return None
    
    def _parse_json_line(self, line: str, file_path: Path, line_num: int) -> Optional[LogEntry]:
        data = json.loads(line)
        
        timestamp = data.get("timestamp") or data.get("time") or datetime.now().isoformat()
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
        
        level_str = data.get("level", "INFO").upper()
        try:
            level = LogLevel[level_str]
        except KeyError:
            level = LogLevel.INFO
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=data.get("message", data.get("msg", "")),
            source=data.get("logger", data.get("source", "")),
            file_path=str(file_path),
            line_number=line_num,
            context=data,
            raw_line=line
        )
    
    def _parse_text_line(self, line: str, file_path: Path, line_num: int) -> Optional[LogEntry]:
        timestamp = datetime.now()
        level = LogLevel.INFO
        message = line
        source = ""
        
        ts_match = re.match(r'^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)', line)
        if ts_match:
            try:
                ts_str = ts_match.group(1).replace(',', '.').replace(' ', 'T')
                timestamp = datetime.fromisoformat(ts_str.split('+')[0].split('Z')[0])
            except:
                pass
        
        level_match = re.search(r'\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b', line, re.IGNORECASE)
        if level_match:
            level_str = level_match.group(1).upper()
            if level_str == "WARN":
                level_str = "WARNING"
            elif level_str == "FATAL":
                level_str = "CRITICAL"
            try:
                level = LogLevel[level_str]
            except KeyError:
                pass
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source=source,
            file_path=str(file_path),
            line_number=line_num,
            raw_line=line
        )


class ErrorPatternMatcher:
    
    PREDEFINED_PATTERNS = [
        ErrorPattern(
            pattern_id="E001",
            name="ImportError",
            regex=r"ImportError|ModuleNotFoundError|No module named",
            category=IssueCategory.DEPENDENCY,
            severity=IssueSeverity.HIGH,
            description="模块导入错误",
            suggested_fix="检查依赖是否安装，运行 pip install 安装缺失的包"
        ),
        ErrorPattern(
            pattern_id="E002",
            name="SyntaxError",
            regex=r"SyntaxError|IndentationError|TabError",
            category=IssueCategory.SYNTAX,
            severity=IssueSeverity.HIGH,
            description="语法错误",
            suggested_fix="检查代码语法，修复缩进或语法问题"
        ),
        ErrorPattern(
            pattern_id="E003",
            name="TypeError",
            regex=r"TypeError|unsupported operand|not callable|NoneType",
            category=IssueCategory.RUNTIME,
            severity=IssueSeverity.HIGH,
            description="类型错误",
            suggested_fix="检查变量类型，添加类型检查或转换"
        ),
        ErrorPattern(
            pattern_id="E004",
            name="AttributeError",
            regex=r"AttributeError|has no attribute",
            category=IssueCategory.RUNTIME,
            severity=IssueSeverity.HIGH,
            description="属性错误",
            suggested_fix="检查对象是否有所需属性，添加属性存在性检查"
        ),
        ErrorPattern(
            pattern_id="E005",
            name="KeyError",
            regex=r"KeyError",
            category=IssueCategory.RUNTIME,
            severity=IssueSeverity.MEDIUM,
            description="键错误",
            suggested_fix="检查字典键是否存在，使用 .get() 方法或添加键检查"
        ),
        ErrorPattern(
            pattern_id="E006",
            name="FileNotFoundError",
            regex=r"FileNotFoundError|No such file or directory",
            category=IssueCategory.RESOURCE,
            severity=IssueSeverity.MEDIUM,
            description="文件未找到",
            suggested_fix="检查文件路径是否正确，确保文件存在"
        ),
        ErrorPattern(
            pattern_id="E007",
            name="PermissionError",
            regex=r"PermissionError|Permission denied|Access denied",
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.HIGH,
            description="权限错误",
            suggested_fix="检查文件/目录权限，以管理员身份运行或修改权限"
        ),
        ErrorPattern(
            pattern_id="E008",
            name="ConnectionError",
            regex=r"ConnectionError|Connection refused|Network is unreachable",
            category=IssueCategory.NETWORK,
            severity=IssueSeverity.HIGH,
            description="网络连接错误",
            suggested_fix="检查网络连接，确认服务是否运行，检查防火墙设置"
        ),
        ErrorPattern(
            pattern_id="E009",
            name="DatabaseError",
            regex=r"DatabaseError|IntegrityError|OperationalError|sqlite3\.Error",
            category=IssueCategory.DATABASE,
            severity=IssueSeverity.HIGH,
            description="数据库错误",
            suggested_fix="检查数据库连接，验证SQL语句，检查数据完整性约束"
        ),
        ErrorPattern(
            pattern_id="E010",
            name="MemoryError",
            regex=r"MemoryError|Out of memory",
            category=IssueCategory.RESOURCE,
            severity=IssueSeverity.CRITICAL,
            description="内存错误",
            suggested_fix="优化内存使用，分批处理数据，增加系统内存"
        ),
        ErrorPattern(
            pattern_id="E011",
            name="TimeoutError",
            regex=r"TimeoutError|timeout|timed out",
            category=IssueCategory.PERFORMANCE,
            severity=IssueSeverity.MEDIUM,
            description="超时错误",
            suggested_fix="增加超时时间，优化处理速度，使用异步处理"
        ),
        ErrorPattern(
            pattern_id="E012",
            name="AssertionError",
            regex=r"AssertionError",
            category=IssueCategory.LOGIC,
            severity=IssueSeverity.MEDIUM,
            description="断言错误",
            suggested_fix="检查断言条件，修复逻辑问题"
        ),
    ]
    
    def __init__(self):
        self.patterns = {p.pattern_id: p for p in self.PREDEFINED_PATTERNS}
        self.matches: Dict[str, List[LogEntry]] = defaultdict(list)
    
    def match(self, entries: List[LogEntry]) -> List[ErrorPattern]:
        matched_patterns = []
        
        for entry in entries:
            if entry.level not in [LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.WARNING]:
                continue
            
            for pattern in self.patterns.values():
                if re.search(pattern.regex, entry.message, re.IGNORECASE):
                    pattern.occurrence_count += 1
                    pattern.affected_files.add(entry.file_path)
                    self.matches[pattern.pattern_id].append(entry)
                    
                    if pattern not in matched_patterns:
                        matched_patterns.append(pattern)
        
        return matched_patterns


class RootCauseAnalyzer:
    
    def __init__(self):
        self.trace_pattern = r'File "([^"]+)", line (\d+), in (\w+)'
    
    def analyze(self, entry: LogEntry, related_entries: List[LogEntry] = None) -> Optional[RootCause]:
        message = entry.message
        
        stack_trace = re.findall(self.trace_pattern, message)
        
        category = self._categorize(message)
        
        confidence = self._calculate_confidence(message, stack_trace)
        
        evidence = self._extract_evidence(message)
        
        related_files = [frame[0] for frame in stack_trace] if stack_trace else []
        
        description = self._generate_description(message, category, stack_trace)
        
        return RootCause(
            description=description,
            category=category,
            confidence=confidence,
            evidence=evidence,
            related_files=related_files,
            stack_trace=[f"{f}:{l} in {fn}" for f, l, fn in stack_trace]
        )
    
    def _categorize(self, message: str) -> IssueCategory:
        category_keywords = {
            IssueCategory.SYNTAX: ["syntax", "indent", "tab", "parse"],
            IssueCategory.RUNTIME: ["type", "attribute", "key", "index", "value"],
            IssueCategory.DEPENDENCY: ["import", "module", "package", "no module"],
            IssueCategory.DATABASE: ["database", "sql", "query", "table", "column"],
            IssueCategory.NETWORK: ["connection", "network", "socket", "timeout"],
            IssueCategory.RESOURCE: ["file", "memory", "disk", "permission"],
            IssueCategory.SECURITY: ["permission", "denied", "auth", "forbidden"],
            IssueCategory.PERFORMANCE: ["timeout", "slow", "memory", "cpu"],
        }
        
        message_lower = message.lower()
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return category
        
        return IssueCategory.UNKNOWN
    
    def _calculate_confidence(self, message: str, stack_trace: List) -> float:
        confidence = 0.5
        
        if stack_trace:
            confidence += 0.2
        
        if "Error" in message or "Exception" in message:
            confidence += 0.1
        
        if re.search(r'line \d+', message):
            confidence += 0.1
        
        if re.search(r'File "[^"]+"', message):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _extract_evidence(self, message: str) -> List[str]:
        evidence = []
        
        error_match = re.search(r'(\w+Error|\w+Exception):?\s*(.+?)(?:\n|$)', message)
        if error_match:
            evidence.append(f"错误类型: {error_match.group(1)}")
            evidence.append(f"错误信息: {error_match.group(2).strip()}")
        
        file_matches = re.findall(r'File "([^"]+)"', message)
        if file_matches:
            evidence.append(f"相关文件: {', '.join(set(file_matches))}")
        
        return evidence
    
    def _generate_description(self, message: str, category: IssueCategory, 
                              stack_trace: List) -> str:
        if stack_trace:
            first_frame = stack_trace[0]
            return f"在 {first_frame[0]}:{first_frame[1]} 的 {first_frame[2]} 函数中发生 {category.value} 错误"
        
        error_type = re.search(r'(\w+Error|\w+Exception)', message)
        if error_type:
            return f"检测到 {error_type.group(1)} ({category.value} 类别)"
        
        return f"检测到 {category.value} 类别的问题"


class IssueLocator:
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getcwd())
    
    def locate(self, root_cause: RootCause) -> Tuple[str, int]:
        if root_cause.related_files:
            for file_path in root_cause.related_files:
                if self.base_path in Path(file_path).parents or not Path(file_path).is_absolute():
                    return file_path, 0
        
        for evidence in root_cause.evidence:
            file_match = re.search(r'["\']?([^"\'\s,]+\.py)["\']?', evidence)
            if file_match:
                potential_path = self.base_path / file_match.group(1)
                if potential_path.exists():
                    return str(potential_path), 0
        
        return "", 0


class FixSuggestionGenerator:
    
    FIX_TEMPLATES = {
        IssueCategory.SYNTAX: [
            "检查代码语法，确保括号、引号配对",
            "验证缩进是否正确（使用空格而非Tab）",
            "检查是否有缺失的冒号或逗号"
        ],
        IssueCategory.RUNTIME: [
            "添加类型检查和空值验证",
            "使用 try-except 捕获异常",
            "检查变量是否已正确初始化"
        ],
        IssueCategory.DEPENDENCY: [
            "运行 pip install -r requirements.txt 安装依赖",
            "检查虚拟环境是否激活",
            "验证包版本兼容性"
        ],
        IssueCategory.DATABASE: [
            "检查数据库连接字符串",
            "验证SQL语句语法",
            "检查表结构和约束"
        ],
        IssueCategory.NETWORK: [
            "验证服务是否运行",
            "检查防火墙和网络配置",
            "增加连接超时时间"
        ],
        IssueCategory.RESOURCE: [
            "检查文件路径是否存在",
            "验证文件权限",
            "释放不必要的资源"
        ],
        IssueCategory.SECURITY: [
            "检查用户权限",
            "验证认证信息",
            "检查安全策略配置"
        ],
        IssueCategory.PERFORMANCE: [
            "优化算法复杂度",
            "使用缓存减少重复计算",
            "分批处理大数据"
        ],
    }
    
    def generate(self, root_cause: RootCause) -> List[str]:
        suggestions = []
        
        if root_cause.category in self.FIX_TEMPLATES:
            suggestions.extend(self.FIX_TEMPLATES[root_cause.category])
        
        for evidence in root_cause.evidence:
            if "Error" in evidence or "Exception" in evidence:
                suggestions.append(f"针对 {evidence} 进行具体修复")
        
        return suggestions[:5]


class IntegratedLogAnalyzer:
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getcwd())
        self.collector = LogCollector(base_path)
        self.matcher = ErrorPatternMatcher()
        self.root_cause_analyzer = RootCauseAnalyzer()
        self.issue_locator = IssueLocator(base_path)
        self.fix_generator = FixSuggestionGenerator()
    
    def analyze(self, log_sources: List[str] = None) -> AnalysisReport:
        logger.info("开始日志分析...")
        
        if log_sources:
            for source in log_sources:
                if source.endswith('.log'):
                    self.collector.collect_from_file(source)
                else:
                    self.collector.collect_from_directory(source)
        else:
            self.collector.collect_from_directory("logs")
            self.collector.collect_from_directory(".trae/skills/sanliu/logs")
        
        entries = self.collector.entries
        logger.info(f"收集到 {len(entries)} 条日志记录")
        
        patterns = self.matcher.match(entries)
        logger.info(f"检测到 {len(patterns)} 种错误模式")
        
        issues = self._identify_issues(entries, patterns)
        logger.info(f"识别到 {len(issues)} 个问题")
        
        summary = self._generate_summary(entries, patterns, issues)
        recommendations = self._generate_recommendations(issues)
        
        return AnalysisReport(
            report_id=f"LOG-ANALYSIS-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            log_files_analyzed=len(set(e.file_path for e in entries)),
            total_entries=len(entries),
            error_count=sum(1 for e in entries if e.level == LogLevel.ERROR),
            warning_count=sum(1 for e in entries if e.level == LogLevel.WARNING),
            issues_found=issues,
            patterns_detected=patterns,
            summary=summary,
            recommendations=recommendations
        )
    
    def _identify_issues(self, entries: List[LogEntry], 
                         patterns: List[ErrorPattern]) -> List[Issue]:
        issues = []
        processed_messages = set()
        
        for pattern in patterns:
            matched_entries = self.matcher.matches.get(pattern.pattern_id, [])
            
            for entry in matched_entries:
                message_hash = hashlib.md5(entry.message.encode()).hexdigest()[:8]
                
                if message_hash in processed_messages:
                    continue
                processed_messages.add(message_hash)
                
                root_cause = self.root_cause_analyzer.analyze(entry, matched_entries)
                
                file_path, line_number = self.issue_locator.locate(root_cause) if root_cause else ("", 0)
                
                suggested_fixes = self.fix_generator.generate(root_cause) if root_cause else []
                
                issue = Issue(
                    issue_id=f"ISSUE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{message_hash}",
                    title=f"{pattern.name}: {entry.message[:100]}",
                    description=entry.message,
                    severity=pattern.severity,
                    category=pattern.category,
                    root_cause=root_cause,
                    location=f"{file_path}:{line_number}" if file_path else "未知位置",
                    file_path=file_path,
                    line_number=line_number,
                    suggested_fixes=suggested_fixes,
                    created_at=datetime.now().isoformat()
                )
                
                issues.append(issue)
        
        return issues
    
    def _generate_summary(self, entries: List[LogEntry], 
                          patterns: List[ErrorPattern],
                          issues: List[Issue]) -> Dict[str, Any]:
        severity_counts = Counter(i.severity for i in issues)
        category_counts = Counter(i.category for i in issues)
        
        return {
            "total_entries": len(entries),
            "error_entries": sum(1 for e in entries if e.level == LogLevel.ERROR),
            "warning_entries": sum(1 for e in entries if e.level == LogLevel.WARNING),
            "critical_issues": severity_counts.get(IssueSeverity.CRITICAL, 0),
            "high_issues": severity_counts.get(IssueSeverity.HIGH, 0),
            "medium_issues": severity_counts.get(IssueSeverity.MEDIUM, 0),
            "low_issues": severity_counts.get(IssueSeverity.LOW, 0),
            "categories": {cat.value: count for cat, count in category_counts.items()},
            "most_common_patterns": [
                {"name": p.name, "count": p.occurrence_count}
                for p in sorted(patterns, key=lambda x: x.occurrence_count, reverse=True)[:5]
            ]
        }
    
    def _generate_recommendations(self, issues: List[Issue]) -> List[str]:
        recommendations = []
        
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        if critical_issues:
            recommendations.append(f"立即处理 {len(critical_issues)} 个严重问题")
        
        high_issues = [i for i in issues if i.severity == IssueSeverity.HIGH]
        if high_issues:
            recommendations.append(f"优先处理 {len(high_issues)} 个高优先级问题")
        
        category_counts = Counter(i.category for i in issues)
        most_common_category = category_counts.most_common(1)
        if most_common_category:
            recommendations.append(f"重点关注 {most_common_category[0][0].value} 类别问题")
        
        return recommendations
    
    def save_report(self, report: AnalysisReport, output_path: str = None):
        output_path = Path(output_path or self.base_path / "docs" / "reports" / 
                          f"log_analysis_{report.report_id}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report_dict = {
            "report_id": report.report_id,
            "generated_at": report.generated_at,
            "log_files_analyzed": report.log_files_analyzed,
            "total_entries": report.total_entries,
            "error_count": report.error_count,
            "warning_count": report.warning_count,
            "summary": report.summary,
            "recommendations": report.recommendations,
            "issues": [
                {
                    "issue_id": i.issue_id,
                    "title": i.title,
                    "severity": i.severity.value,
                    "category": i.category.value,
                    "location": i.location,
                    "suggested_fixes": i.suggested_fixes,
                    "root_cause": {
                        "description": i.root_cause.description,
                        "confidence": i.root_cause.confidence,
                        "evidence": i.root_cause.evidence
                    } if i.root_cause else None
                }
                for i in report.issues_found
            ],
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "name": p.name,
                    "category": p.category.value,
                    "severity": p.severity.value,
                    "occurrence_count": p.occurrence_count,
                    "affected_files": list(p.affected_files)
                }
                for p in report.patterns_detected
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"分析报告已保存: {output_path}")
        
        md_path = output_path.with_suffix('.md')
        self._save_markdown_report(report, md_path)
    
    def _save_markdown_report(self, report: AnalysisReport, output_path: Path):
        lines = [
            "# 日志分析报告",
            f"\n**报告ID**: {report.report_id}",
            f"**生成时间**: {report.generated_at}",
            "\n## 概述",
            f"\n- 分析日志文件: {report.log_files_analyzed} 个",
            f"- 总日志条目: {report.total_entries} 条",
            f"- 错误条目: {report.error_count} 条",
            f"- 警告条目: {report.warning_count} 条",
            "\n## 问题统计",
            f"\n| 严重程度 | 数量 |",
            f"|----------|------|",
            f"| 严重 | {report.summary.get('critical_issues', 0)} |",
            f"| 高 | {report.summary.get('high_issues', 0)} |",
            f"| 中 | {report.summary.get('medium_issues', 0)} |",
            f"| 低 | {report.summary.get('low_issues', 0)} |",
            "\n## 检测到的问题",
        ]
        
        for issue in report.issues_found:
            lines.extend([
                f"\n### {issue.severity.value.upper()}: {issue.title[:50]}...",
                f"- **类别**: {issue.category.value}",
                f"- **位置**: {issue.location}",
                f"- **描述**: {issue.description[:200]}...",
            ])
            
            if issue.suggested_fixes:
                lines.append("\n**建议修复方案**:")
                for fix in issue.suggested_fixes:
                    lines.append(f"  - {fix}")
        
        if report.recommendations:
            lines.append("\n## 改进建议")
            for rec in report.recommendations:
                lines.append(f"- {rec}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        logger.info(f"Markdown报告已保存: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="日志分析和问题定位整合系统")
    parser.add_argument("--base-path", default=".", help="项目基础路径")
    parser.add_argument("--log-dir", action="append", help="日志目录（可多次指定）")
    parser.add_argument("--output", help="报告输出路径")
    
    args = parser.parse_args()
    
    analyzer = IntegratedLogAnalyzer(args.base_path)
    report = analyzer.analyze(args.log_dir)
    
    print("\n" + "="*60)
    print("日志分析报告")
    print("="*60)
    print(f"报告ID: {report.report_id}")
    print(f"\n统计:")
    print(f"  日志文件: {report.log_files_analyzed} 个")
    print(f"  总条目: {report.total_entries} 条")
    print(f"  错误: {report.error_count} 条")
    print(f"  警告: {report.warning_count} 条")
    print(f"\n问题:")
    print(f"  严重: {report.summary.get('critical_issues', 0)}")
    print(f"  高: {report.summary.get('high_issues', 0)}")
    print(f"  中: {report.summary.get('medium_issues', 0)}")
    print(f"  低: {report.summary.get('low_issues', 0)}")
    
    if report.recommendations:
        print("\n建议:")
        for rec in report.recommendations:
            print(f"  - {rec}")
    
    print("\n" + "="*60)
    
    analyzer.save_report(report, args.output)


if __name__ == "__main__":
    main()
