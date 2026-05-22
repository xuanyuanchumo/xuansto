#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
子技能优化器模块

实现子技能的智能优化功能，包括：
1. 子技能内容分析 - 分析文档结构、内容质量
2. 子技能效果评估 - 基于调用记录评估效果
3. 子技能自动更新 - 根据分析结果更新文档
4. 优化建议生成 - 生成改进建议

分析维度：
- 文档完整性（结构、示例、最佳实践）
- 内容质量（准确、清晰、有用）
- 使用频率（调用次数）
- 效果评分（成功率、用户满意度）

使用示例:
    python subskill_optimizer.py --subskills-dir ./subskills
    python subskill_optimizer.py --analyze ceshi
    python subskill_optimizer.py --optimize --dry-run
"""

import json
import logging
import re
import sys
import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import hashlib
import statistics


class SubskillCategory(Enum):
    """子技能类别枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    DESIGN = "design"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    INTEGRATION = "integration"
    DOCUMENTATION = "documentation"


class QualityLevel(Enum):
    """质量等级枚举"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


class OptimizationPriority(Enum):
    """优化优先级枚举"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


class UpdateType(Enum):
    """更新类型枚举"""
    CONTENT_ADDITION = "content_addition"
    CONTENT_IMPROVEMENT = "content_improvement"
    STRUCTURE_REORGANIZATION = "structure_reorganization"
    EXAMPLE_ADDITION = "example_addition"
    BEST_PRACTICE_ADDITION = "best_practice_addition"
    ERROR_CORRECTION = "error_correction"
    CLARIFICATION = "clarification"


@dataclass
class DocumentStructure:
    """文档结构数据类"""
    has_frontmatter: bool = False
    has_name: bool = False
    has_description: bool = False
    sections: List[str] = field(default_factory=list)
    has_examples: bool = False
    has_best_practices: bool = False
    has_code_blocks: bool = False
    has_tables: bool = False
    heading_count: int = 0
    code_block_count: int = 0
    table_count: int = 0
    list_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_frontmatter": self.has_frontmatter,
            "has_name": self.has_name,
            "has_description": self.has_description,
            "sections": self.sections,
            "has_examples": self.has_examples,
            "has_best_practices": self.has_best_practices,
            "has_code_blocks": self.has_code_blocks,
            "has_tables": self.has_tables,
            "heading_count": self.heading_count,
            "code_block_count": self.code_block_count,
            "table_count": self.table_count,
            "list_count": self.list_count
        }


@dataclass
class ContentQuality:
    """内容质量数据类"""
    clarity_score: float = 0.0
    completeness_score: float = 0.0
    accuracy_score: float = 0.0
    usefulness_score: float = 0.0
    readability_score: float = 0.0
    overall_score: float = 0.0
    quality_level: QualityLevel = QualityLevel.ACCEPTABLE
    issues: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clarity_score": round(self.clarity_score, 4),
            "completeness_score": round(self.completeness_score, 4),
            "accuracy_score": round(self.accuracy_score, 4),
            "usefulness_score": round(self.usefulness_score, 4),
            "readability_score": round(self.readability_score, 4),
            "overall_score": round(self.overall_score, 4),
            "quality_level": self.quality_level.value,
            "issues": self.issues,
            "strengths": self.strengths
        }


