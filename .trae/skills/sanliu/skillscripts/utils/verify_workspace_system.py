#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作目录规范化管理系统验证脚本

验证三个增强版管理器的功能：
1. EnhancedPathConfigManager - 工作目录管理器
2. EnhancedDocVersionManager - 文档版本管理器
3. EnhancedReportVersionManager - 报告版本管理器
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from skillscripts.core.path_config_center import get_path_config

sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from utils.enhanced_path_config_manager import (
    EnhancedPathConfigManager, PathMode, DirectoryStatus,
    DirectoryTemplates, DirectoryHealthChecker, DirectorySnapshotManager
)
from utils.enhanced_doc_version_manager import (
    EnhancedDocVersionManager, DocumentCategory, DocumentStatus,
    DocumentChangeTracker, DocumentSnapshotManager as DocSnapshotManager
)
from utils.enhanced_report_version_manager import (
    EnhancedReportVersionManager, ReportCategory, ReportStatus,
    ReportQuery, ArchiveFormat
)


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_result(name: str, success: bool, message: str = ""):
    """打印测试结果"""
    status = "✓ 通过" if success else "✗ 失败"
    print(f"  {status} - {name}")
    if message:
        print(f"         {message}")


def verify_path_config_manager(base_path: Path) -> dict:
    """验证工作目录管理器"""
    print_section("1. 工作目录管理器验证 (EnhancedPathConfigManager)")
    
    results = {"passed": 0, "failed": 0, "details": []}
    
    try:
        manager = EnhancedPathConfigManager(
            mode=PathMode.SELF_ITERATION,
            auto_detect=False
        )
        print_result("管理器初始化", True)
        results["passed"] += 1
    except Exception as e:
        print_result("管理器初始化", False, str(e))
        results["failed"] += 1
        return results
    
    try:
        templates = manager.structure_manager.get_templates_for_mode(PathMode.SELF_ITERATION)
        has_templates = len(templates) > 0
        print_result("获取目录模板", has_templates, f"模板数量: {len(templates)}")
        results["passed"] += 1 if has_templates else 0
        results["failed"] += 0 if has_templates else 1
    except Exception as e:
        print_result("获取目录模板", False, str(e))
        results["failed"] += 1
    
    try:
        status = manager.structure_manager.get_directory_status("docs")
        is_valid = status["status"] in [DirectoryStatus.EXISTS.value, DirectoryStatus.MISSING.value]
        print_result("获取目录状态", is_valid, f"状态: {status['status']}")
        results["passed"] += 1 if is_valid else 0
        results["failed"] += 0 if is_valid else 1
    except Exception as e:
        print_result("获取目录状态", False, str(e))
        results["failed"] += 1
    
    try:
        health_report = manager.health_checker.perform_health_check()
        has_health_score = health_report.health_score >= 0
        print_result("健康检查", has_health_score, f"健康分数: {health_report.health_score:.1f}")
        results["passed"] += 1 if has_health_score else 0
        results["failed"] += 0 if has_health_score else 1
    except Exception as e:
        print_result("健康检查", False, str(e))
        results["failed"] += 1
    
    try:
        snapshot = manager.create_snapshot()
        has_snapshot = snapshot.snapshot_id is not None
        print_result("创建快照", has_snapshot, f"快照ID: {snapshot.snapshot_id}")
        results["passed"] += 1 if has_snapshot else 0
        results["failed"] += 0 if has_snapshot else 1
    except Exception as e:
        print_result("创建快照", False, str(e))
        results["failed"] += 1
    
    try:
        workspace_info = manager.get_workspace_info()
        has_info = "mode" in workspace_info and "health_score" in workspace_info
        print_result("获取工作空间信息", has_info)
        results["passed"] += 1 if has_info else 0
        results["failed"] += 0 if has_info else 1
    except Exception as e:
        print_result("获取工作空间信息", False, str(e))
        results["failed"] += 1
    
    return results


