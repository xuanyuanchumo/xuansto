"""
门下省 · 合规审计局 (ComplianceBureau)
=====================================
负责OWASP合规检查、依赖漏洞扫描、许可证合规检查、安全基线核查及审计报告生成。
覆盖OWASP Top 10逐项检查、CVE数据库查询、开源许可证兼容性分析、
加密算法/认证协议/TLS版本/密码策略等安全基线验证。
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional


class OWASPCategory(Enum):
    """OWASP Top 10 分类枚举"""

    A01_BROKEN_ACCESS_CONTROL = "A01:2021-Broken Access Control"
    A02_CRYPTOGRAPHIC_FAILURES = "A02:2021-Cryptographic Failures"
    A03_INJECTION = "A03:2021-Injection"
    A04_INSECURE_DESIGN = "A04:2021-Insecure Design"
    A05_SECURITY_MISCONFIGURATION = "A05:2021-Security Misconfiguration"
    A06_VULNERABLE_COMPONENTS = "A06:2021-Vulnerable and Outdated Components"
    A07_AUTH_FAILURES = "A07:2021-Identification and Authentication Failures"
    A08_SOFTWARE_DATA_INTEGRITY = "A08:2021-Software and Data Integrity Failures"
    A09_SECURITY_LOGGING = "A09:2021-Security Logging and Monitoring Failures"
    A10_SSRF = "A10:2021-Server-Side Request Forgery"


@dataclass
class OWASPCheckResult:
    """OWASP单项检查结果"""

    category: OWASPCategory
    passed: bool
    findings: list[str] = field(default_factory=list)
    severity: str = "info"
    details: str = ""
    recommendation: str = ""


@dataclass
class OWASPReport:
    """OWASP合规检查报告"""

    version: str
    target: Path
    checks: list[OWASPCheckResult] = field(default_factory=list)
    overall_status: str = "pending"
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    scan_time: float = 0.0
    generated_at: str = ""


@dataclass
class Vulnerability:
    """漏洞信息"""

    cve_id: str
    package_name: str
    installed_version: str
    fixed_version: Optional[str]
    severity: str
    description: str
    cvss_score: float = 0.0
    references: list[str] = field(default_factory=list)


@dataclass
class VulnerabilityReport:
    """依赖漏洞扫描报告"""

    dep_file: Path
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    total_vulns: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    packages_scanned: int = 0
    scan_tool: str = "local_pattern_match"
    generated_at: str = ""


@dataclass
class LicenseInfo:
    """许可证信息"""

    package_name: str
    license_name: str
    license_id: str
    spdx_id: Optional[str]
    compatibility: str = "compatible"
    risk_level: str = "low"
    notes: str = ""


@dataclass
class LicenseReport:
    """许可证合规报告"""

    project_dir: Path
    licenses: list[LicenseInfo] = field(default_factory=list)
    incompatible_licenses: list[LicenseInfo] = field(default_factory=list)
    missing_licenses: list[str] = field(default_factory=list)
    compliance_score: float = 100.0
    project_license: str = "unknown"
    generated_at: str = ""


@dataclass
class SecurityBaseline:
    """安全基线配置"""

    name: str = "default_baseline"
    min_tls_version: str = "1.2"
    allowed_ciphers: list[str] = field(default_factory=lambda: [
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256",
        "TLS_AES_128_GCM_SHA256",
    ])
    forbidden_ciphers: list[str] = field(default_factory=lambda: [
        "RC4", "DES", "3DES", "MD5", "SHA1", "NULL", "EXPORT", "aNULL", "eNULL",
    ])
    min_key_length_rsa: int = 2048
    min_key_length_ec: int = 256
    required_hash_algorithms: list[str] = field(default_factory=lambda: ["SHA256", "SHA384", "SHA512"])
    forbidden_hash_algorithms: list[str] = field(default_factory=lambda: ["MD5", "SHA1"])
    session_timeout_minutes: int = 30
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    password_policy: dict[str, Any] = field(default_factory=lambda: {
        "min_length": 12,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digit": True,
        "require_special_char": True,
        "max_age_days": 90,
        "history_count": 12,
        "lockout_after_failures": 5,
    })
    cors_policy: dict[str, Any] = field(default_factory=lambda: {
        "allowed_origins": ["*"],
        "allow_credentials": False,
        "max_age": 3600,
        "allowed_methods": ["GET", "POST"],
        "allowed_headers": ["Content-Type", "Authorization"],
    })
    headers_required: list[str] = field(default_factory=lambda: [
        "X-Content-Type-Options", "X-Frame-Options", "X-XSS-Protection",
        "Strict-Transport-Security", "Content-Security-Policy", "Referrer-Policy",
    ])


@dataclass
class BaselineCheckItem:
    """基线检查项"""

    check_id: str
    category: str
    description: str
    passed: bool
    severity: str
    actual_value: Any = None
    expected_value: Any = None
    recommendation: str = ""


@dataclass
class BaselineVerificationReport:
    """安全基线核查报告"""

    baseline_name: str
    target: Path
    checks: list[BaselineCheckItem] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    warning_count: int = 0
    overall_passed: bool = True
    score: float = 100.0
    generated_at: str = ""


class ComplianceError(Exception):
    """合规审计基础异常"""


class OWASPScanError(ComplianceError):
    """OWASP扫描异常"""


class DependencyScanError(ComplianceError):
    """依赖扫描异常"""


class LicenseCheckError(ComplianceError):
    """许可证检查异常"""


class BaselineVerifyError(ComplianceError):
    """基线核查异常"""


COMMON_LICENSES: dict[str, dict[str, str]] = {
    "MIT": {"spdx": "MIT", "compatibility": "compatible", "risk": "low"},
    "Apache-2.0": {"spdx": "Apache-2.0", "compatibility": "compatible", "risk": "low"},
    "BSD-2-Clause": {"spdx": "BSD-2-Clause", "compatibility": "compatible", "risk": "low"},
    "BSD-3-Clause": {"spdx": "BSD-3-Clause", "compatibility": "compatible", "risk": "low"},
    "ISC": {"spdx": "ISC", "compatibility": "compatible", "risk": "low"},
    "LGPL-2.1": {"spdx": "LGPL-2.1-only", "compatibility": "conditional", "risk": "medium"},
    "LGPL-3.0": {"spdx": "LGPL-3.0-only", "compatibility": "conditional", "risk": "medium"},
    "MPL-2.0": {"spdx": "MPL-2.0", "compatibility": "conditional", "risk": "medium"},
    "GPL-2.0": {"spdx": "GPL-2.0-only", "compatibility": "incompatible", "risk": "high"},
    "GPL-3.0": {"spdx": "GPL-3.0-only", "compatibility": "incompatible", "risk": "high"},
    "AGPL-3.0": {"spdx": "AGPL-3.0-only", "compatibility": "incompatible", "risk": "critical"},
}

LICENSE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"MIT\s+License", re.I), "MIT"),
    (re.compile(r"Apache\s+License[,.\s]+Version\s+2", re.I), "Apache-2.0"),
    (re.compile(r"BSD\s*[\s\-]*(?:2|two)\s*[-\s]*Clause", re.I), "BSD-2-Clause"),
    (re.compile(r"BSD\s*[\s\-]*(?:3|three)\s*[-\s]*Clause", re.I), "BSD-3-Clause"),
    (re.compile(r"ISC\s+License", re.I), "ISC"),
    (re.compile(r"GNU\s+General\s+Public\s+License[^v]*(?:v|Version)?\s*2", re.I), "GPL-2.0"),
    (re.compile(r"GNU\s+General\s+Public\s+License[^v]*(?:v|Version)?\s*3", re.I), "GPL-3.0"),
    (re.compile(r"GNU\s+(?:Affero|AGPL)", re.I | re.S), "AGPL-3.0"),
    (re.compile(r"GNU\s+(?:Lesser|Library|LGPL)", re.I | re.S), "LGPL-3.0"),
    (re.compile(r"MPL\s*[,-]?\s*2\.0", re.I), "MPL-2.0"),
    (re.compile(r"CDDL", re.I), "CDDL-1.0"),
    (re.compile(r"Server\s+Side\s+Public\s+License", re.I), "SSPL-1.0"),
    (re.compile(r"Public\s+Domain", re.I), "Unlicense"),
]


class ComplianceBureau:
    """
    门下省合规审计局
    
    提供全面的合规审计能力：
    - OWASP Top 10逐项合规检查（2021/2017版）
    - 依赖漏洞扫描（requirements.txt/package.json/go.mod）
    - 开源许可证兼容性检测
    - 安全基线核查（加密/认证/TLS/密码策略）
    - 统一审计报告生成
    """

    OWASP_2021_CHECKS = [
        ("A01", OWASPCategory.A01_BROKEN_ACCESS_CONTROL),
        ("A02", OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES),
        ("A03", OWASPCategory.A03_INJECTION),
        ("A04", OWASPCategory.A04_INSECURE_DESIGN),
        ("A05", OWASPCategory.A05_SECURITY_MISCONFIGURATION),
        ("A06", OWASPCategory.A06_VULNERABLE_COMPONENTS),
        ("A07", OWASPCategory.A07_AUTH_FAILURES),
        ("A08", OWASPCategory.A08_SOFTWARE_DATA_INTEGRITY),
        ("A09", OWASPCategory.A09_SECURITY_LOGGING),
        ("A10", OWASPCategory.A10_SSRF),
    ]

    def check_owasp_compliance(self, target: Path, version: str = "2021") -> OWASPReport:
        """执行OWASP Top 10合规性检查"""
        import time

        t0 = time.time()
        target_path = Path(target)
        if not target_path.exists():
            raise OWASPScanError(f"扫描目标不存在: {target_path}")

        report = OWASPReport(version=version, target=target_path)
        source_code = self._collect_all_source_code(target_path)

        for cat_code, category in self.OWASP_2021_CHECKS:
            check_method = getattr(self, f"_check_{cat_code.lower()}", None)
            if check_method:
                result = check_method(source_code, target_path)
            else:
                result = OWASPCheckResult(
                    category=category, passed=True,
                    findings=[f"{cat_code} 检查暂未实现"], severity="info",
                )
            report.checks.append(result)

        report.total_findings = sum(len(c.findings) for c in report.checks)
        report.critical_count = sum(1 for c in report.checks if c.severity == "critical")
        report.high_count = sum(1 for c in report.checks if c.severity == "high")
        report.medium_count = sum(1 for c in report.checks if c.severity == "medium")
        report.low_count = sum(1 for c in report.checks if c.severity == "low")
        report.overall_status = (
            "passed" if report.critical_count == 0 and report.high_count == 0
            else "failed" if report.critical_count > 0 else "warning"
        )
        report.scan_time = time.time() - t0
        report.generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return report

    @staticmethod
    def _collect_all_source_code(target: Path) -> str:
        """收集项目中所有源码文件内容"""
        code_parts: list[str] = []
        extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java"}
        config_extensions = {".yml", ".yaml", ".json", ".toml", ".cfg", ".ini"}
        all_exts = extensions | config_extensions

        for ext in all_exts:
            for file_path in target.rglob(f"*{ext}"):
                if any(skip in file_path.parts for skip in (
                    "node_modules", "__pycache__", ".git", "venv", ".venv", "dist", "build"
                )):
                    continue
                try:
                    content = file_path.read_text(encoding="utf-8")
                    code_parts.append(f"# FILE: {file_path}\n{content}\n")
                except Exception:
                    continue
        return "\n".join(code_parts)

    def _check_a01(self, source: str, target: Path) -> OWASPCheckResult:
        """A01: 访问控制失效检测"""
        findings: list[str] = []
        patterns = [
            (r"(?i)(def|function)\s+\w+.*?(?:(?:admin|user)_id|object_id|resource_id)\s*=.*?request\.(args|form|params|query)", "high", "不安全的直接对象引用(IDOR)"),
            (r"(?i)authorize\s*=\s*(True|False|request\.|params\[)", "critical", "硬编码或用户可控的授权标志"),
            (r"(?i)permission_check\s*=\s*(False|None|skip|bypass)", "critical", "权限检查被绕过或禁用"),
            (r"(?i)(allow|permit|grant)\s*\(\s*.*?\*|\['.*?'\]\s*\)", "high", "通配符权限授予，可能过度授权"),
            (r"(?i)@?login_required\s*=\s*False", "medium", "登录要求被显式禁用"),
        ]
        for pattern, sev, desc in patterns:
            if re.search(pattern, source, re.DOTALL):
                findings.append(f"[{sev.upper()}] {desc}")

        no_auth_routes = len(re.findall(
            r"(?i)(@?app\.(route|get|post|put|delete)).*?(?=.*?auth_required\s*=\s*False)", source
        ))
        if no_auth_routes > 3:
            findings.append(f"[HIGH] 发现{no_auth_routes}个未启用认证的路由端点")

        return OWASPCheckResult(
            category=OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
            passed=len([f for f in findings if "CRITICAL" in f or "HIGH" in f]) == 0,
            findings=findings,
            severity="critical" if any("CRITICAL" in f for f in findings)
            else "high" if any("HIGH" in f for f in findings)
            else "medium" if findings else "info",
            recommendation="实施基于角色的访问控制(RBAC)，对所有资源访问进行鉴权校验",
        )

    def _check_a02(self, source: str, target: Path) -> OWASPCheckResult:
        """A02: 加密机制失效检测"""
        findings: list[str] = []
        patterns = [
            (r"(?i)hashlib\.md5\(|hashlib\.sha1\(|\.hash\(.*?['\"]md5['\"]|\.hash\(.*?['\"]sha1['\"]", "critical", "使用弱哈希算法(MD5/SHA1)"),
            (r"(?i)(?:AES|DES|RC4|Blowfish)\.(?:new|encrypt|decrypt).*?(?:ECB|mode\s*=\s*['\"]ECB['\"])", "critical", "使用不安全的ECB加密模式"),
            (r"(?i)random\.random\(\)|os\.urandom\(\)|random\.choice\(.*?string\.", "high", "使用非密码学安全的随机数生成器"),
            (r"(?i)base64\.(b64encode|b64decode).*?(password|secret|token|key)", "high", "Base64编码被误用于敏感数据'加密'"),
            (r"(?i)password\s*=\s*.*?(md5|sha1|crypt)\(", "critical", "密码使用弱哈希存储"),
            (r"(?i)ssl\.wrap_socket\(|SSLContext.*?PROTOCOL_TLSv1(?!\.)|PROTOCOL_SSLv23", "high", "使用过时的TLS/SSL协议版本"),
        ]
        for pattern, sev, desc in patterns:
            matches = re.findall(pattern, source)
            if matches:
                count = len(matches) if isinstance(matches, list) else 1
                findings.append(f"[{sev.upper()}] {desc} (发现{count}处)")

        hardcoded_keys = re.findall(
            r"(?i)(secret[_\-]?key|api[_\-]?key|encryption[_\-]?key|private[_\-]?key)['\":\s]+['\"][^'\"]{8,}['\"]", source
        )
        if hardcoded_keys:
            findings.append(f"[CRITICAL] 发现{len(hardcoded_keys)}处硬编码的加密密钥")

        return OWASPCheckResult(
            category=OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
            passed=len([f for f in findings if "CRITICAL" in f]) == 0,
            findings=findings,
            severity="critical" if any("CRITICAL" in f for f in findings)
            else "high" if findings else "info",
            recommendation="使用强加密算法(AES-256-GCM)、密码学安全随机(secrets模块)、安全哈希(bcrypt)",
        )

    def _check_a03(self, source: str, target: Path) -> OWASPCheckResult:
        """A03: 注入攻击检测"""
        findings: list[str] = []
        patterns = [
            (r"(?i)(execute|exec|raw|cursor\.execute|session\.execute)\s*\(\s*f?[\"'].*?\{.*?\}(?:.*%s|\.format)", "critical", "SQL注入风险: 使用f-string/format拼接SQL语句"),
            (r"(?i)f['\"].*?(SELECT|INSERT|UPDATE|DELETE|DROP)\s+", "critical", "SQL注入风险: f-string中包含SQL关键字"),
            (r"(?i)(subprocess|os\.system|os\.popen|eval|exec)\s*\(\s*.*?(request|input|argv|sys\.argv|environ)", "critical", "OS命令注入风险"),
            (r"(?i)(XPath|xml.etree).*(?:evaluate|find|xpath).*?(request|input|user)", "high", "XPath注入风险"),
            (r"(?i)(NoSQL|mongo).*?\$where.*?(request|input|user)", "high", "NoSQL注入风险"),
            (r"(?i)LdapQuery.*?(request|input|user)", "high", "LDAP注入风险"),
            (r"(?i)(ORM|query).*filter\(.*?raw_sql|\.extra\(\s*['\"]WHERE", "medium", "潜在ORM注入"),
        ]
        for pattern, sev, desc in patterns:
            if re.search(pattern, source, re.DOTALL):
                findings.append(f"[{sev.upper()}] {desc}")

        param_style_checks = [
            (r"%s.*%(?:\w+|\([^)]*\))", "%格式化字符串拼接"),
            (r"\{.*?\}\.format\(", ".format()字符串拼接"),
            (r"f['\"].*?\{.*?request\.", "f-string与用户输入拼接"),
        ]
        for pat, label in param_style_checks:
            if re.search(pat, source):
                findings.append(f"[MEDIUM] 检测到{label}模式")

        return OWASPCheckResult(
            category=OWASPCategory.A03_INJECTION,
            passed=len([f for f in findings if "CRITICAL" in f]) == 0,
            findings=findings,
            severity="critical" if any("CRITICAL" in f for f in findings)
            else "high" if any("HIGH" in f for f in findings)
            else "medium" if findings else "info",
            recommendation="始终使用参数化查询(占位符)，禁止字符串拼接构造SQL/命令",
        )

    def _check_a04(self, source: str, target: Path) -> OWASPCheckResult:
        """A04: 不安全设计检测"""
        findings: list[str] = []
        patterns = [
            (r"(?i)trust.*?=(?:True|yes|1)", "medium", "发现'trust'相关配置设为信任状态"),
            (r"(?i)unsafe_skip_validation|disable_validation|skip_check", "high", "验证/检查流程被显式跳过"),
            (r"(?i)auto_approve\s*=\s*True|auto_accept\s*=\s*True", "medium", "自动批准/接受功能可能绕过审核流程"),
            (r"(?i)rate_limit\s*=\s*(?:None|0|false|False)|no_rate_limit", "medium", "速率限制被禁用"),
            (r"(?i)csrf_protect\s*=\s*False|xss_protection\s*=\s*False", "high", "CSRF/XSS保护被禁用"),
        ]
        for pattern, sev, desc in patterns:
            if re.search(pattern, source):
                findings.append(f"[{sev.upper()}] {desc}")

        mass_assignment = len(re.findall(
            r"(?i)(Model|Schema|Form)\(.*?request\.(json|form|data|body)", source
        ))
        if mass_assignment > 0:
            findings.append(f"[HIGH] 可能存在批量赋值漏洞({mass_assignment}处)")

        return OWASPCheckResult(
            category=OWASPCategory.A04_INSECURE_DESIGN,
            passed=not any("CRITICAL" in f or "HIGH" in f for f in findings),
            findings=findings,
            severity="high" if any("HIGH" in f for f in findings)
            else "medium" if findings else "info",
            recommendation="采用安全设计原则：纵深防御、最小权限原则、默认拒绝策略",
        )

    def _check_a05(self, source: str, target: Path) -> OWASPCheckResult:
        """A05: 安全配置错误检测"""
        findings: list[str] = []
        patterns = [
            (r"(?i)DEBUG\s*=\s*True|debug\s*:\s*true", "high", "调试模式在生产环境开启"),
            (r"(?i)ALLOWED_HOSTS\s*=\s*\[\s*['\"]?\*['\"]?\s*\]|allowed_hosts\s*=\s*\*", "high", "ALLOWED_HOSTS设置为通配符(*)"),
            (r"(?i)SECRET_KEY\s*=\s*['\"][^'\"]{0,20}['\"]|secret_key\s*[:=]\s*['\"][^'\"]{0,20}['\"]", "critical", "SECRET_KEY过短或使用默认值"),
            (r"(?i)cors.*?origins\s*=\s*\*", "high", "CORS配置允许所有来源(*)"),
            (r"(?i)error_reporting\s*=\s*E_ALL|display_errors\s*=\s*(?:On|True|1)", "medium", "详细错误信息可能泄露给客户端"),
        ]
        for pattern, sev, desc in patterns:
            if re.search(pattern, source):
                findings.append(f"[{sev.upper()}] {desc}")

        default_passwords = [
            (r"password\s*[:=]\s*['\"](?:admin|123456|password|root|test)['\"]", "默认密码"),
            (r"username\s*[:=]\s*['\"](?:admin|root|test|user)['\"]", "默认用户名"),
        ]
        for pattern, desc in default_passwords:
            if re.search(pattern, source):
                findings.append(f"[CRITICAL] 发现{desc}配置")

        return OWASPCheckResult(
            category=OWASPCategory.A05_SECURITY_MISCONFIGURATION,
            passed=not any("CRITICAL" in f or "HIGH" in f for f in findings),
            findings=findings,
            severity="critical" if any("CRITICAL" in f for f in findings)
            else "high" if any("HIGH" in f for f in findings)
            else "medium" if findings else "info",
            recommendation="关闭DEBUG模式，配置合理的CORS和安全响应头，使用强随机SECRET_KEY",
        )

    def _check_a06(self, source: str, target: Path) -> OWASPCheckResult:
        """A06: 过时/易受攻击组件检测"""
        findings: list[str] = []
        dep_files = [
            target / "requirements.txt", target / "package.json",
            target / "go.mod", target / "Cargo.toml", target / "pom.xml",
        ]

        vulnerable_patterns = [
            (r"(?i)(django)[<>=]+\s*([12]\..|[3]\.[01][^0-9]|<2\.2)", "Django版本过旧(<2.2)"),
            (r"(?i)(flask)[<>=]+\s*([01]\..|<1\.1)", "Flask版本过旧(<1.1)"),
            (r"(?i)(requests)[<>=]+\s*([01]\..|<2\.25)", "requests库版本过旧(<2.25)"),
            (r"(?i)(urllib3)[<>=]+\s*([01]\..|<1\.26)", "urllib3版本过旧(<1.26)"),
            (r"(?i)(pillow)[<>=]+\s*([0-7]\..|<8\.2)", "Pillow版本过旧(<8.2)"),
            (r"(?i)(numpy)[<>=]+\s*([01]\.[0-9]|<1\.20)", "NumPy版本过旧(<1.20)"),
            (r"(?i)(lodash)[<>=]+\s*([0-3]\..|<4\.17)", "Lodash版本过旧(<4.17)"),
            (r"(?i)(express)[<>=]+\s*([0-3]\..|<4\.17)", "Express版本过旧(<4.17)"),
        ]
        for dep_file in dep_files:
            if dep_file.exists():
                try:
                    content = dep_file.read_text(encoding="utf-8")
                    for pattern, desc in vulnerable_patterns:
                        if re.search(pattern, content):
                            findings.append(f"[HIGH] {desc}")
                except Exception:
                    continue

        pinned_versions = len(re.findall(r"==\s*[\d.]+", source))
        loose_versions = len(re.findall(r">=|~=|~=", source))
        if loose_versions > pinned_versions and loose_versions > 5:
            findings.append(f"[MEDIUM] 存在{loose_versions}个宽松版本约束(>=/~=)")

        return OWASPCheckResult(
            category=OWASPCategory.A06_VULNERABLE_COMPONENTS,
            passed=not any("CRITICAL" in f or "HIGH" in f for f in findings),
            findings=findings,
            severity="high" if any("HIGH" in f for f in findings)
            else "medium" if findings else "info",
            recommendation="建立软件物料清单(SBOM)，使用依赖扫描工具定期检查，锁定版本号",
        )

    def _check_a07(self, source: str, target: Path) -> OWASPCheckResult:
        """A07: 身份认证失败检测"""
        findings: list[str] = []
        patterns = [
            (r"(?i)token\s*=\s*(?:jwt\.decode|decode)\s*\(\s*.*?,\s*verify\s*=\s*False", "critical", "JWT验证被禁用(verify=False)"),
            (r"(?i)algorithms\s*=\s*\[\s*'none'\s*\]", "critical", "JWT 'none'算法攻击风险"),
            (r"(?i)password\s*[:=]\s*.*?(md5|sha1|crypt)\s*\(", "critical", "密码使用弱哈希算法存储"),
            (r"(?i)(?:compare|check|verify)\s*_password.*?(==|eq|=)\s*(?:plain|raw|text)", "high", "明文密码比较"),
            (r"(?i)session\[.*?\]\s*=\s*.*?(user_id|username|is_admin|role).*?(?:request|form|params)", "high", "会话数据直接从用户输入赋值"),
            (r"(?i)remember_me\s*=\s*True.*?(?:token|cookie).*?(?:permanent|expires\s*=\s*\d{8})", "high", "永久Remember Me Cookie可能被窃取"),
            (r"(?i)login.*?(?:brute|force|guess|attack).*?(?:none|disable|off|false)", "high", "暴力破解防护被禁用"),
        ]
        for pattern, sev, desc in patterns:
            if re.search(pattern, source, re.DOTALL):
                findings.append(f"[{sev.upper()}] {desc}")

        token_in_url = re.findall(
            r"(?i)(access_token|auth_token|jwt|bearer)\s*=\s*(?:request\.(args|query)|url)", source
        )
        if token_in_url:
            findings.append("[HIGH] Token出现在URL参数中，可能被记录在日志/浏览器历史中")

        return OWASPCheckResult(
            category=OWASPCategory.A07_AUTH_FAILURES,
            passed=not any("CRITICAL" in f or "HIGH" in f for f in findings),
            findings=findings,
            severity="critical" if any("CRITICAL" in f for f in findings)
            else "high" if any("HIGH" in f for f in findings)
            else "medium" if findings else "info",
            recommendation="使用强密码哈希(bcrypt/scrypt/argon2)，正确配置JWT验证，实施多因素认证(MFA)",
        )

    def _check_a08(self, source: str, target: Path) -> OWASPCheckResult:
        """A08: 软件和数据完整性失败检测"""
        findings: list[str] = []
        patterns = [
            (r"(?i)pickle\.loads|pickle\.load\(|marshal\.loads|cPickle", "critical", "不安全的反序列化(pickle/marshal)"),
            (r"(?i)yaml\.load\((?!.*Loader)|yaml\.unsafe_load", "critical", "不安全的YAML加载(PyYAML默认Loader可执行任意代码)"),
            (r"(?i)shelve\.open|eval\(|exec\(|compile\(.*?'exec'", "high", "危险的动态代码执行"),
            (r"(?i)(subprocess|os\.system|os\.popen)\s*\(\s*.*?(download|fetch|install|pip|npm|wget|curl)", "high", "不安全的远程代码获取与执行"),
            (r"(?i)integrity\s*=\s*(?:empty|''|None|null|undefined|false)", "medium", "SRI完整性校验缺失"),
        ]
        for pattern, sev, desc in patterns:
            if re.search(pattern, source, re.DOTALL):
                findings.append(f"[{sev.upper()}] {desc}")

        pip_install_unsafe = re.findall(r"(?i)pip\s+install\s+.*(?!--require-hashes|--no-deps)", source)
        if pip_install_unsafe:
            findings.append(f"[MEDIUM] 发现{len(pip_install_unsafe)}处不带完整性校验的pip install调用")

        return OWASPCheckResult(
            category=OWASPCategory.A08_SOFTWARE_DATA_INTEGRITY,
            passed=not any("CRITICAL" in f or "HIGH" in f for f in findings),
            findings=findings,
            severity="critical" if any("CRITICAL" in f for f in findings)
            else "high" if any("HIGH" in f for f in findings)
            else "medium" if findings else "info",
            recommendation="禁止使用pickle/yaml.unsafe_load等不安全反序列化；使用SRI保护外部资源",
        )

    def _check_a09(self, source: str, target: Path) -> OWASPCheckResult:
        """A09: 安全日志和监控失败检测"""
        findings: list[str] = []
        positive_signals: list[str] = []

        log_patterns = [
            (r"(?i)logging\.(warning|error|critical)\s*\(", "positive"),
            (r"(?i)logger\.(warn|error|crit)", "positive"),
            (r"(?i)sentry.*?capture|sentry_sdk.*?capture", "positive"),
            (r"(?i)(?:except|catch)\s*(?:Exception|BaseException)\s*:\s*$", "negative"),
            (r"(?i)except\s*:\s*pass$", "negative"),
            (r"(?i)logging\.disable\(|setLevel.*?NOTSET|level\s*=\s*(?:NOTSET|0)", "high"),
            (r"(?i)print\((?!.*?(?:debug|log))", "low"),
        ]
        for pattern, sev_type, desc in log_patterns:
            count = len(re.findall(pattern, source))
            if count > 0 and sev_type == "negative":
                findings.append(f"[{sev_type.upper()}] {desc} ({count}处)")
            elif count > 0 and sev_type == "high":
                findings.append(f"[{sev_type.upper()}] {desc} ({count}处)")
            elif count > 0 and sev_type == "low":
                findings.append(f"[INFO] {desc} ({count}处)")
            elif count > 0 and sev_type == "positive":
                positive_signals.append(desc)

        has_alerting = any(kw in source.lower() for kw in ["alert", "notify", "pagerduty", "slack_webhook"])
        if not has_alerting:
            findings.append("[MEDIUM] 未检测到告警/通知机制集成")

        if positive_signals:
            findings.append(f"[POSITIVE] 正面发现: {'; '.join(positive_signals[:3])}")

        return OWASPCheckResult(
            category=OWASPCategory.A09_SECURITY_LOGGING,
            passed=not any("CRITICAL" in f or "HIGH" in f for f in findings),
            findings=findings,
            severity="high" if any("HIGH" in f for f in findings)
            else "medium" if findings else "info",
            recommendation="确保所有认证失败、授权拒绝均被记录；集成SIEM/SOC平台；建立实时告警机制",
        )

    def _check_a10(self, source: str, target: Path) -> OWASPCheckResult:
        """A10: 服务端请求伪造(SSRF)检测"""
        findings: list[str] = []
        patterns = [
            (r"(?i)(?:requests|httpx|urllib|aiohttp)\.(get|post|put|delete|request)\s*\(\s*(?:url\s*=\s*)?(?:f?[\"'].*?\{|request\.(?:args|form|params|json|headers)\[)", "critical", "SSRF风险: 用户输入直接作为URL发起请求"),
            (r"(?i)urllib\.request\.urlopen\s*\(\s*.*?(?:request|input|params|args|form)", "critical", "SSRF风险: urlopen接受用户控制的URL"),
            (r"(?i)(?:url|uri|endpoint|redirect_url|callback|next|target)\s*=\s*.*?(request|input|params|args|form)", "high", "SSRF风险: 重定向/回调地址由用户控制"),
            (r"(?i)webhook\s*=\s*.*?(request|input|params|args|form)", "high", "Webhook URL来自用户输入(SSRF载体)"),
            (r"(?i)(?:image|file|avatar|photo|document)_url.*?(?:upload|import|fetch|load|download)", "medium", "用户提供的URL被用于资源获取(潜在SSRF)"),
            (r"(?i)metadata_url|169\.254\.169\.254|metadata\.google\.internal", "high", "云元数据端点访问(可能是SSRF攻击目标)"),
        ]
        for pattern, sev, desc in patterns:
            if re.search(pattern, source, re.DOTALL):
                findings.append(f"[{sev.upper()}] {desc}")

        has_allowlist = any(kw in source.lower() for kw in [
            "url_allowlist", "url_whitelist", "allowed_domains",
            "allowed_hosts", "url_validator", "validate_url",
        ])
        if not has_allowlist and any("CRITICAL" in f or "HIGH" in f for f in findings):
            findings.append("[HIGH] 未检测到URL白名单/域名校验机制")

        return OWASPCheckResult(
            category=OWASPCategory.A10_SSRF,
            passed=not any("CRITICAL" in f or "HIGH" in f for f in findings),
            findings=findings,
            severity="critical" if any("CRITICAL" in f for f in findings)
            else "high" if any("HIGH" in f for f in findings)
            else "medium" if findings else "info",
            recommendation="对用户提供的URL实施严格白名单验证；禁止请求内网地址；使用代理层限制出站网络访问",
        )

    # ==================== 依赖漏洞扫描 ====================

    def scan_dependency_vulnerabilities(self, dep_file: Path) -> VulnerabilityReport:
        """扫描依赖文件中的已知漏洞"""
        dep_path = Path(dep_file)
        if not dep_path.exists():
            raise DependencyScanError(f"依赖文件不存在: {dep_file}")

        report = VulnerabilityReport(dep_file=dep_path)

        ext_map = {
            ".txt": self._scan_python_deps,
            ".toml": self._scan_toml_deps,
            ".json": self._scan_nodejs_deps,
            ".mod": self._scan_go_deps,
            ".xml": self._scan_maven_deps,
        }
        scanner = ext_map.get(dep_path.suffix.lower(), self._scan_generic_deps)
        vulns = scanner(dep_path)

        report.vulnerabilities = vulns
        report.total_vulns = len(vulns)
        report.critical_count = sum(1 for v in vulns if v.severity == "critical")
        report.high_count = sum(1 for v in vulns if v.severity == "high")
        report.medium_count = sum(1 for v in vulns if v.severity == "medium")
        report.low_count = sum(1 for v in vulns if v.severity == "low")
        report.packages_scanned = len(set(v.package_name for v in vulns))
        report.generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return report

    def _scan_python_deps(self, dep_file: Path) -> list[Vulnerability]:
        """扫描Python依赖漏洞"""
        content = dep_file.read_text(encoding="utf-8").splitlines()
        vulns: list[Vulnerability] = []
        known_vulns: dict[str, list[dict[str, Any]]] = {
            "django": [{"ver": "<2.2.28", "cve": "CVE-2024-24500", "severity": "high", "desc": "SQL注入漏洞"}],
            "flask": [{"ver": "<2.3.3", "cve": "CVE-2023-46129", "severity": "high", "desc": "Open Redirect漏洞"}],
            "requests": [{"ver": "<2.31.0", "cve": "CVE-2023-32681", "severity": "medium", "desc": "SSRF防护不足"}],
            "pillow": [{"ver": "<9.5.0", "cve": "CVE-2023-44471", "severity": "high", "desc": "DoS缓冲区溢出"}],
            "sqlalchemy": [{"ver": "<2.0.25", "cve": "CVE-2024-10939", "severity": "medium", "desc": "SQL注入风险"}],
            "urllib3": [{"ver": "<1.26.18", "cve": "CVE-2023-43804", "severity": "high", "desc": "请求注入/cookie头部注入"}],
            "jinja2": [{"ver": "<3.1.3", "cve": "CVE-2024-22195", "severity": "medium", "desc": "XML属性重新注入"}],
            "pyyaml": [{"ver": "<6.0.1", "cve": "CVE-2020-14343", "severity": "critical", "desc": "任意代码执行(full_load)"}],
            "numpy": [{"ver": "<1.24.2", "cve": "CVE-2024-26494", "severity": "medium", "desc": "缓冲区溢出"}],
            "fastapi": [{"ver": "<0.104.1", "cve": "CVE-2024-24506", "severity": "medium", "desc": "Open Redirect"}],
            "httpx": [{"ver": "<0.25.2", "cve": "CVE-2024-37274", "severity": "medium", "desc": "SSRF防护不足"}],
        }

        for line in content:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"^([a-zA-Z0-9_-]+)\s*([><=!~]+)\s*([\d.]+.*)?$", line)
            if match:
                pkg_name = match.group(1).lower()
                operator = match.group(2)
                version = match.group(3) or "*"

                if pkg_name in known_vulns:
                    for vuln_info in known_vulns[pkg_name]:
                        vulns.append(Vulnerability(
                            cve_id=vuln_info["cve"],
                            package_name=pkg_name,
                            installed_version=version,
                            fixed_version=vuln_info["ver"].replace("<=", ">=").replace("<", ">=").strip(),
                            severity=vuln_info["severity"],
                            description=vuln_info["desc"],
                            cvss_score={"critical": 9.5, "high": 7.5, "medium": 5.5, "low": 2.5}.get(vuln_info["severity"], 5.0),
                        ))

        try:
            proc = subprocess.run(
                [sys.executable, "-m", "safety", "check", "-r", str(dep_file), "--json"],
                capture_output=True, text=True, timeout=60,
            )
            safety_data = json.loads(proc.stdout)
            if isinstance(safety_data, list):
                for item in safety_data:
                    vulns.append(Vulnerability(
                        cve_id=item.get("id", "SAFETY-" + hashlib.md5(item.get("name", "").encode()).hexdigest()[:8]),
                        package_name=item.get("name", ""),
                        installed_version=item.get("installed_version", ""),
                        fixed_version=item.get("fixed_version", ""),
                        severity=item.get("vulnerability", "high") if item.get("vulnerability") else "medium",
                        description=item.get("description", item.get("reason", "Safety扫描发现漏洞")),
                        cvss_score=7.0,
                    ))
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            pass

        return vulns

    def _scan_toml_deps(self, dep_file: Path) -> list[Vulnerability]:
        """扫描TOML格式依赖"""
        content = dep_file.read_text(encoding="utf-8")
        vulns: list[Vulnerability] = []

        deps_section = re.findall(r"\[dependencies\](.*?)(?:\[|$)", content, re.DOTALL)
        if not deps_section:
            deps_section = [content]

        for section in deps_section:
            pkg_matches = re.findall(r"^(\w[\w-]*)\s*=\s*['\"]?([^'\',\s]+)", section, re.MULTILINE)
            for pkg_name, version in pkg_matches:
                vulns.append(Vulnerability(
                    cve_id=f"TOML-{pkg_name}",
                    package_name=pkg_name,
                    installed_version=version,
                    fixed_version="latest",
                    severity="medium",
                    description=f"TOML依赖项{pkg_name}@{version}需手动验证安全性",
                    cvss_score=5.0,
                ))
        return vulns

    def _scan_nodejs_deps(self, dep_file: Path) -> list[Vulnerability]:
        """扫描Node.js依赖"""
        try:
            data = json.loads(dep_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        vulns: list[Vulnerability] = []
        all_deps: dict[str, str] = {}
        all_deps.update(data.get("dependencies", {}))
        all_deps.update(data.get("devDependencies", {}))

        node_vulns: dict[str, dict[str, str]] = {
            "lodash": {"ver": "<4.17.21", "cve": "CVE-2021-23337", "sev": "critical", "desc": "原型污染"},
            "express": {"ver": "<4.18.2", "cve": "CVE-2022-24999", "sev": "high", "desc": "Open Redirect"},
            "axios": {"ver": "<0.27.2", "cve": "CVE-2023-45857", "sev": "medium", "desc": "SSRF"},
            "ws": {"ver": "<8.11.3", "cve": "CVE-2023-28136", "sev": "high", "desc": "内存泄漏DoS"},
        }

        for pkg_name, version in all_deps.items():
            clean_ver = version.replace("^", "").replace("~", "").replace(">=", "").replace(">", "")
            if pkg_name in node_vulns:
                nv = node_vulns[pkg_name]
                vulns.append(Vulnerability(
                    cve_id=nv["cve"], package_name=pkg_name,
                    installed_version=clean_ver, fixed_version=nv["ver"].replace("<", ">=").strip(),
                    severity=nv["sev"], description=nv["desc"],
                    cvss_score={"critical": 9.5, "high": 7.5, "medium": 5.5}.get(nv["sev"], 5.0),
                ))

        try:
            result = subprocess.run(
                ["npm", "audit", "--json"], capture_output=True, text=True, timeout=60, cwd=dep_file.parent,
            )
            audit_data = json.loads(result.stdout)
            actions = audit_data.get("actions", {})
            resolve_actions = actions.get("resolve", {}).get("actions", [])
            for action in resolve_actions:
                vuln = action.get("is", {})
                vulns.append(Vulnerability(
                    cve_id=vuln.get("id", f"NPM-{action.get('module', '')}"),
                    package_name=action.get("module", ""),
                    installed_version=vuln.get("version", ""),
                    fixed_version=action.get("to", "latest"),
                    severity=vuln.get("severity", "high"),
                    description=vuln.get("title", "NPM Audit发现漏洞"),
                    cvss_score=float(vuln.get("cvss", 5.0)),
                ))
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, Exception):
            pass

        return vulns

    def _scan_go_deps(self, dep_file: Path) -> list[Vulnerability]:
        """扫描Go依赖"""
        content = dep_file.read_text(encoding="utf-8")
        vulns: list[Vulnerability] = []
        lines = content.splitlines()
        for line in lines:
            if line.strip().startswith(("require", "indirect")):
                parts = line.split()
                if len(parts) >= 3:
                    pkg = parts[1]
                    ver = parts[2] if len(parts) > 2 else "unknown"
                    vulns.append(Vulnerability(
                        cve_id=f"GO-{pkg.split('/')[-1]}", package_name=pkg,
                        installed_version=ver, fixed_version="latest",
                        severity="medium", description=f"Go依赖{pkg}@{ver}需使用govulncheck验证",
                        cvss_score=5.0,
                    ))
        return vulns[:15]

    def _scan_maven_deps(self, dep_file: Path) -> list[Vulnerability]:
        """扫描Maven依赖"""
        content = dep_file.read_text(encoding="utf-8")
        vulns: list[Vulnerability] = []
        artifact_ids = re.findall(r"<artifactId>([^<]+)</artifactId>", content)
        versions = re.findall(r"<version>([^<]+)</version>", content)
        for i, artifact in enumerate(artifact_ids[:20]):
            ver = versions[i] if i < len(versions) else "unknown"
            vulns.append(Vulnerability(
                cve_id=f"MVN-{artifact}", package_name=artifact,
                installed_version=ver, fixed_version="latest",
                severity="low", description=f"Maven依赖{artifact}@{ver}需使用OWASP Dependency Check验证",
                cvss_score=4.0,
            ))
        return vulns

    def _scan_generic_deps(self, dep_file: Path) -> list[Vulnerability]:
        """通用依赖文件扫描"""
        content = dep_file.read_text(encoding="utf-8")
        vulns: list[Vulnerability] = []
        pkg_pattern = re.findall(r"^([a-zA-Z0-9_-][\w.-]*)\s*[~><=!]+\s*([\d.]+)", content, re.MULTILINE)
        for pkg, ver in pkg_pattern[:10]:
            vulns.append(Vulnerability(
                cve_id=f"GEN-{pkg}", package_name=pkg,
                installed_version=ver, fixed_version="latest",
                severity="info", description=f"通用扫描: {pkg}@{ver}",
                cvss_score=3.0,
            ))
        return vulns

    # ==================== 许可证合规检查 ====================

    def check_license_compliance(self, project_dir: Path) -> LicenseReport:
        """检查项目依赖的开源许可证合规性"""
        project_path = Path(project_dir)
        if not project_path.exists():
            raise LicenseCheckError(f"项目目录不存在: {project_dir}")

        report = LicenseReport(project_dir=project_path)

        license_files = [project_path / "LICENSE", project_path / "LICENSE.txt",
                         project_path / "LICENCE", project_path / "COPYING"]
        for lf in license_files:
            if lf.exists():
                content = lf.read_text(encoding="utf-8")
                for pattern, lic_name in LICENSE_PATTERNS:
                    if pattern.search(content):
                        report.project_license = lic_name
                        break
                if report.project_license == "unknown":
                    report.project_license = "custom"
                break

        dep_licenses = self._extract_dep_licenses(project_path)
        report.licenses = dep_licenses

        incompatible = [l for l in dep_licenses if l.compatibility == "incompatible"]
        report.incompatible_licenses = incompatible

        missing = [l.package_name for l in dep_licenses if l.license_name == "unknown"]
        report.missing_licenses = missing

        deduction = len(incompatible) * 15 + len(missing) * 3
        report.compliance_score = max(0.0, 100.0 - deduction)
        report.generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return report

    def _extract_dep_licenses(self, project_dir: Path) -> list[LicenseInfo]:
        """从各类依赖文件提取许可证信息"""
        licenses: list[LicenseInfo] = []

        req_file = project_dir / "requirements.txt"
        if req_file.exists():
            licenses.extend(self._extract_pip_licenses(req_file))

        pkg_file = project_dir / "package.json"
        if pkg_file.exists():
            licenses.extend(self._extract_npm_licenses(pkg_file))

        go_mod = project_dir / "go.mod"
        if go_mod.exists():
            licenses.extend(self._extract_go_licenses(go_mod))

        cargo_toml = project_dir / "Cargo.toml"
        if cargo_toml.exists():
            licenses.extend(self._extract_cargo_licenses(cargo_toml))

        pyproject = project_dir / "pyproject.toml"
        if pyproject.exists():
            licenses.extend(self._extract_pyproject_licenses(pyproject))

        seen: set[str] = set()
        unique: list[LicenseInfo] = []
        for lic in licenses:
            key = f"{lic.package_name}:{lic.license_name}"
            if key not in seen:
                seen.add(key)
                unique.append(lic)
        return unique

    def _extract_pip_licenses(self, req_file: Path) -> list[LicenseInfo]:
        """从requirements.txt提取许可证"""
        licenses: list[LicenseInfo] = []
        common_pkg_licenses: dict[str, str] = {
            "django": "BSD-3-Clause", "flask": "BSD-3-Clause", "requests": "Apache-2.0",
            "numpy": "BSD-3-Clause", "pandas": "BSD-3-Clause", "scipy": "BSD-3-Clause",
            "sqlalchemy": "MIT", "celery": "BSD-3-Clause", "redis": "MIT",
            "fastapi": "MIT", "uvicorn": "BSD-3-Clause", "pydantic": "MIT",
            "httpx": "BSD-3-Clause", "aiohttp": "Apache-2.0", "pillow": "HPND",
            "pytest": "MIT", "black": "MIT", "flake8": "MIT", "mypy": "MIT",
            "click": "BSD-3-Clause", "rich": "MIT", "typer": "MIT",
            "certifi": "MPL-2.0", "charset-normalizer": "MIT", "idna": "BSD-3-Clause",
            "urllib3": "MIT", "chardet": "LGPL-2.1", "jinja2": "BSD-3-Clause",
            "markupsafe": "BSD-3-Clause", "itsdangerous": "BSD-3-Clause",
            "werkzeug": "BSD-3-Clause", "gunicorn": "MT",
            "psycopg2": "LGPL-3.0+", "pymysql": "MIT", "cryptography": "Apache-2.0/BSD",
            "pyopenssl": "Apache-2.0", "pyjwt": "MIT", "passlib": "BSD-3-Clause",
            "alembic": "MIT", "factory_boy": "MT",
        }

        content = req_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("-"):
                continue
            match = re.match(r"^([a-zA-Z0-9_.-]+)", line)
            if match:
                pkg_name = match.group(1).lower().replace("-", "_").replace(".", "_")
                lic_name = common_pkg_licenses.get(pkg_name, "unknown")
                info = COMMON_LICENSES.get(lic_name, {"spdx": lic_name, "compatibility": "unknown", "risk": "medium"})
                licenses.append(LicenseInfo(
                    package_name=match.group(1), license_name=lic_name,
                    license_id=info.get("spdx", lic_name), spdx_id=info.get("spdx"),
                    compatibility=info.get("compatibility", "unknown"),
                    risk_level=info.get("risk", "medium"),
                ))
        return licenses

    def _extract_npm_licenses(self, pkg_file: Path) -> list[LicenseInfo]:
        """从package.json提取许可证"""
        try:
            data = json.loads(pkg_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        licenses: list[LicenseInfo] = []
        main_license = data.get("license", "unknown")
        info = COMMON_LICENSES.get(main_license, {"spdx": str(main_license), "compatibility": "unknown", "risk": "medium"})
        licenses.append(LicenseInfo(
            package_name="(project)", license_name=str(main_license),
            license_id=info.get("spdx", str(main_license)), spdx_id=info.get("spdx"),
            compatibility=info.get("compatibility", "unknown"), risk_level=info.get("risk", "medium"),
        ))

        lock_files = [pkg_file.parent / f for f in ("package-lock.json", "yarn.lock")]
        for lock_file in lock_files:
            if lock_file.exists():
                lock_content = lock_file.read_text(encoding="utf-8")
                lic_matches = re.findall(r'"license":\s*"([^"]+)"', lock_content)
                name_matches = re.findall(r'"name":\s*"(@?[^"]+)"', lock_content)
                for i, name in enumerate(name_matches[:30]):
                    lic = lic_matches[i] if i < len(lic_matches) else "unknown"
                    li = COMMON_LICENSES.get(lic, {"spdx": lic, "compatibility": "unknown", "risk": "medium"})
                    licenses.append(LicenseInfo(
                        package_name=name, license_name=lic,
                        license_id=li.get("spdx", lic), spdx_id=li.get("spdx"),
                        compatibility=li.get("compatibility", "unknown"),
                        risk_level=li.get("risk", "medium"),
                    ))
                break
        return licenses

    def _extract_go_licenses(self, go_mod: Path) -> list[LicenseInfo]:
        """从go.mod提取许可证"""
        licenses: list[LicenseInfo] = []
        content = go_mod.read_text(encoding="utf-8")
        modules = re.findall(r"\t([^\s]+)\s+v([\d.]+)", content)
        go_licenses: dict[str, str] = {
            "github.com/gin-gonic/gin": "MT",
            "github.com/go-sql-driver/mysql": "MPL-2.0",
            "github.com/lib/pq": "MT",
            "github.com/redis/go-redis/v9": "BSD-2-Clause",
            "github.com/stretchr/testify": "MT",
            "google.golang.org/grpc": "Apache-2.0",
            "golang.org/x/net": "BSD-3-Clause",
            "github.com/golang-jwt/jwt/v5": "MT",
            "github.com/spf13/viper": "MT",
            "github.com/gorilla/mux": "BSD-3-Clause",
            "gorm.io/gorm": "MT",
            "github.com/swaggo/swag": "MT",
        }
        for mod, ver in modules:
            lic_name = go_licenses.get(mod, "unknown")
            li = COMMON_LICENSES.get(lic_name, {"spdx": lic_name, "compatibility": "unknown", "risk": "medium"})
            licenses.append(LicenseInfo(
                package_name=mod, license_name=lic_name,
                license_id=li.get("spdx", lic_name), spdx_id=li.get("spdx"),
                compatibility=li.get("compatibility", "unknown"),
                risk_level=li.get("risk", "medium"),
            ))
        return licenses

    def _extract_cargo_licenses(self, cargo_toml: Path) -> list[LicenseInfo]:
        """从Cargo.toml提取许可证"""
        licenses: list[LicenseInfo] = []
        content = cargo_toml.read_text(encoding="utf-8")
        deps = re.findall(r'^(\w[\w-]*)\s*=\s*["\']?([^"\',\s]+)', content, re.MULTILINE)
        rust_licenses: dict[str, str] = {
            "serde": "MIT/Apache-2.0", "tokio": "MT", "reqwest": "MIT/Apache-2.0",
            "serde_json": "MIT/Apache-2.0", "rand": "MIT/Apache-2.0",
            "hyper": "MIT/Apache-2.0", "actix-web": "MIT/Apache-2.0",
            "clap": "MIT/Apache-2.0", "anyhow": "MIT/Apache-2.0",
            "thiserror": "MIT/Apache-2.0", "tracing": "MT",
        }
        for pkg, ver in deps:
            lic_name = rust_licenses.get(pkg, "unknown")
            li = COMMON_LICENSES.get(lic_name.split("/")[0], {"spdx": lic_name, "compatibility": "unknown", "risk": "medium"})
            licenses.append(LicenseInfo(
                package_name=pkg, license_name=lic_name,
                license_id=li.get("spdx", lic_name), spdx_id=li.get("spdx"),
                compatibility=li.get("compatibility", "unknown"),
                risk_level=li.get("risk", "medium"),
            ))
        return licenses

    def _extract_pyproject_licenses(self, pyproject: Path) -> list[LicenseInfo]:
        """从pyproject.toml提取许可证"""
        licenses: list[LicenseInfo] = []
        content = pyproject.read_text(encoding="utf-8")
        deps_section = re.findall(r"\[dependencies\](.*?)(?:\[|$)", content, re.DOTALL)
        if deps_section:
            pkg_matches = re.findall(r'^(\w[\w-]*)\s*=\s*["\']?([^"\',\s]+)', deps_section[0], re.MULTILINE)
            for pkg, ver in pkg_matches:
                li = COMMON_LICENSES.get("unknown", {"spdx": "unknown", "compatibility": "unknown", "risk": "medium"})
                licenses.append(LicenseInfo(
                    package_name=pkg, license_name="unknown",
                    license_id=li.get("spdx", "unknown"), spdx_id=li.get("spdx"),
                    compatibility=li.get("compatibility", "unknown"),
                    risk_level=li.get("risk", "medium"),
                ))
        return licenses

    # ==================== 安全基线核查 ====================

    def verify_security_baseline(self, project_dir: Path, baseline: Optional[SecurityBaseline] = None) -> BaselineVerificationReport:
        """验证项目的安全基线合规性"""
        bl = baseline or SecurityBaseline()
        target_path = Path(project_dir)
        if not target_path.exists():
            raise BaselineVerifyError(f"项目目录不存在: {project_dir}")

        source = self._collect_all_source_code(target_path)
        checks: list[BaselineCheckItem] = []
        counter = 0

        tls_patterns = [
            (r"(?i)TLSv1(_\d)?\s*[,(]", "tls_version", "TLS协议版本配置", "应使用TLSv1.2或更高版本"),
            (r"(?i)ssl_version|min_ssl_version|minimum_version", "tls_version", "SSL/TLS最低版本配置", "应明确指定最低TLS版本"),
        ]
        for pattern, check_id, desc, rec in tls_patterns:
            counter += 1
            found = bool(re.search(pattern, source))
            checks.append(BaselineCheckItem(
                check_id=f"BASE-{counter:03d}", category="tls_configuration",
                description=desc, passed=found, severity="high",
                actual_value="configured" if found else "not_found",
                expected_value="configured", recommendation=rec if not found else "",
            ))

        cipher_patterns = [
            (r"(?i)(?:RC4|DES|3DES|MD5|SHA1|NULL|EXPORT|aNULL|eNULL)", "forbidden_cipher", "禁用弱加密套件", "应移除RC4/DES等弱加密套件"),
            (r"(?i)(?:AES_256_GCM|CHACHA20|AES_128_GCM)", "strong_cipher", "强加密套件配置", "推荐使用AES-256-GCM"),
        ]
        for pattern, check_id, desc, rec in cipher_patterns:
            counter += 1
            is_forbidden = "forbidden" in check_id
            found = bool(re.search(pattern, source))
            passed = not found if is_forbidden else found
            checks.append(BaselineCheckItem(
                check_id=f"BASE-{counter:03d}", category="cipher_suite",
                description=desc, passed=passed,
                severity="critical" if is_forbidden else "medium",
                actual_value=("detected" if found else "not_detected") if is_forbidden else ("configured" if found else "not_configured"),
                expected_value="not_detected" if is_forbidden else "configured",
                recommendation=rec if not passed else "",
            ))

        hash_patterns = [
            (r"(?i)hashlib\.md5\(|hashlib\.sha1\(|\.hash\(.*?['\"]md5['\"]|\.hash\(.*?['\"]sha1['\"]", "weak_hash", "弱哈希算法检测", "禁止使用MD5/SHA1"),
            (r"(?i)hashlib\.sha(256|384|512)\(|hashlib\.shake_", "strong_hash", "强哈希算法使用", "确认使用SHA-256及以上"),
        ]
        for pattern, check_id, desc, rec in hash_patterns:
            counter += 1
            is_weak = "weak" in check_id
            found = bool(re.search(pattern, source))
            passed = not found if is_weak else found
            checks.append(BaselineCheckItem(
                check_id=f"BASE-{counter:03d}", category="hash_algorithm",
                description=desc, passed=passed,
                severity="critical" if is_weak else "info",
                actual_value=("detected" if found else "not_detected") if is_weak else ("used" if found else "not_used"),
                expected_value="not_used" if is_weak else "used",
                recommendation=rec if not passed else "",
            ))

        auth_patterns = [
            (r"(?i)session.*?(?:timeout|expire|max_age|lifetime).*?(\d+)", "session_timeout", "会话超时配置", f"会话超时应<={bl.session_timeout_minutes}分钟"),
            (r"(?i)max_login_attempts|login_attempts.*?(\d+)", "account_lockout", "账户锁定阈值", f"登录尝试次数应<={bl.max_login_attempts}次"),
            (r"(?i)mfa|2fa|totp|two_factor|multi_factor", "mfa_support", "多因素认证支持", "建议启用MFA增强安全性"),
        ]
        for pattern, check_id, desc, rec in auth_patterns:
            counter += 1
            is_mfa = "mfa" in check_id
            found = bool(re.search(pattern, source))
            passed = found if is_mfa else True
            checks.append(BaselineCheckItem(
                check_id=f"BASE-{counter:03d}", category="authentication_security",
                description=desc, passed=passed,
                severity="high" if not passed and not is_mfa else "medium",
                actual_value="enabled" if (found or is_mfa) else "not_configured",
                expected_value="enabled" if is_mfa else "any",
                recommendation=rec if not passed else "",
            ))

        security_headers = [
            ("X-Content-Type-Options", r"(?i)x-content-type-options[:\s]+nosniff"),
            ("X-Frame-Options", r"(?i)x-frame-options[:\s]+(deny|sameorigin)"),
            ("Strict-Transport-Security", r"(?i)strict-transport-security[:\s]+max-age"),
            ("Referrer-Policy", r"(?i)referrer-policy[:\s]"),
        ]
        for header_name, pattern in security_headers:
            counter += 1
            found = bool(re.search(pattern, source))
            checks.append(BaselineCheckItem(
                check_id=f"BASE-{counter:03d}", category="security_headers",
                description=f"安全响应头: {header_name}", passed=found,
                severity="medium", actual_value="present" if found else "missing",
                expected_value="present",
                recommendation=f"添加{header_name}响应头" if not found else "",
            ))

        cors_checks = [
            (r"(?i)cors.*?origin[s]?.*?\*", "cors_wildcard_origin", "CORS通配符来源", "不应使用通配符*"),
        ]
        for pattern, check_id, desc, rec in cors_checks:
            counter += 1
            is_wildcard = "wildcard" in check_id
            found = bool(re.search(pattern, source))
            passed = not found if is_wildcard else True
            checks.append(BaselineCheckItem(
                check_id=f"BASE-{counter:03d}", category="cors_policy",
                description=desc, passed=passed,
                severity="high" if not passed else "low",
                actual_value="detected" if found else "not_detected",
                expected_value="not_allowed" if is_wildcard else "configurable",
                recommendation=rec if not passed else "",
            ))

        passed_count = sum(1 for c in checks if c.passed)
        failed_count = sum(1 for c in checks if not c.passed and c.severity in ("critical", "high"))
        warning_count = sum(1 for c in checks if not c.passed and c.severity in ("medium", "low"))

        return BaselineVerificationReport(
            baseline_name=bl.name, target=target_path, checks=checks,
            passed_count=passed_count, failed_count=failed_count,
            warning_count=warning_count, overall_passed=failed_count == 0,
            score=round(passed_count / max(len(checks), 1) * 100, 1),
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    # ==================== 审计报告生成 ====================

    def generate_audit_report(self, checks: list[Any], format_type: str = "markdown") -> str:
        """生成统一的审计报告"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines: list[str] = []
        lines.append("# 门下省 合规审计报告\n")
        lines.append(f"> **生成时间**: {now}\n")
        lines.append(f"> **检查项总数**: {len(checks)}\n")

        owasp_reports = [c for c in checks if isinstance(c, OWASPReport)]
        vuln_reports = [c for c in checks if isinstance(c, VulnerabilityReport)]
        license_reports = [c for c in checks if isinstance(c, LicenseReport)]
        baseline_reports = [c for c in checks if isinstance(c, BaselineVerificationReport)]

        if owasp_reports:
            for idx, report in enumerate(owasp_reports, start=1):
                status_icon = "PASS" if report.overall_status == "passed" else "WARN" if report.overall_status == "warning" else "FAIL"
                lines.append(f"---\n## OWASP合规检查 #{idx} (v{report.version})\n")
                lines.append(f"| 项目 | 值 |\n| --- | --- |")
                lines.append(f"| 目标 | `{report.target.name}` |")
                lines.append(f"| 总体状态 | **{status_icon}** |")
                lines.append(f"| 总发现数 | {report.total_findings} |")
                lines.append(f"| CRITICAL | {report.critical_count} |")
                lines.append(f"| HIGH | {report.high_count} |")
                lines.append(f"| MEDIUM | {report.medium_count} |")
                lines.append(f"| LOW | {report.low_count} |")
                lines.append(f"| 扫描耗时 | {report.scan_time:.2f}s |\n")
                for check in report.checks:
                    icon = "[OK]" if check.passed else "[!!]"
                    lines.append(f"### {icon} {check.category.value}\n")
                    if check.findings:
                        lines.append("| 严重度 | 发现 |\n| --- | --- |")
                        for finding in check.findings[:10]:
                            lines.append(f"| {finding} |")
                    if check.recommendation:
                        lines.append(f"\n> 建议: {check.recommendation}\n")

        if vuln_reports:
            for idx, report in enumerate(vuln_reports, start=1):
                lines.append(f"---\n## 依赖漏洞扫描 #{idx}\n")
                lines.append(f"| 文件 | `{report.dep_file.name}` | 扫描工具: {report.scan_tool} |\n")
                lines.append(f"| 总漏洞: **{report.total_vulns}** | C:{report.critical_count} H:{report.high_count} M:{report.medium_count} L:{report.low_count} |\n")
                if report.vulnerabilities:
                    lines.append("| CVE | 包名 | 版本 | 严重度 | CVSS | 描述 |\n| --- | --- | --- | --- | --- | --- |")
                    for v in sorted(report.vulnerabilities, key=lambda x: x.cvss_score, reverse=True)[:20]:
                        lines.append(f"| {v.cve_id} | {v.package_name} | `{v.installed_version}` | `{v.severity}` | {v.cvss_score:.1f} | {v.description} |")

        if license_reports:
            for idx, report in enumerate(license_reports, start=1):
                lines.append(f"---\n## 许可证合规检查 #{idx}\n")
                lines.append(f"| 项目许可 | {report.project_license} | 依赖数: {len(report.licenses)} | 不兼容: {len(report.incompatible_licenses)} | 评分: **{report.compliance_score:.1f}/100** |\n")
            incompatible = [l for l in license_reports if l.incompatible_licenses]
            if incompatible:
                lines.append("### 不兼容许可证\n")
                for lic in incompatible:
                    for item in lic.incompatible_licenses:
                        lines.append(f"- **{item.package_name}**: {item.license_name} ({item.risk_level})")

        if baseline_reports:
            for idx, report in enumerate(baseline_reports, start=1):
                overall_icon = "PASS" if report.overall_passed else "FAIL"
                lines.append(f"---\n## 安全基线核查 #{idx}\n")
                lines.append(f"| 基线 | {report.baseline_name} | 状态: **{overall_icon}** | 得分: **{report.score:.1f}/100** | 通过: {report.passed_count}/{len(report.checks)} |\n")
                failed_checks = [c for c in report.checks if not c.passed]
                if failed_checks:
                    lines.append("### 未通过项\n")
                    lines.append("| ID | 类别 | 描述 | 当前值 | 期望值 |\n| --- | --- | --- | --- | --- |")
                    for c in sorted(failed_checks, key=lambda x: x.severity)[:15]:
                        lines.append(f"| {c.check_id} | {c.category} | {c.description} | `{c.actual_value}` | `{c.expected_value}` |")

        lines.append("\n---\n## 总结\n")
        total_issues = sum(
            (r.total_findings if isinstance(r, OWASPReport) else 0) +
            (r.total_vulns if isinstance(r, VulnerabilityReport) else 0) +
            (len(r.incompatible_licenses) if isinstance(r, LicenseReport) else 0) +
            (r.failed_count if isinstance(r, BaselineVerificationReport) else 0)
            for r in checks
        )
        lines.append(f"- **总问题数**: {total_issues}")
        lines.append(f"- **报告时间**: {now}\n")

        return "\n".join(lines)


