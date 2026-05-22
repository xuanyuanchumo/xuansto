#!/usr/bin/env python3
"""
代码质量自动验证器

自动验证代码质量，支持：
1. 代码风格检查（Lint）
2. 类型检查（Type Check）
3. 复杂度分析
4. 安全漏洞扫描
5. 代码重复检测
6. 文档覆盖率检查

生成代码质量报告，提供改进建议。

用法:
    python code_quality_validator.py --path app/ --output reports/
    python code_quality_validator.py --file app/main.py --full-check
    python code_quality_validator.py --path src/ --lang typescript
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class Language(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    VUE = "vue"
    GO = "go"


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class QualityMetric(Enum):
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    DUPLICATION = "duplication"
    STYLE = "style"
    TYPE_SAFETY = "type_safety"


@dataclass
class QualityIssue:
    file_path: str
    line: int
    column: int
    rule_id: str
    severity: Severity
    message: str
    metric: QualityMetric
    suggestion: str = ""
    code_snippet: str = ""


@dataclass
class FileQualityReport:
    file_path: str
    language: Language
    issues: List[QualityIssue] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    score: float = 0.0
    lines_of_code: int = 0
    lines_of_comments: int = 0
    lines_of_blank: int = 0


@dataclass
class QualityReport:
    project_path: str
    language: Language
    files: List[FileQualityReport] = field(default_factory=list)
    total_issues: int = 0
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    issues_by_metric: Dict[str, int] = field(default_factory=dict)
    overall_score: float = 0.0
    passed: bool = False
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    recommendations: List[str] = field(default_factory=list)


QUALITY_THRESHOLDS = {
    QualityMetric.COMPLEXITY: {"warning": 10, "error": 20},
    QualityMetric.MAINTAINABILITY: {"warning": 65, "error": 50},
    QualityMetric.DUPLICATION: {"warning": 3, "error": 5},
    QualityMetric.DOCUMENTATION: {"warning": 50, "error": 30},
    QualityMetric.TYPE_SAFETY: {"warning": 80, "error": 60},
}


class ComplexityAnalyzer:
    """圈复杂度分析器"""
    
    def __init__(self):
        self.complexity_nodes = {
            ast.If, ast.For, ast.While, ast.ExceptHandler,
            ast.With, ast.Assert, ast.comprehension,
            ast.BoolOp, ast.BinOp, ast.Compare
        }
    
    def analyze(self, source_code: str) -> Dict[str, Any]:
        """分析代码复杂度"""
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return {"complexity": 0, "functions": []}
        
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_function_complexity(node)
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "complexity": complexity,
                    "parameters": len(node.args.args),
                    "lines": self._count_function_lines(node, source_code)
                })
        
        total_complexity = sum(f["complexity"] for f in functions) if functions else 1
        avg_complexity = total_complexity / len(functions) if functions else 0
        
        return {
            "complexity": avg_complexity,
            "total_complexity": total_complexity,
            "functions": functions,
            "function_count": len(functions)
        }
    
    def _calculate_function_complexity(self, node: ast.AST) -> int:
        """计算函数圈复杂度"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                complexity += 1
            elif isinstance(child, ast.For):
                complexity += 1
            elif isinstance(child, ast.While):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)
        
        return complexity
    
    def _count_function_lines(self, node: ast.AST, source_code: str) -> int:
        """计算函数行数"""
        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
            return node.end_lineno - node.lineno + 1
        return 0


