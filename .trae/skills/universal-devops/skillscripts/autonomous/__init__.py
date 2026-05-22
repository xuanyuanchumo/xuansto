"""
AI自主操作框架 (Autonomous Operation Framework, AOF)
=====================================================
提供感知-决策-执行-反馈的完整自主操作闭环能力。
包含五层架构：感知层、决策层、执行层、反馈学习层、双模协调器。

模块组成：
- perceive_layer: 自主感知层 - 代码上下文理解、项目状态采集、质量指标读取、历史模式挖掘
- decide_layer: 自主决策层 - 多准则决策引擎、风险评估、trade-off分析、策略选择
- execute_layer: 自主执行层 - 安全编辑、影响评估、回滚管理、执行验证
- feedback_learning_layer: 反馈学习层 - 结果验证、模式积累、策略调优、知识提炼
- dual_mode_coordinator: 双模协调器 - 模式选择/切换、混合编排、操作治理

增强模块（V2）：
- operation_decider: 多因子操作决策引擎 - 6种规则场景、4维决策因子
- preflight_checker: 预飞检查器 V2 - 35+危险模式检测、7大类别
- transaction_manager: 操作事务管理器 - ACID保证、保存点机制
- operation_logger: 操作审计日志记录器 - 完整轨迹追踪
"""

from .perceive_layer import (
    ContextPerceiver,
    ProjectStateCollector,
    QualityMetricsReader,
    HistoricalPatternMiner,
    PerceptionReport,
)

from .decide_layer import (
    MultiCriteriaDecisionEngine,
    RiskAssessor,
    TradeOffAnalyzer,
    StrategySelector,
    Decision,
    RiskLevel,
)

from .execute_layer import (
    SafeEditor,
    ImpactAssessor,
    RollbackManager,
    ExecutionValidator,
    ExecutionResult,
    ExecutionStatus,
)

from .feedback_learning_layer import (
    ResultVerifier,
    PatternAccumulator,
    StrategyTuner,
    KnowledgeDistiller,
    LearningInsight,
)

from .dual_mode_coordinator import (
    ModeSelector,
    ModeSwitcher,
    HybridOrchestrator,
    OperationGovernor,
    OperatingMode,
    CoordinationResult,
    BatchOperationRequest,
    DryRunResult,
    BatchExecutionResult,
)

from .operation_decider import (
    OperationDecider,
    OperationMode,
    TaskComplexity,
    TaskContext,
    OperationDecision,
    DecisionFactor,
)

from .preflight_checker import (
    PreflightChecker,
    RiskSeverity,
    PreflightResultV2,
    PatternMatch,
)

from .transaction_manager import (
    TransactionManager,
    TransactionState,
    FileOpType,
    FileOperation,
    SavePoint,
    TransactionStatus,
    TransactionInfo,
)

from .operation_logger import (
    OperationLogger,
    OperationType,
    OperationRecord,
    AuditReport,
)

__all__ = [
    "ContextPerceiver",
    "ProjectStateCollector",
    "QualityMetricsReader",
    "HistoricalPatternMiner",
    "PerceptionReport",
    "MultiCriteriaDecisionEngine",
    "RiskAssessor",
    "TradeOffAnalyzer",
    "StrategySelector",
    "Decision",
    "RiskLevel",
    "SafeEditor",
    "ImpactAssessor",
    "RollbackManager",
    "ExecutionValidator",
    "ExecutionResult",
    "ExecutionStatus",
    "ResultVerifier",
    "PatternAccumulator",
    "StrategyTuner",
    "KnowledgeDistiller",
    "LearningInsight",
    "ModeSelector",
    "ModeSwitcher",
    "HybridOrchestrator",
    "OperationGovernor",
    "OperatingMode",
    "CoordinationResult",
    "BatchOperationRequest",
    "DryRunResult",
    "BatchExecutionResult",
    "OperationDecider",
    "OperationMode",
    "TaskComplexity",
    "TaskContext",
    "OperationDecision",
    "DecisionFactor",
    "PreflightChecker",
    "RiskSeverity",
    "PreflightResultV2",
    "PatternMatch",
    "TransactionManager",
    "TransactionState",
    "FileOpType",
    "FileOperation",
    "SavePoint",
    "TransactionStatus",
    "TransactionInfo",
    "OperationLogger",
    "OperationType",
    "OperationRecord",
    "AuditReport",
]