@dataclass
class UsageStatistics:
    """使用统计数据类"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    avg_duration: float = 0.0
    success_rate: float = 0.0
    last_called: Optional[str] = None
    call_frequency: float = 0.0
    peak_usage_period: Optional[str] = None
    unique_callers: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "avg_duration": round(self.avg_duration, 4),
            "success_rate": round(self.success_rate, 4),
            "last_called": self.last_called,
            "call_frequency": round(self.call_frequency, 4),
            "peak_usage_period": self.peak_usage_period,
            "unique_callers": self.unique_callers
        }


@dataclass
class EffectEvaluation:
    """效果评估数据类"""
    effectiveness_score: float = 0.0
    reliability_score: float = 0.0
    user_satisfaction: float = 0.0
    error_rate: float = 0.0
    avg_completion_time: float = 0.0
    improvement_suggestions: List[str] = field(default_factory=list)
    performance_trend: str = "stable"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "effectiveness_score": round(self.effectiveness_score, 4),
            "reliability_score": round(self.reliability_score, 4),
            "user_satisfaction": round(self.user_satisfaction, 4),
            "error_rate": round(self.error_rate, 4),
            "avg_completion_time": round(self.avg_completion_time, 4),
            "improvement_suggestions": self.improvement_suggestions,
            "performance_trend": self.performance_trend
        }


@dataclass
class SubskillAnalysis:
    """子技能分析结果数据类"""
    subskill_name: str
    subskill_path: str
    document_structure: DocumentStructure
    content_quality: ContentQuality
    usage_statistics: UsageStatistics
    effect_evaluation: EffectEvaluation
    overall_score: float = 0.0
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subskill_name": self.subskill_name,
            "subskill_path": self.subskill_path,
            "document_structure": self.document_structure.to_dict(),
            "content_quality": self.content_quality.to_dict(),
            "usage_statistics": self.usage_statistics.to_dict(),
            "effect_evaluation": self.effect_evaluation.to_dict(),
            "overall_score": round(self.overall_score, 4),
            "analyzed_at": self.analyzed_at,
            "recommendations": self.recommendations
        }


@dataclass
class OptimizationSuggestion:
    """优化建议数据类"""
    suggestion_id: str
    subskill_name: str
    priority: OptimizationPriority
    category: str
    title: str
    description: str
    rationale: str
    actions: List[str]
    impact_score: float
    effort_estimate: str
    current_state: str
    target_state: str
    update_type: UpdateType
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "subskill_name": self.subskill_name,
            "priority": self.priority.value,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "actions": self.actions,
            "impact_score": round(self.impact_score, 4),
            "effort_estimate": self.effort_estimate,
            "current_state": self.current_state,
            "target_state": self.target_state,
            "update_type": self.update_type.value,
            "created_at": self.created_at
        }


@dataclass
class UpdatePlan:
    """更新计划数据类"""
    plan_id: str
    subskill_name: str
    updates: List[Dict[str, Any]]
    backup_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    applied_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "subskill_name": self.subskill_name,
            "updates": self.updates,
            "backup_path": self.backup_path,
            "created_at": self.created_at,
            "status": self.status,
            "applied_at": self.applied_at
        }


@dataclass
class OptimizationReport:
    """优化报告数据类"""
    timestamp: str
    total_subskills: int
    analyzed_subskills: int
    average_score: float
    quality_distribution: Dict[str, int]
    top_issues: List[str]
    top_recommendations: List[OptimizationSuggestion]
    improvement_potential: float
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_subskills": self.total_subskills,
            "analyzed_subskills": self.analyzed_subskills,
            "average_score": round(self.average_score, 4),
            "quality_distribution": self.quality_distribution,
            "top_issues": self.top_issues,
            "top_recommendations": [r.to_dict() for r in self.top_recommendations],
            "improvement_potential": round(self.improvement_potential, 4),
            "summary": self.summary
        }


class IAnalyzer(ABC):
    """分析器接口"""

    @abstractmethod
    def analyze(self, content: str, context: Dict[str, Any]) -> Any:
        pass


class DocumentStructureAnalyzer(IAnalyzer):
    """文档结构分析器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def analyze(self, content: str, context: Dict[str, Any]) -> DocumentStructure:
        structure = DocumentStructure()

        structure.has_frontmatter = self._check_frontmatter(content)
        structure.has_name, structure.has_description = self._check_frontmatter_fields(content)
        structure.sections = self._extract_sections(content)
        structure.has_examples = self._check_examples(content)
        structure.has_best_practices = self._check_best_practices(content)
        structure.has_code_blocks = self._check_code_blocks(content)
        structure.has_tables = self._check_tables(content)
        structure.heading_count = self._count_headings(content)
        structure.code_block_count = self._count_code_blocks(content)
        structure.table_count = self._count_tables(content)
        structure.list_count = self._count_lists(content)

        return structure

    def _check_frontmatter(self, content: str) -> bool:
        return content.strip().startswith("---")

    def _check_frontmatter_fields(self, content: str) -> Tuple[bool, bool]:
        has_name = False
        has_description = False

        if content.strip().startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 2:
                frontmatter = parts[1]
                has_name = "name:" in frontmatter.lower()
                has_description = "description:" in frontmatter.lower()

        return has_name, has_description

    def _extract_sections(self, content: str) -> List[str]:
        sections = []
        heading_pattern = re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE)

        for match in heading_pattern.finditer(content):
            sections.append(match.group(1).strip())

        return sections

    def _check_examples(self, content: str) -> bool:
        example_keywords = ["示例", "example", "例子", "用法", "usage", "演示"]
        content_lower = content.lower()
        return any(kw in content_lower for kw in example_keywords)

    def _check_best_practices(self, content: str) -> bool:
        practice_keywords = ["最佳实践", "best practice", "建议", "recommendation", "注意事项", "note"]
        content_lower = content.lower()
        return any(kw in content_lower for kw in practice_keywords)

    def _check_code_blocks(self, content: str) -> bool:
        return "```" in content

    def _check_tables(self, content: str) -> bool:
        return "|" in content and "---" in content

    def _count_headings(self, content: str) -> int:
        heading_pattern = re.compile(r'^#{1,6}\s+', re.MULTILINE)
        return len(heading_pattern.findall(content))

    def _count_code_blocks(self, content: str) -> int:
        return content.count("```") // 2

    def _count_tables(self, content: str) -> int:
        table_pattern = re.compile(r'\|.+\|[\s\S]*?\|.+\|[\s\S]*?\|[-:]+\|')
        return len(table_pattern.findall(content))

    def _count_lists(self, content: str) -> int:
        list_pattern = re.compile(r'^[\*\-\+]\s+|^\d+\.\s+', re.MULTILINE)
        return len(list_pattern.findall(content))


