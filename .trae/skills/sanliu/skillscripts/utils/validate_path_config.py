#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径配置验证脚本

验证三省六部技能的输出路径配置是否正确
"""

import sys
from pathlib import Path

from skillscripts.core.path_config_center import get_path_config

sys.path.insert(0, str(get_path_config().SKILL_ROOT.parent))

from skillscripts.utils.path_config_manager import PathConfigManager, PathMode


def validate_path_config():
    """验证路径配置"""
    print("=" * 80)
    print("三省六部技能 - 路径配置验证")
    print("=" * 80)
    print()
    
    manager = PathConfigManager()
    
    print(f"运行模式: {manager.mode.value}")
    print(f"基础路径: {manager.get_base_path()}")
    print()
    
    print("-" * 80)
    print("核心路径配置:")
    print("-" * 80)
    
    paths = {
        "文档目录": manager.get_docs_path(),
        "文档库目录": manager.get_docs_libs_path(),
        "文档报告目录": manager.get_docs_reports_path(),
        "迭代版本目录": manager.get_docs_iteration_path(),
        "测试目录": manager.get_tests_path(),
        "技能脚本目录": manager.get_skillscripts_path(),
        "临时目录": manager.get_temp_path(),
        "缓存目录": manager.get_cache_path(),
        "数据目录": manager.get_data_path(),
        "配置目录": manager.get_config_path(),
        "报告目录": manager.get_reports_path(),
        "日志目录": manager.get_logs_path(),
        "后端目录": manager.get_backend_path(),
        "前端目录": manager.get_frontend_path(),
    }
    
    for name, path in paths.items():
        exists = "✅" if path.exists() else "❌"
        print(f"{exists} {name:15s}: {path}")
    
    print()
    print("-" * 80)
    print("迭代版本路径验证:")
    print("-" * 80)
    
    version = "v3.0.0"
    iteration_path = manager.get_docs_iteration_path(version)
    print(f"迭代版本目录 (v3.0.0): {iteration_path}")
    print(f"目录存在: {'✅ 是' if iteration_path.exists() else '❌ 否'}")
    
    if iteration_path.exists():
        print("\n迭代版本文件列表:")
        for file in iteration_path.iterdir():
            print(f"  - {file.name}")
    
    print()
    print("-" * 80)
    print("迭代版本报告路径验证:")
    print("-" * 80)
    
    report_types = ["测试报告", "功能分析报告", "路径验证报告", "质量报告"]
    for report_type in report_types:
        report_path = manager.get_iteration_report_path(version, report_type)
        exists = "✅" if report_path.exists() else "❌"
        print(f"{exists} {report_type:15s}: {report_path}")
    
    print()
    print("-" * 80)
    print("配置完整性验证:")
    print("-" * 80)
    
    config = manager.config
    print(f"✅ docs_libs_path: {config.docs_libs_path}")
    print(f"✅ docs_reports_path: {config.docs_reports_path}")
    print(f"✅ docs_iteration_path: {config.docs_iteration_path}")
    print(f"✅ tests_path: {config.tests_path}")
    print(f"✅ skillscripts_path: {config.skillscripts_path}")
    print(f"✅ reports_path: {config.reports_path}")
    print(f"✅ logs_path: {config.logs_path}")
    
    print()
    print("=" * 80)
    print("验证完成！")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        success = validate_path_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
