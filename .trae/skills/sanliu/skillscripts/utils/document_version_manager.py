#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档版本管理器 - Sanliu 技能

功能：
- 文档快照功能：创建、存储、压缩和恢复文档快照
- 文档差异对比：文本差异对比、结构化文档对比、差异报告生成
- 文档回滚功能：版本回滚、选择性回滚、回滚预览
- 文档索引管理：索引创建、更新、搜索

使用方法：
    from document_version_manager import (
        DocumentSnapshotManager,
        DocumentDiffAnalyzer,
        DocumentRollbackManager,
        DocumentIndexManager
    )
    
    # 创建快照管理器
    snapshot_mgr = DocumentSnapshotManager(base_path)
    snapshot = snapshot_mgr.create_snapshot(doc_path, description="初始版本")
    
    # 差异对比
    diff_analyzer = DocumentDiffAnalyzer()
    diff_report = diff_analyzer.compare_files(old_content, new_content)
    
    # 版本回滚
    rollback_mgr = DocumentRollbackManager(base_path)
    rollback_mgr.rollback_to_version(doc_id, target_version)
    
    # 索引管理
    index_mgr = DocumentIndexManager(base_path)
    index_mgr.create_index(doc_path)
    results = index_mgr.search("关键词")
"""

import gzip
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import threading
import zlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from difflib import SequenceMatcher, unified_diff
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

try:
    from path_config_manager import PathConfigManager
    PATH_CONFIG_AVAILABLE = True
except ImportError:
    PATH_CONFIG_AVAILABLE = False
    PathConfigManager = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SnapshotStatus(Enum):
    """快照状态枚举"""
    CREATED = "created"
    COMPRESSED = "compressed"
    RESTORED = "restored"
    DEPRECATED = "deprecated"
    CORRUPTED = "corrupted"


class DiffType(Enum):
    """差异类型枚举"""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class RollbackStatus(Enum):
    """回滚状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IndexStatus(Enum):
    """索引状态枚举"""
    ACTIVE = "active"
    OUTDATED = "outdated"
    REBUILDING = "rebuilding"
    DISABLED = "disabled"


class CompressionType(Enum):
    """压缩类型枚举"""
    NONE = "none"
    GZIP = "gzip"
    ZLIB = "zlib"


class DocumentType(Enum):
    """文档类型枚举"""
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    TEXT = "text"
    HTML = "html"
    XML = "xml"
    CODE = "code"
    BINARY = "binary"
    OTHER = "other"


@dataclass
class SnapshotMetadata:
    """快照元数据"""
    snapshot_id: str
    document_id: str
    document_name: str
    version: str
    created_at: str
    file_path: str
    content_path: str
    checksum: str
    size_bytes: int
    compressed_size: int = 0
    compression_type: str = CompressionType.NONE.value
    status: str = SnapshotStatus.CREATED.value
    description: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    is_auto_snapshot: bool = False
    parent_snapshot_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiffEntry:
    """差异条目"""
    line_number: int
    diff_type: str
    old_content: str
    new_content: str
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)


@dataclass
class DiffReport:
    """差异报告"""
    document_id: str
    old_version: str
    new_version: str
    generated_at: str
    similarity: float
    total_changes: int
    lines_added: int
    lines_removed: int
    lines_modified: int
    entries: List[DiffEntry] = field(default_factory=list)
    unified_diff: str = ""
    summary: str = ""
    structural_changes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RollbackPlan:
    """回滚计划"""
    plan_id: str
    document_id: str
    current_version: str
    target_version: str
    created_at: str
    status: str = RollbackStatus.PENDING.value
    affected_files: List[str] = field(default_factory=list)
    backup_snapshot_id: Optional[str] = None
    estimated_changes: int = 0
    description: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class RollbackResult:
    """回滚结果"""
    plan_id: str
    document_id: str
    success: bool
    message: str
    completed_at: str
    restored_files: List[str] = field(default_factory=list)
    failed_files: List[str] = field(default_factory=list)
    backup_created: bool = False
    backup_snapshot_id: Optional[str] = None


@dataclass
class IndexEntry:
    """索引条目"""
    document_id: str
    document_name: str
    file_path: str
    version: str
    indexed_at: str
    checksum: str
    size_bytes: int
    document_type: str
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    content_hash: Optional[str] = None


@dataclass
class SearchResult:
    """搜索结果"""
    document_id: str
    document_name: str
    file_path: str
    score: float
    matched_keywords: List[str] = field(default_factory=list)
    highlights: List[str] = field(default_factory=list)
    snippet: Optional[str] = None


class DocumentVersionError(Exception):
    """文档版本管理异常基类"""
    pass


class SnapshotError(DocumentVersionError):
    """快照操作异常"""
    pass


class DiffError(DocumentVersionError):
    """差异对比异常"""
    pass


class RollbackError(DocumentVersionError):
    """回滚操作异常"""
    pass


class IndexError(DocumentVersionError):
    """索引操作异常"""
    pass


