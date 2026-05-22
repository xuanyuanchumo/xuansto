"""
底层规则校验层（第三维防线）- Rule Validation Engine

提供输出格式Schema验证、编码规范静态分析、
安全策略强制检查、文档完整性校验等规则验证能力。
"""

from __future__ import annotations

import json
import re
import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

from skillscripts.secrets_manager.secrets_manager import (
    SecretsManager,
    SecretType,
    SecretEntry,
    ValidationResult as SecretValidationResult,
)
from skillscripts.secrets_manager.hardcoded_detector import (
    HardcodedDetector,
    Finding,
    Severity,
    ScanResult,
    DEFAULT_PATTERNS,
)


@dataclass
class ValidationResult:
    """
    验证结果数据类

    包含通过状态、错误列表、警告列表和综合评分。
    """

    validator_name: str
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    score: float = 100.0
    details: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0

    def merge(self, other: ValidationResult) -> ValidationResult:
        combined_errors = self.errors + other.errors
        combined_warnings = self.warnings + other.warnings
        combined_passed = self.passed and other.passed
        combined_score = (self.score + other.score) / 2
        return ValidationResult(
            validator_name=f"{self.validator_name}+{other.validator_name}",
            passed=combined_passed,
            errors=combined_errors,
            warnings=combined_warnings,
            score=combined_score,
            details={**self.details, **other.details},
        )


class BaseValidator(ABC):
    """验证器基类（Validator Pattern）"""

    name: str = "base"
    enabled: bool = True

    @abstractmethod
    def validate(self, content: Any, context: dict[str, Any] | None = None) -> ValidationResult:
        ...

    def is_enabled(self) -> bool:
        return self.enabled

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False


