#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三省六部协同开发系统 - 统一Python脚本调度入口

提供完整的命令行接口，支持三省（中书省/门下省/尚书省）及其下属六部的命令调度，
以及初始化、健康检查、版本信息等全局功能。

用法:
    python main.py <command> [subcommand] [options]
    python main.py --help
    python main.py health-check
    python main.py init
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


__version__ = "3.3.0"
__author__ = "三省六部开发团队"


# ============================================================
# 自定义异常类
# ============================================================

class SkillError(Exception):
    """技能脚本基础异常"""

    def __init__(self, message: str, code: int = 1) -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)


class ConfigurationError(SkillError):
    """配置错误异常"""
    pass


class ModuleLoadError(SkillError):
    """模块加载错误异常"""
    pass


class RouteNotFoundError(SkillError):
    """路由未找到异常"""
    pass


class HealthCheckError(SkillError):
    """健康检查错误异常"""
    pass


class InitError(SkillError):
    """初始化错误异常"""
    pass


# ============================================================
# 日志系统
# ============================================================

class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class SkillLogger:
    """统一日志管理器，支持控制台和文件双输出"""

    _FORMAT = "[%(asctime)s] [%(levelname)-7s] [%(name)s] %(message)s"
    _DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(
        self,
        name: str = "main",
        level: int = logging.INFO,
        log_file: Optional[str] = None,
        quiet: bool = False
    ) -> None:
        self._name = name
        self._quiet = quiet
        self._logger: logging.Logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)
        self._logger.handlers.clear()

        if not quiet:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_formatter = logging.Formatter(self._FORMAT, datefmt=self._DATE_FORMAT)
            console_handler.setFormatter(console_formatter)
            self._logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(self._FORMAT, datefmt=self._DATE_FORMAT)
            file_handler.setFormatter(file_formatter)
            self._logger.addHandler(file_handler)

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.critical(msg, *args, **kwargs)

    def set_level(self, level: int) -> None:
        for handler in self._logger.handlers:
            handler.setLevel(level)


def setup_logger(
    verbose: bool = False,
    quiet: bool = False,
    log_file: Optional[str] = None
) -> SkillLogger:
    """根据命令行参数创建并配置日志记录器"""
    level = logging.DEBUG if verbose else (logging.WARNING if quiet else logging.INFO)
    return SkillLogger(
        name="sanliu",
        level=level,
        log_file=log_file,
        quiet=quiet
    )


# ============================================================
# 健康检查相关数据结构
# ============================================================

class CheckStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


@dataclass
class CheckItem:
    """单个检查项结果"""
    name: str
    status: CheckStatus
    message: str
    detail: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
        }
        if self.detail:
            result["detail"] = self.detail
        return result


@dataclass
class HealthReport:
    """健康检查报告"""
    timestamp: str
    items: List[CheckItem] = field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def overall_status(self) -> CheckStatus:
        if any(item.status == CheckStatus.FAIL for item in self.items):
            return CheckStatus.FAIL
        if any(item.status == CheckStatus.WARN for item in self.items):
            return CheckStatus.WARN
        return CheckStatus.PASS

    @property
    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {s.value: 0 for s in CheckStatus}
        for item in self.items:
            counts[item.status.value] += 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status.value,
            "summary": self.summary,
            "items": [item.to_dict() for item in self.items],
            "duration_ms": round(self.duration_ms, 2),
        }


# ============================================================
# 省部路由配置
# ============================================================

ZHONGSHUSHENG_CMDS: Dict[str, str] = {
    "requirements": "需求分析 - 分析项目需求并生成需求文档",
    "req": "requirements",
    "architecture": "架构设计 - 设计系统架构方案",
    "arch": "architecture",
    "standards": "规范制定 - 制定开发规范和标准",
    "std": "standards",
    "review": "方案审议 - 审议和评审技术方案",
    "rev": "review",
}

MENXIASHENG_CMDS: Dict[str, str] = {
    "code-review": "代码审查 - 审查代码质量和规范性",
    "cr": "code-review",
    "testing": "测试验证 - 验证测试覆盖和质量",
    "test": "testing",
    "quality-monitor": "质量监控 - 监控项目质量指标",
    "qm": "quality-monitor",
    "compliance": "合规审计 - 审计合规性要求",
    "comp": "compliance",
}