class ContentQualityAnalyzer(IAnalyzer):
    """内容质量分析器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._quality_rules = self._initialize_quality_rules()

    def _initialize_quality_rules(self) -> Dict[str, Any]:
        return {
            "clarity": {
                "min_sentence_length": 5,
                "max_sentence_length": 100,
                "ideal_paragraph_length": 150
            },
            "completeness": {
                "required_sections": ["概述", "流程", "输出"],
                "min_word_count": 100
            },
            "accuracy": {
                "code_block_keywords": ["def ", "class ", "function ", "import ", "const "],
                "valid_patterns": [r"```[\w]*\n", r"\[.*\]\(.*\)"]
            }
        }

    def analyze(self, content: str, context: Dict[str, Any]) -> ContentQuality:
        quality = ContentQuality()

        quality.clarity_score = self._analyze_clarity(content)
        quality.completeness_score = self._analyze_completeness(content)
        quality.accuracy_score = self._analyze_accuracy(content)
        quality.usefulness_score = self._analyze_usefulness(content)
        quality.readability_score = self._analyze_readability(content)

        quality.overall_score = self._calculate_overall_score(quality)
        quality.quality_level = self._determine_quality_level(quality.overall_score)
        quality.issues = self._identify_issues(content, quality)
        quality.strengths = self._identify_strengths(content, quality)

        return quality

    def _analyze_clarity(self, content: str) -> float:
        score = 0.5

        sentences = re.split(r'[。！？.!?]', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if sentences:
            avg_length = sum(len(s) for s in sentences) / len(sentences)
            if 20 <= avg_length <= 80:
                score += 0.2
            elif avg_length < 20:
                score += 0.1
            else:
                score -= 0.1

        paragraphs = content.split("\n\n")
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        if paragraphs:
            avg_para_length = sum(len(p) for p in paragraphs) / len(paragraphs)
            if 50 <= avg_para_length <= 300:
                score += 0.2

        if re.search(r'[一二三四五六七八九十]', content):
            score += 0.1

        return min(max(score, 0.0), 1.0)

    def _analyze_completeness(self, content: str) -> float:
        score = 0.0
        required_sections = self._quality_rules["completeness"]["required_sections"]

        content_lower = content.lower()
        for section in required_sections:
            if section.lower() in content_lower:
                score += 0.25

        word_count = len(content)
        min_words = self._quality_rules["completeness"]["min_word_count"]
        if word_count >= min_words:
            score += 0.15
        elif word_count >= min_words * 0.5:
            score += 0.1

        if "```" in content:
            score += 0.1

        return min(score, 1.0)

    def _analyze_accuracy(self, content: str) -> float:
        score = 0.5

        code_keywords = self._quality_rules["accuracy"]["code_block_keywords"]
        code_block_count = content.count("```")

        if code_block_count > 0:
            score += 0.2

            code_blocks = re.findall(r'```[\w]*\n(.*?)```', content, re.DOTALL)
            valid_code_count = 0
            for block in code_blocks:
                if any(kw in block for kw in code_keywords):
                    valid_code_count += 1

            if code_blocks and valid_code_count / len(code_blocks) > 0.5:
                score += 0.2

        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        links = link_pattern.findall(content)
        if links:
            score += 0.1

        return min(score, 1.0)

    def _analyze_usefulness(self, content: str) -> float:
        score = 0.3

        usefulness_indicators = [
            ("示例", 0.15),
            ("最佳实践", 0.15),
            ("注意事项", 0.1),
            ("常见问题", 0.1),
            ("FAQ", 0.1),
            ("命令", 0.1),
            ("配置", 0.1)
        ]

        content_lower = content.lower()
        for indicator, weight in usefulness_indicators:
            if indicator.lower() in content_lower:
                score += weight

        return min(score, 1.0)

    def _analyze_readability(self, content: str) -> float:
        score = 0.5

        heading_count = len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE))
        if heading_count >= 3:
            score += 0.2
        elif heading_count >= 1:
            score += 0.1

        list_count = len(re.findall(r'^[\*\-\+]\s+|^\d+\.\s+', content, re.MULTILINE))
        if list_count >= 5:
            score += 0.15
        elif list_count >= 2:
            score += 0.1

        table_count = content.count("|") // 3
        if table_count >= 1:
            score += 0.15

        return min(score, 1.0)

    def _calculate_overall_score(self, quality: ContentQuality) -> float:
        weights = {
            "clarity": 0.25,
            "completeness": 0.25,
            "accuracy": 0.20,
            "usefulness": 0.20,
            "readability": 0.10
        }

        return (
            quality.clarity_score * weights["clarity"] +
            quality.completeness_score * weights["completeness"] +
            quality.accuracy_score * weights["accuracy"] +
            quality.usefulness_score * weights["usefulness"] +
            quality.readability_score * weights["readability"]
        )

    def _determine_quality_level(self, score: float) -> QualityLevel:
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.75:
            return QualityLevel.GOOD
        elif score >= 0.6:
            return QualityLevel.ACCEPTABLE
        elif score >= 0.4:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL

    def _identify_issues(self, content: str, quality: ContentQuality) -> List[str]:
        issues = []

        if quality.clarity_score < 0.5:
            issues.append("内容清晰度不足，建议简化句子结构")

        if quality.completeness_score < 0.5:
            issues.append("内容完整性不足，缺少必要章节")

        if quality.accuracy_score < 0.5:
            issues.append("代码示例质量需要提升")

        if quality.usefulness_score < 0.5:
            issues.append("实用性不足，建议添加更多示例和最佳实践")

        if quality.readability_score < 0.5:
            issues.append("可读性较差，建议优化文档结构")

        if "```" not in content:
            issues.append("缺少代码示例")

        if len(content) < 200:
            issues.append("内容过于简短")

        return issues

    def _identify_strengths(self, content: str, quality: ContentQuality) -> List[str]:
        strengths = []

        if quality.clarity_score >= 0.7:
            strengths.append("内容表达清晰")

        if quality.completeness_score >= 0.7:
            strengths.append("内容完整度高")

        if quality.accuracy_score >= 0.7:
            strengths.append("代码示例准确")

        if quality.usefulness_score >= 0.7:
            strengths.append("实用性强")

        if quality.readability_score >= 0.7:
            strengths.append("文档结构清晰")

        if content.count("```") >= 3:
            strengths.append("包含丰富的代码示例")

        return strengths


class EffectEvaluator:
    """效果评估器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def evaluate(self, usage_stats: UsageStatistics, context: Dict[str, Any]) -> EffectEvaluation:
        evaluation = EffectEvaluation()

        evaluation.effectiveness_score = self._calculate_effectiveness(usage_stats)
        evaluation.reliability_score = self._calculate_reliability(usage_stats)
        evaluation.user_satisfaction = self._estimate_satisfaction(usage_stats, context)
        evaluation.error_rate = self._calculate_error_rate(usage_stats)
        evaluation.avg_completion_time = usage_stats.avg_duration
        evaluation.improvement_suggestions = self._generate_suggestions(usage_stats, evaluation)
        evaluation.performance_trend = self._analyze_trend(usage_stats, context)

        return evaluation

    def _calculate_effectiveness(self, stats: UsageStatistics) -> float:
        if stats.total_calls == 0:
            return 0.5

        success_factor = stats.success_rate
        frequency_factor = min(stats.call_frequency / 10, 1.0)

        return (success_factor * 0.7 + frequency_factor * 0.3)

    def _calculate_reliability(self, stats: UsageStatistics) -> float:
        if stats.total_calls == 0:
            return 0.5

        if stats.total_calls < 5:
            return 0.6

        consistency_score = 1.0 - abs(stats.success_rate - 0.8) * 0.5

        return min(max(consistency_score, 0.0), 1.0)

    def _estimate_satisfaction(self, stats: UsageStatistics, context: Dict[str, Any]) -> float:
        base_satisfaction = 0.5

        if stats.success_rate > 0.9:
            base_satisfaction += 0.3
        elif stats.success_rate > 0.7:
            base_satisfaction += 0.2
        elif stats.success_rate > 0.5:
            base_satisfaction += 0.1
        else:
            base_satisfaction -= 0.2

        if stats.avg_duration > 0:
            if stats.avg_duration < 5:
                base_satisfaction += 0.1
            elif stats.avg_duration > 60:
                base_satisfaction -= 0.1

        return min(max(base_satisfaction, 0.0), 1.0)

    def _calculate_error_rate(self, stats: UsageStatistics) -> float:
        if stats.total_calls == 0:
            return 0.0

        return stats.failed_calls / stats.total_calls

    def _generate_suggestions(self, stats: UsageStatistics, evaluation: EffectEvaluation) -> List[str]:
        suggestions = []

        if evaluation.error_rate > 0.2:
            suggestions.append("错误率较高，建议检查子技能执行逻辑")

        if stats.success_rate < 0.7:
            suggestions.append("成功率偏低，建议优化执行流程")

        if stats.avg_duration > 30:
            suggestions.append("执行时间较长，建议优化性能")

        if stats.total_calls == 0:
            suggestions.append("尚未被调用，建议增加使用场景说明")

        if stats.call_frequency < 0.1:
            suggestions.append("使用频率较低，建议评估子技能价值")

        return suggestions

    def _analyze_trend(self, stats: UsageStatistics, context: Dict[str, Any]) -> str:
        if stats.total_calls < 5:
            return "insufficient_data"

        if stats.success_rate > 0.9:
            return "improving"
        elif stats.success_rate < 0.5:
            return "declining"
        else:
            return "stable"


