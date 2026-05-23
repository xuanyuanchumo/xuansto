from __future__ import annotations

import asyncio
import json
import threading
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

from .logging_config import get_logger

logger = get_logger("hook_engine")


class HookType(str, Enum):
    PRE = "pre"
    POST = "post"
    PHASE_ENTER = "phase_enter"
    PHASE_EXIT = "phase_exit"
    GATE_PASS = "gate_pass"
    GATE_FAIL = "gate_fail"
    SESSION_START = "session_start"
    SESSION_STOP = "session_stop"


@runtime_checkable
class HookHandler(Protocol):
    def __call__(self, tool_name: str, kwargs: dict[str, Any], **extra: Any) -> dict[str, Any]: ...


@runtime_checkable
class AsyncHookHandler(Protocol):
    async def __call__(self, tool_name: str, kwargs: dict[str, Any], **extra: Any) -> dict[str, Any]: ...


_PreHookType = Callable[[str, dict[str, Any]], tuple[list[dict[str, Any]], list[dict[str, str]]]]
_PostHookType = Callable[[str, dict[str, Any], dict[str, Any]], list[dict[str, str]]]
_AsyncPreHookType = Callable[[str, dict[str, Any]], Any]
_AsyncPostHookType = Callable[[str, dict[str, Any], dict[str, Any]], Any]

_HOOK_FAILURE_THRESHOLD = 5

_hook_failure_counts: dict[str, int] = {}


def _record_hook_failure(handler_name: str) -> None:
    _hook_failure_counts[handler_name] = _hook_failure_counts.get(handler_name, 0) + 1
    count = _hook_failure_counts[handler_name]
    if count == _HOOK_FAILURE_THRESHOLD:
        logger.warning(
            "Hook %s has failed %d times (threshold=%d). Alert: repeated hook failures detected.",
            handler_name, count, _HOOK_FAILURE_THRESHOLD,
        )


def _reset_hook_failure_count(handler_name: str) -> None:
    _hook_failure_counts.pop(handler_name, None)


def _resolve_hook_type(hook_type: str | HookType) -> HookType:
    if isinstance(hook_type, HookType):
        return hook_type
    try:
        return HookType(hook_type)
    except ValueError:
        logger.warning("Unknown hook type string: %s, falling back to PRE", hook_type)
        return HookType.PRE


