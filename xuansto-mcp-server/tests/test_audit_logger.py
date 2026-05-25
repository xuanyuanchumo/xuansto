from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

from xuansto_mcp.core.audit_logger import AuditLogger


@pytest.fixture
def audit_logger(tmp_path):
    return AuditLogger(tmp_path)


class TestAuditLogWrite:
    def test_log_writes_valid_jsonl_line(self, audit_logger, tmp_path):
        audit_logger.log(
            tool_name="test_tool",
            params={"key": "value"},
            result={"error": False, "data": "ok"},
            latency_ms=42.5,
            success=True,
        )
        log_path = tmp_path / "audit_log.jsonl"
        assert log_path.exists()
        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert "timestamp" in entry
        assert isinstance(entry["timestamp"], float)
        assert entry["tool"] == "test_tool"
        assert entry["params_summary"] == {"key": "value"}
        assert entry["success"] is True
        assert entry["latency_ms"] == 42.5
        assert "result_summary" in entry

    def test_log_required_fields(self, audit_logger):
        audit_logger.log(
            tool_name="t",
            params={},
            result={"error": True},
            latency_ms=1.0,
            success=False,
        )
        entries = audit_logger.query()
        assert len(entries) == 1
        entry = entries[0]
        for field in ("timestamp", "tool", "params_summary", "success", "latency_ms", "result_summary"):
            assert field in entry, f"Missing field: {field}"

    def test_latency_ms_rounded(self, audit_logger):
        audit_logger.log(
            tool_name="t",
            params={},
            result={},
            latency_ms=123.4567,
            success=True,
        )
        entries = audit_logger.query()
        assert entries[0]["latency_ms"] == 123.46


class TestAuditQuery:
    def test_query_returns_reverse_chronological(self, audit_logger):
        for i in range(5):
            audit_logger.log(
                tool_name=f"tool_{i}",
                params={},
                result={},
                latency_ms=float(i),
                success=True,
            )
        entries = audit_logger.query()
        tools = [e["tool"] for e in entries]
        assert tools == ["tool_4", "tool_3", "tool_2", "tool_1", "tool_0"]

    def test_query_filter_by_tool_name(self, audit_logger):
        audit_logger.log(tool_name="alpha", params={}, result={}, latency_ms=1.0, success=True)
        audit_logger.log(tool_name="beta", params={}, result={}, latency_ms=2.0, success=True)
        audit_logger.log(tool_name="alpha", params={}, result={}, latency_ms=3.0, success=True)
        entries = audit_logger.query(tool_name="alpha")
        assert len(entries) == 2
        assert all(e["tool"] == "alpha" for e in entries)

    def test_query_respects_limit(self, audit_logger):
        for i in range(10):
            audit_logger.log(tool_name="t", params={}, result={}, latency_ms=float(i), success=True)
        entries = audit_logger.query(limit=3)
        assert len(entries) == 3

    def test_query_empty_when_no_file(self, tmp_path):
        logger = AuditLogger(tmp_path / "subdir")
        log_path = tmp_path / "subdir" / "audit_log.jsonl"
        if log_path.exists():
            log_path.unlink()
        entries = logger.query()
        assert entries == []


class TestSummarizeParams:
    def test_short_string_unchanged(self, audit_logger):
        result = audit_logger._summarize_params({"name": "hello"})
        assert result["name"] == "hello"

    def test_long_string_truncated(self, audit_logger):
        long_val = "x" * 300
        result = audit_logger._summarize_params({"big": long_val})
        assert len(result["big"]) == 203
        assert result["big"].endswith("...")

    def test_string_exactly_200_chars_not_truncated(self, audit_logger):
        val = "x" * 200
        result = audit_logger._summarize_params({"s": val})
        assert result["s"] == val

    def test_string_201_chars_truncated(self, audit_logger):
        val = "x" * 201
        result = audit_logger._summarize_params({"s": val})
        assert result["s"].endswith("...")

    def test_large_collection_summarized(self, audit_logger):
        big_list = list(range(1000))
        result = audit_logger._summarize_params({"items": big_list})
        assert "<list" in result["items"]
        assert "len=" in result["items"]

    def test_small_collection_unchanged(self, audit_logger):
        small = [1, 2, 3]
        result = audit_logger._summarize_params({"items": small})
        assert result["items"] == small

    def test_large_dict_summarized(self, audit_logger):
        big_dict = {f"k{i}": f"v{i}" for i in range(200)}
        result = audit_logger._summarize_params({"data": big_dict})
        assert "<dict" in result["data"]


class TestSummarizeResult:
    def test_dict_result_extracts_error_and_keys(self, audit_logger):
        result = audit_logger._summarize_result({"error": False, "data": "ok", "extra": 1})
        assert result["error"] is False
        assert "error" in result["keys"]
        assert "data" in result["keys"]

    def test_dict_result_limits_keys_to_10(self, audit_logger):
        big = {f"k{i}": i for i in range(20)}
        result = audit_logger._summarize_result(big)
        assert len(result["keys"]) == 10

    def test_non_dict_result(self, audit_logger):
        result = audit_logger._summarize_result("not a dict")
        assert result["type"] == "str"

    def test_dict_without_error_key_defaults_false(self, audit_logger):
        result = audit_logger._summarize_result({"data": "ok"})
        assert result["error"] is False


class TestThreadSafety:
    def test_concurrent_log_does_not_corrupt(self, tmp_path):
        logger = AuditLogger(tmp_path)
        num_threads = 10
        entries_per_thread = 10
        total = num_threads * entries_per_thread

        def write_entries(thread_id):
            for i in range(entries_per_thread):
                logger.log(
                    tool_name=f"t{thread_id}",
                    params={"i": i},
                    result={"error": False},
                    latency_ms=float(thread_id * 100 + i),
                    success=True,
                )

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(write_entries, tid) for tid in range(num_threads)]
            for f in as_completed(futures):
                f.result()

        log_path = tmp_path / "audit_log.jsonl"
        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        valid_entries = []
        for line in lines:
            entry = json.loads(line)
            valid_entries.append(entry)

        assert len(valid_entries) == total
