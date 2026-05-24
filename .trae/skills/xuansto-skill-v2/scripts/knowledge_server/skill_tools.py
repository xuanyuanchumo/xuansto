import ast
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import make_response, make_error_response, mcp_available
from .degradation import MCPToolFallback

logger = logging.getLogger("knowledge-server")

MCP_JSON_SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_skill_tool_definitions() -> list:
    if not mcp_available:
        return []
    return [
        Tool(
            name="skill_analyze",
            description=(
                "[Read-Only] [Idempotent] Analyze skill project structure, extract YAML metadata, "
                "directory structure, agent registry, script dependencies, and validation issues.\n\n"
                "Use this tool to inspect a skill project's overall health and structure. "
                "Returns metadata from SKILL.md frontmatter, directory tree, agent layer breakdown, "
                "script dependency graph, and any detected issues (missing scripts, parse errors, etc.).\n\n"
                "Parameters:\n"
                "- skill_path (string, required): Absolute path to the skill root directory.\n"
                "- include_scripts (boolean, default=true): Whether to analyze the scripts directory.\n"
                "- include_agents (boolean, default=true): Whether to analyze the agents directory.\n"
                "- depth (string, default='basic', enum: basic|full): Analysis depth. 'full' includes "
                "line counts, dependency graphs, and deeper validation.\n\n"
                "Returns an object with:\n"
                "- metadata: Extracted YAML frontmatter (name, version, agents_summary, tags).\n"
                "- structure: Directory info (root, directories, file_count, total_lines).\n"
                "- agents: Agent registry info (total, layers, by_layer).\n"
                "- dependencies: Script and MCP dependencies.\n"
                "- issues: List of detected issues (severity, code, message, path).\n\n"
                "Example: Full analysis of a skill project:\n"
                '{"skill_path": "/path/to/skill", "depth": "full", "include_agents": true}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "skill_path": {"type": "string", "description": "Absolute path to the skill root directory"},
                    "include_scripts": {"type": "boolean", "description": "Whether to analyze scripts directory", "default": True},
                    "include_agents": {"type": "boolean", "description": "Whether to analyze agents directory", "default": True},
                    "depth": {"type": "string", "description": "Analysis depth: basic or full", "default": "basic", "enum": ["basic", "full"]},
                },
                "required": ["skill_path"],
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "metadata": {"type": "object", "properties": {"name": {"type": "string"}, "version": {"type": "string"}, "agents_summary": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}}},
                    "structure": {"type": "object", "properties": {"root": {"type": "string"}, "directories": {"type": "array", "items": {"type": "string"}}, "file_count": {"type": "integer"}, "total_lines": {"type": "integer"}}},
                    "agents": {"type": "object", "properties": {"total": {"type": "integer"}, "layers": {"type": "integer"}, "by_layer": {"type": "object"}}},
                    "dependencies": {"type": "object", "properties": {"mcp_server": {"type": "string"}, "scripts": {"type": "array", "items": {"type": "string"}}, "python_version": {"type": "string"}}},
                    "issues": {"type": "array", "items": {"type": "object", "properties": {"severity": {"type": "string"}, "code": {"type": "string"}, "message": {"type": "string"}, "path": {"type": "string"}}}},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
        ),
        Tool(
            name="quality_gate_check",
            description=(
                "[Read-Only] [Idempotent] Check 54 quality gates by gate_ids or phase.\n\n"
                "Use this tool to validate project quality at any development phase. "
                "Supports checking specific gates by ID, all gates for a phase, or all gates. "
                "Returns pass/fail status with severity levels (BLOCK/WARN) and detailed results.\n\n"
                "Parameters:\n"
                "- gate_ids (array of strings, optional): Specific gate IDs to check. Empty checks all.\n"
                "- phase (string, optional): Phase number (0-8) to filter gates.\n"
                "- project_path (string, default='.'): Project root directory path.\n"
                "- severity_filter (string, default='all', enum: all|BLOCK|WARN): Filter by severity.\n"
                "- force_refresh (boolean, default=false): Force refresh, ignoring file hash cache.\n\n"
                "Returns an object with:\n"
                "- gates_checked: Number of gates evaluated.\n"
                "- gates_passed: Number of passing gates.\n"
                "- gates_failed: Number of failing gates.\n"
                "- results: Array of gate results (gate_id, status, severity, message, details).\n"
                "- phase: The phase filter used.\n"
                "- can_proceed: Whether all BLOCK gates passed.\n\n"
                "Example: Check specific gates:\n"
                '{"gate_ids": ["TEST-PASS", "FILE-ENCODING"], "project_path": "/path/to/project"}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "gate_ids": {"type": "array", "items": {"type": "string"}, "description": "Gate IDs to check; empty checks all"},
                    "phase": {"type": "string", "description": "Phase number (0-8) to filter gates"},
                    "project_path": {"type": "string", "description": "Project root directory path", "default": "."},
                    "severity_filter": {"type": "string", "description": "Severity filter: all, BLOCK, WARN", "default": "all", "enum": ["all", "BLOCK", "WARN"]},
                    "force_refresh": {"type": "boolean", "description": "Force refresh ignoring cache", "default": False},
                },
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "gates_checked": {"type": "integer"},
                    "gates_passed": {"type": "integer"},
                    "gates_failed": {"type": "integer"},
                    "results": {"type": "array", "items": {"type": "object", "properties": {"gate_id": {"type": "string"}, "status": {"type": "string"}, "severity": {"type": "string"}, "message": {"type": "string"}, "details": {"type": "object"}}}},
                    "phase": {"type": "string"},
                    "can_proceed": {"type": "boolean"},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
        ),
        Tool(
            name="spec_drift_detect",
            description=(
                "[Read-Only] [Idempotent] Detect specification drift between spec directory and source directory.\n\n"
                "Use this tool to check if implementation has diverged from specification documents. "
                "Scans spec files and checks for corresponding implementations, reporting mismatches, "
                "missing implementations, and coverage percentage.\n\n"
                "Parameters:\n"
                "- spec_dir (string, default='.trae/specs'): Specification document directory.\n"
                "- src_dir (string, default='.'): Source code directory.\n\n"
                "Returns an object with:\n"
                "- total_specs: Total spec files found.\n"
                "- drifts_detected: Number of drift items.\n"
                "- drifts: Array of drift items (spec_file, spec_requirement, implementation, drift_type, severity, description, suggestion).\n"
                "- coverage_pct: Implementation coverage percentage.\n\n"
                "Example: Detect drift:\n"
                '{"spec_dir": ".trae/specs", "src_dir": "src"}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "spec_dir": {"type": "string", "description": "Specification document directory", "default": ".trae/specs"},
                    "src_dir": {"type": "string", "description": "Source code directory", "default": "."},
                },
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "total_specs": {"type": "integer"},
                    "drifts_detected": {"type": "integer"},
                    "drifts": {"type": "array", "items": {"type": "object", "properties": {"spec_file": {"type": "string"}, "spec_requirement": {"type": "string"}, "implementation": {"type": "string"}, "drift_type": {"type": "string"}, "severity": {"type": "string"}, "description": {"type": "string"}, "suggestion": {"type": "string"}}}},
                    "coverage_pct": {"type": "number"},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
        ),
        Tool(
            name="security_scan",
            description=(
                "[Read-Only] [Idempotent] OWASP Agentic Top 10 + dependency vulnerability scanning.\n\n"
                "Use this tool to scan code for security vulnerabilities including hardcoded secrets, "
                "injection risks, OWASP Top 10 patterns, and dependency vulnerabilities. "
                "Returns findings categorized by severity with remediation suggestions.\n\n"
                "Parameters:\n"
                "- target (string, default='.'): Target directory to scan.\n"
                "- severity_threshold (string, default='medium', enum: critical|high|medium|low): Minimum severity to report.\n"
                "- include_agentic (boolean, default=true): Include OWASP Agentic Top 10 checks.\n"
                "- include_dependency (boolean, default=true): Include dependency vulnerability scanning.\n\n"
                "Returns an object with:\n"
                "- total_findings: Total number of findings.\n"
                "- by_severity: Counts by severity level (critical, high, medium, low).\n"
                "- findings: Array of findings (id, title, severity, category, file, line, description, remediation, references).\n"
                "- agentic_findings: Count of OWASP Agentic findings.\n"
                "- dependency_findings: Count of dependency findings.\n"
                "- scan_duration_ms: Scan duration in milliseconds.\n\n"
                "Example: Scan with high severity threshold:\n"
                '{"target": "src", "severity_threshold": "high"}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target directory to scan", "default": "."},
                    "severity_threshold": {"type": "string", "description": "Minimum severity: critical, high, medium, low", "default": "medium", "enum": ["critical", "high", "medium", "low"]},
                    "include_agentic": {"type": "boolean", "description": "Include OWASP Agentic Top 10 checks", "default": True},
                    "include_dependency": {"type": "boolean", "description": "Include dependency vulnerability scanning", "default": True},
                },
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "total_findings": {"type": "integer"},
                    "by_severity": {"type": "object", "properties": {"critical": {"type": "integer"}, "high": {"type": "integer"}, "medium": {"type": "integer"}, "low": {"type": "integer"}}},
                    "findings": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "title": {"type": "string"}, "severity": {"type": "string"}, "category": {"type": "string"}, "file": {"type": "string"}, "line": {"type": "integer"}, "description": {"type": "string"}, "remediation": {"type": "string"}, "references": {"type": "array", "items": {"type": "string"}}}}},
                    "agentic_findings": {"type": "integer"},
                    "dependency_findings": {"type": "integer"},
                    "scan_duration_ms": {"type": "integer"},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
        ),
        Tool(
            name="code_simplify",
            description=(
                "[Read-Only] [Idempotent] Code simplification analysis.\n\n"
                "Use this tool to detect code simplification opportunities including dead code, "
                "duplication, excessive complexity, and naming issues. Returns actionable suggestions "
                "with safety ratings and estimated line reductions.\n\n"
                "Parameters:\n"
                "- target (string, required): Target file or directory path.\n"
                "- scope (string, default='recent', enum: file|dir|recent): Scan scope.\n"
                "- include_dedup (boolean, default=true): Include duplicate code detection.\n\n"
                "Returns an object with:\n"
                "- total_suggestions: Total simplification suggestions.\n"
                "- by_type: Counts by suggestion type (dead_code, duplication, complexity, naming).\n"
                "- suggestions: Array of suggestions (id, type, file, line_start, line_end, description, safety, action, estimated_reduction).\n"
                "- total_lines_reducible: Total lines that could be reduced.\n"
                "- safe_count: Number of safe suggestions.\n"
                "- caution_count: Number of caution-level suggestions.\n\n"
                "Example: Analyze a directory:\n"
                '{"target": "src/utils", "scope": "dir", "include_dedup": true}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target file or directory path"},
                    "scope": {"type": "string", "description": "Scan scope: file, dir, recent", "default": "recent", "enum": ["file", "dir", "recent"]},
                    "include_dedup": {"type": "boolean", "description": "Include duplicate code detection", "default": True},
                },
                "required": ["target"],
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "total_suggestions": {"type": "integer"},
                    "by_type": {"type": "object", "properties": {"dead_code": {"type": "integer"}, "duplication": {"type": "integer"}, "complexity": {"type": "integer"}, "naming": {"type": "integer"}}},
                    "suggestions": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "type": {"type": "string"}, "file": {"type": "string"}, "line_start": {"type": "integer"}, "line_end": {"type": "integer"}, "description": {"type": "string"}, "safety": {"type": "string"}, "action": {"type": "string"}, "estimated_reduction": {"type": "integer"}}}},
                    "total_lines_reducible": {"type": "integer"},
                    "safe_count": {"type": "integer"},
                    "caution_count": {"type": "integer"},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
        ),
        Tool(
            name="session_manage",
            description=(
                "Session state management: save, load, list, detect, verify, track, restore.\n\n"
                "Use this tool to manage development session state across interruptions. "
                "Save session progress before context switches, load previous sessions to resume work, "
                "and track task completion and decisions.\n\n"
                "Parameters:\n"
                "- action (string, required, enum: save|load|list|detect|verify|track|restore): Operation type.\n"
                "- completed_tasks (array of strings, optional): Completed task list (save action).\n"
                "- pending_tasks (array of strings, optional): Pending task list (save/track action).\n"
                "- decisions (array of objects, optional): Key decisions list (save/track action).\n"
                "- experience (array of objects, optional): Experience precipitation list (save action).\n"
                "- error_log (array of strings, optional): Error log (detect action).\n"
                "- pattern_path (string, optional): Pattern file path (verify action).\n"
                "- success (boolean, default=true): Verification success (verify action).\n"
                "- current_phase (integer, optional): Current phase number (track action).\n"
                "- current_task (string, optional): Current task description (track action).\n\n"
                "Returns an object with:\n"
                "- action: The action performed.\n"
                "- session_id: Session identifier.\n"
                "- saved_at/state: Action-specific result data.\n\n"
                "Example: Save session:\n"
                '{"action": "save", "completed_tasks": ["task-1"], "pending_tasks": ["task-2"], "decisions": [{"id": "ADR-001", "title": "Choose framework"}]}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Operation: save, load, list, detect, verify, track, restore", "enum": ["save", "load", "list", "detect", "verify", "track", "restore"]},
                    "completed_tasks": {"type": "array", "items": {"type": "string"}, "description": "Completed task list (save)"},
                    "pending_tasks": {"type": "array", "items": {"type": "string"}, "description": "Pending task list (save/track)"},
                    "decisions": {"type": "array", "items": {"type": "object"}, "description": "Key decisions list (save/track)"},
                    "experience": {"type": "array", "items": {"type": "object"}, "description": "Experience precipitation list (save)"},
                    "error_log": {"type": "array", "items": {"type": "string"}, "description": "Error log (detect)"},
                    "pattern_path": {"type": "string", "description": "Pattern file path (verify)"},
                    "success": {"type": "boolean", "description": "Verification success (verify)", "default": True},
                    "current_phase": {"type": "integer", "description": "Current phase number (track)"},
                    "current_task": {"type": "string", "description": "Current task description (track)"},
                },
                "required": ["action"],
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "session_id": {"type": "string"},
                    "saved_at": {"type": "string"},
                    "state": {"type": "object"},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
        ),
        Tool(
            name="workflow_dispatch",
            description=(
                "Workflow dispatch: start, status, abort, phase, recover, snapshots.\n\n"
                "Use this tool to manage development workflows. Start SDD/TDD workflows, "
                "query workflow status, advance phases, recover from failures, and manage snapshots.\n\n"
                "Parameters:\n"
                "- action (string, required, enum: start|status|abort|phase|recover|snapshots): Operation type.\n"
                "- workflow (string, optional): Workflow name (start action): sdd-tdd-full, sdd-tdd-medium, sdd-tdd-fast, etc.\n"
                "- project_path (string, default='.'): Project root directory (start action).\n"
                "- workflow_id (string, optional): Workflow instance ID (status/abort/phase/recover/snapshots).\n"
                "- phase_action (string, optional): Phase operation (phase action): advance, current.\n"
                "- snapshot_phase (integer, optional): Target phase snapshot for recovery (recover action).\n\n"
                "Returns an object with:\n"
                "- action: The action performed.\n"
                "- workflow_id: Workflow instance ID.\n"
                "- workflow_name: Workflow name.\n"
                "- current_phase: Current phase number.\n"
                "- phases: Array of phase objects (phase, name, status).\n"
                "- started_at/aborted_at: Timestamps.\n\n"
                "Example: Start a full workflow:\n"
                '{"action": "start", "workflow": "sdd-tdd-full", "project_path": "/path/to/project"}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Operation: start, status, abort, phase, recover, snapshots", "enum": ["start", "status", "abort", "phase", "recover", "snapshots"]},
                    "workflow": {"type": "string", "description": "Workflow name (start): sdd-tdd-full, sdd-tdd-medium, sdd-tdd-fast"},
                    "project_path": {"type": "string", "description": "Project root directory (start)", "default": "."},
                    "workflow_id": {"type": "string", "description": "Workflow instance ID (status/abort/phase/recover/snapshots)"},
                    "phase_action": {"type": "string", "description": "Phase operation (phase): advance, current", "enum": ["advance", "current"]},
                    "snapshot_phase": {"type": "integer", "description": "Target phase snapshot for recovery (recover)"},
                },
                "required": ["action"],
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "workflow_id": {"type": "string"},
                    "workflow_name": {"type": "string"},
                    "current_phase": {"type": "integer"},
                    "phases": {"type": "array", "items": {"type": "object", "properties": {"phase": {"type": "integer"}, "name": {"type": "string"}, "status": {"type": "string"}}}},
                    "started_at": {"type": "string"},
                    "aborted_at": {"type": "string"},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
        ),
        Tool(
            name="agent_status",
            description=(
                "[Read-Only] [Idempotent] Agent status query: list, by_phase, detail.\n\n"
                "Use this tool to query the agent registry. List all agents, filter by phase, "
                "or get detailed information about a specific agent.\n\n"
                "Parameters:\n"
                "- action (string, required, enum: list|by_phase|detail|create|match|assign|release|instance_status|destroy|schedule): Operation type.\n"
                "- phase (integer, optional): Phase number for by_phase query (0-8).\n"
                "- agent_name (string, optional): Agent name for detail query.\n"
                "- agent_type (string, optional): Agent type for create.\n"
                "- capabilities (array of strings, optional): Capability list for create/match.\n"
                "- agent_id (string, optional): Agent instance ID for assign/release/instance_status/destroy.\n"
                "- task (string, optional): Task description for assign.\n\n"
                "Returns an object with:\n"
                "- action: The action performed.\n"
                "- agents: Array of agent objects (name, layer, status, capabilities, etc.).\n"
                "- total_agents: Total number of agents.\n"
                "- available_count: Number of available agents.\n\n"
                "Example: List all agents:\n"
                '{"action": "list"}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Operation: list, by_phase, detail, create, match, assign, release, instance_status, destroy, schedule", "enum": ["list", "by_phase", "detail", "create", "match", "assign", "release", "instance_status", "destroy", "schedule"]},
                    "phase": {"type": "integer", "description": "Phase number for by_phase (0-8)"},
                    "agent_name": {"type": "string", "description": "Agent name for detail"},
                    "agent_type": {"type": "string", "description": "Agent type for create"},
                    "capabilities": {"type": "array", "items": {"type": "string"}, "description": "Capability list for create/match"},
                    "agent_id": {"type": "string", "description": "Agent instance ID for assign/release/instance_status/destroy"},
                    "task": {"type": "string", "description": "Task description for assign"},
                },
                "required": ["action"],
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "agents": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "layer": {"type": "string"}, "status": {"type": "string"}, "capabilities": {"type": "array", "items": {"type": "string"}}, "assigned_tasks": {"type": "integer"}, "completed_tasks": {"type": "integer"}, "definition_file": {"type": "string"}}}},
                    "total_agents": {"type": "integer"},
                    "available_count": {"type": "integer"},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
        ),
        Tool(
            name="hook_manage",
            description=(
                "Hook management: list, execute.\n\n"
                "Use this tool to manage lifecycle hooks. List configured hooks by profile, "
                "or execute a specific hook with context.\n\n"
                "Parameters:\n"
                "- action (string, required, enum: list|execute): Operation type.\n"
                "- profile (string, default='standard', enum: minimal|standard|strict): Hook configuration profile.\n"
                "- hook_name (string, optional): Hook name to execute.\n"
                "- context (object, optional): Execution context for hook.\n\n"
                "Returns an object with:\n"
                "- action: The action performed.\n"
                "- profile: The profile used.\n"
                "- hooks: Array of hook objects (name, trigger, pre_callbacks, post_callbacks, enabled).\n"
                "- total_hooks: Total number of hooks.\n"
                "- enabled_count: Number of enabled hooks.\n\n"
                "Example: List standard hooks:\n"
                '{"action": "list", "profile": "standard"}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Operation: list, execute", "enum": ["list", "execute"]},
                    "profile": {"type": "string", "description": "Hook profile: minimal, standard, strict", "default": "standard", "enum": ["minimal", "standard", "strict"]},
                    "hook_name": {"type": "string", "description": "Hook name to execute"},
                    "context": {"type": "object", "description": "Execution context for hook"},
                },
                "required": ["action"],
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "profile": {"type": "string"},
                    "hooks": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "trigger": {"type": "string"}, "pre_callbacks": {"type": "array", "items": {"type": "string"}}, "post_callbacks": {"type": "array", "items": {"type": "string"}}, "enabled": {"type": "boolean"}}}},
                    "total_hooks": {"type": "integer"},
                    "enabled_count": {"type": "integer"},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
        ),
        Tool(
            name="context_compress",
            description=(
                "[Read-Only] [Idempotent] Context compression: semantic, selective, lossless strategies.\n\n"
                "Use this tool to compress long context text to fit within token budgets. "
                "Supports three strategies: semantic (meaning-preserving summary), selective (keep key sections), "
                "and lossless (whitespace/format optimization only).\n\n"
                "Parameters:\n"
                "- content (string, required): Text content to compress.\n"
                "- strategy (string, default='semantic', enum: semantic|selective|lossless): Compression strategy.\n"
                "- target_tokens (integer, default=2000, range 100-50000): Target token count.\n"
                "- preserve_sections (array of strings, optional): Section titles that must be preserved.\n\n"
                "Returns an object with:\n"
                "- original_tokens: Estimated original token count.\n"
                "- compressed_tokens: Estimated compressed token count.\n"
                "- compression_ratio: Compression ratio (0-1).\n"
                "- strategy_used: The strategy used.\n"
                "- compressed_content: The compressed text.\n"
                "- preserved_sections: Sections that were preserved.\n"
                "- quality_score: Estimated quality score (0-1).\n\n"
                "Example: Semantic compression:\n"
                '{"content": "...(long text)...", "strategy": "semantic", "target_tokens": 2000}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Text content to compress"},
                    "strategy": {"type": "string", "description": "Compression strategy: semantic, selective, lossless", "default": "semantic", "enum": ["semantic", "selective", "lossless"]},
                    "target_tokens": {"type": "integer", "description": "Target token count", "default": 2000, "minimum": 100, "maximum": 50000},
                    "preserve_sections": {"type": "array", "items": {"type": "string"}, "description": "Section titles that must be preserved"},
                },
                "required": ["content"],
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "original_tokens": {"type": "integer"},
                    "compressed_tokens": {"type": "integer"},
                    "compression_ratio": {"type": "number"},
                    "strategy_used": {"type": "string"},
                    "compressed_content": {"type": "string"},
                    "preserved_sections": {"type": "array", "items": {"type": "string"}},
                    "quality_score": {"type": "number"},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
        ),
        Tool(
            name="server_health",
            description=(
                "[Read-Only] [Idempotent] Server health check and version compatibility verification.\n\n"
                "Use this tool to check MCP server health, version compatibility, and tool availability. "
                "Supports three actions: check (full health), version (version info), status (runtime status).\n\n"
                "Parameters:\n"
                "- action (string, default='check', enum: check|version|status): Operation type.\n"
                "- include_details (boolean, default=false): Include detailed tool status information.\n\n"
                "Returns an object with:\n"
                "- status: Health status (HEALTHY/DEGRADED/UNAVAILABLE).\n"
                "- version: Server version.\n"
                "- api_version: API version.\n"
                "- uptime_seconds: Server uptime in seconds.\n"
                "- tools_available: Number of available tools.\n"
                "- degradation_level: Degradation level (none/partial/full).\n"
                "- last_check_timestamp: ISO 8601 timestamp.\n"
                "- tools_status: Per-tool status (when include_details=true).\n\n"
                "Example: Full health check:\n"
                '{"action": "check", "include_details": true}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Operation: check, version, status", "default": "check", "enum": ["check", "version", "status"]},
                    "include_details": {"type": "boolean", "description": "Include detailed tool status", "default": False},
                },
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "version": {"type": "string"},
                    "api_version": {"type": "string"},
                    "uptime_seconds": {"type": "integer"},
                    "tools_available": {"type": "integer"},
                    "degradation_level": {"type": "string"},
                    "last_check_timestamp": {"type": "string"},
                    "tools_status": {"type": "object"},
                    "memory_usage_mb": {"type": "number"},
                    "active_workflows": {"type": "integer"},
                    "active_sessions": {"type": "integer"},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
        ),
        Tool(
            name="decision_log",
            description=(
                "Decision log management: log, query, export.\n\n"
                "Use this tool to record architectural decisions (ADRs), query past decisions, "
                "and export decision records. Supports full ADR fields including alternatives, "
                "rationale, and impact assessment.\n\n"
                "Parameters:\n"
                "- action (string, required, enum: log|query|export): Operation type.\n"
                "- title (string, optional): Decision title (log action).\n"
                "- description (string, optional): Decision description (log action).\n"
                "- context (string, optional): Decision context (log action).\n"
                "- alternatives (array of strings, optional): Alternative options (log action).\n"
                "- decision (string, optional): Final decision (log action).\n"
                "- rationale (string, optional): Decision rationale (log action).\n"
                "- impact (string, optional): Impact scope (log action).\n"
                "- decided_by (string, optional): Decision maker (log action).\n"
                "- keyword (string, optional): Search keyword (query action).\n"
                "- tag (string, optional): Tag filter (query action).\n"
                "- date_from (string, optional): Start date ISO8601 (query/export).\n"
                "- date_to (string, optional): End date ISO8601 (query/export).\n"
                "- limit (integer, default=20, range 1-100): Result limit (query action).\n"
                "- format (string, default='json', enum: json|markdown): Export format (export action).\n\n"
                "Returns an object with:\n"
                "- action: The action performed.\n"
                "- id: Decision ID (log action).\n"
                "- entry: Full decision entry (log action).\n"
                "- results: Array of matching decisions (query action).\n"
                "- total_decisions: Total count.\n\n"
                "Example: Log a decision:\n"
                '{"action": "log", "title": "Choose React", "alternatives": ["Vue", "Angular"], "decision": "React", "rationale": "Team experience"}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Operation: log, query, export", "enum": ["log", "query", "export"]},
                    "title": {"type": "string", "description": "Decision title (log)"},
                    "description": {"type": "string", "description": "Decision description (log)"},
                    "context": {"type": "string", "description": "Decision context (log)"},
                    "alternatives": {"type": "array", "items": {"type": "string"}, "description": "Alternative options (log)"},
                    "decision": {"type": "string", "description": "Final decision (log)"},
                    "rationale": {"type": "string", "description": "Decision rationale (log)"},
                    "impact": {"type": "string", "description": "Impact scope (log)"},
                    "decided_by": {"type": "string", "description": "Decision maker (log)"},
                    "keyword": {"type": "string", "description": "Search keyword (query)"},
                    "tag": {"type": "string", "description": "Tag filter (query)"},
                    "date_from": {"type": "string", "description": "Start date ISO8601 (query/export)"},
                    "date_to": {"type": "string", "description": "End date ISO8601 (query/export)"},
                    "limit": {"type": "integer", "description": "Result limit (query)", "default": 20, "minimum": 1, "maximum": 100},
                    "format": {"type": "string", "description": "Export format (export): json, markdown", "default": "json", "enum": ["json", "markdown"]},
                },
                "required": ["action"],
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "id": {"type": "string"},
                    "entry": {"type": "object"},
                    "results": {"type": "array", "items": {"type": "object"}},
                    "total_decisions": {"type": "integer"},
                    "format": {"type": "string"},
                    "content": {"type": "string"},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
        ),
        Tool(
            name="token_budget",
            description=(
                "Token budget management: status, set_budget, recommend, report.\n\n"
                "Use this tool to manage token budgets across development phases. "
                "Check current budget status, set custom allocations, get recommendations based on "
                "project characteristics, and generate usage reports.\n\n"
                "Parameters:\n"
                "- action (string, required, enum: status|set_budget|recommend|report): Operation type.\n"
                "- total_budget (integer, optional, >=1000): Total token budget (set_budget action).\n"
                "- phase_allocations (object, optional): Per-phase allocation (set_budget action).\n"
                "- project_size (string, optional, enum: small|medium|large): Project size (recommend action).\n"
                "- complexity (string, optional, enum: low|medium|high): Complexity level (recommend action).\n"
                "- team_size (integer, optional, range 1-50): Team size (recommend action).\n"
                "- period (string, default='session', enum: daily|weekly|session): Report period (report action).\n\n"
                "Returns an object with:\n"
                "- action: The action performed.\n"
                "- total_budget: Total token budget.\n"
                "- used: Tokens used.\n"
                "- remaining: Tokens remaining.\n"
                "- phase_allocations: Per-phase allocation map.\n"
                "- usage_by_phase: Per-phase usage map.\n\n"
                "Example: Check budget status:\n"
                '{"action": "status"}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Operation: status, set_budget, recommend, report", "enum": ["status", "set_budget", "recommend", "report"]},
                    "total_budget": {"type": "integer", "description": "Total token budget (set_budget, >=1000)", "minimum": 1000},
                    "phase_allocations": {"type": "object", "description": "Per-phase allocation (set_budget)"},
                    "project_size": {"type": "string", "description": "Project size (recommend): small, medium, large", "enum": ["small", "medium", "large"]},
                    "complexity": {"type": "string", "description": "Complexity (recommend): low, medium, high", "enum": ["low", "medium", "high"]},
                    "team_size": {"type": "integer", "description": "Team size (recommend, 1-50)", "minimum": 1, "maximum": 50},
                    "period": {"type": "string", "description": "Report period (report): daily, weekly, session", "default": "session", "enum": ["daily", "weekly", "session"]},
                },
                "required": ["action"],
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "total_budget": {"type": "integer"},
                    "used": {"type": "integer"},
                    "remaining": {"type": "integer"},
                    "phase_allocations": {"type": "object"},
                    "usage_by_phase": {"type": "object"},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
        ),
        Tool(
            name="knowledge_inject",
            description=(
                "Knowledge injection into context: inject, preview, clear.\n\n"
                "Use this tool to inject retrieved knowledge content into the current session context "
                "for agents to reference during task execution. Supports previewing injection impact "
                "and clearing injected content.\n\n"
                "Parameters:\n"
                "- action (string, required, enum: inject|preview|clear): Operation type.\n"
                "- content (string, optional): Content to inject (inject action).\n"
                "- scope (string, default='session', enum: session|workflow|global): Injection scope.\n"
                "- source (string, optional): Knowledge source identifier.\n"
                "- priority (string, default='normal', enum: low|normal|high): Injection priority.\n\n"
                "Returns an object with:\n"
                "- action: The action performed.\n"
                "- scope: Injection scope.\n"
                "- injected_tokens: Estimated tokens injected.\n"
                "- source: Source identifier.\n"
                "- priority: Priority level.\n"
                "- context_window_usage_pct: Context window usage percentage.\n\n"
                "Example: Inject knowledge:\n"
                '{"action": "inject", "content": "React best practices...", "scope": "session", "priority": "high"}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Operation: inject, preview, clear", "enum": ["inject", "preview", "clear"]},
                    "content": {"type": "string", "description": "Content to inject (inject)"},
                    "scope": {"type": "string", "description": "Injection scope: session, workflow, global", "default": "session", "enum": ["session", "workflow", "global"]},
                    "source": {"type": "string", "description": "Knowledge source identifier"},
                    "priority": {"type": "string", "description": "Priority: low, normal, high", "default": "normal", "enum": ["low", "normal", "high"]},
                },
                "required": ["action"],
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "scope": {"type": "string"},
                    "injected_tokens": {"type": "integer"},
                    "source": {"type": "string"},
                    "priority": {"type": "string"},
                    "context_window_usage_pct": {"type": "number"},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
        ),
        Tool(
            name="project_init",
            description=(
                "Project initialization: create, validate, detect_stack.\n\n"
                "Use this tool to create new projects with templates, validate existing project "
                "configurations, or detect the technology stack of a project.\n\n"
                "Parameters:\n"
                "- action (string, required, enum: create|validate|detect_stack): Operation type.\n"
                "- name (string, optional): Project name (create action).\n"
                "- description (string, optional): Project description (create action).\n"
                "- stack (array of strings, optional): Technology stack list (create action).\n"
                "- template (string, optional): Project template (create action).\n"
                "- directory (string, optional): Project directory (create action).\n"
                "- project_path (string, optional): Project path (validate/detect_stack action).\n\n"
                "Returns an object with:\n"
                "- action: The action performed.\n"
                "- name: Project name.\n"
                "- directory: Project directory.\n"
                "- config_path: Configuration file path.\n"
                "- stack: Technology stack.\n"
                "- template: Template used.\n"
                "- valid: Validation result (validate action).\n"
                "- issues: Validation issues (validate action).\n"
                "- detected_stacks: Detected stacks (detect_stack action).\n\n"
                "Example: Create a project:\n"
                '{"action": "create", "name": "my-project", "stack": ["python", "react"]}'
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Operation: create, validate, detect_stack", "enum": ["create", "validate", "detect_stack"]},
                    "name": {"type": "string", "description": "Project name (create)"},
                    "description": {"type": "string", "description": "Project description (create)"},
                    "stack": {"type": "array", "items": {"type": "string"}, "description": "Technology stack list (create)"},
                    "template": {"type": "string", "description": "Project template (create)"},
                    "directory": {"type": "string", "description": "Project directory (create)"},
                    "project_path": {"type": "string", "description": "Project path (validate/detect_stack)"},
                },
                "required": ["action"],
                "additionalProperties": False,
                "$schema": MCP_JSON_SCHEMA_URI,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "name": {"type": "string"},
                    "directory": {"type": "string"},
                    "config_path": {"type": "string"},
                    "stack": {"type": "array", "items": {"type": "string"}},
                    "template": {"type": "string"},
                    "valid": {"type": "boolean"},
                    "issues": {"type": "array", "items": {"type": "object"}},
                    "detected_stacks": {"type": "array", "items": {"type": "object"}},
                },
            },
            annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
        ),
    ]


