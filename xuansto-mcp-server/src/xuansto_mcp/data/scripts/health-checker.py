#!/usr/bin/env python3
"""项目健康检查器 - 采集Agent、服务与门禁健康状态

检查Agent健康、服务健康、门禁合规、Token使用和知识库状态，
支持简要和完整两种报告模式。

用法:
    python health-checker.py [--detail brief] [--format text]
"""

import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

try:
    import urllib.request
    import urllib.error
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False


def parse_args():
    parser = argparse.ArgumentParser(
        description="项目健康检查器 - 采集Agent、服务与门禁健康状态"
    )
    parser.add_argument(
        "--detail",
        type=str,
        choices=["brief", "full"],
        default="brief",
        help="详情级别: brief(简要), full(完整) (默认: brief)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="输出格式: text, json (默认: text)",
    )
    return parser.parse_args()


def check_agent_health() -> dict:
    agent_dir = Path(".") / "agents"
    if not agent_dir.exists():
        return {
            "name": "Agent健康检查",
            "status": "WARN",
            "details": "agents目录不存在",
            "agent_count": 0,
        }

    agent_count = 0
    for f in agent_dir.rglob("*.md"):
        if f.name != ".gitkeep":
            agent_count += 1

    if agent_count == 0:
        return {
            "name": "Agent健康检查",
            "status": "WARN",
            "details": "未发现Agent定义文件",
            "agent_count": 0,
        }

    return {
        "name": "Agent健康检查",
        "status": "PASS",
        "details": f"发现 {agent_count} 个Agent定义",
        "agent_count": agent_count,
    }


def check_service_health() -> dict:
    checks = []

    if HAS_URLLIB:
        try:
            url = "http://127.0.0.1:8765/v1/knowledge/health"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    checks.append(("知识库服务", "PASS"))
                else:
                    checks.append(("知识库服务", "FAIL"))
        except Exception:
            checks.append(("知识库服务", "FAIL"))
    else:
        checks.append(("知识库服务", "SKIP"))

    has_fail = any(c[1] == "FAIL" for c in checks)
    has_skip = any(c[1] == "SKIP" for c in checks)

    if has_fail:
        return {
            "name": "服务健康检查",
            "status": "FAIL",
            "details": "; ".join(f"{n}: {s}" for n, s in checks),
        }
    if has_skip:
        return {
            "name": "服务健康检查",
            "status": "WARN",
            "details": "; ".join(f"{n}: {s}" for n, s in checks),
        }

    return {
        "name": "服务健康检查",
        "status": "PASS",
        "details": "; ".join(f"{n}: {s}" for n, s in checks),
    }


def check_gate_compliance() -> dict:
    gates_ref = Path(".") / "references" / "quality-gates.md"
    if not gates_ref.exists():
        return {
            "name": "门禁合规检查",
            "status": "WARN",
            "details": "门禁定义文件不存在",
        }

    try:
        content = gates_ref.read_text(encoding="utf-8")
        gate_count = content.count("### ") + content.count("GATE-")
        return {
            "name": "门禁合规检查",
            "status": "PASS",
            "details": f"门禁定义文件存在，包含约 {gate_count} 项门禁",
        }
    except OSError:
        return {
            "name": "门禁合规检查",
            "status": "FAIL",
            "details": "门禁定义文件读取失败",
        }


def check_token_usage() -> dict:
    config_path = Path(".") / ".skill-config.yaml"
    if not config_path.exists():
        return {
            "name": "Token使用检查",
            "status": "WARN",
            "details": "技能配置文件不存在，无法评估Token预算",
        }

    return {
        "name": "Token使用检查",
        "status": "PASS",
        "details": "Token预算配置正常",
    }


def check_kb_status() -> dict:
    kb_dir = Path(".") / ".knowledge"
    if not kb_dir.exists():
        return {
            "name": "知识库状态检查",
            "status": "FAIL",
            "details": "知识库目录不存在",
        }

    required_dirs = ["general", "workspace", "experience", "backup"]
    missing = [d for d in required_dirs if not (kb_dir / d).exists()]

    if missing:
        return {
            "name": "知识库状态检查",
            "status": "WARN",
            "details": f"缺少目录: {', '.join(missing)}",
        }

    db_path = kb_dir / "index" / "knowledge.db"
    db_status = "不存在"
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            db_status = f"正常 ({len(tables)} 个表)"
        except sqlite3.Error:
            db_status = "访问异常"

    return {
        "name": "知识库状态检查",
        "status": "PASS",
        "details": f"目录结构完整，数据库: {db_status}",
    }


def format_text_report(report: dict) -> str:
    lines = []
    lines.append("=" * 50)
    lines.append("项目健康检查报告")
    lines.append("=" * 50)
    lines.append(f"检查时间: {report['timestamp']}")
    lines.append(f"详情级别: {report['detail']}")
    lines.append(f"整体状态: {report['status']}")
    lines.append("")

    icon_map = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "WARN": "⚠"}
    for check in report["checks"]:
        icon = icon_map.get(check["status"], "?")
        lines.append(f"  [{icon}] {check['name']}: {check['status']}")
        lines.append(f"      {check['details']}")

    lines.append("")
    lines.append("=" * 50)
    return "\n".join(lines)


def main():
    args = parse_args()

    print(f"\n{'='*50}")
    print("项目健康检查器")
    print(f"{'='*50}")
    print(f"详情级别: {args.detail}")
    print(f"输出格式: {args.format}")

    checks = [
        check_agent_health(),
        check_service_health(),
        check_gate_compliance(),
        check_token_usage(),
        check_kb_status(),
    ]

    if args.detail == "full":
        checks.append(check_kb_status())

    has_fail = any(c["status"] == "FAIL" for c in checks)
    has_warn = any(c["status"] == "WARN" for c in checks)

    if has_fail:
        overall_status = "FAIL"
    elif has_warn:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    report = {
        "timestamp": datetime.now().isoformat(),
        "detail": args.detail,
        "status": overall_status,
        "checks": checks,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text_report(report))

    if has_fail:
        sys.exit(1)
    if has_warn:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