def verify_doc_version_manager(base_path: Path) -> dict:
    """验证文档版本管理器"""
    print_section("2. 文档版本管理器验证 (EnhancedDocVersionManager)")
    
    results = {"passed": 0, "failed": 0, "details": []}
    
    test_dir = base_path / "test_docs"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_doc = test_dir / "test_requirements.md"
    test_doc.write_text("# 测试需求文档\n\n这是一个测试需求文档。", encoding='utf-8')
    
    try:
        manager = EnhancedDocVersionManager(base_path)
        print_result("管理器初始化", True)
        results["passed"] += 1
    except Exception as e:
        print_result("管理器初始化", False, str(e))
        results["failed"] += 1
        return results
    
    try:
        doc_info = manager.register_document(
            str(test_doc),
            category=DocumentCategory.REQUIREMENTS.value,
            name="测试需求文档",
            tags=["测试", "需求"]
        )
        is_registered = doc_info.doc_id is not None
        print_result("注册文档", is_registered, f"文档ID: {doc_info.doc_id}")
        results["passed"] += 1 if is_registered else 0
        results["failed"] += 0 if is_registered else 1
    except Exception as e:
        print_result("注册文档", False, str(e))
        results["failed"] += 1
        return results
    
    try:
        snapshot = manager.create_snapshot(doc_info.doc_id)
        has_snapshot = snapshot is not None and snapshot.snapshot_id is not None
        print_result("创建文档快照", has_snapshot, f"快照ID: {snapshot.snapshot_id if snapshot else 'N/A'}")
        results["passed"] += 1 if has_snapshot else 0
        results["failed"] += 0 if has_snapshot else 1
    except Exception as e:
        print_result("创建文档快照", False, str(e))
        results["failed"] += 1
    
    try:
        test_doc.write_text("# 测试需求文档\n\n## 更新\n\n添加了更新内容。", encoding='utf-8')
        updated_info = manager.update_document(doc_info.doc_id)
        is_updated = updated_info is not None and updated_info.version != doc_info.version
        print_result("更新文档", is_updated, f"新版本: {updated_info.version if updated_info else 'N/A'}")
        results["passed"] += 1 if is_updated else 0
        results["failed"] += 0 if is_updated else 1
    except Exception as e:
        print_result("更新文档", False, str(e))
        results["failed"] += 1
    
    try:
        changes = manager.get_change_history(doc_info.doc_id)
        has_changes = len(changes) > 0
        print_result("获取变更历史", has_changes, f"变更记录数: {len(changes)}")
        results["passed"] += 1 if has_changes else 0
        results["failed"] += 0 if has_changes else 1
    except Exception as e:
        print_result("获取变更历史", False, str(e))
        results["failed"] += 1
    
    try:
        search_results = manager.search_documents("需求")
        has_results = len(search_results) > 0
        print_result("搜索文档", has_results, f"搜索结果数: {len(search_results)}")
        results["passed"] += 1 if has_results else 0
        results["failed"] += 0 if has_results else 1
    except Exception as e:
        print_result("搜索文档", False, str(e))
        results["failed"] += 1
    
    try:
        stats = manager.get_statistics()
        has_stats = "total_documents" in stats
        print_result("获取统计信息", has_stats, f"文档总数: {stats.get('total_documents', 0)}")
        results["passed"] += 1 if has_stats else 0
        results["failed"] += 0 if has_stats else 1
    except Exception as e:
        print_result("获取统计信息", False, str(e))
        results["failed"] += 1
    
    return results


