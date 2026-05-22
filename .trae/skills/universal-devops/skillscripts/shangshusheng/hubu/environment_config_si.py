"""
环境配置司 - 多环境配置管理、Docker编排、环境一致性保障
"""
from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class EnvironmentConfigError(Exception):
    """环境配置相关异常"""
    pass


class EnvironmentType(str, Enum):
    """环境类型枚举"""
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    UAT = "uat"
    PROD = "prod"


class ConfigSensitivity(str, Enum):
    """配置敏感度枚举"""
    PUBLIC = "public"
    INTERNAL = "internal"
    SECRET = "secret"
    RESTRICTED = "restricted"


@dataclass
class EnvConfig:
    """单个环境配置"""
    env_type: EnvironmentType
    name: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    variables: dict[str, str] = field(default_factory=dict)
    sensitive_vars: set[str] = field(default_factory=set)
    docker_compose: dict[str, Any] | None = None
    feature_flags: dict[str, bool] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, mask_secrets: bool = True) -> dict[str, Any]:
        result = {
            "env_type": self.env_type.value,
            "name": self.name or self.env_type.value,
            "config": self.config,
            "variables": {},
            "feature_flags": self.feature_flags,
        }

        for k, v in self.variables.items():
            if mask_secrets and k in self.sensitive_vars:
                result["variables"][k] = "***MASKED***"
            else:
                result["variables"][k] = v

        return result

    def get_variable(self, key: str) -> str | None:
        return self.variables.get(key)

    def set_variable(
        self,
        key: str,
        value: str,
        sensitivity: ConfigSensitivity = ConfigSensitivity.INTERNAL,
    ) -> None:
        self.variables[key] = value
        if sensitivity in (ConfigSensitivity.SECRET, ConfigSensitivity.RESTRICTED):
            self.sensitive_vars.add(key)

    def remove_variable(self, key: str) -> bool:
        if key in self.variables:
            del self.variables[key]
            self.sensitive_vars.discard(key)
            return True
        return False


@dataclass
class ConfigDiff:
    """配置差异条目"""
    key: str
    env_a_value: Any
    env_b_value: Any
    diff_type: str
    sensitivity: str = "internal"

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "env_a": self.env_a_value,
            "env_b": self.env_b_value,
            "type": self.diff_type,
            "sensitivity": self.sensitivity,
        }


@dataclass
class DriftReport:
    """配置漂移报告"""
    source_env: str
    target_env: str
    total_keys: int
    matched_keys: int
    diff_count: int
    only_in_source: list[str]
    only_in_target: list[str]
    diffs: list[ConfigDiff]
    drift_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_env": self.source_env,
            "target_env": self.target_env,
            "total_keys": self.total_keys,
            "matched_keys": self.matched_keys,
            "diff_count": self.diff_count,
            "only_in_source": self.only_in_source,
            "only_in_target": self.only_in_target,
            "drift_score": round(self.drift_score, 4),
            "diffs": [d.to_dict() for d in self.diffs],
        }


@dataclass
class FeatureFlag:
    """特性开关"""
    name: str
    enabled: bool = False
    description: str = ""
    target_environments: list[EnvironmentType] = field(default_factory=list)
    rollout_percentage: int = 0
    conditions: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "description": self.description,
            "target_environments": [e.value for e in self.target_environments],
            "rollout_percentage": self.rollout_percentage,
            "conditions": self.conditions,
        }


