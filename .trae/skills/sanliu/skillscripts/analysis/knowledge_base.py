#!/usr/bin/env python3
"""
知识库模块 - Sanliu 技能

功能：
1. KnowledgeBase 类：知识库主类
2. 知识存储（支持JSON、SQLite等多种存储后端）
3. 知识检索（关键词搜索、语义搜索、分类检索）
4. 知识更新（增量更新、版本控制）
5. 知识导入导出

增强功能：
6. CrossProjectKnowledgeManager：跨项目知识管理器
   - 项目知识注册和隔离
   - 知识共享池（SharedKnowledgePool）
   - 知识权限控制（公开、私有、共享）

7. KnowledgeSynchronizer：知识同步器
   - 增量同步（只同步变更）
   - 冲突检测和解决
   - 同步状态追踪

8. KnowledgeIndexManager：知识索引管理器
   - 全文索引
   - 标签索引
   - 语义索引接口（预留）

9. KnowledgeUpdateManager：知识更新管理器
   - 批量更新
   - 更新验证
   - 更新回滚

知识类型：
- 修复模式知识 (fix_pattern)
- 最佳实践知识 (best_practice)
- 问题诊断知识 (diagnosis)
- 代码模式知识 (code_pattern)

使用示例：
    from knowledge_base import KnowledgeBase, CrossProjectKnowledgeManager
    
    # 基础使用
    kb = KnowledgeBase(storage_type='sqlite')
    kb.add_knowledge(knowledge_item)
    results = kb.search('关键词')
    kb.export_knowledge('output.json')
    
    # 跨项目管理
    manager = CrossProjectKnowledgeManager()
    manager.initialize()
    manager.register_project('proj1', '项目1', '/path/to/proj1')
    manager.share_knowledge('kb-001', 'proj1', ['proj2'])
"""

import hashlib
import json
import logging
import os
import re
import shutil
import sqlite3
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    FIX_PATTERN = "fix_pattern"
    BEST_PRACTICE = "best_practice"
    DIAGNOSIS = "diagnosis"
    CODE_PATTERN = "code_pattern"