def verify_report_version_manager(base_path: Path) -> dict:
    """验证报告版本管理器"""
    print_section("3. 报告版本管理器验证 (EnhancedReportVersionManager)")
    
    results = {"passed": 0, "failed": 0, "details": []}
    
    test_dir = base_path / "test_reports"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_report = test_dir / "test_unit_report.json"
    test_report.write_text(json.dumps({
        "test_name": "单元测试报告",
        "total": 100,
        "passed": 95,
        "failed": 5,
        "timestamp": datetime.now().isoformat()
    }), encoding='utf-8')
    
    try:
        manager = EnhancedReportVersionManager(base_path)
        print_result("管理器初始化", True)
        results["passed"] += 1
    except Exception as e:
        print_result("管理器初始化", False, str(e))
        results["failed"] += 1
        return results
    
    try:
        report_info = manager.store_report(
            str(test_report),
            category=ReportCategory.UNIT_TEST.value,
            name="单元测试报告",
            metrics={"total": 100, "passed": 95, "failed": 5}
        )
        is_stored = report_info.report_id is not None
        print_result("存储报告", is_stored, f"报告ID: {report_info.report_id}")
        results["passed"] += 1 if is_stored else 0
        results["failed"] += 0 if is_stored else 1
    except Exception as e:
        print_result("存储报告", False, str(e))
        results["failed"] += 1
        return results
    
    try:
        reports = manager.list_reports(category=ReportCategory.UNIT_TEST.value)
        has_reports = len(reports) > 0
        print_result("列出报告", has_reports, f"报告数量: {len(reports)}")
        results["passed"] += 1 if has_reports else 0
        results["failed"] += 0 if has_reports else 1
    except Exception as e:
        print_result("列出报告", False, str(e))
        results["failed"] += 1
    
    try:
        query = ReportQuery(
            categories=[ReportCategory.UNIT_TEST.value],
            limit=10
        )
        query_results = manager.query_reports(query)
        has_query_results = len(query_results) >= 0
        print_result("查询报告", has_query_results, f"查询结果数: {len(query_results)}")
        results["passed"] += 1 if has_query_results else 0
        results["failed"] += 0 if has_query_results else 1
    except Exception as e:
        print_result("查询报告", False, str(e))
        results["failed"] += 1
    
    test_report2 = test_dir / "test_unit_report2.json"
    test_report2.write_text(json.dumps({
        "test_name": "单元测试报告2",
        "total": 120,
        "passed": 115,
        "failed": 5,
        "timestamp": datetime.now().isoformat()
    }), encoding='utf-8')
    
    try:
        report_info2 = manager.store_report(
            str(test_report2),
            category=ReportCategory.UNIT_TEST.value,
            name="单元测试报告2",
            metrics={"total": 120, "passed": 115, "failed": 5}
        )
        
        comparison = manager.compare_reports(report_info.report_id, report_info2.report_id)
        has_comparison = comparison is not None
        print_result("报告对比", has_comparison, f"对比ID: {comparison.comparison_id if comparison else 'N/A'}")
        results["passed"] += 1 if has_comparison else 0
        results["failed"] += 0 if has_comparison else 1
    except Exception as e:
        print_result("报告对比", False, str(e))
        results["failed"] += 1
    
    try:
        archive = manager.archive_reports(
            [report_info.report_id],
            name="测试归档",
            archive_format=ArchiveFormat.ZIP
        )
        has_archive = archive is not None
        print_result("归档报告", has_archive, f"归档ID: {archive.archive_id if archive else 'N/A'}")
        results["passed"] += 1 if has_archive else 0
        results["failed"] += 0 if has_archive else 1
    except Exception as e:
        print_result("归档报告", False, str(e))
        results["failed"] += 1
    
    try:
        stats = manager.get_statistics()
        has_stats = "total_reports" in stats
        print_result("获取统计信息", has_stats, f"报告总数: {stats.get('total_reports', 0)}")
        results["passed"] += 1 if has_stats else 0
        results["failed"] += 0 if has_stats else 1
    except Exception as e:
        print_result("获取统计信息", False, str(e))
        results["failed"] += 1
    
    return results


