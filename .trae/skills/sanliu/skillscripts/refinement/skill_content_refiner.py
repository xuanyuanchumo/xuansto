"""
技能内容完善器 (Phase 9.2)

核心功能:
1. 内容缺失检测 - 识别文档和代码中的内容缺失
2. 不一致性检测 - 发现内容和代码间的不一致
3. 完善建议生成 - 基于检测问题生成改进建议
4. 安全自动更新 - 应用安全的自动完善操作

增强特性:
- 多维度内容分析
- 智能差距分析
- 基于模式的建议生成
- 风险评估机制
- 变更追踪系统
"""

import os
import re
import json
import ast
import sys
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class ContentType(Enum):
    CODE = "code"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    TEST = "test"
    EXAMPLE = "example"
    UNKNOWN = "unknown"


class IssueType(Enum):
    MISSING_CONTENT = "missing_content"
    INCONSISTENCY = "inconsistency"
    OUTDATED_INFO = "outdated_info"
    POOR_QUALITY = "poor_quality"
    DUPLICATION = "duplication"
    SECURITY_ISSUE = "security_issue"


class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ContentIssue:
    """内容问题"""
    issue_id: str
    issue_type: IssueType
    severity: IssueSeverity
    content_type: ContentType
    location: str
    description: str
    suggestion: str
    auto_fixable: bool
    risk_level: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'issue_id': self.issue_id,
            'issue_type': self.issue_type.value,
            'severity': self.severity.value,
            'content_type': self.content_type.value,
            'location': self.location,
            'description': self.description,
            'suggestion': self.suggestion,
            'auto_fixable': self.auto_fixable,
            'risk_level': self.risk_level,
            'metadata': self.metadata
        }


@dataclass
class RefinementSuggestion:
    """完善建议"""
    suggestion_id: str
    target_content: str
    action_type: str
    priority: int
    description: str
    implementation_details: Dict[str, Any]
    expected_benefit: str
    effort_estimate: str
    prerequisites: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'suggestion_id': self.suggestion_id,
            'target_content': self.target_content,
            'action_type': self.action_type,
            'priority': self.priority,
            'description': self.description,
            'implementation_details': self.implementation_details,
            'expected_benefit': self.expected_benefit,
            'effort_estimate': self.effort_estimate,
            'prerequisites': self.prerequisites
        }


@dataclass
class ContentAnalysisResult:
    """内容分析结果"""
    analysis_id: str
    analyzed_at: str
    files_analyzed: int
    issues_found: List[ContentIssue]
    statistics: Dict[str, Any]
    health_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'analysis_id': self.analysis_id,
            'analyzed_at': self.analyzed_at,
            'files_analyzed': self.files_analyzed,
            'issues_found': [i.to_dict() for i in self.issues_found],
            'statistics': self.statistics,
            'health_score': self.health_score
        }


@dataclass
class RefinementReport:
    """完善报告"""
    report_id: str
    generated_at: str
    analysis_result: ContentAnalysisResult
    suggestions: List[RefinementSuggestion]
    applied_changes: List[Dict[str, Any]]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            'generated_at': self.generated_at,
            'analysis_result': self.analysis_result.to_dict(),
            'suggestions': [s.to_dict() for s in self.suggestions],
            'applied_changes': self.applied_changes,
            'summary': self.summary
        }


