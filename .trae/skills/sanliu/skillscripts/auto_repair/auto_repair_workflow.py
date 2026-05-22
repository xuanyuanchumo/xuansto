#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修复工作流 - Auto Repair Workflow

完整的自动修复工作流，包括：
- 问题检测→修复建议流程
- 修复执行→效果验证流程
- 验证失败→回滚重试流程
- 修复完成→知识积累流程

使用示例:
    workflow = AutoRepairWorkflow()
    result = workflow.repair_file("code.py")
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import defaultdict

from .issue_detector import IssueDetector, Issue, IssueCategory, IssueSeverity, DetectionResult
from .fix_strategy import FixStrategyLibrary, FixResult, FixStatus
from .fix_executor import FixExecutor, ExecutionResult, ExecutionStatus, FixPreview

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    INITIALIZATION = auto()
    DETECTION = auto()
    ANALYSIS = auto()
    FIX_GENERATION = auto()
    PREVIEW = auto()
    EXECUTION = auto()
    VERIFICATION = auto()
    ROLLBACK = auto()
    KNOWLEDGE_ACCUMULATION = auto()
    COMPLETED = auto()
    FAILED = auto()


class WorkflowStatus(Enum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowConfig:
    max_retries: int = 3
    auto_apply: bool = True
    create_backup: bool = True
    verify_fixes: bool = True
    confidence_threshold: float = 0.7
    risk_threshold: str = "medium"
    skip_categories: List[IssueCategory] = field(default_factory=list)
    priority_order: List[IssueSeverity] = field(default_factory=lambda: [
        IssueSeverity.CRITICAL,
        IssueSeverity.HIGH,
        IssueSeverity.MEDIUM,
        IssueSeverity.LOW
    ])
    parallel_detection: bool = False
    knowledge_accumulation: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_retries": self.max_retries,
            "auto_apply": self.auto_apply,
            "create_backup": self.create_backup,
            "verify_fixes": self.verify_fixes,
            "confidence_threshold": self.confidence_threshold,
            "risk_threshold": self.risk_threshold,
            "skip_categories": [c.name for c in self.skip_categories],
            "priority_order": [s.value for s in self.priority_order],
            "parallel_detection": self.parallel_detection,
            "knowledge_accumulation": self.knowledge_accumulation
        }


@dataclass
class StageResult:
    stage: WorkflowStage
    status: WorkflowStatus
    start_time: str
    end_time: str
    duration_ms: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.name,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": round(self.duration_ms, 2),
            "message": self.message,
            "details": self.details,
            "errors": self.errors
        }


@dataclass
class KnowledgeEntry:
    entry_id: str
    issue_category: IssueCategory
    issue_pattern: str
    fix_strategy: str
    success_rate: float
    applied_count: int
    last_applied: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "issue_category": self.issue_category.name,
            "issue_pattern": self.issue_pattern,
            "fix_strategy": self.fix_strategy,
            "success_rate": self.success_rate,
            "applied_count": self.applied_count,
            "last_applied": self.last_applied,
            "context": self.context
        }


@dataclass
class WorkflowResult:
    workflow_id: str
    file_path: str
    status: WorkflowStatus
    current_stage: WorkflowStage
    start_time: str
    end_time: Optional[str]
    total_duration_ms: float
    stages: List[StageResult]
    issues_detected: int
    issues_fixed: int
    issues_failed: int
    issues_skipped: int
    detection_result: Optional[DetectionResult]
    execution_result: Optional[ExecutionResult]
    preview: Optional[FixPreview]
    knowledge_entries: List[KnowledgeEntry]
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "file_path": self.file_path,
            "status": self.status.value,
            "current_stage": self.current_stage.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "stages": [s.to_dict() for s in self.stages],
            "issues_detected": self.issues_detected,
            "issues_fixed": self.issues_fixed,
            "issues_failed": self.issues_failed,
            "issues_skipped": self.issues_skipped,
            "detection_result": self.detection_result.to_dict() if self.detection_result else None,
            "execution_result": self.execution_result.to_dict() if self.execution_result else None,
            "preview": self.preview.to_dict() if self.preview else None,
            "knowledge_entries": [k.to_dict() for k in self.knowledge_entries],
            "message": self.message,
            "metadata": self.metadata
        }


