"""
安全扫描智能增强框架

提供漏洞扫描、OWASP Top 10检查、依赖安全检查等功能
支持配置文件、HTML报告生成

增强功能:
- 代码审计扫描: 深度代码质量与安全审计
- 配置安全检查: 检测配置文件中的安全问题
- API安全检查: REST API安全漏洞检测
- 数据流分析: 污点追踪与数据流分析
- 自动修复建议: 智能生成安全修复代码
- 风险评估报告: 全面的安全风险评估
"""

import os
import sys
import json
import time
import argparse
import subprocess
import re
import hashlib
import ast
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
from abc import ABC, abstractmethod

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityCategory(Enum):
    INJECTION = "injection"
    XSS = "xss"
    CSRF = "csrf"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SENSITIVE_DATA = "sensitive_data"
    SECURITY_MISCONFIGURATION = "security_misconfiguration"
    BROKEN_ACCESS_CONTROL = "broken_access_control"
    CRYPTOGRAPHIC_FAILURE = "cryptographic_failure"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    VULNERABLE_DEPENDENCIES = "vulnerable_dependencies"
    LOGGING_MONITORING = "logging_monitoring"
    SSRF = "ssrf"
    PATH_TRAVERSAL = "path_traversal"
    HARDCODED_SECRETS = "hardcoded_secrets"


class ScanStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class ComplianceStandard(Enum):
    OWASP_TOP_10 = "owasp_top_10"
    CWE_TOP_25 = "cwe_top_25"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    SOC2 = "soc2"


class ApiSecurityIssue(Enum):
    MISSING_AUTH = "missing_authentication"
    WEAK_AUTH = "weak_authentication"
    MISSING_RATE_LIMIT = "missing_rate_limit"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    INSECURE_ENDPOINT = "insecure_endpoint"
    MISSING_INPUT_VALIDATION = "missing_input_validation"
    CORS_MISCONFIGURATION = "cors_misconfiguration"
    JWT_ISSUES = "jwt_issues"


class ConfigSecurityIssue(Enum):
    DEBUG_ENABLED = "debug_enabled"
    SECRET_KEY_WEAK = "secret_key_weak"
    INSECURE_COOKIES = "insecure_cookies"
    CORS_WILDCARD = "cors_wildcard"
    SQL_DEBUG_ENABLED = "sql_debug_enabled"
    SSL_DISABLED = "ssl_disabled"
    HARDENING_MISSING = "hardening_missing"


@dataclass
class Vulnerability:
    id: str
    name: str
    category: VulnerabilityCategory
    severity: Severity
    description: str
    location: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: str = ""
    references: List[str] = field(default_factory=list)
    cwe: Optional[str] = None
    owasp: Optional[str] = None
    confidence: float = 1.0
    impact: str = ""
    likelihood: str = ""
    risk_score: float = 0.0
    exploitability: str = ""
    affected_components: List[str] = field(default_factory=list)
    remediation_effort: str = ""
    discovered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: List[str] = field(default_factory=list)
    false_positive: bool = False
    verified: bool = False


@dataclass
class TaintSource:
    name: str
    source_type: str
    location: str
    line_number: int
    description: str


@dataclass
class TaintSink:
    name: str
    sink_type: str
    location: str
    line_number: int
    description: str


@dataclass
class DataFlowPath:
    source: TaintSource
    sink: TaintSink
    path: List[Tuple[str, int]]
    vulnerability_type: str
    sanitized: bool = False


@dataclass
class SecurityRisk:
    risk_id: str
    risk_level: RiskLevel
    category: str
    description: str
    impact: str
    likelihood: str
    affected_assets: List[str]
    mitigation: str
    residual_risk: str


@dataclass
class ComplianceCheck:
    standard: ComplianceStandard
    requirement: str
    status: str
    evidence: str
    gaps: List[str]
    recommendations: List[str]


@dataclass
class DependencyVulnerability:
    package_name: str
    installed_version: str
    vulnerable_versions: str
    fixed_version: str
    severity: Severity
    description: str
    advisory_id: str
    cve_id: Optional[str] = None


@dataclass
class SecurityFinding:
    title: str
    category: VulnerabilityCategory
    severity: Severity
    description: str
    impact: str
    remediation: str
    references: List[str] = field(default_factory=list)


@dataclass
class ScanResult:
    scan_name: str
    status: ScanStatus
    duration: float
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    dependency_vulnerabilities: List[DependencyVulnerability] = field(default_factory=list)
    findings: List[SecurityFinding] = field(default_factory=list)
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SecurityScanConfig:
    source_dirs: List[str] = field(default_factory=lambda: ["backend/app", "src"])
    output_dir: str = None
    output_formats: List[str] = field(default_factory=lambda: ["json", "html"])
    exclude_patterns: List[str] = field(default_factory=lambda: ["__pycache__", ".venv", "venv", "node_modules", "migrations"])
    check_dependencies: bool = True
    check_secrets: bool = True
    check_owasp: bool = True
    check_injection: bool = True
    check_xss: bool = True
    check_auth: bool = True
    check_crypto: bool = True
    check_path_traversal: bool = True
    check_ssrf: bool = True
    fail_on_critical: bool = True
    fail_on_high: bool = False
    max_severity: str = "medium"
    
    def __post_init__(self):
        if self.output_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                self.output_dir = str(_path_mgr.get_output_path(OutputType.REPORT, subdirectory="security"))
            except Exception:
                self.output_dir = "docs/reports"


