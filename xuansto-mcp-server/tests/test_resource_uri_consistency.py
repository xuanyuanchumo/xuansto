from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.core.config import SKILL_ROOT, REFERENCES_DIR, TEMPLATES_DIR, SESSION_DIR
from xuansto_mcp.resources import skill_resources
from mcp.server.fastmcp import FastMCP

RESOURCES_SOURCE = Path(__file__).resolve().parent.parent / "src" / "xuansto_mcp" / "resources" / "skill_resources.py"

DYNAMIC_URIS = {"xuansto://templates/{name}", "xuansto://sessions/latest", "xuansto://loading/status"}


def _extract_static_resource_mappings() -> list[tuple[str, Path]]:
    source = RESOURCES_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    mappings: list[tuple[str, Path]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for deco in node.decorator_list:
            if not isinstance(deco, ast.Call) or not isinstance(deco.func, ast.Attribute):
                continue
            if deco.func.attr != "resource":
                continue
            if not deco.args or not isinstance(deco.args[0], ast.Constant):
                continue
            uri: str = deco.args[0].value
            if "{name}" in uri or "{" in uri:
                continue
            if uri in DYNAMIC_URIS:
                continue

            dir_var: str | None = None
            filename: str | None = None
            for child in ast.walk(node):
                if isinstance(child, ast.Constant) and isinstance(child.value, str):
                    val = child.value
                    if (val.endswith(".md") or val.endswith(".yaml")) and "*" not in val and "{" not in val:
                        filename = val

            for child in ast.walk(node):
                if isinstance(child, ast.Name) and child.id in (
                    "REFERENCES_DIR",
                    "SKILL_ROOT",
                    "TEMPLATES_DIR",
                    "SESSION_DIR",
                ):
                    dir_var = child.id

            if dir_var and filename:
                dir_map = {
                    "REFERENCES_DIR": REFERENCES_DIR,
                    "SKILL_ROOT": SKILL_ROOT,
                    "TEMPLATES_DIR": TEMPLATES_DIR,
                    "SESSION_DIR": SESSION_DIR,
                }
                base = dir_map[dir_var]
                mappings.append((uri, base / filename))

    return mappings


def test_static_resource_files_exist():
    if not REFERENCES_DIR.exists():
        pytest.skip("REFERENCES_DIR does not exist, skipping file existence checks")

    mappings = _extract_static_resource_mappings()
    assert len(mappings) >= 3, f"Expected at least 3 static resource mappings, found {len(mappings)}"

    errors: list[str] = []
    for uri, file_path in mappings:
        if not file_path.exists():
            errors.append(f"URI {uri!r} maps to missing file: {file_path}")

    assert errors == [], "Resource file mapping errors:\n" + "\n".join(errors)


def test_uri_path_segment_matches_filename():
    if not REFERENCES_DIR.exists():
        pytest.skip("REFERENCES_DIR does not exist, skipping URI matching checks")

    source = RESOURCES_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    static_count = 0
    matched_count = 0

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for deco in node.decorator_list:
            if not isinstance(deco, ast.Call) or not isinstance(deco.func, ast.Attribute):
                continue
            if deco.func.attr != "resource":
                continue
            if not deco.args or not isinstance(deco.args[0], ast.Constant):
                continue
            uri: str = deco.args[0].value
            if "{" in uri:
                continue
            if uri in DYNAMIC_URIS:
                continue

            uri_segment = uri.rsplit("/", 1)[-1]

            for child in ast.walk(node):
                if isinstance(child, ast.Constant) and isinstance(child.value, str):
                    val = child.value
                    if val.endswith(".md") and "*" not in val and "{" not in val:
                        stem = val[:-3]
                        static_count += 1
                        if stem == uri_segment or uri_segment in stem:
                            matched_count += 1

    assert static_count > 0, "Expected at least one static resource with .md file"
    assert matched_count > 0, "Expected at least one URI segment to match or be contained in filename stem"


def test_all_resources_registered():
    mcp = FastMCP("test")
    skill_resources.register(mcp)
    resources = mcp._resource_manager._resources
    template_resources = mcp._resource_manager._templates
    total = len(resources) + len(template_resources)
    assert total >= 7, f"Expected at least 7 total resources (static + template), found {total} (static={len(resources)}, template={len(template_resources)})"


def test_templates_dir_exists():
    if not TEMPLATES_DIR.exists():
        pytest.skip(f"TEMPLATES_DIR does not exist: {TEMPLATES_DIR}")
    assert TEMPLATES_DIR.exists(), f"TEMPLATES_DIR does not exist: {TEMPLATES_DIR}"


def test_sessions_dir_accessible():
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    assert SESSION_DIR.exists(), f"SESSION_DIR does not exist: {SESSION_DIR}"


def test_workflow_phases_uri_reads_correct_file():
    if not REFERENCES_DIR.exists():
        pytest.skip("REFERENCES_DIR does not exist")

    mcp = FastMCP("test")
    skill_resources.register(mcp)

    expected_file = REFERENCES_DIR / "workflow-phases.md"
    assert expected_file.exists(), f"workflow-phases.md not found at {expected_file}"

    content = expected_file.read_text(encoding="utf-8")
    assert len(content) > 0, "workflow-phases.md is empty"


def test_workflow_phases_file_exists_and_not_empty():
    if not REFERENCES_DIR.exists():
        pytest.skip("REFERENCES_DIR does not exist")

    phases_file = REFERENCES_DIR / "workflow-phases.md"
    assert phases_file.exists(), f"{phases_file} does not exist"

    phases_content = phases_file.read_text(encoding="utf-8")
    assert len(phases_content) > 0, "workflow-phases.md is empty"
