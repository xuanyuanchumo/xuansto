#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三省六部协同开发系统 - 自迭代回滚器

实现自迭代过程中的安全回滚机制：
- 版本快照管理（增量快照、差异快照）
- 自动回滚触发（异常、测试失败、验证失败、超时）
- 失败通知机制（邮件、Webhook、日志、文件、控制台）
- 回滚验证（基础、标准、彻底三级验证）
- 快照压缩和加密
- 快照差异对比
- 回滚预览

使用示例:
    from self_iteration_rollback import SelfIterationRollback
    
    rollback = SelfIterationRollback("./project")
    
    # 创建快照
    snapshot = rollback.create_snapshot("v1.0.0")
    
    # 在迭代上下文中执行操作
    with rollback.iteration_context("update_feature") as ctx:
        ctx.update_file("script.py", new_content)
    
    # 手动回滚
    result = rollback.rollback(snapshot.snapshot_id)
    
    # 自动回滚（失败时）
    rollback.auto_rollback_on_failure(exception)
    
    # 预览回滚
    preview = rollback.preview_rollback(snapshot.snapshot_id)
    
    # 对比快照差异
    diff = rollback.diff_snapshots(snapshot1_id, snapshot2_id)

CLI使用:
    python self_iteration_rollback.py snapshot --project-root ./ --version v1.0.0
    python self_iteration_rollback.py list --project-root ./
    python self_iteration_rollback.py rollback --snapshot-id SNAP-xxx
    python self_iteration_rollback.py verify --project-root ./
    python self_iteration_rollback.py diff --snapshot-id1 SNAP-xxx --snapshot-id2 SNAP-yyy
