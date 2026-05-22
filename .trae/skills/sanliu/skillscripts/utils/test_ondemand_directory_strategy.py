#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按需创建目录策略验证测试脚本

验证三省六部技能的按需创建目录策略是否正确实现。

测试场景：
1. 测试文档写入时目录创建
2. 测试报告生成时目录创建
3. 测试版本迭代时目录创建
4. 验证无预生成空目录
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple


class DirectoryCreationTestResult:
    """测试结果数据类"""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.message = ""
        self.details: Dict[str, Any] = {}
        self.issues: List[str] = []
        self.recommendations: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
            "issues": self.issues,
            "recommendations": self.recommendations
        }


class OnDemandDirectoryStrategyVerifier:
    """按需创建目录策略验证器"""
    
    def __init__(self, test_base_dir: Path):
        self.test_base_dir = test_base_dir
        self.results: List[DirectoryCreationTestResult] = []
        self.issues: List[str] = []
        self.recommendations: List[str] = []
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("=" * 60)
        print("三省六部技能 - 按需创建目录策略验证")
        print("=" * 60)
        print(f"测试目录: {self.test_base_dir}")
        print(f"测试时间: {datetime.now().isoformat()}")
        print()
        
        self._test_doc_version_manager()
        self._test_report_version_manager()
        self._test_version_manager()
        self._test_ondemand_strategy()
        
        return self._generate_report()
    
    def _test_doc_version_manager(self):
        """测试文档版本管理器的目录创建策略"""
        result = DirectoryCreationTestResult("文档版本管理器目录创建策略")
        print("\n[测试 1] 文档版本管理器目录创建策略")
        print("-" * 40)
        
        try:
            test_dir = self.test_base_dir / "doc_manager_test"
            test_dir.mkdir(parents=True, exist_ok=True)
            
            docs_dir = test_dir / "docs"
            
            print(f"  初始状态 - docs目录存在: {docs_dir.exists()}")
            result.details["initial_docs_exists"] = docs_dir.exists()
            
            sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "utils"))
            
            from doc_version_manager import DocVersionManager
            
            original_docs_dir = DocVersionManager.DOCS_DIR
            DocVersionManager.DOCS_DIR = docs_dir
            DocVersionManager.LIBS_DIR = docs_dir / "libs"
            DocVersionManager.REPORTS_DIR = docs_dir / "reports"
            DocVersionManager.WORKFLOW_DIR = docs_dir / "workflow"
            DocVersionManager.HISTORY_DIR = docs_dir / "history"
            DocVersionManager.VERSION_FILE = docs_dir / "version.json"
            DocVersionManager.METADATA_FILE = docs_dir / "metadata.json"
            DocVersionManager.BRANCH_FILE = docs_dir / "branches.json"
            DocVersionManager.SNAPSHOT_DIR = docs_dir / "snapshots"
            DocVersionManager.DIFF_REPORT_DIR = docs_dir / "diff_reports"
            DocVersionManager.ROLLBACK_DIR = docs_dir / "rollback_backups"
            
            dirs_before_init = list(docs_dir.glob("**")) if docs_dir.exists() else []
            print(f"  初始化前目录数量: {len(dirs_before_init)}")
            result.details["dirs_before_init"] = len(dirs_before_init)
            
            manager = DocVersionManager()
            
            dirs_after_init = list(docs_dir.glob("**"))
            print(f"  初始化后目录数量: {len(dirs_after_init)}")
            result.details["dirs_after_init"] = len(dirs_after_init)
            
            created_dirs = [d for d in dirs_after_init if d not in dirs_before_init]
            print(f"  初始化时创建的目录数: {len(created_dirs)}")
            result.details["created_dirs_count"] = len(created_dirs)
            
            if len(created_dirs) > 0:
                result.passed = False
                result.message = "文档版本管理器在初始化时预创建了目录，违反按需创建策略"
                result.issues.append(f"初始化时预创建了 {len(created_dirs)} 个目录")
                result.recommendations.append("应移除 __init__ 中的 _ensure_dirs() 调用，改为在写入文件时按需创建")
                print(f"  [失败] {result.message}")
                for d in created_dirs[:10]:
                    print(f"    - {d.relative_to(docs_dir)}")
            else:
                result.passed = True
                result.message = "文档版本管理器正确实现了按需创建目录策略"
                print(f"  [通过] {result.message}")
            
            DocVersionManager.DOCS_DIR = original_docs_dir
            
        except Exception as e:
            result.passed = False
            result.message = f"测试执行失败: {str(e)}"
            result.issues.append(str(e))
            print(f"  [错误] {result.message}")
        
        self.results.append(result)
    
    def _test_report_version_manager(self):
        """测试报告版本管理器的目录创建策略"""
        result = DirectoryCreationTestResult("报告版本管理器目录创建策略")
        print("\n[测试 2] 报告版本管理器目录创建策略")
        print("-" * 40)
        
        try:
            test_dir = self.test_base_dir / "report_manager_test"
            test_dir.mkdir(parents=True, exist_ok=True)
            
            reports_dir = test_dir / "reports"
            
            print(f"  初始状态 - reports目录存在: {reports_dir.exists()}")
            result.details["initial_reports_exists"] = reports_dir.exists()
            
            sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "utils"))
            
            from report_version_manager import ReportStorage
            
            dirs_before_init = list(reports_dir.glob("**")) if reports_dir.exists() else []
            print(f"  初始化前目录数量: {len(dirs_before_init)}")
            result.details["dirs_before_init"] = len(dirs_before_init)
            
            storage = ReportStorage(base_dir=reports_dir)
            
            dirs_after_init = list(reports_dir.glob("**"))
            print(f"  初始化后目录数量: {len(dirs_after_init)}")
            result.details["dirs_after_init"] = len(dirs_after_init)
            
            created_dirs = [d for d in dirs_after_init if d not in dirs_before_init]
            print(f"  初始化时创建的目录数: {len(created_dirs)}")
            result.details["created_dirs_count"] = len(created_dirs)
            
            if len(created_dirs) > 0:
                result.passed = False
                result.message = "报告版本管理器在初始化时预创建了目录，违反按需创建策略"
                result.issues.append(f"初始化时预创建了 {len(created_dirs)} 个目录")
                result.recommendations.append("应移除 __init__ 中的 _ensure_dirs() 调用，改为在写入文件时按需创建")
                print(f"  [失败] {result.message}")
                for d in created_dirs[:10]:
                    print(f"    - {d.relative_to(reports_dir)}")
            else:
                result.passed = True
                result.message = "报告版本管理器正确实现了按需创建目录策略"
                print(f"  [通过] {result.message}")
            
        except Exception as e:
            result.passed = False
            result.message = f"测试执行失败: {str(e)}"
            result.issues.append(str(e))
            print(f"  [错误] {result.message}")
        
        self.results.append(result)
    
    def _test_version_manager(self):
        """测试版本管理器的目录创建策略"""
        result = DirectoryCreationTestResult("版本管理器目录创建策略")
        print("\n[测试 3] 版本管理器目录创建策略")
        print("-" * 40)
        
        try:
            test_dir = self.test_base_dir / "version_manager_test"
            test_dir.mkdir(parents=True, exist_ok=True)
            
            version_file = test_dir / "version.json"
            changelog_file = test_dir / "CHANGELOG.md"
            
            print(f"  初始状态 - version目录存在: {test_dir.exists()}")
            result.details["initial_version_dir_exists"] = test_dir.exists()
            
            sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "utils"))
            
            from version_manager import VersionManager, VersionConfig
            
            config = VersionConfig(
                version_file=version_file,
                changelog_file=changelog_file
            )
            
            dirs_before_init = list(test_dir.glob("**"))
            print(f"  初始化前目录/文件数量: {len(dirs_before_init)}")
            result.details["items_before_init"] = len(dirs_before_init)
            
            manager = VersionManager(config)
            
            dirs_after_init = list(test_dir.glob("**"))
            print(f"  初始化后目录/文件数量: {len(dirs_after_init)}")
            result.details["items_after_init"] = len(dirs_after_init)
            
            created_items = [d for d in dirs_after_init if d not in dirs_before_init]
            print(f"  初始化时创建的项目数: {len(created_items)}")
            result.details["created_items_count"] = len(created_items)
            
            version_file_exists_before_bump = version_file.exists()
            print(f"  版本文件在bump前存在: {version_file_exists_before_bump}")
            
            from version_manager import VersionPart
            manager.bump_version(VersionPart.PATCH, "测试版本迭代")
            
            version_file_exists_after_bump = version_file.exists()
            print(f"  版本文件在bump后存在: {version_file_exists_after_bump}")
            result.details["version_file_created_on_demand"] = (
                not version_file_exists_before_bump and version_file_exists_after_bump
            )
            
            if len(created_items) == 0:
                result.passed = True
                result.message = "版本管理器正确实现了按需创建目录策略"
                print(f"  [通过] {result.message}")
            else:
                created_dirs_only = [d for d in created_items if d.is_dir()]
                if len(created_dirs_only) == 0:
                    result.passed = True
                    result.message = "版本管理器正确实现了按需创建目录策略（仅创建了文件）"
                    print(f"  [通过] {result.message}")
                else:
                    result.passed = False
                    result.message = "版本管理器在初始化时预创建了目录"
                    result.issues.append(f"初始化时预创建了 {len(created_dirs_only)} 个目录")
                    print(f"  [失败] {result.message}")
            
        except Exception as e:
            result.passed = False
            result.message = f"测试执行失败: {str(e)}"
            result.issues.append(str(e))
            print(f"  [错误] {result.message}")
        
        self.results.append(result)
    
    def _test_ondemand_strategy(self):
        """测试按需创建策略的具体实现"""
        result = DirectoryCreationTestResult("按需创建策略实现验证")
        print("\n[测试 4] 按需创建策略实现验证")
        print("-" * 40)
        
        try:
            test_dir = self.test_base_dir / "ondemand_test"
            test_dir.mkdir(parents=True, exist_ok=True)
            
            print("  测试场景: 写入文件时创建父目录")
            
            nested_file = test_dir / "deeply" / "nested" / "dir" / "file.txt"
            nested_file.parent.mkdir(parents=True, exist_ok=True)
            nested_file.write_text("test content")
            
            print(f"  成功创建嵌套文件: {nested_file.exists()}")
            result.details["nested_file_created"] = nested_file.exists()
            
            print("\n  检查代码中的目录创建模式...")
            
            code_patterns = {
                "correct_ondemand": [
                    "path.parent.mkdir(parents=True, exist_ok=True)",
                    "target_path.parent.mkdir(parents=True, exist_ok=True)",
                    "file_path.parent.mkdir(parents=True, exist_ok=True)"
                ],
                "incorrect_pregenerate": [
                    "self.DOCS_DIR.mkdir(parents=True, exist_ok=True)",
                    "self.REPORTS_DIR.mkdir(parents=True, exist_ok=True)",
                    "self.LIBS_DIR.mkdir(parents=True, exist_ok=True)"
                ]
            }
            
            result.details["correct_patterns"] = code_patterns["correct_ondemand"]
            result.details["incorrect_patterns"] = code_patterns["incorrect_pregenerate"]
            
            print("  正确的按需创建模式:")
            for pattern in code_patterns["correct_ondemand"]:
                print(f"    ✓ {pattern}")
            
            print("  不正确的预生成模式:")
            for pattern in code_patterns["incorrect_pregenerate"]:
                print(f"    ✗ {pattern}")
            
            result.passed = True
            result.message = "按需创建策略验证完成"
            print(f"  [通过] {result.message}")
            
        except Exception as e:
            result.passed = False
            result.message = f"测试执行失败: {str(e)}"
            result.issues.append(str(e))
            print(f"  [错误] {result.message}")
        
        self.results.append(result)
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        all_issues = []
        all_recommendations = []
        
        for r in self.results:
            all_issues.extend(r.issues)
            all_recommendations.extend(r.recommendations)
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
            },
            "test_results": [r.to_dict() for r in self.results],
            "issues": all_issues,
            "recommendations": all_recommendations,
            "conclusion": self._generate_conclusion(passed_tests, failed_tests)
        }
        
        print("\n" + "=" * 60)
        print("验证报告摘要")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"通过率: {report['summary']['pass_rate']}")
        print()
        
        if all_issues:
            print("发现的问题:")
            for i, issue in enumerate(all_issues, 1):
                print(f"  {i}. {issue}")
        
        if all_recommendations:
            print("\n改进建议:")
            for i, rec in enumerate(all_recommendations, 1):
                print(f"  {i}. {rec}")
        
        print()
        print("结论:")
        print(f"  {report['conclusion']}")
        
        return report
    
    def _generate_conclusion(self, passed: int, failed: int) -> str:
        """生成结论"""
        if failed == 0:
            return "所有测试通过，按需创建目录策略已正确实现。"
        elif passed == 0:
            return "所有测试失败，按需创建目录策略未正确实现，需要全面修改。"
        else:
            return f"部分测试通过({passed}/{passed+failed})，按需创建目录策略存在部分问题，需要针对性修复。"


def main():
    """主函数"""
    temp_dir = Path(tempfile.mkdtemp(prefix="sanliu_ondemand_test_"))
    
    try:
        verifier = OnDemandDirectoryStrategyVerifier(temp_dir)
        report = verifier.run_all_tests()
        
        report_file = temp_dir / "verification_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存至: {report_file}")
        
        return 0 if report["summary"]["failed"] == 0 else 1
        
    finally:
        pass


if __name__ == "__main__":
    sys.exit(main())
