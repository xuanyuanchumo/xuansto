#!/usr/bin/env python3
"""
版本迭代器测试脚本
测试语义化版本自动升级、变更日志自动生成、版本快照自动创建、版本回滚机制
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(get_path_config().SKILL_ROOT.parent))

try:
    from skillscripts.core.version_iterator import (
        VersionIterator,
        VersionBumpType,
        ChangeType,
        ChangeEntry,
        SemanticVersion,
        VersionRange
    )
    from skillscripts.core.auto_iterator import (
        AutoIterator,
        IterationTriggerDetector,
        IterationTriggerType
    )
except ImportError:
    from version_iterator import (
        VersionIterator,
        VersionBumpType,
        ChangeType,
        ChangeEntry,
        SemanticVersion,
        VersionRange
    )
    from auto_iterator import (
        AutoIterator,
        IterationTriggerDetector,
        IterationTriggerType
    )


def test_semantic_version():
    """测试语义化版本"""
    print("\n=== 测试语义化版本 ===")
    
    v1 = SemanticVersion.parse("1.2.3")
    assert str(v1) == "1.2.3"
    print(f"✓ 版本解析: {v1}")
    
    v2 = SemanticVersion.parse("2.0.0-alpha.1")
    assert v2.prerelease == "alpha.1"
    print(f"✓ 预发布版本: {v2}")
    
    v3 = SemanticVersion.parse("1.2.3+build.123")
    assert v3.build_metadata == "build.123"
    print(f"✓ 构建元数据: {v3}")
    
    v4 = v1.bump(VersionBumpType.MAJOR)
    assert str(v4) == "2.0.0"
    print(f"✓ 主版本升级: {v1} -> {v4}")
    
    v5 = v1.bump(VersionBumpType.MINOR)
    assert str(v5) == "1.3.0"
    print(f"✓ 次版本升级: {v1} -> {v5}")
    
    v6 = v1.bump(VersionBumpType.PATCH)
    assert str(v6) == "1.2.4"
    print(f"✓ 修订版本升级: {v1} -> {v6}")
    
    print("✓ 语义化版本测试通过")


def test_version_range():
    """测试版本范围"""
    print("\n=== 测试版本范围 ===")
    
    range1 = VersionRange.parse(">=1.0.0,<2.0.0")
    v1 = SemanticVersion.parse("1.5.0")
    v2 = SemanticVersion.parse("2.0.0")
    
    assert range1.matches(v1) == True
    assert range1.matches(v2) == False
    print(f"✓ 版本范围匹配: {range1.description}")
    
    range2 = VersionRange.parse("^1.2.3")
    v3 = SemanticVersion.parse("1.3.0")
    v4 = SemanticVersion.parse("2.0.0")
    
    assert range2.matches(v3) == True
    assert range2.matches(v4) == False
    print(f"✓ 插入符号范围: {range2.description}")
    
    print("✓ 版本范围测试通过")


def test_version_iterator():
    """测试版本迭代器"""
    print("\n=== 测试版本迭代器 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        test_file = project_root / "test.py"
        test_file.write_text("print('hello')")
        
        vi = VersionIterator(str(project_root))
        
        current = vi.get_current_version()
        assert str(current) == "0.0.0"
        print(f"✓ 初始版本: {current}")
        
        changes = [
            ChangeEntry(
                change_type=ChangeType.FEATURE,
                description="添加新功能",
                scope="core"
            ),
            ChangeEntry(
                change_type=ChangeType.FIX,
                description="修复bug",
                scope="utils"
            )
        ]
        
        entry = vi.iterate(
            bump_type=VersionBumpType.MINOR,
            changes=changes,
            author="Test User",
            notes="测试版本迭代"
        )
        
        assert entry.version == "0.1.0"
        assert len(entry.changes) == 2
        print(f"✓ 版本迭代: {entry.previous_version} -> {entry.version}")
        
        assert len(vi.history.snapshots) == 1
        print(f"✓ 快照创建: {vi.history.snapshots[0].snapshot_id}")
        
        assert vi.changelog_file.exists()
        changelog = vi.changelog_file.read_text(encoding='utf-8')
        assert "0.1.0" in changelog
        print(f"✓ 变更日志生成")
        
        entry2 = vi.iterate(
            bump_type=VersionBumpType.PATCH,
            changes=[ChangeEntry(
                change_type=ChangeType.FIX,
                description="另一个修复"
            )],
            author="Test User"
        )
        
        assert entry2.version == "0.1.1"
        print(f"✓ 版本迭代: {entry2.previous_version} -> {entry2.version}")
        
        stats_before = vi.calculate_statistics()
        assert stats_before.total_versions == 2
        print(f"✓ 统计信息: 总版本数 {stats_before.total_versions}")
        
        assert vi.rollback_version("0.1.0")
        assert vi.history.current_version == "0.1.0"
        print(f"✓ 版本回滚: {vi.history.current_version}")
        
        status = vi.get_status()
        assert status["current_version"] == "0.1.0"
        assert status["iteration_count"] == 2
        print(f"✓ 状态查询: 迭代次数 {status['iteration_count']}")
        
        stats_after = vi.calculate_statistics()
        assert stats_after.total_versions >= 1
        print(f"✓ 回滚后统计: 总版本数 {stats_after.total_versions}")
        
        print("✓ 版本迭代器测试通过")


def test_auto_iterator():
    """测试自动迭代器"""
    print("\n=== 测试自动迭代器 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        test_file = project_root / "test.py"
        test_file.write_text("print('hello')")
        
        ai = AutoIterator(str(project_root))
        
        metrics = {
            'error_rate': 0.08,
            'continuous_failures': 0,
            'code_quality_score': 0.85,
            'test_failure_rate': 0.02
        }
        
        result = ai.check_iteration_needed(metrics)
        assert result['needs_iteration'] == True
        assert len(result['triggered_conditions']) > 0
        print(f"✓ 触发条件检测: {len(result['triggered_conditions'])} 个条件触发")
        
        metrics2 = {
            'error_rate': 0.03,
            'continuous_failures': 0,
            'code_quality_score': 0.95,
            'test_failure_rate': 0.01
        }
        
        result2 = ai.check_iteration_needed(metrics2)
        assert result2['needs_iteration'] == False
        print(f"✓ 无触发条件")
        
        changes = [
            ChangeEntry(
                change_type=ChangeType.FEATURE,
                description="智能功能"
            )
        ]
        
        entry = ai.smart_iterate(changes, author="Auto Test")
        assert entry.version == "0.1.0"
        print(f"✓ 智能迭代: {entry.version}")
        
        status = ai.get_iteration_status()
        assert status["auto_iteration_enabled"] == True
        print(f"✓ 自动迭代状态: 启用")
        
        print("✓ 自动迭代器测试通过")


def test_changelog_generation():
    """测试变更日志生成"""
    print("\n=== 测试变更日志生成 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        vi = VersionIterator(str(project_root))
        
        changes = [
            ChangeEntry(
                change_type=ChangeType.FEATURE,
                description="新功能1",
                scope="api"
            ),
            ChangeEntry(
                change_type=ChangeType.FIX,
                description="修复bug1",
                breaking=True
            ),
            ChangeEntry(
                change_type=ChangeType.DOCS,
                description="更新文档"
            )
        ]
        
        vi.iterate(
            bump_type=VersionBumpType.MINOR,
            changes=changes,
            author="Test User",
            notes="测试变更日志"
        )
        
        changelog = vi.changelog_generator.generate()
        
        assert "新功能" in changelog
        assert "Bug修复" in changelog
        assert "文档" in changelog
        print(f"✓ 变更日志包含所有变更类型")
        
        release_notes = vi.changelog_generator.generate_release_notes("0.1.0")
        assert "发布说明" in release_notes
        print(f"✓ 发布说明生成")
        
        print("✓ 变更日志生成测试通过")


def test_snapshot_management():
    """测试快照管理"""
    print("\n=== 测试快照管理 ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        test_file = project_root / "test.py"
        test_file.write_text("print('version 1')")
        
        vi = VersionIterator(str(project_root))
        
        snapshot1 = vi.create_snapshot("0.0.0", "初始快照")
        assert snapshot1.snapshot_id.startswith("SNAP-")
        print(f"✓ 创建快照: {snapshot1.snapshot_id}")
        
        test_file.write_text("print('version 2')")
        
        snapshot2 = vi.create_snapshot("0.1.0", "第二个快照")
        print(f"✓ 创建快照: {snapshot2.snapshot_id}")
        
        snapshots = vi.list_snapshots()
        assert len(snapshots) == 2
        print(f"✓ 快照列表: {len(snapshots)} 个快照")
        
        assert vi.restore_snapshot(snapshot1.snapshot_id)
        restored_content = test_file.read_text()
        assert "version 1" in restored_content
        print(f"✓ 快照恢复成功")
        
        print("✓ 快照管理测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始运行版本迭代器测试")
    print("="*60)
    
    try:
        test_semantic_version()
        test_version_range()
        test_version_iterator()
        test_auto_iterator()
        test_changelog_generation()
        test_snapshot_management()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)
        
        return True
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
from skillscripts.core.path_config_center import get_path_config
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
