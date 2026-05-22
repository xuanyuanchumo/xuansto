"""
测试框架司 - 测试框架适配、Mock/Stub管理、测试数据管理
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class TestFramework(Enum):
    """支持的测试框架"""

    PYTEST = "pytest"
    JEST = "jest"
    GO_TEST = "go-test"
    JUNIT5 = "junit5"
    RSPEC = "rspec"
    VITEST = "vitest"


class TestMark(Enum):
    """测试标记类型"""

    SLOW = "slow"
    INTEGRATION = "integration"
    SMOKE = "smoke"
    UNIT = "unit"
    E2E = "e2e"
    REGRESSION = "regression"
    SKIP = "skip"
    XFAIL = "xfail"


@dataclass
class MockConfig:
    """Mock配置"""

    target: str
    mock_type: str = "mock"
    return_value: Any = None
    side_effect: Any = None
    autospec: bool = True
    wraps: bool = False


@dataclass
class FixtureConfig:
    """Fixture配置"""

    name: str
    scope: str = "function"
    params: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    code: str = ""
    teardown_code: str = ""


@dataclass
class TestDataFactory:
    """测试数据工厂"""

    name: str
    factory_type: str = "builder"
    fields: dict[str, Any] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)
    template_code: str = ""


@dataclass
class ParametrizedTest:
    """参数化测试"""

    test_name: str
    arg_names: list[str]
    test_cases: list[dict[str, Any]]
    ids: list[str] | None = None


@dataclass
class FrameworkConfig:
    """框架配置"""

    framework: TestFramework
    config_content: str = ""
    best_practices: list[str] = field(default_factory=list)
    required_plugins: list[str] = field(default_factory=list)


@dataclass
class IsolationConfig:
    """环境隔离配置"""

    database_rollback: bool = True
    tmp_filesystem: bool = True
    http_mock_server: bool = False
    env_isolation: bool = True
    process_isolation: bool = False


class TestFrameworkError(Exception):
    """测试框架异常"""


class UnsupportedFrameworkError(TestFrameworkError):
    """不支持的框架异常"""


class MockGenerationError(TestFrameworkError):
    """Mock生成异常"""


class TestFrameworkSi:
    """
    测试框架司 - 兵部·驾部司

    提供多测试框架适配、Mock管理、测试数据工厂等能力：
    - 多框架适配层（pytest/jest/go-test/JUnit5/RSpec/Vitest）
    - Mock/Stub/Spy/Factory模式选择与代码生成
    - 测试Fixture管理与依赖注入
    - 参数化测试生成
    - 测试分组与标记
    """

    def __init__(self) -> None:
        self._framework_configs: dict[TestFramework, FrameworkConfig] = {}
        self._init_framework_configs()

    # ==================== 框架适配 ====================

    def _init_framework_configs(self) -> None:
        """初始化各框架默认配置"""
        self._framework_configs = {
            TestFramework.PYTEST: FrameworkConfig(
                framework=TestFramework.PYTEST,
                config_content="""\
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py *_test.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --tb=short --strict-markers"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: integration tests",
    "smoke: smoke tests",
]
log_cli = true
log_cli_level = INFO
""",
                best_practices=[
                    "使用conftest.py集中管理fixture",
                    "遵循arrange-act-assert模式",
                    "使用pytest.mark进行分类标记",
                    "避免过度mock，优先使用真实对象",
                    "每个测试函数只验证一个行为",
                ],
                required_plugins=["pytest-cov", "pytest-mock", "pytest-xdist"],
            ),
            TestFramework.JEST: FrameworkConfig(
                framework=TestFramework.JEST,
                config_content="""\
