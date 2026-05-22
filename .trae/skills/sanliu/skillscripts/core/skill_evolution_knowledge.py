#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能演化知识积累 - Skill Evolution Knowledge

记录演化历史、提取演化模式、存储最佳实践，并支持知识检索。

核心功能:
- 记录演化历史
- 提取演化模式
- 存储最佳实践
- 支持知识检索
- 演化效果评估

使用示例:
    from skill_evolution_knowledge import SkillEvolutionKnowledge
    
    knowledge = SkillEvolutionKnowledge(skill_dir='./')
    
    # 记录演化事件
    knowledge.record_evolution(evolution_event)
    
    # 检索相关知识
    results = knowledge.search_knowledge("修复模式")
    
    # 提取最佳实践
    practices = knowledge.extract_best_practices()
"""

import json
import logging
import re
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class EvolutionType(Enum):
    """演化类型枚举"""
    CONTENT_UPDATE = "content_update"
    STRUCTURE_CHANGE = "structure_change"
    BEHAVIOR_MODIFICATION = "behavior_modification"
    OPTIMIZATION = "optimization"
    BUG_FIX = "bug_fix"
    FEATURE_ADDITION = "feature_addition"
    REFACTORING = "refactoring"
    DOCUMENTATION_UPDATE = "documentation_update"


class EvolutionStatus(Enum):
    """演化状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class KnowledgeCategory(Enum):
    """知识类别枚举"""
    EVOLUTION_PATTERN = "evolution_pattern"
    BEST_PRACTICE = "best_practice"
    FIX_STRATEGY = "fix_strategy"
    OPTIMIZATION_TIP = "optimization_tip"
    LESSON_LEARNED = "lesson_learned"
    ANTI_PATTERN = "anti_pattern"


