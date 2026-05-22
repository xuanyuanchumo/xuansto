#!/usr/bin/env python3
"""
Agent 分配脚本
根据任务要求分配 Agent
"""
import argparse
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import requests

API_BASE = os.getenv("VISUAL_API_BASE", "http://localhost:8000/api")

def get_available_agents(skill=None, department=None):
    """获取可用 Agent 列表"""
    params = {"status": "idle"}
    if skill:
        params["skill"] = skill
    if department:
        params["department"] = department
    
    try:
        resp = requests.get(f"{API_BASE}/agents", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting agents: {e}", file=sys.stderr)
        return []

def assign_task(agent_id, task_id, task_description, call_id=None):
    """分配任务给 Agent"""
    payload = {
        "agent_id": agent_id,
        "task_id": task_id,
        "task_description": task_description,
        "skill_call_id": call_id
    }
    
    try:
        resp = requests.post(f"{API_BASE}/assignments", json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        print(f"Task assigned: Agent={agent_id}, Task={task_id}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error assigning task: {e}", file=sys.stderr)
        return None

def auto_assign(task_id, required_skill, task_description, call_id=None):
    """自动分配任务给最合适的 Agent"""
    agents = get_available_agents(skill=required_skill)
    
    if not agents:
        print("No available agents found", file=sys.stderr)
        return None
    
    # 选择负载最低的 Agent
    best_agent = min(agents, key=lambda a: a.get("current_load", 0))
    
    return assign_task(best_agent["id"], task_id, task_description, call_id)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assign tasks to agents")
    parser.add_argument("--task-id", type=int, help="Task ID")
    parser.add_argument("--agent-id", type=int, help="Agent ID (for manual assignment)")
    parser.add_argument("--role", type=str, help="Required role/skill")
    parser.add_argument("--task", type=str, required=True, help="Task description")
    parser.add_argument("--call-id", type=int, help="Related skill call ID")
    parser.add_argument("--auto", action="store_true", help="Auto-assign to best agent")
    
    args = parser.parse_args()
    
    if args.auto:
        result = auto_assign(args.task_id, args.role, args.task, args.call_id)
    elif args.agent_id:
        result = assign_task(args.agent_id, args.task_id, args.task, args.call_id)
    else:
        print("Either --agent-id or --auto must be specified", file=sys.stderr)
        sys.exit(1)
    
    if result:
        print(json.dumps(result, indent=2))
    else:
        sys.exit(1)