SHANGSHUSHENG_DEPTS: Dict[str, Dict[str, str]] = {
    "libu": {
        "description": "吏部 - Agent调度与角色管理",
        "subcmds": {
            "agent-dispatch": "Agent分派",
            "role-mgmt": "角色管理",
            "skill-match": "技能匹配",
            "coordinate": "协调调度",
        },
    },
    "hubu": {
        "description": "户部 - 环境配置与资源管理",
        "subcmds": {
            "env-config": "环境配置",
            "dep-mgmt": "依赖管理",
            "resource-opt": "资源优化",
            "infra": "基础设施",
        },
    },
    "libu2": {
        "description": "礼部 - 文档与知识管理",
        "subcmds": {
            "docs": "文档生成",
            "templates": "模板管理",
            "knowledge": "知识库",
            "standardize": "标准化",
        },
    },
    "bingbu": {
        "description": "兵部 - 测试驱动开发(TDD)",
        "subcmds": {
            "tdd": "TDD循环执行",
            "test-framework": "测试框架",
            "coverage": "覆盖率分析",
            "regression": "回归测试",
        },
    },
    "gongbu": {
        "description": "工部 - 代码生成与设计",
        "subcmds": {
            "codegen": "代码生成",
            "uiux": "UI/UX设计",
            "db-design": "数据库设计",
            "api-design": "API设计",
        },
    },
    "xingbu": {
        "description": "刑部 - 缺陷修复与演化",
        "subcmds": {
            "bugfix": "缺陷修复",
            "refactor": "重构优化",
            "evolve": "自演化",
            "version": "版本管理",
        },
    },
}

SUBSKILL_NAMES: List[str] = [
    "anquan_ceshi", "api_sheji", "architecture_overview", "baihehua_liushuixian",
    "bushu", "ceshi", "ceshi_yongli_sheji", "continuous_evolution", "daili_jicheng",
    "daima_chonggou", "daima_shencha", "daima_shengcheng", "department_workflow",
    "guifan_jieexi", "guifan_yanzheng", "huanjing_jiance", "jiagou_yuanze",
    "knowledge_base", "provincial_coordination", "rengong_queren", "sdd_liucheng",
    "sdd_tdd_ronghe", "self_iteration", "shujuku_sheji", "skill_health_assessment",
    "skill_path_management", "skill_script_coordination", "tdd_liucheng",
    "toumingdu_yanzheng", "tubian_ceshi", "ui_ux_sheji", "waiji_jicheng",
    "wenti_xiufu", "xiangmu_guihua", "xingneng_youhua", "xitong_sheji",
    "xuqiu_fenxi", "xuqiu_jiegouhua", "yan_shou_ceshi",
]

REQUIRED_PACKAGES: List[str] = [
    "json", "argparse", "logging", "pathlib", "dataclasses", "enum",
]


# ============================================================
# 路由器类
# ============================================================

