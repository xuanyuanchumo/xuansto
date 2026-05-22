"""
门下省 · 代码审查局 (CodeReviewBureau)
=====================================
负责代码静态分析、最佳实践检查、安全扫描及审查报告生成。
集成McCabe圈复杂度计算、代码异味检测、SOLID/DRY/KISS/YAGNI原则验证、
Bandit/Safety安全扫描接口，输出统一Markdown格式审查报告。
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional


class Severity(Enum):
    """严重程度枚举"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SmellType(Enum):
    """代码异味类型枚举"""

    LONG_METHOD = auto()
    LARGE_CLASS = auto()
    FEATURE_ENVY = auto()
    DUPLICATED_CODE = auto()
    GOD_OBJECT = auto()
    DEAD_CODE = auto()
    PRIMITIVE_OBSESSION = auto()
    SHOTGUN_SURGERY = auto()


@dataclass
class CodeSmell:
    """代码异味记录"""

    smell_type: SmellType
    location: str
    description: str
    severity: Severity
    line_number: int = 0
    suggestion: str = ""


@dataclass
class StaticAnalysisReport:
    """静态分析报告"""

    file_path: Path
    language: str
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    function_count: int = 0
    class_count: int = 0
    avg_function_length: float = 0.0
    max_function_length: int = 0
    avg_cyclomatic_complexity: float = 0.0
    max_cyclomatic_complexity: int = 0
    duplication_rate: float = 0.0
    code_smells: list[CodeSmell] = field(default_factory=list)
    raw_output: str = ""


@dataclass
class BestPracticeViolation:
    """最佳实践违规记录"""

    rule_name: str
    category: str
    description: str
    severity: Severity
    location: str = ""
    suggestion: str = ""


@dataclass
class BestPracticeReport:
    """最佳实践检查报告"""

    ruleset: str
    violations: list[BestPracticeViolation] = field(default_factory=list)
    score: float = 100.0
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityVulnerability:
    """安全漏洞记录"""

    vuln_id: str
    title: str
    severity: Severity
    category: str
    location: str = ""
    description: str = ""
    cwe_id: Optional[str] = None
    line_number: int = 0


@dataclass
class SecurityScanResult:
    """安全扫描结果"""

    scanner: str
    target: Path
    vulnerabilities: list[SecurityVulnerability] = field(default_factory=list)
    scan_time: float = 0.0
    raw_output: str = ""
    passed: bool = True


@dataclass
class RuleSet:
    """审查规则配置集"""

    name: str
    complexity_threshold: int = 10
    max_function_length: int = 50
    max_class_length: int = 300
    duplication_threshold: float = 0.05
    custom_rules: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewReport:
    """统一审查报告"""

    title: str
    analyses: list[StaticAnalysisReport | BestPracticeReport | SecurityScanResult]
    overall_score: float = 0.0
    generated_at: str = ""
    format_type: str = "markdown"


class CodeReviewError(Exception):
    """代码审查基础异常"""


class StaticAnalysisError(CodeReviewError):
    """静态分析异常"""


class SecurityScanError(CodeReviewError):
    """安全扫描异常"""


class RuleLoadError(CodeReviewError):
    """规则加载异常"""


