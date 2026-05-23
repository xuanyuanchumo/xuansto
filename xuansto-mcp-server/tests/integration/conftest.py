from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(autouse=True)
def _isolate_work_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    work_dir = tmp_path / ".xuansto"
    work_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("XUANSTO_WORK_DIR", str(work_dir))
    session_dir = work_dir / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    patterns_dir = work_dir / "patterns"
    patterns_dir.mkdir(parents=True, exist_ok=True)
    yield work_dir


@pytest.fixture()
def mock_config_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    skill_root = tmp_path / "skill_root"
    skill_root.mkdir(parents=True, exist_ok=True)
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    knowledge_dir = data_dir / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("general", "workspace", "experience", "index"):
        (knowledge_dir / sub).mkdir(parents=True, exist_ok=True)
    agents_dir = skill_root / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    references_dir = skill_root / "references"
    references_dir.mkdir(parents=True, exist_ok=True)
    commands_dir = skill_root / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = skill_root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    hooks_dir = skill_root / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hooks_json = hooks_dir / "hooks.json"
    hooks_json.write_text(json.dumps({"hooks": []}), encoding="utf-8")
    monkeypatch.setenv("SKILL_ROOT", str(skill_root))
    return {
        "skill_root": skill_root,
        "data_dir": data_dir,
        "knowledge_dir": knowledge_dir,
        "agents_dir": agents_dir,
        "references_dir": references_dir,
        "commands_dir": commands_dir,
        "scripts_dir": scripts_dir,
    }


@pytest.fixture()
def fresh_mcp(mock_config_paths, tmp_path: Path):
    from mcp.server.fastmcp import FastMCP

    from xuansto_mcp.core.hook_engine import reset_hook_engine

    reset_hook_engine()

    server = FastMCP(
        "xuansto-mcp-server-test",
        instructions="Xuansto Skill MCP服务器 v8.0.0",
    )

    with patch("xuansto_mcp.core.config.KNOWLEDGE_DB_PATH", tmp_path / "knowledge" / "index" / "knowledge.db"), \
         patch("xuansto_mcp.core.config.KNOWLEDGE_CHROMA_PATH", tmp_path / "knowledge" / "index" / "chroma_db"), \
         patch("xuansto_mcp.core.config.HOOKS_PATH", mock_config_paths["skill_root"] / "hooks" / "hooks.json"), \
         patch("xuansto_mcp.core.config.SKILL_ROOT", mock_config_paths["skill_root"]), \
         patch("xuansto_mcp.core.config.DATA_DIR", mock_config_paths["data_dir"]), \
         patch("xuansto_mcp.core.config.WORK_DIR", tmp_path / ".xuansto"), \
         patch("xuansto_mcp.core.config.SESSION_DIR", tmp_path / ".xuansto" / "sessions"), \
         patch("xuansto_mcp.core.config.PATTERNS_DIR", tmp_path / ".xuansto" / "patterns"), \
         patch("xuansto_mcp.core.config.AGENTS_DIR", mock_config_paths["agents_dir"]), \
         patch("xuansto_mcp.core.config.REFERENCES_DIR", mock_config_paths["references_dir"]), \
         patch("xuansto_mcp.core.config.COMMANDS_DIR", mock_config_paths["commands_dir"]), \
         patch("xuansto_mcp.core.config.SCRIPTS_DIR", mock_config_paths["scripts_dir"]):
        yield server

    reset_hook_engine()


@pytest.fixture()
def degradation_manager(tmp_path: Path):
    from xuansto_mcp.core.degradation import DegradationManager

    with patch("xuansto_mcp.core.degradation.DATA_DIR", tmp_path / "data"), \
         patch("xuansto_mcp.core.degradation.SCRIPTS_DIR", tmp_path / "scripts"), \
         patch("xuansto_mcp.core.config.WORK_DIR", tmp_path / ".xuansto"):
        (tmp_path / ".xuansto").mkdir(parents=True, exist_ok=True)
        manager = DegradationManager(health_interval=9999)
        yield manager


@pytest.fixture()
def hook_engine():
    from xuansto_mcp.core.hook_engine import HookEngine, reset_hook_engine

    reset_hook_engine()
    engine = HookEngine()
    yield engine
    reset_hook_engine()
