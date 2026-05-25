from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import SCRIPTS_DIR
from ..core.errors import ERR_VALIDATION, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.subprocess_utils import run_script
from ..core.validator import validate_input, validate_path_safety
from ..models.schemas import SecurityScanInput

logger = get_logger("security_scan")

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

_SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".java", ".go"}

_VULNERABILITY_PATTERNS: list[dict[str, Any]] = [
    {
        "type": "hardcoded_secret",
        "severity": "critical",
        "pattern": re.compile(
            r'(?:api_key|apikey|api_secret|password|passwd|secret|token|auth_token|access_key|secret_key|private_key)\s*=\s*["\'][^"\']+["\']',
            re.IGNORECASE,
        ),
        "description": "Hardcoded secret detected: credentials should not be embedded in source code",
        "cwe_id": "CWE-798",
        "cwe_url": "https://cwe.mitre.org/data/definitions/798.html",
        "remediation": "Use environment variables or a secrets manager (e.g., os.environ, python-decouple, vault)",
    },
    {
        "type": "eval_exec",
        "severity": "critical",
        "pattern": re.compile(r'\b(?:eval|exec)\s*\(', re.IGNORECASE),
        "description": "Use of eval/exec detected: these functions can execute arbitrary code",
        "cwe_id": "CWE-94",
        "cwe_url": "https://cwe.mitre.org/data/definitions/94.html",
        "remediation": "Use ast.literal_eval() for safe evaluation, or refactor to avoid dynamic code execution",
    },
    {
        "type": "sql_injection",
        "severity": "high",
        "pattern": re.compile(
            r'(?:f["\'](?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE).*?\{|(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE).*?\.\s*format\s*\()',
            re.IGNORECASE,
        ),
        "description": "Potential SQL injection: string formatting used in SQL query context",
        "cwe_id": "CWE-89",
        "cwe_url": "https://cwe.mitre.org/data/definitions/89.html",
        "remediation": "Use parameterized queries with placeholders (e.g., cursor.execute('SELECT ? FROM ?', (val,)))",
    },
    {
        "type": "unsafe_deserialization",
        "severity": "high",
        "pattern": re.compile(r'\b(?:pickle\.load|yaml\.load)\s*\(', re.IGNORECASE),
        "description": "Unsafe deserialization: pickle.load or yaml.load without SafeLoader can execute arbitrary code",
        "cwe_id": "CWE-502",
        "cwe_url": "https://cwe.mitre.org/data/definitions/502.html",
        "remediation": "Use yaml.safe_load() instead of yaml.load(), and avoid pickle for untrusted data",
    },
    {
        "type": "xss",
        "severity": "medium",
        "pattern": re.compile(r'(?:innerHTML|document\.write|v-html)\s*[=(]', re.IGNORECASE),
        "description": "Potential XSS: dynamic content inserted via innerHTML, document.write, or v-html",
        "cwe_id": "CWE-79",
        "cwe_url": "https://cwe.mitre.org/data/definitions/79.html",
        "remediation": "Use textContent instead of innerHTML, or sanitize HTML with DOMPurify before insertion",
    },
    {
        "type": "unsafe_shell",
        "severity": "medium",
        "pattern": re.compile(r'(?:os\.system|subprocess\.(?:call|run|Popen))\s*\(', re.IGNORECASE),
        "description": "Unsafe shell operation: os.system or subprocess call detected",
        "cwe_id": "CWE-78",
        "cwe_url": "https://cwe.mitre.org/data/definitions/78.html",
        "remediation": "Use subprocess.run with shell=False and pass arguments as a list",
    },
]

_KNOWN_VULNERABLE_DEPS = [
    {"name": "Flask", "max_version": "2.0", "reason": "Flask < 2.0 has known security vulnerabilities"},
    {"name": "Django", "max_version": "3.2", "reason": "Django < 3.2 has known security vulnerabilities"},
    {"name": "requests", "max_version": "2.25", "reason": "requests < 2.25 has known security vulnerabilities"},
    {"name": "PyYAML", "max_version": "5.4", "reason": "PyYAML < 5.4 has known security vulnerabilities"},
    {"name": "pyyaml", "max_version": "5.4", "reason": "PyYAML < 5.4 has known security vulnerabilities"},
]

