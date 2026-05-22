#!/usr/bin/env python3
"""
项目类型适配器
自动检测项目类型并配置相应的测试框架和工具链

功能：
- 自动检测项目类型（Python、Node.js、Java、Go、Rust 等）
- 根据项目类型自动配置测试框架
- 根据项目类型自动配置工具链
- 生成项目适配配置

支持的适配：
- Python 项目：pytest、unittest、coverage
- Node.js 项目：jest、vitest、mocha
- Java 项目：junit、maven、gradle
- Go 项目：go test
- Rust 项目：cargo test
"""
import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable


class ProjectType(Enum):
    PYTHON = "python"
    NODEJS = "nodejs"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    UNKNOWN = "unknown"


class TestFramework(Enum):
    PYTEST = "pytest"
    UNITTEST = "unittest"
    JEST = "jest"
    VITEST = "vitest"
    MOCHA = "mocha"
    JUNIT = "junit"
    GO_TEST = "go_test"
    CARGO_TEST = "cargo_test"
    NONE = "none"


class BuildTool(Enum):
    PIP = "pip"
    POETRY = "poetry"
    PDM = "pdm"
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    MAVEN = "maven"
    GRADLE = "gradle"
    GO_MOD = "go_mod"
    CARGO = "cargo"
    NONE = "none"


@dataclass
class TestConfig:
    test_framework: TestFramework
    test_command: str
    coverage_command: Optional[str] = None
    test_directory: str = "tests"
    config_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['test_framework'] = self.test_framework.value
        result['coverage_command'] = self.coverage_command
        return result


@dataclass
class ToolchainConfig:
    build_tool: BuildTool
    build_command: str
    install_command: str
    lint_command: Optional[str] = None
    format_command: Optional[str] = None
    package_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['build_tool'] = self.build_tool.value
        return result


@dataclass
class ProjectAdapterConfig:
    project_type: ProjectType
    project_name: str
    project_root: str
    test_config: TestConfig
    toolchain_config: ToolchainConfig
    detected_files: List[str] = field(default_factory=list)
    custom_rules: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_type": self.project_type.value,
            "project_name": self.project_name,
            "project_root": self.project_root,
            "test_config": self.test_config.to_dict(),
            "toolchain_config": self.toolchain_config.to_dict(),
            "detected_files": self.detected_files,
            "custom_rules": self.custom_rules
        }


PROJECT_SIGNATURES = {
    ProjectType.PYTHON: [
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "Pipfile",
        "poetry.lock",
        "Pipfile.lock",
        "pdm.lock",
        "__init__.py",
    ],
    ProjectType.NODEJS: [
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "node_modules",
    ],
    ProjectType.JAVA: [
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "gradlew",
        "mvnw",
    ],
    ProjectType.GO: [
        "go.mod",
        "go.sum",
        "main.go",
        "go.work",
    ],
    ProjectType.RUST: [
        "Cargo.toml",
        "Cargo.lock",
        "src/main.rs",
        "src/lib.rs",
    ],
}


class ProjectTypeDetector:
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.detected_files: List[str] = []
    
    def detect(self) -> ProjectType:
        self.detected_files = []
        
        if not self.project_path.exists():
            return ProjectType.UNKNOWN
        
        scores: Dict[ProjectType, int] = {pt: 0 for pt in ProjectType}
        
        for project_type, signatures in PROJECT_SIGNATURES.items():
            for sig in signatures:
                sig_path = self.project_path / sig
                if sig_path.exists():
                    scores[project_type] += 1
                    self.detected_files.append(sig)
        
        if scores[ProjectType.PYTHON] > 0:
            return ProjectType.PYTHON
        if scores[ProjectType.NODEJS] > 0:
            return ProjectType.NODEJS
        if scores[ProjectType.JAVA] > 0:
            return ProjectType.JAVA
        if scores[ProjectType.GO] > 0:
            return ProjectType.GO
        if scores[ProjectType.RUST] > 0:
            return ProjectType.RUST
        
        return self._detect_by_file_extensions()
    
    def _detect_by_file_extensions(self) -> ProjectType:
        extensions_count: Dict[str, int] = {}
        
        for item in self.project_path.iterdir():
            if item.is_file():
                ext = item.suffix.lower()
                extensions_count[ext] = extensions_count.get(ext, 0) + 1
        
        if extensions_count.get('.py', 0) > 0:
            return ProjectType.PYTHON
        if extensions_count.get('.js', 0) > 0 or extensions_count.get('.ts', 0) > 0:
            return ProjectType.NODEJS
        if extensions_count.get('.java', 0) > 0:
            return ProjectType.JAVA
        if extensions_count.get('.go', 0) > 0:
            return ProjectType.GO
        if extensions_count.get('.rs', 0) > 0:
            return ProjectType.RUST
        
        return ProjectType.UNKNOWN
    
    def get_project_name(self) -> str:
        return self.project_path.name


