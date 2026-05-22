#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复回滚管理器 - Fix Rollback Manager

完善的修复回滚机制，包括：
- 修复前备份（Pre-fix Backup）
- 修复回滚功能（Fix Rollback）
- 修复历史记录（Fix History）
- 修复效果追踪（Fix Effect Tracking）
- 多版本备份管理
- 自动清理过期备份

使用示例:
    python fix_rollback_manager.py --backup --file code.py
    python fix_rollback_manager.py --rollback --fix-id FIX_001
    python fix_rollback_manager.py --history --file code.py
    python fix_rollback_manager.py --stats
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackupStatus(Enum):
    CREATED = "created"
    RESTORED = "restored"
    DELETED = "deleted"
    EXPIRED = "expired"
    CORRUPTED = "corrupted"


class RollbackStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class FixStatus(Enum):
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    PARTIAL = "partial"
    PENDING = "pending"


class TrackingStatus(Enum):
    EFFECTIVE = "effective"
    INEFFECTIVE = "ineffective"
    REGRESSED = "regressed"
    UNKNOWN = "unknown"


@dataclass
class FileBackup:
    backup_id: str
    fix_id: str
    file_path: str
    original_content: str
    backup_path: str
    content_hash: str
    created_at: str
    file_size: int
    status: BackupStatus
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "fix_id": self.fix_id,
            "file_path": self.file_path,
            "backup_path": self.backup_path,
            "content_hash": self.content_hash,
            "created_at": self.created_at,
            "file_size": self.file_size,
            "status": self.status.value,
            "metadata": self.metadata
        }


@dataclass
class FixRecord:
    fix_id: str
    file_path: str
    fix_type: str
    description: str
    original_content: str
    fixed_content: str
    backup_id: str
    applied_at: str
    status: FixStatus
    confidence: float
    validation_result: Optional[Dict[str, Any]] = None
    rollback_count: int = 0
    last_rollback_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fix_id": self.fix_id,
            "file_path": self.file_path,
            "fix_type": self.fix_type,
            "description": self.description,
            "backup_id": self.backup_id,
            "applied_at": self.applied_at,
            "status": self.status.value,
            "confidence": self.confidence,
            "validation_result": self.validation_result,
            "rollback_count": self.rollback_count,
            "last_rollback_at": self.last_rollback_at,
            "metadata": self.metadata
        }


@dataclass
class RollbackRecord:
    rollback_id: str
    fix_id: str
    file_path: str
    backup_id: str
    status: RollbackStatus
    rolled_back_at: str
    reason: str
    content_before: str
    content_after: str
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rollback_id": self.rollback_id,
            "fix_id": self.fix_id,
            "file_path": self.file_path,
            "backup_id": self.backup_id,
            "status": self.status.value,
            "rolled_back_at": self.rolled_back_at,
            "reason": self.reason,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


@dataclass
class TrackingRecord:
    tracking_id: str
    fix_id: str
    file_path: str
    status: TrackingStatus
    tracked_at: str
    metrics_before: Dict[str, Any] = field(default_factory=dict)
    metrics_after: Dict[str, Any] = field(default_factory=dict)
    improvement_score: float = 0.0
    regression_detected: bool = False
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tracking_id": self.tracking_id,
            "fix_id": self.fix_id,
            "file_path": self.file_path,
            "status": self.status.value,
            "tracked_at": self.tracked_at,
            "metrics_before": self.metrics_before,
            "metrics_after": self.metrics_after,
            "improvement_score": self.improvement_score,
            "regression_detected": self.regression_detected,
            "notes": self.notes,
            "metadata": self.metadata
        }


@dataclass
class FixHistory:
    file_path: str
    total_fixes: int
    successful_fixes: int
    rolled_back_fixes: int
    failed_fixes: int
    first_fix_at: Optional[str]
    last_fix_at: Optional[str]
    fix_records: List[FixRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "total_fixes": self.total_fixes,
            "successful_fixes": self.successful_fixes,
            "rolled_back_fixes": self.rolled_back_fixes,
            "failed_fixes": self.failed_fixes,
            "first_fix_at": self.first_fix_at,
            "last_fix_at": self.last_fix_at,
            "fix_records": [r.to_dict() for r in self.fix_records]
        }


