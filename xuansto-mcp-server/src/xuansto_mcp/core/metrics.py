from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from typing import Any

from . import atomic_write
from .config import CURRENT_SCHEMA_VERSION, WORK_DIR, _ensure_schema_version
from .logging_config import get_logger

logger = get_logger("metrics")

_MAX_LATENCY_SAMPLES = 1000
_MAX_DEGRADATION_EVENTS = 200
_MAX_QUALITY_GATE_RECORDS = 500
_MAX_PHASE_TRANSITIONS = 100


class MetricsCollector:
    _instance: MetricsCollector | None = None
    _init_lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> MetricsCollector:
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, persist_interval: float = 60.0) -> None:
        if self._initialized:
            return
        self._lock = threading.Lock()
        self._persist_interval = persist_interval
        self._tool_metrics: dict[str, dict[str, Any]] = {}
        self._degradation_events: list[dict[str, Any]] = []
        self._quality_gate_results: list[dict[str, Any]] = []
        self._phase_transitions: list[dict[str, Any]] = []
        self._last_persist_time: float = 0.0
        self._persist_count: int = 0
        self._persist_call_threshold: int = 100
        self._auto_persist_thread: threading.Thread | None = None
        self._auto_persist_stop = threading.Event()
        self._initialized = True

    def record_tool_call(self, tool_name: str, latency_ms: float, success: bool) -> None:
        should_persist = False
        with self._lock:
            if tool_name not in self._tool_metrics:
                self._tool_metrics[tool_name] = {
                    "call_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "total_latency_ms": 0.0,
                    "min_latency_ms": float("inf"),
                    "max_latency_ms": 0.0,
                    "latency_samples": [],
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                }
            m = self._tool_metrics[tool_name]
            m["call_count"] += 1
            if success:
                m["success_count"] += 1
            else:
                m["failure_count"] += 1
            m["total_latency_ms"] += latency_ms
            m["min_latency_ms"] = min(m["min_latency_ms"], latency_ms)
            m["max_latency_ms"] = max(m["max_latency_ms"], latency_ms)
            m["latency_samples"].append(latency_ms)
            if len(m["latency_samples"]) > _MAX_LATENCY_SAMPLES:
                m["latency_samples"] = m["latency_samples"][-_MAX_LATENCY_SAMPLES:]
            self._persist_count += 1
            should_persist = self._should_auto_persist()
        if should_persist:
            self.persist()

    def record_token_usage(self, tool_name: str, input_tokens: int, output_tokens: int) -> None:
        with self._lock:
            if tool_name not in self._tool_metrics:
                self._tool_metrics[tool_name] = {
                    "call_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "total_latency_ms": 0.0,
                    "min_latency_ms": float("inf"),
                    "max_latency_ms": 0.0,
                    "latency_samples": [],
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                }
            m = self._tool_metrics[tool_name]
            m["total_input_tokens"] += input_tokens
            m["total_output_tokens"] += output_tokens

    def record_degradation_event(self, component: str, from_level: str, to_level: str, reason: str) -> None:
        should_persist = False
        with self._lock:
            self._degradation_events.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component": component,
                "from_level": from_level,
                "to_level": to_level,
                "reason": reason,
            })
            if len(self._degradation_events) > _MAX_DEGRADATION_EVENTS:
                self._degradation_events = self._degradation_events[-_MAX_DEGRADATION_EVENTS:]
            self._persist_count += 1
            should_persist = self._should_auto_persist()
        if should_persist:
            self.persist()

    def record_quality_gate(self, gate_id: str, passed: bool, phase: int) -> None:
        should_persist = False
        with self._lock:
            self._quality_gate_results.append({
                "gate_id": gate_id,
                "passed": passed,
                "phase": phase,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            if len(self._quality_gate_results) > _MAX_QUALITY_GATE_RECORDS:
                self._quality_gate_results = self._quality_gate_results[-_MAX_QUALITY_GATE_RECORDS:]
            self._persist_count += 1
            should_persist = self._should_auto_persist()
        if should_persist:
            self.persist()

    def record_phase_transition(self, from_phase: str, to_phase: str, resources_affected: list[str]) -> None:
        should_persist = False
        with self._lock:
            self._phase_transitions.append({
                "from_phase": from_phase,
                "to_phase": to_phase,
                "resources_affected": list(resources_affected),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            if len(self._phase_transitions) > _MAX_PHASE_TRANSITIONS:
                self._phase_transitions = self._phase_transitions[-_MAX_PHASE_TRANSITIONS:]
            self._persist_count += 1
            should_persist = self._should_auto_persist()
        if should_persist:
            self.persist()

    def get_tool_summary(self) -> dict[str, Any]:
        with self._lock:
            result: dict[str, Any] = {}
            for tool_name, m in self._tool_metrics.items():
                call_count = m["call_count"]
                avg_latency = m["total_latency_ms"] / call_count if call_count > 0 else 0.0
                samples = m["latency_samples"]
                entry: dict[str, Any] = {
                    "call_count": call_count,
                    "success_count": m["success_count"],
                    "failure_count": m["failure_count"],
                    "total_latency_ms": round(m["total_latency_ms"], 2),
                    "avg_latency_ms": round(avg_latency, 2),
                    "min_latency_ms": round(m["min_latency_ms"], 2) if m["min_latency_ms"] != float("inf") else 0.0,
                    "max_latency_ms": round(m["max_latency_ms"], 2),
                    "total_input_tokens": m["total_input_tokens"],
                    "total_output_tokens": m["total_output_tokens"],
                }
                if samples:
                    entry["latency_p50_ms"] = round(self._percentile(samples, 50), 2)
                    entry["latency_p95_ms"] = round(self._percentile(samples, 95), 2)
                    entry["latency_p99_ms"] = round(self._percentile(samples, 99), 2)
                result[tool_name] = entry
            return result

    def get_system_summary(self) -> dict[str, Any]:
        with self._lock:
            total_calls = sum(m["call_count"] for m in self._tool_metrics.values())
            total_success = sum(m["success_count"] for m in self._tool_metrics.values())
            total_failure = sum(m["failure_count"] for m in self._tool_metrics.values())
            total_input_tokens = sum(m["total_input_tokens"] for m in self._tool_metrics.values())
            total_output_tokens = sum(m["total_output_tokens"] for m in self._tool_metrics.values())
            total_latency = sum(m["total_latency_ms"] for m in self._tool_metrics.values())
            degradation_count = len(self._degradation_events)
            gate_pass = sum(1 for g in self._quality_gate_results if g["passed"])
            gate_fail = len(self._quality_gate_results) - gate_pass
            return {
                "total_tool_calls": total_calls,
                "total_success": total_success,
                "total_failure": total_failure,
                "success_rate": round(total_success / total_calls, 4) if total_calls > 0 else 0.0,
                "total_latency_ms": round(total_latency, 2),
                "avg_latency_ms": round(total_latency / total_calls, 2) if total_calls > 0 else 0.0,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens,
                "tools_tracked": len(self._tool_metrics),
                "degradation_events_count": degradation_count,
                "quality_gates_passed": gate_pass,
                "quality_gates_failed": gate_fail,
                "quality_gate_pass_rate": round(gate_pass / len(self._quality_gate_results), 4) if self._quality_gate_results else 0.0,
                "phase_transitions_count": len(self._phase_transitions),
            }

    def get_degradation_history(self, limit: int = 20) -> list[dict]:
        with self._lock:
            return list(self._degradation_events[-limit:])

    def get_quality_gate_stats(self) -> dict[str, Any]:
        with self._lock:
            by_phase: dict[int, dict[str, Any]] = {}
            for g in self._quality_gate_results:
                phase = g["phase"]
                if phase not in by_phase:
                    by_phase[phase] = {"passed": 0, "failed": 0, "total": 0, "gate_ids": set()}
                by_phase[phase]["passed" if g["passed"] else "failed"] += 1
                by_phase[phase]["total"] += 1
                by_phase[phase]["gate_ids"].add(g["gate_id"])
            result: dict[str, Any] = {}
            for phase, stats in sorted(by_phase.items()):
                total = stats["total"]
                result[str(phase)] = {
                    "passed": stats["passed"],
                    "failed": stats["failed"],
                    "total": total,
                    "pass_rate": round(stats["passed"] / total, 4) if total > 0 else 0.0,
                    "unique_gates": len(stats["gate_ids"]),
                }
            return result

    def persist(self) -> None:
        with self._lock:
            tool_summary = {}
            for tool_name, m in self._tool_metrics.items():
                tool_summary[tool_name] = {
                    "call_count": m["call_count"],
                    "success_count": m["success_count"],
                    "failure_count": m["failure_count"],
                    "total_latency_ms": m["total_latency_ms"],
                    "min_latency_ms": m["min_latency_ms"] if m["min_latency_ms"] != float("inf") else 0.0,
                    "max_latency_ms": m["max_latency_ms"],
                    "latency_samples": m["latency_samples"][-100:],
                    "total_input_tokens": m["total_input_tokens"],
                    "total_output_tokens": m["total_output_tokens"],
                }
            data = {
                "schema_version": CURRENT_SCHEMA_VERSION,
                "persisted_at": datetime.now(timezone.utc).isoformat(),
                "tool_metrics": tool_summary,
                "degradation_events": list(self._degradation_events[-50:]),
                "quality_gate_results": list(self._quality_gate_results[-100:]),
                "phase_transitions": list(self._phase_transitions[-50:]),
            }
        persist_dir = WORK_DIR
        persist_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        metrics_path = persist_dir / f"metrics_{ts}.json"
        try:
            atomic_write(metrics_path, json.dumps(data, ensure_ascii=False, indent=2))
            logger.info("Persisted metrics to %s", metrics_path)
        except Exception as exc:
            logger.warning("Failed to persist metrics: %s", exc)
        self._persist_metrics_to_db()
        with self._lock:
            self._last_persist_time = time.time()
            self._persist_count = 0

    def load(self) -> None:
        self._load_metrics_from_db()
        persist_dir = WORK_DIR
        if not persist_dir.exists():
            logger.debug("No metrics directory found at %s", persist_dir)
            return
        candidates = sorted(persist_dir.glob("metrics_*.json"), reverse=True)
        if not candidates:
            logger.debug("No metrics files found in %s", persist_dir)
            return
        metrics_path = candidates[0]
        try:
            raw = json.loads(metrics_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load metrics from %s: %s", metrics_path, exc)
            return
        if isinstance(raw, dict):
            raw = _ensure_schema_version(raw)
        with self._lock:
            for tool_name, d in raw.get("tool_metrics", {}).items():
                if tool_name not in self._tool_metrics:
                    self._tool_metrics[tool_name] = {
                        "call_count": d.get("call_count", 0),
                        "success_count": d.get("success_count", 0),
                        "failure_count": d.get("failure_count", 0),
                        "total_latency_ms": d.get("total_latency_ms", 0.0),
                        "min_latency_ms": d.get("min_latency_ms", 0.0),
                        "max_latency_ms": d.get("max_latency_ms", 0.0),
                        "latency_samples": d.get("latency_samples", []),
                        "total_input_tokens": d.get("total_input_tokens", 0),
                        "total_output_tokens": d.get("total_output_tokens", 0),
                    }
            for evt in raw.get("degradation_events", []):
                self._degradation_events.append(evt)
            if len(self._degradation_events) > _MAX_DEGRADATION_EVENTS:
                self._degradation_events = self._degradation_events[-_MAX_DEGRADATION_EVENTS:]
            for g in raw.get("quality_gate_results", []):
                self._quality_gate_results.append(g)
            if len(self._quality_gate_results) > _MAX_QUALITY_GATE_RECORDS:
                self._quality_gate_results = self._quality_gate_results[-_MAX_QUALITY_GATE_RECORDS:]
            for t in raw.get("phase_transitions", []):
                self._phase_transitions.append(t)
            if len(self._phase_transitions) > _MAX_PHASE_TRANSITIONS:
                self._phase_transitions = self._phase_transitions[-_MAX_PHASE_TRANSITIONS:]
        logger.info("Loaded metrics from %s", metrics_path)

    def _persist_metrics_to_db(self) -> None:
        with self._lock:
            snapshot = {}
            for tool_name, m in self._tool_metrics.items():
                snapshot[tool_name] = {
                    "call_count": m["call_count"],
                    "success_count": m["success_count"],
                    "failure_count": m["failure_count"],
                    "total_latency_ms": m["total_latency_ms"],
                    "min_latency_ms": m["min_latency_ms"] if m["min_latency_ms"] != float("inf") else 0.0,
                    "max_latency_ms": m["max_latency_ms"],
                    "latency_samples": m["latency_samples"][-100:],
                    "total_input_tokens": m["total_input_tokens"],
                    "total_output_tokens": m["total_output_tokens"],
                }
        try:
            from .database import get_db
            conn = get_db()
            try:
                now = datetime.now(timezone.utc).isoformat()
                for tool_name, m in snapshot.items():
                    data_json = json.dumps(m, ensure_ascii=False)
                    conn.execute(
                        "INSERT INTO tool_metrics "
                        "(tool_name, call_count, error_count, total_duration_ms, last_called, data_json) "
                        "VALUES (?, ?, ?, ?, ?, ?) "
                        "ON CONFLICT(tool_name) DO UPDATE SET "
                        "call_count=excluded.call_count, error_count=excluded.error_count, "
                        "total_duration_ms=excluded.total_duration_ms, "
                        "last_called=excluded.last_called, data_json=excluded.data_json",
                        (tool_name, m["call_count"], m["failure_count"], m["total_latency_ms"], now, data_json),
                    )
                conn.commit()
                logger.debug("Persisted tool metrics to SQLite (%d tools)", len(snapshot))
            finally:
                conn.close()
        except Exception as exc:
            logger.warning("Failed to persist tool metrics to SQLite: %s", exc)

    def _load_metrics_from_db(self) -> None:
        try:
            from .database import get_db
            conn = get_db()
            try:
                cursor = conn.execute("SELECT tool_name, data_json FROM tool_metrics")
                rows = cursor.fetchall()
            finally:
                conn.close()
        except Exception as exc:
            logger.warning("Failed to load tool metrics from SQLite: %s", exc)
            return
        if not rows:
            return
        with self._lock:
            for row in rows:
                tool_name = row[0]
                try:
                    d = json.loads(row[1])
                except (json.JSONDecodeError, TypeError):
                    continue
                self._tool_metrics[tool_name] = {
                    "call_count": d.get("call_count", 0),
                    "success_count": d.get("success_count", 0),
                    "failure_count": d.get("failure_count", 0),
                    "total_latency_ms": d.get("total_latency_ms", 0.0),
                    "min_latency_ms": d.get("min_latency_ms", 0.0),
                    "max_latency_ms": d.get("max_latency_ms", 0.0),
                    "latency_samples": d.get("latency_samples", []),
                    "total_input_tokens": d.get("total_input_tokens", 0),
                    "total_output_tokens": d.get("total_output_tokens", 0),
                }
        logger.info("Loaded tool metrics from SQLite (%d tools)", len(rows))

    def reset(self) -> None:
        with self._lock:
            self._tool_metrics.clear()
            self._degradation_events.clear()
            self._quality_gate_results.clear()
            self._phase_transitions.clear()
            self._persist_count = 0
            self._last_persist_time = 0.0

    def start_auto_persist(self) -> None:
        if self._auto_persist_thread is not None and self._auto_persist_thread.is_alive():
            return
        self._auto_persist_stop.clear()
        self._auto_persist_thread = threading.Thread(
            target=self._auto_persist_loop, daemon=True, name="metrics-auto-persist"
        )
        self._auto_persist_thread.start()
        logger.info("Auto-persist started (interval=%.0fs)", self._persist_interval)

    def stop_auto_persist(self) -> None:
        self._auto_persist_stop.set()
        if self._auto_persist_thread is not None:
            self._auto_persist_thread.join(timeout=5.0)
            self._auto_persist_thread = None
        logger.info("Auto-persist stopped")

    def _should_auto_persist(self) -> bool:
        if self._persist_count >= self._persist_call_threshold:
            return True
        if self._last_persist_time == 0.0:
            return False
        return time.time() - self._last_persist_time >= self._persist_interval

    def _auto_persist_loop(self) -> None:
        while not self._auto_persist_stop.is_set():
            self._auto_persist_stop.wait(self._persist_interval)
            if self._auto_persist_stop.is_set():
                break
            try:
                self.persist()
            except Exception as exc:
                logger.warning("Auto-persist failed: %s", exc)

    @staticmethod
    def _percentile(values: list[float], pct: float) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        rank = pct / 100.0 * (n - 1)
        lower = int(rank)
        upper = min(lower + 1, n - 1)
        fraction = rank - lower
        return sorted_vals[lower] + fraction * (sorted_vals[upper] - sorted_vals[lower])


_instance: MetricsCollector | None = None
_instance_lock = threading.Lock()


def get_metrics_collector() -> MetricsCollector:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = MetricsCollector()
        return _instance