class ContentGapDetector:
    """内容缺口检测器"""
    
    REQUIRED_PATTERNS = {
        ContentType.CODE: {
            'docstrings': r'""".*?"""',
            'type_hints': r':\s*(str|int|float|bool|list|dict|Any|Optional|Union)',
            'error_handling': r'(try|except|raise)\b',
            'logging': r'(logger|logging)\.',
            'comments': r'#\s*[A-Z]'
        },
        ContentType.DOCUMENTATION: {
            'title': r'^#\s+.+$',
            'description': r'(?:(?:简介|描述|概述|description|overview))',
            'usage_example': r'(?:示例|example|usage)',
            'parameters': r'(?:参数|parameter|argument)',
            'return_value': r'(?:返回值|return|返回)'
        },
        ContentType.TEST: {
            'test_function': r'def\s+test_',
            'assertions': r'\bassert\b',
            'setup_teardown': r'(setUp|tearDown|@pytest\.fixture)',
            'test_description': r'def\s+test_\w+\([^)]*\):\s*\n\s*"""'
        }
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._detection_cache: Dict[str, List[ContentIssue]] = {}
        self._logger = self._setup_logger()
        
        self._min_confidence = self._config.get('min_confidence', 0.6)
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('ContentGapDetector')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def detect_gaps(
        self,
        project_path: Path,
        file_patterns: Optional[List[str]] = None,
        content_types: Optional[List[ContentType]] = None
    ) -> ContentAnalysisResult:
        """检测内容缺口"""
        analysis_id = f"GAP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        all_issues = []
        files_count = 0
        
        patterns_to_check = file_patterns or ['**/*.py', '**/*.md', '**/*.ts']
        types_to_check = content_types or list(ContentType)
        
        for pattern in patterns_to_check:
            try:
                for file_path in project_path.glob(pattern):
                    if not file_path.is_file():
                        continue
                    
                    if '__pycache__' in str(file_path) or 'node_modules' in str(file_path):
                        continue
                    
                    content_type = self._detect_file_type(file_path)
                    
                    if content_type not in types_to_check:
                        continue
                    
                    file_issues = self._analyze_file_for_gaps(file_path, content_type)
                    all_issues.extend(file_issues)
                    files_count += 1
                    
            except Exception as e:
                self._logger.debug(f"无法处理文件模式 {pattern}: {e}")
        
        deduplicated_issues = self._deduplicate_issues(all_issues)
        
        statistics = self._generate_statistics(deduplicated_issues, files_count)
        health_score = self._calculate_health_score(statistics)
        
        result = ContentAnalysisResult(
            analysis_id=analysis_id,
            analyzed_at=datetime.now().isoformat(),
            files_analyzed=files_count,
            issues_found=deduplicated_issues,
            statistics=statistics,
            health_score=health_score
        )
        
        self._detection_cache[analysis_id] = deduplicated_issues
        self._logger.info(f"缺口检测完成: 分析了 {files_count} 个文件, 发现 {len(deduplicated_issues)} 个问题")
        
        return result
    
    def _detect_file_type(self, file_path: Path) -> ContentType:
        """检测文件类型"""
        suffix_map = {
            '.py': ContentType.CODE,
            '.ts': ContentType.CODE,
            '.js': ContentType.CODE,
            '.md': ContentType.DOCUMENTATION,
            '.rst': ContentType.DOCUMENTATION,
            '.json': ContentType.CONFIGURATION,
            '.yaml': ContentType.CONFIGURATION,
            '.yml': ContentType.CONFIGURATION,
        }
        
        return suffix_map.get(file_path.suffix.lower(), ContentType.UNKNOWN)
    
    def _analyze_file_for_gaps(
        self,
        file_path: Path,
        content_type: ContentType
    ) -> List[ContentIssue]:
        """分析文件的内容缺口"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception:
            return issues
        
        location = str(file_path.relative_to(file_path.anchor))
        
        if content_type == ContentType.CODE and file_path.suffix == '.py':
            code_issues = self._analyze_code_gaps(file_path, content, lines)
            issues.extend(code_issues)
        
        elif content_type == ContentType.DOCUMENTATION:
            doc_issues = self._analyze_documentation_gaps(file_path, content, lines)
            issues.extend(doc_issues)
        
        elif content_type == ContentType.TEST or (content_type == ContentType.CODE and 'test_' in file_path.name):
            test_issues = self._analyze_test_gaps(file_path, content, lines)
            issues.extend(test_issues)
        
        general_issues = self._detect_general_quality_issues(content, lines, location)
        issues.extend(general_issues)
        
        return issues
    
    def _analyze_code_gaps(
        self,
        file_path: Path,
        content: str,
        lines: List[str]
    ) -> List[ContentIssue]:
        """分析代码文件的内容缺口"""
        issues = []
        location = str(file_path)
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_issues = self._check_function_completeness(node, file_path, lines)
                    issues.extend(func_issues)
                
                elif isinstance(node, ast.ClassDef):
                    class_issues = self._check_class_completeness(node, file_path, lines)
                    issues.extend(class_issues)
                    
        except SyntaxError:
            pass
        
        module_docstring = ast.get_docstring(ast.parse(content)) if content else None
        if not module_docstring:
            issues.append(ContentIssue(
                issue_id=f"MISS-{hashlib.md5(str(file_path).encode()).hexdigest()[:8]}",
                issue_type=IssueType.MISSING_CONTENT,
                severity=IssueSeverity.MEDIUM,
                content_type=ContentType.CODE,
                location=f"{location}:module",
                description="模块缺少文档字符串",
                suggestion="添加模块级别的文档字符串，说明模块的用途和主要功能",
                auto_fixable=True,
                risk_level='low',
                metadata={'pattern': 'module_docstring'}
            ))
        
        return issues
    
    def _check_function_completeness(
        self,
        node: ast.FunctionDef,
        file_path: Path,
        lines: List[str]
    ) -> List[ContentIssue]:
        """检查函数完整性"""
        issues = []
        func_location = f"{file_path}:{node.lineno}"
        
        docstring = ast.get_docstring(node)
        if not docstring:
            issues.append(ContentIssue(
                issue_id=f"MISS-{hashlib.md5(f'{func_location}-doc'.encode()).hexdigest()[:8]}",
                issue_type=IssueType.MISSING_CONTENT,
                severity=IssueSeverity.HIGH if len(node.args.args) > 2 else IssueSeverity.MEDIUM,
                content_type=ContentType.CODE,
                location=func_location,
                description=f"函数 '{node.name}' 缺少文档字符串",
                suggestion="添加文档字符串，说明函数的功能、参数、返回值和可能的异常",
                auto_fixable=True,
                risk_level='low',
                metadata={'function_name': node.name, 'arg_count': len(node.args.args)}
            ))
        
        has_return_annotation = hasattr(node, 'returns') and node.returns is not None
        args_without_type = [
            arg.arg 
            for arg in node.args.args 
            if arg.annotation is None and arg.arg != 'self'
        ]
        
        if args_without_type and len(args_without_type) > 0:
            issues.append(ContentIssue(
                issue_id=f"TYPE-{hashlib.md5(f'{func_location}-type'.encode()).hexdigest()[:8]}",
                issue_type=IssueType.MISSING_CONTENT,
                severity=IssueSeverity.LOW,
                content_type=ContentType.CODE,
                location=func_location,
                description=f"函数 '{node.name}' 的 {len(args_without_type)} 个参数缺少类型注解",
                suggestion="为所有参数添加类型注解以提高代码可读性和IDE支持",
                auto_fixable=True,
                risk_level='low',
                metadata={
                    'function_name': node.name,
                    'untyped_args': args_without_type
                }
            ))
        
        has_try_except = any(isinstance(child, ast.Try) for child in ast.walk(node))
        if not has_try_except and any(isinstance(child, ast.Call) for child in ast.walk(node)):
            may_fail = any(
                isinstance(child, ast.Attribute) and child.attr in ('open', 'connect', 'execute', 'request')
                for child in ast.walk(node)
            )
            if may_fail:
                issues.append(ContentIssue(
                    issue_id=f"ERR-{hashlib.md5(f'{func_location}-err'.encode()).hexdigest()[:8]}",
                    issue_type=IssueType.MISSING_CONTENT,
                    severity=IssueSeverity.MEDIUM,
                    content_type=ContentType.CODE,
                    location=func_location,
                    description=f"函数 '{node.name}' 可能执行失败的操作但缺少错误处理",
                    suggestion="添加 try-except 块来处理可能出现的异常",
                    auto_fixable=False,
                    risk_level='medium',
                    metadata={'function_name': node.name}
                ))
        
        return issues
    
    def _check_class_completeness(
        self,
        node: ast.ClassDef,
        file_path: Path,
        lines: List[str]
    ) -> List[ContentIssue]:
        """检查类完整性"""
        issues = []
        class_location = f"{file_path}:{node.lineno}"
        
        docstring = ast.get_docstring(node)
        if not docstring:
            issues.append(ContentIssue(
                issue_id=f"MISS-{hashlib.md5(f'{class_location}-doc'.encode()).hexdigest()[:8]}",
                issue_type=IssueType.MISSING_CONTENT,
                severity=IssueSeverity.HIGH,
                content_type=ContentType.CODE,
                location=class_location,
                description=f"类 '{node.name}' 缺少类文档字符串",
                suggestion="添加类文档字符串，描述类的用途、属性和使用方法",
                auto_fixable=True,
                risk_level='low',
                metadata={'class_name': node.name}
            ))
        
        method_names = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        
        if '__init__' not in method_names and any(not n.name.startswith('_') for n in node.body if isinstance(n, ast.FunctionDef)):
            issues.append(ContentIssue(
                issue_id=f"INIT-{hashlib.md5(f'{class_location}-init'.encode()).hexdigest()[:8]}",
                issue_type=IssueType.MISSING_CONTENT,
                severity=IssueSeverity.MEDIUM,
                content_type=ContentType.CODE,
                location=class_location,
                description=f"类 '{node.name}' 缺少 __init__ 方法",
                suggestion="添加 __init__ 方法来初始化实例属性",
                auto_fixable=True,
                risk_level='low',
                metadata={'class_name': node.name}
            ))
        
        if '__str__' not in method_names and '__repr__' not in method_names:
            issues.append(ContentIssue(
                issue_id=f"STR-{hashlib.md5(f'{class_location}-str'.encode()).hexdigest()[:8]}",
                issue_type=IssueType.MISSING_CONTENT,
                severity=IssueSeverity.LOW,
                content_type=ContentType.CODE,
                location=class_location,
                description=f"类 '{node.name}' 缺少 __str__ 或 __repr__ 方法",
                suggestion="实现 __str__ 或 __repr__ 方法以提供有意义的对象表示",
                auto_fixable=True,
                risk_level='low',
                metadata={'class_name': node.name}
            ))
        
        return issues
    
    def _analyze_documentation_gaps(
        self,
        file_path: Path,
        content: str,
        lines: List[str]
    ) -> List[ContentIssue]:
        """分析文档文件的缺口"""
        issues = []
        location = str(file_path)
        
        has_title = bool(re.search(r'^#\s+.+', content, re.MULTILINE))
        if not has_title:
            issues.append(ContentIssue(
                issue_id=f"TITLE-{hashlib.md5(str(file_path).encode()).hexdigest()[:8]}",
                issue_type=IssueType.MISSING_CONTENT,
                severity=IssueSeverity.CRITICAL,
                content_type=ContentType.DOCUMENTATION,
                location=location,
                description="文档缺少标题",
                suggestion="在文档开头添加一个清晰的标题（使用 # 标记）",
                auto_fixable=True,
                risk_level='low'
            ))
        
        sections = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        
        if len(sections) < 2:
            issues.append(ContentIssue(
                issue_id=f"SEC-{hashlib.md5(f'{location}-sec'.encode()).hexdigest()[:8]}",
                issue_type=IssueType.MISSING_CONTENT,
                severity=IssueSeverity.HIGH,
                content_type=ContentType.DOCUMENTATION,
                location=location,
                description="文档结构过于简单，缺少足够的章节",
                suggestion="将文档组织成多个逻辑章节，如概述、安装、使用、API参考等",
                auto_fixable=False,
                risk_level='low'
            ))
        
        has_code_examples = bool(re.search(r'```(?:python|javascript|bash)', content))
        if not has_code_examples and len(lines) > 50:
            issues.append(ContentIssue(
                issue_id=f"EX-{hashlib.md5(f'{location}-ex'.encode()).hexdigest()[:8]}",
                issue_type=IssueType.MISSING_CONTENT,
                severity=IssueSeverity.MEDIUM,
                content_type=ContentType.DOCUMENTATION,
                location=location,
                description="文档缺少代码示例",
                suggestion="添加实际的代码示例来说明如何使用文档中描述的功能",
                auto_fixable=False,
                risk_level='low'
            ))
        
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        broken_links = []
        for link_text, link_url in links:
            if link_url.startswith('#'):
                anchor_target = link_url[1:]
                if anchor_target and not any(anchor_target in s.lower().replace(' ', '-') for s in sections):
                    broken_links.append(link_url)
        
        if broken_links:
            issues.append(ContentIssue(
                issue_id=f"LINK-{hashlib.md5(f'{location}-link'.encode()).hexdigest()[:8]}",
                issue_type=IssueType.INCONSISTENCY,
                severity=IssueSeverity.MEDIUM,
                content_type=ContentType.DOCUMENTATION,
                location=location,
                description=f"发现 {len(broken_links)} 个断开的内部链接",
                suggestion="修复或移除指向不存在锚点的内部链接",
                auto_fixable=False,
                risk_level='low',
                metadata={'broken_links': broken_links}
            ))
        
        return issues
    
    def _analyze_test_gaps(
        self,
        file_path: Path,
        content: str,
        lines: List[str]
    ) -> List[ContentIssue]:
        """分析测试文件的缺口"""
        issues = []
        location = str(file_path)
        
        test_functions = re.findall(r'def\s+(test_\w+)\s*\(', content)
        
        if not test_functions:
            return issues
        
        for test_func in test_functions:
            func_match = re.search(
                rf'def\s+{re.escape(test_func)}\s*\([^)]*\):.*?(?=\ndef\s|\Z)',
                content,
                re.DOTALL
            )
            
            if func_match:
                func_body = func_match.group(0)
                
                if '"""' not in func_body and "'''" not in func_body:
                    issues.append(ContentIssue(
                        issue_id=f"TDOC-{hashlib.md5(f'{location}-{test_func}'.encode()).hexdigest()[:8]}",
                        issue_type=IssueType.MISSING_CONTENT,
                        severity=IssueSeverity.LOW,
                        content_type=ContentType.TEST,
                        location=f"{location}:{test_func}",
                        description=f"测试函数 '{test_func}' 缺少文档说明",
                        suggestion="添加简短的文档字符串说明测试的目的",
                        auto_fixable=True,
                        risk_level='low',
                        metadata={'test_function': test_func}
                    ))
                
                assert_count = len(re.findall(r'\bassert\b', func_body))
                if assert_count == 0:
                    issues.append(ContentIssue(
                        issue_id=f"TASSERT-{hashlib.md5(f'{location}-{test_func}'.encode()).hexdigest()[:8]}",
                        issue_type=IssueType.MISSING_CONTENT,
                        severity=IssueSeverity.HIGH,
                        content_type=ContentType.TEST,
                        location=f"{location}:{test_func}",
                        description=f"测试函数 '{test_func}' 缺少断言语句",
                        suggestion="添加适当的断言来验证预期行为",
                        auto_fixable=False,
                        risk_level='low',
                        metadata={'test_function': test_func}
                    ))
        
        return issues
    
    def _detect_general_quality_issues(
        self,
        content: str,
        lines: List[str],
        location: str
    ) -> List[ContentIssue]:
        """检测通用质量问题"""
        issues = []
        
        very_long_lines = [(i + 1, line) for i, line in enumerate(lines) if len(line) > 150]
        if len(very_long_lines) > len(lines) * 0.05:
            issues.append(ContentIssue(
                issue_id=f"LONG-{hashlib.md5(location.encode()).hexdigest()[:8]}",
                issue_type=IssueType.POOR_QUALITY,
                severity=IssueSeverity.LOW,
                content_type=self._detect_file_type(Path(location)),
                location=location,
                description=f"发现 {len(very_long_lines)} 行超过150字符的长行",
                suggestion="将长行拆分为多行以提高可读性",
                auto_fixable=True,
                risk_level='low',
                metadata={'long_line_count': len(very_long_lines)}
            ))
        
        todo_comments = [line for line in lines if re.match(r'^\s*#?\s*(TODO|FIXME|HACK|XXX)\b', line, re.IGNORECASE)]
        if todo_comments:
            issues.append(ContentIssue(
                issue_id=f"TODO-{hashlib.md5(location.encode()).hexdigest()[:8]}",
                issue_type=IssueType.POOR_QUALITY,
                severity=IssueSeverity.INFO,
                content_type=self._detect_file_type(Path(location)),
                location=location,
                description=f"发现 {len(todo_comments)} 个待办事项注释",
                suggestion="审查并处理标记为 TODO/FIXME 的项目",
                auto_fixable=False,
                risk_level='none',
                metadata={'todo_items': todo_comments}
            ))
        
        return issues
    
    def _deduplicate_issues(self, issues: List[ContentIssue]) -> List[ContentIssue]:
        """去重问题"""
        seen_keys = set()
        unique_issues = []
        
        for issue in issues:
            key = (issue.issue_type, issue.location, issue.description[:50])
            if key not in seen_keys:
                seen_keys.add(key)
                unique_issues.append(issue)
        
        return unique_issues
    
    def _generate_statistics(self, issues: List[ContentIssue], files_count: int) -> Dict[str, Any]:
        """生成统计信息"""
        type_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        content_type_counts = defaultdict(int)
        auto_fixable_count = sum(1 for i in issues if i.auto_fixable)
        
        for issue in issues:
            type_counts[issue.issue_type.value] += 1
            severity_counts[issue.severity.value] += 1
            content_type_counts[issue.content_type.value] += 1
        
        return {
            'total_issues': len(issues),
            'files_analyzed': files_count,
            'average_issues_per_file': round(len(issues) / max(files_count, 1), 2),
            'by_type': dict(type_counts),
            'by_severity': dict(severity_counts),
            'by_content_type': dict(content_type_counts),
            'auto_fixable_count': auto_fixable_count,
            'auto_fixable_percentage': round(auto_fixable_count / max(len(issues), 1) * 100, 1)
        }
    
    def _calculate_health_score(self, stats: Dict[str, Any]) -> float:
        """计算健康分数"""
        total_issues = stats.get('total_issues', 0)
        critical_count = stats.get('by_severity', {}).get('critical', 0)
        high_count = stats.get('by_severity', {}).get('high', 0)
        
        base_score = 100.0
        
        base_score -= critical_count * 15
        base_score -= high_count * 8
        base_score -= total_issues * 0.5
        
        auto_fix_bonus = stats.get('auto_fixable_percentage', 0) * 0.1
        base_score += auto_fix_bonus
        
        return round(max(min(base_score, 100), 0), 1)


class InconsistencyDetector:
    """不一致性检测器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('InconsistencyDetector')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def detect_inconsistencies(
        self,
        project_path: Path,
        code_files: Optional[List[Path]] = None,
        doc_files: Optional[List[Path]] = None
    ) -> List[ContentIssue]:
        """检测不一致性"""
        inconsistencies = []
        
        if code_files is None:
            code_files = list(project_path.rglob("*.py"))
        
        if doc_files is None:
            doc_files = list(project_path.rglob("*.md"))
        
        code_functions = self._extract_code_api(code_files)
        doc_references = self._extract_documentation_refs(doc_files)
        
        api_inconsistencies = self._compare_code_and_docs(code_functions, doc_references, project_path)
        inconsistencies.extend(api_inconsistencies)
        
        naming_inconsistencies = self._detect_naming_inconsistencies(code_files)
        inconsistencies.extend(naming_inconsistencies)
        
        style_inconsistencies = self._detect_style_inconsistencies(code_files)
        inconsistencies.extend(style_inconsistencies)
        
        self._logger.info(f"不一致性检测完成: 发现 {len(inconsistencies)} 个问题")
        
        return inconsistencies
    
    def _extract_code_api(self, code_files: List[Path]) -> Dict[str, Dict[str, Any]]:
        """提取代码中的API定义"""
        api_definitions = {}
        
        for file_path in code_files:
            if not file_path.exists() or '__pycache__' in str(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        key = f"{node.name}"
                        
                        params = []
                        for arg in node.args.args:
                            param_info = {'name': arg.arg}
                            if arg.annotation:
                                param_info['type'] = ast.unparse(arg.annotation)
                            params.append(param_info)
                        
                        returns = ""
                        if node.returns:
                            returns = ast.unparse(node.returns)
                        
                        docstring = ast.get_docstring(node)
                        
                        api_definitions[key] = {
                            'file': str(file_path),
                            'line': node.lineno,
                            'params': params,
                            'returns': returns,
                            'has_docstring': bool(docstring),
                            'docstring_preview': (docstring[:100] + '...') if docstring and len(docstring) > 100 else docstring
                        }
                        
            except Exception:
                continue
        
        return api_definitions
    
    def _extract_documentation_refs(self, doc_files: List[Path]) -> Dict[str, List[Dict[str, Any]]]:
        """提取文档中的引用"""
        references = defaultdict(list)
        
        for doc_file in doc_files:
            if not doc_file.exists():
                continue
            
            try:
                with open(doc_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                code_block_pattern = r'```(\w*)\n([\s\S]*?)```'
                for match in re.finditer(code_block_pattern, content):
                    lang = match.group(1)
                    code = match.group(2)
                    
                    function_calls = re.findall(r'(\w+)\s*\(', code)
                    for func_name in function_calls:
                        references[func_name].append({
                            'source': str(doc_file),
                            'language': lang,
                            'context': code[:200]
                        })
                        
            except Exception:
                continue
        
        return dict(references)
    
    def _compare_code_and_docs(
        self,
        code_api: Dict[str, Dict[str, Any]],
        doc_refs: Dict[str, List[Dict[str, Any]]],
        project_path: Path
    ) -> List[ContentIssue]:
        """比较代码和文档"""
        issues = []
        
        documented_funcs = set(doc_refs.keys())
        defined_funcs = set(code_api.keys())
        
        undocumented_public = defined_funcs - documented_funcs
        for func_name in sorted(undocumented_public)[:10]:
            if not func_name.startswith('_'):
                func_info = code_api[func_name]
                issues.append(ContentIssue(
                    issue_id=f"UNDOC-{hashlib.md5(func_name.encode()).hexdigest()[:8]}",
                    issue_type=IssueType.INCONSISTENCY,
                    severity=IssueSeverity.MEDIUM,
                    content_type=ContentType.DOCUMENTATION,
                    location=func_info['file'],
                    description=f"公共函数/方法 '{func_name}' 在代码中定义但未在文档中使用或提及",
                    suggestion="考虑在用户指南或API文档中记录此函数",
                    auto_fixable=False,
                    risk_level='low',
                    metadata={'function': func_name, 'defined_at': f"{func_info['file']}:{func_info['line']}"}
                ))
        
        referenced_but_missing = documented_funcs - defined_funcs
        for func_name in sorted(referenced_but_missing)[:10]:
            ref_info = doc_refs[func_name][0]
            issues.append(ContentIssue(
                issue_id=f"MISSFUNC-{hashlib.md5(func_name.encode()).hexdigest()[:8]}",
                issue_type=IssueType.INCONSISTENCY,
                severity=IssueSeverity.HIGH,
                content_type=ContentType.DOCUMENTATION,
                location=ref_info['source'],
                description=f"文档引用了函数 '{func_name}' 但该函数在代码中未找到",
                suggestion="验证函数名是否正确，或者如果函数已被重命名/删除，请更新文档",
                auto_fixable=False,
                risk_level='medium',
                metadata={'referenced_function': func_name, 'reference_source': ref_info['source']}
            ))
        
        return issues
    
    def _detect_naming_inconsistencies(self, code_files: List[Path]) -> List[ContentIssue]:
        """检测命名不一致性"""
        issues = []
        naming_conventions = defaultdict(list)
        
        for file_path in code_files:
            if not file_path.exists() or '__pycache__' in str(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        name = node.name
                        if name.startswith('_') and not name.startswith('__'):
                            naming_conventions['private_function'].append({
                                'name': name,
                                'file': str(file_path),
                                'line': node.lineno
                            })
                        elif re.match(r'^[a-z][a-z0-9_]*$', name):
                            naming_conventions['snake_case'].append(name)
                        elif re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
                            naming_conventions['PascalCase'].append(name)
                            
            except Exception:
                continue
        
        snake_case_count = len(naming_conventions.get('snake_case', []))
        pascal_case_count = len(naming_conventions.get('PascalCase', []))
        
        total_named = snake_case_count + pascal_case_count
        if total_named > 10:
            snake_ratio = snake_case_count / total_named
            pascal_ratio = pascal_case_count / total_named
            
            if 0.1 < snake_ratio < 0.9 and 0.1 < pascal_ratio < 0.9:
                sample_snake = naming_conventions['snake_case'][:3]
                sample_pascal = naming_conventions['PascalCase'][:3]
                
                issues.append(ContentIssue(
                    issue_id=f"NAMING-{hashlib.md5(str(code_files[0]).encode()).hexdigest()[:8]}",
                    issue_type=IssueType.INCONSISTENCY,
                    severity=IssueSeverity.LOW,
                    content_type=ContentType.CODE,
                    location=str(code_files[0].parent),
                    description=f"项目中混合使用了命名风格 (snake_case: {snake_count}, PascalCase: {pascal_count})",
                    suggestion="统一采用一种命名约定（推荐Python使用snake_case）",
                    auto_fixable=False,
                    risk_level='medium',
                    metadata={
                        'snake_case_samples': sample_snake,
                        'pascal_case_samples': sample_pascal,
                        'ratios': {'snake_case': round(snake_ratio, 2), 'PascalCase': round(pascal_ratio, 2)}
                    }
                ))
        
        return issues
    
    def _detect_style_inconsistencies(self, code_files: List[Path]) -> List[ContentIssue]:
        """检测风格不一致性"""
        issues = []
        quote_styles = defaultdict(int)
        indent_styles = defaultdict(int)
        
        for file_path in code_files[:20]:
            if not file_path.exists():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        single_quotes = line.count("'") - line.count("'") // 2 if "'" in line else 0
                        double_quotes = line.count('"') - line.count('"') // 2 if '"' in line else 0
                        
                        if single_quotes > 0:
                            quote_styles['single'] += single_quotes
                        if double_quotes > 0:
                            quote_styles['double'] += double_quotes
                        
                        if line.startswith('    '):
                            indent_styles['4_spaces'] += 1
                        elif line.startswith('\t'):
                            indent_styles['tab'] += 1
                        elif line.startswith('  ') and not line.startswith('    '):
                            indent_styles['2_spaces'] += 1
                            
            except Exception:
                continue
        
        if quote_styles.get('single', 0) > 10 and quote_styles.get('double', 0) > 10:
            total_quotes = quote_styles['single'] + quote_styles['double']
            single_ratio = quote_styles['single'] / total_quotes
            
            if 0.2 < single_ratio < 0.8:
                issues.append(ContentIssue(
                    issue_id=f"QUOTE-{hashlib.md5(str(code_files[0]).encode()).hexdigest()[:8]}",
                    issue_type=IssueType.INCONSISTENCY,
                    severity=IssueSeverity.INFO,
                    content_type=ContentType.CODE,
                    location=str(code_files[0].parent),
                    description="项目中混合使用单引号和双引号",
                    suggestion="统一引号风格（PEP 8 推荐使用单引号，但保持一致即可）",
                    auto_fixable=True,
                    risk_level='low',
                    metadata={'single_quote_pct': round(single_ratio * 100, 1)}
                ))
        
        return issues


class SuggestionGenerator:
    """完善建议生成器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._logger = self._setup_logger()
        
        self._suggestion_templates = self._load_suggestion_templates()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SuggestionGenerator')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _load_suggestion_templates(self) -> Dict[str, Any]:
        """加载建议模板"""
        return {
            IssueType.MISSING_CONTENT: {
                'add_docstring': {
                    'template': '''"""
{function_summary}

Args:
{params_doc}

Returns:
{return_doc}

Raises:
{exceptions_doc}
"""''',
                    'applicable_to': ['function', 'method', 'class', 'module'],
                    'effort': '1-5分钟',
                    'benefit': '提升代码可读性和可维护性'
                },
                'add_type_hints': {
                    'template': None,
                    'applicable_to': ['function', 'method'],
                    'effort': '2-10分钟',
                    'benefit': '增强IDE支持和代码自文档化'
                },
                'add_error_handling': {
                    'template': '''try:
    {existing_code}
except {exception_type} as e:
    logger.error(f"Error in {function_name}: {{e}}")
    raise''',
                    'applicable_to': ['function'],
                    'effort': '5-15分钟',
                    'benefit': '提高代码健壮性'
                },
                'add_tests': {
                    'template': '''def test_{test_name}(self):
    """
    {test_description}
    """
    # Arrange
    {setup_code}
    
    # Act
    result = {function_call}
    
    # Assert
    {assertions}''',
                    'applicable_to': ['function'],
                    'effort': '10-30分钟',
                    'benefit': '确保功能正确性并防止回归'
                }
            },
            IssueType.INCONSISTENCY: {
                'fix_reference': {
                    'template': None,
                    'applicable_to': ['documentation'],
                    'effort': '2-5分钟',
                    'benefit': '消除误导信息'
                },
                'standardize_naming': {
                    'template': None,
                    'applicable_to': ['code'],
                    'effort': '5-30分钟',
                    'benefit': '提高代码一致性和可读性'
                }
            }
        }
    
    def generate_suggestions(
        self,
        issues: List[ContentIssue],
        context: Dict[str, Any] = None
    ) -> List[RefinementSuggestion]:
        """生成完善建议"""
        suggestions = []
        
        grouped_issues = self._group_issues_by_type(issues)
        
        for issue_type, issue_list in grouped_issues.items():
            type_suggestions = self._generate_suggestions_for_type(issue_type, issue_list, context)
            suggestions.extend(type_suggestions)
        
        prioritized = self._prioritize_suggestions(suggestions)
        
        self._logger.info(f"生成了 {len(prioritized)} 条完善建议")
        
        return prioritized
    
    def _group_issues_by_type(self, issues: List[ContentIssue]) -> Dict[IssueType, List[ContentIssue]]:
        """按类型分组问题"""
        grouped = defaultdict(list)
        for issue in issues:
            grouped[issue.issue_type].append(issue)
        return dict(grouped)
    
    def _generate_suggestions_for_type(
        self,
        issue_type: IssueType,
        issues: List[ContentIssue],
        context: Dict[str, Any] = None
    ) -> List[RefinementSuggestion]:
        """为特定类型的问题生成建议"""
        suggestions = []
        
        templates = self._suggestion_templates.get(issue_type, {})
        
        for issue in issues:
            best_template_key = self._find_best_template(issue, templates)
            
            if best_template_key:
                template_data = templates[best_template_key]
                
                suggestion = RefinementSuggestion(
                    suggestion_id=f"SUG-{hashlib.md5(f'{issue.issue_id}-{best_template_key}'.encode()).hexdigest()[:8]}",
                    target_content=issue.location,
                    action_type=best_template_key,
                    priority=self._calculate_priority(issue),
                    description=issue.suggestion or template_data.get('benefit', ''),
                    implementation_details={
                        'issue': issue.to_dict(),
                        'template': template_data.get('template'),
                        'steps': self._generate_implementation_steps(best_template_key, issue)
                    },
                    expected_benefit=template_data.get('benefit', '改善代码质量'),
                    effort_estimate=template_data.get('effort', '未知'),
                    prerequisites=self._identify_prerequisites(best_template_key, issue)
                )
                
                suggestions.append(suggestion)
        
        return suggestions
    
    def _find_best_template(
        self, 
        issue: ContentIssue, 
        templates: Dict[str, Any]
    ) -> Optional[str]:
        """查找最佳模板"""
        issue_desc_lower = issue.description.lower()
        location_lower = issue.location.lower()
        
        scoring = {}
        
        for template_key, template_data in templates.items():
            score = 0
            
            keywords = template_key.replace('_', ' ').split()
            for keyword in keywords:
                if keyword in issue_desc_lower:
                    score += 2
                if keyword in location_lower:
                    score += 1
            
            applicable_to = template_data.get('applicable_to', [])
            content_type_str = issue.content_type.value
            if any(app in content_type_str for app in applicable_to):
                score += 3
            
            if issue.auto_fixable:
                score += 1
            
            scoring[template_key] = score
        
        if not scoring:
            return None
        
        return max(scoring, key=scoring.get)
    
    def _calculate_priority(self, issue: ContentIssue) -> int:
        """计算优先级"""
        severity_priority = {
            IssueSeverity.CRITICAL: 100,
            IssueSeverity.HIGH: 75,
            IssueSeverity.MEDIUM: 50,
            IssueSeverity.LOW: 25,
            IssueSeverity.INFO: 10
        }
        
        base_priority = severity_priority.get(issue.severity, 25)
        
        if issue.auto_fixable:
            base_priority -= 5
        
        type_priority = {
            IssueType.SECURITY_ISSUE: 20,
            IssueType.MISSING_CONTENT: 10,
            IssueType.INCONSISTENCY: 5,
            IssueType.OUTDATED_INFO: 5,
            IssueType.POOR_QUALITY: 0,
            IssueType.DUPLICATION: -5
        }
        
        base_priority += type_priority.get(issue.issue_type, 0)
        
        return max(0, min(base_priority, 100))
    
    def _generate_implementation_steps(
        self, 
        template_key: str, 
        issue: ContentIssue
    ) -> List[str]:
        """生成实施步骤"""
        steps_map = {
            'add_docstring': [
                "识别函数/类的目的和功能",
                "列出所有参数及其类型和用途",
                "描述返回值的类型和含义",
                "列出可能抛出的异常",
                "编写简洁的文档字符串"
            ],
            'add_type_hints': [
                "分析每个参数的预期类型",
                "确定返回值的类型",
                "添加类型注解到函数签名",
                "导入必要的类型（如 Optional, Union 等）"
            ],
            'add_error_handling': [
                "识别可能失败的代码段",
                "确定需要捕获的异常类型",
                "添加 try-except 块",
                "决定异常处理策略（日志、重新抛出、降级等）"
            ],
            'add_tests': [
                "理解被测函数的行为",
                "设计正常情况下的测试用例",
                "设计边界条件和异常情况的用例",
                "编写清晰的有意义的断言"
            ],
            'fix_reference': [
                "定位文档中的错误引用",
                "验证正确的名称或路径",
                "更新文档内容"
            ],
            'standardize_naming': [
                "确定项目的命名约定",
                "列出需要重命名的标识符",
                "执行重命名（确保更新所有引用）"
            ]
        }
        
        return steps_map.get(template_key, ["实施具体修改"])
    
    def _identify_prerequisites(
        self, 
        template_key: str, 
        issue: ContentIssue
    ) -> List[str]:
        """识别前提条件"""
        prereqs = {
            'add_docstring': [],
            'add_type_hints': ['Python 3.5+ 类型注解支持'],
            'add_error_handling': ['了解可能出现的异常类型'],
            'add_tests': ['测试框架已配置（pytest/unittest）'],
            'fix_reference': ['访问源代码以验证正确名称'],
            'standardize_naming': ['团队对命名约定的共识']
        }
        
        return prereqs.get(template_key, [])


    def _prioritize_suggestions(self, suggestions: List[RefinementSuggestion]) -> List[RefinementSuggestion]:
        """对建议排序"""
        return sorted(suggestions, key=lambda s: (-s.priority, s.effort_estimate))


class SafeAutoRefiner:
    """安全自动完善器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._applied_changes: List[Dict[str, Any]] = []
        self._backup_manager = RefinementBackupManager(config)
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SafeAutoRefiner')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def apply_safe_refinements(
        self,
        suggestions: List[RefinementSuggestion],
        issues: List[ContentIssue],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """应用安全的自动完善"""
        results = {
            'total_suggestions': len(suggestions),
            'applied': 0,
            'skipped': 0,
            'failed': 0,
            'changes': [],
            'summary': ''
        }
        
        safe_actions = self._filter_safe_actions(suggestions, issues)
        
        for suggestion in safe_actions:
            related_issue = next(
                (i for i in issues if i.issue_id in suggestion.target_content or 
                 any(i.issue_id in imp.get('issue', {}).get('issue_id', '') 
                     for imp in suggestion.implementation_details.get('steps', []) if isinstance(imp, dict))),
                None
            )
            
            if not related_issue or not related_issue.auto_fixable:
                results['skipped'] += 1
                continue
            
            try:
                if dry_run:
                    change_record = {
                        'status': 'simulated',
                        'suggestion': suggestion.to_dict(),
                        'message': f"[DRY RUN] 将应用: {suggestion.description}"
                    }
                    results['changes'].append(change_record)
                    results['applied'] += 1
                else:
                    apply_result = self._apply_single_refinement(suggestion, related_issue)
                    
                    if apply_result['success']:
                        results['changes'].append({
                            'status': 'applied',
                            'suggestion': suggestion.to_dict(),
                            **apply_result
                        })
                        results['applied'] += 1
                        self._applied_changes.append(results['changes'][-1])
                    else:
                        results['changes'].append({
                            'status': 'failed',
                            'suggestion': suggestion.to_dict(),
                            'error': apply_result.get('error', 'Unknown error')
                        })
                        results['failed'] += 1
                        
            except Exception as e:
                results['failed'] += 1
                results['changes'].append({
                    'status': 'error',
                    'suggestion': suggestion.to_dict(),
                    'error': str(e)
                })
        
        results['summary'] = self._generate_execution_summary(results)
        
        self._logger.info(f"安全完善完成: {results['applied']} 已应用, {results['skipped']} 跳过, {results['failed']} 失败")
        
        return results
    
    def _filter_safe_actions(
        self,
        suggestions: List[RefinementSuggestion],
        issues: List[ContentIssue]
    ) -> List[Tuple[RefinementSuggestion, ContentIssue]]:
        """筛选安全的操作"""
        safe_pairs = []
        
        for suggestion in suggestions:
            matching_issues = [
                issue for issue in issues 
                if issue.auto_fixable and 
                (issue.issue_id in suggestion.target_content or 
                 issue.location in suggestion.target_content)
            ]
            
            if matching_issues:
                safe_pairs.append((suggestion, matching_issues[0]))
        
        return safe_pairs
    
    def _apply_single_refinement(
        self,
        suggestion: RefinementSuggestion,
        issue: ContentIssue
    ) -> Dict[str, Any]:
        """应用单个完善"""
        target_path = Path(issue.location.split(':')[0])
        
        if not target_path.exists():
            return {'success': False, 'error': '目标文件不存在'}
        
        backup_path = self._backup_manager.create_backup(target_path)
        
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            modified_content = original_content
            
            if suggestion.action_type == 'add_docstring':
                modified_content = self._add_docstring(original_content, issue)
            elif suggestion.action_type == 'add_type_hints':
                modified_content = self._add_type_hints(original_content, issue)
            elif suggestion.action_type == 'fix_reference':
                modified_content = self._fix_reference(original_content, issue)
            
            if modified_content != original_content:
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                return {
                    'success': True,
                    'target_file': str(target_path),
                    'backup_created': bool(backup_path),
                    'change_type': suggestion.action_type
                }
            else:
                return {
                    'success': True,
                    'message': '无需更改（已是最新状态）'
                }
                
        except Exception as e:
            if backup_path:
                self._backup_manager.restore(backup_path, target_path)
            
            return {'success': False, 'error': str(e)}
    
    def _add_docstring(self, content: str, issue: ContentIssue) -> str:
        """添加文档字符串"""
        metadata = issue.metadata
        func_or_class = metadata.get('function_name') or metadata.get('class_name', '')
        
        if not func_or_class:
            return content
        
        simple_docstring = f'''"""
Brief description of {func_or_class}.

More detailed explanation if needed.
"""
'''
        
        pattern = rf'(def|class)\s+{re.escape(func_or_class)}\s*[(:]'
        match = re.search(pattern, content)
        
        if match:
            insert_pos = match.end()
            
            next_line_start = content.find('\n', insert_pos)
            if next_line_start != -1:
                insert_pos = next_line_start + 1
            
            return content[:insert_pos] + simple_docstring + '\n' + content[insert_pos:]
        
        return content
    
    def _add_type_hints(self, content: str, issue: ContentIssue) -> str:
        """添加类型提示（简化版）"""
        metadata = issue.metadata
        untyped_args = metadata.get('untyped_args', [])
        func_name = metadata.get('function_name', '')
        
        if not func_name or not untyped_args:
            return content
        
        for arg_name in untyped_args[:3]:
            pattern = rf'(def\s+{re.escape(func_name)}\s*\([^)]*?)\b{re.escape(arg_name)}\b([^)]*?\))'
            
            def replace_with_type(match):
                before_arg = match.group(1)
                after_arg = match.group(2)
                return f"{before_arg}{arg_name}: Any{after_arg}"
            
            content = re.sub(pattern, replace_with_type, content, count=1)
        
        if 'Any' in content and 'from typing import Any' not in content:
            content = 'from typing import Any\n' + content
        
        return content
    
    def _fix_reference(self, content: str, issue: ContentIssue) -> str:
        """修复引用"""
        metadata = issue.metadata
        
        if 'broken_links' in metadata:
            for link in metadata['broken_links'][:3]:
                content = content.replace(f"]({link})", f"](#{link.lower().replace(' ', '-')})")
        
        return content
    
    def _generate_execution_summary(self, results: Dict[str, Any]) -> str:
        """生成执行摘要"""
        total = results['total_suggestions']
        applied = results['applied']
        skipped = results['skipped']
        failed = results['failed']
        
        if applied == total:
            return "✅ 所有安全建议都已成功应用"
        elif applied > 0:
            return f"⚠️ 应用了 {applied}/{total} 个建议，{skipped} 个跳过，{failed} 个失败"
        else:
            return "ℹ️ 未应用任何更改（所有建议都需要手动处理或不适用）"


class RefinementBackupManager:
    """完善备份管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._backup_dir = Path(self._config.get('backup_dir', './.refinement_backups'))
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('RefinementBackupManager')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def create_backup(self, file_path: Path) -> str:
        """创建备份"""
        if not file_path.exists():
            return ""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
        backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}.bak"
        backup_path = self._backup_dir / backup_filename
        
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            import shutil
            shutil.copy2(file_path, backup_path)
            return str(backup_path)
        except Exception as e:
            self._logger.error(f"备份创建失败: {e}")
            return ""
    
    def restore(self, backup_path: str, target_path: Path) -> bool:
        """恢复备份"""
        import shutil
        backup = Path(backup_path)
        
        if not backup.exists():
            return False
        
        try:
            shutil.copy2(backup, target_path)
            return True
        except Exception:
            return False


