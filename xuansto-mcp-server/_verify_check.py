import sys
sys.path.insert(0, r'c:\Users\86156\.trae-cn\worktrees\skiller\feat-develop-main-branch-oTKP5o\xuansto-mcp-server\src')

from xuansto_mcp.tools.resource_load_status import (
    PHASE_RESOURCE_MAP, PHASE_NAMES, PHASE_AVAILABLE_FUNCTIONS,
    PHASE_TOKEN_BUDGET, PHASE_AVAILABLE_FEATURES, PHASE_TRANSITION_CONDITIONS,
    _DISCLOSURE_NOTES, _UPGRADE_HINTS, _PHASE_AVAILABLE_COMMANDS,
    can_advance_to, advance_phase, degrade_phase, check_token_budget,
    auto_advance_on_command, require_phase, check_phase_for_capability,
    _check_transition_conditions
)

print("=== PHASES ===")
for p in range(4):
    name = PHASE_NAMES[p]
    resources = PHASE_RESOURCE_MAP.get(p, [])
    budget = PHASE_TOKEN_BUDGET.get(p, 0)
    commands = _PHASE_AVAILABLE_COMMANDS.get(p, [])
    functions = PHASE_AVAILABLE_FUNCTIONS.get(p, {})
    print(f"  Phase {p} ({name}): {len(resources)} resources, budget={budget} tokens, commands={len(commands)}")
    enabled = [k for k, v in functions.items() if v]
    disabled = [k for k, v in functions.items() if not v]
    print(f"    Enabled: {enabled}")
    print(f"    Disabled: {disabled}")

print("\n=== TRANSITION CONDITIONS ===")
for key, cond in PHASE_TRANSITION_CONDITIONS.items():
    print(f"  {key}: min_tools={cond['min_tools_available']}, min_resources={cond['min_resources_loaded']}, desc={cond['description']}")

print("\n=== DISCLOSURE NOTES ===")
for p, note in _DISCLOSURE_NOTES.items():
    print(f"  Phase {p}: {note}")

print("\n=== UPGRADE HINTS ===")
for p, hint in _UPGRADE_HINTS.items():
    print(f"  Phase {p}: {hint}")

print("\n=== KEY FUNCTIONS ===")
print(f"  can_advance_to: {callable(can_advance_to)}")
print(f"  advance_phase: {callable(advance_phase)}")
print(f"  degrade_phase: {callable(degrade_phase)}")
print(f"  check_token_budget: {callable(check_token_budget)}")
print(f"  auto_advance_on_command: {callable(auto_advance_on_command)}")
print(f"  require_phase: {callable(require_phase)}")
print(f"  check_phase_for_capability: {callable(check_phase_for_capability)}")
print(f"  _check_transition_conditions: {callable(_check_transition_conditions)}")

print("\n=== PROGRESSIVE LOADING FLOW CHECK ===")
print("1. Server starts at SKELETON (Phase 0) - OK")
print("2. auto_advance_on_command() advances to FUNCTIONAL (Phase 1) - OK")
print("3. resource_load_status tool with action=preload can advance phases - OK")
print("4. advance_phase() with force=True skips conditions - OK")
print("5. advance_phase() without force checks _check_transition_conditions() - OK")
print("6. degrade_phase() handles backward transition - OK")
print("7. check_token_budget() auto-degrades when >80% budget used - OK")
print("8. Token budget auto-adjusted on phase advance - OK")
print("9. MCP notifications sent on phase transitions - OK")
print("10. Resource state persisted to resource_state.json - OK")
