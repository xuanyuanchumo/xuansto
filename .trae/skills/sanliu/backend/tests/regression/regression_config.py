"""
回归测试套件配置

定义回归测试的核心配置、测试优先级和执行策略
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class TestPriority(Enum):
    P0_CRITICAL = "p0_critical"
    P1_HIGH = "p1_high"
    P2_MEDIUM = "p2_medium"
    P3_LOW = "p3_low"


class TestCategory(Enum):
    PROJECT_MANAGEMENT = "project_management"
    TASK_MANAGEMENT = "task_management"
    USER_AUTHENTICATION = "user_authentication"
    REPORT_GENERATION = "report_generation"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"


class ExecutionStrategy(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PRIORITY_BASED = "priority_based"
    IMPACT_BASED = "impact_based"


@dataclass
class RegressionTestConfig:
    source_dirs: List[str] = field(default_factory=lambda: ["backend/app"])
    test_dirs: List[str] = field(default_factory=lambda: ["backend/tests"])
    output_dir: str = "docs/reports/regression"
    baseline_file: str = "test_baseline.json"
    history_file: str = "test_history.json"
    coverage_threshold: float = 70.0
    parallel_workers: int = 4
    timeout_seconds: int = 300
    retry_count: int = 2
    fail_fast: bool = False
    enable_coverage: bool = True
    enable_performance_tracking: bool = True
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", ".venv", "venv", "node_modules", "migrations"
    ])


@dataclass
class TestSuiteDefinition:
    name: str
    category: TestCategory
    priority: TestPriority
    test_files: List[str]
    description: str
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    estimated_duration: float = 0.0
    critical_threshold: float = 0.0


REGRESSION_TEST_SUITES: Dict[str, TestSuiteDefinition] = {
    "project_management": TestSuiteDefinition(
        name="项目管理功能回归测试",
        category=TestCategory.PROJECT_MANAGEMENT,
        priority=TestPriority.P0_CRITICAL,
        test_files=[
            "backend/tests/api/test_projects.py",
        ],
        description="验证项目创建、更新、删除、查询等核心功能",
        tags=["api", "project", "crud"],
        estimated_duration=60.0,
        critical_threshold=100.0
    ),
    "task_management": TestSuiteDefinition(
        name="任务管理功能回归测试",
        category=TestCategory.TASK_MANAGEMENT,
        priority=TestPriority.P0_CRITICAL,
        test_files=[
            "backend/tests/api/test_tasks.py",
        ],
        description="验证任务创建、分配、状态更新、依赖管理等核心功能",
        tags=["api", "task", "crud"],
        estimated_duration=45.0,
        critical_threshold=100.0
    ),
    "user_authentication": TestSuiteDefinition(
        name="用户认证功能回归测试",
        category=TestCategory.USER_AUTHENTICATION,
        priority=TestPriority.P0_CRITICAL,
        test_files=[
            "backend/tests/test_security.py",
        ],
        description="验证用户认证、授权、会话管理等安全功能",
        tags=["api", "auth", "security"],
        estimated_duration=30.0,
        critical_threshold=100.0
    ),
    "report_generation": TestSuiteDefinition(
        name="报告生成功能回归测试",
        category=TestCategory.REPORT_GENERATION,
        priority=TestPriority.P1_HIGH,
        test_files=[
            "backend/tests/test_report_services.py",
        ],
        description="验证统计报告、风险分析、进度报告等生成功能",
        tags=["service", "report", "statistics"],
        estimated_duration=40.0,
        critical_threshold=90.0
    ),
    "workflow": TestSuiteDefinition(
        name="工作流功能回归测试",
        category=TestCategory.WORKFLOW,
        priority=TestPriority.P1_HIGH,
        test_files=[
            "backend/tests/test_workflow_services.py",
            "backend/tests/services/test_workflow_executor.py",
        ],
        description="验证工作流执行、状态转换、验证器等功能",
        tags=["service", "workflow"],
        estimated_duration=35.0,
        critical_threshold=90.0
    ),
    "integration": TestSuiteDefinition(
        name="集成测试回归套件",
        category=TestCategory.INTEGRATION,
        priority=TestPriority.P2_MEDIUM,
        test_files=[
            "backend/tests/test_integration.py",
            "backend/tests/test_pipeline_services.py",
        ],
        description="验证系统各模块集成后的端到端功能",
        tags=["integration", "e2e"],
        estimated_duration=90.0,
        critical_threshold=80.0
    ),
}


PRIORITY_EXECUTION_ORDER = [
    TestPriority.P0_CRITICAL,
    TestPriority.P1_HIGH,
    TestPriority.P2_MEDIUM,
    TestPriority.P3_LOW,
]


CRITICAL_ASSERTIONS = {
    "project_management": [
        "test_create_project_success",
        "test_list_projects_with_data",
        "test_get_project_success",
        "test_update_project_success",
        "test_delete_project_success",
    ],
    "task_management": [
        "test_create_task_success",
        "test_list_tasks_with_data",
        "test_get_task_detail_success",
        "test_update_task_success",
        "test_delete_task_success",
    ],
    "user_authentication": [
        "test_authentication_flow",
        "test_authorization_check",
        "test_session_management",
    ],
    "report_generation": [
        "test_generate_report",
        "test_collect_tasks",
        "test_analyze_risks",
    ],
}
