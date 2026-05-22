"""
密钥管理器模块 - SecretsManager

提供安全的密钥加载、存储、分类、脱敏和验证功能。
支持多源加载链：.env → .env.local → os.environ → 默认值
无外部依赖，纯Python标准库实现。
"""

import os
import re
import logging
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Any


class SecretType(Enum):
    """密钥类型枚举，共8种类型"""

    PASSWORD = "password"
    API_KEY = "api_key"
    TOKEN = "token"
    SECRET = "secret"
    CREDENTIAL = "credential"
    CONNECTION_STRING = "connection_string"
    PRIVATE_KEY = "private_key"
    ENCRYPTION_KEY = "encryption_key"


@dataclass
class SecretEntry:
    """密钥条目数据类，记录单个密钥的完整信息"""

    key: str
    value: str
    secret_type: SecretType
    source: str  # 来源标识，如 env_file, os_environ, default
    loaded_at: datetime = field(default_factory=datetime.now)
    is_masked: bool = False

    def __repr__(self) -> str:
        if self.is_masked:
            return f"SecretEntry(key='{self.key}', type={self.secret_type.value}, source='{self.source}', value='***')"
        return f"SecretEntry(key='{self.key}', type={self.secret_type.value}, source='{self.source}')"


@dataclass
class ValidationResult:
    """密钥验证结果数据类"""

    is_valid: bool
    total_checked: int = 0
    passed: int = 0
    failed: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    details: dict[str, dict] = field(default_factory=dict)

    def summary(self) -> str:
        """生成验证结果摘要文本"""
        status = "✅ 通过" if self.is_valid else "❌ 未通过"
        lines = [
            f"密钥验证结果: {status}",
            f"  总计检查: {self.total_checked} | 通过: {self.passed} | 失败: {self.failed}",
        ]
        if self.warnings:
            lines.append(f"  警告 ({len(self.warnings)}):")
            for w in self.warnings[:5]:
                lines.append(f"    ⚠ {w}")
        if self.errors:
            lines.append(f"  错误 ({len(self.errors)}):")
            for e in self.errors[:5]:
                lines.append(f"    ✗ {e}")
        return "\n".join(lines)


