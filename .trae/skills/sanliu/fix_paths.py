#!/usr/bin/env python3
"""
批量修复技能文档中的脚本路径引用
"""
import re
import os
from pathlib import Path

PATH_MAPPINGS = {
    'self_iteration.md': {
        'skillscripts/version_iterator.py': 'backend/scripts/version_iterator.py',
        'skillscripts/rollback_manager.py': 'backend/scripts/rollback_manager.py',
        'skillscripts/auto_fixer.py': 'backend/scripts/auto_fixer.py',
        'skillscripts/log_analyzer.py': 'backend/scripts/log_analyzer.py',
        'skillscripts/issue_locator.py': 'backend/scripts/issue_locator.py',
        'skillscripts/skill_caller.py': 'skillscripts/utils/skill_caller.py',
        'skillscripts/skill_registry.py': 'skillscripts/utils/skill_registry.py',
        'skillscripts/interface_validator.py': 'skillscripts/utils/interface_validator.py',
        'skillscripts/self_iterate.py': 'skillscripts/utils/self_iterate.py',
        'skillscripts/iteration_coordinator.py': 'skillscripts/utils/iteration_coordinator.py',
        'skillscripts/skill_content_updater.py': 'skillscripts/utils/skill_content_updater.py',
        'skillscripts/doc_updater.py': 'skillscripts/utils/doc_updater.py',
        'skillscripts/self_optimizer.py': 'skillscripts/utils/self_optimizer.py',
        'skillscripts/self_healer.py': 'skillscripts/utils/self_healer.py',
        'skillscripts/self_improver.py': 'skillscripts/utils/self_improver.py',
    },
    'continuous_evolution.md': {
        'skillscripts/evolution_manager.py': 'skillscripts/utils/evolution_manager.py',
        'skillscripts/continuous_evolution_controller.py': 'skillscripts/utils/continuous_evolution_controller.py',
        'skillscripts/skill_evolution_manager.py': 'skillscripts/utils/skill_evolution_manager.py',
    },
    'knowledge_base.md': {
        'skillscripts/knowledge_manager.py': 'skillscripts/utils/knowledge_manager.py',
        'skillscripts/knowledge_learner.py': 'skillscripts/utils/knowledge_learner.py',
        'skillscripts/knowledge_sharing.py': 'skillscripts/utils/knowledge_sharing.py',
        'skillscripts/knowledge_quality.py': 'skillscripts/utils/knowledge_quality.py',
    },
    'baihehua_liushuixian.md': {
        'skillscripts/validate_specs.py': 'skillscripts/utils/validate_specs.py',
        'skillscripts/check_db_connection.py': 'skillscripts/utils/check_db_connection.py',
        'skillscripts/check_dependencies.py': 'skillscripts/utils/check_dependencies.py',
        'skillscripts/init_test_data.py': 'skillscripts/utils/init_test_data.py',
    },
    'daima_chonggou.md': {
        'skillscripts/code_review_automation.py': 'skillscripts/utils/code_review_automation.py',
    },
    'skill_path_management.md': {
        'skillscripts/path_migration_tool.py': 'skillscripts/utils/path_migration_tool.py',
    },
    'skill_script_coordination.md': {
        'skillscripts/core/skill_caller.py': 'skillscripts/utils/skill_caller.py',
        'skillscripts/core/call_tracer.py': 'skillscripts/utils/call_tracer.py',
    },
}

def fix_file_paths(file_path, mappings):
    """修复单个文件中的路径引用"""
    print(f"正在修复: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  读取文件失败: {e}")
        return 0
    
    original_content = content
    fix_count = 0
    
    for old_path, new_path in mappings.items():
        if old_path in content:
            count = content.count(old_path)
            content = content.replace(old_path, new_path)
            fix_count += count
            print(f"  替换: {old_path} -> {new_path} ({count} 处)")
    
    if fix_count > 0:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ 已修复 {fix_count} 处路径引用")
        except Exception as e:
            print(f"  写入文件失败: {e}")
            return 0
    else:
        print(f"  无需修复")
    
    return fix_count

def main():
    """主函数"""
    base_dir = Path(__file__).parent
    subskills_dir = base_dir / 'subskills'
    
    total_fixes = 0
    
    print("=" * 60)
    print("开始批量修复路径引用")
    print("=" * 60)
    
    for doc_name, mappings in PATH_MAPPINGS.items():
        doc_path = subskills_dir / doc_name
        if doc_path.exists():
            fixes = fix_file_paths(doc_path, mappings)
            total_fixes += fixes
        else:
            print(f"文件不存在: {doc_path}")
        print()
    
    print("=" * 60)
    print(f"修复完成！共修复 {total_fixes} 处路径引用")
    print("=" * 60)

if __name__ == '__main__':
    main()