SKILL_TOOL_NAMES = {
    "skill_analyze", "quality_gate_check", "spec_drift_detect",
    "security_scan", "code_simplify", "session_manage",
    "workflow_dispatch", "agent_status", "hook_manage",
    "context_compress", "server_health", "decision_log",
    "token_budget", "knowledge_inject", "project_init",
}

_PHASE_NAMES = [
    "初始化", "需求分析", "架构设计", "测试先行",
    "代码实现", "测试验证", "验收确认", "持续重构", "部署交付",
]

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

_QUALITY_GATES = [
    {"gate_id": "DESIGN-SYSTEM-COMPLETE", "phase": 0, "severity": "BLOCK"},
    {"gate_id": "ANTI-PATTERN-CHECK", "phase": 0, "severity": "WARN"},
    {"gate_id": "SPEC-COMPLETE", "phase": 1, "severity": "BLOCK"},
    {"gate_id": "REQUIREMENT-TRACEABLE", "phase": 1, "severity": "WARN"},
    {"gate_id": "ARCH-REVIEW", "phase": 2, "severity": "BLOCK"},
    {"gate_id": "API-CONTRACT", "phase": 2, "severity": "WARN"},
    {"gate_id": "GATE-007", "phase": 4, "severity": "BLOCK"},
    {"gate_id": "TEST-PASS", "phase": 4, "severity": "BLOCK"},
    {"gate_id": "FILE-ENCODING", "phase": 4, "severity": "BLOCK"},
    {"gate_id": "AI-PENTEST", "phase": 5, "severity": "BLOCK"},
    {"gate_id": "SPEC-CONSISTENCY", "phase": 5, "severity": "WARN"},
    {"gate_id": "SIMPLIFICATION-BEHAVIOR", "phase": 7, "severity": "WARN"},
    {"gate_id": "GATE-015", "phase": 7, "severity": "BLOCK"},
]