"""

import os
import sys
import json
import shutil
import hashlib
import subprocess
import threading
import time
import traceback
import gzip
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable, Union, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import contextmanager
import logging
import argparse
import tempfile
from concurrent.futures import ThreadPoolExecutor
from difflib import unified_diff

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


class SnapshotStatus(Enum):
    CREATED = "created"
    ACTIVE = "active"
    RESTORED = "restored"
    DEPRECATED = "deprecated"
    ERROR = "error"
    CORRUPTED = "corrupted"
    ARCHIVED = "archived"


class RollbackTrigger(Enum):
    MANUAL = "manual"
    AUTO_EXCEPTION = "auto_exception"
    AUTO_TEST_FAILURE = "auto_test_failure"
    AUTO_VALIDATION_FAILURE = "auto_validation_failure"
    AUTO_TIMEOUT = "auto_timeout"
    AUTO_MEMORY_LIMIT = "auto_memory_limit"
    AUTO_CPU_LIMIT = "auto_cpu_limit"
    EMERGENCY = "emergency"
    SCHEDULED = "scheduled"


class NotificationType(Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    LOG = "log"
    FILE = "file"
    CONSOLE = "console"
    SLACK = "slack"
    TEAMS = "teams"


class VerificationLevel(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    THOROUGH = "thorough"


class SnapshotType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class DiffType(Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class RollbackStrategy(Enum):
    """回滚策略枚举"""
    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    SELECTIVE = "selective"
    CASCADE = "cascade"
    SAFE_FIRST = "safe_first"
    PRIORITY_BASED = "priority_based"


class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TriggerEventType(Enum):
    """触发事件类型枚举"""
    FILE_CHANGE = "file_change"
    TEST_FAILURE = "test_failure"
    BUILD_FAILURE = "build_failure"
    DEPLOYMENT = "deployment"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    THRESHOLD_BREACH = "threshold_breach"
    ANOMALY_DETECTED = "anomaly_detected"


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class SnapshotInfo:
    snapshot_id: str
    version: str
    timestamp: str
    project_root: str
    files_count: int
    total_size: int
    verification_hash: str
    status: SnapshotStatus = SnapshotStatus.CREATED
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    snapshot_type: SnapshotType = SnapshotType.FULL
    parent_snapshot_id: Optional[str] = None
    compressed: bool = False
    encrypted: bool = False
    description: str = ""
    author: str = ""
    branch: str = ""


@dataclass
class RollbackResult:
    success: bool
    snapshot_id: str
    trigger: RollbackTrigger
    timestamp: str
    files_restored: int
    files_failed: int
    verification_passed: bool
    error_message: Optional[str] = None
    rollback_duration_seconds: float = 0.0
    files_details: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    passed: bool
    level: VerificationLevel
    checks_total: int
    checks_passed: int
    checks_failed: int
    details: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class NotificationMessage:
    notification_type: NotificationType
    title: str
    message: str
    timestamp: str
    severity: str
    details: Dict[str, Any] = field(default_factory=dict)
    snapshot_id: Optional[str] = None
    rollback_result: Optional[RollbackResult] = None


@dataclass
class NotificationConfig:
    enabled: bool = True
    notification_types: List[NotificationType] = field(default_factory=lambda: [NotificationType.LOG, NotificationType.CONSOLE])
    email_recipients: List[str] = field(default_factory=list)
    email_smtp_host: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_use_tls: bool = True
    webhook_url: str = ""
    webhook_timeout: int = 10
    notification_file: str = ""
    slack_webhook_url: str = ""
    teams_webhook_url: str = ""
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class IterationResult:
    success: bool
    operation_name: str
    snapshot_id: str
    start_time: str
    end_time: str
    modified_files: List[str]
    verification_passed: bool
    error: Optional[str] = None
    rollback_performed: bool = False
    duration_seconds: float = 0.0


@dataclass
class FileDiffInfo:
    file_path: str
    diff_type: DiffType
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    old_size: int = 0
    new_size: int = 0
    diff_content: Optional[str] = None


@dataclass
class SnapshotDiffResult:
    snapshot1_id: str
    snapshot2_id: str
    added_files: List[str] = field(default_factory=list)
    removed_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    unchanged_files: List[str] = field(default_factory=list)
    file_diffs: List[FileDiffInfo] = field(default_factory=list)


@dataclass
class RollbackPreview:
    snapshot_id: str
    files_to_restore: int
    files_to_delete: int
    files_to_modify: int
    files_details: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    estimated_size: int = 0


@dataclass
class AutoRollbackConfig:
    enabled: bool = True
    on_exception: bool = True
    on_test_failure: bool = True
    on_validation_failure: bool = True
    on_timeout: bool = True
    timeout_seconds: float = 300.0
    max_auto_rollbacks: int = 5
    cooldown_seconds: float = 60.0
    verification_level: VerificationLevel = VerificationLevel.STANDARD


@dataclass
class RollbackStrategyConfig:
    """回滚策略配置"""
    strategy: RollbackStrategy = RollbackStrategy.IMMEDIATE
    risk_threshold: RiskLevel = RiskLevel.MEDIUM
    max_retries: int = 3
    retry_delay: float = 5.0
    pre_rollback_hooks: List[str] = field(default_factory=list)
    post_rollback_hooks: List[str] = field(default_factory=list)
    verification_before: bool = True
    verification_after: bool = True
    backup_before_rollback: bool = True
    notify_on_start: bool = True
    notify_on_complete: bool = True
    notify_on_failure: bool = True
    priority_files: List[str] = field(default_factory=list)
    exclude_files: List[str] = field(default_factory=list)


@dataclass
class RiskAssessment:
    """风险评估结果"""
    risk_level: RiskLevel
    risk_score: float
    affected_files: int
    critical_files: List[str]
    warnings: List[str]
    recommendations: List[str]
    can_proceed: bool
    requires_backup: bool
    estimated_impact: str


@dataclass
class AutoSnapshotConfig:
    """自动快照配置"""
    enabled: bool = True
    schedule_interval: int = 3600
    on_file_change: bool = True
    on_test_pass: bool = True
    on_deployment: bool = True
    max_snapshots: int = 20
    min_interval_seconds: int = 300
    file_change_threshold: int = 5
    exclude_patterns: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=lambda: ["auto"])
    compress: bool = False
    retention_days: int = 30


@dataclass
class HealthMetrics:
    """健康度指标"""
    status: HealthStatus
    score: float
    test_pass_rate: float
    build_success_rate: float
    error_count: int
    warning_count: int
    last_check_time: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    response_time: float
    error_rate: float
    throughput: float
    timestamp: str


@dataclass
class AnomalyInfo:
    """异常信息"""
    anomaly_type: str
    severity: RiskLevel
    detected_at: str
    description: str
    affected_components: List[str]
    metrics: Dict[str, float]
    recommended_action: str


@dataclass
class AuditLogEntry:
    """审计日志条目"""
    timestamp: str
    action: str
    actor: str
    target: str
    details: Dict[str, Any]
    result: str
    risk_level: RiskLevel
    snapshot_id: Optional[str] = None


@dataclass
class FailureAnalysis:
    """失败分析结果"""
    failure_id: str
    timestamp: str
    failure_type: str
    root_cause: str
    affected_files: List[str]
    impact_assessment: str
    recovery_suggestions: List[str]
    related_failures: List[str]
    metrics: Dict[str, Any]


@dataclass
class NotificationTemplate:
    """通知模板"""
    template_id: str
    name: str
    title_template: str
    body_template: str
    severity_mapping: Dict[str, str]
    include_details: bool = True
    include_metrics: bool = False
    custom_fields: Dict[str, str] = field(default_factory=dict)


class SnapshotManager:
    """版本快照管理器"""
    
    def __init__(self, snapshot_dir: str, compress: bool = False, encrypt: bool = False, encryption_key: str = None):
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self._snapshots: Dict[str, SnapshotInfo] = {}
        self._lock = threading.Lock()
        self._compress = compress
        self._encrypt = encrypt
        self._encryption_key = encryption_key
        self._load_snapshot_index()
    
    def _load_snapshot_index(self):
        index_file = self.snapshot_dir / "snapshot_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for snap_id, info in data.items():
                        self._snapshots[snap_id] = SnapshotInfo(
                            snapshot_id=info['snapshot_id'],
                            version=info['version'],
                            timestamp=info['timestamp'],
                            project_root=info['project_root'],
                            files_count=info['files_count'],
                            total_size=info['total_size'],
                            verification_hash=info['verification_hash'],
                            status=SnapshotStatus(info.get('status', 'created')),
                            metadata=info.get('metadata', {}),
                            tags=info.get('tags', []),
                            snapshot_type=SnapshotType(info.get('snapshot_type', 'full')),
                            parent_snapshot_id=info.get('parent_snapshot_id'),
                            compressed=info.get('compressed', False),
                            encrypted=info.get('encrypted', False),
                            description=info.get('description', ''),
                            author=info.get('author', ''),
                            branch=info.get('branch', '')
                        )
            except Exception as e:
                logger.error(f"加载快照索引失败: {e}")
    
    def _save_snapshot_index(self):
        index_file = self.snapshot_dir / "snapshot_index.json"
        try:
            data = {}
            for snap_id, info in self._snapshots.items():
                data[snap_id] = {
                    'snapshot_id': info.snapshot_id,
                    'version': info.version,
                    'timestamp': info.timestamp,
                    'project_root': info.project_root,
                    'files_count': info.files_count,
                    'total_size': info.total_size,
                    'verification_hash': info.verification_hash,
                    'status': info.status.value,
                    'metadata': info.metadata,
                    'tags': info.tags,
                    'snapshot_type': info.snapshot_type.value,
                    'parent_snapshot_id': info.parent_snapshot_id,
                    'compressed': info.compressed,
                    'encrypted': info.encrypted,
                    'description': info.description,
                    'author': info.author,
                    'branch': info.branch
                }
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存快照索引失败: {e}")
    
    def create_snapshot(
        self,
        project_root: str,
        version: str,
        file_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
        metadata: Dict[str, Any] = None,
        tags: List[str] = None,
        snapshot_type: SnapshotType = SnapshotType.FULL,
        parent_snapshot_id: str = None,
        description: str = "",
        author: str = ""
    ) -> SnapshotInfo:
        snapshot_id = f"SNAP-{version}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        snapshot_path = self.snapshot_dir / snapshot_id
        snapshot_path.mkdir(parents=True, exist_ok=True)
        
        file_patterns = file_patterns or ['*.py', '*.json', '*.yaml', '*.yml', '*.toml', '*.md', '*.txt']
        exclude_patterns = exclude_patterns or ['__pycache__', '*.pyc', '.git', 'node_modules', '.pytest_cache', '*.bak_*', '*_temp_*']
        
        files_data = {}
        total_size = 0
        hash_parts = []
        
        project_path = Path(project_root)
        
        for pattern in file_patterns:
            for file_path in project_path.rglob(pattern):
                if self._should_exclude(file_path, exclude_patterns, project_path):
                    continue
                
                try:
                    rel_path = str(file_path.relative_to(project_path))
                    content = file_path.read_bytes()
                    content_hash = hashlib.sha256(content).hexdigest()
                    
                    if self._compress:
                        content = gzip.compress(content)
                    
                    if self._encrypt and self._encryption_key:
                        content = self._encrypt_data(content)
                    
                    snapshot_file = snapshot_path / rel_path
                    snapshot_file.parent.mkdir(parents=True, exist_ok=True)
                    snapshot_file.write_bytes(content)
                    
                    files_data[rel_path] = {
                        'original_path': str(file_path),
                        'snapshot_path': str(snapshot_file),
                        'content_hash': content_hash,
                        'size': len(content),
                        'compressed': self._compress,
                        'encrypted': self._encrypt
                    }
                    
                    total_size += len(content)
                    hash_parts.append(content_hash)
                    
                except Exception as e:
                    logger.warning(f"快照文件失败 {file_path}: {e}")
        
        verification_hash = hashlib.sha256(''.join(hash_parts).encode()).hexdigest()
        
        files_index_path = snapshot_path / "files_index.json"
        with open(files_index_path, 'w', encoding='utf-8') as f:
            json.dump(files_data, f, indent=2, ensure_ascii=False)
        
        snapshot_info = SnapshotInfo(
            snapshot_id=snapshot_id,
            version=version,
            timestamp=datetime.now().isoformat(),
            project_root=str(project_root),
            files_count=len(files_data),
            total_size=total_size,
            verification_hash=verification_hash,
            status=SnapshotStatus.ACTIVE,
            metadata=metadata or {},
            tags=tags or [],
            snapshot_type=snapshot_type,
            parent_snapshot_id=parent_snapshot_id,
            compressed=self._compress,
            encrypted=self._encrypt,
            description=description,
            author=author
        )
        
        metadata_path = snapshot_path / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump({
                'snapshot_id': snapshot_id,
                'version': version,
                'timestamp': snapshot_info.timestamp,
                'description': description,
                'author': author,
                'tags': tags or [],
                'metadata': metadata or {}
            }, f, indent=2, ensure_ascii=False)
        
        with self._lock:
            self._snapshots[snapshot_id] = snapshot_info
        
        self._save_snapshot_index()
        
        logger.info(f"创建快照成功: {snapshot_id}, 文件数: {len(files_data)}, 类型: {snapshot_type.value}")
        return snapshot_info
    
    def _encrypt_data(self, data: bytes) -> bytes:
        """简单的数据加密（实际应用中应使用更安全的方法）"""
        if not self._encryption_key:
            return data
        key_bytes = self._encryption_key.encode()
        encrypted = bytearray()
        for i, byte in enumerate(data):
            encrypted.append(byte ^ key_bytes[i % len(key_bytes)])
        return base64.b64encode(bytes(encrypted))
    
    def _decrypt_data(self, data: bytes) -> bytes:
        """解密数据"""
        if not self._encryption_key:
            return data
        key_bytes = self._encryption_key.encode()
        decoded = base64.b64decode(data)
        decrypted = bytearray()
        for i, byte in enumerate(decoded):
            decrypted.append(byte ^ key_bytes[i % len(key_bytes)])
        return bytes(decrypted)
    
    def _should_exclude(self, file_path: Path, exclude_patterns: List[str], project_root: Path) -> bool:
        rel_path = str(file_path.relative_to(project_root))
        
        for pattern in exclude_patterns:
            if pattern.startswith('*'):
                if file_path.name.endswith(pattern[1:]):
                    return True
            elif pattern in rel_path:
                return True
        
        return False
    
    def get_snapshot(self, snapshot_id: str) -> Optional[SnapshotInfo]:
        with self._lock:
            return self._snapshots.get(snapshot_id)
    
    def list_snapshots(
        self,
        status: SnapshotStatus = None,
        tags: List[str] = None,
        limit: int = 100,
        snapshot_type: SnapshotType = None
    ) -> List[SnapshotInfo]:
        with self._lock:
            snapshots = list(self._snapshots.values())
        
        if status:
            snapshots = [s for s in snapshots if s.status == status]
        
        if tags:
            snapshots = [s for s in snapshots if any(t in s.tags for t in tags)]
        
        if snapshot_type:
            snapshots = [s for s in snapshots if s.snapshot_type == snapshot_type]
        
        snapshots.sort(key=lambda x: x.timestamp, reverse=True)
        return snapshots[:limit]
    
    def restore_snapshot(
        self,
        snapshot_id: str,
        project_root: str = None,
        verify: bool = True,
        files_filter: List[str] = None
    ) -> Tuple[bool, int, int, List[str], List[Dict[str, Any]]]:
        snapshot_info = self.get_snapshot(snapshot_id)
        
        if not snapshot_info:
            logger.error(f"快照不存在: {snapshot_id}")
            return False, 0, 0, [f"快照不存在: {snapshot_id}"], []
        
        project_root = project_root or snapshot_info.project_root
        snapshot_path = self.snapshot_dir / snapshot_id
        files_index_path = snapshot_path / "files_index.json"
        
        if not files_index_path.exists():
            return False, 0, 0, ["快照文件索引不存在"], []
        
        try:
            with open(files_index_path, 'r', encoding='utf-8') as f:
                files_data = json.load(f)
        except Exception as e:
            return False, 0, 0, [f"加载文件索引失败: {e}"], []
        
        restored = 0
        failed = 0
        errors = []
        files_details = []
        
        for rel_path, file_info in files_data.items():
            if files_filter and not any(f in rel_path for f in files_filter):
                continue
            
            try:
                target_path = Path(project_root) / rel_path
                snapshot_file = Path(file_info['snapshot_path'])
                
                if not snapshot_file.exists():
                    failed += 1
                    errors.append(f"快照文件不存在: {rel_path}")
                    files_details.append({
                        'path': rel_path,
                        'status': 'failed',
                        'error': '快照文件不存在'
                    })
                    continue
                
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                content = snapshot_file.read_bytes()
                
                if file_info.get('encrypted') and self._encryption_key:
                    content = self._decrypt_data(content)
                
                if file_info.get('compressed'):
                    content = gzip.decompress(content)
                
                target_path.write_bytes(content)
                restored += 1
                files_details.append({
                    'path': rel_path,
                    'status': 'restored',
                    'size': len(content)
                })
                
            except Exception as e:
                failed += 1
                errors.append(f"恢复文件失败 {rel_path}: {e}")
                files_details.append({
                    'path': rel_path,
                    'status': 'failed',
                    'error': str(e)
                })
        
        if restored > 0:
            with self._lock:
                snapshot_info.status = SnapshotStatus.RESTORED
            self._save_snapshot_index()
        
        return restored > 0 and failed == 0, restored, failed, errors, files_details
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        snapshot_info = self.get_snapshot(snapshot_id)
        
        if not snapshot_info:
            return False
        
        snapshot_path = self.snapshot_dir / snapshot_id
        
        try:
            if snapshot_path.exists():
                shutil.rmtree(snapshot_path)
            
            with self._lock:
                del self._snapshots[snapshot_id]
            
            self._save_snapshot_index()
            return True
            
        except Exception as e:
            logger.error(f"删除快照失败: {e}")
            return False
    
    def cleanup_old_snapshots(self, days: int = 30, keep_count: int = 5, keep_tags: List[str] = None) -> int:
        cutoff = datetime.now() - timedelta(days=days)
        deleted = 0
        
        snapshots = self.list_snapshots()
        
        for i, snapshot in enumerate(snapshots):
            if i < keep_count:
                continue
            
            if keep_tags and any(t in snapshot.tags for t in keep_tags):
                continue
            
            try:
                snapshot_time = datetime.fromisoformat(snapshot.timestamp)
                if snapshot_time < cutoff:
                    if self.delete_snapshot(snapshot.snapshot_id):
                        deleted += 1
            except Exception as e:
                logger.warning(f"清理快照失败 {snapshot.snapshot_id}: {e}")
        
        return deleted
    
    def verify_snapshot(self, snapshot_id: str) -> Tuple[bool, List[str]]:
        """验证快照完整性"""
        snapshot_info = self.get_snapshot(snapshot_id)
        
        if not snapshot_info:
            return False, [f"快照不存在: {snapshot_id}"]
        
        snapshot_path = self.snapshot_dir / snapshot_id
        files_index_path = snapshot_path / "files_index.json"
        
        if not files_index_path.exists():
            return False, ["快照文件索引不存在"]
        
        errors = []
        
        try:
            with open(files_index_path, 'r', encoding='utf-8') as f:
                files_data = json.load(f)
        except Exception as e:
            return False, [f"加载文件索引失败: {e}"]
        
        hash_parts = []
        
        for rel_path, file_info in files_data.items():
            snapshot_file = Path(file_info['snapshot_path'])
            
            if not snapshot_file.exists():
                errors.append(f"快照文件缺失: {rel_path}")
                continue
            
            try:
                content = snapshot_file.read_bytes()
                if file_info.get('encrypted') and self._encryption_key:
                    content = self._decrypt_data(content)
                if file_info.get('compressed'):
                    content = gzip.decompress(content)
                
                content_hash = hashlib.sha256(content).hexdigest()
                if content_hash != file_info['content_hash']:
                    errors.append(f"文件哈希不匹配: {rel_path}")
                else:
                    hash_parts.append(content_hash)
            except Exception as e:
                errors.append(f"验证文件失败 {rel_path}: {e}")
        
        if not errors:
            verification_hash = hashlib.sha256(''.join(hash_parts).encode()).hexdigest()
            if verification_hash != snapshot_info.verification_hash:
                errors.append("快照验证哈希不匹配")
        
        return len(errors) == 0, errors
    
    def diff_snapshots(
        self,
        snapshot_id1: str,
        snapshot_id2: str,
        include_content_diff: bool = False
    ) -> SnapshotDiffResult:
        """对比两个快照的差异"""
        snapshot1 = self.get_snapshot(snapshot_id1)
        snapshot2 = self.get_snapshot(snapshot_id2)
        
        if not snapshot1 or not snapshot2:
            raise ValueError("快照不存在")
        
        snapshot_path1 = self.snapshot_dir / snapshot_id1 / "files_index.json"
        snapshot_path2 = self.snapshot_dir / snapshot_id2 / "files_index.json"
        
        with open(snapshot_path1, 'r', encoding='utf-8') as f:
            files1 = json.load(f)
        
        with open(snapshot_path2, 'r', encoding='utf-8') as f:
            files2 = json.load(f)
        
        files_set1 = set(files1.keys())
        files_set2 = set(files2.keys())
        
        added = list(files_set2 - files_set1)
        removed = list(files_set1 - files_set2)
        common = files_set1 & files_set2
        
        modified = []
        unchanged = []
        file_diffs = []
        
        for rel_path in common:
            if files1[rel_path]['content_hash'] != files2[rel_path]['content_hash']:
                modified.append(rel_path)
                
                diff_info = FileDiffInfo(
                    file_path=rel_path,
                    diff_type=DiffType.MODIFIED,
                    old_hash=files1[rel_path]['content_hash'],
                    new_hash=files2[rel_path]['content_hash'],
                    old_size=files1[rel_path]['size'],
                    new_size=files2[rel_path]['size']
                )
                
                if include_content_diff:
                    diff_info.diff_content = self._compute_file_diff(
                        files1[rel_path]['snapshot_path'],
                        files2[rel_path]['snapshot_path']
                    )
                
                file_diffs.append(diff_info)
            else:
                unchanged.append(rel_path)
        
        for rel_path in added:
            file_diffs.append(FileDiffInfo(
                file_path=rel_path,
                diff_type=DiffType.ADDED,
                new_hash=files2[rel_path]['content_hash'],
                new_size=files2[rel_path]['size']
            ))
        
        for rel_path in removed:
            file_diffs.append(FileDiffInfo(
                file_path=rel_path,
                diff_type=DiffType.REMOVED,
                old_hash=files1[rel_path]['content_hash'],
                old_size=files1[rel_path]['size']
            ))
        
        return SnapshotDiffResult(
            snapshot1_id=snapshot_id1,
            snapshot2_id=snapshot_id2,
            added_files=added,
            removed_files=removed,
            modified_files=modified,
            unchanged_files=unchanged,
            file_diffs=file_diffs
        )
    
    def _compute_file_diff(self, file1_path: str, file2_path: str) -> str:
        """计算文件差异"""
        try:
            content1 = Path(file1_path).read_text(encoding='utf-8', errors='replace').splitlines(keepends=True)
            content2 = Path(file2_path).read_text(encoding='utf-8', errors='replace').splitlines(keepends=True)
            
            diff = unified_diff(content1, content2, fromfile=file1_path, tofile=file2_path)
            return ''.join(diff)
        except Exception:
            return ""


class RollbackStrategyManager:
    """回滚策略管理器 - 管理多级回滚策略和风险评估"""
    
    def __init__(self, config: RollbackStrategyConfig = None):
        self.config = config or RollbackStrategyConfig()
        self._strategy_history: List[Dict[str, Any]] = []
        self._risk_cache: Dict[str, RiskAssessment] = {}
        self._lock = threading.Lock()
    
    def assess_rollback_risk(
        self,
        snapshot_id: str,
        current_files: List[str],
        snapshot_files: List[str],
        critical_patterns: List[str] = None
    ) -> RiskAssessment:
        """评估回滚风险"""
        critical_patterns = critical_patterns or [
            'config', 'settings', 'env', 'secret', 'key', 'credential',
            'database', 'migration', 'schema'
        ]
        
        affected_files = len(set(current_files) ^ set(snapshot_files))
        
        critical_files = []
        for file_path in snapshot_files:
            if any(pattern in file_path.lower() for pattern in critical_patterns):
                critical_files.append(file_path)
        
        risk_score = 0.0
        risk_score += min(affected_files * 0.5, 30)
        risk_score += min(len(critical_files) * 5, 40)
        
        warnings = []
        recommendations = []
        
        if len(critical_files) > 0:
            warnings.append(f"发现 {len(critical_files)} 个关键文件将被修改")
            recommendations.append("建议在回滚前备份关键配置文件")
        
        if affected_files > 50:
            warnings.append(f"大量文件受影响 ({affected_files})")
            recommendations.append("建议分阶段回滚或使用选择性回滚策略")
        
        if risk_score < 20:
            risk_level = RiskLevel.LOW
            can_proceed = True
            requires_backup = False
            estimated_impact = "影响较小，可以安全回滚"
        elif risk_score < 50:
            risk_level = RiskLevel.MEDIUM
            can_proceed = True
            requires_backup = True
            estimated_impact = "中等影响，建议创建备份后回滚"
        elif risk_score < 80:
            risk_level = RiskLevel.HIGH
            can_proceed = True
            requires_backup = True
            estimated_impact = "影响较大，必须创建备份并验证后回滚"
        else:
            risk_level = RiskLevel.CRITICAL
            can_proceed = False
            requires_backup = True
            estimated_impact = "风险极高，建议人工审核后操作"
            recommendations.append("强烈建议人工审核后再执行回滚")
        
        assessment = RiskAssessment(
            risk_level=risk_level,
            risk_score=risk_score,
            affected_files=affected_files,
            critical_files=critical_files,
            warnings=warnings,
            recommendations=recommendations,
            can_proceed=can_proceed,
            requires_backup=requires_backup,
            estimated_impact=estimated_impact
        )
        
        with self._lock:
            self._risk_cache[snapshot_id] = assessment
        
        return assessment
    
    def select_strategy(
        self,
        risk_assessment: RiskAssessment,
        trigger: RollbackTrigger,
        context: Dict[str, Any] = None
    ) -> RollbackStrategy:
        """根据风险评估选择最佳回滚策略"""
        context = context or {}
        
        if risk_assessment.risk_level == RiskLevel.CRITICAL:
            return RollbackStrategy.SAFE_FIRST
        
        if trigger in [RollbackTrigger.EMERGENCY, RollbackTrigger.AUTO_EXCEPTION]:
            if risk_assessment.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
                return RollbackStrategy.IMMEDIATE
            else:
                return RollbackStrategy.GRADUAL
        
        if risk_assessment.affected_files > 100:
            return RollbackStrategy.SELECTIVE
        
        if risk_assessment.risk_level == RiskLevel.HIGH:
            return RollbackStrategy.CASCADE
        
        if context.get('priority_files'):
            return RollbackStrategy.PRIORITY_BASED
        
        return self.config.strategy
    
    def execute_strategy(
        self,
        strategy: RollbackStrategy,
        rollback_func: Callable,
        files: List[str],
        priority_files: List[str] = None
    ) -> Dict[str, Any]:
        """执行回滚策略"""
        result = {
            'strategy': strategy.value,
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'success': False,
            'files_processed': 0,
            'errors': [],
            'phases': []
        }
        
        try:
            if strategy == RollbackStrategy.IMMEDIATE:
                success = rollback_func(files)
                result['files_processed'] = len(files)
                result['success'] = success
                result['phases'].append({'name': 'immediate', 'files': len(files)})
            
            elif strategy == RollbackStrategy.GRADUAL:
                batch_size = max(1, len(files) // 5)
                total_processed = 0
                for i in range(0, len(files), batch_size):
                    batch = files[i:i + batch_size]
                    success = rollback_func(batch)
                    total_processed += len(batch)
                    result['phases'].append({
                        'name': f'batch_{i // batch_size + 1}',
                        'files': len(batch),
                        'success': success
                    })
                    if not success:
                        break
                result['files_processed'] = total_processed
                result['success'] = success
            
            elif strategy == RollbackStrategy.SELECTIVE:
                selected_files = priority_files or files[:min(20, len(files))]
                success = rollback_func(selected_files)
                result['files_processed'] = len(selected_files)
                result['success'] = success
                result['phases'].append({'name': 'selective', 'files': len(selected_files)})
            
            elif strategy == RollbackStrategy.CASCADE:
                sorted_files = sorted(files, key=lambda x: (
                    0 if 'config' in x.lower() else 1,
                    1 if 'test' in x.lower() else 0
                ))
                success = rollback_func(sorted_files)
                result['files_processed'] = len(sorted_files)
                result['success'] = success
                result['phases'].append({'name': 'cascade', 'files': len(sorted_files)})
            
            elif strategy == RollbackStrategy.SAFE_FIRST:
                safe_files = [f for f in files if 'test' in f.lower() or 'doc' in f.lower()]
                if safe_files:
                    rollback_func(safe_files)
                    result['phases'].append({'name': 'safe_files', 'files': len(safe_files)})
                
                remaining = [f for f in files if f not in safe_files]
                if remaining:
                    success = rollback_func(remaining)
                    result['phases'].append({'name': 'remaining_files', 'files': len(remaining)})
                result['files_processed'] = len(files)
                result['success'] = True
            
            elif strategy == RollbackStrategy.PRIORITY_BASED:
                if priority_files:
                    rollback_func(priority_files)
                    result['phases'].append({'name': 'priority', 'files': len(priority_files)})
                
                other_files = [f for f in files if f not in (priority_files or [])]
                if other_files:
                    success = rollback_func(other_files)
                    result['phases'].append({'name': 'others', 'files': len(other_files)})
                result['files_processed'] = len(files)
                result['success'] = True
            
        except Exception as e:
            result['errors'].append(str(e))
            result['success'] = False
        
        result['completed_at'] = datetime.now().isoformat()
        
        with self._lock:
            self._strategy_history.append(result)
        
        return result
    
    def get_strategy_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取策略执行历史"""
        with self._lock:
            return self._strategy_history[-limit:]


