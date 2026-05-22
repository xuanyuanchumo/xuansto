#!/usr/bin/env python3
"""
文档变更追踪模块 - Sanliu 技能

功能：
- 文档差异对比
- 变更历史记录
- 文档变更报告增强
- 版本索引管理

使用方法：
    python scripts/doc_change_tracker.py --compare v1.0.0 v1.1.0
    python scripts/doc_change_tracker.py --history --file README.md
    python scripts/doc_change_tracker.py --report --version v1.1.0
"""

import argparse
import difflib
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from path_config_manager import PathConfigManager


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('doc_change_tracker.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class ChangeType(Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


class DocType(Enum):
    API = "api"
    ARCHITECTURE = "architecture"
    TEST_REPORT = "test_report"
    CHANGELOG = "changelog"
    README = "readme"
    GUIDE = "guide"


@dataclass
class DocChange:
    file_path: str
    change_type: ChangeType
    old_content: str = ""
    new_content: str = ""
    diff: str = ""
    timestamp: Optional[datetime] = None
    author: str = ""
    description: str = ""
    lines_added: int = 0
    lines_removed: int = 0
    lines_modified: int = 0


@dataclass
class DocVersion:
    version: str
    timestamp: datetime
    changes: list[DocChange]
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass
class DiffResult:
    file_path: str
    has_changes: bool
    similarity: float
    changes: list[dict] = field(default_factory=list)
    unified_diff: str = ""


class DocDiffComparator:
    """文档差异对比器"""

    def __init__(self):
        pass

    def compare_files(self, old_content: str, new_content: str, file_path: str = "") -> DiffResult:
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        if old_lines == new_lines:
            return DiffResult(
                file_path=file_path,
                has_changes=False,
                similarity=1.0,
                changes=[],
                unified_diff=""
            )

        similarity = self._calculate_similarity(old_lines, new_lines)

        unified_diff = self._generate_unified_diff(old_lines, new_lines, file_path)
        changes = self._analyze_changes(old_lines, new_lines)

        return DiffResult(
            file_path=file_path,
            has_changes=True,
            similarity=similarity,
            changes=changes,
            unified_diff=unified_diff
        )

    def compare_directories(
        self,
        old_dir: Path,
        new_dir: Path,
        file_patterns: list[str] = None
    ) -> dict[str, DiffResult]:
        results = {}
        file_patterns = file_patterns or ["*.md", "*.json", "*.txt", "*.html"]

        old_files = set()
        new_files = set()

        for pattern in file_patterns:
            if old_dir.exists():
                old_files.update(str(f.relative_to(old_dir)) for f in old_dir.rglob(pattern))
            if new_dir.exists():
                new_files.update(str(f.relative_to(new_dir)) for f in new_dir.rglob(pattern))

        all_files = old_files | new_files

        for rel_path in all_files:
            old_file = old_dir / rel_path
            new_file = new_dir / rel_path

            old_content = ""
            new_content = ""

            if old_file.exists():
                try:
                    with open(old_file, 'r', encoding='utf-8') as f:
                        old_content = f.read()
                except Exception:
                    pass

            if new_file.exists():
                try:
                    with open(new_file, 'r', encoding='utf-8') as f:
                        new_content = f.read()
                except Exception:
                    pass

            diff_result = self.compare_files(old_content, new_content, rel_path)
            results[rel_path] = diff_result

        return results

    def _calculate_similarity(self, old_lines: list[str], new_lines: list[str]) -> float:
        if not old_lines and not new_lines:
            return 1.0
        if not old_lines or not new_lines:
            return 0.0

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        return matcher.ratio()

    def _generate_unified_diff(
        self,
        old_lines: list[str],
        new_lines: list[str],
        file_path: str
    ) -> str:
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=""
        )
        return "".join(diff)

    def _analyze_changes(self, old_lines: list[str], new_lines: list[str]) -> list[dict]:
        changes = []
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue

            change = {
                "type": tag,
                "old_start": i1 + 1,
                "old_end": i2,
                "new_start": j1 + 1,
                "new_end": j2,
                "old_content": "".join(old_lines[i1:i2]) if i1 < i2 else "",
                "new_content": "".join(new_lines[j1:j2]) if j1 < j2 else ""
            }
            changes.append(change)

        return changes


