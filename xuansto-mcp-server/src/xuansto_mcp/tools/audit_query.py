from __future__ import annotations

from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.audit_logger import get_audit_logger
from ..core.errors import ERR_VALIDATION, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.validator import validate_input
from ..models.schemas import AuditQueryInput

logger = get_logger("audit_query")


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    async def audit_query(
        tool_name: str | None = None,
        date_range: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """审计日志查询：查询MCP工具调用审计记录，支持按工具名和日期范围过滤。Prefer using Resource xuansto://audit/recent for read-only access."""
        validated, val_err = validate_input(
            AuditQueryInput, tool_name=tool_name, date_range=date_range, limit=limit
        )
        if val_err:
            return val_err

        assert validated is not None
        tool_name_val = validated.tool_name
        date_range_val = validated.date_range
        limit_val = validated.limit

        logger.info("audit_query called: tool_name=%s, date_range=%s, limit=%d", tool_name_val, date_range_val, limit_val)

        try:
            audit = get_audit_logger()

            date_from: datetime | None = None
            date_to: datetime | None = None
            if date_range_val:
                parts = date_range_val.split(":")
                if len(parts) != 2:
                    return make_error_response(
                        ValueError(f"date_range格式错误，应为 YYYY-MM-DD:YYYY-MM-DD，实际: {date_range_val}"),
                        error_code=ERR_VALIDATION,
                    )
                try:
                    date_from = datetime.strptime(parts[0].strip(), "%Y-%m-%d")
                    date_to = datetime.strptime(parts[1].strip() + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                except ValueError as e:
                    return make_error_response(
                        ValueError(f"date_range日期解析失败: {e}"),
                        error_code=ERR_VALIDATION,
                    )

            effective_limit = min(limit_val, 500)
            raw_limit = effective_limit * 5 if date_range_val else effective_limit

            entries = audit.query(tool_name=tool_name_val, limit=raw_limit)

            if date_range_val and (date_from is not None or date_to is not None):
                filtered: list[dict[str, Any]] = []
                for entry in entries:
                    ts = entry.get("timestamp")
                    if ts is None:
                        continue
                    try:
                        entry_dt = datetime.fromtimestamp(ts)
                    except (OSError, ValueError, OverflowError):
                        continue
                    if date_from and entry_dt < date_from:
                        continue
                    if date_to and entry_dt > date_to:
                        continue
                    filtered.append(entry)
                    if len(filtered) >= effective_limit:
                        break
                entries = filtered
            else:
                entries = entries[:effective_limit]

            success_count = sum(1 for e in entries if e.get("success") is True)
            error_count = sum(1 for e in entries if e.get("success") is False)
            tool_names = sorted({e.get("tool", "") for e in entries if e.get("tool")})

            return make_success_response({
                "entries": entries,
                "total_returned": len(entries),
                "filters": {
                    "tool_name": tool_name_val,
                    "date_range": date_range_val,
                    "limit": effective_limit,
                },
                "summary": {
                    "success_count": success_count,
                    "error_count": error_count,
                    "unique_tools": len(tool_names),
                    "tool_names": tool_names,
                },
            })

        except Exception as e:
            logger.error("audit_query error: %s", e)
            return make_error_response(e)
