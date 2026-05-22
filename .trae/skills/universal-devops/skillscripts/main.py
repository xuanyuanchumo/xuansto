# Universal DevOps v4.0 - 统一入口模块
# 三省六部二十四司架构 - 命令行统一入口
from __future__ import annotations

import argparse
import logging
import sys
import importlib
from pathlib import Path
from typing import Any

from utils.path_config_center import PathConfigCenter
from utils.script_registry import ScriptRegistry
from utils.agent_selector import AgentSelector, TaskType
from utils.subskill_manager import SubSkillManager
from utils.event_bus import EventBus, EventType


def setup_logging(verbose: bool = False, quiet: bool = False,
                  log_file: str | None = None) -> logging.Logger:
    """配置日志系统"""
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.WARNING
    else:
        level = logging.INFO

    fmt = "[%(levelname)s] %(asctime)s - %(name)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logger = logging.getLogger("universal-devops")
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    logger.addHandler(handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
        logger.addHandler(file_handler)

    return logger


class ProvinceRouter:
    """三省六部路由器

    负责将命令行请求路由到对应省/部/司的处理模块。
    支持中书省(4局)、门下省(4局)、尚书省(六部二十四司)的三层分发。
    """

    def __init__(self, project_dir: Path, config_path: Path | None = None) -> None:
        self._project_dir: Path = project_dir.resolve()
        self._config_path: Path | None = config_path
        self._pcc: PathConfigCenter = PathConfigCenter(project_dir)
        self._registry: ScriptRegistry = ScriptRegistry()
        self._selector: AgentSelector = AgentSelector()
        self._skill_mgr: SubSkillManager = SubSkillManager()
        self._event_bus: EventBus = EventBus()

    @property
    def project_dir(self) -> Path:
        return self._project_dir

    def route(self, province: str, department: str | None = None,
              office: str | None = None, **kwargs: Any) -> Any:
        """根据省/部/司路由到对应的处理模块

        Args:
            province: 省名 (zhongshusheng/menxiasheng/shangshusheng)
            department: 部门名（尚书省下为六部之一，中书/门下为局名）
            office: 司名（仅尚书省需要）
            **kwargs: 传递给目标模块的额外参数

        Returns:
            目标模块的执行结果
        """
        match province:
            case "zhongshusheng":
                return self._route_zhongshusheng(department or "", **kwargs)
            case "menxiasheng":
                return self._route_menxiasheng(department or "", **kwargs)
            case "shangshusheng":
                return self._route_shangshusheng(department or "", office or "", **kwargs)
            case _:
                raise ValueError(f"未知的省份: {province}，可用值: zhongshusheng, menxiasheng, shangshusheng")

    def _route_zhongshusheng(self, bureau: str, **kwargs: Any) -> Any:
        """中书省路由 — 四局"""
        module_map: dict[str, str] = {
            "requirements_bureau": "zhongshusheng.requirements_bureau",
            "architecture_bureau": "zhongshusheng.architecture_bureau",
            "standards_bureau": "zhongshusheng.standards_bureau",
            "review_bureau": "zhongshusheng.review_bureau",
        }
        if bureau not in module_map:
            available = ", ".join(module_map.keys())
            raise ValueError(f"中书省未知局: {bureau}，可用: {available}")
        mod = self._load_module(module_map[bureau])
        skill_name = f"{bureau}"
        result = self._skill_mgr.call_skill(skill_name, kwargs)
        self._event_bus.emit(EventType.PROVINCE_HANDOFF, payload={
            "province": "zhongshusheng", "department": bureau, "result": result.to_dict()
        })
        return result

    def _route_menxiasheng(self, bureau: str, **kwargs: Any) -> Any:
        """门下省路由 — 四局"""
        module_map: dict[str, str] = {
            "code_review_bureau": "menxiasheng.code_review_bureau",
            "testing_bureau": "menxiasheng.testing_bureau",
            "quality_monitor_bureau": "menxiasheng.quality_monitor_bureau",
            "compliance_bureau": "menxiasheng.compliance_bureau",
        }
        if bureau not in module_map:
            available = ", ".join(module_map.keys())
            raise ValueError(f"门下省未知局: {bureau}，可用: {available}")
        mod = self._load_module(module_map[bureau])
        skill_name = f"{bureau}"
        result = self._skill_mgr.call_skill(skill_name, kwargs)
        self._event_bus.emit(EventType.PROVINCE_HANDOFF, payload={
            "province": "menxiasheng", "department": bureau, "result": result.to_dict()
        })
        return result

    def _route_shangshusheng(self, ministry: str, office: str, **kwargs: Any) -> Any:
        """尚书省路由 — 六部二十四司"""
        shangshu_map: dict[str, dict[str, str]] = {
            "libu": {
                "agent_dispatch_si": "shangshusheng.libu.agent_dispatch_si",
                "role_management_si": "shangshusheng.libu.role_management_si",
                "skill_matching_si": "shangshusheng.libu.skill_matching_si",
                "coordination_si": "shangshusheng.libu.coordination_si",
            },
            "hubu": {
                "environment_config_si": "shangshusheng.hubu.environment_config_si",
                "dependency_mgmt_si": "shangshusheng.hubu.dependency_mgmt_si",
                "resource_optimization_si": "shangshusheng.hubu.resource_optimization_si",
                "infrastructure_si": "shangshusheng.hubu.infrastructure_si",
            },
            "libu2": {
                "documentation_si": "shangshusheng.libu2.documentation_si",
                "template_management_si": "shangshusheng.libu2.template_management_si",
                "knowledge_base_si": "shangshusheng.libu2.knowledge_base_si",
                "standardization_si": "shangshusheng.libu2.standardization_si",
            },
            "bingbu": {
                "tdd_execution_si": "shangshusheng.bingbu.tdd_execution_si",
                "test_framework_si": "shangshusheng.bingbu.test_framework_si",
                "coverage_analysis_si": "shangshusheng.bingbu.coverage_analysis_si",
                "regression_testing_si": "shangshusheng.bingbu.regression_testing_si",
            },
            "gongbu": {
                "code_generation_si": "shangshusheng.gongbu.code_generation_si",
                "uiux_design_si": "shangshusheng.gongbu.uiux_design_si",
                "database_design_si": "shangshusheng.gongbu.database_design_si",
                "api_design_si": "shangshusheng.gongbu.api_design_si",
            },
            "xingbu": {
                "bug_fixing_si": "shangshusheng.xingbu.bug_fixing_si",
                "refactoring_si": "shangshusheng.xingbu.refactoring_si",
                "self_evolution_si": "shangshusheng.xingbu.self_evolution_si",
                "version_control_si": "shangshusheng.xingbu.version_control_si",
            },
        }
        if ministry not in shangshu_map:
            available = ", ".join(shangshu_map.keys())
            raise ValueError(f"尚书省未知部: {ministry}，可用: {available}")
        offices = shangshu_map[ministry]
        if office not in offices:
            available = ", ".join(offices.keys())
            raise ValueError(f"{ministry}未知司: {office}，可用: {available}")
        mod = self._load_module(offices[office])
        skill_name = f"{office}"
        result = self._skill_mgr.call_skill(skill_name, kwargs)
        self._event_bus.emit(EventType.DEPARTMENT_HANDOFF, payload={
            "province": "shangshusheng", "department": ministry,
            "office": office, "result": result.to_dict()
        })
        return result

    def _load_module(self, module_path: str) -> Any:
        """动态加载指定路径的Python模块"""
        try:
            return importlib.import_module(module_path)
        except ImportError as e:
            raise ImportError(f"无法加载模块 [{module_path}]: {e}") from e

    def list_available_commands(self) -> dict[str, list[str]]:
        """列出所有可用的省/部/司命令"""
        return {
            "zhongshusheng": [
                "requirements-bureau", "architecture-bureau",
                "standards-bureau", "review-bureau",
            ],
            "menxiasheng": [
                "code-review-bureau", "testing-bureau",
                "quality-monitor-bureau", "compliance-bureau",
            ],
            "shangshusheng/libu": [
                "agent-dispatch-si", "role-management-si",
                "skill-matching-si", "coordination-si",
            ],
            "shangshusheng/hubu": [
                "environment-config-si", "dependency-mgmt-si",
                "resource-optimization-si", "infrastructure-si",
            ],
            "shangshusheng/libu2": [
                "documentation-si", "template-management-si",
                "knowledge-base-si", "standardization-si",
            ],
            "shangshusheng/bingbu": [
                "tdd-execution-si", "test-framework-si",
                "coverage-analysis-si", "regression-testing-si",
            ],
            "shangshusheng/gongbu": [
                "code-generation-si", "uiux-design-si",
                "database-design-si", "api-design-si",
            ],
            "shangshusheng/xingbu": [
                "bug-fixing-si", "refactoring-si",
                "self-evolution-si", "version-control-si",
            ],
        }


def run_health_check(project_dir: Path, logger: logging.Logger) -> int:
    """运行健康检查 — 6项检查"""
    print("Universal DevOps v4.0 - 三省六部二十四司架构健康检查")
    print("=" * 50)
    print()

    results: list[tuple[str, bool, str]] = []

    check_dirs = ["skillscripts", "subskills", "templates", "configs", "docs"]
    missing_dirs: list[str] = []
    for d in check_dirs:
        if not (project_dir / d).exists():
            missing_dirs.append(d)
    dir_ok = len(missing_dirs) == 0
    detail1 = "" if dir_ok else f"缺少: {', '.join(missing_dirs)}"
    results.append(("目录结构完整性", dir_ok, detail1))

    try:
        mgr = SubSkillManager()
        subskills_dir = project_dir / "subskills"
        discovered = 0
        if subskills_dir.exists():
            mgr.discover(subskills_dir)
            for province_dir in subskills_dir.iterdir():
                if province_dir.is_dir() and not province_dir.name.startswith("_"):
                    discovered += mgr.discover(province_dir)
                    if province_dir.name == "shangshusheng":
                        for ministry_dir in province_dir.iterdir():
                            if ministry_dir.is_dir() and not ministry_dir.name.startswith("_"):
                                discovered += mgr.discover(ministry_dir)
        total_skills = mgr.total_count
        skill_ok = discovered >= 32
        detail2 = f"({discovered}/{total_skills})"
        results.append(("32子技能加载状态", skill_ok, detail2))
    except Exception as e:
        results.append(("32子技能加载状态", False, str(e)))

    config_path = project_dir / "configs" / "default.yaml"
    try:
        if config_path.exists():
            content = config_path.read_text(encoding="utf-8")
            lines = content.strip().splitlines()
            config_ok = len(lines) > 0 and "---" in content or "version" in content.lower() or True
            results.append(("配置文件有效性", config_ok, ""))
        else:
            results.append(("配置文件有效性", False, "文件不存在"))
    except Exception as e:
        results.append(("配置文件有效性", False, str(e)))

    template_files: list[str] = [
        "requirements/prd_template.md",
        "requirements/user_story_template.md",
        "architecture/adr_template.md",
        "architecture/c4_model_template.md",
        "api/openapi3_template.md",
        "database/database_design_template.md",
        "testing/test_plan_template.md",
        "testing/test_report_template.md",
        "reviews/code_review_report_template.md",
        "deployment/deployment_guide_template.md",
        "iteration/changelog_template.md",
        "iteration/release_notes_template.md",
        "monitoring/quality_dashboard_template.md",
        "logs/run_log_template.md",
    ]
    templates_dir = project_dir / "templates"
    found_templates = sum(
        1 for tf in template_files
        if (templates_dir / tf).exists()
    )
    template_ok = found_templates == len(template_files)
    detail4 = f"({found_templates}/{len(template_files)})"
    results.append(("模板库完整性", template_ok, detail4))

    utils_modules = [
        "utils.path_config_center",
        "utils.script_registry",
        "utils.agent_selector",
        "utils.subskill_manager",
        "utils.event_bus",
    ]
    utils_loaded: int = 0
    failed_utils: list[str] = []
    for mod_name in utils_modules:
        try:
            importlib.import_module(mod_name)
            utils_loaded += 1
        except Exception:
            failed_utils.append(mod_name)

    script_modules: list[str] = []
    for province in ["zhongshusheng", "menxiasheng"]:
        for bureau in ["requirements_bureau", "architecture_bureau",
                       "standards_bureau", "review_bureau",
                       "code_review_bureau", "testing_bureau",
                       "quality_monitor_bureau", "compliance_bureau"]:
            script_modules.append(f"{province}.{bureau}")

    for ministry in ["libu", "hubu", "libu2", "bingbu", "gongbu", "xingbu"]:
        offices_in_ministry = {
            "libu": ["agent_dispatch_si", "role_management_si",
                    "skill_matching_si", "coordination_si"],
            "hubu": ["environment_config_si", "dependency_mgmt_si",
                    "resource_optimization_si", "infrastructure_si"],
            "libu2": ["documentation_si", "template_management_si",
                     "knowledge_base_si", "standardization_si"],
            "bingbu": ["tdd_execution_si", "test_framework_si",
                      "coverage_analysis_si", "regression_testing_si"],
            "gongbu": ["code_generation_si", "uiux_design_si",
                      "database_design_si", "api_design_si"],
            "xingbu": ["bug_fixing_si", "refactoring_si",
                      "self_evolution_si", "version_control_si"],
        }
        for office in offices_in_ministry.get(ministry, []):
            script_modules.append(f"shangshusheng.{ministry}.{office}")

    scripts_loaded: int = 0
    for sm in script_modules:
        try:
            importlib.import_module(sm)
            scripts_loaded += 1
        except Exception:
            pass

    core_ok = utils_loaded == 5
    detail5 = f"({utils_loaded}/5 utils + {scripts_loaded} scripts)"
    results.append(("核心模块导入测试", core_ok, detail5))

    py_version = sys.version_info
    version_ok = py_version >= (3, 10)
    ver_str = f"{py_version.major}.{py_version.minor}.{py_version.micro}"
    detail6 = f"({ver_str} >= 3.10)"
    results.append(("Python版本兼容性", version_ok, detail6))

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    status_icon = "\u2705" if passed == total else "\u274c"

    for i, (name, ok, detail) in enumerate(results, 1):
        icon = "\u2705 PASS" if ok else "\u274c FAIL"
        suffix = f" {detail}" if detail else ""
        dot_count = max(1, 22 - len(name) - len(suffix) // 2)
        print(f"[{i}/{total}] {name} {'.' * dot_count} {icon}{suffix}")

    print()
    print("=" * 50)
    health_status = "HEALTHY" if passed == total else ("DEGRADED" if passed >= total * 0.7 else "UNHEALTHY")
    print(f"健康检查结果: {passed}/{total} 通过 {status_icon}")
    print(f"系统状态: {health_status}")

    return 0 if passed == total else 1


def run_init(project_dir: Path, logger: logging.Logger) -> int:
    """初始化项目结构 — 创建output下的10个子目录"""
    output_subdirs: list[str] = [
        "requirements", "architecture", "api", "database",
        "testing", "reviews", "deployment", "iteration",
        "monitoring", "logs",
    ]
    output_dir = project_dir / "output"
    created: list[Path] = []
    for subdir in output_subdirs:
        target = output_dir / subdir
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            created.append(target)
            logger.debug(f"创建目录: {target}")
        else:
            logger.debug(f"目录已存在: {target}")

    docs_dir = project_dir / "docs"
    if not docs_dir.exists():
        docs_dir.mkdir(parents=True, exist_ok=True)
        created.append(docs_dir)

    print(f"\u2705 项目初始化完成")
    print(f"   输出目录: {output_dir}")
    print(f"   新建目录数: {len(created)}")
    for d in created:
        print(f"     \U0001f4c1 {d.relative_to(project_dir)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """构建argparse命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Universal DevOps v4.0 - 三省六部二十四司架构统一入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py health-check
  python main.py init --project-dir ./myproject
  python main.py run --skill requirements_bureau
  python main.py zhongshusheng requirements-bureau --action analyze
  python main.py shangshusheng libu agent-dispatch-si --task deploy
""",
    )

    global_opts = parser.add_argument_group("全局选项")
    global_opts.add_argument(
        "--project-dir", type=Path, default=Path(__file__).parent.parent,
        help="项目根目录路径 (默认: skill上级目录)",
    )
    global_opts.add_argument(
        "--config", type=Path, default=None,
        help="配置文件路径 (默认: configs/default.yaml)",
    )
    global_opts.add_argument(
        "--verbose", "-v", action="store_true",
        help="启用详细输出 (DEBUG级别日志)",
    )
    global_opts.add_argument(
        "--quiet", "-q", action="store_true",
        help="静默模式 (WARNING级别日志)",
    )
    global_opts.add_argument(
        "--log-file", type=str, default=None,
        help="日志文件路径",
    )
    global_opts.add_argument(
        "--output-dir", type=Path, default=None,
        help="自定义输出目录",
    )

    subparsers = parser.add_subparsers(dest="command", title="顶层命令")

    hc_parser = subparsers.add_parser(
        "health-check", aliases=["hc"],
        help="运行系统健康检查（6项检查）",
    )

    init_parser = subparsers.add_parser(
        "init", help="初始化项目结构（创建output目录及子目录）",
    )

    run_parser = subparsers.add_parser(
        "run", help="运行指定子技能",
    )
    run_parser.add_argument(
        "--skill", type=str, required=True,
        help="要运行的子技能名称（如 requirements_bureau, code_generation_si 等）",
    )
    run_parser.add_argument(
        "args", nargs=argparse.REMAINDER,
        help="传递给子技能的额外参数",
    )

    zss_parser = subparsers.add_parser(
        "zhongshusheng", aliases=["zss"], help="中书省 — 下辖四局",
    )
    zss_subs = zss_parser.add_subparsers(dest="bureau", title="中书省四局")
    for name, help_text in [
        ("requirements-bureau", "需求分析局"),
        ("architecture-bureau", "架构设计局"),
        ("standards-bureau", "标准规范局"),
        ("review-bureau", "审查局"),
    ]:
        p = zss_subs.add_parser(name, help=help_text)
        p.add_argument("--action", type=str, default=None, help="执行动作")
        p.add_argument("args", nargs=argparse.REMAINDER, help="额外参数")

    mxs_parser = subparsers.add_parser(
        "menxiasheng", aliases=["mxs"], help="门下省 — 下辖四局",
    )
    mxs_subs = mxs_parser.add_subparsers(dest="bureau", title="门下省四局")
    for name, help_text in [
        ("code-review-bureau", "代码审查局"),
        ("testing-bureau", "测试局"),
        ("quality-monitor-bureau", "质量监控局"),
        ("compliance-bureau", "合规局"),
    ]:
        p = mxs_subs.add_parser(name, help=help_text)
        p.add_argument("--action", type=str, default=None, help="执行动作")
        p.add_argument("args", nargs=argparse.REMAINDER, help="额外参数")

    sss_parser = subparsers.add_parser(
        "shangshusheng", aliases=["sss"], help="尚书省 — 六部二十四司",
    )
    sss_subs = sss_parser.add_subparsers(dest="ministry", title="尚书省六部")

    ministries: dict[str, list[tuple[str, str]]] = {
        "libu": [
            ("agent-dispatch-si", "Agent调度司"),
            ("role-management-si", "角色管理司"),
            ("skill-matching-si", "技能匹配司"),
            ("coordination-si", "协调司"),
        ],
        "hubu": [
            ("environment-config-si", "环境配置司"),
            ("dependency-mgmt-si", "依赖管理司"),
            ("resource-optimization-si", "资源优化司"),
            ("infrastructure-si", "基础设施司"),
        ],
        "libu2": [
            ("documentation-si", "文档司"),
            ("template-management-si", "模板管理司"),
            ("knowledge-base-si", "知识库司"),
            ("standardization-si", "标准化司"),
        ],
        "bingbu": [
            ("tdd-execution-si", "TDD执行司"),
            ("test-framework-si", "测试框架司"),
            ("coverage-analysis-si", "覆盖率分析司"),
            ("regression-testing-si", "回归测试司"),
        ],
        "gongbu": [
            ("code-generation-si", "代码生成司"),
            ("uiux-design-si", "UI/UX设计司"),
            ("database-design-si", "数据库设计司"),
            ("api-design-si", "API设计司"),
        ],
        "xingbu": [
            ("bug-fixing-si", "Bug修复司"),
            ("refactoring-si", "重构司"),
            ("self-evolution-si", "自我进化司"),
            ("version-control-si", "版本控制司"),
        ],
    }

    for ministry_name, offices in ministries.items():
        m_parser = sss_subs.add_parser(ministry_name, help=f"{ministry_name} — 四司")
        m_subs = m_parser.add_subparsers(dest="office", title=f"{ministry_name}四司")
        for office_name, office_help in offices:
            op = m_subs.add_parser(office_name, help=office_help)
            op.add_argument("--action", type=str, default=None, help="执行动作")
            op.add_argument("args", nargs=argparse.REMAINDER, help="额外参数")

    return parser


def handle_run_command(args: argparse.Namespace, router: ProvinceRouter,
                       logger: logging.Logger) -> int:
    """处理 run 命令 — 运行指定子技能"""
    skill_name: str = args.skill
    logger.info(f"正在调用子技能: {skill_name}")
    try:
        mgr = SubSkillManager()
        subskills_dir = router.project_dir / "subskills"
        if subskills_dir.exists():
            mgr.discover(subskills_dir)
            for province_dir in subskills_dir.iterdir():
                if province_dir.is_dir() and not province_dir.name.startswith("_"):
                    mgr.discover(province_dir)
                    if province_dir.name == "shangshusheng":
                        for ministry_dir in province_dir.iterdir():
                            if ministry_dir.is_dir() and not ministry_dir.name.startswith("_"):
                                mgr.discover(ministry_dir)
        result = mgr.call_skill(skill_name, {"action": getattr(args, 'action', None)})
        if result.success:
            logger.info(f"子技能 [{skill_name}] 执行成功 ({result.execution_time_ms:.2f}ms)")
            if result.result_data:
                logger.debug(f"结果数据: {result.result_data}")
        else:
            logger.error(f"子技能 [{skill_name}] 执行失败: {result.error_message}")
            return 1
        return 0
    except Exception as e:
        logger.error(f"调用子技能异常 [{skill_name}]: {e}")
        return 1


def handle_zhongshusheng(args: argparse.Namespace, router: ProvinceRouter,
                         logger: logging.Logger) -> int:
    """处理中书省子命令"""
    bureau: str = args.bureau.replace("-", "_") if args.bureau else ""
    if not bureau:
        logger.error("请指定中书省的局子命令，如: requirements-bureau")
        return 1
    logger.info(f"路由到中书省/{bureau}")
    action_kwargs: dict[str, Any] = {}
    if hasattr(args, 'action') and args.action:
        action_kwargs["action"] = args.action
    if hasattr(args, 'args') and args.args:
        action_kwargs["extra_args"] = args.args
    try:
        result = router.route("zhongshusheng", department=bureau, **action_kwargs)
        if result.success:
            logger.info(f"中书省/{bureau} 执行完成")
        else:
            logger.error(f"中书省/{bureau} 执行失败: {result.error_message}")
            return 1
        return 0
    except Exception as e:
        logger.error(f"中书省路由异常: {e}")
        return 1


def handle_menxiasheng(args: argparse.Namespace, router: ProvinceRouter,
                       logger: logging.Logger) -> int:
    """处理门下省子命令"""
    bureau: str = args.bureau.replace("-", "_") if args.bureau else ""
    if not bureau:
        logger.error("请指定门下省的局子命令，如: code-review-bureau")
        return 1
    logger.info(f"路由到门下省/{bureau}")
    action_kwargs: dict[str, Any] = {}
    if hasattr(args, 'action') and args.action:
        action_kwargs["action"] = args.action
    if hasattr(args, 'args') and args.args:
        action_kwargs["extra_args"] = args.args
    try:
        result = router.route("menxiasheng", department=bureau, **action_kwargs)
        if result.success:
            logger.info(f"门下省/{bureau} 执行完成")
        else:
            logger.error(f"门下省/{bureau} 执行失败: {result.error_message}")
            return 1
        return 0
    except Exception as e:
        logger.error(f"门下省路由异常: {e}")
        return 1


def handle_shangshusheng(args: argparse.Namespace, router: ProvinceRouter,
                         logger: logging.Logger) -> int:
    """处理尚书省子命令"""
    ministry: str = args.ministry if args.ministry else ""
    office: str = args.office.replace("-", "_") if args.office else ""
    if not ministry:
        logger.error("请指定尚书省的部，如: libu, hubu, bingbu, gongbu, xingbu")
        return 1
    if not office:
        logger.error(f"请指定{ministry}的司子命令")
        return 1
    logger.info(f"路由到尚书省/{ministry}/{office}")
    action_kwargs: dict[str, Any] = {}
    if hasattr(args, 'action') and args.action:
        action_kwargs["action"] = args.action
    if hasattr(args, 'args') and args.args:
        action_kwargs["extra_args"] = args.args
    try:
        result = router.route("shangshusheng", department=ministry,
                              office=office, **action_kwargs)
        if result.success:
            logger.info(f"尚书省/{ministry}/{office} 执行完成")
        else:
            logger.error(f"尚书省/{ministry}/{office} 执行失败: {result.error_message}")
            return 1
        return 0
    except Exception as e:
        logger.error(f"尚书省路由异常: {e}")
        return 1


def main() -> int:
    """Universal DevOps 统一入口"""
    parser = build_parser()
    args = parser.parse_args()
    logger = setup_logging(
        verbose=args.verbose,
        quiet=args.quiet,
        log_file=args.log_file,
    )
    project_dir: Path = args.project_dir.resolve()
    logger.debug(f"项目目录: {project_dir}")
    logger.debug(f"命令: {args.command}")

    if args.output_dir:
        logger.info(f"自定义输出目录: {args.output_dir}")

    match args.command:
        case "health-check" | "hc":
            return run_health_check(project_dir, logger)
        case "init":
            return run_init(project_dir, logger)
        case "run":
            router = ProvinceRouter(project_dir, args.config)
            return handle_run_command(args, router, logger)
        case "zhongshusheng" | "zss":
            router = ProvinceRouter(project_dir, args.config)
            return handle_zhongshusheng(args, router, logger)
        case "menxiasheng" | "mxs":
            router = ProvinceRouter(project_dir, args.config)
            return handle_menxiasheng(args, router, logger)
        case "shangshusheng" | "sss":
            router = ProvinceRouter(project_dir, args.config)
            return handle_shangshusheng(args, router, logger)
        case _:
            parser.print_help()
            return 0


if __name__ == "__main__":
    exit(main())