class DocumentSnapshotManager:
    """
    文档快照管理器
    
    功能：
    - 创建文档快照
    - 快照存储和压缩
    - 快照恢复
    - 快照清理
    """
    
    SNAPSHOT_DIR = "snapshots"
    METADATA_DIR = "snapshot_metadata"
    MAX_SNAPSHOTS_PER_DOC = 50
    DEFAULT_COMPRESSION = CompressionType.GZIP
    
    def __init__(
        self,
        base_path: Optional[Path] = None,
        compression: CompressionType = CompressionType.GZIP,
        max_snapshots: int = 50
    ):
        """
        初始化快照管理器
        
        Args:
            base_path: 基础路径，None则使用 PathConfigManager
            compression: 压缩类型
            max_snapshots: 每个文档最大快照数
        """
        if base_path is None:
            if PATH_CONFIG_AVAILABLE and PathConfigManager:
                self.base_path = PathConfigManager(auto_detect=True).get_base_path()
            else:
                self.base_path = Path.cwd()
        else:
            self.base_path = Path(base_path)
        
        self.snapshot_dir = self.base_path / self.SNAPSHOT_DIR
        self.metadata_dir = self.base_path / self.METADATA_DIR
        self.compression = compression
        self.max_snapshots = max_snapshots
        self._lock = threading.Lock()
        
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """确保目录存在"""
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_snapshot_id(self, document_id: str) -> str:
        """生成快照ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        hash_part = hashlib.md5(f"{document_id}{timestamp}".encode()).hexdigest()[:8]
        return f"snap_{document_id[:12]}_{timestamp}_{hash_part}"
    
    def _calculate_checksum(self, content: bytes) -> str:
        """计算校验和"""
        return hashlib.sha256(content).hexdigest()
    
    def _compress_content(self, content: bytes) -> Tuple[bytes, CompressionType]:
        """压缩内容"""
        if self.compression == CompressionType.NONE:
            return content, CompressionType.NONE
        elif self.compression == CompressionType.GZIP:
            return gzip.compress(content), CompressionType.GZIP
        elif self.compression == CompressionType.ZLIB:
            return zlib.compress(content), CompressionType.ZLIB
        return content, CompressionType.NONE
    
    def _decompress_content(self, content: bytes, compression_type: CompressionType) -> bytes:
        """解压内容"""
        if compression_type == CompressionType.NONE:
            return content
        elif compression_type == CompressionType.GZIP:
            return gzip.decompress(content)
        elif compression_type == CompressionType.ZLIB:
            return zlib.decompress(content)
        return content
    
    def create_snapshot(
        self,
        file_path: Union[str, Path],
        document_id: Optional[str] = None,
        version: str = "1.0.0",
        description: Optional[str] = None,
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_auto: bool = False,
        parent_snapshot_id: Optional[str] = None
    ) -> SnapshotMetadata:
        """
        创建文档快照
        
        Args:
            file_path: 文档文件路径
            document_id: 文档ID，None则自动生成
            version: 文档版本
            description: 快照描述
            author: 作者
            tags: 标签列表
            is_auto: 是否为自动快照
            parent_snapshot_id: 父快照ID
            
        Returns:
            快照元数据
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise SnapshotError(f"文件不存在: {file_path}")
        
        if document_id is None:
            document_id = hashlib.md5(str(file_path.absolute()).encode()).hexdigest()[:16]
        
        document_name = file_path.stem
        snapshot_id = self._generate_snapshot_id(document_id)
        
        content = file_path.read_bytes()
        checksum = self._calculate_checksum(content)
        size_bytes = len(content)
        
        compressed_content, compression_type = self._compress_content(content)
        compressed_size = len(compressed_content)
        
        content_path = self.snapshot_dir / f"{snapshot_id}.dat"
        content_path.write_bytes(compressed_content)
        
        metadata = SnapshotMetadata(
            snapshot_id=snapshot_id,
            document_id=document_id,
            document_name=document_name,
            version=version,
            created_at=datetime.now().isoformat(),
            file_path=str(file_path.absolute()),
            content_path=str(content_path),
            checksum=checksum,
            size_bytes=size_bytes,
            compressed_size=compressed_size,
            compression_type=compression_type.value,
            status=SnapshotStatus.COMPRESSED.value if compression_type != CompressionType.NONE else SnapshotStatus.CREATED.value,
            description=description,
            author=author,
            tags=tags or [],
            is_auto_snapshot=is_auto,
            parent_snapshot_id=parent_snapshot_id
        )
        
        self._save_metadata(metadata)
        self._cleanup_old_snapshots(document_id)
        
        logger.info(f"创建快照: {snapshot_id} (文档: {document_name}, 压缩率: {compressed_size/size_bytes:.1%})")
        return metadata
    
    def _save_metadata(self, metadata: SnapshotMetadata) -> None:
        """保存快照元数据"""
        meta_path = self.metadata_dir / f"{metadata.snapshot_id}.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(metadata), f, indent=2, ensure_ascii=False)
    
    def load_metadata(self, snapshot_id: str) -> Optional[SnapshotMetadata]:
        """加载快照元数据"""
        meta_path = self.metadata_dir / f"{snapshot_id}.json"
        
        if not meta_path.exists():
            return None
        
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SnapshotMetadata(**data)
        except Exception as e:
            logger.error(f"加载快照元数据失败: {e}")
            return None
    
    def restore_snapshot(
        self,
        snapshot_id: str,
        target_path: Optional[Union[str, Path]] = None,
        create_backup: bool = True
    ) -> Tuple[bool, str]:
        """
        从快照恢复文档
        
        Args:
            snapshot_id: 快照ID
            target_path: 目标路径，None则恢复到原路径
            create_backup: 是否创建备份
            
        Returns:
            (是否成功, 消息) 元组
        """
        metadata = self.load_metadata(snapshot_id)
        
        if metadata is None:
            return False, f"快照不存在: {snapshot_id}"
        
        content_path = Path(metadata.content_path)
        
        if not content_path.exists():
            return False, f"快照内容文件不存在: {content_path}"
        
        compressed_content = content_path.read_bytes()
        compression_type = CompressionType(metadata.compression_type)
        
        try:
            content = self._decompress_content(compressed_content, compression_type)
        except Exception as e:
            return False, f"解压快照内容失败: {e}"
        
        current_checksum = self._calculate_checksum(content)
        if current_checksum != metadata.checksum:
            return False, "快照校验和不匹配，可能已损坏"
        
        if target_path is None:
            target_path = Path(metadata.file_path)
        else:
            target_path = Path(target_path)
        
        if create_backup and target_path.exists():
            backup_path = target_path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{target_path.suffix}")
            shutil.copy2(target_path, backup_path)
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)
        
        metadata.status = SnapshotStatus.RESTORED.value
        self._save_metadata(metadata)
        
        logger.info(f"恢复快照: {snapshot_id} -> {target_path}")
        return True, f"已恢复文档: {metadata.document_name} (版本: {metadata.version})"
    
    def list_snapshots(
        self,
        document_id: Optional[str] = None,
        status: Optional[SnapshotStatus] = None,
        limit: int = 100
    ) -> List[SnapshotMetadata]:
        """
        列出快照
        
        Args:
            document_id: 文档ID过滤
            status: 状态过滤
            limit: 返回数量限制
            
        Returns:
            快照元数据列表
        """
        snapshots = []
        
        for meta_file in self.metadata_dir.glob("*.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                snapshot = SnapshotMetadata(**data)
                
                if document_id and snapshot.document_id != document_id:
                    continue
                if status and snapshot.status != status.value:
                    continue
                
                snapshots.append(snapshot)
            except Exception:
                pass
        
        snapshots.sort(key=lambda x: x.created_at, reverse=True)
        return snapshots[:limit]
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        try:
            meta_path = self.metadata_dir / f"{snapshot_id}.json"
            content_path = self.snapshot_dir / f"{snapshot_id}.dat"
            
            if meta_path.exists():
                meta_path.unlink()
            if content_path.exists():
                content_path.unlink()
            
            logger.info(f"删除快照: {snapshot_id}")
            return True
        except Exception as e:
            logger.error(f"删除快照失败: {e}")
            return False
    
    def _cleanup_old_snapshots(self, document_id: str) -> None:
        """清理旧快照"""
        snapshots = self.list_snapshots(document_id=document_id, limit=self.max_snapshots + 10)
        
        if len(snapshots) > self.max_snapshots:
            to_remove = snapshots[self.max_snapshots:]
            for snapshot in to_remove:
                if not snapshot.is_auto_snapshot:
                    continue
                self.delete_snapshot(snapshot.snapshot_id)
    
    def get_snapshot_info(self, snapshot_id: str) -> Dict[str, Any]:
        """获取快照详细信息"""
        metadata = self.load_metadata(snapshot_id)
        
        if metadata is None:
            return {"error": "快照不存在"}
        
        content_path = Path(metadata.content_path)
        
        info = asdict(metadata)
        info["content_exists"] = content_path.exists()
        info["compression_ratio"] = (
            metadata.compressed_size / metadata.size_bytes 
            if metadata.size_bytes > 0 else 0
        )
        
        return info


class DocumentDiffAnalyzer:
    """
    文档差异分析器
    
    功能：
    - 文本差异对比
    - 结构化文档对比
    - 差异报告生成
    """
    
    def __init__(
        self,
        context_lines: int = 3,
        ignore_whitespace: bool = False,
        ignore_case: bool = False
    ):
        """
        初始化差异分析器
        
        Args:
            context_lines: 上下文行数
            ignore_whitespace: 是否忽略空白字符
            ignore_case: 是否忽略大小写
        """
        self.context_lines = context_lines
        self.ignore_whitespace = ignore_whitespace
        self.ignore_case = ignore_case
    
    def _normalize_content(self, content: str) -> str:
        """标准化内容"""
        if self.ignore_case:
            content = content.lower()
        if self.ignore_whitespace:
            content = re.sub(r'\s+', ' ', content)
        return content
    
    def _detect_document_type(self, file_path: str) -> DocumentType:
        """检测文档类型"""
        ext = Path(file_path).suffix.lower()
        
        type_map = {
            '.md': DocumentType.MARKDOWN,
            '.markdown': DocumentType.MARKDOWN,
            '.json': DocumentType.JSON,
            '.yaml': DocumentType.YAML,
            '.yml': DocumentType.YAML,
            '.txt': DocumentType.TEXT,
            '.html': DocumentType.HTML,
            '.htm': DocumentType.HTML,
            '.xml': DocumentType.XML,
            '.py': DocumentType.CODE,
            '.js': DocumentType.CODE,
            '.ts': DocumentType.CODE,
            '.java': DocumentType.CODE,
            '.cpp': DocumentType.CODE,
            '.c': DocumentType.CODE,
        }
        
        return type_map.get(ext, DocumentType.OTHER)
    
    def compare_files(
        self,
        old_content: str,
        new_content: str,
        file_path: str = "",
        old_version: str = "old",
        new_version: str = "new"
    ) -> DiffReport:
        """
        对比两个文件内容
        
        Args:
            old_content: 旧内容
            new_content: 新内容
            file_path: 文件路径
            old_version: 旧版本号
            new_version: 新版本号
            
        Returns:
            差异报告
        """
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        normalized_old = self._normalize_content(old_content)
        normalized_new = self._normalize_content(new_content)
        
        similarity = self._calculate_similarity(normalized_old, normalized_new)
        
        entries = self._analyze_diff_entries(old_lines, new_lines)
        
        unified = self._generate_unified_diff(old_lines, new_lines, file_path)
        
        lines_added = sum(1 for e in entries if e.diff_type == DiffType.ADDED.value)
        lines_removed = sum(1 for e in entries if e.diff_type == DiffType.REMOVED.value)
        lines_modified = sum(1 for e in entries if e.diff_type == DiffType.MODIFIED.value)
        
        summary = self._generate_summary(entries, similarity)
        
        doc_type = self._detect_document_type(file_path)
        structural_changes = self._analyze_structural_changes(
            old_content, new_content, doc_type
        )
        
        document_id = hashlib.md5(file_path.encode()).hexdigest()[:16]
        
        return DiffReport(
            document_id=document_id,
            old_version=old_version,
            new_version=new_version,
            generated_at=datetime.now().isoformat(),
            similarity=similarity,
            total_changes=len(entries),
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_modified=lines_modified,
            entries=entries,
            unified_diff=unified,
            summary=summary,
            structural_changes=structural_changes
        )
    
    def _calculate_similarity(self, old_content: str, new_content: str) -> float:
        """计算相似度"""
        if not old_content and not new_content:
            return 1.0
        if not old_content or not new_content:
            return 0.0
        
        matcher = SequenceMatcher(None, old_content, new_content)
        return matcher.ratio()
    
    def _analyze_diff_entries(
        self,
        old_lines: List[str],
        new_lines: List[str]
    ) -> List[DiffEntry]:
        """分析差异条目"""
        entries = []
        matcher = SequenceMatcher(None, old_lines, new_lines)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            
            diff_type = {
                'replace': DiffType.MODIFIED.value,
                'delete': DiffType.REMOVED.value,
                'insert': DiffType.ADDED.value
            }.get(tag, DiffType.MODIFIED.value)
            
            old_content = ''.join(old_lines[i1:i2]) if i1 < i2 else ''
            new_content = ''.join(new_lines[j1:j2]) if j1 < j2 else ''
            
            line_number = max(i1, j1) + 1
            
            context_before = []
            context_after = []
            
            if i1 > 0:
                context_before = old_lines[max(0, i1 - self.context_lines):i1]
            if i2 < len(old_lines):
                context_after = old_lines[i2:min(len(old_lines), i2 + self.context_lines)]
            
            entries.append(DiffEntry(
                line_number=line_number,
                diff_type=diff_type,
                old_content=old_content,
                new_content=new_content,
                context_before=[line.rstrip('\n\r') for line in context_before],
                context_after=[line.rstrip('\n\r') for line in context_after]
            ))
        
        return entries
    
    def _generate_unified_diff(
        self,
        old_lines: List[str],
        new_lines: List[str],
        file_path: str
    ) -> str:
        """生成统一差异格式"""
        diff = unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=""
        )
        return ''.join(diff)
    
    def _generate_summary(
        self,
        entries: List[DiffEntry],
        similarity: float
    ) -> str:
        """生成差异摘要"""
        if not entries:
            return "无差异"
        
        added = sum(1 for e in entries if e.diff_type == DiffType.ADDED.value)
        removed = sum(1 for e in entries if e.diff_type == DiffType.REMOVED.value)
        modified = sum(1 for e in entries if e.diff_type == DiffType.MODIFIED.value)
        
        parts = []
        if added > 0:
            parts.append(f"新增 {added} 行")
        if removed > 0:
            parts.append(f"删除 {removed} 行")
        if modified > 0:
            parts.append(f"修改 {modified} 处")
        
        summary = f"相似度: {similarity:.1%}，" + "、".join(parts)
        return summary
    
    def _analyze_structural_changes(
        self,
        old_content: str,
        new_content: str,
        doc_type: DocumentType
    ) -> List[Dict[str, Any]]:
        """分析结构化变更"""
        changes = []
        
        if doc_type == DocumentType.MARKDOWN:
            changes.extend(self._analyze_markdown_structure(old_content, new_content))
        elif doc_type == DocumentType.JSON:
            changes.extend(self._analyze_json_structure(old_content, new_content))
        
        return changes
    
    def _analyze_markdown_structure(
        self,
        old_content: str,
        new_content: str
    ) -> List[Dict[str, Any]]:
        """分析 Markdown 结构变更"""
        changes = []
        
        old_headers = set(re.findall(r'^(#{1,6})\s+(.+)$', old_content, re.MULTILINE))
        new_headers = set(re.findall(r'^(#{1,6})\s+(.+)$', new_content, re.MULTILINE))
        
        added_headers = new_headers - old_headers
        removed_headers = old_headers - new_headers
        
        for level, title in added_headers:
            changes.append({
                "type": "header_added",
                "level": len(level),
                "title": title
            })
        
        for level, title in removed_headers:
            changes.append({
                "type": "header_removed",
                "level": len(level),
                "title": title
            })
        
        return changes
    
    def _analyze_json_structure(
        self,
        old_content: str,
        new_content: str
    ) -> List[Dict[str, Any]]:
        """分析 JSON 结构变更"""
        changes = []
        
        try:
            old_data = json.loads(old_content)
            new_data = json.loads(new_content)
            
            old_keys = set(self._get_json_keys(old_data))
            new_keys = set(self._get_json_keys(new_data))
            
            added_keys = new_keys - old_keys
            removed_keys = old_keys - new_keys
            
            for key in added_keys:
                changes.append({"type": "key_added", "key": key})
            
            for key in removed_keys:
                changes.append({"type": "key_removed", "key": key})
        except json.JSONDecodeError:
            pass
        
        return changes
    
    def _get_json_keys(
        self,
        data: Any,
        prefix: str = ""
    ) -> Generator[str, None, None]:
        """获取 JSON 所有键"""
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                yield full_key
                yield from self._get_json_keys(value, full_key)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                yield from self._get_json_keys(item, f"{prefix}[{i}]")
    
    def compare_directories(
        self,
        old_dir: Union[str, Path],
        new_dir: Union[str, Path],
        file_patterns: Optional[List[str]] = None
    ) -> Dict[str, DiffReport]:
        """
        对比两个目录
        
        Args:
            old_dir: 旧目录
            new_dir: 新目录
            file_patterns: 文件模式列表
            
        Returns:
            文件路径到差异报告的映射
        """
        old_dir = Path(old_dir)
        new_dir = Path(new_dir)
        file_patterns = file_patterns or ["*.md", "*.json", "*.txt", "*.yaml", "*.yml"]
        
        results = {}
        
        old_files = set()
        new_files = set()
        
        for pattern in file_patterns:
            if old_dir.exists():
                old_files.update(str(f.relative_to(old_dir)) for f in old_dir.rglob(pattern))
            if new_dir.exists():
                new_files.update(str(f.relative_to(new_dir)) for f in new_dir.rglob(pattern))
        
        all_files = old_files | new_files
        
        for rel_path in all_files:
            old_file = old_dir / rel_path
            new_file = new_dir / rel_path
            
            old_content = ""
            new_content = ""
            
            if old_file.exists():
                try:
                    old_content = old_file.read_text(encoding='utf-8')
                except Exception:
                    pass
            
            if new_file.exists():
                try:
                    new_content = new_file.read_text(encoding='utf-8')
                except Exception:
                    pass
            
            report = self.compare_files(old_content, new_content, rel_path)
            results[rel_path] = report
        
        return results
    
    def generate_diff_report_markdown(self, report: DiffReport) -> str:
        """生成 Markdown 格式的差异报告"""
        md = f"""# 文档差异报告

**文档ID**: {report.document_id}
**版本对比**: {report.old_version} → {report.new_version}
**生成时间**: {report.generated_at}

## 摘要

{report.summary}

| 指标 | 数值 |
|------|------|
| 相似度 | {report.similarity:.1%} |
| 总变更数 | {report.total_changes} |
| 新增行数 | {report.lines_added} |
| 删除行数 | {report.lines_removed} |
| 修改行数 | {report.lines_modified} |

"""
        
        if report.structural_changes:
            md += "## 结构变更\n\n"
            for change in report.structural_changes:
                md += f"- {change['type']}: {change.get('title', change.get('key', ''))}\n"
            md += "\n"
        
        if report.entries:
            md += "## 详细变更\n\n"
            for entry in report.entries[:50]:
                md += f"### 行 {entry.line_number} ({entry.diff_type})\n\n"
                if entry.context_before:
                    md += "**上下文**:\n```\n" + "\n".join(entry.context_before) + "\n```\n\n"
                if entry.old_content:
                    md += f"**旧内容**:\n```\n{entry.old_content}```\n\n"
                if entry.new_content:
                    md += f"**新内容**:\n```\n{entry.new_content}```\n\n"
        
        return md


