#!/usr/bin/env python3
"""
Deduplication Detector
Detects duplicate code patterns, similar functions, and repeated string constants
"""

import argparse
import ast
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


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

MIN_BLOCK_LINES = 3


def parse_args():
    parser = argparse.ArgumentParser(
        description='Deduplication Detector - detect duplicate code patterns'
    )
    parser.add_argument(
        '--target',
        type=str,
        required=True,
        help='Target directory path'
    )
    parser.add_argument(
        '--min-occurrences',
        type=int,
        default=3,
        help='Minimum occurrence count to report (default: 3)'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['text', 'json'],
        default='json',
        help='Output format: text or json (default: json)'
    )
    return parser.parse_args()


def collect_files(target: str) -> List[Path]:
    target_path = Path(target).resolve()
    if not target_path.is_dir():
        print(f"Target is not a directory: {target}", file=sys.stderr)
        return []
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
    return result


def normalize_line(line: str) -> str:
    stripped = line.strip()
    stripped = re.sub(r'#.*$', '', stripped)
    stripped = re.sub(r'//.*$', '', stripped)
    stripped = re.sub(r'/\*.*?\*/', '', stripped)
    stripped = re.sub(r'\s+', ' ', stripped)
    return stripped


def compute_block_hash(lines: List[str]) -> str:
    normalized = '\n'.join(normalize_line(l) for l in lines if normalize_line(l))
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()


class FunctionSignature:
    def __init__(self, name: str, params: List[str], file_path: str, line: int,
                 body_lines: int, body_hash: str, body_summary: str):
        self.name = name
        self.params = params
        self.file_path = file_path
        self.line = line
        self.body_lines = body_lines
        self.body_hash = body_hash
        self.body_summary = body_summary


class SlidingWindowBlockDetector:
    def __init__(self, min_occurrences: int, window_sizes: Optional[List[int]] = None):
        self.min_occurrences = min_occurrences
        self.window_sizes = window_sizes or [3, 4, 5, 6, 7, 8]
        self.findings: List[Dict[str, Any]] = []

    def detect(self, files: List[Path]):
        hash_map: Dict[str, List[Tuple[str, int, int]]] = defaultdict(list)

        for fpath in files:
            try:
                content = fpath.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            lines = content.splitlines()
            file_str = str(fpath)

            for window_size in self.window_sizes:
                for start in range(len(lines) - window_size + 1):
                    window = lines[start:start + window_size]
                    if sum(1 for l in window if l.strip()) < MIN_BLOCK_LINES:
                        continue
                    block_hash = compute_block_hash(window)
                    hash_map[block_hash].append((file_str, start + 1, start + window_size))

        reported_hashes: set = set()
        for block_hash, occurrences in hash_map.items():
            if len(occurrences) >= self.min_occurrences and block_hash not in reported_hashes:
                reported_hashes.add(block_hash)
                sample_lines = self._get_sample_lines(occurrences[0][0], occurrences[0][1], occurrences[0][2])
                self.findings.append({
                    'type': 'duplicate_block',
                    'pattern_hash': block_hash[:12],
                    'pattern_summary': sample_lines,
                    'occurrence_count': len(occurrences),
                    'occurrences': [
                        {
                            'file': occ[0],
                            'start_line': occ[1],
                            'end_line': occ[2],
                        }
                        for occ in occurrences
                    ],
                    'suggestion': 'Extract duplicated code block into a shared function or utility',
                })

    def _get_sample_lines(self, file_path: str, start: int, end: int) -> str:
        try:
            content = Path(file_path).read_text(encoding='utf-8')
            lines = content.splitlines()
            sample = lines[start - 1:end]
            normalized = [normalize_line(l) for l in sample if normalize_line(l)]
            return ' | '.join(normalized)[:100]
        except (OSError, UnicodeDecodeError):
            return '<unable to read>'


