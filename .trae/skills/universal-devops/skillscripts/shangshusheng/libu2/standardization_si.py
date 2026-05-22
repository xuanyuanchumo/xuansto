"""
标准化司 - 命名规范检查、目录结构合规、文件编码、版权声明、.gitignore、EditorConfig、标准化评分
"""
from __future__ import annotations

import re
import json
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class StandardizationError(Exception):
    """标准化相关异常"""
    pass


class CheckError(StandardizationError):
    """检查错误"""


class LanguageConvention(str, Enum):
    """编程语言约定枚举"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    SQL = "sql"
    RUST = "rust"


@dataclass
class NamingRule:
    """命名规则定义"""
    pattern: str
    description: str
    convention: str
    examples_good: list[str] = field(default_factory=list)
    examples_bad: list[str] = field(default_factory=list)
    severity: str = "error"

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern": self.pattern,
            "description": self.description,
            "convention": self.convention,
            "severity": self.severity,
        }


@dataclass
class NamingViolation:
    """命名违规条目"""
    file_path: str
    line_number: int
    violation_type: str
    actual_name: str
    expected_pattern: str
    suggestion: str = ""
    severity: str = "warning"

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file_path,
            "line": self.line_number,
            "type": self.violation_type,
            "actual": self.actual_name,
            "expected": self.expected_pattern,
            "suggestion": self.suggestion,
            "severity": self.severity,
        }


@dataclass
class DirectoryStructure:
    """目录结构检查结果"""
    expected_dirs: list[str]
    existing_dirs: list[str]
    missing_dirs: list[str]
    extra_dirs: list[str]
    compliance_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected_count": len(self.expected_dirs),
            "existing_count": len(self.existing_dirs),
            "missing": self.missing_dirs,
            "extra": self.extra_dirs[:10],
            "compliance_score": round(self.compliance_score, 2),
        }


@dataclass
class EncodingCheck:
    """编码检查结果"""
    file_path: str
    encoding: str
    has_bom: bool = False
    is_utf8: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file_path,
            "encoding": self.encoding,
            "has_bom": self.has_bom,
            "is_utf8": self.is_utf8,
            "issues": self.issues,
        }


@dataclass
class CopyrightHeader:
    """版权头检查结果"""
    file_path: str
    has_header: bool = False
    header_format: str = ""
    license_id: str = ""
    year: str = ""
    holder: str = ""
    is_valid_spdx: bool = False
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file_path,
            "has_header": self.has_header,
            "license": self.license_id or "未检测到",
            "spdx_valid": self.is_valid_spdx,
            "issues": self.issues,
        }


@dataclass
class GitignoreCheck:
    """.gitignore检查结果"""
    file_exists: bool = False
    missing_entries: list[str] = field(default_factory=list)
    present_entries: list[str] = field(default_factory=list)
    unnecessary_entries: list[str] = field(default_factory=list)
    compliance_pct: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "exists": self.file_exists,
            "present": len(self.present_entries),
            "missing": self.missing_entries[:15],
            "unnecessary": self.unnecessary_entries[:5],
            "compliance": round(self.compliance_pct, 1),
        }


@dataclass
class EditorConfigCheck:
    """EditorConfig检查结果"""
    file_exists: bool = False
    checked_keys: list[dict[str, Any]] = field(default_factory=list)
    missing_recommended: list[str] = field(default_factory=list)
    violations: list[dict[str, Any]] = field(default_factory=dict)
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "exists": self.file_exists,
            "checked_items": len(self.checked_keys),
            "missing": self.missing_recommended,
            "violations": self.violations,
            "score": round(self.score, 2),
        }


@dataclass
class StandardizationReport:
    """标准化综合报告"""
    project_name: str = ""
    total_score: float = 0.0
    naming_score: float = 0.0
    directory_score: float = 0.0
    encoding_score: float = 0.0
    copyright_score: float = 0.0
    gitignore_score: float = 0.0
    editorconfig_score: float = 0.0
    violations: list[NamingViolation] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def grade(self) -> str:
        if self.total_score >= 90: return "A (优秀)"
        if self.total_score >= 80: return "B (良好)"
        if self.total_score >= 70: return "C (合格)"
        if self.total_score >= 60: return "D (需改进)"
        return "F (不合格)"

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project_name,
            "total_score": round(self.total_score, 1),
            "grade": self.grade(),
            "naming": round(self.naming_score, 1),
            "directory": round(self.directory_score, 1),
            "encoding": round(self.encoding_score, 1),
            "copyright": round(self.copyright_score, 1),
            "gitignore": round(self.gitignore_score, 1),
            "editorconfig": round(self.editorconfig_score, 1),
            "violation_count": len(self.violations),
        }

    def to_markdown(self) -> str:
        lines: list[str] = []
        lines.append("# 📏 标准化司 · 检查报告\n")
        lines.append(f"## 项目: {self.project_name}\n")
        lines.append(f"| 维度 | 得分 | 权重 | 加权分 |")
        lines.append(f"| --- | --- | --- | --- |")
        weights = {"naming": 25, "directory": 15, "encoding": 10, "copyright": 15, "gitignore": 15, "editorconfig": 20}
        scores_map = [
            ("命名规范", self.naming_score, weights["naming"]),
            ("目录结构", self.directory_score, weights["directory"]),
            ("文件编码", self.encoding_score, weights["encoding"]),
            ("版权声明", self.copyright_score, weights["copyright"]),
            (".gitignore", self.gitignore_score, weights["gitignore"]),
            ("EditorConfig", self.editorconfig_score, weights["editorconfig"]),
        ]
        for name, score, weight in scores_map:
            weighted = score * weight / 100
            icon = "🟢" if score >= 80 else ("🟡" if score >= 60 else "🔴")
            lines.append(f"{name} | {icon} **{score:.1f}** | {weight}% | **{weighted:.1f}** |")

        lines.append(f"\n### 总分: **{self.total_score:.1f}** / 100 → 等级: **{self.grade()}**\n")

        if self.violations:
            lines.append("### 主要违规\n")
            for v in self.violations[:20]:
                sev_icon = {"error": "🔴", "warning": "🟡"}.get(v.severity, "⚪")
                lines.append(f"- {sev_icon} `{v.file_path}`:{v.line_number} "
                             f"`{v.actual_name}` 应为{v.expected_pattern} - {v.suggestion}")

        return "\n".join(lines)


_NAMING_RULES: dict[LanguageConvention, dict[str, NamingRule]] = {
    LanguageConvention.PYTHON: {
        "module_snake_case": NamingRule(
            pattern=r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$",
            description="Python模块/函数/变量名使用snake_case",
            convention="snake_case",
            examples_good=["user_service", "get_user_by_id", "MAX_CONNECTIONS"],
            examples_bad=["UserService", "getUserById", "max-connections"],
            severity="error",
        ),
        "class_pascal_case": NamingRule(
            pattern=r"^[A-Z][a-zA-Z0-9]*$",
            description="Python类名使用PascalCase",
            convention="PascalCase",
            examples_good=["UserService", "HTTPClient", "APIRouter"],
            examples_bad=["userService", "http_client", "api_router"],
            severity="error",
        ),
        "constant_upper_snake": NamingRule(
            pattern=r"^[A-Z][A-Z0-9_]*$",
            description="Python常量使用UPPER_SNAKE_CASE",
            convention="UPPER_SNAKE_CASE",
            examples_good=["MAX_RETRIES", "DEFAULT_TIMEOUT", "API_BASE_URL"],
            examples_bad=["maxRetries", "default_timeout", "ApiBaseUrl"],
            severity="warning",
        ),
        "private_underscore": NamingRule(
            pattern=r"^_[a-z][a-z0-9_]*$",
            description="Python私有属性/方法以单下划线开头",
            convention="_leading_underscore",
            examples_good=["_internal_cache", "_validate_input"],
            examples_bad=["__private", "internalCache"],
            severity="info",
        ),
    },
    LanguageConvention.JAVASCRIPT: {
        "var_camel_case": NamingRule(
            pattern=r"^[a-z][a-zA-Z0-9]*$",
            description="JS/TS变量和函数名使用camelCase",
            convention="camelCase",
            examples_good=["userName", "getUserById", "isLoading"],
            examples_bad=["UserName", "get_user_by_id", "is-loading"],
            severity="error",
        ),
        "class_pascal_case": NamingRule(
            pattern=r"^[A-Z][a-zA-Z0-9]*$",
            description="JS/TS类、组件、接口、类型别名使用PascalCase",
            convention="PascalCase",
            examples_good=["UserService", "ButtonComponent", "IUserRepository"],
            examples_bad=["userService", "button_component", "iUserRepo"],
            severity="error",
        ),
        "file_kebab_or_camel": NamingRule(
            pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$|^[a-z][a-zA-Z0-9]*$",
            description="JS/TS文件和目录名使用kebab-case或camelCase",
            convention="kebab-case/camelCase",
            examples_good=["user-service.ts", "UserProfile.ts", "utils/"],
            examples_bad=["User_Service.ts", "userService.js", "Utils/"],
            severity="warning",
        ),
        "constant_upper_snake": NamingRule(
            pattern=r"^[A-Z][A-Z0-9_]*$",
            description="JS/TS常量使用UPPER_SNAKE_CASE",
            convention="UPPER_SNAKE_CASE",
            examples_good=["API_URL", "MAX_ITEMS", "DB_HOST"],
            examples_bad=["apiUrl", "MaxItems", "dbHost"],
            severity="warning",
        ),
    },
    LanguageConvention.GO: {
        "exported_pascal": NamingRule(
            pattern=r"^[A-Z]",
            description="Go导出标识符（首字母大写）",
            convention="PascalCase (exported)",
            examples_good=["UserService", "NewClient", "GetUserByID"],
            examples_bad=["userService", "newClient", "getUserByID"],
            severity="error",
        ),
        "unexported_camel": NamingRule(
            pattern=r"^[a-z]",
            description="Go非导出标识符（首字母小写）",
            convention="camelCase (unexported)",
            examples_good=["cache", "parseResponse", "httpClient"],
            examples_bad=["Cache", "ParseResponse", "HttpClient"],
            severity="error",
        ),
        "acronym_upper": NamingRule(
            pattern=r"(?<![a-zA-Z])(?:HTTP|URL|API|ID|JSON|XML|SQL|OS|CPU|IO|TCP|UDP|DNS|TLS|SSL|GCL|AWS|GCP)(?![a-z])",
            description="Go缩写词全大写：HTTP/URL/API等",
            convention="Acronym Uppercase",
            examples_good=["HTTPClient", "APIKey", "JSONParser", "url.URL"],
            examples_bad=["HttpClient", "apiKey", "JsonParser", "Url"],
            severity="warning",
        ),
        "interface_suffix": NamingRule(
            pattern=r"(?:er|able)$",
            description="Go接口通常以er或able后缀结尾",
            convention="Interface Suffix",
            examples_good=["Reader", "Writer", "Closer", "Sorter"],
            examples_bad=["IReader", "IUserInterface", "UserIFace"],
            severity="info",
        ),
    },
    LanguageConvention.JAVA: {
        "member_camel_case": NamingRule(
            pattern=r"^[a-z][a-zA-Z0-9]*$",
            description="Java成员变量和方法使用camelCase",
            convention="camelCase",
            examples_good=["userName", "calculateTotal", "isActive"],
            examples_bad=["UserName", "user_name", "IsActive"],
            severity="error",
        ),
        "class_pascal_case": NamingRule(
            pattern=r"^[A-Z][a-zA-Z0-9]*$",
            description="Java类和接口使用PascalCase",
            convention="PascalCase",
            examples_good=["UserService", "IUserRepository", "AppConfig"],
            examples_bad=["userService", "iUserRepository", "appConfig"],
            severity="error",
        },
        "package_snake_case": NamingRule(
            pattern=r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$",
            description="Java包名使用snake_case，全小写",
            convention="snake_case (lowercase)",
            examples_good=["com.example.service.user", "org.apache.utils"],
            examples_bad=["com.example.Service.User", "org.apache.Utils"],
            severity="error",
        ),
        "constant_upper_snake": NamingRule(
            pattern=r"^[A-Z][A-Z0-9_]*(_[A-Z0-9_]+)*$",
            description="Java常量使用UPPER_SNAKE_CASE",
            convention="UPPER_SNAKE_CASE",
            examples_good=["MAX_CONNECTIONS", "DEFAULT_TIMEOUT_MS", "PI"],
            examples_bad=["maxConnections", "DefaultTimeoutMs", "pi"],
            severity="warning",
        ),
    },
    LanguageConvention.SQL: {
        "table_snake_case": NamingRule(
            pattern=r"^[a-z][a-z0-9_]*$",
            description="SQL表名使用snake_case，复数形式",
            convention="snake_case (plural)",
            examples_good=["users", "order_items", "user_profiles"],
            examples_bad=["Users", "OrderItems", "userProfiles"],
            severity="error",
        ),
        "column_snake_case": NamingRule(
            pattern=r"^[a-z][a-z0-9_]*$",
            description="SQL列名使用snake_case",
            convention="snake_case",
            examples_good=["user_id", "created_at", "is_active", "full_name"],
            examples_bad=["userId", "createdAt", "isActive", "fullName"],
            severity="error",
        ),
        "keyword_upper": NamingRule(
            pattern=r"^(SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP|BY|ORDER|HAVING|LIMIT|OFFSET|CREATE|ALTER|DROP|TABLE|INDEX|VIEW|TRIGGER|PROCEDURE|FUNCTION|AND|OR|NOT|IN|EXISTS|BETWEEN|LIKE|IS|NULL|AS|DISTINCT|UNION|ALL|SET|VALUES|INTO|CASCADE|RESTRICT|PRIMARY|KEY|FOREIGN|REFERENCES|UNIQUE|CHECK|DEFAULT|NOT NULL|AUTO_INCREMENT|SERIAL|VARCHAR|TEXT|INT|BIGINT|BOOLEAN|DATE|TIMESTAMP|DECIMAL|FLOAT|DOUBLE|ENUM)$",
            description="SQL关键字使用大写",
            convention="UPPERCASE keywords",
            examples_good=["SELECT * FROM users WHERE id = ?", "INSERT INTO logs VALUES (...)"],
            examples_bad:["select * from users where id = ?", "insert into logs values (...)"],
            severity="warning",
        ),
        "index_naming": NamingRule(
            pattern=r"^idx_[a-z][a-z0-9_]*(_[a-z]+)?$",
            description="SQL索引以idx_前缀+表名列命名",
            convention="idx_{table}_{columns}",
            examples_good=["idx_users_email", "idx_orders_created_at_status"],
            examples_bad=["email_index", "IX_users_email", "UsersEmailIdx"],
            severity="info",
        },
    },
}

_STANDARD_DIRS: dict[str, list[str]] = {
    "python": ["src/", "tests/", "docs/", "config/", "scripts/", ".github/workflows/"],
    "javascript": ["src/", "tests/", "public/", "dist/", "docs/", ".github/workflows/"],
    "go": ["cmd/", "internal/", "pkg/", "api/", "configs/", "docs/", "scripts/"],
    "java": ["src/main/java/", "src/main/resources/", "src/test/java/", "docs/"],
    "general": [".git/", "README.md", "LICENSE", ".gitignore", ".editorconfig"],
}

_GITIGNORE_ESSENTIAL: list[str] = [
    "__pycache__/",
    "*.py[cod]",
    "$py.class",
    "*.so",
    ".Python",
    "build/",
    "develop-eggs/",
    "dist/",
    "downloads/",
    "eggs/",
    ".eggs/",
    "lib/",
    "lib64/",
    "parts/",
    "sdist/",
    "var/",
    "wheels/",
    "*.egg-info/",
    ".installed.cfg",
    "*.egg",
    "MANIFEST",
    ".env",
    ".venv/",
    "venv/",
    "ENV/",
    "node_modules/",
    "*.db",
    "*.sqlite3",
    ".DS_Store",
    "Thumbs.db",
    "*.log",
    "coverage/",
    "htmlcov/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    ".idea/",
    ".vscode/",
    "*.swp",
    "*.swo",
    "*~",
]

_SPDX_LICENSE_PATTERN = re.compile(
    r"SPDX-License-Identifier:\s*([A-Za-z0-9.\-+ OR ]+)"
)


class StandardizationSi:
    """
    标准化司 - 礼部·仪制司

    提供全面的代码标准化检查能力：
    - 命名规范检查器（Python PEP8 / JS camelCase / Go PascalCase / Java / SQL）
    - 目录结构合规性检查（约定布局）
    - 文件编码检查（UTF-8 BOM检测）
    - 文件头版权声明检查（SPDX许可证格式）
    - .gitignore完整性检查
    - EditorConfig合规检查
    - 整体标准化评分（0-100分）
    """

    _INSTANCE: StandardizationSi | None = None

    def __init__(self) -> None:
        self._report: StandardizationReport = StandardizationReport()
        self._naming_violations: list[NamingViolation] = []
        self._encoding_results: list[EncodingCheck] = []
        self._copyright_results: list[CopyrightHeader] = []
        self._directory_result: DirectoryStructure | None = None
        self._gitignore_result: GitignoreCheck | None = None
        self._editorconfig_result: EditorConfigCheck | None = None

    @classmethod
    def get_instance(cls) -> StandardizationSi:
        """获取单例实例"""
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    # ==================== 命名规范检查 ====================

    def check_naming_conventions(
        self,
        project_root: Path | str,
        language: LanguageConvention = LanguageConvention.PYTHON,
        extensions: list[str] | None = None,
    ) -> list[NamingViolation]:
        """
        检查项目中的命名规范合规性

        Args:
            project_root: 项目根目录路径
            language: 目标语言约定
            extensions: 要检查的文件扩展名列表

        Returns:
            违规列表
        """
        root = Path(project_root)
        rules = _NAMING_RULES.get(language, {})
        if not rules:
            raise CheckError(f"不支持的语言约定: {language.value}")

        ext_map: dict[LanguageConvention, list[str]] = {
            LanguageConvention.PYTHON: [".py"],
            LanguageConvention.JAVASCRIPT: [".js", ".jsx", ".mjs", ".cjs"],
            LanguageConvention.TYPESCRIPT: [".ts", ".tsx"],
            LanguageConvention.GO: [".go"],
            LanguageConvention.JAVA: [".java"],
            LanguageConvention.SQL: [".sql"],
        }
        target_exts = extensions or ext_map.get(language, [])

        self._naming_violations.clear()

        for ext in target_exts:
            for fpath in root.rglob(f"*{ext}"):
                if any(part.startswith(".") and part not in {".vscode", ".github"} for part in fpath.parts):
                    continue
                try:
                    content = fpath.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                violations = self._check_file_naming(content, str(fpath), language, rules)
                self._naming_violations.extend(violations)

        self._report.naming_score = self._calc_naming_score()
        self._report.violations = self._naming_violations
        return self._naming_violations

    def _check_file_naming(
        self,
        content: str,
        filepath: str,
        language: LanguageConvention,
        rules: dict[str, NamingRule],
    ) -> list[NamingViolation]:
        """检查单个文件的命名规范"""
        violations: list[NamingViolation] = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            match language:
                case LanguageConvention.PYTHON:
                    class_match = re.match(r'^class\s+(\w+)', stripped)
                    func_match = re.match(r'^(?:async\s+)?def\s+(\w+)', stripped)
                    var_assign = re.match(r'^(\w+)\s*=', stripped)
                    const_match = re.match(r'^([A-Z][A-Z0-9_]*)\s*=\s*', stripped)
                    import_as_match = re.match(r'^import\s+\w+\s+as\s+(\w+)', stripped)
                    from_import_match = re.match(r'^from\s+\w+\s+import\s+(.+)', stripped)

                    if class_match:
                        name = class_match.group(1)
                        rule = rules.get("class_pascal_case")
                        if rule and not re.match(rule.pattern, name):
                            violations.append(NamingViolation(
                                file_path=filepath, line_number=line_num,
                                violation_type="class_naming", actual_name=name,
                                expected_pattern="PascalCase (如UserService)",
                                suggestion=f"建议改为: {''.join(word.capitalize() for word in re.sub(r'(?<=[a-z])(?=[A-Z])|_', ' ', name).split())}",
                                severity=rule.severity,
                            ))

                    elif func_match:
                        name = func_match.group(1)
                        if name.startswith("__") and name.endswith("__"):
                            continue
                        rule = rules.get("module_snake_case")
                        if rule and not re.match(rule.pattern, name):
                            is_private = name.startswith("_")
                            private_rule = rules.get("private_underscore")
                            if is_private and private_rule and re.match(private_rule.pattern, name):
                                pass
                            elif not re.match(r"^[a-z][a-z0-9_]*$", name):
                                violations.append(NamingViolation(
                                    file_path=filepath, line_number=line_num,
                                    violation_type="function_naming", actual_name=name,
                                    expected_pattern="snake_case (如 get_user_by_id)",
                                    severity=rule.severity,
                                ))

                    elif const_match and const_match.group(1):
                        name = const_match.group(1)
                        rule = rules.get("constant_upper_snake")
                        if rule and not re.match(rule.pattern, name):
                            violations.append(NamingViolation(
                                file_path=filepath, line_number=line_num,
                                violation_type="constant_naming", actual_name=name,
                                expected_pattern="UPPER_SNAKE_CASE (如 MAX_CONNECTIONS)",
                                severity=rule.severity,
                            ))

                case LanguageConvention.JAVASCRIPT | LanguageConvention.TYPESCRIPT:
                    class_match = re.match(r'^(?:export\s+)?(?:class|interface|type|enum)\s+(\w+)', stripped)
                    func_match = re.match(r'(?:const|let|var|function|async function)\s+(\w+)', stripped)
                    component_match = re.match(r'(?:export\s+)?(?:default\s+)?function\s+(\w+)|([A-Z]\w*)\s*(?:=\s*(?:\(|async)|extends|:.*React\.)', stripped)

                    if class_match or component_match:
                        name = (class_match or component_match).group(1) or (component_match.group(2) if component_match and len(component_match.groups()) > 1 else "")
                        if name:
                            rule = rules.get("class_pascal_case")
                            if rule and not re.match(rule.pattern, name):
                                violations.append(NamingViolation(
                                    file_path=filepath, line_number=line_num,
                                    violation_type="component_class_naming", actual_name=name,
                                    expected_pattern="PascalCase (如 UserService)",
                                    severity=rule.severity,
                                ))

                    elif func_match:
                        name = func_match.group(1)
                        if name != name[0].upper() + name[1:]:
                            rule = rules.get("var_camel_case")
                            if rule and not re.match(rule.pattern, name):
                                violations.append(NamingViolation(
                                    file_path=filepath, line_number=line_num,
                                    violation_type="variable_function_naming", actual_name=name,
                                    expected_pattern="camelCase (如 getUserById)",
                                    severity=rule.severity,
                                ))

                case LanguageConvention.GO:
                    type_match = re.match(r'^type\s+(\w+)\s+', stripped)
                    func_match = re.match(r'^func\s+(\w+)\s*\(', stripped)
                    var_match = re.match(r'^(?:var|const)\s+(\w+)', stripped)
                    struct_field_match = re.match(r'^\s+(\w+)\s+\w+', stripped)

                    if type_match:
                        name = type_match.group(1)
                        rule = rules.get("exported_pascal")
                        if rule and not re.match(r"^[A-Z]", name):
                            violations.append(NamingViolation(
                                file_path=filepath, line_number=line_num,
                                violation_type="type_naming", actual_name=name,
                                expected_pattern="PascalCase (首字母大写导出)",
                                severity=rule.severity,
                            ))

                    elif func_match:
                        name = func_match.group(1)
                        if re.match(r"^[A-Z]", name):
                            rule = rules.get("exported_pascal")
                            pass
                        else:
                            rule = rules.get("unexported_camel")
                            if rule and not re.match(rule.pattern, name):
                                violations.append(NamingViolation(
                                    file_path=filepath, line_number=line_num,
                                    violation_type="func_naming", actual_name=name,
                                    expected_pattern="camelCase (首字母小写非导出)",
                                    severity=rule.severity,
                                ))

                case LanguageConvention.SQL:
                    table_create = re.match(r'^CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"]?(\w+)[`"]?', stripped, re.IGNORECASE)
                    column_def = re.match(r'^\s+[`"]?(\w+)[`"]?\s+(?:INT|BIGINT|SMALLINT|TINYINT|VARCHAR|TEXT|CHAR|BOOLEAN|BOOL|DATE|DATETIME|TIMESTAMP|DECIMAL|FLOAT|DOUBLE|ENUM|JSON|JSONB|UUID|BYTEA|BLOB|INET)', stripped, re.IGNORECASE)

                    if table_create:
                        name = table_create.group(1)
                        rule = rules.get("table_snake_case")
                        if rule and not re.match(rule.pattern, name):
                            violations.append(NamingViolation(
                                file_path=filepath, line_number=line_num,
                                violation_type="table_naming", actual_name=name,
                                expected_pattern="snake_case 复数 (如 users, order_items)",
                                severity=rule.severity,
                            ))
                    elif column_def:
                        name = column_def.group(1)
                        rule = rules.get("column_snake_case")
                        if rule and not re.match(rule.pattern, name):
                            violations.append(NamingViolation(
                                file_path=filepath, line_number=line_num,
                                violation_type="column_naming", actual_name=name,
                                expected_pattern="snake_case (如 user_id, created_at)",
                                severity=rule.severity,
                            ))

        return violations

    # ==================== 目录结构检查 ====================

    def check_directory_structure(
        self,
        project_root: Path | str,
        project_type: str = "python",
    ) -> DirectoryStructure:
        """
        检查目录结构是否符合标准约定

        Args:
            project_root: 项目根目录
            project_type: 项目类型 (python/javascript/go/java/general)

        Returns:
            DirectoryStructure对象
        """
        root = Path(project_root)
        expected = _STANDARD_DIRS.get(project_type, _STANDARD_DIRS["general"])

        existing: list[str] = []
        missing: list[str] = []
        extra: list[str] = []

        for d in expected:
            full_path = root / d
            if full_path.exists():
                rel = str(full_path.relative_to(root)).replace("\\", "/") + ("/" if full_path.is_dir() else "")
                existing.append(rel)
            else:
                missing.append(d)

        if root.is_dir():
            for item in root.iterdir():
                rel_item = str(item.relative_to(root)).replace("\\", "/")
                rel_with_slash = rel_item + ("/" if item.is_dir() else "")
                if rel_with_slash not in expected and rel_item not in expected:
                    if not item.name.startswith("."):
                        extra.append(rel_with_slash)

        compliance = len(existing) / max(len(expected), 1) * 100

        result = DirectoryStructure(
            expected_dirs=expected,
            existing_dirs=existing,
            missing_dirs=missing,
            extra_dirs=extra,
            compliance_score=compliance,
        )
        self._directory_result = result
        self._report.directory_score = min(compliance, 100)
        return result

    # ==================== 编码检查 ====================

    def check_file_encodings(
        self,
        project_root: Path | str,
        extensions: list[str] | None = None,
    ) -> list[EncodingCheck]:
        """
        检查项目文件编码

        Args:
            project_root: 项目根目录
            extensions: 要检查的扩展名列表

        Returns:
            EncodingCheck结果列表
        """
        root = Path(project_root)
        target_exts = extensions or [".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".rs", ".md", ".yml", ".yaml", ".json", ".html", ".css"]
        self._encoding_results.clear()

        source_code_exts = set(target_exts) - {".md"}
        for ext in source_code_exts:
            for fpath in sorted(root.rglob(f"*{ext}"))[:50]:
                if fpath.is_file() and fpath.stat().st_size < 10 * 1024 * 1024:
                    try:
                        raw_bytes = fpath.read_bytes()
                        has_bom = raw_bytes[:3] == b'\xef\xbb\xbf'
                        issues: list[str] = []
                        enc = "utf-8-sig" if has_bom else "utf-8"

                        if has_bom:
                            issues.append("检测到UTF-8 BOM标记（源码文件不应有BOM）")

                        non_ascii = sum(1 for b in raw_bytes if b > 127)
                        ratio = non_ascii / max(len(raw_bytes), 1)
                        if ratio > 0.3 and not has_bom:
                            try:
                                raw_bytes.decode("gbk")
                                issues.append(f"可能是GBK编码（非UTF-8），非ASCII字符占比{ratio:.0%}")
                            except UnicodeDecodeError:
                                pass

                        self._encoding_results.append(EncodingCheck(
                            file_path=str(fpath.relative_to(root)),
                            encoding=enc,
                            has_bom=has_bom,
                            is_utf8=True,
                            issues=issues,
                        ))
                    except Exception as e:
                        self._encoding_results.append(EncodingCheck(
                            file_path=str(fpath.relative_to(root)),
                            encoding="unknown",
                            issues=[f"读取失败: {str(e)[:60]}"],
                        ))

        problem_files = [e for e in self._encoding_results if e.issues]
        self._report.encoding_score = max(0, 100 - len(problem_files) * 5)
        return self._encoding_results

    # ==================== 版权声明检查 ====================

    def check_copyright_headers(
        self,
        project_root: Path | str,
        extensions: list[str] | None = None,
    ) -> list[CopyrightHeader]:
        """
        检查文件头的SPDX许可证声明

        Args:
            project_root: 项目根目录
            extensions: 要检查的扩展名列表

        Returns:
            CopyrightHeader结果列表
        """
        root = Path(project_root)
        target_exts = extensions or [".py", ".js", ".ts", ".go", ".java", ".rs"]
        self._copyright_results.clear()

        for ext in target_exts:
            for fpath in sorted(root.rglob(f"*{ext}"))[:30]:
                if not fpath.is_file():
                    continue
                try:
                    first_lines = []
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        for _ in range(5):
                            line = f.readline()
                            if line:
                                first_lines.append(line.rstrip())
                            else:
                                break
                except Exception:
                    continue

                header_text = "\n".join(first_lines)
                spdx_match = _SPDX_LICENSE_PATTERN.search(header_text)
                issues: list[str] = []

                has_header = bool(first_lines and (
                    "copyright" in header_text.lower() or
                    "license" in header_text.lower() or
                    "spdx" in header_text.lower() or
                    header_text.lstrip().startswith("#") or
                    header_text.lstrip().startswith("//") or
                    header_text.lstrip().startswith("/*") or
                    header_text.lstrip().startswith("*")
                ))

                license_id = spdx_match.group(1) if spdx_match else ""

                year_match = re.search(r'(?:Copyright|©|\(c\))\s*(?:\(c\))?\s*(\d{4}(?:-\d{4})?)', header_text, re.IGNORECASE)
                year = year_match.group(1) if year_match else ""

                holder_match = re.search(r'(?:Copyright|©|\(c\))\s*(?:\(c\))?\s*\d{4}(?:-\d{4})?\s+(.+?)(?:\.\s|$|All\s)', header_text, re.IGNORECASE)
                holder = holder_match.group(1).strip()[:40] if holder_match else ""

                if not has_header:
                    issues.append("缺少版权/许可声明头")
                elif not spdx_match:
                    issues.append("缺少SPDX-License-Identifier标识")

                valid_spdx = bool(spdx_match)

                known_licenses = {"MIT", "Apache-2.0", "GPL-3.0-or-later", "LGPL-3.0-or-later",
                                  "BSD-2-Clause", "BSD-3-Clause", "ISC", "AGPL-3.0-or-later", "0BSD"}
                if license_id and license_id.split()[0] not in known_licenses:
                    issues.append(f"许可证 '{license_id}' 可能不是标准的SPDX标识")

                self._copyright_results.append(CopyrightHeader(
                    file_path=str(fpath.relative_to(root)),
                    has_header=has_header,
                    header_format="#" if first_lines and first_lines[0].lstrip().startswith("#") else "//",
                    license_id=license_id,
                    year=year,
                    holder=holder,
                    is_valid_spdx=valid_spdx,
                    issues=issues,
                ))
                except Exception as e:
                    pass

        files_with_header = sum(1 for c in self._copyright_results if c.has_header)
        files_valid = sum(1 for c in self._copyright_results if c.is_valid_spdx)
        total = max(len(self._copyright_results), 1)
        self._report.copyright_score = (files_with_header / total * 50 + files_valid / total * 50)
        return self._copyright_results

    # ==================== .gitignore 检查 ====================

    def check_gitignore(
        self,
        project_root: Path | str,
    ) -> GitignoreCheck:
        """
        检查.gitignore完整性

        Args:
            project_root: 项目根目录

        Returns:
            GitignoreCheck对象
        """
        root = Path(project_root)
        gitignore_path = root / ".gitignore"

        present: list[str] = []
        missing: list[str] = []

        if gitignore_path.exists():
            content = gitignore_path.read_text(encoding="utf-8", errors="replace")
            present = [line.strip() for line in content.splitlines()
                       if line.strip() and not line.strip().startswith("#")]
        else:
            missing = list(_GITIGNORE_ESSENTIAL[:10])

        essential_set = set(_GITIGNORE_ESSENTIAL)
        present_set = set(present)

        for entry in _GITIGNORE_ESSENTIAL:
            normalized_entry = entry.rstrip("/")
            found = False
            for p in present:
                p_normalized = p.rstrip("/")
                if p_normalized == normalized_entry or \
                   (p_normalized.endswith("*") and normalized_entry.startswith(p_normalized[:-1])) or \
                   (normalized_entry.endswith("/") and p_normalized.startswith(normalized.rstrip("/"))):
                    found = True
                    break
            if not found:
                missing.append(entry)

        unnecessary = [p for p in present if p in {".DS_Store", "Thumbs.db"} and not any(d.name == ".DS_Store" for d in root.iterdir() if d.is_dir())]

        compliance = (len(present_set & essential_set) / max(len(essential_set), 1)) * 100

        result = GitignoreCheck(
            file_exists=gitignore_path.exists(),
            missing_entries=missing,
            present_entries=present,
            unnecessary_entries=unnecessary,
            compliance_pct=compliance,
        )
        self._gitignore_result = result
        self._report.gitignore_score = min(compliance + (20 if gitignore_path.exists() else 0), 100)
        return result

    # ==================== EditorConfig 检查 ====================

    def check_editorconfig(
        self,
        project_root: Path | str,
    ) -> EditorConfigCheck:
        """
        检查.editorconfig合规性

        Args:
            project_root: 项目根目录

        Returns:
            EditorConfigCheck对象
        """
        root = Path(project_root)
        editorconfig_path = root / ".editorconfig"
        recommended_keys = {
            "root": "true",
            "charset": "utf-8",
            "end_of_line": "lf",
            "indent_style": "space",
            "indent_size": "4",
            "trim_trailing_whitespace": "true",
            "insert_final_newline": "true",
        }
        checked: list[dict[str, Any]] = []
        missing_rec: list[str] = []
        violations: list[dict[str, Any]] = []

        if editorconfig_path.exists():
            content = editorconfig_path.read_text(encoding="utf-8", errors="replace")
            in_section = False
            current_section = "global"
            section_values: dict[str, str] = {}

            for line in content.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if stripped.startswith("["):
                    if current_section != "global":
                        checked.append({"section": current_section, "values": dict(section_values)})
                    current_section = stripped
                    section_values = {}
                    in_section = True
                elif "=" in stripped:
                    key, _, val = stripped.partition("=")
                    section_values[key.strip()] = val.strip()

            if current_section != "global":
                checked.append({"section": current_section, "values": dict(section_values)})

            global_values: dict[str, str] = {}
            for item in checked:
                if item["section"] in ("[*]", "[*.{js,ts,py,go,java,rs}]"):
                    global_values.update(item["values"])
                if item["section"] == "[*]":
                    global_values.update(item["values"])

            for key, recommended_val in recommended_keys.items():
                if key not in global_values:
                    missing_rec.append(key)
                else:
                    actual_val = global_values[key]
                    if key == "indent_style" and actual_val not in ("space", "tab"):
                        violations.append({"key": key, "expected": recommended_val, "actual": actual_val})
                    elif key == "charset" and actual_val.lower() not in ("utf-8", "utf8"):
                        violations.append({"key": key, "expected": recommended_val, "actual": actual_val})
                    elif key == "end_of_line" and actual_val.lower() not in ("lf", "crlf", "cr"):
                        violations.append({"key": key, "expected": recommended_val, "actual": actual_val})

            score = max(0, 100 - len(missing_rec) * 10 - len(violations) * 15)
        else:
            missing_rec = list(recommended_keys.keys())
            score = 0

        result = EditorConfigCheck(
            file_exists=editorconfig_path.exists(),
            checked_keys=checked,
            missing_recommended=missing_rec,
            violations=violations,
            score=min(score, 100),
        )
        self._editorconfig_result = result
        self._report.editorconfig_score = result.score
        return result

    # ==================== 综合评分 ====================

    def _calc_naming_score(self) -> float:
        if not self._naming_violations:
            return 100.0
        error_count = sum(1 for v in self._naming_violations if v.severity == "error")
        warning_count = sum(1 for v in self._naming_violations if v.severity == "warning")
        deduction = error_count * 5 + warning_count * 2
        return max(0, 100 - deduction)

    def run_full_check(
        self,
        project_root: Path | str,
        project_name: str = "",
        language: LanguageConvention = LanguageConvention.PYTHON,
        project_type: str = "python",
    ) -> StandardizationReport:
        """
        执行完整的标准化检查

        Args:
            project_root: 项目根目录
            project_name: 项目名称
            language: 主语言
            project_type: 项目类型

        Returns:
            StandardizationReport综合报告
        """
        self._report = StandardizationReport(project_name=project_name or Path(project_root).name)

        self.check_naming conventions(project_root, language)
        self.check_directory_structure(project_root, project_type)
        self.check_file_encodings(project_root)
        self.check_copyright_headers(project_root)
        self.check_gitignore(project_root)
        self.check_editorconfig(project_root)

        weights = {"naming": 25, "directory": 15, "encoding": 10, "copyright": 15, "gitignore": 15, "editorconfig": 20}
        self._report.total_score = (
            self._report.naming_score * weights["naming"] / 100 +
            self._report.directory_score * weights["directory"] / 100 +
            self._report.encoding_score * weights["encoding"] / 100 +
            self._report.copyright_score * weights["copyright"] / 100 +
            self._report.gitignore_score * weights["gitignore"] / 100 +
            self._report.editorconfig_score * weights["editorconfig"] / 100
        )

        self._report.details = {
            "naming_violations": len(self._naming_violations),
            "encoding_issues": sum(1 for e in self._encoding_results if e.issues),
            "copyright_issues": sum(1 for c in self._copyright_results if c.issues),
            "directory_missing": self._directory_result.missing_dirs if self._directory_result else [],
            "gitignore_missing": self._gitignore_result.missing_entries if self._gitignore_result else [],
            "editorconfig_issues": self._editorconfig_result.violations if self._editorconfig_result else [],
        }

        return self._report

    @property
    def report(self) -> StandardizationReport:
        return self._report

    @property
    def violation_count(self) -> int:
        return len(self._naming_violations)

    def __repr__(self) -> str:
        return (
            f"StandardizationSi(score={self._report.total_score:.1f}, "
            f"grade={self._report.grade()}, "
            f"violations={self.violation_count})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 标准化司测试")
    print("=" * 60)

    si = StandardizationSi()

    test_dir = Path(__file__).parent.parent.parent.parent

    print("\n--- Python 命名规范检查 ---")
    py_violations = si.check_naming_conventions(test_dir, LanguageConvention.PYTHON)
    print(f"   检测到 {len(py_violations)} 个潜在违规:")
    for v in py_violations[:10]:
        icon = {"error": "🔴", "warning": "🟡", "info": "ℹ️"}.get(v.severity, "•")
        fname = v.file_path.split("/")[-1] if "/" in v.file_path else v.file_path
        print(f"   {icon} {fname}:{v.line_number} `{v.actual_name}` → {v.suggestion or v.expected_pattern}")

    print("\n--- JavaScript 命名规范检查 ---")
    js_violations = si.check_naming_conventions(test_dir, LanguageConvention.JAVASCRIPT)
    print(f"   JS违规数: {len(js_violations)}")

    print("\n--- Go 命名规范检查 ---")
    go_violations = si.check_naming_conventions(test_dir, LanguageConvention.GO)
    print(f"   Go违规数: {len(go_violations)}")

    print("\n--- SQL 命名规范检查 ---")
    sql_violations = si.check_naming_conventions(test_dir, LanguageConvention.SQL)
    print(f"   SQL违规数: {len(sql_violations)}")

    print("\n--- 目录结构检查 ---")
    dir_result = si.check_directory_structure(test_dir, project_type="general")
    print(f"   存在: {len(dir_result.existing_dirs)}, 缺失: {len(dir_result.missing_dirs)}")
    if dir_result.missing_dirs:
        print(f"   缺失目录: {dir_result.missing_dirs}")
    if dir_result.extra_dirs:
        print(f"   额外目录({len(dir_result.extra_dirs)}): {dir_result.extra_dirs[:5]}")
    print(f"   合规率: {dir_result.compliance_score:.1f}%")

    print("\n--- 文件编码检查 ---")
    enc_results = si.check_file_encodings(test_dir)
    problem_enc = [e for e in enc_results if e.issues]
    print(f"   检查了 {len(enc_results)} 个文件, 问题文件: {len(problem_enc)}")
    for e in problem_enc[:5]:
        print(f"      ⚠️ {e.file_path}: {e.issues[0][:50]}")

    print("\n--- 版权声明检查 ---")
    copyright_results = si.check_copyright_headers(test_dir)
    with_header = sum(1 for c in copyright_results if c.has_header)
    valid SPDX = sum(1 for c in copyright_results if c.is_valid_spdx)
    print(f"   检查了 {len(copyright_results)} 个文件")
    print(f"   有声明头: {with_header}, 有效SPDX: {valid_SPDX}")
    no_header = [c for c in copyright_results if not c.has_header]
    if no_header:
        print(f"   无声明头 ({len(no_header)}个): {[c.file_path.split('/')[-1] for c in no_header[:5]]}")

    print("\n--- .gitignore 检查 ---")
    gi_result = si.check_gitignore(test_dir)
    print(f"   文件存在: {'✅' if gi_result.file_exists else '❌'}")
    print(f"   覆盖项: {len(gi_result.present_entries)}/{len(_GITIGNORE_ESSENTIAL)}")
    print(f"   合规率: {gi_result.compliance_pct:.1f}%")
    if gi_result.missing_entries:
        print(f"   缺失项 ({len(gi_result.missing_entries)}): {gi_result.missing_entries[:8]}")

    print("\n--- EditorConfig 检查 ---")
    ec_result = si.check_editorconfig(test_dir)
    print(f"   文件存在: {'✅' if ec_result.file_exists else '❌'}")
    print(f"   检查配置段: {len(ec_result.checked_keys)}")
    print(f"   缺失推荐项: {ec_result.missing_recommended}")
    print(f"   违规项: {len(ec_result.violations)}")
    print(f"   得分: {ec_result.score:.1f}")

    print("\n--- 综合评分 ---")
    report = si.report
    print(f"   各维度得分:")
    print(f"      命名规范:     {report.naming_score:.1f}/100")
    print(f"      目录结构:     {report.directory_score:.1f}/100")
    print(f"      文件编码:     {report.encoding_score:.1f}/100")
    print(f"      版权声明:     {report.copyright_score:.1f}/100")
    print(f"      .gitignore:   {report.gitignore_score:.1f}/100")
    print(f"      EditorConfig: {report.editorconfig_score:.1f}/100")
    print(f"\n   📊 总分: **{report.total_score:.1f}** / 100 → 等级: **{report.grade()}**")

    md_report = report.to_markdown()
    print(f"\n--- Markdown报告预览 (前1200字符) ---\n{md_report[:1200]}")

    print("\n✅ 所有测试通过!")
