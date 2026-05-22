#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强型自完善系统 - Enhanced Self-Improvement System

核心功能：
1. CrossProjectKnowledgeBase - 跨项目知识库
   - 标准化知识格式
   - 多项目共享机制
   - 知识权限控制
   - 知识版本管理

2. EnhancedBestPracticeExtractor - 增强最佳实践提取器
   - 多维度分析（架构/性能/安全/可维护性/可扩展性）
   - 成功案例学习
   - 实践有效性验证

3. FailurePatternLearner - 失败模式学习与预防系统
   - 失败案例分析
   - 模式识别与分类
   - 预防规则生成
   - 自动预警机制

使用示例：
    from enhanced_self_improvement import (
        CrossProjectKnowledgeBase,
        EnhancedBestPracticeExtractor,
        FailurePatternLearner
    )

    kb = CrossProjectKnowledgeBase()
    kb.initialize()
    kb.share_knowledge(knowledge_item, ['project1', 'project2'])

    extractor = EnhancedBestPracticeExtractor()
    practices = extractor.extract_from_success_case(case_data)

    learner = FailurePatternLearner()
    prevention = learner.learn_from_failure(failure_case)
"""

import json
import logging
import os
import re
import hashlib
import uuid
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeCategory(Enum):
    """知识类别"""
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    SECURITY = "security"
    TESTING = "testing"
    MAINTAINABILITY = "maintainability"
    SCALABILITY = "scalability"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    BEST_PRACTICE = "best_practice"
    ANTI_PATTERN = "anti_pattern"


class KnowledgeSource(Enum):
    """知识来源"""
    AUTO_EXTRACTED = "auto_extracted"
    MANUAL = "manual"
    RECOMMENDED = "recommended"
    LEARNED_FROM_FAILURE = "learned_from_failure"
    COMMUNITY = "community"


class KnowledgePermission(Enum):
    """知识权限"""
    PUBLIC = "public"
    PRIVATE = "private"
    SHARED = "shared"
    PROJECT_ONLY = "project_only"


class PracticeDimension(Enum):
    """最佳实践维度"""
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    SCALABILITY = "scalability"


class PracticeValidity(Enum):
    """实践有效性"""
    VALIDATED = "validated"
    PROVISIONAL = "provisional"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"


@dataclass
class StandardizedKnowledge:
    """
    标准化知识条目

    支持跨项目共享的统一知识格式。
    """
    id: str
    title: str
    category: KnowledgeCategory
    project: str
    version: str
    content: str
    tags: List[str] = field(default_factory=list)
    source: KnowledgeSource = KnowledgeSource.AUTO_EXTRACTED
    effectiveness: float = 0.5              # 0-1，使用效果评分
    usage_count: int = 0                    # 使用次数
    created_at: str = ""
    updated_at: str = ""
    author: str = ""
    permission: KnowledgePermission = KnowledgePermission.SHARED
    related_projects: List[str] = field(default_factory=list)
    success_cases: List[Dict[str, Any]] = field(default_factory=list)
    failure_cases: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.id:
            self.id = f"KB-{uuid.uuid4().hex[:12].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category.value,
            'project': self.project,
            'version': self.version,
            'content': self.content[:500] + '...' if len(self.content) > 500 else self.content,
            'tags': self.tags,
            'source': self.source.value,
            'effectiveness': round(self.effectiveness, 3),
            'usage_count': self.usage_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'author': self.author,
            'permission': self.permission.value,
            'related_projects': self.related_projects,
            'success_case_count': len(self.success_cases),
            'failure_case_count': len(self.failure_cases),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StandardizedKnowledge":
        if isinstance(data.get('category'), str):
            data['category'] = KnowledgeCategory(data['category'])
        if isinstance(data.get('source'), str):
            data['source'] = KnowledgeSource(data['source'])
        if isinstance(data.get('permission'), str):
            data['permission'] = KnowledgePermission(data['permission'])
        return cls(**data)


@dataclass
class BestPractice:
    """最佳实践"""
    practice_id: str
    title: str
    dimension: PracticeDimension
    description: str
    context: str                           # 适用场景
    implementation_steps: List[str]        # 实施步骤
    benefits: List[str]                    # 收益列表
    risks: List[str]                      # 风险列表
    examples: List[Dict[str, str]]         # 示例代码/配置
    validity: PracticeValidity = PracticeValidity.PROVISIONAL
    effectiveness_score: float = 0.7       # 有效性得分 (0-1)
    difficulty_level: int = 3              # 难度等级 (1-10)
    adoption_rate: float = 0.0             # 采用率 (0-1)
    source_case_id: str = ""               # 来源案例ID
    tags: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)
    metrics_impact: Dict[str, float] = field(default_factory=dict)
    created_at: str = ""
    last_validated: str = ""
    validation_history: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if not self.practice_id:
            self.practice_id = f"BP-{uuid.uuid4().hex[:8].upper()}"
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'practice_id': self.practice_id,
            'title': self.title,
            'dimension': self.dimension.value,
            'description': self.description,
            'context': self.context,
            'implementation_steps': self.implementation_steps,
            'benefits': self.benefits,
            'risks': self.risks,
            'examples': self.examples,
            'validity': self.validity.value,
            'effectiveness_score': round(self.effectiveness_score, 3),
            'difficulty_level': self.difficulty_level,
            'adoption_rate': round(self.adoption_rate, 3),
            'source_case_id': self.source_case_id,
            'tags': self.tags,
            'prerequisites': self.prerequisites,
            'anti_patterns': self.anti_patterns,
            'metrics_impact': self.metrics_impact,
            'created_at': self.created_at,
            'last_validated': self.last_validated
        }


@dataclass
class FailurePattern:
    """失败模式"""
    pattern_id: str
    name: str
    category: str
    description: str
    symptoms: List[str]                   # 症状列表
    root_causes: List[str]                # 根因列表
    contributing_factors: List[str]       # 促成因素
    prevention_rules: List[Dict[str, Any]] # 预防规则
    detection_methods: List[str]          # 检测方法
    severity: str                         # 严重程度
    frequency: int                        # 发生频率
    similar_cases: List[str]              # 相似案例ID
    learned_from: List[str]               # 学习来源
    effectiveness_of_prevention: float = 0.0  # 预防措施效果
    created_at: str = ""
    last_updated: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.pattern_id:
            self.pattern_id = f"FP-{uuid.uuid4().hex[:8].upper()}"
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            'pattern_id': self.pattern_id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'symptoms': self.symptoms,
            'root_causes': self.root_causes,
            'contributing_factors': self.contributing_factors,
            'prevention_rules': self.prevention_rules,
            'detection_methods': self.detection_methods,
            'severity': self.severity,
            'frequency': self.frequency,
            'similar_cases': self.similar_cases,
            'learned_from': self.learned_from,
            'effectiveness_of_prevention': round(self.effectiveness_of_prevention, 3),
            'created_at': self.created_at,
            'last_updated': self.last_updated,
            'metadata': self.metadata
        }


@dataclass
class PreventionWarning:
    """预防警告"""
    warning_id: str
    pattern_id: str
    pattern_name: str
    severity: str
    message: str
    triggered_by: List[str]               # 触发条件
    suggested_actions: List[str]          # 建议操作
    confidence: float                     # 置信度 (0-1)
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'warning_id': self.warning_id,
            'pattern_id': self.pattern_id,
            'pattern_name': self.pattern_name,
            'severity': self.severity,
            'message': self.message,
            'triggered_by': self.triggered_by,
            'suggested_actions': self.suggested_actions,
            'confidence': round(self.confidence, 3),
            'timestamp': self.timestamp
        }


class CrossProjectKnowledgeBase:
    """
    跨项目知识库

    支持标准化知识格式和多项目共享，
    实现知识的统一管理和跨项目复用。
    """

    DEFAULT_STORAGE_PATH = ".trae/skills/sanliu/data/cross_project_knowledge"

    def __init__(
        self,
        storage_path: Optional[str] = None,
        auto_save: bool = True
    ):
        self.storage_path = Path(storage_path or self.DEFAULT_STORAGE_PATH)
        self.auto_save = auto_save
        self.logger = logging.getLogger('CrossProjectKnowledgeBase')

        self.knowledge_store: Dict[str, StandardizedKnowledge] = {}
        self.project_index: Dict[str, Set[str]] = defaultdict(set)     # project_id -> knowledge_ids
        self.category_index: Dict[KnowledgeCategory, Set[str]] = defaultdict(set)
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)

        self._initialized = False

    def initialize(self) -> bool:
        """初始化知识库"""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)

            knowledge_file = self.storage_path / "knowledge_store.json"

            if knowledge_file.exists():
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for item_data in data.get('knowledge', []):
                    knowledge = StandardizedKnowledge.from_dict(item_data)
                    self._add_to_indices(knowledge)

            self._initialized = True
            self.logger.info(
                f"知识库初始化完成，已加载 {len(self.knowledge_store)} 条知识"
            )
            return True

        except Exception as e:
            self.logger.error(f"知识库初始化失败: {e}")
            return False

    def add_knowledge(
        self,
        knowledge: StandardizedKnowledge,
        overwrite: bool = False
    ) -> bool:
        """
        添加知识到知识库

        Args:
            knowledge: 标准化知识对象
            overwrite: 是否覆盖已有知识

        Returns:
            是否添加成功
        """
        if not self._initialized and not self.initialize():
            return False

        if knowledge.id in self.knowledge_store and not overwrite:
            self.logger.warning(f"知识 {knowledge.id} 已存在，跳过")
            return False

        self.knowledge_store[knowledge.id] = knowledge
        self._add_to_indices(knowledge)

        if self.auto_save:
            self._save()

        self.logger.info(f"已添加知识: {knowledge.id} - {knowledge.title}")
        return True

    def _add_to_indices(self, knowledge: StandardizedKnowledge):
        """更新索引"""
        self.project_index[knowledge.project].add(knowledge.id)
        self.category_index[knowledge.category].add(knowledge.id)

        for tag in knowledge.tags:
            self.tag_index[tag.lower()].add(knowledge.id)

    def share_knowledge(
        self,
        knowledge_id: str,
        target_projects: Optional[List[str]] = None,
        permission: KnowledgePermission = KnowledgePermission.SHARED
    ) -> bool:
        """
        共享知识到其他项目

        Args:
            knowledge_id: 知识ID
            target_projects: 目标项目列表（None表示所有项目）
            permission: 共享权限

        Returns:
            是否共享成功
        """
        if knowledge_id not in self.knowledge_store:
            self.logger.error(f"知识 {knowledge_id} 不存在")
            return False

        knowledge = self.knowledge_store[knowledge_id]
        knowledge.permission = permission

        if target_projects:
            for project in target_projects:
                knowledge.related_projects.append(project)
                self.project_index[project].add(knowledge_id)
        else:
            knowledge.permission = KnowledgePermission.PUBLIC

        knowledge.updated_at = datetime.now().isoformat()

        if self.auto_save:
            self._save()

        self.logger.info(
            f"知识 {knowledge_id} 已共享至 {len(target_projects or ['所有'])} 个项目"
        )
        return True

    def query_knowledge(
        self,
        query: str,
        category: Optional[KnowledgeCategory] = None,
        project: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
        min_effectiveness: float = 0.0
    ) -> List[StandardizedKnowledge]:
        """
        查询知识

        Args:
            query: 搜索关键词
            category: 知识类别过滤
            project: 项目过滤
            tags: 标签过滤
            limit: 返回数量限制
            min_effectiveness: 最低有效性阈值

        Returns:
            匹配的知识列表
        """
        results = []

        candidate_ids: Set[str] = set(self.knowledge_store.keys())

        if category:
            candidate_ids &= self.category_index.get(category, set())

        if project:
            candidate_ids &= self.project_index.get(project, set())

        if tags:
            tag_matches = set()
            for tag in tags:
                tag_matches |= self.tag_index.get(tag.lower(), set())
            candidate_ids &= tag_matches

        for kid in candidate_ids:
            knowledge = self.knowledge_store[kid]

            if knowledge.effectiveness < min_effectiveness:
                continue

            score = self._calculate_relevance(query, knowledge)

            if query and score == 0:
                continue

            results.append((knowledge, score))

        results.sort(key=lambda x: x[1], reverse=True)

        return [item[0] for item in results[:limit]]

    def query_similar_projects(
        self,
        query: str,
        current_project: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        查询相似项目的经验

        Args:
            query: 查询内容
            current_project: 当前项目ID
            limit: 返回数量限制

        Returns:
            相似项目的经验列表
        """
        all_knowledge = [
            k for k in self.knowledge_store.values()
            if k.project != current_project
            and k.effectiveness > 0.5
        ]

        scored = []
        for knowledge in all_knowledge:
            relevance = self._calculate_relevance(query, knowledge)
            if relevance > 0.1:
                scored.append({
                    'knowledge': knowledge,
                    'relevance': relevance,
                    'project': knowledge.project
                })

        scored.sort(key=lambda x: x['relevance'], reverse=True)

        return [
            {
                'project_id': item['project'],
                'title': item['knowledge'].title,
                'category': item['knowledge'].category.value,
                'effectiveness': item['knowledge'].effectiveness,
                'relevance_score': round(item['relevance'], 3),
                'summary': item['knowledge'].content[:200]
            }
            for item in scored[:limit]
        ]

    def record_usage(
        self,
        knowledge_id: str,
        success: bool = True,
        feedback: Optional[str] = None
    ) -> bool:
        """
        记录知识使用情况并更新有效性评分

        Args:
            knowledge_id: 知识ID
            success: 是否成功应用
            feedback: 用户反馈

        Returns:
            是否记录成功
        """
        if knowledge_id not in self.knowledge_store:
            return False

        knowledge = self.knowledge_store[knowledge_id]
        knowledge.usage_count += 1

        alpha = 0.3
        new_effectiveness = (1 - alpha) * knowledge.effectiveness + alpha * (1.0 if success else 0.3)
        knowledge.effectiveness = max(0.0, min(1.0, new_effectiveness))

        knowledge.updated_at = datetime.now().isoformat()

        if feedback:
            knowledge.metadata.setdefault('feedback', []).append({
                'timestamp': datetime.now().isoformat(),
                'success': success,
                'comment': feedback
            })

        if self.auto_save:
            self._save()

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        categories = Counter(k.category.value for k in self.knowledge_store.values())
        sources = Counter(k.source.value for k in self.knowledge_store.values())
        projects = Counter(k.project for k in self.knowledge_store.values())
        permissions = Counter(k.permission.value for k in self.knowledge_store.values())

        effective = sum(1 for k in self.knowledge_store.values() if k.effectiveness >= 0.7)
        total_usage = sum(k.usage_count for k in self.knowledge_store.values())

        return {
            'total_knowledge': len(self.knowledge_store),
            'by_category': dict(categories),
            'by_source': dict(sources),
            'by_project': dict(projects.most_common(10)),
            'by_permission': dict(permissions),
            'high_effective_count': effective,
            'total_usage_count': total_usage,
            'avg_effectiveness': (
                sum(k.effectiveness for k in self.knowledge_store.values()) / len(self.knowledge_store)
                if self.knowledge_store else 0
            )
        }

    def _calculate_relevance(self, query: str, knowledge: StandardizedKnowledge) -> float:
        """计算查询相关性得分"""
        if not query:
            return 0.5

        query_lower = query.lower()
        score = 0.0

        title_match = sum(1 for word in query_lower.split() if word in knowledge.title.lower())
        score += title_match * 3

        content_match = sum(1 for word in query_lower.split() if word in knowledge.content.lower())
        score += content_match * 1

        tag_match = sum(1 for tag in knowledge.tags if any(word in tag.lower() for word in query_lower.split()))
        score += tag_match * 2

        cat_match = query_lower in knowledge.category.value
        if cat_match:
            score += 2

        effectiveness_bonus = knowledge.effectiveness * 0.5
        usage_bonus = min(knowledge.usage_count / 100, 0.3)

        score += effectiveness_bonus + usage_bonus

        return score

    def _save(self):
        """保存知识库到文件"""
        try:
            data = {
                'version': '1.0',
                'updated_at': datetime.now().isoformat(),
                'knowledge': [k.to_dict() for k in self.knowledge_store.values()]
            }

            file_path = self.storage_path / "knowledge_store.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"保存知识库失败: {e}")