class SimilarFunctionDetector:
    def __init__(self, min_occurrences: int):
        self.min_occurrences = min_occurrences
        self.findings: List[Dict[str, Any]] = []

    def detect(self, files: List[Path]):
        all_sigs: List[FunctionSignature] = []

        for fpath in files:
            try:
                content = fpath.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            suffix = fpath.suffix.lower()
            if suffix == '.py':
                sigs = self._extract_python_signatures(str(fpath), content)
            elif suffix in {'.js', '.ts', '.tsx', '.jsx'}:
                sigs = self._extract_js_signatures(str(fpath), content)
            else:
                sigs = self._extract_generic_signatures(str(fpath), content)
            all_sigs.extend(sigs)

        self._find_similar(all_sigs)

    def _extract_python_signatures(self, file_path: str, content: str) -> List[FunctionSignature]:
        sigs = []
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError:
            return sigs

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = [arg.arg for arg in node.args.args if arg.arg != 'self']
                body_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') and node.end_lineno else 0
                body_content = content.splitlines()[node.lineno:node.lineno + body_lines]
                body_hash = hashlib.md5(
                    '\n'.join(normalize_line(l) for l in body_content).encode('utf-8')
                ).hexdigest()
                body_summary = ''
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, (ast.Return, ast.Assign, ast.Expr)):
                        body_summary = ast.dump(child)[:80]
                        break
                sigs.append(FunctionSignature(
                    name=node.name,
                    params=params,
                    file_path=file_path,
                    line=node.lineno,
                    body_lines=body_lines,
                    body_hash=body_hash,
                    body_summary=body_summary,
                ))
        return sigs

    def _extract_js_signatures(self, file_path: str, content: str) -> List[FunctionSignature]:
        sigs = []
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            match = re.match(
                r'(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)',
                stripped
            )
            if not match:
                match = re.match(
                    r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>',
                    stripped
                )
            if match:
                name = match.group(1)
                params = [p.strip().split('=')[0].strip() for p in match.group(2).split(',') if p.strip()]
                body_hash = hashlib.md5(stripped.encode('utf-8')).hexdigest()
                sigs.append(FunctionSignature(
                    name=name,
                    params=params,
                    file_path=file_path,
                    line=i,
                    body_lines=0,
                    body_hash=body_hash,
                    body_summary=stripped[:80],
                ))
        return sigs

    def _extract_generic_signatures(self, file_path: str, content: str) -> List[FunctionSignature]:
        sigs = []
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            match = re.match(r'(?:function|def|fn|func|sub)\s+(\w+)\s*\(([^)]*)\)', stripped)
            if match:
                name = match.group(1)
                params = [p.strip() for p in match.group(2).split(',') if p.strip()]
                body_hash = hashlib.md5(stripped.encode('utf-8')).hexdigest()
                sigs.append(FunctionSignature(
                    name=name,
                    params=params,
                    file_path=file_path,
                    line=i,
                    body_lines=0,
                    body_hash=body_hash,
                    body_summary=stripped[:80],
                ))
        return sigs

    def _find_similar(self, sigs: List[FunctionSignature]):
        param_groups: Dict[str, List[FunctionSignature]] = defaultdict(list)
        for sig in sigs:
            param_key = str(len(sig.params))
            param_groups[param_key].append(sig)

        for param_key, group in param_groups.items():
            if len(group) < self.min_occurrences:
                continue

            body_hash_groups: Dict[str, List[FunctionSignature]] = defaultdict(list)
            for sig in group:
                body_hash_groups[sig.body_hash].append(sig)

            for body_hash, same_body in body_hash_groups.items():
                if len(same_body) >= self.min_occurrences:
                    self.findings.append({
                        'type': 'similar_function',
                        'pattern_hash': body_hash[:12],
                        'pattern_summary': f"{len(same_body)} functions with same body ({same_body[0].name} pattern)",
                        'occurrence_count': len(same_body),
                        'occurrences': [
                            {
                                'file': s.file_path,
                                'start_line': s.line,
                                'function_name': s.name,
                                'params': s.params,
                            }
                            for s in same_body
                        ],
                        'suggestion': 'Extract shared logic into a common function with parameterized differences',
                    })

            name_groups: Dict[str, List[FunctionSignature]] = defaultdict(list)
            for sig in group:
                name_lower = sig.name.lower()
                for existing_key in list(name_groups.keys()):
                    if self._names_similar(existing_key, name_lower):
                        name_groups[existing_key].append(sig)
                        break
                else:
                    name_groups[name_lower].append(sig)

            for name_key, similar_names in name_groups.items():
                if len(similar_names) >= self.min_occurrences:
                    already_reported = any(
                        f['pattern_hash'] == body_hash[:12]
                        for f in self.findings
                    )
                    if not already_reported:
                        self.findings.append({
                            'type': 'similar_function',
                            'pattern_hash': hashlib.md5(name_key.encode('utf-8')).hexdigest()[:12],
                            'pattern_summary': f"{len(similar_names)} similarly named functions ('{name_key}' pattern)",
                            'occurrence_count': len(similar_names),
                            'occurrences': [
                                {
                                    'file': s.file_path,
                                    'start_line': s.line,
                                    'function_name': s.name,
                                    'params': s.params,
                                }
                                for s in similar_names
                            ],
                            'suggestion': 'Consider merging similar functions or extracting shared logic',
                        })

    def _names_similar(self, name1: str, name2: str) -> bool:
        if name1 == name2:
            return True
        if name1.replace('_', '') == name2.replace('_', ''):
            return True
        if name1.replace('get', '').replace('set', '') == name2.replace('get', '').replace('set', ''):
            return True
        common_prefix = os.path.commonprefix([name1, name2])
        if len(common_prefix) >= min(len(name1), len(name2)) * 0.6:
            return True
        return False