class DocChangeHistory:
    """文档变更历史记录器"""

    def __init__(self, history_file: Path = None):
        self.history_file = history_file or PathConfigManager(auto_detect=True).get_docs_path() / "change_history.json"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history: list[DocVersion] = []
        self._load_history()

    def _load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for ver_data in data.get("versions", []):
                    changes = []
                    for change_data in ver_data.get("changes", []):
                        changes.append(DocChange(
                            file_path=change_data['file_path'],
                            change_type=ChangeType(change_data['change_type']),
                            old_content=change_data.get('old_content', ''),
                            new_content=change_data.get('new_content', ''),
                            diff=change_data.get('diff', ''),
                            timestamp=datetime.fromisoformat(change_data['timestamp']) if change_data.get('timestamp') else None,
                            author=change_data.get('author', ''),
                            description=change_data.get('description', ''),
                            lines_added=change_data.get('lines_added', 0),
                            lines_removed=change_data.get('lines_removed', 0),
                            lines_modified=change_data.get('lines_modified', 0)
                        ))

                    self.history.append(DocVersion(
                        version=ver_data['version'],
                        timestamp=datetime.fromisoformat(ver_data['timestamp']),
                        changes=changes,
                        summary=ver_data.get('summary', {})
                    ))
            except Exception as e:
                logger.warning(f"加载变更历史失败: {e}")

    def _save_history(self):
        data = {"versions": []}
        for ver in self.history:
            ver_data = {
                "version": ver.version,
                "timestamp": ver.timestamp.isoformat(),
                "summary": ver.summary,
                "changes": []
            }
            for change in ver.changes:
                ver_data["changes"].append({
                    "file_path": change.file_path,
                    "change_type": change.change_type.value,
                    "old_content": change.old_content[:500] if change.old_content else "",
                    "new_content": change.new_content[:500] if change.new_content else "",
                    "diff": change.diff[:1000] if change.diff else "",
                    "timestamp": change.timestamp.isoformat() if change.timestamp else None,
                    "author": change.author,
                    "description": change.description,
                    "lines_added": change.lines_added,
                    "lines_removed": change.lines_removed,
                    "lines_modified": change.lines_modified
                })
            data["versions"].append(ver_data)

        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def record_change(
        self,
        version: str,
        file_path: str,
        change_type: ChangeType,
        old_content: str = "",
        new_content: str = "",
        description: str = ""
    ):
        comparator = DocDiffComparator()
        diff_result = comparator.compare_files(old_content, new_content, file_path)

        change = DocChange(
            file_path=file_path,
            change_type=change_type,
            old_content=old_content,
            new_content=new_content,
            diff=diff_result.unified_diff,
            timestamp=datetime.now(),
            description=description,
            lines_added=len([c for c in diff_result.changes if c['type'] in ('insert', 'replace')]),
            lines_removed=len([c for c in diff_result.changes if c['type'] in ('delete', 'replace')])
        )

        existing_version = next((v for v in self.history if v.version == version), None)
        if existing_version:
            existing_version.changes.append(change)
        else:
            doc_version = DocVersion(
                version=version,
                timestamp=datetime.now(),
                changes=[change]
            )
            self.history.append(doc_version)

        self._save_history()

    def record_version(self, version: str, changes: list[DocChange], summary: dict[str, Any] = None):
        doc_version = DocVersion(
            version=version,
            timestamp=datetime.now(),
            changes=changes,
            summary=summary or {}
        )
        self.history.append(doc_version)
        self._save_history()

    def get_version_changes(self, version: str) -> Optional[DocVersion]:
        return next((v for v in self.history if v.version == version), None)

    def get_file_history(self, file_path: str) -> list[DocChange]:
        changes = []
        for ver in self.history:
            for change in ver.changes:
                if change.file_path == file_path:
                    changes.append(change)
        return sorted(changes, key=lambda x: x.timestamp, reverse=True)

    def get_recent_changes(self, days: int = 30) -> list[DocChange]:
        cutoff = datetime.now() - timedelta(days=days)
        changes = []
        for ver in self.history:
            for change in ver.changes:
                if change.timestamp and change.timestamp >= cutoff:
                    changes.append(change)
        return sorted(changes, key=lambda x: x.timestamp, reverse=True)


