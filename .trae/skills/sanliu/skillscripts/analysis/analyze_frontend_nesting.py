#!/usr/bin/env python3
"""分析前端代码嵌套层级"""

import os
import re
from pathlib import Path


def analyze_frontend_file(file_path):
    """分析前端文件的嵌套层级"""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except:
        return issues
    
    brace_stack = []
    function_name = ""
    in_template = False
    
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        
        if not stripped or stripped.startswith('//') or stripped.startswith('*'):
            continue
        
        if '<template>' in stripped:
            in_template = True
        elif '</template>' in stripped:
            in_template = False
        
        if in_template:
            continue
        
        func_match = re.search(r'(function\s+(\w+)|const\s+(\w+)\s*=.*=>|(\w+)\s*\([^)]*\)\s*{)', line)
        if func_match:
            function_name = func_match.group(2) or func_match.group(3) or func_match.group(4) or ""
        
        for i, char in enumerate(line):
            if char == '{':
                brace_stack.append((line_num, len(brace_stack) + 1, stripped[:60]))
                current_nesting = len(brace_stack)
                
                if current_nesting > 3:
                    issues.append({
                        'file': file_path,
                        'line': line_num,
                        'level': current_nesting,
                        'code': stripped[:80],
                        'function': function_name
                    })
            elif char == '}':
                if brace_stack:
                    brace_stack.pop()
    
    return issues


def main():
    base_dir = Path(__file__).parent.parent / "frontend" / "src"
    all_issues = []
    
    print("分析前端代码嵌套层级...")
    print("=" * 80)
    
    for file_path in sorted(base_dir.rglob("*.ts")):
        if "node_modules" in str(file_path):
            continue
        
        issues = analyze_frontend_file(str(file_path))
        if issues:
            all_issues.extend(issues)
            print(f"\n📁 {file_path.relative_to(base_dir.parent.parent)}")
            for issue in issues:
                print(f"  第 {issue['line']} 行 (嵌套层级: {issue['level']})")
                if issue['function']:
                    print(f"    函数: {issue['function']}")
                print(f"    代码: {issue['code']}")
    
    for file_path in sorted(base_dir.rglob("*.vue")):
        issues = analyze_frontend_file(str(file_path))
        if issues:
            all_issues.extend(issues)
            print(f"\n📁 {file_path.relative_to(base_dir.parent.parent)}")
            for issue in issues:
                print(f"  第 {issue['line']} 行 (嵌套层级: {issue['level']})")
                if issue['function']:
                    print(f"    函数: {issue['function']}")
                print(f"    代码: {issue['code']}")
    
    print("\n" + "=" * 80)
    if not all_issues:
        print("✅ 所有前端代码的嵌套层级都符合要求（≤3层）")
    else:
        print(f"⚠️  发现 {len(all_issues)} 处深层嵌套问题需要优化")
        print("\n优化建议：")
        print("1. 提取复杂逻辑到独立函数")
        print("2. 使用策略模式替代多层if-else")
        print("3. 使用对象映射替代switch/if-else")
        print("4. 使用函数组合减少嵌套")
    
    return len(all_issues)


if __name__ == "__main__":
    exit(main())