class DuplicateStringDetector:
    def __init__(self, min_occurrences: int):
        self.min_occurrences = min_occurrences
        self.findings: List[Dict[str, Any]] = []

    def detect(self, files: List[Path]):
        string_map: Dict[str, List[Tuple[str, int]]] = defaultdict(list)

        for fpath in files:
            try:
                content = fpath.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            lines = content.splitlines()
            file_str = str(fpath)

            for i, line in enumerate(lines, start=1):
                stripped = line.lstrip()
                if stripped.startswith(('#', '//', '/*', '*')):
                    continue
                for match in re.finditer(r'["\']([^"\']{4,})["\']', line):
                    val = match.group(1)
                    if val.startswith(('http://', 'https://', 'ftp://')):
                        continue
                    string_map[val].append((file_str, i))

        for val, occurrences in string_map.items():
            if len(occurrences) >= self.min_occurrences:
                self.findings.append({
                    'type': 'duplicate_string',
                    'pattern_hash': hashlib.md5(val.encode('utf-8')).hexdigest()[:12],
                    'pattern_summary': f"String '{val[:50]}{'...' if len(val) > 50 else ''}' repeated {len(occurrences)} times",
                    'occurrence_count': len(occurrences),
                    'occurrences': [
                        {
                            'file': occ[0],
                            'start_line': occ[1],
                        }
                        for occ in occurrences
                    ],
                    'suggestion': 'Extract to a named constant to avoid duplication and improve maintainability',
                })


def format_text_report(result: Dict[str, Any]) -> str:
    lines: List[str] = []
    summary = result['summary']

    lines.append('=' * 80)
    lines.append('Deduplication Detection Report')
    lines.append('=' * 80)
    lines.append(f"Timestamp:        {result['timestamp']}")
    lines.append(f"Target:           {result['target']}")
    lines.append(f"Min occurrences:  {result['min_occurrences']}")
    lines.append(f"Files scanned:    {summary['files_scanned']}")
    lines.append('-' * 80)
    lines.append(f"Total patterns:   {summary['total_patterns']}")
    lines.append(f"  Duplicate blocks:   {summary['duplicate_block']}")
    lines.append(f"  Similar functions:  {summary['similar_function']}")
    lines.append(f"  Duplicate strings:  {summary['duplicate_string']}")
    lines.append('=' * 80)

    patterns = result['patterns']
    if not patterns:
        lines.append('No duplicate patterns detected.')
    else:
        for pattern in patterns:
            lines.append('')
            lines.append(f"  [{pattern['type']}] Count: {pattern['occurrence_count']}")
            lines.append(f"    Summary:    {pattern['pattern_summary']}")
            lines.append(f"    Suggestion: {pattern['suggestion']}")
            for occ in pattern['occurrences']:
                line_info = f":{occ['start_line']}" if 'start_line' in occ else ''
                func_info = f" ({occ['function_name']})" if 'function_name' in occ else ''
                lines.append(f"      - {occ['file']}{line_info}{func_info}")

    lines.append('')
    lines.append('=' * 80)
    return '\n'.join(lines)


def main():
    args = parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.is_dir():
        print(f"Target is not a directory: {args.target}", file=sys.stderr)
        sys.exit(2)

    files = collect_files(args.target)
    if not files:
        print("No source files found to analyze.", file=sys.stderr)
        sys.exit(2)

    block_detector = SlidingWindowBlockDetector(args.min_occurrences)
    block_detector.detect(files)

    function_detector = SimilarFunctionDetector(args.min_occurrences)
    function_detector.detect(files)

    string_detector = DuplicateStringDetector(args.min_occurrences)
    string_detector.detect(files)

    all_patterns = block_detector.findings + function_detector.findings + string_detector.findings

    type_counts: Dict[str, int] = {
        'duplicate_block': 0,
        'similar_function': 0,
        'duplicate_string': 0,
    }
    for p in all_patterns:
        ptype = p['type']
        if ptype in type_counts:
            type_counts[ptype] += 1

    result = {
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'target': str(target_path),
        'min_occurrences': args.min_occurrences,
        'summary': {
            'files_scanned': len(files),
            'total_patterns': len(all_patterns),
            **type_counts,
        },
        'patterns': all_patterns,
    }

    if args.format == 'json':
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = format_text_report(result)

    sys.stdout.buffer.write(output.encode('utf-8'))
    sys.stdout.buffer.write(b'\n')

    if all_patterns:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