class BackupManager:
    """备份管理器"""

    def __init__(self, backup_dir: Optional[Path] = None, max_backups: int = 100,
                 retention_days: int = 30):
        self.backup_dir = backup_dir or Path.cwd() / ".fix_backups"
        self.max_backups = max_backups
        self.retention_days = retention_days
        self._backup_counter = 0
        self._backups: Dict[str, FileBackup] = {}

        self._ensure_backup_dir()
        self._load_existing_backups()

    def _ensure_backup_dir(self) -> None:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        (self.backup_dir / "metadata").mkdir(exist_ok=True)

    def _load_existing_backups(self) -> None:
        metadata_dir = self.backup_dir / "metadata"
        for meta_file in metadata_dir.glob("*.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                backup = FileBackup(
                    backup_id=data["backup_id"],
                    fix_id=data["fix_id"],
                    file_path=data["file_path"],
                    original_content="",
                    backup_path=data["backup_path"],
                    content_hash=data["content_hash"],
                    created_at=data["created_at"],
                    file_size=data["file_size"],
                    status=BackupStatus(data["status"]),
                    metadata=data.get("metadata", {})
                )
                self._backups[backup.backup_id] = backup
            except Exception as e:
                logger.error(f"加载备份元数据失败: {meta_file}, {e}")

    def create_backup(self, file_path: str, fix_id: str,
                     content: Optional[str] = None) -> Optional[FileBackup]:
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"文件不存在: {file_path}")
                return None

            if content is None:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

            self._backup_counter += 1
            backup_id = f"BACKUP_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._backup_counter:04d}"

            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            backup_filename = f"{backup_id}_{path.stem}.bak"
            backup_path = self.backup_dir / backup_filename

            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)

            backup = FileBackup(
                backup_id=backup_id,
                fix_id=fix_id,
                file_path=str(path.absolute()),
                original_content=content,
                backup_path=str(backup_path),
                content_hash=content_hash,
                created_at=datetime.now().isoformat(),
                file_size=len(content),
                status=BackupStatus.CREATED,
                metadata={
                    "original_filename": path.name,
                    "original_dir": str(path.parent)
                }
            )

            self._backups[backup_id] = backup
            self._save_backup_metadata(backup)

            self._cleanup_old_backups()

            logger.info(f"创建备份成功: {backup_id} -> {backup_path}")
            return backup

        except Exception as e:
            logger.error(f"创建备份失败: {file_path}, {e}")
            return None

    def _save_backup_metadata(self, backup: FileBackup) -> None:
        metadata_path = self.backup_dir / "metadata" / f"{backup.backup_id}.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(backup.to_dict(), f, indent=2, ensure_ascii=False)

    def restore_backup(self, backup_id: str) -> Tuple[bool, str]:
        if backup_id not in self._backups:
            return False, f"备份不存在: {backup_id}"

        backup = self._backups[backup_id]

        try:
            backup_path = Path(backup.backup_path)
            if not backup_path.exists():
                return False, f"备份文件不存在: {backup.backup_path}"

            with open(backup_path, 'r', encoding='utf-8') as f:
                content = f.read()

            file_path = Path(backup.file_path)
            if not file_path.parent.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            backup.status = BackupStatus.RESTORED
            self._save_backup_metadata(backup)

            logger.info(f"恢复备份成功: {backup_id} -> {backup.file_path}")
            return True, f"成功恢复到 {backup.file_path}"

        except Exception as e:
            logger.error(f"恢复备份失败: {backup_id}, {e}")
            return False, str(e)

    def delete_backup(self, backup_id: str) -> bool:
        if backup_id not in self._backups:
            return False

        backup = self._backups[backup_id]

        try:
            backup_path = Path(backup.backup_path)
            if backup_path.exists():
                backup_path.unlink()

            metadata_path = self.backup_dir / "metadata" / f"{backup_id}.json"
            if metadata_path.exists():
                metadata_path.unlink()

            backup.status = BackupStatus.DELETED
            del self._backups[backup_id]

            logger.info(f"删除备份成功: {backup_id}")
            return True

        except Exception as e:
            logger.error(f"删除备份失败: {backup_id}, {e}")
            return False

    def get_backup(self, backup_id: str) -> Optional[FileBackup]:
        return self._backups.get(backup_id)

    def get_backups_for_file(self, file_path: str) -> List[FileBackup]:
        return [b for b in self._backups.values() if b.file_path == file_path]

    def get_backups_for_fix(self, fix_id: str) -> List[FileBackup]:
        return [b for b in self._backups.values() if b.fix_id == fix_id]

    def _cleanup_old_backups(self) -> int:
        cleaned = 0
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        expired_backups = [
            b for b in self._backups.values()
            if datetime.fromisoformat(b.created_at) < cutoff_date
        ]

        for backup in expired_backups:
            if self.delete_backup(backup.backup_id):
                cleaned += 1

        if len(self._backups) > self.max_backups:
            sorted_backups = sorted(
                self._backups.values(),
                key=lambda b: b.created_at
            )
            to_delete = sorted_backups[:len(self._backups) - self.max_backups]
            for backup in to_delete:
                if self.delete_backup(backup.backup_id):
                    cleaned += 1

        if cleaned > 0:
            logger.info(f"清理了 {cleaned} 个过期备份")

        return cleaned

    def get_backup_content(self, backup_id: str) -> Optional[str]:
        backup = self.get_backup(backup_id)
        if not backup:
            return None

        try:
            with open(backup.backup_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取备份内容失败: {backup_id}, {e}")
            return None

    def list_backups(self) -> List[FileBackup]:
        return list(self._backups.values())


class RollbackManager:
    """回滚管理器"""

    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self._rollback_counter = 0
        self._rollback_records: Dict[str, RollbackRecord] = {}

    def rollback_fix(self, fix_id: str, reason: str = "",
                    file_path: Optional[str] = None) -> Optional[RollbackRecord]:
        backups = self.backup_manager.get_backups_for_fix(fix_id)

        if not backups:
            logger.error(f"未找到修复 {fix_id} 的备份")
            return None

        if file_path:
            backups = [b for b in backups if b.file_path == file_path]

        if not backups:
            logger.error(f"未找到修复 {fix_id} 在文件 {file_path} 的备份")
            return None

        backup = backups[0]

        try:
            with open(backup.file_path, 'r', encoding='utf-8') as f:
                content_before = f.read()
        except Exception:
            content_before = ""

        success, message = self.backup_manager.restore_backup(backup.backup_id)

        self._rollback_counter += 1
        rollback_id = f"ROLLBACK_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._rollback_counter:04d}"

        status = RollbackStatus.SUCCESS if success else RollbackStatus.FAILED

        try:
            with open(backup.file_path, 'r', encoding='utf-8') as f:
                content_after = f.read()
        except Exception:
            content_after = content_before

        rollback_record = RollbackRecord(
            rollback_id=rollback_id,
            fix_id=fix_id,
            file_path=backup.file_path,
            backup_id=backup.backup_id,
            status=status,
            rolled_back_at=datetime.now().isoformat(),
            reason=reason or "手动回滚",
            content_before=content_before,
            content_after=content_after,
            error_message="" if success else message
        )

        self._rollback_records[rollback_id] = rollback_record

        if success:
            logger.info(f"回滚成功: {rollback_id}")
        else:
            logger.error(f"回滚失败: {rollback_id}, {message}")

        return rollback_record

    def rollback_file(self, file_path: str, reason: str = "") -> List[RollbackRecord]:
        backups = self.backup_manager.get_backups_for_file(file_path)
        if not backups:
            logger.warning(f"文件 {file_path} 没有可用的备份")
            return []

        latest_backup = max(backups, key=lambda b: b.created_at)
        record = self.rollback_fix(latest_backup.fix_id, reason, file_path)
        return [record] if record else []

    def get_rollback_record(self, rollback_id: str) -> Optional[RollbackRecord]:
        return self._rollback_records.get(rollback_id)

    def get_rollback_history(self, file_path: Optional[str] = None) -> List[RollbackRecord]:
        records = list(self._rollback_records.values())
        if file_path:
            records = [r for r in records if r.file_path == file_path]
        return sorted(records, key=lambda r: r.rolled_back_at, reverse=True)


class FixHistoryManager:
    """修复历史管理器"""

    def __init__(self, backup_manager: BackupManager, history_file: Optional[Path] = None):
        self.backup_manager = backup_manager
        self.history_file = history_file or Path.cwd() / ".fix_history" / "fix_history.json"
        self._fix_counter = 0
        self._fix_records: Dict[str, FixRecord] = {}
        self._file_histories: Dict[str, FixHistory] = {}

        self._ensure_history_dir()
        self._load_history()

    def _ensure_history_dir(self) -> None:
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_history(self) -> None:
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for fix_id, record_data in data.get("fix_records", {}).items():
                    self._fix_records[fix_id] = FixRecord(
                        fix_id=record_data["fix_id"],
                        file_path=record_data["file_path"],
                        fix_type=record_data["fix_type"],
                        description=record_data["description"],
                        original_content="",
                        fixed_content="",
                        backup_id=record_data["backup_id"],
                        applied_at=record_data["applied_at"],
                        status=FixStatus(record_data["status"]),
                        confidence=record_data.get("confidence", 1.0),
                        validation_result=record_data.get("validation_result"),
                        rollback_count=record_data.get("rollback_count", 0),
                        last_rollback_at=record_data.get("last_rollback_at"),
                        metadata=record_data.get("metadata", {})
                    )

                logger.info(f"加载了 {len(self._fix_records)} 条修复历史记录")
            except Exception as e:
                logger.error(f"加载修复历史失败: {e}")

    def _save_history(self) -> None:
        try:
            data = {
                "fix_records": {
                    fix_id: record.to_dict()
                    for fix_id, record in self._fix_records.items()
                },
                "last_updated": datetime.now().isoformat()
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存修复历史失败: {e}")

    def record_fix(self, file_path: str, fix_type: str, description: str,
                  original_content: str, fixed_content: str,
                  backup_id: str, confidence: float = 1.0,
                  validation_result: Optional[Dict[str, Any]] = None) -> FixRecord:
        self._fix_counter += 1
        fix_id = f"FIX_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._fix_counter:04d}"

        record = FixRecord(
            fix_id=fix_id,
            file_path=file_path,
            fix_type=fix_type,
            description=description,
            original_content=original_content,
            fixed_content=fixed_content,
            backup_id=backup_id,
            applied_at=datetime.now().isoformat(),
            status=FixStatus.APPLIED,
            confidence=confidence,
            validation_result=validation_result
        )

        self._fix_records[fix_id] = record
        self._update_file_history(record)
        self._save_history()

        logger.info(f"记录修复: {fix_id}")
        return record

    def _update_file_history(self, record: FixRecord) -> None:
        file_path = record.file_path
        if file_path not in self._file_histories:
            self._file_histories[file_path] = FixHistory(
                file_path=file_path,
                total_fixes=0,
                successful_fixes=0,
                rolled_back_fixes=0,
                failed_fixes=0,
                first_fix_at=record.applied_at,
                last_fix_at=record.applied_at
            )

        history = self._file_histories[file_path]
        history.total_fixes += 1
        history.last_fix_at = record.applied_at

        if record.status == FixStatus.APPLIED:
            history.successful_fixes += 1
        elif record.status == FixStatus.ROLLED_BACK:
            history.rolled_back_fixes += 1
        elif record.status == FixStatus.FAILED:
            history.failed_fixes += 1

        history.fix_records.append(record)

    def update_fix_status(self, fix_id: str, status: FixStatus) -> bool:
        if fix_id not in self._fix_records:
            return False

        record = self._fix_records[fix_id]
        record.status = status

        if status == FixStatus.ROLLED_BACK:
            record.rollback_count += 1
            record.last_rollback_at = datetime.now().isoformat()

        self._save_history()
        return True

    def get_fix_record(self, fix_id: str) -> Optional[FixRecord]:
        return self._fix_records.get(fix_id)

    def get_file_history(self, file_path: str) -> Optional[FixHistory]:
        return self._file_histories.get(file_path)

    def get_recent_fixes(self, limit: int = 10) -> List[FixRecord]:
        sorted_records = sorted(
            self._fix_records.values(),
            key=lambda r: r.applied_at,
            reverse=True
        )
        return sorted_records[:limit]

    def get_fixes_by_type(self, fix_type: str) -> List[FixRecord]:
        return [r for r in self._fix_records.values() if r.fix_type == fix_type]

    def get_fixes_by_status(self, status: FixStatus) -> List[FixRecord]:
        return [r for r in self._fix_records.values() if r.status == status]


class FixEffectTracker:
    """修复效果追踪器"""

    def __init__(self, history_manager: FixHistoryManager):
        self.history_manager = history_manager
        self._tracking_counter = 0
        self._tracking_records: Dict[str, TrackingRecord] = {}

    def track_fix(self, fix_id: str, metrics_before: Dict[str, Any],
                 metrics_after: Dict[str, Any]) -> Optional[TrackingRecord]:
        fix_record = self.history_manager.get_fix_record(fix_id)
        if not fix_record:
            logger.error(f"修复记录不存在: {fix_id}")
            return None

        self._tracking_counter += 1
        tracking_id = f"TRACK_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._tracking_counter:04d}"

        improvement_score = self._calculate_improvement(metrics_before, metrics_after)
        regression_detected = self._detect_regression(metrics_before, metrics_after)

        if regression_detected:
            status = TrackingStatus.REGRESSED
        elif improvement_score > 0:
            status = TrackingStatus.EFFECTIVE
        elif improvement_score < 0:
            status = TrackingStatus.INEFFECTIVE
        else:
            status = TrackingStatus.UNKNOWN

        tracking_record = TrackingRecord(
            tracking_id=tracking_id,
            fix_id=fix_id,
            file_path=fix_record.file_path,
            status=status,
            tracked_at=datetime.now().isoformat(),
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            improvement_score=improvement_score,
            regression_detected=regression_detected
        )

        self._tracking_records[tracking_id] = tracking_record

        logger.info(f"追踪修复效果: {tracking_id}, 状态: {status.value}, 改进分数: {improvement_score:.2f}")
        return tracking_record

    def _calculate_improvement(self, before: Dict[str, Any], after: Dict[str, Any]) -> float:
        score = 0.0

        if "error_count" in before and "error_count" in after:
            diff = before["error_count"] - after["error_count"]
            score += diff * 10

        if "warning_count" in before and "warning_count" in after:
            diff = before["warning_count"] - after["warning_count"]
            score += diff * 5

        if "complexity" in before and "complexity" in after:
            diff = before["complexity"] - after["complexity"]
            score += diff * 2

        if "test_pass_rate" in before and "test_pass_rate" in after:
            diff = after["test_pass_rate"] - before["test_pass_rate"]
            score += diff * 20

        if "performance_score" in before and "performance_score" in after:
            diff = after["performance_score"] - before["performance_score"]
            score += diff * 5

        return score

    def _detect_regression(self, before: Dict[str, Any], after: Dict[str, Any]) -> bool:
        if "error_count" in before and "error_count" in after:
            if after["error_count"] > before["error_count"]:
                return True

        if "test_pass_rate" in before and "test_pass_rate" in after:
            if after["test_pass_rate"] < before["test_pass_rate"] - 0.1:
                return True

        if "new_issues" in after and after["new_issues"] > 0:
            return True

        return False

    def get_tracking_record(self, tracking_id: str) -> Optional[TrackingRecord]:
        return self._tracking_records.get(tracking_id)

    def get_tracking_for_fix(self, fix_id: str) -> List[TrackingRecord]:
        return [r for r in self._tracking_records.values() if r.fix_id == fix_id]

    def get_effective_fixes(self) -> List[TrackingRecord]:
        return [r for r in self._tracking_records.values() if r.status == TrackingStatus.EFFECTIVE]

    def get_regressed_fixes(self) -> List[TrackingRecord]:
        return [r for r in self._tracking_records.values() if r.status == TrackingStatus.REGRESSED]

    def get_tracking_statistics(self) -> Dict[str, Any]:
        total = len(self._tracking_records)
        if total == 0:
            return {"total": 0}

        effective = sum(1 for r in self._tracking_records.values() if r.status == TrackingStatus.EFFECTIVE)
        ineffective = sum(1 for r in self._tracking_records.values() if r.status == TrackingStatus.INEFFECTIVE)
        regressed = sum(1 for r in self._tracking_records.values() if r.status == TrackingStatus.REGRESSED)

        avg_improvement = sum(r.improvement_score for r in self._tracking_records.values()) / total

        return {
            "total": total,
            "effective": effective,
            "ineffective": ineffective,
            "regressed": regressed,
            "effectiveness_rate": effective / total,
            "regression_rate": regressed / total,
            "average_improvement": avg_improvement
        }


class FixRollbackManager:
    """修复回滚管理器主类"""

    def __init__(self, backup_dir: Optional[Path] = None):
        self.backup_manager = BackupManager(backup_dir)
        self.rollback_manager = RollbackManager(self.backup_manager)
        self.history_manager = FixHistoryManager(self.backup_manager)
        self.effect_tracker = FixEffectTracker(self.history_manager)

    def backup_before_fix(self, file_path: str, fix_id: str) -> Optional[FileBackup]:
        return self.backup_manager.create_backup(file_path, fix_id)

    def record_fix(self, file_path: str, fix_type: str, description: str,
                  original_content: str, fixed_content: str,
                  backup_id: str, confidence: float = 1.0) -> FixRecord:
        return self.history_manager.record_fix(
            file_path=file_path,
            fix_type=fix_type,
            description=description,
            original_content=original_content,
            fixed_content=fixed_content,
            backup_id=backup_id,
            confidence=confidence
        )

    def rollback(self, fix_id: str, reason: str = "") -> Optional[RollbackRecord]:
        result = self.rollback_manager.rollback_fix(fix_id, reason)
        if result and result.status == RollbackStatus.SUCCESS:
            self.history_manager.update_fix_status(fix_id, FixStatus.ROLLED_BACK)
        return result

    def rollback_file(self, file_path: str, reason: str = "") -> List[RollbackRecord]:
        return self.rollback_manager.rollback_file(file_path, reason)

    def track_effect(self, fix_id: str, metrics_before: Dict[str, Any],
                    metrics_after: Dict[str, Any]) -> Optional[TrackingRecord]:
        return self.effect_tracker.track_fix(fix_id, metrics_before, metrics_after)

    def get_fix_history(self, file_path: str) -> Optional[FixHistory]:
        return self.history_manager.get_file_history(file_path)

    def get_recent_fixes(self, limit: int = 10) -> List[FixRecord]:
        return self.history_manager.get_recent_fixes(limit)

    def get_effective_fixes(self) -> List[TrackingRecord]:
        return self.effect_tracker.get_effective_fixes()

    def get_regressed_fixes(self) -> List[TrackingRecord]:
        return self.effect_tracker.get_regressed_fixes()

    def get_statistics(self) -> Dict[str, Any]:
        tracking_stats = self.effect_tracker.get_tracking_statistics()

        all_records = list(self.history_manager._fix_records.values())
        total_fixes = len(all_records)
        applied = sum(1 for r in all_records if r.status == FixStatus.APPLIED)
        rolled_back = sum(1 for r in all_records if r.status == FixStatus.ROLLED_BACK)
        failed = sum(1 for r in all_records if r.status == FixStatus.FAILED)

        return {
            "total_fixes": total_fixes,
            "applied_fixes": applied,
            "rolled_back_fixes": rolled_back,
            "failed_fixes": failed,
            "total_backups": len(self.backup_manager._backups),
            "total_rollbacks": len(self.rollback_manager._rollback_records),
            "tracking_statistics": tracking_stats
        }

    def cleanup(self) -> Dict[str, int]:
        cleaned_backups = self.backup_manager._cleanup_old_backups()

        return {
            "cleaned_backups": cleaned_backups
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="修复回滚管理器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--backup", action="store_true", help="创建备份")
    parser.add_argument("--rollback", action="store_true", help="执行回滚")
    parser.add_argument("--history", action="store_true", help="查看历史")
    parser.add_argument("--track", action="store_true", help="追踪效果")
    parser.add_argument("--stats", action="store_true", help="查看统计")
    parser.add_argument("--cleanup", action="store_true", help="清理过期备份")
    parser.add_argument("--file", type=str, help="文件路径")
    parser.add_argument("--fix-id", type=str, help="修复ID")
    parser.add_argument("--reason", type=str, default="", help="回滚原因")
    parser.add_argument("--backup-dir", type=str, help="备份目录")

    args = parser.parse_args()

    backup_dir = Path(args.backup_dir) if args.backup_dir else None
    manager = FixRollbackManager(backup_dir)

    if args.backup and args.file:
        fix_id = args.fix_id or f"FIX_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        backup = manager.backup_before_fix(args.file, fix_id)
        if backup:
            print(f"备份创建成功: {backup.backup_id}")
        else:
            print("备份创建失败")

    elif args.rollback and args.fix_id:
        record = manager.rollback(args.fix_id, args.reason)
        if record:
            print(f"回滚状态: {record.status.value}")
            if record.error_message:
                print(f"错误信息: {record.error_message}")
        else:
            print("回滚失败")

    elif args.history and args.file:
        history = manager.get_fix_history(args.file)
        if history:
            print(f"\n文件: {history.file_path}")
            print(f"总修复次数: {history.total_fixes}")
            print(f"成功修复: {history.successful_fixes}")
            print(f"已回滚: {history.rolled_back_fixes}")
            print(f"失败: {history.failed_fixes}")
            print(f"\n最近修复记录:")
            for record in history.fix_records[-5:]:
                print(f"  - {record.fix_id}: {record.fix_type} ({record.applied_at})")
        else:
            print("未找到历史记录")

    elif args.stats:
        stats = manager.get_statistics()
        print("\n修复统计:")
        print(f"  总修复数: {stats['total_fixes']}")
        print(f"  已应用: {stats['applied_fixes']}")
        print(f"  已回滚: {stats['rolled_back_fixes']}")
        print(f"  失败: {stats['failed_fixes']}")
        print(f"  总备份数: {stats['total_backups']}")
        print(f"  总回滚数: {stats['total_rollbacks']}")
        print(f"\n效果追踪统计:")
        tracking = stats['tracking_statistics']
        print(f"  总追踪数: {tracking['total']}")
        if tracking['total'] > 0:
            print(f"  有效修复: {tracking['effective']}")
            print(f"  无效修复: {tracking['ineffective']}")
            print(f"  回归修复: {tracking['regressed']}")
            print(f"  有效率: {tracking['effectiveness_rate']:.1%}")
            print(f"  平均改进分数: {tracking['average_improvement']:.2f}")

    elif args.cleanup:
        result = manager.cleanup()
        print(f"清理完成: 删除了 {result['cleaned_backups']} 个过期备份")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