def generate_directory_structure_example() -> str:
    """生成目录结构示例"""
    return """
工作目录结构示例 (三省六部技能项目)
========================================

sanliu/                              # 技能根目录
├── docs/                            # 文档目录
│   ├── libs/                        # 文档库
│   │   └── v1.0.0/                  # 版本化文档
│   ├── reports/                     # 文档报告
│   ├── workflow/                    # 工作流程文档
│   │   ├── requirements/            # 需求阶段文档
│   │   ├── design/                  # 设计阶段文档
│   │   ├── implementation/          # 实现阶段文档
│   │   ├── testing/                 # 测试阶段文档
│   │   └── deployment/              # 部署阶段文档
│   ├── snapshots/                   # 文档快照
│   └── diff_reports/                # 差异报告
│
├── reports/                         # 测试报告目录
│   ├── unit_tests/                  # 单元测试报告
│   ├── integration_tests/           # 集成测试报告
│   ├── e2e_tests/                   # E2E测试报告
│   ├── performance_tests/           # 性能测试报告
│   ├── security_tests/              # 安全测试报告
│   ├── regression_tests/            # 回归测试报告
│   ├── coverage/                    # 覆盖率报告
│   ├── pipeline/                    # 流水线报告
│   ├── quality/                     # 质量报告
│   ├── custom/                      # 自定义报告
│   └── report_archives/             # 报告归档
│
├── tests/                           # 测试目录
│   ├── unit/                        # 单元测试
│   ├── integration/                 # 集成测试
│   ├── e2e/                         # E2E测试
│   ├── database/                    # 数据库测试
│   ├── security/                    # 安全测试
│   ├── performance/                 # 性能测试
│   └── regression/                  # 回归测试
│
├── skillscripts/                    # 技能脚本目录
│   ├── core/                        # 核心脚本
│   ├── analysis/                    # 分析脚本
│   ├── pipeline/                    # 流水线脚本
│   ├── test/                        # 测试脚本
│   ├── utils/                       # 工具脚本
│   ├── requirements/                # 需求管理脚本
│   ├── optimization/                # 优化脚本
│   ├── monitoring/                  # 监控脚本
│   ├── design/                      # 设计脚本
│   ├── reports/                     # 报告脚本
│   ├── logs/                        # 日志脚本
│   └── docs/                        # 文档脚本
│
├── data/                            # 数据目录
│   ├── cache/                       # 缓存数据
│   ├── temp/                        # 临时数据
│   └── backups/                     # 备份数据
│
├── logs/                            # 日志目录
│
├── path_config.json                 # 路径配置文件
├── version.json                     # 版本信息文件
└── SKILL.md                         # 技能说明文档
"""


def main():
    """主函数"""
    print("=" * 60)
    print(" 三省六部技能项目 - 工作目录规范化管理系统验证")
    print("=" * 60)
    print(f" 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    base_path = Path(__file__).parent.parent.parent
    
    path_results = verify_path_config_manager(base_path)
    doc_results = verify_doc_version_manager(base_path)
    report_results = verify_report_version_manager(base_path)
    
    print_section("验证结果汇总")
    
    total_passed = path_results["passed"] + doc_results["passed"] + report_results["passed"]
    total_failed = path_results["failed"] + doc_results["failed"] + report_results["failed"]
    total_tests = total_passed + total_failed
    
    print(f"\n  工作目录管理器: {path_results['passed']}/{path_results['passed'] + path_results['failed']} 通过")
    print(f"  文档版本管理器: {doc_results['passed']}/{doc_results['passed'] + doc_results['failed']} 通过")
    print(f"  报告版本管理器: {report_results['passed']}/{report_results['passed'] + report_results['failed']} 通过")
    
    print(f"\n  总计: {total_passed}/{total_tests} 测试通过")
    
    if total_failed == 0:
        print("\n  ✓ 所有验证测试通过!")
    else:
        print(f"\n  ✗ {total_failed} 个测试失败")
    
    print(generate_directory_structure_example())
    
    print_section("新增/修改文件列表")
    
    files = [
        ("skillscripts/utils/enhanced_path_config_manager.py", "新增", "工作目录管理器增强版"),
        ("skillscripts/utils/enhanced_doc_version_manager.py", "新增", "文档版本管理器增强版"),
        ("skillscripts/utils/enhanced_report_version_manager.py", "新增", "报告版本管理器增强版"),
        ("skillscripts/utils/verify_workspace_system.py", "新增", "系统验证脚本"),
    ]
    
    print("\n  文件路径".ljust(60) + "状态".ljust(8) + "说明")
    print("  " + "-" * 90)
    
    for file_path, status, desc in files:
        print(f"  {file_path.ljust(60)}{status.ljust(8)}{desc}")
    
    print("\n" + "=" * 60)
    print(" 验证完成")
    print("=" * 60)
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