class SchemaValidator(BaseValidator):
    """
    输出格式Schema验证器

    支持 JSON Schema、YAML结构、Markdown标题层级检查。
    """

    name = "schema_validator"

    def __init__(self) -> None:
        self._json_schema_cache: dict[str, dict[str, Any]] = {}
        self._required_fields: dict[str, list[str]] = {}

    def register_json_schema(self, schema_name: str, schema: dict[str, Any]) -> None:
        self._json_schema_cache[schema_name] = schema

    def set_required_fields(self, format_type: str, fields: list[str]) -> None:
        self._required_fields[format_type] = fields

    def validate(self, content: Any, context: dict[str, Any] | None = None) -> ValidationResult:
        ctx = context or {}
        format_type = ctx.get("format_type", "auto")
        schema_name = ctx.get("schema_name", "")
        errors: list[str] = []
        warnings: list[str] = []
        if isinstance(content, str):
            if format_type == "json" or (format_type == "auto" and content.strip().startswith("{")):
                j_errs, j_warns = self._validate_json(content, schema_name)
                errors.extend(j_errs)
                warnings.extend(j_warns)
            elif format_type == "yaml" or (format_type == "auto" and content.strip().startswith("---")):
                y_errs, y_warns = self._validate_yaml_structure(content)
                errors.extend(y_errs)
                warnings.extend(y_warns)
            elif format_type == "markdown" or format_type == "md":
                md_errs, md_warns = self._validate_markdown(content)
                errors.extend(md_errs)
                warnings.extend(md_warns)
            else:
                warnings.append(f"Unknown format type '{format_type}', performing basic structure check")
                struct_errs, struct_warns = self._validate_generic_structure(content)
                errors.extend(struct_errs)
                warnings.extend(struct_warns)
        else:
            errors.append("Content must be a string for schema validation")
        score = max(0.0, 100.0 - len(errors) * 10 - len(warnings) * 2)
        return ValidationResult(
            validator_name=self.name,
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            score=score,
            details={"format_type": format_type},
        )

    def _validate_json(self, text: str, schema_name: str = "") -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e.msg} at line {e.lineno}")
            return errors, warnings
        if not isinstance(data, dict):
            errors.append("JSON root must be an object")
            return errors, warnings
        required = self._required_fields.get("json", [])
        for field_name in required:
            if field_name not in data:
                errors.append(f"Missing required field: {field_name}")
        if schema_name and schema_name in self._json_schema_cache:
            schema = self._json_schema_cache[schema_name]
            for key, spec in schema.get("properties", {}).items():
                if key in data:
                    expected_type = spec.get("type")
                    actual_type = type(data[key]).__name__
                    type_map = {"string": "str", "integer": "int", "number": "(int|float)",
                                "boolean": "bool", "array": "list", "object": "dict"}
                    mapped = type_map.get(expected_type, expected_type)
                    if mapped not in actual_type and actual_type not in mapped:
                        warnings.append(f"Field '{key}' type mismatch: expected {expected_type}, got {actual_type}")
        return errors, warnings

    def _validate_yaml_structure(self, text: str) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        lines = text.splitlines()
        has_content = any(line.strip() and not line.strip().startswith("#") for line in lines)
        if not has_content:
            errors.append("YAML content is empty or contains only comments")
        top_indent = -1
        for line in lines:
            stripped = line.rstrip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
                indent = len(line) - len(line.lstrip())
                if top_indent == -1 and stripped.endswith(":"):
                    top_indent = indent
        if top_indent > 0:
            warnings.append("YAML document may have unexpected top-level indentation")
        required = self._required_fields.get("yaml", [])
        found_keys: set[str] = set()
        for line in lines:
            match = re.match(r"^(\s*)(\w[\w\s-]*?):\s", line)
            if match:
                found_keys.add(match.group(2).strip())
        for req in required:
            if req not in found_keys:
                errors.append(f"Missing required YAML key: {req}")
        return errors, warnings

    def _validate_markdown(self, text: str) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        lines = text.splitlines()
        heading_levels: list[int] = []
        for line in lines:
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                heading_levels.append(level)
        if heading_levels:
            for i in range(1, len(heading_levels)):
                if heading_levels[i] > heading_levels[i - 1] + 1:
                    warnings.append(
                        f"Heading level jump from H{heading_levels[i-1]} to "
                        f"H{heading_levels[i]} at line {i+1}"
                    )
        has_h1 = any(l == 1 for l in heading_levels)
        if not has_h1 and heading_levels:
            warnings.append("Missing H1 heading (document title)")
        required_sections = self._required_fields.get("markdown", [])
        for section in required_sections:
            pattern = rf"^#+\s*.*{re.escape(section)}"
            if not re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
                errors.append(f"Missing required section: {section}")
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        links = re.findall(link_pattern, text)
        broken_links: list[str] = []
        for link_text, link_url in links:
            if link_url.startswith("http") and ("example.com" in link_url or "localhost" in link_url):
                broken_links.append(f"[{link_text}]({link_url})")
        if broken_links:
            warnings.append(f"Found {len(broken_links)} potentially placeholder/broken links")
        return errors, warnings

    def _validate_generic_structure(self, text: str) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        if len(text.strip()) < 10:
            errors.append("Content too short to be valid output")
        if text.count("{") != text.count("}"):
            warnings.append("Unmatched braces detected")
        if text.count("(") != text.count(")"):
            warnings.append("Unmatched parentheses detected")
        return errors, warnings