class CodeStyleChecker:
    """代码风格检查器"""
    
    STYLE_RULES = {
        "line_length": {"max": 120, "severity": Severity.WARNING},
        "trailing_whitespace": {"severity": Severity.INFO},
        "missing_newline": {"severity": Severity.INFO},
        "multiple_blank_lines": {"max": 2, "severity": Severity.INFO},
        "naming_convention": {"severity": Severity.WARNING},
    }
    
    def check(self, source_code: str, file_path: str) -> List[QualityIssue]:
        """检查代码风格"""
        issues = []
        lines = source_code.split("\n")
        
        for i, line in enumerate(lines, 1):
            if len(line) > self.STYLE_RULES["line_length"]["max"]:
                issues.append(QualityIssue(
                    file_path=file_path,
                    line=i,
                    column=self.STYLE_RULES["line_length"]["max"],
                    rule_id="STYLE001",
                    severity=Severity.WARNING,
                    message=f"行长度超过 {self.STYLE_RULES['line_length']['max']} 字符",
                    metric=QualityMetric.STYLE,
                    suggestion="将长行拆分为多行",
                    code_snippet=line[:100] + "..." if len(line) > 100 else line
                ))
            
            if line.rstrip() != line and line.strip():
                issues.append(QualityIssue(
                    file_path=file_path,
                    line=i,
                    column=len(line.rstrip()),
                    rule_id="STYLE002",
                    severity=Severity.INFO,
                    message="行尾存在空白字符",
                    metric=QualityMetric.STYLE,
                    suggestion="移除行尾空白字符"
                ))
        
        if lines and lines[-1].strip() and not source_code.endswith("\n"):
            issues.append(QualityIssue(
                file_path=file_path,
                line=len(lines),
                column=len(lines[-1]),
                rule_id="STYLE003",
                severity=Severity.INFO,
                message="文件末尾缺少换行符",
                metric=QualityMetric.STYLE,
                suggestion="在文件末尾添加空行"
            ))
        
        return issues


class DocumentationChecker:
    """文档覆盖率检查器"""
    
    def check(self, source_code: str, file_path: str) -> Tuple[List[QualityIssue], float]:
        """检查文档覆盖率"""
        issues = []
        
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return issues, 0.0
        
        total_items = 0
        documented_items = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_items += 1
                docstring = ast.get_docstring(node)
                if docstring:
                    documented_items += 1
                else:
                    issues.append(QualityIssue(
                        file_path=file_path,
                        line=node.lineno,
                        column=0,
                        rule_id="DOC001",
                        severity=Severity.WARNING,
                        message=f"函数 '{node.name}' 缺少文档字符串",
                        metric=QualityMetric.DOCUMENTATION,
                        suggestion="添加描述函数功能、参数和返回值的文档字符串"
                    ))
            
            elif isinstance(node, ast.ClassDef):
                total_items += 1
                docstring = ast.get_docstring(node)
                if docstring:
                    documented_items += 1
                else:
                    issues.append(QualityIssue(
                        file_path=file_path,
                        line=node.lineno,
                        column=0,
                        rule_id="DOC002",
                        severity=Severity.WARNING,
                        message=f"类 '{node.name}' 缺少文档字符串",
                        metric=QualityMetric.DOCUMENTATION,
                        suggestion="添加描述类功能和用法的文档字符串"
                    ))
        
        coverage = (documented_items / total_items * 100) if total_items > 0 else 100.0
        
        return issues, coverage


class TypeSafetyChecker:
    """类型安全检查器"""
    
    def check(self, source_code: str, file_path: str) -> Tuple[List[QualityIssue], float]:
        """检查类型注解覆盖率"""
        issues = []
        
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return issues, 0.0
        
        total_params = 0
        typed_params = 0
        total_returns = 0
        typed_returns = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for arg in node.args.args:
                    total_params += 1
                    if arg.annotation:
                        typed_params += 1
                    else:
                        issues.append(QualityIssue(
                            file_path=file_path,
                            line=node.lineno,
                            column=arg.col_offset,
                            rule_id="TYPE001",
                            severity=Severity.INFO,
                            message=f"参数 '{arg.arg}' 缺少类型注解",
                            metric=QualityMetric.TYPE_SAFETY,
                            suggestion="添加参数类型注解"
                        ))
                
                total_returns += 1
                if node.returns:
                    typed_returns += 1
                else:
                    if not node.name.startswith("_"):
                        issues.append(QualityIssue(
                            file_path=file_path,
                            line=node.lineno,
                            column=0,
                            rule_id="TYPE002",
                            severity=Severity.INFO,
                            message=f"函数 '{node.name}' 缺少返回类型注解",
                            metric=QualityMetric.TYPE_SAFETY,
                            suggestion="添加返回类型注解"
                        ))
        
        param_coverage = (typed_params / total_params * 100) if total_params > 0 else 100.0
        return_coverage = (typed_returns / total_returns * 100) if total_returns > 0 else 100.0
        overall_coverage = (param_coverage + return_coverage) / 2
        
        return issues, overall_coverage


