#!/usr/bin/env python3
"""
Code Simplification Detector
Detects simplification opportunities in source code
"""

import argparse
import ast
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any


SOURCE_EXTENSIONS = {
    '.py', '.js', '.ts', '.tsx', '.jsx', '.vue', '.svelte',
    '.java', '.go', '.rs', '.rb', '.php', '.cs', '.swift',
    '.kt', '.c', '.cpp', '.h', '.hpp',
}

IGNORED_DIRS = {
    'node_modules', '.git', '__pycache__', '.venv', 'venv',
    'dist', 'build', '.next', '.nuxt', 'target', 'bin',
    'obj', '.idea', '.vscode', 'coverage', '.cache',
}

NESTING_THRESHOLD = 3
LONG_FUNCTION_LINES = 50


def parse_args():
    parser = argparse.ArgumentParser(
        description='Code Simplification Detector - detect simplification opportunities'
    )
    parser.add_argument(
        '--target',
        type=str,
        required=True,
        help='Target file or directory path'
    )
    parser.add_argument(
        '--scope',
        type=str,
        choices=['file', 'dir', 'recent'],
        default='recent',
        help='Scope: file, dir, or recent (default: recent)'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['text', 'json'],
        default='json',
        help='Output format: text or json (default: json)'
    )
    return parser.parse_args()


def collect_files(target: str, scope: str) -> List[Path]:
    target_path = Path(target).resolve()
    if scope == 'file':
        if target_path.is_file() and target_path.suffix.lower() in SOURCE_EXTENSIONS:
            return [target_path]
        return []
    if scope in ('dir', 'recent'):
        if target_path.is_file():
            return [target_path]
        if target_path.is_dir():
            result = []
            for root, dirs, files in os.walk(target_path):
                dirs[:] = [
                    d for d in dirs
                    if d not in IGNORED_DIRS and not d.startswith('.')
                ]
                for fname in files:
                    fpath = Path(root) / fname
                    if fpath.suffix.lower() in SOURCE_EXTENSIONS:
                        result.append(fpath)
            if scope == 'recent' and result:
                result.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                result = result[:20]
            return result
    return []