@dataclass
class AuditRecord:
    """审计日志记录数据类"""

    timestamp: datetime
    action: str  # 操作类型: get, get_required, load, validate
    key: str
    result: str  # 结果状态: success, missing, error
    secret_type: Optional[SecretType] = None
    masked_value: Optional[str] = None
    extra: str = ""

    def to_dict(self) -> dict:
        """转换为字典格式，便于序列化"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "key": self.key,
            "result": self.result,
            "secret_type": self.secret_type.value if self.secret_type else None,
            "masked_value": self.masked_value,
            "extra": self.extra,
        }


class SecretsManager:
    """
    密钥管理器核心类

    功能概述：
    - 多源加载链：.env → .env.local → os.environ → defaults
    - 类型安全获取与自动分类
    - 日志脱敏输出
    - 密钥强度验证
    - 审计日志记录

    使用示例：
        mgr = SecretsManager(env_file=".env")
        mgr.load()
        db_url = mgr.get_required("DATABASE_URL", purpose="数据库连接")
        api_key = mgr.get("API_KEY", default="dev-key")
        result = mgr.validate_all()
    """

    _KEY_TYPE_PATTERNS: dict[SecretType, list[re.Pattern]] = {
        SecretType.PASSWORD: [
            re.compile(r"(?i)password|passwd|pwd|pass"),
            re.compile(r"(?i)db_password|database_password"),
        ],
        SecretType.API_KEY: [
            re.compile(r"(?i)api_key|apikey|api\.key"),
            re.compile(r"(?i)_key$|_KEY$"),
            re.compile(r"(?i)secret_key|access_key"),
        ],
        SecretType.TOKEN: [
            re.compile(r"(?i)token|auth_token|access_token|bearer"),
            re.compile(r"(?i)jwt_|id_token|refresh_token"),
        ],
        SecretType.SECRET: [
            re.compile(r"(?i)secret|client_secret|app_secret"),
            re.compile(r"(?i)webhook_secret|signing_secret"),
        ],
        SecretType.CREDENTIAL: [
            re.compile(r"(?i)credential|creds?|auth$"),
            re.compile(r"(?i)username|user|login"),
        ],
        SecretType.CONNECTION_STRING: [
            re.compile(r"(?i)conn_str|connection_string|database_url|db_url"),
            re.compile(r"(?i)mongodb://|postgres://|mysql://|redis://"),
            re.compile(r"(?i)redis_url|mongo_url|pg_url"),
        ],
        SecretType.PRIVATE_KEY: [
            re.compile(r"(?i)private_key|priv_key|pem_key"),
            re.compile(r"(?i)rsa_private|ec_private"),
        ],
        SecretType.ENCRYPTION_KEY: [
            re.compile(r"(?i)encryption_key|enc_key|cipher_key"),
            re.compile(r"(?i)master_key|derived_key|hmac_key"),
        ],
    }

    _DEFAULT_SECRETS: dict[str, str] = {}

    def __init__(self, env_file: Optional[str] = None):
        """
        初始化密钥管理器

        Args:
            env_file: 可选的 .env 文件路径，默认为项目根目录下的 .env
        """
        self._secrets: dict[str, SecretEntry] = {}
        self._audit_log_records: list[AuditRecord] = []
        self._env_file: Optional[str] = env_file or ".env"
        self._logger = logging.getLogger(__name__)
        self._loaded_sources: set[str] = set()

    def load(self, env_file: Optional[str] = None) -> None:
        """
        多源加载链：按优先级依次从各来源加载环境变量

        加载顺序（后加载的覆盖先加载的）：
        1. .env 文件
        2. .env.local 文件（本地覆盖）
        3. os.environ 系统环境变量
        4. 内置默认值（最低优先级）

        Args:
            env_file: 可选的 .env 文件路径，覆盖初始化时指定的路径
        """
        target_env = env_file or self._env_file
        base_path = Path(target_env)

        sources_to_load = []

        if base_path.exists():
            sources_to_load.append((str(base_path), "env_file"))

        local_path = base_path.with_name(base_path.name + ".local")
        if local_path.exists():
            sources_to_load.append((str(local_path), "env_local"))

        sources_to_load.append((None, "os_environ"))
        sources_to_load.append((None, "defaults"))

        for path, source in sources_to_load:
            try:
                if path:
                    data = self._load_env_file(path)
                    for key, value in data.items():
                        if key not in self._secrets:
                            stype = self.classify(key)
                            entry = SecretEntry(
                                key=key,
                                value=value,
                                secret_type=stype,
                                source=source,
                            )
                            self._secrets[key] = entry
                    self._loaded_sources.add(source)
                elif source == "os_environ":
                    for key, value in os.environ.items():
                        if key not in self._secrets:
                            stype = self.classify(key)
                            entry = SecretEntry(
                                key=key,
                                value=value,
                                secret_type=stype,
                                source="os_environ",
                            )
                            self._secrets[key] = entry
                    self._loaded_sources.add("os_environ")
                elif source == "defaults":
                    for key, value in self._DEFAULT_SECRETS.items():
                        if key not in self._secrets:
                            stype = self.classify(key)
                            entry = SecretEntry(
                                key=key,
                                value=value,
                                secret_type=stype,
                                source="default",
                            )
                            self._secrets[key] = entry
                    self._loaded_sources.add("defaults")
            except Exception as exc:
                self._logger.warning("加载来源 %s 时出错: %s", source, exc)
                self._audit_log("load", source or "__system__", f"error:{exc}")

        total_loaded = len(self._secrets)
        self._audit_log("load", "__all__", f"success:{total_loaded}", extra=f"sources={self._loaded_sources}")

    def get(self, key: str, default: Any = None) -> str:
        """
        类型安全地获取密钥值

        自动对密钥进行分类并记录审计日志。
        如果密钥不存在则返回默认值。

        Args:
            key: 环境变量名/密钥名
            default: 密钥不存在时的默认返回值

        Returns:
            密钥值的字符串形式
        """
        entry = self._secrets.get(key)
        if entry is None:
            self._audit_log("get", key, "missing", extra=f"default_used=True")
            return str(default) if default is not None else ""

        self._audit_log("get", key, "success", secret_type=entry.secret_type, masked_value=self.mask_for_log(entry.value))
        return entry.value

    def get_required(self, key: str, purpose: str = "") -> str:
        """
        获取必需密钥，缺失时抛出清晰的错误信息

        Args:
            key: 环境变量名/密钥名
            purpose: 该密钥的用途描述，用于生成更友好的错误消息

        Returns:
            密钥值的字符串

        Raises:
            KeyError: 当密钥未找到时抛出，附带详细的缺失原因说明
        """
        entry = self._secrets.get(key)
        if entry is None:
            purpose_msg = f" (用途: {purpose})" if purpose else ""
            available = ", ".join(sorted(self._secrets.keys()))[:200]
            msg = (
                f"[SecretsManager] 必需密钥 '{key}' 未找到{purpose_msg}。\n"
                f"  已加载来源: {', '.join(sorted(self._loaded_sources)) or '无'}\n"
                f"  当前已加载密钥数量: {len(self._secrets)}\n"
                f"  请在 .env 或 .env.local 文件中配置此密钥。\n"
                f"  已有密钥示例: {available}"
            )
            self._audit_log("get_required", key, "error:missing", extra=f"purpose={purpose}")
            raise KeyError(msg)

        self._audit_log("get_required", key, "success", secret_type=entry.secret_type, masked_value=self.mask_for_log(entry.value), extra=f"purpose={purpose}")
        return entry.value

    def classify(self, value: str) -> SecretType:
        """
        根据键名自动分类密钥类型

        通过内置的正则模式匹配键名，判断该密钥属于哪种类型。
        匹配顺序按 SecretType 枚举定义顺序，首个匹配的类型即为结果。

        Args:
            value: 待分类的键名字符串

        Returns:
            匹配到的 SecretType 枚举值，若无匹配则默认为 SECRET
        """
        for stype, patterns in self._KEY_TYPE_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(value):
                    return stype
        return SecretType.SECRET

    @staticmethod
    def mask_for_log(value: str) -> str:
        """
        对敏感值进行日志脱敏处理

        脱敏规则：保留首尾各2个字符，中间用 **** 替代。
        若值长度 <= 4 则全部用 * 替代。

        Examples:
            >>> SecretsManager.mask_for_log("admin123")
            'ad****23'
            >>> SecretsManager.mask_for_log("ab")
            '**'
            >>> SecretsManager.mask_for_log("")
            ''

        Args:
            value: 原始敏感值字符串

        Returns:
            脱敏后的安全字符串
        """
        if not value:
            return ""
        if len(value) <= 4:
            return "*" * len(value)
        return value[:2] + "****" + value[-2:]

    def validate_all(self) -> ValidationResult:
        """
        验证所有已加载密钥的安全性强度

        检查项包括：
        - 密码类密钥长度是否 >= 8
        - API Key / Token 是否非空
        - 连接字符串是否包含协议前缀
        - 私钥是否包含典型标记
        - 敏感字段是否使用了占位符或弱值

        Returns:
            包含详细检查结果的 ValidationResult 对象
        """
        result = ValidationResult(is_valid=True, total_checked=len(self._secrets))

        weak_patterns = {
            "password": [re.compile(r"^(123456|password|admin|root|test)$", re.I)],
            "generic": [
                re.compile(r"^(changeme|default|placeholder|todo|xxx|none|null|\$\{.*\})$", re.I),
                re.compile(r"^.{1,4}$"),
            ],
        }

        placeholder_keywords = ("placeholder", "change_me", "todo", "xxx", "your_", "<insert>", "replace")

        for key, entry in self._secrets.items():
            val = entry.value
            issues = []
            stype = entry.secret_type

            if stype == SecretType.PASSWORD and len(val) < 8:
                issues.append(f"密码长度不足8字符 (当前: {len(val)})")

            if val.strip() == "":
                issues.append("值为空字符串")

            lower_val = val.lower()
            if any(kw in lower_val for kw in placeholder_keywords):
                issues.append(f"检测到占位符关键字: {val}")

            for label, patterns in weak_patterns.items():
                for pat in patterns:
                    if pat.search(val):
                        issues.append(f"检测到弱值模式 [{label}]: {self.mask_for_log(val)}")

            if stype == SecretType.CONNECTION_STRING:
                has_protocol = any(val.startswith(p) for p in ("mongodb://", "postgres://", "mysql://", "redis://", "amqp://"))
                if not has_protocol and "://" in val:
                    pass
                elif not has_protocol and len(val) > 10:
                    issues.append("连接字符串缺少已知协议前缀")

            if stype == SecretType.PRIVATE_KEY and not any(m in val for m in ("BEGIN", "-----", "MIIE")):
                issues.append("私钥内容缺少典型的PEM/DER标记")

            result.details[key] = {
                "type": stype.value,
                "source": entry.source,
                "value_length": len(val),
                "masked": self.mask_for_log(val),
                "issues": issues,
            }

            if issues:
                result.failed += 1
                result.is_valid = False
                for issue in issues:
                    result.warnings.append(f"[{key}] {issue}")
            else:
                result.passed += 1

        result.total_checked = len(self._secrets)
        self._audit_log("validate_all", "__all__", "passed" if result.is_valid else "failed", extra=f"total={result.total_checked},failed={result.failed}")
        return result

    def _load_env_file(self, path: str) -> dict[str, str]:
        """
        手动解析 .env 文件，不依赖 python-dotenv 等外部库

        解析规则：
        - 支持 KEY=VALUE 格式
        - 支持单引号/双引号包裹的值（含空格和特殊字符）
        - 支持行内注释（# 开头，但引号内的 # 不算注释）
        - 忽略空行和纯注释行
        - 支持 export 前缀（兼容 bash 风格）

        Args:
            path: .env 文件的绝对或相对路径

        Returns:
            解析出的键值对字典

        Raises:
            FileNotFoundError: 文件不存在时抛出
            UnicodeDecodeError: 编码异常时抛出
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f".env 文件不存在: {path}")

        data: dict[str, str] = {}
        raw_content = file_path.read_text(encoding="utf-8").splitlines()

        for line_num, line in enumerate(raw_content, start=1):
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            export_prefix = ""
            if stripped.lower().startswith("export "):
                export_prefix = "export "
                stripped = stripped[7:].strip()

            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", stripped)
            if not match:
                continue

            key = match.group(1)
            raw_value = match.group(2).strip()

            if (raw_value.startswith('"') and raw_value.endswith('"')) or (
                raw_value.startswith("'") and raw_value.endswith("'")
            ):
                value = raw_value[1:-1]
            else:
                comment_idx = raw_value.find("#")
                if comment_idx != -1:
                    value = raw_value[:comment_idx].rstrip()
                else:
                    value = raw_value

            data[key] = value

        return data

    def _audit_log(self, action: str, key: str, result: str, secret_type: Optional[SecretType] = None, masked_value: Optional[str] = None, extra: str = "") -> None:
        """
        记录审计日志到内存列表

        所有密钥访问操作都会被记录，包括：
        - get / get_required 等读取操作
        - load 加载操作
        - validate_all 验证操作

        日志包含时间戳、操作类型、密钥名、结果状态、脱敏值等。

        Args:
            action: 操作类型字符串
            key: 相关的密钥名
            result: 操作结果状态
            secret_type: 密钥类型（可选）
            masked_value: 脱敏后的值（可选）
            extra: 额外附加信息（可选）
        """
        record = AuditRecord(
            timestamp=datetime.now(),
            action=action,
            key=key,
            result=result,
            secret_type=secret_type,
            masked_value=masked_value,
            extra=extra,
        )
        self._audit_log_records.append(record)
        self._logger.debug("审计日志: %s", record.to_dict())

    @property
    def audit_logs(self) -> list[AuditRecord]:
        """获取所有审计日志记录（只读属性）"""
        return list(self._audit_log_records)

    @property
    def loaded_keys(self) -> list[str]:
        """获取所有已加载的密钥名称列表（只读属性）"""
        return sorted(self._secrets.keys())

    def __contains__(self, key: str) -> bool:
        """支持 'in' 运算符检查密钥是否存在"""
        return key in self._secrets

    def __getitem__(self, key: str) -> str:
        """支持字典式访问: manager["KEY"]"""
        return self.get_required(key)

    def __repr__(self) -> str:
        return f"SecretsManager(loaded={len(self._secrets)} keys, sources={self._loaded_sources})"
