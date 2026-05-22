#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化路径迁移脚本
==================
将 skillscripts/ 下所有 Python 文件中的硬编码路径替换为 PathConfigCenter 调用
"""

import os
import re
import sys
import py_compile
from pathlib import Path
from typing import List, Tuple, Dict, Set

# 配置
SKILLSCRIPTS_DIR = Path(r'd:\Projects\TraeProjects\skiller\.trae\skills\sanliu\skillscripts')
PCC_IMPORT_LINE = "from skillscripts.core.path_config_center import get_path_config"

# 统计数据
stats = {
    'total_files': 0,
    'modified_files': 0,
    'total_replacements': 0,
    'errors': [],
    'skipped_files': []
}


def should_skip_file(file_path: Path) -> bool:
    """判断是否应该跳过该文件"""
    filename = file_path.name
    
    if filename == 'path_config_center.py':
        return True
    
    if '__pycache__' in str(file_path):
        return True
    
    if filename == '__init__.py':
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        if not any(pattern in content for pattern in ['sys.path.insert', 'Path(__file__', 'project_root', 'PROJECT_ROOT']):
            return True
    
    return False


def add_pcc_import(content: str) -> str:
    """在文件顶部添加 PathConfigCenter 导入"""
    
    if 'get_path_config' in content or 'PathConfigCenter' in content:
        return content
    
    lines = content.split('\n')
    insert_idx = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            insert_idx = i + 1
        elif insert_idx > 0 and stripped and not stripped.startswith('#'):
            break
    
    lines.insert(insert_idx, PCC_IMPORT_LINE)
    return '\n'.join(lines)


def replace_sys_path_pattern(content: str, file_path: Path) -> Tuple[str, int]:
    """替换模式1: sys.path.insert with os.path.dirname(os.path.abspath(__file__))"""
    replacements = 0
    
    # 模式1a: sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    pattern1a = r'sys\.path\.insert\(0,\s*os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)'
    if re.search(pattern1a, content):
        content = re.sub(
            pattern1a,
            'sys.path.insert(0, str(get_path_config().SKILL_ROOT))',
            content
        )
        replacements += 1
    
    # 模式1b: sys.path.insert(0, str(Path(__file__).parent))
    pattern1b = r'sys\.path\.insert\(0,\s*str\(Path\(__file__\)\.parent\)\)'
    if re.search(pattern1b, content):
        parent_dir = file_path.parent.name
        
        if parent_dir == 'core':
            replacement = 'sys.path.insert(0, str(get_path_config().SCRIPTS_DIR))'
        elif parent_dir == 'test':
            replacement = 'sys.path.insert(0, str(get_path_config().SKILL_ROOT))'
        else:
            replacement = f'sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "{parent_dir}"))'
        
        content = re.sub(pattern1b, replacement, content)
        replacements += 1
    
    # 模式1c: sys.path.insert(0, str(Path(__file__).parent.parent))
    pattern1c = r'sys\.path\.insert\(0,\s*str\(Path\(__file__\)\.parent\.parent\)\)'
    if re.search(pattern1c, content):
        content = re.sub(
            pattern1c,
            'sys.path.insert(0, str(get_path_config().SKILL_ROOT))',
            content
        )
        replacements += 1
    
    # 模式1d: sys.path.insert(0, str(Path(__file__).parent.parent / "xxx"))
    pattern1d = r'sys\.path\.insert\(0,\s*str\(Path\(__file__\)\.parent\.parent\s*/\s*["\'](\w+)["\']\)\)'
    match = re.search(pattern1d, content)
    if match:
        subdir = match.group(1)
        if subdir == 'utils':
            replacement = 'sys.path.insert(0, str(get_path_config().SKILL_ROOT / "skillscripts" / "utils"))'
        else:
            replacement = f'sys.path.insert(0, str(get_path_config().SKILL_ROOT / "{subdir}"))'
        content = re.sub(pattern1d, replacement, content)
        replacements += 1
    
    # 模式1e: sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    pattern1e = r'sys\.path\.insert\(0,\s*str\(Path\(__file__\)\.parent\.parent\.parent\)\)'
    if re.search(pattern1e, content):
        content = re.sub(
            pattern1e,
            'sys.path.insert(0, str(get_path_config().SKILL_ROOT.parent))',
            content
        )
        replacements += 1
    
    return content, replacements


def replace_path_file_parent_pattern(content: str, file_path: Path) -> Tuple[str, int]:
    """替换模式2: Path(__file__).parent.parent... 用于定义根目录"""
    replacements = 0
    
    # 模式2a: PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    pattern2a = r'^(\s*)(PROJECT_ROOT|BASE_DIR|ROOT_DIR)\s*=\s*Path\(__file__\)\.parent(?:\.parent)+'
    matches = list(re.finditer(pattern2a, content, re.MULTILINE))
    for match in matches:
        var_name = match.group(2)
        indent = match.group(1)
        replacement = f'{indent}{var_name} = get_path_config().SKILL_ROOT'
        content = content[:match.start()] + replacement + content[match.end():]
        replacements += 1
    
    # 模式2b: SKILLSCRIPTS_DIR = Path(__file__).parent.parent
    pattern2b = r'^(\s*)SKILLSCRIPTS_DIR\s*=\s*Path\(__file__\)\.parent\.parent'
    if re.search(pattern2b, content, re.MULTILINE):
        content = re.sub(
            pattern2b,
            r'\1SKILLSCRIPTS_DIR = get_path_config().SCRIPTS_DIR',
            content,
            flags=re.MULTILINE
        )
        replacements += 1
    
    # 模式2c: CORE_DIR = Path(__file__).parent
    pattern2c = r'^(\s*)CORE_DIR\s*=\s*Path\(__file__\)\.parent'
    if re.search(pattern2c, content, re.MULTILINE):
        content = re.sub(
            pattern2c,
            r'\1CORE_DIR = get_path_config().SCRIPTS_DIR / "core"',
            content,
            flags=re.MULTILINE
        )
        replacements += 1
    
    # 模式2d: self.project_root = project_root or Path(__file__).parent.parent...
    pattern2d = r'self\.project_root\s*=\s*project_root\s+or\s+Path\(__file__\)\.parent(?:\.parent)+'
    if re.search(pattern2d, content):
        content = re.sub(
            pattern2d,
            'self.project_root = project_root or get_path_config().SKILL_ROOT',
            content
        )
        replacements += 1
    
    # 模式2e: project_root = Path(__file__).parent.parent.parent.parent
    pattern2e = r'(\s*)project_root\s*=\s*Path\(__file__\)\.parent(?:\.parent)+'
    if re.search(pattern2e, content):
        content = re.sub(
            pattern2e,
            r'\1project_root = get_path_config().SKILL_ROOT',
            content
        )
        replacements += 1
    
    # 模式2f: project_path = Path(__file__).parent.parent.parent.parent
    pattern2f = r'(\s*)project_path\s*=\s*Path\(__file__\)\.parent(?:\.parent)+'
    if re.search(pattern2f, content):
        content = re.sub(
            pattern2f,
            r'\1project_path = get_path_config().SKILL_ROOT',
            content
        )
        replacements += 1
    
    # 模式2g: BASE_DIR = Path(__file__).parent.parent
    pattern2g = r'^(\s*)BASE_DIR\s*=\s*Path\(__file__\)\.parent\.parent'
    if re.search(pattern2g, content, re.MULTILINE):
        content = re.sub(
            pattern2g,
            r'\1BASE_DIR = get_path_config().SKILL_ROOT',
            content,
            flags=re.MULTILINE
        )
        replacements += 1
    
    # 模式2h: self._scripts_dir = scripts_dir or Path(__file__).parent.parent
    pattern2h = r'self\._scripts_dir\s*=\s*scripts_dir\s+or\s+Path\(__file__\)\.parent\.parent'
    if re.search(pattern2h, content):
        content = re.sub(
            pattern2h,
            'self._scripts_dir = scripts_dir or get_path_config().SCRIPTS_DIR',
            content
        )
        replacements += 1
    
    # 模式2i: self.base_path = base_path or Path(__file__).parent.parent
    pattern2i = r'self\.base_path\s*=\s*base_path\s+or\s+Path\(__file__\)\.parent\.parent'
    if re.search(pattern2i, content):
        content = re.sub(
            pattern2i,
            'self.base_path = base_path or get_path_config().SKILL_ROOT',
            content
        )
        replacements += 1
    
    # 模式2j: self.project_root = project_root or Path(__file__).parent.parent
    pattern2j = r'self\.project_root\s*=\s*project_root\s+or\s+Path\(__file__\)\.parent\.parent'
    if re.search(pattern2j, content):
        content = re.sub(
            pattern2j,
            'self.project_root = project_root or get_path_config().SKILL_ROOT',
            content
        )
        replacements += 1
    
    return content, replacements


def replace_hardcoded_paths(content: str) -> Tuple[str, int]:
    """替换模式3&4: 硬编码的相对路径字符串"""
    replacements = 0
    
    # 模式3a: default='./reports/xxx.json' 或 default='./reports'
    pattern3a = r"default=['\"]\.\/(reports\/[^'\"]*|reports)['\"]"
    def replace_default_reports(match):
        nonlocal replacements
        path = match.group(1)
        replacements += 1
        if path == 'reports':
            return "default=str(get_path_config().REPORTS_DIR)"
        elif path.startswith('reports/'):
            filename = path[len('reports/'):]
            return f'default=str(get_path_config().REPORTS_DIR / "{filename}")'
        return match.group(0)
    
    content = re.sub(pattern3a, replace_default_reports, content)
    
    # 模式3b: output_path = './reports/xxx.json'
    pattern3b = r"output_path\s*=\s*['\"]\.\/(reports\/[^'\"]*)['\"]"
    def replace_output_path(match):
        nonlocal replacements
        path = match.group(1)
        replacements += 1
        if path.startswith('reports/'):
            filename = path[len('reports/'):]
            return f'output_path = str(get_path_config().REPORTS_DIR / "{filename}")'
        return match.group(0)
    
    content = re.sub(pattern3b, replace_output_path, content)
    
    # 模式3c: kwargs.get('output_path', './reports/xxx')
    pattern3c = r"kwargs\.get\(['\"]output_path['\"],\s*['\"]\.\/(reports\/[^'\"]*)['\"]\)"
    def replace_kwargs_output(match):
        nonlocal replacements
        path = match.group(1)
        replacements += 1
        if path.startswith('reports/'):
            filename = path[len('reports/'):]
            return f"kwargs.get('output_path', str(get_path_config().REPORTS_DIR / '{filename}'))"
        return match.group(0)
    
    content = re.sub(pattern3c, replace_kwargs_output, content)
    
    # 模式3d: kwargs.get('output', './reports') 或类似
    pattern3d = r"kwargs\.get\(['\"]output['\"],\s*['\"]\.\/(reports\/?[^'\"]*)['\"]\)"
    def replace_kwargs_output2(match):
        nonlocal replacements
        path = match.group(1)
        replacements += 1
        if path in ['reports', 'reports/']:
            return "kwargs.get('output', str(get_path_config().REPORTS_DIR))"
        elif path.startswith('reports/'):
            subdir = path[len('reports/'):]
            return f"kwargs.get('output', str(get_path_config().REPORTS_DIR / '{subdir}'))"
        return match.group(0)
    
    content = re.sub(pattern3d, replace_kwargs_output2, content)
    
    # 模式3e: parser.add_argument(..., default='./reports/...')
    pattern3e = r"(parser\.add_argument\([^)]*default=['\"])(\.\/(reports\/?[^'\"]*))(['\"])"
    def replace_parser_default(match):
        nonlocal replacements
        prefix = match.group(1)
        path = match.group(3)
        suffix = match.group(4)
        replacements += 1
        if path in ['reports', 'reports/']:
            return f'{prefix}str(get_path_config().REPORTS_DIR){suffix}'
        elif path.startswith('reports/'):
            filename = path[len('reports/'):]
            return f"{prefix}str(get_path_config().REPORTS_DIR / '{filename}'){suffix}"
        return match.group(0)
    
    content = re.sub(pattern3e, replace_parser_default, content)
    
    # 模式3f: config.get('output', './reports/xxx') 或 config.get('report_dir', './reports/xxx')
    pattern3f = r"config\.get\(['\"](?:output|report_dir|history_dir)['\"],\s*['\"]\.\/(reports\/?[^'\"]*)['\"]\)"
    def replace_config_get(match):
        nonlocal replacements
        original = match.group(0)
        path = match.group(1)
        replacements += 1
        if 'report_dir' in original and ('tests' in path or path == 'reports/tests'):
            return "config.get('report_dir', str(get_path_config().REPORTS_DIR / 'tests'))"
        elif 'history_dir' in original and ('test_history' in path or path == 'reports/test_history'):
            return "config.get('history_dir', str(get_path_config().REPORTS_DIR / 'test_history'))"
        elif path in ['reports', 'reports/']:
            quote_pos = original.find("'")
            return f"{original[:quote_pos]}', str(get_path_config().REPORTS_DIR))"
        elif path.startswith('reports/'):
            subdir = path[len('reports/'):]
            quote_pos = original.find("'")
            return f"{original[:quote_pos]}', str(get_path_config().REPORTS_DIR / '{subdir}'))"
        return match.group(0)
    
    content = re.sub(pattern3f, replace_config_get, content)
    
    # 模式3g: Path('./reports/xxx') 基本形式
    pattern3g = r"Path\(['\"]\.\/(reports\/[^'\"]*)['\"]\)"
    def replace_path_constructor_simple(match):
        nonlocal replacements
        path = match.group(1)
        replacements += 1
        if path.startswith('reports/'):
            subdir = path[len('reports/'):]
            return f'get_path_config().REPORTS_DIR / "{subdir}"'
        return match.group(0)
    
    content = re.sub(pattern3g, replace_path_constructor_simple, content)
    
    # 模式3h: Path('./docs/libs') 或 Path('./docs/xxx')
    pattern3h = r"Path\(['\"]\.\/(docs\/[^'\"]*)['\"]\)"
    def replace_docs_path(match):
        nonlocal replacements
        path = match.group(1)
        replacements += 1
        if path == 'docs/libs':
            return 'get_path_config().DOCS_DIR / "libs"'
        elif path.startswith('docs/'):
            subdir = path[len('docs/'):]
            return f'get_path_config().DOCS_DIR / "{subdir}"'
        return match.group(0)
    
    content = re.sub(pattern3h, replace_docs_path, content)
    
    # 模式3i: './data/knowledge' 或 './data/xxx' (只在默认参数中替换)
    pattern3i = r"(default=)['\"]\.\/(data\/[^'\"]*)['\"]"
    def replace_data_path(match):
        nonlocal replacements
        prefix = match.group(1)
        path = match.group(2)
        replacements += 1
        if path.startswith('data/'):
            filename = path[len('data/'):]
            return f'{prefix}str(get_path_config().DATA_DIR / "{filename}")'
        return match.group(0)
    
    content = re.sub(pattern3i, replace_data_path, content)
    
    # 模式3j: docs_dir = self.project_root / "docs"
    pattern3j = r'(\s*)docs_dir\s*=\s*self\.project_root\s*/\s*["\']docs["\']'
    if re.search(pattern3j, content):
        content = re.sub(
            pattern3j,
            r'\1docs_dir = get_path_config().DOCS_DIR',
            content
        )
        replacements += 1
    
    # 模式3k: output_dir = self.project_root / "reports"
    pattern3k = r'(\s*)output_dir\s*=\s*self\.project_root\s*/\s*["\']reports["\']'
    if re.search(pattern3k, content):
        content = re.sub(
            pattern3k,
            r'\1output_dir = get_path_config().REPORTS_DIR',
            content
        )
        replacements += 1
    
    # 模式3l: Path("reports/sdd_tdd_fusion")
    pattern3l = r'Path\(["\']reports\/[^\']*\)'
    def replace_reports_path_literal(match):
        nonlocal replacements
        full_path = match.group(0)[6:-2]
        replacements += 1
        if full_path.startswith('reports/'):
            subdir = full_path[len('reports/'):]
            return f'get_path_config().REPORTS_DIR / "{subdir}"'
        return match.group(0)
    
    content = re.sub(pattern3l, replace_reports_path_literal, content)
    
    # 模式3m: output_dir = Path('./reports/ui_validation') 或 output_dir = './reports/xxx'
    pattern3m = r'(\s*)output_dir\s*=\s*(?:Path\()?["\']\.\/(reports\/[^\'"]*)["\']\)?'
    def replace_output_dir_var(match):
        nonlocal replacements
        indent = match.group(1)
        path = match.group(2)
        replacements += 1
        if path.startswith('reports/'):
            subdir = path[len('reports/'):]
            return f'{indent}output_dir = get_path_config().REPORTS_DIR / "{subdir}"'
        return match.group(0)
    
    content = re.sub(pattern3m, replace_output_dir_var, content)
    
    # 模式3n: report_dir = kwargs.get('report_dir', './reports/tests')
    pattern3n = r"(\s*)report_dir\s*=\s*kwargs\.get\(['\"]report_dir['\"],\s*['\"]\.\/(reports\/[^'\"]*)['\"]\)"
    def replace_report_dir_kwarg(match):
        nonlocal replacements
        indent = match.group(1)
        path = match.group(2)
        replacements += 1
        if path.startswith('reports/'):
            subdir = path[len('reports/'):]
            return f'{indent}report_dir = kwargs.get(\'report_dir\', str(get_path_config().REPORTS_DIR / \'{subdir}\'))'
        return match.group(0)
    
    content = re.sub(pattern3n, replace_report_dir_kwarg, content)
    
    # 模式3o: history_dir = kwargs.get('history_dir', './reports/test_history')
    pattern3o = r"(\s*)history_dir\s*=\s*kwargs\.get\(['\"]history_dir['\"],\s*['\"]\.\/(reports\/[^'\"]*)['\"]\)"
    def replace_history_dir_kwarg(match):
        nonlocal replacements
        indent = match.group(1)
        path = match.group(2)
        replacements += 1
        if path.startswith('reports/'):
            subdir = path[len('reports/'):]
            return f'{indent}history_dir = kwargs.get(\'history_dir\', str(get_path_config().REPORTS_DIR / \'{subdir}\'))'
        return match.group(0)
    
    content = re.sub(pattern3o, replace_history_dir_kwarg, content)
    
    return content, replacements


def process_file(file_path: Path) -> bool:
    """处理单个文件"""
    global stats
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        original_content = content
        
        content, reps1 = replace_sys_path_pattern(content, file_path)
        content, reps2 = replace_path_file_parent_pattern(content, file_path)
        content, reps3 = replace_hardcoded_paths(content)
        
        total_reps = reps1 + reps2 + reps3
        
        if total_reps > 0:
            if 'get_path_config' not in original_content:
                content = add_pcc_import(content)
            
            file_path.write_text(content, encoding='utf-8')
            
            stats['modified_files'] += 1
            stats['total_replacements'] += total_reps
            
            print(f"[OK] {file_path.relative_to(SKILLSCRIPTS_DIR)} ({total_reps} replacements)")
            return True
        else:
            stats['skipped_files'].append(str(file_path))
            return False
            
    except Exception as e:
        error_msg = f"Failed to process {file_path}: {e}"
        stats['errors'].append(error_msg)
        print(f"[FAIL] {file_path.relative_to(SKILLSCRIPTS_DIR)}: {e}")
        return False


def validate_file(file_path: Path) -> bool:
    """验证文件语法"""
    try:
        py_compile.compile(str(file_path), doraise=True)
        return True
    except py_compile.PyCompileError as e:
        stats['errors'].append(f"Syntax error {file_path}: {e}")
        print(f"[FAIL] Syntax error {file_path.relative_to(SKILLSCRIPTS_DIR)}: {e}")
        return False


def main():
    """主函数"""
    print("=" * 80)
    print("Starting hardcoded path migration - PathConfigCenter integration")
    print("=" * 80)
    print(f"Target directory: {SKILLSCRIPTS_DIR}")
    print()
    
    py_files = sorted(SKILLSCRIPTS_DIR.rglob('*.py'))
    py_files = [f for f in py_files if not should_skip_file(f)]
    
    stats['total_files'] = len(py_files)
    print(f"Found {len(py_files)} files to process")
    print()
    
    directories = {}
    for f in py_files:
        rel_parent = f.relative_to(SKILLSCRIPTS_DIR).parent
        dir_name = str(rel_parent) if str(rel_parent) != '.' else 'root'
        if dir_name not in directories:
            directories[dir_name] = []
        directories[dir_name].append(f)
    
    for dir_name in sorted(directories.keys()):
        files = directories[dir_name]
        print(f"\n{'=' * 60}")
        print(f"Processing: {dir_name}/ ({len(files)} files)")
        print('=' * 60)
        
        for file_path in files:
            process_file(file_path)
    
    print("\n" + "=" * 80)
    print("Migration complete! Statistics:")
    print("=" * 80)
    print(f"Total files: {stats['total_files']}")
    print(f"Modified files: {stats['modified_files']}")
    print(f"Total replacements: {stats['total_replacements']}")
    print(f"Skipped files: {len(stats['skipped_files'])}")
    
    if stats['errors']:
        print(f"\nErrors: {len(stats['errors'])}")
        print("\nError details:")
        for err in stats['errors']:
            print(f"  - {err}")
    
    print("\n" + "=" * 80)
    print("Validating modified files...")
    print("=" * 80)
    
    validation_errors = 0
    for dir_name in sorted(directories.keys()):
        files = directories[dir_name]
        for file_path in files:
            if str(file_path) not in [s for s in stats['skipped_files']]:
                if not validate_file(file_path):
                    validation_errors += 1
    
    if validation_errors == 0:
        print(f"\n[OK] All files passed syntax validation!")
    else:
        print(f"\n[FAIL] Found {validation_errors} files with syntax errors")
    
    print("\nMigration finished!")


if __name__ == '__main__':
    main()
