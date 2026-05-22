# 持续演化系统模块 - 自迭代、自优化、自修复、自改进
from .self_iterator import SelfIterator, ProblemType, Prediction, OptimizationStrategy, ImprovementPlan, IterationEffect
from .self_optimizer import SelfOptimizer, RuntimeMetrics, BottleneckDiagnosis, OptimizedConfig, ResourceUsage, AllocationAdjustment, OptimizationTracking
from .self_repairer import SelfRepairer, RepairRule, RepairResult, Checkpoint, VerificationResult, ErrorPattern
from .self_improver import SelfImprover, SuccessCase, KnowledgeItem, BestPractice, AntiPattern, CodePattern, SharingResult, QualityScore
from .evolution_controller import EvolutionController, EvolutionTrigger, EvolutionCycleReport, EvolutionEvent, EvolutionState, EvolutionMode, EvolutionPhase

__all__ = [
    "SelfIterator", "ProblemType", "Prediction", "OptimizationStrategy",
    "ImprovementPlan", "IterationEffect",
    "SelfOptimizer", "RuntimeMetrics", "BottleneckDiagnosis", "OptimizedConfig",
    "ResourceUsage", "AllocationAdjustment", "OptimizationTracking",
    "SelfRepairer", "RepairRule", "RepairResult", "Checkpoint",
    "VerificationResult", "ErrorPattern",
    "SelfImprover", "SuccessCase", "KnowledgeItem", "BestPractice",
    "AntiPattern", "CodePattern", "SharingResult", "QualityScore",
    "EvolutionController", "EvolutionTrigger", "EvolutionCycleReport",
    "EvolutionEvent", "EvolutionState", "EvolutionMode", "EvolutionPhase",
]
