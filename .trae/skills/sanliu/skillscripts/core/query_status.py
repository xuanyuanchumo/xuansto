#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态查询脚本

查询系统状态信息，包括：
- 技能调用详情
- 调用树
- Agent 列表
- 仪表盘统计

使用示例:
    python query_status.py --call-id 123      # 查询技能调用详情
    python query_status.py --tree 1           # 查询调用树
    python query_status.py --agents           # 查询 Agent 列表
    python query_status.py --dashboard        # 查询仪表盘统计
    python query_status.py --json             # JSON 格式输出

退出码:
    0 - 成功
    1 - 错误
"""

import argparse
import sys
import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from skillscripts.utils.script_utils import (
    ScriptBase, ScriptResult, ExitCode, create_result
)

import requests


@dataclass
class QueryResult:
    query_type: str
    data: Any = None
    api_url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_type": self.query_type,
            "data": self.data,
            "api_url": self.api_url
        }


class QueryStatusScript(ScriptBase):
    DEFAULT_DESCRIPTION = "状态查询脚本"
    DEFAULT_EPILOG = """
示例:
  python query_status.py --call-id 123      # 查询技能调用详情
  python query_status.py --tree 1           # 查询调用树
  python query_status.py --agents           # 查询 Agent 列表
  python query_status.py --dashboard        # 查询仪表盘统计
  python query_status.py --json             # JSON 格式输出

退出码:
  0 - 成功
  1 - 错误
"""
    
    def _add_arguments(self):
        self.parser.add_argument(
            "--call-id",
            type=int,
            help="查询指定技能调用ID的详情"
        )
        self.parser.add_argument(
            "--tree",
            type=int,
            help="查询指定根ID的调用树"
        )
        self.parser.add_argument(
            "--agents",
            action="store_true",
            help="查询 Agent 列表"
        )
        self.parser.add_argument(
            "--dashboard",
            action="store_true",
            help="查询仪表盘统计"
        )
        self.parser.add_argument(
            "--status",
            type=str,
            help="按状态过滤 Agent"
        )
        self.parser.add_argument(
            "--department",
            type=str,
            help="按部门过滤 Agent"
        )
        self.parser.add_argument(
            "--api-base",
            type=str,
            default=os.getenv("VISUAL_API_BASE", "http://localhost:8000/api"),
            help="API 基础 URL"
        )
    
    def query_skill_call(self, call_id: int) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.get(f"{self.args.api_base}/skill_calls/{call_id}", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"查询技能调用失败: {e}")
            return None
    
    def query_call_tree(self, root_id: int) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.get(f"{self.args.api_base}/skill_calls/tree/{root_id}", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"查询调用树失败: {e}")
            return None
    
    def query_agents(self, status: str = None, department: str = None) -> List[Dict[str, Any]]:
        params = {}
        if status:
            params["status"] = status
        if department:
            params["department"] = department
        
        try:
            resp = requests.get(f"{self.args.api_base}/agents", params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"查询 Agent 列表失败: {e}")
            return []
    
    def query_dashboard(self) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.get(f"{self.args.api_base}/../dashboard/stats", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"查询仪表盘失败: {e}")
            return None
    
    def run(self) -> int:
        errors: List[str] = []
        query_result = QueryResult(query_type="unknown")
        
        if self.args.call_id:
            query_result.query_type = "skill_call"
            query_result.api_url = f"{self.args.api_base}/skill_calls/{self.args.call_id}"
            data = self.query_skill_call(self.args.call_id)
            if data:
                query_result.data = data
                message = f"技能调用 {self.args.call_id} 查询成功"
            else:
                errors.append(f"无法获取技能调用 {self.args.call_id}")
                message = f"技能调用 {self.args.call_id} 查询失败"
        
        elif self.args.tree:
            query_result.query_type = "call_tree"
            query_result.api_url = f"{self.args.api_base}/skill_calls/tree/{self.args.tree}"
            data = self.query_call_tree(self.args.tree)
            if data:
                query_result.data = data
                message = f"调用树 {self.args.tree} 查询成功"
            else:
                errors.append(f"无法获取调用树 {self.args.tree}")
                message = f"调用树 {self.args.tree} 查询失败"
        
        elif self.args.agents:
            query_result.query_type = "agents"
            query_result.api_url = f"{self.args.api_base}/agents"
            data = self.query_agents(self.args.status, self.args.department)
            query_result.data = data
            message = f"查询到 {len(data)} 个 Agent"
        
        elif self.args.dashboard:
            query_result.query_type = "dashboard"
            query_result.api_url = f"{self.args.api_base}/../dashboard/stats"
            data = self.query_dashboard()
            if data:
                query_result.data = data
                message = "仪表盘统计查询成功"
            else:
                errors.append("无法获取仪表盘统计")
                message = "仪表盘统计查询失败"
        
        else:
            self.parser.print_help()
            return ExitCode.EXIT_CODE_ERROR.value
        
        success = len(errors) == 0
        
        result = create_result(
            success=success,
            message=message,
            data=query_result,
            errors=errors,
            duration_ms=self.get_duration_ms()
        )
        
        if self.args.json:
            self.output_json(result)
        elif self.args.markdown:
            self.output_markdown(result)
        else:
            self.output_console(result)
            if query_result.data:
                print("\n数据:")
                print(json.dumps(query_result.data, indent=2, ensure_ascii=False))
        
        return ExitCode.EXIT_CODE_SUCCESS.value if success else ExitCode.EXIT_CODE_ERROR.value


def main():
    script = QueryStatusScript()
    return script.execute()


if __name__ == "__main__":
    sys.exit(main())
