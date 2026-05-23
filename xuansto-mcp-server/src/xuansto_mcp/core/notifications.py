from __future__ import annotations

import threading
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class NotificationCallback(Protocol):
    def send(self, message: str, level: str = "info") -> None: ...


class _NullNotificationCallback:
    def send(self, message: str, level: str = "info") -> None:
        pass


_notification_callback: NotificationCallback = _NullNotificationCallback()
_notification_lock = threading.Lock()


def set_notification_callback(callback: NotificationCallback | None) -> None:
    global _notification_callback
    with _notification_lock:
        if callback is None:
            _notification_callback = _NullNotificationCallback()
        else:
            _notification_callback = callback


def get_notification_callback() -> NotificationCallback:
    return _notification_callback


def notify(message: str, level: str = "info") -> None:
    from .logging_config import get_logger
    logger = get_logger("notification")
    try:
        callback = get_notification_callback()
        callback.send(message, level)
    except Exception as e:
        logger.warning("Notification callback failed: %s", e)
