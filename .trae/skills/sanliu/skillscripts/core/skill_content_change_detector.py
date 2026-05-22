#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能内容变化检测器 - Skill Content Change Detector

检测技能文件的变化，包括 SKILL.md、子技能文档、脚本文件和配置文件。
支持增量检测和文件哈希计算。

核心功能:
- 检测 SKILL.md 文件变化
- 检测子技能文档变化 (subskills/*.md)
- 检测脚本文件变化 (skillscripts/**/*.py)
- 检测配置文件变化
- 计算文件哈希值进行变化检测
- 支持增量检测

使用示例:
    from skill_content_change_detector import SkillContentChangeDetector
    
    detector = SkillContentChangeDetector(skill_dir='./')
    changes = detector.detect_changes()
    
    if changes.has_changes:
        print(f"检测到 {len(changes.changed_files)} 个文件变化")
"""

import hashlib
import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class ChangeType(Enum):
    """变化类型枚举"""
    CREATED = auto()
    MODIFIED = auto()
    DELETED = auto()
    RENAMED = auto()


class FileType(Enum):
    """文件类型枚举"""
    SKILL_MD = "skill_md"
    SUBSKILL_MD = "subskill_md"
    SCRIPT_PY = "script_py"
    CONFIG = "config"
    OTHER = "other"


@dataclass
class FileHash:
    """文件哈希数据类"""
    file_path: str
    hash_value: str
    file_size: int
    last_modified: float
    file_type: FileType
    computed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "hash_value": self.hash_value,
            "file_size": self.file_size,
            "last_modified": self.last_modified,
            "file_type": self.file_type.value,
            "computed_at": self.computed_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileHash':
        return cls(
            file_path=data["file_path"],
            hash_value=data["hash_value"],
            file_size=data["file_size"],
            last_modified=data["last_modified"],
            file_type=FileType(data["file_type"]),
            computed_at=datetime.fromisoformat(data["computed_at"]) if isinstance(data.get("computed_at"), str) else datetime.now()
        )


@dataclass
class FileChange:
    """文件变化数据类"""
    file_path: str
    change_type: ChangeType
    file_type: FileType
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    old_size: Optional[int] = None
    new_size: Optional[int] = None
    detected_at: datetime = field(default_factory=datetime.now)
    diff_summary: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "change_type": self.change_type.name,
            "file_type": self.file_type.value,
            "old_hash": self.old_hash,
            "new_hash": self.new_hash,
            "old_size": self.old_size,
            "new_size": self.new_size,
            "detected_at": self.detected_at.isoformat(),
            "diff_summary": self.diff_summary
        }


@dataclass
class ChangeDetectionResult:
    """变化检测结果数据类"""
    detection_id: str
    detected_at: datetime
    has_changes: bool
    changed_files: List[FileChange] = field(default_factory=list)
    added_files: List[FileChange] = field(default_factory=list)
    modified_files: List[FileChange] = field(default_factory=list)
    deleted_files: List[FileChange] = field(default_factory=list)
    total_files_scanned: int = 0
    scan_duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "detection_id": self.detection_id,
            "detected_at": self.detected_at.isoformat(),
            "has_changes": self.has_changes,
            "changed_files": [f.to_dict() for f in self.changed_files],
            "added_files": [f.to_dict() for f in self.added_files],
            "modified_files": [f.to_dict() for f in self.modified_files],
            "deleted_files": [f.to_dict() for f in self.deleted_files],
            "total_files_scanned": self.total_files_scanned,
            "scan_duration_seconds": self.scan_duration_seconds,
            "metadata": self.metadata
        }
    
    def get_changes_by_type(self, file_type: FileType) -> List[FileChange]:
        """获取指定类型的文件变化"""
        return [c for c in self.changed_files if c.file_type == file_type]
    
    def get_critical_changes(self) -> List[FileChange]:
        """获取关键变化（SKILL.md 和脚本文件）"""
        critical_types = {FileType.SKILL_MD, FileType.SCRIPT_PY}
        return [c for c in self.changed_files if c.file_type in critical_types]


class HashCache:
    """文件哈希缓存"""
    
    def __init__(self, cache_file: Optional[Path] = None):
        self._cache: Dict[str, FileHash] = {}
        self._cache_file = cache_file
        self._lock = threading.Lock()
        self._logger = logging.getLogger('HashCache')
        
        if self._cache_file:
            self._load_cache()
    
    def _load_cache(self) -> None:
        """加载缓存"""
        if not self._cache_file or not self._cache_file.exists():
            return
        
        try:
            with open(self._cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data.get("hashes", []):
                file_hash = FileHash.from_dict(item)
                self._cache[file_hash.file_path] = file_hash
            
            self._logger.debug(f"已加载 {len(self._cache)} 个文件哈希缓存")
            
        except Exception as e:
            self._logger.error(f"加载哈希缓存失败: {e}")
    
    def save_cache(self) -> None:
        """保存缓存"""
        if not self._cache_file:
            return
        
        with self._lock:
            try:
                data = {
                    "version": "1.0",
                    "updated_at": datetime.now().isoformat(),
                    "hashes": [h.to_dict() for h in self._cache.values()]
                }
                
                temp_file = self._cache_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                temp_file.replace(self._cache_file)
                
            except Exception as e:
                self._logger.error(f"保存哈希缓存失败: {e}")
    
    def get(self, file_path: str) -> Optional[FileHash]:
        """获取文件哈希"""
        with self._lock:
            return self._cache.get(file_path)
    
    def set(self, file_hash: FileHash) -> None:
        """设置文件哈希"""
        with self._lock:
            self._cache[file_hash.file_path] = file_hash
    
    def remove(self, file_path: str) -> bool:
        """移除文件哈希"""
        with self._lock:
            if file_path in self._cache:
                del self._cache[file_path]
                return True
            return False
    
    def get_all_paths(self) -> Set[str]:
        """获取所有缓存的文件路径"""
        with self._lock:
            return set(self._cache.keys())
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()


class SkillContentChangeDetector:
    """技能内容变化检测器"""
    
    SKILL_MD_NAME = "SKILL.md"
    SUBSKILL_DIR = "subskills"
    SCRIPTS_DIR = "skillscripts"
    CONFIG_PATTERNS = [
        "*.json",
        "*.yaml",
        "*.yml",
        "*.toml",
        "*.ini",
        "*.cfg",
        ".env*"
    ]
    
    IGNORE_PATTERNS = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".git",
        "node_modules",
        "*.tmp",
        "*.bak",
        ".pytest_cache",
        "*.egg-info",
        "dist",
        "build"
    ]
    
    def __init__(
        self,
        skill_dir: str,
        cache_dir: Optional[str] = None,
        auto_save_cache: bool = True
    ):
        self._skill_dir = Path(skill_dir)
        self._cache_dir = Path(cache_dir) if cache_dir else self._skill_dir / ".evolution" / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._hash_cache = HashCache(self._cache_dir / "file_hashes.json")
        self._auto_save_cache = auto_save_cache
        self._logger = logging.getLogger('SkillContentChangeDetector')
        
        self._detection_history: List[ChangeDetectionResult] = []
        self._lock = threading.Lock()
    
    def detect_changes(
        self,
        incremental: bool = True,
        file_types: Optional[Set[FileType]] = None
    ) -> ChangeDetectionResult:
        """检测文件变化
        
        Args:
            incremental: 是否增量检测（仅检测有变化的文件）
            file_types: 要检测的文件类型集合，None 表示检测所有类型
        
        Returns:
            变化检测结果
        """
        start_time = datetime.now()
        detection_id = f"DETECT-{start_time.strftime('%Y%m%d%H%M%S')}"
        
        self._logger.info(f"开始变化检测: {detection_id}, 增量模式: {incremental}")
        
        changed_files: List[FileChange] = []
        added_files: List[FileChange] = []
        modified_files: List[FileChange] = []
        deleted_files: List[FileChange] = []
        
        current_files = self._scan_files(file_types)
        cached_paths = self._hash_cache.get_all_paths()
        
        for file_path_str, file_type in current_files:
            file_path = Path(file_path_str)
            current_hash = self._compute_file_hash(file_path)
            
            if current_hash is None:
                continue
            
            cached = self._hash_cache.get(file_path_str)
            
            if cached is None:
                change = FileChange(
                    file_path=file_path_str,
                    change_type=ChangeType.CREATED,
                    file_type=file_type,
                    new_hash=current_hash.hash_value,
                    new_size=current_hash.file_size
                )
                changed_files.append(change)
                added_files.append(change)
                
                if not incremental:
                    self._hash_cache.set(current_hash)
                    
            elif cached.hash_value != current_hash.hash_value:
                change = FileChange(
                    file_path=file_path_str,
                    change_type=ChangeType.MODIFIED,
                    file_type=file_type,
                    old_hash=cached.hash_value,
                    new_hash=current_hash.hash_value,
                    old_size=cached.file_size,
                    new_size=current_hash.file_size
                )
                changed_files.append(change)
                modified_files.append(change)
                self._hash_cache.set(current_hash)
        
        for cached_path in cached_paths:
            if cached_path not in {p for p, _ in current_files}:
                cached = self._hash_cache.get(cached_path)
                if cached:
                    change = FileChange(
                        file_path=cached_path,
                        change_type=ChangeType.DELETED,
                        file_type=cached.file_type,
                        old_hash=cached.hash_value,
                        old_size=cached.file_size
                    )
                    changed_files.append(change)
                    deleted_files.append(change)
                    self._hash_cache.remove(cached_path)
        
        if incremental:
            for change in added_files:
                file_path = Path(change.file_path)
                file_hash = self._compute_file_hash(file_path)
                if file_hash:
                    self._hash_cache.set(file_hash)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = ChangeDetectionResult(
            detection_id=detection_id,
            detected_at=start_time,
            has_changes=len(changed_files) > 0,
            changed_files=changed_files,
            added_files=added_files,
            modified_files=modified_files,
            deleted_files=deleted_files,
            total_files_scanned=len(current_files),
            scan_duration_seconds=duration,
            metadata={
                "incremental": incremental,
                "file_types_filter": [ft.value for ft in file_types] if file_types else None
            }
        )
        
        with self._lock:
            self._detection_history.append(result)
            if len(self._detection_history) > 100:
                self._detection_history = self._detection_history[-100:]
        
        if self._auto_save_cache:
            self._hash_cache.save_cache()
        
        self._logger.info(
            f"变化检测完成: 发现 {len(changed_files)} 个变化 "
            f"(新增: {len(added_files)}, 修改: {len(modified_files)}, 删除: {len(deleted_files)})"
        )
        
        return result
    
    def _scan_files(
        self,
        file_types: Optional[Set[FileType]] = None
    ) -> List[Tuple[str, FileType]]:
        """扫描文件"""
        files: List[Tuple[str, FileType]] = []
        
        if file_types is None or FileType.SKILL_MD in file_types:
            skill_md = self._skill_dir / self.SKILL_MD_NAME
            if skill_md.exists():
                files.append((str(skill_md), FileType.SKILL_MD))
        
        if file_types is None or FileType.SUBSKILL_MD in file_types:
            subskill_dir = self._skill_dir / self.SUBSKILL_DIR
            if subskill_dir.exists():
                for md_file in subskill_dir.rglob("*.md"):
                    if not self._should_ignore(md_file):
                        files.append((str(md_file), FileType.SUBSKILL_MD))
        
        if file_types is None or FileType.SCRIPT_PY in file_types:
            scripts_dir = self._skill_dir / self.SCRIPTS_DIR
            if scripts_dir.exists():
                for py_file in scripts_dir.rglob("*.py"):
                    if not self._should_ignore(py_file):
                        files.append((str(py_file), FileType.SCRIPT_PY))
        
        if file_types is None or FileType.CONFIG in file_types:
            for pattern in self.CONFIG_PATTERNS:
                for config_file in self._skill_dir.rglob(pattern):
                    if not self._should_ignore(config_file):
                        files.append((str(config_file), FileType.CONFIG))
        
        return files
    
    def _should_ignore(self, file_path: Path) -> bool:
        """检查文件是否应该被忽略"""
        path_str = str(file_path)
        
        for pattern in self.IGNORE_PATTERNS:
            if pattern.startswith('*'):
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in path_str:
                return True
        
        return False
    
    def _compute_file_hash(self, file_path: Path) -> Optional[FileHash]:
        """计算文件哈希"""
        if not file_path.exists():
            return None
        
        try:
            stat = file_path.stat()
            
            hasher = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            
            file_type = self._determine_file_type(file_path)
            
            return FileHash(
                file_path=str(file_path),
                hash_value=hasher.hexdigest(),
                file_size=stat.st_size,
                last_modified=stat.st_mtime,
                file_type=file_type
            )
            
        except Exception as e:
            self._logger.error(f"计算文件哈希失败 {file_path}: {e}")
            return None
    
    def _determine_file_type(self, file_path: Path) -> FileType:
        """确定文件类型"""
        name = file_path.name
        parent = file_path.parent.name
        
        if name == self.SKILL_MD_NAME:
            return FileType.SKILL_MD
        
        if parent == self.SUBSKILL_DIR and name.endswith('.md'):
            return FileType.SUBSKILL_MD
        
        if name.endswith('.py'):
            return FileType.SCRIPT_PY
        
        for pattern in self.CONFIG_PATTERNS:
            if pattern.startswith('*'):
                if name.endswith(pattern[1:]):
                    return FileType.CONFIG
            elif name == pattern:
                return FileType.CONFIG
        
        return FileType.OTHER
    
    def get_file_hash(self, file_path: str) -> Optional[FileHash]:
        """获取文件哈希"""
        return self._hash_cache.get(file_path)
    
    def update_file_hash(self, file_path: str) -> Optional[FileHash]:
        """更新文件哈希"""
        path = Path(file_path)
        file_hash = self._compute_file_hash(path)
        if file_hash:
            self._hash_cache.set(file_hash)
            if self._auto_save_cache:
                self._hash_cache.save_cache()
        return file_hash
    
    def remove_file_hash(self, file_path: str) -> bool:
        """移除文件哈希"""
        result = self._hash_cache.remove(file_path)
        if result and self._auto_save_cache:
            self._hash_cache.save_cache()
        return result
    
    def get_detection_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取检测历史"""
        with self._lock:
            return [r.to_dict() for r in self._detection_history[-limit:]]
    
    def get_last_detection(self) -> Optional[ChangeDetectionResult]:
        """获取最后一次检测结果"""
        with self._lock:
            return self._detection_history[-1] if self._detection_history else None
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._hash_cache.clear()
        if self._auto_save_cache:
            self._hash_cache.save_cache()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            total_detections = len(self._detection_history)
            total_changes = sum(len(r.changed_files) for r in self._detection_history)
            
            changes_by_type: Dict[str, int] = {}
            for result in self._detection_history:
                for change in result.changed_files:
                    type_name = change.file_type.value
                    changes_by_type[type_name] = changes_by_type.get(type_name, 0) + 1
            
            return {
                "total_detections": total_detections,
                "total_changes": total_changes,
                "changes_by_type": changes_by_type,
                "cached_files": len(self._hash_cache.get_all_paths())
            }
    
    def watch_for_changes(
        self,
        callback: Any,
        interval_seconds: int = 60,
        file_types: Optional[Set[FileType]] = None
    ) -> threading.Thread:
        """监视文件变化
        
        Args:
            callback: 变化时的回调函数，接收 ChangeDetectionResult 参数
            interval_seconds: 检查间隔（秒）
            file_types: 要监视的文件类型
        
        Returns:
            监视线程
        """
        stop_event = threading.Event()
        
        def watch_loop():
            while not stop_event.is_set():
                try:
                    result = self.detect_changes(
                        incremental=True,
                        file_types=file_types
                    )
                    
                    if result.has_changes:
                        try:
                            callback(result)
                        except Exception as e:
                            self._logger.error(f"回调函数执行失败: {e}")
                    
                except Exception as e:
                    self._logger.error(f"监视变化失败: {e}")
                
                stop_event.wait(interval_seconds)
        
        thread = threading.Thread(target=watch_loop, daemon=True)
        thread.start()
        
        return thread
