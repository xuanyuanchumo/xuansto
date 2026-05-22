#!/usr/bin/env python3
"""
自动迭代与自完善机制模块

该模块实现了三省六部技能的自动迭代与自完善机制，包括：
- 增强版版本迭代器
- 自完善循环系统
- 迭代触发器
- 迭代效果评估
"""

from .enhanced_version_iterator import (
    EnhancedVersionIterator,
    SemanticVersion,
    VersionBumpType,
    ChangeType,
    ChangeEntry,
    VersionSnapshot,
    ChangelogGenerator
)

from .self_improvement_cycle import (
    SelfImprovementCycle,
    IssueDiscoveryEngine,
    IssueAnalyzer,
    FixExecutor,
    VerificationEngine,
    LearningEngine,
    OptimizationApplier
)

from .iteration_trigger_system import (
    IterationTriggerSystem,
    TriggerType,
    ScheduledTrigger,
    EventTrigger,
    ThresholdTrigger,
    ManualTrigger
)

from .iteration_effect_evaluator import (
    IterationEffectEvaluator,
    EffectMetrics,
    ComparisonReport,
    IterationHistoryAnalyzer
)

__version__ = "1.0.0"
__all__ = [
    "EnhancedVersionIterator",
    "SemanticVersion",
    "VersionBumpType",
    "ChangeType",
    "ChangeEntry",
    "VersionSnapshot",
    "ChangelogGenerator",
    "SelfImprovementCycle",
    "IssueDiscoveryEngine",
    "IssueAnalyzer",
    "FixExecutor",
    "VerificationEngine",
    "LearningEngine",
    "OptimizationApplier",
    "IterationTriggerSystem",
    "TriggerType",
    "ScheduledTrigger",
    "EventTrigger",
    "ThresholdTrigger",
    "ManualTrigger",
    "IterationEffectEvaluator",
    "EffectMetrics",
    "ComparisonReport",
    "IterationHistoryAnalyzer",
]