class KnowledgeBase:
    """知识库 - 积累修复经验"""

    def __init__(self, knowledge_file: Optional[Path] = None):
        self.knowledge_file = knowledge_file or Path.cwd() / ".fix_knowledge" / "knowledge_base.json"
        self._entries: Dict[str, KnowledgeEntry] = {}
        self._entry_counter = 0
        self._ensure_knowledge_dir()
        self._load_knowledge()

    def _ensure_knowledge_dir(self) -> None:
        self.knowledge_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_knowledge(self) -> None:
        if self.knowledge_file.exists():
            try:
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for entry_id, entry_data in data.get("entries", {}).items():
                    self._entries[entry_id] = KnowledgeEntry(
                        entry_id=entry_data["entry_id"],
                        issue_category=IssueCategory[entry_data["issue_category"]],
                        issue_pattern=entry_data["issue_pattern"],
                        fix_strategy=entry_data["fix_strategy"],
                        success_rate=entry_data["success_rate"],
                        applied_count=entry_data["applied_count"],
                        last_applied=entry_data["last_applied"],
                        context=entry_data.get("context", {})
                    )
                
                logger.info(f"加载了 {len(self._entries)} 条知识记录")
            except Exception as e:
                logger.error(f"加载知识库失败: {e}")

    def _save_knowledge(self) -> None:
        try:
            data = {
                "entries": {entry_id: entry.to_dict() for entry_id, entry in self._entries.items()},
                "last_updated": datetime.now().isoformat()
            }
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存知识库失败: {e}")

    def add_entry(
        self,
        issue_category: IssueCategory,
        issue_pattern: str,
        fix_strategy: str,
        success: bool
    ) -> KnowledgeEntry:
        self._entry_counter += 1
        entry_id = f"KNOW_{self._entry_counter:04d}"
        
        pattern_key = f"{issue_category.name}_{hashlib.md5(issue_pattern.encode()).hexdigest()[:8]}"
        
        if pattern_key in self._entries:
            entry = self._entries[pattern_key]
            entry.applied_count += 1
            if success:
                entry.success_rate = (entry.success_rate * (entry.applied_count - 1) + 1) / entry.applied_count
            else:
                entry.success_rate = entry.success_rate * (entry.applied_count - 1) / entry.applied_count
            entry.last_applied = datetime.now().isoformat()
        else:
            entry = KnowledgeEntry(
                entry_id=entry_id,
                issue_category=issue_category,
                issue_pattern=issue_pattern,
                fix_strategy=fix_strategy,
                success_rate=1.0 if success else 0.0,
                applied_count=1,
                last_applied=datetime.now().isoformat()
            )
            self._entries[pattern_key] = entry
        
        self._save_knowledge()
        return entry

    def get_best_strategy(self, issue_category: IssueCategory, issue_pattern: str) -> Optional[str]:
        pattern_key = f"{issue_category.name}_{hashlib.md5(issue_pattern.encode()).hexdigest()[:8]}"
        
        if pattern_key in self._entries:
            entry = self._entries[pattern_key]
            if entry.success_rate >= 0.5:
                return entry.fix_strategy
        
        return None

    def get_entries_for_category(self, category: IssueCategory) -> List[KnowledgeEntry]:
        return [e for e in self._entries.values() if e.issue_category == category]


import hashlib