class SecurityScanner:
    """安全漏洞扫描器"""
    
    SECURITY_PATTERNS = [
        (r"eval\s*\(", "SEC001", "使用 eval() 存在安全风险", Severity.ERROR),
        (r"exec\s*\(", "SEC002", "使用 exec() 存在安全风险", Severity.ERROR),
        (r"__import__\s*\(", "SEC003", "动态导入可能存在安全风险", Severity.WARNING),
        (r"subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True", "SEC004", "使用 shell=True 存在命令注入风险", Severity.ERROR),
        (r"pickle\.loads?\s*\(", "SEC005", "pickle 反序列化存在安全风险", Severity.WARNING),
        (r"yaml\.load\s*\([^)]*\)", "SEC006", "使用 yaml.load() 存在安全风险，建议使用 yaml.safe_load()", Severity.WARNING),
        (r"password\s*=\s*['\"]", "SEC007", "代码中可能包含硬编码密码", Severity.ERROR),
        (r"secret\s*=\s*['\"]", "SEC008", "代码中可能包含硬编码密钥", Severity.ERROR),
        (r"api_key\s*=\s*['\"]", "SEC009", "代码中可能包含硬编码API密钥", Severity.ERROR),
        (r"SQL\s*\+|f['\"].*SELECT.*{", "SEC010", "可能存在SQL注入风险", Severity.ERROR),
    ]
    
    def scan(self, source_code: str, file_path: str) -> List[QualityIssue]:
        """扫描安全漏洞"""
        issues = []
        lines = source_code.split("\n")
        
        for i, line in enumerate(lines, 1):
            for pattern, rule_id, message, severity in self.SECURITY_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(QualityIssue(
                        file_path=file_path,
                        line=i,
                        column=0,
                        rule_id=rule_id,
                        severity=severity,
                        message=message,
                        metric=QualityMetric.SECURITY,
                        suggestion="请检查并修复安全问题",
                        code_snippet=line.strip()[:100]
                    ))
        
        return issues


class DuplicationDetector:
    """代码重复检测器"""
    
    MIN_DUPLICATION_LENGTH = 6
    
    def detect(self, source_code: str, file_path: str) -> Tuple[List[QualityIssue], float]:
        """检测代码重复"""
        issues = []
        
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return issues, 0.0
        
        code_blocks = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                try:
                    code = ast.unparse(node)
                    code_blocks.append({
                        "name": node.name,
                        "line": node.lineno,
                        "code": code,
                        "hash": hash(code)
                    })
                except:
                    pass
        
        seen_hashes = {}
        duplications = 0
        
        for block in code_blocks:
            if block["hash"] in seen_hashes:
                duplications += 1
                issues.append(QualityIssue(
                    file_path=file_path,
                    line=block["line"],
                    column=0,
                    rule_id="DUP001",
                    severity=Severity.WARNING,
                    message=f"函数 '{block['name']}' 与函数 '{seen_hashes[block['hash']]['name']}' 可能重复",
                    metric=QualityMetric.DUPLICATION,
                    suggestion="考虑提取公共代码到独立函数"
                ))
            else:
                seen_hashes[block["hash"]] = block
        
        duplication_rate = (duplications / len(code_blocks) * 100) if code_blocks else 0.0
        
        return issues, duplication_rate


