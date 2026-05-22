#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识应用引擎 - Knowledge Application Engine

实现知识检索匹配、应用建议生成、效果跟踪和反馈收集。

核心功能:
- 知识检索和匹配
- 知识应用建议生成
- 知识应用效果跟踪
- 知识反馈收集
- 应用历史管理
"""

import json
import logging
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import hashlib

from .knowledge_updater import (
    KnowledgeUpdater,
    KnowledgeCategory,
    KnowledgeQuality,
    KnowledgeEntry
)


class ApplicationStatus(Enum):
    """应用状态枚举"""
    PENDING = "pending"
    APPLIED = "applied"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class FeedbackType(Enum):
    """反馈类型枚举"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    SUGGESTION = "suggestion"


@dataclass
class ApplicationContext:
    """应用上下文数据类"""
    context_id: str
    project_type: str
    technology_stack: List[str]
    current_state: Dict[str, Any]
    objectives: List[str]
    constraints: List[str]
    environment: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "project_type": self.project_type,
            "technology_stack": self.technology_stack,
            "current_state": self.current_state,
            "objectives": self.objectives,
            "constraints": self.constraints,
            "environment": self.environment,
            "metadata": self.metadata
        }


@dataclass
class ApplicationSuggestion:
    """应用建议数据类"""
    suggestion_id: str
    knowledge_id: str
    relevance_score: float
    applicability_score: float
    priority: int
    title: str
    description: str
    implementation_steps: List[Dict[str, Any]]
    expected_benefits: List[str]
    potential_risks: List[str]
    prerequisites: List[str]
    estimated_effort: str
    context_match: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "knowledge_id": self.knowledge_id,
            "relevance_score": self.relevance_score,
            "applicability_score": self.applicability_score,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "implementation_steps": self.implementation_steps,
            "expected_benefits": self.expected_benefits,
            "potential_risks": self.potential_risks,
            "prerequisites": self.prerequisites,
            "estimated_effort": self.estimated_effort,
            "context_match": self.context_match,
            "metadata": self.metadata
        }


@dataclass
class ApplicationResult:
    """应用结果数据类"""
    result_id: str
    suggestion_id: str
    knowledge_id: str
    status: ApplicationStatus
    applied_at: datetime
    completed_at: Optional[datetime]
    effectiveness_score: float
    metrics_before: Dict[str, Any]
    metrics_after: Dict[str, Any]
    improvements: Dict[str, float]
    issues: List[str]
    lessons_learned: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "suggestion_id": self.suggestion_id,
            "knowledge_id": self.knowledge_id,
            "status": self.status.value,
            "applied_at": self.applied_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "effectiveness_score": self.effectiveness_score,
            "metrics_before": self.metrics_before,
            "metrics_after": self.metrics_after,
            "improvements": self.improvements,
            "issues": self.issues,
            "lessons_learned": self.lessons_learned,
            "metadata": self.metadata
        }


@dataclass
class Feedback:
    """反馈数据类"""
    feedback_id: str
    knowledge_id: str
    result_id: Optional[str]
    feedback_type: FeedbackType
    rating: int
    comment: str
    suggested_improvements: List[str]
    created_at: datetime
    user_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "knowledge_id": self.knowledge_id,
            "result_id": self.result_id,
            "feedback_type": self.feedback_type.value,
            "rating": self.rating,
            "comment": self.comment,
            "suggested_improvements": self.suggested_improvements,
            "created_at": self.created_at.isoformat(),
            "user_context": self.user_context
        }