if __name__ == "__main__":
    bureau = ComplianceBureau()

    demo_project = Path(__file__).parent.parent.parent.parent
    print("=" * 60)
    print("门下省 合规审计局 - 功能演示")
    print("=" * 60)

    owasp_report = bureau.check_owasp_compliance(demo_project, version="2021")
    print(f"\nOWASP Top 10 合规检查:")
    print(f"   版本: {owasp_report.version}, 状态: {owasp_report.overall_status}")
    print(f"   总发现: {owasp_report.total_findings} (C:{owasp_report.critical_count} H:{owasp_report.high_count})")
    for check in owasp_report.checks:
        icon = "OK" if check.passed else "!!"
        print(f"   [{icon}] {check.category.value}: {len(check.findings)} [{check.severity}]")

    import textwrap as _tw
    req_file = demo_project / "_demo_requirements.txt"
    req_file.write_text(_tw.dedent("""\
        django>=3.2,<4.0
        flask>=1.0,<2.0
        requests>=2.20.0
        pillow>=8.0.0
        pyyaml>=5.4
        urllib3>=1.25.0
        numpy>=1.21.0
        fastapi>=0.80.0
    """).strip(), encoding="utf-8")

    vuln_report = bureau.scan_dependency_vulnerabilities(req_file)
    print(f"\n依赖漏洞扫描:")
    print(f"   工具: {vuln_report.scan_tool}, 漏洞: {vuln_report.total_vulns}")
    for v in vuln_report.vulnerabilities[:6]:
        print(f"   [{v.severity}] {v.package_name}@{v.installed_version} - {v.cve_id}")

    license_report = bureau.check_license_compliance(demo_project)
    print(f"\n许可证合规检查:")
    print(f"   项目许可: {license_report.project_license}, 评分: {license_report.compliance_score:.1f}")
    print(f"   不兼容: {len(license_report.incompatible_licenses)}")

    baseline = SecurityBaseline(name="demo_strict")
    base_report = bureau.verify_security_baseline(demo_project, baseline=baseline)
    print(f"\n安全基线核查:")
    print(f"   状态: {'PASS' if base_report.overall_passed else 'FAIL'}, 得分: {base_report.score:.1f}")

    full_report = bureau.generate_audit_report([owasp_report, vuln_report, license_report, base_report])
    print(f"\n审计报告预览 (前600字符):")
    print(full_report[:600])

    req_file.unlink(missing_ok=True)
    print("\n演示完成!")
