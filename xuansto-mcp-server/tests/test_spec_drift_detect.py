import sys
import pytest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.spec_drift_detect import register, _inline_spec_drift


@pytest.mark.asyncio
async def test_spec_drift_detect_registered():
    mcp = FastMCP("test")
    register(mcp)
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "spec_drift_detect" in tool_names


def test_inline_spec_drift_empty_dir(tmp_path):
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    result = _inline_spec_drift(str(spec_dir), str(src_dir))
    assert result["total_specs"] == 0
    assert result["total_pending_tasks"] == 0
    assert result["drifts"] == []
    assert result["implementation_rate"] == 0.0


def test_inline_spec_drift_nonexistent_dir(tmp_path):
    result = _inline_spec_drift(str(tmp_path / "no_such_dir"), str(tmp_path / "src"))
    assert result["total_specs"] == 0
    assert result["total_pending_tasks"] == 0
    assert result["drifts"] == []
    assert result["implementation_rate"] == 0.0


def test_inline_spec_drift_pending_without_implementation(tmp_path):
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    (spec_dir / "tasks.md").write_text(
        "- [ ] Task 1: Create user model\n- [ ] Task 2: Build auth service\n",
        encoding="utf-8",
    )

    result = _inline_spec_drift(str(spec_dir), str(src_dir))
    assert result["total_specs"] == 1
    assert result["total_pending_tasks"] == 2
    assert len(result["drifts"]) == 2
    assert result["implementation_rate"] == 0.0

    for drift in result["drifts"]:
        assert drift["has_implementation"] is False
        assert drift["potential_files"] == []


def test_inline_spec_drift_pending_with_implementation(tmp_path):
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    (spec_dir / "tasks.md").write_text(
        "- [ ] Task 1: Create user model\n- [ ] Task 2: Build auth service\n",
        encoding="utf-8",
    )
    (src_dir / "user_model.py").write_text("", encoding="utf-8")
    (src_dir / "auth_service.py").write_text("", encoding="utf-8")

    result = _inline_spec_drift(str(spec_dir), str(src_dir))
    assert result["total_specs"] == 1
    assert result["total_pending_tasks"] == 2
    assert result["implementation_rate"] == 1.0

    for drift in result["drifts"]:
        assert drift["has_implementation"] is True
        assert len(drift["potential_files"]) > 0


def test_inline_spec_drift_mixed_implementation(tmp_path):
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    (spec_dir / "tasks.md").write_text(
        "- [ ] Task 1: Create user model\n- [ ] Task 2: Build payment gateway\n",
        encoding="utf-8",
    )
    (src_dir / "user_model.py").write_text("", encoding="utf-8")

    result = _inline_spec_drift(str(spec_dir), str(src_dir))
    assert result["total_pending_tasks"] == 2
    assert result["implementation_rate"] == 0.5

    user_drift = [d for d in result["drifts"] if "user" in d["task"].lower()][0]
    payment_drift = [d for d in result["drifts"] if "payment" in d["task"].lower()][0]
    assert user_drift["has_implementation"] is True
    assert payment_drift["has_implementation"] is False


def test_inline_spec_drift_completed_tasks_ignored(tmp_path):
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    (spec_dir / "tasks.md").write_text(
        "- [x] Task 1: Create user model\n- [ ] Task 2: Build auth service\n",
        encoding="utf-8",
    )

    result = _inline_spec_drift(str(spec_dir), str(src_dir))
    assert result["total_pending_tasks"] == 1
    assert len(result["drifts"]) == 1
    assert "auth" in result["drifts"][0]["task"].lower()


def test_inline_spec_drift_multiple_spec_files(tmp_path):
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    sub_dir = spec_dir / "module_a"
    sub_dir.mkdir()
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    (spec_dir / "tasks.md").write_text(
        "- [ ] Task 1: Create user model\n",
        encoding="utf-8",
    )
    (sub_dir / "tasks.md").write_text(
        "- [ ] Task 1: Build logger utility\n",
        encoding="utf-8",
    )

    result = _inline_spec_drift(str(spec_dir), str(src_dir))
    assert result["total_specs"] == 2
    assert result["total_pending_tasks"] == 2


def test_inline_spec_drift_spec_file_in_drift(tmp_path):
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    tasks_file = spec_dir / "tasks.md"
    tasks_file.write_text("- [ ] Task 1: Create user model\n", encoding="utf-8")

    result = _inline_spec_drift(str(spec_dir), str(src_dir))
    assert result["drifts"][0]["spec_file"] == str(tasks_file)


@pytest.mark.asyncio
async def test_spec_drift_detect_inline_degradation(tmp_path):
    mcp = FastMCP("test")
    register(mcp)

    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (spec_dir / "tasks.md").write_text(
        "- [ ] Task 1: Create user model\n",
        encoding="utf-8",
    )

    with patch("xuansto_mcp.tools.spec_drift_detect.SCRIPTS_DIR", tmp_path / "no_scripts"):
        from xuansto_mcp.tools.spec_drift_detect import register as reg
        mcp2 = FastMCP("test2")
        reg(mcp2)

        tool_fn = None
        for name, fn in mcp2._tool_manager._tools.items():
            if name == "spec_drift_detect":
                tool_fn = fn
                break

        if tool_fn:
            result = await tool_fn.fn(spec_dir=str(spec_dir), src_dir=str(src_dir))
            assert result.get("degradation_level") == "inline"
            assert result.get("error") is False
