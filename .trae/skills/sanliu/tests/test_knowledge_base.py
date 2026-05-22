#!/usr/bin/env python3
"""
知识库功能测试

测试内容：
1. 知识存储
2. 知识检索
3. 知识学习系统
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent / "skillscripts"))

from test_runner import TestRunner, TestResult, print_header, print_result

TEST_DATA_DIR = Path(__file__).parent / "test_data" / "knowledge_base"
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)


def cleanup_test_data():
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR)
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)


def test_knowledge_base_import():
    try:
        from analysis.knowledge_base import (
            KnowledgeBase,
            KnowledgeItem,
            KnowledgeType,
            KnowledgeStatus,
            StorageType,
            SearchMode
        )
        return True, "模块导入成功", {
            "classes": ["KnowledgeBase", "KnowledgeItem", "KnowledgeType", "KnowledgeStatus", "StorageType", "SearchMode"]
        }
    except ImportError as e:
        return False, f"模块导入失败: {e}", {}


def test_knowledge_item_creation():
    try:
        from analysis.knowledge_base import KnowledgeItem, KnowledgeType, KnowledgeStatus
        
        item = KnowledgeItem(
            knowledge_id="KB-TEST-001",
            knowledge_type=KnowledgeType.FIX_PATTERN,
            title="空指针异常修复模式",
            content="检查变量是否为None，使用安全访问操作符",
            tags=["null_pointer", "fix", "python"],
            category="null_pointer",
            confidence_score=0.95,
            examples=[
                {"code": "if value is not None:", "description": "空值检查"}
            ]
        )
        
        assert item.knowledge_id == "KB-TEST-001"
        assert item.knowledge_type == KnowledgeType.FIX_PATTERN
        assert len(item.tags) == 3
        
        item_dict = item.to_dict()
        assert "knowledge_id" in item_dict
        
        restored = KnowledgeItem.from_dict(item_dict)
        assert restored.knowledge_id == item.knowledge_id
        
        return True, "知识项创建测试成功", {
            "knowledge_id": item.knowledge_id,
            "type": item.knowledge_type.value,
            "tags_count": len(item.tags),
            "serialization": "成功"
        }
    except Exception as e:
        return False, f"知识项创建测试失败: {e}", {}


def test_knowledge_base_initialization():
    try:
        from analysis.knowledge_base import KnowledgeBase, StorageType
        
        kb = KnowledgeBase(
            storage_path=TEST_DATA_DIR / "kb_init",
            storage_type=StorageType.SQLITE
        )
        
        assert kb.storage_type == StorageType.SQLITE
        
        return True, "知识库初始化测试成功", {
            "storage_type": kb.storage_type.value,
            "initialized": True
        }
    except Exception as e:
        return False, f"知识库初始化测试失败: {e}", {}


def test_knowledge_storage():
    try:
        from analysis.knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeType, StorageType
        
        kb = KnowledgeBase(
            storage_path=TEST_DATA_DIR / "kb_storage",
            storage_type=StorageType.SQLITE
        )
        
        item = KnowledgeItem(
            knowledge_id="",
            knowledge_type=KnowledgeType.BEST_PRACTICE,
            title="代码审查最佳实践",
            content="定期进行代码审查，关注代码质量和安全性",
            tags=["code_review", "best_practice"],
            category="coding_style"
        )
        
        kid = kb.add_knowledge(item)
        
        assert kid is not None
        
        retrieved = kb.get_knowledge(kid)
        assert retrieved is not None
        assert retrieved.title == "代码审查最佳实践"
        
        return True, "知识存储测试成功", {
            "added_knowledge_id": kid,
            "retrieved_title": retrieved.title
        }
    except Exception as e:
        return False, f"知识存储测试失败: {e}", {}


def test_knowledge_search():
    try:
        from analysis.knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeType, SearchMode, StorageType
        
        kb = KnowledgeBase(
            storage_path=TEST_DATA_DIR / "kb_search",
            storage_type=StorageType.SQLITE
        )
        
        items = [
            KnowledgeItem(
                knowledge_id="",
                knowledge_type=KnowledgeType.FIX_PATTERN,
                title="Python空指针修复",
                content="使用is None检查空值",
                tags=["python", "null"]
            ),
            KnowledgeItem(
                knowledge_id="",
                knowledge_type=KnowledgeType.FIX_PATTERN,
                title="JavaScript空指针修复",
                content="使用=== null检查空值",
                tags=["javascript", "null"]
            ),
            KnowledgeItem(
                knowledge_id="",
                knowledge_type=KnowledgeType.BEST_PRACTICE,
                title="代码质量最佳实践",
                content="编写高质量的代码需要遵循最佳实践",
                tags=["quality", "best_practice"]
            )
        ]
        
        for item in items:
            kb.add_knowledge(item)
        
        results = kb.search("空指针", mode=SearchMode.KEYWORD)
        
        return True, "知识检索测试成功", {
            "search_query": "空指针",
            "results_count": len(results),
            "search_mode": "keyword"
        }
    except Exception as e:
        return False, f"知识检索测试失败: {e}", {}


def test_knowledge_update():
    try:
        from analysis.knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeType, StorageType
        
        kb = KnowledgeBase(
            storage_path=TEST_DATA_DIR / "kb_update",
            storage_type=StorageType.SQLITE
        )
        
        item = KnowledgeItem(
            knowledge_id="",
            knowledge_type=KnowledgeType.DIAGNOSIS,
            title="性能问题诊断",
            content="分析性能瓶颈",
            tags=["performance"]
        )
        
        kid = kb.add_knowledge(item)
        
        updated = kb.update_knowledge(kid, {
            "content": "分析性能瓶颈，使用性能分析工具",
            "confidence_score": 0.9
        })
        
        assert updated is not None
        assert "性能分析工具" in updated.content
        assert updated.confidence_score == 0.9
        
        return True, "知识更新测试成功", {
            "knowledge_id": kid,
            "updated_content": updated.content[:50],
            "confidence": updated.confidence_score
        }
    except Exception as e:
        return False, f"知识更新测试失败: {e}", {}


def test_knowledge_deletion():
    try:
        from analysis.knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeType, StorageType
        
        kb = KnowledgeBase(
            storage_path=TEST_DATA_DIR / "kb_delete",
            storage_type=StorageType.SQLITE
        )
        
        item = KnowledgeItem(
            knowledge_id="",
            knowledge_type=KnowledgeType.CODE_PATTERN,
            title="待删除的知识",
            content="这个知识将被删除",
            tags=["temp"]
        )
        
        kid = kb.add_knowledge(item)
        
        result = kb.delete_knowledge(kid)
        assert result == True
        
        deleted = kb.get_knowledge(kid)
        assert deleted is None
        
        return True, "知识删除测试成功", {
            "deleted_knowledge_id": kid,
            "deletion_result": result
        }
    except Exception as e:
        return False, f"知识删除测试失败: {e}", {}


def test_knowledge_export_import():
    try:
        from analysis.knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeType, StorageType
        
        kb = KnowledgeBase(
            storage_path=TEST_DATA_DIR / "kb_export",
            storage_type=StorageType.SQLITE
        )
        
        item = KnowledgeItem(
            knowledge_id="",
            knowledge_type=KnowledgeType.FIX_PATTERN,
            title="导出测试知识",
            content="用于测试导出功能",
            tags=["export", "test"]
        )
        kb.add_knowledge(item)
        
        export_file = TEST_DATA_DIR / "export" / "knowledge_export.json"
        kb.export_knowledge(str(export_file))
        
        assert export_file.exists()
        
        kb2 = KnowledgeBase(
            storage_path=TEST_DATA_DIR / "kb_import",
            storage_type=StorageType.SQLITE
        )
        
        stats = kb2.import_knowledge(str(export_file))
        
        return True, "知识导入导出测试成功", {
            "export_file_exists": export_file.exists(),
            "import_stats": stats
        }
    except Exception as e:
        return False, f"知识导入导出测试失败: {e}", {}


def test_knowledge_statistics():
    try:
        from analysis.knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeType, StorageType
        
        kb = KnowledgeBase(
            storage_path=TEST_DATA_DIR / "kb_stats",
            storage_type=StorageType.SQLITE
        )
        
        for i in range(5):
            item = KnowledgeItem(
                knowledge_id="",
                knowledge_type=KnowledgeType.FIX_PATTERN if i % 2 == 0 else KnowledgeType.BEST_PRACTICE,
                title=f"统计测试知识 {i}",
                content=f"内容 {i}",
                tags=[f"tag{i}"]
            )
            kb.add_knowledge(item)
        
        stats = kb.get_statistics()
        
        assert "total_knowledge" in stats
        assert stats["total_knowledge"] >= 5
        
        return True, "知识统计测试成功", {
            "total_knowledge": stats["total_knowledge"],
            "by_type": stats.get("by_type", {})
        }
    except Exception as e:
        return False, f"知识统计测试失败: {e}", {}


def test_cross_project_knowledge_manager():
    try:
        from analysis.knowledge_base import CrossProjectKnowledgeManager
        
        manager = CrossProjectKnowledgeManager(base_path=TEST_DATA_DIR / "cross_project")
        manager.initialize()
        
        project = manager.register_project(
            project_id="test-proj-001",
            project_name="测试项目",
            project_path="/test/path"
        )
        
        assert project.project_id == "test-proj-001"
        
        kb = manager.get_knowledge_base("test-proj-001")
        assert kb is not None
        
        return True, "跨项目知识管理器测试成功", {
            "project_id": project.project_id,
            "has_knowledge_base": kb is not None
        }
    except Exception as e:
        return False, f"跨项目知识管理器测试失败: {e}", {}


def test_knowledge_index_manager():
    try:
        from analysis.knowledge_base import (
            KnowledgeBase,
            KnowledgeIndexManager,
            KnowledgeItem,
            KnowledgeType,
            StorageType
        )
        
        kb = KnowledgeBase(
            storage_path=TEST_DATA_DIR / "kb_index",
            storage_type=StorageType.SQLITE
        )
        
        for i in range(3):
            item = KnowledgeItem(
                knowledge_id=f"idx-item-{i}",
                knowledge_type=KnowledgeType.FIX_PATTERN,
                title=f"索引测试 {i}",
                content=f"索引测试内容 {i}",
                tags=[f"tag{i}", "index"]
            )
            kb.add_knowledge(item, auto_id=False)
        
        index_manager = KnowledgeIndexManager(kb)
        index_manager.build_fulltext_index()
        index_manager.build_tag_index()
        
        stats = index_manager.get_index_statistics()
        
        return True, "知识索引管理器测试成功", {
            "index_stats": stats
        }
    except Exception as e:
        return False, f"知识索引管理器测试失败: {e}", {}


def test_knowledge_update_manager():
    try:
        from analysis.knowledge_base import (
            KnowledgeBase,
            KnowledgeUpdateManager,
            KnowledgeItem,
            KnowledgeType,
            StorageType
        )
        
        kb = KnowledgeBase(
            storage_path=TEST_DATA_DIR / "kb_update_mgr",
            storage_type=StorageType.SQLITE
        )
        
        item = KnowledgeItem(
            knowledge_id="update-mgr-test",
            knowledge_type=KnowledgeType.FIX_PATTERN,
            title="更新管理器测试",
            content="原始内容",
            tags=["test"]
        )
        kb.add_knowledge(item, auto_id=False)
        
        update_mgr = KnowledgeUpdateManager(kb)
        
        batch = update_mgr.create_batch([
            {
                "knowledge_id": "update-mgr-test",
                "updates": {"content": "更新后的内容", "confidence_score": 0.8}
            }
        ])
        
        result = update_mgr.apply_batch(batch.batch_id)
        
        return True, "知识更新管理器测试成功", {
            "batch_id": batch.batch_id,
            "apply_result": result
        }
    except Exception as e:
        return False, f"知识更新管理器测试失败: {e}", {}


def test_knowledge_learning():
    try:
        from analysis.knowledge_base import (
            KnowledgeBase,
            KnowledgeItem,
            KnowledgeType,
            StorageType
        )
        
        kb = KnowledgeBase(
            storage_path=TEST_DATA_DIR / "kb_learning",
            storage_type=StorageType.SQLITE
        )
        
        item = KnowledgeItem(
            knowledge_id="learning-test",
            knowledge_type=KnowledgeType.FIX_PATTERN,
            title="学习测试知识",
            content="用于测试学习功能",
            tags=["learning"]
        )
        kb.add_knowledge(item, auto_id=False)
        
        kb.record_usage("learning-test", success=True)
        kb.record_usage("learning-test", success=True)
        kb.record_usage("learning-test", success=False)
        
        updated = kb.get_knowledge("learning-test")
        
        return True, "知识学习测试成功", {
            "usage_count": updated.usage_count if updated else 0,
            "success_rate": updated.success_rate if updated else 0
        }
    except Exception as e:
        return False, f"知识学习测试失败: {e}", {}


def test_knowledge_versioning():
    try:
        from analysis.knowledge_base import (
            KnowledgeBase,
            KnowledgeItem,
            KnowledgeType,
            StorageType
        )
        
        kb = KnowledgeBase(
            storage_path=TEST_DATA_DIR / "kb_version",
            storage_type=StorageType.SQLITE
        )
        
        item = KnowledgeItem(
            knowledge_id="version-test",
            knowledge_type=KnowledgeType.BEST_PRACTICE,
            title="版本测试",
            content="版本1",
            tags=["version"]
        )
        kb.add_knowledge(item, auto_id=False)
        
        kb.update_knowledge("version-test", {"content": "版本2"})
        kb.update_knowledge("version-test", {"content": "版本3"})
        
        versions = kb.get_version_history("version-test")
        
        return True, "知识版本控制测试成功", {
            "version_count": len(versions),
            "has_versions": len(versions) > 0
        }
    except Exception as e:
        return False, f"知识版本控制测试失败: {e}", {}


def run_knowledge_base_tests():
    print_header("知识库功能测试")
    
    cleanup_test_data()
    
    runner = TestRunner()
    
    tests = [
        ("模块导入测试", test_knowledge_base_import),
        ("知识项创建测试", test_knowledge_item_creation),
        ("知识库初始化测试", test_knowledge_base_initialization),
        ("知识存储测试", test_knowledge_storage),
        ("知识检索测试", test_knowledge_search),
        ("知识更新测试", test_knowledge_update),
        ("知识删除测试", test_knowledge_deletion),
        ("知识导入导出测试", test_knowledge_export_import),
        ("知识统计测试", test_knowledge_statistics),
        ("跨项目知识管理器测试", test_cross_project_knowledge_manager),
        ("知识索引管理器测试", test_knowledge_index_manager),
        ("知识更新管理器测试", test_knowledge_update_manager),
        ("知识学习测试", test_knowledge_learning),
        ("知识版本控制测试", test_knowledge_versioning),
    ]
    
    for test_name, test_func in tests:
        result = runner.run_test(test_func, "知识库功能", test_name)
        print_result(result)
        runner.report.add_result(result)
    
    return runner.finalize()


if __name__ == "__main__":
    report = run_knowledge_base_tests()
    print(f"\n测试完成: {report.passed}/{report.total_tests} 通过")