class ExternalToolRunner:
    """外部工具运行器"""
    
    @staticmethod
    def run_pylint(file_path: str) -> List[QualityIssue]:
        """运行pylint检查"""
        issues = []
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pylint", file_path, "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                try:
                    pylint_issues = json.loads(result.stdout)
                    for issue in pylint_issues:
                        issues.append(QualityIssue(
                            file_path=file_path,
                            line=issue.get("line", 0),
                            column=issue.get("column", 0),
                            rule_id=issue.get("message-id", "PYLINT"),
                            severity=Severity.WARNING if issue.get("type") == "warning" else Severity.ERROR,
                            message=issue.get("message", ""),
                            metric=QualityMetric.STYLE,
                            suggestion=""
                        ))
                except json.JSONDecodeError:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return issues
    
    @staticmethod
    def run_mypy(file_path: str) -> List[QualityIssue]:
        """运行mypy类型检查"""
        issues = []
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "mypy", file_path, "--output=json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            for line in result.stdout.split("\n"):
                if ":" in line and "error:" in line.lower():
                    parts = line.split(":")
                    if len(parts) >= 3:
                        try:
                            line_num = int(parts[1].strip())
                            message = ":".join(parts[2:]).strip()
                            issues.append(QualityIssue(
                                file_path=file_path,
                                line=line_num,
                                column=0,
                                rule_id="MYPY",
                                severity=Severity.ERROR,
                                message=message,
                                metric=QualityMetric.TYPE_SAFETY
                            ))
                        except ValueError:
                            pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return issues
    
    @staticmethod
    def run_ruff(file_path: str) -> List[QualityIssue]:
        """运行ruff检查"""
        issues = []
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", file_path, "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                try:
                    ruff_issues = json.loads(result.stdout)
                    for issue in ruff_issues:
                        issues.append(QualityIssue(
                            file_path=file_path,
                            line=issue.get("location", {}).get("row", 0),
                            column=issue.get("location", {}).get("column", 0),
                            rule_id=issue.get("code", "RUFF"),
                            severity=Severity.WARNING,
                            message=issue.get("message", ""),
                            metric=QualityMetric.STYLE
                        ))
                except json.JSONDecodeError:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return issues