class DocVersionIndexManager:
    """版本索引管理器"""

    def __init__(self, docs_dir: Path = None):
        self.docs_dir = docs_dir or PathConfigManager(auto_detect=True).get_docs_path()
        self.index_file = self.docs_dir / "version_index.json"
        self.index: dict[str, Any] = {}
        self._load_index()

    def _load_index(self):
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            except Exception:
                self.index = {"versions": {}, "current": None}

    def _save_index(self):
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)

    def add_version(
        self,
        version: str,
        doc_types: list[DocType],
        file_count: int,
        description: str = ""
    ):
        self.index["versions"][version] = {
            "created_at": datetime.now().isoformat(),
            "doc_types": [dt.value for dt in doc_types],
            "file_count": file_count,
            "description": description,
            "status": "active"
        }
        self.index["current"] = version
        self._save_index()

    def deprecate_version(self, version: str):
        if version in self.index["versions"]:
            self.index["versions"][version]["status"] = "deprecated"
            self.index["versions"][version]["deprecated_at"] = datetime.now().isoformat()
            self._save_index()

    def get_version_info(self, version: str) -> Optional[dict]:
        return self.index["versions"].get(version)

    def list_versions(self) -> list[dict]:
        versions = []
        for ver, info in self.index["versions"].items():
            versions.append({
                "version": ver,
                **info
            })
        return sorted(versions, key=lambda x: x["created_at"], reverse=True)

    def generate_index_report(self) -> dict[str, Any]:
        return {
            "total_versions": len(self.index["versions"]),
            "current_version": self.index.get("current"),
            "versions": self.list_versions(),
            "generated_at": datetime.now().isoformat()
        }


class DocChangeReportGenerator:
    """文档变更报告生成器"""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or PathConfigManager(auto_detect=True).get_docs_reports_path()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        version: str,
        changes: list[DocChange],
        diff_results: dict[str, DiffResult] = None
    ) -> dict[str, Any]:
        summary = self._calculate_summary(changes)

        report = {
            "metadata": {
                "version": version,
                "generated_at": datetime.now().isoformat(),
                "report_type": "doc_change_report"
            },
            "summary": summary,
            "changes": self._format_changes(changes),
            "diff_summary": self._format_diff_summary(diff_results) if diff_results else {},
            "recommendations": self._generate_recommendations(changes, summary)
        }

        return report

    def _calculate_summary(self, changes: list[DocChange]) -> dict[str, Any]:
        summary = {
            "total_changes": len(changes),
            "by_type": {ct.value: 0 for ct in ChangeType},
            "total_lines_added": 0,
            "total_lines_removed": 0,
            "files_changed": set()
        }

        for change in changes:
            summary["by_type"][change.change_type.value] += 1
            summary["total_lines_added"] += change.lines_added
            summary["total_lines_removed"] += change.lines_removed
            summary["files_changed"].add(change.file_path)

        summary["files_changed"] = len(summary["files_changed"])
        return summary

    def _format_changes(self, changes: list[DocChange]) -> list[dict]:
        return [
            {
                "file_path": change.file_path,
                "change_type": change.change_type.value,
                "timestamp": change.timestamp.isoformat() if change.timestamp else None,
                "description": change.description,
                "lines_added": change.lines_added,
                "lines_removed": change.lines_removed,
                "author": change.author
            }
            for change in changes
        ]

    def _format_diff_summary(self, diff_results: dict[str, DiffResult]) -> dict[str, Any]:
        return {
            "files_compared": len(diff_results),
            "files_with_changes": len([d for d in diff_results.values() if d.has_changes]),
            "avg_similarity": sum(d.similarity for d in diff_results.values()) / len(diff_results) if diff_results else 0,
            "details": [
                {
                    "file": path,
                    "has_changes": diff.has_changes,
                    "similarity": diff.similarity
                }
                for path, diff in diff_results.items()
            ]
        }

    def _generate_recommendations(self, changes: list[DocChange], summary: dict) -> list[str]:
        recommendations = []

        if summary["total_changes"] > 50:
            recommendations.append("变更数量较多，建议分批审核")

        if summary["by_type"]["deleted"] > 10:
            recommendations.append("删除文件较多，请确认是否需要更新相关引用")

        if summary["total_lines_removed"] > summary["total_lines_added"] * 2:
            recommendations.append("删除行数远多于新增行数，请确认是否为预期行为")

        return recommendations

    def save_report(self, report: dict[str, Any], filename: str = None) -> Path:
        filename = filename or f"doc_change_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = self.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"文档变更报告已保存: {output_path}")
        return output_path

    def generate_markdown_report(self, report: dict[str, Any]) -> str:
        md = f"""# 文档变更报告

**版本**: {report['metadata']['version']}
**生成时间**: {report['metadata']['generated_at']}

## 摘要

| 指标 | 数值 |
|------|------|
| 总变更数 | {report['summary']['total_changes']} |
| 变更文件数 | {report['summary']['files_changed']} |
| 新增行数 | {report['summary']['total_lines_added']} |
| 删除行数 | {report['summary']['total_lines_removed']} |

### 变更类型分布

"""
        for change_type, count in report['summary']['by_type'].items():
            md += f"- {change_type}: {count}\n"

        if report.get('recommendations'):
            md += "\n## 建议\n\n"
            for rec in report['recommendations']:
                md += f"- {rec}\n"

        md += "\n## 变更详情\n\n"
        for change in report['changes'][:50]:
            md += f"### {change['file_path']}\n\n"
            md += f"- 类型: {change['change_type']}\n"
            md += f"- 时间: {change['timestamp']}\n"
            if change['description']:
                md += f"- 描述: {change['description']}\n"
            md += "\n"

        return md