class ConfigLoader:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def load(self, config_path: Optional[str] = None) -> SecurityScanConfig:
        config = SecurityScanConfig()
        
        if config_path:
            full_path = Path(self.base_path) / config_path
            if full_path.exists():
                try:
                    if full_path.suffix in [".yaml", ".yml"] and HAS_YAML:
                        with open(full_path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                    elif full_path.suffix == ".json":
                        with open(full_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                    else:
                        return config
                    
                    if data:
                        for key, value in data.items():
                            if hasattr(config, key):
                                setattr(config, key, value)
                except Exception as e:
                    print(f"加载配置文件失败: {e}")
        
        return config

    def save_template(self, output_path: str):
        template = {
            "source_dirs": ["backend/app", "src"],
            "output_dir": "docs/reports",
            "output_formats": ["json", "html"],
            "exclude_patterns": ["__pycache__", ".venv", "venv", "node_modules", "migrations", "tests"],
            "check_dependencies": True,
            "check_secrets": True,
            "check_owasp": True,
            "check_injection": True,
            "check_xss": True,
            "check_auth": True,
            "check_crypto": True,
            "check_path_traversal": True,
            "check_ssrf": True,
            "fail_on_critical": True,
            "fail_on_high": False,
            "max_severity": "medium"
        }
        
        full_path = Path(self.base_path) / output_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            if HAS_YAML:
                yaml.dump(template, f, default_flow_style=False, allow_unicode=True)
            else:
                json.dump(template, f, indent=2, ensure_ascii=False)


class SecretScanner:
    SECRET_PATTERNS = [
        (r'(?i)(password|passwd|pwd)\s*=\s*["\']([^"\']+)["\']', "password", Severity.HIGH),
        (r'(?i)(api_key|apikey|api-key)\s*=\s*["\']([^"\']+)["\']', "api_key", Severity.HIGH),
        (r'(?i)(secret|secret_key|secretkey)\s*=\s*["\']([^"\']+)["\']', "secret", Severity.HIGH),
        (r'(?i)(token|access_token|auth_token)\s*=\s*["\']([^"\']+)["\']', "token", Severity.HIGH),
        (r'(?i)(private_key|privatekey)\s*=\s*["\']([^"\']+)["\']', "private_key", Severity.CRITICAL),
        (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', "private_key_block", Severity.CRITICAL),
        (r'(?i)aws_access_key_id\s*=\s*["\']?([A-Z0-9]{20})["\']?', "aws_access_key", Severity.CRITICAL),
        (r'(?i)aws_secret_access_key\s*=\s*["\']?([A-Za-z0-9/+=]{40})["\']?', "aws_secret", Severity.CRITICAL),
        (r'sk-[a-zA-Z0-9]{20,}', "openai_key", Severity.HIGH),
        (r'ghp_[a-zA-Z0-9]{36}', "github_token", Severity.HIGH),
        (r'xox[baprs]-[a-zA-Z0-9-]+', "slack_token", Severity.HIGH),
        (r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', "jwt_token", Severity.MEDIUM),
    ]

    def __init__(self, config: SecurityScanConfig):
        self.config = config
        self.findings: List[Vulnerability] = []

    def scan_directory(self, directory: Path) -> List[Vulnerability]:
        self.findings = []
        
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            self._scan_file(py_file)
        
        for env_file in directory.rglob(".env*"):
            self._scan_file(env_file)
        
        for config_file in directory.rglob("*.json"):
            if "package" not in config_file.name and "lock" not in config_file.name:
                self._scan_file(config_file)
        
        for config_file in directory.rglob("*.yaml"):
            self._scan_file(config_file)
        
        for config_file in directory.rglob("*.yml"):
            self._scan_file(config_file)
        
        return self.findings

    def _should_skip_file(self, file_path: Path) -> bool:
        return any(pattern in str(file_path) for pattern in self.config.exclude_patterns)

    def _scan_file(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")

            for pattern, secret_type, severity in self.SECRET_PATTERNS:
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count("\n") + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                    
                    finding = Vulnerability(
                        id=f"SECRET-{len(self.findings) + 1}",
                        name=f"Hardcoded {secret_type.replace('_', ' ').title()}",
                        category=VulnerabilityCategory.HARDCODED_SECRETS,
                        severity=severity,
                        description=f"检测到硬编码的敏感信息: {secret_type}",
                        location=str(file_path),
                        line_number=line_num,
                        code_snippet=line_content.strip()[:100],
                        recommendation="使用环境变量或安全的密钥管理服务存储敏感信息",
                        cwe="CWE-798",
                        owasp="A07:2021"
                    )
                    self.findings.append(finding)

        except Exception as e:
            print(f"扫描文件失败 {file_path}: {e}")


class InjectionScanner:
    INJECTION_PATTERNS = [
        (r'execute\s*\(\s*["\'].*%s.*["\']', "sql_injection_safe", False),
        (r'execute\s*\(\s*[^"\']+\.format\(', "sql_injection_risk", True),
        (r'execute\s*\(\s*f["\']', "sql_injection_fstring", True),
        (r'\.raw\s*\(\s*["\'].*\+', "raw_sql_risk", True),
        (r'eval\s*\(', "eval_usage", True),
        (r'exec\s*\(', "exec_usage", True),
        (r'subprocess\..*\(\s*shell\s*=\s*True', "shell_injection", True),
        (r'os\.system\s*\(', "os_system", True),
        (r'os\.popen\s*\(', "os_popen", True),
    ]

    def __init__(self, config: SecurityScanConfig):
        self.config = config
        self.findings: List[Vulnerability] = []

    def scan_directory(self, directory: Path) -> List[Vulnerability]:
        self.findings = []
        
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            self._scan_file(py_file)
        
        return self.findings

    def _should_skip_file(self, file_path: Path) -> bool:
        return any(pattern in str(file_path) for pattern in self.config.exclude_patterns)

    def _scan_file(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            for pattern, issue_type, is_risk in self.INJECTION_PATTERNS:
                if is_risk:
                    for match in re.finditer(pattern, content):
                        line_num = content[:match.start()].count("\n") + 1
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                        
                        severity = Severity.HIGH if "sql" in issue_type.lower() else Severity.MEDIUM
                        
                        finding = Vulnerability(
                            id=f"INJECT-{len(self.findings) + 1}",
                            name=f"Potential {issue_type.replace('_', ' ').title()}",
                            category=VulnerabilityCategory.INJECTION,
                            severity=severity,
                            description=f"检测到潜在的注入风险: {issue_type}",
                            location=str(file_path),
                            line_number=line_num,
                            code_snippet=line_content.strip()[:100],
                            recommendation="使用参数化查询或安全的API",
                            cwe="CWE-89",
                            owasp="A03:2021"
                        )
                        self.findings.append(finding)

        except Exception as e:
            print(f"扫描文件失败 {file_path}: {e}")


class XSSScanner:
    XSS_PATTERNS = [
        (r'return\s+.*\+.*request\.', "response_concatenation", True),
        (r'mark_safe\s*\(', "mark_safe_usage", True),
        (r'\|safe\s*}}', "template_safe_filter", True),
        (r'innerHTML\s*=', "inner_html", True),
        (r'document\.write\s*\(', "document_write", True),
    ]

    def __init__(self, config: SecurityScanConfig):
        self.config = config
        self.findings: List[Vulnerability] = []

    def scan_directory(self, directory: Path) -> List[Vulnerability]:
        self.findings = []
        
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            self._scan_file(py_file)
        
        for template_file in directory.rglob("*.html"):
            self._scan_file(template_file)
        
        for js_file in directory.rglob("*.js"):
            if "node_modules" not in str(js_file):
                self._scan_file(js_file)
        
        return self.findings

    def _should_skip_file(self, file_path: Path) -> bool:
        return any(pattern in str(file_path) for pattern in self.config.exclude_patterns)

    def _scan_file(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            for pattern, issue_type, is_risk in self.XSS_PATTERNS:
                if is_risk:
                    for match in re.finditer(pattern, content):
                        line_num = content[:match.start()].count("\n") + 1
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                        
                        finding = Vulnerability(
                            id=f"XSS-{len(self.findings) + 1}",
                            name=f"Potential XSS Vulnerability: {issue_type}",
                            category=VulnerabilityCategory.XSS,
                            severity=Severity.MEDIUM,
                            description=f"检测到潜在的XSS风险: {issue_type}",
                            location=str(file_path),
                            line_number=line_num,
                            code_snippet=line_content.strip()[:100],
                            recommendation="对用户输入进行适当的转义和验证",
                            cwe="CWE-79",
                            owasp="A03:2021"
                        )
                        self.findings.append(finding)

        except Exception as e:
            print(f"扫描文件失败 {file_path}: {e}")


class AuthScanner:
    AUTH_PATTERNS = [
        (r'@app\.route.*methods\s*=\s*\[.*["\']POST["\'].*\].*\ndef\s+\w+\([^)]*\):', "post_without_csrf", True),
        (r'password\s*=\s*request\.(form|json)', "plaintext_password", True),
        (r'check_password\s*\(\s*\w+\s*,\s*["\']', "hardcoded_password_check", True),
        (r'session\[.user.\]\s*=\s*\w+', "session_user_assignment", False),
        (r'@login_required', "login_required_decorator", False),
        (r'verify_password\s*\(', "password_verification", False),
    ]

    def __init__(self, config: SecurityScanConfig):
        self.config = config
        self.findings: List[Vulnerability] = []

    def scan_directory(self, directory: Path) -> List[Vulnerability]:
        self.findings = []
        
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            self._scan_file(py_file)
        
        return self.findings

    def _should_skip_file(self, file_path: Path) -> bool:
        return any(pattern in str(file_path) for pattern in self.config.exclude_patterns)

    def _scan_file(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            for pattern, issue_type, is_risk in self.AUTH_PATTERNS:
                if is_risk:
                    for match in re.finditer(pattern, content):
                        line_num = content[:match.start()].count("\n") + 1
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                        
                        severity = Severity.MEDIUM
                        
                        finding = Vulnerability(
                            id=f"AUTH-{len(self.findings) + 1}",
                            name=f"Authentication Issue: {issue_type}",
                            category=VulnerabilityCategory.AUTHENTICATION,
                            severity=severity,
                            description=f"检测到认证相关问题: {issue_type}",
                            location=str(file_path),
                            line_number=line_num,
                            code_snippet=line_content.strip()[:100],
                            recommendation="确保使用安全的认证机制和CSRF保护",
                            cwe="CWE-287",
                            owasp="A07:2021"
                        )
                        self.findings.append(finding)

        except Exception as e:
            print(f"扫描文件失败 {file_path}: {e}")


class CryptoScanner:
    CRYPTO_PATTERNS = [
        (r'MD5\s*\(', "md5_usage", Severity.MEDIUM),
        (r'SHA1\s*\(', "sha1_usage", Severity.MEDIUM),
        (r'DES\s*\(', "des_usage", Severity.HIGH),
        (r'RC4\s*\(', "rc4_usage", Severity.HIGH),
        (r'random\.random\s*\(', "weak_random", Severity.LOW),
        (r'random\.randint\s*\(', "weak_random", Severity.LOW),
        (r'hashlib\.md5\s*\(', "md5_hash", Severity.MEDIUM),
        (r'hashlib\.sha1\s*\(', "sha1_hash", Severity.MEDIUM),
        (r'AES\.MODE_ECB', "ecb_mode", Severity.HIGH),
        (r'PROTOCOL_TLS\s*\)', "tls_protocol", Severity.MEDIUM),
        (r'PROTOCOL_SSLv[23]', "ssl_protocol", Severity.HIGH),
    ]

    def __init__(self, config: SecurityScanConfig):
        self.config = config
        self.findings: List[Vulnerability] = []

    def scan_directory(self, directory: Path) -> List[Vulnerability]:
        self.findings = []
        
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            self._scan_file(py_file)
        
        return self.findings

    def _should_skip_file(self, file_path: Path) -> bool:
        return any(pattern in str(file_path) for pattern in self.config.exclude_patterns)

    def _scan_file(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            for pattern, issue_type, severity in self.CRYPTO_PATTERNS:
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count("\n") + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                    
                    finding = Vulnerability(
                        id=f"CRYPTO-{len(self.findings) + 1}",
                        name=f"Cryptographic Issue: {issue_type}",
                        category=VulnerabilityCategory.CRYPTOGRAPHIC_FAILURE,
                        severity=severity,
                        description=f"检测到加密相关问题: {issue_type}",
                        location=str(file_path),
                        line_number=line_num,
                        code_snippet=line_content.strip()[:100],
                        recommendation="使用现代、安全的加密算法",
                        cwe="CWE-327",
                        owasp="A02:2021"
                    )
                    self.findings.append(finding)

        except Exception as e:
            print(f"扫描文件失败 {file_path}: {e}")


class VulnerabilityDetector:
    VULNERABILITY_SIGNATURES = {
        "sql_injection": {
            "patterns": [
                (r'cursor\.execute\s*\(\s*f["\'].*\{.*\}.*["\']', "f-string SQL injection"),
                (r'cursor\.execute\s*\(\s*["\'].*%\(.*\)s.*["\'].*%', "format string SQL injection"),
                (r'\.raw\s*\(\s*f["\']', "raw SQL with f-string"),
                (r'connection\.execute\s*\(\s*[^"]*\+', "concatenated SQL"),
                (r'TextClause\s*\(\s*f["\']', "SQLAlchemy text with f-string"),
            ],
            "severity": Severity.CRITICAL,
            "cwe": "CWE-89",
            "owasp": "A03:2021"
        },
        "command_injection": {
            "patterns": [
                (r'subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True', "shell=True subprocess"),
                (r'os\.system\s*\(\s*f["\']', "os.system with f-string"),
                (r'os\.popen\s*\(\s*f["\']', "os.popen with f-string"),
                (r'commands\.getoutput\s*\(', "deprecated commands module"),
            ],
            "severity": Severity.CRITICAL,
            "cwe": "CWE-78",
            "owasp": "A03:2021"
        },
        "path_traversal": {
            "patterns": [
                (r'open\s*\(\s*f["\'].*\{.*request\..*\}', "path traversal via request"),
                (r'open\s*\(\s*[^)]*\+.*request\.', "path concatenation with request"),
                (r'\.read\s*\(\s*f["\'].*\{.*\}', "file read with user input"),
                (r'send_file\s*\(\s*request\.', "Flask send_file with request"),
                (r'static_file\s*\(\s*request\.', "Bottle static_file with request"),
            ],
            "severity": Severity.HIGH,
            "cwe": "CWE-22",
            "owasp": "A01:2021"
        },
        "ssrf": {
            "patterns": [
                (r'requests\.(get|post|put|delete)\s*\(\s*request\.', "requests with user URL"),
                (r'urllib\.request\.urlopen\s*\(\s*request\.', "urllib with user URL"),
                (r'httpx\.(get|post)\s*\(\s*request\.', "httpx with user URL"),
                (r'aiohttp\.ClientSession\(\)\.(get|post)\s*\(\s*request\.', "aiohttp with user URL"),
            ],
            "severity": Severity.HIGH,
            "cwe": "CWE-918",
            "owasp": "A10:2021"
        },
        "xxe": {
            "patterns": [
                (r'xml\.etree\.ElementTree\.parse\s*\(\s*request\.', "XML parse with user input"),
                (r'lxml\.etree\.parse\s*\(\s*request\.', "lxml parse with user input"),
                (r'xml\.dom\.minidom\.parse\s*\(', "minidom parse"),
                (r'defusedxml', "safe XML library usage", False),
            ],
            "severity": Severity.HIGH,
            "cwe": "CWE-611",
            "owasp": "A05:2021"
        },
        "deserialization": {
            "patterns": [
                (r'pickle\.loads\s*\(\s*request\.', "pickle with user input"),
                (r'yaml\.load\s*\(\s*request\.', "yaml.load with user input"),
                (r'yaml\.unsafe_load\s*\(', "yaml.unsafe_load"),
                (r'marshal\.loads\s*\(', "marshal.loads"),
                (r'shelve\.open\s*\(', "shelve.open"),
            ],
            "severity": Severity.CRITICAL,
            "cwe": "CWE-502",
            "owasp": "A08:2021"
        },
        "ldap_injection": {
            "patterns": [
                (r'ldap\.search\s*\(\s*f["\']', "LDAP search with f-string"),
                (r'ldapsearch.*\+', "LDAP query concatenation"),
            ],
            "severity": Severity.HIGH,
            "cwe": "CWE-90",
            "owasp": "A03:2021"
        },
        "open_redirect": {
            "patterns": [
                (r'redirect\s*\(\s*request\.(args|form|json)', "redirect with user input"),
                (r'redirect\s*\(\s*f["\'].*\{', "redirect with f-string"),
                (r'HttpResponseRedirect\s*\(\s*request\.', "Django redirect with request"),
            ],
            "severity": Severity.MEDIUM,
            "cwe": "CWE-601",
            "owasp": "A01:2021"
        },
        "info_disclosure": {
            "patterns": [
                (r'debug\s*=\s*True', "debug mode enabled"),
                (r'print\s*\(\s*.*password', "password in print"),
                (r'print\s*\(\s*.*secret', "secret in print"),
                (r'print\s*\(\s*.*token', "token in print"),
                (r'logging\.(debug|info)\s*\(\s*f["\'].*\{.*password', "password in log"),
            ],
            "severity": Severity.MEDIUM,
            "cwe": "CWE-200",
            "owasp": "A01:2021"
        },
        "weak_random": {
            "patterns": [
                (r'random\.(random|randint|choice)\s*\([^)]*\).*token', "random for token"),
                (r'random\.(random|randint|choice)\s*\([^)]*\).*password', "random for password"),
                (r'random\.(random|randint|choice)\s*\([^)]*\).*secret', "random for secret"),
            ],
            "severity": Severity.MEDIUM,
            "cwe": "CWE-338",
            "owasp": "A02:2021"
        }
    }

    def __init__(self, config: SecurityScanConfig):
        self.config = config
        self.findings: List[Vulnerability] = []
        self._vulnerability_id = 0

    def scan_directory(self, directory: Path) -> List[Vulnerability]:
        self.findings = []
        
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            self._scan_file(py_file)
        
        return self.findings

    def _should_skip_file(self, file_path: Path) -> bool:
        return any(pattern in str(file_path) for pattern in self.config.exclude_patterns)

    def _scan_file(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            for vuln_type, vuln_info in self.VULNERABILITY_SIGNATURES.items():
                for pattern_info in vuln_info["patterns"]:
                    if len(pattern_info) == 3:
                        pattern, desc, is_vuln = pattern_info
                        if not is_vuln:
                            continue
                    else:
                        pattern, desc = pattern_info
                    
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        line_num = content[:match.start()].count("\n") + 1
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                        
                        self._vulnerability_id += 1
                        finding = Vulnerability(
                            id=f"VULN-{self._vulnerability_id:04d}",
                            name=f"{vuln_type.replace('_', ' ').title()}: {desc}",
                            category=self._get_category(vuln_type),
                            severity=vuln_info["severity"],
                            description=f"检测到潜在的{vuln_type.replace('_', ' ')}漏洞: {desc}",
                            location=str(file_path),
                            line_number=line_num,
                            code_snippet=line_content.strip()[:100],
                            recommendation=self._get_recommendation(vuln_type),
                            cwe=vuln_info["cwe"],
                            owasp=vuln_info["owasp"],
                            references=self._get_references(vuln_type)
                        )
                        self.findings.append(finding)

        except Exception as e:
            print(f"扫描文件失败 {file_path}: {e}")

    def _get_category(self, vuln_type: str) -> VulnerabilityCategory:
        category_map = {
            "sql_injection": VulnerabilityCategory.INJECTION,
            "command_injection": VulnerabilityCategory.INJECTION,
            "path_traversal": VulnerabilityCategory.PATH_TRAVERSAL,
            "ssrf": VulnerabilityCategory.SSRF,
            "xxe": VulnerabilityCategory.INJECTION,
            "deserialization": VulnerabilityCategory.INSECURE_DESERIALIZATION,
            "ldap_injection": VulnerabilityCategory.INJECTION,
            "open_redirect": VulnerabilityCategory.BROKEN_ACCESS_CONTROL,
            "info_disclosure": VulnerabilityCategory.SENSITIVE_DATA,
            "weak_random": VulnerabilityCategory.CRYPTOGRAPHIC_FAILURE,
        }
        return category_map.get(vuln_type, VulnerabilityCategory.SECURITY_MISCONFIGURATION)

    def _get_recommendation(self, vuln_type: str) -> str:
        recommendations = {
            "sql_injection": "使用参数化查询或ORM，避免字符串拼接SQL语句",
            "command_injection": "避免使用shell=True，使用参数列表形式传递命令",
            "path_traversal": "验证和清理用户输入的文件路径，使用os.path.basename限制",
            "ssrf": "验证和限制用户输入的URL，使用白名单机制",
            "xxe": "禁用外部实体解析，使用defusedxml库",
            "deserialization": "避免反序列化不受信任的数据，使用JSON等安全格式",
            "ldap_injection": "对LDAP查询进行参数化，转义特殊字符",
            "open_redirect": "验证重定向URL，使用白名单或相对路径",
            "info_disclosure": "关闭调试模式，避免在日志中输出敏感信息",
            "weak_random": "使用secrets模块生成安全随机数",
        }
        return recommendations.get(vuln_type, "修复此安全问题")

    def _get_references(self, vuln_type: str) -> List[str]:
        references = {
            "sql_injection": ["https://owasp.org/www-community/attacks/SQL_Injection"],
            "command_injection": ["https://owasp.org/www-community/attacks/Command_Injection"],
            "path_traversal": ["https://owasp.org/www-community/attacks/Path_Traversal"],
            "ssrf": ["https://owasp.org/www-community/attacks/Server_Side_Request_Forgery"],
            "xxe": ["https://owasp.org/www-community/vulnerabilities/XML_External_Entity_(XXE)_Processing"],
            "deserialization": ["https://owasp.org/www-community/vulnerabilities/Deserialization_of_untrusted_data"],
        }
        return references.get(vuln_type, [])


class SecurityFixGenerator:
    FIX_TEMPLATES = {
        "sql_injection": {
            "vulnerable": 'cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")',
            "fixed": 'cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))',
            "description": "使用参数化查询替代字符串格式化"
        },
        "command_injection": {
            "vulnerable": 'subprocess.run(f"ls {user_input}", shell=True)',
            "fixed": 'subprocess.run(["ls", user_input], shell=False)',
            "description": "使用参数列表形式，避免shell=True"
        },
        "path_traversal": {
            "vulnerable": 'open(f"/uploads/{filename}", "r")',
            "fixed": 'import os\nsafe_path = os.path.join("/uploads", os.path.basename(filename))\nopen(safe_path, "r")',
            "description": "使用os.path.basename限制路径遍历"
        },
        "hardcoded_secrets": {
            "vulnerable": 'API_KEY = "sk-1234567890abcdef"',
            "fixed": 'import os\nAPI_KEY = os.environ.get("API_KEY")',
            "description": "使用环境变量存储敏感信息"
        },
        "weak_crypto": {
            "vulnerable": 'hashlib.md5(password.encode())',
            "fixed": 'import hashlib\nhashlib.sha256(password.encode())',
            "description": "使用SHA-256等安全哈希算法"
        },
        "weak_random": {
            "vulnerable": 'random.randint(0, 999999)',
            "fixed": 'import secrets\nsecrets.randbelow(1000000)',
            "description": "使用secrets模块生成安全随机数"
        },
        "xss": {
            "vulnerable": 'return f"<div>{user_input}</div>"',
            "fixed": 'from markupsafe import escape\nreturn f"<div>{escape(user_input)}</div>"',
            "description": "对用户输入进行HTML转义"
        },
        "ssrf": {
            "vulnerable": 'requests.get(user_url)',
            "fixed": '''from urllib.parse import urlparse
allowed_domains = ["api.example.com", "cdn.example.com"]
parsed = urlparse(user_url)
if parsed.netloc not in allowed_domains:
    raise ValueError("Domain not allowed")
requests.get(user_url)''',
            "description": "验证URL域名白名单"
        },
        "deserialization": {
            "vulnerable": 'pickle.loads(user_data)',
            "fixed": 'import json\ndata = json.loads(user_data)',
            "description": "使用JSON等安全序列化格式"
        },
        "debug_mode": {
            "vulnerable": 'app.run(debug=True)',
            "fixed": 'app.run(debug=False)',
            "description": "生产环境关闭调试模式"
        }
    }

    def __init__(self):
        self.fixes: List[Dict[str, Any]] = []

    def generate_fix(self, vulnerability: Vulnerability) -> Dict[str, Any]:
        fix_key = self._determine_fix_key(vulnerability)
        
        fix_info = self.FIX_TEMPLATES.get(fix_key, {})
        
        fix = {
            "vulnerability_id": vulnerability.id,
            "vulnerability_name": vulnerability.name,
            "severity": vulnerability.severity.value,
            "location": vulnerability.location,
            "line_number": vulnerability.line_number,
            "current_code": vulnerability.code_snippet,
            "fix_description": fix_info.get("description", "请手动修复此问题"),
            "suggested_fix": fix_info.get("fixed", ""),
            "vulnerable_example": fix_info.get("vulnerable", ""),
            "fix_steps": self._generate_fix_steps(vulnerability, fix_key),
            "priority": self._calculate_priority(vulnerability),
            "estimated_effort": self._estimate_effort(vulnerability),
            "references": vulnerability.references
        }
        
        self.fixes.append(fix)
        return fix

    def _determine_fix_key(self, vulnerability: Vulnerability) -> str:
        name_lower = vulnerability.name.lower()
        category = vulnerability.category.value
        
        if "sql" in name_lower or "injection" in name_lower and "sql" in name_lower:
            return "sql_injection"
        elif "command" in name_lower or "shell" in name_lower:
            return "command_injection"
        elif "path" in name_lower or "traversal" in name_lower:
            return "path_traversal"
        elif "secret" in name_lower or "password" in name_lower or "key" in name_lower:
            return "hardcoded_secrets"
        elif "md5" in name_lower or "sha1" in name_lower or "des" in name_lower:
            return "weak_crypto"
        elif "random" in name_lower:
            return "weak_random"
        elif "xss" in name_lower:
            return "xss"
        elif "ssrf" in name_lower:
            return "ssrf"
        elif "pickle" in name_lower or "yaml" in name_lower:
            return "deserialization"
        elif "debug" in name_lower:
            return "debug_mode"
        
        return category

    def _generate_fix_steps(self, vulnerability: Vulnerability, fix_key: str) -> List[str]:
        base_steps = [
            f"1. 定位文件: {vulnerability.location}",
            f"2. 找到第 {vulnerability.line_number} 行的问题代码",
        ]
        
        specific_steps = {
            "sql_injection": [
                "3. 将SQL语句中的变量替换为参数占位符",
                "4. 使用参数化查询传递变量值",
                "5. 测试修改后的查询功能"
            ],
            "command_injection": [
                "3. 移除shell=True参数",
                "4. 将命令改为列表形式传递",
                "5. 验证命令执行结果"
            ],
            "hardcoded_secrets": [
                "3. 将敏感信息移至环境变量",
                "4. 使用os.environ.get()获取值",
                "5. 更新部署配置添加环境变量"
            ],
            "weak_crypto": [
                "3. 替换为安全的加密算法",
                "4. 更新相关依赖库",
                "5. 重新哈希现有数据"
            ],
            "path_traversal": [
                "3. 使用os.path.basename()清理文件名",
                "4. 验证最终路径是否在允许目录内",
                "5. 添加路径访问日志"
            ]
        }
        
        return base_steps + specific_steps.get(fix_key, ["3. 根据最佳实践修复问题", "4. 测试修复效果"])

    def _calculate_priority(self, vulnerability: Vulnerability) -> str:
        if vulnerability.severity == Severity.CRITICAL:
            return "P0 - 立即修复"
        elif vulnerability.severity == Severity.HIGH:
            return "P1 - 优先修复"
        elif vulnerability.severity == Severity.MEDIUM:
            return "P2 - 计划修复"
        else:
            return "P3 - 低优先级"

    def _estimate_effort(self, vulnerability: Vulnerability) -> str:
        category = vulnerability.category
        
        high_effort_categories = [
            VulnerabilityCategory.INJECTION,
            VulnerabilityCategory.AUTHENTICATION,
            VulnerabilityCategory.AUTHORIZATION
        ]
        
        medium_effort_categories = [
            VulnerabilityCategory.CRYPTOGRAPHIC_FAILURE,
            VulnerabilityCategory.SSRF,
            VulnerabilityCategory.INSECURE_DESERIALIZATION
        ]
        
        if category in high_effort_categories:
            return "高 (需要仔细测试)"
        elif category in medium_effort_categories:
            return "中 (需要一定测试)"
        else:
            return "低 (简单修改)"

    def generate_fix_report(self, vulnerabilities: List[Vulnerability]) -> Dict[str, Any]:
        fixes = [self.generate_fix(v) for v in vulnerabilities]
        
        return {
            "total_fixes": len(fixes),
            "by_priority": {
                "P0": len([f for f in fixes if f["priority"].startswith("P0")]),
                "P1": len([f for f in fixes if f["priority"].startswith("P1")]),
                "P2": len([f for f in fixes if f["priority"].startswith("P2")]),
                "P3": len([f for f in fixes if f["priority"].startswith("P3")])
            },
            "by_effort": {
                "高": len([f for f in fixes if f["estimated_effort"].startswith("高")]),
                "中": len([f for f in fixes if f["estimated_effort"].startswith("中")]),
                "低": len([f for f in fixes if f["estimated_effort"].startswith("低")])
            },
            "fixes": fixes
        }


class DependencyScanner:
    def __init__(self, config: SecurityScanConfig):
        self.config = config
        self.vulnerabilities: List[DependencyVulnerability] = []

    def scan_python_dependencies(self) -> List[DependencyVulnerability]:
        self.vulnerabilities = []
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                
                known_vulnerable = [
                    ("requests", "2.25.0", "2.26.0", "CVE-2021-33503", Severity.MEDIUM),
                    ("pyyaml", "5.3", "5.4", "CVE-2020-14343", Severity.HIGH),
                    ("jinja2", "2.11.0", "2.11.3", "CVE-2021-28976", Severity.MEDIUM),
                ]
                
                for pkg in packages:
                    name = pkg.get("name", "").lower()
                    version = pkg.get("version", "")
                    
                    for vuln_name, vuln_ver, fixed_ver, cve, severity in known_vulnerable:
                        if name == vuln_name.lower():
                            self.vulnerabilities.append(DependencyVulnerability(
                                package_name=name,
                                installed_version=version,
                                vulnerable_versions=f"< {fixed_ver}",
                                fixed_version=fixed_ver,
                                severity=severity,
                                description=f"已知漏洞 {cve}",
                                advisory_id=cve,
                                cve_id=cve
                            ))
        
        except Exception as e:
            print(f"扫描Python依赖失败: {e}")
        
        return self.vulnerabilities

    def scan_node_dependencies(self) -> List[DependencyVulnerability]:
        node_vulns = []
        
        package_json = Path("package.json")
        if package_json.exists():
            try:
                with open(package_json, "r") as f:
                    data = json.load(f)
                
                dependencies = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                
                known_vulnerable = [
                    ("lodash", "4.17.15", "4.17.21", "CVE-2021-23337", Severity.HIGH),
                    ("axios", "0.21.0", "0.21.1", "CVE-2021-3749", Severity.MEDIUM),
                    ("node-fetch", "2.6.0", "2.6.1", "CVE-2020-15168", Severity.MEDIUM),
                ]
                
                for name, version in dependencies.items():
                    clean_version = version.replace("^", "").replace("~", "").replace(">=", "").replace("<=", "")
                    
                    for vuln_name, vuln_ver, fixed_ver, cve, severity in known_vulnerable:
                        if name.lower() == vuln_name.lower():
                            node_vulns.append(DependencyVulnerability(
                                package_name=name,
                                installed_version=clean_version,
                                vulnerable_versions=f"< {fixed_ver}",
                                fixed_version=fixed_ver,
                                severity=severity,
                                description=f"已知漏洞 {cve}",
                                advisory_id=cve,
                                cve_id=cve
                            ))
            
            except Exception as e:
                print(f"扫描Node依赖失败: {e}")
        
        return node_vulns


class CodeAuditScanner:
    """
    代码审计扫描器
    执行深度代码质量与安全审计
    """
    
    CODE_QUALITY_PATTERNS = {
        "complexity": [
            (r'def\s+\w+\([^)]*\):[^}]{500,}', "函数过长", Severity.LOW),
            (r'if\s+.*if\s+.*if\s+.*if\s+', "嵌套过深", Severity.LOW),
            (r'except\s*:', "裸except捕获", Severity.MEDIUM),
            (r'except\s+Exception\s*:', "宽泛异常捕获", Severity.LOW),
        ],
        "security_patterns": [
            (r'try\s*:\s*\n\s*pass\s*\n\s*except', "空try块", Severity.LOW),
            (r'#\s*TODO|#\s*FIXME|#\s*HACK', "未完成代码标记", Severity.INFO),
            (r'assert\s+', "断言使用(生产环境可能被禁用)", Severity.LOW),
            (r'__import__\s*\(', "动态导入", Severity.MEDIUM),
        ],
        "best_practices": [
            (r'global\s+\w+', "全局变量使用", Severity.LOW),
            (r'from\s+\w+\s+import\s+\*', "通配符导入", Severity.LOW),
            (r'exec\s*\(\s*["\']', "动态代码执行", Severity.HIGH),
            (r'compile\s*\(\s*["\']', "动态编译", Severity.MEDIUM),
        ]
    }
    
    DANGEROUS_FUNCTIONS = {
        "eval": {"severity": Severity.HIGH, "description": "动态代码执行风险", "cwe": "CWE-95"},
        "exec": {"severity": Severity.HIGH, "description": "动态代码执行风险", "cwe": "CWE-95"},
        "compile": {"severity": Severity.MEDIUM, "description": "动态编译风险", "cwe": "CWE-95"},
        "__import__": {"severity": Severity.MEDIUM, "description": "动态导入风险", "cwe": "CWE-94"},
        "input": {"severity": Severity.LOW, "description": "Python 2中不安全的输入函数", "cwe": "CWE-20"},
        "raw_input": {"severity": Severity.LOW, "description": "Python 2遗留函数", "cwe": "CWE-20"},
    }
    
    def __init__(self, config: SecurityScanConfig):
        self.config = config
        self.findings: List[Vulnerability] = []
        self._audit_id = 0
    
    def scan_directory(self, directory: Path) -> List[Vulnerability]:
        self.findings = []
        
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            self._audit_file(py_file)
        
        return self.findings
    
    def _should_skip_file(self, file_path: Path) -> bool:
        return any(pattern in str(file_path) for pattern in self.config.exclude_patterns)
    
    def _audit_file(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
            
            self._check_code_quality(file_path, content, lines)
            self._check_dangerous_functions(file_path, content, lines)
            self._check_ast_security(file_path, content)
            
        except Exception as e:
            print(f"审计文件失败 {file_path}: {e}")
    
    def _check_code_quality(self, file_path: Path, content: str, lines: List[str]):
        for category, patterns in self.CODE_QUALITY_PATTERNS.items():
            for pattern, desc, severity in patterns:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    line_num = content[:match.start()].count("\n") + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                    
                    self._audit_id += 1
                    finding = Vulnerability(
                        id=f"AUDIT-{self._audit_id:04d}",
                        name=f"代码质量: {desc}",
                        category=VulnerabilityCategory.SECURITY_MISCONFIGURATION,
                        severity=severity,
                        description=f"代码审计发现: {desc}",
                        location=str(file_path),
                        line_number=line_num,
                        code_snippet=line_content.strip()[:100],
                        recommendation=self._get_quality_recommendation(desc),
                        confidence=0.8,
                        tags=["code-quality", category]
                    )
                    self.findings.append(finding)
    
    def _check_dangerous_functions(self, file_path: Path, content: str, lines: List[str]):
        for func_name, info in self.DANGEROUS_FUNCTIONS.items():
            pattern = rf'\b{func_name}\s*\('
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count("\n") + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                if self._is_safe_context(content, match.start()):
                    continue
                
                self._audit_id += 1
                finding = Vulnerability(
                    id=f"AUDIT-{self._audit_id:04d}",
                    name=f"危险函数使用: {func_name}",
                    category=VulnerabilityCategory.INJECTION,
                    severity=info["severity"],
                    description=info["description"],
                    location=str(file_path),
                    line_number=line_num,
                    code_snippet=line_content.strip()[:100],
                    recommendation=f"避免使用 {func_name} 函数，寻找安全的替代方案",
                    cwe=info["cwe"],
                    confidence=0.9,
                    tags=["dangerous-function", "security"]
                )
                self.findings.append(finding)
    
    def _check_ast_security(self, file_path: Path, content: str):
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.DANGEROUS_FUNCTIONS:
                            self._audit_id += 1
                            finding = Vulnerability(
                                id=f"AUDIT-{self._audit_id:04d}",
                                name=f"AST检测: 危险函数 {node.func.id}",
                                category=VulnerabilityCategory.INJECTION,
                                severity=self.DANGEROUS_FUNCTIONS[node.func.id]["severity"],
                                description=f"AST分析发现危险函数调用: {node.func.id}",
                                location=str(file_path),
                                line_number=node.lineno,
                                recommendation="重构代码避免使用此函数",
                                confidence=0.95,
                                tags=["ast-analysis", "dangerous-function"]
                            )
                            self.findings.append(finding)
                
                elif isinstance(node, ast.Attribute):
                    if node.attr.startswith("_") and not node.attr.startswith("__"):
                        self._audit_id += 1
                        finding = Vulnerability(
                            id=f"AUDIT-{self._audit_id:04d}",
                            name="访问私有属性",
                            category=VulnerabilityCategory.SECURITY_MISCONFIGURATION,
                            severity=Severity.INFO,
                            description=f"访问私有属性: {node.attr}",
                            location=str(file_path),
                            line_number=node.lineno,
                            recommendation="避免访问私有属性，使用公共API",
                            confidence=0.7,
                            tags=["code-quality", "private-access"]
                        )
                        self.findings.append(finding)
        
        except SyntaxError:
            pass
    
    def _is_safe_context(self, content: str, position: int) -> bool:
        safe_patterns = [
            r'#\s*safe:',
            r'#\s*nosec',
            r'#\s*noqa',
        ]
        
        line_start = content.rfind("\n", 0, position) + 1
        line_end = content.find("\n", position)
        line = content[line_start:line_end] if line_end != -1 else content[line_start:]
        
        return any(re.search(p, line) for p in safe_patterns)
    
    def _get_quality_recommendation(self, issue: str) -> str:
        recommendations = {
            "函数过长": "将长函数拆分为更小的、单一职责的函数",
            "嵌套过深": "使用早返回或提取方法减少嵌套层级",
            "裸except捕获": "明确指定要捕获的异常类型",
            "宽泛异常捕获": "捕获具体的异常类型，避免隐藏错误",
            "空try块": "添加适当的异常处理逻辑",
            "断言使用(生产环境可能被禁用)": "使用显式的条件检查替代断言",
            "动态导入": "使用静态导入，或确保动态导入的安全性",
            "全局变量使用": "避免使用全局变量，使用函数参数和返回值",
            "通配符导入": "明确导入需要的模块成员",
        }
        return recommendations.get(issue, "遵循代码最佳实践")


class ConfigSecurityScanner:
    """
    配置安全扫描器
    检测配置文件中的安全问题
    """
    
    CONFIG_SECURITY_CHECKS = {
        "django": {
            "patterns": [
                (r'DEBUG\s*=\s*True', ConfigSecurityIssue.DEBUG_ENABLED, Severity.HIGH),
                (r'SECRET_KEY\s*=\s*["\'][^"\']{1,20}["\']', ConfigSecurityIssue.SECRET_KEY_WEAK, Severity.CRITICAL),
                (r'SECRET_KEY\s*=\s*["\'][^"\']+["\']', ConfigSecurityIssue.SECRET_KEY_WEAK, Severity.HIGH),
                (r'ALLOWED_HOSTS\s*=\s*\[\s*\*\s*\]', ConfigSecurityIssue.HARDENING_MISSING, Severity.HIGH),
                (r'SESSION_COOKIE_SECURE\s*=\s*False', ConfigSecurityIssue.INSECURE_COOKIES, Severity.MEDIUM),
                (r'CSRF_COOKIE_SECURE\s*=\s*False', ConfigSecurityIssue.INSECURE_COOKIES, Severity.MEDIUM),
                (r'SECURE_SSL_REDIRECT\s*=\s*False', ConfigSecurityIssue.SSL_DISABLED, Severity.MEDIUM),
            ],
            "file_patterns": ["settings.py", "settings/*.py", "local_settings.py"]
        },
        "flask": {
            "patterns": [
                (r'app\.debug\s*=\s*True', ConfigSecurityIssue.DEBUG_ENABLED, Severity.HIGH),
                (r'app\.config\[.SECRET_KEY.\]\s*=\s*["\'][^"\']{1,20}["\']', ConfigSecurityIssue.SECRET_KEY_WEAK, Severity.CRITICAL),
                (r'SECRET_KEY\s*=\s*["\'][^"\']{1,20}["\']', ConfigSecurityIssue.SECRET_KEY_WEAK, Severity.CRITICAL),
                (r'session\.permanent\s*=\s*True', ConfigSecurityIssue.INSECURE_COOKIES, Severity.LOW),
            ],
            "file_patterns": ["app.py", "config.py", "settings.py"]
        },
        "general": {
            "patterns": [
                (r'password\s*=\s*["\'][^"\']+["\']', ConfigSecurityIssue.SECRET_KEY_WEAK, Severity.CRITICAL),
                (r'api_key\s*=\s*["\'][^"\']+["\']', ConfigSecurityIssue.SECRET_KEY_WEAK, Severity.CRITICAL),
                (r'secret\s*=\s*["\'][^"\']+["\']', ConfigSecurityIssue.SECRET_KEY_WEAK, Severity.HIGH),
                (r'cors.*\*.*allow', ConfigSecurityIssue.CORS_WILDCARD, Severity.MEDIUM),
                (r'Access-Control-Allow-Origin\s*:\s*\*', ConfigSecurityIssue.CORS_WILDCARD, Severity.MEDIUM),
            ],
            "file_patterns": ["*.py", "*.json", "*.yaml", "*.yml", "*.env", ".env*"]
        }
    }
    
    def __init__(self, config: SecurityScanConfig):
        self.config = config
        self.findings: List[Vulnerability] = []
        self._config_id = 0
    
    def scan_directory(self, directory: Path) -> List[Vulnerability]:
        self.findings = []
        
        self._scan_framework_configs(directory, "django")
        self._scan_framework_configs(directory, "flask")
        self._scan_general_configs(directory)
        self._scan_env_files(directory)
        
        return self.findings
    
    def _scan_framework_configs(self, directory: Path, framework: str):
        framework_config = self.CONFIG_SECURITY_CHECKS.get(framework, {})
        file_patterns = framework_config.get("file_patterns", [])
        
        for pattern in file_patterns:
            for config_file in directory.rglob(pattern):
                if self._should_skip_file(config_file):
                    continue
                self._check_config_file(config_file, framework)
    
    def _scan_general_configs(self, directory: Path):
        general_config = self.CONFIG_SECURITY_CHECKS.get("general", {})
        
        for ext in [".py", ".json", ".yaml", ".yml"]:
            for config_file in directory.rglob(f"*{ext}"):
                if self._should_skip_file(config_file):
                    continue
                self._check_config_file(config_file, "general")
    
    def _scan_env_files(self, directory: Path):
        for env_file in directory.rglob(".env*"):
            if "example" in env_file.name.lower():
                continue
            self._check_env_file(env_file)
    
    def _should_skip_file(self, file_path: Path) -> bool:
        skip_patterns = ["__pycache__", ".venv", "venv", "node_modules", "migrations", ".git"]
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _check_config_file(self, file_path: Path, framework: str):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
            
            patterns = self.CONFIG_SECURITY_CHECKS.get(framework, {}).get("patterns", [])
            
            for pattern, issue_type, severity in patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    line_num = content[:match.start()].count("\n") + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                    
                    self._config_id += 1
                    finding = Vulnerability(
                        id=f"CONFIG-{self._config_id:04d}",
                        name=f"配置安全: {issue_type.value}",
                        category=VulnerabilityCategory.SECURITY_MISCONFIGURATION,
                        severity=severity,
                        description=f"配置文件中发现安全问题: {issue_type.value}",
                        location=str(file_path),
                        line_number=line_num,
                        code_snippet=line_content.strip()[:100],
                        recommendation=self._get_config_recommendation(issue_type),
                        cwe="CWE-16",
                        owasp="A05:2021",
                        confidence=0.95,
                        tags=["config-security", framework]
                    )
                    self.findings.append(finding)
        
        except Exception as e:
            print(f"扫描配置文件失败 {file_path}: {e}")
    
    def _check_env_file(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
            
            for i, line in enumerate(lines, 1):
                if "=" in line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    if value and not value.startswith("${") and not value.startswith("$"):
                        sensitive_keys = ["password", "secret", "key", "token", "api_key", "private"]
                        if any(sk in key.lower() for sk in sensitive_keys):
                            self._config_id += 1
                            finding = Vulnerability(
                                id=f"CONFIG-{self._config_id:04d}",
                                name=f"环境文件中的敏感信息: {key}",
                                category=VulnerabilityCategory.HARDCODED_SECRETS,
                                severity=Severity.HIGH,
                                description=f"环境文件中可能包含敏感信息",
                                location=str(file_path),
                                line_number=i,
                                code_snippet=f"{key}=***",
                                recommendation="确保.env文件不被提交到版本控制，使用.env.example作为模板",
                                cwe="CWE-538",
                                owasp="A07:2021",
                                confidence=0.8,
                                tags=["env-security", "secrets"]
                            )
                            self.findings.append(finding)
        
        except Exception as e:
            print(f"扫描环境文件失败 {file_path}: {e}")
    
    def _get_config_recommendation(self, issue_type: ConfigSecurityIssue) -> str:
        recommendations = {
            ConfigSecurityIssue.DEBUG_ENABLED: "生产环境必须关闭DEBUG模式",
            ConfigSecurityIssue.SECRET_KEY_WEAK: "使用强随机密钥，并通过环境变量管理",
            ConfigSecurityIssue.INSECURE_COOKIES: "启用Cookie安全标志: Secure, HttpOnly, SameSite",
            ConfigSecurityIssue.CORS_WILDCARD: "限制CORS允许的域名，避免使用通配符",
            ConfigSecurityIssue.SQL_DEBUG_ENABLED: "关闭SQL调试输出",
            ConfigSecurityIssue.SSL_DISABLED: "强制使用HTTPS，启用SSL重定向",
            ConfigSecurityIssue.HARDENING_MISSING: "添加安全加固配置",
        }
        return recommendations.get(issue_type, "修复配置安全问题")


class ApiSecurityScanner:
    """
    API安全扫描器
    检测REST API安全漏洞
    """
    
    API_SECURITY_PATTERNS = {
        "authentication": [
            (r'@app\.route\s*\([^)]*\)\s*\ndef\s+\w+\([^)]*\):(?:(?!@login_required|@auth|@jwt|@api_key).)*$', 
             ApiSecurityIssue.MISSING_AUTH, Severity.HIGH),
            (r'@route.*methods\s*=\s*\[.*["\']POST["\'].*\](?!.*@csrf)', 
             ApiSecurityIssue.MISSING_AUTH, Severity.MEDIUM),
        ],
        "authorization": [
            (r'@app\.route.*delete', ApiSecurityIssue.INSECURE_ENDPOINT, Severity.HIGH),
            (r'@app\.route.*admin', ApiSecurityIssue.INSECURE_ENDPOINT, Severity.HIGH),
            (r'delete_user|delete_account|remove_user', ApiSecurityIssue.INSECURE_ENDPOINT, Severity.MEDIUM),
        ],
        "input_validation": [
            (r'request\.(json|form|args)\[[\'"][^\'"]+[\'"]\](?!\s*(or|and|\|\||&&))', 
             ApiSecurityIssue.MISSING_INPUT_VALIDATION, Severity.MEDIUM),
            (r'request\.data(?!\s*(or|and|==|!=))', ApiSecurityIssue.MISSING_INPUT_VALIDATION, Severity.LOW),
        ],
        "data_exposure": [
            (r'return\s+jsonify\s*\(\s*\w+\s*\)', ApiSecurityIssue.SENSITIVE_DATA_EXPOSURE, Severity.MEDIUM),
            (r'return\s+\{.*password.*\}', ApiSecurityIssue.SENSITIVE_DATA_EXPOSURE, Severity.HIGH),
            (r'return\s+\{.*token.*\}', ApiSecurityIssue.SENSITIVE_DATA_EXPOSURE, Severity.MEDIUM),
            (r'return\s+\{.*secret.*\}', ApiSecurityIssue.SENSITIVE_DATA_EXPOSURE, Severity.HIGH),
        ],
        "rate_limiting": [
            (r'@app\.route(?!\s*(?:.*@rate_limit|.*@limiter))', ApiSecurityIssue.MISSING_RATE_LIMIT, Severity.LOW),
        ],
        "cors": [
            (r'CORS\s*\(\s*app\s*\)', ApiSecurityIssue.CORS_MISCONFIGURATION, Severity.MEDIUM),
            (r'@cross_origin\s*\(\s*\)', ApiSecurityIssue.CORS_MISCONFIGURATION, Severity.MEDIUM),
        ],
        "jwt": [
            (r'jwt\.encode\s*\([^)]*algorithm\s*=\s*["\']none["\']', ApiSecurityIssue.JWT_ISSUES, Severity.CRITICAL),
            (r'jwt\.decode\s*\([^)]*verify\s*=\s*False', ApiSecurityIssue.JWT_ISSUES, Severity.CRITICAL),
            (r'jwt\.encode\s*\([^)]*\)(?!.*algorithm)', ApiSecurityIssue.JWT_ISSUES, Severity.HIGH),
        ]
    }
    
    SENSITIVE_ENDPOINTS = [
        "/login", "/logout", "/register", "/password", "/admin",
        "/api/users", "/api/accounts", "/api/auth", "/api/token",
        "/graphql", "/api/internal"
    ]
    
    def __init__(self, config: SecurityScanConfig):
        self.config = config
        self.findings: List[Vulnerability] = []
        self._api_id = 0
    
    def scan_directory(self, directory: Path) -> List[Vulnerability]:
        self.findings = []
        
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            self._scan_api_file(py_file)
        
        return self.findings
    
    def _should_skip_file(self, file_path: Path) -> bool:
        return any(pattern in str(file_path) for pattern in self.config.exclude_patterns)
    
    def _scan_api_file(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
            
            self._check_authentication(file_path, content, lines)
            self._check_authorization(file_path, content, lines)
            self._check_input_validation(file_path, content, lines)
            self._check_data_exposure(file_path, content, lines)
            self._check_rate_limiting(file_path, content, lines)
            self._check_cors(file_path, content, lines)
            self._check_jwt(file_path, content, lines)
            self._check_sensitive_endpoints(file_path, content, lines)
            
        except Exception as e:
            print(f"扫描API文件失败 {file_path}: {e}")
    
    def _check_authentication(self, file_path: Path, content: str, lines: List[str]):
        route_pattern = r'@app\.route\s*\(["\']([^"\']+)["\']'
        
        for match in re.finditer(route_pattern, content):
            endpoint = match.group(1)
            line_num = content[:match.start()].count("\n") + 1
            
            context_start = max(0, match.start() - 200)
            context = content[context_start:match.start() + 500]
            
            has_auth = bool(re.search(r'@(login_required|auth|jwt|api_key|token_required)', context))
            
            if not has_auth and self._is_sensitive_endpoint(endpoint):
                self._api_id += 1
                finding = Vulnerability(
                    id=f"API-{self._api_id:04d}",
                    name="API缺少认证保护",
                    category=VulnerabilityCategory.AUTHENTICATION,
                    severity=Severity.HIGH,
                    description=f"敏感端点 {endpoint} 缺少认证保护",
                    location=str(file_path),
                    line_number=line_num,
                    code_snippet=f"Endpoint: {endpoint}",
                    recommendation="为敏感端点添加认证装饰器",
                    cwe="CWE-306",
                    owasp="A07:2021",
                    confidence=0.85,
                    tags=["api-security", "authentication"]
                )
                self.findings.append(finding)
    
    def _check_authorization(self, file_path: Path, content: str, lines: List[str]):
        patterns = self.API_SECURITY_PATTERNS["authorization"]
        
        for pattern, issue_type, severity in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count("\n") + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                self._api_id += 1
                finding = Vulnerability(
                    id=f"API-{self._api_id:04d}",
                    name=f"API授权问题: {issue_type.value}",
                    category=VulnerabilityCategory.AUTHORIZATION,
                    severity=severity,
                    description="检测到潜在的授权问题",
                    location=str(file_path),
                    line_number=line_num,
                    code_snippet=line_content.strip()[:100],
                    recommendation="实现适当的授权检查",
                    cwe="CWE-863",
                    owasp="A01:2021",
                    confidence=0.7,
                    tags=["api-security", "authorization"]
                )
                self.findings.append(finding)
    
    def _check_input_validation(self, file_path: Path, content: str, lines: List[str]):
        patterns = self.API_SECURITY_PATTERNS["input_validation"]
        
        for pattern, issue_type, severity in patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count("\n") + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                self._api_id += 1
                finding = Vulnerability(
                    id=f"API-{self._api_id:04d}",
                    name="API输入验证缺失",
                    category=VulnerabilityCategory.INJECTION,
                    severity=severity,
                    description="API端点缺少输入验证",
                    location=str(file_path),
                    line_number=line_num,
                    code_snippet=line_content.strip()[:100],
                    recommendation="添加输入验证和清理逻辑",
                    cwe="CWE-20",
                    owasp="A03:2021",
                    confidence=0.75,
                    tags=["api-security", "input-validation"]
                )
                self.findings.append(finding)
    
    def _check_data_exposure(self, file_path: Path, content: str, lines: List[str]):
        patterns = self.API_SECURITY_PATTERNS["data_exposure"]
        
        for pattern, issue_type, severity in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count("\n") + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                self._api_id += 1
                finding = Vulnerability(
                    id=f"API-{self._api_id:04d}",
                    name="API敏感数据暴露",
                    category=VulnerabilityCategory.SENSITIVE_DATA,
                    severity=severity,
                    description="API响应可能暴露敏感数据",
                    location=str(file_path),
                    line_number=line_num,
                    code_snippet=line_content.strip()[:100],
                    recommendation="过滤响应中的敏感字段",
                    cwe="CWE-200",
                    owasp="A01:2021",
                    confidence=0.7,
                    tags=["api-security", "data-exposure"]
                )
                self.findings.append(finding)
    
    def _check_rate_limiting(self, file_path: Path, content: str, lines: List[str]):
        route_pattern = r'@app\.route'
        rate_limit_pattern = r'@(rate_limit|limiter)'
        
        route_matches = list(re.finditer(route_pattern, content))
        rate_limit_matches = list(re.finditer(rate_limit_pattern, content))
        
        if route_matches and not rate_limit_matches:
            self._api_id += 1
            finding = Vulnerability(
                id=f"API-{self._api_id:04d}",
                name="API缺少速率限制",
                category=VulnerabilityCategory.SECURITY_MISCONFIGURATION,
                severity=Severity.LOW,
                description="API端点缺少速率限制保护",
                location=str(file_path),
                line_number=1,
                code_snippet="",
                recommendation="添加速率限制装饰器防止滥用",
                cwe="CWE-770",
                owasp="A04:2021",
                confidence=0.6,
                tags=["api-security", "rate-limiting"]
            )
            self.findings.append(finding)
    
    def _check_cors(self, file_path: Path, content: str, lines: List[str]):
        patterns = self.API_SECURITY_PATTERNS["cors"]
        
        for pattern, issue_type, severity in patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count("\n") + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                self._api_id += 1
                finding = Vulnerability(
                    id=f"API-{self._api_id:04d}",
                    name="CORS配置问题",
                    category=VulnerabilityCategory.SECURITY_MISCONFIGURATION,
                    severity=severity,
                    description="CORS配置可能过于宽松",
                    location=str(file_path),
                    line_number=line_num,
                    code_snippet=line_content.strip()[:100],
                    recommendation="限制CORS允许的来源",
                    cwe="CWE-942",
                    owasp="A05:2021",
                    confidence=0.75,
                    tags=["api-security", "cors"]
                )
                self.findings.append(finding)
    
    def _check_jwt(self, file_path: Path, content: str, lines: List[str]):
        patterns = self.API_SECURITY_PATTERNS["jwt"]
        
        for pattern, issue_type, severity in patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count("\n") + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                self._api_id += 1
                finding = Vulnerability(
                    id=f"API-{self._api_id:04d}",
                    name="JWT安全问题",
                    category=VulnerabilityCategory.AUTHENTICATION,
                    severity=severity,
                    description="JWT配置存在安全问题",
                    location=str(file_path),
                    line_number=line_num,
                    code_snippet=line_content.strip()[:100],
                    recommendation="使用安全的JWT配置，避免none算法，启用签名验证",
                    cwe="CWE-327",
                    owasp="A07:2021",
                    confidence=0.9,
                    tags=["api-security", "jwt"]
                )
                self.findings.append(finding)
    
    def _check_sensitive_endpoints(self, file_path: Path, content: str, lines: List[str]):
        for endpoint in self.SENSITIVE_ENDPOINTS:
            if endpoint in content:
                route_pattern = rf'@app\.route\s*\(["\']({re.escape(endpoint)}[^"\']*)["\']'
                for match in re.finditer(route_pattern, content):
                    line_num = content[:match.start()].count("\n") + 1
                    
                    self._api_id += 1
                    finding = Vulnerability(
                        id=f"API-{self._api_id:04d}",
                        name="敏感API端点",
                        category=VulnerabilityCategory.BROKEN_ACCESS_CONTROL,
                        severity=Severity.INFO,
                        description=f"发现敏感端点: {match.group(1)}",
                        location=str(file_path),
                        line_number=line_num,
                        code_snippet=f"Endpoint: {match.group(1)}",
                        recommendation="确保敏感端点有适当的保护措施",
                        confidence=0.9,
                        tags=["api-security", "sensitive-endpoint"]
                    )
                    self.findings.append(finding)
    
    def _is_sensitive_endpoint(self, endpoint: str) -> bool:
        sensitive_patterns = [
            "/admin", "/delete", "/create", "/update", "/user",
            "/account", "/password", "/auth", "/token", "/api"
        ]
        return any(pattern in endpoint.lower() for pattern in sensitive_patterns)


class DataFlowAnalyzer:
    """
    数据流分析器
    执行污点追踪和数据流分析
    """
    
    TAINT_SOURCES = {
        "request.args": {"type": "query_param", "severity": Severity.MEDIUM},
        "request.form": {"type": "form_data", "severity": Severity.MEDIUM},
        "request.json": {"type": "json_data", "severity": Severity.MEDIUM},
        "request.data": {"type": "raw_data", "severity": Severity.HIGH},
        "request.files": {"type": "file_upload", "severity": Severity.HIGH},
        "request.cookies": {"type": "cookie", "severity": Severity.MEDIUM},
        "request.headers": {"type": "header", "severity": Severity.MEDIUM},
        "input()": {"type": "user_input", "severity": Severity.HIGH},
        "sys.argv": {"type": "command_line", "severity": Severity.MEDIUM},
    }
    
    TAINT_SINKS = {
        "cursor.execute": {"type": "sql", "severity": Severity.CRITICAL},
        "connection.execute": {"type": "sql", "severity": Severity.CRITICAL},
        "subprocess.run": {"type": "command", "severity": Severity.CRITICAL},
        "subprocess.call": {"type": "command", "severity": Severity.CRITICAL},
        "os.system": {"type": "command", "severity": Severity.CRITICAL},
        "os.popen": {"type": "command", "severity": Severity.CRITICAL},
        "eval": {"type": "code", "severity": Severity.CRITICAL},
        "exec": {"type": "code", "severity": Severity.CRITICAL},
        "open": {"type": "file", "severity": Severity.HIGH},
        "pickle.loads": {"type": "deserialize", "severity": Severity.CRITICAL},
        "yaml.load": {"type": "deserialize", "severity": Severity.HIGH},
        "requests.get": {"type": "http", "severity": Severity.MEDIUM},
        "requests.post": {"type": "http", "severity": Severity.MEDIUM},
    }
    
    SANITIZERS = {
        "escape": {"for_sinks": ["html", "xss"]},
        "quote": {"for_sinks": ["command", "sql"]},
        "sanitize": {"for_sinks": ["sql", "html", "command"]},
        "validate": {"for_sinks": ["all"]},
        "clean": {"for_sinks": ["all"]},
        "parameterize": {"for_sinks": ["sql"]},
    }
    
    def __init__(self, config: SecurityScanConfig):
        self.config = config
        self.findings: List[Vulnerability] = []
        self.data_flows: List[DataFlowPath] = []
        self._flow_id = 0
    
    def analyze_file(self, file_path: Path) -> List[DataFlowPath]:
        self.data_flows = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            self._analyze_data_flow(file_path, content)
            
        except Exception as e:
            print(f"数据流分析失败 {file_path}: {e}")
        
        return self.data_flows
    
    def scan_directory(self, directory: Path) -> List[Vulnerability]:
        self.findings = []
        
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            flows = self.analyze_file(py_file)
            for flow in flows:
                if not flow.sanitized:
                    self._create_vulnerability(flow)
        
        return self.findings
    
    def _should_skip_file(self, file_path: Path) -> bool:
        return any(pattern in str(file_path) for pattern in self.config.exclude_patterns)
    
    def _analyze_data_flow(self, file_path: Path, content: str):
        lines = content.split("\n")
        
        source_pattern = r'(' + '|'.join(re.escape(s) for s in self.TAINT_SOURCES.keys()) + r')'
        sink_pattern = r'(' + '|'.join(re.escape(s) for s in self.TAINT_SINKS.keys()) + r')'
        
        source_matches = list(re.finditer(source_pattern, content))
        sink_matches = list(re.finditer(sink_pattern, content))
        
        for source_match in source_matches:
            source_name = source_match.group(1)
            source_line = content[:source_match.start()].count("\n") + 1
            source_info = self.TAINT_SOURCES.get(source_name, {})
            
            taint_source = TaintSource(
                name=source_name,
                source_type=source_info.get("type", "unknown"),
                location=str(file_path),
                line_number=source_line,
                description=f"用户输入源: {source_name}"
            )
            
            for sink_match in sink_matches:
                sink_name = sink_match.group(1)
                sink_line = content[:sink_match.start()].count("\n") + 1
                sink_info = self.TAINT_SINKS.get(sink_name, {})
                
                if sink_line < source_line:
                    continue
                
                taint_sink = TaintSink(
                    name=sink_name,
                    sink_type=sink_info.get("type", "unknown"),
                    location=str(file_path),
                    line_number=sink_line,
                    description=f"危险汇点: {sink_name}"
                )
                
                path = self._trace_path(content, source_line, sink_line)
                sanitized = self._check_sanitization(content, source_line, sink_line)
                
                flow = DataFlowPath(
                    source=taint_source,
                    sink=taint_sink,
                    path=path,
                    vulnerability_type=f"{taint_source.source_type}_to_{taint_sink.sink_type}",
                    sanitized=sanitized
                )
                self.data_flows.append(flow)
    
    def _trace_path(self, content: str, start_line: int, end_line: int) -> List[Tuple[str, int]]:
        lines = content.split("\n")
        path = []
        
        for i in range(start_line - 1, min(end_line, len(lines))):
            line = lines[i].strip()
            if line and not line.startswith("#"):
                path.append((line[:80], i + 1))
        
        return path
    
    def _check_sanitization(self, content: str, start_line: int, end_line: int) -> bool:
        lines = content.split("\n")
        
        for i in range(start_line - 1, min(end_line, len(lines))):
            line = lines[i].lower()
            for sanitizer in self.SANITIZERS.keys():
                if sanitizer in line:
                    return True
        
        return False
    
    def _create_vulnerability(self, flow: DataFlowPath):
        self._flow_id += 1
        
        severity = self.TAINT_SINKS.get(flow.sink.name, {}).get("severity", Severity.MEDIUM)
        
        finding = Vulnerability(
            id=f"DATAFLOW-{self._flow_id:04d}",
            name=f"数据流漏洞: {flow.source.name} -> {flow.sink.name}",
            category=VulnerabilityCategory.INJECTION,
            severity=severity,
            description=f"检测到从 {flow.source.source_type} 到 {flow.sink.sink_type} 的不安全数据流",
            location=flow.source.location,
            line_number=flow.source.line_number,
            code_snippet=f"Source: {flow.source.name}, Sink: {flow.sink.name}",
            recommendation=self._get_flow_recommendation(flow),
            cwe="CWE-89",
            owasp="A03:2021",
            confidence=0.85,
            impact="可能导致注入攻击",
            likelihood="高",
            tags=["dataflow", "taint-analysis"]
        )
        self.findings.append(finding)
    
    def _get_flow_recommendation(self, flow: DataFlowPath) -> str:
        sink_type = flow.sink.sink_type
        
        recommendations = {
            "sql": "使用参数化查询，避免直接拼接用户输入",
            "command": "避免shell=True，使用参数列表形式",
            "code": "禁止执行用户输入的代码",
            "file": "验证文件路径，使用白名单限制",
            "deserialize": "使用JSON等安全格式，避免pickle",
            "http": "验证URL，限制请求目标",
        }
        
        return recommendations.get(sink_type, "对用户输入进行验证和清理")


class OWASPScanner:
    OWASP_TOP_10 = {
        "A01:2021": {
            "name": "Broken Access Control",
            "checks": ["@login_required", "@permission_required", "authorize"]
        },
        "A02:2021": {
            "name": "Cryptographic Failures",
            "checks": ["https://", "ssl", "tls", "encrypt", "decrypt"]
        },
        "A03:2021": {
            "name": "Injection",
            "checks": ["parameterized", "prepared statement", "orm"]
        },
        "A04:2021": {
            "name": "Insecure Design",
            "checks": ["rate_limit", "throttle", "validation"]
        },
        "A05:2021": {
            "name": "Security Misconfiguration",
            "checks": ["DEBUG = False", "SECRET_KEY", "ALLOWED_HOSTS"]
        },
        "A06:2021": {
            "name": "Vulnerable Components",
            "checks": ["requirements.txt", "package.json"]
        },
        "A07:2021": {
            "name": "Authentication Failures",
            "checks": ["password_hash", "bcrypt", "argon2", "mfa"]
        },
        "A08:2021": {
            "name": "Software and Data Integrity Failures",
            "checks": ["signature", "verify", "checksum"]
        },
        "A09:2021": {
            "name": "Security Logging and Monitoring Failures",
            "checks": ["logging", "audit", "monitor"]
        },
        "A10:2021": {
            "name": "Server-Side Request Forgery",
            "checks": ["url_validation", "whitelist", "internal"]
        }
    }

    def __init__(self, config: SecurityScanConfig):
        self.config = config
        self.findings: List[SecurityFinding] = []

    def scan_directory(self, directory: Path) -> List[SecurityFinding]:
        self.findings = []
        
        for code in self.OWASP_TOP_10:
            finding = SecurityFinding(
                title=f"OWASP {code}: {self.OWASP_TOP_10[code]['name']}",
                category=VulnerabilityCategory.SECURITY_MISCONFIGURATION,
                severity=Severity.INFO,
                description=f"检查 {self.OWASP_TOP_10[code]['name']} 相关的安全配置",
                impact="可能导致安全漏洞",
                remediation=f"确保遵循 {code} 的最佳实践",
                references=[f"https://owasp.org/Top10/{code}/"]
            )
            self.findings.append(finding)
        
        return self.findings


class HTMLReportGenerator:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def generate(
        self,
        results: List[ScanResult],
        output_path: str
    ) -> str:
        html_content = self._generate_html(results)
        
        full_output_path = Path(self.base_path) / output_path
        full_output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return str(full_output_path)

    def _generate_html(self, results: List[ScanResult]) -> str:
        total_vulns = sum(len(r.vulnerabilities) for r in results)
        total_deps = sum(len(r.dependency_vulnerabilities) for r in results)
        
        critical = sum(1 for r in results for v in r.vulnerabilities if v.severity == Severity.CRITICAL)
        high = sum(1 for r in results for v in r.vulnerabilities if v.severity == Severity.HIGH)
        medium = sum(1 for r in results for v in r.vulnerabilities if v.severity == Severity.MEDIUM)
        low = sum(1 for r in results for v in r.vulnerabilities if v.severity == Severity.LOW)
        
        vulns_html = self._generate_vulns_table(results)
        deps_html = self._generate_deps_table(results)

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>安全扫描报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; margin-bottom: 20px; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .card h3 {{ color: #333; margin-bottom: 15px; font-size: 14px; text-transform: uppercase; }}
        .card .value {{ font-size: 32px; font-weight: bold; color: #ef4444; }}
        .card .label {{ color: #666; font-size: 12px; margin-top: 5px; }}
        .section {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #ef4444; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #333; }}
        .severity-critical {{ color: #ef4444; font-weight: bold; }}
        .severity-high {{ color: #f97316; font-weight: bold; }}
        .severity-medium {{ color: #f59e0b; }}
        .severity-low {{ color: #6b7280; }}
        .severity-info {{ color: #3b82f6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 安全扫描报告</h1>
            <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div class="summary">
            <div class="card">
                <h3>总漏洞数</h3>
                <div class="value">{total_vulns + total_deps}</div>
                <div class="label">漏洞</div>
            </div>
            <div class="card">
                <h3>严重</h3>
                <div class="value" style="color: #ef4444;">{critical}</div>
                <div class="label">Critical</div>
            </div>
            <div class="card">
                <h3>高危</h3>
                <div class="value" style="color: #f97316;">{high}</div>
                <div class="label">High</div>
            </div>
            <div class="card">
                <h3>中危</h3>
                <div class="value" style="color: #f59e0b;">{medium}</div>
                <div class="label">Medium</div>
            </div>
            <div class="card">
                <h3>低危</h3>
                <div class="value" style="color: #6b7280;">{low}</div>
                <div class="label">Low</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🛡️ 代码漏洞</h2>
            {vulns_html}
        </div>
        
        <div class="section">
            <h2>📦 依赖漏洞</h2>
            {deps_html}
        </div>
    </div>
</body>
</html>'''

    def _generate_vulns_table(self, results: List[ScanResult]) -> str:
        rows = ""
        for r in results:
            for v in r.vulnerabilities:
                severity_class = f"severity-{v.severity.value}"
                rows += f'''
                <tr>
                    <td>{v.name}</td>
                    <td>{v.category.value}</td>
                    <td class="{severity_class}">{v.severity.value}</td>
                    <td>{v.location}:{v.line_number or '-'}</td>
                    <td>{v.recommendation[:50]}...</td>
                </tr>'''
        
        if not rows:
            return "<p>未发现代码漏洞</p>"
        
        return f'''<table>
            <thead>
                <tr>
                    <th>漏洞名称</th>
                    <th>类别</th>
                    <th>严重程度</th>
                    <th>位置</th>
                    <th>建议</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>'''

    def _generate_deps_table(self, results: List[ScanResult]) -> str:
        rows = ""
        for r in results:
            for d in r.dependency_vulnerabilities:
                severity_class = f"severity-{d.severity.value}"
                rows += f'''
                <tr>
                    <td>{d.package_name}</td>
                    <td>{d.installed_version}</td>
                    <td>{d.fixed_version}</td>
                    <td class="{severity_class}">{d.severity.value}</td>
                    <td>{d.cve_id or d.advisory_id}</td>
                </tr>'''
        
        if not rows:
            return "<p>未发现依赖漏洞</p>"
        
        return f'''<table>
            <thead>
                <tr>
                    <th>包名</th>
                    <th>当前版本</th>
                    <th>修复版本</th>
                    <th>严重程度</th>
                    <th>CVE/Advisory</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>'''


class SecurityScanReporter:
    def __init__(self, base_path: str, config: SecurityScanConfig):
        self.base_path = base_path
        self.config = config
        self.html_generator = HTMLReportGenerator(base_path)

    def generate_report(
        self,
        results: List[ScanResult],
        output_path: str
    ) -> Dict[str, Any]:
        total_vulns = sum(len(r.vulnerabilities) for r in results)
        total_deps = sum(len(r.dependency_vulnerabilities) for r in results)
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "config": {
                "source_dirs": self.config.source_dirs,
                "check_dependencies": self.config.check_dependencies,
                "check_secrets": self.config.check_secrets,
                "check_owasp": self.config.check_owasp
            },
            "summary": {
                "total_vulnerabilities": total_vulns,
                "total_dependency_vulnerabilities": total_deps,
                "critical": sum(1 for r in results for v in r.vulnerabilities if v.severity == Severity.CRITICAL),
                "high": sum(1 for r in results for v in r.vulnerabilities if v.severity == Severity.HIGH),
                "medium": sum(1 for r in results for v in r.vulnerabilities if v.severity == Severity.MEDIUM),
                "low": sum(1 for r in results for v in r.vulnerabilities if v.severity == Severity.LOW),
                "scan_duration": round(sum(r.duration for r in results), 2)
            },
            "scan_results": [
                {
                    "scan_name": r.scan_name,
                    "status": r.status.value,
                    "duration": round(r.duration, 4),
                    "vulnerabilities": [
                        {
                            "id": v.id,
                            "name": v.name,
                            "category": v.category.value,
                            "severity": v.severity.value,
                            "description": v.description,
                            "location": v.location,
                            "line_number": v.line_number,
                            "recommendation": v.recommendation,
                            "cwe": v.cwe,
                            "owasp": v.owasp
                        }
                        for v in r.vulnerabilities
                    ],
                    "dependency_vulnerabilities": [
                        {
                            "package_name": d.package_name,
                            "installed_version": d.installed_version,
                            "fixed_version": d.fixed_version,
                            "severity": d.severity.value,
                            "cve_id": d.cve_id
                        }
                        for d in r.dependency_vulnerabilities
                    ],
                    "error": r.error
                }
                for r in results
            ],
            "recommendations": self._generate_recommendations(results),
            "compliance": self._check_compliance(results)
        }

        full_output_path = Path(self.base_path) / output_path
        full_output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        if "html" in self.config.output_formats:
            html_path = str(full_output_path).replace(".json", ".html")
            self.html_generator.generate(results, html_path)

        return report

    def _generate_recommendations(self, results: List[ScanResult]) -> List[str]:
        recommendations = []
        
        critical = sum(1 for r in results for v in r.vulnerabilities if v.severity == Severity.CRITICAL)
        if critical > 0:
            recommendations.append(f"发现 {critical} 个严重漏洞，请立即修复")
        
        high = sum(1 for r in results for v in r.vulnerabilities if v.severity == Severity.HIGH)
        if high > 0:
            recommendations.append(f"发现 {high} 个高危漏洞，建议优先处理")
        
        secrets = sum(1 for r in results for v in r.vulnerabilities if v.category == VulnerabilityCategory.HARDCODED_SECRETS)
        if secrets > 0:
            recommendations.append(f"发现 {secrets} 处硬编码敏感信息，请使用环境变量")
        
        deps = sum(len(r.dependency_vulnerabilities) for r in results)
        if deps > 0:
            recommendations.append(f"发现 {deps} 个依赖漏洞，请更新依赖版本")
        
        if not recommendations:
            recommendations.append("未发现安全漏洞，继续保持")
        
        recommendations.extend([
            "建议定期运行安全扫描",
            "保持依赖版本更新",
            "遵循OWASP安全最佳实践"
        ])
        
        return recommendations

    def _check_compliance(self, results: List[ScanResult]) -> Dict[str, Any]:
        return {
            "owasp_top_10": {
                "passed": sum(1 for r in results for v in r.vulnerabilities if v.owasp) == 0,
                "issues": sum(1 for r in results for v in r.vulnerabilities if v.owasp)
            },
            "no_critical_vulns": {
                "passed": sum(1 for r in results for v in r.vulnerabilities if v.severity == Severity.CRITICAL) == 0
            },
            "no_hardcoded_secrets": {
                "passed": sum(1 for r in results for v in r.vulnerabilities if v.category == VulnerabilityCategory.HARDCODED_SECRETS) == 0
            }
        }

    def print_report(self, report: Dict[str, Any]):
        print("\n" + "=" * 80)
        print("安全扫描报告")
        print("=" * 80)
        
        summary = report["summary"]
        print(f"\n扫描摘要:")
        print(f"  总漏洞数: {summary['total_vulnerabilities']}")
        print(f"  依赖漏洞: {summary['total_dependency_vulnerabilities']}")
        print(f"  严重: {summary['critical']}")
        print(f"  高危: {summary['high']}")
        print(f"  中危: {summary['medium']}")
        print(f"  低危: {summary['low']}")
        print(f"  扫描耗时: {summary['scan_duration']}s")
        
        print(f"\n建议:")
        for i, rec in enumerate(report["recommendations"][:5], 1):
            print(f"  {i}. {rec}")


class SecurityScanner:
    def __init__(self, base_path: str, config: Optional[SecurityScanConfig] = None):
        self.base_path = base_path
        self.config = config or SecurityScanConfig()
        self.secret_scanner = SecretScanner(self.config)
        self.injection_scanner = InjectionScanner(self.config)
        self.xss_scanner = XSSScanner(self.config)
        self.auth_scanner = AuthScanner(self.config)
        self.crypto_scanner = CryptoScanner(self.config)
        self.dependency_scanner = DependencyScanner(self.config)
        self.owasp_scanner = OWASPScanner(self.config)
        self.vulnerability_detector = VulnerabilityDetector(self.config)
        self.fix_generator = SecurityFixGenerator()
        self.reporter = SecurityScanReporter(base_path, self.config)

    def scan(
        self,
        output_path: str = "docs/reports/security_scan.json",
        generate_fixes: bool = True
    ) -> Dict[str, Any]:
        print("=" * 60)
        print("安全扫描智能增强分析")
        print("=" * 60)
        
        results = []
        start_time = time.time()
        
        for source_dir in self.config.source_dirs:
            source_path = Path(self.base_path) / source_dir
            if not source_path.exists():
                continue
            
            print(f"\n扫描目录: {source_dir}")
            
            if self.config.check_secrets:
                print("  - 扫描敏感信息...")
                secrets = self.secret_scanner.scan_directory(source_path)
                print(f"    发现 {len(secrets)} 处敏感信息")
            
            if self.config.check_injection:
                print("  - 扫描注入漏洞...")
                injections = self.injection_scanner.scan_directory(source_path)
                print(f"    发现 {len(injections)} 处注入风险")
            
            if self.config.check_xss:
                print("  - 扫描XSS漏洞...")
                xss = self.xss_scanner.scan_directory(source_path)
                print(f"    发现 {len(xss)} 处XSS风险")
            
            if self.config.check_auth:
                print("  - 扫描认证问题...")
                auth = self.auth_scanner.scan_directory(source_path)
                print(f"    发现 {len(auth)} 处认证问题")
            
            if self.config.check_crypto:
                print("  - 扫描加密问题...")
                crypto = self.crypto_scanner.scan_directory(source_path)
                print(f"    发现 {len(crypto)} 处加密问题")
            
            print("  - 运行高级漏洞检测...")
            advanced_vulns = self.vulnerability_detector.scan_directory(source_path)
            print(f"    发现 {len(advanced_vulns)} 个高级漏洞")
            
            all_vulns = (
                self.secret_scanner.findings +
                self.injection_scanner.findings +
                self.xss_scanner.findings +
                self.auth_scanner.findings +
                self.crypto_scanner.findings +
                advanced_vulns
            )
            
            result = ScanResult(
                scan_name=f"scan_{source_dir.replace('/', '_')}",
                status=ScanStatus.COMPLETED,
                duration=0,
                vulnerabilities=all_vulns
            )
            results.append(result)
        
        if self.config.check_dependencies:
            print("\n扫描依赖漏洞...")
            py_deps = self.dependency_scanner.scan_python_dependencies()
            node_deps = self.dependency_scanner.scan_node_dependencies()
            
            dep_result = ScanResult(
                scan_name="dependency_scan",
                status=ScanStatus.COMPLETED,
                duration=0,
                dependency_vulnerabilities=py_deps + node_deps
            )
            results.append(dep_result)
            print(f"  发现 {len(py_deps) + len(node_deps)} 个依赖漏洞")
        
        if self.config.check_owasp:
            print("\n检查OWASP Top 10...")
            owasp_findings = self.owasp_scanner.scan_directory(Path(self.base_path))
            
            owasp_result = ScanResult(
                scan_name="owasp_scan",
                status=ScanStatus.COMPLETED,
                duration=0,
                findings=owasp_findings
            )
            results.append(owasp_result)
        
        all_vulnerabilities = [
            v for r in results for v in r.vulnerabilities
        ]
        
        fix_report = None
        if generate_fixes and all_vulnerabilities:
            print("\n生成安全修复建议...")
            fix_report = self.fix_generator.generate_fix_report(all_vulnerabilities)
            print(f"  生成 {fix_report['total_fixes']} 条修复建议")
        
        print("\n生成安全报告...")
        report = self.reporter.generate_report(results, output_path)
        
        if fix_report:
            report["fix_report"] = fix_report
        
        scan_duration = time.time() - start_time
        report["scan_duration"] = round(scan_duration, 2)
        
        self.reporter.print_report(report)
        
        return report

    def scan_file(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            return {"error": f"文件不存在: {file_path}"}
        
        vulnerabilities = []
        
        if path.suffix == ".py":
            content = path.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            for pattern, secret_type, severity in SecretScanner.SECRET_PATTERNS:
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count("\n") + 1
                    vulnerabilities.append({
                        "type": "hardcoded_secret",
                        "secret_type": secret_type,
                        "severity": severity.value,
                        "line": line_num,
                        "code": lines[line_num - 1].strip()[:80]
                    })
            
            for vuln_type, vuln_info in VulnerabilityDetector.VULNERABILITY_SIGNATURES.items():
                for pattern_info in vuln_info["patterns"]:
                    if len(pattern_info) == 3:
                        pattern, desc, is_vuln = pattern_info
                        if not is_vuln:
                            continue
                    else:
                        pattern, desc = pattern_info
                    
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        line_num = content[:match.start()].count("\n") + 1
                        vulnerabilities.append({
                            "type": vuln_type,
                            "description": desc,
                            "severity": vuln_info["severity"].value,
                            "line": line_num,
                            "code": lines[line_num - 1].strip()[:80],
                            "cwe": vuln_info["cwe"],
                            "owasp": vuln_info["owasp"]
                        })
        
        return {
            "file": file_path,
            "vulnerabilities": vulnerabilities,
            "total": len(vulnerabilities),
            "critical": len([v for v in vulnerabilities if v.get("severity") == "critical"]),
            "high": len([v for v in vulnerabilities if v.get("severity") == "high"]),
            "medium": len([v for v in vulnerabilities if v.get("severity") == "medium"]),
            "low": len([v for v in vulnerabilities if v.get("severity") == "low"])
        }

    def get_fix_suggestion(self, vulnerability_id: str) -> Optional[Dict[str, Any]]:
        for fix in self.fix_generator.fixes:
            if fix["vulnerability_id"] == vulnerability_id:
                return fix
        return None

    def quick_scan(self, directory: str) -> Dict[str, Any]:
        dir_path = Path(directory)
        if not dir_path.exists():
            return {"error": f"目录不存在: {directory}"}
        
        quick_findings = []
        
        for py_file in dir_path.rglob("*.py"):
            if any(p in str(py_file) for p in self.config.exclude_patterns):
                continue
            
            file_result = self.scan_file(str(py_file))
            if file_result.get("vulnerabilities"):
                quick_findings.append({
                    "file": str(py_file),
                    "vulnerabilities": file_result["vulnerabilities"],
                    "total": file_result["total"]
                })
        
        return {
            "directory": directory,
            "files_scanned": len(quick_findings),
            "total_vulnerabilities": sum(f["total"] for f in quick_findings),
            "findings": quick_findings
        }


def main():
    parser = argparse.ArgumentParser(description="安全扫描智能增强")
    parser.add_argument(
        "--config",
        help="配置文件路径 (YAML/JSON)"
    )
    parser.add_argument(
        "--source-dirs",
        nargs="+",
        help="源代码目录"
    )
    parser.add_argument(
        "--output",
        default="docs/reports/security_scan.json",
        help="输出报告路径"
    )
    parser.add_argument(
        "--generate-config",
        action="store_true",
        help="生成配置文件模板"
    )
    parser.add_argument(
        "--no-deps",
        action="store_true",
        help="跳过依赖检查"
    )
    parser.add_argument(
        "--no-secrets",
        action="store_true",
        help="跳过敏感信息检查"
    )
    
    args = parser.parse_args()
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    config_loader = ConfigLoader(base_path)
    
    if args.generate_config:
        config_loader.save_template("security_scan_config.yaml")
        print("配置文件模板已生成: security_scan_config.yaml")
        return 0
    
    config = config_loader.load(args.config)
    
    if args.source_dirs:
        config.source_dirs = args.source_dirs
    if args.no_deps:
        config.check_dependencies = False
    if args.no_secrets:
        config.check_secrets = False
    
    scanner = SecurityScanner(base_path, config)
    report = scanner.scan(args.output)
    
    if config.fail_on_critical and report["summary"]["critical"] > 0:
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