class AutoRepairWorkflow:
    """自动修复工作流"""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        config: Optional[WorkflowConfig] = None
    ):
        self.project_root = project_root or Path.cwd()
        self.config = config or WorkflowConfig()
        
        self.detector = IssueDetector(self.project_root)
        self.strategy_library = FixStrategyLibrary()
        self.executor = FixExecutor(self.project_root)
        self.knowledge_base = KnowledgeBase()
        
        self._workflow_counter = 0
        self._current_workflow: Optional[WorkflowResult] = None

    def repair_file(self, file_path: str) -> WorkflowResult:
        self._workflow_counter += 1
        workflow_id = f"WORKFLOW_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._workflow_counter:04d}"
        
        self._current_workflow = WorkflowResult(
            workflow_id=workflow_id,
            file_path=file_path,
            status=WorkflowStatus.RUNNING,
            current_stage=WorkflowStage.INITIALIZATION,
            start_time=datetime.now().isoformat(),
            end_time=None,
            total_duration_ms=0,
            stages=[],
            issues_detected=0,
            issues_fixed=0,
            issues_failed=0,
            issues_skipped=0,
            detection_result=None,
            execution_result=None,
            preview=None,
            knowledge_entries=[],
            message="工作流初始化"
        )
        
        workflow_start = time.perf_counter()
        
        try:
            self._run_initialization_stage(file_path)
            self._run_detection_stage(file_path)
            self._run_analysis_stage()
            self._run_fix_generation_stage(file_path)
            self._run_preview_stage()
            self._run_execution_stage(file_path)
            self._run_verification_stage()
            self._run_knowledge_accumulation_stage()
            self._complete_workflow(workflow_start)
        
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            self._fail_workflow(str(e), workflow_start)
        
        return self._current_workflow

    def _run_initialization_stage(self, file_path: str) -> None:
        stage_start = time.perf_counter()
        start_time = datetime.now().isoformat()
        
        self._current_workflow.current_stage = WorkflowStage.INITIALIZATION
        
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.INITIALIZATION,
                status=WorkflowStatus.SUCCESS,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message="初始化完成",
                details={"file_path": file_path, "config": self.config.to_dict()}
            )
            self._current_workflow.stages.append(stage_result)
            logger.info(f"初始化阶段完成: {file_path}")
        
        except Exception as e:
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.INITIALIZATION,
                status=WorkflowStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message="初始化失败",
                errors=[str(e)]
            )
            self._current_workflow.stages.append(stage_result)
            raise

    def _run_detection_stage(self, file_path: str) -> None:
        stage_start = time.perf_counter()
        start_time = datetime.now().isoformat()
        
        self._current_workflow.current_stage = WorkflowStage.DETECTION
        
        try:
            detection_result = self.detector.detect_file(file_path)
            self._current_workflow.detection_result = detection_result
            self._current_workflow.issues_detected = detection_result.total_issues
            
            issues_by_severity = defaultdict(int)
            for issue in detection_result.issues:
                issues_by_severity[issue.severity.value] += 1
            
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.DETECTION,
                status=WorkflowStatus.SUCCESS,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message=f"检测到 {detection_result.total_issues} 个问题",
                details={
                    "total_issues": detection_result.total_issues,
                    "critical": detection_result.critical_count,
                    "high": detection_result.high_count,
                    "medium": detection_result.medium_count,
                    "low": detection_result.low_count,
                    "detectors_used": detection_result.detectors_used
                }
            )
            self._current_workflow.stages.append(stage_result)
            logger.info(f"检测阶段完成: 发现 {detection_result.total_issues} 个问题")
        
        except Exception as e:
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.DETECTION,
                status=WorkflowStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message="检测失败",
                errors=[str(e)]
            )
            self._current_workflow.stages.append(stage_result)
            raise

    def _run_analysis_stage(self) -> None:
        stage_start = time.perf_counter()
        start_time = datetime.now().isoformat()
        
        self._current_workflow.current_stage = WorkflowStage.ANALYSIS
        
        try:
            issues = self._current_workflow.detection_result.issues
            
            filtered_issues = [
                i for i in issues
                if i.category not in self.config.skip_categories
            ]
            
            sorted_issues = sorted(
                filtered_issues,
                key=lambda i: self.config.priority_order.index(i.severity)
                if i.severity in self.config.priority_order
                else len(self.config.priority_order)
            )
            
            fixable_issues = [i for i in sorted_issues if self.strategy_library.can_fix(i)]
            non_fixable_issues = [i for i in sorted_issues if not self.strategy_library.can_fix(i)]
            
            self._current_workflow.issues_skipped = len(non_fixable_issues)
            
            self._current_workflow.metadata["fixable_issues"] = [i.issue_id for i in fixable_issues]
            self._current_workflow.metadata["non_fixable_issues"] = [i.issue_id for i in non_fixable_issues]
            
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.ANALYSIS,
                status=WorkflowStatus.SUCCESS,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message=f"分析了 {len(issues)} 个问题，{len(fixable_issues)} 个可修复",
                details={
                    "total_issues": len(issues),
                    "fixable": len(fixable_issues),
                    "non_fixable": len(non_fixable_issues),
                    "skipped_categories": [c.name for c in self.config.skip_categories]
                }
            )
            self._current_workflow.stages.append(stage_result)
            logger.info(f"分析阶段完成: {len(fixable_issues)} 个问题可修复")
        
        except Exception as e:
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.ANALYSIS,
                status=WorkflowStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message="分析失败",
                errors=[str(e)]
            )
            self._current_workflow.stages.append(stage_result)
            raise

    def _run_fix_generation_stage(self, file_path: str) -> None:
        stage_start = time.perf_counter()
        start_time = datetime.now().isoformat()
        
        self._current_workflow.current_stage = WorkflowStage.FIX_GENERATION
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = self._current_workflow.detection_result.issues
            fixable_issue_ids = self._current_workflow.metadata.get("fixable_issues", [])
            fixable_issues = [i for i in issues if i.issue_id in fixable_issue_ids]
            
            fixed_content, fix_results = self.strategy_library.apply_fix_batch(fixable_issues, content)
            
            self._current_workflow.metadata["fixed_content"] = fixed_content
            self._current_workflow.metadata["fix_results"] = [r.to_dict() for r in fix_results]
            
            successful = sum(1 for r in fix_results if r.status == FixStatus.SUCCESS)
            partial = sum(1 for r in fix_results if r.status == FixStatus.PARTIAL)
            failed = sum(1 for r in fix_results if r.status == FixStatus.FAILED)
            
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.FIX_GENERATION,
                status=WorkflowStatus.SUCCESS if successful > 0 else WorkflowStatus.PARTIAL,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message=f"生成了 {len(fix_results)} 个修复，{successful} 个成功",
                details={
                    "total_fixes": len(fix_results),
                    "successful": successful,
                    "partial": partial,
                    "failed": failed
                }
            )
            self._current_workflow.stages.append(stage_result)
            logger.info(f"修复生成阶段完成: {successful} 个修复成功")
        
        except Exception as e:
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.FIX_GENERATION,
                status=WorkflowStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message="修复生成失败",
                errors=[str(e)]
            )
            self._current_workflow.stages.append(stage_result)
            raise

    def _run_preview_stage(self) -> None:
        stage_start = time.perf_counter()
        start_time = datetime.now().isoformat()
        
        self._current_workflow.current_stage = WorkflowStage.PREVIEW
        
        try:
            file_path = self._current_workflow.file_path
            
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            fixed_content = self._current_workflow.metadata.get("fixed_content", original_content)
            fix_results_data = self._current_workflow.metadata.get("fix_results", [])
            
            fix_results = []
            for r in fix_results_data:
                fix_results.append(FixResult(
                    result_id=r["result_id"],
                    issue_id=r["issue_id"],
                    strategy_name=r["strategy_name"],
                    status=FixStatus(r["status"]),
                    original_code=r["original_code"],
                    fixed_code=r["fixed_code"],
                    line_number=r["line_number"],
                    confidence=r["confidence"],
                    execution_time_ms=r["execution_time_ms"],
                    message=r.get("message", ""),
                    warnings=r.get("warnings", [])
                ))
            
            preview = self.executor.preview_fix(file_path, original_content, fixed_content, fix_results)
            self._current_workflow.preview = preview
            
            can_apply = preview.can_auto_apply and self.config.auto_apply
            can_apply = can_apply and preview.confidence >= self.config.confidence_threshold
            
            self._current_workflow.metadata["can_apply"] = can_apply
            
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.PREVIEW,
                status=WorkflowStatus.SUCCESS,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message=f"预览生成完成，{'可自动应用' if can_apply else '需要人工审查'}",
                details={
                    "risk_level": preview.risk_level.value,
                    "confidence": preview.confidence,
                    "can_auto_apply": can_apply,
                    "changes_count": len(preview.changes)
                }
            )
            self._current_workflow.stages.append(stage_result)
            logger.info(f"预览阶段完成: 风险={preview.risk_level.value}, 置信度={preview.confidence:.2f}")
        
        except Exception as e:
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.PREVIEW,
                status=WorkflowStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message="预览生成失败",
                errors=[str(e)]
            )
            self._current_workflow.stages.append(stage_result)
            raise

    def _run_execution_stage(self, file_path: str) -> None:
        stage_start = time.perf_counter()
        start_time = datetime.now().isoformat()
        
        self._current_workflow.current_stage = WorkflowStage.EXECUTION
        
        can_apply = self._current_workflow.metadata.get("can_apply", False)
        
        if not can_apply:
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.EXECUTION,
                status=WorkflowStatus.CANCELLED,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message="修复需要人工审查，跳过自动执行"
            )
            self._current_workflow.stages.append(stage_result)
            self._current_workflow.issues_skipped = self._current_workflow.issues_detected
            return
        
        try:
            fixed_content = self._current_workflow.metadata.get("fixed_content", "")
            fix_results_data = self._current_workflow.metadata.get("fix_results", [])
            
            fix_results = []
            for r in fix_results_data:
                fix_results.append(FixResult(
                    result_id=r["result_id"],
                    issue_id=r["issue_id"],
                    strategy_name=r["strategy_name"],
                    status=FixStatus(r["status"]),
                    original_code=r["original_code"],
                    fixed_code=r["fixed_code"],
                    line_number=r["line_number"],
                    confidence=r["confidence"],
                    execution_time_ms=r["execution_time_ms"],
                    message=r.get("message", ""),
                    warnings=r.get("warnings", [])
                ))
            
            execution_result = self.executor.execute_fix(
                file_path=file_path,
                modified_content=fixed_content,
                fix_results=fix_results,
                create_backup=self.config.create_backup,
                verify=self.config.verify_fixes
            )
            
            self._current_workflow.execution_result = execution_result
            self._current_workflow.issues_fixed = execution_result.issues_fixed
            self._current_workflow.issues_failed = execution_result.issues_failed
            
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.EXECUTION,
                status=WorkflowStatus.SUCCESS if execution_result.status == ExecutionStatus.SUCCESS else WorkflowStatus.PARTIAL,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message=execution_result.message,
                details={
                    "status": execution_result.status.value,
                    "issues_fixed": execution_result.issues_fixed,
                    "issues_failed": execution_result.issues_failed
                }
            )
            self._current_workflow.stages.append(stage_result)
            logger.info(f"执行阶段完成: {execution_result.message}")
        
        except Exception as e:
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.EXECUTION,
                status=WorkflowStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message="执行失败",
                errors=[str(e)]
            )
            self._current_workflow.stages.append(stage_result)
            raise

    def _run_verification_stage(self) -> None:
        stage_start = time.perf_counter()
        start_time = datetime.now().isoformat()
        
        self._current_workflow.current_stage = WorkflowStage.VERIFICATION
        
        execution_result = self._current_workflow.execution_result
        if not execution_result or not execution_result.fix_record:
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.VERIFICATION,
                status=WorkflowStatus.SKIPPED,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message="无执行结果，跳过验证"
            )
            self._current_workflow.stages.append(stage_result)
            return
        
        verification = execution_result.fix_record.verification_result
        if not verification:
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.VERIFICATION,
                status=WorkflowStatus.SKIPPED,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message="验证已跳过"
            )
            self._current_workflow.stages.append(stage_result)
            return
        
        duration = (time.perf_counter() - stage_start) * 1000
        stage_result = StageResult(
            stage=WorkflowStage.VERIFICATION,
            status=WorkflowStatus.SUCCESS if verification.status.value == "passed" else WorkflowStatus.PARTIAL,
            start_time=start_time,
            end_time=datetime.now().isoformat(),
            duration_ms=duration,
            message=f"验证{'通过' if verification.status.value == 'passed' else '有警告'}",
            details={
                "status": verification.status.value,
                "syntax_valid": verification.syntax_valid,
                "quality_score": verification.quality_score,
                "issues_found": verification.issues_found
            }
        )
        self._current_workflow.stages.append(stage_result)
        logger.info(f"验证阶段完成: {verification.status.value}")

    def _run_knowledge_accumulation_stage(self) -> None:
        stage_start = time.perf_counter()
        start_time = datetime.now().isoformat()
        
        self._current_workflow.current_stage = WorkflowStage.KNOWLEDGE_ACCUMULATION
        
        if not self.config.knowledge_accumulation:
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.KNOWLEDGE_ACCUMULATION,
                status=WorkflowStatus.SKIPPED,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message="知识积累已禁用"
            )
            self._current_workflow.stages.append(stage_result)
            return
        
        try:
            fix_results_data = self._current_workflow.metadata.get("fix_results", [])
            knowledge_entries = []
            
            for r in fix_results_data:
                if r["status"] in ["success", "partial"]:
                    issue = next(
                        (i for i in self._current_workflow.detection_result.issues if i.issue_id == r["issue_id"]),
                        None
                    )
                    if issue:
                        entry = self.knowledge_base.add_entry(
                            issue_category=issue.category,
                            issue_pattern=issue.message[:100],
                            fix_strategy=r["strategy_name"],
                            success=r["status"] == "success"
                        )
                        knowledge_entries.append(entry)
            
            self._current_workflow.knowledge_entries = knowledge_entries
            
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.KNOWLEDGE_ACCUMULATION,
                status=WorkflowStatus.SUCCESS,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message=f"积累了 {len(knowledge_entries)} 条知识",
                details={"entries_count": len(knowledge_entries)}
            )
            self._current_workflow.stages.append(stage_result)
            logger.info(f"知识积累阶段完成: {len(knowledge_entries)} 条记录")
        
        except Exception as e:
            duration = (time.perf_counter() - stage_start) * 1000
            stage_result = StageResult(
                stage=WorkflowStage.KNOWLEDGE_ACCUMULATION,
                status=WorkflowStatus.PARTIAL,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                message="知识积累部分失败",
                errors=[str(e)]
            )
            self._current_workflow.stages.append(stage_result)

    def _complete_workflow(self, workflow_start: float) -> None:
        self._current_workflow.current_stage = WorkflowStage.COMPLETED
        self._current_workflow.end_time = datetime.now().isoformat()
        self._current_workflow.total_duration_ms = (time.perf_counter() - workflow_start) * 1000
        
        if self._current_workflow.issues_failed == 0:
            self._current_workflow.status = WorkflowStatus.SUCCESS
            self._current_workflow.message = f"修复完成，成功修复 {self._current_workflow.issues_fixed} 个问题"
        elif self._current_workflow.issues_fixed > 0:
            self._current_workflow.status = WorkflowStatus.PARTIAL
            self._current_workflow.message = f"部分修复完成，成功 {self._current_workflow.issues_fixed}，失败 {self._current_workflow.issues_failed}"
        else:
            self._current_workflow.status = WorkflowStatus.FAILED
            self._current_workflow.message = "修复失败"
        
        logger.info(f"工作流完成: {self._current_workflow.message}")

    def _fail_workflow(self, error_message: str, workflow_start: float) -> None:
        self._current_workflow.current_stage = WorkflowStage.FAILED
        self._current_workflow.status = WorkflowStatus.FAILED
        self._current_workflow.end_time = datetime.now().isoformat()
        self._current_workflow.total_duration_ms = (time.perf_counter() - workflow_start) * 1000
        self._current_workflow.message = f"工作流失败: {error_message}"
        
        logger.error(f"工作流失败: {error_message}")

    def repair_project(self, file_pattern: str = "*.py") -> Dict[str, WorkflowResult]:
        results = {}
        
        for py_file in self.project_root.rglob(file_pattern):
            if '.git' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            result = self.repair_file(str(py_file))
            results[str(py_file)] = result
        
        return results

    def preview_repair(self, file_path: str) -> Optional[FixPreview]:
        workflow_id = f"PREVIEW_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            detection_result = self.detector.detect_file(file_path)
            if not detection_result.issues:
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            fixable_issues = [i for i in detection_result.issues if self.strategy_library.can_fix(i)]
            if not fixable_issues:
                return None
            
            fixed_content, fix_results = self.strategy_library.apply_fix_batch(fixable_issues, content)
            
            return self.executor.preview_fix(file_path, content, fixed_content, fix_results)
        
        except Exception as e:
            logger.error(f"预览失败: {e}")
            return None

    def get_workflow_status(self) -> Optional[WorkflowResult]:
        return self._current_workflow


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="自动修复工作流")
    parser.add_argument("--file", type=str, help="要修复的文件")
    parser.add_argument("--project", action="store_true", help="修复整个项目")
    parser.add_argument("--preview", action="store_true", help="仅预览修复")
    parser.add_argument("--output", type=str, help="输出报告路径")
    parser.add_argument("--auto-apply", action="store_true", help="自动应用修复")
    parser.add_argument("--confidence", type=float, default=0.7, help="置信度阈值")
    
    args = parser.parse_args()
    
    config = WorkflowConfig(
        auto_apply=args.auto_apply,
        confidence_threshold=args.confidence
    )
    workflow = AutoRepairWorkflow(config=config)
    
    if args.file:
        if args.preview:
            preview = workflow.preview_repair(args.file)
            if preview:
                print(f"\n修复预览:")
                print(f"文件: {preview.file_path}")
                print(f"风险等级: {preview.risk_level.value}")
                print(f"置信度: {preview.confidence:.0%}")
                print(f"可自动应用: {'是' if preview.can_auto_apply else '否'}")
                print(f"\n变更数量: {len(preview.changes)}")
                print(f"\n差异:\n{preview.diff}")
            else:
                print("无需修复或预览失败")
        else:
            result = workflow.repair_file(args.file)
            
            print(f"\n工作流结果:")
            print(f"状态: {result.status.value}")
            print(f"检测问题: {result.issues_detected}")
            print(f"修复成功: {result.issues_fixed}")
            print(f"修复失败: {result.issues_failed}")
            print(f"跳过问题: {result.issues_skipped}")
            print(f"总耗时: {result.total_duration_ms:.2f}ms")
            print(f"\n消息: {result.message}")
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
                print(f"\n报告已保存到: {args.output}")
    
    elif args.project:
        results = workflow.repair_project()
        
        total_fixed = sum(r.issues_fixed for r in results.values())
        total_failed = sum(r.issues_failed for r in results.values())
        
        print(f"\n项目修复结果:")
        print(f"处理文件数: {len(results)}")
        print(f"总修复成功: {total_fixed}")
        print(f"总修复失败: {total_failed}")
        
        if args.output:
            output_data = {k: v.to_dict() for k, v in results.items()}
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
