"""
环境变量模板生成器模块 - EnvTemplateGenerator

自动扫描项目源代码中的环境变量使用模式，生成 .env.example 模板文件
和 Markdown 参考文档，帮助团队规范化环境变量管理。
无外部依赖，纯Python标准库实现。
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class VarCategory(Enum):
    """环境变量分类枚举"""

    REQUIRED = "required"
    OPTIONAL = "optional"
    SECRET = "secret"


@dataclass
class EnvVariable:
    """单个环境变量条目数据类"""

    name: str  # 变量名，如 DATABASE_URL
    category: VarCategory = VarCategory.OPTIONAL
    description: str = ""  # 用途说明
    default_value: Optional[str] = None  # 默认值（如有）
    example_value: str = ""  # 示例值（用于 .env.example）
    found_in_files: list[str] = field(default_factory=list)  # 发现该变量的源码文件列表
    pattern_matched: str = ""  # 匹配到的检测模式描述

    def __repr__(self) -> str:
        return f"EnvVariable(name='{self.name}', category={category.value}, files={len(self.found_in_files)})"


class EnvTemplateGenerator:
    """
    环境变量模板生成器

    功能概述：
    - 扫描源码中7种 os.environ 使用模式
    - 自动识别变量是否为必需/可选/敏感类型
    - 生成结构化的 .env.example 内容
    - 生成完整的 Markdown 环境变量参考文档

    支持的扫描模式：
    1. os.environ["KEY"] / os.environ['KEY']
    2. os.environ.get("KEY")
    3. os.getenv("KEY") / os.getenv("KEY", default)
    4. environ["KEY"] / environ.get("KEY")
    5. os.getenv 的链式调用 (os.getenv(..., os.getenv(...)))
    6. 环境变量在字符串格式化中的引用 (f"...{os.getenv...}")
    7. @value / @ConfigurationProperties 风格的注解引用（Java 兼容）

    使用示例：
        gen = EnvTemplateGenerator()
        variables = gen.scan_project(Path("./src"))
        example_content = gen.generate_example(variables)
        docs = gen.generate_documentation(variables)
    """

    _SCAN_PATTERNS: list[tuple[re.Pattern, str, VarCategory]] = []

    _SENSITIVE_KEYWORDS: set[str] = set()

    _REQUIRED_KEYWORDS: set[str] = set()

    @classmethod
    def _get_patterns(cls) -> list[tuple[re.Pattern, str, VarCategory]]:
        """
        返回7种环境变量检测模式列表

        每个模式为三元组: (编译后的正则, 模式描述, 默认分类)
        """
        if cls._SCAN_PATTERNS:
            return cls._SCAN_PATTERNS

        patterns = [
            (
                re.compile(r"""os\.environ\(\s*['"]([^'"]+)['"]\s*\)"""),
                "os.environ('KEY') 方括号索引访问",
                VarCategory.REQUIRED,
            ),
            (
                re.compile(r"""os\.environ\[['"]([^'"]+)['"]\]"""),
                "os.environ['KEY'] 字典式访问",
                VarCategory.REQUIRED,
            ),
            (
                re.compile(r"""os\.environ\.get\(\s*['"]([^'"]+)['"]"""),
                "os.environ.get('KEY') 安全获取",
                VarCategory.OPTIONAL,
            ),
            (
                re.compile(r"""os\.getenv\(\s*['"]([^'"]+)['"](?:\s*,\s*[^)]*)?\)"""),
                "os.getenv('KEY', default) 获取",
                VarCategory.OPTIONAL,
            ),
            (
                re.compile(r"""(?<![\w])environ(?:\.get)?\(\s*['"]([^'"]+)['"]"""),
                "environ.get('KEY') / environ('KEY') 简写访问",
                VarCategory.OPTIONAL,
            ),
            (
                re.compile(r"""os\.getenv\([^)]*os\.getenv\("""),
                "os.getenv 链式嵌套调用（回退模式）",
                VarCategory.OPTIONAL,
            ),
            (
                re.compile(r"""@Value\s*\(\s*['"]\$\{([^}]+)\}['"]\)"""),
                "@Value('${KEY}') Spring 注解风格",
                VarCategory.OPTIONAL,
            ),
        ]

        cls._SCAN_PATTERNS = patterns
        return patterns

    @classmethod
    def _get_sensitive_keywords(cls) -> set[str]:
        """返回用于判定敏感变量的关键字集合"""
        if cls._SENSITIVE_KEYWORDS:
            return cls._SENSITIVE_KEYWORDS
        keywords = {
            "password", "passwd", "pwd", "secret", "api_key", "apikey",
            "token", "private_key", "credential", "encryption", "jwt",
            "webhook_secret", "signing_key", "master_key", "client_secret",
            "access_key", "aws_secret", "oauth", "auth_token",
        }
        cls._SENSITIVE_KEYWORDS = keywords
        return keywords

    @classmethod
    def _get_required_keywords(cls) -> set[str]:
        """返回用于判定必需变量的关键字集合"""
        if cls._REQUIRED_KEYWORDS:
            return cls._REQUIRED_KEYWORDS
        keywords = {
            "database_url", "db_url", "db_host", "connection_string",
            "redis_url", "mongo_url", "app_port", "host", "port",
            "server_url", "base_url", "endpoint", "dsn",
        }
        cls._REQUIRED_KEYWORDS = keywords
        return keywords

    def __init__(self):
        """初始化模板生成器"""
        self._patterns = self._get_patterns()
        self._sensitive_kw = self._get_sensitive_keywords()
        self._required_kw = self._get_required_keywords()

    def scan_project(self, project_path: Path) -> list[EnvVariable]:
        """
        扫描项目目录中所有源码文件的环境变量使用情况

        支持的文件扩展名：
        .py .js .ts .jsx .tsx .java .go .rs .rb .php .cs .vue .yaml .yml .json .sh .bat .ps1

        自动跳过：node_modules, .git, __pycache__, dist, build, venv, vendor 等

        Args:
            project_path: 项目根目录路径

        Returns:
            去重后的 EnvVariable 列表，按变量名排序
        """
        extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
            ".rb", ".php", ".cs", ".vue", ".yaml", ".yml", ".json",
            ".sh", ".bat", ".ps1", ".toml",
        }
        skip_dirs = {
            "__pycache__", ".git", "node_modules", "dist", "build",
            ".venv", "venv", "vendor", ".tox", ".mypy_cache", ".cache",
            ".next", ".nuxt", "target", "bin", "obj",
        }

        variables_map: dict[str, EnvVariable] = {}

        if not project_path.is_dir():
            return []

        all_files = sorted(project_path.rglob("*"))
        source_files = [
            f for f in all_files
            if f.is_file() and f.suffix.lower() in extensions
            and not any(skip in f.parts for skip in skip_dirs)
        ]

        for file_path in source_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                rel_path = str(file_path.relative_to(project_path))
                file_vars = self._extract_from_content(content)

                for var_name, pattern_desc in file_vars:
                    if var_name not in variables_map:
                        var_entry = EnvVariable(
                            name=var_name,
                            pattern_matched=pattern_desc,
                            found_in_files=[rel_path],
                        )
                        var_entry.category = self._classify_variable(var_name)
                        variables_map[var_name] = var_entry
                    else:
                        existing = variables_map[var_name]
                        if rel_path not in existing.found_in_files:
                            existing.found_in_files.append(rel_path)
                        if pattern_desc and not existing.pattern_matched:
                            existing.pattern_matched = pattern_desc
            except Exception:
                continue

        for var in variables_map.values():
            var.description = self._generate_description(var.name, var.category)

        return sorted(variables_map.values(), key=lambda v: (v.category.value, v.name))

    def generate_example(self, variables: list[EnvVariable]) -> str:
        """
        生成 .env.example 文件内容

        输出格式按 Required → Secret → Optional 三组分组，
        每组内按字母排序，包含注释说明和示例占位符。

        格式示例：
            # ===========================================
            #  Required Variables (必需变量)
            # ===========================================

            # 数据库连接地址 [Required]
            DATABASE_URL=postgresql://user:pass@localhost:5432/mydb

        Args:
            variables: 扫描得到的环境变量列表

        Returns:
            格式化的 .env.example 文件文本内容
        """
        lines = []
        lines.append("# ===========================================")
        lines.append("#  Environment Variables Template (.env.example)")
        lines.append(f"#  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("#  Copy this file to .env and fill in the values")
        lines.append("# ===========================================\n")

        groups = {
            VarCategory.REQUIRED: ("Required Variables (必需变量)", "这些变量必须配置才能正常运行"),
            VarCategory.SECRET: ("Secret Variables (敏感变量)", "包含密钥/密码等敏感信息，请勿提交到版本控制"),
            VarCategory.OPTIONAL: ("Optional Variables (可选变量)", "这些变量有默认值或非必须"),
        }

        for cat, (title, desc) in groups.items():
            group_vars = [v for v in variables if v.category == cat]
            if not group_vars:
                continue

            lines.append(f"# -------------------------------------------")
            lines.append(f"#  {title}")
            lines.append(f"#  {desc}")
            lines.append(f"# -------------------------------------------\n")

            for var in sorted(group_vars, key=lambda v: v.name):
                example = var.example_value or self._generate_example_value(var.name, var.category)
                comment_parts = [f"[{var.category.value.title()}]"]
                if var.description:
                    comment_parts.append(var.description)
                if var.found_in_files:
                    comment_parts.append(f"used in: {', '.join(var.found_in_files[:3])}")

                comment = " | ".join(comment_parts)
                lines.append(f"# {comment}")
                if var.default_value is not None:
                    lines.append(f"{var.name}={var.default_value}")
                else:
                    lines.append(f"{var.name}={example}")
                lines.append("")

        return "\n".join(lines)

    def generate_documentation(self, variables: list[EnvVariable]) -> str:
        """
        生成 Markdown 格式的环境变量参考文档

        文档内容包括：
        - 标题与生成时间
        - 总览统计表（名称、分类、说明、默认值、来源文件）
        - 按类别分组的详细说明
        - 快速开始指南

        Args:
            variables: 扫描得到的环境变量列表

        Returns:
            完整的 Markdown 文档文本
        """
        lines = []
        lines.append("# 🌍 环境变量参考文档\n")
        lines.append(f"> 自动生成于 **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}** | 共 **{len(variables)}** 个变量\n")

        total_required = sum(1 for v in variables if v.category == VarCategory.REQUIRED)
        total_secret = sum(1 for v in variables if v.category == VarCategory.SECRET)
        total_optional = sum(1 for v in variables if v.category == VarCategory.OPTIONAL)

        lines.append("## 📊 总览\n")
        lines.append("| 分类 | 数量 |")
        lines.append("|------|------|")
        lines.append(f"| 🔴 必需 (Required) | {total_required} |")
        lines.append(f"| 🔐 敏感 (Secret) | {total_secret} |")
        lines.append(f"| ⚪ 可选 (Optional) | {total_optional} |")
        lines.append(f"| **合计** | **{len(variables)}** |\n")

        lines.append("## 📋 变量详情\n")
        lines.append("| 变量名 | 分类 | 说明 | 默认值 | 来源文件 |")
        lines.append("|--------|------|------|--------|----------|")

        for var in variables:
            cat_icon = {"required": "🔴", "secret": "🔐", "optional": "⚪"}.get(var.category.value, "")
            default_str = var.default_value or "-"
            files_str = ", ".join(var.found_in_files[:3])
            if len(var.found_in_files) > 3:
                files_str += f" (+{len(var.found_in_files) - 3})"
            lines.append(
                f"| `{var.name}` | {cat_icon} {var.category.value} "
                f"| {var.description or '-'} "
                f"| `{default_str}` "
                f"| {files_str} |"
            )
        lines.append("")

        group_titles = {
            VarCategory.REQUIRED: ("🔴 必需变量 (Required)", "以下变量必须在 `.env` 中配置："),
            VarCategory.SECRET: ("🔐 敏感变量 (Secret)", "以下变量包含敏感信息，请勿提交到版本控制："),
            VarCategory.OPTIONAL: ("⚪ 可选变量 (Optional)", "以下变量有默认值或非运行必需："),
        }

        for cat, (title, intro) in group_titles.items():
            group_vars = [v for v in variables if v.category == cat]
            if not group_vars:
                continue

            lines.append(f"\n## {title}\n")
            lines.append(f"{intro}\n")

            for var in sorted(group_vars, key=lambda v: v.name):
                example = var.example_value or self._generate_example_value(var.name, var.category)
                lines.append(f"### `{var.name}`\n")
                lines.append(f"- **分类**: {var.category.value}")
                if var.description:
                    lines.append(f"- **说明**: {var.description}")
                lines.append(f"- **示例值**: `{example}`")
                if var.default_value is not None:
                    lines.append(f"- **默认值**: `{var.default_value}`")
                if var.found_in_files:
                    lines.append(f"- **使用位置**:")
                    for fp in var.found_in_files:
                        lines.append(f"  - `{fp}`")
                if var.pattern_matched:
                    lines.append(f"- **检测模式**: {var.pattern_matched}")
                lines.append("")

        lines.append("---\n")
        lines.append("## 🚀 快速开始\n")
        lines.append("```bash")
        lines.append("# 1. 复制模板文件")
        lines.append("cp .env.example .env")
        lines.append("")
        lines.append("# 2. 编辑并填入实际值")
        lines.append("nano .env   # 或使用你喜欢的编辑器")
        lines.append("")
        lines.append("# 3. 验证配置（如项目有验证脚本）")
        lines.append("# python check_env.py")
        lines.append("```\n")
        lines.append("> ⚠️ **安全提醒**: 请确保 `.env` 已添加到 `.gitignore` 中！\n")

        return "\n".join(lines)

    def _extract_from_content(self, content: str) -> list[tuple[str, str]]:
        """
        从文件内容中提取所有环境变量引用

        应用全部7种检测模式，返回去重后的 (变量名, 匹配模式描述) 元组列表。

        Args:
            content: 文件原始文本

        Returns:
            [(变量名, 模式描述), ...] 列表
        """
        results: list[tuple[str, str]] = []
        seen: set[str] = set()

        for pattern, description, _ in self._patterns:
            for match in pattern.finditer(content):
                var_name = match.group(1).strip()
                if var_name and var_name not in seen:
                    seen.add(var_name)
                    results.append((var_name, description))

        return results

    def _classify_variable(self, var_name: str) -> VarCategory:
        """
        根据变量名自动分类为 Required / Secret / Optional

        分类规则：
        - 包含敏感关键字的 → SECRET
        - 包含必需关键字的 → REQUIRED
        - 其他 → OPTIONAL

        Args:
            var_name: 环境变量名

        Returns:
            VarCategory 分类枚举值
        """
        lower_name = var_name.lower()

        for kw in self._sensitive_kw:
            if kw in lower_name:
                return VarCategory.SECRET

        for kw in self._required_kw:
            if kw in lower_name:
                return VarCategory.REQUIRED

        return VarCategory.OPTIONAL

    @staticmethod
    def _generate_description(var_name: str, category: VarCategory) -> str:
        """
        根据变量名和分类生成用途说明文字

        Args:
            var_name: 变量名
            category: 已分类的类型

        Returns:
            中文用途说明字符串
        """
        lower = var_name.lower()
        descriptions: dict[str, str] = {}

        if "database" in lower or "db_" in lower or lower.startswith("db"):
            descriptions.update({
                "url": "数据库连接 URL (含协议、主机、端口、凭据)",
                "host": "数据库服务器主机地址",
                "port": "数据库服务端口号",
                "name": "数据库名称",
                "user": "数据库用户名",
                "password": "数据库用户密码",
                "pool_size": "数据库连接池大小",
            })

        if "redis" in lower:
            descriptions.setdefault("", "Redis 连接配置")

        if "api" in lower and "key" in lower:
            descriptions.setdefault("", "第三方 API 访问密钥")

        if "secret" in lower or "key" in lower:
            descriptions.setdefault("", "加密/签名密钥")

        if "token" in lower:
            descriptions.setdefault("", "认证令牌或 OAuth Token")

        if "host" in lower:
            descriptions.setdefault("", "服务主机地址")

        if "port" in lower:
            descriptions.setdefault("", "服务监听端口")

        if "debug" in lower:
            descriptions.setdefault("", "调试模式开关 (true/false)")

        if "log" in lower and "level" in lower:
            descriptions.setdefault("", "日志级别 (DEBUG/INFO/WARN/ERROR)")

        suffixes = ["_url", "_uri", "_host", "_port", "_key", "_secret", "_token", "_password", "_passwd", "_pwd"]
        for suf in suffixes:
            if lower.endswith(suf):
                key_part = lower[: -len(suf)]
                base_desc = descriptions.get(key_part, "") or descriptions.get(suf.lstrip("_"), "")
                if base_desc:
                    return base_desc

        fallback_by_category = {
            VarCategory.SECRET: "敏感凭据信息（密钥/密码/Token）",
            VarCategory.REQUIRED: "运行必需的配置参数",
            VarCategory.OPTIONAL: "可选的功能开关或配置项",
        }

        return descriptions.get("") or fallback_by_category.get(category, "")

    @staticmethod
    def _generate_example_value(var_name: str, category: VarCategory) -> str:
        """
        为指定变量生成合理的示例占位值

        根据变量名后缀和分类推断值的格式，生成安全的示例值。

        Args:
            var_name: 变量名
            variable: 变量分类

        Returns:
            示例值字符串
        """
        lower = var_name.lower()

        url_indicators = ("_url", "_uri", "connection", "dsn", "endpoint")
        host_indicators = ("_host", "host")
        port_indicators = ("_port", "port")
        bool_indicators = ("debug", "enabled", "verbose", "mock", "test", "ssl", "tls")
        level_indicators = ("log_level", "loglevel", "logging")

        for ind in url_indicators:
            if ind in lower:
                if "redis" in lower:
                    return "redis://localhost:6379/0"
                if "mongo" in lower or "mongodb" in lower:
                    return "mongodb://localhost:27017/mydb"
                if "postgres" in lower or "pg_" in lower or "database" in lower:
                    return "postgresql://user:pass@localhost:5432/mydb"
                if "mysql" in lower:
                    return "mysql://user:pass@localhost:3306/mydb"
                return "https://example.com/api"

        for ind in host_indicators:
            if ind in lower:
                return "localhost"

        for ind in port_indicators:
            if ind in lower:
                return "8080"

        for ind in bool_indicators:
            if ind in lower:
                return "false"

        for ind in level_indicators:
            if ind in lower:
                return "INFO"

        if category == VarCategory.SECRET:
            return "change-me-to-a-secure-value"

        if category == VarCategory.REQUIRED:
            return "<please-fill-in>"

        return ""

    def __repr__(self) -> str:
        return f"EnvTemplateGenerator(patterns={len(self._patterns)})"
