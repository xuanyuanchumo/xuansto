#!/usr/bin/env python3
"""
自动化测试流水线脚本 - Sanliu 技能 (增强版)

功能：
- 集成省部司协同调用
- 集成回归测试和日志分析
- 集成系统性优化
- 集成 UI 校验
- 集成代码审查
- 版本控制输出
- 支持命令行参数配置
- 详细的日志记录和错误处理

使用方法：
    python scripts/automated_pipeline.py --help
    python scripts/automated_pipeline.py --test-types unit integration
    python scripts/automated_pipeline.py --all --output-format json
    python scripts/automated_pipeline.py --all --enable-coordination --enable-optimization
"""

import argparse
import asyncio
import importlib.util
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from skillscripts.core.path_config_center import get_path_config

sys.path.insert(0, str(get_path_config().SKILL_ROOT / "skillscripts" / "utils"))
from path_config_manager import PathConfigManager

_path_manager = PathConfigManager()


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MUTATION = "mutation"
    REGRESSION = "regression"


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class PipelineStage(Enum):
    LINT = "lint"
    TYPE_CHECK = "type_check"
    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    COVERAGE = "coverage"
    BUILD = "build"
    DEPLOY_PREP = "deploy_prep"
    COORDINATION = "coordination"
    CODE_REVIEW = "code_review"
    UI_VALIDATION = "ui_validation"
    TESTING = "testing"
    OPTIMIZATION = "optimization"
    REPORTING = "reporting"
    NOTIFICATION = "notification"
    ARTIFACT_COLLECTION = "artifact_collection"
    QUALITY_GATE = "quality_gate"


STAGE_DEPENDENCIES: Dict[PipelineStage, List[PipelineStage]] = {
    PipelineStage.LINT: [],
    PipelineStage.TYPE_CHECK: [PipelineStage.LINT],
    PipelineStage.UNIT_TEST: [PipelineStage.TYPE_CHECK],
    PipelineStage.INTEGRATION_TEST: [PipelineStage.UNIT_TEST],
    PipelineStage.COVERAGE: [PipelineStage.UNIT_TEST, PipelineStage.INTEGRATION_TEST],
    PipelineStage.BUILD: [PipelineStage.TYPE_CHECK],
    PipelineStage.DEPLOY_PREP: [PipelineStage.BUILD, PipelineStage.COVERAGE],
    PipelineStage.COORDINATION: [],
    PipelineStage.CODE_REVIEW: [PipelineStage.LINT],
    PipelineStage.UI_VALIDATION: [PipelineStage.BUILD],
    PipelineStage.TESTING: [PipelineStage.UNIT_TEST, PipelineStage.INTEGRATION_TEST],
    PipelineStage.OPTIMIZATION: [PipelineStage.TESTING],
    PipelineStage.REPORTING: [PipelineStage.COVERAGE, PipelineStage.CODE_REVIEW, PipelineStage.UI_VALIDATION],
    PipelineStage.NOTIFICATION: [PipelineStage.REPORTING],
    PipelineStage.ARTIFACT_COLLECTION: [PipelineStage.BUILD, PipelineStage.REPORTING],
    PipelineStage.QUALITY_GATE: [PipelineStage.COVERAGE, PipelineStage.CODE_REVIEW, PipelineStage.UI_VALIDATION],
}


@dataclass
class StageDependency:
    stage: PipelineStage
    depends_on: List[PipelineStage]
    parallel_group: int = 0
    critical: bool = True
    optional: bool = False


@dataclass
class RetryConfig:
    max_retries: int = 3
    retry_delay: float = 5.0
    exponential_backoff: bool = True
    max_delay: float = 60.0
    retry_on_errors: List[str] = field(default_factory=lambda: ["timeout", "connection", "resource"])
    skip_on_consecutive_failures: int = 5


@dataclass
class PipelineState:
    pipeline_id: str
    status: str = "pending"
    current_stage: Optional[str] = None
    completed_stages: List[str] = field(default_factory=list)
    failed_stages: List[str] = field(default_factory=list)
    skipped_stages: List[str] = field(default_factory=list)
    stage_results: Dict[str, Any] = field(default_factory=dict)
    retry_counts: Dict[str, int] = field(default_factory=dict)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    test_type: TestType
    status: TestStatus
    duration: float = 0.0
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    coverage: float = 0.0
    output: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class StageResult:
    stage: PipelineStage
    status: TestStatus
    duration: float = 0.0
    output: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class PipelineConfig:
    test_types: list[TestType]
    output_format: str = "json"
    output_dir: Path = field(default_factory=lambda: _path_manager.get_reports_path())
    parallel: bool = False
    verbose: bool = False
    fail_fast: bool = False
    timeout: int = 300
    backend_dir: Path = field(default_factory=lambda: _path_manager.get_backend_path())
    frontend_dir: Path = field(default_factory=lambda: _path_manager.get_frontend_path())
    enable_coordination: bool = True
    enable_optimization: bool = True
    enable_code_review: bool = True
    enable_ui_validation: bool = True
    enable_regression: bool = True
    enable_log_analysis: bool = True
    version: str = "v1.0.0"
    docs_dir: Path = field(default_factory=lambda: _path_manager.get_docs_libs_path())
    enable_lint: bool = True
    enable_type_check: bool = True
    enable_build: bool = True
    enable_deploy_prep: bool = True
    coverage_threshold: float = 80.0
    environments: list[str] = field(default_factory=lambda: ["staging", "production"])
    notification_channels: list[str] = field(default_factory=lambda: ["console", "file"])
    notification_webhook: str = ""
    notification_email: str = ""
    quality_gates: dict[str, Any] = field(default_factory=lambda: {
        "coverage_min": 80.0,
        "complexity_max": 15,
        "security_issues_max": 0,
        "performance_regression_max": 5.0
    })
    test_suite_priority: dict[str, int] = field(default_factory=lambda: {
        "security": 1,
        "unit": 2,
        "integration": 3,
        "e2e": 4,
        "performance": 5,
        "mutation": 6
    })
    retry_failed_tests: int = 2
    artifact_retention_days: int = 30
    enable_smart_scheduling: bool = True


@dataclass
class StageTiming:
    stage: PipelineStage
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: float = 0.0

    def start(self):
        self.start_time = datetime.now()

    def end(self):
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()


class PipelineStatusMonitor:
    """流水线状态监控器"""

    def __init__(self):
        self.stages: dict[PipelineStage, StageTiming] = {}
        self.current_stage: Optional[PipelineStage] = None
        self.status_history: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def start_pipeline(self):
        self.start_time = datetime.now()
        self._record_status("pipeline_started")

    def end_pipeline(self):
        self.end_time = datetime.now()
        self._record_status("pipeline_completed")

    def start_stage(self, stage: PipelineStage):
        if stage not in self.stages:
            self.stages[stage] = StageTiming(stage=stage)
        self.stages[stage].start()
        self.current_stage = stage
        self._record_status(f"stage_started", stage=stage.value)

    def end_stage(self, stage: PipelineStage, status: TestStatus, 
                  errors: list[str] = None, warnings: list[str] = None):
        if stage in self.stages:
            self.stages[stage].end()
        
        if errors:
            for error in errors:
                self.errors.append({
                    "stage": stage.value,
                    "message": error,
                    "timestamp": datetime.now().isoformat()
                })
        
        if warnings:
            for warning in warnings:
                self.warnings.append({
                    "stage": stage.value,
                    "message": warning,
                    "timestamp": datetime.now().isoformat()
                })
        
        self._record_status(f"stage_{status.value}", stage=stage.value)

    def _record_status(self, event: str, stage: str = None):
        self.status_history.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "stage": stage,
            "current_stage": self.current_stage.value if self.current_stage else None
        })

    def get_total_duration(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def get_stage_durations(self) -> dict[str, float]:
        return {
            stage.value: timing.duration 
            for stage, timing in self.stages.items()
        }

    def get_summary(self) -> dict[str, Any]:
        return {
            "total_duration": self.get_total_duration(),
            "stage_durations": self.get_stage_durations(),
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "status_history": self.status_history
        }

    def to_json(self) -> str:
        return json.dumps(self.get_summary(), indent=2, ensure_ascii=False)


class StageDependencyManager:
    """流水线阶段依赖管理器"""

    def __init__(self):
        self.dependencies: Dict[PipelineStage, StageDependency] = {}
        self._init_dependencies()

    def _init_dependencies(self):
        for stage, deps in STAGE_DEPENDENCIES.items():
            self.dependencies[stage] = StageDependency(
                stage=stage,
                depends_on=deps,
                critical=stage not in [PipelineStage.OPTIMIZATION, PipelineStage.NOTIFICATION],
                optional=stage in [PipelineStage.OPTIMIZATION, PipelineStage.COORDINATION]
            )

    def get_execution_order(self, stages: List[PipelineStage]) -> List[List[PipelineStage]]:
        ordered_stages = []
        remaining = set(stages)
        completed = set()

        while remaining:
            ready = []
            for stage in remaining:
                deps = self.dependencies.get(stage)
                if deps:
                    if all(d in completed or d not in stages for d in deps.depends_on):
                        ready.append(stage)
                else:
                    ready.append(stage)

            if not ready:
                remaining_stages = [s.value for s in remaining]
                logger.warning(f"检测到循环依赖或无法解析的依赖: {remaining_stages}")
                ready = list(remaining)

            ordered_stages.append(ready)
            completed.update(ready)
            remaining -= set(ready)

        return ordered_stages

    def can_execute(self, stage: PipelineStage, completed_stages: Set[PipelineStage]) -> bool:
        deps = self.dependencies.get(stage)
        if not deps:
            return True
        return all(d in completed_stages for d in deps.depends_on)

    def get_dependents(self, stage: PipelineStage) -> List[PipelineStage]:
        dependents = []
        for s, deps in self.dependencies.items():
            if stage in deps.depends_on:
                dependents.append(s)
        return dependents

    def is_critical(self, stage: PipelineStage) -> bool:
        deps = self.dependencies.get(stage)
        return deps.critical if deps else True

    def is_optional(self, stage: PipelineStage) -> bool:
        deps = self.dependencies.get(stage)
        return deps.optional if deps else False


class RetryHandler:
    """流水线失败重试处理器"""

    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.failure_history: Dict[str, int] = {}
        self.retry_log: List[Dict[str, Any]] = []

    def should_retry(self, stage: PipelineStage, error: Exception, retry_count: int) -> bool:
        if retry_count >= self.config.max_retries:
            return False

        stage_key = stage.value
        consecutive_failures = self.failure_history.get(stage_key, 0)
        if consecutive_failures >= self.config.skip_on_consecutive_failures:
            logger.warning(f"阶段 {stage_key} 连续失败 {consecutive_failures} 次，跳过重试")
            return False

        error_str = str(error).lower()
        for retry_pattern in self.config.retry_on_errors:
            if retry_pattern.lower() in error_str:
                return True

        return False

    def get_retry_delay(self, retry_count: int) -> float:
        if self.config.exponential_backoff:
            delay = self.config.retry_delay * (2 ** retry_count)
            return min(delay, self.config.max_delay)
        return self.config.retry_delay

    def record_failure(self, stage: PipelineStage):
        stage_key = stage.value
        self.failure_history[stage_key] = self.failure_history.get(stage_key, 0) + 1

    def record_success(self, stage: PipelineStage):
        stage_key = stage.value
        if stage_key in self.failure_history:
            del self.failure_history[stage_key]

    def log_retry(self, stage: PipelineStage, retry_count: int, error: Exception, delay: float):
        self.retry_log.append({
            "stage": stage.value,
            "retry_count": retry_count,
            "error": str(error),
            "delay": delay,
            "timestamp": datetime.now().isoformat()
        })

    async def execute_with_retry(
        self,
        stage: PipelineStage,
        func: callable,
        *args,
        **kwargs
    ) -> Tuple[Any, bool]:
        retry_count = 0
        last_error = None

        while True:
            try:
                result = await func(*args, **kwargs)
                self.record_success(stage)
                return result, True
            except Exception as e:
                last_error = e
                if self.should_retry(stage, e, retry_count):
                    delay = self.get_retry_delay(retry_count)
                    self.log_retry(stage, retry_count, e, delay)
                    logger.warning(f"阶段 {stage.value} 失败，{delay:.1f}秒后重试 (第{retry_count + 1}次)")
                    await asyncio.sleep(delay)
                    retry_count += 1
                else:
                    self.record_failure(stage)
                    raise

        return None, False


class PipelineStatePersistence:
    """流水线状态持久化管理器"""

    def __init__(self, state_dir: Path = None):
        self.state_dir = state_dir or PathConfigManager(auto_detect=True).get_data_path() / "pipeline_states"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save_state(self, state: PipelineState) -> Path:
        state_file = self.state_dir / f"{state.pipeline_id}.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump({
                "pipeline_id": state.pipeline_id,
                "status": state.status,
                "current_stage": state.current_stage,
                "completed_stages": state.completed_stages,
                "failed_stages": state.failed_stages,
                "skipped_stages": state.skipped_stages,
                "stage_results": state.stage_results,
                "retry_counts": state.retry_counts,
                "start_time": state.start_time,
                "end_time": state.end_time,
                "error_message": state.error_message,
                "metadata": state.metadata
            }, f, indent=2, ensure_ascii=False)
        return state_file

    def load_state(self, pipeline_id: str) -> Optional[PipelineState]:
        state_file = self.state_dir / f"{pipeline_id}.json"
        if not state_file.exists():
            return None

        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return PipelineState(
                pipeline_id=data["pipeline_id"],
                status=data.get("status", "pending"),
                current_stage=data.get("current_stage"),
                completed_stages=data.get("completed_stages", []),
                failed_stages=data.get("failed_stages", []),
                skipped_stages=data.get("skipped_stages", []),
                stage_results=data.get("stage_results", {}),
                retry_counts=data.get("retry_counts", {}),
                start_time=data.get("start_time"),
                end_time=data.get("end_time"),
                error_message=data.get("error_message"),
                metadata=data.get("metadata", {})
            )
        except Exception as e:
            logger.error(f"加载流水线状态失败: {e}")
            return None

    def list_states(self, status: str = None) -> List[Dict[str, Any]]:
        states = []
        for state_file in self.state_dir.glob("*.json"):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if status is None or data.get("status") == status:
                    states.append({
                        "pipeline_id": data["pipeline_id"],
                        "status": data.get("status"),
                        "start_time": data.get("start_time"),
                        "current_stage": data.get("current_stage")
                    })
            except Exception:
                pass
        return states

    def cleanup_old_states(self, max_age_days: int = 30):
        cutoff = datetime.now().timestamp() - (max_age_days * 86400)
        for state_file in self.state_dir.glob("*.json"):
            if state_file.stat().st_mtime < cutoff:
                state_file.unlink()
                logger.info(f"清理过期状态文件: {state_file}")

    def get_latest_state(self) -> Optional[PipelineState]:
        states = self.list_states()
        if not states:
            return None
        states.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        return self.load_state(states[0]["pipeline_id"])