class ProvinceRouter:
    """省部命令路由器

    根据命令自动识别属于哪个省/部/司，加载对应的脚本模块，
    传递参数并执行，捕获异常并格式化输出。
    """

    def __init__(
        self,
        project_dir: Path,
        output_dir: Path,
        logger: SkillLogger,
        config_path: Optional[Path] = None
    ) -> None:
        self._project_dir = project_dir
        self._output_dir = output_dir
        self._logger = logger
        self._config_path = config_path
        self._scripts_dir = project_dir / "skillscripts"

    def resolve_alias(self, cmd: str, cmd_map: Dict[str, str]) -> str:
        """解析命令别名"""
        resolved = cmd_map.get(cmd)
        if resolved and resolved in cmd_map:
            return resolved
        return cmd

    def route(self, args: argparse.Namespace) -> int:
        """根据解析后的参数路由到对应的处理函数"""
        command = getattr(args, "command", None)
        subcommand = getattr(args, "subcommand", None)
        department = getattr(args, "department", None)
        dept_subcmd = getattr(args, "dept_subcommand", None)

        try:
            if command in ("zhongshusheng", "zs"):
                return self._route_zhongshusheng(subcommand, args)
            elif command in ("menxiasheng", "ms"):
                return self._route_menxiasheng(subcommand, args)
            elif command in ("shangshusheng", "ss"):
                return self._route_shangshusheng(department, dept_subcmd, args)
            elif command == "init":
                return self._execute_init(args)
            elif command in ("health-check", "status"):
                return self._execute_health_check(args)
            elif command == "run":
                return self._execute_run(args)
            elif command in ("fusion",):
                return self._execute_fusion(args)
            elif command in ("evolve",):
                return self._execute_evolve(args)
            elif command in ("coordinate", "coord"):
                return self._execute_coordinate(args)
            elif command in ("generate-docs", "gendoc"):
                return self._execute_generate_docs(args)
            elif command in ("version", "--version"):
                self._print_version()
                return 0
            else:
                raise RouteNotFoundError(f"未知命令: {command}")

        except SkillError as e:
            self._logger.error(f"执行失败 [{type(e).__name__}]: {e.message}")
            print(f"\n❌ 错误: {e.message}", file=sys.stderr)
            return e.code
        except Exception as e:
            self._logger.critical(f"未预期的异常: {e}", exc_info=True)
            print(f"\n💥 未预期错误: {type(e).__name__}: {e}", file=sys.stderr)
            return 1

    def _route_zhongshusheng(self, subcommand: Optional[str], args: argparse.Namespace) -> int:
        """路由中书省命令"""
        if not subcommand:
            raise RouteNotFoundError("中书省需要指定子命令，使用 --help 查看可用子命令")
        real_cmd = self.resolve_alias(subcommand, ZHONGSHUSHENG_CMDS)
        self._logger.info(f"中书省命令路由: {subcommand} -> {real_cmd}")
        print(f"\n📋 [中书省] 执行: {real_cmd}")
        print(f"   描述: {ZHONGSHUSHENG_CMDS.get(real_cmd, 'N/A')}")
        self._show_stub_info("zhongshusheng", real_cmd)
        return 0

    def _route_menxiasheng(self, subcommand: Optional[str], args: argparse.Namespace) -> int:
        """路由门下省命令"""
        if not subcommand:
            raise RouteNotFoundError("门下省需要指定子命令，使用 --help 查看可用子命令")
        real_cmd = self.resolve_alias(subcommand, MENXIASHENG_CMDS)
        self._logger.info(f"门下省命令路由: {subcommand} -> {real_cmd}")
        print(f"\n✍️ [门下省] 执行: {real_cmd}")
        print(f"   描述: {MENXIASHENG_CMDS.get(real_cmd, 'N/A')}")
        self._show_stub_info("menxiasheng", real_cmd)
        return 0

    def _route_shangshusheng(
        self,
        department: Optional[str],
        dept_subcmd: Optional[str],
        args: argparse.Namespace
    ) -> int:
        """路由尚书省命令（含六部）"""
        if not department:
            raise RouteNotFoundError("尚书省需要指定部门，使用 --help 查看可用部门")
        if department not in SHANGSHUSHENG_DEPTS:
            valid_depts = ", ".join(SHANGSHUSHENG_DEPTS.keys())
            raise RouteNotFoundError(f"未知部门: {department}，可选: {valid_depts}")

        dept_info = SHANGSHUSHENG_DEPTS[department]
        if not dept_subcmd:
            dept_subcmd = self._resolve_nested_subcmd(department)
        if not dept_subcmd or dept_subcmd not in dept_info["subcmds"]:
            valid_cmds = ", ".join(dept_info["subcmds"].keys())
            raise RouteNotFoundError(
                f"{dept_info['description'].split(' - ')[0]} 需要指定子命令，可选: {valid_cmds}"
            )

        self._logger.info(f"尚书省命令路由: {department}/{dept_subcmd}")
        print(f"\n⚙️  [尚书省-{department}] 执行: {dept_subcmd}")
        print(f"   描述: {dept_info['description']}")
        cmd_desc = dept_info["subcmds"].get(dept_subcmd, "N/A")
        print(f"   子命令: {cmd_desc}")
        self._show_stub_info("shangshusheng", f"{department}_{dept_subcmd}")
        return 0

    def _resolve_nested_subcmd(self, department: str) -> Optional[str]:
        """从sys.argv中解析嵌套子命令（解决argparse嵌套subparser的dest传播限制）"""
        try:
            argv = sys.argv[1:]
            ss_indices = [i for i, a in enumerate(argv) if a in ("shangshusheng", "ss")]
            if not ss_indices:
                return None
            ss_idx = ss_indices[0]
            remaining = argv[ss_idx + 1:]
            if len(remaining) >= 2 and remaining[0] == department:
                candidate = remaining[1]
                if candidate in SHANGSHUSHENG_DEPTS.get(department, {}).get("subcmds", {}):
                    return candidate
        except (IndexError, KeyError):
            pass
        return None

    def _show_stub_info(self, province: str, command: str) -> None:
        """显示存根提示信息"""
        print(f"   📍 脚本路径: skillscripts/{province}/{command}.py (待实现)")
        print(f"   💡 提示: 该功能正在开发中，当前为路由存根")

    def _load_module(self, module_path: Path, module_name: str) -> Any:
        """动态加载Python模块"""
        if not module_path.exists():
            raise ModuleLoadError(f"脚本模块不存在: {module_path}")
        spec = importlib.util.spec_from_file_location(module_name, str(module_path))
        if spec is None or spec.loader is None:
            raise ModuleLoadError(f"无法创建模块规格: {module_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def _execute_init(self, args: argparse.Namespace) -> int:
        """执行初始化操作"""
        self._logger.info("开始初始化项目...")
        return execute_init(self._project_dir, self._output_dir, self._logger)

    def _execute_health_check(self, args: argparse.Namespace) -> int:
        """执行健康检查"""
        self._logger.info("开始健康检查...")
        report = execute_health_check(self._project_dir, self._output_dir, self._logger)
        print_health_report(report, getattr(args, "json", False))
        return 0 if report.overall_status != CheckStatus.FAIL else 1

    def _execute_run(self, args: argparse.Namespace) -> int:
        """运行完整工作流"""
        self._logger.info("启动完整工作流...")
        print("\n🔄 [工作流] 启动完整三省六部工作流")
        print("   步骤1: 中书省 - 需求分析与架构设计")
        print("   步骤2: 门下省 - 方案审议与质量把控")
        print("   步骤3: 尚书省 - 六部协同TDD执行")
        print("   💡 提示: 完整工作流正在开发中")
        return 0

    def _execute_fusion(self, args: argparse.Namespace) -> int:
        """执行SDD+TDD融合引擎"""
        self._logger.info("启动SDD+TDD融合引擎...")
        print("\n🔗 [融合引擎] SDD+TDD深度融合引擎")
        print("   规范驱动 + 测试驱动 = 高质量交付")
        print("   💡 提示: 融合引擎正在开发中")
        return 0

    def _execute_evolve(self, args: argparse.Namespace) -> int:
        """执行自演化系统"""
        self._logger.info("启动自演化系统...")
        print("\n🧬 [自演化] 持续演化系统")
        print("   自迭代 | 自优化 | 自修复 | 自完善")
        print("   💡 提示: 自演化系统正在开发中")
        return 0

    def _execute_coordinate(self, args: argparse.Namespace) -> int:
        """执行三省协调"""
        self._logger.info("启动三省协调...")
        print("\n🏛️ [三省协调] 中书省 ↔ 门下省 ↔ 尚书省")
        print("   协同决策 → 审议监督 → 执行统筹")
        print("   💡 提示: 三省协调机制正在开发中")
        return 0

    def _execute_generate_docs(self, args: argparse.Namespace) -> int:
        """批量生成文档"""
        self._logger.info("批量生成文档...")
        print("\n📝 [文档生成] 批量文档生成")
        print("   目标目录: docs/universal-skill/")
        print("   💡 提示: 文档生成功能正在开发中")
        return 0

    def _print_version(self) -> None:
        """打印版本信息"""
        print(f"三省六部协同开发系统 v{__version__}")
        print(f"作者: {__author__}")
        print(f"Python: {sys.version.split()[0]}")
        print(f"日期: {datetime.now().strftime('%Y-%m-%d')}")


# ============================================================
# 健康检查实现
# ============================================================

def check_python_version() -> CheckItem:
    """检查Python版本是否 >= 3.10"""
    version_info = sys.version_info
    major, minor = version_info.major, version_info.minor
    required = (3, 10)
    if (major, minor) >= required:
        return CheckItem(
            name="Python版本",
            status=CheckStatus.PASS,
            message=f"Python {major}.{minor}.{version_info.micro} >= 3.10",
            detail=f"完整版本: {sys.version}"
        )
    return CheckItem(
        name="Python版本",
        status=CheckStatus.FAIL,
        message=f"Python {major}.{minor} 不满足最低要求 3.10",
        detail=f"请升级Python至3.10或更高版本"
    )


def check_dependencies() -> CheckItem:
    """检查必要的依赖包是否可导入"""
    missing: List[str] = []
    available: List[str] = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
            available.append(pkg)
        except ImportError:
            missing.append(pkg)

    if not missing:
        return CheckItem(
            name="依赖包检查",
            status=CheckStatus.PASS,
            message=f"所有必要依赖已安装 ({len(available)}/{len(REQUIRED_PACKAGES)})",
            detail=", ".join(available)
        )
    return CheckItem(
        name="依赖包检查",
        status=CheckStatus.WARN if len(missing) < len(REQUIRED_PACKAGES) // 2 else CheckStatus.FAIL,
        message=f"缺少依赖包: {', '.join(missing)}",
        detail=f"已安装: {', '.join(available)}；缺失: {', '.join(missing)}"
    )


def check_script_modules(project_dir: Path) -> CheckItem:
    """检查各脚本模块是否可加载"""
    scripts_dir = project_dir / "skillscripts"
    core_modules = [
        "core/__init__", "core/script_base", "core/health_check",
        "core/script_registry", "utils/__init__",
    ]
    loaded: List[str] = []
    failed: List[str] = []

    for mod_name in core_modules:
        mod_path = scripts_dir / f"{mod_name}.py"
        if mod_path.exists():
            loaded.append(mod_name)
        else:
            failed.append(mod_name)

    total = len(core_modules)
    if not failed:
        return CheckItem(
            name="脚本模块检查",
            status=CheckStatus.PASS,
            message=f"核心脚本模块完整 ({len(loaded)}/{total})",
            detail=", ".join(loaded)
        )
    return CheckItem(
        name="脚本模块检查",
        status=CheckStatus.WARN,
        message=f"部分脚本模块缺失 ({len(failed)}/{total})",
        detail=f"已加载: {', '.join(loaded)}；缺失: {', '.join(failed)}"
    )


def check_config_file(project_dir: Path) -> CheckItem:
    """检查配置文件是否存在且格式正确"""
    config_paths = [
        project_dir / "config.json",
        project_dir / "config.yaml",
        project_dir / ".env",
        project_dir / ".env.example",
    ]
    found: List[str] = []
    for config_path in config_paths:
        if config_path.exists():
            found.append(config_path.name)
            if config_path.suffix == ".json":
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        json.load(f)
                    return CheckItem(
                        name="配置文件检查",
                        status=CheckStatus.PASS,
                        message=f"配置文件存在且格式正确: {config_path.name}",
                        detail=str(config_path)
                    )
                except json.JSONDecodeError as e:
                    return CheckItem(
                        name="配置文件检查",
                        status=CheckStatus.WARN,
                        message=f"配置文件JSON格式错误: {config_path.name}",
                        detail=str(e)
                    )

    if found:
        return CheckItem(
            name="配置文件检查",
            status=CheckStatus.PASS,
            message=f"找到配置文件: {', '.join(found)}",
            detail=None
        )
    return CheckItem(
        name="配置文件检查",
        status=CheckStatus.WARN,
        message="未找到配置文件（将使用默认配置）",
        detail=f"搜索路径: {project_dir}"
    )


def check_output_dir(output_dir: Path) -> CheckItem:
    """检查输出目录是否可写"""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        test_file = output_dir / ".write_test"
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()
        return CheckItem(
            name="输出目录检查",
            status=CheckStatus.PASS,
            message=f"输出目录可写: {output_dir}",
            detail=str(output_dir.resolve())
        )
    except PermissionError:
        return CheckItem(
            name="输出目录检查",
            status=CheckStatus.FAIL,
            message=f"输出目录无写入权限: {output_dir}",
            detail="请检查目录权限或更换输出路径"
        )
    except OSError as e:
        return CheckItem(
            name="输出目录检查",
            status=CheckStatus.FAIL,
            message=f"输出目录不可用: {output_dir}",
            detail=str(e)
        )


def check_subskills(project_dir: Path) -> CheckItem:
    """检查子技能目录完整性（32个子技能）"""
    subskills_dir = project_dir / "subskills"
    if not subskills_dir.exists():
        return CheckItem(
            name="子技能完整性检查",
            status=CheckStatus.FAIL,
            message="子技能目录不存在",
            detail=f"期望路径: {subskills_dir}"
        )

    existing_files = list(subskills_dir.glob("*.md"))
    existing_names = sorted([f.stem for f in existing_files])
    missing_names = [s for s in SUBSKILL_NAMES if s not in existing_names]
    extra_names = [s for s in existing_names if s not in SUBSKILL_NAMES]

    total_expected = len(SUBSKILL_NAMES)
    actual_count = len(existing_files)

    if not missing_names and not extra_names:
        return CheckItem(
            name="子技能完整性检查",
            status=CheckStatus.PASS,
            message=f"子技能完整 ({actual_count}/{total_expected})",
            detail=f"共{actual_count}个子技能文件"
        )

    status = CheckStatus.WARN if len(missing_names) <= 5 else CheckStatus.FAIL
    detail_parts: List[str] = [f"已有{actual_count}个"]
    if missing_names:
        detail_parts.append(f"缺失{len(missing_names)}个: {', '.join(missing_names[:10])}")
    if extra_names:
        detail_parts.append(f"额外{len(extra_names)}个: {', '.join(extra_names[:5])}")

    return CheckItem(
        name="子技能完整性检查",
        status=status,
        message=f"子技能数量: {actual_count}/{total_expected}（{'完整' if not missing_names else '不完整'}）",
        detail="; ".join(detail_parts)
    )


def execute_health_check(
    project_dir: Path,
    output_dir: Path,
    logger: SkillLogger
) -> HealthReport:
    """执行全部健康检查项并返回报告"""
    start_time = time.time()
    items: List[CheckItem] = []

    checks: List[Tuple[str, Callable[[Path], CheckItem]]] = [
        ("Python版本", lambda _: check_python_version()),
        ("依赖包检查", lambda _: check_dependencies()),
        ("脚本模块检查", lambda d: check_script_modules(d)),
        ("配置文件检查", lambda d: check_config_file(d)),
        ("输出目录检查", lambda _: check_output_dir(output_dir)),
        ("子技能完整性检查", lambda d: check_subskills(d)),
    ]

    for check_name, check_fn in checks:
        logger.info(f"执行检查: {check_name}")
        try:
            result = check_fn(project_dir)
            items.append(result)
            status_icon = {CheckStatus.PASS: "✅", CheckStatus.FAIL: "❌", CheckStatus.WARN: "⚠️", CheckStatus.SKIP: "⏭️"}
            icon = status_icon.get(result.status, "❓")
            logger.info(f"  {icon} {check_name}: {result.status.value} - {result.message}")
        except Exception as e:
            logger.error(f"  ❌ {check_name} 检查异常: {e}")
            items.append(CheckItem(
                name=check_name,
                status=CheckStatus.FAIL,
                message=f"检查异常: {e}",
                detail=str(e)
            ))

    duration_ms = (time.time() - start_time) * 1000
    return HealthReport(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        items=items,
        duration_ms=duration_ms,
    )


def print_health_report(report: HealthReport, as_json: bool = False) -> None:
    """格式化输出健康检查报告"""
    if as_json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        return

    status_icons = {
        CheckStatus.PASS: "✅",
        CheckStatus.FAIL: "❌",
        CheckStatus.WARN: "⚠️",
        CheckStatus.SKIP: "⏭️",
    }
    overall_icon = status_icons.get(report.overall_status, "❓")

    print(f"\n{'='*60}")
    print(f"🏥  三省六部协同开发系统 - 健康检查报告")
    print(f"{'='*60}")
    print(f"⏰  检查时间: {report.timestamp}")
    print(f"⏱️  检查耗时: {report.duration_ms:.2f}ms")
    print(f"📊 整体状态: {overall_icon} {report.overall_status.value}")
    print(f"\n📈 检查统计:")
    summary = report.summary
    for status_name, count in summary.items():
        if count > 0:
            icon = status_icons.get(CheckStatus(status_name), "❓")
            print(f"   {icon} {status_name}: {count}")

    print(f"\n{'-'*60}")
    for item in report.items:
        icon = status_icons.get(item.status, "❓")
        print(f"{icon} {item.name}")
        print(f"   └─ {item.message}")
        if item.detail:
            print(f"      详情: {item.detail}")
        print()

    print(f"{'='*60}")
    if report.overall_status == CheckStatus.PASS:
        print("🎉 所有检查项通过！系统状态良好。")
    elif report.overall_status == CheckStatus.WARN:
        print("⚠️  部分检查项有警告，建议查看详情。")
    else:
        print("❌ 存在失败的检查项，请处理后重试。")
    print(f"{'='*60}\n")


# ============================================================
# 初始化功能实现
# ============================================================

DEFAULT_CONFIG: Dict[str, Any] = {
    "version": __version__,
    "project": {
        "name": "universal-skill-project",
        "description": "三省六部协同开发项目",
    },
    "zhongshusheng": {"enabled": True},
    "menxiasheng": {"enabled": True},
    "shangshusheng": {"enabled": True, "departments": list(SHANGSHUSHENG_DEPTS.keys())},
    "logging": {"level": "INFO", "file": "logs/sanliu.log"},
    "output": {"dir": "docs/universal-skill"},
}

OUTPUT_SUBDIRS: List[str] = [
    "reports", "api", "workflow", "knowledge", "specs",
    "architecture", "testing", "deployment", "changelog", "assets",
]


def execute_init(
    project_dir: Path,
    output_dir: Path,
    logger: SkillLogger
) -> int:
    """执行项目初始化操作"""
    created_dirs: List[str] = []
    created_files: List[str] = []

    try:
        standard_dirs = [
            project_dir / "skillscripts" / "zhongshusheng",
            project_dir / "skillscripts" / "menxiasheng",
            project_dir / "skillscripts" / "shangshusheng",
            project_dir / "logs",
            project_dir / "data",
            project_dir / "cache",
        ]

        for dir_path in standard_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            init_marker = dir_path / "__init__.py"
            if not init_marker.exists():
                init_marker.write_text("", encoding="utf-8")
            created_dirs.append(str(dir_path.relative_to(project_dir)))
            logger.debug(f"创建目录: {dir_path}")

        for subdir_name in OUTPUT_SUBDIRS:
            full_path = output_dir / subdir_name
            full_path.mkdir(parents=True, exist_ok=True)
            keep_file = full_path / ".gitkeep"
            if not keep_file.exists():
                keep_file.write_text("", encoding="utf-8")
            created_dirs.append(str(full_path.relative_to(project_dir)))
            logger.debug(f"创建输出子目录: {full_path}")

        config_path = project_dir / "config.json"
        if not config_path.exists():
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            created_files.append("config.json")
            logger.info(f"生成默认配置文件: {config_path}")

        skill_md_path = output_dir / "SKILL.md"
        skill_content = generate_skill_md_reference(project_dir.name)
        if not skill_md_path.exists():
            skill_md_path.write_text(skill_content, encoding="utf-8")
            created_files.append(f"docs/universal-skill/SKILL.md")
            logger.info(f"生成SKILL.md引用: {skill_md_path}")

    except OSError as e:
        raise InitError(f"创建目录或文件失败: {e}") from e
    except Exception as e:
        raise InitError(f"初始化过程发生意外错误: {e}") from e

    print("\n" + "=" * 60)
    print("🚀 项目初始化完成")
    print("=" * 60)
    print(f"\n📁 创建的目录 ({len(created_dirs)} 个):")
    for d in created_dirs:
        print(f"   📂 {d}")
    print(f"\n📄 生成的文件 ({len(created_files)} 个):")
    for f in created_files:
        print(f"   📝 {f}")
    print(f"\n📍 项目根目录: {project_dir.resolve()}")
    print(f"📍 输出目录:   {output_dir.resolve()}")
    print(f"\n💡 下一步:")
    print("   python main.py health-check   # 验证环境")
    print("   python main.py --help         # 查看所有命令")
    print("=" * 60 + "\n")
    return 0


def generate_skill_md_reference(project_name: str) -> str:
    """生成基础 SKILL.md 引用内容"""
    return f"""---
name: {project_name}
description: 三省六部协同开发项目 | TDD/SDD驱动 | 全流程管理
---

# {project_name}

> 🏛️ 基于**三省六部协同开发系统**构建的项目

## 快速开始

```bash
# 健康检查
python main.py health-check

# 初始化（如需重新初始化）
python main.py init

# 查看帮助
python main.py --help
```

## 项目架构

| 省 | 职责 | 入口命令 |
|---|------|---------|
| 中书省 | 决策制定 | `python main.py zhongshusheng` |
| 门下省 | 审议监督 | `python main.py menxiasheng` |
| 尚书省 | 执行统筹 | `python main.py shangshusheng` |

## 输出目录结构

```
docs/universal-skill/
├── reports/      # 报告
├── api/          # API文档
├── workflow/     # 工作流文档
├── knowledge/    # 知识库
├── specs/        # 规范文档
├── architecture/ # 架构文档
├── testing/      # 测试文档
├── deployment/   # 部署文档
├── changelog/    # 变更日志
└── assets/       # 资源文件
```

---

*由三省六部协同开发系统 v{__version__} 自动生成*
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""


# ============================================================
# ArgumentParser 构建
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    """构建完整的命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="🏛️  三省六部协同开发系统 - 统一脚本调度入口 v" + __version__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --help              显示此帮助信息
  python main.py health-check        运行环境健康检查
  python main.py init                初始化项目结构
  python main.py version             显示版本信息
  python main.py zs requirements     中书省-需求分析
  python main.py ms code-review      门下省-代码审查
  python main.py ss libu agent-dispatch 尚书省-吏部-Agent分派
  python main.py run                 运行完整工作流
  python main.py fusion              启动SDD+TDD融合引擎
""",
    )

    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s v{__version__}"
    )

    global_opts = parser.add_argument_group("全局选项")
    global_opts.add_argument(
        "--project-dir", "-p",
        type=str,
        default=".",
        help="项目根目录（默认: 当前目录）"
    )
    global_opts.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="配置文件路径"
    )
    global_opts.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="详细输出（DEBUG级别日志）"
    )
    global_opts.add_argument(
        "--quiet", "-q",
        action="store_true",
        default=False,
        help="静默模式（仅显示WARNING及以上日志）"
    )
    global_opts.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="日志文件路径"
    )
    global_opts.add_argument(
        "--output-dir", "-o",
        type=str,
        default="./docs/universal-skill",
        help="输出目录（默认: ./docs/universal-skill）"
    )

    subparsers = parser.add_subparsers(dest="command", title="可用命令", metavar="<command>")

    _add_zhongshusheng_parser(subparsers)
    _add_menxiasheng_parser(subparsers)
    _add_shangshusheng_parser(subparsers)
    _add_init_parser(subparsers)
    _add_health_check_parser(subparsers)
    _add_run_parser(subparsers)
    _add_version_parser(subparsers)
    _add_fusion_parser(subparsers)
    _add_evolve_parser(subparsers)
    _add_coordinate_parser(subparsers)
    _add_generate_docs_parser(subparsers)

    return parser


def _add_zhongshusheng_parser(subparsers: argparse._SubParsersAction) -> None:
    """添加中书省命令组"""
    desc = "📋 中书省 - 决策制定中心（需求分析/架构设计/规范制定/方案审议）"
    p = subparsers.add_parser("zhongshusheng", aliases=["zs"], help=desc, description=desc)
    subs = p.add_subparsers(dest="subcommand", title="中书省子命令", metavar="<subcommand>")
    main_cmds = {k: v for k, v in ZHONGSHUSHENG_CMDS.items() if v not in ZHONGSHUSHENG_CMDS}
    for cmd, help_text in main_cmds.items():
        aliases = [k for k, v in ZHONGSHUSHENG_CMDS.items() if v == cmd and k != cmd]
        sp = subs.add_parser(cmd, aliases=aliases, help=help_text)
        sp.add_argument("--input", "-i", type=str, help="输入文件路径")
        sp.add_argument("--output", "-o", type=str, help="输出路径")


def _add_menxiasheng_parser(subparsers: argparse._SubParsersAction) -> None:
    """添加门下省命令组"""
    desc = "✍️ 门下省 - 审议监督中心（代码审查/测试验证/质量监控/合规审计）"
    p = subparsers.add_parser("menxiasheng", aliases=["ms"], help=desc, description=desc)
    subs = p.add_subparsers(dest="subcommand", title="门下省子命令", metavar="<subcommand>")
    main_cmds = {k: v for k, v in MENXIASHENG_CMDS.items() if v not in MENXIASHENG_CMDS}
    for cmd, help_text in main_cmds.items():
        aliases = [k for k, v in MENXIASHENG_CMDS.items() if v == cmd and k != cmd]
        sp = subs.add_parser(cmd, aliases=aliases, help=help_text)
        sp.add_argument("--target", "-t", type=str, help="目标路径")
        sp.add_argument("--strict", action="store_true", help="严格模式")


def _add_shangshusheng_parser(subparsers: argparse._SubParsersAction) -> None:
    """添加尚书省命令组（含六部，两级子命令：部门→司）"""
    desc = "⚙️  尚书省 - 执行统筹中心（吏户礼兵工刑六部）"
    p = subparsers.add_parser("shangshusheng", aliases=["ss"], help=desc, description=desc)
    dept_subs = p.add_subparsers(dest="department", title="六部", metavar="<department>")

    for dept_key, dept_info in SHANGSHUSHENG_DEPTS.items():
        dept_parser = dept_subs.add_parser(dept_key, help=dept_info["description"])
        cmd_subs = dept_parser.add_subparsers(
            dest="dept_subcmd",
            title=f"{dept_info['description'].split(' - ')[0]} 子命令",
            metavar="<subcmd>"
        )
        for subcmd_name, subcmd_help in dept_info["subcmds"].items():
            sp = cmd_subs.add_parser(subcmd_name, help=subcmd_help)
            sp.add_argument("--source", "-s", type=str, help="源文件/目录")


def _add_init_parser(subparsers: argparse._SubParsersAction) -> None:
    """添加初始化命令"""
    p = subparsers.add_parser("init", help="🚀 初始化项目目录结构和配置文件")
    p.add_argument("--force", action="store_true", help="强制重新初始化（覆盖现有文件）")


def _add_health_check_parser(subparsers: argparse._SubParsersAction) -> None:
    """添加健康检查命令"""
    p = subparsers.add_parser(
        "health-check",
        aliases=["status"],
        help="🏥 运行环境健康检查"
    )
    p.add_argument("--json", action="store_true", help="以JSON格式输出结果")


def _add_run_parser(subparsers: argparse._SubParsersAction) -> None:
    """添加运行完整工作流命令"""
    subparsers.add_parser("run", help="🔄 运行完整的三省六部工作流")


def _add_version_parser(subparsers: argparse._SubParsersAction) -> None:
    """添加版本信息命令"""
    subparsers.add_parser("version", aliases=["--version"], help="📌 显示版本信息")


def _add_fusion_parser(subparsers: argparse._SubParsersAction) -> None:
    """添加SDD+TDD融合引擎命令"""
    p = subparsers.add_parser("fusion", help="🔗 启动SDD+TDD深度融合引擎")
    p.add_argument("--spec", "-s", type=str, help="SDD规范文件路径")
    p.add_argument("--tdd-mode", choices=["strict", "normal", "relaxed"], default="normal", help="TDD模式")


def _add_evolve_parser(subparsers: argparse._SubParsersAction) -> None:
    """添加自演化系统命令"""
    p = subparsers.add_parser("evolve", help="🧬 启动自演化系统")
    p.add_argument("--mode", choices=["auto", "manual", "monitor"], default="auto", help="演化模式")


def _add_coordinate_parser(subparsers: argparse._SubParsersAction) -> None:
    """添加三省协调命令"""
    p = subparsers.add_parser("coordinate", aliases=["coord"], help="🏛️ 启动三省协调机制")
    p.add_argument("--task", "-t", type=str, help="任务描述")


def _add_generate_docs_parser(subparsers: argparse._SubParsersAction) -> None:
    """添加批量文档生成命令"""
    p = subparsers.add_parser(
        "generate-docs",
        aliases=["gendoc"],
        help="📝 批量生成项目文档"
    )
    p.add_argument("--format", "-f", choices=["markdown", "html", "json"], default="markdown", help="输出格式")
    p.add_argument("--all", action="store_true", help="生成全部类型文档")


# ============================================================
# 主入口
# ============================================================

def main(argv: Optional[List[str]] = None) -> int:
    """主入口函数"""
    parser = build_parser()
    args = parser.parse_args(argv)

    project_dir = Path(args.project_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    config_path = Path(args.config) if args.config else None

    logger = setup_logger(
        verbose=args.verbose,
        quiet=args.quiet,
        log_file=args.log_file,
    )

    logger.info(f"三省六部系统启动 v{__version__}")
    logger.info(f"项目目录: {project_dir}")
    logger.info(f"输出目录: {output_dir}")

    if not args.command:
        parser.print_help()
        return 0

    router = ProvinceRouter(
        project_dir=project_dir,
        output_dir=output_dir,
        logger=logger,
        config_path=config_path,
    )
    return router.route(args)


if __name__ == "__main__":
    sys.exit(main())
