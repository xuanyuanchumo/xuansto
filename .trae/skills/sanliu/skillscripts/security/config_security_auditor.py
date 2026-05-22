"""
配置安全审计器模块 - ConfigSecurityAuditor

审计 YAML/JSON 配置文件中的敏感字段暴露风险，检查文件权限合规性，
验证 .gitignore 规则是否覆盖了敏感文件，并评估加密存储方案。
无外部依赖，纯Python标准库实现。
"""

import json
import os
import re
import stat
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class AuditResult:
    """配置文件审计结果数据类"""

    file_path: Path
    is_valid: bool = True
    total_checks: int = 0
    passed: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)
    scanned_at: datetime = field(default_factory=datetime.now)

    def summary(self) -> str:
        status = "✅ 通过" if self.is_valid else "⚠ 发现问题"
        return (
            f"[{self.file_path.name}] {status} | "
            f"检查:{self.total_checks} 通过:{self.passed} "
            f"警告:{len(self.warnings)} 错误:{len(self.errors)}"
        )


@dataclass
class PermissionResult:
    """文件权限检查结果数据类"""

    file_path: Path
    is_secure: bool = True
    file_mode_octal: str = ""
    owner_readable: bool = True
    group_readable: bool = False
    others_readable: bool = False
    is_executable: bool = False
    recommendations: list[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "🔒 安全" if self.is_secure else "⚠ 权限过宽"
        return f"{status} | 模式:{self.file_mode_octal} | owner_r:{self.owner_readable} group_r:{self.group_readable} others_r:{self.others_readable}"


@dataclass
class GitignoreResult:
    """.gitignore 合规性验证结果数据类"""

    gitignore_path: Optional[Path]
    is_compliant: bool = True
    missing_patterns: list[str] = field(default_factory=list)
    existing_patterns: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    score: int = 100

    def summary(self) -> str:
        status = "✅ 合规" if self.is_compliant else "❌ 不合规"
        return (
            f"{status} | 得分:{self.score}/100 | "
            f"缺失规则:{len(self.missing_patterns)} | 现有规则:{len(self.existing_patterns)}"
        )


@dataclass
class EncryptionRecommendation:
    """加密存储评估建议数据类"""

    has_encrypted_fields: bool = False
    encryption_method: str = ""
    risk_level: str = "unknown"
    recommendations: list[str] = field(default_factory=list)
    encrypted_keys: list[str] = field(default_factory=list)
    plaintext_keys: list[str] = field(default_factory=list)


class ConfigSecurityAuditor:
    """
    配置安全审计器

    功能概述：
    - 审计 YAML/JSON 配置文件中的17种敏感字段模式
    - 检查敏感文件的操作系统权限（Unix权限位）
    - 验证 .gitignore 是否覆盖11种敏感文件模式
    - 评估配置中密钥的加密存储状态并给出改进建议

    使用示例：
        auditor = ConfigSecurityAuditor()
        result = auditor.audit_config_file(Path("config/settings.yaml"))
        perm = auditor.check_file_permissions(Path(".env"))
        gi = auditor.validate_gitignore(Path("."))
    """

    _SENSITIVE_FIELD_PATTERNS: list[tuple[str, re.Pattern, str]] = []

    _GITIGNORE_REQUIRED_PATTERNS: list[tuple[str, str]] = []

    @classmethod
    def _get_sensitive_patterns(cls) -> list[tuple[str, re.Pattern, str]]:
        """
        返回17种YAML/JSON敏感字段检测模式列表

        每个模式为三元组: (字段名正则, 编译后的Pattern, 风险说明)
        覆盖密码、API Key、Token、数据库凭据、证书路径等常见敏感字段。
        """
        if cls._SENSITIVE_FIELD_PATTERNS:
            return cls._SENSITIVE_FIELD_PATTERNS

        patterns = [
            # 密码相关 (4种)
            (r"(?i)password|passwd|pwd|pass", re.compile(r"(?i)password|passwd|pwd|pass"), "检测到密码字段"),
            (r"(?i)db_password|database_pwd|dbpass", re.compile(r"(?i)db_password|database_pwd|dbpass"), "检测到数据库密码字段"),
            (r"(?i)admin_password|root_password", re.compile(r"(?i)admin_password|root_password"), "检测到管理员/Root密码字段"),
            (r"(?i)secret_key|master_key|encryption_key", re.compile(r"(?i)secret_key|master_key|encryption_key"), "检测到加密密钥字段"),

            # API Key / Token / Secret (5种)
            (r"(?i)api_?key|apikey", re.compile(r"(?i)api_?key|apikey"), "检测到 API Key 字段"),
            (r"(?i)(?:access_|auth_|bearer_)token|jwt_secret", re.compile(r"(?i)(?:access_|auth_|bearer_)token|jwt_secret"), "检测到认证令牌字段"),
            (r"(?i)client_secret|app_secret|oauth.*secret", re.compile(r"(?i)client_secret|app_secret|oauth.*secret"), "检测到客户端/应用密钥字段"),
            (r"(?i)webhook_secret|signing_secret|verification_token", re.compile(r"(?i)webhook_secret|signing_secret|verification_token"), "检测到 Webhook 签名密钥字段"),
            (r"(?i)private_key|certificate|pem_file|key_file", re.compile(r"(?i)private_key|certificate|pem_file|key_file"), "检测到私钥/证书路径字段"),

            # 连接字符串 / 数据库凭据 (3种)
            (r"(?i)connection_string|conn_str|database_url|db_url", re.compile(r"(?i)connection_string|conn_str|database_url|db_url"), "检测到连接字符串字段"),
            (r"(?i)redis_url|mongo_url|pg_url|mysql_uri", re.compile(r"(?i)redis_url|mongo_url|pg_url|mysql_uri"), "检测到数据库连接URL字段"),
            (r"(?i)mongodb://|postgres://|mysql://|redis://|amqp://", re.compile(r"(?i)mongodb://|postgres://|mysql://|redis://|amqp://"), "检测到内嵌协议前缀的连接字符串"),

            # 凭据 / 认证信息 (3种)
            (r"(?i)credential|aws_access_key|aws_secret_key", re.compile(r"(?i)credential|aws_access_key|aws_secret_key"), "检测到云服务凭据字段"),
            (r"(?i)username|user|login", re.compile(r"(?i)username|user|login"), "检测到用户名字段（可能伴随密码）"),
            (r"(?i)basic_auth|authorization_header|auth_header", re.compile(r"(?i)basic_auth|authorization_header|auth_header"), "检测到 HTTP 认证头字段"),

            # 其他敏感配置 (2种)
            (r"(?i)webhook_url|callback_url|redirect_uri", re.compile(r"(?i)webhook_url|callback_url|redirect_uri"), "检测到 Webhook/回调 URL 字段"),
        ]

        cls._SENSITIVE_FIELD_PATTERNS = patterns
        return patterns

    @classmethod
    def _get_gitignore_patterns(cls) -> list[tuple[str, str]]:
        """
        返回11种应在 .gitignore 中出现的敏感文件模式

        每个模式为二元组: (gitignore 规则文本, 说明)
        """
        if cls._GITIGNORE_REQUIRED_PATTERNS:
            return cls._GITIGNORE_REQUIRED_PATTERNS

        patterns = [
            (".env", "环境变量文件"),
            (".env.local", "本地环境变量覆盖文件"),
            (".env.*.local", "所有带 .local 后缀的环境变量文件"),
            ("*.pem", "PEM 格式私钥/证书文件"),
            ("*.key", "通用密钥文件"),
            ("*.p12", "PKCS#12 证书文件"),
            ("*.pfx", "PFX 证书文件"),
            ("credentials.json", "Google/AWS 等服务凭据文件"),
            ("service-account.json", "GCP 服务账号 JSON 密钥文件"),
            ("id_rsa", "SSH 私钥文件"),
            ("id_ed25519", "Ed25519 SSH 私钥文件"),
        ]

        cls._GITIGNORE_REQUIRED_PATTERNS = patterns
        return patterns

    def __init__(self):
        """初始化审计器"""
        self._sensitive_patterns = self._get_sensitive_patterns()
        self._gitignore_patterns = self._get_gitignore_patterns()

    def audit_config_file(self, path: Path) -> AuditResult:
        """
        审计单个 YAML 或 JSON 配置文件中的敏感字段

        支持格式：.yaml, .yml, .json
        对于 YAML 文件采用简易解析（逐行键值匹配），JSON 文件使用标准库解析。

        Args:
            path: 配置文件路径

        Returns:
            AuditResult 包含详细审计结果
        """
        result = AuditResult(file_path=path.resolve())

        if not path.exists():
            result.is_valid = False
            result.errors.append(f"配置文件不存在: {path}")
            return result

        suffix = path.suffix.lower()
        if suffix not in (".yaml", ".yml", ".json"):
            result.warnings.append(f"不支持的文件格式: {suffix}，仅支持 yaml/yml/json")
            return result

        try:
            raw_text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            result.is_valid = False
            result.errors.append(f"读取文件失败: {exc}")
            return result

        config_data: dict[str, Any] = {}
        if suffix == ".json":
            try:
                config_data = json.loads(raw_text)
            except json.JSONDecodeError as exc:
                result.errors.append(f"JSON 解析错误: {exc}")
                result.is_valid = False
                return result
        else:
            config_data = self._parse_yaml_simple(raw_text)

        flat_items = self._flatten_dict(config_data, parent_key="")

        for key_path, value in flat_items.items():
            result.total_checks += 1
            for pattern_name, pattern_regex, description in self._sensitive_patterns:
                if pattern_regex.search(key_path):
                    value_str = str(value) if value is not None else ""
                    is_empty_or_placeholder = (
                        len(value_str.strip()) == 0
                        or value_str.lower() in ("changeme", "placeholder", "todo", "xxx", "none", "null")
                        or value_str.startswith("${") and value_str.endswith("}")
                    )

                    if not is_empty_or_placeholder and len(value_str) > 2:
                        masked = self._mask_value(value_str)
                        finding = {
                            "field": key_path,
                            "pattern": pattern_name,
                            "description": description,
                            "severity": "high",
                            "masked_value": masked,
                            "value_length": len(value_str),
                        }
                        result.findings.append(finding)
                        result.warnings.append(f"[{key_path}] {description} — 值长度:{len(value_str)}, 脱敏值:{masked}")
                        result.is_valid = False
                    else:
                        result.passed += 1
                    break
            else:
                result.passed += 1

        if result.findings:
            result.recommendations = [
                "将敏感值迁移至环境变量或密钥管理服务",
                "使用 .env 文件存储并确保其已加入 .gitignore",
                "考虑使用加密存储方案如 AWS Secrets Manager / HashiCorp Vault",
            ]

        return result

    def check_file_permissions(self, path: Path) -> PermissionResult:
        """
        检查指定文件的操作系统权限安全性

        在 Windows 上仅检查文件是否存在和可读性。
        在 Unix/Linux 上检查完整的权限位（owner/group/others 的读/写/执行）。

        安全判定标准：
        - others 可读 → 不安全
        - group 可读 → 警告
        - 仅 owner 可读写 → 安全

        Args:
            path: 要检查的文件路径

        Returns:
            PermissionResult 包含详细的权限分析结果
        """
        result = PermissionResult(file_path=path.resolve())

        if not path.exists():
            result.is_secure = False
            result.recommendations.append(f"文件不存在: {path}")
            return result

        try:
            stat_info = os.stat(path)
            mode = stat_info.st_mode
            result.file_mode_octal = oct(mode & 0o777)

            result.owner_readable = bool(mode & stat.S_IRUSR)
            result.group_readable = bool(mode & stat.S_IRGRP)
            result.others_readable = bool(mode & stat.S_IROTH)
            result.is_executable = bool(mode & stat.S_IXUSR) or bool(mode & stat.S_IXGRP) or bool(mode & stat.S_IXOTH)

            if result.others_readable:
                result.is_secure = False
                result.recommendations.append(
                    f"文件对其他用户可读 (mode={result.file_mode_octal})。"
                    f"建议执行: chmod 600 '{path}' 以限制仅 owner 可读写"
                )
            elif result.group_readable:
                result.recommendations.append(
                    f"文件对同组用户可读 (mode={result.file_mode_octal})。"
                    f"建议执行: chmod 640 '{path}' 或 chmod 600 '{path}'"
                )

            sensitive_indicators = [".env", ".pem", ".key", ".p12", ".pfx", "credentials", "id_rsa", "id_ed25519"]
            filename_lower = path.name.lower()
            if any(ind in filename_lower for ind in sensitive_indicators):
                if result.others_readable or result.group_readable:
                    result.is_secure = False
                    result.recommendations.insert(0, f"⚠ 检测到敏感文件类型 '{path.name}'，当前权限过宽！")

        except OSError as exc:
            result.is_secure = False
            result.recommendations.append(f"无法获取文件权限信息: {exc}")

        return result

    def validate_gitignore(self, project_root: Path) -> GitignoreResult:
        """
        验证项目根目录下的 .gitignore 是否包含必要的敏感文件排除规则

        检查11种常见的敏感文件模式是否已被 .gitignore 覆盖，
        并给出合规评分和改进建议。

        Args:
            project_root: 项目根目录路径（.gitignore 所在位置）

        Returns:
            GitignoreResult 包含合规性分析和缺失规则列表
        """
        result = GitignoreResult(gitignore_path=None)

        gitignore_path = project_root / ".gitignore"

        if not gitignore_path.exists():
            result.gitignore_path = None
            result.is_compliant = False
            result.score = 0
            result.missing_patterns = [p[0] for p in self._gitignore_patterns]
            result.suggestions.append("项目中缺少 .gitignore 文件，请立即创建以防止敏感文件被提交")
            return result

        result.gitignore_path = gitignore_path.resolve()

        try:
            ignore_content = gitignore_path.read_text(encoding="utf-8", errors="replace").lower()
        except Exception as exc:
            result.suggestions.append(f"读取 .gitignore 失败: {exc}")
            result.is_compliant = False
            return result

        existing_lines = []
        for line in ignore_content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                existing_lines.append(stripped)
        result.existing_patterns = existing_lines

        required_count = len(self._gitignore_patterns)
        found_count = 0

        for pattern_text, description in self._gitignore_patterns:
            pattern_lower = pattern_text.lower()

            is_covered = False
            if "*" in pattern_lower:
                base_part = pattern_lower.replace("*", "")
                is_covered = any(base_part in ex for ex in existing_lines)
            else:
                is_covered = any(pattern_lower == ex or pattern_lower in ex or ex.startswith(pattern_lower) for ex in existing_lines)

            if is_covered:
                found_count += 1
            else:
                result.missing_patterns.append(pattern_text)

        result.is_compliant = len(result.missing_patterns) == 0
        result.score = int((found_count / required_count) * 100) if required_count > 0 else 100

        if result.missing_patterns:
            result.suggestions.append(f"以下 {len(result.missing_patterns)} 条敏感文件规则未在 .gitignore 中找到:")
            for mp in result.missing_patterns:
                result.suggestions.append(f"  - {mp}")

        if result.score < 80:
            result.suggestions.append(f"\n合规得分仅为 {result.score}/100，强烈建议补充上述缺失规则")

        return result

    def evaluate_encryption_storage(self, config_data: dict) -> EncryptionRecommendation:
        """
        评估配置数据中的加密存储状态

        分析逻辑：
        - 检测是否有字段使用了已知加密标记（如 ENC(), vault:, aws:ssm: 等前缀）
        - 统计明文敏感字段数量
        - 根据明文/加密比例评估整体风险等级

        Args:
            config_data: 已加载的配置字典（通常来自 YAML/JSON 解析）

        Returns:
            EncryptionRecommendation 包含风险评估和改进建议
        """
        result = EncryptionRecommendation()
        flat_items = self._flatten_dict(config_data, parent_key="")

        encryption_indicators = [
            re.compile(r"^ENC\(", re.I),
            re.compile(r"^vault:", re.I),
            re.compile(r"^aws:ssm:", re.I),
            re.compile(r"^aws:secretsmanager:", re.I),
            re.compile(r "^cipher:", re.I),
            re.compile(r"^kms:", re.I),
            re.compile(r"^\$\{.*ENC", re.I),
            re.compile(r"^[A-Za-z0-9+/]{40,}={0,2}$"),
        ]

        for key_path, value in flat_items.items():
            value_str = str(value) if value is not None else ""

            is_encrypted = any(ind.search(value_str) for ind in encryption_indicators)

            for _, pattern_regex, _ in self._sensitive_patterns:
                if pattern_regex.search(key_path):
                    if is_encrypted:
                        result.encrypted_keys.append(key_path)
                        result.has_encrypted_fields = True
                    elif len(value_str.strip()) > 2:
                        result.plaintext_keys.append(key_path)
                    break

        total_sensitive = len(result.encrypted_keys) + len(result.plaintext_keys)

        if total_sensitive == 0:
            result.risk_level = "low"
            result.recommendations.append("未在配置中发现明显的敏感字段")
        elif len(result.plaintext_keys) == 0:
            result.risk_level = "safe"
            result.encryption_method = "all_encrypted"
            result.recommendations.append("所有敏感字段均已加密存储 ✅")
        elif len(result.encrypted_keys) > len(result.plaintext_keys):
            result.risk_level = "medium"
            result.encryption_method = "partial"
            result.recommendations.append(f"部分敏感字段已加密 ({len(result.encrypted_keys)}/{total_sensitive})，仍有 {len(result.plaintext_keys)} 个明文字段需要处理")
        else:
            result.risk_level = "high"
            result.encryption_method = "none_or_few"
            ratio = len(result.plaintext_keys) / total_sensitive * 100
            result.recommendations.extend([
                f"高风险: {ratio:.0f}% 的敏感字段 ({len(result.plaintext_keys)}/{total_sensitive}) 以明文形式存储",
                "建议采用的加密方案:",
                "  1. 环境变量注入 + .env 文件（开发环境）",
                "  2. HashiCorp Vault / AWS Secrets Manager（生产环境）",
                "  3. SOPS (Mozilla Opaque Secret Store) 加密 YAML/JSON",
                "  4. Ansible Vault 或类似的配置加密工具",
            ])

        return result

    @staticmethod
    def _parse_yaml_simple(text: str) -> dict:
        """
        简易 YAML 解析器（不依赖 PyYAML 外部库）

        支持特性：
        - 键: 值 格式
        - 缩进表示层级（2空格或4空格）
        - 注释行 (# 开头) 自动跳过
        - 简单的字符串/数字/布尔/null 值
        - 列表项 (- item) 基本支持

        注意：不支持多行字符串、锚点/引用等高级 YAML 特性。
        如需完整 YAML 支持，请安装 pyyaml 库。

        Args:
            text: YAML 文件的原始文本内容

        Returns:
            嵌套字典表示的配置数据
        """
        result: dict = {}
        stack: list[tuple[dict, int]] = [(result, 0)]

        for line in text.splitlines():
            stripped = line.rstrip()
            if not stripped or stripped.lstrip().startswith("#"):
                continue

            indent = len(stripped) - len(stripped.lstrip())
            content = stripped.lstrip()

            while stack and stack[-1][1] >= indent:
                stack.pop()

            current_dict, _ = stack[-1] if stack else (result, 0)

            if content.startswith("- "):
                continue

            colon_idx = content.find(":")
            if colon_idx <= 0:
                continue

            key = content[:colon_idx].strip().rstrip('"').rstrip("'")
            val_raw = content[colon_idx + 1:].strip()

            if not val_raw or val_raw.startswith("#"):
                new_dict: dict = {}
                current_dict[key] = new_dict
                stack.append((new_dict, indent))
            else:
                val_unquoted = val_raw.strip('"').strip("'")
                parsed_val = ConfigSecurityAuditor._parse_yaml_value(val_unquoted)
                current_dict[key] = parsed_val

        return result

    @staticmethod
    def _parse_yaml_value(val: str) -> Any:
        """解析 YAML 标量值为对应的 Python 类型"""
        lower = val.lower()
        if lower in ("true", "yes", "on"):
            return True
        if lower in ("false", "no", "off"):
            return False
        if lower in ("null", "~", ""):
            return None
        try:
            if "." in val:
                return float(val)
            return int(val)
        except ValueError:
            return val

    @staticmethod
    def _flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict[str, Any]:
        """
        将嵌套字典展平为单层键值对

        例如 {"database": {"host": "localhost", "port": 5432}}
        展平后为 {"database.host": "localhost", "database.port": 5432}

        Args:
            d: 待展平的嵌套字典
            parent_key: 当前父级键前缀
            sep: 层级分隔符

        Returns:
            展平后的字典
        """
        items: dict[str, Any] = {}
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(ConfigSecurityAuditor._flatten_dict(v, new_key, sep=sep))
            else:
                items[new_key] = v
        return items

    @staticmethod
    def _mask_value(value: str) -> str:
        """对敏感值进行脱敏显示（保留首尾各3字符）"""
        if len(value) <= 6:
            return "*" * len(value)
        return value[:3] + "***" + value[-3:]

    def __repr__(self) -> str:
        return "ConfigSecurityAuditor(sensitive_patterns={}, gitignore_patterns={})".format(
            len(self._sensitive_patterns), len(self._gitignore_patterns)
        )
