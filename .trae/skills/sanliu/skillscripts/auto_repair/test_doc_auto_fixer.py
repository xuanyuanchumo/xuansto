#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档自动修复器测试 - Document Auto Fixer Test

测试文档自动修复器的各项功能：
- 链接检测和修复
- 格式问题检测和修复
- 修复结果验证
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "auto_repair"))

from doc_auto_fixer import (
from skillscripts.core.path_config_center import get_path_config
    DocumentAutoFixer,
    LinkFixer,
    FormatFixer,
    DocIssueType,
    FixStatus
)


class TestDocumentAutoFixer:
    """文档自动修复器测试类"""

    def __init__(self):
        self.test_dir = None
        self.test_files = []
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }

    def setup(self):
        """设置测试环境"""
        self.test_dir = tempfile.mkdtemp(prefix="doc_fixer_test_")
        print(f"测试目录: {self.test_dir}")

        self._create_test_files()

    def teardown(self):
        """清理测试环境"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            print(f"已清理测试目录: {self.test_dir}")

    def _create_test_files(self):
        """创建测试文件"""
        test_readme = os.path.join(self.test_dir, "README.md")
        with open(test_readme, 'w', encoding='utf-8') as f:
            f.write("""# 测试文档

这是一个测试文档，包含各种问题。

## 断裂的链接

这里有一个断裂的链接: [不存在的文件](./nonexistent.md)
这里有一个断裂的图片: ![](./missing_image.png)

## 编码问题

这里有一些编码问题：â€™ â€œ â€"

## 格式问题

###缺少空格的标题

1.缺少空格的列表项

## 正常的链接

