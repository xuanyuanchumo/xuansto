from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any


class AuditLogger:
    def __init__(self, log_dir: Path):
        self._log_path = log_dir / "audit_log.jsonl"
        self._lock = threading.Lock()
        log_dir.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        tool_name: str,
        params: dict[str, Any],
        result: dict[str, Any],
        latency_ms: float,
        success: bool,
    ) -> None:
        entry = {
            "timestamp": time.time(),
            "tool": tool_name,
            "params_summary": self._summarize_params(params),
            "success": success,
            "latency_ms": round(latency_ms, 2),
            "result_summary": self._summarize_result(result),
        }
        with self._lock, open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _summarize_params(self, params: dict[str, Any]) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        for k, v in params.items():
            if isinstance(v, str) and len(v) > 200:
                summary[k] = v[:200] + "..."
            elif isinstance(v, (list, dict)) and len(str(v)) > 500:
                summary[k] = f"<{type(v).__name__} len={len(v)}>"
            else:
                summary[k] = v
        return summary

    def _summarize_result(self, result: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(result, dict):
            return {"type": type(result).__name__}
        return {"error": result.get("error", False), "keys": list(result.keys())[:10]}

    def query(
        self, tool_name: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        if not self._log_path.exists():
            return entries
        with self._lock, open(self._log_path, encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            try:
                entry = json.loads(line.strip())
                if tool_name and entry.get("tool") != tool_name:
                    continue
                entries.append(entry)
                if len(entries) >= limit:
                    break
            except json.JSONDecodeError:
                continue
        return entries


_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        from .config import WORK_DIR

        _audit_logger = AuditLogger(WORK_DIR)
    return _audit_logger
