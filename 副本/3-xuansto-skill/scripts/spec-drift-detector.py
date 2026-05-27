#!/usr/bin/env python3
"""
规格漂移检测脚本
功能：检测规格文档与实际代码实现之间的差异
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='规格漂移检测脚本 - 检测规格文档与代码实现的差异'
    )
    parser.add_argument(
        '--spec-dir',
        type=str,
        default='.trae/specs',
        help='规格文档目录（默认：.trae/specs）'
    )
    parser.add_argument(
        '--src-dir',
        type=str,
        default='.',
        help='源代码目录（默认：.）'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['json', 'text'],
        default='json',
        help='输出格式：json或text（默认：json）'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='输出文件路径（默认：stdout）'
    )
    return parser.parse_args()


SOURCE_EXTENSIONS = {
    '.py', '.js', '.ts', '.tsx', '.jsx', '.vue', '.svelte',
    '.java', '.go', '.rs', '.rb', '.php', '.cs', '.swift',
    '.kt', '.c', '.cpp', '.h', '.hpp',
}

SPEC_EXTENSIONS = {'.md', '.markdown'}

REQUIREMENT_KEYWORDS = {
    'SHALL': 'critical',
    'MUST': 'high',
    'SHOULD': 'medium',
}

IGNORED_DIRS = {
    'node_modules', '.git', '__pycache__', '.venv', 'venv',
    'dist', 'build', '.next', '.nuxt', 'target', 'bin',
    'obj', '.idea', '.vscode', 'coverage', '.cache',
}


class Requirement:
    """从规格文档中提取的单条需求"""

    def __init__(self, keyword: str, text: str, spec_file: str,
                 line_number: int, severity: str):
        self.keyword = keyword
        self.text = text
        self.spec_file = spec_file
        self.line_number = line_number
        self.severity = severity
        self.identifiers: List[str] = []
        self._extract_identifiers()

    def _extract_identifiers(self):
        """从需求文本中提取可能的代码标识符"""
        camel_case = re.findall(
            r'[A-Z][a-zA-Z0-9]{2,}', self.text
        )
        snake_case = re.findall(
            r'[a-z][a-z0-9]+(?:_[a-z0-9]+){1,}', self.text
        )
        kebab_case = re.findall(
            r'[a-z][a-z0-9]+(?:-[a-z0-9]+){1,}', self.text
        )
        quoted = re.findall(
            r'[`"\']([A-Za-z_][A-Za-z0-9_\-\.]*)[`"\']', self.text
        )
        self.identifiers = list(set(
            camel_case + snake_case + kebab_case + quoted
        ))
        self.identifiers = [
            ident for ident in self.identifiers
            if len(ident) >= 3 and ident not in REQUIREMENT_KEYWORDS
        ]

    @property
    def spec_ref(self) -> str:
        """规格引用路径"""
        return f"{self.spec_file}#L{self.line_number}"


class SpecParser:
    """规格文档解析器"""

    def __init__(self, spec_dir: str):
        self.spec_dir = Path(spec_dir)
        self.requirements: List[Requirement] = []
        self.spec_files: List[str] = []
        self.versions: Dict[str, str] = {}

    def parse(self) -> bool:
        """
        解析规格目录下所有Markdown文件

        返回:
            是否成功解析
        """
        if not self.spec_dir.exists():
            print(f"规格目录不存在: {self.spec_dir}", file=sys.stderr)
            return False

        md_files = self._find_spec_files()
        if not md_files:
            print(f"规格目录中未找到Markdown文件: {self.spec_dir}", file=sys.stderr)
            return False

        for md_file in md_files:
            rel_path = str(md_file.relative_to(self.spec_dir))
            self.spec_files.append(rel_path)
            self._parse_file(md_file, rel_path)

        return True

    def _find_spec_files(self) -> List[Path]:
        """递归查找所有规格Markdown文件"""
        result = []
        for root, dirs, files in os.walk(self.spec_dir):
            dirs[:] = [
                d for d in dirs
                if d not in IGNORED_DIRS and not d.startswith('.')
            ]
            for fname in files:
                fpath = Path(root) / fname
                if fpath.suffix.lower() in SPEC_EXTENSIONS:
                    result.append(fpath)
        result.sort()
        return result

    def _parse_file(self, file_path: Path, rel_path: str):
        """
        解析单个规格文件

        参数:
            file_path: 文件绝对路径
            rel_path: 相对于规格目录的相对路径
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError) as e:
            print(f"读取文件失败 {file_path}: {e}", file=sys.stderr)
            return

        for line_num, line in enumerate(content.splitlines(), start=1):
            self._extract_requirements(line, rel_path, line_num)
            self._extract_version(line, rel_path)

    def _extract_requirements(self, line: str, spec_file: str,
                              line_number: int):
        """
        从单行文本中提取需求

        参数:
            line: 单行文本
            spec_file: 规格文件相对路径
            line_number: 行号
        """
        for keyword, severity in REQUIREMENT_KEYWORDS.items():
            pattern = re.compile(
                rf'\b{keyword}\b',
                re.IGNORECASE
            )
            if pattern.search(line):
                clean = line.strip()
                if (clean and not clean.startswith('#')) or (
                    clean.startswith('#') and len(clean) > 1
                ):
                    self.requirements.append(
                        Requirement(keyword, clean, spec_file,
                                    line_number, severity)
                    )
                break

    def _extract_version(self, line: str, spec_file: str):
        """
        提取版本声明

        参数:
            line: 单行文本
            spec_file: 规格文件相对路径
        """
        version_pattern = re.compile(
            r'(?:version|版本)\s*[:：]?\s*["\']?'
            r'(\d+\.\d+(?:\.\d+)?)["\']?',
            re.IGNORECASE
        )
        match = version_pattern.search(line)
        if match:
            self.versions[spec_file] = match.group(1)