class CodeStyleValidator(BaseValidator):
    """
    编码规范静态分析验证器

    支持 PEP8（Python）、ESLint（JavaScript）、Airbnb（TypeScript）等规范。
    """

    name = "code_style_validator"

    PEP8_RULES: dict[str, tuple[str, int]] = {
        "E501": ("Line too long (>79 chars)", 5),
        "E302": ("Expected 2 blank lines before function", 8),
        "E303": ("Too many blank lines", 3),
        "E225": ("Missing whitespace around operator", 7),
        "E231": ("Missing whitespace after ','", 6),
        "W291": ("Trailing whitespace", 2),
        "W292": ("No newline at end of file", 3),
        "W293": ("Backslash continuation", 4),
        "E111": ("Indentation is not a multiple of 4", 6),
        "N806": ("Variable in function should be lowercase", 4),
        "N802": ("Function name should be lowercase", 5),
        "N816": ("Variable should not mix case", 3),
    }
    ESLINT_RULES: dict[str, tuple[str, int]] = {
        "no-unused-vars": ("Unused variable declared", 6),
        "no-undef": ("Undefined variable used", 9),
        "semi": ("Missing semicolon", 5),
        "eqeqeq": ("Expected === instead of ==", 4),
        "no-var": ("Use let/const instead of var", 5),
        "no-trailing-spaces": ("Trailing whitespace", 2),
        "no-multiple-empty-lines": ("Multiple empty lines", 3),
        "quotes": ("Inconsistent quote style", 3),
        "indent": ("Incorrect indentation", 6),
        "comma-dangle": ("Trailing comma issue", 2),
    }

    def __init__(self) -> None:
        self.language: str = "python"
        self.max_line_length: int = 88
        self.strict_mode: bool = False

    def set_language(self, language: str) -> None:
        self.language = language.lower()

    def validate(self, content: Any, context: dict[str, Any] | None = None) -> ValidationResult:
        ctx = context or {}
        lang = ctx.get("language", self.language)
        errors: list[str] = []
        warnings: list[str] = []
        if not isinstance(content, str):
            return ValidationResult(
                validator_name=self.name, passed=False, errors=["Content must be a string"], score=0.0
            )
        if lang == "python":
            errors, warnings = self._check_python(content)
        elif lang in ("javascript", "js"):
            errors, warnings = self._check_javascript(content)
        elif lang in ("typescript", "ts"):
            errors, warnings = self._check_typescript(content)
        else:
            warnings.append(f"Unsupported language '{lang}', performing generic checks")
            errors, warnings = self._check_generic(content)
        score = max(0.0, 100.0 - sum(e[1] for e in [(err, 8) for err in errors]) - sum(w[1] for w in [(warn, 2) for warn in warnings]))
        return ValidationResult(
            validator_name=self.name,
            passed=(len(errors) == 0 or (not self.strict_mode)),
            errors=errors,
            warnings=warnings,
            score=score,
            details={"language": lang},
        )

    def _check_python(self, code: str) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        lines = code.splitlines()
        for i, line in enumerate(lines, 1):
            stripped = line.rstrip("\n\r")
            if len(stripped) > self.max_line_length:
                errors.append(f"[E501] Line {i}: Line length {len(stripped)} exceeds {self.max_line_length}")
            if stripped and stripped != line:
                warnings.append(f"[W291] Line {i}: Trailing whitespace")
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = node.name
                    if not name.islower() and "_" not in name:
                        warnings.append(f"[N802] Function '{name}' should be lowercase")
                    args = node.args.args
                    for arg in args:
                        if not arg.arg.islower() and arg.arg != "self":
                            warnings.append(f"[N806] Argument '{arg.arg}' in '{name}' should be lowercase")
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and not target.id.islower():
                            warnings.append(f"[N806] Variable '{target.id}' should be lowercase")
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        if code and not code.endswith("\n"):
            warnings.append("[W292] No newline at end of file")
        return errors, warnings

    def _check_javascript(self, code: str) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        lines = code.splitlines()
        var_pattern = re.compile(r"\bvar\s+(\w+)")
        for i, line in enumerate(lines, 1):
            if var_pattern.search(line):
                warnings.append(f"[no-var] Line {i}: Use 'let' or 'const' instead of 'var'")
            if line.rstrip() != line and line.strip():
                warnings.append(f"[no-trailing-spaces] Line {i}: Trailing whitespace")
            if len(line.rstrip()) > self.max_line_length:
                errors.append(f"Line {i}: Line exceeds {self.max_line_length} characters")
        eq_pattern = re.compile(r"(?<!\!|\=)=[^=]")
        for i, line in enumerate(lines, 1):
            if eq_pattern.search(line) and not line.strip().startswith("//") and "'" not in line and '"' not in line:
                if "for" not in line and "while" not in line and "if" not in line:
                    warnings.append(f"[eqeqeq] Line {i}: Consider using '===' instead of '=='")
        func_pattern = re.compile(r"\bfunction\s+([A-Z])")
        for i, line in enumerate(lines, 1):
            if func_pattern.search(line):
                warnings.append(f"Line {i}: Function names should start with lowercase")
        if code and not code.endswith("\n"):
            warnings.append("No newline at end of file")
        return errors, warnings

    def _check_typescript(self, code: str) -> tuple[list[str], list[str]]:
        errors, base_warnings = self._check_javascript(code)
        warnings = list(base_warnings)
        any_pattern = re.compile(r":\s*any\b(?![\w[])")
        lines = code.splitlines()
        for i, line in enumerate(lines, 1):
            if any_pattern.search(line) and "declare" not in line:
                warnings.append(f"Line {i}: Avoid using 'any' type; use specific types instead")
        interface_pattern = re.compile(r"\binterface\s+\w+")
        if not interface_pattern.search(code) and "type " not in code and ":" in code:
            warnings.append("Consider defining TypeScript interfaces for better type safety")
        return errors, warnings

    def _check_generic(self, code: str) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        lines = code.splitlines()
        for i, line in enumerate(lines, 1):
            if len(line.rstrip()) > self.max_line_length:
                errors.append(f"Line {i}: Exceeds max line length ({self.max_line_length})")
        if code and not code.endswith("\n"):
            warnings.append("No newline at end of file")
        return errors, warnings