class SuggestionGenerator:
    """优化建议生成器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._suggestion_templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[str, Dict[str, Any]]:
        return {
            "structure": {
                "missing_frontmatter": {
                    "title": "添加文档元数据",
                    "description": "文档缺少必要的 frontmatter 元数据",
                    "actions": ["添加 name 字段", "添加 description 字段"],
                    "impact": 0.8,
                    "effort": "低 (5分钟)"
                },
                "missing_sections": {
                    "title": "完善文档结构",
                    "description": "文档缺少必要的章节",
                    "actions": ["添加概述章节", "添加流程说明", "添加输出物说明"],
                    "impact": 0.7,
                    "effort": "中 (15分钟)"
                }
            },
            "content": {
                "no_examples": {
                    "title": "添加代码示例",
                    "description": "文档缺少代码示例",
                    "actions": ["添加使用示例", "添加代码片段", "添加输出示例"],
                    "impact": 0.85,
                    "effort": "中 (20分钟)"
                },
                "no_best_practices": {
                    "title": "添加最佳实践",
                    "description": "文档缺少最佳实践说明",
                    "actions": ["添加注意事项", "添加最佳实践建议", "添加常见问题解答"],
                    "impact": 0.75,
                    "effort": "中 (15分钟)"
                },
                "content_too_short": {
                    "title": "扩充文档内容",
                    "description": "文档内容过于简短",
                    "actions": ["添加详细说明", "添加使用场景", "添加相关资源"],
                    "impact": 0.7,
                    "effort": "高 (30分钟)"
                }
            },
            "quality": {
                "low_clarity": {
                    "title": "提升内容清晰度",
                    "description": "内容表达不够清晰",
                    "actions": ["简化句子结构", "使用更明确的术语", "添加解释说明"],
                    "impact": 0.65,
                    "effort": "中 (20分钟)"
                },
                "low_completeness": {
                    "title": "完善内容完整性",
                    "description": "内容完整性不足",
                    "actions": ["补充缺失信息", "添加边界情况说明", "完善流程描述"],
                    "impact": 0.7,
                    "effort": "中 (25分钟)"
                }
            },
            "usage": {
                "low_usage": {
                    "title": "提升子技能使用率",
                    "description": "子技能使用频率较低",
                    "actions": ["优化技能描述", "增加使用场景", "改进文档可见性"],
                    "impact": 0.6,
                    "effort": "中 (20分钟)"
                },
                "high_error_rate": {
                    "title": "降低错误率",
                    "description": "子技能执行错误率较高",
                    "actions": ["分析错误原因", "优化执行逻辑", "添加错误处理"],
                    "impact": 0.9,
                    "effort": "高 (1小时)"
                }
            }
        }

    def generate(
        self,
        analysis: SubskillAnalysis,
        context: Dict[str, Any]
    ) -> List[OptimizationSuggestion]:
        suggestions = []

        suggestions.extend(self._generate_structure_suggestions(analysis))
        suggestions.extend(self._generate_content_suggestions(analysis))
        suggestions.extend(self._generate_quality_suggestions(analysis))
        suggestions.extend(self._generate_usage_suggestions(analysis))

        suggestions.sort(key=lambda s: s.priority.value)

        return suggestions

    def _generate_structure_suggestions(self, analysis: SubskillAnalysis) -> List[OptimizationSuggestion]:
        suggestions = []
        structure = analysis.document_structure

        if not structure.has_frontmatter or not structure.has_name or not structure.has_description:
            template = self._suggestion_templates["structure"]["missing_frontmatter"]
            suggestions.append(self._create_suggestion(
                analysis.subskill_name,
                "structure",
                template,
                UpdateType.CONTENT_ADDITION,
                "缺少元数据",
                "包含完整元数据"
            ))

        if len(structure.sections) < 3:
            template = self._suggestion_templates["structure"]["missing_sections"]
            suggestions.append(self._create_suggestion(
                analysis.subskill_name,
                "structure",
                template,
                UpdateType.STRUCTURE_REORGANIZATION,
                f"仅有 {len(structure.sections)} 个章节",
                "包含完整章节结构"
            ))

        return suggestions

    def _generate_content_suggestions(self, analysis: SubskillAnalysis) -> List[OptimizationSuggestion]:
        suggestions = []
        structure = analysis.document_structure

        if not structure.has_examples or structure.code_block_count < 2:
            template = self._suggestion_templates["content"]["no_examples"]
            suggestions.append(self._create_suggestion(
                analysis.subskill_name,
                "content",
                template,
                UpdateType.EXAMPLE_ADDITION,
                f"仅有 {structure.code_block_count} 个代码块",
                "包含丰富的代码示例"
            ))

        if not structure.has_best_practices:
            template = self._suggestion_templates["content"]["no_best_practices"]
            suggestions.append(self._create_suggestion(
                analysis.subskill_name,
                "content",
                template,
                UpdateType.BEST_PRACTICE_ADDITION,
                "缺少最佳实践",
                "包含最佳实践说明"
            ))

        return suggestions

    def _generate_quality_suggestions(self, analysis: SubskillAnalysis) -> List[OptimizationSuggestion]:
        suggestions = []
        quality = analysis.content_quality

        if quality.clarity_score < 0.6:
            template = self._suggestion_templates["quality"]["low_clarity"]
            suggestions.append(self._create_suggestion(
                analysis.subskill_name,
                "quality",
                template,
                UpdateType.CLARIFICATION,
                f"清晰度评分: {quality.clarity_score:.2f}",
                "清晰度评分 > 0.7"
            ))

        if quality.completeness_score < 0.6:
            template = self._suggestion_templates["quality"]["low_completeness"]
            suggestions.append(self._create_suggestion(
                analysis.subskill_name,
                "quality",
                template,
                UpdateType.CONTENT_IMPROVEMENT,
                f"完整性评分: {quality.completeness_score:.2f}",
                "完整性评分 > 0.7"
            ))

        return suggestions

    def _generate_usage_suggestions(self, analysis: SubskillAnalysis) -> List[OptimizationSuggestion]:
        suggestions = []
        usage = analysis.usage_statistics
        effect = analysis.effect_evaluation

        if usage.total_calls == 0 or usage.call_frequency < 0.5:
            template = self._suggestion_templates["usage"]["low_usage"]
            suggestions.append(self._create_suggestion(
                analysis.subskill_name,
                "usage",
                template,
                UpdateType.CONTENT_IMPROVEMENT,
                f"调用次数: {usage.total_calls}",
                "提升使用频率"
            ))

        if effect.error_rate > 0.1:
            template = self._suggestion_templates["usage"]["high_error_rate"]
            suggestions.append(self._create_suggestion(
                analysis.subskill_name,
                "usage",
                template,
                UpdateType.ERROR_CORRECTION,
                f"错误率: {effect.error_rate:.2%}",
                "错误率 < 5%"
            ))

        return suggestions

    def _create_suggestion(
        self,
        subskill_name: str,
        category: str,
        template: Dict[str, Any],
        update_type: UpdateType,
        current_state: str,
        target_state: str
    ) -> OptimizationSuggestion:
        suggestion_id = f"OPT-{subskill_name}-{category.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        priority = self._determine_priority(template["impact"])

        return OptimizationSuggestion(
            suggestion_id=suggestion_id,
            subskill_name=subskill_name,
            priority=priority,
            category=category,
            title=template["title"],
            description=template["description"],
            rationale=f"影响分数: {template['impact']:.2f}",
            actions=template["actions"],
            impact_score=template["impact"],
            effort_estimate=template["effort"],
            current_state=current_state,
            target_state=target_state,
            update_type=update_type
        )

    def _determine_priority(self, impact: float) -> OptimizationPriority:
        if impact >= 0.85:
            return OptimizationPriority.CRITICAL
        elif impact >= 0.75:
            return OptimizationPriority.HIGH
        elif impact >= 0.6:
            return OptimizationPriority.MEDIUM
        elif impact >= 0.4:
            return OptimizationPriority.LOW
        else:
            return OptimizationPriority.INFO


class SubskillUpdater:
    """子技能更新器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def create_update_plan(
        self,
        subskill_path: Path,
        suggestions: List[OptimizationSuggestion],
        dry_run: bool = True
    ) -> UpdatePlan:
        plan_id = f"PLAN-{subskill_path.stem}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        updates = []
        for suggestion in suggestions[:5]:
            updates.append({
                "suggestion_id": suggestion.suggestion_id,
                "title": suggestion.title,
                "actions": suggestion.actions,
                "update_type": suggestion.update_type.value
            })

        plan = UpdatePlan(
            plan_id=plan_id,
            subskill_name=subskill_path.stem,
            updates=updates
        )

        if not dry_run:
            plan.backup_path = self._create_backup(subskill_path)

        return plan

    def apply_update(
        self,
        subskill_path: Path,
        plan: UpdatePlan,
        dry_run: bool = True
    ) -> bool:
        if dry_run:
            self.logger.info(f"[DRY RUN] 将应用更新计划: {plan.plan_id}")
            return True

        try:
            content = self._read_subskill(subskill_path)
            updated_content = self._apply_updates(content, plan.updates)
            self._write_subskill(subskill_path, updated_content)

            plan.status = "applied"
            plan.applied_at = datetime.now().isoformat()

            self.logger.info(f"成功应用更新计划: {plan.plan_id}")
            return True
        except Exception as e:
            self.logger.error(f"应用更新失败: {e}")
            plan.status = "failed"
            return False

    def _create_backup(self, subskill_path: Path) -> str:
        backup_dir = subskill_path.parent / ".backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = backup_dir / f"{subskill_path.stem}_{timestamp}.md"

        content = self._read_subskill(subskill_path)
        backup_path.write_text(content, encoding="utf-8")

        return str(backup_path)

    def _read_subskill(self, subskill_path: Path) -> str:
        return subskill_path.read_text(encoding="utf-8")

    def _write_subskill(self, subskill_path: Path, content: str) -> None:
        subskill_path.write_text(content, encoding="utf-8")

    def _apply_updates(self, content: str, updates: List[Dict[str, Any]]) -> str:
        for update in updates:
            update_type = update.get("update_type", "")

            if update_type == UpdateType.EXAMPLE_ADDITION.value:
                content = self._add_examples_section(content)
            elif update_type == UpdateType.BEST_PRACTICE_ADDITION.value:
                content = self._add_best_practices_section(content)
            elif update_type == UpdateType.CONTENT_ADDITION.value:
                content = self._ensure_frontmatter(content)

        return content

    def _add_examples_section(self, content: str) -> str:
        if "示例" in content or "Example" in content.lower():
            return content

        example_section = """

## 示例

### 基本用法

```python
# 示例代码待补充
```

### 进阶用法

```python
# 进阶示例待补充
```
"""
        return content + example_section

    def _add_best_practices_section(self, content: str) -> str:
        if "最佳实践" in content or "Best Practice" in content.lower():
            return content

        bp_section = """

## 最佳实践

### 推荐做法

1. 遵循项目代码规范
2. 编写清晰的注释
3. 进行充分的测试

### 注意事项

- 确保代码质量
- 注意性能影响
- 保持文档更新
"""
        return content + bp_section

    def _ensure_frontmatter(self, content: str) -> str:
        if content.strip().startswith("---"):
            return content

        name = "未命名子技能"
        description = "待补充描述"

        frontmatter = f"""---
name: {name}
description: {description}
---

"""
        return frontmatter + content


