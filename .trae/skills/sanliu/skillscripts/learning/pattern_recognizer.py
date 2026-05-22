#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式识别器 - Pattern Recognizer

实现成功模式、失败模式、优化模式的识别算法，并提供模式置信度评估。

核心功能:
- 成功模式识别
- 失败模式识别
- 优化模式识别
- 模式置信度评估
- 模式相似度计算
- 模式聚类分析
"""

import json
import logging
import re
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
import hashlib


class PatternType(Enum):
    """模式类型枚举"""
    SUCCESS = "success"
    FAILURE = "failure"
    OPTIMIZATION = "optimization"
    ANTI_PATTERN = "anti_pattern"
    HYBRID = "hybrid"


class PatternConfidence(Enum):
    """模式置信度枚举"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


@dataclass
class RecognizedPattern:
    """识别出的模式数据类"""
    pattern_id: str
    pattern_type: PatternType
    name: str
    description: str
    confidence: PatternConfidence
    confidence_score: float
    occurrences: int
    first_seen: datetime
    last_seen: datetime
    features: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type.value,
            "name": self.name,
            "description": self.description,
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "occurrences": self.occurrences,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "features": self.features,
            "context": self.context,
            "examples": self.examples,
            "related_patterns": self.related_patterns,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecognizedPattern':
        return cls(
            pattern_id=data["pattern_id"],
            pattern_type=PatternType(data["pattern_type"]),
            name=data["name"],
            description=data["description"],
            confidence=PatternConfidence(data["confidence"]),
            confidence_score=data["confidence_score"],
            occurrences=data["occurrences"],
            first_seen=datetime.fromisoformat(data["first_seen"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
            features=data.get("features", {}),
            context=data.get("context", {}),
            examples=data.get("examples", []),
            related_patterns=data.get("related_patterns", []),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class PatternFeature:
    """模式特征数据类"""
    feature_name: str
    feature_value: Any
    importance: float
    frequency: int
    stability: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_name": self.feature_name,
            "feature_value": self.feature_value,
            "importance": self.importance,
            "frequency": self.frequency,
            "stability": self.stability
        }


class PatternRecognizer:
    """模式识别器"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self._storage_path = Path(storage_path) if storage_path else None
        self._logger = logging.getLogger('PatternRecognizer')
        
        self._patterns: Dict[str, RecognizedPattern] = {}
        self._feature_extractors: Dict[str, Callable] = {}
        self._pattern_cache: Dict[str, List[RecognizedPattern]] = defaultdict(list)
        
        self._success_threshold = 0.8
        self._failure_threshold = 0.3
        self._optimization_threshold = 0.6
        
        self._register_default_extractors()
        
        if self._storage_path:
            self._load_patterns()
    
    def _register_default_extractors(self) -> None:
        """注册默认特征提取器"""
        self._feature_extractors['code_structure'] = self._extract_code_structure_features
        self._feature_extractors['execution_context'] = self._extract_execution_context_features
        self._feature_extractors['performance_metrics'] = self._extract_performance_features
        self._feature_extractors['error_patterns'] = self._extract_error_features
        self._feature_extractors['temporal_patterns'] = self._extract_temporal_features
    
    def recognize_success_pattern(
        self,
        execution_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[RecognizedPattern]:
        """识别成功模式
        
        Args:
            execution_data: 执行数据
            context: 上下文信息
        
        Returns:
            识别出的成功模式
        """
        success_indicators = self._extract_success_indicators(execution_data)
        
        if not self._is_success_pattern(success_indicators):
            return None
        
        features = self._extract_features(execution_data, context)
        pattern_signature = self._generate_pattern_signature(features, PatternType.SUCCESS)
        
        existing_pattern = self._find_similar_pattern(pattern_signature, PatternType.SUCCESS)
        
        if existing_pattern:
            existing_pattern.occurrences += 1
            existing_pattern.last_seen = datetime.now()
            existing_pattern.confidence_score = self._update_confidence_score(
                existing_pattern.confidence_score,
                success_indicators['success_rate']
            )
            existing_pattern.confidence = self._calculate_confidence_level(
                existing_pattern.confidence_score
            )
            existing_pattern.examples.append({
                "timestamp": datetime.now().isoformat(),
                "data": execution_data
            })
            
            if len(existing_pattern.examples) > 10:
                existing_pattern.examples = existing_pattern.examples[-10:]
            
            return existing_pattern
        
        pattern_id = f"SUCCESS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(pattern_signature.encode()).hexdigest()[:8]}"
        
        pattern = RecognizedPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.SUCCESS,
            name=self._generate_pattern_name(features, PatternType.SUCCESS),
            description=self._generate_pattern_description(features, success_indicators),
            confidence=self._calculate_confidence_level(success_indicators['success_rate']),
            confidence_score=success_indicators['success_rate'],
            occurrences=1,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            features=features,
            context=context or {},
            examples=[{
                "timestamp": datetime.now().isoformat(),
                "data": execution_data
            }],
            tags=self._extract_tags(features, PatternType.SUCCESS)
        )
        
        self._patterns[pattern_id] = pattern
        self._pattern_cache[PatternType.SUCCESS.value].append(pattern)
        
        if self._storage_path:
            self._save_patterns()
        
        self._logger.info(f"识别到新的成功模式: {pattern.name} (置信度: {pattern.confidence.value})")
        return pattern
    
    def recognize_failure_pattern(
        self,
        execution_data: Dict[str, Any],
        error_info: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[RecognizedPattern]:
        """识别失败模式
        
        Args:
            execution_data: 执行数据
            error_info: 错误信息
            context: 上下文信息
        
        Returns:
            识别出的失败模式
        """
        failure_indicators = self._extract_failure_indicators(execution_data, error_info)
        
        if not self._is_failure_pattern(failure_indicators):
            return None
        
        features = self._extract_features(execution_data, context)
        features.update(self._extract_error_features(error_info) if error_info else {})
        
        pattern_signature = self._generate_pattern_signature(features, PatternType.FAILURE)
        
        existing_pattern = self._find_similar_pattern(pattern_signature, PatternType.FAILURE)
        
        if existing_pattern:
            existing_pattern.occurrences += 1
            existing_pattern.last_seen = datetime.now()
            existing_pattern.confidence_score = self._update_confidence_score(
                existing_pattern.confidence_score,
                1.0 - failure_indicators['failure_rate']
            )
            existing_pattern.confidence = self._calculate_confidence_level(
                existing_pattern.confidence_score
            )
            existing_pattern.examples.append({
                "timestamp": datetime.now().isoformat(),
                "data": execution_data,
                "error": error_info
            })
            
            if len(existing_pattern.examples) > 10:
                existing_pattern.examples = existing_pattern.examples[-10:]
            
            return existing_pattern
        
        pattern_id = f"FAILURE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(pattern_signature.encode()).hexdigest()[:8]}"
        
        pattern = RecognizedPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.FAILURE,
            name=self._generate_pattern_name(features, PatternType.FAILURE),
            description=self._generate_failure_description(features, failure_indicators, error_info),
            confidence=self._calculate_confidence_level(1.0 - failure_indicators['failure_rate']),
            confidence_score=1.0 - failure_indicators['failure_rate'],
            occurrences=1,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            features=features,
            context=context or {},
            examples=[{
                "timestamp": datetime.now().isoformat(),
                "data": execution_data,
                "error": error_info
            }],
            tags=self._extract_tags(features, PatternType.FAILURE)
        )
        
        self._patterns[pattern_id] = pattern
        self._pattern_cache[PatternType.FAILURE.value].append(pattern)
        
        if self._storage_path:
            self._save_patterns()
        
        self._logger.info(f"识别到新的失败模式: {pattern.name} (置信度: {pattern.confidence.value})")
        return pattern
    
    def recognize_optimization_pattern(
        self,
        before_data: Dict[str, Any],
        after_data: Dict[str, Any],
        optimization_type: str = "general",
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[RecognizedPattern]:
        """识别优化模式
        
        Args:
            before_data: 优化前的数据
            after_data: 优化后的数据
            optimization_type: 优化类型
            context: 上下文信息
        
        Returns:
            识别出的优化模式
        """
        optimization_indicators = self._extract_optimization_indicators(before_data, after_data)
        
        if not self._is_optimization_pattern(optimization_indicators):
            return None
        
        features = {
            "before": self._extract_features(before_data, context),
            "after": self._extract_features(after_data, context),
            "delta": self._calculate_feature_deltas(
                self._extract_features(before_data, context),
                self._extract_features(after_data, context)
            )
        }
        
        pattern_signature = self._generate_pattern_signature(features, PatternType.OPTIMIZATION)
        
        existing_pattern = self._find_similar_pattern(pattern_signature, PatternType.OPTIMIZATION)
        
        if existing_pattern:
            existing_pattern.occurrences += 1
            existing_pattern.last_seen = datetime.now()
            existing_pattern.confidence_score = self._update_confidence_score(
                existing_pattern.confidence_score,
                optimization_indicators['improvement_rate']
            )
            existing_pattern.confidence = self._calculate_confidence_level(
                existing_pattern.confidence_score
            )
            existing_pattern.examples.append({
                "timestamp": datetime.now().isoformat(),
                "before": before_data,
                "after": after_data
            })
            
            if len(existing_pattern.examples) > 10:
                existing_pattern.examples = existing_pattern.examples[-10:]
            
            return existing_pattern
        
        pattern_id = f"OPT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(pattern_signature.encode()).hexdigest()[:8]}"
        
        pattern = RecognizedPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.OPTIMIZATION,
            name=self._generate_pattern_name(features, PatternType.OPTIMIZATION),
            description=self._generate_optimization_description(features, optimization_indicators),
            confidence=self._calculate_confidence_level(optimization_indicators['improvement_rate']),
            confidence_score=optimization_indicators['improvement_rate'],
            occurrences=1,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            features=features,
            context=context or {},
            examples=[{
                "timestamp": datetime.now().isoformat(),
                "before": before_data,
                "after": after_data
            }],
            tags=self._extract_tags(features, PatternType.OPTIMIZATION) + [optimization_type]
        )
        
        self._patterns[pattern_id] = pattern
        self._pattern_cache[PatternType.OPTIMIZATION.value].append(pattern)
        
        if self._storage_path:
            self._save_patterns()
        
        self._logger.info(f"识别到新的优化模式: {pattern.name} (置信度: {pattern.confidence.value})")
        return pattern
    
    def evaluate_pattern_confidence(
        self,
        pattern_id: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[PatternConfidence, float]:
        """评估模式置信度
        
        Args:
            pattern_id: 模式ID
            additional_data: 额外数据
        
        Returns:
            (置信度级别, 置信度分数)
        """
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return PatternConfidence.VERY_LOW, 0.0
        
        base_score = pattern.confidence_score
        
        occurrence_factor = min(pattern.occurrences / 10.0, 1.0)
        recency_factor = self._calculate_recency_factor(pattern.last_seen)
        stability_factor = self._calculate_stability_factor(pattern)
        
        final_score = (
            base_score * 0.5 +
            occurrence_factor * 0.2 +
            recency_factor * 0.15 +
            stability_factor * 0.15
        )
        
        if additional_data:
            consistency_bonus = self._check_pattern_consistency(pattern, additional_data)
            final_score = final_score * 0.8 + consistency_bonus * 0.2
        
        confidence_level = self._calculate_confidence_level(final_score)
        
        return confidence_level, final_score
    
    def find_similar_patterns(
        self,
        pattern: RecognizedPattern,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[RecognizedPattern, float]]:
        """查找相似模式
        
        Args:
            pattern: 目标模式
            similarity_threshold: 相似度阈值
        
        Returns:
            相似模式列表及其相似度
        """
        similar_patterns = []
        
        for pid, p in self._patterns.items():
            if pid == pattern.pattern_id:
                continue
            
            similarity = self._calculate_pattern_similarity(pattern, p)
            
            if similarity >= similarity_threshold:
                similar_patterns.append((p, similarity))
        
        similar_patterns.sort(key=lambda x: x[1], reverse=True)
        
        return similar_patterns
    
    def get_patterns_by_type(
        self,
        pattern_type: PatternType,
        min_confidence: Optional[PatternConfidence] = None
    ) -> List[RecognizedPattern]:
        """按类型获取模式
        
        Args:
            pattern_type: 模式类型
            min_confidence: 最低置信度
        
        Returns:
            模式列表
        """
        patterns = self._pattern_cache.get(pattern_type.value, [])
        
        if min_confidence:
            confidence_order = [
                PatternConfidence.VERY_LOW,
                PatternConfidence.LOW,
                PatternConfidence.MEDIUM,
                PatternConfidence.HIGH,
                PatternConfidence.VERY_HIGH
            ]
            min_index = confidence_order.index(min_confidence)
            patterns = [
                p for p in patterns
                if confidence_order.index(p.confidence) >= min_index
            ]
        
        return sorted(patterns, key=lambda p: p.confidence_score, reverse=True)
    
    def get_top_patterns(
        self,
        pattern_type: Optional[PatternType] = None,
        limit: int = 10
    ) -> List[RecognizedPattern]:
        """获取顶级模式
        
        Args:
            pattern_type: 模式类型（可选）
            limit: 数量限制
        
        Returns:
            顶级模式列表
        """
        if pattern_type:
            patterns = self._pattern_cache.get(pattern_type.value, [])
        else:
            patterns = list(self._patterns.values())
        
        scored_patterns = []
        for p in patterns:
            score = (
                p.confidence_score * 0.4 +
                min(p.occurrences / 20.0, 1.0) * 0.3 +
                self._calculate_recency_factor(p.last_seen) * 0.3
            )
            scored_patterns.append((p, score))
        
        scored_patterns.sort(key=lambda x: x[1], reverse=True)
        
        return [p for p, s in scored_patterns[:limit]]
    
    def _extract_success_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取成功指标"""
        indicators = {
            'success_rate': 0.0,
            'completion_status': False,
            'quality_score': 0.0,
            'performance_score': 0.0
        }
        
        if 'success_rate' in data:
            indicators['success_rate'] = float(data['success_rate'])
        elif 'status' in data:
            indicators['completion_status'] = data['status'] in ['success', 'completed', 'passed']
            indicators['success_rate'] = 1.0 if indicators['completion_status'] else 0.0
        
        if 'quality_score' in data:
            indicators['quality_score'] = float(data['quality_score'])
        
        if 'performance_score' in data:
            indicators['performance_score'] = float(data['performance_score'])
        
        if 'metrics' in data:
            metrics = data['metrics']
            if isinstance(metrics, dict):
                if 'success_count' in metrics and 'total_count' in metrics:
                    total = metrics['total_count']
                    if total > 0:
                        indicators['success_rate'] = metrics['success_count'] / total
        
        return indicators
    
    def _extract_failure_indicators(
        self,
        data: Dict[str, Any],
        error_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """提取失败指标"""
        indicators = {
            'failure_rate': 0.0,
            'error_count': 0,
            'error_types': [],
            'severity': 'low'
        }
        
        if 'failure_rate' in data:
            indicators['failure_rate'] = float(data['failure_rate'])
        elif 'status' in data:
            if data['status'] in ['failed', 'error', 'timeout']:
                indicators['failure_rate'] = 1.0
        
        if error_info:
            indicators['error_count'] = error_info.get('count', 1)
            indicators['error_types'] = error_info.get('types', [])
            indicators['severity'] = error_info.get('severity', 'low')
        
        if 'errors' in data:
            errors = data['errors']
            if isinstance(errors, list):
                indicators['error_count'] = len(errors)
                indicators['error_types'] = list(set(
                    e.get('type', 'unknown') for e in errors
                ))
        
        return indicators
    
    def _extract_optimization_indicators(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取优化指标"""
        indicators = {
            'improvement_rate': 0.0,
            'performance_gain': 0.0,
            'quality_gain': 0.0,
            'efficiency_gain': 0.0
        }
        
        if 'performance' in before and 'performance' in after:
            before_perf = before['performance']
            after_perf = after['performance']
            
            if isinstance(before_perf, (int, float)) and isinstance(after_perf, (int, float)):
                if before_perf > 0:
                    indicators['performance_gain'] = (after_perf - before_perf) / before_perf
        
        if 'quality_score' in before and 'quality_score' in after:
            before_quality = before['quality_score']
            after_quality = after['quality_score']
            
            if isinstance(before_quality, (int, float)) and isinstance(after_quality, (int, float)):
                if before_quality > 0:
                    indicators['quality_gain'] = (after_quality - before_quality) / before_quality
        
        if 'execution_time' in before and 'execution_time' in after:
            before_time = before['execution_time']
            after_time = after['execution_time']
            
            if isinstance(before_time, (int, float)) and isinstance(after_time, (int, float)):
                if before_time > 0:
                    indicators['efficiency_gain'] = (before_time - after_time) / before_time
        
        gains = [
            indicators['performance_gain'],
            indicators['quality_gain'],
            indicators['efficiency_gain']
        ]
        positive_gains = [g for g in gains if g > 0]
        
        if positive_gains:
            indicators['improvement_rate'] = sum(positive_gains) / len(positive_gains)
        
        return indicators
    
    def _is_success_pattern(self, indicators: Dict[str, Any]) -> bool:
        """判断是否为成功模式"""
        return indicators['success_rate'] >= self._success_threshold
    
    def _is_failure_pattern(self, indicators: Dict[str, Any]) -> bool:
        """判断是否为失败模式"""
        return indicators['failure_rate'] >= self._failure_threshold
    
    def _is_optimization_pattern(self, indicators: Dict[str, Any]) -> bool:
        """判断是否为优化模式"""
        return indicators['improvement_rate'] >= self._optimization_threshold
    
    def _extract_features(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """提取特征"""
        features = {}
        
        for feature_name, extractor in self._feature_extractors.items():
            try:
                extracted = extractor(data, context)
                if extracted:
                    features.update(extracted)
            except Exception as e:
                self._logger.warning(f"特征提取失败 {feature_name}: {e}")
        
        return features
    
    def _extract_code_structure_features(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """提取代码结构特征"""
        features = {}
        
        if 'code' in data:
            code = data['code']
            features['code_length'] = len(code)
            features['line_count'] = code.count('\n') + 1
            features['function_count'] = len(re.findall(r'\bdef\s+\w+', code))
            features['class_count'] = len(re.findall(r'\bclass\s+\w+', code))
        
        if 'file_path' in data:
            file_path = data['file_path']
            features['file_extension'] = Path(file_path).suffix
            features['file_name'] = Path(file_path).name
        
        return features
    
    def _extract_execution_context_features(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """提取执行上下文特征"""
        features = {}
        
        if context:
            features['context_keys'] = list(context.keys())
            features['context_size'] = len(str(context))
        
        if 'environment' in data:
            features['environment'] = data['environment']
        
        if 'timestamp' in data:
            features['execution_time_of_day'] = datetime.fromisoformat(
                data['timestamp']
            ).hour if isinstance(data['timestamp'], str) else datetime.now().hour
        
        return features
    
    def _extract_performance_features(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """提取性能特征"""
        features = {}
        
        if 'execution_time' in data:
            features['execution_time'] = data['execution_time']
        
        if 'memory_usage' in data:
            features['memory_usage'] = data['memory_usage']
        
        if 'cpu_usage' in data:
            features['cpu_usage'] = data['cpu_usage']
        
        return features
    
    def _extract_error_features(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """提取错误特征"""
        features = {}
        
        error_info = data.get('error_info') if isinstance(data, dict) else None
        
        if not error_info:
            return features
        
        if 'type' in error_info:
            features['error_type'] = error_info['type']
        
        if 'message' in error_info:
            features['error_message_length'] = len(error_info['message'])
            features['error_keywords'] = self._extract_error_keywords(error_info['message'])
        
        if 'stack_trace' in error_info:
            features['stack_trace_depth'] = error_info['stack_trace'].count('\n')
        
        return features
    
    def _extract_temporal_features(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """提取时间特征"""
        features = {}
        
        now = datetime.now()
        features['hour_of_day'] = now.hour
        features['day_of_week'] = now.weekday()
        features['is_weekend'] = now.weekday() >= 5
        
        return features
    
    def _extract_error_keywords(self, error_message: str) -> List[str]:
        """提取错误关键词"""
        keywords = []
        
        error_patterns = [
            r'Error:\s*(\w+)',
            r'Exception:\s*(\w+)',
            r'Failed\s+to\s+(\w+)',
            r'Cannot\s+(\w+)',
            r'Unable\s+to\s+(\w+)',
            r'Missing\s+(\w+)',
            r'Invalid\s+(\w+)',
            r'Undefined\s+(\w+)'
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, error_message, re.IGNORECASE)
            keywords.extend(matches)
        
        return list(set(keywords))
    
    def _generate_pattern_signature(
        self,
        features: Dict[str, Any],
        pattern_type: PatternType
    ) -> str:
        """生成模式签名"""
        signature_parts = [pattern_type.value]
        
        sorted_features = sorted(features.items(), key=lambda x: x[0])
        
        for key, value in sorted_features:
            if isinstance(value, (str, int, float, bool)):
                signature_parts.append(f"{key}:{value}")
            elif isinstance(value, list):
                signature_parts.append(f"{key}:[{','.join(map(str, sorted(value)))}]")
        
        return "|".join(signature_parts)
    
    def _find_similar_pattern(
        self,
        signature: str,
        pattern_type: PatternType
    ) -> Optional[RecognizedPattern]:
        """查找相似模式"""
        patterns = self._pattern_cache.get(pattern_type.value, [])
        
        for pattern in patterns:
            pattern_signature = self._generate_pattern_signature(
                pattern.features,
                pattern.pattern_type
            )
            
            if self._calculate_signature_similarity(signature, pattern_signature) > 0.9:
                return pattern
        
        return None
    
    def _calculate_signature_similarity(self, sig1: str, sig2: str) -> float:
        """计算签名相似度"""
        parts1 = set(sig1.split('|'))
        parts2 = set(sig2.split('|'))
        
        if not parts1 or not parts2:
            return 0.0
        
        intersection = parts1 & parts2
        union = parts1 | parts2
        
        return len(intersection) / len(union)
    
    def _generate_pattern_name(
        self,
        features: Dict[str, Any],
        pattern_type: PatternType
    ) -> str:
        """生成模式名称"""
        type_names = {
            PatternType.SUCCESS: "成功",
            PatternType.FAILURE: "失败",
            PatternType.OPTIMIZATION: "优化",
            PatternType.ANTI_PATTERN: "反模式",
            PatternType.HYBRID: "混合"
        }
        
        base_name = type_names.get(pattern_type, "未知")
        
        key_features = []
        
        if 'file_extension' in features:
            key_features.append(features['file_extension'])
        
        if 'error_type' in features:
            key_features.append(features['error_type'])
        
        if 'optimization_type' in features:
            key_features.append(features['optimization_type'])
        
        if key_features:
            return f"{base_name}模式-{'-'.join(key_features[:3])}"
        else:
            return f"{base_name}模式-{datetime.now().strftime('%H%M%S')}"
    
    def _generate_pattern_description(
        self,
        features: Dict[str, Any],
        indicators: Dict[str, Any]
    ) -> str:
        """生成模式描述"""
        desc_parts = []
        
        if 'success_rate' in indicators:
            desc_parts.append(f"成功率: {indicators['success_rate']:.2%}")
        
        if 'quality_score' in indicators:
            desc_parts.append(f"质量分数: {indicators['quality_score']:.2f}")
        
        if 'performance_score' in indicators:
            desc_parts.append(f"性能分数: {indicators['performance_score']:.2f}")
        
        if desc_parts:
            return " | ".join(desc_parts)
        else:
            return "成功执行的模式"
    
    def _generate_failure_description(
        self,
        features: Dict[str, Any],
        indicators: Dict[str, Any],
        error_info: Optional[Dict[str, Any]]
    ) -> str:
        """生成失败描述"""
        desc_parts = []
        
        if 'failure_rate' in indicators:
            desc_parts.append(f"失败率: {indicators['failure_rate']:.2%}")
        
        if 'error_count' in indicators:
            desc_parts.append(f"错误数量: {indicators['error_count']}")
        
        if 'error_types' in indicators and indicators['error_types']:
            desc_parts.append(f"错误类型: {', '.join(indicators['error_types'][:3])}")
        
        if error_info and 'message' in error_info:
            desc_parts.append(f"错误信息: {error_info['message'][:100]}")
        
        if desc_parts:
            return " | ".join(desc_parts)
        else:
            return "执行失败的模式"
    
    def _generate_optimization_description(
        self,
        features: Dict[str, Any],
        indicators: Dict[str, Any]
    ) -> str:
        """生成优化描述"""
        desc_parts = []
        
        if 'improvement_rate' in indicators:
            desc_parts.append(f"改进率: {indicators['improvement_rate']:.2%}")
        
        if 'performance_gain' in indicators and indicators['performance_gain'] > 0:
            desc_parts.append(f"性能提升: {indicators['performance_gain']:.2%}")
        
        if 'quality_gain' in indicators and indicators['quality_gain'] > 0:
            desc_parts.append(f"质量提升: {indicators['quality_gain']:.2%}")
        
        if 'efficiency_gain' in indicators and indicators['efficiency_gain'] > 0:
            desc_parts.append(f"效率提升: {indicators['efficiency_gain']:.2%}")
        
        if desc_parts:
            return " | ".join(desc_parts)
        else:
            return "优化改进的模式"
    
    def _calculate_feature_deltas(
        self,
        before_features: Dict[str, Any],
        after_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算特征变化"""
        deltas = {}
        
        all_keys = set(before_features.keys()) | set(after_features.keys())
        
        for key in all_keys:
            before_val = before_features.get(key)
            after_val = after_features.get(key)
            
            if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                if before_val != 0:
                    deltas[f"{key}_delta"] = (after_val - before_val) / abs(before_val)
                else:
                    deltas[f"{key}_delta"] = after_val - before_val
            elif before_val != after_val:
                deltas[f"{key}_changed"] = True
        
        return deltas
    
    def _extract_tags(
        self,
        features: Dict[str, Any],
        pattern_type: PatternType
    ) -> List[str]:
        """提取标签"""
        tags = [pattern_type.value]
        
        if 'file_extension' in features:
            ext = features['file_extension'].lstrip('.')
            tags.append(ext if ext else 'unknown')
        
        if 'error_type' in features:
            tags.append(features['error_type'].lower())
        
        if 'environment' in features:
            tags.append(features['environment'])
        
        return list(set(tags))
    
    def _calculate_confidence_level(self, score: float) -> PatternConfidence:
        """计算置信度级别"""
        if score >= 0.9:
            return PatternConfidence.VERY_HIGH
        elif score >= 0.75:
            return PatternConfidence.HIGH
        elif score >= 0.5:
            return PatternConfidence.MEDIUM
        elif score >= 0.25:
            return PatternConfidence.LOW
        else:
            return PatternConfidence.VERY_LOW
    
    def _update_confidence_score(self, current_score: float, new_score: float) -> float:
        """更新置信度分数"""
        return current_score * 0.7 + new_score * 0.3
    
    def _calculate_recency_factor(self, last_seen: datetime) -> float:
        """计算时效性因子"""
        age = datetime.now() - last_seen
        
        if age.days == 0:
            return 1.0
        elif age.days < 7:
            return 0.8
        elif age.days < 30:
            return 0.6
        elif age.days < 90:
            return 0.4
        else:
            return 0.2
    
    def _calculate_stability_factor(self, pattern: RecognizedPattern) -> float:
        """计算稳定性因子"""
        if pattern.occurrences < 3:
            return 0.5
        
        if len(pattern.examples) < 2:
            return 0.6
        
        return min(pattern.occurrences / 20.0, 1.0)
    
    def _check_pattern_consistency(
        self,
        pattern: RecognizedPattern,
        data: Dict[str, Any]
    ) -> float:
        """检查模式一致性"""
        consistency_scores = []
        
        for key, value in pattern.features.items():
            if key in data:
                if isinstance(value, (int, float)) and isinstance(data[key], (int, float)):
                    if value != 0:
                        similarity = 1.0 - abs(value - data[key]) / abs(value)
                        consistency_scores.append(max(0, similarity))
                elif value == data[key]:
                    consistency_scores.append(1.0)
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5
    
    def _calculate_pattern_similarity(
        self,
        pattern1: RecognizedPattern,
        pattern2: RecognizedPattern
    ) -> float:
        """计算模式相似度"""
        if pattern1.pattern_type != pattern2.pattern_type:
            return 0.0
        
        feature_similarity = self._calculate_feature_similarity(
            pattern1.features,
            pattern2.features
        )
        
        tag_similarity = self._calculate_tag_similarity(
            pattern1.tags,
            pattern2.tags
        )
        
        confidence_similarity = 1.0 - abs(
            pattern1.confidence_score - pattern2.confidence_score
        )
        
        return (
            feature_similarity * 0.5 +
            tag_similarity * 0.3 +
            confidence_similarity * 0.2
        )
    
    def _calculate_feature_similarity(
        self,
        features1: Dict[str, Any],
        features2: Dict[str, Any]
    ) -> float:
        """计算特征相似度"""
        if not features1 or not features2:
            return 0.0
        
        common_keys = set(features1.keys()) & set(features2.keys())
        
        if not common_keys:
            return 0.0
        
        similarities = []
        for key in common_keys:
            val1 = features1[key]
            val2 = features2[key]
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                if val1 != 0:
                    sim = 1.0 - abs(val1 - val2) / abs(val1)
                    similarities.append(max(0, sim))
            elif val1 == val2:
                similarities.append(1.0)
            else:
                similarities.append(0.0)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _calculate_tag_similarity(
        self,
        tags1: List[str],
        tags2: List[str]
    ) -> float:
        """计算标签相似度"""
        if not tags1 or not tags2:
            return 0.0
        
        set1 = set(tags1)
        set2 = set(tags2)
        
        intersection = set1 & set2
        union = set1 | set2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _save_patterns(self) -> None:
        """保存模式"""
        if not self._storage_path:
            return
        
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "patterns": [p.to_dict() for p in self._patterns.values()]
            }
            
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            temp_file = self._storage_path.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            temp_file.replace(self._storage_path)
            
        except Exception as e:
            self._logger.error(f"保存模式失败: {e}")
    
    def _load_patterns(self) -> None:
        """加载模式"""
        if not self._storage_path or not self._storage_path.exists():
            return
        
        try:
            with open(self._storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for pattern_data in data.get("patterns", []):
                pattern = RecognizedPattern.from_dict(pattern_data)
                self._patterns[pattern.pattern_id] = pattern
                self._pattern_cache[pattern.pattern_type.value].append(pattern)
            
            self._logger.info(f"已加载 {len(self._patterns)} 个模式")
            
        except Exception as e:
            self._logger.error(f"加载模式失败: {e}")
    
    def track_pattern_evolution(
        self,
        pattern_id: str,
        evolution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """跟踪模式演化
        
        Args:
            pattern_id: 模式ID
            evolution_data: 演化数据
        
        Returns:
            演化分析结果
        """
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return {"status": "error", "message": "模式不存在"}
        
        evolution_result = {
            "pattern_id": pattern_id,
            "timestamp": datetime.now().isoformat(),
            "evolution_type": "unknown",
            "changes": [],
            "trend": "stable"
        }
        
        if 'confidence_change' in evolution_data:
            old_confidence = pattern.confidence_score
            new_confidence = evolution_data['confidence_change']
            change = new_confidence - old_confidence
            
            evolution_result["changes"].append({
                "aspect": "confidence",
                "old_value": old_confidence,
                "new_value": new_confidence,
                "change": change
            })
            
            if change > 0.1:
                evolution_result["evolution_type"] = "improving"
                evolution_result["trend"] = "upward"
            elif change < -0.1:
                evolution_result["evolution_type"] = "degrading"
                evolution_result["trend"] = "downward"
        
        if 'occurrence_change' in evolution_data:
            old_occurrences = pattern.occurrences
            new_occurrences = old_occurrences + evolution_data['occurrence_change']
            
            evolution_result["changes"].append({
                "aspect": "occurrences",
                "old_value": old_occurrences,
                "new_value": new_occurrences,
                "change": evolution_data['occurrence_change']
            })
        
        if 'feature_changes' in evolution_data:
            for feature_name, change_info in evolution_data['feature_changes'].items():
                evolution_result["changes"].append({
                    "aspect": f"feature_{feature_name}",
                    "old_value": change_info.get('old'),
                    "new_value": change_info.get('new'),
                    "change": change_info.get('delta')
                })
        
        if not pattern.metadata.get('evolution_history'):
            pattern.metadata['evolution_history'] = []
        
        pattern.metadata['evolution_history'].append(evolution_result)
        
        if len(pattern.metadata['evolution_history']) > 20:
            pattern.metadata['evolution_history'] = pattern.metadata['evolution_history'][-20:]
        
        if self._storage_path:
            self._save_patterns()
        
        return evolution_result
    
    def cluster_patterns(
        self,
        pattern_type: Optional[PatternType] = None,
        min_cluster_size: int = 2
    ) -> Dict[str, List[str]]:
        """聚类模式
        
        Args:
            pattern_type: 模式类型（可选）
            min_cluster_size: 最小聚类大小
        
        Returns:
            聚类结果 {cluster_id: [pattern_ids]}
        """
        if pattern_type:
            patterns = self._pattern_cache.get(pattern_type.value, [])
        else:
            patterns = list(self._patterns.values())
        
        if len(patterns) < min_cluster_size:
            return {}
        
        clusters: Dict[str, List[str]] = {}
        cluster_id_counter = 0
        
        for pattern in patterns:
            assigned = False
            
            for cluster_id, cluster_pattern_ids in clusters.items():
                cluster_patterns = [
                    self._patterns[pid] for pid in cluster_pattern_ids
                    if pid in self._patterns
                ]
                
                if cluster_patterns:
                    avg_similarity = sum(
                        self._calculate_pattern_similarity(pattern, cp)
                        for cp in cluster_patterns
                    ) / len(cluster_patterns)
                    
                    if avg_similarity > 0.7:
                        clusters[cluster_id].append(pattern.pattern_id)
                        assigned = True
                        break
            
            if not assigned:
                cluster_id = f"cluster_{cluster_id_counter}"
                clusters[cluster_id] = [pattern.pattern_id]
                cluster_id_counter += 1
        
        clusters = {
            cid: pids for cid, pids in clusters.items()
            if len(pids) >= min_cluster_size
        }
        
        return clusters
    
    def predict_pattern_applicability(
        self,
        pattern_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """预测模式适用性
        
        Args:
            pattern_id: 模式ID
            context: 上下文信息
        
        Returns:
            预测结果
        """
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return {
                "applicable": False,
                "confidence": 0.0,
                "reason": "模式不存在"
            }
        
        prediction = {
            "pattern_id": pattern_id,
            "applicable": True,
            "confidence": 0.5,
            "factors": [],
            "recommendations": []
        }
        
        context_features = self._extract_features(context)
        feature_match_score = self._calculate_feature_similarity(
            pattern.features,
            context_features
        )
        
        prediction["factors"].append({
            "name": "feature_match",
            "score": feature_match_score,
            "weight": 0.3
        })
        
        tag_match_score = 0.0
        if 'tags' in context:
            context_tags = set(context['tags'])
            pattern_tags = set(pattern.tags)
            if context_tags and pattern_tags:
                tag_match_score = len(context_tags & pattern_tags) / len(pattern_tags)
        
        prediction["factors"].append({
            "name": "tag_match",
            "score": tag_match_score,
            "weight": 0.2
        })
        
        prediction["factors"].append({
            "name": "pattern_confidence",
            "score": pattern.confidence_score,
            "weight": 0.25
        })
        
        recency_score = self._calculate_recency_factor(pattern.last_seen)
        prediction["factors"].append({
            "name": "recency",
            "score": recency_score,
            "weight": 0.15
        })
        
        stability_score = self._calculate_stability_factor(pattern)
        prediction["factors"].append({
            "name": "stability",
            "score": stability_score,
            "weight": 0.1
        })
        
        total_score = sum(
            factor["score"] * factor["weight"]
            for factor in prediction["factors"]
        )
        
        prediction["confidence"] = total_score
        prediction["applicable"] = total_score > 0.6
        
        if feature_match_score < 0.5:
            prediction["recommendations"].append(
                "上下文特征与模式特征匹配度较低，建议谨慎应用"
            )
        
        if pattern.occurrences < 3:
            prediction["recommendations"].append(
                "模式验证次数较少，建议先在小范围测试"
            )
        
        if recency_score < 0.5:
            prediction["recommendations"].append(
                "模式较长时间未使用，建议重新验证"
            )
        
        return prediction
    
    def extract_advanced_features(
        self,
        data: Dict[str, Any],
        feature_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """提取高级特征
        
        Args:
            data: 数据
            feature_types: 特征类型列表
        
        Returns:
            高级特征字典
        """
        features = {}
        
        if not feature_types:
            feature_types = [
                'complexity', 'dependency', 'semantic', 
                'structural', 'temporal', 'contextual'
            ]
        
        if 'complexity' in feature_types:
            features['complexity'] = self._extract_complexity_features(data)
        
        if 'dependency' in feature_types:
            features['dependency'] = self._extract_dependency_features(data)
        
        if 'semantic' in feature_types:
            features['semantic'] = self._extract_semantic_features(data)
        
        if 'structural' in feature_types:
            features['structural'] = self._extract_structural_features(data)
        
        if 'temporal' in feature_types:
            features['temporal'] = self._extract_temporal_advanced_features(data)
        
        if 'contextual' in feature_types:
            features['contextual'] = self._extract_contextual_features(data)
        
        return features
    
    def _extract_complexity_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取复杂度特征"""
        features = {}
        
        if 'code' in data:
            code = data['code']
            lines = code.split('\n')
            
            features['lines_of_code'] = len(lines)
            features['non_empty_lines'] = sum(1 for line in lines if line.strip())
            features['comment_lines'] = sum(1 for line in lines if line.strip().startswith('#'))
            
            indentations = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
            features['max_indentation'] = max(indentations) // 4 if indentations else 0
            features['avg_indentation'] = sum(indentations) // len(indentations) // 4 if indentations else 0
            
            features['cyclomatic_complexity'] = (
                code.count('if ') + code.count('elif ') + 
                code.count('for ') + code.count('while ') + 
                code.count('and ') + code.count('or ') + 1
            )
        
        return features
    
    def _extract_dependency_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取依赖特征"""
        features = {}
        
        if 'code' in data:
            code = data['code']
            
            features['import_count'] = len(re.findall(r'^import\s+', code, re.MULTILINE))
            features['from_import_count'] = len(re.findall(r'^from\s+', code, re.MULTILINE))
            
            imports = re.findall(r'^import\s+(\w+)', code, re.MULTILINE)
            imports.extend(re.findall(r'^from\s+(\w+)', code, re.MULTILINE))
            features['unique_dependencies'] = len(set(imports))
            features['dependency_list'] = list(set(imports))[:10]
        
        if 'dependencies' in data:
            deps = data['dependencies']
            if isinstance(deps, list):
                features['external_dependencies'] = len(deps)
        
        return features
    
    def _extract_semantic_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取语义特征"""
        features = {}
        
        text = ''
        if 'code' in data:
            text += data['code']
        if 'description' in data:
            text += ' ' + data['description']
        if 'title' in data:
            text += ' ' + data['title']
        
        semantic_keywords = {
            'data_processing': ['data', 'process', 'transform', 'convert', 'parse'],
            'io_operations': ['read', 'write', 'file', 'input', 'output', 'stream'],
            'network': ['http', 'request', 'response', 'api', 'network', 'socket'],
            'database': ['query', 'database', 'sql', 'table', 'record', 'insert', 'update'],
            'security': ['encrypt', 'decrypt', 'auth', 'token', 'secure', 'password'],
            'testing': ['test', 'assert', 'mock', 'spec', 'verify', 'validate'],
            'optimization': ['optimize', 'performance', 'cache', 'speed', 'efficient'],
            'error_handling': ['error', 'exception', 'catch', 'handle', 'retry', 'fallback']
        }
        
        text_lower = text.lower()
        for category, keywords in semantic_keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            features[f'semantic_{category}'] = matches / len(keywords) if keywords else 0
        
        return features
    
    def _extract_structural_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取结构特征"""
        features = {}
        
        if 'code' in data:
            code = data['code']
            
            features['function_count'] = len(re.findall(r'\bdef\s+\w+', code))
            features['class_count'] = len(re.findall(r'\bclass\s+\w+', code))
            features['method_count'] = len(re.findall(r'\bdef\s+self\.\w+', code))
            
            features['has_main'] = 'if __name__' in code
            features['has_init'] = '__init__' in code
            features['has_decorator'] = '@' in code
            
            features['nesting_depth'] = self._calculate_nesting_depth(code)
        
        return features
    
    def _extract_temporal_advanced_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取高级时间特征"""
        features = {}
        
        now = datetime.now()
        
        features['hour_of_day'] = now.hour
        features['day_of_week'] = now.weekday()
        features['day_of_month'] = now.day
        features['month'] = now.month
        features['quarter'] = (now.month - 1) // 3 + 1
        features['year'] = now.year
        
        features['is_weekend'] = now.weekday() >= 5
        features['is_business_hours'] = 9 <= now.hour < 18
        
        if 'timestamp' in data:
            try:
                if isinstance(data['timestamp'], str):
                    ts = datetime.fromisoformat(data['timestamp'])
                else:
                    ts = data['timestamp']
                
                features['age_hours'] = (now - ts).total_seconds() / 3600
                features['age_days'] = (now - ts).days
            except:
                pass
        
        return features
    
    def _extract_contextual_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取上下文特征"""
        features = {}
        
        if 'context' in data:
            ctx = data['context']
            
            features['context_size'] = len(str(ctx))
            features['context_keys'] = list(ctx.keys()) if isinstance(ctx, dict) else []
            features['context_depth'] = self._calculate_dict_depth(ctx) if isinstance(ctx, dict) else 0
        
        if 'environment' in data:
            features['environment'] = data['environment']
        
        if 'project_type' in data:
            features['project_type'] = data['project_type']
        
        if 'technology_stack' in data:
            stack = data['technology_stack']
            if isinstance(stack, list):
                features['tech_stack_size'] = len(stack)
                features['tech_stack'] = stack[:5]
        
        return features
    
    def _calculate_nesting_depth(self, code: str) -> int:
        """计算代码嵌套深度"""
        max_depth = 0
        current_depth = 0
        
        for line in code.split('\n'):
            if not line.strip():
                continue
            
            indent = len(line) - len(line.lstrip())
            current_depth = indent // 4
            max_depth = max(max_depth, current_depth)
        
        return max_depth
    
    def _calculate_dict_depth(self, d: Any, current_depth: int = 0) -> int:
        """计算字典深度"""
        if not isinstance(d, dict) or not d:
            return current_depth
        
        return max(
            self._calculate_dict_depth(v, current_depth + 1)
            for v in d.values()
        )
    
    def analyze_success_pattern_correlations(
        self,
        pattern_id: str,
        min_correlation: float = 0.5
    ) -> Dict[str, Any]:
        """分析成功模式的关联关系
        
        Args:
            pattern_id: 模式ID
            min_correlation: 最小关联度阈值
        
        Returns:
            关联分析结果
        """
        pattern = self._patterns.get(pattern_id)
        if not pattern or pattern.pattern_type != PatternType.SUCCESS:
            return {"status": "error", "message": "模式不存在或不是成功模式"}
        
        correlations = []
        success_patterns = self._pattern_cache.get(PatternType.SUCCESS.value, [])
        
        for other_pattern in success_patterns:
            if other_pattern.pattern_id == pattern_id:
                continue
            
            correlation_score = self._calculate_pattern_correlation(pattern, other_pattern)
            
            if correlation_score >= min_correlation:
                correlations.append({
                    "pattern_id": other_pattern.pattern_id,
                    "pattern_name": other_pattern.name,
                    "correlation_score": correlation_score,
                    "co_occurrence_probability": self._calculate_co_occurrence_probability(
                        pattern, other_pattern
                    )
                })
        
        correlations.sort(key=lambda x: x["correlation_score"], reverse=True)
        
        return {
            "pattern_id": pattern_id,
            "pattern_name": pattern.name,
            "total_correlations": len(correlations),
            "correlations": correlations[:10],
            "correlation_strength": self._calculate_correlation_strength(correlations)
        }
    
    def predict_success_probability(
        self,
        context: Dict[str, Any],
        pattern_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """预测成功概率
        
        Args:
            context: 上下文信息
            pattern_ids: 指定的模式ID列表（可选）
        
        Returns:
            成功概率预测结果
        """
        context_features = self._extract_features(context)
        
        if pattern_ids:
            patterns = [
                self._patterns[pid] for pid in pattern_ids
                if pid in self._patterns and self._patterns[pid].pattern_type == PatternType.SUCCESS
            ]
        else:
            patterns = self._pattern_cache.get(PatternType.SUCCESS.value, [])
        
        if not patterns:
            return {
                "success_probability": 0.0,
                "confidence": 0.0,
                "applicable_patterns": [],
                "recommendations": ["未找到可应用的成功模式"]
            }
        
        pattern_scores = []
        for pattern in patterns:
            feature_similarity = self._calculate_feature_similarity(
                pattern.features, context_features
            )
            
            applicability = self.predict_pattern_applicability(pattern.pattern_id, context)
            
            weighted_score = (
                feature_similarity * 0.3 +
                pattern.confidence_score * 0.3 +
                applicability["confidence"] * 0.2 +
                self._calculate_recency_factor(pattern.last_seen) * 0.2
            )
            
            pattern_scores.append({
                "pattern_id": pattern.pattern_id,
                "pattern_name": pattern.name,
                "score": weighted_score,
                "feature_similarity": feature_similarity,
                "applicability": applicability["confidence"]
            })
        
        pattern_scores.sort(key=lambda x: x["score"], reverse=True)
        
        top_patterns = pattern_scores[:5]
        success_probability = sum(p["score"] for p in top_patterns) / len(top_patterns) if top_patterns else 0.0
        
        confidence = min(
            sum(p["applicability"] for p in top_patterns) / len(top_patterns) if top_patterns else 0.0,
            1.0
        )
        
        recommendations = self._generate_success_recommendations(top_patterns, context)
        
        return {
            "success_probability": success_probability,
            "confidence": confidence,
            "applicable_patterns": top_patterns,
            "recommendations": recommendations,
            "risk_factors": self._identify_risk_factors(context_features, patterns)
        }
    
    def analyze_failure_root_cause(
        self,
        pattern_id: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分析失败模式的根本原因
        
        Args:
            pattern_id: 模式ID
            additional_context: 额外上下文信息
        
        Returns:
            根因分析结果
        """
        pattern = self._patterns.get(pattern_id)
        if not pattern or pattern.pattern_type != PatternType.FAILURE:
            return {"status": "error", "message": "模式不存在或不是失败模式"}
        
        root_causes = []
        
        error_features = {
            k: v for k, v in pattern.features.items()
            if 'error' in k.lower() or 'fail' in k.lower()
        }
        
        for feature_name, feature_value in error_features.items():
            cause_analysis = self._analyze_error_feature(feature_name, feature_value, pattern)
            if cause_analysis:
                root_causes.append(cause_analysis)
        
        if additional_context:
            context_causes = self._analyze_context_for_causes(pattern, additional_context)
            root_causes.extend(context_causes)
        
        root_causes.sort(key=lambda x: x["severity"], reverse=True)
        
        return {
            "pattern_id": pattern_id,
            "pattern_name": pattern.name,
            "root_causes": root_causes,
            "primary_cause": root_causes[0] if root_causes else None,
            "contributing_factors": self._identify_contributing_factors(pattern),
            "remediation_suggestions": self._generate_remediation_suggestions(root_causes)
        }
    
    def generate_failure_warning(
        self,
        context: Dict[str, Any],
        warning_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """生成失败预警
        
        Args:
            context: 上下文信息
            warning_threshold: 预警阈值
        
        Returns:
            预警信息
        """
        context_features = self._extract_features(context)
        failure_patterns = self._pattern_cache.get(PatternType.FAILURE.value, [])
        
        warnings = []
        for pattern in failure_patterns:
            similarity = self._calculate_feature_similarity(pattern.features, context_features)
            
            if similarity >= warning_threshold:
                warning = {
                    "pattern_id": pattern.pattern_id,
                    "pattern_name": pattern.name,
                    "risk_level": self._calculate_risk_level(similarity, pattern),
                    "similarity": similarity,
                    "potential_issues": self._extract_potential_issues(pattern),
                    "preventive_actions": self._generate_preventive_actions(pattern)
                }
                warnings.append(warning)
        
        warnings.sort(key=lambda x: x["risk_level"], reverse=True)
        
        return {
            "has_warnings": len(warnings) > 0,
            "warning_count": len(warnings),
            "warnings": warnings[:5],
            "overall_risk": self._calculate_overall_risk(warnings),
            "recommended_actions": self._consolidate_preventive_actions(warnings)
        }
    
    def evaluate_optimization_effect(
        self,
        pattern_id: str,
        before_data: Dict[str, Any],
        after_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估优化效果
        
        Args:
            pattern_id: 模式ID
            before_data: 优化前数据
            after_data: 优化后数据
        
        Returns:
            优化效果评估结果
        """
        pattern = self._patterns.get(pattern_id)
        if not pattern or pattern.pattern_type != PatternType.OPTIMIZATION:
            return {"status": "error", "message": "模式不存在或不是优化模式"}
        
        metrics = {}
        
        performance_metrics = ['execution_time', 'memory_usage', 'cpu_usage', 'response_time']
        for metric in performance_metrics:
            if metric in before_data and metric in after_data:
                before_val = before_data[metric]
                after_val = after_data[metric]
                
                if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                    if before_val > 0:
                        improvement = (before_val - after_val) / before_val
                        metrics[metric] = {
                            "before": before_val,
                            "after": after_val,
                            "improvement": improvement,
                            "improvement_percentage": f"{improvement * 100:.2f}%"
                        }
        
        quality_metrics = ['quality_score', 'code_coverage', 'test_pass_rate']
        for metric in quality_metrics:
            if metric in before_data and metric in after_data:
                before_val = before_data[metric]
                after_val = after_data[metric]
                
                if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                    if before_val > 0:
                        improvement = (after_val - before_val) / before_val
                        metrics[metric] = {
                            "before": before_val,
                            "after": after_val,
                            "improvement": improvement,
                            "improvement_percentage": f"{improvement * 100:.2f}%"
                        }
        
        overall_improvement = self._calculate_overall_improvement(metrics)
        
        return {
            "pattern_id": pattern_id,
            "pattern_name": pattern.name,
            "metrics": metrics,
            "overall_improvement": overall_improvement,
            "effectiveness_score": self._calculate_effectiveness_score(metrics, pattern),
            "applicability_score": self._calculate_applicability_score(pattern),
            "recommendations": self._generate_optimization_recommendations(metrics, pattern)
        }
    
    def analyze_optimization_scenarios(
        self,
        pattern_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析优化模式的适用场景
        
        Args:
            pattern_id: 模式ID
            context: 上下文信息
        
        Returns:
            适用场景分析结果
        """
        pattern = self._patterns.get(pattern_id)
        if not pattern or pattern.pattern_type != PatternType.OPTIMIZATION:
            return {"status": "error", "message": "模式不存在或不是优化模式"}
        
        context_features = self._extract_features(context)
        
        scenario_match = self._calculate_scenario_match(pattern, context_features)
        
        applicable_scenarios = self._identify_applicable_scenarios(pattern, context)
        
        constraints = self._identify_constraints(pattern, context)
        
        prerequisites = self._identify_prerequisites(pattern)
        
        return {
            "pattern_id": pattern_id,
            "pattern_name": pattern.name,
            "scenario_match_score": scenario_match,
            "applicable_scenarios": applicable_scenarios,
            "constraints": constraints,
            "prerequisites": prerequisites,
            "implementation_complexity": self._assess_implementation_complexity(pattern),
            "expected_benefits": self._estimate_expected_benefits(pattern, context),
            "risk_assessment": self._assess_optimization_risks(pattern, context)
        }
    
    def evaluate_confidence_with_decay(
        self,
        pattern_id: str,
        decay_rate: float = 0.1,
        time_horizon_days: int = 30
    ) -> Dict[str, Any]:
        """评估带衰减的置信度
        
        Args:
            pattern_id: 模式ID
            decay_rate: 衰减率
            time_horizon_days: 时间范围（天）
        
        Returns:
            置信度评估结果
        """
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return {"status": "error", "message": "模式不存在"}
        
        base_confidence = pattern.confidence_score
        
        age_days = (datetime.now() - pattern.last_seen).days
        
        decayed_confidence = base_confidence * (1 - decay_rate) ** min(age_days, time_horizon_days)
        
        future_confidence_7d = decayed_confidence * (1 - decay_rate) ** 7
        future_confidence_30d = decayed_confidence * (1 - decay_rate) ** 30
        
        stability_score = self._calculate_stability_factor(pattern)
        recency_score = self._calculate_recency_factor(pattern.last_seen)
        consistency_score = self._calculate_pattern_consistency_score(pattern)
        
        adjusted_confidence = (
            decayed_confidence * 0.4 +
            stability_score * 0.25 +
            recency_score * 0.2 +
            consistency_score * 0.15
        )
        
        return {
            "pattern_id": pattern_id,
            "pattern_name": pattern.name,
            "base_confidence": base_confidence,
            "decayed_confidence": decayed_confidence,
            "adjusted_confidence": adjusted_confidence,
            "age_days": age_days,
            "decay_rate": decay_rate,
            "future_projections": {
                "7_days": future_confidence_7d,
                "30_days": future_confidence_30d
            },
            "confidence_factors": {
                "stability": stability_score,
                "recency": recency_score,
                "consistency": consistency_score
            },
            "recommendation": self._generate_confidence_recommendation(
                adjusted_confidence, age_days, stability_score
            )
        }
    
    def dynamic_confidence_adjustment(
        self,
        pattern_id: str,
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """动态调整置信度
        
        Args:
            pattern_id: 模式ID
            feedback: 反馈信息
        
        Returns:
            调整结果
        """
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return {"status": "error", "message": "模式不存在"}
        
        old_confidence = pattern.confidence_score
        
        feedback_type = feedback.get("type", "neutral")
        feedback_score = feedback.get("score", 0.5)
        feedback_weight = feedback.get("weight", 1.0)
        
        adjustment_factor = self._calculate_adjustment_factor(feedback_type, feedback_score)
        
        adjustment = adjustment_factor * feedback_weight * 0.1
        
        new_confidence = max(0.0, min(1.0, old_confidence + adjustment))
        
        pattern.confidence_score = new_confidence
        pattern.confidence = self._calculate_confidence_level(new_confidence)
        pattern.last_seen = datetime.now()
        
        if not pattern.metadata.get("confidence_history"):
            pattern.metadata["confidence_history"] = []
        
        pattern.metadata["confidence_history"].append({
            "timestamp": datetime.now().isoformat(),
            "old_confidence": old_confidence,
            "new_confidence": new_confidence,
            "adjustment": adjustment,
            "feedback_type": feedback_type,
            "feedback_score": feedback_score
        })
        
        if len(pattern.metadata["confidence_history"]) > 50:
            pattern.metadata["confidence_history"] = pattern.metadata["confidence_history"][-50:]
        
        if self._storage_path:
            self._save_patterns()
        
        return {
            "pattern_id": pattern_id,
            "old_confidence": old_confidence,
            "new_confidence": new_confidence,
            "adjustment": adjustment,
            "adjustment_direction": "increase" if adjustment > 0 else "decrease" if adjustment < 0 else "neutral",
            "confidence_level": pattern.confidence.value,
            "feedback_processed": feedback_type
        }
    
    def _calculate_pattern_correlation(
        self,
        pattern1: RecognizedPattern,
        pattern2: RecognizedPattern
    ) -> float:
        """计算模式关联度"""
        feature_correlation = self._calculate_feature_similarity(
            pattern1.features, pattern2.features
        )
        
        tag_correlation = self._calculate_tag_similarity(pattern1.tags, pattern2.tags)
        
        time_correlation = self._calculate_time_correlation(pattern1, pattern2)
        
        return (
            feature_correlation * 0.4 +
            tag_correlation * 0.35 +
            time_correlation * 0.25
        )
    
    def _calculate_co_occurrence_probability(
        self,
        pattern1: RecognizedPattern,
        pattern2: RecognizedPattern
    ) -> float:
        """计算共现概率"""
        if not pattern1.examples or not pattern2.examples:
            return 0.0
        
        timestamps1 = set()
        for example in pattern1.examples:
            if "timestamp" in example:
                try:
                    ts = datetime.fromisoformat(example["timestamp"])
                    timestamps1.add(ts.date())
                except:
                    pass
        
        timestamps2 = set()
        for example in pattern2.examples:
            if "timestamp" in example:
                try:
                    ts = datetime.fromisoformat(example["timestamp"])
                    timestamps2.add(ts.date())
                except:
                    pass
        
        if not timestamps1 or not timestamps2:
            return 0.0
        
        common_dates = timestamps1 & timestamps2
        
        return len(common_dates) / min(len(timestamps1), len(timestamps2))
    
    def _calculate_correlation_strength(self, correlations: List[Dict[str, Any]]) -> str:
        """计算关联强度"""
        if not correlations:
            return "none"
        
        avg_correlation = sum(c["correlation_score"] for c in correlations) / len(correlations)
        
        if avg_correlation >= 0.8:
            return "very_strong"
        elif avg_correlation >= 0.6:
            return "strong"
        elif avg_correlation >= 0.4:
            return "moderate"
        elif avg_correlation >= 0.2:
            return "weak"
        else:
            return "very_weak"
    
    def _generate_success_recommendations(
        self,
        top_patterns: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[str]:
        """生成成功建议"""
        recommendations = []
        
        if not top_patterns:
            recommendations.append("未找到适用的成功模式，建议收集更多数据")
            return recommendations
        
        best_pattern = top_patterns[0]
        if best_pattern["score"] >= 0.8:
            recommendations.append(
                f"强烈建议应用 '{best_pattern['pattern_name']}' 模式，匹配度极高"
            )
        elif best_pattern["score"] >= 0.6:
            recommendations.append(
                f"建议考虑应用 '{best_pattern['pattern_name']}' 模式，匹配度良好"
            )
        
        if len(top_patterns) >= 2:
            recommendations.append(
                f"可以组合应用 '{top_patterns[0]['pattern_name']}' 和 '{top_patterns[1]['pattern_name']}' 模式以获得更好效果"
            )
        
        low_similarity_patterns = [p for p in top_patterns if p["feature_similarity"] < 0.5]
        if low_similarity_patterns:
            recommendations.append(
                f"注意：{len(low_similarity_patterns)} 个模式的特征相似度较低，建议谨慎应用"
            )
        
        return recommendations
    
    def _identify_risk_factors(
        self,
        context_features: Dict[str, Any],
        success_patterns: List[RecognizedPattern]
    ) -> List[Dict[str, Any]]:
        """识别风险因素"""
        risk_factors = []
        
        if 'complexity' in context_features:
            complexity = context_features['complexity']
            if isinstance(complexity, dict) and complexity.get('cyclomatic_complexity', 0) > 10:
                risk_factors.append({
                    "factor": "high_complexity",
                    "severity": "medium",
                    "description": "代码复杂度较高，可能影响成功率"
                })
        
        if 'dependency' in context_features:
            dependency = context_features['dependency']
            if isinstance(dependency, dict) and dependency.get('unique_dependencies', 0) > 10:
                risk_factors.append({
                    "factor": "high_dependency",
                    "severity": "low",
                    "description": "依赖项较多，可能增加失败风险"
                })
        
        avg_pattern_confidence = sum(p.confidence_score for p in success_patterns) / len(success_patterns) if success_patterns else 0
        if avg_pattern_confidence < 0.6:
            risk_factors.append({
                "factor": "low_pattern_confidence",
                "severity": "high",
                "description": "可用模式的平均置信度较低"
            })
        
        return risk_factors
    
    def _analyze_error_feature(
        self,
        feature_name: str,
        feature_value: Any,
        pattern: RecognizedPattern
    ) -> Optional[Dict[str, Any]]:
        """分析错误特征"""
        if feature_name == "error_type":
            return {
                "cause_type": "error_type",
                "description": f"错误类型: {feature_value}",
                "severity": "high",
                "frequency": pattern.occurrences,
                "suggested_action": f"检查并修复 {feature_value} 类型的错误"
            }
        
        elif feature_name == "error_keywords":
            if isinstance(feature_value, list) and feature_value:
                return {
                    "cause_type": "error_keywords",
                    "description": f"关键错误关键词: {', '.join(feature_value[:5])}",
                    "severity": "medium",
                    "frequency": pattern.occurrences,
                    "suggested_action": "针对关键词错误进行专项检查"
                }
        
        return None
    
    def _analyze_context_for_causes(
        self,
        pattern: RecognizedPattern,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """从上下文分析原因"""
        causes = []
        
        if 'environment' in context:
            env = context['environment']
            if env in ['production', 'staging']:
                causes.append({
                    "cause_type": "environment",
                    "description": f"环境因素: {env}",
                    "severity": "medium",
                    "frequency": 1,
                    "suggested_action": "检查环境配置和依赖"
                })
        
        if 'load' in context:
            load = context['load']
            if isinstance(load, (int, float)) and load > 80:
                causes.append({
                    "cause_type": "high_load",
                    "description": f"高负载: {load}%",
                    "severity": "high",
                    "frequency": 1,
                    "suggested_action": "优化性能或增加资源"
                })
        
        return causes
    
    def _identify_contributing_factors(self, pattern: RecognizedPattern) -> List[str]:
        """识别促成因素"""
        factors = []
        
        if pattern.occurrences > 5:
            factors.append("频繁发生")
        
        if 'error_type' in pattern.features:
            factors.append(f"错误类型: {pattern.features['error_type']}")
        
        if 'environment' in pattern.features:
            factors.append(f"环境: {pattern.features['environment']}")
        
        return factors
    
    def _generate_remediation_suggestions(self, root_causes: List[Dict[str, Any]]) -> List[str]:
        """生成修复建议"""
        suggestions = []
        
        for cause in root_causes[:3]:
            if "suggested_action" in cause:
                suggestions.append(cause["suggested_action"])
        
        if not suggestions:
            suggestions.append("建议详细分析失败日志以确定具体原因")
            suggestions.append("考虑增加监控和告警机制")
        
        return suggestions
    
    def _calculate_risk_level(self, similarity: float, pattern: RecognizedPattern) -> float:
        """计算风险级别"""
        base_risk = similarity
        
        occurrence_factor = min(pattern.occurrences / 10.0, 1.0)
        
        confidence_factor = pattern.confidence_score
        
        return base_risk * 0.5 + occurrence_factor * 0.3 + confidence_factor * 0.2
    
    def _extract_potential_issues(self, pattern: RecognizedPattern) -> List[str]:
        """提取潜在问题"""
        issues = []
        
        if 'error_type' in pattern.features:
            issues.append(f"可能出现 {pattern.features['error_type']} 错误")
        
        if 'error_keywords' in pattern.features:
            keywords = pattern.features['error_keywords']
            if isinstance(keywords, list):
                issues.append(f"可能涉及: {', '.join(keywords[:3])}")
        
        issues.append(f"基于历史数据，该模式已出现 {pattern.occurrences} 次")
        
        return issues
    
    def _generate_preventive_actions(self, pattern: RecognizedPattern) -> List[str]:
        """生成预防措施"""
        actions = []
        
        if pattern.pattern_type == PatternType.FAILURE:
            actions.append("执行前进行充分测试")
            actions.append("准备回滚方案")
            
            if 'error_type' in pattern.features:
                actions.append(f"针对 {pattern.features['error_type']} 错误类型进行检查")
        
        actions.append("增加监控和日志记录")
        
        return actions
    
    def _calculate_overall_risk(self, warnings: List[Dict[str, Any]]) -> str:
        """计算整体风险"""
        if not warnings:
            return "low"
        
        avg_risk = sum(w["risk_level"] for w in warnings) / len(warnings)
        
        if avg_risk >= 0.7:
            return "critical"
        elif avg_risk >= 0.5:
            return "high"
        elif avg_risk >= 0.3:
            return "medium"
        else:
            return "low"
    
    def _consolidate_preventive_actions(self, warnings: List[Dict[str, Any]]) -> List[str]:
        """整合预防措施"""
        all_actions = []
        for warning in warnings:
            all_actions.extend(warning.get("preventive_actions", []))
        
        unique_actions = list(dict.fromkeys(all_actions))
        
        return unique_actions[:5]
    
    def _calculate_overall_improvement(self, metrics: Dict[str, Any]) -> float:
        """计算整体改进"""
        if not metrics:
            return 0.0
        
        improvements = []
        for metric_data in metrics.values():
            if isinstance(metric_data, dict) and "improvement" in metric_data:
                improvements.append(abs(metric_data["improvement"]))
        
        return sum(improvements) / len(improvements) if improvements else 0.0
    
    def _calculate_effectiveness_score(
        self,
        metrics: Dict[str, Any],
        pattern: RecognizedPattern
    ) -> float:
        """计算有效性分数"""
        overall_improvement = self._calculate_overall_improvement(metrics)
        
        confidence_factor = pattern.confidence_score
        
        occurrence_factor = min(pattern.occurrences / 10.0, 1.0)
        
        return overall_improvement * 0.5 + confidence_factor * 0.3 + occurrence_factor * 0.2
    
    def _calculate_applicability_score(self, pattern: RecognizedPattern) -> float:
        """计算适用性分数"""
        return (
            pattern.confidence_score * 0.4 +
            min(pattern.occurrences / 10.0, 1.0) * 0.3 +
            self._calculate_recency_factor(pattern.last_seen) * 0.3
        )
    
    def _generate_optimization_recommendations(
        self,
        metrics: Dict[str, Any],
        pattern: RecognizedPattern
    ) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if not metrics:
            recommendations.append("未检测到明显的优化效果，建议重新评估优化策略")
            return recommendations
        
        for metric_name, metric_data in metrics.items():
            if isinstance(metric_data, dict):
                improvement = metric_data.get("improvement", 0)
                if improvement > 0.2:
                    recommendations.append(
                        f"{metric_name} 提升显著 ({metric_data.get('improvement_percentage', 'N/A')})"
                    )
                elif improvement < 0:
                    recommendations.append(
                        f"警告: {metric_name} 出现退化，需要关注"
                    )
        
        if pattern.occurrences < 3:
            recommendations.append("该优化模式验证次数较少，建议进行更多测试")
        
        return recommendations
    
    def _calculate_scenario_match(
        self,
        pattern: RecognizedPattern,
        context_features: Dict[str, Any]
    ) -> float:
        """计算场景匹配度"""
        return self._calculate_feature_similarity(pattern.features, context_features)
    
    def _identify_applicable_scenarios(
        self,
        pattern: RecognizedPattern,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """识别适用场景"""
        scenarios = []
        
        if 'performance' in pattern.tags or 'performance' in pattern.features:
            scenarios.append({
                "scenario": "性能优化",
                "applicability": "high",
                "description": "适用于需要提升性能的场景"
            })
        
        if 'quality' in pattern.tags or 'quality' in pattern.features:
            scenarios.append({
                "scenario": "质量改进",
                "applicability": "high",
                "description": "适用于需要提升代码质量的场景"
            })
        
        if 'efficiency' in pattern.tags or 'efficiency' in pattern.features:
            scenarios.append({
                "scenario": "效率提升",
                "applicability": "medium",
                "description": "适用于需要提升执行效率的场景"
            })
        
        return scenarios
    
    def _identify_constraints(
        self,
        pattern: RecognizedPattern,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """识别约束条件"""
        constraints = []
        
        if 'environment' in pattern.features:
            constraints.append({
                "constraint_type": "environment",
                "value": pattern.features['environment'],
                "description": f"需要 {pattern.features['environment']} 环境"
            })
        
        if 'technology_stack' in pattern.features:
            constraints.append({
                "constraint_type": "technology",
                "value": pattern.features['technology_stack'],
                "description": "需要特定的技术栈支持"
            })
        
        return constraints
    
    def _identify_prerequisites(self, pattern: RecognizedPattern) -> List[str]:
        """识别前置条件"""
        prerequisites = []
        
        if pattern.occurrences < 5:
            prerequisites.append("建议先在测试环境验证")
        
        if 'dependencies' in pattern.features:
            prerequisites.append("确保所有依赖项已正确配置")
        
        prerequisites.append("备份当前状态以便回滚")
        
        return prerequisites
    
    def _assess_implementation_complexity(self, pattern: RecognizedPattern) -> str:
        """评估实施复杂度"""
        if 'complexity' in pattern.features:
            complexity = pattern.features['complexity']
            if isinstance(complexity, dict):
                cc = complexity.get('cyclomatic_complexity', 0)
                if cc > 15:
                    return "high"
                elif cc > 8:
                    return "medium"
                else:
                    return "low"
        
        if pattern.occurrences > 10:
            return "low"
        elif pattern.occurrences > 5:
            return "medium"
        else:
            return "high"
    
    def _estimate_expected_benefits(
        self,
        pattern: RecognizedPattern,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """估算预期收益"""
        benefits = {
            "performance_improvement": "0-10%",
            "quality_improvement": "0-10%",
            "efficiency_gain": "0-10%"
        }
        
        if 'performance_gain' in pattern.features:
            gain = pattern.features['performance_gain']
            if isinstance(gain, (int, float)):
                benefits["performance_improvement"] = f"{gain * 100:.1f}%"
        
        if 'quality_gain' in pattern.features:
            gain = pattern.features['quality_gain']
            if isinstance(gain, (int, float)):
                benefits["quality_improvement"] = f"{gain * 100:.1f}%"
        
        if 'efficiency_gain' in pattern.features:
            gain = pattern.features['efficiency_gain']
            if isinstance(gain, (int, float)):
                benefits["efficiency_gain"] = f"{gain * 100:.1f}%"
        
        return benefits
    
    def _assess_optimization_risks(
        self,
        pattern: RecognizedPattern,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估优化风险"""
        risks = {
            "overall_risk": "low",
            "risk_factors": [],
            "mitigation_strategies": []
        }
        
        if pattern.occurrences < 3:
            risks["risk_factors"].append("验证次数较少")
            risks["mitigation_strategies"].append("增加测试覆盖")
        
        if 'breaking_changes' in pattern.features:
            risks["risk_factors"].append("可能包含破坏性变更")
            risks["mitigation_strategies"].append("准备回滚方案")
        
        if len(risks["risk_factors"]) > 2:
            risks["overall_risk"] = "high"
        elif len(risks["risk_factors"]) > 0:
            risks["overall_risk"] = "medium"
        
        return risks
    
    def _calculate_pattern_consistency_score(self, pattern: RecognizedPattern) -> float:
        """计算模式一致性分数"""
        if len(pattern.examples) < 2:
            return 0.5
        
        consistency_scores = []
        
        for i in range(len(pattern.examples) - 1):
            for j in range(i + 1, len(pattern.examples)):
                example1 = pattern.examples[i].get("data", {})
                example2 = pattern.examples[j].get("data", {})
                
                similarity = self._calculate_feature_similarity(
                    self._extract_features(example1),
                    self._extract_features(example2)
                )
                consistency_scores.append(similarity)
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5
    
    def _generate_confidence_recommendation(
        self,
        confidence: float,
        age_days: int,
        stability: float
    ) -> str:
        """生成置信度建议"""
        if confidence >= 0.8:
            return "模式置信度很高，可以放心使用"
        elif confidence >= 0.6:
            if age_days > 30:
                return "模式置信度良好，但较长时间未更新，建议重新验证"
            else:
                return "模式置信度良好，可以使用"
        elif confidence >= 0.4:
            return "模式置信度中等，建议谨慎使用并收集更多反馈"
        else:
            return "模式置信度较低，建议先进行验证或寻找替代方案"
    
    def _calculate_adjustment_factor(self, feedback_type: str, feedback_score: float) -> float:
        """计算调整因子"""
        if feedback_type == "positive":
            return feedback_score
        elif feedback_type == "negative":
            return -feedback_score
        else:
            return (feedback_score - 0.5) * 2
    
    def _calculate_time_correlation(
        self,
        pattern1: RecognizedPattern,
        pattern2: RecognizedPattern
    ) -> float:
        """计算时间相关性"""
        time_diff = abs((pattern1.last_seen - pattern2.last_seen).days)
        
        if time_diff == 0:
            return 1.0
        elif time_diff <= 1:
            return 0.9
        elif time_diff <= 7:
            return 0.7
        elif time_diff <= 30:
            return 0.5
        else:
            return 0.3
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_patterns": len(self._patterns),
            "by_type": {},
            "by_confidence": {},
            "avg_occurrences": 0.0,
            "avg_confidence_score": 0.0
        }
        
        for pattern_type in PatternType:
            patterns = self._pattern_cache.get(pattern_type.value, [])
            stats["by_type"][pattern_type.value] = len(patterns)
        
        for confidence in PatternConfidence:
            count = sum(
                1 for p in self._patterns.values()
                if p.confidence == confidence
            )
            stats["by_confidence"][confidence.value] = count
        
        if self._patterns:
            stats["avg_occurrences"] = sum(
                p.occurrences for p in self._patterns.values()
            ) / len(self._patterns)
            
            stats["avg_confidence_score"] = sum(
                p.confidence_score for p in self._patterns.values()
            ) / len(self._patterns)
        
        return stats
