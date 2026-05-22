"""CI Pipeline Orchestrator for Harness CI module integration.

Provides intelligent pipeline orchestration including incremental change detection,
cache optimization, parallel stage scheduling, quality gate embedding, and
multi-platform Pipeline-as-Code generation.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class BuildTool(str, Enum):
    """Supported build tools for CI pipelines."""

    MAVEN = "maven"
    GRADLE = "gradle"
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    PIP = "pip"
    POETRY = "poetry"
    CARGO = "cargo"
    GO = "go"
    DOCKER = "docker"


class CacheStrategy(str, Enum):
    """Cache strategy types for build optimization."""

    DEPENDENCY_CACHE = "dependency_cache"
    LAYER_CACHE = "layer_cache"
    SOURCE_CACHE = "source_cache"
    CUSTOM_CACHE = "custom_cache"


class PlatformType(str, Enum):
    """Supported CI/CD platforms for YAML generation."""

    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    HARNESS_CI = "harness_ci"


@dataclass
class QualityGate:
    """Represents a quality gate configuration in the pipeline.

    Attributes:
        name: Name of the quality gate.
        gate_type: Type of quality check (lint, test, security_scan).
        threshold: Pass/fail threshold (e.g., coverage percentage).
        blocking: Whether this gate blocks the pipeline on failure.
        tool: Tool used for the quality check.
    """

    name: str
    gate_type: str
    threshold: float | None = None
    blocking: bool = True
    tool: str = ""


@dataclass
class ParallelStage:
    """Represents a parallel stage in the pipeline DAG.

    Attributes:
        name: Stage name.
        commands: List of shell commands to execute.
        depends_on: List of stage names this stage depends on.
        timeout_minutes: Stage timeout in minutes.
        condition: Conditional expression for stage execution.
    """

    name: str
    commands: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    timeout_minutes: int = 30
    condition: str = ""


@dataclass
class CIPipelineConfig:
    """Configuration data class for CI Pipeline Orchestrator.

    Attributes:
        project_root: Root directory of the project.
        build_tool: Primary build tool to use.
        cache_strategy: Caching strategy for builds.
        parallel_stages: List of parallel stages with dependencies.
        quality_gates: List of quality gates to enforce.
        platform: Target CI/CD platform for YAML generation.
        docker_registry: Container registry URL if applicable.
        artifact_path: Path where build artifacts are stored.
    """

    project_root: Path
    build_tool: BuildTool = BuildTool.NPM
    cache_strategy: CacheStrategy = CacheStrategy.DEPENDENCY_CACHE
    parallel_stages: list[ParallelStage] = field(default_factory=list)
    quality_gates: list[QualityGate] = field(default_factory=list)
    platform: PlatformType = PlatformType.GITHUB_ACTIONS
    docker_registry: str = ""
    artifact_path: Path | None = None


@dataclass
class IncrementalChange:
    """Represents detected incremental changes from git diff.

    Attributes:
        changed_files: List of changed file paths.
        added_files: List of newly added files.
        deleted_files: List of deleted files.
        modified_modules: Affected modules/packages.
        has_test_changes: Whether test files were modified.
        change_hash: SHA256 hash of the change set.
    """

    changed_files: list[Path] = field(default_factory=list)
    added_files: list[Path] = field(default_factory=list)
    deleted_files: list[Path] = field(default_factory=list)
    modified_modules: list[str] = field(default_factory=list)
    has_test_changes: bool = False
    change_hash: str = ""


@dataclass
class CacheOptimizationResult:
    """Result of cache strategy optimization.

    Attributes:
        recommended_strategy: Recommended cache strategy.
        cache_keys: Computed cache keys for different layers.
        estimated_time_savings: Estimated time savings in seconds.
        invalidation_rules: Rules for cache invalidation.
    """

    recommended_strategy: CacheStrategy
    cache_keys: dict[str, str] = field(default_factory=dict)
    estimated_time_savings: float = 0.0
    invalidation_rules: list[str] = field(default_factory=list)


@dataclass
class PipelineValidationResult:
    """Result of pipeline validation.

    Attributes:
        is_valid: Whether the pipeline configuration is valid.
        errors: List of validation errors.
        warnings: List of validation warnings.
        suggestions: List of improvement suggestions.
    """

    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


class CIPipelineOrchestrator:
    """CI Pipeline Orchestrator for Harness CI integration.

    Provides comprehensive CI pipeline management including incremental build
    detection, intelligent caching, parallel stage execution via DAG analysis,
    quality gate enforcement, and multi-platform Pipeline-as-Code generation.

    Args:
        config: CI pipeline configuration object.
    """

    def __init__(self, config: CIPipelineConfig) -> None:
        self._config = config
        self._project_root = config.project_root.resolve()

    def detect_incremental_changes(
        self, base_ref: str = "main", head_ref: str = "HEAD"
    ) -> IncrementalChange:
        """Detect incremental changes based on git diff analysis.

        Analyzes git diff between two refs to identify changed files,
        affected modules, and compute a deterministic change hash for
        cache key derivation.

        Args:
            base_ref: Base git reference for comparison (default: 'main').
            head_ref: Head git reference for comparison (default: 'HEAD').

        Returns:
            IncrementalChange object containing detailed change information.
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-status", f"{base_ref}...{head_ref}"],
                cwd=str(self._project_root),
                capture_output=True,
                text=True,
                timeout=60,
            )
            diff_output = result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            diff_output = ""

        changed_files: list[Path] = []
        added_files: list[Path] = []
        deleted_files: list[Path] = []

        for line in diff_output.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            status = parts[0][0] if parts else ""
            file_path = parts[-1] if len(parts) > 1 else ""
            full_path = self._project_root / file_path

            match status:
                case "A" | "?":
                    added_files.append(full_path)
                    changed_files.append(full_path)
                case "D":
                    deleted_files.append(full_path)
                    changed_files.append(full_path)
                case _:
                    changed_files.append(full_path)

        modified_modules = self._extract_affected_modules(changed_files)
        has_test_changes = any(
            self._is_test_file(f) for f in changed_files
        )

        change_hash = self._compute_change_hash(changed_files)

        return IncrementalChange(
            changed_files=changed_files,
            added_files=added_files,
            deleted_files=deleted_files,
            modified_modules=modified_modules,
            has_test_changes=has_test_changes,
            change_hash=change_hash,
        )

    def optimize_cache_strategy(self) -> CacheOptimizationResult:
        """Optimize build cache strategy based on project characteristics.

        Analyzes dependency files and project structure to recommend optimal
        caching strategies including dependency caching, layer caching, and
        custom cache key computation.

        Returns:
            CacheOptimizationResult with recommendations and computed cache keys.
        """
        dep_files = self._find_dependency_files()
        lock_files = self._find_lock_files()

        cache_keys: dict[str, str] = {}
        invalidation_rules: list[str] = []

        for dep_file in dep_files + lock_files:
            if dep_file.exists():
                content = dep_file.read_text(encoding="utf-8")
                file_hash = hashlib.sha256(content.encode()).hexdigest()[:12]
                rel_name = dep_file.name
                cache_keys[f"dep-{rel_name}"] = file_hash
                invalidation_rules.append(
                    f"Cache invalidates when {rel_name} content changes"
                )

        source_key = self._compute_source_cache_key()
        cache_keys["source-hash"] = source_key

        estimated_savings = self._estimate_cache_time_savings(dep_files)

        return CacheOptimizationResult(
            recommended_strategy=self._config.cache_strategy,
            cache_keys=cache_keys,
            estimated_time_savings=estimated_savings,
            invalidation_rules=invalidation_rules,
        )

    def schedule_parallel_stages(self) -> list[list[ParallelStage]]:
        """Schedule parallel stages using DAG dependency analysis.

        Analyzes stage dependencies and produces an execution plan that
        maximizes parallelism while respecting dependency constraints.
        Uses topological sort to determine execution levels.

        Returns:
            List of execution levels, each containing parallel stages.
        """
        stages = self._config.parallel_stages
        if not stages:
            return []

        stage_map: dict[str, ParallelStage] = {s.name: s for s in stages}
        in_degree: dict[str, int] = {s.name: 0 for s in stages}
        dependents: dict[str, list[str]] = {s.name: [] for s in stages}

        for stage in stages:
            for dep in stage.depends_on:
                if dep in dependents:
                    dependents[dep].append(stage.name)
                    in_degree[stage.name] += 1

        execution_levels: list[list[ParallelStage]] = []
        available = [name for name, degree in in_degree.items() if degree == 0]
        visited: set[str] = set()

        while available:
            level_stages = [
                stage_map[name] for name in sorted(available) if name not in visited
            ]
            if level_stages:
                execution_levels.append(level_stages)

            next_available: list[str] = []
            for stage_name in available:
                if stage_name in visited:
                    continue
                visited.add(stage_name)
                for dependent in dependents.get(stage_name, []):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_available.append(dependent)
            available = next_available

        unvisited = [s for s in stages if s.name not in visited]
        if unvisited:
            execution_levels.append(unvisited)

        return execution_levels

    def embed_quality_gates(self) -> dict[str, QualityGate]:
        """Embed quality gates into the pipeline configuration.

        Configures lint, test, and security scan gates with appropriate
        thresholds and blocking behavior based on project type.

        Returns:
            Dictionary mapping gate names to their configurations.
        """
        gates: dict[str, QualityGate] = {}

        for gate in self._config.quality_gates:
            gates[gate.name] = gate

        default_gates = self._get_default_quality_gates()
        for name, gate in default_gates.items():
            if name not in gates:
                gates[name] = gate

        return gates

    def generate_pipeline_yaml(self) -> str:
        """Generate Pipeline as Code YAML for the target platform.

        Produces complete pipeline configuration supporting GitHub Actions,
        GitLab CI, Jenkins, or Harness CI formats. Includes all configured
        parallel stages, quality gates, and cache strategies.

        Returns:
            Complete pipeline YAML string.
        """
        platform = self._config.platform
        generators = {
            PlatformType.GITHUB_ACTIONS: self._generate_github_actions_yaml,
            PlatformType.GITLAB_CI: self._generate_gitlab_ci_yaml,
            PlatformType.JENKINS: self._generate_jenkinsfile,
            PlatformType.HARNESS_CI: self._generate_harness_ci_yaml,
        }
        generator = generators.get(platform, self._generate_github_actions_yaml)
        return generator()

    def validate_pipeline(self) -> PipelineValidationResult:
        """Validate the current pipeline configuration.

        Checks for common misconfigurations including circular dependencies
        between stages, missing required fields, incompatible settings, and
        best practice violations.

        Returns:
            PipelineValidationResult with validation status and details.
        """
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        stages = self._config.parallel_stages
        stage_names = {s.name for s in stages}

        circular_deps = self._detect_circular_dependencies(stages)
        if circular_deps:
            errors.append(f"Circular dependencies detected: {circular_deps}")

        for stage in stages:
            for dep in stage.depends_on:
                if dep not in stage_names:
                    warnings.append(
                        f"Stage '{stage.name}' depends on unknown stage '{dep}'"
                    )
            if not stage.commands:
                warnings.append(f"Stage '{stage.name}' has no commands defined")

        if not self._config.quality_gates:
            suggestions.append("Consider adding quality gates for better code quality")

        if self._config.build_tool == BuildTool.DOCKER and not self._config.docker_registry:
            warnings.append("Docker build tool selected but no registry configured")

        is_valid = len(errors) == 0
        return PipelineValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def _find_dependency_files(self) -> list[Path]:
        patterns = {
            BuildTool.NPM: "package.json",
            BuildTool.YARN: "package.json",
            BuildTool.PNPM: "package.json",
            BuildTool.PIP: ["requirements.txt", "pyproject.toml", "setup.py"],
            BuildTool.POETRY: "pyproject.toml",
            BuildTool.MAVEN: "pom.xml",
            BuildTool.GRADLE: ["build.gradle", "build.gradle.kts"],
            BuildTool.GO: "go.mod",
            BuildTool.CARGO: "Cargo.toml",
            BuildTool.DOCKER: "Dockerfile",
        }
        dep_patterns = patterns.get(self._config.build_tool, [])
        if isinstance(dep_patterns, str):
            dep_patterns = [dep_patterns]

        found: list[Path] = []
        for pattern in dep_patterns:
            candidate = self._project_root / pattern
            if candidate.exists():
                found.append(candidate)
        return found

    def _find_lock_files(self) -> list[Path]:
        lock_map = {
            BuildTool.NPM: "package-lock.json",
            BuildTool.YARN: "yarn.lock",
            BuildTool.PNPM: "pnpm-lock.yaml",
            BuildTool.PIP: ["Pipfile.lock", ".pip-tools"],
            BuildTool.POETRY: "poetry.lock",
            BuildTool.MAVEN: None,
            BuildTool.GRADLE: None,
            BuildTool.GO: "go.sum",
            BuildTool.CARGO: "Cargo.lock",
            BuildTool.DOCKER: None,
        }
        lock_pattern = lock_map.get(self._config.build_tool)
        if lock_pattern is None:
            return []
        if isinstance(lock_pattern, str):
            lock_file = self._project_root / lock_pattern
            return [lock_file] if lock_file.exists() else []
        return []

    def _compute_source_cache_key(self) -> str:
        hasher = hashlib.sha256()
        for src_file in self._project_root.rglob("*"):
            if (
                src_file.is_file()
                and not any(p.startswith(".") for p in src_file.parts)
                and src_file.suffix not in {".pyc", ".log"}
            ):
                try:
                    hasher.update(src_file.read_bytes())
                except OSError:
                    pass
        return hasher.hexdigest()[:16]

    def _estimate_cache_time_savings(self, dep_files: list[Path]) -> float:
        base_times = {
            BuildTool.NPM: 120.0,
            BuildTool.MAVEN: 180.0,
            BuildTool.GRADLE: 150.0,
            BuildTool.PIP: 90.0,
            BuildTool.GO: 60.0,
            BuildTool.CARGO: 120.0,
        }
        base = base_times.get(self._config.build_tool, 100.0)
        cache_hit_rate = 0.85 if dep_files else 0.3
        return base * cache_hit_rate

    def _extract_affected_modules(self, files: list[Path]) -> list[str]:
        modules: set[str] = set()
        for f in files:
            try:
                relative = f.relative_to(self._project_root)
                parts = relative.parts
                if len(parts) >= 1:
                    modules.add(parts[0])
            except ValueError:
                pass
        return sorted(modules)

    def _is_test_file(self, file_path: Path) -> bool:
        name = file_path.name.lower()
        return (
            "test" in name
            or "spec" in name
            or file_path.suffix in {".test.js", ".test.py", ".spec.ts"}
        )

    def _compute_change_hash(self, files: list[Path]) -> str:
        hasher = hashlib.sha256()
        for f in sorted(files, key=lambda p: str(p)):
            hasher.update(str(f).encode())
            if f.exists():
                try:
                    stat = f.stat()
                    hasher.update(str(stat.st_mtime).encode())
                    hasher.update(str(stat.st_size).encode())
                except OSError:
                    pass
        return hasher.hexdigest()[:16]

    def _detect_circular_dependencies(
        self, stages: list[ParallelStage]
    ) -> list[str]:
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {s.name: WHITE for s in stages}
        adj: dict[str, list[str]] = {s.name: list(s.depends_on) for s in stages}
        cycle_path: list[str] = []

        def dfs(node: str, path: list[str]) -> bool:
            color[node] = GRAY
            path.append(node)
            for neighbor in adj.get(node, []):
                if neighbor not in color:
                    continue
                if color[neighbor] == GRAY:
                    cycle_start = path.index(neighbor)
                    cycle_path.extend(path[cycle_start:])
                    return True
                if color[neighbor] == WHITE and dfs(neighbor, path):
                    return True
            path.pop()
            color[node] = BLACK
            return False

        for stage in stages:
            if color[stage.name] == WHITE:
                if dfs(stage.name, []):
                    break
        return cycle_path

    def _get_default_quality_gates(self) -> dict[str, QualityGate]:
        tool_defaults = {
            BuildTool.NPM: ("eslint", "prettier"),
            BuildTool.PIP: ("flake8", "black", "pylint"),
            BuildTool.GO: ("golint", "vet"),
            BuildTool.CARGO: ("clippy", "fmt"),
            BuildTool.JAVA_TOOL: ("checkstyle", "spotbugs"),
        }

        lint_tool, fmt_tool = tool_defaults.get(
            self._config.build_tool, ("generic-linter", "generic-formatter")
        )

        return {
            "lint-check": QualityGate(
                name="lint-check",
                gate_type="lint",
                tool=lint_tool,
                blocking=True,
            ),
            "unit-tests": QualityGate(
                name="unit-tests",
                gate_type="test",
                threshold=80.0,
                blocking=True,
            ),
            "security-scan": QualityGate(
                name="security-scan",
                gate_type="security_scan",
                tool="trivy",
                blocking=False,
            ),
        }

    def _generate_github_actions_yaml(self) -> str:
        lines: list[str] = [
            "name: CI Pipeline",
            "",
            "on:",
            "  push:",
            "    branches: [main, develop]",
            "  pull_request:",
            "    branches: [main]",
            "",
            "jobs:",
        ]
        execution_plan = self.schedule_parallel_stages()
        needs_map: dict[str, list[str]] = {}
        for level_idx, level in enumerate(execution_plan):
            for stage in level:
                deps = []
                if level_idx > 0:
                    prev_level = execution_plan[level_idx - 1]
                    deps = [s.name.replace("-", "_") for s in prev_level]
                needs_map[stage.name] = deps

        for level_idx, level in enumerate(execution_plan):
            for stage in level:
                job_name = stage.name.replace("-", "_")
                lines.append(f"  {job_name}:")
                lines.append(f"    runs-on: ubuntu-latest")
                deps = needs_map.get(stage.name, [])
                if deps:
                    lines.append(f"    needs: [{', '.join(deps)}]")
                lines.append(f"    timeout-minutes: {stage.timeout_minutes}")
                if stage.condition:
                    lines.append(f"    if: {stage.condition}")
                lines.append("    steps:")
                lines.append("      - uses: actions/checkout@v4")

                cache_result = self.optimize_cache_strategy()
                if cache_result.cache_keys:
                    lines.append("      - name: Cache dependencies")
                    lines.append(
                        f"        uses: actions/cache@v4"
                    )
                    lines.append("        with:")
                    lines.append(
                        f"          key: ${{{{ runner.os }}}}-{cache_result.recommended_strategy.value}-${{{{ hashFiles('**/*.lock') }}}}"
                    )
                    lines.append(
                        "          restore-keys: |"
                    )
                    for key_name, key_val in cache_result.cache_keys.items():
                        lines.append(f"            {key_name}-{key_val}-")

                for cmd in stage.commands:
                    lines.append(f"      - name: Execute step")
                    lines.append(f"        run: {cmd}")

                lines.append("")

        quality_gates = self.embed_quality_gates()
        for gate_name, gate in quality_gates.items():
            safe_name = gate_name.replace("-", "_")
            lines.append(f"  {safe_name}:")
            lines.append("    runs-on: ubuntu-latest")
            lines.append(f"    steps:")
            lines.append("      - uses: actions/checkout@v4")
            lines.append(f"      - name: {gate.name}")
            if gate.gate_type == "test" and gate.threshold is not None:
                lines.append(
                    f"        run: {gate.tool} --coverage-threshold {gate.threshold}"
                )
            else:
                lines.append(f"        run: {gate.tool}")
            lines.append("")

        return "\n".join(lines)

    def _generate_gitlab_ci_yaml(self) -> str:
        lines: list[str] = [
            "stages:",
            "  - build",
            "  - test",
            "  - deploy",
            "",
            "variables:",
            "  CACHE_STRATEGY: " + self._config.cache_strategy.value,
            "",
        ]

        execution_plan = self.schedule_parallel_stages()
        for level_idx, level in enumerate(execution_plan):
            stage_name = f"parallel_level_{level_idx}"
            for stage in level:
                job_name = stage.name.replace("-", "_").replace(" ", "_").lower()
                lines.append(f"{job_name}:")
                lines.append(f"  stage: {stage_name}")
                lines.append(f"  image: ubuntu:latest")
                lines.append(f"  timeout: {stage.timeout_minutes}m")
                if stage.condition:
                    lines.append(f"  only:")
                    lines.append(f"    variables: [{stage.condition}]")
                lines.append(f"  script:")
                for cmd in stage.commands:
                    lines.append(f"    - {cmd}")
                lines.append("")

        return "\n".join(lines)

    def _generate_jenkinsfile(self) -> str:
        lines: list[str] = [
            "pipeline {",
            "    agent any",
            "",
            "    environment {",
            f"        BUILD_TOOL = '{self._config.build_tool.value}'",
            f"        CACHE_STRATEGY = '{self._config.cache_strategy.value}'",
            "    }",
            "",
            "    stages {",
        ]

        execution_plan = self.schedule_parallel_stages()
        for level_idx, level in enumerate(execution_plan):
            lines.append(f"        stage('Parallel Level {level_idx}') {{")
            lines.append("            parallel {")
            for stage in level:
                safe_name = stage.name.replace("-", " ").title().replace(" ", "")
                lines.append(f"                \"{stage.name}\" {{")
                lines.append(f"                    steps {{")
                lines.append(f"                        echo 'Running {stage.name}'")
                for cmd in stage.commands:
                    lines.append(f"                        sh '{cmd}'")
                lines.append("                    }")
                lines.append("                }")
            lines.append("            }")
            lines.append("        }")

        lines.append("    }")
        lines.append("}")

        return "\n".join(lines)

    def _generate_harness_ci_yaml(self) -> str:
        lines: list[str] = [
            "pipeline:",
            "  name: harness-ci-pipeline",
            "  identifier: harness_ci_pipeline",
            "  projectIdentifier: ${{ project.identifier }}",
            "  orgIdentifier: ${{ org.identifier }}",
            "  tags: {}",
            "  properties:",
            "    ci:",
            "      codebase:",
            "        build: ${{ <+codebase> }}",
            "  stages:",
        ]

        execution_plan = self.schedule_parallel_stages()
        for level_idx, level in enumerate(execution_plan):
            for stage in level:
                identifier = stage.name.lower().replace("-", "_").replace(" ", "_")
                lines.append(f"    - stage:")
                lines.append(f"        name: {stage.name}")
                lines.append(f"        identifier: {identifier}")
                lines.append(f"        type: CI")
                lines.append(f"        spec:")
                lines.append(f"          cloneCodebase: true")
                lines.append(f"          execution:")
                lines.append(f"            steps:")
                for cmd_idx, cmd in enumerate(stage.commands, 1):
                    lines.append(f"              - step:")
                    lines.append(
                        f"                  type: Run"
                    )
                    lines.append(f"                  name: step_{cmd_idx}")
                    lines.append(f"                  identifier: step_{cmd_idx}")
                    lines.append(f"                  spec:")
                    lines.append(f"                    shell: Bash")
                    lines.append(f"                    command: |-")
                    lines.append(f"                      {cmd}")
                lines.append("")

        return "\n".join(lines)
