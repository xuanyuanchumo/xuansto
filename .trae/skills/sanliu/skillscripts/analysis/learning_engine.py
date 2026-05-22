#!/usr/bin/env python3
"""
Learning Engine - 学习引擎模块

三省六部技能系统的核心学习引擎，负责从案例中学习模式并优化知识库。

功能：
1. 失败模式学习：从失败案例中提取模式，更新修复策略
2. 成功模式学习：从成功案例中提取最佳实践
3. 模式库管理：存储、检索、更新学习到的模式
4. 学习效果评估：评估学习效果，持续优化

学习流程：
案例收集 -> 模式提取 -> 模式验证 -> 模式存储 -> 效果评估

使用示例：
    from learning_engine import LearningEngine
    
    engine = LearningEngine()
    
    # 学习失败案例
    engine.learn_from_failure(failure_case)
    
    # 学习成功案例
    engine.learn_from_success(success_case)
    
    # 获取最佳实践
    practices = engine.get_best_practices()
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
from typing import Any, Dict, List, Optional, Set, Tuple, Union

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PatternType(Enum):
    FAILURE = "failure"
    SUCCESS = "success"
    BEHAVIORAL = "behavioral"
    PERFORMANCE = "performance"
    ARCHITECTURAL = "architectural"


class LearningPhase(Enum):
    COLLECTION = "collection"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    STORAGE = "storage"
    EVALUATION = "evaluation"


class PatternStatus(Enum):
    NEW = "new"
    LEARNING = "learning"
    VALIDATED = "validated"
    DEPRECATED = "deprecated"


class ConfidenceLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class CaseSignature:
    signature_id: str
    case_type: str
    context_hash: str
    feature_vector: List[float] = field(default_factory=list)
    created_at: str = ""
    occurrence_count: int = 1


@dataclass
class LearningPattern:
    pattern_id: str
    pattern_type: PatternType
    name: str
    description: str
    signatures: List[CaseSignature] = field(default_factory=list)
    features: Dict[str, Any] = field(default_factory=dict)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    confidence_score: float = 0.0
    occurrence_count: int = 0
    success_rate: float = 0.0
    last_updated: str = ""
    status: PatternStatus = PatternStatus.NEW
    tags: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningCase:
    case_id: str
    case_type: PatternType
    timestamp: str
    context: Dict[str, Any]
    features: Dict[str, Any]
    outcome: str
    feedback: Optional[str] = None
    applied_patterns: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningResult:
    result_id: str
    pattern_id: str
    phase: LearningPhase
    confidence: float
    evidence: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class EvaluationMetrics:
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    coverage: float = 0.0
    improvement_rate: float = 0.0


class CaseCollector:
    """案例收集器
    
    负责从多种数据源收集学习案例，支持去重、清洗和验证。
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("./learning_cases")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._cases_file = self.storage_dir / "cases.json"
        self._dedup_file = self.storage_dir / "dedup_index.json"
        self._cases: List[Dict[str, Any]] = self._load_cases()
        self._dedup_index: Dict[str, str] = self._load_dedup_index()
        self._stats: Dict[str, Any] = {
            "total_collected": 0,
            "duplicates_skipped": 0,
            "invalid_skipped": 0,
            "by_type": defaultdict(int)
        }
    
    def _load_cases(self) -> List[Dict[str, Any]]:
        if self._cases_file.exists():
            try:
                with open(self._cases_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载案例数据失败: {e}")
        return []
    
    def _load_dedup_index(self) -> Dict[str, str]:
        if self._dedup_file.exists():
            try:
                with open(self._dedup_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载去重索引失败: {e}")
        return {}
    
    def _save_cases(self) -> None:
        try:
            with open(self._cases_file, "w", encoding="utf-8") as f:
                json.dump(self._cases, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存案例数据失败: {e}")
    
    def _save_dedup_index(self) -> None:
        try:
            with open(self._dedup_file, "w", encoding="utf-8") as f:
                json.dump(self._dedup_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存去重索引失败: {e}")
    
    def _create_signature(self, case: LearningCase) -> str:
        content = f"{case.case_type.value}:{json.dumps(case.context, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _validate_case(self, case: LearningCase) -> Tuple[bool, Optional[str]]:
        if not case.case_id:
            return False, "缺少案例ID"
        if not case.context:
            return False, "缺少上下文信息"
        if not case.outcome:
            return False, "缺少结果信息"
        return True, None
    
    def _clean_case(self, case: LearningCase) -> LearningCase:
        cleaned_context = {}
        for key, value in case.context.items():
            if value is not None:
                if isinstance(value, str):
                    cleaned_context[key] = value.strip()
                else:
                    cleaned_context[key] = value
        
        case.context = cleaned_context
        case.timestamp = case.timestamp or datetime.now().isoformat()
        return case
    
    def collect(
        self,
        case: LearningCase,
        skip_duplicate: bool = True
    ) -> Optional[str]:
        signature = self._create_signature(case)
        
        if skip_duplicate and signature in self._dedup_index:
            self._stats["duplicates_skipped"] += 1
            logger.debug(f"跳过重复案例: {signature[:8]}...")
            return None
        
        is_valid, error_msg = self._validate_case(case)
        if not is_valid:
            self._stats["invalid_skipped"] += 1
            logger.warning(f"跳过无效案例: {error_msg}")
            return None
        
        case = self._clean_case(case)
        
        case_dict = {
            "case_id": case.case_id,
            "case_type": case.case_type.value,
            "timestamp": case.timestamp,
            "context": case.context,
            "features": case.features,
            "outcome": case.outcome,
            "feedback": case.feedback,
            "applied_pattern": case.applied_pattern,
            "metadata": case.metadata,
            "signature": signature
        }
        
        self._cases.append(case_dict)
        self._dedup_index[signature] = case.case_id
        self._stats["total_collected"] += 1
        self._stats["by_type"][case.case_type.value] += 1
        
        self._save_cases()
        self._save_dedup_index()
        
        logger.info(f"收集案例: {case.case_id} (类型: {case.case_type.value})")
        return case.case_id
    
    def collect_batch(self, cases: List[LearningCase]) -> List[str]:
        collected_ids = []
        for case in cases:
            case_id = self.collect(case)
            if case_id:
                collected_ids.append(case_id)
        return collected_ids
    
    def get_cases(
        self,
        case_type: Optional[PatternType] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        cases = self._cases
        
        if case_type:
            cases = [c for c in cases if c.get("case_type") == case_type.value]
        
        return cases[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_cases": len(self._cases),
            "by_type": dict(self._stats["by_type"]),
            "collection_stats": {
                "total_collected": self._stats["total_collected"],
                "duplicates_skipped": self._stats["duplicates_skipped"],
                "invalid_skipped": self._stats["invalid_skipped"]
            }
        }
    
    def clear(self) -> None:
        self._cases = []
        self._dedup_index = {}
        self._stats = {
            "total_collected": 0,
            "duplicates_skipped": 0,
            "invalid_skipped": 0,
            "by_type": defaultdict(int)
        }
        self._save_cases()
        self._save_dedup_index()
        logger.info("案例数据已清空")


class PatternExtractor:
    """模式提取器
    
    从案例中提取学习模式，支持特征提取和模式识别。
    """
    
    def __init__(self):
        self._extraction_rules = self._initialize_extraction_rules()
        self._feature_weights = self._initialize_feature_weights()
    
    def _initialize_extraction_rules(self) -> Dict[str, Any]:
        return {
            "failure": {
                "error_patterns": [
                    r"(\w+Error): (.+)",
                    r"(\w+Exception): (.+)",
                    r"assertion failed: (.+)"
                ],
                "context_keys": ["error_message", "exception_type", "stack_trace", "file_path"],
                "feature_extractors": ["error_type", "error_location", "affected_components"]
            },
            "success": {
                "success_indicators": ["completed", "passed", "success"],
                "context_keys": ["operation", "duration", "resources_used"],
                "feature_extractors": ["success_factors", "optimal_conditions", "best_practices"]
            },
            "behavioral": {
                "behavior_patterns": ["sequence", "state_transition", "interaction"],
                "context_keys": ["actions", "states", "transitions"],
                "feature_extractors": ["behavior_sequence", "state_pattern", "interaction_pattern"]
            },
            "performance": {
                "metrics": ["response_time", "throughput", "resource_usage"],
                "context_keys": ["metrics", "baseline", "threshold"],
                "feature_extractors": ["performance_pattern", "bottleneck", "optimization"]
            },
            "architectural": {
                "patterns": ["layer", "component", "dependency"],
                "context_keys": ["architecture", "components", "dependencies"],
                "feature_extractors": ["architectural_pattern", "dependency_pattern", "layer_pattern"]
            }
        }
    
    def _initialize_feature_weights(self) -> Dict[str, float]:
        return {
            "error_type": 0.3,
            "error_location": 0.2,
            "affected_components": 0.2,
            "success_factors": 0.3,
            "optimal_conditions": 0.2,
            "behavior_sequence": 0.25,
            "performance_pattern": 0.3,
            "architectural_pattern": 0.25
        }
    
    def extract_pattern(
        self,
        cases: List[Dict[str, Any]],
        pattern_type: PatternType
    ) -> Optional[LearningPattern]:
        if not cases:
            return None
        
        rules = self._extraction_rules.get(pattern_type.value, {})
        if not rules:
            return None
        
        features = self._extract_features(cases, rules)
        conditions = self._extract_conditions(cases, rules)
        actions = self._extract_actions(cases, pattern_type)
        signatures = self._create_signatures(cases)
        
        pattern_id = self._generate_pattern_id(features, pattern_type)
        name = self._generate_pattern_name(features, pattern_type)
        description = self._generate_description(cases, pattern_type)
        tags = self._extract_tags(cases, rules)
        
        confidence = self._calculate_confidence(cases, features)
        
        return LearningPattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            name=name,
            description=description,
            signatures=signatures,
            features=features,
            conditions=conditions,
            actions=actions,
            confidence_score=confidence,
            occurrence_count=len(cases),
            status=PatternStatus.NEW,
            tags=tags,
            last_updated=datetime.now().isoformat()
        )
    
    def _extract_features(
        self,
        cases: List[Dict[str, Any]],
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        features = defaultdict(list)
        
        for case in cases:
            context = case.get("context", {})
            
            for key in rules.get("context_keys", []):
                if key in context:
                    features[key].append(context[key])
        
        aggregated = {}
        for key, values in features.items():
            if values:
                if isinstance(values[0], (int, float)):
                    aggregated[key] = {
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values)
                    }
                else:
                    counter = defaultdict(int)
                    for v in values:
                        if isinstance(v, str):
                            counter[v] += 1
                    aggregated[key] = dict(counter)
        
        return aggregated
    
    def _extract_conditions(
        self,
        cases: List[Dict[str, Any]],
        rules: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        conditions = []
        
        common_contexts = defaultdict(int)
        for case in cases:
            context = case.get("context", {})
            for key, value in context.items():
                if isinstance(value, (str, int, float, bool)):
                    common_contexts[f"{key}={value}"] += 1
        
        threshold = len(cases) * 0.5
        for key_value, count in common_contexts.items():
            if count >= threshold:
                key, value = key_value.split("=", 1)
                conditions.append({
                    "type": "context_match",
                    "key": key,
                    "value": value,
                    "frequency": count / len(cases)
                })
        
        return conditions[:10]
    
    def _extract_actions(
        self,
        cases: List[Dict[str, Any]],
        pattern_type: PatternType
    ) -> List[Dict[str, Any]]:
        actions = []
        
        if pattern_type == PatternType.FAILURE:
            successful_fixes = []
            for case in cases:
                if case.get("outcome") == "fixed":
                    successful_fixes.append(case.get("feedback", ""))
            
            if successful_fixes:
                actions.append({
                    "type": "fix_suggestion",
                    "description": "基于成功修复案例的建议",
                    "examples": successful_fixes[:3]
                })
        
        elif pattern_type == PatternType.SUCCESS:
            best_practices = []
            for case in cases:
                if case.get("outcome") == "success":
                    best_practices.append(case.get("feedback", ""))
            
            if best_practices:
                actions.append({
                    "type": "best_practice",
                    "description": "成功案例的最佳实践",
                    "examples": best_practices[:3]
                })
        
        return actions
    
    def _create_signatures(self, cases: List[Dict[str, Any]]) -> List[CaseSignature]:
        signatures = []
        
        for case in cases[:20]:
            context_hash = hashlib.md5(
                json.dumps(case.get("context", {}), sort_keys=True).encode()
            ).hexdigest()[:12]
            
            sig = CaseSignature(
                signature_id=f"SIG-{context_hash}",
                case_type=case.get("case_type", "unknown"),
                context_hash=context_hash,
                created_at=case.get("timestamp", datetime.now().isoformat()),
                occurrence_count=1
            )
            signatures.append(sig)
        
        return signatures
    
    def _generate_pattern_id(
        self,
        features: Dict[str, Any],
        pattern_type: PatternType
    ) -> str:
        content = f"{pattern_type.value}:{json.dumps(features, sort_keys=True)}"
        hash_val = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"pattern_{pattern_type.value}_{hash_val}"
    
    def _generate_pattern_name(
        self,
        features: Dict[str, Any],
        pattern_type: PatternType
    ) -> str:
        type_names = {
            PatternType.FAILURE: "失败模式",
            PatternType.SUCCESS: "成功模式",
            PatternType.BEHAVIORAL: "行为模式",
            PatternType.PERFORMANCE: "性能模式",
            PatternType.ARCHITECTURAL: "架构模式"
        }
        
        key_features = list(features.keys())[:3]
        if key_features:
            feature_str = "_".join(key_features)
            return f"{type_names.get(pattern_type, '模式')}_{feature_str}"
        
        return type_names.get(pattern_type, "未知模式")
    
    def _generate_description(
        self,
        cases: List[Dict[str, Any]],
        pattern_type: PatternType
    ) -> str:
        type_desc = {
            PatternType.FAILURE: "从失败案例中提取的模式",
            PatternType.SUCCESS: "从成功案例中提取的最佳实践",
            PatternType.BEHAVIORAL: "从行为观察中提取的模式",
            PatternType.PERFORMANCE: "从性能数据中提取的模式",
            PatternType.ARCHITECTURAL: "从架构分析中提取的模式"
        }
        
        return f"{type_desc.get(pattern_type, '未知模式')}，基于 {len(cases)} 个案例"
    
    def _extract_tags(
        self,
        cases: List[Dict[str, Any]],
        rules: Dict[str, Any]
    ) -> List[str]:
        tags = set()
        
        for case in cases:
            context = case.get("context", {})
            
            for key, value in context.items():
                if isinstance(value, str):
                    words = re.findall(r'\b\w+\b', value.lower())
                    for word in words:
                        if len(word) > 3:
                            tags.add(word)
        
        return list(tags)[:10]
    
    def _calculate_confidence(
        self,
        cases: List[Dict[str, Any]],
        features: Dict[str, Any]
    ) -> float:
        base_confidence = 0.3
        
        case_count_score = min(len(cases) / 10, 0.3)
        
        feature_score = min(len(features) / 5, 0.2)
        
        consistency_score = 0.2
        
        return min(base_confidence + case_count_score + feature_score + consistency_score, 1.0)


class PatternValidator:
    """模式验证器
    
    验证提取的模式是否有效，支持交叉验证和统计验证。
    """
    
    def __init__(self, validation_threshold: float = 0.6):
        self.validation_threshold = validation_threshold
        self._validation_history: List[Dict[str, Any]] = []
    
    def validate_pattern(
        self,
        pattern: LearningPattern,
        test_cases: List[Dict[str, Any]]
    ) -> Tuple[bool, Dict[str, Any]]:
        if not test_cases:
            return False, {"error": "没有测试案例"}
        
        matches = 0
        correct_matches = 0
        
        for case in test_cases:
            is_match = self._check_pattern_match(pattern, case)
            if is_match:
                matches += 1
                if self._check_outcome_match(pattern, case):
                    correct_matches += 1
        
        precision = correct_matches / matches if matches > 0 else 0
        recall = matches / len(test_cases)
        
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        validation_result = {
            "pattern_id": pattern.pattern_id,
            "total_cases": len(test_cases),
            "matched_cases": matches,
            "correct_matches": correct_matches,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "is_valid": f1_score >= self.validation_threshold
        }
        
        self._validation_history.append(validation_result)
        
        return validation_result["is_valid"], validation_result
    
    def _check_pattern_match(
        self,
        pattern: LearningPattern,
        case: Dict[str, Any]
    ) -> bool:
        context = case.get("context", {})
        
        for condition in pattern.conditions:
            key = condition.get("key")
            value = condition.get("value")
            
            if key in context:
                if str(context[key]) != str(value):
                    return False
        
        return True
    
    def _check_outcome_match(
        self,
        pattern: LearningPattern,
        case: Dict[str, Any]
    ) -> bool:
        expected_outcomes = {
            PatternType.FAILURE: ["fixed", "resolved"],
            PatternType.SUCCESS: ["success", "completed"],
            PatternType.BEHAVIORAL: ["expected", "normal"],
            PatternType.PERFORMANCE: ["improved", "optimized"],
            PatternType.ARCHITECTURAL: ["valid", "compliant"]
        }
        
        expected = expected_outcomes.get(pattern.pattern_type, [])
        return case.get("outcome", "") in expected
    
    def cross_validate(
        self,
        pattern: LearningPattern,
        cases: List[Dict[str, Any]],
        folds: int = 5
    ) -> Dict[str, Any]:
        if len(cases) < folds:
            return {"error": "案例数量不足以进行交叉验证"}
        
        fold_size = len(cases) // folds
        results = []
        
        for i in range(folds):
            test_start = i * fold_size
            test_end = test_start + fold_size
            
            test_cases = cases[test_start:test_end]
            
            is_valid, result = self.validate_pattern(pattern, test_cases)
            results.append(result)
        
        avg_precision = sum(r["precision"] for r in results) / folds
        avg_recall = sum(r["recall"] for r in results) / folds
        avg_f1 = sum(r["f1_score"] for r in results) / folds
        
        return {
            "fold_results": results,
            "average_precision": avg_precision,
            "average_recall": avg_recall,
            "average_f1_score": avg_f1,
            "is_valid": avg_f1 >= self.validation_threshold
        }
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        if not self._validation_history:
            return {"total_validations": 0}
        
        valid_count = sum(1 for v in self._validation_history if v.get("is_valid"))
        
        return {
            "total_validations": len(self._validation_history),
            "valid_patterns": valid_count,
            "validation_rate": valid_count / len(self._validation_history),
            "average_f1_score": sum(v["f1_score"] for v in self._validation_history) / len(self._validation_history)
        }


class PatternLibrary:
    """模式库
    
    管理学习到的模式，提供存储、检索、更新功能。
    """
    
    def __init__(self, library_dir: Optional[Path] = None):
        self.library_dir = library_dir or Path("./pattern_library")
        self.library_dir.mkdir(parents=True, exist_ok=True)
        
        self._patterns_file = self.library_dir / "patterns.json"
        self._index_file = self.library_dir / "pattern_index.json"
        self._patterns: Dict[str, LearningPattern] = {}
        self._index: Dict[str, List[str]] = defaultdict(list)
        
        self._load_library()
    
    def _load_library(self) -> None:
        if self._patterns_file.exists():
            try:
                with open(self._patterns_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for pattern_id, pattern_data in data.items():
                    self._patterns[pattern_id] = self._deserialize_pattern(pattern_data)
                
                logger.info(f"加载模式库: {len(self._patterns)} 个模式")
            except Exception as e:
                logger.warning(f"加载模式库失败: {e}")
        
        if self._index_file.exists():
            try:
                with open(self._index_file, "r", encoding="utf-8") as f:
                    self._index = defaultdict(list, json.load(f))
            except Exception as e:
                logger.warning(f"加载模式索引失败: {e}")
    
    def _save_library(self) -> None:
        try:
            data = {}
            for pattern_id, pattern in self._patterns.items():
                data[pattern_id] = self._serialize_pattern(pattern)
            
            with open(self._patterns_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(dict(self._index), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存模式库失败: {e}")
    
    def _serialize_pattern(self, pattern: LearningPattern) -> Dict[str, Any]:
        return {
            "pattern_id": pattern.pattern_id,
            "pattern_type": pattern.pattern_type.value,
            "name": pattern.name,
            "description": pattern.description,
            "signatures": [
                {
                    "signature_id": s.signature_id,
                    "case_type": s.case_type,
                    "context_hash": s.context_hash,
                    "created_at": s.created_at,
                    "occurrence_count": s.occurrence_count
                }
                for s in pattern.signatures
            ],
            "features": pattern.features,
            "conditions": pattern.conditions,
            "actions": pattern.actions,
            "confidence_score": pattern.confidence_score,
            "occurrence_count": pattern.occurrence_count,
            "success_rate": pattern.success_rate,
            "last_updated": pattern.last_updated,
            "status": pattern.status.value,
            "tags": pattern.tags,
            "related_patterns": pattern.related_patterns,
            "metadata": pattern.metadata
        }
    
    def _deserialize_pattern(self, data: Dict[str, Any]) -> LearningPattern:
        signatures = [
            CaseSignature(
                signature_id=s.get("signature_id", ""),
                case_type=s.get("case_type", ""),
                context_hash=s.get("context_hash", ""),
                created_at=s.get("created_at", ""),
                occurrence_count=s.get("occurrence_count", 1)
            )
            for s in data.get("signatures", [])
        ]
        
        return LearningPattern(
            pattern_id=data.get("pattern_id", ""),
            pattern_type=PatternType(data.get("pattern_type", "failure")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            signatures=signatures,
            features=data.get("features", {}),
            conditions=data.get("conditions", []),
            actions=data.get("actions", []),
            confidence_score=data.get("confidence_score", 0.0),
            occurrence_count=data.get("occurrence_count", 0),
            success_rate=data.get("success_rate", 0.0),
            last_updated=data.get("last_updated", ""),
            status=PatternStatus(data.get("status", "new")),
            tags=data.get("tags", []),
            related_patterns=data.get("related_patterns", []),
            metadata=data.get("metadata", {})
        )
    
    def add_pattern(self, pattern: LearningPattern) -> None:
        self._patterns[pattern.pattern_id] = pattern
        
        self._index["by_type"][pattern.pattern_type.value].append(pattern.pattern_id)
        
        for tag in pattern.tags:
            self._index["by_tag"][tag].append(pattern.pattern_id)
        
        self._save_library()
        logger.info(f"添加模式: {pattern.pattern_id}")
    
    def update_pattern(
        self,
        pattern_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        if pattern_id not in self._patterns:
            return False
        
        pattern = self._patterns[pattern_id]
        
        for key, value in updates.items():
            if hasattr(pattern, key):
                setattr(pattern, key, value)
        
        pattern.last_updated = datetime.now().isoformat()
        self._save_library()
        
        return True
    
    def get_pattern(self, pattern_id: str) -> Optional[LearningPattern]:
        return self._patterns.get(pattern_id)
    
    def get_all_patterns(self) -> List[LearningPattern]:
        return list(self._patterns.values())
    
    def find_patterns(
        self,
        pattern_type: Optional[PatternType] = None,
        tags: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        status: Optional[PatternStatus] = None
    ) -> List[LearningPattern]:
        results = []
        
        for pattern in self._patterns.values():
            if pattern_type and pattern.pattern_type != pattern_type:
                continue
            
            if tags and not any(tag in pattern.tags for tag in tags):
                continue
            
            if pattern.confidence_score < min_confidence:
                continue
            
            if status and pattern.status != status:
                continue
            
            results.append(pattern)
        
        return results
    
    def find_matching_patterns(
        self,
        context: Dict[str, Any],
        pattern_type: Optional[PatternType] = None
    ) -> List[Tuple[LearningPattern, float]]:
        matches = []
        
        for pattern in self._patterns.values():
            if pattern_type and pattern.pattern_type != pattern_type:
                continue
            
            score = self._calculate_match_score(pattern, context)
            
            if score > 0:
                matches.append((pattern, score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def _calculate_match_score(
        self,
        pattern: LearningPattern,
        context: Dict[str, Any]
    ) -> float:
        score = 0.0
        
        for condition in pattern.conditions:
            key = condition.get("key")
            value = condition.get("value")
            frequency = condition.get("frequency", 0.5)
            
            if key in context:
                if str(context[key]) == str(value):
                    score += frequency * 0.3
        
        for tag in pattern.tags:
            for key, value in context.items():
                if isinstance(value, str) and tag in value.lower():
                    score += 0.1
                    break
        
        score += pattern.confidence_score * 0.3
        
        return min(score, 1.0)
    
    def record_pattern_application(
        self,
        pattern_id: str,
        success: bool
    ) -> None:
        if pattern_id not in self._patterns:
            return
        
        pattern = self._patterns[pattern_id]
        pattern.occurrence_count += 1
        
        if success:
            current_successes = pattern.success_rate * (pattern.occurrence_count - 1)
            pattern.success_rate = (current_successes + 1) / pattern.occurrence_count
        else:
            current_successes = pattern.success_rate * (pattern.occurrence_count - 1)
            pattern.success_rate = current_successes / pattern.occurrence_count
        
        if pattern.occurrence_count >= 5 and pattern.success_rate >= 0.7:
            pattern.status = PatternStatus.VALIDATED
        elif pattern.occurrence_count >= 2:
            pattern.status = PatternStatus.LEARNING
        
        self._save_library()
    
    def remove_pattern(self, pattern_id: str) -> bool:
        if pattern_id not in self._patterns:
            return False
        
        pattern = self._patterns[pattern_id]
        
        if pattern.pattern_type.value in self._index["by_type"]:
            if pattern_id in self._index["by_type"][pattern.pattern_type.value]:
                self._index["by_type"][pattern.pattern_type.value].remove(pattern_id)
        
        for tag in pattern.tags:
            if tag in self._index["by_tag"]:
                if pattern_id in self._index["by_tag"][tag]:
                    self._index["by_tag"][tag].remove(pattern_id)
        
        del self._patterns[pattern_id]
        self._save_library()
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        total = len(self._patterns)
        if total == 0:
            return {"total_patterns": 0}
        
        by_type: Dict[str, int] = defaultdict(int)
        by_status: Dict[str, int] = defaultdict(int)
        
        for pattern in self._patterns.values():
            by_type[pattern.pattern_type.value] += 1
            by_status[pattern.status.value] += 1
        
        return {
            "total_patterns": total,
            "by_type": dict(by_type),
            "by_status": dict(by_status),
            "average_confidence": sum(p.confidence_score for p in self._patterns.values()) / total,
            "average_success_rate": sum(p.success_rate for p in self._patterns.values()) / total,
            "validated_patterns": by_status.get("validated", 0)
        }
    
    def export_library(self, output_path: str) -> None:
        data = {
            "exported_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "patterns": [
                self._serialize_pattern(p)
                for p in self._patterns.values()
            ]
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"模式库已导出到: {output_path}")


class LearningEvaluator:
    """学习效果评估器
    
    评估学习引擎的效果，提供多种评估指标。
    """
    
    def __init__(self):
        self._evaluation_history: List[Dict[str, Any]] = []
        self._baseline_metrics: Optional[EvaluationMetrics] = None
    
    def evaluate(
        self,
        patterns: List[LearningPattern],
        test_cases: List[Dict[str, Any]]
    ) -> EvaluationMetrics:
        if not patterns or not test_cases:
            return EvaluationMetrics()
        
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0
        
        for case in test_cases:
            matched = False
            correct = False
            
            for pattern in patterns:
                if self._case_matches_pattern(case, pattern):
                    matched = True
                    if self._outcome_is_correct(case, pattern):
                        correct = True
                    break
            
            expected_positive = case.get("outcome") in ["success", "fixed", "resolved"]
            
            if matched and expected_positive:
                if correct:
                    true_positives += 1
                else:
                    false_positives += 1
            elif not matched and expected_positive:
                false_negatives += 1
            elif not matched and not expected_positive:
                true_negatives += 1
        
        accuracy = (true_positives + true_negatives) / len(test_cases) if test_cases else 0
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        coverage = sum(1 for case in test_cases if any(
            self._case_matches_pattern(case, p) for p in patterns
        )) / len(test_cases) if test_cases else 0
        
        improvement_rate = 0.0
        if self._baseline_metrics:
            if self._baseline_metrics.f1_score > 0:
                improvement_rate = (f1_score - self._baseline_metrics.f1_score) / self._baseline_metrics.f1_score
        
        metrics = EvaluationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            coverage=coverage,
            improvement_rate=improvement_rate
        )
        
        self._evaluation_history.append({
            "timestamp": datetime.now().isoformat(),
            "patterns_count": len(patterns),
            "test_cases_count": len(test_cases),
            "metrics": {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
                "coverage": coverage,
                "improvement_rate": improvement_rate
            }
        })
        
        return metrics
    
    def _case_matches_pattern(
        self,
        case: Dict[str, Any],
        pattern: LearningPattern
    ) -> bool:
        context = case.get("context", {})
        
        for condition in pattern.conditions:
            key = condition.get("key")
            value = condition.get("value")
            
            if key in context:
                if str(context[key]) != str(value):
                    return False
        
        return True
    
    def _outcome_is_correct(
        self,
        case: Dict[str, Any],
        pattern: LearningPattern
    ) -> bool:
        expected_outcomes = {
            PatternType.FAILURE: ["fixed", "resolved"],
            PatternType.SUCCESS: ["success", "completed"],
            PatternType.BEHAVIORAL: ["expected", "normal"],
            PatternType.PERFORMANCE: ["improved", "optimized"],
            PatternType.ARCHITECTURAL: ["valid", "compliant"]
        }
        
        expected = expected_outcomes.get(pattern.pattern_type, [])
        return case.get("outcome", "") in expected
    
    def set_baseline(self, metrics: EvaluationMetrics) -> None:
        self._baseline_metrics = metrics
    
    def get_evaluation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._evaluation_history[-limit:]
    
    def get_improvement_trend(self) -> Dict[str, Any]:
        if len(self._evaluation_history) < 2:
            return {"trend": "insufficient_data"}
        
        recent = self._evaluation_history[-5:]
        f1_scores = [e["metrics"]["f1_score"] for e in recent]
        
        if len(f1_scores) >= 2:
            if f1_scores[-1] > f1_scores[0]:
                trend = "improving"
            elif f1_scores[-1] < f1_scores[0]:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "recent_f1_scores": f1_scores,
            "average_f1_score": sum(f1_scores) / len(f1_scores),
            "improvement_rate": (f1_scores[-1] - f1_scores[0]) / f1_scores[0] if f1_scores[0] > 0 else 0
        }
    
    def generate_evaluation_report(self) -> Dict[str, Any]:
        if not self._evaluation_history:
            return {"status": "no_evaluations"}
        
        latest = self._evaluation_history[-1]
        trend = self.get_improvement_trend()
        
        return {
            "generated_at": datetime.now().isoformat(),
            "latest_evaluation": latest,
            "trend_analysis": trend,
            "total_evaluations": len(self._evaluation_history),
            "recommendations": self._generate_recommendations(latest, trend)
        }
    
    def _generate_recommendations(
        self,
        latest: Dict[str, Any],
        trend: Dict[str, Any]
    ) -> List[str]:
        recommendations = []
        
        metrics = latest.get("metrics", {})
        
        if metrics.get("precision", 0) < 0.7:
            recommendations.append("精确度较低，建议增加模式条件以提高匹配准确性")
        
        if metrics.get("recall", 0) < 0.7:
            recommendations.append("召回率较低，建议扩展模式覆盖范围")
        
        if metrics.get("coverage", 0) < 0.5:
            recommendations.append("覆盖率较低，建议收集更多样化的案例")
        
        if trend.get("trend") == "declining":
            recommendations.append("学习效果呈下降趋势，建议检查数据质量或调整学习策略")
        
        if not recommendations:
            recommendations.append("学习效果良好，建议持续监控并优化")
        
        return recommendations


class LearningEngine:
    """学习引擎主类
    
    整合案例收集、模式提取、验证、存储和评估的完整学习流程。
    """
    
    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        library_dir: Optional[Path] = None
    ):
        self.collector = CaseCollector(storage_dir)
        self.extractor = PatternExtractor()
        self.validator = PatternValidator()
        self.library = PatternLibrary(library_dir)
        self.evaluator = LearningEvaluator()
        
        self._learning_sessions: List[Dict[str, Any]] = []
        self._session_id = 0
    
    def learn_from_failure(
        self,
        context: Dict[str, Any],
        outcome: str,
        feedback: Optional[str] = None,
        applied_pattern: Optional[str] = None
    ) -> LearningResult:
        case = LearningCase(
            case_id=self._generate_case_id(),
            case_type=PatternType.FAILURE,
            timestamp=datetime.now().isoformat(),
            context=context,
            features=self._extract_features_from_context(context),
            outcome=outcome,
            feedback=feedback,
            applied_pattern=applied_pattern
        )
        
        case_id = self.collector.collect(case)
        
        if not case_id:
            return LearningResult(
                result_id="result_none",
                pattern_id="",
                phase=LearningPhase.COLLECTION,
                confidence=0.0,
                warnings=["案例收集失败或重复"]
            )
        
        failure_cases = self.collector.get_cases(PatternType.FAILURE, limit=100)
        
        pattern = self.extractor.extract_pattern(failure_cases, PatternType.FAILURE)
        
        if not pattern:
            return LearningResult(
                result_id=self._generate_result_id(),
                pattern_id="",
                phase=LearningPhase.EXTRACTION,
                confidence=0.0,
                warnings=["模式提取失败"]
            )
        
        existing_patterns = self.library.find_matching_patterns(context, PatternType.FAILURE)
        
        if existing_patterns:
            existing_pattern = existing_patterns[0][0]
            self.library.update_pattern(
                existing_pattern.pattern_id,
                {
                    "occurrence_count": existing_pattern.occurrence_count + 1,
                    "success_rate": self._update_success_rate(
                        existing_pattern.success_rate,
                        existing_pattern.occurrence_count,
                        outcome in ["fixed", "resolved"]
                    )
                }
            )
            
            return LearningResult(
                result_id=self._generate_result_id(),
                pattern_id=existing_pattern.pattern_id,
                phase=LearningPhase.STORAGE,
                confidence=existing_patterns[0][1],
                evidence=[f"更新现有模式: {existing_pattern.name}"],
                suggestions=existing_pattern.actions[:3] if existing_pattern.actions else []
            )
        
        is_valid, validation_result = self.validator.validate_pattern(
            pattern,
            failure_cases[-20:] if len(failure_cases) >= 20 else failure_cases
        )
        
        if is_valid:
            pattern.status = PatternStatus.LEARNING
            self.library.add_pattern(pattern)
            
            return LearningResult(
                result_id=self._generate_result_id(),
                pattern_id=pattern.pattern_id,
                phase=LearningPhase.STORAGE,
                confidence=pattern.confidence_score,
                evidence=[f"创建新模式: {pattern.name}"],
                suggestions=pattern.actions[:3] if pattern.actions else []
            )
        else:
            return LearningResult(
                result_id=self._generate_result_id(),
                pattern_id=pattern.pattern_id,
                phase=LearningPhase.VALIDATION,
                confidence=validation_result.get("f1_score", 0),
                warnings=["模式验证未通过"],
                evidence=[f"验证结果: {validation_result}"]
            )
    
    def learn_from_success(
        self,
        context: Dict[str, Any],
        outcome: str,
        feedback: Optional[str] = None,
        best_practices: Optional[List[str]] = None
    ) -> LearningResult:
        case = LearningCase(
            case_id=self._generate_case_id(),
            case_type=PatternType.SUCCESS,
            timestamp=datetime.now().isoformat(),
            context=context,
            features=self._extract_features_from_context(context),
            outcome=outcome,
            feedback=feedback,
            metadata={"best_practices": best_practices or []}
        )
        
        case_id = self.collector.collect(case)
        
        if not case_id:
            return LearningResult(
                result_id="result_none",
                pattern_id="",
                phase=LearningPhase.COLLECTION,
                confidence=0.0,
                warnings=["案例收集失败或重复"]
            )
        
        success_cases = self.collector.get_cases(PatternType.SUCCESS, limit=100)
        
        pattern = self.extractor.extract_pattern(success_cases, PatternType.SUCCESS)
        
        if not pattern:
            return LearningResult(
                result_id=self._generate_result_id(),
                pattern_id="",
                phase=LearningPhase.EXTRACTION,
                confidence=0.0,
                warnings=["模式提取失败"]
            )
        
        existing_patterns = self.library.find_matching_patterns(context, PatternType.SUCCESS)
        
        if existing_patterns:
            existing_pattern = existing_patterns[0][0]
            self.library.update_pattern(
                existing_pattern.pattern_id,
                {
                    "occurrence_count": existing_pattern.occurrence_count + 1,
                    "success_rate": self._update_success_rate(
                        existing_pattern.success_rate,
                        existing_pattern.occurrence_count,
                        outcome in ["success", "completed"]
                    )
                }
            )
            
            return LearningResult(
                result_id=self._generate_result_id(),
                pattern_id=existing_pattern.pattern_id,
                phase=LearningPhase.STORAGE,
                confidence=existing_patterns[0][1],
                evidence=[f"更新最佳实践: {existing_pattern.name}"],
                suggestions=existing_pattern.actions[:3] if existing_pattern.actions else []
            )
        
        is_valid, validation_result = self.validator.validate_pattern(
            pattern,
            success_cases[-20:] if len(success_cases) >= 20 else success_cases
        )
        
        if is_valid:
            pattern.status = PatternStatus.LEARNING
            self.library.add_pattern(pattern)
            
            return LearningResult(
                result_id=self._generate_result_id(),
                pattern_id=pattern.pattern_id,
                phase=LearningPhase.STORAGE,
                confidence=pattern.confidence_score,
                evidence=[f"创建最佳实践: {pattern.name}"],
                suggestions=pattern.actions[:3] if pattern.actions else []
            )
        else:
            return LearningResult(
                result_id=self._generate_result_id(),
                pattern_id=pattern.pattern_id,
                phase=LearningPhase.VALIDATION,
                confidence=validation_result.get("f1_score", 0),
                warnings=["模式验证未通过"],
                evidence=[f"验证结果: {validation_result}"]
            )
    
    def batch_learn(
        self,
        cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        self._session_id += 1
        session_start = datetime.now()
        
        results = {
            "session_id": self._session_id,
            "started_at": session_start.isoformat(),
            "total_cases": len(cases),
            "by_type": defaultdict(int),
            "patterns_created": 0,
            "patterns_updated": 0,
            "errors": []
        }
        
        for case_data in cases:
            case_type_str = case_data.get("case_type", "failure")
            try:
                case_type = PatternType(case_type_str)
            except ValueError:
                results["errors"].append(f"无效的案例类型: {case_type_str}")
                continue
            
            if case_type == PatternType.FAILURE:
                result = self.learn_from_failure(
                    context=case_data.get("context", {}),
                    outcome=case_data.get("outcome", ""),
                    feedback=case_data.get("feedback"),
                    applied_pattern=case_data.get("applied_pattern")
                )
            else:
                result = self.learn_from_success(
                    context=case_data.get("context", {}),
                    outcome=case_data.get("outcome", ""),
                    feedback=case_data.get("feedback"),
                    best_practices=case_data.get("best_practices")
                )
            
            results["by_type"][case_type_str] += 1
            
            if result.phase == LearningPhase.STORAGE:
                if "更新" in str(result.evidence):
                    results["patterns_updated"] += 1
                else:
                    results["patterns_created"] += 1
        
        session_end = datetime.now()
        results["completed_at"] = session_end.isoformat()
        results["duration_seconds"] = (session_end - session_start).total_seconds()
        results["by_type"] = dict(results["by_type"])
        
        self._learning_sessions.append(results)
        
        return results
    
    def get_best_practices(
        self,
        pattern_type: Optional[PatternType] = None,
        min_confidence: float = 0.7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        patterns = self.library.find_patterns(
            pattern_type=pattern_type,
            min_confidence=min_confidence,
            status=PatternStatus.VALIDATED
        )
        
        patterns.sort(key=lambda p: p.success_rate, reverse=True)
        
        practices = []
        for pattern in patterns[:limit]:
            practice = {
                "pattern_id": pattern.pattern_id,
                "name": pattern.name,
                "description": pattern.description,
                "confidence_score": pattern.confidence_score,
                "success_rate": pattern.success_rate,
                "occurrence_count": pattern.occurrence_count,
                "actions": pattern.actions,
                "tags": pattern.tags,
                "recommendation_level": self._get_recommendation_level(pattern)
            }
            practices.append(practice)
        
        return practices
    
    def _get_recommendation_level(self, pattern: LearningPattern) -> str:
        if pattern.success_rate >= 0.9 and pattern.occurrence_count >= 10:
            return "highly_recommended"
        elif pattern.success_rate >= 0.8 and pattern.occurrence_count >= 5:
            return "recommended"
        elif pattern.success_rate >= 0.7:
            return "suggested"
        else:
            return "experimental"
    
    def apply_pattern(
        self,
        context: Dict[str, Any],
        pattern_type: Optional[PatternType] = None
    ) -> Dict[str, Any]:
        matches = self.library.find_matching_patterns(context, pattern_type)
        
        if not matches:
            return {
                "status": "no_match",
                "message": "没有找到匹配的模式"
            }
        
        best_match = matches[0]
        pattern = best_match[0]
        confidence = best_match[1]
        
        return {
            "status": "success",
            "pattern_id": pattern.pattern_id,
            "pattern_name": pattern.name,
            "confidence": confidence,
            "actions": pattern.actions,
            "conditions": pattern.conditions,
            "evidence": [
                f"模式类型: {pattern.pattern_type.value}",
                f"历史成功率: {pattern.success_rate:.0%}",
                f"应用次数: {pattern.occurrence_count}"
            ],
            "warnings": self._generate_application_warnings(pattern, confidence)
        }
    
    def _generate_application_warnings(
        self,
        pattern: LearningPattern,
        confidence: float
    ) -> List[str]:
        warnings = []
        
        if confidence < 0.5:
            warnings.append("匹配置信度较低，建议人工验证")
        
        if pattern.status == PatternStatus.NEW:
            warnings.append("这是新模式，建议谨慎应用")
        
        if pattern.occurrence_count < 3:
            warnings.append("该模式历史数据较少")
        
        if pattern.success_rate < 0.5:
            warnings.append("该模式历史成功率较低")
        
        return warnings
    
    def record_application_result(
        self,
        pattern_id: str,
        success: bool,
        feedback: Optional[str] = None
    ) -> None:
        self.library.record_pattern_application(pattern_id, success)
        
        if feedback:
            pattern = self.library.get_pattern(pattern_id)
            if pattern:
                if "feedback_history" not in pattern.metadata:
                    pattern.metadata["feedback_history"] = []
                pattern.metadata["feedback_history"].append({
                    "timestamp": datetime.now().isoformat(),
                    "success": success,
                    "feedback": feedback
                })
                self.library.update_pattern(pattern_id, {"metadata": pattern.metadata})
    
    def evaluate_learning(self) -> Dict[str, Any]:
        all_cases = self.collector.get_cases(limit=1000)
        all_patterns = self.library.get_all_patterns()
        
        metrics = self.evaluator.evaluate(all_patterns, all_cases)
        
        evaluation_report = self.evaluator.generate_evaluation_report()
        
        return {
            "metrics": {
                "accuracy": metrics.accuracy,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1_score": metrics.f1_score,
                "coverage": metrics.coverage,
                "improvement_rate": metrics.improvement_rate
            },
            "evaluation_report": evaluation_report,
            "library_statistics": self.library.get_statistics(),
            "collection_statistics": self.collector.get_statistics()
        }
    
    def optimize_patterns(self) -> Dict[str, Any]:
        optimizations = {
            "deprecated": 0,
            "merged": 0,
            "promoted": 0,
            "details": []
        }
        
        for pattern in self.library.get_all_patterns():
            if pattern.success_rate < 0.3 and pattern.occurrence_count >= 10:
                self.library.update_pattern(
                    pattern.pattern_id,
                    {"status": PatternStatus.DEPRECATED}
                )
                optimizations["deprecated"] += 1
                optimizations["details"].append({
                    "pattern_id": pattern.pattern_id,
                    "action": "deprecated",
                    "reason": "低成功率"
                })
            
            elif pattern.success_rate >= 0.8 and pattern.occurrence_count >= 5:
                if pattern.status != PatternStatus.VALIDATED:
                    self.library.update_pattern(
                        pattern.pattern_id,
                        {"status": PatternStatus.VALIDATED}
                    )
                    optimizations["promoted"] += 1
                    optimizations["details"].append({
                        "pattern_id": pattern.pattern_id,
                        "action": "promoted",
                        "reason": "高成功率"
                    })
        
        return optimizations
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        return {
            "collection": self.collector.get_statistics(),
            "library": self.library.get_statistics(),
            "validation": self.validator.get_validation_statistics(),
            "sessions": {
                "total_sessions": len(self._learning_sessions),
                "recent_sessions": self._learning_sessions[-5:]
            }
        }
    
    def export_knowledge(self, output_path: str) -> None:
        self.library.export_library(output_path)
    
    def _generate_case_id(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
        return f"case_{timestamp}_{random_hash}"
    
    def _generate_result_id(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"result_{timestamp}"
    
    def _extract_features_from_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        features = {}
        
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                features[key] = value
            elif isinstance(value, list):
                features[f"{key}_count"] = len(value)
            elif isinstance(value, dict):
                features[f"{key}_keys"] = list(value.keys())
        
        return features
    
    def _update_success_rate(
        self,
        current_rate: float,
        current_count: int,
        is_success: bool
    ) -> float:
        total_successes = current_rate * current_count
        if is_success:
            total_successes += 1
        return total_successes / (current_count + 1)


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="学习引擎 - 从案例中学习模式并优化知识库"
    )
    
    parser.add_argument(
        "--learn-failure",
        action="store_true",
        help="学习失败案例"
    )
    
    parser.add_argument(
        "--learn-success",
        action="store_true",
        help="学习成功案例"
    )
    
    parser.add_argument(
        "--context",
        type=str,
        help="上下文JSON字符串"
    )
    
    parser.add_argument(
        "--outcome",
        type=str,
        help="结果"
    )
    
    parser.add_argument(
        "--feedback",
        type=str,
        help="反馈信息"
    )
    
    parser.add_argument(
        "--get-practices",
        action="store_true",
        help="获取最佳实践"
    )
    
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="评估学习效果"
    )
    
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="优化模式库"
    )
    
    parser.add_argument(
        "--export",
        type=str,
        help="导出知识库"
    )
    
    parser.add_argument(
        "--statistics",
        action="store_true",
        help="显示统计信息"
    )
    
    args = parser.parse_args()
    
    engine = LearningEngine()
    
    try:
        if args.learn_failure:
            context = json.loads(args.context) if args.context else {}
            result = engine.learn_from_failure(
                context=context,
                outcome=args.outcome or "",
                feedback=args.feedback
            )
            print(f"学习结果: {result.phase.value}")
            print(f"置信度: {result.confidence:.2f}")
            if result.evidence:
                print(f"证据: {result.evidence}")
            if result.warnings:
                print(f"警告: {result.warnings}")
        
        elif args.learn_success:
            context = json.loads(args.context) if args.context else {}
            result = engine.learn_from_success(
                context=context,
                outcome=args.outcome or "",
                feedback=args.feedback
            )
            print(f"学习结果: {result.phase.value}")
            print(f"置信度: {result.confidence:.2f}")
            if result.evidence:
                print(f"证据: {result.evidence}")
        
        elif args.get_practices:
            practices = engine.get_best_practices()
            print(f"最佳实践 ({len(practices)} 个):")
            for p in practices:
                print(f"  - {p['name']}: {p['success_rate']:.0%} 成功率")
        
        elif args.evaluate:
            evaluation = engine.evaluate_learning()
            metrics = evaluation["metrics"]
            print("学习效果评估:")
            print(f"  准确率: {metrics['accuracy']:.2f}")
            print(f"  精确率: {metrics['precision']:.2f}")
            print(f"  召回率: {metrics['recall']:.2f}")
            print(f"  F1分数: {metrics['f1_score']:.2f}")
            print(f"  覆盖率: {metrics['coverage']:.2f}")
        
        elif args.optimize:
            result = engine.optimize_patterns()
            print(f"优化完成:")
            print(f"  废弃模式: {result['deprecated']}")
            print(f"  合并模式: {result['merged']}")
            print(f"  提升模式: {result['promoted']}")
        
        elif args.export:
            engine.export_knowledge(args.export)
            print(f"知识库已导出到: {args.export}")
        
        elif args.statistics:
            stats = engine.get_learning_statistics()
            print("学习统计:")
            print(f"  收集统计: {stats['collection']}")
            print(f"  模式库统计: {stats['library']}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"执行错误: {e}")
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