_SEVERITY_WEIGHTS = {"critical": 25, "high": 15, "medium": 8, "low": 3}


def _is_likely_false_positive(vuln_type: str, line: str, context_lines: list[str]) -> bool:
    if vuln_type == "hardcoded_secret":
        env_patterns = ["os.environ", "os.getenv", "environ.get", "ENV[", "config(", "settings."]
        for pattern in env_patterns:
            if pattern in line:
                return True
        for ctx in context_lines:
            if pattern in ctx:
                return True
    if vuln_type == "unsafe_shell":
        safe_patterns = ["shell=False", "check=True"]
        for pattern in safe_patterns:
            if pattern in line:
                return True
    return False


def _calculate_security_score(vulnerabilities: list[dict[str, Any]]) -> int:
    if not vulnerabilities:
        return 100
    total_deduction = 0
    for v in vulnerabilities:
        if v.get("likely_false_positive"):
            continue
        sev = v.get("severity", "low")
        total_deduction += _SEVERITY_WEIGHTS.get(sev, 3)
    score = max(0, 100 - total_deduction)
    return score


def _parse_version(version_str: str) -> tuple[int, ...]:
    parts = []
    for part in version_str.replace("v", "").split("."):
        try:
            parts.append(int(part))
        except ValueError:
            break
    return tuple(parts)


def _inline_agentic_scan(target: str, severity_threshold: str) -> dict[str, Any]:
    target_path = Path(target).resolve()
    if not target_path.exists():
        return {
            "vulnerabilities": [],
            "total": 0,
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        }

    threshold_level = _SEVERITY_ORDER.get(severity_threshold, 2)
    vulnerabilities = []

    source_files = []
    if target_path.is_file():
        if target_path.suffix in _SOURCE_EXTENSIONS:
            source_files.append(target_path)
    else:
        for ext in _SOURCE_EXTENSIONS:
            source_files.extend(target_path.rglob(f"*{ext}"))

    for file_path in source_files:
        try:
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue

        rel_path = str(file_path.relative_to(target_path)) if target_path.is_dir() else file_path.name

        for line_num, line in enumerate(lines, start=1):
            for vuln_def in _VULNERABILITY_PATTERNS:
                match = vuln_def["pattern"].search(line)
                if match:
                    vuln_severity = vuln_def["severity"]
                    context = lines[max(0, line_num - 2):line_num + 1]
                    likely_fp = _is_likely_false_positive(vuln_def["type"], line, context)
                    effective_severity = "low" if likely_fp else vuln_severity
                    if _SEVERITY_ORDER.get(effective_severity, 3) > threshold_level:
                        continue
                    vulnerabilities.append({
                        "type": vuln_def["type"],
                        "severity": effective_severity,
                        "file": rel_path,
                        "line": line_num,
                        "pattern": match.group(0),
                        "description": vuln_def["description"],
                        "cwe_id": vuln_def.get("cwe_id", ""),
                        "cwe_url": vuln_def.get("cwe_url", ""),
                        "remediation": vuln_def.get("remediation", ""),
                        "likely_false_positive": likely_fp,
                    })

    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for v in vulnerabilities:
        sev = v["severity"]
        if sev in by_severity:
            by_severity[sev] += 1

    security_score = _calculate_security_score(vulnerabilities)
    return {
        "vulnerabilities": vulnerabilities,
        "total": len(vulnerabilities),
        "by_severity": by_severity,
        "security_score": security_score,
    }


