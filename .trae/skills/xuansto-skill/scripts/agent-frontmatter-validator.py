#!/usr/bin/env python3
"""
Agent Frontmatter验证脚本
功能：验证 agents/ 目录下所有Agent定义文件的YAML frontmatter是否符合规范
"""

import argparse
import json
import re
import sys
import os
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


TAILWIND_COLORS = {
    "blue", "green", "teal", "pink", "purple", "yellow",
    "red", "orange", "indigo", "cyan", "emerald",
    "amber", "rose", "fuchsia", "violet", "sky",
    "lime", "slate", "gray", "zinc", "neutral", "stone"
}

PASCAL_CASE_RE = re.compile(r'^[A-Z][a-zA-Z0-9]*$')

HEX_COLOR_RE = re.compile(r'^#[0-9A-Fa-f]{3,8}$')

KEBAB_CASE_RE = re.compile(r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$')

Kebab_FILENAME_RE = re.compile(r'^[a-z][a-z0-9]*(-[a-z0-9]+)*\.md$')

ZWJ = '\u200D'
VARIATION_SELECTORS = {'\uFE0F', '\uFE0E'}

SKIP_FILENAME_CHECK = {"agents/orchestrator/orchestrator.md"}

VALID_MODELS = {"fast", "standard", "deep"}

MAX_AGENT_LINES = 100


def parse_args():
    parser = argparse.ArgumentParser(
        description='Agent Frontmatter验证脚本 - 验证agents/目录下所有Agent的YAML frontmatter'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        default=False,
        help='以JSON格式输出结果'
    )
    return parser.parse_args()


def find_agent_files(agents_dir: Path):
    md_files = []
    for md_path in agents_dir.rglob("*.md"):
        if md_path.is_file():
            md_files.append(md_path)
    return md_files


def parse_frontmatter(file_path: Path):
    content = file_path.read_text(encoding='utf-8')
    if not content.startswith('---'):
        return None

    second_delim = content.find('---', 3)
    if second_delim == -1:
        return None

    frontmatter_text = content[3:second_delim].strip()
    if not frontmatter_text:
        return None

    if yaml is None:
        print("错误: 需要pyyaml模块，请安装: pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    try:
        return yaml.safe_load(frontmatter_text)
    except Exception as e:
        print(f"警告: YAML解析失败 [{file_path}]: {e}", file=sys.stderr)
        return None


def validate_emoji(value):
    if not isinstance(value, str):
        return False, "非字符串类型"

    emoji = value.strip()
    if not emoji:
        return False, "空字符串"

    if ZWJ in emoji:
        return False, "包含零宽连接符(ZWJ)，属于组合emoji"

    cleaned = ''.join(ch for ch in emoji if ch not in VARIATION_SELECTORS)

    if len(cleaned) < 1:
        return False, "去除变体选择器后为空"

    if len(cleaned) > 2:
        return False, f"多字符序列(len={len(cleaned)})，非单字符emoji"

    if all(ord(ch) < 128 for ch in cleaned):
        return False, "ASCII字符，非emoji"

    return True, ""


def validate_color(value):
    if not isinstance(value, str):
        return False, "非字符串类型"

    color = value.strip()

    if HEX_COLOR_RE.match(color):
        return True, ""

    if color in TAILWIND_COLORS:
        return True, ""

    return False, f"'{color}' 既非合法hex色值也非Tailwind色名"


def validate_services(value):
    if not isinstance(value, list):
        return False, "非列表类型"

    for item in value:
        if not isinstance(item, str):
            return False, f"列表元素非字符串: {item}"
        if not KEBAB_CASE_RE.match(item):
            return False, f"'{item}' 不符合kebab-case格式"

    return True, ""


def validate_description(value):
    if not isinstance(value, str):
        return False, "非字符串类型"

    if len(value) > 30:
        return False, f"长度 {len(value)} 字，超过30字限制"

    return True, ""


def validate_tools(value):
    if not isinstance(value, list):
        return False, "非列表类型"

    for item in value:
        if not isinstance(item, str):
            return False, f"列表元素非字符串: {item}"

    return True, ""


def validate_model(value):
    if not isinstance(value, str):
        return False, "非字符串类型"

    if value not in VALID_MODELS:
        return False, f"'{value}' 不在合法值 {sorted(VALID_MODELS)} 中"

    return True, ""


def validate_filename(rel_path: str):
    filename = os.path.basename(rel_path)

    if rel_path.replace('\\', '/') in SKIP_FILENAME_CHECK:
        return True, ""

    if not Kebab_FILENAME_RE.match(filename):
        return False, f"'{filename}' 不符合 kebab-case 命名规范"

    return True, ""


def validate_agent_file(file_path: Path, agents_dir: Path):
    failures = []

    rel_path = str(file_path.relative_to(agents_dir.parent)).replace('\\', '/')

    frontmatter = parse_frontmatter(file_path)
    if frontmatter is None:
        print(f"警告: 跳过文件（无有效frontmatter）: {rel_path}", file=sys.stderr)
        return failures, True

    if not isinstance(frontmatter, dict):
        print(f"警告: 跳过文件（frontmatter非字典）: {rel_path}", file=sys.stderr)
        return failures, True

    if 'name' in frontmatter:
        name_val = frontmatter['name']
        if not isinstance(name_val, str):
            failures.append({
                "file": rel_path,
                "field": "name",
                "value": str(name_val),
                "reason": "非字符串类型"
            })
        elif not PASCAL_CASE_RE.match(name_val):
            failures.append({
                "file": rel_path,
                "field": "name",
                "value": name_val,
                "reason": f"'{name_val}' 不符合PascalCase格式"
            })

    if 'emoji' in frontmatter:
        valid, reason = validate_emoji(frontmatter['emoji'])
        if not valid:
            failures.append({
                "file": rel_path,
                "field": "emoji",
                "value": str(frontmatter['emoji']),
                "reason": reason
            })

    if 'color' in frontmatter:
        valid, reason = validate_color(frontmatter['color'])
        if not valid:
            failures.append({
                "file": rel_path,
                "field": "color",
                "value": str(frontmatter['color']),
                "reason": reason
            })

    if 'services' in frontmatter:
        valid, reason = validate_services(frontmatter['services'])
        if not valid:
            failures.append({
                "file": rel_path,
                "field": "services",
                "value": str(frontmatter['services']),
                "reason": reason
            })

    if 'description' in frontmatter:
        valid, reason = validate_description(frontmatter['description'])
        if not valid:
            failures.append({
                "file": rel_path,
                "field": "description",
                "value": str(frontmatter['description']),
                "reason": reason
            })

    if 'tools' not in frontmatter:
        failures.append({
            "file": rel_path,
            "field": "tools",
            "value": "(缺失)",
            "reason": "tools字段必须存在"
        })
    else:
        valid, reason = validate_tools(frontmatter['tools'])
        if not valid:
            failures.append({
                "file": rel_path,
                "field": "tools",
                "value": str(frontmatter['tools']),
                "reason": reason
            })

    if 'model' not in frontmatter:
        failures.append({
            "file": rel_path,
            "field": "model",
            "value": "(缺失)",
            "reason": "model字段必须存在"
        })
    else:
        valid, reason = validate_model(frontmatter['model'])
        if not valid:
            failures.append({
                "file": rel_path,
                "field": "model",
                "value": str(frontmatter['model']),
                "reason": reason
            })

    content = file_path.read_text(encoding='utf-8')
    line_count = len(content.splitlines())
    if line_count > MAX_AGENT_LINES:
        failures.append({
            "file": rel_path,
            "field": "行数",
            "value": str(line_count),
            "reason": f"超过{MAX_AGENT_LINES}行限制(当前{line_count}行)"
        })

    filename_rel = rel_path
    valid, reason = validate_filename(filename_rel)
    if not valid:
        failures.append({
            "file": rel_path,
            "field": "文件名",
            "value": os.path.basename(rel_path),
            "reason": reason
        })

    skipped = False
    return failures, skipped


def main():
    args = parse_args()

    script_dir = Path(__file__).resolve().parent
    skill_root = script_dir.parent
    agents_dir = skill_root / "agents"

    if not agents_dir.is_dir():
        print(f"错误: agents目录不存在: {agents_dir}", file=sys.stderr)
        sys.exit(1)

    md_files = find_agent_files(agents_dir)
    total = len(md_files)
    all_failures = []

    for file_path in sorted(md_files):
        failures, skipped = validate_agent_file(file_path, agents_dir)
        if failures:
            all_failures.extend(failures)

    pass_count = total - len({f["file"] for f in all_failures})
    fail_count = len({f["file"] for f in all_failures})

    report = {
        "total": total,
        "pass": pass_count,
        "fail": fail_count,
        "failures": all_failures
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        if all_failures:
            for f in all_failures:
                print(f"[FAIL] {f['file']} - {f['field']}: {f['reason']} (value: {f['value']})")
        else:
            print(f"所有 {total} 个Agent文件验证通过")

    if all_failures:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