class DocumentRollbackManager:
    """
    文档回滚管理器
    
    功能：
    - 版本回滚
    - 选择性回滚
    - 回滚预览
    """
    
    ROLLBACK_DIR = "rollbacks"
    PLANS_DIR = "rollback_plans"
    
    def __init__(
        self,
        base_path: Optional[Path] = None,
        snapshot_manager: Optional[DocumentSnapshotManager] = None
    ):
        """
        初始化回滚管理器
        
        Args:
            base_path: 基础路径
            snapshot_manager: 快照管理器实例
        """
        if base_path is None:
            if PATH_CONFIG_AVAILABLE and PathConfigManager:
                self.base_path = PathConfigManager(auto_detect=True).get_base_path()
            else:
                self.base_path = Path.cwd()
        else:
            self.base_path = Path(base_path)
        
        self.rollback_dir = self.base_path / self.ROLLBACK_DIR
        self.plans_dir = self.base_path / self.PLANS_DIR
        
        self.snapshot_manager = snapshot_manager or DocumentSnapshotManager(self.base_path)
        self._lock = threading.Lock()
        
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """确保目录存在"""
        self.rollback_dir.mkdir(parents=True, exist_ok=True)
        self.plans_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_plan_id(self, document_id: str) -> str:
        """生成计划ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"plan_{document_id[:12]}_{timestamp}"
    
    def create_rollback_plan(
        self,
        document_id: str,
        target_version: str,
        description: Optional[str] = None
    ) -> RollbackPlan:
        """
        创建回滚计划
        
        Args:
            document_id: 文档ID
            target_version: 目标版本
            description: 描述
            
        Returns:
            回滚计划
        """
        snapshots = self.snapshot_manager.list_snapshots(document_id=document_id)
        
        current_snapshot = snapshots[0] if snapshots else None
        current_version = current_snapshot.version if current_snapshot else "unknown"
        
        target_snapshot = None
        for snap in snapshots:
            if snap.version == target_version:
                target_snapshot = snap
                break
        
        if target_snapshot is None:
            raise RollbackError(f"找不到目标版本的快照: {target_version}")
        
        plan_id = self._generate_plan_id(document_id)
        
        warnings = []
        affected_files = [target_snapshot.file_path]
        
        if current_snapshot and current_snapshot.checksum != target_snapshot.checksum:
            warnings.append("当前版本与目标版本内容不同，回滚将覆盖当前内容")
        
        plan = RollbackPlan(
            plan_id=plan_id,
            document_id=document_id,
            current_version=current_version,
            target_version=target_version,
            created_at=datetime.now().isoformat(),
            affected_files=affected_files,
            estimated_changes=1,
            description=description,
            warnings=warnings
        )
        
        self._save_plan(plan)
        
        logger.info(f"创建回滚计划: {plan_id}")
        return plan
    
    def _save_plan(self, plan: RollbackPlan) -> None:
        """保存回滚计划"""
        plan_path = self.plans_dir / f"{plan.plan_id}.json"
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(plan), f, indent=2, ensure_ascii=False)
    
    def load_plan(self, plan_id: str) -> Optional[RollbackPlan]:
        """加载回滚计划"""
        plan_path = self.plans_dir / f"{plan_id}.json"
        
        if not plan_path.exists():
            return None
        
        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return RollbackPlan(**data)
        except Exception as e:
            logger.error(f"加载回滚计划失败: {e}")
            return None
    
    def preview_rollback(self, plan_id: str) -> Dict[str, Any]:
        """
        预览回滚
        
        Args:
            plan_id: 计划ID
            
        Returns:
            预览信息
        """
        plan = self.load_plan(plan_id)
        
        if plan is None:
            return {"error": "计划不存在"}
        
        snapshots = self.snapshot_manager.list_snapshots(document_id=plan.document_id)
        
        current_snapshot = snapshots[0] if snapshots else None
        target_snapshot = None
        
        for snap in snapshots:
            if snap.version == plan.target_version:
                target_snapshot = snap
                break
        
        preview = {
            "plan_id": plan_id,
            "document_id": plan.document_id,
            "current_version": plan.current_version,
            "target_version": plan.target_version,
            "affected_files": plan.affected_files,
            "warnings": plan.warnings,
            "will_change": current_snapshot.checksum != target_snapshot.checksum if current_snapshot and target_snapshot else True,
            "current_snapshot": asdict(current_snapshot) if current_snapshot else None,
            "target_snapshot": asdict(target_snapshot) if target_snapshot else None
        }
        
        if current_snapshot and target_snapshot:
            diff_analyzer = DocumentDiffAnalyzer()
            
            current_content = self._get_snapshot_content(current_snapshot)
            target_content = self._get_snapshot_content(target_snapshot)
            
            if current_content and target_content:
                diff_report = diff_analyzer.compare_files(
                    current_content,
                    target_content,
                    plan.affected_files[0] if plan.affected_files else "",
                    plan.current_version,
                    plan.target_version
                )
                preview["diff_summary"] = {
                    "similarity": diff_report.similarity,
                    "total_changes": diff_report.total_changes,
                    "lines_added": diff_report.lines_added,
                    "lines_removed": diff_report.lines_removed,
                    "lines_modified": diff_report.lines_modified
                }
        
        return preview
    
    def _get_snapshot_content(self, snapshot: SnapshotMetadata) -> Optional[str]:
        """获取快照内容"""
        content_path = Path(snapshot.content_path)
        
        if not content_path.exists():
            return None
        
        try:
            compressed_content = content_path.read_bytes()
            compression_type = CompressionType(snapshot.compression_type)
            
            if compression_type == CompressionType.GZIP:
                content = gzip.decompress(compressed_content)
            elif compression_type == CompressionType.ZLIB:
                content = zlib.decompress(compressed_content)
            else:
                content = compressed_content
            
            return content.decode('utf-8', errors='ignore')
        except Exception:
            return None
    
    def execute_rollback(
        self,
        plan_id: str,
        create_backup: bool = True
    ) -> RollbackResult:
        """
        执行回滚
        
        Args:
            plan_id: 计划ID
            create_backup: 是否创建备份
            
        Returns:
            回滚结果
        """
        plan = self.load_plan(plan_id)
        
        if plan is None:
            return RollbackResult(
                plan_id=plan_id,
                document_id="",
                success=False,
                message="计划不存在",
                completed_at=datetime.now().isoformat()
            )
        
        plan.status = RollbackStatus.IN_PROGRESS.value
        self._save_plan(plan)
        
        backup_snapshot_id = None
        
        try:
            if create_backup:
                snapshots = self.snapshot_manager.list_snapshots(document_id=plan.document_id)
                current_snapshot = snapshots[0] if snapshots else None
                
                if current_snapshot and Path(current_snapshot.file_path).exists():
                    backup_snapshot = self.snapshot_manager.create_snapshot(
                        current_snapshot.file_path,
                        document_id=plan.document_id,
                        version=f"{plan.current_version}_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        description=f"回滚前备份 (计划: {plan_id})",
                        is_auto=True
                    )
                    backup_snapshot_id = backup_snapshot.snapshot_id
            
            target_snapshot = None
            for snap in self.snapshot_manager.list_snapshots(document_id=plan.document_id):
                if snap.version == plan.target_version:
                    target_snapshot = snap
                    break
            
            if target_snapshot is None:
                raise RollbackError(f"找不到目标版本快照: {plan.target_version}")
            
            success, message = self.snapshot_manager.restore_snapshot(
                target_snapshot.snapshot_id,
                create_backup=False
            )
            
            if not success:
                raise RollbackError(message)
            
            plan.status = RollbackStatus.COMPLETED.value
            self._save_plan(plan)
            
            result = RollbackResult(
                plan_id=plan_id,
                document_id=plan.document_id,
                success=True,
                message=f"成功回滚到版本 {plan.target_version}",
                completed_at=datetime.now().isoformat(),
                restored_files=plan.affected_files,
                backup_created=create_backup,
                backup_snapshot_id=backup_snapshot_id
            )
            
            logger.info(f"回滚成功: {plan_id}")
            return result
            
        except Exception as e:
            plan.status = RollbackStatus.FAILED.value
            self._save_plan(plan)
            
            logger.error(f"回滚失败: {e}")
            return RollbackResult(
                plan_id=plan_id,
                document_id=plan.document_id,
                success=False,
                message=f"回滚失败: {str(e)}",
                completed_at=datetime.now().isoformat(),
                backup_created=create_backup,
                backup_snapshot_id=backup_snapshot_id
            )
    
    def selective_rollback(
        self,
        document_id: str,
        target_version: str,
        sections: Optional[List[str]] = None
    ) -> RollbackResult:
        """
        选择性回滚
        
        Args:
            document_id: 文档ID
            target_version: 目标版本
            sections: 要回滚的部分列表
            
        Returns:
            回滚结果
        """
        snapshots = self.snapshot_manager.list_snapshots(document_id=document_id)
        
        target_snapshot = None
        for snap in snapshots:
            if snap.version == target_version:
                target_snapshot = snap
                break
        
        if target_snapshot is None:
            return RollbackResult(
                plan_id="",
                document_id=document_id,
                success=False,
                message=f"找不到目标版本快照: {target_version}",
                completed_at=datetime.now().isoformat()
            )
        
        target_content = self._get_snapshot_content(target_snapshot)
        
        if target_content is None:
            return RollbackResult(
                plan_id="",
                document_id=document_id,
                success=False,
                message="无法读取目标快照内容",
                completed_at=datetime.now().isoformat()
            )
        
        current_file = Path(target_snapshot.file_path)
        
        if not current_file.exists():
            return RollbackResult(
                plan_id="",
                document_id=document_id,
                success=False,
                message="当前文件不存在",
                completed_at=datetime.now().isoformat()
            )
        
        current_content = current_file.read_text(encoding='utf-8')
        
        if sections:
            merged_content = self._merge_selective_content(
                current_content,
                target_content,
                sections
            )
        else:
            merged_content = target_content
        
        backup_path = current_file.with_suffix(
            f".backup_{datetime.now().strftime('%Y%m%d%H%M%S')}{current_file.suffix}"
        )
        shutil.copy2(current_file, backup_path)
        
        current_file.write_text(merged_content, encoding='utf-8')
        
        return RollbackResult(
            plan_id=f"selective_{document_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            document_id=document_id,
            success=True,
            message=f"选择性回滚成功",
            completed_at=datetime.now().isoformat(),
            restored_files=[str(current_file)]
        )
    
    def _merge_selective_content(
        self,
        current_content: str,
        target_content: str,
        sections: List[str]
    ) -> str:
        """合并选择性内容"""
        current_lines = current_content.split('\n')
        target_lines = target_content.split('\n')
        
        result_lines = current_lines.copy()
        
        for section in sections:
            section_pattern = re.compile(section, re.IGNORECASE)
            
            for i, line in enumerate(target_lines):
                if section_pattern.search(line):
                    if i < len(result_lines):
                        result_lines[i] = line
                    else:
                        result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def list_plans(
        self,
        document_id: Optional[str] = None,
        status: Optional[RollbackStatus] = None
    ) -> List[RollbackPlan]:
        """列出回滚计划"""
        plans = []
        
        for plan_file in self.plans_dir.glob("*.json"):
            try:
                with open(plan_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                plan = RollbackPlan(**data)
                
                if document_id and plan.document_id != document_id:
                    continue
                if status and plan.status != status.value:
                    continue
                
                plans.append(plan)
            except Exception:
                pass
        
        plans.sort(key=lambda x: x.created_at, reverse=True)
        return plans
    
    def cancel_plan(self, plan_id: str) -> bool:
        """取消回滚计划"""
        plan = self.load_plan(plan_id)
        
        if plan is None:
            return False
        
        if plan.status == RollbackStatus.COMPLETED.value:
            return False
        
        plan.status = RollbackStatus.CANCELLED.value
        self._save_plan(plan)
        
        logger.info(f"取消回滚计划: {plan_id}")
        return True


class DocumentIndexManager:
    """
    文档索引管理器
    
    功能：
    - 文档索引创建
    - 索引更新
    - 索引搜索
    """
    
    INDEX_DIR = "doc_index"
    INDEX_FILE = "document_index.json"
    KEYWORDS_FILE = "keywords_index.json"
    
    def __init__(
        self,
        base_path: Optional[Path] = None,
        auto_update: bool = True
    ):
        """
        初始化索引管理器
        
        Args:
            base_path: 基础路径
            auto_update: 是否自动更新索引
        """
        if base_path is None:
            if PATH_CONFIG_AVAILABLE and PathConfigManager:
                self.base_path = PathConfigManager(auto_detect=True).get_base_path()
            else:
                self.base_path = Path.cwd()
        else:
            self.base_path = Path(base_path)
        
        self.index_dir = self.base_path / self.INDEX_DIR
        self.index_file = self.index_dir / self.INDEX_FILE
        self.keywords_file = self.index_dir / self.KEYWORDS_FILE
        
        self.auto_update = auto_update
        self._lock = threading.Lock()
        
        self._index: Dict[str, IndexEntry] = {}
        self._keywords_index: Dict[str, List[str]] = {}
        
        self._ensure_directories()
        self._load_index()
    
    def _ensure_directories(self) -> None:
        """确保目录存在"""
        self.index_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_index(self) -> None:
        """加载索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._index = {
                    k: IndexEntry(**v) for k, v in data.get("entries", {}).items()
                }
            except Exception as e:
                logger.warning(f"加载索引失败: {e}")
        
        if self.keywords_file.exists():
            try:
                with open(self.keywords_file, 'r', encoding='utf-8') as f:
                    self._keywords_index = json.load(f)
            except Exception as e:
                logger.warning(f"加载关键词索引失败: {e}")
    
    def _save_index(self) -> None:
        """保存索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {
                        "version": "1.0",
                        "updated_at": datetime.now().isoformat(),
                        "entries": {k: asdict(v) for k, v in self._index.items()}
                    },
                    f, indent=2, ensure_ascii=False
                )
            
            with open(self.keywords_file, 'w', encoding='utf-8') as f:
                json.dump(self._keywords_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存索引失败: {e}")
    
    def _generate_document_id(self, file_path: Union[str, Path]) -> str:
        """生成文档ID"""
        path_str = str(Path(file_path).absolute())
        return hashlib.md5(path_str.encode()).hexdigest()[:16]
    
    def _detect_document_type(self, file_path: Union[str, Path]) -> DocumentType:
        """检测文档类型"""
        ext = Path(file_path).suffix.lower()
        
        type_map = {
            '.md': DocumentType.MARKDOWN,
            '.json': DocumentType.JSON,
            '.yaml': DocumentType.YAML,
            '.yml': DocumentType.YAML,
            '.txt': DocumentType.TEXT,
            '.html': DocumentType.HTML,
            '.xml': DocumentType.XML,
        }
        
        return type_map.get(ext, DocumentType.OTHER)
    
    def _extract_keywords(self, content: str, document_type: DocumentType) -> List[str]:
        """提取关键词"""
        keywords = set()
        
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
            '的', '了', '和', '是', '就', '都', '而', '及', '与', '着',
            '或', '一个', '没有', '我们', '你们', '他们', '它们', '这个', '那个'
        }
        
        words = re.findall(r'\b[a-zA-Z]{2,}\b', content.lower())
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,}', content)
        
        for word in words:
            if word not in stop_words:
                keywords.add(word)
        
        for word in chinese_words:
            if word not in stop_words:
                keywords.add(word)
        
        if document_type == DocumentType.MARKDOWN:
            headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
            for header in headers:
                keywords.update(header.lower().split())
        
        return list(keywords)[:100]
    
    def create_index(
        self,
        file_path: Union[str, Path],
        version: str = "1.0.0",
        metadata: Optional[Dict[str, Any]] = None
    ) -> IndexEntry:
        """
        创建文档索引
        
        Args:
            file_path: 文档文件路径
            version: 文档版本
            metadata: 额外元数据
            
        Returns:
            索引条目
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise IndexError(f"文件不存在: {file_path}")
        
        document_id = self._generate_document_id(file_path)
        document_name = file_path.stem
        document_type = self._detect_document_type(file_path)
        
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        checksum = hashlib.sha256(content.encode()).hexdigest()
        content_hash = hashlib.md5(content.encode()).hexdigest()
        size_bytes = file_path.stat().st_size
        
        keywords = self._extract_keywords(content, document_type)
        
        entry = IndexEntry(
            document_id=document_id,
            document_name=document_name,
            file_path=str(file_path.absolute()),
            version=version,
            indexed_at=datetime.now().isoformat(),
            checksum=checksum,
            size_bytes=size_bytes,
            document_type=document_type.value,
            keywords=keywords,
            metadata=metadata or {},
            content_hash=content_hash
        )
        
        with self._lock:
            self._index[document_id] = entry
            
            for keyword in keywords:
                if keyword not in self._keywords_index:
                    self._keywords_index[keyword] = []
                if document_id not in self._keywords_index[keyword]:
                    self._keywords_index[keyword].append(document_id)
            
            self._save_index()
        
        logger.info(f"创建索引: {document_id} ({document_name})")
        return entry
    
    def update_index(
        self,
        document_id: Optional[str] = None,
        file_path: Optional[Union[str, Path]] = None
    ) -> Optional[IndexEntry]:
        """
        更新文档索引
        
        Args:
            document_id: 文档ID
            file_path: 文件路径
            
        Returns:
            更新后的索引条目
        """
        if document_id:
            entry = self._index.get(document_id)
            if entry is None:
                return None
            file_path = Path(entry.file_path)
        elif file_path:
            file_path = Path(file_path)
            document_id = self._generate_document_id(file_path)
            entry = self._index.get(document_id)
        else:
            return None
        
        if not file_path.exists():
            return None
        
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        new_checksum = hashlib.sha256(content.encode()).hexdigest()
        
        if entry and entry.checksum == new_checksum:
            return entry
        
        return self.create_index(
            file_path,
            version=entry.version if entry else "1.0.0",
            metadata=entry.metadata if entry else None
        )
    
    def remove_index(self, document_id: str) -> bool:
        """删除索引"""
        entry = self._index.get(document_id)
        
        if entry is None:
            return False
        
        with self._lock:
            for keyword in entry.keywords:
                if keyword in self._keywords_index:
                    if document_id in self._keywords_index[keyword]:
                        self._keywords_index[keyword].remove(document_id)
                    if not self._keywords_index[keyword]:
                        del self._keywords_index[keyword]
            
            del self._index[document_id]
            self._save_index()
        
        logger.info(f"删除索引: {document_id}")
        return True
    
    def search(
        self,
        query: str,
        document_type: Optional[DocumentType] = None,
        limit: int = 20
    ) -> List[SearchResult]:
        """
        搜索文档
        
        Args:
            query: 搜索关键词
            document_type: 文档类型过滤
            limit: 返回数量限制
            
        Returns:
            搜索结果列表
        """
        results = []
        query_lower = query.lower()
        query_keywords = set(re.findall(r'\b\w+\b', query_lower))
        
        for document_id, entry in self._index.items():
            if document_type and entry.document_type != document_type.value:
                continue
            
            score = 0
            matched_keywords = []
            highlights = []
            
            if query_lower in entry.document_name.lower():
                score += 10
                highlights.append(f"名称: {entry.document_name}")
            
            for keyword in query_keywords:
                if keyword in entry.keywords:
                    score += 5
                    matched_keywords.append(keyword)
            
            if query_lower in entry.file_path.lower():
                score += 2
            
            if score > 0:
                snippet = self._get_snippet(entry, query_keywords)
                
                results.append(SearchResult(
                    document_id=document_id,
                    document_name=entry.document_name,
                    file_path=entry.file_path,
                    score=score,
                    matched_keywords=matched_keywords,
                    highlights=highlights,
                    snippet=snippet
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    def _get_snippet(
        self,
        entry: IndexEntry,
        keywords: set,
        max_length: int = 200
    ) -> Optional[str]:
        """获取内容片段"""
        try:
            file_path = Path(entry.file_path)
            if not file_path.exists():
                return None
            
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            for keyword in keywords:
                idx = content.lower().find(keyword.lower())
                if idx >= 0:
                    start = max(0, idx - 50)
                    end = min(len(content), idx + len(keyword) + 50)
                    snippet = content[start:end]
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(content):
                        snippet = snippet + "..."
                    return snippet[:max_length]
            
            return content[:max_length] + "..." if len(content) > max_length else content
        except Exception:
            return None
    
    def get_entry(self, document_id: str) -> Optional[IndexEntry]:
        """获取索引条目"""
        return self._index.get(document_id)
    
    def list_entries(
        self,
        document_type: Optional[DocumentType] = None,
        limit: int = 100
    ) -> List[IndexEntry]:
        """列出索引条目"""
        entries = list(self._index.values())
        
        if document_type:
            entries = [e for e in entries if e.document_type == document_type.value]
        
        entries.sort(key=lambda x: x.indexed_at, reverse=True)
        return entries[:limit]
    
    def rebuild_index(self, docs_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        重建索引
        
        Args:
            docs_path: 文档目录路径
            
        Returns:
            重建结果
        """
        if docs_path is None:
            docs_path = self.base_path / "docs"
        else:
            docs_path = Path(docs_path)
        
        if not docs_path.exists():
            return {"error": "文档目录不存在"}
        
        self._index.clear()
        self._keywords_index.clear()
        
        file_patterns = ["*.md", "*.json", "*.yaml", "*.yml", "*.txt", "*.html"]
        indexed_count = 0
        failed_count = 0
        
        for pattern in file_patterns:
            for file_path in docs_path.rglob(pattern):
                try:
                    self.create_index(file_path)
                    indexed_count += 1
                except Exception as e:
                    logger.warning(f"索引失败: {file_path} - {e}")
                    failed_count += 1
        
        return {
            "indexed_count": indexed_count,
            "failed_count": failed_count,
            "total_keywords": len(self._keywords_index),
            "rebuild_at": datetime.now().isoformat()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取索引统计"""
        stats = {
            "total_documents": len(self._index),
            "total_keywords": len(self._keywords_index),
            "by_type": {},
            "total_size_bytes": 0,
            "oldest_index": None,
            "newest_index": None
        }
        
        timestamps = []
        
        for entry in self._index.values():
            doc_type = entry.document_type
            stats["by_type"][doc_type] = stats["by_type"].get(doc_type, 0) + 1
            stats["total_size_bytes"] += entry.size_bytes
            timestamps.append(entry.indexed_at)
        
        if timestamps:
            timestamps.sort()
            stats["oldest_index"] = timestamps[0]
            stats["newest_index"] = timestamps[-1]
        
        return stats


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="文档版本管理器 - Sanliu 技能"
    )
    
    parser.add_argument(
        '--base-path',
        type=str,
        default='.',
        help='基础路径'
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    parser_snapshot = subparsers.add_parser("snapshot", help="快照管理")
    parser_snapshot.add_argument("action", choices=["create", "list", "restore", "delete"])
    parser_snapshot.add_argument("--file", help="文件路径")
    parser_snapshot.add_argument("--snapshot-id", help="快照ID")
    parser_snapshot.add_argument("--doc-id", help="文档ID")
    parser_snapshot.add_argument("--description", help="描述")
    
    parser_diff = subparsers.add_parser("diff", help="差异对比")
    parser_diff.add_argument("old_file", help="旧文件")
    parser_diff.add_argument("new_file", help="新文件")
    parser_diff.add_argument("--output", help="输出文件")
    
    parser_rollback = subparsers.add_parser("rollback", help="回滚管理")
    parser_rollback.add_argument("action", choices=["plan", "preview", "execute", "list"])
    parser_rollback.add_argument("--plan-id", help="计划ID")
    parser_rollback.add_argument("--doc-id", help="文档ID")
    parser_rollback.add_argument("--target-version", help="目标版本")
    
    parser_index = subparsers.add_parser("index", help="索引管理")
    parser_index.add_argument("action", choices=["create", "update", "search", "list", "rebuild", "stats"])
    parser_index.add_argument("--file", help="文件路径")
    parser_index.add_argument("--query", help="搜索关键词")
    parser_index.add_argument("--doc-id", help="文档ID")
    
    args = parser.parse_args()
    
    base_path = Path(args.base_path).resolve()
    
    if args.command == "snapshot":
        manager = DocumentSnapshotManager(base_path)
        
        if args.action == "create" and args.file:
            snapshot = manager.create_snapshot(args.file, description=args.description)
            print(json.dumps(asdict(snapshot), indent=2, ensure_ascii=False))
        
        elif args.action == "list":
            snapshots = manager.list_snapshots(document_id=args.doc_id)
            for snap in snapshots:
                print(f"- [{snap.snapshot_id}] {snap.document_name} v{snap.version} ({snap.created_at[:10]})")
        
        elif args.action == "restore" and args.snapshot_id:
            success, message = manager.restore_snapshot(args.snapshot_id)
            print(message)
        
        elif args.action == "delete" and args.snapshot_id:
            success = manager.delete_snapshot(args.snapshot_id)
            print(f"删除{'成功' if success else '失败'}")
    
    elif args.command == "diff":
        analyzer = DocumentDiffAnalyzer()
        
        old_content = Path(args.old_file).read_text(encoding='utf-8')
        new_content = Path(args.new_file).read_text(encoding='utf-8')
        
        report = analyzer.compare_files(old_content, new_content, args.old_file)
        
        if args.output:
            md_content = analyzer.generate_diff_report_markdown(report)
            Path(args.output).write_text(md_content, encoding='utf-8')
            print(f"报告已保存: {args.output}")
        else:
            print(f"相似度: {report.similarity:.1%}")
            print(f"变更: 新增 {report.lines_added} 行, 删除 {report.lines_removed} 行, 修改 {report.lines_modified} 行")
    
    elif args.command == "rollback":
        manager = DocumentRollbackManager(base_path)
        
        if args.action == "plan" and args.doc_id and args.target_version:
            plan = manager.create_rollback_plan(args.doc_id, args.target_version)
            print(json.dumps(asdict(plan), indent=2, ensure_ascii=False))
        
        elif args.action == "preview" and args.plan_id:
            preview = manager.preview_rollback(args.plan_id)
            print(json.dumps(preview, indent=2, ensure_ascii=False))
        
        elif args.action == "execute" and args.plan_id:
            result = manager.execute_rollback(args.plan_id)
            print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        
        elif args.action == "list":
            plans = manager.list_plans(document_id=args.doc_id)
            for plan in plans:
                print(f"- [{plan.plan_id}] {plan.document_id}: {plan.current_version} -> {plan.target_version} ({plan.status})")
    
    elif args.command == "index":
        manager = DocumentIndexManager(base_path)
        
        if args.action == "create" and args.file:
            entry = manager.create_index(args.file)
            print(json.dumps(asdict(entry), indent=2, ensure_ascii=False))
        
        elif args.action == "update":
            entry = manager.update_index(document_id=args.doc_id, file_path=args.file)
            if entry:
                print(json.dumps(asdict(entry), indent=2, ensure_ascii=False))
            else:
                print("更新失败")
        
        elif args.action == "search" and args.query:
            results = manager.search(args.query)
            for result in results:
                print(f"- [{result.document_id}] {result.document_name} (分数: {result.score})")
        
        elif args.action == "list":
            entries = manager.list_entries()
            for entry in entries:
                print(f"- [{entry.document_id}] {entry.document_name} ({entry.document_type})")
        
        elif args.action == "rebuild":
            result = manager.rebuild_index()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif args.action == "stats":
            stats = manager.get_statistics()
            print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