class EffectivenessLevel(Enum):
    """有效性级别枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class EvolutionEvent:
    """演化事件数据类"""
    event_id: str
    evolution_type: EvolutionType
    status: EvolutionStatus
    triggered_at: datetime
    trigger_reason: str
    affected_files: List[str] = field(default_factory=list)
    changes_summary: str = ""
    execution_time_seconds: float = 0.0
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    rollback_available: bool = False
    rollback_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "evolution_type": self.evolution_type.value,
            "status": self.status.value,
            "triggered_at": self.triggered_at.isoformat(),
            "trigger_reason": self.trigger_reason,
            "affected_files": self.affected_files,
            "changes_summary": self.changes_summary,
            "execution_time_seconds": self.execution_time_seconds,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "rollback_available": self.rollback_available,
            "rollback_data": self.rollback_data,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvolutionEvent':
        return cls(
            event_id=data["event_id"],
            evolution_type=EvolutionType(data["evolution_type"]),
            status=EvolutionStatus(data["status"]),
            triggered_at=datetime.fromisoformat(data["triggered_at"]),
            trigger_reason=data["trigger_reason"],
            affected_files=data.get("affected_files", []),
            changes_summary=data.get("changes_summary", ""),
            execution_time_seconds=data.get("execution_time_seconds", 0.0),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error_message=data.get("error_message"),
            rollback_available=data.get("rollback_available", False),
            rollback_data=data.get("rollback_data"),
            metadata=data.get("metadata", {})
        )


@dataclass
class EvolutionPattern:
    """演化模式数据类"""
    pattern_id: str
    name: str
    description: str
    category: KnowledgeCategory
    trigger_conditions: List[str] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    success_rate: float = 0.0
    application_count: int = 0
    last_applied: Optional[datetime] = None
    effectiveness: EffectivenessLevel = EffectivenessLevel.UNKNOWN
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "trigger_conditions": self.trigger_conditions,
            "actions": self.actions,
            "success_rate": self.success_rate,
            "application_count": self.application_count,
            "last_applied": self.last_applied.isoformat() if self.last_applied else None,
            "effectiveness": self.effectiveness.value,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvolutionPattern':
        return cls(
            pattern_id=data["pattern_id"],
            name=data["name"],
            description=data["description"],
            category=KnowledgeCategory(data["category"]),
            trigger_conditions=data.get("trigger_conditions", []),
            actions=data.get("actions", []),
            success_rate=data.get("success_rate", 0.0),
            application_count=data.get("application_count", 0),
            last_applied=datetime.fromisoformat(data["last_applied"]) if data.get("last_applied") else None,
            effectiveness=EffectivenessLevel(data.get("effectiveness", "unknown")),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()
        )


@dataclass
class BestPractice:
    """最佳实践数据类"""
    practice_id: str
    title: str
    description: str
    category: KnowledgeCategory
    context: str
    solution: str
    benefits: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    effectiveness_score: float = 0.0
    verified: bool = False
    source_event_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "practice_id": self.practice_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "context": self.context,
            "solution": self.solution,
            "benefits": self.benefits,
            "prerequisites": self.prerequisites,
            "examples": self.examples,
            "effectiveness_score": self.effectiveness_score,
            "verified": self.verified,
            "source_event_ids": self.source_event_ids,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BestPractice':
        return cls(
            practice_id=data["practice_id"],
            title=data["title"],
            description=data["description"],
            category=KnowledgeCategory(data["category"]),
            context=data.get("context", ""),
            solution=data.get("solution", ""),
            benefits=data.get("benefits", []),
            prerequisites=data.get("prerequisites", []),
            examples=data.get("examples", []),
            effectiveness_score=data.get("effectiveness_score", 0.0),
            verified=data.get("verified", False),
            source_event_ids=data.get("source_event_ids", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()
        )


@dataclass
class KnowledgeSearchResult:
    """知识检索结果数据类"""
    query: str
    results: List[Dict[str, Any]]
    total_count: int
    search_time_seconds: float
    categories_found: List[str]
    relevance_scores: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "results": self.results,
            "total_count": self.total_count,
            "search_time_seconds": self.search_time_seconds,
            "categories_found": self.categories_found,
            "relevance_scores": self.relevance_scores
        }


class KnowledgeBase:
    """知识库管理器"""
    
    def __init__(self, knowledge_file: Path):
        self._knowledge_file = knowledge_file
        self._lock = threading.Lock()
        self._logger = logging.getLogger('KnowledgeBase')
        
        self._patterns: Dict[str, EvolutionPattern] = {}
        self._practices: Dict[str, BestPractice] = {}
        self._events: Dict[str, EvolutionEvent] = {}
        self._index: Dict[str, Set[str]] = defaultdict(set)
        
        self._load_knowledge()
    
    def _load_knowledge(self) -> None:
        """加载知识库"""
        if not self._knowledge_file.exists():
            return
        
        try:
            with open(self._knowledge_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for pattern_data in data.get("patterns", []):
                pattern = EvolutionPattern.from_dict(pattern_data)
                self._patterns[pattern.pattern_id] = pattern
            
            for practice_data in data.get("practices", []):
                practice = BestPractice.from_dict(practice_data)
                self._practices[practice.practice_id] = practice
            
            for event_data in data.get("events", []):
                event = EvolutionEvent.from_dict(event_data)
                self._events[event.event_id] = event
            
            self._rebuild_index()
            
            self._logger.info(
                f"已加载知识库: {len(self._patterns)} 模式, "
                f"{len(self._practices)} 最佳实践, {len(self._events)} 事件"
            )
            
        except Exception as e:
            self._logger.error(f"加载知识库失败: {e}")
    
    def save_knowledge(self) -> None:
        """保存知识库"""
        with self._lock:
            try:
                data = {
                    "version": "1.0",
                    "updated_at": datetime.now().isoformat(),
                    "patterns": [p.to_dict() for p in self._patterns.values()],
                    "practices": [p.to_dict() for p in self._practices.values()],
                    "events": [e.to_dict() for e in self._events.values()]
                }
                
                temp_file = self._knowledge_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                temp_file.replace(self._knowledge_file)
                
            except Exception as e:
                self._logger.error(f"保存知识库失败: {e}")
    
    def _rebuild_index(self) -> None:
        """重建索引"""
        self._index.clear()
        
        for pattern in self._patterns.values():
            self._index_pattern(pattern)
        
        for practice in self._practices.values():
            self._index_practice(practice)
    
    def _index_pattern(self, pattern: EvolutionPattern) -> None:
        """索引模式"""
        words = self._extract_keywords(pattern.name + " " + pattern.description)
        for word in words:
            self._index[f"pattern:{word}"].add(pattern.pattern_id)
        
        for tag in pattern.tags:
            self._index[f"tag:{tag}"].add(pattern.pattern_id)
    
    def _index_practice(self, practice: BestPractice) -> None:
        """索引最佳实践"""
        words = self._extract_keywords(practice.title + " " + practice.description)
        for word in words:
            self._index[f"practice:{word}"].add(practice.practice_id)
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """提取关键词"""
        words = re.findall(r'\w+', text.lower())
        return {w for w in words if len(w) >= 2}
    
    def add_pattern(self, pattern: EvolutionPattern) -> None:
        """添加模式"""
        with self._lock:
            self._patterns[pattern.pattern_id] = pattern
            self._index_pattern(pattern)
    
    def add_practice(self, practice: BestPractice) -> None:
        """添加最佳实践"""
        with self._lock:
            self._practices[practice.practice_id] = practice
            self._index_practice(practice)
    
    def add_event(self, event: EvolutionEvent) -> None:
        """添加事件"""
        with self._lock:
            self._events[event.event_id] = event
            
            if len(self._events) > 1000:
                sorted_events = sorted(
                    self._events.values(),
                    key=lambda e: e.triggered_at,
                    reverse=True
                )
                self._events = {e.event_id: e for e in sorted_events[:1000]}
    
    def get_pattern(self, pattern_id: str) -> Optional[EvolutionPattern]:
        """获取模式"""
        return self._patterns.get(pattern_id)
    
    def get_practice(self, practice_id: str) -> Optional[BestPractice]:
        """获取最佳实践"""
        return self._practices.get(practice_id)
    
    def get_event(self, event_id: str) -> Optional[EvolutionEvent]:
        """获取事件"""
        return self._events.get(event_id)
    
    def search_patterns(self, query: str, limit: int = 10) -> List[EvolutionPattern]:
        """搜索模式"""
        keywords = self._extract_keywords(query)
        pattern_scores: Dict[str, int] = defaultdict(int)
        
        for keyword in keywords:
            pattern_ids = self._index.get(f"pattern:{keyword}", set())
            for pid in pattern_ids:
                pattern_scores[pid] += 1
        
        sorted_ids = sorted(pattern_scores.keys(), key=lambda x: pattern_scores[x], reverse=True)
        
        results = []
        for pid in sorted_ids[:limit]:
            if pid in self._patterns:
                results.append(self._patterns[pid])
        
        return results
    
    def search_practices(self, query: str, limit: int = 10) -> List[BestPractice]:
        """搜索最佳实践"""
        keywords = self._extract_keywords(query)
        practice_scores: Dict[str, int] = defaultdict(int)
        
        for keyword in keywords:
            practice_ids = self._index.get(f"practice:{keyword}", set())
            for pid in practice_ids:
                practice_scores[pid] += 1
        
        sorted_ids = sorted(practice_scores.keys(), key=lambda x: practice_scores[x], reverse=True)
        
        results = []
        for pid in sorted_ids[:limit]:
            if pid in self._practices:
                results.append(self._practices[pid])
        
        return results
    
    def get_all_patterns(self) -> List[EvolutionPattern]:
        """获取所有模式"""
        return list(self._patterns.values())
    
    def get_all_practices(self) -> List[BestPractice]:
        """获取所有最佳实践"""
        return list(self._practices.values())
    
    def get_recent_events(self, limit: int = 50) -> List[EvolutionEvent]:
        """获取最近事件"""
        sorted_events = sorted(
            self._events.values(),
            key=lambda e: e.triggered_at,
            reverse=True
        )
        return sorted_events[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        successful_events = sum(
            1 for e in self._events.values()
            if e.status == EvolutionStatus.COMPLETED
        )
        
        return {
            "total_patterns": len(self._patterns),
            "total_practices": len(self._practices),
            "total_events": len(self._events),
            "successful_events": successful_events,
            "success_rate": successful_events / len(self._events) if self._events else 0,
            "index_size": len(self._index)
        }


class SkillEvolutionKnowledge:
    """技能演化知识管理器"""
    
    def __init__(
        self,
        skill_dir: str,
        knowledge_dir: Optional[str] = None,
        auto_save: bool = True
    ):
        self._skill_dir = Path(skill_dir)
        self._knowledge_dir = Path(knowledge_dir) if knowledge_dir else self._skill_dir / ".evolution" / "knowledge"
        self._knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        self._knowledge_base = KnowledgeBase(self._knowledge_dir / "evolution_knowledge.json")
        self._auto_save = auto_save
        self._logger = logging.getLogger('SkillEvolutionKnowledge')
        
        self._pattern_extractor = PatternExtractor()
        self._practice_extractor = PracticeExtractor()
        
        self._lock = threading.Lock()
    
    def record_evolution(self, event: EvolutionEvent) -> str:
        """记录演化事件
        
        Args:
            event: 演化事件
        
        Returns:
            事件ID
        """
        self._knowledge_base.add_event(event)
        
        if event.status == EvolutionStatus.COMPLETED:
            self._extract_and_store_pattern(event)
        
        if self._auto_save:
            self._knowledge_base.save_knowledge()
        
        self._logger.info(f"已记录演化事件: {event.event_id}")
        return event.event_id
    
    def _extract_and_store_pattern(self, event: EvolutionEvent) -> None:
        """从事件中提取并存储模式"""
        pattern = self._pattern_extractor.extract(event)
        if pattern:
            self._knowledge_base.add_pattern(pattern)
            self._logger.debug(f"从事件 {event.event_id} 提取模式: {pattern.name}")
    
    def extract_best_practices(
        self,
        min_success_rate: float = 0.7,
        min_applications: int = 3
    ) -> List[BestPractice]:
        """提取最佳实践
        
        Args:
            min_success_rate: 最低成功率
            min_applications: 最低应用次数
        
        Returns:
            最佳实践列表
        """
        practices = []
        
        patterns = self._knowledge_base.get_all_patterns()
        for pattern in patterns:
            if pattern.success_rate >= min_success_rate and pattern.application_count >= min_applications:
                practice = self._practice_extractor.from_pattern(pattern)
                if practice:
                    self._knowledge_base.add_practice(practice)
                    practices.append(practice)
        
        if self._auto_save:
            self._knowledge_base.save_knowledge()
        
        self._logger.info(f"提取了 {len(practices)} 个最佳实践")
        return practices
    
    def search_knowledge(
        self,
        query: str,
        categories: Optional[List[KnowledgeCategory]] = None,
        limit: int = 10
    ) -> KnowledgeSearchResult:
        """搜索知识
        
        Args:
            query: 搜索查询
            categories: 要搜索的知识类别
            limit: 结果数量限制
        
        Returns:
            搜索结果
        """
        start_time = datetime.now()
        
        results = []
        categories_found = []
        relevance_scores: Dict[str, float] = {}
        
        if categories is None or KnowledgeCategory.EVOLUTION_PATTERN in categories:
            patterns = self._knowledge_base.search_patterns(query, limit)
            for p in patterns:
                results.append({
                    "type": "pattern",
                    "id": p.pattern_id,
                    "name": p.name,
                    "description": p.description,
                    "category": p.category.value,
                    "success_rate": p.success_rate
                })
                relevance_scores[p.pattern_id] = p.success_rate
            if patterns:
                categories_found.append("evolution_pattern")
        
        if categories is None or KnowledgeCategory.BEST_PRACTICE in categories:
            practices = self._knowledge_base.search_practices(query, limit)
            for p in practices:
                results.append({
                    "type": "practice",
                    "id": p.practice_id,
                    "title": p.title,
                    "description": p.description,
                    "category": p.category.value,
                    "effectiveness_score": p.effectiveness_score
                })
                relevance_scores[p.practice_id] = p.effectiveness_score
            if practices:
                categories_found.append("best_practice")
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return KnowledgeSearchResult(
            query=query,
            results=results[:limit],
            total_count=len(results),
            search_time_seconds=duration,
            categories_found=categories_found,
            relevance_scores=relevance_scores
        )
    
    def get_evolution_history(
        self,
        evolution_type: Optional[EvolutionType] = None,
        status: Optional[EvolutionStatus] = None,
        limit: int = 50
    ) -> List[EvolutionEvent]:
        """获取演化历史
        
        Args:
            evolution_type: 演化类型过滤
            status: 状态过滤
            limit: 结果数量限制
        
        Returns:
            演化事件列表
        """
        events = self._knowledge_base.get_recent_events(limit * 2)
        
        filtered = events
        if evolution_type:
            filtered = [e for e in filtered if e.evolution_type == evolution_type]
        if status:
            filtered = [e for e in filtered if e.status == status]
        
        return filtered[:limit]
    
    def get_pattern_recommendations(
        self,
        context: Dict[str, Any]
    ) -> List[EvolutionPattern]:
        """获取模式推荐
        
        Args:
            context: 上下文信息
        
        Returns:
            推荐的模式列表
        """
        patterns = self._knowledge_base.get_all_patterns()
        
        scored_patterns: List[Tuple[EvolutionPattern, float]] = []
        
        for pattern in patterns:
            score = self._calculate_pattern_score(pattern, context)
            scored_patterns.append((pattern, score))
        
        scored_patterns.sort(key=lambda x: x[1], reverse=True)
        
        return [p for p, s in scored_patterns[:10]]
    
    def _calculate_pattern_score(
        self,
        pattern: EvolutionPattern,
        context: Dict[str, Any]
    ) -> float:
        """计算模式匹配分数"""
        score = 0.0
        
        score += pattern.success_rate * 0.4
        
        if pattern.effectiveness == EffectivenessLevel.HIGH:
            score += 0.3
        elif pattern.effectiveness == EffectivenessLevel.MEDIUM:
            score += 0.15
        
        score += min(pattern.application_count / 10, 0.2)
        
        trigger_match = 0
        for condition in pattern.trigger_conditions:
            if condition.lower() in str(context).lower():
                trigger_match += 1
        if pattern.trigger_conditions:
            score += (trigger_match / len(pattern.trigger_conditions)) * 0.1
        
        return score
    
    def update_pattern_effectiveness(
        self,
        pattern_id: str,
        success: bool
    ) -> None:
        """更新模式有效性
        
        Args:
            pattern_id: 模式ID
            success: 是否成功
        """
        pattern = self._knowledge_base.get_pattern(pattern_id)
        if not pattern:
            return
        
        pattern.application_count += 1
        pattern.last_applied = datetime.now()
        pattern.updated_at = datetime.now()
        
        if success:
            pattern.success_rate = (
                pattern.success_rate * (pattern.application_count - 1) + 1.0
            ) / pattern.application_count
        else:
            pattern.success_rate = (
                pattern.success_rate * (pattern.application_count - 1)
            ) / pattern.application_count
        
        if pattern.success_rate >= 0.8:
            pattern.effectiveness = EffectivenessLevel.HIGH
        elif pattern.success_rate >= 0.5:
            pattern.effectiveness = EffectivenessLevel.MEDIUM
        else:
            pattern.effectiveness = EffectivenessLevel.LOW
        
        if self._auto_save:
            self._knowledge_base.save_knowledge()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._knowledge_base.get_statistics()
    
    def export_knowledge(self, output_path: str) -> str:
        """导出知识库
        
        Args:
            output_path: 输出路径
        
        Returns:
            导出文件路径
        """
        data = {
            "exported_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "patterns": [p.to_dict() for p in self._knowledge_base.get_all_patterns()],
            "practices": [p.to_dict() for p in self._knowledge_base.get_all_practices()],
            "recent_events": [e.to_dict() for e in self._knowledge_base.get_recent_events(100)]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self._logger.info(f"知识库已导出到: {output_path}")
        return output_path
    
    def import_knowledge(self, input_path: str, merge: bool = True) -> int:
        """导入知识库
        
        Args:
            input_path: 输入路径
            merge: 是否合并（True）或覆盖（False）
        
        Returns:
            导入的项目数量
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        
        if not merge:
            self._knowledge_base._patterns.clear()
            self._knowledge_base._practices.clear()
        
        for pattern_data in data.get("patterns", []):
            pattern = EvolutionPattern.from_dict(pattern_data)
            self._knowledge_base.add_pattern(pattern)
            count += 1
        
        for practice_data in data.get("practices", []):
            practice = BestPractice.from_dict(practice_data)
            self._knowledge_base.add_practice(practice)
            count += 1
        
        if self._auto_save:
            self._knowledge_base.save_knowledge()
        
        self._logger.info(f"从 {input_path} 导入了 {count} 个知识项")
        return count