class KnowledgeApplicationEngine:
    """知识应用引擎"""
    
    def __init__(
        self,
        knowledge_updater: Optional[KnowledgeUpdater] = None,
        storage_path: Optional[str] = None
    ):
        self._knowledge_updater = knowledge_updater or KnowledgeUpdater()
        self._storage_path = Path(storage_path) if storage_path else None
        self._logger = logging.getLogger('KnowledgeApplicationEngine')
        self._lock = threading.Lock()
        
        self._suggestions: Dict[str, ApplicationSuggestion] = {}
        self._results: Dict[str, ApplicationResult] = {}
        self._feedbacks: Dict[str, Feedback] = {}
        self._application_history: Dict[str, List[str]] = defaultdict(list)
        
        self._relevance_weights = {
            'category_match': 0.25,
            'tag_match': 0.20,
            'context_similarity': 0.25,
            'quality_score': 0.15,
            'success_rate': 0.15
        }
        
        if self._storage_path:
            self._load_application_data()
    
    def retrieve_and_match(
        self,
        context: ApplicationContext,
        categories: Optional[List[KnowledgeCategory]] = None,
        limit: int = 10
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """检索和匹配知识
        
        Args:
            context: 应用上下文
            categories: 类别过滤
            limit: 结果数量限制
        
        Returns:
            (知识条目, 匹配分数) 列表
        """
        all_entries = []
        
        if categories:
            for category in categories:
                entries = self._knowledge_updater.get_knowledge_by_category(category)
                all_entries.extend(entries)
        else:
            for category in KnowledgeCategory:
                entries = self._knowledge_updater.get_knowledge_by_category(category)
                all_entries.extend(entries)
        
        scored_entries = []
        for entry in all_entries:
            score = self._calculate_relevance_score(entry, context)
            if score > 0.3:
                scored_entries.append((entry, score))
        
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        
        return scored_entries[:limit]
    
    def generate_suggestions(
        self,
        context: ApplicationContext,
        max_suggestions: int = 5
    ) -> List[ApplicationSuggestion]:
        """生成应用建议
        
        Args:
            context: 应用上下文
            max_suggestions: 最大建议数量
        
        Returns:
            应用建议列表
        """
        matched_entries = self.retrieve_and_match(context, limit=max_suggestions * 2)
        
        suggestions = []
        priority = 1
        
        for entry, relevance_score in matched_entries:
            if len(suggestions) >= max_suggestions:
                break
            
            applicability_score = self._calculate_applicability_score(entry, context)
            
            if applicability_score < 0.5:
                continue
            
            suggestion_id = f"SUG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(entry.entry_id.encode()).hexdigest()[:8]}"
            
            implementation_steps = self._generate_implementation_steps(entry, context)
            expected_benefits = self._extract_benefits(entry)
            potential_risks = self._identify_risks(entry, context)
            prerequisites = self._extract_prerequisites(entry)
            
            suggestion = ApplicationSuggestion(
                suggestion_id=suggestion_id,
                knowledge_id=entry.entry_id,
                relevance_score=relevance_score,
                applicability_score=applicability_score,
                priority=priority,
                title=f"应用: {entry.title}",
                description=self._generate_suggestion_description(entry, context),
                implementation_steps=implementation_steps,
                expected_benefits=expected_benefits,
                potential_risks=potential_risks,
                prerequisites=prerequisites,
                estimated_effort=self._estimate_effort(entry),
                context_match={
                    "project_type": context.project_type,
                    "objectives": context.objectives
                }
            )
            
            suggestions.append(suggestion)
            self._suggestions[suggestion_id] = suggestion
            
            priority += 1
        
        if self._storage_path:
            self._save_application_data()
        
        self._logger.info(f"生成了 {len(suggestions)} 个应用建议")
        return suggestions
    
    def track_application_effect(
        self,
        suggestion_id: str,
        metrics_before: Dict[str, Any],
        metrics_after: Dict[str, Any]
    ) -> ApplicationResult:
        """跟踪应用效果
        
        Args:
            suggestion_id: 建议ID
            metrics_before: 应用前指标
            metrics_after: 应用后指标
        
        Returns:
            应用结果
        """
        suggestion = self._suggestions.get(suggestion_id)
        if not suggestion:
            raise ValueError(f"建议不存在: {suggestion_id}")
        
        result_id = f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(suggestion_id.encode()).hexdigest()[:8]}"
        
        improvements = self._calculate_improvements(metrics_before, metrics_after)
        effectiveness_score = self._calculate_effectiveness_score(improvements)
        
        status = ApplicationStatus.SUCCESSFUL if effectiveness_score > 0.5 else ApplicationStatus.FAILED
        
        issues = self._identify_issues(metrics_before, metrics_after)
        lessons_learned = self._extract_lessons_learned(suggestion, metrics_before, metrics_after)
        
        result = ApplicationResult(
            result_id=result_id,
            suggestion_id=suggestion_id,
            knowledge_id=suggestion.knowledge_id,
            status=status,
            applied_at=datetime.now() - timedelta(minutes=30),
            completed_at=datetime.now(),
            effectiveness_score=effectiveness_score,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            improvements=improvements,
            issues=issues,
            lessons_learned=lessons_learned
        )
        
        with self._lock:
            self._results[result_id] = result
            self._application_history[suggestion.knowledge_id].append(result_id)
        
        self._update_knowledge_metrics(suggestion.knowledge_id, effectiveness_score)
        
        if self._storage_path:
            self._save_application_data()
        
        self._logger.info(f"跟踪应用效果: {result_id} (有效性: {effectiveness_score:.2f})")
        return result
    
    def collect_feedback(
        self,
        knowledge_id: str,
        result_id: Optional[str],
        feedback_type: FeedbackType,
        rating: int,
        comment: str,
        suggested_improvements: Optional[List[str]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Feedback:
        """收集反馈
        
        Args:
            knowledge_id: 知识ID
            result_id: 结果ID
            feedback_type: 反馈类型
            rating: 评分 (1-5)
            comment: 评论
            suggested_improvements: 建议改进
            user_context: 用户上下文
        
        Returns:
            反馈对象
        """
        feedback_id = f"FB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(knowledge_id.encode()).hexdigest()[:8]}"
        
        feedback = Feedback(
            feedback_id=feedback_id,
            knowledge_id=knowledge_id,
            result_id=result_id,
            feedback_type=feedback_type,
            rating=max(1, min(5, rating)),
            comment=comment,
            suggested_improvements=suggested_improvements or [],
            created_at=datetime.now(),
            user_context=user_context or {}
        )
        
        with self._lock:
            self._feedbacks[feedback_id] = feedback
        
        self._apply_feedback_to_knowledge(feedback)
        
        if self._storage_path:
            self._save_application_data()
        
        self._logger.info(f"收集反馈: {feedback_id} (类型: {feedback_type.value}, 评分: {rating})")
        return feedback
    
    def get_application_history(
        self,
        knowledge_id: str,
        limit: int = 10
    ) -> List[ApplicationResult]:
        """获取应用历史
        
        Args:
            knowledge_id: 知识ID
            limit: 数量限制
        
        Returns:
            应用结果列表
        """
        result_ids = self._application_history.get(knowledge_id, [])
        
        results = []
        for result_id in result_ids[-limit:]:
            if result_id in self._results:
                results.append(self._results[result_id])
        
        return sorted(results, key=lambda r: r.applied_at, reverse=True)
    
    def get_feedback_summary(
        self,
        knowledge_id: str
    ) -> Dict[str, Any]:
        """获取反馈摘要
        
        Args:
            knowledge_id: 知识ID
        
        Returns:
            反馈摘要
        """
        knowledge_feedbacks = [
            f for f in self._feedbacks.values()
            if f.knowledge_id == knowledge_id
        ]
        
        if not knowledge_feedbacks:
            return {
                "total_count": 0,
                "avg_rating": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0
            }
        
        total_count = len(knowledge_feedbacks)
        avg_rating = sum(f.rating for f in knowledge_feedbacks) / total_count
        
        positive_count = sum(
            1 for f in knowledge_feedbacks
            if f.feedback_type == FeedbackType.POSITIVE
        )
        negative_count = sum(
            1 for f in knowledge_feedbacks
            if f.feedback_type == FeedbackType.NEGATIVE
        )
        neutral_count = sum(
            1 for f in knowledge_feedbacks
            if f.feedback_type == FeedbackType.NEUTRAL
        )
        
        return {
            "total_count": total_count,
            "avg_rating": avg_rating,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "suggestion_count": sum(
                1 for f in knowledge_feedbacks
                if f.feedback_type == FeedbackType.SUGGESTION
            )
        }
    
    def _calculate_relevance_score(
        self,
        entry: KnowledgeEntry,
        context: ApplicationContext
    ) -> float:
        """计算相关性分数"""
        score = 0.0
        
        if context.project_type.lower() in ' '.join(entry.tags).lower():
            score += self._relevance_weights['category_match']
        
        context_tags = set(context.technology_stack + context.objectives)
        entry_tags = set(entry.tags)
        tag_overlap = len(context_tags & entry_tags)
        tag_score = tag_overlap / max(len(context_tags), len(entry_tags), 1)
        score += tag_score * self._relevance_weights['tag_match']
        
        context_similarity = self._calculate_context_similarity(entry, context)
        score += context_similarity * self._relevance_weights['context_similarity']
        
        score += entry.quality_score * self._relevance_weights['quality_score']
        
        score += entry.success_rate * self._relevance_weights['success_rate']
        
        return score
    
    def _calculate_applicability_score(
        self,
        entry: KnowledgeEntry,
        context: ApplicationContext
    ) -> float:
        """计算适用性分数"""
        score = 0.5
        
        if entry.quality in [KnowledgeQuality.EXCELLENT, KnowledgeQuality.GOOD]:
            score += 0.2
        
        if entry.success_rate > 0.8:
            score += 0.15
        
        if entry.application_count > 5:
            score += 0.1
        
        constraint_violations = 0
        for constraint in context.constraints:
            if constraint.lower() in str(entry.content).lower():
                if 'not' in constraint.lower() or 'avoid' in constraint.lower():
                    constraint_violations += 1
        
        score -= constraint_violations * 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_context_similarity(
        self,
        entry: KnowledgeEntry,
        context: ApplicationContext
    ) -> float:
        """计算上下文相似度"""
        if not entry.metadata:
            return 0.5
        
        similarity_scores = []
        
        if 'project_type' in entry.metadata:
            if entry.metadata['project_type'] == context.project_type:
                similarity_scores.append(1.0)
            else:
                similarity_scores.append(0.3)
        
        if 'technology_stack' in entry.metadata:
            entry_tech = set(entry.metadata['technology_stack'])
            context_tech = set(context.technology_stack)
            overlap = len(entry_tech & context_tech)
            similarity_scores.append(overlap / max(len(entry_tech), len(context_tech), 1))
        
        return sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.5
    
    def _generate_implementation_steps(
        self,
        entry: KnowledgeEntry,
        context: ApplicationContext
    ) -> List[Dict[str, Any]]:
        """生成实施步骤"""
        steps = []
        
        if 'implementation_steps' in entry.content:
            steps = entry.content['implementation_steps']
        else:
            steps = [
                {
                    "step": 1,
                    "action": "评估当前状态",
                    "details": f"分析{context.project_type}项目的当前状态"
                },
                {
                    "step": 2,
                    "action": "准备实施环境",
                    "details": "确保满足所有前提条件"
                },
                {
                    "step": 3,
                    "action": "应用知识",
                    "details": f"实施{entry.title}"
                },
                {
                    "step": 4,
                    "action": "验证结果",
                    "details": "检查应用效果"
                },
                {
                    "step": 5,
                    "action": "记录经验",
                    "details": "记录应用过程中的经验教训"
                }
            ]
        
        return steps
    
    def _extract_benefits(self, entry: KnowledgeEntry) -> List[str]:
        """提取收益"""
        if 'benefits' in entry.content:
            return entry.content['benefits']
        
        benefits = []
        
        if entry.success_rate > 0.8:
            benefits.append("高成功率")
        
        if entry.quality in [KnowledgeQuality.EXCELLENT, KnowledgeQuality.GOOD]:
            benefits.append("质量保证")
        
        if entry.application_count > 5:
            benefits.append("经过多次验证")
        
        return benefits if benefits else ["提升整体质量"]
    
    def _identify_risks(
        self,
        entry: KnowledgeEntry,
        context: ApplicationContext
    ) -> List[str]:
        """识别风险"""
        risks = []
        
        if 'risks' in entry.content:
            risks.extend(entry.content['risks'])
        
        if entry.application_count < 3:
            risks.append("应用案例较少")
        
        if entry.quality in [KnowledgeQuality.POOR, KnowledgeQuality.AVERAGE]:
            risks.append("质量等级较低")
        
        for constraint in context.constraints:
            if constraint.lower() in str(entry.content).lower():
                risks.append(f"可能与约束冲突: {constraint}")
        
        return risks if risks else ["需要谨慎评估"]
    
    def _extract_prerequisites(self, entry: KnowledgeEntry) -> List[str]:
        """提取前提条件"""
        if 'prerequisites' in entry.content:
            return entry.content['prerequisites']
        
        if 'dependencies' in entry.metadata:
            return entry.metadata['dependencies']
        
        return ["确保项目环境准备就绪"]
    
    def _estimate_effort(self, entry: KnowledgeEntry) -> str:
        """估算工作量"""
        if 'estimated_effort' in entry.metadata:
            return entry.metadata['estimated_effort']
        
        if entry.application_count > 10:
            return "低"
        elif entry.application_count > 5:
            return "中"
        else:
            return "高"
    
    def _generate_suggestion_description(
        self,
        entry: KnowledgeEntry,
        context: ApplicationContext
    ) -> str:
        """生成建议描述"""
        desc = f"基于{entry.application_count}次成功应用，建议在{context.project_type}项目中应用此知识。\n\n"
        desc += f"知识类别: {entry.category.value}\n"
        desc += f"质量等级: {entry.quality.value}\n"
        desc += f"成功率: {entry.success_rate:.1%}\n\n"
        desc += f"详细说明: {entry.title}"
        
        return desc
    
    def _calculate_improvements(
        self,
        metrics_before: Dict[str, Any],
        metrics_after: Dict[str, Any]
    ) -> Dict[str, float]:
        """计算改进"""
        improvements = {}
        
        all_keys = set(metrics_before.keys()) | set(metrics_after.keys())
        
        for key in all_keys:
            before_val = metrics_before.get(key, 0)
            after_val = metrics_after.get(key, 0)
            
            if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                if before_val != 0:
                    improvement = (after_val - before_val) / abs(before_val)
                    improvements[key] = improvement
        
        return improvements
    
    def _calculate_effectiveness_score(
        self,
        improvements: Dict[str, float]
    ) -> float:
        """计算有效性分数"""
        if not improvements:
            return 0.0
        
        positive_improvements = [v for v in improvements.values() if v > 0]
        
        if not positive_improvements:
            return 0.0
        
        avg_improvement = sum(positive_improvements) / len(positive_improvements)
        
        effectiveness = min(avg_improvement / 0.5, 1.0)
        
        return effectiveness
    
    def _identify_issues(
        self,
        metrics_before: Dict[str, Any],
        metrics_after: Dict[str, Any]
    ) -> List[str]:
        """识别问题"""
        issues = []
        
        for key in metrics_before:
            if key in metrics_after:
                before_val = metrics_before[key]
                after_val = metrics_after[key]
                
                if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                    if after_val < before_val:
                        issues.append(f"{key} 性能下降: {before_val} -> {after_val}")
        
        return issues
    
    def _extract_lessons_learned(
        self,
        suggestion: ApplicationSuggestion,
        metrics_before: Dict[str, Any],
        metrics_after: Dict[str, Any]
    ) -> List[str]:
        """提取经验教训"""
        lessons = []
        
        improvements = self._calculate_improvements(metrics_before, metrics_after)
        
        if improvements:
            best_improvement = max(improvements.items(), key=lambda x: x[1])
            lessons.append(f"最佳改进: {best_improvement[0]} ({best_improvement[1]:.1%})")
        
        if suggestion.potential_risks:
            lessons.append(f"需要注意的风险: {', '.join(suggestion.potential_risks[:2])}")
        
        return lessons if lessons else ["应用过程顺利"]
    
    def _update_knowledge_metrics(
        self,
        knowledge_id: str,
        effectiveness_score: float
    ) -> None:
        """更新知识指标"""
        entry = self._knowledge_updater._entries.get(knowledge_id)
        if not entry:
            return
        
        entry.application_count += 1
        
        entry.success_rate = (
            entry.success_rate * (entry.application_count - 1) + effectiveness_score
        ) / entry.application_count
        
        entry.access_count += 1
        entry.updated_at = datetime.now()
    
    def _apply_feedback_to_knowledge(self, feedback: Feedback) -> None:
        """将反馈应用到知识"""
        entry = self._knowledge_updater._entries.get(feedback.knowledge_id)
        if not entry:
            return
        
        if feedback.feedback_type == FeedbackType.POSITIVE:
            entry.quality_score = min(1.0, entry.quality_score + 0.05)
        elif feedback.feedback_type == FeedbackType.NEGATIVE:
            entry.quality_score = max(0.0, entry.quality_score - 0.05)
        
        if feedback.suggested_improvements:
            if 'suggested_improvements' not in entry.metadata:
                entry.metadata['suggested_improvements'] = []
            
            entry.metadata['suggested_improvements'].extend(feedback.suggested_improvements)
        
        entry.updated_at = datetime.now()
    
    def _save_application_data(self) -> None:
        """保存应用数据"""
        if not self._storage_path:
            return
        
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "suggestions": {
                    sid: s.to_dict() for sid, s in self._suggestions.items()
                },
                "results": {
                    rid: r.to_dict() for rid, r in self._results.items()
                },
                "feedbacks": {
                    fid: f.to_dict() for fid, f in self._feedbacks.items()
                },
                "application_history": dict(self._application_history)
            }
            
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            temp_file = self._storage_path.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            temp_file.replace(self._storage_path)
            
        except Exception as e:
            self._logger.error(f"保存应用数据失败: {e}")
    
    def _load_application_data(self) -> None:
        """加载应用数据"""
        if not self._storage_path or not self._storage_path.exists():
            return
        
        try:
            with open(self._storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for sid, sdata in data.get("suggestions", {}).items():
                self._suggestions[sid] = ApplicationSuggestion(
                    suggestion_id=sdata["suggestion_id"],
                    knowledge_id=sdata["knowledge_id"],
                    relevance_score=sdata["relevance_score"],
                    applicability_score=sdata["applicability_score"],
                    priority=sdata["priority"],
                    title=sdata["title"],
                    description=sdata["description"],
                    implementation_steps=sdata.get("implementation_steps", []),
                    expected_benefits=sdata.get("expected_benefits", []),
                    potential_risks=sdata.get("potential_risks", []),
                    prerequisites=sdata.get("prerequisites", []),
                    estimated_effort=sdata.get("estimated_effort", "中"),
                    context_match=sdata.get("context_match", {}),
                    metadata=sdata.get("metadata", {})
                )
            
            for rid, rdata in data.get("results", {}).items():
                self._results[rid] = ApplicationResult(
                    result_id=rdata["result_id"],
                    suggestion_id=rdata["suggestion_id"],
                    knowledge_id=rdata["knowledge_id"],
                    status=ApplicationStatus(rdata["status"]),
                    applied_at=datetime.fromisoformat(rdata["applied_at"]),
                    completed_at=datetime.fromisoformat(rdata["completed_at"]) if rdata.get("completed_at") else None,
                    effectiveness_score=rdata["effectiveness_score"],
                    metrics_before=rdata["metrics_before"],
                    metrics_after=rdata["metrics_after"],
                    improvements=rdata.get("improvements", {}),
                    issues=rdata.get("issues", []),
                    lessons_learned=rdata.get("lessons_learned", []),
                    metadata=rdata.get("metadata", {})
                )
            
            for fid, fdata in data.get("feedbacks", {}).items():
                self._feedbacks[fid] = Feedback(
                    feedback_id=fdata["feedback_id"],
                    knowledge_id=fdata["knowledge_id"],
                    result_id=fdata.get("result_id"),
                    feedback_type=FeedbackType(fdata["feedback_type"]),
                    rating=fdata["rating"],
                    comment=fdata["comment"],
                    suggested_improvements=fdata.get("suggested_improvements", []),
                    created_at=datetime.fromisoformat(fdata["created_at"]),
                    user_context=fdata.get("user_context", {})
                )
            
            self._application_history = defaultdict(
                list,
                data.get("application_history", {})
            )
            
            self._logger.info(
                f"已加载应用数据: {len(self._suggestions)} 建议, "
                f"{len(self._results)} 结果, {len(self._feedbacks)} 反馈"
            )
            
        except Exception as e:
            self._logger.error(f"加载应用数据失败: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_suggestions": len(self._suggestions),
            "total_results": len(self._results),
            "total_feedbacks": len(self._feedbacks),
            "successful_applications": 0,
            "failed_applications": 0,
            "avg_effectiveness": 0.0,
            "avg_rating": 0.0
        }
        
        for result in self._results.values():
            if result.status == ApplicationStatus.SUCCESSFUL:
                stats["successful_applications"] += 1
            elif result.status == ApplicationStatus.FAILED:
                stats["failed_applications"] += 1
        
        if self._results:
            stats["avg_effectiveness"] = sum(
                r.effectiveness_score for r in self._results.values()
            ) / len(self._results)
        
        if self._feedbacks:
            stats["avg_rating"] = sum(
                f.rating for f in self._feedbacks.values()
            ) / len(self._feedbacks)
        
        return stats
