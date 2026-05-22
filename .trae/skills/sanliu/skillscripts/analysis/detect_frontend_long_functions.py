#!/usr/bin/env python3
"""检测前端TypeScript/Vue过长函数的脚本"""
import re
import sys
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(get_path_config().SKILL_ROOT / "skillscripts" / "utils"))

try:
    from enhanced_path_config_manager import EnhancedSkillPathManager, PathKey
except ImportError:
    from utils.enhanced_path_config_manager import EnhancedSkillPathManager, PathKey
from skillscripts.core.path_config_center import get_path_config


def count_function_lines(content: str, start_pos: int) -> tuple:
    brace_count = 0
    in_function = False
    line_count = 0
    pos = start_pos
    
    while pos < len(content):
        char = content[pos]
        
        if char == '{':
            brace_count += 1
            in_function = True
        elif char == '}':
            brace_count -= 1
            if in_function and brace_count == 0:
                return line_count + 1, pos
        elif char == '\n':
            line_count += 1
        
        pos += 1
    
    return line_count, pos


def find_ts_functions(content: str) -> List[Dict]:
    results = []
    lines = content.split('\n')
    
    patterns = [
        r'(?:async\s+)?function\s+(\w+)\s*\(',
        r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=])\s*=>',
        r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function\s*\(',
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            func_name = match.group(1)
            start_line = content[:match.start()].count('\n') + 1
            
            brace_start = content.find('{', match.start())
            if brace_start != -1:
                line_count, _ = count_function_lines(content, brace_start)
                end_line = start_line + line_count - 1
                
                if line_count > 0:
                    results.append({
                        'function': func_name,
                        'start_line': start_line,
                        'end_line': end_line,
                        'line_count': line_count
                    })
    
    return results


def find_vue_functions(content: str) -> List[Dict]:
    results = []
    
    script_match = re.search(r'<script[^>]*lang=["\']ts["\'][^>]*>(.*?)</script>', content, re.DOTALL)
    if script_match:
        script_content = script_match.group(1)
        results = find_ts_functions(script_content)
        
        script_start = content[:script_match.start()].count('\n') + 1
        for func in results:
            func['start_line'] += script_start
            func['end_line'] += script_start
    
    return results


def analyze_file(file_path: Path, max_lines: int = 50) -> List[Dict]:
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if file_path.suffix == '.vue':
            functions = find_vue_functions(content)
        else:
            functions = find_ts_functions(content)
        
        for func in functions:
            if func['line_count'] > max_lines:
                func['file'] = str(file_path)
                results.append(func)
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
    
    return results


def main():
    path_manager = EnhancedSkillPathManager.get_instance()
    frontend_dir = path_manager.resolve_path(PathKey.FRONTEND_DIR)
    frontend_src_dir = frontend_dir / 'src'
    
    print("=" * 80)
    print("检测前端TypeScript/Vue过长函数（>50行）")
    print("=" * 80)
    
    long_functions = []
    
    for ext in ['*.ts', '*.vue']:
        for file_path in frontend_src_dir.rglob(ext):
            if 'node_modules' in str(file_path):
                continue
            
            if 'tests' in str(file_path) or 'scripts' in str(file_path):
                continue
            
            functions = analyze_file(file_path, max_lines=50)
            long_functions.extend(functions)
    
    long_functions = sorted(long_functions, key=lambda x: x['line_count'], reverse=True)
    
    if not long_functions:
        print("\n✅ 没有发现超过50行的函数！")
    else:
        print(f"\n❌ 发现 {len(long_functions)} 个超过50行的函数：\n")
        
        for i, func in enumerate(long_functions, 1):
            print(f"{i}. {func['function']}")
            print(f"   文件: {func['file']}")
            print(f"   行数: {func['line_count']} 行 (第 {func['start_line']}-{func['end_line']} 行)")
            print()
    
    return long_functions


if __name__ == '__main__':
    main()
