"""
路径配置中心 - 统一管理所有路径配置
提供路径验证、动态解析、健康检查、快照管理等能力
"""
from __future__ import annotations

import json
import copy
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class PathConfigError(Exception):
    """路径配置相关异常"""
    pass


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True)
class PathConfig:
    """预定义路径常量"""
    SKILL_ROOT: Path = field(default=Path("."))
    SCRIPTS_DIR: Path = field(default=Path("skillscripts"))
    CORE_DIR: Path = field(default=Path("skillscripts/core"))
    SUBSKILLS_DIR: Path = field(default=Path("subskills"))
    TEMPLATES_DIR: Path = field(default=Path("templates"))
    CONFIGS_DIR: Path = field(default=Path("configs"))
    DOCS_DIR: Path = field(default=Path("docs"))
    OUTPUT_DIR: Path = field(default=Path("output"))

    OUTPUT_REQUIREMENTS: Path = field(default=Path("output/requirements"))
    OUTPUT_ARCHITECTURE: Path = field(default=Path("output/architecture"))
    OUTPUT_API: Path = field(default=Path("output/api"))
    OUTPUT_DATABASE: Path = field(default=Path("output/database"))
    OUTPUT_TESTING: Path = field(default=Path("output/testing"))
    OUTPUT_REVIEWS: Path = field(default=Path("output/reviews"))
    OUTPUT_DEPLOYMENT: Path = field(default=Path("output/deployment"))
    OUTPUT_ITERATION: Path = field(default=Path("output/iteration"))
    OUTPUT_MONITORING: Path = field(default=Path("output/monitoring"))
    OUTPUT_LOGS: Path = field(default=Path("output/logs"))

    HARNESS_DIR: Path = field(default=Path(".harness"))
    AGENCY_AGENTS_DIR: Path = field(default=Path("../agency-agents"))
    EVOLUTION_LOGS_DIR: Path = field(default=Path("logs/evolution_logs"))
    DECISION_LOGS_DIR: Path = field(default=Path("logs/decision_logs"))
    AUDIT_TRAILS_DIR: Path = field(default=Path("logs/audit_trials"))

    PROVINCES: list[str] = field(
        default_factory=lambda: ["zhongshusheng", "menxiasheng", "shangshusheng"]
    )
    DEPARTMENTS: list[str] = field(
        default_factory=lambda: [
            "libu", "hubu", "libu2", "bingbu", "gongbu", "xingbu",
            "requirements_bureau", "architecture_bureau", "standards_bureau",
            "review_bureau", "code_review_bureau", "testing_bureau",
            "quality_monitor_bureau", "compliance_bureau"
        ]
    )


@dataclass
class HealthReport:
    """路径健康报告"""
    status: HealthStatus
    total_paths: int = 0
    existing_count: int = 0
    missing_count: int = 0
    writable_count: int = 0
    not_writable_count: int = 0
    details: dict[str, dict] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def health_percentage(self) -> float:
        if self.total_paths == 0:
            return 0.0
        return (self.existing_count / self.total_paths) * 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "total_paths": self.total_paths,
            "existing_count": self.existing_count,
            "missing_count": self.missing_count,
            "writable_count": self.writable_count,
            "not_writable_count": self.not_writable_count,
            "health_percentage": round(self.health_percentage, 2),
            "details": self.details,
            "timestamp": self.timestamp,
        }