class SecurityPolicyValidator(BaseValidator):
    """
    安全策略强制检查验证器

    检测硬编码密钥、SQL注入模式、XSS向量等安全问题。
    """

    name = "security_policy_validator"

    SECRET_PATTERNS: list[tuple[str, str, int]] = [
        (r"(?i)(api[_-]?key|apikey)['\"]?\s*[:=]\s*['\"][^'\"]{10,}['\"]", "Hardcoded API key", 10),
        (r"(?i)(secret|password|passwd|pwd)['\"]?\s*[:=]\s*['\"][^'\"]{4,}['\"]", "Hardcoded password/secret", 10),
        (r"(?i)(token|auth[_-]?token|access[_-]?token)['\"]?\s*[:=]\s*['\"][^'\"]{10,}['\"]", "Hardcoded token", 10),
        (r"(?i)(private[_-]?key|secret[_-]?key)['\"]?\s*[:=]\s*['\"][^'\"]{20,}['\"]", "Hardcoded private key", 10),
        (r"(?i)(aws_access_key_id)['\"]?\s*[:=]\s*['\"][A-Z0-9]{20}['\"]", "AWS access key hardcoded", 10),
        (r"(?i)(aws_secret_access_key)['\"]?\s*[:=]\s*['\"][A-Za-z0-9/+=]{40}['\"]", "AWS secret key hardcoded", 10),
    ]
    SQL_INJECTION_PATTERNS: list[tuple[str, str, int]] = [
        (r'["\']\s*\+\s*["\'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP)', "String concatenation in SQL (injection risk)", 10),
        (r'(?:SELECT|INSERT|UPDATE|DELETE)\s+.*(?:FROM|INTO)\s+.*f["\']', "f-string in SQL query (injection risk)", 9),
        (r'(?:SELECT|INSERT|UPDATE|DELETE)\s+.*(?:FROM|INTO)\s+.*%\s*\(', "% formatting in SQL (injection risk)", 9),
        (r'(?:SELECT|INSERT|UPDATE|DELETE)\s+.*(?:FROM|INTO)\s+.*\.format\(', ".format() in SQL (injection risk)", 9),
        (r'"OR\s+1\s*=\s*1', "Classic SQL injection pattern (OR 1=1)", 10),
        (r'"\;\s*(DROP|DELETE|TRUNCATE)', "SQL injection with statement terminator", 10),
        (r'UNION\s+SELECT', "UNION-based SQL injection attempt", 9),
    ]
    XSS_PATTERNS: list[tuple[str, str, int]] = [
        (r'innerHTML\s*=\s*', "Direct innerHTML assignment (XSS risk)", 8),
        (r'document\.write\s*\(', "document.write usage (XSS risk)", 8),
        (r'eval\s*\(', "eval() usage (XSS/code injection risk)", 7),
        (r'<script\b', "Inline script tag detected (XSS risk)", 9),
        (r'on(error|load|click|mouseover)\s*=', "Inline event handler (XSS risk)", 7),
        (r'javascript:', "javascript: protocol (XSS risk)", 9),
    ]

    def __init__(self) -> None:
        self.check_secrets: bool = True
        self.check_sql_injection: bool = True
        self.check_xss: bool = True
        self.custom_patterns: list[tuple[str, str, int]] = []
        self._hardcoded_detector: HardcodedDetector = HardcodedDetector()
        self._secrets_manager: SecretsManager | None = None

    def add_custom_pattern(self, pattern: str, description: str, severity: int = 5) -> None:
        self.custom_patterns.append((pattern, description, severity))

    def validate(self, content: Any, context: dict[str, Any] | None = None) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        issues: list[dict[str, Any]] = []
        if not isinstance(content, str):
            return ValidationResult(
                validator_name=self.name, passed=False, errors=["Content must be a string"], score=0.0
            )
        ctx = context or {}
        file_path = ctx.get("file_path")
        hardcoded_findings = self.detect_hardcoded_secrets(str(content), file_path=str(file_path) if file_path else "inline")
        if hardcoded_findings:
            critical_count = sum(1 for f in hardcoded_findings if f.severity in (Severity.CRITICAL, Severity.HIGH))
            if critical_count > 0:
                issues.append({
                    "type": "hardcoded_secret",
                    "severity": "critical" if any(f.severity == Severity.CRITICAL for f in hardcoded_findings) else "high",
                    "message": f"检测到 {len(hardcoded_findings)} 个硬编码敏感信息 ({critical_count} 个 Critical/High)",
                    "details": [{"file": str(f.file_path), "line": f.line, "pattern": f.pattern_name} for f in hardcoded_findings[:10]],
                })
        if self.check_secrets:
            sec_errs, sec_warns = self._check_secrets(content)
            errors.extend(sec_errs)
            warnings.extend(sec_warns)
        if self.check_sql_injection:
            sql_errs, sql_warns = self._check_sql_injection(content)
            errors.extend(sql_errs)
            warnings.extend(sql_warns)
        if self.check_xss:
            xss_errs, xss_warns = self._check_xss(content)
            errors.extend(xss_errs)
            warnings.extend(xss_warns)
        for pattern, desc, severity in self.custom_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                if severity >= 8:
                    errors.append(f"[CUSTOM-HIGH] {desc}")
                else:
                    warnings.append(f"[CUSTOM] {desc}")
        total_deduction = len(errors) * 10 + len(warnings) * 3
        score = max(0.0, 100.0 - total_deduction)
        return ValidationResult(
            validator_name=self.name,
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            score=score,
            details={
                "secrets_checked": self.check_secrets,
                "sql_checked": self.check_sql_injection,
                "xss_checked": self.check_xss,
            },
        )

    def _check_secrets(self, content: str) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        for pattern, desc, severity in self.SECRET_PATTERNS:
            matches = re.finditer(pattern, content)
            for m in matches:
                line_num = content[:m.start()].count("\n") + 1
                redacted = m.group()[:20] + "..." if len(m.group()) > 20 else m.group()
                msg = f"[SECRET-{severity}] Line {line_num}: {desc} -> `{redacted}`"
                if severity >= 10:
                    errors.append(msg)
                else:
                    warnings.append(msg)
        return errors, warnings

    def _check_sql_injection(self, content: str) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        for pattern, desc, severity in self.SQL_INJECTION_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for m in matches:
                line_num = content[:m.start()].count("\n") + 1
                snippet = m.group()[:50] + "..." if len(m.group()) > 50 else m.group()
                msg = f"[SQL-{severity}] Line {line_num}: {desc} -> `{snippet}`"
                if severity >= 10:
                    errors.append(msg)
                else:
                    warnings.append(msg)
        return errors, warnings

    def _check_xss(self, content: str) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        for pattern, desc, severity in self.XSS_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for m in matches:
                line_num = content[:m.start()].count("\n") + 1
                snippet = m.group()[:50] + "..." if len(m.group()) > 50 else m.group()
                msg = f"[XSS-{severity}] Line {line_num}: {desc} -> `{snippet}`"
                if severity >= 9:
                    errors.append(msg)
                else:
                    warnings.append(msg)
        return errors, warnings

    def detect_hardcoded_secrets(self, source_code: str, file_path: Path | str = "inline") -> list[Finding]:
        """调用 HardcodedDetector 扫描源码中的硬编码敏感信息"""
        if isinstance(source_code, str) and len(source_code.strip()) == 0:
            return []
        import tempfile
        if isinstance(file_path, str):
            temp_path = Path(tempfile.gettempdir()) / "_secrets_scan_tmp.py"
            temp_path.write_text(source_code, encoding="utf-8")
            try:
                result = self._hardcoded_detector.scan_file(temp_path)
                return result.findings
            finally:
                temp_path.unlink(missing_ok=True)
        else:
            result = self._hardcoded_detector.scan_file(Path(file_path))
            return result.findings

    def validate_env_config(self) -> dict:
        """验证当前环境变量配置的完整性"""
        sm = SecretsManager()
        try:
            sm.load()
        except Exception:
            pass
        result = sm.validate_all()
        return {
            "is_valid": result.is_valid,
            "issues": result.issues,
            "score": result.score,
            "warnings": result.warnings,
            "loaded_keys_count": len(sm._store) if hasattr(sm, '_store') else 0,
        }