class CodeIndex:
    """源代码索引"""

    def __init__(self, src_dir: str):
        self.src_dir = Path(src_dir)
        self.class_names: List[str] = []
        self.function_names: List[str] = []
        self.config_keys: List[str] = []
        self.route_paths: List[str] = []
        self.all_identifiers: List[str] = []
        self.file_count: int = 0

    def build(self):
        """构建源代码索引"""
        if not self.src_dir.exists():
            print(f"源代码目录不存在: {self.src_dir}", file=sys.stderr)
            return

        for root, dirs, files in os.walk(self.src_dir):
            dirs[:] = [
                d for d in dirs
                if d not in IGNORED_DIRS and not d.startswith('.')
            ]
            for fname in files:
                fpath = Path(root) / fname
                if fpath.suffix.lower() in SOURCE_EXTENSIONS:
                    self._index_file(fpath)
                    self.file_count += 1

        self.all_identifiers = list(set(
            self.class_names + self.function_names + self.config_keys
        ))

    def _index_file(self, file_path: Path):
        """
        索引单个源代码文件

        参数:
            file_path: 文件路径
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            return

        suffix = file_path.suffix.lower()

        if suffix == '.py':
            self._index_python(content)
        elif suffix in {'.js', '.ts', '.tsx', '.jsx', '.vue', '.svelte'}:
            self._index_javascript(content)
        elif suffix == '.go':
            self._index_go(content)
        elif suffix == '.java':
            self._index_java(content)
        elif suffix == '.rs':
            self._index_rust(content)
        else:
            self._index_generic(content)

        self._index_routes(content)
        self._index_config_keys(content)

    def _index_python(self, content: str):
        """索引Python代码标识符"""
        for match in re.finditer(
            r'^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)', content, re.MULTILINE
        ):
            self.class_names.append(match.group(1))

        for match in re.finditer(
            r'^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)', content, re.MULTILINE
        ):
            self.function_names.append(match.group(1))

    def _index_javascript(self, content: str):
        """索引JavaScript/TypeScript代码标识符"""
        for match in re.finditer(
            r'\bclass\s+([A-Za-z_$][A-Za-z0-9_$]*)', content
        ):
            self.class_names.append(match.group(1))

        for match in re.finditer(
            r'\b(?:function\s+|const\s+|let\s+|var\s+)'
            r'([A-Za-z_$][A-Za-z0-9_$]*)\s*(?:=\s*(?:async\s+)?'
            r'(?:function|\([^)]*\)\s*=>)|\()',
            content
        ):
            self.function_names.append(match.group(1))

        for match in re.finditer(
            r'(?:export\s+(?:default\s+)?)?'
            r'function\s+([A-Za-z_$][A-Za-z0-9_$]*)', content
        ):
            self.function_names.append(match.group(1))

    def _index_go(self, content: str):
        """索引Go代码标识符"""
        for match in re.finditer(
            r'\btype\s+([A-Za-z_][A-Za-z0-9_]*)\s+struct', content
        ):
            self.class_names.append(match.group(1))

        for match in re.finditer(
            r'\bfunc\s+(?:\([^)]+\)\s*)?([A-Za-z_][A-Za-z0-9_]*)', content
        ):
            self.function_names.append(match.group(1))

    def _index_java(self, content: str):
        """索引Java代码标识符"""
        for match in re.finditer(
            r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)', content
        ):
            self.class_names.append(match.group(1))

        for match in re.finditer(
            r'\b(?:public|private|protected)?\s*(?:static\s+)?'
            r'(?:\w+\s+)+([A-Za-z_][A-Za-z0-9_]*)\s*\(', content
        ):
            name = match.group(1)
            if name not in {'if', 'for', 'while', 'switch', 'catch', 'new'}:
                self.function_names.append(name)

    def _index_rust(self, content: str):
        """索引Rust代码标识符"""
        for match in re.finditer(
            r'\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)', content
        ):
            self.class_names.append(match.group(1))

        for match in re.finditer(
            r'\bfn\s+([A-Za-z_][A-Za-z0-9_]*)', content
        ):
            self.function_names.append(match.group(1))

    def _index_generic(self, content: str):
        """通用标识符索引"""
        for match in re.finditer(
            r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)', content
        ):
            self.class_names.append(match.group(1))

        for match in re.finditer(
            r'\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)', content
        ):
            self.function_names.append(match.group(1))

    def _index_routes(self, content: str):
        """索引路由路径"""
        for match in re.finditer(
            r'(?:app|router|Route)\s*\.\s*(?:get|post|put|delete|patch|use)'
            r'\s*\(\s*["\']([^"\']+)["\']',
            content
        ):
            self.route_paths.append(match.group(1))

        for match in re.finditer(
            r'@(?:Get|Post|Put|Delete|Patch|RequestMapping)'
            r'(?:Mapping)?\s*\(\s*["\']([^"\']+)["\']',
            content
        ):
            self.route_paths.append(match.group(1))

    def _index_config_keys(self, content: str):
        """索引配置键名"""
        for match in re.finditer(
            r'(?:process\.env\.|import\.meta\.env\.|os\.environ\.get\()'
            r'([A-Za-z_][A-Za-z0-9_]*)',
            content
        ):
            self.config_keys.append(match.group(1))

        for match in re.finditer(
            r'["\']([A-Z][A-Z0-9_]{2,})["\']\s*:', content
        ):
            self.config_keys.append(match.group(1))

    def search_evidence(self, requirement: Requirement) -> List[str]:
        """
        搜索需求在代码中的实现证据

        参数:
            requirement: 需求对象

        返回:
            匹配到的标识符列表
        """
        evidence: List[str] = []

        text_lower = requirement.text.lower()

        keyword_map = self._build_keyword_map(requirement)

        for identifier in self.all_identifiers:
            ident_lower = identifier.lower()

            if ident_lower in text_lower:
                evidence.append(identifier)
                continue

            for kw in keyword_map:
                if kw in ident_lower or ident_lower in kw:
                    evidence.append(identifier)
                    break

        for route in self.route_paths:
            route_parts = [
                p for p in route.strip('/').split('/')
                if p and not p.startswith('{') and not p.startswith(':')
            ]
            for part in route_parts:
                part_lower = part.lower()
                for kw in keyword_map:
                    if part_lower in kw or kw in part_lower:
                        evidence.append(f"route:{route}")
                        break

        for config_key in self.config_keys:
            config_lower = config_key.lower()
            for kw in keyword_map:
                if config_lower in kw or kw in config_lower:
                    evidence.append(f"config:{config_key}")
                    break

        return list(set(evidence))

    def _build_keyword_map(self, requirement: Requirement) -> List[str]:
        """
        构建需求的关键词映射表

        参数:
            requirement: 需求对象

        返回:
            小写关键词列表
        """
        keywords: List[str] = []

        for ident in requirement.identifiers:
            keywords.append(ident.lower())

        words = re.findall(r'[A-Za-z]{3,}', requirement.text)
        for word in words:
            w_lower = word.lower()
            if w_lower not in REQUIREMENT_KEYWORDS and len(w_lower) >= 4:
                keywords.append(w_lower)

        return list(set(keywords))


class DriftDetector:
    """漂移检测器"""

    def __init__(self, spec_parser: SpecParser, code_index: CodeIndex):
        self.spec_parser = spec_parser
        self.code_index = code_index
        self.drifts: List[Dict[str, Any]] = []
        self.drift_counter: int = 0

    def detect(self) -> Dict[str, Any]:
        """
        执行漂移检测

        返回:
            检测结果字典
        """
        self._detect_missing_implementations()
        self._detect_orphaned_code()
        self._detect_version_mismatches()

        total = len(self.spec_parser.requirements)
        missing = sum(
            1 for d in self.drifts
            if d['type'] == 'missing_implementation'
        )
        orphaned = sum(
            1 for d in self.drifts
            if d['type'] == 'orphaned_code'
        )
        implemented = total - missing
        compliance_rate = round(
            implemented / total, 2
        ) if total > 0 else 1.0

        return {
            'timestamp': datetime.now(timezone.utc).strftime(
                '%Y-%m-%dT%H:%M:%SZ'
            ),
            'spec_dir': str(self.spec_parser.spec_dir),
            'src_dir': str(self.code_index.src_dir),
            'summary': {
                'total_requirements': total,
                'implemented': implemented,
                'missing': missing,
                'orphaned': orphaned,
                'compliance_rate': compliance_rate,
            },
            'drifts': self.drifts,
        }

    def _next_drift_id(self) -> str:
        """生成下一个漂移ID"""
        self.drift_counter += 1
        return f"DRIFT-{self.drift_counter:03d}"

    def _detect_missing_implementations(self):
        """检测缺失的实现"""
        for req in self.spec_parser.requirements:
            evidence = self.code_index.search_evidence(req)

            if not evidence:
                self.drifts.append({
                    'id': self._next_drift_id(),
                    'type': 'missing_implementation',
                    'severity': req.severity,
                    'spec_ref': req.spec_ref,
                    'requirement': req.text,
                    'evidence': '未找到相关代码实现',
                    'suggestion': self._suggest_implementation(req),
                })

    def _detect_orphaned_code(self):
        """检测孤立代码（无规格对应的代码）"""
        spec_identifiers: List[str] = []
        for req in self.spec_parser.requirements:
            spec_identifiers.extend(
                ident.lower() for ident in req.identifiers
            )
            words = re.findall(r'[A-Za-z]{3,}', req.text)
            spec_identifiers.extend(
                w.lower() for w in words if len(w) >= 4
            )

        spec_identifiers = list(set(spec_identifiers))

        checked: set = set()
        for identifier in self.code_index.all_identifiers:
            ident_lower = identifier.lower()
            if ident_lower in checked:
                continue
            checked.add(ident_lower)

            if self._is_common_name(identifier):
                continue

            matched = False
            for spec_ident in spec_identifiers:
                if len(spec_ident) < 3:
                    continue
                if (spec_ident.startswith(ident_lower)
                        or ident_lower.startswith(spec_ident)):
                    matched = True
                    break

            if not matched:
                self.drifts.append({
                    'id': self._next_drift_id(),
                    'type': 'orphaned_code',
                    'severity': 'low',
                    'spec_ref': '-',
                    'requirement': f'代码标识符: {identifier}',
                    'evidence': f'未在规格文档中找到对 {identifier} 的定义',
                    'suggestion': f'确认 {identifier} 是否需要补充规格说明或为冗余代码',
                })

    def _detect_version_mismatches(self):
        """检测版本不匹配"""
        if not self.spec_parser.versions:
            return

        for spec_file, spec_version in self.spec_parser.versions.items():
            package_files = self._find_package_files()
            for pkg_file in package_files:
                pkg_version = self._extract_package_version(pkg_file)
                if pkg_version and pkg_version != spec_version:
                    self.drifts.append({
                        'id': self._next_drift_id(),
                        'type': 'version_mismatch',
                        'severity': 'medium',
                        'spec_ref': f"{spec_file}",
                        'requirement': f'版本应为 {spec_version}',
                        'evidence': f'{pkg_file.name} 中版本为 {pkg_version}',
                        'suggestion': f'将版本从 {pkg_version} 更新至 {spec_version}',
                    })

    def _find_package_files(self) -> List[Path]:
        """查找项目包文件"""
        package_names = [
            'package.json', 'pyproject.toml', 'setup.py',  # setup.py is legacy
            'Cargo.toml', 'go.mod', 'pom.xml',
        ]
        result = []
        for name in package_names:
            fpath = self.code_index.src_dir / name
            if fpath.exists():
                result.append(fpath)
        return result

    def _extract_package_version(self, pkg_file: Path) -> Optional[str]:
        """
        从包文件中提取版本号

        参数:
            pkg_file: 包文件路径

        返回:
            版本号字符串或None
        """
        try:
            content = pkg_file.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            return None

        if pkg_file.name == 'package.json':
            match = re.search(
                r'"version"\s*:\s*"(\d+\.\d+(?:\.\d+)?)', content
            )
            return match.group(1) if match else None

        if pkg_file.name in {'pyproject.toml', 'setup.py'}:  # setup.py is legacy
            match = re.search(
                r'version\s*=\s*["\'](\d+\.\d+(?:\.\d+)?)["\']', content
            )
            return match.group(1) if match else None

        if pkg_file.name == 'Cargo.toml':
            match = re.search(
                r'version\s*=\s*"(\d+\.\d+(?:\.\d+)?)', content
            )
            return match.group(1) if match else None

        return None

    def _is_common_name(self, name: str) -> bool:
        """
        判断是否为通用名称（不应标记为孤立代码）

        参数:
            name: 标识符名称

        返回:
            是否为通用名称
        """
        common = {
            'main', 'init', 'setup', 'run', 'start', 'stop',
            'handle', 'process', 'execute', 'perform', 'create',
            'update', 'delete', 'get', 'set', 'add', 'remove',
            'check', 'validate', 'parse', 'format', 'convert',
            'load', 'save', 'read', 'write', 'open', 'close',
            'connect', 'disconnect', 'send', 'receive', 'encode',
            'decode', 'serialize', 'deserialize', 'clone', 'copy',
            'equals', 'hash', 'tostring', 'valueof', 'compare',
            'index', 'test', 'helper', 'util', 'utils', 'config',
            'logger', 'log', 'error', 'warn', 'info', 'debug',
            'App', 'Config', 'Logger', 'Handler', 'Manager',
            'Factory', 'Builder', 'Service', 'Controller',
            'Repository', 'Model', 'View', 'Component',
        }
        return name in common or name.startswith('__')

    def _suggest_implementation(self, req: Requirement) -> str:
        """
        根据需求生成实现建议

        参数:
            req: 需求对象

        返回:
            建议字符串
        """
        text_lower = req.text.lower()

        if any(kw in text_lower for kw in
               ['auth', 'login', 'password', 'token']):
            return '实现身份认证模块'
        if any(kw in text_lower for kw in
               ['database', 'db', 'storage', 'persist']):
            return '实现数据持久化层'
        if any(kw in text_lower for kw in
               ['api', 'endpoint', 'route', 'rest']):
            return '实现API接口层'
        if any(kw in text_lower for kw in
               ['test', 'testing', 'coverage']):
            return '补充测试用例'
        if any(kw in text_lower for kw in
               ['log', 'monitor', 'metric', 'trace']):
            return '实现日志监控模块'
        if any(kw in text_lower for kw in
               ['cache', 'redis', 'memo']):
            return '实现缓存机制'
        if any(kw in text_lower for kw in
               ['queue', 'message', 'event', 'async']):
            return '实现消息队列/事件系统'
        if any(kw in text_lower for kw in
               ['config', 'setting', 'env', 'environment']):
            return '实现配置管理模块'
        if any(kw in text_lower for kw in
               ['error', 'exception', 'handle', 'retry']):
            return '实现错误处理机制'
        if any(kw in text_lower for kw in
               ['security', 'encrypt', 'decrypt', 'hash']):
            return '实现安全模块'

        return '根据规格要求实现相应功能'


def format_text_report(result: Dict[str, Any]) -> str:
    """
    格式化文本报告

    参数:
        result: 检测结果字典

    返回:
        格式化的文本字符串
    """
    lines: List[str] = []

    summary = result['summary']
    lines.append('=' * 80)
    lines.append('规格漂移检测报告')
    lines.append('=' * 80)
    lines.append(f"检测时间:   {result['timestamp']}")
    lines.append(f"规格目录:   {result['spec_dir']}")
    lines.append(f"源码目录:   {result['src_dir']}")
    lines.append('-' * 80)
    lines.append(f"需求总数:   {summary['total_requirements']}")
    lines.append(f"已实现:     {summary['implemented']}")
    lines.append(f"缺失实现:   {summary['missing']}")
    lines.append(f"孤立代码:   {summary['orphaned']}")
    lines.append(f"合规率:     {summary['compliance_rate']:.0%}")
    lines.append('=' * 80)

    drifts = result['drifts']
    if not drifts:
        lines.append('未检测到规格漂移')
    else:
        lines.append(f"检测到 {len(drifts)} 项漂移:")
        lines.append('')

        header = (
            f"{'ID':<12} {'类型':<22} {'严重度':<10} "
            f"{'需求描述':<36} {'建议':<30}"
        )
        lines.append(header)
        lines.append('-' * 110)

        for drift in drifts:
            req_short = drift['requirement'][:34] + '..' if len(
                drift['requirement']
            ) > 36 else drift['requirement']
            sug_short = drift['suggestion'][:28] + '..' if len(
                drift['suggestion']
            ) > 30 else drift['suggestion']

            type_map = {
                'missing_implementation': '缺失实现',
                'orphaned_code': '孤立代码',
                'version_mismatch': '版本不匹配',
            }
            type_cn = type_map.get(drift['type'], drift['type'])

            sev_map = {
                'critical': '严重',
                'high': '高',
                'medium': '中',
                'low': '低',
            }
            sev_cn = sev_map.get(drift['severity'], drift['severity'])

            line = (
                f"{drift['id']:<12} {type_cn:<22} {sev_cn:<10} "
                f"{req_short:<36} {sug_short:<30}"
            )
            lines.append(line)

    lines.append('=' * 80)
    return '\n'.join(lines)


def main():
    """主函数"""
    args = parse_args()

    spec_parser = SpecParser(args.spec_dir)
    if not spec_parser.parse():
        sys.exit(2)

    code_index = CodeIndex(args.src_dir)
    code_index.build()

    if code_index.file_count == 0 and len(spec_parser.requirements) > 0:
        print("警告: 源代码目录中未找到代码文件", file=sys.stderr)

    detector = DriftDetector(spec_parser, code_index)
    result = detector.detect()

    if args.format == 'json':
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = format_text_report(result)

    if args.output:
        try:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output, encoding='utf-8')
        except OSError as e:
            print(f"写入输出文件失败: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        print(output)

    has_drift = (
        result['summary']['missing'] > 0
        or result['summary']['orphaned'] > 0
    )
    if has_drift:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
