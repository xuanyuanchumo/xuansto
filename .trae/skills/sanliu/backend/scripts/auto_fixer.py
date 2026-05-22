#!/usr/bin/env python3
"""
自动修复脚本 - 自动修复常见问题，支持多种修复策略，生成修复报告，记录修复历史
集成日志分析和问题定位能力，实现端到端的自动修复流程
增强功能：修复预览、智能验证、回滚机制、修复置信度评估
"""

import re
import json
import os
import sys
import ast
import shutil
import hashlib
import subprocess
import difflib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple, Callable, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from enum import Enum, auto
import argparse
import logging
import tempfile


class FixStrategy(Enum):
    SYNTAX_FIX = "syntax_fix"
    IMPORT_FIX = "import_fix"
    FORMAT_FIX = "format_fix"
    SECURITY_FIX = "security_fix"
    PERFORMANCE_FIX = "performance_fix"
    STYLE_FIX = "style_fix"
    TYPE_FIX = "type_fix"
    REFACTOR_FIX = "refactor_fix"
    LOGIC_FIX = "logic_fix"
    DEPENDENCY_FIX = "dependency_fix"
    CONFIGURATION_FIX = "configuration_fix"
    DOCUMENTATION_FIX = "documentation_fix"
    TEST_FIX = "test_fix"
    MANUAL_REQUIRED = "manual_required"


class FixStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    VERIFIED = "verified"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"
    NEEDS_REVIEW = "needs_review"


class FixRisk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FixAttempt:
    attempt_id: str
    strategy: FixStrategy
    file_path: str
    line_number: int
    original_code: str
    modified_code: str
    description: str
    status: FixStatus
    timestamp: datetime
    error_message: Optional[str] = None
    verification_result: Optional[bool] = None
    backup_path: Optional[str] = None
    confidence: float = 0.0
    risk: FixRisk = FixRisk.MEDIUM
    diff: str = ""
    preview_only: bool = False


@dataclass
class FixPreview:
    file_path: str
    original_content: str
    modified_content: str
    diff: str
    changes: List[Dict[str, Any]]
    risk_level: FixRisk
    confidence: float
    can_auto_apply: bool


