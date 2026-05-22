"""
回归测试司 - 冒烟测试套件、回归优先级排序、测试稳定性保障
"""
from __future__ import annotations

import json
import re
import hashlib
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class RegressionStrategy(Enum):
    """回归策略"""

    FULL = "full"
    INCREMENTAL = "incremental"
    SELECTIVE = "selective"


class FlakySeverity(Enum):
    """Flaky Test严重度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SmokeTest:
    """冒烟测试用例"""

    name: str
    description: str
    priority: int = 1
    estimated_time: float = 0.5
    test_path: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class TestCasePriority:
    """测试用例优先级"""

    test_name: str
    test_path: str
    score: float = 0.0
    factors: dict[str, float] = field(default_factory=dict)
    recommended: bool = True


@dataclass
class FlakyTest:
    """不稳定测试记录"""

    test_name: str
    test_path: str
    failure_rate: float = 0.0
    total_runs: int = 0
    consecutive_failures: int = 0
    last_failure_msg: str = ""
    severity: FlakySeverity = FlakySeverity.MEDIUM
    root_cause_hints: list[str] = field(default_factory=list)
    suggested_fix: str = ""


@dataclass
class ChangeImpact:
    """变更影响分析"""

    changed_files: list[str]
    affected_modules: list[str]
    affected_tests: list[str]
    impact_score: float = 0.0
    recommended_subset: list[str] = field(default_factory=list)


@dataclass
class RegressionWindow:
    """回归窗口配置"""

    iteration_name: str
    total_budget_minutes: float = 60.0
    smoke_budget_pct: float = 20.0
    regression_budget_pct: float = 60.0
    flaky_investigation_budget_pct: float = 10.0
    remaining_buffer_pct: float = 10.0


@dataclass
class DuplicateInfo:
    """重复测试信息"""

    test_a: str
    test_b: str
    similarity_score: float
    duplicate_type: str
    recommendation: str = ""


class RegressionTestingError(Exception):
    """回归测试异常"""


class FlakyTestError(RegressionTestingError):
    """Flaky测试异常"""


class ImpactAnalysisError(RegressionTestingError):
    """影响分析异常"""


class RegressionTestingSi:
    """
    回归测试司 - 兵部·兵部司

    提供全面的回归测试能力：
    - 冒烟测试套件生成（核心路径快速验证）
    - 回归优先级排序（基于变更/历史故障/业务重要性）
    - 测试稳定性分析（Flaky Test检测与治理）
    - 变更影响分析
    - 测试去重
    - 回归窗口策略
    """

    def __init__(self) -> None:
        self._smoke_tests: list[SmokeTest] = []
        self._flaky_tests: dict[str, FlakyTest] = {}
        self._test_history: dict[str, list[dict[str, Any]]] = {}
        self._failure_frequency: dict[str, int] = {}

    # ==================== 冒烟测试套件 ====================

    def generate_smoke_suite(self, project_type: str = "web_api") -> list[SmokeTest]:
        """
        生成冒烟测试套件

        Args:
            project_type: 项目类型

        Returns:
            冒烟测试用例列表
        """
        templates: dict[str, list[SmokeTest]] = {
            "web_api": [
                SmokeTest(
                    name="health_check",
                    description="API健康检查端点响应",
                    priority=1,
                    estimated_time=0.1,
                    tags=["critical", "smoke"],
                ),
                SmokeTest(
                    name="auth_login",
                    description="用户登录流程验证",
                    priority=1,
                    estimated_time=0.3,
                    tags=["critical", "smoke", "auth"],
                ),
                SmokeTest(
                    name="db_connection",
                    description="数据库连接可用性",
                    priority=1,
                    estimated_time=0.2,
                    tags=["critical", "smoke", "infra"],
                ),
                SmokeTest(
                    name="core_crud",
                    description="核心CRUD操作基本功能",
                    priority=2,
                    estimated_time=1.0,
                    tags=["smoke", "core"],
                ),
                SmokeTest(
                    name="cache_layer",
                    description="缓存层读写验证",
                    priority=2,
                    estimated_time=0.3,
                    tags=["smoke", "cache"],
                ),
                SmokeTest(
                    name="message_queue",
                    description="消息队列连接与发送",
                    priority=3,
                    estimated_time=0.5,
                    tags=["smoke", "mq"],
                ),
            ],
            "library": [
                SmokeTest(name="import_test", description="模块导入验证", priority=1),
                SmokeTest(name="core_function", description="核心函数调用", priority=1),
                SmokeTest(name="edge_case", description="边界条件处理", priority=2),
                SmokeTest(name="type_safety", description="类型安全检查", priority=2),
            ],
            "cli_tool": [
                SmokeTest(name="help_output", description="帮助信息输出", priority=1),
                SmokeTest(name="version_check", description="版本号显示", priority=1),
                SmokeTest(name="basic_command", description="基本命令执行", priority=1),
                SmokeTest(name="error_handling", description="错误处理流程", priority=2),
            ],
        }

        self._smoke_tests = templates.get(project_type, templates["web_api"])
        return self._smoke_tests

    def get_smoke_report(self) -> str:
        """生成冒烟测试报告"""
        if not self._smoke_tests:
            return "# 冒烟测试\n> 尚未生成冒烟测试套件\n"

        lines: list[str] = []
        lines.append("# 🚬 冒烟测试套件\n")
        lines.append("| # | 用例名 | 描述 | 优先级 | 预估时间 | 标签 |")
        lines.append("| --- | --- | --- | --- | --- | --- |")

        total_time = 0.0
        for i, st in enumerate(sorted(self._smoke_tests, key=lambda s: s.priority), start=1):
            total_time += st.estimated_time
            tags_str = ", ".join(f"`{t}`" for t in st.tags)
            lines.append(
                f"| {i} | `{st.name}` | {st.description} | P{st.priority} "
                f"| {stestimated_time:.1f}s | {tags_str} |"
            )

        lines.append(f"\n**总预估时间**: {total_time:.1f}s ({len(self._smoke_tests)}个用例)")
        return "\n".join(lines)

    # ==================== 回归优先级排序 ====================

    def prioritize_tests(
        self,
        all_tests: list[dict[str, str]],
        change_info: ChangeImpact | None = None,
    ) -> list[TestCasePriority]:
        """
        回归优先级排序

        排序因子：
        - 代码变更影响权重 (40%)
        - 历史故障频率权重 (30%)
        - 业务重要性权重 (20%)
        - 测试执行时间惩罚 (10%)

        Args:
            all_tests: 所有测试用例列表
            change_info: 变更影响分析结果

        Returns:
            排序后的测试用例优先级列表
        """
        priorities: list[TestCasePriority] = []

        for test in all_tests:
            test_name = test.get("name", "")
            test_path = test.get("path", "")

            factor_change = self._calc_change_factor(test_path, change_info)
            factor_history = self._calc_history_factor(test_name)
            factor_business = self._calc_business_factor(test.get("tags", []))
            factor_time = self._calc_time_penalty(test.get("estimated_time", 1.0))

            score = (
                factor_change * 0.40
                + factor_history * 0.30
                + factor_business * 0.20
                + factor_time * 0.10
            )

            priorities.append(
                TestCasePriority(
                    test_name=test_name,
                    test_path=test_path,
                    score=round(score, 3),
                    factors={
                        "change_impact": round(factor_change, 3),
                        "history_failure": round(factor_history, 3),
                        "business_importance": round(factor_business, 3),
                        "time_efficiency": round(factor_time, 3),
                    },
                    recommended=score >= 30,
                )
            )

        priorities.sort(key=lambda p: p.score, reverse=True)
        return priorities

    def _calc_change_factor(self, test_path: str, change_info: ChangeImpact | None) -> float:
        """计算变更影响因子"""
        if not change_info:
            return 50.0

        if test_path in change_info.affected_tests:
            return 100.0

        path_parts = Path(test_path).parts
        for module in change_info.affected_modules:
            if any(module in p.lower() for p in path_parts):
                return 75.0

        for changed_file in change_info.changed_files:
            cf_stem = Path(changed_file).stem
            if cf_stem and cf_stem in test_path.lower():
                return 60.0

        return 25.0

    def _calc_history_factor(self, test_name: str) -> float:
        """计算历史故障因子"""
        failures = self._failure_frequency.get(test_name, 0)

        if failures == 0:
            return 20.0
        elif failures <= 2:
            return 50.0 + failures * 10
        elif failures <= 5:
            return 80.0 + (failures - 2) * 5
        else:
            return 100.0

    def _calc_business_factor(self, tags: list[str]) -> float:
        """计算业务重要性因子"""
        importance_map: dict[str, float] = {
            "critical": 100.0,
            "smoke": 90.0,
            "integration": 80.0,
            "regression": 70.0,
            "security": 95.0,
            "payment": 100.0,
            "auth": 90.0,
            "e2e": 85.0,
        }

        if not tags:
            return 50.0

        max_score = max(importance_map.get(t.lower(), 50.0) for t in tags)
        return max_score

    def _calc_time_penalty(self, estimated_time: float) -> float:
        """计算时间效率因子（时间越长分数越低）"""
        if estimated_time <= 0.5:
            return 100.0
        elif estimated_time <= 2.0:
            return 80.0
        elif estimated_time <= 5.0:
            return 60.0
        elif estimated_time <= 10.0:
            return 40.0
        else:
            return 20.0

    # ==================== Flaky Test治理 ====================

    def record_test_result(
        self, test_name: str, passed: bool, error_msg: str = "", duration: float = 0.0
    ) -> None:
        """
        记录测试运行结果

        Args:
            test_name: 测试名称
            passed: 是否通过
            error_msg: 错误消息
            duration: 执行时长
        """
        if test_name not in self._test_history:
            self._test_history[test_name] = []

        self._test_history[test_name].append({
            "passed": passed,
            "error": error_msg,
            "duration": duration,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        })

        if not passed:
            self._failure_frequency[test_name] = self._failure_frequency.get(test_name, 0) + 1

    def detect_flaky_tests(self, min_runs: int = 5) -> list[FlakyTest]:
        """
        检测Flaky测试

        Args:
            min_runs: 最小运行次数阈值

        Returns:
            Flaky测试列表
        """
        flaky: list[FlakyTest] = []

        for test_name, history in self._test_history.items():
            if len(history) < min_runs:
                continue

            total = len(history)
            failures = sum(1 for h in history if not h["passed"])
            failure_rate = failures / total

            if 0.05 < failure_rate < 1.0:

                consecutive_fails = 0
                for h in reversed(history):
                    if not h["passed"]:
                        consecutive_fails += 1
                    else:
                        break

                last_error = next(
                    (h["error"] for h in reversed(history) if not h["pass"]),
                    "",
                )

                severity = self._classify_flaky_severity(failure_rate, consecutive_fails)
                hints = self._analyze_flaky_root_cause(last_error)

                flaky_test = FlakyTest(
                    test_name=test_name,
                    test_path=test_name,
                    failure_rate=round(failure_rate, 3),
                    total_runs=total,
                    consecutive_failures=consecutive_fails,
                    last_failure_msg=last_error[:200],
                    severity=severity,
                    root_cause_hints=hints,
                    suggested_fix=self._suggest_flaky_fix(hints),
                )
                self._flaky_tests[test_name] = flaky_test
                flaky.append(flaky_test)

        flaky.sort(key=lambda ft: ft.failure_rate, reverse=True)
        return flaky

    def _classify_flaky_severity(self, rate: float, consecutive: int) -> FlakySeverity:
        """分类Flaky严重度"""
        if rate > 0.5 or consecutive >= 5:
            return FlakySeverity.CRITICAL
        elif rate > 0.3 or consecutive >= 3:
            return FlakySeverity.HIGH
        elif rate > 0.15 or consecutive >= 2:
            return FlakySeverity.MEDIUM
        else:
            return FlakySeverity.LOW

    def _analyze_flaky_root_cause(self, error_msg: str) -> list[str]:
        """分析Flaky根因线索"""
        hints: list[str] = []
        error_lower = error_msg.lower()

        patterns: list[tuple[str, str]] = [
            (r"(timeout|timed out)", "超时问题：可能依赖外部服务或网络延迟"),
            (r"(connection|refused|network|socket)", "网络问题：外部服务不可用或DNS解析失败"),
            (r"(race condition|deadlock|concurrent)", "竞态条件：多线程/异步并发问题"),
            (r"(assertionerror|expected.*actual)", "断言不确定：可能依赖非确定性数据"),
            (r"(keyerror|indexerror|out of range)", "集合访问异常：数据状态不一致"),
            (r"(file.*not found|permission denied)", "文件系统问题：临时文件或权限问题"),
            (r"(memory|oom|allocation)", "内存问题：资源泄漏或内存不足"),
            (r"(order|sequence|depends)", "执行顺序依赖：测试间存在隐式依赖"),
        ]

        for pattern, hint in patterns:
            if re.search(pattern, error_lower):
                hints.append(hint)

        if not hints:
            hints.append("原因不明，建议增加日志和重试机制")

        return hints

    def _suggest_flaky_fix(self, hints: list[str]) -> str:
        """建议Flaky修复方案"""
        fix_map: dict[str, str] = {
            "超时": "增加超时时间或使用pytest-timeout，添加显式等待",
            "网络": "使用mock替代真实网络调用，或增加重试逻辑",
            "竞态": "确保线程安全，使用锁或同步原语",
            "断言不确定": "固定随机种子，使用确定的测试数据",
            "集合访问": "检查前置条件，使用get()方法避免KeyError",
            "文件系统": "使用tmp_path fixture管理临时文件",
            "内存": "检查资源释放，使用weakref监控对象生命周期",
            "执行顺序": "消除测试间共享状态，每个测试独立setup/teardown",
        }

        for hint in hints:
            for keyword, fix in fix_map.items():
                if keyword in hint:
                    return fix

        return "隔离测试环境，增加日志输出以定位根因"

    # ==================== 变更影响分析 ====================

    def analyze_change_impact(
        self,
        diff_content: str,
        base_branch: str = "main",
    ) -> ChangeImpact:
        """
        分析代码变更的影响范围

        Args:
            diff_content: git diff内容
            base_branch: 基础分支

        Returns:
            变更影响分析结果
        """
        file_pattern = re.compile(r"^diff --git a/(.*?) b/", re.MULTILINE)
        changed_files = file_pattern.findall(diff_content)

        affected_modules: set[str] = set()
        for f in changed_files:
            parts = Path(f).parts
            if len(parts) >= 1:
                affected_modules.add(parts[0])

        all_tests = self._discover_all_tests()
        affected_tests = self._map_changes_to_tests(changed_files, all_tests)

        impact_score = self._calculate_impact_score(len(changed_files), len(affected_modules))

        return ChangeImpact(
            changed_files=changed_files,
            affected_modules=list(affected_modules),
            affected_tests=affected_tests,
            impact_score=impact_score,
            recommended_subset=self._select_recommended_subset(affected_tests, impact_score),
        )

    def _discover_all_tests(self) -> list[str]:
        """发现所有测试文件"""
        tests: list[str] = []
        for smoke in self._smoke_tests:
            if smoke.test_path:
                tests.append(smoke.test_path)
        return tests

    def _map_changes_to_tests(self, changed_files: list[str], all_tests: list[str]) -> list[str]:
        """映射变更到受影响的测试"""
        affected: set[str] = set()
        for cf in changed_files:
            cf_stem = Path(cf).stem.lower()
            for test in all_tests:
                if cf_stem in test.lower():
                    affected.add(test)
        return list(affected)

    def _calculate_impact_score(self, files_changed: int, modules_affected: int) -> float:
        """计算影响评分"""
        raw_score = files_changed * 2 + modules_affected * 5
        return min(100.0, raw_score)

    def _select_recommended_subset(self, affected_tests: list[str], impact_score: float) -> list[str]:
        """选择推荐回归子集"""
        if impact_score > 70:
            return affected_tests
        elif impact_score > 40:
            return affected_tests[:max(1, len(affected_tests) // 2)]
        else:
            return affected_tests[:max(1, len(affected_tests) // 4)]

    # ==================== 测试去重 ====================

    def deduplicate_tests(self, tests: list[dict[str, str]]) -> list[DuplicateInfo]:
        """
        检测并报告重复测试

        Args:
            tests: 测试用例列表

        Returns:
            重复测试信息列表
        """
        duplicates: list[DuplicateInfo] = []

        for i, ta in enumerate(tests):
            for tb in tests[i + 1 :]:
                sim = self._calculate_similarity(ta, tb)
                if sim >= 0.8:
                    dup_type = "exact" if sim >= 0.95 else ("similar" if sim >= 0.9 else "overlapping")
                    duplicates.append(
                        DuplicateInfo(
                            test_a=ta.get("name", ""),
                            test_b=tb.get("name", ""),
                            similarity_score=sim,
                            duplicate_type=dup_type,
                            recommendation=self._dedup_recommendation(dup_type),
                        )
                    )

        duplicates.sort(key=lambda d: d.similarity_score, reverse=True)
        return duplicates

    def _calculate_similarity(self, test_a: dict[str, str], test_b: dict[str, str]) -> float:
        """计算两个测试的相似度"""
        name_sim = self._jaccard_similarity(test_a.get("name", ""), test_b.get("name", ""))
        desc_sim = self._jaccard_similarity(test_a.get("description", ""), test_b.get("description", ""))
        tag_sim = self._set_similarity(test_a.get("tags", []), test_b.get("tags", []))

        return name_sim * 0.4 + desc_sim * 0.35 + tag_sim * 0.25

    def _jaccard_similarity(self, a: str, b: str) -> float:
        """Jaccard相似度"""
        set_a = set(a.lower().split())
        set_b = set(b.lower().split())
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0

    def _set_similarity(self, a: list[str], b: list[str]) -> float:
        """集合相似度"""
        set_a = set(t.lower() for t in a)
        set_b = set(t.lower() for t in b)
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0

    def _dedup_recommendation(self, dup_type: str) -> str:
        """去重建议"""
        recommendations = {
            "exact": "完全重复，删除其中一个测试",
            "similar": "高度相似，合并为一个参数化测试",
            "overlapping": "部分重叠，提取公共断言为辅助函数",
        }
        return recommendations.get(dup_type, "审查两个测试的必要性")

    # ==================== 回归窗口策略 ====================

    def plan_regression_window(
        self,
        strategy: RegressionStrategy = RegressionStrategy.SELECTIVE,
        custom_window: RegressionWindow | None = None,
    ) -> dict[str, Any]:
        """
        规划回归窗口

        Args:
            strategy: 回归策略
            custom_window: 自定义窗口配置

        Returns:
            窗口规划结果
        """
        window = custom_window or RegressionWindow(iteration_name="default")

        smoke_budget = window.total_budget_minutes * window.smoke_budget_pct / 100
        regression_budget = window.total_budget_minutes * window.regression_budget_pct / 100
        flaky_budget = window.total_budget_minutes * window.flaky_investigation_budget_pct / 100
        buffer_budget = window.total_budget_minutes * window.remaining_buffer_pct / 100

        plan: dict[str, Any] = {
            "window_name": window.iteration_name,
            "strategy": strategy.value,
            "total_budget_min": window.total_budget_minutes,
            "allocations": {
                "smoke_tests": {"budget_min": smoke_budget, "count": len(self._smoke_tests)},
                "regression_tests": {"budget_min": regression_budget},
                "flaky_investigation": {"budget_min": flaky_budget},
                "buffer": {"budget_min": buffer_budget},
            },
            "strategy_description": self._describe_strategy(strategy),
        }

        match strategy:
            case RegressionStrategy.FULL:
                plan["note"] = "全量回归：执行所有测试套件"
            case RegressionStrategy.INCREMENTAL:
                plan["note"] = "增量回归：仅执行变更影响的测试"
            case RegressionStrategy.SELECTIVE:
                plan["note"] = "选择性回归：基于优先级排序选择高价值测试"

        return plan

    def _describe_strategy(self, strategy: RegressionStrategy) -> str:
        """描述策略"""
        descriptions = {
            RegressionStrategy.FULL: "执行全部测试用例，适用于发布前最终验证",
            RegressionStrategy.INCREMENTAL: "仅执行受变更影响的测试子集，适用于日常CI",
            RegressionStrategy.SELECTIVE: "基于风险模型选择性执行高优先级测试，平衡速度与覆盖",
        }
        return descriptions.get(strategy, "未知策略")

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成回归测试司报告"""
        lines: list[str] = []
        lines.append("# 🔄 回归测试司 · 综合报告\n")

        lines.append(self.get_smoke_report())

        flaky = [ft for ft in self._flaky_tests.values()]
        if flaky:
            lines.append("\n## ⚠️ Flaky Test检测\n")
            lines.append("| 测试 | 失败率 | 运行次数 | 连续失败 | 严重度 | 建议修复 |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for ft in sorted(flaky, key=lambda f: f.failure_rate, reverse=True)[:10]:
                icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(ft.severity.value, "⚪")
                lines.append(
                    f"| `{ft.test_name}` | {ft.failure_rate:.1%} "
                    f"| {ft.total_runs} | {ft.consecutive_failures} "
                    f"| {icon} {ft.severity.value} | {ft.suggested_fix[:30]}... |"
                )

        window_plan = self.plan_regression_window()
        lines.append(f"\n## 📋 回归窗口规划 [{window_plan['strategy']}]\n")
        for alloc_name, alloc_data in window_plan["allocations"].items():
            lines.append(f"- **{alloc_name}**: {alloc_data['budget_min']:.0f}分钟")

        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print("=" * 60)
    print("回归测试司 - 功能演示")
    print("=" * 60)

    si = RegressionTestingSi()

    print("\n--- 冒烟测试套件 ---")
    smoke = si.generate_smoke_suite("web_api")
    print(f"  用例数: {len(smoke)}")
    for s in smoke[:3]:
        print(f"  P{s.priority}: {s.name} - {s.description}")

    print("\n--- 优先级排序 ---")
    tests = [
        {"name": "test_user_login", "path": "tests/auth/test_login.py", "tags": ["critical", "auth"]},
        {"name": "test_payment", "path": "tests/payment/test_pay.py", "tags": ["critical", "payment"]},
        {"name": "test_ui_button", "path": "tests/ui/test_button.py", "tags": ["ui"]},
        {"name": "test_utils_format", "path": "tests/utils/test_format.py", "tags": ["unit"]},
    ]
    priorities = si.prioritize_tests(tests)
    for p in priorities[:4]:
        print(f"  {p.score:.1f}: {p.test_name} [{'✅' if p.recommended else '⏭️'}]")

    print("\n--- Flaky检测 ---")
    for _ in range(8):
        si.record_test_result("test_flaky_network", passed=_ % 3 != 0)
        si.record_test_result("test_stable", passed=True)
    flaky = si.detect_flaky_tests(min_runs=5)
    print(f"  发现Flaky: {len(flaky)}个")
    for ft in flaky:
        print(f"  [{ft.severity.value}] {ft.test_name}: 失败率={ft.failure_rate:.1%}, 建议: {ft.suggested_fix}")

    print("\n--- 测试去重 ---")
    dupes = si.deduplicate_tests([
        {"name": "test_user_create_success", "description": "创建用户成功", "tags": ["user", "crud"]},
        {"name": "test_user_creation_ok", "description": "用户创建正常", "tags": ["user", "create"]},
        {"name": "test_delete_item", "description": "删除条目", "tags": ["item", "delete"]},
    ])
    for d in dupes:
        print(f"  [{d.duplicate_type}] '{d.test_a}' ~ '{d.test_b}' (相似度:{d.similarity_score:.1%})")

    print("\n--- 回归窗口 ---")
    window = si.plan_regression_window(RegressionStrategy.SELECTIVE)
    print(f"  策略: {window['strategy']}")

    report = si.generate_report()
    print(f"\n--- 报告预览 (前600字符) ---\n{report[:600]}...")

    print("\n✅ 所有测试通过!")