def _inline_dependency_scan(target: str) -> dict[str, Any]:
    target_path = Path(target).resolve()
    dependencies = []

    req_file = target_path / "requirements.txt" if target_path.is_dir() else target_path / "../requirements.txt"
    if req_file.exists():
        try:
            lines = req_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                matched = False
                for op in [">=", "<=", "!=", "~=", "==", ">", "<"]:
                    idx = line.find(op)
                    if idx != -1:
                        name = line[:idx].strip()
                        version = line[idx + len(op):].strip()
                        status = "ok"
                        reason = ""
                        for vuln_dep in _KNOWN_VULNERABLE_DEPS:
                            if name.lower() == vuln_dep["name"].lower():
                                max_v = _parse_version(vuln_dep["max_version"])
                                cur_v = _parse_version(version)
                                if cur_v < max_v:
                                    status = "potentially_vulnerable"
                                    reason = vuln_dep["reason"]
                                break
                        dependencies.append({
                            "name": name,
                            "version": version,
                            "status": status,
                            "reason": reason,
                        })
                        matched = True
                        break
                if not matched:
                    dependencies.append({
                        "name": line,
                        "version": "unknown",
                        "status": "ok",
                        "reason": "",
                    })
        except (OSError, PermissionError):
            pass

    pkg_file = target_path / "package.json" if target_path.is_dir() else target_path / "../package.json"
    if pkg_file.exists():
        try:
            import json
            data = json.loads(pkg_file.read_text(encoding="utf-8", errors="ignore"))
            for dep_section in ["dependencies", "devDependencies"]:
                for name, version in data.get(dep_section, {}).items():
                    clean_version = version.lstrip("^~>=<")
                    dependencies.append({
                        "name": name,
                        "version": clean_version,
                        "status": "ok",
                        "reason": "",
                    })
        except (OSError, PermissionError, json.JSONDecodeError):
            pass

    vulnerable_count = sum(1 for d in dependencies if d["status"] == "potentially_vulnerable")

    return {
        "dependencies": dependencies,
        "total": len(dependencies),
        "vulnerable_count": vulnerable_count,
    }


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=True,
        )
    )
    async def security_scan(
        target: str = ".",
        severity_threshold: str = "medium",
        include_agentic: bool = True,
        include_dependency: bool = True,
    ) -> dict[str, Any]:
        """安全扫描引擎：OWASP Agentic Top 10检查 + 依赖漏洞扫描。支持严重级别过滤(critical/high/medium/low)，返回分类漏洞列表和修复建议。"""
        validated, err = validate_input(SecurityScanInput, target=target, severity_threshold=severity_threshold, include_agentic=include_agentic, include_dependency=include_dependency)
        if err:
            return err
        logger.info("security_scan called: target=%s", target)
        try:
            safe_path, path_err = validate_path_safety(target, allow_absolute=True)
            if path_err:
                return make_error_response(ValueError(path_err), error_code=ERR_VALIDATION)
            results: dict[str, Any] = {}
            degradation_level = "none"

            if include_agentic:
                script_path = SCRIPTS_DIR / "agentic-security-scanner.py"
                used_inline = False
                if script_path.exists():
                    result = run_script(
                        script_path,
                        args=["--target", target, "--severity-threshold", severity_threshold, "--format", "json"],
                        timeout=120,
                    )
                    if result.get("error"):
                        results["agentic_scan"] = _inline_agentic_scan(target, severity_threshold)
                        used_inline = True
                    else:
                        results["agentic_scan"] = result.get("data", result)
                else:
                    results["agentic_scan"] = _inline_agentic_scan(target, severity_threshold)
                    used_inline = True
                if used_inline:
                    logger.warning("security_scan degraded: agentic_scan -> inline")
                    from .server_health import track_degradation
                    track_degradation("security_scan")
                    results["agentic_scan"]["degradation_level"] = "inline"
                    degradation_level = "inline"

            if include_dependency:
                script_path = SCRIPTS_DIR / "dependency-scan.py"
                used_inline = False
                if script_path.exists():
                    result = run_script(
                        script_path,
                        args=["--target", target, "--format", "json"],
                        timeout=60,
                    )
                    if result.get("error"):
                        results["dependency_scan"] = _inline_dependency_scan(target)
                        used_inline = True
                    else:
                        results["dependency_scan"] = result.get("data", result)
                else:
                    results["dependency_scan"] = _inline_dependency_scan(target)
                    used_inline = True
                if used_inline:
                    logger.warning("security_scan degraded: dependency_scan -> inline")
                    from .server_health import track_degradation
                    track_degradation("security_scan")
                    results["dependency_scan"]["degradation_level"] = "inline"
                    degradation_level = "inline"

            return make_success_response(results, degradation_level=degradation_level if degradation_level != "none" else None)
        except Exception as e:
            logger.error("security_scan error: %s", e)
            return make_error_response(e)
