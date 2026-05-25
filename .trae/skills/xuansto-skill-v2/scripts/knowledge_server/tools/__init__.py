from .skill_analyze import get_tool_definition as skill_analyze_def, handle_tool as skill_analyze_handler
from .quality_gate_check import get_tool_definition as quality_gate_check_def, handle_tool as quality_gate_check_handler
from .spec_drift_detect import get_tool_definition as spec_drift_detect_def, handle_tool as spec_drift_detect_handler
from .security_scan import get_tool_definition as security_scan_def, handle_tool as security_scan_handler
from .code_simplify import get_tool_definition as code_simplify_def, handle_tool as code_simplify_handler
from .session_manage import get_tool_definition as session_manage_def, handle_tool as session_manage_handler
from .workflow_dispatch import get_tool_definition as workflow_dispatch_def, handle_tool as workflow_dispatch_handler
from .agent_status import get_tool_definition as agent_status_def, handle_tool as agent_status_handler
from .hook_manage import get_tool_definition as hook_manage_def, handle_tool as hook_manage_handler
from .context_compress import get_tool_definition as context_compress_def, handle_tool as context_compress_handler
from .server_health import get_tool_definition as server_health_def, handle_tool as server_health_handler
from .decision_log import get_tool_definition as decision_log_def, handle_tool as decision_log_handler
from .token_budget import get_tool_definition as token_budget_def, handle_tool as token_budget_handler
from .knowledge_inject import get_tool_definition as knowledge_inject_def, handle_tool as knowledge_inject_handler
from .project_init import get_tool_definition as project_init_def, handle_tool as project_init_handler

TOOL_REGISTRY = {
    "skill_analyze": (skill_analyze_def, skill_analyze_handler),
    "quality_gate_check": (quality_gate_check_def, quality_gate_check_handler),
    "spec_drift_detect": (spec_drift_detect_def, spec_drift_detect_handler),
    "security_scan": (security_scan_def, security_scan_handler),
    "code_simplify": (code_simplify_def, code_simplify_handler),
    "session_manage": (session_manage_def, session_manage_handler),
    "workflow_dispatch": (workflow_dispatch_def, workflow_dispatch_handler),
    "agent_status": (agent_status_def, agent_status_handler),
    "hook_manage": (hook_manage_def, hook_manage_handler),
    "context_compress": (context_compress_def, context_compress_handler),
    "server_health": (server_health_def, server_health_handler),
    "decision_log": (decision_log_def, decision_log_handler),
    "token_budget": (token_budget_def, token_budget_handler),
    "knowledge_inject": (knowledge_inject_def, knowledge_inject_handler),
    "project_init": (project_init_def, project_init_handler),
}

SKILL_TOOL_NAMES = set(TOOL_REGISTRY.keys())


def get_skill_tool_definitions():
    definitions = []
    for tool_name, (get_def, _handler) in TOOL_REGISTRY.items():
        definition = get_def()
        if definition is not None:
            definitions.append(definition)
    return definitions