class TestFrameworkConfigurator:
    
    PYTHON_FRAMEWORKS = {
        "pytest": TestConfig(
            test_framework=TestFramework.PYTEST,
            test_command="pytest",
            coverage_command="pytest --cov --cov-report=xml",
            test_directory="tests",
            config_file="pytest.ini"
        ),
        "unittest": TestConfig(
            test_framework=TestFramework.UNITTEST,
            test_command="python -m unittest discover",
            coverage_command="coverage run -m unittest discover && coverage report",
            test_directory="tests",
            config_file=None
        ),
    }
    
    NODEJS_FRAMEWORKS = {
        "jest": TestConfig(
            test_framework=TestFramework.JEST,
            test_command="npm test",
            coverage_command="npm test -- --coverage",
            test_directory="__tests__",
            config_file="jest.config.js"
        ),
        "vitest": TestConfig(
            test_framework=TestFramework.VITEST,
            test_command="npx vitest run",
            coverage_command="npx vitest run --coverage",
            test_directory="test",
            config_file="vitest.config.ts"
        ),
        "mocha": TestConfig(
            test_framework=TestFramework.MOCHA,
            test_command="npx mocha",
            coverage_command="npx nyc mocha",
            test_directory="test",
            config_file=".mocharc.js"
        ),
    }
    
    JAVA_FRAMEWORKS = {
        "junit": TestConfig(
            test_framework=TestFramework.JUNIT,
            test_command="mvn test",
            coverage_command="mvn test jacoco:report",
            test_directory="src/test/java",
            config_file="pom.xml"
        ),
    }
    
    GO_FRAMEWORK = TestConfig(
        test_framework=TestFramework.GO_TEST,
        test_command="go test ./...",
        coverage_command="go test -coverprofile=coverage.out ./... && go tool cover -html=coverage.out",
        test_directory=".",
        config_file=None
    )
    
    RUST_FRAMEWORK = TestConfig(
        test_framework=TestFramework.CARGO_TEST,
        test_command="cargo test",
        coverage_command="cargo tarpaulin --out Xml",
        test_directory="tests",
        config_file="Cargo.toml"
    )
    
    NONE_CONFIG = TestConfig(
        test_framework=TestFramework.NONE,
        test_command="",
        test_directory="tests",
        config_file=None
    )
    
    def configure(self, project_type: ProjectType, project_path: Path) -> TestConfig:
        if project_type == ProjectType.PYTHON:
            return self._configure_python(project_path)
        elif project_type == ProjectType.NODEJS:
            return self._configure_nodejs(project_path)
        elif project_type == ProjectType.JAVA:
            return self._configure_java(project_path)
        elif project_type == ProjectType.GO:
            return self.GO_FRAMEWORK
        elif project_type == ProjectType.RUST:
            return self.RUST_FRAMEWORK
        else:
            return self.NONE_CONFIG
    
    def _configure_python(self, project_path: Path) -> TestConfig:
        pyproject = project_path / "pyproject.toml"
        pytest_ini = project_path / "pytest.ini"
        setup_cfg = project_path / "setup.cfg"
        
        if pytest_ini.exists():
            return self.PYTHON_FRAMEWORKS["pytest"]
        
        if pyproject.exists():
            content = pyproject.read_text(encoding='utf-8')
            if '[tool.pytest' in content or 'pytest' in content:
                return self.PYTHON_FRAMEWORKS["pytest"]
            if '[tool.unittest' in content or 'unittest' in content:
                return self.PYTHON_FRAMEWORKS["unittest"]
        
        if setup_cfg.exists():
            content = setup_cfg.read_text(encoding='utf-8')
            if '[tool:pytest]' in content:
                return self.PYTHON_FRAMEWORKS["pytest"]
        
        tests_dir = project_path / "tests"
        test_dir = project_path / "test"
        
        if tests_dir.exists():
            test_files = list(tests_dir.glob("test_*.py")) + list(tests_dir.glob("*_test.py"))
            if test_files:
                return self.PYTHON_FRAMEWORKS["pytest"]
        
        return self.PYTHON_FRAMEWORKS["pytest"]
    
    def _configure_nodejs(self, project_path: Path) -> TestConfig:
        package_json = project_path / "package.json"
        
        if package_json.exists():
            try:
                content = json.loads(package_json.read_text(encoding='utf-8'))
                
                dev_deps = content.get('devDependencies', {})
                deps = content.get('dependencies', {})
                all_deps = {**deps, **dev_deps}
                
                if 'vitest' in all_deps:
                    return self.NODEJS_FRAMEWORKS["vitest"]
                if 'jest' in all_deps:
                    return self.NODEJS_FRAMEWORKS["jest"]
                if 'mocha' in all_deps:
                    return self.NODEJS_FRAMEWORKS["mocha"]
                
                scripts = content.get('scripts', {})
                test_script = scripts.get('test', '')
                
                if 'vitest' in test_script:
                    return self.NODEJS_FRAMEWORKS["vitest"]
                if 'jest' in test_script:
                    return self.NODEJS_FRAMEWORKS["jest"]
                if 'mocha' in test_script:
                    return self.NODEJS_FRAMEWORKS["mocha"]
                
            except json.JSONDecodeError:
                pass
        
        vitest_config = project_path / "vitest.config.ts"
        if vitest_config.exists():
            return self.NODEJS_FRAMEWORKS["vitest"]
        
        jest_config = project_path / "jest.config.js"
        if jest_config.exists():
            return self.NODEJS_FRAMEWORKS["jest"]
        
        return self.NODEJS_FRAMEWORKS["jest"]
    
    def _configure_java(self, project_path: Path) -> TestConfig:
        pom_xml = project_path / "pom.xml"
        build_gradle = project_path / "build.gradle"
        build_gradle_kts = project_path / "build.gradle.kts"
        
        config = TestConfig(
            test_framework=TestFramework.JUNIT,
            test_command="mvn test",
            coverage_command="mvn test jacoco:report",
            test_directory="src/test/java",
            config_file="pom.xml"
        )
        
        if pom_xml.exists():
            content = pom_xml.read_text(encoding='utf-8')
            if 'junit' in content.lower():
                config.config_file = "pom.xml"
                config.test_command = "mvn test"
                config.coverage_command = "mvn test jacoco:report"
            return config
        
        if build_gradle.exists() or build_gradle_kts.exists():
            config.test_command = "./gradlew test"
            config.coverage_command = "./gradlew test jacocoTestReport"
            config.config_file = "build.gradle"
            return config
        
        return config


