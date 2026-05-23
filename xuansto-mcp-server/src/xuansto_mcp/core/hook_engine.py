from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

from .logging_config import get_logger

logger = get_logger("hook_engine")


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


class HookEngine:
    def __init__(self) -> None:
        self._pre_hooks: dict[str, list[_PreHookType | _AsyncPreHookType]] = {}
        self._post_hooks: dict[str, list[_PostHookType | _AsyncPostHookType]] = {}
        self._global_pre_hooks: list[_PreHookType | _AsyncPreHookType] = []
        self._global_post_hooks: list[_PostHookType | _AsyncPostHookType] = []
        self._lock = threading.Lock()

    def register_hook(self, hook_type: str, handler: Callable[..., Any], tool_name: str | None = None) -> None:
        with self._lock:
            if hook_type == "pre":
                if tool_name:
                    self._pre_hooks.setdefault(tool_name, []).append(handler)
                else:
                    self._global_pre_hooks.append(handler)
            elif hook_type == "post":
                if tool_name:
                    self._post_hooks.setdefault(tool_name, []).append(handler)
                else:
                    self._global_post_hooks.append(handler)
            else:
                logger.warning("Unknown hook type: %s", hook_type)

    def unregister_hook(self, hook_type: str, handler: Callable[..., Any], tool_name: str | None = None) -> bool:
        with self._lock:
            if hook_type == "pre":
                store = self._pre_hooks.get(tool_name, []) if tool_name else self._global_pre_hooks
            elif hook_type == "post":
                store = self._post_hooks.get(tool_name, []) if tool_name else self._global_post_hooks
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
            except Exception as e:
                handler_name = getattr(handler, "__name__", str(handler))
                all_errors.append({"hook": handler_name, "error": str(e)})
                logger.error("Pre-hook %s failed: %s", handler_name, e)

        return all_results, all_errors

    async def execute_post_hooks(self, tool_name: str, kwargs: dict[str, Any], result: dict[str, Any]) -> list[dict[str, str]]:
        all_errors: list[dict[str, str]] = []

        with self._lock:
            handlers = list(self._global_post_hooks) + list(self._post_hooks.get(tool_name, []))

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    hook_errors = await handler(tool_name, kwargs, result)
                else:
                    hook_errors = await asyncio.to_thread(handler, tool_name, kwargs, result)

                if isinstance(hook_errors, list):
                    all_errors.extend(hook_errors)
            except Exception as e:
                handler_name = getattr(handler, "__name__", str(handler))
                all_errors.append({"hook": handler_name, "error": str(e)})
                logger.error("Post-hook %s failed: %s", handler_name, e)

        return all_errors

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

            if not module_path or not function_name or hook_type not in ("pre", "post"):
                continue

            try:
                import importlib
                module = importlib.import_module(module_path)
                handler = getattr(module, function_name)
                self.register_hook(hook_type, handler, tool_name=tool_name)
                logger.info("Loaded hook from config: %s.%s (%s, tool=%s)", module_path, function_name, hook_type, tool_name)
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