class PatternExtractor:
    """模式提取器"""
    
    def extract(self, event: EvolutionEvent) -> Optional[EvolutionPattern]:
        """从事件中提取模式"""
        if event.status != EvolutionStatus.COMPLETED:
            return None
        
        pattern_id = f"PATTERN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        name = self._generate_pattern_name(event)
        description = self._generate_pattern_description(event)
        trigger_conditions = self._extract_trigger_conditions(event)
        actions = self._extract_actions(event)
        
        return EvolutionPattern(
            pattern_id=pattern_id,
            name=name,
            description=description,
            category=KnowledgeCategory.EVOLUTION_PATTERN,
            trigger_conditions=trigger_conditions,
            actions=actions,
            success_rate=1.0,
            application_count=1,
            last_applied=event.completed_at,
            effectiveness=EffectivenessLevel.UNKNOWN,
            tags=self._extract_tags(event)
        )
    
    def _generate_pattern_name(self, event: EvolutionEvent) -> str:
        """生成模式名称"""
        type_names = {
            EvolutionType.CONTENT_UPDATE: "内容更新",
            EvolutionType.STRUCTURE_CHANGE: "结构调整",
            EvolutionType.BEHAVIOR_MODIFICATION: "行为修改",
            EvolutionType.OPTIMIZATION: "优化改进",
            EvolutionType.BUG_FIX: "问题修复",
            EvolutionType.FEATURE_ADDITION: "功能添加",
            EvolutionType.REFACTORING: "重构优化",
            EvolutionType.DOCUMENTATION_UPDATE: "文档更新"
        }
        
        type_name = type_names.get(event.evolution_type, "未知类型")
        return f"{type_name}模式"
    
    def _generate_pattern_description(self, event: EvolutionEvent) -> str:
        """生成模式描述"""
        return f"触发原因: {event.trigger_reason}. 变更摘要: {event.changes_summary}"
    
    def _extract_trigger_conditions(self, event: EvolutionEvent) -> List[str]:
        """提取触发条件"""
        conditions = [event.trigger_reason]
        
        for file_path in event.affected_files:
            conditions.append(f"文件变化: {file_path}")
        
        return conditions[:5]
    
    def _extract_actions(self, event: EvolutionEvent) -> List[Dict[str, Any]]:
        """提取动作"""
        actions = []
        
        for file_path in event.affected_files:
            actions.append({
                "type": "file_modification",
                "target": file_path,
                "timestamp": event.triggered_at.isoformat()
            })
        
        return actions
    
    def _extract_tags(self, event: EvolutionEvent) -> List[str]:
        """提取标签"""
        tags = [event.evolution_type.value]
        
        if event.affected_files:
            for file_path in event.affected_files:
                if ".py" in file_path:
                    tags.append("python")
                elif ".md" in file_path:
                    tags.append("markdown")
                elif ".json" in file_path:
                    tags.append("json")
        
        return list(set(tags))


