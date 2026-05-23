from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import WORK_DIR
from ..core.errors import make_error_response, make_success_response, ERR_VALIDATION, ERR_NOT_FOUND
from ..core.logging_config import get_logger
from ..core.notifications import notify
from ..core.validator import validate_input
from ..models.schemas import DecisionLogInput

logger = get_logger("decision_log")

DECISIONS_FILE = WORK_DIR / "decisions.json"


def _load_decisions() -> list[dict[str, Any]]:
    if not DECISIONS_FILE.exists():
        return []
    try:
        data = json.loads(DECISIONS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def _save_decisions(decisions: list[dict[str, Any]]) -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    DECISIONS_FILE.write_text(
        json.dumps(decisions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _log_decision(
    title: str | None = None,
    description: str | None = None,
    context: str | None = None,
    alternatives: list[str] | None = None,
    decision: str | None = None,
    rationale: str | None = None,
    impact: str | None = None,
    decided_by: str | None = None,
) -> dict[str, Any]:
    decisions = _load_decisions()
    now = datetime.now()
    entry_id = f"ADR-{now.strftime('%Y%m%d')}-{len(decisions) + 1:03d}"
    entry: dict[str, Any] = {
        "id": entry_id,
        "title": title or "",
        "description": description or "",
        "context": context or "",
        "alternatives": alternatives or [],
        "decision": decision or "",
        "rationale": rationale or "",
        "impact": impact or "",
        "decided_by": decided_by or "",
        "tags": [],
        "created_at": now.isoformat(),
    }
    decisions.append(entry)
    _save_decisions(decisions)
    notify(f"Decision logged: {entry_id} - {title or 'untitled'}", "info")
    return {"id": entry_id, "entry": entry, "total_decisions": len(decisions)}


def _query_decisions(
    keyword: str | None = None,
    tag: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    decisions = _load_decisions()
    results = list(decisions)
    if keyword:
        kw_lower = keyword.lower()
        results = [
            d for d in results
            if kw_lower in d.get("title", "").lower()
            or kw_lower in d.get("description", "").lower()
            or kw_lower in d.get("decision", "").lower()
            or kw_lower in d.get("rationale", "").lower()
        ]
    if tag:
        results = [d for d in results if tag in d.get("tags", [])]
    if date_from:
        results = [d for d in results if d.get("created_at", "") >= date_from]
    if date_to:
        results = [d for d in results if d.get("created_at", "") <= date_to]
    total = len(results)
    results = results[:limit]
    return {"results": results, "total": total, "limit": limit}


def _export_decisions(
    format: str = "json",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    decisions = _load_decisions()
    if date_from:
        decisions = [d for d in decisions if d.get("created_at", "") >= date_from]
    if date_to:
        decisions = [d for d in decisions if d.get("created_at", "") <= date_to]
    if format == "markdown":
        lines = ["# Decision Log\n"]
        for d in decisions:
            lines.append(f"## {d.get('id', '')}: {d.get('title', '')}\n")
            lines.append(f"- **Description**: {d.get('description', '')}")
            lines.append(f"- **Context**: {d.get('context', '')}")
            lines.append(f"- **Decision**: {d.get('decision', '')}")
            lines.append(f"- **Rationale**: {d.get('rationale', '')}")
            lines.append(f"- **Impact**: {d.get('impact', '')}")
            lines.append(f"- **Decided By**: {d.get('decided_by', '')}")
            alts = d.get("alternatives", [])
            if alts:
                lines.append(f"- **Alternatives**: {', '.join(alts)}")
            lines.append(f"- **Created At**: {d.get('created_at', '')}\n")
        exported = "\n".join(lines)
        return {"format": "markdown", "content": exported, "total": len(decisions)}
    return {"format": "json", "content": decisions, "total": len(decisions)}


def _inline_decision_log(action: str, **kwargs: Any) -> dict[str, Any]:
    if action == "log":
        return _log_decision(**{k: v for k, v in kwargs.items() if k in (
            "title", "description", "context", "alternatives",
            "decision", "rationale", "impact", "decided_by",
        )})
    elif action == "query":
        return _query_decisions(**{k: v for k, v in kwargs.items() if k in (
            "keyword", "tag", "date_from", "date_to", "limit",
        )})
    elif action == "export":
        return _export_decisions(**{k: v for k, v in kwargs.items() if k in (
            "format", "date_from", "date_to",
        )})
    return {"error": True, "message": f"未知操作: {action}"}


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        )
    )
    async def decision_log(
        action: str,
        title: str | None = None,
        description: str | None = None,
        context: str | None = None,
        alternatives: list[str] | None = None,
        decision: str | None = None,
        rationale: str | None = None,
        impact: str | None = None,
        decided_by: str | None = None,
        keyword: str | None = None,
        tag: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 20,
        format: str = "json",
    ) -> dict[str, Any]:
        """决策日志管理：记录决策条目、搜索决策、导出决策记录。log操作记录一条决策(含标题/描述/上下文/备选方案/最终决策/理由/影响/决策者)，query操作按关键词/标签/日期范围搜索决策，export操作导出决策为JSON或Markdown格式。"""
        validated, err = validate_input(DecisionLogInput, action=action, title=title, description=description, context=context, alternatives=alternatives, decision=decision, rationale=rationale, impact=impact, decided_by=decided_by, keyword=keyword, tag=tag, date_from=date_from, date_to=date_to, limit=limit, format=format)
        if err:
            return err
        logger.info("decision_log called: action=%s", action)
        if action == "log":
            if not title:
                return make_error_response(ValueError("log操作需要title参数"), error_code=ERR_VALIDATION)
            return make_success_response(_log_decision(title, description, context, alternatives, decision, rationale, impact, decided_by))
        elif action == "query":
            return make_success_response(_query_decisions(keyword, tag, date_from, date_to, limit))
        elif action == "export":
            return make_success_response(_export_decisions(format, date_from, date_to))
        else:
            return make_error_response(ValueError(f"未知操作: {action}，支持: log, query, export"), error_code=ERR_VALIDATION)