class EnhancedBestPracticeExtractor:
    """
    增强最佳实践提取器

    从成功案例中提炼可复用的最佳实践，
    支持多维度分析和有效性验证。
    """

    ANALYSIS_DIMENSIONS = list(PracticeDimension)

    DIMENSION_KEYWORDS = {
        PracticeDimension.ARCHITECTURE: [
            'architecture', 'design pattern', 'layer', 'module', 'component',
            'microservice', 'monolith', 'api', 'interface', 'abstraction'
        ],
        PracticeDimension.PERFORMANCE: [
            'performance', 'speed', 'latency', 'throughput', 'optimization',
            'cache', 'async', 'concurrent', 'memory', 'cpu', 'benchmark'
        ],
        PracticeDimension.SECURITY: [
            'security', 'authentication', 'authorization', 'encryption',
            'vulnerability', 'injection', 'xss', 'csrf', 'permission', 'audit'
        ],
        PracticeDimension.MAINTAINABILITY: [
            'maintainable', 'readable', 'refactor', 'clean code', 'documentation',
            'test coverage', 'code quality', 'technical debt', 'standard'
        ],
        PracticeDimension.SCALABILITY: [
            'scalable', 'scale', 'horizontal', 'vertical', 'load balance',
            'sharding', 'partition', 'distributed', 'cluster', 'elastic'
        ]
    }

    def __init__(self):
        self.logger = logging.getLogger('EnhancedBestPracticeExtractor')
        self.extracted_practices: List[BestPractice] = []
        self.validation_results: List[Dict[str, Any]] = []

    def extract_from_success_case(
        self,
        case_data: Dict[str, Any],
        dimensions: Optional[List[PracticeDimension]] = None
    ) -> List[BestPractice]:
        """
        从成功案例中提取最佳实践

        Args:
            case_data: 成功案例数据
                应包含: {
                    'case_id': str,
                    'title': str,
                    'description': str,
                    'problem_solved': str,
                    'solution_description': str,
                    'results': dict,
                    'lessons_learned': list,
                    'metrics_before': dict,
                    'metrics_after': dict,
                    'challenges_overcome': list,
                    'technologies_used': list,
                    'team_composition': str,
                    'duration_days': int
                }
            dimensions: 要分析的维度列表（默认全部分析）

        Returns:
            提取的最佳实践列表
        """
        dimensions = dimensions or self.ANALYSIS_DIMENSIONS
        practices = []

        case_text = self._concatenate_case_text(case_data)

        for dimension in dimensions:
            dimension_practices = self._analyze_dimension(case_data, dimension, case_text)
            practices.extend(dimension_practices)

        practices = self._deduplicate_practices(practices)

        for practice in practices:
            practice.source_case_id = case_data.get('case_id', '')
            self.extracted_practices.append(practice)

        self.logger.info(
            f"从案例 {case_data.get('case_id', 'unknown')} 提取了 {len(practices)} 条最佳实践"
        )

        return practices

    def _analyze_dimension(
        self,
        case_data: Dict[str, Any],
        dimension: PracticeDimension,
        full_text: str
    ) -> List[BestPractice]:
        """分析特定维度"""
        keywords = self.DIMENSION_KEYWORDS.get(dimension, [])
        practices = []

        keyword_matches = [kw for kw in keywords if kw.lower() in full_text.lower()]

        if not keyword_matches:
            return practices

        solution_text = case_data.get('solution_description', '')
        lessons = case_data.get('lessons_learned', [])
        challenges = case_data.get('challenges_overcome', [])
        metrics_before = case_data.get('metrics_before', {})
        metrics_after = case_data.get('metrics_after', {})

        key_insights = []
        for lesson in lessons:
            lesson_lower = lesson.lower()
            if any(kw.lower() in lesson_lower for kw in keywords):
                key_insights.append(lesson)

        if not key_insights:
            for challenge in challenges:
                challenge_lower = challenge.lower()
                if any(kw.lower() in challenge_lower for kw in keywords):
                    key_insights.append(f"解决挑战: {challenge}")

        if key_insights or solution_text:
            practice = BestPractice(
                title=f"{dimension.value.capitalize()}最佳实践: {case_data.get('title', '')[:40]}",
                dimension=dimension,
                description=self._generate_description(dimension, case_data, key_insights),
                context=f"适用于: {', '.join(case_data.get('technologies_used', []))}",
                implementation_steps=self._extract_implementation_steps(solution_text, lessons),
                benefits=self._extract_benefits(metrics_before, metrics_after),
                risks=self._identify_risks(challenges),
                examples=self._extract_examples(case_data),
                tags=keyword_matches[:5],
                metrics_impact=self._calculate_metrics_impact(metrics_before, metrics_after)
            )

            practice.effectiveness_score = self._estimate_effectiveness(practice, case_data)
            practice.validity = self._determine_validity(practice, case_data)

            practices.append(practice)

        return practices

    def validate_practice(self, practice: BestPractice) -> Tuple[bool, str]:
        """
        验证最佳实践的有效性

        Args:
            practice: 最佳实践对象

        Returns:
            (是否有效, 验证消息)
        """
        validation_issues = []

        if not practice.implementation_steps:
            validation_issues.append("缺少实施步骤")

        if not practice.benefits:
            validation_issues.append("缺少收益说明")

        if practice.effectiveness_score < 0.3:
            validation_issues.append(f"有效性得分过低 ({practice.effectiveness_score})")

        if len(practice.description) < 50:
            validation_issues.append("描述过于简短")

        has_code_example = any(ex.get('type') == 'code' for ex in practice.examples)
        if practice.difficulty_level <= 5 and not has_code_example:
            validation_issues.append("简单实践应包含代码示例")

        is_valid = len(validation_issues) == 0
        message = "验证通过" if is_valid else "; ".join(validation_issues)

        result = {
            'practice_id': practice.practice_id,
            'is_valid': is_valid,
            'issues': validation_issues,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }

        self.validation_results.append(result)

        if is_valid:
            practice.validity = PracticeValidity.VALIDATED
            practice.last_validated = datetime.now().isoformat()
            practice.validation_history.append(result)

        return is_valid, message

    def get_extraction_statistics(self) -> Dict[str, Any]:
        """获取提取统计信息"""
        dimensions = Counter(p.dimension.value for p in self.extracted_practices)
        validities = Counter(p.validity.value for p in self.extracted_practices)

        avg_effectiveness = (
            sum(p.effectiveness_score for p in self.extracted_practices) /
            len(self.extracted_practices)
            if self.extracted_practices else 0
        )

        avg_difficulty = (
            sum(p.difficulty_level for p in self.extracted_practices) /
            len(self.extracted_practices)
            if self.extracted_practices else 0
        )

        return {
            'total_practices_extracted': len(self.extracted_practices),
            'by_dimension': dict(dimensions),
            'by_validity': dict(validities),
            'avg_effectiveness': round(avg_effectiveness, 3),
            'avg_difficulty': round(avg_difficulty, 2),
            'validation_performed': len(self.validation_results),
            'validation_pass_rate': (
                sum(1 for r in self.validation_results if r['is_valid']) /
                len(self.validation_results)
                if self.validation_results else 0
            )
        }

    def _concatenate_case_text(self, case_data: Dict[str, Any]) -> str:
        """合并案例文本"""
        parts = [
            case_data.get('title', ''),
            case_data.get('description', ''),
            case_data.get('problem_solved', ''),
            case_data.get('solution_description', ''),
            ' '.join(case_data.get('lessons_learned', [])),
            ' '.join(case_data.get('challenges_overcome', [])),
            ' '.join(case_data.get('technologies_used', []))
        ]

        return ' '.join(filter(None, parts))

    def _generate_description(
        self,
        dimension: PracticeDimension,
        case_data: Dict[str, Any],
        insights: List[str]
    ) -> str:
        """生成实践描述"""
        base = f"基于{dimension.value}维度从成功案例中提取的实践。"

        problem = case_data.get('problem_solved', '')
        if problem:
            base += f"\n解决的问题: {problem}"

        if insights:
            base += "\n关键洞察:\n" + '\n'.join(f"- {ins}" for ins in insights[:3])

        return base

    def _extract_implementation_steps(self, solution: str, lessons: List[str]) -> List[str]:
        """提取实施步骤"""
        steps = []

        step_patterns = [
            r'(?:首先|第一步|1[\.、])\s*(.+)',
            r'(?:然后|第二步|2[\.、])\s*(.+)',
            r'(?:接着|第三步|3[\.、])\s*(.+)',
            r'(?:最后|最终|完成)\s*(.+)',
        ]

        text = solution + '\n' + '\n'.join(lessons)

        for pattern in step_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            steps.extend(matches)

        if not steps and solution:
            sentences = re.split(r'[。！？\n]', solution)
            steps = [s.strip() for s in sentences if len(s.strip()) > 10][:5]

        return steps[:6]

    def _extract_benefits(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any]
    ) -> List[str]:
        """提取收益"""
        benefits = []

        for metric, after_val in after.items():
            before_val = before.get(metric)
            if before_val is not None and isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                if before_val != 0:
                    change_pct = ((after_val - before_val) / abs(before_val)) * 100
                    direction = "提升" if after_val > before_val else ("降低" if metric in ['error_rate', 'latency'] else "变化")
                    benefits.append(f"{metric}: {direction}{abs(change_pct):.1f}%")

        if not benefits:
            benefits = ["提升整体质量", "改善可维护性", "降低技术债务"]

        return benefits[:5]

    def _identify_risks(self, challenges: List[str]) -> List[str]:
        """识别风险"""
        risk_keywords = ['风险', '问题', '困难', '挑战', '依赖', '复杂']
        risks = []

        for challenge in challenges:
            if any(kw in challenge for kw in risk_keywords):
                risks.append(challenge)

        return risks[:3]

    def _extract_examples(self, case_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """提取示例"""
        examples = []

        tech_stack = case_data.get('technologies_used', [])
        if tech_stack:
            examples.append({
                'type': 'tech_stack',
                'label': '技术栈',
                'content': ', '.join(tech_stack)
            })

        solution_snippet = case_data.get('solution_description', '')[:200]
        if solution_snippet:
            examples.append({
                'type': 'text',
                'label': '方案摘要',
                'content': solution_snippet
            })

        return examples

    def _calculate_metrics_impact(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any]
    ) -> Dict[str, float]:
        """计算指标影响"""
        impact = {}

        for metric, after_val in after.items():
            before_val = before.get(metric)
            if before_val is not None and isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                if before_val != 0:
                    impact[metric] = round((after_val - before_val) / abs(before_val), 3)

        return impact

    def _estimate_effectiveness(
        self,
        practice: BestPractice,
        case_data: Dict[str, Any]
    ) -> float:
        """估算有效性得分"""
        score = 0.5

        if practice.implementation_steps:
            score += 0.15

        if practice.benefits:
            score += 0.1

        if practice.metrics_impact:
            positive_impacts = sum(1 for v in practice.metrics_impact.values() if abs(v) > 0.1)
            score += min(0.2, positive_impacts * 0.05)

        duration = case_data.get('duration_days', 30)
        if duration < 30:
            score += 0.05

        return min(1.0, score)

    def _determine_validity(
        self,
        practice: BestPractice,
        case_data: Dict[str, Any]
    ) -> PracticeValidity:
        """确定实践有效性状态"""
        if practice.effectiveness_score >= 0.8:
            return PracticeValidity.VALIDATED
        elif practice.effectiveness_score >= 0.5:
            return PracticeValidity.PROVISIONAL
        else:
            return PracticeValidity.EXPERIMENTAL

    def _deduplicate_practices(self, practices: List[BestPractice]) -> List[BestPractice]:
        """去重实践"""
        seen_titles = set()
        unique = []

        for practice in practices:
            title_key = practice.title.lower()[:50]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique.append(practice)

        return unique