class PracticeExtractor:
    """最佳实践提取器"""
    
    def from_pattern(self, pattern: EvolutionPattern) -> Optional[BestPractice]:
        """从模式提取最佳实践"""
        if pattern.success_rate < 0.7:
            return None
        
        practice_id = f"PRACTICE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return BestPractice(
            practice_id=practice_id,
            title=f"最佳实践: {pattern.name}",
            description=pattern.description,
            category=KnowledgeCategory.BEST_PRACTICE,
            context="基于成功演化模式提取",
            solution=self._generate_solution(pattern),
            benefits=self._extract_benefits(pattern),
            prerequisites=pattern.trigger_conditions,
            examples=[{"action": a} for a in pattern.actions[:3]],
            effectiveness_score=pattern.success_rate,
            verified=True,
            source_event_ids=[]
        )
    
    def _generate_solution(self, pattern: EvolutionPattern) -> str:
        """生成解决方案描述"""
        actions_desc = []
        for action in pattern.actions[:3]:
            action_type = action.get("type", "unknown")
            target = action.get("target", "")
            actions_desc.append(f"- {action_type}: {target}")
        
        return "\n".join(actions_desc) if actions_desc else "执行标准演化流程"
    
    def _extract_benefits(self, pattern: EvolutionPattern) -> List[str]:
        """提取收益"""
        benefits = []
        
        if pattern.success_rate >= 0.9:
            benefits.append("高成功率保障")
        elif pattern.success_rate >= 0.7:
            benefits.append("良好的成功记录")
        
        if pattern.application_count >= 5:
            benefits.append("经过多次验证")
        
        if pattern.effectiveness == EffectivenessLevel.HIGH:
            benefits.append("高效执行")
        
        return benefits if benefits else ["有效的演化策略"]
