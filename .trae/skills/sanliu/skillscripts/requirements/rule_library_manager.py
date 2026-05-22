#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
规则库管理器 - 增强版
支持存储、查询、版本控制、知识自动提取、分类存储、检索优化

增强功能:
1. 知识自动提取 - 从代码、文档、日志中自动提取知识
2. 知识分类存储 - 多维度分类、标签管理、层级组织
3. 知识版本管理 - 版本追踪、变更历史、回滚机制
4. 知识检索优化 - 语义检索、相似度匹配、智能推荐
"""

import json
import os
import re
import sqlite3
import ast
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, Callable, Set, Union
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import shutil
from pathlib import Path
import threading
import time


class RuleStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


class ChangeType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ACTIVATE = "activate"
    DEPRECATE = "deprecate"


class KnowledgeCategory(Enum):
    CODE_PATTERN = "code_pattern"
    BEST_PRACTICE = "best_practice"
    ERROR_PATTERN = "error_pattern"
    FIX_STRATEGY = "fix_strategy"
    PERFORMANCE_TIP = "performance_tip"
    SECURITY_RULE = "security_rule"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"


class KnowledgeSource(Enum):
    CODE_ANALYSIS = "code_analysis"
    LOG_ANALYSIS = "log_analysis"
    MANUAL_INPUT = "manual_input"
    LEARNING_SYSTEM = "learning_system"
    EXTERNAL_IMPORT = "external_import"
    PATTERN_RECOGNITION = "pattern_recognition"


class ExtractionConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SearchMode(Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


@dataclass
class RuleVersion:
    version: int
    rule_data: Dict[str, Any]
    changed_at: str
    changed_by: str
    change_type: ChangeType
    change_description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "rule_data": self.rule_data,
            "changed_at": self.changed_at,
            "changed_by": self.changed_by,
            "change_type": self.change_type.value,
            "change_description": self.change_description
        }


@dataclass
class ExtractedKnowledge:
    knowledge_id: str
    title: str
    category: KnowledgeCategory
    source: KnowledgeSource
    content: Dict[str, Any]
    confidence: ExtractionConfidence
    extracted_at: str
    source_location: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    related_rules: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "title": self.title,
            "category": self.category.value,
            "source": self.source.value,
            "content": self.content,
            "confidence": self.confidence.value,
            "extracted_at": self.extracted_at,
            "source_location": self.source_location,
            "tags": self.tags,
            "metadata": self.metadata,
            "related_rules": self.related_rules
        }


@dataclass
class KnowledgeClassification:
    primary_category: KnowledgeCategory
    secondary_categories: List[KnowledgeCategory] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    hierarchy_path: List[str] = field(default_factory=list)
    similarity_groups: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_category": self.primary_category.value,
            "secondary_categories": [c.value for c in self.secondary_categories],
            "tags": self.tags,
            "keywords": self.keywords,
            "hierarchy_path": self.hierarchy_path,
            "similarity_groups": self.similarity_groups
        }


@dataclass
class SearchResult:
    rule: 'StoredRule'
    relevance_score: float
    match_type: str
    matched_fields: List[str]
    highlights: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule.to_dict(),
            "relevance_score": self.relevance_score,
            "match_type": self.match_type,
            "matched_fields": self.matched_fields,
            "highlights": self.highlights
        }


@dataclass
class VersionDiff:
    version_from: int
    version_to: int
    changes: List[Dict[str, Any]]
    summary: str
    impact_analysis: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_from": self.version_from,
            "version_to": self.version_to,
            "changes": self.changes,
            "summary": self.summary,
            "impact_analysis": self.impact_analysis
        }


@dataclass
class StoredRule:
    id: str
    name: str
    category: str
    rule_type: str
    description: str
    content: Dict[str, Any]
    tags: List[str]
    status: RuleStatus
    current_version: int
    created_at: str
    updated_at: str
    created_by: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    knowledge_category: Optional[KnowledgeCategory] = None
    knowledge_source: Optional[KnowledgeSource] = None
    extraction_confidence: Optional[ExtractionConfidence] = None
    similarity_vector: List[float] = field(default_factory=list)
    usage_count: int = 0
    success_rate: float = 0.0
    last_used_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "rule_type": self.rule_type,
            "description": self.description,
            "content": self.content,
            "tags": self.tags,
            "status": self.status.value,
            "current_version": self.current_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "metadata": self.metadata,
            "knowledge_category": self.knowledge_category.value if self.knowledge_category else None,
            "knowledge_source": self.knowledge_source.value if self.knowledge_source else None,
            "extraction_confidence": self.extraction_confidence.value if self.extraction_confidence else None,
            "similarity_vector": self.similarity_vector,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "last_used_at": self.last_used_at
        }


@dataclass
class RuleQuery:
    keywords: Optional[List[str]] = None
    category: Optional[str] = None
    rule_type: Optional[str] = None
    status: Optional[RuleStatus] = None
    tags: Optional[List[str]] = None
    created_after: Optional[str] = None
    created_before: Optional[str] = None
    limit: int = 100
    offset: int = 0
    knowledge_category: Optional[KnowledgeCategory] = None
    knowledge_source: Optional[KnowledgeSource] = None
    min_confidence: Optional[ExtractionConfidence] = None
    search_mode: SearchMode = SearchMode.HYBRID
    min_relevance: float = 0.0


class KnowledgeExtractor:
    """知识自动提取器
    
    从代码、文档、日志等来源自动提取知识
    """
    
    CODE_PATTERNS = {
        'error_handling': {
            'pattern': r'try:\s*\n(.*?)\n\s*except\s+(\w+)',
            'category': KnowledgeCategory.ERROR_PATTERN,
            'extractor': '_extract_error_pattern'
        },
        'validation': {
            'pattern': r'(if|assert)\s+[^:]+:\s*\n?\s*(raise|return)',
            'category': KnowledgeCategory.CODE_PATTERN,
            'extractor': '_extract_validation_pattern'
        },
        'configuration': {
            'pattern': r'(\w+)\s*=\s*(["\'][^"\']+["\']|\d+|True|False|None)',
            'category': KnowledgeCategory.CONFIGURATION,
            'extractor': '_extract_config_pattern'
        },
        'logging': {
            'pattern': r'(logger|logging)\.(debug|info|warning|error|critical)\s*\([^)]+\)',
            'category': KnowledgeCategory.CODE_PATTERN,
            'extractor': '_extract_logging_pattern'
        },
        'security_check': {
            'pattern': r'(validate|check|verify|sanitize|escape)\s*\([^)]*\)',
            'category': KnowledgeCategory.SECURITY_RULE,
            'extractor': '_extract_security_pattern'
        }
    }
    
    DOC_PATTERNS = {
        'docstring': r'"""([\s\S]*?)"""',
        'comment_block': r'#\s*([^\n]+(?:\n#\s*[^\n]+)*)',
        'todo': r'#\s*(TODO|FIXME|HACK|XXX):\s*([^\n]+)',
        'note': r'#\s*NOTE:\s*([^\n]+)'
    }
    
    LOG_PATTERNS = {
        'error_log': r'\[ERROR\].*?(\w+Error|Exception).*?[:\-]\s*(.+)',
        'warning_log': r'\[WARNING\].*?[:\-]\s*(.+)',
        'performance': r'(slow|timeout|memory|cpu).*?[:\-]\s*(\d+\.?\d*)',
        'pattern_occurrence': r'(\w+Error|Exception).*?occurred\s+(\d+)\s+times'
    }
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./extracted_knowledge")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._extraction_cache: Dict[str, ExtractedKnowledge] = {}
        self._logger = logging.getLogger('KnowledgeExtractor')
    
    def extract_from_code(self, code: str, file_path: str = "") -> List[ExtractedKnowledge]:
        """从代码中提取知识"""
        extracted = []
        
        for pattern_name, config in self.CODE_PATTERNS.items():
            try:
                matches = re.finditer(config['pattern'], code, re.MULTILINE | re.DOTALL)
                extractor_method = getattr(self, config['extractor'], None)
                
                if extractor_method:
                    for match in matches:
                        knowledge = extractor_method(
                            match, pattern_name, config['category'], file_path
                        )
                        if knowledge:
                            extracted.append(knowledge)
            except Exception as e:
                self._logger.warning(f"提取模式 {pattern_name} 失败: {e}")
        
        extracted.extend(self._extract_from_docstrings(code, file_path))
        extracted.extend(self._extract_from_comments(code, file_path))
        
        return extracted
    
    def _extract_error_pattern(self, match, pattern_name: str, 
                               category: KnowledgeCategory, 
                               file_path: str) -> Optional[ExtractedKnowledge]:
        """提取错误处理模式"""
        try:
            try_block = match.group(1) if match.groups() else ""
            exception_type = match.group(2) if len(match.groups()) > 1 else "Exception"
            
            knowledge_id = f"EXT-ERR-{hashlib.md5(f'{exception_type}{try_block[:50]}'.encode()).hexdigest()[:8]}"
            
            return ExtractedKnowledge(
                knowledge_id=knowledge_id,
                title=f"错误处理模式: {exception_type}",
                category=category,
                source=KnowledgeSource.CODE_ANALYSIS,
                content={
                    "exception_type": exception_type,
                    "try_block_preview": try_block[:200],
                    "pattern_type": pattern_name
                },
                confidence=ExtractionConfidence.HIGH,
                extracted_at=datetime.now().isoformat(),
                source_location=file_path,
                tags=["error_handling", exception_type.lower(), "pattern"],
                metadata={"line_number": match.start()}
            )
        except Exception:
            return None
    
    def _extract_validation_pattern(self, match, pattern_name: str,
                                    category: KnowledgeCategory,
                                    file_path: str) -> Optional[ExtractedKnowledge]:
        """提取验证模式"""
        try:
            condition = match.group(0)[:100]
            knowledge_id = f"EXT-VAL-{hashlib.md5(condition.encode()).hexdigest()[:8]}"
            
            return ExtractedKnowledge(
                knowledge_id=knowledge_id,
                title=f"验证模式: {condition[:30]}...",
                category=category,
                source=KnowledgeSource.CODE_ANALYSIS,
                content={
                    "condition": condition,
                    "pattern_type": pattern_name
                },
                confidence=ExtractionConfidence.MEDIUM,
                extracted_at=datetime.now().isoformat(),
                source_location=file_path,
                tags=["validation", "pattern"],
                metadata={"line_number": match.start()}
            )
        except Exception:
            return None
    
    def _extract_config_pattern(self, match, pattern_name: str,
                                category: KnowledgeCategory,
                                file_path: str) -> Optional[ExtractedKnowledge]:
        """提取配置模式"""
        try:
            key = match.group(1)
            value = match.group(2)
            knowledge_id = f"EXT-CFG-{hashlib.md5(f'{key}{value}'.encode()).hexdigest()[:8]}"
            
            return ExtractedKnowledge(
                knowledge_id=knowledge_id,
                title=f"配置项: {key}",
                category=category,
                source=KnowledgeSource.CODE_ANALYSIS,
                content={
                    "key": key,
                    "value": value,
                    "pattern_type": pattern_name
                },
                confidence=ExtractionConfidence.HIGH,
                extracted_at=datetime.now().isoformat(),
                source_location=file_path,
                tags=["configuration", key.lower()],
                metadata={"line_number": match.start()}
            )
        except Exception:
            return None
    
    def _extract_logging_pattern(self, match, pattern_name: str,
                                 category: KnowledgeCategory,
                                 file_path: str) -> Optional[ExtractedKnowledge]:
        """提取日志模式"""
        try:
            log_level = match.group(2)
            log_content = match.group(0)[:100]
            knowledge_id = f"EXT-LOG-{hashlib.md5(log_content.encode()).hexdigest()[:8]}"
            
            return ExtractedKnowledge(
                knowledge_id=knowledge_id,
                title=f"日志模式: {log_level}",
                category=category,
                source=KnowledgeSource.CODE_ANALYSIS,
                content={
                    "log_level": log_level,
                    "log_content": log_content,
                    "pattern_type": pattern_name
                },
                confidence=ExtractionConfidence.MEDIUM,
                extracted_at=datetime.now().isoformat(),
                source_location=file_path,
                tags=["logging", log_level.lower()],
                metadata={"line_number": match.start()}
            )
        except Exception:
            return None
    
    def _extract_security_pattern(self, match, pattern_name: str,
                                  category: KnowledgeCategory,
                                  file_path: str) -> Optional[ExtractedKnowledge]:
        """提取安全模式"""
        try:
            check_type = match.group(1)
            knowledge_id = f"EXT-SEC-{hashlib.md5(f'{check_type}{match.group(0)[:50]}'.encode()).hexdigest()[:8]}"
            
            return ExtractedKnowledge(
                knowledge_id=knowledge_id,
                title=f"安全检查: {check_type}",
                category=category,
                source=KnowledgeSource.CODE_ANALYSIS,
                content={
                    "check_type": check_type,
                    "full_call": match.group(0),
                    "pattern_type": pattern_name
                },
                confidence=ExtractionConfidence.HIGH,
                extracted_at=datetime.now().isoformat(),
                source_location=file_path,
                tags=["security", check_type.lower()],
                metadata={"line_number": match.start()}
            )
        except Exception:
            return None
    
    def _extract_from_docstrings(self, code: str, file_path: str) -> List[ExtractedKnowledge]:
        """从文档字符串提取知识"""
        extracted = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                docstring = ast.get_docstring(node)
                if docstring and len(docstring) > 20:
                    node_type = type(node).__name__
                    node_name = getattr(node, 'name', 'unknown')
                    
                    knowledge_id = f"EXT-DOC-{hashlib.md5(docstring[:100].encode()).hexdigest()[:8]}"
                    
                    category = KnowledgeCategory.DOCUMENTATION
                    if 'param' in docstring.lower() or 'arg' in docstring.lower():
                        category = KnowledgeCategory.CODE_PATTERN
                    elif 'example' in docstring.lower():
                        category = KnowledgeCategory.BEST_PRACTICE
                    
                    extracted.append(ExtractedKnowledge(
                        knowledge_id=knowledge_id,
                        title=f"文档: {node_type} {node_name}",
                        category=category,
                        source=KnowledgeSource.CODE_ANALYSIS,
                        content={
                            "docstring": docstring,
                            "node_type": node_type,
                            "node_name": node_name
                        },
                        confidence=ExtractionConfidence.HIGH,
                        extracted_at=datetime.now().isoformat(),
                        source_location=file_path,
                        tags=["documentation", node_type.lower(), node_name.lower()],
                        metadata={"line_number": getattr(node, 'lineno', 0)}
                    ))
        except SyntaxError:
            pass
        except Exception as e:
            self._logger.warning(f"提取文档字符串失败: {e}")
        
        return extracted
    
    def _extract_from_comments(self, code: str, file_path: str) -> List[ExtractedKnowledge]:
        """从注释提取知识"""
        extracted = []
        
        for pattern_name, pattern in self.DOC_PATTERNS.items():
            try:
                matches = re.finditer(pattern, code, re.MULTILINE)
                for match in matches:
                    content = match.group(1) if match.groups() else match.group(0)
                    
                    if len(content) < 10:
                        continue
                    
                    knowledge_id = f"EXT-CMT-{hashlib.md5(content[:50].encode()).hexdigest()[:8]}"
                    
                    category = KnowledgeCategory.DOCUMENTATION
                    if pattern_name == 'todo':
                        category = KnowledgeCategory.CODE_PATTERN
                    
                    extracted.append(ExtractedKnowledge(
                        knowledge_id=knowledge_id,
                        title=f"注释: {pattern_name}",
                        category=category,
                        source=KnowledgeSource.CODE_ANALYSIS,
                        content={
                            "comment": content,
                            "type": pattern_name
                        },
                        confidence=ExtractionConfidence.LOW,
                        extracted_at=datetime.now().isoformat(),
                        source_location=file_path,
                        tags=["comment", pattern_name],
                        metadata={"line_number": code[:match.start()].count('\n') + 1}
                    ))
            except Exception:
                pass
        
        return extracted
    
    def extract_from_log(self, log_content: str, log_file: str = "") -> List[ExtractedKnowledge]:
        """从日志中提取知识"""
        extracted = []
        
        for pattern_name, pattern in self.LOG_PATTERNS.items():
            try:
                matches = re.finditer(pattern, log_content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    knowledge_id = f"EXT-LOG-{hashlib.md5(match.group(0)[:50].encode()).hexdigest()[:8]}"
                    
                    category = KnowledgeCategory.ERROR_PATTERN
                    if pattern_name == 'performance':
                        category = KnowledgeCategory.PERFORMANCE_TIP
                    elif pattern_name == 'warning_log':
                        category = KnowledgeCategory.CODE_PATTERN
                    
                    extracted.append(ExtractedKnowledge(
                        knowledge_id=knowledge_id,
                        title=f"日志模式: {pattern_name}",
                        category=category,
                        source=KnowledgeSource.LOG_ANALYSIS,
                        content={
                            "log_entry": match.group(0),
                            "pattern_type": pattern_name,
                            "groups": match.groups()
                        },
                        confidence=ExtractionConfidence.MEDIUM,
                        extracted_at=datetime.now().isoformat(),
                        source_location=log_file,
                        tags=["log", pattern_name],
                        metadata={}
                    ))
            except Exception:
                pass
        
        return extracted
    
    def extract_from_file(self, file_path: Union[str, Path]) -> List[ExtractedKnowledge]:
        """从文件提取知识"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return []
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return []
        
        suffix = file_path.suffix.lower()
        
        if suffix == '.py':
            return self.extract_from_code(content, str(file_path))
        elif suffix in ['.log', '.txt']:
            return self.extract_from_log(content, str(file_path))
        elif suffix in ['.md', '.rst']:
            return self._extract_from_documentation(content, str(file_path))
        else:
            return []
    
    def _extract_from_documentation(self, content: str, file_path: str) -> List[ExtractedKnowledge]:
        """从文档提取知识"""
        extracted = []
        
        sections = re.split(r'\n#{1,3}\s+', content)
        
        for i, section in enumerate(sections[1:], 1):
            lines = section.split('\n')
            title = lines[0] if lines else f"Section {i}"
            body = '\n'.join(lines[1:]) if len(lines) > 1 else ""
            
            if len(body) > 50:
                knowledge_id = f"EXT-DOC-{hashlib.md5(f'{title}{body[:50]}'.encode()).hexdigest()[:8]}"
                
                extracted.append(ExtractedKnowledge(
                    knowledge_id=knowledge_id,
                    title=f"文档章节: {title[:50]}",
                    category=KnowledgeCategory.DOCUMENTATION,
                    source=KnowledgeSource.CODE_ANALYSIS,
                    content={
                        "title": title,
                        "body": body[:500],
                        "full_length": len(body)
                    },
                    confidence=ExtractionConfidence.MEDIUM,
                    extracted_at=datetime.now().isoformat(),
                    source_location=file_path,
                    tags=["documentation", "section"],
                    metadata={"section_index": i}
                ))
        
        return extracted
    
    def batch_extract(self, directory: Union[str, Path], 
                     file_patterns: List[str] = None) -> List[ExtractedKnowledge]:
        """批量提取知识"""
        directory = Path(directory)
        file_patterns = file_patterns or ['*.py', '*.log', '*.md', '*.txt']
        
        all_extracted = []
        
        for pattern in file_patterns:
            for file_path in directory.rglob(pattern):
                if '__pycache__' in str(file_path) or '.venv' in str(file_path):
                    continue
                
                extracted = self.extract_from_file(file_path)
                all_extracted.extend(extracted)
        
        self._logger.info(f"批量提取完成: {len(all_extracted)} 条知识")
        return all_extracted