class KnowledgeStatus(Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DRAFT = "draft"
    ARCHIVED = "archived"


class StorageType(Enum):
    JSON = "json"
    SQLITE = "sqlite"
    MEMORY = "memory"


class SearchMode(Enum):
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    CATEGORY = "category"
    HYBRID = "hybrid"


@dataclass
class KnowledgeItem:
    knowledge_id: str
    knowledge_type: KnowledgeType
    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    category: str = ""
    subcategory: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    version: int = 1
    status: KnowledgeStatus = KnowledgeStatus.ACTIVE
    confidence_score: float = 0.0
    usage_count: int = 0
    success_rate: float = 0.0
    source: str = ""
    related_ids: List[str] = field(default_factory=list)
    examples: List[Dict[str, str]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if isinstance(self.knowledge_type, str):
            self.knowledge_type = KnowledgeType(self.knowledge_type)
        if isinstance(self.status, str):
            self.status = KnowledgeStatus(self.status)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['knowledge_type'] = self.knowledge_type.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeItem":
        if isinstance(data.get('knowledge_type'), str):
            data['knowledge_type'] = KnowledgeType(data['knowledge_type'])
        if isinstance(data.get('status'), str):
            data['status'] = KnowledgeStatus(data['status'])
        return cls(**data)
    
    def generate_id(self) -> str:
        content_hash = hashlib.md5(f"{self.title}:{self.content}".encode()).hexdigest()[:8]
        return f"KB-{self.knowledge_type.value[:3].upper()}-{content_hash}"


@dataclass
class KnowledgeVersion:
    version_id: str
    knowledge_id: str
    version_number: int
    content_snapshot: Dict[str, Any]
    changes: List[str]
    created_at: str
    created_by: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SearchResult:
    item: KnowledgeItem
    score: float
    matched_fields: List[str]
    highlights: Dict[str, List[str]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "item": self.item.to_dict(),
            "score": self.score,
            "matched_fields": self.matched_fields,
            "highlights": self.highlights
        }


class StorageBackend(ABC):
    @abstractmethod
    def initialize(self) -> None:
        pass
    
    @abstractmethod
    def save(self, item: KnowledgeItem) -> None:
        pass
    
    @abstractmethod
    def load(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        pass
    
    @abstractmethod
    def delete(self, knowledge_id: str) -> bool:
        pass
    
    @abstractmethod
    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[KnowledgeItem]:
        pass
    
    @abstractmethod
    def search(self, query: str, fields: List[str]) -> List[Tuple[KnowledgeItem, float]]:
        pass
    
    @abstractmethod
    def clear(self) -> None:
        pass
    
    @abstractmethod
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        pass


class JSONStorageBackend(StorageBackend):
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.data_file = storage_path / "knowledge_base.json"
        self.index_file = storage_path / "knowledge_index.json"
        self._data: Dict[str, Dict[str, Any]] = {}
        self._index: Dict[str, List[str]] = defaultdict(list)
    
    def initialize(self) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._load_data()
    
    def _load_data(self) -> None:
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                logger.info(f"加载知识库数据: {len(self._data)} 条记录")
            except Exception as e:
                logger.error(f"加载知识库数据失败: {e}")
                self._data = {}
        
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self._index = defaultdict(list, json.load(f))
            except Exception as e:
                logger.warning(f"加载索引失败: {e}")
                self._index = defaultdict(list)
    
    def _save_data(self) -> None:
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self._index), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存知识库数据失败: {e}")
    
    def _build_index(self, item: KnowledgeItem) -> None:
        words = set()
        for tag in item.tags:
            words.add(tag.lower())
        
        words.update(re.findall(r'\w+', item.title.lower()))
        words.update(re.findall(r'\w+', item.content.lower()[:500]))
        
        for word in words:
            if len(word) > 1:
                self._index[word].append(item.knowledge_id)
    
    def _remove_from_index(self, knowledge_id: str) -> None:
        for word in list(self._index.keys()):
            if knowledge_id in self._index[word]:
                self._index[word].remove(knowledge_id)
            if not self._index[word]:
                del self._index[word]
    
    def save(self, item: KnowledgeItem) -> None:
        self._data[item.knowledge_id] = item.to_dict()
        self._remove_from_index(item.knowledge_id)
        self._build_index(item)
        self._save_data()
    
    def load(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        data = self._data.get(knowledge_id)
        if data:
            return KnowledgeItem.from_dict(data)
        return None
    
    def delete(self, knowledge_id: str) -> bool:
        if knowledge_id in self._data:
            del self._data[knowledge_id]
            self._remove_from_index(knowledge_id)
            self._save_data()
            return True
        return False
    
    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[KnowledgeItem]:
        items = [KnowledgeItem.from_dict(d) for d in self._data.values()]
        
        if filters:
            items = self._apply_filters(items, filters)
        
        return items
    
    def _apply_filters(self, items: List[KnowledgeItem], filters: Dict[str, Any]) -> List[KnowledgeItem]:
        filtered = items
        
        if 'knowledge_type' in filters:
            kt = filters['knowledge_type']
            if isinstance(kt, KnowledgeType):
                kt = kt.value
            filtered = [i for i in filtered if i.knowledge_type.value == kt]
        
        if 'status' in filters:
            st = filters['status']
            if isinstance(st, KnowledgeStatus):
                st = st.value
            filtered = [i for i in filtered if i.status.value == st]
        
        if 'category' in filters:
            filtered = [i for i in filtered if i.category == filters['category']]
        
        if 'tags' in filters:
            filter_tags = set(filters['tags'])
            filtered = [i for i in filtered if filter_tags & set(i.tags)]
        
        if 'min_confidence' in filters:
            filtered = [i for i in filtered if i.confidence_score >= filters['min_confidence']]
        
        return filtered
    
    def search(self, query: str, fields: List[str]) -> List[Tuple[KnowledgeItem, float]]:
        results = []
        query_words = set(re.findall(r'\w+', query.lower()))
        
        candidate_ids = set()
        for word in query_words:
            if word in self._index:
                candidate_ids.update(self._index[word])
        
        for kid in candidate_ids:
            item = self.load(kid)
            if not item:
                continue
            
            score = 0.0
            for field in fields:
                field_value = getattr(item, field, "")
                if isinstance(field_value, str):
                    field_words = set(re.findall(r'\w+', field_value.lower()))
                    overlap = query_words & field_words
                    if overlap:
                        field_score = len(overlap) / len(query_words) if query_words else 0
                        score += field_score
            
            if score > 0:
                results.append((item, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def clear(self) -> None:
        self._data = {}
        self._index = defaultdict(list)
        self._save_data()
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return len(self.list_all(filters))


class SQLiteStorageBackend(StorageBackend):
    def __init__(self, storage_path: Path, db_name: str = "knowledge_base.db"):
        self.storage_path = storage_path
        self.db_path = storage_path / db_name
        self._conn: Optional[sqlite3.Connection] = None
    
    def initialize(self) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self) -> None:
        cursor = self._conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_items (
                knowledge_id TEXT PRIMARY KEY,
                knowledge_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                tags TEXT,
                category TEXT,
                subcategory TEXT,
                metadata TEXT,
                created_at TEXT,
                updated_at TEXT,
                version INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active',
                confidence_score REAL DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0,
                source TEXT,
                related_ids TEXT,
                examples TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_versions (
                version_id TEXT PRIMARY KEY,
                knowledge_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                content_snapshot TEXT,
                changes TEXT,
                created_at TEXT,
                created_by TEXT,
                FOREIGN KEY (knowledge_id) REFERENCES knowledge_items(knowledge_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (knowledge_id) REFERENCES knowledge_items(knowledge_id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_items(knowledge_type)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON knowledge_items(category)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status ON knowledge_items(status)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tags ON knowledge_tags(tag)
        ''')
        
        self._conn.commit()
    
    def save(self, item: KnowledgeItem) -> None:
        cursor = self._conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO knowledge_items (
                knowledge_id, knowledge_type, title, content, tags, category,
                subcategory, metadata, created_at, updated_at, version, status,
                confidence_score, usage_count, success_rate, source, related_ids, examples
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item.knowledge_id,
            item.knowledge_type.value,
            item.title,
            item.content,
            json.dumps(item.tags, ensure_ascii=False),
            item.category,
            item.subcategory,
            json.dumps(item.metadata, ensure_ascii=False),
            item.created_at,
            item.updated_at,
            item.version,
            item.status.value,
            item.confidence_score,
            item.usage_count,
            item.success_rate,
            item.source,
            json.dumps(item.related_ids, ensure_ascii=False),
            json.dumps(item.examples, ensure_ascii=False)
        ))
        
        cursor.execute('DELETE FROM knowledge_tags WHERE knowledge_id = ?', (item.knowledge_id,))
        for tag in item.tags:
            cursor.execute('INSERT INTO knowledge_tags (knowledge_id, tag) VALUES (?, ?)',
                          (item.knowledge_id, tag))
        
        self._conn.commit()
    
    def load(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        cursor = self._conn.cursor()
        cursor.execute('SELECT * FROM knowledge_items WHERE knowledge_id = ?', (knowledge_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_item(row)
        return None
    
    def _row_to_item(self, row: sqlite3.Row) -> KnowledgeItem:
        return KnowledgeItem(
            knowledge_id=row['knowledge_id'],
            knowledge_type=KnowledgeType(row['knowledge_type']),
            title=row['title'],
            content=row['content'] or "",
            tags=json.loads(row['tags']) if row['tags'] else [],
            category=row['category'] or "",
            subcategory=row['subcategory'] or "",
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            created_at=row['created_at'] or "",
            updated_at=row['updated_at'] or "",
            version=row['version'] or 1,
            status=KnowledgeStatus(row['status']) if row['status'] else KnowledgeStatus.ACTIVE,
            confidence_score=row['confidence_score'] or 0,
            usage_count=row['usage_count'] or 0,
            success_rate=row['success_rate'] or 0,
            source=row['source'] or "",
            related_ids=json.loads(row['related_ids']) if row['related_ids'] else [],
            examples=json.loads(row['examples']) if row['examples'] else []
        )
    
    def delete(self, knowledge_id: str) -> bool:
        cursor = self._conn.cursor()
        cursor.execute('DELETE FROM knowledge_tags WHERE knowledge_id = ?', (knowledge_id,))
        cursor.execute('DELETE FROM knowledge_versions WHERE knowledge_id = ?', (knowledge_id,))
        cursor.execute('DELETE FROM knowledge_items WHERE knowledge_id = ?', (knowledge_id,))
        self._conn.commit()
        return cursor.rowcount > 0
    
    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[KnowledgeItem]:
        cursor = self._conn.cursor()
        
        query = 'SELECT * FROM knowledge_items WHERE 1=1'
        params = []
        
        if filters:
            if 'knowledge_type' in filters:
                kt = filters['knowledge_type']
                if isinstance(kt, KnowledgeType):
                    kt = kt.value
                query += ' AND knowledge_type = ?'
                params.append(kt)
            
            if 'status' in filters:
                st = filters['status']
                if isinstance(st, KnowledgeStatus):
                    st = st.value
                query += ' AND status = ?'
                params.append(st)
            
            if 'category' in filters:
                query += ' AND category = ?'
                params.append(filters['category'])
            
            if 'min_confidence' in filters:
                query += ' AND confidence_score >= ?'
                params.append(filters['min_confidence'])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        items = [self._row_to_item(row) for row in rows]
        
        if filters and 'tags' in filters:
            filter_tags = set(filters['tags'])
            items = [i for i in items if filter_tags & set(i.tags)]
        
        return items
    
    def search(self, query: str, fields: List[str]) -> List[Tuple[KnowledgeItem, float]]:
        cursor = self._conn.cursor()
        
        search_conditions = []
        params = []
        query_lower = f"%{query.lower()}%"
        
        if 'title' in fields:
            search_conditions.append('LOWER(title) LIKE ?')
            params.append(query_lower)
        
        if 'content' in fields:
            search_conditions.append('LOWER(content) LIKE ?')
            params.append(query_lower)
        
        if 'tags' in fields:
            search_conditions.append('LOWER(tags) LIKE ?')
            params.append(query_lower)
        
        if not search_conditions:
            return []
        
        sql = f"SELECT * FROM knowledge_items WHERE {' OR '.join(search_conditions)}"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            item = self._row_to_item(row)
            score = self._calculate_search_score(item, query, fields)
            results.append((item, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def _calculate_search_score(self, item: KnowledgeItem, query: str, fields: List[str]) -> float:
        score = 0.0
        query_lower = query.lower()
        
        if 'title' in fields and query_lower in item.title.lower():
            score += 0.5
        
        if 'content' in fields and query_lower in item.content.lower():
            score += 0.3
        
        if 'tags' in fields:
            for tag in item.tags:
                if query_lower in tag.lower():
                    score += 0.2
                    break
        
        return min(score, 1.0)
    
    def clear(self) -> None:
        cursor = self._conn.cursor()
        cursor.execute('DELETE FROM knowledge_tags')
        cursor.execute('DELETE FROM knowledge_versions')
        cursor.execute('DELETE FROM knowledge_items')
        self._conn.commit()
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return len(self.list_all(filters))
    
    def save_version(self, version: KnowledgeVersion) -> None:
        cursor = self._conn.cursor()
        cursor.execute('''
            INSERT INTO knowledge_versions (
                version_id, knowledge_id, version_number, content_snapshot,
                changes, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            version.version_id,
            version.knowledge_id,
            version.version_number,
            json.dumps(version.content_snapshot, ensure_ascii=False),
            json.dumps(version.changes, ensure_ascii=False),
            version.created_at,
            version.created_by
        ))
        self._conn.commit()
    
    def get_versions(self, knowledge_id: str) -> List[KnowledgeVersion]:
        cursor = self._conn.cursor()
        cursor.execute('''
            SELECT * FROM knowledge_versions 
            WHERE knowledge_id = ? 
            ORDER BY version_number DESC
        ''', (knowledge_id,))
        rows = cursor.fetchall()
        
        versions = []
        for row in rows:
            versions.append(KnowledgeVersion(
                version_id=row['version_id'],
                knowledge_id=row['knowledge_id'],
                version_number=row['version_number'],
                content_snapshot=json.loads(row['content_snapshot']) if row['content_snapshot'] else {},
                changes=json.loads(row['changes']) if row['changes'] else [],
                created_at=row['created_at'],
                created_by=row['created_by']
            ))
        
        return versions


class MemoryStorageBackend(StorageBackend):
    def __init__(self):
        self._data: Dict[str, KnowledgeItem] = {}
        self._index: Dict[str, List[str]] = defaultdict(list)
    
    def initialize(self) -> None:
        pass
    
    def save(self, item: KnowledgeItem) -> None:
        self._data[item.knowledge_id] = item
        self._update_index(item)
    
    def _update_index(self, item: KnowledgeItem) -> None:
        words = set()
        for tag in item.tags:
            words.add(tag.lower())
        words.update(re.findall(r'\w+', item.title.lower()))
        words.update(re.findall(r'\w+', item.content.lower()[:500]))
        
        for word in words:
            if len(word) > 1:
                if item.knowledge_id not in self._index[word]:
                    self._index[word].append(item.knowledge_id)
    
    def load(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        return self._data.get(knowledge_id)
    
    def delete(self, knowledge_id: str) -> bool:
        if knowledge_id in self._data:
            del self._data[knowledge_id]
            return True
        return False
    
    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[KnowledgeItem]:
        items = list(self._data.values())
        
        if filters:
            if 'knowledge_type' in filters:
                kt = filters['knowledge_type']
                if isinstance(kt, KnowledgeType):
                    kt = kt.value
                items = [i for i in items if i.knowledge_type.value == kt]
            
            if 'status' in filters:
                st = filters['status']
                if isinstance(st, KnowledgeStatus):
                    st = st.value
                items = [i for i in items if i.status.value == st]
            
            if 'category' in filters:
                items = [i for i in items if i.category == filters['category']]
        
        return items
    
    def search(self, query: str, fields: List[str]) -> List[Tuple[KnowledgeItem, float]]:
        results = []
        query_words = set(re.findall(r'\w+', query.lower()))
        
        candidate_ids = set()
        for word in query_words:
            if word in self._index:
                candidate_ids.update(self._index[word])
        
        for kid in candidate_ids:
            item = self._data.get(kid)
            if not item:
                continue
            
            score = 0.0
            for field in fields:
                field_value = getattr(item, field, "")
                if isinstance(field_value, str):
                    field_words = set(re.findall(r'\w+', field_value.lower()))
                    overlap = query_words & field_words
                    if overlap:
                        field_score = len(overlap) / len(query_words) if query_words else 0
                        score += field_score
            
            if score > 0:
                results.append((item, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def clear(self) -> None:
        self._data = {}
        self._index = defaultdict(list)
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return len(self.list_all(filters))


class KnowledgeBase:
    """知识库主类
    
    提供知识的存储、检索、更新和导入导出功能。
    
    功能特性：
    - 多种存储后端支持（JSON、SQLite、内存）
    - 多种检索模式（关键词、语义、分类、混合）
    - 增量更新和版本控制
    - 知识导入导出
    - 知识统计和分析
    
    使用示例：
        kb = KnowledgeBase(storage_type='sqlite')
        
        # 添加知识
        item = KnowledgeItem(
            knowledge_id="KB-FIX-001",
            knowledge_type=KnowledgeType.FIX_PATTERN,
            title="空指针修复模式",
            content="检查None值..."
        )
        kb.add_knowledge(item)
        
        # 搜索知识
        results = kb.search("空指针", mode=SearchMode.KEYWORD)
        
        # 导出知识
        kb.export_knowledge("knowledge_export.json")
    """
    
    DEFAULT_CATEGORIES = {
        KnowledgeType.FIX_PATTERN: ["null_pointer", "type_error", "index_error", "logic_error", "performance"],
        KnowledgeType.BEST_PRACTICE: ["coding_style", "security", "performance", "testing", "documentation"],
        KnowledgeType.DIAGNOSIS: ["runtime_error", "compile_error", "logic_error", "performance_issue"],
        KnowledgeType.CODE_PATTERN: ["design_pattern", "architectural_pattern", "idiom", "anti_pattern"]
    }
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        storage_type: Union[StorageType, str] = StorageType.JSON,
        auto_initialize: bool = True
    ):
        if isinstance(storage_type, str):
            storage_type = StorageType(storage_type)
        
        self.storage_type = storage_type
        self.storage_path = storage_path or Path("./knowledge_base_data")
        
        self._backend: Optional[StorageBackend] = None
        self._version_history: Dict[str, List[KnowledgeVersion]] = defaultdict(list)
        
        if auto_initialize:
            self.initialize()
    
    def initialize(self) -> None:
        if self.storage_type == StorageType.JSON:
            self._backend = JSONStorageBackend(self.storage_path)
        elif self.storage_type == StorageType.SQLITE:
            self._backend = SQLiteStorageBackend(self.storage_path)
        else:
            self._backend = MemoryStorageBackend()
        
        self._backend.initialize()
        logger.info(f"知识库初始化完成: {self.storage_type.value}")
    
    def add_knowledge(
        self,
        item: KnowledgeItem,
        auto_id: bool = True
    ) -> str:
        if not self._backend:
            raise RuntimeError("知识库未初始化")
        
        if auto_id and not item.knowledge_id:
            item.knowledge_id = item.generate_id()
        
        self._backend.save(item)
        
        self._record_version(item, ["初始创建"])
        
        logger.info(f"添加知识: {item.knowledge_id} - {item.title}")
        return item.knowledge_id
    
    def add_knowledge_batch(self, items: List[KnowledgeItem]) -> List[str]:
        ids = []
        for item in items:
            kid = self.add_knowledge(item)
            ids.append(kid)
        return ids
    
    def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        if not self._backend:
            return None
        return self._backend.load(knowledge_id)
    
    def update_knowledge(
        self,
        knowledge_id: str,
        updates: Dict[str, Any],
        record_version: bool = True
    ) -> Optional[KnowledgeItem]:
        if not self._backend:
            return None
        
        item = self._backend.load(knowledge_id)
        if not item:
            return None
        
        changes = []
        for key, value in updates.items():
            if hasattr(item, key):
                old_value = getattr(item, key)
                if old_value != value:
                    changes.append(f"{key}: {old_value} -> {value}")
                    setattr(item, key, value)
        
        if changes:
            item.updated_at = datetime.now().isoformat()
            item.version += 1
            
            self._backend.save(item)
            
            if record_version:
                self._record_version(item, changes)
            
            logger.info(f"更新知识: {knowledge_id} - {len(changes)} 个变更")
        
        return item
    
    def delete_knowledge(self, knowledge_id: str) -> bool:
        if not self._backend:
            return False
        
        result = self._backend.delete(knowledge_id)
        if result:
            logger.info(f"删除知识: {knowledge_id}")
        return result
    
    def search(
        self,
        query: str,
        mode: Union[SearchMode, str] = SearchMode.KEYWORD,
        fields: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50
    ) -> List[SearchResult]:
        if not self._backend:
            return []
        
        if isinstance(mode, str):
            mode = SearchMode(mode)
        
        fields = fields or ['title', 'content', 'tags']
        
        if mode == SearchMode.KEYWORD:
            raw_results = self._backend.search(query, fields)
        elif mode == SearchMode.CATEGORY:
            raw_results = self._search_by_category(query, filters)
        elif mode == SearchMode.HYBRID:
            raw_results = self._hybrid_search(query, fields, filters)
        else:
            raw_results = self._backend.search(query, fields)
        
        results = []
        for item, score in raw_results[:limit]:
            matched_fields = self._get_matched_fields(item, query, fields)
            highlights = self._generate_highlights(item, query, fields)
            
            results.append(SearchResult(
                item=item,
                score=score,
                matched_fields=matched_fields,
                highlights=highlights
            ))
        
        return results
    
    def _search_by_category(
        self,
        category: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[KnowledgeItem, float]]:
        if not filters:
            filters = {}
        
        filters['category'] = category
        items = self._backend.list_all(filters)
        return [(item, 1.0) for item in items]
    
    def _hybrid_search(
        self,
        query: str,
        fields: List[str],
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[KnowledgeItem, float]]:
        keyword_results = self._backend.search(query, fields)
        
        if filters:
            filtered_items = self._backend.list_all(filters)
            filtered_ids = {item.knowledge_id for item in filtered_items}
            keyword_results = [(item, score) for item, score in keyword_results
                              if item.knowledge_id in filtered_ids]
        
        return keyword_results
    
    def _get_matched_fields(self, item: KnowledgeItem, query: str, fields: List[str]) -> List[str]:
        matched = []
        query_lower = query.lower()
        
        for field in fields:
            value = getattr(item, field, "")
            if isinstance(value, str) and query_lower in value.lower():
                matched.append(field)
            elif isinstance(value, list):
                for v in value:
                    if isinstance(v, str) and query_lower in v.lower():
                        matched.append(field)
                        break
        
        return matched
    
    def _generate_highlights(
        self,
        item: KnowledgeItem,
        query: str,
        fields: List[str]
    ) -> Dict[str, List[str]]:
        highlights = {}
        query_lower = query.lower()
        
        for field in fields:
            value = getattr(item, field, "")
            if isinstance(value, str) and query_lower in value.lower():
                highlights[field] = self._extract_highlights(value, query_lower)
        
        return highlights
    
    def _extract_highlights(self, text: str, query: str, context_chars: int = 50) -> List[str]:
        highlights = []
        text_lower = text.lower()
        start = 0
        
        while True:
            pos = text_lower.find(query, start)
            if pos == -1:
                break
            
            highlight_start = max(0, pos - context_chars)
            highlight_end = min(len(text), pos + len(query) + context_chars)
            
            highlight = text[highlight_start:highlight_end]
            if highlight_start > 0:
                highlight = "..." + highlight
            if highlight_end < len(text):
                highlight = highlight + "..."
            
            highlights.append(highlight)
            start = pos + len(query)
        
        return highlights
    
    def list_knowledge(
        self,
        knowledge_type: Optional[Union[KnowledgeType, str]] = None,
        category: Optional[str] = None,
        status: Optional[Union[KnowledgeStatus, str]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[KnowledgeItem]:
        if not self._backend:
            return []
        
        filters = {}
        
        if knowledge_type:
            if isinstance(knowledge_type, KnowledgeType):
                knowledge_type = knowledge_type.value
            filters['knowledge_type'] = knowledge_type
        
        if category:
            filters['category'] = category
        
        if status:
            if isinstance(status, KnowledgeStatus):
                status = status.value
            filters['status'] = status
        
        if tags:
            filters['tags'] = tags
        
        items = self._backend.list_all(filters)
        return items[:limit]
    
    def _record_version(self, item: KnowledgeItem, changes: List[str]) -> None:
        version_id = f"VER-{item.knowledge_id}-{item.version}"
        
        version = KnowledgeVersion(
            version_id=version_id,
            knowledge_id=item.knowledge_id,
            version_number=item.version,
            content_snapshot=item.to_dict(),
            changes=changes,
            created_at=datetime.now().isoformat()
        )
        
        self._version_history[item.knowledge_id].append(version)
        
        if self.storage_type == StorageType.SQLITE and isinstance(self._backend, SQLiteStorageBackend):
            self._backend.save_version(version)
    
    def get_version_history(self, knowledge_id: str) -> List[KnowledgeVersion]:
        if knowledge_id in self._version_history:
            return self._version_history[knowledge_id]
        
        if self.storage_type == StorageType.SQLITE and isinstance(self._backend, SQLiteStorageBackend):
            return self._backend.get_versions(knowledge_id)
        
        return []
    
    def rollback_version(self, knowledge_id: str, target_version: int) -> Optional[KnowledgeItem]:
        versions = self.get_version_history(knowledge_id)
        
        target = None
        for v in versions:
            if v.version_number == target_version:
                target = v
                break
        
        if not target:
            return None
        
        item = KnowledgeItem.from_dict(target.content_snapshot)
        item.version = target.version_number
        item.updated_at = datetime.now().isoformat()
        
        self._backend.save(item)
        self._record_version(item, [f"回滚到版本 {target_version}"])
        
        logger.info(f"回滚知识: {knowledge_id} 到版本 {target_version}")
        return item
    
    def export_knowledge(
        self,
        output_path: str,
        format: str = "json",
        filters: Optional[Dict[str, Any]] = None
    ) -> None:
        items = self._backend.list_all(filters)
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total_count": len(items),
            "storage_type": self.storage_type.value,
            "items": [item.to_dict() for item in items]
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
        
        logger.info(f"导出知识库: {len(items)} 条记录 -> {output_path}")
    
    def import_knowledge(
        self,
        input_path: str,
        merge_strategy: str = "skip"
    ) -> Dict[str, Any]:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        items_data = data.get('items', [])
        
        stats = {
            "total": len(items_data),
            "imported": 0,
            "skipped": 0,
            "updated": 0,
            "errors": []
        }
        
        for item_data in items_data:
            try:
                item = KnowledgeItem.from_dict(item_data)
                
                existing = self._backend.load(item.knowledge_id)
                
                if existing:
                    if merge_strategy == "skip":
                        stats["skipped"] += 1
                        continue
                    elif merge_strategy == "update":
                        self.update_knowledge(item.knowledge_id, item.to_dict())
                        stats["updated"] += 1
                    elif merge_strategy == "overwrite":
                        self._backend.save(item)
                        stats["imported"] += 1
                else:
                    self._backend.save(item)
                    stats["imported"] += 1
            
            except Exception as e:
                stats["errors"].append(f"导入失败: {item_data.get('knowledge_id', 'unknown')} - {str(e)}")
        
        logger.info(f"导入知识库: 导入 {stats['imported']}, 更新 {stats['updated']}, 跳过 {stats['skipped']}")
        return stats
    
    def record_usage(self, knowledge_id: str, success: bool = True) -> None:
        item = self._backend.load(knowledge_id)
        if not item:
            return
        
        item.usage_count += 1
        
        if success:
            current_successes = item.success_rate * (item.usage_count - 1)
            item.success_rate = (current_successes + 1) / item.usage_count
        else:
            current_successes = item.success_rate * (item.usage_count - 1)
            item.success_rate = current_successes / item.usage_count
        
        self._backend.save(item)
    
    def get_statistics(self) -> Dict[str, Any]:
        if not self._backend:
            return {}
        
        all_items = self._backend.list_all()
        
        type_counts: Dict[str, int] = defaultdict(int)
        category_counts: Dict[str, int] = defaultdict(int)
        status_counts: Dict[str, int] = defaultdict(int)
        tag_counts: Dict[str, int] = defaultdict(int)
        
        total_confidence = 0
        total_usage = 0
        total_success_rate = 0
        
        for item in all_items:
            type_counts[item.knowledge_type.value] += 1
            category_counts[item.category] += 1
            status_counts[item.status.value] += 1
            
            for tag in item.tags:
                tag_counts[tag] += 1
            
            total_confidence += item.confidence_score
            total_usage += item.usage_count
            total_success_rate += item.success_rate
        
        n = len(all_items)
        
        return {
            "total_knowledge": n,
            "by_type": dict(type_counts),
            "by_category": dict(category_counts),
            "by_status": dict(status_counts),
            "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "average_confidence": total_confidence / n if n > 0 else 0,
            "total_usage": total_usage,
            "average_success_rate": total_success_rate / n if n > 0 else 0
        }
    
    def get_categories(self, knowledge_type: Optional[KnowledgeType] = None) -> List[str]:
        if knowledge_type:
            return self.DEFAULT_CATEGORIES.get(knowledge_type, [])
        
        all_categories = []
        for categories in self.DEFAULT_CATEGORIES.values():
            all_categories.extend(categories)
        return list(set(all_categories))
    
    def suggest_tags(self, content: str, limit: int = 5) -> List[str]:
        all_items = self._backend.list_all()
        
        tag_scores: Dict[str, float] = defaultdict(float)
        content_words = set(re.findall(r'\w+', content.lower()))
        
        for item in all_items:
            item_words = set(re.findall(r'\w+', item.content.lower()[:500]))
            overlap = len(content_words & item_words)
            
            if overlap > 0:
                similarity = overlap / max(len(content_words), len(item_words))
                for tag in item.tags:
                    tag_scores[tag] += similarity
        
        sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)
        return [tag for tag, _ in sorted_tags[:limit]]
    
    def find_related(self, knowledge_id: str, limit: int = 5) -> List[KnowledgeItem]:
        item = self._backend.load(knowledge_id)
        if not item:
            return []
        
        query = f"{item.title} {' '.join(item.tags[:3])}"
        results = self.search(query, mode=SearchMode.KEYWORD, limit=limit + 1)
        
        return [r.item for r in results if r.item.knowledge_id != knowledge_id][:limit]
    
    def merge_knowledge(
        self,
        knowledge_ids: List[str],
        merged_title: Optional[str] = None
    ) -> Optional[KnowledgeItem]:
        items = [self._backend.load(kid) for kid in knowledge_ids]
        items = [i for i in items if i is not None]
        
        if len(items) < 2:
            return None
        
        all_tags = set()
        all_content = []
        total_confidence = 0
        total_usage = 0
        
        for item in items:
            all_tags.update(item.tags)
            all_content.append(item.content)
            total_confidence += item.confidence_score
            total_usage += item.usage_count
        
        merged = KnowledgeItem(
            knowledge_id=f"KB-MERGED-{hashlib.md5('|'.join(knowledge_ids).encode()).hexdigest()[:8]}",
            knowledge_type=items[0].knowledge_type,
            title=merged_title or f"合并知识 ({len(items)}条)",
            content="\n\n---\n\n".join(all_content),
            tags=list(all_tags),
            category=items[0].category,
            confidence_score=total_confidence / len(items),
            usage_count=total_usage,
            related_ids=knowledge_ids,
            metadata={"merged_from": knowledge_ids}
        )
        
        self._backend.save(merged)
        
        for kid in knowledge_ids:
            self.update_knowledge(kid, {"status": KnowledgeStatus.ARCHIVED})
        
        logger.info(f"合并知识: {knowledge_ids} -> {merged.knowledge_id}")
        return merged
    
    def clear(self) -> None:
        if self._backend:
            self._backend.clear()
            self._version_history.clear()
            logger.info("知识库已清空")
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        if self._backend:
            return self._backend.count(filters)
        return 0
    
    def backup(self, backup_path: str) -> None:
        if self.storage_type == StorageType.JSON:
            shutil.copytree(self.storage_path, backup_path)
        else:
            self.export_knowledge(backup_path, format="json")
        
        logger.info(f"知识库备份完成: {backup_path}")
    
    def restore(self, backup_path: str) -> None:
        backup_file = Path(backup_path)
        
        if backup_file.is_dir():
            if self.storage_type == StorageType.JSON:
                shutil.copytree(backup_path, self.storage_path)
                self._backend = JSONStorageBackend(self.storage_path)
                self._backend.initialize()
        else:
            self.import_knowledge(backup_path)
        
        logger.info(f"知识库恢复完成: {backup_path}")


def create_fix_pattern_knowledge(
    title: str,
    content: str,
    error_type: str,
    fix_steps: List[str],
    tags: Optional[List[str]] = None
) -> KnowledgeItem:
    return KnowledgeItem(
        knowledge_id="",
        knowledge_type=KnowledgeType.FIX_PATTERN,
        title=title,
        content=content,
        tags=tags or [error_type],
        category=error_type,
        examples=[{"step": str(i+1), "action": step} for i, step in enumerate(fix_steps)]
    )


def create_best_practice_knowledge(
    title: str,
    content: str,
    practice_area: str,
    code_example: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> KnowledgeItem:
    examples = []
    if code_example:
        examples.append({"type": "code", "content": code_example})
    
    return KnowledgeItem(
        knowledge_id="",
        knowledge_type=KnowledgeType.BEST_PRACTICE,
        title=title,
        content=content,
        tags=tags or [practice_area],
        category=practice_area,
        examples=examples
    )


def create_diagnosis_knowledge(
    title: str,
    content: str,
    symptom: str,
    root_cause: str,
    solution: str,
    tags: Optional[List[str]] = None
) -> KnowledgeItem:
    return KnowledgeItem(
        knowledge_id="",
        knowledge_type=KnowledgeType.DIAGNOSIS,
        title=title,
        content=content,
        tags=tags or [symptom],
        category=symptom,
        metadata={
            "symptom": symptom,
            "root_cause": root_cause,
            "solution": solution
        }
    )


def create_code_pattern_knowledge(
    title: str,
    content: str,
    pattern_name: str,
    code_template: str,
    tags: Optional[List[str]] = None
) -> KnowledgeItem:
    return KnowledgeItem(
        knowledge_id="",
        knowledge_type=KnowledgeType.CODE_PATTERN,
        title=title,
        content=content,
        tags=tags or [pattern_name],
        category=pattern_name,
        examples=[{"type": "template", "content": code_template}]
    )


class KnowledgePermission(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    SHARED = "shared"


class SyncStatus(Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


class ConflictResolution(Enum):
    KEEP_LOCAL = "keep_local"
    KEEP_REMOTE = "keep_remote"
    MERGE = "merge"
    MANUAL = "manual"


@dataclass
class ProjectInfo:
    project_id: str
    project_name: str
    project_path: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectInfo":
        return cls(**data)


@dataclass
class SharedKnowledge:
    knowledge_id: str
    source_project_id: str
    target_project_ids: List[str]
    permission: KnowledgePermission
    shared_at: str
    shared_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.permission, str):
            self.permission = KnowledgePermission(self.permission)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['permission'] = self.permission.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SharedKnowledge":
        if isinstance(data.get('permission'), str):
            data['permission'] = KnowledgePermission(data['permission'])
        return cls(**data)


@dataclass
class SyncRecord:
    sync_id: str
    source_project_id: str
    target_project_id: str
    knowledge_ids: List[str]
    status: SyncStatus
    started_at: str
    completed_at: str = ""
    error_message: str = ""
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = SyncStatus(self.status)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncRecord":
        if isinstance(data.get('status'), str):
            data['status'] = SyncStatus(data['status'])
        return cls(**data)


@dataclass
class ConflictInfo:
    knowledge_id: str
    source_project_id: str
    target_project_id: str
    local_version: Dict[str, Any]
    remote_version: Dict[str, Any]
    detected_at: str
    resolution: ConflictResolution = ConflictResolution.MANUAL
    
    def __post_init__(self):
        if isinstance(self.resolution, str):
            self.resolution = ConflictResolution(self.resolution)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['resolution'] = self.resolution.value
        return data


@dataclass
class IndexEntry:
    knowledge_id: str
    project_id: str
    indexed_fields: Dict[str, Any]
    tags: List[str]
    embedding: Optional[List[float]] = None
    indexed_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UpdateBatch:
    batch_id: str
    updates: List[Dict[str, Any]]
    created_at: str
    status: str = "pending"
    applied_count: int = 0
    failed_count: int = 0
    rollback_data: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SharedKnowledgePool:
    """知识共享池
    
    管理跨项目的共享知识，支持权限控制和知识隔离。
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./shared_knowledge_pool")
        self._shared_items: Dict[str, SharedKnowledge] = {}
        self._access_cache: Dict[str, Set[str]] = defaultdict(set)
    
    def initialize(self) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._load_shared_items()
    
    def _load_shared_items(self) -> None:
        shared_file = self.storage_path / "shared_items.json"
        if shared_file.exists():
            try:
                with open(shared_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._shared_items = {
                        k: SharedKnowledge.from_dict(v) 
                        for k, v in data.items()
                    }
                self._rebuild_access_cache()
            except Exception as e:
                logger.error(f"加载共享知识失败: {e}")
    
    def _save_shared_items(self) -> None:
        shared_file = self.storage_path / "shared_items.json"
        try:
            with open(shared_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {k: v.to_dict() for k, v in self._shared_items.items()},
                    f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            logger.error(f"保存共享知识失败: {e}")
    
    def _rebuild_access_cache(self) -> None:
        self._access_cache.clear()
        for shared in self._shared_items.values():
            for project_id in shared.target_project_ids:
                self._access_cache[project_id].add(shared.knowledge_id)
    
    def share_knowledge(
        self,
        knowledge_id: str,
        source_project_id: str,
        target_project_ids: List[str],
        permission: KnowledgePermission = KnowledgePermission.SHARED,
        shared_by: str = "system"
    ) -> SharedKnowledge:
        shared = SharedKnowledge(
            knowledge_id=knowledge_id,
            source_project_id=source_project_id,
            target_project_ids=target_project_ids,
            permission=permission,
            shared_at=datetime.now().isoformat(),
            shared_by=shared_by
        )
        
        self._shared_items[knowledge_id] = shared
        self._rebuild_access_cache()
        self._save_shared_items()
        
        logger.info(f"共享知识: {knowledge_id} -> {target_project_ids}")
        return shared
    
    def revoke_sharing(self, knowledge_id: str, target_project_id: Optional[str] = None) -> bool:
        if knowledge_id not in self._shared_items:
            return False
        
        shared = self._shared_items[knowledge_id]
        
        if target_project_id:
            if target_project_id in shared.target_project_ids:
                shared.target_project_ids.remove(target_project_id)
                if not shared.target_project_ids:
                    del self._shared_items[knowledge_id]
        else:
            del self._shared_items[knowledge_id]
        
        self._rebuild_access_cache()
        self._save_shared_items()
        return True
    
    def get_accessible_knowledge(self, project_id: str) -> List[str]:
        return list(self._access_cache.get(project_id, set()))
    
    def check_permission(
        self,
        knowledge_id: str,
        project_id: str
    ) -> Optional[KnowledgePermission]:
        shared = self._shared_items.get(knowledge_id)
        if not shared:
            return None
        
        if shared.permission == KnowledgePermission.PUBLIC:
            return KnowledgePermission.PUBLIC
        
        if project_id == shared.source_project_id:
            return KnowledgePermission.PRIVATE
        
        if project_id in shared.target_project_ids:
            return KnowledgePermission.SHARED
        
        return None
    
    def get_shared_by_project(self, project_id: str) -> List[SharedKnowledge]:
        result = []
        for shared in self._shared_items.values():
            if shared.source_project_id == project_id:
                result.append(shared)
        return result
    
    def get_shared_to_project(self, project_id: str) -> List[SharedKnowledge]:
        result = []
        for shared in self._shared_items.values():
            if project_id in shared.target_project_ids:
                result.append(shared)
        return result


class CrossProjectKnowledgeManager:
    """跨项目知识管理器
    
    管理多个项目的知识库，实现知识隔离和共享。
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path("./cross_project_kb")
        self._projects: Dict[str, ProjectInfo] = {}
        self._knowledge_bases: Dict[str, KnowledgeBase] = {}
        self._shared_pool = SharedKnowledgePool(self.base_path / "shared_pool")
    
    def initialize(self) -> None:
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._shared_pool.initialize()
        self._load_projects()
    
    def _load_projects(self) -> None:
        projects_file = self.base_path / "projects.json"
        if projects_file.exists():
            try:
                with open(projects_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._projects = {
                        k: ProjectInfo.from_dict(v) for k, v in data.items()
                    }
            except Exception as e:
                logger.error(f"加载项目信息失败: {e}")
    
    def _save_projects(self) -> None:
        projects_file = self.base_path / "projects.json"
        try:
            with open(projects_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {k: v.to_dict() for k, v in self._projects.items()},
                    f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            logger.error(f"保存项目信息失败: {e}")
    
    def register_project(
        self,
        project_id: str,
        project_name: str,
        project_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProjectInfo:
        if project_id in self._projects:
            raise ValueError(f"项目已存在: {project_id}")
        
        project = ProjectInfo(
            project_id=project_id,
            project_name=project_name,
            project_path=project_path,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        self._projects[project_id] = project
        
        kb_path = self.base_path / "projects" / project_id
        kb_path.mkdir(parents=True, exist_ok=True)
        
        self._knowledge_bases[project_id] = KnowledgeBase(
            storage_path=kb_path,
            storage_type=StorageType.SQLITE
        )
        
        self._save_projects()
        logger.info(f"注册项目: {project_id} - {project_name}")
        return project
    
    def unregister_project(self, project_id: str) -> bool:
        if project_id not in self._projects:
            return False
        
        del self._projects[project_id]
        if project_id in self._knowledge_bases:
            del self._knowledge_bases[project_id]
        
        self._save_projects()
        logger.info(f"注销项目: {project_id}")
        return True
    
    def get_project(self, project_id: str) -> Optional[ProjectInfo]:
        return self._projects.get(project_id)
    
    def list_projects(self) -> List[ProjectInfo]:
        return list(self._projects.values())
    
    def get_knowledge_base(self, project_id: str) -> Optional[KnowledgeBase]:
        if project_id not in self._knowledge_bases:
            project = self._projects.get(project_id)
            if project:
                kb_path = self.base_path / "projects" / project_id
                self._knowledge_bases[project_id] = KnowledgeBase(
                    storage_path=kb_path,
                    storage_type=StorageType.SQLITE
                )
        return self._knowledge_bases.get(project_id)
    
    def share_knowledge(
        self,
        knowledge_id: str,
        source_project_id: str,
        target_project_ids: List[str],
        permission: KnowledgePermission = KnowledgePermission.SHARED
    ) -> Optional[SharedKnowledge]:
        source_kb = self.get_knowledge_base(source_project_id)
        if not source_kb:
            return None
        
        item = source_kb.get_knowledge(knowledge_id)
        if not item:
            return None
        
        return self._shared_pool.share_knowledge(
            knowledge_id=knowledge_id,
            source_project_id=source_project_id,
            target_project_ids=target_project_ids,
            permission=permission
        )
    
    def get_shared_knowledge(self, project_id: str) -> List[Tuple[KnowledgeItem, str]]:
        result = []
        shared_list = self._shared_pool.get_shared_to_project(project_id)
        
        for shared in shared_list:
            source_kb = self.get_knowledge_base(shared.source_project_id)
            if source_kb:
                item = source_kb.get_knowledge(shared.knowledge_id)
                if item:
                    result.append((item, shared.source_project_id))
        
        return result
    
    def copy_knowledge(
        self,
        knowledge_id: str,
        source_project_id: str,
        target_project_id: str
    ) -> Optional[str]:
        source_kb = self.get_knowledge_base(source_project_id)
        target_kb = self.get_knowledge_base(target_project_id)
        
        if not source_kb or not target_kb:
            return None
        
        item = source_kb.get_knowledge(knowledge_id)
        if not item:
            return None
        
        new_item = KnowledgeItem(
            knowledge_id="",
            knowledge_type=item.knowledge_type,
            title=item.title,
            content=item.content,
            tags=item.tags.copy(),
            category=item.category,
            subcategory=item.subcategory,
            metadata={
                **item.metadata,
                "copied_from": knowledge_id,
                "source_project": source_project_id
            },
            examples=item.examples.copy()
        )
        
        return target_kb.add_knowledge(new_item)
    
    def get_statistics(self) -> Dict[str, Any]:
        stats = {
            "total_projects": len(self._projects),
            "projects": {},
            "shared_count": len(self._shared_pool._shared_items)
        }
        
        for project_id, kb in self._knowledge_bases.items():
            kb_stats = kb.get_statistics()
            stats["projects"][project_id] = kb_stats
        
        return stats


class KnowledgeSynchronizer:
    """知识同步器
    
    实现跨项目知识的增量同步和冲突处理。
    """
    
    def __init__(self, manager: CrossProjectKnowledgeManager):
        self.manager = manager
        self._sync_records: Dict[str, SyncRecord] = {}
        self._sync_history: List[SyncRecord] = []
        self._change_log: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    def record_change(
        self,
        project_id: str,
        knowledge_id: str,
        change_type: str,
        change_data: Dict[str, Any]
    ) -> None:
        self._change_log[f"{project_id}:{knowledge_id}"].append({
            "type": change_type,
            "data": change_data,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_changes_since(
        self,
        project_id: str,
        since: str
    ) -> List[Dict[str, Any]]:
        changes = []
        for key, log in self._change_log.items():
            if key.startswith(f"{project_id}:"):
                for entry in log:
                    if entry["timestamp"] > since:
                        changes.append({
                            "key": key,
                            **entry
                        })
        return sorted(changes, key=lambda x: x["timestamp"])
    
    def sync_knowledge(
        self,
        source_project_id: str,
        target_project_id: str,
        knowledge_ids: Optional[List[str]] = None
    ) -> SyncRecord:
        sync_id = f"SYNC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(f'{source_project_id}-{target_project_id}'.encode()).hexdigest()[:6]}"
        
        record = SyncRecord(
            sync_id=sync_id,
            source_project_id=source_project_id,
            target_project_id=target_project_id,
            knowledge_ids=knowledge_ids or [],
            status=SyncStatus.PENDING,
            started_at=datetime.now().isoformat()
        )
        
        self._sync_records[sync_id] = record
        
        try:
            record.status = SyncStatus.SYNCING
            
            source_kb = self.manager.get_knowledge_base(source_project_id)
            target_kb = self.manager.get_knowledge_base(target_project_id)
            
            if not source_kb or not target_kb:
                record.status = SyncStatus.FAILED
                record.error_message = "源项目或目标项目不存在"
                return record
            
            if not knowledge_ids:
                shared = self.manager._shared_pool.get_shared_to_project(target_project_id)
                knowledge_ids = [s.knowledge_id for s in shared 
                               if s.source_project_id == source_project_id]
                record.knowledge_ids = knowledge_ids
            
            conflicts = []
            for kid in knowledge_ids:
                item = source_kb.get_knowledge(kid)
                if not item:
                    continue
                
                target_item = target_kb.get_knowledge(kid)
                
                if target_item:
                    conflict = self._detect_conflict(item, target_item, source_project_id, target_project_id)
                    if conflict:
                        conflicts.append(conflict.to_dict())
                        continue
                
                new_item = KnowledgeItem(
                    knowledge_id=kid,
                    knowledge_type=item.knowledge_type,
                    title=item.title,
                    content=item.content,
                    tags=item.tags.copy(),
                    category=item.category,
                    subcategory=item.subcategory,
                    metadata={
                        **item.metadata,
                        "synced_from": source_project_id,
                        "synced_at": datetime.now().isoformat()
                    },
                    version=item.version,
                    examples=item.examples.copy()
                )
                target_kb._backend.save(new_item)
            
            if conflicts:
                record.status = SyncStatus.CONFLICT
                record.conflicts = conflicts
            else:
                record.status = SyncStatus.COMPLETED
            
            record.completed_at = datetime.now().isoformat()
            
        except Exception as e:
            record.status = SyncStatus.FAILED
            record.error_message = str(e)
            logger.error(f"同步失败: {e}")
        
        self._sync_history.append(record)
        return record
    
    def _detect_conflict(
        self,
        source_item: KnowledgeItem,
        target_item: KnowledgeItem,
        source_project_id: str,
        target_project_id: str
    ) -> Optional[ConflictInfo]:
        if source_item.updated_at == target_item.updated_at:
            return None
        
        if source_item.updated_at > target_item.updated_at:
            return None
        
        source_meta = source_item.metadata.get("synced_from")
        target_meta = target_item.metadata.get("synced_from")
        
        if source_meta != target_project_id and target_meta != source_project_id:
            return ConflictInfo(
                knowledge_id=source_item.knowledge_id,
                source_project_id=source_project_id,
                target_project_id=target_project_id,
                local_version=target_item.to_dict(),
                remote_version=source_item.to_dict(),
                detected_at=datetime.now().isoformat()
            )
        
        return None
    
    def resolve_conflict(
        self,
        conflict: ConflictInfo,
        resolution: ConflictResolution
    ) -> Optional[KnowledgeItem]:
        source_kb = self.manager.get_knowledge_base(conflict.source_project_id)
        target_kb = self.manager.get_knowledge_base(conflict.target_project_id)
        
        if not source_kb or not target_kb:
            return None
        
        if resolution == ConflictResolution.KEEP_LOCAL:
            return target_kb.get_knowledge(conflict.knowledge_id)
        
        elif resolution == ConflictResolution.KEEP_REMOTE:
            remote_item = KnowledgeItem.from_dict(conflict.remote_version)
            target_kb._backend.save(remote_item)
            return remote_item
        
        elif resolution == ConflictResolution.MERGE:
            local = conflict.local_version
            remote = conflict.remote_version
            
            merged_tags = list(set(local.get("tags", []) + remote.get("tags", [])))
            
            merged_item = KnowledgeItem(
                knowledge_id=conflict.knowledge_id,
                knowledge_type=KnowledgeType(remote.get("knowledge_type")),
                title=remote.get("title", local.get("title", "")),
                content=f"{local.get('content', '')}\n\n--- Merged ---\n\n{remote.get('content', '')}",
                tags=merged_tags,
                category=remote.get("category", local.get("category", "")),
                metadata={
                    **local.get("metadata", {}),
                    **remote.get("metadata", {}),
                    "merged_at": datetime.now().isoformat()
                },
                version=max(local.get("version", 1), remote.get("version", 1)) + 1
            )
            
            target_kb._backend.save(merged_item)
            return merged_item
        
        return None
    
    def get_sync_status(self, sync_id: str) -> Optional[SyncRecord]:
        return self._sync_records.get(sync_id)
    
    def get_sync_history(
        self,
        project_id: Optional[str] = None,
        limit: int = 50
    ) -> List[SyncRecord]:
        history = self._sync_history
        
        if project_id:
            history = [
                r for r in history
                if r.source_project_id == project_id or r.target_project_id == project_id
            ]
        
        return history[-limit:]
    
    def schedule_sync(
        self,
        source_project_id: str,
        target_project_id: str,
        interval_seconds: int
    ) -> str:
        schedule_id = f"SCHED-{hashlib.md5(f'{source_project_id}-{target_project_id}'.encode()).hexdigest()[:8]}"
        
        logger.info(f"计划同步: {schedule_id}, 间隔: {interval_seconds}秒")
        return schedule_id


class KnowledgeIndexManager:
    """知识索引管理器
    
    管理全文索引、标签索引和语义索引。
    """
    
    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
        self._fulltext_index: Dict[str, List[str]] = defaultdict(list)
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)
        self._semantic_index: Dict[str, List[float]] = {}
        self._project_index: Dict[str, Set[str]] = defaultdict(set)
        self._indexed_at: Dict[str, str] = {}
    
    def build_fulltext_index(self) -> None:
        self._fulltext_index.clear()
        
        items = self.kb.list_knowledge(limit=10000)
        
        for item in items:
            self._index_item_fulltext(item)
        
        logger.info(f"构建全文索引完成: {len(items)} 条知识")
    
    def _index_item_fulltext(self, item: KnowledgeItem) -> None:
        words = set()
        
        words.update(self._tokenize(item.title))
        words.update(self._tokenize(item.content))
        
        for word in words:
            if len(word) > 1:
                if item.knowledge_id not in self._fulltext_index[word]:
                    self._fulltext_index[word].append(item.knowledge_id)
        
        self._indexed_at[item.knowledge_id] = datetime.now().isoformat()
    
    def _tokenize(self, text: str) -> Set[str]:
        words = set()
        
        words.update(re.findall(r'\w+', text.lower()))
        
        for i in range(len(text) - 1):
            words.add(text[i:i+2].lower())
        
        return words
    
    def build_tag_index(self) -> None:
        self._tag_index.clear()
        
        items = self.kb.list_knowledge(limit=10000)
        
        for item in items:
            for tag in item.tags:
                self._tag_index[tag.lower()].add(item.knowledge_id)
        
        logger.info(f"构建标签索引完成: {len(self._tag_index)} 个标签")
    
    def build_project_index(self, project_id: str, knowledge_ids: List[str]) -> None:
        self._project_index[project_id] = set(knowledge_ids)
        logger.info(f"构建项目索引: {project_id}, {len(knowledge_ids)} 条知识")
    
    def build_semantic_index(
        self,
        embedding_func: Optional[Callable[[str], List[float]]] = None
    ) -> None:
        self._semantic_index.clear()
        
        items = self.kb.list_knowledge(limit=10000)
        
        for item in items:
            if embedding_func:
                try:
                    text = f"{item.title} {item.content[:500]}"
                    embedding = embedding_func(text)
                    self._semantic_index[item.knowledge_id] = embedding
                except Exception as e:
                    logger.warning(f"生成语义索引失败: {item.knowledge_id} - {e}")
            else:
                self._semantic_index[item.knowledge_id] = self._generate_simple_embedding(item)
        
        logger.info(f"构建语义索引完成: {len(self._semantic_index)} 条知识")
    
    def _generate_simple_embedding(self, item: KnowledgeItem) -> List[float]:
        text = f"{item.title} {item.content[:500]}"
        
        words = re.findall(r'\w+', text.lower())
        
        embedding = [0.0] * 100
        for i, word in enumerate(words[:100]):
            embedding[i % 100] += hash(word) % 100 / 100.0
        
        total = sum(embedding) or 1
        return [v / total for v in embedding]
    
    def search_fulltext(self, query: str, limit: int = 50) -> List[Tuple[str, float]]:
        query_words = self._tokenize(query)
        
        scores: Dict[str, float] = defaultdict(float)
        
        for word in query_words:
            if word in self._fulltext_index:
                for kid in self._fulltext_index[word]:
                    scores[kid] += 1.0 / len(query_words)
        
        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def search_by_tag(self, tags: List[str], match_all: bool = False) -> List[str]:
        if not tags:
            return []
        
        tags_lower = [t.lower() for t in tags]
        
        if match_all:
            result = None
            for tag in tags_lower:
                if tag in self._tag_index:
                    if result is None:
                        result = self._tag_index[tag].copy()
                    else:
                        result &= self._tag_index[tag]
            return list(result) if result else []
        else:
            result = set()
            for tag in tags_lower:
                if tag in self._tag_index:
                    result |= self._tag_index[tag]
            return list(result)
    
    def search_semantic(
        self,
        query_embedding: List[float],
        threshold: float = 0.5,
        limit: int = 10
    ) -> List[Tuple[str, float]]:
        if not self._semantic_index:
            return []
        
        results = []
        
        for kid, embedding in self._semantic_index.items():
            similarity = self._cosine_similarity(query_embedding, embedding)
            if similarity >= threshold:
                results.append((kid, similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def update_index(self, item: KnowledgeItem) -> None:
        self._index_item_fulltext(item)
        
        for tag in item.tags:
            self._tag_index[tag.lower()].add(item.knowledge_id)
    
    def remove_from_index(self, knowledge_id: str) -> None:
        for word in list(self._fulltext_index.keys()):
            if knowledge_id in self._fulltext_index[word]:
                self._fulltext_index[word].remove(knowledge_id)
            if not self._fulltext_index[word]:
                del self._fulltext_index[word]
        
        for tag in list(self._tag_index.keys()):
            self._tag_index[tag].discard(knowledge_id)
        
        if knowledge_id in self._semantic_index:
            del self._semantic_index[knowledge_id]
        
        if knowledge_id in self._indexed_at:
            del self._indexed_at[knowledge_id]
    
    def get_index_statistics(self) -> Dict[str, Any]:
        return {
            "fulltext_words": len(self._fulltext_index),
            "total_indexed_items": len(self._indexed_at),
            "tag_count": len(self._tag_index),
            "semantic_indexed": len(self._semantic_index),
            "project_count": len(self._project_index)
        }
    
    def export_index(self, output_path: str) -> None:
        data = {
            "fulltext_index": dict(self._fulltext_index),
            "tag_index": {k: list(v) for k, v in self._tag_index.items()},
            "semantic_index": self._semantic_index,
            "indexed_at": self._indexed_at
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_index(self, input_path: str) -> None:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self._fulltext_index = defaultdict(list, data.get("fulltext_index", {}))
        self._tag_index = defaultdict(set, {k: set(v) for k, v in data.get("tag_index", {}).items()})
        self._semantic_index = data.get("semantic_index", {})
        self._indexed_at = data.get("indexed_at", {})


class KnowledgeUpdateManager:
    """知识更新管理器
    
    管理批量更新、验证和回滚。
    """
    
    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
        self._batches: Dict[str, UpdateBatch] = {}
        self._validators: Dict[str, Callable[[KnowledgeItem], bool]] = {}
        self._update_hooks: List[Callable[[str, Dict[str, Any]], None]] = []
    
    def register_validator(
        self,
        field_name: str,
        validator: Callable[[KnowledgeItem], bool]
    ) -> None:
        self._validators[field_name] = validator
        logger.info(f"注册验证器: {field_name}")
    
    def add_update_hook(self, hook: Callable[[str, Dict[str, Any]], None]) -> None:
        self._update_hooks.append(hook)
    
    def create_batch(self, updates: List[Dict[str, Any]]) -> UpdateBatch:
        batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(str(len(updates)).encode()).hexdigest()[:6]}"
        
        batch = UpdateBatch(
            batch_id=batch_id,
            updates=updates,
            created_at=datetime.now().isoformat()
        )
        
        self._batches[batch_id] = batch
        return batch
    
    def validate_update(self, update: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        
        if "knowledge_id" not in update:
            errors.append("缺少 knowledge_id")
            return False, errors
        
        item = self.kb.get_knowledge(update["knowledge_id"])
        if not item:
            errors.append(f"知识不存在: {update['knowledge_id']}")
            return False, errors
        
        for field, value in update.get("updates", {}).items():
            if field in self._validators:
                try:
                    temp_item = KnowledgeItem.from_dict(item.to_dict())
                    setattr(temp_item, field, value)
                    
                    if not self._validators[field](temp_item):
                        errors.append(f"验证失败: {field}")
                except Exception as e:
                    errors.append(f"验证异常: {field} - {e}")
        
        return len(errors) == 0, errors
    
    def apply_batch(
        self,
        batch_id: str,
        validate: bool = True,
        auto_rollback: bool = True
    ) -> Dict[str, Any]:
        batch = self._batches.get(batch_id)
        if not batch:
            return {"success": False, "error": "批次不存在"}
        
        batch.status = "running"
        applied = []
        failed = []
        rollback_data = []
        
        for update in batch.updates:
            if validate:
                is_valid, errors = self.validate_update(update)
                if not is_valid:
                    failed.append({
                        "knowledge_id": update.get("knowledge_id"),
                        "errors": errors
                    })
                    continue
            
            knowledge_id = update["knowledge_id"]
            updates = update.get("updates", {})
            
            item = self.kb.get_knowledge(knowledge_id)
            if item:
                rollback_data.append({
                    "knowledge_id": knowledge_id,
                    "snapshot": item.to_dict()
                })
                
                try:
                    self.kb.update_knowledge(knowledge_id, updates)
                    applied.append(knowledge_id)
                    batch.applied_count += 1
                    
                    for hook in self._update_hooks:
                        try:
                            hook(knowledge_id, updates)
                        except Exception as e:
                            logger.warning(f"更新钩子执行失败: {e}")
                            
                except Exception as e:
                    failed.append({
                        "knowledge_id": knowledge_id,
                        "error": str(e)
                    })
                    batch.failed_count += 1
        
        batch.rollback_data = rollback_data
        
        if failed and auto_rollback:
            self.rollback_batch(batch_id)
            batch.status = "rolled_back"
        elif failed:
            batch.status = "partial"
        else:
            batch.status = "completed"
        
        return {
            "success": len(failed) == 0,
            "applied": applied,
            "failed": failed,
            "rolled_back": auto_rollback and len(failed) > 0
        }
    
    def rollback_batch(self, batch_id: str) -> bool:
        batch = self._batches.get(batch_id)
        if not batch or not batch.rollback_data:
            return False
        
        for snapshot_data in reversed(batch.rollback_data):
            knowledge_id = snapshot_data["knowledge_id"]
            snapshot = snapshot_data["snapshot"]
            
            try:
                item = KnowledgeItem.from_dict(snapshot)
                self.kb._backend.save(item)
            except Exception as e:
                logger.error(f"回滚失败: {knowledge_id} - {e}")
        
        batch.status = "rolled_back"
        logger.info(f"批次已回滚: {batch_id}")
        return True
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        batch = self._batches.get(batch_id)
        if not batch:
            return None
        
        return batch.to_dict()
    
    def list_batches(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        batches = list(self._batches.values())
        
        if status:
            batches = [b for b in batches if b.status == status]
        
        return [b.to_dict() for b in batches]
    
    def update_with_validation(
        self,
        knowledge_id: str,
        updates: Dict[str, Any],
        validators: Optional[Dict[str, Callable]] = None
    ) -> Tuple[bool, Optional[KnowledgeItem], List[str]]:
        errors = []
        
        item = self.kb.get_knowledge(knowledge_id)
        if not item:
            return False, None, ["知识不存在"]
        
        merged_validators = {**self._validators, **(validators or {})}
        
        for field, value in updates.items():
            if field in merged_validators:
                try:
                    temp_item = KnowledgeItem.from_dict(item.to_dict())
                    setattr(temp_item, field, value)
                    
                    if not merged_validators[field](temp_item):
                        errors.append(f"验证失败: {field}")
                except Exception as e:
                    errors.append(f"验证异常: {field} - {e}")
        
        if errors:
            return False, None, errors
        
        updated_item = self.kb.update_knowledge(knowledge_id, updates)
        return True, updated_item, []
    
    def bulk_update(
        self,
        updates: List[Dict[str, Any]],
        stop_on_error: bool = True
    ) -> Dict[str, Any]:
        results = {
            "total": len(updates),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for update in updates:
            try:
                knowledge_id = update.get("knowledge_id")
                item_updates = update.get("updates", {})
                
                success, _, errors = self.update_with_validation(knowledge_id, item_updates)
                
                if success:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "knowledge_id": knowledge_id,
                        "errors": errors
                    })
                    
                    if stop_on_error:
                        break
                        
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "knowledge_id": update.get("knowledge_id"),
                    "errors": [str(e)]
                })
                
                if stop_on_error:
                    break
        
        return results
    
    def create_snapshot(self, knowledge_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        snapshot = {}
        
        for kid in knowledge_ids:
            item = self.kb.get_knowledge(kid)
            if item:
                snapshot[kid] = item.to_dict()
        
        return snapshot
    
    def restore_snapshot(self, snapshot: Dict[str, Dict[str, Any]]) -> int:
        restored = 0
        
        for kid, data in snapshot.items():
            try:
                item = KnowledgeItem.from_dict(data)
                self.kb._backend.save(item)
                restored += 1
            except Exception as e:
                logger.error(f"恢复快照失败: {kid} - {e}")
        
        return restored


class EvolutionType(Enum):
    OPTIMIZATION = "optimization"
    REFACTORING = "refactoring"
    ENHANCEMENT = "enhancement"
    BUG_FIX = "bug_fix"
    ADAPTATION = "adaptation"
    EXTENSION = "extension"
    DEPRECATION = "deprecation"
    MERGE = "merge"
    SPLIT = "split"
    REPLACEMENT = "replacement"


class EvolutionTrigger(Enum):
    PERFORMANCE_ISSUE = "performance_issue"
    CODE_SMELL = "code_smell"
    REQUIREMENT_CHANGE = "requirement_change"
    BUG_REPORT = "bug_report"
    DEPENDENCY_UPDATE = "dependency_update"
    USER_FEEDBACK = "user_feedback"
    AUTOMATED_DETECTION = "automated_detection"
    MANUAL_REVIEW = "manual_review"
    SCHEDULED_MAINTENANCE = "scheduled_maintenance"


class EvolutionStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"


class EffectMetric(Enum):
    PERFORMANCE_GAIN = "performance_gain"
    CODE_QUALITY = "code_quality"
    MAINTAINABILITY = "maintainability"
    TEST_COVERAGE = "test_coverage"
    COMPLEXITY_REDUCTION = "complexity_reduction"
    BUG_FIX_RATE = "bug_fix_rate"
    USER_SATISFACTION = "user_satisfaction"


@dataclass
class EvolutionStep:
    step_id: str
    step_order: int
    action: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_outcome: str = ""
    rollback_action: str = ""
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvolutionStep":
        return cls(**data)


@dataclass
class TriggerCondition:
    condition_id: str
    condition_type: EvolutionTrigger
    description: str
    threshold: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['condition_type'] = self.condition_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriggerCondition":
        if isinstance(data.get('condition_type'), str):
            data['condition_type'] = EvolutionTrigger(data['condition_type'])
        return cls(**data)


@dataclass
class EffectEvaluation:
    evaluation_id: str
    metric: EffectMetric
    before_value: float
    after_value: float
    improvement: float
    evaluation_time: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['metric'] = self.metric.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EffectEvaluation":
        if isinstance(data.get('metric'), str):
            data['metric'] = EffectMetric(data['metric'])
        return cls(**data)


@dataclass
class EvolutionPattern:
    pattern_id: str
    pattern_name: str
    evolution_type: EvolutionType
    description: str
    trigger_conditions: List[TriggerCondition] = field(default_factory=list)
    execution_steps: List[EvolutionStep] = field(default_factory=list)
    effect_evaluations: List[EffectEvaluation] = field(default_factory=list)
    applicability: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    success_rate: float = 0.0
    usage_count: int = 0
    avg_execution_time: float = 0.0
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if isinstance(self.evolution_type, str):
            self.evolution_type = EvolutionType(self.evolution_type)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['evolution_type'] = self.evolution_type.value
        data['trigger_conditions'] = [tc.to_dict() for tc in self.trigger_conditions]
        data['execution_steps'] = [es.to_dict() for es in self.execution_steps]
        data['effect_evaluations'] = [ee.to_dict() for ee in self.effect_evaluations]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvolutionPattern":
        if isinstance(data.get('evolution_type'), str):
            data['evolution_type'] = EvolutionType(data['evolution_type'])
        
        data['trigger_conditions'] = [
            TriggerCondition.from_dict(tc) if isinstance(tc, dict) else tc
            for tc in data.get('trigger_conditions', [])
        ]
        data['execution_steps'] = [
            EvolutionStep.from_dict(es) if isinstance(es, dict) else es
            for es in data.get('execution_steps', [])
        ]
        data['effect_evaluations'] = [
            EffectEvaluation.from_dict(ee) if isinstance(ee, dict) else ee
            for ee in data.get('effect_evaluations', [])
        ]
        return cls(**data)


@dataclass
class EvolutionContext:
    context_id: str
    skill_id: str
    skill_name: str
    skill_version: str
    evolution_type: EvolutionType
    trigger_reason: str
    trigger_source: str
    environment: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.evolution_type, str):
            self.evolution_type = EvolutionType(self.evolution_type)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['evolution_type'] = self.evolution_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvolutionContext":
        if isinstance(data.get('evolution_type'), str):
            data['evolution_type'] = EvolutionType(data['evolution_type'])
        return cls(**data)


@dataclass
class EvolutionOperation:
    operation_id: str
    operation_type: str
    target: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    before_state: Dict[str, Any] = field(default_factory=dict)
    after_state: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    success: bool = True
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvolutionOperation":
        return cls(**data)


@dataclass
class EvolutionResult:
    result_id: str
    success: bool
    changes_made: List[str] = field(default_factory=list)
    effects: Dict[str, float] = field(default_factory=dict)
    side_effects: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    rollback_available: bool = True
    rollback_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvolutionResult":
        return cls(**data)


@dataclass
class EvolutionRecord:
    record_id: str
    pattern_id: str
    context: EvolutionContext
    operations: List[EvolutionOperation] = field(default_factory=list)
    result: Optional[EvolutionResult] = None
    status: EvolutionStatus = EvolutionStatus.PENDING
    started_at: str = ""
    completed_at: str = ""
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()
        if isinstance(self.status, str):
            self.status = EvolutionStatus(self.status)
        if isinstance(self.context, dict):
            self.context = EvolutionContext.from_dict(self.context)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        data['context'] = self.context.to_dict()
        data['operations'] = [op.to_dict() for op in self.operations]
        if self.result:
            data['result'] = self.result.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvolutionRecord":
        if isinstance(data.get('status'), str):
            data['status'] = EvolutionStatus(data['status'])
        if isinstance(data.get('context'), dict):
            data['context'] = EvolutionContext.from_dict(data['context'])
        data['operations'] = [
            EvolutionOperation.from_dict(op) if isinstance(op, dict) else op
            for op in data.get('operations', [])
        ]
        if isinstance(data.get('result'), dict):
            data['result'] = EvolutionResult.from_dict(data['result'])
        return cls(**data)


class EvolutionPatternStorage:
    """演化模式存储器
    
    负责演化模式的持久化存储、检索和管理。
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./evolution_patterns")
        self._patterns: Dict[str, EvolutionPattern] = {}
        self._type_index: Dict[str, Set[str]] = defaultdict(set)
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)
        self._trigger_index: Dict[str, Set[str]] = defaultdict(set)
    
    def initialize(self) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._load_patterns()
    
    def _load_patterns(self) -> None:
        patterns_file = self.storage_path / "evolution_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._patterns = {
                        k: EvolutionPattern.from_dict(v) 
                        for k, v in data.items()
                    }
                self._rebuild_indexes()
                logger.info(f"加载演化模式: {len(self._patterns)} 条")
            except Exception as e:
                logger.error(f"加载演化模式失败: {e}")
    
    def _save_patterns(self) -> None:
        patterns_file = self.storage_path / "evolution_patterns.json"
        try:
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {k: v.to_dict() for k, v in self._patterns.items()},
                    f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            logger.error(f"保存演化模式失败: {e}")
    
    def _rebuild_indexes(self) -> None:
        self._type_index.clear()
        self._tag_index.clear()
        self._trigger_index.clear()
        
        for pattern in self._patterns.values():
            self._type_index[pattern.evolution_type.value].add(pattern.pattern_id)
            
            for tag in pattern.tags:
                self._tag_index[tag.lower()].add(pattern.pattern_id)
            
            for trigger in pattern.trigger_conditions:
                self._trigger_index[trigger.condition_type.value].add(pattern.pattern_id)
    
    def save_pattern(self, pattern: EvolutionPattern) -> str:
        if not pattern.pattern_id:
            pattern.pattern_id = f"EVO-{pattern.evolution_type.value[:3].upper()}-{hashlib.md5(pattern.pattern_name.encode()).hexdigest()[:8]}"
        
        self._patterns[pattern.pattern_id] = pattern
        self._update_indexes(pattern)
        self._save_patterns()
        
        logger.info(f"保存演化模式: {pattern.pattern_id} - {pattern.pattern_name}")
        return pattern.pattern_id
    
    def _update_indexes(self, pattern: EvolutionPattern) -> None:
        self._type_index[pattern.evolution_type.value].add(pattern.pattern_id)
        
        for tag in pattern.tags:
            self._tag_index[tag.lower()].add(pattern.pattern_id)
        
        for trigger in pattern.trigger_conditions:
            self._trigger_index[trigger.condition_type.value].add(pattern.pattern_id)
    
    def get_pattern(self, pattern_id: str) -> Optional[EvolutionPattern]:
        return self._patterns.get(pattern_id)
    
    def delete_pattern(self, pattern_id: str) -> bool:
        if pattern_id not in self._patterns:
            return False
        
        pattern = self._patterns[pattern_id]
        
        self._type_index[pattern.evolution_type.value].discard(pattern_id)
        for tag in pattern.tags:
            self._tag_index[tag.lower()].discard(pattern_id)
        for trigger in pattern.trigger_conditions:
            self._trigger_index[trigger.condition_type.value].discard(pattern_id)
        
        del self._patterns[pattern_id]
        self._save_patterns()
        
        return True
    
    def find_by_type(self, evolution_type: EvolutionType) -> List[EvolutionPattern]:
        pattern_ids = self._type_index.get(evolution_type.value, set())
        return [self._patterns[pid] for pid in pattern_ids if pid in self._patterns]
    
    def find_by_trigger(self, trigger_type: EvolutionTrigger) -> List[EvolutionPattern]:
        pattern_ids = self._trigger_index.get(trigger_type.value, set())
        return [self._patterns[pid] for pid in pattern_ids if pid in self._patterns]
    
    def find_by_tags(self, tags: List[str], match_all: bool = False) -> List[EvolutionPattern]:
        if not tags:
            return []
        
        tags_lower = [t.lower() for t in tags]
        
        if match_all:
            result_ids = None
            for tag in tags_lower:
                if tag in self._tag_index:
                    if result_ids is None:
                        result_ids = self._tag_index[tag].copy()
                    else:
                        result_ids &= self._tag_index[tag]
            return [self._patterns[pid] for pid in (result_ids or set()) if pid in self._patterns]
        else:
            result_ids = set()
            for tag in tags_lower:
                if tag in self._tag_index:
                    result_ids |= self._tag_index[tag]
            return [self._patterns[pid] for pid in result_ids if pid in self._patterns]
    
    def search_patterns(
        self,
        query: str,
        evolution_type: Optional[EvolutionType] = None,
        min_success_rate: float = 0.0,
        limit: int = 20
    ) -> List[Tuple[EvolutionPattern, float]]:
        results = []
        query_lower = query.lower()
        
        for pattern in self._patterns.values():
            if evolution_type and pattern.evolution_type != evolution_type:
                continue
            
            if pattern.success_rate < min_success_rate:
                continue
            
            score = 0.0
            
            if query_lower in pattern.pattern_name.lower():
                score += 0.5
            if query_lower in pattern.description.lower():
                score += 0.3
            for tag in pattern.tags:
                if query_lower in tag.lower():
                    score += 0.2
                    break
            
            if score > 0:
                results.append((pattern, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def get_applicable_patterns(
        self,
        context: Dict[str, Any],
        limit: int = 10
    ) -> List[EvolutionPattern]:
        applicable = []
        
        for pattern in self._patterns.values():
            applicability_score = self._calculate_applicability(pattern, context)
            if applicability_score > 0:
                applicable.append((pattern, applicability_score))
        
        applicable.sort(key=lambda x: (x[1], x[0].success_rate), reverse=True)
        return [p for p, _ in applicable[:limit]]
    
    def _calculate_applicability(self, pattern: EvolutionPattern, context: Dict[str, Any]) -> float:
        score = 0.0
        
        context_type = context.get('evolution_type')
        if context_type and pattern.evolution_type.value == context_type:
            score += 0.4
        
        context_triggers = context.get('triggers', [])
        for trigger in context_triggers:
            for pt in pattern.trigger_conditions:
                if trigger == pt.condition_type.value:
                    score += 0.2
                    break
        
        context_tags = context.get('tags', [])
        for tag in context_tags:
            if tag.lower() in [t.lower() for t in pattern.tags]:
                score += 0.1
        
        return min(score, 1.0)
    
    def update_usage_stats(
        self,
        pattern_id: str,
        success: bool,
        execution_time: float
    ) -> None:
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return
        
        pattern.usage_count += 1
        
        if success:
            current_successes = pattern.success_rate * (pattern.usage_count - 1)
            pattern.success_rate = (current_successes + 1) / pattern.usage_count
        else:
            current_successes = pattern.success_rate * (pattern.usage_count - 1)
            pattern.success_rate = current_successes / pattern.usage_count
        
        pattern.avg_execution_time = (
            (pattern.avg_execution_time * (pattern.usage_count - 1) + execution_time) 
            / pattern.usage_count
        )
        
        pattern.updated_at = datetime.now().isoformat()
        self._save_patterns()
    
    def get_statistics(self) -> Dict[str, Any]:
        type_counts = defaultdict(int)
        total_usage = 0
        total_success_rate = 0
        total_avg_time = 0
        
        for pattern in self._patterns.values():
            type_counts[pattern.evolution_type.value] += 1
            total_usage += pattern.usage_count
            total_success_rate += pattern.success_rate
            total_avg_time += pattern.avg_execution_time
        
        n = len(self._patterns)
        
        return {
            "total_patterns": n,
            "by_type": dict(type_counts),
            "total_usage": total_usage,
            "average_success_rate": total_success_rate / n if n > 0 else 0,
            "average_execution_time": total_avg_time / n if n > 0 else 0,
            "tag_count": len(self._tag_index),
            "trigger_count": len(self._trigger_index)
        }


class EvolutionContextRecorder:
    """演化上下文记录器
    
    记录每次演化的完整上下文信息，包括时间、原因、操作和结果。
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./evolution_records")
        self._records: Dict[str, EvolutionRecord] = {}
        self._skill_index: Dict[str, List[str]] = defaultdict(list)
        self._pattern_index: Dict[str, List[str]] = defaultdict(list)
        self._time_index: Dict[str, List[str]] = defaultdict(list)
    
    def initialize(self) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._load_records()
    
    def _load_records(self) -> None:
        records_file = self.storage_path / "evolution_records.json"
        if records_file.exists():
            try:
                with open(records_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._records = {
                        k: EvolutionRecord.from_dict(v) 
                        for k, v in data.items()
                    }
                self._rebuild_indexes()
                logger.info(f"加载演化记录: {len(self._records)} 条")
            except Exception as e:
                logger.error(f"加载演化记录失败: {e}")
    
    def _save_records(self) -> None:
        records_file = self.storage_path / "evolution_records.json"
        try:
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {k: v.to_dict() for k, v in self._records.items()},
                    f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            logger.error(f"保存演化记录失败: {e}")
    
    def _rebuild_indexes(self) -> None:
        self._skill_index.clear()
        self._pattern_index.clear()
        self._time_index.clear()
        
        for record in self._records.values():
            self._skill_index[record.context.skill_id].append(record.record_id)
            self._pattern_index[record.pattern_id].append(record.record_id)
            
            date_key = record.started_at[:10] if record.started_at else "unknown"
            self._time_index[date_key].append(record.record_id)
    
    def start_evolution(
        self,
        pattern_id: str,
        context: EvolutionContext
    ) -> EvolutionRecord:
        record_id = f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(f'{pattern_id}-{context.skill_id}'.encode()).hexdigest()[:6]}"
        
        record = EvolutionRecord(
            record_id=record_id,
            pattern_id=pattern_id,
            context=context,
            status=EvolutionStatus.IN_PROGRESS,
            started_at=datetime.now().isoformat()
        )
        
        self._records[record_id] = record
        self._skill_index[context.skill_id].append(record_id)
        self._pattern_index[pattern_id].append(record_id)
        
        date_key = record.started_at[:10]
        self._time_index[date_key].append(record_id)
        
        self._save_records()
        
        logger.info(f"开始演化记录: {record_id}")
        return record
    
    def add_operation(
        self,
        record_id: str,
        operation: EvolutionOperation
    ) -> None:
        record = self._records.get(record_id)
        if not record:
            return
        
        record.operations.append(operation)
        self._save_records()
    
    def complete_evolution(
        self,
        record_id: str,
        result: EvolutionResult
    ) -> None:
        record = self._records.get(record_id)
        if not record:
            return
        
        record.result = result
        record.status = EvolutionStatus.COMPLETED if result.success else EvolutionStatus.FAILED
        record.completed_at = datetime.now().isoformat()
        
        if record.started_at:
            start_time = datetime.fromisoformat(record.started_at)
            end_time = datetime.fromisoformat(record.completed_at)
            record.duration = (end_time - start_time).total_seconds()
        
        self._save_records()
        
        logger.info(f"完成演化记录: {record_id}, 状态: {record.status.value}")
    
    def rollback_evolution(self, record_id: str) -> bool:
        record = self._records.get(record_id)
        if not record or not record.result or not record.result.rollback_available:
            return False
        
        record.status = EvolutionStatus.ROLLED_BACK
        record.completed_at = datetime.now().isoformat()
        
        self._save_records()
        
        logger.info(f"回滚演化记录: {record_id}")
        return True
    
    def get_record(self, record_id: str) -> Optional[EvolutionRecord]:
        return self._records.get(record_id)
    
    def get_records_by_skill(self, skill_id: str) -> List[EvolutionRecord]:
        record_ids = self._skill_index.get(skill_id, [])
        return [self._records[rid] for rid in record_ids if rid in self._records]
    
    def get_records_by_pattern(self, pattern_id: str) -> List[EvolutionRecord]:
        record_ids = self._pattern_index.get(pattern_id, [])
        return [self._records[rid] for rid in record_ids if rid in self._records]
    
    def get_records_by_date_range(
        self,
        start_date: str,
        end_date: str
    ) -> List[EvolutionRecord]:
        results = []
        
        for record in self._records.values():
            if record.started_at:
                record_date = record.started_at[:10]
                if start_date <= record_date <= end_date:
                    results.append(record)
        
        return sorted(results, key=lambda x: x.started_at)
    
    def get_recent_records(self, limit: int = 20) -> List[EvolutionRecord]:
        sorted_records = sorted(
            self._records.values(),
            key=lambda x: x.started_at,
            reverse=True
        )
        return sorted_records[:limit]
    
    def get_failed_records(self) -> List[EvolutionRecord]:
        return [
            r for r in self._records.values()
            if r.status == EvolutionStatus.FAILED
        ]
    
    def get_successful_records(self) -> List[EvolutionRecord]:
        return [
            r for r in self._records.values()
            if r.status == EvolutionStatus.COMPLETED
        ]
    
    def analyze_evolution_history(
        self,
        skill_id: Optional[str] = None
    ) -> Dict[str, Any]:
        records = self.get_records_by_skill(skill_id) if skill_id else list(self._records.values())
        
        if not records:
            return {"total": 0}
        
        type_counts = defaultdict(int)
        status_counts = defaultdict(int)
        total_duration = 0
        success_count = 0
        effect_sum = defaultdict(float)
        effect_count = defaultdict(int)
        
        for record in records:
            type_counts[record.context.evolution_type.value] += 1
            status_counts[record.status.value] += 1
            total_duration += record.duration
            
            if record.status == EvolutionStatus.COMPLETED:
                success_count += 1
            
            if record.result:
                for metric, value in record.result.effects.items():
                    effect_sum[metric] += value
                    effect_count[metric] += 1
        
        return {
            "total": len(records),
            "by_type": dict(type_counts),
            "by_status": dict(status_counts),
            "success_rate": success_count / len(records),
            "average_duration": total_duration / len(records),
            "average_effects": {
                metric: effect_sum[metric] / effect_count[metric]
                for metric in effect_sum
            }
        }
    
    def export_records(
        self,
        output_path: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> None:
        records = list(self._records.values())
        
        if filters:
            if 'skill_id' in filters:
                records = [r for r in records if r.context.skill_id == filters['skill_id']]
            if 'pattern_id' in filters:
                records = [r for r in records if r.pattern_id == filters['pattern_id']]
            if 'status' in filters:
                status_val = filters['status']
                if isinstance(status_val, EvolutionStatus):
                    status_val = status_val.value
                records = [r for r in records if r.status.value == status_val]
            if 'start_date' in filters:
                records = [r for r in records if r.started_at and r.started_at >= filters['start_date']]
            if 'end_date' in filters:
                records = [r for r in records if r.started_at and r.started_at <= filters['end_date']]
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total_count": len(records),
            "records": [r.to_dict() for r in records]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"导出演化记录: {len(records)} 条 -> {output_path}")


class EvolutionPatternExtractor:
    """演化模式提取器
    
    从历史演化记录中提取可复用的演化模式。
    """
    
    def __init__(
        self,
        pattern_storage: EvolutionPatternStorage,
        context_recorder: EvolutionContextRecorder
    ):
        self.pattern_storage = pattern_storage
        self.context_recorder = context_recorder
        self._extraction_rules: List[Dict[str, Any]] = []
    
    def add_extraction_rule(self, rule: Dict[str, Any]) -> None:
        self._extraction_rules.append(rule)
    
    def extract_patterns_from_records(
        self,
        min_occurrences: int = 3,
        min_success_rate: float = 0.6
    ) -> List[EvolutionPattern]:
        records = self.context_recorder.get_successful_records()
        
        pattern_groups = self._group_similar_records(records)
        
        extracted_patterns = []
        
        for group_key, group_records in pattern_groups.items():
            if len(group_records) < min_occurrences:
                continue
            
            success_rate = len(group_records) / len([
                r for r in self.context_recorder._records.values()
                if self._get_group_key(r) == group_key
            ])
            
            if success_rate < min_success_rate:
                continue
            
            pattern = self._create_pattern_from_group(group_key, group_records)
            if pattern:
                extracted_patterns.append(pattern)
        
        logger.info(f"提取演化模式: {len(extracted_patterns)} 个")
        return extracted_patterns
    
    def _group_similar_records(
        self,
        records: List[EvolutionRecord]
    ) -> Dict[str, List[EvolutionRecord]]:
        groups: Dict[str, List[EvolutionRecord]] = defaultdict(list)
        
        for record in records:
            group_key = self._get_group_key(record)
            groups[group_key].append(record)
        
        return groups
    
    def _get_group_key(self, record: EvolutionRecord) -> str:
        trigger_types = sorted([
            tc.condition_type.value 
            for tc in self.pattern_storage.get_pattern(record.pattern_id).trigger_conditions
        ]) if self.pattern_storage.get_pattern(record.pattern_id) else []
        
        operation_types = sorted([
            op.operation_type for op in record.operations
        ])
        
        return f"{record.context.evolution_type.value}|{','.join(trigger_types)}|{','.join(operation_types)}"
    
    def _create_pattern_from_group(
        self,
        group_key: str,
        records: List[EvolutionRecord]
    ) -> Optional[EvolutionPattern]:
        if not records:
            return None
        
        first_record = records[0]
        
        common_steps = self._extract_common_steps(records)
        
        common_triggers = self._extract_common_triggers(records)
        
        avg_effects = self._calculate_average_effects(records)
        
        parts = group_key.split('|')
        evolution_type = EvolutionType(parts[0]) if parts else first_record.context.evolution_type
        
        pattern = EvolutionPattern(
            pattern_id="",
            pattern_name=f"自动提取模式-{group_key[:20]}",
            evolution_type=evolution_type,
            description=f"从 {len(records)} 条成功记录中自动提取的演化模式",
            trigger_conditions=common_triggers,
            execution_steps=common_steps,
            effect_evaluations=[
                EffectEvaluation(
                    evaluation_id=f"EVAL-{metric}",
                    metric=EffectMetric(metric) if metric in [e.value for e in EffectMetric] else EffectMetric.CODE_QUALITY,
                    before_value=0,
                    after_value=value,
                    improvement=value,
                    evaluation_time=datetime.now().isoformat()
                )
                for metric, value in avg_effects.items()
            ],
            success_rate=len(records) / max(len(records), 1),
            usage_count=len(records),
            tags=["auto-extracted", evolution_type.value]
        )
        
        return pattern
    
    def _extract_common_steps(
        self,
        records: List[EvolutionRecord]
    ) -> List[EvolutionStep]:
        if not records:
            return []
        
        step_occurrences: Dict[str, int] = defaultdict(int)
        step_templates: Dict[str, EvolutionStep] = {}
        
        for record in records:
            seen_types = set()
            for op in record.operations:
                if op.operation_type not in seen_types:
                    step_occurrences[op.operation_type] += 1
                    if op.operation_type not in step_templates:
                        step_templates[op.operation_type] = EvolutionStep(
                            step_id=f"STEP-{op.operation_type}",
                            step_order=len(step_templates),
                            action=op.operation_type,
                            description=op.action,
                            parameters=op.parameters
                        )
                    seen_types.add(op.operation_type)
        
        threshold = len(records) * 0.7
        
        common_steps = []
        for op_type, count in sorted(step_occurrences.items(), key=lambda x: x[1], reverse=True):
            if count >= threshold:
                step = step_templates[op_type]
                step.step_order = len(common_steps)
                common_steps.append(step)
        
        return common_steps
    
    def _extract_common_triggers(
        self,
        records: List[EvolutionRecord]
    ) -> List[TriggerCondition]:
        trigger_counts: Dict[str, int] = defaultdict(int)
        
        for record in records:
            pattern = self.pattern_storage.get_pattern(record.pattern_id)
            if pattern:
                for trigger in pattern.trigger_conditions:
                    trigger_counts[trigger.condition_type.value] += 1
        
        threshold = len(records) * 0.5
        
        common_triggers = []
        for trigger_type, count in trigger_counts.items():
            if count >= threshold:
                common_triggers.append(TriggerCondition(
                    condition_id=f"TRIG-{trigger_type}",
                    condition_type=EvolutionTrigger(trigger_type),
                    description=f"常见触发条件: {trigger_type}"
                ))
        
        return common_triggers
    
    def _calculate_average_effects(
        self,
        records: List[EvolutionRecord]
    ) -> Dict[str, float]:
        effect_sum: Dict[str, float] = defaultdict(float)
        effect_count: Dict[str, int] = defaultdict(int)
        
        for record in records:
            if record.result:
                for metric, value in record.result.effects.items():
                    effect_sum[metric] += value
                    effect_count[metric] += 1
        
        return {
            metric: effect_sum[metric] / effect_count[metric]
            for metric in effect_sum
        }
    
    def suggest_pattern_for_context(
        self,
        context: EvolutionContext
    ) -> Optional[EvolutionPattern]:
        similar_records = self._find_similar_records(context)
        
        if not similar_records:
            return None
        
        successful = [r for r in similar_records if r.status == EvolutionStatus.COMPLETED]
        
        if len(successful) < 2:
            return None
        
        group_key = self._get_group_key(successful[0])
        pattern = self._create_pattern_from_group(group_key, successful)
        
        if pattern:
            pattern.pattern_name = f"建议模式-{context.skill_name}"
            pattern.description = f"基于 {len(successful)} 条相似记录为 {context.skill_name} 建议的演化模式"
        
        return pattern
    
    def _find_similar_records(
        self,
        context: EvolutionContext,
        limit: int = 10
    ) -> List[EvolutionRecord]:
        similar = []
        
        for record in self.context_recorder._records.values():
            score = 0.0
            
            if record.context.evolution_type == context.evolution_type:
                score += 0.5
            
            if record.context.skill_id == context.skill_id:
                score += 0.3
            
            common_deps = set(record.context.dependencies) & set(context.dependencies)
            if common_deps:
                score += 0.2 * len(common_deps) / max(len(record.context.dependencies), len(context.dependencies), 1)
            
            if score > 0:
                similar.append((record, score))
        
        similar.sort(key=lambda x: x[1], reverse=True)
        return [r for r, _ in similar[:limit]]


class EvolutionEffectPredictor:
    """演化效果预测器
    
    基于历史数据预测演化操作的效果。
    """
    
    def __init__(
        self,
        pattern_storage: EvolutionPatternStorage,
        context_recorder: EvolutionContextRecorder
    ):
        self.pattern_storage = pattern_storage
        self.context_recorder = context_recorder
        self._prediction_models: Dict[str, Any] = {}
        self._feature_weights: Dict[str, float] = {
            "pattern_success_rate": 0.3,
            "similar_context_success": 0.25,
            "historical_average": 0.25,
            "complexity_factor": 0.2
        }
    
    def set_feature_weights(self, weights: Dict[str, float]) -> None:
        self._feature_weights.update(weights)
    
    def predict_effect(
        self,
        pattern_id: str,
        context: EvolutionContext
    ) -> Dict[str, Any]:
        pattern = self.pattern_storage.get_pattern(pattern_id)
        if not pattern:
            return {
                "success_probability": 0.0,
                "predicted_effects": {},
                "confidence": 0.0,
                "warnings": ["模式不存在"]
            }
        
        features = self._extract_features(pattern, context)
        
        success_prob = self._calculate_success_probability(pattern, context, features)
        
        predicted_effects = self._predict_effects(pattern, context, features)
        
        confidence = self._calculate_confidence(pattern, context)
        
        warnings = self._generate_warnings(pattern, context, features)
        
        return {
            "success_probability": success_prob,
            "predicted_effects": predicted_effects,
            "confidence": confidence,
            "estimated_duration": self._estimate_duration(pattern, context),
            "warnings": warnings,
            "recommendations": self._generate_recommendations(pattern, context, features)
        }
    
    def _extract_features(
        self,
        pattern: EvolutionPattern,
        context: EvolutionContext
    ) -> Dict[str, float]:
        features = {}
        
        features["pattern_success_rate"] = pattern.success_rate
        
        features["pattern_usage_count"] = min(pattern.usage_count / 100, 1.0)
        
        similar_records = self._find_similar_historical_records(context)
        if similar_records:
            success_count = sum(1 for r in similar_records if r.status == EvolutionStatus.COMPLETED)
            features["similar_context_success"] = success_count / len(similar_records)
        else:
            features["similar_context_success"] = 0.5
        
        features["complexity_factor"] = 1.0 - min(len(pattern.execution_steps) / 20, 1.0)
        
        features["dependency_factor"] = 1.0 - min(len(context.dependencies) / 10, 1.0)
        
        return features
    
    def _find_similar_historical_records(
        self,
        context: EvolutionContext,
        limit: int = 20
    ) -> List[EvolutionRecord]:
        similar = []
        
        for record in self.context_recorder._records.values():
            score = 0.0
            
            if record.context.evolution_type == context.evolution_type:
                score += 0.5
            
            if record.context.skill_id == context.skill_id:
                score += 0.3
            
            if score > 0:
                similar.append((record, score))
        
        similar.sort(key=lambda x: x[1], reverse=True)
        return [r for r, _ in similar[:limit]]
    
    def _calculate_success_probability(
        self,
        pattern: EvolutionPattern,
        context: EvolutionContext,
        features: Dict[str, float]
    ) -> float:
        weights = self._feature_weights
        
        probability = 0.0
        total_weight = 0.0
        
        for feature, value in features.items():
            weight = weights.get(feature, 0.1)
            probability += value * weight
            total_weight += weight
        
        if total_weight > 0:
            probability /= total_weight
        
        return min(max(probability, 0.0), 1.0)
    
    def _predict_effects(
        self,
        pattern: EvolutionPattern,
        context: EvolutionContext,
        features: Dict[str, float]
    ) -> Dict[str, float]:
        predicted = {}
        
        for evaluation in pattern.effect_evaluations:
            base_improvement = evaluation.improvement
            
            adjustment = features.get("similar_context_success", 0.5) - 0.5
            
            predicted_improvement = base_improvement * (1 + adjustment * 0.2)
            
            predicted[evaluation.metric.value] = max(0, predicted_improvement)
        
        similar_records = self._find_similar_historical_records(context)
        if similar_records:
            effect_sum: Dict[str, float] = defaultdict(float)
            effect_count: Dict[str, int] = defaultdict(int)
            
            for record in similar_records:
                if record.result:
                    for metric, value in record.result.effects.items():
                        effect_sum[metric] += value
                        effect_count[metric] += 1
            
            for metric in effect_sum:
                if metric not in predicted:
                    predicted[metric] = effect_sum[metric] / effect_count[metric]
        
        return predicted
    
    def _calculate_confidence(
        self,
        pattern: EvolutionPattern,
        context: EvolutionContext
    ) -> float:
        confidence = 0.0
        
        if pattern.usage_count >= 10:
            confidence += 0.3
        elif pattern.usage_count >= 5:
            confidence += 0.2
        elif pattern.usage_count >= 1:
            confidence += 0.1
        
        similar_records = self._find_similar_historical_records(context)
        if len(similar_records) >= 5:
            confidence += 0.3
        elif len(similar_records) >= 2:
            confidence += 0.2
        elif len(similar_records) >= 1:
            confidence += 0.1
        
        if pattern.success_rate >= 0.8:
            confidence += 0.3
        elif pattern.success_rate >= 0.6:
            confidence += 0.2
        elif pattern.success_rate >= 0.4:
            confidence += 0.1
        
        if len(pattern.effect_evaluations) >= 3:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _estimate_duration(
        self,
        pattern: EvolutionPattern,
        context: EvolutionContext
    ) -> float:
        base_duration = pattern.avg_execution_time
        
        if base_duration == 0:
            base_duration = len(pattern.execution_steps) * 5
        
        complexity_factor = 1 + len(context.dependencies) * 0.1
        
        return base_duration * complexity_factor
    
    def _generate_warnings(
        self,
        pattern: EvolutionPattern,
        context: EvolutionContext,
        features: Dict[str, float]
    ) -> List[str]:
        warnings = []
        
        if pattern.success_rate < 0.5:
            warnings.append(f"模式成功率较低 ({pattern.success_rate:.1%})，建议谨慎使用")
        
        if pattern.usage_count < 3:
            warnings.append("模式使用次数较少，预测可能不够准确")
        
        if features.get("similar_context_success", 0) < 0.3:
            warnings.append("相似上下文的历史成功率较低")
        
        if len(context.dependencies) > 5:
            warnings.append(f"依赖项较多 ({len(context.dependencies)})，可能影响演化效果")
        
        for prereq in pattern.prerequisites:
            if prereq not in context.environment.get("available_resources", []):
                warnings.append(f"缺少前置条件: {prereq}")
        
        return warnings
    
    def _generate_recommendations(
        self,
        pattern: EvolutionPattern,
        context: EvolutionContext,
        features: Dict[str, float]
    ) -> List[str]:
        recommendations = []
        
        if features.get("pattern_success_rate", 0) >= 0.8:
            recommendations.append("该模式历史表现优秀，推荐使用")
        
        similar_records = self._find_similar_historical_records(context)
        if similar_records:
            successful = [r for r in similar_records if r.status == EvolutionStatus.COMPLETED]
            if successful:
                recommendations.append(f"发现 {len(successful)} 条相似的成功案例，可参考其操作步骤")
        
        if len(pattern.execution_steps) > 5:
            recommendations.append("演化步骤较多，建议分阶段执行并验证中间结果")
        
        if pattern.prerequisites:
            recommendations.append(f"执行前请确保满足前置条件: {', '.join(pattern.prerequisites)}")
        
        return recommendations
    
    def batch_predict(
        self,
        predictions: List[Tuple[str, EvolutionContext]]
    ) -> List[Dict[str, Any]]:
        results = []
        
        for pattern_id, context in predictions:
            result = self.predict_effect(pattern_id, context)
            results.append({
                "pattern_id": pattern_id,
                "context_id": context.context_id,
                **result
            })
        
        return results
    
    def compare_patterns(
        self,
        pattern_ids: List[str],
        context: EvolutionContext
    ) -> Dict[str, Any]:
        comparisons = []
        
        for pattern_id in pattern_ids:
            prediction = self.predict_effect(pattern_id, context)
            pattern = self.pattern_storage.get_pattern(pattern_id)
            
            comparisons.append({
                "pattern_id": pattern_id,
                "pattern_name": pattern.pattern_name if pattern else "未知",
                "success_probability": prediction["success_probability"],
                "confidence": prediction["confidence"],
                "estimated_duration": prediction["estimated_duration"],
                "predicted_effects": prediction["predicted_effects"],
                "warnings_count": len(prediction["warnings"])
            })
        
        comparisons.sort(key=lambda x: (
            -x["success_probability"],
            -x["confidence"],
            x["warnings_count"]
        ))
        
        return {
            "comparisons": comparisons,
            "recommended": comparisons[0]["pattern_id"] if comparisons else None,
            "recommendation_reason": "最高成功概率和置信度" if comparisons else ""
        }


class EvolutionKnowledgeManager:
    """演化知识管理器
    
    整合演化模式存储、上下文记录、模式提取和效果预测功能。
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./evolution_knowledge")
        
        self.pattern_storage = EvolutionPatternStorage(self.storage_path / "patterns")
        self.context_recorder = EvolutionContextRecorder(self.storage_path / "records")
        self.pattern_extractor = EvolutionPatternExtractor(self.pattern_storage, self.context_recorder)
        self.effect_predictor = EvolutionEffectPredictor(self.pattern_storage, self.context_recorder)
    
    def initialize(self) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.pattern_storage.initialize()
        self.context_recorder.initialize()
        logger.info("演化知识管理器初始化完成")
    
    def create_evolution_pattern(
        self,
        pattern_name: str,
        evolution_type: EvolutionType,
        description: str,
        trigger_conditions: Optional[List[TriggerCondition]] = None,
        execution_steps: Optional[List[EvolutionStep]] = None,
        tags: Optional[List[str]] = None
    ) -> EvolutionPattern:
        pattern = EvolutionPattern(
            pattern_id="",
            pattern_name=pattern_name,
            evolution_type=evolution_type,
            description=description,
            trigger_conditions=trigger_conditions or [],
            execution_steps=execution_steps or [],
            tags=tags or []
        )
        
        self.pattern_storage.save_pattern(pattern)
        return pattern
    
    def start_evolution(
        self,
        pattern_id: str,
        skill_id: str,
        skill_name: str,
        skill_version: str,
        trigger_reason: str,
        trigger_source: str = "manual",
        dependencies: Optional[List[str]] = None
    ) -> EvolutionRecord:
        context = EvolutionContext(
            context_id=f"CTX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            skill_id=skill_id,
            skill_name=skill_name,
            skill_version=skill_version,
            evolution_type=self.pattern_storage.get_pattern(pattern_id).evolution_type if self.pattern_storage.get_pattern(pattern_id) else EvolutionType.OPTIMIZATION,
            trigger_reason=trigger_reason,
            trigger_source=trigger_source,
            dependencies=dependencies or []
        )
        
        return self.context_recorder.start_evolution(pattern_id, context)
    
    def execute_step(
        self,
        record_id: str,
        step: EvolutionStep,
        executor: Callable[[EvolutionStep], Tuple[bool, Dict[str, Any]]]
    ) -> EvolutionOperation:
        operation_id = f"OP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{step.step_id}"
        
        operation = EvolutionOperation(
            operation_id=operation_id,
            operation_type=step.action,
            target=step.description,
            action=step.description,
            parameters=step.parameters
        )
        
        start_time = datetime.now()
        
        try:
            success, result_data = executor(step)
            operation.success = success
            operation.after_state = result_data
            if not success:
                operation.error_message = result_data.get("error", "执行失败")
        except Exception as e:
            operation.success = False
            operation.error_message = str(e)
        
        end_time = datetime.now()
        operation.execution_time = (end_time - start_time).total_seconds()
        
        self.context_recorder.add_operation(record_id, operation)
        
        return operation
    
    def complete_evolution(
        self,
        record_id: str,
        success: bool,
        effects: Optional[Dict[str, float]] = None,
        changes_made: Optional[List[str]] = None,
        side_effects: Optional[List[str]] = None
    ) -> None:
        result = EvolutionResult(
            result_id=f"RES-{record_id}",
            success=success,
            effects=effects or {},
            changes_made=changes_made or [],
            side_effects=side_effects or []
        )
        
        self.context_recorder.complete_evolution(record_id, result)
        
        record = self.context_recorder.get_record(record_id)
        if record:
            self.pattern_storage.update_usage_stats(
                record.pattern_id,
                success,
                record.duration
            )
    
    def predict_evolution(
        self,
        pattern_id: str,
        skill_id: str,
        skill_name: str,
        skill_version: str
    ) -> Dict[str, Any]:
        context = EvolutionContext(
            context_id=f"PRED-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            skill_id=skill_id,
            skill_name=skill_name,
            skill_version=skill_version,
            evolution_type=EvolutionType.OPTIMIZATION,
            trigger_reason="prediction",
            trigger_source="system"
        )
        
        return self.effect_predictor.predict_effect(pattern_id, context)
    
    def extract_new_patterns(self) -> List[EvolutionPattern]:
        new_patterns = self.pattern_extractor.extract_patterns_from_records()
        
        for pattern in new_patterns:
            self.pattern_storage.save_pattern(pattern)
        
        return new_patterns
    
    def get_evolution_recommendations(
        self,
        skill_id: str,
        skill_name: str,
        current_issues: List[str]
    ) -> List[Dict[str, Any]]:
        recommendations = []
        
        for issue in current_issues:
            trigger_type = self._map_issue_to_trigger(issue)
            
            patterns = self.pattern_storage.find_by_trigger(trigger_type)
            
            for pattern in patterns[:3]:
                context = EvolutionContext(
                    context_id=f"REC-{skill_id}",
                    skill_id=skill_id,
                    skill_name=skill_name,
                    skill_version="current",
                    evolution_type=pattern.evolution_type,
                    trigger_reason=issue,
                    trigger_source="recommendation"
                )
                
                prediction = self.effect_predictor.predict_effect(pattern.pattern_id, context)
                
                recommendations.append({
                    "pattern_id": pattern.pattern_id,
                    "pattern_name": pattern.pattern_name,
                    "evolution_type": pattern.evolution_type.value,
                    "trigger_issue": issue,
                    "success_probability": prediction["success_probability"],
                    "confidence": prediction["confidence"],
                    "predicted_effects": prediction["predicted_effects"],
                    "warnings": prediction["warnings"]
                })
        
        recommendations.sort(key=lambda x: (-x["success_probability"], -x["confidence"]))
        return recommendations
    
    def _map_issue_to_trigger(self, issue: str) -> EvolutionTrigger:
        issue_lower = issue.lower()
        
        if "性能" in issue_lower or "performance" in issue_lower:
            return EvolutionTrigger.PERFORMANCE_ISSUE
        elif "代码异味" in issue_lower or "code smell" in issue_lower:
            return EvolutionTrigger.CODE_SMELL
        elif "bug" in issue_lower or "错误" in issue_lower:
            return EvolutionTrigger.BUG_REPORT
        elif "需求" in issue_lower or "requirement" in issue_lower:
            return EvolutionTrigger.REQUIREMENT_CHANGE
        elif "依赖" in issue_lower or "dependency" in issue_lower:
            return EvolutionTrigger.DEPENDENCY_UPDATE
        else:
            return EvolutionTrigger.AUTOMATED_DETECTION
    
    def get_statistics(self) -> Dict[str, Any]:
        pattern_stats = self.pattern_storage.get_statistics()
        history_analysis = self.context_recorder.analyze_evolution_history()
        
        return {
            "patterns": pattern_stats,
            "history": history_analysis,
            "total_records": len(self.context_recorder._records)
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="知识库管理工具")
    parser.add_argument('--storage-type', choices=['json', 'sqlite', 'memory'], default='json')
    parser.add_argument('--storage-path', type=Path, default=Path('./kb_data'))
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    add_parser = subparsers.add_parser('add', help='添加知识')
    add_parser.add_argument('--type', required=True, choices=['fix_pattern', 'best_practice', 'diagnosis', 'code_pattern'])
    add_parser.add_argument('--title', required=True)
    add_parser.add_argument('--content', required=True)
    add_parser.add_argument('--category', default='')
    add_parser.add_argument('--tags', nargs='*', default=[])
    
    search_parser = subparsers.add_parser('search', help='搜索知识')
    search_parser.add_argument('query', help='搜索关键词')
    search_parser.add_argument('--mode', choices=['keyword', 'semantic', 'category', 'hybrid'], default='keyword')
    search_parser.add_argument('--limit', type=int, default=10)
    
    export_parser = subparsers.add_parser('export', help='导出知识库')
    export_parser.add_argument('output', help='输出文件路径')
    
    import_parser = subparsers.add_parser('import', help='导入知识库')
    import_parser.add_argument('input', help='输入文件路径')
    import_parser.add_argument('--strategy', choices=['skip', 'update', 'overwrite'], default='skip')
    
    subparsers.add_parser('stats', help='显示统计信息')
    
    args = parser.parse_args()
    
    kb = KnowledgeBase(
        storage_type=args.storage_type,
        storage_path=args.storage_path
    )
    
    if args.command == 'add':
        kt = KnowledgeType(args.type)
        item = KnowledgeItem(
            knowledge_id="",
            knowledge_type=kt,
            title=args.title,
            content=args.content,
            category=args.category,
            tags=args.tags
        )
        kid = kb.add_knowledge(item)
        print(f"添加成功: {kid}")
    
    elif args.command == 'search':
        mode = SearchMode(args.mode)
        results = kb.search(args.query, mode=mode, limit=args.limit)
        
        print(f"\n搜索结果 ({len(results)} 条):")
        for r in results:
            print(f"\n[{r.item.knowledge_id}] {r.item.title}")
            print(f"  类型: {r.item.knowledge_type.value}")
            print(f"  匹配度: {r.score:.2f}")
            print(f"  匹配字段: {', '.join(r.matched_fields)}")
    
    elif args.command == 'export':
        kb.export_knowledge(args.output)
        print(f"导出完成: {args.output}")
    
    elif args.command == 'import':
        stats = kb.import_knowledge(args.input, args.strategy)
        print(f"导入完成: {stats}")
    
    elif args.command == 'stats':
        stats = kb.get_statistics()
        print("\n知识库统计:")
        print(f"  总数: {stats['total_knowledge']}")
        print(f"  按类型: {stats['by_type']}")
        print(f"  按状态: {stats['by_status']}")
        print(f"  平均置信度: {stats['average_confidence']:.2f}")
        print(f"  总使用次数: {stats['total_usage']}")
    
    else:
        parser.print_help()


import unittest
import tempfile


class TestEvolutionDataModels(unittest.TestCase):
    """演化数据模型测试"""
    
    def test_evolution_step_creation(self):
        step = EvolutionStep(
            step_id="STEP-001",
            step_order=1,
            action="refactor",
            description="重构代码结构",
            parameters={"target": "module_a"},
            expected_outcome="提高代码可读性"
        )
        
        self.assertEqual(step.step_id, "STEP-001")
        self.assertEqual(step.action, "refactor")
        
        step_dict = step.to_dict()
        restored = EvolutionStep.from_dict(step_dict)
        self.assertEqual(restored.step_id, step.step_id)
    
    def test_trigger_condition_creation(self):
        condition = TriggerCondition(
            condition_id="TRIG-001",
            condition_type=EvolutionTrigger.PERFORMANCE_ISSUE,
            description="性能低于阈值",
            threshold=0.5
        )
        
        self.assertEqual(condition.condition_type, EvolutionTrigger.PERFORMANCE_ISSUE)
        
        condition_dict = condition.to_dict()
        restored = TriggerCondition.from_dict(condition_dict)
        self.assertEqual(restored.condition_type, EvolutionTrigger.PERFORMANCE_ISSUE)
    
    def test_effect_evaluation_creation(self):
        evaluation = EffectEvaluation(
            evaluation_id="EVAL-001",
            metric=EffectMetric.PERFORMANCE_GAIN,
            before_value=0.5,
            after_value=0.8,
            improvement=0.3,
            evaluation_time=datetime.now().isoformat()
        )
        
        self.assertEqual(evaluation.metric, EffectMetric.PERFORMANCE_GAIN)
        self.assertEqual(evaluation.improvement, 0.3)
    
    def test_evolution_pattern_creation(self):
        pattern = EvolutionPattern(
            pattern_id="",
            pattern_name="性能优化模式",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="用于性能优化的演化模式",
            trigger_conditions=[
                TriggerCondition(
                    condition_id="TRIG-001",
                    condition_type=EvolutionTrigger.PERFORMANCE_ISSUE,
                    description="性能问题"
                )
            ],
            execution_steps=[
                EvolutionStep(
                    step_id="STEP-001",
                    step_order=1,
                    action="analyze",
                    description="分析性能瓶颈"
                )
            ],
            tags=["performance", "optimization"]
        )
        
        self.assertEqual(pattern.evolution_type, EvolutionType.OPTIMIZATION)
        self.assertEqual(len(pattern.trigger_conditions), 1)
        self.assertEqual(len(pattern.execution_steps), 1)
        
        pattern_dict = pattern.to_dict()
        restored = EvolutionPattern.from_dict(pattern_dict)
        self.assertEqual(restored.evolution_type, EvolutionType.OPTIMIZATION)
    
    def test_evolution_context_creation(self):
        context = EvolutionContext(
            context_id="CTX-001",
            skill_id="skill-001",
            skill_name="测试技能",
            skill_version="1.0.0",
            evolution_type=EvolutionType.REFACTORING,
            trigger_reason="代码异味检测",
            trigger_source="automated"
        )
        
        self.assertEqual(context.skill_id, "skill-001")
        self.assertEqual(context.evolution_type, EvolutionType.REFACTORING)
    
    def test_evolution_operation_creation(self):
        operation = EvolutionOperation(
            operation_id="OP-001",
            operation_type="refactor",
            target="module_a",
            action="提取方法",
            parameters={"method_name": "new_method"},
            success=True
        )
        
        self.assertTrue(operation.success)
        self.assertEqual(operation.operation_type, "refactor")
    
    def test_evolution_result_creation(self):
        result = EvolutionResult(
            result_id="RES-001",
            success=True,
            changes_made=["重构完成"],
            effects={"performance_gain": 0.3},
            side_effects=[]
        )
        
        self.assertTrue(result.success)
        self.assertIn("performance_gain", result.effects)
    
    def test_evolution_record_creation(self):
        context = EvolutionContext(
            context_id="CTX-001",
            skill_id="skill-001",
            skill_name="测试技能",
            skill_version="1.0.0",
            evolution_type=EvolutionType.OPTIMIZATION,
            trigger_reason="性能问题",
            trigger_source="automated"
        )
        
        record = EvolutionRecord(
            record_id="REC-001",
            pattern_id="EVO-OPT-001",
            context=context,
            status=EvolutionStatus.IN_PROGRESS
        )
        
        self.assertEqual(record.status, EvolutionStatus.IN_PROGRESS)
        self.assertEqual(record.context.skill_id, "skill-001")


class TestEvolutionPatternStorage(unittest.TestCase):
    """演化模式存储测试"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage = EvolutionPatternStorage(Path(self.temp_dir))
        self.storage.initialize()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_get_pattern(self):
        pattern = EvolutionPattern(
            pattern_id="",
            pattern_name="测试模式",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="测试描述",
            tags=["test"]
        )
        
        pattern_id = self.storage.save_pattern(pattern)
        self.assertTrue(pattern_id.startswith("EVO-"))
        
        retrieved = self.storage.get_pattern(pattern_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.pattern_name, "测试模式")
    
    def test_find_by_type(self):
        pattern1 = EvolutionPattern(
            pattern_id="",
            pattern_name="优化模式",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="优化描述"
        )
        pattern2 = EvolutionPattern(
            pattern_id="",
            pattern_name="重构模式",
            evolution_type=EvolutionType.REFACTORING,
            description="重构描述"
        )
        
        self.storage.save_pattern(pattern1)
        self.storage.save_pattern(pattern2)
        
        opt_patterns = self.storage.find_by_type(EvolutionType.OPTIMIZATION)
        self.assertEqual(len(opt_patterns), 1)
        
        ref_patterns = self.storage.find_by_type(EvolutionType.REFACTORING)
        self.assertEqual(len(ref_patterns), 1)
    
    def test_find_by_trigger(self):
        pattern = EvolutionPattern(
            pattern_id="",
            pattern_name="性能优化模式",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="性能优化",
            trigger_conditions=[
                TriggerCondition(
                    condition_id="TRIG-001",
                    condition_type=EvolutionTrigger.PERFORMANCE_ISSUE,
                    description="性能问题"
                )
            ]
        )
        
        self.storage.save_pattern(pattern)
        
        found = self.storage.find_by_trigger(EvolutionTrigger.PERFORMANCE_ISSUE)
        self.assertEqual(len(found), 1)
    
    def test_find_by_tags(self):
        pattern1 = EvolutionPattern(
            pattern_id="",
            pattern_name="模式1",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="描述1",
            tags=["performance", "critical"]
        )
        pattern2 = EvolutionPattern(
            pattern_id="",
            pattern_name="模式2",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="描述2",
            tags=["performance", "normal"]
        )
        
        self.storage.save_pattern(pattern1)
        self.storage.save_pattern(pattern2)
        
        found = self.storage.find_by_tags(["performance"])
        self.assertEqual(len(found), 2)
        
        found = self.storage.find_by_tags(["performance", "critical"], match_all=True)
        self.assertEqual(len(found), 1)
    
    def test_search_patterns(self):
        pattern = EvolutionPattern(
            pattern_id="",
            pattern_name="性能优化模式",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="用于提升系统性能的优化模式",
            tags=["performance", "optimization"]
        )
        
        self.storage.save_pattern(pattern)
        
        results = self.storage.search_patterns("性能")
        self.assertEqual(len(results), 1)
        
        results = self.storage.search_patterns("optimization")
        self.assertEqual(len(results), 1)
    
    def test_update_usage_stats(self):
        pattern = EvolutionPattern(
            pattern_id="",
            pattern_name="测试模式",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="测试"
        )
        
        pattern_id = self.storage.save_pattern(pattern)
        
        self.storage.update_usage_stats(pattern_id, True, 5.0)
        
        updated = self.storage.get_pattern(pattern_id)
        self.assertEqual(updated.usage_count, 1)
        self.assertEqual(updated.success_rate, 1.0)
        self.assertEqual(updated.avg_execution_time, 5.0)
    
    def test_delete_pattern(self):
        pattern = EvolutionPattern(
            pattern_id="",
            pattern_name="待删除模式",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="测试删除"
        )
        
        pattern_id = self.storage.save_pattern(pattern)
        
        result = self.storage.delete_pattern(pattern_id)
        self.assertTrue(result)
        
        retrieved = self.storage.get_pattern(pattern_id)
        self.assertIsNone(retrieved)


class TestEvolutionContextRecorder(unittest.TestCase):
    """演化上下文记录器测试"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.recorder = EvolutionContextRecorder(Path(self.temp_dir))
        self.recorder.initialize()
        
        self.pattern_storage = EvolutionPatternStorage(Path(self.temp_dir) / "patterns")
        self.pattern_storage.initialize()
        
        self.pattern = EvolutionPattern(
            pattern_id="",
            pattern_name="测试模式",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="测试"
        )
        self.pattern_id = self.pattern_storage.save_pattern(self.pattern)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_start_evolution(self):
        context = EvolutionContext(
            context_id="CTX-001",
            skill_id="skill-001",
            skill_name="测试技能",
            skill_version="1.0.0",
            evolution_type=EvolutionType.OPTIMIZATION,
            trigger_reason="测试",
            trigger_source="manual"
        )
        
        record = self.recorder.start_evolution(self.pattern_id, context)
        
        self.assertEqual(record.status, EvolutionStatus.IN_PROGRESS)
        self.assertEqual(record.context.skill_id, "skill-001")
    
    def test_add_operation(self):
        context = EvolutionContext(
            context_id="CTX-001",
            skill_id="skill-001",
            skill_name="测试技能",
            skill_version="1.0.0",
            evolution_type=EvolutionType.OPTIMIZATION,
            trigger_reason="测试",
            trigger_source="manual"
        )
        
        record = self.recorder.start_evolution(self.pattern_id, context)
        
        operation = EvolutionOperation(
            operation_id="OP-001",
            operation_type="analyze",
            target="module_a",
            action="分析模块",
            success=True
        )
        
        self.recorder.add_operation(record.record_id, operation)
        
        updated = self.recorder.get_record(record.record_id)
        self.assertEqual(len(updated.operations), 1)
    
    def test_complete_evolution(self):
        context = EvolutionContext(
            context_id="CTX-001",
            skill_id="skill-001",
            skill_name="测试技能",
            skill_version="1.0.0",
            evolution_type=EvolutionType.OPTIMIZATION,
            trigger_reason="测试",
            trigger_source="manual"
        )
        
        record = self.recorder.start_evolution(self.pattern_id, context)
        
        result = EvolutionResult(
            result_id="RES-001",
            success=True,
            effects={"performance_gain": 0.2}
        )
        
        self.recorder.complete_evolution(record.record_id, result)
        
        completed = self.recorder.get_record(record.record_id)
        self.assertEqual(completed.status, EvolutionStatus.COMPLETED)
        self.assertTrue(completed.result.success)
    
    def test_get_records_by_skill(self):
        context = EvolutionContext(
            context_id="CTX-001",
            skill_id="skill-001",
            skill_name="测试技能",
            skill_version="1.0.0",
            evolution_type=EvolutionType.OPTIMIZATION,
            trigger_reason="测试",
            trigger_source="manual"
        )
        
        self.recorder.start_evolution(self.pattern_id, context)
        
        records = self.recorder.get_records_by_skill("skill-001")
        self.assertEqual(len(records), 1)
    
    def test_analyze_evolution_history(self):
        context = EvolutionContext(
            context_id="CTX-001",
            skill_id="skill-001",
            skill_name="测试技能",
            skill_version="1.0.0",
            evolution_type=EvolutionType.OPTIMIZATION,
            trigger_reason="测试",
            trigger_source="manual"
        )
        
        record = self.recorder.start_evolution(self.pattern_id, context)
        
        result = EvolutionResult(
            result_id="RES-001",
            success=True,
            effects={"performance_gain": 0.2}
        )
        
        self.recorder.complete_evolution(record.record_id, result)
        
        analysis = self.recorder.analyze_evolution_history("skill-001")
        self.assertEqual(analysis["total"], 1)
        self.assertEqual(analysis["success_rate"], 1.0)


class TestEvolutionEffectPredictor(unittest.TestCase):
    """演化效果预测器测试"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        self.pattern_storage = EvolutionPatternStorage(Path(self.temp_dir) / "patterns")
        self.pattern_storage.initialize()
        
        self.context_recorder = EvolutionContextRecorder(Path(self.temp_dir) / "records")
        self.context_recorder.initialize()
        
        self.predictor = EvolutionEffectPredictor(self.pattern_storage, self.context_recorder)
        
        self.pattern = EvolutionPattern(
            pattern_id="",
            pattern_name="性能优化模式",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="性能优化",
            success_rate=0.8,
            usage_count=10,
            avg_execution_time=5.0,
            effect_evaluations=[
                EffectEvaluation(
                    evaluation_id="EVAL-001",
                    metric=EffectMetric.PERFORMANCE_GAIN,
                    before_value=0.5,
                    after_value=0.8,
                    improvement=0.3,
                    evaluation_time=datetime.now().isoformat()
                )
            ]
        )
        self.pattern_id = self.pattern_storage.save_pattern(self.pattern)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_predict_effect(self):
        context = EvolutionContext(
            context_id="CTX-001",
            skill_id="skill-001",
            skill_name="测试技能",
            skill_version="1.0.0",
            evolution_type=EvolutionType.OPTIMIZATION,
            trigger_reason="性能问题",
            trigger_source="automated"
        )
        
        prediction = self.predictor.predict_effect(self.pattern_id, context)
        
        self.assertIn("success_probability", prediction)
        self.assertIn("predicted_effects", prediction)
        self.assertIn("confidence", prediction)
        self.assertIn("warnings", prediction)
        
        self.assertGreater(prediction["success_probability"], 0)
        self.assertGreater(prediction["confidence"], 0)
    
    def test_predict_nonexistent_pattern(self):
        context = EvolutionContext(
            context_id="CTX-001",
            skill_id="skill-001",
            skill_name="测试技能",
            skill_version="1.0.0",
            evolution_type=EvolutionType.OPTIMIZATION,
            trigger_reason="测试",
            trigger_source="manual"
        )
        
        prediction = self.predictor.predict_effect("NONEXISTENT", context)
        
        self.assertEqual(prediction["success_probability"], 0.0)
        self.assertIn("模式不存在", prediction["warnings"])
    
    def test_compare_patterns(self):
        pattern2 = EvolutionPattern(
            pattern_id="",
            pattern_name="重构模式",
            evolution_type=EvolutionType.REFACTORING,
            description="重构",
            success_rate=0.6,
            usage_count=5
        )
        pattern_id2 = self.pattern_storage.save_pattern(pattern2)
        
        context = EvolutionContext(
            context_id="CTX-001",
            skill_id="skill-001",
            skill_name="测试技能",
            skill_version="1.0.0",
            evolution_type=EvolutionType.OPTIMIZATION,
            trigger_reason="测试",
            trigger_source="manual"
        )
        
        comparison = self.predictor.compare_patterns([self.pattern_id, pattern_id2], context)
        
        self.assertIn("comparisons", comparison)
        self.assertEqual(len(comparison["comparisons"]), 2)
        self.assertIn("recommended", comparison)


class TestEvolutionKnowledgeManager(unittest.TestCase):
    """演化知识管理器测试"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = EvolutionKnowledgeManager(Path(self.temp_dir))
        self.manager.initialize()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_evolution_pattern(self):
        pattern = self.manager.create_evolution_pattern(
            pattern_name="测试模式",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="测试描述",
            tags=["test"]
        )
        
        self.assertIsNotNone(pattern.pattern_id)
        self.assertEqual(pattern.pattern_name, "测试模式")
    
    def test_start_and_complete_evolution(self):
        pattern = self.manager.create_evolution_pattern(
            pattern_name="测试模式",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="测试描述"
        )
        
        record = self.manager.start_evolution(
            pattern_id=pattern.pattern_id,
            skill_id="skill-001",
            skill_name="测试技能",
            skill_version="1.0.0",
            trigger_reason="性能问题"
        )
        
        self.assertEqual(record.status, EvolutionStatus.IN_PROGRESS)
        
        self.manager.complete_evolution(
            record_id=record.record_id,
            success=True,
            effects={"performance_gain": 0.2},
            changes_made=["优化完成"]
        )
        
        completed = self.manager.context_recorder.get_record(record.record_id)
        self.assertEqual(completed.status, EvolutionStatus.COMPLETED)
    
    def test_predict_evolution(self):
        pattern = self.manager.create_evolution_pattern(
            pattern_name="测试模式",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="测试描述",
            execution_steps=[
                EvolutionStep(
                    step_id="STEP-001",
                    step_order=1,
                    action="analyze",
                    description="分析"
                )
            ]
        )
        
        prediction = self.manager.predict_evolution(
            pattern_id=pattern.pattern_id,
            skill_id="skill-001",
            skill_name="测试技能",
            skill_version="1.0.0"
        )
        
        self.assertIn("success_probability", prediction)
    
    def test_get_evolution_recommendations(self):
        pattern = self.manager.create_evolution_pattern(
            pattern_name="性能优化模式",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="性能优化",
            trigger_conditions=[
                TriggerCondition(
                    condition_id="TRIG-001",
                    condition_type=EvolutionTrigger.PERFORMANCE_ISSUE,
                    description="性能问题"
                )
            ]
        )
        
        recommendations = self.manager.get_evolution_recommendations(
            skill_id="skill-001",
            skill_name="测试技能",
            current_issues=["性能下降"]
        )
        
        self.assertIsInstance(recommendations, list)
    
    def test_get_statistics(self):
        pattern = self.manager.create_evolution_pattern(
            pattern_name="测试模式",
            evolution_type=EvolutionType.OPTIMIZATION,
            description="测试描述"
        )
        
        stats = self.manager.get_statistics()
        
        self.assertIn("patterns", stats)
        self.assertIn("history", stats)
        self.assertEqual(stats["patterns"]["total_patterns"], 1)


def run_evolution_tests():
    """运行演化功能测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestEvolutionDataModels))
    suite.addTests(loader.loadTestsFromTestCase(TestEvolutionPatternStorage))
    suite.addTests(loader.loadTestsFromTestCase(TestEvolutionContextRecorder))
    suite.addTests(loader.loadTestsFromTestCase(TestEvolutionEffectPredictor))
    suite.addTests(loader.loadTestsFromTestCase(TestEvolutionKnowledgeManager))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()
