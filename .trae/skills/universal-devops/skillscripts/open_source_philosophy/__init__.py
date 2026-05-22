"""
Universal DevOps v6.0 - Open Source Philosophy Integration Module
开源理念深化模块：将OpenCode/OpenClaude/Claw-Code/Harness的设计理念从功能映射升级为架构级内化实现

本模块提供四大开源理念的深度集成：
- OpenCode Transparency: 透明化决策引擎，自动生成Decision Log和DX评分
- OpenClaude Orchestrator: Agent编排增强，YAML声明式工作流DSL
- Claw-Code SDD/TDD Engine: 契约驱动开发和测试闭环反馈
- Philosophy Integration: 理念融合协调器，统一入口和冲突解决
"""

from .opencode_transparency import (
    OpenCodeTransparency,
    DecisionRecord,
    Alternative,
    RiskAssessment,
    DXScore,
    RiskLevel,
    ComplexityLevel,
)

from .openclaude_orchestrator import (
    OpenClaudeOrchestrator,
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowStep,
    ContextInjector,
)

from .clawcode_sdd_tdd_engine import (
    ClawCodeSDDTDDEngine,
    SDDExecutableClause,
    SDDCoverageReport,
    ClauseCategory,
    Priority,
    ClauseStatus,
    CategoryCoverage,
)

from .philosophy_integration import (
    PhilosophyIntegration,
    PhilosophyConflictResolver,
    BestPracticeRecommender,
    PhilosophyEffectivenessEvaluator,
)

__all__ = [
    "OpenCodeTransparency",
    "DecisionRecord",
    "Alternative",
    "RiskAssessment",
    "DXScore",
    "RiskLevel",
    "ComplexityLevel",
    "OpenClaudeOrchestrator",
    "WorkflowEngine",
    "WorkflowDefinition",
    "WorkflowStep",
    "ContextInjector",
    "ClawCodeSDDTDDEngine",
    "SDDExecutableClause",
    "SDDCoverageReport",
    "ClauseCategory",
    "Priority",
    "ClauseStatus",
    "CategoryCoverage",
    "PhilosophyIntegration",
    "PhilosophyConflictResolver",
    "BestPracticeRecommender",
    "PhilosophyEffectivenessEvaluator",
]

__version__ = "6.0.0"
__author__ = "Universal DevOps Team"
