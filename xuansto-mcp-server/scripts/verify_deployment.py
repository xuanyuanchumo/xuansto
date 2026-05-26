from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

EXPECTED_TOOLS = [
    "skill_analyze",
    "knowledge_search",
    "quality_gate_check",
    "spec_drift_detect",
    "security_scan",
    "code_simplify",
    "session_manage",
    "workflow_dispatch",
    "agent_status",
    "hook_manage",
    "resource_load_status",
    "context_compress",
    "server_health",
    "decision_log",
    "token_budget",
    "project_init",
]

EXPECTED_RESOURCES = [
    "xuansto://config/skill",
    "xuansto://gates/definitions",
    "xuansto://agents/registry",
    "xuansto://workflows/definitions",
    "xuansto://templates/{name}",
    "xuansto://sessions/latest",
    "xuansto://loading/status",
]

DEGRADATION_CHAIN = [
    "skill_analyze",
    "knowledge_search",
    "quality_gate_check",
    "spec_drift_detect",
    "security_scan",
    "code_simplify",
    "session_manage",
    "workflow_dispatch",
    "agent_status",
    "hook_manage",
    "resource_load_status",
    "context_compress",
    "server_health",
    "decision_log",
    "token_budget",
    "project_init",
]


class DeploymentVerifier:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[str] = []
        self.warnings: list[str] = []

    def _pass(self, check: str) -> None:
        self.passed.append(check)

    def _fail(self, check: str, reason: str) -> None:
        self.failed.append(f"{check}: {reason}")

    def _warn(self, check: str, reason: str) -> None:
        self.warnings.append(f"{check}: {reason}")

    def check_tools_registered(self) -> None:
        check = "tools_registered"
        try:
            from xuansto_mcp.server import mcp

            import asyncio

            async def _get_tools():
                tools = await mcp.list_tools()
                return [t.name for t in tools]

            tool_names = asyncio.run(_get_tools())
            for tool_name in EXPECTED_TOOLS:
                if tool_name in tool_names:
                    self._pass(f"tool:{tool_name}")
                else:
                    self._fail(f"tool:{tool_name}", "not registered")
            extra = set(tool_names) - set(EXPECTED_TOOLS)
            if extra:
                self._warn(check, f"extra tools found: {extra}")
            if len(tool_names) < len(EXPECTED_TOOLS):
                self._fail(check, f"expected {len(EXPECTED_TOOLS)} tools, found {len(tool_names)}")
        except Exception as e:
            self._fail(check, str(e))

    def check_resources_accessible(self) -> None:
        check = "resources_accessible"
        try:
            from xuansto_mcp.server import mcp

            import asyncio

            async def _get_resources():
                resources = await mcp.list_resources()
                templates = await mcp.list_resource_templates()
                resource_uris = [str(r.uri) for r in resources.resources]
                template_uris = [str(t.uriTemplate) for t in templates.resourceTemplates]
                return resource_uris, template_uris

            resource_uris, template_uris = asyncio.run(_get_resources())
            all_uris = resource_uris + template_uris
            for expected_uri in EXPECTED_RESOURCES:
                if expected_uri in all_uris:
                    self._pass(f"resource:{expected_uri}")
                else:
                    self._fail(f"resource:{expected_uri}", "not accessible")
            if len(all_uris) < len(EXPECTED_RESOURCES):
                self._warn(check, f"expected {len(EXPECTED_RESOURCES)} resources, found {len(all_uris)}")
        except Exception as e:
            self._fail(check, str(e))

    def check_skill_root_resolution(self) -> None:
        check = "skill_root_resolution"
        try:
            from xuansto_mcp.core.config import SKILL_ROOT, DATA_DIR

            if SKILL_ROOT.exists():
                self._pass(f"{check}:SKILL_ROOT")
            else:
                self._warn(check, f"SKILL_ROOT does not exist: {SKILL_ROOT}")
            if DATA_DIR.exists():
                self._pass(f"{check}:DATA_DIR")
            else:
                self._fail(f"{check}:DATA_DIR", f"does not exist: {DATA_DIR}")
        except Exception as e:
            self._fail(check, str(e))

    def check_config_loading(self) -> None:
        check = "config_loading"
        try:
            from xuansto_mcp.core.config import (
                GATE_SCRIPTS_MAP,
                QUALITY_GATES_PHASE_MAP,
                HOOK_SCRIPTS_MAP,
                MCP_API_VERSION,
                MCP_MIN_SUPPORTED_VERSION,
            )

            if isinstance(GATE_SCRIPTS_MAP, dict) and len(GATE_SCRIPTS_MAP) > 0:
                self._pass(f"{check}:GATE_SCRIPTS_MAP")
            else:
                self._fail(f"{check}:GATE_SCRIPTS_MAP", "empty or not dict")

            if isinstance(QUALITY_GATES_PHASE_MAP, dict) and len(QUALITY_GATES_PHASE_MAP) > 0:
                self._pass(f"{check}:QUALITY_GATES_PHASE_MAP")
            else:
                self._fail(f"{check}:QUALITY_GATES_PHASE_MAP", "empty or not dict")

            if isinstance(HOOK_SCRIPTS_MAP, dict) and len(HOOK_SCRIPTS_MAP) > 0:
                self._pass(f"{check}:HOOK_SCRIPTS_MAP")
            else:
                self._fail(f"{check}:HOOK_SCRIPTS_MAP", "empty or not dict")

            if MCP_API_VERSION and MCP_MIN_SUPPORTED_VERSION:
                self._pass(f"{check}:API_VERSIONS")
            else:
                self._fail(f"{check}:API_VERSIONS", "missing version constants")
        except Exception as e:
            self._fail(check, str(e))

    def check_degradation_chain(self) -> None:
        check = "degradation_chain"
        try:
            from xuansto_mcp.core.degradation import FALLBACK_MAP

            for tool_name in DEGRADATION_CHAIN:
                if tool_name in FALLBACK_MAP:
                    fallback_fn = FALLBACK_MAP[tool_name]
                    if callable(fallback_fn):
                        self._pass(f"{check}:{tool_name}")
                    else:
                        self._fail(f"{check}:{tool_name}", "fallback not callable")
                else:
                    self._fail(f"{check}:{tool_name}", "no fallback registered")
        except Exception as e:
            self._fail(check, str(e))

    def run(self) -> bool:
        print("=" * 60)
        print("Xuansto MCP Server - Deployment Verification")
        print("=" * 60)

        checks = [
            self.check_tools_registered,
            self.check_resources_accessible,
            self.check_skill_root_resolution,
            self.check_config_loading,
            self.check_degradation_chain,
        ]

        for check_fn in checks:
            try:
                check_fn()
            except Exception as e:
                self._fail(check_fn.__name__, traceback.format_exc())

        print(f"\nPassed:   {len(self.passed)}")
        print(f"Failed:   {len(self.failed)}")
        print(f"Warnings: {len(self.warnings)}")

        if self.failed:
            print("\n--- FAILURES ---")
            for f in self.failed:
                print(f"  [FAIL] {f}")

        if self.warnings:
            print("\n--- WARNINGS ---")
            for w in self.warnings:
                print(f"  [WARN] {w}")

        print("\n" + "=" * 60)
        if self.failed:
            print("RESULT: DEPLOYMENT VERIFICATION FAILED")
            return False
        print("RESULT: DEPLOYMENT VERIFICATION PASSED")
        return True


def main() -> int:
    verifier = DeploymentVerifier()
    success = verifier.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