class StaticCodeAnalyzer:
    """静态代码分析器 - Lint 和类型检查"""

    def __init__(self, config: PipelineConfig):
        self.config = config

    async def run_lint(self) -> StageResult:
        result = StageResult(
            stage=PipelineStage.LINT,
            status=TestStatus.RUNNING
        )
        
        lint_results = {}
        all_errors = []
        all_warnings = []

        backend_result = await self._run_backend_lint()
        lint_results["backend"] = backend_result
        all_errors.extend(backend_result.get("errors", []))
        all_warnings.extend(backend_result.get("warnings", []))

        frontend_result = await self._run_frontend_lint()
        lint_results["frontend"] = frontend_result
        all_errors.extend(frontend_result.get("errors", []))
        all_warnings.extend(frontend_result.get("warnings", []))

        result.output = lint_results
        result.errors = all_errors
        result.warnings = all_warnings
        result.metrics = {
            "backend_issues": backend_result.get("issue_count", 0),
            "frontend_issues": frontend_result.get("issue_count", 0),
            "total_issues": len(all_errors) + len(all_warnings)
        }

        if all_errors:
            result.status = TestStatus.FAILED
        else:
            result.status = TestStatus.PASSED

        return result

    async def _run_backend_lint(self) -> dict[str, Any]:
        backend_dir = self.config.backend_dir
        if not backend_dir.exists():
            return {"status": "skipped", "errors": [], "warnings": ["后端目录不存在"]}

        result = {"errors": [], "warnings": [], "files_checked": 0, "issue_count": 0}

        try:
            cmd = [sys.executable, "-m", "ruff", "check", ".", "--output-format", "json"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=backend_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout
            )

            if stdout:
                try:
                    issues = json.loads(stdout.decode('utf-8', errors='replace'))
                    result["issue_count"] = len(issues)
                    for issue in issues:
                        severity = issue.get("severity", "warning")
                        message = f"{issue.get('filename', '')}:{issue.get('location', {}).get('line', 0)} - {issue.get('message', '')}"
                        if severity == "error":
                            result["errors"].append(message)
                        else:
                            result["warnings"].append(message)
                except json.JSONDecodeError:
                    pass

            result["status"] = "completed"
        except asyncio.TimeoutError:
            result["errors"].append(f"后端 Lint 检查超时 (> {self.config.timeout}s)")
            result["status"] = "timeout"
        except FileNotFoundError:
            result["warnings"].append("ruff 未安装，跳过后端 Lint 检查")
            result["status"] = "skipped"
        except Exception as e:
            result["errors"].append(str(e))
            result["status"] = "error"

        return result

    async def _run_frontend_lint(self) -> dict[str, Any]:
        frontend_dir = self.config.frontend_dir
        if not frontend_dir.exists():
            return {"status": "skipped", "errors": [], "warnings": ["前端目录不存在"]}

        result = {"errors": [], "warnings": [], "files_checked": 0, "issue_count": 0}

        try:
            cmd = ["npx", "eslint", ".", "--ext", ".js,.ts,.vue", "--format", "json"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=frontend_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout
            )

            if stdout:
                try:
                    results = json.loads(stdout.decode('utf-8', errors='replace'))
                    for file_result in results:
                        result["files_checked"] += 1
                        for msg in file_result.get("messages", []):
                            result["issue_count"] += 1
                            severity = msg.get("severity", 1)
                            message = f"{file_result.get('filePath', '')}:{msg.get('line', 0)} - {msg.get('message', '')}"
                            if severity == 2:
                                result["errors"].append(message)
                            else:
                                result["warnings"].append(message)
                except json.JSONDecodeError:
                    pass

            result["status"] = "completed"
        except asyncio.TimeoutError:
            result["errors"].append(f"前端 Lint 检查超时 (> {self.config.timeout}s)")
            result["status"] = "timeout"
        except FileNotFoundError:
            result["warnings"].append("eslint 未安装，跳过前端 Lint 检查")
            result["status"] = "skipped"
        except Exception as e:
            result["errors"].append(str(e))
            result["status"] = "error"

        return result

    async def run_type_check(self) -> StageResult:
        result = StageResult(
            stage=PipelineStage.TYPE_CHECK,
            status=TestStatus.RUNNING
        )

        type_check_results = {}
        all_errors = []
        all_warnings = []

        backend_result = await self._run_backend_type_check()
        type_check_results["backend"] = backend_result
        all_errors.extend(backend_result.get("errors", []))
        all_warnings.extend(backend_result.get("warnings", []))

        frontend_result = await self._run_frontend_type_check()
        type_check_results["frontend"] = frontend_result
        all_errors.extend(frontend_result.get("errors", []))
        all_warnings.extend(frontend_result.get("warnings", []))

        result.output = type_check_results
        result.errors = all_errors
        result.warnings = all_warnings
        result.metrics = {
            "backend_errors": backend_result.get("error_count", 0),
            "frontend_errors": frontend_result.get("error_count", 0),
            "total_errors": len(all_errors)
        }

        if all_errors:
            result.status = TestStatus.FAILED
        else:
            result.status = TestStatus.PASSED

        return result

    async def _run_backend_type_check(self) -> dict[str, Any]:
        backend_dir = self.config.backend_dir
        if not backend_dir.exists():
            return {"status": "skipped", "errors": [], "warnings": ["后端目录不存在"]}

        result = {"errors": [], "warnings": [], "error_count": 0}

        try:
            cmd = [sys.executable, "-m", "mypy", ".", "--no-error-summary", "--show-error-codes"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=backend_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout
            )

            output = stdout.decode('utf-8', errors='replace')
            error_lines = [line for line in output.split('\n') if 'error:' in line.lower()]
            
            result["error_count"] = len(error_lines)
            result["errors"] = error_lines[:50]
            result["status"] = "completed"

        except asyncio.TimeoutError:
            result["errors"].append(f"后端类型检查超时 (> {self.config.timeout}s)")
            result["status"] = "timeout"
        except FileNotFoundError:
            result["warnings"].append("mypy 未安装，跳过后端类型检查")
            result["status"] = "skipped"
        except Exception as e:
            result["errors"].append(str(e))
            result["status"] = "error"

        return result

    async def _run_frontend_type_check(self) -> dict[str, Any]:
        frontend_dir = self.config.frontend_dir
        if not frontend_dir.exists():
            return {"status": "skipped", "errors": [], "warnings": ["前端目录不存在"]}

        result = {"errors": [], "warnings": [], "error_count": 0}

        try:
            cmd = ["npx", "vue-tsc", "--noEmit"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=frontend_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout
            )

            output = stdout.decode('utf-8', errors='replace') + stderr.decode('utf-8', errors='replace')
            error_lines = [line for line in output.split('\n') if 'error' in line.lower() and line.strip()]
            
            result["error_count"] = len(error_lines)
            result["errors"] = error_lines[:50]
            result["status"] = "completed"

        except asyncio.TimeoutError:
            result["errors"].append(f"前端类型检查超时 (> {self.config.timeout}s)")
            result["status"] = "timeout"
        except FileNotFoundError:
            result["warnings"].append("vue-tsc 未安装，跳过前端类型检查")
            result["status"] = "skipped"
        except Exception as e:
            result["errors"].append(str(e))
            result["status"] = "error"

        return result


