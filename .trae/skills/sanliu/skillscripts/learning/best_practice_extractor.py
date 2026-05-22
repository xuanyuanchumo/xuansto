#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最佳实践提取器 - Best Practice Extractor

从成功模式、优化模式和代码分析中提取最佳实践，并进行质量评估。

核心功能:
- 代码最佳实践提取
- 架构最佳实践提取
- 流程最佳实践提取
- 实践质量评估
- 实践验证和验证
"""

import json
import logging
import os
import re
import sys
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import hashlib

# 添加当前目录到路径
sys.path.insert(0, str(get_path_config().SKILL_ROOT))

try:
    from .pattern_recognizer import (
        PatternRecognizer,
        PatternType,
        PatternConfidence,
        RecognizedPattern
    )
except ImportError:
    try:
        from skillscripts.core.path_config_center import get_path_config
        from pattern_recognizer import (
            PatternRecognizer,
            PatternType,
            PatternConfidence,
            RecognizedPattern
        )
    except ImportError:
        # 如果还是失败，创建空类以避免导入错误
        class PatternRecognizer: pass
        class PatternType: pass
        class PatternConfidence: pass
        class RecognizedPattern: pass


class PracticeCategory(Enum):
    """实践类别枚举"""
    CODE = "code"
    ARCHITECTURE = "architecture"
    PROCESS = "process"
    PERFORMANCE = "performance"
    SECURITY = "security"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"


class PracticeQuality(Enum):
    """实践质量枚举"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class ExtractedPractice:
    """提取的最佳实践数据类"""
    practice_id: str
    category: PracticeCategory
    title: str
    description: str
    quality: PracticeQuality
    quality_score: float
    applicability: float
    impact: float
    evidence_count: int
    source_patterns: List[str]
    context_requirements: List[str] = field(default_factory=list)
    implementation_steps: List[Dict[str, Any]] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    verified: bool = False
    verification_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "practice_id": self.practice_id,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "quality": self.quality.value,
            "quality_score": self.quality_score,
            "applicability": self.applicability,
            "impact": self.impact,
            "evidence_count": self.evidence_count,
            "source_patterns": self.source_patterns,
            "context_requirements": self.context_requirements,
            "implementation_steps": self.implementation_steps,
            "benefits": self.benefits,
            "risks": self.risks,
            "examples": self.examples,
            "metrics": self.metrics,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "verified": self.verified,
            "verification_count": self.verification_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractedPractice':
        return cls(
            practice_id=data["practice_id"],
            category=PracticeCategory(data["category"]),
            title=data["title"],
            description=data["description"],
            quality=PracticeQuality(data["quality"]),
            quality_score=data["quality_score"],
            applicability=data["applicability"],
            impact=data["impact"],
            evidence_count=data["evidence_count"],
            source_patterns=data.get("source_patterns", []),
            context_requirements=data.get("context_requirements", []),
            implementation_steps=data.get("implementation_steps", []),
            benefits=data.get("benefits", []),
            risks=data.get("risks", []),
            examples=data.get("examples", []),
            metrics=data.get("metrics", {}),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            verified=data.get("verified", False),
            verification_count=data.get("verification_count", 0)
        )


