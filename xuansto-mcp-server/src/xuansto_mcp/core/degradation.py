from __future__ import annotations

import asyncio
import atexit
import contextlib
import hashlib
import importlib
import importlib.util
import json
import random
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Any, cast

from . import atomic_write
from .config import DATA_DIR, SCRIPTS_DIR
from .errors import ERR_INTERNAL, XuanstoMCPError, make_error_response, make_success_response
from .logging_config import get_logger

logger = get_logger("degradation")

MCP_AVAILABLE = True

_FALLBACK_CONFIG_PATH = DATA_DIR / "fallback_config.yaml"


class DegradationLevel(str, Enum):
    L1_NORMAL = "L1_NORMAL"
    L2_LOCAL_SEMANTIC = "L2_LOCAL_SEMANTIC"
    L3_BM25_ONLY = "L3_BM25_ONLY"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, DegradationLevel):
            return NotImplemented
        order = [DegradationLevel.L1_NORMAL, DegradationLevel.L2_LOCAL_SEMANTIC, DegradationLevel.L3_BM25_ONLY]
        return order.index(self) < order.index(other)

    def __le__(self, other: object) -> bool:
        return self == other or self < other

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, DegradationLevel):
            return NotImplemented
        return not self <= other

    def __ge__(self, other: object) -> bool:
        return self == other or self > other


_LEVEL_ORDER = [DegradationLevel.L1_NORMAL, DegradationLevel.L2_LOCAL_SEMANTIC, DegradationLevel.L3_BM25_ONLY]


class _ComponentState:
    __slots__ = ("name", "level", "check_fn", "recover_fn", "last_check_time",
                 "last_check_healthy", "recovery_attempts", "next_recovery_time",
                 "degraded_since", "levels")

    def __init__(
        self,
        name: str,
        check_fn: Callable[[], bool],
        recover_fn: Callable[[], bool],
        levels: list[str],
    ) -> None:
        self.name = name
        self.level = levels[0] if levels else "normal"
        self.check_fn = check_fn
        self.recover_fn = recover_fn
        self.last_check_time: float = 0.0
        self.last_check_healthy: bool = True
        self.recovery_attempts: int = 0
        self.next_recovery_time: float = 0.0
        self.degraded_since: float | None = None
        self.levels = levels

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "last_check_time": self.last_check_time,
            "last_check_healthy": self.last_check_healthy,
            "recovery_attempts": self.recovery_attempts,
            "next_recovery_time": self.next_recovery_time,
            "degraded_since": self.degraded_since,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], check_fn: Callable[[], bool],
                  recover_fn: Callable[[], bool], levels: list[str]) -> _ComponentState:
        state = cls(data.get("name", ""), check_fn, recover_fn, levels)
        state.level = data.get("level", levels[0] if levels else "normal")
        state.last_check_time = data.get("last_check_time", 0.0)
        state.last_check_healthy = data.get("last_check_healthy", True)
        state.recovery_attempts = data.get("recovery_attempts", 0)
        state.next_recovery_time = data.get("next_recovery_time", 0.0)
        state.degraded_since = data.get("degraded_since")
        return state