class DocumentIntegrityValidator(BaseValidator):
    """
    文档完整性校验器

    检查必需章节存在性、Markdown链接有效性、图片引用完整性。
    """

    name = "document_integrity_validator"

    def __init__(self) -> None:
        self.required_sections: list[str] = []
        self.required_headings: list[str] = []
        self.base_path: Path | None = None

    def set_required_sections(self, sections: list[str]) -> None:
        self.required_sections = sections

    def set_base_path(self, path: Path | str) -> None:
        self.base_path = Path(path)

    def validate(self, content: Any, context: dict[str, Any] | None = None) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        if not isinstance(content, str):
            return ValidationResult(
                validator_name=self.name, passed=False, errors=["Content must be a string"], score=0.0
            )
        ctx = context or {}
        required = ctx.get("required_sections", self.required_sections)
        section_errs, section_warns = self._check_sections(content, required)
        errors.extend(section_errs)
        warnings.extend(section_warns)
        link_errs, link_warns = self._check_links(content)
        errors.extend(link_errs)
        warnings.extend(link_warns)
        img_issues = self._check_images(content)
        warnings.extend(img_issues)
        score = max(0.0, 100.0 - len(errors) * 12 - len(warnings) * 3)
        return ValidationResult(
            validator_name=self.name,
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            score=score,
            details={
                "sections_checked": len(required),
                "links_found": len(re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)),
                "images_found": len(re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", content)),
            },
        )

    def _check_sections(self, content: str, required: list[str]) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        for section in required:
            escaped = re.escape(section)
            pattern = rf"^#+\s*.*{escaped}\s*$"
            if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                errors.append(f"Missing required section: '{section}'")
        headings = re.findall(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE)
        if headings:
            levels = [len(h[0]) for h in headings]
            for i in range(1, len(levels)):
                if levels[i] > levels[i - 1] + 1:
                    warnings.append(
                        f"Heading level skip from H{levels[i-1]} to H{levels[i]} near: '{headings[i][1][:30]}'"
                    )
        return errors, warnings

    def _check_links(self, content: str) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        empty_link_pattern = re.compile(r"\[\]\(\)")
        if empty_link_pattern.search(content):
            errors.append("Found empty markdown link []()")
        links = link_pattern.findall(content)
        for link_text, url in links:
            if not url or url.strip() == "":
                errors.append(f"Empty URL for link text: '{link_text}'")
            elif url.startswith("http://") or url.startswith("https://"):
                if "example.com" in url or "localhost" in url or "127.0.0.1" in url:
                    warnings.append(f"Placeholder/development URL: [{link_text}]({url})")
            elif not url.startswith("#") and not url.startswith("mailto:") and not url.startswith("/"):
                if self.base_path:
                    target = self.base_path / url
                    if not target.exists():
                        warnings.append(f"Broken local link: [{link_text}]({url}) -> {target} does not exist")
                else:
                    warnings.append(f"Relative link (cannot verify without base_path): [{link_text}]({url})")
        ref_pattern = re.compile(r"^\[([^\]]+)\]:\s*(.+)$", re.MULTILINE)
        refs = ref_pattern.findall(content)
        ref_ids = {ref_id for ref_id, _ in refs}
        ref_usage_pattern = re.compile(r"\[([^\]]+)\]\[([^\]]+)\]")
        usages = ref_usage_pattern.findall(content)
        for _, ref_id in usages:
            if ref_id and ref_id not in ref_ids:
                errors.append(f"Undefined reference: [{ref_id}]")
        return errors, warnings

    def _check_images(self, content: str) -> tuple[list[str], list[str]]:
        issues: list[str] = []
        img_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
        images = img_pattern.findall(content)
        for alt_text, src in images:
            if not alt_text.strip():
                issues.append(f"Image missing alt text: ({src})")
            if not src.strip():
                issues.append("Image with empty source URL")
            elif self.base_path and not src.startswith("http") and not src.startswith("data:"):
                target = self.base_path / src
                if not target.exists():
                    issues.append(f"Missing image file: {src} (resolved: {target})")
        return issues


