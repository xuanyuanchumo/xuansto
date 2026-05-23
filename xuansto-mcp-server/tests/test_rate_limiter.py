from __future__ import annotations

import time
import threading

import pytest

from xuansto_mcp.core.rate_limiter import (
    TokenBucket,
    check_rate_limit,
    configure_tool_limit,
    reset_all_limits,
    _buckets,
    _bucket_lock,
)


def test_token_bucket_allows_within_limit():
    bucket = TokenBucket(max_tokens=5.0, refill_rate=1.0)
    for _ in range(5):
        assert bucket.consume() is True


def test_token_bucket_denies_over_limit():
    bucket = TokenBucket(max_tokens=3.0, refill_rate=1.0)
    for _ in range(3):
        assert bucket.consume() is True
    assert bucket.consume() is False


def test_token_bucket_refill_over_time():
    bucket = TokenBucket(max_tokens=10.0, refill_rate=100.0)
    for _ in range(10):
        bucket.consume()
    assert bucket.consume() is False
    time.sleep(0.05)
    assert bucket.consume() is True


def test_token_bucket_available_tokens():
    bucket = TokenBucket(max_tokens=10.0, refill_rate=1.0)
    assert bucket.available_tokens() <= 10.0
    bucket.consume(5.0)
    assert bucket.available_tokens() <= 5.0


def test_token_bucket_reset():
    bucket = TokenBucket(max_tokens=5.0, refill_rate=1.0)
    for _ in range(5):
        bucket.consume()
    assert bucket.consume() is False
    bucket.reset()
    assert bucket.consume() is True


def test_token_bucket_consume_custom_amount():
    bucket = TokenBucket(max_tokens=10.0, refill_rate=1.0)
    assert bucket.consume(5.0) is True
    assert bucket.consume(5.0) is True
    assert bucket.consume(1.0) is False


def test_check_rate_limit_allows():
    with _bucket_lock:
        _buckets.clear()
    allowed, info = check_rate_limit("test_tool_allow")
    assert allowed is True
    assert info == {}


def test_check_rate_limit_denies():
    with _bucket_lock:
        _buckets.clear()
    configure_tool_limit("test_tool_deny", max_tokens=2.0, refill_rate=0.001)
    check_rate_limit("test_tool_deny")
    check_rate_limit("test_tool_deny")
    allowed, info = check_rate_limit("test_tool_deny")
    assert allowed is False
    assert "error_code" in info
    assert info["error_code"] == "ERR_RATE_LIMITED"


def test_check_rate_limit_returns_retry_info():
    with _bucket_lock:
        _buckets.clear()
    configure_tool_limit("test_tool_info", max_tokens=1.0, refill_rate=0.001)
    check_rate_limit("test_tool_info")
    allowed, info = check_rate_limit("test_tool_info")
    if not allowed:
        assert "retry_after_seconds" in info


def test_configure_tool_limit():
    with _bucket_lock:
        _buckets.clear()
    configure_tool_limit("custom_tool", max_tokens=100.0, refill_rate=10.0)
    allowed, _ = check_rate_limit("custom_tool")
    assert allowed is True


def test_reset_all_limits():
    with _bucket_lock:
        _buckets.clear()
    configure_tool_limit("reset_tool", max_tokens=1.0, refill_rate=0.001)
    check_rate_limit("reset_tool")
    assert check_rate_limit("reset_tool")[0] is False
    reset_all_limits()
    assert check_rate_limit("reset_tool")[0] is True


def test_token_bucket_thread_safety():
    bucket = TokenBucket(max_tokens=100.0, refill_rate=10.0)
    errors = []
    success_count = threading.atomic = []

    def consumer():
        try:
            for _ in range(50):
                bucket.consume()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=consumer) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    assert len(errors) == 0, f"Thread safety errors: {errors}"


def test_check_rate_limit_different_tools_independent():
    with _bucket_lock:
        _buckets.clear()
    configure_tool_limit("tool_a", max_tokens=1.0, refill_rate=0.001)
    configure_tool_limit("tool_b", max_tokens=1.0, refill_rate=0.001)
    check_rate_limit("tool_a")
    check_rate_limit("tool_b")
    assert check_rate_limit("tool_a")[0] is False
    assert check_rate_limit("tool_b")[0] is False