class FailurePatternLearner:
    """
    失败模式学习与预防系统

    从失败案例中学习，形成预防机制。
    """

    SEVERITY_LEVELS = ['critical', 'high', 'medium', 'low']

    PATTERN_TEMPLATES = {
        'performance_degradation': {
            'symptoms': ['响应时间增加', '吞吐量下降', '资源占用升高'],
            'root_causes': ['算法效率低', '数据库查询慢', '内存泄漏', '锁竞争'],
            'preventions': ['性能监控', '压力测试', '性能基线', '自动告警']
        },
        'security_vulnerability': {
            'symptoms': ['安全扫描告警', '入侵检测触发', '异常访问模式'],
            'root_causes': ['输入未验证', '权限配置错误', '加密不足', '依赖漏洞'],
            'preventions': ['安全审计', '依赖扫描', '渗透测试', '代码审查']
        },
        'deployment_failure': {
            'symptoms': ['部署回滚', '服务不可用', '配置错误'],
            'root_causes': ['配置缺失', '环境差异', '依赖不兼容', '脚本错误'],
            'preventions': ['部署清单', '环境一致性', '灰度发布', '自动化测试']
        },
        'data_corruption': {
            'symptoms': ['数据不一致', '数据丢失', '校验失败'],
            'root_causes': ['并发写入冲突', '事务处理不当', '备份失败', '硬件故障'],
            'preventions': ['事务管理', '数据校验', '定期备份', '冗余存储']
        },
        'integration_breakage': {
            'symptoms': ['API调用失败', '接口不兼容', '数据格式错误'],
            'root_causes': ['API变更未通知', '版本不匹配', '协议变更', '文档过时'],
            'preventions': ['版本锁定', '契约测试', '变更通知', '兼容层']
        }
    }

    def __init__(self):
        self.logger = logging.getLogger('FailurePatternLearner')
        self.patterns: Dict[str, FailurePattern] = {}
        self.failure_history: List[Dict[str, Any]] = []
        self.prevention_rules: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def learn_from_failure(self, failure: Dict[str, Any]) -> Dict[str, Any]:
        """
        从失败中学习

        Args:
            failure: 失败案例数据
                应包含: {
                    'failure_id': str,
                    'title': str,
                    'description': str,
                    'severity': str,
                    'category': str,
                    'symptoms': list,
                    'timeline': list,
                    'root_cause_analysis': str,
                    'impact': dict,
                    'resolution': str,
                    'lessons_learned': list,
                    'preventive_measures_taken': list,
                    'detected_at': str,
                    'resolved_at': str,
                    'related_systems': list,
                    'environment_context': dict
                }

        Returns:
            学习结果，包含识别的模式和预防规则
        """
        failure_id = failure.get('failure_id', f"FAIL-{uuid.uuid4().hex[:8]}")
        self.failure_history.append(failure)

        pattern = self._identify_pattern(failure)
        prevention = self._generate_prevention(pattern, failure)
        similar_cases = self._find_similar_failures(pattern)

        if pattern['pattern_id'] not in self.patterns:
            failure_pattern = FailurePattern(
                pattern_id=pattern['pattern_id'],
                name=pattern['name'],
                category=failure.get('category', 'unknown'),
                description=pattern['description'],
                symptoms=pattern.get('symptoms', []),
                root_causes=pattern.get('root_causes', []),
                contributing_factors=pattern.get('contributing_factors', []),
                prevention_rules=[prevention],
                detection_methods=pattern.get('detection_methods', []),
                severity=failure.get('severity', 'medium'),
                frequency=1,
                similar_cases=similar_cases,
                learned_from=[failure_id]
            )
            self.patterns[pattern['pattern_id']] = failure_pattern
        else:
            existing = self.patterns[pattern['pattern_id']]
            existing.frequency += 1
            existing.similar_cases.extend(similar_cases)
            existing.learned_from.append(failure_id)
            existing.prevention_rules.append(prevention)
            existing.last_updated = datetime.now().isoformat()

        self.prevention_rules[pattern['pattern_id']].append(prevention)

        result = {
            'failure_id': failure_id,
            'pattern': pattern,
            'prevention_rule': prevention,
            'similar_cases_found': len(similar_cases),
            'learning_confidence': self._calculate_learning_confidence(pattern, similar_cases),
            'recommendations': self._generate_recommendations(pattern, prevention)
        }

        self.logger.info(
            f"从失败 {failure_id} 中学习，识别模式: {pattern['name']}, "
            f"找到 {len(similar_cases)} 个相似案例"
        )

        return result

    def check_prevention(self, current_state: Dict[str, Any]) -> List[PreventionWarning]:
        """
        检查当前状态是否触发了已知的预防规则

        Args:
            current_state: 当前系统状态
                应包含: {
                    'metrics': dict,
                    'recent_errors': list,
                    'recent_changes': list,
                    'system_health': str,
                    'active_alerts': list,
                    'configuration': dict,
                    'deployment_info': dict
                }

        Returns:
            触发的预防警告列表
        """
        warnings = []

        state_text = self._serialize_state(current_state)

        for pattern_id, pattern in self.patterns.items():
            triggers = []
            confidence = 0.0

            for symptom in pattern.symptoms:
                if symptom.lower() in state_text.lower():
                    triggers.append(symptom)
                    confidence += 0.25

            for cause in pattern.root_causes:
                if cause.lower() in state_text.lower():
                    triggers.append(f"潜在根因: {cause}")
                    confidence += 0.15

            if confidence > 0.3:
                warning = PreventionWarning(
                    warning_id=f"WARN-{uuid.uuid4().hex[:8].upper()}",
                    pattern_id=pattern_id,
                    pattern_name=pattern.name,
                    severity=pattern.severity,
                    message=f"检测到可能触发 '{pattern.name}' 模式的迹象",
                    triggered_by=triggers,
                    suggested_actions=[
                        rule.get('action', 'review') for rule in pattern.prevention_rules[-3:]
                    ],
                    confidence=min(1.0, confidence),
                    timestamp=datetime.now().isoformat()
                )
                warnings.append(warning)

        warnings.sort(key=lambda w: (-self.SEVERITY_LEVELS.index(w.severity), -w.confidence))

        return warnings

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """获取模式统计信息"""
        categories = Counter(p.category for p in self.patterns.values())
        severities = Counter(p.severity for p in self.patterns.values())

        high_frequency = sorted(
            [(p.name, p.frequency) for p in self.patterns.values()],
            key=lambda x: x[1],
            reverse=True
        )[:10]

        total_preventions = sum(len(rules) for rules in self.prevention_rules.values())

        return {
            'total_patterns_identified': len(self.patterns),
            'total_failures_analyzed': len(self.failure_history),
            'total_prevention_rules_generated': total_preventions,
            'by_category': dict(categories),
            'by_severity': dict(severities),
            'most_frequent_patterns': high_frequency,
            'avg_prevention_coverage': (
                sum(len(p.detection_methods) for p in self.patterns.values()) /
                len(self.patterns)
                if self.patterns else 0
            )
        }

    def export_patterns(self, output_path: Optional[str] = None) -> str:
        """导出模式数据"""
        data = {
            'export_time': datetime.now().isoformat(),
            'patterns': [p.to_dict() for p in self.patterns.values()],
            'statistics': self.get_pattern_statistics()
        }

        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str

    def _identify_pattern(self, failure: Dict[str, Any]) -> Dict[str, Any]:
        """识别失败模式"""
        description = failure.get('description', '').lower()
        symptoms = failure.get('symptoms', [])
        root_cause = failure.get('root_cause_analysis', '').lower()
        category = failure.get('category', '').lower()

        best_match = None
        best_score = 0.0

        for template_name, template in self.PATTERN_TEMPLATES.items():
            score = 0.0

            for symptom in template['symptoms']:
                if symptom.lower() in description or any(symptom.lower() in s.lower() for s in symptoms):
                    score += 2

            for cause in template['root_causes']:
                if cause.lower() in root_cause:
                    score += 3

            if template_name.replace('_', ' ') in category:
                score += 2

            if score > best_score:
                best_score = score
                best_match = template_name

        pattern_id = f"PT-{best_match or 'UNKNOWN'}-{uuid.uuid4().hex[:6].upper()}"

        return {
            'pattern_id': pattern_id,
            'name': best_match.replace('_', ' ').title() if best_match else 'Unknown Pattern',
            'description': failure.get('description', ''),
            'symptoms': symptoms + self.PATTERN_TEMPLATES.get(best_match, {}).get('symptoms', [])[:3],
            'root_causes': [root_cause] if root_cause else [],
            'contributing_factors': failure.get('lessons_learned', []),
            'detection_methods': self._suggest_detection_methods(best_match),
            'match_score': best_score
        }

    def _generate_prevention(
        self,
        pattern: Dict[str, Any],
        failure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成预防规则"""
        template_name = next(
            (name for name, tpl in self.PATTERN_TEMPLATES.items()
             if name.replace('_', ' ') in pattern['name'].lower()),
            None
        )

        default_preventions = self.PATTERN_TEMPLATES.get(template_name, {}).get('preventions', [])

        custom_preventions = failure.get('preventive_measures_taken', [])
        lessons = failure.get('lessons_learned', [])

        all_preventions = list(set(default_preventions + custom_preventions + lessons))

        rule = {
            'rule_id': f"PR-{uuid.uuid4().hex[:8].upper()}",
            'pattern_id': pattern['pattern_id'],
            'actions': all_preventions[:5],
            'priority': failure.get('severity', 'medium'),
            'auto_applicable': len(custom_preventions) > 0,
            'effectiveness_estimate': 0.7,
            'created_from': failure.get('failure_id', ''),
            'conditions': pattern.get('symptoms', [])[:3]
        }

        return rule

    def _find_similar_failures(self, pattern: Dict[str, Any]) -> List[str]:
        """查找相似失败案例"""
        similar = []

        pattern_text = ' '.join([
            pattern.get('name', ''),
            pattern.get('description', ''),
            ' '.join(pattern.get('symptoms', []))
        ]).lower()

        for failure in self.failure_history[:-1]:
            failure_text = ' '.join([
                failure.get('title', ''),
                failure.get('description', ''),
                ' '.join(failure.get('symptoms', []))
            ]).lower()

            common_words = set(pattern_text.split()) & set(failure_text.split())
            similarity = len(common_words) / max(len(set(pattern_text.split())), 1)

            if similarity > 0.2:
                similar.append(failure.get('failure_id', ''))

        return similar

    def _suggest_detection_methods(self, pattern_template: Optional[str]) -> List[str]:
        """建议检测方法"""
        detection_map = {
            'performance_degradation': [
                '性能监控仪表板', 'APM工具集成', '响应时间追踪', '资源利用率监控'
            ],
            'security_vulnerability': [
                '安全扫描工具', '日志异常检测', '访问模式分析', '依赖漏洞扫描'
            ],
            'deployment_failure': [
                '部署检查清单', '健康检查端点', '配置验证工具', '回滚自动化'
            ],
            'data_corruption': [
                '数据完整性校验', '事务日志监控', '备份恢复测试', '数据对比工具'
            ],
            'integration_breakage': [
                '契约测试套件', 'API版本监控', '集成测试流水线', '接口文档同步'
            ]
        }

        return detection_map.get(pattern_template, ['常规监控', '日志分析', '定期审查'])

    def _calculate_learning_confidence(
        self,
        pattern: Dict[str, Any],
        similar_cases: List[str]
    ) -> float:
        """计算学习置信度"""
        confidence = 0.5

        match_score = pattern.get('match_score', 0)
        confidence += min(0.2, match_score / 20)

        confidence += min(0.2, len(similar_cases) * 0.05)

        if len(pattern.get('root_causes', [])) > 0:
            confidence += 0.1

        return min(1.0, confidence)

    def _generate_recommendations(
        self,
        pattern: Dict[str, Any],
        prevention: Dict[str, Any]
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        recommendations.append(f"将 '{pattern['name']}' 添加到团队知识库")

        if prevention.get('actions'):
            recommendations.append(f"实施以下预防措施: {', '.join(prevention['actions'][:3])}")

        recommendations.append("在CI/CD流程中加入相关检查点")

        recommendations.append("组织团队进行案例回顾会议")

        return recommendations

    def _serialize_state(self, state: Dict[str, Any]) -> str:
        """序列化状态为文本"""
        parts = []

        for key, value in state.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    parts.append(f"{k}: {v}")
            elif isinstance(value, list):
                parts.extend(str(item) for item in value[:10])
            else:
                parts.append(f"{key}: {value}")

        return ' '.join(parts)


if __name__ == '__main__':
    print("增强型自完善系统模块已加载")