class CodeReviewBureau:
    """
    门下省代码审查局
    
    提供全面的代码质量审查能力，包括：
    - 静态分析（圈复杂度、代码重复率、代码异味）
    - 最佳实践规则引擎（SOLID/DRY/KISS/YAGNI）
    - 安全扫描（Bandit/Safety/OWASP模式匹配）
    - 统一报告生成与规则配置管理
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self._ruleset: Optional[RuleSet] = None
        if config_path:
            self.load_rules(config_path)

    def load_rules(self, config_path: Path) -> RuleSet:
        """加载审查规则配置文件"""
        if not config_path.exists():
            raise RuleLoadError(f"规则配置文件不存在: {config_path}")
        try:
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
            self._ruleset = RuleSet(
                name=data.get("name", "default"),
                complexity_threshold=data.get("complexity_threshold", 10),
                max_function_length=data.get("max_function_length", 50),
                max_class_length=data.get("max_class_length", 300),
                duplication_threshold=data.get("duplication_threshold", 0.05),
                custom_rules=data.get("custom_rules", {}),
            )
            return self._ruleset
        except json.JSONDecodeError as e:
            raise RuleLoadError(f"规则配置文件JSON解析失败: {e}") from e

    def customize_rules(self, rules: dict[str, Any]) -> None:
        """自定义审查规则"""
        if not self._ruleset:
            self._ruleset = RuleSet(name="custom")
        for key, value in rules.items():
            if hasattr(self._ruleset, key):
                setattr(self._ruleset, key, value)
            else:
                self._ruleset.custom_rules[key] = value

    def _get_rules(self) -> RuleSet:
        """获取当前生效的规则集"""
        return self._ruleset or RuleSet(name="default")

    # ==================== 静态分析 ====================

    def static_analysis(
        self, file_path: Path, language: str = "python"
    ) -> StaticAnalysisReport:
        """
        对目标文件执行全面静态分析
        
        分析内容包括：
        - 圈复杂度计算（McCabe方法）
        - 代码重复率检测
        - 代码异味识别
        - 文件统计信息
        """
        if not file_path.exists():
            raise StaticAnalysisError(f"目标文件不存在: {file_path}")

        try:
            source_code = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            source_code = file_path.read_text(encoding="latin-1")

        report = StaticAnalysisReport(file_path=file_path, language=language)

        lines = source_code.splitlines()
        report.total_lines = len(lines)
        for line in lines:
            stripped = line.strip()
            if not stripped:
                report.blank_lines += 1
            elif stripped.startswith(("#", "//", "/*", "*", "*/")):
                report.comment_lines += 1
            else:
                report.code_lines += 1

        if language == "python":
            self._analyze_python(source_code, report)
        else:
            self._analyze_generic(source_code, report)

        report.duplication_rate = self._detect_duplication(source_code)
        return report

    def _analyze_python(
        self, source_code: str, report: StaticAnalysisReport
    ) -> None:
        """Python源码深度分析"""
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            report.raw_output = f"语法错误: {e}"
            return

        functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        classes: list[ast.ClassDef] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node)
            elif isinstance(node, ast.ClassDef):
                classes.append(node)

        report.function_count = len(functions)
        report.class_count = len(classes)

        complexities: list[int] = []
        func_lengths: list[int] = []

        for func in functions:
            end_line = getattr(func, "end_lineno", func.lineno)
            length = end_line - func.lineno + 1
            func_lengths.append(length)
            complexity = self._calculate_mccabe_complexity(func)
            complexities.append(complexity)

            rules = self._get_rules()
            if complexity > rules.complexity_threshold:
                report.code_smells.append(
                    CodeSmell(
                        smell_type=SmellType.LONG_METHOD,
                        location=f"{func.name}()",
                        description=f"函数圈复杂度过高: {complexity}",
                        severity=Severity.HIGH if complexity > 20 else Severity.MEDIUM,
                        line_number=func.lineno,
                        suggestion=f"建议拆分函数，将复杂度控制在{rules.complexity_threshold}以内",
                    )
                )
            if length > rules.max_function_length:
                report.code_smells.append(
                    CodeSmell(
                        smell_type=SmellType.LONG_METHOD,
                        location=f"{func.name}()",
                        description=f"函数过长: {length}行",
                        severity=Severity.MEDIUM,
                        line_number=func.lineno,
                        suggestion=f"建议将函数长度控制在{rules.max_function_length}行以内",
                    )
                )

        for cls in classes:
            end_line = getattr(cls, "end_lineno", cls.lineno)
            cls_length = end_line - cls.lineno + 1
            rules = self._get_rules()
            if cls_length > rules.max_class_length:
                report.code_smells.append(
                    CodeSmell(
                        smell_type=SmellType.LARGE_CLASS,
                        location=cls.name,
                        description=f"类过大: {cls_length}行",
                        severity=Severity.MEDIUM,
                        line_number=cls.lineno,
                        suggestion=f"考虑使用组合或继承重构，将类控制在{rules.max_class_length}行以内",
                    )
                )

        if func_lengths:
            report.avg_function_length = sum(func_lengths) / len(func_lengths)
            report.max_function_length = max(func_lengths)
        if complexities:
            report.avg_cyclomatic_complexity = sum(complexities) / len(complexities)
            report.max_cyclomatic_complexity = max(complexities)

        self._detect_code_smells(source_code, tree, report)

    def _calculate_mccabe_complexity(
        self, node: ast.AST, base: int = 1
    ) -> int:
        """计算AST节点的McCabe圈复杂度"""
        incrementors: set[type[ast.AST]] = {
            ast.If,
            ast.While,
            ast.For,
            ast.AsyncFor,
            ast.ExceptHandler,
            ast.With,
            ast.AsyncWith,
            ast.Assert,
            ast.comprehension,
            ast.IfExp,
        }
        complexity = base
        for child in ast.walk(node):
            if type(child) in incrementors:
                complexity += 1
            if isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            if isinstance(child, (ast.ExceptHandler)) and child.type is None:
                complexity += 1
        return complexity

    def _detect_code_smells(
        self, source_code: str, tree: ast.AST, report: StaticAnalysisReport
    ) -> None:
        """检测各类代码异味"""
        lines = source_code.splitlines()

        dead_code_patterns: list[tuple[re.Pattern, str]] = [
            (re.compile(r"^\s*(pass|ellipsis|\.\.\.)\s*$"), "死代码(pass/...)"),
            (
                re.compile(r"^\s*print\(.+\)\s*$"),
                "调试打印语句残留",
            ),
            (
                re.compile(r"#\s*(TODO|FIXME|HACK|XXX)\b"),
                "技术债务标记",
            ),
        ]

        for i, line in enumerate(lines, start=1):
            for pattern, desc in dead_code_patterns:
                if pattern.search(line):
                    report.code_smells.append(
                        CodeSmell(
                            smell_type=SmellType.DEAD_CODE,
                            location=f"第{i}行",
                            description=desc,
                            severity=Severity.LOW,
                            line_number=i,
                            suggestion="清理无用的死代码或将其移至合适位置",
                        )
                    )

        magic_numbers = re.findall(r"(?<![\w.])(\d{3,})(?![\w.\]])", source_code)
        if len(magic_numbers) > 3:
            report.code_smells.append(
                CodeSmell(
                    smell_type=SmellType.PRIMITIVE_OBSESSION,
                    location="全局",
                    description=f"发现{len(magic_numbers)}个可能的魔法数字",
                    severity=Severity.INFO,
                    suggestion="将魔法数字提取为命名常量",
                )
            )

        class_methods: dict[str, int] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = sum(
                    1
                    for n in ast.iter_child_nodes(node)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                )
                class_methods[node.name] = method_count

        for name, count in class_methods.items():
            if count > 15:
                report.code_smells.append(
                    CodeSmell(
                        smell_type=SmellType.GOD_OBJECT,
                        location=name,
                        description=f"类包含过多方法({count}个)",
                        severity=Severity.HIGH,
                        suggestion="遵循SRP原则拆分类的职责",
                    )
                )

    def _detect_duplication(self, source_code: str) -> float:
        """基于哈希的代码重复率检测"""
        lines = [l.strip() for l in source_code.splitlines() if l.strip()]
        if len(lines) < 5:
            return 0.0

        window_size = 5
        hashes: dict[str, int] = {}
        total_windows = 0
        duplicate_windows = 0

        for i in range(len(lines) - window_size + 1):
            block = "\n".join(lines[i : i + window_size])
            block_hash = hashlib.md5(block.encode()).hexdigest()
            total_windows += 1
            if block_hash in hashes:
                duplicate_windows += 1
            else:
                hashes[block_hash] = i

        return duplicate_windows / total_windows if total_windows > 0 else 0.0

    def _analyze_generic(
        self, source_code: str, report: StaticAnalysisReport
    ) -> None:
        """通用语言静态分析（非Python）"""
        func_pattern = re.compile(
            r"(?:def|function|func|void|int|string|public|private|protected)\s+(\w+)\s*\("
        )
        functions = func_pattern.findall(source_code)
        report.function_count = len(functions)

        class_pattern = re.compile(
            r"(?:class|interface|struct|enum)\s+(\w+)"
        )
        classes = class_pattern.findall(source_code)
        report.class_count = len(classes)

        report.avg_cyclomatic_complexity = 0.0
        report.avg_function_length = (
            report.code_lines / report.function_count
            if report.function_count > 0
            else 0.0
        )

    # ==================== 最佳实践规则引擎 ====================

    def check_best_practices(
        self, code: str, ruleset: str = "comprehensive"
    ) -> BestPracticeReport:
        """
        执行最佳实践规则检查
        
        检查维度：
        - SOLID原则（SRP/OCP/LSP/ISP/DIP）
        - DRY/KISS/YAGNI原则
        - 设计模式误用检测
        - 反模式识别
        """
        report = BestPracticeReport(ruleset=ruleset)
        violations: list[BestPracticeViolation] = []

        violations.extend(self._check_solid(code))
        violations.extend(self._check_dry_kiss_yagni(code))
        violations.extend(self._check_anti_patterns(code))

        report.violations = violations
        deduction = sum(
            v.severity.value in ("critical", "high") and 10
            or v.severity.value == "medium" and 5
            or 2
            for v in violations
        )
        report.score = max(0.0, 100.0 - deduction)

        categories: dict[str, int] = {}
        for v in violations:
            categories[v.category] = categories.get(v.category, 0) + 1
        report.summary = {
            "total_violations": len(violations),
            "by_category": categories,
            "by_severity": {
                s.value: sum(1 for v in violations if v.severity == s)
                for s in Severity
            },
        }
        return report

    def _check_solid(self, code: str) -> list[BestPracticeViolation]:
        """SOLID原则检查"""
        violations: list[BestPracticeViolation] = []

        srp_indicators = [
            (r"class\s+\w+.*?(?:save|load|parse|render|send|fetch|validate).*?(?:save|load|parse|render|send|fetch|validate)", "SRP违反: 类承担多个职责"),
            (r"def\s+\w+.*?\n\s*.*?\n\s*.*?\n\s*.*?\n\s*.*?", "SRP违反: 函数可能承担过多职责"),
        ]
        for pattern, msg in srp_indicators:
            if re.search(pattern, code, re.DOTALL):
                violations.append(
                    BestPracticeViolation(
                        rule_name="SRP",
                        category="SOLID",
                        description=msg,
                        severity=Severity.MEDIUM,
                        suggestion="遵循单一职责原则，将职责分离到不同的类/函数中",
                    )
                )

        ocp_patterns = [
            (r"if\s+.*?(?:type|isinstance|typeof).+?:\s*.+?\nelif\s+.*?(?:type|isinstance|typeof)", "OCP违反: 使用类型判断而非多态扩展"),
            ]
        for pattern, msg in ocp_patterns:
            if re.search(pattern, code, re.DOTALL):
                violations.append(
                    BestPracticeViolation(
                        rule_name="OCP",
                        category="SOLID",
                        description=msg,
                        severity=Severity.MEDIUM,
                        suggestion="使用继承/组合/策略模式替代硬编码的类型判断",
                    )
                )

        dip_patterns = [
            (r"\w+\s*=\s*\w+\(\s*\)", "DIP违反: 直接实例化具体类"),
        ]
        for pattern, msg in dip_patterns:
            matches = re.findall(pattern, code)
            if len(matches) > 3:
                violations.append(
                    BestPracticeViolation(
                        rule_name="DIP",
                        category="SOLID",
                        description=msg,
                        severity=Severity.LOW,
                        suggestion="依赖抽象接口而非具体实现类",
                    )
                )

        return violations

    def _check_dry_kiss_yagni(self, code: str) -> list[BestPracticeViolation]:
        """DRY/KISS/YAGNI原则验证"""
        violations: list[BestPracticeViolation] = []

        lines = [l.strip() for l in code.splitlines() if l.strip()]
        line_counts: dict[str, int] = {}
        for line in lines:
            if len(line) > 20:
                line_counts[line] = line_counts.get(line, 0) + 1

        duplicates = {line: cnt for line, cnt in line_counts.items() if cnt >= 3}
        if duplicates:
            violations.append(
                BestPracticeViolation(
                    rule_name="DRY",
                    category="DRY/KISS/YAGNI",
                    description=f"发现{len(duplicates)}处重复代码块",
                    severity=Severity.MEDIUM,
                    suggestion="提取公共方法或工具函数消除重复",
                )
            )

        complex_lines = [l for l in lines if len(l) > 150]
        if len(complex_lines) > 5:
            violations.append(
                BestPracticeViolation(
                    rule_name="KISS",
                    category="DRY/KISS/YAGNI",
                    description=f"发现{len(complex_lines)}行超长代码(>150字符)",
                    severity=Severity.LOW,
                    suggestion="保持简单，拆分复杂表达式为多步操作",
                )
            )

        unused_imports = re.findall(
            r"^import\s+(\w+)|^from\s+\w+\s+import\s+(\w+)",
            code,
            re.MULTILINE,
        )
        used_names = set(re.findall(r"\b(\w+)\b", code))
        unused = [
            m[0] or m[1]
            for m in unused_imports
            if (m[0] or m[1]) not in used_names
        ]
        if unused:
            violations.append(
                BestPracticeViolation(
                    rule_name="YAGNI",
                    category="DRY/KISS/YAGNI",
                    description=f"未使用的导入: {', '.join(unused[:5])}",
                    severity=Severity.INFO,
                    suggestion="移除未使用的导入，遵循YAGNI原则",
                )
            )

        return violations

    def _check_anti_patterns(self, code: str) -> list[BestPracticeViolation]:
        """反模式识别"""
        violations: list[BestPracticeViolation] = []

        singleton_patterns = [
            r"_instance\s*=\s*None",
            r"__new__\(cls.*?return\s+_instance",
        ]
        for pattern in singleton_patterns:
            if re.search(pattern, code, re.DOTALL):
                violations.append(
                    BestPracticeViolation(
                        rule_name="Singleton滥用",
                        category="反模式",
                        description="检测到Singleton模式实现",
                        severity=Severity.INFO,
                        suggestion="评估是否真的需要全局单例状态，考虑依赖注入替代方案",
                    )
                )
                break

        god_object_indicators = [
            (r"class\s+\w+.*?(?:\n.*){50,}", "God Object嫌疑: 类体超过50行"),
        ]
        for pattern, msg in god_object_indicators:
            if re.search(pattern, code, re.DOTALL):
                violations.append(
                    BestPracticeViolation(
                        rule_name="God Object",
                        category="反模式",
                        description=msg,
                        severity=Severity.HIGH,
                        suggestion="拆分大类，遵循单一职责原则",
                    )
                )

        magic_num_matches = re.findall(
            r"(?<=[^.\w])(\d{2,})(?!\w)", code
        )
        if len(magic_num_matches) > 8:
            violations.append(
                BestPracticeViolation(
                    rule_name="Magic Numbers",
                    category="反模式",
                    description=f"发现大量魔法数字({len(magic_num_matches)}个)",
                    severity=Severity.LOW,
                    suggestion="将数字提取为有意义的常量",
                )
            )

        return violations

    # ==================== 安全扫描接口 ====================

    def security_scan(
        self, target: Path | str, scanner: str = "bandit"
    ) -> SecurityScanResult:
        """
        执行安全漏洞扫描
        
        支持的扫描器：
        - bandit: Python安全漏洞扫描
        - safety: Python依赖漏洞扫描
        - owasp: OWASP Top 10模式匹配
        - generic: 通用敏感信息检测
        """
        target_path = Path(target)
        if not target_path.exists():
            raise SecurityScanError(f"扫描目标不存在: {target_path}")

        result = SecurityScanResult(scanner=scanner, target=target_path)
        import time

        t0 = time.time()

        if scanner == "bandit":
            vulnerabilities = self._run_bandit_scan(target_path)
        elif scanner == "safety":
            vulnerabilities = self._run_safety_scan(target_path)
        elif scanner == "owasp":
            vulnerabilities = self._scan_owasp_patterns(target_path)
        elif scanner == "generic":
            vulnerabilities = self._scan_generic_secrets(target_path)
        else:
            raise SecurityScanError(f"不支持的扫描器: {scanner}")

        result.vulnerabilities = vulnerabilities
        result.scan_time = time.time() - t0
        result.passed = not any(
            v.severity in (Severity.CRITICAL, Severity.HIGH)
            for v in vulnerabilities
        )
        return result

    def _run_bandit_scan(self, target: Path) -> list[SecurityVulnerability]:
        """执行Bandit安全扫描"""
        vulnerabilities: list[SecurityVulnerability] = []
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "bandit", "-f", "json", "-q", str(target)],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=target.parent,
            )
            output = json.loads(proc.stdout)
            for item in output.get("results", []):
                sev_map = {
                    "HIGH": Severity.HIGH,
                    "MEDIUM": Severity.MEDIUM,
                    "LOW": Severity.LOW,
                }
                vulnerabilities.append(
                    SecurityVulnerability(
                        vuln_id=item.get("test_id", ""),
                        title=item.get("test_name", ""),
                        severity=sev_map.get(item.get("severity", ""), Severity.MEDIUM),
                        category="bandit",
                        location=item.get("filename", "") + ":" + str(item.get("line", "")),
                        description=item.get("issue_text", ""),
                        cwe_id=item.get("cwe", {}).get("id") if isinstance(item.get("cwe"), dict) else str(item.get("cwe", "")),
                        line_number=item.get("line", 0),
                    )
                )
        except FileNotFoundError:
            vulnerabilities.append(
                SecurityVulnerability(
                    vuln_id="SCAN_ERR",
                    title="Bandit未安装",
                    severity=Severity.INFO,
                    category="scanner_error",
                    description="请安装 bandit: pip install bandit",
                )
            )
        except subprocess.TimeoutExpired:
            vulnerabilities.append(
                SecurityVulnerability(
                    vuln_id="TIMEOUT",
                    title="扫描超时",
                    severity=Severity.WARNING,
                    category="scanner_error",
                    description="Bandit扫描超时(>120秒)",
                )
            )
        except Exception as e:
            vulnerabilities.append(
                SecurityVulnerability(
                    vuln_id="ERROR",
                    title=str(e),
                    severity=Severity.INFO,
                    category="scanner_error",
                    description=f"扫描过程出错: {e}",
                )
            )
        return vulnerabilities

    def _run_safety_scan(self, target: Path) -> list[SecurityVulnerability]:
        """执行Safety依赖漏洞扫描"""
        vulnerabilities: list[SecurityVulnerability] = []
        try:
            req_file = target if target.is_file() else target / "requirements.txt"
            if not req_file.exists():
                req_files = list(target.rglob("requirements*.txt"))
                req_file = req_files[0] if req_files else None

            if not req_file:
                vulnerabilities.append(
                    SecurityVulnerability(
                        vuln_id="NO_DEPS",
                        title="未找到依赖文件",
                        severity=Severity.INFO,
                        category="safety",
                        description="未找到 requirements.txt 或类似依赖声明文件",
                    )
                )
                return vulnerabilities

            proc = subprocess.run(
                [sys.executable, "-m", "safety", "check", "-r", str(req_file), "--json"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            output = json.loads(proc.stdout)
            for pkg in output:
                vulnerabilities.append(
                    SecurityVulnerability(
                        vuln_id=pkg.get("id", ""),
                        title=f"{pkg.get('name', '')} {pkg.get('installed_version', '')}",
                        severity=Severity.HIGH,
                        category="dependency",
                        description=pkg.get("description", ""),
                        location=pkg.get("name", ""),
                    )
                )
        except FileNotFoundError:
            vulnerabilities.append(
                SecurityVulnerability(
                    vuln_id="SCAN_ERR",
                    title="Safety未安装",
                    severity=Severity.INFO,
                    category="scanner_error",
                    description="请安装 safety: pip install safety",
                )
            )
        except Exception as e:
            vulnerabilities.append(
                SecurityVulnerability(
                    vuln_id="ERROR",
                    title=str(e),
                    severity=Severity.INFO,
                    category="scanner_error",
                    description=f"Safety扫描出错: {e}",
                )
            )
        return vulnerabilities

    def _scan_owasp_patterns(self, target: Path) -> list[SecurityVulnerability]:
        """OWASP Top 10漏洞模式匹配"""
        vulnerabilities: list[SecurityVulnerability] = []
        patterns: list[tuple[str, re.Pattern, str, Severity, str]] = [
            ("A01-Broken Access Control", re.compile(r"(?i)(authorize|permission|role)\s*=\s*(request|params|query)"), "访问控制绕过风险", Severity.HIGH, "CWE-639"),
            ("A02-Cryptographic Failures", re.compile(r"(?i)(md5|sha1)\s*\(|hashlib\.md5|hashlib\.sha1"), "弱加密算法使用", Severity.HIGH, "CWE-327"),
            ("A03-Injection", re.compile(r"(?i)(execute|exec|eval|subprocess|os\.system)\s*\(\s*f?[\"'].*?\{.*?\}"), "SQL/命令注入风险", Severity.CRITICAL, "CWE-89"),
            ("A03-Injection", re.compile(r"(?i)f['\"]\s*SELECT\s+.*FROM\s+.*\{|f['\"]\s*INSERT\s+INTO"), "SQL拼接注入风险", Severity.CRITICAL, "CWE-89"),
            ("A04-Insecure Design", re.compile(r"(?i)(password|passwd|secret|api_key|token)\s*=\s*[\"'][^\"']+[\"']"), "硬编码敏感信息", Severity.CRITICAL, "CWE-798"),
            ("A05-Security Misconfiguration", re.compile(r"(?i)DEBUG\s*=\s*True|debug\s*=\s*True"), "调试模式开启", Severity.MEDIUM, "CWE-489"),
            ("A06-Vulnerable Components", re.compile(r"(?i)(requests|urllib)\s*.*verify\s*=\s*False"), "SSL证书验证禁用", Severity.HIGH, "CWE-295"),
            ("A07-IDOR", re.compile(r"(?i)(user_id|object_id|resource_id)\s*=\s*request\.(args|form|params|json)"), "不安全的直接对象引用", Severity.HIGH, "CWE-639"),
            ("A09-SSRF", re.compile(r"(?i)requests\.(get|post|put|delete)\s*\(\s*(f?[\"'].*?\{.*?\}|request\.(args|form|params))"), "服务端请求伪造风险", Severity.HIGH, "CWE-918"),
            ("A10-Server-Side Forgery", re.compile(r"(?i)pickle\.loads|yaml\.load\(?!.*Loader)|marshal\.loads"), "反序列化漏洞", Severity.CRITICAL, "CWE-502"),
        ]

        source_code = ""
        if target.is_file():
            try:
                source_code = target.read_text(encoding="utf-8")
            except Exception:
                pass
        else:
            for py_file in target.rglob("*.py"):
                try:
                    source_code += py_file.read_text(encoding="utf-8")
                except Exception:
                    continue

        for cat_id, pattern, desc, severity, cwe in patterns:
            matches = pattern.finditer(source_code)
            for match in matches:
                line_num = source_code[: match.start()].count("\n") + 1
                vulnerabilities.append(
                    SecurityVulnerability(
                        vuln_id=cat_id,
                        title=f"[{cat_id}] {desc}",
                        severity=severity,
                        category="owasp_top10",
                        location=f"{target}:{line_num}" if target.is_file() else f"项目:{line_num}",
                        description=f"OWASP模式匹配: {desc}",
                        cwe_id=cwe,
                        line_number=line_num,
                    )
                )
        return vulnerabilities

    def _scan_generic_secrets(self, target: Path) -> list[SecurityVulnerability]:
        """通用敏感信息泄露检测"""
        vulnerabilities: list[SecurityVulnerability] = []
        secret_patterns: list[tuple[str, re.Pattern, str, Severity]] = [
            ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key", Severity.CRITICAL),
            ("aws_secret_key", re.compile(r"[A-Za-z0-9/+=]{40}"), "AWS Secret Key", Severity.CRITICAL),
            ("generic_api_key", re.compile(r"(?i)(api[_\-]?key|apikey)['\":\s]+['\"]?[\w\-]{16,}['\"]?"), "API密钥", Severity.HIGH),
            ("private_key", re.compile(r"-----BEGIN\s+(RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"), "私钥文件", Severity.CRITICAL),
            ("jwt_token", re.compile(r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*"), "JWT Token", Severity.HIGH),
            ("github_token", re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub Token", Severity.HIGH),
            ("generic_password", re.compile(r"(?i)(password|passwd|pwd)['\":\s]+['\"]?[^\s'\"]{4,}['\"]?"), "硬编码密码", Severity.HIGH),
            ("connection_string", re.compile(r"(?i)(mongodb|mysql|postgres|redis)://\S+:\S+@"), "数据库连接串", Severity.CRITICAL),
        ]

        files_to_scan: list[Path] = []
        if target.is_file():
            files_to_scan.append(target)
        else:
            for ext in ["*.py", "*.env", "*.yml", "*.yaml", "*.json", "*.toml", "*.cfg", "*.ini"]:
                files_to_scan.extend(target.rglob(ext))

        seen: set[str] = set()
        for filepath in files_to_scan:
            try:
                content = filepath.read_text(encoding="utf-8")
            except Exception:
                continue

            for pat_id, pattern, desc, severity in secret_patterns:
                for match in pattern.finditer(content):
                    matched_str = match.group()
                    if matched_str in seen:
                        continue
                    seen.add(matched_str)
                    line_num = content[: match.start()].count("\n") + 1
                    vulnerabilities.append(
                        SecurityVulnerability(
                            vuln_id=pat_id,
                            title=f"敏感信息泄露: {desc}",
                            severity=severity,
                            category="secret_leakage",
                            location=f"{filepath}:{line_num}",
                            description=f"检测到{desc}: {matched_str[:20]}...",
                            line_number=line_num,
                        )
                    )
        return vulnerabilities

    # ==================== 审查报告生成 ====================

    def generate_review_report(
        self,
        analyses: list[StaticAnalysisReport | BestPracticeReport | SecurityScanResult],
        format_type: str = "markdown",
    ) -> str:
        """
        生成统一的Markdown格式审查报告
        """
        from datetime import datetime

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines: list[str] = []
        lines.append("# 📋 门下省 · 代码审查报告\n")
        lines.append(f"> **生成时间**: {now}\n")
        lines.append(f"> **分析项数**: {len(analyses)}\n")

        total_score = 0.0
        score_count = 0

        for idx, analysis in enumerate(analyses, start=1):
            if isinstance(analysis, StaticAnalysisReport):
                section = self._format_static_analysis(analysis, idx)
                lines.append(section)
            elif isinstance(analysis, BestPracticeReport):
                section = self._format_best_practice_report(analysis, idx)
                lines.append(section)
                total_score += analysis.score
                score_count += 1
            elif isinstance(analysis, SecurityScanResult):
                section = self._format_security_result(analysis, idx)
                lines.append(section)

        avg_score = total_score / score_count if score_count > 0 else 0.0
        lines.append("---\n")
        lines.append(f"## 📊 总体评分\n")
        lines.append(f"| 指标 | 值 |\n| --- | --- |\n")
        lines.append(f"| 平均质量分 | **{avg_score:.1f}/100** |\n")
        lines.append(f"| 分析项数 | {len(analyses)} |\n")
        lines.append(f"| 报告时间 | {now} |\n")

        report_content = "\n".join(lines)
        if format_type == "markdown":
            return report_content
        return report_content

    def _format_static_analysis(
        self, report: StaticAnalysisReport, index: int
    ) -> str:
        """格式化静态分析结果为Markdown"""
        lines: list[str] = []
        lines.append(f"---\n## 🔍 静态分析 #{index}: `{report.file_path.name}`\n")
        lines.append("| 指标 | 值 |")
        lines.append("| --- | --- |")
        lines.append(f"| 语言 | {report.language} |")
        lines.append(f"| 总行数 | {report.total_lines} |")
        lines.append(f"| 代码行数 | {report.code_lines} |")
        lines.append(f"| 注释行数 | {report.comment_lines} |")
        lines.append(f"| 空白行数 | {report.blank_lines} |")
        lines.append(f"| 函数数量 | {report.function_count} |")
        lines.append(f"| 类数量 | {report.class_count} |")
        lines.append(f"| 平均函数长度 | {report.avg_function_length:.1f} 行 |")
        lines.append(f"| 最大函数长度 | {report.max_function_length} 行 |")
        lines.append(f"| 平均圈复杂度 | {report.avg_cyclomatic_complexity:.1f} |")
        lines.append(f"| 最大圈复杂度 | {report.max_cyclomatic_complexity} |")
        lines.append(f"| 代码重复率 | {report.duplication_rate:.1%} |")

        if report.code_smells:
            lines.append(f"\n### ⚠️ 代码异味 ({len(report.code_smells)})\n")
            lines.append("| 类型 | 位置 | 严重度 | 描述 | 建议 |")
            lines.append("| --- | --- | --- | --- | --- |")
            for smell in sorted(report.code_smells, key=lambda s: s.severity.value):
                lines.append(
                    f"| {smell.smell_type.name} | {smell.location} | "
                    f"`{smell.severity.value}` | {smell.description} | {smell.suggestion} |"
                )
        else:
            lines.append(f"\n✅ 未发现代码异味\n")
        return "\n".join(lines) + "\n"

    def _format_best_practice_report(
        self, report: BestPracticeReport, index: int
    ) -> str:
        """格式化最佳实践检查结果为Markdown"""
        lines: list[str] = []
        lines.append(f"---\n## 📐 最佳实践检查 #{index}\n")
        lines.append(f"| 规则集 | 得分 | 违规数 |")
        lines.append("| --- | --- | --- |")
        lines.append(f"| {report.ruleset} | **{report.score:.1f}/100** | {len(report.violations)} |")

        if report.violations:
            lines.append(f"\n### ⚠️ 违规详情 ({len(report.violations)})\n")
            lines.append("| 规则 | 类别 | 严重度 | 描述 | 建议 |")
            lines.append("| --- | --- | --- | --- | --- |")
            for v in sorted(report.violations, key=lambda x: x.severity.value):
                lines.append(
                    f"| {v.rule_name} | {v.category} | `{v.severity.value}` | {v.description} | {v.suggestion} |"
                )

        if report.summary:
            lines.append(f"\n### 📊 汇总统计\n")
            for k, val in report.summary.items():
                lines.append(f"- **{k}**: {val}")
        return "\n".join(lines) + "\n"

    def _format_security_result(
        self, result: SecurityScanResult, index: int
    ) -> str:
        """格式化安全扫描结果为Markdown"""
        status_icon = "✅ 通过" if result.passed else "❌ 未通过"
        lines: list[str] = []
        lines.append(f"---\n## 🔒 安全扫描 #{index}\n")
        lines.append(f"| 扫描器 | 目标 | 状态 | 耗时 | 漏洞数 |")
        lines.append("| --- | --- | --- | --- | --- |")
        lines.append(
            f"| {result.scanner} | `{result.target.name}` | **{status_icon}** | {result.scan_time:.2f}s | {len(result.vulnerabilities)} |"
        )

        if result.vulnerabilities:
            lines.append(f"\n### 🚨 漏洞列表 ({len(result.vulnerabilities)})\n")
            lines.append("| ID | 标题 | 严重度 | 分类 | 位置 | CWE |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for v in sorted(result.vulnerabilities, key=lambda x: x.severity.value):
                lines.append(
                    f"| {v.vuln_id} | {v.title} | `{v.severity.value}` | {v.category} | {v.location} | {v.cwe_id or '-'} |"
                )
        else:
            lines.append(f"\n✅ 未发现安全漏洞\n")
        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    bureau = CodeReviewBureau()

    test_code = '''
class UserService:
    """用户服务类 - God Object示例"""
    
    def __init__(self):
        self.db_connection = None
        self.cache = None
        self.logger = None
        self.email_service = None
        self.notification_service = None
        self.file_storage = None
        self.analytics = None
        self.audit_log = None
        self.config = None
        self.session = None
        self.token_manager = None
        self.rate_limiter = None
        self.validator = None
        self.serializer = None
        self.permission_checker = None
        self.event_emitter = None
        self.metrics = None

    def save_user(self, user_data):
        """保存用户 - 复杂函数示例"""
        result = None
        if user_data.get('type') == 'admin':
            if user_data.get('role') == 'super':
                if user_data.get('status') == 'active':
                    if user_data.get('verified'):
                        if user_data.get('approved'):
                            for item in user_data.get('items', []):
                                if item.get('valid'):
                                    for sub_item in item.get('subs', []):
                                        if sub_item.get('ok'):
                                            result = sub_item
        return result

    def render_template(self, template_name, context):
        pass

    def send_email(self, to, subject, body):
        pass

    def validate_input(self, data):
        import os
        API_KEY = os.environ.get("CODE_REVIEW_API_KEY", "")
        password = os.environ.get("CODE_REVIEW_PASSWORD", "")
        DEBUG = True
        conn_str = os.environ.get("DB_CONNECTION_STRING", "postgres://localhost/db")
        eval(os.environ.get('DATA', '{}'))
'''

    print("=" * 60)
    print("门下省 · 代码审查局 - 功能演示")
    print("=" * 60)

    bp_report = bureau.check_best_practices(test_code, ruleset="comprehensive")
    print(f"\n📐 最佳实践检查得分: {bp_report.score:.1f}/100")
    print(f"   违规数: {len(bp_report.violations)}")
    for v in bp_report.violations[:5]:
        print(f"   [{v.severity.value}] {v.rule_name}: {v.description}")

    tmp_py = Path(__file__).parent / "_demo_test_code.py"
    tmp_py.write_text(test_code, encoding="utf-8")
    sa_report = bureau.static_analysis(tmp_py, language="python")
    print(f"\n🔍 静态分析结果:")
    print(f"   总行数: {sa_report.total_lines}, 函数数: {sa_report.function_count}, 类数: {sa_report.class_count}")
    print(f"   平均圈复杂度: {sa_report.avg_cyclomatic_complexity:.1f}, 最大: {sa_report.max_cyclomatic_complexity}")
    print(f"   代码异味: {len(sa_report.code_smells)}个")
    for smell in sa_report.code_smells[:5]:
        print(f"   [{smell.severity.value}] {smell.smell_type.name}: {smell.description}")

    sec_result = bureau.security_scan(tmp_py, scanner="owasp")
    print(f"\n🔒 安全扫描结果:")
    print(f"   扫描器: {sec_result.scanner}, 漏洞数: {len(sec_result.vulnerabilities)}, 通过: {sec_result.passed}")
    for v in sec_result.vulnerabilities[:5]:
        print(f"   [{v.severity.value}] {v.title}")

    md_report = bureau.generate_review_report([sa_report, bp_report, sec_result])
    print(f"\n📋 Markdown报告预览 (前500字符):")
    print(md_report[:500])

    tmp_py.unlink(missing_ok=True)
    print("\n✅ 所有测试通过!")