class HookEngine:
    def __init__(self) -> None:
        self._pre_hooks: dict[str, list[_PreHookType | _AsyncPreHookType]] = {}
        self._post_hooks: dict[str, list[_PostHookType | _AsyncPostHookType]] = {}
        self._phase_enter_hooks: dict[str, list[Callable[..., Any]]] = {}
        self._phase_exit_hooks: dict[str, list[Callable[..., Any]]] = {}
        self._gate_pass_hooks: dict[str, list[Callable[..., Any]]] = {}
        self._gate_fail_hooks: dict[str, list[Callable[..., Any]]] = {}
        self._session_start_hooks: list[Callable[..., Any]] = []
        self._session_stop_hooks: list[Callable[..., Any]] = []
        self._global_pre_hooks: list[_PreHookType | _AsyncPreHookType] = []
        self._global_post_hooks: list[_PostHookType | _AsyncPostHookType] = []
        self._lock = threading.Lock()

    def register_hook(self, hook_type: str | HookType, handler: Callable[..., Any], tool_name: str | None = None) -> None:
        resolved = _resolve_hook_type(hook_type)
        with self._lock:
            if resolved == HookType.PRE:
                if tool_name:
                    self._pre_hooks.setdefault(tool_name, []).append(handler)
                else:
                    self._global_pre_hooks.append(handler)
            elif resolved == HookType.POST:
                if tool_name:
                    self._post_hooks.setdefault(tool_name, []).append(handler)
                else:
                    self._global_post_hooks.append(handler)
            elif resolved == HookType.PHASE_ENTER:
                key = tool_name or "__global__"
                self._phase_enter_hooks.setdefault(key, []).append(handler)
            elif resolved == HookType.PHASE_EXIT:
                key = tool_name or "__global__"
                self._phase_exit_hooks.setdefault(key, []).append(handler)
            elif resolved == HookType.GATE_PASS:
                key = tool_name or "__global__"
                self._gate_pass_hooks.setdefault(key, []).append(handler)
            elif resolved == HookType.GATE_FAIL:
                key = tool_name or "__global__"
                self._gate_fail_hooks.setdefault(key, []).append(handler)
            elif resolved == HookType.SESSION_START:
                self._session_start_hooks.append(handler)
            elif resolved == HookType.SESSION_STOP:
                self._session_stop_hooks.append(handler)

    def unregister_hook(self, hook_type: str | HookType, handler: Callable[..., Any], tool_name: str | None = None) -> bool:
        resolved = _resolve_hook_type(hook_type)
        with self._lock:
            if resolved == HookType.PRE:
                store = self._pre_hooks.get(tool_name, []) if tool_name else self._global_pre_hooks
            elif resolved == HookType.POST:
                store = self._post_hooks.get(tool_name, []) if tool_name else self._global_post_hooks
            elif resolved == HookType.PHASE_ENTER:
                key = tool_name or "__global__"
                store = self._phase_enter_hooks.get(key, [])
            elif resolved == HookType.PHASE_EXIT:
                key = tool_name or "__global__"
                store = self._phase_exit_hooks.get(key, [])
            elif resolved == HookType.GATE_PASS:
                key = tool_name or "__global__"
                store = self._gate_pass_hooks.get(key, [])
            elif resolved == HookType.GATE_FAIL:
                key = tool_name or "__global__"
                store = self._gate_fail_hooks.get(key, [])
            elif resolved == HookType.SESSION_START:
                store = self._session_start_hooks
            elif resolved == HookType.SESSION_STOP:
                store = self._session_stop_hooks
            else:
                return False
            try:
                store.remove(handler)
                return True
            except ValueError:
                return False

    async def execute_pre_hooks(self, tool_name: str, kwargs: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        all_results: list[dict[str, Any]] = []
        all_errors: list[dict[str, str]] = []

        with self._lock:
            handlers = list(self._global_pre_hooks) + list(self._pre_hooks.get(tool_name, []))

        for handler in handlers:
            handler_name = getattr(handler, "__name__", str(handler))
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(tool_name, kwargs)
                else:
                    result = await asyncio.to_thread(handler, tool_name, kwargs)

                if isinstance(result, tuple) and len(result) == 2:
                    hook_results, hook_errors = result
                    all_results.extend(hook_results if isinstance(hook_results, list) else [])
                    all_errors.extend(hook_errors if isinstance(hook_errors, list) else [])
                elif isinstance(result, dict):
                    all_results.append(result)
                    if result.get("status") == "block":
                        break
                elif isinstance(result, list):
                    all_results.extend(result)
                _reset_hook_failure_count(handler_name)
            except Exception as e:
                all_errors.append({"hook": handler_name, "error": str(e)})
                logger.error("Pre-hook %s failed: %s", handler_name, e)
                _record_hook_failure(handler_name)

        return all_results, all_errors

    async def execute_post_hooks(self, tool_name: str, kwargs: dict[str, Any], result: dict[str, Any]) -> list[dict[str, str]]:
        all_errors: list[dict[str, str]] = []

        with self._lock:
            handlers = list(self._global_post_hooks) + list(self._post_hooks.get(tool_name, []))

        for handler in handlers:
            handler_name = getattr(handler, "__name__", str(handler))
            try:
                if asyncio.iscoroutinefunction(handler):
                    hook_errors = await handler(tool_name, kwargs, result)
                else:
                    hook_errors = await asyncio.to_thread(handler, tool_name, kwargs, result)

                if isinstance(hook_errors, list):
                    all_errors.extend(hook_errors)
                _reset_hook_failure_count(handler_name)
            except Exception as e:
                all_errors.append({"hook": handler_name, "error": str(e)})
                logger.error("Post-hook %s failed: %s", handler_name, e)
                _record_hook_failure(handler_name)

        return all_errors

    def get_failure_counts(self) -> dict[str, int]:
        return dict(_hook_failure_counts)

    def load_hooks_from_config(self, config_path: str | Path) -> None:
        path = Path(config_path)
        if not path.exists():
            logger.debug("Hook config file not found: %s", path)
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load hook config from %s: %s", path, exc)
            return

        if not isinstance(data, dict):
            return

        hooks = data.get("hooks", [])
        if not isinstance(hooks, list):
            return

        for hook_entry in hooks:
            if not isinstance(hook_entry, dict):
                continue
            hook_type = hook_entry.get("type", "")
            tool_name = hook_entry.get("tool_name")
            module_path = hook_entry.get("module")
            function_name = hook_entry.get("function")

            try:
                resolved = _resolve_hook_type(hook_type)
            except Exception:
                continue

            if not module_path or not function_name:
                continue

            try:
                import importlib
                module = importlib.import_module(module_path)
                handler = getattr(module, function_name)
                self.register_hook(resolved, handler, tool_name=tool_name)
                logger.info("Loaded hook from config: %s.%s (%s, tool=%s)", module_path, function_name, resolved.value, tool_name)
            except Exception as exc:
                logger.warning("Failed to load hook %s.%s: %s", module_path, function_name, exc)


_hook_engine: HookEngine | None = None
_hook_engine_lock = threading.Lock()


def get_hook_engine() -> HookEngine:
    global _hook_engine
    with _hook_engine_lock:
        if _hook_engine is None:
            _hook_engine = HookEngine()
        return _hook_engine


def reset_hook_engine() -> None:
    global _hook_engine
    with _hook_engine_lock:
        _hook_engine = None