@dataclass
class VerificationResult:
    passed: bool
    checks: List[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    score: float


@dataclass
class FixHistory:
    history_id: str
    timestamp: str
    total_attempts: int
    successful_fixes: int
    failed_fixes: int
    rolled_back_fixes: int
    attempts: List[FixAttempt]
    affected_files: Set[str] = field(default_factory=set)


@dataclass
class AutoFixResult:
    success: bool
    file_path: str
    fix_count: int
    failed_count: int
    issues_remaining: int
    report_path: Optional[str] = None
    error_message: Optional[str] = None
    previews: List[FixPreview] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    verification_score: float = 0.0


class SyntaxFixer:
    """语法错误修复器"""

    COMMON_SYNTAX_ERRORS = {
        r"expected ':'$": {
            "fix": "add_colon",
            "description": "添加缺失的冒号"
        },
        r"unexpected indent": {
            "fix": "fix_indentation",
            "description": "修复缩进问题"
        },
        r"unexpected EOF": {
            "fix": "add_missing_bracket",
            "description": "添加缺失的括号"
        },
        r"EOL while scanning string literal": {
            "fix": "close_string",
            "description": "关闭字符串引号"
        },
        r"invalid syntax.*print ": {
            "fix": "fix_print_statement",
            "description": "将Python 2 print语句改为函数"
        },
    }

    def __init__(self):
        self.compiled_patterns = {
            re.compile(pattern, re.IGNORECASE): fix_info
            for pattern, fix_info in self.COMMON_SYNTAX_ERRORS.items()
        }

    def can_fix(self, error_message: str) -> bool:
        """检查是否可以修复"""
        for pattern in self.compiled_patterns:
            if pattern.search(error_message):
                return True
        return False

    def fix(self, file_path: str, error_message: str, line_number: int) -> Optional[str]:
        """尝试修复语法错误"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if line_number < 1 or line_number > len(lines):
                return None

            for pattern, fix_info in self.compiled_patterns.items():
                if pattern.search(error_message):
                    fix_method = getattr(self, f"_{fix_info['fix']}", None)
                    if fix_method:
                        return fix_method(lines, line_number - 1)

            return None

        except Exception as e:
            logging.error(f"语法修复失败: {e}")
            return None

    def _add_colon(self, lines: List[str], line_idx: int) -> Optional[str]:
        """添加缺失的冒号"""
        line = lines[line_idx]
        stripped = line.strip()

        if stripped.startswith(('def ', 'class ', 'if ', 'elif ', 'else', 'for ', 'while ', 'try', 'except', 'finally', 'with ')):
            if not stripped.rstrip().endswith(':'):
                lines[line_idx] = line.rstrip() + ':\n'
                return ''.join(lines)

        return None

    def _fix_indentation(self, lines: List[str], line_idx: int) -> Optional[str]:
        """修复缩进问题"""
        if line_idx == 0:
            return None

        prev_line = lines[line_idx - 1]
        curr_line = lines[line_idx]

        prev_indent = len(prev_line) - len(prev_line.lstrip())

        if prev_line.rstrip().endswith(':'):
            expected_indent = prev_indent + 4
        else:
            expected_indent = prev_indent

        curr_indent = len(curr_line) - len(curr_line.lstrip())

        if curr_indent != expected_indent:
            lines[line_idx] = ' ' * expected_indent + curr_line.lstrip()
            return ''.join(lines)

        return None

    def _add_missing_bracket(self, lines: List[str], line_idx: int) -> Optional[str]:
        """添加缺失的括号"""
        content = ''.join(lines)

        open_parens = content.count('(') - content.count(')')
        open_brackets = content.count('[') - content.count(']')
        open_braces = content.count('{') - content.count('}')

        if open_parens > 0:
            lines.append(')' * open_parens + '\n')
        if open_brackets > 0:
            lines.append(']' * open_brackets + '\n')
        if open_braces > 0:
            lines.append('}' * open_braces + '\n')

        if open_parens > 0 or open_brackets > 0 or open_braces > 0:
            return ''.join(lines)

        return None

    def _close_string(self, lines: List[str], line_idx: int) -> Optional[str]:
        """关闭字符串引号"""
        line = lines[line_idx]

        single_quotes = line.count("'") - line.count("\\'")
        double_quotes = line.count('"') - line.count('\\"')

        if single_quotes % 2 == 1:
            lines[line_idx] = line.rstrip() + "'\n"
            return ''.join(lines)
        elif double_quotes % 2 == 1:
            lines[line_idx] = line.rstrip() + '"\n'
            return ''.join(lines)

        return None

    def _fix_print_statement(self, lines: List[str], line_idx: int) -> Optional[str]:
        """修复Python 2的print语句"""
        line = lines[line_idx]

        match = re.match(r'(\s*)print\s+(.+)$', line)
        if match:
            indent, content = match.groups()
            lines[line_idx] = f"{indent}print({content})\n"
            return ''.join(lines)

        return None


class ImportFixer:
    """导入问题修复器"""

    COMMON_MISSING_MODULES = {
        'requests': 'requests',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'flask': 'Flask',
        'django': 'Django',
        'fastapi': 'fastapi',
        'pydantic': 'pydantic',
        'sqlalchemy': 'SQLAlchemy',
        'pytest': 'pytest',
        'black': 'black',
        'flake8': 'flake8',
        'mypy': 'mypy',
        'isort': 'isort',
    }

    def can_fix(self, error_message: str) -> bool:
        """检查是否可以修复导入错误"""
        return 'ModuleNotFoundError' in error_message or 'ImportError' in error_message

    def fix(self, file_path: str, error_message: str, line_number: int) -> Optional[str]:
        """尝试修复导入错误"""
        match = re.search(r"No module named '([^']+)'", error_message)
        if not match:
            match = re.search(r"cannot import name '([^']+)'", error_message)

        if match:
            module_name = match.group(1)
            package = self.COMMON_MISSING_MODULES.get(module_name)

            if package:
                try:
                    subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', package],
                        check=True,
                        capture_output=True,
                        timeout=60
                    )
                    return "installed"
                except subprocess.CalledProcessError:
                    return None

        return None

    def generate_requirements(self, file_paths: List[str]) -> str:
        """生成requirements.txt内容"""
        imports = set()

        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split('.')[0])

            except Exception:
                continue

        requirements = []
        for imp in sorted(imports):
            package = self.COMMON_MISSING_MODULES.get(imp, imp)
            requirements.append(package)

        return '\n'.join(requirements)


class SecurityFixer:
    """安全问题修复器"""

    SECURITY_PATTERNS = {
        r'password\s*=\s*["\'][^"\']+["\']': {
            "fix": "extract_to_env",
            "description": "将硬编码密码提取到环境变量"
        },
        r'secret\s*=\s*["\'][^"\']+["\']': {
            "fix": "extract_to_env",
            "description": "将硬编码密钥提取到环境变量"
        },
        r'api_key\s*=\s*["\'][^"\']+["\']': {
            "fix": "extract_to_env",
            "description": "将硬编码API密钥提取到环境变量"
        },
        r'eval\s*\(': {
            "fix": "replace_eval",
            "description": "将eval替换为安全的替代方案"
        },
        r'exec\s*\(': {
            "fix": "replace_exec",
            "description": "将exec替换为安全的替代方案"
        },
        r'yaml\.load\s*\((?!.*Loader)': {
            "fix": "fix_yaml_load",
            "description": "使用SafeLoader加载YAML"
        },
        r'pickle\.loads?\s*\(': {
            "fix": "warn_pickle",
            "description": "警告pickle安全风险"
        },
    }

    def __init__(self):
        self.compiled_patterns = {
            re.compile(pattern, re.IGNORECASE): fix_info
            for pattern, fix_info in self.SECURITY_PATTERNS.items()
        }

    def scan_and_fix(self, file_path: str) -> List[Dict[str, Any]]:
        """扫描并修复安全问题"""
        fixes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            for pattern, fix_info in self.compiled_patterns.items():
                for match in pattern.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    original_line = lines[line_num - 1] if line_num <= len(lines) else ""

                    fix_method = getattr(self, f"_{fix_info['fix']}", None)
                    if fix_method:
                        result = fix_method(original_line, file_path)
                        if result:
                            fixes.append({
                                'line': line_num,
                                'original': original_line,
                                'fixed': result['code'],
                                'description': fix_info['description'],
                                'warning': result.get('warning', False)
                            })

        except Exception as e:
            logging.error(f"安全扫描失败: {e}")

        return fixes

    def _extract_to_env(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """提取到环境变量"""
        match = re.match(r'(\s*)(\w+)\s*=\s*["\']([^"\']+)["\']', line)
        if match:
            indent, var_name, value = match.groups()
            return {
                'code': f'{indent}{var_name} = os.environ.get("{var_name.upper()}", "")',
                'warning': True
            }
        return None

    def _replace_eval(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """替换eval"""
        match = re.search(r'eval\s*\(([^)]+)\)', line)
        if match:
            expr = match.group(1)
            return {
                'code': line.replace(f'eval({expr})', f'ast.literal_eval({expr})'),
                'warning': True
            }
        return None

    def _replace_exec(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """替换exec"""
        return {
            'code': f'# WARNING: exec() is dangerous. Consider using a safer alternative\n# {line}',
            'warning': True
        }

    def _fix_yaml_load(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """修复yaml.load"""
        return {
            'code': re.sub(
                r'yaml\.load\s*\(([^)]+)\)',
                r'yaml.load(\1, Loader=yaml.SafeLoader)',
                line
            ),
            'warning': False
        }

    def _warn_pickle(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """警告pickle使用"""
        return {
            'code': f'# SECURITY WARNING: pickle can execute arbitrary code\n# {line}',
            'warning': True
        }


class EnhancedSecurityFixer(SecurityFixer):
    """增强的安全问题修复器"""

    def __init__(self):
        super().__init__()
        self.additional_patterns = {
            r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True': {
                "fix": "fix_shell_true",
                "description": "避免使用shell=True，存在命令注入风险"
            },
            r'os\.system\s*\(': {
                "fix": "replace_os_system",
                "description": "os.system存在命令注入风险，使用subprocess替代"
            },
            r'(?:md5|sha1)\s*\(': {
                "fix": "warn_weak_hash",
                "description": "使用弱哈希算法，建议使用sha256或更强算法"
            },
            r'random\.random\s*\(': {
                "fix": "warn_insecure_random",
                "description": "random模块不安全，密码学用途请使用secrets模块"
            },
            r'ssl\._create_unverified_context': {
                "fix": "fix_ssl_verify",
                "description": "禁用SSL证书验证，存在中间人攻击风险"
            },
            r'TEMP\s*=\s*["\']/(?:tmp|var/tmp)["\']': {
                "fix": "warn_insecure_temp",
                "description": "使用不安全的临时目录"
            },
            r'chmod\s*\(.*777': {
                "fix": "warn_insecure_permission",
                "description": "设置过于宽松的文件权限"
            },
            r'cursor\.execute\s*\([^)]*\+': {
                "fix": "fix_sql_injection",
                "description": "SQL拼接存在注入风险，使用参数化查询"
            },
        }
        
        for pattern, fix_info in self.additional_patterns.items():
            self.compiled_patterns[re.compile(pattern, re.IGNORECASE)] = fix_info

    def _fix_shell_true(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """修复shell=True问题"""
        if 'shell=True' in line:
            new_line = line.replace('shell=True', 'shell=False')
            return {
                'code': f'# SECURITY: Avoid shell=True to prevent command injection\n{new_line}',
                'warning': True
            }
        return None

    def _replace_os_system(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """替换os.system"""
        match = re.search(r'os\.system\s*\(\s*([^)]+)\s*\)', line)
        if match:
            cmd = match.group(1)
            indent = len(line) - len(line.lstrip())
            return {
                'code': f'{" " * indent}# SECURITY: Use subprocess instead of os.system\n{" " * indent}subprocess.run({cmd}, shell=False, check=True)',
                'warning': True
            }
        return None

    def _warn_weak_hash(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """警告弱哈希算法"""
        return {
            'code': f'# SECURITY WARNING: Use stronger hash algorithm (sha256, sha512)\n# {line}',
            'warning': True
        }

    def _warn_insecure_random(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """警告不安全的随机数"""
        return {
            'code': f'# SECURITY WARNING: For cryptographic purposes, use secrets module\n# {line}',
            'warning': True
        }

    def _fix_ssl_verify(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """修复SSL验证"""
        return {
            'code': line.replace(
                'ssl._create_unverified_context',
                'ssl.create_default_context()'
            ),
            'warning': True
        }

    def _warn_insecure_temp(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """警告不安全的临时目录"""
        return {
            'code': f'# SECURITY WARNING: Use tempfile module for secure temporary files\n# {line}',
            'warning': True
        }

    def _warn_insecure_permission(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """警告不安全的权限"""
        return {
            'code': f'# SECURITY WARNING: Avoid 777 permissions, use more restrictive permissions\n# {line}',
            'warning': True
        }

    def _fix_sql_injection(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """修复SQL注入"""
        return {
            'code': f'# SECURITY WARNING: SQL string concatenation detected, use parameterized queries\n# Example: cursor.execute("SELECT * FROM table WHERE id = %s", (id,))\n# {line}',
            'warning': True
        }


class PerformanceFixer:
    """性能问题修复器"""

    PERFORMANCE_PATTERNS = {
        r'for\s+\w+\s+in\s+range\(len\((\w+)\)\)': {
            "fix": "optimize_enumerate",
            "description": "使用enumerate替代range(len())"
        },
        r'\+\s*=\s*["\'].*["\']\s*(?:\n\s*\+\s*=\s*["\'].*["\'])*': {
            "fix": "optimize_string_concat",
            "description": "字符串拼接使用join替代+="
        },
        r'\.append\s*\([^)]*\)\s*(?:\n\s*\.append\s*\([^)]*\))*': {
            "fix": "optimize_list_creation",
            "description": "多次append考虑使用列表推导式"
        },
        r'if\s+\w+\s+in\s+\[\s*[^\]]+\s*\]': {
            "fix": "optimize_membership",
            "description": "列表成员检查改用集合提高性能"
        },
        r'while\s+True\s*:': {
            "fix": "check_infinite_loop",
            "description": "检查无限循环，确保有退出条件"
        },
        r'sleep\s*\(\s*\d+\s*\)': {
            "fix": "check_long_sleep",
            "description": "检查长时间sleep，考虑异步实现"
        },
    }

    def __init__(self):
        self.compiled_patterns = {
            re.compile(pattern): fix_info
            for pattern, fix_info in self.PERFORMANCE_PATTERNS.items()
        }

    def scan_and_fix(self, file_path: str) -> List[Dict[str, Any]]:
        """扫描并修复性能问题"""
        fixes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            for pattern, fix_info in self.compiled_patterns.items():
                for match in pattern.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    original_line = lines[line_num - 1] if line_num <= len(lines) else ""

                    fix_method = getattr(self, f"_{fix_info['fix']}", None)
                    if fix_method:
                        result = fix_method(original_line, match)
                        if result:
                            fixes.append({
                                'line': line_num,
                                'original': original_line,
                                'fixed': result['code'],
                                'description': fix_info['description'],
                                'warning': result.get('warning', False)
                            })

        except Exception as e:
            logging.error(f"性能扫描失败: {e}")

        return fixes

    def _optimize_enumerate(self, line: str, match) -> Optional[Dict[str, Any]]:
        """优化enumerate"""
        list_name = match.group(1)
        optimized = re.sub(
            r'for\s+(\w+)\s+in\s+range\(len\((\w+)\)\)',
            f'for i, item in enumerate({list_name})',
            line
        )
        if optimized != line:
            return {
                'code': optimized,
                'warning': False
            }
        return None

    def _optimize_string_concat(self, line: str, match) -> Optional[Dict[str, Any]]:
        """优化字符串拼接"""
        return {
            'code': f'# PERF: Consider using "".join() for string concatenation\n# {line}',
            'warning': True
        }

    def _optimize_list_creation(self, line: str, match) -> Optional[Dict[str, Any]]:
        """优化列表创建"""
        return {
            'code': f'# PERF: Consider using list comprehension\n# {line}',
            'warning': True
        }

    def _optimize_membership(self, line: str, match) -> Optional[Dict[str, Any]]:
        """优化成员检查"""
        optimized = re.sub(
            r'if\s+(\w+)\s+in\s+\[([^\]]+)\]',
            r'if \1 in {\2}',
            line
        )
        if optimized != line:
            return {
                'code': optimized,
                'warning': False
            }
        return None

    def _check_infinite_loop(self, line: str, match) -> Optional[Dict[str, Any]]:
        """检查无限循环"""
        return {
            'code': f'# PERF: Check for infinite loop, ensure proper exit condition\n# {line}',
            'warning': True
        }

    def _check_long_sleep(self, line: str, match) -> Optional[Dict[str, Any]]:
        """检查长时间sleep"""
        return {
            'code': f'# PERF: Consider async implementation for long sleep\n# {line}',
            'warning': True
        }


class CodeQualityFixer:
    """代码质量修复器"""

    QUALITY_PATTERNS = {
        r'except\s*:': {
            "fix": "fix_bare_except",
            "description": "避免裸except，指定具体异常类型"
        },
        r'except\s+Exception\s*:': {
            "fix": "fix_generic_except",
            "description": "避免捕获通用Exception，指定具体异常"
        },
        r'pass\s*$': {
            "fix": "fix_pass_only",
            "description": "仅有pass的代码块，考虑添加文档或实现"
        },
        r'print\s*\(': {
            "fix": "replace_print_logging",
            "description": "使用logging替代print"
        },
        r'#\s*TODO': {
            "fix": "track_todo",
            "description": "TODO注释需要跟踪处理"
        },
        r'#\s*FIXME': {
            "fix": "track_fixme",
            "description": "FIXME注释需要优先处理"
        },
        r'#\s*HACK': {
            "fix": "track_hack",
            "description": "HACK代码需要重构"
        },
        r'__import__\s*\(': {
            "fix": "warn_dynamic_import",
            "description": "动态导入需要谨慎使用"
        },
    }

    def __init__(self):
        self.compiled_patterns = {
            re.compile(pattern): fix_info
            for pattern, fix_info in self.QUALITY_PATTERNS.items()
        }

    def scan_and_fix(self, file_path: str) -> List[Dict[str, Any]]:
        """扫描并修复代码质量问题"""
        fixes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            for pattern, fix_info in self.compiled_patterns.items():
                for match in pattern.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    original_line = lines[line_num - 1] if line_num <= len(lines) else ""

                    fix_method = getattr(self, f"_{fix_info['fix']}", None)
                    if fix_method:
                        result = fix_method(original_line, file_path)
                        if result:
                            fixes.append({
                                'line': line_num,
                                'original': original_line,
                                'fixed': result['code'],
                                'description': fix_info['description'],
                                'warning': result.get('warning', False)
                            })

        except Exception as e:
            logging.error(f"代码质量扫描失败: {e}")

        return fixes

    def _fix_bare_except(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """修复裸except"""
        indent = len(line) - len(line.lstrip())
        return {
            'code': f'{" " * indent}except Exception as e:  # Specify the exception type\n{" " * indent}    logger.error(f"Error: {{e}}")',
            'warning': True
        }

    def _fix_generic_except(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """修复通用Exception捕获"""
        return {
            'code': line.replace('except Exception:', 'except Exception as e:  # Handle specific exceptions'),
            'warning': True
        }

    def _fix_pass_only(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """修复仅有pass的代码块"""
        indent = len(line) - len(line.lstrip())
        return {
            'code': f'{" " * indent}pass  # TODO: Implement this\n{" " * indent}# logger.debug("Not implemented")',
            'warning': True
        }

    def _replace_print_logging(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """替换print为logging"""
        match = re.search(r'print\s*\(\s*(.+)\s*\)', line)
        if match:
            content = match.group(1)
            indent = len(line) - len(line.lstrip())
            return {
                'code': f'{" " * indent}logger.info({content})  # Use logging instead of print',
                'warning': True
            }
        return None

    def _track_todo(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """跟踪TODO"""
        return {
            'code': line,
            'warning': True
        }

    def _track_fixme(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """跟踪FIXME"""
        return {
            'code': line,
            'warning': True
        }

    def _track_hack(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """跟踪HACK"""
        return {
            'code': line,
            'warning': True
        }

    def _warn_dynamic_import(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """警告动态导入"""
        return {
            'code': f'# QUALITY: Dynamic import detected, ensure proper validation\n# {line}',
            'warning': True
        }


class UIUXFixer:
    """UI/UX问题修复器"""

    UIUX_PATTERNS = {
        r'time\.sleep\s*\(\s*\d+\s*\)': {
            "fix": "check_blocking_sleep",
            "description": "阻塞式sleep影响UI响应，考虑异步实现"
        },
        r'input\s*\(': {
            "fix": "check_blocking_input",
            "description": "阻塞式input影响UI响应，考虑异步输入"
        },
        r'while\s+True\s*:': {
            "fix": "check_ui_loop",
            "description": "检查UI线程中的无限循环"
        },
        r'print\s*\([^)]*\)': {
            "fix": "suggest_ui_feedback",
            "description": "考虑使用UI反馈替代控制台输出"
        },
        r'exit\s*\(\s*\)': {
            "fix": "suggest_graceful_exit",
            "description": "直接exit影响用户体验，考虑优雅退出"
        },
        r'sys\.exit\s*\(': {
            "fix": "suggest_graceful_exit",
            "description": "直接sys.exit影响用户体验，考虑优雅退出"
        },
    }

    def __init__(self):
        self.compiled_patterns = {
            re.compile(pattern): fix_info
            for pattern, fix_info in self.UIUX_PATTERNS.items()
        }

    def scan_and_fix(self, file_path: str) -> List[Dict[str, Any]]:
        """扫描并修复UI/UX问题"""
        fixes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            for pattern, fix_info in self.compiled_patterns.items():
                for match in pattern.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    original_line = lines[line_num - 1] if line_num <= len(lines) else ""

                    fix_method = getattr(self, f"_{fix_info['fix']}", None)
                    if fix_method:
                        result = fix_method(original_line, file_path)
                        if result:
                            fixes.append({
                                'line': line_num,
                                'original': original_line,
                                'fixed': result['code'],
                                'description': fix_info['description'],
                                'warning': result.get('warning', False)
                            })

        except Exception as e:
            logging.error(f"UI/UX扫描失败: {e}")

        return fixes

    def _check_blocking_sleep(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """检查阻塞式sleep"""
        return {
            'code': f'# UI/UX: Blocking sleep affects UI responsiveness\n# Consider using asyncio.sleep() or QTimer for async implementation\n# {line}',
            'warning': True
        }

    def _check_blocking_input(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """检查阻塞式input"""
        return {
            'code': f'# UI/UX: Blocking input affects UI responsiveness\n# Consider using async input or UI dialog\n# {line}',
            'warning': True
        }

    def _check_ui_loop(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """检查UI循环"""
        return {
            'code': f'# UI/UX: Check if this infinite loop runs on UI thread\n# Consider moving to background thread\n# {line}',
            'warning': True
        }

    def _suggest_ui_feedback(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """建议UI反馈"""
        return {
            'code': f'# UI/UX: Consider using UI feedback (toast, dialog, status bar) instead of print\n# {line}',
            'warning': True
        }

    def _suggest_graceful_exit(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
        """建议优雅退出"""
        return {
            'code': f'# UI/UX: Consider graceful exit with user confirmation\n# Save state, close connections, show goodbye message\n# {line}',
            'warning': True
        }


class StyleFixer:
    """代码风格修复器"""

    def __init__(self):
        self.tools_available = self._check_tools()

    def _check_tools(self) -> Dict[str, bool]:
        """检查可用的格式化工具"""
        tools = {}
        for tool in ['black', 'isort', 'autopep8', 'yapf']:
            try:
                subprocess.run(
                    [sys.executable, '-m', tool, '--version'],
                    check=True,
                    capture_output=True,
                    timeout=5
                )
                tools[tool] = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                tools[tool] = False
        return tools

    def fix_file(self, file_path: str) -> bool:
        """修复文件风格"""
        if self.tools_available.get('black'):
            return self._run_black(file_path)
        elif self.tools_available.get('autopep8'):
            return self._run_autopep8(file_path)
        elif self.tools_available.get('yapf'):
            return self._run_yapf(file_path)
        else:
            return self._basic_style_fix(file_path)

    def _run_black(self, file_path: str) -> bool:
        """运行black格式化"""
        try:
            subprocess.run(
                [sys.executable, '-m', 'black', file_path],
                check=True,
                capture_output=True,
                timeout=30
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _run_autopep8(self, file_path: str) -> bool:
        """运行autopep8格式化"""
        try:
            subprocess.run(
                [sys.executable, '-m', 'autopep8', '--in-place', '--aggressive', file_path],
                check=True,
                capture_output=True,
                timeout=30
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _run_yapf(self, file_path: str) -> bool:
        """运行yapf格式化"""
        try:
            subprocess.run(
                [sys.executable, '-m', 'yapf', '-i', file_path],
                check=True,
                capture_output=True,
                timeout=30
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _basic_style_fix(self, file_path: str) -> bool:
        """基本的风格修复"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            content = re.sub(r'[ \t]+\n', '\n', content)
            content = re.sub(r'\n{3,}', '\n\n', content)
            content = re.sub(r',([^ \t])', r', \1', content)
            content = re.sub(r'([^ \t])=([^ \t])', r'\1 = \2', content)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception:
            return False


class LogicFixer:
    """逻辑错误修复器"""

    LOGIC_PATTERNS = {
        r'if\s+(\w+)\s*=\s*([^=])': {
            "fix": "fix_assignment_in_condition",
            "description": "条件语句中使用了赋值而非比较"
        },
        r'except\s*:': {
            "fix": "fix_bare_except",
            "description": "裸except应该指定异常类型"
        },
        r'return\s+None\s*$': {
            "fix": "optimize_return_none",
            "description": "可以简化return语句"
        },
        r'if\s+not\s+\w+\s*:\s*\n\s*return\s+False\s*\n\s*return\s+True': {
            "fix": "simplify_boolean_return",
            "description": "可以简化布尔返回逻辑"
        },
    }

    def __init__(self):
        self.compiled_patterns = {
            re.compile(pattern, re.MULTILINE): fix_info
            for pattern, fix_info in self.LOGIC_PATTERNS.items()
        }

    def scan_and_fix(self, file_path: str) -> List[Dict[str, Any]]:
        """扫描并修复逻辑问题"""
        fixes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            for pattern, fix_info in self.compiled_patterns.items():
                for match in pattern.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    original_line = lines[line_num - 1] if line_num <= len(lines) else ""

                    fix_method = getattr(self, f"_{fix_info['fix']}", None)
                    if fix_method:
                        result = fix_method(original_line, match, content)
                        if result:
                            fixes.append({
                                'line': line_num,
                                'original': original_line,
                                'fixed': result['code'],
                                'description': fix_info['description'],
                                'confidence': result.get('confidence', 0.7)
                            })

        except Exception as e:
            logging.error(f"逻辑扫描失败: {e}")

        return fixes

    def _fix_assignment_in_condition(self, line: str, match, content: str) -> Optional[Dict[str, Any]]:
        """修复条件中的赋值"""
        var = match.group(1)
        value = match.group(2)
        fixed = line.replace(f'{var} = {value}', f'{var} == {value}')
        return {'code': fixed, 'confidence': 0.9}

    def _fix_bare_except(self, line: str, match, content: str) -> Optional[Dict[str, Any]]:
        """修复裸except"""
        indent = len(line) - len(line.lstrip())
        fixed = ' ' * indent + 'except Exception as e:'
        return {'code': fixed, 'confidence': 0.8}

    def _optimize_return_none(self, line: str, match, content: str) -> Optional[Dict[str, Any]]:
        """优化return None"""
        indent = len(line) - len(line.lstrip())
        fixed = ' ' * indent + 'return'
        return {'code': fixed, 'confidence': 0.6}

    def _simplify_boolean_return(self, line: str, match, content: str) -> Optional[Dict[str, Any]]:
        """简化布尔返回"""
        return {'code': '# Consider simplifying this boolean return logic', 'confidence': 0.5}


class DocumentationFixer:
    """文档修复器"""

    def scan_and_fix(self, file_path: str) -> List[Dict[str, Any]]:
        """扫描并修复文档问题"""
        fixes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            lines = content.split('\n')

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    docstring = ast.get_docstring(node)
                    if not docstring and node.body:
                        line_num = node.lineno
                        fixes.append({
                            'line': line_num,
                            'original': '',
                            'fixed': self._generate_docstring_stub(node),
                            'description': f"缺少文档字符串: {node.name}",
                            'confidence': 0.5
                        })

        except Exception as e:
            logging.error(f"文档扫描失败: {e}")

        return fixes

    def _generate_docstring_stub(self, node) -> str:
        """生成文档字符串存根"""
        if isinstance(node, ast.ClassDef):
            return f'"""TODO: Add docstring for class {node.name}"""'
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [arg.arg for arg in node.args.args]
            params = '\n'.join([f"    {arg}: TODO" for arg in args])
            return f'"""TODO: Add docstring\n\nArgs:\n{params}\n\nReturns:\n    TODO\n"""'
        return '"""TODO: Add docstring"""'


class FixVerifier:
    """修复验证器"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()

    def verify_fix(
        self,
        file_path: str,
        original_content: str,
        modified_content: str
    ) -> VerificationResult:
        """验证修复是否成功"""
        checks = []
        errors = []
        warnings = []
        score = 0.0

        syntax_check = self._check_syntax(modified_content)
        checks.append(syntax_check)
        if not syntax_check['passed']:
            errors.append(syntax_check['message'])
        else:
            score += 0.4

        style_check = self._check_style(file_path, modified_content)
        checks.append(style_check)
        if not style_check['passed']:
            warnings.append(style_check['message'])
        score += 0.2 if style_check['passed'] else 0.1

        logic_check = self._check_logic(modified_content)
        checks.append(logic_check)
        if not logic_check['passed']:
            warnings.append(logic_check['message'])
        score += 0.2 if logic_check['passed'] else 0.1

        diff_check = self._check_diff_quality(original_content, modified_content)
        checks.append(diff_check)
        score += diff_check['score'] * 0.2

        return VerificationResult(
            passed=len(errors) == 0,
            checks=checks,
            errors=errors,
            warnings=warnings,
            score=min(score, 1.0)
        )

    def _check_syntax(self, content: str) -> Dict[str, Any]:
        """检查语法"""
        try:
            ast.parse(content)
            return {'name': 'syntax', 'passed': True, 'message': '语法检查通过'}
        except SyntaxError as e:
            return {'name': 'syntax', 'passed': False, 'message': f'语法错误: {e}'}

    def _check_style(self, file_path: str, content: str) -> Dict[str, Any]:
        """检查代码风格"""
        issues = []
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(f"行 {i} 超过120字符")
        
        if issues:
            return {'name': 'style', 'passed': False, 'message': '; '.join(issues[:3])}
        return {'name': 'style', 'passed': True, 'message': '风格检查通过'}

    def _check_logic(self, content: str) -> Dict[str, Any]:
        """检查逻辑问题"""
        issues = []
        
        if 'except:' in content:
            issues.append("发现裸except")
        
        if re.search(r'if\s+\w+\s*=\s*[^=]', content):
            issues.append("条件中可能存在赋值错误")
        
        if issues:
            return {'name': 'logic', 'passed': False, 'message': '; '.join(issues)}
        return {'name': 'logic', 'passed': True, 'message': '逻辑检查通过'}

    def _check_diff_quality(self, original: str, modified: str) -> Dict[str, Any]:
        """检查差异质量"""
        original_lines = original.split('\n')
        modified_lines = modified.split('\n')
        
        diff_ratio = difflib.SequenceMatcher(None, original_lines, modified_lines).ratio()
        
        return {
            'name': 'diff_quality',
            'passed': diff_ratio > 0.5,
            'message': f'修改比例: {(1-diff_ratio)*100:.1f}%',
            'score': diff_ratio
        }

    def run_tests(self, file_path: str) -> Dict[str, Any]:
        """运行测试"""
        test_file = self._find_test_file(file_path)
        if not test_file:
            return {'passed': True, 'message': '未找到测试文件，跳过测试'}
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                'passed': result.returncode == 0,
                'message': result.stdout[-500:] if result.returncode != 0 else '测试通过'
            }
        except subprocess.TimeoutExpired:
            return {'passed': False, 'message': '测试超时'}
        except FileNotFoundError:
            return {'passed': True, 'message': 'pytest未安装，跳过测试'}

    def _find_test_file(self, file_path: str) -> Optional[str]:
        """查找对应的测试文件"""
        file_name = Path(file_path).stem
        test_patterns = [
            f"test_{file_name}.py",
            f"{file_name}_test.py",
            f"tests/test_{file_name}.py",
            f"tests/{file_name}_test.py",
        ]
        
        for pattern in test_patterns:
            test_path = self.project_root / pattern
            if test_path.exists():
                return str(test_path)
        
        return None


class FixPreviewer:
    """修复预览器"""

    def generate_preview(
        self,
        file_path: str,
        fixes: List[Dict[str, Any]]
    ) -> FixPreview:
        """生成修复预览"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception:
            original_content = ""

        modified_lines = original_content.split('\n')
        changes = []

        for fix in sorted(fixes, key=lambda x: x['line'], reverse=True):
            line_idx = fix['line'] - 1
            if 0 <= line_idx < len(modified_lines):
                original_line = modified_lines[line_idx]
                modified_lines[line_idx] = fix['fixed']
                changes.append({
                    'line': fix['line'],
                    'original': original_line,
                    'modified': fix['fixed'],
                    'description': fix['description']
                })

        modified_content = '\n'.join(modified_lines)
        diff = self._generate_diff(original_content, modified_content)

        risk_level = self._assess_risk(changes)
        confidence = self._calculate_confidence(fixes)
        can_auto_apply = risk_level in [FixRisk.LOW, FixRisk.MEDIUM] and confidence >= 0.7

        return FixPreview(
            file_path=file_path,
            original_content=original_content,
            modified_content=modified_content,
            diff=diff,
            changes=changes,
            risk_level=risk_level,
            confidence=confidence,
            can_auto_apply=can_auto_apply
        )

    def _generate_diff(self, original: str, modified: str) -> str:
        """生成差异"""
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile='original',
            tofile='modified'
        )
        return ''.join(diff)

    def _assess_risk(self, changes: List[Dict[str, Any]]) -> FixRisk:
        """评估修复风险"""
        if not changes:
            return FixRisk.LOW

        if len(changes) > 10:
            return FixRisk.HIGH
        elif len(changes) > 5:
            return FixRisk.MEDIUM

        high_risk_keywords = ['password', 'secret', 'token', 'auth', 'security']
        for change in changes:
            for keyword in high_risk_keywords:
                if keyword in change['original'].lower() or keyword in change['modified'].lower():
                    return FixRisk.CRITICAL

        return FixRisk.LOW

    def _calculate_confidence(self, fixes: List[Dict[str, Any]]) -> float:
        """计算修复置信度"""
        if not fixes:
            return 0.0

        confidences = [f.get('confidence', 0.5) for f in fixes]
        return sum(confidences) / len(confidences)