class ToolchainConfigurator:
    
    PYTHON_TOOLCHAINS = {
        "poetry": ToolchainConfig(
            build_tool=BuildTool.POETRY,
            build_command="poetry build",
            install_command="poetry install",
            lint_command="poetry run ruff check .",
            format_command="poetry run ruff format .",
            package_file="pyproject.toml"
        ),
        "pdm": ToolchainConfig(
            build_tool=BuildTool.PDM,
            build_command="pdm build",
            install_command="pdm install",
            lint_command="pdm run ruff check .",
            format_command="pdm run ruff format .",
            package_file="pyproject.toml"
        ),
        "pip": ToolchainConfig(
            build_tool=BuildTool.PIP,
            build_command="python -m build",
            install_command="pip install -r requirements.txt",
            lint_command="ruff check .",
            format_command="ruff format .",
            package_file="requirements.txt"
        ),
    }
    
    NODEJS_TOOLCHAINS = {
        "npm": ToolchainConfig(
            build_tool=BuildTool.NPM,
            build_command="npm run build",
            install_command="npm install",
            lint_command="npm run lint",
            format_command="npm run format",
            package_file="package.json"
        ),
        "yarn": ToolchainConfig(
            build_tool=BuildTool.YARN,
            build_command="yarn build",
            install_command="yarn install",
            lint_command="yarn lint",
            format_command="yarn format",
            package_file="package.json"
        ),
        "pnpm": ToolchainConfig(
            build_tool=BuildTool.PNPM,
            build_command="pnpm build",
            install_command="pnpm install",
            lint_command="pnpm lint",
            format_command="pnpm format",
            package_file="package.json"
        ),
    }
    
    JAVA_TOOLCHAINS = {
        "maven": ToolchainConfig(
            build_tool=BuildTool.MAVEN,
            build_command="mvn package",
            install_command="mvn install",
            lint_command="mvn checkstyle:check",
            format_command="mvn spotless:apply",
            package_file="pom.xml"
        ),
        "gradle": ToolchainConfig(
            build_tool=BuildTool.GRADLE,
            build_command="./gradlew build",
            install_command="./gradlew assemble",
            lint_command="./gradlew checkstyleMain",
            format_command="./gradlew spotlessApply",
            package_file="build.gradle"
        ),
    }
    
    GO_TOOLCHAIN = ToolchainConfig(
        build_tool=BuildTool.GO_MOD,
        build_command="go build ./...",
        install_command="go mod download",
        lint_command="golangci-lint run",
        format_command="go fmt ./...",
        package_file="go.mod"
    )
    
    RUST_TOOLCHAIN = ToolchainConfig(
        build_tool=BuildTool.CARGO,
        build_command="cargo build",
        install_command="cargo build --release",
        lint_command="cargo clippy",
        format_command="cargo fmt",
        package_file="Cargo.toml"
    )
    
    NONE_TOOLCHAIN = ToolchainConfig(
        build_tool=BuildTool.NONE,
        build_command="",
        install_command="",
        package_file=None
    )
    
    def configure(self, project_type: ProjectType, project_path: Path) -> ToolchainConfig:
        if project_type == ProjectType.PYTHON:
            return self._configure_python(project_path)
        elif project_type == ProjectType.NODEJS:
            return self._configure_nodejs(project_path)
        elif project_type == ProjectType.JAVA:
            return self._configure_java(project_path)
        elif project_type == ProjectType.GO:
            return self.GO_TOOLCHAIN
        elif project_type == ProjectType.RUST:
            return self.RUST_TOOLCHAIN
        else:
            return self.NONE_TOOLCHAIN
    
    def _configure_python(self, project_path: Path) -> ToolchainConfig:
        poetry_lock = project_path / "poetry.lock"
        pdm_lock = project_path / "pdm.lock"
        pyproject = project_path / "pyproject.toml"
        pipfile = project_path / "Pipfile"
        requirements = project_path / "requirements.txt"
        
        if poetry_lock.exists():
            return self.PYTHON_TOOLCHAINS["poetry"]
        
        if pdm_lock.exists():
            return self.PYTHON_TOOLCHAINS["pdm"]
        
        if pyproject.exists():
            content = pyproject.read_text(encoding='utf-8')
            if '[tool.poetry]' in content:
                return self.PYTHON_TOOLCHAINS["poetry"]
            if '[project]' in content and 'pdm' in content.lower():
                return self.PYTHON_TOOLCHAINS["pdm"]
        
        if pipfile.exists():
            return self.PYTHON_TOOLCHAINS["pip"]
        
        if requirements.exists():
            return self.PYTHON_TOOLCHAINS["pip"]
        
        return self.PYTHON_TOOLCHAINS["pip"]
    
    def _configure_nodejs(self, project_path: Path) -> ToolchainConfig:
        yarn_lock = project_path / "yarn.lock"
        pnpm_lock = project_path / "pnpm-lock.yaml"
        package_lock = project_path / "package-lock.json"
        
        if yarn_lock.exists():
            return self.NODEJS_TOOLCHAINS["yarn"]
        
        if pnpm_lock.exists():
            return self.NODEJS_TOOLCHAINS["pnpm"]
        
        if package_lock.exists():
            return self.NODEJS_TOOLCHAINS["npm"]
        
        return self.NODEJS_TOOLCHAINS["npm"]
    
    def _configure_java(self, project_path: Path) -> ToolchainConfig:
        gradlew = project_path / "gradlew"
        gradlew_bat = project_path / "gradlew.bat"
        build_gradle = project_path / "build.gradle"
        build_gradle_kts = project_path / "build.gradle.kts"
        pom_xml = project_path / "pom.xml"
        
        if gradlew.exists() or gradlew_bat.exists() or build_gradle.exists() or build_gradle_kts.exists():
            return self.JAVA_TOOLCHAINS["gradle"]
        
        if pom_xml.exists():
            return self.JAVA_TOOLCHAINS["maven"]
        
        return self.JAVA_TOOLCHAINS["maven"]


