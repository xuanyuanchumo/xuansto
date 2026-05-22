#!/usr/bin/env python3
"""
知识学习系统模块 - Sanliu 技能

功能：
1. PatternRecognizer 类：模式识别器
   - 代码模式识别
   - 行为模式识别
   - 模式库管理

2. BestPracticeExtractor 类：最佳实践提取器
   - 最佳实践识别
   - 实践评分
   - 实践推荐

3. FixStrategyLearner 类：修复策略学习器
   - 修复策略学习
   - 策略效果评估
   - 策略优化

4. KnowledgeQualityEvaluator 类：知识质量评估器
   - 知识质量评分
   - 知识有效性验证
   - 知识淘汰机制

与 knowledge_base.py 集成，提供完整的知识学习和管理能力。

使用示例：
    from knowledge_learning_system import (
        PatternRecognizer,
        BestPracticeExtractor,
        FixStrategyLearner,
        KnowledgeQualityEvaluator
    )
    
    # 模式识别
    recognizer = PatternRecognizer()
    patterns = recognizer.recognize_code_patterns(source_code)
    
    # 最佳实践提取
    extractor = BestPracticeExtractor()
    practices = extractor.extract_from_codebase(codebase_path)
    
    # 修复策略学习
    learner = FixStrategyLearner()
    learner.learn_from_fix(issue, fix)
    
    # 知识质量评估
    evaluator = KnowledgeQualityEvaluator()
    quality = evaluator.evaluate_knowledge(knowledge_item)
"""

import hashlib
import json
import logging
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable

# 添加当前目录到路径
sys.path.insert(0, str(get_path_config().SKILL_ROOT))

try:
    from .knowledge_base import (
        KnowledgeBase,
        KnowledgeItem,
        KnowledgeType,
        KnowledgeStatus
    )
except ImportError:
    try:
        from knowledge_base import (
            KnowledgeBase,
            KnowledgeItem,
            KnowledgeType,
            KnowledgeStatus
        )
    except ImportError:
        # 如果还是失败，创建空类以避免导入错误
        class KnowledgeBase: pass
        class KnowledgeItem: pass
        class KnowledgeType: pass
        class KnowledgeStatus: pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PatternCategory(Enum):
    CODE = "code"
    BEHAVIORAL = "behavioral"
    STRUCTURAL = "structural"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ANTI_PATTERN = "anti_pattern"


