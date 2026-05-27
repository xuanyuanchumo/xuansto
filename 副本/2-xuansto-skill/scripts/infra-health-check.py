#!/usr/bin/env python3
"""基础设施健康检查 - INFRA-HEALTH门禁健康检查脚本

检查知识库服务健康端点、数据库完整性、目录结构、配置文件和工具链可用性。

用法:
    python infra-health-check.py [--host 127.0.0.1] [--port 8765] [--timeout 5] [--format json|text]
"""

import argparse
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

try:
    import urllib.request
    import urllib.error
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

KNOWLEDGE_DIR = ".knowledge"
REQUIRED_SUBDIRS = ["general", "workspace", "experience", "backup"]
REQUIRED_CONFIGS = ["config.yaml", "platform-config.yaml"]
TOOLCHAIN_COMMANDS = ["python3", "node", "pwsh"]


def check_knowledge_service_health(host: str, port: int, timeout: int) -> dict:
    if not HAS_URLLIB:
        return {"name": "知识服务健康检查", "status": "SKIP", "details": "urllib不可用"}

    url = f"http://{host}:{port}/v1/knowledge/health"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status_code = resp.status
            body = resp.read().decode("utf-8")
            if status_code == 200:
                try:
                    data = json.loads(body)
                    return {
                        "name": "知识服务健康检查",
                        "status": "PASS",
                        "details": f"健康端点正常 (200)",
                        "data": data,
                    }
                except json.JSONDecodeError:
                    return {
                        "name": "知识服务健康检查",
                        "status": "PASS",
                        "details": "健康端点正常 (200)，非JSON响应",
                    }
            else:
                return {
                    "name": "知识服务健康检查",
                    "status": "FAIL",
                    "details": f"健康端点返回状态码 {status_code}",
                }
    except urllib.error.URLError as e:
        return {
            "name": "知识服务健康检查",
            "status": "FAIL",
            "details": f"健康端点不可达: {e.reason}",
        }
    except Exception as e:
        return {
            "name": "知识服务健康检查",
            "status": "FAIL",
            "details": f"健康检查异常: {str(e)}",
        }


def check_knowledge_db_integrity(knowledge_dir: str) -> dict:
    db_path = Path(knowledge_dir) / "index" / "knowledge.db"

    if not db_path.exists():
        return {
            "name": "知识数据库完整性",
            "status": "FAIL",
            "details": f"数据库文件不存在: {db_path}",
        }

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            conn.close()
            return {
                "name": "知识数据库完整性",
                "status": "FAIL",
                "details": "数据库无任何表",
            }

        integrity_result = cursor.execute("PRAGMA integrity_check").fetchone()
        conn.close()

        if integrity_result[0] == "ok":
            return {
                "name": "知识数据库完整性",
                "status": "PASS",
                "details": f"数据库完整性正常，包含 {len(tables)} 个表",
                "tables": tables,
            }
        else:
            return {
                "name": "知识数据库完整性",
                "status": "FAIL",
                "details": f"数据库完整性检查失败: {integrity_result[0]}",
            }
    except sqlite3.Error as e:
        return {
            "name": "知识数据库完整性",
            "status": "FAIL",
            "details": f"数据库访问异常: {str(e)}",
        }


def check_directory_structure(knowledge_dir: str) -> dict:
    base = Path(knowledge_dir)
    missing = []
    existing = []

    for subdir in REQUIRED_SUBDIRS:
        dir_path = base / subdir
        if dir_path.is_dir():
            existing.append(subdir)
        else:
            missing.append(subdir)

    if missing:
        return {
            "name": "目录结构完整性",
            "status": "FAIL",
            "details": f"缺少必要目录: {', '.join(missing)}",
            "existing": existing,
            "missing": missing,
        }

    return {
        "name": "目录结构完整性",
        "status": "PASS",
        "details": f"所有必要目录均存在: {', '.join(existing)}",
        "existing": existing,
    }