class ProjectTypeAdapter:
    
    def __init__(self, project_path: str, custom_rules: Optional[Dict[str, Any]] = None):
        self.project_path = Path(project_path).resolve()
        self.custom_rules = custom_rules or {}
        
        self.detector = ProjectTypeDetector(project_path)
        self.test_configurator = TestFrameworkConfigurator()
        self.toolchain_configurator = ToolchainConfigurator()
    
    def adapt(self) -> ProjectAdapterConfig:
        project_type = self.detector.detect()
        project_name = self.detector.get_project_name()
        
        test_config = self.test_configurator.configure(project_type, self.project_path)
        toolchain_config = self.toolchain_configurator.configure(project_type, self.project_path)
        
        if self.custom_rules:
            test_config = self._apply_custom_test_rules(test_config)
            toolchain_config = self._apply_custom_toolchain_rules(toolchain_config)
        
        return ProjectAdapterConfig(
            project_type=project_type,
            project_name=project_name,
            project_root=str(self.project_path),
            test_config=test_config,
            toolchain_config=toolchain_config,
            detected_files=self.detector.detected_files,
            custom_rules=self.custom_rules
        )
    
    def _apply_custom_test_rules(self, test_config: TestConfig) -> TestConfig:
        if 'test_framework' in self.custom_rules:
            framework = self.custom_rules['test_framework']
            if framework in TestFramework.__members__:
                test_config.test_framework = TestFramework(framework)
        
        if 'test_command' in self.custom_rules:
            test_config.test_command = self.custom_rules['test_command']
        
        if 'coverage_command' in self.custom_rules:
            test_config.coverage_command = self.custom_rules['coverage_command']
        
        if 'test_directory' in self.custom_rules:
            test_config.test_directory = self.custom_rules['test_directory']
        
        return test_config
    
    def _apply_custom_toolchain_rules(self, toolchain_config: ToolchainConfig) -> ToolchainConfig:
        if 'build_tool' in self.custom_rules:
            tool = self.custom_rules['build_tool']
            if tool in BuildTool.__members__:
                toolchain_config.build_tool = BuildTool(tool)
        
        if 'build_command' in self.custom_rules:
            toolchain_config.build_command = self.custom_rules['build_command']
        
        if 'install_command' in self.custom_rules:
            toolchain_config.install_command = self.custom_rules['install_command']
        
        if 'lint_command' in self.custom_rules:
            toolchain_config.lint_command = self.custom_rules['lint_command']
        
        if 'format_command' in self.custom_rules:
            toolchain_config.format_command = self.custom_rules['format_command']
        
        return toolchain_config
    
    def save_config(self, output_path: str) -> bool:
        try:
            config = self.adapt()
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"保存配置失败: {e}", file=sys.stderr)
            return False


