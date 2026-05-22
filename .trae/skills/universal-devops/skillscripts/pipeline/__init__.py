# 融合引擎模块 - SDD+TDD融合引擎及闭环验证器
from .sdd_spec_parser import SDDSpecParser, SpecSection, SDDSpec, SDDRequirement, APIContract, DataModel, BusinessRule, AcceptanceCriterion, CoverageReport
from .sdd_tdd_fusion_engine import SDDTDDFusionEngine, FusionPhase, FusionReport, TestMapping, CodeGuidance, FeedbackReport, FusionMetrics
from .tdd_executor import TDDExecutor, TDDState, RedPhaseResult, GreenPhaseResult, BluePhaseResult, CycleStats, DisciplineReport, TDDSession
from .closed_loop_verifier import ClosedLoopVerifier, CompletenessReport, CoverageGapReport, DeviationReport, EffectivenessAssessment, RegressionRiskReport

__all__ = [
    "SDDSpecParser", "SpecSection", "SDDSpec", "SDDRequirement", "APIContract",
    "DataModel", "BusinessRule", "AcceptanceCriterion", "CoverageReport",
    "SDDTDDFusionEngine", "FusionPhase", "FusionReport", "TestMapping",
    "CodeGuidance", "FeedbackReport", "FusionMetrics",
    "TDDExecutor", "TDDState", "RedPhaseResult", "GreenPhaseResult",
    "BluePhaseResult", "CycleStats", "DisciplineReport", "TDDSession",
    "ClosedLoopVerifier", "CompletenessReport", "CoverageGapReport",
    "DeviationReport", "EffectivenessAssessment", "RegressionRiskReport",
]