class CodeQualityValidator:
    """代码质量验证器主类"""
    
    def __init__(
        self,
        language: Language = Language.PYTHON,
        run_external_tools: bool = True
    ):
        self.language = language
        self.run_external_tools = run_external_tools
        
        self.complexity_analyzer = ComplexityAnalyzer()
        self.style_checker = CodeStyleChecker()
        self.doc_checker = DocumentationChecker()
        self.type_checker = TypeSafetyChecker()
        self.security_scanner = SecurityScanner()
        self.duplication_detector = DuplicationDetector()
    
    def validate_file(self, file_path: str) -> FileQualityReport:
        """验证单个文件"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            source_code = f.read()
        
        report = FileQualityReport(
            file_path=str(path),
            language=self.language
        )
        
        report.lines_of_code, report.lines_of_comments, report.lines_of_blank = \
            self._count_lines(source_code)
        
        complexity_result = self.complexity_analyzer.analyze(source_code)
        report.metrics["complexity"] = complexity_result["complexity"]
        report.metrics["function_count"] = complexity_result["function_count"]
        
        for func in complexity_result.get("functions", []):
            if func["complexity"] > QUALITY_THRESHOLDS[QualityMetric.COMPLEXITY]["error"]:
                report.issues.append(QualityIssue(
                    file_path=str(path),
                    line=func["line"],
                    column=0,
                    rule_id="CPLX001",
                    severity=Severity.ERROR,
                    message=f"函数 '{func['name']}' 圈复杂度过高 ({func['complexity']})",
                    metric=QualityMetric.COMPLEXITY,
                    suggestion="考虑拆分函数或简化逻辑"
                ))
            elif func["complexity"] > QUALITY_THRESHOLDS[QualityMetric.COMPLEXITY]["warning"]:
                report.issues.append(QualityIssue(
                    file_path=str(path),
                    line=func["line"],
                    column=0,
                    rule_id="CPLX002",
                    severity=Severity.WARNING,
                    message=f"函数 '{func['name']}' 圈复杂度较高 ({func['complexity']})",
                    metric=QualityMetric.COMPLEXITY,
                    suggestion="考虑拆分函数或简化逻辑"
                ))
        
        style_issues = self.style_checker.check(source_code, str(path))
        report.issues.extend(style_issues)
        
        doc_issues, doc_coverage = self.doc_checker.check(source_code, str(path))
        report.issues.extend(doc_issues)
        report.metrics["documentation_coverage"] = doc_coverage
        
        type_issues, type_coverage = self.type_checker.check(source_code, str(path))
        report.issues.extend(type_issues)
        report.metrics["type_coverage"] = type_coverage
        
        security_issues = self.security_scanner.scan(source_code, str(path))
        report.issues.extend(security_issues)
        
        dup_issues, dup_rate = self.duplication_detector.detect(source_code, str(path))
        report.issues.extend(dup_issues)
        report.metrics["duplication_rate"] = dup_rate
        
        if self.run_external_tools and self.language == Language.PYTHON:
            pylint_issues = ExternalToolRunner.run_pylint(file_path)
            report.issues.extend(pylint_issues)
            
            mypy_issues = ExternalToolRunner.run_mypy(file_path)
            report.issues.extend(mypy_issues)
            
            ruff_issues = ExternalToolRunner.run_ruff(file_path)
            report.issues.extend(ruff_issues)
        
        report.score = self._calculate_score(report)
        
        return report
    
    def validate_directory(self, dir_path: str) -> QualityReport:
        """验证目录下所有代码文件"""
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"目录不存在: {dir_path}")
        
        report = QualityReport(
            project_path=str(path),
            language=self.language
        )
        
        extensions = self._get_extensions()
        
        for ext in extensions:
            for file_path in path.rglob(f"*{ext}"):
                if self._should_skip(file_path):
                    continue
                
                try:
                    file_report = self.validate_file(str(file_path))
                    report.files.append(file_report)
                    report.total_issues += len(file_report.issues)
                except Exception as e:
                    pass
        
        report.issues_by_severity = self._count_by_severity(report.files)
        report.issues_by_metric = self._count_by_metric(report.files)
        report.overall_score = self._calculate_overall_score(report.files)
        report.passed = report.overall_score >= 60 and report.issues_by_severity.get("error", 0) == 0
        report.recommendations = self._generate_recommendations(report)
        
        return report
    
    def _count_lines(self, source_code: str) -> Tuple[int, int, int]:
        """统计代码行数"""
        lines = source_code.split("\n")
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        in_multiline_string = False
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                blank_lines += 1
            elif stripped.startswith("#"):
                comment_lines += 1
            elif '"""' in stripped or "'''" in stripped:
                if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                    comment_lines += 1
                else:
                    in_multiline_string = not in_multiline_string
                    comment_lines += 1
            elif in_multiline_string:
                comment_lines += 1
            else:
                code_lines += 1
        
        return code_lines, comment_lines, blank_lines
    
    def _get_extensions(self) -> List[str]:
        """获取文件扩展名"""
        extensions = {
            Language.PYTHON: [".py"],
            Language.TYPESCRIPT: [".ts", ".tsx"],
            Language.JAVASCRIPT: [".js", ".jsx"],
            Language.VUE: [".vue"],
            Language.GO: [".go"],
        }
        return extensions.get(self.language, [".py"])
    
    def _should_skip(self, file_path: Path) -> bool:
        """判断是否跳过文件"""
        skip_patterns = [
            "__pycache__", ".git", ".venv", "venv", "node_modules",
            "dist", "build", ".eggs", "*.egg-info", "migrations"
        ]
        
        for pattern in skip_patterns:
            if pattern in str(file_path):
                return True
        
        return False
    
    def _calculate_score(self, report: FileQualityReport) -> float:
        """计算文件质量分数"""
        score = 100.0
        
        for issue in report.issues:
            if issue.severity == Severity.ERROR:
                score -= 10
            elif issue.severity == Severity.WARNING:
                score -= 5
            elif issue.severity == Severity.INFO:
                score -= 1
        
        if report.metrics.get("complexity", 0) > 15:
            score -= (report.metrics["complexity"] - 15) * 2
        
        if report.metrics.get("documentation_coverage", 100) < 50:
            score -= (50 - report.metrics["documentation_coverage"]) * 0.5
        
        if report.metrics.get("type_coverage", 100) < 80:
            score -= (80 - report.metrics["type_coverage"]) * 0.3
        
        return max(0, min(100, score))
    
    def _count_by_severity(self, files: List[FileQualityReport]) -> Dict[str, int]:
        """按严重程度统计问题"""
        counts = {}
        for file_report in files:
            for issue in file_report.issues:
                severity = issue.severity.value
                counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def _count_by_metric(self, files: List[FileQualityReport]) -> Dict[str, int]:
        """按指标统计问题"""
        counts = {}
        for file_report in files:
            for issue in file_report.issues:
                metric = issue.metric.value
                counts[metric] = counts.get(metric, 0) + 1
        return counts
    
    def _calculate_overall_score(self, files: List[FileQualityReport]) -> float:
        """计算总体质量分数"""
        if not files:
            return 0.0
        
        total_score = sum(f.score for f in files)
        return total_score / len(files)
    
    def _generate_recommendations(self, report: QualityReport) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if report.issues_by_severity.get("error", 0) > 0:
            recommendations.append(
                f"发现 {report.issues_by_severity['error']} 个错误级别问题，请优先修复"
            )
        
        if report.issues_by_metric.get("security", 0) > 0:
            recommendations.append(
                "发现安全问题，请立即处理"
            )
        
        if report.issues_by_metric.get("complexity", 0) > 5:
            recommendations.append(
                "存在较多复杂度问题，建议重构高复杂度函数"
            )
        
        avg_doc_coverage = sum(
            f.metrics.get("documentation_coverage", 0) for f in report.files
        ) / len(report.files) if report.files else 0
        
        if avg_doc_coverage < 50:
            recommendations.append(
                f"文档覆盖率仅 {avg_doc_coverage:.1f}%，建议添加更多文档"
            )
        
        avg_type_coverage = sum(
            f.metrics.get("type_coverage", 0) for f in report.files
        ) / len(report.files) if report.files else 0
        
        if avg_type_coverage < 80:
            recommendations.append(
                f"类型覆盖率仅 {avg_type_coverage:.1f}%，建议添加类型注解"
            )
        
        if not recommendations:
            recommendations.append("代码质量良好，继续保持！")
        
        return recommendations
    
    def generate_report(self, report: QualityReport, output_path: str = None) -> str:
        """生成质量报告"""
        lines = [
            "# 代码质量报告",
            "",
            f"**项目路径**: {report.project_path}",
            f"**语言**: {report.language.value}",
            f"**生成时间**: {report.generated_at}",
            f"**总体评分**: {report.overall_score:.1f}/100",
            f"**验证结果**: {'✅ 通过' if report.passed else '❌ 未通过'}",
            "",
            "## 问题统计",
            "",
            "### 按严重程度",
            "",
        ]
        
        for severity, count in sorted(report.issues_by_severity.items()):
            icon = {"error": "🔴", "warning": "🟡", "info": "🔵", "hint": "💡"}.get(severity, "⚪")
            lines.append(f"- {icon} **{severity}**: {count}")
        
        lines.extend([
            "",
            "### 按指标类型",
            "",
        ])
        
        for metric, count in sorted(report.issues_by_metric.items()):
            lines.append(f"- **{metric}**: {count}")
        
        lines.extend([
            "",
            "## 文件详情",
            "",
        ])
        
        for file_report in sorted(report.files, key=lambda x: x.score):
            lines.append(f"### {file_report.file_path}")
            lines.append(f"- **评分**: {file_report.score:.1f}")
            lines.append(f"- **代码行数**: {file_report.lines_of_code}")
            lines.append(f"- **文档覆盖率**: {file_report.metrics.get('documentation_coverage', 0):.1f}%")
            lines.append(f"- **类型覆盖率**: {file_report.metrics.get('type_coverage', 0):.1f}%")
            lines.append(f"- **问题数**: {len(file_report.issues)}")
            
            if file_report.issues:
                lines.append("")
                lines.append("**问题列表**:")
                lines.append("")
                for issue in file_report.issues[:10]:
                    lines.append(f"- L{issue.line}: [{issue.rule_id}] {issue.message}")
                if len(file_report.issues) > 10:
                    lines.append(f"- ... 还有 {len(file_report.issues) - 10} 个问题")
            
            lines.append("")
        
        lines.extend([
            "## 改进建议",
            "",
        ])
        
        for rec in report.recommendations:
            lines.append(f"- {rec}")
        
        lines.extend([
            "",
            "## 质量阈值配置",
            "",
            "| 指标 | 警告阈值 | 错误阈值 |",
            "|------|----------|----------|",
        ])
        
        for metric, thresholds in QUALITY_THRESHOLDS.items():
            lines.append(f"| {metric.value} | {thresholds['warning']} | {thresholds['error']} |")
        
        report_content = "\n".join(lines)
        
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_content)
        
        return report_content