def print_config(config: ProjectAdapterConfig, verbose: bool = False) -> None:
    print("\n" + "=" * 60)
    print("项目类型适配配置")
    print("=" * 60)
    print(f"项目名称: {config.project_name}")
    print(f"项目路径: {config.project_root}")
    print(f"项目类型: {config.project_type.value}")
    
    print("-" * 60)
    print("测试配置:")
    print(f"  测试框架: {config.test_config.test_framework.value}")
    print(f"  测试命令: {config.test_config.test_command}")
    if config.test_config.coverage_command:
        print(f"  覆盖率命令: {config.test_config.coverage_command}")
    print(f"  测试目录: {config.test_config.test_directory}")
    if config.test_config.config_file:
        print(f"  配置文件: {config.test_config.config_file}")
    
    print("-" * 60)
    print("工具链配置:")
    print(f"  构建工具: {config.toolchain_config.build_tool.value}")
    print(f"  构建命令: {config.toolchain_config.build_command}")
    print(f"  安装命令: {config.toolchain_config.install_command}")
    if config.toolchain_config.lint_command:
        print(f"  Lint 命令: {config.toolchain_config.lint_command}")
    if config.toolchain_config.format_command:
        print(f"  格式化命令: {config.toolchain_config.format_command}")
    
    if verbose and config.detected_files:
        print("-" * 60)
        print("检测到的文件:")
        for f in config.detected_files:
            print(f"  - {f}")
    
    if verbose and config.custom_rules:
        print("-" * 60)
        print("自定义规则:")
        for key, value in config.custom_rules.items():
            print(f"  {key}: {value}")
    
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="项目类型适配器 - 自动检测项目类型并配置测试框架和工具链",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python project_type_adapter.py /path/to/project
  python project_type_adapter.py . --json
  python project_type_adapter.py . --output adapter_config.json
  python project_type_adapter.py . --custom-test-framework pytest
  python project_type_adapter.py . --custom-build-tool poetry
        """
    )
    
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="项目路径 (默认: 当前目录)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON 格式"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="输出配置文件路径"
    )
    parser.add_argument(
        "--custom-test-framework",
        type=str,
        choices=["pytest", "unittest", "jest", "vitest", "mocha", "junit", "go_test", "cargo_test"],
        help="自定义测试框架"
    )
    parser.add_argument(
        "--custom-build-tool",
        type=str,
        choices=["pip", "poetry", "pdm", "npm", "yarn", "pnpm", "maven", "gradle", "go_mod", "cargo"],
        help="自定义构建工具"
    )
    parser.add_argument(
        "--custom-test-command",
        type=str,
        help="自定义测试命令"
    )
    parser.add_argument(
        "--custom-build-command",
        type=str,
        help="自定义构建命令"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    custom_rules: Dict[str, Any] = {}
    if args.custom_test_framework:
        custom_rules['test_framework'] = args.custom_test_framework
    if args.custom_build_tool:
        custom_rules['build_tool'] = args.custom_build_tool
    if args.custom_test_command:
        custom_rules['test_command'] = args.custom_test_command
    if args.custom_build_command:
        custom_rules['build_command'] = args.custom_build_command
    
    adapter = ProjectTypeAdapter(args.path, custom_rules if custom_rules else None)
    config = adapter.adapt()
    
    if args.json:
        print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
    else:
        print_config(config, verbose=args.verbose)
    
    if args.output:
        if adapter.save_config(args.output):
            print(f"\n配置已保存到: {args.output}")
        else:
            print(f"\n保存配置失败", file=sys.stderr)
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