class PatternConfidence(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class PracticeCategory(Enum):
    CODING_STYLE = "coding_style"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    SECURITY = "security"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ERROR_HANDLING = "error_handling"


class PracticeLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class FixStrategyType(Enum):
    DIRECT_FIX = "direct_fix"
    WORKAROUND = "workaround"
    REFACTORING = "refactoring"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    ENVIRONMENT = "environment"


class FixEffectiveness(Enum):
    INEFFECTIVE = "ineffective"
    PARTIALLY_EFFECTIVE = "partially_effective"
    EFFECTIVE = "effective"
    HIGHLY_EFFECTIVE = "highly_effective"


class QualityDimension(Enum):
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"
    TIMELINESS = "timeliness"
    USABILITY = "usability"
    CONSISTENCY = "consistency"


class QualityLevel(Enum):
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class CodePattern:
    pattern_id: str
    category: PatternCategory
    name: str
    description: str
    pattern_regex: str = ""
    code_template: str = ""
    indicators: List[str] = field(default_factory=list)
    confidence: PatternConfidence = PatternConfidence.MEDIUM
    occurrence_count: int = 0
    success_rate: float = 0.0
    tags: List[str] = field(default_factory=list)
    examples: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "category": self.category.value,
            "name": self.name,
            "description": self.description,
            "pattern_regex": self.pattern_regex,
            "code_template": self.code_template,
            "indicators": self.indicators,
            "confidence": self.confidence.value,
            "occurrence_count": self.occurrence_count,
            "success_rate": self.success_rate,
            "tags": self.tags,
            "examples": self.examples,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodePattern":
        return cls(
            pattern_id=data.get("pattern_id", ""),
            category=PatternCategory(data.get("category", "code")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            pattern_regex=data.get("pattern_regex", ""),
            code_template=data.get("code_template", ""),
            indicators=data.get("indicators", []),
            confidence=PatternConfidence(data.get("confidence", "medium")),
            occurrence_count=data.get("occurrence_count", 0),
            success_rate=data.get("success_rate", 0.0),
            tags=data.get("tags", []),
            examples=data.get("examples", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class BehavioralPattern:
    pattern_id: str
    name: str
    description: str
    trigger_conditions: List[Dict[str, Any]] = field(default_factory=list)
    expected_actions: List[Dict[str, Any]] = field(default_factory=list)
    frequency: int = 0
    last_observed: str = ""
    context_tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "description": self.description,
            "trigger_conditions": self.trigger_conditions,
            "expected_actions": self.expected_actions,
            "frequency": self.frequency,
            "last_observed": self.last_observed,
            "context_tags": self.context_tags,
            "metadata": self.metadata
        }


@dataclass
class PatternMatchResult:
    pattern: CodePattern
    matched_text: str
    start_pos: int
    end_pos: int
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.pattern.to_dict(),
            "matched_text": self.matched_text,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "confidence": self.confidence,
            "context": self.context
        }


@dataclass
class BestPractice:
    practice_id: str
    category: PracticeCategory
    level: PracticeLevel
    title: str
    description: str
    rationale: str = ""
    code_example: str = ""
    anti_example: str = ""
    benefits: List[str] = field(default_factory=list)
    drawbacks: List[str] = field(default_factory=list)
    applicability: List[str] = field(default_factory=list)
    score: float = 0.0
    usage_count: int = 0
    success_rate: float = 0.0
    tags: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "practice_id": self.practice_id,
            "category": self.category.value,
            "level": self.level.value,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "code_example": self.code_example,
            "anti_example": self.anti_example,
            "benefits": self.benefits,
            "drawbacks": self.drawbacks,
            "applicability": self.applicability,
            "score": self.score,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "tags": self.tags,
            "references": self.references,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BestPractice":
        return cls(
            practice_id=data.get("practice_id", ""),
            category=PracticeCategory(data.get("category", "coding_style")),
            level=PracticeLevel(data.get("level", "intermediate")),
            title=data.get("title", ""),
            description=data.get("description", ""),
            rationale=data.get("rationale", ""),
            code_example=data.get("code_example", ""),
            anti_example=data.get("anti_example", ""),
            benefits=data.get("benefits", []),
            drawbacks=data.get("drawbacks", []),
            applicability=data.get("applicability", []),
            score=data.get("score", 0.0),
            usage_count=data.get("usage_count", 0),
            success_rate=data.get("success_rate", 0.0),
            tags=data.get("tags", []),
            references=data.get("references", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class PracticeRecommendation:
    practice: BestPractice
    relevance_score: float
    applicability_score: float
    priority: int
    reasons: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "practice": self.practice.to_dict(),
            "relevance_score": self.relevance_score,
            "applicability_score": self.applicability_score,
            "priority": self.priority,
            "reasons": self.reasons,
            "suggestions": self.suggestions
        }


@dataclass
class FixStrategy:
    strategy_id: str
    strategy_type: FixStrategyType
    name: str
    description: str
    issue_patterns: List[str] = field(default_factory=list)
    fix_steps: List[Dict[str, str]] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    effectiveness: FixEffectiveness = FixEffectiveness.EFFECTIVE
    application_count: int = 0
    success_count: int = 0
    average_time: float = 0.0
    tags: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_type": self.strategy_type.value,
            "name": self.name,
            "description": self.description,
            "issue_patterns": self.issue_patterns,
            "fix_steps": self.fix_steps,
            "prerequisites": self.prerequisites,
            "risks": self.risks,
            "effectiveness": self.effectiveness.value,
            "application_count": self.application_count,
            "success_count": self.success_count,
            "average_time": self.average_time,
            "tags": self.tags,
            "examples": self.examples,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FixStrategy":
        return cls(
            strategy_id=data.get("strategy_id", ""),
            strategy_type=FixStrategyType(data.get("strategy_type", "direct_fix")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            issue_patterns=data.get("issue_patterns", []),
            fix_steps=data.get("fix_steps", []),
            prerequisites=data.get("prerequisites", []),
            risks=data.get("risks", []),
            effectiveness=FixEffectiveness(data.get("effectiveness", "effective")),
            application_count=data.get("application_count", 0),
            success_count=data.get("success_count", 0),
            average_time=data.get("average_time", 0.0),
            tags=data.get("tags", []),
            examples=data.get("examples", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class FixRecord:
    record_id: str
    issue_type: str
    issue_description: str
    strategy_used: str
    fix_description: str
    time_taken: float
    success: bool
    side_effects: List[str] = field(default_factory=list)
    feedback: str = ""
    timestamp: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "issue_type": self.issue_type,
            "issue_description": self.issue_description,
            "strategy_used": self.strategy_used,
            "fix_description": self.fix_description,
            "time_taken": self.time_taken,
            "success": self.success,
            "side_effects": self.side_effects,
            "feedback": self.feedback,
            "timestamp": self.timestamp,
            "context": self.context
        }


@dataclass
class StrategyEvaluation:
    strategy_id: str
    total_applications: int
    success_rate: float
    average_time: float
    effectiveness_score: float
    trend: str
    recommendations: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "total_applications": self.total_applications,
            "success_rate": self.success_rate,
            "average_time": self.average_time,
            "effectiveness_score": self.effectiveness_score,
            "trend": self.trend,
            "recommendations": self.recommendations,
            "metrics": self.metrics
        }


@dataclass
class QualityScore:
    overall_score: float
    level: QualityLevel
    dimension_scores: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "level": self.level.value,
            "dimension_scores": self.dimension_scores,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendations": self.recommendations
        }


@dataclass
class ValidationResult:
    is_valid: bool
    validation_score: float
    issues: List[str]
    warnings: List[str]
    suggestions: List[str]
    checked_aspects: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "validation_score": self.validation_score,
            "issues": self.issues,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "checked_aspects": self.checked_aspects
        }


@dataclass
class RetirementCandidate:
    knowledge_id: str
    retirement_reason: str
    quality_score: float
    last_used: str
    usage_trend: str
    recommendation: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "retirement_reason": self.retirement_reason,
            "quality_score": self.quality_score,
            "last_used": self.last_used,
            "usage_trend": self.usage_trend,
            "recommendation": self.recommendation,
            "metadata": self.metadata
        }


class PatternRecognizer:
    """模式识别器
    
    负责识别代码模式和行为模式，支持模式库管理。
    
    功能：
    - 代码模式识别：识别代码中的设计模式、反模式等
    - 行为模式识别：识别用户行为、系统行为模式
    - 模式库管理：存储、检索、更新识别到的模式
    
    使用示例：
        recognizer = PatternRecognizer()
        
        # 识别代码模式
        patterns = recognizer.recognize_code_patterns(source_code)
        
        # 识别行为模式
        behaviors = recognizer.recognize_behavioral_patterns(behavior_data)
        
        # 添加自定义模式
        recognizer.add_pattern(custom_pattern)
    """
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        storage_path: Optional[Path] = None
    ):
        self.knowledge_base = knowledge_base
        self.storage_path = storage_path or Path("./pattern_recognizer_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._code_patterns: Dict[str, CodePattern] = {}
        self._behavioral_patterns: Dict[str, BehavioralPattern] = {}
        self._pattern_index: Dict[str, List[str]] = defaultdict(list)
        self._recognition_history: List[Dict[str, Any]] = []
        
        self._initialize_default_patterns()
        self._load_patterns()
    
    def _initialize_default_patterns(self) -> None:
        default_code_patterns = [
            CodePattern(
                pattern_id="CP-SINGLETON-001",
                category=PatternCategory.STRUCTURAL,
                name="单例模式",
                description="确保一个类只有一个实例",
                pattern_regex=r"class\s+\w+.*:\s*\n\s*_instance\s*=\s*None",
                indicators=["_instance", "__new__", "getInstance"],
                confidence=PatternConfidence.HIGH,
                tags=["design_pattern", "creational"]
            ),
            CodePattern(
                pattern_id="CP-FACTORY-001",
                category=PatternCategory.STRUCTURAL,
                name="工厂模式",
                description="创建对象的接口",
                pattern_regex=r"(def\s+create_\w+|class\s+\w+Factory)",
                indicators=["Factory", "create_", "build"],
                confidence=PatternConfidence.HIGH,
                tags=["design_pattern", "creational"]
            ),
            CodePattern(
                pattern_id="CP-OBSERVER-001",
                category=PatternCategory.BEHAVIORAL,
                name="观察者模式",
                description="定义对象间的一对多依赖",
                pattern_regex=r"(def\s+(add|remove|notify)_observer|class\s+\w+Observer)",
                indicators=["observer", "subscribe", "notify", "listener"],
                confidence=PatternConfidence.HIGH,
                tags=["design_pattern", "behavioral"]
            ),
            CodePattern(
                pattern_id="CP-TRY-EXCEPT-001",
                category=PatternCategory.CODE,
                name="异常处理模式",
                description="标准的异常处理结构",
                pattern_regex=r"try:\s*\n.*\n\s*except\s+\w+",
                indicators=["try", "except", "finally", "raise"],
                confidence=PatternConfidence.VERY_HIGH,
                tags=["error_handling", "best_practice"]
            ),
            CodePattern(
                pattern_id="CP-CONTEXT-MANAGER-001",
                category=PatternCategory.CODE,
                name="上下文管理器模式",
                description="使用 with 语句管理资源",
                pattern_regex=r"(with\s+\w+|def\s+__enter__|def\s+__exit__)",
                indicators=["with", "__enter__", "__exit__", "contextmanager"],
                confidence=PatternConfidence.VERY_HIGH,
                tags=["resource_management", "best_practice"]
            ),
            CodePattern(
                pattern_id="CP-DECORATOR-001",
                category=PatternCategory.STRUCTURAL,
                name="装饰器模式",
                description="动态添加功能到对象",
                pattern_regex=r"@\w+.*\n\s*def\s+\w+",
                indicators=["@", "wrapper", "decorator"],
                confidence=PatternConfidence.HIGH,
                tags=["design_pattern", "python"]
            ),
            CodePattern(
                pattern_id="CP-GOD-CLASS-001",
                category=PatternCategory.ANTI_PATTERN,
                name="上帝类反模式",
                description="承担过多职责的类",
                pattern_regex=r"",
                indicators=[],
                confidence=PatternConfidence.MEDIUM,
                tags=["anti_pattern", "code_smell"]
            ),
            CodePattern(
                pattern_id="CP-SPAGHETTI-001",
                category=PatternCategory.ANTI_PATTERN,
                name="面条代码反模式",
                description="复杂且难以理解的代码结构",
                pattern_regex=r"",
                indicators=[],
                confidence=PatternConfidence.LOW,
                tags=["anti_pattern", "code_smell"]
            )
        ]
        
        for pattern in default_code_patterns:
            self._code_patterns[pattern.pattern_id] = pattern
            self._index_pattern(pattern)
    
    def _index_pattern(self, pattern: CodePattern) -> None:
        self._pattern_index["by_category"][pattern.category.value].append(pattern.pattern_id)
        for tag in pattern.tags:
            self._pattern_index[f"by_tag_{tag}"].append(pattern.pattern_id)
    
    def _load_patterns(self) -> None:
        patterns_file = self.storage_path / "patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for pattern_data in data.get("code_patterns", []):
                    pattern = CodePattern.from_dict(pattern_data)
                    self._code_patterns[pattern.pattern_id] = pattern
                    self._index_pattern(pattern)
                
                logger.info(f"加载模式: {len(self._code_patterns)} 个代码模式")
            except Exception as e:
                logger.warning(f"加载模式失败: {e}")
    
    def _save_patterns(self) -> None:
        patterns_file = self.storage_path / "patterns.json"
        try:
            data = {
                "code_patterns": [p.to_dict() for p in self._code_patterns.values()],
                "behavioral_patterns": [p.to_dict() for p in self._behavioral_patterns.values()]
            }
            with open(patterns_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存模式失败: {e}")
    
    def recognize_code_patterns(
        self,
        source_code: str,
        categories: Optional[List[PatternCategory]] = None,
        min_confidence: PatternConfidence = PatternConfidence.LOW
    ) -> List[PatternMatchResult]:
        results = []
        
        confidence_order = {
            PatternConfidence.LOW: 0,
            PatternConfidence.MEDIUM: 1,
            PatternConfidence.HIGH: 2,
            PatternConfidence.VERY_HIGH: 3
        }
        min_confidence_level = confidence_order.get(min_confidence, 0)
        
        for pattern in self._code_patterns.values():
            if categories and pattern.category not in categories:
                continue
            
            if confidence_order.get(pattern.confidence, 0) < min_confidence_level:
                continue
            
            matches = self._match_pattern(source_code, pattern)
            results.extend(matches)
        
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        self._record_recognition("code", len(results))
        
        return results
    
    def _match_pattern(
        self,
        source_code: str,
        pattern: CodePattern
    ) -> List[PatternMatchResult]:
        results = []
        
        if pattern.pattern_regex:
            try:
                regex = re.compile(pattern.pattern_regex, re.MULTILINE | re.DOTALL)
                for match in regex.finditer(source_code):
                    results.append(PatternMatchResult(
                        pattern=pattern,
                        matched_text=match.group(0),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=self._calculate_match_confidence(pattern, match.group(0)),
                        context=self._extract_context(source_code, match.start(), match.end())
                    ))
            except re.error:
                pass
        
        if pattern.indicators:
            indicator_matches = self._match_by_indicators(source_code, pattern)
            results.extend(indicator_matches)
        
        return results
    
    def _match_by_indicators(
        self,
        source_code: str,
        pattern: CodePattern
    ) -> List[PatternMatchResult]:
        results = []
        lines = source_code.split("\n")
        
        for i, line in enumerate(lines):
            match_count = sum(1 for indicator in pattern.indicators if indicator in line)
            
            if match_count >= len(pattern.indicators) * 0.5:
                start_pos = sum(len(l) + 1 for l in lines[:i])
                end_pos = start_pos + len(line)
                
                results.append(PatternMatchResult(
                    pattern=pattern,
                    matched_text=line,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    confidence=match_count / len(pattern.indicators) if pattern.indicators else 0.5,
                    context={"line_number": i + 1}
                ))
        
        return results
    
    def _calculate_match_confidence(
        self,
        pattern: CodePattern,
        matched_text: str
    ) -> float:
        base_confidence = {
            PatternConfidence.LOW: 0.3,
            PatternConfidence.MEDIUM: 0.5,
            PatternConfidence.HIGH: 0.7,
            PatternConfidence.VERY_HIGH: 0.9
        }.get(pattern.confidence, 0.5)
        
        indicator_boost = 0.0
        if pattern.indicators:
            matched_indicators = sum(1 for ind in pattern.indicators if ind in matched_text)
            indicator_boost = matched_indicators / len(pattern.indicators) * 0.2
        
        return min(base_confidence + indicator_boost, 1.0)
    
    def _extract_context(
        self,
        source_code: str,
        start: int,
        end: int,
        context_lines: int = 3
    ) -> Dict[str, Any]:
        lines = source_code.split("\n")
        
        start_line = source_code[:start].count("\n")
        end_line = source_code[:end].count("\n")
        
        context_start = max(0, start_line - context_lines)
        context_end = min(len(lines), end_line + context_lines + 1)
        
        return {
            "start_line": start_line + 1,
            "end_line": end_line + 1,
            "context_lines": lines[context_start:context_end]
        }
    
    def recognize_behavioral_patterns(
        self,
        behavior_data: List[Dict[str, Any]],
        time_window: Optional[int] = None
    ) -> List[BehavioralPattern]:
        recognized = []
        
        sequences = self._extract_behavior_sequences(behavior_data)
        
        for seq in sequences:
            matching_patterns = self._find_matching_behavioral_patterns(seq)
            recognized.extend(matching_patterns)
        
        new_patterns = self._discover_new_patterns(behavior_data)
        for pattern in new_patterns:
            self._behavioral_patterns[pattern.pattern_id] = pattern
            recognized.append(pattern)
        
        self._record_recognition("behavioral", len(recognized))
        
        return recognized
    
    def _extract_behavior_sequences(
        self,
        behavior_data: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        sequences = []
        current_seq = []
        
        for i, data in enumerate(behavior_data):
            current_seq.append(data)
            
            if self._is_sequence_boundary(data, behavior_data, i):
                if len(current_seq) >= 2:
                    sequences.append(current_seq)
                current_seq = []
        
        if len(current_seq) >= 2:
            sequences.append(current_seq)
        
        return sequences
    
    def _is_sequence_boundary(
        self,
        current: Dict[str, Any],
        all_data: List[Dict[str, Any]],
        index: int
    ) -> bool:
        if index == 0:
            return False
        
        current_time = current.get("timestamp", "")
        prev_time = all_data[index - 1].get("timestamp", "")
        
        if current_time and prev_time:
            try:
                t1 = datetime.fromisoformat(current_time)
                t0 = datetime.fromisoformat(prev_time)
                if (t1 - t0).total_seconds() > 300:
                    return True
            except ValueError:
                pass
        
        current_action = current.get("action", "")
        boundary_actions = ["session_start", "session_end", "login", "logout"]
        return current_action in boundary_actions
    
    def _find_matching_behavioral_patterns(
        self,
        sequence: List[Dict[str, Any]]
    ) -> List[BehavioralPattern]:
        matching = []
        
        for pattern in self._behavioral_patterns.values():
            if self._sequence_matches_pattern(sequence, pattern):
                pattern.frequency += 1
                pattern.last_observed = datetime.now().isoformat()
                matching.append(pattern)
        
        return matching
    
    def _sequence_matches_pattern(
        self,
        sequence: List[Dict[str, Any]],
        pattern: BehavioralPattern
    ) -> bool:
        if len(sequence) < len(pattern.trigger_conditions):
            return False
        
        for i, condition in enumerate(pattern.trigger_conditions):
            if i >= len(sequence):
                return False
            
            seq_item = sequence[i]
            for key, expected_value in condition.items():
                if seq_item.get(key) != expected_value:
                    return False
        
        return True
    
    def _discover_new_patterns(
        self,
        behavior_data: List[Dict[str, Any]]
    ) -> List[BehavioralPattern]:
        new_patterns = []
        
        action_sequences = defaultdict(int)
        
        for i in range(len(behavior_data) - 1):
            seq_key = self._create_sequence_key(behavior_data[i:i+2])
            action_sequences[seq_key] += 1
        
        for seq_key, count in action_sequences.items():
            if count >= 3:
                pattern = self._create_behavioral_pattern(seq_key, count)
                if pattern:
                    new_patterns.append(pattern)
        
        return new_patterns
    
    def _create_sequence_key(self, sequence: List[Dict[str, Any]]) -> str:
        actions = [item.get("action", "unknown") for item in sequence]
        return "->".join(actions)
    
    def _create_behavioral_pattern(
        self,
        seq_key: str,
        frequency: int
    ) -> Optional[BehavioralPattern]:
        actions = seq_key.split("->")
        
        return BehavioralPattern(
            pattern_id=f"BP-{hashlib.md5(seq_key.encode()).hexdigest()[:8]}",
            name=f"行为模式: {' -> '.join(actions)}",
            description=f"检测到的高频行为序列，出现 {frequency} 次",
            trigger_conditions=[{"action": actions[0]}] if actions else [],
            expected_actions=[{"action": a} for a in actions[1:]],
            frequency=frequency,
            last_observed=datetime.now().isoformat()
        )
    
    def add_pattern(self, pattern: CodePattern) -> str:
        if not pattern.pattern_id:
            pattern.pattern_id = f"CP-CUSTOM-{hashlib.md5(pattern.name.encode()).hexdigest()[:8]}"
        
        self._code_patterns[pattern.pattern_id] = pattern
        self._index_pattern(pattern)
        self._save_patterns()
        
        logger.info(f"添加模式: {pattern.pattern_id} - {pattern.name}")
        return pattern.pattern_id
    
    def add_behavioral_pattern(self, pattern: BehavioralPattern) -> str:
        if not pattern.pattern_id:
            pattern.pattern_id = f"BP-{hashlib.md5(pattern.name.encode()).hexdigest()[:8]}"
        
        self._behavioral_patterns[pattern.pattern_id] = pattern
        self._save_patterns()
        
        logger.info(f"添加行为模式: {pattern.pattern_id} - {pattern.name}")
        return pattern.pattern_id
    
    def get_pattern(self, pattern_id: str) -> Optional[CodePattern]:
        return self._code_patterns.get(pattern_id)
    
    def get_behavioral_pattern(self, pattern_id: str) -> Optional[BehavioralPattern]:
        return self._behavioral_patterns.get(pattern_id)
    
    def find_patterns(
        self,
        category: Optional[PatternCategory] = None,
        tags: Optional[List[str]] = None,
        min_confidence: Optional[PatternConfidence] = None
    ) -> List[CodePattern]:
        results = []
        
        for pattern in self._code_patterns.values():
            if category and pattern.category != category:
                continue
            
            if tags and not any(tag in pattern.tags for tag in tags):
                continue
            
            if min_confidence:
                confidence_order = [PatternConfidence.LOW, PatternConfidence.MEDIUM, 
                                   PatternConfidence.HIGH, PatternConfidence.VERY_HIGH]
                if confidence_order.index(pattern.confidence) < confidence_order.index(min_confidence):
                    continue
            
            results.append(pattern)
        
        return results
    
    def update_pattern(
        self,
        pattern_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        pattern = self._code_patterns.get(pattern_id)
        if not pattern:
            return False
        
        for key, value in updates.items():
            if hasattr(pattern, key):
                setattr(pattern, key, value)
        
        self._save_patterns()
        return True
    
    def remove_pattern(self, pattern_id: str) -> bool:
        if pattern_id in self._code_patterns:
            del self._code_patterns[pattern_id]
            self._save_patterns()
            return True
        return False
    
    def _record_recognition(self, recognition_type: str, count: int) -> None:
        self._recognition_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": recognition_type,
            "count": count
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_code_patterns": len(self._code_patterns),
            "total_behavioral_patterns": len(self._behavioral_patterns),
            "by_category": {
                cat.value: len([p for p in self._code_patterns.values() if p.category == cat])
                for cat in PatternCategory
            },
            "recognition_history_count": len(self._recognition_history)
        }
    
    def export_patterns(self, output_path: str) -> None:
        data = {
            "exported_at": datetime.now().isoformat(),
            "code_patterns": [p.to_dict() for p in self._code_patterns.values()],
            "behavioral_patterns": [p.to_dict() for p in self._behavioral_patterns.values()]
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"模式已导出到: {output_path}")


class BestPracticeExtractor:
    """最佳实践提取器
    
    负责从代码库中识别和提取最佳实践，支持评分和推荐。
    
    功能：
    - 最佳实践识别：从代码中识别最佳实践模式
    - 实践评分：对识别的实践进行质量评分
    - 实践推荐：根据上下文推荐适用的最佳实践
    
    使用示例：
        extractor = BestPracticeExtractor()
        
        # 从代码库提取最佳实践
        practices = extractor.extract_from_codebase(codebase_path)
        
        # 评分实践
        score = extractor.score_practice(practice)
        
        # 获取推荐
        recommendations = extractor.get_recommendations(context)
    """
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        storage_path: Optional[Path] = None
    ):
        self.knowledge_base = knowledge_base
        self.storage_path = storage_path or Path("./best_practices_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._practices: Dict[str, BestPractice] = {}
        self._practice_index: Dict[str, List[str]] = defaultdict(list)
        self._extraction_history: List[Dict[str, Any]] = []
        
        self._initialize_default_practices()
        self._load_practices()
    
    def _initialize_default_practices(self) -> None:
        default_practices = [
            BestPractice(
                practice_id="BP-CODE-001",
                category=PracticeCategory.CODING_STYLE,
                level=PracticeLevel.BEGINNER,
                title="使用有意义的变量名",
                description="变量名应该清晰表达其用途",
                rationale="提高代码可读性和可维护性",
                code_example="user_count = len(users)  # 好的命名\nx = len(users)  # 不好的命名",
                benefits=["提高可读性", "减少注释需求", "便于团队协作"],
                drawbacks=[],
                applicability=["所有编程语言", "所有项目规模"],
                score=0.95,
                tags=["naming", "readability", "basics"]
            ),
            BestPractice(
                practice_id="BP-CODE-002",
                category=PracticeCategory.CODING_STYLE,
                level=PracticeLevel.INTERMEDIATE,
                title="函数应该只做一件事",
                description="每个函数应该有单一明确的职责",
                rationale="遵循单一职责原则，提高代码可测试性和可维护性",
                code_example="def calculate_total(items):\n    return sum(item.price for item in items)\n\ndef format_receipt(items, total):\n    # 格式化收据\n    pass",
                benefits=["提高可测试性", "便于重构", "减少bug"],
                drawbacks=["可能导致函数数量增加"],
                applicability=["面向对象编程", "函数式编程"],
                score=0.90,
                tags=["solid", "srp", "functions"]
            ),
            BestPractice(
                practice_id="BP-ERROR-001",
                category=PracticeCategory.ERROR_HANDLING,
                level=PracticeLevel.INTERMEDIATE,
                title="使用具体的异常类型",
                description="捕获和处理具体的异常而非通用异常",
                rationale="避免意外捕获不相关的异常，便于调试",
                code_example="try:\n    value = data[key]\nexcept KeyError:\n    handle_missing_key(key)\nexcept ValueError:\n    handle_invalid_value()",
                benefits=["精确的错误处理", "更好的错误信息", "避免隐藏bug"],
                drawbacks=["代码可能变长"],
                applicability=["所有需要异常处理的场景"],
                score=0.88,
                tags=["exceptions", "error_handling", "robustness"]
            ),
            BestPractice(
                practice_id="BP-TEST-001",
                category=PracticeCategory.TESTING,
                level=PracticeLevel.BEGINNER,
                title="编写单元测试",
                description="为关键功能编写单元测试",
                rationale="确保代码正确性，便于重构",
                code_example="def test_calculate_total():\n    items = [Item(price=10), Item(price=20)]\n    assert calculate_total(items) == 30",
                benefits=["发现回归问题", "文档化行为", "支持重构"],
                drawbacks=["需要额外时间编写"],
                applicability=["所有生产代码"],
                score=0.92,
                tags=["testing", "unit_test", "quality"]
            ),
            BestPractice(
                practice_id="BP-DOC-001",
                category=PracticeCategory.DOCUMENTATION,
                level=PracticeLevel.BEGINNER,
                title="编写文档字符串",
                description="为公共API编写清晰的文档字符串",
                rationale="提高代码可用性，便于团队协作",
                code_example='def calculate_discount(price, rate):\n    """计算折扣价格。\n    \n    Args:\n        price: 原价\n        rate: 折扣率(0-1)\n    \n    Returns:\n        折扣后的价格\n    """\n    return price * (1 - rate)',
                benefits=["自动生成文档", "IDE支持", "团队协作"],
                drawbacks=["需要维护"],
                applicability=["公共API", "库开发"],
                score=0.85,
                tags=["documentation", "docstring", "api"]
            ),
            BestPractice(
                practice_id="BP-PERF-001",
                category=PracticeCategory.PERFORMANCE,
                level=PracticeLevel.ADVANCED,
                title="避免过早优化",
                description="先保证正确性，再优化性能",
                rationale="过早优化可能导致代码复杂且难以维护",
                benefits=["保持代码简洁", "聚焦真正的问题", "节省开发时间"],
                drawbacks=["后期可能需要重构"],
                applicability=["性能敏感场景"],
                score=0.82,
                tags=["performance", "optimization", "maintainability"]
            ),
            BestPractice(
                practice_id="BP-SEC-001",
                category=PracticeCategory.SECURITY,
                level=PracticeLevel.INTERMEDIATE,
                title="输入验证",
                description="验证所有外部输入",
                rationale="防止注入攻击和数据污染",
                code_example="def process_user_input(data):\n    if not isinstance(data, dict):\n        raise TypeError(\"Expected dict\")\n    if 'name' not in data:\n        raise ValueError(\"Missing name field\")\n    # 处理数据",
                benefits=["防止安全漏洞", "数据完整性", "更好的错误信息"],
                drawbacks=["需要额外代码"],
                applicability=["所有处理外部输入的场景"],
                score=0.93,
                tags=["security", "validation", "input"]
            ),
            BestPractice(
                practice_id="BP-ARCH-001",
                category=PracticeCategory.ARCHITECTURE,
                level=PracticeLevel.ADVANCED,
                title="依赖注入",
                description="通过构造函数或参数注入依赖",
                rationale="提高可测试性和灵活性",
                code_example="class UserService:\n    def __init__(self, db_connection):\n        self.db = db_connection\n\n# 使用\ndb = DatabaseConnection()\nservice = UserService(db)",
                benefits=["可测试性", "灵活性", "解耦"],
                drawbacks=["可能增加复杂性"],
                applicability=["中大型项目", "需要测试的项目"],
                score=0.87,
                tags=["architecture", "di", "testing"]
            )
        ]
        
        for practice in default_practices:
            self._practices[practice.practice_id] = practice
            self._index_practice(practice)
    
    def _index_practice(self, practice: BestPractice) -> None:
        self._practice_index["by_category"][practice.category.value].append(practice.practice_id)
        self._practice_index["by_level"][practice.level.value].append(practice.practice_id)
        for tag in practice.tags:
            self._practice_index[f"by_tag_{tag}"].append(practice.practice_id)
    
    def _load_practices(self) -> None:
        practices_file = self.storage_path / "practices.json"
        if practices_file.exists():
            try:
                with open(practices_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for practice_data in data.get("practices", []):
                    practice = BestPractice.from_dict(practice_data)
                    self._practices[practice.practice_id] = practice
                    self._index_practice(practice)
                
                logger.info(f"加载最佳实践: {len(self._practices)} 个")
            except Exception as e:
                logger.warning(f"加载最佳实践失败: {e}")
    
    def _save_practices(self) -> None:
        practices_file = self.storage_path / "practices.json"
        try:
            data = {
                "practices": [p.to_dict() for p in self._practices.values()]
            }
            with open(practices_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存最佳实践失败: {e}")
    
    def extract_from_codebase(
        self,
        codebase_path: Union[str, Path],
        file_patterns: Optional[List[str]] = None
    ) -> List[BestPractice]:
        codebase_path = Path(codebase_path)
        extracted = []
        
        file_patterns = file_patterns or ["*.py", "*.js", "*.ts", "*.java"]
        
        for pattern in file_patterns:
            for file_path in codebase_path.rglob(pattern):
                try:
                    practices = self._extract_from_file(file_path)
                    extracted.extend(practices)
                except Exception as e:
                    logger.warning(f"处理文件失败 {file_path}: {e}")
        
        self._extraction_history.append({
            "timestamp": datetime.now().isoformat(),
            "codebase_path": str(codebase_path),
            "practices_found": len(extracted)
        })
        
        return extracted
    
    def _extract_from_file(self, file_path: Path) -> List[BestPractice]:
        extracted = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return extracted
        
        extracted.extend(self._detect_docstring_practices(content, file_path))
        extracted.extend(self._detect_error_handling_practices(content, file_path))
        extracted.extend(self._detect_naming_practices(content, file_path))
        extracted.extend(self._detect_function_practices(content, file_path))
        
        return extracted
    
    def _detect_docstring_practices(
        self,
        content: str,
        file_path: Path
    ) -> List[BestPractice]:
        practices = []
        
        docstring_pattern = r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\''
        docstrings = re.findall(docstring_pattern, content)
        
        if len(docstrings) >= 3:
            practice = BestPractice(
                practice_id=f"BP-EXTRACT-DOC-{hashlib.md5(str(file_path).encode()).hexdigest()[:6]}",
                category=PracticeCategory.DOCUMENTATION,
                level=PracticeLevel.BEGINNER,
                title=f"良好的文档实践: {file_path.name}",
                description=f"文件包含 {len(docstrings)} 个文档字符串",
                code_example=docstrings[0] if docstrings else "",
                benefits=["代码文档化"],
                score=0.85,
                tags=["documentation", "docstring"]
            )
            practices.append(practice)
        
        return practices
    
    def _detect_error_handling_practices(
        self,
        content: str,
        file_path: Path
    ) -> List[BestPractice]:
        practices = []
        
        specific_except = r'except\s+\w+Error'
        generic_except = r'except\s*:'
        
        specific_count = len(re.findall(specific_except, content))
        generic_count = len(re.findall(generic_except, content))
        
        if specific_count >= 2 and generic_count == 0:
            practice = BestPractice(
                practice_id=f"BP-EXTRACT-ERR-{hashlib.md5(str(file_path).encode()).hexdigest()[:6]}",
                category=PracticeCategory.ERROR_HANDLING,
                level=PracticeLevel.INTERMEDIATE,
                title=f"良好的异常处理: {file_path.name}",
                description=f"使用具体异常类型 {specific_count} 次，无通用异常捕获",
                benefits=["精确的错误处理"],
                score=0.88,
                tags=["error_handling", "exceptions"]
            )
            practices.append(practice)
        
        return practices
    
    def _detect_naming_practices(
        self,
        content: str,
        file_path: Path
    ) -> List[BestPractice]:
        practices = []
        
        good_names = re.findall(r'\b([a-z][a-z0-9_]*)\s*=', content)
        bad_names = re.findall(r'\b([a-z])\s*=', content)
        
        if len(good_names) > len(bad_names) * 5:
            practice = BestPractice(
                practice_id=f"BP-EXTRACT-NAME-{hashlib.md5(str(file_path).encode()).hexdigest()[:6]}",
                category=PracticeCategory.CODING_STYLE,
                level=PracticeLevel.BEGINNER,
                title=f"良好的命名实践: {file_path.name}",
                description="使用有意义的变量名",
                benefits=["提高可读性"],
                score=0.85,
                tags=["naming", "readability"]
            )
            practices.append(practice)
        
        return practices
    
    def _detect_function_practices(
        self,
        content: str,
        file_path: Path
    ) -> List[BestPractice]:
        practices = []
        
        functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', content)
        
        short_functions = 0
        for func in functions:
            func_pattern = rf'def\s+{func}\s*\([^)]*\):[\s\S]*?(?=\ndef\s|\nclass\s|\Z)'
            func_match = re.search(func_pattern, content)
            if func_match:
                func_lines = func_match.group(0).count('\n')
                if func_lines <= 20:
                    short_functions += 1
        
        if len(functions) > 0 and short_functions / len(functions) >= 0.8:
            practice = BestPractice(
                practice_id=f"BP-EXTRACT-FUNC-{hashlib.md5(str(file_path).encode()).hexdigest()[:6]}",
                category=PracticeCategory.CODING_STYLE,
                level=PracticeLevel.INTERMEDIATE,
                title=f"良好的函数设计: {file_path.name}",
                description=f"{short_functions}/{len(functions)} 函数保持简短",
                benefits=["可读性", "可维护性"],
                score=0.87,
                tags=["functions", "srp"]
            )
            practices.append(practice)
        
        return practices
    
    def score_practice(
        self,
        practice: BestPractice,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        score = 0.0
        
        score += self._score_completeness(practice) * 0.25
        score += self._score_clarity(practice) * 0.25
        score += self._score_applicability(practice, context) * 0.20
        score += self._score_evidence(practice) * 0.15
        score += self._score_usage(practice) * 0.15
        
        return min(score, 1.0)
    
    def _score_completeness(self, practice: BestPractice) -> float:
        score = 0.0
        
        if practice.title:
            score += 0.15
        if practice.description:
            score += 0.20
        if practice.rationale:
            score += 0.15
        if practice.code_example:
            score += 0.20
        if practice.benefits:
            score += 0.15
        if practice.applicability:
            score += 0.15
        
        return score
    
    def _score_clarity(self, practice: BestPractice) -> float:
        score = 0.5
        
        if practice.description and len(practice.description) > 20:
            score += 0.1
        
        if practice.code_example:
            lines = practice.code_example.count('\n')
            if 2 <= lines <= 10:
                score += 0.2
            elif lines > 0:
                score += 0.1
        
        if practice.benefits and len(practice.benefits) >= 2:
            score += 0.1
        
        if not practice.drawbacks:
            score -= 0.1
        
        return max(0, min(score, 1.0))
    
    def _score_applicability(
        self,
        practice: BestPractice,
        context: Optional[Dict[str, Any]]
    ) -> float:
        if not context:
            return 0.7
        
        score = 0.5
        
        if practice.applicability:
            context_tags = context.get("tags", [])
            for applicability in practice.applicability:
                if any(tag.lower() in applicability.lower() for tag in context_tags):
                    score += 0.1
        
        return min(score, 1.0)
    
    def _score_evidence(self, practice: BestPractice) -> float:
        score = 0.5
        
        if practice.code_example:
            score += 0.2
        
        if practice.anti_example:
            score += 0.1
        
        if practice.references:
            score += 0.1 * min(len(practice.references), 2)
        
        return min(score, 1.0)
    
    def _score_usage(self, practice: BestPractice) -> float:
        if practice.usage_count == 0:
            return 0.5
        
        score = min(practice.usage_count / 100, 0.5)
        score += practice.success_rate * 0.5
        
        return min(score, 1.0)
    
    def get_recommendations(
        self,
        context: Dict[str, Any],
        categories: Optional[List[PracticeCategory]] = None,
        level: Optional[PracticeLevel] = None,
        limit: int = 10
    ) -> List[PracticeRecommendation]:
        recommendations = []
        
        for practice in self._practices.values():
            if categories and practice.category not in categories:
                continue
            
            if level and practice.level != level:
                continue
            
            relevance = self._calculate_relevance(practice, context)
            applicability = self._calculate_applicability(practice, context)
            
            if relevance > 0.3:
                priority = self._calculate_priority(practice, relevance, applicability)
                
                recommendation = PracticeRecommendation(
                    practice=practice,
                    relevance_score=relevance,
                    applicability_score=applicability,
                    priority=priority,
                    reasons=self._generate_reasons(practice, context),
                    suggestions=self._generate_suggestions(practice, context)
                )
                recommendations.append(recommendation)
        
        recommendations.sort(key=lambda x: x.priority, reverse=True)
        return recommendations[:limit]
    
    def _calculate_relevance(
        self,
        practice: BestPractice,
        context: Dict[str, Any]
    ) -> float:
        score = 0.0
        
        context_tags = set(context.get("tags", []))
        practice_tags = set(practice.tags)
        tag_overlap = len(context_tags & practice_tags)
        if tag_overlap > 0:
            score += min(tag_overlap * 0.15, 0.4)
        
        context_issues = context.get("issues", [])
        for issue in context_issues:
            if any(issue.lower() in tag.lower() for tag in practice.tags):
                score += 0.1
        
        context_category = context.get("category")
        if context_category and practice.category.value == context_category:
            score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_applicability(
        self,
        practice: BestPractice,
        context: Dict[str, Any]
    ) -> float:
        score = 0.5
        
        project_type = context.get("project_type", "")
        for applicability in practice.applicability:
            if project_type.lower() in applicability.lower():
                score += 0.15
        
        team_level = context.get("team_level", "intermediate")
        level_order = ["beginner", "intermediate", "advanced", "expert"]
        team_level_idx = level_order.index(team_level) if team_level in level_order else 1
        practice_level_idx = level_order.index(practice.level.value)
        
        if practice_level_idx <= team_level_idx:
            score += 0.2
        elif practice_level_idx == team_level_idx + 1:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_priority(
        self,
        practice: BestPractice,
        relevance: float,
        applicability: float
    ) -> int:
        base_score = (relevance * 0.6 + applicability * 0.4) * 100
        
        if practice.success_rate > 0.8:
            base_score += 10
        elif practice.success_rate > 0.6:
            base_score += 5
        
        if practice.level == PracticeLevel.BEGINNER:
            base_score += 5
        
        return int(base_score)
    
    def _generate_reasons(
        self,
        practice: BestPractice,
        context: Dict[str, Any]
    ) -> List[str]:
        reasons = []
        
        if practice.benefits:
            reasons.append(f"主要收益: {practice.benefits[0]}")
        
        if practice.success_rate > 0.8:
            reasons.append(f"高成功率: {practice.success_rate:.0%}")
        
        context_issues = context.get("issues", [])
        for issue in context_issues:
            if any(issue.lower() in tag.lower() for tag in practice.tags):
                reasons.append(f"与问题相关: {issue}")
                break
        
        return reasons[:3]
    
    def _generate_suggestions(
        self,
        practice: BestPractice,
        context: Dict[str, Any]
    ) -> List[str]:
        suggestions = []
        
        if practice.code_example:
            suggestions.append("参考代码示例进行实现")
        
        if practice.prerequisites:
            suggestions.append(f"确保满足前提条件: {', '.join(practice.prerequisites[:2])}")
        
        if practice.level == PracticeLevel.ADVANCED:
            suggestions.append("建议先熟悉基础概念再应用")
        
        return suggestions[:3]
    
    def add_practice(self, practice: BestPractice) -> str:
        if not practice.practice_id:
            practice.practice_id = f"BP-CUSTOM-{hashlib.md5(practice.title.encode()).hexdigest()[:8]}"
        
        practice.score = self.score_practice(practice)
        
        self._practices[practice.practice_id] = practice
        self._index_practice(practice)
        self._save_practices()
        
        logger.info(f"添加最佳实践: {practice.practice_id} - {practice.title}")
        return practice.practice_id
    
    def get_practice(self, practice_id: str) -> Optional[BestPractice]:
        return self._practices.get(practice_id)
    
    def find_practices(
        self,
        category: Optional[PracticeCategory] = None,
        level: Optional[PracticeLevel] = None,
        tags: Optional[List[str]] = None,
        min_score: float = 0.0
    ) -> List[BestPractice]:
        results = []
        
        for practice in self._practices.values():
            if category and practice.category != category:
                continue
            
            if level and practice.level != level:
                continue
            
            if tags and not any(tag in practice.tags for tag in tags):
                continue
            
            if practice.score < min_score:
                continue
            
            results.append(practice)
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def update_practice(
        self,
        practice_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        practice = self._practices.get(practice_id)
        if not practice:
            return False
        
        for key, value in updates.items():
            if hasattr(practice, key):
                setattr(practice, key, value)
        
        practice.score = self.score_practice(practice)
        self._save_practices()
        
        return True
    
    def record_usage(
        self,
        practice_id: str,
        success: bool
    ) -> None:
        practice = self._practices.get(practice_id)
        if not practice:
            return
        
        practice.usage_count += 1
        
        if success:
            current_successes = practice.success_rate * (practice.usage_count - 1)
            practice.success_rate = (current_successes + 1) / practice.usage_count
        else:
            current_successes = practice.success_rate * (practice.usage_count - 1)
            practice.success_rate = current_successes / practice.usage_count
        
        self._save_practices()
    
    def get_statistics(self) -> Dict[str, Any]:
        by_category: Dict[str, int] = defaultdict(int)
        by_level: Dict[str, int] = defaultdict(int)
        
        for practice in self._practices.values():
            by_category[practice.category.value] += 1
            by_level[practice.level.value] += 1
        
        return {
            "total_practices": len(self._practices),
            "by_category": dict(by_category),
            "by_level": dict(by_level),
            "average_score": sum(p.score for p in self._practices.values()) / len(self._practices) if self._practices else 0,
            "extraction_history_count": len(self._extraction_history)
        }
    
    def export_practices(self, output_path: str) -> None:
        data = {
            "exported_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "practices": [p.to_dict() for p in self._practices.values()]
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"最佳实践已导出到: {output_path}")


class FixStrategyLearner:
    """修复策略学习器
    
    负责学习和管理问题修复策略，支持效果评估和优化。
    
    功能：
    - 修复策略学习：从修复记录中学习有效策略
    - 策略效果评估：评估策略的成功率和效率
    - 策略优化：优化和改进现有策略
    
    使用示例：
        learner = FixStrategyLearner()
        
        # 学习修复
        learner.learn_from_fix(issue, fix)
        
        # 获取策略
        strategy = learner.get_strategy_for_issue(issue_type)
        
        # 评估效果
        evaluation = learner.evaluate_strategy(strategy_id)
    """
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        storage_path: Optional[Path] = None
    ):
        self.knowledge_base = knowledge_base
        self.storage_path = storage_path or Path("./fix_strategy_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._strategies: Dict[str, FixStrategy] = {}
        self._fix_records: List[FixRecord] = []
        self._strategy_index: Dict[str, List[str]] = defaultdict(list)
        
        self._initialize_default_strategies()
        self._load_data()
    
    def _initialize_default_strategies(self) -> None:
        default_strategies = [
            FixStrategy(
                strategy_id="FS-NULL-001",
                strategy_type=FixStrategyType.DIRECT_FIX,
                name="空指针检查修复",
                description="添加空值检查防止空指针异常",
                issue_patterns=["NullPointerException", "NoneType", "AttributeError.*None"],
                fix_steps=[
                    {"step": 1, "action": "定位空值来源"},
                    {"step": 2, "action": "添加空值检查"},
                    {"step": 3, "action": "提供默认值或处理逻辑"}
                ],
                prerequisites=["理解代码逻辑"],
                risks=["可能隐藏其他问题"],
                effectiveness=FixEffectiveness.HIGHLY_EFFECTIVE,
                tags=["null", "error_handling", "common"]
            ),
            FixStrategy(
                strategy_id="FS-TYPE-001",
                strategy_type=FixStrategyType.DIRECT_FIX,
                name="类型错误修复",
                description="修复类型不匹配问题",
                issue_patterns=["TypeError", "type.*expected", "unsupported operand"],
                fix_steps=[
                    {"step": 1, "action": "确定期望类型"},
                    {"step": 2, "action": "添加类型转换"},
                    {"step": 3, "action": "验证转换结果"}
                ],
                prerequisites=["了解数据类型"],
                risks=["可能丢失精度"],
                effectiveness=FixEffectiveness.EFFECTIVE,
                tags=["type", "conversion", "common"]
            ),
            FixStrategy(
                strategy_id="FS-INDEX-001",
                strategy_type=FixStrategyType.DIRECT_FIX,
                name="索引越界修复",
                description="修复数组/列表索引越界问题",
                issue_patterns=["IndexError", "ArrayIndexOutOfBoundsException", "list index out of range"],
                fix_steps=[
                    {"step": 1, "action": "检查索引范围"},
                    {"step": 2, "action": "添加边界检查"},
                    {"step": 3, "action": "处理边界情况"}
                ],
                prerequisites=["理解数据结构"],
                risks=[],
                effectiveness=FixEffectiveness.EFFECTIVE,
                tags=["index", "boundary", "common"]
            ),
            FixStrategy(
                strategy_id="FS-DEP-001",
                strategy_type=FixStrategyType.DEPENDENCY,
                name="依赖问题修复",
                description="解决依赖缺失或版本冲突",
                issue_patterns=["ModuleNotFoundError", "ImportError", "dependency", "version conflict"],
                fix_steps=[
                    {"step": 1, "action": "确认依赖名称和版本"},
                    {"step": 2, "action": "安装或更新依赖"},
                    {"step": 3, "action": "验证依赖可用"}
                ],
                prerequisites=["包管理器访问权限"],
                risks=["版本冲突"],
                effectiveness=FixEffectiveness.EFFECTIVE,
                tags=["dependency", "import", "environment"]
            ),
            FixStrategy(
                strategy_id="FS-SYNTAX-001",
                strategy_type=FixStrategyType.DIRECT_FIX,
                name="语法错误修复",
                description="修复代码语法错误",
                issue_patterns=["SyntaxError", "IndentationError", "ParseError"],
                fix_steps=[
                    {"step": 1, "action": "定位语法错误位置"},
                    {"step": 2, "action": "修正语法"},
                    {"step": 3, "action": "验证修复"}
                ],
                prerequisites=["语言语法知识"],
                risks=[],
                effectiveness=FixEffectiveness.HIGHLY_EFFECTIVE,
                tags=["syntax", "parsing", "common"]
            ),
            FixStrategy(
                strategy_id="FS-REF-001",
                strategy_type=FixStrategyType.REFACTORING,
                name="重构优化",
                description="通过重构改进代码结构",
                issue_patterns=["code smell", "duplicate", "complex", "long method"],
                fix_steps=[
                    {"step": 1, "action": "识别重构目标"},
                    {"step": 2, "action": "设计重构方案"},
                    {"step": 3, "action": "执行重构"},
                    {"step": 4, "action": "验证功能不变"}
                ],
                prerequisites=["测试覆盖", "代码理解"],
                risks=["可能引入新bug"],
                effectiveness=FixEffectiveness.EFFECTIVE,
                tags=["refactoring", "quality", "improvement"]
            ),
            FixStrategy(
                strategy_id="FS-CONFIG-001",
                strategy_type=FixStrategyType.CONFIGURATION,
                name="配置问题修复",
                description="解决配置错误",
                issue_patterns=["config", "setting", "environment variable", "property"],
                fix_steps=[
                    {"step": 1, "action": "检查配置文件"},
                    {"step": 2, "action": "验证配置值"},
                    {"step": 3, "action": "修正配置"}
                ],
                prerequisites=["配置文件访问权限"],
                risks=["影响其他功能"],
                effectiveness=FixEffectiveness.EFFECTIVE,
                tags=["config", "settings", "environment"]
            ),
            FixStrategy(
                strategy_id="FS-PERF-001",
                strategy_type=FixStrategyType.REFACTORING,
                name="性能优化修复",
                description="解决性能问题",
                issue_patterns=["slow", "timeout", "memory", "performance"],
                fix_steps=[
                    {"step": 1, "action": "性能分析定位瓶颈"},
                    {"step": 2, "action": "优化算法或数据结构"},
                    {"step": 3, "action": "测试性能改进"}
                ],
                prerequisites=["性能分析工具"],
                risks=["可能影响可读性"],
                effectiveness=FixEffectiveness.PARTIALLY_EFFECTIVE,
                tags=["performance", "optimization", "memory"]
            )
        ]
        
        for strategy in default_strategies:
            self._strategies[strategy.strategy_id] = strategy
            self._index_strategy(strategy)
    
    def _index_strategy(self, strategy: FixStrategy) -> None:
        self._strategy_index["by_type"][strategy.strategy_type.value].append(strategy.strategy_id)
        for tag in strategy.tags:
            self._strategy_index[f"by_tag_{tag}"].append(strategy.strategy_id)
        for pattern in strategy.issue_patterns:
            self._strategy_index[f"by_pattern_{pattern[:20]}"].append(strategy.strategy_id)
    
    def _load_data(self) -> None:
        strategies_file = self.storage_path / "strategies.json"
        records_file = self.storage_path / "fix_records.json"
        
        if strategies_file.exists():
            try:
                with open(strategies_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for strategy_data in data.get("strategies", []):
                    strategy = FixStrategy.from_dict(strategy_data)
                    self._strategies[strategy.strategy_id] = strategy
                    self._index_strategy(strategy)
                
                logger.info(f"加载修复策略: {len(self._strategies)} 个")
            except Exception as e:
                logger.warning(f"加载修复策略失败: {e}")
        
        if records_file.exists():
            try:
                with open(records_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for record_data in data.get("records", []):
                    record = FixRecord(
                        record_id=record_data.get("record_id", ""),
                        issue_type=record_data.get("issue_type", ""),
                        issue_description=record_data.get("issue_description", ""),
                        strategy_used=record_data.get("strategy_used", ""),
                        fix_description=record_data.get("fix_description", ""),
                        time_taken=record_data.get("time_taken", 0.0),
                        success=record_data.get("success", False),
                        side_effects=record_data.get("side_effects", []),
                        feedback=record_data.get("feedback", ""),
                        timestamp=record_data.get("timestamp", ""),
                        context=record_data.get("context", {})
                    )
                    self._fix_records.append(record)
                
                logger.info(f"加载修复记录: {len(self._fix_records)} 条")
            except Exception as e:
                logger.warning(f"加载修复记录失败: {e}")
    
    def _save_data(self) -> None:
        strategies_file = self.storage_path / "strategies.json"
        records_file = self.storage_path / "fix_records.json"
        
        try:
            with open(strategies_file, "w", encoding="utf-8") as f:
                json.dump({
                    "strategies": [s.to_dict() for s in self._strategies.values()]
                }, f, ensure_ascii=False, indent=2)
            
            with open(records_file, "w", encoding="utf-8") as f:
                json.dump({
                    "records": [r.to_dict() for r in self._fix_records]
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
    
    def learn_from_fix(
        self,
        issue: Dict[str, Any],
        fix: Dict[str, Any],
        outcome: Dict[str, Any]
    ) -> Optional[FixStrategy]:
        issue_type = issue.get("type", "unknown")
        issue_description = issue.get("description", "")
        fix_description = fix.get("description", "")
        strategy_used = fix.get("strategy_id", "")
        time_taken = outcome.get("time_taken", 0.0)
        success = outcome.get("success", False)
        side_effects = outcome.get("side_effects", [])
        
        record = FixRecord(
            record_id=f"FR-{hashlib.md5(f'{issue_type}{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}",
            issue_type=issue_type,
            issue_description=issue_description,
            strategy_used=strategy_used,
            fix_description=fix_description,
            time_taken=time_taken,
            success=success,
            side_effects=side_effects,
            timestamp=datetime.now().isoformat(),
            context=issue.get("context", {})
        )
        
        self._fix_records.append(record)
        
        if strategy_used and strategy_used in self._strategies:
            self._update_strategy_stats(strategy_used, success, time_taken)
        
        new_strategy = self._extract_new_strategy(issue, fix, outcome)
        if new_strategy:
            self._strategies[new_strategy.strategy_id] = new_strategy
            self._index_strategy(new_strategy)
        
        self._save_data()
        
        return new_strategy
    
    def _update_strategy_stats(
        self,
        strategy_id: str,
        success: bool,
        time_taken: float
    ) -> None:
        strategy = self._strategies.get(strategy_id)
        if not strategy:
            return
        
        strategy.application_count += 1
        if success:
            strategy.success_count += 1
        
        if strategy.application_count > 1:
            strategy.average_time = (
                (strategy.average_time * (strategy.application_count - 1) + time_taken)
                / strategy.application_count
            )
        else:
            strategy.average_time = time_taken
        
        success_rate = strategy.success_count / strategy.application_count
        if success_rate >= 0.8:
            strategy.effectiveness = FixEffectiveness.HIGHLY_EFFECTIVE
        elif success_rate >= 0.6:
            strategy.effectiveness = FixEffectiveness.EFFECTIVE
        elif success_rate >= 0.4:
            strategy.effectiveness = FixEffectiveness.PARTIALLY_EFFECTIVE
        else:
            strategy.effectiveness = FixEffectiveness.INEFFECTIVE
    
    def _extract_new_strategy(
        self,
        issue: Dict[str, Any],
        fix: Dict[str, Any],
        outcome: Dict[str, Any]
    ) -> Optional[FixStrategy]:
        if not outcome.get("success"):
            return None
        
        if not fix.get("is_new_approach"):
            return None
        
        issue_type = issue.get("type", "unknown")
        fix_steps = fix.get("steps", [])
        
        if not fix_steps:
            return None
        
        strategy_id = f"FS-LEARNED-{hashlib.md5(f'{issue_type}{fix_steps}'.encode()).hexdigest()[:8]}"
        
        if strategy_id in self._strategies:
            return None
        
        return FixStrategy(
            strategy_id=strategy_id,
            strategy_type=FixStrategyType(fix.get("strategy_type", "direct_fix")),
            name=f"学习策略: {issue_type}",
            description=f"从修复记录中学习的策略",
            issue_patterns=[issue_type],
            fix_steps=[{"step": i+1, "action": step} for i, step in enumerate(fix_steps)],
            prerequisites=fix.get("prerequisites", []),
            risks=fix.get("risks", []),
            effectiveness=FixEffectiveness.EFFECTIVE,
            tags=["learned", issue_type],
            metadata={
                "learned_from": issue.get("source", "unknown"),
                "learned_at": datetime.now().isoformat()
            }
        )
    
    def get_strategy_for_issue(
        self,
        issue_type: str,
        issue_description: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[FixStrategy]:
        candidates = []
        
        for strategy in self._strategies.values():
            match_score = self._calculate_issue_match(strategy, issue_type, issue_description)
            if match_score > 0:
                candidates.append((strategy, match_score))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def _calculate_issue_match(
        self,
        strategy: FixStrategy,
        issue_type: str,
        issue_description: Optional[str]
    ) -> float:
        score = 0.0
        
        for pattern in strategy.issue_patterns:
            if pattern.lower() in issue_type.lower():
                score += 0.5
                break
        
        if issue_description:
            for pattern in strategy.issue_patterns:
                if pattern.lower() in issue_description.lower():
                    score += 0.3
                    break
        
        effectiveness_scores = {
            FixEffectiveness.HIGHLY_EFFECTIVE: 0.2,
            FixEffectiveness.EFFECTIVE: 0.15,
            FixEffectiveness.PARTIALLY_EFFECTIVE: 0.1,
            FixEffectiveness.INEFFECTIVE: 0.0
        }
        score += effectiveness_scores.get(strategy.effectiveness, 0.1)
        
        if strategy.application_count > 0:
            success_rate = strategy.success_count / strategy.application_count
            score += success_rate * 0.1
        
        return min(score, 1.0)
    
    def evaluate_strategy(
        self,
        strategy_id: str,
        recent_count: int = 50
    ) -> Optional[StrategyEvaluation]:
        strategy = self._strategies.get(strategy_id)
        if not strategy:
            return None
        
        related_records = [
            r for r in self._fix_records
            if r.strategy_used == strategy_id
        ][-recent_count:]
        
        if not related_records:
            return StrategyEvaluation(
                strategy_id=strategy_id,
                total_applications=0,
                success_rate=0.0,
                average_time=0.0,
                effectiveness_score=0.0,
                trend="no_data",
                recommendations=["需要更多应用数据"]
            )
        
        success_count = sum(1 for r in related_records if r.success)
        success_rate = success_count / len(related_records)
        average_time = sum(r.time_taken for r in related_records) / len(related_records)
        
        effectiveness_score = self._calculate_effectiveness_score(
            success_rate, average_time, len(related_records)
        )
        
        trend = self._calculate_trend(related_records)
        
        recommendations = self._generate_strategy_recommendations(
            strategy, success_rate, average_time, trend
        )
        
        return StrategyEvaluation(
            strategy_id=strategy_id,
            total_applications=len(related_records),
            success_rate=success_rate,
            average_time=average_time,
            effectiveness_score=effectiveness_score,
            trend=trend,
            recommendations=recommendations,
            metrics={
                "success_rate": success_rate,
                "average_time": average_time,
                "application_count": len(related_records)
            }
        )
    
    def _calculate_effectiveness_score(
        self,
        success_rate: float,
        average_time: float,
        application_count: int
    ) -> float:
        score = success_rate * 0.6
        
        if average_time > 0:
            time_score = max(0, 1 - average_time / 60)
            score += time_score * 0.2
        
        count_score = min(application_count / 20, 1.0)
        score += count_score * 0.2
        
        return min(score, 1.0)
    
    def _calculate_trend(self, records: List[FixRecord]) -> str:
        if len(records) < 5:
            return "insufficient_data"
        
        mid = len(records) // 2
        early_success = sum(1 for r in records[:mid] if r.success) / mid
        late_success = sum(1 for r in records[mid:] if r.success) / (len(records) - mid)
        
        if late_success > early_success + 0.1:
            return "improving"
        elif late_success < early_success - 0.1:
            return "declining"
        else:
            return "stable"
    
    def _generate_strategy_recommendations(
        self,
        strategy: FixStrategy,
        success_rate: float,
        average_time: float,
        trend: str
    ) -> List[str]:
        recommendations = []
        
        if success_rate < 0.5:
            recommendations.append("成功率较低，建议重新评估策略有效性")
        
        if average_time > 30:
            recommendations.append("修复时间较长，考虑优化修复步骤")
        
        if trend == "declining":
            recommendations.append("成功率呈下降趋势，需要分析原因")
        
        if strategy.effectiveness == FixEffectiveness.INEFFECTIVE:
            recommendations.append("策略效果不佳，建议废弃或重构")
        
        if not recommendations:
            recommendations.append("策略表现良好，建议继续使用")
        
        return recommendations
    
    def optimize_strategies(self) -> Dict[str, Any]:
        optimizations = {
            "deprecated": [],
            "promoted": [],
            "merged": [],
            "improved": []
        }
        
        for strategy in list(self._strategies.values()):
            if strategy.application_count >= 10 and strategy.success_count / strategy.application_count < 0.3:
                strategy.effectiveness = FixEffectiveness.INEFFECTIVE
                optimizations["deprecated"].append(strategy.strategy_id)
            
            elif strategy.application_count >= 5 and strategy.success_count / strategy.application_count >= 0.8:
                if strategy.effectiveness != FixEffectiveness.HIGHLY_EFFECTIVE:
                    strategy.effectiveness = FixEffectiveness.HIGHLY_EFFECTIVE
                    optimizations["promoted"].append(strategy.strategy_id)
        
        similar_pairs = self._find_similar_strategies()
        for s1_id, s2_id in similar_pairs:
            if s1_id in self._strategies and s2_id in self._strategies:
                merged = self._merge_strategies(
                    self._strategies[s1_id],
                    self._strategies[s2_id]
                )
                if merged:
                    self._strategies[merged.strategy_id] = merged
                    optimizations["merged"].append((s1_id, s2_id, merged.strategy_id))
        
        self._save_data()
        
        return optimizations
    
    def _find_similar_strategies(self) -> List[Tuple[str, str]]:
        similar = []
        strategies = list(self._strategies.values())
        
        for i, s1 in enumerate(strategies):
            for s2 in strategies[i+1:]:
                if self._are_strategies_similar(s1, s2):
                    similar.append((s1.strategy_id, s2.strategy_id))
        
        return similar
    
    def _are_strategies_similar(
        self,
        s1: FixStrategy,
        s2: FixStrategy
    ) -> bool:
        if s1.strategy_type != s2.strategy_type:
            return False
        
        patterns1 = set(s1.issue_patterns)
        patterns2 = set(s2.issue_patterns)
        overlap = len(patterns1 & patterns2)
        
        return overlap >= min(len(patterns1), len(patterns2)) * 0.5
    
    def _merge_strategies(
        self,
        s1: FixStrategy,
        s2: FixStrategy
    ) -> Optional[FixStrategy]:
        merged_id = f"FS-MERGED-{hashlib.md5(f'{s1.strategy_id}{s2.strategy_id}'.encode()).hexdigest()[:8]}"
        
        merged_patterns = list(set(s1.issue_patterns + s2.issue_patterns))
        merged_tags = list(set(s1.tags + s2.tags))
        
        total_applications = s1.application_count + s2.application_count
        total_successes = s1.success_count + s2.success_count
        
        return FixStrategy(
            strategy_id=merged_id,
            strategy_type=s1.strategy_type,
            name=f"合并策略: {s1.name[:20]} & {s2.name[:20]}",
            description=f"合并自 {s1.strategy_id} 和 {s2.strategy_id}",
            issue_patterns=merged_patterns,
            fix_steps=s1.fix_steps if len(s1.fix_steps) >= len(s2.fix_steps) else s2.fix_steps,
            prerequisites=list(set(s1.prerequisites + s2.prerequisites)),
            risks=list(set(s1.risks + s2.risks)),
            effectiveness=s1.effectiveness if s1.success_count > s2.success_count else s2.effectiveness,
            application_count=total_applications,
            success_count=total_successes,
            average_time=(s1.average_time + s2.average_time) / 2,
            tags=merged_tags,
            metadata={"merged_from": [s1.strategy_id, s2.strategy_id]}
        )
    
    def add_strategy(self, strategy: FixStrategy) -> str:
        if not strategy.strategy_id:
            strategy.strategy_id = f"FS-CUSTOM-{hashlib.md5(strategy.name.encode()).hexdigest()[:8]}"
        
        self._strategies[strategy.strategy_id] = strategy
        self._index_strategy(strategy)
        self._save_data()
        
        logger.info(f"添加修复策略: {strategy.strategy_id} - {strategy.name}")
        return strategy.strategy_id
    
    def get_strategy(self, strategy_id: str) -> Optional[FixStrategy]:
        return self._strategies.get(strategy_id)
    
    def find_strategies(
        self,
        strategy_type: Optional[FixStrategyType] = None,
        effectiveness: Optional[FixEffectiveness] = None,
        tags: Optional[List[str]] = None
    ) -> List[FixStrategy]:
        results = []
        
        for strategy in self._strategies.values():
            if strategy_type and strategy.strategy_type != strategy_type:
                continue
            
            if effectiveness and strategy.effectiveness != effectiveness:
                continue
            
            if tags and not any(tag in strategy.tags for tag in tags):
                continue
            
            results.append(strategy)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = defaultdict(int)
        by_effectiveness: Dict[str, int] = defaultdict(int)
        
        for strategy in self._strategies.values():
            by_type[strategy.strategy_type.value] += 1
            by_effectiveness[strategy.effectiveness.value] += 1
        
        total_applications = sum(s.application_count for s in self._strategies.values())
        total_successes = sum(s.success_count for s in self._strategies.values())
        
        return {
            "total_strategies": len(self._strategies),
            "total_fix_records": len(self._fix_records),
            "by_type": dict(by_type),
            "by_effectiveness": dict(by_effectiveness),
            "total_applications": total_applications,
            "overall_success_rate": total_successes / total_applications if total_applications > 0 else 0
        }
    
    def export_strategies(self, output_path: str) -> None:
        data = {
            "exported_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "strategies": [s.to_dict() for s in self._strategies.values()]
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"修复策略已导出到: {output_path}")


class KnowledgeQualityEvaluator:
    """知识质量评估器
    
    负责评估知识库中知识的质量，支持有效性验证和淘汰机制。
    
    功能：
    - 知识质量评分：从多个维度评估知识质量
    - 知识有效性验证：验证知识是否仍然有效
    - 知识淘汰机制：识别和淘汰过时或低质量知识
    
    使用示例：
        evaluator = KnowledgeQualityEvaluator()
        
        # 评估知识质量
        quality = evaluator.evaluate_knowledge(knowledge_item)
        
        # 验证有效性
        validation = evaluator.validate_knowledge(knowledge_id)
        
        # 获取淘汰候选
        candidates = evaluator.get_retirement_candidates()
    """
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        storage_path: Optional[Path] = None
    ):
        self.knowledge_base = knowledge_base
        self.storage_path = storage_path or Path("./knowledge_quality_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._quality_scores: Dict[str, QualityScore] = {}
        self._validation_history: Dict[str, List[ValidationResult]] = defaultdict(list)
        self._retirement_candidates: List[RetirementCandidate] = []
        
        self._dimension_weights = {
            QualityDimension.ACCURACY: 0.25,
            QualityDimension.RELEVANCE: 0.20,
            QualityDimension.COMPLETENESS: 0.20,
            QualityDimension.TIMELINESS: 0.15,
            QualityDimension.USABILITY: 0.10,
            QualityDimension.CONSISTENCY: 0.10
        }
        
        self._quality_thresholds = {
            QualityLevel.EXCELLENT: 0.85,
            QualityLevel.GOOD: 0.70,
            QualityLevel.FAIR: 0.50,
            QualityLevel.POOR: 0.0
        }
        
        self._load_data()
    
    def _load_data(self) -> None:
        scores_file = self.storage_path / "quality_scores.json"
        
        if scores_file.exists():
            try:
                with open(scores_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for kid, score_data in data.get("scores", {}).items():
                    self._quality_scores[kid] = QualityScore(
                        overall_score=score_data.get("overall_score", 0.0),
                        level=QualityLevel(score_data.get("level", "fair")),
                        dimension_scores=score_data.get("dimension_scores", {}),
                        strengths=score_data.get("strengths", []),
                        weaknesses=score_data.get("weaknesses", []),
                        recommendations=score_data.get("recommendations", [])
                    )
                
                logger.info(f"加载质量评分: {len(self._quality_scores)} 条")
            except Exception as e:
                logger.warning(f"加载质量评分失败: {e}")
    
    def _save_data(self) -> None:
        scores_file = self.storage_path / "quality_scores.json"
        
        try:
            data = {
                "scores": {
                    kid: score.to_dict()
                    for kid, score in self._quality_scores.items()
                }
            }
            with open(scores_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存质量评分失败: {e}")
    
    def evaluate_knowledge(
        self,
        knowledge: KnowledgeItem,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        dimension_scores = {}
        
        dimension_scores[QualityDimension.ACCURACY.value] = self._evaluate_accuracy(knowledge)
        dimension_scores[QualityDimension.RELEVANCE.value] = self._evaluate_relevance(knowledge, context)
        dimension_scores[QualityDimension.COMPLETENESS.value] = self._evaluate_completeness(knowledge)
        dimension_scores[QualityDimension.TIMELINESS.value] = self._evaluate_timeliness(knowledge)
        dimension_scores[QualityDimension.USABILITY.value] = self._evaluate_usability(knowledge)
        dimension_scores[QualityDimension.CONSISTENCY.value] = self._evaluate_consistency(knowledge)
        
        overall_score = sum(
            dimension_scores[dim.value] * weight
            for dim, weight in self._dimension_weights.items()
        )
        
        level = self._determine_quality_level(overall_score)
        
        strengths = self._identify_strengths(dimension_scores)
        weaknesses = self._identify_weaknesses(dimension_scores)
        recommendations = self._generate_recommendations(dimension_scores, weaknesses)
        
        quality_score = QualityScore(
            overall_score=overall_score,
            level=level,
            dimension_scores=dimension_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
        
        self._quality_scores[knowledge.knowledge_id] = quality_score
        self._save_data()
        
        return quality_score
    
    def _evaluate_accuracy(self, knowledge: KnowledgeItem) -> float:
        score = 0.5
        
        if knowledge.success_rate > 0.8:
            score += 0.3
        elif knowledge.success_rate > 0.6:
            score += 0.2
        elif knowledge.success_rate > 0.4:
            score += 0.1
        
        if knowledge.confidence_score > 0.8:
            score += 0.2
        elif knowledge.confidence_score > 0.6:
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_relevance(
        self,
        knowledge: KnowledgeItem,
        context: Optional[Dict[str, Any]]
    ) -> float:
        score = 0.5
        
        if knowledge.usage_count > 50:
            score += 0.2
        elif knowledge.usage_count > 20:
            score += 0.1
        
        if context:
            context_tags = set(context.get("tags", []))
            knowledge_tags = set(knowledge.tags)
            if context_tags & knowledge_tags:
                score += 0.2
        
        if knowledge.status == KnowledgeStatus.ACTIVE:
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_completeness(self, knowledge: KnowledgeItem) -> float:
        score = 0.0
        
        if knowledge.title:
            score += 0.15
        if knowledge.content and len(knowledge.content) > 50:
            score += 0.25
        if knowledge.tags:
            score += 0.15
        if knowledge.category:
            score += 0.10
        if knowledge.examples:
            score += 0.15
        if knowledge.metadata:
            score += 0.10
        if knowledge.related_ids:
            score += 0.10
        
        return min(score, 1.0)
    
    def _evaluate_timeliness(self, knowledge: KnowledgeItem) -> float:
        score = 0.5
        
        try:
            if knowledge.updated_at:
                updated = datetime.fromisoformat(knowledge.updated_at)
                days_since_update = (datetime.now() - updated).days
                
                if days_since_update < 30:
                    score += 0.4
                elif days_since_update < 90:
                    score += 0.3
                elif days_since_update < 180:
                    score += 0.2
                elif days_since_update < 365:
                    score += 0.1
        except (ValueError, TypeError):
            pass
        
        return min(score, 1.0)
    
    def _evaluate_usability(self, knowledge: KnowledgeItem) -> float:
        score = 0.5
        
        if knowledge.examples:
            score += 0.2
        
        if knowledge.content:
            readability = self._calculate_readability(knowledge.content)
            score += readability * 0.2
        
        if knowledge.metadata.get("instructions"):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_readability(self, text: str) -> float:
        if not text:
            return 0.0
        
        sentences = text.count('.') + text.count('!') + text.count('?')
        words = len(text.split())
        
        if sentences == 0:
            sentences = 1
        
        avg_words_per_sentence = words / sentences
        
        if avg_words_per_sentence < 15:
            return 1.0
        elif avg_words_per_sentence < 25:
            return 0.8
        elif avg_words_per_sentence < 35:
            return 0.6
        else:
            return 0.4
    
    def _evaluate_consistency(self, knowledge: KnowledgeItem) -> float:
        score = 0.7
        
        if knowledge.tags:
            tag_consistency = all(
                tag.islower() or tag.isupper() or tag.istitle()
                for tag in knowledge.tags
            )
            if tag_consistency:
                score += 0.1
        
        if knowledge.title and knowledge.content:
            title_words = set(knowledge.title.lower().split())
            content_words = set(knowledge.content.lower().split()[:100])
            if title_words & content_words:
                score += 0.1
        
        if knowledge.category and knowledge.knowledge_type:
            score += 0.1
        
        return min(score, 1.0)
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        if score >= self._quality_thresholds[QualityLevel.EXCELLENT]:
            return QualityLevel.EXCELLENT
        elif score >= self._quality_thresholds[QualityLevel.GOOD]:
            return QualityLevel.GOOD
        elif score >= self._quality_thresholds[QualityLevel.FAIR]:
            return QualityLevel.FAIR
        else:
            return QualityLevel.POOR
    
    def _identify_strengths(
        self,
        dimension_scores: Dict[str, float]
    ) -> List[str]:
        strengths = []
        
        for dim, score in dimension_scores.items():
            if score >= 0.8:
                strengths.append(f"{dim}表现优秀 ({score:.0%})")
        
        return strengths
    
    def _identify_weaknesses(
        self,
        dimension_scores: Dict[str, float]
    ) -> List[str]:
        weaknesses = []
        
        for dim, score in dimension_scores.items():
            if score < 0.5:
                weaknesses.append(f"{dim}需要改进 ({score:.0%})")
        
        return weaknesses
    
    def _generate_recommendations(
        self,
        dimension_scores: Dict[str, float],
        weaknesses: List[str]
    ) -> List[str]:
        recommendations = []
        
        if dimension_scores.get(QualityDimension.COMPLETENESS.value, 0) < 0.6:
            recommendations.append("添加更多示例和详细说明")
        
        if dimension_scores.get(QualityDimension.TIMELINESS.value, 0) < 0.6:
            recommendations.append("更新知识内容以保持时效性")
        
        if dimension_scores.get(QualityDimension.USABILITY.value, 0) < 0.6:
            recommendations.append("改进知识结构和可读性")
        
        if dimension_scores.get(QualityDimension.ACCURACY.value, 0) < 0.6:
            recommendations.append("验证知识准确性并更新")
        
        if not recommendations:
            recommendations.append("知识质量良好，建议持续监控")
        
        return recommendations
    
    def validate_knowledge(
        self,
        knowledge_id: str,
        validation_tests: Optional[List[Dict[str, Any]]] = None
    ) -> ValidationResult:
        if not self.knowledge_base:
            return ValidationResult(
                is_valid=False,
                validation_score=0.0,
                issues=["知识库未配置"],
                warnings=[],
                suggestions=[],
                checked_aspects=[]
            )
        
        knowledge = self.knowledge_base.get_knowledge(knowledge_id)
        if not knowledge:
            return ValidationResult(
                is_valid=False,
                validation_score=0.0,
                issues=["知识不存在"],
                warnings=[],
                suggestions=[],
                checked_aspects=[]
            )
        
        issues = []
        warnings = []
        suggestions = []
        checked_aspects = []
        
        is_syntax_valid = self._validate_syntax(knowledge)
        checked_aspects.append("syntax")
        if not is_syntax_valid:
            issues.append("语法验证失败")
        
        is_content_valid = self._validate_content(knowledge)
        checked_aspects.append("content")
        if not is_content_valid:
            warnings.append("内容验证有警告")
        
        is_metadata_valid = self._validate_metadata(knowledge)
        checked_aspects.append("metadata")
        if not is_metadata_valid:
            warnings.append("元数据不完整")
        
        if validation_tests:
            for test in validation_tests:
                test_result = self._run_validation_test(knowledge, test)
                checked_aspects.append(test.get("name", "unknown_test"))
                if not test_result.get("passed"):
                    issues.append(test_result.get("message", "测试失败"))
        
        validation_score = self._calculate_validation_score(
            len(issues), len(warnings), len(checked_aspects)
        )
        
        is_valid = len(issues) == 0
        
        if not is_valid:
            suggestions.append("修复验证失败的问题")
        if warnings:
            suggestions.append("关注警告事项")
        
        result = ValidationResult(
            is_valid=is_valid,
            validation_score=validation_score,
            issues=issues,
            warnings=warnings,
            suggestions=suggestions,
            checked_aspects=checked_aspects
        )
        
        self._validation_history[knowledge_id].append(result)
        
        return result
    
    def _validate_syntax(self, knowledge: KnowledgeItem) -> bool:
        if not knowledge.content:
            return False
        
        if knowledge.knowledge_type == KnowledgeType.CODE_PATTERN:
            try:
                compile(knowledge.content, '<string>', 'exec')
            except SyntaxError:
                return False
        
        return True
    
    def _validate_content(self, knowledge: KnowledgeItem) -> bool:
        if not knowledge.title or len(knowledge.title) < 3:
            return False
        
        if not knowledge.content or len(knowledge.content) < 10:
            return False
        
        return True
    
    def _validate_metadata(self, knowledge: KnowledgeItem) -> bool:
        if not knowledge.tags:
            return False
        
        if not knowledge.category:
            return False
        
        return True
    
    def _run_validation_test(
        self,
        knowledge: KnowledgeItem,
        test: Dict[str, Any]
    ) -> Dict[str, Any]:
        test_type = test.get("type", "unknown")
        
        if test_type == "keyword_check":
            keywords = test.get("keywords", [])
            content_lower = knowledge.content.lower()
            found = any(kw.lower() in content_lower for kw in keywords)
            return {
                "passed": found,
                "message": "关键词检查" + ("通过" if found else "未通过")
            }
        
        elif test_type == "length_check":
            min_length = test.get("min_length", 0)
            max_length = test.get("max_length", float('inf'))
            length = len(knowledge.content)
            passed = min_length <= length <= max_length
            return {
                "passed": passed,
                "message": f"长度检查: {length} (范围: {min_length}-{max_length})"
            }
        
        return {"passed": True, "message": "未知测试类型，默认通过"}
    
    def _calculate_validation_score(
        self,
        issue_count: int,
        warning_count: int,
        checked_count: int
    ) -> float:
        if checked_count == 0:
            return 0.0
        
        base_score = 1.0
        base_score -= issue_count * 0.2
        base_score -= warning_count * 0.1
        
        return max(0.0, min(base_score, 1.0))
    
    def get_retirement_candidates(
        self,
        threshold_days: int = 365,
        min_quality_score: float = 0.4,
        max_usage_count: int = 5
    ) -> List[RetirementCandidate]:
        candidates = []
        
        if not self.knowledge_base:
            return candidates
        
        all_knowledge = self.knowledge_base.list_knowledge(limit=10000)
        
        for knowledge in all_knowledge:
            quality_score = self._quality_scores.get(knowledge.knowledge_id)
            overall_score = quality_score.overall_score if quality_score else 0.5
            
            is_old = False
            try:
                if knowledge.updated_at:
                    updated = datetime.fromisoformat(knowledge.updated_at)
                    days_since_update = (datetime.now() - updated).days
                    is_old = days_since_update > threshold_days
            except (ValueError, TypeError):
                is_old = True
            
            is_low_quality = overall_score < min_quality_score
            is_unused = knowledge.usage_count < max_usage_count
            
            if is_old or is_low_quality or is_unused:
                reason = self._determine_retirement_reason(
                    is_old, is_low_quality, is_unused
                )
                
                usage_trend = self._calculate_usage_trend(knowledge)
                
                recommendation = self._generate_retirement_recommendation(
                    is_old, is_low_quality, is_unused, overall_score
                )
                
                candidate = RetirementCandidate(
                    knowledge_id=knowledge.knowledge_id,
                    retirement_reason=reason,
                    quality_score=overall_score,
                    last_used=knowledge.updated_at or "",
                    usage_trend=usage_trend,
                    recommendation=recommendation,
                    metadata={
                        "usage_count": knowledge.usage_count,
                        "success_rate": knowledge.success_rate,
                        "days_since_update": days_since_update if is_old else 0
                    }
                )
                candidates.append(candidate)
        
        self._retirement_candidates = candidates
        
        return candidates
    
    def _determine_retirement_reason(
        self,
        is_old: bool,
        is_low_quality: bool,
        is_unused: bool
    ) -> str:
        reasons = []
        if is_old:
            reasons.append("过时")
        if is_low_quality:
            reasons.append("质量低")
        if is_unused:
            reasons.append("使用率低")
        
        return "、".join(reasons) if reasons else "未知原因"
    
    def _calculate_usage_trend(self, knowledge: KnowledgeItem) -> str:
        if knowledge.usage_count == 0:
            return "never_used"
        elif knowledge.usage_count < 5:
            return "rarely_used"
        elif knowledge.usage_count < 20:
            return "occasionally_used"
        else:
            return "frequently_used"
    
    def _generate_retirement_recommendation(
        self,
        is_old: bool,
        is_low_quality: bool,
        is_unused: bool,
        quality_score: float
    ) -> str:
        if quality_score < 0.3:
            return "建议立即淘汰"
        elif is_old and is_unused:
            return "建议归档或淘汰"
        elif is_low_quality:
            return "建议改进或淘汰"
        elif is_unused:
            return "建议评估后决定"
        else:
            return "建议保留但需更新"
    
    def retire_knowledge(
        self,
        knowledge_id: str,
        reason: str = ""
    ) -> bool:
        if not self.knowledge_base:
            return False
        
        result = self.knowledge_base.update_knowledge(
            knowledge_id,
            {
                "status": KnowledgeStatus.ARCHIVED,
                "metadata": {
                    "retired_at": datetime.now().isoformat(),
                    "retirement_reason": reason
                }
            }
        )
        
        if result:
            logger.info(f"知识已淘汰: {knowledge_id}")
        
        return result is not None
    
    def batch_retire(
        self,
        knowledge_ids: List[str],
        reason: str = ""
    ) -> Dict[str, bool]:
        results = {}
        
        for kid in knowledge_ids:
            results[kid] = self.retire_knowledge(kid, reason)
        
        return results
    
    def get_quality_score(self, knowledge_id: str) -> Optional[QualityScore]:
        return self._quality_scores.get(knowledge_id)
    
    def get_validation_history(
        self,
        knowledge_id: str,
        limit: int = 10
    ) -> List[ValidationResult]:
        return self._validation_history.get(knowledge_id, [])[-limit:]
    
    def evaluate_all(self) -> Dict[str, Any]:
        if not self.knowledge_base:
            return {"error": "知识库未配置"}
        
        all_knowledge = self.knowledge_base.list_knowledge(limit=10000)
        
        for knowledge in all_knowledge:
            self.evaluate_knowledge(knowledge)
        
        level_counts: Dict[str, int] = defaultdict(int)
        for score in self._quality_scores.values():
            level_counts[score.level.value] += 1
        
        avg_score = (
            sum(s.overall_score for s in self._quality_scores.values())
            / len(self._quality_scores)
            if self._quality_scores else 0
        )
        
        return {
            "total_evaluated": len(self._quality_scores),
            "by_level": dict(level_counts),
            "average_score": avg_score,
            "retirement_candidates": len(self._retirement_candidates)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        level_counts: Dict[str, int] = defaultdict(int)
        dimension_averages: Dict[str, float] = defaultdict(float)
        
        for score in self._quality_scores.values():
            level_counts[score.level.value] += 1
            for dim, value in score.dimension_scores.items():
                dimension_averages[dim] += value
        
        if self._quality_scores:
            for dim in dimension_averages:
                dimension_averages[dim] /= len(self._quality_scores)
        
        return {
            "total_evaluated": len(self._quality_scores),
            "by_level": dict(level_counts),
            "dimension_averages": dict(dimension_averages),
            "validation_history_count": sum(len(h) for h in self._validation_history.values()),
            "retirement_candidates_count": len(self._retirement_candidates)
        }
    
    def export_evaluation(self, output_path: str) -> None:
        data = {
            "exported_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "quality_scores": {
                kid: score.to_dict()
                for kid, score in self._quality_scores.items()
            },
            "retirement_candidates": [
                c.to_dict() for c in self._retirement_candidates
            ]
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"质量评估已导出到: {output_path}")


class FailureSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FailureCategory(Enum):
    SYNTAX_ERROR = "syntax_error"
    LOGIC_ERROR = "logic_error"
    RUNTIME_ERROR = "runtime_error"
    PERFORMANCE_ERROR = "performance_error"
    SECURITY_ERROR = "security_error"
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_ERROR = "dependency_error"
    INTEGRATION_ERROR = "integration_error"


@dataclass
class FailurePattern:
    pattern_id: str
    category: FailureCategory
    severity: FailureSeverity
    name: str
    description: str
    root_cause: str
    symptoms: List[str] = field(default_factory=list)
    fix_methods: List[Dict[str, Any]] = field(default_factory=list)
    prevention_tips: List[str] = field(default_factory=list)
    occurrence_count: int = 0
    fix_success_rate: float = 0.0
    avg_fix_time: float = 0.0
    related_patterns: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    examples: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "name": self.name,
            "description": self.description,
            "root_cause": self.root_cause,
            "symptoms": self.symptoms,
            "fix_methods": self.fix_methods,
            "prevention_tips": self.prevention_tips,
            "occurrence_count": self.occurrence_count,
            "fix_success_rate": self.fix_success_rate,
            "avg_fix_time": self.avg_fix_time,
            "related_patterns": self.related_patterns,
            "tags": self.tags,
            "examples": self.examples,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailurePattern":
        return cls(
            pattern_id=data.get("pattern_id", ""),
            category=FailureCategory(data.get("category", "logic_error")),
            severity=FailureSeverity(data.get("severity", "medium")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            root_cause=data.get("root_cause", ""),
            symptoms=data.get("symptoms", []),
            fix_methods=data.get("fix_methods", []),
            prevention_tips=data.get("prevention_tips", []),
            occurrence_count=data.get("occurrence_count", 0),
            fix_success_rate=data.get("fix_success_rate", 0.0),
            avg_fix_time=data.get("avg_fix_time", 0.0),
            related_patterns=data.get("related_patterns", []),
            tags=data.get("tags", []),
            examples=data.get("examples", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class FailureRecord:
    record_id: str
    pattern_id: str
    category: FailureCategory
    severity: FailureSeverity
    error_type: str
    error_message: str
    error_location: str
    root_cause_analysis: str
    fix_method: str
    fix_description: str
    fix_time: float
    fix_success: bool
    side_effects: List[str] = field(default_factory=list)
    lessons_learned: str = ""
    timestamp: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "pattern_id": self.pattern_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "error_location": self.error_location,
            "root_cause_analysis": self.root_cause_analysis,
            "fix_method": self.fix_method,
            "fix_description": self.fix_description,
            "fix_time": self.fix_time,
            "fix_success": self.fix_success,
            "side_effects": self.side_effects,
            "lessons_learned": self.lessons_learned,
            "timestamp": self.timestamp,
            "context": self.context
        }


class FailurePatternLearner:
    """失败模式学习器
    
    负责从失败案例中学习模式，记录失败原因和修复方法。
    
    功能：
    - 失败模式识别：识别和分类失败模式
    - 根因分析：分析失败的根本原因
    - 修复方法学习：学习有效的修复方法
    - 预防建议：生成预防类似失败的建议
    
    使用示例：
        learner = FailurePatternLearner()
        
        # 记录失败
        learner.record_failure(error_info, fix_info)
        
        # 获取失败模式
        pattern = learner.get_failure_pattern(error_type)
        
        # 获取预防建议
        tips = learner.get_prevention_tips(category)
    """
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        storage_path: Optional[Path] = None
    ):
        self.knowledge_base = knowledge_base
        self.storage_path = storage_path or Path("./failure_pattern_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._patterns: Dict[str, FailurePattern] = {}
        self._records: List[FailureRecord] = []
        self._pattern_index: Dict[str, List[str]] = defaultdict(list)
        
        self._initialize_default_patterns()
        self._load_data()
    
    def _initialize_default_patterns(self) -> None:
        default_patterns = [
            FailurePattern(
                pattern_id="FP-NULL-001",
                category=FailureCategory.RUNTIME_ERROR,
                severity=FailureSeverity.HIGH,
                name="空指针异常",
                description="访问空对象或未初始化的变量",
                root_cause="未进行空值检查或初始化",
                symptoms=["NullPointerException", "NoneType", "AttributeError"],
                fix_methods=[
                    {
                        "method": "添加空值检查",
                        "description": "在访问对象前检查是否为空",
                        "success_rate": 0.95
                    },
                    {
                        "method": "使用默认值",
                        "description": "提供合理的默认值避免空值",
                        "success_rate": 0.85
                    }
                ],
                prevention_tips=[
                    "使用类型提示明确可能为空的变量",
                    "采用防御性编程",
                    "使用Optional类型"
                ],
                tags=["null", "runtime", "common"]
            ),
            FailurePattern(
                pattern_id="FP-TYPE-001",
                category=FailureCategory.RUNTIME_ERROR,
                severity=FailureSeverity.MEDIUM,
                name="类型错误",
                description="操作或函数接收到错误类型的参数",
                root_cause="类型不匹配或缺少类型检查",
                symptoms=["TypeError", "type error", "unsupported operand"],
                fix_methods=[
                    {
                        "method": "添加类型转换",
                        "description": "将参数转换为期望的类型",
                        "success_rate": 0.90
                    },
                    {
                        "method": "添加类型检查",
                        "description": "验证参数类型并处理异常",
                        "success_rate": 0.85
                    }
                ],
                prevention_tips=[
                    "使用类型提示",
                    "编写单元测试验证类型",
                    "使用静态类型检查工具"
                ],
                tags=["type", "runtime", "common"]
            ),
            FailurePattern(
                pattern_id="FP-INDEX-001",
                category=FailureCategory.LOGIC_ERROR,
                severity=FailureSeverity.MEDIUM,
                name="索引越界",
                description="访问数组或列表时索引超出范围",
                root_cause="未验证索引范围",
                symptoms=["IndexError", "ArrayIndexOutOfBoundsException", "out of range"],
                fix_methods=[
                    {
                        "method": "添加边界检查",
                        "description": "访问前检查索引是否在有效范围内",
                        "success_rate": 0.95
                    },
                    {
                        "method": "使用安全访问方法",
                        "description": "使用get()等安全访问方法",
                        "success_rate": 0.90
                    }
                ],
                prevention_tips=[
                    "使用迭代器而非索引",
                    "添加边界断言",
                    "使用更安全的容器方法"
                ],
                tags=["index", "logic", "common"]
            ),
            FailurePattern(
                pattern_id="FP-DEP-001",
                category=FailureCategory.DEPENDENCY_ERROR,
                severity=FailureSeverity.HIGH,
                name="依赖缺失",
                description="缺少必需的依赖包或模块",
                root_cause="依赖未安装或版本不兼容",
                symptoms=["ModuleNotFoundError", "ImportError", "dependency not found"],
                fix_methods=[
                    {
                        "method": "安装依赖",
                        "description": "使用包管理器安装缺失的依赖",
                        "success_rate": 0.95
                    },
                    {
                        "method": "更新依赖版本",
                        "description": "调整依赖版本以解决兼容性问题",
                        "success_rate": 0.80
                    }
                ],
                prevention_tips=[
                    "维护完整的依赖清单",
                    "使用虚拟环境",
                    "定期更新和测试依赖"
                ],
                tags=["dependency", "import", "environment"]
            ),
            FailurePattern(
                pattern_id="FP-SYNTAX-001",
                category=FailureCategory.SYNTAX_ERROR,
                severity=FailureSeverity.LOW,
                name="语法错误",
                description="代码不符合语言语法规范",
                root_cause="拼写错误、缺少符号或格式错误",
                symptoms=["SyntaxError", "IndentationError", "ParseError"],
                fix_methods=[
                    {
                        "method": "修正语法",
                        "description": "根据错误提示修正语法问题",
                        "success_rate": 0.99
                    }
                ],
                prevention_tips=[
                    "使用IDE语法检查",
                    "配置代码格式化工具",
                    "编写代码时注意语法规范"
                ],
                tags=["syntax", "parsing", "common"]
            ),
            FailurePattern(
                pattern_id="FP-PERF-001",
                category=FailureCategory.PERFORMANCE_ERROR,
                severity=FailureSeverity.MEDIUM,
                name="性能瓶颈",
                description="代码执行效率低下导致超时或资源耗尽",
                root_cause="算法复杂度过高或资源使用不当",
                symptoms=["timeout", "slow", "memory leak", "high CPU"],
                fix_methods=[
                    {
                        "method": "优化算法",
                        "description": "使用更高效的算法或数据结构",
                        "success_rate": 0.85
                    },
                    {
                        "method": "缓存优化",
                        "description": "添加缓存减少重复计算",
                        "success_rate": 0.80
                    },
                    {
                        "method": "异步处理",
                        "description": "使用异步方式处理耗时操作",
                        "success_rate": 0.75
                    }
                ],
                prevention_tips=[
                    "进行性能测试",
                    "使用性能分析工具",
                    "遵循性能最佳实践"
                ],
                tags=["performance", "optimization", "timeout"]
            ),
            FailurePattern(
                pattern_id="FP-SEC-001",
                category=FailureCategory.SECURITY_ERROR,
                severity=FailureSeverity.CRITICAL,
                name="安全漏洞",
                description="代码存在安全隐患可能被攻击利用",
                root_cause="缺少安全检查或使用不安全的实践",
                symptoms=["SQL injection", "XSS", "CSRF", "vulnerability"],
                fix_methods=[
                    {
                        "method": "输入验证",
                        "description": "验证和清理所有外部输入",
                        "success_rate": 0.90
                    },
                    {
                        "method": "参数化查询",
                        "description": "使用参数化查询防止注入",
                        "success_rate": 0.95
                    },
                    {
                        "method": "权限检查",
                        "description": "添加适当的权限验证",
                        "success_rate": 0.85
                    }
                ],
                prevention_tips=[
                    "遵循安全编码规范",
                    "进行安全代码审查",
                    "使用安全扫描工具"
                ],
                tags=["security", "vulnerability", "critical"]
            )
        ]
        
        for pattern in default_patterns:
            self._patterns[pattern.pattern_id] = pattern
            self._index_pattern(pattern)
    
    def _index_pattern(self, pattern: FailurePattern) -> None:
        self._pattern_index["by_category"][pattern.category.value].append(pattern.pattern_id)
        self._pattern_index["by_severity"][pattern.severity.value].append(pattern.pattern_id)
        for tag in pattern.tags:
            self._pattern_index[f"by_tag_{tag}"].append(pattern.pattern_id)
        for symptom in pattern.symptoms:
            self._pattern_index[f"by_symptom_{symptom[:20]}"].append(pattern.pattern_id)
    
    def _load_data(self) -> None:
        patterns_file = self.storage_path / "failure_patterns.json"
        records_file = self.storage_path / "failure_records.json"
        
        if patterns_file.exists():
            try:
                with open(patterns_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for pattern_data in data.get("patterns", []):
                    pattern = FailurePattern.from_dict(pattern_data)
                    self._patterns[pattern.pattern_id] = pattern
                    self._index_pattern(pattern)
                
                logger.info(f"加载失败模式: {len(self._patterns)} 个")
            except Exception as e:
                logger.warning(f"加载失败模式失败: {e}")
        
        if records_file.exists():
            try:
                with open(records_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for record_data in data.get("records", []):
                    record = FailureRecord(
                        record_id=record_data.get("record_id", ""),
                        pattern_id=record_data.get("pattern_id", ""),
                        category=FailureCategory(record_data.get("category", "logic_error")),
                        severity=FailureSeverity(record_data.get("severity", "medium")),
                        error_type=record_data.get("error_type", ""),
                        error_message=record_data.get("error_message", ""),
                        error_location=record_data.get("error_location", ""),
                        root_cause_analysis=record_data.get("root_cause_analysis", ""),
                        fix_method=record_data.get("fix_method", ""),
                        fix_description=record_data.get("fix_description", ""),
                        fix_time=record_data.get("fix_time", 0.0),
                        fix_success=record_data.get("fix_success", False),
                        side_effects=record_data.get("side_effects", []),
                        lessons_learned=record_data.get("lessons_learned", ""),
                        timestamp=record_data.get("timestamp", ""),
                        context=record_data.get("context", {})
                    )
                    self._records.append(record)
                
                logger.info(f"加载失败记录: {len(self._records)} 条")
            except Exception as e:
                logger.warning(f"加载失败记录失败: {e}")
    
    def _save_data(self) -> None:
        patterns_file = self.storage_path / "failure_patterns.json"
        records_file = self.storage_path / "failure_records.json"
        
        try:
            with open(patterns_file, "w", encoding="utf-8") as f:
                json.dump({
                    "patterns": [p.to_dict() for p in self._patterns.values()]
                }, f, ensure_ascii=False, indent=2)
            
            with open(records_file, "w", encoding="utf-8") as f:
                json.dump({
                    "records": [r.to_dict() for r in self._records]
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存失败模式数据失败: {e}")
    
    def record_failure(
        self,
        error_info: Dict[str, Any],
        fix_info: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> FailurePattern:
        error_type = error_info.get("error_type", "unknown")
        error_message = error_info.get("error_message", "")
        error_location = error_info.get("error_location", "")
        
        pattern = self._identify_failure_pattern(error_type, error_message)
        
        record = FailureRecord(
            record_id=f"FR-{hashlib.md5(f'{error_type}{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}",
            pattern_id=pattern.pattern_id,
            category=pattern.category,
            severity=pattern.severity,
            error_type=error_type,
            error_message=error_message,
            error_location=error_location,
            root_cause_analysis=fix_info.get("root_cause", ""),
            fix_method=fix_info.get("method", ""),
            fix_description=fix_info.get("description", ""),
            fix_time=fix_info.get("time_taken", 0.0),
            fix_success=fix_info.get("success", False),
            side_effects=fix_info.get("side_effects", []),
            lessons_learned=fix_info.get("lessons_learned", ""),
            timestamp=datetime.now().isoformat(),
            context=context or {}
        )
        
        self._records.append(record)
        
        self._update_pattern_stats(pattern, fix_info)
        
        if fix_info.get("success") and fix_info.get("is_new_method"):
            self._add_fix_method(pattern, fix_info)
        
        self._save_data()
        
        return pattern
    
    def _identify_failure_pattern(
        self,
        error_type: str,
        error_message: str
    ) -> FailurePattern:
        for pattern in self._patterns.values():
            for symptom in pattern.symptoms:
                if symptom.lower() in error_type.lower() or symptom.lower() in error_message.lower():
                    return pattern
        
        return self._create_new_pattern(error_type, error_message)
    
    def _create_new_pattern(
        self,
        error_type: str,
        error_message: str
    ) -> FailurePattern:
        category = self._infer_category(error_type, error_message)
        severity = self._infer_severity(error_type, error_message)
        
        pattern = FailurePattern(
            pattern_id=f"FP-AUTO-{hashlib.md5(error_type.encode()).hexdigest()[:8]}",
            category=category,
            severity=severity,
            name=f"自动识别: {error_type}",
            description=f"从错误自动识别的模式: {error_message[:100]}",
            root_cause="待分析",
            symptoms=[error_type],
            tags=["auto_detected", error_type.lower()]
        )
        
        self._patterns[pattern.pattern_id] = pattern
        self._index_pattern(pattern)
        
        logger.info(f"创建新的失败模式: {pattern.pattern_id}")
        return pattern
    
    def _infer_category(self, error_type: str, error_message: str) -> FailureCategory:
        error_lower = f"{error_type} {error_message}".lower()
        
        if any(kw in error_lower for kw in ["syntax", "parse", "indent"]):
            return FailureCategory.SYNTAX_ERROR
        elif any(kw in error_lower for kw in ["null", "none", "pointer"]):
            return FailureCategory.RUNTIME_ERROR
        elif any(kw in error_lower for kw in ["type", "cast", "convert"]):
            return FailureCategory.RUNTIME_ERROR
        elif any(kw in error_lower for kw in ["index", "range", "bound"]):
            return FailureCategory.LOGIC_ERROR
        elif any(kw in error_lower for kw in ["import", "module", "dependency"]):
            return FailureCategory.DEPENDENCY_ERROR
        elif any(kw in error_lower for kw in ["timeout", "performance", "slow"]):
            return FailureCategory.PERFORMANCE_ERROR
        elif any(kw in error_lower for kw in ["security", "auth", "permission"]):
            return FailureCategory.SECURITY_ERROR
        else:
            return FailureCategory.LOGIC_ERROR
    
    def _infer_severity(self, error_type: str, error_message: str) -> FailureSeverity:
        error_lower = f"{error_type} {error_message}".lower()
        
        if any(kw in error_lower for kw in ["critical", "fatal", "security"]):
            return FailureSeverity.CRITICAL
        elif any(kw in error_lower for kw in ["error", "exception", "fail"]):
            return FailureSeverity.HIGH
        elif any(kw in error_lower for kw in ["warning", "deprecated"]):
            return FailureSeverity.MEDIUM
        else:
            return FailureSeverity.LOW
    
    def _update_pattern_stats(
        self,
        pattern: FailurePattern,
        fix_info: Dict[str, Any]
    ) -> None:
        pattern.occurrence_count += 1
        
        if fix_info.get("success"):
            current_successes = pattern.fix_success_rate * (pattern.occurrence_count - 1)
            pattern.fix_success_rate = (current_successes + 1) / pattern.occurrence_count
        else:
            current_successes = pattern.fix_success_rate * (pattern.occurrence_count - 1)
            pattern.fix_success_rate = current_successes / pattern.occurrence_count
        
        fix_time = fix_info.get("time_taken", 0.0)
        if pattern.occurrence_count > 1:
            pattern.avg_fix_time = (
                (pattern.avg_fix_time * (pattern.occurrence_count - 1) + fix_time)
                / pattern.occurrence_count
            )
        else:
            pattern.avg_fix_time = fix_time
    
    def _add_fix_method(
        self,
        pattern: FailurePattern,
        fix_info: Dict[str, Any]
    ) -> None:
        new_method = {
            "method": fix_info.get("method", "unknown"),
            "description": fix_info.get("description", ""),
            "success_rate": 1.0 if fix_info.get("success") else 0.0,
            "added_at": datetime.now().isoformat()
        }
        
        pattern.fix_methods.append(new_method)
        logger.info(f"为模式 {pattern.pattern_id} 添加新的修复方法")
    
    def get_failure_pattern(
        self,
        error_type: str,
        error_message: Optional[str] = None
    ) -> Optional[FailurePattern]:
        return self._identify_failure_pattern(error_type, error_message or "")
    
    def get_prevention_tips(
        self,
        category: Optional[FailureCategory] = None,
        tags: Optional[List[str]] = None
    ) -> List[str]:
        tips = []
        
        for pattern in self._patterns.values():
            if category and pattern.category != category:
                continue
            
            if tags and not any(tag in pattern.tags for tag in tags):
                continue
            
            tips.extend(pattern.prevention_tips)
        
        return list(set(tips))
    
    def get_fix_recommendations(
        self,
        error_type: str,
        error_message: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        pattern = self.get_failure_pattern(error_type, error_message)
        
        if not pattern:
            return []
        
        recommendations = []
        for method in pattern.fix_methods:
            recommendations.append({
                "method": method.get("method", ""),
                "description": method.get("description", ""),
                "success_rate": method.get("success_rate", 0.0),
                "pattern_id": pattern.pattern_id,
                "pattern_name": pattern.name
            })
        
        recommendations.sort(key=lambda x: x["success_rate"], reverse=True)
        return recommendations
    
    def analyze_failure_trends(
        self,
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        cutoff_time = datetime.now()
        
        recent_records = [
            r for r in self._records
            if self._is_within_time_window(r.timestamp, cutoff_time, time_window_days)
        ]
        
        by_category: Dict[str, int] = defaultdict(int)
        by_severity: Dict[str, int] = defaultdict(int)
        by_pattern: Dict[str, int] = defaultdict(int)
        
        for record in recent_records:
            by_category[record.category.value] += 1
            by_severity[record.severity.value] += 1
            by_pattern[record.pattern_id] += 1
        
        success_rate = (
            sum(1 for r in recent_records if r.fix_success) / len(recent_records)
            if recent_records else 0
        )
        
        avg_fix_time = (
            sum(r.fix_time for r in recent_records) / len(recent_records)
            if recent_records else 0
        )
        
        top_patterns = sorted(by_pattern.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_failures": len(recent_records),
            "by_category": dict(by_category),
            "by_severity": dict(by_severity),
            "success_rate": success_rate,
            "average_fix_time": avg_fix_time,
            "top_patterns": [
                {
                    "pattern_id": pid,
                    "count": count,
                    "pattern": self._patterns.get(pid, None).to_dict() if pid in self._patterns else None
                }
                for pid, count in top_patterns
            ]
        }
    
    def _is_within_time_window(
        self,
        timestamp_str: str,
        reference_time: datetime,
        window_days: int
    ) -> bool:
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            return (reference_time - timestamp).days <= window_days
        except (ValueError, TypeError):
            return False
    
    def add_pattern(self, pattern: FailurePattern) -> str:
        if not pattern.pattern_id:
            pattern.pattern_id = f"FP-CUSTOM-{hashlib.md5(pattern.name.encode()).hexdigest()[:8]}"
        
        self._patterns[pattern.pattern_id] = pattern
        self._index_pattern(pattern)
        self._save_data()
        
        logger.info(f"添加失败模式: {pattern.pattern_id} - {pattern.name}")
        return pattern.pattern_id
    
    def get_statistics(self) -> Dict[str, Any]:
        by_category: Dict[str, int] = defaultdict(int)
        by_severity: Dict[str, int] = defaultdict(int)
        
        for pattern in self._patterns.values():
            by_category[pattern.category.value] += 1
            by_severity[pattern.severity.value] += 1
        
        total_occurrences = sum(p.occurrence_count for p in self._patterns.values())
        avg_success_rate = (
            sum(p.fix_success_rate for p in self._patterns.values()) / len(self._patterns)
            if self._patterns else 0
        )
        
        return {
            "total_patterns": len(self._patterns),
            "total_records": len(self._records),
            "by_category": dict(by_category),
            "by_severity": dict(by_severity),
            "total_occurrences": total_occurrences,
            "average_fix_success_rate": avg_success_rate
        }


class SuccessQualityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"


@dataclass
class SuccessPattern:
    pattern_id: str
    name: str
    description: str
    quality_level: SuccessQualityLevel
    code_pattern: str
    context_requirements: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    success_cases: List[Dict[str, Any]] = field(default_factory=list)
    applicability: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    implementation_steps: List[Dict[str, str]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.0
    usage_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "description": self.description,
            "quality_level": self.quality_level.value,
            "code_pattern": self.code_pattern,
            "context_requirements": self.context_requirements,
            "benefits": self.benefits,
            "metrics": self.metrics,
            "success_cases": self.success_cases,
            "applicability": self.applicability,
            "prerequisites": self.prerequisites,
            "implementation_steps": self.implementation_steps,
            "tags": self.tags,
            "confidence": self.confidence,
            "usage_count": self.usage_count,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SuccessPattern":
        return cls(
            pattern_id=data.get("pattern_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            quality_level=SuccessQualityLevel(data.get("quality_level", "good")),
            code_pattern=data.get("code_pattern", ""),
            context_requirements=data.get("context_requirements", []),
            benefits=data.get("benefits", []),
            metrics=data.get("metrics", {}),
            success_cases=data.get("success_cases", []),
            applicability=data.get("applicability", []),
            prerequisites=data.get("prerequisites", []),
            implementation_steps=data.get("implementation_steps", []),
            tags=data.get("tags", []),
            confidence=data.get("confidence", 0.0),
            usage_count=data.get("usage_count", 0),
            metadata=data.get("metadata", {})
        )


@dataclass
class CodeQualityMetrics:
    readability: float
    maintainability: float
    performance: float
    security: float
    testability: float
    overall_score: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "readability": self.readability,
            "maintainability": self.maintainability,
            "performance": self.performance,
            "security": self.security,
            "testability": self.testability,
            "overall_score": self.overall_score
        }


class SuccessPatternExtractor:
    """成功模式提取器
    
    负责从高质量代码中提取成功模式，识别最佳实践。
    
    功能：
    - 代码质量评估：评估代码质量指标
    - 成功模式识别：识别高质量代码模式
    - 模式提取：从成功案例中提取可复用模式
    - 模式推荐：根据上下文推荐适用的成功模式
    
    使用示例：
        extractor = SuccessPatternExtractor()
        
        # 提取成功模式
        pattern = extractor.extract_from_code(code, metrics)
        
        # 评估代码质量
        quality = extractor.evaluate_code_quality(code)
        
        # 获取推荐模式
        patterns = extractor.get_recommended_patterns(context)
    """
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        storage_path: Optional[Path] = None
    ):
        self.knowledge_base = knowledge_base
        self.storage_path = storage_path or Path("./success_pattern_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._patterns: Dict[str, SuccessPattern] = {}
        self._pattern_index: Dict[str, List[str]] = defaultdict(list)
        
        self._initialize_default_patterns()
        self._load_patterns()
    
    def _initialize_default_patterns(self) -> None:
        default_patterns = [
            SuccessPattern(
                pattern_id="SP-SOLID-001",
                name="单一职责原则",
                description="一个类或函数应该只有一个引起它变化的原因",
                quality_level=SuccessQualityLevel.EXCELLENT,
                code_pattern="class|def",
                context_requirements=["面向对象设计"],
                benefits=[
                    "提高代码可维护性",
                    "降低耦合度",
                    "便于测试"
                ],
                metrics={
                    "maintainability": 0.95,
                    "testability": 0.90
                },
                applicability=["类设计", "函数设计", "模块设计"],
                prerequisites=["理解SOLID原则"],
                implementation_steps=[
                    {"step": "1", "action": "识别类的职责"},
                    {"step": "2", "action": "分离不同职责到不同的类"},
                    {"step": "3", "action": "确保每个类只有一个职责"}
                ],
                tags=["solid", "srp", "design"],
                confidence=0.95
            ),
            SuccessPattern(
                pattern_id="SP-DRY-001",
                name="不要重复自己",
                description="每一条知识都必须在系统内有单一、明确、权威的表述",
                quality_level=SuccessQualityLevel.EXCELLENT,
                code_pattern="def|class",
                context_requirements=["代码重构"],
                benefits=[
                    "减少代码重复",
                    "提高可维护性",
                    "降低bug风险"
                ],
                metrics={
                    "maintainability": 0.92,
                    "readability": 0.88
                },
                applicability=["函数提取", "类提取", "模块化"],
                prerequisites=["识别重复代码"],
                implementation_steps=[
                    {"step": "1", "action": "识别重复代码片段"},
                    {"step": "2", "action": "提取公共逻辑"},
                    {"step": "3", "action": "创建可复用函数或类"}
                ],
                tags=["dry", "refactoring", "quality"],
                confidence=0.90
            ),
            SuccessPattern(
                pattern_id="SP-KISS-001",
                name="保持简单",
                description="保持代码简单直接，避免过度设计",
                quality_level=SuccessQualityLevel.EXCELLENT,
                code_pattern="def|if|for",
                context_requirements=["代码设计"],
                benefits=[
                    "提高可读性",
                    "降低复杂度",
                    "便于理解"
                ],
                metrics={
                    "readability": 0.95,
                    "maintainability": 0.90
                },
                applicability=["函数设计", "算法实现", "架构设计"],
                prerequisites=["理解问题本质"],
                implementation_steps=[
                    {"step": "1", "action": "分析问题核心需求"},
                    {"step": "2", "action": "选择最简单的实现方式"},
                    {"step": "3", "action": "避免不必要的抽象"}
                ],
                tags=["kiss", "simplicity", "design"],
                confidence=0.88
            ),
            SuccessPattern(
                pattern_id="SP-ERROR-HANDLING-001",
                name="优雅的错误处理",
                description="使用适当的异常处理和错误恢复机制",
                quality_level=SuccessQualityLevel.GOOD,
                code_pattern="try|except|raise",
                context_requirements=["异常处理"],
                benefits=[
                    "提高代码健壮性",
                    "更好的错误信息",
                    "便于调试"
                ],
                metrics={
                    "maintainability": 0.85,
                    "testability": 0.80
                },
                applicability=["IO操作", "网络请求", "数据处理"],
                prerequisites=["理解异常类型"],
                implementation_steps=[
                    {"step": "1", "action": "识别可能失败的操作"},
                    {"step": "2", "action": "选择合适的异常类型"},
                    {"step": "3", "action": "实现错误恢复或清理逻辑"}
                ],
                tags=["error_handling", "robustness", "exceptions"],
                confidence=0.85
            ),
            SuccessPattern(
                pattern_id="SP-TEST-FIRST-001",
                name="测试驱动开发",
                description="先写测试再写实现",
                quality_level=SuccessQualityLevel.EXCELLENT,
                code_pattern="def test_|assert",
                context_requirements=["单元测试"],
                benefits=[
                    "提高代码质量",
                    "更好的设计",
                    "回归测试保护"
                ],
                metrics={
                    "testability": 0.95,
                    "maintainability": 0.88
                },
                applicability=["新功能开发", "bug修复", "重构"],
                prerequisites=["测试框架知识"],
                implementation_steps=[
                    {"step": "1", "action": "编写失败的测试"},
                    {"step": "2", "action": "编写最小实现使测试通过"},
                    {"step": "3", "action": "重构优化代码"}
                ],
                tags=["tdd", "testing", "quality"],
                confidence=0.92
            ),
            SuccessPattern(
                pattern_id="SP-DOC-001",
                name="清晰的文档",
                description="为公共API编写清晰完整的文档",
                quality_level=SuccessQualityLevel.GOOD,
                code_pattern='"""|\'\'\'',
                context_requirements=["API设计"],
                benefits=[
                    "提高可用性",
                    "便于团队协作",
                    "降低学习成本"
                ],
                metrics={
                    "readability": 0.90,
                    "maintainability": 0.85
                },
                applicability=["公共函数", "类", "模块"],
                prerequisites=["文档规范知识"],
                implementation_steps=[
                    {"step": "1", "action": "为函数添加文档字符串"},
                    {"step": "2", "action": "描述参数和返回值"},
                    {"step": "3", "action": "提供使用示例"}
                ],
                tags=["documentation", "api", "readability"],
                confidence=0.85
            )
        ]
        
        for pattern in default_patterns:
            self._patterns[pattern.pattern_id] = pattern
            self._index_pattern(pattern)
    
    def _index_pattern(self, pattern: SuccessPattern) -> None:
        self._pattern_index["by_quality"][pattern.quality_level.value].append(pattern.pattern_id)
        for tag in pattern.tags:
            self._pattern_index[f"by_tag_{tag}"].append(pattern.pattern_id)
    
    def _load_patterns(self) -> None:
        patterns_file = self.storage_path / "success_patterns.json"
        
        if patterns_file.exists():
            try:
                with open(patterns_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for pattern_data in data.get("patterns", []):
                    pattern = SuccessPattern.from_dict(pattern_data)
                    self._patterns[pattern.pattern_id] = pattern
                    self._index_pattern(pattern)
                
                logger.info(f"加载成功模式: {len(self._patterns)} 个")
            except Exception as e:
                logger.warning(f"加载成功模式失败: {e}")
    
    def _save_patterns(self) -> None:
        patterns_file = self.storage_path / "success_patterns.json"
        
        try:
            with open(patterns_file, "w", encoding="utf-8") as f:
                json.dump({
                    "patterns": [p.to_dict() for p in self._patterns.values()]
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存成功模式失败: {e}")
    
    def evaluate_code_quality(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CodeQualityMetrics:
        readability = self._evaluate_readability(code)
        maintainability = self._evaluate_maintainability(code)
        performance = self._evaluate_performance(code)
        security = self._evaluate_security(code)
        testability = self._evaluate_testability(code)
        
        overall_score = (
            readability * 0.25 +
            maintainability * 0.25 +
            performance * 0.20 +
            security * 0.15 +
            testability * 0.15
        )
        
        return CodeQualityMetrics(
            readability=readability,
            maintainability=maintainability,
            performance=performance,
            security=security,
            testability=testability,
            overall_score=overall_score
        )
    
    def _evaluate_readability(self, code: str) -> float:
        score = 0.5
        
        lines = code.split("\n")
        avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0
        
        if avg_line_length < 80:
            score += 0.2
        elif avg_line_length < 100:
            score += 0.1
        
        if code.count('"""') >= 2 or code.count("'''") >= 2:
            score += 0.15
        
        meaningful_names = len(re.findall(r'\b[a-z][a-z0-9_]{3,}\b', code))
        total_names = len(re.findall(r'\b[a-z][a-z0-9_]*\b', code))
        if total_names > 0 and meaningful_names / total_names > 0.7:
            score += 0.15
        
        return min(score, 1.0)
    
    def _evaluate_maintainability(self, code: str) -> float:
        score = 0.5
        
        functions = re.findall(r'def\s+\w+', code)
        if functions:
            avg_func_length = len(code) / len(functions)
            if avg_func_length < 200:
                score += 0.2
            elif avg_func_length < 400:
                score += 0.1
        
        nesting_level = self._calculate_max_nesting(code)
        if nesting_level <= 3:
            score += 0.2
        elif nesting_level <= 5:
            score += 0.1
        
        if re.search(r'TODO|FIXME|XXX', code):
            score -= 0.1
        
        return max(0, min(score, 1.0))
    
    def _calculate_max_nesting(self, code: str) -> int:
        max_nesting = 0
        current_nesting = 0
        
        for line in code.split("\n"):
            if not line.strip():
                continue
            
            indent = len(line) - len(line.lstrip())
            current_nesting = indent // 4
            max_nesting = max(max_nesting, current_nesting)
        
        return max_nesting
    
    def _evaluate_performance(self, code: str) -> float:
        score = 0.7
        
        if re.search(r'for\s+\w+\s+in\s+range\(len\(', code):
            if not re.search(r'for\s+\w+,\s*\w+\s+in\s+enumerate', code):
                score -= 0.1
        
        if re.search(r'\+\s*=\s*.*\n.*for', code, re.MULTILINE):
            score -= 0.1
        
        if re.search(r'append|extend|update', code):
            score += 0.1
        
        return max(0, min(score, 1.0))
    
    def _evaluate_security(self, code: str) -> float:
        score = 0.8
        
        dangerous_patterns = [
            (r'eval\s*\(', -0.3),
            (r'exec\s*\(', -0.3),
            (r'__import__\s*\(', -0.2),
            (r'subprocess\.call.*shell=True', -0.2),
            (r'pickle\.loads', -0.2)
        ]
        
        for pattern, penalty in dangerous_patterns:
            if re.search(pattern, code):
                score += penalty
        
        if re.search(r'input\s*\(|sys\.argv', code):
            if re.search(r'validate|sanitize|escape', code, re.IGNORECASE):
                score += 0.1
            else:
                score -= 0.1
        
        return max(0, min(score, 1.0))
    
    def _evaluate_testability(self, code: str) -> float:
        score = 0.5
        
        functions = re.findall(r'def\s+(\w+)', code)
        if functions:
            pure_functions = sum(
                1 for func in functions
                if not func.startswith('_') and func not in ['main', 'run', 'execute']
            )
            score += (pure_functions / len(functions)) * 0.2
        
        if re.search(r'class\s+\w+.*:', code):
            if re.search(r'def\s+__init__', code):
                score += 0.1
            
            if re.search(r'def\s+__init__.*:\s*\n\s*pass', code):
                score += 0.1
        
        if re.search(r'dependency|inject|mock', code, re.IGNORECASE):
            score += 0.1
        
        return min(score, 1.0)
    
    def extract_from_code(
        self,
        code: str,
        metrics: Optional[CodeQualityMetrics] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[SuccessPattern]:
        if not metrics:
            metrics = self.evaluate_code_quality(code)
        
        if metrics.overall_score < 0.7:
            return None
        
        quality_level = self._determine_quality_level(metrics.overall_score)
        
        pattern_name = self._generate_pattern_name(code, metrics)
        description = self._generate_description(code, metrics)
        
        pattern = SuccessPattern(
            pattern_id=f"SP-EXTRACT-{hashlib.md5(pattern_name.encode()).hexdigest()[:8]}",
            name=pattern_name,
            description=description,
            quality_level=quality_level,
            code_pattern=self._extract_pattern_signature(code),
            benefits=self._identify_benefits(code, metrics),
            metrics=metrics.to_dict(),
            applicability=self._identify_applicability(code),
            tags=self._extract_tags(code),
            confidence=metrics.overall_score,
            metadata={
                "extracted_at": datetime.now().isoformat(),
                "original_metrics": metrics.to_dict()
            }
        )
        
        self._patterns[pattern.pattern_id] = pattern
        self._index_pattern(pattern)
        self._save_patterns()
        
        logger.info(f"提取成功模式: {pattern.pattern_id} - {pattern.name}")
        return pattern
    
    def _determine_quality_level(self, score: float) -> SuccessQualityLevel:
        if score >= 0.9:
            return SuccessQualityLevel.EXCELLENT
        elif score >= 0.75:
            return SuccessQualityLevel.GOOD
        elif score >= 0.6:
            return SuccessQualityLevel.ACCEPTABLE
        else:
            return SuccessQualityLevel.POOR
    
    def _generate_pattern_name(
        self,
        code: str,
        metrics: CodeQualityMetrics
    ) -> str:
        if metrics.readability > 0.8:
            return "高可读性代码模式"
        elif metrics.maintainability > 0.8:
            return "高可维护性代码模式"
        elif metrics.testability > 0.8:
            return "高可测试性代码模式"
        else:
            return "高质量代码模式"
    
    def _generate_description(
        self,
        code: str,
        metrics: CodeQualityMetrics
    ) -> str:
        strengths = []
        
        if metrics.readability > 0.8:
            strengths.append("可读性优秀")
        if metrics.maintainability > 0.8:
            strengths.append("可维护性优秀")
        if metrics.testability > 0.8:
            strengths.append("可测试性优秀")
        if metrics.security > 0.8:
            strengths.append("安全性优秀")
        
        return f"从高质量代码中提取的模式，特点：{', '.join(strengths)}"
    
    def _extract_pattern_signature(self, code: str) -> str:
        lines = code.split("\n")[:5]
        return "\n".join(lines)
    
    def _identify_benefits(
        self,
        code: str,
        metrics: CodeQualityMetrics
    ) -> List[str]:
        benefits = []
        
        if metrics.readability > 0.7:
            benefits.append("代码易于理解")
        if metrics.maintainability > 0.7:
            benefits.append("易于维护和修改")
        if metrics.testability > 0.7:
            benefits.append("便于编写测试")
        if metrics.security > 0.7:
            benefits.append("安全性良好")
        if metrics.performance > 0.7:
            benefits.append("性能表现良好")
        
        return benefits
    
    def _identify_applicability(self, code: str) -> List[str]:
        applicability = []
        
        if re.search(r'class\s+\w+', code):
            applicability.append("类设计")
        if re.search(r'def\s+\w+', code):
            applicability.append("函数设计")
        if re.search(r'import|from', code):
            applicability.append("模块化开发")
        
        return applicability if applicability else ["通用场景"]
    
    def _extract_tags(self, code: str) -> List[str]:
        tags = []
        
        if re.search(r'def\s+test_', code):
            tags.append("testing")
        if re.search(r'class\s+\w+', code):
            tags.append("oop")
        if re.search(r'async\s+def|await', code):
            tags.append("async")
        if re.search(r'try|except', code):
            tags.append("error_handling")
        
        return tags if tags else ["general"]
    
    def get_recommended_patterns(
        self,
        context: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        recommendations = []
        
        for pattern in self._patterns.values():
            score = self._calculate_relevance_score(pattern, context)
            
            if score > 0.3:
                recommendations.append({
                    "pattern": pattern.to_dict(),
                    "relevance_score": score,
                    "reasons": self._generate_recommendation_reasons(pattern, context)
                })
        
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        return recommendations[:limit]
    
    def _calculate_relevance_score(
        self,
        pattern: SuccessPattern,
        context: Dict[str, Any]
    ) -> float:
        score = 0.0
        
        context_tags = set(context.get("tags", []))
        pattern_tags = set(pattern.tags)
        tag_overlap = len(context_tags & pattern_tags)
        if tag_overlap > 0:
            score += min(tag_overlap * 0.2, 0.5)
        
        context_requirements = context.get("requirements", [])
        for req in context_requirements:
            if req in pattern.applicability:
                score += 0.15
        
        score += pattern.confidence * 0.3
        
        return min(score, 1.0)
    
    def _generate_recommendation_reasons(
        self,
        pattern: SuccessPattern,
        context: Dict[str, Any]
    ) -> List[str]:
        reasons = []
        
        if pattern.quality_level == SuccessQualityLevel.EXCELLENT:
            reasons.append("质量等级优秀")
        
        if pattern.benefits:
            reasons.append(f"主要收益: {pattern.benefits[0]}")
        
        context_tags = set(context.get("tags", []))
        matching_tags = context_tags & set(pattern.tags)
        if matching_tags:
            reasons.append(f"标签匹配: {', '.join(list(matching_tags)[:3])}")
        
        return reasons[:3]
    
    def add_success_case(
        self,
        pattern_id: str,
        case: Dict[str, Any]
    ) -> bool:
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return False
        
        pattern.success_cases.append({
            **case,
            "added_at": datetime.now().isoformat()
        })
        pattern.usage_count += 1
        
        self._save_patterns()
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        by_quality: Dict[str, int] = defaultdict(int)
        
        for pattern in self._patterns.values():
            by_quality[pattern.quality_level.value] += 1
        
        avg_confidence = (
            sum(p.confidence for p in self._patterns.values()) / len(self._patterns)
            if self._patterns else 0
        )
        
        return {
            "total_patterns": len(self._patterns),
            "by_quality": dict(by_quality),
            "average_confidence": avg_confidence,
            "total_success_cases": sum(len(p.success_cases) for p in self._patterns.values())
        }


class ApplicationContext(Enum):
    CODE_REVIEW = "code_review"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    NEW_FEATURE = "new_feature"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_REVIEW = "security_review"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


@dataclass
class KnowledgeApplication:
    application_id: str
    knowledge_id: str
    context: ApplicationContext
    target_description: str
    applied_at: str
    success: bool
    effectiveness_score: float
    feedback: str = ""
    adaptations: List[str] = field(default_factory=list)
    outcomes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "application_id": self.application_id,
            "knowledge_id": self.knowledge_id,
            "context": self.context.value,
            "target_description": self.target_description,
            "applied_at": self.applied_at,
            "success": self.success,
            "effectiveness_score": self.effectiveness_score,
            "feedback": self.feedback,
            "adaptations": self.adaptations,
            "outcomes": self.outcomes,
            "metadata": self.metadata
        }


@dataclass
class ApplicationRecommendation:
    knowledge_id: str
    knowledge_type: str
    title: str
    relevance_score: float
    applicability_score: float
    priority: int
    context_match: List[str]
    suggested_adaptations: List[str]
    expected_benefits: List[str]
    potential_risks: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "knowledge_type": self.knowledge_type,
            "title": self.title,
            "relevance_score": self.relevance_score,
            "applicability_score": self.applicability_score,
            "priority": self.priority,
            "context_match": self.context_match,
            "suggested_adaptations": self.suggested_adaptations,
            "expected_benefits": self.expected_benefits,
            "potential_risks": self.potential_risks
        }


class KnowledgeApplicationEngine:
    """知识应用引擎
    
    负责将学习到的知识应用到新场景，提供智能推荐。
    
    功能：
    - 知识匹配：根据上下文匹配相关知识
    - 应用推荐：推荐最适用的知识
    - 效果跟踪：跟踪知识应用效果
    - 自适应调整：根据应用反馈调整知识
    
    使用示例：
        engine = KnowledgeApplicationEngine()
        
        # 获取推荐
        recommendations = engine.get_recommendations(context)
        
        # 应用知识
        result = engine.apply_knowledge(knowledge_id, context)
        
        # 记录反馈
        engine.record_feedback(application_id, feedback)
    """
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        pattern_recognizer: Optional[PatternRecognizer] = None,
        failure_learner: Optional[FailurePatternLearner] = None,
        success_extractor: Optional[SuccessPatternExtractor] = None,
        storage_path: Optional[Path] = None
    ):
        self.knowledge_base = knowledge_base
        self.pattern_recognizer = pattern_recognizer
        self.failure_learner = failure_learner
        self.success_extractor = success_extractor
        self.storage_path = storage_path or Path("./knowledge_application_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._applications: List[KnowledgeApplication] = []
        self._application_index: Dict[str, List[str]] = defaultdict(list)
        
        self._load_data()
    
    def _load_data(self) -> None:
        applications_file = self.storage_path / "applications.json"
        
        if applications_file.exists():
            try:
                with open(applications_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for app_data in data.get("applications", []):
                    application = KnowledgeApplication(
                        application_id=app_data.get("application_id", ""),
                        knowledge_id=app_data.get("knowledge_id", ""),
                        context=ApplicationContext(app_data.get("context", "code_review")),
                        target_description=app_data.get("target_description", ""),
                        applied_at=app_data.get("applied_at", ""),
                        success=app_data.get("success", False),
                        effectiveness_score=app_data.get("effectiveness_score", 0.0),
                        feedback=app_data.get("feedback", ""),
                        adaptations=app_data.get("adaptations", []),
                        outcomes=app_data.get("outcomes", []),
                        metadata=app_data.get("metadata", {})
                    )
                    self._applications.append(application)
                    self._index_application(application)
                
                logger.info(f"加载知识应用记录: {len(self._applications)} 条")
            except Exception as e:
                logger.warning(f"加载知识应用记录失败: {e}")
    
    def _save_data(self) -> None:
        applications_file = self.storage_path / "applications.json"
        
        try:
            with open(applications_file, "w", encoding="utf-8") as f:
                json.dump({
                    "applications": [a.to_dict() for a in self._applications]
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存知识应用记录失败: {e}")
    
    def _index_application(self, application: KnowledgeApplication) -> None:
        self._application_index["by_context"][application.context.value].append(application.application_id)
        self._application_index[f"by_knowledge_{application.knowledge_id}"].append(application.application_id)
    
    def get_recommendations(
        self,
        context: Dict[str, Any],
        application_context: ApplicationContext,
        limit: int = 10
    ) -> List[ApplicationRecommendation]:
        recommendations = []
        
        if self.knowledge_base:
            kb_recommendations = self._get_knowledge_base_recommendations(
                context, application_context
            )
            recommendations.extend(kb_recommendations)
        
        if self.failure_learner:
            failure_recommendations = self._get_failure_pattern_recommendations(
                context, application_context
            )
            recommendations.extend(failure_recommendations)
        
        if self.success_extractor:
            success_recommendations = self._get_success_pattern_recommendations(
                context, application_context
            )
            recommendations.extend(success_recommendations)
        
        recommendations.sort(key=lambda x: x.priority, reverse=True)
        
        seen_ids = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec.knowledge_id not in seen_ids:
                seen_ids.add(rec.knowledge_id)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:limit]
    
    def _get_knowledge_base_recommendations(
        self,
        context: Dict[str, Any],
        application_context: ApplicationContext
    ) -> List[ApplicationRecommendation]:
        recommendations = []
        
        if not self.knowledge_base:
            return recommendations
        
        search_query = self._build_search_query(context)
        search_results = self.knowledge_base.search(search_query, mode=SearchMode.HYBRID)
        
        for result in search_results[:20]:
            relevance = self._calculate_relevance(result.item, context)
            applicability = self._calculate_applicability(result.item, application_context)
            
            if relevance > 0.3:
                priority = self._calculate_priority(relevance, applicability, result.item)
                
                recommendation = ApplicationRecommendation(
                    knowledge_id=result.item.knowledge_id,
                    knowledge_type=result.item.knowledge_type.value,
                    title=result.item.title,
                    relevance_score=relevance,
                    applicability_score=applicability,
                    priority=priority,
                    context_match=self._identify_context_matches(result.item, context),
                    suggested_adaptations=self._suggest_adaptations(result.item, context),
                    expected_benefits=result.item.examples[0].get("benefits", []) if result.item.examples else [],
                    potential_risks=self._identify_risks(result.item, context)
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _get_failure_pattern_recommendations(
        self,
        context: Dict[str, Any],
        application_context: ApplicationContext
    ) -> List[ApplicationRecommendation]:
        recommendations = []
        
        if not self.failure_learner:
            return recommendations
        
        error_type = context.get("error_type", "")
        error_message = context.get("error_message", "")
        
        if error_type:
            fix_recs = self.failure_learner.get_fix_recommendations(error_type, error_message)
            
            for rec in fix_recs:
                relevance = rec.get("success_rate", 0.5)
                applicability = 0.8 if application_context == ApplicationContext.BUG_FIX else 0.5
                
                recommendation = ApplicationRecommendation(
                    knowledge_id=rec.get("pattern_id", ""),
                    knowledge_type="failure_pattern",
                    title=f"修复方法: {rec.get('method', '')}",
                    relevance_score=relevance,
                    applicability_score=applicability,
                    priority=int(relevance * 80),
                    context_match=["错误类型匹配"],
                    suggested_adaptations=["根据具体场景调整修复步骤"],
                    expected_benefits=[f"成功率: {rec.get('success_rate', 0):.0%}"],
                    potential_risks=["可能需要根据上下文调整"]
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _get_success_pattern_recommendations(
        self,
        context: Dict[str, Any],
        application_context: ApplicationContext
    ) -> List[ApplicationRecommendation]:
        recommendations = []
        
        if not self.success_extractor:
            return recommendations
        
        pattern_recs = self.success_extractor.get_recommended_patterns(context)
        
        for rec in pattern_recs:
            pattern_data = rec.get("pattern", {})
            relevance = rec.get("relevance_score", 0.5)
            
            applicability = self._calculate_pattern_applicability(
                pattern_data, application_context
            )
            
            recommendation = ApplicationRecommendation(
                knowledge_id=pattern_data.get("pattern_id", ""),
                knowledge_type="success_pattern",
                title=pattern_data.get("name", ""),
                relevance_score=relevance,
                applicability_score=applicability,
                priority=int((relevance + applicability) * 50),
                context_match=rec.get("reasons", []),
                suggested_adaptations=pattern_data.get("prerequisites", []),
                expected_benefits=pattern_data.get("benefits", []),
                potential_risks=[]
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _build_search_query(self, context: Dict[str, Any]) -> str:
        query_parts = []
        
        if context.get("error_type"):
            query_parts.append(context["error_type"])
        
        if context.get("tags"):
            query_parts.extend(context["tags"][:3])
        
        if context.get("category"):
            query_parts.append(context["category"])
        
        if context.get("keywords"):
            query_parts.extend(context["keywords"][:3])
        
        return " ".join(query_parts) if query_parts else ""
    
    def _calculate_relevance(
        self,
        knowledge: KnowledgeItem,
        context: Dict[str, Any]
    ) -> float:
        score = 0.0
        
        context_tags = set(context.get("tags", []))
        knowledge_tags = set(knowledge.tags)
        tag_overlap = len(context_tags & knowledge_tags)
        if tag_overlap > 0:
            score += min(tag_overlap * 0.15, 0.4)
        
        if knowledge.success_rate > 0.8:
            score += 0.2
        elif knowledge.success_rate > 0.6:
            score += 0.1
        
        if knowledge.usage_count > 20:
            score += 0.2
        elif knowledge.usage_count > 10:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_applicability(
        self,
        knowledge: KnowledgeItem,
        application_context: ApplicationContext
    ) -> float:
        score = 0.5
        
        context_keywords = {
            ApplicationContext.BUG_FIX: ["fix", "error", "bug", "issue"],
            ApplicationContext.REFACTORING: ["refactor", "improve", "optimize"],
            ApplicationContext.NEW_FEATURE: ["feature", "new", "add"],
            ApplicationContext.CODE_REVIEW: ["review", "quality", "best"],
            ApplicationContext.TESTING: ["test", "unit", "coverage"],
            ApplicationContext.SECURITY_REVIEW: ["security", "vulnerability"],
            ApplicationContext.PERFORMANCE_OPTIMIZATION: ["performance", "optimize", "speed"],
            ApplicationContext.DOCUMENTATION: ["doc", "comment", "readme"]
        }
        
        keywords = context_keywords.get(application_context, [])
        
        for keyword in keywords:
            if keyword in knowledge.title.lower() or keyword in knowledge.content.lower():
                score += 0.15
        
        return min(score, 1.0)
    
    def _calculate_pattern_applicability(
        self,
        pattern_data: Dict[str, Any],
        application_context: ApplicationContext
    ) -> float:
        applicability = pattern_data.get("applicability", [])
        
        context_mapping = {
            ApplicationContext.CODE_REVIEW: ["代码审查", "质量检查"],
            ApplicationContext.BUG_FIX: ["错误修复", "调试"],
            ApplicationContext.REFACTORING: ["重构", "优化"],
            ApplicationContext.NEW_FEATURE: ["新功能", "开发"],
            ApplicationContext.TESTING: ["测试", "单元测试"],
            ApplicationContext.DOCUMENTATION: ["文档", "注释"]
        }
        
        matches = context_mapping.get(application_context, [])
        match_count = sum(1 for m in matches if any(m in a for a in applicability))
        
        return min(0.5 + match_count * 0.2, 1.0)
    
    def _calculate_priority(
        self,
        relevance: float,
        applicability: float,
        knowledge: KnowledgeItem
    ) -> int:
        base_score = (relevance * 0.6 + applicability * 0.4) * 100
        
        if knowledge.confidence_score > 0.8:
            base_score += 10
        
        if knowledge.success_rate > 0.8:
            base_score += 10
        
        return int(base_score)
    
    def _identify_context_matches(
        self,
        knowledge: KnowledgeItem,
        context: Dict[str, Any]
    ) -> List[str]:
        matches = []
        
        context_tags = set(context.get("tags", []))
        knowledge_tags = set(knowledge.tags)
        matching_tags = context_tags & knowledge_tags
        if matching_tags:
            matches.append(f"标签匹配: {', '.join(list(matching_tags)[:3])}")
        
        if context.get("category") and context["category"] == knowledge.category:
            matches.append("类别匹配")
        
        return matches
    
    def _suggest_adaptations(
        self,
        knowledge: KnowledgeItem,
        context: Dict[str, Any]
    ) -> List[str]:
        adaptations = []
        
        if knowledge.examples:
            adaptations.append("参考示例代码进行适配")
        
        if knowledge.metadata.get("prerequisites"):
            adaptations.extend(knowledge.metadata["prerequisites"])
        
        return adaptations[:3]
    
    def _identify_risks(
        self,
        knowledge: KnowledgeItem,
        context: Dict[str, Any]
    ) -> List[str]:
        risks = []
        
        if knowledge.success_rate < 0.6:
            risks.append("成功率较低，需谨慎应用")
        
        if knowledge.usage_count < 5:
            risks.append("应用次数较少，效果待验证")
        
        return risks
    
    def apply_knowledge(
        self,
        knowledge_id: str,
        context: ApplicationContext,
        target_description: str,
        adaptations: Optional[List[str]] = None
    ) -> KnowledgeApplication:
        application = KnowledgeApplication(
            application_id=f"KA-{hashlib.md5(f'{knowledge_id}{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}",
            knowledge_id=knowledge_id,
            context=context,
            target_description=target_description,
            applied_at=datetime.now().isoformat(),
            success=False,
            effectiveness_score=0.0,
            adaptations=adaptations or []
        )
        
        self._applications.append(application)
        self._index_application(application)
        self._save_data()
        
        if self.knowledge_base:
            knowledge = self.knowledge_base.get_knowledge(knowledge_id)
            if knowledge:
                knowledge.usage_count += 1
                self.knowledge_base.update_knowledge(
                    knowledge_id,
                    {"usage_count": knowledge.usage_count}
                )
        
        logger.info(f"应用知识: {knowledge_id} 到 {context.value}")
        return application
    
    def record_feedback(
        self,
        application_id: str,
        success: bool,
        effectiveness_score: float,
        feedback: str = "",
        outcomes: Optional[List[str]] = None
    ) -> bool:
        application = None
        for app in self._applications:
            if app.application_id == application_id:
                application = app
                break
        
        if not application:
            return False
        
        application.success = success
        application.effectiveness_score = effectiveness_score
        application.feedback = feedback
        application.outcomes = outcomes or []
        
        self._update_knowledge_effectiveness(
            application.knowledge_id,
            success,
            effectiveness_score
        )
        
        self._save_data()
        
        logger.info(f"记录应用反馈: {application_id}, 成功: {success}")
        return True
    
    def _update_knowledge_effectiveness(
        self,
        knowledge_id: str,
        success: bool,
        effectiveness_score: float
    ) -> None:
        if not self.knowledge_base:
            return
        
        knowledge = self.knowledge_base.get_knowledge(knowledge_id)
        if not knowledge:
            return
        
        current_successes = knowledge.success_rate * knowledge.usage_count
        if success:
            new_success_rate = (current_successes + 1) / knowledge.usage_count
        else:
            new_success_rate = current_successes / knowledge.usage_count
        
        self.knowledge_base.update_knowledge(
            knowledge_id,
            {"success_rate": new_success_rate}
        )
    
    def get_application_history(
        self,
        knowledge_id: Optional[str] = None,
        context: Optional[ApplicationContext] = None,
        limit: int = 50
    ) -> List[KnowledgeApplication]:
        applications = self._applications
        
        if knowledge_id:
            applications = [
                a for a in applications
                if a.knowledge_id == knowledge_id
            ]
        
        if context:
            applications = [
                a for a in applications
                if a.context == context
            ]
        
        applications.sort(key=lambda x: x.applied_at, reverse=True)
        return applications[:limit]
    
    def analyze_effectiveness(
        self,
        knowledge_id: Optional[str] = None
    ) -> Dict[str, Any]:
        applications = self._applications
        
        if knowledge_id:
            applications = [
                a for a in applications
                if a.knowledge_id == knowledge_id
            ]
        
        if not applications:
            return {
                "total_applications": 0,
                "success_rate": 0.0,
                "average_effectiveness": 0.0
            }
        
        success_count = sum(1 for a in applications if a.success)
        avg_effectiveness = (
            sum(a.effectiveness_score for a in applications) / len(applications)
        )
        
        by_context: Dict[str, int] = defaultdict(int)
        for app in applications:
            by_context[app.context.value] += 1
        
        return {
            "total_applications": len(applications),
            "success_rate": success_count / len(applications),
            "average_effectiveness": avg_effectiveness,
            "by_context": dict(by_context)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        by_context: Dict[str, int] = defaultdict(int)
        
        for app in self._applications:
            by_context[app.context.value] += 1
        
        success_count = sum(1 for a in self._applications if a.success)
        
        return {
            "total_applications": len(self._applications),
            "success_rate": success_count / len(self._applications) if self._applications else 0,
            "by_context": dict(by_context),
            "unique_knowledge_applied": len(set(a.knowledge_id for a in self._applications))
        }


class KnowledgeLearningSystem:
    """知识学习系统集成类
    
    整合所有知识学习组件，提供统一的接口。
    
    新增功能：
    - 失败模式学习：记录和分析失败案例
    - 成功模式提取：从高质量代码中提取模式
    - 知识应用引擎：智能推荐和应用知识
    """
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        storage_path: Optional[Path] = None
    ):
        self.storage_path = storage_path or Path("./knowledge_learning_system")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.knowledge_base = knowledge_base or KnowledgeBase(
            storage_path=self.storage_path / "kb",
            storage_type="sqlite"
        )
        
        self.pattern_recognizer = PatternRecognizer(
            knowledge_base=self.knowledge_base,
            storage_path=self.storage_path / "patterns"
        )
        
        self.best_practice_extractor = BestPracticeExtractor(
            knowledge_base=self.knowledge_base,
            storage_path=self.storage_path / "practices"
        )
        
        self.fix_strategy_learner = FixStrategyLearner(
            knowledge_base=self.knowledge_base,
            storage_path=self.storage_path / "strategies"
        )
        
        self.quality_evaluator = KnowledgeQualityEvaluator(
            knowledge_base=self.knowledge_base,
            storage_path=self.storage_path / "quality"
        )
        
        self.failure_learner = FailurePatternLearner(
            knowledge_base=self.knowledge_base,
            storage_path=self.storage_path / "failures"
        )
        
        self.success_extractor = SuccessPatternExtractor(
            knowledge_base=self.knowledge_base,
            storage_path=self.storage_path / "success_patterns"
        )
        
        self.application_engine = KnowledgeApplicationEngine(
            knowledge_base=self.knowledge_base,
            pattern_recognizer=self.pattern_recognizer,
            failure_learner=self.failure_learner,
            success_extractor=self.success_extractor,
            storage_path=self.storage_path / "applications"
        )
    
    def analyze_code(self, source_code: str) -> Dict[str, Any]:
        patterns = self.pattern_recognizer.recognize_code_patterns(source_code)
        
        return {
            "patterns_found": len(patterns),
            "patterns": [p.to_dict() for p in patterns[:10]],
            "recommendations": self._generate_code_recommendations(patterns)
        }
    
    def _generate_code_recommendations(
        self,
        patterns: List[PatternMatchResult]
    ) -> List[str]:
        recommendations = []
        
        anti_patterns = [
            p for p in patterns
            if p.pattern.category == PatternCategory.ANTI_PATTERN
        ]
        
        for ap in anti_patterns[:3]:
            recommendations.append(f"检测到反模式: {ap.pattern.name}，建议重构")
        
        return recommendations
    
    def learn_from_fix(
        self,
        issue: Dict[str, Any],
        fix: Dict[str, Any],
        outcome: Dict[str, Any]
    ) -> Dict[str, Any]:
        strategy = self.fix_strategy_learner.learn_from_fix(issue, fix, outcome)
        
        if outcome.get("success"):
            practice = self._extract_practice_from_fix(issue, fix)
            if practice:
                self.best_practice_extractor.add_practice(practice)
        
        return {
            "strategy_learned": strategy is not None,
            "strategy_id": strategy.strategy_id if strategy else None
        }
    
    def _extract_practice_from_fix(
        self,
        issue: Dict[str, Any],
        fix: Dict[str, Any]
    ) -> Optional[BestPractice]:
        if not fix.get("is_best_practice"):
            return None
        
        return BestPractice(
            practice_id="",
            category=PracticeCategory.CODING_STYLE,
            level=PracticeLevel.INTERMEDIATE,
            title=f"修复实践: {issue.get('type', 'unknown')}",
            description=fix.get("description", ""),
            code_example=fix.get("code", ""),
            benefits=["解决类似问题"],
            tags=["learned", issue.get("type", "general")]
        )
    
    def evaluate_knowledge_quality(self) -> Dict[str, Any]:
        evaluation = self.quality_evaluator.evaluate_all()
        
        candidates = self.quality_evaluator.get_retirement_candidates()
        
        return {
            "evaluation": evaluation,
            "retirement_candidates": len(candidates),
            "recommendations": self._generate_quality_recommendations(evaluation)
        }
    
    def _generate_quality_recommendations(
        self,
        evaluation: Dict[str, Any]
    ) -> List[str]:
        recommendations = []
        
        by_level = evaluation.get("by_level", {})
        
        if by_level.get("poor", 0) > 0:
            recommendations.append(f"有 {by_level['poor']} 条知识质量较差，建议改进或淘汰")
        
        if by_level.get("fair", 0) > by_level.get("good", 0) + by_level.get("excellent", 0):
            recommendations.append("大部分知识质量一般，建议系统性地提升知识质量")
        
        if evaluation.get("retirement_candidates", 0) > 10:
            recommendations.append("存在较多淘汰候选，建议进行知识清理")
        
        return recommendations
    
    def learn_from_failure(
        self,
        error_info: Dict[str, Any],
        fix_info: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        pattern = self.failure_learner.record_failure(error_info, fix_info, context)
        
        return {
            "pattern_id": pattern.pattern_id,
            "pattern_name": pattern.name,
            "category": pattern.category.value,
            "severity": pattern.severity.value,
            "fix_success_rate": pattern.fix_success_rate
        }
    
    def extract_success_pattern(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        metrics = self.success_extractor.evaluate_code_quality(code)
        
        if metrics.overall_score < 0.7:
            return {
                "success": False,
                "reason": "代码质量未达到提取标准",
                "metrics": metrics.to_dict()
            }
        
        pattern = self.success_extractor.extract_from_code(code, metrics, context)
        
        if pattern:
            return {
                "success": True,
                "pattern_id": pattern.pattern_id,
                "pattern_name": pattern.name,
                "quality_level": pattern.quality_level.value,
                "metrics": metrics.to_dict()
            }
        else:
            return {
                "success": False,
                "reason": "无法提取有效模式",
                "metrics": metrics.to_dict()
            }
    
    def get_knowledge_recommendations(
        self,
        context: Dict[str, Any],
        application_context: str = "code_review",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        try:
            app_context = ApplicationContext(application_context)
        except ValueError:
            app_context = ApplicationContext.CODE_REVIEW
        
        recommendations = self.application_engine.get_recommendations(
            context, app_context, limit
        )
        
        return [rec.to_dict() for rec in recommendations]
    
    def apply_knowledge_to_context(
        self,
        knowledge_id: str,
        application_context: str,
        target_description: str,
        adaptations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        try:
            app_context = ApplicationContext(application_context)
        except ValueError:
            app_context = ApplicationContext.CODE_REVIEW
        
        application = self.application_engine.apply_knowledge(
            knowledge_id, app_context, target_description, adaptations
        )
        
        return {
            "application_id": application.application_id,
            "knowledge_id": application.knowledge_id,
            "context": application.context.value,
            "applied_at": application.applied_at
        }
    
    def record_application_feedback(
        self,
        application_id: str,
        success: bool,
        effectiveness_score: float,
        feedback: str = "",
        outcomes: Optional[List[str]] = None
    ) -> bool:
        return self.application_engine.record_feedback(
            application_id, success, effectiveness_score, feedback, outcomes
        )
    
    def analyze_failure_trends(self, days: int = 30) -> Dict[str, Any]:
        return self.failure_learner.analyze_failure_trends(days)
    
    def get_prevention_tips(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[str]:
        failure_category = None
        if category:
            try:
                failure_category = FailureCategory(category)
            except ValueError:
                pass
        
        return self.failure_learner.get_prevention_tips(failure_category, tags)
    
    def evaluate_code_quality(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        metrics = self.success_extractor.evaluate_code_quality(code, context)
        return metrics.to_dict()
    
    def get_system_statistics(self) -> Dict[str, Any]:
        return {
            "knowledge_base": self.knowledge_base.get_statistics(),
            "pattern_recognizer": self.pattern_recognizer.get_statistics(),
            "best_practice_extractor": self.best_practice_extractor.get_statistics(),
            "fix_strategy_learner": self.fix_strategy_learner.get_statistics(),
            "quality_evaluator": self.quality_evaluator.get_statistics(),
            "failure_learner": self.failure_learner.get_statistics(),
            "success_extractor": self.success_extractor.get_statistics(),
            "application_engine": self.application_engine.get_statistics()
        }
    
    def generate_learning_report(self) -> Dict[str, Any]:
        kb_stats = self.knowledge_base.get_statistics()
        failure_stats = self.failure_learner.get_statistics()
        success_stats = self.success_extractor.get_statistics()
        app_stats = self.application_engine.get_statistics()
        
        return {
            "report_generated_at": datetime.now().isoformat(),
            "knowledge_summary": {
                "total_knowledge": kb_stats.get("total_knowledge", 0),
                "active_knowledge": kb_stats.get("active_count", 0)
            },
            "failure_learning": {
                "total_patterns": failure_stats.get("total_patterns", 0),
                "total_records": failure_stats.get("total_records", 0),
                "average_fix_success_rate": failure_stats.get("average_fix_success_rate", 0)
            },
            "success_patterns": {
                "total_patterns": success_stats.get("total_patterns", 0),
                "average_confidence": success_stats.get("average_confidence", 0)
            },
            "knowledge_application": {
                "total_applications": app_stats.get("total_applications", 0),
                "success_rate": app_stats.get("success_rate", 0)
            },
            "recommendations": self._generate_system_recommendations(
                kb_stats, failure_stats, success_stats, app_stats
            )
        }
    
    def _generate_system_recommendations(
        self,
        kb_stats: Dict[str, Any],
        failure_stats: Dict[str, Any],
        success_stats: Dict[str, Any],
        app_stats: Dict[str, Any]
    ) -> List[str]:
        recommendations = []
        
        if failure_stats.get("average_fix_success_rate", 0) < 0.7:
            recommendations.append("失败修复成功率较低，建议改进修复策略")
        
        if success_stats.get("total_patterns", 0) < 5:
            recommendations.append("成功模式数量较少，建议从更多高质量代码中提取模式")
        
        if app_stats.get("success_rate", 0) < 0.6:
            recommendations.append("知识应用成功率较低，建议优化知识推荐算法")
        
        if kb_stats.get("total_knowledge", 0) < 50:
            recommendations.append("知识库规模较小，建议持续积累知识")
        
        if not recommendations:
            recommendations.append("系统运行良好，建议持续监控和优化")
        
        return recommendations


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="知识学习系统 - 模式识别、最佳实践提取、修复策略学习和质量评估"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    recognize_parser = subparsers.add_parser("recognize", help="识别代码模式")
    recognize_parser.add_argument("file", help="要分析的文件路径")
    recognize_parser.add_argument("--category", choices=[c.value for c in PatternCategory])
    
    practice_parser = subparsers.add_parser("practices", help="获取最佳实践")
    practice_parser.add_argument("--category", choices=[c.value for c in PracticeCategory])
    practice_parser.add_argument("--level", choices=[l.value for l in PracticeLevel])
    
    strategy_parser = subparsers.add_parser("strategy", help="获取修复策略")
    strategy_parser.add_argument("issue_type", help="问题类型")
    
    evaluate_parser = subparsers.add_parser("evaluate", help="评估知识质量")
    evaluate_parser.add_argument("--knowledge-id", help="特定知识ID")
    
    failure_parser = subparsers.add_parser("failure", help="失败模式分析")
    failure_parser.add_argument("--error-type", help="错误类型")
    failure_parser.add_argument("--days", type=int, default=30, help="分析天数")
    
    success_parser = subparsers.add_parser("success", help="成功模式提取")
    success_parser.add_argument("file", help="要分析的文件路径")
    
    apply_parser = subparsers.add_parser("apply", help="应用知识推荐")
    apply_parser.add_argument("--context", default="code_review", help="应用上下文")
    apply_parser.add_argument("--tags", nargs="+", help="上下文标签")
    
    report_parser = subparsers.add_parser("report", help="生成学习报告")
    
    stats_parser = subparsers.add_parser("stats", help="显示统计信息")
    
    args = parser.parse_args()
    
    system = KnowledgeLearningSystem()
    
    try:
        if args.command == "recognize":
            with open(args.file, "r", encoding="utf-8") as f:
                code = f.read()
            
            category = PatternCategory(args.category) if args.category else None
            patterns = system.pattern_recognizer.recognize_code_patterns(
                code, categories=[category] if category else None
            )
            
            print(f"\n识别到 {len(patterns)} 个模式:")
            for p in patterns[:10]:
                print(f"  - {p.pattern.name} (置信度: {p.confidence:.2f})")
        
        elif args.command == "practices":
            category = PracticeCategory(args.category) if args.category else None
            level = PracticeLevel(args.level) if args.level else None
            
            practices = system.best_practice_extractor.find_practices(
                category=category, level=level
            )
            
            print(f"\n找到 {len(practices)} 个最佳实践:")
            for p in practices[:10]:
                print(f"  - {p.title} (评分: {p.score:.2f})")
        
        elif args.command == "strategy":
            strategy = system.fix_strategy_learner.get_strategy_for_issue(args.issue_type)
            
            if strategy:
                print(f"\n推荐策略: {strategy.name}")
                print(f"描述: {strategy.description}")
                print(f"效果: {strategy.effectiveness.value}")
                print("\n修复步骤:")
                for step in strategy.fix_steps:
                    print(f"  {step['step']}. {step['action']}")
            else:
                print("未找到匹配的策略")
        
        elif args.command == "evaluate":
            if args.knowledge_id:
                kb = system.knowledge_base
                knowledge = kb.get_knowledge(args.knowledge_id)
                if knowledge:
                    score = system.quality_evaluator.evaluate_knowledge(knowledge)
                    print(f"\n知识质量评估: {args.knowledge_id}")
                    print(f"总体评分: {score.overall_score:.2f}")
                    print(f"质量等级: {score.level.value}")
                    print(f"优势: {', '.join(score.strengths) if score.strengths else '无'}")
                    print(f"劣势: {', '.join(score.weaknesses) if score.weaknesses else '无'}")
                else:
                    print(f"知识不存在: {args.knowledge_id}")
            else:
                evaluation = system.evaluate_knowledge_quality()
                print("\n知识库质量评估:")
                print(f"  总评估数: {evaluation['evaluation'].get('total_evaluated', 0)}")
                print(f"  平均分: {evaluation['evaluation'].get('average_score', 0):.2f}")
                print(f"  淘汰候选: {evaluation['retirement_candidates']}")
        
        elif args.command == "failure":
            if args.error_type:
                pattern = system.failure_learner.get_failure_pattern(args.error_type)
                if pattern:
                    print(f"\n失败模式: {pattern.name}")
                    print(f"类别: {pattern.category.value}")
                    print(f"严重程度: {pattern.severity.value}")
                    print(f"发生次数: {pattern.occurrence_count}")
                    print(f"修复成功率: {pattern.fix_success_rate:.0%}")
                    print("\n修复方法:")
                    for method in pattern.fix_methods[:3]:
                        print(f"  - {method.get('method', '')}: {method.get('success_rate', 0):.0%}")
                else:
                    print("未找到匹配的失败模式")
            else:
                trends = system.analyze_failure_trends(args.days)
                print(f"\n失败趋势分析 (最近 {args.days} 天):")
                print(f"  总失败数: {trends['total_failures']}")
                print(f"  成功率: {trends['success_rate']:.0%}")
                print(f"  平均修复时间: {trends['average_fix_time']:.1f}分钟")
                print("\n按类别分布:")
                for cat, count in trends['by_category'].items():
                    print(f"  {cat}: {count}")
        
        elif args.command == "success":
            with open(args.file, "r", encoding="utf-8") as f:
                code = f.read()
            
            result = system.extract_success_pattern(code)
            
            if result.get("success"):
                print(f"\n成功提取模式:")
                print(f"  模式ID: {result['pattern_id']}")
                print(f"  模式名称: {result['pattern_name']}")
                print(f"  质量等级: {result['quality_level']}")
                print(f"  质量评分:")
                for metric, score in result['metrics'].items():
                    print(f"    {metric}: {score:.2f}")
            else:
                print(f"\n提取失败: {result.get('reason', '未知原因')}")
                if 'metrics' in result:
                    print("质量评分:")
                    for metric, score in result['metrics'].items():
                        print(f"  {metric}: {score:.2f}")
        
        elif args.command == "apply":
            context = {
                "tags": args.tags or []
            }
            
            recommendations = system.get_knowledge_recommendations(
                context, args.context
            )
            
            print(f"\n知识推荐 (上下文: {args.context}):")
            if recommendations:
                for i, rec in enumerate(recommendations[:10], 1):
                    print(f"\n{i}. {rec['title']}")
                    print(f"   相关度: {rec['relevance_score']:.2f}")
                    print(f"   适用性: {rec['applicability_score']:.2f}")
                    print(f"   优先级: {rec['priority']}")
                    if rec['expected_benefits']:
                        print(f"   预期收益: {', '.join(rec['expected_benefits'][:2])}")
            else:
                print("未找到匹配的知识推荐")
        
        elif args.command == "report":
            report = system.generate_learning_report()
            
            print("\n=== 知识学习系统报告 ===")
            print(f"生成时间: {report['report_generated_at']}")
            
            print("\n知识摘要:")
            ks = report['knowledge_summary']
            print(f"  总知识数: {ks['total_knowledge']}")
            print(f"  活跃知识数: {ks['active_knowledge']}")
            
            print("\n失败学习:")
            fl = report['failure_learning']
            print(f"  失败模式数: {fl['total_patterns']}")
            print(f"  失败记录数: {fl['total_records']}")
            print(f"  平均修复成功率: {fl['average_fix_success_rate']:.0%}")
            
            print("\n成功模式:")
            sp = report['success_patterns']
            print(f"  成功模式数: {sp['total_patterns']}")
            print(f"  平均置信度: {sp['average_confidence']:.2f}")
            
            print("\n知识应用:")
            ka = report['knowledge_application']
            print(f"  总应用次数: {ka['total_applications']}")
            print(f"  成功率: {ka['success_rate']:.0%}")
            
            print("\n系统建议:")
            for rec in report['recommendations']:
                print(f"  - {rec}")
        
        elif args.command == "stats":
            stats = system.get_system_statistics()
            print("\n系统统计:")
            print(f"  知识库: {stats['knowledge_base'].get('total_knowledge', 0)} 条知识")
            print(f"  模式识别: {stats['pattern_recognizer'].get('total_code_patterns', 0)} 个模式")
            print(f"  最佳实践: {stats['best_practice_extractor'].get('total_practices', 0)} 个实践")
            print(f"  修复策略: {stats['fix_strategy_learner'].get('total_strategies', 0)} 个策略")
            print(f"  失败模式: {stats['failure_learner'].get('total_patterns', 0)} 个模式")
            print(f"  成功模式: {stats['success_extractor'].get('total_patterns', 0)} 个模式")
            print(f"  知识应用: {stats['application_engine'].get('total_applications', 0)} 次")
        
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"执行错误: {e}")
        print(f"错误: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