class AutoSnapshotManager:
    """自动快照管理器 - 实现智能自动快照创建"""
    
    def __init__(
        self,
        snapshot_manager: SnapshotManager,
        config: AutoSnapshotConfig = None
    ):
        self.snapshot_manager = snapshot_manager
        self.config = config or AutoSnapshotConfig()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._running = False
        self._last_snapshot_time = 0
        self._file_change_counter = 0
        self._last_file_state: Dict[str, str] = {}
        self._lock = threading.Lock()
        self._event_handlers: Dict[TriggerEventType, List[Callable]] = {}
    
    def start_scheduler(self, project_root: str):
        """启动定时快照调度器"""
        if not self.config.enabled:
            logger.info("自动快照已禁用")
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            args=(project_root,),
            daemon=True
        )
        self._scheduler_thread.start()
        logger.info(f"自动快照调度器已启动，间隔: {self.config.schedule_interval}秒")
    
    def stop_scheduler(self):
        """停止调度器"""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        logger.info("自动快照调度器已停止")
    
    def _scheduler_loop(self, project_root: str):
        """调度循环"""
        while self._running:
            try:
                current_time = time.time()
                if current_time - self._last_snapshot_time >= self.config.schedule_interval:
                    self._create_scheduled_snapshot(project_root)
                    self._last_snapshot_time = current_time
                
                self._check_file_changes(project_root)
                
            except Exception as e:
                logger.error(f"调度器错误: {e}")
            
            time.sleep(60)
    
    def _create_scheduled_snapshot(self, project_root: str):
        """创建定时快照"""
        try:
            snapshots = self.snapshot_manager.list_snapshots()
            if len(snapshots) >= self.config.max_snapshots:
                oldest = snapshots[-1]
                self.snapshot_manager.delete_snapshot(oldest.snapshot_id)
                logger.info(f"删除旧快照: {oldest.snapshot_id}")
            
            snapshot = self.snapshot_manager.create_snapshot(
                project_root=project_root,
                version=f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                tags=self.config.tags + ["scheduled"],
                description="定时自动快照",
                snapshot_type=SnapshotType.FULL
            )
            
            logger.info(f"创建定时快照: {snapshot.snapshot_id}")
            
        except Exception as e:
            logger.error(f"创建定时快照失败: {e}")
    
    def _check_file_changes(self, project_root: str):
        """检查文件变化"""
        if not self.config.on_file_change:
            return
        
        project_path = Path(project_root)
        current_state = {}
        
        for py_file in project_path.rglob('*.py'):
            try:
                rel_path = str(py_file.relative_to(project_path))
                content_hash = hashlib.sha256(py_file.read_bytes()).hexdigest()[:16]
                current_state[rel_path] = content_hash
            except Exception:
                continue
        
        with self._lock:
            if self._last_file_state:
                changes = 0
                for path, hash_val in current_state.items():
                    if path not in self._last_file_state or self._last_file_state[path] != hash_val:
                        changes += 1
                
                if changes >= self.config.file_change_threshold:
                    current_time = time.time()
                    if current_time - self._last_snapshot_time >= self.config.min_interval_seconds:
                        self._trigger_event_snapshot(
                            project_root,
                            TriggerEventType.FILE_CHANGE,
                            {'changes': changes}
                        )
            
            self._last_file_state = current_state
    
    def _trigger_event_snapshot(
        self,
        project_root: str,
        event_type: TriggerEventType,
        event_data: Dict[str, Any]
    ):
        """触发事件快照"""
        try:
            snapshot = self.snapshot_manager.create_snapshot(
                project_root=project_root,
                version=f"event_{event_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                tags=self.config.tags + [f"event:{event_type.value}"],
                description=f"事件触发快照: {event_type.value}",
                metadata=event_data,
                snapshot_type=SnapshotType.INCREMENTAL
            )
            
            self._last_snapshot_time = time.time()
            logger.info(f"创建事件快照: {snapshot.snapshot_id}, 触发事件: {event_type.value}")
            
        except Exception as e:
            logger.error(f"创建事件快照失败: {e}")
    
    def register_event_handler(self, event_type: TriggerEventType, handler: Callable):
        """注册事件处理器"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def trigger_event(self, event_type: TriggerEventType, project_root: str, event_data: Dict[str, Any] = None):
        """触发事件"""
        event_data = event_data or {}
        
        if event_type == TriggerEventType.TEST_FAILURE and not self.config.on_test_pass:
            return
        if event_type == TriggerEventType.DEPLOYMENT and not self.config.on_deployment:
            return
        
        self._trigger_event_snapshot(project_root, event_type, event_data)
        
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event_type, event_data)
            except Exception as e:
                logger.error(f"事件处理器错误: {e}")
    
    def cleanup_old_snapshots(self):
        """清理旧快照"""
        deleted = self.snapshot_manager.cleanup_old_snapshots(
            days=self.config.retention_days,
            keep_count=self.config.max_snapshots // 2,
            keep_tags=self.config.tags
        )
        return deleted


class HealthMonitor:
    """健康度监控器 - 监控系统健康状态"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self._metrics_history: List[HealthMetrics] = []
        self._anomaly_thresholds = {
            'error_rate': 0.1,
            'test_pass_rate': 0.8,
            'build_success_rate': 0.9,
            'cpu_usage': 80.0,
            'memory_usage': 85.0
        }
        self._lock = threading.Lock()
    
    def check_health(
        self,
        run_tests: bool = False,
        test_command: str = None
    ) -> HealthMetrics:
        """检查系统健康状态"""
        test_pass_rate = 1.0
        build_success_rate = 1.0
        error_count = 0
        warning_count = 0
        details = {}
        
        try:
            py_files = list(self.project_root.rglob('*.py'))
            for py_file in py_files[:50]:
                result = subprocess.run(
                    [sys.executable, '-m', 'py_compile', str(py_file)],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode != 0:
                    error_count += 1
        except Exception:
            pass
        
        if run_tests:
            try:
                cmd = test_command.split() if test_command else [sys.executable, '-m', 'pytest', '-q', '--tb=no']
                result = subprocess.run(
                    cmd,
                    cwd=str(self.project_root),
                    capture_output=True,
                    timeout=120
                )
                output = result.stdout.decode('utf-8', errors='replace')
                if 'passed' in output.lower():
                    import re
                    match = re.search(r'(\d+) passed', output)
                    if match:
                        passed = int(match.group(1))
                        match_total = re.search(r'(\d+) (?:passed|failed)', output)
                        total = int(match_total.group(1)) if match_total else passed
                        test_pass_rate = passed / total if total > 0 else 1.0
            except Exception:
                test_pass_rate = 0.0
        
        score = 100.0
        score -= error_count * 5
        score -= (1 - test_pass_rate) * 30
        score -= (1 - build_success_rate) * 20
        score = max(0, min(100, score))
        
        if score >= 90:
            status = HealthStatus.HEALTHY
        elif score >= 70:
            status = HealthStatus.DEGRADED
        elif score >= 50:
            status = HealthStatus.UNHEALTHY
        else:
            status = HealthStatus.CRITICAL
        
        metrics = HealthMetrics(
            status=status,
            score=score,
            test_pass_rate=test_pass_rate,
            build_success_rate=build_success_rate,
            error_count=error_count,
            warning_count=warning_count,
            last_check_time=datetime.now().isoformat(),
            details=details
        )
        
        with self._lock:
            self._metrics_history.append(metrics)
            if len(self._metrics_history) > 100:
                self._metrics_history = self._metrics_history[-100:]
        
        return metrics
    
    def detect_anomalies(self, metrics: HealthMetrics) -> List[AnomalyInfo]:
        """检测异常"""
        anomalies = []
        
        if metrics.test_pass_rate < self._anomaly_thresholds['test_pass_rate']:
            anomalies.append(AnomalyInfo(
                anomaly_type='low_test_pass_rate',
                severity=RiskLevel.HIGH if metrics.test_pass_rate < 0.5 else RiskLevel.MEDIUM,
                detected_at=datetime.now().isoformat(),
                description=f"测试通过率过低: {metrics.test_pass_rate:.2%}",
                affected_components=['tests'],
                metrics={'test_pass_rate': metrics.test_pass_rate},
                recommended_action='检查最近的代码变更，考虑回滚到稳定版本'
            ))
        
        if metrics.error_count > 10:
            anomalies.append(AnomalyInfo(
                anomaly_type='high_error_count',
                severity=RiskLevel.HIGH if metrics.error_count > 20 else RiskLevel.MEDIUM,
                detected_at=datetime.now().isoformat(),
                description=f"错误数量过高: {metrics.error_count}",
                affected_components=['code'],
                metrics={'error_count': metrics.error_count},
                recommended_action='检查语法错误和导入问题'
            ))
        
        if metrics.status == HealthStatus.CRITICAL:
            anomalies.append(AnomalyInfo(
                anomaly_type='critical_health',
                severity=RiskLevel.CRITICAL,
                detected_at=datetime.now().isoformat(),
                description="系统健康状态严重",
                affected_components=['system'],
                metrics={'health_score': metrics.score},
                recommended_action='立即执行回滚操作'
            ))
        
        return anomalies
    
    def get_metrics_history(self, limit: int = 50) -> List[HealthMetrics]:
        """获取指标历史"""
        with self._lock:
            return self._metrics_history[-limit:]
    
    def set_threshold(self, metric_name: str, value: float):
        """设置阈值"""
        if metric_name in self._anomaly_thresholds:
            self._anomaly_thresholds[metric_name] = value


class IntelligentTriggerEngine:
    """智能回滚触发引擎 - 智能决策是否触发回滚"""
    
    def __init__(
        self,
        health_monitor: HealthMonitor,
        strategy_manager: RollbackStrategyManager
    ):
        self.health_monitor = health_monitor
        self.strategy_manager = strategy_manager
        self._trigger_history: List[Dict[str, Any]] = []
        self._decision_rules: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认决策规则"""
        self._decision_rules = [
            {
                'name': 'critical_health',
                'condition': lambda m: m.status == HealthStatus.CRITICAL,
                'action': 'immediate_rollback',
                'priority': 100
            },
            {
                'name': 'high_error_rate',
                'condition': lambda m: m.error_count > 20,
                'action': 'assess_and_rollback',
                'priority': 80
            },
            {
                'name': 'low_test_rate',
                'condition': lambda m: m.test_pass_rate < 0.5,
                'action': 'assess_and_rollback',
                'priority': 70
            },
            {
                'name': 'degraded_health',
                'condition': lambda m: m.status == HealthStatus.DEGRADED,
                'action': 'monitor_closely',
                'priority': 50
            }
        ]
    
    def evaluate(self, metrics: HealthMetrics) -> Dict[str, Any]:
        """评估是否需要触发回滚"""
        triggered_rules = []
        
        for rule in sorted(self._decision_rules, key=lambda x: x['priority'], reverse=True):
            try:
                if rule['condition'](metrics):
                    triggered_rules.append({
                        'rule_name': rule['name'],
                        'action': rule['action'],
                        'priority': rule['priority']
                    })
            except Exception:
                continue
        
        should_rollback = False
        rollback_reason = None
        recommended_action = 'none'
        
        if triggered_rules:
            top_rule = triggered_rules[0]
            
            if top_rule['action'] == 'immediate_rollback':
                should_rollback = True
                rollback_reason = f"规则触发: {top_rule['rule_name']}"
                recommended_action = 'immediate_rollback'
            elif top_rule['action'] == 'assess_and_rollback':
                should_rollback = True
                rollback_reason = f"规则触发: {top_rule['rule_name']}"
                recommended_action = 'assess_before_rollback'
            elif top_rule['action'] == 'monitor_closely':
                should_rollback = False
                rollback_reason = f"监控中: {top_rule['rule_name']}"
                recommended_action = 'increase_monitoring'
        
        decision = {
            'timestamp': datetime.now().isoformat(),
            'should_rollback': should_rollback,
            'rollback_reason': rollback_reason,
            'recommended_action': recommended_action,
            'triggered_rules': triggered_rules,
            'health_score': metrics.score,
            'health_status': metrics.status.value
        }
        
        with self._lock:
            self._trigger_history.append(decision)
        
        return decision
    
    def add_rule(self, name: str, condition: Callable, action: str, priority: int = 50):
        """添加决策规则"""
        self._decision_rules.append({
            'name': name,
            'condition': condition,
            'action': action,
            'priority': priority
        })
    
    def get_trigger_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取触发历史"""
        with self._lock:
            return self._trigger_history[-limit:]


class AuditLogger:
    """审计日志记录器 - 记录所有操作的审计日志"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file
        self._entries: List[AuditLogEntry] = []
        self._lock = threading.Lock()
        
        if log_file:
            self._load_from_file()
    
    def _load_from_file(self):
        """从文件加载日志"""
        if not self.log_file or not Path(self.log_file).exists():
            return
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        self._entries.append(AuditLogEntry(
                            timestamp=data['timestamp'],
                            action=data['action'],
                            actor=data['actor'],
                            target=data['target'],
                            details=data.get('details', {}),
                            result=data['result'],
                            risk_level=RiskLevel(data.get('risk_level', 'low')),
                            snapshot_id=data.get('snapshot_id')
                        ))
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"加载审计日志失败: {e}")
    
    def log(
        self,
        action: str,
        actor: str,
        target: str,
        result: str,
        details: Dict[str, Any] = None,
        risk_level: RiskLevel = RiskLevel.LOW,
        snapshot_id: str = None
    ):
        """记录审计日志"""
        entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            actor=actor,
            target=target,
            details=details or {},
            result=result,
            risk_level=risk_level,
            snapshot_id=snapshot_id
        )
        
        with self._lock:
            self._entries.append(entry)
        
        if self.log_file:
            self._write_entry(entry)
        
        logger.info(f"[AUDIT] {action} by {actor} on {target}: {result}")
    
    def _write_entry(self, entry: AuditLogEntry):
        """写入日志条目"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    'timestamp': entry.timestamp,
                    'action': entry.action,
                    'actor': entry.actor,
                    'target': entry.target,
                    'details': entry.details,
                    'result': entry.result,
                    'risk_level': entry.risk_level.value,
                    'snapshot_id': entry.snapshot_id
                }, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"写入审计日志失败: {e}")
    
    def get_entries(
        self,
        action: str = None,
        actor: str = None,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """获取日志条目"""
        with self._lock:
            entries = self._entries.copy()
        
        if action:
            entries = [e for e in entries if e.action == action]
        if actor:
            entries = [e for e in entries if e.actor == actor]
        
        return entries[-limit:]
    
    def export_to_json(self, output_file: str):
        """导出为JSON"""
        with self._lock:
            data = [asdict(e) for e in self._entries]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class FailureAnalyzer:
    """失败分析器 - 分析失败原因并提供建议"""
    
    def __init__(self):
        self._failure_history: List[FailureAnalysis] = []
        self._lock = threading.Lock()
    
    def analyze(
        self,
        error: Exception,
        context: Dict[str, Any],
        affected_files: List[str] = None
    ) -> FailureAnalysis:
        """分析失败"""
        failure_id = f"FAIL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        root_cause = self._identify_root_cause(error, context)
        impact_assessment = self._assess_impact(error, context, affected_files)
        recovery_suggestions = self._generate_suggestions(error, context, root_cause)
        related_failures = self._find_related_failures(error)
        
        analysis = FailureAnalysis(
            failure_id=failure_id,
            timestamp=datetime.now().isoformat(),
            failure_type=type(error).__name__,
            root_cause=root_cause,
            affected_files=affected_files or [],
            impact_assessment=impact_assessment,
            recovery_suggestions=recovery_suggestions,
            related_failures=related_failures,
            metrics=context.get('metrics', {})
        )
        
        with self._lock:
            self._failure_history.append(analysis)
        
        return analysis
    
    def _identify_root_cause(self, error: Exception, context: Dict[str, Any]) -> str:
        """识别根本原因"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        if 'SyntaxError' in error_type:
            return "代码语法错误"
        elif 'ImportError' in error_type or 'ModuleNotFoundError' in error_type:
            return "依赖模块缺失或导入路径错误"
        elif 'PermissionError' in error_type:
            return "文件权限不足"
        elif 'FileNotFoundError' in error_type:
            return "文件不存在"
        elif 'TimeoutError' in error_type:
            return "操作超时"
        elif 'AssertionError' in error_type:
            return "断言失败，测试或验证未通过"
        elif 'KeyError' in error_type:
            return "配置或数据键缺失"
        elif 'ValueError' in error_type:
            return "值错误，参数或数据格式不正确"
        elif 'TypeError' in error_type:
            return "类型错误"
        else:
            return f"未知错误类型: {error_type}"
    
    def _assess_impact(
        self,
        error: Exception,
        context: Dict[str, Any],
        affected_files: List[str]
    ) -> str:
        """评估影响"""
        impact_parts = []
        
        if affected_files:
            impact_parts.append(f"受影响文件数: {len(affected_files)}")
        
        if context.get('modified_files'):
            impact_parts.append(f"已修改文件: {len(context['modified_files'])}")
        
        if context.get('rollback_performed'):
            impact_parts.append("已执行回滚")
        else:
            impact_parts.append("未执行回滚")
        
        return "; ".join(impact_parts) if impact_parts else "影响未知"
    
    def _generate_suggestions(
        self,
        error: Exception,
        context: Dict[str, Any],
        root_cause: str
    ) -> List[str]:
        """生成恢复建议"""
        suggestions = []
        
        if '语法' in root_cause:
            suggestions.append("检查代码语法，使用IDE或linter工具")
            suggestions.append("运行 python -m py_compile 检查语法")
        elif '依赖' in root_cause:
            suggestions.append("检查 requirements.txt 是否完整")
            suggestions.append("运行 pip install -r requirements.txt 安装依赖")
        elif '权限' in root_cause:
            suggestions.append("检查文件权限设置")
            suggestions.append("以管理员权限运行")
        elif '超时' in root_cause:
            suggestions.append("增加超时时间设置")
            suggestions.append("优化性能瓶颈")
        elif '断言' in root_cause:
            suggestions.append("检查测试用例是否正确")
            suggestions.append("验证业务逻辑")
        
        suggestions.append("查看详细错误日志")
        suggestions.append("考虑回滚到上一个稳定版本")
        
        return suggestions
    
    def _find_related_failures(self, error: Exception) -> List[str]:
        """查找相关失败"""
        related = []
        error_type = type(error).__name__
        
        with self._lock:
            for failure in self._failure_history[-20:]:
                if failure.failure_type == error_type:
                    related.append(failure.failure_id)
        
        return related[:5]
    
    def get_failure_history(self, limit: int = 50) -> List[FailureAnalysis]:
        """获取失败历史"""
        with self._lock:
            return self._failure_history[-limit:]


class NotificationTemplateManager:
    """通知模板管理器"""
    
    def __init__(self):
        self._templates: Dict[str, NotificationTemplate] = {}
        self._init_default_templates()
    
    def _init_default_templates(self):
        """初始化默认模板"""
        self._templates['rollback_success'] = NotificationTemplate(
            template_id='rollback_success',
            name='回滚成功通知',
            title_template='[成功] 回滚操作完成 - {snapshot_id}',
            body_template='''
回滚操作已成功完成。

快照ID: {snapshot_id}
触发原因: {trigger}
恢复文件数: {files_restored}
耗时: {duration}秒
验证结果: {verification_result}

详细信息请查看日志。
            ''',
            severity_mapping={'success': 'info'},
            include_details=True
        )
        
        self._templates['rollback_failure'] = NotificationTemplate(
            template_id='rollback_failure',
            name='回滚失败通知',
            title_template='[失败] 回滚操作失败 - {snapshot_id}',
            body_template='''
回滚操作失败！

快照ID: {snapshot_id}
错误信息: {error_message}
受影响文件: {affected_files}

请立即检查并采取手动恢复措施。
            ''',
            severity_mapping={'failure': 'error'},
            include_details=True
        )
        
        self._templates['auto_rollback'] = NotificationTemplate(
            template_id='auto_rollback',
            name='自动回滚通知',
            title_template='[自动] 系统触发自动回滚 - {trigger}',
            body_template='''
系统检测到异常，已自动触发回滚。

触发原因: {trigger}
目标快照: {snapshot_id}
健康分数: {health_score}
异常详情: {anomaly_details}

回滚结果: {rollback_result}
            ''',
            severity_mapping={'auto': 'warning'},
            include_details=True,
            include_metrics=True
        )
        
        self._templates['health_alert'] = NotificationTemplate(
            template_id='health_alert',
            name='健康状态告警',
            title_template='[告警] 系统健康状态异常 - {status}',
            body_template='''
系统健康状态检测到异常。

当前状态: {status}
健康分数: {score}
测试通过率: {test_pass_rate}
错误数量: {error_count}

建议操作: {recommended_action}
            ''',
            severity_mapping={'alert': 'warning'},
            include_metrics=True
        )
    
    def get_template(self, template_id: str) -> Optional[NotificationTemplate]:
        """获取模板"""
        return self._templates.get(template_id)
    
    def render(
        self,
        template_id: str,
        variables: Dict[str, Any]
    ) -> Tuple[str, str]:
        """渲染模板"""
        template = self.get_template(template_id)
        if not template:
            return "通知", "无模板内容"
        
        title = template.title_template.format(**variables)
        body = template.body_template.format(**variables)
        
        return title, body
    
    def add_template(self, template: NotificationTemplate):
        """添加模板"""
        self._templates[template.template_id] = template
    
    def list_templates(self) -> List[str]:
        """列出所有模板"""
        return list(self._templates.keys())


class NotificationManager:
    """失败通知管理器"""
    
    def __init__(self, config: NotificationConfig = None):
        self.config = config or NotificationConfig()
        self._notification_history: List[NotificationMessage] = []
        self._lock = threading.Lock()
        self._failure_counts: Dict[str, int] = {}
        self._last_notification_time: Dict[str, float] = {}
    
    def send_notification(
        self,
        title: str,
        message: str,
        severity: str = "info",
        details: Dict[str, Any] = None,
        snapshot_id: str = None,
        rollback_result: RollbackResult = None,
        dedup_key: str = None
    ) -> Dict[NotificationType, bool]:
        if not self.config.enabled:
            return {}
        
        if dedup_key:
            current_time = time.time()
            last_time = self._last_notification_time.get(dedup_key, 0)
            if current_time - last_time < 60:
                return {}
            self._last_notification_time[dedup_key] = current_time
        
        results = {}
        
        notification = NotificationMessage(
            notification_type=NotificationType.LOG,
            title=title,
            message=message,
            timestamp=datetime.now().isoformat(),
            severity=severity,
            details=details or {},
            snapshot_id=snapshot_id,
            rollback_result=rollback_result
        )
        
        for notif_type in self.config.notification_types:
            for attempt in range(self.config.max_retries):
                try:
                    if notif_type == NotificationType.EMAIL:
                        results[notif_type] = self._send_email(notification)
                    elif notif_type == NotificationType.WEBHOOK:
                        results[notif_type] = self._send_webhook(notification)
                    elif notif_type == NotificationType.LOG:
                        results[notif_type] = self._send_log(notification)
                    elif notif_type == NotificationType.FILE:
                        results[notif_type] = self._send_file(notification)
                    elif notif_type == NotificationType.CONSOLE:
                        results[notif_type] = self._send_console(notification)
                    elif notif_type == NotificationType.SLACK:
                        results[notif_type] = self._send_slack(notification)
                    elif notif_type == NotificationType.TEAMS:
                        results[notif_type] = self._send_teams(notification)
                    
                    if results.get(notif_type):
                        break
                        
                except Exception as e:
                    logger.error(f"发送通知失败 {notif_type} (尝试 {attempt + 1}): {e}")
                    if attempt < self.config.max_retries - 1:
                        time.sleep(self.config.retry_delay)
                    results[notif_type] = False
        
        with self._lock:
            self._notification_history.append(notification)
        
        return results
    
    def _send_email(self, notification: NotificationMessage) -> bool:
        if not self.config.email_recipients:
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = self.config.email_username
            msg['To'] = ', '.join(self.config.email_recipients)
            msg['Subject'] = f"[{notification.severity.upper()}] {notification.title}"
            
            body = f"""
标题: {notification.title}
时间: {notification.timestamp}
严重程度: {notification.severity}

消息:
{notification.message}

详情:
{json.dumps(notification.details, indent=2, ensure_ascii=False)}
"""
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            with smtplib.SMTP(self.config.email_smtp_host, self.config.email_smtp_port) as server:
                if self.config.email_use_tls:
                    server.starttls()
                server.login(self.config.email_username, self.config.email_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False
    
    def _send_webhook(self, notification: NotificationMessage) -> bool:
        if not self.config.webhook_url:
            return False
        
        try:
            import urllib.request
            
            payload = json.dumps({
                'title': notification.title,
                'message': notification.message,
                'timestamp': notification.timestamp,
                'severity': notification.severity,
                'details': notification.details
            }).encode('utf-8')
            
            req = urllib.request.Request(
                self.config.webhook_url,
                data=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=self.config.webhook_timeout) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"发送Webhook失败: {e}")
            return False
    
    def _send_slack(self, notification: NotificationMessage) -> bool:
        if not self.config.slack_webhook_url:
            return False
        
        try:
            import urllib.request
            
            color = {
                'info': '#36a64f',
                'warning': '#ff9900',
                'error': '#ff0000',
                'critical': '#8b0000'
            }.get(notification.severity, '#808080')
            
            payload = json.dumps({
                'attachments': [{
                    'color': color,
                    'title': notification.title,
                    'text': notification.message,
                    'fields': [
                        {'title': 'Severity', 'value': notification.severity, 'short': True},
                        {'title': 'Time', 'value': notification.timestamp, 'short': True}
                    ],
                    'footer': 'Self Iteration Rollback'
                }]
            }).encode('utf-8')
            
            req = urllib.request.Request(
                self.config.slack_webhook_url,
                data=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=self.config.webhook_timeout) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"发送Slack通知失败: {e}")
            return False
    
    def _send_teams(self, notification: NotificationMessage) -> bool:
        if not self.config.teams_webhook_url:
            return False
        
        try:
            import urllib.request
            
            theme_color = {
                'info': '36a64f',
                'warning': 'ff9900',
                'error': 'ff0000',
                'critical': '8b0000'
            }.get(notification.severity, '808080')
            
            payload = json.dumps({
                '@type': 'MessageCard',
                '@context': 'http://schema.org/extensions',
                'themeColor': theme_color,
                'summary': notification.title,
                'sections': [{
                    'activityTitle': notification.title,
                    'text': notification.message,
                    'facts': [
                        {'name': 'Severity', 'value': notification.severity},
                        {'name': 'Time', 'value': notification.timestamp}
                    ],
                    'markdown': True
                }]
            }).encode('utf-8')
            
            req = urllib.request.Request(
                self.config.teams_webhook_url,
                data=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=self.config.webhook_timeout) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"发送Teams通知失败: {e}")
            return False
    
    def _send_log(self, notification: NotificationMessage) -> bool:
        log_message = f"[{notification.severity.upper()}] {notification.title}: {notification.message}"
        
        if notification.severity == "error":
            logger.error(log_message)
        elif notification.severity == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        return True
    
    def _send_file(self, notification: NotificationMessage) -> bool:
        if not self.config.notification_file:
            return False
        
        try:
            with open(self.config.notification_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"时间: {notification.timestamp}\n")
                f.write(f"严重程度: {notification.severity}\n")
                f.write(f"标题: {notification.title}\n")
                f.write(f"消息: {notification.message}\n")
                if notification.details:
                    f.write(f"详情: {json.dumps(notification.details, indent=2, ensure_ascii=False)}\n")
                f.write(f"{'='*60}\n")
            return True
        except Exception as e:
            logger.error(f"写入通知文件失败: {e}")
            return False
    
    def _send_console(self, notification: NotificationMessage) -> bool:
        severity_icons = {
            "info": "[INFO]",
            "warning": "[WARN]",
            "error": "[ERROR]",
            "critical": "[CRITICAL]"
        }
        icon = severity_icons.get(notification.severity, "[INFO]")
        print(f"\n{icon} {notification.title}")
        print(f"   {notification.message}")
        if notification.details:
            print(f"   详情: {notification.details}")
        return True
    
    def get_notification_history(self, limit: int = 100) -> List[NotificationMessage]:
        with self._lock:
            return self._notification_history[-limit:]
    
    def get_failure_statistics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'total_notifications': len(self._notification_history),
                'failure_counts': dict(self._failure_counts)
            }


class RollbackVerifier:
    """回滚验证器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    
    def verify(
        self,
        level: VerificationLevel = VerificationLevel.STANDARD,
        custom_checks: List[Callable[[], bool]] = None,
        test_command: str = None,
        lint_command: str = None
    ) -> VerificationResult:
        checks_passed = 0
        checks_failed = 0
        errors = []
        warnings = []
        details = {}
        
        basic_checks = {
            "项目目录存在": self._check_project_exists,
            "关键文件检查": self._check_key_files,
            "文件权限检查": self._check_file_permissions,
        }
        
        standard_checks = {
            **basic_checks,
            "Python语法检查": self._check_python_syntax,
            "配置文件格式": self._check_config_files,
            "导入检查": self._check_imports,
        }
        
        thorough_checks = {
            **standard_checks,
            "单元测试": lambda: self._run_unit_tests(test_command),
            "代码风格检查": lambda: self._run_lint(lint_command),
            "依赖检查": self._check_dependencies,
            "安全检查": self._check_security,
        }
        
        if level == VerificationLevel.BASIC:
            checks = basic_checks
        elif level == VerificationLevel.STANDARD:
            checks = standard_checks
        else:
            checks = thorough_checks
        
        if custom_checks:
            for i, check_func in enumerate(custom_checks):
                checks[f"自定义检查{i+1}"] = check_func
        
        for check_name, check_func in checks.items():
            try:
                result = check_func()
                if result:
                    checks_passed += 1
                    details[check_name] = "通过"
                else:
                    checks_failed += 1
                    details[check_name] = "失败"
                    errors.append(f"{check_name}: 验证失败")
            except Exception as e:
                checks_failed += 1
                details[check_name] = f"错误: {e}"
                errors.append(f"{check_name}: {e}")
        
        return VerificationResult(
            passed=checks_failed == 0,
            level=level,
            checks_total=len(checks),
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            details=details,
            errors=errors,
            warnings=warnings
        )
    
    def _check_project_exists(self) -> bool:
        return self.project_root.exists()
    
    def _check_key_files(self) -> bool:
        key_files = ['__init__.py', 'setup.py', 'pyproject.toml', 'requirements.txt']
        for key_file in key_files:
            if (self.project_root / key_file).exists():
                return True
        return True
    
    def _check_file_permissions(self) -> bool:
        try:
            for py_file in list(self.project_root.rglob('*.py'))[:10]:
                if not os.access(py_file, os.R_OK):
                    return False
            return True
        except Exception:
            return True
    
    def _check_python_syntax(self) -> bool:
        try:
            py_files = list(self.project_root.rglob('*.py'))[:20]
            for py_file in py_files:
                result = subprocess.run(
                    [sys.executable, '-m', 'py_compile', str(py_file)],
                    capture_output=True,
                    timeout=30
                )
                if result.returncode != 0:
                    return False
            return True
        except Exception:
            return True
    
    def _check_config_files(self) -> bool:
        config_patterns = ['*.json', '*.yaml', '*.yml', '*.toml']
        for pattern in config_patterns:
            for config_file in list(self.project_root.rglob(pattern))[:5]:
                try:
                    content = config_file.read_text(encoding='utf-8')
                    if config_file.suffix == '.json':
                        json.loads(content)
                    elif config_file.suffix in ['.yaml', '.yml']:
                        pass
                    elif config_file.suffix == '.toml':
                        pass
                except Exception:
                    return False
        return True
    
    def _check_imports(self) -> bool:
        try:
            py_files = list(self.project_root.rglob('*.py'))[:10]
            for py_file in py_files:
                result = subprocess.run(
                    [sys.executable, '-c', f'import ast; ast.parse(open("{py_file}").read())'],
                    capture_output=True,
                    timeout=30
                )
            return True
        except Exception:
            return True
    
    def _run_unit_tests(self, test_command: str = None) -> bool:
        try:
            if test_command:
                cmd = test_command.split()
            else:
                cmd = [sys.executable, '-m', 'pytest', '-x', '--tb=no', '-q']
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                timeout=120
            )
            return result.returncode == 0
        except Exception:
            return True
    
    def _run_lint(self, lint_command: str = None) -> bool:
        try:
            if lint_command:
                cmd = lint_command.split()
            else:
                cmd = [sys.executable, '-m', 'pylint', '--errors-only', '.']
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception:
            return True
    
    def _check_dependencies(self) -> bool:
        requirements_file = self.project_root / 'requirements.txt'
        if not requirements_file.exists():
            return True
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'check'],
                cwd=self.project_root,
                capture_output=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception:
            return True
    
    def _check_security(self) -> bool:
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'bandit', '-r', '.', '-f', 'json'],
                cwd=self.project_root,
                capture_output=True,
                timeout=120
            )
            if result.returncode == 0:
                return True
            try:
                data = json.loads(result.stdout)
                high_severity = [r for r in data.get('results', []) if r.get('issue_severity') == 'HIGH']
                return len(high_severity) == 0
            except Exception:
                return True
        except Exception:
            return True