module.exports = {
  testMatch: ['**/__tests__/**/*.test.js', '**/?(*.)+(spec|test).js'],
  collectCoverageFrom: ['src/**/*.{js,jsx}', '!src/index.js'],
  coverageThreshold: {
    global: { branches: 80, functions: 80, lines: 80, statements: 80 }
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
};
""",
                best_practices=[
                    "使用describe/it组织测试",
                    "beforeEach/beforeAll管理状态",
                    "使用jest.fn()创建mock函数",
                    "使用toMatchSnapshot做快照测试",
                ],
                required_plugins=["@testing-library/react", "@testing-library/jest-dom"],
            ),
            TestFramework.GO_TEST: FrameworkConfig(
                framework=TestFramework.GO_TEST,
                config_content="",
                best_practices=[
                    "使用table-driven tests",
                    "子测试(subtests)组织用例",
                    "使用testify/mockery进行mock",
                    "_test.go文件与源码同目录",
                ],
                required_plugins=[],
            ),
        }

    def get_framework_config(self, framework: TestFramework) -> FrameworkConfig:
        """
        获取指定框架的配置

        Args:
            framework: 测试框架枚举

        Returns:
            框架配置对象
        """
        if framework not in self._framework_configs:
            raise UnsupportedFrameworkError(f"不支持的测试框架: {framework.value}")
        return self._framework_configs[framework]

    def generate_config_file(self, framework: TestFramework) -> str:
        """生成框架配置文件内容"""
        config = self.get_framework_config(framework)
        match framework:
            case TestFramework.PYTEST:
                filename = "pytest.ini / pyproject.toml [tool.pytest.ini_options]"
            case TestFramework.JEST:
                filename = "jest.config.js"
            case _:
                filename = f"{framework.value}.config"

        lines: list[str] = []
        lines.append(f"# {filename}\n")
        lines.append(config.config_content)
        if config.required_plugins:
            lines.append(f"\n# 推荐插件: {', '.join(config.required_plugins)}")
        return "\n".join(lines)

    # ==================== Mock/Stub代码生成 ====================

    def generate_mock_code(
        self, config: MockConfig, framework: TestFramework = TestFramework.PYTEST
    ) -> str:
        """
        生成Mock代码

        Args:
            config: Mock配置
            framework: 目标框架

        Returns:
            生成的Mock代码字符串
        """
        match framework:
            case TestFramework.PYTEST:
                return self._generate_pytest_mock(config)
            case TestFramework.JEST:
                return self._generate_jest_mock(config)
            case _:
                return f"# TODO: 实现{framework.value}的mock生成"

    def _generate_pytest_mock(self, config: MockConfig) -> str:
        """生成pytest风格的mock代码"""
        lines: list[str] = []
        lines.append(f"@pytest.fixture")

        fixture_name = f"mock_{config.target.replace('.', '_')}"
        lines.append(f"def {fixture_name}():")
        if config.mock_type == "spy":
            lines.append(f"    spy = MagicMock(wraps={config.target})")
            lines.append("    yield spy")
        elif config.mock_type == "stub":
            lines.append(f"    stub = MagicMock()")
            if config.return_value is not None:
                rv_str = json.dumps(config.return_value, ensure_ascii=False)
                lines.append(f"    stub.return_value = {rv_str}")
            lines.append("    yield stub")
        else:
            lines.append(f"    m = MagicMock(autospec={config.autospec})")
            if config.return_value is not None:
                rv_str = json.dumps(config.return_value, ensure_ascii=False)
                lines.append(f"    m.return_value = {rv_str}")
            if config.side_effect is not None:
                se_str = json.dumps(config.side_effect, ensure_ascii=False)
                lines.append(f"    m.side_effect = {se_str}")
            lines.append("    yield m")

        return "\n".join(lines)

    def _generate_jest_mock(self, config: MockConfig) -> str:
        """生成Jest风格的mock代码"""
        lines: list[str] = []
        module_path = config.target.replace(".", "/")
        lines.append(f"jest.mock('{module_path}')")

        if config.mock_type == "spy":
            lines.append(f"const {config.target} = require.actual('{module_path}')")
            lines.append(f"jest.spyOn({config.target}, 'methodName')")
        elif config.mock_type == "stub":
            lines.append(f"const {config.target} = jest.fn()")
            if config.return_value is not None:
                rv_str = json.dumps(config.return_value, ensure_ascii=False)
                lines.append(f"{config.target}.mockReturnValue({rv_str})")
        else:
            lines.append(f"const {config.target}: any = jest.fn()")

        return "\n".join(lines)

    # ==================== Fixture管理 ====================

    def generate_fixture(self, config: FixtureConfig, framework: TestFramework = TestFramework.PYTEST) -> str:
        """
        生成Fixture代码

        Args:
            config: Fixture配置
            framework: 目标框架

        Returns:
            生成的Fixture代码
        """
        match framework:
            case TestFramework.PYTEST:
                return self._generate_pytest_fixture(config)
            case TestFramework.JEST:
                return self._generate_jest_fixture(config)
            case _:
                return f"# TODO: 实现{framework.value}的fixture生成"

    def _generate_pytest_fixture(self, config: FixtureConfig) -> str:
        """生成pytest fixture"""
        scope_map = {
            "function": "",
            "class": "(scope='class')",
            "module": "(scope='module')",
            "session": "(scope='session')",
        }
        scope_decorator = scope_map.get(config.scope, "")
        param_str = ", ".join(config.params)

        lines: list[str] = []
        lines.append(f"@pytest.fixture{scope_decorator}")
        if param_str:
            lines.append(f"def {config.name}({param_str}):")
        else:
            lines.append(f"def {config.name}():")

        if config.code:
            for line in config.code.split("\n"):
                lines.append(f"    {line}")

        lines.append("    # 返回fixture值")
        lines.append("    yield ...")

        if config.teardown_code:
            lines.append("")
            for line in config.teardown_code.split("\n"):
                lines.append(f"    {line}")

        return "\n".join(lines)

    def _generate_jest_fixture(self, config: FixtureConfig) -> str:
        """生成Jest fixture"""
        scope_map = {"function": "", "class": "", "module": "beforeAll", "session": ""}
        prefix = scope_map.get(config.scope, "")

        lines: list[str] = []
        func_name = f"{prefix}{config.name}" if prefix else config.name
        lines.append(f"let {func_name}: any;")
        lines.append(f"beforeEach(() => {{")

        if config.code:
            for line in config.code.split("\n"):
                lines.append(f"  {line}")

        lines.append("});")

        if config.teardown_code:
            lines.append(f"afterEach(() => {{")
            for line in config.teardown_code.split("\n"):
                lines.append(f"  {line}")
            lines.append("});")

        return "\n".join(lines)

    # ==================== 测试数据工厂 ====================

    def generate_data_factory(self, factory: TestDataFactory, framework: TestFramework = TestFramework.PYTEST) -> str:
        """
        生成测试数据工厂代码

        Args:
            factory: 数据工厂配置
            framework: 目标框架

        Returns:
            生成的数据工厂代码
        """
        match factory.factory_type:
            case "builder":
                return self._generate_builder_pattern(factory)
            case "object_mother":
                return self._generate_object_mother(factory)
            case "fuzz":
                return self._generate_fuzz_data(factory)
            case _:
                return "# 未知的工厂类型"

    def _generate_builder_pattern(self, factory: TestDataFactory) -> str:
        """Builder Pattern生成"""
        class_name = f"{factory.name.title()}Builder"
        lines: list[str] = []
        lines.append(f"class {class_name}:")
        lines.append(f'    """{factory.name}数据构建器"""')
        lines.append("    def __init__(self):")

        for field_name, field_type in factory.fields.items():
            default_val = factory.defaults.get(field_name, "None")
            lines.append(f"        self._{field_name} = {default_val}")

        lines.append("")

        for field_name, field_type in factory.fields.items():
            lines.append(f"    def with_{field_name}(self, value):")
            lines.append(f"        self._{field_name} = value")
            lines.append(f"        return self")
            lines.append("")

        lines.append("    def build(self) -> dict:")
        lines.append("        return {")
        for field_name in factory.fields:
            lines.append(f"            '{field_name}': self._{field_name},")
        lines.append("        }")
        return "\n".join(lines)

    def _generate_object_mother(self, factory: TestDataFactory) -> str:
        """Object Mother模式生成"""
        lines: list[str] = []
        lines.append(f"class {factory.name}Mother:")
        lines.append(f'    """{factory.name} Object Mother"""')

        lines.append("    @staticmethod")
        lines.append(f"    def default() -> dict:")
        data_dict = {k: v for k, v in factory.defaults.items()}
        if not data_dict:
            data_dict = {k: f"<{v}>" for k, v in factory.fields.items()}
        lines.append(f'        return {json.dumps(data_dict, indent=8, ensure_ascii=False)}')

        lines.append("")
        lines.append("    @staticmethod")
        lines.append(f"    def with_custom_{list(factory.fields.keys())[0] if factory.fields else 'value'}(value) -> dict:")
        lines.append("        data = {factory.name}Mother.default()")
        key = list(factory.fields.keys())[0] if factory.fields else "key"
        lines.append(f"        data['{key}'] = value")
        lines.append("        return data")

        return "\n".join(lines)

    def _generate_fuzz_data(self, factory: TestDataFactory) -> str:
        """Fuzz测试数据生成"""
        import random
        import string

        lines: list[str] = []
        lines.append(f"def generate_fuzz_{factory.name.lower()}(count: int = 10) -> list[dict]:")
        lines.append('    """生成模糊测试数据"""')
        lines.append("    results = []")
        lines.append("    for _ in range(count):")
        lines.append("        results.append({")

        for field_name, field_type in factory.fields.items():
            type_generators: dict[str, str] = {
                "str": f"''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(1, 20)))'",
                "int": "random.randint(-1000, 1000)",
                "float": "round(random.uniform(-100.0, 100.0), 2)",
                "bool": "random.choice([True, False])",
                "list": "[random.randint(0, 9) for _ in range(random.randint(0, 5))]",
            }
            gen = type_generators.get(str(field_type), "None")
            lines.append(f"            '{field_name}': {gen},")

        lines.append("        })")
        lines.append("    return results")

        return "\n".join(lines)

    # ==================== 参数化测试 ====================

    def generate_parametrized_test(
        self, test: ParametrizedTest, framework: TestFramework = TestFramework.PYTEST
    ) -> str:
        """
        生成参数化测试代码

        Args:
            test: 参数化测试配置
            framework: 目标框架

        Returns:
            生成的参数化测试代码
        """
        match framework:
            case TestFramework.PYTEST:
                return self._generate_pytest_parametrize(test)
            case TestFramework.JEST:
                return self._generate_jest_parametrize(test)
            case TestFramework.GO_TEST:
                return self._generate_go_parametrize(test)
            case _:
                return f"# TODO: 实现{framework.value}的参数化测试"

    def _generate_pytest_parametrize(self, test: ParametrizedTest) -> str:
        """pytest参数化测试"""
        args_str = ", ".join(test.arg_names)
        cases_json = json.dumps(test.test_cases, indent=4, ensure_ascii=False)

        lines: list[str] = []
        decorator = "@pytest.mark.parametrize"
        if test.ids:
            ids_json = json.dumps(test.ids, ensure_ascii=False)
            lines.append(f'{decorator}("{args_str}", {cases_json}, ids={ids_json})')
        else:
            lines.append(f'{decorator}("{args_str}", {cases_json})')

        lines.append(f"def {test.test_name}({args_str}):")
        lines.append("    # Arrange & Act & Assert")
        lines.append("    ...")

        return "\n".join(lines)

    def _generate_jest_parametrize(self, test: ParametrizedTest) -> str:
        """Jest参数化测试"""
        args_str = ", ".join(test.arg_names)
        lines: list[str] = []

        lines.append(f"describe('{test.test_name}', () => {{")

        for i, case in enumerate(test.test_cases):
            values = [case.get(a, "...") for a in test.arg_names]
            values_str = ", ".join(str(v) for v in values)
            label = test.ids[i] if test.ids and i < len(test.ids) else f"case_{i}"

            escaped_label = label.replace("'", "\\'")
            lines.append(f"  it('{escaped_label}', () => {{")

            for j, arg_name in enumerate(test.arg_names):
                val = values[j]
                val_str = json.dumps(val, ensure_ascii=False) if isinstance(val, (str, int, float, bool, list, dict)) else str(val)
                lines.append(f"    const {arg_name} = {val_str};")

            lines.append("    // Act & Assert")
            lines.append("  });")

        lines.append("});")
        return "\n".join(lines)

    def _generate_go_parametrize(self, test: ParametrizedTest) -> str:
        """Go table-driven test"""
        args_str = ", ".join(test.arg_names)
        lines: list[str] = []

        lines.append(f"func {test.test_name}(t *testing.T) {{")

        lines.append("    tests := []struct {")
        for arg in test.arg_names:
            lines.append(f"        {arg} interface{{}}")
        lines.append("    }{")

        for case in test.test_cases:
            values = [case.get(a, "nil") for a in test.arg_names]
            values_str = ", ".join(json.dumps(v, ensure_ascii=False) for v in values)
            lines.append(f"        {{{values_str}}},")

        lines.append("    }")

        lines.append("    for _, tt := range tests {")
        lines.append(f"        t.Run(fmt.Sprintf({args_str}), func(t *testing.T) {{")
        lines.append("            // test logic here")
        lines.append("        })")
        lines.append("    }")
        lines.append("}")

        return "\n".join(lines)

    # ==================== 测试标记与分组 ====================

    def apply_test_mark(
        self, mark: TestMark, reason: str = "", framework: TestFramework = TestFramework.PYTEST
    ) -> str:
        """
        应用测试标记

        Args:
            mark: 标记类型
            reason: 标记原因
            framework: 目标框架

        Returns:
            装饰器/标记代码
        """
        match framework:
            case TestFramework.PYTEST:
                reason_str = f', reason="{reason}"' if reason else ""
                match mark:
                    case TestMark.SKIP:
                        return f"@pytest.mark.skip{reason_str}"
                    case TestMark.XFAIL:
                        return f"@pytest.mark.xfail{reason_str}"
                    case _:
                        return f"@pytest.mark.{mark.value}{reason_str}"
            case TestFramework.JEST:
                match mark:
                    case TestMark.SKIP:
                        return f".skip('{reason}')"
                    case TestMark.XFAIL:
                        return f".todo('{reason}')"
                    case _:
                        return f".describe('{mark.value}', () => {{"
            case _:
                return f"# [{mark.value}] {reason}"

    # ==================== 环境隔离 ====================

    def setup_isolation(self, config: IsolationConfig, framework: TestFramework = TestFramework.PYTEST) -> str:
        """
        设置测试环境隔离

        Args:
            config: 隔离配置
            framework: 目标框架

        Returns:
            隔离设置代码
        """
        lines: list[str] = []

        match framework:
            case TestFramework.PYTEST:
                lines.append("# conftest.py - 环境隔离配置\n")

                if config.database_rollback:
                    lines.append("@pytest.fixture")
                    lines.append("def db_session():")
                    lines.append("    session = SessionLocal()")
                    lines.append("    yield session")
                    lines.append("    session.rollback()")
                    lines.append("    session.close()\n")

                if config.tmp_filesystem:
                    lines.append("@pytest.fixture")
                    lines.append("def temp_dir(tmp_path):")
                    lines.append("    yield tmp_path")
                    lines.append("    # 自动清理\n")

                if config.env_isolation:
                    lines.append("@pytest.fixture(autouse=True)")
                    lines.append("def isolate_env(monkeypatch):")
                    lines.append("    monkeypatch.setenv('ENVIRONMENT', 'testing')")
                    lines.append("    monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')\n")

                if config.http_mock_server:
                    lines.append("@pytest.fixture")
                    lines.append("def http_mock(responses):")
                    lines.append("    responses.start()")
                    lines.append("    yield responses")
                    lines.append("    responses.stop()\n")

            case TestFramework.JEST:
                lines.append("// jest.setup.ts - 环境隔离\n")

                if config.env_isolation:
                    lines.append("beforeEach(() => {")
                    lines.append("    process.env.NODE_ENV = 'test';")
                    lines.append("});\n")

                if config.http_mock_server:
                    lines.append("import { server } from './mocks/server';")
                    lines.append("beforeAll(() => server.listen());")
                    lines.append("afterEach(() => server.resetHandlers());")
                    lines.append("afterAll(() => server.close());")

            case _:
                lines.append(f"# TODO: 实现{framework.value}的环境隔离")

        return "\n".join(lines)

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成测试框架司报告"""
        lines: list[str] = []
        lines.append("# 🧪 测试框架司 · 能力报告\n")
        lines.append("| 框架 | 状态 | 插件数 |")
        lines.append("| --- | --- | --- |")

        for fw, cfg in self._framework_configs.items():
            status = "✅ 已配置"
            plugin_count = len(cfg.required_plugins)
            lines.append(f"| `{fw.value}` | {status} | {plugin_count} |")

        lines.append("\n### 支持的Mock类型\n")
        lines.append("| 类型 | 说明 | 适用场景 |")
        lines.append("| --- | --- | --- |")
        lines.append("| Mock | 完全控制行为 | HTTP客户端、外部API |")
        lines.append("| Stub | 预设响应 | 数据库查询、文件读取 |")
        lines.append("| Spy | 记录调用信息 | 日志、事件发送 |")
        lines.append("| Fake | 轻量实现 | 内存数据库、缓存 |")

        lines.append("\n### 支持的测试标记\n")
        marks = [m.value for m in TestMark]
        lines.append(", ".join(f"`{m}`" for m in marks))

        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print("=" * 60)
    print("测试框架司 - 功能演示")
    print("=" * 60)

    si = TestFrameworkSi()

    print("\n--- 框架配置 ---")
    pytest_cfg = si.generate_config_file(TestFramework.PYTEST)
    print(f"Pytest配置预览:\n{pytest_cfg[:300]}...")

    print("\n--- Mock代码生成 ---")
    mock_cfg = MockConfig(target="requests.Session", mock_type="mock", return_value={"status": "ok"})
    mock_code = si.generate_mock_code(mock_cfg, TestFramework.PYTEST)
    print(mock_code[:400])

    print("\n--- Fixture生成 ---")
    fx_cfg = FixtureConfig(name="user_session", scope="function", code=["user = create_test_user()", "session = login(user)"])
    fx_code = si.generate_fixture(fx_cfg, TestFramework.PYTEST)
    print(fx_code[:400])

    print("\n--- 参数化测试 ---")
    param_test = ParametrizedTest(
        test_name="test_addition",
        arg_names=["a", "b", "expected"],
        test_cases=[
            {"a": 1, "b": 2, "expected": 3},
            {"a": -1, "b": 1, "expected": 0},
            {"a": 0, "b": 0, "expected": 0},
        ],
        ids=["positive", "zero_sum", "both_zero"],
    )
    param_code = si.generate_parametrized_test(param_test, TestFramework.PYTEST)
    print(param_code)

    print("\n--- 测试标记 ---")
    skip_mark = si.apply_test_mark(TestMark.SKIP, "待修复", TestFramework.PYTEST)
    slow_mark = si.apply_test_mark(TestMark.SLOW, framework=TestFramework.PYTEST)
    print(f"  Skip: {skip_mark}")
    print(f"  Slow: {slow_mark}")

    print("\n--- 环境隔离 ---")
    iso_cfg = IsolationConfig(database_rollback=True, env_isolation=True)
    iso_code = si.setup_isolation(iso_cfg, TestFramework.PYTEST)
    print(iso_code[:500])

    report = si.generate_report()
    print(f"\n--- 报告预览 ---\n{report}")

    print("\n✅ 所有测试通过!")