class PathConfigCenter:
    """
    路径配置中心

    统一管理所有路径配置，提供验证、健康检查、快照管理等功能。
    基于项目根目录自动解析所有子路径，支持动态导入导出配置。
    """

    _instance: PathConfigCenter | None = None

    def __init__(self, project_root: Path | str) -> None:
        self._project_root: Path = Path(project_root).resolve()
        self._paths: dict[str, Path] = {}
        self._config: PathConfig = PathConfig()
        self._snapshot_cache: dict[str, Any] = {}
        self._initialize_paths()

    def _initialize_paths(self) -> None:
        """初始化所有路径映射"""
        root = self._project_root
        config_fields: dict[str, Path] = {
            name: getattr(self._config, name)
            for name in dir(self._config)
            if isinstance(getattr(self._config, name, None), Path)
        }
        for key, rel_path in config_fields.items():
            self._paths[key] = (root / rel_path).resolve()

    @classmethod
    def init_project(cls, root: Path | str) -> PathConfigCenter:
        """
        一键初始化新项目

        Args:
            root: 项目根目录路径

        Returns:
            初始化完成的PathConfigCenter实例
        """
        center = cls(root)
        created = center.ensure_dirs()
        print(f"✅ 项目初始化完成: {root}")
        print(f"   已创建 {len(created)} 个目录")
        return center

    def validate(self) -> dict[str, Any]:
        """
        验证所有路径是否存在/可写

        Returns:
            包含每个路径诊断信息的字典
        """
        report: dict[str, Any] = {
            "project_root": str(self._project_root),
            "total_paths": len(self._paths),
            "results": {},
            "errors": [],
            "warnings": [],
        }

        for key, path in self._paths.items():
            exists = path.exists()
            is_dir = path.is_dir() if exists else False
            is_file = path.is_file() if exists else False
            try:
                writable = os.access(path, os.W_OK) if exists else False
            except Exception:
                writable = False

            result: dict[str, Any] = {
                "key": key,
                "path": str(path),
                "exists": exists,
                "type": "directory" if is_dir else ("file" if is_file else "nonexistent"),
                "writable": writable,
            }

            if not exists:
                report["warnings"].append(f"路径不存在: {key} -> {path}")
            elif not writable and is_dir:
                report["warnings"].append(f"目录不可写: {key} -> {path}")

            report["results"][key] = result

        return report

    def health_check(self) -> HealthReport:
        """
        生成路径健康报告

        Returns:
            HealthReport对象，包含详细健康状态信息
        """
        total = len(self._paths)
        existing = 0
        missing = 0
        writable = 0
        not_writable = 0
        details: dict[str, dict] = {}

        for key, path in self._paths.items():
            exists = path.exists()
            is_dir = path.is_dir() if exists else False

            if exists:
                existing += 1
                try:
                    can_write = os.access(path, os.W_OK)
                except Exception:
                    can_write = False

                if can_write and is_dir:
                    writable += 1
                elif is_dir:
                    not_writable += 1
            else:
                missing += 1

            details[key] = {
                "path": str(path),
                "exists": exists,
                "writable": os.access(path, os.W_OK) if exists else False,
            }

        if missing == 0 and not_writable == 0:
            status = HealthStatus.HEALTHY
        elif missing > total * 0.3 or not_writable > total * 0.3:
            status = HealthStatus.CRITICAL
        else:
            status = HealthStatus.WARNING

        return HealthReport(
            status=status,
            total_paths=total,
            existing_count=existing,
            missing_count=missing,
            writable_count=writable,
            not_writable_count=not_writable,
            details=details,
        )

    def ensure_dirs(self) -> list[Path]:
        """
        自动创建不存在的目录

        Returns:
            新创建的目录路径列表
        """
        created: list[Path] = []
        for key, path in self._paths.items():
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    created.append(path)
                except OSError as e:
                    raise PathConfigError(f"无法创建目录 {path}: {e}") from e
        return created

    def get_path(self, key: str) -> Path:
        """
        根据键名获取路径

        Args:
            key: 路径键名（如 SKILL_ROOT, SCRIPTS_DIR 等）

        Returns:
            对应的绝对路径

        Raises:
            PathConfigError: 当键名不存在时
        """
        if key not in self._paths:
            available = ", ".join(sorted(self._paths.keys()))
            raise PathConfigError(
                f"未知的路径键: '{key}'。可用键: {available}"
            )
        return self._paths[key]

    def resolve_relative(self, rel_path: str) -> Path:
        """
        解析相对路径为基于项目根目录的绝对路径

        Args:
            rel_path: 相对路径字符串

        Returns:
            解析后的绝对路径
        """
        return (self._project_root / rel_path).resolve()

    def export_config(self, output_path: Path | str, format: str = "json") -> None:
        """
        导出当前配置为JSON或YAML文件

        Args:
            output_path: 输出文件路径
            format: 导出格式 ('json' 或 'yaml')

        Raises:
            PathConfigError: 当格式不支持或写入失败时
        """
        output = Path(output_path)
        data: dict[str, Any] = {
            "project_root": str(self._project_root),
            "exported_at": datetime.now().isoformat(),
            "paths": {k: str(v) for k, v in self._paths.items()},
        }

        match format.lower():
            case "json":
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            case "yaml":
                try:
                    import yaml
                except ImportError as e:
                    raise PathConfigError(
                        "需要安装PyYAML库才能导出YAML格式"
                    ) from e
                with open(output, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            case _:
                raise PathConfigError(f"不支持的导出格式: {format}，仅支持 json 和 yaml")

    def import_config(self, config_path: Path | str) -> None:
        """
        从文件导入配置并更新当前路径映射

        Args:
            config_path: 配置文件路径（JSON或YAML）

        Raises:
            PathConfigError: 当文件不存在或格式错误时
        """
        path = Path(config_path)
        if not path.exists():
            raise PathConfigError(f"配置文件不存在: {path}")

        suffix = path.suffix.lower()
        match suffix:
            case ".json":
                with open(path, "r", encoding="utf-8") as f:
                    data: dict[str, Any] = json.load(f)
            case ".yaml" | ".yml":
                try:
                    import yaml
                except ImportError as e:
                    raise PathConfigError(
                        "需要安装PyYAML库才能导入YAML格式"
                    ) from e
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            case _:
                raise PathConfigError(f"不支持的配置文件格式: {suffix}")

        if "paths" not in data:
            raise PathConfigError("配置文件缺少 'paths' 字段")

        for key, value in data["paths"].items():
            self._paths[key] = Path(value).resolve()

    def snapshot(self) -> dict[str, Any]:
        """
        创建当前路径状态快照

        Returns:
            包含路径状态和元数据的快照字典
        """
        state: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self._project_root),
            "paths_state": {},
            "hash": "",
        }

        for key, path in self._paths.items():
            state["paths_state"][key] = {
                "path": str(path),
                "exists": path.exists(),
                "is_dir": path.is_dir() if path.exists() else None,
                "mtime": (
                    datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                    if path.exists()
                    else None
                ),
            }

        snapshot_str = json.dumps(state["paths_state"], sort_keys=True)
        state["hash"] = hashlib.md5(snapshot_str.encode()).hexdigest()

        self._snapshot_cache = copy.deepcopy(state)
        return state

    def restore(self, snapshot: dict[str, Any]) -> bool:
        """
        从快照恢复路径状态

        Args:
            snapshot: 之前创建的快照字典

        Returns:
            是否恢复成功

        Raises:
            PathConfigError: 当快照无效时
        """
        if "paths_state" not in snapshot:
            raise PathConfigError("无效的快照数据：缺少 paths_state")

        restored_count = 0
        for key, info in snapshot["paths_state"].items():
            original_path_str: str = info.get("path", "")
            if not original_path_str:
                continue

            original_path = Path(original_path_str)
            existed_before: bool | None = info.get("exists")

            if existed_before and not original_path.exists():
                try:
                    original_path.mkdir(parents=True, exist_ok=True)
                    restored_count += 1
                except OSError as e:
                    print(f"⚠️ 恢复目录失败 {original_path}: {e}")

            self._paths[key] = original_path.resolve()

        print(f"📦 快照恢复完成，恢复 {restored_count} 个目录")
        return True

    def check_path_length(self, path: Path, max_length: int = 260) -> dict[str, Any]:
        """
        检查路径长度是否超过限制（Windows默认260字符）

        Args:
            path: 待检查的路径
            max_length: 最大允许长度

        Returns:
            包含检查结果的字典
        """
        path_str = str(path)
        length = len(path_str)
        return {
            "path": path_str,
            "length": length,
            "max_length": max_length,
            "exceeds_limit": length > max_length,
            "overflow": max(0, length - max_length),
            "platform": "windows" if os.name == "nt" else "posix",
        }

    def auto_fix_broken_paths(self) -> dict[str, Any]:
        """
        自动修复断链路径引用

        Returns:
            修复结果报告
        """
        fixed = []
        failed = []
        for key, path in self._paths.items():
            if not path.exists():
                try:
                    if key.endswith("_DIR") or key.startswith("OUTPUT_") or key.endswith("_LOGS_DIR"):
                        path.mkdir(parents=True, exist_ok=True)
                        fixed.append({"key": key, "path": str(path), "action": "created"})
                except OSError as e:
                    failed.append({"key": key, "path": str(path), "error": str(e)})
        return {"fixed_count": len(fixed), "fixed": fixed, "failed_count": len(failed), "failed": failed}

    def get_platform_info(self) -> dict[str, str]:
        """
        获取当前平台信息

        Returns:
            平台信息字典
        """
        import platform
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "path_separator": os.sep,
            "home_dir": str(Path.home()),
        }

    def generate_diagnostic_report(self) -> str:
        """
        生成完整的路径诊断报告

        Returns:
            Markdown格式的诊断报告
        """
        health = self.health_check()
        platform_info = self.get_platform_info()
        lines = [
            "# 路径配置诊断报告",
            f"\n**生成时间**: {health.timestamp}",
            f"**项目根目录**: {self._project_root}",
            f"\n## 平台信息\n",
            f"- 系统: {platform_info['system']} {platform_info['release']}",
            f"- 架构: {platform_info['machine']}",
            f"- 路径分隔符: `{platform_info['path_separator']}`",
            f"\n## 健康状态: {health.status.value.upper()}\n",
            f"- 总路径数: {health.total_paths}",
            f"- 已存在: {health.existing_count}",
            f"- 缺失: {health.missing_count}",
            f"- 健康度: **{health.health_percentage:.1f}%**",
            "\n## 路径长度检查\n",
        ]
        long_paths = []
        for key, path in self._paths.items():
            check = self.check_path_length(path)
            if check["exceeds_limit"]:
                long_paths.append(check)
                lines.append(f"- ⚠️ `{key}`: {check['length']}字符 (超限{check['overflow']}字符)")
        if not long_paths:
            lines.append("- ✅ 所有路径长度正常")
        if health.missing_count > 0:
            lines.append("\n## 缺失路径\n")
            for key, detail in health.details.items():
                if not detail["exists"]:
                    lines.append(f"- ❌ `{key}`: {detail['path']}")
        return "\n".join(lines)

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def all_paths(self) -> dict[str, Path]:
        return dict(self._paths)

    def __repr__(self) -> str:
        return (
            f"PathConfigCenter(root={self._project_root}, "
            f"paths_count={len(self._paths)})"
        )