class RuleValidationEngine:
    """
    底层规则校验引擎 - 第三维输出防线

    职责：
      - 输出格式Schema验证（JSON/YAML/Markdown）
      - 编码规范静态分析（PEP8/ESLint/Airbnb）
      - 安全策略强制检查（密钥/SQL注入/XSS）
      - 文档完整性校验（章节/链接/图片）
    """

    def __init__(self) -> None:
        self._validators: dict[str, BaseValidator] = {
            SchemaValidator.name: SchemaValidator(),
            CodeStyleValidator.name: CodeStyleValidator(),
            SecurityPolicyValidator.name: SecurityPolicyValidator(),
            DocumentIntegrityValidator.name: DocumentIntegrityValidator(),
        }

    def get_validator(self, name: str) -> BaseValidator | None:
        return self._validators.get(name)

    def add_validator(self, validator: BaseValidator) -> None:
        self._validators[validator.name] = validator

    def remove_validator(self, name: str) -> BaseValidator | None:
        return self._validators.pop(name, None)

    def enable_validator(self, name: str) -> bool:
        v = self._validators.get(name)
        if v:
            v.enable()
            return True
        return False

    def disable_validator(self, name: str) -> bool:
        v = self._validators.get(name)
        if v:
            v.disable()
            return True
        return False

    def validate_all(
        self,
        content: Any,
        context: dict[str, Any] | None = None,
        validators: list[str] | None = None,
    ) -> ValidationResult:
        target_names = validators or list(self._validators.keys())
        results: list[ValidationResult] = []
        for name in target_names:
            validator = self._validators.get(name)
            if validator and validator.is_enabled():
                result = validator.validate(content, context)
                results.append(result)
        if not results:
            return ValidationResult(
                validator_name="engine",
                passed=True,
                warnings=["No validators executed"],
                score=100.0,
            )
        merged = results[0]
        for r in results[1:]:
            merged = merged.merge(r)
        merged.validator_name = "RuleValidationEngine"
        merged.details["validators_run"] = len(results)
        merged.details["validator_names"] = [r.validator_name for r in results]
        return merged

    def validate_single(
        self,
        validator_name: str,
        content: Any,
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        validator = self._validators.get(validator_name)
        if not validator:
            return ValidationResult(
                validator_name=validator_name,
                passed=False,
                errors=[f"Validator '{validator_name}' not found"],
                score=0.0,
            )
        return validator.validate(content, context)

    @property
    def available_validators(self) -> list[str]:
        return [name for name, v in self._validators.items() if v.is_enabled()]

    @property
    def all_validator_names(self) -> list[str]:
        return list(self._validators.keys())
