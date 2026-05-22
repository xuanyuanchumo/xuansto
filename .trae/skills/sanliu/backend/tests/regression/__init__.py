"""
回归测试套件

提供完整的回归测试功能，包括：
- 项目管理功能测试
- 任务管理功能测试
- 用户认证功能测试
- 报告生成功能测试
- 智能测试选择
- 报告生成
"""

from .regression_config import (
    RegressionTestConfig,
    TestSuiteDefinition,
    TestPriority,
    TestCategory,
    ExecutionStrategy,
    REGRESSION_TEST_SUITES,
    PRIORITY_EXECUTION_ORDER,
    CRITICAL_ASSERTIONS,
)

from .intelligent_selector import (
    IntelligentTestSelector,
    SelectionStrategy,
    SelectionResult,
    TestInfo,
    CodeChange,
)

from .report_generator import (
    RegressionReportGenerator,
    RegressionReport,
    TestSuiteResult,
    TestResult,
    TestStatus,
    ReportFormat,
)

__all__ = [
    "RegressionTestConfig",
    "TestSuiteDefinition",
    "TestPriority",
    "TestCategory",
    "ExecutionStrategy",
    "REGRESSION_TEST_SUITES",
    "PRIORITY_EXECUTION_ORDER",
    "CRITICAL_ASSERTIONS",
    "IntelligentTestSelector",
    "SelectionStrategy",
    "SelectionResult",
    "TestInfo",
    "CodeChange",
    "RegressionReportGenerator",
    "RegressionReport",
    "TestSuiteResult",
    "TestResult",
    "TestStatus",
    "ReportFormat",
]