def check_config_files(knowledge_dir: str) -> dict:
    base = Path(knowledge_dir)
    missing = []
    invalid = []
    found = []

    for config_name in REQUIRED_CONFIGS:
        config_path = base / config_name
        if not config_path.exists():
            missing.append(config_name)
            continue

        try:
            content = config_path.read_text(encoding="utf-8")
            if not content.strip():
                invalid.append(config_name)
            else:
                found.append(config_name)
        except Exception:
            invalid.append(config_name)

    if missing:
        return {
            "name": "配置文件检查",
            "status": "FAIL",
            "details": f"缺少配置文件: {', '.join(missing)}",
            "found": found,
            "missing": missing,
            "invalid": invalid,
        }

    if invalid:
        return {
            "name": "配置文件检查",
            "status": "FAIL",
            "details": f"配置文件格式异常: {', '.join(invalid)}",
            "found": found,
            "missing": missing,
            "invalid": invalid,
        }

    return {
        "name": "配置文件检查",
        "status": "PASS",
        "details": f"所有配置文件存在且格式正常: {', '.join(found)}",
        "found": found,
    }


def check_toolchain_availability() -> dict:
    available = []
    unavailable = []

    for cmd in TOOLCHAIN_COMMANDS:
        if shutil.which(cmd):
            available.append(cmd)
        else:
            unavailable.append(cmd)

    if unavailable:
        return {
            "name": "脚本工具链可用性",
            "status": "WARN",
            "details": f"不可用工具: {', '.join(unavailable)}；可用工具: {', '.join(available)}",
            "available": available,
            "unavailable": unavailable,
        }

    return {
        "name": "脚本工具链可用性",
        "status": "PASS",
        "details": f"所有工具均可用: {', '.join(available)}",
        "available": available,
    }


def check_log_trace_fields(log_dir: str) -> dict:
    trace_fields = ["timestamp", "agent", "action", "phase"]
    log_file = os.path.join(log_dir, "knowledge-server.log")

    if not os.path.exists(log_file):
        log_files = []
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith(".log")]
        if not log_files:
            return {"name": "日志Trace字段", "status": "SKIP", "details": f"日志目录无日志文件: {log_dir}"}
        log_file = os.path.join(log_dir, log_files[0])

    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-100:]

        if not lines:
            return {"name": "日志Trace字段", "status": "SKIP", "details": "日志文件为空"}

        missing_fields = set()
        checked = 0
        for line in lines:
            try:
                entry = json.loads(line.strip())
                checked += 1
                for field in trace_fields:
                    if field not in entry:
                        missing_fields.add(field)
            except json.JSONDecodeError:
                continue

        if checked == 0:
            return {"name": "日志Trace字段", "status": "SKIP", "details": "未找到JSON格式日志条目"}

        if missing_fields:
            return {
                "name": "日志Trace字段",
                "status": "FAIL",
                "details": f"缺失Trace字段: {', '.join(missing_fields)}",
            }
        return {"name": "日志Trace字段", "status": "PASS", "details": f"所有Trace字段完整，已检查 {checked} 条日志"}

    except Exception as e:
        return {"name": "日志Trace字段", "status": "FAIL", "details": f"日志检查异常: {str(e)}"}


def format_text_report(report: dict) -> str:
    lines = []
    lines.append("=" * 50)
    lines.append("基础设施健康检查报告")
    lines.append("=" * 50)

    icon_map = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "WARN": "⚠"}

    for check in report["checks"]:
        icon = icon_map.get(check["status"], "?")
        lines.append(f"  [{icon}] {check['name']}: {check['status']} - {check['details']}")

    lines.append("=" * 50)
    lines.append(f"结果: {report['status']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="基础设施健康检查")
    parser.add_argument("--host", default="127.0.0.1", help="知识服务主机地址")
    parser.add_argument("--port", type=int, default=8765, help="知识服务端口")
    parser.add_argument("--timeout", type=int, default=5, help="请求超时时间（秒）")
    parser.add_argument("--log-dir", default=".skill-logs", help="日志目录路径")
    parser.add_argument(
        "--knowledge-dir",
        default=KNOWLEDGE_DIR,
        help=f"知识库根目录路径（默认: {KNOWLEDGE_DIR}）",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="输出格式: json 或 text（默认: json）",
    )
    args = parser.parse_args()

    checks = [
        check_knowledge_service_health(args.host, args.port, args.timeout),
        check_knowledge_db_integrity(args.knowledge_dir),
        check_directory_structure(args.knowledge_dir),
        check_config_files(args.knowledge_dir),
        check_toolchain_availability(),
        check_log_trace_fields(args.log_dir),
    ]

    has_fail = any(c["status"] == "FAIL" for c in checks)
    has_warn = any(c["status"] == "WARN" for c in checks)
    if has_fail:
        overall_status = "FAIL"
    elif has_warn:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    report = {
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
