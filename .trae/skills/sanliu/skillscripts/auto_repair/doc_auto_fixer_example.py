#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档自动修复器使用示例 - Document Auto Fixer Usage Example

展示如何使用文档自动修复器的各项功能
"""

from pathlib import Path
from doc_auto_fixer import DocumentAutoFixer


def example_basic_usage():
    """基本使用示例"""
    print("\n" + "=" * 80)
    print("示例 1: 基本使用")
    print("=" * 80)

    fixer = DocumentAutoFixer()

    file_path = "README.md"

    print(f"\n检测文档问题: {file_path}")
    issues = fixer.detect_issues(file_path)

    print(f"\n检测到 {len(issues)} 个问题:")
    for issue in issues[:5]:
        print(f"  - [{issue.issue_type.name}] 行 {issue.line_number}: {issue.message}")

    if len(issues) > 5:
        print(f"  ... 还有 {len(issues) - 5} 个问题")


def example_preview_fix():
    """预览修复示例"""
    print("\n" + "=" * 80)
    print("示例 2: 预览修复")
    print("=" * 80)

    fixer = DocumentAutoFixer()

    file_path = "README.md"

    print(f"\n预览修复结果: {file_path}")
    report = fixer.preview_fix(file_path)

    print(f"\n修复统计:")
    print(f"  检测问题: {report.total_issues}")
    print(f"  成功修复: {report.fixed_issues}")
    print(f"  失败修复: {report.failed_issues}")
    print(f"  跳过修复: {report.skipped_issues}")
    print(f"  执行时间: {report.execution_time_ms:.2f}ms")

    if report.diff:
        print(f"\n修改预览:")
        print(report.diff[:500])


def example_apply_fix():
    """应用修复示例"""
    print("\n" + "=" * 80)
    print("示例 3: 应用修复")
    print("=" * 80)

    fixer = DocumentAutoFixer()

    file_path = "README.md"

    print(f"\n应用修复: {file_path}")
    print("⚠️  警告: 这将修改文件内容")

    report = fixer.apply_fix(file_path)

    print(f"\n修复结果:")
    print(f"  状态: {'成功' if report.fixed_issues > 0 else '无变化'}")
    print(f"  修复问题: {report.fixed_issues}")

    print(f"\n修复详情:")
    for result in report.results[:3]:
        if result.status.value == "success":
            print(f"  ✓ {result.message}")


def example_batch_processing():
    """批量处理示例"""
    print("\n" + "=" * 80)
    print("示例 4: 批量处理")
    print("=" * 80)

    fixer = DocumentAutoFixer()

    file_paths = [
        "README.md",
        "docs/guide.md",
        "docs/api.md"
    ]

    existing_files = [f for f in file_paths if Path(f).exists()]

    if existing_files:
        print(f"\n批量处理 {len(existing_files)} 个文件:")
        for f in existing_files:
            print(f"  - {f}")

        reports = fixer.batch_fix(existing_files, auto_apply=False)

        total_issues = sum(r.total_issues for r in reports)
        total_fixed = sum(r.fixed_issues for r in reports)

        print(f"\n批量处理结果:")
        print(f"  处理文件: {len(reports)}")
        print(f"  总问题数: {total_issues}")
        print(f"  总修复数: {total_fixed}")
    else:
        print("\n没有找到要处理的文件")


def example_custom_project_root():
    """自定义项目根目录示例"""
    print("\n" + "=" * 80)
    print("示例 5: 自定义项目根目录")
    print("=" * 80)

    project_root = Path.cwd()
    print(f"\n项目根目录: {project_root}")

    fixer = DocumentAutoFixer(project_root=project_root)

    file_path = "README.md"

    print(f"\n检测文档问题: {file_path}")
    issues = fixer.detect_issues(file_path)

    print(f"\n检测到 {len(issues)} 个问题")


def example_generate_report():
    """生成报告示例"""
    print("\n" + "=" * 80)
    print("示例 6: 生成报告")
    print("=" * 80)

    fixer = DocumentAutoFixer()

    file_path = "README.md"

    print(f"\n生成修复报告: {file_path}")
    report = fixer.preview_fix(file_path)

    summary = fixer.generate_report_summary(report)
    print(summary)


def example_link_fixing():
    """链接修复示例"""
    print("\n" + "=" * 80)
    print("示例 7: 链接修复")
    print("=" * 80)

    from doc_auto_fixer import LinkFixer, DocIssueType

    fixer = LinkFixer()

    file_path = "README.md"

    if Path(file_path).exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"\n检测断裂链接: {file_path}")
        issues = fixer.detect_broken_links(content, file_path)

        broken_links = [i for i in issues if i.issue_type == DocIssueType.BROKEN_LINK]
        broken_images = [i for i in issues if i.issue_type == DocIssueType.BROKEN_IMAGE_LINK]

        print(f"\n断裂的链接: {len(broken_links)}")
        print(f"断裂的图片: {len(broken_images)}")

        for issue in issues[:5]:
            print(f"\n  问题: {issue.message}")
            print(f"  位置: 行 {issue.line_number}")
            if issue.suggested_fix:
                print(f"  建议: {issue.suggested_fix}")
    else:
        print(f"\n文件不存在: {file_path}")


def example_format_fixing():
    """格式修复示例"""
    print("\n" + "=" * 80)
    print("示例 8: 格式修复")
    print("=" * 80)

    from doc_auto_fixer import FormatFixer

    fixer = FormatFixer()

    file_path = "README.md"

    if Path(file_path).exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"\n检测格式问题: {file_path}")
        issues = fixer.detect_format_issues(content, file_path)

        print(f"\n检测到 {len(issues)} 个格式问题:")

        for issue in issues[:5]:
            print(f"\n  类型: {issue.issue_type.name}")
            print(f"  位置: 行 {issue.line_number}")
            print(f"  问题: {issue.message}")
            if issue.suggested_fix:
                print(f"  建议: {issue.suggested_fix[:50]}...")
    else:
        print(f"\n文件不存在: {file_path}")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("文档自动修复器使用示例")
    print("=" * 80)

    examples = [
        ("基本使用", example_basic_usage),
        ("预览修复", example_preview_fix),
        ("应用修复", example_apply_fix),
        ("批量处理", example_batch_processing),
        ("自定义项目根目录", example_custom_project_root),
        ("生成报告", example_generate_report),
        ("链接修复", example_link_fixing),
        ("格式修复", example_format_fixing),
    ]

    print("\n可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\n运行所有示例...")

    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n示例 '{name}' 执行失败: {e}")

    print("\n" + "=" * 80)
    print("示例运行完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
