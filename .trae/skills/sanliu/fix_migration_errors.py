#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复迁移脚本导致的语法错误
"""

from pathlib import Path
import re

SKILLSCRIPTS_DIR = Path(r'd:\Projects\TraeProjects\skiller\.trae\skills\sanliu\skillscripts')

def fix_extra_parenthesis(content: str) -> str:
    """修复多余的右括号问题
    
    模式: get_path_config().REPORTS_DIR / "xxx")  ->  get_path_config().REPORTS_DIR / "xxx"
    """
    # 匹配 REPORTS_DIR / "xxx") 这种模式（末尾多了一个右括号）
    pattern = r"get_path_config\(\)\.REPORTS_DIR\s*/\s*['\"]([^'\"]*)['\"]\)"
    
    def replace_func(match):
        path = match.group(1)
        return f'get_path_config().REPORTS_DIR / "{path}"'
    
    content = re.sub(pattern, replace_func, content)
    return content


def fix_ui_validation_error(content: str) -> str:
    """修复 ui_validation_intelligence.py 的特殊错误"""
    # 修复: Path(config.get(', str(get_path_config().REPORTS_DIR / 'ui_validation')))
    # 正确应该是: Path(config.get('output', str(get_path_config().REPORTS_DIR / 'ui_validation')))
    
    error_pattern = r"Path\(config\.get\(\',\s*str\(get_path_config\(\)\.REPORTS_DIR\s*/\s*['\"]([^'\"]*)['\"]\)\)\)"
    
    def replace_func(match):
        subdir = match.group(1)
        return f"Path(config.get('output', str(get_path_config().REPORTS_DIR / '{subdir}')))"
    
    content = re.sub(error_pattern, replace_func, content)
    return content


def fix_auto_optimizer(content: str) -> str:
    """修复 auto_optimizer.py 的原有语法错误"""
    # 原来的错误代码: sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    # 缺少一个右括号
    
    error_pattern = r"sys\.path\.insert\(0,\s*os\.path\.dirname\(os\.path\.dirname\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)\)"
    
    def replace_func(match):
        return 'sys.path.insert(0, str(get_path_config().SKILL_ROOT))'
    
    content = re.sub(error_pattern, replace_func, content)
    return content


def process_file(file_path: Path):
    """处理单个文件"""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        original_content = content
        
        # 应用所有修复
        content = fix_extra_parenthesis(content)
        content = fix_ui_validation_error(content)
        content = fix_auto_optimizer(content)
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            print(f"[FIXED] {file_path.relative_to(SKILLSCRIPTS_DIR)}")
            return True
        else:
            print(f"[NO CHANGE] {file_path.relative_to(SKILLSCRIPTS_DIR)}")
            return False
            
    except Exception as e:
        print(f"[ERROR] {file_path.relative_to(SKILLSCRIPTS_DIR)}: {e}")
        return False


def main():
    """主函数"""
    print("=" * 80)
    print("Fixing syntax errors from migration")
    print("=" * 80)
    
    # 已知有问题的文件列表
    problem_files = [
        SKILLSCRIPTS_DIR / 'analysis' / 'department_logic_checker.py',
        SKILLSCRIPTS_DIR / 'analysis' / 'provincial_logic_checker.py',
        SKILLSCRIPTS_DIR / 'analysis' / 'skill_call_chain_checker.py',
        SKILLSCRIPTS_DIR / 'core' / 'auto_optimizer.py',
        SKILLSCRIPTS_DIR / 'core' / 'department_logic_checker.py',
        SKILLSCRIPTS_DIR / 'core' / 'skill_call_chain_checker.py',
        SKILLSCRIPTS_DIR / 'pipeline' / 'pipeline_intelligence.py',
        SKILLSCRIPTS_DIR / 'pipeline' / 'sdd_tdd_fusion_engine.py',
        SKILLSCRIPTS_DIR / 'pipeline' / 'skill_creator_integration.py',
        SKILLSCRIPTS_DIR / 'pipeline' / 'ui_ux_integration.py',
        SKILLSCRIPTS_DIR / 'pipeline' / 'ui_validation_intelligence.py',
    ]
    
    fixed_count = 0
    for file_path in problem_files:
        if file_path.exists():
            if process_file(file_path):
                fixed_count += 1
    
    print(f"\n{'=' * 80}")
    print(f"Fixed {fixed_count} files")
    print("=" * 80)


if __name__ == '__main__':
    main()