def main():
    parser = argparse.ArgumentParser(
        description="代码质量自动验证器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 验证单个文件
  python code_quality_validator.py --file app/main.py
  
  # 验证目录
  python code_quality_validator.py --path app/ --output reports/
  
  # 完整检查（包括外部工具）
  python code_quality_validator.py --path src/ --full-check
  
  # 指定语言
  python code_quality_validator.py --path src/ --lang typescript
        """
    )
    
    parser.add_argument(
        "--file",
        help="要验证的文件路径"
    )
    
    parser.add_argument(
        "--path",
        help="要验证的目录路径"
    )
    
    parser.add_argument(
        "--output",
        default="reports",
        help="报告输出目录"
    )
    
    parser.add_argument(
        "--lang",
        choices=["python", "typescript", "javascript", "vue", "go"],
        default="python",
        help="目标语言"
    )
    
    parser.add_argument(
        "--full-check",
        action="store_true",
        help="运行完整检查（包括外部工具）"
    )
    
    parser.add_argument(
        "--no-external",
        action="store_true",
        help="不运行外部工具"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    if not args.file and not args.path:
        parser.error("必须指定 --file 或 --path")
    
    language = Language(args.lang)
    validator = CodeQualityValidator(
        language=language,
        run_external_tools=args.full_check and not args.no_external
    )
    
    print("=" * 60)
    print("代码质量自动验证器")
    print("=" * 60)
    
    if args.file:
        print(f"验证文件: {args.file}")
        report = validator.validate_file(args.file)
        
        print(f"\n文件评分: {report.score:.1f}/100")
        print(f"代码行数: {report.lines_of_code}")
        print(f"问题数量: {len(report.issues)}")
        
        if args.verbose and report.issues:
            print("\n问题列表:")
            for issue in report.issues:
                print(f"  L{issue.line}: [{issue.severity.value}] {issue.message}")
        
        output_file = Path(args.output) / f"quality_report_{Path(args.file).stem}.md"
        validator.generate_report(
            QualityReport(
                project_path=args.file,
                language=language,
                files=[report],
                total_issues=len(report.issues),
                overall_score=report.score
            ),
            str(output_file)
        )
        print(f"\n报告已生成: {output_file}")
        
    elif args.path:
        print(f"验证目录: {args.path}")
        report = validator.validate_directory(args.path)
        
        print(f"\n总体评分: {report.overall_score:.1f}/100")
        print(f"验证结果: {'✅ 通过' if report.passed else '❌ 未通过'}")
        print(f"文件数量: {len(report.files)}")
        print(f"问题总数: {report.total_issues}")
        
        print("\n问题统计:")
        for severity, count in sorted(report.issues_by_severity.items()):
            print(f"  {severity}: {count}")
        
        output_file = Path(args.output) / "quality_report.md"
        validator.generate_report(report, str(output_file))
        print(f"\n报告已生成: {output_file}")
    
    print("\n" + "=" * 60)
    
    sys.exit(0 if (args.file and report.score >= 60) or (args.path and report.passed) else 1)


if __name__ == "__main__":
    main()
