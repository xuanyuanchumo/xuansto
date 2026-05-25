import json
import os
import re
import time as _time
from pathlib import Path

from ..config import make_response, make_error_response, mcp_available
from ._shared import MCP_JSON_SCHEMA_URI, _SEVERITY_ORDER, _scan_dependencies

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_tool_definition():
    if not mcp_available:
        return None
    return Tool(
        name="security_scan",
        description=(
            "[Read-Only] [Idempotent] OWASP Agentic Top 10 + dependency vulnerability scanning.\n\n"
            "Use this tool to scan code for security vulnerabilities including hardcoded secrets, "
            "injection risks, OWASP Top 10 patterns, and dependency vulnerabilities. "
            "Returns findings categorized by severity with remediation suggestions.\n\n"
            "Parameters:\n"
            "- target (string, default='.'): Target directory to scan.\n"
            "- severity_threshold (string, default='medium', enum: critical|high|medium|low): Minimum severity to report.\n"
            "- include_agentic (boolean, default=true): Include OWASP Agentic Top 10 checks.\n"
            "- include_dependency (boolean, default=true): Include dependency vulnerability scanning.\n\n"
            "Returns an object with:\n"
            "- total_findings: Total number of findings.\n"
            "- by_severity: Counts by severity level (critical, high, medium, low).\n"
            "- findings: Array of findings (id, title, severity, category, file, line, description, remediation, references).\n"
            "- agentic_findings: Count of OWASP Agentic findings.\n"
            "- dependency_findings: Count of dependency findings.\n"
            "- scan_duration_ms: Scan duration in milliseconds.\n\n"
            "Example: Scan with high severity threshold:\n"
            '{"target": "src", "severity_threshold": "high"}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target directory to scan", "default": "."},
                "severity_threshold": {"type": "string", "description": "Minimum severity: critical, high, medium, low", "default": "medium", "enum": ["critical", "high", "medium", "low"]},
                "include_agentic": {"type": "boolean", "description": "Include OWASP Agentic Top 10 checks", "default": True},
                "include_dependency": {"type": "boolean", "description": "Include dependency vulnerability scanning", "default": True},
            },
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "total_findings": {"type": "integer"},
                "by_severity": {"type": "object", "properties": {"critical": {"type": "integer"}, "high": {"type": "integer"}, "medium": {"type": "integer"}, "low": {"type": "integer"}}},
                "findings": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "title": {"type": "string"}, "severity": {"type": "string"}, "category": {"type": "string"}, "file": {"type": "string"}, "line": {"type": "integer"}, "description": {"type": "string"}, "remediation": {"type": "string"}, "references": {"type": "array", "items": {"type": "string"}}}}},
                "agentic_findings": {"type": "integer"},
                "dependency_findings": {"type": "integer"},
                "scan_duration_ms": {"type": "integer"},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True),
    )


async def handle_tool(arguments: dict, context: dict):
    start = _time.monotonic()

    target = arguments.get("target", ".")
    severity_threshold = arguments.get("severity_threshold", "medium")
    include_agentic = arguments.get("include_agentic", True)
    include_dependency = arguments.get("include_dependency", True)

    target_path = Path(target)
    if not target_path.exists():
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="NOT_FOUND",
            message=f"Target path not found: {target}",
            details={"target": target},
        ), ensure_ascii=False), isError=True)]

    findings = []
    sensitive_patterns = [
        (r'(?:api[_-]?key|secret|password|token)\s*[:=]\s*["\'][^"\']+["\']', "hardcoded_secret", "critical", "OWASP-A07", "Hardcoded secret detected", "Use environment variables or secret management"),
        (r'eval\s*\(', "eval_usage", "high", "OWASP-A03", "Use of eval() detected", "Avoid eval(); use safer alternatives"),
        (r'subprocess\.call\s*\(\s*["\']', "shell_injection_risk", "high", "OWASP-A03", "Potential shell injection via subprocess", "Use subprocess with list args, not shell=True"),
        (r'os\.system\s*\(', "os_system_usage", "medium", "OWASP-A03", "Use of os.system() detected", "Use subprocess module instead"),
        (r'innerHTML\s*=', "xss_innerhtml", "high", "OWASP-A03", "Direct innerHTML assignment", "Use textContent or DOMPurify"),
        (r'document\.write\s*\(', "xss_docwrite", "medium", "OWASP-A03", "Use of document.write()", "Use DOM manipulation methods"),
        (r'SELECT\s+.*\s+FROM\s+.*\s*\+\s*', "sql_injection", "critical", "OWASP-A03", "Potential SQL injection via string concatenation", "Use parameterized queries"),
    ]

    agentic_patterns = [
        (r'execute\s*\(\s*["\'].*(?:rm|del|drop|truncate)', "agentic_destructive_action", "critical", "OWASP-AG-01", "Agent may execute destructive commands", "Add human-in-the-loop confirmation"),
        (r'tools\s*=\s*\[.*\*.*\]', "agentic_unrestricted_tools", "high", "OWASP-AG-06", "Agent has unrestricted tool access", "Limit tool scope to minimum required"),
    ]

    scan_exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".yaml", ".yml", ".json"}
    all_patterns = list(sensitive_patterns)
    if include_agentic:
        all_patterns.extend(agentic_patterns)

    min_severity = _SEVERITY_ORDER.get(severity_threshold, 2)

    if target_path.exists():
        for root_dir, _dirs, files in os.walk(str(target_path)):
            if any(skip in root_dir for skip in ("node_modules", ".git", "__pycache__", ".venv", ".knowledge")):
                continue
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in scan_exts:
                    continue
                fpath = os.path.join(root_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                        for lineno, line in enumerate(fh, 1):
                            for pattern, rule_id, severity, category, title, remediation in all_patterns:
                                if _SEVERITY_ORDER.get(severity, 3) > min_severity:
                                    continue
                                if re.search(pattern, line, re.IGNORECASE):
                                    findings.append({
                                        "id": f"SEC-{len(findings)+1:03d}",
                                        "title": title,
                                        "severity": severity,
                                        "category": category,
                                        "file": os.path.relpath(fpath, str(target_path)),
                                        "line": lineno,
                                        "description": title,
                                        "remediation": remediation,
                                        "references": [f"https://owasp.org/Top10/{category.replace('OWASP-', '').replace('AG-', '')}_2021/"] if not category.startswith("OWASP-AG") else [],
                                    })
                except OSError:
                    pass

    dep_findings = 0
    if include_dependency:
        dep_findings = _scan_dependencies(target_path, findings, min_severity)

    elapsed_ms = int((_time.monotonic() - start) * 1000)
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1

    agentic_count = sum(1 for f in findings if f["category"].startswith("OWASP-AG"))

    result = {
        "total_findings": len(findings),
        "by_severity": by_severity,
        "findings": findings[:50],
        "agentic_findings": agentic_count,
        "dependency_findings": dep_findings,
        "scan_duration_ms": elapsed_ms,
    }
    return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]
