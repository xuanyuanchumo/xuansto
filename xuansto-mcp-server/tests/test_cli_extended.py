import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.cli import main


def test_cli_workflow_start():
    with patch("xuansto_mcp.cli._invoke_tool") as mock_invoke:
        mock_invoke.return_value = {"status": "success", "data": {"workflow_id": "wf-001"}}
        with patch("sys.argv", ["xuansto-cli", "workflow", "start", "sdd-tdd-fast"]):
            main()


def test_cli_workflow_status():
    with patch("xuansto_mcp.cli._invoke_tool") as mock_invoke:
        mock_invoke.return_value = {"status": "success", "data": {"current_phase": 1}}
        with patch("sys.argv", ["xuansto-cli", "workflow", "status", "--workflow-id", "wf-001"]):
            main()


def test_cli_session_save():
    with patch("xuansto_mcp.cli._invoke_tool") as mock_invoke:
        mock_invoke.return_value = {"status": "success", "data": {"session_id": "sess-001"}}
        with patch("sys.argv", ["xuansto-cli", "session", "save", "--label", "test"]):
            main()


def test_cli_agent_list():
    with patch("xuansto_mcp.cli._invoke_tool") as mock_invoke:
        mock_invoke.return_value = {"status": "success", "data": {"agents": []}}
        with patch("sys.argv", ["xuansto-cli", "agent", "list"]):
            main()


def test_cli_agent_create():
    with patch("xuansto_mcp.cli._invoke_tool") as mock_invoke:
        mock_invoke.return_value = {"status": "success", "data": {"agent_id": "agent-001"}}
        with patch("sys.argv", ["xuansto-cli", "agent", "create", "--type", "Backend", "--capabilities", "python", "sql"]):
            main()


def test_cli_agent_match():
    with patch("xuansto_mcp.cli._invoke_tool") as mock_invoke:
        mock_invoke.return_value = {"status": "success", "data": {"matches": []}}
        with patch("sys.argv", ["xuansto-cli", "agent", "match", "--capabilities", "python"]):
            main()
