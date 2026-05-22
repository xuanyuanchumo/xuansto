from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any


def _format_error(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": True, "code": code, "message": message, "details": details}


def _run_async(coro: Any) -> Any:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    return asyncio.run(coro)


def _invoke_tool(tool_name: str, params_json: str) -> dict[str, Any]:
    from .server import _REGISTERED_TOOL_NAMES, _TOOL_REGISTRY

    if tool_name not in _REGISTERED_TOOL_NAMES:
        return _format_error("TOOL_NOT_FOUND", f"工具不存在: {tool_name}", {"available": _REGISTERED_TOOL_NAMES})

    tool_fn = _TOOL_REGISTRY[tool_name]
    try:
        params = json.loads(params_json) if params_json else {}
    except json.JSONDecodeError as e:
        return _format_error("INVALID_JSON", f"参数JSON解析失败: {e}")

    try:
        result = _run_async(tool_fn.fn(**params))
        if isinstance(result, dict):
            return result
        return {"error": False, "data": result}
    except Exception as e:
        return _format_error("EXECUTION_ERROR", str(e))


def _health_check() -> dict[str, Any]:
    from .server import _REGISTERED_TOOL_NAMES, _TOOL_REGISTRY

    if "server_health" not in _REGISTERED_TOOL_NAMES:
        return _format_error("TOOL_NOT_FOUND", "server_health 工具未注册")

    tool_fn = _TOOL_REGISTRY["server_health"]
    try:
        result = _run_async(tool_fn.fn())
        if isinstance(result, dict):
            return result
        return {"error": False, "data": result}
    except Exception as e:
        return _format_error("HEALTH_CHECK_FAILED", str(e))


def main() -> None:
    parser = argparse.ArgumentParser(prog="xuansto-cli", description="xuansto-mcp-server 命令行工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    health_parser = subparsers.add_parser("health", help="检查 MCP Server 健康状态")
    invoke_parser = subparsers.add_parser("invoke", help="调用 MCP 工具")
    invoke_parser.add_argument("tool", help="工具名称")
    invoke_parser.add_argument("--params", default="{}", help="工具参数 (JSON 格式)")

    gate_parser = subparsers.add_parser("gate", help="执行质量门禁检查")
    gate_parser.add_argument("gate_id", help="门禁ID (如 GATE-007)")
    gate_parser.add_argument("--project-path", default=".", help="项目路径")

    version_parser = subparsers.add_parser("version", help="显示版本号")

    config_parser = subparsers.add_parser("config", help="显示当前配置")

    reload_parser = subparsers.add_parser("reload", help="重载配置")

    workflow_parser = subparsers.add_parser("workflow", help="工作流管理")
    workflow_sub = workflow_parser.add_subparsers(dest="workflow_action")

    workflow_start = workflow_sub.add_parser("start", help="启动工作流")
    workflow_start.add_argument("workflow_name", help="工作流名称")

    workflow_status = workflow_sub.add_parser("status", help="查询工作流状态")
    workflow_status.add_argument("--workflow-id", default="", help="工作流ID")

    workflow_recover = workflow_sub.add_parser("recover", help="从快照恢复工作流")
    workflow_recover.add_argument("--workflow-id", required=True, help="工作流ID")
    workflow_recover.add_argument("--phase", type=int, default=None, help="恢复到指定Phase")

    workflow_snapshots = workflow_sub.add_parser("snapshots", help="列出工作流快照")
    workflow_snapshots.add_argument("--workflow-id", default="", help="工作流ID")

    session_parser = subparsers.add_parser("session", help="会话管理")
    session_sub = session_parser.add_subparsers(dest="session_action")

    session_save = session_sub.add_parser("save", help="保存会话状态")
    session_save.add_argument("--label", default="", help="会话标签")

    session_load = session_sub.add_parser("load", help="加载会话状态")
    session_load.add_argument("--session-id", default="", help="会话ID")

    session_list = session_sub.add_parser("list", help="列出会话")

    agent_parser = subparsers.add_parser("agent", help="Agent管理")
    agent_sub = agent_parser.add_subparsers(dest="agent_action")

    agent_list = agent_sub.add_parser("list", help="列出Agent")

    agent_create = agent_sub.add_parser("create", help="创建Agent")
    agent_create.add_argument("--type", dest="agent_type", required=True, help="Agent类型")
    agent_create.add_argument("--capabilities", nargs="+", default=[], help="Agent能力列表")

    agent_match = agent_sub.add_parser("match", help="按能力匹配Agent")
    agent_match.add_argument("--capabilities", nargs="+", required=True, help="所需能力")

    args = parser.parse_args()

    if args.command == "health":
        result = _health_check()
    elif args.command == "invoke":
        result = _invoke_tool(args.tool, args.params)
    elif args.command == "gate":
        result = _invoke_tool("quality_gate_check", json.dumps({"gate_ids": [args.gate_id], "project_path": args.project_path}))
    elif args.command == "version":
        from . import __version__
        result = {"version": __version__}
    elif args.command == "config":
        from .core.config import DATA_DIR, SKILL_ROOT, WORK_DIR
        result = {
            "data_dir": str(DATA_DIR),
            "skill_root": str(SKILL_ROOT),
            "work_dir": str(WORK_DIR),
            "data_dir_exists": DATA_DIR.exists(),
            "skill_root_exists": SKILL_ROOT.exists(),
            "work_dir_exists": WORK_DIR.exists(),
        }
    elif args.command == "reload":
        from .core.config import reload_config
        result = reload_config()
    elif args.command == "workflow":
        if args.workflow_action == "start":
            result = _invoke_tool("workflow_dispatch", json.dumps({"action": "start", "workflow": args.workflow_name}))
        elif args.workflow_action == "status":
            result = _invoke_tool("workflow_dispatch", json.dumps({"action": "status", "workflow_id": args.workflow_id}))
        elif args.workflow_action == "recover":
            params: dict[str, Any] = {"action": "recover", "workflow_id": args.workflow_id}
            if args.phase is not None:
                params["snapshot_phase"] = args.phase
            result = _invoke_tool("workflow_dispatch", json.dumps(params))
        elif args.workflow_action == "snapshots":
            result = _invoke_tool("workflow_dispatch", json.dumps({"action": "snapshots", "workflow_id": args.workflow_id}))
        else:
            workflow_parser.print_help()
            return
    elif args.command == "session":
        if args.session_action == "save":
            result = _invoke_tool("session_manage", json.dumps({"action": "track", "label": args.label}))
        elif args.session_action == "load":
            result = _invoke_tool("session_manage", json.dumps({"action": "restore", "session_id": args.session_id}))
        elif args.session_action == "list":
            result = _invoke_tool("session_manage", json.dumps({"action": "list"}))
        else:
            session_parser.print_help()
            return
    elif args.command == "agent":
        if args.agent_action == "list":
            result = _invoke_tool("agent_status", json.dumps({"action": "list"}))
        elif args.agent_action == "create":
            result = _invoke_tool("agent_status", json.dumps({"action": "create", "agent_type": args.agent_type, "capabilities": args.capabilities}))
        elif args.agent_action == "match":
            result = _invoke_tool("agent_status", json.dumps({"action": "match", "capabilities": args.capabilities}))
        else:
            agent_parser.print_help()
            return
    else:
        parser.print_help()
        sys.exit(1)
        return

    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    if isinstance(result, dict) and result.get("error"):
        print(output, file=sys.stderr)


if __name__ == "__main__":
    main()
