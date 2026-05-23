from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from xuansto_mcp.models.schemas import (
    DisclosureTransition,
    SkillAnalyzeInput,
    KnowledgeSearchInput,
    QualityGateCheckInput,
    SpecDriftDetectInput,
    SecurityScanInput,
    CodeSimplifyInput,
    SessionManageInput,
    WorkflowDispatchInput,
    AgentStatusInput,
    AgentManageInput,
    HookManageInput,
    ResourceLoadStatusInput,
    ServerHealthInput,
    ContextCompressInput,
    DecisionLogInput,
    TokenBudgetInput,
    ProjectInitInput,
    KnowledgeInjectInput,
    MetricsReportInput,
    ConfigManageInput,
)


_ACTION_MODELS = [
    (KnowledgeSearchInput, "action"),
    (SessionManageInput, "action"),
    (WorkflowDispatchInput, "action"),
    (AgentStatusInput, "action"),
    (AgentManageInput, "action"),
    (HookManageInput, "action"),
    (ResourceLoadStatusInput, "action"),
    (ServerHealthInput, "action"),
    (DecisionLogInput, "action"),
    (TokenBudgetInput, "action"),
    (ProjectInitInput, "action"),
    (KnowledgeInjectInput, "action"),
    (MetricsReportInput, "action"),
    (ConfigManageInput, "action"),
    (ContextCompressInput, "content"),
]


def test_knowledge_search_input_only_retrieve():
    instance = KnowledgeSearchInput(action="retrieve", query="test")
    assert instance.action == "retrieve"


def test_knowledge_search_input_rejects_other_action():
    with pytest.raises(PydanticValidationError):
        KnowledgeSearchInput(action="delete", query="test")


def test_agent_status_input_query_actions():
    for action in ("list", "by_phase", "detail", "match", "merge"):
        instance = AgentStatusInput(action=action)
        assert instance.action == action


def test_agent_status_input_rejects_invalid():
    with pytest.raises(PydanticValidationError):
        AgentStatusInput(action="create")


def test_agent_manage_input_mutation_actions():
    for action in ("create", "assign", "release", "instance_status", "destroy", "schedule"):
        instance = AgentManageInput(action=action)
        assert instance.action == action


def test_agent_manage_input_rejects_query_action():
    with pytest.raises(PydanticValidationError):
        AgentManageInput(action="list")


def test_action_field_is_required():
    for model_cls, field_name in _ACTION_MODELS:
        with pytest.raises(PydanticValidationError):
            model_cls()


def test_disclosure_transition_model():
    instance = DisclosureTransition(from_phase="phase1", to_phase="phase2")
    assert instance.from_phase == "phase1"
    assert instance.to_phase == "phase2"
    assert instance.status == "pending"


def test_disclosure_transition_status_literal():
    for status in ("pending", "in_progress", "completed", "failed"):
        instance = DisclosureTransition(status=status)
        assert instance.status == status


def test_disclosure_transition_invalid_status():
    with pytest.raises(PydanticValidationError):
        DisclosureTransition(status="invalid")


def test_disclosure_transition_extra_forbid():
    with pytest.raises(PydanticValidationError):
        DisclosureTransition(unknown_field="value")


def test_skill_analyze_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        SkillAnalyzeInput(skill_path="/tmp", unknown_field="x")


def test_knowledge_search_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        KnowledgeSearchInput(action="retrieve", unknown_field="x")


def test_quality_gate_check_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        QualityGateCheckInput(unknown_field="x")


def test_spec_drift_detect_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        SpecDriftDetectInput(unknown_field="x")


def test_security_scan_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        SecurityScanInput(unknown_field="x")


def test_code_simplify_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        CodeSimplifyInput(target="/tmp", unknown_field="x")


def test_session_manage_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        SessionManageInput(action="save", unknown_field="x")


def test_workflow_dispatch_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        WorkflowDispatchInput(action="start", unknown_field="x")


def test_agent_status_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        AgentStatusInput(action="list", unknown_field="x")


def test_agent_manage_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        AgentManageInput(action="create", unknown_field="x")


def test_hook_manage_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        HookManageInput(action="list", unknown_field="x")


def test_resource_load_status_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        ResourceLoadStatusInput(action="status", unknown_field="x")


def test_server_health_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        ServerHealthInput(action="check", unknown_field="x")


def test_context_compress_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        ContextCompressInput(content="hello", unknown_field="x")


def test_decision_log_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        DecisionLogInput(action="log", unknown_field="x")


def test_token_budget_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        TokenBudgetInput(action="status", unknown_field="x")


def test_project_init_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        ProjectInitInput(action="create", unknown_field="x")


def test_knowledge_inject_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        KnowledgeInjectInput(action="inject", unknown_field="x")


def test_metrics_report_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        MetricsReportInput(action="query", unknown_field="x")


def test_config_manage_input_extra_forbid():
    with pytest.raises(PydanticValidationError):
        ConfigManageInput(action="reload", unknown_field="x")


def test_session_manage_input_actions():
    for action in ("save", "load", "list", "detect", "verify", "track", "restore"):
        instance = SessionManageInput(action=action)
        assert instance.action == action


def test_workflow_dispatch_input_actions():
    for action in ("start", "status", "abort", "phase", "recover", "snapshots"):
        instance = WorkflowDispatchInput(action=action)
        assert instance.action == action


def test_hook_manage_input_actions():
    for action in ("list", "execute"):
        instance = HookManageInput(action=action)
        assert instance.action == action


def test_resource_load_status_input_actions():
    for action in ("status", "preload", "cache", "clear_cache", "loading_progress", "token_report", "disclosure_transition"):
        instance = ResourceLoadStatusInput(action=action)
        assert instance.action == action


def test_server_health_input_actions():
    for action in ("check", "negotiate_version", "capabilities"):
        instance = ServerHealthInput(action=action)
        assert instance.action == action


def test_knowledge_search_input_top_k_bounds():
    with pytest.raises(PydanticValidationError):
        KnowledgeSearchInput(action="retrieve", top_k=0)
    with pytest.raises(PydanticValidationError):
        KnowledgeSearchInput(action="retrieve", top_k=51)


def test_context_compress_input_target_tokens_bounds():
    with pytest.raises(PydanticValidationError):
        ContextCompressInput(content="test", target_tokens=50)
    with pytest.raises(PydanticValidationError):
        ContextCompressInput(content="test", target_tokens=60000)


def test_agent_status_input_phase_bounds():
    with pytest.raises(PydanticValidationError):
        AgentStatusInput(action="by_phase", phase=-1)
    with pytest.raises(PydanticValidationError):
        AgentStatusInput(action="by_phase", phase=9)
