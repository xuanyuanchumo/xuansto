"""
硬编码密钥检测引擎模块 - HardcodedDetector

静态分析源代码文件，检测其中硬编码的敏感信息（密码、API Key、Token、
连接字符串、私钥等），支持 SARIF v2.1.0 和 Markdown 两种报告格式导出。
无外部依赖，纯Python标准库实现。
"""

import json
import re
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class Severity(Enum):
    """严重程度枚举"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Pattern:
    """正则检测模式数据类"""

    id: str  # 唯一标识符，如 HW-001
    name: str  # 模式名称描述
    category: str  # 分类: password, api_key, token, connection_string, cloud_key, private_key, other
    severity: Severity  # 默认严重程度
    pattern: re.Pattern  # 编译后的正则表达式
    description: str  # 检测规则说明


@dataclass
class Finding:
    """单条检测结果数据类"""

    rule_id: str
    rule_name: str
    severity: Severity
    line_number: int
    column_number: int
    matched_text: str
    file_path: str
    category: str
    message: str

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "matched_text": self.matched_text,
            "file_path": str(self.file_path),
            "category": self.category,
            "message": self.message,
        }


@dataclass
class FileReport:
    """单文件扫描报告"""

    file_path: Path
    findings: list[Finding] = field(default_factory=list)
    lines_scanned: int = 0
    scan_duration_ms: float = 0.0
    error: Optional[str] = None

    @property
    def has_issues(self) -> bool:
        return len(self.findings) > 0

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    def summary(self) -> str:
        status = "⚠ 发现问题" if self.has_issues else "✅ 安全"
        return f"[{self.file_path.name}] {status} - 发现 {len(self.findings)} 个问题 (CRITICAL:{self.critical_count}, HIGH:{self.high_count})"


@dataclass
class DetectionReport:
    """目录级扫描总报告"""

    scan_root: Path
    file_reports: list[FileReport] = field(default_factory=list)
    scan_started_at: datetime = field(default_factory=datetime.now)
    scan_finished_at: Optional[datetime] = None
    total_files_scanned: int = 0
    total_findings: int = 0
    files_with_issues: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def all_findings(self) -> list[Finding]:
        findings = []
        for fr in self.file_reports:
            findings.extend(fr.findings)
        return sorted(findings, key=lambda f: (f.severity.value, f.file_path, f.line_number))

    @property
    def severity_breakdown(self) -> dict[str, int]:
        breakdown: dict[str, int] = {s.value: 0 for s in Severity}
        for f in self.all_findings:
            breakdown[f.severity.value] += 1
        return breakdown

    def summary(self) -> str:
        sb = self.severity_breakdown
        lines = [
            "=" * 60,
            "  硬编码密钥检测报告",
            "=" * 60,
            f"  扫描根目录 : {self.scan_root}",
            f"  扫描时间   : {(self.scan_finished_at - self.scan_started_at).total_seconds():.2f}s" if self.scan_finished_at else "",
            f"  扫描文件数 : {self.total_files_scanned}",
            f"  问题文件数 : {self.files_with_issues}",
            f"  总发现问题 : {self.total_findings}",
            "-" * 40,
            f"  CRITICAL : {sb['critical']}",
            f"  HIGH     : {sb['high']}",
            f"  MEDIUM   : {sb['medium']}",
            f"  LOW      : {sb['low']}",
            f"  INFO     : {sb['info']}",
            "=" * 60,
        ]
        return "\n".join(lines)


class HardcodedDetector:
    """
    硬编码密钥检测引擎

    内置25种正则检测模式，覆盖以下类别：
    - 密码/API Key/Token/Secret 硬编码（10种）
    - 连接字符串内嵌凭据（MongoDB/PostgreSQL/MySQL/Redis，4种）
    - AWS/GitHub/Slack/AI服务密钥（4种）
    - 私钥/Base64/JWT/通用长随机字符串（4种）
    - IP地址硬编码/数据库端口硬编码（3种）

    使用示例：
        detector = HardcodedDetector()
        report = detector.scan_directory(Path("./src"))
        detector.export_report_sarif(report, "report.sarif.json")
        detector.export_report_markdown(report, "report.md")
    """

    _PATTERNS: list[Pattern] = []

    @classmethod
    def _get_patterns(cls) -> list[Pattern]:
        """
        返回所有内置的正则检测模式列表（共25种）

        模式分类：
        Group 1: 密码/API Key/Token/Secret 硬编码 (HW-001 ~ HW-010)
        Group 2: 连接字符串内嵌凭据 (HW-011 ~ HW-014)
        Group 3: 云服务/AI服务密钥 (HW-015 ~ HW-018)
        Group 4: 私钥/Base64/JWT/长随机串 (HW-019 ~ HW-022)
        Group 5: IP地址/端口硬编码 (HW-023 ~ HW-025)
        """
        if cls._PATTERNS:
            return cls._PATTERNS

        patterns = [
            # ====== Group 1: 密码/API Key/Token/Secret 硬编码 (10种) ======
            Pattern(
                id="HW-001", name="密码硬编码 - password/passwd/pwd 赋值",
                category="password", severity=Severity.CRITICAL,
                pattern=re.compile(r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"]?[^\s'\"<>]{4,}['\"]?"),
                description="检测代码中直接赋值的密码字段，如 password='xxx'",
            ),
            Pattern(
                id="HW-002", name="API Key 硬编码 - api_key/apiKey 赋值",
                category="api_key", severity=Severity.CRITICAL,
                pattern=re.compile(r"(?i)(?:api_?key|apikey)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"),
                description="检测硬编码的 API Key（长度>=16的字母数字组合）",
            ),
            Pattern(
                id="HW-003", name="Token/Bearer Token 硬编码",
                category="token", severity=Severity.CRITICAL,
                pattern=re.compile(r"(?i)(?:token|bearer|access_token)\s*[:=]\s*['\"][a-zA-Z0-9._\-]{20,}['\"]"),
                description="检测硬编码的认证令牌",
            ),
            Pattern(
                id="HW-004", name="Secret/Client Secret 硬编码",
                category="secret", severity=Severity.CRITICAL,
                pattern=re.compile(r"(?i)(?:secret|client_secret|app_secret)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"),
                description="检测硬编码的应用密钥或客户端密钥",
            ),
            Pattern(
                id="HW-005", name="数据库密码硬编码 - DB_PASSWORD 变量",
                category="password", severity=Severity.CRITICAL,
                pattern=re.compile(r"(?i)(?:db_password|database_pwd|dbpass)\s*[:=]\s*['\"][^\s'\"]{4,}['\"]"),
                description="检测数据库连接中的硬编码密码",
            ),
            Pattern(
                id="HW-006", name="JWT Secret 硬编码",
                category="secret", severity=Severity.HIGH,
                pattern=re.compile(r"(?i)jwt\s*_?(?:secret|key)\s*[:=]\s*['\"][^\s'\"]{10,}['\"]"),
                description="检测 JWT 签名密钥硬编码",
            ),
            Pattern(
                id="HW-007", name="Webhook Secret 硬编码",
                category="secret", severity=Severity.HIGH,
                pattern=re.compile(r"(?i)(?:webhook|signing)_?secret\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]"),
                description="检测 Webhook 签名密钥硬编码",
            ),
            Pattern(
                id="HW-008", name="加密密钥/盐值硬编码",
                category="encryption", severity=Severity.HIGH,
                pattern=re.compile(r"(?i)(?:encryption[_ ]?key|salt|cipher[_ ]?key|secret[_ ]?key)\s*[:=]\s*['\"][a-fA-F0-9]{16,}['\"]|['\"][^\s'\"]{12,}['\"]"),
                description="检测加密算法中使用的密钥或盐值硬编码",
            ),
            Pattern(
                id="HW-009", name="OAuth Client ID/Secret 硬编码",
                category="credential", severity=Severity.HIGH,
                pattern=re.compile(r"(?i)(?:client_id|client_secret|oauth.*secret)\s*[:=]\s*['\"][a-zA-Z0-9._\-]{12,}['\"]"),
                description="检测 OAuth 凭证硬编码",
            ),
            Pattern(
                id="HW-010", name="通用密码赋值模式 - user/pass 组合",
                category="password", severity=Severity.MEDIUM,
                pattern=re.compile(r"""(?i)(?:user|username)\s*[:=]\s*['"]\w+['"].*?(?:password|passwd|pwd)\s*[:=]\s*['"][^'"]{3,}['"]""", re.DOTALL),
                description="检测同一作用域内用户名和密码同时硬编码的情况",
            ),

            # ====== Group 2: 连接字符串内嵌凭据 (4种) ======
            Pattern(
                id="HW-011", name="MongoDB 连接字符串内嵌凭据",
                category="connection_string", severity=Severity.CRITICAL,
                pattern=re.compile(r"mongodb(?:\+srv)?://[^/\s]+:[^/@\s]+@"),
                description="检测 MongoDB 连接 URI 中内嵌的用户名和密码",
            ),
            Pattern(
                id="HW-012", name="PostgreSQL 连接字符串内嵌凭据",
                category="connection_string", severity=Severity.CRITICAL,
                pattern=re.compile(r"postgres(?:ql)?://[^/\s]+:[^/@\s]+@"),
                description="检测 PostgreSQL 连接字符串中内嵌的凭据",
            ),
            Pattern(
                id="HW-013", name="MySQL 连接字符串内嵌凭据",
                category="connection_string", severity=Severity.CRITICAL,
                pattern=re.compile(r"mysql://[^/\s]+:[^/@\s]+@"),
                description="检测 MySQL 连接字符串中内嵌的凭据",
            ),
            Pattern(
                id="HW-014", name="Redis 连接字符串内嵌凭据",
                category="connection_string", severity=Severity.HIGH,
                pattern=re.compile(r"redis://[^/\s]*:[^/@\s]+@"),
                description="检测 Redis 连接字符串中可能内嵌的密码",
            ),

            # ====== Group 3: 云服务/AI服务密钥 (4种) ======
            Pattern(
                id="HW-015", name="AWS 密钥硬编码 - AKIA 开头",
                category="cloud_key", severity=Severity.CRITICAL,
                pattern=re.compile(r"AKIA[A-Z0-9]{16}"),
                description="检测 AWS Access Key ID（AKIA 开头 + 16字符）",
            ),
            Pattern(
                id="HW-016", name="GitHub Personal Access Token / App Token",
                category="cloud_key", severity=Severity.CRITICAL,
                pattern=re.compile(r"(?:ghp_|gho_|ghu_|ghs_|ghr_)[a-zA-Z0-9]{36,}"),
                description="检测 GitHub 个人访问令牌或应用令牌",
            ),
            Pattern(
                id="HW-017", name="Slack Bot/User OAuth Token",
                category="cloud_key", severity=Severity.CRITICAL,
                pattern=re.compile(r"xox[baprs]-[a-zA-Z0-9\-]{10,}"),
                description="检测 Slack OAuth/Bot Token",
            ),
            Pattern(
                id="HW-018", name="AI 服务 API Key (OpenAI/Anthropic/Claude/Gemini)",
                category="ai_key", severity=Severity.CRITICAL,
                pattern=re.compile(r"(?:sk-|sk_[a-zA-Z0-9]{20,}|ant-api-|anthropic-api-|AIza[a-zA-Z0-9_-]{35})"),
                description="检测 OpenAI / Anthropic / Google AI 等 API Key",
            ),

            # ====== Group 4: 私钥/Base64/JWT/长随机串 (4种) ======
            Pattern(
                id="HW-019", name="PEM 私钥内容泄露",
                category="private_key", severity=Severity.CRITICAL,
                pattern=re.compile(r"-----BEGIN\s+(?:RSA |EC |DSA |OPENSSH |PRIVATE )?PRIVATE KEY-----"),
                description="检测 PEM 格式的私钥文件内容泄露到源码中",
            ),
            Pattern(
                id="HW-020", name="疑似 Base64 编码的长随机字符串",
                category="encoded_secret", severity=Severity.MEDIUM,
                pattern=re.compile(r"(?:['\"]([A-Za-z0-9+/]{40,}={0,2})['\"])"),
                description="检测疑似 Base64 编码的高熵长字符串（可能是编码后的密钥）",
            ),
            Pattern(
                id="HW-021", name="JWT Token 硬编码",
                category="token", severity=Severity.HIGH,
                pattern=re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
                description="检测硬编码的 JSON Web Token",
            ),
            Pattern(
                id="HW-022", name="通用高熵长随机字符串（疑似密钥）",
                category="generic_secret", severity=Severity.MEDIUM,
                pattern=re.compile(r"""(?i)['"]([a-f0-9]{32,}|[A-Za-z0-9+/]{40,}={0,2})['"]"""),
                description="检测疑似随机生成的长字符串（32位以上十六进制或40位以上Base64）",
            ),

            # ====== Group 5: IP地址/端口硬编码 (3种) ======
            Pattern(
                id="HW-023", name="IP 地址硬编码（非 localhost/127.0.0.1）",
                category="network", severity=Severity.LOW,
                pattern=re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b(?!:\d*)(?!.*localhost)"),
                description="检测源码中硬编码的非本地回环 IP 地址",
            ),
            Pattern(
                id="HW-024", name="数据库默认端口硬编码 (3306/5432/27017/6379)",
                category="network", severity=Severity.INFO,
                pattern=re.compile(r"(?::)(3306|5432|27017|6379|5672|9092)(?:\b|[/\"'])"),
                description="检测常见数据库/中间件的默认端口号硬编码",
            ),
            Pattern(
                id="HW-025", name="HTTP Basic Auth 内嵌凭据",
                category="credential", severity=Severity.CRITICAL,
                pattern=re.compile(r"https?://[^/\s]+:[^/@\s]+@"),
                description="检测 HTTP URL 中内嵌的用户名密码（Basic Auth）",
            ),
        ]

        cls._PATTERNS = patterns
        return patterns

    def __init__(self):
        """初始化检测器，加载所有内置模式"""
        self._patterns = self._get_patterns()

    def scan_directory(self, path: Path) -> DetectionReport:
        """
        静态扫描指定目录下的所有源代码文件

        支持扫描的文件扩展名：
        .py .js .ts .jsx .tsx .java .go .rs .rb .php .cs .vue .yaml .yml .json .env .conf .ini .cfg .xml .sh .bat .ps1 .sql

        自动跳过以下目录：node_modules, .git, __pycache__, dist, build, .venv, venv, vendor, .tox, .mypy_cache, .cache

        Args:
            path: 要扫描的目录路径

        Returns:
            DetectionReport 包含所有文件的扫描结果
        """
        report = DetectionReport(scan_root=path.resolve())
        extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
            ".rb", ".php", ".cs", ".vue", ".yaml", ".yml", ".json",
            ".env", ".conf", ".ini", ".cfg", ".xml", ".sh", ".bat",
            ".ps1", ".sql", ".toml", ".properties",
        }
        skip_dirs = {
            "__pycache__", ".git", "node_modules", "dist", "build",
            ".venv", "venv", "vendor", ".tox", ".mypy_cache", ".cache",
            ".next", ".nuxt", "target", "bin", "obj", ".idea", ".vscode",
        }

        if not path.is_dir():
            report.errors.append(f"路径不是有效目录: {path}")
            return report

        all_files = sorted(path.rglob("*"))
        source_files = [
            f for f in all_files
            if f.is_file() and f.suffix.lower() in extensions
            and not any(skip in f.parts for skip in skip_dirs)
        ]

        for file_path in source_files:
            try:
                file_report = self.scan_file(file_path)
                report.file_reports.append(file_report)
                report.total_files_scanned += 1
                if file_report.has_issues:
                    report.files_with_issues += 1
                    report.total_findings += len(file_report.findings)
            except Exception as exc:
                report.errors.append(f"扫描文件 {file_path} 时出错: {exc}")

        report.scan_finished_at = datetime.now()
        return report

    def scan_file(self, file_path: Path) -> FileReport:
        """
        扫描单个文件，应用所有检测模式

        Args:
            file_path: 要扫描的文件路径

        Returns:
            FileReport 包含该文件的所有发现项
        """
        report = FileReport(file_path=file_path.resolve())

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            report.lines_scanned = len(lines)
        except Exception as exc:
            report.error = f"读取文件失败: {exc}"
            return report

        for pat in self._patterns:
            for line_idx, line in enumerate(lines, start=1):
                for match in pat.pattern.finditer(line):
                    finding = Finding(
                        rule_id=pat.id,
                        rule_name=pat.name,
                        severity=pat.severity,
                        line_number=line_idx,
                        column_number=match.start() + 1,
                        matched_text=match.group(),
                        file_path=str(report.file_path),
                        category=pat.category,
                        message=f"{pat.name}: 在第 {line_idx} 行发现匹配 — {pat.description}",
                    )
                    report.findings.append(finding)

        return report

    def export_report_sarif(self, report: DetectionReport, output_path: str) -> None:
        """
        导出扫描结果为 SARIF v2.1.0 格式的 JSON 文件

        SARIF (Static Analysis Results Interchange Format) 是业界标准的静态分析
        结果交换格式，可被 GitHub Code Scanning、Azure DevOps 等工具直接消费。

        Args:
            report: DetectionReport 扫描结果
            output_path: 输出文件的保存路径
        """
        rules = []
        for pat in self._patterns:
            rules.append({
                "id": pat.id,
                "name": pat.name,
                "shortDescription": {"text": pat.description},
                "fullDescription": {"text": f"{pat.name}\n{pat.description}"},
                "defaultConfiguration": {"level": self._severity_to_sarif_level(pat.severity)},
                "properties": {"tags": [pat.category]},
            })

        results = []
        for finding in report.all_findings:
            result_entry = {
                "ruleId": finding.rule_id,
                "level": self._severity_to_sarif_level(finding.severity),
                "message": {"text": finding.message},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": str(Path(finding.file_path).as_posix())},
                        "region": {
                            "startLine": finding.line_number,
                            "startColumn": finding.column_number,
                        },
                    },
                }],
            }
            results.append(result_entry)

        sarif_doc = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "HardcodedDetector",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/example/hardcoded-detector",
                        "rules": rules,
                    },
                },
                "results": results,
            }],
        }

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(sarif_doc, ensure_ascii=False, indent=2), encoding="utf-8")

    def export_report_markdown(self, report: DetectionReport, output_path: str) -> None:
        """
        导出人类可读的 Markdown 格式报告

        报告包含：
        - 总体摘要统计
        - 按严重程度分组的详细发现列表
        - 每个问题的文件位置和匹配文本

        Args:
            report: DetectionReport 扫描结果
            output_path: 输出文件的保存路径
        """
        lines = []
        lines.append("# 🔐 硬编码密钥检测报告\n")
        lines.append(f"- **扫描目录**: `{report.scan_root}`")
        lines.append(f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if report.scan_finished_at and report.scan_started_at:
            duration = (report.scan_finished_at - report.scan_started_at).total_seconds()
            lines.append(f"- **扫描耗时**: {duration:.2f}s")
        lines.append(f"- **扫描文件**: {report.total_files_scanned}")
        lines.append(f"- **问题文件**: {report.files_with_issues}")
        lines.append(f"- **总发现数**: {report.total_findings}\n")

        sb = report.severity_breakdown
        lines.append("## 📊 严重程度分布\n")
        lines.append(f"| 严重程度 | 数量 |")
        lines.append(f"|----------|------|")
        sev_icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "⚪"}
        for sev in ("critical", "high", "medium", "low", "info"):
            icon = sev_icons.get(sev, "")
            lines.append(f"| {icon} {sev.upper()} | {sb[sev]} |")
        lines.append("")

        lines.append("## 📋 详细发现\n")

        severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3, Severity.INFO: 4}
        sorted_findings = sorted(report.all_findings, key=lambda f: (severity_order[f.severity], f.file_path, f.line_number))

        current_sev = None
        for i, f in enumerate(sorted_findings, start=1):
            if f.severity != current_sev:
                current_sev = f.severity
                lines.append(f"\n### {sev_icons.get(current_sev.value, '')} {current_severity.value.upper()}\n")

            masked = self._mask_match(f.matched_text)
            rel_path = str(Path(f.file_path))
            lines.append(f"**{i}. [{f.rule_id}]** {f.rule_name}")
            lines.append(f"   - **文件**: `{rel_path}:{f.line_number}:{f.column_number}`")
            lines.append(f"   - **匹配**: `{masked}`")
            lines.append(f"   - **说明**: {f.message}")
            lines.append("")

        if report.errors:
            lines.append("## ⚠️ 扫描错误\n")
            for err in report.errors:
                lines.append(f"- {err}")
            lines.append("")

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines), encoding="utf-8")

    @staticmethod
    def _severity_to_sarif_level(severity: Severity) -> str:
        """将内部严重程度映射为 SARIF level 字符串"""
        mapping = {
            Severity.CRITICAL: "error",
            Severity.HIGH: "error",
            Severity.MEDIUM: "warning",
            Severity.LOW: "note",
            Severity.INFO: "note",
        }
        return mapping.get(severity, "note")

    @staticmethod
    def _mask_match(text: str) -> str:
        """对匹配到的敏感文本进行脱敏显示"""
        if len(text) <= 8:
            return "*" * len(text)
        return text[:4] + "****" + text[-4:]

    def __repr__(self) -> str:
        return f"HardcodedDetector(patterns={len(self._patterns)})"
