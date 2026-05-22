#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复执行器 - Fix Executor

增强的修复执行能力，包括：
- 修复预览功能
- 修复回滚机制
- 修复效果验证
- 修复历史记录

使用示例:
    executor = FixExecutor()
    preview = executor.preview_fix(file_path, issues)
    result = executor.execute_fix(file_path, issues)
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import hashlib
import difflib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import defaultdict

from .issue_detector import Issue, IssueCategory, IssueSeverity, DetectionResult
from .fix_strategy import FixResult, FixStatus

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"


class VerificationStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FixPreview:
    preview_id: str
    file_path: str
    original_content: str
    modified_content: str
    diff: str
    changes: List[Dict[str, Any]]
    risk_level: RiskLevel
    confidence: float
    can_auto_apply: bool
    issues_addressed: List[str]
    warnings: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preview_id": self.preview_id,
            "file_path": self.file_path,
            "diff": self.diff,
            "changes": self.changes,
            "risk_level": self.risk_level.value,
            "confidence": self.confidence,
            "can_auto_apply": self.can_auto_apply,
            "issues_addressed": self.issues_addressed,
            "warnings": self.warnings,
            "created_at": self.created_at
        }


@dataclass
class BackupRecord:
    backup_id: str
    file_path: str
    backup_path: str
    content_hash: str
    created_at: str
    fix_id: str
    file_size: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "file_path": self.file_path,
            "backup_path": self.backup_path,
            "content_hash": self.content_hash,
            "created_at": self.created_at,
            "fix_id": self.fix_id,
            "file_size": self.file_size,
            "metadata": self.metadata
        }


@dataclass
class VerificationResult:
    verification_id: str
    file_path: str
    status: VerificationStatus
    syntax_valid: bool
    tests_passed: Optional[bool]
    quality_score: float
    issues_found: List[str]
    metrics: Dict[str, Any]
    execution_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "file_path": self.file_path,
            "status": self.status.value,
            "syntax_valid": self.syntax_valid,
            "tests_passed": self.tests_passed,
            "quality_score": self.quality_score,
            "issues_found": self.issues_found,
            "metrics": self.metrics,
            "execution_time_ms": self.execution_time_ms
        }


@dataclass
class FixRecord:
    fix_id: str
    file_path: str
    status: ExecutionStatus
    issues_fixed: List[str]
    issues_failed: List[str]
    backup_id: Optional[str]
    verification_result: Optional[VerificationResult]
    execution_time_ms: float
    applied_at: str
    rolled_back: bool = False
    rollback_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fix_id": self.fix_id,
            "file_path": self.file_path,
            "status": self.status.value,
            "issues_fixed": self.issues_fixed,
            "issues_failed": self.issues_failed,
            "backup_id": self.backup_id,
            "verification_result": self.verification_result.to_dict() if self.verification_result else None,
            "execution_time_ms": self.execution_time_ms,
            "applied_at": self.applied_at,
            "rolled_back": self.rolled_back,
            "rollback_at": self.rollback_at,
            "metadata": self.metadata
        }


@dataclass
class FixHistory:
    history_id: str
    file_path: str
    total_fixes: int
    successful_fixes: int
    failed_fixes: int
    rolled_back_fixes: int
    first_fix_at: Optional[str]
    last_fix_at: Optional[str]
    records: List[FixRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "history_id": self.history_id,
            "file_path": self.file_path,
            "total_fixes": self.total_fixes,
            "successful_fixes": self.successful_fixes,
            "failed_fixes": self.failed_fixes,
            "rolled_back_fixes": self.rolled_back_fixes,
            "first_fix_at": self.first_fix_at,
            "last_fix_at": self.last_fix_at,
            "records": [r.to_dict() for r in self.records]
        }


@dataclass
class ExecutionResult:
    result_id: str
    file_path: str
    status: ExecutionStatus
    preview: Optional[FixPreview]
    fix_record: Optional[FixRecord]
    issues_detected: int
    issues_fixed: int
    issues_failed: int
    total_time_ms: float
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "file_path": self.file_path,
            "status": self.status.value,
            "preview": self.preview.to_dict() if self.preview else None,
            "fix_record": self.fix_record.to_dict() if self.fix_record else None,
            "issues_detected": self.issues_detected,
            "issues_fixed": self.issues_fixed,
            "issues_failed": self.issues_failed,
            "total_time_ms": self.total_time_ms,
            "message": self.message,
            "metadata": self.metadata
        }