import os


if __name__ == "__main__":
    test_root = Path(__file__).parent.parent.parent
    print("=" * 60)
    print("🧪 路径配置中心测试")
    print("=" * 60)

    pcc = PathConfigCenter(test_root)
    print(f"\n📍 项目根目录: {pcc.project_root}")
    print(f"📂 总路径数: {len(pcc.all_paths)}")

    print("\n--- 验证测试 ---")
    validation = pcc.validate()
    print(f"总路径数: {validation['total_paths']}")
    print(f"警告数: {len(validation['warnings'])}")

    print("\n--- 健康检查 ---")
    health = pcc.health_check()
    print(f"状态: {health.status.value}")
    print(f"健康度: {health.health_percentage:.1f}%")
    print(f"存在: {health.existing_count}/{health.total_paths}")

    print("\n--- 确保目录存在 ---")
    created_dirs = pcc.ensure_dirs()
    print(f"新建目录数: {len(created_dirs)}")

    print("\n--- 快照与恢复测试 ---")
    snap = pcc.snapshot()
    print(f"快照哈希: {snap['hash'][:12]}...")
    print(f"快照时间戳: {snap['timestamp']}")

    print("\n--- 获取特定路径示例 ---")
    print(f"SCRIPTS_DIR: {pcc.get_path('SCRIPTS_DIR')}")
    print(f"TEMPLATES_DIR: {pcc.get_path('TEMPLATES_DIR')}")

    print("\n--- 导出配置测试 ---")
    export_path = test_root / "configs" / "path_config_test.json"
    pcc.export_config(export_path)
    print(f"配置已导出至: {export_path}")

    print("\n✅ 所有测试通过!")
