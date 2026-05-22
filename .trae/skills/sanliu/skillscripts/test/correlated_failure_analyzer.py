#!/usr/bin/env python3
"""
Correlated Failure Analyzer - 关联失败分析器

分析多个测试失败之间的关联性，识别共同根因，生成综合修复方案。

功能：
1. 失败关联性分析
2. 共同根因识别
3. 综合修复方案生成
4. 失败传播路径分析

使用示例：
    python correlated_failure_analyzer.py --pytest-output test_output.txt --analyze
    python correlated_failure_analyzer.py --failures failures.json --report correlation_report.md
"""

import argparse
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
from typing import Any, Dict, List, Optional, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CorrelationType(Enum):
    SAME_ROOT_CAUSE = "same_root_cause"
    DEPENDENCY_CHAIN = "dependency_chain"
    SHARED_RESOURCE = "shared_resource"
    TEMPORAL_CORRELATION = "temporal_correlation"
    CODE_PROXIMITY = "code_proximity"
    TEST_SUITE_CORRELATION = "test_suite_correlation"
    CONFIGURATION_ISSUE = "configuration_issue"
    ENVIRONMENT_ISSUE = "environment_issue"
    DATA_DEPENDENCY = "data_dependency"
    API_CONTRACT = "api_contract"
    UNKNOWN = "unknown"


class CorrelationStrength(Enum):
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"
    NONE = "none"


@dataclass
class FailureInfo:
    test_name: str
    test_file: str
    failure_type: str
    error_message: str
    exception_type: Optional[str] = None
    stack_trace: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""
    affected_files: List[str] = field(default_factory=list)
    affected_functions: List[str] = field(default_factory=list)
    test_class: Optional[str] = None
    test_module: Optional[str] = None
    assertion_details: List[Dict[str, Any]] = field(default_factory=list)
    fixture_dependencies: List[str] = field(default_factory=list)
    parametrize_params: Dict[str, Any] = field(default_factory=dict)
    environment_info: Dict[str, str] = field(default_factory=dict)
    test_duration_ms: Optional[float] = None
    retry_count: int = 0


@dataclass
class CorrelationResult:
    correlation_id: str
    correlation_type: CorrelationType
    strength: CorrelationStrength
    confidence: float
    related_failures: List[str]
    evidence: List[str]
    common_factors: List[str] = field(default_factory=list)
    propagation_path: List[str] = field(default_factory=list)
    impact_score: float = 0.0
    fix_recommendation: str = ""
    detailed_analysis: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommonRootCause:
    root_cause_id: str
    description: str
    affected_tests: List[str]
    affected_files: List[str]
    confidence: float
    fix_priority: int
    suggested_fix: str
    root_cause_category: str = "unknown"
    fix_complexity: str = "medium"
    estimated_time_minutes: int = 30
    dependencies: List[str] = field(default_factory=list)
    code_snippets: List[Dict[str, str]] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)
    verification_commands: List[str] = field(default_factory=list)


@dataclass
class ComprehensiveFixPlan:
    plan_id: str
    title: str
    description: str
    root_causes: List[CommonRootCause]
    fix_steps: List[Dict[str, Any]]
    estimated_effort: str
    priority_order: List[str]
    verification_steps: List[str]


class FailureFeatureExtractor:
    """失败特征提取器
    
    从失败信息中提取多维特征，用于关联性分析和根因识别。
    特征包括：错误签名、模块模式、函数模式、错误关键词、时间特征等。
    """
    
    def __init__(self):
        self._feature_cache: Dict[str, Dict[str, Any]] = {}
        
        self._error_pattern_library = {
            "assertion": [r"assert\s+", r"AssertionError", r"Expected\s+", r"Actual\s+"],
            "type_error": [r"TypeError", r"type\s+object", r"not\s+supported"],
            "value_error": [r"ValueError", r"invalid\s+value", r"could\s+not\s+convert"],
            "key_error": [r"KeyError", r"key\s+not\s+found"],
            "index_error": [r"IndexError", r"list\s+index\s+out\s+of\s+range"],
            "attribute_error": [r"AttributeError", r"has\s+no\s+attribute"],
            "import_error": [r"ImportError", r"ModuleNotFoundError", r"No\s+module\s+named"],
            "connection_error": [r"ConnectionError", r"ConnectionRefused", r"timeout"],
            "permission_error": [r"PermissionError", r"AccessDenied", r"forbidden"],
            "file_error": [r"FileNotFoundError", r"FileExistsError", r"No\s+such\s+file"],
        }
        
        self._fixture_patterns = {
            "database": ["db", "database", "session", "connection"],
            "api": ["client", "api", "request", "response"],
            "file": ["tmp_path", "temp_file", "file_handle"],
            "mock": ["mocker", "mock", "patch", "fixture"],
        }
    
    def extract_features(self, failure: FailureInfo) -> Dict[str, Any]:
        """提取失败的完整特征集
        
        Args:
            failure: 失败信息对象
            
        Returns:
            包含所有特征的字典
        """
        cache_key = f"{failure.test_name}:{failure.error_message[:50]}"
        if cache_key in self._feature_cache:
            return self._feature_cache[cache_key]
        
        features = {
            "error_signature": self._extract_error_signature(failure.error_message),
            "exception_type": failure.exception_type or "unknown",
            "file_patterns": self._extract_file_patterns(failure),
            "function_patterns": self._extract_function_patterns(failure),
            "stack_depth": len(failure.stack_trace),
            "affected_modules": self._extract_modules(failure),
            "error_keywords": self._extract_error_keywords(failure.error_message),
            "temporal_features": self._extract_temporal_features(failure),
            "error_category": self._categorize_error(failure),
            "fixture_features": self._extract_fixture_features(failure),
            "assertion_features": self._extract_assertion_features(failure),
            "code_context": self._extract_code_context(failure),
            "dependency_features": self._extract_dependency_features(failure),
            "performance_features": self._extract_performance_features(failure),
        }
        
        self._feature_cache[cache_key] = features
        return features
    
    def _extract_error_signature(self, error_message: str) -> str:
        signature = error_message.lower()
        signature = re.sub(r'\d+', '#', signature)
        signature = re.sub(r"'[^']*'", "'*'", signature)
        signature = re.sub(r'"[^"]*"', '"*"', signature)
        signature = re.sub(r'/[\w/]+/', '/*/', signature)
        signature = re.sub(r'0x[0-9a-fA-F]+', '0x#', signature)
        return signature[:200]
    
    def _extract_file_patterns(self, failure: FailureInfo) -> Set[str]:
        patterns = set()
        
        for file_path in failure.affected_files:
            parts = Path(file_path).parts
            if len(parts) >= 2:
                patterns.add("/".join(parts[-2:]))
            if len(parts) >= 1:
                patterns.add(parts[-1])
        
        for frame in failure.stack_trace:
            file_path = frame.get("file_path", "")
            if file_path:
                parts = Path(file_path).parts
                if len(parts) >= 2:
                    patterns.add("/".join(parts[-2:]))
        
        return patterns
    
    def _extract_function_patterns(self, failure: FailureInfo) -> Set[str]:
        patterns = set()
        
        for func in failure.affected_functions:
            patterns.add(func)
        
        for frame in failure.stack_trace:
            func_name = frame.get("function_name", "")
            if func_name and not func_name.startswith("<"):
                patterns.add(func_name)
        
        return patterns
    
    def _extract_modules(self, failure: FailureInfo) -> Set[str]:
        modules = set()
        
        for file_path in failure.affected_files:
            module = Path(file_path).stem
            if module and not module.startswith("test_"):
                modules.add(module)
        
        for frame in failure.stack_trace:
            file_path = frame.get("file_path", "")
            if file_path and "site-packages" not in file_path:
                module = Path(file_path).stem
                if module:
                    modules.add(module)
        
        return modules
    
    def _extract_error_keywords(self, error_message: str) -> Set[str]:
        keywords = set()
        
        error_keywords = [
            "none", "null", "empty", "missing", "invalid",
            "type", "value", "key", "index", "attribute",
            "import", "module", "connection", "timeout",
            "permission", "file", "not found", "access"
        ]
        
        message_lower = error_message.lower()
        for keyword in error_keywords:
            if keyword in message_lower:
                keywords.add(keyword)
        
        return keywords
    
    def _extract_temporal_features(self, failure: FailureInfo) -> Dict[str, Any]:
        """提取时间相关特征
        
        分析失败的时间模式，包括时间戳、小时、星期等。
        """
        features = {
            "has_timestamp": bool(failure.timestamp),
            "hour": None,
            "day_of_week": None
        }
        
        if failure.timestamp:
            try:
                if "T" in failure.timestamp:
                    dt = datetime.fromisoformat(failure.timestamp.replace("Z", "+00:00"))
                else:
                    dt = datetime.strptime(failure.timestamp, "%Y-%m-%d %H:%M:%S")
                
                features["hour"] = dt.hour
                features["day_of_week"] = dt.weekday()
                features["is_business_hours"] = 9 <= dt.hour < 18
                features["is_weekend"] = dt.weekday() >= 5
            except (ValueError, TypeError):
                pass
        
        return features
    
    def _categorize_error(self, failure: FailureInfo) -> str:
        """对错误进行分类
        
        根据错误消息和异常类型，将错误归类到预定义的类别中。
        
        Returns:
            错误类别字符串
        """
        error_text = f"{failure.error_message} {failure.exception_type or ''}".lower()
        
        for category, patterns in self._error_pattern_library.items():
            for pattern in patterns:
                if re.search(pattern, error_text, re.IGNORECASE):
                    return category
        
        if "assert" in error_text:
            return "assertion"
        
        return "unknown"
    
    def _extract_fixture_features(self, failure: FailureInfo) -> Dict[str, Any]:
        """提取fixture相关特征
        
        分析测试使用的fixture，识别可能的fixture相关问题。
        """
        features = {
            "fixture_count": len(failure.fixture_dependencies),
            "fixture_types": set(),
            "has_db_fixture": False,
            "has_api_fixture": False,
            "has_file_fixture": False,
            "has_mock_fixture": False,
        }
        
        for fixture in failure.fixture_dependencies:
            fixture_lower = fixture.lower()
            
            for ftype, keywords in self._fixture_patterns.items():
                if any(kw in fixture_lower for kw in keywords):
                    features["fixture_types"].add(ftype)
                    if ftype == "database":
                        features["has_db_fixture"] = True
                    elif ftype == "api":
                        features["has_api_fixture"] = True
                    elif ftype == "file":
                        features["has_file_fixture"] = True
                    elif ftype == "mock":
                        features["has_mock_fixture"] = True
        
        features["fixture_types"] = list(features["fixture_types"])
        return features
    
    def _extract_assertion_features(self, failure: FailureInfo) -> Dict[str, Any]:
        """提取断言相关特征
        
        分析断言失败的具体内容，提取预期值和实际值。
        """
        features = {
            "has_assertion": False,
            "assertion_count": len(failure.assertion_details),
            "expected_values": [],
            "actual_values": [],
            "assertion_operators": [],
        }
        
        if failure.assertion_details:
            features["has_assertion"] = True
            for detail in failure.assertion_details:
                if "expected" in detail:
                    features["expected_values"].append(str(detail["expected"])[:50])
                if "actual" in detail:
                    features["actual_values"].append(str(detail["actual"])[:50])
                if "operator" in detail:
                    features["assertion_operators"].append(detail["operator"])
        
        if not features["has_assertion"] and failure.error_message:
            if "assert" in failure.error_message.lower():
                features["has_assertion"] = True
                
                expected_match = re.search(r"Expected[:\s]+['\"]?([^'\"\n]+)['\"]?", 
                                          failure.error_message, re.IGNORECASE)
                if expected_match:
                    features["expected_values"].append(expected_match.group(1)[:50])
                
                actual_match = re.search(r"Actual[:\s]+['\"]?([^'\"\n]+)['\"]?", 
                                        failure.error_message, re.IGNORECASE)
                if actual_match:
                    features["actual_values"].append(actual_match.group(1)[:50])
        
        return features
    
    def _extract_code_context(self, failure: FailureInfo) -> Dict[str, Any]:
        """提取代码上下文特征
        
        分析失败涉及的代码上下文，包括文件类型、代码结构等。
        """
        features = {
            "test_file_type": "unknown",
            "source_file_types": set(),
            "has_test_fixture": False,
            "has_setup_teardown": False,
        }
        
        if failure.test_file:
            if "test_" in failure.test_file or "_test.py" in failure.test_file:
                features["test_file_type"] = "unit_test"
            elif "integration" in failure.test_file.lower():
                features["test_file_type"] = "integration_test"
            elif "e2e" in failure.test_file.lower() or "end_to_end" in failure.test_file.lower():
                features["test_file_type"] = "e2e_test"
        
        for file_path in failure.affected_files:
            if file_path.endswith((".py",)):
                features["source_file_types"].add("python")
            elif file_path.endswith((".json", ".yaml", ".yml", ".toml")):
                features["source_file_types"].add("config")
            elif file_path.endswith((".sql",)):
                features["source_file_types"].add("database")
        
        for func in failure.affected_functions:
            if func in ("setup", "setup_method", "setup_class", "setUp"):
                features["has_setup_teardown"] = True
            if func in ("teardown", "teardown_method", "teardown_class", "tearDown"):
                features["has_setup_teardown"] = True
        
        features["source_file_types"] = list(features["source_file_types"])
        return features
    
    def _extract_dependency_features(self, failure: FailureInfo) -> Dict[str, Any]:
        """提取依赖相关特征
        
        分析测试的外部依赖情况。
        """
        features = {
            "has_external_dependencies": False,
            "dependency_types": set(),
            "parametrize_count": len(failure.parametrize_params),
            "has_params": bool(failure.parametrize_params),
        }
        
        error_lower = failure.error_message.lower()
        
        dependency_indicators = {
            "database": ["database", "db", "sql", "query", "connection"],
            "api": ["api", "http", "request", "response", "endpoint"],
            "file_system": ["file", "directory", "path", "permission"],
            "network": ["network", "socket", "connection", "timeout"],
            "cache": ["cache", "redis", "memcached"],
            "message_queue": ["queue", "kafka", "rabbitmq", "mq"],
        }
        
        for dep_type, indicators in dependency_indicators.items():
            if any(ind in error_lower for ind in indicators):
                features["has_external_dependencies"] = True
                features["dependency_types"].add(dep_type)
        
        for fixture in failure.fixture_dependencies:
            fixture_lower = fixture.lower()
            for dep_type, indicators in dependency_indicators.items():
                if any(ind in fixture_lower for ind in indicators):
                    features["has_external_dependencies"] = True
                    features["dependency_types"].add(dep_type)
        
        features["dependency_types"] = list(features["dependency_types"])
        return features
    
    def _extract_performance_features(self, failure: FailureInfo) -> Dict[str, Any]:
        """提取性能相关特征
        
        分析测试执行时间和重试情况。
        """
        features = {
            "test_duration_ms": failure.test_duration_ms,
            "has_timeout": False,
            "is_slow_test": False,
            "retry_count": failure.retry_count,
            "has_retries": failure.retry_count > 0,
        }
        
        if failure.test_duration_ms:
            if failure.test_duration_ms > 30000:
                features["is_slow_test"] = True
            if failure.test_duration_ms > 60000:
                features["has_timeout"] = True
        
        if "timeout" in failure.error_message.lower():
            features["has_timeout"] = True
        
        return features