[存在的文件](./existing.md)
""")
        self.test_files.append(test_readme)

        existing_file = os.path.join(self.test_dir, "existing.md")
        with open(existing_file, 'w', encoding='utf-8') as f:
            f.write("# 存在的文件\n\n这是一个存在的文件。")
        self.test_files.append(existing_file)

        sub_dir = os.path.join(self.test_dir, "docs")
        os.makedirs(sub_dir, exist_ok=True)
        
        doc_file = os.path.join(sub_dir, "nonexistent.md")
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write("# 另一个文档\n\n这是在docs目录下的文档。")
        self.test_files.append(doc_file)

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 80)
        print("开始运行文档自动修复器测试")
        print("=" * 80 + "\n")

        self.setup()

        try:
            self.test_link_detection()
            self.test_link_fixing()
            self.test_format_detection()
            self.test_format_fixing()
            self.test_full_workflow()
            self.test_batch_processing()

        finally:
            self.teardown()

        self._print_summary()

    def test_link_detection(self):
        """测试链接检测"""
        print("\n测试 1: 链接检测")
        print("-" * 80)

        test_file = self.test_files[0]
        fixer = DocumentAutoFixer(Path(self.test_dir))

        issues = fixer.detect_issues(test_file)
        link_issues = [i for i in issues if i.issue_type in [DocIssueType.BROKEN_LINK, DocIssueType.BROKEN_IMAGE_LINK]]

        self.results["total_tests"] += 1
        
        if len(link_issues) >= 2:
            print(f"✓ 检测到 {len(link_issues)} 个链接问题")
            for issue in link_issues:
                print(f"  - {issue.issue_type.name}: {issue.message}")
            self.results["passed_tests"] += 1
            self.results["test_details"].append({
                "test": "link_detection",
                "status": "passed",
                "issues_found": len(link_issues)
            })
        else:
            print(f"✗ 链接检测失败，期望至少2个问题，实际检测到 {len(link_issues)} 个")
            self.results["failed_tests"] += 1
            self.results["test_details"].append({
                "test": "link_detection",
                "status": "failed",
                "expected": 2,
                "actual": len(link_issues)
            })

    def test_link_fixing(self):
        """测试链接修复"""
        print("\n测试 2: 链接修复")
        print("-" * 80)

        test_file = self.test_files[0]
        fixer = DocumentAutoFixer(Path(self.test_dir))

        report = fixer.preview_fix(test_file)

        self.results["total_tests"] += 1

        if report.fixed_issues > 0:
            print(f"✓ 成功修复 {report.fixed_issues} 个链接问题")
            for result in report.results:
                if result.issue_type in [DocIssueType.BROKEN_LINK, DocIssueType.BROKEN_IMAGE_LINK]:
                    print(f"  - {result.message}")
                    if result.status == FixStatus.SUCCESS:
                        print(f"    原内容: {result.original_content}")
                        print(f"    修复后: {result.fixed_content}")
            
            self.results["passed_tests"] += 1
            self.results["test_details"].append({
                "test": "link_fixing",
                "status": "passed",
                "fixed_issues": report.fixed_issues
            })
        else:
            print(f"✗ 链接修复失败")
            self.results["failed_tests"] += 1
            self.results["test_details"].append({
                "test": "link_fixing",
                "status": "failed"
            })

    def test_format_detection(self):
        """测试格式问题检测"""
        print("\n测试 3: 格式问题检测")
        print("-" * 80)

        test_file = self.test_files[0]
        fixer = DocumentAutoFixer(Path(self.test_dir))

        issues = fixer.detect_issues(test_file)
        format_issues = [i for i in issues if i.issue_type in [
            DocIssueType.ENCODING_ERROR,
            DocIssueType.MARKDOWN_SYNTAX_ERROR,
            DocIssueType.MISSING_ALT_TEXT
        ]]

        self.results["total_tests"] += 1

        if len(format_issues) >= 3:
            print(f"✓ 检测到 {len(format_issues)} 个格式问题")
            for issue in format_issues:
                print(f"  - {issue.issue_type.name}: {issue.message}")
            
            self.results["passed_tests"] += 1
            self.results["test_details"].append({
                "test": "format_detection",
                "status": "passed",
                "issues_found": len(format_issues)
            })
        else:
            print(f"✗ 格式问题检测失败，期望至少3个问题，实际检测到 {len(format_issues)} 个")
            self.results["failed_tests"] += 1
            self.results["test_details"].append({
                "test": "format_detection",
                "status": "failed",
                "expected": 3,
                "actual": len(format_issues)
            })

    def test_format_fixing(self):
        """测试格式修复"""
        print("\n测试 4: 格式修复")
        print("-" * 80)

        test_file = self.test_files[0]
        fixer = DocumentAutoFixer(Path(self.test_dir))

        report = fixer.preview_fix(test_file)

        format_results = [r for r in report.results if r.issue_type in [
            DocIssueType.ENCODING_ERROR,
            DocIssueType.MARKDOWN_SYNTAX_ERROR,
            DocIssueType.MISSING_ALT_TEXT
        ]]

        self.results["total_tests"] += 1

        fixed_format_issues = sum(1 for r in format_results if r.status == FixStatus.SUCCESS)

        if fixed_format_issues > 0:
            print(f"✓ 成功修复 {fixed_format_issues} 个格式问题")
            for result in format_results:
                if result.status == FixStatus.SUCCESS:
                    print(f"  - {result.message}")
                    print(f"    原内容: {result.original_content}")
                    print(f"    修复后: {result.fixed_content}")
            
            self.results["passed_tests"] += 1
            self.results["test_details"].append({
                "test": "format_fixing",
                "status": "passed",
                "fixed_issues": fixed_format_issues
            })
        else:
            print(f"✗ 格式修复失败")
            self.results["failed_tests"] += 1
            self.results["test_details"].append({
                "test": "format_fixing",
                "status": "failed"
            })

    def test_full_workflow(self):
        """测试完整工作流"""
        print("\n测试 5: 完整工作流")
        print("-" * 80)

        test_file = self.test_files[0]
        fixer = DocumentAutoFixer(Path(self.test_dir))

        with open(test_file, 'r', encoding='utf-8') as f:
            original_content = f.read()

        report = fixer.apply_fix(test_file)

        self.results["total_tests"] += 1

        if os.path.exists(test_file):
            with open(test_file, 'r', encoding='utf-8') as f:
                modified_content = f.read()

            if modified_content != original_content:
                print(f"✓ 文件已修改")
                print(f"  检测问题: {report.total_issues}")
                print(f"  成功修复: {report.fixed_issues}")
                print(f"  失败修复: {report.failed_issues}")
                print(f"  执行时间: {report.execution_time_ms:.2f}ms")

                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                self.results["passed_tests"] += 1
                self.results["test_details"].append({
                    "test": "full_workflow",
                    "status": "passed",
                    "total_issues": report.total_issues,
                    "fixed_issues": report.fixed_issues
                })
            else:
                print(f"✗ 文件未被修改")
                self.results["failed_tests"] += 1
                self.results["test_details"].append({
                    "test": "full_workflow",
                    "status": "failed",
                    "reason": "file_not_modified"
                })
        else:
            print(f"✗ 文件不存在")
            self.results["failed_tests"] += 1
            self.results["test_details"].append({
                "test": "full_workflow",
                "status": "failed",
                "reason": "file_not_found"
            })

    def test_batch_processing(self):
        """测试批量处理"""
        print("\n测试 6: 批量处理")
        print("-" * 80)

        fixer = DocumentAutoFixer(Path(self.test_dir))

        reports = fixer.batch_fix(self.test_files, auto_apply=False)

        self.results["total_tests"] += 1

        if len(reports) == len(self.test_files):
            print(f"✓ 成功处理 {len(reports)} 个文件")
            total_issues = sum(r.total_issues for r in reports)
            total_fixed = sum(r.fixed_issues for r in reports)
            print(f"  总问题数: {total_issues}")
            print(f"  总修复数: {total_fixed}")
            
            self.results["passed_tests"] += 1
            self.results["test_details"].append({
                "test": "batch_processing",
                "status": "passed",
                "files_processed": len(reports),
                "total_issues": total_issues,
                "total_fixed": total_fixed
            })
        else:
            print(f"✗ 批量处理失败，期望 {len(self.test_files)} 个报告，实际 {len(reports)} 个")
            self.results["failed_tests"] += 1
            self.results["test_details"].append({
                "test": "batch_processing",
                "status": "failed",
                "expected": len(self.test_files),
                "actual": len(reports)
            })

    def _print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 80)
        print("测试摘要")
        print("=" * 80)
        print(f"总测试数: {self.results['total_tests']}")
        print(f"通过测试: {self.results['passed_tests']}")
        print(f"失败测试: {self.results['failed_tests']}")
        print(f"通过率: {self.results['passed_tests'] / max(self.results['total_tests'], 1) * 100:.1f}%")
        print("=" * 80)

        report_file = "test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n测试报告已保存: {os.path.abspath(report_file)}")


def main():
    """主函数"""
    tester = TestDocumentAutoFixer()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