class SubskillOptimizer:
    """子技能优化器主类"""

    def __init__(
        self,
        subskills_dir: Path,
        logger: Optional[logging.Logger] = None
    ):
        self.subskills_dir = Path(subskills_dir)
        self.logger = logger or logging.getLogger(__name__)

        self.structure_analyzer = DocumentStructureAnalyzer(logger)
        self.quality_analyzer = ContentQualityAnalyzer(logger)
        self.effect_evaluator = EffectEvaluator(logger)
        self.suggestion_generator = SuggestionGenerator(logger)
        self.updater = SubskillUpdater(logger)

        self._analyses: Dict[str, SubskillAnalysis] = {}
        self._suggestions: Dict[str, List[OptimizationSuggestion]] = {}

    def discover_subskills(self) -> List[Path]:
        if not self.subskills_dir.exists():
            self.logger.warning(f"子技能目录不存在: {self.subskills_dir}")
            return []

        subskill_files = list(self.subskills_dir.glob("*.md"))
        self.logger.info(f"发现 {len(subskill_files)} 个子技能文件")

        return subskill_files

    def analyze_subskill(
        self,
        subskill_path: Path,
        call_records: Optional[List[Dict[str, Any]]] = None
    ) -> SubskillAnalysis:
        self.logger.info(f"分析子技能: {subskill_path.name}")

        content = subskill_path.read_text(encoding="utf-8")

        structure = self.structure_analyzer.analyze(content, {})
        quality = self.quality_analyzer.analyze(content, {})

        usage_stats = self._calculate_usage_stats(subskill_path.stem, call_records)
        effect_eval = self.effect_evaluator.evaluate(usage_stats, {})

        overall_score = self._calculate_overall_score(structure, quality, usage_stats, effect_eval)

        recommendations = self._generate_recommendations(structure, quality, usage_stats, effect_eval)

        analysis = SubskillAnalysis(
            subskill_name=subskill_path.stem,
            subskill_path=str(subskill_path),
            document_structure=structure,
            content_quality=quality,
            usage_statistics=usage_stats,
            effect_evaluation=effect_eval,
            overall_score=overall_score,
            recommendations=recommendations
        )

        self._analyses[subskill_path.stem] = analysis

        return analysis

    def _calculate_usage_stats(
        self,
        subskill_name: str,
        call_records: Optional[List[Dict[str, Any]]] = None
    ) -> UsageStatistics:
        stats = UsageStatistics()

        if not call_records:
            return stats

        filtered_records = [
            r for r in call_records
            if r.get("skill_name") == subskill_name
        ]

        if not filtered_records:
            return stats

        stats.total_calls = len(filtered_records)
        stats.successful_calls = sum(1 for r in filtered_records if r.get("status") == "completed")
        stats.failed_calls = sum(1 for r in filtered_records if r.get("status") == "failed")

        if stats.total_calls > 0:
            stats.success_rate = stats.successful_calls / stats.total_calls

        durations = [
            r.get("duration_seconds", 0)
            for r in filtered_records
            if r.get("duration_seconds")
        ]
        if durations:
            stats.avg_duration = statistics.mean(durations)

        timestamps = [
            r.get("start_time") or r.get("created_at")
            for r in filtered_records
            if r.get("start_time") or r.get("created_at")
        ]
        if timestamps:
            stats.last_called = max(timestamps)

        callers = set(r.get("caller") for r in filtered_records if r.get("caller"))
        stats.unique_callers = len(callers)

        return stats

    def _calculate_overall_score(
        self,
        structure: DocumentStructure,
        quality: ContentQuality,
        usage: UsageStatistics,
        effect: EffectEvaluation
    ) -> float:
        structure_score = self._score_structure(structure)
        quality_score = quality.overall_score
        usage_score = self._score_usage(usage)
        effect_score = effect.effectiveness_score

        weights = {
            "structure": 0.15,
            "quality": 0.35,
            "usage": 0.25,
            "effect": 0.25
        }

        return (
            structure_score * weights["structure"] +
            quality_score * weights["quality"] +
            usage_score * weights["usage"] +
            effect_score * weights["effect"]
        )

    def _score_structure(self, structure: DocumentStructure) -> float:
        score = 0.0

        if structure.has_frontmatter:
            score += 0.2
        if structure.has_name:
            score += 0.1
        if structure.has_description:
            score += 0.1
        if structure.has_examples:
            score += 0.15
        if structure.has_best_practices:
            score += 0.15
        if structure.has_code_blocks:
            score += 0.15
        if structure.heading_count >= 3:
            score += 0.15

        return min(score, 1.0)

    def _score_usage(self, usage: UsageStatistics) -> float:
        if usage.total_calls == 0:
            return 0.3

        score = 0.5

        if usage.success_rate > 0.9:
            score += 0.3
        elif usage.success_rate > 0.7:
            score += 0.2
        elif usage.success_rate > 0.5:
            score += 0.1

        if usage.call_frequency > 1:
            score += 0.2

        return min(score, 1.0)

    def _generate_recommendations(
        self,
        structure: DocumentStructure,
        quality: ContentQuality,
        usage: UsageStatistics,
        effect: EffectEvaluation
    ) -> List[str]:
        recommendations = []

        if not structure.has_examples:
            recommendations.append("建议添加代码示例以提高实用性")

        if not structure.has_best_practices:
            recommendations.append("建议添加最佳实践章节")

        if quality.overall_score < 0.6:
            recommendations.append("建议全面提升文档质量")

        if usage.total_calls == 0:
            recommendations.append("子技能尚未被调用，建议检查使用场景")

        if effect.error_rate > 0.1:
            recommendations.append("错误率较高，建议优化执行逻辑")

        return recommendations

    def analyze_all(
        self,
        call_records: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, SubskillAnalysis]:
        subskill_files = self.discover_subskills()

        for subskill_path in subskill_files:
            self.analyze_subskill(subskill_path, call_records)

        return self._analyses

    def generate_suggestions(
        self,
        subskill_name: Optional[str] = None
    ) -> Dict[str, List[OptimizationSuggestion]]:
        if subskill_name:
            if subskill_name not in self._analyses:
                self.logger.warning(f"未找到子技能分析结果: {subskill_name}")
                return {}

            analysis = self._analyses[subskill_name]
            suggestions = self.suggestion_generator.generate(analysis, {})
            self._suggestions[subskill_name] = suggestions
            return {subskill_name: suggestions}

        for name, analysis in self._analyses.items():
            suggestions = self.suggestion_generator.generate(analysis, {})
            self._suggestions[name] = suggestions

        return self._suggestions

    def create_update_plan(
        self,
        subskill_name: str,
        dry_run: bool = True
    ) -> Optional[UpdatePlan]:
        if subskill_name not in self._suggestions:
            self.logger.warning(f"未找到子技能优化建议: {subskill_name}")
            return None

        subskill_path = self.subskills_dir / f"{subskill_name}.md"
        if not subskill_path.exists():
            self.logger.warning(f"子技能文件不存在: {subskill_path}")
            return None

        suggestions = self._suggestions[subskill_name]
        return self.updater.create_update_plan(subskill_path, suggestions, dry_run)

    def apply_update(
        self,
        plan: UpdatePlan,
        dry_run: bool = True
    ) -> bool:
        subskill_path = Path(plan.subskill_name)
        if not subskill_path.is_absolute():
            subskill_path = self.subskills_dir / f"{plan.subskill_name}.md"

        return self.updater.apply_update(subskill_path, plan, dry_run)

    def generate_report(
        self,
        include_suggestions: bool = True
    ) -> OptimizationReport:
        total_subskills = len(self.discover_subskills())
        analyzed_subskills = len(self._analyses)

        scores = [a.overall_score for a in self._analyses.values()]
        average_score = statistics.mean(scores) if scores else 0.0

        quality_distribution: Dict[str, int] = {}
        for analysis in self._analyses.values():
            level = analysis.content_quality.quality_level.value
            quality_distribution[level] = quality_distribution.get(level, 0) + 1

        all_issues: List[str] = []
        for analysis in self._analyses.values():
            all_issues.extend(analysis.content_quality.issues)

        issue_counts: Dict[str, int] = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

        top_issues = sorted(issue_counts.keys(), key=lambda x: issue_counts[x], reverse=True)[:5]

        top_recommendations: List[OptimizationSuggestion] = []
        if include_suggestions:
            all_suggestions = []
            for suggestions in self._suggestions.values():
                all_suggestions.extend(suggestions)

            top_recommendations = sorted(
                all_suggestions,
                key=lambda s: (s.priority.value, -s.impact_score)
            )[:10]

        improvement_potential = self._calculate_improvement_potential()

        summary = {
            "total_analyzed": analyzed_subskills,
            "average_quality_score": round(average_score, 4),
            "most_common_issues": top_issues[:3],
            "suggestions_generated": sum(len(s) for s in self._suggestions.values())
        }

        return OptimizationReport(
            timestamp=datetime.now().isoformat(),
            total_subskills=total_subskills,
            analyzed_subskills=analyzed_subskills,
            average_score=average_score,
            quality_distribution=quality_distribution,
            top_issues=top_issues,
            top_recommendations=top_recommendations,
            improvement_potential=improvement_potential,
            summary=summary
        )

    def _calculate_improvement_potential(self) -> float:
        if not self._analyses:
            return 0.0

        potential = 0.0
        for analysis in self._analyses.values():
            gap = 1.0 - analysis.overall_score
            potential += gap

        return potential / len(self._analyses)

    def save_report(self, report: OptimizationReport, output_path: Path) -> bool:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

            self.logger.info(f"报告已保存到: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")
            return False

    def save_analysis(self, subskill_name: str, output_path: Path) -> bool:
        if subskill_name not in self._analyses:
            self.logger.warning(f"未找到子技能分析结果: {subskill_name}")
            return False

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            analysis = self._analyses[subskill_name]
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis.to_dict(), f, indent=2, ensure_ascii=False)

            self.logger.info(f"分析结果已保存到: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存分析结果失败: {e}")
            return False