class AutoFixer:
    """自动修复器主类"""

    def __init__(self, project_root: str = ".", backup_dir: Optional[str] = None):
        self.project_root = Path(project_root).resolve()
        self.backup_dir = Path(backup_dir) if backup_dir else self.project_root / '.fix_backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.syntax_fixer = SyntaxFixer()
        self.import_fixer = ImportFixer()
        self.security_fixer = EnhancedSecurityFixer()
        self.performance_fixer = PerformanceFixer()
        self.code_quality_fixer = CodeQualityFixer()
        self.uiux_fixer = UIUXFixer()
        self.style_fixer = StyleFixer()
        self.logic_fixer = LogicFixer()
        self.documentation_fixer = DocumentationFixer()
        self.verifier = FixVerifier(project_root)
        self.previewer = FixPreviewer()

        self.logger = self._setup_logger()
        self.fix_history: List[FixAttempt] = []
        self.attempt_counter = 0

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('AutoFixer')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _generate_attempt_id(self) -> str:
        """生成尝试ID"""
        self.attempt_counter += 1
        return f"FIX-{datetime.now().strftime('%Y%m%d')}-{self.attempt_counter:04d}"

    def _create_backup(self, file_path: str) -> str:
        """创建文件备份"""
        original_path = Path(file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{original_path.stem}_{timestamp}{original_path.suffix}"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(file_path, backup_path)
        return str(backup_path)

    def _restore_backup(self, backup_path: str, original_path: str) -> bool:
        """恢复备份"""
        try:
            shutil.copy2(backup_path, original_path)
            return True
        except Exception as e:
            self.logger.error(f"恢复备份失败: {e}")
            return False

    def _verify_fix(self, file_path: str) -> bool:
        """验证修复是否成功"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            try:
                ast.parse(content)
                return True
            except SyntaxError:
                return False

        except Exception:
            return False

    def fix_syntax_error(
        self,
        file_path: str,
        error_message: str,
        line_number: int
    ) -> FixAttempt:
        """修复语法错误"""
        attempt_id = self._generate_attempt_id()
        backup_path = self._create_backup(file_path)

        attempt = FixAttempt(
            attempt_id=attempt_id,
            strategy=FixStrategy.SYNTAX_FIX,
            file_path=file_path,
            line_number=line_number,
            original_code="",
            modified_code="",
            description="修复语法错误",
            status=FixStatus.IN_PROGRESS,
            timestamp=datetime.now(),
            backup_path=backup_path
        )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
                attempt.original_code = original_content.split('\n')[line_number - 1] if line_number > 0 else ""

            if not self.syntax_fixer.can_fix(error_message):
                attempt.status = FixStatus.FAILED
                attempt.error_message = "无法自动修复此语法错误"
                return attempt

            fixed_content = self.syntax_fixer.fix(file_path, error_message, line_number)

            if fixed_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)

                attempt.modified_code = fixed_content.split('\n')[line_number - 1] if line_number > 0 else ""

                if self._verify_fix(file_path):
                    attempt.status = FixStatus.SUCCESS
                    attempt.verification_result = True
                else:
                    attempt.status = FixStatus.FAILED
                    attempt.error_message = "修复后语法验证失败"
                    self._restore_backup(backup_path, file_path)
            else:
                attempt.status = FixStatus.FAILED
                attempt.error_message = "无法生成修复代码"

        except Exception as e:
            attempt.status = FixStatus.FAILED
            attempt.error_message = str(e)
            self._restore_backup(backup_path, file_path)

        self.fix_history.append(attempt)
        return attempt

    def fix_import_error(
        self,
        file_path: str,
        error_message: str,
        line_number: int
    ) -> FixAttempt:
        """修复导入错误"""
        attempt_id = self._generate_attempt_id()

        attempt = FixAttempt(
            attempt_id=attempt_id,
            strategy=FixStrategy.IMPORT_FIX,
            file_path=file_path,
            line_number=line_number,
            original_code="",
            modified_code="",
            description="安装缺失的依赖",
            status=FixStatus.IN_PROGRESS,
            timestamp=datetime.now()
        )

        try:
            result = self.import_fixer.fix(file_path, error_message, line_number)

            if result == "installed":
                attempt.status = FixStatus.SUCCESS
                attempt.modified_code = "依赖已安装"
            else:
                attempt.status = FixStatus.FAILED
                attempt.error_message = "无法自动安装依赖"

        except Exception as e:
            attempt.status = FixStatus.FAILED
            attempt.error_message = str(e)

        self.fix_history.append(attempt)
        return attempt

    def fix_security_issues(self, file_path: str) -> List[FixAttempt]:
        """修复安全问题"""
        attempts = []
        fixes = self.security_fixer.scan_and_fix(file_path)

        for fix in fixes:
            attempt_id = self._generate_attempt_id()
            backup_path = self._create_backup(file_path)

            attempt = FixAttempt(
                attempt_id=attempt_id,
                strategy=FixStrategy.SECURITY_FIX,
                file_path=file_path,
                line_number=fix['line'],
                original_code=fix['original'],
                modified_code=fix['fixed'],
                description=fix['description'],
                status=FixStatus.IN_PROGRESS,
                timestamp=datetime.now(),
                backup_path=backup_path
            )

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                lines[fix['line'] - 1] = fix['fixed'] + '\n'

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

                if fix.get('warning'):
                    attempt.status = FixStatus.SUCCESS
                    attempt.verification_result = True
                elif self._verify_fix(file_path):
                    attempt.status = FixStatus.SUCCESS
                    attempt.verification_result = True
                else:
                    attempt.status = FixStatus.FAILED
                    attempt.error_message = "修复验证失败"
                    self._restore_backup(backup_path, file_path)

            except Exception as e:
                attempt.status = FixStatus.FAILED
                attempt.error_message = str(e)
                self._restore_backup(backup_path, file_path)

            attempts.append(attempt)
            self.fix_history.append(attempt)

        return attempts

    def fix_style(self, file_path: str) -> FixAttempt:
        """修复代码风格"""
        attempt_id = self._generate_attempt_id()
        backup_path = self._create_backup(file_path)

        attempt = FixAttempt(
            attempt_id=attempt_id,
            strategy=FixStrategy.STYLE_FIX,
            file_path=file_path,
            line_number=0,
            original_code="",
            modified_code="",
            description="格式化代码风格",
            status=FixStatus.IN_PROGRESS,
            timestamp=datetime.now(),
            backup_path=backup_path
        )

        try:
            if self.style_fixer.fix_file(file_path):
                attempt.status = FixStatus.SUCCESS
                attempt.verification_result = True
            else:
                attempt.status = FixStatus.FAILED
                attempt.error_message = "格式化失败"

        except Exception as e:
            attempt.status = FixStatus.FAILED
            attempt.error_message = str(e)

        self.fix_history.append(attempt)
        return attempt

    def fix_performance_issues(self, file_path: str) -> List[FixAttempt]:
        """修复性能问题"""
        attempts = []
        fixes = self.performance_fixer.scan_and_fix(file_path)

        for fix in fixes:
            attempt_id = self._generate_attempt_id()
            backup_path = self._create_backup(file_path)

            attempt = FixAttempt(
                attempt_id=attempt_id,
                strategy=FixStrategy.PERFORMANCE_FIX,
                file_path=file_path,
                line_number=fix['line'],
                original_code=fix['original'],
                modified_code=fix['fixed'],
                description=fix['description'],
                status=FixStatus.IN_PROGRESS,
                timestamp=datetime.now(),
                backup_path=backup_path
            )

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                lines[fix['line'] - 1] = fix['fixed'] + '\n'

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

                if fix.get('warning'):
                    attempt.status = FixStatus.SUCCESS
                    attempt.verification_result = True
                elif self._verify_fix(file_path):
                    attempt.status = FixStatus.SUCCESS
                    attempt.verification_result = True
                else:
                    attempt.status = FixStatus.FAILED
                    attempt.error_message = "修复验证失败"
                    self._restore_backup(backup_path, file_path)

            except Exception as e:
                attempt.status = FixStatus.FAILED
                attempt.error_message = str(e)
                self._restore_backup(backup_path, file_path)

            attempts.append(attempt)
            self.fix_history.append(attempt)

        return attempts

    def fix_code_quality_issues(self, file_path: str) -> List[FixAttempt]:
        """修复代码质量问题"""
        attempts = []
        fixes = self.code_quality_fixer.scan_and_fix(file_path)

        for fix in fixes:
            attempt_id = self._generate_attempt_id()
            backup_path = self._create_backup(file_path)

            attempt = FixAttempt(
                attempt_id=attempt_id,
                strategy=FixStrategy.REFACTOR_FIX,
                file_path=file_path,
                line_number=fix['line'],
                original_code=fix['original'],
                modified_code=fix['fixed'],
                description=fix['description'],
                status=FixStatus.IN_PROGRESS,
                timestamp=datetime.now(),
                backup_path=backup_path
            )

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                lines[fix['line'] - 1] = fix['fixed'] + '\n'

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

                if fix.get('warning'):
                    attempt.status = FixStatus.SUCCESS
                    attempt.verification_result = True
                elif self._verify_fix(file_path):
                    attempt.status = FixStatus.SUCCESS
                    attempt.verification_result = True
                else:
                    attempt.status = FixStatus.FAILED
                    attempt.error_message = "修复验证失败"
                    self._restore_backup(backup_path, file_path)

            except Exception as e:
                attempt.status = FixStatus.FAILED
                attempt.error_message = str(e)
                self._restore_backup(backup_path, file_path)

            attempts.append(attempt)
            self.fix_history.append(attempt)

        return attempts

    def fix_uiux_issues(self, file_path: str) -> List[FixAttempt]:
        """修复UI/UX问题"""
        attempts = []
        fixes = self.uiux_fixer.scan_and_fix(file_path)

        for fix in fixes:
            attempt_id = self._generate_attempt_id()
            backup_path = self._create_backup(file_path)

            attempt = FixAttempt(
                attempt_id=attempt_id,
                strategy=FixStrategy.STYLE_FIX,
                file_path=file_path,
                line_number=fix['line'],
                original_code=fix['original'],
                modified_code=fix['fixed'],
                description=fix['description'],
                status=FixStatus.IN_PROGRESS,
                timestamp=datetime.now(),
                backup_path=backup_path
            )

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                lines[fix['line'] - 1] = fix['fixed'] + '\n'

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

                if fix.get('warning'):
                    attempt.status = FixStatus.SUCCESS
                    attempt.verification_result = True
                elif self._verify_fix(file_path):
                    attempt.status = FixStatus.SUCCESS
                    attempt.verification_result = True
                else:
                    attempt.status = FixStatus.FAILED
                    attempt.error_message = "修复验证失败"
                    self._restore_backup(backup_path, file_path)

            except Exception as e:
                attempt.status = FixStatus.FAILED
                attempt.error_message = str(e)
                self._restore_backup(backup_path, file_path)

            attempts.append(attempt)
            self.fix_history.append(attempt)

        return attempts

    def auto_fix_file(
        self,
        file_path: str,
        error_message: Optional[str] = None,
        line_number: Optional[int] = None,
        preview_only: bool = False
    ) -> Union[List[FixAttempt], FixPreview]:
        """自动修复文件"""
        attempts = []
        all_fixes = []

        if error_message and line_number:
            if self.syntax_fixer.can_fix(error_message):
                attempts.append(self.fix_syntax_error(file_path, error_message, line_number))
            elif self.import_fixer.can_fix(error_message):
                attempts.append(self.fix_import_error(file_path, error_message, line_number))

        security_fixes = self.security_fixer.scan_and_fix(file_path)
        all_fixes.extend(security_fixes)

        performance_fixes = self.performance_fixer.scan_and_fix(file_path)
        all_fixes.extend(performance_fixes)

        quality_fixes = self.code_quality_fixer.scan_and_fix(file_path)
        all_fixes.extend(quality_fixes)

        uiux_fixes = self.uiux_fixer.scan_and_fix(file_path)
        all_fixes.extend(uiux_fixes)

        logic_fixes = self.logic_fixer.scan_and_fix(file_path)
        all_fixes.extend(logic_fixes)

        if preview_only and all_fixes:
            preview = self.previewer.generate_preview(file_path, all_fixes)
            return preview

        for fix in all_fixes:
            attempt = self._apply_fix(file_path, fix)
            attempts.append(attempt)

        style_attempt = self.fix_style(file_path)
        attempts.append(style_attempt)

        return attempts

    def _apply_fix(self, file_path: str, fix: Dict[str, Any]) -> FixAttempt:
        """应用单个修复"""
        attempt_id = self._generate_attempt_id()
        backup_path = self._create_backup(file_path)

        attempt = FixAttempt(
            attempt_id=attempt_id,
            strategy=FixStrategy.REFACTOR_FIX,
            file_path=file_path,
            line_number=fix['line'],
            original_code=fix['original'],
            modified_code=fix['fixed'],
            description=fix['description'],
            status=FixStatus.IN_PROGRESS,
            timestamp=datetime.now(),
            backup_path=backup_path,
            confidence=fix.get('confidence', 0.7),
            risk=FixRisk.LOW
        )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            lines[fix['line'] - 1] = fix['fixed'] + '\n'

            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            verification = self.verifier.verify(file_path, fix['original'], fix['fixed'])
            attempt.verification_result = verification.passed
            attempt.diff = self._generate_single_line_diff(fix['original'], fix['fixed'])

            if verification.passed:
                attempt.status = FixStatus.SUCCESS
            else:
                attempt.status = FixStatus.NEEDS_REVIEW
                attempt.error_message = '; '.join(verification.warnings)

        except Exception as e:
            attempt.status = FixStatus.FAILED
            attempt.error_message = str(e)
            self._restore_backup(backup_path, file_path)

        self.fix_history.append(attempt)
        return attempt

    def _generate_single_line_diff(self, original: str, modified: str) -> str:
        """生成单行差异"""
        return f"- {original}\n+ {modified}"

    def preview_fixes(self, file_path: str) -> FixPreview:
        """预览修复"""
        return self.auto_fix_file(file_path, preview_only=True)

    def verify_fix(self, file_path: str) -> VerificationResult:
        """验证修复"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.verifier.verify(file_path, "", content)
        except Exception as e:
            return VerificationResult(
                passed=False,
                checks=[],
                errors=[str(e)],
                warnings=[],
                score=0.0
            )

    def auto_fix_project(self, file_pattern: str = "*.py", preview_only: bool = False) -> AutoFixResult:
        """自动修复整个项目"""
        all_attempts = []
        affected_files = set()
        previews = []

        for py_file in self.project_root.rglob(file_pattern):
            try:
                result = self.auto_fix_file(str(py_file), preview_only=preview_only)
                
                if preview_only and isinstance(result, FixPreview):
                    previews.append(result)
                elif isinstance(result, list):
                    all_attempts.extend(result)

                    if any(a.status == FixStatus.SUCCESS for a in result):
                        affected_files.add(str(py_file))

            except Exception as e:
                self.logger.error(f"修复文件失败 {py_file}: {e}")

        successful = sum(1 for a in all_attempts if a.status == FixStatus.SUCCESS)
        failed = sum(1 for a in all_attempts if a.status == FixStatus.FAILED)

        return AutoFixResult(
            success=failed == 0,
            file_path=str(self.project_root),
            fix_count=successful,
            failed_count=failed,
            issues_remaining=failed,
            affected_files=list(affected_files),
            previews=previews
        )

    def rollback(self, attempt_id: str) -> bool:
        """回滚特定修复"""
        for attempt in self.fix_history:
            if attempt.attempt_id == attempt_id and attempt.backup_path:
                if self._restore_backup(attempt.backup_path, attempt.file_path):
                    attempt.status = FixStatus.ROLLED_BACK
                    return True
        return False

    def rollback_all(self) -> int:
        """回滚所有修复"""
        count = 0
        for attempt in self.fix_history:
            if attempt.status == FixStatus.SUCCESS and attempt.backup_path:
                if self._restore_backup(attempt.backup_path, attempt.file_path):
                    attempt.status = FixStatus.ROLLED_BACK
                    count += 1
        return count

    def generate_report(
        self,
        output_path: Optional[str] = None,
        output_format: str = "markdown"
    ) -> str:
        """生成修复报告"""
        if output_format == "json":
            return self._generate_json_report(output_path)
        return self._generate_markdown_report(output_path)

    def _generate_markdown_report(self, output_path: Optional[str] = None) -> str:
        """生成Markdown格式报告"""
        successful = [a for a in self.fix_history if a.status == FixStatus.SUCCESS]
        failed = [a for a in self.fix_history if a.status == FixStatus.FAILED]
        rolled_back = [a for a in self.fix_history if a.status == FixStatus.ROLLED_BACK]
        needs_review = [a for a in self.fix_history if a.status == FixStatus.NEEDS_REVIEW]

        lines = [
            "# 自动修复报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n## 修复统计",
            f"- 总尝试次数: {len(self.fix_history)}",
            f"- 成功修复: {len(successful)}",
            f"- 修复失败: {len(failed)}",
            f"- 已回滚: {len(rolled_back)}",
            f"- 需要人工审查: {len(needs_review)}",
            f"- 成功率: {len(successful)/len(self.fix_history)*100:.1f}%" if self.fix_history else "- 成功率: N/A",
        ]
        
        avg_confidence = sum(a.confidence for a in self.fix_history) / len(self.fix_history) if self.fix_history else 0
        lines.append(f"- 平均置信度: {avg_confidence:.1%}")

        if successful:
            lines.extend([
                f"\n## ✅ 成功修复 ({len(successful)})",
                "| ID | 策略 | 文件 | 行号 | 描述 | 置信度 |",
                "|----|------|------|------|------|--------|",
            ])
            for a in successful:
                lines.append(
                    f"| {a.attempt_id} | {a.strategy.value} | {Path(a.file_path).name} | "
                    f"{a.line_number} | {a.description} | {a.confidence:.0%} |"
                )

        if needs_review:
            lines.extend([
                f"\n## ⚠️ 需要审查 ({len(needs_review)})",
                "| ID | 策略 | 文件 | 错误信息 |",
                "|----|------|------|----------|",
            ])
            for a in needs_review:
                error = a.error_message[:50] + "..." if a.error_message and len(a.error_message) > 50 else (a.error_message or "")
                lines.append(
                    f"| {a.attempt_id} | {a.strategy.value} | {Path(a.file_path).name} | {error} |"
                )

        if failed:
            lines.extend([
                f"\n## ❌ 修复失败 ({len(failed)})",
                "| ID | 策略 | 文件 | 错误信息 |",
                "|----|------|------|----------|",
            ])
            for a in failed:
                error = a.error_message[:50] + "..." if a.error_message and len(a.error_message) > 50 else (a.error_message or "")
                lines.append(
                    f"| {a.attempt_id} | {a.strategy.value} | {Path(a.file_path).name} | {error} |"
                )

        if rolled_back:
            lines.extend([
                f"\n## 🔄 已回滚 ({len(rolled_back)})",
            ])
            for a in rolled_back:
                lines.append(f"- {a.attempt_id}: {a.file_path}")

        lines.extend([
            "\n## 修复详情",
        ])

        for attempt in self.fix_history[:20]:
            lines.extend([
                f"\n### {attempt.attempt_id}",
                f"- **策略**: {attempt.strategy.value}",
                f"- **文件**: {attempt.file_path}",
                f"- **行号**: {attempt.line_number}",
                f"- **状态**: {attempt.status.value}",
                f"- **时间**: {attempt.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                f"- **置信度**: {attempt.confidence:.0%}",
                f"- **风险等级**: {attempt.risk.value}",
            ])

            if attempt.original_code:
                lines.extend([
                    "- **原始代码**:",
                    "```python",
                    attempt.original_code,
                    "```"
                ])

            if attempt.modified_code:
                lines.extend([
                    "- **修复后**:",
                    "```python",
                    attempt.modified_code,
                    "```"
                ])
            
            if attempt.diff:
                lines.extend([
                    "- **差异**:",
                    "```diff",
                    attempt.diff,
                    "```"
                ])

            if attempt.error_message:
                lines.extend([
                    "- **错误信息**:",
                    f"```\n{attempt.error_message}\n```"
                ])

        report = '\n'.join(lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report

    def _generate_json_report(self, output_path: Optional[str] = None) -> str:
        """生成JSON格式报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_attempts": len(self.fix_history),
                "successful": len([a for a in self.fix_history if a.status == FixStatus.SUCCESS]),
                "failed": len([a for a in self.fix_history if a.status == FixStatus.FAILED]),
                "rolled_back": len([a for a in self.fix_history if a.status == FixStatus.ROLLED_BACK])
            },
            "attempts": [
                {
                    "id": a.attempt_id,
                    "strategy": a.strategy.value,
                    "file": a.file_path,
                    "line": a.line_number,
                    "status": a.status.value,
                    "description": a.description,
                    "timestamp": a.timestamp.isoformat(),
                    "original_code": a.original_code,
                    "modified_code": a.modified_code,
                    "error_message": a.error_message,
                    "verification_result": a.verification_result,
                    "backup_path": a.backup_path
                }
                for a in self.fix_history
            ]
        }

        json_str = json.dumps(report, indent=2, ensure_ascii=False)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str

    def save_history(self, history_path: Optional[str] = None) -> str:
        """保存修复历史"""
        if not history_path:
            history_path = self.backup_dir / f"fix_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        history = FixHistory(
            history_id=f"HIST-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            total_attempts=len(self.fix_history),
            successful_fixes=len([a for a in self.fix_history if a.status == FixStatus.SUCCESS]),
            failed_fixes=len([a for a in self.fix_history if a.status == FixStatus.FAILED]),
            rolled_back_fixes=len([a for a in self.fix_history if a.status == FixStatus.ROLLED_BACK]),
            attempts=self.fix_history,
            affected_files=set(a.file_path for a in self.fix_history)
        )

        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(history), f, indent=2, ensure_ascii=False, default=str)

        return str(history_path)


def main():
    parser = argparse.ArgumentParser(
        description='自动修复脚本 - 自动修复常见问题'
    )
    parser.add_argument(
        'target',
        help='要修复的文件或目录'
    )
    parser.add_argument(
        '--error',
        help='错误信息（用于针对性修复）'
    )
    parser.add_argument(
        '--line',
        type=int,
        help='错误所在行号'
    )
    parser.add_argument(
        '--project-root',
        default='.',
        help='项目根目录'
    )
    parser.add_argument(
        '--backup-dir',
        help='备份目录'
    )
    parser.add_argument(
        '-o', '--output',
        help='报告输出路径'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['markdown', 'json'],
        default='markdown',
        help='输出格式'
    )
    parser.add_argument(
        '--rollback',
        help='回滚指定ID的修复'
    )
    parser.add_argument(
        '--rollback-all',
        action='store_true',
        help='回滚所有修复'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅预览，不实际修复'
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help='生成修复预览'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='修复后运行验证'
    )
    parser.add_argument(
        '--confidence-threshold',
        type=float,
        default=0.7,
        help='自动应用修复的置信度阈值（默认0.7）'
    )

    args = parser.parse_args()

    fixer = AutoFixer(args.project_root, args.backup_dir)

    if args.rollback:
        if fixer.rollback(args.rollback):
            print(f"成功回滚修复: {args.rollback}")
            return 0
        else:
            print(f"回滚失败: {args.rollback}")
            return 1

    if args.rollback_all:
        count = fixer.rollback_all()
        print(f"成功回滚 {count} 个修复")
        return 0

    print(f"正在修复: {args.target}")

    if args.dry_run or args.preview:
        print("[预览模式] 不会实际修改文件")

    if os.path.isfile(args.target):
        if args.preview:
            preview = fixer.preview_fixes(args.target)
            print(f"\n修复预览:")
            print(f"- 文件: {preview.file_path}")
            print(f"- 变更数量: {len(preview.changes)}")
            print(f"- 风险等级: {preview.risk_level.value}")
            print(f"- 置信度: {preview.confidence:.0%}")
            print(f"- 可自动应用: {'是' if preview.can_auto_apply else '否'}")
            print(f"\n差异:\n{preview.diff}")
        elif args.dry_run:
            print(f"将扫描文件: {args.target}")
            security_fixes = fixer.security_fixer.scan_and_fix(args.target)
            if security_fixes:
                print(f"发现 {len(security_fixes)} 个安全问题可修复")
                for fix in security_fixes:
                    print(f"  行 {fix['line']}: {fix['description']}")
        else:
            attempts = fixer.auto_fix_file(args.target, args.error, args.line)
            
            if args.verify:
                verification = fixer.verify_fix(args.target)
                print(f"\n验证结果: {'通过' if verification.passed else '失败'}")
                print(f"验证分数: {verification.score:.0%}")
                if verification.warnings:
                    print("警告:")
                    for w in verification.warnings:
                        print(f"  - {w}")
    else:
        if args.preview:
            result = fixer.auto_fix_project(preview_only=True)
            print(f"\n项目修复预览:")
            print(f"- 扫描文件数: {len(result.previews)}")
            high_risk = [p for p in result.previews if p.risk_level in [FixRisk.HIGH, FixRisk.CRITICAL]]
            print(f"- 高风险文件: {len(high_risk)}")
            for preview in result.previews[:5]:
                print(f"\n  文件: {preview.file_path}")
                print(f"    变更: {len(preview.changes)}, 风险: {preview.risk_level.value}, 置信度: {preview.confidence:.0%}")
        elif args.dry_run:
            print(f"将扫描目录: {args.target}")
        else:
            result = fixer.auto_fix_project()
            print(f"\n修复完成!")
            print(f"成功: {result.fix_count}")
            print(f"失败: {result.failed_count}")
            
            if args.verify:
                print(f"验证分数: {result.verification_score:.0%}")

    if not (args.dry_run or args.preview):
        report = fixer.generate_report(args.output, args.format)

        if args.output:
            print(f"\n报告已保存到: {args.output}")
        else:
            print("\n" + "="*60)
            print(report)

        history_path = fixer.save_history()
        print(f"修复历史已保存到: {history_path}")

    return 0


if __name__ == '__main__':
    exit(main())
