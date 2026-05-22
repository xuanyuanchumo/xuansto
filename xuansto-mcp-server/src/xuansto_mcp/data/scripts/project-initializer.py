#!/usr/bin/env python3
"""项目初始化器 - 创建基础项目结构与配置

创建 .knowledge/ 目录、.skill-config.yaml、.editorconfig 等基础配置，
自动检测项目类型并生成对应的项目结构。

用法:
    python project-initializer.py [--type web] [--skip-kb]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="项目初始化器 - 创建基础项目结构与配置"
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["web", "desktop", "cross-platform", "auto"],
        default="auto",
        help="项目类型: web, desktop, cross-platform, auto (默认: auto)",
    )
    parser.add_argument(
        "--skip-kb",
        action="store_true",
        help="跳过知识库初始化",
    )
    return parser.parse_args()


def detect_project_type() -> str:
    cwd = Path(".")
    pkg_path = cwd / "package.json"
    if pkg_path.exists():
        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "electron" in deps or "tauri" in deps:
                return "desktop"
            if "react-native" in deps or "flutter" in deps:
                return "cross-platform"
        except (json.JSONDecodeError, OSError):
            pass
    return "web"


def create_knowledge_dirs(base: Path) -> dict:
    dirs = [
        "general",
        "workspace",
        "experience",
        "experience/decisions",
        "experience/errors",
        "experience/patterns",
        "experience/integration",
        "experience/performance",
        "experience/security",
        "experience/desktop",
        "backup",
        "backup/full",
        "backup/incremental",
        "backup/snapshot",
        "index",
    ]
    created = []
    existing = []
    for d in dirs:
        dir_path = base / d
        if dir_path.exists():
            existing.append(d)
        else:
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(d)

    gitkeep_dirs = ["backup/full", "backup/incremental", "backup/snapshot", "index"]
    for d in gitkeep_dirs:
        gitkeep = base / d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    return {"created": created, "existing": existing}


def create_skill_config(base: Path, project_type: str) -> dict:
    config_path = base / ".skill-config.yaml"
    if config_path.exists():
        return {"status": "SKIP", "details": f"配置文件已存在: {config_path}"}

    config_content = f"""project:
  name: auto-detected
  type: {project_type}
  language: auto-detect
  framework: auto-detect

knowledge:
  enabled: true
  backend: sqlite+chroma
  path: .knowledge/

quality:
  gates_enabled: true
  block_on_failure: true

agents:
  default_team: full
  max_parallel: 5
"""
    try:
        config_path.write_text(config_content, encoding="utf-8")
        return {"status": "PASS", "details": f"已创建: {config_path}"}
    except OSError as e:
        return {"status": "FAIL", "details": f"创建失败: {e}"}


def create_editorconfig(base: Path) -> dict:
    ec_path = base / ".editorconfig"
    if ec_path.exists():
        return {"status": "SKIP", "details": f"编辑器配置已存在: {ec_path}"}

    content = """root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 2

[*.py]
indent_size = 4

[*.md]
trim_trailing_whitespace = false
"""
    try:
        ec_path.write_text(content, encoding="utf-8")
        return {"status": "PASS", "details": f"已创建: {ec_path}"}
    except OSError as e:
        return {"status": "FAIL", "details": f"创建失败: {e}"}


def main():
    args = parse_args()

    project_type = args.type
    if project_type == "auto":
        project_type = detect_project_type()

    print(f"\n{'='*50}")
    print("项目初始化器")
    print(f"{'='*50}")
    print(f"项目类型: {project_type}")
    print(f"跳过知识库: {'是' if args.skip_kb else '否'}")

    results = []

    if not args.skip_kb:
        kb_base = Path(".") / ".knowledge"
        print(f"\n创建知识库目录: {kb_base}")
        kb_result = create_knowledge_dirs(kb_base)
        print(f"  新建: {len(kb_result['created'])} 个目录")
        print(f"  已有: {len(kb_result['existing'])} 个目录")
        results.append({"name": "知识库目录", "status": "PASS", "details": f"新建{len(kb_result['created'])}个，已有{len(kb_result['existing'])}个"})
    else:
        results.append({"name": "知识库目录", "status": "SKIP", "details": "已跳过"})

    print(f"\n创建技能配置文件...")
    config_result = create_skill_config(Path("."), project_type)
    print(f"  {config_result['status']}: {config_result['details']}")
    results.append({"name": "技能配置", **config_result})

    print(f"\n创建编辑器配置文件...")
    ec_result = create_editorconfig(Path("."))
    print(f"  {ec_result['status']}: {ec_result['details']}")
    results.append({"name": "编辑器配置", **ec_result})

    has_fail = any(r["status"] == "FAIL" for r in results)
    overall = "FAIL" if has_fail else "PASS"

    print(f"\n{'='*50}")
    print(f"初始化结果: {overall}")
    for r in results:
        icon = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘"}.get(r["status"], "?")
        print(f"  [{icon}] {r['name']}: {r['details']}")
    print(f"{'='*50}")

    if has_fail:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
