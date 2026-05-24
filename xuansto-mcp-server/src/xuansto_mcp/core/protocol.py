from __future__ import annotations

import asyncio
from typing import Any


TOOL_CALL_TIMEOUT_SECONDS = 30
CHAIN_TIMEOUT_SECONDS = 120
MAX_CHAIN_RETRIES = 2

VERSION_CONFLICT_MAX_RETRIES = 3
SERVICE_ERROR_MAX_RETRIES = 2
SERVICE_ERROR_BASE_DELAY = 1.0
EMBEDDING_FAILURE_MAX_RETRIES = 5
EMBEDDING_FAILURE_DELAY = 60.0


def get_retry_config(error_type: str) -> dict[str, Any]:
    if error_type == "version_conflict":
        return {"max_retries": VERSION_CONFLICT_MAX_RETRIES, "delay": 0, "backoff": "immediate"}
    elif error_type == "service_error":
        return {"max_retries": SERVICE_ERROR_MAX_RETRIES, "delay": SERVICE_ERROR_BASE_DELAY, "backoff": "exponential"}
    elif error_type == "embedding_failure":
        return {"max_retries": EMBEDDING_FAILURE_MAX_RETRIES, "delay": EMBEDDING_FAILURE_DELAY, "backoff": "fixed"}
    return {"max_retries": 0, "delay": 0, "backoff": "none"}


async def async_retry(fn, error_type: str = "service_error", **kwargs):
    config = get_retry_config(error_type)
    last_error = None
    for attempt in range(config["max_retries"] + 1):
        try:
            return await fn(**kwargs)
        except Exception as exc:
            last_error = exc
            if attempt >= config["max_retries"]:
                break
            delay = config["delay"]
            if config["backoff"] == "exponential":
                delay = config["delay"] * (2 ** attempt)
            elif config["backoff"] == "fixed":
                delay = config["delay"]
            if delay > 0:
                await asyncio.sleep(delay)
    raise last_error


class SkillToolCallProtocol:
    @staticmethod
    def validate_call(tool_name: str, params: dict[str, Any]) -> dict[str, Any] | None:
        return None

    @staticmethod
    def should_retry(error: Exception, attempt: int) -> bool:
        from .errors import is_retryable_error
        if attempt >= MAX_CHAIN_RETRIES:
            return False
        return is_retryable_error(error)

    @staticmethod
    def get_timeout(tool_name: str) -> int:
        return TOOL_CALL_TIMEOUT_SECONDS

    @staticmethod
    def get_chain_timeout(chain_length: int) -> int:
        return CHAIN_TIMEOUT_SECONDS

    @staticmethod
    def format_chain_call(tools: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "chain": tools,
            "timeout": SkillToolCallProtocol.get_chain_timeout(len(tools)),
            "max_retries": MAX_CHAIN_RETRIES,
        }