class DegradationManager:
    _DEFAULT_HEALTH_INTERVAL: float = 30.0
    _BASE_RECOVERY_BACKOFF: float = 5.0
    _MAX_RECOVERY_BACKOFF: float = 300.0
    _BACKOFF_MULTIPLIER: float = 2.0
    _STATE_FILENAME: str = "degradation_state.json"

    def __init__(self, health_interval: float | None = None) -> None:
        self._lock = threading.RLock()
        self._components: dict[str, _ComponentState] = {}
        self._subscribers: list[Callable[[str, str, str], None]] = []
        self._health_interval = health_interval or self._DEFAULT_HEALTH_INTERVAL
        self._health_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._started = False
        self._overall_level = DegradationLevel.L1_NORMAL
        atexit.register(self._persist_state)

    def register_component(
        self,
        name: str,
        check_fn: Callable[[], bool],
        recover_fn: Callable[[], bool],
        levels: list[str] | None = None,
    ) -> None:
        if levels is None:
            levels = ["normal", "degraded", "unavailable"]
        with self._lock:
            if name in self._components:
                logger.warning("Component %s already registered, updating", name)
                existing = self._components[name]
                existing.check_fn = check_fn
                existing.recover_fn = recover_fn
                existing.levels = levels
            else:
                self._components[name] = _ComponentState(name, check_fn, recover_fn, levels)
            logger.info("Registered degradation component: %s (levels=%s)", name, levels)

    def get_current_level(self) -> str:
        with self._lock:
            return self._overall_level.value

    def check_and_degrade(self, component: str) -> str:
        with self._lock:
            state = self._components.get(component)
            if state is None:
                logger.warning("Unknown component: %s", component)
                return "unknown"
            healthy = False
            try:
                healthy = state.check_fn()
            except Exception as exc:
                logger.warning("Health check failed for %s: %s", component, exc)
                healthy = False
            state.last_check_time = time.time()
            state.last_check_healthy = healthy
            if not healthy:
                current_idx = state.levels.index(state.level) if state.level in state.levels else 0
                if current_idx < len(state.levels) - 1:
                    old_level = state.level
                    state.level = state.levels[current_idx + 1]
                    if state.degraded_since is None:
                        state.degraded_since = time.time()
                    state.recovery_attempts = 0
                    state.next_recovery_time = time.time() + self._compute_backoff(0)
                    logger.warning(
                        "Component %s degraded: %s -> %s", component, old_level, state.level
                    )
                    self._notify(component, old_level, state.level)
            self._update_overall_level()
            self._persist_state()
            return state.level

    def attempt_recovery(self, component: str) -> bool:
        with self._lock:
            state = self._components.get(component)
            if state is None:
                logger.warning("Unknown component: %s", component)
                return False
            if state.level == state.levels[0]:
                return True
            if time.time() < state.next_recovery_time:
                return False
            recovered = False
            try:
                recovered = state.recover_fn()
            except Exception as exc:
                logger.warning("Recovery attempt failed for %s: %s", component, exc)
                recovered = False
            if recovered:
                old_level = state.level
                current_idx = state.levels.index(state.level) if state.level in state.levels else 0
                if current_idx > 0:
                    state.level = state.levels[current_idx - 1]
                else:
                    state.level = state.levels[0]
                if state.level == state.levels[0]:
                    state.degraded_since = None
                    state.recovery_attempts = 0
                else:
                    state.recovery_attempts += 1
                    state.next_recovery_time = time.time() + self._compute_backoff(state.recovery_attempts)
                logger.info(
                    "Component %s recovered: %s -> %s", component, old_level, state.level
                )
                self._notify(component, old_level, state.level)
            else:
                state.recovery_attempts += 1
                state.next_recovery_time = time.time() + self._compute_backoff(state.recovery_attempts)
                logger.info(
                    "Component %s recovery failed (attempt %d), next try in %.1fs",
                    component, state.recovery_attempts,
                    self._compute_backoff(state.recovery_attempts),
                )
            self._update_overall_level()
            self._persist_state()
            return recovered

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            components = {}
            for name, state in self._components.items():
                components[name] = state.to_dict()
            return {
                "overall_level": self._overall_level.value,
                "components": components,
                "health_interval": self._health_interval,
                "started": self._started,
            }

    def subscribe(self, callback: Callable[[str, str, str], None]) -> None:
        with self._lock:
            self._subscribers.append(callback)

    def start_health_monitor(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True
            self._stop_event.clear()
        self._health_thread = threading.Thread(
            target=self._health_loop, daemon=True, name="degradation-health-monitor"
        )
        self._health_thread.start()
        logger.info("Degradation health monitor started (interval=%.1fs)", self._health_interval)

    def stop_health_monitor(self) -> None:
        with self._lock:
            if not self._started:
                return
            self._started = False
        self._stop_event.set()
        if self._health_thread is not None:
            self._health_thread.join(timeout=5.0)
            self._health_thread = None
        logger.info("Degradation health monitor stopped")

    def load_state(self) -> None:
        try:
            from .config import WORK_DIR
            state_path = WORK_DIR / self._STATE_FILENAME
        except Exception:
            return
        if not state_path.exists():
            return
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load degradation state: %s", exc)
            return
        components_data = data.get("components", {})
        stored_hash = data.get("_hash")
        if stored_hash is not None:
            computed_hash = hashlib.sha256(json.dumps(components_data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
            if computed_hash != stored_hash:
                logger.warning("Degradation state hash mismatch, skipping load")
                return
        else:
            logger.warning("Degradation state file has no integrity hash, loading without verification")
        with self._lock:
            for name, comp_data in components_data.items():
                state = self._components.get(name)
                if state is not None:
                    state.level = comp_data.get("level", state.levels[0])
                    state.last_check_time = comp_data.get("last_check_time", 0.0)
                    state.last_check_healthy = comp_data.get("last_check_healthy", True)
                    state.recovery_attempts = comp_data.get("recovery_attempts", 0)
                    state.next_recovery_time = comp_data.get("next_recovery_time", 0.0)
                    state.degraded_since = comp_data.get("degraded_since")
            overall = data.get("overall_level")
            if overall:
                with contextlib.suppress(ValueError):
                    self._overall_level = DegradationLevel(overall)
        logger.info("Loaded degradation state from %s", state_path)

    def _compute_backoff(self, attempts: int) -> float:
        backoff = self._BASE_RECOVERY_BACKOFF * (self._BACKOFF_MULTIPLIER ** attempts)
        jitter = random.uniform(0, 0.5) * backoff
        return min(backoff + jitter, self._MAX_RECOVERY_BACKOFF)

    def _update_overall_level(self) -> None:
        worst = DegradationLevel.L1_NORMAL
        for state in self._components.values():
            level_map = {
                "chromadb": DegradationLevel.L1_NORMAL,
                "sqlite_fts": DegradationLevel.L2_LOCAL_SEMANTIC,
                "keyword": DegradationLevel.L3_BM25_ONLY,
                "full": DegradationLevel.L1_NORMAL,
                "workspace_only": DegradationLevel.L2_LOCAL_SEMANTIC,
                "no_knowledge": DegradationLevel.L3_BM25_ONLY,
                "full_hooks": DegradationLevel.L1_NORMAL,
                "essential_only": DegradationLevel.L2_LOCAL_SEMANTIC,
                "no_hooks": DegradationLevel.L3_BM25_ONLY,
                "full_resources": DegradationLevel.L1_NORMAL,
                "cached_only": DegradationLevel.L2_LOCAL_SEMANTIC,
                "minimal": DegradationLevel.L3_BM25_ONLY,
                "normal": DegradationLevel.L1_NORMAL,
                "degraded": DegradationLevel.L2_LOCAL_SEMANTIC,
                "unavailable": DegradationLevel.L3_BM25_ONLY,
            }
            component_level = level_map.get(state.level, DegradationLevel.L2_LOCAL_SEMANTIC)
            if component_level > worst:
                worst = component_level
        old_overall = self._overall_level
        self._overall_level = worst
        if old_overall != worst:
            logger.info("Overall degradation level changed: %s -> %s", old_overall.value, worst.value)

    def _notify(self, component: str, old_level: str, new_level: str) -> None:
        for callback in self._subscribers:
            try:
                callback(component, old_level, new_level)
            except Exception as exc:
                logger.warning("Subscriber callback error: %s", exc)
        try:
            from .notifications import send_mcp_notification
            send_mcp_notification("degradation_change", {
                "component": component,
                "old_level": old_level,
                "new_level": new_level,
                "overall_level": self._overall_level.value,
            })
        except Exception:
            pass

    def _persist_state(self) -> None:
        try:
            from .config import WORK_DIR
            state_path = WORK_DIR / self._STATE_FILENAME
        except Exception:
            return
        with self._lock:
            try:
                data = self.get_status()
                components_data = data.get("components", {})
                data["_timestamp"] = time.time()
                data["_hash"] = hashlib.sha256(json.dumps(components_data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
                atomic_write(state_path, json.dumps(data, ensure_ascii=False, indent=2))
            except Exception as exc:
                logger.warning("Failed to persist degradation state: %s", exc)

    def _health_loop(self) -> None:
        while not self._stop_event.is_set():
            component_names: list[str]
            with self._lock:
                component_names = list(self._components.keys())
            for name in component_names:
                if self._stop_event.is_set():
                    break
                self.check_and_degrade(name)
                with self._lock:
                    state = self._components.get(name)
                if state is not None and state.level != state.levels[0]:
                    self.attempt_recovery(name)
            self._stop_event.wait(self._health_interval)


def _check_search_engine() -> bool:
    try:
        import chromadb

        from .config import KNOWLEDGE_CHROMA_PATH
        client = chromadb.PersistentClient(path=str(KNOWLEDGE_CHROMA_PATH))
        client.get_or_create_collection("knowledge")
        return True
    except ImportError:
        return False
    except Exception:
        return False


def _recover_search_engine() -> bool:
    try:
        import chromadb

        from .config import KNOWLEDGE_CHROMA_PATH
        client = chromadb.PersistentClient(path=str(KNOWLEDGE_CHROMA_PATH))
        client.get_or_create_collection("knowledge")
        return True
    except Exception:
        return False


def _check_knowledge_base() -> bool:
    try:
        from .config import KNOWLEDGE_CHROMA_PATH, KNOWLEDGE_DB_PATH
        if KNOWLEDGE_CHROMA_PATH.exists() and KNOWLEDGE_DB_PATH.exists():
            return True
        return bool(KNOWLEDGE_DB_PATH.exists())
    except Exception:
        return False


def _recover_knowledge_base() -> bool:
    try:
        from .config import KNOWLEDGE_DB_PATH
        return KNOWLEDGE_DB_PATH.exists()
    except Exception:
        return False


def _check_hooks() -> bool:
    try:
        from .config import HOOKS_PATH
        return HOOKS_PATH.exists()
    except Exception:
        return False


def _recover_hooks() -> bool:
    try:
        from .config import HOOKS_PATH
        return HOOKS_PATH.exists()
    except Exception:
        return False


def _check_resources() -> bool:
    try:
        from .config import DATA_DIR
        return DATA_DIR.exists()
    except Exception:
        return False


def _recover_resources() -> bool:
    try:
        from .config import DATA_DIR
        return DATA_DIR.exists()
    except Exception:
        return False


_MANAGER: DegradationManager | None = None
_MANAGER_LOCK = threading.Lock()


def get_degradation_manager() -> DegradationManager:
    global _MANAGER
    with _MANAGER_LOCK:
        if _MANAGER is None:
            from .config import DEGRADATION_HEALTH_CHECK_INTERVAL
            _MANAGER = DegradationManager(health_interval=DEGRADATION_HEALTH_CHECK_INTERVAL)
            _MANAGER.register_component(
                "search_engine",
                check_fn=_check_search_engine,
                recover_fn=_recover_search_engine,
                levels=["chromadb", "sqlite_fts", "keyword"],
            )
            _MANAGER.register_component(
                "knowledge_base",
                check_fn=_check_knowledge_base,
                recover_fn=_recover_knowledge_base,
                levels=["full", "workspace_only", "no_knowledge"],
            )
            _MANAGER.register_component(
                "hooks",
                check_fn=_check_hooks,
                recover_fn=_recover_hooks,
                levels=["full_hooks", "essential_only", "no_hooks"],
            )
            _MANAGER.register_component(
                "resources",
                check_fn=_check_resources,
                recover_fn=_recover_resources,
                levels=["full_resources", "cached_only", "minimal"],
            )
            _MANAGER.load_state()
        return _MANAGER


def check_mcp_available() -> bool:
    global MCP_AVAILABLE
    try:
        from mcp.server.fastmcp import FastMCP
        MCP_AVAILABLE = True
        return True
    except ImportError:
        MCP_AVAILABLE = False
        return False


def run_script_fallback(
    script_name: str,
    args: list[str] | None = None,
    cwd: str = ".",
    timeout: int = 60,
) -> dict[str, Any]:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        return {
            "error": True,
            "code": "SCRIPT_NOT_FOUND",
            "message": f"脚本不存在: {script_name}",
            "fallback": True,
        }

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        try:
            parsed = json.loads(result.stdout)
            return {"error": False, "data": parsed, "fallback": True, "degraded": True}
        except json.JSONDecodeError:
            return {
                "error": False,
                "data": {"raw_output": result.stdout[:2000]},
                "fallback": True,
                "degraded": True,
            }
    except subprocess.TimeoutExpired:
        return {
            "error": True,
            "code": "TIMEOUT",
            "message": f"脚本执行超时({timeout}s): {script_name}",
            "fallback": True,
        }
    except Exception as e:
        return {
            "error": True,
            "code": "EXECUTION_ERROR",
            "message": str(e),
            "fallback": True,
        }


async def run_script_fallback_async(
    script_name: str,
    args: list[str] | None = None,
    cwd: str = ".",
    timeout: int = 60,
) -> dict[str, Any]:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        return {"error": True, "code": "SCRIPT_NOT_FOUND", "message": f"脚本不存在: {script_name}", "fallback": True}
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode("utf-8", errors="replace").strip()
        try:
            parsed = json.loads(output)
            return {"error": False, "data": parsed, "fallback": True, "degraded": True}
        except json.JSONDecodeError:
            return {"error": False, "data": {"raw_output": output[:2000]}, "fallback": True, "degraded": True}
    except asyncio.TimeoutError:
        return {"error": True, "code": "TIMEOUT", "message": f"脚本执行超时({timeout}s): {script_name}", "fallback": True}
    except Exception as e:
        return {"error": True, "code": "EXECUTION_ERROR", "message": str(e), "fallback": True}


def _fallback_success(
    tool: str,
    data: dict[str, Any] | None = None,
    degradation_level: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    base = data if isinstance(data, dict) else {}
    enriched = {"tool": tool, "source": "fallback", **base, **extra}
    enriched["degraded"] = True
    if "status" not in enriched:
        enriched["status"] = "degraded"
    if "note" not in enriched:
        enriched["note"] = "主工具不可用，使用降级响应"
    result = make_success_response(enriched, degradation_level=degradation_level)
    result["degraded"] = True
    return result


def _fallback_error(tool: str, code: str, message: str) -> dict[str, Any]:
    return make_error_response(XuanstoMCPError(
        code=code,
        message=message,
        details={"tool": tool, "source": "fallback"},
    ), error_code=ERR_INTERNAL)


def _standardize_result(
    result: dict[str, Any],
    tool: str,
    **extra: Any,
) -> dict[str, Any]:
    if result.get("error"):
        return make_error_response(XuanstoMCPError(
            code=result.get("code", "UNKNOWN_ERROR"),
            message=result.get("message", "未知错误"),
            details={"tool": tool, "source": "fallback"},
        ), error_code=ERR_INTERNAL)
    data = result.get("data", {})
    if not isinstance(data, dict):
        data = {"result": data}
    data["degraded"] = True
    return _fallback_success(tool, data, **extra)


def _try_inline_fallback(tool_module: str, func_name: str, *args: Any, **kwargs: Any) -> Any | None:
    module_name = f"xuansto_mcp.tools.{tool_module}"
    try:
        if importlib.util.find_spec(module_name) is None:
            return None
        mod = importlib.import_module(module_name)
        fn = getattr(mod, func_name, None)
        if fn is None:
            return None
        return fn(*args, **kwargs)
    except Exception:
        return None


def skill_analyze_fallback(skill_path: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "skill_analyze")
    script_result = run_script_fallback(
        "skill-test.py",
        args=["--analyze", "--path", skill_path, "--format", "json"],
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "skill_analyze")
    script_result = run_script_fallback(
        "skill-test.py",
        args=["--path", skill_path, "--format", "json"],
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "skill_analyze")
    inline_result = _try_inline_fallback("skill_analyze", "_inline_skill_analyze", skill_path, **kwargs)
    if inline_result is not None:
        return _fallback_success("skill_analyze", inline_result, degradation_level="inline")
    return _fallback_success("skill_analyze", {"skill_path": skill_path, "analyzed": False}, degradation_level="minimal")


def knowledge_search_fallback(query: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "knowledge_search")
    script_result = run_script_fallback(
        "knowledge-server.py",
        args=["--search", "--query", query, "--format", "json"],
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "knowledge_search")
    script_result = run_script_fallback(
        "knowledge-server.py",
        args=["search", "--query", query, "--format", "json"],
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "knowledge_search")
    inline_result = _try_inline_fallback("knowledge_search", "_inline_knowledge_search", query, **kwargs)
    if inline_result is not None:
        return _fallback_success("knowledge_search", inline_result, degradation_level="inline")
    return _fallback_success("knowledge_search", {"query": query, "results": []}, degradation_level="minimal")


def knowledge_inject_fallback(action: str = "inject", topics: list[str] | None = None, scope: str = "general", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "knowledge_inject")
    script_result = run_script_fallback(
        "knowledge-server.py",
        args=["--inject", "--action", action, "--scope", scope, "--format", "json"],
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "knowledge_inject")
    inline_result = _try_inline_fallback("knowledge_inject", "_inline_knowledge_inject", action, topics, scope, **kwargs)
    if inline_result is not None:
        return _fallback_success("knowledge_inject", inline_result, degradation_level="inline")
    return _fallback_success("knowledge_inject", {"action": action, "injected_count": 0, "topics": topics or []}, degradation_level="minimal")


def quality_gate_fallback(gate_ids: list[str] | None = None, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "quality_gate_check")
    gate_args = ["--gate", "--format", "json"]
    if gate_ids:
        gate_args.extend(["--gate-ids", ",".join(gate_ids)])
    script_result = run_script_fallback(
        "skill-test.py",
        args=gate_args,
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "quality_gate_check")
    from .config import GATE_SCRIPTS_MAP
    if not gate_ids:
        gate_ids = list(GATE_SCRIPTS_MAP.keys())
    results = []
    for gate_id in gate_ids:
        script = GATE_SCRIPTS_MAP.get(gate_id)
        if script:
            result = run_script_fallback(script, args=["--format", "json"], timeout=30)
            results.append({"gate_id": gate_id, **result})
        else:
            results.append({"gate_id": gate_id, "status": "SKIP", "fallback": True})
    if any(r.get("status") != "SKIP" for r in results):
        return _fallback_success("quality_gate_check", {"checks": results})
    inline_result = _try_inline_fallback("quality_gate_check", "_inline_quality_gate", gate_ids, **kwargs)
    if inline_result is not None:
        return _fallback_success("quality_gate_check", inline_result, degradation_level="inline")
    return _fallback_success("quality_gate_check", {"checks": results}, degradation_level="minimal")


def spec_drift_fallback(spec_dir: str = ".trae/specs", src_dir: str = ".", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "spec_drift_detect")
    script_result = run_script_fallback(
        "spec-drift-detector.py",
        args=["--spec-dir", spec_dir, "--src-dir", src_dir, "--format", "json"],
        timeout=60,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "spec_drift_detect")
    inline_result = _try_inline_fallback("spec_drift_detect", "_inline_spec_drift", spec_dir, src_dir)
    if inline_result is not None:
        return _fallback_success("spec_drift_detect", inline_result, degradation_level="inline")
    return _fallback_success("spec_drift_detect", {"spec_dir": spec_dir, "src_dir": src_dir, "drifts": []}, degradation_level="minimal")


def security_scan_fallback(target: str = ".", severity_threshold: str = "medium", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "security_scan")
    script_path = SCRIPTS_DIR / "agentic-security-scanner.py"
    if script_path.exists():
        result = run_script_fallback(
            "agentic-security-scanner.py",
            args=["--target", target, "--severity-threshold", severity_threshold, "--format", "json"],
            timeout=120,
        )
        if not result.get("error"):
            return _standardize_result(result, "security_scan")
    inline_result = _try_inline_fallback("security_scan", "_inline_agentic_scan", target, severity_threshold)
    if inline_result is not None:
        return _fallback_success("security_scan", {"agentic_scan": inline_result}, degradation_level="inline")
    return _fallback_success("security_scan", {"target": target, "issues": [], "scanned": False}, degradation_level="minimal")


def code_simplify_fallback(target: str, scope: str = "recent", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "code_simplify")
    script_result = run_script_fallback(
        "code-simplifier.py",
        args=["--target", target, "--scope", scope, "--format", "json"],
        timeout=60,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "code_simplify")
    inline_result = _try_inline_fallback("code_simplify", "_inline_simplify", target, scope)
    if inline_result is not None:
        return _fallback_success("code_simplify", inline_result, degradation_level="inline")
    return _fallback_success("code_simplify", {"target": target, "scope": scope, "simplified": False}, degradation_level="minimal")


def session_manage_fallback(action: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "session_manage")
    if action in ("save", "init"):
        script_result = run_script_fallback(
            "init-session.py",
            args=["--action", action, "--format", "json"],
            timeout=15,
        )
        if not script_result.get("error"):
            return _standardize_result(script_result, "session_manage")
    if action in ("load", "detect", "restore"):
        script_result = run_script_fallback(
            "session-catchup.py",
            args=["--action", action, "--format", "json"],
            timeout=15,
        )
        if not script_result.get("error"):
            return _standardize_result(script_result, "session_manage")
    args_map = {
        "save": ["save"],
        "load": ["load"],
        "list": ["list"],
    }
    args = args_map.get(action, [action])
    script_result = run_script_fallback(
        "session-persist.py",
        args=args,
        timeout=15,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "session_manage")
    inline_result = _try_inline_fallback("session_manage", "_inline_session_manage", action, **kwargs)
    if inline_result is not None:
        return _fallback_success("session_manage", inline_result, degradation_level="inline")
    return _fallback_success("session_manage", {"action": action, "status": "unavailable"}, degradation_level="minimal")


def workflow_dispatch_fallback(action: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "workflow_dispatch")
    if action == "start":
        script_result = run_script_fallback("project-initializer.py", args=["--format", "json"], timeout=30)
        if not script_result.get("error"):
            return _standardize_result(script_result, "workflow_dispatch")
        try:
            from ..tools.workflow_dispatch import _load_workflow
            return _fallback_success("workflow_dispatch", {"action": "start", "status": "script_failed"})
        except Exception:
            pass
        return _fallback_success("workflow_dispatch", {"action": "start", "status": "unavailable"}, degradation_level="minimal")
    elif action == "status":
        try:
            from ..tools.workflow_dispatch import _load_workflow
            workflow_id = kwargs.get("workflow_id", "")
            if workflow_id:
                state = _load_workflow(workflow_id)
                if state:
                    return _fallback_success("workflow_dispatch", state)
        except Exception:
            pass
        return _fallback_success("workflow_dispatch", {"action": action, "status": "unavailable"}, degradation_level="minimal")
    elif action == "abort":
        return _fallback_success("workflow_dispatch", {"status": "aborted"})
    return _fallback_error("workflow_dispatch", "UNKNOWN_ACTION", f"未知操作: {action}")


def agent_status_fallback(action: str = "list", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "agent_status")
    from .config import AGENTS_DIR
    registry_yaml = AGENTS_DIR / "registry.yaml"
    phase_map: dict[str, int] = {}
    if registry_yaml.exists():
        try:
            import yaml
            raw = yaml.safe_load(registry_yaml.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                for layer in raw.get("layers", []):
                    for agent in layer.get("agents", []):
                        name = agent.get("name", "")
                        p = agent.get("phase", 2)
                        if name:
                            phase_map[name] = p
        except Exception:
            pass
    if action == "list" and AGENTS_DIR.exists():
        agents = []
        for agent_file in sorted(AGENTS_DIR.rglob("*.md")):
            name = agent_file.stem
            agents.append({
                "name": name,
                "layer": agent_file.parent.name,
                "phase": phase_map.get(name, 2),
                "source": "static_registry",
            })
        phase_filter = kwargs.get("phase")
        if phase_filter is not None:
            try:
                phase_val = int(phase_filter)
                agents = [a for a in agents if a.get("phase", 2) <= phase_val]
            except (ValueError, TypeError):
                pass
        return _fallback_success("agent_status", {"agents": agents, "total": len(agents), "phase_filter": phase_filter})
    if action in ("detail", "by_phase") and AGENTS_DIR.exists():
        agent_name = kwargs.get("agent_name", "")
        phase = kwargs.get("phase", "")
        if agent_name:
            for agent_file in AGENTS_DIR.rglob(f"{agent_name}.md"):
                content = agent_file.read_text(encoding="utf-8", errors="replace")[:2000]
                return _fallback_success("agent_status", {"name": agent_name, "content_preview": content, "phase": phase_map.get(agent_name, 2), "source": "static_registry"})
        if phase:
            phase_agents = []
            for agent_file in sorted(AGENTS_DIR.rglob("*.md")):
                name = agent_file.stem
                phase_agents.append({"name": name, "layer": agent_file.parent.name, "phase": phase_map.get(name, 2)})
            return _fallback_success("agent_status", {"agents": phase_agents, "phase": phase, "source": "static_registry"})
    script_result = run_script_fallback("skill-test.py", args=["--agents", "--format", "json"], timeout=30)
    if not script_result.get("error"):
        return _standardize_result(script_result, "agent_status")
    inline_result = _try_inline_fallback("agent_status", "_inline_agent_status", action, **kwargs)
    if inline_result is not None:
        return _fallback_success("agent_status", inline_result, degradation_level="inline")
    return _fallback_success("agent_status", {"agents": [], "total": 0}, degradation_level="minimal")


def hook_manage_fallback(action: str = "list", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "hook_manage")
    if action == "execute" and kwargs.get("hook_name"):
        hook_scripts = {
            "encoding-check": "check-encoding.py",
            "token-budget-check": "token-budget-guard.py",
            "session-save": "session-persist.py",
        }
        script = hook_scripts.get(kwargs["hook_name"])
        if script:
            script_result = run_script_fallback(script, args=["--format", "json"], timeout=30)
            if not script_result.get("error"):
                return _standardize_result(script_result, "hook_manage")
    inline_result = _try_inline_fallback("hook_manage", "_inline_hook_manage", action, **kwargs)
    if inline_result is not None:
        return _fallback_success("hook_manage", inline_result, degradation_level="inline")
    return _fallback_success("hook_manage", {"hooks": []}, degradation_level="minimal")


def resource_load_status_fallback(action: str = "status", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "resource_load_status")
    try:
        from .config import WORK_DIR
        state_file = WORK_DIR / "resource_state.json"
        if state_file.exists():
            data = json.loads(state_file.read_text(encoding="utf-8"))
            return _fallback_success("resource_load_status", {"resources": data})
    except Exception:
        pass
    inline_result = _try_inline_fallback("resource_load_status", "_inline_resource_load_status", action, **kwargs)
    if inline_result is not None:
        return _fallback_success("resource_load_status", inline_result, degradation_level="inline")
    return _fallback_success("resource_load_status", {"resources": {}}, degradation_level="minimal")


def context_compress_fallback(content: str = "", strategy: str = "semantic", **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "context_compress")
    script_result = run_script_fallback("context-compressor.py", args=["--strategy", strategy, "--format", "json"], timeout=30)
    if not script_result.get("error"):
        return _standardize_result(script_result, "context_compress")
    inline_result = _try_inline_fallback("context_compress", "_inline_context_compress", content, strategy, **kwargs)
    if inline_result is not None:
        return _fallback_success("context_compress", inline_result, degradation_level="inline")
    return _fallback_success("context_compress", {"strategy": strategy, "compressed": False}, degradation_level="minimal")


def server_health_fallback(**kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "server_health")
    script_result = run_script_fallback(
        "health-checker.py",
        args=["--format", "json"],
        timeout=15,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "server_health")
    inline_result = _try_inline_fallback("server_health", "_inline_server_health", **kwargs)
    if inline_result is not None:
        return _fallback_success("server_health", inline_result, degradation_level="inline")
    return _fallback_success("server_health", {"status": "degraded", "mcp_available": False}, degradation_level="minimal")


def fallback_decision_log(action: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "decision_log")
    script_result = run_script_fallback(
        "decision-log.py",
        args=["--action", action, "--format", "json"],
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "decision_log")
    inline_result = _try_inline_fallback("decision_log", "_inline_decision_log", action, **kwargs)
    if inline_result is not None:
        return _fallback_success("decision_log", inline_result, degradation_level="inline")
    return _fallback_success("decision_log", {"action": action, "entries": []}, degradation_level="minimal")


def fallback_token_budget(action: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "token_budget")
    script_result = run_script_fallback(
        "token-budget-guard.py",
        args=["--action", action, "--format", "json"],
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "token_budget")
    inline_result = _try_inline_fallback("token_budget", "_inline_token_budget", action, **kwargs)
    if inline_result is not None:
        return _fallback_success("token_budget", inline_result, degradation_level="inline")
    return _fallback_success("token_budget", {"action": action, "budget": {}}, degradation_level="minimal")


def fallback_project_init(action: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "project_init")
    script_result = run_script_fallback(
        "project-initializer.py",
        args=["--action", action, "--format", "json"],
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "project_init")
    inline_result = _try_inline_fallback("project_init", "_inline_project_init", action, **kwargs)
    if inline_result is not None:
        return _fallback_success("project_init", inline_result, degradation_level="inline")
    return _fallback_success("project_init", {"action": action, "initialized": False}, degradation_level="minimal")


def agent_manage_fallback(action: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "agent_manage")
    inline_result = _try_inline_fallback("agent_manage", "_inline_agent_manage", action, **kwargs)
    if inline_result is not None:
        return _fallback_success("agent_manage", inline_result, degradation_level="inline")
    return _fallback_success("agent_manage", {"action": action, "managed": False}, degradation_level="minimal")


def metrics_report_fallback(action: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "metrics_report")
    script_result = run_script_fallback(
        "test-reporter.py",
        args=["--action", action, "--format", "json"],
        timeout=30,
    )
    if not script_result.get("error"):
        return _standardize_result(script_result, "metrics_report")
    inline_result = _try_inline_fallback("metrics_report", "_inline_metrics_report", action, **kwargs)
    if inline_result is not None:
        return _fallback_success("metrics_report", inline_result, degradation_level="inline")
    return _fallback_success("metrics_report", {"action": action, "metrics": {}}, degradation_level="minimal")


def config_manage_fallback(action: str, **kwargs: Any) -> dict[str, Any]:
    logger.warning("Tool %s using fallback", "config_manage")
    inline_result = _try_inline_fallback("config_manage", "_inline_config_manage", action, **kwargs)
    if inline_result is not None:
        return _fallback_success("config_manage", inline_result, degradation_level="inline")
    return _fallback_success("config_manage", {"action": action, "config": {}}, degradation_level="minimal")


FALLBACK_MAP = {
    "skill_analyze": skill_analyze_fallback,
    "knowledge_search": knowledge_search_fallback,
    "knowledge_inject": knowledge_inject_fallback,
    "quality_gate_check": quality_gate_fallback,
    "spec_drift_detect": spec_drift_fallback,
    "security_scan": security_scan_fallback,
    "code_simplify": code_simplify_fallback,
    "session_manage": session_manage_fallback,
    "workflow_dispatch": workflow_dispatch_fallback,
    "agent_status": agent_status_fallback,
    "hook_manage": hook_manage_fallback,
    "resource_load_status": resource_load_status_fallback,
    "context_compress": context_compress_fallback,
    "server_health": server_health_fallback,
    "decision_log": fallback_decision_log,
    "token_budget": fallback_token_budget,
    "project_init": fallback_project_init,
    "agent_manage": agent_manage_fallback,
    "metrics_report": metrics_report_fallback,
    "config_manage": config_manage_fallback,
}


class DegradationExecutor:
    def __init__(self, scripts_dir: Path | None = None, timeout: int = 5) -> None:
        self._scripts_dir = scripts_dir or SCRIPTS_DIR
        self._timeout = timeout
        self._fallback_map = FALLBACK_MAP

    async def execute(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        fallback_fn = self._fallback_map.get(tool_name)
        if fallback_fn is not None:
            try:
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, lambda: fallback_fn(**kwargs)),
                    timeout=self._timeout,
                )
                if isinstance(result, dict):
                    result["degraded"] = True
                return result
            except asyncio.TimeoutError:
                logger.error("DegradationExecutor timeout for %s (%ds)", tool_name, self._timeout)
            except Exception as exc:
                logger.error("Fallback execution failed for %s: %s", tool_name, exc)

        return self._minimal_response(tool_name, kwargs)

    def execute_sync(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        fallback_fn = self._fallback_map.get(tool_name)
        if fallback_fn is not None:
            try:
                result = fallback_fn(**kwargs)
                if isinstance(result, dict):
                    result["degraded"] = True
                return result
            except Exception as exc:
                logger.error("Fallback execution failed for %s: %s", tool_name, exc)

        return self._minimal_response(tool_name, kwargs)

    def _minimal_response(self, tool_name: str, kwargs: dict[str, Any]) -> dict[str, Any]:
        return make_success_response({
            "tool": tool_name,
            "status": "unavailable",
            "degraded": True,
            "source": "minimal_fallback",
        })


_EXECUTOR: DegradationExecutor | None = None
_EXECUTOR_LOCK = threading.Lock()


def get_degradation_executor() -> DegradationExecutor:
    global _EXECUTOR
    with _EXECUTOR_LOCK:
        if _EXECUTOR is None:
            _EXECUTOR = DegradationExecutor()
        return _EXECUTOR


_INLINE_FALLBACK_MAP = {
    "skill_analyze_fallback": skill_analyze_fallback,
    "knowledge_search_fallback": knowledge_search_fallback,
    "knowledge_inject_fallback": knowledge_inject_fallback,
    "quality_gate_fallback": quality_gate_fallback,
    "spec_drift_fallback": spec_drift_fallback,
    "security_scan_fallback": security_scan_fallback,
    "code_simplify_fallback": code_simplify_fallback,
    "session_manage_fallback": session_manage_fallback,
    "workflow_dispatch_fallback": workflow_dispatch_fallback,
    "agent_status_fallback": agent_status_fallback,
    "hook_manage_fallback": hook_manage_fallback,
    "resource_load_status_fallback": resource_load_status_fallback,
    "context_compress_fallback": context_compress_fallback,
    "server_health_fallback": server_health_fallback,
    "decision_log_fallback": fallback_decision_log,
    "token_budget_fallback": fallback_token_budget,
    "project_init_fallback": fallback_project_init,
    "agent_manage_fallback": agent_manage_fallback,
    "metrics_report_fallback": metrics_report_fallback,
    "config_manage_fallback": config_manage_fallback,
}


def _load_fallback_config_from_yaml() -> dict[str, Any] | None:
    if not _FALLBACK_CONFIG_PATH.exists():
        return None
    try:
        import yaml
        raw = yaml.safe_load(_FALLBACK_CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "fallback_map" in raw:
            return raw["fallback_map"]
    except Exception as exc:
        logger.warning("Failed to load fallback config from YAML: %s", exc)
    return None


def _build_fallback_map_from_yaml(yaml_config: dict[str, Any]) -> dict[str, Callable[..., Any]]:
    built: dict[str, Callable[..., Any]] = {}
    for tool_name, entry in yaml_config.items():
        inline_name = entry.get("inline") if isinstance(entry, dict) else None
        if inline_name and inline_name in _INLINE_FALLBACK_MAP:
            built[tool_name] = _INLINE_FALLBACK_MAP[inline_name]
        elif tool_name in FALLBACK_MAP:
            built[tool_name] = FALLBACK_MAP[tool_name]
    return built


_fallback_config_mtime: float = 0.0


def _get_fallback_config_mtime() -> float:
    try:
        if _FALLBACK_CONFIG_PATH.exists():
            return _FALLBACK_CONFIG_PATH.stat().st_mtime
    except OSError:
        pass
    return 0.0


def _resolve_fallback_map() -> dict[str, Callable[..., Any]]:
    global _fallback_config_mtime
    current_mtime = _get_fallback_config_mtime()
    if current_mtime != _fallback_config_mtime:
        _fallback_config_mtime = current_mtime
        yaml_config = _load_fallback_config_from_yaml()
        if yaml_config is not None:
            merged = _build_fallback_map_from_yaml(yaml_config)
            for tool_name, fn in FALLBACK_MAP.items():
                if tool_name not in merged:
                    merged[tool_name] = fn
            return merged
    return dict(FALLBACK_MAP)


_RESOLVED_FALLBACK_MAP: dict[str, Callable[..., Any]] = _resolve_fallback_map()


def _refresh_resolved_fallback_map() -> None:
    global _RESOLVED_FALLBACK_MAP
    _RESOLVED_FALLBACK_MAP = _resolve_fallback_map()


_HAS_WATCHFILES_DEGR = False
try:
    import watchfiles as _watchfiles_degr_mod
    _HAS_WATCHFILES_DEGR = True
except ImportError:
    _HAS_WATCHFILES_DEGR = False


_fallback_watcher_thread: threading.Thread | None = None
_fallback_watcher_stop = threading.Event()


def _fallback_watcher_poll() -> None:
    while not _fallback_watcher_stop.is_set():
        _fallback_watcher_stop.wait(5.0)
        _refresh_resolved_fallback_map()


def _fallback_watcher_watchfiles() -> None:
    watch_dir = _FALLBACK_CONFIG_PATH.parent if _FALLBACK_CONFIG_PATH.exists() else DATA_DIR
    if not watch_dir.exists():
        _fallback_watcher_poll()
        return
    try:
        for _changes in _watchfiles_degr_mod.watch(watch_dir, stop_event=_fallback_watcher_stop):
            _refresh_resolved_fallback_map()
    except Exception as exc:
        logger.warning("Fallback config watchfiles watcher failed, falling back to polling: %s", exc)
        _fallback_watcher_poll()


def start_fallback_watcher() -> None:
    global _fallback_watcher_thread
    target = _fallback_watcher_watchfiles if _HAS_WATCHFILES_DEGR else _fallback_watcher_poll
    _fallback_watcher_thread = threading.Thread(target=target, daemon=True)
    _fallback_watcher_thread.start()
    logger.info("Fallback config watcher started (%s)", "watchfiles" if _HAS_WATCHFILES_DEGR else "polling")


def stop_fallback_watcher() -> None:
    _fallback_watcher_stop.set()


def get_fallback(tool_name: str) -> Callable[..., Any] | None:
    _refresh_resolved_fallback_map()
    fn = _RESOLVED_FALLBACK_MAP.get(tool_name)
    if fn:
        return cast(Callable[..., Any], fn)
    logger.warning("No fallback function for tool: %s", tool_name)
    return None


def _atexit_persist_state() -> None:
    global _MANAGER
    if _MANAGER is not None:
        with contextlib.suppress(Exception):
            _MANAGER._persist_state()


atexit.register(_atexit_persist_state)
