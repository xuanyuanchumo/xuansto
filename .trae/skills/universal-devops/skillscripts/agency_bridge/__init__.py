"""
Agency-Agent Bridge (AAB) 模块

桥接 universal-devops 的三省六部二十四司架构与 agency-agents 中的 144+ 专业 AI 智能体。
提供 Agent 注册、路由、编排、部门映射、上下文构建和结果收集等核心功能。
"""
from __future__ import annotations

from .agent_registry import AgentRegistry, AgentMetadata, RegistryStats
from .agent_router import AgentRouter, RoutingRequest, RoutingResult
from .agent_orchestrator import (
    AgentOrchestrator,
    OrchestrationPhase,
    OrchestrationSession,
    PipelineStage,
)
from .department_mapper import DepartmentMapper, DepartmentID, MappingEntry
from .agent_context_builder import AgentContextBuilder, AgentContext
from .agent_result_collector import (
    AgentResultCollector,
    AgentResult,
    CollectedResult,
    ConflictResolutionStrategy,
)

__all__ = [
    "AgentRegistry",
    "AgentMetadata",
    "RegistryStats",
    "AgentRouter",
    "RoutingRequest",
    "RoutingResult",
    "AgentOrchestrator",
    "OrchestrationPhase",
    "OrchestrationSession",
    "PipelineStage",
    "DepartmentMapper",
    "DepartmentID",
    "MappingEntry",
    "AgentContextBuilder",
    "AgentContext",
    "AgentResultCollector",
    "AgentResult",
    "CollectedResult",
    "ConflictResolutionStrategy",
]
