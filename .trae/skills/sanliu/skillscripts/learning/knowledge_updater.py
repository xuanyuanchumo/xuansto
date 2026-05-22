#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库更新器 - Knowledge Updater

实现知识自动分类、质量评估、去重合并和版本管理。

核心功能:
- 知识自动分类
- 知识质量评估
- 知识去重和合并
- 知识版本管理
- 知识生命周期管理
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


class KnowledgeCategory(Enum):
    """知识类别枚举"""
    PATTERN = "pattern"
    PRACTICE = "practice"
    SOLUTION = "solution"
    LESSON = "lesson"
    TEMPLATE = "template"
    REFERENCE = "reference"
    GUIDELINE = "guideline"
    ANTI_PATTERN = "anti_pattern"


class KnowledgeQuality(Enum):
    """知识质量枚举"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    OBSOLETE = "obsolete"


class UpdateStrategy(Enum):
    """更新策略枚举"""
    MERGE = "merge"
    REPLACE = "replace"
    APPEND = "append"
    VERSION = "version"
    ARCHIVE = "archive"


@dataclass
class KnowledgeEntry:
    """知识条目数据类"""
    entry_id: str
    category: KnowledgeCategory
    title: str
    content: Dict[str, Any]
    quality: KnowledgeQuality
    quality_score: float
    version: int
    created_at: datetime
    updated_at: datetime
    access_count: int
    application_count: int
    success_rate: float
    tags: List[str] = field(default_factory=list)
    source: str = ""
    dependencies: List[str] = field(default_factory=list)
    related_entries: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "category": self.category.value,
            "title": self.title,
            "content": self.content,
            "quality": self.quality.value,
            "quality_score": self.quality_score,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "access_count": self.access_count,
            "application_count": self.application_count,
            "success_rate": self.success_rate,
            "tags": self.tags,
            "source": self.source,
            "dependencies": self.dependencies,
            "related_entries": self.related_entries,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeEntry':
        return cls(
            entry_id=data["entry_id"],
            category=KnowledgeCategory(data["category"]),
            title=data["title"],
            content=data["content"],
            quality=KnowledgeQuality(data["quality"]),
            quality_score=data["quality_score"],
            version=data["version"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            access_count=data.get("access_count", 0),
            application_count=data.get("application_count", 0),
            success_rate=data.get("success_rate", 0.0),
            tags=data.get("tags", []),
            source=data.get("source", ""),
            dependencies=data.get("dependencies", []),
            related_entries=data.get("related_entries", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class KnowledgeVersion:
    """知识版本数据类"""
    version_id: str
    entry_id: str
    version_number: int
    content: Dict[str, Any]
    created_at: datetime
    change_summary: str
    changed_by: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "entry_id": self.entry_id,
            "version_number": self.version_number,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "change_summary": self.change_summary,
            "changed_by": self.changed_by
        }


class KnowledgeUpdater:
    """知识库更新器"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self._storage_path = Path(storage_path) if storage_path else None
        self._logger = logging.getLogger('KnowledgeUpdater')
        self._lock = threading.Lock()
        
        self._entries: Dict[str, KnowledgeEntry] = {}
        self._versions: Dict[str, List[KnowledgeVersion]] = defaultdict(list)
        self._category_index: Dict[str, Set[str]] = defaultdict(set)
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)
        self._quality_index: Dict[str, Set[str]] = defaultdict(set)
        
        self._classification_rules = self._initialize_classification_rules()
        self._quality_thresholds = self._initialize_quality_thresholds()
        
        if self._storage_path:
            self._load_knowledge()
    
    def _initialize_classification_rules(self) -> Dict[str, Any]:
        """初始化分类规则"""
        return {
            KnowledgeCategory.PATTERN: {
                "keywords": ["模式", "pattern", "规律", "重复", "识别"],
                "content_keys": ["pattern_type", "features", "occurrences"],
                "min_confidence": 0.6
            },
            KnowledgeCategory.PRACTICE: {
                "keywords": ["最佳实践", "best practice", "推荐", "建议", "优化"],
                "content_keys": ["implementation_steps", "benefits", "risks"],
                "min_confidence": 0.7
            },
            KnowledgeCategory.SOLUTION: {
                "keywords": ["解决方案", "solution", "修复", "方法", "实现"],
                "content_keys": ["solution", "steps", "approach"],
                "min_confidence": 0.5
            },
            KnowledgeCategory.LESSON: {
                "keywords": ["教训", "lesson", "失败", "错误", "避免"],
                "content_keys": ["failure", "error", "lesson_learned"],
                "min_confidence": 0.4
            },
            KnowledgeCategory.TEMPLATE: {
                "keywords": ["模板", "template", "示例", "example", "样板"],
                "content_keys": ["template", "example", "sample"],
                "min_confidence": 0.5
            },
            KnowledgeCategory.REFERENCE: {
                "keywords": ["参考", "reference", "文档", "文档", "链接"],
                "content_keys": ["reference", "documentation", "link"],
                "min_confidence": 0.3
            },
            KnowledgeCategory.GUIDELINE: {
                "keywords": ["指南", "guideline", "规范", "标准", "原则"],
                "content_keys": ["guideline", "standard", "principle"],
                "min_confidence": 0.6
            },
            KnowledgeCategory.ANTI_PATTERN: {
                "keywords": ["反模式", "anti-pattern", "避免", "不要", "错误做法"],
                "content_keys": ["anti_pattern", "avoid", "bad_practice"],
                "min_confidence": 0.5
            }
        }
    
    def _initialize_quality_thresholds(self) -> Dict[str, Any]:
        """初始化质量阈值"""
        return {
            KnowledgeQuality.EXCELLENT: {
                "min_score": 0.9,
                "min_applications": 10,
                "min_success_rate": 0.95
            },
            KnowledgeQuality.GOOD: {
                "min_score": 0.75,
                "min_applications": 5,
                "min_success_rate": 0.85
            },
            KnowledgeQuality.AVERAGE: {
                "min_score": 0.6,
                "min_applications": 2,
                "min_success_rate": 0.7
            },
            KnowledgeQuality.POOR: {
                "min_score": 0.4,
                "min_applications": 1,
                "min_success_rate": 0.5
            },
            KnowledgeQuality.OBSOLETE: {
                "min_score": 0.0,
                "min_applications": 0,
                "min_success_rate": 0.0
            }
        }
    
    def classify_knowledge(
        self,
        knowledge_data: Dict[str, Any]
    ) -> KnowledgeCategory:
        """自动分类知识
        
        Args:
            knowledge_data: 知识数据
        
        Returns:
            知识类别
        """
        scores = {}
        
        for category, rules in self._classification_rules.items():
            score = 0.0
            
            title = knowledge_data.get('title', '')
            description = knowledge_data.get('description', '')
            content_str = str(knowledge_data.get('content', {}))
            
            combined_text = f"{title} {description} {content_str}".lower()
            
            for keyword in rules['keywords']:
                if keyword.lower() in combined_text:
                    score += 1.0
            
            score = score / len(rules['keywords']) if rules['keywords'] else 0
            
            content_keys = rules['content_keys']
            matching_keys = sum(
                1 for key in content_keys
                if key in knowledge_data.get('content', {})
            )
            score += matching_keys / len(content_keys) if content_keys else 0
            
            confidence = knowledge_data.get('confidence_score', 0.5)
            if confidence >= rules['min_confidence']:
                score += 0.5
            
            scores[category] = score
        
        if not scores:
            return KnowledgeCategory.REFERENCE
        
        best_category = max(scores.items(), key=lambda x: x[1])
        return best_category[0]
    
    def evaluate_knowledge_quality(
        self,
        entry_id: str,
        additional_metrics: Optional[Dict[str, Any]] = None
    ) -> Tuple[KnowledgeQuality, float]:
        """评估知识质量
        
        Args:
            entry_id: 条目ID
            additional_metrics: 额外指标
        
        Returns:
            (质量级别, 质量分数)
        """
        entry = self._entries.get(entry_id)
        if not entry:
            return KnowledgeQuality.POOR, 0.0
        
        base_score = entry.quality_score
        
        application_factor = min(entry.application_count / 10.0, 1.0)
        success_factor = entry.success_rate
        access_factor = min(entry.access_count / 50.0, 1.0)
        
        age_days = (datetime.now() - entry.updated_at).days
        recency_factor = max(0.5, 1.0 - age_days / 365.0)
        
        final_score = (
            base_score * 0.3 +
            application_factor * 0.25 +
            success_factor * 0.25 +
            access_factor * 0.1 +
            recency_factor * 0.1
        )
        
        if additional_metrics:
            if 'user_rating' in additional_metrics:
                final_score = final_score * 0.8 + additional_metrics['user_rating'] * 0.2
            
            if 'feedback_score' in additional_metrics:
                final_score = final_score * 0.9 + additional_metrics['feedback_score'] * 0.1
        
        quality = self._determine_quality_level(final_score)
        
        return quality, final_score
    
    def deduplicate_knowledge(
        self,
        knowledge_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """去重知识
        
        Args:
            knowledge_data: 知识数据
        
        Returns:
            (是否重复, 重复条目ID)
        """
        title = knowledge_data.get('title', '')
        content = knowledge_data.get('content', {})
        
        title_hash = hashlib.md5(title.encode()).hexdigest()
        
        for entry_id, entry in self._entries.items():
            entry_title_hash = hashlib.md5(entry.title.encode()).hexdigest()
            
            if title_hash == entry_title_hash:
                return True, entry_id
        
        content_str = json.dumps(content, sort_keys=True)
        content_hash = hashlib.md5(content_str.encode()).hexdigest()
        
        for entry_id, entry in self._entries.items():
            entry_content_str = json.dumps(entry.content, sort_keys=True)
            entry_content_hash = hashlib.md5(entry_content_str.encode()).hexdigest()
            
            if content_hash == entry_content_hash:
                return True, entry_id
        
        similarity_threshold = 0.85
        for entry_id, entry in self._entries.items():
            similarity = self._calculate_content_similarity(
                knowledge_data,
                {"title": entry.title, "content": entry.content}
            )
            
            if similarity >= similarity_threshold:
                return True, entry_id
        
        return False, None
    
    def merge_knowledge(
        self,
        target_id: str,
        source_id: str,
        merge_strategy: UpdateStrategy = UpdateStrategy.MERGE
    ) -> Optional[KnowledgeEntry]:
        """合并知识
        
        Args:
            target_id: 目标条目ID
            source_id: 源条目ID
            merge_strategy: 合并策略
        
        Returns:
            合并后的条目
        """
        target = self._entries.get(target_id)
        source = self._entries.get(source_id)
        
        if not target or not source:
            return None
        
        with self._lock:
            old_version = self._create_version(target, "合并前备份")
            
            if merge_strategy == UpdateStrategy.MERGE:
                merged_content = self._merge_contents(
                    target.content,
                    source.content
                )
                target.content = merged_content
                
                target.tags = list(set(target.tags + source.tags))
                
                target.application_count += source.application_count
                target.success_rate = (
                    target.success_rate * target.application_count +
                    source.success_rate * source.application_count
                ) / (target.application_count + source.application_count)
                
            elif merge_strategy == UpdateStrategy.REPLACE:
                target.content = source.content.copy()
                target.tags = source.tags.copy()
                
            elif merge_strategy == UpdateStrategy.APPEND:
                for key, value in source.content.items():
                    if key in target.content:
                        if isinstance(target.content[key], list):
                            if isinstance(value, list):
                                target.content[key].extend(value)
                            else:
                                target.content[key].append(value)
                        elif isinstance(target.content[key], dict) and isinstance(value, dict):
                            target.content[key].update(value)
                    else:
                        target.content[key] = value
            
            target.version += 1
            target.updated_at = datetime.now()
            
            new_version = self._create_version(target, f"合并自 {source_id}")
            self._versions[target_id].append(old_version)
            self._versions[target_id].append(new_version)
            
            self._remove_entry(source_id)
            
            if self._storage_path:
                self._save_knowledge()
            
            self._logger.info(f"已合并知识: {source_id} -> {target_id}")
            return target
    
    def update_knowledge(
        self,
        entry_id: str,
        updates: Dict[str, Any],
        update_strategy: UpdateStrategy = UpdateStrategy.VERSION
    ) -> Optional[KnowledgeEntry]:
        """更新知识
        
        Args:
            entry_id: 条目ID
            updates: 更新内容
            update_strategy: 更新策略
        
        Returns:
            更新后的条目
        """
        entry = self._entries.get(entry_id)
        if not entry:
            return None
        
        with self._lock:
            if update_strategy == UpdateStrategy.VERSION:
                old_version = self._create_version(entry, "更新前版本")
                self._versions[entry_id].append(old_version)
            
            if 'content' in updates:
                if update_strategy == UpdateStrategy.MERGE:
                    entry.content = self._merge_contents(entry.content, updates['content'])
                else:
                    entry.content.update(updates['content'])
            
            if 'tags' in updates:
                if update_strategy == UpdateStrategy.APPEND:
                    entry.tags = list(set(entry.tags + updates['tags']))
                else:
                    entry.tags = updates['tags']
            
            if 'metadata' in updates:
                entry.metadata.update(updates['metadata'])
            
            entry.version += 1
            entry.updated_at = datetime.now()
            
            quality, quality_score = self.evaluate_knowledge_quality(entry_id)
            entry.quality = quality
            entry.quality_score = quality_score
            
            self._update_indices(entry)
            
            if self._storage_path:
                self._save_knowledge()
            
            self._logger.info(f"已更新知识: {entry_id} (版本: {entry.version})")
            return entry
    
    def add_knowledge(
        self,
        knowledge_data: Dict[str, Any],
        auto_classify: bool = True
    ) -> KnowledgeEntry:
        """添加知识
        
        Args:
            knowledge_data: 知识数据
            auto_classify: 是否自动分类
        
        Returns:
            添加的条目
        """
        is_duplicate, duplicate_id = self.deduplicate_knowledge(knowledge_data)
        
        if is_duplicate and duplicate_id:
            self._logger.info(f"检测到重复知识，更新现有条目: {duplicate_id}")
            return self.update_knowledge(
                duplicate_id,
                knowledge_data,
                UpdateStrategy.MERGE
            )
        
        with self._lock:
            entry_id = f"KB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(str(knowledge_data).encode()).hexdigest()[:8]}"
            
            if auto_classify:
                category = self.classify_knowledge(knowledge_data)
            else:
                category = KnowledgeCategory(
                    knowledge_data.get('category', 'reference')
                )
            
            quality_score = knowledge_data.get('quality_score', 0.7)
            quality = self._determine_quality_level(quality_score)
            
            entry = KnowledgeEntry(
                entry_id=entry_id,
                category=category,
                title=knowledge_data.get('title', '未命名知识'),
                content=knowledge_data.get('content', {}),
                quality=quality,
                quality_score=quality_score,
                version=1,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                access_count=0,
                application_count=knowledge_data.get('application_count', 0),
                success_rate=knowledge_data.get('success_rate', 0.0),
                tags=knowledge_data.get('tags', []),
                source=knowledge_data.get('source', ''),
                dependencies=knowledge_data.get('dependencies', []),
                related_entries=knowledge_data.get('related_entries', []),
                metadata=knowledge_data.get('metadata', {})
            )
            
            self._entries[entry_id] = entry
            self._index_entry(entry)
            
            version = self._create_version(entry, "初始版本")
            self._versions[entry_id].append(version)
            
            if self._storage_path:
                self._save_knowledge()
            
            self._logger.info(f"已添加知识: {entry.title} (类别: {category.value})")
            return entry
    
    def get_knowledge_version(
        self,
        entry_id: str,
        version_number: Optional[int] = None
    ) -> Optional[KnowledgeVersion]:
        """获取知识版本
        
        Args:
            entry_id: 条目ID
            version_number: 版本号（None表示最新版本）
        
        Returns:
            知识版本
        """
        versions = self._versions.get(entry_id, [])
        
        if not versions:
            return None
        
        if version_number is None:
            return versions[-1]
        
        for version in versions:
            if version.version_number == version_number:
                return version
        
        return None
    
    def rollback_knowledge(
        self,
        entry_id: str,
        version_number: int
    ) -> Optional[KnowledgeEntry]:
        """回滚知识
        
        Args:
            entry_id: 条目ID
            version_number: 目标版本号
        
        Returns:
            回滚后的条目
        """
        entry = self._entries.get(entry_id)
        if not entry:
            return None
        
        target_version = self.get_knowledge_version(entry_id, version_number)
        if not target_version:
            return None
        
        with self._lock:
            current_version = self._create_version(entry, "回滚前备份")
            self._versions[entry_id].append(current_version)
            
            entry.content = target_version.content.copy()
            entry.version += 1
            entry.updated_at = datetime.now()
            
            quality, quality_score = self.evaluate_knowledge_quality(entry_id)
            entry.quality = quality
            entry.quality_score = quality_score
            
            if self._storage_path:
                self._save_knowledge()
            
            self._logger.info(f"已回滚知识: {entry_id} 到版本 {version_number}")
            return entry
    
    def archive_obsolete_knowledge(
        self,
        days_threshold: int = 180
    ) -> List[str]:
        """归档过时知识
        
        Args:
            days_threshold: 天数阈值
        
        Returns:
            归档的条目ID列表
        """
        archived_ids = []
        threshold_date = datetime.now() - timedelta(days=days_threshold)
        
        with self._lock:
            for entry_id, entry in list(self._entries.items()):
                if entry.updated_at < threshold_date:
                    if entry.quality in [KnowledgeQuality.POOR, KnowledgeQuality.OBSOLETE]:
                        entry.quality = KnowledgeQuality.OBSOLETE
                        entry.metadata['archived'] = True
                        entry.metadata['archived_at'] = datetime.now().isoformat()
                        archived_ids.append(entry_id)
                        
                        self._logger.info(f"已归档知识: {entry_id}")
            
            if self._storage_path:
                self._save_knowledge()
        
        return archived_ids
    
    def get_knowledge_by_category(
        self,
        category: KnowledgeCategory,
        min_quality: Optional[KnowledgeQuality] = None
    ) -> List[KnowledgeEntry]:
        """按类别获取知识
        
        Args:
            category: 知识类别
            min_quality: 最低质量
        
        Returns:
            知识条目列表
        """
        entry_ids = self._category_index.get(category.value, set())
        entries = [self._entries[eid] for eid in entry_ids if eid in self._entries]
        
        if min_quality:
            quality_order = [
                KnowledgeQuality.OBSOLETE,
                KnowledgeQuality.POOR,
                KnowledgeQuality.AVERAGE,
                KnowledgeQuality.GOOD,
                KnowledgeQuality.EXCELLENT
            ]
            min_index = quality_order.index(min_quality)
            entries = [
                e for e in entries
                if quality_order.index(e.quality) >= min_index
            ]
        
        return sorted(entries, key=lambda e: e.quality_score, reverse=True)
    
    def search_knowledge(
        self,
        query: str,
        categories: Optional[List[KnowledgeCategory]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """搜索知识
        
        Args:
            query: 搜索查询
            categories: 类别过滤
            tags: 标签过滤
            limit: 结果数量限制
        
        Returns:
            (条目, 相关度分数) 列表
        """
        results = []
        query_lower = query.lower()
        
        for entry_id, entry in self._entries.items():
            if categories and entry.category not in categories:
                continue
            
            if tags and not any(tag in entry.tags for tag in tags):
                continue
            
            score = 0.0
            
            if query_lower in entry.title.lower():
                score += 0.5
            
            content_str = json.dumps(entry.content).lower()
            if query_lower in content_str:
                score += 0.3
            
            if query_lower in ' '.join(entry.tags).lower():
                score += 0.2
            
            if score > 0:
                results.append((entry, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:limit]
    
    def _determine_quality_level(self, score: float) -> KnowledgeQuality:
        """确定质量级别"""
        if score >= 0.9:
            return KnowledgeQuality.EXCELLENT
        elif score >= 0.75:
            return KnowledgeQuality.GOOD
        elif score >= 0.6:
            return KnowledgeQuality.AVERAGE
        elif score >= 0.4:
            return KnowledgeQuality.POOR
        else:
            return KnowledgeQuality.OBSOLETE
    
    def _calculate_content_similarity(
        self,
        data1: Dict[str, Any],
        data2: Dict[str, Any]
    ) -> float:
        """计算内容相似度"""
        text1 = f"{data1.get('title', '')} {json.dumps(data1.get('content', {}))}"
        text2 = f"{data2.get('title', '')} {json.dumps(data2.get('content', {}))}"
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _merge_contents(
        self,
        content1: Dict[str, Any],
        content2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并内容"""
        merged = content1.copy()
        
        for key, value in content2.items():
            if key in merged:
                if isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key].update(value)
                elif isinstance(merged[key], list) and isinstance(value, list):
                    merged[key] = list(set(merged[key] + value))
                else:
                    merged[key] = value
            else:
                merged[key] = value
        
        return merged
    
    def _create_version(
        self,
        entry: KnowledgeEntry,
        change_summary: str
    ) -> KnowledgeVersion:
        """创建版本"""
        version_id = f"VER-{entry.entry_id}-{entry.version}"
        
        return KnowledgeVersion(
            version_id=version_id,
            entry_id=entry.entry_id,
            version_number=entry.version,
            content=entry.content.copy(),
            created_at=datetime.now(),
            change_summary=change_summary
        )
    
    def _index_entry(self, entry: KnowledgeEntry) -> None:
        """索引条目"""
        self._category_index[entry.category.value].add(entry.entry_id)
        self._quality_index[entry.quality.value].add(entry.entry_id)
        
        for tag in entry.tags:
            self._tag_index[tag].add(entry.entry_id)
    
    def _update_indices(self, entry: KnowledgeEntry) -> None:
        """更新索引"""
        for category in KnowledgeCategory:
            self._category_index[category.value].discard(entry.entry_id)
        self._category_index[entry.category.value].add(entry.entry_id)
        
        for quality in KnowledgeQuality:
            self._quality_index[quality.value].discard(entry.entry_id)
        self._quality_index[entry.quality.value].add(entry.entry_id)
        
        for tag_set in self._tag_index.values():
            tag_set.discard(entry.entry_id)
        for tag in entry.tags:
            self._tag_index[tag].add(entry.entry_id)
    
    def _remove_entry(self, entry_id: str) -> None:
        """移除条目"""
        entry = self._entries.pop(entry_id, None)
        
        if entry:
            self._category_index[entry.category.value].discard(entry_id)
            self._quality_index[entry.quality.value].discard(entry_id)
            
            for tag in entry.tags:
                self._tag_index[tag].discard(entry_id)
    
    def _save_knowledge(self) -> None:
        """保存知识"""
        if not self._storage_path:
            return
        
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "entries": [e.to_dict() for e in self._entries.values()],
                "versions": {
                    eid: [v.to_dict() for v in versions]
                    for eid, versions in self._versions.items()
                }
            }
            
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            temp_file = self._storage_path.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            temp_file.replace(self._storage_path)
            
        except Exception as e:
            self._logger.error(f"保存知识失败: {e}")
    
    def _load_knowledge(self) -> None:
        """加载知识"""
        if not self._storage_path or not self._storage_path.exists():
            return
        
        try:
            with open(self._storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for entry_data in data.get("entries", []):
                entry = KnowledgeEntry.from_dict(entry_data)
                self._entries[entry.entry_id] = entry
                self._index_entry(entry)
            
            for entry_id, version_list in data.get("versions", {}).items():
                for version_data in version_list:
                    version = KnowledgeVersion(
                        version_id=version_data["version_id"],
                        entry_id=version_data["entry_id"],
                        version_number=version_data["version_number"],
                        content=version_data["content"],
                        created_at=datetime.fromisoformat(version_data["created_at"]),
                        change_summary=version_data["change_summary"],
                        changed_by=version_data.get("changed_by", "system")
                    )
                    self._versions[entry_id].append(version)
            
            self._logger.info(f"已加载 {len(self._entries)} 个知识条目")
            
        except Exception as e:
            self._logger.error(f"加载知识失败: {e}")
    
    def build_knowledge_graph(
        self,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """构建知识图谱
        
        Args:
            max_depth: 最大深度
        
        Returns:
            知识图谱
        """
        graph = {
            "nodes": [],
            "edges": [],
            "clusters": {}
        }
        
        for entry_id, entry in self._entries.items():
            node = {
                "id": entry_id,
                "label": entry.title,
                "category": entry.category.value,
                "quality": entry.quality.value,
                "quality_score": entry.quality_score,
                "size": min(entry.application_count / 10.0 + 1, 5)
            }
            graph["nodes"].append(node)
        
        for entry_id, entry in self._entries.items():
            for related_id in entry.related_entries:
                if related_id in self._entries:
                    edge = {
                        "source": entry_id,
                        "target": related_id,
                        "type": "related"
                    }
                    graph["edges"].append(edge)
            
            for dep_id in entry.dependencies:
                if dep_id in self._entries:
                    edge = {
                        "source": entry_id,
                        "target": dep_id,
                        "type": "dependency"
                    }
                    graph["edges"].append(edge)
        
        clusters = self._cluster_knowledge_by_tags()
        graph["clusters"] = clusters
        
        return graph
    
    def infer_knowledge_relations(
        self,
        entry_id: str
    ) -> Dict[str, Any]:
        """推理知识关系
        
        Args:
            entry_id: 条目ID
        
        Returns:
            推理结果
        """
        entry = self._entries.get(entry_id)
        if not entry:
            return {"status": "error", "message": "知识条目不存在"}
        
        inference_result = {
            "entry_id": entry_id,
            "inferred_relations": [],
            "inferred_dependencies": [],
            "similar_entries": [],
            "complementary_entries": []
        }
        
        for other_id, other_entry in self._entries.items():
            if other_id == entry_id:
                continue
            
            similarity = self._calculate_content_similarity(
                {"title": entry.title, "content": entry.content},
                {"title": other_entry.title, "content": other_entry.content}
            )
            
            if similarity > 0.7:
                inference_result["similar_entries"].append({
                    "entry_id": other_id,
                    "title": other_entry.title,
                    "similarity": similarity
                })
            
            tag_overlap = len(set(entry.tags) & set(other_entry.tags)) / max(len(entry.tags), len(other_entry.tags), 1)
            
            if tag_overlap > 0.5 and similarity < 0.5:
                inference_result["complementary_entries"].append({
                    "entry_id": other_id,
                    "title": other_entry.title,
                    "tag_overlap": tag_overlap
                })
        
        if entry.category == KnowledgeCategory.PRACTICE:
            for other_id, other_entry in self._entries.items():
                if other_entry.category == KnowledgeCategory.PATTERN:
                    if self._practice_derived_from_pattern(entry, other_entry):
                        inference_result["inferred_relations"].append({
                            "entry_id": other_id,
                            "title": other_entry.title,
                            "relation_type": "derived_from"
                        })
        
        for other_id, other_entry in self._entries.items():
            if other_id == entry_id:
                continue
            
            if self._has_dependency_keywords(entry, other_entry):
                inference_result["inferred_dependencies"].append({
                    "entry_id": other_id,
                    "title": other_entry.title,
                    "dependency_type": "prerequisite"
                })
        
        for key in ["similar_entries", "complementary_entries", "inferred_relations", "inferred_dependencies"]:
            inference_result[key] = inference_result[key][:5]
        
        return inference_result
    
    def improve_deduplication(
        self,
        knowledge_data: Dict[str, Any],
        use_semantic_similarity: bool = True
    ) -> Tuple[bool, Optional[str], float]:
        """改进的去重算法
        
        Args:
            knowledge_data: 知识数据
            use_semantic_similarity: 是否使用语义相似度
        
        Returns:
            (是否重复, 重复条目ID, 相似度分数)
        """
        title = knowledge_data.get('title', '')
        content = knowledge_data.get('content', {})
        
        title_hash = hashlib.md5(title.encode()).hexdigest()
        
        for entry_id, entry in self._entries.items():
            entry_title_hash = hashlib.md5(entry.title.encode()).hexdigest()
            
            if title_hash == entry_title_hash:
                return True, entry_id, 1.0
        
        content_str = json.dumps(content, sort_keys=True)
        content_hash = hashlib.md5(content_str.encode()).hexdigest()
        
        for entry_id, entry in self._entries.items():
            entry_content_str = json.dumps(entry.content, sort_keys=True)
            entry_content_hash = hashlib.md5(entry_content_str.encode()).hexdigest()
            
            if content_hash == entry_content_hash:
                return True, entry_id, 1.0
        
        if use_semantic_similarity:
            max_similarity = 0.0
            max_similarity_entry_id = None
            
            for entry_id, entry in self._entries.items():
                similarity = self._calculate_semantic_similarity(
                    knowledge_data,
                    {"title": entry.title, "content": entry.content, "tags": entry.tags}
                )
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    max_similarity_entry_id = entry_id
            
            if max_similarity >= 0.85:
                return True, max_similarity_entry_id, max_similarity
        
        return False, None, 0.0
    
    def manage_knowledge_lifecycle(
        self,
        lifecycle_policy: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """管理知识生命周期
        
        Args:
            lifecycle_policy: 生命周期策略
        
        Returns:
            生命周期管理结果
        """
        if not lifecycle_policy:
            lifecycle_policy = {
                "archive_after_days": 180,
                "remove_after_days": 365,
                "min_quality_for_archive": KnowledgeQuality.POOR,
                "min_applications_for_keep": 2
            }
        
        result = {
            "archived": [],
            "removed": [],
            "kept": [],
            "promoted": []
        }
        
        now = datetime.now()
        archive_threshold = now - timedelta(days=lifecycle_policy["archive_after_days"])
        remove_threshold = now - timedelta(days=lifecycle_policy["remove_after_days"])
        
        for entry_id, entry in list(self._entries.items()):
            age_days = (now - entry.updated_at).days
            
            if entry.updated_at < remove_threshold:
                if entry.quality == KnowledgeQuality.OBSOLETE and entry.application_count < lifecycle_policy["min_applications_for_keep"]:
                    self._remove_entry(entry_id)
                    result["removed"].append({
                        "entry_id": entry_id,
                        "title": entry.title,
                        "reason": "过时且未使用"
                    })
                    continue
            
            if entry.updated_at < archive_threshold:
                if entry.quality in [KnowledgeQuality.POOR, KnowledgeQuality.OBSOLETE]:
                    entry.quality = KnowledgeQuality.OBSOLETE
                    entry.metadata['archived'] = True
                    entry.metadata['archived_at'] = now.isoformat()
                    result["archived"].append({
                        "entry_id": entry_id,
                        "title": entry.title,
                        "reason": "质量低且长期未更新"
                    })
                    continue
            
            if entry.quality == KnowledgeQuality.GOOD and entry.application_count > 10 and entry.success_rate > 0.9:
                entry.quality = KnowledgeQuality.EXCELLENT
                result["promoted"].append({
                    "entry_id": entry_id,
                    "title": entry.title,
                    "new_quality": "excellent"
                })
            
            result["kept"].append({
                "entry_id": entry_id,
                "title": entry.title,
                "quality": entry.quality.value
            })
        
        if self._storage_path:
            self._save_knowledge()
        
        return result
    
    def _cluster_knowledge_by_tags(self) -> Dict[str, List[str]]:
        """按标签聚类知识"""
        clusters = defaultdict(list)
        
        for entry_id, entry in self._entries.items():
            for tag in entry.tags:
                clusters[tag].append(entry_id)
        
        return dict(clusters)
    
    def _practice_derived_from_pattern(
        self,
        practice: KnowledgeEntry,
        pattern: KnowledgeEntry
    ) -> bool:
        """判断实践是否来自模式"""
        if 'source_patterns' in practice.content:
            if pattern.entry_id in practice.content['source_patterns']:
                return True
        
        tag_overlap = len(set(practice.tags) & set(pattern.tags)) / max(len(practice.tags), len(pattern.tags), 1)
        
        return tag_overlap > 0.6
    
    def _has_dependency_keywords(
        self,
        entry1: KnowledgeEntry,
        entry2: KnowledgeEntry
    ) -> bool:
        """判断是否存在依赖关键词"""
        dependency_keywords = ['需要', 'require', '依赖', 'depend', '前提', 'prerequisite']
        
        text1 = f"{entry1.title} {json.dumps(entry1.content)}".lower()
        text2 = f"{entry2.title} {json.dumps(entry2.content)}".lower()
        
        for keyword in dependency_keywords:
            if keyword in text1 and entry2.title.lower() in text1:
                return True
        
        return False
    
    def _calculate_semantic_similarity(
        self,
        data1: Dict[str, Any],
        data2: Dict[str, Any]
    ) -> float:
        """计算语义相似度"""
        title1 = data1.get('title', '')
        title2 = data2.get('title', '')
        
        title_sim = self._calculate_text_similarity(title1, title2)
        
        content1 = json.dumps(data1.get('content', {}))
        content2 = json.dumps(data2.get('content', {}))
        
        content_sim = self._calculate_text_similarity(content1, content2)
        
        tags1 = set(data1.get('tags', []))
        tags2 = set(data2.get('tags', []))
        
        tag_sim = 0.0
        if tags1 and tags2:
            tag_sim = len(tags1 & tags2) / len(tags1 | tags2)
        
        semantic_sim = title_sim * 0.4 + content_sim * 0.4 + tag_sim * 0.2
        
        return semantic_sim
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_entries": len(self._entries),
            "by_category": {},
            "by_quality": {},
            "total_versions": sum(len(v) for v in self._versions.values()),
            "avg_quality_score": 0.0,
            "avg_application_count": 0.0,
            "avg_success_rate": 0.0
        }
        
        for category in KnowledgeCategory:
            count = len(self._category_index.get(category.value, set()))
            stats["by_category"][category.value] = count
        
        for quality in KnowledgeQuality:
            count = len(self._quality_index.get(quality.value, set()))
            stats["by_quality"][quality.value] = count
        
        if self._entries:
            stats["avg_quality_score"] = sum(
                e.quality_score for e in self._entries.values()
            ) / len(self._entries)
            
            stats["avg_application_count"] = sum(
                e.application_count for e in self._entries.values()
            ) / len(self._entries)
            
            stats["avg_success_rate"] = sum(
                e.success_rate for e in self._entries.values()
            ) / len(self._entries)
        
        return stats