class RollbackManager:
    """回滚管理器"""

    def __init__(self, backup_dir: Optional[Path] = None, max_backups: int = 100, retention_days: int = 30):
        self.backup_dir = backup_dir or Path.cwd() / ".fix_backups"
        self.max_backups = max_backups
        self.retention_days = retention_days
        self._backup_counter = 0
        self._backups: Dict[str, BackupRecord] = {}
        self._rollback_history: List[Dict[str, Any]] = []
        
        self._ensure_backup_dir()
        self._load_existing_backups()

    def _ensure_backup_dir(self) -> None:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        (self.backup_dir / "metadata").mkdir(exist_ok=True)
        (self.backup_dir / "snapshots").mkdir(exist_ok=True)

    def _load_existing_backups(self) -> None:
        metadata_dir = self.backup_dir / "metadata"
        for meta_file in metadata_dir.glob("*.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                backup = BackupRecord(
                    backup_id=data["backup_id"],
                    file_path=data["file_path"],
                    backup_path=data["backup_path"],
                    content_hash=data["content_hash"],
                    created_at=data["created_at"],
                    fix_id=data["fix_id"],
                    file_size=data["file_size"],
                    metadata=data.get("metadata", {})
                )
                self._backups[backup.backup_id] = backup
            except Exception as e:
                logger.error(f"加载备份元数据失败: {meta_file}, {e}")

    def create_backup(self, file_path: str, fix_id: str) -> Optional[BackupRecord]:
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"文件不存在: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self._backup_counter += 1
            backup_id = f"BACKUP_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._backup_counter:04d}"
            
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            
            backup_filename = f"{backup_id}_{path.stem}.bak"
            backup_path = self.backup_dir / backup_filename
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            snapshot_path = self._create_snapshot(file_path, content, backup_id)
            
            backup = BackupRecord(
                backup_id=backup_id,
                file_path=str(path.absolute()),
                backup_path=str(backup_path),
                content_hash=content_hash,
                created_at=datetime.now().isoformat(),
                fix_id=fix_id,
                file_size=len(content),
                metadata={
                    "original_filename": path.name,
                    "snapshot_path": str(snapshot_path) if snapshot_path else None
                }
            )
            
            self._backups[backup_id] = backup
            self._save_backup_metadata(backup)
            self._cleanup_old_backups()
            
            logger.info(f"创建备份成功: {backup_id}")
            return backup
        
        except Exception as e:
            logger.error(f"创建备份失败: {file_path}, {e}")
            return None

    def _create_snapshot(self, file_path: str, content: str, backup_id: str) -> Optional[Path]:
        try:
            snapshot_dir = self.backup_dir / "snapshots"
            snapshot_filename = f"{backup_id}_snapshot.json"
            snapshot_path = snapshot_dir / snapshot_filename
            
            snapshot_data = {
                "backup_id": backup_id,
                "file_path": file_path,
                "content": content,
                "created_at": datetime.now().isoformat(),
                "file_stats": {
                    "size": len(content),
                    "lines": len(content.split('\n')),
                    "hash": hashlib.sha256(content.encode()).hexdigest()
                }
            }
            
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
            
            return snapshot_path
        except Exception as e:
            logger.error(f"创建快照失败: {e}")
            return None

    def _save_backup_metadata(self, backup: BackupRecord) -> None:
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
            
            if file_path.exists():
                pre_rollback_backup = self._create_pre_rollback_backup(str(file_path), backup_id)
            
            if not file_path.parent.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._record_rollback(backup_id, backup.file_path, success=True)
            
            logger.info(f"恢复备份成功: {backup_id} -> {backup.file_path}")
            return True, f"成功恢复到 {backup.file_path}"
        
        except Exception as e:
            self._record_rollback(backup_id, backup.file_path, success=False, error=str(e))
            logger.error(f"恢复备份失败: {backup_id}, {e}")
            return False, str(e)

    def _create_pre_rollback_backup(self, file_path: str, target_backup_id: str) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            pre_rollback_id = f"PRE_ROLLBACK_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            backup_path = self.backup_dir / f"{pre_rollback_id}.bak"
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"创建回滚前备份: {pre_rollback_id}")
            return pre_rollback_id
        except Exception as e:
            logger.error(f"创建回滚前备份失败: {e}")
            return None

    def _record_rollback(self, backup_id: str, file_path: str, success: bool, error: str = "") -> None:
        record = {
            "timestamp": datetime.now().isoformat(),
            "backup_id": backup_id,
            "file_path": file_path,
            "success": success,
            "error": error
        }
        self._rollback_history.append(record)
        self._save_rollback_history()

    def _save_rollback_history(self) -> None:
        try:
            history_path = self.backup_dir / "rollback_history.json"
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(self._rollback_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存回滚历史失败: {e}")

    def get_backup(self, backup_id: str) -> Optional[BackupRecord]:
        return self._backups.get(backup_id)

    def get_backups_for_file(self, file_path: str) -> List[BackupRecord]:
        return [b for b in self._backups.values() if b.file_path == file_path]

    def get_latest_backup(self, file_path: str) -> Optional[BackupRecord]:
        backups = self.get_backups_for_file(file_path)
        if not backups:
            return None
        return max(backups, key=lambda b: b.created_at)

    def multi_rollback(self, backup_ids: List[str]) -> Dict[str, Tuple[bool, str]]:
        results = {}
        
        sorted_ids = sorted(
            backup_ids,
            key=lambda bid: self._backups.get(bid, BackupRecord("", "", "", "", "", "", 0)).created_at,
            reverse=True
        )
        
        for backup_id in sorted_ids:
            success, message = self.restore_backup(backup_id)
            results[backup_id] = (success, message)
        
        return results

    def verify_backup(self, backup_id: str) -> Tuple[bool, str]:
        if backup_id not in self._backups:
            return False, f"备份不存在: {backup_id}"
        
        backup = self._backups[backup_id]
        
        try:
            backup_path = Path(backup.backup_path)
            if not backup_path.exists():
                return False, f"备份文件不存在: {backup.backup_path}"
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            current_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            
            if current_hash != backup.content_hash:
                return False, f"备份内容哈希不匹配: 期望 {backup.content_hash}, 实际 {current_hash}"
            
            try:
                ast.parse(content)
            except SyntaxError as e:
                return False, f"备份内容存在语法错误: {e}"
            
            return True, "备份验证通过"
        
        except Exception as e:
            return False, f"验证备份失败: {e}"

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
            sorted_backups = sorted(self._backups.values(), key=lambda b: b.created_at)
            to_delete = sorted_backups[:len(self._backups) - self.max_backups]
            for backup in to_delete:
                if self.delete_backup(backup.backup_id):
                    cleaned += 1
        
        if cleaned > 0:
            logger.info(f"清理了 {cleaned} 个过期备份")
        
        return cleaned

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
            
            snapshot_path = backup.metadata.get("snapshot_path")
            if snapshot_path:
                snapshot_file = Path(snapshot_path)
                if snapshot_file.exists():
                    snapshot_file.unlink()
            
            del self._backups[backup_id]
            logger.info(f"删除备份成功: {backup_id}")
            return True
        
        except Exception as e:
            logger.error(f"删除备份失败: {backup_id}, {e}")
            return False

    def get_rollback_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._rollback_history[-limit:]

    def create_checkpoint(self, file_path: str, checkpoint_name: str) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            checkpoint_id = f"CHECKPOINT_{checkpoint_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            checkpoint_path = self.backup_dir / f"{checkpoint_id}.checkpoint"
            
            checkpoint_data = {
                "checkpoint_id": checkpoint_id,
                "checkpoint_name": checkpoint_name,
                "file_path": file_path,
                "content": content,
                "created_at": datetime.now().isoformat()
            }
            
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"创建检查点成功: {checkpoint_id}")
            return checkpoint_id
        except Exception as e:
            logger.error(f"创建检查点失败: {e}")
            return None

    def restore_checkpoint(self, checkpoint_id: str) -> Tuple[bool, str]:
        try:
            checkpoint_path = self.backup_dir / f"{checkpoint_id}.checkpoint"
            
            if not checkpoint_path.exists():
                return False, f"检查点不存在: {checkpoint_id}"
            
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            file_path = checkpoint_data["file_path"]
            content = checkpoint_data["content"]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"恢复检查点成功: {checkpoint_id}")
            return True, f"成功恢复检查点 {checkpoint_id}"
        except Exception as e:
            logger.error(f"恢复检查点失败: {e}")
            return False, str(e)