def setup_logger(verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("SubskillOptimizer")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def main():
    parser = argparse.ArgumentParser(
        description="子技能优化器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python subskill_optimizer.py --subskills-dir ./subskills
  python subskill_optimizer.py --analyze ceshi
  python subskill_optimizer.py --optimize --dry-run
  python subskill_optimizer.py --report --output report.json
        """
    )

    parser.add_argument(
        "--subskills-dir",
        type=str,
        default="./subskills",
        help="子技能目录路径 (默认: ./subskills)"
    )

    parser.add_argument(
        "--analyze",
        type=str,
        help="分析指定的子技能"
    )

    parser.add_argument(
        "--analyze-all",
        action="store_true",
        help="分析所有子技能"
    )

    parser.add_argument(
        "--optimize",
        action="store_true",
        help="生成优化建议"
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="应用优化更新"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟运行，不实际修改文件"
    )

    parser.add_argument(
        "--report",
        action="store_true",
        help="生成优化报告"
    )

    parser.add_argument(
        "--output",
        type=str,
        help="输出文件路径"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )

    args = parser.parse_args()

    logger = setup_logger(args.verbose)

    print("=" * 80)
    print("子技能优化器")
    print("=" * 80)

    optimizer = SubskillOptimizer(
        subskills_dir=Path(args.subskills_dir),
        logger=logger
    )

    if args.analyze:
        subskill_path = Path(args.subskills_dir) / f"{args.analyze}.md"
        if subskill_path.exists():
            analysis = optimizer.analyze_subskill(subskill_path)

            print(f"\n子技能分析结果: {args.analyze}")
            print(f"  整体评分: {analysis.overall_score:.2f}")
            print(f"  质量等级: {analysis.content_quality.quality_level.value}")
            print(f"  结构评分: {optimizer._score_structure(analysis.document_structure):.2f}")
            print(f"  内容质量: {analysis.content_quality.overall_score:.2f}")
            print(f"  使用统计: 调用 {analysis.usage_statistics.total_calls} 次")
            print(f"  效果评分: {analysis.effect_evaluation.effectiveness_score:.2f}")

            if analysis.recommendations:
                print(f"\n  建议:")
                for i, rec in enumerate(analysis.recommendations, 1):
                    print(f"    {i}. {rec}")

            if args.output:
                optimizer.save_analysis(args.analyze, Path(args.output))
        else:
            print(f"子技能文件不存在: {subskill_path}")
            return 1

    elif args.analyze_all:
        analyses = optimizer.analyze_all()

        print(f"\n分析了 {len(analyses)} 个子技能")

        sorted_analyses = sorted(
            analyses.items(),
            key=lambda x: x[1].overall_score
        )

        print("\n子技能评分排名:")
        for name, analysis in sorted_analyses:
            print(f"  {name}: {analysis.overall_score:.2f} ({analysis.content_quality.quality_level.value})")

    if args.optimize:
        suggestions = optimizer.generate_suggestions(args.analyze)

        print(f"\n生成了 {sum(len(s) for s in suggestions.values())} 条优化建议")

        for name, suggs in suggestions.items():
            print(f"\n{name}:")
            for sugg in suggs[:5]:
                priority_icon = {
                    OptimizationPriority.CRITICAL: "🔴",
                    OptimizationPriority.HIGH: "🟠",
                    OptimizationPriority.MEDIUM: "🟡",
                    OptimizationPriority.LOW: "🟢",
                    OptimizationPriority.INFO: "🔵"
                }.get(sugg.priority, "⚪")

                print(f"  {priority_icon} [{sugg.category}] {sugg.title}")
                print(f"     影响: {sugg.impact_score:.2f}, 工作量: {sugg.effort_estimate}")

    if args.apply and args.analyze:
        plan = optimizer.create_update_plan(args.analyze, dry_run=args.dry_run)

        if plan:
            print(f"\n更新计划: {plan.plan_id}")
            print(f"  子技能: {plan.subskill_name}")
            print(f"  更新数量: {len(plan.updates)}")
            print(f"  模拟运行: {args.dry_run}")

            for update in plan.updates:
                print(f"    - {update['title']}")

            success = optimizer.apply_update(plan, dry_run=args.dry_run)
            print(f"\n更新结果: {'成功' if success else '失败'}")

    if args.report:
        report = optimizer.generate_report()

        print(f"\n优化报告")
        print(f"  时间: {report.timestamp}")
        print(f"  总子技能数: {report.total_subskills}")
        print(f"  已分析数: {report.analyzed_subskills}")
        print(f"  平均评分: {report.average_score:.2f}")
        print(f"  改进潜力: {report.improvement_potential:.2%}")

        print(f"\n质量分布:")
        for level, count in report.quality_distribution.items():
            print(f"  {level}: {count}")

        if report.top_issues:
            print(f"\n主要问题:")
            for issue in report.top_issues:
                print(f"  - {issue}")

        if args.output:
            optimizer.save_report(report, Path(args.output))

    return 0


if __name__ == "__main__":
    sys.exit(main())