class CorrelationAnalyzer:
    """关联性分析器
    
    分析多个测试失败之间的关联性，识别不同类型的关联关系。
    支持的关联类型：相同根因、依赖链、共享资源、时间相关性、代码邻近性等。
    """
    
    def __init__(self):
        self.feature_extractor = FailureFeatureExtractor()
        self._correlation_counter = 0
        
        self._correlation_thresholds = {
            "strong": 0.7,
            "medium": 0.5,
            "weak": 0.3,
        }
        
        self._weight_config = {
            "same_root_cause": {
                "error_signature": 0.5,
                "exception_type": 0.2,
                "common_modules": 0.15,
                "common_keywords": 0.15,
            },
            "dependency_chain": {
                "common_functions": 0.3,
                "common_files": 0.2,
                "common_modules": 0.3,
                "stack_overlap": 0.2,
            },
            "shared_resource": {
                "resource_keywords": 0.4,
                "resource_modules": 0.3,
                "fixture_overlap": 0.3,
            },
        }
    
    def analyze_correlations(
        self,
        failures: List[FailureInfo]
    ) -> List[CorrelationResult]:
        """分析所有失败之间的关联性
        
        对每对失败进行分析，识别关联关系并返回关联结果列表。
        
        Args:
            failures: 失败信息列表
            
        Returns:
            关联结果列表
        """
        if len(failures) < 2:
            return []
        
        correlations = []
        analyzed_pairs: Set[Tuple[str, str]] = set()
        
        for i, failure1 in enumerate(failures):
            for j, failure2 in enumerate(failures):
                if i >= j:
                    continue
                
                pair_key = tuple(sorted([failure1.test_name, failure2.test_name]))
                if pair_key in analyzed_pairs:
                    continue
                analyzed_pairs.add(pair_key)
                
                correlation = self._analyze_pair(failure1, failure2)
                if correlation and correlation.strength != CorrelationStrength.NONE:
                    correlations.append(correlation)
        
        correlations = self._merge_related_correlations(correlations)
        
        return correlations
    
    def _analyze_pair(
        self,
        failure1: FailureInfo,
        failure2: FailureInfo
    ) -> Optional[CorrelationResult]:
        """分析一对失败之间的关联性
        
        计算多种关联类型的得分，选择最高得分的类型作为最终结果。
        """
        features1 = self.feature_extractor.extract_features(failure1)
        features2 = self.feature_extractor.extract_features(failure2)
        
        scores = {
            "same_root_cause": self._score_same_root_cause(features1, features2),
            "dependency_chain": self._score_dependency_chain(failure1, failure2, features1, features2),
            "shared_resource": self._score_shared_resource(features1, features2),
            "code_proximity": self._score_code_proximity(features1, features2),
            "test_suite": self._score_test_suite(failure1, failure2),
            "configuration_issue": self._score_configuration_issue(features1, features2),
            "environment_issue": self._score_environment_issue(features1, features2),
            "data_dependency": self._score_data_dependency(features1, features2),
            "api_contract": self._score_api_contract(features1, features2),
        }
        
        best_type = max(scores.keys(), key=lambda k: scores[k])
        best_score = scores[best_type]
        
        if best_score < self._correlation_thresholds["weak"]:
            return None
        
        self._correlation_counter += 1
        
        strength = self._determine_strength(best_score)
        evidence = self._generate_evidence(best_type, features1, features2)
        common_factors = self._identify_common_factors(features1, features2)
        propagation_path = self._analyze_propagation_path(failure1, failure2, features1, features2)
        impact_score = self._calculate_impact_score(failure1, failure2, best_score)
        fix_recommendation = self._generate_fix_recommendation(best_type, features1, features2)
        detailed_analysis = self._generate_detailed_analysis(best_type, features1, features2, scores)
        
        return CorrelationResult(
            correlation_id=f"COR-{self._correlation_counter:03d}",
            correlation_type=CorrelationType(best_type),
            strength=strength,
            confidence=best_score,
            related_failures=[failure1.test_name, failure2.test_name],
            evidence=evidence,
            common_factors=common_factors,
            propagation_path=propagation_path,
            impact_score=impact_score,
            fix_recommendation=fix_recommendation,
            detailed_analysis=detailed_analysis
        )
    
    def _score_same_root_cause(
        self,
        features1: Dict[str, Any],
        features2: Dict[str, Any]
    ) -> float:
        score = 0.0
        
        if features1["error_signature"] == features2["error_signature"]:
            score += 0.5
        
        if features1["exception_type"] == features2["exception_type"]:
            score += 0.2
        
        common_modules = features1["affected_modules"] & features2["affected_modules"]
        if common_modules:
            score += 0.15 * min(len(common_modules), 3) / 3
        
        common_keywords = features1["error_keywords"] & features2["error_keywords"]
        if common_keywords:
            score += 0.15 * min(len(common_keywords), 3) / 3
        
        return min(score, 1.0)
    
    def _score_dependency_chain(
        self,
        failure1: FailureInfo,
        failure2: FailureInfo,
        features1: Dict[str, Any],
        features2: Dict[str, Any]
    ) -> float:
        score = 0.0
        
        funcs1 = features1["function_patterns"]
        funcs2 = features2["function_patterns"]
        
        files1 = features1["file_patterns"]
        files2 = features2["file_patterns"]
        
        if funcs1 & funcs2:
            score += 0.3
        
        if files1 & files2:
            score += 0.2
        
        modules1 = features1["affected_modules"]
        modules2 = features2["affected_modules"]
        
        if modules1 & modules2:
            score += 0.3
        
        for frame in failure1.stack_trace:
            file_path = frame.get("file_path", "")
            if any(file_path in f.get("file_path", "") for f in failure2.stack_trace):
                score += 0.2
                break
        
        return min(score, 1.0)
    
    def _score_shared_resource(
        self,
        features1: Dict[str, Any],
        features2: Dict[str, Any]
    ) -> float:
        score = 0.0
        
        resource_keywords = {"file", "connection", "database", "socket", "resource"}
        
        kw1 = features1["error_keywords"] & resource_keywords
        kw2 = features2["error_keywords"] & resource_keywords
        
        if kw1 and kw2 and kw1 & kw2:
            score += 0.4
        
        common_modules = features1["affected_modules"] & features2["affected_modules"]
        resource_modules = {"database", "cache", "storage", "connection", "file"}
        if common_modules & resource_modules:
            score += 0.3
        
        return min(score, 1.0)
    
    def _score_code_proximity(
        self,
        features1: Dict[str, Any],
        features2: Dict[str, Any]
    ) -> float:
        score = 0.0
        
        common_files = features1["file_patterns"] & features2["file_patterns"]
        if common_files:
            score += 0.4 * min(len(common_files), 2) / 2
        
        common_funcs = features1["function_patterns"] & features2["function_patterns"]
        if common_funcs:
            score += 0.3 * min(len(common_funcs), 2) / 2
        
        common_modules = features1["affected_modules"] & features2["affected_modules"]
        if common_modules:
            score += 0.3 * min(len(common_modules), 2) / 2
        
        return min(score, 1.0)
    
    def _score_test_suite(
        self,
        failure1: FailureInfo,
        failure2: FailureInfo
    ) -> float:
        score = 0.0
        
        file1 = Path(failure1.test_file)
        file2 = Path(failure2.test_file)
        
        if file1.parent == file2.parent:
            score += 0.3
        
        if file1.stem == file2.stem:
            score += 0.4
        
        name1_parts = failure1.test_name.split("::")
        name2_parts = failure2.test_name.split("::")
        
        if len(name1_parts) > 1 and len(name2_parts) > 1:
            if name1_parts[0] == name2_parts[0]:
                score += 0.3
        
        return min(score, 1.0)
    
    def _determine_strength(self, score: float) -> CorrelationStrength:
        if score >= 0.7:
            return CorrelationStrength.STRONG
        elif score >= 0.5:
            return CorrelationStrength.MEDIUM
        elif score >= 0.3:
            return CorrelationStrength.WEAK
        else:
            return CorrelationStrength.NONE
    
    def _generate_evidence(
        self,
        correlation_type: str,
        features1: Dict[str, Any],
        features2: Dict[str, Any]
    ) -> List[str]:
        evidence = []
        
        if features1["error_signature"] == features2["error_signature"]:
            evidence.append("错误签名完全匹配")
        
        if features1["exception_type"] == features2["exception_type"]:
            evidence.append(f"异常类型相同: {features1['exception_type']}")
        
        common_modules = features1["affected_modules"] & features2["affected_modules"]
        if common_modules:
            evidence.append(f"共同模块: {', '.join(common_modules)}")
        
        common_files = features1["file_patterns"] & features2["file_patterns"]
        if common_files:
            evidence.append(f"共同文件模式: {', '.join(list(common_files)[:3])}")
        
        common_keywords = features1["error_keywords"] & features2["error_keywords"]
        if common_keywords:
            evidence.append(f"共同错误关键词: {', '.join(common_keywords)}")
        
        return evidence
    
    def _identify_common_factors(
        self,
        features1: Dict[str, Any],
        features2: Dict[str, Any]
    ) -> List[str]:
        """识别两个失败之间的共同因素
        
        分析模块、函数、文件等多个维度的共同点。
        """
        factors = []
        
        common_modules = features1["affected_modules"] & features2["affected_modules"]
        if common_modules:
            factors.append(f"模块: {', '.join(common_modules)}")
        
        common_funcs = features1["function_patterns"] & features2["function_patterns"]
        if common_funcs:
            factors.append(f"函数: {', '.join(list(common_funcs)[:3])}")
        
        common_files = features1["file_patterns"] & features2["file_patterns"]
        if common_files:
            factors.append(f"文件: {', '.join(list(common_files)[:3])}")
        
        dep_features1 = features1.get("dependency_features", {})
        dep_features2 = features2.get("dependency_features", {})
        common_deps = set(dep_features1.get("dependency_types", [])) & set(dep_features2.get("dependency_types", []))
        if common_deps:
            factors.append(f"依赖: {', '.join(common_deps)}")
        
        fixture1 = features1.get("fixture_features", {})
        fixture2 = features2.get("fixture_features", {})
        common_fixtures = set(fixture1.get("fixture_types", [])) & set(fixture2.get("fixture_types", []))
        if common_fixtures:
            factors.append(f"Fixture: {', '.join(common_fixtures)}")
        
        return factors
    
    def _score_configuration_issue(
        self,
        features1: Dict[str, Any],
        features2: Dict[str, Any]
    ) -> float:
        """评估配置问题导致的关联性
        
        分析是否由于配置文件或配置相关问题导致多个失败。
        """
        score = 0.0
        
        config_keywords = {"config", "setting", "environment", "variable", "property"}
        
        kw1 = features1.get("error_keywords", set()) & config_keywords
        kw2 = features2.get("error_keywords", set()) & config_keywords
        
        if kw1 and kw2 and kw1 & kw2:
            score += 0.4
        
        code_ctx1 = features1.get("code_context", {})
        code_ctx2 = features2.get("code_context", {})
        
        src_types1 = set(code_ctx1.get("source_file_types", []))
        src_types2 = set(code_ctx2.get("source_file_types", []))
        
        if "config" in src_types1 and "config" in src_types2:
            score += 0.3
        
        dep1 = features1.get("dependency_features", {})
        dep2 = features2.get("dependency_features", {})
        
        if dep1.get("has_external_dependencies") and dep2.get("has_external_dependencies"):
            common_deps = set(dep1.get("dependency_types", [])) & set(dep2.get("dependency_types", []))
            if common_deps:
                score += 0.3
        
        return min(score, 1.0)
    
    def _score_environment_issue(
        self,
        features1: Dict[str, Any],
        features2: Dict[str, Any]
    ) -> float:
        """评估环境问题导致的关联性
        
        分析是否由于环境配置、资源限制等问题导致多个失败。
        """
        score = 0.0
        
        env_keywords = {"permission", "access", "denied", "timeout", "connection", "unavailable"}
        
        kw1 = features1.get("error_keywords", set()) & env_keywords
        kw2 = features2.get("error_keywords", set()) & env_keywords
        
        if kw1 and kw2 and kw1 & kw2:
            score += 0.4
        
        perf1 = features1.get("performance_features", {})
        perf2 = features2.get("performance_features", {})
        
        if perf1.get("has_timeout") and perf2.get("has_timeout"):
            score += 0.3
        
        if perf1.get("is_slow_test") and perf2.get("is_slow_test"):
            score += 0.2
        
        temporal1 = features1.get("temporal_features", {})
        temporal2 = features2.get("temporal_features", {})
        
        if temporal1.get("is_weekend") and temporal2.get("is_weekend"):
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_data_dependency(
        self,
        features1: Dict[str, Any],
        features2: Dict[str, Any]
    ) -> float:
        """评估数据依赖导致的关联性
        
        分析是否由于共享测试数据或数据状态问题导致多个失败。
        """
        score = 0.0
        
        data_keywords = {"data", "value", "state", "record", "entry", "row", "column"}
        
        kw1 = features1.get("error_keywords", set()) & data_keywords
        kw2 = features2.get("error_keywords", set()) & data_keywords
        
        if kw1 and kw2 and kw1 & kw2:
            score += 0.3
        
        fixture1 = features1.get("fixture_features", {})
        fixture2 = features2.get("fixture_features", {})
        
        if fixture1.get("has_db_fixture") and fixture2.get("has_db_fixture"):
            score += 0.3
        
        assertion1 = features1.get("assertion_features", {})
        assertion2 = features2.get("assertion_features", {})
        
        expected1 = set(assertion1.get("expected_values", []))
        expected2 = set(assertion2.get("expected_values", []))
        
        if expected1 and expected2 and expected1 & expected2:
            score += 0.2
        
        dep1 = features1.get("dependency_features", {})
        dep2 = features2.get("dependency_features", {})
        
        if "database" in dep1.get("dependency_types", []) and "database" in dep2.get("dependency_types", []):
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_api_contract(
        self,
        features1: Dict[str, Any],
        features2: Dict[str, Any]
    ) -> float:
        """评估API契约问题导致的关联性
        
        分析是否由于API接口变更或契约不匹配导致多个失败。
        """
        score = 0.0
        
        api_keywords = {"api", "endpoint", "response", "request", "status", "json", "schema"}
        
        kw1 = features1.get("error_keywords", set()) & api_keywords
        kw2 = features2.get("error_keywords", set()) & api_keywords
        
        if kw1 and kw2 and kw1 & kw2:
            score += 0.4
        
        fixture1 = features1.get("fixture_features", {})
        fixture2 = features2.get("fixture_features", {})
        
        if fixture1.get("has_api_fixture") and fixture2.get("has_api_fixture"):
            score += 0.3
        
        dep1 = features1.get("dependency_features", {})
        dep2 = features2.get("dependency_features", {})
        
        if "api" in dep1.get("dependency_types", []) and "api" in dep2.get("dependency_types", []):
            score += 0.3
        
        return min(score, 1.0)
    
    def _merge_related_correlations(
        self,
        correlations: List[CorrelationResult]
    ) -> List[CorrelationResult]:
        """合并相关的关联结果
        
        将重叠的关联结果合并，形成更大的关联组。
        """
        if not correlations:
            return correlations
        
        test_to_correlations: Dict[str, List[CorrelationResult]] = defaultdict(list)
        for corr in correlations:
            for test in corr.related_failures:
                test_to_correlations[test].append(corr)
        
        merged = []
        processed = set()
        
        for corr in correlations:
            if corr.correlation_id in processed:
                continue
            
            related_tests = set(corr.related_failures)
            queue = list(corr.related_failures)
            
            while queue:
                test = queue.pop(0)
                for related_corr in test_to_correlations.get(test, []):
                    if related_corr.correlation_id not in processed:
                        for t in related_corr.related_failures:
                            if t not in related_tests:
                                related_tests.add(t)
                                queue.append(t)
                        processed.add(related_corr.correlation_id)
            
            if len(related_tests) > 2:
                merged_corr = self._create_merged_correlation(corr, list(related_tests))
                merged.append(merged_corr)
            else:
                merged.append(corr)
            processed.add(corr.correlation_id)
        
        return merged
    
    def _create_merged_correlation(
        self,
        base_corr: CorrelationResult,
        all_tests: List[str]
    ) -> CorrelationResult:
        """创建合并后的关联结果
        
        将多个关联结果合并为一个更大的关联组。
        """
        self._correlation_counter += 1
        
        return CorrelationResult(
            correlation_id=f"COR-{self._correlation_counter:03d}",
            correlation_type=base_corr.correlation_type,
            strength=base_corr.strength,
            confidence=base_corr.confidence,
            related_failures=all_tests,
            evidence=base_corr.evidence + [f"合并了 {len(all_tests)} 个相关测试"],
            common_factors=base_corr.common_factors,
            propagation_path=all_tests,
            impact_score=base_corr.impact_score * len(all_tests) / 2,
            fix_recommendation=base_corr.fix_recommendation,
            detailed_analysis={
                "merged": True,
                "original_correlation": base_corr.correlation_id,
                "total_tests": len(all_tests)
            }
        )
    
    def _analyze_propagation_path(
        self,
        failure1: FailureInfo,
        failure2: FailureInfo,
        features1: Dict[str, Any],
        features2: Dict[str, Any]
    ) -> List[str]:
        """分析失败传播路径
        
        识别失败可能如何在测试之间传播。
        """
        path = []
        
        common_funcs = features1["function_patterns"] & features2["function_patterns"]
        if common_funcs:
            path.append(f"共享函数: {', '.join(list(common_funcs)[:2])}")
        
        common_files = features1["file_patterns"] & features2["file_patterns"]
        if common_files:
            path.append(f"共享文件: {', '.join(list(common_files)[:2])}")
        
        fixture1 = features1.get("fixture_features", {})
        fixture2 = features2.get("fixture_features", {})
        common_fixtures = set(fixture1.get("fixture_types", [])) & set(fixture2.get("fixture_types", []))
        if common_fixtures:
            path.append(f"共享Fixture: {', '.join(common_fixtures)}")
        
        dep1 = features1.get("dependency_features", {})
        dep2 = features2.get("dependency_features", {})
        common_deps = set(dep1.get("dependency_types", [])) & set(dep2.get("dependency_types", []))
        if common_deps:
            path.append(f"共享依赖: {', '.join(common_deps)}")
        
        return path
    
    def _calculate_impact_score(
        self,
        failure1: FailureInfo,
        failure2: FailureInfo,
        correlation_score: float
    ) -> float:
        """计算关联的影响分数
        
        评估这个关联对整体测试套件的影响程度。
        """
        base_score = correlation_score
        
        stack_depth = len(failure1.stack_trace) + len(failure2.stack_trace)
        if stack_depth > 10:
            base_score *= 1.2
        
        files_count = len(failure1.affected_files) + len(failure2.affected_files)
        if files_count > 4:
            base_score *= 1.1
        
        if failure1.exception_type in ("ImportError", "SyntaxError", "SystemError"):
            base_score *= 1.3
        if failure2.exception_type in ("ImportError", "SyntaxError", "SystemError"):
            base_score *= 1.3
        
        return min(base_score, 1.0)
    
    def _generate_fix_recommendation(
        self,
        correlation_type: str,
        features1: Dict[str, Any],
        features2: Dict[str, Any]
    ) -> str:
        """生成修复建议
        
        根据关联类型生成具体的修复建议。
        """
        recommendations = {
            "same_root_cause": "修复共同的根因问题，可以同时解决多个测试失败",
            "dependency_chain": "检查依赖链中的问题，修复上游依赖可能解决下游失败",
            "shared_resource": "检查共享资源的配置和状态，确保资源正确初始化和清理",
            "code_proximity": "检查相邻代码的变更，可能是同一处修改导致的问题",
            "test_suite": "检查测试套件的公共设置和fixture配置",
            "configuration_issue": "检查配置文件和环境变量设置",
            "environment_issue": "检查运行环境，包括权限、网络、资源限制等",
            "data_dependency": "检查测试数据的准备和清理逻辑",
            "api_contract": "检查API接口的变更，确保契约一致性",
        }
        
        base_recommendation = recommendations.get(correlation_type, "分析关联失败的具体原因")
        
        specific_hints = []
        
        if features1.get("error_category") == features2.get("error_category"):
            category = features1.get("error_category")
            if category == "assertion":
                specific_hints.append("关注断言逻辑和预期值")
            elif category == "import_error":
                specific_hints.append("检查模块导入路径和依赖安装")
            elif category == "connection_error":
                specific_hints.append("检查网络连接和服务可用性")
        
        fixture1 = features1.get("fixture_features", {})
        fixture2 = features2.get("fixture_features", {})
        if fixture1.get("has_db_fixture") and fixture2.get("has_db_fixture"):
            specific_hints.append("检查数据库fixture的初始化和清理")
        
        if specific_hints:
            return f"{base_recommendation}。提示: {', '.join(specific_hints)}"
        
        return base_recommendation
    
    def _generate_detailed_analysis(
        self,
        correlation_type: str,
        features1: Dict[str, Any],
        features2: Dict[str, Any],
        scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """生成详细分析结果
        
        提供关联分析的详细信息，包括各项得分和分析结论。
        """
        return {
            "correlation_type": correlation_type,
            "score_breakdown": {
                k: round(v, 3) for k, v in scores.items()
            },
            "feature_comparison": {
                "error_signature_match": features1["error_signature"] == features2["error_signature"],
                "exception_type_match": features1["exception_type"] == features2["exception_type"],
                "common_modules_count": len(features1["affected_modules"] & features2["affected_modules"]),
                "common_files_count": len(features1["file_patterns"] & features2["file_patterns"]),
                "common_functions_count": len(features1["function_patterns"] & features2["function_patterns"]),
            },
            "error_categories": {
                "failure1": features1.get("error_category", "unknown"),
                "failure2": features2.get("error_category", "unknown"),
            },
            "dependency_analysis": {
                "failure1_has_external_deps": features1.get("dependency_features", {}).get("has_external_dependencies", False),
                "failure2_has_external_deps": features2.get("dependency_features", {}).get("has_external_dependencies", False),
            },
            "fixture_analysis": {
                "failure1_fixture_types": features1.get("fixture_features", {}).get("fixture_types", []),
                "failure2_fixture_types": features2.get("fixture_features", {}).get("fixture_types", []),
            }
        }


class CommonRootCauseIdentifier:
    """共同根因识别器
    
    分析多个失败的共同根因，识别问题模式并生成修复建议。
    支持多种根因类型：代码缺陷、配置问题、环境问题、数据问题等。
    """
    
    def __init__(self):
        self._root_cause_counter = 0
        
        self._category_keywords = {
            "code_defect": ["assertion", "type", "value", "attribute", "index"],
            "configuration": ["config", "setting", "environment", "variable"],
            "environment": ["permission", "access", "timeout", "connection", "resource"],
            "data_issue": ["data", "value", "state", "record", "null", "empty"],
            "dependency": ["import", "module", "package", "dependency"],
            "api_issue": ["api", "endpoint", "response", "request", "status"],
        }
        
        self._fix_templates = {
            "code_defect": {
                "TypeError": "检查类型转换，确保参数类型正确",
                "ValueError": "验证输入值范围，添加边界检查",
                "KeyError": "使用 dict.get() 或检查键是否存在",
                "IndexError": "添加索引边界检查",
                "AttributeError": "检查对象属性是否存在，使用 hasattr()",
                "AssertionError": "检查断言条件，验证预期结果",
            },
            "configuration": {
                "default": "检查配置文件和环境变量设置",
                "missing": "添加缺失的配置项",
                "invalid": "修正配置项的值",
            },
            "environment": {
                "default": "检查运行环境配置",
                "permission": "检查文件和目录权限",
                "timeout": "增加超时时间或优化性能",
                "connection": "检查网络连接和服务可用性",
            },
            "data_issue": {
                "default": "检查测试数据的准备和清理",
                "null": "添加空值检查和处理",
                "empty": "处理空数据情况",
            },
            "dependency": {
                "ImportError": "安装缺失的依赖包",
                "ModuleNotFoundError": "检查模块路径和导入语句",
                "default": "检查依赖版本和兼容性",
            },
            "api_issue": {
                "default": "检查API接口契约",
                "status": "处理不同的HTTP状态码",
                "response": "验证响应数据格式",
            },
        }
    
    def identify_root_causes(
        self,
        failures: List[FailureInfo],
        correlations: List[CorrelationResult]
    ) -> List[CommonRootCause]:
        """识别所有失败的共同根因
        
        分析失败和关联关系，识别共同根因并生成修复建议。
        
        Args:
            failures: 失败信息列表
            correlations: 关联分析结果列表
            
        Returns:
            共同根因列表，按优先级排序
        """
        root_causes = []
        
        strong_correlations = [
            c for c in correlations
            if c.strength == CorrelationStrength.STRONG
        ]
        
        medium_correlations = [
            c for c in correlations
            if c.strength == CorrelationStrength.MEDIUM
        ]
        
        clusters = self._cluster_failures(strong_correlations + medium_correlations)
        
        for cluster_tests in clusters.values():
            cluster_failures = [
                f for f in failures
                if f.test_name in cluster_tests
            ]
            
            if len(cluster_failures) >= 2:
                root_cause = self._identify_cluster_root_cause(cluster_failures)
                if root_cause:
                    root_causes.append(root_cause)
        
        for failure in failures:
            if not any(failure.test_name in rc.affected_tests for rc in root_causes):
                individual_root_cause = self._identify_individual_root_cause(failure)
                if individual_root_cause:
                    root_causes.append(individual_root_cause)
        
        root_causes = self._deduplicate_root_causes(root_causes)
        
        return sorted(root_causes, key=lambda rc: rc.fix_priority, reverse=True)
    
    def _cluster_failures(
        self,
        correlations: List[CorrelationResult]
    ) -> Dict[str, Set[str]]:
        """将失败的测试聚类
        
        根据关联关系将失败的测试分组到不同的簇中。
        """
        clusters: Dict[str, Set[str]] = defaultdict(set)
        cluster_id = 0
        
        for correlation in correlations:
            related_tests = correlation.related_failures
            
            found_cluster = None
            for cid, tests in clusters.items():
                if any(test in tests for test in related_tests):
                    found_cluster = cid
                    break
            
            if found_cluster:
                for test in related_tests:
                    clusters[found_cluster].add(test)
            else:
                cluster_id += 1
                clusters[f"cluster_{cluster_id}"] = set(related_tests)
        
        return self._merge_overlapping_clusters(clusters)
    
    def _merge_overlapping_clusters(
        self,
        clusters: Dict[str, Set[str]]
    ) -> Dict[str, Set[str]]:
        """合并重叠的簇
        
        如果两个簇有共同的测试，则将它们合并。
        """
        merged = True
        while merged:
            merged = False
            cluster_list = list(clusters.items())
            
            for i, (cid1, tests1) in enumerate(cluster_list):
                for j, (cid2, tests2) in enumerate(cluster_list[i+1:], i+1):
                    if tests1 & tests2:
                        clusters[cid1] = tests1 | tests2
                        del clusters[cid2]
                        merged = True
                        break
                if merged:
                    break
        
        return clusters
    
    def _identify_cluster_root_cause(
        self,
        failures: List[FailureInfo]
    ) -> Optional[CommonRootCause]:
        """识别一个簇的共同根因
        
        分析簇内所有失败，识别共同根因。
        """
        if not failures:
            return None
        
        self._root_cause_counter += 1
        
        common_files = self._find_common_files(failures)
        common_exception = self._find_common_exception(failures)
        common_patterns = self._extract_common_patterns([f.error_message for f in failures])
        root_cause_category = self._categorize_root_cause(failures, common_patterns, common_exception)
        
        description = self._generate_description(failures, common_patterns, common_exception, root_cause_category)
        suggested_fix = self._generate_suggested_fix(common_patterns, common_exception, root_cause_category)
        
        affected_tests = [f.test_name for f in failures]
        affected_files = list(common_files) if common_files else list(set(
            f for failure in failures for f in failure.affected_files
        ))
        
        confidence = self._calculate_confidence(failures, common_patterns, common_exception)
        priority = self._calculate_priority(failures, common_exception, root_cause_category)
        fix_complexity = self._estimate_fix_complexity(failures, common_files, common_exception)
        estimated_time = self._estimate_fix_time(failures, fix_complexity)
        dependencies = self._identify_dependencies(failures)
        code_snippets = self._extract_code_snippets(failures)
        verification_commands = self._generate_verification_commands(failures, affected_files)
        
        return CommonRootCause(
            root_cause_id=f"RC-{self._root_cause_counter:03d}",
            description=description,
            affected_tests=affected_tests,
            affected_files=affected_files,
            confidence=confidence,
            fix_priority=priority,
            suggested_fix=suggested_fix,
            root_cause_category=root_cause_category,
            fix_complexity=fix_complexity,
            estimated_time_minutes=estimated_time,
            dependencies=dependencies,
            code_snippets=code_snippets,
            verification_commands=verification_commands
        )
    
    def _identify_individual_root_cause(
        self,
        failure: FailureInfo
    ) -> Optional[CommonRootCause]:
        """识别单个失败的根因
        
        为孤立的失败生成根因分析。
        """
        self._root_cause_counter += 1
        
        root_cause_category = self._categorize_single_failure(failure)
        
        description = f"单个测试失败: {failure.error_message[:100]}"
        suggested_fix = self._generate_individual_fix(failure, root_cause_category)
        
        fix_complexity = self._estimate_single_fix_complexity(failure)
        estimated_time = self._estimate_single_fix_time(failure)
        verification_commands = self._generate_single_verification_commands(failure)
        
        return CommonRootCause(
            root_cause_id=f"RC-{self._root_cause_counter:03d}",
            description=description,
            affected_tests=[failure.test_name],
            affected_files=failure.affected_files,
            confidence=0.6,
            fix_priority=2,
            suggested_fix=suggested_fix,
            root_cause_category=root_cause_category,
            fix_complexity=fix_complexity,
            estimated_time_minutes=estimated_time,
            verification_commands=verification_commands
        )
    
    def _find_common_files(self, failures: List[FailureInfo]) -> Set[str]:
        """找出所有失败共同的文件
        
        返回在所有失败中都出现的文件列表。
        """
        if not failures:
            return set()
        
        common_files = set(failures[0].affected_files)
        for failure in failures[1:]:
            common_files &= set(failure.affected_files)
        
        return common_files
    
    def _find_common_exception(self, failures: List[FailureInfo]) -> Optional[str]:
        """找出所有失败共同的异常类型
        
        如果所有失败都有相同的异常类型，返回该类型，否则返回None。
        """
        if not failures:
            return None
        
        common_exception = failures[0].exception_type
        for failure in failures[1:]:
            if failure.exception_type != common_exception:
                return None
        
        return common_exception
    
    def _categorize_root_cause(
        self,
        failures: List[FailureInfo],
        common_patterns: List[str],
        common_exception: Optional[str]
    ) -> str:
        """对根因进行分类
        
        根据错误模式和异常类型，将根因归类到预定义的类别中。
        """
        all_text = " ".join(common_patterns).lower()
        all_text += " " + " ".join(f.exception_type or "" for f in failures)
        
        category_scores = {}
        for category, keywords in self._category_keywords.items():
            score = sum(1 for kw in keywords if kw in all_text)
            category_scores[category] = score
        
        if common_exception:
            if common_exception in ("ImportError", "ModuleNotFoundError"):
                return "dependency"
            if common_exception in ("ConnectionError", "TimeoutError"):
                return "environment"
        
        best_category = max(category_scores.keys(), key=lambda k: category_scores[k])
        
        if category_scores[best_category] == 0:
            return "code_defect"
        
        return best_category
    
    def _categorize_single_failure(self, failure: FailureInfo) -> str:
        """对单个失败的根因进行分类"""
        error_text = f"{failure.error_message} {failure.exception_type or ''}".lower()
        
        for category, keywords in self._category_keywords.items():
            if any(kw in error_text for kw in keywords):
                return category
        
        return "code_defect"
    
    def _extract_common_patterns(self, messages: List[str]) -> List[str]:
        """从错误消息中提取共同模式
        
        找出所有消息中都出现的关键词。
        """
        if not messages:
            return []
        
        patterns = []
        words_list = [set(re.findall(r'\w+', msg.lower())) for msg in messages]
        
        if words_list:
            common_words = words_list[0]
            for words in words_list[1:]:
                common_words &= words
            
            stop_words = {"the", "and", "for", "with", "from", "this", "that", "has", "have", "been", "was", "were"}
            significant_words = {
                w for w in common_words
                if len(w) > 3 and w not in stop_words
            }
            patterns.extend(list(significant_words)[:5])
        
        return patterns
    
    def _generate_description(
        self,
        failures: List[FailureInfo],
        common_patterns: List[str],
        common_exception: Optional[str],
        category: str
    ) -> str:
        """生成根因描述
        
        创建包含关键信息的根因描述。
        """
        category_names = {
            "code_defect": "代码缺陷",
            "configuration": "配置问题",
            "environment": "环境问题",
            "data_issue": "数据问题",
            "dependency": "依赖问题",
            "api_issue": "API问题",
        }
        
        parts = [f"[{category_names.get(category, '未知')}] 影响 {len(failures)} 个测试"]
        
        if common_exception:
            parts.append(f"异常: {common_exception}")
        
        if common_patterns:
            parts.append(f"特征: {', '.join(common_patterns[:3])}")
        
        test_names = [f.test_name.split("::")[-1] for f in failures[:3]]
        parts.append(f"测试: {', '.join(test_names)}")
        
        return " | ".join(parts)
    
    def _generate_suggested_fix(
        self,
        common_patterns: List[str],
        common_exception: Optional[str],
        category: str
    ) -> str:
        """生成修复建议
        
        根据根因类型和错误模式生成具体的修复建议。
        """
        fixes = []
        
        if category in self._fix_templates:
            template = self._fix_templates[category]
            
            if common_exception and common_exception in template:
                fixes.append(template[common_exception])
            elif "default" in template:
                fixes.append(template["default"])
        
        if "none" in common_patterns or "null" in common_patterns:
            fixes.append("添加空值检查和处理逻辑")
        
        if "empty" in common_patterns:
            fixes.append("处理空数据情况")
        
        if "file" in common_patterns:
            fixes.append("检查文件路径和权限")
        
        if "connection" in common_patterns:
            fixes.append("检查网络连接和服务状态")
        
        if not fixes:
            fixes.append("分析错误日志并检查相关代码")
        
        return "; ".join(fixes[:3])
    
    def _generate_individual_fix(self, failure: FailureInfo, category: str) -> str:
        """为单个失败生成修复建议"""
        if failure.exception_type and category in self._fix_templates:
            template = self._fix_templates[category]
            if failure.exception_type in template:
                return template[failure.exception_type]
        
        if failure.exception_type:
            return f"处理 {failure.exception_type}: {failure.error_message[:50]}"
        
        return f"检查测试失败原因: {failure.error_message[:50]}"
    
    def _calculate_confidence(
        self,
        failures: List[FailureInfo],
        common_patterns: List[str],
        common_exception: Optional[str]
    ) -> float:
        """计算根因识别的置信度
        
        基于多个因素评估根因识别的可信程度。
        """
        confidence = 0.5
        
        if len(failures) >= 3:
            confidence += 0.1
        if len(failures) >= 5:
            confidence += 0.1
        
        if common_patterns:
            confidence += 0.05 * min(len(common_patterns), 3)
        
        if common_exception:
            confidence += 0.15
        
        common_files = self._find_common_files(failures)
        if common_files:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_priority(
        self,
        failures: List[FailureInfo],
        common_exception: Optional[str],
        category: str
    ) -> int:
        """计算修复优先级
        
        基于影响范围和问题严重程度计算优先级。
        """
        priority = len(failures)
        
        critical_exceptions = {"ImportError", "SyntaxError", "SystemError", "MemoryError"}
        if common_exception in critical_exceptions:
            priority += 5
        
        high_priority_categories = {"configuration", "environment", "dependency"}
        if category in high_priority_categories:
            priority += 3
        
        for failure in failures:
            if failure.exception_type in critical_exceptions:
                priority += 1
        
        return min(priority, 10)
    
    def _estimate_fix_complexity(
        self,
        failures: List[FailureInfo],
        common_files: Set[str],
        common_exception: Optional[str]
    ) -> str:
        """评估修复复杂度
        
        估计修复所需的复杂程度。
        """
        complexity_score = 0
        
        if len(failures) > 5:
            complexity_score += 2
        elif len(failures) > 2:
            complexity_score += 1
        
        if len(common_files) > 3:
            complexity_score += 2
        elif len(common_files) > 1:
            complexity_score += 1
        
        simple_exceptions = {"AssertionError", "ValueError", "KeyError"}
        complex_exceptions = {"ImportError", "ConnectionError", "TimeoutError"}
        
        if common_exception in complex_exceptions:
            complexity_score += 2
        elif common_exception not in simple_exceptions:
            complexity_score += 1
        
        if complexity_score <= 2:
            return "low"
        elif complexity_score <= 4:
            return "medium"
        else:
            return "high"
    
    def _estimate_fix_time(
        self,
        failures: List[FailureInfo],
        complexity: str
    ) -> int:
        """估计修复所需时间（分钟）
        
        基于复杂度和失败数量估计修复时间。
        """
        base_times = {
            "low": 15,
            "medium": 45,
            "high": 120,
        }
        
        base_time = base_times.get(complexity, 30)
        
        if len(failures) > 3:
            base_time = int(base_time * 1.5)
        
        return base_time
    
    def _estimate_single_fix_complexity(self, failure: FailureInfo) -> str:
        """评估单个失败修复的复杂度"""
        if len(failure.stack_trace) > 5:
            return "medium"
        
        if failure.exception_type in ("ImportError", "ConnectionError"):
            return "medium"
        
        return "low"
    
    def _estimate_single_fix_time(self, failure: FailureInfo) -> int:
        """估计单个失败修复所需时间"""
        complexity = self._estimate_single_fix_complexity(failure)
        return {"low": 15, "medium": 30, "high": 60}.get(complexity, 20)
    
    def _identify_dependencies(self, failures: List[FailureInfo]) -> List[str]:
        """识别修复的依赖关系
        
        找出修复前需要先处理的其他问题。
        """
        dependencies = []
        
        for failure in failures:
            if failure.exception_type == "ImportError":
                module_match = re.search(r"No module named '(\w+)'", failure.error_message)
                if module_match:
                    dependencies.append(f"安装模块: {module_match.group(1)}")
            
            if "connection" in failure.error_message.lower():
                dependencies.append("确保相关服务已启动")
        
        return list(set(dependencies))
    
    def _extract_code_snippets(self, failures: List[FailureInfo]) -> List[Dict[str, str]]:
        """提取相关代码片段信息
        
        从失败信息中提取可能需要修改的代码位置。
        """
        snippets = []
        
        for failure in failures[:3]:
            if failure.stack_trace:
                frame = failure.stack_trace[0]
                snippets.append({
                    "file": frame.get("file_path", ""),
                    "line": str(frame.get("line_number", "")),
                    "function": frame.get("function_name", ""),
                    "test": failure.test_name
                })
        
        return snippets
    
    def _generate_verification_commands(
        self,
        failures: List[FailureInfo],
        affected_files: List[str]
    ) -> List[str]:
        """生成验证命令
        
        生成用于验证修复是否成功的命令。
        """
        commands = []
        
        test_files = set()
        for failure in failures:
            if failure.test_file:
                test_files.add(failure.test_file)
        
        for test_file in list(test_files)[:3]:
            commands.append(f"pytest {test_file} -v")
        
        if affected_files:
            for file in affected_files[:2]:
                if file.endswith(".py"):
                    commands.append(f"python -m py_compile {file}")
        
        return commands
    
    def _generate_single_verification_commands(self, failure: FailureInfo) -> List[str]:
        """为单个失败生成验证命令"""
        commands = []
        
        if failure.test_file:
            commands.append(f"pytest {failure.test_file}::{failure.test_name.split('::')[-1]} -v")
        
        return commands
    
    def _deduplicate_root_causes(self, root_causes: List[CommonRootCause]) -> List[CommonRootCause]:
        """去除重复的根因
        
        合并相似或重复的根因。
        """
        if len(root_causes) <= 1:
            return root_causes
        
        unique_causes = []
        seen_descriptions = set()
        
        for rc in root_causes:
            desc_key = rc.description[:50]
            if desc_key not in seen_descriptions:
                seen_descriptions.add(desc_key)
                unique_causes.append(rc)
            else:
                for existing in unique_causes:
                    if existing.description[:50] == desc_key:
                        existing.affected_tests = list(set(existing.affected_tests + rc.affected_tests))
                        existing.affected_files = list(set(existing.affected_files + rc.affected_files))
                        break
        
        return unique_causes


class ComprehensiveFixPlanGenerator:
    """综合修复方案生成器
    
    根据根因分析结果生成详细的修复计划，包括修复步骤、优先级、
    工作量估计、风险评估和验证方案。
    """
    
    def __init__(self):
        self._plan_counter = 0
        
        self._effort_multipliers = {
            "low": 1.0,
            "medium": 2.0,
            "high": 4.0,
        }
        
        self._risk_factors = {
            "code_defect": {"risk": "medium", "impact": "localized"},
            "configuration": {"risk": "high", "impact": "widespread"},
            "environment": {"risk": "high", "impact": "widespread"},
            "data_issue": {"risk": "medium", "impact": "localized"},
            "dependency": {"risk": "high", "impact": "widespread"},
            "api_issue": {"risk": "medium", "impact": "localized"},
        }
    
    def generate_plan(
        self,
        root_causes: List[CommonRootCause],
        correlations: List[CorrelationResult]
    ) -> ComprehensiveFixPlan:
        """生成综合修复计划
        
        根据根因和关联分析结果，生成完整的修复方案。
        
        Args:
            root_causes: 识别出的根因列表
            correlations: 关联分析结果列表
            
        Returns:
            综合修复计划对象
        """
        self._plan_counter += 1
        
        sorted_causes = self._prioritize_root_causes(root_causes, correlations)
        
        fix_steps = self._generate_fix_steps(sorted_causes)
        
        priority_order = [rc.root_cause_id for rc in sorted_causes]
        
        verification_steps = self._generate_verification_steps(sorted_causes)
        
        estimated_effort = self._estimate_effort(sorted_causes)
        
        risk_assessment = self._assess_risks(sorted_causes)
        
        rollback_plan = self._generate_rollback_plan(sorted_causes)
        
        return ComprehensiveFixPlan(
            plan_id=f"FP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._plan_counter:03d}",
            title="综合修复方案",
            description=self._generate_plan_description(sorted_causes, correlations),
            root_causes=sorted_causes,
            fix_steps=fix_steps,
            estimated_effort=estimated_effort,
            priority_order=priority_order,
            verification_steps=verification_steps
        )
    
    def _prioritize_root_causes(
        self,
        root_causes: List[CommonRootCause],
        correlations: List[CorrelationResult]
    ) -> List[CommonRootCause]:
        """对根因进行优先级排序
        
        综合考虑影响范围、严重程度和依赖关系来确定修复顺序。
        """
        cause_scores = {}
        
        for rc in root_causes:
            score = rc.fix_priority * 10
            
            score += len(rc.affected_tests) * 2
            
            score += len(rc.affected_files) * 3
            
            if rc.root_cause_category in ("configuration", "environment", "dependency"):
                score += 5
            
            if rc.fix_complexity == "low":
                score += 3
            elif rc.fix_complexity == "high":
                score -= 2
            
            cause_scores[rc.root_cause_id] = score
        
        return sorted(root_causes, key=lambda rc: cause_scores.get(rc.root_cause_id, 0), reverse=True)
    
    def _generate_plan_description(
        self,
        root_causes: List[CommonRootCause],
        correlations: List[CorrelationResult]
    ) -> str:
        """生成修复计划描述
        
        创建包含关键统计信息的计划描述。
        """
        total_tests = sum(len(rc.affected_tests) for rc in root_causes)
        total_files = len(set(f for rc in root_causes for f in rc.affected_files))
        
        categories = set(rc.root_cause_category for rc in root_causes)
        category_names = {
            "code_defect": "代码缺陷",
            "configuration": "配置问题",
            "environment": "环境问题",
            "data_issue": "数据问题",
            "dependency": "依赖问题",
            "api_issue": "API问题",
        }
        category_str = "、".join(category_names.get(c, c) for c in categories)
        
        strong_corrs = len([c for c in correlations if c.strength == CorrelationStrength.STRONG])
        
        return (f"针对 {len(root_causes)} 个根因的综合修复计划，"
                f"涉及 {total_tests} 个测试、{total_files} 个文件。"
                f"问题类型: {category_str}。"
                f"发现 {strong_corrs} 个强关联。")
    
    def _generate_fix_steps(self, root_causes: List[CommonRootCause]) -> List[Dict[str, Any]]:
        """生成详细的修复步骤
        
        为每个根因创建具体的修复步骤，包括前置条件和验证方法。
        """
        steps = []
        step_num = 1
        
        for rc in root_causes:
            step = {
                "step": step_num,
                "root_cause_id": rc.root_cause_id,
                "category": rc.root_cause_category,
                "action": rc.suggested_fix,
                "affected_tests": rc.affected_tests,
                "affected_files": rc.affected_files,
                "priority": self._get_step_priority(rc),
                "complexity": rc.fix_complexity,
                "estimated_minutes": rc.estimated_time_minutes,
                "dependencies": rc.dependencies if hasattr(rc, 'dependencies') else [],
                "verification": rc.verification_commands[:2] if hasattr(rc, 'verification_commands') else [],
                "code_locations": rc.code_snippets[:3] if hasattr(rc, 'code_snippets') else [],
            }
            
            preconditions = self._identify_preconditions(rc, root_causes[:root_causes.index(rc)])
            if preconditions:
                step["preconditions"] = preconditions
            
            steps.append(step)
            step_num += 1
        
        all_tests = list(set(test for rc in root_causes for test in rc.affected_tests))
        steps.append({
            "step": step_num,
            "root_cause_id": "final_verification",
            "category": "verification",
            "action": "运行所有失败的测试验证修复",
            "affected_tests": all_tests,
            "affected_files": [],
            "priority": "high",
            "complexity": "low",
            "estimated_minutes": 10,
            "dependencies": [rc.root_cause_id for rc in root_causes],
        })
        
        return steps
    
    def _get_step_priority(self, root_cause: CommonRootCause) -> str:
        """获取步骤优先级
        
        根据根因特征确定修复步骤的优先级。
        """
        if root_cause.fix_priority >= 7:
            return "critical"
        elif root_cause.fix_priority >= 5:
            return "high"
        elif root_cause.fix_priority >= 3:
            return "medium"
        else:
            return "low"
    
    def _identify_preconditions(
        self,
        current_rc: CommonRootCause,
        previous_rcs: List[CommonRootCause]
    ) -> List[str]:
        """识别修复的前置条件
        
        找出当前修复步骤依赖的前置条件。
        """
        preconditions = []
        
        if hasattr(current_rc, 'dependencies'):
            preconditions.extend(current_rc.dependencies)
        
        for prev_rc in previous_rcs:
            if set(prev_rc.affected_files) & set(current_rc.affected_files):
                preconditions.append(f"完成 {prev_rc.root_cause_id} 的修复")
        
        return list(set(preconditions))[:5]
    
    def _generate_verification_steps(self, root_causes: List[CommonRootCause]) -> List[str]:
        """生成验证步骤
        
        创建详细的验证流程，确保修复有效。
        """
        steps = []
        
        all_tests = list(set(
            test for rc in root_causes for test in rc.affected_tests
        ))
        
        all_files = list(set(
            f for rc in root_causes for f in rc.affected_files
        ))
        
        steps.append(f"1. 逐个运行修复后的测试文件，验证单个修复")
        steps.append(f"2. 运行所有失败的测试 ({len(all_tests)} 个)，确认全部通过")
        steps.append("3. 检查是否引入新的测试失败")
        steps.append("4. 运行完整的测试套件，确保没有回归问题")
        steps.append("5. 代码审查确认修复质量和代码风格")
        
        if any(rc.root_cause_category in ("configuration", "environment") for rc in root_causes):
            steps.append("6. 验证配置变更在不同环境下的正确性")
        
        if any(rc.root_cause_category == "dependency" for rc in root_causes):
            steps.append("7. 验证依赖版本兼容性")
        
        steps.append(f"8. 更新相关文档和注释")
        
        return steps
    
    def _estimate_effort(self, root_causes: List[CommonRootCause]) -> str:
        """估计修复工作量
        
        综合评估修复所需的时间和资源。
        """
        total_minutes = sum(rc.estimated_time_minutes for rc in root_causes)
        
        total_tests = sum(len(rc.affected_tests) for rc in root_causes)
        total_files = len(set(f for rc in root_causes for f in rc.affected_files))
        
        complexity_factor = 1.0
        high_complexity_count = sum(1 for rc in root_causes if rc.fix_complexity == "high")
        if high_complexity_count > 2:
            complexity_factor = 1.5
        elif high_complexity_count > 0:
            complexity_factor = 1.2
        
        adjusted_minutes = int(total_minutes * complexity_factor)
        
        if adjusted_minutes <= 60:
            effort_level = "低"
            time_range = "< 1小时"
        elif adjusted_minutes <= 240:
            effort_level = "中"
            time_range = "1-4小时"
        else:
            effort_level = "高"
            time_range = "> 4小时"
        
        return f"{effort_level} (预计 {time_range}，约 {adjusted_minutes} 分钟)"
    
    def _assess_risks(self, root_causes: List[CommonRootCause]) -> Dict[str, Any]:
        """评估修复风险
        
        分析修复过程中可能遇到的风险。
        """
        risks = {
            "overall_risk": "low",
            "risk_factors": [],
            "mitigation_strategies": [],
        }
        
        categories = [rc.root_cause_category for rc in root_causes]
        
        if "configuration" in categories or "environment" in categories:
            risks["risk_factors"].append("配置/环境变更可能影响其他测试")
            risks["mitigation_strategies"].append("在隔离环境中测试配置变更")
        
        if "dependency" in categories:
            risks["risk_factors"].append("依赖更新可能导致兼容性问题")
            risks["mitigation_strategies"].append("检查依赖版本兼容性")
        
        if len(root_causes) > 5:
            risks["risk_factors"].append("根因数量较多，修复顺序重要")
            risks["mitigation_strategies"].append("按优先级顺序修复，逐步验证")
        
        affected_files = set(f for rc in root_causes for f in rc.affected_files)
        if len(affected_files) > 10:
            risks["risk_factors"].append("涉及文件较多，可能引入新问题")
            risks["mitigation_strategies"].append("进行充分的代码审查")
        
        if len(risks["risk_factors"]) > 2:
            risks["overall_risk"] = "high"
        elif len(risks["risk_factors"]) > 0:
            risks["overall_risk"] = "medium"
        
        return risks
    
    def _generate_rollback_plan(self, root_causes: List[CommonRootCause]) -> List[str]:
        """生成回滚计划
        
        提供应对修复失败的回滚策略。
        """
        plan = []
        
        plan.append("1. 使用版本控制系统创建修复前的分支")
        plan.append("2. 记录所有修改的文件和配置")
        
        config_categories = ["configuration", "environment"]
        if any(rc.root_cause_category in config_categories for rc in root_causes):
            plan.append("3. 备份当前配置文件")
            plan.append("4. 记录环境变量和设置")
        
        plan.append("5. 如果修复失败，使用 git revert 或 git reset 回滚")
        plan.append("6. 恢复备份的配置文件")
        plan.append("7. 重新运行测试确认回滚成功")
        
        return plan


class CorrelatedFailureAnalyzer:
    """关联失败分析器主类"""
    
    def __init__(self):
        self.feature_extractor = FailureFeatureExtractor()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.root_cause_identifier = CommonRootCauseIdentifier()
        self.fix_plan_generator = ComprehensiveFixPlanGenerator()
        
        self._analysis_history: List[Dict[str, Any]] = []
    
    def analyze(
        self,
        failures: List[FailureInfo]
    ) -> Dict[str, Any]:
        """分析测试失败
        
        执行完整的关联失败分析流程，包括关联分析、根因识别和修复方案生成。
        
        Args:
            failures: 失败信息列表
            
        Returns:
            包含完整分析结果的字典
        """
        if not failures:
            return {
                "status": "no_failures",
                "message": "没有失败需要分析"
            }
        
        correlations = self.correlation_analyzer.analyze_correlations(failures)
        
        root_causes = self.root_cause_identifier.identify_root_causes(failures, correlations)
        
        fix_plan = self.fix_plan_generator.generate_plan(root_causes, correlations)
        
        analysis_result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_failures": len(failures),
                "total_correlations": len(correlations),
                "strong_correlations": len([c for c in correlations if c.strength == CorrelationStrength.STRONG]),
                "medium_correlations": len([c for c in correlations if c.strength == CorrelationStrength.MEDIUM]),
                "weak_correlations": len([c for c in correlations if c.strength == CorrelationStrength.WEAK]),
                "root_causes_identified": len(root_causes),
                "categories": list(set(rc.root_cause_category for rc in root_causes)),
                "total_affected_files": len(set(f for rc in root_causes for f in rc.affected_files)),
                "estimated_total_time_minutes": sum(rc.estimated_time_minutes for rc in root_causes),
            },
            "correlations": [
                {
                    "correlation_id": c.correlation_id,
                    "type": c.correlation_type.value,
                    "strength": c.strength.value,
                    "confidence": c.confidence,
                    "related_failures": c.related_failures,
                    "evidence": c.evidence,
                    "common_factors": c.common_factors,
                    "propagation_path": c.propagation_path,
                    "impact_score": c.impact_score,
                    "fix_recommendation": c.fix_recommendation,
                    "detailed_analysis": c.detailed_analysis,
                }
                for c in correlations
            ],
            "root_causes": [
                {
                    "root_cause_id": rc.root_cause_id,
                    "description": rc.description,
                    "affected_tests": rc.affected_tests,
                    "affected_files": rc.affected_files,
                    "confidence": rc.confidence,
                    "fix_priority": rc.fix_priority,
                    "suggested_fix": rc.suggested_fix,
                    "root_cause_category": rc.root_cause_category,
                    "fix_complexity": rc.fix_complexity,
                    "estimated_time_minutes": rc.estimated_time_minutes,
                    "dependencies": rc.dependencies,
                    "code_snippets": rc.code_snippets,
                    "verification_commands": rc.verification_commands,
                }
                for rc in root_causes
            ],
            "fix_plan": {
                "plan_id": fix_plan.plan_id,
                "title": fix_plan.title,
                "description": fix_plan.description,
                "estimated_effort": fix_plan.estimated_effort,
                "priority_order": fix_plan.priority_order,
                "fix_steps": fix_plan.fix_steps,
                "verification_steps": fix_plan.verification_steps
            }
        }
        
        self._analysis_history.append(analysis_result)
        
        return analysis_result
    
    def analyze_from_pytest_output(self, pytest_output: str) -> Dict[str, Any]:
        failures = self._parse_pytest_output(pytest_output)
        return self.analyze(failures)
    
    def analyze_from_file(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if file_path.endswith(".json"):
            data = json.loads(content)
            if isinstance(data, list):
                failures = [
                    FailureInfo(
                        test_name=item.get("test_name", ""),
                        test_file=item.get("test_file", ""),
                        failure_type=item.get("failure_type", "unknown"),
                        error_message=item.get("error_message", ""),
                        exception_type=item.get("exception_type"),
                        stack_trace=item.get("stack_trace", []),
                        affected_files=item.get("affected_files", []),
                        affected_functions=item.get("affected_functions", [])
                    )
                    for item in data
                ]
            else:
                failures = self._parse_pytest_output(content)
        else:
            failures = self._parse_pytest_output(content)
        
        return self.analyze(failures)
    
    def _parse_pytest_output(self, output: str) -> List[FailureInfo]:
        failures = []
        
        pattern = r"(FAILED|ERROR)\s+([^\s]+)"
        for match in re.finditer(pattern, output):
            test_name = match.group(2)
            
            block_start = match.start()
            next_match = re.search(pattern, output[block_start + 1:])
            if next_match:
                block_end = block_start + 1 + next_match.start()
            else:
                block_end = len(output)
            
            block = output[block_start:block_end]
            
            failure = self._parse_failure_block(test_name, block)
            failures.append(failure)
        
        return failures
    
    def _parse_failure_block(self, test_name: str, block: str) -> FailureInfo:
        test_file = ""
        file_match = re.search(r'File\s+"([^"]+)"', block)
        if file_match:
            test_file = file_match.group(1)
        
        error_message = ""
        lines = block.strip().split("\n")
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith((" ", "\t", "File", "During", "Traceback")):
                if re.search(r"(Error|Exception|assert)", line):
                    error_message = line
                    break
        
        if not error_message:
            error_message = "Unknown error"
        
        exception_type = None
        exc_match = re.search(r"(\w+(?:Error|Exception)):", block)
        if exc_match:
            exception_type = exc_match.group(1)
        
        stack_trace = []
        frame_pattern = r'File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+(\w+)'
        for match in re.finditer(frame_pattern, block):
            stack_trace.append({
                "file_path": match.group(1),
                "line_number": int(match.group(2)),
                "function_name": match.group(3)
            })
        
        affected_files = list(set(
            frame["file_path"] for frame in stack_trace
            if "site-packages" not in frame["file_path"]
        ))
        
        affected_functions = list(set(
            frame["function_name"] for frame in stack_trace
        ))
        
        return FailureInfo(
            test_name=test_name,
            test_file=test_file,
            failure_type="error" if "ERROR" in block[:20] else "failure",
            error_message=error_message,
            exception_type=exception_type,
            stack_trace=stack_trace,
            affected_files=affected_files,
            affected_functions=affected_functions
        )
    
    def generate_report_markdown(self, analysis_result: Dict[str, Any]) -> str:
        """生成Markdown格式的分析报告
        
        创建详细的Markdown报告，包含摘要、关联分析、根因分析和修复方案。
        
        Args:
            analysis_result: 分析结果字典
            
        Returns:
            Markdown格式的报告字符串
        """
        lines = [
            "# 关联失败分析报告",
            "",
            f"**生成时间**: {analysis_result.get('timestamp', '')}",
            "",
            "---",
            "",
            "## 📊 分析摘要",
            "",
        ]
        
        summary = analysis_result.get("summary", {})
        total_failures = summary.get('total_failures', 0)
        total_correlations = summary.get('total_correlations', 0)
        strong_correlations = summary.get('strong_correlations', 0)
        root_causes = summary.get('root_causes_identified', 0)
        
        lines.extend([
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 总失败数 | {total_failures} |",
            f"| 关联数 | {total_correlations} |",
            f"| 强关联数 | {strong_correlations} |",
            f"| 识别的根因数 | {root_causes} |",
            "",
        ])
        
        if strong_correlations > 0:
            reduction_rate = (strong_correlations * 2 / total_failures * 100) if total_failures > 0 else 0
            lines.extend([
                f"> 💡 **提示**: 发现 {strong_correlations} 个强关联，修复对应的根因可能同时解决约 {reduction_rate:.0f}% 的失败。",
                "",
            ])
        
        correlations = analysis_result.get("correlations", [])
        if correlations:
            lines.extend([
                "---",
                "",
                "## 🔗 关联分析详情",
                "",
            ])
            
            strong_corrs = [c for c in correlations if c['strength'] == 'strong']
            medium_corrs = [c for c in correlations if c['strength'] == 'medium']
            weak_corrs = [c for c in correlations if c['strength'] == 'weak']
            
            if strong_corrs:
                lines.extend([
                    "### 强关联",
                    "",
                ])
                for corr in strong_corrs:
                    lines.extend(self._format_correlation_section(corr))
            
            if medium_corrs:
                lines.extend([
                    "### 中等关联",
                    "",
                ])
                for corr in medium_corrs:
                    lines.extend(self._format_correlation_section(corr))
            
            if weak_corrs:
                lines.extend([
                    "### 弱关联",
                    "",
                ])
                for corr in weak_corrs[:3]:
                    lines.extend(self._format_correlation_section(corr, brief=True))
        
        root_causes_data = analysis_result.get("root_causes", [])
        if root_causes_data:
            lines.extend([
                "---",
                "",
                "## 🎯 根因分析",
                "",
            ])
            
            for rc in root_causes_data:
                lines.extend(self._format_root_cause_section(rc))
        
        fix_plan = analysis_result.get("fix_plan", {})
        if fix_plan:
            lines.extend([
                "---",
                "",
                "## 🔧 综合修复方案",
                "",
                f"**方案ID**: `{fix_plan.get('plan_id', '')}`",
                "",
                f"**描述**: {fix_plan.get('description', '')}",
                "",
                f"**预估工作量**: {fix_plan.get('estimated_effort', '')}",
                "",
            ])
            
            lines.extend([
                "### 修复步骤",
                "",
                "| 步骤 | 根因ID | 操作 | 优先级 | 复杂度 | 预计时间 |",
                "|------|--------|------|--------|--------|----------|",
            ])
            
            for step in fix_plan.get("fix_steps", []):
                step_num = step.get('step', '')
                rc_id = step.get('root_cause_id', '')
                action = step.get('action', '')[:50]
                priority = step.get('priority', '')
                complexity = step.get('complexity', '-')
                time = f"{step.get('estimated_minutes', '-')}分钟" if step.get('estimated_minutes') else '-'
                lines.append(f"| {step_num} | {rc_id} | {action} | {priority} | {complexity} | {time} |")
            
            lines.append("")
            
            lines.extend([
                "### 验证步骤",
                "",
            ])
            
            for step in fix_plan.get("verification_steps", []):
                lines.append(f"- {step}")
            
            lines.extend([
                "",
                "### ⚠️ 注意事项",
                "",
            ])
            
            if root_causes_data:
                has_config = any(rc.get('root_cause_category') in ('configuration', 'environment') for rc in root_causes_data)
                has_dependency = any(rc.get('root_cause_category') == 'dependency' for rc in root_causes_data)
                
                if has_config:
                    lines.append("- 配置/环境相关修改请在测试环境验证后再部署到生产环境")
                if has_dependency:
                    lines.append("- 依赖更新请检查版本兼容性，避免引入新问题")
                if len(root_causes_data) > 3:
                    lines.append("- 根因较多，建议按优先级顺序逐步修复并验证")
            
            lines.extend([
                "",
                "---",
                "",
                "*报告由关联失败分析器自动生成*",
            ])
        
        return "\n".join(lines)
    
    def _format_correlation_section(self, corr: Dict[str, Any], brief: bool = False) -> List[str]:
        """格式化关联分析部分
        
        生成关联分析的Markdown内容。
        """
        lines = []
        
        type_names = {
            "same_root_cause": "相同根因",
            "dependency_chain": "依赖链",
            "shared_resource": "共享资源",
            "temporal_correlation": "时间相关",
            "code_proximity": "代码邻近",
            "test_suite_correlation": "测试套件相关",
            "configuration_issue": "配置问题",
            "environment_issue": "环境问题",
            "data_dependency": "数据依赖",
            "api_contract": "API契约",
        }
        
        type_name = type_names.get(corr['type'], corr['type'])
        
        lines.append(f"#### {corr['correlation_id']}: {type_name}")
        lines.append("")
        
        if not brief:
            lines.extend([
                f"- **强度**: {corr['strength']}",
                f"- **置信度**: {corr['confidence']:.0%}",
                f"- **相关测试**: {', '.join(corr['related_failures'][:5])}",
            ])
            
            if corr.get("evidence"):
                lines.append("- **证据**:")
                for e in corr["evidence"][:5]:
                    lines.append(f"  - {e}")
            
            if corr.get("fix_recommendation"):
                lines.append(f"- **修复建议**: {corr['fix_recommendation']}")
            
            if corr.get("propagation_path"):
                lines.append(f"- **传播路径**: {' → '.join(corr['propagation_path'][:3])}")
        else:
            lines.append(f"- 相关测试: {', '.join(corr['related_failures'][:3])}")
            lines.append(f"- 置信度: {corr['confidence']:.0%}")
        
        lines.append("")
        return lines
    
    def _format_root_cause_section(self, rc: Dict[str, Any]) -> List[str]:
        """格式化根因分析部分
        
        生成根因分析的Markdown内容。
        """
        lines = []
        
        category_names = {
            "code_defect": "代码缺陷",
            "configuration": "配置问题",
            "environment": "环境问题",
            "data_issue": "数据问题",
            "dependency": "依赖问题",
            "api_issue": "API问题",
            "unknown": "未知",
        }
        
        category = category_names.get(rc.get('root_cause_category', 'unknown'), '未知')
        
        lines.append(f"### {rc['root_cause_id']}: {category}")
        lines.append("")
        
        lines.extend([
            f"- **描述**: {rc['description']}",
            f"- **置信度**: {rc['confidence']:.0%}",
            f"- **优先级**: {rc['fix_priority']}",
            f"- **复杂度**: {rc.get('fix_complexity', '未知')}",
            f"- **预计时间**: {rc.get('estimated_time_minutes', '-')}分钟",
        ])
        
        affected_tests = rc['affected_tests']
        if len(affected_tests) > 5:
            lines.append(f"- **影响测试**: {', '.join(affected_tests[:5])} 等 {len(affected_tests)} 个")
        else:
            lines.append(f"- **影响测试**: {', '.join(affected_tests)}")
        
        affected_files = rc.get('affected_files', [])
        if affected_files:
            if len(affected_files) > 3:
                lines.append(f"- **影响文件**: {', '.join(affected_files[:3])} 等 {len(affected_files)} 个")
            else:
                lines.append(f"- **影响文件**: {', '.join(affected_files)}")
        
        lines.append(f"- **建议修复**: {rc['suggested_fix']}")
        
        dependencies = rc.get('dependencies', [])
        if dependencies:
            lines.append(f"- **前置依赖**: {', '.join(dependencies[:3])}")
        
        verification = rc.get('verification_commands', [])
        if verification:
            lines.append(f"- **验证命令**: `{verification[0]}`")
        
        lines.append("")
        return lines
    
    def generate_report_html(self, analysis_result: Dict[str, Any]) -> str:
        """生成HTML格式的分析报告
        
        创建带有样式的HTML报告，适合在浏览器中查看。
        
        Args:
            analysis_result: 分析结果字典
            
        Returns:
            HTML格式的报告字符串
        """
        md_content = self.generate_report_markdown(analysis_result)
        
        html_lines = [
            "<!DOCTYPE html>",
            "<html lang='zh-CN'>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "    <title>关联失败分析报告</title>",
            "    <style>",
            "        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f5f5f5; }",
            "        h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }",
            "        h2 { color: #444; margin-top: 30px; }",
            "        h3 { color: #555; }",
            "        table { border-collapse: collapse; width: 100%; margin: 15px 0; background: white; }",
            "        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }",
            "        th { background-color: #4CAF50; color: white; }",
            "        tr:nth-child(even) { background-color: #f9f9f9; }",
            "        tr:hover { background-color: #f1f1f1; }",
            "        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }",
            "        blockquote { border-left: 4px solid #4CAF50; margin: 15px 0; padding: 10px 20px; background: #e8f5e9; }",
            "        .summary-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 20px 0; }",
            "        .priority-critical { color: #d32f2f; font-weight: bold; }",
            "        .priority-high { color: #f57c00; }",
            "        .priority-medium { color: #fbc02d; }",
            "        .priority-low { color: #388e3c; }",
            "    </style>",
            "</head>",
            "<body>",
        ]
        
        for line in md_content.split('\n'):
            if line.startswith('# '):
                html_lines.append(f"    <h1>{line[2:]}</h1>")
            elif line.startswith('## '):
                html_lines.append(f"    <h2>{line[3:]}</h2>")
            elif line.startswith('### '):
                html_lines.append(f"    <h3>{line[4:]}</h3>")
            elif line.startswith('#### '):
                html_lines.append(f"    <h4>{line[5:]}</h4>")
            elif line.startswith('| '):
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if all(c.replace('-', '').replace(':', '') == '' for c in cells):
                    continue
                html_lines.append(f"    <tr>{''.join(f'<td>{c}</td>' for c in cells)}</tr>")
            elif line.startswith('> '):
                html_lines.append(f"    <blockquote>{line[2:]}</blockquote>")
            elif line.startswith('- '):
                html_lines.append(f"    <li>{line[2:]}</li>")
            elif line.startswith('---'):
                html_lines.append("    <hr>")
            elif line.strip():
                html_lines.append(f"    <p>{line}</p>")
            else:
                html_lines.append("    <br>")
        
        html_lines.extend([
            "</body>",
            "</html>",
        ])
        
        return '\n'.join(html_lines)
    
    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """获取分析历史记录
        
        返回所有历史分析结果的副本。
        """
        return self._analysis_history.copy()
    
    def export_results(
        self,
        analysis_result: Dict[str, Any],
        output_dir: str,
        formats: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """导出分析结果到多种格式
        
        将分析结果导出为Markdown、JSON、HTML等格式。
        
        Args:
            analysis_result: 分析结果字典
            output_dir: 输出目录路径
            formats: 要导出的格式列表，默认为 ['markdown', 'json']
            
        Returns:
            生成的文件路径字典
        """
        if formats is None:
            formats = ['markdown', 'json']
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        exported_files = {}
        
        if 'markdown' in formats:
            md_path = output_dir / f"correlation_report_{timestamp}.md"
            md_content = self.generate_report_markdown(analysis_result)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            exported_files['markdown'] = str(md_path)
        
        if 'json' in formats:
            json_path = output_dir / f"correlation_report_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2, default=str)
            exported_files['json'] = str(json_path)
        
        if 'html' in formats:
            html_path = output_dir / f"correlation_report_{timestamp}.html"
            html_content = self.generate_report_html(analysis_result)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            exported_files['html'] = str(html_path)
        
        return exported_files


def main():
    """主函数
    
    解析命令行参数并执行关联失败分析。
    """
    parser = argparse.ArgumentParser(
        description="关联失败分析器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析pytest输出
  python correlated_failure_analyzer.py --pytest-output test_output.txt --analyze
  
  # 从JSON文件分析
  python correlated_failure_analyzer.py --failures failures.json --report correlation_report.md
  
  # 深度分析模式
  python correlated_failure_analyzer.py --pytest-output test_output.txt --deep-analysis
  
  # 导出多种格式报告
  python correlated_failure_analyzer.py --pytest-output test_output.txt --export-dir ./reports
        """
    )
    
    parser.add_argument(
        "--pytest-output",
        help="pytest输出文件路径"
    )
    
    parser.add_argument(
        "--failures",
        help="失败信息JSON文件路径"
    )
    
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="执行分析"
    )
    
    parser.add_argument(
        "--deep-analysis",
        action="store_true",
        help="执行深度分析"
    )
    
    parser.add_argument(
        "--report",
        help="Markdown报告输出路径"
    )
    
    parser.add_argument(
        "--json-report",
        help="JSON报告输出路径"
    )
    
    parser.add_argument(
        "--html-report",
        help="HTML报告输出路径"
    )
    
    parser.add_argument(
        "--export-dir",
        help="导出目录路径，将生成所有格式的报告"
    )
    
    args = parser.parse_args()
    
    if not args.pytest_output and not args.failures:
        parser.error("需要指定 --pytest-output 或 --failures")
    
    try:
        analyzer = CorrelatedFailureAnalyzer()
        
        if args.pytest_output:
            result = analyzer.analyze_from_file(args.pytest_output)
        else:
            result = analyzer.analyze_from_file(args.failures)
        
        if result.get("status") == "no_failures":
            print("没有检测到测试失败")
            return
        
        summary = result.get("summary", {})
        
        print("=" * 60)
        print("关联失败分析报告")
        print("=" * 60)
        print(f"\n📊 分析摘要:")
        print(f"  总失败数: {summary.get('total_failures', 0)}")
        print(f"  关联数: {summary.get('total_correlations', 0)}")
        print(f"    - 强关联: {summary.get('strong_correlations', 0)}")
        print(f"    - 中等关联: {summary.get('medium_correlations', 0)}")
        print(f"    - 弱关联: {summary.get('weak_correlations', 0)}")
        print(f"  识别的根因数: {summary.get('root_causes_identified', 0)}")
        print(f"  涉及文件数: {summary.get('total_affected_files', 0)}")
        print(f"  预计修复时间: {summary.get('estimated_total_time_minutes', 0)} 分钟")
        
        categories = summary.get('categories', [])
        if categories:
            category_names = {
                "code_defect": "代码缺陷",
                "configuration": "配置问题",
                "environment": "环境问题",
                "data_issue": "数据问题",
                "dependency": "依赖问题",
                "api_issue": "API问题",
            }
            cat_str = ", ".join(category_names.get(c, c) for c in categories)
            print(f"  问题类型: {cat_str}")
        
        if args.analyze or args.deep_analysis:
            print(f"\n🔗 关联分析详情:")
            correlations = result.get("correlations", [])
            
            strong_corrs = [c for c in correlations if c['strength'] == 'strong']
            if strong_corrs:
                print("  强关联:")
                for corr in strong_corrs[:5]:
                    print(f"    - {corr['correlation_id']}: {corr['type']}")
                    print(f"      相关测试: {', '.join(corr['related_failures'][:3])}")
                    if corr.get('fix_recommendation'):
                        print(f"      建议: {corr['fix_recommendation'][:50]}...")
            
            medium_corrs = [c for c in correlations if c['strength'] == 'medium']
            if medium_corrs:
                print("  中等关联:")
                for corr in medium_corrs[:3]:
                    print(f"    - {corr['correlation_id']}: {corr['type']} (置信度: {corr['confidence']:.0%})")
            
            print(f"\n🎯 根因分析:")
            for rc in result.get("root_causes", [])[:5]:
                print(f"  [{rc['root_cause_id']}] {rc['root_cause_category']}")
                print(f"    描述: {rc['description'][:60]}...")
                print(f"    优先级: {rc['fix_priority']} | 复杂度: {rc['fix_complexity']} | 时间: {rc['estimated_time_minutes']}分钟")
                print(f"    影响: {len(rc['affected_tests'])} 个测试, {len(rc['affected_files'])} 个文件")
            
            fix_plan = result.get("fix_plan", {})
            print(f"\n🔧 修复方案:")
            print(f"  方案ID: {fix_plan.get('plan_id', '')}")
            print(f"  工作量: {fix_plan.get('estimated_effort', '')}")
            print(f"  修复步骤数: {len(fix_plan.get('fix_steps', []))}")
        
        if args.report:
            report_content = analyzer.generate_report_markdown(result)
            Path(args.report).parent.mkdir(parents=True, exist_ok=True)
            with open(args.report, "w", encoding="utf-8") as f:
                f.write(report_content)
            print(f"\n✅ Markdown报告已生成: {args.report}")
        
        if args.json_report:
            Path(args.json_report).parent.mkdir(parents=True, exist_ok=True)
            with open(args.json_report, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            print(f"✅ JSON报告已生成: {args.json_report}")
        
        if args.html_report:
            html_content = analyzer.generate_report_html(result)
            Path(args.html_report).parent.mkdir(parents=True, exist_ok=True)
            with open(args.html_report, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"✅ HTML报告已生成: {args.html_report}")
        
        if args.export_dir:
            exported = analyzer.export_results(result, args.export_dir, formats=['markdown', 'json', 'html'])
            print(f"\n✅ 报告已导出到目录: {args.export_dir}")
            for fmt, path in exported.items():
                print(f"  - {fmt}: {path}")
        
        print("\n" + "=" * 60)
        
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        print(f"❌ 错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行错误: {e}")
        print(f"❌ 执行错误: {e}")
        import traceback as tb
        tb.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