class KnowledgeClassifier:
    """知识分类器
    
    对知识进行多维度分类和标签管理
    """
    
    CATEGORY_KEYWORDS = {
        KnowledgeCategory.CODE_PATTERN: ['pattern', 'design', 'structure', 'algorithm', 'implementation'],
        KnowledgeCategory.BEST_PRACTICE: ['best', 'practice', 'recommend', 'should', 'avoid', 'prefer'],
        KnowledgeCategory.ERROR_PATTERN: ['error', 'exception', 'fail', 'bug', 'issue', 'problem'],
        KnowledgeCategory.FIX_STRATEGY: ['fix', 'solution', 'resolve', 'repair', 'patch'],
        KnowledgeCategory.PERFORMANCE_TIP: ['performance', 'optimize', 'fast', 'slow', 'memory', 'cpu'],
        KnowledgeCategory.SECURITY_RULE: ['security', 'vulnerability', 'attack', 'safe', 'validate'],
        KnowledgeCategory.ARCHITECTURE: ['architecture', 'design', 'module', 'component', 'layer'],
        KnowledgeCategory.TESTING: ['test', 'spec', 'coverage', 'unit', 'integration'],
        KnowledgeCategory.DOCUMENTATION: ['doc', 'comment', 'readme', 'guide', 'tutorial'],
        KnowledgeCategory.CONFIGURATION: ['config', 'setting', 'option', 'parameter', 'environment']
    }
    
    HIERARCHY = {
        KnowledgeCategory.ARCHITECTURE: [
            KnowledgeCategory.CODE_PATTERN,
            KnowledgeCategory.BEST_PRACTICE
        ],
        KnowledgeCategory.SECURITY_RULE: [
            KnowledgeCategory.ERROR_PATTERN,
            KnowledgeCategory.FIX_STRATEGY
        ],
        KnowledgeCategory.TESTING: [
            KnowledgeCategory.CODE_PATTERN,
            KnowledgeCategory.BEST_PRACTICE
        ]
    }
    
    def __init__(self):
        self._classification_cache: Dict[str, KnowledgeClassification] = {}
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)
        self._keyword_index: Dict[str, Set[str]] = defaultdict(set)
    
    def classify(self, knowledge: ExtractedKnowledge) -> KnowledgeClassification:
        """分类知识"""
        cache_key = knowledge.knowledge_id
        if cache_key in self._classification_cache:
            return self._classification_cache[cache_key]
        
        primary_category = self._determine_primary_category(knowledge)
        secondary_categories = self._determine_secondary_categories(knowledge, primary_category)
        tags = self._extract_tags(knowledge)
        keywords = self._extract_keywords(knowledge)
        hierarchy_path = self._build_hierarchy_path(primary_category)
        similarity_groups = self._find_similarity_groups(knowledge)
        
        classification = KnowledgeClassification(
            primary_category=primary_category,
            secondary_categories=secondary_categories,
            tags=tags,
            keywords=keywords,
            hierarchy_path=hierarchy_path,
            similarity_groups=similarity_groups
        )
        
        self._classification_cache[cache_key] = classification
        self._update_indices(knowledge.knowledge_id, classification)
        
        return classification
    
    def _determine_primary_category(self, knowledge: ExtractedKnowledge) -> KnowledgeCategory:
        """确定主分类"""
        if knowledge.category != KnowledgeCategory.DOCUMENTATION:
            return knowledge.category
        
        text = f"{knowledge.title} {json.dumps(knowledge.content)}"
        text_lower = text.lower()
        
        scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return knowledge.category
    
    def _determine_secondary_categories(self, knowledge: ExtractedKnowledge,
                                        primary: KnowledgeCategory) -> List[KnowledgeCategory]:
        """确定次级分类"""
        secondary = []
        
        if primary in self.HIERARCHY:
            secondary.extend(self.HIERARCHY[primary])
        
        text = f"{knowledge.title} {json.dumps(knowledge.content)}"
        text_lower = text.lower()
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if category == primary or category in secondary:
                continue
            
            if any(kw in text_lower for kw in keywords):
                secondary.append(category)
        
        return secondary[:3]
    
    def _extract_tags(self, knowledge: ExtractedKnowledge) -> List[str]:
        """提取标签"""
        tags = list(knowledge.tags)
        
        text = f"{knowledge.title} {json.dumps(knowledge.content)}"
        
        tag_patterns = [
            (r'\b(async|sync|thread|process)\b', 'concurrency'),
            (r'\b(database|db|sql|query)\b', 'database'),
            (r'\b(api|rest|http|endpoint)\b', 'api'),
            (r'\b(auth|login|token|session)\b', 'authentication'),
            (r'\b(cache|redis|memory)\b', 'caching'),
            (r'\b(test|spec|mock|fixture)\b', 'testing'),
            (r'\b(log|debug|trace|monitor)\b', 'observability'),
        ]
        
        for pattern, tag in tag_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                tags.append(tag)
        
        return list(set(tags))
    
    def _extract_keywords(self, knowledge: ExtractedKnowledge) -> List[str]:
        """提取关键词"""
        text = f"{knowledge.title} {knowledge.description if hasattr(knowledge, 'description') else ''}"
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out'}
        keywords = [w for w in words if w not in stop_words]
        
        word_freq = defaultdict(int)
        for word in keywords:
            word_freq[word] += 1
        
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [kw for kw, _ in sorted_keywords[:10]]
    
    def _build_hierarchy_path(self, category: KnowledgeCategory) -> List[str]:
        """构建层级路径"""
        path = [category.value]
        
        for parent, children in self.HIERARCHY.items():
            if category in children:
                path.insert(0, parent.value)
                break
        
        return path
    
    def _find_similarity_groups(self, knowledge: ExtractedKnowledge) -> List[str]:
        """查找相似组"""
        groups = []
        
        for tag in knowledge.tags:
            groups.append(f"tag:{tag}")
        
        groups.append(f"category:{knowledge.category.value}")
        groups.append(f"source:{knowledge.source.value}")
        
        return groups
    
    def _update_indices(self, knowledge_id: str, classification: KnowledgeClassification):
        """更新索引"""
        for tag in classification.tags:
            self._tag_index[tag].add(knowledge_id)
        
        for keyword in classification.keywords:
            self._keyword_index[keyword].add(knowledge_id)
    
    def find_similar(self, knowledge_id: str) -> List[str]:
        """查找相似知识"""
        if knowledge_id not in self._classification_cache:
            return []
        
        classification = self._classification_cache[knowledge_id]
        similar_ids = set()
        
        for tag in classification.tags:
            similar_ids.update(self._tag_index.get(tag, set()))
        
        for keyword in classification.keywords[:3]:
            similar_ids.update(self._keyword_index.get(keyword, set()))
        
        similar_ids.discard(knowledge_id)
        
        return list(similar_ids)