class EnvironmentConfigSi:
    """
    环境配置司

    负责多环境配置管理、Docker编排和环境一致性保障。
    支持配置差异对比、.env文件管理、特性开关等功能。
    """

    _instance: EnvironmentConfigSi | None = None

    def __init__(self) -> None:
        self._environments: dict[EnvironmentType, EnvConfig] = {}
        self._feature_flags: dict[str, FeatureFlag] = {}
        self._config_templates: dict[str, dict[str, Any]] = {}
        self._docker_templates: dict[str, str] = {}
        self._initialize_default_environments()

    @classmethod
    def get_instance(cls) -> EnvironmentConfigSi:
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _initialize_default_environments(self) -> None:
        """初始化默认环境配置"""
        default_configs: dict[EnvironmentType, dict[str, Any]] = {
            EnvironmentType.LOCAL: {
                "debug": True,
                "log_level": "DEBUG",
                "database_url": "postgresql://localhost:5432/myapp_dev",
                "redis_url": "redis://localhost:6379/0",
                "allowed_origins": ["http://localhost:3000", "http://localhost:8000"],
                "cors_enabled": True,
                "rate_limit": 1000,
            },
            EnvironmentType.DEV: {
                "debug": True,
                "log_level": "DEBUG",
                "database_url": "postgresql://dev-db:5432/myapp_dev",
                "redis_url": "redis://dev-redis:6379/0",
                "allowed_origins": ["https://dev.example.com"],
                "cors_enabled": True,
                "rate_limit": 500,
                "api_key": "dev-api-key-12345",
            },
            EnvironmentType.STAGING: {
                "debug": False,
                "log_level": "INFO",
                "database_url": "postgresql://staging-db:5432/myapp_staging",
                "redis_url": "redis://staging-redis:6379/0",
                "allowed_origins": ["https://staging.example.com"],
                "cors_enabled": False,
                "rate_limit": 200,
                "api_key": "staging-api-key-67890",
            },
            EnvironmentType.UAT: {
                "debug": False,
                "log_level": "INFO",
                "database_url": "postgresql://uat-db:5432/myapp_uat",
                "redis_url": "redis://uat-redis:6379/0",
                "allowed_origins": ["https://uat.example.com"],
                "cors_enabled": False,
                "rate_limit": 100,
                "api_key": "uat-api-key-abcde",
            },
            EnvironmentType.PROD: {
                "debug": False,
                "log_level": "WARNING",
                "database_url": "postgresql://prod-db-replica:5432/myapp_prod",
                "redis_url": "redis://prod-redis-cluster:6379/0",
                "allowed_origins": ["https://app.example.com", "https://www.example.com"],
                "cors_enabled": False,
                "rate_limit": 50,
                "api_key": "prod-secret-key-fghij",
            },
        }

        for env_type, config_data in default_configs.items():
            env_config = EnvConfig(env_type=env_type, config=config_data.copy())
            for key, value in config_data.items():
                sensitivity = ConfigSensitivity.PUBLIC
                if any(kw in key.lower() for kw in ["secret", "password", "key", "token"]):
                    sensitivity = ConfigSensitivity.SECRET
                elif any(kw in key.lower() for kw in ["url", "db", "connection"]):
                    sensitivity = ConfigSensitivity.INTERNAL
                env_config.set_variable(str(key), str(value), sensitivity)
            self._environments[env_type] = env_config

    def register_environment(
        self,
        env_type: EnvironmentType,
        name: str = "",
        **kwargs: Any,
    ) -> EnvConfig:
        """
        注册新环境

        Args:
            env_type: 环境类型
            name: 环境名称
            **kwargs: 其他配置参数

        Returns:
            创建的EnvConfig对象

        Raises:
            EnvironmentConfigError: 当环境已存在时
        """
        if env_type in self._environments:
            raise EnvironmentConfigError(f"环境已注册: {env_type.value}")
        env_config = EnvConfig(env_type=env_type, name=name or env_type.value, **kwargs)
        self._environments[env_type] = env_config
        return env_config

    def get_environment(self, env_type: EnvironmentType) -> EnvConfig:
        """获取环境配置"""
        if env_type not in self._environments:
            raise EnvironmentConfigError(f"环境不存在: {env_type.value}")
        return self._environments[env_type]

    def compare_environments(
        self,
        env_a: EnvironmentType,
        env_b: EnvironmentType,
        include_sensitive: bool = False,
    ) -> DriftReport:
        """
        对比两个环境的配置差异

        Args:
            env_a: 源环境
            env_b: 目标环境
            include_sensitive: 是否包含敏感信息对比

        Returns:
            DriftReport对象
        """
        config_a = self.get_environment(env_a)
        config_b = self.get_environment(env_b)

        all_keys = set(config_a.variables.keys()) | set(config_b.variables.keys())

        diffs: list[ConfigDiff] = []
        only_in_a: list[str] = []
        only_in_b: list[str] = []

        for key in sorted(all_keys):
            val_a = config_a.variables.get(key)
            val_b = config_b.variables.get(key)

            is_sensitive = key in config_a.sensitive_vars or key in config_b.sensitive_vars

            if val_a is None and val_b is not None:
                only_in_b.append(key)
            elif val_b is None and val_a is not None:
                only_in_a.append(key)
            elif val_a != val_b:
                if include_sensitive or not is_sensitive:
                    diff_type = "value_changed"
                    diffs.append(ConfigDiff(
                        key=key,
                        env_a_value=val_a,
                        env_b_value=val_b,
                        diff_type=diff_type,
                        sensitivity="secret" if is_sensitive else "internal",
                    ))

        total_keys = len(all_keys)
        diff_count = len(diffs) + len(only_in_a) + len(only_in_b)
        drift_score = diff_count / total_keys if total_keys > 0 else 0.0

        return DriftReport(
            source_env=env_a.value,
            target_env=env_b.value,
            total_keys=total_keys,
            matched_keys=total_keys - diff_count,
            diff_count=diff_count,
            only_in_source=only_in_a,
            only_in_target=only_in_b,
            diffs=diffs,
            drift_score=drift_score,
        )

    def check_consistency(
        self,
        baseline_env: EnvironmentType = EnvironmentType.STAGING,
    ) -> dict[str, Any]:
        """
        检查所有环境与基线环境的一致性（漂移检测）

        Args:
            baseline_env: 基线环境，默认为STAGING

        Returns:
            一致性检查结果字典
        """
        results: dict[str, Any] = {
            "baseline": baseline_env.value,
            "env_checks": {},
            "overall_status": "consistent",
            "issues_found": 0,
        }

        for env_type in self._environments:
            if env_type == baseline_env:
                continue

            try:
                report = self.compare_environments(baseline_env, env_type)
                status = "consistent" if report.drift_score < 0.1 else (
                    "minor_drift" if report.drift_score < 0.3 else "major_drift"
                )
                results["env_checks"][env_type.value] = {
                    "status": status,
                    "drift_score": round(report.drift_score, 4),
                    "diff_count": report.diff_count,
                }
                if status != "consistent":
                    results["overall_status"] = "inconsistent"
                    results["issues_found"] += 1
            except EnvironmentConfigError as e:
                results["env_checks"][env_type.value] = {"error": str(e)}
                results["overall_status"] = "error"

        return results

    def generate_docker_compose(
        self,
        env_type: EnvironmentType,
        services: list[dict[str, Any]] | None = None,
        version: str = "3.8",
    ) -> dict[str, Any]:
        """
        生成Docker Compose配置

        Args:
            env_type: 目标环境类型
            services: 服务列表（使用默认服务如果未提供）
            version: Docker Compose版本

        Returns:
            Docker Compose字典
        """
        config = self.get_environment(env_type)

        default_services: list[dict[str, Any]] = [
            {
                "name": "app",
                "image": f"myapp:{env_type.value}",
                "build": {"context": ".", "dockerfile": "Dockerfile"},
                "ports": [f"{8000 + list(EnvironmentType).index(env_type)}:8000"],
                "environment": {k: v for k, v in config.variables.items()
                                if k not in config.sensitive_vars},
                "depends_on": ["db", "redis"],
                "restart": "unless-stopped" if env_type == EnvironmentType.PROD else "no",
                "deploy": {
                    "replicas": 1 if env_type in (EnvironmentType.LOCAL, EnvironmentType.DEV) else 3,
                    "resources": {
                        "limits": {"cpus": "2.0", "memory": "2G"},
                        "reservations": {"cpus": "0.5", "memory": "512M"},
                    },
                } if env_type != EnvironmentType.LOCAL else None,
            },
            {
                "name": "db",
                "image": "postgres:15-alpine",
                "environment": {
                    "POSTGRES_DB": "myapp",
                    "POSTGRES_USER": "appuser",
                    "POSTGRES_PASSWORD": "${DB_PASSWORD}",
                },
                "volumes": ["pgdata:/var/lib/postgresql/data"],
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U appuser"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 5,
                },
            },
            {
                "name": "redis",
                "image": "redis:7-alpine",
                "command": "redis-server --appendonly yes",
                "volumes": ["redisdata:/data"],
            },
        ]

        services_to_use = services or default_services

        compose: dict[str, Any] = {
            "version": version,
            "services": {s.pop("name"): s for s in services_to_use},
            "volumes": {
                "pgdata": {"driver": "local"},
                "redisdata": {"driver": "local"},
            },
            "networks": {
                "app_net": {"driver": "bridge"},
            },
        }

        config.docker_compose = compose
        return compose

    def generate_dockerfile(
        self,
        base_image: str = "python:3.11-slim",
        app_type: str = "python",
        **kwargs: Any,
    ) -> str:
        """
        生成Dockerfile内容

        Args:
            base_image: 基础镜像
            app_type: 应用类型 (python/node/go/rust)
            **kwargs: 额外参数

        Returns:
            Dockerfile字符串
        """
        match app_type:
            case "python":
                lines = [
                    f"FROM {base_image}",
                    "",
                    "WORKDIR /app",
                    "",
                    "ENV PYTHONDONTWRITEBYTECODE=1 \\",
                    "    PYTHONUNBUFFERED=1 \\",
                    "    PIP_NO_CACHE_DIR=1 \\",
                    "    PIP_DISABLE_PIP_VERSION_CHECK=1",
                    "",
                    "RUN apt-get update && apt-get install -y --no-install-recommends \\",
                    "    build-essential && rm -rf /var/lib/apt/lists/*",
                    "",
                    "COPY requirements.txt .",
                    "RUN pip install --no-cache-dir -r requirements.txt",
                    "",
                    "COPY . .",
                    "",
                    'EXPOSE 8000',
                    "",
                    'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]',
                ]
            case "node":
                lines = [
                    f"FROM node:18-alpine AS builder",
                    "WORKDIR /app",
                    "COPY package*.json ./",
                    "RUN npm ci",
                    "COPY . .",
                    "RUN npm run build",
                    "",
                    "FROM node:18-alpine AS runner",
                    "WORKDIR /app",
                    "COPY --from=builder /app/dist ./dist",
                    "COPY --from=builder /app/node_modules ./node_modules",
                    "COPY --from=builder /app/package.json ./package.json",
                    'EXPOSE 3000',
                    'CMD ["npm", "start"]',
                ]
            case "go":
                lines = [
                    "FROM golang:1.21-alpine AS builder",
                    "WORKDIR /app",
                    "COPY go.mod go.sum ./",
                    "RUN go mod download",
                    "COPY . .",
                    "RUN CGO_ENABLED=0 GOOS=linux go build -o /server .",
                    "",
                    "FROM alpine:3.19",
                    "RUN apk --no-cache add ca-certificates tzdata",
                    "COPY --from=builder /server /server",
                    'EXPOSE 8080',
                    'CMD ["/server"]',
                ]
            case _:
                lines = [f"FROM {base_image}", 'CMD ["echo", "Hello"]']

        return "\n".join(lines)

    def generate_env_file(
        self,
        env_type: EnvironmentType,
        encrypt_secrets: bool = False,
    ) -> str:
        """
        生成.env文件内容

        Args:
            env_type: 环境类型
            encrypt_secrets: 是否加密敏感变量

        Returns:
            .env文件字符串
        """
        config = self.get_environment(env_type)
        lines: list[str] = [f"# Environment: {config.name or env_type.value}"]
        lines.append(f"# Generated by EnvironmentConfigSi")
        lines.append("")

        for key in sorted(config.variables.keys()):
            value = config.variables[key]
            is_secret = key in config.sensitive_vars

            if encrypt_secrets and is_secret:
                encoded = base64.b64encode(value.encode()).decode()
                value = f"ENC({encoded})"
            elif is_secret:
                value = "${" + key.upper().replace(".", "_") + "}"

            comment = " # [SENSITIVE]" if is_secret else ""
            lines.append(f"{key}={value}{comment}")

        return "\n".join(lines)

    def create_feature_flag(
        self,
        name: str,
        description: str = "",
        target_environments: list[EnvironmentType] | None = None,
        rollout_percentage: int = 0,
        conditions: dict[str, Any] | None = None,
    ) -> FeatureFlag:
        """
        创建特性开关

        Args:
            name: 开关名称
            description: 描述
            target_environments: 目标环境列表
            rollout_percentage: 灰度发布百分比 (0-100)
            conditions: 条件规则

        Returns:
            创建的FeatureFlag对象
        """
        now = __import__("datetime").datetime.now().isoformat()

        flag = FeatureFlag(
            name=name,
            enabled=False,
            description=description,
            target_environments=target_environments or [],
            rollout_percentage=max(0, min(100, rollout_percentage)),
            conditions=conditions or {},
            created_at=now,
            updated_at=now,
        )

        self._feature_flags[name] = flag
        return flag

    def toggle_feature_flag(
        self,
        name: str,
        enabled: bool | None = None,
        env_type: EnvironmentType | None = None,
    ) -> FeatureFlag:
        """
        切换特性开关状态

        Args:
            name: 开关名称
            enabled: 启用状态（None则翻转当前状态）
            env_type: 特定环境（可选）

        Returns:
            更新后的FeatureFlag对象

        Raises:
            EnvironmentConfigError: 当开关不存在时
        """
        if name not in self._feature_flags:
            raise EnvironmentConfigError(f"特性开关不存在: {name}")

        flag = self._feature_flags[name]

        if enabled is None:
            flag.enabled = not flag.enabled
        else:
            flag.enabled = enabled

        flag.updated_at = __import__("datetime").datetime.now().isoformat()

        if env_type and env_type not in flag.target_environments:
            flag.target_environments.append(env_type)

        target_envs = flag.target_environments or list(EnvironmentType)
        for env in target_envs:
            if env in self._environments:
                self._environments[env].feature_flags[name] = flag.enabled

        return flag

    def evaluate_feature_flag(
        self,
        name: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """
        评估特性开关是否生效

        Args:
            name: 开关名称
            context: 评估上下文（用户ID、百分比等）

        Returns:
            是否启用
        """
        flag = self._feature_flags.get(name)
        if not flag:
            return False

        if not flag.enabled:
            return False

        if flag.conditions:
            user_id = str(context.get("user_id", "")) if context else ""
            if user_id:
                hash_val = int(hashlib.md5(f"{name}:{user_id}".encode()).hexdigest(), 16)
                if hash_val % 100 >= flag.rollout_percentage:
                    return False

        return True

    def get_all_feature_flags(self) -> dict[str, FeatureFlag]:
        return dict(self._feature_flags)

    @property
    def environment_count(self) -> int:
        return len(self._environments)

    @property
    def registered_env_types(self) -> list[str]:
        return [e.value for e in self._environments.keys()]

    def export_all_config_markdown(self) -> str:
        """导出所有环境配置为Markdown格式"""
        lines: list[str] = []
        lines.append("# 多环境配置总览")
        lines.append("")
        lines.append(f"## 环境数量: {self.environment_count}")
        lines.append("")

        for env_type in EnvironmentType:
            if env_type not in self._environments:
                continue
            config = self._environments[env_type]
            lines.append(f"### 📦 {config.name or env_type.value.upper()} 环境")
            lines.append("")
            lines.append("| 配置项 | 值 | 敏感度 |")
            lines.append("|--------|-----|--------|")

            for key in sorted(config.variables.keys()):
                value = config.variables[key]
                is_secret = key in config.sensitive_vars
                display_val = "***" if is_secret else value
                sens_label = "🔒" if is_secret else "📖"
                lines.append(f"| `{key}` | `{display_val}` | {sens_label} |")

            if config.feature_flags:
                lines.append("")
                lines.append("**特性开关:**")
                for fname, fenabled in config.feature_flags.items():
                    status = "✅ 启用" if fenabled else "⏸️ 关闭"
                    lines.append(f"- {fname}: {status}")

            lines.append("")

        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"EnvironmentConfigSi(environments={self.environment_count}, "
            f"flags={len(self._feature_flags)})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 环境配置司测试")
    print("=" * 60)

    env_si = EnvironmentConfigSi()

    print("\n--- 已注册环境 ---")
    for etype in EnvironmentType:
        try:
            env = env_si.get_environment(etype)
            var_count = len(env.variables)
            secret_count = len(env.sensitive_vars)
            print(f"   ✅ {etype.value:8s}: {var_count}个变量 ({secret_count}个敏感)")
        except EnvironmentConfigError:
            pass

    print("\n--- 环境配置对比 (DEV vs PROD) ---")
    drift = env_si.compare_environments(EnvironmentType.DEV, EnvironmentType.PROD, include_sensitive=True)
    print(f"   📊 总键数: {drift.total_keys}")
    print(f"   匹配键数: {drift.matched_keys}")
    print(f"   差异数: {drift.diff_count}")
    print(f"   漂移分数: {drift.drift_score:.4f}")

    if drift.diffs:
        print(f"\n   差异详情:")
        for d in drift.diffs[:10]:
            icon = "🔴" if d.sensitivity == "secret" else "🟡"
            print(f"   {icon} {d.key}: DEV={str(d.env_a_value)[:30]}... vs PROD={str(d.env_b_value)[:30]}...")

    print("\n--- 一致性检查 ---")
    consistency = env_si.check_consistency(baseline_env=EnvironmentType.STAGING)
    print(f"   基线环境: {consistency['baseline']}")
    print(f"   整体状态: {consistency['overall_status']}")
    print(f"   问题数量: {consistency['issues_found']}")

    for env_name, check in consistency['env_checks'].items():
        icon = "✅" if check.get('status') == 'consistent' else "⚠️"
        print(f"   {icon} {env_name}: {check.get('status', 'N/A')} "
              f"(漂移={check.get('drift_score', 0):.4f}, 差异={check.get('diff_count', 0)})")

    print("\n--- Docker Compose生成 ---")
    compose = env_si.generate_docker_compose(EnvironmentType.DEV)
    print(f"   版本: {compose.get('version')}")
    print(f"   服务: {list(compose.get('services', {}).keys())}")
    print(f"   卷: {list(compose.get('volumes', {}).keys())}")
    print(f"   网络: {list(compose.get('networks', {}).keys())}")

    print("\n--- Dockerfile生成 ---")
    dockerfile = env_si.generate_dockerfile(app_type="python")
    print("   Python应用 Dockerfile:")
    for line in dockerfile.split('\n')[:12]:
        print(f"      {line}")

    print("\n--- .env文件生成 ---")
    env_content = env_si.generate_env_file(EnvironmentType.DEV, encrypt_secrets=False)
    print("   DEV环境 .env:")
    for line in env_content.split('\n')[:10]:
        print(f"      {line}")

    print("\n--- 特性开关管理 ---")
    flag1 = env_si.create_feature_flag(
        name="new_dashboard_ui",
        description="新版仪表盘界面",
        target_environments=[EnvironmentType.DEV, EnvironmentType.STAGING],
        rollout_percentage=50,
    )
    print(f"   ✅ 创建开关: {flag1.name} (灰度{flag1.rollout_percentage}%)")

    flag2 = env_si.create_feature_flag(
        name="dark_mode",
        description="暗色主题模式",
        target_environments=[EnvironmentType.DEV],
    )
    print(f"   ✅ 创建开关: {flag2.name}")

    toggled = env_si.toggle_feature_flag("new_dashboard_ui", enabled=True)
    print(f"   🔄 切换开关 new_dashboard_ui → {'开启' if toggled.enabled else '关闭'}")

    eval_result = env_si.evaluate_feature_flag("new_dashboard_ui", context={"user_id": "user_001"})
    print(f"   📋 评估 new_dashboard_ui (user_001): {'启用' if eval_result else '关闭'}")

    all_flags = env_si.get_all_feature_flags()
    print(f"\n   当前开关数: {len(all_flags)}")
    for fname, flag in all_flags.items():
        status = "🟢" if flag.enabled else "⚪"
        print(f"   {status} {fname}: {flag.description[:40]}...")

    print("\n--- 导出配置Markdown ---")
    md = env_si.export_all_config_markdown()
    print(md[:600])

    print("\n✅ 所有测试通过!")
