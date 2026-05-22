#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强需求追溯管理器
实现需求-测试追溯矩阵生成、需求-代码追溯矩阵生成、追溯关系可视化
增强功能：智能追溯分析、覆盖率分析、追溯报告生成
"""

import json
import sqlite3
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, Set
from datetime import datetime
from enum import Enum
from pathlib import Path
from collections import defaultdict


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TraceStatus(Enum):
    PENDING = "pending"
    COVERED = "covered"
    VERIFIED = "verified"
    FAILED = "failed"
    PARTIAL = "partial"
    ORPHANED = "orphaned"
    DEPRECATED = "deprecated"


class TraceType(Enum):
    REQUIREMENT_TO_TEST = "requirement_to_test"
    REQUIREMENT_TO_CODE = "requirement_to_code"
    REQUIREMENT_TO_FEATURE = "requirement_to_feature"
    FEATURE_TO_TEST = "feature_to_test"
    USER_STORY_TO_TEST = "user_story_to_test"
    CODE_TO_TEST = "code_to_test"
    REQUIREMENT_TO_REQUIREMENT = "requirement_to_requirement"
    TEST_TO_TEST = "test_to_test"


class CodeElementType(Enum):
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    METHOD = "method"
    VARIABLE = "variable"
    INTERFACE = "interface"
    API_ENDPOINT = "api_endpoint"
    DATABASE_TABLE = "database_table"


class ImpactLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class RequirementType(Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    BUSINESS = "business"
    TECHNICAL = "technical"
    USER_STORY = "user_story"
    EPIC = "epic"
    FEATURE = "feature"


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    ACCEPTANCE = "acceptance"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REGRESSION = "regression"


@dataclass
class TraceLink:
    id: str
    source_type: str
    source_id: str
    source_name: str
    target_type: str
    target_id: str
    target_name: str
    trace_type: TraceType
    status: TraceStatus
    confidence: float = 1.0
    is_automatic: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "trace_type": self.trace_type.value,
            "status": self.status.value,
            "confidence": self.confidence,
            "is_automatic": self.is_automatic,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }


@dataclass
class TestCase:
    id: str
    name: str
    description: str
    test_type: TestType
    scenario: str
    given: str
    when: str
    then: str
    priority: str = "medium"
    status: str = "pending"
    execution_result: Optional[str] = None
    execution_time: Optional[str] = None
    duration_ms: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "test_type": self.test_type.value if isinstance(self.test_type, TestType) else self.test_type,
            "scenario": self.scenario,
            "given": self.given,
            "when": self.when,
            "then": self.then,
            "priority": self.priority,
            "status": self.status,
            "execution_result": self.execution_result,
            "execution_time": self.execution_time,
            "duration_ms": self.duration_ms,
            "tags": self.tags,
            "created_at": self.created_at
        }


@dataclass
class RequirementNode:
    id: str
    name: str
    requirement_type: RequirementType
    description: str
    priority: str = "medium"
    status: str = "active"
    version: str = "1.0"
    parent_id: Optional[str] = None
    children: List['RequirementNode'] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    acceptance_criteria: List[Dict[str, str]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "requirement_type": self.requirement_type.value if isinstance(self.requirement_type, RequirementType) else self.requirement_type,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "version": self.version,
            "parent_id": self.parent_id,
            "children": [c.to_dict() for c in self.children],
            "tags": self.tags,
            "acceptance_criteria": self.acceptance_criteria,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class CodeElement:
    id: str
    name: str
    element_type: CodeElementType
    file_path: str
    line_start: int
    line_end: int
    module_name: str
    class_name: Optional[str] = None
    docstring: Optional[str] = None
    source_code: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    called_by: List[str] = field(default_factory=list)
    complexity: int = 1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "element_type": self.element_type.value if isinstance(self.element_type, CodeElementType) else self.element_type,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "module_name": self.module_name,
            "class_name": self.class_name,
            "docstring": self.docstring,
            "source_code": self.source_code,
            "keywords": self.keywords,
            "dependencies": self.dependencies,
            "called_by": self.called_by,
            "complexity": self.complexity,
            "created_at": self.created_at
        }


@dataclass
class TraceMatrix:
    project_id: str
    project_name: str
    requirements: List[RequirementNode]
    test_cases: List[TestCase]
    code_elements: List[CodeElement]
    trace_links: List[TraceLink]
    coverage_stats: Dict[str, Any]
    code_coverage_stats: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "requirements": [r.to_dict() for r in self.requirements],
            "test_cases": [t.to_dict() for t in self.test_cases],
            "code_elements": [c.to_dict() for c in self.code_elements],
            "trace_links": [l.to_dict() for l in self.trace_links],
            "coverage_stats": self.coverage_stats,
            "code_coverage_stats": self.code_coverage_stats,
            "quality_metrics": self.quality_metrics,
            "generated_at": self.generated_at
        }


@dataclass
class VisualizationNode:
    id: str
    label: str
    node_type: str
    status: str
    x: float = 0.0
    y: float = 0.0
    size: int = 30
    color: str = "#409EFF"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type,
            "status": self.status,
            "x": self.x,
            "y": self.y,
            "size": self.size,
            "color": self.color,
            "metadata": self.metadata
        }


@dataclass
class VisualizationEdge:
    id: str
    source: str
    target: str
    edge_type: str
    status: str
    color: str = "#909399"
    width: int = 2
    confidence: float = 1.0
    is_automatic: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.edge_type,
            "status": self.status,
            "color": self.color,
            "width": self.width,
            "confidence": self.confidence,
            "is_automatic": self.is_automatic
        }


@dataclass
class TraceVisualization:
    nodes: List[VisualizationNode]
    edges: List[VisualizationEdge]
    layout: str = "hierarchical"
    title: str = "需求追溯矩阵"
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "layout": self.layout,
            "title": self.title,
            "generated_at": self.generated_at
        }


@dataclass
class CoverageReport:
    total_requirements: int
    covered_requirements: int
    verified_requirements: int
    partial_requirements: int
    uncovered_requirements: int
    coverage_rate: float
    verification_rate: float
    by_priority: Dict[str, Dict[str, int]]
    by_type: Dict[str, Dict[str, int]]
    gaps: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requirements": self.total_requirements,
            "covered_requirements": self.covered_requirements,
            "verified_requirements": self.verified_requirements,
            "partial_requirements": self.partial_requirements,
            "uncovered_requirements": self.uncovered_requirements,
            "coverage_rate": self.coverage_rate,
            "verification_rate": self.verification_rate,
            "by_priority": self.by_priority,
            "by_type": self.by_type,
            "gaps": self.gaps,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at
        }


@dataclass
class ImpactAnalysisResult:
    """影响分析结果数据类"""
    source_id: str
    source_name: str
    source_type: str
    change_type: str
    affected_items: List[Dict[str, Any]]
    impact_level: ImpactLevel
    risk_score: float
    recommendations: List[str]
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "change_type": self.change_type,
            "affected_items": self.affected_items,
            "impact_level": self.impact_level.value,
            "risk_score": self.risk_score,
            "recommendations": self.recommendations,
            "analyzed_at": self.analyzed_at
        }


@dataclass
class TraceIntegrityReport:
    """追溯完整性检查报告数据类"""
    total_traces: int
    valid_traces: int
    invalid_traces: int
    missing_traces: int
    orphaned_items: Dict[str, List[str]]
    broken_links: List[Dict[str, Any]]
    consistency_issues: List[Dict[str, Any]]
    integrity_score: float
    recommendations: List[str]
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_traces": self.total_traces,
            "valid_traces": self.valid_traces,
            "invalid_traces": self.invalid_traces,
            "missing_traces": self.missing_traces,
            "orphaned_items": self.orphaned_items,
            "broken_links": self.broken_links,
            "consistency_issues": self.consistency_issues,
            "integrity_score": self.integrity_score,
            "recommendations": self.recommendations,
            "checked_at": self.checked_at
        }


@dataclass
class TestTraceMatrixView:
    """需求-测试追溯矩阵视图数据类"""
    view_name: str
    dimension: str
    data: List[Dict[str, Any]]
    summary: Dict[str, Any]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "view_name": self.view_name,
            "dimension": self.dimension,
            "data": self.data,
            "summary": self.summary,
            "generated_at": self.generated_at
        }


@dataclass
class CodeTraceMatrixView:
    """需求-代码追溯矩阵视图数据类"""
    view_name: str
    dimension: str
    data: List[Dict[str, Any]]
    summary: Dict[str, Any]
    file_coverage: Dict[str, Any]
    module_coverage: Dict[str, Any]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "view_name": self.view_name,
            "dimension": self.dimension,
            "data": self.data,
            "summary": self.summary,
            "file_coverage": self.file_coverage,
            "module_coverage": self.module_coverage,
            "generated_at": self.generated_at
        }


@dataclass
class CodeChangeRecord:
    """代码变更记录数据类"""
    id: str
    code_element_id: str
    change_type: str
    old_value: Optional[str]
    new_value: Optional[str]
    changed_by: str
    changed_at: str
    commit_id: Optional[str] = None
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code_element_id": self.code_element_id,
            "change_type": self.change_type,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_by": self.changed_by,
            "changed_at": self.changed_at,
            "commit_id": self.commit_id,
            "description": self.description
        }


@dataclass
class EnhancedVisualization:
    """增强的可视化数据类"""
    nodes: List[VisualizationNode]
    edges: List[VisualizationEdge]
    layout_type: str
    title: str
    filters: Dict[str, Any]
    statistics: Dict[str, Any]
    interactive_options: Dict[str, Any]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "layout_type": self.layout_type,
            "title": self.title,
            "filters": self.filters,
            "statistics": self.statistics,
            "interactive_options": self.interactive_options,
            "generated_at": self.generated_at
        }


class IntelligentTraceAnalyzer:
    KEYWORD_WEIGHTS = {
        'exact_match': 1.0,
        'partial_match': 0.7,
        'semantic_match': 0.5,
        'fuzzy_match': 0.3
    }
    
    def __init__(self):
        self._stop_words = {'的', '是', '在', '和', '与', '或', '等', '及', '将', '被', '为', '到', '从', '对', '按', 'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once'}
    
    def analyze_trace_confidence(self, source_text: str, target_text: str) -> float:
        if not source_text or not target_text:
            return 0.0
        
        source_lower = source_text.lower()
        target_lower = target_text.lower()
        
        if source_lower == target_lower:
            return self.KEYWORD_WEIGHTS['exact_match']
        
        source_words = self._tokenize(source_text)
        target_words = self._tokenize(target_text)
        
        if not source_words or not target_words:
            return 0.0
        
        intersection = source_words & target_words
        union = source_words | target_words
        
        jaccard = len(intersection) / len(union) if union else 0
        
        source_keywords = self._extract_keywords(source_text)
        target_keywords = self._extract_keywords(target_text)
        
        keyword_overlap = 0.0
        if source_keywords and target_keywords:
            keyword_intersection = source_keywords & target_keywords
            keyword_overlap = len(keyword_intersection) / min(len(source_keywords), len(target_keywords))
        
        confidence = jaccard * 0.6 + keyword_overlap * 0.4
        
        return min(confidence, 1.0)
    
    def _tokenize(self, text: str) -> Set[str]:
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b|\b[\u4e00-\u9fa5]+\b', text.lower())
        return set(w for w in words if w not in self._stop_words and len(w) > 1)
    
    def _extract_keywords(self, text: str) -> Set[str]:
        keywords = set()
        
        patterns = [
            r'(?:用户|客户|管理员|系统)',
            r'(?:登录|注册|认证|授权)',
            r'(?:订单|支付|发货|退款)',
            r'(?:商品|库存|价格|折扣)',
            r'(?:查询|搜索|筛选|排序)',
            r'(?:添加|修改|删除|更新)',
            r'(?:验证|检查|校验|确认)',
            r'(?:发送|接收|通知|消息)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            keywords.update(matches)
        
        words = self._tokenize(text)
        keywords.update(w for w in words if len(w) >= 3)
        
        return keywords
    
    def suggest_traces(self, requirement: RequirementNode, 
                       test_cases: List[TestCase],
                       code_elements: List[CodeElement]) -> Dict[str, List[Tuple[str, float]]]:
        suggestions = {
            'test_cases': [],
            'code_elements': []
        }
        
        req_text = f"{requirement.name} {requirement.description}"
        
        for test in test_cases:
            test_text = f"{test.name} {test.description} {test.scenario}"
            confidence = self.analyze_trace_confidence(req_text, test_text)
            if confidence >= 0.3:
                suggestions['test_cases'].append((test.id, confidence))
        
        for code in code_elements:
            code_text = f"{code.name} {code.docstring or ''}"
            confidence = self.analyze_trace_confidence(req_text, code_text)
            if confidence >= 0.3:
                suggestions['code_elements'].append((code.id, confidence))
        
        suggestions['test_cases'].sort(key=lambda x: x[1], reverse=True)
        suggestions['code_elements'].sort(key=lambda x: x[1], reverse=True)
        
        return suggestions


class RequirementTraceManager:
    TYPE_COLORS = {
        "requirement": "#409EFF",
        "user_story": "#67C23A",
        "feature": "#E6A23C",
        "test_case": "#F56C6C",
        "code_element": "#9B59B6",
        "function": "#9B59B6",
        "class": "#8E44AD",
        "module": "#7D3C98"
    }
    
    STATUS_COLORS = {
        "covered": "#67C23A",
        "verified": "#67C23A",
        "pending": "#E6A23C",
        "failed": "#F56C6C",
        "partial": "#E6A23C",
        "uncovered": "#F56C6C",
        "active": "#409EFF",
        "passed": "#67C23A",
        "orphaned": "#909399"
    }
    
    EDGE_COLORS = {
        "requirement_to_test": "#409EFF",
        "requirement_to_code": "#67C23A",
        "feature_to_test": "#E6A23C",
        "user_story_to_test": "#909399",
        "code_to_test": "#9B59B6"
    }
    
    def __init__(self, db_path: str = "requirement_trace.db"):
        self.db_path = db_path
        self._init_database()
        self._analyzer = IntelligentTraceAnalyzer()
        logger.info(f"需求追溯管理器初始化完成: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requirements (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                requirement_type TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'active',
                version TEXT DEFAULT '1.0',
                parent_id TEXT,
                tags TEXT,
                acceptance_criteria TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (parent_id) REFERENCES requirements(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_cases (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                test_type TEXT NOT NULL,
                scenario TEXT,
                given TEXT,
                "when" TEXT,
                "then" TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                execution_result TEXT,
                execution_time TEXT,
                duration_ms INTEGER,
                tags TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_elements (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                element_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_start INTEGER,
                line_end INTEGER,
                module_name TEXT,
                class_name TEXT,
                docstring TEXT,
                source_code TEXT,
                keywords TEXT,
                dependencies TEXT,
                called_by TEXT,
                complexity INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trace_links (
                id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_name TEXT,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                target_name TEXT,
                trace_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                confidence REAL DEFAULT 1.0,
                is_automatic INTEGER DEFAULT 0,
                verified_by TEXT,
                verified_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trace_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                action TEXT NOT NULL,
                old_status TEXT,
                new_status TEXT,
                changed_by TEXT,
                changed_at TEXT NOT NULL,
                reason TEXT,
                FOREIGN KEY (trace_id) REFERENCES trace_links(id)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trace_source ON trace_links(source_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trace_target ON trace_links(target_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trace_type ON trace_links(trace_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_file ON code_elements(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_module ON code_elements(module_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_req_parent ON requirements(parent_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_req_type ON requirements(requirement_type)')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_changes (
                id TEXT PRIMARY KEY,
                code_element_id TEXT NOT NULL,
                change_type TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_by TEXT,
                changed_at TEXT NOT NULL,
                commit_id TEXT,
                description TEXT,
                FOREIGN KEY (code_element_id) REFERENCES code_elements(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trace_integrity_checks (
                id TEXT PRIMARY KEY,
                check_type TEXT NOT NULL,
                result TEXT NOT NULL,
                issues TEXT,
                checked_at TEXT NOT NULL,
                checked_by TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS impact_analyses (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                change_type TEXT NOT NULL,
                impact_level TEXT NOT NULL,
                affected_items TEXT,
                risk_score REAL,
                recommendations TEXT,
                analyzed_at TEXT NOT NULL,
                analyzed_by TEXT
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_changes ON code_changes(code_element_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_impact_source ON impact_analyses(source_id)')
        
        conn.commit()
        conn.close()
    
    def _generate_id(self, prefix: str = "TR") -> str:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"{prefix}-{timestamp}"
    
    def add_requirement(self, 
                        name: str,
                        requirement_type: RequirementType,
                        description: str = "",
                        priority: str = "medium",
                        parent_id: str = None,
                        tags: List[str] = None,
                        acceptance_criteria: List[Dict[str, str]] = None) -> RequirementNode:
        
        req_id = self._generate_id("REQ")
        now = datetime.now().isoformat()
        tags = tags or []
        acceptance_criteria = acceptance_criteria or []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO requirements (id, name, requirement_type, description, priority, status, parent_id, tags, acceptance_criteria, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (req_id, name, requirement_type.value, description, priority, 'active', parent_id,
                  json.dumps(tags, ensure_ascii=False), json.dumps(acceptance_criteria, ensure_ascii=False), now, now))
            
            conn.commit()
            conn.close()
            
            logger.info(f"添加需求: {req_id} - {name}")
            
            return RequirementNode(
                id=req_id,
                name=name,
                requirement_type=requirement_type,
                description=description,
                priority=priority,
                parent_id=parent_id,
                tags=tags,
                acceptance_criteria=acceptance_criteria
            )
            
        except Exception as e:
            logger.error(f"添加需求失败: {e}")
            raise
    
    def add_test_case(self,
                       name: str,
                       test_type: TestType,
                       scenario: str = "",
                       given: str = "",
                       when: str = "",
                       then: str = "",
                       description: str = "",
                       priority: str = "medium",
                       tags: List[str] = None) -> TestCase:
        
        test_id = self._generate_id("TC")
        now = datetime.now().isoformat()
        tags = tags or []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO test_cases (id, name, description, test_type, scenario, given, "when", "then", priority, status, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (test_id, name, description, test_type.value, scenario, given, when, then, priority, 'pending',
                  json.dumps(tags, ensure_ascii=False), now))
            
            conn.commit()
            conn.close()
            
            logger.info(f"添加测试用例: {test_id} - {name}")
            
            return TestCase(
                id=test_id,
                name=name,
                description=description,
                test_type=test_type,
                scenario=scenario,
                given=given,
                when=when,
                then=then,
                priority=priority,
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"添加测试用例失败: {e}")
            raise
    
    def add_code_element(self,
                         name: str,
                         element_type: CodeElementType,
                         file_path: str,
                         line_start: int,
                         line_end: int,
                         module_name: str,
                         class_name: str = None,
                         docstring: str = None,
                         source_code: str = None,
                         keywords: List[str] = None,
                         dependencies: List[str] = None,
                         called_by: List[str] = None,
                         complexity: int = 1) -> CodeElement:
        
        element_id = self._generate_id("CODE")
        now = datetime.now().isoformat()
        keywords = keywords or []
        dependencies = dependencies or []
        called_by = called_by or []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO code_elements 
                (id, name, element_type, file_path, line_start, line_end, module_name, class_name, 
                 docstring, source_code, keywords, dependencies, called_by, complexity, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (element_id, name, element_type.value, file_path, line_start, line_end,
                  module_name, class_name, docstring, source_code,
                  json.dumps(keywords, ensure_ascii=False),
                  json.dumps(dependencies, ensure_ascii=False),
                  json.dumps(called_by, ensure_ascii=False),
                  complexity, now))
            
            conn.commit()
            conn.close()
            
            logger.info(f"添加代码元素: {element_id} - {name}")
            
            return CodeElement(
                id=element_id,
                name=name,
                element_type=element_type,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                module_name=module_name,
                class_name=class_name,
                docstring=docstring,
                source_code=source_code,
                keywords=keywords,
                dependencies=dependencies,
                called_by=called_by,
                complexity=complexity
            )
            
        except Exception as e:
            logger.error(f"添加代码元素失败: {e}")
            raise
    
    def create_trace_link(self,
                          source_type: str,
                          source_id: str,
                          source_name: str,
                          target_type: str,
                          target_id: str,
                          target_name: str,
                          trace_type: TraceType,
                          confidence: float = 1.0,
                          is_automatic: bool = False,
                          metadata: Dict[str, Any] = None) -> TraceLink:
        
        link_id = self._generate_id("TL")
        now = datetime.now().isoformat()
        metadata = metadata or {}
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trace_links 
                (id, source_type, source_id, source_name, target_type, target_id, target_name, 
                 trace_type, status, confidence, is_automatic, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (link_id, source_type, source_id, source_name, target_type, target_id, target_name,
                  trace_type.value, TraceStatus.PENDING.value, confidence, 1 if is_automatic else 0, now, now,
                  json.dumps(metadata, ensure_ascii=False)))
            
            conn.commit()
            conn.close()
            
            logger.info(f"创建追溯链接: {link_id} ({source_name} -> {target_name})")
            
            return TraceLink(
                id=link_id,
                source_type=source_type,
                source_id=source_id,
                source_name=source_name,
                target_type=target_type,
                target_id=target_id,
                target_name=target_name,
                trace_type=trace_type,
                status=TraceStatus.PENDING,
                confidence=confidence,
                is_automatic=is_automatic,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"创建追溯链接失败: {e}")
            raise
    
    def get_requirement_traces(self, requirement_id: str) -> List[TraceLink]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM trace_links 
                WHERE source_id = ? OR target_id = ?
            ''', (requirement_id, requirement_id))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_trace_link(row) for row in rows]
            
        except Exception as e:
            logger.error(f"获取需求追溯失败: {e}")
            return []
    
    def get_test_case_traces(self, test_case_id: str) -> List[TraceLink]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM trace_links WHERE target_id = ?
            ''', (test_case_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_trace_link(row) for row in rows]
            
        except Exception as e:
            logger.error(f"获取测试用例追溯失败: {e}")
            return []
    
    def get_code_element_traces(self, code_element_id: str) -> List[TraceLink]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM trace_links 
                WHERE source_id = ? OR target_id = ?
            ''', (code_element_id, code_element_id))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_trace_link(row) for row in rows]
            
        except Exception as e:
            logger.error(f"获取代码元素追溯失败: {e}")
            return []
    
    def _row_to_trace_link(self, row: sqlite3.Row) -> TraceLink:
        return TraceLink(
            id=row['id'],
            source_type=row['source_type'],
            source_id=row['source_id'],
            source_name=row['source_name'],
            target_type=row['target_type'],
            target_id=row['target_id'],
            target_name=row['target_name'],
            trace_type=TraceType(row['trace_type']),
            status=TraceStatus(row['status']),
            confidence=row['confidence'],
            is_automatic=bool(row['is_automatic']),
            verified_by=row['verified_by'],
            verified_at=row['verified_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )
    
    def update_trace_status(self, trace_id: str, status: TraceStatus, 
                            verified_by: str = None) -> Optional[TraceLink]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                UPDATE trace_links SET status = ?, verified_by = ?, verified_at = ?, updated_at = ? WHERE id = ?
            ''', (status.value, verified_by, now if verified_by else None, now, trace_id))
            
            cursor.execute('''
                INSERT INTO trace_history (trace_id, action, new_status, changed_by, changed_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (trace_id, 'status_change', status.value, verified_by or 'system', now))
            
            conn.commit()
            
            cursor.execute('SELECT * FROM trace_links WHERE id = ?', (trace_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_trace_link(row)
            return None
            
        except Exception as e:
            logger.error(f"更新追溯状态失败: {e}")
            return None
    
    def verify_trace(self, trace_id: str, verified_by: str) -> Optional[TraceLink]:
        return self.update_trace_status(trace_id, TraceStatus.VERIFIED, verified_by)
    
    def generate_test_from_acceptance_criteria(self, 
                                                requirement_id: str,
                                                requirement_name: str,
                                                acceptance_criteria: List[Dict[str, str]]) -> List[TestCase]:
        
        test_cases = []
        
        try:
            for i, ac in enumerate(acceptance_criteria):
                scenario = ac.get('scenario', f'场景{i+1}')
                given = ac.get('given', '')
                when = ac.get('when', '')
                then = ac.get('then', '')
                
                test_case = self.add_test_case(
                    name=f"{requirement_name} - {scenario}",
                    test_type=TestType.ACCEPTANCE,
                    scenario=scenario,
                    given=given,
                    when=when,
                    then=then,
                    description=f"由需求 {requirement_id} 的验收标准自动生成",
                    tags=['auto-generated', 'acceptance']
                )
                
                self.create_trace_link(
                    source_type="requirement",
                    source_id=requirement_id,
                    source_name=requirement_name,
                    target_type="test_case",
                    target_id=test_case.id,
                    target_name=test_case.name,
                    trace_type=TraceType.REQUIREMENT_TO_TEST,
                    confidence=1.0,
                    is_automatic=True,
                    metadata={"auto_generated": True, "from_acceptance_criteria": True}
                )
                
                test_cases.append(test_case)
            
            logger.info(f"从验收标准生成 {len(test_cases)} 个测试用例")
            
        except Exception as e:
            logger.error(f"生成测试用例失败: {e}")
        
        return test_cases
    
    def link_requirement_to_code(self,
                                  requirement_id: str,
                                  requirement_name: str,
                                  code_element_id: str,
                                  code_element_name: str,
                                  confidence: float = 1.0,
                                  is_automatic: bool = False,
                                  metadata: Dict[str, Any] = None) -> Optional[TraceLink]:
        
        return self.create_trace_link(
            source_type="requirement",
            source_id=requirement_id,
            source_name=requirement_name,
            target_type="code_element",
            target_id=code_element_id,
            target_name=code_element_name,
            trace_type=TraceType.REQUIREMENT_TO_CODE,
            confidence=confidence,
            is_automatic=is_automatic,
            metadata=metadata
        )
    
    def auto_link_code_by_keywords(self,
                                    requirement_id: str,
                                    requirement_name: str,
                                    requirement_keywords: List[str]) -> List[TraceLink]:
        
        links = []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for keyword in requirement_keywords:
                cursor.execute('''
                    SELECT * FROM code_elements 
                    WHERE keywords LIKE ? OR name LIKE ? OR docstring LIKE ?
                ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
                
                rows = cursor.fetchall()
                
                for row in rows:
                    code_element = self._row_to_code_element(row)
                    confidence = 0.7 if keyword.lower() in row['name'].lower() else 0.5
                    
                    link = self.link_requirement_to_code(
                        requirement_id=requirement_id,
                        requirement_name=requirement_name,
                        code_element_id=code_element.id,
                        code_element_name=code_element.name,
                        confidence=confidence,
                        is_automatic=True,
                        metadata={"auto_linked": True, "matched_keyword": keyword}
                    )
                    
                    if link:
                        links.append(link)
            
            conn.close()
            logger.info(f"自动关联代码元素: {len(links)} 个")
            
        except Exception as e:
            logger.error(f"自动关联代码失败: {e}")
        
        return links
    
    def auto_link_tests_by_keywords(self,
                                     requirement_id: str,
                                     requirement_name: str,
                                     requirement_description: str) -> List[TraceLink]:
        
        links = []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM test_cases')
            rows = cursor.fetchall()
            test_cases = [self._row_to_test_case(row) for row in rows]
            
            suggestions = self._analyzer.suggest_traces(
                RequirementNode(
                    id=requirement_id,
                    name=requirement_name,
                    requirement_type=RequirementType.FUNCTIONAL,
                    description=requirement_description
                ),
                test_cases,
                []
            )
            
            for test_id, confidence in suggestions['test_cases']:
                test = next((t for t in test_cases if t.id == test_id), None)
                if test:
                    link = self.create_trace_link(
                        source_type="requirement",
                        source_id=requirement_id,
                        source_name=requirement_name,
                        target_type="test_case",
                        target_id=test.id,
                        target_name=test.name,
                        trace_type=TraceType.REQUIREMENT_TO_TEST,
                        confidence=confidence,
                        is_automatic=True,
                        metadata={"auto_linked": True}
                    )
                    if link:
                        links.append(link)
            
            conn.close()
            logger.info(f"自动关联测试用例: {len(links)} 个")
            
        except Exception as e:
            logger.error(f"自动关联测试失败: {e}")
        
        return links
    
    def _row_to_code_element(self, row: sqlite3.Row) -> CodeElement:
        return CodeElement(
            id=row['id'],
            name=row['name'],
            element_type=CodeElementType(row['element_type']),
            file_path=row['file_path'],
            line_start=row['line_start'],
            line_end=row['line_end'],
            module_name=row['module_name'],
            class_name=row['class_name'],
            docstring=row['docstring'],
            source_code=row['source_code'],
            keywords=json.loads(row['keywords']) if row['keywords'] else [],
            dependencies=json.loads(row['dependencies']) if row['dependencies'] else [],
            called_by=json.loads(row['called_by']) if row['called_by'] else [],
            complexity=row['complexity'] or 1
        )
    
    def _row_to_test_case(self, row: sqlite3.Row) -> TestCase:
        return TestCase(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            test_type=TestType(row['test_type']),
            scenario=row['scenario'],
            given=row['given'],
            when=row['when'],
            then=row['then'],
            priority=row['priority'],
            status=row['status'],
            execution_result=row['execution_result'],
            execution_time=row['execution_time'],
            duration_ms=row['duration_ms'],
            tags=json.loads(row['tags']) if row['tags'] else [],
            created_at=row['created_at']
        )
    
    def _row_to_requirement(self, row: sqlite3.Row) -> RequirementNode:
        return RequirementNode(
            id=row['id'],
            name=row['name'],
            requirement_type=RequirementType(row['requirement_type']),
            description=row['description'],
            priority=row['priority'],
            status=row['status'],
            version=row['version'],
            parent_id=row['parent_id'],
            tags=json.loads(row['tags']) if row['tags'] else [],
            acceptance_criteria=json.loads(row['acceptance_criteria']) if row['acceptance_criteria'] else [],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def calculate_coverage(self, project_id: str = None) -> Dict[str, Any]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as total FROM requirements')
            total_requirements = cursor.fetchone()['total']
            
            cursor.execute('''
                SELECT DISTINCT source_id FROM trace_links 
                WHERE source_type = 'requirement' AND trace_type = 'requirement_to_test'
            ''')
            covered_requirements = len(cursor.fetchall())
            
            cursor.execute('''
                SELECT status, COUNT(*) as count FROM trace_links 
                WHERE trace_type = 'requirement_to_test'
                GROUP BY status
            ''')
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute('SELECT COUNT(*) as total FROM test_cases')
            total_tests = cursor.fetchone()['total']
            
            cursor.execute('''
                SELECT execution_result, COUNT(*) as count FROM test_cases 
                WHERE execution_result IS NOT NULL
                GROUP BY execution_result
            ''')
            test_results = {row['execution_result']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute('''
                SELECT priority, COUNT(*) as count FROM requirements
                GROUP BY priority
            ''')
            by_priority = {}
            for row in cursor.fetchall():
                priority = row['priority']
                cursor.execute('''
                    SELECT COUNT(DISTINCT source_id) as covered FROM trace_links
                    WHERE source_type = 'requirement' AND trace_type = 'requirement_to_test'
                    AND source_id IN (SELECT id FROM requirements WHERE priority = ?)
                ''', (priority,))
                covered = cursor.fetchone()['covered']
                by_priority[priority] = {
                    "total": row['count'],
                    "covered": covered,
                    "coverage_rate": round(covered / row['count'] * 100, 2) if row['count'] > 0 else 0
                }
            
            cursor.execute('''
                SELECT requirement_type, COUNT(*) as count FROM requirements
                GROUP BY requirement_type
            ''')
            by_type = {}
            for row in cursor.fetchall():
                req_type = row['requirement_type']
                cursor.execute('''
                    SELECT COUNT(DISTINCT source_id) as covered FROM trace_links
                    WHERE source_type = 'requirement' AND trace_type = 'requirement_to_test'
                    AND source_id IN (SELECT id FROM requirements WHERE requirement_type = ?)
                ''', (req_type,))
                covered = cursor.fetchone()['covered']
                by_type[req_type] = {
                    "total": row['count'],
                    "covered": covered,
                    "coverage_rate": round(covered / row['count'] * 100, 2) if row['count'] > 0 else 0
                }
            
            conn.close()
            
            coverage_rate = (covered_requirements / total_requirements * 100) if total_requirements > 0 else 0
            verified_count = status_counts.get('verified', 0)
            verification_rate = (verified_count / covered_requirements * 100) if covered_requirements > 0 else 0
            
            return {
                "total_requirements": total_requirements,
                "covered_requirements": covered_requirements,
                "uncovered_requirements": total_requirements - covered_requirements,
                "coverage_rate": round(coverage_rate, 2),
                "verification_rate": round(verification_rate, 2),
                "trace_status": status_counts,
                "total_test_cases": total_tests,
                "test_results": test_results,
                "by_priority": by_priority,
                "by_type": by_type
            }
            
        except Exception as e:
            logger.error(f"计算覆盖率失败: {e}")
            return {}
    
    def calculate_code_coverage(self) -> Dict[str, Any]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as total FROM code_elements')
            total_code_elements = cursor.fetchone()['total']
            
            cursor.execute('''
                SELECT DISTINCT target_id FROM trace_links 
                WHERE target_type = 'code_element' AND trace_type = 'requirement_to_code'
            ''')
            linked_code_elements = len(cursor.fetchall())
            
            cursor.execute('''
                SELECT ce.element_type, COUNT(*) as count 
                FROM code_elements ce
                GROUP BY ce.element_type
            ''')
            elements_by_type = {row['element_type']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute('''
                SELECT ce.element_type, COUNT(DISTINCT ce.id) as count
                FROM code_elements ce
                INNER JOIN trace_links tl ON ce.id = tl.target_id AND tl.trace_type = 'requirement_to_code'
                GROUP BY ce.element_type
            ''')
            linked_by_type = {row['element_type']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute('''
                SELECT DISTINCT source_id FROM trace_links 
                WHERE source_type = 'requirement' AND trace_type = 'requirement_to_code'
            ''')
            requirements_with_code = len(cursor.fetchall())
            
            cursor.execute('''
                SELECT file_path, COUNT(*) as count
                FROM code_elements
                GROUP BY file_path
            ''')
            files_with_code = {row['file_path']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute('''
                SELECT ce.file_path, COUNT(DISTINCT ce.id) as count
                FROM code_elements ce
                INNER JOIN trace_links tl ON ce.id = tl.target_id AND tl.trace_type = 'requirement_to_code'
                GROUP BY ce.file_path
            ''')
            files_with_traces = {row['file_path']: row['count'] for row in cursor.fetchall()}
            
            conn.close()
            
            coverage_rate = (linked_code_elements / total_code_elements * 100) if total_code_elements > 0 else 0
            
            return {
                "total_code_elements": total_code_elements,
                "linked_code_elements": linked_code_elements,
                "unlinked_code_elements": total_code_elements - linked_code_elements,
                "coverage_rate": round(coverage_rate, 2),
                "elements_by_type": elements_by_type,
                "linked_by_type": linked_by_type,
                "requirements_with_code": requirements_with_code,
                "total_files": len(files_with_code),
                "files_with_traces": len(files_with_traces)
            }
            
        except Exception as e:
            logger.error(f"计算代码覆盖率失败: {e}")
            return {}
    
    def get_uncovered_requirements(self) -> List[RequirementNode]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT r.* FROM requirements r
                WHERE r.id NOT IN (
                    SELECT DISTINCT source_id FROM trace_links 
                    WHERE source_type = 'requirement' AND trace_type = 'requirement_to_test'
                )
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_requirement(row) for row in rows]
            
        except Exception as e:
            logger.error(f"获取未覆盖需求失败: {e}")
            return []
    
    def get_unlinked_code_elements(self) -> List[CodeElement]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ce.* FROM code_elements ce
                WHERE ce.id NOT IN (
                    SELECT DISTINCT target_id FROM trace_links 
                    WHERE target_type = 'code_element' AND trace_type = 'requirement_to_code'
                )
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_code_element(row) for row in rows]
            
        except Exception as e:
            logger.error(f"获取未关联代码元素失败: {e}")
            return []
    
    def get_orphaned_tests(self) -> List[TestCase]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT tc.* FROM test_cases tc
                WHERE tc.id NOT IN (
                    SELECT DISTINCT target_id FROM trace_links 
                    WHERE target_type = 'test_case'
                )
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_test_case(row) for row in rows]
            
        except Exception as e:
            logger.error(f"获取孤立测试失败: {e}")
            return []
    
    def get_trace_matrix(self, project_id: str = "default", project_name: str = "") -> TraceMatrix:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM requirements')
            req_rows = cursor.fetchall()
            requirements = [self._row_to_requirement(row) for row in req_rows]
            
            cursor.execute('SELECT * FROM test_cases')
            test_rows = cursor.fetchall()
            test_cases = [self._row_to_test_case(row) for row in test_rows]
            
            cursor.execute('SELECT * FROM code_elements')
            code_rows = cursor.fetchall()
            code_elements = [self._row_to_code_element(row) for row in code_rows]
            
            cursor.execute('SELECT * FROM trace_links')
            link_rows = cursor.fetchall()
            trace_links = [self._row_to_trace_link(row) for row in link_rows]
            
            conn.close()
            
            coverage_stats = self.calculate_coverage(project_id)
            code_coverage_stats = self.calculate_code_coverage()
            
            quality_metrics = self._calculate_quality_metrics(requirements, test_cases, trace_links)
            
            return TraceMatrix(
                project_id=project_id,
                project_name=project_name,
                requirements=requirements,
                test_cases=test_cases,
                code_elements=code_elements,
                trace_links=trace_links,
                coverage_stats=coverage_stats,
                code_coverage_stats=code_coverage_stats,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            logger.error(f"获取追溯矩阵失败: {e}")
            raise
    
    def _calculate_quality_metrics(self, requirements: List[RequirementNode],
                                    test_cases: List[TestCase],
                                    trace_links: List[TraceLink]) -> Dict[str, Any]:
        total_traces = len(trace_links)
        automatic_traces = sum(1 for t in trace_links if t.is_automatic)
        verified_traces = sum(1 for t in trace_links if t.status == TraceStatus.VERIFIED)
        
        avg_confidence = sum(t.confidence for t in trace_links) / total_traces if total_traces > 0 else 0
        
        orphaned_tests = len(self.get_orphaned_tests())
        orphaned_code = len(self.get_unlinked_code_elements())
        
        trace_quality_score = (
            (verified_traces / total_traces * 0.4 if total_traces > 0 else 0) +
            (avg_confidence * 0.3) +
            ((1 - orphaned_tests / len(test_cases)) * 0.15 if test_cases else 0) +
            ((1 - automatic_traces / total_traces) * 0.15 if total_traces > 0 else 0)
        )
        
        return {
            "total_traces": total_traces,
            "automatic_traces": automatic_traces,
            "manual_traces": total_traces - automatic_traces,
            "verified_traces": verified_traces,
            "average_confidence": round(avg_confidence, 3),
            "orphaned_tests": orphaned_tests,
            "orphaned_code_elements": orphaned_code,
            "trace_quality_score": round(trace_quality_score, 3)
        }
    
    def generate_coverage_report(self) -> CoverageReport:
        coverage_stats = self.calculate_coverage()
        
        uncovered = self.get_uncovered_requirements()
        gaps = []
        for req in uncovered:
            gaps.append({
                "requirement_id": req.id,
                "requirement_name": req.name,
                "requirement_type": req.requirement_type.value if isinstance(req.requirement_type, RequirementType) else req.requirement_type,
                "priority": req.priority,
                "gap_type": "no_test_coverage"
            })
        
        recommendations = []
        if coverage_stats.get('coverage_rate', 0) < 80:
            recommendations.append(f"测试覆盖率仅为 {coverage_stats.get('coverage_rate', 0)}%，建议提高到80%以上")
        if coverage_stats.get('verification_rate', 0) < 50:
            recommendations.append(f"验证率仅为 {coverage_stats.get('verification_rate', 0)}%，建议增加追溯验证")
        if len(gaps) > 0:
            recommendations.append(f"发现 {len(gaps)} 个未覆盖需求，建议优先处理高优先级需求")
        
        orphaned_tests = len(self.get_orphaned_tests())
        if orphaned_tests > 0:
            recommendations.append(f"发现 {orphaned_tests} 个孤立测试用例，建议关联到相应需求")
        
        return CoverageReport(
            total_requirements=coverage_stats.get('total_requirements', 0),
            covered_requirements=coverage_stats.get('covered_requirements', 0),
            verified_requirements=coverage_stats.get('trace_status', {}).get('verified', 0),
            partial_requirements=coverage_stats.get('trace_status', {}).get('partial', 0),
            uncovered_requirements=coverage_stats.get('uncovered_requirements', 0),
            coverage_rate=coverage_stats.get('coverage_rate', 0),
            verification_rate=coverage_stats.get('verification_rate', 0),
            by_priority=coverage_stats.get('by_priority', {}),
            by_type=coverage_stats.get('by_type', {}),
            gaps=gaps,
            recommendations=recommendations
        )
    
    def generate_visualization(self, matrix: TraceMatrix) -> TraceVisualization:
        nodes: List[VisualizationNode] = []
        edges: List[VisualizationEdge] = []
        
        node_id_map: Dict[str, str] = {}
        node_counter = 0
        edge_counter = 0
        
        def get_node_id(original_id: str) -> str:
            nonlocal node_counter
            if original_id not in node_id_map:
                node_counter += 1
                node_id_map[original_id] = f"node_{node_counter}"
            return node_id_map[original_id]
        
        for req in matrix.requirements:
            node_id = get_node_id(req.id)
            nodes.append(VisualizationNode(
                id=node_id,
                label=req.name,
                node_type="requirement",
                status=req.status,
                color=self.TYPE_COLORS.get("requirement", "#409EFF"),
                metadata={
                    "requirement_type": req.requirement_type.value if isinstance(req.requirement_type, RequirementType) else req.requirement_type,
                    "priority": req.priority
                }
            ))
        
        for test in matrix.test_cases:
            node_id = get_node_id(test.id)
            status = test.execution_result or test.status
            nodes.append(VisualizationNode(
                id=node_id,
                label=test.name,
                node_type="test_case",
                status=status,
                color=self._get_status_color(status),
                metadata={"test_type": test.test_type.value if isinstance(test.test_type, TestType) else test.test_type}
            ))
        
        for code in matrix.code_elements:
            node_id = get_node_id(code.id)
            nodes.append(VisualizationNode(
                id=node_id,
                label=code.name,
                node_type="code_element",
                status="active",
                color=self.TYPE_COLORS.get(code.element_type.value, "#9B59B6"),
                metadata={
                    "file_path": code.file_path,
                    "element_type": code.element_type.value if isinstance(code.element_type, CodeElementType) else code.element_type
                }
            ))
        
        for link in matrix.trace_links:
            source_id = node_id_map.get(link.source_id)
            target_id = node_id_map.get(link.target_id)
            
            if source_id and target_id:
                edge_counter += 1
                edges.append(VisualizationEdge(
                    id=f"edge_{edge_counter}",
                    source=source_id,
                    target=target_id,
                    edge_type=link.trace_type.value,
                    status=link.status.value,
                    color=self.EDGE_COLORS.get(link.trace_type.value, "#909399"),
                    confidence=link.confidence,
                    is_automatic=link.is_automatic
                ))
        
        nodes = self._calculate_layout(nodes, edges)
        
        return TraceVisualization(
            nodes=nodes,
            edges=edges,
            title="需求追溯矩阵可视化"
        )
    
    def _get_status_color(self, status: str) -> str:
        return self.STATUS_COLORS.get(status, "#909399")
    
    def _calculate_layout(self, 
                          nodes: List[VisualizationNode],
                          edges: List[VisualizationEdge]) -> List[VisualizationNode]:
        
        levels: Dict[str, int] = {}
        
        type_order = {
            "requirement": 0,
            "user_story": 1,
            "feature": 1,
            "code_element": 2,
            "test_case": 3
        }
        
        for node in nodes:
            levels[node.id] = type_order.get(node.node_type, 0)
        
        for edge in edges:
            source_level = levels.get(edge.source, 0)
            target_level = levels.get(edge.target, 0)
            if target_level <= source_level:
                levels[edge.target] = source_level + 1
        
        level_nodes: Dict[int, List[VisualizationNode]] = {}
        for node in nodes:
            level = levels.get(node.id, 0)
            if level not in level_nodes:
                level_nodes[level] = []
            level_nodes[level].append(node)
        
        max_level = max(level_nodes.keys()) if level_nodes else 0
        
        for level, nodes_at_level in level_nodes.items():
            count = len(nodes_at_level)
            y = level * 180 + 50
            for i, node in enumerate(nodes_at_level):
                node.x = (i + 1) * (1200 / (count + 1))
                node.y = y
        
        return nodes
    
    def export_trace_matrix(self, format: str = "json") -> str:
        matrix = self.get_trace_matrix()
        
        if format == "json":
            return json.dumps(matrix.to_dict(), ensure_ascii=False, indent=2)
        elif format == "markdown":
            return self._matrix_to_markdown(matrix)
        elif format == "html":
            visualization = self.generate_visualization(matrix)
            return self._visualization_to_html(visualization, matrix)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def _matrix_to_markdown(self, matrix: TraceMatrix) -> str:
        lines = [
            "# 需求追溯矩阵",
            "",
            f"**生成时间**: {matrix.generated_at}",
            "",
            "## 测试覆盖统计",
            "",
            f"- 需求总数: {matrix.coverage_stats.get('total_requirements', 0)}",
            f"- 已覆盖: {matrix.coverage_stats.get('covered_requirements', 0)}",
            f"- 未覆盖: {matrix.coverage_stats.get('uncovered_requirements', 0)}",
            f"- 覆盖率: {matrix.coverage_stats.get('coverage_rate', 0)}%",
            f"- 验证率: {matrix.coverage_stats.get('verification_rate', 0)}%",
            f"- 测试用例数: {matrix.coverage_stats.get('total_test_cases', 0)}",
            "",
            "## 代码覆盖统计",
            "",
            f"- 代码元素总数: {matrix.code_coverage_stats.get('total_code_elements', 0)}",
            f"- 已关联: {matrix.code_coverage_stats.get('linked_code_elements', 0)}",
            f"- 未关联: {matrix.code_coverage_stats.get('unlinked_code_elements', 0)}",
            f"- 覆盖率: {matrix.code_coverage_stats.get('coverage_rate', 0)}%",
            "",
            "## 质量指标",
            "",
            f"- 追溯链接总数: {matrix.quality_metrics.get('total_traces', 0)}",
            f"- 自动追溯: {matrix.quality_metrics.get('automatic_traces', 0)}",
            f"- 已验证追溯: {matrix.quality_metrics.get('verified_traces', 0)}",
            f"- 平均置信度: {matrix.quality_metrics.get('average_confidence', 0)}",
            f"- 孤立测试: {matrix.quality_metrics.get('orphaned_tests', 0)}",
            f"- 质量评分: {matrix.quality_metrics.get('trace_quality_score', 0)}",
            "",
            "## 需求-测试追溯矩阵",
            "",
            "| 需求ID | 需求名称 | 类型 | 优先级 | 测试用例 | 状态 |",
            "|--------|----------|------|--------|----------|------|"
        ]
        
        req_test_map: Dict[str, List[Tuple[str, str, str]]] = {}
        for link in matrix.trace_links:
            if link.trace_type == TraceType.REQUIREMENT_TO_TEST:
                if link.source_id not in req_test_map:
                    req_test_map[link.source_id] = []
                req_test_map[link.source_id].append((link.target_id, link.target_name, link.status.value))
        
        for req in matrix.requirements:
            tests = req_test_map.get(req.id, [])
            test_str = ", ".join([f"{t[1]} ({t[2]})" for t in tests]) if tests else "-"
            status = "已覆盖" if tests else "未覆盖"
            req_type = req.requirement_type.value if isinstance(req.requirement_type, RequirementType) else req.requirement_type
            lines.append(f"| {req.id} | {req.name} | {req_type} | {req.priority} | {test_str} | {status} |")
        
        lines.extend([
            "",
            "## 需求-代码追溯矩阵",
            "",
            "| 需求ID | 需求名称 | 代码元素 | 类型 | 文件 |",
            "|--------|----------|----------|------|------|"
        ])
        
        req_code_map: Dict[str, List[Tuple[str, str, str, str]]] = {}
        for link in matrix.trace_links:
            if link.trace_type == TraceType.REQUIREMENT_TO_CODE:
                if link.source_id not in req_code_map:
                    req_code_map[link.source_id] = []
                code_elem = next((c for c in matrix.code_elements if c.id == link.target_id), None)
                if code_elem:
                    req_code_map[link.source_id].append((
                        link.target_id, 
                        link.target_name,
                        code_elem.element_type.value if isinstance(code_elem.element_type, CodeElementType) else code_elem.element_type,
                        code_elem.file_path
                    ))
        
        for req in matrix.requirements:
            codes = req_code_map.get(req.id, [])
            if codes:
                for code in codes:
                    lines.append(f"| {req.id} | {req.name} | {code[1]} | {code[2]} | {code[3]} |")
            else:
                lines.append(f"| {req.id} | {req.name} | - | - | - |")
        
        lines.extend([
            "",
            "## 未覆盖需求",
            ""
        ])
        
        uncovered = self.get_uncovered_requirements()
        if uncovered:
            for req in uncovered:
                req_type = req.requirement_type.value if isinstance(req.requirement_type, RequirementType) else req.requirement_type
                lines.append(f"- **{req.id}**: {req.name} ({req_type}) - 优先级: {req.priority}")
        else:
            lines.append("所有需求均已覆盖。")
        
        lines.extend([
            "",
            "## 覆盖率改进建议",
            ""
        ])
        
        report = self.generate_coverage_report()
        for rec in report.recommendations:
            lines.append(f"- {rec}")
        
        return '\n'.join(lines)
    
    def _visualization_to_html(self, visualization: TraceVisualization, matrix: TraceMatrix) -> str:
        html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>需求追溯矩阵可视化</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; padding: 20px; }
        .container { max-width: 1600px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #409EFF, #67C23A); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; text-align: center; }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
        .stat-value { font-size: 32px; font-weight: bold; color: #409EFF; }
        .stat-label { color: #909399; margin-top: 5px; font-size: 14px; }
        .chart-container { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
        .chart-title { font-size: 18px; font-weight: bold; margin-bottom: 15px; color: #303133; border-left: 4px solid #409EFF; padding-left: 10px; }
        #graph-chart { width: 100%; height: 700px; }
        .legend { display: flex; justify-content: center; gap: 30px; margin-top: 20px; flex-wrap: wrap; }
        .legend-item { display: flex; align-items: center; gap: 8px; }
        .legend-color { width: 20px; height: 20px; border-radius: 4px; }
        .quality-section { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px; }
        .quality-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
        .quality-title { font-size: 16px; font-weight: bold; color: #303133; margin-bottom: 10px; }
        .quality-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #EBEEF5; }
        .quality-item:last-child { border-bottom: none; }
        .quality-label { color: #606266; }
        .quality-value { font-weight: bold; color: #409EFF; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>需求追溯矩阵可视化</h1>
            <p>生成时间: ''' + visualization.generated_at + '''</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">''' + str(matrix.coverage_stats.get('total_requirements', 0)) + '''</div>
                <div class="stat-label">需求总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(matrix.coverage_stats.get('covered_requirements', 0)) + '''</div>
                <div class="stat-label">已覆盖需求</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(matrix.coverage_stats.get('coverage_rate', 0)) + '''%</div>
                <div class="stat-label">测试覆盖率</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(matrix.code_coverage_stats.get('linked_code_elements', 0)) + '''</div>
                <div class="stat-label">已关联代码</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(matrix.coverage_stats.get('total_test_cases', 0)) + '''</div>
                <div class="stat-label">测试用例</div>
            </div>
        </div>
        
        <div class="quality-section">
            <div class="quality-card">
                <div class="quality-title">追溯质量</div>
                <div class="quality-item"><span class="quality-label">追溯链接总数</span><span class="quality-value">''' + str(matrix.quality_metrics.get('total_traces', 0)) + '''</span></div>
                <div class="quality-item"><span class="quality-label">自动追溯</span><span class="quality-value">''' + str(matrix.quality_metrics.get('automatic_traces', 0)) + '''</span></div>
                <div class="quality-item"><span class="quality-label">已验证追溯</span><span class="quality-value">''' + str(matrix.quality_metrics.get('verified_traces', 0)) + '''</span></div>
            </div>
            <div class="quality-card">
                <div class="quality-title">置信度分析</div>
                <div class="quality-item"><span class="quality-label">平均置信度</span><span class="quality-value">''' + str(round(matrix.quality_metrics.get('average_confidence', 0) * 100, 1)) + '''%</span></div>
                <div class="quality-item"><span class="quality-label">质量评分</span><span class="quality-value">''' + str(round(matrix.quality_metrics.get('trace_quality_score', 0) * 100, 1)) + '''%</span></div>
                <div class="quality-item"><span class="quality-label">验证率</span><span class="quality-value">''' + str(matrix.coverage_stats.get('verification_rate', 0)) + '''%</span></div>
            </div>
            <div class="quality-card">
                <div class="quality-title">孤立项</div>
                <div class="quality-item"><span class="quality-label">孤立测试</span><span class="quality-value">''' + str(matrix.quality_metrics.get('orphaned_tests', 0)) + '''</span></div>
                <div class="quality-item"><span class="quality-label">孤立代码</span><span class="quality-value">''' + str(matrix.quality_metrics.get('orphaned_code_elements', 0)) + '''</span></div>
                <div class="quality-item"><span class="quality-label">未覆盖需求</span><span class="quality-value">''' + str(matrix.coverage_stats.get('uncovered_requirements', 0)) + '''</span></div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">追溯关系图</div>
            <div id="graph-chart"></div>
            <div class="legend">
                <div class="legend-item"><div class="legend-color" style="background: #409EFF;"></div><span>需求</span></div>
                <div class="legend-item"><div class="legend-color" style="background: #F56C6C;"></div><span>测试用例</span></div>
                <div class="legend-item"><div class="legend-color" style="background: #9B59B6;"></div><span>代码元素</span></div>
                <div class="legend-item"><div class="legend-color" style="background: #67C23A;"></div><span>已覆盖</span></div>
                <div class="legend-item"><div class="legend-color" style="background: #909399;"></div><span>自动追溯</span></div>
            </div>
        </div>
    </div>
    
    <script>
        const graphData = ''' + json.dumps(visualization.to_dict(), ensure_ascii=False) + ''';
        const chart = echarts.init(document.getElementById('graph-chart'));
        const option = {
            tooltip: { 
                trigger: 'item',
                formatter: function(params) {
                    if (params.dataType === 'node') {
                        return params.data.label + '<br/>类型: ' + params.data.type + '<br/>状态: ' + params.data.status;
                    } else {
                        return '追溯链接<br/>置信度: ' + (params.data.confidence * 100).toFixed(1) + '%';
                    }
                }
            },
            series: [{
                type: 'graph',
                layout: 'none',
                symbolSize: 40,
                roam: true,
                label: { show: true, position: 'bottom', fontSize: 11 },
                edgeSymbol: ['none', 'arrow'],
                edgeSymbolSize: [4, 10],
                data: graphData.nodes.map(n => ({
                    id: n.id, name: n.label, label: n.label, type: n.type, status: n.status, x: n.x, y: n.y,
                    itemStyle: { color: n.color },
                    symbolSize: n.type === 'requirement' ? 50 : 35
                })),
                links: graphData.edges.map(e => ({
                    source: e.source, target: e.target, confidence: e.confidence,
                    lineStyle: { color: e.color, width: e.width, type: e.is_automatic ? 'dashed' : 'solid' }
                })),
                lineStyle: { opacity: 0.8, width: 2, curveness: 0.1 }
            }]
        };
        chart.setOption(option);
        window.addEventListener('resize', () => chart.resize());
    </script>
</body>
</html>'''
        return html_template
    
    def save_html_report(self, output_path: str) -> str:
        matrix = self.get_trace_matrix()
        visualization = self.generate_visualization(matrix)
        html_content = self._visualization_to_html(visualization, matrix)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML报告已保存: {output_path}")
        return output_path
    
    def delete_trace_link(self, trace_id: str) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM trace_history WHERE trace_id = ?', (trace_id,))
            cursor.execute('DELETE FROM trace_links WHERE id = ?', (trace_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"删除追溯链接: {trace_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除追溯链接失败: {e}")
            return False
    
    def batch_create_trace_links(self, 
                                  trace_links_data: List[Dict[str, Any]]) -> List[TraceLink]:
        """
        批量创建追溯链接
        
        Args:
            trace_links_data: 追溯链接数据列表，每个元素包含创建追溯链接所需的参数
            
        Returns:
            创建成功的追溯链接列表
        """
        created_links = []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            for link_data in trace_links_data:
                link_id = self._generate_id("TL")
                
                cursor.execute('''
                    INSERT INTO trace_links 
                    (id, source_type, source_id, source_name, target_type, target_id, target_name, 
                     trace_type, status, confidence, is_automatic, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (link_id, link_data['source_type'], link_data['source_id'], link_data['source_name'],
                      link_data['target_type'], link_data['target_id'], link_data['target_name'],
                      link_data['trace_type'].value, TraceStatus.PENDING.value, 
                      link_data.get('confidence', 1.0), 1 if link_data.get('is_automatic', False) else 0,
                      now, now, json.dumps(link_data.get('metadata', {}), ensure_ascii=False)))
                
                created_links.append(TraceLink(
                    id=link_id,
                    source_type=link_data['source_type'],
                    source_id=link_data['source_id'],
                    source_name=link_data['source_name'],
                    target_type=link_data['target_type'],
                    target_id=link_data['target_id'],
                    target_name=link_data['target_name'],
                    trace_type=link_data['trace_type'],
                    status=TraceStatus.PENDING,
                    confidence=link_data.get('confidence', 1.0),
                    is_automatic=link_data.get('is_automatic', False),
                    metadata=link_data.get('metadata', {})
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"批量创建追溯链接: {len(created_links)} 个")
            
        except Exception as e:
            logger.error(f"批量创建追溯链接失败: {e}")
        
        return created_links
    
    def batch_update_trace_status(self, 
                                   trace_updates: List[Dict[str, Any]]) -> int:
        """
        批量更新追溯状态
        
        Args:
            trace_updates: 更新数据列表，每个元素包含 trace_id, status, verified_by
            
        Returns:
            成功更新的数量
        """
        updated_count = 0
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            for update in trace_updates:
                trace_id = update['trace_id']
                status = update['status']
                verified_by = update.get('verified_by')
                
                cursor.execute('''
                    UPDATE trace_links 
                    SET status = ?, verified_by = ?, verified_at = ?, updated_at = ? 
                    WHERE id = ?
                ''', (status.value, verified_by, now if verified_by else None, now, trace_id))
                
                cursor.execute('''
                    INSERT INTO trace_history (trace_id, action, new_status, changed_by, changed_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (trace_id, 'batch_status_change', status.value, verified_by or 'system', now))
                
                updated_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"批量更新追溯状态: {updated_count} 个")
            
        except Exception as e:
            logger.error(f"批量更新追溯状态失败: {e}")
        
        return updated_count
    
    def batch_delete_trace_links(self, trace_ids: List[str]) -> int:
        """
        批量删除追溯链接
        
        Args:
            trace_ids: 要删除的追溯链接ID列表
            
        Returns:
            成功删除的数量
        """
        deleted_count = 0
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for trace_id in trace_ids:
                cursor.execute('DELETE FROM trace_history WHERE trace_id = ?', (trace_id,))
                cursor.execute('DELETE FROM trace_links WHERE id = ?', (trace_id,))
                deleted_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"批量删除追溯链接: {deleted_count} 个")
            
        except Exception as e:
            logger.error(f"批量删除追溯链接失败: {e}")
        
        return deleted_count
    
    def check_trace_integrity(self) -> TraceIntegrityReport:
        """
        检查追溯完整性
        
        Returns:
            追溯完整性检查报告
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as total FROM trace_links')
            total_traces = cursor.fetchone()['total']
            
            cursor.execute('SELECT * FROM trace_links')
            all_traces = cursor.fetchall()
            
            valid_traces = 0
            invalid_traces = 0
            broken_links = []
            consistency_issues = []
            
            for trace in all_traces:
                is_valid = True
                
                if trace['source_type'] == 'requirement':
                    cursor.execute('SELECT id FROM requirements WHERE id = ?', (trace['source_id'],))
                    if not cursor.fetchone():
                        broken_links.append({
                            "trace_id": trace['id'],
                            "issue": "source_requirement_not_found",
                            "source_id": trace['source_id']
                        })
                        is_valid = False
                
                if trace['target_type'] == 'test_case':
                    cursor.execute('SELECT id FROM test_cases WHERE id = ?', (trace['target_id'],))
                    if not cursor.fetchone():
                        broken_links.append({
                            "trace_id": trace['id'],
                            "issue": "target_test_case_not_found",
                            "target_id": trace['target_id']
                        })
                        is_valid = False
                
                if trace['target_type'] == 'code_element':
                    cursor.execute('SELECT id FROM code_elements WHERE id = ?', (trace['target_id'],))
                    if not cursor.fetchone():
                        broken_links.append({
                            "trace_id": trace['id'],
                            "issue": "target_code_element_not_found",
                            "target_id": trace['target_id']
                        })
                        is_valid = False
                
                if trace['confidence'] < 0.3:
                    consistency_issues.append({
                        "trace_id": trace['id'],
                        "issue": "low_confidence",
                        "confidence": trace['confidence']
                    })
                
                if is_valid:
                    valid_traces += 1
                else:
                    invalid_traces += 1
            
            orphaned_items = {
                "requirements": [r.id for r in self.get_uncovered_requirements()],
                "test_cases": [t.id for t in self.get_orphaned_tests()],
                "code_elements": [c.id for c in self.get_unlinked_code_elements()]
            }
            
            missing_traces = len(orphaned_items['requirements'])
            
            integrity_score = (valid_traces / total_traces * 100) if total_traces > 0 else 100
            
            recommendations = []
            if broken_links:
                recommendations.append(f"发现 {len(broken_links)} 个断裂的追溯链接，建议修复或删除")
            if consistency_issues:
                recommendations.append(f"发现 {len(consistency_issues)} 个一致性问题的追溯链接，建议重新验证")
            if orphaned_items['requirements']:
                recommendations.append(f"发现 {len(orphaned_items['requirements'])} 个未追溯的需求")
            if orphaned_items['test_cases']:
                recommendations.append(f"发现 {len(orphaned_items['test_cases'])} 个孤立的测试用例")
            
            conn.close()
            
            check_id = self._generate_id("IC")
            cursor = self._get_connection().cursor()
            cursor.execute('''
                INSERT INTO trace_integrity_checks (id, check_type, result, issues, checked_at, checked_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (check_id, 'full_integrity_check', 'completed' if integrity_score >= 80 else 'needs_attention',
                  json.dumps({"broken_links": broken_links, "consistency_issues": consistency_issues}, ensure_ascii=False),
                  datetime.now().isoformat(), 'system'))
            
            return TraceIntegrityReport(
                total_traces=total_traces,
                valid_traces=valid_traces,
                invalid_traces=invalid_traces,
                missing_traces=missing_traces,
                orphaned_items=orphaned_items,
                broken_links=broken_links,
                consistency_issues=consistency_issues,
                integrity_score=round(integrity_score, 2),
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"检查追溯完整性失败: {e}")
            return TraceIntegrityReport(
                total_traces=0, valid_traces=0, invalid_traces=0, missing_traces=0,
                orphaned_items={}, broken_links=[], consistency_issues=[],
                integrity_score=0, recommendations=[f"检查失败: {str(e)}"]
            )
    
    def analyze_impact(self, 
                       source_id: str, 
                       source_type: str,
                       change_type: str = "modification") -> ImpactAnalysisResult:
        """
        分析变更影响
        
        Args:
            source_id: 变更源ID
            source_type: 变更源类型 (requirement/test_case/code_element)
            change_type: 变更类型 (modification/deletion/addition)
            
        Returns:
            影响分析结果
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            source_name = ""
            affected_items = []
            impact_level = ImpactLevel.LOW
            risk_score = 0.0
            
            if source_type == "requirement":
                cursor.execute('SELECT * FROM requirements WHERE id = ?', (source_id,))
                req_row = cursor.fetchone()
                if req_row:
                    source_name = req_row['name']
                    
                    cursor.execute('''
                        SELECT * FROM trace_links WHERE source_id = ?
                    ''', (source_id,))
                    traces = cursor.fetchall()
                    
                    for trace in traces:
                        if trace['target_type'] == 'test_case':
                            cursor.execute('SELECT * FROM test_cases WHERE id = ?', (trace['target_id'],))
                            test = cursor.fetchone()
                            if test:
                                affected_items.append({
                                    "id": test['id'],
                                    "name": test['name'],
                                    "type": "test_case",
                                    "impact": "test_may_need_update",
                                    "trace_id": trace['id']
                                })
                        elif trace['target_type'] == 'code_element':
                            cursor.execute('SELECT * FROM code_elements WHERE id = ?', (trace['target_id'],))
                            code = cursor.fetchone()
                            if code:
                                affected_items.append({
                                    "id": code['id'],
                                    "name": code['name'],
                                    "type": "code_element",
                                    "file_path": code['file_path'],
                                    "impact": "code_may_need_refactor",
                                    "trace_id": trace['id']
                                })
                    
                    cursor.execute('SELECT priority FROM requirements WHERE id = ?', (source_id,))
                    priority_row = cursor.fetchone()
                    if priority_row:
                        priority = priority_row['priority']
                        if priority == 'high':
                            impact_level = ImpactLevel.HIGH
                            risk_score = 0.7
                        elif priority == 'medium':
                            impact_level = ImpactLevel.MEDIUM
                            risk_score = 0.5
                        else:
                            impact_level = ImpactLevel.LOW
                            risk_score = 0.3
            
            elif source_type == "test_case":
                cursor.execute('SELECT * FROM test_cases WHERE id = ?', (source_id,))
                test_row = cursor.fetchone()
                if test_row:
                    source_name = test_row['name']
                    
                    cursor.execute('''
                        SELECT * FROM trace_links WHERE target_id = ?
                    ''', (source_id,))
                    traces = cursor.fetchall()
                    
                    for trace in traces:
                        if trace['source_type'] == 'requirement':
                            cursor.execute('SELECT * FROM requirements WHERE id = ?', (trace['source_id'],))
                            req = cursor.fetchone()
                            if req:
                                affected_items.append({
                                    "id": req['id'],
                                    "name": req['name'],
                                    "type": "requirement",
                                    "impact": "requirement_verification_impacted",
                                    "trace_id": trace['id']
                                })
                    
                    impact_level = ImpactLevel.MEDIUM
                    risk_score = 0.5
            
            elif source_type == "code_element":
                cursor.execute('SELECT * FROM code_elements WHERE id = ?', (source_id,))
                code_row = cursor.fetchone()
                if code_row:
                    source_name = code_row['name']
                    
                    cursor.execute('''
                        SELECT * FROM trace_links WHERE target_id = ?
                    ''', (source_id,))
                    traces = cursor.fetchall()
                    
                    for trace in traces:
                        if trace['source_type'] == 'requirement':
                            cursor.execute('SELECT * FROM requirements WHERE id = ?', (trace['source_id'],))
                            req = cursor.fetchone()
                            if req:
                                affected_items.append({
                                    "id": req['id'],
                                    "name": req['name'],
                                    "type": "requirement",
                                    "impact": "requirement_implementation_changed",
                                    "trace_id": trace['id']
                                })
                    
                    cursor.execute('SELECT complexity FROM code_elements WHERE id = ?', (source_id,))
                    complexity_row = cursor.fetchone()
                    if complexity_row:
                        complexity = complexity_row['complexity']
                        if complexity >= 8:
                            impact_level = ImpactLevel.HIGH
                            risk_score = 0.8
                        elif complexity >= 5:
                            impact_level = ImpactLevel.MEDIUM
                            risk_score = 0.6
                        else:
                            impact_level = ImpactLevel.LOW
                            risk_score = 0.4
            
            if change_type == "deletion":
                if impact_level == ImpactLevel.MEDIUM:
                    impact_level = ImpactLevel.HIGH
                elif impact_level == ImpactLevel.LOW:
                    impact_level = ImpactLevel.MEDIUM
                risk_score = min(risk_score + 0.2, 1.0)
            
            risk_score = min(risk_score + len(affected_items) * 0.05, 1.0)
            
            recommendations = []
            if affected_items:
                recommendations.append(f"变更将影响 {len(affected_items)} 个相关项")
                test_count = sum(1 for item in affected_items if item['type'] == 'test_case')
                if test_count > 0:
                    recommendations.append(f"需要更新或重新执行 {test_count} 个测试用例")
                code_count = sum(1 for item in affected_items if item['type'] == 'code_element')
                if code_count > 0:
                    recommendations.append(f"需要检查或重构 {code_count} 个代码元素")
            if risk_score >= 0.7:
                recommendations.append("高风险变更，建议进行详细评审")
            
            conn.close()
            
            analysis_id = self._generate_id("IA")
            cursor = self._get_connection().cursor()
            cursor.execute('''
                INSERT INTO impact_analyses 
                (id, source_id, source_type, change_type, impact_level, affected_items, 
                 risk_score, recommendations, analyzed_at, analyzed_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (analysis_id, source_id, source_type, change_type, impact_level.value,
                  json.dumps(affected_items, ensure_ascii=False), risk_score,
                  json.dumps(recommendations, ensure_ascii=False),
                  datetime.now().isoformat(), 'system'))
            
            return ImpactAnalysisResult(
                source_id=source_id,
                source_name=source_name,
                source_type=source_type,
                change_type=change_type,
                affected_items=affected_items,
                impact_level=impact_level,
                risk_score=round(risk_score, 3),
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"分析变更影响失败: {e}")
            return ImpactAnalysisResult(
                source_id=source_id,
                source_name="",
                source_type=source_type,
                change_type=change_type,
                affected_items=[],
                impact_level=ImpactLevel.LOW,
                risk_score=0.0,
                recommendations=[f"分析失败: {str(e)}"]
            )
    
    def generate_test_trace_matrix_view(self, 
                                         dimension: str = "requirement",
                                         filters: Dict[str, Any] = None) -> TestTraceMatrixView:
        """
        生成需求-测试追溯矩阵视图
        
        Args:
            dimension: 维度类型 (requirement/test_type/priority/status)
            filters: 过滤条件
            
        Returns:
            测试追溯矩阵视图
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            filters = filters or {}
            
            data = []
            summary = {
                "total_requirements": 0,
                "total_tests": 0,
                "total_traces": 0,
                "coverage_rate": 0.0
            }
            
            if dimension == "requirement":
                cursor.execute('''
                    SELECT r.id, r.name, r.requirement_type, r.priority, r.status,
                           COUNT(DISTINCT tl.id) as test_count,
                           GROUP_CONCAT(tc.name, '|||') as test_names
                    FROM requirements r
                    LEFT JOIN trace_links tl ON r.id = tl.source_id AND tl.trace_type = 'requirement_to_test'
                    LEFT JOIN test_cases tc ON tl.target_id = tc.id
                    GROUP BY r.id
                ''')
                
                rows = cursor.fetchall()
                summary["total_requirements"] = len(rows)
                
                for row in rows:
                    test_names = row['test_names'].split('|||') if row['test_names'] else []
                    data.append({
                        "requirement_id": row['id'],
                        "requirement_name": row['name'],
                        "requirement_type": row['requirement_type'],
                        "priority": row['priority'],
                        "status": row['status'],
                        "test_count": row['test_count'],
                        "test_names": test_names,
                        "coverage_status": "已覆盖" if row['test_count'] > 0 else "未覆盖"
                    })
                    summary["total_traces"] += row['test_count']
                
                covered = sum(1 for d in data if d['test_count'] > 0)
                summary["coverage_rate"] = round(covered / len(rows) * 100, 2) if rows else 0
                
            elif dimension == "test_type":
                cursor.execute('''
                    SELECT tc.test_type, 
                           COUNT(DISTINCT tc.id) as test_count,
                           COUNT(DISTINCT tl.source_id) as linked_req_count,
                           GROUP_CONCAT(DISTINCT r.name, '|||') as requirement_names
                    FROM test_cases tc
                    LEFT JOIN trace_links tl ON tc.id = tl.target_id AND tl.trace_type = 'requirement_to_test'
                    LEFT JOIN requirements r ON tl.source_id = r.id
                    GROUP BY tc.test_type
                ''')
                
                rows = cursor.fetchall()
                
                for row in rows:
                    req_names = row['requirement_names'].split('|||') if row['requirement_names'] else []
                    data.append({
                        "test_type": row['test_type'],
                        "test_count": row['test_count'],
                        "linked_requirement_count": row['linked_req_count'],
                        "requirement_names": req_names,
                        "orphaned_tests": row['test_count'] - row['linked_req_count']
                    })
                    summary["total_tests"] += row['test_count']
                    summary["total_traces"] += row['linked_req_count']
                
            elif dimension == "priority":
                cursor.execute('''
                    SELECT r.priority,
                           COUNT(DISTINCT r.id) as req_count,
                           COUNT(DISTINCT tl.id) as trace_count,
                           SUM(CASE WHEN tl.id IS NOT NULL THEN 1 ELSE 0 END) as covered_count
                    FROM requirements r
                    LEFT JOIN trace_links tl ON r.id = tl.source_id AND tl.trace_type = 'requirement_to_test'
                    GROUP BY r.priority
                ''')
                
                rows = cursor.fetchall()
                
                for row in rows:
                    data.append({
                        "priority": row['priority'],
                        "requirement_count": row['req_count'],
                        "trace_count": row['trace_count'],
                        "covered_requirements": row['covered_count'] if row['covered_count'] else 0,
                        "coverage_rate": round((row['covered_count'] or 0) / row['req_count'] * 100, 2) if row['req_count'] > 0 else 0
                    })
                    summary["total_requirements"] += row['req_count']
                    summary["total_traces"] += row['trace_count'] or 0
                    
            elif dimension == "status":
                cursor.execute('''
                    SELECT tl.status,
                           COUNT(DISTINCT tl.id) as trace_count,
                           COUNT(DISTINCT tl.source_id) as req_count,
                           COUNT(DISTINCT tl.target_id) as test_count
                    FROM trace_links tl
                    WHERE tl.trace_type = 'requirement_to_test'
                    GROUP BY tl.status
                ''')
                
                rows = cursor.fetchall()
                
                for row in rows:
                    data.append({
                        "trace_status": row['status'],
                        "trace_count": row['trace_count'],
                        "requirement_count": row['req_count'],
                        "test_count": row['test_count']
                    })
                    summary["total_traces"] += row['trace_count']
            
            conn.close()
            
            view_name = f"需求-测试追溯矩阵({dimension}维度)"
            
            return TestTraceMatrixView(
                view_name=view_name,
                dimension=dimension,
                data=data,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"生成测试追溯矩阵视图失败: {e}")
            return TestTraceMatrixView(
                view_name="需求-测试追溯矩阵",
                dimension=dimension,
                data=[],
                summary={}
            )
    
    def generate_code_trace_matrix_view(self,
                                         dimension: str = "requirement",
                                         filters: Dict[str, Any] = None) -> CodeTraceMatrixView:
        """
        生成需求-代码追溯矩阵视图
        
        Args:
            dimension: 维度类型 (requirement/file/module/element_type)
            filters: 过滤条件
            
        Returns:
            代码追溯矩阵视图
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            filters = filters or {}
            
            data = []
            summary = {
                "total_requirements": 0,
                "total_code_elements": 0,
                "total_traces": 0,
                "coverage_rate": 0.0
            }
            
            file_coverage = {}
            module_coverage = {}
            
            if dimension == "requirement":
                cursor.execute('''
                    SELECT r.id, r.name, r.requirement_type, r.priority,
                           COUNT(DISTINCT tl.id) as code_count,
                           GROUP_CONCAT(ce.name, '|||') as code_names,
                           GROUP_CONCAT(ce.file_path, '|||') as file_paths
                    FROM requirements r
                    LEFT JOIN trace_links tl ON r.id = tl.source_id AND tl.trace_type = 'requirement_to_code'
                    LEFT JOIN code_elements ce ON tl.target_id = ce.id
                    GROUP BY r.id
                ''')
                
                rows = cursor.fetchall()
                summary["total_requirements"] = len(rows)
                
                for row in rows:
                    code_names = row['code_names'].split('|||') if row['code_names'] else []
                    file_paths = list(set(row['file_paths'].split('|||'))) if row['file_paths'] else []
                    data.append({
                        "requirement_id": row['id'],
                        "requirement_name": row['name'],
                        "requirement_type": row['requirement_type'],
                        "priority": row['priority'],
                        "code_count": row['code_count'],
                        "code_names": code_names,
                        "file_paths": file_paths,
                        "implementation_status": "已实现" if row['code_count'] > 0 else "未实现"
                    })
                    summary["total_traces"] += row['code_count']
                
                implemented = sum(1 for d in data if d['code_count'] > 0)
                summary["coverage_rate"] = round(implemented / len(rows) * 100, 2) if rows else 0
                
            elif dimension == "file":
                cursor.execute('''
                    SELECT ce.file_path,
                           COUNT(DISTINCT ce.id) as code_count,
                           COUNT(DISTINCT tl.id) as trace_count,
                           COUNT(DISTINCT tl.source_id) as req_count,
                           GROUP_CONCAT(DISTINCT r.name, '|||') as requirement_names
                    FROM code_elements ce
                    LEFT JOIN trace_links tl ON ce.id = tl.target_id AND tl.trace_type = 'requirement_to_code'
                    LEFT JOIN requirements r ON tl.source_id = r.id
                    GROUP BY ce.file_path
                ''')
                
                rows = cursor.fetchall()
                
                for row in rows:
                    req_names = row['requirement_names'].split('|||') if row['requirement_names'] else []
                    data.append({
                        "file_path": row['file_path'],
                        "code_element_count": row['code_count'],
                        "trace_count": row['trace_count'],
                        "linked_requirement_count": row['req_count'],
                        "requirement_names": req_names,
                        "coverage_status": "已追溯" if row['trace_count'] > 0 else "未追溯"
                    })
                    summary["total_code_elements"] += row['code_count']
                    summary["total_traces"] += row['trace_count'] or 0
                    file_coverage[row['file_path']] = {
                        "code_count": row['code_count'],
                        "trace_count": row['trace_count'] or 0
                    }
                
            elif dimension == "module":
                cursor.execute('''
                    SELECT ce.module_name,
                           COUNT(DISTINCT ce.id) as code_count,
                           COUNT(DISTINCT tl.id) as trace_count,
                           COUNT(DISTINCT tl.source_id) as req_count,
                           GROUP_CONCAT(DISTINCT r.name, '|||') as requirement_names
                    FROM code_elements ce
                    LEFT JOIN trace_links tl ON ce.id = tl.target_id AND tl.trace_type = 'requirement_to_code'
                    LEFT JOIN requirements r ON tl.source_id = r.id
                    GROUP BY ce.module_name
                ''')
                
                rows = cursor.fetchall()
                
                for row in rows:
                    req_names = row['requirement_names'].split('|||') if row['requirement_names'] else []
                    data.append({
                        "module_name": row['module_name'],
                        "code_element_count": row['code_count'],
                        "trace_count": row['trace_count'],
                        "linked_requirement_count": row['req_count'],
                        "requirement_names": req_names
                    })
                    summary["total_code_elements"] += row['code_count']
                    summary["total_traces"] += row['trace_count'] or 0
                    module_coverage[row['module_name']] = {
                        "code_count": row['code_count'],
                        "trace_count": row['trace_count'] or 0
                    }
                
            elif dimension == "element_type":
                cursor.execute('''
                    SELECT ce.element_type,
                           COUNT(DISTINCT ce.id) as code_count,
                           COUNT(DISTINCT tl.id) as trace_count,
                           COUNT(DISTINCT tl.source_id) as req_count
                    FROM code_elements ce
                    LEFT JOIN trace_links tl ON ce.id = tl.target_id AND tl.trace_type = 'requirement_to_code'
                    GROUP BY ce.element_type
                ''')
                
                rows = cursor.fetchall()
                
                for row in rows:
                    data.append({
                        "element_type": row['element_type'],
                        "code_count": row['code_count'],
                        "trace_count": row['trace_count'] or 0,
                        "linked_requirement_count": row['req_count'] or 0,
                        "coverage_rate": round((row['trace_count'] or 0) / row['code_count'] * 100, 2) if row['code_count'] > 0 else 0
                    })
                    summary["total_code_elements"] += row['code_count']
                    summary["total_traces"] += row['trace_count'] or 0
            
            conn.close()
            
            view_name = f"需求-代码追溯矩阵({dimension}维度)"
            
            return CodeTraceMatrixView(
                view_name=view_name,
                dimension=dimension,
                data=data,
                summary=summary,
                file_coverage=file_coverage,
                module_coverage=module_coverage
            )
            
        except Exception as e:
            logger.error(f"生成代码追溯矩阵视图失败: {e}")
            return CodeTraceMatrixView(
                view_name="需求-代码追溯矩阵",
                dimension=dimension,
                data=[],
                summary={},
                file_coverage={},
                module_coverage={}
            )
    
    def record_code_change(self,
                           code_element_id: str,
                           change_type: str,
                           old_value: str = None,
                           new_value: str = None,
                           changed_by: str = "system",
                           commit_id: str = None,
                           description: str = "") -> CodeChangeRecord:
        """
        记录代码变更
        
        Args:
            code_element_id: 代码元素ID
            change_type: 变更类型 (created/modified/deleted/refactored)
            old_value: 旧值
            new_value: 新值
            changed_by: 变更人
            commit_id: 提交ID
            description: 变更描述
            
        Returns:
            代码变更记录
        """
        try:
            change_id = self._generate_id("CC")
            now = datetime.now().isoformat()
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO code_changes 
                (id, code_element_id, change_type, old_value, new_value, changed_by, 
                 changed_at, commit_id, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (change_id, code_element_id, change_type, old_value, new_value, 
                  changed_by, now, commit_id, description))
            
            conn.commit()
            conn.close()
            
            logger.info(f"记录代码变更: {change_id} - {change_type}")
            
            return CodeChangeRecord(
                id=change_id,
                code_element_id=code_element_id,
                change_type=change_type,
                old_value=old_value,
                new_value=new_value,
                changed_by=changed_by,
                changed_at=now,
                commit_id=commit_id,
                description=description
            )
            
        except Exception as e:
            logger.error(f"记录代码变更失败: {e}")
            raise
    
    def get_code_change_history(self, 
                                 code_element_id: str,
                                 limit: int = 50) -> List[CodeChangeRecord]:
        """
        获取代码变更历史
        
        Args:
            code_element_id: 代码元素ID
            limit: 返回记录数量限制
            
        Returns:
            代码变更记录列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM code_changes 
                WHERE code_element_id = ?
                ORDER BY changed_at DESC
                LIMIT ?
            ''', (code_element_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [CodeChangeRecord(
                id=row['id'],
                code_element_id=row['code_element_id'],
                change_type=row['change_type'],
                old_value=row['old_value'],
                new_value=row['new_value'],
                changed_by=row['changed_by'],
                changed_at=row['changed_at'],
                commit_id=row['commit_id'],
                description=row['description']
            ) for row in rows]
            
        except Exception as e:
            logger.error(f"获取代码变更历史失败: {e}")
            return []
    
    def get_bidirectional_traces(self, item_id: str, item_type: str) -> Dict[str, Any]:
        """
        获取双向追溯信息
        
        Args:
            item_id: 项目ID
            item_type: 项目类型 (requirement/test_case/code_element)
            
        Returns:
            双向追溯信息字典
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            forward_traces = []
            backward_traces = []
            
            if item_type == "requirement":
                cursor.execute('''
                    SELECT tl.*, tc.name as target_name, tc.test_type
                    FROM trace_links tl
                    LEFT JOIN test_cases tc ON tl.target_id = tc.id
                    WHERE tl.source_id = ? AND tl.trace_type = 'requirement_to_test'
                ''', (item_id,))
                
                for row in cursor.fetchall():
                    forward_traces.append({
                        "trace_id": row['id'],
                        "target_type": "test_case",
                        "target_id": row['target_id'],
                        "target_name": row['target_name'],
                        "test_type": row['test_type'],
                        "status": row['status'],
                        "confidence": row['confidence']
                    })
                
                cursor.execute('''
                    SELECT tl.*, ce.name as target_name, ce.file_path, ce.element_type
                    FROM trace_links tl
                    LEFT JOIN code_elements ce ON tl.target_id = ce.id
                    WHERE tl.source_id = ? AND tl.trace_type = 'requirement_to_code'
                ''', (item_id,))
                
                for row in cursor.fetchall():
                    forward_traces.append({
                        "trace_id": row['id'],
                        "target_type": "code_element",
                        "target_id": row['target_id'],
                        "target_name": row['target_name'],
                        "file_path": row['file_path'],
                        "element_type": row['element_type'],
                        "status": row['status'],
                        "confidence": row['confidence']
                    })
                
            elif item_type == "test_case":
                cursor.execute('''
                    SELECT tl.*, r.name as source_name, r.requirement_type, r.priority
                    FROM trace_links tl
                    LEFT JOIN requirements r ON tl.source_id = r.id
                    WHERE tl.target_id = ? AND tl.trace_type = 'requirement_to_test'
                ''', (item_id,))
                
                for row in cursor.fetchall():
                    backward_traces.append({
                        "trace_id": row['id'],
                        "source_type": "requirement",
                        "source_id": row['source_id'],
                        "source_name": row['source_name'],
                        "requirement_type": row['requirement_type'],
                        "priority": row['priority'],
                        "status": row['status'],
                        "confidence": row['confidence']
                    })
                
            elif item_type == "code_element":
                cursor.execute('''
                    SELECT tl.*, r.name as source_name, r.requirement_type, r.priority
                    FROM trace_links tl
                    LEFT JOIN requirements r ON tl.source_id = r.id
                    WHERE tl.target_id = ? AND tl.trace_type = 'requirement_to_code'
                ''', (item_id,))
                
                for row in cursor.fetchall():
                    backward_traces.append({
                        "trace_id": row['id'],
                        "source_type": "requirement",
                        "source_id": row['source_id'],
                        "source_name": row['source_name'],
                        "requirement_type": row['requirement_type'],
                        "priority": row['priority'],
                        "status": row['status'],
                        "confidence": row['confidence']
                    })
            
            conn.close()
            
            return {
                "item_id": item_id,
                "item_type": item_type,
                "forward_traces": forward_traces,
                "backward_traces": backward_traces,
                "forward_count": len(forward_traces),
                "backward_count": len(backward_traces),
                "total_traces": len(forward_traces) + len(backward_traces)
            }
            
        except Exception as e:
            logger.error(f"获取双向追溯信息失败: {e}")
            return {
                "item_id": item_id,
                "item_type": item_type,
                "forward_traces": [],
                "backward_traces": [],
                "forward_count": 0,
                "backward_count": 0,
                "total_traces": 0
            }
    
    def generate_enhanced_visualization(self,
                                        layout_type: str = "hierarchical",
                                        filters: Dict[str, Any] = None) -> EnhancedVisualization:
        """
        生成增强的可视化数据
        
        Args:
            layout_type: 布局类型 (hierarchical/force/radial/tree)
            filters: 过滤条件
            
        Returns:
            增强的可视化数据
        """
        try:
            matrix = self.get_trace_matrix()
            filters = filters or {}
            
            nodes: List[VisualizationNode] = []
            edges: List[VisualizationEdge] = []
            
            node_id_map: Dict[str, str] = {}
            node_counter = 0
            edge_counter = 0
            
            def get_node_id(original_id: str) -> str:
                nonlocal node_counter
                if original_id not in node_id_map:
                    node_counter += 1
                    node_id_map[original_id] = f"node_{node_counter}"
                return node_id_map[original_id]
            
            for req in matrix.requirements:
                if filters.get('requirement_types') and req.requirement_type.value not in filters['requirement_types']:
                    continue
                if filters.get('priorities') and req.priority not in filters['priorities']:
                    continue
                    
                node_id = get_node_id(req.id)
                nodes.append(VisualizationNode(
                    id=node_id,
                    label=req.name,
                    node_type="requirement",
                    status=req.status,
                    color=self.TYPE_COLORS.get("requirement", "#409EFF"),
                    metadata={
                        "requirement_type": req.requirement_type.value,
                        "priority": req.priority,
                        "description": req.description[:100] if req.description else ""
                    }
                ))
            
            for test in matrix.test_cases:
                if filters.get('test_types') and test.test_type.value not in filters['test_types']:
                    continue
                    
                node_id = get_node_id(test.id)
                status = test.execution_result or test.status
                nodes.append(VisualizationNode(
                    id=node_id,
                    label=test.name,
                    node_type="test_case",
                    status=status,
                    color=self._get_status_color(status),
                    metadata={
                        "test_type": test.test_type.value,
                        "scenario": test.scenario
                    }
                ))
            
            for code in matrix.code_elements:
                if filters.get('element_types') and code.element_type.value not in filters['element_types']:
                    continue
                if filters.get('file_patterns') and not any(p in code.file_path for p in filters['file_patterns']):
                    continue
                    
                node_id = get_node_id(code.id)
                nodes.append(VisualizationNode(
                    id=node_id,
                    label=code.name,
                    node_type="code_element",
                    status="active",
                    color=self.TYPE_COLORS.get(code.element_type.value, "#9B59B6"),
                    metadata={
                        "file_path": code.file_path,
                        "element_type": code.element_type.value,
                        "complexity": code.complexity
                    }
                ))
            
            for link in matrix.trace_links:
                source_id = node_id_map.get(link.source_id)
                target_id = node_id_map.get(link.target_id)
                
                if source_id and target_id:
                    edge_counter += 1
                    edges.append(VisualizationEdge(
                        id=f"edge_{edge_counter}",
                        source=source_id,
                        target=target_id,
                        edge_type=link.trace_type.value,
                        status=link.status.value,
                        color=self.EDGE_COLORS.get(link.trace_type.value, "#909399"),
                        confidence=link.confidence,
                        is_automatic=link.is_automatic
                    ))
            
            nodes = self._apply_layout(nodes, edges, layout_type)
            
            statistics = {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": {},
                "edge_types": {}
            }
            
            for node in nodes:
                statistics["node_types"][node.node_type] = statistics["node_types"].get(node.node_type, 0) + 1
            
            for edge in edges:
                statistics["edge_types"][edge.edge_type] = statistics["edge_types"].get(edge.edge_type, 0) + 1
            
            interactive_options = {
                "zoom": True,
                "pan": True,
                "node_selection": True,
                "edge_highlight": True,
                "tooltip": True,
                "search": True,
                "filter": True,
                "export_formats": ["json", "png", "svg"]
            }
            
            return EnhancedVisualization(
                nodes=nodes,
                edges=edges,
                layout_type=layout_type,
                title="增强需求追溯矩阵可视化",
                filters=filters,
                statistics=statistics,
                interactive_options=interactive_options
            )
            
        except Exception as e:
            logger.error(f"生成增强可视化失败: {e}")
            return EnhancedVisualization(
                nodes=[],
                edges=[],
                layout_type=layout_type,
                title="需求追溯矩阵可视化",
                filters=filters or {},
                statistics={},
                interactive_options={}
            )
    
    def _apply_layout(self,
                      nodes: List[VisualizationNode],
                      edges: List[VisualizationEdge],
                      layout_type: str) -> List[VisualizationNode]:
        """
        应用布局算法
        
        Args:
            nodes: 节点列表
            edges: 边列表
            layout_type: 布局类型
            
        Returns:
            应用布局后的节点列表
        """
        if layout_type == "hierarchical":
            return self._apply_hierarchical_layout(nodes, edges)
        elif layout_type == "radial":
            return self._apply_radial_layout(nodes, edges)
        elif layout_type == "tree":
            return self._apply_tree_layout(nodes, edges)
        else:
            return self._apply_force_layout(nodes, edges)
    
    def _apply_hierarchical_layout(self,
                                    nodes: List[VisualizationNode],
                                    edges: List[VisualizationEdge]) -> List[VisualizationNode]:
        """应用层次布局"""
        levels: Dict[str, int] = {}
        
        type_order = {
            "requirement": 0,
            "user_story": 1,
            "feature": 1,
            "code_element": 2,
            "test_case": 3
        }
        
        for node in nodes:
            levels[node.id] = type_order.get(node.node_type, 0)
        
        for edge in edges:
            source_level = levels.get(edge.source, 0)
            target_level = levels.get(edge.target, 0)
            if target_level <= source_level:
                levels[edge.target] = source_level + 1
        
        level_nodes: Dict[int, List[VisualizationNode]] = {}
        for node in nodes:
            level = levels.get(node.id, 0)
            if level not in level_nodes:
                level_nodes[level] = []
            level_nodes[level].append(node)
        
        for level, nodes_at_level in level_nodes.items():
            count = len(nodes_at_level)
            y = level * 180 + 50
            for i, node in enumerate(nodes_at_level):
                node.x = (i + 1) * (1200 / (count + 1))
                node.y = y
        
        return nodes
    
    def _apply_radial_layout(self,
                              nodes: List[VisualizationNode],
                              edges: List[VisualizationEdge]) -> List[VisualizationNode]:
        """应用径向布局"""
        import math
        
        center_x = 600
        center_y = 400
        
        type_rings = {
            "requirement": 100,
            "code_element": 200,
            "test_case": 300
        }
        
        type_nodes: Dict[str, List[VisualizationNode]] = {}
        for node in nodes:
            node_type = node.node_type
            if node_type not in type_nodes:
                type_nodes[node_type] = []
            type_nodes[node_type].append(node)
        
        for node_type, nodes_of_type in type_nodes.items():
            radius = type_rings.get(node_type, 150)
            count = len(nodes_of_type)
            angle_step = 2 * math.pi / count if count > 0 else 0
            
            for i, node in enumerate(nodes_of_type):
                angle = i * angle_step
                node.x = center_x + radius * math.cos(angle)
                node.y = center_y + radius * math.sin(angle)
        
        return nodes
    
    def _apply_tree_layout(self,
                           nodes: List[VisualizationNode],
                           edges: List[VisualizationEdge]) -> List[VisualizationNode]:
        """应用树形布局"""
        children_map: Dict[str, List[str]] = {}
        parent_map: Dict[str, str] = {}
        
        for edge in edges:
            if edge.source not in children_map:
                children_map[edge.source] = []
            children_map[edge.source].append(edge.target)
            parent_map[edge.target] = edge.source
        
        roots = [n.id for n in nodes if n.id not in parent_map]
        
        def calculate_positions(node_id: str, x: float, y: float, level: int, width: float):
            node = next((n for n in nodes if n.id == node_id), None)
            if node:
                node.x = x
                node.y = y
                
                children = children_map.get(node_id, [])
                if children:
                    child_width = width / max(len(children), 1)
                    for i, child_id in enumerate(children):
                        child_x = x - width/2 + child_width * (i + 0.5)
                        child_y = y + 120
                        calculate_positions(child_id, child_x, child_y, level + 1, child_width)
        
        if roots:
            root_width = 1200 / max(len(roots), 1)
            for i, root_id in enumerate(roots):
                calculate_positions(root_id, root_width * (i + 0.5), 50, 0, root_width)
        
        return nodes
    
    def _apply_force_layout(self,
                            nodes: List[VisualizationNode],
                            edges: List[VisualizationEdge]) -> List[VisualizationNode]:
        """应用力导向布局（简化版）"""
        import random
        import math
        
        for node in nodes:
            node.x = random.uniform(100, 1100)
            node.y = random.uniform(100, 700)
        
        iterations = 50
        k = 100
        
        for _ in range(iterations):
            for i, node1 in enumerate(nodes):
                fx, fy = 0, 0
                
                for j, node2 in enumerate(nodes):
                    if i != j:
                        dx = node1.x - node2.x
                        dy = node1.y - node2.y
                        distance = math.sqrt(dx*dx + dy*dy) + 0.1
                        
                        force = k * k / distance
                        fx += force * dx / distance
                        fy += force * dy / distance
                
                for edge in edges:
                    if edge.source == node1.id:
                        target = next((n for n in nodes if n.id == edge.target), None)
                        if target:
                            dx = node1.x - target.x
                            dy = node1.y - target.y
                            distance = math.sqrt(dx*dx + dy*dy) + 0.1
                            
                            force = distance * distance / k
                            fx -= force * dx / distance
                            fy -= force * dy / distance
                
                node1.x = max(50, min(1150, node1.x + fx * 0.1))
                node1.y = max(50, min(750, node1.y + fy * 0.1))
        
        return nodes


def main():
    import os
    db_path = "test_requirement_trace.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    manager = RequirementTraceManager(db_path)
    
    print("="*60)
    print("增强需求追溯管理器测试")
    print("="*60)
    
    req1 = manager.add_requirement(
        name="用户登录功能",
        requirement_type=RequirementType.FUNCTIONAL,
        description="用户可以通过用户名和密码登录系统",
        priority="high",
        acceptance_criteria=[
            {"scenario": "成功登录", "given": "用户已注册且账户正常", "when": "输入正确的用户名和密码", "then": "成功登录并跳转到首页"},
            {"scenario": "登录失败", "given": "用户已注册", "when": "输入错误的密码", "then": "显示错误提示"}
        ]
    )
    print(f"\n创建需求: {req1.id} - {req1.name}")
    
    req2 = manager.add_requirement(
        name="密码重置功能",
        requirement_type=RequirementType.FUNCTIONAL,
        description="用户可以重置忘记的密码",
        priority="medium"
    )
    print(f"创建需求: {req2.id} - {req2.name}")
    
    req3 = manager.add_requirement(
        name="系统性能要求",
        requirement_type=RequirementType.NON_FUNCTIONAL,
        description="系统响应时间应小于2秒",
        priority="high"
    )
    print(f"创建需求: {req3.id} - {req3.name}")
    
    code1 = manager.add_code_element(
        name="login",
        element_type=CodeElementType.FUNCTION,
        file_path="src/auth/login.py",
        line_start=10,
        line_end=50,
        module_name="auth.login",
        keywords=["login", "authentication", "user"],
        complexity=5
    )
    print(f"\n创建代码元素: {code1.id} - {code1.name}")
    
    code2 = manager.add_code_element(
        name="reset_password",
        element_type=CodeElementType.FUNCTION,
        file_path="src/auth/password.py",
        line_start=20,
        line_end=80,
        module_name="auth.password",
        keywords=["password", "reset", "email"],
        complexity=3
    )
    print(f"创建代码元素: {code2.id} - {code2.name}")
    
    tests = manager.generate_test_from_acceptance_criteria(
        requirement_id=req1.id,
        requirement_name=req1.name,
        acceptance_criteria=req1.acceptance_criteria
    )
    print(f"\n自动生成测试用例: {len(tests)} 个")
    
    test3 = manager.add_test_case(
        name="密码重置流程测试",
        test_type=TestType.ACCEPTANCE,
        scenario="重置密码",
        given="用户忘记密码",
        when="点击重置密码并输入邮箱",
        then="收到重置邮件并成功重置"
    )
    print(f"创建测试用例: {test3.id} - {test3.name}")
    
    link1 = manager.create_trace_link(
        source_type="requirement",
        source_id=req1.id,
        source_name=req1.name,
        target_type="test_case",
        target_id=tests[0].id,
        target_name=tests[0].name,
        trace_type=TraceType.REQUIREMENT_TO_TEST,
        confidence=1.0
    )
    print(f"\n创建追溯链接: {link1.id}")
    
    link2 = manager.link_requirement_to_code(
        requirement_id=req1.id,
        requirement_name=req1.name,
        code_element_id=code1.id,
        code_element_name=code1.name
    )
    print(f"创建需求-代码链接: {link2.id}")
    
    auto_links = manager.auto_link_tests_by_keywords(
        requirement_id=req2.id,
        requirement_name=req2.name,
        requirement_description=req2.description
    )
    print(f"自动关联测试: {len(auto_links)} 个")
    
    print("\n" + "="*60)
    print("测试覆盖率统计")
    print("="*60)
    
    coverage = manager.calculate_coverage()
    print(json.dumps(coverage, ensure_ascii=False, indent=2))
    
    print("\n" + "="*60)
    print("代码覆盖率统计")
    print("="*60)
    
    code_coverage = manager.calculate_code_coverage()
    print(json.dumps(code_coverage, ensure_ascii=False, indent=2))
    
    print("\n" + "="*60)
    print("覆盖率报告")
    print("="*60)
    
    report = manager.generate_coverage_report()
    print(f"总需求: {report.total_requirements}")
    print(f"已覆盖: {report.covered_requirements}")
    print(f"覆盖率: {report.coverage_rate}%")
    print(f"改进建议:")
    for rec in report.recommendations:
        print(f"  - {rec}")
    
    print("\n" + "="*60)
    print("追溯矩阵 (Markdown)")
    print("="*60)
    
    md = manager.export_trace_matrix("markdown")
    print(md[:2000])
    
    if os.path.exists(db_path):
        os.remove(db_path)
        print("\n清理测试数据库")


if __name__ == "__main__":
    main()