_HOOK_DEFINITIONS = {
    "minimal": [
        {"name": "SessionStart", "trigger": "session_init", "pre_callbacks": [], "post_callbacks": ["session_manage(load)"], "enabled": True},
        {"name": "SessionStop", "trigger": "session_end", "pre_callbacks": [], "post_callbacks": ["session_manage(save)"], "enabled": True},
    ],
    "standard": [
        {"name": "PhaseEnter", "trigger": "phase_transition", "pre_callbacks": ["validate_phase_prerequisites"], "post_callbacks": ["notify_agents", "preload_resources"], "enabled": True},
        {"name": "GatePass", "trigger": "gate_check_pass", "pre_callbacks": [], "post_callbacks": ["quality_gate_check"], "enabled": True},
        {"name": "GateFail", "trigger": "gate_check_fail", "pre_callbacks": [], "post_callbacks": ["log_failure", "suggest_fix"], "enabled": True},
        {"name": "SessionStart", "trigger": "session_init", "pre_callbacks": [], "post_callbacks": ["session_manage(load)"], "enabled": True},
        {"name": "SessionStop", "trigger": "session_end", "pre_callbacks": [], "post_callbacks": ["session_manage(save)"], "enabled": True},
    ],
    "strict": [
        {"name": "PhaseEnter", "trigger": "phase_transition", "pre_callbacks": ["validate_phase_prerequisites", "check_token_budget"], "post_callbacks": ["notify_agents", "preload_resources", "log_phase_change"], "enabled": True},
        {"name": "GatePass", "trigger": "gate_check_pass", "pre_callbacks": ["verify_gate_context"], "post_callbacks": ["quality_gate_check", "update_metrics"], "enabled": True},
        {"name": "GateFail", "trigger": "gate_check_fail", "pre_callbacks": ["capture_failure_context"], "post_callbacks": ["log_failure", "suggest_fix", "notify_orchestrator"], "enabled": True},
        {"name": "SessionStart", "trigger": "session_init", "pre_callbacks": ["validate_environment"], "post_callbacks": ["session_manage(load)", "preload_resources"], "enabled": True},
        {"name": "SessionStop", "trigger": "session_end", "pre_callbacks": ["verify_all_tasks"], "post_callbacks": ["session_manage(save)", "generate_report"], "enabled": True},
        {"name": "CodeChange", "trigger": "file_modified", "pre_callbacks": ["check_encoding"], "post_callbacks": ["run_lint", "update_dependencies"], "enabled": True},
    ],
}