class KnowledgeSearchEngine:
    """知识检索引擎
    
    支持语义检索、相似度匹配、智能推荐
    """
    
    def __init__(self, db_path: str = "rule_library.db"):
        self.db_path = db_path
        self._search_cache: Dict[str, List[SearchResult]] = {}
        self._embedding_cache: Dict[str, List[float]] = {}
        self._logger = logging.getLogger('KnowledgeSearchEngine')
    
    def search(self, query: RuleQuery, rules: List['StoredRule']) -> List[SearchResult]:
        """搜索知识"""
        cache_key = self._generate_cache_key(query)
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]
        
        results = []
        
        if query.search_mode == SearchMode.EXACT:
            results = self._exact_search(query, rules)
        elif query.search_mode == SearchMode.FUZZY:
            results = self._fuzzy_search(query, rules)
        elif query.search_mode == SearchMode.SEMANTIC:
            results = self._semantic_search(query, rules)
        else:
            results = self._hybrid_search(query, rules)
        
        results = [r for r in results if r.relevance_score >= query.min_relevance]
        
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        results = results[:query.limit]
        
        self._search_cache[cache_key] = results
        
        return results
    
    def _exact_search(self, query: RuleQuery, rules: List['StoredRule']) -> List[SearchResult]:
        """精确搜索"""
        results = []
        
        for rule in rules:
            if query.category and rule.category != query.category:
                continue
            if query.rule_type and rule.rule_type != query.rule_type:
                continue
            if query.status and rule.status != query.status:
                continue
            if query.knowledge_category and rule.knowledge_category != query.knowledge_category:
                continue
            
            relevance = 1.0
            matched_fields = []
            highlights = {}
            
            if query.keywords:
                keyword_matches = 0
                for keyword in query.keywords:
                    if keyword.lower() in rule.name.lower():
                        keyword_matches += 1
                        matched_fields.append('name')
                        highlights['name'] = self._highlight(rule.name, keyword)
                    if keyword.lower() in rule.description.lower():
                        keyword_matches += 1
                        matched_fields.append('description')
                        highlights['description'] = self._highlight(rule.description, keyword)
                
                if keyword_matches == 0:
                    continue
                relevance = keyword_matches / len(query.keywords)
            
            results.append(SearchResult(
                rule=rule,
                relevance_score=relevance,
                match_type='exact',
                matched_fields=list(set(matched_fields)),
                highlights=highlights
            ))
        
        return results
    
    def _fuzzy_search(self, query: RuleQuery, rules: List['StoredRule']) -> List[SearchResult]:
        """模糊搜索"""
        results = []
        
        for rule in rules:
            relevance = 0.0
            matched_fields = []
            highlights = {}
            
            if query.keywords:
                for keyword in query.keywords:
                    kw_lower = keyword.lower()
                    
                    if self._fuzzy_match(kw_lower, rule.name.lower()):
                        relevance += 0.4
                        matched_fields.append('name')
                        highlights['name'] = self._highlight(rule.name, keyword)
                    
                    if self._fuzzy_match(kw_lower, rule.description.lower()):
                        relevance += 0.3
                        matched_fields.append('description')
                        highlights['description'] = self._highlight(rule.description, keyword)
                    
                    for tag in rule.tags:
                        if self._fuzzy_match(kw_lower, tag.lower()):
                            relevance += 0.2
                            matched_fields.append('tags')
                            break
            
            if relevance > 0:
                results.append(SearchResult(
                    rule=rule,
                    relevance_score=min(relevance, 1.0),
                    match_type='fuzzy',
                    matched_fields=list(set(matched_fields)),
                    highlights=highlights
                ))
        
        return results
    
    def _semantic_search(self, query: RuleQuery, rules: List['StoredRule']) -> List[SearchResult]:
        """语义搜索"""
        results = []
        
        query_text = ' '.join(query.keywords or [])
        query_embedding = self._get_embedding(query_text)
        
        for rule in rules:
            rule_text = f"{rule.name} {rule.description}"
            rule_embedding = self._get_embedding(rule_text)
            
            if rule.similarity_vector:
                rule_embedding = rule.similarity_vector
            
            similarity = self._cosine_similarity(query_embedding, rule_embedding)
            
            if similarity > 0.1:
                results.append(SearchResult(
                    rule=rule,
                    relevance_score=similarity,
                    match_type='semantic',
                    matched_fields=['content'],
                    highlights={}
                ))
        
        return results
    
    def _hybrid_search(self, query: RuleQuery, rules: List['StoredRule']) -> List[SearchResult]:
        """混合搜索"""
        exact_results = self._exact_search(query, rules)
        fuzzy_results = self._fuzzy_search(query, rules)
        semantic_results = self._semantic_search(query, rules)
        
        combined = {}
        
        for result in exact_results:
            combined[result.rule.id] = result
            combined[result.rule.id].relevance_score *= 1.0
        
        for result in fuzzy_results:
            if result.rule.id in combined:
                combined[result.rule.id].relevance_score += result.relevance_score * 0.5
            else:
                combined[result.rule.id] = result
                combined[result.rule.id].relevance_score *= 0.7
        
        for result in semantic_results:
            if result.rule.id in combined:
                combined[result.rule.id].relevance_score += result.relevance_score * 0.3
            else:
                combined[result.rule.id] = result
                combined[result.rule.id].relevance_score *= 0.5
        
        return list(combined.values())
    
    def _fuzzy_match(self, pattern: str, text: str, threshold: float = 0.7) -> bool:
        """模糊匹配"""
        if pattern in text:
            return True
        
        if len(pattern) < 3:
            return False
        
        pattern_chars = set(pattern)
        text_chars = set(text)
        
        intersection = len(pattern_chars & text_chars)
        union = len(pattern_chars | text_chars)
        
        jaccard = intersection / union if union > 0 else 0
        
        return jaccard >= threshold
    
    def _get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入向量（简化版）"""
        if text in self._embedding_cache:
            return self._embedding_cache[text]
        
        words = text.lower().split()
        
        embedding = [0.0] * 100
        
        for i, word in enumerate(words[:20]):
            for j, char in enumerate(word[:5]):
                idx = (i * 5 + j) % 100
                embedding[idx] += ord(char) / 255.0
        
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        self._embedding_cache[text] = embedding
        
        return embedding
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _highlight(self, text: str, keyword: str) -> str:
        """高亮关键词"""
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        return pattern.sub(f'**{keyword}**', text)
    
    def _generate_cache_key(self, query: RuleQuery) -> str:
        """生成缓存键"""
        key_parts = [
            str(query.keywords),
            query.category or '',
            query.rule_type or '',
            query.status.value if query.status else '',
            str(query.tags),
            query.search_mode.value,
            str(query.min_relevance)
        ]
        return hashlib.md5('|'.join(key_parts).encode()).hexdigest()
    
    def recommend(self, rule_id: str, rules: List['StoredRule'], limit: int = 5) -> List[SearchResult]:
        """推荐相关知识"""
        target_rule = next((r for r in rules if r.id == rule_id), None)
        if not target_rule:
            return []
        
        results = []
        
        for rule in rules:
            if rule.id == rule_id:
                continue
            
            score = 0.0
            
            if rule.category == target_rule.category:
                score += 0.3
            
            common_tags = set(rule.tags) & set(target_rule.tags)
            score += len(common_tags) * 0.1
            
            if rule.knowledge_category and target_rule.knowledge_category:
                if rule.knowledge_category == target_rule.knowledge_category:
                    score += 0.2
            
            if rule.similarity_vector and target_rule.similarity_vector:
                similarity = self._cosine_similarity(rule.similarity_vector, target_rule.similarity_vector)
                score += similarity * 0.4
            
            if score > 0:
                results.append(SearchResult(
                    rule=rule,
                    relevance_score=score,
                    match_type='recommendation',
                    matched_fields=['category', 'tags'],
                    highlights={}
                ))
        
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results[:limit]


class RuleLibraryManager:
    """增强版规则库管理器
    
    集成知识自动提取、分类存储、版本管理、检索优化功能
    """
    
    def __init__(self, db_path: str = "rule_library.db", 
                 enable_extraction: bool = True,
                 enable_classification: bool = True,
                 enable_search_optimization: bool = True):
        self.db_path = db_path
        self._init_database()
        
        self._logger = logging.getLogger('RuleLibraryManager')
        
        self._extractor = KnowledgeExtractor() if enable_extraction else None
        self._classifier = KnowledgeClassifier() if enable_classification else None
        self._search_engine = KnowledgeSearchEngine(db_path) if enable_search_optimization else None
        
        self._lock = threading.Lock()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                description TEXT,
                content TEXT NOT NULL,
                tags TEXT,
                status TEXT DEFAULT 'active',
                current_version INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                created_by TEXT,
                metadata TEXT,
                knowledge_category TEXT,
                knowledge_source TEXT,
                extraction_confidence TEXT,
                similarity_vector TEXT,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                last_used_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                rule_data TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                changed_by TEXT,
                change_type TEXT NOT NULL,
                change_description TEXT,
                UNIQUE(rule_id, version),
                FOREIGN KEY (rule_id) REFERENCES rules(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (rule_id) REFERENCES rules(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                FOREIGN KEY (rule_id) REFERENCES rules(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_similarity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id1 TEXT NOT NULL,
                rule_id2 TEXT NOT NULL,
                similarity_score REAL NOT NULL,
                FOREIGN KEY (rule_id1) REFERENCES rules(id),
                FOREIGN KEY (rule_id2) REFERENCES rules(id)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rules_category ON rules(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rules_status ON rules(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rules_type ON rules(rule_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rule_versions_rule_id ON rule_versions(rule_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rule_tags_tag ON rule_tags(tag)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_index_keyword ON knowledge_index(keyword)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_similarity ON knowledge_similarity(rule_id1, rule_id2)')
        
        conn.commit()
        conn.close()
    
    def _generate_rule_id(self, category: str) -> str:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"RULE-{category.upper()}-{timestamp}"
    
    def store_rule(self, 
                   name: str,
                   category: str,
                   rule_type: str,
                   description: str,
                   content: Dict[str, Any],
                   tags: List[str] = None,
                   created_by: str = "system",
                   metadata: Dict[str, Any] = None) -> StoredRule:
        
        rule_id = self._generate_rule_id(category)
        now = datetime.now().isoformat()
        tags = tags or []
        metadata = metadata or {}
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO rules (id, name, category, rule_type, description, content, tags, status, current_version, created_at, updated_at, created_by, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (rule_id, name, category, rule_type, description, 
              json.dumps(content, ensure_ascii=False), 
              json.dumps(tags, ensure_ascii=False),
              RuleStatus.ACTIVE.value, 1, now, now, created_by,
              json.dumps(metadata, ensure_ascii=False)))
        
        for tag in tags:
            cursor.execute('INSERT INTO rule_tags (rule_id, tag) VALUES (?, ?)', (rule_id, tag))
        
        cursor.execute('''
            INSERT INTO rule_versions (rule_id, version, rule_data, changed_at, changed_by, change_type, change_description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (rule_id, 1, json.dumps(content, ensure_ascii=False), now, created_by, 
              ChangeType.CREATE.value, "初始创建"))
        
        conn.commit()
        conn.close()
        
        return StoredRule(
            id=rule_id,
            name=name,
            category=category,
            rule_type=rule_type,
            description=description,
            content=content,
            tags=tags,
            status=RuleStatus.ACTIVE,
            current_version=1,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            metadata=metadata
        )
    
    def get_rule(self, rule_id: str) -> Optional[StoredRule]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM rules WHERE id = ?', (rule_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_rule(row)
        return None
    
    def _row_to_rule(self, row: sqlite3.Row) -> StoredRule:
        knowledge_category = None
        if row['knowledge_category']:
            try:
                knowledge_category = KnowledgeCategory(row['knowledge_category'])
            except ValueError:
                pass
        
        knowledge_source = None
        if row['knowledge_source']:
            try:
                knowledge_source = KnowledgeSource(row['knowledge_source'])
            except ValueError:
                pass
        
        extraction_confidence = None
        if row['extraction_confidence']:
            try:
                extraction_confidence = ExtractionConfidence(row['extraction_confidence'])
            except ValueError:
                pass
        
        similarity_vector = []
        if row['similarity_vector']:
            try:
                similarity_vector = json.loads(row['similarity_vector'])
            except:
                pass
        
        return StoredRule(
            id=row['id'],
            name=row['name'],
            category=row['category'],
            rule_type=row['rule_type'],
            description=row['description'],
            content=json.loads(row['content']),
            tags=json.loads(row['tags']) if row['tags'] else [],
            status=RuleStatus(row['status']),
            current_version=row['current_version'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            created_by=row['created_by'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            knowledge_category=knowledge_category,
            knowledge_source=knowledge_source,
            extraction_confidence=extraction_confidence,
            similarity_vector=similarity_vector,
            usage_count=row['usage_count'] or 0,
            success_rate=row['success_rate'] or 0.0,
            last_used_at=row['last_used_at']
        )
    
    def query_rules(self, query: RuleQuery) -> List[StoredRule]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        sql = "SELECT * FROM rules WHERE 1=1"
        params = []
        
        if query.category:
            sql += " AND category = ?"
            params.append(query.category)
        
        if query.rule_type:
            sql += " AND rule_type = ?"
            params.append(query.rule_type)
        
        if query.status:
            sql += " AND status = ?"
            params.append(query.status.value)
        
        if query.created_after:
            sql += " AND created_at >= ?"
            params.append(query.created_after)
        
        if query.created_before:
            sql += " AND created_at <= ?"
            params.append(query.created_before)
        
        if query.keywords:
            keyword_conditions = []
            for keyword in query.keywords:
                keyword_conditions.append("(name LIKE ? OR description LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            sql += " AND (" + " OR ".join(keyword_conditions) + ")"
        
        if query.tags:
            for tag in query.tags:
                sql += " AND id IN (SELECT rule_id FROM rule_tags WHERE tag = ?)"
                params.append(tag)
        
        sql += f" ORDER BY created_at DESC LIMIT {query.limit} OFFSET {query.offset}"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_rule(row) for row in rows]
    
    def update_rule(self, 
                    rule_id: str, 
                    content: Dict[str, Any] = None,
                    name: str = None,
                    description: str = None,
                    tags: List[str] = None,
                    changed_by: str = "system",
                    change_description: str = "") -> Optional[StoredRule]:
        
        rule = self.get_rule(rule_id)
        if not rule:
            return None
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        new_version = rule.current_version + 1
        
        new_content = content if content is not None else rule.content
        new_name = name if name is not None else rule.name
        new_description = description if description is not None else rule.description
        new_tags = tags if tags is not None else rule.tags
        
        cursor.execute('''
            UPDATE rules 
            SET name = ?, description = ?, content = ?, tags = ?, current_version = ?, updated_at = ?
            WHERE id = ?
        ''', (new_name, new_description, 
              json.dumps(new_content, ensure_ascii=False),
              json.dumps(new_tags, ensure_ascii=False),
              new_version, now, rule_id))
        
        cursor.execute('DELETE FROM rule_tags WHERE rule_id = ?', (rule_id,))
        for tag in new_tags:
            cursor.execute('INSERT INTO rule_tags (rule_id, tag) VALUES (?, ?)', (rule_id, tag))
        
        cursor.execute('''
            INSERT INTO rule_versions (rule_id, version, rule_data, changed_at, changed_by, change_type, change_description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (rule_id, new_version, json.dumps(new_content, ensure_ascii=False), 
              now, changed_by, ChangeType.UPDATE.value, change_description))
        
        conn.commit()
        conn.close()
        
        return self.get_rule(rule_id)
    
    def delete_rule(self, rule_id: str, deleted_by: str = "system") -> bool:
        rule = self.get_rule(rule_id)
        if not rule:
            return False
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO rule_versions (rule_id, version, rule_data, changed_at, changed_by, change_type, change_description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (rule_id, rule.current_version + 1, 
              json.dumps(rule.content, ensure_ascii=False),
              now, deleted_by, ChangeType.DELETE.value, "规则已删除"))
        
        cursor.execute('DELETE FROM rule_tags WHERE rule_id = ?', (rule_id,))
        cursor.execute('DELETE FROM rule_versions WHERE rule_id = ?', (rule_id,))
        cursor.execute('DELETE FROM rules WHERE id = ?', (rule_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    def deprecate_rule(self, rule_id: str, reason: str = "", deprecated_by: str = "system") -> Optional[StoredRule]:
        rule = self.get_rule(rule_id)
        if not rule:
            return None
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        new_version = rule.current_version + 1
        
        cursor.execute('UPDATE rules SET status = ?, current_version = ?, updated_at = ? WHERE id = ?',
                      (RuleStatus.DEPRECATED.value, new_version, now, rule_id))
        
        cursor.execute('''
            INSERT INTO rule_versions (rule_id, version, rule_data, changed_at, changed_by, change_type, change_description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (rule_id, new_version, json.dumps(rule.content, ensure_ascii=False),
              now, deprecated_by, ChangeType.DEPRECATE.value, reason))
        
        conn.commit()
        conn.close()
        
        return self.get_rule(rule_id)
    
    def get_rule_versions(self, rule_id: str) -> List[RuleVersion]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT version, rule_data, changed_at, changed_by, change_type, change_description
            FROM rule_versions
            WHERE rule_id = ?
            ORDER BY version DESC
        ''', (rule_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        versions = []
        for row in rows:
            versions.append(RuleVersion(
                version=row['version'],
                rule_data=json.loads(row['rule_data']),
                changed_at=row['changed_at'],
                changed_by=row['changed_by'],
                change_type=ChangeType(row['change_type']),
                change_description=row['change_description']
            ))
        
        return versions
    
    def get_rule_at_version(self, rule_id: str, version: int) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT rule_data FROM rule_versions
            WHERE rule_id = ? AND version = ?
        ''', (rule_id, version))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row['rule_data'])
        return None
    
    def rollback_to_version(self, rule_id: str, target_version: int, rolled_back_by: str = "system") -> Optional[StoredRule]:
        rule = self.get_rule(rule_id)
        if not rule:
            return None
        
        target_content = self.get_rule_at_version(rule_id, target_version)
        if not target_content:
            return None
        
        return self.update_rule(
            rule_id=rule_id,
            content=target_content,
            changed_by=rolled_back_by,
            change_description=f"回滚到版本 {target_version}"
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM rules')
        total_rules = cursor.fetchone()['total']
        
        cursor.execute('SELECT status, COUNT(*) as count FROM rules GROUP BY status')
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        cursor.execute('SELECT category, COUNT(*) as count FROM rules GROUP BY category')
        category_counts = {row['category']: row['count'] for row in cursor.fetchall()}
        
        cursor.execute('SELECT rule_type, COUNT(*) as count FROM rules GROUP BY rule_type')
        type_counts = {row['rule_type']: row['count'] for row in cursor.fetchall()}
        
        cursor.execute('SELECT COUNT(*) as total FROM rule_versions')
        total_versions = cursor.fetchone()['total']
        
        conn.close()
        
        return {
            "total_rules": total_rules,
            "total_versions": total_versions,
            "by_status": status_counts,
            "by_category": category_counts,
            "by_type": type_counts
        }
    
    def export_rules(self, output_path: str, format: str = "json"):
        rules = self.query_rules(RuleQuery(limit=10000))
        
        if format == "json":
            data = [rule.to_dict() for rule in rules]
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif format == "markdown":
            lines = ["# 规则库导出\n\n"]
            lines.append(f"导出时间: {datetime.now().isoformat()}\n\n")
            lines.append(f"规则总数: {len(rules)}\n\n")
            
            for rule in rules:
                lines.append(f"## {rule.id}: {rule.name}\n\n")
                lines.append(f"- 类别: {rule.category}\n")
                lines.append(f"- 类型: {rule.rule_type}\n")
                lines.append(f"- 状态: {rule.status.value}\n")
                lines.append(f"- 版本: {rule.current_version}\n")
                lines.append(f"- 描述: {rule.description}\n")
                lines.append(f"- 标签: {', '.join(rule.tags)}\n\n")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(''.join(lines))
        
        return output_path
    
    def import_rules(self, input_path: str, imported_by: str = "system") -> int:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        imported_count = 0
        for rule_data in data:
            try:
                self.store_rule(
                    name=rule_data['name'],
                    category=rule_data['category'],
                    rule_type=rule_data['rule_type'],
                    description=rule_data.get('description', ''),
                    content=rule_data.get('content', {}),
                    tags=rule_data.get('tags', []),
                    created_by=imported_by,
                    metadata=rule_data.get('metadata', {})
                )
                imported_count += 1
            except Exception as e:
                print(f"导入规则失败: {rule_data.get('name', 'unknown')}, 错误: {e}")
        
        return imported_count


def main():
    manager = RuleLibraryManager("test_rule_library.db")
    
    print("="*60)
    print("测试规则库管理器")
    print("="*60)
    
    rule1 = manager.store_rule(
        name="用户登录验证规则",
        category="security",
        rule_type="validation",
        description="用户登录时的密码验证规则",
        content={
            "min_length": 8,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_number": True,
            "require_special": False
        },
        tags=["登录", "密码", "安全"],
        created_by="admin"
    )
    print(f"\n创建规则: {rule1.id}")
    
    rule2 = manager.store_rule(
        name="订单金额计算规则",
        category="calculation",
        rule_type="formula",
        description="订单总金额的计算公式",
        content={
            "formula": "total = price * quantity - discount",
            "dependencies": ["price", "quantity", "discount"]
        },
        tags=["订单", "计算", "金额"],
        created_by="admin"
    )
    print(f"创建规则: {rule2.id}")
    
    updated_rule = manager.update_rule(
        rule1.id,
        content={
            "min_length": 10,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_number": True,
            "require_special": True
        },
        changed_by="admin",
        change_description="增加密码复杂度要求"
    )
    print(f"\n更新规则: {updated_rule.id}, 新版本: {updated_rule.current_version}")
    
    print("\n查询安全类规则:")
    security_rules = manager.query_rules(RuleQuery(category="security"))
    for r in security_rules:
        print(f"  - {r.id}: {r.name}")
    
    print("\n规则版本历史:")
    versions = manager.get_rule_versions(rule1.id)
    for v in versions:
        print(f"  - 版本 {v.version}: {v.change_type.value} - {v.change_description}")
    
    print("\n统计信息:")
    stats = manager.get_statistics()
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    import os
    if os.path.exists("test_rule_library.db"):
        os.remove("test_rule_library.db")
        print("\n清理测试数据库")


if __name__ == "__main__":
    main()
