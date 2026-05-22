#!/usr/bin/env python3
"""精确的嵌套分析 - 只分析核心业务代码"""

import os
import re
from pathlib import Path


def count_real_nesting(lines, start_idx):
    """计算真实的嵌套层级"""
    nesting = 0
    max_nesting = 0
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        stripped = line.strip()
        
        if not stripped or stripped.startswith('#'):
            continue
        
        if any(kw in stripped for kw in ['if ', 'elif ', 'else:', 'for ', 'while ', 'with ', 'try:', 'except ', 'finally:']):
            nesting += 1
            max_nesting = max(max_nesting, nesting)
        
        if stripped.endswith(':') and i > start_idx:
            pass
        
        if stripped in ['}', 'endif', 'endfor', 'endwhile']:
            nesting -= 1
    
    return max_nesting


def analyze_file_deep_nesting(file_path):
    """分析文件中的深层嵌套"""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except:
        return issues
    
    nesting_stack = []
    function_name = ""
    
    for line_num, line in enumerate(lines, 1):
        stripped = line.lstrip()
        
        if not stripped or stripped.startswith('#'):
            continue
        
        indent = len(line) - len(stripped)
        
        if re.match(r'^\s*(def |async def )', line):
            match = re.search(r'def (\w+)', line)
            function_name = match.group(1) if match else ""
        
        control_keywords = ['if ', 'elif ', 'else:', 'for ', 'while ', 'with ', 'try:', 'except ', 'finally:']
        is_control = False
        
        for keyword in control_keywords:
            if keyword in stripped and stripped.endswith(':'):
                is_control = True
                break
        
        if is_control:
            while nesting_stack and indent <= nesting_stack[-1][1]:
                nesting_stack.pop()
            
            nesting_stack.append((line_num, indent, stripped[:60]))
            current_nesting = len(nesting_stack)
            
            if current_nesting > 3:
                issues.append({
                    'file': file_path,
                    'line': line_num,
                    'level': current_nesting,
                    'code': stripped[:80],
                    'function': function_name
                })
    
    return issues


def main():
    base_dir = Path(__file__).parent.parent / "backend" / "app"
    all_issues = []
    
    print("分析核心业务代码嵌套层级...")
    print("=" * 80)
    
    for py_file in sorted(base_dir.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        
        issues = analyze_file_deep_nesting(str(py_file))
        if issues:
            all_issues.extend(issues)
            print(f"\n📁 {py_file.relative_to(base_dir.parent.parent)}")
            for issue in issues:
                print(f"  第 {issue['line']} 行 (嵌套层级: {issue['level']})")
                if issue['function']:
                    print(f"    函数: {issue['function']}")
                print(f"    代码: {issue['code']}")
    
    print("\n" + "=" * 80)
    if not all_issues:
        print("✅ 所有核心业务代码的嵌套层级都符合要求（≤3层）")
    else:
        print(f"⚠️  发现 {len(all_issues)} 处深层嵌套问题需要优化")
        print("\n优化建议：")
        print("1. 使用早返回（Guard Clause）减少嵌套")
        print("2. 提取复杂逻辑到独立函数")
        print("3. 使用策略模式替代多层if-else")
        print("4. 使用对象映射替代switch/if-else")
    
    return len(all_issues)


if __name__ == "__main__":
    exit(main())