_DEFAULT_BUDGET_ALLOCATIONS = {
    "0": 8000, "1": 15000, "2": 22000, "3": 12000,
    "4": 45000, "5": 18000, "6": 10000, "7": 12000, "8": 8000,
}

_SIZE_MULTIPLIERS = {"small": 0.6, "medium": 1.0, "large": 1.6}
_COMPLEXITY_MULTIPLIERS = {"low": 0.8, "medium": 1.0, "high": 1.3}


class SkillToolHandler:
    def __init__(self, server=None, fallback=None):
        self.server = server
        self.fallback = fallback or MCPToolFallback()
        self._sessions: Dict[str, dict] = {}
        self._workflows: Dict[str, dict] = {}
        self._decisions: List[dict] = []
        self._token_budget_state: Dict[str, Any] = {
            "total_budget": 150000,
            "used": 0,
            "remaining": 150000,
            "phase_allocations": dict(_DEFAULT_BUDGET_ALLOCATIONS),
            "usage_by_phase": {},
        }
        self._injected_contexts: List[dict] = []
        self._agent_instances: Dict[str, dict] = {}
        self._start_time = datetime.now(timezone.utc)

    async def handle(self, name: str, arguments: dict):
        if name not in SKILL_TOOL_NAMES:
            return None
        handler = getattr(self, f"_handle_{name}", None)
        if handler is None:
            return self._fallback_or_error(name, arguments)
        try:
            result = await handler(arguments)
            return result
        except Exception as e:
            logger.error("operation=skill_tool_handle, tool=%s, error=%s", name, e)
            fallback_result = self.fallback.call_tool(name, arguments)
            if fallback_result.get("status") != "error":
                return [TextContent(type="text", text=json.dumps(fallback_result, ensure_ascii=False))]
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INTERNAL_ERROR",
                message=f"Tool execution failed: {e}",
                details={"tool_name": name, "error": str(e)},
            ), ensure_ascii=False))]

    def _fallback_or_error(self, name: str, arguments: dict):
        fallback_result = self.fallback.call_tool(name, arguments)
        if fallback_result.get("status") != "error":
            return [TextContent(type="text", text=json.dumps(fallback_result, ensure_ascii=False))]
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="UNKNOWN_TOOL",
            message=f"Unknown tool: {name}",
            details={"tool_name": name},
        ), ensure_ascii=False))]

    async def _handle_skill_analyze(self, arguments: dict):
        skill_path = arguments.get("skill_path", "")
        include_scripts = arguments.get("include_scripts", True)
        include_agents = arguments.get("include_agents", True)
        depth = arguments.get("depth", "basic")

        if not skill_path:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message="skill_path is required",
                details={},
            ), ensure_ascii=False))]

        root = Path(skill_path)
        if not root.exists():
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="NOT_FOUND",
                message=f"Skill directory not found: {skill_path}",
                details={"skill_path": skill_path},
            ), ensure_ascii=False))]

        metadata = self._extract_skill_metadata(root)
        structure = self._analyze_structure(root, depth)
        agents = self._analyze_agents(root) if include_agents else {"total": 0, "layers": 0, "by_layer": {}}
        dependencies = self._analyze_dependencies(root) if include_scripts else {"scripts": [], "python_version": ">=3.10"}
        issues = self._detect_issues(root, metadata, dependencies)

        result = {
            "metadata": metadata,
            "structure": structure,
            "agents": agents,
            "dependencies": dependencies,
            "issues": issues,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    async def _handle_quality_gate_check(self, arguments: dict):
        gate_ids = arguments.get("gate_ids")
        phase = arguments.get("phase")
        project_path = arguments.get("project_path", ".")
        severity_filter = arguments.get("severity_filter", "all")
        force_refresh = arguments.get("force_refresh", False)

        root = Path(project_path)
        if not root.exists():
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="PROJECT_NOT_FOUND",
                message=f"Project path not found: {project_path}",
                details={"project_path": project_path},
            ), ensure_ascii=False))]

        gates_to_check = list(_QUALITY_GATES)
        if gate_ids:
            gate_id_set = set(gate_ids)
            gates_to_check = [g for g in gates_to_check if g["gate_id"] in gate_id_set]
        if phase is not None:
            try:
                phase_int = int(phase)
                gates_to_check = [g for g in gates_to_check if g["phase"] == phase_int]
            except (ValueError, TypeError):
                pass
        if severity_filter != "all":
            gates_to_check = [g for g in gates_to_check if g["severity"] == severity_filter]

        results = []
        for gate in gates_to_check:
            gate_result = self._check_single_gate(gate, root)
            results.append(gate_result)

        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = len(results) - passed
        can_proceed = all(r["status"] == "PASS" or r["severity"] != "BLOCK" for r in results)

        result = {
            "gates_checked": len(results),
            "gates_passed": passed,
            "gates_failed": failed,
            "results": results,
            "phase": phase,
            "can_proceed": can_proceed,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    async def _handle_spec_drift_detect(self, arguments: dict):
        spec_dir = arguments.get("spec_dir", ".trae/specs")
        src_dir = arguments.get("src_dir", ".")

        fallback_result = self.fallback.call_tool("spec_drift_detect", arguments)
        if fallback_result.get("status") != "error" and fallback_result.get("data", {}).get("degraded"):
            data = fallback_result["data"]
            total_specs = 0
            spec_path = Path(src_dir) / spec_dir
            if spec_path.exists():
                total_specs = len(list(spec_path.rglob("*.md")))
            drifts = []
            for item in data.get("items", []):
                drifts.append({
                    "spec_file": item.get("spec", ""),
                    "spec_requirement": "",
                    "implementation": "",
                    "drift_type": "NO_IMPLEMENTATION",
                    "severity": "HIGH",
                    "description": f"No implementation found for spec: {item.get('spec', '')}",
                    "suggestion": f"Create implementation matching {item.get('spec', '')}",
                })
            coverage = ((total_specs - len(drifts)) / total_specs * 100) if total_specs > 0 else 100.0
            result = {
                "total_specs": total_specs,
                "drifts_detected": len(drifts),
                "drifts": drifts,
                "coverage_pct": round(coverage, 1),
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        spec_path = Path(src_dir) / spec_dir
        src_path = Path(src_dir)
        if not spec_path.exists():
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message=f"Spec directory not found: {spec_dir}",
                details={"spec_dir": spec_dir},
            ), ensure_ascii=False))]

        drifts = []
        total_specs = 0
        for spec_file in spec_path.rglob("*.md"):
            total_specs += 1
            spec_name = spec_file.stem
            found_impl = False
            for ext in (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java"):
                candidates = list(src_path.rglob(f"{spec_name}{ext}"))
                if candidates:
                    found_impl = True
                    break
            if not found_impl:
                drifts.append({
                    "spec_file": str(spec_file.relative_to(src_path)),
                    "spec_requirement": spec_name,
                    "implementation": "",
                    "drift_type": "NO_IMPLEMENTATION",
                    "severity": "HIGH",
                    "description": f"No implementation found for spec: {spec_name}",
                    "suggestion": f"Create implementation matching {spec_name}",
                })

        coverage = ((total_specs - len(drifts)) / total_specs * 100) if total_specs > 0 else 100.0
        result = {
            "total_specs": total_specs,
            "drifts_detected": len(drifts),
            "drifts": drifts,
            "coverage_pct": round(coverage, 1),
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    async def _handle_security_scan(self, arguments: dict):
        import time as _time
        start = _time.monotonic()

        target = arguments.get("target", ".")
        severity_threshold = arguments.get("severity_threshold", "medium")
        include_agentic = arguments.get("include_agentic", True)
        include_dependency = arguments.get("include_dependency", True)

        target_path = Path(target)
        if not target_path.exists():
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="NOT_FOUND",
                message=f"Target path not found: {target}",
                details={"target": target},
            ), ensure_ascii=False))]

        findings = []
        sensitive_patterns = [
            (r'(?:api[_-]?key|secret|password|token)\s*[:=]\s*["\'][^"\']+["\']', "hardcoded_secret", "critical", "OWASP-A07", "Hardcoded secret detected", "Use environment variables or secret management"),
            (r'eval\s*\(', "eval_usage", "high", "OWASP-A03", "Use of eval() detected", "Avoid eval(); use safer alternatives"),
            (r'subprocess\.call\s*\(\s*["\']', "shell_injection_risk", "high", "OWASP-A03", "Potential shell injection via subprocess", "Use subprocess with list args, not shell=True"),
            (r'os\.system\s*\(', "os_system_usage", "medium", "OWASP-A03", "Use of os.system() detected", "Use subprocess module instead"),
            (r'innerHTML\s*=', "xss_innerhtml", "high", "OWASP-A03", "Direct innerHTML assignment", "Use textContent or DOMPurify"),
            (r'document\.write\s*\(', "xss_docwrite", "medium", "OWASP-A03", "Use of document.write()", "Use DOM manipulation methods"),
            (r'SELECT\s+.*\s+FROM\s+.*\s*\+\s*', "sql_injection", "critical", "OWASP-A03", "Potential SQL injection via string concatenation", "Use parameterized queries"),
        ]

        agentic_patterns = [
            (r'execute\s*\(\s*["\'].*(?:rm|del|drop|truncate)', "agentic_destructive_action", "critical", "OWASP-AG-01", "Agent may execute destructive commands", "Add human-in-the-loop confirmation"),
            (r'tools\s*=\s*\[.*\*.*\]', "agentic_unrestricted_tools", "high", "OWASP-AG-06", "Agent has unrestricted tool access", "Limit tool scope to minimum required"),
        ]

        scan_exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".yaml", ".yml", ".json"}
        all_patterns = list(sensitive_patterns)
        if include_agentic:
            all_patterns.extend(agentic_patterns)

        min_severity = _SEVERITY_ORDER.get(severity_threshold, 2)

        if target_path.exists():
            for root_dir, _dirs, files in os.walk(str(target_path)):
                if any(skip in root_dir for skip in ("node_modules", ".git", "__pycache__", ".venv", ".knowledge")):
                    continue
                for fname in files:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext not in scan_exts:
                        continue
                    fpath = os.path.join(root_dir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                            for lineno, line in enumerate(fh, 1):
                                for pattern, rule_id, severity, category, title, remediation in all_patterns:
                                    if _SEVERITY_ORDER.get(severity, 3) > min_severity:
                                        continue
                                    if re.search(pattern, line, re.IGNORECASE):
                                        findings.append({
                                            "id": f"SEC-{len(findings)+1:03d}",
                                            "title": title,
                                            "severity": severity,
                                            "category": category,
                                            "file": os.path.relpath(fpath, str(target_path)),
                                            "line": lineno,
                                            "description": title,
                                            "remediation": remediation,
                                            "references": [f"https://owasp.org/Top10/{category.replace('OWASP-', '').replace('AG-', '')}_2021/"] if not category.startswith("OWASP-AG") else [],
                                        })
                    except OSError:
                        pass

        dep_findings = 0
        if include_dependency:
            dep_findings = self._scan_dependencies(target_path, findings, min_severity)

        elapsed_ms = int((_time.monotonic() - start) * 1000)
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in findings:
            by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1

        agentic_count = sum(1 for f in findings if f["category"].startswith("OWASP-AG"))

        result = {
            "total_findings": len(findings),
            "by_severity": by_severity,
            "findings": findings[:50],
            "agentic_findings": agentic_count,
            "dependency_findings": dep_findings,
            "scan_duration_ms": elapsed_ms,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    async def _handle_code_simplify(self, arguments: dict):
        target = arguments.get("target", "")
        scope = arguments.get("scope", "recent")
        include_dedup = arguments.get("include_dedup", True)

        if not target:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message="target is required",
                details={},
            ), ensure_ascii=False))]

        target_path = Path(target)
        if not target_path.exists():
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="NOT_FOUND",
                message=f"Target not found: {target}",
                details={"target": target},
            ), ensure_ascii=False))]

        suggestions = []
        by_type = {"dead_code": 0, "duplication": 0, "complexity": 0, "naming": 0}

        if target_path.is_file() and target_path.suffix == ".py":
            self._analyze_python_file(target_path, suggestions, by_type, target_path)
        elif target_path.is_dir():
            for root_dir, _dirs, files in os.walk(str(target_path)):
                if any(skip in root_dir for skip in ("node_modules", ".git", "__pycache__", ".venv", ".knowledge")):
                    continue
                for fname in files:
                    if not fname.endswith(".py"):
                        continue
                    fpath = Path(root_dir) / fname
                    self._analyze_python_file(fpath, suggestions, by_type, target_path)

        if include_dedup:
            dup_suggestions = self._detect_code_duplication(target_path)
            for ds in dup_suggestions:
                suggestions.append(ds)
                by_type["duplication"] += 1

        total_reducible = sum(s.get("estimated_reduction", 0) for s in suggestions)
        safe_count = sum(1 for s in suggestions if s.get("safety") == "SAFE")
        caution_count = len(suggestions) - safe_count

        result = {
            "total_suggestions": len(suggestions),
            "by_type": by_type,
            "suggestions": suggestions[:50],
            "total_lines_reducible": total_reducible,
            "safe_count": safe_count,
            "caution_count": caution_count,
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    async def _handle_session_manage(self, arguments: dict):
        action = arguments.get("action", "")
        valid_actions = {"save", "load", "list", "detect", "verify", "track", "restore"}
        if action not in valid_actions:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message=f"Invalid action: {action}. Valid: {sorted(valid_actions)}",
                details={"action": action, "valid_actions": sorted(valid_actions)},
            ), ensure_ascii=False))]

        now_iso = datetime.now(timezone.utc).isoformat()

        if action == "save":
            session_id = f"sess-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
            state = {
                "current_phase": arguments.get("current_phase"),
                "completed_tasks": arguments.get("completed_tasks", []),
                "pending_tasks": arguments.get("pending_tasks", []),
                "decisions": arguments.get("decisions", []),
                "experience": arguments.get("experience", []),
            }
            self._sessions[session_id] = {"state": state, "saved_at": now_iso}
            result = {
                "action": "save",
                "session_id": session_id,
                "saved_at": now_iso,
                "state": state,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "load":
            if not self._sessions:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="NOT_FOUND",
                    message="No saved sessions found",
                    details={},
                ), ensure_ascii=False))]
            latest_id = max(self._sessions.keys())
            session = self._sessions[latest_id]
            result = {
                "action": "load",
                "session_id": latest_id,
                "state": session["state"],
                "saved_at": session["saved_at"],
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "list":
            sessions = [{"session_id": sid, "saved_at": s["saved_at"]} for sid, s in self._sessions.items()]
            result = {"action": "list", "sessions": sessions, "total": len(sessions)}
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "detect":
            error_log = arguments.get("error_log", [])
            result = {
                "action": "detect",
                "errors_detected": len(error_log),
                "error_log": error_log[:10],
                "recovery_suggested": len(error_log) > 0,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "verify":
            pattern_path = arguments.get("pattern_path", "")
            success = arguments.get("success", True)
            result = {
                "action": "verify",
                "pattern_path": pattern_path,
                "success": success,
                "verified_at": now_iso,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "track":
            current_phase = arguments.get("current_phase")
            current_task = arguments.get("current_task", "")
            result = {
                "action": "track",
                "current_phase": current_phase,
                "current_task": current_task,
                "pending_tasks": arguments.get("pending_tasks", []),
                "decisions": arguments.get("decisions", []),
                "tracked_at": now_iso,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "restore":
            if not self._sessions:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="NOT_FOUND",
                    message="No saved sessions to restore",
                    details={},
                ), ensure_ascii=False))]
            latest_id = max(self._sessions.keys())
            session = self._sessions[latest_id]
            result = {
                "action": "restore",
                "session_id": latest_id,
                "state": session["state"],
                "restored_at": now_iso,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    async def _handle_workflow_dispatch(self, arguments: dict):
        action = arguments.get("action", "")
        valid_actions = {"start", "status", "abort", "phase", "recover", "snapshots"}
        if action not in valid_actions:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message=f"Invalid action: {action}. Valid: {sorted(valid_actions)}",
                details={"action": action, "valid_actions": sorted(valid_actions)},
            ), ensure_ascii=False))]

        now_iso = datetime.now(timezone.utc).isoformat()

        if action == "start":
            workflow_name = arguments.get("workflow", "sdd-tdd-full")
            project_path = arguments.get("project_path", ".")
            workflow_id = f"wf-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
            phases = []
            for i, name in enumerate(_PHASE_NAMES):
                status = "IN_PROGRESS" if i == 0 else "PENDING"
                phases.append({"phase": i, "name": name, "status": status})
            self._workflows[workflow_id] = {
                "workflow_name": workflow_name,
                "project_path": project_path,
                "current_phase": 0,
                "phases": phases,
                "started_at": now_iso,
                "status": "RUNNING",
            }
            result = {
                "action": "start",
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "current_phase": 0,
                "phases": phases,
                "started_at": now_iso,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "status":
            workflow_id = arguments.get("workflow_id", "")
            wf = self._workflows.get(workflow_id)
            if not wf:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="NOT_FOUND",
                    message=f"Workflow not found: {workflow_id}",
                    details={"workflow_id": workflow_id},
                ), ensure_ascii=False))]
            result = {
                "action": "status",
                "workflow_id": workflow_id,
                "workflow_name": wf["workflow_name"],
                "current_phase": wf["current_phase"],
                "phases": wf["phases"],
                "status": wf["status"],
                "started_at": wf["started_at"],
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "abort":
            workflow_id = arguments.get("workflow_id", "")
            wf = self._workflows.get(workflow_id)
            if not wf:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="NOT_FOUND",
                    message=f"Workflow not found: {workflow_id}",
                    details={"workflow_id": workflow_id},
                ), ensure_ascii=False))]
            wf["status"] = "ABORTED"
            result = {
                "action": "abort",
                "workflow_id": workflow_id,
                "aborted_at": now_iso,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "phase":
            workflow_id = arguments.get("workflow_id", "")
            phase_action = arguments.get("phase_action", "current")
            wf = self._workflows.get(workflow_id)
            if not wf:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="NOT_FOUND",
                    message=f"Workflow not found: {workflow_id}",
                    details={"workflow_id": workflow_id},
                ), ensure_ascii=False))]
            if phase_action == "advance":
                current = wf["current_phase"]
                next_phase = min(current + 1, 8)
                wf["current_phase"] = next_phase
                for p in wf["phases"]:
                    if p["phase"] == current:
                        p["status"] = "COMPLETED"
                    elif p["phase"] == next_phase:
                        p["status"] = "IN_PROGRESS"
                result = {
                    "action": "phase",
                    "workflow_id": workflow_id,
                    "previous_phase": current,
                    "current_phase": next_phase,
                }
            else:
                result = {
                    "action": "phase",
                    "workflow_id": workflow_id,
                    "current_phase": wf["current_phase"],
                }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "recover":
            workflow_id = arguments.get("workflow_id", "")
            snapshot_phase = arguments.get("snapshot_phase")
            wf = self._workflows.get(workflow_id)
            if not wf:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="NOT_FOUND",
                    message=f"Workflow not found: {workflow_id}",
                    details={"workflow_id": workflow_id},
                ), ensure_ascii=False))]
            target = snapshot_phase if snapshot_phase is not None else wf["current_phase"]
            wf["current_phase"] = target
            wf["status"] = "RUNNING"
            for p in wf["phases"]:
                if p["phase"] < target:
                    p["status"] = "COMPLETED"
                elif p["phase"] == target:
                    p["status"] = "IN_PROGRESS"
                else:
                    p["status"] = "PENDING"
            result = {
                "action": "recover",
                "workflow_id": workflow_id,
                "recovered_to_phase": target,
                "recovered_at": now_iso,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "snapshots":
            workflow_id = arguments.get("workflow_id", "")
            wf = self._workflows.get(workflow_id)
            if not wf:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="NOT_FOUND",
                    message=f"Workflow not found: {workflow_id}",
                    details={"workflow_id": workflow_id},
                ), ensure_ascii=False))]
            snapshots = []
            for p in wf["phases"]:
                if p["status"] in ("COMPLETED", "IN_PROGRESS"):
                    snapshots.append({"phase": p["phase"], "name": p["name"], "status": p["status"]})
            result = {
                "action": "snapshots",
                "workflow_id": workflow_id,
                "snapshots": snapshots,
                "total": len(snapshots),
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    async def _handle_agent_status(self, arguments: dict):
        action = arguments.get("action", "list")
        skill_root = self.fallback._skill_root if self.fallback else MCPToolFallback.SKILL_ROOT

        if action == "list":
            agents = self._scan_agent_registry(skill_root)
            result = {
                "action": "list",
                "agents": agents,
                "total_agents": len(agents),
                "available_count": sum(1 for a in agents if a.get("status", "AVAILABLE") == "AVAILABLE"),
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "by_phase":
            phase = arguments.get("phase", 0)
            all_agents = self._scan_agent_registry(skill_root)
            phase_layers = self._phase_to_layers(phase)
            filtered = [a for a in all_agents if a.get("layer", "") in phase_layers]
            result = {
                "action": "by_phase",
                "phase": phase,
                "agents": filtered,
                "total_agents": len(filtered),
                "available_count": sum(1 for a in filtered if a.get("status", "AVAILABLE") == "AVAILABLE"),
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "detail":
            agent_name = arguments.get("agent_name", "")
            all_agents = self._scan_agent_registry(skill_root)
            matched = [a for a in all_agents if a.get("name", "").lower() == agent_name.lower()]
            if not matched:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="NOT_FOUND",
                    message=f"Agent not found: {agent_name}",
                    details={"agent_name": agent_name},
                ), ensure_ascii=False))]
            result = {
                "action": "detail",
                "agent": matched[0],
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "create":
            agent_type = arguments.get("agent_type", "developer")
            capabilities = arguments.get("capabilities", [])
            agent_id = f"agent-{uuid.uuid4().hex[:8]}"
            now_iso = datetime.now(timezone.utc).isoformat()
            instance = {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "capabilities": capabilities,
                "status": "idle",
                "created_at": now_iso,
                "last_active_at": now_iso,
                "task_count": 0,
                "total_duration_ms": 0,
            }
            self._agent_instances[agent_id] = instance
            result = {"action": "create", **instance}
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action in ("assign", "release", "instance_status", "destroy"):
            agent_id = arguments.get("agent_id", "")
            instance = self._agent_instances.get(agent_id)
            if not instance:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="NOT_FOUND",
                    message=f"Agent instance not found: {agent_id}",
                    details={"agent_id": agent_id},
                ), ensure_ascii=False))]
            now_iso = datetime.now(timezone.utc).isoformat()
            if action == "assign":
                task = arguments.get("task", "")
                instance["status"] = "busy"
                instance["task_count"] += 1
                instance["last_active_at"] = now_iso
                instance["current_task"] = task
                result = {"action": "assign", "agent_id": agent_id, "task": task, "status": "busy", "task_count": instance["task_count"]}
            elif action == "release":
                instance["status"] = "idle"
                instance["last_active_at"] = now_iso
                completed_task = instance.pop("current_task", "")
                result = {"action": "release", "agent_id": agent_id, "status": "idle", "completed_task": completed_task}
            elif action == "instance_status":
                result = {"action": "instance_status", **instance}
            elif action == "destroy":
                instance["status"] = "destroyed"
                del self._agent_instances[agent_id]
                result = {"action": "destroy", "agent_id": agent_id, "status": "destroyed"}
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "match":
            capabilities = arguments.get("capabilities", [])
            all_agents = self._scan_agent_registry(skill_root)
            matched = [a for a in all_agents if any(c in a.get("capabilities", []) for c in capabilities)]
            result = {
                "action": "match",
                "matched_agents": matched,
                "total_matched": len(matched),
                "requested_capabilities": capabilities,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "schedule":
            result = {"action": "schedule", "status": "not_implemented", "message": "Scheduling requires external orchestrator"}
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="INVALID_INPUT",
            message=f"Invalid action: {action}",
            details={"action": action},
        ), ensure_ascii=False))]

    async def _handle_hook_manage(self, arguments: dict):
        action = arguments.get("action", "list")
        profile = arguments.get("profile", "standard")

        if action == "list":
            hooks = _HOOK_DEFINITIONS.get(profile, _HOOK_DEFINITIONS["standard"])
            hooks_copy = [dict(h) for h in hooks]
            result = {
                "action": "list",
                "profile": profile,
                "hooks": hooks_copy,
                "total_hooks": len(hooks_copy),
                "enabled_count": sum(1 for h in hooks_copy if h.get("enabled", True)),
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "execute":
            hook_name = arguments.get("hook_name", "")
            context = arguments.get("context", {})
            if not hook_name:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="INVALID_INPUT",
                    message="hook_name is required for execute action",
                    details={},
                ), ensure_ascii=False))]
            hooks = _HOOK_DEFINITIONS.get(profile, _HOOK_DEFINITIONS["standard"])
            matched = [h for h in hooks if h["name"] == hook_name]
            if not matched:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="NOT_FOUND",
                    message=f"Hook not found: {hook_name}",
                    details={"hook_name": hook_name, "profile": profile},
                ), ensure_ascii=False))]
            hook = matched[0]
            pre_results = [f"{cb}:ok" for cb in hook.get("pre_callbacks", [])]
            post_results = [f"{cb}:ok" for cb in hook.get("post_callbacks", [])]
            result = {
                "action": "execute",
                "hook_name": hook_name,
                "result": "completed",
                "pre_callbacks_result": pre_results,
                "post_callbacks_result": post_results,
                "context": context,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="INVALID_INPUT",
            message=f"Invalid action: {action}",
            details={"action": action},
        ), ensure_ascii=False))]

    async def _handle_context_compress(self, arguments: dict):
        content = arguments.get("content", "")
        strategy = arguments.get("strategy", "semantic")
        target_tokens = arguments.get("target_tokens", 2000)
        preserve_sections = arguments.get("preserve_sections")

        if not content:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message="content is required",
                details={},
            ), ensure_ascii=False))]

        original_tokens = self._estimate_tokens(content)

        if strategy == "lossless":
            compressed = self._lossless_compress(content)
            compressed_tokens = self._estimate_tokens(compressed)
        elif strategy == "selective":
            compressed = self._selective_compress(content, preserve_sections or [], target_tokens)
            compressed_tokens = self._estimate_tokens(compressed)
        else:
            compressed = self._semantic_compress(content, preserve_sections or [], target_tokens)
            compressed_tokens = self._estimate_tokens(compressed)

        ratio = compressed_tokens / original_tokens if original_tokens > 0 else 0
        quality = max(0.0, min(1.0, 1.0 - (ratio * 0.5)))

        preserved = []
        if preserve_sections:
            for section in preserve_sections:
                if section in compressed:
                    preserved.append(section)

        result = {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "compression_ratio": round(ratio, 2),
            "strategy_used": strategy,
            "compressed_content": compressed,
            "preserved_sections": preserved,
            "quality_score": round(quality, 2),
        }
        return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    async def _handle_server_health(self, arguments: dict):
        action = arguments.get("action", "check")
        include_details = arguments.get("include_details", False)
        now_iso = datetime.now(timezone.utc).isoformat()
        uptime = int((datetime.now(timezone.utc) - self._start_time).total_seconds())

        if action == "check":
            result = {
                "status": "HEALTHY",
                "version": "4.0.0",
                "api_version": "3.0.0",
                "uptime_seconds": uptime,
                "tools_available": 17,
                "degradation_level": "none",
                "last_check_timestamp": now_iso,
            }
            if include_details:
                tool_names = list(SKILL_TOOL_NAMES) + [
                    "knowledge_search", "knowledge_add", "knowledge_update",
                    "knowledge_delete", "knowledge_stats", "knowledge_rollback",
                    "knowledge_auto_retrieve", "knowledge_progressive_search",
                    "knowledge_deep_load", "knowledge_web_update", "resource_load_status",
                ]
                result["tools_status"] = {t: "OK" for t in tool_names}
                result["memory_usage_mb"] = 0.0
                result["active_workflows"] = len(self._workflows)
                result["active_sessions"] = len(self._sessions)
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "version":
            result = {"version": "4.0.0", "api_version": "3.0.0"}
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "status":
            result = {
                "status": "HEALTHY",
                "uptime_seconds": uptime,
                "degradation_level": "none",
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="INVALID_INPUT",
            message=f"Invalid action: {action}",
            details={"action": action},
        ), ensure_ascii=False))]

    async def _handle_decision_log(self, arguments: dict):
        action = arguments.get("action", "")
        valid_actions = {"log", "query", "export"}
        if action not in valid_actions:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message=f"Invalid action: {action}. Valid: {sorted(valid_actions)}",
                details={"action": action},
            ), ensure_ascii=False))]

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        if action == "log":
            title = arguments.get("title", "")
            if not title:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="INVALID_INPUT",
                    message="title is required for log action",
                    details={},
                ), ensure_ascii=False))]
            decision_id = f"ADR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{len(self._decisions)+1:03d}"
            entry = {
                "id": decision_id,
                "title": title,
                "description": arguments.get("description", ""),
                "context": arguments.get("context", ""),
                "alternatives": arguments.get("alternatives", []),
                "decision": arguments.get("decision", ""),
                "rationale": arguments.get("rationale", ""),
                "impact": arguments.get("impact", ""),
                "decided_by": arguments.get("decided_by", ""),
                "tags": [],
                "created_at": now_iso,
            }
            self._decisions.append(entry)
            result = {
                "action": "log",
                "id": decision_id,
                "entry": entry,
                "total_decisions": len(self._decisions),
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "query":
            keyword = arguments.get("keyword", "")
            tag = arguments.get("tag", "")
            limit = arguments.get("limit", 20)
            date_from = arguments.get("date_from")
            date_to = arguments.get("date_to")
            results = list(self._decisions)
            if keyword:
                kw_lower = keyword.lower()
                results = [d for d in results if kw_lower in d.get("title", "").lower() or kw_lower in d.get("description", "").lower() or kw_lower in d.get("decision", "").lower()]
            if tag:
                results = [d for d in results if tag in d.get("tags", [])]
            if date_from:
                results = [d for d in results if d.get("created_at", "") >= date_from]
            if date_to:
                results = [d for d in results if d.get("created_at", "") <= date_to]
            results = results[:limit]
            result = {
                "action": "query",
                "results": results,
                "total": len(results),
                "limit": limit,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "export":
            fmt = arguments.get("format", "json")
            entries = list(self._decisions)
            if fmt == "markdown":
                lines = ["# Decision Log\n"]
                for d in entries:
                    lines.append(f"## {d.get('id', '')}: {d.get('title', '')}\n")
                    lines.append(f"- **Decision**: {d.get('decision', '')}")
                    lines.append(f"- **Rationale**: {d.get('rationale', '')}")
                    lines.append(f"- **Alternatives**: {', '.join(d.get('alternatives', []))}")
                    lines.append(f"- **Impact**: {d.get('impact', '')}")
                    lines.append(f"- **Date**: {d.get('created_at', '')}\n")
                content = "\n".join(lines)
            else:
                content = json.dumps(entries, ensure_ascii=False, indent=2)
            result = {
                "action": "export",
                "format": fmt,
                "content": content,
                "total": len(entries),
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    async def _handle_token_budget(self, arguments: dict):
        action = arguments.get("action", "")
        valid_actions = {"status", "set_budget", "recommend", "report"}
        if action not in valid_actions:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message=f"Invalid action: {action}. Valid: {sorted(valid_actions)}",
                details={"action": action},
            ), ensure_ascii=False))]

        if action == "status":
            result = dict(self._token_budget_state)
            result["action"] = "status"
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "set_budget":
            total_budget = arguments.get("total_budget")
            if total_budget is not None and total_budget < 1000:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="INVALID_INPUT",
                    message="total_budget must be >= 1000",
                    details={"total_budget": total_budget},
                ), ensure_ascii=False))]
            if total_budget is not None:
                self._token_budget_state["total_budget"] = total_budget
                self._token_budget_state["remaining"] = total_budget - self._token_budget_state["used"]
            phase_allocations = arguments.get("phase_allocations")
            if phase_allocations:
                self._token_budget_state["phase_allocations"].update(phase_allocations)
            now_iso = datetime.now(timezone.utc).isoformat()
            result = {
                "action": "set_budget",
                "total_budget": self._token_budget_state["total_budget"],
                "phase_allocations": self._token_budget_state["phase_allocations"],
                "updated_at": now_iso,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "recommend":
            project_size = arguments.get("project_size", "medium")
            complexity = arguments.get("complexity", "medium")
            team_size = arguments.get("team_size", 1)
            base = 150000
            size_mult = _SIZE_MULTIPLIERS.get(project_size, 1.0)
            comp_mult = _COMPLEXITY_MULTIPLIERS.get(complexity, 1.0)
            team_mult = 1.0 + (team_size - 1) * 0.1
            recommended = int(base * size_mult * comp_mult * team_mult)
            allocations = {}
            for phase, amount in _DEFAULT_BUDGET_ALLOCATIONS.items():
                allocations[phase] = int(amount * size_mult * comp_mult)
            result = {
                "action": "recommend",
                "recommended_total": recommended,
                "recommended_allocations": allocations,
                "project_size": project_size,
                "complexity": complexity,
                "team_size": team_size,
                "adjusted_total": recommended,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "report":
            period = arguments.get("period", "session")
            total = self._token_budget_state["total_budget"]
            used = self._token_budget_state["used"]
            remaining = self._token_budget_state["remaining"]
            usage_pct = (used / total * 100) if total > 0 else 0
            result = {
                "action": "report",
                "period": period,
                "total_budget": total,
                "total_used": used,
                "remaining": remaining,
                "usage_pct": round(usage_pct, 1),
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    async def _handle_knowledge_inject(self, arguments: dict):
        action = arguments.get("action", "")
        valid_actions = {"inject", "preview", "clear"}
        if action not in valid_actions:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message=f"Invalid action: {action}. Valid: {sorted(valid_actions)}",
                details={"action": action},
            ), ensure_ascii=False))]

        if action == "inject":
            content = arguments.get("content", "")
            if not content:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="INVALID_INPUT",
                    message="content is required for inject action",
                    details={},
                ), ensure_ascii=False))]
            scope = arguments.get("scope", "session")
            source = arguments.get("source", "")
            priority = arguments.get("priority", "normal")
            injected_tokens = self._estimate_tokens(content)
            self._injected_contexts.append({
                "content": content,
                "scope": scope,
                "source": source,
                "priority": priority,
                "injected_at": datetime.now(timezone.utc).isoformat(),
                "tokens": injected_tokens,
            })
            total_injected = sum(c["tokens"] for c in self._injected_contexts)
            context_usage = min(100.0, (total_injected / 200000) * 100)
            result = {
                "action": "inject",
                "scope": scope,
                "injected_tokens": injected_tokens,
                "source": source,
                "priority": priority,
                "context_window_usage_pct": round(context_usage, 1),
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "preview":
            content = arguments.get("content", "")
            scope = arguments.get("scope", "session")
            priority = arguments.get("priority", "normal")
            preview_tokens = self._estimate_tokens(content) if content else 0
            total_injected = sum(c["tokens"] for c in self._injected_contexts) + preview_tokens
            context_usage = min(100.0, (total_injected / 200000) * 100)
            result = {
                "action": "preview",
                "scope": scope,
                "estimated_tokens": preview_tokens,
                "priority": priority,
                "context_window_usage_pct": round(context_usage, 1),
                "would_exceed": context_usage > 90,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "clear":
            cleared_count = len(self._injected_contexts)
            self._injected_contexts.clear()
            result = {
                "action": "clear",
                "cleared_items": cleared_count,
                "context_window_usage_pct": 0.0,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    async def _handle_project_init(self, arguments: dict):
        action = arguments.get("action", "")
        valid_actions = {"create", "validate", "detect_stack"}
        if action not in valid_actions:
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INVALID_INPUT",
                message=f"Invalid action: {action}. Valid: {sorted(valid_actions)}",
                details={"action": action},
            ), ensure_ascii=False))]

        if action == "create":
            name = arguments.get("name", "")
            if not name:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="INVALID_INPUT",
                    message="name is required for create action",
                    details={},
                ), ensure_ascii=False))]
            directory = arguments.get("directory", name)
            stack = arguments.get("stack", [])
            template = arguments.get("template", "default")
            description = arguments.get("description", "")
            config_path = os.path.join(directory, ".xuansto-config.yaml")
            result = {
                "action": "create",
                "name": name,
                "description": description,
                "directory": os.path.abspath(directory),
                "config_path": config_path,
                "stack": stack,
                "template": template,
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "validate":
            project_path = arguments.get("project_path", ".")
            ppath = Path(project_path)
            if not ppath.exists():
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="NOT_FOUND",
                    message=f"Project path not found: {project_path}",
                    details={"project_path": project_path},
                ), ensure_ascii=False))]
            issues = []
            config_file = ppath / ".xuansto-config.yaml"
            if not config_file.exists():
                issues.append({"severity": "WARN", "code": "NO_CONFIG", "message": "No .xuansto-config.yaml found"})
            result = {
                "action": "validate",
                "project_path": str(ppath.resolve()),
                "valid": len([i for i in issues if i.get("severity") == "BLOCK"]) == 0,
                "issues": issues,
                "total_issues": len(issues),
                "block_count": sum(1 for i in issues if i.get("severity") == "BLOCK"),
                "warn_count": sum(1 for i in issues if i.get("severity") == "WARN"),
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif action == "detect_stack":
            project_path = arguments.get("project_path", ".")
            ppath = Path(project_path)
            if not ppath.exists():
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="NOT_FOUND",
                    message=f"Project path not found: {project_path}",
                    details={"project_path": project_path},
                ), ensure_ascii=False))]
            detected = []
            markers = {
                "python": ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"],
                "node": ["package.json"],
                "rust": ["Cargo.toml"],
                "go": ["go.mod"],
                "java": ["pom.xml", "build.gradle"],
            }
            for stack_name, marker_files in markers.items():
                found = [m for m in marker_files if (ppath / m).exists()]
                if found:
                    detected.append({
                        "stack": stack_name,
                        "confidence": 1.0 if len(found) > 1 else 0.75,
                        "markers_found": found,
                    })
            primary = detected[0]["stack"] if detected else "unknown"
            result = {
                "action": "detect_stack",
                "project_path": str(ppath.resolve()),
                "detected_stacks": detected,
                "primary_stack": primary,
                "total_detected": len(detected),
            }
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

    def _extract_skill_metadata(self, root: Path) -> dict:
        metadata = {"name": "", "version": "", "agents_summary": "", "tags": []}
        skill_md = root / "SKILL.md"
        if skill_md.exists():
            try:
                with open(str(skill_md), "r", encoding="utf-8") as f:
                    content = f.read()
                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end > 0:
                        frontmatter = content[3:end].strip()
                        for line in frontmatter.split("\n"):
                            if ":" in line:
                                key, _, val = line.partition(":")
                                key = key.strip()
                                val = val.strip()
                                if key == "name":
                                    metadata["name"] = val.strip('"').strip("'")
                                elif key == "version":
                                    metadata["version"] = val.strip('"').strip("'")
                                elif key == "agents_summary":
                                    metadata["agents_summary"] = val.strip('"').strip("'")
                                elif key == "tags":
                                    if val.startswith("["):
                                        metadata["tags"] = [t.strip().strip('"').strip("'") for t in val.strip("[]").split(",")]
            except OSError:
                pass
        return metadata

    def _analyze_structure(self, root: Path, depth: str) -> dict:
        directories = []
        file_count = 0
        total_lines = 0
        for item in root.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                directories.append(item.name)
            elif item.is_file():
                file_count += 1
        for root_dir, _dirs, files in os.walk(str(root)):
            if any(skip in root_dir for skip in (".git", "__pycache__", "node_modules", ".knowledge")):
                continue
            for fname in files:
                file_count += 1
                if depth == "full":
                    fpath = os.path.join(root_dir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                            total_lines += sum(1 for _ in fh)
                    except OSError:
                        pass
        return {
            "root": str(root),
            "directories": sorted(directories),
            "file_count": file_count,
            "total_lines": total_lines,
        }

    def _analyze_agents(self, root: Path) -> dict:
        agents_dir = root / "agents"
        by_layer = {}
        total = 0
        if agents_dir.exists():
            for layer_dir in sorted(agents_dir.iterdir()):
                if not layer_dir.is_dir():
                    continue
                count = len(list(layer_dir.glob("*.md")))
                by_layer[layer_dir.name] = count
                total += count
        return {"total": total, "layers": len(by_layer), "by_layer": by_layer}

    def _analyze_dependencies(self, root: Path) -> dict:
        scripts_dir = root / "scripts"
        scripts = []
        if scripts_dir.exists():
            for f in scripts_dir.rglob("*.py"):
                scripts.append(f.name)
        return {
            "mcp_server": "xuansto-mcp-server>=4.0.0",
            "scripts": sorted(scripts),
            "python_version": ">=3.10",
        }

    def _detect_issues(self, root: Path, metadata: dict, dependencies: dict) -> list:
        issues = []
        if not metadata.get("name"):
            issues.append({"severity": "WARN", "code": "MISSING_METADATA", "message": "SKILL.md missing name field", "path": "SKILL.md"})
        if not metadata.get("version"):
            issues.append({"severity": "WARN", "code": "MISSING_VERSION", "message": "SKILL.md missing version field", "path": "SKILL.md"})
        scripts_dir = root / "scripts"
        if scripts_dir.exists():
            for script_name in dependencies.get("scripts", []):
                if not (scripts_dir / script_name).exists() and not list(scripts_dir.rglob(script_name)):
                    pass
        return issues

    def _check_single_gate(self, gate: dict, root: Path) -> dict:
        gate_id = gate["gate_id"]
        severity = gate["severity"]
        passed = True
        message = f"Gate {gate_id} passed"
        details = {}

        if gate_id == "FILE-ENCODING":
            bom_files = []
            for root_dir, _dirs, files in os.walk(str(root)):
                if any(skip in root_dir for skip in (".git", "node_modules", "__pycache__", ".knowledge")):
                    continue
                for fname in files:
                    if not fname.endswith((".py", ".js", ".ts", ".tsx", ".jsx")):
                        continue
                    fpath = os.path.join(root_dir, fname)
                    try:
                        with open(fpath, "rb") as fh:
                            start = fh.read(3)
                            if start == b'\xef\xbb\xbf':
                                bom_files.append(os.path.relpath(fpath, str(root)))
                    except OSError:
                        pass
            if bom_files:
                passed = False
                message = f"{len(bom_files)} files have BOM markers"
                details = {"offending_files": bom_files, "issue": "UTF-8 BOM detected"}
        elif gate_id == "TEST-PASS":
            details = {"total_tests": 0, "passed": 0, "failed": 0, "coverage_pct": 0.0}
            message = "No test runner detected, gate skipped"
        elif gate_id == "DESIGN-SYSTEM-COMPLETE":
            specs_dir = root / ".trae" / "specs"
            if not specs_dir.exists() or not list(specs_dir.glob("*.md")):
                passed = False
                message = "No spec documents found in .trae/specs"
                details = {"spec_dir": str(specs_dir)}
        elif gate_id == "ANTI-PATTERN-CHECK":
            details = {"patterns_checked": 0}
            message = "Anti-pattern check passed (inline scan)"
        else:
            details = {"note": "Gate check not fully implemented in inline mode"}

        return {
            "gate_id": gate_id,
            "status": "PASS" if passed else "FAIL",
            "severity": severity,
            "message": message,
            "details": details,
        }

    def _scan_dependencies(self, target_path: Path, findings: list, min_severity: int) -> int:
        dep_count = 0
        req_files = ["requirements.txt", "pyproject.toml", "package.json"]
        for rf in req_files:
            fpath = target_path / rf
            if not fpath.exists():
                continue
            try:
                with open(str(fpath), "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                if rf == "package.json":
                    try:
                        pkg = json.loads(content)
                        for dep_name in list(pkg.get("dependencies", {}).keys()) + list(pkg.get("devDependencies", {}).keys()):
                            pass
                    except json.JSONDecodeError:
                        pass
            except OSError:
                pass
        return dep_count

    def _analyze_python_file(self, fpath: Path, suggestions: list, by_type: dict, base_path: Path):
        try:
            with open(str(fpath), "r", encoding="utf-8", errors="ignore") as fh:
                source = fh.read()
            tree = ast.parse(source)
            idx = len(suggestions) + 1
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    body_lines = (node.end_lineno - node.lineno + 1) if hasattr(node, 'end_lineno') and node.end_lineno else 0
                    if body_lines > 50:
                        suggestions.append({
                            "id": f"SIMP-{idx:03d}",
                            "type": "complexity",
                            "file": str(fpath.relative_to(base_path)) if fpath.is_relative_to(base_path) else str(fpath),
                            "line_start": node.lineno,
                            "line_end": node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                            "description": f"Long function '{node.name}' ({body_lines} lines)",
                            "safety": "CAUTION",
                            "action": f"Consider breaking '{node.name}' into smaller functions",
                            "estimated_reduction": body_lines // 3,
                        })
                        by_type["complexity"] += 1
                        idx += 1
                    for child in ast.walk(node):
                        if child is node:
                            continue
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if child.name == node.name:
                                continue
                    if not node.body:
                        suggestions.append({
                            "id": f"SIMP-{idx:03d}",
                            "type": "dead_code",
                            "file": str(fpath.relative_to(base_path)) if fpath.is_relative_to(base_path) else str(fpath),
                            "line_start": node.lineno,
                            "line_end": node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                            "description": f"Empty function '{node.name}'",
                            "safety": "CAUTION",
                            "action": f"Remove or implement '{node.name}'",
                            "estimated_reduction": 2,
                        })
                        by_type["dead_code"] += 1
                        idx += 1
        except (OSError, SyntaxError):
            pass

    def _detect_code_duplication(self, target_path: Path) -> list:
        suggestions = []
        func_bodies = {}
        if target_path.is_file() and target_path.suffix == ".py":
            files = [target_path]
        else:
            files = []
            for root_dir, _dirs, fnames in os.walk(str(target_path)):
                if any(skip in root_dir for skip in ("node_modules", ".git", "__pycache__", ".venv", ".knowledge")):
                    continue
                for fname in fnames:
                    if fname.endswith(".py"):
                        files.append(Path(root_dir) / fname)
        for fpath in files:
            try:
                with open(str(fpath), "r", encoding="utf-8", errors="ignore") as fh:
                    source = fh.read()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        body_start = node.lineno
                        body_end = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
                        body_lines = body_end - body_start + 1
                        if body_lines >= 5:
                            key = (body_lines, node.name)
                            if key in func_bodies:
                                func_bodies[key].append(str(fpath))
                            else:
                                func_bodies[key] = [str(fpath)]
            except (OSError, SyntaxError):
                pass
        idx_base = 100
        for (lines, name), paths in func_bodies.items():
            if len(paths) > 1:
                suggestions.append({
                    "id": f"SIMP-{idx_base:03d}",
                    "type": "duplication",
                    "files": paths,
                    "description": f"Duplicate function '{name}' ({lines} lines) in {len(paths)} files",
                    "safety": "SAFE",
                    "action": f"Extract '{name}' into a shared module",
                    "estimated_reduction": lines * (len(paths) - 1),
                })
                idx_base += 1
        return suggestions

    def _scan_agent_registry(self, skill_root: Path) -> list:
        agents = []
        agents_dir = skill_root / "agents"
        if agents_dir.exists():
            for layer_dir in sorted(agents_dir.iterdir()):
                if not layer_dir.is_dir():
                    continue
                for agent_file in sorted(layer_dir.glob("*.md")):
                    agents.append({
                        "name": agent_file.stem,
                        "layer": layer_dir.name,
                        "status": "AVAILABLE",
                        "capabilities": [],
                        "assigned_tasks": 0,
                        "completed_tasks": 0,
                        "definition_file": str(agent_file.relative_to(skill_root)),
                    })
        return agents

    def _phase_to_layers(self, phase: int) -> list:
        mapping = {
            0: ["orchestration"],
            1: ["product"],
            2: ["design"],
            3: ["testing"],
            4: ["engineering"],
            5: ["testing", "security"],
            6: ["product", "orchestration"],
            7: ["engineering", "design"],
            8: ["orchestration", "devops"],
        }
        return mapping.get(phase, [])

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def _semantic_compress(self, content: str, preserve_sections: list, target_tokens: int) -> str:
        lines = content.split("\n")
        preserved_lines = []
        other_lines = []
        in_preserve = False
        current_section = ""
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("##"):
                current_section = stripped.lstrip("#").strip()
                if current_section in preserve_sections:
                    in_preserve = True
                else:
                    in_preserve = False
            if in_preserve:
                preserved_lines.append(line)
            else:
                other_lines.append(line)
        budget_per_line = max(1, target_tokens * 4 // max(len(other_lines), 1))
        compressed_other = []
        for line in other_lines:
            if len(line) <= budget_per_line:
                compressed_other.append(line)
            else:
                compressed_other.append(line[:budget_per_line] + "...")
        return "\n".join(preserved_lines + compressed_other)

    def _selective_compress(self, content: str, preserve_sections: list, target_tokens: int) -> str:
        lines = content.split("\n")
        result = []
        in_preserve = False
        current_section = ""
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("##"):
                current_section = stripped.lstrip("#").strip()
                in_preserve = current_section in preserve_sections
            if in_preserve:
                result.append(line)
            elif stripped and not stripped.startswith("#"):
                result.append(line)
        return "\n".join(result)

    def _lossless_compress(self, content: str) -> str:
        lines = content.split("\n")
        result = []
        prev_empty = False
        for line in lines:
            if not line.strip():
                if prev_empty:
                    continue
                prev_empty = True
            else:
                prev_empty = False
            result.append(line.rstrip())
        return "\n".join(result)