class FixVerifier:
    """修复验证器"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self._verification_counter = 0

    def verify(self, file_path: str, original_content: str, modified_content: str) -> VerificationResult:
        start_time = time.perf_counter()
        self._verification_counter += 1
        
        syntax_valid = self._check_syntax(modified_content)
        quality_score = self._calculate_quality_score(original_content, modified_content)
        issues_found = []
        
        if not syntax_valid:
            issues_found.append("修复后存在语法错误")
        
        additional_checks = self._run_additional_checks(file_path, modified_content)
        issues_found.extend(additional_checks['issues'])
        
        status = VerificationStatus.PASSED if syntax_valid and quality_score >= 0.7 and len(issues_found) == 0 else (
            VerificationStatus.WARNING if syntax_valid and len(issues_found) < 3 else VerificationStatus.FAILED
        )
        
        execution_time = (time.perf_counter() - start_time) * 1000
        
        return VerificationResult(
            verification_id=f"VERIFY_{self._verification_counter:04d}",
            file_path=file_path,
            status=status,
            syntax_valid=syntax_valid,
            tests_passed=additional_checks.get('tests_passed'),
            quality_score=quality_score,
            issues_found=issues_found,
            metrics={
                "original_lines": len(original_content.split('\n')),
                "modified_lines": len(modified_content.split('\n')),
                "change_ratio": self._calculate_change_ratio(original_content, modified_content),
                "complexity_change": self._calculate_complexity_change(original_content, modified_content),
                "maintainability_score": additional_checks.get('maintainability_score', 0.8)
            },
            execution_time_ms=execution_time
        )

    def _check_syntax(self, content: str) -> bool:
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            return False

    def _calculate_quality_score(self, original: str, modified: str) -> float:
        score = 1.0
        
        original_lines = original.split('\n')
        modified_lines = modified.split('\n')
        
        change_ratio = abs(len(modified_lines) - len(original_lines)) / max(len(original_lines), 1)
        if change_ratio > 0.5:
            score -= 0.2
        
        diff_ratio = difflib.SequenceMatcher(None, original_lines, modified_lines).ratio()
        if diff_ratio < 0.5:
            score -= 0.3
        
        if modified:
            try:
                tree = ast.parse(modified)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if not ast.get_docstring(node):
                            score -= 0.05
            except:
                pass
        
        return max(0, score)

    def _calculate_change_ratio(self, original: str, modified: str) -> float:
        original_lines = set(original.split('\n'))
        modified_lines = set(modified.split('\n'))
        
        if not original_lines:
            return 1.0 if modified_lines else 0.0
        
        common = original_lines & modified_lines
        return 1 - (len(common) / len(original_lines))

    def _run_additional_checks(self, file_path: str, content: str) -> Dict[str, Any]:
        result = {
            'issues': [],
            'tests_passed': None,
            'maintainability_score': 0.8
        }
        
        issues = []
        issues.extend(self._check_import_consistency(content))
        issues.extend(self._check_code_style(content))
        issues.extend(self._check_security_patterns(content))
        
        result['issues'] = issues
        
        if self._is_test_file(file_path):
            result['tests_passed'] = self._run_tests(file_path)
        
        result['maintainability_score'] = self._calculate_maintainability(content)
        
        return result

    def _check_import_consistency(self, content: str) -> List[str]:
        issues = []
        
        try:
            tree = ast.parse(content)
        except:
            return issues
        
        imports = set()
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.asname or alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
                for alias in node.names:
                    imports.add(alias.asname or alias.name)
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
        
        unused = imports - used_names - {'__future__', '__all__'}
        if unused:
            issues.append(f"可能存在未使用的导入: {', '.join(unused)}")
        
        return issues

    def _check_code_style(self, content: str) -> List[str]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(f"行 {i} 超过120字符")
            
            if '\t' in line:
                issues.append(f"行 {i} 使用了制表符")
        
        return issues[:5]

    def _check_security_patterns(self, content: str) -> List[str]:
        issues = []
        
        dangerous_patterns = [
            (r'eval\s*\(', '使用eval函数可能存在安全风险'),
            (r'exec\s*\(', '使用exec函数可能存在安全风险'),
            (r'password\s*=\s*["\'][^"\']+["\']', '硬编码密码'),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, content):
                issues.append(message)
        
        return issues

    def _is_test_file(self, file_path: str) -> bool:
        return 'test' in file_path.lower() or file_path.endswith('_test.py')

    def _run_tests(self, file_path: str) -> Optional[bool]:
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', file_path, '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.project_root)
            )
            return result.returncode == 0
        except Exception:
            return None

    def _calculate_maintainability(self, content: str) -> float:
        try:
            tree = ast.parse(content)
        except:
            return 0.5
        
        score = 1.0
        
        function_count = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.FunctionDef))
        if function_count > 20:
            score -= 0.1
        
        class_count = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.ClassDef))
        if class_count > 10:
            score -= 0.1
        
        max_complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_function_complexity(node)
                max_complexity = max(max_complexity, complexity)
        
        if max_complexity > 10:
            score -= 0.2
        
        return max(0, score)

    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity

    def _calculate_complexity_change(self, original: str, modified: str) -> float:
        try:
            original_tree = ast.parse(original)
            modified_tree = ast.parse(modified)
        except:
            return 0.0
        
        original_complexity = self._calculate_total_complexity(original_tree)
        modified_complexity = self._calculate_total_complexity(modified_tree)
        
        if original_complexity == 0:
            return 0.0
        
        return (modified_complexity - original_complexity) / original_complexity

    def _calculate_total_complexity(self, tree: ast.AST) -> int:
        total = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total += self._calculate_function_complexity(node)
        return total


class FixPreviewer:
    """修复预览器"""

    def __init__(self):
        self._preview_counter = 0

    def generate_preview(
        self,
        file_path: str,
        original_content: str,
        modified_content: str,
        fix_results: List[FixResult]
    ) -> FixPreview:
        self._preview_counter += 1
        
        diff = self._generate_diff(original_content, modified_content)
        changes = self._extract_changes(fix_results)
        risk_level = self._assess_risk(changes, fix_results)
        confidence = self._calculate_confidence(fix_results)
        can_auto_apply = risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM] and confidence >= 0.7
        issues_addressed = [r.issue_id for r in fix_results if r.status == FixStatus.SUCCESS]
        warnings = []
        
        for result in fix_results:
            warnings.extend(result.warnings)
        
        return FixPreview(
            preview_id=f"PREVIEW_{self._preview_counter:04d}",
            file_path=file_path,
            original_content=original_content,
            modified_content=modified_content,
            diff=diff,
            changes=changes,
            risk_level=risk_level,
            confidence=confidence,
            can_auto_apply=can_auto_apply,
            issues_addressed=issues_addressed,
            warnings=warnings
        )

    def _generate_diff(self, original: str, modified: str) -> str:
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile='original',
            tofile='modified'
        )
        return ''.join(diff)

    def _extract_changes(self, fix_results: List[FixResult]) -> List[Dict[str, Any]]:
        changes = []
        for result in fix_results:
            if result.status in [FixStatus.SUCCESS, FixStatus.PARTIAL]:
                changes.append({
                    "line": result.line_number,
                    "strategy": result.strategy_name,
                    "message": result.message,
                    "confidence": result.confidence
                })
        return changes

    def _assess_risk(self, changes: List[Dict[str, Any]], fix_results: List[FixResult]) -> RiskLevel:
        if not changes:
            return RiskLevel.LOW
        
        if len(changes) > 10:
            return RiskLevel.HIGH
        elif len(changes) > 5:
            return RiskLevel.MEDIUM
        
        high_risk_keywords = ['password', 'secret', 'token', 'auth', 'security', 'eval', 'exec']
        for result in fix_results:
            for keyword in high_risk_keywords:
                if keyword in result.original_code.lower() or keyword in result.fixed_code.lower():
                    return RiskLevel.CRITICAL
        
        return RiskLevel.LOW

    def _calculate_confidence(self, fix_results: List[FixResult]) -> float:
        if not fix_results:
            return 0.0
        
        confidences = [r.confidence for r in fix_results]
        return sum(confidences) / len(confidences)


class FixHistoryManager:
    """修复历史管理器"""

    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or Path.cwd() / ".fix_history" / "fix_history.json"
        self._fix_counter = 0
        self._records: Dict[str, FixRecord] = {}
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
                
                for fix_id, record_data in data.get("records", {}).items():
                    verification_data = record_data.get("verification_result")
                    verification = None
                    if verification_data:
                        verification = VerificationResult(
                            verification_id=verification_data["verification_id"],
                            file_path=verification_data["file_path"],
                            status=VerificationStatus(verification_data["status"]),
                            syntax_valid=verification_data["syntax_valid"],
                            tests_passed=verification_data.get("tests_passed"),
                            quality_score=verification_data["quality_score"],
                            issues_found=verification_data["issues_found"],
                            metrics=verification_data["metrics"],
                            execution_time_ms=verification_data["execution_time_ms"]
                        )
                    
                    self._records[fix_id] = FixRecord(
                        fix_id=record_data["fix_id"],
                        file_path=record_data["file_path"],
                        status=ExecutionStatus(record_data["status"]),
                        issues_fixed=record_data["issues_fixed"],
                        issues_failed=record_data["issues_failed"],
                        backup_id=record_data.get("backup_id"),
                        verification_result=verification,
                        execution_time_ms=record_data["execution_time_ms"],
                        applied_at=record_data["applied_at"],
                        rolled_back=record_data.get("rolled_back", False),
                        rollback_at=record_data.get("rollback_at"),
                        metadata=record_data.get("metadata", {})
                    )
                
                logger.info(f"加载了 {len(self._records)} 条修复历史记录")
            except Exception as e:
                logger.error(f"加载修复历史失败: {e}")

    def _save_history(self) -> None:
        try:
            data = {
                "records": {fix_id: record.to_dict() for fix_id, record in self._records.items()},
                "last_updated": datetime.now().isoformat()
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存修复历史失败: {e}")

    def record_fix(self, fix_record: FixRecord) -> None:
        self._records[fix_record.fix_id] = fix_record
        self._update_file_history(fix_record)
        self._save_history()
        logger.info(f"记录修复: {fix_record.fix_id}")

    def _update_file_history(self, record: FixRecord) -> None:
        file_path = record.file_path
        if file_path not in self._file_histories:
            self._file_histories[file_path] = FixHistory(
                history_id=f"HIST_{file_path.replace('/', '_').replace('\\', '_')}",
                file_path=file_path,
                total_fixes=0,
                successful_fixes=0,
                failed_fixes=0,
                rolled_back_fixes=0,
                first_fix_at=record.applied_at,
                last_fix_at=record.applied_at
            )
        
        history = self._file_histories[file_path]
        history.total_fixes += 1
        history.last_fix_at = record.applied_at
        
        if record.status == ExecutionStatus.SUCCESS:
            history.successful_fixes += 1
        elif record.status == ExecutionStatus.FAILED:
            history.failed_fixes += 1
        elif record.status == ExecutionStatus.ROLLED_BACK:
            history.rolled_back_fixes += 1
        
        history.records.append(record)

    def update_rollback(self, fix_id: str) -> bool:
        if fix_id not in self._records:
            return False
        
        record = self._records[fix_id]
        record.rolled_back = True
        record.rollback_at = datetime.now().isoformat()
        record.status = ExecutionStatus.ROLLED_BACK
        
        self._save_history()
        return True

    def get_fix_record(self, fix_id: str) -> Optional[FixRecord]:
        return self._records.get(fix_id)

    def get_file_history(self, file_path: str) -> Optional[FixHistory]:
        return self._file_histories.get(file_path)

    def get_recent_fixes(self, limit: int = 10) -> List[FixRecord]:
        sorted_records = sorted(self._records.values(), key=lambda r: r.applied_at, reverse=True)
        return sorted_records[:limit]


class FixEffectEvaluator:
    """修复效果评估器"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self._evaluation_counter = 0
        self._evaluation_history: List[Dict[str, Any]] = []

    def evaluate(
        self,
        file_path: str,
        original_content: str,
        fixed_content: str,
        fix_results: List[FixResult]
    ) -> Dict[str, Any]:
        self._evaluation_counter += 1
        
        evaluation = {
            "evaluation_id": f"EVAL_{self._evaluation_counter:04d}",
            "file_path": file_path,
            "timestamp": datetime.now().isoformat(),
            "metrics": self._calculate_metrics(original_content, fixed_content, fix_results),
            "quality_improvement": self._calculate_quality_improvement(original_content, fixed_content),
            "issue_resolution": self._analyze_issue_resolution(fix_results),
            "risk_assessment": self._assess_risks(fixed_content),
            "recommendations": []
        }
        
        evaluation["overall_score"] = self._calculate_overall_score(evaluation)
        evaluation["recommendations"] = self._generate_recommendations(evaluation)
        
        self._evaluation_history.append(evaluation)
        
        return evaluation

    def _calculate_metrics(
        self,
        original: str,
        fixed: str,
        fix_results: List[FixResult]
    ) -> Dict[str, Any]:
        original_lines = original.split('\n')
        fixed_lines = fixed.split('\n')
        
        total_issues = len(fix_results)
        successful_fixes = sum(1 for r in fix_results if r.status == FixStatus.SUCCESS)
        partial_fixes = sum(1 for r in fix_results if r.status == FixStatus.PARTIAL)
        failed_fixes = sum(1 for r in fix_results if r.status == FixStatus.FAILED)
        
        avg_confidence = (
            sum(r.confidence for r in fix_results) / len(fix_results)
            if fix_results else 0.0
        )
        
        total_execution_time = sum(r.execution_time_ms for r in fix_results)
        
        return {
            "lines_changed": abs(len(fixed_lines) - len(original_lines)),
            "change_percentage": abs(len(fixed_lines) - len(original_lines)) / max(len(original_lines), 1) * 100,
            "total_issues_addressed": total_issues,
            "successful_fixes": successful_fixes,
            "partial_fixes": partial_fixes,
            "failed_fixes": failed_fixes,
            "success_rate": successful_fixes / total_issues if total_issues > 0 else 0.0,
            "average_confidence": avg_confidence,
            "total_execution_time_ms": total_execution_time,
            "strategies_used": list(set(r.strategy_name for r in fix_results))
        }

    def _calculate_quality_improvement(self, original: str, fixed: str) -> Dict[str, float]:
        improvements = {}
        
        original_score = self._calculate_code_quality_score(original)
        fixed_score = self._calculate_code_quality_score(fixed)
        
        improvements["quality_score_change"] = fixed_score - original_score
        improvements["quality_improvement_percentage"] = (
            (fixed_score - original_score) / max(original_score, 0.1) * 100
            if original_score > 0 else 0.0
        )
        
        original_complexity = self._calculate_complexity(original)
        fixed_complexity = self._calculate_complexity(fixed)
        
        improvements["complexity_change"] = fixed_complexity - original_complexity
        improvements["complexity_improvement"] = (
            (original_complexity - fixed_complexity) / max(original_complexity, 1) * 100
            if original_complexity > 0 else 0.0
        )
        
        original_maintainability = self._calculate_maintainability(original)
        fixed_maintainability = self._calculate_maintainability(fixed)
        
        improvements["maintainability_change"] = fixed_maintainability - original_maintainability
        
        return improvements

    def _calculate_code_quality_score(self, content: str) -> float:
        score = 100.0
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return 0.0
        
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    score -= 2
                
                if hasattr(node, 'end_lineno'):
                    func_lines = node.end_lineno - node.lineno
                    if func_lines > 50:
                        score -= 5
                
                param_count = len(node.args.args)
                if param_count > 5:
                    score -= 3
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    score -= 3
        
        if not ast.get_docstring(tree):
            score -= 5
        
        return max(0, score)

    def _calculate_complexity(self, content: str) -> int:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return 0
        
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity

    def _calculate_maintainability(self, content: str) -> float:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return 0.0
        
        score = 100.0
        
        function_count = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.FunctionDef))
        if function_count > 20:
            score -= (function_count - 20) * 2
        
        class_count = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.ClassDef))
        if class_count > 10:
            score -= (class_count - 10) * 3
        
        complexity = self._calculate_complexity(content)
        if complexity > 50:
            score -= (complexity - 50) * 0.5
        
        return max(0, score)

    def _analyze_issue_resolution(self, fix_results: List[FixResult]) -> Dict[str, Any]:
        by_category = defaultdict(lambda: {"total": 0, "success": 0, "partial": 0, "failed": 0})
        
        for result in fix_results:
            category = result.strategy_name
            by_category[category]["total"] += 1
            
            if result.status == FixStatus.SUCCESS:
                by_category[category]["success"] += 1
            elif result.status == FixStatus.PARTIAL:
                by_category[category]["partial"] += 1
            else:
                by_category[category]["failed"] += 1
        
        resolution_rate = {}
        for category, stats in by_category.items():
            total = stats["total"]
            if total > 0:
                resolution_rate[category] = {
                    "success_rate": stats["success"] / total,
                    "partial_rate": stats["partial"] / total,
                    "failure_rate": stats["failed"] / total
                }
        
        return {
            "by_category": dict(by_category),
            "resolution_rates": resolution_rate
        }

    def _assess_risks(self, content: str) -> Dict[str, Any]:
        risks = []
        risk_level = "low"
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return {
                "risk_level": "critical",
                "risks": [{"type": "syntax_error", "severity": "critical", "description": "代码存在语法错误"}]
            }
        
        dangerous_patterns = [
            (r'eval\s*\(', '代码注入风险', 'high'),
            (r'exec\s*\(', '代码注入风险', 'high'),
            (r'password\s*=\s*["\'][^"\']+["\']', '硬编码密码', 'medium'),
            (r'subprocess\..*shell\s*=\s*True', '命令注入风险', 'high'),
        ]
        
        for pattern, desc, severity in dangerous_patterns:
            if re.search(pattern, content):
                risks.append({
                    "type": "security",
                    "severity": severity,
                    "description": desc
                })
        
        function_count = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.FunctionDef))
        if function_count > 30:
            risks.append({
                "type": "maintainability",
                "severity": "medium",
                "description": f"文件包含过多函数 ({function_count})"
            })
        
        if risks:
            high_risks = sum(1 for r in risks if r["severity"] == "high")
            medium_risks = sum(1 for r in risks if r["severity"] == "medium")
            
            if high_risks > 0:
                risk_level = "high"
            elif medium_risks > 2:
                risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "risks": risks
        }

    def _calculate_overall_score(self, evaluation: Dict[str, Any]) -> float:
        score = 0.0
        
        metrics = evaluation["metrics"]
        score += metrics["success_rate"] * 40
        score += metrics["average_confidence"] * 30
        
        quality_improvement = evaluation["quality_improvement"]
        if quality_improvement["quality_score_change"] > 0:
            score += min(20, quality_improvement["quality_score_change"])
        
        risk_assessment = evaluation["risk_assessment"]
        if risk_assessment["risk_level"] == "low":
            score += 10
        elif risk_assessment["risk_level"] == "medium":
            score += 5
        
        return min(100, max(0, score))

    def _generate_recommendations(self, evaluation: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        metrics = evaluation["metrics"]
        if metrics["failed_fixes"] > 0:
            recommendations.append(
                f"有 {metrics['failed_fixes']} 个问题未能自动修复，建议手动检查"
            )
        
        if metrics["average_confidence"] < 0.7:
            recommendations.append("修复置信度较低，建议仔细审查所有修改")
        
        quality_improvement = evaluation["quality_improvement"]
        if quality_improvement["quality_score_change"] < 0:
            recommendations.append("修复后代码质量有所下降，建议重新评估修复策略")
        
        risk_assessment = evaluation["risk_assessment"]
        if risk_assessment["risk_level"] == "high":
            recommendations.append("检测到高风险问题，建议立即处理")
        elif risk_assessment["risk_level"] == "medium":
            recommendations.append("存在中等风险问题，建议尽快处理")
        
        if not recommendations:
            recommendations.append("修复效果良好，建议进行测试验证")
        
        return recommendations

    def get_evaluation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._evaluation_history[-limit:]

    def generate_evaluation_report(self, evaluation: Dict[str, Any]) -> str:
        lines = [
            "=" * 80,
            "修复效果评估报告",
            "=" * 80,
            f"评估ID: {evaluation['evaluation_id']}",
            f"文件路径: {evaluation['file_path']}",
            f"评估时间: {evaluation['timestamp']}",
            "",
            "-" * 80,
            "总体评分",
            "-" * 80,
            f"综合得分: {evaluation['overall_score']:.1f}/100",
            "",
            "-" * 80,
            "修复指标",
            "-" * 80,
        ]
        
        metrics = evaluation["metrics"]
        lines.append(f"处理问题数: {metrics['total_issues_addressed']}")
        lines.append(f"成功修复: {metrics['successful_fixes']}")
        lines.append(f"部分修复: {metrics['partial_fixes']}")
        lines.append(f"修复失败: {metrics['failed_fixes']}")
        lines.append(f"成功率: {metrics['success_rate']:.1%}")
        lines.append(f"平均置信度: {metrics['average_confidence']:.1%}")
        lines.append(f"执行时间: {metrics['total_execution_time_ms']:.2f}ms")
        
        lines.extend([
            "",
            "-" * 80,
            "质量改进",
            "-" * 80,
        ])
        
        quality = evaluation["quality_improvement"]
        lines.append(f"质量分数变化: {quality['quality_score_change']:+.1f}")
        lines.append(f"复杂度变化: {quality['complexity_change']:+d}")
        lines.append(f"可维护性变化: {quality['maintainability_change']:+.1f}")
        
        lines.extend([
            "",
            "-" * 80,
            "风险评估",
            "-" * 80,
            f"风险等级: {evaluation['risk_assessment']['risk_level']}",
        ])
        
        if evaluation['risk_assessment']['risks']:
            lines.append("检测到的风险:")
            for risk in evaluation['risk_assessment']['risks']:
                lines.append(f"  - [{risk['severity']}] {risk['description']}")
        
        lines.extend([
            "",
            "-" * 80,
            "建议",
            "-" * 80,
        ])
        
        for rec in evaluation["recommendations"]:
            lines.append(f"• {rec}")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


class FixExecutor:
    """修复执行器主类"""

    def __init__(self, project_root: Optional[Path] = None, backup_dir: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.rollback_manager = RollbackManager(backup_dir)
        self.verifier = FixVerifier(self.project_root)
        self.previewer = FixPreviewer()
        self.history_manager = FixHistoryManager()
        self.evaluator = FixEffectEvaluator(self.project_root)
        self._result_counter = 0

    def preview_fix(
        self,
        file_path: str,
        original_content: str,
        modified_content: str,
        fix_results: List[FixResult]
    ) -> FixPreview:
        return self.previewer.generate_preview(
            file_path=file_path,
            original_content=original_content,
            modified_content=modified_content,
            fix_results=fix_results
        )

    def execute_fix(
        self,
        file_path: str,
        modified_content: str,
        fix_results: List[FixResult],
        create_backup: bool = True,
        verify: bool = True
    ) -> ExecutionResult:
        start_time = time.perf_counter()
        self._result_counter += 1
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            return self._create_error_result(file_path, f"读取文件失败: {e}")
        
        preview = self.preview_fix(file_path, original_content, modified_content, fix_results)
        
        if not preview.can_auto_apply:
            return ExecutionResult(
                result_id=f"EXEC_{self._result_counter:04d}",
                file_path=file_path,
                status=ExecutionStatus.SKIPPED,
                preview=preview,
                fix_record=None,
                issues_detected=len(fix_results),
                issues_fixed=0,
                issues_failed=len(fix_results),
                total_time_ms=(time.perf_counter() - start_time) * 1000,
                message="修复风险过高或置信度过低，需要人工审查"
            )
        
        fix_id = f"FIX_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._result_counter:04d}"
        backup = None
        
        if create_backup:
            backup = self.rollback_manager.create_backup(file_path, fix_id)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            verification_result = None
            if verify:
                verification_result = self.verifier.verify(file_path, original_content, modified_content)
            
            issues_fixed = [r.issue_id for r in fix_results if r.status == FixStatus.SUCCESS]
            issues_failed = [r.issue_id for r in fix_results if r.status == FixStatus.FAILED]
            
            status = ExecutionStatus.SUCCESS if len(issues_failed) == 0 else ExecutionStatus.PARTIAL
            
            if verification_result and verification_result.status == VerificationStatus.FAILED:
                status = ExecutionStatus.FAILED
                if backup:
                    self.rollback_manager.restore_backup(backup.backup_id)
                    status = ExecutionStatus.ROLLED_BACK
            
            fix_record = FixRecord(
                fix_id=fix_id,
                file_path=file_path,
                status=status,
                issues_fixed=issues_fixed,
                issues_failed=issues_failed,
                backup_id=backup.backup_id if backup else None,
                verification_result=verification_result,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                applied_at=datetime.now().isoformat()
            )
            
            self.history_manager.record_fix(fix_record)
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            return ExecutionResult(
                result_id=f"EXEC_{self._result_counter:04d}",
                file_path=file_path,
                status=status,
                preview=preview,
                fix_record=fix_record,
                issues_detected=len(fix_results),
                issues_fixed=len(issues_fixed),
                issues_failed=len(issues_failed),
                total_time_ms=execution_time,
                message=self._generate_message(status, len(issues_fixed), len(issues_failed))
            )
        
        except Exception as e:
            logger.error(f"执行修复失败: {e}")
            
            if backup:
                self.rollback_manager.restore_backup(backup.backup_id)
            
            return ExecutionResult(
                result_id=f"EXEC_{self._result_counter:04d}",
                file_path=file_path,
                status=ExecutionStatus.FAILED,
                preview=preview,
                fix_record=None,
                issues_detected=len(fix_results),
                issues_fixed=0,
                issues_failed=len(fix_results),
                total_time_ms=(time.perf_counter() - start_time) * 1000,
                message=f"执行修复失败: {e}"
            )

    def rollback(self, fix_id: str) -> Tuple[bool, str]:
        fix_record = self.history_manager.get_fix_record(fix_id)
        if not fix_record:
            return False, f"修复记录不存在: {fix_id}"
        
        if not fix_record.backup_id:
            return False, f"修复没有备份: {fix_id}"
        
        success, message = self.rollback_manager.restore_backup(fix_record.backup_id)
        
        if success:
            self.history_manager.update_rollback(fix_id)
        
        return success, message

    def get_fix_history(self, file_path: str) -> Optional[FixHistory]:
        return self.history_manager.get_file_history(file_path)

    def get_recent_fixes(self, limit: int = 10) -> List[FixRecord]:
        return self.history_manager.get_recent_fixes(limit)

    def _create_error_result(self, file_path: str, error_message: str) -> ExecutionResult:
        self._result_counter += 1
        return ExecutionResult(
            result_id=f"EXEC_{self._result_counter:04d}",
            file_path=file_path,
            status=ExecutionStatus.FAILED,
            preview=None,
            fix_record=None,
            issues_detected=0,
            issues_fixed=0,
            issues_failed=0,
            total_time_ms=0,
            message=error_message
        )

    def _generate_message(self, status: ExecutionStatus, fixed: int, failed: int) -> str:
        if status == ExecutionStatus.SUCCESS:
            return f"成功修复 {fixed} 个问题"
        elif status == ExecutionStatus.PARTIAL:
            return f"部分修复成功: {fixed} 个成功, {failed} 个失败"
        elif status == ExecutionStatus.ROLLED_BACK:
            return "修复验证失败，已自动回滚"
        elif status == ExecutionStatus.FAILED:
            return f"修复失败: {failed} 个问题未能修复"
        else:
            return "修复已跳过"


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="修复执行器")
    parser.add_argument("--history", type=str, help="查看文件修复历史")
    parser.add_argument("--recent", type=int, default=10, help="查看最近N条修复记录")
    parser.add_argument("--rollback", type=str, help="回滚指定修复")
    
    args = parser.parse_args()
    
    executor = FixExecutor()
    
    if args.history:
        history = executor.get_fix_history(args.history)
        if history:
            print(f"\n文件: {history.file_path}")
            print(f"总修复次数: {history.total_fixes}")
            print(f"成功修复: {history.successful_fixes}")
            print(f"失败修复: {history.failed_fixes}")
            print(f"已回滚: {history.rolled_back_fixes}")
            print(f"\n最近修复记录:")
            for record in history.records[-5:]:
                print(f"  - {record.fix_id}: {record.status.value} ({record.applied_at})")
        else:
            print("未找到历史记录")
    
    elif args.rollback:
        success, message = executor.rollback(args.rollback)
        print(f"回滚结果: {message}")
    
    else:
        recent = executor.get_recent_fixes(args.recent)
        print(f"\n最近 {len(recent)} 条修复记录:")
        for record in recent:
            print(f"  - {record.fix_id}: {record.file_path}")
            print(f"    状态: {record.status.value}")
            print(f"    成功: {len(record.issues_fixed)}, 失败: {len(record.issues_failed)}")
            print(f"    时间: {record.applied_at}")


if __name__ == "__main__":
    main()