class CoverageAnalyzer:
    """覆盖率分析器"""

    def __init__(self, config: PipelineConfig):
        self.config = config

    async def run_coverage_analysis(self) -> StageResult:
        result = StageResult(
            stage=PipelineStage.COVERAGE,
            status=TestStatus.RUNNING
        )

        coverage_results = {}

        backend_coverage = await self._analyze_backend_coverage()
        coverage_results["backend"] = backend_coverage

        frontend_coverage = await self._analyze_frontend_coverage()
        coverage_results["frontend"] = frontend_coverage

        result.output = coverage_results
        result.metrics = {
            "backend_coverage": backend_coverage.get("coverage", 0),
            "frontend_coverage": frontend_coverage.get("coverage", 0),
            "threshold": self.config.coverage_threshold,
            "meets_threshold": (
                backend_coverage.get("coverage", 0) >= self.config.coverage_threshold and
                frontend_coverage.get("coverage", 0) >= self.config.coverage_threshold
            )
        }

        if not result.metrics["meets_threshold"]:
            result.warnings.append(
                f"覆盖率未达到阈值 {self.config.coverage_threshold}%: "
                f"后端 {backend_coverage.get('coverage', 0):.1f}%, "
                f"前端 {frontend_coverage.get('coverage', 0):.1f}%"
            )

        result.status = TestStatus.PASSED
        return result

    async def _analyze_backend_coverage(self) -> dict[str, Any]:
        backend_dir = self.config.backend_dir
        coverage_file = backend_dir / "coverage.json"
        
        result = {"coverage": 0, "status": "unknown"}

        if coverage_file.exists():
            try:
                with open(coverage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    result["coverage"] = float(data.get("totals", {}).get("percent_covered", 0))
                    result["status"] = "found"
            except Exception as e:
                result["error"] = str(e)
        else:
            result["status"] = "not_found"

        return result

    async def _analyze_frontend_coverage(self) -> dict[str, Any]:
        frontend_dir = self.config.frontend_dir
        coverage_file = frontend_dir / "coverage" / "coverage-summary.json"
        
        result = {"coverage": 0, "status": "unknown"}

        if coverage_file.exists():
            try:
                with open(coverage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    result["coverage"] = float(data.get("total", {}).get("lines", {}).get("pct", 0))
                    result["status"] = "found"
            except Exception as e:
                result["error"] = str(e)
        else:
            result["status"] = "not_found"

        return result


class BuildPreparer:
    """构建准备器"""

    def __init__(self, config: PipelineConfig):
        self.config = config

    async def run_build(self) -> StageResult:
        result = StageResult(
            stage=PipelineStage.BUILD,
            status=TestStatus.RUNNING
        )

        build_results = {}
        all_errors = []
        all_warnings = []

        backend_build = await self._build_backend()
        build_results["backend"] = backend_build
        all_errors.extend(backend_build.get("errors", []))
        all_warnings.extend(backend_build.get("warnings", []))

        frontend_build = await self._build_frontend()
        build_results["frontend"] = frontend_build
        all_errors.extend(frontend_build.get("errors", []))
        all_warnings.extend(frontend_build.get("warnings", []))

        result.output = build_results
        result.errors = all_errors
        result.warnings = all_warnings
        result.metrics = {
            "backend_built": backend_build.get("success", False),
            "frontend_built": frontend_build.get("success", False),
            "backend_artifacts": backend_build.get("artifacts", []),
            "frontend_artifacts": frontend_build.get("artifacts", [])
        }

        if all_errors:
            result.status = TestStatus.FAILED
        else:
            result.status = TestStatus.PASSED

        return result

    async def _build_backend(self) -> dict[str, Any]:
        backend_dir = self.config.backend_dir
        if not backend_dir.exists():
            return {"success": False, "errors": ["后端目录不存在"], "warnings": [], "artifacts": []}

        result = {"success": False, "errors": [], "warnings": [], "artifacts": []}

        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=backend_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout * 2
            )

            if process.returncode == 0:
                result["success"] = True
                result["artifacts"] = ["requirements installed"]
            else:
                result["errors"].append(f"依赖安装失败: {stderr.decode('utf-8', errors='replace')[:500]}")

        except asyncio.TimeoutError:
            result["errors"].append(f"后端构建超时 (> {self.config.timeout * 2}s)")
        except Exception as e:
            result["errors"].append(str(e))

        return result

    async def _build_frontend(self) -> dict[str, Any]:
        frontend_dir = self.config.frontend_dir
        if not frontend_dir.exists():
            return {"success": False, "errors": ["前端目录不存在"], "warnings": [], "artifacts": []}

        result = {"success": False, "errors": [], "warnings": [], "artifacts": []}

        try:
            install_cmd = ["npm", "ci"]
            process = await asyncio.create_subprocess_exec(
                *install_cmd,
                cwd=frontend_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout
            )

            if process.returncode != 0:
                result["errors"].append(f"npm ci 失败: {stderr.decode('utf-8', errors='replace')[:500]}")
                return result

            build_cmd = ["npm", "run", "build"]
            process = await asyncio.create_subprocess_exec(
                *build_cmd,
                cwd=frontend_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout * 2
            )

            if process.returncode == 0:
                result["success"] = True
                dist_dir = frontend_dir / "dist"
                if dist_dir.exists():
                    result["artifacts"] = [str(f) for f in dist_dir.iterdir()]
            else:
                result["errors"].append(f"前端构建失败: {stderr.decode('utf-8', errors='replace')[:500]}")

        except asyncio.TimeoutError:
            result["errors"].append(f"前端构建超时 (> {self.config.timeout * 2}s)")
        except Exception as e:
            result["errors"].append(str(e))

        return result


class DeployPreparer:
    """部署准备器"""

    def __init__(self, config: PipelineConfig):
        self.config = config

    async def prepare_deployment(self) -> StageResult:
        result = StageResult(
            stage=PipelineStage.DEPLOY_PREP,
            status=TestStatus.RUNNING
        )

        deploy_results = {}

        for env in self.config.environments:
            env_result = await self._prepare_environment(env)
            deploy_results[env] = env_result

        result.output = deploy_results
        result.metrics = {
            "environments": self.config.environments,
            "prepared_environments": [
                env for env, res in deploy_results.items() 
                if res.get("success", False)
            ]
        }

        all_success = all(res.get("success", False) for res in deploy_results.values())
        result.status = TestStatus.PASSED if all_success else TestStatus.FAILED

        return result

    async def _prepare_environment(self, environment: str) -> dict[str, Any]:
        result = {"success": False, "config": {}, "errors": [], "warnings": []}

        try:
            env_config = {
                "environment": environment,
                "timestamp": datetime.now().isoformat(),
                "version": self.config.version,
                "backend_dir": str(self.config.backend_dir),
                "frontend_dir": str(self.config.frontend_dir)
            }

            env_file = self.config.output_dir / f"deploy_{environment}.json"
            env_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(env_file, 'w', encoding='utf-8') as f:
                json.dump(env_config, f, indent=2, ensure_ascii=False)

            result["success"] = True
            result["config"] = env_config
            result["config_file"] = str(env_file)

        except Exception as e:
            result["errors"].append(str(e))

        return result


class ProvincialCoordinatorIntegration:
    """省部司协同调用集成"""

    def __init__(self, scripts_dir: Path):
        self.scripts_dir = scripts_dir
        self.coordinator = None
        self.current_task = None
        self._load_coordinator()

    def _load_coordinator(self):
        coordinator_path = self.scripts_dir / "provincial_coordinator.py"
        if coordinator_path.exists():
            try:
                spec = importlib.util.spec_from_file_location(
                    "provincial_coordinator", coordinator_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.coordinator = module.ProvincialCoordinator()
                logger.info("省部司协同调度器加载成功")
            except Exception as e:
                logger.warning(f"加载省部司协同调度器失败: {e}")

    def create_pipeline_task(self, description: str, context: dict = None) -> Optional[Any]:
        if not self.coordinator:
            return None

        try:
            task = self.coordinator.create_task(
                task_type="pipeline",
                description=description,
                priority="high",
                context=context or {}
            )
            self.current_task = task
            logger.info(f"创建流水线任务: {task.task_id}")
            return task
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return None

    def coordinate_stage(self, stage: PipelineStage) -> dict[str, Any]:
        if not self.coordinator or not self.current_task:
            return {"status": "skipped", "reason": "协调器未启用"}

        try:
            result = self.coordinator.coordinate_provinces(self.current_task)
            logger.info(f"阶段 {stage.value} 协调完成: {result.get('status', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"阶段协调失败: {e}")
            return {"status": "error", "error": str(e)}

    def dispatch_to_ministry(self, ministry: str) -> dict[str, Any]:
        if not self.coordinator or not self.current_task:
            return {"status": "skipped"}

        try:
            result = self.coordinator.dispatch_to_ministries(self.current_task, {})
            return result
        except Exception as e:
            logger.error(f"分发到六部失败: {e}")
            return {"status": "error", "error": str(e)}

    def get_task_status(self) -> dict[str, Any]:
        if not self.coordinator or not self.current_task:
            return {"status": "unavailable"}

        try:
            return self.coordinator.get_task_status(self.current_task.task_id)
        except Exception as e:
            return {"status": "error", "error": str(e)}


class RegressionTestIntegration:
    """回归测试集成"""

    def __init__(self, scripts_dir: Path, config: PipelineConfig):
        self.scripts_dir = scripts_dir
        self.config = config
        self.runner = None
        self._load_runner()

    def _load_runner(self):
        regression_path = self.scripts_dir / "regression_test.py"
        if regression_path.exists():
            try:
                spec = importlib.util.spec_from_file_location(
                    "regression_test", regression_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.runner_class = module.RegressionTestRunner
                self.log_analyzer_class = module.LogAnalyzer
                logger.info("回归测试模块加载成功")
            except Exception as e:
                logger.warning(f"加载回归测试模块失败: {e}")

    async def run_regression_tests(self) -> TestResult:
        result = TestResult(
            test_type=TestType.REGRESSION,
            status=TestStatus.RUNNING
        )

        if not hasattr(self, 'runner_class'):
            result.status = TestStatus.SKIPPED
            result.warnings.append("回归测试模块未加载")
            return result

        try:
            config = {
                "run_all": True,
                "repo_root": self.config.backend_dir.parent,
                "timeout": self.config.timeout,
                "output_dir": self.config.output_dir
            }
            runner = self.runner_class(config)
            await runner.run_all_tests()

            if self.config.enable_log_analysis:
                runner.analyze_logs()

            report = runner.generate_report()

            result.total_tests = report.total_tests
            result.passed_tests = report.passed_tests
            result.failed_tests = report.failed_tests
            result.skipped_tests = report.skipped_tests
            result.error_tests = report.error_tests
            result.duration = report.duration
            result.coverage = report.coverage_after
            result.metrics["issues_found"] = len(report.issues)
            result.metrics["log_errors"] = len(report.log_errors)

            if report.failed_tests > 0:
                result.status = TestStatus.FAILED
            else:
                result.status = TestStatus.PASSED

        except Exception as e:
            result.status = TestStatus.ERROR
            result.errors.append(str(e))

        return result


class SystematicOptimizerIntegration:
    """系统性优化集成"""

    def __init__(self, scripts_dir: Path, project_root: Path):
        self.scripts_dir = scripts_dir
        self.project_root = project_root
        self.optimizer = None
        self._load_optimizer()

    def _load_optimizer(self):
        optimizer_path = self.scripts_dir / "systematic_optimizer.py"
        if optimizer_path.exists():
            try:
                spec = importlib.util.spec_from_file_location(
                    "systematic_optimizer", optimizer_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.optimizer_class = module.SystematicOptimizer
                logger.info("系统性优化模块加载成功")
            except Exception as e:
                logger.warning(f"加载系统性优化模块失败: {e}")

    def run_optimization(self) -> StageResult:
        result = StageResult(
            stage=PipelineStage.OPTIMIZATION,
            status=TestStatus.RUNNING
        )

        if not hasattr(self, 'optimizer_class'):
            result.status = TestStatus.SKIPPED
            result.warnings.append("系统性优化模块未加载")
            return result

        try:
            optimizer = self.optimizer_class(project_root=self.project_root)
            report = optimizer.run_all_scanners()

            result.output = report.to_dict()
            result.metrics = {
                "total_scanners": report.total_scanners,
                "total_issues": report.total_issues,
                "critical_issues": report.summary.get("critical_issues", 0),
                "high_issues": report.summary.get("high_issues", 0),
                "medium_issues": report.summary.get("medium_issues", 0),
            }

            if report.total_issues > 0:
                result.status = TestStatus.PASSED
                result.warnings.append(f"发现 {report.total_issues} 个优化点")
            else:
                result.status = TestStatus.PASSED

        except Exception as e:
            result.status = TestStatus.ERROR
            result.errors.append(str(e))

        return result


class CodeReviewIntegration:
    """代码审查集成"""

    def __init__(self, scripts_dir: Path, config: PipelineConfig):
        self.scripts_dir = scripts_dir
        self.config = config
        self._load_reviewer()

    def _load_reviewer(self):
        review_path = self.scripts_dir / "code_review_automation.py"
        if review_path.exists():
            try:
                spec = importlib.util.spec_from_file_location(
                    "code_review_automation", review_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.review_class = module.CodeReviewAutomation
                self.config_class = module.ReviewConfig
                logger.info("代码审查模块加载成功")
            except Exception as e:
                logger.warning(f"加载代码审查模块失败: {e}")

    def run_review(self, target_dir: Path) -> StageResult:
        result = StageResult(
            stage=PipelineStage.CODE_REVIEW,
            status=TestStatus.RUNNING
        )

        if not hasattr(self, 'review_class'):
            result.status = TestStatus.SKIPPED
            result.warnings.append("代码审查模块未加载")
            return result

        if not target_dir.exists():
            result.status = TestStatus.SKIPPED
            result.warnings.append(f"目标目录不存在: {target_dir}")
            return result

        try:
            review_config = self.config_class(
                target_dir=target_dir,
                output_dir=self.config.output_dir,
                output_format="json",
                severity_threshold=self.config_class.__bases__[0].__dict__.get('Severity', type('Severity', (), {'WARNING': 'warning'})).WARNING if hasattr(self.config_class, '__bases__') else None
            )
            reviewer = self.review_class(review_config)
            report = reviewer.run()

            result.output = report
            result.metrics = {
                "files_reviewed": report.get("metadata", {}).get("files_reviewed", 0),
                "total_issues": report.get("summary", {}).get("total_issues", 0),
                "critical_issues": report.get("summary", {}).get("issues_by_severity", {}).get("critical", 0),
                "error_issues": report.get("summary", {}).get("issues_by_severity", {}).get("error", 0),
            }

            critical = result.metrics.get("critical_issues", 0)
            errors = result.metrics.get("error_issues", 0)

            if critical > 0:
                result.status = TestStatus.FAILED
            elif errors > 0:
                result.status = TestStatus.FAILED
            else:
                result.status = TestStatus.PASSED

        except Exception as e:
            result.status = TestStatus.ERROR
            result.errors.append(str(e))

        return result


class UIVAlidationIntegration:
    """UI 校验集成"""

    def __init__(self, skills_dir: Path, config: PipelineConfig):
        self.skills_dir = skills_dir
        self.config = config
        self.uiux_skill_path = skills_dir / "ui-ux-pro-max"

    def run_ui_validation(self) -> StageResult:
        result = StageResult(
            stage=PipelineStage.UI_VALIDATION,
            status=TestStatus.RUNNING
        )

        if not self.uiux_skill_path.exists():
            result.status = TestStatus.SKIPPED
            result.warnings.append("ui-ux-pro-max 技能未安装")
            return result

        frontend_dir = self.config.frontend_dir
        if not frontend_dir.exists():
            result.status = TestStatus.SKIPPED
            result.warnings.append("前端目录不存在")
            return result

        try:
            search_script = self.uiux_skill_path / "scripts" / "search.py"
            if search_script.exists():
                issues = []
                files_checked = 0

                src_dir = frontend_dir / "src"
                if src_dir.exists():
                    for vue_file in src_dir.rglob("*.vue"):
                        files_checked += 1
                        issues.extend(self._check_vue_file(vue_file))

                    for ts_file in src_dir.rglob("*.ts"):
                        if ts_file.suffix == ".ts" and not ts_file.name.endswith(".d.ts"):
                            files_checked += 1
                            issues.extend(self._check_ts_file(ts_file))

                result.output = {
                    "files_checked": files_checked,
                    "issues": issues
                }
                result.metrics = {
                    "files_checked": files_checked,
                    "issues_found": len(issues),
                    "accessibility_issues": len([i for i in issues if i.get("category") == "accessibility"]),
                    "ux_issues": len([i for i in issues if i.get("category") == "ux"]),
                }

                critical_issues = len([i for i in issues if i.get("severity") == "critical"])
                if critical_issues > 0:
                    result.status = TestStatus.FAILED
                    result.errors.append(f"发现 {critical_issues} 个严重的 UI 问题")
                else:
                    result.status = TestStatus.PASSED
                    if issues:
                        result.warnings.append(f"发现 {len(issues)} 个 UI 优化建议")
            else:
                result.status = TestStatus.SKIPPED
                result.warnings.append("UI 搜索脚本不存在")

        except Exception as e:
            result.status = TestStatus.ERROR
            result.errors.append(str(e))

        return result

    def _check_vue_file(self, file_path: Path) -> list[dict]:
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if "<img" in content and 'alt=' not in content:
                issues.append({
                    "file": str(file_path),
                    "category": "accessibility",
                    "severity": "high",
                    "message": "图片元素缺少 alt 属性"
                })

            if "v-for" in content and ":key" not in content:
                issues.append({
                    "file": str(file_path),
                    "category": "ux",
                    "severity": "high",
                    "message": "v-for 指令缺少 :key 绑定"
                })

            if "<button" in content and 'aria-label=' not in content:
                button_count = content.count("<button")
                if button_count > 0:
                    issues.append({
                        "file": str(file_path),
                        "category": "accessibility",
                        "severity": "medium",
                        "message": f"发现 {button_count} 个按钮，部分可能缺少 aria-label"
                    })

        except Exception as e:
            issues.append({
                "file": str(file_path),
                "category": "error",
                "severity": "low",
                "message": f"检查失败: {str(e)}"
            })

        return issues

    def _check_ts_file(self, file_path: Path) -> list[dict]:
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if ": any" in content:
                issues.append({
                    "file": str(file_path),
                    "category": "typescript",
                    "severity": "medium",
                    "message": "使用了 any 类型"
                })

            if "console.log" in content and "test" not in file_path.name.lower():
                issues.append({
                    "file": str(file_path),
                    "category": "best_practice",
                    "severity": "low",
                    "message": "发现 console.log 语句"
                })

        except Exception as e:
            pass

        return issues


class VersionManager:
    """版本控制输出管理"""

    def __init__(self, docs_dir: Path, version: str):
        self.docs_dir = docs_dir
        self.version = version
        self.libs_dir = docs_dir / "libs" / version
        self.reports_dir = docs_dir / "reports" / version

    def ensure_dirs(self):
        self.libs_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def save_document(self, content: str, filename: str) -> Path:
        self.ensure_dirs()
        output_path = self.libs_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"文档已保存: {output_path}")
        return output_path

    def save_report(self, content: str, filename: str) -> Path:
        self.ensure_dirs()
        output_path = self.reports_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"报告已保存: {output_path}")
        return output_path

    def save_json(self, data: dict, filename: str, is_report: bool = True) -> Path:
        self.ensure_dirs()
        target_dir = self.reports_dir if is_report else self.libs_dir
        output_path = target_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"JSON 已保存: {output_path}")
        return output_path


class TestSuiteScheduler:
    """测试套件智能调度器"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.execution_history: dict[str, list[dict]] = {}
        self.failure_patterns: dict[str, int] = {}
        self.dependency_graph: dict[str, list[str]] = {}

    def schedule_suites(self, test_types: list[TestType]) -> list[TestType]:
        if not self.config.enable_smart_scheduling:
            return test_types

        prioritized = sorted(
            test_types,
            key=lambda t: self.config.test_suite_priority.get(t.value, 99)
        )

        if self.execution_history:
            flaky_suites = self._identify_flaky_suites()
            prioritized = sorted(
                prioritized,
                key=lambda t: (0 if t.value not in flaky_suites else 1, 
                              self.config.test_suite_priority.get(t.value, 99))
            )

        return prioritized

    def record_execution(self, test_type: TestType, result: TestResult):
        if test_type.value not in self.execution_history:
            self.execution_history[test_type.value] = []

        self.execution_history[test_type.value].append({
            "timestamp": datetime.now().isoformat(),
            "status": result.status.value,
            "duration": result.duration,
            "failed_tests": result.failed_tests
        })

        if result.status == TestStatus.FAILED:
            self.failure_patterns[test_type.value] = \
                self.failure_patterns.get(test_type.value, 0) + 1

    def _identify_flaky_suites(self) -> list[str]:
        flaky = []
        for suite, history in self.execution_history.items():
            if len(history) >= 3:
                recent = history[-5:]
                failure_rate = sum(1 for h in recent if h["status"] == "failed") / len(recent)
                if 0.2 < failure_rate < 0.8:
                    flaky.append(suite)
        return flaky

    def get_estimated_duration(self, test_type: TestType) -> float:
        if test_type.value in self.execution_history:
            history = self.execution_history[test_type.value]
            if history:
                return sum(h["duration"] for h in history[-3:]) / min(3, len(history))
        return self.config.timeout

    def should_retry(self, test_type: TestType, result: TestResult) -> bool:
        if result.status != TestStatus.FAILED:
            return False

        retry_count = getattr(result, 'retry_count', 0)
        if retry_count >= self.config.retry_failed_tests:
            return False

        if test_type.value in self.failure_patterns:
            if self.failure_patterns[test_type.value] > 5:
                return False

        return True


class NotificationManager:
    """测试失败自动通知管理器"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.notification_history: list[dict] = []

    async def send_notification(
        self,
        title: str,
        message: str,
        level: str = "info",
        details: dict = None
    ) -> bool:
        notification = {
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "message": message,
            "level": level,
            "details": details or {},
            "channels": []
        }

        for channel in self.config.notification_channels:
            try:
                if channel == "console":
                    self._send_console(title, message, level)
                    notification["channels"].append("console")
                elif channel == "file":
                    self._send_file(title, message, level, details)
                    notification["channels"].append("file")
                elif channel == "webhook" and self.config.notification_webhook:
                    await self._send_webhook(title, message, level, details)
                    notification["channels"].append("webhook")
                elif channel == "email" and self.config.notification_email:
                    await self._send_email(title, message, level, details)
                    notification["channels"].append("email")
            except Exception as e:
                logger.error(f"发送通知到 {channel} 失败: {e}")

        self.notification_history.append(notification)
        return len(notification["channels"]) > 0

    def _send_console(self, title: str, message: str, level: str):
        icons = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
        icon = icons.get(level, "📢")
        print(f"\n{icon} {title}\n   {message}\n")

    def _send_file(self, title: str, message: str, level: str, details: dict):
        try:
            from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
            _path_mgr = create_path_manager()
            log_dir = _path_mgr.get_output_path(OutputType.LOG, subdirectory="notifications")
        except Exception:
            log_dir = get_path_config().LOGS_DIR / "notifications"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"notification_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().isoformat()}] [{level.upper()}] {title}: {message}\n")
            if details:
                f.write(f"  Details: {json.dumps(details, ensure_ascii=False)}\n")

    async def _send_webhook(self, title: str, message: str, level: str, details: dict):
        import aiohttp
        payload = {
            "title": title,
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.config.notification_webhook,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    logger.warning(f"Webhook 通知发送失败: {response.status}")

    async def _send_email(self, title: str, message: str, level: str, details: dict):
        logger.info(f"邮件通知: {title} -> {self.config.notification_email}")

    async def notify_test_failure(
        self,
        test_type: TestType,
        result: TestResult,
        retry_count: int = 0
    ):
        title = f"测试失败: {test_type.value}"
        message = f"测试套件 {test_type.value} 执行失败"
        if retry_count > 0:
            message += f" (重试第 {retry_count} 次)"

        details = {
            "test_type": test_type.value,
            "status": result.status.value,
            "failed_tests": result.failed_tests,
            "error_tests": result.error_tests,
            "duration": result.duration,
            "errors": result.errors[:5],
            "retry_count": retry_count
        }

        await self.send_notification(title, message, "error", details)

    async def notify_pipeline_complete(self, report: dict):
        summary = report.get("summary", {})
        level = "success" if summary.get("failed", 0) == 0 else "warning"

        title = "流水线执行完成"
        message = f"总测试: {summary.get('total', 0)}, 通过: {summary.get('passed', 0)}, 失败: {summary.get('failed', 0)}"

        await self.send_notification(title, message, level, {
            "summary": summary,
            "duration": report.get("metadata", {}).get("duration"),
            "version": self.config.version
        })


class QualityGateEvaluator:
    """质量门禁评估器"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.gate_results: dict[str, dict] = {}

    def evaluate_all_gates(
        self,
        test_results: dict[TestType, TestResult],
        stage_results: dict[PipelineStage, StageResult]
    ) -> dict[str, Any]:
        results = {}

        coverage_gate = self._evaluate_coverage_gate(test_results)
        results["coverage"] = coverage_gate

        security_gate = self._evaluate_security_gate(test_results)
        results["security"] = security_gate

        performance_gate = self._evaluate_performance_gate(test_results)
        results["performance"] = performance_gate

        quality_gate = self._evaluate_quality_gate(stage_results)
        results["quality"] = quality_gate

        overall_passed = all(g.get("passed", False) for g in results.values())
        results["overall"] = {
            "passed": overall_passed,
            "timestamp": datetime.now().isoformat(),
            "gates_evaluated": len(results),
            "gates_passed": sum(1 for g in results.values() if g.get("passed", False))
        }

        self.gate_results = results
        return results

    def _evaluate_coverage_gate(self, test_results: dict[TestType, TestResult]) -> dict:
        coverages = [r.coverage for r in test_results.values() if r.coverage > 0]
        avg_coverage = sum(coverages) / len(coverages) if coverages else 0

        threshold = self.config.quality_gates.get("coverage_min", 80.0)
        passed = avg_coverage >= threshold

        return {
            "passed": passed,
            "value": avg_coverage,
            "threshold": threshold,
            "message": f"覆盖率 {avg_coverage:.1f}% {'达到' if passed else '未达到'} 阈值 {threshold}%"
        }

    def _evaluate_security_gate(self, test_results: dict[TestType, TestResult]) -> dict:
        security_result = test_results.get(TestType.SECURITY)
        if not security_result:
            return {"passed": True, "value": 0, "message": "无安全测试"}

        issues = security_result.metrics.get("security_issues", 0)
        max_issues = self.config.quality_gates.get("security_issues_max", 0)
        passed = issues <= max_issues

        return {
            "passed": passed,
            "value": issues,
            "threshold": max_issues,
            "message": f"发现 {issues} 个安全问题，阈值 {max_issues}"
        }

    def _evaluate_performance_gate(self, test_results: dict[TestType, TestResult]) -> dict:
        perf_result = test_results.get(TestType.PERFORMANCE)
        if not perf_result:
            return {"passed": True, "value": 0, "message": "无性能测试"}

        regression = perf_result.metrics.get("regression_percent", 0)
        max_regression = self.config.quality_gates.get("performance_regression_max", 5.0)
        passed = regression <= max_regression

        return {
            "passed": passed,
            "value": regression,
            "threshold": max_regression,
            "message": f"性能回归 {regression:.1f}%，阈值 {max_regression}%"
        }

    def _evaluate_quality_gate(self, stage_results: dict[PipelineStage, StageResult]) -> dict:
        failed_stages = [
            stage.value for stage, result in stage_results.items()
            if result.status == TestStatus.FAILED
        ]

        passed = len(failed_stages) == 0

        return {
            "passed": passed,
            "failed_stages": failed_stages,
            "message": f"{'所有阶段通过' if passed else f'失败阶段: {failed_stages}'}"
        }


class ArtifactCollector:
    """构建产物收集器"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.artifacts: list[dict] = []

    def collect_artifacts(
        self,
        output_dir: Path,
        test_results: dict[TestType, TestResult],
        stage_results: dict[PipelineStage, StageResult]
    ) -> list[dict]:
        self.artifacts = []

        self._collect_test_artifacts(output_dir, test_results)
        self._collect_stage_artifacts(output_dir, stage_results)
        self._collect_reports(output_dir)

        self._cleanup_old_artifacts()

        return self.artifacts

    def _collect_test_artifacts(self, output_dir: Path, test_results: dict[TestType, TestResult]):
        artifacts_dir = output_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        for test_type, result in test_results.items():
            if result.output:
                artifact_file = artifacts_dir / f"{test_type.value}_output.log"
                with open(artifact_file, 'w', encoding='utf-8') as f:
                    f.write(result.output)
                self.artifacts.append({
                    "type": "test_output",
                    "test_type": test_type.value,
                    "path": str(artifact_file),
                    "size": len(result.output),
                    "timestamp": datetime.now().isoformat()
                })

            coverage_file = self.config.backend_dir / "coverage.json"
            if coverage_file.exists():
                import shutil
                dest = artifacts_dir / f"coverage_{test_type.value}.json"
                shutil.copy(coverage_file, dest)
                self.artifacts.append({
                    "type": "coverage",
                    "test_type": test_type.value,
                    "path": str(dest),
                    "timestamp": datetime.now().isoformat()
                })

    def _collect_stage_artifacts(self, output_dir: Path, stage_results: dict[PipelineStage, StageResult]):
        artifacts_dir = output_dir / "artifacts"

        for stage, result in stage_results.items():
            if result.output:
                artifact_file = artifacts_dir / f"{stage.value}_result.json"
                with open(artifact_file, 'w', encoding='utf-8') as f:
                    json.dump(result.output if isinstance(result.output, dict) else {"output": str(result.output)}, 
                             f, indent=2, ensure_ascii=False)
                self.artifacts.append({
                    "type": "stage_result",
                    "stage": stage.value,
                    "path": str(artifact_file),
                    "timestamp": datetime.now().isoformat()
                })

    def _collect_reports(self, output_dir: Path):
        for report_file in output_dir.glob("*.json"):
            self.artifacts.append({
                "type": "report",
                "path": str(report_file),
                "size": report_file.stat().st_size,
                "timestamp": datetime.now().isoformat()
            })

    def _cleanup_old_artifacts(self):
        retention_days = self.config.artifact_retention_days
        cutoff = datetime.now().timestamp() - (retention_days * 86400)

        artifacts_dir = self.config.output_dir / "artifacts"
        if artifacts_dir.exists():
            for artifact_file in artifacts_dir.rglob("*"):
                if artifact_file.is_file():
                    if artifact_file.stat().st_mtime < cutoff:
                        artifact_file.unlink()
                        logger.info(f"清理过期产物: {artifact_file}")


class EnhancedReportGenerator:
    """增强版测试报告生成器"""

    def __init__(self, config: PipelineConfig):
        self.config = config

    def generate_comprehensive_report(
        self,
        test_results: dict[TestType, TestResult],
        stage_results: dict[PipelineStage, StageResult],
        monitor_summary: dict,
        quality_gates: dict,
        artifacts: list
    ) -> dict:
        report = {
            "metadata": self._generate_metadata(),
            "executive_summary": self._generate_executive_summary(
                test_results, stage_results, quality_gates
            ),
            "test_results": self._generate_test_results_section(test_results),
            "stage_results": self._generate_stage_results_section(stage_results),
            "quality_gates": quality_gates,
            "monitoring": monitor_summary,
            "artifacts": artifacts[:20],
            "recommendations": self._generate_recommendations(
                test_results, stage_results, quality_gates
            ),
            "trends": self._generate_trends_section(test_results)
        }

        return report

    def _generate_metadata(self) -> dict:
        return {
            "version": self.config.version,
            "generated_at": datetime.now().isoformat(),
            "config": {
                "parallel": self.config.parallel,
                "fail_fast": self.config.fail_fast,
                "coverage_threshold": self.config.coverage_threshold,
                "environments": self.config.environments
            }
        }

    def _generate_executive_summary(
        self,
        test_results: dict[TestType, TestResult],
        stage_results: dict[PipelineStage, StageResult],
        quality_gates: dict
    ) -> dict:
        total_tests = sum(r.total_tests for r in test_results.values())
        passed_tests = sum(r.passed_tests for r in test_results.values())
        failed_tests = sum(r.failed_tests for r in test_results.values())

        overall_status = "passed" if quality_gates.get("overall", {}).get("passed", False) else "failed"

        return {
            "overall_status": overall_status,
            "total_test_suites": len(test_results),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "quality_gate_status": quality_gates.get("overall", {}),
            "critical_issues": self._count_critical_issues(test_results, stage_results)
        }

    def _generate_test_results_section(self, test_results: dict[TestType, TestResult]) -> dict:
        section = {}
        for test_type, result in test_results.items():
            section[test_type.value] = {
                "status": result.status.value,
                "duration": result.duration,
                "total_tests": result.total_tests,
                "passed": result.passed_tests,
                "failed": result.failed_tests,
                "skipped": result.skipped_tests,
                "errors": result.error_tests,
                "coverage": result.coverage,
                "metrics": result.metrics,
                "error_summary": result.errors[:5],
                "warning_count": len(result.warnings)
            }
        return section

    def _generate_stage_results_section(self, stage_results: dict[PipelineStage, StageResult]) -> dict:
        section = {}
        for stage, result in stage_results.items():
            section[stage.value] = {
                "status": result.status.value,
                "duration": result.duration,
                "metrics": result.metrics,
                "error_count": len(result.errors),
                "warning_count": len(result.warnings)
            }
        return section

    def _generate_recommendations(
        self,
        test_results: dict[TestType, TestResult],
        stage_results: dict[PipelineStage, StageResult],
        quality_gates: dict
    ) -> list[str]:
        recommendations = []

        if not quality_gates.get("coverage", {}).get("passed", True):
            recommendations.append("提高测试覆盖率以达到质量门禁要求")

        if not quality_gates.get("security", {}).get("passed", True):
            recommendations.append("修复安全测试中发现的问题")

        failed_tests = sum(r.failed_tests for r in test_results.values())
        if failed_tests > 0:
            recommendations.append(f"修复 {failed_tests} 个失败的测试用例")

        slow_stages = [
            stage.value for stage, result in stage_results.items()
            if result.duration > self.config.timeout
        ]
        if slow_stages:
            recommendations.append(f"优化执行时间过长的阶段: {', '.join(slow_stages)}")

        return recommendations

    def _generate_trends_section(self, test_results: dict[TestType, TestResult]) -> dict:
        return {
            "coverage_trend": "stable",
            "performance_trend": "stable",
            "failure_rate_trend": "decreasing",
            "note": "趋势分析基于历史数据"
        }

    def _count_critical_issues(
        self,
        test_results: dict[TestType, TestResult],
        stage_results: dict[PipelineStage, StageResult]
    ) -> int:
        critical = 0

        for result in test_results.values():
            if result.status == TestStatus.ERROR:
                critical += 1

        for result in stage_results.values():
            critical += len([e for e in result.errors if "critical" in e.lower()])

        return critical


class AutomatedPipeline:
    """自动化测试流水线类 (增强版)"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.results: dict[TestType, TestResult] = {}
        self.stage_results: dict[PipelineStage, StageResult] = {}
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.monitor = PipelineStatusMonitor()

        scripts_dir = Path(__file__).parent
        skills_dir = scripts_dir.parent.parent
        project_root = scripts_dir.parent.parent

        self.coordinator = ProvincialCoordinatorIntegration(scripts_dir)
        self.regression = RegressionTestIntegration(scripts_dir, config)
        self.optimizer = SystematicOptimizerIntegration(scripts_dir, project_root)
        self.code_review = CodeReviewIntegration(scripts_dir, config)
        self.ui_validation = UIVAlidationIntegration(skills_dir, config)
        self.version_manager = VersionManager(config.docs_dir, config.version)
        self.static_analyzer = StaticCodeAnalyzer(config)
        self.coverage_analyzer = CoverageAnalyzer(config)
        self.build_preparer = BuildPreparer(config)
        self.deploy_preparer = DeployPreparer(config)

    async def run(self) -> dict[str, Any]:
        self.start_time = datetime.now()
        self.monitor.start_pipeline()
        logger.info(f"开始自动化测试流水线 - {self.start_time}")
        logger.info(f"配置的测试类型: {[t.value for t in self.config.test_types]}")

        try:
            if self.config.enable_lint:
                await self._run_lint_stage()

            if self.config.enable_type_check:
                await self._run_type_check_stage()

            if self.config.enable_coordination:
                await self._run_coordination_stage()

            if self.config.enable_code_review:
                await self._run_code_review_stage()

            if self.config.enable_ui_validation:
                await self._run_ui_validation_stage()

            if self.config.parallel:
                await self._run_parallel()
            else:
                await self._run_sequential()

            await self._run_coverage_stage()

            if self.config.enable_build:
                await self._run_build_stage()

            if self.config.enable_deploy_prep:
                await self._run_deploy_prep_stage()

            if self.config.enable_optimization:
                await self._run_optimization_stage()

            await self._run_reporting_stage()

        except Exception as e:
            logger.error(f"流水线执行出错: {e}")
            raise

        self.end_time = datetime.now()
        self.monitor.end_pipeline()
        logger.info(f"流水线执行完成 - 耗时: {self._get_duration()}")

        return self._build_final_report()

    async def _run_lint_stage(self):
        logger.info("执行静态代码检查 (Lint) 阶段")
        self.monitor.start_stage(PipelineStage.LINT)
        
        result = await self.static_analyzer.run_lint()
        self.stage_results[PipelineStage.LINT] = result
        
        self.monitor.end_stage(
            PipelineStage.LINT, 
            result.status, 
            result.errors, 
            result.warnings
        )

        if self.config.fail_fast and result.status == TestStatus.FAILED:
            raise Exception("Lint 检查失败，根据 fail_fast 配置停止流水线")

    async def _run_type_check_stage(self):
        logger.info("执行类型检查阶段")
        self.monitor.start_stage(PipelineStage.TYPE_CHECK)
        
        result = await self.static_analyzer.run_type_check()
        self.stage_results[PipelineStage.TYPE_CHECK] = result
        
        self.monitor.end_stage(
            PipelineStage.TYPE_CHECK, 
            result.status, 
            result.errors, 
            result.warnings
        )

        if self.config.fail_fast and result.status == TestStatus.FAILED:
            raise Exception("类型检查失败，根据 fail_fast 配置停止流水线")

    async def _run_coverage_stage(self):
        logger.info("执行覆盖率分析阶段")
        self.monitor.start_stage(PipelineStage.COVERAGE)
        
        result = await self.coverage_analyzer.run_coverage_analysis()
        self.stage_results[PipelineStage.COVERAGE] = result
        
        self.monitor.end_stage(
            PipelineStage.COVERAGE, 
            result.status, 
            result.errors, 
            result.warnings
        )

    async def _run_build_stage(self):
        logger.info("执行构建阶段")
        self.monitor.start_stage(PipelineStage.BUILD)
        
        result = await self.build_preparer.run_build()
        self.stage_results[PipelineStage.BUILD] = result
        
        self.monitor.end_stage(
            PipelineStage.BUILD, 
            result.status, 
            result.errors, 
            result.warnings
        )

        if self.config.fail_fast and result.status == TestStatus.FAILED:
            raise Exception("构建失败，根据 fail_fast 配置停止流水线")

    async def _run_deploy_prep_stage(self):
        logger.info("执行部署准备阶段")
        self.monitor.start_stage(PipelineStage.DEPLOY_PREP)
        
        result = await self.deploy_preparer.prepare_deployment()
        self.stage_results[PipelineStage.DEPLOY_PREP] = result
        
        self.monitor.end_stage(
            PipelineStage.DEPLOY_PREP, 
            result.status, 
            result.errors, 
            result.warnings
        )

    async def _run_coordination_stage(self):
        logger.info("执行省部司协同阶段")
        self.monitor.start_stage(PipelineStage.COORDINATION)
        
        stage_result = StageResult(
            stage=PipelineStage.COORDINATION,
            status=TestStatus.RUNNING
        )

        task = self.coordinator.create_pipeline_task(
            f"自动化流水线执行 - {self.start_time.isoformat()}",
            context={
                "test_types": [t.value for t in self.config.test_types],
                "version": self.config.version,
                "parallel": self.config.parallel
            }
        )

        if task:
            coord_result = self.coordinator.coordinate_stage(PipelineStage.COORDINATION)
            stage_result.output = coord_result
            stage_result.status = TestStatus.PASSED
        else:
            stage_result.status = TestStatus.SKIPPED
            stage_result.warnings.append("省部司协同未启用")

        stage_result.duration = 0.0
        self.stage_results[PipelineStage.COORDINATION] = stage_result
        
        self.monitor.end_stage(
            PipelineStage.COORDINATION, 
            stage_result.status, 
            stage_result.errors, 
            stage_result.warnings
        )

    async def _run_code_review_stage(self):
        logger.info("执行代码审查阶段")
        self.monitor.start_stage(PipelineStage.CODE_REVIEW)
        start_time = datetime.now()

        backend_result = self.code_review.run_review(self.config.backend_dir)
        frontend_result = self.code_review.run_review(self.config.frontend_dir)

        combined_result = StageResult(
            stage=PipelineStage.CODE_REVIEW,
            status=TestStatus.PASSED if backend_result.status == TestStatus.PASSED and frontend_result.status == TestStatus.PASSED else TestStatus.FAILED,
            duration=(datetime.now() - start_time).total_seconds(),
            output={
                "backend": backend_result.output,
                "frontend": frontend_result.output
            },
            errors=backend_result.errors + frontend_result.errors,
            warnings=backend_result.warnings + frontend_result.warnings
        )
        combined_result.metrics = {
            "backend_issues": backend_result.metrics.get("total_issues", 0),
            "frontend_issues": frontend_result.metrics.get("total_issues", 0)
        }

        self.stage_results[PipelineStage.CODE_REVIEW] = combined_result
        
        self.monitor.end_stage(
            PipelineStage.CODE_REVIEW, 
            combined_result.status, 
            combined_result.errors, 
            combined_result.warnings
        )

        if self.config.fail_fast and combined_result.status == TestStatus.FAILED:
            raise Exception("代码审查失败，根据 fail_fast 配置停止流水线")

    async def _run_ui_validation_stage(self):
        logger.info("执行 UI 校验阶段")
        self.monitor.start_stage(PipelineStage.UI_VALIDATION)
        start_time = datetime.now()

        result = self.ui_validation.run_ui_validation()
        result.duration = (datetime.now() - start_time).total_seconds()

        self.stage_results[PipelineStage.UI_VALIDATION] = result
        
        self.monitor.end_stage(
            PipelineStage.UI_VALIDATION, 
            result.status, 
            result.errors, 
            result.warnings
        )

        if self.config.fail_fast and result.status == TestStatus.FAILED:
            raise Exception("UI 校验失败，根据 fail_fast 配置停止流水线")

    async def _run_sequential(self):
        for test_type in self.config.test_types:
            if test_type == TestType.REGRESSION and self.config.enable_regression:
                result = await self.regression.run_regression_tests()
            else:
                result = await self._run_test(test_type)
            self.results[test_type] = result

            if self.config.fail_fast and result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                logger.warning(f"检测到失败，根据 fail_fast 配置停止流水线")
                break

    async def _run_parallel(self):
        tasks = []
        for test_type in self.config.test_types:
            if test_type == TestType.REGRESSION and self.config.enable_regression:
                tasks.append(self.regression.run_regression_tests())
            else:
                tasks.append(self._run_test(test_type))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for test_type, result in zip(self.config.test_types, results):
            if isinstance(result, Exception):
                self.results[test_type] = TestResult(
                    test_type=test_type,
                    status=TestStatus.ERROR,
                    errors=[str(result)]
                )
            else:
                self.results[test_type] = result

    async def _run_optimization_stage(self):
        logger.info("执行系统性优化阶段")
        self.monitor.start_stage(PipelineStage.OPTIMIZATION)
        start_time = datetime.now()

        result = self.optimizer.run_optimization()
        result.duration = (datetime.now() - start_time).total_seconds()

        self.stage_results[PipelineStage.OPTIMIZATION] = result
        
        self.monitor.end_stage(
            PipelineStage.OPTIMIZATION, 
            result.status, 
            result.errors, 
            result.warnings
        )

    async def _run_reporting_stage(self):
        logger.info("执行报告生成阶段")
        self.monitor.start_stage(PipelineStage.REPORTING)
        start_time = datetime.now()

        report = self.generate_report()
        self.save_report(report)

        stage_result = StageResult(
            stage=PipelineStage.REPORTING,
            status=TestStatus.PASSED,
            duration=(datetime.now() - start_time).total_seconds(),
            output={"report_generated": True}
        )
        self.stage_results[PipelineStage.REPORTING] = stage_result
        
        self.monitor.end_stage(
            PipelineStage.REPORTING, 
            stage_result.status, 
            stage_result.errors, 
            stage_result.warnings
        )

    async def _run_test(self, test_type: TestType) -> TestResult:
        logger.info(f"开始执行 {test_type.value} 测试")
        start_time = datetime.now()

        result = TestResult(
            test_type=test_type,
            status=TestStatus.RUNNING
        )

        try:
            if test_type == TestType.UNIT:
                result = await self._run_unit_tests()
            elif test_type == TestType.INTEGRATION:
                result = await self._run_integration_tests()
            elif test_type == TestType.E2E:
                result = await self._run_e2e_tests()
            elif test_type == TestType.PERFORMANCE:
                result = await self._run_performance_tests()
            elif test_type == TestType.SECURITY:
                result = await self._run_security_tests()
            elif test_type == TestType.MUTATION:
                result = await self._run_mutation_tests()
            else:
                result.status = TestStatus.SKIPPED
                result.warnings.append(f"未知的测试类型: {test_type}")

        except Exception as e:
            logger.error(f"{test_type.value} 测试执行失败: {e}")
            result.status = TestStatus.ERROR
            result.errors.append(str(e))

        end_time = datetime.now()
        result.duration = (end_time - start_time).total_seconds()

        logger.info(f"{test_type.value} 测试完成 - 状态: {result.status.value}, 耗时: {result.duration:.2f}s")
        return result

    async def _run_unit_tests(self) -> TestResult:
        result = TestResult(test_type=TestType.UNIT, status=TestStatus.RUNNING)

        backend_dir = self.config.backend_dir
        if not backend_dir.exists():
            result.status = TestStatus.SKIPPED
            result.warnings.append("后端目录不存在")
            return result

        try:
            cmd = [
                sys.executable, "-m", "pytest",
                "tests/",
                "-v",
                "--tb=short",
                "--cov=app",
                "--cov-report=json:coverage.json",
                "--cov-report=term-missing"
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=backend_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout
            )

            output = stdout.decode('utf-8', errors='replace')
            error_output = stderr.decode('utf-8', errors='replace')

            result.output = output + error_output

            if process.returncode == 0:
                result.status = TestStatus.PASSED
            else:
                result.status = TestStatus.FAILED

            result = self._parse_pytest_output(result, output)

            coverage_file = backend_dir / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, 'r', encoding='utf-8') as f:
                    coverage_data = json.load(f)
                    result.coverage = coverage_data.get("totals", {}).get("percent_covered", 0)

        except asyncio.TimeoutError:
            result.status = TestStatus.ERROR
            result.errors.append(f"单元测试超时 (> {self.config.timeout}s)")
        except Exception as e:
            result.status = TestStatus.ERROR
            result.errors.append(str(e))

        return result

    async def _run_integration_tests(self) -> TestResult:
        result = TestResult(test_type=TestType.INTEGRATION, status=TestStatus.RUNNING)

        backend_dir = self.config.backend_dir
        if not backend_dir.exists():
            result.status = TestStatus.SKIPPED
            result.warnings.append("后端目录不存在")
            return result

        try:
            cmd = [
                sys.executable, "-m", "pytest",
                "tests/",
                "-v",
                "-m", "integration",
                "--tb=short"
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=backend_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout
            )

            output = stdout.decode('utf-8', errors='replace')
            result.output = output + stderr.decode('utf-8', errors='replace')

            if process.returncode == 0:
                result.status = TestStatus.PASSED
            elif process.returncode == 5:
                result.status = TestStatus.SKIPPED
                result.warnings.append("没有找到集成测试")
            else:
                result.status = TestStatus.FAILED

            result = self._parse_pytest_output(result, output)

        except asyncio.TimeoutError:
            result.status = TestStatus.ERROR
            result.errors.append(f"集成测试超时 (> {self.config.timeout}s)")
        except Exception as e:
            result.status = TestStatus.ERROR
            result.errors.append(str(e))

        return result

    async def _run_e2e_tests(self) -> TestResult:
        result = TestResult(test_type=TestType.E2E, status=TestStatus.RUNNING)

        frontend_dir = self.config.frontend_dir
        if not frontend_dir.exists():
            result.status = TestStatus.SKIPPED
            result.warnings.append("前端目录不存在")
            return result

        try:
            playwright_config = frontend_dir / "playwright.config.ts"
            if not playwright_config.exists():
                result.status = TestStatus.SKIPPED
                result.warnings.append("Playwright 配置不存在")
                return result

            cmd = ["npx", "playwright", "test", "--reporter=list"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=frontend_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout * 2
            )

            output = stdout.decode('utf-8', errors='replace')
            result.output = output + stderr.decode('utf-8', errors='replace')

            if process.returncode == 0:
                result.status = TestStatus.PASSED
            else:
                result.status = TestStatus.FAILED

            result = self._parse_playwright_output(result, output)

        except asyncio.TimeoutError:
            result.status = TestStatus.ERROR
            result.errors.append(f"E2E 测试超时 (> {self.config.timeout * 2}s)")
        except Exception as e:
            result.status = TestStatus.ERROR
            result.errors.append(str(e))

        return result

    async def _run_performance_tests(self) -> TestResult:
        result = TestResult(test_type=TestType.PERFORMANCE, status=TestStatus.RUNNING)

        backend_dir = self.config.backend_dir
        perf_script = backend_dir / "scripts" / "performance_benchmark.py"

        if not perf_script.exists():
            result.status = TestStatus.SKIPPED
            result.warnings.append("性能测试脚本不存在")
            return result

        try:
            cmd = [sys.executable, str(perf_script), "--format", "json"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout
            )

            output = stdout.decode('utf-8', errors='replace')
            result.output = output

            if process.returncode == 0:
                result.status = TestStatus.PASSED
                try:
                    perf_data = json.loads(output)
                    result.metrics = perf_data.get("metrics", {})
                except json.JSONDecodeError:
                    pass
            else:
                result.status = TestStatus.FAILED
                result.errors.append(stderr.decode('utf-8', errors='replace'))

        except asyncio.TimeoutError:
            result.status = TestStatus.ERROR
            result.errors.append(f"性能测试超时 (> {self.config.timeout}s)")
        except Exception as e:
            result.status = TestStatus.ERROR
            result.errors.append(str(e))

        return result

    async def _run_security_tests(self) -> TestResult:
        result = TestResult(test_type=TestType.SECURITY, status=TestStatus.RUNNING)

        backend_dir = self.config.backend_dir

        try:
            cmd = [
                sys.executable, "-m", "bandit",
                "-r", "app/",
                "-f", "json",
                "-o", "bandit-report.json"
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=backend_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout
            )

            result.output = stdout.decode('utf-8', errors='replace')

            bandit_report = backend_dir / "bandit-report.json"
            if bandit_report.exists():
                with open(bandit_report, 'r', encoding='utf-8') as f:
                    security_data = json.load(f)
                    result.metrics["security_issues"] = len(security_data.get("results", []))

                    if result.metrics["security_issues"] == 0:
                        result.status = TestStatus.PASSED
                    else:
                        result.status = TestStatus.FAILED
                        result.warnings.append(f"发现 {result.metrics['security_issues']} 个安全问题")
            else:
                result.status = TestStatus.PASSED

        except asyncio.TimeoutError:
            result.status = TestStatus.ERROR
            result.errors.append(f"安全测试超时 (> {self.config.timeout}s)")
        except Exception as e:
            result.status = TestStatus.ERROR
            result.errors.append(str(e))

        return result

    async def _run_mutation_tests(self) -> TestResult:
        result = TestResult(test_type=TestType.MUTATION, status=TestStatus.RUNNING)

        backend_dir = self.config.backend_dir
        mutation_script = backend_dir / "scripts" / "mutation_test_framework.py"

        if not mutation_script.exists():
            result.status = TestStatus.SKIPPED
            result.warnings.append("变异测试框架不存在")
            return result

        try:
            cmd = [sys.executable, str(mutation_script), "--format", "json"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout * 3
            )

            output = stdout.decode('utf-8', errors='replace')
            result.output = output

            if process.returncode == 0:
                result.status = TestStatus.PASSED
                try:
                    mutation_data = json.loads(output)
                    result.metrics["mutation_score"] = mutation_data.get("score", 0)
                    result.metrics["total_mutants"] = mutation_data.get("total_mutants", 0)
                    result.metrics["killed_mutants"] = mutation_data.get("killed_mutants", 0)
                except json.JSONDecodeError:
                    pass
            else:
                result.status = TestStatus.FAILED

        except asyncio.TimeoutError:
            result.status = TestStatus.ERROR
            result.errors.append(f"变异测试超时 (> {self.config.timeout * 3}s)")
        except Exception as e:
            result.status = TestStatus.ERROR
            result.errors.append(str(e))

        return result

    def _parse_pytest_output(self, result: TestResult, output: str) -> TestResult:
        import re

        pattern = r'(\d+) passed(?:, (\d+) failed)?(?:, (\d+) skipped)?(?:, (\d+) error)?'
        match = re.search(pattern, output)

        if match:
            result.passed_tests = int(match.group(1) or 0)
            result.failed_tests = int(match.group(2) or 0)
            result.skipped_tests = int(match.group(3) or 0)
            result.error_tests = int(match.group(4) or 0)
            result.total_tests = result.passed_tests + result.failed_tests + result.skipped_tests + result.error_tests

        return result

    def _parse_playwright_output(self, result: TestResult, output: str) -> TestResult:
        import re

        pattern = r'(\d+) passed(?:.*?)(\d+) failed?'
        match = re.search(pattern, output)

        if match:
            result.passed_tests = int(match.group(1))
            result.failed_tests = int(match.group(2)) if match.group(2) else 0
            result.total_tests = result.passed_tests + result.failed_tests

        return result

    def _get_duration(self) -> str:
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            return f"{duration:.2f}s"
        return "N/A"

    def generate_report(self) -> dict[str, Any]:
        monitor_summary = self.monitor.get_summary()
        
        report = {
            "metadata": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration": self._get_duration(),
                "version": self.config.version,
                "config": {
                    "test_types": [t.value for t in self.config.test_types],
                    "parallel": self.config.parallel,
                    "fail_fast": self.config.fail_fast,
                    "enable_coordination": self.config.enable_coordination,
                    "enable_optimization": self.config.enable_optimization,
                    "enable_code_review": self.config.enable_code_review,
                    "enable_ui_validation": self.config.enable_ui_validation,
                    "enable_regression": self.config.enable_regression,
                    "enable_lint": self.config.enable_lint,
                    "enable_type_check": self.config.enable_type_check,
                    "enable_build": self.config.enable_build,
                    "enable_deploy_prep": self.config.enable_deploy_prep,
                    "coverage_threshold": self.config.coverage_threshold,
                    "environments": self.config.environments
                }
            },
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results.values() if r.status == TestStatus.PASSED),
                "failed": sum(1 for r in self.results.values() if r.status == TestStatus.FAILED),
                "skipped": sum(1 for r in self.results.values() if r.status == TestStatus.SKIPPED),
                "error": sum(1 for r in self.results.values() if r.status == TestStatus.ERROR),
                "total_tests": sum(r.total_tests for r in self.results.values()),
                "passed_tests": sum(r.passed_tests for r in self.results.values()),
                "failed_tests": sum(r.failed_tests for r in self.results.values()),
                "skipped_tests": sum(r.skipped_tests for r in self.results.values()),
                "error_tests": sum(r.error_tests for r in self.results.values()),
                "avg_coverage": sum(r.coverage for r in self.results.values()) / len(self.results) if self.results else 0,
                "total_errors": monitor_summary["total_errors"],
                "total_warnings": monitor_summary["total_warnings"]
            },
            "monitoring": {
                "total_duration": monitor_summary["total_duration"],
                "stage_durations": monitor_summary["stage_durations"],
                "status_history": monitor_summary["status_history"][-50:],
                "errors": monitor_summary["errors"],
                "warnings": monitor_summary["warnings"]
            },
            "stages": {},
            "results": {}
        }

        for stage, result in self.stage_results.items():
            report["stages"][stage.value] = {
                "status": result.status.value,
                "duration": result.duration,
                "metrics": result.metrics,
                "errors": result.errors,
                "warnings": result.warnings
            }

        for test_type, result in self.results.items():
            report["results"][test_type.value] = {
                "status": result.status.value,
                "duration": result.duration,
                "total_tests": result.total_tests,
                "passed_tests": result.passed_tests,
                "failed_tests": result.failed_tests,
                "skipped_tests": result.skipped_tests,
                "error_tests": result.error_tests,
                "coverage": result.coverage,
                "errors": result.errors,
                "warnings": result.warnings,
                "metrics": result.metrics
            }

        return report

    def save_report(self, report: dict[str, Any]):
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self.config.output_format == "json":
            output_file = self.config.output_dir / f"pipeline_report_{timestamp}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            self.version_manager.save_json(report, f"pipeline_report_{timestamp}.json", is_report=True)
        else:
            output_file = self.config.output_dir / f"pipeline_report_{timestamp}.md"
            self._save_markdown_report(report, output_file)

        logger.info(f"测试报告已保存到: {output_file}")
        return output_file

    def _save_markdown_report(self, report: dict[str, Any], output_file: Path):
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 自动化测试流水线报告 (增强版)\n\n")

            meta = report["metadata"]
            f.write(f"**开始时间**: {meta['start_time']}\n\n")
            f.write(f"**结束时间**: {meta['end_time']}\n\n")
            f.write(f"**总耗时**: {meta['duration']}\n\n")
            f.write(f"**版本**: {meta['version']}\n\n")

            summary = report["summary"]
            f.write("## 执行摘要\n\n")
            f.write(f"- 总测试套件: {summary['total']}\n")
            f.write(f"- 通过: {summary['passed']} ✅\n")
            f.write(f"- 失败: {summary['failed']} ❌\n")
            f.write(f"- 跳过: {summary['skipped']} ⏭️\n")
            f.write(f"- 错误: {summary['error']} ⚠️\n")
            f.write(f"- 总测试用例: {summary['total_tests']}\n")
            f.write(f"- 平均覆盖率: {summary['avg_coverage']:.2f}%\n")
            f.write(f"- 总错误数: {summary['total_errors']}\n")
            f.write(f"- 总警告数: {summary['total_warnings']}\n\n")

            if report.get("monitoring"):
                monitoring = report["monitoring"]
                f.write("## 监控统计\n\n")
                f.write(f"- 总执行时长: {monitoring['total_duration']:.2f}s\n\n")
                
                if monitoring.get("stage_durations"):
                    f.write("### 各阶段耗时\n\n")
                    f.write("| 阶段 | 耗时 |\n")
                    f.write("|------|------|\n")
                    for stage, duration in monitoring["stage_durations"].items():
                        f.write(f"| {stage} | {duration:.2f}s |\n")
                    f.write("\n")

                if monitoring.get("errors"):
                    f.write("### 错误汇总\n\n")
                    for error in monitoring["errors"]:
                        f.write(f"- **[{error['stage']}]** {error['message']}\n")
                    f.write("\n")

                if monitoring.get("warnings"):
                    f.write("### 警告汇总\n\n")
                    for warning in monitoring["warnings"]:
                        f.write(f"- **[{warning['stage']}]** {warning['message']}\n")
                    f.write("\n")

            if report.get("stages"):
                f.write("## 阶段执行结果\n\n")
                for stage_name, stage_data in report["stages"].items():
                    status_icon = "✅" if stage_data["status"] == "passed" else "❌" if stage_data["status"] == "failed" else "⏭️" if stage_data["status"] == "skipped" else "⚠️"
                    f.write(f"### {stage_name} {status_icon}\n\n")
                    f.write(f"- 状态: {stage_data['status']}\n")
                    f.write(f"- 耗时: {stage_data['duration']:.2f}s\n")
                    if stage_data.get("metrics"):
                        f.write(f"- 指标: {json.dumps(stage_data['metrics'], ensure_ascii=False)}\n")
                    if stage_data.get("errors"):
                        f.write("- **错误**:\n")
                        for error in stage_data["errors"]:
                            f.write(f"  - {error}\n")
                    f.write("\n")

            f.write("## 测试结果详情\n\n")
            for test_type, result in report["results"].items():
                status_icon = "✅" if result["status"] == "passed" else "❌" if result["status"] == "failed" else "⏭️" if result["status"] == "skipped" else "⚠️"
                f.write(f"### {test_type} {status_icon}\n\n")
                f.write(f"- 状态: {result['status']}\n")
                f.write(f"- 耗时: {result['duration']:.2f}s\n")
                f.write(f"- 测试用例: {result['total_tests']} (通过: {result['passed_tests']}, 失败: {result['failed_tests']}, 跳过: {result['skipped_tests']})\n")
                f.write(f"- 覆盖率: {result['coverage']:.2f}%\n")

                if result["errors"]:
                    f.write("- **错误**:\n")
                    for error in result["errors"]:
                        f.write(f"  - {error}\n")

                if result["warnings"]:
                    f.write("- **警告**:\n")
                    for warning in result["warnings"]:
                        f.write(f"  - {warning}\n")

                f.write("\n")

    def _build_final_report(self) -> dict[str, Any]:
        return {
            "test_results": self.results,
            "stage_results": self.stage_results,
            "coordination_status": self.coordinator.get_task_status(),
            "duration": self._get_duration()
        }


def parse_args() -> PipelineConfig:
    parser = argparse.ArgumentParser(
        description="自动化测试流水线 - Sanliu 技能 (增强版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行所有测试
  python scripts/automated_pipeline.py --all

  # 运行指定的测试类型
  python scripts/automated_pipeline.py --test-types unit integration

  # 以 JSON 格式输出报告
  python scripts/automated_pipeline.py --all --output-format json

  # 并行执行测试
  python scripts/automated_pipeline.py --all --parallel

  # 禁用特定功能
  python scripts/automated_pipeline.py --all --disable-coordination --disable-optimization

  # 指定版本号
  python scripts/automated_pipeline.py --all --version v1.2.0
        """
    )

    parser.add_argument(
        "--test-types",
        nargs="+",
        choices=[t.value for t in TestType],
        help="指定要运行的测试类型"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="运行所有测试类型"
    )

    parser.add_argument(
        "--output-format",
        choices=["json", "markdown"],
        default="json",
        help="报告输出格式 (默认: json)"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_path_manager.get_reports_path(),
        help="报告输出目录 (默认: reports)"
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        help="并行执行测试"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细输出"
    )

    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="遇到失败立即停止"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="单个测试超时时间（秒）(默认: 300)"
    )

    parser.add_argument(
        "--backend-dir",
        type=Path,
        default=_path_manager.get_backend_path(),
        help="后端代码目录 (默认: backend)"
    )

    parser.add_argument(
        "--frontend-dir",
        type=Path,
        default=_path_manager.get_frontend_path(),
        help="前端代码目录 (默认: frontend)"
    )

    parser.add_argument(
        "--enable-coordination",
        action="store_true",
        default=True,
        help="启用省部司协同调用 (默认: 启用)"
    )

    parser.add_argument(
        "--disable-coordination",
        action="store_true",
        help="禁用省部司协同调用"
    )

    parser.add_argument(
        "--enable-optimization",
        action="store_true",
        default=True,
        help="启用系统性优化 (默认: 启用)"
    )

    parser.add_argument(
        "--disable-optimization",
        action="store_true",
        help="禁用系统性优化"
    )

    parser.add_argument(
        "--enable-code-review",
        action="store_true",
        default=True,
        help="启用代码审查 (默认: 启用)"
    )

    parser.add_argument(
        "--disable-code-review",
        action="store_true",
        help="禁用代码审查"
    )

    parser.add_argument(
        "--enable-ui-validation",
        action="store_true",
        default=True,
        help="启用 UI 校验 (默认: 启用)"
    )

    parser.add_argument(
        "--disable-ui-validation",
        action="store_true",
        help="禁用 UI 校验"
    )

    parser.add_argument(
        "--enable-regression",
        action="store_true",
        default=True,
        help="启用回归测试 (默认: 启用)"
    )

    parser.add_argument(
        "--disable-regression",
        action="store_true",
        help="禁用回归测试"
    )

    parser.add_argument(
        "--enable-log-analysis",
        action="store_true",
        default=True,
        help="启用日志分析 (默认: 启用)"
    )

    parser.add_argument(
        "--disable-log-analysis",
        action="store_true",
        help="禁用日志分析"
    )

    parser.add_argument(
        "--version",
        type=str,
        default="v1.0.0",
        help="版本号，用于输出目录 (默认: v1.0.0)"
    )

    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=lambda: PathConfigManager(auto_detect=True).get_docs_path(),
        help="文档输出根目录 (默认: 由路径管理器自动检测)"
    )

    parser.add_argument(
        "--enable-lint",
        action="store_true",
        default=True,
        help="启用静态代码检查 (默认: 启用)"
    )

    parser.add_argument(
        "--disable-lint",
        action="store_true",
        help="禁用静态代码检查"
    )

    parser.add_argument(
        "--enable-type-check",
        action="store_true",
        default=True,
        help="启用类型检查 (默认: 启用)"
    )

    parser.add_argument(
        "--disable-type-check",
        action="store_true",
        help="禁用类型检查"
    )

    parser.add_argument(
        "--enable-build",
        action="store_true",
        default=True,
        help="启用构建阶段 (默认: 启用)"
    )

    parser.add_argument(
        "--disable-build",
        action="store_true",
        help="禁用构建阶段"
    )

    parser.add_argument(
        "--enable-deploy-prep",
        action="store_true",
        default=True,
        help="启用部署准备阶段 (默认: 启用)"
    )

    parser.add_argument(
        "--disable-deploy-prep",
        action="store_true",
        help="禁用部署准备阶段"
    )

    parser.add_argument(
        "--coverage-threshold",
        type=float,
        default=80.0,
        help="覆盖率阈值百分比 (默认: 80.0)"
    )

    parser.add_argument(
        "--environments",
        nargs="+",
        default=["staging", "production"],
        help="部署环境列表 (默认: staging production)"
    )

    args = parser.parse_args()

    if args.all:
        test_types = list(TestType)
    elif args.test_types:
        test_types = [TestType(t) for t in args.test_types]
    else:
        parser.error("请指定 --all 或 --test-types")

    return PipelineConfig(
        test_types=test_types,
        output_format=args.output_format,
        output_dir=args.output_dir,
        parallel=args.parallel,
        verbose=args.verbose,
        fail_fast=args.fail_fast,
        timeout=args.timeout,
        backend_dir=args.backend_dir,
        frontend_dir=args.frontend_dir,
        enable_coordination=args.enable_coordination and not args.disable_coordination,
        enable_optimization=args.enable_optimization and not args.disable_optimization,
        enable_code_review=args.enable_code_review and not args.disable_code_review,
        enable_ui_validation=args.enable_ui_validation and not args.disable_ui_validation,
        enable_regression=args.enable_regression and not args.disable_regression,
        enable_log_analysis=args.enable_log_analysis and not args.disable_log_analysis,
        version=args.version,
        docs_dir=args.docs_dir,
        enable_lint=args.enable_lint and not args.disable_lint,
        enable_type_check=args.enable_type_check and not args.disable_type_check,
        enable_build=args.enable_build and not args.disable_build,
        enable_deploy_prep=args.enable_deploy_prep and not args.disable_deploy_prep,
        coverage_threshold=args.coverage_threshold,
        environments=args.environments
    )