def main():
    parser = argparse.ArgumentParser(description="文档变更追踪模块")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    parser_compare = subparsers.add_parser("compare", help="对比版本差异")
    parser_compare.add_argument("old_version", help="旧版本号")
    parser_compare.add_argument("new_version", help="新版本号")
    parser_compare.add_argument("--docs-dir", type=Path, default=PathConfigManager(auto_detect=True).get_docs_path(), help="文档目录")

    parser_history = subparsers.add_parser("history", help="查看变更历史")
    parser_history.add_argument("--file", help="指定文件路径")
    parser_history.add_argument("--days", type=int, default=30, help="最近天数")

    parser_report = subparsers.add_parser("report", help="生成变更报告")
    parser_report.add_argument("--version", required=True, help="版本号")
    parser_report.add_argument("--format", choices=["json", "markdown"], default="json", help="报告格式")

    parser_index = subparsers.add_parser("index", help="版本索引管理")
    parser_index.add_argument("--list", action="store_true", help="列出所有版本")
    parser_index.add_argument("--add", metavar="VERSION", help="添加新版本")

    args = parser.parse_args()

    if args.command == "compare":
        docs_dir = args.docs_dir
        old_dir = docs_dir / "libs" / args.old_version
        new_dir = docs_dir / "libs" / args.new_version

        comparator = DocDiffComparator()
        results = comparator.compare_directories(old_dir, new_dir)

        print("\n" + "=" * 60)
        print(f"版本对比: {args.old_version} vs {args.new_version}")
        print("=" * 60)

        changed_files = [f for f, r in results.items() if r.has_changes]
        print(f"比较文件数: {len(results)}")
        print(f"有变化的文件: {len(changed_files)}")

        if changed_files:
            print("\n变更文件:")
            for file_path in changed_files[:20]:
                result = results[file_path]
                print(f"  - {file_path} (相似度: {result.similarity:.1%})")

    elif args.command == "history":
        history = DocChangeHistory()

        if args.file:
            changes = history.get_file_history(args.file)
            print("\n" + "=" * 60)
            print(f"文件变更历史: {args.file}")
            print("=" * 60)
            for change in changes[:20]:
                print(f"  [{change.timestamp.strftime('%Y-%m-%d')}] {change.change_type.value}: {change.description or '无描述'}")
        else:
            changes = history.get_recent_changes(args.days)
            print("\n" + "=" * 60)
            print(f"最近 {args.days} 天变更")
            print("=" * 60)
            print(f"总变更数: {len(changes)}")

    elif args.command == "report":
        history = DocChangeHistory()
        version_changes = history.get_version_changes(args.version)

        if not version_changes:
            print(f"未找到版本 {args.version} 的变更记录")
            return

        generator = DocChangeReportGenerator()
        report = generator.generate_report(args.version, version_changes.changes)

        if args.format == "markdown":
            md_content = generator.generate_markdown_report(report)
            output_path = generator.output_dir / f"doc_change_report_{args.version}.md"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
        else:
            output_path = generator.save_report(report)

        print("\n" + "=" * 60)
        print("文档变更报告")
        print("=" * 60)
        print(f"版本: {report['metadata']['version']}")
        print(f"总变更数: {report['summary']['total_changes']}")
        print(f"变更文件数: {report['summary']['files_changed']}")
        print(f"\n报告已保存: {output_path}")

    elif args.command == "index":
        manager = DocVersionIndexManager()

        if args.list:
            versions = manager.list_versions()
            print("\n" + "=" * 60)
            print("版本索引")
            print("=" * 60)
            for ver in versions:
                status = ver.get('status', 'active')
                print(f"  {ver['version']} - {ver['created_at'][:10]} - {status}")

        elif args.add:
            manager.add_version(args.add, [DocType.API], 0, "手动添加")
            print(f"版本 {args.add} 已添加到索引")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