class BestPracticeExtractor:
    """最佳实践提取器"""
    
    def __init__(
        self,
        pattern_recognizer: Optional[PatternRecognizer] = None,
        storage_path: Optional[str] = None
    ):
        self._pattern_recognizer = pattern_recognizer or PatternRecognizer()
        self._storage_path = Path(storage_path) if storage_path else None
        self._logger = logging.getLogger('BestPracticeExtractor')
        
        self._practices: Dict[str, ExtractedPractice] = {}
        self._category_index: Dict[str, Set[str]] = defaultdict(set)
        self._quality_index: Dict[str, Set[str]] = defaultdict(set)
        
        self._extraction_rules = self._initialize_extraction_rules()
        
        if self._storage_path:
            self._load_practices()
    
    def _initialize_extraction_rules(self) -> Dict[str, Any]:
        """初始化提取规则"""
        return {
            'code': {
                'min_confidence': PatternConfidence.HIGH,
                'min_occurrences': 3,
                'quality_threshold': 0.7,
                'keywords': [
                    'clean', 'readable', 'maintainable', 'modular',
                    'reusable', 'testable', 'documented', 'efficient'
                ]
            },
            'architecture': {
                'min_confidence': PatternConfidence.MEDIUM,
                'min_occurrences': 2,
                'quality_threshold': 0.6,
                'keywords': [
                    'scalable', 'modular', 'decoupled', 'layered',
                    'microservice', 'distributed', 'resilient'
                ]
            },
            'process': {
                'min_confidence': PatternConfidence.MEDIUM,
                'min_occurrences': 5,
                'quality_threshold': 0.65,
                'keywords': [
                    'automated', 'standardized', 'documented',
                    'repeatable', 'measurable', 'optimized'
                ]
            },
            'performance': {
                'min_confidence': PatternConfidence.HIGH,
                'min_occurrences': 2,
                'quality_threshold': 0.75,
                'keywords': [
                    'fast', 'optimized', 'cached', 'indexed',
                    'parallel', 'async', 'lazy', 'batch'
                ]
            },
            'security': {
                'min_confidence': PatternConfidence.VERY_HIGH,
                'min_occurrences': 1,
                'quality_threshold': 0.8,
                'keywords': [
                    'secure', 'encrypted', 'authenticated', 'authorized',
                    'validated', 'sanitized', 'protected', 'audited'
                ]
            },
            'testing': {
                'min_confidence': PatternConfidence.HIGH,
                'min_occurrences': 3,
                'quality_threshold': 0.7,
                'keywords': [
                    'comprehensive', 'automated', 'isolated',
                    'repeatable', 'fast', 'maintainable', 'clear'
                ]
            },
            'documentation': {
                'min_confidence': PatternConfidence.MEDIUM,
                'min_occurrences': 2,
                'quality_threshold': 0.6,
                'keywords': [
                    'clear', 'complete', 'updated', 'structured',
                    'searchable', 'versioned', 'accessible'
                ]
            },
            'deployment': {
                'min_confidence': PatternConfidence.HIGH,
                'min_occurrences': 2,
                'quality_threshold': 0.7,
                'keywords': [
                    'automated', 'repeatable', 'rollback',
                    'monitored', 'tested', 'versioned', 'documented'
                ]
            }
        }
    
    def extract_code_practice(
        self,
        pattern: RecognizedPattern,
        code_analysis: Optional[Dict[str, Any]] = None
    ) -> Optional[ExtractedPractice]:
        """提取代码最佳实践
        
        Args:
            pattern: 成功模式
            code_analysis: 代码分析结果
        
        Returns:
            提取的最佳实践
        """
        if pattern.pattern_type != PatternType.SUCCESS:
            return None
        
        rules = self._extraction_rules['code']
        
        if not self._meets_extraction_criteria(pattern, rules):
            return None
        
        practice_id = self._generate_practice_id(pattern, PracticeCategory.CODE)
        
        if practice_id in self._practices:
            return self._update_existing_practice(practice_id, pattern)
        
        quality_score = self._evaluate_code_quality(pattern, code_analysis)
        quality = self._determine_quality_level(quality_score)
        
        implementation_steps = self._extract_code_implementation_steps(pattern, code_analysis)
        benefits = self._extract_code_benefits(pattern, code_analysis)
        risks = self._identify_code_risks(pattern, code_analysis)
        
        practice = ExtractedPractice(
            practice_id=practice_id,
            category=PracticeCategory.CODE,
            title=self._generate_practice_title(pattern, PracticeCategory.CODE),
            description=self._generate_practice_description(pattern, PracticeCategory.CODE),
            quality=quality,
            quality_score=quality_score,
            applicability=self._calculate_applicability(pattern),
            impact=self._calculate_impact(pattern),
            evidence_count=pattern.occurrences,
            source_patterns=[pattern.pattern_id],
            context_requirements=self._extract_context_requirements(pattern),
            implementation_steps=implementation_steps,
            benefits=benefits,
            risks=risks,
            examples=pattern.examples[:3],
            metrics=self._extract_metrics(pattern),
            tags=self._extract_practice_tags(pattern, PracticeCategory.CODE)
        )
        
        self._practices[practice_id] = practice
        self._index_practice(practice)
        
        if self._storage_path:
            self._save_practices()
        
        self._logger.info(f"提取代码最佳实践: {practice.title} (质量: {quality.value})")
        return practice
    
    def extract_architecture_practice(
        self,
        pattern: RecognizedPattern,
        architecture_analysis: Optional[Dict[str, Any]] = None
    ) -> Optional[ExtractedPractice]:
        """提取架构最佳实践
        
        Args:
            pattern: 成功或优化模式
            architecture_analysis: 架构分析结果
        
        Returns:
            提取的最佳实践
        """
        if pattern.pattern_type not in [PatternType.SUCCESS, PatternType.OPTIMIZATION]:
            return None
        
        rules = self._extraction_rules['architecture']
        
        if not self._meets_extraction_criteria(pattern, rules):
            return None
        
        practice_id = self._generate_practice_id(pattern, PracticeCategory.ARCHITECTURE)
        
        if practice_id in self._practices:
            return self._update_existing_practice(practice_id, pattern)
        
        quality_score = self._evaluate_architecture_quality(pattern, architecture_analysis)
        quality = self._determine_quality_level(quality_score)
        
        implementation_steps = self._extract_architecture_implementation_steps(
            pattern, architecture_analysis
        )
        benefits = self._extract_architecture_benefits(pattern, architecture_analysis)
        risks = self._identify_architecture_risks(pattern, architecture_analysis)
        
        practice = ExtractedPractice(
            practice_id=practice_id,
            category=PracticeCategory.ARCHITECTURE,
            title=self._generate_practice_title(pattern, PracticeCategory.ARCHITECTURE),
            description=self._generate_practice_description(pattern, PracticeCategory.ARCHITECTURE),
            quality=quality,
            quality_score=quality_score,
            applicability=self._calculate_applicability(pattern),
            impact=self._calculate_impact(pattern),
            evidence_count=pattern.occurrences,
            source_patterns=[pattern.pattern_id],
            context_requirements=self._extract_context_requirements(pattern),
            implementation_steps=implementation_steps,
            benefits=benefits,
            risks=risks,
            examples=pattern.examples[:3],
            metrics=self._extract_metrics(pattern),
            tags=self._extract_practice_tags(pattern, PracticeCategory.ARCHITECTURE)
        )
        
        self._practices[practice_id] = practice
        self._index_practice(practice)
        
        if self._storage_path:
            self._save_practices()
        
        self._logger.info(f"提取架构最佳实践: {practice.title} (质量: {quality.value})")
        return practice
    
    def extract_process_practice(
        self,
        pattern: RecognizedPattern,
        process_analysis: Optional[Dict[str, Any]] = None
    ) -> Optional[ExtractedPractice]:
        """提取流程最佳实践
        
        Args:
            pattern: 成功模式
            process_analysis: 流程分析结果
        
        Returns:
            提取的最佳实践
        """
        if pattern.pattern_type != PatternType.SUCCESS:
            return None
        
        rules = self._extraction_rules['process']
        
        if not self._meets_extraction_criteria(pattern, rules):
            return None
        
        practice_id = self._generate_practice_id(pattern, PracticeCategory.PROCESS)
        
        if practice_id in self._practices:
            return self._update_existing_practice(practice_id, pattern)
        
        quality_score = self._evaluate_process_quality(pattern, process_analysis)
        quality = self._determine_quality_level(quality_score)
        
        implementation_steps = self._extract_process_implementation_steps(pattern, process_analysis)
        benefits = self._extract_process_benefits(pattern, process_analysis)
        risks = self._identify_process_risks(pattern, process_analysis)
        
        practice = ExtractedPractice(
            practice_id=practice_id,
            category=PracticeCategory.PROCESS,
            title=self._generate_practice_title(pattern, PracticeCategory.PROCESS),
            description=self._generate_practice_description(pattern, PracticeCategory.PROCESS),
            quality=quality,
            quality_score=quality_score,
            applicability=self._calculate_applicability(pattern),
            impact=self._calculate_impact(pattern),
            evidence_count=pattern.occurrences,
            source_patterns=[pattern.pattern_id],
            context_requirements=self._extract_context_requirements(pattern),
            implementation_steps=implementation_steps,
            benefits=benefits,
            risks=risks,
            examples=pattern.examples[:3],
            metrics=self._extract_metrics(pattern),
            tags=self._extract_practice_tags(pattern, PracticeCategory.PROCESS)
        )
        
        self._practices[practice_id] = practice
        self._index_practice(practice)
        
        if self._storage_path:
            self._save_practices()
        
        self._logger.info(f"提取流程最佳实践: {practice.title} (质量: {quality.value})")
        return practice
    
    def evaluate_practice_quality(
        self,
        practice_id: str,
        additional_evidence: Optional[Dict[str, Any]] = None
    ) -> Tuple[PracticeQuality, float]:
        """评估实践质量
        
        Args:
            practice_id: 实践ID
            additional_evidence: 额外证据
        
        Returns:
            (质量级别, 质量分数)
        """
        practice = self._practices.get(practice_id)
        if not practice:
            return PracticeQuality.POOR, 0.0
        
        base_score = practice.quality_score
        
        evidence_factor = min(practice.evidence_count / 10.0, 1.0)
        verification_factor = min(practice.verification_count / 5.0, 1.0)
        impact_factor = practice.impact
        applicability_factor = practice.applicability
        
        final_score = (
            base_score * 0.3 +
            evidence_factor * 0.2 +
            verification_factor * 0.2 +
            impact_factor * 0.15 +
            applicability_factor * 0.15
        )
        
        if additional_evidence:
            consistency_score = self._check_practice_consistency(practice, additional_evidence)
            final_score = final_score * 0.8 + consistency_score * 0.2
        
        quality = self._determine_quality_level(final_score)
        
        return quality, final_score
    
    def verify_practice(
        self,
        practice_id: str,
        verification_data: Dict[str, Any]
    ) -> bool:
        """验证实践
        
        Args:
            practice_id: 实践ID
            verification_data: 验证数据
        
        Returns:
            验证是否成功
        """
        practice = self._practices.get(practice_id)
        if not practice:
            return False
        
        success = verification_data.get('success', False)
        
        if success:
            practice.verification_count += 1
            
            if practice.verification_count >= 3:
                practice.verified = True
        
        practice.updated_at = datetime.now()
        
        if self._storage_path:
            self._save_practices()
        
        return success
    
    def get_practices_by_category(
        self,
        category: PracticeCategory,
        min_quality: Optional[PracticeQuality] = None
    ) -> List[ExtractedPractice]:
        """按类别获取实践
        
        Args:
            category: 实践类别
            min_quality: 最低质量
        
        Returns:
            实践列表
        """
        practice_ids = self._category_index.get(category.value, set())
        practices = [self._practices[pid] for pid in practice_ids if pid in self._practices]
        
        if min_quality:
            quality_order = [
                PracticeQuality.CRITICAL,
                PracticeQuality.POOR,
                PracticeQuality.ACCEPTABLE,
                PracticeQuality.GOOD,
                PracticeQuality.EXCELLENT
            ]
            min_index = quality_order.index(min_quality)
            practices = [
                p for p in practices
                if quality_order.index(p.quality) >= min_index
            ]
        
        return sorted(practices, key=lambda p: p.quality_score, reverse=True)
    
    def get_top_practices(
        self,
        category: Optional[PracticeCategory] = None,
        limit: int = 10
    ) -> List[ExtractedPractice]:
        """获取顶级实践
        
        Args:
            category: 实践类别（可选）
            limit: 数量限制
        
        Returns:
            顶级实践列表
        """
        if category:
            practices = self.get_practices_by_category(category)
        else:
            practices = list(self._practices.values())
        
        scored_practices = []
        for p in practices:
            score = (
                p.quality_score * 0.3 +
                p.impact * 0.25 +
                p.applicability * 0.2 +
                min(p.evidence_count / 10.0, 1.0) * 0.15 +
                min(p.verification_count / 5.0, 1.0) * 0.1
            )
            scored_practices.append((p, score))
        
        scored_practices.sort(key=lambda x: x[1], reverse=True)
        
        return [p for p, s in scored_practices[:limit]]
    
    def _meets_extraction_criteria(
        self,
        pattern: RecognizedPattern,
        rules: Dict[str, Any]
    ) -> bool:
        """检查是否满足提取条件"""
        confidence_order = [
            PatternConfidence.VERY_LOW,
            PatternConfidence.LOW,
            PatternConfidence.MEDIUM,
            PatternConfidence.HIGH,
            PatternConfidence.VERY_HIGH
        ]
        
        min_confidence = rules['min_confidence']
        min_confidence_index = confidence_order.index(min_confidence)
        pattern_confidence_index = confidence_order.index(pattern.confidence)
        
        if pattern_confidence_index < min_confidence_index:
            return False
        
        if pattern.occurrences < rules['min_occurrences']:
            return False
        
        if pattern.confidence_score < rules['quality_threshold']:
            return False
        
        return True
    
    def _generate_practice_id(
        self,
        pattern: RecognizedPattern,
        category: PracticeCategory
    ) -> str:
        """生成实践ID"""
        signature = f"{category.value}-{pattern.pattern_type.value}-{pattern.name}"
        hash_part = hashlib.md5(signature.encode()).hexdigest()[:8]
        return f"PRACTICE-{category.value.upper()}-{hash_part}"
    
    def _update_existing_practice(
        self,
        practice_id: str,
        pattern: RecognizedPattern
    ) -> ExtractedPractice:
        """更新现有实践"""
        practice = self._practices[practice_id]
        
        practice.evidence_count += 1
        practice.updated_at = datetime.now()
        
        if pattern.pattern_id not in practice.source_patterns:
            practice.source_patterns.append(pattern.pattern_id)
        
        if len(practice.examples) < 10:
            practice.examples.extend(pattern.examples[:2])
        
        quality, quality_score = self.evaluate_practice_quality(practice_id)
        practice.quality = quality
        practice.quality_score = quality_score
        
        return practice
    
    def _evaluate_code_quality(
        self,
        pattern: RecognizedPattern,
        code_analysis: Optional[Dict[str, Any]]
    ) -> float:
        """评估代码质量"""
        score = pattern.confidence_score * 0.4
        
        score += min(pattern.occurrences / 10.0, 1.0) * 0.2
        
        if code_analysis:
            if 'complexity' in code_analysis:
                complexity = code_analysis['complexity']
                if complexity < 10:
                    score += 0.15
                elif complexity < 20:
                    score += 0.1
                elif complexity < 30:
                    score += 0.05
            
            if 'test_coverage' in code_analysis:
                coverage = code_analysis['test_coverage']
                score += min(coverage / 100.0, 1.0) * 0.15
            
            if 'documentation' in code_analysis:
                doc_score = code_analysis['documentation']
                score += min(doc_score, 1.0) * 0.1
        else:
            score += 0.2
        
        return min(score, 1.0)
    
    def _evaluate_architecture_quality(
        self,
        pattern: RecognizedPattern,
        architecture_analysis: Optional[Dict[str, Any]]
    ) -> float:
        """评估架构质量"""
        score = pattern.confidence_score * 0.35
        
        score += min(pattern.occurrences / 8.0, 1.0) * 0.2
        
        if architecture_analysis:
            if 'modularity' in architecture_analysis:
                score += architecture_analysis['modularity'] * 0.15
            
            if 'scalability' in architecture_analysis:
                score += architecture_analysis['scalability'] * 0.15
            
            if 'maintainability' in architecture_analysis:
                score += architecture_analysis['maintainability'] * 0.15
        else:
            score += 0.25
        
        return min(score, 1.0)
    
    def _evaluate_process_quality(
        self,
        pattern: RecognizedPattern,
        process_analysis: Optional[Dict[str, Any]]
    ) -> float:
        """评估流程质量"""
        score = pattern.confidence_score * 0.3
        
        score += min(pattern.occurrences / 15.0, 1.0) * 0.25
        
        if process_analysis:
            if 'automation_level' in process_analysis:
                score += process_analysis['automation_level'] * 0.15
            
            if 'efficiency' in process_analysis:
                score += process_analysis['efficiency'] * 0.15
            
            if 'reliability' in process_analysis:
                score += process_analysis['reliability'] * 0.15
        else:
            score += 0.3
        
        return min(score, 1.0)
    
    def _determine_quality_level(self, score: float) -> PracticeQuality:
        """确定质量级别"""
        if score >= 0.9:
            return PracticeQuality.EXCELLENT
        elif score >= 0.75:
            return PracticeQuality.GOOD
        elif score >= 0.6:
            return PracticeQuality.ACCEPTABLE
        elif score >= 0.4:
            return PracticeQuality.POOR
        else:
            return PracticeQuality.CRITICAL
    
    def _calculate_applicability(self, pattern: RecognizedPattern) -> float:
        """计算适用性"""
        applicability = 0.5
        
        if pattern.context:
            context_diversity = len(set(str(v) for v in pattern.context.values()))
            applicability += min(context_diversity / 5.0, 0.3)
        
        if len(pattern.tags) > 3:
            applicability += 0.1
        
        if pattern.occurrences > 5:
            applicability += 0.1
        
        return min(applicability, 1.0)
    
    def _calculate_impact(self, pattern: RecognizedPattern) -> float:
        """计算影响力"""
        impact = pattern.confidence_score * 0.5
        
        if pattern.pattern_type == PatternType.OPTIMIZATION:
            impact += 0.2
        
        if pattern.occurrences > 10:
            impact += 0.15
        
        if pattern.confidence in [PatternConfidence.HIGH, PatternConfidence.VERY_HIGH]:
            impact += 0.15
        
        return min(impact, 1.0)
    
    def _extract_context_requirements(self, pattern: RecognizedPattern) -> List[str]:
        """提取上下文要求"""
        requirements = []
        
        if pattern.context:
            for key, value in pattern.context.items():
                if isinstance(value, (str, int, float, bool)):
                    requirements.append(f"{key}: {value}")
        
        if 'environment' in pattern.features:
            requirements.append(f"环境: {pattern.features['environment']}")
        
        return requirements[:5]
    
    def _extract_code_implementation_steps(
        self,
        pattern: RecognizedPattern,
        code_analysis: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """提取代码实现步骤"""
        steps = []
        
        steps.append({
            "step": 1,
            "action": "分析现有代码结构",
            "details": "识别需要改进的代码区域"
        })
        
        if pattern.features:
            if 'code_length' in pattern.features:
                steps.append({
                    "step": 2,
                    "action": "优化代码长度",
                    "details": f"建议代码长度: {pattern.features['code_length']} 字符"
                })
            
            if 'function_count' in pattern.features:
                steps.append({
                    "step": 3,
                    "action": "组织函数结构",
                    "details": f"建议函数数量: {pattern.features['function_count']}"
                })
        
        steps.append({
            "step": len(steps) + 1,
            "action": "编写单元测试",
            "details": "确保代码质量和可维护性"
        })
        
        steps.append({
            "step": len(steps) + 1,
            "action": "更新文档",
            "details": "记录变更和使用说明"
        })
        
        return steps
    
    def _extract_architecture_implementation_steps(
        self,
        pattern: RecognizedPattern,
        architecture_analysis: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """提取架构实现步骤"""
        steps = []
        
        steps.append({
            "step": 1,
            "action": "评估现有架构",
            "details": "分析当前架构的优缺点"
        })
        
        steps.append({
            "step": 2,
            "action": "设计改进方案",
            "details": "基于成功模式设计架构改进"
        })
        
        steps.append({
            "step": 3,
            "action": "制定迁移计划",
            "details": "规划从当前架构到目标架构的迁移路径"
        })
        
        steps.append({
            "step": 4,
            "action": "实施变更",
            "details": "逐步实施架构改进"
        })
        
        steps.append({
            "step": 5,
            "action": "验证和监控",
            "details": "验证架构改进效果并持续监控"
        })
        
        return steps
    
    def _extract_process_implementation_steps(
        self,
        pattern: RecognizedPattern,
        process_analysis: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """提取流程实现步骤"""
        steps = []
        
        steps.append({
            "step": 1,
            "action": "文档化当前流程",
            "details": "记录现有流程的每个步骤"
        })
        
        steps.append({
            "step": 2,
            "action": "识别改进机会",
            "details": "基于成功模式识别可优化的环节"
        })
        
        steps.append({
            "step": 3,
            "action": "设计新流程",
            "details": "整合最佳实践设计改进流程"
        })
        
        steps.append({
            "step": 4,
            "action": "试点实施",
            "details": "在小范围内试点新流程"
        })
        
        steps.append({
            "step": 5,
            "action": "全面推广",
            "details": "根据试点结果全面推广新流程"
        })
        
        return steps
    
    def _extract_code_benefits(
        self,
        pattern: RecognizedPattern,
        code_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """提取代码收益"""
        benefits = []
        
        if pattern.confidence_score > 0.8:
            benefits.append("高可靠性和稳定性")
        
        if pattern.occurrences > 5:
            benefits.append("经过多次验证")
        
        if code_analysis:
            if code_analysis.get('test_coverage', 0) > 80:
                benefits.append("高测试覆盖率")
            
            if code_analysis.get('complexity', 100) < 15:
                benefits.append("低代码复杂度")
        
        if not benefits:
            benefits.append("提升代码质量")
        
        return benefits
    
    def _extract_architecture_benefits(
        self,
        pattern: RecognizedPattern,
        architecture_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """提取架构收益"""
        benefits = []
        
        if pattern.pattern_type == PatternType.OPTIMIZATION:
            benefits.append("性能显著提升")
        
        if architecture_analysis:
            if architecture_analysis.get('scalability', 0) > 0.7:
                benefits.append("良好的可扩展性")
            
            if architecture_analysis.get('maintainability', 0) > 0.7:
                benefits.append("易于维护")
        
        if not benefits:
            benefits.append("改善架构设计")
        
        return benefits
    
    def _extract_process_benefits(
        self,
        pattern: RecognizedPattern,
        process_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """提取流程收益"""
        benefits = []
        
        if pattern.occurrences > 10:
            benefits.append("流程稳定可靠")
        
        if process_analysis:
            if process_analysis.get('automation_level', 0) > 0.7:
                benefits.append("高度自动化")
            
            if process_analysis.get('efficiency', 0) > 0.7:
                benefits.append("执行效率高")
        
        if not benefits:
            benefits.append("优化工作流程")
        
        return benefits
    
    def _identify_code_risks(
        self,
        pattern: RecognizedPattern,
        code_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """识别代码风险"""
        risks = []
        
        if pattern.occurrences < 3:
            risks.append("验证次数较少")
        
        if code_analysis:
            if code_analysis.get('complexity', 0) > 20:
                risks.append("代码复杂度较高")
            
            if code_analysis.get('test_coverage', 100) < 60:
                risks.append("测试覆盖率不足")
        
        if not risks:
            risks.append("需要持续监控")
        
        return risks
    
    def _identify_architecture_risks(
        self,
        pattern: RecognizedPattern,
        architecture_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """识别架构风险"""
        risks = []
        
        if pattern.occurrences < 2:
            risks.append("应用案例较少")
        
        if architecture_analysis:
            if architecture_analysis.get('scalability', 1) < 0.5:
                risks.append("可扩展性有限")
        
        if not risks:
            risks.append("需要评估适用性")
        
        return risks
    
    def _identify_process_risks(
        self,
        pattern: RecognizedPattern,
        process_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """识别流程风险"""
        risks = []
        
        if pattern.occurrences < 5:
            risks.append("流程验证不充分")
        
        if process_analysis:
            if process_analysis.get('automation_level', 1) < 0.5:
                risks.append("自动化程度低")
        
        if not risks:
            risks.append("需要定期审查")
        
        return risks
    
    def _extract_metrics(self, pattern: RecognizedPattern) -> Dict[str, Any]:
        """提取指标"""
        metrics = {
            "occurrences": pattern.occurrences,
            "confidence_score": pattern.confidence_score,
            "first_seen": pattern.first_seen.isoformat(),
            "last_seen": pattern.last_seen.isoformat()
        }
        
        if pattern.features:
            for key, value in pattern.features.items():
                if isinstance(value, (int, float)):
                    metrics[f"feature_{key}"] = value
        
        return metrics
    
    def _extract_practice_tags(
        self,
        pattern: RecognizedPattern,
        category: PracticeCategory
    ) -> List[str]:
        """提取实践标签"""
        tags = [category.value]
        
        tags.extend(pattern.tags[:3])
        
        rules = self._extraction_rules.get(category.value, {})
        keywords = rules.get('keywords', [])
        
        for keyword in keywords:
            if keyword.lower() in pattern.description.lower():
                tags.append(keyword)
        
        return list(set(tags))[:8]
    
    def _generate_practice_title(
        self,
        pattern: RecognizedPattern,
        category: PracticeCategory
    ) -> str:
        """生成实践标题"""
        category_names = {
            PracticeCategory.CODE: "代码",
            PracticeCategory.ARCHITECTURE: "架构",
            PracticeCategory.PROCESS: "流程",
            PracticeCategory.PERFORMANCE: "性能",
            PracticeCategory.SECURITY: "安全",
            PracticeCategory.TESTING: "测试",
            PracticeCategory.DOCUMENTATION: "文档",
            PracticeCategory.DEPLOYMENT: "部署"
        }
        
        category_name = category_names.get(category, "通用")
        
        return f"{category_name}最佳实践: {pattern.name}"
    
    def _generate_practice_description(
        self,
        pattern: RecognizedPattern,
        category: PracticeCategory
    ) -> str:
        """生成实践描述"""
        return f"基于{pattern.occurrences}次成功应用提取的{category.value}最佳实践。{pattern.description}"
    
    def _check_practice_consistency(
        self,
        practice: ExtractedPractice,
        evidence: Dict[str, Any]
    ) -> float:
        """检查实践一致性"""
        consistency_scores = []
        
        if 'success' in evidence:
            consistency_scores.append(1.0 if evidence['success'] else 0.0)
        
        if 'metrics' in evidence:
            for key, value in evidence['metrics'].items():
                if key in practice.metrics:
                    expected = practice.metrics[key]
                    if isinstance(expected, (int, float)) and isinstance(value, (int, float)):
                        if expected != 0:
                            sim = 1.0 - abs(expected - value) / abs(expected)
                            consistency_scores.append(max(0, sim))
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5
    
    def _index_practice(self, practice: ExtractedPractice) -> None:
        """索引实践"""
        self._category_index[practice.category.value].add(practice.practice_id)
        self._quality_index[practice.quality.value].add(practice.practice_id)
    
    def _save_practices(self) -> None:
        """保存实践"""
        if not self._storage_path:
            return
        
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "practices": [p.to_dict() for p in self._practices.values()]
            }
            
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            temp_file = self._storage_path.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            temp_file.replace(self._storage_path)
            
        except Exception as e:
            self._logger.error(f"保存实践失败: {e}")
    
    def _load_practices(self) -> None:
        """加载实践"""
        if not self._storage_path or not self._storage_path.exists():
            return
        
        try:
            with open(self._storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for practice_data in data.get("practices", []):
                practice = ExtractedPractice.from_dict(practice_data)
                self._practices[practice.practice_id] = practice
                self._index_practice(practice)
            
            self._logger.info(f"已加载 {len(self._practices)} 个最佳实践")
            
        except Exception as e:
            self._logger.error(f"加载实践失败: {e}")
    
    def analyze_practice_correlations(
        self,
        practice_id: str
    ) -> Dict[str, Any]:
        """分析实践关联
        
        Args:
            practice_id: 实践ID
        
        Returns:
            关联分析结果
        """
        practice = self._practices.get(practice_id)
        if not practice:
            return {"status": "error", "message": "实践不存在"}
        
        correlations = {
            "practice_id": practice_id,
            "strongly_related": [],
            "moderately_related": [],
            "weakly_related": [],
            "complementary": [],
            "conflicting": []
        }
        
        for pid, p in self._practices.items():
            if pid == practice_id:
                continue
            
            tag_similarity = self._calculate_tag_similarity(practice.tags, p.tags)
            context_overlap = self._calculate_context_overlap(
                practice.context_requirements,
                p.context_requirements
            )
            benefit_similarity = self._calculate_list_similarity(
                practice.benefits,
                p.benefits
            )
            
            overall_similarity = (
                tag_similarity * 0.4 +
                context_overlap * 0.3 +
                benefit_similarity * 0.3
            )
            
            relation = {
                "practice_id": pid,
                "title": p.title,
                "similarity": overall_similarity,
                "tag_similarity": tag_similarity,
                "context_overlap": context_overlap,
                "benefit_similarity": benefit_similarity
            }
            
            if overall_similarity > 0.7:
                correlations["strongly_related"].append(relation)
            elif overall_similarity > 0.5:
                correlations["moderately_related"].append(relation)
            elif overall_similarity > 0.3:
                correlations["weakly_related"].append(relation)
            
            if self._are_complementary(practice, p):
                correlations["complementary"].append({
                    "practice_id": pid,
                    "title": p.title,
                    "reason": "收益互补"
                })
            
            if self._are_conflicting(practice, p):
                correlations["conflicting"].append({
                    "practice_id": pid,
                    "title": p.title,
                    "reason": "存在冲突风险"
                })
        
        for key in ["strongly_related", "moderately_related", "weakly_related"]:
            correlations[key] = sorted(
                correlations[key],
                key=lambda x: x["similarity"],
                reverse=True
            )[:5]
        
        return correlations
    
    def track_practice_evolution(
        self,
        practice_id: str,
        evolution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """跟踪实践演化
        
        Args:
            practice_id: 实践ID
            evolution_data: 演化数据
        
        Returns:
            演化分析结果
        """
        practice = self._practices.get(practice_id)
        if not practice:
            return {"status": "error", "message": "实践不存在"}
        
        evolution_result = {
            "practice_id": practice_id,
            "timestamp": datetime.now().isoformat(),
            "evolution_type": "unknown",
            "changes": [],
            "trend": "stable"
        }
        
        if 'quality_change' in evolution_data:
            old_quality = practice.quality_score
            new_quality = evolution_data['quality_change']
            change = new_quality - old_quality
            
            evolution_result["changes"].append({
                "aspect": "quality",
                "old_value": old_quality,
                "new_value": new_quality,
                "change": change
            })
            
            if change > 0.1:
                evolution_result["evolution_type"] = "improving"
                evolution_result["trend"] = "upward"
            elif change < -0.1:
                evolution_result["evolution_type"] = "degrading"
                evolution_result["trend"] = "downward"
        
        if 'evidence_change' in evolution_data:
            old_evidence = practice.evidence_count
            new_evidence = old_evidence + evolution_data['evidence_change']
            
            evolution_result["changes"].append({
                "aspect": "evidence_count",
                "old_value": old_evidence,
                "new_value": new_evidence,
                "change": evolution_data['evidence_change']
            })
        
        if 'verification_change' in evolution_data:
            old_verification = practice.verification_count
            new_verification = old_verification + evolution_data['verification_change']
            
            evolution_result["changes"].append({
                "aspect": "verification_count",
                "old_value": old_verification,
                "new_value": new_verification,
                "change": evolution_data['verification_change']
            })
        
        if not practice.metadata.get('evolution_history'):
            practice.metadata['evolution_history'] = []
        
        practice.metadata['evolution_history'].append(evolution_result)
        
        if len(practice.metadata['evolution_history']) > 20:
            practice.metadata['evolution_history'] = practice.metadata['evolution_history'][-20:]
        
        if self._storage_path:
            self._save_practices()
        
        return evolution_result
    
    def recommend_practices(
        self,
        context: Dict[str, Any],
        objectives: List[str],
        constraints: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """推荐实践
        
        Args:
            context: 上下文信息
            objectives: 目标列表
            constraints: 约束条件
            limit: 推荐数量限制
        
        Returns:
            推荐实践列表
        """
        recommendations = []
        
        for practice_id, practice in self._practices.items():
            relevance_score = self._calculate_practice_relevance(
                practice,
                context,
                objectives,
                constraints or []
            )
            
            if relevance_score > 0.5:
                recommendation = {
                    "practice_id": practice_id,
                    "title": practice.title,
                    "category": practice.category.value,
                    "quality": practice.quality.value,
                    "quality_score": practice.quality_score,
                    "relevance_score": relevance_score,
                    "applicability": practice.applicability,
                    "impact": practice.impact,
                    "reasons": [],
                    "warnings": []
                }
                
                if practice.quality in [PracticeQuality.EXCELLENT, PracticeQuality.GOOD]:
                    recommendation["reasons"].append("高质量实践")
                
                if practice.verified:
                    recommendation["reasons"].append("已验证实践")
                
                if practice.evidence_count > 5:
                    recommendation["reasons"].append(f"有{practice.evidence_count}次证据支持")
                
                if practice.verification_count < 3:
                    recommendation["warnings"].append("验证次数较少")
                
                if constraints:
                    for constraint in constraints:
                        if self._practice_violates_constraint(practice, constraint):
                            recommendation["warnings"].append(f"可能与约束冲突: {constraint}")
                
                recommendations.append(recommendation)
        
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return recommendations[:limit]
    
    def extract_performance_practice(
        self,
        pattern: RecognizedPattern,
        performance_analysis: Optional[Dict[str, Any]] = None
    ) -> Optional[ExtractedPractice]:
        """提取性能最佳实践
        
        Args:
            pattern: 成功或优化模式
            performance_analysis: 性能分析结果
        
        Returns:
            提取的最佳实践
        """
        if pattern.pattern_type not in [PatternType.SUCCESS, PatternType.OPTIMIZATION]:
            return None
        
        rules = self._extraction_rules['performance']
        
        if not self._meets_extraction_criteria(pattern, rules):
            return None
        
        practice_id = self._generate_practice_id(pattern, PracticeCategory.PERFORMANCE)
        
        if practice_id in self._practices:
            return self._update_existing_practice(practice_id, pattern)
        
        quality_score = self._evaluate_performance_quality(pattern, performance_analysis)
        quality = self._determine_quality_level(quality_score)
        
        implementation_steps = self._extract_performance_implementation_steps(
            pattern, performance_analysis
        )
        benefits = self._extract_performance_benefits(pattern, performance_analysis)
        risks = self._identify_performance_risks(pattern, performance_analysis)
        
        practice = ExtractedPractice(
            practice_id=practice_id,
            category=PracticeCategory.PERFORMANCE,
            title=self._generate_practice_title(pattern, PracticeCategory.PERFORMANCE),
            description=self._generate_practice_description(pattern, PracticeCategory.PERFORMANCE),
            quality=quality,
            quality_score=quality_score,
            applicability=self._calculate_applicability(pattern),
            impact=self._calculate_impact(pattern),
            evidence_count=pattern.occurrences,
            source_patterns=[pattern.pattern_id],
            context_requirements=self._extract_context_requirements(pattern),
            implementation_steps=implementation_steps,
            benefits=benefits,
            risks=risks,
            examples=pattern.examples[:3],
            metrics=self._extract_metrics(pattern),
            tags=self._extract_practice_tags(pattern, PracticeCategory.PERFORMANCE)
        )
        
        self._practices[practice_id] = practice
        self._index_practice(practice)
        
        if self._storage_path:
            self._save_practices()
        
        self._logger.info(f"提取性能最佳实践: {practice.title} (质量: {quality.value})")
        return practice
    
    def extract_security_practice(
        self,
        pattern: RecognizedPattern,
        security_analysis: Optional[Dict[str, Any]] = None
    ) -> Optional[ExtractedPractice]:
        """提取安全最佳实践
        
        Args:
            pattern: 成功模式
            security_analysis: 安全分析结果
        
        Returns:
            提取的最佳实践
        """
        if pattern.pattern_type != PatternType.SUCCESS:
            return None
        
        rules = self._extraction_rules['security']
        
        if not self._meets_extraction_criteria(pattern, rules):
            return None
        
        practice_id = self._generate_practice_id(pattern, PracticeCategory.SECURITY)
        
        if practice_id in self._practices:
            return self._update_existing_practice(practice_id, pattern)
        
        quality_score = self._evaluate_security_quality(pattern, security_analysis)
        quality = self._determine_quality_level(quality_score)
        
        implementation_steps = self._extract_security_implementation_steps(
            pattern, security_analysis
        )
        benefits = self._extract_security_benefits(pattern, security_analysis)
        risks = self._identify_security_risks(pattern, security_analysis)
        
        practice = ExtractedPractice(
            practice_id=practice_id,
            category=PracticeCategory.SECURITY,
            title=self._generate_practice_title(pattern, PracticeCategory.SECURITY),
            description=self._generate_practice_description(pattern, PracticeCategory.SECURITY),
            quality=quality,
            quality_score=quality_score,
            applicability=self._calculate_applicability(pattern),
            impact=self._calculate_impact(pattern),
            evidence_count=pattern.occurrences,
            source_patterns=[pattern.pattern_id],
            context_requirements=self._extract_context_requirements(pattern),
            implementation_steps=implementation_steps,
            benefits=benefits,
            risks=risks,
            examples=pattern.examples[:3],
            metrics=self._extract_metrics(pattern),
            tags=self._extract_practice_tags(pattern, PracticeCategory.SECURITY)
        )
        
        self._practices[practice_id] = practice
        self._index_practice(practice)
        
        if self._storage_path:
            self._save_practices()
        
        self._logger.info(f"提取安全最佳实践: {practice.title} (质量: {quality.value})")
        return practice
    
    def _calculate_tag_similarity(self, tags1: List[str], tags2: List[str]) -> float:
        """计算标签相似度"""
        if not tags1 or not tags2:
            return 0.0
        
        set1 = set(tags1)
        set2 = set(tags2)
        
        intersection = set1 & set2
        union = set1 | set2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_context_overlap(
        self,
        context1: List[str],
        context2: List[str]
    ) -> float:
        """计算上下文重叠度"""
        if not context1 or not context2:
            return 0.0
        
        set1 = set(c.lower() for c in context1)
        set2 = set(c.lower() for c in context2)
        
        intersection = set1 & set2
        
        return len(intersection) / max(len(set1), len(set2))
    
    def _calculate_list_similarity(
        self,
        list1: List[str],
        list2: List[str]
    ) -> float:
        """计算列表相似度"""
        if not list1 or not list2:
            return 0.0
        
        set1 = set(item.lower() for item in list1)
        set2 = set(item.lower() for item in list2)
        
        intersection = set1 & set2
        union = set1 | set2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _are_complementary(
        self,
        practice1: ExtractedPractice,
        practice2: ExtractedPractice
    ) -> bool:
        """判断两个实践是否互补"""
        benefits1 = set(b.lower() for b in practice1.benefits)
        benefits2 = set(b.lower() for b in practice2.benefits)
        
        if not benefits1 or not benefits2:
            return False
        
        if benefits1.isdisjoint(benefits2):
            return True
        
        return False
    
    def _are_conflicting(
        self,
        practice1: ExtractedPractice,
        practice2: ExtractedPractice
    ) -> bool:
        """判断两个实践是否冲突"""
        risks1 = set(r.lower() for r in practice1.risks)
        benefits2 = set(b.lower() for b in practice2.benefits)
        
        for risk in risks1:
            for benefit in benefits2:
                if risk in benefit or benefit in risk:
                    return True
        
        return False
    
    def _calculate_practice_relevance(
        self,
        practice: ExtractedPractice,
        context: Dict[str, Any],
        objectives: List[str],
        constraints: List[str]
    ) -> float:
        """计算实践相关性"""
        score = 0.0
        
        context_tags = set(context.get('tags', []))
        practice_tags = set(practice.tags)
        if context_tags and practice_tags:
            tag_match = len(context_tags & practice_tags) / len(practice_tags)
            score += tag_match * 0.25
        
        objective_keywords = set(' '.join(objectives).lower().split())
        benefit_keywords = set(' '.join(practice.benefits).lower().split())
        if objective_keywords and benefit_keywords:
            objective_match = len(objective_keywords & benefit_keywords) / len(benefit_keywords)
            score += objective_match * 0.3
        
        score += practice.quality_score * 0.2
        score += practice.applicability * 0.15
        score += practice.impact * 0.1
        
        if constraints:
            violations = sum(
                1 for c in constraints
                if self._practice_violates_constraint(practice, c)
            )
            score -= violations * 0.1
        
        return max(0.0, min(1.0, score))
    
    def _practice_violates_constraint(
        self,
        practice: ExtractedPractice,
        constraint: str
    ) -> bool:
        """判断实践是否违反约束"""
        constraint_lower = constraint.lower()
        
        if 'not' in constraint_lower or 'avoid' in constraint_lower:
            keywords = constraint_lower.replace('not', '').replace('avoid', '').strip()
            if keywords in ' '.join(practice.tags).lower():
                return True
            if keywords in ' '.join(practice.benefits).lower():
                return True
        
        return False
    
    def _evaluate_performance_quality(
        self,
        pattern: RecognizedPattern,
        performance_analysis: Optional[Dict[str, Any]]
    ) -> float:
        """评估性能质量"""
        score = pattern.confidence_score * 0.4
        
        score += min(pattern.occurrences / 8.0, 1.0) * 0.2
        
        if performance_analysis:
            if 'improvement_rate' in performance_analysis:
                score += min(performance_analysis['improvement_rate'], 1.0) * 0.2
            
            if 'benchmark_score' in performance_analysis:
                score += min(performance_analysis['benchmark_score'], 1.0) * 0.2
        else:
            score += 0.2
        
        return min(score, 1.0)
    
    def _evaluate_security_quality(
        self,
        pattern: RecognizedPattern,
        security_analysis: Optional[Dict[str, Any]]
    ) -> float:
        """评估安全质量"""
        score = pattern.confidence_score * 0.5
        
        score += min(pattern.occurrences / 5.0, 1.0) * 0.2
        
        if security_analysis:
            if 'vulnerability_score' in security_analysis:
                score += (1.0 - security_analysis['vulnerability_score']) * 0.15
            
            if 'compliance_score' in security_analysis:
                score += security_analysis['compliance_score'] * 0.15
        else:
            score += 0.15
        
        return min(score, 1.0)
    
    def _extract_performance_implementation_steps(
        self,
        pattern: RecognizedPattern,
        performance_analysis: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """提取性能实施步骤"""
        steps = []
        
        steps.append({
            "step": 1,
            "action": "性能基准测试",
            "details": "建立当前性能基准"
        })
        
        steps.append({
            "step": 2,
            "action": "识别性能瓶颈",
            "details": "分析性能瓶颈和优化机会"
        })
        
        steps.append({
            "step": 3,
            "action": "实施优化",
            "details": "应用性能优化实践"
        })
        
        steps.append({
            "step": 4,
            "action": "性能验证",
            "details": "验证性能改进效果"
        })
        
        steps.append({
            "step": 5,
            "action": "持续监控",
            "details": "建立性能监控机制"
        })
        
        return steps
    
    def _extract_security_implementation_steps(
        self,
        pattern: RecognizedPattern,
        security_analysis: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """提取安全实施步骤"""
        steps = []
        
        steps.append({
            "step": 1,
            "action": "安全评估",
            "details": "评估当前安全状态"
        })
        
        steps.append({
            "step": 2,
            "action": "威胁建模",
            "details": "识别潜在安全威胁"
        })
        
        steps.append({
            "step": 3,
            "action": "实施安全措施",
            "details": "应用安全最佳实践"
        })
        
        steps.append({
            "step": 4,
            "action": "安全测试",
            "details": "进行安全测试和验证"
        })
        
        steps.append({
            "step": 5,
            "action": "持续审计",
            "details": "建立安全审计机制"
        })
        
        return steps
    
    def _extract_performance_benefits(
        self,
        pattern: RecognizedPattern,
        performance_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """提取性能收益"""
        benefits = []
        
        if performance_analysis:
            if performance_analysis.get('improvement_rate', 0) > 0.2:
                benefits.append("显著性能提升")
            
            if performance_analysis.get('latency_reduction', 0) > 0.3:
                benefits.append("延迟大幅降低")
            
            if performance_analysis.get('throughput_increase', 0) > 0.3:
                benefits.append("吞吐量显著提升")
        
        if not benefits:
            benefits.append("优化系统性能")
        
        return benefits
    
    def _extract_security_benefits(
        self,
        pattern: RecognizedPattern,
        security_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """提取安全收益"""
        benefits = []
        
        if security_analysis:
            if security_analysis.get('vulnerability_reduction', 0) > 0.5:
                benefits.append("显著降低安全风险")
            
            if security_analysis.get('compliance_achieved', False):
                benefits.append("满足合规要求")
        
        if not benefits:
            benefits.append("增强系统安全性")
        
        return benefits
    
    def _identify_performance_risks(
        self,
        pattern: RecognizedPattern,
        performance_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """识别性能风险"""
        risks = []
        
        if pattern.occurrences < 3:
            risks.append("验证次数较少")
        
        if performance_analysis:
            if performance_analysis.get('complexity_increase', 0) > 0.3:
                risks.append("可能增加系统复杂度")
        
        if not risks:
            risks.append("需要在测试环境验证")
        
        return risks
    
    def _identify_security_risks(
        self,
        pattern: RecognizedPattern,
        security_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """识别安全风险"""
        risks = []
        
        if pattern.occurrences < 2:
            risks.append("应用案例较少")
        
        if security_analysis:
            if security_analysis.get('remaining_vulnerabilities', 0) > 0:
                risks.append("仍存在潜在漏洞")
        
        if not risks:
            risks.append("需要持续安全监控")
        
        return risks
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_practices": len(self._practices),
            "by_category": {},
            "by_quality": {},
            "avg_quality_score": 0.0,
            "avg_evidence_count": 0.0,
            "verified_count": 0
        }
        
        for category in PracticeCategory:
            count = len(self._category_index.get(category.value, set()))
            stats["by_category"][category.value] = count
        
        for quality in PracticeQuality:
            count = len(self._quality_index.get(quality.value, set()))
            stats["by_quality"][quality.value] = count
        
        if self._practices:
            stats["avg_quality_score"] = sum(
                p.quality_score for p in self._practices.values()
            ) / len(self._practices)
            
            stats["avg_evidence_count"] = sum(
                p.evidence_count for p in self._practices.values()
            ) / len(self._practices)
            
            stats["verified_count"] = sum(
                1 for p in self._practices.values() if p.verified
            )
        
        return stats
    
    def recognize_code_patterns(
        self,
        code_content: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """识别代码模式
        
        Args:
            code_content: 代码内容
            language: 编程语言
            context: 上下文信息
        
        Returns:
            识别出的代码模式
        """
        patterns = {
            "design_patterns": self._recognize_design_patterns(code_content, language),
            "code_structures": self._recognize_code_structures(code_content, language),
            "naming_conventions": self._recognize_naming_conventions(code_content, language),
            "code_quality_indicators": self._analyze_code_quality_indicators(code_content, language),
            "anti_patterns": self._detect_anti_patterns(code_content, language)
        }
        
        patterns["overall_score"] = self._calculate_overall_pattern_score(patterns)
        patterns["recommendations"] = self._generate_pattern_recommendations(patterns)
        
        return patterns
    
    def _recognize_design_patterns(
        self,
        code_content: str,
        language: str
    ) -> List[Dict[str, Any]]:
        """识别设计模式"""
        design_patterns = []
        
        patterns_to_check = {
            "singleton": self._check_singleton_pattern,
            "factory": self._check_factory_pattern,
            "observer": self._check_observer_pattern,
            "strategy": self._check_strategy_pattern,
            "decorator": self._check_decorator_pattern,
            "adapter": self._check_adapter_pattern,
            "facade": self._check_facade_pattern,
            "builder": self._check_builder_pattern,
            "prototype": self._check_prototype_pattern,
            "command": self._check_command_pattern
        }
        
        for pattern_name, checker in patterns_to_check.items():
            result = checker(code_content, language)
            if result["detected"]:
                design_patterns.append({
                    "pattern_name": pattern_name,
                    "confidence": result["confidence"],
                    "locations": result.get("locations", []),
                    "quality": result.get("quality", "good"),
                    "description": self._get_pattern_description(pattern_name)
                })
        
        return design_patterns
    
    def _check_singleton_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """检查单例模式"""
        result = {"detected": False, "confidence": 0.0, "locations": [], "quality": "unknown"}
        
        if language == "python":
            if re.search(r'__new__\s*\(', code) and re.search(r'_instance\s*=', code):
                result["detected"] = True
                result["confidence"] = 0.85
                result["locations"] = re.findall(r'class\s+(\w+).*?__new__', code, re.DOTALL)
            elif re.search(r'@staticmethod', code) and re.search(r'get_instance\s*\(', code):
                result["detected"] = True
                result["confidence"] = 0.75
                result["locations"] = re.findall(r'class\s+(\w+)', code)
        
        if result["detected"]:
            if re.search(r'thread', code, re.IGNORECASE):
                result["quality"] = "excellent"
            else:
                result["quality"] = "good"
        
        return result
    
    def _check_factory_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """检查工厂模式"""
        result = {"detected": False, "confidence": 0.0, "locations": [], "quality": "unknown"}
        
        factory_keywords = ['factory', 'create', 'build', 'make']
        has_factory_class = any(kw in code.lower() for kw in factory_keywords)
        
        if language == "python":
            if has_factory_class and re.search(r'def\s+(create|build|make)\w*\s*\(', code):
                result["detected"] = True
                result["confidence"] = 0.8
                result["locations"] = re.findall(r'def\s+(create\w+|build\w+|make\w+)', code)
                
                if re.search(r'if\s+.*:\s*return', code) and re.search(r'elif\s+.*:\s*return', code):
                    result["quality"] = "good"
                else:
                    result["quality"] = "acceptable"
        
        return result
    
    def _check_observer_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """检查观察者模式"""
        result = {"detected": False, "confidence": 0.0, "locations": [], "quality": "unknown"}
        
        observer_keywords = ['observer', 'subscribe', 'notify', 'listener', 'emit']
        has_observer = sum(1 for kw in observer_keywords if kw in code.lower()) >= 2
        
        if has_observer:
            result["detected"] = True
            result["confidence"] = 0.75
            
            if re.search(r'(add|attach|subscribe)\w*\s*\(', code):
                if re.search(r'(remove|detach|unsubscribe)\w*\s*\(', code):
                    result["quality"] = "excellent"
                else:
                    result["quality"] = "good"
            else:
                result["quality"] = "acceptable"
            
            result["locations"] = re.findall(r'def\s+(notify|emit|subscribe)\w*', code)
        
        return result
    
    def _check_strategy_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """检查策略模式"""
        result = {"detected": False, "confidence": 0.0, "locations": [], "quality": "unknown"}
        
        if 'strategy' in code.lower() or 'algorithm' in code.lower():
            if re.search(r'def\s+execute\s*\(', code) or re.search(r'def\s+apply\s*\(', code):
                result["detected"] = True
                result["confidence"] = 0.7
                result["locations"] = re.findall(r'class\s+(\w*Strategy\w*|\w*Algorithm\w*)', code)
                
                if re.search(r'abstract', code, re.IGNORECASE) or re.search(r'ABC', code):
                    result["quality"] = "excellent"
                else:
                    result["quality"] = "good"
        
        return result
    
    def _check_decorator_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """检查装饰器模式"""
        result = {"detected": False, "confidence": 0.0, "locations": [], "quality": "unknown"}
        
        if language == "python":
            decorator_pattern = r'@(\w+)'
            decorators = re.findall(decorator_pattern, code)
            
            if len(decorators) > 0:
                result["detected"] = True
                result["confidence"] = min(0.6 + len(decorators) * 0.1, 0.95)
                result["locations"] = decorators
                
                custom_decorators = [d for d in decorators if not d.startswith('_') and d not in 
                                    ['staticmethod', 'classmethod', 'property']]
                if custom_decorators:
                    result["quality"] = "excellent"
                else:
                    result["quality"] = "good"
        
        return result
    
    def _check_adapter_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """检查适配器模式"""
        result = {"detected": False, "confidence": 0.0, "locations": [], "quality": "unknown"}
        
        if 'adapter' in code.lower():
            if re.search(r'class\s+\w*Adapter\w*', code):
                result["detected"] = True
                result["confidence"] = 0.8
                result["locations"] = re.findall(r'class\s+(\w*Adapter\w*)', code)
                result["quality"] = "good"
        
        return result
    
    def _check_facade_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """检查外观模式"""
        result = {"detected": False, "confidence": 0.0, "locations": [], "quality": "unknown"}
        
        if 'facade' in code.lower():
            if re.search(r'class\s+\w*Facade\w*', code):
                result["detected"] = True
                result["confidence"] = 0.75
                result["locations"] = re.findall(r'class\s+(\w*Facade\w*)', code)
                result["quality"] = "good"
        
        return result
    
    def _check_builder_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """检查建造者模式"""
        result = {"detected": False, "confidence": 0.0, "locations": [], "quality": "unknown"}
        
        if 'builder' in code.lower():
            has_build_method = re.search(r'def\s+build\s*\(', code)
            has_fluent_interface = re.search(r'return\s+self', code)
            
            if has_build_method or has_fluent_interface:
                result["detected"] = True
                result["confidence"] = 0.75
                result["locations"] = re.findall(r'class\s+(\w*Builder\w*)', code)
                
                if has_fluent_interface:
                    result["quality"] = "excellent"
                else:
                    result["quality"] = "good"
        
        return result
    
    def _check_prototype_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """检查原型模式"""
        result = {"detected": False, "confidence": 0.0, "locations": [], "quality": "unknown"}
        
        if language == "python":
            if re.search(r'def\s+clone\s*\(', code) or re.search(r'__copy__\s*\(', code):
                result["detected"] = True
                result["confidence"] = 0.8
                result["locations"] = re.findall(r'class\s+(\w+)', code)
                result["quality"] = "good"
        
        return result
    
    def _check_command_pattern(self, code: str, language: str) -> Dict[str, Any]:
        """检查命令模式"""
        result = {"detected": False, "confidence": 0.0, "locations": [], "quality": "unknown"}
        
        command_keywords = ['command', 'execute', 'undo', 'redo']
        has_command = sum(1 for kw in command_keywords if kw in code.lower()) >= 2
        
        if has_command:
            if re.search(r'def\s+execute\s*\(', code):
                result["detected"] = True
                result["confidence"] = 0.7
                result["locations"] = re.findall(r'class\s+(\w*Command\w*)', code)
                
                if re.search(r'def\s+undo\s*\(', code):
                    result["quality"] = "excellent"
                else:
                    result["quality"] = "good"
        
        return result
    
    def _get_pattern_description(self, pattern_name: str) -> str:
        """获取模式描述"""
        descriptions = {
            "singleton": "确保一个类只有一个实例，并提供一个全局访问点",
            "factory": "定义一个创建对象的接口，让子类决定实例化哪一个类",
            "observer": "定义对象间的一对多依赖关系，当一个对象状态改变时，所有依赖它的对象都会收到通知",
            "strategy": "定义一系列算法，把它们一个个封装起来，并且使它们可相互替换",
            "decorator": "动态地给一个对象添加一些额外的职责",
            "adapter": "将一个类的接口转换成客户希望的另一个接口",
            "facade": "为子系统中的一组接口提供一个一致的界面",
            "builder": "将一个复杂对象的构建与它的表示分离，使得同样的构建过程可以创建不同的表示",
            "prototype": "用原型实例指定创建对象的种类，并且通过拷贝这些原型创建新的对象",
            "command": "将一个请求封装为一个对象，从而使你可用不同的请求对客户进行参数化"
        }
        return descriptions.get(pattern_name, "设计模式")
    
    def _recognize_code_structures(
        self,
        code_content: str,
        language: str
    ) -> Dict[str, Any]:
        """识别代码结构"""
        structures = {
            "classes": self._extract_class_structures(code_content, language),
            "functions": self._extract_function_structures(code_content, language),
            "modules": self._extract_module_structures(code_content, language),
            "inheritance": self._analyze_inheritance(code_content, language),
            "composition": self._analyze_composition(code_content, language)
        }
        
        return structures
    
    def _extract_class_structures(self, code: str, language: str) -> List[Dict[str, Any]]:
        """提取类结构"""
        classes = []
        
        if language == "python":
            class_pattern = r'class\s+(\w+)(?:\(([^)]*)\))?:'
            for match in re.finditer(class_pattern, code):
                class_name = match.group(1)
                parent_classes = match.group(2).split(',') if match.group(2) else []
                parent_classes = [p.strip() for p in parent_classes if p.strip()]
                
                classes.append({
                    "name": class_name,
                    "parent_classes": parent_classes,
                    "has_inheritance": len(parent_classes) > 0,
                    "line_number": code[:match.start()].count('\n') + 1
                })
        
        return classes
    
    def _extract_function_structures(self, code: str, language: str) -> List[Dict[str, Any]]:
        """提取函数结构"""
        functions = []
        
        if language == "python":
            func_pattern = r'def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:'
            for match in re.finditer(func_pattern, code):
                func_name = match.group(1)
                params = match.group(2).split(',') if match.group(2) else []
                params = [p.strip() for p in params if p.strip()]
                return_type = match.group(3).strip() if match.group(3) else None
                
                functions.append({
                    "name": func_name,
                    "parameters": params,
                    "param_count": len(params),
                    "has_return_type": return_type is not None,
                    "return_type": return_type,
                    "line_number": code[:match.start()].count('\n') + 1
                })
        
        return functions
    
    def _extract_module_structures(self, code: str, language: str) -> Dict[str, Any]:
        """提取模块结构"""
        modules = {
            "imports": [],
            "from_imports": [],
            "total_imports": 0
        }
        
        if language == "python":
            import_pattern = r'^import\s+(.+)$'
            from_import_pattern = r'^from\s+(\S+)\s+import\s+(.+)$'
            
            for match in re.finditer(import_pattern, code, re.MULTILINE):
                modules["imports"].append(match.group(1).strip())
            
            for match in re.finditer(from_import_pattern, code, re.MULTILINE):
                modules["from_imports"].append({
                    "module": match.group(1),
                    "items": match.group(2).strip()
                })
            
            modules["total_imports"] = len(modules["imports"]) + len(modules["from_imports"])
        
        return modules
    
    def _analyze_inheritance(self, code: str, language: str) -> Dict[str, Any]:
        """分析继承关系"""
        inheritance = {
            "depth": 0,
            "hierarchy": [],
            "multiple_inheritance": False
        }
        
        if language == "python":
            class_pattern = r'class\s+(\w+)(?:\(([^)]*)\))?:'
            hierarchy = {}
            
            for match in re.finditer(class_pattern, code):
                class_name = match.group(1)
                parents = match.group(2).split(',') if match.group(2) else []
                parents = [p.strip() for p in parents if p.strip()]
                
                hierarchy[class_name] = parents
                
                if len(parents) > 1:
                    inheritance["multiple_inheritance"] = True
            
            inheritance["hierarchy"] = hierarchy
            inheritance["depth"] = self._calculate_inheritance_depth(hierarchy)
        
        return inheritance
    
    def _calculate_inheritance_depth(self, hierarchy: Dict[str, List[str]]) -> int:
        """计算继承深度"""
        def get_depth(class_name: str, visited: set) -> int:
            if class_name in visited:
                return 0
            visited.add(class_name)
            
            parents = hierarchy.get(class_name, [])
            if not parents:
                return 0
            
            return 1 + max(get_depth(p, visited) for p in parents)
        
        max_depth = 0
        for class_name in hierarchy:
            depth = get_depth(class_name, set())
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _analyze_composition(self, code: str, language: str) -> Dict[str, Any]:
        """分析组合关系"""
        composition = {
            "has_composition": False,
            "composition_instances": []
        }
        
        if language == "python":
            self_attr_pattern = r'self\.(\w+)\s*=\s*(\w+)\('
            
            for match in re.finditer(self_attr_pattern, code):
                attr_name = match.group(1)
                class_name = match.group(2)
                
                composition["composition_instances"].append({
                    "attribute": attr_name,
                    "class": class_name
                })
                composition["has_composition"] = True
        
        return composition
    
    def _recognize_naming_conventions(
        self,
        code_content: str,
        language: str
    ) -> Dict[str, Any]:
        """识别命名规范"""
        conventions = {
            "class_naming": self._check_class_naming(code_content, language),
            "function_naming": self._check_function_naming(code_content, language),
            "variable_naming": self._check_variable_naming(code_content, language),
            "constant_naming": self._check_constant_naming(code_content, language),
            "overall_compliance": 0.0
        }
        
        scores = [
            conventions["class_naming"]["compliance"],
            conventions["function_naming"]["compliance"],
            conventions["variable_naming"]["compliance"],
            conventions["constant_naming"]["compliance"]
        ]
        conventions["overall_compliance"] = sum(scores) / len(scores)
        
        return conventions
    
    def _check_class_naming(self, code: str, language: str) -> Dict[str, Any]:
        """检查类命名规范"""
        result = {
            "convention": "PascalCase",
            "compliance": 0.0,
            "violations": []
        }
        
        if language == "python":
            class_names = re.findall(r'class\s+(\w+)', code)
            
            if class_names:
                compliant = 0
                for name in class_names:
                    if name[0].isupper() and '_' not in name:
                        compliant += 1
                    else:
                        result["violations"].append(name)
                
                result["compliance"] = compliant / len(class_names)
        
        return result
    
    def _check_function_naming(self, code: str, language: str) -> Dict[str, Any]:
        """检查函数命名规范"""
        result = {
            "convention": "snake_case",
            "compliance": 0.0,
            "violations": []
        }
        
        if language == "python":
            func_names = re.findall(r'def\s+(\w+)', code)
            
            if func_names:
                compliant = 0
                for name in func_names:
                    if name.islower() or (name.islower() or '_' in name):
                        if not name[0].isupper():
                            compliant += 1
                        else:
                            result["violations"].append(name)
                    else:
                        compliant += 1
                
                result["compliance"] = compliant / len(func_names)
        
        return result
    
    def _check_variable_naming(self, code: str, language: str) -> Dict[str, Any]:
        """检查变量命名规范"""
        result = {
            "convention": "snake_case",
            "compliance": 0.0,
            "violations": []
        }
        
        if language == "python":
            var_pattern = r'(\w+)\s*=\s*[^=]'
            var_names = re.findall(var_pattern, code)
            
            var_names = [v for v in var_names if not v.startswith('__') and v not in 
                        ['self', 'cls', 'True', 'False', 'None']]
            
            if var_names:
                compliant = 0
                for name in var_names:
                    if name.islower() or '_' in name:
                        if not name[0].isupper():
                            compliant += 1
                        else:
                            result["violations"].append(name)
                    else:
                        compliant += 1
                
                result["compliance"] = compliant / len(var_names)
        
        return result
    
    def _check_constant_naming(self, code: str, language: str) -> Dict[str, Any]:
        """检查常量命名规范"""
        result = {
            "convention": "UPPER_CASE",
            "compliance": 0.0,
            "violations": []
        }
        
        if language == "python":
            const_pattern = r'^([A-Z_][A-Z0-9_]*)\s*=\s*[^=]'
            const_names = re.findall(const_pattern, code, re.MULTILINE)
            
            if const_names:
                compliant = 0
                for name in const_names:
                    if name.isupper() and '_' in name:
                        compliant += 1
                    else:
                        result["violations"].append(name)
                
                result["compliance"] = compliant / len(const_names)
            else:
                result["compliance"] = 1.0
        
        return result
    
    def _analyze_code_quality_indicators(
        self,
        code_content: str,
        language: str
    ) -> Dict[str, Any]:
        """分析代码质量指标"""
        indicators = {
            "documentation": self._check_documentation(code_content, language),
            "complexity": self._estimate_complexity(code_content, language),
            "test_coverage_hints": self._check_test_hints(code_content, language),
            "error_handling": self._check_error_handling(code_content, language)
        }
        
        return indicators
    
    def _check_documentation(self, code: str, language: str) -> Dict[str, Any]:
        """检查文档"""
        result = {
            "has_docstrings": False,
            "docstring_coverage": 0.0,
            "has_comments": False,
            "comment_ratio": 0.0
        }
        
        if language == "python":
            docstrings = re.findall(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', code)
            result["has_docstrings"] = len(docstrings) > 0
            
            functions = re.findall(r'def\s+\w+', code)
            if functions:
                result["docstring_coverage"] = len(docstrings) / len(functions)
            
            comments = re.findall(r'#.*$', code, re.MULTILINE)
            result["has_comments"] = len(comments) > 0
            
            total_lines = len(code.split('\n'))
            if total_lines > 0:
                result["comment_ratio"] = len(comments) / total_lines
        
        return result
    
    def _estimate_complexity(self, code: str, language: str) -> Dict[str, Any]:
        """估算复杂度"""
        result = {
            "cyclomatic_complexity": 0,
            "nesting_depth": 0,
            "lines_of_code": 0
        }
        
        lines = code.split('\n')
        result["lines_of_code"] = len([l for l in lines if l.strip()])
        
        if language == "python":
            decision_points = ['if', 'elif', 'for', 'while', 'and', 'or', 'except']
            complexity = 1
            
            for line in lines:
                for point in decision_points:
                    if point in line:
                        complexity += 1
            
            result["cyclomatic_complexity"] = complexity
            
            max_indent = 0
            for line in lines:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    max_indent = max(max_indent, indent // 4)
            
            result["nesting_depth"] = max_indent
        
        return result
    
    def _check_test_hints(self, code: str, language: str) -> Dict[str, Any]:
        """检查测试提示"""
        result = {
            "has_tests": False,
            "test_framework": None,
            "test_count": 0
        }
        
        test_indicators = {
            "unittest": ["import unittest", "class.*Test.*unittest"],
            "pytest": ["import pytest", "@pytest", "def test_"],
            "nose": ["import nose", "@nose"]
        }
        
        for framework, indicators in test_indicators.items():
            for indicator in indicators:
                if re.search(indicator, code):
                    result["has_tests"] = True
                    result["test_framework"] = framework
                    break
            
            if result["has_tests"]:
                break
        
        if result["has_tests"]:
            result["test_count"] = len(re.findall(r'def\s+test_\w+', code))
        
        return result
    
    def _check_error_handling(self, code: str, language: str) -> Dict[str, Any]:
        """检查错误处理"""
        result = {
            "has_try_catch": False,
            "exception_count": 0,
            "has_logging": False
        }
        
        if language == "python":
            result["has_try_catch"] = 'try:' in code
            result["exception_count"] = len(re.findall(r'except\s+\w+', code))
            result["has_logging"] = 'import logging' in code or 'logger' in code
        
        return result
    
    def _detect_anti_patterns(
        self,
        code_content: str,
        language: str
    ) -> List[Dict[str, Any]]:
        """检测反模式"""
        anti_patterns = []
        
        anti_pattern_checks = [
            {
                "name": "God Class",
                "check": lambda c: len(re.findall(r'def\s+\w+', c)) > 20,
                "description": "类中方法过多，违反单一职责原则"
            },
            {
                "name": "Long Method",
                "check": lambda c: any(len(m.split('\n')) > 50 for m in re.findall(r'def\s+\w+[\s\S]*?(?=\ndef\s|\nclass\s|\Z)', c)),
                "description": "方法过长，难以理解和维护"
            },
            {
                "name": "Magic Numbers",
                "check": lambda c: bool(re.search(r'(?<!["\'])\b\d{2,}\b(?!["\'])', c)),
                "description": "代码中存在魔法数字，应使用常量"
            },
            {
                "name": "Deep Nesting",
                "check": lambda c: max(len(line) - len(line.lstrip()) for line in c.split('\n') if line.strip()) > 16,
                "description": "嵌套层级过深，应重构提取方法"
            },
            {
                "name": "Duplicate Code",
                "check": lambda c: len(set(re.findall(r'^\s{4,}.+$', c, re.MULTILINE))) < len(re.findall(r'^\s{4,}.+$', c, re.MULTILINE)) * 0.8,
                "description": "存在重复代码，应提取公共方法"
            }
        ]
        
        for ap in anti_pattern_checks:
            try:
                if ap["check"](code_content):
                    anti_patterns.append({
                        "name": ap["name"],
                        "description": ap["description"],
                        "severity": "medium"
                    })
            except:
                pass
        
        return anti_patterns
    
    def _calculate_overall_pattern_score(self, patterns: Dict[str, Any]) -> float:
        """计算整体模式得分"""
        score = 0.0
        
        design_pattern_score = len(patterns["design_patterns"]) * 0.1
        score += min(design_pattern_score, 0.3)
        
        quality_indicators = patterns["code_quality_indicators"]
        if quality_indicators["documentation"]["docstring_coverage"] > 0.5:
            score += 0.2
        
        if quality_indicators["complexity"]["cyclomatic_complexity"] < 10:
            score += 0.2
        elif quality_indicators["complexity"]["cyclomatic_complexity"] < 20:
            score += 0.1
        
        naming_compliance = patterns["naming_conventions"]["overall_compliance"]
        score += naming_compliance * 0.2
        
        anti_pattern_penalty = len(patterns["anti_patterns"]) * 0.1
        score = max(0, score - anti_pattern_penalty)
        
        return min(score, 1.0)
    
    def _generate_pattern_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """生成模式建议"""
        recommendations = []
        
        if len(patterns["anti_patterns"]) > 0:
            for ap in patterns["anti_patterns"]:
                recommendations.append(f"避免{ap['name']}: {ap['description']}")
        
        quality_indicators = patterns["code_quality_indicators"]
        if quality_indicators["documentation"]["docstring_coverage"] < 0.5:
            recommendations.append("增加文档字符串覆盖率，提高代码可读性")
        
        if quality_indicators["complexity"]["cyclomatic_complexity"] > 15:
            recommendations.append("降低代码复杂度，考虑提取方法或重构")
        
        if quality_indicators["error_handling"]["exception_count"] == 0:
            recommendations.append("添加异常处理机制，提高代码健壮性")
        
        naming = patterns["naming_conventions"]
        if naming["overall_compliance"] < 0.8:
            recommendations.append("改进命名规范一致性，遵循语言最佳实践")
        
        if not recommendations:
            recommendations.append("代码质量良好，继续保持当前实践")
        
        return recommendations
    
    def generate_practice_document(
        self,
        practice_id: str,
        output_format: str = "markdown",
        include_examples: bool = True
    ) -> str:
        """生成最佳实践文档
        
        Args:
            practice_id: 实践ID
            output_format: 输出格式 (markdown, html, json)
            include_examples: 是否包含示例
        
        Returns:
            生成的文档内容
        """
        practice = self._practices.get(practice_id)
        if not practice:
            return ""
        
        if output_format == "markdown":
            return self._generate_markdown_document(practice, include_examples)
        elif output_format == "html":
            return self._generate_html_document(practice, include_examples)
        elif output_format == "json":
            return json.dumps(practice.to_dict(), indent=2, ensure_ascii=False)
        else:
            return ""
    
    def _generate_markdown_document(
        self,
        practice: ExtractedPractice,
        include_examples: bool
    ) -> str:
        """生成Markdown文档"""
        doc = f"# {practice.title}\n\n"
        
        doc += "## 基本信息\n\n"
        doc += f"- **类别**: {practice.category.value}\n"
        doc += f"- **质量等级**: {practice.quality.value}\n"
        doc += f"- **质量分数**: {practice.quality_score:.2f}\n"
        doc += f"- **适用性**: {practice.applicability:.2f}\n"
        doc += f"- **影响力**: {practice.impact:.2f}\n"
        doc += f"- **证据数量**: {practice.evidence_count}\n"
        doc += f"- **验证状态**: {'已验证' if practice.verified else '未验证'}\n"
        doc += f"- **创建时间**: {practice.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        doc += f"- **更新时间**: {practice.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        doc += "## 描述\n\n"
        doc += f"{practice.description}\n\n"
        
        if practice.context_requirements:
            doc += "## 上下文要求\n\n"
            for req in practice.context_requirements:
                doc += f"- {req}\n"
            doc += "\n"
        
        if practice.implementation_steps:
            doc += "## 实施步骤\n\n"
            for step in practice.implementation_steps:
                doc += f"{step['step']}. **{step['action']}**: {step['details']}\n"
            doc += "\n"
        
        if practice.benefits:
            doc += "## 收益\n\n"
            for benefit in practice.benefits:
                doc += f"- {benefit}\n"
            doc += "\n"
        
        if practice.risks:
            doc += "## 风险\n\n"
            for risk in practice.risks:
                doc += f"- {risk}\n"
            doc += "\n"
        
        if include_examples and practice.examples:
            doc += "## 示例\n\n"
            for i, example in enumerate(practice.examples[:3], 1):
                doc += f"### 示例 {i}\n\n"
                doc += f"```json\n{json.dumps(example, indent=2, ensure_ascii=False)}\n```\n\n"
        
        if practice.metrics:
            doc += "## 指标\n\n"
            doc += "| 指标 | 值 |\n"
            doc += "|------|----|\n"
            for key, value in practice.metrics.items():
                if isinstance(value, (int, float)):
                    doc += f"| {key} | {value:.2f} |\n"
                else:
                    doc += f"| {key} | {value} |\n"
            doc += "\n"
        
        if practice.tags:
            doc += "## 标签\n\n"
            doc += " ".join([f"`{tag}`" for tag in practice.tags])
            doc += "\n\n"
        
        return doc
    
    def _generate_html_document(
        self,
        practice: ExtractedPractice,
        include_examples: bool
    ) -> str:
        """生成HTML文档"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{practice.title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .info-box {{
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .quality-{practice.quality.value} {{
            border-left: 4px solid {self._get_quality_color(practice.quality)};
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .tag {{
            background-color: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            margin-right: 5px;
            display: inline-block;
        }}
    </style>
</head>
<body>
    <h1>{practice.title}</h1>
    
    <div class="info-box quality-{practice.quality.value}">
        <h2>基本信息</h2>
        <ul>
            <li><strong>类别:</strong> {practice.category.value}</li>
            <li><strong>质量等级:</strong> {practice.quality.value}</li>
            <li><strong>质量分数:</strong> {practice.quality_score:.2f}</li>
            <li><strong>适用性:</strong> {practice.applicability:.2f}</li>
            <li><strong>影响力:</strong> {practice.impact:.2f}</li>
            <li><strong>证据数量:</strong> {practice.evidence_count}</li>
            <li><strong>验证状态:</strong> {'已验证' if practice.verified else '未验证'}</li>
        </ul>
    </div>
    
    <h2>描述</h2>
    <p>{practice.description}</p>
"""
        
        if practice.context_requirements:
            html += """
    <h2>上下文要求</h2>
    <ul>
"""
            for req in practice.context_requirements:
                html += f"        <li>{req}</li>\n"
            html += "    </ul>\n"
        
        if practice.implementation_steps:
            html += """
    <h2>实施步骤</h2>
    <ol>
"""
            for step in practice.implementation_steps:
                html += f"        <li><strong>{step['action']}:</strong> {step['details']}</li>\n"
            html += "    </ol>\n"
        
        if practice.benefits:
            html += """
    <h2>收益</h2>
    <ul>
"""
            for benefit in practice.benefits:
                html += f"        <li>{benefit}</li>\n"
            html += "    </ul>\n"
        
        if practice.risks:
            html += """
    <h2>风险</h2>
    <ul>
"""
            for risk in practice.risks:
                html += f"        <li>{risk}</li>\n"
            html += "    </ul>\n"
        
        if include_examples and practice.examples:
            html += """
    <h2>示例</h2>
"""
            for i, example in enumerate(practice.examples[:3], 1):
                html += f"""
    <h3>示例 {i}</h3>
    <pre><code class="json">{json.dumps(example, indent=2, ensure_ascii=False)}</code></pre>
"""
        
        if practice.metrics:
            html += """
    <h2>指标</h2>
    <table>
        <tr>
            <th>指标</th>
            <th>值</th>
        </tr>
"""
            for key, value in practice.metrics.items():
                if isinstance(value, (int, float)):
                    html += f"        <tr><td>{key}</td><td>{value:.2f}</td></tr>\n"
                else:
                    html += f"        <tr><td>{key}</td><td>{value}</td></tr>\n"
            html += "    </table>\n"
        
        if practice.tags:
            html += """
    <h2>标签</h2>
    <div>
"""
            for tag in practice.tags:
                html += f"        <span class=\"tag\">{tag}</span>\n"
            html += "    </div>\n"
        
        html += """
</body>
</html>
"""
        
        return html
    
    def _get_quality_color(self, quality: PracticeQuality) -> str:
        """获取质量颜色"""
        colors = {
            PracticeQuality.EXCELLENT: "#28a745",
            PracticeQuality.GOOD: "#17a2b8",
            PracticeQuality.ACCEPTABLE: "#ffc107",
            PracticeQuality.POOR: "#fd7e14",
            PracticeQuality.CRITICAL: "#dc3545"
        }
        return colors.get(quality, "#6c757d")
    
    def analyze_pattern_applicability(
        self,
        pattern: RecognizedPattern,
        target_context: Dict[str, Any],
        constraints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """分析模式适用性
        
        Args:
            pattern: 识别出的模式
            target_context: 目标上下文
            constraints: 约束条件
        
        Returns:
            适用性分析结果
        """
        analysis = {
            "pattern_id": pattern.pattern_id,
            "pattern_name": pattern.name,
            "applicability_score": 0.0,
            "context_match": 0.0,
            "constraint_compliance": 0.0,
            "risks": [],
            "recommendations": [],
            "adaptation_needed": []
        }
        
        analysis["context_match"] = self._calculate_context_match(
            pattern.context,
            target_context
        )
        
        if constraints:
            analysis["constraint_compliance"] = self._check_constraint_compliance(
                pattern,
                constraints
            )
        else:
            analysis["constraint_compliance"] = 1.0
        
        analysis["applicability_score"] = (
            pattern.confidence_score * 0.3 +
            analysis["context_match"] * 0.4 +
            analysis["constraint_compliance"] * 0.3
        )
        
        analysis["risks"] = self._identify_applicability_risks(
            pattern,
            target_context,
            constraints
        )
        
        analysis["recommendations"] = self._generate_applicability_recommendations(
            pattern,
            target_context,
            analysis
        )
        
        analysis["adaptation_needed"] = self._identify_needed_adaptations(
            pattern,
            target_context
        )
        
        return analysis
    
    def _calculate_context_match(
        self,
        pattern_context: Dict[str, Any],
        target_context: Dict[str, Any]
    ) -> float:
        """计算上下文匹配度"""
        if not pattern_context or not target_context:
            return 0.5
        
        matches = 0
        total = 0
        
        for key, value in pattern_context.items():
            if key in target_context:
                total += 1
                if target_context[key] == value:
                    matches += 1
                elif isinstance(value, str) and isinstance(target_context[key], str):
                    similarity = self._calculate_string_similarity(value, target_context[key])
                    matches += similarity
        
        if total == 0:
            return 0.5
        
        return matches / total
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """计算字符串相似度"""
        str1_lower = str1.lower()
        str2_lower = str2.lower()
        
        if str1_lower == str2_lower:
            return 1.0
        
        words1 = set(str1_lower.split())
        words2 = set(str2_lower.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _check_constraint_compliance(
        self,
        pattern: RecognizedPattern,
        constraints: List[str]
    ) -> float:
        """检查约束合规性"""
        if not constraints:
            return 1.0
        
        violations = 0
        
        for constraint in constraints:
            if self._pattern_violates_constraint_pattern(pattern, constraint):
                violations += 1
        
        return max(0.0, 1.0 - violations / len(constraints))
    
    def _pattern_violates_constraint_pattern(
        self,
        pattern: RecognizedPattern,
        constraint: str
    ) -> bool:
        """判断模式是否违反约束"""
        constraint_lower = constraint.lower()
        
        if 'not' in constraint_lower or 'avoid' in constraint_lower:
            keywords = constraint_lower.replace('not', '').replace('avoid', '').strip()
            
            if keywords in pattern.name.lower():
                return True
            
            if keywords in pattern.description.lower():
                return True
            
            if any(keywords in tag.lower() for tag in pattern.tags):
                return True
        
        return False
    
    def _identify_applicability_risks(
        self,
        pattern: RecognizedPattern,
        target_context: Dict[str, Any],
        constraints: Optional[List[str]]
    ) -> List[str]:
        """识别适用性风险"""
        risks = []
        
        if pattern.occurrences < 3:
            risks.append("模式验证次数较少，稳定性有待观察")
        
        if pattern.confidence_score < 0.7:
            risks.append("模式置信度较低，应用时需谨慎")
        
        if target_context.get("scale", "medium") == "large" and "scalability" not in pattern.tags:
            risks.append("模式未在大规模场景验证，可能存在扩展性风险")
        
        if constraints:
            for constraint in constraints:
                if self._pattern_violates_constraint_pattern(pattern, constraint):
                    risks.append(f"模式可能与约束冲突: {constraint}")
        
        return risks
    
    def _generate_applicability_recommendations(
        self,
        pattern: RecognizedPattern,
        target_context: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> List[str]:
        """生成适用性建议"""
        recommendations = []
        
        if analysis["applicability_score"] > 0.8:
            recommendations.append("高度适用，建议直接应用")
        elif analysis["applicability_score"] > 0.6:
            recommendations.append("中等适用，建议进行适当调整后应用")
        else:
            recommendations.append("适用性较低，建议寻找替代方案或进行重大调整")
        
        if analysis["context_match"] < 0.5:
            recommendations.append("上下文匹配度较低，需要评估环境差异的影响")
        
        if analysis["constraint_compliance"] < 1.0:
            recommendations.append("存在约束冲突，需要优先解决约束问题")
        
        if pattern.occurrences < 5:
            recommendations.append("建议在小范围内试点验证后再全面推广")
        
        return recommendations
    
    def _identify_needed_adaptations(
        self,
        pattern: RecognizedPattern,
        target_context: Dict[str, Any]
    ) -> List[str]:
        """识别需要的适配"""
        adaptations = []
        
        if "language" in pattern.context and "language" in target_context:
            if pattern.context["language"] != target_context["language"]:
                adaptations.append(f"需要从{pattern.context['language']}适配到{target_context['language']}")
        
        if "framework" in pattern.context and "framework" in target_context:
            if pattern.context["framework"] != target_context["framework"]:
                adaptations.append(f"需要从{pattern.context['framework']}框架适配到{target_context['framework']}框架")
        
        if "scale" in pattern.context and "scale" in target_context:
            scale_order = ["small", "medium", "large", "enterprise"]
            pattern_scale_idx = scale_order.index(pattern.context["scale"]) if pattern.context["scale"] in scale_order else 1
            target_scale_idx = scale_order.index(target_context["scale"]) if target_context["scale"] in scale_order else 1
            
            if target_scale_idx > pattern_scale_idx:
                adaptations.append("需要增强模式的可扩展性以适应更大规模")
        
        return adaptations
    
    def export_practices_to_standards(
        self,
        output_dir: str,
        categories: Optional[List[PracticeCategory]] = None,
        min_quality: Optional[PracticeQuality] = None
    ) -> Dict[str, str]:
        """导出最佳实践到礼部规范库
        
        Args:
            output_dir: 输出目录
            categories: 要导出的类别列表
            min_quality: 最低质量要求
        
        Returns:
            导出的文件路径映射
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        practices_to_export = self._filter_practices_for_export(categories, min_quality)
        
        for category, practices in practices_to_export.items():
            if not practices:
                continue
            
            filename = f"{category.value}_best_practices.md"
            filepath = output_path / filename
            
            content = self._generate_category_document(category, practices)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            exported_files[category.value] = str(filepath)
            
            self._logger.info(f"导出{category.value}类别的最佳实践到{filepath}")
        
        index_path = output_path / "best_practices_index.md"
        index_content = self._generate_index_document(practices_to_export)
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        exported_files["index"] = str(index_path)
        
        return exported_files
    
    def _filter_practices_for_export(
        self,
        categories: Optional[List[PracticeCategory]],
        min_quality: Optional[PracticeQuality]
    ) -> Dict[PracticeCategory, List[ExtractedPractice]]:
        """筛选要导出的实践"""
        filtered = defaultdict(list)
        
        quality_order = [
            PracticeQuality.CRITICAL,
            PracticeQuality.POOR,
            PracticeQuality.ACCEPTABLE,
            PracticeQuality.GOOD,
            PracticeQuality.EXCELLENT
        ]
        
        for practice in self._practices.values():
            if categories and practice.category not in categories:
                continue
            
            if min_quality:
                min_index = quality_order.index(min_quality)
                practice_index = quality_order.index(practice.quality)
                if practice_index < min_index:
                    continue
            
            filtered[practice.category].append(practice)
        
        for category in filtered:
            filtered[category] = sorted(
                filtered[category],
                key=lambda p: p.quality_score,
                reverse=True
            )
        
        return filtered
    
    def _generate_category_document(
        self,
        category: PracticeCategory,
        practices: List[ExtractedPractice]
    ) -> str:
        """生成类别文档"""
        category_names = {
            PracticeCategory.CODE: "代码最佳实践",
            PracticeCategory.ARCHITECTURE: "架构最佳实践",
            PracticeCategory.PROCESS: "流程最佳实践",
            PracticeCategory.PERFORMANCE: "性能最佳实践",
            PracticeCategory.SECURITY: "安全最佳实践",
            PracticeCategory.TESTING: "测试最佳实践",
            PracticeCategory.DOCUMENTATION: "文档最佳实践",
            PracticeCategory.DEPLOYMENT: "部署最佳实践"
        }
        
        doc = f"# {category_names.get(category, category.value)}\n\n"
        doc += f"本文档包含{len(practices)}个最佳实践。\n\n"
        doc += "---\n\n"
        
        for i, practice in enumerate(practices, 1):
            doc += f"## {i}. {practice.title}\n\n"
            doc += f"**质量等级**: {practice.quality.value}  \n"
            doc += f"**质量分数**: {practice.quality_score:.2f}  \n"
            doc += f"**适用性**: {practice.applicability:.2f}  \n"
            doc += f"**影响力**: {practice.impact:.2f}  \n\n"
            
            doc += "### 描述\n\n"
            doc += f"{practice.description}\n\n"
            
            if practice.benefits:
                doc += "### 收益\n\n"
                for benefit in practice.benefits:
                    doc += f"- {benefit}\n"
                doc += "\n"
            
            if practice.implementation_steps:
                doc += "### 实施步骤\n\n"
                for step in practice.implementation_steps:
                    doc += f"{step['step']}. **{step['action']}**: {step['details']}\n"
                doc += "\n"
            
            if practice.risks:
                doc += "### 注意事项\n\n"
                for risk in practice.risks:
                    doc += f"- ⚠️ {risk}\n"
                doc += "\n"
            
            doc += "---\n\n"
        
        return doc
    
    def _generate_index_document(
        self,
        practices_by_category: Dict[PracticeCategory, List[ExtractedPractice]]
    ) -> str:
        """生成索引文档"""
        doc = "# 最佳实践索引\n\n"
        doc += "本索引包含所有导出的最佳实践文档。\n\n"
        doc += "---\n\n"
        
        doc += "## 文档列表\n\n"
        
        total_practices = 0
        for category, practices in practices_by_category.items():
            if practices:
                count = len(practices)
                total_practices += count
                doc += f"- [{category.value}_best_practices.md]({category.value}_best_practices.md) - {count}个最佳实践\n"
        
        doc += f"\n**总计**: {total_practices}个最佳实践\n\n"
        
        doc += "---\n\n"
        doc += "## 使用指南\n\n"
        doc += "1. 根据需要选择相应类别的最佳实践文档\n"
        doc += "2. 评估最佳实践的适用性和质量分数\n"
        doc += "3. 参考实施步骤进行应用\n"
        doc += "4. 注意潜在风险和注意事项\n\n"
        
        doc += "---\n\n"
        doc += f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return doc