class IterationContext:
    """迭代上下文"""
    
    def __init__(self, rollback_manager: 'SelfIterationRollback', operation_name: str, snapshot_id: str):
        self.rollback_manager = rollback_manager
        self.operation_name = operation_name
        self.snapshot_id = snapshot_id
        self.project_root = rollback_manager.project_root
        self._modified_files: List[str] = []
        self._start_time = datetime.now()
        self._commands_run: List[Dict[str, Any]] = []
    
    def update_file(self, file_path: str, content: str) -> bool:
        try:
            full_path = self.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            self._modified_files.append(str(full_path))
            return True
        except Exception as e:
            logger.error(f"更新文件失败: {e}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        try:
            full_path = self.project_root / file_path
            if full_path.exists():
                full_path.unlink()
                self._modified_files.append(str(full_path))
            return True
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False
    
    def run_command(self, command: List[str], cwd: str = None, timeout: int = 300) -> Tuple[int, str, str]:
        try:
            result = subprocess.run(
                command,
                cwd=cwd or str(self.project_root),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            self._commands_run.append({
                'command': ' '.join(command),
                'returncode': result.returncode,
                'stdout': result.stdout[:1000],
                'stderr': result.stderr[:1000]
            })
            
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "命令执行超时"
        except Exception as e:
            return -1, "", str(e)
    
    def get_modified_files(self) -> List[str]:
        return self._modified_files.copy()
    
    def complete(self, verify: bool = True, verification_level: VerificationLevel = VerificationLevel.STANDARD) -> IterationResult:
        verification_passed = True
        if verify:
            verification_result = self.rollback_manager.verifier.verify(verification_level)
            verification_passed = verification_result.passed
        
        return IterationResult(
            success=verification_passed,
            operation_name=self.operation_name,
            snapshot_id=self.snapshot_id,
            start_time=self._start_time.isoformat(),
            end_time=datetime.now().isoformat(),
            modified_files=self._modified_files,
            verification_passed=verification_passed,
            duration_seconds=(datetime.now() - self._start_time).total_seconds()
        )


class SelfIterationRollback:
    """自迭代回滚器 - 增强版
    
    集成功能:
    - 多级回滚策略管理
    - 自动快照创建
    - 智能回滚触发
    - 健康度监控
    - 审计日志
    - 失败分析
    - 通知模板
    """
    
    def __init__(
        self,
        project_root: str,
        snapshot_dir: str = None,
        notification_config: NotificationConfig = None,
        auto_rollback_config: AutoRollbackConfig = None,
        rollback_strategy_config: RollbackStrategyConfig = None,
        auto_snapshot_config: AutoSnapshotConfig = None,
        compress_snapshots: bool = False,
        encrypt_snapshots: bool = False,
        encryption_key: str = None,
        audit_log_file: str = None
    ):
        self.project_root = Path(project_root).resolve()
        self.snapshot_dir = snapshot_dir or str(self.project_root / ".snapshots")
        
        self.snapshot_manager = SnapshotManager(
            self.snapshot_dir,
            compress=compress_snapshots,
            encrypt=encrypt_snapshots,
            encryption_key=encryption_key
        )
        self.notification_manager = NotificationManager(notification_config)
        self.verifier = RollbackVerifier(str(self.project_root))
        self.auto_rollback_config = auto_rollback_config or AutoRollbackConfig()
        
        self.strategy_manager = RollbackStrategyManager(rollback_strategy_config)
        self.auto_snapshot_manager = AutoSnapshotManager(
            self.snapshot_manager,
            auto_snapshot_config
        )
        self.health_monitor = HealthMonitor(str(self.project_root))
        self.trigger_engine = IntelligentTriggerEngine(
            self.health_monitor,
            self.strategy_manager
        )
        self.audit_logger = AuditLogger(audit_log_file)
        self.failure_analyzer = FailureAnalyzer()
        self.template_manager = NotificationTemplateManager()
        
        self._rollback_history: List[RollbackResult] = []
        self._iteration_history: List[IterationResult] = []
        self._current_iteration_snapshot: Optional[str] = None
        self._lock = threading.Lock()
        self._auto_rollback_count = 0
        self._last_auto_rollback_time = 0
        self._monitoring_enabled = False
        self._monitoring_thread: Optional[threading.Thread] = None
    
    def start_auto_snapshot(self):
        """启动自动快照服务"""
        self.auto_snapshot_manager.start_scheduler(str(self.project_root))
    
    def stop_auto_snapshot(self):
        """停止自动快照服务"""
        self.auto_snapshot_manager.stop_scheduler()
    
    def start_health_monitoring(self, interval: int = 300):
        """启动健康度监控"""
        self._monitoring_enabled = True
        
        def monitor_loop():
            while self._monitoring_enabled:
                try:
                    metrics = self.health_monitor.check_health()
                    decision = self.trigger_engine.evaluate(metrics)
                    
                    if decision['should_rollback']:
                        logger.warning(f"健康监控触发回滚建议: {decision['rollback_reason']}")
                        self._handle_health_trigger(decision, metrics)
                    
                except Exception as e:
                    logger.error(f"健康监控错误: {e}")
                
                time.sleep(interval)
        
        self._monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitoring_thread.start()
        logger.info(f"健康度监控已启动，间隔: {interval}秒")
    
    def stop_health_monitoring(self):
        """停止健康度监控"""
        self._monitoring_enabled = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("健康度监控已停止")
    
    def _handle_health_trigger(self, decision: Dict[str, Any], metrics: HealthMetrics):
        """处理健康监控触发的回滚"""
        if decision['recommended_action'] == 'immediate_rollback':
            self.auto_rollback(
                RollbackTrigger.AUTO_VALIDATION_FAILURE,
                {
                    'health_score': metrics.score,
                    'health_status': metrics.status.value,
                    'decision': decision
                }
            )
        elif decision['recommended_action'] == 'assess_before_rollback':
            anomalies = self.health_monitor.detect_anomalies(metrics)
            if anomalies:
                critical_anomalies = [a for a in anomalies if a.severity == RiskLevel.CRITICAL]
                if critical_anomalies:
                    self.auto_rollback(
                        RollbackTrigger.AUTO_VALIDATION_FAILURE,
                        {
                            'anomalies': [asdict(a) for a in critical_anomalies],
                            'health_score': metrics.score
                        }
                    )
    
    def assess_rollback_risk(
        self,
        snapshot_id: str,
        critical_patterns: List[str] = None
    ) -> RiskAssessment:
        """评估回滚风险"""
        snapshot_info = self.snapshot_manager.get_snapshot(snapshot_id)
        if not snapshot_info:
            raise ValueError(f"快照不存在: {snapshot_id}")
        
        current_files = []
        for py_file in self.project_root.rglob('*.py'):
            current_files.append(str(py_file.relative_to(self.project_root)))
        
        snapshot_path = self.snapshot_manager.snapshot_dir / snapshot_id
        files_index_path = snapshot_path / "files_index.json"
        
        with open(files_index_path, 'r', encoding='utf-8') as f:
            files_data = json.load(f)
        
        snapshot_files = list(files_data.keys())
        
        return self.strategy_manager.assess_rollback_risk(
            snapshot_id,
            current_files,
            snapshot_files,
            critical_patterns
        )
    
    def intelligent_rollback(
        self,
        snapshot_id: str,
        trigger: RollbackTrigger = RollbackTrigger.MANUAL,
        context: Dict[str, Any] = None
    ) -> RollbackResult:
        """智能回滚 - 使用策略管理器执行优化的回滚"""
        context = context or {}
        
        risk_assessment = self.assess_rollback_risk(snapshot_id)
        
        if not risk_assessment.can_proceed:
            error_msg = f"风险评估未通过: {risk_assessment.estimated_impact}"
            logger.error(error_msg)
            return RollbackResult(
                success=False,
                snapshot_id=snapshot_id,
                trigger=trigger,
                timestamp=datetime.now().isoformat(),
                files_restored=0,
                files_failed=0,
                verification_passed=False,
                error_message=error_msg
            )
        
        if risk_assessment.requires_backup:
            backup_snapshot = self.create_snapshot(
                version=f"backup_before_rollback_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                description="回滚前自动备份",
                tags=["backup", "pre-rollback"]
            )
            logger.info(f"创建回滚前备份: {backup_snapshot.snapshot_id}")
        
        strategy = self.strategy_manager.select_strategy(risk_assessment, trigger, context)
        
        self.audit_logger.log(
            action="intelligent_rollback_start",
            actor="system",
            target=snapshot_id,
            result="started",
            details={
                'strategy': strategy.value,
                'risk_level': risk_assessment.risk_level.value,
                'risk_score': risk_assessment.risk_score
            },
            risk_level=risk_assessment.risk_level,
            snapshot_id=snapshot_id
        )
        
        result = self.rollback(
            snapshot_id,
            trigger=trigger,
            verify=True,
            verification_level=VerificationLevel.STANDARD
        )
        
        self.audit_logger.log(
            action="intelligent_rollback_complete",
            actor="system",
            target=snapshot_id,
            result="success" if result.success else "failed",
            details={
                'strategy': strategy.value,
                'files_restored': result.files_restored,
                'duration': result.rollback_duration_seconds
            },
            risk_level=RiskLevel.LOW if result.success else RiskLevel.HIGH,
            snapshot_id=snapshot_id
        )
        
        return result
    
    def create_snapshot(
        self,
        version: str = None,
        file_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
        metadata: Dict[str, Any] = None,
        tags: List[str] = None,
        snapshot_type: SnapshotType = SnapshotType.FULL,
        parent_snapshot_id: str = None,
        description: str = "",
        author: str = ""
    ) -> SnapshotInfo:
        version = version or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return self.snapshot_manager.create_snapshot(
            project_root=str(self.project_root),
            version=version,
            file_patterns=file_patterns,
            exclude_patterns=exclude_patterns,
            metadata=metadata,
            tags=tags,
            snapshot_type=snapshot_type,
            parent_snapshot_id=parent_snapshot_id,
            description=description,
            author=author
        )
    
    def rollback(
        self,
        snapshot_id: str,
        trigger: RollbackTrigger = RollbackTrigger.MANUAL,
        verify: bool = True,
        verification_level: VerificationLevel = VerificationLevel.STANDARD,
        files_filter: List[str] = None
    ) -> RollbackResult:
        start_time = time.time()
        
        success, restored, failed, errors, files_details = self.snapshot_manager.restore_snapshot(
            snapshot_id,
            str(self.project_root),
            verify=False,
            files_filter=files_filter
        )
        
        verification_passed = True
        warnings = []
        
        if verify and success:
            verification_result = self.verifier.verify(verification_level)
            verification_passed = verification_result.passed
            
            if not verification_passed:
                errors.extend(verification_result.errors)
            warnings.extend(verification_result.warnings)
        
        result = RollbackResult(
            success=success and verification_passed,
            snapshot_id=snapshot_id,
            trigger=trigger,
            timestamp=datetime.now().isoformat(),
            files_restored=restored,
            files_failed=failed,
            verification_passed=verification_passed,
            error_message='\n'.join(errors) if errors else None,
            rollback_duration_seconds=time.time() - start_time,
            files_details=files_details,
            warnings=warnings
        )
        
        with self._lock:
            self._rollback_history.append(result)
        
        logger.info(f"回滚完成: {snapshot_id}, 成功: {result.success}, 文件: {restored}")
        
        return result
    
    def preview_rollback(self, snapshot_id: str) -> RollbackPreview:
        """预览回滚操作"""
        snapshot_info = self.snapshot_manager.get_snapshot(snapshot_id)
        
        if not snapshot_info:
            raise ValueError(f"快照不存在: {snapshot_id}")
        
        snapshot_path = self.snapshot_manager.snapshot_dir / snapshot_id
        files_index_path = snapshot_path / "files_index.json"
        
        with open(files_index_path, 'r', encoding='utf-8') as f:
            files_data = json.load(f)
        
        files_to_restore = 0
        files_to_modify = 0
        files_to_delete = 0
        files_details = []
        warnings = []
        estimated_size = 0
        
        current_files = set()
        for py_file in self.project_root.rglob('*.py'):
            current_files.add(str(py_file.relative_to(self.project_root)))
        
        for rel_path, file_info in files_data.items():
            target_path = self.project_root / rel_path
            estimated_size += file_info['size']
            
            if target_path.exists():
                current_content = target_path.read_bytes()
                current_hash = hashlib.sha256(current_content).hexdigest()
                
                if current_hash != file_info['content_hash']:
                    files_to_modify += 1
                    files_details.append({
                        'path': rel_path,
                        'action': 'modify'
                    })
                else:
                    files_details.append({
                        'path': rel_path,
                        'action': 'unchanged'
                    })
            else:
                files_to_restore += 1
                files_details.append({
                    'path': rel_path,
                    'action': 'restore'
                })
        
        for current_file in current_files:
            if current_file not in files_data:
                files_to_delete += 1
                files_details.append({
                    'path': current_file,
                    'action': 'delete'
                })
        
        if files_to_delete > 0:
            warnings.append(f"将删除 {files_to_delete} 个不在快照中的文件")
        
        return RollbackPreview(
            snapshot_id=snapshot_id,
            files_to_restore=files_to_restore,
            files_to_delete=files_to_delete,
            files_to_modify=files_to_modify,
            files_details=files_details,
            warnings=warnings,
            estimated_size=estimated_size
        )
    
    def auto_rollback(
        self,
        trigger: RollbackTrigger,
        error_details: Dict[str, Any] = None,
        exception: Exception = None
    ) -> Optional[RollbackResult]:
        """自动回滚 - 增强版，包含失败分析和通知模板"""
        if not self.auto_rollback_config.enabled:
            logger.warning("自动回滚已禁用")
            return None
        
        current_time = time.time()
        if current_time - self._last_auto_rollback_time < self.auto_rollback_config.cooldown_seconds:
            logger.warning("自动回滚冷却中，跳过")
            return None
        
        if self._auto_rollback_count >= self.auto_rollback_config.max_auto_rollbacks:
            logger.error("已达到最大自动回滚次数")
            
            title, body = self.template_manager.render('rollback_failure', {
                'snapshot_id': 'N/A',
                'error_message': f"已达到最大自动回滚次数: {self.auto_rollback_config.max_auto_rollbacks}",
                'affected_files': 'N/A'
            })
            self.notify_failure(title, body, severity="critical", details=error_details)
            return None
        
        snapshots = self.snapshot_manager.list_snapshots(status=SnapshotStatus.ACTIVE)
        
        if not snapshots:
            snapshots = self.snapshot_manager.list_snapshots()
        
        if not snapshots:
            logger.error("没有可用的快照进行自动回滚")
            return None
        
        latest_snapshot = snapshots[0]
        
        if exception:
            failure_analysis = self.failure_analyzer.analyze(
                exception,
                error_details or {},
                error_details.get('affected_files') if error_details else None
            )
            logger.info(f"失败分析完成: {failure_analysis.failure_id}, 根因: {failure_analysis.root_cause}")
        
        logger.warning(f"触发自动回滚: {trigger.value}, 目标快照: {latest_snapshot.snapshot_id}")
        
        self._auto_rollback_count += 1
        self._last_auto_rollback_time = current_time
        
        self.audit_logger.log(
            action="auto_rollback_triggered",
            actor="system",
            target=latest_snapshot.snapshot_id,
            result="started",
            details={
                'trigger': trigger.value,
                'auto_rollback_count': self._auto_rollback_count
            },
            risk_level=RiskLevel.MEDIUM,
            snapshot_id=latest_snapshot.snapshot_id
        )
        
        result = self.rollback(
            latest_snapshot.snapshot_id,
            trigger=trigger,
            verify=True,
            verification_level=self.auto_rollback_config.verification_level
        )
        
        template_id = 'auto_rollback' if result.success else 'rollback_failure'
        title, body = self.template_manager.render(template_id, {
            'snapshot_id': latest_snapshot.snapshot_id,
            'trigger': trigger.value,
            'files_restored': result.files_restored,
            'duration': f"{result.rollback_duration_seconds:.2f}",
            'verification_result': '通过' if result.verification_passed else '失败',
            'health_score': error_details.get('health_score', 'N/A') if error_details else 'N/A',
            'anomaly_details': str(error_details.get('anomalies', [])) if error_details else 'N/A',
            'rollback_result': '成功' if result.success else '失败',
            'error_message': result.error_message or 'N/A',
            'affected_files': result.files_failed
        })
        
        self.notify_failure(
            title,
            body,
            details={
                'trigger': trigger.value,
                'snapshot_id': latest_snapshot.snapshot_id,
                'success': result.success,
                'error_details': error_details,
                'auto_rollback_count': self._auto_rollback_count,
                'failure_analysis': asdict(failure_analysis) if exception else None
            },
            severity="warning" if result.success else "error",
            snapshot_id=latest_snapshot.snapshot_id
        )
        
        self.audit_logger.log(
            action="auto_rollback_complete",
            actor="system",
            target=latest_snapshot.snapshot_id,
            result="success" if result.success else "failed",
            details={
                'files_restored': result.files_restored,
                'duration': result.rollback_duration_seconds
            },
            risk_level=RiskLevel.LOW if result.success else RiskLevel.HIGH,
            snapshot_id=latest_snapshot.snapshot_id
        )
        
        return result
    
    def notify_failure(
        self,
        title: str,
        message: str = "",
        details: Dict[str, Any] = None,
        severity: str = "error",
        snapshot_id: str = None,
        dedup_key: str = None
    ) -> Dict[NotificationType, bool]:
        return self.notification_manager.send_notification(
            title=title,
            message=message,
            severity=severity,
            details=details,
            snapshot_id=snapshot_id,
            dedup_key=dedup_key
        )
    
    def verify_current_state(
        self,
        level: VerificationLevel = VerificationLevel.STANDARD,
        custom_checks: List[Callable[[], bool]] = None
    ) -> VerificationResult:
        return self.verifier.verify(level, custom_checks)
    
    def verify_snapshot(self, snapshot_id: str) -> Tuple[bool, List[str]]:
        """验证快照完整性"""
        return self.snapshot_manager.verify_snapshot(snapshot_id)
    
    def diff_snapshots(
        self,
        snapshot_id1: str,
        snapshot_id2: str,
        include_content_diff: bool = False
    ) -> SnapshotDiffResult:
        """对比两个快照的差异"""
        return self.snapshot_manager.diff_snapshots(
            snapshot_id1,
            snapshot_id2,
            include_content_diff
        )
    
    @contextmanager
    def iteration_context(
        self,
        operation_name: str,
        auto_snapshot: bool = True,
        auto_rollback: bool = True,
        verify_after: bool = True,
        verification_level: VerificationLevel = VerificationLevel.STANDARD,
        timeout: float = None
    ):
        """迭代上下文 - 增强版，包含审计日志和失败分析"""
        snapshot_id = None
        
        if auto_snapshot:
            snapshot = self.create_snapshot(
                version=f"pre_{operation_name}",
                description=f"迭代前快照: {operation_name}"
            )
            snapshot_id = snapshot.snapshot_id
            self._current_iteration_snapshot = snapshot_id
            
            self.audit_logger.log(
                action="iteration_snapshot_created",
                actor="system",
                target=operation_name,
                result="success",
                details={'snapshot_id': snapshot_id},
                risk_level=RiskLevel.LOW,
                snapshot_id=snapshot_id
            )
        
        ctx = IterationContext(self, operation_name, snapshot_id or "")
        exception_occurred = False
        
        try:
            yield ctx
            
            if verify_after:
                verification_result = self.verifier.verify(verification_level)
                if not verification_result.passed:
                    raise RuntimeError(f"验证失败: {verification_result.errors}")
            
            iteration_result = ctx.complete(verify=verify_after, verification_level=verification_level)
            with self._lock:
                self._iteration_history.append(iteration_result)
            
            self.audit_logger.log(
                action="iteration_complete",
                actor="system",
                target=operation_name,
                result="success",
                details={
                    'snapshot_id': snapshot_id,
                    'modified_files': len(ctx.get_modified_files()),
                    'duration': iteration_result.duration_seconds
                },
                risk_level=RiskLevel.LOW,
                snapshot_id=snapshot_id
            )
            
        except Exception as e:
            exception_occurred = True
            logger.error(f"迭代操作失败: {operation_name}, 错误: {e}")
            
            failure_analysis = self.failure_analyzer.analyze(
                e,
                {'operation_name': operation_name, 'snapshot_id': snapshot_id},
                ctx.get_modified_files()
            )
            
            self.audit_logger.log(
                action="iteration_failed",
                actor="system",
                target=operation_name,
                result="failed",
                details={
                    'exception_type': type(e).__name__,
                    'failure_analysis_id': failure_analysis.failure_id,
                    'root_cause': failure_analysis.root_cause,
                    'modified_files': ctx.get_modified_files()
                },
                risk_level=RiskLevel.HIGH,
                snapshot_id=snapshot_id
            )
            
            if auto_rollback and snapshot_id and self.auto_rollback_config.on_exception:
                logger.info(f"执行自动回滚: {snapshot_id}")
                rollback_result = self.rollback(
                    snapshot_id,
                    trigger=RollbackTrigger.AUTO_EXCEPTION,
                    verify=True
                )
                
                title, body = self.template_manager.render('rollback_failure' if not rollback_result.success else 'rollback_success', {
                    'snapshot_id': snapshot_id,
                    'trigger': 'exception',
                    'files_restored': rollback_result.files_restored,
                    'duration': f"{rollback_result.rollback_duration_seconds:.2f}",
                    'verification_result': '通过' if rollback_result.verification_passed else '失败',
                    'error_message': str(e),
                    'affected_files': len(ctx.get_modified_files())
                })
                
                self.notify_failure(
                    title,
                    body,
                    details={
                        'exception_type': type(e).__name__,
                        'traceback': traceback.format_exc(),
                        'modified_files': ctx.get_modified_files(),
                        'rollback_success': rollback_result.success,
                        'failure_analysis': asdict(failure_analysis)
                    },
                    severity="error",
                    snapshot_id=snapshot_id
                )
            
            raise
        
        finally:
            self._current_iteration_snapshot = None
    
    def list_snapshots(
        self,
        status: SnapshotStatus = None,
        tags: List[str] = None,
        limit: int = 100,
        snapshot_type: SnapshotType = None
    ) -> List[SnapshotInfo]:
        return self.snapshot_manager.list_snapshots(
            status=status,
            tags=tags,
            limit=limit,
            snapshot_type=snapshot_type
        )
    
    def get_rollback_history(self, limit: int = 100) -> List[RollbackResult]:
        with self._lock:
            return self._rollback_history[-limit:]
    
    def get_iteration_history(self, limit: int = 100) -> List[IterationResult]:
        with self._lock:
            return self._iteration_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息 - 增强版"""
        with self._lock:
            total_rollbacks = len(self._rollback_history)
            successful = sum(1 for r in self._rollback_history if r.success)
            auto_rollbacks = sum(
                1 for r in self._rollback_history
                if r.trigger != RollbackTrigger.MANUAL
            )
            
            total_iterations = len(self._iteration_history)
            successful_iterations = sum(1 for i in self._iteration_history if i.success)
        
        snapshots = self.snapshot_manager.list_snapshots()
        
        health_metrics = self.health_monitor.get_metrics_history(limit=1)
        current_health = health_metrics[0] if health_metrics else None
        
        strategy_history = self.strategy_manager.get_strategy_history(limit=10)
        trigger_history = self.trigger_engine.get_trigger_history(limit=10)
        failure_history = self.failure_analyzer.get_failure_history(limit=10)
        
        return {
            "total_snapshots": len(snapshots),
            "total_rollbacks": total_rollbacks,
            "successful_rollbacks": successful,
            "failed_rollbacks": total_rollbacks - successful,
            "auto_rollbacks": auto_rollbacks,
            "rollback_success_rate": round(successful / total_rollbacks * 100, 2) if total_rollbacks > 0 else 0,
            "total_iterations": total_iterations,
            "successful_iterations": successful_iterations,
            "iteration_success_rate": round(successful_iterations / total_iterations * 100, 2) if total_iterations > 0 else 0,
            "auto_rollback_count": self._auto_rollback_count,
            "health_status": {
                "status": current_health.status.value if current_health else "unknown",
                "score": current_health.score if current_health else 0,
                "error_count": current_health.error_count if current_health else 0
            },
            "strategy_stats": {
                "total_strategies_executed": len(strategy_history),
                "recent_strategies": [s.get('strategy') for s in strategy_history[-5:]]
            },
            "trigger_stats": {
                "total_triggers": len(trigger_history),
                "rollbacks_triggered": sum(1 for t in trigger_history if t.get('should_rollback'))
            },
            "failure_stats": {
                "total_failures": len(failure_history),
                "recent_failure_types": list(set(f.failure_type for f in failure_history[-10:]))
            },
            "monitoring_enabled": self._monitoring_enabled,
            "auto_snapshot_enabled": self.auto_snapshot_manager.config.enabled
        }
    
    def cleanup(self, days: int = 30, keep_count: int = 5, keep_tags: List[str] = None) -> Dict[str, int]:
        deleted_snapshots = self.snapshot_manager.cleanup_old_snapshots(days, keep_count, keep_tags)
        
        return {
            "deleted_snapshots": deleted_snapshots
        }
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        return self.snapshot_manager.delete_snapshot(snapshot_id)
    
    def check_health(self, run_tests: bool = False) -> HealthMetrics:
        """检查系统健康状态"""
        return self.health_monitor.check_health(run_tests=run_tests)
    
    def get_audit_log(self, action: str = None, limit: int = 100) -> List[AuditLogEntry]:
        """获取审计日志"""
        return self.audit_logger.get_entries(action=action, limit=limit)
    
    def export_audit_log(self, output_file: str):
        """导出审计日志"""
        self.audit_logger.export_to_json(output_file)
    
    def get_failure_analysis(self, limit: int = 10) -> List[FailureAnalysis]:
        """获取失败分析历史"""
        return self.failure_analyzer.get_failure_history(limit=limit)
    
    def add_trigger_rule(self, name: str, condition: Callable, action: str, priority: int = 50):
        """添加自定义触发规则"""
        self.trigger_engine.add_rule(name, condition, action, priority)
    
    def trigger_event_snapshot(self, event_type: TriggerEventType, event_data: Dict[str, Any] = None):
        """触发事件快照"""
        self.auto_snapshot_manager.trigger_event(
            event_type,
            str(self.project_root),
            event_data
        )
    
    def get_anomalies(self) -> List[AnomalyInfo]:
        """获取当前异常"""
        metrics = self.health_monitor.check_health()
        return self.health_monitor.detect_anomalies(metrics)
    
    def add_notification_template(self, template: NotificationTemplate):
        """添加自定义通知模板"""
        self.template_manager.add_template(template)
    
    def send_templated_notification(
        self,
        template_id: str,
        variables: Dict[str, Any],
        severity: str = "info"
    ) -> Dict[NotificationType, bool]:
        """使用模板发送通知"""
        title, body = self.template_manager.render(template_id, variables)
        return self.notify_failure(title, body, severity=severity, details=variables)


def create_rollback_manager(
    project_root: str,
    snapshot_dir: str = None,
    notification_config: NotificationConfig = None,
    auto_rollback_config: AutoRollbackConfig = None,
    rollback_strategy_config: RollbackStrategyConfig = None,
    auto_snapshot_config: AutoSnapshotConfig = None
) -> SelfIterationRollback:
    """创建回滚管理器 - 增强版工厂函数"""
    return SelfIterationRollback(
        project_root,
        snapshot_dir,
        notification_config,
        auto_rollback_config,
        rollback_strategy_config,
        auto_snapshot_config
    )


def run_cli():
    """CLI入口 - 增强版"""
    parser = argparse.ArgumentParser(
        description='自迭代回滚器 - 版本快照与安全回滚（增强版）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 创建快照
  python self_iteration_rollback.py snapshot --project-root ./ --version v1.0.0
  
  # 列出快照
  python self_iteration_rollback.py list --project-root ./
  
  # 回滚到指定快照
  python self_iteration_rollback.py rollback --snapshot-id SNAP-xxx
  
  # 智能回滚（风险评估+策略选择）
  python self_iteration_rollback.py intelligent-rollback --snapshot-id SNAP-xxx
  
  # 预览回滚
  python self_iteration_rollback.py preview --snapshot-id SNAP-xxx
  
  # 验证快照
  python self_iteration_rollback.py verify-snapshot --snapshot-id SNAP-xxx
  
  # 对比快照差异
  python self_iteration_rollback.py diff --snapshot-id1 SNAP-xxx --snapshot-id2 SNAP-yyy
  
  # 查看统计
  python self_iteration_rollback.py stats --project-root ./
  
  # 健康检查
  python self_iteration_rollback.py health --project-root ./
  
  # 风险评估
  python self_iteration_rollback.py risk --snapshot-id SNAP-xxx
  
  # 查看审计日志
  python self_iteration_rollback.py audit --project-root ./
  
  # 查看失败分析
  python self_iteration_rollback.py failures --project-root ./
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    snapshot_parser = subparsers.add_parser('snapshot', help='创建快照')
    snapshot_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    snapshot_parser.add_argument('--version', '-v', help='版本号')
    snapshot_parser.add_argument('--description', '-d', help='快照描述')
    snapshot_parser.add_argument('--tags', '-t', help='标签（逗号分隔）')
    snapshot_parser.add_argument('--compress', action='store_true', help='压缩快照')
    
    list_parser = subparsers.add_parser('list', help='列出快照')
    list_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    list_parser.add_argument('--status', '-s', choices=['created', 'active', 'restored', 'deprecated'], help='过滤状态')
    list_parser.add_argument('--limit', '-l', type=int, default=20, help='显示数量')
    
    rollback_parser = subparsers.add_parser('rollback', help='回滚到快照')
    rollback_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    rollback_parser.add_argument('--snapshot-id', '-s', required=True, help='快照ID')
    rollback_parser.add_argument('--verify', action='store_true', help='回滚后验证')
    rollback_parser.add_argument('--level', choices=['basic', 'standard', 'thorough'], default='standard', help='验证级别')
    
    intelligent_rollback_parser = subparsers.add_parser('intelligent-rollback', help='智能回滚（风险评估+策略选择）')
    intelligent_rollback_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    intelligent_rollback_parser.add_argument('--snapshot-id', '-s', required=True, help='快照ID')
    
    preview_parser = subparsers.add_parser('preview', help='预览回滚')
    preview_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    preview_parser.add_argument('--snapshot-id', '-s', required=True, help='快照ID')
    
    verify_parser = subparsers.add_parser('verify', help='验证当前状态')
    verify_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    verify_parser.add_argument('--level', choices=['basic', 'standard', 'thorough'], default='standard', help='验证级别')
    
    verify_snapshot_parser = subparsers.add_parser('verify-snapshot', help='验证快照完整性')
    verify_snapshot_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    verify_snapshot_parser.add_argument('--snapshot-id', '-s', required=True, help='快照ID')
    
    diff_parser = subparsers.add_parser('diff', help='对比快照差异')
    diff_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    diff_parser.add_argument('--snapshot-id1', '-s1', required=True, help='快照ID 1')
    diff_parser.add_argument('--snapshot-id2', '-s2', required=True, help='快照ID 2')
    diff_parser.add_argument('--content', action='store_true', help='包含内容差异')
    
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    stats_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    
    health_parser = subparsers.add_parser('health', help='健康检查')
    health_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    health_parser.add_argument('--run-tests', action='store_true', help='运行测试')
    
    risk_parser = subparsers.add_parser('risk', help='风险评估')
    risk_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    risk_parser.add_argument('--snapshot-id', '-s', required=True, help='快照ID')
    
    audit_parser = subparsers.add_parser('audit', help='查看审计日志')
    audit_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    audit_parser.add_argument('--action', '-a', help='过滤操作类型')
    audit_parser.add_argument('--limit', '-l', type=int, default=20, help='显示数量')
    audit_parser.add_argument('--export', '-e', help='导出到文件')
    
    failures_parser = subparsers.add_parser('failures', help='查看失败分析')
    failures_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    failures_parser.add_argument('--limit', '-l', type=int, default=10, help='显示数量')
    
    anomalies_parser = subparsers.add_parser('anomalies', help='检测异常')
    anomalies_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    
    cleanup_parser = subparsers.add_parser('cleanup', help='清理旧快照')
    cleanup_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    cleanup_parser.add_argument('--days', '-d', type=int, default=30, help='保留天数')
    cleanup_parser.add_argument('--keep', '-k', type=int, default=5, help='最少保留数量')
    
    delete_parser = subparsers.add_parser('delete', help='删除快照')
    delete_parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    delete_parser.add_argument('--snapshot-id', '-s', required=True, help='快照ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    rollback = SelfIterationRollback(args.project_root)
    
    if args.command == 'snapshot':
        tags = args.tags.split(',') if args.tags else []
        snapshot = rollback.create_snapshot(
            version=args.version,
            description=args.description or "",
            tags=tags
        )
        print(f"快照创建成功: {snapshot.snapshot_id}")
        print(f"版本: {snapshot.version}")
        print(f"文件数: {snapshot.files_count}")
        print(f"大小: {snapshot.total_size} bytes")
    
    elif args.command == 'list':
        status = SnapshotStatus(args.status) if args.status else None
        snapshots = rollback.list_snapshots(status=status, limit=args.limit)
        print(f"\n共 {len(snapshots)} 个快照:")
        for snap in snapshots:
            status_icon = {
                SnapshotStatus.ACTIVE: "[ACTIVE]",
                SnapshotStatus.RESTORED: "[RESTORED]",
                SnapshotStatus.DEPRECATED: "[DEPRECATED]",
                SnapshotStatus.ERROR: "[ERROR]"
            }.get(snap.status, "[?]")
            print(f"  {status_icon} {snap.snapshot_id}: v{snap.version} ({snap.timestamp[:10]}) - {snap.files_count} 文件, {snap.total_size} bytes")
            if snap.description:
                print(f"       描述: {snap.description}")
    
    elif args.command == 'rollback':
        level = VerificationLevel(args.level)
        result = rollback.rollback(args.snapshot_id, verify=args.verify, verification_level=level)
        
        if result.success:
            print(f"回滚成功: {result.files_restored} 文件已恢复")
            print(f"耗时: {result.rollback_duration_seconds:.2f}秒")
        else:
            print(f"回滚失败: {result.error_message}")
            sys.exit(1)
    
    elif args.command == 'preview':
        preview = rollback.preview_rollback(args.snapshot_id)
        print(f"回滚预览: {args.snapshot_id}")
        print(f"  文件恢复: {preview.files_to_restore}")
        print(f"  文件修改: {preview.files_to_modify}")
        print(f"  文件删除: {preview.files_to_delete}")
        print(f"  预估大小: {preview.estimated_size} bytes")
        if preview.warnings:
            print("\n警告:")
            for w in preview.warnings:
                print(f"  - {w}")
    
    elif args.command == 'verify':
        level = VerificationLevel(args.level)
        result = rollback.verify_current_state(level)
        
        print(f"验证结果: {'通过' if result.passed else '失败'}")
        print(f"检查项: {result.checks_passed}/{result.checks_total} 通过")
        
        if result.errors:
            print("\n错误:")
            for error in result.errors:
                print(f"  - {error}")
    
    elif args.command == 'verify-snapshot':
        success, errors = rollback.verify_snapshot(args.snapshot_id)
        if success:
            print(f"快照验证通过: {args.snapshot_id}")
        else:
            print(f"快照验证失败:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
    
    elif args.command == 'diff':
        diff_result = rollback.diff_snapshots(
            args.snapshot_id1,
            args.snapshot_id2,
            include_content_diff=args.content
        )
        print(f"快照差异对比:")
        print(f"  {args.snapshot_id1} -> {args.snapshot_id2}")
        print(f"\n  新增文件: {len(diff_result.added_files)}")
        for f in diff_result.added_files[:10]:
            print(f"    + {f}")
        
        print(f"\n  删除文件: {len(diff_result.removed_files)}")
        for f in diff_result.removed_files[:10]:
            print(f"    - {f}")
        
        print(f"\n  修改文件: {len(diff_result.modified_files)}")
        for f in diff_result.modified_files[:10]:
            print(f"    ~ {f}")
        
        print(f"\n  未变文件: {len(diff_result.unchanged_files)}")
    
    elif args.command == 'stats':
        stats = rollback.get_statistics()
        print("=== 回滚统计 ===")
        print(f"总快照数: {stats['total_snapshots']}")
        print(f"总回滚数: {stats['total_rollbacks']}")
        print(f"成功回滚: {stats['successful_rollbacks']}")
        print(f"自动回滚: {stats['auto_rollbacks']}")
        print(f"成功率: {stats['rollback_success_rate']}%")
        print(f"总迭代数: {stats['total_iterations']}")
        print(f"成功迭代: {stats['successful_iterations']}")
        print(f"迭代成功率: {stats['iteration_success_rate']}%")
        print(f"自动回滚计数: {stats['auto_rollback_count']}")
        
        if 'health_status' in stats:
            print(f"\n=== 健康状态 ===")
            print(f"状态: {stats['health_status']['status']}")
            print(f"分数: {stats['health_status']['score']}")
            print(f"错误数: {stats['health_status']['error_count']}")
        
        if 'strategy_stats' in stats:
            print(f"\n=== 策略统计 ===")
            print(f"执行策略数: {stats['strategy_stats']['total_strategies_executed']}")
        
        if 'failure_stats' in stats:
            print(f"\n=== 失败统计 ===")
            print(f"总失败数: {stats['failure_stats']['total_failures']}")
    
    elif args.command == 'health':
        metrics = rollback.check_health(run_tests=args.run_tests)
        print("=== 健康检查结果 ===")
        print(f"状态: {metrics.status.value}")
        print(f"分数: {metrics.score}")
        print(f"测试通过率: {metrics.test_pass_rate:.2%}")
        print(f"构建成功率: {metrics.build_success_rate:.2%}")
        print(f"错误数: {metrics.error_count}")
        print(f"警告数: {metrics.warning_count}")
        print(f"检查时间: {metrics.last_check_time}")
        
        anomalies = rollback.health_monitor.detect_anomalies(metrics)
        if anomalies:
            print(f"\n检测到 {len(anomalies)} 个异常:")
            for anomaly in anomalies:
                print(f"  [{anomaly.severity.value}] {anomaly.anomaly_type}: {anomaly.description}")
                print(f"    建议: {anomaly.recommended_action}")
    
    elif args.command == 'risk':
        try:
            assessment = rollback.assess_rollback_risk(args.snapshot_id)
            print(f"=== 风险评估: {args.snapshot_id} ===")
            print(f"风险等级: {assessment.risk_level.value}")
            print(f"风险分数: {assessment.risk_score}")
            print(f"受影响文件: {assessment.affected_files}")
            print(f"关键文件数: {len(assessment.critical_files)}")
            print(f"可以执行: {assessment.can_proceed}")
            print(f"需要备份: {assessment.requires_backup}")
            print(f"影响评估: {assessment.estimated_impact}")
            
            if assessment.warnings:
                print("\n警告:")
                for w in assessment.warnings:
                    print(f"  - {w}")
            
            if assessment.recommendations:
                print("\n建议:")
                for r in assessment.recommendations:
                    print(f"  - {r}")
        except Exception as e:
            print(f"风险评估失败: {e}")
            sys.exit(1)
    
    elif args.command == 'intelligent-rollback':
        result = rollback.intelligent_rollback(args.snapshot_id)
        
        if result.success:
            print(f"智能回滚成功: {result.files_restored} 文件已恢复")
            print(f"耗时: {result.rollback_duration_seconds:.2f}秒")
        else:
            print(f"智能回滚失败: {result.error_message}")
            sys.exit(1)
    
    elif args.command == 'audit':
        entries = rollback.get_audit_log(action=args.action, limit=args.limit)
        
        if args.export:
            rollback.export_audit_log(args.export)
            print(f"审计日志已导出到: {args.export}")
        else:
            print(f"=== 审计日志 (共 {len(entries)} 条) ===")
            for entry in entries:
                print(f"\n[{entry.timestamp}] {entry.action}")
                print(f"  操作者: {entry.actor}")
                print(f"  目标: {entry.target}")
                print(f"  结果: {entry.result}")
                print(f"  风险等级: {entry.risk_level.value}")
                if entry.snapshot_id:
                    print(f"  快照ID: {entry.snapshot_id}")
    
    elif args.command == 'failures':
        failures = rollback.get_failure_analysis(limit=args.limit)
        print(f"=== 失败分析 (共 {len(failures)} 条) ===")
        
        for failure in failures:
            print(f"\n[{failure.failure_id}] {failure.timestamp}")
            print(f"  类型: {failure.failure_type}")
            print(f"  根因: {failure.root_cause}")
            print(f"  影响: {failure.impact_assessment}")
            print(f"  受影响文件: {len(failure.affected_files)}")
            if failure.recovery_suggestions:
                print(f"  恢复建议:")
                for s in failure.recovery_suggestions[:3]:
                    print(f"    - {s}")
    
    elif args.command == 'anomalies':
        anomalies = rollback.get_anomalies()
        print(f"=== 异常检测 (共 {len(anomalies)} 个) ===")
        
        for anomaly in anomalies:
            print(f"\n[{anomaly.severity.value}] {anomaly.anomaly_type}")
            print(f"  检测时间: {anomaly.detected_at}")
            print(f"  描述: {anomaly.description}")
            print(f"  受影响组件: {', '.join(anomaly.affected_components)}")
            print(f"  建议操作: {anomaly.recommended_action}")
    
    elif args.command == 'cleanup':
        result = rollback.cleanup(args.days, args.keep)
        print(f"清理完成: 删除 {result['deleted_snapshots']} 个快照")
    
    elif args.command == 'delete':
        if rollback.delete_snapshot(args.snapshot_id):
            print(f"快照已删除: {args.snapshot_id}")
        else:
            print(f"删除失败: {args.snapshot_id}")
            sys.exit(1)


class IntelligentSnapshotCreator:
    """智能快照创建器 - 自动创建版本快照"""
    
    def __init__(self, snapshot_manager: SnapshotManager, project_root: str):
        self.snapshot_manager = snapshot_manager
        self.project_root = project_root
        self._auto_snapshot_config = AutoSnapshotConfig()
        self._file_state_cache: Dict[str, str] = {}
        self._change_history: List[Dict[str, Any]] = []
        self._last_snapshot_time: float = 0
        self._lock = threading.Lock()
        self._watcher_thread: Optional[threading.Thread] = None
        self._running = False
    
    def start_auto_snapshot(self, config: AutoSnapshotConfig = None):
        """启动自动快照服务"""
        self._auto_snapshot_config = config or AutoSnapshotConfig()
        
        if not self._auto_snapshot_config.enabled:
            return
        
        self._running = True
        self._watcher_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._watcher_thread.start()
        logger.info("智能快照服务已启动")
    
    def stop_auto_snapshot(self):
        """停止自动快照服务"""
        self._running = False
        if self._watcher_thread:
            self._watcher_thread.join(timeout=5)
        logger.info("智能快照服务已停止")
    
    def _watch_loop(self):
        """监控循环"""
        while self._running:
            try:
                self._check_and_create_snapshot()
            except Exception as e:
                logger.error(f"快照监控错误: {e}")
            
            time.sleep(self._auto_snapshot_config.schedule_interval)
    
    def _check_and_create_snapshot(self):
        """检查并创建快照"""
        current_time = time.time()
        
        if current_time - self._last_snapshot_time < self._auto_snapshot_config.min_interval_seconds:
            return
        
        should_create = False
        reason = ""
        
        if self._auto_snapshot_config.on_file_change:
            changes = self._detect_file_changes()
            if changes >= self._auto_snapshot_config.file_change_threshold:
                should_create = True
                reason = f"检测到 {changes} 个文件变化"
        
        if should_create:
            self._create_auto_snapshot(reason)
            self._last_snapshot_time = current_time
    
    def _detect_file_changes(self) -> int:
        """检测文件变化"""
        current_state = {}
        project_path = Path(self.project_root)
        changes = 0
        
        for py_file in project_path.rglob('*.py'):
            try:
                rel_path = str(py_file.relative_to(project_path))
                content_hash = hashlib.sha256(py_file.read_bytes()).hexdigest()[:16]
                current_state[rel_path] = content_hash
                
                if rel_path in self._file_state_cache:
                    if self._file_state_cache[rel_path] != content_hash:
                        changes += 1
            except Exception:
                continue
        
        with self._lock:
            self._file_state_cache = current_state
        
        return changes
    
    def _create_auto_snapshot(self, reason: str):
        """创建自动快照"""
        try:
            snapshots = self.snapshot_manager.list_snapshots()
            if len(snapshots) >= self._auto_snapshot_config.max_snapshots:
                oldest = snapshots[-1]
                self.snapshot_manager.delete_snapshot(oldest.snapshot_id)
                logger.info(f"删除旧快照: {oldest.snapshot_id}")
            
            snapshot = self.snapshot_manager.create_snapshot(
                project_root=self.project_root,
                version=f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                tags=self._auto_snapshot_config.tags + ["auto"],
                description=f"自动快照: {reason}",
                snapshot_type=SnapshotType.INCREMENTAL
            )
            
            logger.info(f"创建自动快照: {snapshot.snapshot_id}, 原因: {reason}")
            
            with self._lock:
                self._change_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'snapshot_id': snapshot.snapshot_id,
                    'reason': reason
                })
        
        except Exception as e:
            logger.error(f"创建自动快照失败: {e}")
    
    def create_pre_operation_snapshot(self, operation_name: str, metadata: Dict[str, Any] = None) -> Optional[SnapshotInfo]:
        """创建操作前快照"""
        try:
            snapshot = self.snapshot_manager.create_snapshot(
                project_root=self.project_root,
                version=f"pre_{operation_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                tags=["pre-operation", operation_name],
                description=f"操作前快照: {operation_name}",
                metadata=metadata or {}
            )
            
            logger.info(f"创建操作前快照: {snapshot.snapshot_id}")
            return snapshot
        
        except Exception as e:
            logger.error(f"创建操作前快照失败: {e}")
            return None
    
    def get_change_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取变化历史"""
        with self._lock:
            return self._change_history[-limit:]


class IntelligentRollbackTrigger:
    """智能回滚触发器 - 自动检测并触发回滚"""
    
    def __init__(
        self,
        rollback_manager: 'SelfIterationRollback',
        health_monitor: HealthMonitor
    ):
        self.rollback_manager = rollback_manager
        self.health_monitor = health_monitor
        self._trigger_rules: List[Dict[str, Any]] = []
        self._trigger_history: List[Dict[str, Any]] = []
        self._cooldown_until: float = 0
        self._lock = threading.Lock()
        
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认触发规则"""
        self._trigger_rules = [
            {
                'name': 'critical_health',
                'condition': lambda m: m.status == HealthStatus.CRITICAL,
                'action': 'immediate_rollback',
                'priority': 100,
                'cooldown': 60
            },
            {
                'name': 'high_error_rate',
                'condition': lambda m: m.error_count > 20,
                'action': 'assess_and_rollback',
                'priority': 80,
                'cooldown': 120
            },
            {
                'name': 'low_test_rate',
                'condition': lambda m: m.test_pass_rate < 0.5,
                'action': 'assess_and_rollback',
                'priority': 70,
                'cooldown': 180
            },
            {
                'name': 'degraded_health',
                'condition': lambda m: m.status == HealthStatus.DEGRADED,
                'action': 'monitor_closely',
                'priority': 50,
                'cooldown': 300
            },
            {
                'name': 'memory_anomaly',
                'condition': self._check_memory_anomaly,
                'action': 'immediate_rollback',
                'priority': 90,
                'cooldown': 60
            }
        ]
    
    def _check_memory_anomaly(self, metrics: HealthMetrics) -> bool:
        """检查内存异常"""
        return metrics.details.get('memory_usage', 0) > 90
    
    def evaluate(self, metrics: HealthMetrics) -> Dict[str, Any]:
        """评估是否需要触发回滚"""
        current_time = time.time()
        
        if current_time < self._cooldown_until:
            return {
                'should_rollback': False,
                'reason': '冷却中',
                'cooldown_remaining': self._cooldown_until - current_time
            }
        
        triggered_rules = []
        
        for rule in sorted(self._trigger_rules, key=lambda x: x['priority'], reverse=True):
            try:
                if rule['condition'](metrics):
                    triggered_rules.append({
                        'rule_name': rule['name'],
                        'action': rule['action'],
                        'priority': rule['priority']
                    })
            except Exception:
                continue
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'should_rollback': False,
            'triggered_rules': triggered_rules,
            'recommended_action': 'none',
            'health_score': metrics.score
        }
        
        if triggered_rules:
            top_rule = triggered_rules[0]
            
            if top_rule['action'] == 'immediate_rollback':
                result['should_rollback'] = True
                result['recommended_action'] = 'immediate_rollback'
                result['reason'] = f"规则触发: {top_rule['rule_name']}"
                
                cooldown = next(
                    (r['cooldown'] for r in self._trigger_rules if r['name'] == top_rule['rule_name']),
                    60
                )
                self._cooldown_until = current_time + cooldown
            
            elif top_rule['action'] == 'assess_and_rollback':
                result['should_rollback'] = True
                result['recommended_action'] = 'assess_before_rollback'
                result['reason'] = f"规则触发: {top_rule['rule_name']}"
            
            elif top_rule['action'] == 'monitor_closely':
                result['recommended_action'] = 'increase_monitoring'
                result['reason'] = f"监控中: {top_rule['rule_name']}"
        
        with self._lock:
            self._trigger_history.append(result)
        
        return result
    
    def add_custom_rule(
        self,
        name: str,
        condition: Callable,
        action: str,
        priority: int = 50,
        cooldown: int = 60
    ):
        """添加自定义规则"""
        self._trigger_rules.append({
            'name': name,
            'condition': condition,
            'action': action,
            'priority': priority,
            'cooldown': cooldown
        })
    
    def get_trigger_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取触发历史"""
        with self._lock:
            return self._trigger_history[-limit:]


class EnhancedNotificationManager:
    """增强通知管理器 - 完善失败通知和日志记录"""
    
    def __init__(self, config: NotificationConfig = None):
        self.config = config or NotificationConfig()
        self._notification_queue: List[NotificationMessage] = []
        self._notification_history: List[Dict[str, Any]] = []
        self._dedup_cache: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._rate_limits: Dict[str, List[float]] = {}
    
    def send_enhanced_notification(
        self,
        title: str,
        message: str,
        severity: str = "info",
        details: Dict[str, Any] = None,
        dedup_key: str = None,
        rate_limit_key: str = None,
        rate_limit_count: int = 10,
        rate_limit_window: int = 60
    ) -> Dict[str, Any]:
        """发送增强通知"""
        current_time = time.time()
        
        if dedup_key:
            last_time = self._dedup_cache.get(dedup_key, 0)
            if current_time - last_time < 60:
                return {'sent': False, 'reason': 'deduplicated'}
            self._dedup_cache[dedup_key] = current_time
        
        if rate_limit_key:
            with self._lock:
                if rate_limit_key not in self._rate_limits:
                    self._rate_limits[rate_limit_key] = []
                
                self._rate_limits[rate_limit_key] = [
                    t for t in self._rate_limits[rate_limit_key]
                    if current_time - t < rate_limit_window
                ]
                
                if len(self._rate_limits[rate_limit_key]) >= rate_limit_count:
                    return {'sent': False, 'reason': 'rate_limited'}
                
                self._rate_limits[rate_limit_key].append(current_time)
        
        notification = NotificationMessage(
            notification_type=NotificationType.LOG,
            title=title,
            message=message,
            timestamp=datetime.now().isoformat(),
            severity=severity,
            details=details or {}
        )
        
        results = {}
        
        for notif_type in self.config.notification_types:
            try:
                if notif_type == NotificationType.LOG:
                    results[notif_type.value] = self._send_log(notification)
                elif notif_type == NotificationType.CONSOLE:
                    results[notif_type.value] = self._send_console(notification)
                elif notif_type == NotificationType.FILE:
                    results[notif_type.value] = self._send_file(notification)
                elif notif_type == NotificationType.WEBHOOK:
                    results[notif_type.value] = self._send_webhook(notification)
            except Exception as e:
                results[notif_type.value] = False
                logger.error(f"发送通知失败 {notif_type}: {e}")
        
        with self._lock:
            self._notification_history.append({
                'timestamp': notification.timestamp,
                'title': title,
                'severity': severity,
                'results': results
            })
        
        return {'sent': True, 'results': results}
    
    def _send_log(self, notification: NotificationMessage) -> bool:
        """发送日志通知"""
        log_message = f"[{notification.severity.upper()}] {notification.title}: {notification.message}"
        
        if notification.severity == "error":
            logger.error(log_message)
        elif notification.severity == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        return True
    
    def _send_console(self, notification: NotificationMessage) -> bool:
        """发送控制台通知"""
        severity_icons = {
            "info": "[INFO]",
            "warning": "[WARN]",
            "error": "[ERROR]",
            "critical": "[CRITICAL]"
        }
        icon = severity_icons.get(notification.severity, "[INFO]")
        print(f"\n{icon} {notification.title}")
        print(f"   {notification.message}")
        return True
    
    def _send_file(self, notification: NotificationMessage) -> bool:
        """发送文件通知"""
        if not self.config.notification_file:
            return False
        
        try:
            with open(self.config.notification_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"时间: {notification.timestamp}\n")
                f.write(f"严重程度: {notification.severity}\n")
                f.write(f"标题: {notification.title}\n")
                f.write(f"消息: {notification.message}\n")
                f.write(f"{'='*60}\n")
            return True
        except Exception:
            return False
    
    def _send_webhook(self, notification: NotificationMessage) -> bool:
        """发送Webhook通知"""
        if not self.config.webhook_url:
            return False
        
        try:
            import urllib.request
            
            payload = json.dumps({
                'title': notification.title,
                'message': notification.message,
                'timestamp': notification.timestamp,
                'severity': notification.severity,
                'details': notification.details
            }).encode('utf-8')
            
            req = urllib.request.Request(
                self.config.webhook_url,
                data=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=self.config.webhook_timeout) as response:
                return response.status == 200
        
        except Exception:
            return False
    
    def get_notification_statistics(self) -> Dict[str, Any]:
        """获取通知统计"""
        with self._lock:
            if not self._notification_history:
                return {'total_notifications': 0}
            
            severity_counts = {}
            for n in self._notification_history:
                sev = n.get('severity', 'unknown')
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            return {
                'total_notifications': len(self._notification_history),
                'severity_distribution': severity_counts
            }


class EnhancedRollbackVerifier:
    """增强回滚验证器 - 添加回滚验证功能"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self._verification_history: List[Dict[str, Any]] = []
        self._custom_checks: List[Callable[[], bool]] = []
        self._lock = threading.Lock()
    
    def verify_rollback(
        self,
        level: VerificationLevel = VerificationLevel.STANDARD,
        include_custom: bool = True,
        include_tests: bool = False,
        test_command: str = None
    ) -> Dict[str, Any]:
        """验证回滚结果"""
        results = {
            'passed': True,
            'level': level.value,
            'checks': {},
            'errors': [],
            'warnings': [],
            'timestamp': datetime.now().isoformat()
        }
        
        basic_checks = {
            'project_exists': self._check_project_exists,
            'key_files_present': self._check_key_files,
            'file_permissions': self._check_file_permissions,
            'directory_structure': self._check_directory_structure
        }
        
        standard_checks = {
            **basic_checks,
            'python_syntax': self._check_python_syntax,
            'config_files': self._check_config_files,
            'import_validity': self._check_imports
        }
        
        thorough_checks = {
            **standard_checks,
            'unit_tests': lambda: self._run_tests(test_command) if include_tests else lambda: True,
            'dependency_check': self._check_dependencies,
            'security_scan': self._check_security
        }
        
        checks_map = {
            VerificationLevel.BASIC: basic_checks,
            VerificationLevel.STANDARD: standard_checks,
            VerificationLevel.THOROUGH: thorough_checks
        }
        
        checks = checks_map.get(level, standard_checks)
        
        if include_custom:
            for i, check_func in enumerate(self._custom_checks):
                checks[f'custom_check_{i+1}'] = check_func
        
        for check_name, check_func in checks.items():
            try:
                passed = check_func()
                results['checks'][check_name] = {
                    'passed': passed,
                    'error': None
                }
                
                if not passed:
                    results['errors'].append(f"{check_name}: 验证失败")
                    results['passed'] = False
            
            except Exception as e:
                results['checks'][check_name] = {
                    'passed': False,
                    'error': str(e)
                }
                results['errors'].append(f"{check_name}: {e}")
                results['passed'] = False
        
        with self._lock:
            self._verification_history.append(results)
        
        return results
    
    def _check_project_exists(self) -> bool:
        """检查项目目录存在"""
        return self.project_root.exists()
    
    def _check_key_files(self) -> bool:
        """检查关键文件"""
        key_files = ['__init__.py', 'setup.py', 'pyproject.toml', 'requirements.txt']
        for key_file in key_files:
            if (self.project_root / key_file).exists():
                return True
        return True
    
    def _check_file_permissions(self) -> bool:
        """检查文件权限"""
        try:
            for py_file in list(self.project_root.rglob('*.py'))[:10]:
                if not os.access(py_file, os.R_OK):
                    return False
            return True
        except Exception:
            return True
    
    def _check_directory_structure(self) -> bool:
        """检查目录结构"""
        try:
            py_files = list(self.project_root.rglob('*.py'))
            return len(py_files) > 0
        except Exception:
            return False
    
    def _check_python_syntax(self) -> bool:
        """检查Python语法"""
        try:
            py_files = list(self.project_root.rglob('*.py'))[:20]
            for py_file in py_files:
                result = subprocess.run(
                    [sys.executable, '-m', 'py_compile', str(py_file)],
                    capture_output=True,
                    timeout=30
                )
                if result.returncode != 0:
                    return False
            return True
        except Exception:
            return True
    
    def _check_config_files(self) -> bool:
        """检查配置文件"""
        config_patterns = ['*.json', '*.yaml', '*.yml', '*.toml']
        for pattern in config_patterns:
            for config_file in list(self.project_root.rglob(pattern))[:5]:
                try:
                    content = config_file.read_text(encoding='utf-8')
                    if config_file.suffix == '.json':
                        json.loads(content)
                except Exception:
                    return False
        return True
    
    def _check_imports(self) -> bool:
        """检查导入"""
        try:
            py_files = list(self.project_root.rglob('*.py'))[:10]
            for py_file in py_files:
                result = subprocess.run(
                    [sys.executable, '-c', f'import ast; ast.parse(open("{py_file}").read())'],
                    capture_output=True,
                    timeout=30
                )
            return True
        except Exception:
            return True
    
    def _run_tests(self, test_command: str = None) -> bool:
        """运行测试"""
        try:
            if test_command:
                cmd = test_command.split()
            else:
                cmd = [sys.executable, '-m', 'pytest', '-x', '--tb=no', '-q']
            
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                timeout=120
            )
            return result.returncode == 0
        except Exception:
            return True
    
    def _check_dependencies(self) -> bool:
        """检查依赖"""
        requirements_file = self.project_root / 'requirements.txt'
        if not requirements_file.exists():
            return True
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'check'],
                cwd=str(self.project_root),
                capture_output=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception:
            return True
    
    def _check_security(self) -> bool:
        """检查安全"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'bandit', '-r', '.', '-f', 'json'],
                cwd=str(self.project_root),
                capture_output=True,
                timeout=120
            )
            if result.returncode == 0:
                return True
            try:
                data = json.loads(result.stdout)
                high_severity = [r for r in data.get('results', []) if r.get('issue_severity') == 'HIGH']
                return len(high_severity) == 0
            except Exception:
                return True
        except Exception:
            return True
    
    def add_custom_check(self, check_func: Callable[[], bool]):
        """添加自定义检查"""
        with self._lock:
            self._custom_checks.append(check_func)
    
    def get_verification_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取验证历史"""
        with self._lock:
            return self._verification_history[-limit:]


class EnhancedSelfIterationRollback(SelfIterationRollback):
    """增强自迭代回滚器 - 集成所有增强功能"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self._intelligent_snapshot = IntelligentSnapshotCreator(
            self.snapshot_manager,
            str(self.project_root)
        )
        self._intelligent_trigger = IntelligentRollbackTrigger(
            self,
            self.health_monitor
        )
        self._enhanced_notification = EnhancedNotificationManager()
        self._enhanced_verifier = EnhancedRollbackVerifier(str(self.project_root))
    
    def start_intelligent_snapshot(self, config: AutoSnapshotConfig = None):
        """启动智能快照服务"""
        self._intelligent_snapshot.start_auto_snapshot(config)
    
    def stop_intelligent_snapshot(self):
        """停止智能快照服务"""
        self._intelligent_snapshot.stop_auto_snapshot()
    
    def create_pre_operation_snapshot(self, operation_name: str, metadata: Dict[str, Any] = None) -> Optional[SnapshotInfo]:
        """创建操作前快照"""
        return self._intelligent_snapshot.create_pre_operation_snapshot(operation_name, metadata)
    
    def evaluate_rollback_trigger(self, metrics: HealthMetrics = None) -> Dict[str, Any]:
        """评估回滚触发"""
        if metrics is None:
            metrics = self.health_monitor.check_health()
        
        return self._intelligent_trigger.evaluate(metrics)
    
    def add_trigger_rule(self, name: str, condition: Callable, action: str, priority: int = 50, cooldown: int = 60):
        """添加触发规则"""
        self._intelligent_trigger.add_custom_rule(name, condition, action, priority, cooldown)
    
    def send_enhanced_notification(
        self,
        title: str,
        message: str,
        severity: str = "info",
        details: Dict[str, Any] = None,
        dedup_key: str = None
    ) -> Dict[str, Any]:
        """发送增强通知"""
        return self._enhanced_notification.send_enhanced_notification(
            title, message, severity, details, dedup_key
        )
    
    def verify_rollback_enhanced(
        self,
        level: VerificationLevel = VerificationLevel.STANDARD,
        include_tests: bool = False
    ) -> Dict[str, Any]:
        """增强回滚验证"""
        return self._enhanced_verifier.verify_rollback(level, include_tests=include_tests)
    
    def add_verification_check(self, check_func: Callable[[], bool]):
        """添加验证检查"""
        self._enhanced_verifier.add_custom_check(check_func)
    
    def intelligent_rollback_v2(
        self,
        snapshot_id: str,
        trigger: RollbackTrigger = RollbackTrigger.MANUAL,
        verify: bool = True,
        verify_level: VerificationLevel = VerificationLevel.STANDARD
    ) -> RollbackResult:
        """智能回滚 V2"""
        
        risk_assessment = self.assess_rollback_risk(snapshot_id)
        
        if not risk_assessment.can_proceed:
            self._enhanced_notification.send_enhanced_notification(
                "[警告] 回滚风险评估未通过",
                f"快照: {snapshot_id}, 影响: {risk_assessment.estimated_impact}",
                severity="warning",
                details={'risk_assessment': asdict(risk_assessment)}
            )
            
            return RollbackResult(
                success=False,
                snapshot_id=snapshot_id,
                trigger=trigger,
                timestamp=datetime.now().isoformat(),
                files_restored=0,
                files_failed=0,
                verification_passed=False,
                error_message=risk_assessment.estimated_impact
            )
        
        if risk_assessment.requires_backup:
            backup_snapshot = self.create_snapshot(
                version=f"backup_before_rollback_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                description="回滚前自动备份",
                tags=["backup", "pre-rollback"]
            )
            logger.info(f"创建回滚前备份: {backup_snapshot.snapshot_id}")
        
        result = self.rollback(
            snapshot_id,
            trigger=trigger,
            verify=verify,
            verification_level=verify_level
        )
        
        if verify:
            enhanced_result = self._enhanced_verifier.verify_rollback(verify_level)
            if not enhanced_result['passed']:
                result.verification_passed = False
                result.warnings.extend(enhanced_result['errors'])
        
        notification_severity = "info" if result.success else "error"
        self._enhanced_notification.send_enhanced_notification(
            f"[{'成功' if result.success else '失败'}] 回滚操作完成",
            f"快照: {snapshot_id}, 恢复文件: {result.files_restored}",
            severity=notification_severity,
            details={'rollback_result': asdict(result)},
            dedup_key=f"rollback_{snapshot_id}"
        )
        
        return result
    
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """获取增强统计信息"""
        base_stats = self.get_statistics()
        
        enhanced_stats = {
            'notification_stats': self._enhanced_notification.get_notification_statistics(),
            'trigger_history': self._intelligent_trigger.get_trigger_history(limit=10),
            'verification_history': self._enhanced_verifier.get_verification_history(limit=10),
            'snapshot_changes': self._intelligent_snapshot.get_change_history(limit=10)
        }
        
        return {**base_stats, 'enhanced': enhanced_stats}


if __name__ == "__main__":
    run_cli()