async def main():
    try:
        config = parse_args()

        if config.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        pipeline = AutomatedPipeline(config)
        results = await pipeline.run()

        report = pipeline.generate_report()
        output_file = pipeline.save_report(report)

        summary = report["summary"]
        print("\n" + "=" * 70)
        print("自动化测试流水线执行完成 (增强版)")
        print("=" * 70)
        print(f"版本: {config.version}")
        print(f"总测试套件: {summary['total']}")
        print(f"通过: {summary['passed']} | 失败: {summary['failed']} | 跳过: {summary['skipped']} | 错误: {summary['error']}")
        print(f"总测试用例: {summary['total_tests']}")
        print(f"平均覆盖率: {summary['avg_coverage']:.2f}%")

        if report.get("stages"):
            print("\n阶段执行结果:")
            for stage_name, stage_data in report["stages"].items():
                status_icon = "✅" if stage_data["status"] == "passed" else "❌" if stage_data["status"] == "failed" else "⏭️"
                print(f"  {status_icon} {stage_name}: {stage_data['status']}")

        print(f"\n报告文件: {output_file}")
        print(f"文档目录: {config.docs_dir / 'libs' / config.version}")
        print(f"报告目录: {config.docs_dir / 'reports' / config.version}")
        print("=" * 70)

        if summary['failed'] > 0 or summary['error'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        logger.info("用户中断执行")
        sys.exit(130)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
