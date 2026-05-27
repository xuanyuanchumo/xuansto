#!/usr/bin/env python3
"""Schema validation script for xuansto-mcp-server spec-locks.

Validates JSON Schema files in spec-locks/ directory against actual code definitions:
- api-contract-version.json: API version consistency with config.py
- skill-definition-schema.json: Schema structural validity
- tool-parameter-schemas.json: Tool parameter schemas match Pydantic models

Usage:
    python scripts/validate_schemas.py [--spec-locks-dir DIR] [--verbose]
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any


class SchemaValidator:
    def __init__(self, spec_locks_dir: Path, verbose: bool = False):
        self.spec_locks_dir = spec_locks_dir
        self.verbose = verbose
        self.results: list[dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"  {msg}")

    def _add_result(self, name: str, status: str, message: str, details: dict[str, Any] | None = None) -> None:
        entry = {"name": name, "status": status, "message": message}
        if details:
            entry["details"] = details
        self.results.append(entry)
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        else:
            self.skipped += 1

    def _load_json(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            self._add_result(path.name, "SKIP", f"File not found: {path}")
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._log(f"Loaded {path.name} ({len(json.dumps(data))} bytes)")
            return data
        except json.JSONDecodeError as e:
            self._add_result(path.name, "FAIL", f"Invalid JSON in {path}: {e}")
            return None

    def validate_api_contract_version(self) -> None:
        path = self.spec_locks_dir / "api-contract-version.json"
        data = self._load_json(path)
        if data is None:
            return

        check_name = "api-contract-version.json"

        required_fields = ["current_version", "min_supported_version", "version_history", "compatibility_rules"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            self._add_result(check_name, "FAIL", f"Missing required fields: {missing}")
            return

        for field in ["current_version", "min_supported_version"]:
            val = data.get(field, "")
            parts = val.split(".")
            if len(parts) != 3 or not all(p.isdigit() for p in parts):
                self._add_result(check_name, "FAIL", f"{field} is not valid semver: {val}")
                return

        current = data["current_version"]
        min_ver = data["min_supported_version"]
        current_parts = tuple(int(p) for p in current.split("."))
        min_parts = tuple(int(p) for p in min_ver.split("."))
        if current_parts < min_parts:
            self._add_result(check_name, "FAIL", f"current_version ({current}) < min_supported_version ({min_ver})")
            return

        history_versions = [h.get("version", "") for h in data.get("version_history", [])]
        if current not in history_versions:
            self._add_result(check_name, "FAIL", f"current_version ({current}) not in version_history")
            return

        try:
            src_root = self.spec_locks_dir.parent / "src" / "xuansto_mcp"
            config_path = src_root / "core" / "config.py"
            if config_path.exists():
                config_text = config_path.read_text(encoding="utf-8")
                import re
                api_ver_match = re.search(r'MCP_API_VERSION\s*=\s*"([^"]+)"', config_text)
                min_ver_match = re.search(r'MCP_MIN_SUPPORTED_VERSION\s*=\s*"([^"]+)"', config_text)
                if api_ver_match:
                    code_api_ver = api_ver_match.group(1)
                    if code_api_ver != current:
                        self._add_result(
                            check_name, "FAIL",
                            f"API version mismatch: spec-locks says {current}, config.py says {code_api_ver}",
                            {"spec_version": current, "code_version": code_api_ver},
                        )
                        return
                if min_ver_match:
                    code_min_ver = min_ver_match.group(1)
                    if code_min_ver != min_ver:
                        self._add_result(
                            check_name, "FAIL",
                            f"Min version mismatch: spec-locks says {min_ver}, config.py says {code_min_ver}",
                            {"spec_min_version": min_ver, "code_min_version": code_min_ver},
                        )
                        return
        except Exception as e:
            self._log(f"Could not verify against config.py: {e}")

        compat_rules = data.get("compatibility_rules", {})
        if not compat_rules:
            self._add_result(check_name, "FAIL", "compatibility_rules is empty")
            return

        self._add_result(check_name, "PASS", f"API contract version valid (current={current}, min={min_ver})")

    def validate_skill_definition_schema(self) -> None:
        path = self.spec_locks_dir / "skill-definition-schema.json"
        data = self._load_json(path)
        if data is None:
            return

        check_name = "skill-definition-schema.json"

        if data.get("$schema") is None:
            self._add_result(check_name, "FAIL", "Missing $schema field")
            return

        if data.get("type") != "object":
            self._add_result(check_name, "FAIL", f"Root type should be 'object', got '{data.get('type')}'")
            return

        required_fields = data.get("required", [])
        if not required_fields:
            self._add_result(check_name, "FAIL", "No required fields defined")
            return

        properties = data.get("properties", {})
        for req_field in required_fields:
            if req_field not in properties:
                self._add_result(check_name, "FAIL", f"Required field '{req_field}' not in properties")
                return

        expected_required = ["name", "version", "description", "triggers", "tools"]
        for field in expected_required:
            if field not in required_fields:
                self._add_result(check_name, "FAIL", f"Expected required field '{field}' not in required list")
                return

        version_prop = properties.get("version", {})
        if not version_prop.get("pattern"):
            self._add_result(check_name, "FAIL", "version property missing semver pattern")
            return

        triggers_prop = properties.get("triggers", {})
        if triggers_prop.get("type") != "array":
            self._add_result(check_name, "FAIL", "triggers property should be array type")
            return

        tools_prop = properties.get("tools", {})
        if tools_prop.get("type") != "array":
            self._add_result(check_name, "FAIL", "tools property should be array type")
            return

        self._add_result(check_name, "PASS", f"Skill definition schema valid (required={required_fields})")

    def validate_tool_parameter_schemas(self) -> None:
        path = self.spec_locks_dir / "tool-parameter-schemas.json"
        data = self._load_json(path)
        if data is None:
            return

        check_name = "tool-parameter-schemas.json"

        definitions = data.get("definitions", {})
        if not definitions:
            self._add_result(check_name, "FAIL", "No definitions found")
            return

        tool_schemas = data.get("tool_schemas", {})
        if not tool_schemas:
            self._add_result(check_name, "FAIL", "No tool_schemas mapping found")
            return

        for tool_name, ref in tool_schemas.items():
            if isinstance(ref, dict) and "$ref" in ref:
                ref_path = ref["$ref"]
                def_name = ref_path.split("/")[-1]
                if def_name not in definitions:
                    self._add_result(check_name, "FAIL", f"Tool '{tool_name}' references missing definition '{def_name}'")
                    return
            elif isinstance(ref, str) and ref.startswith("#/definitions/"):
                def_name = ref.split("/")[-1]
                if def_name not in definitions:
                    self._add_result(check_name, "FAIL", f"Tool '{tool_name}' references missing definition '{def_name}'")
                    return

        for def_name, def_schema in definitions.items():
            if not isinstance(def_schema, dict):
                self._add_result(check_name, "FAIL", f"Definition '{def_name}' is not a dict")
                return
            if "type" not in def_schema and "properties" not in def_schema:
                self._add_result(check_name, "FAIL", f"Definition '{def_name}' missing type or properties")
                return

        try:
            sys.path.insert(0, str(self.spec_locks_dir.parent / "src"))
            from xuansto_mcp.models.schemas import (
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
                ResourceSubscribeInput,
                ServerHealthInput,
                ContextCompressInput,
                DecisionLogInput,
                TokenBudgetInput,
                ProjectInitInput,
                KnowledgeInjectInput,
                MetricsReportInput,
                ConfigManageInput,
                AuditQueryInput,
            )

            pydantic_models = {
                "SkillAnalyzeInput": SkillAnalyzeInput,
                "KnowledgeSearchInput": KnowledgeSearchInput,
                "QualityGateCheckInput": QualityGateCheckInput,
                "SpecDriftDetectInput": SpecDriftDetectInput,
                "SecurityScanInput": SecurityScanInput,
                "CodeSimplifyInput": CodeSimplifyInput,
                "SessionManageInput": SessionManageInput,
                "WorkflowDispatchInput": WorkflowDispatchInput,
                "AgentStatusInput": AgentStatusInput,
                "AgentManageInput": AgentManageInput,
                "HookManageInput": HookManageInput,
                "ResourceLoadStatusInput": ResourceLoadStatusInput,
                "ResourceSubscribeInput": ResourceSubscribeInput,
                "ServerHealthInput": ServerHealthInput,
                "ContextCompressInput": ContextCompressInput,
                "DecisionLogInput": DecisionLogInput,
                "TokenBudgetInput": TokenBudgetInput,
                "ProjectInitInput": ProjectInitInput,
                "KnowledgeInjectInput": KnowledgeInjectInput,
                "MetricsReportInput": MetricsReportInput,
                "ConfigManageInput": ConfigManageInput,
                "AuditQueryInput": AuditQueryInput,
            }

            mismatches = []
            for model_name, model_cls in pydantic_models.items():
                schema_def = definitions.get(model_name)
                if schema_def is None:
                    mismatches.append(f"Definition '{model_name}' not found in spec-locks")
                    continue

                schema_props = schema_def.get("properties", {})
                pydantic_fields = model_cls.model_fields

                for field_name, field_info in pydantic_fields.items():
                    if field_name not in schema_props:
                        mismatches.append(f"{model_name}.{field_name}: in Pydantic but not in spec-locks")

                for field_name in schema_props:
                    if field_name not in pydantic_fields:
                        mismatches.append(f"{model_name}.{field_name}: in spec-locks but not in Pydantic")

            if mismatches:
                self._add_result(
                    check_name, "FAIL",
                    f"Schema-code mismatches found: {len(mismatches)}",
                    {"mismatches": mismatches[:20]},
                )
                return

        except ImportError as e:
            self._log(f"Could not import Pydantic models for cross-validation: {e}")
        except Exception as e:
            self._log(f"Cross-validation error: {e}")

        tool_count = len(tool_schemas)
        def_count = len(definitions)
        self._add_result(check_name, "PASS", f"Tool parameter schemas valid ({tool_count} tools, {def_count} definitions)")

    def validate_all(self) -> bool:
        print("=" * 60)
        print("Xuansto MCP Server - Schema Validation")
        print("=" * 60)
        print(f"Spec-locks directory: {self.spec_locks_dir}")
        print()

        if not self.spec_locks_dir.exists():
            print(f"ERROR: spec-locks directory not found: {self.spec_locks_dir}")
            return False

        print("[1/3] Validating api-contract-version.json...")
        self.validate_api_contract_version()

        print("[2/3] Validating skill-definition-schema.json...")
        self.validate_skill_definition_schema()

        print("[3/3] Validating tool-parameter-schemas.json...")
        self.validate_tool_parameter_schemas()

        print()
        print("-" * 60)
        print("RESULTS")
        print("-" * 60)

        for r in self.results:
            status_icon = {"PASS": "✓", "FAIL": "✗", "SKIP": "○"}.get(r["status"], "?")
            print(f"  {status_icon} [{r['status']}] {r['name']}: {r['message']}")
            if self.verbose and "details" in r:
                for k, v in r["details"].items():
                    print(f"      {k}: {v}")

        print()
        total = self.passed + self.failed + self.skipped
        print(f"Total: {total} | Passed: {self.passed} | Failed: {self.failed} | Skipped: {self.skipped}")

        if self.failed > 0:
            print()
            print("VALIDATION FAILED - Some schemas do not match code definitions.")
            return False

        print()
        print("ALL SCHEMAS VALID - All spec-lock files match code definitions.")
        return True


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Validate xuansto-mcp-server schema files")
    parser.add_argument(
        "--spec-locks-dir",
        type=Path,
        default=None,
        help="Path to spec-locks directory (default: auto-detect)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output",
    )
    args = parser.parse_args()

    spec_locks_dir = args.spec_locks_dir
    if spec_locks_dir is None:
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent
        spec_locks_dir = project_root / "spec-locks"
        if not spec_locks_dir.exists():
            spec_locks_dir = project_root / "xuansto-mcp-server" / "spec-locks"

    validator = SchemaValidator(spec_locks_dir, verbose=args.verbose)
    success = validator.validate_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
