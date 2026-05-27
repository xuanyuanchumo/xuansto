from __future__ import annotations

import threading
import time
from typing import Any


class TokenBucket:
    def __init__(self, max_tokens: float, refill_rate: float) -> None:
        self._max_tokens = max_tokens
        self._refill_rate = refill_rate
        self._tokens = max_tokens
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def consume(self, tokens: float = 1.0) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self._max_tokens, self._tokens + elapsed * self._refill_rate)
            self._last_refill = now
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def available_tokens(self) -> float:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            return min(self._max_tokens, self._tokens + elapsed * self._refill_rate)

    def reset(self) -> None:
        with self._lock:
            self._tokens = self._max_tokens
            self._last_refill = time.monotonic()


_DEFAULT_MAX_TOKENS = 60.0
_DEFAULT_REFILL_RATE = 1.0

_TOOL_RATE_LIMITS: dict[str, tuple[float, float]] = {
    "quality_gate_check": (120.0, 2.0),
    "config_manage": (10.0, 1.0 / 6.0),
    "security_scan": (30.0, 0.5),
}

_bucket_lock = threading.Lock()
_buckets: dict[str, TokenBucket] = {}


def _get_bucket(tool_name: str) -> TokenBucket:
    with _bucket_lock:
        if tool_name not in _buckets:
            max_tokens, refill_rate = _TOOL_RATE_LIMITS.get(
                tool_name, (_DEFAULT_MAX_TOKENS, _DEFAULT_REFILL_RATE)
            )
            _buckets[tool_name] = TokenBucket(
                max_tokens=max_tokens,
                refill_rate=refill_rate,
            )
        return _buckets[tool_name]


def check_rate_limit(tool_name: str) -> tuple[bool, dict[str, Any]]:
    bucket = _get_bucket(tool_name)
    allowed = bucket.consume()
    if allowed:
        return True, {}
    max_tokens, refill_rate = _TOOL_RATE_LIMITS.get(
        tool_name, (_DEFAULT_MAX_TOKENS, _DEFAULT_REFILL_RATE)
    )
    return False, {
        "error_code": "ERR_RATE_LIMITED",
        "message": f"Rate limit exceeded for tool: {tool_name}",
        "retry_after_seconds": 1.0 / refill_rate,
        "available_tokens": 0,
        "rate_limit": {
            "max_tokens": max_tokens,
            "refill_rate": refill_rate,
        },
    }


def configure_tool_limit(tool_name: str, max_tokens: float, refill_rate: float) -> None:
    with _bucket_lock:
        _buckets[tool_name] = TokenBucket(max_tokens=max_tokens, refill_rate=refill_rate)


def reset_all_limits() -> None:
    with _bucket_lock:
        for bucket in _buckets.values():
            bucket.reset()
