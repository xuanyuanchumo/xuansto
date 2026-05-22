#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修复建议系统 - Auto Fix Suggestion System
提供智能修复建议生成、修复策略库和修复效果评估

功能:
1. 修复建议生成器 - 基于问题类型生成修复建议
2. 修复策略库 - 预定义和自定义修复策略
3. 修复效果评估 - 评估修复方案的有效性
4. 代码模板生成 - 生成修复代码模板
5. 风险评估 - 评估修复方案的风险
"""

import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FixCategory(Enum):
    CODE_FIX = "code_fix"
    CONFIG_FIX = "config_fix"
    DEPENDENCY_FIX = "dependency_fix"
    DATABASE_FIX = "database_fix"
    NETWORK_FIX = "network_fix"
    SECURITY_FIX = "security_fix"
    PERFORMANCE_FIX = "performance_fix"
    LOGIC_FIX = "logic_fix"
    REFACTOR = "refactor"
    WORKAROUND = "workaround"


class FixComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    MAJOR = "major"


class FixRisk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FixConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    EXPERIMENTAL = "experimental"


@dataclass
class FixSuggestion:
    suggestion_id: str
    title: str
    description: str
    category: FixCategory
    complexity: FixComplexity
    risk: FixRisk
    confidence: FixConfidence
    steps: List[str]
    code_templates: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    estimated_time: str = ""
    references: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class FixStrategy:
    strategy_id: str
    name: str
    description: str
    applicable_patterns: List[str]
    suggestions: List[FixSuggestion]
    priority: int = 0
    success_rate: float = 0.0
    usage_count: int = 0


@dataclass
class FixEvaluation:
    evaluation_id: str
    suggestion: FixSuggestion
    effectiveness_score: float
    risk_score: float
    effort_score: float
    overall_score: float
    pros: List[str]
    cons: List[str]
    recommendation: str
    alternative_suggestions: List[str] = field(default_factory=list)


@dataclass
class FixReport:
    report_id: str
    generated_at: str
    issue_description: str
    suggestions: List[FixSuggestion]
    evaluations: List[FixEvaluation]
    best_suggestion: Optional[FixSuggestion]
    summary: str


class FixStrategyLibrary:
    """修复策略库"""
    
    STRATEGIES = [
        {
            "id": "S001",
            "name": "空值检查策略",
            "description": "添加空值检查以防止空指针异常",
            "patterns": ["AttributeError", "NullPointerException", "NoneType"],
            "suggestions": [
                {
                    "title": "添加None检查",
                    "description": "在使用对象前检查是否为None",
                    "category": FixCategory.CODE_FIX,
                    "complexity": FixComplexity.SIMPLE,
                    "risk": FixRisk.LOW,
                    "confidence": FixConfidence.HIGH,
                    "steps": [
                        "识别可能导致None的变量",
                        "在使用前添加 if var is not None 检查",
                        "为None情况添加适当的处理逻辑",
                    ],
                    "code_templates": [
                        "# Before:\nresult = obj.method()\n\n# After:\nif obj is not None:\n    result = obj.method()\nelse:\n    result = default_value",
                        "# Python 安全访问\nresult = obj.method() if obj else default_value",
                    ],
                    "estimated_time": "5-15分钟",
                },
            ],
        },
        {
            "id": "S002",
            "name": "类型转换策略",
            "description": "添加类型检查和转换以解决类型错误",
            "patterns": ["TypeError", "type mismatch", "cannot convert"],
            "suggestions": [
                {
                    "title": "添加类型检查和转换",
                    "description": "在操作前验证并转换类型",
                    "category": FixCategory.CODE_FIX,
                    "complexity": FixComplexity.SIMPLE,
                    "risk": FixRisk.LOW,
                    "confidence": FixConfidence.HIGH,
                    "steps": [
                        "识别类型不匹配的位置",
                        "添加类型检查 isinstance()",
                        "添加适当的类型转换",
                    ],
                    "code_templates": [
                        "# Before:\nresult = a + b\n\n# After:\nif isinstance(a, (int, float)) and isinstance(b, (int, float)):\n    result = a + b\nelse:\n    result = float(a) + float(b)",
                    ],
                    "estimated_time": "10-20分钟",
                },
            ],
        },
        {
            "id": "S003",
            "name": "字典键检查策略",
            "description": "安全访问字典键以避免KeyError",
            "patterns": ["KeyError", "key not found"],
            "suggestions": [
                {
                    "title": "使用get方法或检查键存在",
                    "description": "使用dict.get()或in操作符安全访问字典",
                    "category": FixCategory.CODE_FIX,
                    "complexity": FixComplexity.SIMPLE,
                    "risk": FixRisk.LOW,
                    "confidence": FixConfidence.HIGH,
                    "steps": [
                        "找到直接访问字典键的代码",
                        "替换为dict.get()方法",
                        "或添加键存在性检查",
                    ],
                    "code_templates": [
                        "# Before:\nvalue = my_dict[key]\n\n# After:\nvalue = my_dict.get(key, default_value)",
                        "# Before:\nvalue = my_dict[key]\n\n# After:\nif key in my_dict:\n    value = my_dict[key]\nelse:\n    value = default_value",
                    ],
                    "estimated_time": "5-10分钟",
                },
            ],
        },
        {
            "id": "S004",
            "name": "索引边界检查策略",
            "description": "添加索引边界检查以防止IndexError",
            "patterns": ["IndexError", "index out of range"],
            "suggestions": [
                {
                    "title": "添加索引边界检查",
                    "description": "在访问列表/数组前检查索引范围",
                    "category": FixCategory.CODE_FIX,
                    "complexity": FixComplexity.SIMPLE,
                    "risk": FixRisk.LOW,
                    "confidence": FixConfidence.HIGH,
                    "steps": [
                        "识别索引访问的位置",
                        "添加索引范围检查",
                        "处理越界情况",
                    ],
                    "code_templates": [
                        "# Before:\nitem = my_list[index]\n\n# After:\nif 0 <= index < len(my_list):\n    item = my_list[index]\nelse:\n    item = default_value",
                        "# 使用切片安全访问\nitem = my_list[index:index+1][0] if index < len(my_list) else default_value",
                    ],
                    "estimated_time": "5-15分钟",
                },
            ],
        },
        {
            "id": "S005",
            "name": "异常处理策略",
            "description": "添加try-except块捕获和处理异常",
            "patterns": ["Error", "Exception", "failed"],
            "suggestions": [
                {
                    "title": "添加异常处理",
                    "description": "使用try-except捕获并处理可能的异常",
                    "category": FixCategory.CODE_FIX,
                    "complexity": FixComplexity.MODERATE,
                    "risk": FixRisk.MEDIUM,
                    "confidence": FixConfidence.HIGH,
                    "steps": [
                        "识别可能抛出异常的代码",
                        "添加try-except块",
                        "实现适当的异常处理逻辑",
                        "添加日志记录",
                    ],
                    "code_templates": [
                        "try:\n    result = risky_operation()\nexcept SpecificException as e:\n    logger.error(f'Operation failed: {e}')\n    result = fallback_value",
                    ],
                    "estimated_time": "15-30分钟",
                },
            ],
        },
        {
            "id": "S006",
            "name": "依赖安装策略",
            "description": "安装缺失的依赖包",
            "patterns": ["ImportError", "ModuleNotFoundError", "No module named"],
            "suggestions": [
                {
                    "title": "安装缺失的依赖",
                    "description": "使用pip安装缺失的Python包",
                    "category": FixCategory.DEPENDENCY_FIX,
                    "complexity": FixComplexity.SIMPLE,
                    "risk": FixRisk.LOW,
                    "confidence": FixConfidence.HIGH,
                    "steps": [
                        "识别缺失的模块名称",
                        "使用pip install安装",
                        "验证安装成功",
                    ],
                    "code_templates": [
                        "# 安装命令\npip install package_name\n\n# 或添加到requirements.txt\necho 'package_name==version' >> requirements.txt\npip install -r requirements.txt",
                    ],
                    "estimated_time": "5-10分钟",
                },
            ],
        },
        {
            "id": "S007",
            "name": "文件路径修复策略",
            "description": "修复文件路径问题",
            "patterns": ["FileNotFoundError", "No such file or directory"],
            "suggestions": [
                {
                    "title": "检查和修复文件路径",
                    "description": "验证文件路径是否存在，使用正确的路径格式",
                    "category": FixCategory.CODE_FIX,
                    "complexity": FixComplexity.SIMPLE,
                    "risk": FixRisk.LOW,
                    "confidence": FixConfidence.HIGH,
                    "steps": [
                        "检查文件路径是否正确",
                        "使用os.path处理路径",
                        "添加文件存在性检查",
                    ],
                    "code_templates": [
                        "import os\nfrom pathlib import Path\n\n# 使用Path处理路径\nfile_path = Path('data') / 'file.txt'\n\n# 检查文件存在\nif file_path.exists():\n    with open(file_path) as f:\n        content = f.read()\nelse:\n    print(f'File not found: {file_path}')",
                    ],
                    "estimated_time": "10-20分钟",
                },
            ],
        },
        {
            "id": "S008",
            "name": "数据库连接修复策略",
            "description": "修复数据库连接和查询问题",
            "patterns": ["DatabaseError", "IntegrityError", "OperationalError", "SQL error"],
            "suggestions": [
                {
                    "title": "检查数据库连接和查询",
                    "description": "验证数据库连接配置，检查SQL语句",
                    "category": FixCategory.DATABASE_FIX,
                    "complexity": FixComplexity.MODERATE,
                    "risk": FixRisk.MEDIUM,
                    "confidence": FixConfidence.MEDIUM,
                    "steps": [
                        "检查数据库连接字符串",
                        "验证数据库服务状态",
                        "检查SQL语句语法",
                        "验证表结构和约束",
                    ],
                    "code_templates": [
                        "import sqlite3\n\ntry:\n    conn = sqlite3.connect('database.db')\n    cursor = conn.cursor()\n    cursor.execute('SELECT * FROM table WHERE id = ?', (id,))\n    result = cursor.fetchone()\nexcept sqlite3.Error as e:\n    print(f'Database error: {e}')\nfinally:\n    conn.close()",
                    ],
                    "estimated_time": "30-60分钟",
                },
            ],
        },
        {
            "id": "S009",
            "name": "网络连接修复策略",
            "description": "修复网络连接问题",
            "patterns": ["ConnectionError", "Connection refused", "timeout", "Network is unreachable"],
            "suggestions": [
                {
                    "title": "添加网络连接处理",
                    "description": "添加重试机制和超时处理",
                    "category": FixCategory.NETWORK_FIX,
                    "complexity": FixComplexity.MODERATE,
                    "risk": FixRisk.MEDIUM,
                    "confidence": FixConfidence.MEDIUM,
                    "steps": [
                        "检查网络连接状态",
                        "验证目标服务是否运行",
                        "添加连接超时设置",
                        "实现重试机制",
                    ],
                    "code_templates": [
                        "import requests\nfrom requests.adapters import HTTPAdapter\nfrom urllib3.util.retry import Retry\n\nsession = requests.Session()\nretry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])\nadapter = HTTPAdapter(max_retries=retry)\nsession.mount('http://', adapter)\nsession.mount('https://', adapter)\n\ntry:\n    response = session.get(url, timeout=30)\n    response.raise_for_status()\nexcept requests.RequestException as e:\n    print(f'Network error: {e}')",
                    ],
                    "estimated_time": "30-60分钟",
                },
            ],
        },
        {
            "id": "S010",
            "name": "权限问题修复策略",
            "description": "修复权限相关问题",
            "patterns": ["PermissionError", "Permission denied", "Access denied", "Unauthorized"],
            "suggestions": [
                {
                    "title": "检查和修复权限",
                    "description": "检查文件/目录权限，验证用户权限",
                    "category": FixCategory.SECURITY_FIX,
                    "complexity": FixComplexity.SIMPLE,
                    "risk": FixRisk.MEDIUM,
                    "confidence": FixConfidence.MEDIUM,
                    "steps": [
                        "检查当前用户权限",
                        "验证文件/目录权限设置",
                        "修改权限或使用正确的用户运行",
                    ],
                    "code_templates": [
                        "import os\nimport stat\n\n# 检查文件权限\nfile_path = '/path/to/file'\nfile_stat = os.stat(file_path)\nprint(f'Permissions: {stat.filemode(file_stat.st_mode)}')\n\n# 修改权限\nos.chmod(file_path, 0o644)",
                    ],
                    "estimated_time": "10-30分钟",
                },
            ],
        },
        {
            "id": "S011",
            "name": "内存优化策略",
            "description": "优化内存使用以解决内存问题",
            "patterns": ["MemoryError", "Out of memory", "heap space"],
            "suggestions": [
                {
                    "title": "优化内存使用",
                    "description": "分批处理数据，优化数据结构",
                    "category": FixCategory.PERFORMANCE_FIX,
                    "complexity": FixComplexity.COMPLEX,
                    "risk": FixRisk.HIGH,
                    "confidence": FixConfidence.MEDIUM,
                    "steps": [
                        "分析内存使用情况",
                        "实现分批处理",
                        "优化数据结构",
                        "添加内存监控",
                    ],
                    "code_templates": [
                        "# 分批处理大数据\ndef process_large_data(data, batch_size=1000):\n    for i in range(0, len(data), batch_size):\n        batch = data[i:i + batch_size]\n        yield process_batch(batch)\n\n# 使用生成器\ndef generate_data():\n    for item in large_dataset:\n        yield transform(item)",
                    ],
                    "estimated_time": "2-4小时",
                },
            ],
        },
        {
            "id": "S012",
            "name": "递归深度修复策略",
            "description": "修复递归深度问题",
            "patterns": ["RecursionError", "maximum recursion depth"],
            "suggestions": [
                {
                    "title": "转换为迭代或增加递归限制",
                    "description": "将递归改为迭代，或增加递归深度限制",
                    "category": FixCategory.CODE_FIX,
                    "complexity": FixComplexity.MODERATE,
                    "risk": FixRisk.MEDIUM,
                    "confidence": FixConfidence.MEDIUM,
                    "steps": [
                        "分析递归逻辑",
                        "检查递归终止条件",
                        "转换为迭代实现",
                        "或增加递归深度限制",
                    ],
                    "code_templates": [
                        "import sys\n\n# 增加递归深度限制\nsys.setrecursionlimit(3000)\n\n# 转换为迭代\ndef iterative_solution(data):\n    stack = [data]\n    result = []\n    while stack:\n        current = stack.pop()\n        result.append(process(current))\n        stack.extend(get_children(current))\n    return result",
                    ],
                    "estimated_time": "30-60分钟",
                },
            ],
        },
        {
            "id": "S013",
            "name": "死锁修复策略",
            "description": "修复死锁问题",
            "patterns": ["Deadlock", "deadlock detected", "lock wait timeout"],
            "suggestions": [
                {
                    "title": "优化锁的使用",
                    "description": "检查锁的使用顺序，减少锁持有时间",
                    "category": FixCategory.CODE_FIX,
                    "complexity": FixComplexity.COMPLEX,
                    "risk": FixRisk.HIGH,
                    "confidence": FixConfidence.LOW,
                    "steps": [
                        "分析锁的使用情况",
                        "确保锁的获取顺序一致",
                        "减少锁持有时间",
                        "考虑使用无锁数据结构",
                    ],
                    "code_templates": [
                        "import threading\n\n# 使用上下文管理器\nlock = threading.Lock()\n\nwith lock:\n    critical_section()\n\n# 使用RLock避免死锁\nrlock = threading.RLock()",
                    ],
                    "estimated_time": "2-4小时",
                },
            ],
        },
        {
            "id": "S014",
            "name": "SQL注入防护策略",
            "description": "防止SQL注入攻击",
            "patterns": ["sql injection", "SQLInjection", "injection"],
            "suggestions": [
                {
                    "title": "使用参数化查询",
                    "description": "使用参数化查询防止SQL注入",
                    "category": FixCategory.SECURITY_FIX,
                    "complexity": FixComplexity.MODERATE,
                    "risk": FixRisk.LOW,
                    "confidence": FixConfidence.HIGH,
                    "steps": [
                        "识别存在SQL注入风险的代码",
                        "使用参数化查询替换字符串拼接",
                        "验证输入数据",
                    ],
                    "code_templates": [
                        "# Before (不安全)\nquery = f\"SELECT * FROM users WHERE id = {user_id}\"\n\n# After (安全)\nquery = \"SELECT * FROM users WHERE id = ?\"\ncursor.execute(query, (user_id,))",
                    ],
                    "estimated_time": "30-60分钟",
                },
            ],
        },
        {
            "id": "S015",
            "name": "语法错误修复策略",
            "description": "修复代码语法错误",
            "patterns": ["SyntaxError", "IndentationError", "TabError"],
            "suggestions": [
                {
                    "title": "修复语法错误",
                    "description": "检查并修复代码语法问题",
                    "category": FixCategory.CODE_FIX,
                    "complexity": FixComplexity.SIMPLE,
                    "risk": FixRisk.LOW,
                    "confidence": FixConfidence.HIGH,
                    "steps": [
                        "定位语法错误位置",
                        "检查括号、引号配对",
                        "修复缩进问题",
                        "验证修复后代码",
                    ],
                    "code_templates": [
                        "# 检查括号配对\n# 检查引号配对\n# 使用一致的缩进（4空格）",
                    ],
                    "estimated_time": "5-15分钟",
                },
            ],
        },
    ]
    
    def __init__(self):
        self.strategies: Dict[str, FixStrategy] = {}
        self._load_strategies()
    
    def _load_strategies(self):
        for s in self.STRATEGIES:
            suggestions = []
            for sug in s["suggestions"]:
                suggestions.append(FixSuggestion(
                    suggestion_id=f"{s['id']}-{len(suggestions)+1:02d}",
                    title=sug["title"],
                    description=sug["description"],
                    category=sug["category"],
                    complexity=sug["complexity"],
                    risk=sug["risk"],
                    confidence=sug["confidence"],
                    steps=sug["steps"],
                    code_templates=sug.get("code_templates", []),
                    estimated_time=sug.get("estimated_time", ""),
                ))
            
            self.strategies[s["id"]] = FixStrategy(
                strategy_id=s["id"],
                name=s["name"],
                description=s["description"],
                applicable_patterns=s["patterns"],
                suggestions=suggestions,
                priority=s.get("priority", 0),
            )
    
    def find_strategies(self, error_pattern: str) -> List[FixStrategy]:
        matching = []
        
        for strategy in self.strategies.values():
            for pattern in strategy.applicable_patterns:
                if pattern.lower() in error_pattern.lower():
                    matching.append(strategy)
                    break
        
        return sorted(matching, key=lambda s: s.priority, reverse=True)
    
    def add_custom_strategy(self, strategy: FixStrategy):
        self.strategies[strategy.strategy_id] = strategy


class FixSuggestionGenerator:
    """修复建议生成器"""
    
    def __init__(self):
        self.strategy_library = FixStrategyLibrary()
        self.suggestion_counter = 0
    
    def generate(self, error_message: str, error_type: str = None,
                 context: Dict[str, Any] = None) -> List[FixSuggestion]:
        suggestions = []
        
        strategies = self.strategy_library.find_strategies(error_message)
        
        for strategy in strategies:
            for suggestion in strategy.suggestions:
                self.suggestion_counter += 1
                
                customized = self._customize_suggestion(suggestion, error_message, context)
                customized.suggestion_id = f"FIX-{self.suggestion_counter:04d}"
                
                suggestions.append(customized)
        
        generic_suggestions = self._generate_generic_suggestions(error_message, error_type)
        suggestions.extend(generic_suggestions)
        
        return self._deduplicate_suggestions(suggestions)
    
    def _customize_suggestion(self, suggestion: FixSuggestion, 
                              error_message: str, context: Dict[str, Any]) -> FixSuggestion:
        customized_steps = []
        for step in suggestion.steps:
            customized_step = step
            if context:
                for key, value in context.items():
                    if isinstance(value, str):
                        customized_step = customized_step.replace(f"{{{key}}}", value)
            customized_steps.append(customized_step)
        
        return FixSuggestion(
            suggestion_id=suggestion.suggestion_id,
            title=suggestion.title,
            description=suggestion.description,
            category=suggestion.category,
            complexity=suggestion.complexity,
            risk=suggestion.risk,
            confidence=suggestion.confidence,
            steps=customized_steps,
            code_templates=suggestion.code_templates,
            prerequisites=suggestion.prerequisites,
            side_effects=suggestion.side_effects,
            estimated_time=suggestion.estimated_time,
            references=suggestion.references,
            tags=suggestion.tags,
        )
    
    def _generate_generic_suggestions(self, error_message: str, 
                                       error_type: str) -> List[FixSuggestion]:
        suggestions = []
        
        self.suggestion_counter += 1
        
        suggestions.append(FixSuggestion(
            suggestion_id=f"FIX-GENERIC-{self.suggestion_counter:04d}",
            title="添加日志记录",
            description="在关键位置添加日志记录以便调试",
            category=FixCategory.CODE_FIX,
            complexity=FixComplexity.SIMPLE,
            risk=FixRisk.LOW,
            confidence=FixConfidence.MEDIUM,
            steps=[
                "在错误发生位置添加try-except",
                "记录详细的错误信息",
                "记录相关的上下文数据",
            ],
            code_templates=[
                "import logging\nlogger = logging.getLogger(__name__)\n\ntry:\n    result = operation()\nexcept Exception as e:\n    logger.error(f'Operation failed: {e}', exc_info=True)\n    raise",
            ],
            estimated_time="10-20分钟",
        ))
        
        suggestions.append(FixSuggestion(
            suggestion_id=f"FIX-GENERIC-{self.suggestion_counter+1:04d}",
            title="添加单元测试",
            description="为相关功能添加单元测试",
            category=FixCategory.CODE_FIX,
            complexity=FixComplexity.MODERATE,
            risk=FixRisk.LOW,
            confidence=FixConfidence.HIGH,
            steps=[
                "识别需要测试的功能",
                "编写测试用例覆盖边界情况",
                "运行测试验证修复",
            ],
            code_templates=[
                "import pytest\n\ndef test_function():\n    # Test normal case\n    assert function(normal_input) == expected_output\n    \n    # Test edge cases\n    assert function(edge_case) == expected_result\n    \n    # Test error handling\n    with pytest.raises(ExpectedException):\n        function(invalid_input)",
            ],
            estimated_time="30-60分钟",
        ))
        
        return suggestions
    
    def _deduplicate_suggestions(self, suggestions: List[FixSuggestion]) -> List[FixSuggestion]:
        seen_titles = set()
        unique = []
        
        for suggestion in suggestions:
            if suggestion.title not in seen_titles:
                seen_titles.add(suggestion.title)
                unique.append(suggestion)
        
        return unique[:10]


class FixEffectEvaluator:
    """修复效果评估器"""
    
    def __init__(self):
        self.evaluation_counter = 0
    
    def evaluate(self, suggestion: FixSuggestion, 
                 context: Dict[str, Any] = None) -> FixEvaluation:
        self.evaluation_counter += 1
        
        effectiveness_score = self._calculate_effectiveness(suggestion)
        risk_score = self._calculate_risk_score(suggestion)
        effort_score = self._calculate_effort_score(suggestion)
        
        overall_score = self._calculate_overall_score(
            effectiveness_score, risk_score, effort_score
        )
        
        pros = self._identify_pros(suggestion)
        cons = self._identify_cons(suggestion)
        recommendation = self._generate_recommendation(suggestion, overall_score)
        alternatives = self._suggest_alternatives(suggestion)
        
        return FixEvaluation(
            evaluation_id=f"EVAL-{self.evaluation_counter:04d}",
            suggestion=suggestion,
            effectiveness_score=effectiveness_score,
            risk_score=risk_score,
            effort_score=effort_score,
            overall_score=overall_score,
            pros=pros,
            cons=cons,
            recommendation=recommendation,
            alternative_suggestions=alternatives,
        )
    
    def _calculate_effectiveness(self, suggestion: FixSuggestion) -> float:
        score = 0.5
        
        confidence_scores = {
            FixConfidence.HIGH: 0.3,
            FixConfidence.MEDIUM: 0.2,
            FixConfidence.LOW: 0.1,
            FixConfidence.EXPERIMENTAL: 0.05,
        }
        score += confidence_scores.get(suggestion.confidence, 0.1)
        
        if suggestion.category == FixCategory.CODE_FIX:
            score += 0.1
        elif suggestion.category == FixCategory.SECURITY_FIX:
            score += 0.15
        
        if len(suggestion.steps) >= 3:
            score += 0.05
        
        return min(1.0, score)
    
    def _calculate_risk_score(self, suggestion: FixSuggestion) -> float:
        risk_scores = {
            FixRisk.LOW: 0.1,
            FixRisk.MEDIUM: 0.3,
            FixRisk.HIGH: 0.6,
            FixRisk.CRITICAL: 0.9,
        }
        return risk_scores.get(suggestion.risk, 0.3)
    
    def _calculate_effort_score(self, suggestion: FixSuggestion) -> float:
        complexity_scores = {
            FixComplexity.SIMPLE: 0.1,
            FixComplexity.MODERATE: 0.3,
            FixComplexity.COMPLEX: 0.6,
            FixComplexity.MAJOR: 0.9,
        }
        return complexity_scores.get(suggestion.complexity, 0.3)
    
    def _calculate_overall_score(self, effectiveness: float, 
                                  risk: float, effort: float) -> float:
        effectiveness_weight = 0.5
        risk_weight = 0.3
        effort_weight = 0.2
        
        score = (
            effectiveness * effectiveness_weight +
            (1 - risk) * risk_weight +
            (1 - effort) * effort_weight
        )
        
        return round(score * 100, 1)
    
    def _identify_pros(self, suggestion: FixSuggestion) -> List[str]:
        pros = []
        
        if suggestion.confidence == FixConfidence.HIGH:
            pros.append("高置信度解决方案")
        
        if suggestion.risk == FixRisk.LOW:
            pros.append("低风险修改")
        
        if suggestion.complexity == FixComplexity.SIMPLE:
            pros.append("实现简单快速")
        
        if suggestion.code_templates:
            pros.append("提供代码模板")
        
        if suggestion.category == FixCategory.SECURITY_FIX:
            pros.append("提升安全性")
        
        return pros
    
    def _identify_cons(self, suggestion: FixSuggestion) -> List[str]:
        cons = []
        
        if suggestion.risk in [FixRisk.HIGH, FixRisk.CRITICAL]:
            cons.append("修改风险较高")
        
        if suggestion.complexity in [FixComplexity.COMPLEX, FixComplexity.MAJOR]:
            cons.append("实现复杂耗时")
        
        if suggestion.confidence in [FixConfidence.LOW, FixConfidence.EXPERIMENTAL]:
            cons.append("解决方案不确定")
        
        if suggestion.side_effects:
            cons.extend(suggestion.side_effects[:2])
        
        return cons
    
    def _generate_recommendation(self, suggestion: FixSuggestion, 
                                  overall_score: float) -> str:
        if overall_score >= 80:
            return "强烈推荐采用此修复方案"
        elif overall_score >= 60:
            return "推荐采用此修复方案"
        elif overall_score >= 40:
            return "可以考虑此修复方案，但需谨慎评估"
        else:
            return "建议寻找其他替代方案"
    
    def _suggest_alternatives(self, suggestion: FixSuggestion) -> List[str]:
        alternatives = []
        
        if suggestion.category == FixCategory.CODE_FIX:
            alternatives.append("考虑使用workaround临时规避问题")
            alternatives.append("评估是否可以通过配置调整解决")
        
        if suggestion.complexity in [FixComplexity.COMPLEX, FixComplexity.MAJOR]:
            alternatives.append("考虑分阶段实施修复")
            alternatives.append("评估是否需要架构层面的调整")
        
        return alternatives[:3]


class AutoFixSuggestionSystem:
    """自动修复建议系统主类"""
    
    def __init__(self):
        self.generator = FixSuggestionGenerator()
        self.evaluator = FixEffectEvaluator()
        self.report_counter = 0
    
    def analyze_and_suggest(self, error_message: str, error_type: str = None,
                            context: Dict[str, Any] = None) -> FixReport:
        self.report_counter += 1
        
        suggestions = self.generator.generate(error_message, error_type, context)
        
        evaluations = []
        for suggestion in suggestions:
            evaluation = self.evaluator.evaluate(suggestion, context)
            evaluations.append(evaluation)
        
        best_suggestion = self._select_best_suggestion(suggestions, evaluations)
        
        summary = self._generate_summary(suggestions, evaluations, best_suggestion)
        
        return FixReport(
            report_id=f"FIX-REPORT-{self.report_counter:04d}",
            generated_at=datetime.now().isoformat(),
            issue_description=error_message,
            suggestions=suggestions,
            evaluations=evaluations,
            best_suggestion=best_suggestion,
            summary=summary,
        )
    
    def _select_best_suggestion(self, suggestions: List[FixSuggestion],
                                 evaluations: List[FixEvaluation]) -> Optional[FixSuggestion]:
        if not evaluations:
            return suggestions[0] if suggestions else None
        
        best_eval = max(evaluations, key=lambda e: e.overall_score)
        return best_eval.suggestion
    
    def _generate_summary(self, suggestions: List[FixSuggestion],
                          evaluations: List[FixEvaluation],
                          best: Optional[FixSuggestion]) -> str:
        parts = [
            f"共生成 {len(suggestions)} 个修复建议",
        ]
        
        if best:
            parts.append(f"推荐方案: {best.title}")
            parts.append(f"复杂度: {best.complexity.value}")
            parts.append(f"风险: {best.risk.value}")
        
        avg_score = sum(e.overall_score for e in evaluations) / len(evaluations) if evaluations else 0
        parts.append(f"平均评分: {avg_score:.1f}")
        
        return " | ".join(parts)
    
    def generate_markdown_report(self, report: FixReport) -> str:
        lines = [
            "# 自动修复建议报告",
            "",
            f"**报告ID**: {report.report_id}",
            f"**生成时间**: {report.generated_at}",
            "",
            "---",
            "",
            "## 📋 问题描述",
            "",
            f"```\n{report.issue_description[:500]}\n```",
            "",
            "---",
            "",
            "## 📊 摘要",
            "",
            report.summary,
            "",
            "---",
            "",
            "## 🎯 推荐方案",
            "",
        ]
        
        if report.best_suggestion:
            best = report.best_suggestion
            lines.extend([
                f"### {best.title}",
                "",
                f"- **类别**: {best.category.value}",
                f"- **复杂度**: {best.complexity.value}",
                f"- **风险**: {best.risk.value}",
                f"- **置信度**: {best.confidence.value}",
                f"- **预估时间**: {best.estimated_time}",
                "",
                f"**描述**: {best.description}",
                "",
                "**修复步骤**:",
                "",
            ])
            
            for i, step in enumerate(best.steps, 1):
                lines.append(f"{i}. {step}")
            
            if best.code_templates:
                lines.extend([
                    "",
                    "**代码模板**:",
                    "",
                ])
                for template in best.code_templates:
                    lines.extend([
                        "```python",
                        template,
                        "```",
                        "",
                    ])
        
        lines.extend([
            "---",
            "",
            "## 📝 所有修复建议",
            "",
        ])
        
        for i, (suggestion, evaluation) in enumerate(zip(report.suggestions, report.evaluations), 1):
            emoji = "🟢" if evaluation.overall_score >= 60 else "🟡" if evaluation.overall_score >= 40 else "🔴"
            
            lines.extend([
                f"### {emoji} 方案 {i}: {suggestion.title}",
                "",
                f"- **评分**: {evaluation.overall_score}",
                f"- **类别**: {suggestion.category.value}",
                f"- **复杂度**: {suggestion.complexity.value}",
                f"- **风险**: {suggestion.risk.value}",
                "",
                f"**描述**: {suggestion.description}",
                "",
            ])
            
            if evaluation.pros:
                lines.append("**优点**:")
                for pro in evaluation.pros:
                    lines.append(f"- ✅ {pro}")
                lines.append("")
            
            if evaluation.cons:
                lines.append("**缺点**:")
                for con in evaluation.cons:
                    lines.append(f"- ⚠️ {con}")
                lines.append("")
            
            lines.append(f"**建议**: {evaluation.recommendation}")
            lines.append("")
        
        return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="自动修复建议系统")
    parser.add_argument("--error", required=True, help="错误消息")
    parser.add_argument("--type", help="错误类型")
    parser.add_argument("--output", help="报告输出路径")
    
    args = parser.parse_args()
    
    system = AutoFixSuggestionSystem()
    report = system.analyze_and_suggest(args.error, args.type)
    
    print("\n" + "=" * 60)
    print("自动修复建议报告")
    print("=" * 60)
    print(f"报告ID: {report.report_id}")
    print(f"问题: {report.issue_description[:100]}...")
    print(f"\n{report.summary}")
    
    if report.best_suggestion:
        print(f"\n推荐方案: {report.best_suggestion.title}")
        print(f"复杂度: {report.best_suggestion.complexity.value}")
        print(f"风险: {report.best_suggestion.risk.value}")
    
    print("=" * 60)
    
    md_report = system.generate_markdown_report(report)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(md_report, encoding='utf-8')
        print(f"\n报告已保存: {output_path}")
    else:
        print("\n" + md_report)


if __name__ == "__main__":
    main()
