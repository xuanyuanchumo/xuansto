#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版路径配置管理器使用示例

演示如何使用 EnhancedSkillPathManager 管理技能路径配置
"""

import json
import os
from pathlib import Path

try:
    from enhanced_path_config_manager import (
        EnhancedSkillPathManager,
        PathKey,
        EnvironmentVariableManager,
        create_path_manager
    )
except ImportError:
    from .enhanced_path_config_manager import (
        EnhancedSkillPathManager,
        PathKey,
        EnvironmentVariableManager,
        create_path_manager
    )


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("基本使用示例")
    print("=" * 60)
    
    manager = create_path_manager()
    
    print(f"\n技能根目录: {manager.skill_root}")
    
    print("\n路径配置:")
    for path_key in PathKey:
        path = manager.resolve_path(path_key)
        exists = "✓" if path.exists() else "✗"
        print(f"  {exists} {path_key.value:30s} -> {path}")
    
    print()


def example_subskills():
    """子技能管理示例"""
    print("=" * 60)
    print("子技能管理示例")
    print("=" * 60)
    
    manager = create_path_manager()
    
    subskills = manager.get_all_subskills()
    
    print(f"\n找到 {len(subskills)} 个子技能:")
    for subskill in subskills[:5]:
        print(f"  - {subskill.name}")
        print(f"    路径: {subskill.path}")
        print(f"    大小: {subskill.size} 字节")
        print(f"    修改时间: {subskill.last_modified}")
    
    if len(subskills) > 5:
        print(f"  ... 还有 {len(subskills) - 5} 个子技能")
    
    print()


def example_script_paths():
    """脚本路径管理示例"""
    print("=" * 60)
    print("脚本路径管理示例")
    print("=" * 60)
    
    manager = create_path_manager()
    
    script_types = ["core", "pipeline", "test", "analysis", "optimization", "requirements", "utils", "monitoring"]
    
    print("\n脚本路径示例:")
    for script_type in script_types:
        script_path = manager.get_script_path("example_script", script_type)
        print(f"  {script_type:15s} -> {script_path}")
    
    print()


def example_environment_variables():
    """环境变量示例"""
    print("=" * 60)
    print("环境变量示例")
    print("=" * 60)
    
    print("\n设置环境变量覆盖:")
    EnvironmentVariableManager.set_env_override(PathKey.DATA_DIR, "/custom/data/path")
    print(f"  设置 SANLIU_DATA_DIR = /custom/data/path")
    
    env_value = EnvironmentVariableManager.get_env_override(PathKey.DATA_DIR)
    print(f"  获取环境变量: {env_value}")
    
    all_overrides = EnvironmentVariableManager.get_all_env_overrides()
    print(f"\n所有环境变量覆盖: {json.dumps(all_overrides, indent=2)}")
    
    EnvironmentVariableManager.clear_env_override(PathKey.DATA_DIR)
    print("\n清除环境变量覆盖")
    
    print()


def example_workspace_management():
    """工作空间管理示例"""
    print("=" * 60)
    print("工作空间管理示例")
    print("=" * 60)
    
    manager = create_path_manager()
    
    print("\n初始化工作空间:")
    result = manager.initialize_workspace(verify=True, lazy=True)
    print(f"  技能根目录: {result['skill_root']}")
    print(f"  懒加载模式: {result['lazy_mode']}")
    
    print("\n验证工作空间:")
    validation = manager.validate_workspace()
    print(f"  验证结果: {'有效' if validation['valid'] else '无效'}")
    if validation['errors']:
        print(f"  错误: {validation['errors']}")
    if validation['warnings']:
        print(f"  警告: {validation['warnings']}")
    
    print("\n工作空间信息:")
    info = manager.get_workspace_info()
    print(f"  健康分数: {info['health_score']:.1f}")
    print(f"  子技能数量: {info['subskills_count']}")
    
    print()


def example_path_operations():
    """路径操作示例"""
    print("=" * 60)
    print("路径操作示例")
    print("=" * 60)
    
    manager = create_path_manager()
    
    print("\n路径解析:")
    skill_root = manager.resolve_path(PathKey.SKILL_ROOT)
    print(f"  技能根目录: {skill_root}")
    
    subskills_dir = manager.resolve_path("subskills")
    print(f"  子技能目录: {subskills_dir}")
    
    print("\n相对路径转换:")
    absolute_path = manager.skill_root / "skillscripts" / "utils" / "test.py"
    relative_path = manager.get_relative_path(absolute_path)
    print(f"  绝对路径: {absolute_path}")
    print(f"  相对路径: {relative_path}")
    
    print("\n绝对路径转换:")
    relative = "docs/reports/test.md"
    absolute = manager.to_absolute_path(relative)
    print(f"  相对路径: {relative}")
    print(f"  绝对路径: {absolute}")
    
    print("\n路径验证:")
    valid, error = manager.validate_path(manager.skill_root)
    print(f"  技能根目录: {'有效' if valid else '无效'}")
    if error:
        print(f"  错误: {error}")
    
    print("\n确保路径存在:")
    data_dir = manager.ensure_path(PathKey.DATA_DIR)
    print(f"  数据目录: {data_dir}")
    print(f"  是否存在: {data_dir.exists()}")
    
    print()


def example_config_export():
    """配置导出示例"""
    print("=" * 60)
    print("配置导出示例")
    print("=" * 60)
    
    manager = create_path_manager()
    
    print("\n导出配置:")
    config = manager.export_config()
    print(json.dumps(config, indent=2, ensure_ascii=False))
    
    print()


def example_health_check():
    """健康检查示例"""
    print("=" * 60)
    print("健康检查示例")
    print("=" * 60)
    
    manager = create_path_manager()
    
    print("\n执行健康检查:")
    report = manager.health_checker.perform_health_check()
    
    print(f"  总目录数: {report.total_directories}")
    print(f"  存在目录数: {report.existing_directories}")
    print(f"  缺失目录数: {report.missing_directories}")
    print(f"  无效目录数: {report.invalid_directories}")
    print(f"  健康分数: {report.health_score:.1f}")
    
    if report.recommendations:
        print("\n建议:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")
    
    print()


def example_snapshot():
    """快照示例"""
    print("=" * 60)
    print("快照示例")
    print("=" * 60)
    
    manager = create_path_manager()
    
    print("\n创建快照:")
    snapshot = manager.create_snapshot("example_snapshot")
    print(f"  快照ID: {snapshot.snapshot_id}")
    print(f"  文件数: {snapshot.file_count}")
    print(f"  总大小: {snapshot.total_size} 字节")
    
    print("\n列出所有快照:")
    snapshots = manager.snapshot_manager.list_snapshots()
    for snap in snapshots[:3]:
        print(f"  - {snap['snapshot_id']} ({snap['timestamp']})")
    
    print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("增强版路径配置管理器使用示例")
    print("=" * 60 + "\n")
    
    try:
        example_basic_usage()
        example_subskills()
        example_script_paths()
        example_environment_variables()
        example_workspace_management()
        example_path_operations()
        example_config_export()
        example_health_check()
        example_snapshot()
        
        print("=" * 60)
        print("所有示例执行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