class PythonAnalyzer:
    def __init__(self):
        self.findings: List[Dict[str, Any]] = []

    def analyze(self, file_path: Path, content: str):
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            self._analyze_with_regex(file_path, content)
            return

        self._detect_dead_imports(tree, file_path)
        self._detect_dead_variables(tree, file_path)
        self._detect_dead_functions(tree, file_path)
        self._detect_deep_nesting_ast(tree, file_path)
        self._detect_long_functions_ast(tree, file_path, content)
        self._detect_complex_conditions_ast(tree, file_path)
        self._detect_duplicate_strings_ast(tree, file_path)

    def _detect_dead_imports(self, tree: ast.AST, file_path: Path):
        imports: Dict[str, int] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split('.')[0]
                    imports[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = node.lineno

        used_names: set = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                root = node
                while isinstance(root, ast.Attribute):
                    root = root.value
                if isinstance(root, ast.Name):
                    used_names.add(root.id)

        for name, lineno in imports.items():
            if name not in used_names and name != '__future__':
                self.findings.append({
                    'file': str(file_path),
                    'line': lineno,
                    'type': 'dead_code',
                    'subtype': 'unused_import',
                    'description': f"Unused import: {name}",
                    'suggestion': f"Remove unused import '{name}'",
                })

    def _detect_dead_variables(self, tree: ast.AST, file_path: Path):
        assignments: Dict[str, int] = {}
        reads: set = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith('_'):
                        assignments[target.id] = node.lineno
            elif isinstance(node, ast.AugAssign):
                if isinstance(node.target, ast.Name):
                    reads.add(node.target.id)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                reads.add(node.id)

        for name, lineno in assignments.items():
            if name not in reads and not name.isupper():
                self.findings.append({
                    'file': str(file_path),
                    'line': lineno,
                    'type': 'dead_code',
                    'subtype': 'unused_variable',
                    'description': f"Unused variable: {name}",
                    'suggestion': f"Remove or use variable '{name}'",
                })

    def _detect_dead_functions(self, tree: ast.AST, file_path: Path):
        defined_funcs: Dict[str, int] = {}
        called_funcs: set = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_'):
                    defined_funcs[node.name] = node.lineno
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_funcs.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_funcs.add(node.func.attr)

        for name, lineno in defined_funcs.items():
            if name not in called_funcs and name != 'main':
                self.findings.append({
                    'file': str(file_path),
                    'line': lineno,
                    'type': 'dead_code',
                    'subtype': 'unused_function',
                    'description': f"Unused function: {name}",
                    'suggestion': f"Remove unused function '{name}' or mark as private with underscore prefix",
                })

    def _detect_deep_nesting_ast(self, tree: ast.AST, file_path: Path):
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_nesting(node, file_path, 0, node.name)

    def _check_nesting(self, node: ast.AST, file_path: Path, depth: int, func_name: str):
        nesting_constructs = (ast.If, ast.For, ast.While, ast.With, ast.Try)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, nesting_constructs):
                new_depth = depth + 1
                if new_depth > NESTING_THRESHOLD:
                    self.findings.append({
                        'file': str(file_path),
                        'line': child.lineno,
                        'type': 'deep_nesting',
                        'subtype': f"{type(child).__name__}_depth_{new_depth}",
                        'description': f"Deep nesting (depth={new_depth}) in function '{func_name}'",
                        'suggestion': "Use early returns, extract method, or guard clauses to reduce nesting",
                    })
                self._check_nesting(child, file_path, new_depth, func_name)
            elif isinstance(child, (ast.If, ast.For, ast.While)):
                self._check_nesting(child, file_path, depth, func_name)

    def _detect_long_functions_ast(self, tree: ast.AST, file_path: Path, content: str):
        lines = content.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_lineno = getattr(node, 'end_lineno', None)
                if end_lineno:
                    func_lines = end_lineno - node.lineno + 1
                else:
                    func_lines = self._count_function_lines(node, lines)

                if func_lines > LONG_FUNCTION_LINES:
                    self.findings.append({
                        'file': str(file_path),
                        'line': node.lineno,
                        'type': 'long_function',
                        'subtype': f"{func_lines}_lines",
                        'description': f"Long function '{node.name}' ({func_lines} lines, threshold={LONG_FUNCTION_LINES})",
                        'suggestion': "Extract sub-functions or methods to reduce function length",
                    })

    def _count_function_lines(self, node: ast.AST, lines: List[str]) -> int:
        start = node.lineno - 1
        max_line = start
        for child in ast.walk(node):
            if hasattr(child, 'lineno') and child.lineno:
                max_line = max(max_line, child.lineno - 1)
        return max_line - start + 1

    def _detect_complex_conditions_ast(self, tree: ast.AST, file_path: Path):
        for node in ast.walk(tree):
            if isinstance(node, ast.BoolOp):
                op_count = len(node.values)
                if op_count >= 4:
                    self.findings.append({
                        'file': str(file_path),
                        'line': node.lineno,
                        'type': 'complex_condition',
                        'subtype': 'dense_boolean',
                        'description': f"Complex boolean expression with {op_count} operands",
                        'suggestion': "Extract sub-conditions into named variables or helper functions",
                    })
            elif isinstance(node, ast.IfExp):
                parent_check = getattr(node, '_parent_chained', False)
                if not parent_check:
                    chain_count = self._count_ternary_chain(node)
                    if chain_count >= 3:
                        self.findings.append({
                            'file': str(file_path),
                            'line': node.lineno,
                            'type': 'complex_condition',
                            'subtype': 'dense_ternary',
                            'description': f"Dense ternary chain (depth={chain_count})",
                            'suggestion': "Replace ternary chain with if/elif or dictionary dispatch",
                        })

    def _count_ternary_chain(self, node: ast.AST) -> int:
        count = 1
        if isinstance(node, ast.IfExp) and isinstance(node.orelse, ast.IfExp):
            count += self._count_ternary_chain(node.orelse)
        return count

    def _detect_duplicate_strings_ast(self, tree: ast.AST, file_path: Path):
        string_occurrences: Dict[str, List[int]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val = node.value.strip()
                if len(val) >= 5 and not val.startswith(('#', '//', '/*')):
                    if val not in string_occurrences:
                        string_occurrences[val] = []
                    string_occurrences[val].append(node.lineno)

        for val, lines in string_occurrences.items():
            if len(lines) >= 3:
                self.findings.append({
                    'file': str(file_path),
                    'line': lines[0],
                    'type': 'duplicate_string',
                    'subtype': 'repeated_constant',
                    'description': f"Duplicate string constant appears {len(lines)} times: '{val[:40]}{'...' if len(val) > 40 else ''}'",
                    'suggestion': "Extract to a named constant",
                })

    def _analyze_with_regex(self, file_path: Path, content: str):
        self._detect_deep_nesting_regex(file_path, content)
        self._detect_long_functions_regex(file_path, content)
        self._detect_complex_conditions_regex(file_path, content)
        self._detect_duplicate_strings_regex(file_path, content)
        self._detect_unused_imports_regex(file_path, content)

    def _detect_deep_nesting_regex(self, file_path: Path, content: str):
        lines = content.splitlines()
        depth = 0
        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            if not stripped or stripped.startswith('#'):
                continue
            indent = len(line) - len(stripped)
            new_depth = indent // 4
            if new_depth > NESTING_THRESHOLD:
                if any(stripped.startswith(kw) for kw in ('if ', 'elif ', 'else:', 'for ', 'while ', 'with ', 'try:', 'except ')):
                    self.findings.append({
                        'file': str(file_path),
                        'line': i,
                        'type': 'deep_nesting',
                        'subtype': f"indent_depth_{new_depth}",
                        'description': f"Deep nesting (indent depth={new_depth})",
                        'suggestion': "Use early returns, extract method, or guard clauses to reduce nesting",
                    })

    def _detect_long_functions_regex(self, file_path: Path, content: str):
        lines = content.splitlines()
        func_start = None
        func_name = ''
        func_indent = 0
        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            match = re.match(r'^(?:async\s+)?def\s+(\w+)', stripped)
            if match:
                if func_start and (i - func_start) > LONG_FUNCTION_LINES:
                    self.findings.append({
                        'file': str(file_path),
                        'line': func_start,
                        'type': 'long_function',
                        'subtype': f"{i - func_start}_lines",
                        'description': f"Long function '{func_name}' ({i - func_start} lines, threshold={LONG_FUNCTION_LINES})",
                        'suggestion': "Extract sub-functions or methods to reduce function length",
                    })
                func_start = i
                func_name = match.group(1)
                func_indent = len(line) - len(stripped)
            elif func_start and stripped and (len(line) - len(stripped)) <= func_indent and not stripped.startswith(('#', '@', '"""', "'''")):
                if (i - func_start) > LONG_FUNCTION_LINES:
                    self.findings.append({
                        'file': str(file_path),
                        'line': func_start,
                        'type': 'long_function',
                        'subtype': f"{i - func_start}_lines",
                        'description': f"Long function '{func_name}' ({i - func_start} lines, threshold={LONG_FUNCTION_LINES})",
                        'suggestion': "Extract sub-functions or methods to reduce function length",
                    })
                func_start = None

    def _detect_complex_conditions_regex(self, file_path: Path, content: str):
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            if stripped.startswith('#'):
                continue
            and_count = len(re.findall(r'\band\b', stripped))
            or_count = len(re.findall(r'\bor\b', stripped))
            if and_count + or_count >= 4:
                self.findings.append({
                    'file': str(file_path),
                    'line': i,
                    'type': 'complex_condition',
                    'subtype': 'dense_boolean',
                    'description': f"Complex boolean expression ({and_count} 'and' + {or_count} 'or')",
                    'suggestion': "Extract sub-conditions into named variables or helper functions",
                })
            ternary_count = stripped.count(' if ') + stripped.count(' else ')
            if ternary_count >= 4:
                self.findings.append({
                    'file': str(file_path),
                    'line': i,
                    'type': 'complex_condition',
                    'subtype': 'dense_ternary',
                    'description': f"Dense ternary chain (ternary count={ternary_count})",
                    'suggestion': "Replace ternary chain with if/elif or dictionary dispatch",
                })

    def _detect_duplicate_strings_regex(self, file_path: Path, content: str):
        string_pattern = re.compile(r'["\']([^"\']{5,})["\']')
        occurrences: Dict[str, List[int]] = {}
        for i, line in enumerate(content.splitlines(), start=1):
            for match in string_pattern.finditer(line):
                val = match.group(1).strip()
                if val and not val.startswith(('#', '//', '/*', 'http')):
                    if val not in occurrences:
                        occurrences[val] = []
                    occurrences[val].append(i)

        for val, line_nums in occurrences.items():
            if len(line_nums) >= 3:
                self.findings.append({
                    'file': str(file_path),
                    'line': line_nums[0],
                    'type': 'duplicate_string',
                    'subtype': 'repeated_constant',
                    'description': f"Duplicate string constant appears {len(line_nums)} times: '{val[:40]}{'...' if len(val) > 40 else ''}'",
                    'suggestion': "Extract to a named constant",
                })

    def _detect_unused_imports_regex(self, file_path: Path, content: str):
        lines = content.splitlines()
        imports: Dict[str, int] = {}
        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            match = re.match(r'^import\s+([A-Za-z_][\w.]*)', stripped)
            if match:
                name = match.group(1).split('.')[0]
                imports[name] = i
                continue
            match = re.match(r'^from\s+[A-Za-z_][\w.]*\s+import\s+(.+)', stripped)
            if match:
                for alias_str in match.group(1).split(','):
                    alias_str = alias_str.strip()
                    parts = alias_str.split(' as ')
                    name = parts[-1].strip() if len(parts) > 1 else parts[0].strip()
                    if name and name != '*':
                        imports[name] = i

        for name, lineno in imports.items():
            pattern = re.compile(r'\b' + re.escape(name) + r'\b')
            used = False
            for j, line in enumerate(lines, start=1):
                if j == lineno:
                    continue
                if pattern.search(line):
                    used = True
                    break
            if not used:
                self.findings.append({
                    'file': str(file_path),
                    'line': lineno,
                    'type': 'dead_code',
                    'subtype': 'unused_import',
                    'description': f"Unused import: {name}",
                    'suggestion': f"Remove unused import '{name}'",
                })


class JavaScriptAnalyzer:
    def __init__(self):
        self.findings: List[Dict[str, Any]] = []

    def analyze(self, file_path: Path, content: str):
        self._detect_deep_nesting(file_path, content)
        self._detect_long_functions(file_path, content)
        self._detect_complex_conditions(file_path, content)
        self._detect_duplicate_strings(file_path, content)
        self._detect_unused_imports_js(file_path, content)

    def _detect_deep_nesting(self, file_path: Path, content: str):
        lines = content.splitlines()
        depth = 0
        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            if not stripped or stripped.startswith('//') or stripped.startswith('/*'):
                continue
            indent = len(line) - len(stripped)
            nesting = indent // 2
            if nesting > NESTING_THRESHOLD:
                if any(stripped.startswith(kw) for kw in ('if ', 'if(', 'else ', 'else{', 'else if', 'for ', 'for(', 'while ', 'while(', 'switch ', 'switch(', 'try {', 'try{')):
                    self.findings.append({
                        'file': str(file_path),
                        'line': i,
                        'type': 'deep_nesting',
                        'subtype': f"indent_depth_{nesting}",
                        'description': f"Deep nesting (indent depth={nesting})",
                        'suggestion': "Use early returns, extract method, or guard clauses to reduce nesting",
                    })

    def _detect_long_functions(self, file_path: Path, content: str):
        lines = content.splitlines()
        func_start = None
        func_name = ''
        brace_depth = 0
        in_func = False
        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            match = re.match(
                r'(?:async\s+)?(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=])\s*=>)',
                stripped
            )
            if match:
                if in_func and func_start and (i - func_start) > LONG_FUNCTION_LINES:
                    self.findings.append({
                        'file': str(file_path),
                        'line': func_start,
                        'type': 'long_function',
                        'subtype': f"{i - func_start}_lines",
                        'description': f"Long function '{func_name}' ({i - func_start} lines, threshold={LONG_FUNCTION_LINES})",
                        'suggestion': "Extract sub-functions or methods to reduce function length",
                    })
                func_start = i
                func_name = match.group(1) or match.group(2) or '<anonymous>'
                brace_depth = 0
                in_func = True

            if in_func:
                brace_depth += line.count('{') - line.count('}')
                if brace_depth <= 0 and i > (func_start or 0):
                    if (i - (func_start or i)) > LONG_FUNCTION_LINES:
                        self.findings.append({
                            'file': str(file_path),
                            'line': func_start or i,
                            'type': 'long_function',
                            'subtype': f"{i - (func_start or i)}_lines",
                            'description': f"Long function '{func_name}' ({i - (func_start or i)} lines, threshold={LONG_FUNCTION_LINES})",
                            'suggestion': "Extract sub-functions or methods to reduce function length",
                        })
                    in_func = False

    def _detect_complex_conditions(self, file_path: Path, content: str):
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            if stripped.startswith('//') or stripped.startswith('/*'):
                continue
            and_count = len(re.findall(r'&&', stripped))
            or_count = len(re.findall(r'\|\|', stripped))
            if and_count + or_count >= 4:
                self.findings.append({
                    'file': str(file_path),
                    'line': i,
                    'type': 'complex_condition',
                    'subtype': 'dense_boolean',
                    'description': f"Complex boolean expression ({and_count} '&&' + {or_count} '||')",
                    'suggestion': "Extract sub-conditions into named variables or helper functions",
                })
            ternary_count = stripped.count('?') + stripped.count(':')
            if ternary_count >= 6:
                self.findings.append({
                    'file': str(file_path),
                    'line': i,
                    'type': 'complex_condition',
                    'subtype': 'dense_ternary',
                    'description': f"Dense ternary chain (ternary count={ternary_count // 2})",
                    'suggestion': "Replace ternary chain with if/else or object dispatch",
                })

    def _detect_duplicate_strings(self, file_path: Path, content: str):
        string_pattern = re.compile(r'["\']([^"\']{5,})["\']')
        occurrences: Dict[str, List[int]] = {}
        for i, line in enumerate(content.splitlines(), start=1):
            stripped = line.lstrip()
            if stripped.startswith('//') or stripped.startswith('/*'):
                continue
            for match in string_pattern.finditer(line):
                val = match.group(1).strip()
                if val and not val.startswith(('http', '//', '/*', '#')):
                    if val not in occurrences:
                        occurrences[val] = []
                    occurrences[val].append(i)

        for val, line_nums in occurrences.items():
            if len(line_nums) >= 3:
                self.findings.append({
                    'file': str(file_path),
                    'line': line_nums[0],
                    'type': 'duplicate_string',
                    'subtype': 'repeated_constant',
                    'description': f"Duplicate string constant appears {len(line_nums)} times: '{val[:40]}{'...' if len(val) > 40 else ''}'",
                    'suggestion': "Extract to a named constant",
                })

    def _detect_unused_imports_js(self, file_path: Path, content: str):
        lines = content.splitlines()
        imports: Dict[str, int] = {}
        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            match = re.match(r'import\s+(?:\{([^}]+)\}|\*\s+as\s+(\w+)|(\w+))\s+from', stripped)
            if match:
                if match.group(1):
                    for name in match.group(1).split(','):
                        name = name.strip().split(' as ')[-1].strip()
                        if name:
                            imports[name] = i
                elif match.group(2):
                    imports[match.group(2)] = i
                elif match.group(3):
                    imports[match.group(3)] = i

        for name, lineno in imports.items():
            pattern = re.compile(r'\b' + re.escape(name) + r'\b')
            used = False
            for j, line in enumerate(lines, start=1):
                if j == lineno:
                    continue
                if pattern.search(line):
                    used = True
                    break
            if not used:
                self.findings.append({
                    'file': str(file_path),
                    'line': lineno,
                    'type': 'dead_code',
                    'subtype': 'unused_import',
                    'description': f"Unused import: {name}",
                    'suggestion': f"Remove unused import '{name}'",
                })


class GenericAnalyzer:
    def __init__(self):
        self.findings: List[Dict[str, Any]] = []

    def analyze(self, file_path: Path, content: str):
        self._detect_deep_nesting(file_path, content)
        self._detect_long_functions(file_path, content)
        self._detect_complex_conditions(file_path, content)
        self._detect_duplicate_strings(file_path, content)

    def _detect_deep_nesting(self, file_path: Path, content: str):
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            if not stripped:
                continue
            indent = len(line) - len(stripped)
            nesting = indent // 4
            if nesting > NESTING_THRESHOLD:
                self.findings.append({
                    'file': str(file_path),
                    'line': i,
                    'type': 'deep_nesting',
                    'subtype': f"indent_depth_{nesting}",
                    'description': f"Deep nesting (indent depth={nesting})",
                    'suggestion': "Use early returns, extract method, or guard clauses to reduce nesting",
                })

    def _detect_long_functions(self, file_path: Path, content: str):
        lines = content.splitlines()
        block_start = None
        brace_depth = 0
        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            if any(kw in stripped for kw in ('function ', 'def ', 'fn ', 'func ', 'sub ')):
                block_start = i
                brace_depth = 0
            if block_start:
                brace_depth += line.count('{') - line.count('}')
                if brace_depth <= 0 and i > block_start:
                    if (i - block_start) > LONG_FUNCTION_LINES:
                        self.findings.append({
                            'file': str(file_path),
                            'line': block_start,
                            'type': 'long_function',
                            'subtype': f"{i - block_start}_lines",
                            'description': f"Long function/block ({i - block_start} lines, threshold={LONG_FUNCTION_LINES})",
                            'suggestion': "Extract sub-functions or methods to reduce function length",
                        })
                    block_start = None

    def _detect_complex_conditions(self, file_path: Path, content: str):
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            if stripped.startswith(('#', '//', '/*')):
                continue
            bool_ops = len(re.findall(r'&&|\|\||\band\b|\bor\b', stripped))
            if bool_ops >= 4:
                self.findings.append({
                    'file': str(file_path),
                    'line': i,
                    'type': 'complex_condition',
                    'subtype': 'dense_boolean',
                    'description': f"Complex boolean expression ({bool_ops} operators)",
                    'suggestion': "Extract sub-conditions into named variables or helper functions",
                })

    def _detect_duplicate_strings(self, file_path: Path, content: str):
        string_pattern = re.compile(r'["\']([^"\']{5,})["\']')
        occurrences: Dict[str, List[int]] = {}
        for i, line in enumerate(content.splitlines(), start=1):
            for match in string_pattern.finditer(line):
                val = match.group(1).strip()
                if val and not val.startswith(('http', '//', '/*', '#')):
                    if val not in occurrences:
                        occurrences[val] = []
                    occurrences[val].append(i)

        for val, line_nums in occurrences.items():
            if len(line_nums) >= 3:
                self.findings.append({
                    'file': str(file_path),
                    'line': line_nums[0],
                    'type': 'duplicate_string',
                    'subtype': 'repeated_constant',
                    'description': f"Duplicate string constant appears {len(line_nums)} times: '{val[:40]}{'...' if len(val) > 40 else ''}'",
                    'suggestion': "Extract to a named constant",
                })


def analyze_file(file_path: Path) -> List[Dict[str, Any]]:
    try:
        content = file_path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as e:
        print(f"Failed to read {file_path}: {e}", file=sys.stderr)
        return []

    suffix = file_path.suffix.lower()

    if suffix == '.py':
        analyzer = PythonAnalyzer()
        analyzer.analyze(file_path, content)
        return analyzer.findings
    elif suffix in {'.js', '.ts', '.tsx', '.jsx', '.vue', '.svelte'}:
        analyzer = JavaScriptAnalyzer()
        analyzer.analyze(file_path, content)
        return analyzer.findings
    else:
        analyzer = GenericAnalyzer()
        analyzer.analyze(file_path, content)
        return analyzer.findings


def format_text_report(result: Dict[str, Any]) -> str:
    lines: List[str] = []
    summary = result['summary']

    lines.append('=' * 80)
    lines.append('Code Simplification Report')
    lines.append('=' * 80)
    lines.append(f"Timestamp: {result['timestamp']}")
    lines.append(f"Target:    {result['target']}")
    lines.append(f"Scope:     {result['scope']}")
    lines.append(f"Files:     {summary['files_scanned']}")
    lines.append('-' * 80)
    lines.append(f"Total findings:       {summary['total_findings']}")
    lines.append(f"  Dead code:          {summary['dead_code']}")
    lines.append(f"  Deep nesting:       {summary['deep_nesting']}")
    lines.append(f"  Complex conditions: {summary['complex_condition']}")
    lines.append(f"  Long functions:     {summary['long_function']}")
    lines.append(f"  Duplicate strings:  {summary['duplicate_string']}")
    lines.append('=' * 80)

    findings = result['findings']
    if not findings:
        lines.append('No simplification opportunities detected.')
    else:
        for finding in findings:
            lines.append('')
            lines.append(f"  [{finding['type']}] {finding['file']}:{finding['line']}")
            lines.append(f"    Description: {finding['description']}")
            lines.append(f"    Suggestion:  {finding['suggestion']}")

    lines.append('')
    lines.append('=' * 80)
    return '\n'.join(lines)


def main():
    args = parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"Target does not exist: {args.target}", file=sys.stderr)
        sys.exit(2)

    files = collect_files(args.target, args.scope)
    if not files:
        print("No source files found to analyze.", file=sys.stderr)
        sys.exit(2)

    all_findings: List[Dict[str, Any]] = []
    for f in files:
        findings = analyze_file(f)
        all_findings.extend(findings)

    type_counts: Dict[str, int] = {
        'dead_code': 0,
        'deep_nesting': 0,
        'complex_condition': 0,
        'long_function': 0,
        'duplicate_string': 0,
    }
    for f in all_findings:
        ftype = f['type']
        if ftype in type_counts:
            type_counts[ftype] += 1

    result = {
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'target': str(target_path),
        'scope': args.scope,
        'summary': {
            'files_scanned': len(files),
            'total_findings': len(all_findings),
            **type_counts,
        },
        'findings': all_findings,
    }

    if args.format == 'json':
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = format_text_report(result)

    sys.stdout.buffer.write(output.encode('utf-8'))
    sys.stdout.buffer.write(b'\n')

    if all_findings:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
