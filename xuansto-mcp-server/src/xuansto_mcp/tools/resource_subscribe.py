from __future__ import annotations

import uuid
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.errors import ERR_VALIDATION, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.validator import validate_input
from ..models.schemas import ResourceSubscribeInput
from ..resources.skill_resources import get_subscriptions, subscribe_resource, unsubscribe_resource

logger = get_logger("resource_subscribe")

_VALID_URI_PREFIX = "xuansto://"


def notify_subscribers(uri: str, event_data: dict[str, Any]) -> None:
    from ..core.notifications import send_mcp_notification
    subs = get_subscriptions(uri)
    subscribers = subs.get("subscribers", [])
    if not subscribers:
        return
    send_mcp_notification("resource_updated", {
        "uri": uri,
        "subscribers": subscribers,
        "event_data": event_data,
    })
    logger.info("Notified %d subscribers of %s update", len(subscribers), uri)


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        )
    )
    async def resource_subscribe(
        action: str,
        uri: str | None = None,
        client_id: str | None = None,
    ) -> dict[str, Any]:
        """资源订阅管理：订阅/取消订阅/列出资源变更通知。当订阅的资源(如xuansto://loading/status)发生变化时，服务器会通过MCP通知推送更新。"""
        validated, err = validate_input(ResourceSubscribeInput, action=action, uri=uri, client_id=client_id)
        if err:
            return err
        logger.info("resource_subscribe called: action=%s uri=%s client_id=%s", action, uri, client_id)
        try:
            if action == "subscribe":
                if not uri:
                    return make_error_response(ValueError("subscribe操作需要提供uri参数"), error_code=ERR_VALIDATION)
                if not uri.startswith(_VALID_URI_PREFIX):
                    return make_error_response(ValueError(f"无效的资源URI: {uri}，必须以 {_VALID_URI_PREFIX} 开头"), error_code=ERR_VALIDATION)
                resolved_client_id = client_id or f"client-{uuid.uuid4().hex[:8]}"
                result = subscribe_resource(uri, resolved_client_id)
                return make_success_response({
                    "action": "subscribe",
                    "uri": uri,
                    "client_id": resolved_client_id,
                    "subscribed": result.get("subscribed", True),
                })

            elif action == "unsubscribe":
                if not uri:
                    return make_error_response(ValueError("unsubscribe操作需要提供uri参数"), error_code=ERR_VALIDATION)
                if not client_id:
                    return make_error_response(ValueError("unsubscribe操作需要提供client_id参数"), error_code=ERR_VALIDATION)
                result = unsubscribe_resource(uri, client_id)
                return make_success_response({
                    "action": "unsubscribe",
                    "uri": uri,
                    "client_id": client_id,
                    "unsubscribed": result.get("unsubscribed", True),
                })

            elif action == "list":
                result = get_subscriptions(uri)
                return make_success_response({
                    "action": "list",
                    **result,
                })

            else:
                return make_error_response(ValueError(f"未知操作: {action}，支持: subscribe, unsubscribe, list"), error_code=ERR_VALIDATION)
        except Exception as e:
            logger.error("resource_subscribe error: %s", e)
            return make_error_response(e)
