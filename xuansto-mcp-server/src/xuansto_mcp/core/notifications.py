from __future__ import annotations

import threading
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class NotificationCallback(Protocol):
    def send(self, message: str, level: str = "info") -> None: ...


class _NullNotificationCallback:
    def send(self, message: str, level: str = "info") -> None:
        pass


@runtime_checkable
class MCPNotificationCallback(Protocol):
    def send_notification(self, event_type: str, data: dict[str, Any]) -> None: ...


class _NullMCPNotificationCallback:
    def send_notification(self, event_type: str, data: dict[str, Any]) -> None:
        pass


_notification_callback: NotificationCallback = _NullNotificationCallback()
_notification_lock = threading.Lock()

_mcp_notification_callback: MCPNotificationCallback = _NullMCPNotificationCallback()
_mcp_notification_lock = threading.Lock()

_NOTIFICATION_EVENTS = frozenset({
    "degradation_change",
    "phase_transition",
    "phase_degradation",
    "token_budget_exceeded",
    "gate_failed",
    "config_change",
    "resource_updated",
})


def set_notification_callback(callback: NotificationCallback | None) -> None:
    global _notification_callback
    with _notification_lock:
        _notification_callback = _NullNotificationCallback() if callback is None else callback


def get_notification_callback() -> NotificationCallback:
    return _notification_callback


def set_mcp_notification_callback(callback: MCPNotificationCallback | None) -> None:
    global _mcp_notification_callback
    with _mcp_notification_lock:
        _mcp_notification_callback = _NullMCPNotificationCallback() if callback is None else callback


def get_mcp_notification_callback() -> MCPNotificationCallback:
    return _mcp_notification_callback


def send_mcp_notification(event_type: str, data: dict[str, Any]) -> None:
    from .logging_config import get_logger
    logger = get_logger("mcp_notification")
    if event_type not in _NOTIFICATION_EVENTS:
        logger.debug("Unknown MCP notification event type: %s", event_type)
    try:
        callback = get_mcp_notification_callback()
        callback.send_notification(event_type, data)
    except Exception as e:
        logger.warning("MCP notification callback failed for %s: %s", event_type, e)


def notify(message: str, level: str = "info") -> None:
    from .logging_config import get_logger
    logger = get_logger("notification")
    try:
        callback = get_notification_callback()
        callback.send(message, level)
    except Exception as e:
        logger.warning("Notification callback failed: %s", e)
