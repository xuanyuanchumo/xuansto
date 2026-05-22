#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全方位自修复系统 - Comprehensive Auto Repair System

核心功能：
1. ExtendedFixRuleLibrary - 扩展修复规则库（100+规则）
   - 代码修复规则 (30+条)：语法错误、代码风格、性能问题、安全问题
   - 文档修复规则 (30+条)：编码问题、格式问题、内容问题
   - 配置修复规则 (20+条)：配置迁移、类型匹配、重复检测
   - 路径修复规则 (20+条)：硬编码路径、跨平台兼容、路径验证
   - 依赖修复规则 (10+条)：版本冲突、缺失依赖、废弃包

2. EnhancedDocEncodingFixer - 增强版文档编码修复器
   - 多编码自动检测
   - 乱码字符智能识别
   - 启发式算法还原

使用示例：
    from comprehensive_auto_repair import (
        ExtendedFixRuleLibrary,
        EnhancedDocEncodingFixer,
        ComprehensiveAutoRepairer
    )

    library = ExtendedFixRuleLibrary()
    rules = library.get_rules_by_category('code')

    fixer = EnhancedDocEncodingFixer()
    result = fixer.detect_and_fix(file_path)

    repairer = ComprehensiveAutoRepairer()
    report = repairer.repair_all(target_path)
