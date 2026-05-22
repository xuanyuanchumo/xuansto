"""
TDD执行司 - 红绿蓝循环引擎、测试先行驱动、断言设计指导
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class TDDPhase(Enum):
    """TDD循环阶段"""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class AssertionType(Enum):
    """断言类型枚举"""

    EQUAL = auto()
    CONTAINS = auto()
    RAISES = auto()
    ATTRIBUTE_MATCH = auto()
    COLLECTION_MATCH = auto()
    TYPE_CHECK = auto()
    TRUTHY = auto()
    NONE_CHECK = auto()


class MockType(Enum):
    """Mock类型枚举"""

    MOCK = "mock"
    STUB = "stub"
    SPY = "spy"
    FAKE = "fake"


@dataclass
class FunctionSignature:
    """函数签名"""

    name: str
    params: list[dict[str, str]] = field(default_factory=list)
    return_type: str = "Any"
    docstring: str = ""


@dataclass
class TestSkeleton:
    """测试骨架"""

    test_name: str
    setup_code: str = ""
    action_code: str = ""
    assertion_code: str = ""
    teardown_code: str = ""


@dataclass
class TDDCycleState:
    """TDD循环状态"""

    current_phase: TDDPhase = TDDPhase.RED
    iteration_count: int = 0
    tests_written: int = 0
    tests_passing: int = 0
    pass_rate: float = 0.0
    violations: list[str] = field(default_factory=list)
    phase_history: list[TDDPhase] = field(default_factory=list)


@dataclass
class AssertionPattern:
    """断言模式"""

    assertion_type: AssertionType
    template: str
    description: str
    example: str


@dataclass
class DisciplineCheckResult:
    """纪律检查结果"""

    passed: bool = True
    violations: list[dict[str, str]] = field(default_factory=list)
    score: float = 100.0


class TDDExecutionError(Exception):
    """TDD执行异常"""


class TDDPhaseError(TDDExecutionError):
    """TDD阶段异常"""


class TDDExecutionSi:
    """
    TDD执行司 - 兵部·职方司

    提供完整的TDD红绿蓝循环支持：
    - 红阶段：测试编写引导（基于函数签名生成测试骨架、断言设计）
    - 绿阶段：最小实现引导（仅写足够通过测试的代码、禁止过度实现警告）
    - 蓝阶段：重构引导（安全重构检查清单、重构前后行为不变验证）
    """

    def __init__(self) -> None:
        self._state = TDDCycleState()
        self._assertion_patterns = self._build_assertion_patterns()

    @property
    def state(self) -> TDDCycleState:
        return self._state

    # ==================== TDD状态机 ====================

    def advance_phase(self) -> TDDPhase:
        """
        推进到下一个阶段 (RED → GREEN → BLUE → RED)
        """
        match self._state.current_phase:
            case TDDPhase.RED:
                self._state.current_phase = TDDPhase.GREEN
            case TDDPhase.GREEN:
                self._state.current_phase = TDDPhase.BLUE
            case TDDPhase.BLUE:
                self._state.current_phase = TDDPhase.RED
                self._state.iteration_count += 1
            case _:
                raise TDDPhaseError(f"未知TDD阶段: {self._state.current_phase}")

        self._state.phase_history.append(self._state.current_phase)
        return self._state.current_phase

    def set_phase(self, phase: TDDPhase) -> None:
        """手动设置当前阶段"""
        self._state.current_phase = phase
        self._state.phase_history.append(phase)

    def reset_cycle(self) -> None:
        """重置TDD循环"""
        self._state = TDDCycleState()

    def get_progress(self) -> dict[str, Any]:
        """获取循环进度信息"""
        return {
            "current_phase": self._state.current_phase.value,
            "iteration_count": self._state.iteration_count,
            "tests_written": self._state.tests_written,
            "tests_passing": self._state.tests_passing,
            "pass_rate": f"{self._state.pass_rate:.1%}",
            "total_phases": len(self._state.phase_history),
            "phase_sequence": [p.value for p in self._state.phase_history[-10:]],
        }

    # ==================== 红阶段：测试编写引导 ====================

    def generate_test_skeleton(
        self, signature: FunctionSignature | dict[str, Any]
    ) -> TestSkeleton:
        """
        基于函数签名生成测试骨架

        Args:
            signature: 函数签名对象或字典

        Returns:
            测试骨架对象
        """
        if isinstance(signature, dict):
            sig = FunctionSignature(
                name=signature.get("name", "func"),
                params=signature.get("params", []),
                return_type=signature.get("return_type", "Any"),
                docstring=signature.get("docstring", ""),
            )
        else:
            sig = signature

        param_names = [p.get("name", f"arg{i}") for i, p in enumerate(sig.params)]
        test_name = f"test_{sig.name}"
        setup_code = self._generate_setup(sig, param_names)
        action_code = self._generate_action(sig, param_names)
        assertion_code = self._generate_assertion(sig)

        return TestSkeleton(
            test_name=test_name,
            setup_code=setup_code,
            action_code=action_code,
            assertion_code=assertion_code,
        )

    def _generate_setup(self, sig: FunctionSignature, param_names: list[str]) -> str:
        """生成setUp代码"""
        lines: list[str] = []
        for i, param in enumerate(sig.params):
            pname = param.get("name", f"arg{i}")
            ptype = param.get("type", "Any")
            default = param.get("default")

            if default is not None:
                continue

            type_hints: dict[str, str] = {
                "str": 'f"test_{pname}"',
                "int": "42",
                "float": "3.14",
                "bool": "True",
                "list": "[1, 2, 3]",
                "dict": '{"key": "value"}',
                "Path": 'Path("/tmp/test")',
            }
            value = type_hints.get(ptype, f"Mock()")
            lines.append(f"{pname} = {value}")

        return "\n".join(lines) if lines else "# 无需前置准备"

    def _generate_action(self, sig: FunctionSignature, param_names: list[str]) -> str:
        """生成动作代码"""
        args_str = ", ".join(param_names)
        if sig.return_type != "None":
            return f"result = {sig.name}({args_str})"
        return f"{sig.name}({args_str})"

    def _generate_assertion(self, sig: FunctionSignature) -> str:
        """生成断言代码"""
        type_assertion_map: dict[str, str] = {
            "int": "assert isinstance(result, int)",
            "str": "assert isinstance(result, str)",
            "bool": "assert isinstance(result, bool)",
            "list": "assert isinstance(result, list)",
            "dict": "assert isinstance(result, dict)",
            "None": "pass",
        }
        base_assert = type_assertion_map.get(
            sig.return_type, "assert result is not None"
        )
        return f"# TODO: 添加具体断言\n{base_assert}"

    def design_assertions(
        self, scenario: str, expected_behavior: str
    ) -> list[AssertionPattern]:
        """
        根据场景和行为设计推荐断言

        Args:
            scenario: 测试场景描述
            expected_behavior: 预期行为描述

        Returns:
            推荐的断言模式列表
        """
        keywords_lower = scenario.lower() + " " + expected_behavior.lower()
        recommended: list[AssertionPattern] = []

        keyword_patterns: list[tuple[list[str], AssertionType]] = [
            (["equal", "等于", "相同", "返回"], AssertionType.EQUAL),
            (["contain", "包含", "存在", "有"], AssertionType.CONTAINS),
            (["raise", "抛出", "异常", "错误"], AssertionType.RAISES),
            (["attribute", "属性", "字段"], AssertionType.ATTRIBUTE_MATCH),
            (["collection", "列表", "数组", "集合"], AssertionType.COLLECTION_MATCH),
            (["type", "类型", "实例"], AssertionType.TYPE_CHECK),
            (["truthy", "真", "非空"], AssertionType.TRUTHY),
            (["none", "空", "null"], AssertionType.NONE_CHECK),
        ]

        for keywords, atype in keyword_patterns:
            if any(kw in keywords_lower for kw in keywords):
                pattern = next(
                    (p for p in self._assertion_patterns if p.assertion_type == atype), None
                )
                if pattern:
                    recommended.append(pattern)

        return recommended or [
            p for p in self._assertion_patterns if p.assertion_type == AssertionType.EQUAL
        ]

    # ==================== 绿阶段：最小实现引导 ====================

    def guide_minimal_implementation(self, test_skeleton: TestSkeleton) -> dict[str, Any]:
        """
        最小实现引导 - 仅写足够通过测试的代码

        Args:
            test_skeleton: 对应的测试骨架

        Returns:
            实现指导字典
        """
        assertions = test_skeleton.assertion_code
        required_return = self._infer_required_return(assertions)
        warnings: list[str] = []

        over_impl_patterns = [
            (r"(?:if|elif|else).*?(?:and|or)", "条件分支过多，可能过度实现"),
            (r"for\s+\w+\s+in.*?:\s*.*?\n\s*.*?\n\s*.*?", "循环体内逻辑过多"),
            (r"class\s+\w+", "不应在最小实现中定义新类"),
            (r"(?:try|except|finally)", "不应在最小实现中添加异常处理"),
        ]

        for pattern, msg in over_impl_patterns:
            if re.search(pattern, assertions, re.DOTALL):
                warnings.append(msg)

        return {
            "required_return": required_return,
            "implementation_hint": f"实现只需让以下断言通过:\n{assertions}",
            "warnings": warnings,
            "over_implementation_risk": len(warnings) > 0,
            "principle": "YAGNI - 只写足够通过当前测试的代码",
        }

    def _infer_required_return(self, assertion_code: str) -> str:
        """从断言代码推断所需返回值"""
        if "isinstance(result, int)" in assertion_code:
            return "int (如: 0, 1, 42)"
        elif "isinstance(result, str)" in assertion_code:
            return 'str (如: "", "ok")'
        elif "isinstance(result, bool)" in assertion_code:
            return "bool (如: True, False)"
        elif "isinstance(result, list)" in assertion_code:
            return "list (如: [], [1])"
        elif "isinstance(result, dict)" in assertion_code:
            return "dict (如: {}, {'key': 'value'})"
        elif "not None" in assertion_code:
            return "非None的任意值"
        return "根据断言推断"

    # ==================== 蓝阶段：重构引导 ====================

    def get_refactoring_checklist(self) -> list[dict[str, str]]:
        """获取重构检查清单"""
        return [
            {"item": "所有测试是否仍然通过？", "category": "验证"},
            {"item": "是否消除了代码异味？", "category": "质量"},
            {"item": "函数/方法长度是否合理(≤30行)?", "category": "可读性"},
            {"item": "命名是否有意义且一致？", "category": "命名"},
            {"item": "是否减少了重复代码(DRY)?", "category": "DRY"},
            {"item": "复杂度是否降低？", "category": "复杂度"},
            {"item": "是否保持了公共API不变？", "category": "兼容性"},
            {"item": "注释和文档是否更新？", "category": "文档"},
        ]

    def verify_refactoring_safety(
        self, before_output: str, after_output: str
    ) -> dict[str, Any]:
        """
        验证重构前后行为等价性

        Args:
            before_output: 重构前输出
            after_output: 重构后输出

        Returns:
            验证结果
        """
        is_equivalent = before_output.strip() == after_output.strip()
        return {
            "behavior_preserved": is_equivalent,
            "before_length": len(before_output),
            "after_length": len(after_output),
            "size_change": len(after_output) - len(before_output),
            "size_change_pct": (
                (len(after_output) - len(before_output)) / max(len(before_output), 1) * 100
            ),
            "recommendation": (
                "✅ 重构安全，行为保持一致"
                if is_equivalent
                else "⚠️ 输出不一致，请检查重构是否引入了行为变更"
            ),
        }

    # ==================== TDD纪律检查 ====================

    def check_discipline(self, actions_log: list[dict[str, str]]) -> DisciplineCheckResult:
        """
        TDD纪律检查

        检查项：
        - 是否跳过红阶段直接写代码
        - 是否遗漏蓝阶段重构
        - 是否一次写过多测试
        - 是否跳过失败的测试去写新功能
        """
        result = DisciplineCheckResult()
        phases_seen: set[str] = set()
        red_before_green = True
        green_before_blue = True

        for idx, action in enumerate(actions_log):
            phase = action.get("phase", "")
            action_type = action.get("action", "")

            phases_seen.add(phase)

            if phase == "GREEN" and "RED" not in phases_seen:
                red_before_green = False
                result.violations.append({
                    "type": "skip_red",
                    "message": f"步骤{idx}: 跳过RED阶段直接进入GREEN",
                    "severity": "high",
                })
                result.score -= 20

            if phase == "BLUE" and "GREEN" not in phases_seen:
                green_before_blue = False
                result.violations.append({
                    "type": "skip_green",
                    "message": f"步骤{idx}: 跳过GREEN阶段直接进入BLUE",
                    "severity": "high",
                })
                result.score -= 15

            if phase == "RED" and action_type == "implement":
                result.violations.append({
                    "type": "red_phase_implement",
                    "message": f"步骤{idx}: 在RED阶段写了实现代码而非测试",
                    "severity": "medium",
                })
                result.score -= 10

        has_red = "RED" in phases_seen
        has_green = "GREEN" in phases_seen
        has_blue = "BLUE" in phases_seen

        if has_red and has_green and not has_blue:
            result.violations.append({
                "type": "missing_refactor",
                "message": "完成GREEN后未执行BLUE(重构)阶段",
                "severity": "medium",
            })
            result.score -= 15

        result.passed = result.score >= 70
        result.score = max(0, result.score)
        return result

    # ==================== Mock/Stub选择指南 ====================

    def get_mock_guide(self, dependency_type: str) -> dict[str, Any]:
        """
        Mock/Stub/Spy/Fake选择指南

        Args:
            dependency_type: 依赖类型描述

        Returns:
            推荐方案及说明
        """
        guides: dict[str, dict[str, Any]] = {
            "database": {
                "recommended": MockType.FAKE,
                "reason": "数据库依赖应使用Fake(内存数据库)，保留真实查询语义",
                "example": "SQLite内存模式 / SQLAlchemy mock session",
                "alternative": MockType.STUB,
            },
            "http_client": {
                "recommended": MockType.MOCK,
                "reason": "HTTP客户端适合用Mock控制响应，隔离外部服务",
                "example": "responses库 / pytest-httpx / unittest.mock.patch",
                "alternative": MockType.STUB,
            },
            "file_system": {
                "recommended": MockType.FAKE,
                "reason": "文件系统使用tmp_path/临时目录作为Fake",
                "example": "pytest tmp_path fixture / tempfile.mkdtemp()",
                "alternative": MockType.MOCK,
            },
            "external_api": {
                "recommended": MockType.STUB,
                "reason": "外部API用Stub预设返回值，简化测试设置",
                "example": "预定义响应字典 / 固定返回值",
                "alternative": MockType.MOCK,
            },
            "time": {
                "recommended": MockType.MOCK,
                "reason": "时间相关需要Mock来控制时钟",
                "example": "freezegun / unittest.mock.patch('time.time')",
                "alternative": MockType.STUB,
            },
            "logger": {
                "recommended": MockType.SPY,
                "reason": "日志记录使用Spy验证是否被调用",
                "example": "caplog fixture / Mock(wraps=logger)",
                "alternative": MockType.STUB,
            },
        }

        dep_key = dependency_type.lower().replace(" ", "_")
        base_guide = guides.get(dep_key, {
            "recommended": MockType.MOCK,
            "reason": "默认使用Mock进行依赖隔离",
            "example": "unittest.mock.patch / pytest-mock",
            "alternative": MockType.STUB,
        })

        type_descriptions = {
            MockType.MOCK: "完全控制对象行为，可设置返回值和副作用",
            MockType.STUB: "提供预设响应，不关心调用细节",
            MockType.SPY: "记录调用信息，用于验证交互",
            MockType.FAKE: "轻量级真实实现替代品",
        }

        base_guide["type_descriptions"] = {
            k.value: v for k, v in type_descriptions.items()
        }
        return base_guide

    # ==================== 断言模式库 ====================

    def _build_assertion_patterns(self) -> list[AssertionPattern]:
        """构建断言模式库"""
        return [
            AssertionPattern(
                assertion_type=AssertionType.EQUAL,
                template="assert actual == expected, f'Expected {expected}, got {actual}'",
                description="精确相等比较",
                example="assert result.status_code == 200",
            ),
            AssertionPattern(
                assertion_type=AssertionType.CONTAINS,
                template="assert needle in haystack, f'{needle} not found'",
                description="包含关系检查",
                example="assert 'success' in response.text",
            ),
            AssertionPattern(
                assertion_type=AssertionType.RAISES,
                template="with pytest.raises(ExpectedException) as exc_info:\n    func()",
                description="异常抛出验证",
                example="with pytest.raises(ValueError):\n    divide(1, 0)",
            ),
            AssertionPattern(
                assertion_type=AssertionType.ATTRIBUTE_MATCH,
                template="assert hasattr(obj, 'attr')\nassert obj.attr == expected",
                description="属性匹配验证",
                example="assert user.name == 'Alice'",
            ),
            AssertionPattern(
                assertion_type=AssertionType.COLLECTION_MATCH,
                template="assert len(collection) == expected_len\nassert all(item in collection for item in expected_items)",
                description="集合内容匹配",
                example="assert set(result) == {1, 2, 3}",
            ),
            AssertionPattern(
                assertion_type=AssertionType.TYPE_CHECK,
                template="assert isinstance(value, ExpectedType)",
                description="类型验证",
                example="assert isinstance(config, dict)",
            ),
            AssertionPattern(
                assertion_type=AssertionType.TRUTHY,
                template="assert value, 'Expected truthy value'",
                description="真值检查",
                example="assert user.is_active",
            ),
            AssertionPattern(
                assertion_type=AssertionType.NONE_CHECK,
                template="assert value is None, 'Expected None'",
                description="空值检查",
                example="assert result.error is None",
            ),
        ]

    def get_assertion_pattern(self, assertion_type: AssertionType) -> AssertionPattern | None:
        """获取指定类型的断言模式"""
        for pattern in self._assertion_patterns:
            if pattern.assertion_type == assertion_type:
                return pattern
        return None

    def list_all_patterns(self) -> list[dict[str, str]]:
        """列出所有断言模式"""
        return [
            {
                "type": p.assertion_type.name,
                "description": p.description,
                "template": p.template,
                "example": p.example,
            }
            for p in self._assertion_patterns
        ]

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成TDD循环进度报告"""
        progress = self.get_progress()
        lines: list[str] = []
        lines.append("# 🔴🟢🔵 TDD执行司 · 循环报告\n")
        lines.append("| 指标 | 值 |")
        lines.append("| --- | --- |")
        lines.append(f"| 当前阶段 | **{progress['current_phase'].upper()}** |")
        lines.append(f"| 迭代次数 | {progress['iteration_count']} |")
        lines.append(f"| 已写测试 | {progress['tests_written']} |")
        lines.append(f"| 通过测试 | {progress['tests_passing']} |")
        lines.append(f"| 通过率 | {progress['pass_rate']} |")
        lines.append(f"| 总阶段切换 | {progress['total_phases']} |")

        if progress["phase_sequence"]:
            lines.append(f"\n### 近期阶段序列\n")
            lines.append(" → ".join(progress["phase_sequence"]))

        checklist = self.get_refactoring_checklist()
        lines.append(f"\n### 📋 重构检查清单\n")
        for item in checklist:
            lines.append(f"- [ ] {item['item']} ({item['category']})")

        patterns = self.list_all_patterns()
        lines.append(f"\n### 📐 断言模式库 ({len(patterns)})\n")
        lines.append("| 类型 | 描述 | 示例 |")
        lines.append("| --- | --- | --- |")
        for p in patterns[:5]:
            lines.append(f"| `{p['type']}` | {p['description']} | `{p['example']}` |")

        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print("=" * 60)
    print("TDD执行司 - 功能演示")
    print("=" * 60)

    si = TDDExecutionSi()

    print("\n--- TDD状态机 ---")
    for _ in range(4):
        phase = si.advance_phase()
        print(f"  当前阶段: {phase.value.upper()}")

    si.reset_cycle()
    progress = si.get_progress()
    print(f"\n  进度: {progress}")

    print("\n--- 测试骨架生成 ---")
    sig = FunctionSignature(
        name="calculate_discount",
        params=[
            {"name": "price", "type": "float"},
            {"name": "rate", "type": "float", "default": "0.1"},
        ],
        return_type="float",
        docstring="计算折扣价格",
    )
    skeleton = si.generate_test_skeleton(sig)
    print(f"  测试名: {skeleton.test_name}")
    print(f"  Setup:\n{skeleton.setup_code}")
    print(f"  Action:\n{skeleton.action_code}")
    print(f"  Assert:\n{skeleton.assertion_code}")

    print("\n--- 断言设计 ---")
    patterns = si.design_assertions("用户登录成功", "返回用户token字符串")
    for p in patterns:
        print(f"  [{p.assertion_type.name}] {p.description}")

    print("\n--- 纪律检查 ---")
    bad_actions = [
        {"phase": "GREEN", "action": "implement"},
        {"phase": "RED", "action": "implement"},
    ]
    disc_result = si.check_discipline(bad_actions)
    print(f"  通过: {disc_result.passed}, 得分: {disc_result.score:.0f}")
    for v in disc_result.violations:
        print(f"  ⚠️ [{v['type']}] {v['message']}")

    print("\n--- Mock指南 ---")
    guide = si.get_mock_guide("http_client")
    print(f"  推荐: {guide['recommended'].value}")
    print(f"  原因: {guide['reason']}")

    report = si.generate_report()
    print(f"\n--- 报告预览 ---\n{report[:400]}...")

    print("\n✅ 所有测试通过!")
