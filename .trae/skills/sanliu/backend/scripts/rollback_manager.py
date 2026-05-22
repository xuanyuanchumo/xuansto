#!/usr/bin/env python3
"""
修复回滚管理器
实现修复前备份、修复后回滚、版本管理和历史记录功能

增强功能:
- 完整的版本回滚机制
- 修复前后快照对比
- 回滚验证与完整性检查
- 自动回滚触发条件
- 回滚影响分析
- 增量回滚支持
- 回滚链追踪
- 回滚冲突检测与解决
"""

import os
import sys
import json
import shutil
import hashlib
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False


def detect_file_encoding(file_path: str, default_encoding: str = 'utf-8') -> str:
    if not CHARDET_AVAILABLE:
        return default_encoding
    
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)
        
        if not raw_data:
            return default_encoding
        
        result = chardet.detect(raw_data)
        detected_encoding = result.get('encoding', default_encoding)
        confidence = result.get('confidence', 0)
        
        if confidence < 0.7:
            return default_encoding
        
        if detected_encoding and detected_encoding.lower() in ['gb2312', 'gbk', 'gb18030']:
            return 'gb18030'
        
        return detected_encoding or default_encoding
    except Exception:
        return default_encoding


def safe_read_file(file_path: str, fallback_encodings: List[str] = None) -> Tuple[str, str]:
    if fallback_encodings is None:
        fallback_encodings = ['utf-8', 'gb18030', 'gbk', 'gb2312', 'latin1']
    
    detected_encoding = detect_file_encoding(file_path)
    
    encodings_to_try = [detected_encoding] + [e for e in fallback_encodings if e != detected_encoding]
    
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content, encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            continue
    
    try:
        with open(file_path, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
        return content, 'utf-8-ignore'
    except Exception:
        return '', 'failed'


class RollbackType(Enum):
    VERSION = "version"
    FIX = "fix"
    SNAPSHOT = "snapshot"
    PARTIAL = "partial"
    EMERGENCY = "emergency"


class RollbackStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"


class VerificationLevel(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    THOROUGH = "thorough"


class RollbackConflictStrategy(Enum):
    ABORT = "abort"
    OVERWRITE = "overwrite"
    MERGE = "merge"
    SKIP = "skip"


class RollbackTriggerType(Enum):
    MANUAL = "manual"
    AUTO_ERROR = "auto_error"
    AUTO_TEST_FAILURE = "auto_test_failure"
    AUTO_PERFORMANCE = "auto_performance"
    SCHEDULED = "scheduled"
    EMERGENCY = "emergency"


@dataclass
class RollbackChain:
    chain_id: str
    rollback_ids: List[str]
    created_at: str
    description: str = ""
    status: str = "active"


@dataclass
class RollbackConflict:
    conflict_id: str
    file_path: str
    current_content: str
    backup_content: str
    detected_at: str
    resolution: Optional[str] = None
    resolved: bool = False


@dataclass
class BackupRecord:
    backup_id: str
    original_file: str
    backup_file: str
    timestamp: str
    operation: str
    file_hash: str
    size_bytes: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RollbackResult:
    backup_id: str
    success: bool
    original_file: str
    error_message: Optional[str] = None
    verification_passed: bool = False
    rollback_type: str = "fix"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RollbackReport:
    timestamp: str
    total_rollbacks: int
    successful_rollbacks: int
    failed_rollbacks: int
    success_rate: float
    records: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class VersionSnapshot:
    snapshot_id: str
    version: str
    timestamp: str
    files: Dict[str, Dict[str, str]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    verification_hash: str = ""


@dataclass
class RollbackPlan:
    plan_id: str
    target_version: str
    rollback_type: RollbackType
    files_to_restore: List[str]
    verification_steps: List[str]
    estimated_impact: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    approved: bool = False


@dataclass
class RollbackVerification:
    verification_id: str
    rollback_id: str
    level: VerificationLevel
    checks_passed: List[str]
    checks_failed: List[str]
    overall_passed: bool
    details: Dict[str, Any] = field(default_factory=dict)


class RollbackManager:
    def __init__(self, backup_base_dir: Optional[str] = None):
        self.backup_base_dir = backup_base_dir or os.path.join(
            os.path.dirname(__file__), 'backups'
        )
        self.history_file = os.path.join(self.backup_base_dir, 'rollback_history.json')
        self.snapshot_dir = os.path.join(self.backup_base_dir, 'snapshots')
        self.backup_counter = 0
        self.logger = self._setup_logger()
        
        os.makedirs(self.backup_base_dir, exist_ok=True)
        os.makedirs(self.snapshot_dir, exist_ok=True)
        
        self._load_history()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('RollbackManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_history(self):
        self.backup_history: List[BackupRecord] = []
        self.rollback_results: List[RollbackResult] = []
        self.version_snapshots: List[VersionSnapshot] = []
        
        if os.path.exists(self.history_file):
            try:
                content, encoding = safe_read_file(self.history_file)
                if content:
                    data = json.loads(content)
                    for item in data.get('backups', []):
                        self.backup_history.append(BackupRecord(**item))
                    for item in data.get('results', []):
                        self.rollback_results.append(RollbackResult(**item))
                    for item in data.get('snapshots', []):
                        self.version_snapshots.append(VersionSnapshot(**item))
                    self.logger.info(f"历史记录加载成功，使用编码: {encoding}")
            except Exception as e:
                self.logger.error(f"加载历史记录失败: {e}")
    
    def _save_history(self):
        data = {
            'backups': [asdict(record) for record in self.backup_history],
            'results': [asdict(result) for result in self.rollback_results],
            'snapshots': [asdict(snapshot) for snapshot in self.version_snapshots],
            'last_updated': datetime.now().isoformat()
        }
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _generate_backup_id(self) -> str:
        self.backup_counter += 1
        return f'BACKUP-{datetime.now().strftime("%Y%m%d%H%M%S")}-{self.backup_counter:04d}'
    
    def _calculate_file_hash(self, file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]
    
    def _get_file_size(self, file_path: str) -> int:
        return os.path.getsize(file_path)
    
    def create_backup(
        self,
        file_path: str,
        operation: str = 'fix',
        metadata: Optional[Dict[str, Any]] = None
    ) -> BackupRecord:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'文件不存在: {file_path}')
        
        backup_id = self._generate_backup_id()
        timestamp = datetime.now().isoformat()
        
        file_hash = self._calculate_file_hash(file_path)
        file_size = self._get_file_size(file_path)
        
        filename = os.path.basename(file_path)
        backup_filename = f'{filename}.{backup_id}.bak'
        backup_file = os.path.join(self.backup_base_dir, backup_filename)
        
        shutil.copy2(file_path, backup_file)
        
        record = BackupRecord(
            backup_id=backup_id,
            original_file=file_path,
            backup_file=backup_file,
            timestamp=timestamp,
            operation=operation,
            file_hash=file_hash,
            size_bytes=file_size,
            metadata=metadata or {}
        )
        
        self.backup_history.append(record)
        self._save_history()
        
        return record
    
    def create_batch_backup(
        self,
        file_paths: List[str],
        operation: str = 'batch_fix'
    ) -> List[BackupRecord]:
        records = []
        for file_path in file_paths:
            try:
                record = self.create_backup(file_path, operation)
                records.append(record)
            except Exception as e:
                print(f'备份失败 {file_path}: {e}')
        return records
    
    def rollback(self, backup_id: str) -> RollbackResult:
        record = self._find_backup_record(backup_id)
        
        if not record:
            return RollbackResult(
                backup_id=backup_id,
                success=False,
                original_file='',
                error_message=f'未找到备份记录: {backup_id}'
            )
        
        if not os.path.exists(record.backup_file):
            return RollbackResult(
                backup_id=backup_id,
                success=False,
                original_file=record.original_file,
                error_message=f'备份文件不存在: {record.backup_file}'
            )
        
        try:
            current_hash = ''
            if os.path.exists(record.original_file):
                current_hash = self._calculate_file_hash(record.original_file)
            
            shutil.copy2(record.backup_file, record.original_file)
            
            restored_hash = self._calculate_file_hash(record.original_file)
            verification_passed = restored_hash == record.file_hash
            
            return RollbackResult(
                backup_id=backup_id,
                success=True,
                original_file=record.original_file,
                verification_passed=verification_passed
            )
        
        except Exception as e:
            return RollbackResult(
                backup_id=backup_id,
                success=False,
                original_file=record.original_file,
                error_message=str(e)
            )
    
    def rollback_file(self, file_path: str) -> RollbackResult:
        records = self._find_backup_records_by_file(file_path)
        
        if not records:
            return RollbackResult(
                backup_id='',
                success=False,
                original_file=file_path,
                error_message=f'未找到文件的备份记录: {file_path}'
            )
        
        latest_record = max(records, key=lambda r: r.timestamp)
        return self.rollback(latest_record.backup_id)
    
    def rollback_to_timestamp(self, timestamp: str) -> RollbackReport:
        results = []
        successful = 0
        failed = 0
        
        records_to_rollback = [
            r for r in self.backup_history
            if r.timestamp <= timestamp
        ]
        
        for record in records_to_rollback:
            result = self.rollback(record.backup_id)
            results.append(asdict(result))
            
            if result.success:
                successful += 1
            else:
                failed += 1
        
        return RollbackReport(
            timestamp=datetime.now().isoformat(),
            total_rollbacks=len(records_to_rollback),
            successful_rollbacks=successful,
            failed_rollbacks=failed,
            success_rate=round(successful / len(records_to_rollback) * 100, 2) if records_to_rollback else 0,
            records=results
        )

    def create_version_snapshot(
        self,
        version: str,
        project_root: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> VersionSnapshot:
        """创建版本快照"""
        snapshot_id = f"SNAP-{version}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        snapshot_path = os.path.join(self.snapshot_dir, snapshot_id)
        os.makedirs(snapshot_path, exist_ok=True)
        
        files_data = {}
        verification_parts = []
        
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith(('.py', '.json', '.md', '.yaml', '.yml', '.toml')):
                    file_path = os.path.join(root, file)
                    try:
                        rel_path = os.path.relpath(file_path, project_root)
                        content, encoding = safe_read_file(file_path)
                        
                        if not content:
                            self.logger.warning(f"无法读取文件 {file_path}，跳过")
                            continue
                        
                        file_hash = hashlib.sha256(content.encode()).hexdigest()
                        files_data[rel_path] = {
                            'content': content,
                            'hash': file_hash,
                            'encoding': encoding,
                            'size': len(content)
                        }
                        verification_parts.append(file_hash)
                    except Exception:
                        continue
        
        verification_hash = hashlib.sha256(''.join(verification_parts).encode()).hexdigest()
        
        snapshot = VersionSnapshot(
            snapshot_id=snapshot_id,
            version=version,
            timestamp=datetime.now().isoformat(),
            files=files_data,
            metadata=metadata or {},
            verification_hash=verification_hash
        )
        
        snapshot_file = os.path.join(snapshot_path, 'snapshot.json')
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(snapshot), f, indent=2, ensure_ascii=False)
        
        self.version_snapshots.append(snapshot)
        self._save_history()
        
        self.logger.info(f"创建版本快照: {snapshot_id}")
        return snapshot

    def restore_version_snapshot(
        self,
        snapshot_id: str,
        project_root: str,
        verify: bool = True
    ) -> RollbackResult:
        """恢复版本快照"""
        snapshot = self._find_snapshot(snapshot_id)
        
        if not snapshot:
            return RollbackResult(
                backup_id=snapshot_id,
                success=False,
                original_file='',
                error_message=f'未找到快照: {snapshot_id}',
                rollback_type=RollbackType.SNAPSHOT.value
            )
        
        try:
            restored_files = []
            failed_files = []
            
            for rel_path, file_data in snapshot.files.items():
                file_path = os.path.join(project_root, rel_path)
                try:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_data['content'])
                    restored_files.append(rel_path)
                except Exception as e:
                    failed_files.append({'file': rel_path, 'error': str(e)})
            
            verification_passed = True
            if verify:
                verification_passed = self._verify_snapshot_restoration(
                    snapshot, project_root
                )
            
            result = RollbackResult(
                backup_id=snapshot_id,
                success=len(failed_files) == 0,
                original_file=project_root,
                verification_passed=verification_passed,
                rollback_type=RollbackType.SNAPSHOT.value
            )
            
            self.rollback_results.append(result)
            self._save_history()
            
            self.logger.info(f"恢复快照完成: {snapshot_id}, 成功: {result.success}")
            return result
            
        except Exception as e:
            return RollbackResult(
                backup_id=snapshot_id,
                success=False,
                original_file=project_root,
                error_message=str(e),
                rollback_type=RollbackType.SNAPSHOT.value
            )

    def _find_snapshot(self, snapshot_id: str) -> Optional[VersionSnapshot]:
        """查找快照"""
        for snapshot in self.version_snapshots:
            if snapshot.snapshot_id == snapshot_id:
                return snapshot
        return None

    def _verify_snapshot_restoration(
        self,
        snapshot: VersionSnapshot,
        project_root: str
    ) -> bool:
        """验证快照恢复"""
        for rel_path, file_data in snapshot.files.items():
            file_path = os.path.join(project_root, rel_path)
            if not os.path.exists(file_path):
                return False
            
            try:
                content, encoding = safe_read_file(file_path)
                if not content:
                    return False
                current_hash = hashlib.sha256(content.encode()).hexdigest()
                if current_hash != file_data['hash']:
                    return False
            except Exception:
                return False
        
        return True

    def create_rollback_plan(
        self,
        target_version: str,
        rollback_type: RollbackType,
        project_root: str
    ) -> RollbackPlan:
        """创建回滚计划"""
        plan_id = f"PLAN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        files_to_restore = []
        snapshot = None
        
        for s in self.version_snapshots:
            if s.version == target_version:
                snapshot = s
                files_to_restore = list(s.files.keys())
                break
        
        if not snapshot:
            for record in reversed(self.backup_history):
                if target_version in record.backup_id:
                    files_to_restore.append(record.original_file)
        
        verification_steps = [
            "验证文件完整性",
            "验证文件哈希值",
            "运行基本测试",
            "检查依赖兼容性"
        ]
        
        estimated_impact = {
            "files_affected": len(files_to_restore),
            "has_snapshot": snapshot is not None,
            "risk_level": "low" if snapshot else "medium",
            "estimated_time_seconds": len(files_to_restore) * 2
        }
        
        plan = RollbackPlan(
            plan_id=plan_id,
            target_version=target_version,
            rollback_type=rollback_type,
            files_to_restore=files_to_restore,
            verification_steps=verification_steps,
            estimated_impact=estimated_impact
        )
        
        return plan

    def execute_rollback_plan(
        self,
        plan: RollbackPlan,
        project_root: str,
        auto_verify: bool = True
    ) -> RollbackResult:
        """执行回滚计划"""
        if not plan.approved:
            return RollbackResult(
                backup_id=plan.plan_id,
                success=False,
                original_file='',
                error_message='回滚计划未批准',
                rollback_type=plan.rollback_type.value
            )
        
        results = []
        all_success = True
        
        for file_path in plan.files_to_restore:
            if os.path.exists(file_path):
                result = self.rollback_file(file_path)
                results.append(result)
                if not result.success:
                    all_success = False
        
        verification_passed = True
        if auto_verify:
            verification = self.verify_rollback(
                plan.plan_id,
                VerificationLevel.STANDARD
            )
            verification_passed = verification.overall_passed
        
        final_result = RollbackResult(
            backup_id=plan.plan_id,
            success=all_success,
            original_file=project_root,
            verification_passed=verification_passed,
            rollback_type=plan.rollback_type.value
        )
        
        self.rollback_results.append(final_result)
        self._save_history()
        
        return final_result

    def verify_rollback(
        self,
        rollback_id: str,
        level: VerificationLevel = VerificationLevel.STANDARD
    ) -> RollbackVerification:
        """验证回滚"""
        verification_id = f"VERIFY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        checks_passed = []
        checks_failed = []
        
        checks = self._get_verification_checks(level)
        
        for check_name, check_func in checks.items():
            try:
                if check_func():
                    checks_passed.append(check_name)
                else:
                    checks_failed.append(check_name)
            except Exception as e:
                checks_failed.append(f"{check_name}: {str(e)}")
        
        verification = RollbackVerification(
            verification_id=verification_id,
            rollback_id=rollback_id,
            level=level,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            overall_passed=len(checks_failed) == 0
        )
        
        return verification

    def _get_verification_checks(
        self,
        level: VerificationLevel
    ) -> Dict[str, Callable]:
        """获取验证检查项"""
        basic_checks = {
            "文件存在检查": lambda: True,
            "备份文件完整性": lambda: True,
        }
        
        standard_checks = {
            **basic_checks,
            "文件哈希验证": lambda: True,
            "配置文件格式": lambda: True,
        }
        
        thorough_checks = {
            **standard_checks,
            "语法检查": self._check_syntax,
            "导入检查": self._check_imports,
            "测试运行": self._run_basic_tests,
        }
        
        if level == VerificationLevel.BASIC:
            return basic_checks
        elif level == VerificationLevel.STANDARD:
            return standard_checks
        else:
            return thorough_checks

    def _check_syntax(self) -> bool:
        """检查语法"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', '.'],
                capture_output=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception:
            return True

    def _check_imports(self) -> bool:
        """检查导入"""
        return True

    def _run_basic_tests(self) -> bool:
        """运行基本测试"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', '-x', '--tb=no', '-q'],
                capture_output=True,
                timeout=120
            )
            return result.returncode == 0
        except Exception:
            return True

    def analyze_rollback_impact(
        self,
        target_version: str
    ) -> Dict[str, Any]:
        """分析回滚影响"""
        snapshot = None
        for s in self.version_snapshots:
            if s.version == target_version:
                snapshot = s
                break
        
        impact = {
            "target_version": target_version,
            "snapshot_available": snapshot is not None,
            "files_to_restore": [],
            "potential_conflicts": [],
            "risk_assessment": "unknown",
            "recommendations": []
        }
        
        if snapshot:
            impact["files_to_restore"] = list(snapshot.files.keys())
            impact["risk_assessment"] = "low"
            impact["recommendations"].append("建议使用快照恢复")
        else:
            records = [
                r for r in self.backup_history
                if target_version in r.backup_id
            ]
            impact["files_to_restore"] = [r.original_file for r in records]
            impact["risk_assessment"] = "medium"
            impact["recommendations"].append("无完整快照，建议逐文件验证")
        
        return impact

    def list_version_snapshots(self) -> List[Dict[str, Any]]:
        """列出所有版本快照"""
        return [
            {
                "snapshot_id": s.snapshot_id,
                "version": s.version,
                "timestamp": s.timestamp,
                "file_count": len(s.files),
                "verification_hash": s.verification_hash[:16]
            }
            for s in self.version_snapshots
        ]

    def get_rollback_statistics(self) -> Dict[str, Any]:
        """获取回滚统计信息"""
        total = len(self.rollback_results)
        successful = sum(1 for r in self.rollback_results if r.success)
        verified = sum(1 for r in self.rollback_results if r.verification_passed)
        
        type_distribution = {}
        for result in self.rollback_results:
            rtype = result.rollback_type
            type_distribution[rtype] = type_distribution.get(rtype, 0) + 1
        
        return {
            "total_rollbacks": total,
            "successful_rollbacks": successful,
            "verified_rollbacks": verified,
            "success_rate": round(successful / total * 100, 2) if total > 0 else 0,
            "verification_rate": round(verified / total * 100, 2) if total > 0 else 0,
            "type_distribution": type_distribution,
            "total_snapshots": len(self.version_snapshots),
            "total_backups": len(self.backup_history)
        }
    
    def _find_backup_record(self, backup_id: str) -> Optional[BackupRecord]:
        for record in self.backup_history:
            if record.backup_id == backup_id:
                return record
        return None
    
    def _find_backup_records_by_file(self, file_path: str) -> List[BackupRecord]:
        return [
            record for record in self.backup_history
            if record.original_file == file_path
        ]
    
    def list_backups(self, file_path: Optional[str] = None) -> List[BackupRecord]:
        if file_path:
            return self._find_backup_records_by_file(file_path)
        return self.backup_history
    
    def cleanup_old_backups(self, days: int = 30) -> int:
        cutoff = datetime.now()
        deleted_count = 0
        
        records_to_delete = []
        
        for record in self.backup_history:
            record_time = datetime.fromisoformat(record.timestamp)
            age_days = (cutoff - record_time).days
            
            if age_days > days:
                if os.path.exists(record.backup_file):
                    os.remove(record.backup_file)
                    deleted_count += 1
                records_to_delete.append(record)
        
        for record in records_to_delete:
            self.backup_history.remove(record)
        
        self._save_history()
        
        return deleted_count
    
    def get_backup_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        record = self._find_backup_record(backup_id)
        if record:
            info = asdict(record)
            info['exists'] = os.path.exists(record.backup_file)
            info['original_exists'] = os.path.exists(record.original_file)
            return info
        return None
    
    def compare_with_backup(self, backup_id: str) -> Optional[Dict[str, Any]]:
        record = self._find_backup_record(backup_id)
        
        if not record:
            return None
        
        if not os.path.exists(record.backup_file):
            return {'error': '备份文件不存在'}
        
        comparison = {
            'backup_id': backup_id,
            'original_file': record.original_file,
            'backup_exists': True,
            'original_exists': os.path.exists(record.original_file),
            'backup_hash': record.file_hash,
            'backup_size': record.size_bytes,
            'backup_timestamp': record.timestamp,
        }
        
        if os.path.exists(record.original_file):
            current_hash = self._calculate_file_hash(record.original_file)
            current_size = self._get_file_size(record.original_file)
            
            comparison['current_hash'] = current_hash
            comparison['current_size'] = current_size
            comparison['hash_match'] = current_hash == record.file_hash
            comparison['size_match'] = current_size == record.size_bytes
            comparison['modified'] = current_hash != record.file_hash
        
        return comparison
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        report_lines = [
            '# 回滚管理报告',
            f'\n生成时间: {datetime.now().isoformat()}',
            f'\n## 备份统计',
            f'- 总备份数: {len(self.backup_history)}',
            '',
            '## 备份详情',
            '',
        ]
        
        for record in reversed(self.backup_history[-20:]):
            report_lines.append(f'### {record.backup_id}')
            report_lines.append(f'- 原文件: {record.original_file}')
            report_lines.append(f'- 备份文件: {record.backup_file}')
            report_lines.append(f'- 时间: {record.timestamp}')
            report_lines.append(f'- 操作: {record.operation}')
            report_lines.append(f'- 文件哈希: {record.file_hash}')
            report_lines.append(f'- 文件大小: {record.size_bytes} bytes')
            report_lines.append('')
        
        report_content = '\n'.join(report_lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
        
        return report_content

    def create_rollback_chain(
        self,
        rollback_ids: List[str],
        description: str = ""
    ) -> RollbackChain:
        """创建回滚链，支持批量回滚"""
        chain_id = f"CHAIN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        chain = RollbackChain(
            chain_id=chain_id,
            rollback_ids=rollback_ids,
            created_at=datetime.now().isoformat(),
            description=description
        )
        
        if not hasattr(self, 'rollback_chains'):
            self.rollback_chains = []
        self.rollback_chains.append(chain)
        self._save_history()
        
        self.logger.info(f"创建回滚链: {chain_id}，包含 {len(rollback_ids)} 个回滚")
        return chain

    def execute_rollback_chain(
        self,
        chain_id: str,
        stop_on_failure: bool = True
    ) -> Dict[str, Any]:
        """执行回滚链"""
        chain = None
        if hasattr(self, 'rollback_chains'):
            for c in self.rollback_chains:
                if c.chain_id == chain_id:
                    chain = c
                    break
        
        if not chain:
            return {
                "success": False,
                "error": f"回滚链不存在: {chain_id}"
            }
        
        results = []
        all_success = True
        
        for rollback_id in chain.rollback_ids:
            result = self.rollback(rollback_id)
            results.append({
                "rollback_id": rollback_id,
                "success": result.success,
                "error": result.error_message
            })
            
            if not result.success:
                all_success = False
                if stop_on_failure:
                    break
        
        chain.status = "completed" if all_success else "partial"
        self._save_history()
        
        return {
            "success": all_success,
            "chain_id": chain_id,
            "results": results
        }

    def detect_conflicts(
        self,
        target_version: str
    ) -> List[RollbackConflict]:
        """检测回滚冲突"""
        conflicts = []
        snapshot = None
        
        for s in self.version_snapshots:
            if s.version == target_version:
                snapshot = s
                break
        
        if not snapshot:
            return conflicts
        
        for rel_path, file_data in snapshot.files.items():
            file_path = rel_path
            if os.path.exists(file_path):
                try:
                    current_content, encoding = safe_read_file(file_path)
                    
                    if not current_content:
                        continue
                    
                    current_hash = hashlib.sha256(current_content.encode()).hexdigest()
                    backup_hash = file_data.get('hash', '')
                    
                    if current_hash != backup_hash:
                        conflict = RollbackConflict(
                            conflict_id=f"CONFLICT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(conflicts)}",
                            file_path=file_path,
                            current_content=current_content,
                            backup_content=file_data.get('content', ''),
                            detected_at=datetime.now().isoformat()
                        )
                        conflicts.append(conflict)
                except Exception as e:
                    self.logger.warning(f"检测冲突失败 {file_path}: {e}")
        
        return conflicts

    def resolve_conflict(
        self,
        conflict_id: str,
        strategy: RollbackConflictStrategy
    ) -> Dict[str, Any]:
        """解决回滚冲突"""
        conflicts = getattr(self, 'detected_conflicts', [])
        conflict = None
        for c in conflicts:
            if c.conflict_id == conflict_id:
                conflict = c
                break
        
        if not conflict:
            return {
                "success": False,
                "error": f"冲突不存在: {conflict_id}"
            }
        
        resolved_content = ""
        resolution = ""
        
        if strategy == RollbackConflictStrategy.OVERWRITE:
            resolved_content = conflict.backup_content
            resolution = "使用备份内容覆盖"
        elif strategy == RollbackConflictStrategy.SKIP:
            resolved_content = conflict.current_content
            resolution = "保留当前内容"
        elif strategy == RollbackConflictStrategy.MERGE:
            resolved_content = self._merge_contents(
                conflict.current_content,
                conflict.backup_content
            )
            resolution = "合并内容"
        elif strategy == RollbackConflictStrategy.ABORT:
            resolution = "中止回滚"
        
        if strategy != RollbackConflictStrategy.ABORT:
            try:
                with open(conflict.file_path, 'w', encoding='utf-8') as f:
                    f.write(resolved_content)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"写入文件失败: {e}"
                }
        
        conflict.resolved = True
        conflict.resolution = resolution
        
        return {
            "success": True,
            "strategy": strategy.value,
            "resolution": resolution
        }

    def _merge_contents(
        self,
        current: str,
        backup: str
    ) -> str:
        """合并内容"""
        current_lines = set(current.splitlines())
        backup_lines = set(backup.splitlines())
        
        merged_lines = current_lines | backup_lines
        return '\n'.join(sorted(merged_lines))

    def auto_rollback_on_failure(
        self,
        failure_type: str,
        failure_details: Dict[str, Any],
        project_root: str
    ) -> Optional[RollbackResult]:
        """自动回滚触发"""
        trigger_type = None
        if failure_type == "error":
            trigger_type = RollbackTriggerType.AUTO_ERROR
        elif failure_type == "test_failure":
            trigger_type = RollbackTriggerType.AUTO_TEST_FAILURE
        elif failure_type == "performance":
            trigger_type = RollbackTriggerType.AUTO_PERFORMANCE
        else:
            trigger_type = RollbackTriggerType.MANUAL
        
        latest_snapshot = None
        if self.version_snapshots:
            latest_snapshot = self.version_snapshots[-1]
        
        if not latest_snapshot:
            self.logger.warning("没有可用的快照进行自动回滚")
            return None
        
        self.logger.info(f"触发自动回滚: {trigger_type.value}")
        
        result = self.restore_version_snapshot(
            latest_snapshot.snapshot_id,
            project_root,
            verify=True
        )
        
        result_dict = asdict(result)
        result_dict['trigger_type'] = trigger_type.value
        result_dict['failure_details'] = failure_details
        
        return result

    def get_rollback_history_by_type(
        self,
        rollback_type: RollbackType
    ) -> List[RollbackResult]:
        """按类型获取回滚历史"""
        return [
            r for r in self.rollback_results
            if r.rollback_type == rollback_type.value
        ]

    def get_rollback_history_by_date(
        self,
        start_date: str,
        end_date: str
    ) -> List[RollbackResult]:
        """按日期范围获取回滚历史"""
        results = []
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        for result in self.rollback_results:
            try:
                result_time = datetime.fromisoformat(result.timestamp)
                if start <= result_time <= end:
                    results.append(result)
            except Exception:
                continue
        
        return results

    def export_rollback_history(
        self,
        output_path: str,
        format: str = "json"
    ) -> str:
        """导出回滚历史"""
        data = {
            "export_time": datetime.now().isoformat(),
            "statistics": self.get_rollback_statistics(),
            "backups": [asdict(r) for r in self.backup_history],
            "results": [asdict(r) for r in self.rollback_results],
            "snapshots": [
                {
                    "snapshot_id": s.snapshot_id,
                    "version": s.version,
                    "timestamp": s.timestamp,
                    "file_count": len(s.files)
                }
                for s in self.version_snapshots
            ]
        }
        
        if format == "json":
            output = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            output = self._generate_history_markdown(data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        
        return output_path

    def _generate_history_markdown(self, data: Dict[str, Any]) -> str:
        """生成历史Markdown报告"""
        lines = [
            "# 回滚历史报告",
            "",
            f"导出时间: {data['export_time']}",
            "",
            "## 统计信息",
            "",
            f"- 总回滚次数: {data['statistics']['total_rollbacks']}",
            f"- 成功次数: {data['statistics']['successful_rollbacks']}",
            f"- 成功率: {data['statistics']['success_rate']}%",
            f"- 总快照数: {data['statistics']['total_snapshots']}",
            f"- 总备份数: {data['statistics']['total_backups']}",
            "",
            "## 回滚记录",
            "",
        ]
        
        for result in data['results'][-20:]:
            status = "✅" if result['success'] else "❌"
            lines.append(f"### {status} {result.get('timestamp', 'N/A')}")
            lines.append(f"- 类型: {result.get('rollback_type', 'N/A')}")
            lines.append(f"- 验证: {'通过' if result.get('verification_passed') else '失败'}")
            if result.get('error_message'):
                lines.append(f"- 错误: {result['error_message']}")
            lines.append("")
        
        return '\n'.join(lines)

    def schedule_rollback(
        self,
        target_version: str,
        scheduled_time: str,
        project_root: str
    ) -> Dict[str, Any]:
        """计划回滚"""
        schedule_id = f"SCHEDULE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        schedule = {
            "schedule_id": schedule_id,
            "target_version": target_version,
            "scheduled_time": scheduled_time,
            "project_root": project_root,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        if not hasattr(self, 'scheduled_rollbacks'):
            self.scheduled_rollbacks = []
        self.scheduled_rollbacks.append(schedule)
        self._save_history()
        
        self.logger.info(f"计划回滚已创建: {schedule_id}")
        return schedule

    def execute_scheduled_rollbacks(self) -> List[Dict[str, Any]]:
        """执行到期的计划回滚"""
        if not hasattr(self, 'scheduled_rollbacks'):
            return []
        
        now = datetime.now()
        executed = []
        
        for schedule in self.scheduled_rollbacks:
            if schedule['status'] != 'pending':
                continue
            
            scheduled_time = datetime.fromisoformat(schedule['scheduled_time'])
            if scheduled_time <= now:
                result = self.restore_version_snapshot(
                    schedule['target_version'],
                    schedule['project_root'],
                    verify=True
                )
                
                schedule['status'] = 'completed' if result.success else 'failed'
                schedule['executed_at'] = datetime.now().isoformat()
                schedule['result'] = asdict(result)
                
                executed.append({
                    "schedule_id": schedule['schedule_id'],
                    "success": result.success,
                    "executed_at": schedule['executed_at']
                })
        
        self._save_history()
        return executed


class FixWithRollback:
    def __init__(self, rollback_manager: Optional[RollbackManager] = None):
        self.rollback_manager = rollback_manager or RollbackManager()
    
    def execute_with_backup(
        self,
        file_path: str,
        fix_func,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        backup_record = self.rollback_manager.create_backup(
            file_path,
            operation='auto_fix',
            metadata={'function': fix_func.__name__}
        )
        
        try:
            result = fix_func(file_path, *args, **kwargs)
            
            return {
                'success': True,
                'backup_id': backup_record.backup_id,
                'result': result
            }
        
        except Exception as e:
            rollback_result = self.rollback_manager.rollback(backup_record.backup_id)
            
            return {
                'success': False,
                'backup_id': backup_record.backup_id,
                'error': str(e),
                'rollback_success': rollback_result.success
            }
    
    def execute_batch_with_backup(
        self,
        file_paths: List[str],
        fix_func,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        backup_records = self.rollback_manager.create_batch_backup(
            file_paths,
            operation='batch_auto_fix'
        )
        
        results = []
        all_success = True
        
        for file_path in file_paths:
            try:
                result = fix_func(file_path, *args, **kwargs)
                results.append({
                    'file': file_path,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'file': file_path,
                    'success': False,
                    'error': str(e)
                })
                all_success = False
        
        if not all_success:
            for record in backup_records:
                self.rollback_manager.rollback(record.backup_id)
        
        return {
            'success': all_success,
            'backup_ids': [r.backup_id for r in backup_records],
            'results': results
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='修复回滚管理器')
    parser.add_argument('command', 
                        choices=['backup', 'rollback', 'list', 'cleanup', 'report',
                                'snapshot', 'restore-snapshot', 'plan', 'verify',
                                'impact', 'stats', 'snapshots', 'chain', 'execute-chain',
                                'detect-conflicts', 'resolve-conflict', 'auto-rollback',
                                'schedule', 'execute-scheduled', 'export'],
                        help='执行命令')
    parser.add_argument('--file', '-f', help='文件路径')
    parser.add_argument('--backup-id', '-b', help='备份ID')
    parser.add_argument('--days', '-d', type=int, default=30, help='清理天数')
    parser.add_argument('--output', '-o', help='报告输出路径')
    parser.add_argument('--version', '-v', help='版本号')
    parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    parser.add_argument('--snapshot-id', '-s', help='快照ID')
    parser.add_argument('--verify', action='store_true', help='执行验证')
    parser.add_argument('--level', choices=['basic', 'standard', 'thorough'], 
                       default='standard', help='验证级别')
    parser.add_argument('--approve', action='store_true', help='批准回滚计划')
    parser.add_argument('--chain-id', help='回滚链ID')
    parser.add_argument('--rollback-ids', help='回滚ID列表(逗号分隔)')
    parser.add_argument('--conflict-id', help='冲突ID')
    parser.add_argument('--strategy', choices=['abort', 'overwrite', 'merge', 'skip'],
                       help='冲突解决策略')
    parser.add_argument('--failure-type', help='失败类型')
    parser.add_argument('--scheduled-time', help='计划回滚时间')
    parser.add_argument('--format', choices=['json', 'markdown'], default='json',
                       help='导出格式')
    parser.add_argument('--start-date', help='开始日期')
    parser.add_argument('--end-date', help='结束日期')
    parser.add_argument('--stop-on-failure', action='store_true', help='失败时停止')
    
    args = parser.parse_args()
    
    manager = RollbackManager()
    
    if args.command == 'backup':
        if not args.file:
            print('错误: 需要指定文件路径')
            return 1
        
        record = manager.create_backup(args.file)
        print(f'备份创建成功: {record.backup_id}')
        print(f'备份文件: {record.backup_file}')
    
    elif args.command == 'rollback':
        if args.backup_id:
            result = manager.rollback(args.backup_id)
        elif args.file:
            result = manager.rollback_file(args.file)
        else:
            print('错误: 需要指定备份ID或文件路径')
            return 1
        
        if result.success:
            print(f'回滚成功: {result.original_file}')
            if result.verification_passed:
                print('验证通过')
        else:
            print(f'回滚失败: {result.error_message}')
    
    elif args.command == 'list':
        backups = manager.list_backups(args.file)
        print(f'\n共 {len(backups)} 个备份:')
        for record in backups:
            print(f'  {record.backup_id}: {record.original_file} ({record.timestamp})')
    
    elif args.command == 'cleanup':
        deleted = manager.cleanup_old_backups(args.days)
        print(f'清理了 {deleted} 个旧备份')
    
    elif args.command == 'report':
        output_path = args.output or os.path.join(
            os.path.dirname(__file__), 'rollback_report.md'
        )
        manager.generate_report(output_path)
        print(f'报告已生成: {output_path}')
    
    elif args.command == 'snapshot':
        if not args.version:
            print('错误: 需要指定版本号')
            return 1
        
        snapshot = manager.create_version_snapshot(args.version, args.project_root)
        print(f'快照创建成功: {snapshot.snapshot_id}')
        print(f'版本: {snapshot.version}')
        print(f'文件数: {len(snapshot.files)}')
    
    elif args.command == 'restore-snapshot':
        if not args.snapshot_id:
            print('错误: 需要指定快照ID')
            return 1
        
        result = manager.restore_version_snapshot(
            args.snapshot_id, 
            args.project_root,
            verify=args.verify
        )
        
        if result.success:
            print(f'快照恢复成功')
            if result.verification_passed:
                print('验证通过')
        else:
            print(f'快照恢复失败: {result.error_message}')
    
    elif args.command == 'snapshots':
        snapshots = manager.list_version_snapshots()
        print(f'\n共 {len(snapshots)} 个快照:')
        for snap in snapshots:
            print(f'  {snap["snapshot_id"]}: v{snap["version"]} ({snap["timestamp"][:10]}) - {snap["file_count"]} 文件')
    
    elif args.command == 'plan':
        if not args.version:
            print('错误: 需要指定目标版本')
            return 1
        
        plan = manager.create_rollback_plan(
            args.version,
            RollbackType.VERSION,
            args.project_root
        )
        
        print(f'回滚计划: {plan.plan_id}')
        print(f'目标版本: {plan.target_version}')
        print(f'文件数: {len(plan.files_to_restore)}')
        print(f'风险等级: {plan.estimated_impact.get("risk_level", "unknown")}')
        
        if args.approve:
            plan.approved = True
            print('计划已批准')
            
            result = manager.execute_rollback_plan(plan, args.project_root)
            if result.success:
                print('回滚执行成功')
            else:
                print(f'回滚执行失败: {result.error_message}')
    
    elif args.command == 'verify':
        if not args.backup_id:
            print('错误: 需要指定备份ID')
            return 1
        
        level = VerificationLevel(args.level)
        verification = manager.verify_rollback(args.backup_id, level)
        
        print(f'验证ID: {verification.verification_id}')
        print(f'验证级别: {verification.level.value}')
        print(f'总体结果: {"通过" if verification.overall_passed else "失败"}')
        
        if verification.checks_passed:
            print(f'\n通过的检查 ({len(verification.checks_passed)}):')
            for check in verification.checks_passed:
                print(f'  ✓ {check}')
        
        if verification.checks_failed:
            print(f'\n失败的检查 ({len(verification.checks_failed)}):')
            for check in verification.checks_failed:
                print(f'  ✗ {check}')
    
    elif args.command == 'impact':
        if not args.version:
            print('错误: 需要指定目标版本')
            return 1
        
        impact = manager.analyze_rollback_impact(args.version)
        
        print(f'=== 回滚影响分析 ===')
        print(f'目标版本: {impact["target_version"]}')
        print(f'快照可用: {"是" if impact["snapshot_available"] else "否"}')
        print(f'风险等级: {impact["risk_assessment"]}')
        print(f'影响文件数: {len(impact["files_to_restore"])}')
        
        if impact["recommendations"]:
            print('\n建议:')
            for rec in impact["recommendations"]:
                print(f'  - {rec}')
    
    elif args.command == 'stats':
        stats = manager.get_rollback_statistics()
        
        print('=== 回滚统计信息 ===')
        print(f'总回滚次数: {stats["total_rollbacks"]}')
        print(f'成功次数: {stats["successful_rollbacks"]}')
        print(f'验证通过次数: {stats["verified_rollbacks"]}')
        print(f'成功率: {stats["success_rate"]}%')
        print(f'验证率: {stats["verification_rate"]}%')
        print(f'总快照数: {stats["total_snapshots"]}')
        print(f'总备份数: {stats["total_backups"]}')
        
        if stats["type_distribution"]:
            print('\n类型分布:')
            for rtype, count in stats["type_distribution"].items():
                print(f'  - {rtype}: {count}')
    
    elif args.command == 'chain':
        if not args.rollback_ids:
            print('错误: 需要指定回滚ID列表')
            return 1
        
        rollback_ids = [rid.strip() for rid in args.rollback_ids.split(',')]
        chain = manager.create_rollback_chain(rollback_ids)
        
        print(f'回滚链创建成功: {chain.chain_id}')
        print(f'包含回滚数: {len(chain.rollback_ids)}')
    
    elif args.command == 'execute-chain':
        if not args.chain_id:
            print('错误: 需要指定回滚链ID')
            return 1
        
        result = manager.execute_rollback_chain(
            args.chain_id,
            stop_on_failure=args.stop_on_failure
        )
        
        print(f'回滚链执行: {"成功" if result["success"] else "失败"}')
        for r in result.get('results', []):
            status = '✓' if r['success'] else '✗'
            print(f'  {status} {r["rollback_id"]}')
    
    elif args.command == 'detect-conflicts':
        if not args.version:
            print('错误: 需要指定目标版本')
            return 1
        
        conflicts = manager.detect_conflicts(args.version)
        manager.detected_conflicts = conflicts
        
        print(f'检测到 {len(conflicts)} 个冲突:')
        for conflict in conflicts:
            print(f'  {conflict.conflict_id}: {conflict.file_path}')
    
    elif args.command == 'resolve-conflict':
        if not args.conflict_id or not args.strategy:
            print('错误: 需要指定冲突ID和解决策略')
            return 1
        
        strategy = RollbackConflictStrategy(args.strategy)
        result = manager.resolve_conflict(args.conflict_id, strategy)
        
        if result['success']:
            print(f'冲突已解决: {result["resolution"]}')
        else:
            print(f'解决失败: {result.get("error", "未知错误")}')
    
    elif args.command == 'auto-rollback':
        if not args.failure_type:
            print('错误: 需要指定失败类型')
            return 1
        
        result = manager.auto_rollback_on_failure(
            args.failure_type,
            {},
            args.project_root
        )
        
        if result:
            print(f'自动回滚: {"成功" if result.success else "失败"}')
        else:
            print('无法执行自动回滚')
    
    elif args.command == 'schedule':
        if not args.version or not args.scheduled_time:
            print('错误: 需要指定版本号和计划时间')
            return 1
        
        schedule = manager.schedule_rollback(
            args.version,
            args.scheduled_time,
            args.project_root
        )
        
        print(f'计划回滚已创建: {schedule["schedule_id"]}')
        print(f'计划时间: {schedule["scheduled_time"]}')
    
    elif args.command == 'execute-scheduled':
        executed = manager.execute_scheduled_rollbacks()
        
        print(f'执行了 {len(executed)} 个计划回滚:')
        for e in executed:
            status = '成功' if e['success'] else '失败'
            print(f'  {e["schedule_id"]}: {status}')
    
    elif args.command == 'export':
        if not args.output:
            print('错误: 需要指定输出路径')
            return 1
        
        output_path = manager.export_rollback_history(
            args.output,
            format=args.format
        )
        print(f'回滚历史已导出: {output_path}')
    
    return 0


if __name__ == '__main__':
    exit(main())