class SkillContentRefiner:
    """技能内容完善器主类"""
    
    def __init__(self, project_path: str, config: Dict[str, Any] = None):
        self.project_path = Path(project_path)
        self._config = config or {}
        
        self.gap_detector = ContentGapDetector(config)
        self.inconsistency_detector = InconsistencyDetector(config)
        self.suggestion_generator = SuggestionGenerator(config)
        self.safe_refiner = SafeAutoRefiner(config)
        
        self._refinement_history: List[RefinementReport] = []
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SkillContentRefiner')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def run_full_refinement_cycle(
        self,
        dry_run: bool = False,
        auto_apply_safe: bool = True,
        focus_areas: Optional[List[ContentType]] = None
    ) -> RefinementReport:
        """运行完整的内容完善周期"""
        cycle_start = datetime.now()
        
        self._logger.info("=" * 70)
        self._logger.info("开始技能内容完善周期")
        self._logger.info("=" * 70)
        
        self._logger.info("步骤 1/4: 检测内容缺口...")
        gap_analysis = self.gap_detector.detect_gaps(
            self.project_path,
            content_types=focus_areas
        )
        
        self._logger.info(f"发现 {len(gap_analysis.issues_found)} 个内容问题 (健康分数: {gap_analysis.health_score})")
        
        self._logger.info("步骤 2/4: 检测不一致性...")
        inconsistencies = self.inconsistency_detector.detect_inconsistencies(self.project_path)
        
        all_issues = gap_analysis.issues_found + inconsistencies
        all_issues = self._deduplicate_all_issues(all_issues)
        
        self._logger.info(f"总计 {len(all_issues)} 个问题待处理")
        
        self._logger.info("步骤 3/4: 生成完善建议...")
        suggestions = self.suggestion_generator.generate_suggestions(all_issues)
        
        self._logger.info(f"生成了 {len(suggestions)} 条完善建议")
        
        self._logger.info("步骤 4/4: 应用安全完善...")
        refinement_results = self.safe_refiner.apply_safe_refinements(
            suggestions,
            all_issues,
            dry_run=dry_run
        )
        
        cycle_end = datetime.now()
        
        report = RefinementReport(
            report_id=f"REFINE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=cycle_end.isoformat(),
            analysis_result=gap_analysis,
            suggestions=suggestions,
            applied_changes=refinement_results['changes'],
            summary=self._generate_cycle_summary(gap_analysis, refinement_results, cycle_end - cycle_start)
        )
        
        self._refinement_history.append(report)
        
        self._logger.info("=" * 70)
        self._logger.info("内容完善周期完成")
        self._logger.info(f"- 问题总数: {len(all_issues)}")
        self._logger.info(f"- 建议数量: {len(suggestions)}")
        self._logger.info(f"- 已应用: {refinement_results['applied']}")
        self._logger.info(f"- 跳过: {refinement_results['skipped']}")
        self._logger.info(f"- 失败: {refinement_results['failed']}")
        self._logger.info(f"- 耗时: {(cycle_end - cycle_start).total_seconds():.1f}s")
        self._logger.info("=" * 70)
        
        return report
    
    def _deduplicate_all_issues(self, issues: List[ContentIssue]) -> List[ContentIssue]:
        """去重所有问题"""
        seen = set()
        unique = []
        
        for issue in issues:
            key = (issue.issue_type, issue.location, issue.description[:80])
            if key not in seen:
                seen.add(key)
                unique.append(issue)
        
        return unique
    
    def _generate_cycle_summary(
        self,
        analysis: ContentAnalysisResult,
        refinement_results: Dict[str, Any],
        duration: timedelta
    ) -> Dict[str, Any]:
        """生成周期摘要"""
        return {
            'initial_health_score': analysis.health_score,
            'issues_before': len(analysis.issues_found),
            'issues_critical': len([i for i in analysis.issues_found if i.severity == IssueSeverity.CRITICAL]),
            'issues_high': len([i for i in analysis.issues_found if i.severity == IssueSeverity.HIGH]),
            'auto_fixable_count': analysis.statistics.get('auto_fixable_count', 0),
            'refinements_applied': refinement_results['applied'],
            'refinements_skipped': refinement_results['skipped'],
            'refinements_failed': refinement_results['failed'],
            'duration_seconds': duration.total_seconds(),
            'improvement_estimation': self._estimate_improvement(refinement_results),
            'next_recommendations': self._get_next_steps(analysis, refinement_results)
        }
    
    def _estimate_improvement(self, results: Dict[str, Any]) -> str:
        """估算改进程度"""
        applied = results['applied']
        total = results['total_suggestions']
        
        if total == 0:
            return "无变化"
        
        ratio = applied / total
        
        if ratio >= 0.8:
            return "显著改善"
        elif ratio >= 0.5:
            return "中等改善"
        elif ratio > 0:
            return "轻微改善"
        else:
            return "需手动处理"
    
    def _get_next_steps(
        self,
        analysis: ContentAnalysisResult,
        results: Dict[str, Any]
    ) -> List[str]:
        """获取下一步行动"""
        recommendations = []
        
        critical_remaining = len([i for i in analysis.issues_found 
                                if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH] 
                                and not i.auto_fixable])
        
        if critical_remaining > 0:
            recommendations.append(f"🔴 优先处理 {critical_remaining} 个高优先级手动项")
        
        skipped = results['skipped']
        if skipped > 3:
            recommendations.append(f"⏭️ 审查 {skipped} 个被跳过的建议")
        
        if analysis.health_score < 60:
            recommendations.append("📊 安排一次全面的代码质量审查")
        
        auto_fixable_remaining = analysis.statistics.get('auto_fixable_count', 0) - results['applied']
        if auto_fixable_remaining > 5:
            recommendations.append(f"🔧 运行另一次自动完善周期以处理剩余 {auto_fixable_remaining} 个可自动修复项")
        
        if not recommendations:
            recommendations.append("✅ 内容质量良好，继续保持定期维护即可")
        
        return recommendations[:4]
    
    def get_refinement_history(self, limit: int = 10) -> List[RefinementReport]:
        """获取完善历史"""
        return self._refinement_history[-limit:]
    
    def export_report(self, output_path: Path, report: RefinementReport):
        """导出报告"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2, default=str)
        
        self._logger.info(f"报告已导出: {output_path}")


if __name__ == '__main__':
    print("技能内容完善器模块已加载 (Phase 9.2)")
    print("\n主要组件:")
    print("- ContentGapDetector: 内容缺口检测器")
    print("- InconsistencyDetector: 不一致性检测器")
    print("- SuggestionGenerator: 完善建议生成器")
    print("- SafeAutoRefiner: 安全自动完善器")
    print("- SkillContentRefiner: 技能内容完善器主类")
