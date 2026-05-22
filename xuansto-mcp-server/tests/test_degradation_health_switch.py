from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.server_health import (
    _DEGRADATION_COUNTS,
    _CHROMADB_DEGRADATION_KEY,
    _check_chromadb_health,
    register,
)
import xuansto_mcp.tools.server_health as _sh_mod
from xuansto_mcp.tools.knowledge_search import _chromadb_search


@pytest.fixture(autouse=True)
def _reset_degradation():
    _DEGRADATION_COUNTS.pop(_CHROMADB_DEGRADATION_KEY, None)
    _sh_mod._chromadb_client = None
    yield
    _DEGRADATION_COUNTS.pop(_CHROMADB_DEGRADATION_KEY, None)
    _sh_mod._chromadb_client = None


def test_chromadb_unavailable_sets_degradation_mark():
    with patch.dict("sys.modules", {"chromadb": None}):
        result = _check_chromadb_health()
    assert result["available"] is False
    assert _DEGRADATION_COUNTS.get(_CHROMADB_DEGRADATION_KEY, 0) > 0


def test_chromadb_available_clears_degradation_mark():
    _DEGRADATION_COUNTS[_CHROMADB_DEGRADATION_KEY] = 5

    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = MagicMock()
    mock_chromadb = MagicMock()
    mock_chromadb.PersistentClient.return_value = mock_client

    with patch.dict("sys.modules", {"chromadb": mock_chromadb}):
        result = _check_chromadb_health()

    assert result["available"] is True
    assert _DEGRADATION_COUNTS.get(_CHROMADB_DEGRADATION_KEY, 0) == 0


def test_chromadb_connection_failure_increments_degradation():
    mock_chromadb = MagicMock()
    mock_chromadb.PersistentClient.side_effect = RuntimeError("connection refused")

    with patch.dict("sys.modules", {"chromadb": mock_chromadb}):
        result = _check_chromadb_health()

    assert result["available"] is False
    assert "reason" in result
    assert _DEGRADATION_COUNTS.get(_CHROMADB_DEGRADATION_KEY, 0) > 0


def test_health_check_response_includes_services_chromadb():
    from mcp.server.fastmcp import FastMCP

    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = MagicMock()
    mock_chromadb = MagicMock()
    mock_chromadb.PersistentClient.return_value = mock_client

    with patch.dict("sys.modules", {"chromadb": mock_chromadb}):
        mcp = FastMCP("test")
        register(mcp)

        tool_fn = None
        for name, fn in mcp._tool_manager._tools.items():
            if name == "server_health":
                tool_fn = fn
                break

        assert tool_fn is not None
        result = tool_fn.fn()
        if hasattr(result, "__await__"):
            import asyncio
            result = asyncio.run(result)

    data = result["data"]
    assert "services" in data
    assert "chromadb" in data["services"]
    chromadb_status = data["services"]["chromadb"]
    assert "available" in chromadb_status
    assert "latency_ms" in chromadb_status


def test_knowledge_search_respects_degradation_mark():
    _DEGRADATION_COUNTS[_CHROMADB_DEGRADATION_KEY] = 3

    result = _chromadb_search("test query", 5, None, 0.0)
    assert result is None


def test_knowledge_search_uses_chromadb_when_not_degraded():
    _DEGRADATION_COUNTS.pop(_CHROMADB_DEGRADATION_KEY, None)

    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "ids": [["doc1"]],
        "distances": [[0.1]],
        "documents": [["content1"]],
    }
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_chromadb = MagicMock()
    mock_chromadb.PersistentClient.return_value = mock_client

    with patch.dict("sys.modules", {"chromadb": mock_chromadb}):
        result = _chromadb_search("test query", 5, None, 0.0)

    assert result is not None
    assert result["strategy"] == "chromadb_semantic"


def test_degradation_count_accumulates_on_repeated_failures():
    with patch.dict("sys.modules", {"chromadb": None}):
        _check_chromadb_health()
        _check_chromadb_health()
        _check_chromadb_health()

    assert _DEGRADATION_COUNTS.get(_CHROMADB_DEGRADATION_KEY, 0) == 3


def test_recovery_resets_count_to_zero():
    _DEGRADATION_COUNTS[_CHROMADB_DEGRADATION_KEY] = 10

    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = MagicMock()
    mock_chromadb = MagicMock()
    mock_chromadb.PersistentClient.return_value = mock_client

    with patch.dict("sys.modules", {"chromadb": mock_chromadb}):
        _check_chromadb_health()

    assert _DEGRADATION_COUNTS.get(_CHROMADB_DEGRADATION_KEY, 0) == 0
