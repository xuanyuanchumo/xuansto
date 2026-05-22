import sys
import json
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.session_manage import restore_on_startup, _RESTORED_STATE


def test_restore_on_startup_no_file(tmp_path: Path, monkeypatch):
    from xuansto_mcp.tools import session_manage
    monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session_manage, "_RESTORED_STATE", None)
    result = restore_on_startup()
    assert result is None


def test_restore_on_startup_with_file(tmp_path: Path, monkeypatch):
    from xuansto_mcp.tools import session_manage
    monkeypatch.setattr(session_manage, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(session_manage, "_RESTORED_STATE", None)
    state = {"current_phase": 3, "current_task": "testing"}
    (tmp_path / "current.json").write_text(json.dumps(state), encoding="utf-8")
    result = restore_on_startup()
    assert result is not None
    assert result["current_phase"] == 3
