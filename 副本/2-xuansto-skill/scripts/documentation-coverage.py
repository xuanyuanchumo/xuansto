#!/usr/bin/env python3
"""
文档覆盖率检查脚本
功能：检查项目文档的存在性和完整性，生成覆盖率报告
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


DOC_DEFINITIONS = {
    "prd": {
        "label": "产品需求文档",
        "search_paths": [
            "docs/product/prd.md",
            "docs/product/requirements.md",
            "docs/prd.md",
            "docs/requirements.md",
        ],
        "key_sections": ["功能需求", "非功能需求", "用户故事", "验收标准"],
        "is_multi_file": False,
    },
    "adr": {
        "label": "架构决策记录",
        "search_paths": [
            "docs/technical/architecture",
            "docs/architecture",
            "docs/adr",
        ],
        "file_pattern": "adr-*.md",
        "key_sections": ["背景", "决策", "后果"],
        "is_multi_file": True,
    },
    "api": {
        "label": "API文档",
        "search_paths": [
            "docs/technical/api/openapi.yaml",
            "docs/technical/api/openapi.yml",
            "docs/technical/api/swagger.yaml",
            "docs/api/openapi.yaml",
            "docs/api/openapi.yml",
        ],
        "key_sections": ["paths", "components", "info"],
        "is_multi_file": False,
        "is_yaml": True,
    },
    "user-manual": {
        "label": "用户手册",
        "search_paths": [
            "docs/user/user-manual.md",
            "docs/user-guide.md",
            "docs/user/manual.md",
            "docs/manual.md",
        ],
        "key_sections": ["快速开始", "安装", "使用说明", "常见问题"],
        "is_multi_file": False,
    },
    "design-system": {
        "label": "设计系统文档",
        "search_paths": [
            "docs/design/design-system.md",
            "docs/design-system.md",
            "docs/design/tokens.md",
        ],
        "key_sections": ["颜色", "字体", "间距", "组件"],
        "is_multi_file": False,
    },
    "ipc-contract": {
        "label": "IPC通道文档",
        "search_paths": [
            "docs/technical/desktop/ipc-channels.md",
            "docs/desktop/ipc-channels.md",
            "docs/technical/ipc-channels.md",
        ],
        "key_sections": ["通道列表", "消息格式", "安全策略"],
        "is_multi_file": False,
    },
    "security-guidelines": {
        "label": "安全指南",
        "search_paths": [
            "references/security-guidelines.md",
            "docs/security-guidelines.md",
            "docs/security/guidelines.md",
            "docs/references/security-guidelines.md",
        ],
        "key_sections": ["认证", "授权", "数据保护", "漏洞防护"],
        "is_multi_file": False,
    },
    "test-guidelines": {
        "label": "测试指南",
        "search_paths": [
            "references/test-guidelines.md",
            "docs/test-guidelines.md",
            "docs/testing/guidelines.md",
            "docs/references/test-guidelines.md",
        ],
        "key_sections": ["单元测试", "集成测试", "E2E测试", "覆盖率要求"],
        "is_multi_file": False,
    },
}


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="文档覆盖率检查脚本 - 检查项目文档的存在性和完整性"
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default=".",
        help="项目根目录（默认：当前目录）",
    )
    parser.add_argument(
        "--required-docs",
        type=str,
        default="prd,adr,api,user-manual,design-system",
        help="需要检查的文档类型，逗号分隔（默认：prd,adr,api,user-manual,design-system）",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "text"],
        default="json",
        help="输出格式（默认：json）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出文件路径（默认：标准输出）",
    )
    return parser.parse_args()


def find_doc_file(project_dir: Path, doc_type: str, definition: dict):
    """查找文档文件或目录"""
    if definition.get("is_multi_file"):
        for search_path in definition["search_paths"]:
            dir_path = project_dir / search_path
            if dir_path.is_dir():
                pattern = definition.get("file_pattern", "*.md")
                matched_files = sorted(dir_path.glob(pattern))
                if matched_files:
                    return str(dir_path.relative_to(project_dir)), matched_files
        return None, []

    for search_path in definition["search_paths"]:
        file_path = project_dir / search_path
        if file_path.is_file():
            return str(file_path.relative_to(project_dir)), [file_path]
    return None, []


def read_file_content(file_path: Path) -> str:
    """读取文件内容"""
    try:
        return file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def check_yaml_sections(content: str, key_sections: list) -> list:
    """检查YAML文件中的关键节"""
    missing = []
    for section in key_sections:
        if f"{section}:" not in content:
            missing.append(section)
    return missing


def check_markdown_sections(content: str, key_sections: list) -> list:
    """检查Markdown文件中的关键章节"""
    missing = []
    for section in key_sections:
        found = False
        for prefix in ["## ", "### ", "# ", "- "]:
            if prefix + section in content:
                found = True
                break
        if not found and section in content:
            found = True
        if not found:
            missing.append(section)
    return missing


def check_completeness(file_path: Path, definition: dict) -> tuple:
    """检查文档完整性，返回(完整度, 缺失章节)"""
    content = read_file_content(file_path)
    if not content.strip():
        return 0.0, list(definition["key_sections"])

    lines = content.strip().split("\n")
    non_header_lines = [
        line
        for line in lines
        if line.strip() and not line.strip().startswith("#") and not line.strip() == "---"
    ]
    if not non_header_lines:
        return 0.0, list(definition["key_sections"])

    key_sections = definition.get("key_sections", [])
    if not key_sections:
        return 1.0, []

    is_yaml = definition.get("is_yaml", False)
    if is_yaml:
        missing = check_yaml_sections(content, key_sections)
    else:
        missing = check_markdown_sections(content, key_sections)

    if not missing:
        return 1.0, []

    completeness = (len(key_sections) - len(missing)) / len(key_sections)
    return round(completeness, 2), missing


def check_single_doc(project_dir: Path, doc_type: str, definition: dict) -> dict:
    """检查单个文档类型的存在性和完整性"""
    rel_path, files = find_doc_file(project_dir, doc_type, definition)

    if not rel_path:
        first_suggestion = definition["search_paths"][0]
        return {
            "type": doc_type,
            "status": "missing",
            "path": None,
            "suggestion": f"Create {first_suggestion}",
        }

    if definition.get("is_multi_file"):
        total_completeness = 0.0
        all_missing = []
        valid_count = 0

        for f in files:
            comp, missing = check_completeness(f, definition)
            total_completeness += comp
            all_missing.extend(missing)
            valid_count += 1

        avg_completeness = round(total_completeness / valid_count, 2) if valid_count else 0.0
        unique_missing = list(dict.fromkeys(all_missing))

        if avg_completeness < 1.0:
            return {
                "type": doc_type,
                "status": "incomplete",
                "path": rel_path,
                "count": len(files),
                "completeness": avg_completeness,
                "missing_sections": unique_missing,
            }

        return {
            "type": doc_type,
            "status": "present",
            "path": rel_path,
            "count": len(files),
            "completeness": 1.0,
        }

    file_path = files[0]
    completeness, missing_sections = check_completeness(file_path, definition)

    if completeness < 1.0:
        return {
            "type": doc_type,
            "status": "incomplete",
            "path": rel_path,
            "completeness": completeness,
            "missing_sections": missing_sections,
        }

    return {
        "type": doc_type,
        "status": "present",
        "path": rel_path,
        "completeness": 1.0,
    }


def generate_text_report(result: dict) -> str:
    """生成文本格式报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("文档覆盖率检查报告")
    lines.append("=" * 60)
    lines.append(f"项目目录: {result['project_dir']}")
    lines.append(f"检查时间: {result['timestamp']}")
    lines.append("")

    s = result["summary"]
    lines.append(f"文档类型总数: {s['total_doc_types']}")
    lines.append(f"完整: {s['present']}  缺失: {s['missing']}  不完整: {s['incomplete']}")
    lines.append(f"覆盖率: {s['coverage_rate']:.1%}")
    lines.append("")
    lines.append("-" * 60)

    for doc in result["documents"]:
        status_label = {"present": "✓ 完整", "incomplete": "△ 不完整", "missing": "✗ 缺失"}
        label = status_label.get(doc["status"], doc["status"])
        lines.append(f"[{label}] {doc['type']}")

        if doc["status"] == "missing":
            lines.append(f"  建议: {doc['suggestion']}")
        else:
            lines.append(f"  路径: {doc['path']}")
            comp = doc.get("completeness", 0)
            lines.append(f"  完整度: {comp:.0%}")
            if "count" in doc:
                lines.append(f"  文件数: {doc['count']}")
            missing = doc.get("missing_sections", [])
            if missing:
                lines.append(f"  缺失章节: {', '.join(missing)}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    """主函数"""
    args = parse_args()

    try:
        project_dir = Path(args.project_dir).resolve()
    except Exception as e:
        print(f"无效的项目目录: {e}", file=sys.stderr)
        sys.exit(2)

    if not project_dir.is_dir():
        print(f"项目目录不存在: {project_dir}", file=sys.stderr)
        sys.exit(2)

    required_docs = [d.strip() for d in args.required_docs.split(",") if d.strip()]

    invalid_docs = [d for d in required_docs if d not in DOC_DEFINITIONS]
    if invalid_docs:
        valid_list = ", ".join(sorted(DOC_DEFINITIONS.keys()))
        print(f"不支持的文档类型: {', '.join(invalid_docs)}", file=sys.stderr)
        print(f"支持的类型: {valid_list}", file=sys.stderr)
        sys.exit(2)

    documents = []
    present_count = 0
    missing_count = 0
    incomplete_count = 0

    for doc_type in required_docs:
        definition = DOC_DEFINITIONS[doc_type]
        doc_result = check_single_doc(project_dir, doc_type, definition)
        documents.append(doc_result)

        if doc_result["status"] == "present":
            present_count += 1
        elif doc_result["status"] == "incomplete":
            incomplete_count += 1
        else:
            missing_count += 1

    total = len(required_docs)
    coverage_rate = round(present_count / total, 3) if total > 0 else 0.0

    result = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project_dir": args.project_dir,
        "summary": {
            "total_doc_types": total,
            "present": present_count,
            "missing": missing_count,
            "incomplete": incomplete_count,
            "coverage_rate": coverage_rate,
        },
        "documents": documents,
    }

    if args.format == "json":
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = generate_text_report(result)

    if args.output:
        try:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output, encoding="utf-8")
        except OSError as e:
            print(f"无法写入输出文件: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        print(output)

    if missing_count > 0 or incomplete_count > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