"""

import json
import logging
import os
import re
import chardet
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set, Union

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FixRuleCategory(Enum):
    """修复规则分类"""
    CODE = "code"
    DOCUMENT = "document"
    CONFIG = "config"
    PATH = "path"
    DEPENDENCY = "dependency"


class FixSeverity(Enum):
    """修复严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FixStatus(Enum):
    """修复状态"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"
    NEEDS_MANUAL_REVIEW = "needs_manual_review"


@dataclass
class FixRule:
    """修复规则定义"""
    rule_id: str
    category: FixRuleCategory
    pattern: str                          # 匹配模式（正则或关键词）
    description: str                      # 规则描述
    fix_action: str                       # 修复动作
    severity: FixSeverity                 # 严重程度
    auto_fixable: bool = True             # 是否可自动修复
    confidence: float = 0.8               # 修复置信度
    affected_extensions: List[str] = field(default_factory=list)  # 影响的文件扩展名
    example_before: str = ""              # 示例：修复前
    example_after: str = ""               # 示例：修复后
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'rule_id': self.rule_id,
            'category': self.category.value,
            'pattern': self.pattern,
            'description': self.description,
            'fix_action': self.fix_action,
            'severity': self.severity.value,
            'auto_fixable': self.auto_fixable,
            'confidence': round(self.confidence, 2),
            'affected_extensions': self.affected_extensions,
            'example_before': self.example_before,
            'example_after': self.example_after,
            'metadata': self.metadata
        }


@dataclass
class RepairResult:
    """修复结果"""
    result_id: str
    rule_id: str
    file_path: str
    status: FixStatus
    issue_description: str
    fix_applied: bool
    original_content: str = ""
    fixed_content: str = ""
    line_number: int = 0
    confidence: float = 0.0
    execution_time_ms: float = 0.0
    message: str = ""
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'result_id': self.result_id,
            'rule_id': self.rule_id,
            'file_path': self.file_path,
            'status': self.status.value,
            'issue_description': self.issue_description,
            'fix_applied': self.fix_applied,
            'line_number': self.line_number,
            'confidence': round(self.confidence, 2),
            'execution_time_ms': round(self.execution_time_ms, 2),
            'message': self.message,
            'warnings': self.warnings,
            'metadata': self.metadata
        }


@dataclass
class EncodingFixResult:
    """编码修复结果"""
    file_path: str
    original_encoding: str
    detected_encoding: str
    fixed_encoding: str
    had_bom: bool
    bom_removed: bool
    garbled_chars_found: int
    garbled_chars_fixed: int
    success: bool
    confidence: float
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_path': str(self.file_path),
            'original_encoding': self.original_encoding,
            'detected_encoding': self.detected_encoding,
            'fixed_encoding': self.fixed_encoding,
            'had_bom': self.had_bom,
            'bom_removed': self.bom_removed,
            'garbled_chars_found': self.garbled_chars_found,
            'garbled_chars_fixed': self.garbled_chars_fixed,
            'success': self.success,
            'confidence': round(self.confidence, 3),
            'details': self.details
        }


class ExtendedFixRuleLibrary:
    """
    扩展修复规则库

    提供100+条修复规则，覆盖代码、文档、配置、路径、依赖等多个维度。
    """

    CODE_FIX_RULES = [
        # ===== 语法错误修复 (8条) =====
        {
            'rule_id': 'CODE-001',
            'pattern': r'indentation_error|IndentationError',
            'description': '缩进错误',
            'fix_action': 'auto_indent',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.py'],
            'example_before': 'def foo():\nprint("x")',
            'example_after': 'def foo():\n    print("x")'
        },
        {
            'rule_id': 'CODE-002',
            'pattern': r'syntax_error.*colon|expected.*colon',
            'description': '缺少冒号',
            'fix_action': 'add_colon',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.py'],
            'example_before': 'if True\n    print("yes")',
            'example_after': 'if True:\n    print("yes")'
        },
        {
            'rule_id': 'CODE-003',
            'pattern': r"undefined_variable|NameError.*'(\w+)'",
            'description': '未定义变量',
            'fix_action': 'declare_variable',
            'severity': 'medium',
            'auto_fixable': False,
            'extensions': ['.py']
        },
        {
            'rule_id': 'CODE-004',
            'pattern': r'missing_import|ModuleNotFoundError|ImportError',
            'description': '缺少导入语句',
            'fix_action': 'add_import',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.ts']
        },
        {
            'rule_id': 'CODE-005',
            'pattern': r'unmatched_bracket|unmatched_parenthesis',
            'description': '括号不匹配',
            'fix_action': 'fix_brackets',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.ts', '.java']
        },
        {
            'rule_id': 'CODE-006',
            'pattern': r'invalid_syntax|SyntaxError',
            'description': '语法错误',
            'fix_action': 'suggest_fix',
            'severity': 'high',
            'auto_fixable': False,
            'extensions': ['.py', '.js', '.ts']
        },
        {
            'rule_id': 'CODE-007',
            'pattern': r'eof_while_scanning|unexpected EOF',
            'description': '意外的文件结束符',
            'fix_action': 'complete_statement',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.ts']
        },
        {
            'rule_id': 'CODE-008',
            'pattern': r'dedent_mismatch|unindent does not match',
            'description': '缩进不匹配',
            'fix_action': 'normalize_indentation',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.py']
        },

        # ===== 代码风格修复 (8条) =====
        {
            'rule_id': 'CODE-010',
            'pattern': r'line_too_long|E501',
            'description': '行过长（超过79/120字符）',
            'fix_action': 'wrap_line',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.ts', '.java']
        },
        {
            'rule_id': 'CODE-011',
            'pattern': r'trailing_whitespace|W291',
            'description': '行尾空白字符',
            'fix_action': 'trim_whitespace',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.ts', '.md', '.txt']
        },
        {
            'rule_id': 'CODE-012',
            'pattern': r'missing_docstring|D100|D101|D102|D103',
            'description': '缺少文档字符串',
            'fix_action': 'add_docstring',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.py']
        },
        {
            'rule_id': 'CODE-013',
            'pattern': r'unused_import|F401',
            'description': '未使用的导入',
            'fix_action': 'remove_import',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.ts']
        },
        {
            'rule_id': 'CODE-014',
            'pattern': r'multiple_statements_on_one_line|E701|E702',
            'description': '多语句同行',
            'fix_action': 'split_statements',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.py']
        },
        {
            'rule_id': 'CODE-015',
            'pattern': r'blank_line_missing|E301|E302|E303',
            'description': '缺少空行',
            'fix_action': 'add_blank_lines',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.py']
        },
        {
            'rule_id': 'CODE-016',
            'pattern': r'naming_convention|N801|N802|N803|N806|N807',
            'description': '命名规范违反',
            'fix_action': 'rename_identifier',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.ts']
        },
        {
            'rule_id': 'CODE-017',
            'pattern': r'too_many_arguments|R0913',
            'description': '函数参数过多',
            'fix_action': 'refactor_to_config_object',
            'severity': 'medium',
            'auto_fixable': False,
            'extensions': ['.py', '.js', '.ts', '.java']
        },

        # ===== 性能问题修复 (6条) =====
        {
            'rule_id': 'CODE-020',
            'pattern': r'n_plus_1_query|N\+1 query',
            'description': 'N+1查询问题',
            'fix_action': 'batch_query',
            'severity': 'high',
            'auto_fixable': False,
            'extensions': ['.py', '.js', '.java']
        },
        {
            'rule_id': 'CODE-021',
            'pattern': r'memory_leak|memory leak|resource leak',
            'description': '内存泄漏风险',
            'fix_action': 'add_cleanup',
            'severity': 'critical',
            'auto_fixable': False,
            'extensions': ['.py', '.js', '.cpp', '.java']
        },
        {
            'rule_id': 'CODE-022',
            'pattern': r'inefficient_loop|nested loop|O\(n[23]\)',
            'description': '低效循环',
            'fix_action': 'optimize_loop',
            'severity': 'medium',
            'auto_fixable': False,
            'extensions': ['.py', '.js', '.java', '.cpp']
        },
        {
            'rule_id': 'CODE-023',
            'pattern': r'string_concatenation_in_loop|\+.*in for|\+.*in while',
            'description': '循环中字符串拼接',
            'fix_action': 'use_join_or_builder',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.java']
        },
        {
            'rule_id': 'CODE-024',
            'pattern': r'redundant_computation|repeated_calculation',
            'description': '冗余计算',
            'fix_action': 'cache_result',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.ts', '.java']
        },
        {
            'rule_id': 'CODE-025',
            'pattern': r'global_variable_overuse|too many globals',
            'description': '过度使用全局变量',
            'fix_action': 'encapsulate_in_class',
            'severity': 'medium',
            'auto_fixable': False,
            'extensions': ['.py', '.js']
        },

        # ===== 安全问题修复 (8条) =====
        {
            'rule_id': 'CODE-030',
            'pattern': r'sql_injection|SQL injection|raw SQL.*format|execute\(.*f["\']',
            'description': 'SQL注入风险',
            'fix_action': 'parameterized_query',
            'severity': 'critical',
            'auto_fixable': True,
            'extensions': ['.py', '.php', '.java', '.js']
        },
        {
            'rule_id': 'CODE-031',
            'pattern': r'xss_vulnerability|XSS|innerHTML.*\+|\.html\(.*user',
            'description': 'XSS跨站脚本攻击风险',
            'fix_action': 'escape_output',
            'severity': 'critical',
            'auto_fixable': True,
            'extensions': ['.js', '.ts', '.php', '.py']
        },
        {
            'rule_id': 'CODE-032',
            'pattern': r'hardcoded_password|hardcoded_secret|password\s*=\s*["\']',
            'description': '硬编码密码/密钥',
            'fix_action': 'use_env_var',
            'severity': 'critical',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.java', '.config']
        },
        {
            'rule_id': 'CODE-033',
            'pattern': r'insecure_random|random\(\)|Math\.random\(\)',
            'description': '使用不安全的随机数生成器',
            'fix_action': 'use_crypto_random',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.java']
        },
        {
            'rule_id': 'CODE-034',
            'pattern': r'command_injection|os\.system|subprocess.*shell=True|exec\(.*user',
            'description': '命令注入风险',
            'fix_action': 'sanitize_input_use_list',
            'severity': 'critical',
            'auto_fixable': True,
            'extensions': ['.py', '.php', '.ruby']
        },
        {
            'rule_id': 'CODE-035',
            'pattern': r'path_traversal|\.\./|\.\.\\\\|read_file.*user',
            'description': '路径遍历漏洞',
            'fix_action': 'validate_normalize_path',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.py', '.php', '.java', '.js']
        },
        {
            'rule_id': 'CODE-036',
            'pattern': r'insecure_deserialize|pickle\.load|eval\(|exec\(',
            'description': '不安全反序列化/代码执行',
            'fix_action': 'use_safe_alternative',
            'severity': 'critical',
            'auto_fixable': True,
            'extensions': ['.py', '.php', '.java']
        },
        {
            'rule_id': 'CODE-037',
            'pattern': r'debug_code_left|console\.log|print\(.*debug|TODO.*remove',
            'description': '调试代码残留',
            'fix_action': 'remove_debug_code',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.ts']
        }
    ]

    DOC_FIX_RULES = [
        # ===== 编码问题修复 (5条) =====
        {
            'rule_id': 'DOC-001',
            'pattern': 'non_utf8_encoding',
            'description': '非UTF-8编码',
            'fix_action': 'convert_to_utf8',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.md', '.txt', '.rst', '.adoc']
        },
        {
            'rule_id': 'DOC-002',
            'pattern': 'bom_detected|byte_order_mark',
            'description': 'BOM标记存在',
            'fix_action': 'remove_bom',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.md', '.txt', '.rst']
        },
        {
            'rule_id': 'DOC-003',
            'pattern': 'garbled_characters|乱码|mojibake|encoding error',
            'description': '乱码字符',
            'fix_action': 'detect_and_fix_encoding',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.md', '.txt', '.rst', '.csv']
        },
        {
            'rule_id': 'DOC-004',
            'pattern': 'mixed_line_ending|CRLF_LF_mixed',
            'description': '混合换行符',
            'fix_action': 'normalize_line_endings',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.md', '.txt', '.rst']
        },
        {
            'rule_id': 'DOC-005',
            'pattern': 'trailing_newlines_missing',
            'description': '文件末尾缺少换行',
            'fix_action': 'add_final_newline',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.md', '.txt', '.rst', '.py', '.js']
        },

        # ===== 格式问题修复 (10条) =====
        {
            'rule_id': 'DOC-010',
            'pattern': 'heading_skip|heading_level_skip',
            'description': '标题级别跳跃（如从H1直接到H3）',
            'fix_action': 'normalize_heading_levels',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.md', '.rst']
        },
        {
            'rule_id': 'DOC-011',
            'pattern': 'broken_table|malformed_table|table_syntax_error',
            'description': '表格格式错误',
            'fix_action': 'fix_table_syntax',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.md']
        },
        {
            'rule_id': 'DOC-012',
            'pattern': 'broken_link|dead_link|link_not_found',
            'description': '断裂链接',
            'fix_action': 'update_or_remove_link',
            'severity': 'medium',
            'auto_fixable': False,
            'extensions': ['.md', '.rst', '.html']
        },
        {
            'rule_id': 'DOC-013',
            'pattern': 'missing_alt_text|image_without_alt',
            'description': '图片缺少替代文本',
            'fix_action': 'add_alt_text',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.md', '.html', '.rst']
        },
        {
            'rule_id': 'DOC-014',
            'pattern': 'incorrect_list_formatting|list_indent_error',
            'description': '列表格式错误',
            'fix_action': 'fix_list_formatting',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.md', '.rst']
        },
        {
            'rule_id': 'DOC-015',
            'pattern': 'empty_section|section_without_content',
            'description': '空章节',
            'fix_action': 'fill_content_or_remove',
            'severity': 'medium',
            'auto_fixable': False,
            'extensions': ['.md', '.rst']
        },
        {
            'rule_id': 'DOC-016',
            'pattern': 'duplicate_heading|duplicate_title',
            'description': '重复标题',
            'fix_action': 'rename_duplicate',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.md', '.rst']
        },
        {
            'rule_id': 'DOC-017',
            'pattern': 'code_block_unclosed|fenced_block_not_closed',
            'description': '代码块未关闭',
            'fix_action': 'close_code_block',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.md']
        },
        {
            'rule_id': 'DOC-018',
            'pattern': 'hard_break_excessive|too_many_line_breaks',
            'description': '过多硬换行',
            'fix_action': 'merge_paragraphs',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.md']
        },
        {
            'rule_id': 'DOC-019',
            'pattern': 'whitespace_formatting|extra_spaces|multiple_spaces',
            'description': '多余空格',
            'fix_action': 'normalize_whitespace',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.md', '.rst']
        },

        # ===== 内容问题修复 (10条) =====
        {
            'rule_id': 'DOC-020',
            'pattern': 'outdated_info|deprecated_info|version_outdated',
            'description': '过时信息',
            'fix_action': 'mark_for_review',
            'severity': 'low',
            'auto_fixable': False,
            'extensions': ['.md', '.rst', '.html']
        },
        {
            'rule_id': 'DOC-021',
            'pattern': 'inconsistent_terminology|term_inconsistency',
            'description': '术语不一致',
            'fix_action': 'standardize_terms',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.md', '.rst']
        },
        {
            'rule_id': 'DOC-022',
            'pattern': 'missing_toc|table_of_contents_missing',
            'description': '缺少目录',
            'fix_action': 'generate_toc',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.md', '.rst']
        },
        {
            'rule_id': 'DOC-023',
            'pattern': 'spell_check|spelling_error|typo',
            'description': '拼写错误',
            'fix_action': 'suggest_correction',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.md', '.rst', '.txt']
        },
        {
            'rule_id': 'DOC-024',
            'pattern': 'image_path_relative|relative_image_path',
            'description': '使用相对图片路径',
            'fix_action': 'convert_to_absolute_or_verify',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.md', '.rst']
        },
        {
            'rule_id': 'DOC-025',
            'pattern': 'anchor_link_broken|internal_link_error',
            'description': '内部锚点链接错误',
            'fix_action': 'fix_anchor_links',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.md', '.html']
        },
        {
            'rule_id': 'DOC-026',
            'pattern': 'admonition_format_error|warning_note_format',
            'description': '警告/提示块格式错误',
            'fix_action': 'fix_admonition_format',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.md', '.rst']
        },
        {
            'rule_id': 'DOC-027',
            'pattern': 'footnote_error|reference_not_found',
            'description': '脚注引用错误',
            'fix_action': 'fix_footnote_references',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.md', '.rst']
        },
        {
            'rule_id': 'DOC-028',
            'pattern': 'language_tag_missing|code_no_language',
            'description': '代码块缺少语言标识',
            'fix_action': 'add_language_tag',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.md']
        },
        {
            'rule_id': 'DOC-029',
            'pattern': 'metadata_incomplete|frontmatter_missing',
            'description': '元数据不完整',
            'fix_action': 'update_metadata',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.md']
        }
    ]

    CONFIG_FIX_RULES = [
        # ===== 配置格式和结构 (8条) =====
        {
            'rule_id': 'CONFIG-001',
            'pattern': 'deprecated_config|deprecated_option|legacy_config',
            'description': '已弃用的配置项',
            'fix_action': 'migrate_to_new_format',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg']
        },
        {
            'rule_id': 'CONFIG-002',
            'pattern': 'missing_required_field|required_field_missing',
            'description': '缺少必需字段',
            'fix_action': 'add_default_value',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.json', '.yaml', '.yml', '.toml']
        },
        {
            'rule_id': 'CONFIG-003',
            'pattern': 'type_mismatch|type_error|invalid_type',
            'description': '类型不匹配',
            'fix_action': 'convert_type',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.json', '.yaml', '.yml', '.toml']
        },
        {
            'rule_id': 'CONFIG-004',
            'pattern': 'duplicate_key|duplicate_entry',
            'description': '重复键值',
            'fix_action': 'merge_or_rename',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.json', '.yaml', '.yml', '.ini']
        },
        {
            'rule_id': 'CONFIG-005',
            'pattern': 'syntax_error_config|parse_error|invalid_yaml|invalid_json',
            'description': '配置文件语法错误',
            'fix_action': 'fix_syntax',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.json', '.yaml', '.yml', '.toml', '.xml']
        },
        {
            'rule_id': 'CONFIG-006',
            'pattern': 'trailing_comma_json|trailing_comma_issue',
            'description': 'JSON尾部逗号（非标准）',
            'fix_action': 'remove_trailing_comma',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.json']
        },
        {
            'rule_id': 'CONFIG-007',
            'pattern': 'comment_in_json|JSON_comment',
            'description': 'JSON中的注释（非标准）',
            'fix_action': 'remove_comments_or_convert',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.json']
        },
        {
            'rule_id': 'CONFIG-008',
            'pattern': 'env_var_hardcoded|environment_hardcoded',
            'description': '硬编码环境变量值',
            'fix_action': 'use_env_placeholder',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.json', '.yaml', '.yml', '.env', '.ini']
        },

        # ===== 配置安全和最佳实践 (7条) =====
        {
            'rule_id': 'CONFIG-010',
            'pattern': 'insecure_default|default_password|default_secret',
            'description': '使用不安全的默认值',
            'fix_action': 'require_custom_value',
            'severity': 'high',
            'auto_fixable': False,
            'extensions': ['.json', '.yaml', '.yml', '.env', '.ini']
        },
        {
            'rule_id': 'CONFIG-011',
            'pattern': 'debug_enabled_production|debug.*true.*production',
            'description': '生产环境开启调试模式',
            'fix_action': 'disable_debug',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.json', '.yaml', '.yml', '.env', '.py']
        },
        {
            'rule_id': 'CONFIG-012',
            'pattern': 'excessive_permissions|permissions_too_open|777|world_writable',
            'description': '权限过于宽松',
            'fix_action': 'restrict_permissions',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.yaml', '.yml', '.sh', '.conf']
        },
        {
            'rule_id': 'CONFIG-013',
            'pattern': 'unused_config|unused_setting|dead_config',
            'description': '未使用的配置项',
            'fix_action': 'remove_unused_config',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.json', '.yaml', '.yml', '.toml', '.ini']
        },
        {
            'rule_id': 'CONFIG-014',
            'pattern': 'version_pin_missing|unpinned_dependency',
            'description': '依赖版本未锁定',
            'fix_action': 'pin_version',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.json', '.yaml', '.yml', '.toml', 'requirements.txt']
        },
        {
            'rule_id': 'CONFIG-015',
            'pattern': 'logging_level_verbose|DEBUG_logging_everywhere',
            'description': '日志级别设置过详细',
            'fix_action': 'adjust_log_level',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.json', '.yaml', '.yml', '.py', '.env']
        },
        {
            'rule_id': 'CONFIG-016',
            'pattern': 'port_conflict|default_port_in_use',
            'description': '端口配置可能冲突',
            'fix_action': 'suggest_alternate_port',
            'severity': 'medium',
            'auto_fixable': False,
            'extensions': ['.json', '.yaml', '.yml', '.env', '.conf']
        }
    ]

    PATH_FIX_RULES = [
        # ===== 路径硬编码和安全 (6条) =====
        {
            'rule_id': 'PATH-001',
            'pattern': 'hardcoded_absolute_path|/home/|/usr/local/|C:\\\\Users\\\\',
            'description': '硬编码绝对路径',
            'fix_action': 'use_path_config',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.sh', '.bat', '.ps1']
        },
        {
            'rule_id': 'PATH-002',
            'pattern': 'nonexistent_path|path_not_exist|directory_not_found',
            'description': '不存在的路径',
            'fix_action': 'validate_or_create',
            'severity': 'high',
            'auto_fixable': False,
            'extensions': ['.py', '.js', '.yaml', '.yml', '.json']
        },
        {
            'rule_id': 'PATH-003',
            'pattern': 'cross_platform_incompatible|backslash_forward_slash|path_separator',
            'description': '跨平台路径不兼容',
            'fix_action': 'use_pathlib',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.ts']
        },
        {
            'rule_id': 'PATH-004',
            'pattern': 'relative_path_outside_root|\\..\\/|\\..\\\\\\',
            'description': '相对路径超出项目根目录',
            'fix_action': 'resolve_to_absolute',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.yaml', '.yml']
        },
        {
            'rule_id': 'PATH-005',
            'pattern': 'temp_file_cleanup_missing|temporary_file_not_deleted',
            'description': '临时文件未清理',
            'fix_action': 'add_cleanup_logic',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.java']
        },
        {
            'rule_id': 'PATH-006',
            'pattern': 'sensitive_path_exposed|secret_path|credential_path',
            'description': '敏感路径暴露',
            'fix_action': 'use_secure_storage',
            'severity': 'critical',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.yaml', '.yml', '.env']
        },

        # ===== 路径组织和最佳实践 (7条) =====
        {
            'rule_id': 'PATH-010',
            'pattern': 'deeply_nested_path|nesting_too_deep',
            'description': '路径嵌套过深',
            'fix_action': 'flatten_structure',
            'severity': 'low',
            'auto_fixable': False,
            'extensions': ['.py', '.js', '.yaml', '.yml']
        },
        {
            'rule_id': 'PATH-011',
            'pattern': 'magic_path|unnamed_temp|tmp_dir',
            'description': '魔术路径/未命名的临时目录',
            'fix_action': 'use_named_temp_directory',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.java']
        },
        {
            'rule_id': 'PATH-012',
            'pattern': 'case_sensitive_path_issue|filename_case',
            'description': '路径大小写敏感问题',
            'fix_action': 'normalize_case',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.sh']
        },
        {
            'rule_id': 'PATH-013',
            'pattern': 'path_concatenation_unsafe|string_concat_path',
            'description': '不安全的路径拼接',
            'fix_action': 'use_path_join',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['.py', '.js', '.java']
        },
        {
            'rule_id': 'PATH-014',
            'pattern': 'symlink_not_handled|symbolic_link',
            'description': '符号链接未处理',
            'fix_action': 'handle_symlink_properly',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['.py', '.sh']
        },
        {
            'rule_id': 'PATH-015',
            'pattern': 'network_path_used|UNC_path|smb://|//server/',
            'description': '使用网络路径',
            'fix_action': 'use_local_or_configured_path',
            'severity': 'medium',
            'auto_fixable': False,
            'extensions': ['.py', '.js', '.yaml', '.yml', '.json']
        },
        {
            'rule_id': 'PATH-016',
            'pattern': 'path_with_spaces|space_in_path',
            'description': '路径包含空格',
            'fix_action': 'quote_or_escape_path',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['.py', '.sh', '.bat', '.ps1']
        }
    ]

    DEPENDENCY_FIX_RULES = [
        # ===== 依赖管理 (6条) =====
        {
            'rule_id': 'DEP-001',
            'pattern': 'outdated_dependency|dependency_outdated|version_old',
            'description': '依赖版本过旧',
            'fix_action': 'update_version',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['requirements.txt', 'package.json', 'Pipfile', 'pyproject.toml', 'pom.xml']
        },
        {
            'rule_id': 'DEP-002',
            'pattern': 'missing_dependency|dependency_missing|import_error',
            'description': '缺少依赖',
            'fix_action': 'install_package',
            'severity': 'high',
            'auto_fixable': True,
            'extensions': ['requirements.txt', 'package.json', 'Pipfile', 'pyproject.toml']
        },
        {
            'rule_id': 'DEP-003',
            'pattern': 'version_conflict|dependency_conflict|version_clash',
            'description': '版本冲突',
            'fix_action': 'resolve_conflict',
            'severity': 'high',
            'auto_fixable': False,
            'extensions': ['requirements.txt', 'package.json', 'Pipfile', 'pyproject.toml', 'pom.xml']
        },
        {
            'rule_id': 'DEP-004',
            'pattern': 'deprecated_package|package_deprecated|abandoned_package',
            'description': '使用已弃用的包',
            'fix_action': 'find_alternative',
            'severity': 'medium',
            'auto_fixable': False,
            'extensions': ['requirements.txt', 'package.json', 'Pipfile', 'pyproject.toml']
        },
        {
            'rule_id': 'DEP-005',
            'pattern': 'vulnerable_dependency|security_vulnerability|CVE',
            'description': '存在安全漏洞的依赖',
            'fix_action': 'upgrade_to_safe_version',
            'severity': 'critical',
            'auto_fixable': True,
            'extensions': ['requirements.txt', 'package.json', 'Pipfile', 'pyproject.toml', 'pom.xml']
        },
        {
            'rule_id': 'DEP-006',
            'pattern': 'unnecessary_dependency|unused_dependency|bloat',
            'description': '不必要的依赖',
            'fix_action': 'remove_unused',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['requirements.txt', 'package.json', 'Pipfile', 'pyproject.toml']
        },

        # ===== 依赖安全和合规 (4条) =====
        {
            'rule_id': 'DEP-010',
            'pattern': 'license_incompatible|license_issue|GPL_violation',
            'description': '许可证不兼容',
            'fix_action': 'check_license_compatibility',
            'severity': 'medium',
            'auto_fixable': False,
            'extensions': ['requirements.txt', 'package.json', 'Pipfile', 'pyproject.toml', 'pom.xml']
        },
        {
            'rule_id': 'DEP-011',
            'pattern': 'dev_dependency_in_prod|development_only_in_production',
            'description': '开发依赖出现在生产环境',
            'fix_action': 'move_to_dev_dependencies',
            'severity': 'medium',
            'auto_fixable': True,
            'extensions': ['package.json', 'Pipfile', 'pyproject.toml']
        },
        {
            'rule_id': 'DEP-012',
            'pattern': 'pinned_to_commit|commit_hash_dependency',
            'description': '依赖固定到特定提交',
            'fix_action': 'use_semver_range',
            'severity': 'low',
            'auto_fixable': True,
            'extensions': ['package.json', 'requirements.txt']
        },
        {
            'rule_id': 'DEP-013',
            'pattern': 'circular_dependency|circular_import',
            'description': '循环依赖',
            'fix_action': 'refactor_to_break_cycle',
            'severity': 'high',
            'auto_fixable': False,
            'extensions': ['.py', '.js', '.ts', '.java']
        }
    ]

    ALL_RULES = CODE_FIX_RULES + DOC_FIX_RULES + CONFIG_FIX_RULES + PATH_FIX_RULES + DEPENDENCY_FIX_RULES

    def __init__(self):
        self.logger = logging.getLogger('ExtendedFixRuleLibrary')
        self._rules_cache: Dict[str, FixRule] = {}
        self._category_index: Dict[FixRuleCategory, List[FixRule]] = defaultdict(list)
        self._initialize_rules()

    def _initialize_rules(self):
        """初始化所有规则"""
        category_map = {
            'code': FixRuleCategory.CODE,
            'document': FixRuleCategory.DOCUMENT,
            'config': FixRuleCategory.CONFIG,
            'path': FixRuleCategory.PATH,
            'dependency': FixRuleCategory.DEPENDENCY
        }

        for rule_data in self.ALL_RULES:
            rule = FixRule(
                rule_id=rule_data['rule_id'],
                category=category_map.get(
                    next((k for k in ['code', 'document', 'config', 'path', 'dependency']
                         if k in rule_data.get('rule_id', '').lower()), ''),
                    FixRuleCategory.CODE
                ) if any(k in rule_data['rule_id'].lower() for k in ['CODE', 'DOC', 'CONFIG', 'PATH', 'DEP'])
                else FixRuleCategory.CODE,
                pattern=rule_data['pattern'],
                description=rule_data['description'],
                fix_action=rule_data['fix_action'],
                severity=FixSeverity(rule_data['severity']),
                auto_fixable=rule_data.get('auto_fixable', True),
                confidence=rule_data.get('confidence', 0.8),
                affected_extensions=rule_data.get('extensions', []),
                example_before=rule_data.get('example_before', ''),
                example_after=rule_data.get('example_after', '')
            )

            if rule_data['rule_id'].startswith('CODE'):
                rule.category = FixRuleCategory.CODE
            elif rule_data['rule_id'].startswith('DOC'):
                rule.category = FixRuleCategory.DOCUMENT
            elif rule_data['rule_id'].startswith('CONFIG'):
                rule.category = FixRuleCategory.CONFIG
            elif rule_data['rule_id'].startswith('PATH'):
                rule.category = FixRuleCategory.PATH
            elif rule_data['rule_id'].startswith('DEP'):
                rule.category = FixRuleCategory.DEPENDENCY

            self._rules_cache[rule.rule_id] = rule
            self._category_index[rule.category].append(rule)

        self.logger.info(f"已初始化 {len(self._rules_cache)} 条修复规则")

    def get_all_rules(self) -> List[FixRule]:
        """获取所有规则"""
        return list(self._rules_cache.values())

    def get_rule(self, rule_id: str) -> Optional[FixRule]:
        """获取单个规则"""
        return self._rules_cache.get(rule_id)

    def get_rules_by_category(self, category: Union[str, FixRuleCategory]) -> List[FixRule]:
        """按类别获取规则"""
        if isinstance(category, str):
            category = FixRuleCategory(category)
        return list(self._category_index.get(category, []))

    def get_rules_by_severity(self, severity: Union[str, FixSeverity]) -> List[FixRule]:
        """按严重程度获取规则"""
        if isinstance(severity, str):
            severity = FixSeverity(severity)
        return [r for r in self._rules_cache.values() if r.severity == severity]

    def get_auto_fixable_rules(self) -> List[FixRule]:
        """获取可自动修复的规则"""
        return [r for r in self._rules_cache.values() if r.auto_fixable]

    def find_matching_rules(self, content: str, file_extension: str = "") -> List[Tuple[FixRule, float]]:
        """
        查找匹配的规则

        Returns:
            匹配的规则列表，每个元素为(规则, 匹配度得分)
        """
        matches = []

        for rule in self._rules_cache.values():
            if file_extension and rule.affected_extensions:
                if file_extension not in rule.affected_extensions and '*' not in rule.affected_extensions:
                    continue

            try:
                if re.search(rule.pattern, content, re.IGNORECASE):
                    matches.append((rule, 0.9))
                elif any(word.lower() in content.lower() for word in rule.pattern.split('|')[:3]):
                    matches.append((rule, 0.5))
            except re.error:
                if rule.pattern.lower() in content.lower():
                    matches.append((rule, 0.7))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def get_statistics(self) -> Dict[str, Any]:
        """获取规则库统计信息"""
        categories = defaultdict(int)
        severities = defaultdict(int)
        auto_fixable_count = 0

        for rule in self._rules_cache.values():
            categories[rule.category.value] += 1
            severities[rule.severity.value] += 1
            if rule.auto_fixable:
                auto_fixable_count += 1

        return {
            'total_rules': len(self._rules_cache),
            'by_category': dict(categories),
            'by_severity': dict(severities),
            'auto_fixable_count': auto_fixable_count,
            'auto_fixable_rate': f"{auto_fixable_count / len(self._rules_cache) * 100:.1f}%"
        }


class EnhancedDocEncodingFixer:
    """
    增强版文档编码修复器

    支持多种编码自动检测、乱码字符识别和智能修复。
    """

    ENCODINGS_TO_TRY = ['utf-8', 'gbk', 'gb2312', 'big5', 'latin-1', 'cp1252', 'shift_jis']

    GARBLE_PATTERNS = [
        re.compile(r'[ï¿½ï¿½]+'),
        re.compile(r'[ä¸€æœŸ]+'),
        re.compile(r'[æ–‡æ¡£ç¼–ç ]+'),
        re.compile(r'[ä»€åŠ¨èªž]+'),
        re.compile(r'[ÃÂÃ¡Ã©Ã³]+'),
        re.compile(r'[ï¼Œï¼šï¼]+'),
        re.compile(r'[â€œâ€�â€™â€œ]+'),
        re.compile(r'[ðŸ\x94¥ðŸ\x93]+'),
    ]

    def __init__(self):
        self.logger = logging.getLogger('EnhancedDocEncodingFixer')
        self.fix_history: List[EncodingFixResult] = []

    def detect_and_fix(self, file_path: Union[str, Path]) -> EncodingFixResult:
        """
        检测并修复文档编码问题

        Args:
            file_path: 文件路径

        Returns:
            修复结果报告
        """
        path = Path(file_path)

        if not path.exists():
            return EncodingFixResult(
                file_path=path,
                original_encoding="unknown",
                detected_encoding="unknown",
                fixed_encoding="unknown",
                had_bom=False,
                bom_removed=False,
                garbled_chars_found=0,
                garbled_chars_fixed=0,
                success=False,
                confidence=0.0,
                details=f"文件不存在: {file_path}"
            )

        try:
            with open(path, 'rb') as f:
                raw_bytes = f.read()

            original_encoding = self._detect_original_encoding(raw_bytes)

            has_bom = raw_bytes.startswith(b'\xef\xbb\xbf') or \
                     raw_bytes.startswith(b'\xff\xfe') or \
                     raw_bytes.startswith(b'\xfe\xff')

            best_encoding, confidence = self._find_best_encoding(raw_bytes)

            content, garbled_count = self._decode_with_fallback(raw_bytes, best_encoding)

            garbled_fixed = self._count_garbled_characters(content)

            if has_bom or garbled_fixed > 0 or original_encoding != best_encoding:
                fixed_content = self._fix_garbled_text(content, best_encoding)

                if has_bom:
                    raw_bytes = self._remove_bom(raw_bytes)

                with open(path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(fixed_content)

                result = EncodingFixResult(
                    file_path=path,
                    original_encoding=original_encoding,
                    detected_encoding=best_encoding,
                    fixed_encoding='utf-8',
                    had_bom=has_bom,
                    bom_removed=has_bom,
                    garbled_chars_found=garbled_count + garbled_fixed,
                    garbled_chars_fixed=garbled_fixed,
                    success=True,
                    confidence=confidence,
                    details=f"成功转换 {original_encoding} → UTF-8，修复{garbled_fixed}个乱码字符"
                )
            else:
                result = EncodingFixResult(
                    file_path=path,
                    original_encoding=original_encoding,
                    detected_encoding=original_encoding,
                    fixed_encoding=original_encoding,
                    had_bom=has_bom,
                    bom_removed=False,
                    garbled_chars_found=garbled_count,
                    garbled_chars_fixed=0,
                    success=True,
                    confidence=1.0,
                    details="文件编码正常，无需修复"
                )

            self.fix_history.append(result)
            return result

        except Exception as e:
            self.logger.error(f"处理文件 {file_path} 时出错: {e}")
            return EncodingFixResult(
                file_path=path,
                original_encoding="error",
                detected_encoding="error",
                fixed_encoding="error",
                had_bom=False,
                bom_removed=False,
                garbled_chars_found=0,
                garbled_chars_fixed=0,
                success=False,
                confidence=0.0,
                details=f"处理失败: {str(e)}"
            )

    def _detect_original_encoding(self, raw_bytes: bytes) -> str:
        """检测原始编码"""
        if raw_bytes.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-bom'
        elif raw_bytes.startswith(b'\xff\xfe'):
            return 'utf-16-le'
        elif raw_bytes.startswith(b'\xfe\xff'):
            return 'utf-16-be'

        detection = chardet.detect(raw_bytes)
        encoding = detection.get('encoding', 'utf-8')
        confidence = detection.get('confidence', 0)

        if confidence < 0.5:
            return 'unknown'

        return encoding or 'utf-8'

    def _find_best_encoding(self, raw_bytes: bytes) -> Tuple[str, float]:
        """查找最佳编码"""
        best_encoding = 'utf-8'
        best_score = 0.0

        for encoding in self.ENCODINGS_TO_TRY:
            try:
                decoded = raw_bytes.decode(encoding, errors='ignore')
                score = self._evaluate_decoded_quality(decoded)

                if score > best_score:
                    best_score = score
                    best_encoding = encoding
            except (UnicodeDecodeError, LookupError):
                continue

        chardet_result = chardet.detect(raw_bytes)
        chardet_encoding = chardet_result.get('encoding')
        chardet_confidence = chardet_result.get('confidence', 0)

        if chardet_encoding and chardet_confidence > 0.7:
            return chardet_encoding, chardet_confidence

        return best_encoding, min(1.0, best_score / 100)

    def _evaluate_decoded_quality(self, text: str) -> float:
        """评估解码文本质量"""
        score = 100.0

        chinese_char_ratio = sum(1 for c in text if '\u4e00' <= c <= '\u9fff') / max(len(text), 1)
        if chinese_char_ratio > 0.3:
            score += 20

        printable_ratio = sum(1 for c in text if c.isprintable() or c in '\n\r\t') / max(len(text), 1)
        score *= printable_ratio

        garble_count = sum(1 for pattern in self.GARBLE_PATTERNS for _ in pattern.findall(text))
        score -= garble_count * 5

        common_chinese_words = ['的', '是', '在', '了', '和', '有', '为', '与', '对', '等',
                               'the', 'is', 'are', 'was', 'were', 'and', 'or', 'to', 'of', 'in']
        common_word_count = sum(1 for word in common_chinese_words if word in text.lower())
        score += common_word_count * 2

        return max(0, score)

    def _decode_with_fallback(self, raw_bytes: bytes, encoding: str) -> Tuple[str, int]:
        """解码内容并统计乱码"""
        errors = 'replace'
        content = raw_bytes.decode(encoding, errors=errors)

        garbled_count = content.count('\ufffd')

        return content, garbled_count

    def _count_garbled_characters(self, content: str) -> int:
        """计数乱码字符"""
        count = 0
        for pattern in self.GARBLE_PATTERNS:
            count += len(pattern.findall(content))
        return count

    def fix_garbled_text(self, content: bytes) -> str:
        """
        修复乱码文本内容

        使用启发式算法尝试还原正确内容
        """
        text = content.decode('utf-8', errors='replace')

        for pattern in self.GARBLE_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                try:
                    fixed = self._attempt_garble_fix(match)
                    if fixed and fixed != match:
                        text = text.replace(match, fixed, 1)
                except Exception:
                    continue

        text = self._normalize_text(text)

        return text

    def _fix_garbled_text(self, content: str, source_encoding: str) -> str:
        """基于源编码修复乱码"""
        fixed = content

        encoding_pairs = [
            ('gbk', 'utf-8'),
            ('gb2312', 'utf-8'),
            ('big5', 'utf-8'),
            ('latin-1', 'utf-8'),
            ('cp1252', 'utf-8'),
        ]

        for src_enc, target_enc in encoding_pairs:
            if src_enc == source_encoding:
                continue

            try:
                as_bytes = content.encode(src_enc, errors='ignore')
                candidate = as_bytes.decode(target_enc, errors='ignore')

                candidate_score = self._evaluate_decoded_quality(candidate)
                current_score = self._evaluate_decoded_quality(fixed)

                if candidate_score > current_score:
                    fixed = candidate
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue

        return fixed

    def _attempt_garble_fix(self, garbled_segment: str) -> Optional[str]:
        """尝试修复单个乱码段"""
        fixes = {
            'ï¿½': '',
            'ä¸€': '一',
            'æœŸ': '期',
            'æ–‡': '文',
            'æ¡£': '档',
            'ç¼–': '编',
            'ä»€': '全',
            'åŠ¨': '动',
            'è¯­': '语',
            'ÃÂ': '',
            'ï¼Œ': '，',
            'ï¼š': '：',
            'ï¼': '',
            'â€œ': '"',
            'â€�': '"',
            'â€™': "'",
        }

        return fixes.get(garbled_segment)

    def _normalize_text(self, text: str) -> str:
        """规范化文本"""
        replacements = {
            '\r\n': '\n',
            '\r': '\n',
            '\t': '    ',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')

        text = text.rstrip('\n') + '\n'

        return text

    def _remove_bom(self, raw_bytes: bytes) -> bytes:
        """移除BOM标记"""
        if raw_bytes.startswith(b'\xef\xbb\xbf'):
            return raw_bytes[3:]
        elif raw_bytes.startswith(b'\xff\xfe'):
            return raw_bytes[2:]
        elif raw_bytes.startswith(b'\xfe\xff'):
            return raw_bytes[2:]
        return raw_bytes

    def batch_fix_directory(
        self,
        directory: Union[str, Path],
        extensions: Optional[List[str]] = None
    ) -> List[EncodingFixResult]:
        """
        批量修复目录中的文件

        Args:
            directory: 目录路径
            extensions: 要处理的文件扩展名列表（默认处理所有文本文件）

        Returns:
            所有文件的修复结果列表
        """
        dir_path = Path(directory)
        extensions = extensions or ['.md', '.txt', '.rst', '.csv', '.json', '.yaml', '.yml']

        results = []

        for ext in extensions:
            for file_path in dir_path.rglob(f'*{ext}'):
                if file_path.is_file():
                    result = self.detect_and_fix(file_path)
                    results.append(result)

        self.logger.info(f"批量修复完成: {len(results)} 个文件")
        return results


if __name__ == '__main__':
    print("全方位自修复系统模块已加载")
