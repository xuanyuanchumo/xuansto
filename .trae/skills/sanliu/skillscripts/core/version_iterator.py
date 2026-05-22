#!/usr/bin/env python3
"""
版本迭代器 - 核心模块
实现语义化版本自动升级、变更日志自动生成、版本快照自动创建、版本回滚机制

功能特性:
1. 完整的语义化版本管理 (SemVer 2.0.0)
2. 版本约束解析与范围检查
3. 自动变更日志生成 (Keep a Changelog)
4. 版本历史追踪与统计
5. 自迭代触发条件检测
6. 版本兼容性检查
7. 版本分支管理
8. 版本文档自动生成
9. 版本快照自动创建与恢复
10. 版本回滚机制
"""

import re
import json
import os
import sys
import shutil
import hashlib
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import logging


class VersionBumpType(Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRERELEASE = "prerelease"
    BUILD = "build"


class ChangeType(Enum):
    FEATURE = "feat"
    FIX = "fix"
    DOCS = "docs"
    STYLE = "style"
    REFACTOR = "refactor"
    PERF = "perf"
    TEST = "test"
    CHORE = "chore"
    BREAKING = "breaking"
    SECURITY = "security"
    DEPRECATE = "deprecate"


class IterationTriggerType(Enum):
    ERROR_RATE = "error_rate"
    CONTINUOUS_FAILURE = "continuous_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SECURITY_ALERT = "security_alert"
    CODE_QUALITY = "code_quality"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    TEST_FAILURE = "test_failure"
    DEPENDENCY_UPDATE = "dependency_update"
    QUALITY_THRESHOLD = "quality_threshold"
    HEALTH_SCORE = "health_score"
    COVERAGE_RATE = "coverage_rate"
    COMPLEXITY_SCORE = "complexity_score"


class IterationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    PAUSED = "paused"


class ImprovementTaskPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPTIONAL = "optional"


class IterationPhase(Enum):
    TRIGGER_DETECTION = "trigger_detection"
    QUALITY_ASSESSMENT = "quality_assessment"
    TASK_GENERATION = "task_generation"
    TASK_EXECUTION = "task_execution"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    POST_MONITORING = "post_monitoring"


class CompatibilityLevel(Enum):
    BREAKING = "breaking"
    COMPATIBLE = "compatible"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


class VersionConstraintOperator(Enum):
    EXACT = "=="
    GREATER = ">"
    GREATER_EQUAL = ">="
    LESS = "<"
    LESS_EQUAL = "<="
    COMPATIBLE = "~="
    WILDCARD = "*"
    CARET = "^"


@dataclass
class SemanticVersion:
    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build_metadata: str = ""

    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build_metadata:
            version += f"+{self.build_metadata}"
        return version

    def __lt__(self, other: "SemanticVersion") -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        return False

    def __le__(self, other: "SemanticVersion") -> bool:
        return self == other or self < other

    def __gt__(self, other: "SemanticVersion") -> bool:
        return not self <= other

    def __ge__(self, other: "SemanticVersion") -> bool:
        return not self < other

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return False
        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch and
            self.prerelease == other.prerelease
        )

    @classmethod
    def parse(cls, version_str: str) -> "SemanticVersion":
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$'
        match = re.match(pattern, version_str)

        if not match:
            raise ValueError(f"无效的版本格式: {version_str}")

        major, minor, patch, prerelease, build = match.groups()
        return cls(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=prerelease or "",
            build_metadata=build or ""
        )

    def bump(self, bump_type: VersionBumpType, prerelease_id: str = "", build_metadata: str = "") -> "SemanticVersion":
        if bump_type == VersionBumpType.MAJOR:
            return SemanticVersion(
                major=self.major + 1,
                minor=0,
                patch=0,
                prerelease=prerelease_id,
                build_metadata=build_metadata
            )
        elif bump_type == VersionBumpType.MINOR:
            return SemanticVersion(
                major=self.major,
                minor=self.minor + 1,
                patch=0,
                prerelease=prerelease_id,
                build_metadata=build_metadata
            )
        elif bump_type == VersionBumpType.PATCH:
            return SemanticVersion(
                major=self.major,
                minor=self.minor,
                patch=self.patch + 1,
                prerelease=prerelease_id,
                build_metadata=build_metadata
            )
        elif bump_type == VersionBumpType.PRERELEASE:
            return SemanticVersion(
                major=self.major,
                minor=self.minor,
                patch=self.patch,
                prerelease=prerelease_id or f"alpha.{self._get_next_prerelease_number()}",
                build_metadata=build_metadata
            )
        elif bump_type == VersionBumpType.BUILD:
            return SemanticVersion(
                major=self.major,
                minor=self.minor,
                patch=self.patch,
                prerelease=self.prerelease,
                build_metadata=build_metadata or datetime.now().strftime('%Y%m%d%H%M%S')
            )
        else:
            raise ValueError(f"未知的版本升级类型: {bump_type}")

    def _get_next_prerelease_number(self) -> int:
        if self.prerelease and 'alpha' in self.prerelease:
            try:
                return int(self.prerelease.split('.')[-1]) + 1
            except ValueError:
                return 1
        return 1


@dataclass
class VersionConstraint:
    operator: VersionConstraintOperator
    version: SemanticVersion
    description: str = ""

    def matches(self, version: SemanticVersion) -> bool:
        if self.operator == VersionConstraintOperator.EXACT:
            return str(version) == str(self.version)
        elif self.operator == VersionConstraintOperator.GREATER:
            return self._compare(version, self.version) > 0
        elif self.operator == VersionConstraintOperator.GREATER_EQUAL:
            return self._compare(version, self.version) >= 0
        elif self.operator == VersionConstraintOperator.LESS:
            return self._compare(version, self.version) < 0
        elif self.operator == VersionConstraintOperator.LESS_EQUAL:
            return self._compare(version, self.version) <= 0
        elif self.operator == VersionConstraintOperator.COMPATIBLE:
            return (
                version.major == self.version.major and
                version.minor == self.version.minor and
                version.patch >= self.version.patch
            )
        elif self.operator == VersionConstraintOperator.CARET:
            if self.version.major > 0:
                return (
                    version.major == self.version.major and
                    self._compare(version, self.version) >= 0
                )
            else:
                return (
                    version.major == 0 and
                    version.minor == self.version.minor and
                    version.patch >= self.version.patch
                )
        elif self.operator == VersionConstraintOperator.WILDCARD:
            return True
        return False

    def _compare(self, v1: SemanticVersion, v2: SemanticVersion) -> int:
        if v1.major != v2.major:
            return 1 if v1.major > v2.major else -1
        if v1.minor != v2.minor:
            return 1 if v1.minor > v2.minor else -1
        if v1.patch != v2.patch:
            return 1 if v1.patch > v2.patch else -1
        return 0


@dataclass
class VersionRange:
    constraints: List[VersionConstraint]
    description: str = ""

    def matches(self, version: SemanticVersion) -> bool:
        return all(c.matches(version) for c in self.constraints)

    @classmethod
    def parse(cls, range_str: str) -> "VersionRange":
        constraints = []
        parts = range_str.split(",")
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            op = VersionConstraintOperator.EXACT
            version_str = part
            
            if part.startswith(">="):
                op = VersionConstraintOperator.GREATER_EQUAL
                version_str = part[2:].strip()
            elif part.startswith("<="):
                op = VersionConstraintOperator.LESS_EQUAL
                version_str = part[2:].strip()
            elif part.startswith("~="):
                op = VersionConstraintOperator.COMPATIBLE
                version_str = part[2:].strip()
            elif part.startswith("^"):
                op = VersionConstraintOperator.CARET
                version_str = part[1:].strip()
            elif part.startswith(">"):
                op = VersionConstraintOperator.GREATER
                version_str = part[1:].strip()
            elif part.startswith("<"):
                op = VersionConstraintOperator.LESS
                version_str = part[1:].strip()
            elif part.startswith("=="):
                op = VersionConstraintOperator.EXACT
                version_str = part[2:].strip()
            elif part == "*":
                op = VersionConstraintOperator.WILDCARD
                version_str = "0.0.0"
            
            if version_str and version_str != "0.0.0":
                version = SemanticVersion.parse(version_str)
                constraints.append(VersionConstraint(operator=op, version=version))
        
        return cls(constraints=constraints, description=range_str)


@dataclass
class ChangeEntry:
    change_type: ChangeType
    description: str
    scope: str = ""
    breaking: bool = False
    issue_refs: List[str] = field(default_factory=list)
    author: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    commit_hash: str = ""
    file_paths: List[str] = field(default_factory=list)
    impact_level: str = "low"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_type": self.change_type.value,
            "description": self.description,
            "scope": self.scope,
            "breaking": self.breaking,
            "issue_refs": self.issue_refs,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
            "commit_hash": self.commit_hash,
            "file_paths": self.file_paths,
            "impact_level": self.impact_level
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChangeEntry":
        return cls(
            change_type=ChangeType(data.get("change_type", "chore")),
            description=data.get("description", ""),
            scope=data.get("scope", ""),
            breaking=data.get("breaking", False),
            issue_refs=data.get("issue_refs", []),
            author=data.get("author", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            commit_hash=data.get("commit_hash", ""),
            file_paths=data.get("file_paths", []),
            impact_level=data.get("impact_level", "low")
        )


@dataclass
class VersionSnapshot:
    version: str
    timestamp: str
    snapshot_id: str
    files: Dict[str, Dict[str, str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "snapshot_id": self.snapshot_id,
            "files": self.files,
            "metadata": self.metadata,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VersionSnapshot":
        return cls(
            version=data.get("version", ""),
            timestamp=data.get("timestamp", ""),
            snapshot_id=data.get("snapshot_id", ""),
            files=data.get("files", {}),
            metadata=data.get("metadata", {}),
            description=data.get("description", "")
        )


@dataclass
class DependencyInfo:
    name: str
    version_range: str
    compatibility: CompatibilityLevel
    required: bool = True
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version_range": self.version_range,
            "compatibility": self.compatibility.value,
            "required": self.required,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DependencyInfo":
        return cls(
            name=data.get("name", ""),
            version_range=data.get("version_range", ""),
            compatibility=CompatibilityLevel(data.get("compatibility", "compatible")),
            required=data.get("required", True),
            notes=data.get("notes", "")
        )


@dataclass
class QualityMetrics:
    code_quality_score: float = 1.0
    test_coverage: float = 0.0
    error_rate: float = 0.0
    performance_score: float = 1.0
    security_score: float = 1.0
    health_score: float = 1.0
    complexity_score: float = 0.0
    maintainability_index: float = 1.0
    technical_debt_ratio: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code_quality_score": self.code_quality_score,
            "test_coverage": self.test_coverage,
            "error_rate": self.error_rate,
            "performance_score": self.performance_score,
            "security_score": self.security_score,
            "health_score": self.health_score,
            "complexity_score": self.complexity_score,
            "maintainability_index": self.maintainability_index,
            "technical_debt_ratio": self.technical_debt_ratio,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityMetrics":
        return cls(
            code_quality_score=data.get("code_quality_score", 1.0),
            test_coverage=data.get("test_coverage", 0.0),
            error_rate=data.get("error_rate", 0.0),
            performance_score=data.get("performance_score", 1.0),
            security_score=data.get("security_score", 1.0),
            health_score=data.get("health_score", 1.0),
            complexity_score=data.get("complexity_score", 0.0),
            maintainability_index=data.get("maintainability_index", 1.0),
            technical_debt_ratio=data.get("technical_debt_ratio", 0.0),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
        )
    
    def calculate_overall_score(self) -> float:
        weights = {
            "code_quality": 0.25,
            "test_coverage": 0.15,
            "error_rate": 0.15,
            "performance": 0.15,
            "security": 0.15,
            "health": 0.15
        }
        
        error_rate_score = max(0, 1.0 - self.error_rate)
        coverage_score = min(1.0, self.test_coverage / 100.0)
        
        overall = (
            self.code_quality_score * weights["code_quality"] +
            coverage_score * weights["test_coverage"] +
            error_rate_score * weights["error_rate"] +
            self.performance_score * weights["performance"] +
            self.security_score * weights["security"] +
            self.health_score * weights["health"]
        )
        
        return round(overall, 3)


@dataclass
class ImprovementTask:
    task_id: str
    title: str
    description: str
    priority: ImprovementTaskPriority
    category: str
    affected_components: List[str] = field(default_factory=list)
    estimated_effort: str = "medium"
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    assigned_to: str = ""
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metrics_before: Optional[QualityMetrics] = None
    metrics_after: Optional[QualityMetrics] = None
    impact_score: float = 0.0
    iteration_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "category": self.category,
            "affected_components": self.affected_components,
            "estimated_effort": self.estimated_effort,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "assigned_to": self.assigned_to,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "metrics_before": self.metrics_before.to_dict() if self.metrics_before else None,
            "metrics_after": self.metrics_after.to_dict() if self.metrics_after else None,
            "impact_score": self.impact_score,
            "iteration_id": self.iteration_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImprovementTask":
        return cls(
            task_id=data.get("task_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            priority=ImprovementTaskPriority(data.get("priority", "medium")),
            category=data.get("category", ""),
            affected_components=data.get("affected_components", []),
            estimated_effort=data.get("estimated_effort", "medium"),
            status=data.get("status", "pending"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            assigned_to=data.get("assigned_to", ""),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            dependencies=data.get("dependencies", []),
            tags=data.get("tags", []),
            metrics_before=QualityMetrics.from_dict(data["metrics_before"]) if data.get("metrics_before") else None,
            metrics_after=QualityMetrics.from_dict(data["metrics_after"]) if data.get("metrics_after") else None,
            impact_score=data.get("impact_score", 0.0),
            iteration_id=data.get("iteration_id", "")
        )


@dataclass
class IterationProgress:
    iteration_id: str
    version: str
    status: IterationStatus
    current_phase: IterationPhase
    progress_percentage: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    phases_completed: List[IterationPhase] = field(default_factory=list)
    phases_pending: List[IterationPhase] = field(default_factory=list)
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    metrics_snapshot: Optional[QualityMetrics] = None
    triggers: List[IterationTriggerType] = field(default_factory=list)
    rollback_available: bool = True
    rollback_snapshot_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration_id": self.iteration_id,
            "version": self.version,
            "status": self.status.value,
            "current_phase": self.current_phase.value,
            "progress_percentage": self.progress_percentage,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "phases_completed": [p.value for p in self.phases_completed],
            "phases_pending": [p.value for p in self.phases_pending],
            "tasks_total": self.tasks_total,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics_snapshot": self.metrics_snapshot.to_dict() if self.metrics_snapshot else None,
            "triggers": [t.value for t in self.triggers],
            "rollback_available": self.rollback_available,
            "rollback_snapshot_id": self.rollback_snapshot_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IterationProgress":
        return cls(
            iteration_id=data.get("iteration_id", ""),
            version=data.get("version", ""),
            status=IterationStatus(data.get("status", "pending")),
            current_phase=IterationPhase(data.get("current_phase", "trigger_detection")),
            progress_percentage=data.get("progress_percentage", 0.0),
            started_at=datetime.fromisoformat(data.get("started_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            phases_completed=[IterationPhase(p) for p in data.get("phases_completed", [])],
            phases_pending=[IterationPhase(p) for p in data.get("phases_pending", [])],
            tasks_total=data.get("tasks_total", 0),
            tasks_completed=data.get("tasks_completed", 0),
            tasks_failed=data.get("tasks_failed", 0),
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
            metrics_snapshot=QualityMetrics.from_dict(data["metrics_snapshot"]) if data.get("metrics_snapshot") else None,
            triggers=[IterationTriggerType(t) for t in data.get("triggers", [])],
            rollback_available=data.get("rollback_available", True),
            rollback_snapshot_id=data.get("rollback_snapshot_id", "")
        )


@dataclass
class IterationTrigger:
    trigger_type: IterationTriggerType
    threshold: float
    current_value: float
    triggered: bool
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VersionEntry:
    version: str
    previous_version: str
    timestamp: str
    changes: List[ChangeEntry]
    author: str = ""
    commit_hash: str = ""
    tag_name: str = ""
    notes: str = ""
    release_type: str = "patch"
    stability: str = "stable"
    test_coverage: float = 0.0
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    snapshot_id: str = ""
    compatibility_level: CompatibilityLevel = CompatibilityLevel.COMPATIBLE
    dependencies: List[DependencyInfo] = field(default_factory=list)
    deprecation_warnings: List[str] = field(default_factory=list)
    migration_guide: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "previous_version": self.previous_version,
            "timestamp": self.timestamp,
            "changes": [c.to_dict() for c in self.changes],
            "author": self.author,
            "commit_hash": self.commit_hash,
            "tag_name": self.tag_name,
            "notes": self.notes,
            "release_type": self.release_type,
            "stability": self.stability,
            "test_coverage": self.test_coverage,
            "performance_metrics": self.performance_metrics,
            "snapshot_id": self.snapshot_id,
            "compatibility_level": self.compatibility_level.value,
            "dependencies": [d.to_dict() for d in self.dependencies],
            "deprecation_warnings": self.deprecation_warnings,
            "migration_guide": self.migration_guide
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VersionEntry":
        return cls(
            version=data.get("version", "0.0.0"),
            previous_version=data.get("previous_version", ""),
            timestamp=data.get("timestamp", ""),
            changes=[ChangeEntry.from_dict(c) for c in data.get("changes", [])],
            author=data.get("author", ""),
            commit_hash=data.get("commit_hash", ""),
            tag_name=data.get("tag_name", ""),
            notes=data.get("notes", ""),
            release_type=data.get("release_type", "patch"),
            stability=data.get("stability", "stable"),
            test_coverage=data.get("test_coverage", 0.0),
            performance_metrics=data.get("performance_metrics", {}),
            snapshot_id=data.get("snapshot_id", ""),
            compatibility_level=CompatibilityLevel(data.get("compatibility_level", "compatible")),
            dependencies=[DependencyInfo.from_dict(d) for d in data.get("dependencies", [])],
            deprecation_warnings=data.get("deprecation_warnings", []),
            migration_guide=data.get("migration_guide", "")
        )


@dataclass
class VersionHistory:
    project_name: str
    current_version: str
    versions: List[VersionEntry]
    iteration_count: int = 0
    total_changes: int = 0
    last_iteration_time: str = ""
    snapshots: List[VersionSnapshot] = field(default_factory=list)
    iteration_triggers: List[IterationTrigger] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    version_constraints: Dict[str, str] = field(default_factory=dict)
    improvement_tasks: List[ImprovementTask] = field(default_factory=list)
    iteration_progress_history: List[IterationProgress] = field(default_factory=list)
    quality_metrics_history: List[QualityMetrics] = field(default_factory=list)
    current_iteration: Optional[IterationProgress] = None
    quality_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "code_quality_score": 0.7,
        "test_coverage": 60.0,
        "error_rate": 0.05,
        "performance_score": 0.7,
        "security_score": 0.8,
        "health_score": 0.75,
        "overall_score": 0.7
    })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "current_version": self.current_version,
            "versions": [v.to_dict() for v in self.versions],
            "iteration_count": self.iteration_count,
            "total_changes": self.total_changes,
            "last_iteration_time": self.last_iteration_time,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "iteration_triggers": [
                {
                    "trigger_type": t.trigger_type.value,
                    "threshold": t.threshold,
                    "current_value": t.current_value,
                    "triggered": t.triggered,
                    "timestamp": t.timestamp.isoformat(),
                    "details": t.details
                }
                for t in self.iteration_triggers
            ],
            "statistics": self.statistics,
            "version_constraints": self.version_constraints,
            "improvement_tasks": [t.to_dict() for t in self.improvement_tasks],
            "iteration_progress_history": [p.to_dict() for p in self.iteration_progress_history],
            "quality_metrics_history": [m.to_dict() for m in self.quality_metrics_history],
            "current_iteration": self.current_iteration.to_dict() if self.current_iteration else None,
            "quality_thresholds": self.quality_thresholds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VersionHistory":
        return cls(
            project_name=data.get("project_name", "Unknown"),
            current_version=data.get("current_version", "0.0.0"),
            versions=[VersionEntry.from_dict(v) for v in data.get("versions", [])],
            iteration_count=data.get("iteration_count", 0),
            total_changes=data.get("total_changes", 0),
            last_iteration_time=data.get("last_iteration_time", ""),
            snapshots=[VersionSnapshot.from_dict(s) for s in data.get("snapshots", [])],
            iteration_triggers=[
                IterationTrigger(
                    trigger_type=IterationTriggerType(t.get("trigger_type", "manual")),
                    threshold=t.get("threshold", 0.0),
                    current_value=t.get("current_value", 0.0),
                    triggered=t.get("triggered", False),
                    timestamp=datetime.fromisoformat(t.get("timestamp", datetime.now().isoformat())),
                    details=t.get("details", {})
                )
                for t in data.get("iteration_triggers", [])
            ],
            statistics=data.get("statistics", {}),
            version_constraints=data.get("version_constraints", {}),
            improvement_tasks=[ImprovementTask.from_dict(t) for t in data.get("improvement_tasks", [])],
            iteration_progress_history=[IterationProgress.from_dict(p) for p in data.get("iteration_progress_history", [])],
            quality_metrics_history=[QualityMetrics.from_dict(m) for m in data.get("quality_metrics_history", [])],
            current_iteration=IterationProgress.from_dict(data["current_iteration"]) if data.get("current_iteration") else None,
            quality_thresholds=data.get("quality_thresholds", {
                "code_quality_score": 0.7,
                "test_coverage": 60.0,
                "error_rate": 0.05,
                "performance_score": 0.7,
                "security_score": 0.8,
                "health_score": 0.75,
                "overall_score": 0.7
            })
        )


@dataclass
class VersionStatistics:
    total_versions: int
    major_versions: int
    minor_versions: int
    patch_versions: int
    prerelease_versions: int
    average_changes_per_version: float
    most_active_scope: str
    change_type_distribution: Dict[str, int]
    version_frequency: Dict[str, int]
    recent_velocity: float


class ChangelogGenerator:
    """变更日志生成器"""

    TYPE_TITLES = {
        ChangeType.BREAKING: "⚠️ 重大变更",
        ChangeType.FEATURE: "✨ 新功能",
        ChangeType.FIX: "🐛 Bug修复",
        ChangeType.PERF: "⚡ 性能优化",
        ChangeType.REFACTOR: "♻️ 代码重构",
        ChangeType.DOCS: "📝 文档",
        ChangeType.STYLE: "💄 代码风格",
        ChangeType.TEST: "✅ 测试",
        ChangeType.SECURITY: "🔒 安全",
        ChangeType.DEPRECATE: "⚠️ 废弃",
        ChangeType.CHORE: "🔧 其他",
    }

    def __init__(self, version_history: VersionHistory):
        self.history = version_history

    def generate(self, output_format: str = "markdown", include_unreleased: bool = True, detail_level: str = "normal") -> str:
        if output_format == "json":
            return self._generate_json()
        return self._generate_markdown(include_unreleased, detail_level)

    def _generate_markdown(self, include_unreleased: bool = True, detail_level: str = "normal") -> str:
        lines = [
            f"# {self.history.project_name} 变更日志",
            "",
            "所有显著变更都将记录在此文件中。",
            "",
            "格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，",
            "并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。",
            "",
        ]

        for version in self.history.versions:
            lines.extend([
                f"## [{version.version}] - {version.timestamp[:10]}",
                "",
            ])

            if version.notes:
                lines.extend([version.notes, ""])

            if version.changes:
                lines.extend(self._format_changes_by_type(version.changes, detail_level))
            else:
                lines.extend(["- 无显著变更", ""])

            if detail_level == "detailed":
                lines.extend(self._generate_version_details(version))

            lines.append("")

        return '\n'.join(lines)

    def _generate_json(self) -> str:
        data = {
            "project": self.history.project_name,
            "current_version": self.history.current_version,
            "versions": [v.to_dict() for v in self.history.versions]
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _format_changes_by_type(self, changes: List[ChangeEntry], detail_level: str = "normal") -> List[str]:
        grouped = defaultdict(list)
        for change in changes:
            grouped[change.change_type].append(change)

        lines = []
        for change_type in ChangeType:
            if change_type in grouped:
                lines.append(f"### {self.TYPE_TITLES.get(change_type, change_type.value)}")
                lines.append("")

                for change in grouped[change_type]:
                    scope = f"**{change.scope}**: " if change.scope else ""
                    breaking_marker = " 💥" if change.breaking else ""

                    if detail_level == "detailed" and change.issue_refs:
                        issues = f" (refs: {', '.join(change.issue_refs)})"
                    else:
                        issues = ""

                    lines.append(f"- {scope}{change.description}{breaking_marker}{issues}")

                lines.append("")

        return lines

    def _generate_version_details(self, version: VersionEntry) -> List[str]:
        details = []

        if version.author:
            details.append(f"**作者**: {version.author}")

        if version.commit_hash:
            details.append(f"**提交**: {version.commit_hash}")

        if version.tag_name:
            details.append(f"**标签**: {version.tag_name}")

        breaking_changes = [c for c in version.changes if c.breaking]
        if breaking_changes:
            details.append("")
            details.append("**⚠️ 重大变更详情**:")
            for change in breaking_changes:
                details.append(f"- {change.description}")
                if change.issue_refs:
                    details.append(f"  相关问题: {', '.join(change.issue_refs)}")

        if details:
            return ["", "### 版本详情", ""] + details + [""]
        return []

    def generate_release_notes(self, version: str) -> str:
        version_entry = None
        for v in self.history.versions:
            if v.version == version:
                version_entry = v
                break

        if not version_entry:
            return f"版本 {version} 未找到"

        lines = [
            f"# {self.history.project_name} v{version} 发布说明",
            "",
            f"**发布日期**: {version_entry.timestamp[:10]}",
            "",
        ]

        if version_entry.notes:
            lines.extend([version_entry.notes, ""])

        if version_entry.changes:
            lines.extend(self._format_changes_by_type(version_entry.changes, "detailed"))

        if version_entry.commit_hash:
            lines.extend([
                "## 技术详情",
                "",
                f"- 提交哈希: {version_entry.commit_hash}",
                f"- 标签: {version_entry.tag_name}",
            ])

        return '\n'.join(lines)


class VersionIterator:
    """版本迭代器核心类"""

    DEFAULT_VERSION_FILE = "version.json"
    DEFAULT_CHANGELOG_FILE = "CHANGELOG.md"
    DEFAULT_SNAPSHOT_DIR = ".version_snapshots"
    DEFAULT_DOCS_DIR = "docs/versions"

    def __init__(self, project_root: str = ".", version_file: Optional[str] = None):
        self.project_root = Path(project_root).resolve()
        self.version_file = Path(version_file) if version_file else self.project_root / self.DEFAULT_VERSION_FILE
        self.changelog_file = self.project_root / self.DEFAULT_CHANGELOG_FILE
        self.snapshot_dir = self.project_root / self.DEFAULT_SNAPSHOT_DIR
        self.docs_dir = self.project_root / self.DEFAULT_DOCS_DIR
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()
        self.history = self._load_history()
        self.changelog_generator = ChangelogGenerator(self.history)

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('VersionIterator')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_history(self) -> VersionHistory:
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return VersionHistory.from_dict(data)
            except Exception as e:
                self.logger.error(f"加载版本历史失败: {e}")

        return VersionHistory(
            project_name=self.project_root.name,
            current_version="0.0.0",
            versions=[],
            iteration_count=0
        )

    def _save_history(self) -> None:
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(self.history.to_dict(), f, indent=2, ensure_ascii=False)

    def get_current_version(self) -> SemanticVersion:
        return SemanticVersion.parse(self.history.current_version)

    def bump_version(
        self,
        bump_type: VersionBumpType,
        prerelease_id: str = "",
        build_metadata: str = ""
    ) -> str:
        current = self.get_current_version()
        new_version = current.bump(bump_type, prerelease_id, build_metadata)
        return str(new_version)

    def create_snapshot(self, version: str, description: str = "") -> VersionSnapshot:
        snapshot_id = f"SNAP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        snapshot_dir = self.snapshot_dir / snapshot_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        snapshot = VersionSnapshot(
            version=version,
            timestamp=datetime.now().isoformat(),
            snapshot_id=snapshot_id,
            description=description
        )

        for py_file in self.project_root.rglob("*.py"):
            try:
                rel_path = py_file.relative_to(self.project_root)
                if str(rel_path).startswith('.version_snapshots'):
                    continue
                    
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                snapshot.files[str(rel_path)] = {
                    "content": content,
                    "hash": hashlib.md5(content.encode()).hexdigest()
                }
            except Exception:
                continue

        snapshot_file = snapshot_dir / "snapshot.json"
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot.to_dict(), f, indent=2, ensure_ascii=False)

        self.history.snapshots.append(snapshot)
        self._save_history()

        self.logger.info(f"创建版本快照: {snapshot_id}")
        return snapshot

    def restore_snapshot(self, snapshot_id: str) -> bool:
        snapshot = None
        for s in self.history.snapshots:
            if s.snapshot_id == snapshot_id:
                snapshot = s
                break

        if not snapshot:
            self.logger.error(f"快照不存在: {snapshot_id}")
            return False

        try:
            for rel_path, file_data in snapshot.files.items():
                file_path = self.project_root / rel_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_data["content"])

            self.history.current_version = snapshot.version
            self._save_history()

            self.logger.info(f"恢复快照成功: {snapshot_id}")
            return True

        except Exception as e:
            self.logger.error(f"恢复快照失败: {e}")
            return False

    def list_snapshots(self) -> List[Dict[str, Any]]:
        return [
            {
                "snapshot_id": s.snapshot_id,
                "version": s.version,
                "timestamp": s.timestamp,
                "file_count": len(s.files),
                "description": s.description
            }
            for s in self.history.snapshots
        ]

    def cleanup_old_snapshots(self, keep_count: int = 10) -> int:
        snapshots = self.list_snapshots()
        removed_count = 0
        
        for snapshot in snapshots[keep_count:]:
            try:
                snapshot_dir = self.snapshot_dir / snapshot["snapshot_id"]
                if snapshot_dir.exists():
                    shutil.rmtree(snapshot_dir)
                    
                self.history.snapshots = [
                    s for s in self.history.snapshots 
                    if s.snapshot_id != snapshot["snapshot_id"]
                ]
                removed_count += 1
            except Exception:
                continue
        
        if removed_count > 0:
            self._save_history()
            
        return removed_count

    def create_version_entry(
        self,
        new_version: str,
        changes: List[ChangeEntry],
        author: str = "",
        notes: str = "",
        create_snapshot: bool = True
    ) -> VersionEntry:
        previous_version = self.history.current_version
        commit_hash = self._get_git_commit_hash()
        tag_name = f"v{new_version}"

        snapshot_id = ""
        if create_snapshot:
            snapshot = self.create_snapshot(new_version, f"Version {new_version}")
            snapshot_id = snapshot.snapshot_id

        entry = VersionEntry(
            version=new_version,
            previous_version=previous_version,
            timestamp=datetime.now().isoformat(),
            changes=changes,
            author=author or self._get_git_user(),
            commit_hash=commit_hash,
            tag_name=tag_name,
            notes=notes,
            snapshot_id=snapshot_id
        )

        self.history.versions.insert(0, entry)
        self.history.current_version = new_version
        self.history.iteration_count += 1
        self.history.total_changes += len(changes)
        self.history.last_iteration_time = datetime.now().isoformat()

        self._save_history()

        return entry

    def _get_git_commit_hash(self) -> str:
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _get_git_user(self) -> str:
        try:
            result = subprocess.run(
                ['git', 'config', 'user.name'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def rollback_version(self, target_version: Optional[str] = None) -> bool:
        if not target_version:
            if len(self.history.versions) < 2:
                self.logger.error("没有可回滚的版本")
                return False
            target_version = self.history.versions[1].version

        target_entry = None
        target_index = -1
        for i, version in enumerate(self.history.versions):
            if version.version == target_version:
                target_entry = version
                target_index = i
                break

        if not target_entry:
            self.logger.error(f"未找到版本: {target_version}")
            return False

        if target_entry.snapshot_id:
            if not self.restore_snapshot(target_entry.snapshot_id):
                self.logger.warning(f"快照恢复失败，仅回滚版本号")

        self.history.current_version = target_version
        self.history.versions = self.history.versions[target_index:]
        self._save_history()

        self.logger.info(f"已回滚到版本: {target_version}")
        return True

    def iterate(
        self,
        bump_type: VersionBumpType,
        changes: List[ChangeEntry],
        author: str = "",
        notes: str = "",
        prerelease_id: str = "",
        build_metadata: str = "",
        create_snapshot: bool = True
    ) -> VersionEntry:
        new_version = self.bump_version(bump_type, prerelease_id, build_metadata)

        entry = self.create_version_entry(
            new_version=new_version,
            changes=changes,
            author=author,
            notes=notes,
            create_snapshot=create_snapshot
        )

        self.changelog_generator = ChangelogGenerator(self.history)
        changelog = self.changelog_generator.generate()
        with open(self.changelog_file, 'w', encoding='utf-8') as f:
            f.write(changelog)

        self.logger.info(f"版本迭代完成: {entry.previous_version} -> {new_version}")

        return entry

    def auto_iterate(self, author: str = "") -> VersionEntry:
        changes = self._get_unreleased_changes()

        if not changes:
            self.logger.warning("没有检测到变更，使用默认变更记录")
            changes = [ChangeEntry(
                change_type=ChangeType.CHORE,
                description="版本迭代",
                scope="version"
            )]

        has_breaking = any(c.breaking or c.change_type == ChangeType.BREAKING for c in changes)
        has_feature = any(c.change_type == ChangeType.FEATURE for c in changes)

        if has_breaking:
            bump_type = VersionBumpType.MAJOR
        elif has_feature:
            bump_type = VersionBumpType.MINOR
        else:
            bump_type = VersionBumpType.PATCH

        return self.iterate(bump_type, changes, author)

    def _get_unreleased_changes(self) -> List[ChangeEntry]:
        try:
            result = subprocess.run(
                ['git', 'log', f'{self.history.current_version}..HEAD', '--pretty=format:%s'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )

            changes = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    change = self._parse_commit_message(line)
                    if change:
                        changes.append(change)

            return changes

        except Exception:
            return []

    def _parse_commit_message(self, message: str) -> Optional[ChangeEntry]:
        pattern = r'^(\w+)(?:\(([^)]+)\))?:\s*(.+)$'
        match = re.match(pattern, message)

        if match:
            change_type_str, scope, description = match.groups()

            change_type_map = {
                'feat': ChangeType.FEATURE,
                'fix': ChangeType.FIX,
                'docs': ChangeType.DOCS,
                'style': ChangeType.STYLE,
                'refactor': ChangeType.REFACTOR,
                'perf': ChangeType.PERF,
                'test': ChangeType.TEST,
                'chore': ChangeType.CHORE,
            }

            change_type = change_type_map.get(change_type_str, ChangeType.CHORE)
            breaking = '!' in message or 'BREAKING CHANGE' in message

            return ChangeEntry(
                change_type=change_type,
                description=description,
                scope=scope or "",
                breaking=breaking
            )

        return None

    def suggest_next_version(self, changes: List[ChangeEntry]) -> Tuple[str, VersionBumpType]:
        has_breaking = any(c.breaking or c.change_type == ChangeType.BREAKING for c in changes)
        has_feature = any(c.change_type == ChangeType.FEATURE for c in changes)
        has_security = any(c.change_type == ChangeType.SECURITY for c in changes)

        if has_breaking:
            bump_type = VersionBumpType.MAJOR
        elif has_feature:
            bump_type = VersionBumpType.MINOR
        else:
            bump_type = VersionBumpType.PATCH

        next_version = self.bump_version(bump_type)
        return next_version, bump_type

    def calculate_statistics(self) -> VersionStatistics:
        major_count = 0
        minor_count = 0
        patch_count = 0
        prerelease_count = 0
        total_changes = 0
        change_type_dist = defaultdict(int)
        scope_counts = defaultdict(int)
        version_freq = defaultdict(int)

        for version_entry in self.history.versions:
            v = SemanticVersion.parse(version_entry.version)
            
            if v.prerelease:
                prerelease_count += 1
            elif version_entry.release_type == "major" or (v.major > 0 and v.minor == 0 and v.patch == 0):
                major_count += 1
            elif version_entry.release_type == "minor" or v.patch == 0:
                minor_count += 1
            else:
                patch_count += 1

            total_changes += len(version_entry.changes)

            for change in version_entry.changes:
                change_type_dist[change.change_type.value] += 1
                if change.scope:
                    scope_counts[change.scope] += 1

            month_key = version_entry.timestamp[:7]
            version_freq[month_key] += 1

        most_active_scope = max(scope_counts.items(), key=lambda x: x[1])[0] if scope_counts else ""

        avg_changes = total_changes / len(self.history.versions) if self.history.versions else 0

        recent_versions = [
            v for v in self.history.versions
            if datetime.fromisoformat(v.timestamp) > datetime.now() - timedelta(days=30)
        ]
        recent_velocity = len(recent_versions) / 4.0 if recent_versions else 0

        return VersionStatistics(
            total_versions=len(self.history.versions),
            major_versions=major_count,
            minor_versions=minor_count,
            patch_versions=patch_count,
            prerelease_versions=prerelease_count,
            average_changes_per_version=round(avg_changes, 2),
            most_active_scope=most_active_scope,
            change_type_distribution=dict(change_type_dist),
            version_frequency=dict(version_freq),
            recent_velocity=round(recent_velocity, 2)
        )

    def check_compatibility(self, from_version: str, to_version: str) -> Dict[str, Any]:
        from_ver = SemanticVersion.parse(from_version)
        to_ver = SemanticVersion.parse(to_version)

        compatibility_result = {
            "from_version": from_version,
            "to_version": to_version,
            "compatible": True,
            "breaking_changes": [],
            "deprecations": [],
            "migration_required": False,
            "migration_guide": ""
        }

        from_entry = None
        to_entry = None
        for v in self.history.versions:
            if v.version == from_version:
                from_entry = v
            if v.version == to_version:
                to_entry = v

        if to_entry:
            compatibility_result["compatible"] = to_entry.compatibility_level != CompatibilityLevel.BREAKING
            compatibility_result["deprecations"] = to_entry.deprecation_warnings
            compatibility_result["migration_guide"] = to_entry.migration_guide
            compatibility_result["migration_required"] = len(to_entry.deprecation_warnings) > 0

            breaking_changes = [c for c in to_entry.changes if c.breaking]
            compatibility_result["breaking_changes"] = [
                {
                    "description": c.description,
                    "scope": c.scope,
                    "file_paths": c.file_paths
                }
                for c in breaking_changes
            ]

        if from_ver.major != to_ver.major:
            compatibility_result["compatible"] = False
            compatibility_result["migration_required"] = True

        return compatibility_result

    def get_status(self) -> Dict[str, Any]:
        stats = self.calculate_statistics()
        return {
            "project_name": self.history.project_name,
            "current_version": self.history.current_version,
            "iteration_count": self.history.iteration_count,
            "total_versions": len(self.history.versions),
            "total_changes": self.history.total_changes,
            "last_iteration_time": self.history.last_iteration_time,
            "snapshots_count": len(self.history.snapshots),
            "statistics": asdict(stats)
        }

    def generate_report(self, output_path: Optional[str] = None) -> str:
        status = self.get_status()

        lines = [
            "# 版本迭代报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n## 项目信息",
            f"- 项目名称: {status['project_name']}",
            f"- 当前版本: {status['current_version']}",
            f"- 迭代次数: {status['iteration_count']}",
            f"- 版本总数: {status['total_versions']}",
            f"- 变更总数: {status['total_changes']}",
            f"- 快照数量: {status['snapshots_count']}",
        ]

        if self.history.versions:
            lines.extend([
                f"\n## 最近版本",
                "| 版本 | 时间 | 作者 | 变更数 |",
                "|------|------|------|--------|",
            ])

            for v in self.history.versions[:10]:
                lines.append(
                    f"| {v.version} | {v.timestamp[:10]} | {v.author} | {len(v.changes)} |"
                )

        report = '\n'.join(lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report

    def check_version_constraint(self, version: str, constraint_str: str) -> bool:
        try:
            version_info = SemanticVersion.parse(version)
            version_range = VersionRange.parse(constraint_str)
            return version_range.matches(version_info)
        except Exception as e:
            self.logger.error(f"版本约束检查失败: {e}")
            return False

    def resolve_version_range(self, range_str: str) -> List[str]:
        try:
            version_range = VersionRange.parse(range_str)
            matching_versions = []
            
            for version_entry in self.history.versions:
                version_info = SemanticVersion.parse(version_entry.version)
                if version_range.matches(version_info):
                    matching_versions.append(version_entry.version)
            
            return matching_versions
        except Exception as e:
            self.logger.error(f"版本范围解析失败: {e}")
            return []

    def generate_version_documentation(self, version: str, output_dir: Optional[str] = None) -> str:
        version_entry = None
        for v in self.history.versions:
            if v.version == version:
                version_entry = v
                break
        
        if not version_entry:
            return f"版本 {version} 未找到"
        
        docs_path = Path(output_dir) if output_dir else self.docs_dir / version
        docs_path.mkdir(parents=True, exist_ok=True)
        
        doc_content = self._generate_version_doc_content(version_entry)
        doc_file = docs_path / "README.md"
        
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        self.logger.info(f"版本文档已生成: {docs_path}")
        return str(docs_path)

    def _generate_version_doc_content(self, version_entry: VersionEntry) -> str:
        lines = [
            f"# {self.history.project_name} v{version_entry.version}",
            "",
            f"**发布日期**: {version_entry.timestamp[:10]}",
            f"**作者**: {version_entry.author or 'N/A'}",
            f"**提交**: {version_entry.commit_hash or 'N/A'}",
            "",
        ]
        
        if version_entry.notes:
            lines.extend([
                "## 发布说明",
                "",
                version_entry.notes,
                "",
            ])
        
        lines.extend([
            "## 变更列表",
            "",
        ])
        
        for change in version_entry.changes:
            scope = f"[{change.scope}] " if change.scope else ""
            breaking = "⚠️ " if change.breaking else ""
            lines.append(f"- {breaking}{scope}{change.description}")
        
        if version_entry.previous_version:
            lines.extend([
                "",
                f"## 上一版本",
                "",
                f"[v{version_entry.previous_version}](../{version_entry.previous_version}/)",
            ])
        
        return '\n'.join(lines)
    
    def check_quality_thresholds(self, metrics: QualityMetrics) -> List[IterationTrigger]:
        """检查质量指标是否低于阈值，返回触发的迭代触发器"""
        triggers = []
        thresholds = self.history.quality_thresholds
        
        if metrics.code_quality_score < thresholds.get("code_quality_score", 0.7):
            triggers.append(IterationTrigger(
                trigger_type=IterationTriggerType.CODE_QUALITY,
                threshold=thresholds.get("code_quality_score", 0.7),
                current_value=metrics.code_quality_score,
                triggered=True,
                details={"message": f"代码质量分数 {metrics.code_quality_score:.2f} 低于阈值 {thresholds.get('code_quality_score', 0.7):.2f}"}
            ))
        
        if metrics.test_coverage < thresholds.get("test_coverage", 60.0):
            triggers.append(IterationTrigger(
                trigger_type=IterationTriggerType.COVERAGE_RATE,
                threshold=thresholds.get("test_coverage", 60.0),
                current_value=metrics.test_coverage,
                triggered=True,
                details={"message": f"测试覆盖率 {metrics.test_coverage:.2f}% 低于阈值 {thresholds.get('test_coverage', 60.0):.2f}%"}
            ))
        
        if metrics.error_rate > thresholds.get("error_rate", 0.05):
            triggers.append(IterationTrigger(
                trigger_type=IterationTriggerType.ERROR_RATE,
                threshold=thresholds.get("error_rate", 0.05),
                current_value=metrics.error_rate,
                triggered=True,
                details={"message": f"错误率 {metrics.error_rate:.2%} 超过阈值 {thresholds.get('error_rate', 0.05):.2%}"}
            ))
        
        if metrics.health_score < thresholds.get("health_score", 0.75):
            triggers.append(IterationTrigger(
                trigger_type=IterationTriggerType.HEALTH_SCORE,
                threshold=thresholds.get("health_score", 0.75),
                current_value=metrics.health_score,
                triggered=True,
                details={"message": f"健康分数 {metrics.health_score:.2f} 低于阈值 {thresholds.get('health_score', 0.75):.2f}"}
            ))
        
        overall_score = metrics.calculate_overall_score()
        if overall_score < thresholds.get("overall_score", 0.7):
            triggers.append(IterationTrigger(
                trigger_type=IterationTriggerType.QUALITY_THRESHOLD,
                threshold=thresholds.get("overall_score", 0.7),
                current_value=overall_score,
                triggered=True,
                details={"message": f"综合质量分数 {overall_score:.2f} 低于阈值 {thresholds.get('overall_score', 0.7):.2f}"}
            ))
        
        return triggers
    
    def record_quality_metrics(self, metrics: QualityMetrics) -> None:
        """记录质量指标到历史"""
        self.history.quality_metrics_history.append(metrics)
        self._save_history()
        self.logger.info(f"已记录质量指标，综合分数: {metrics.calculate_overall_score():.3f}")
    
    def get_latest_quality_metrics(self) -> Optional[QualityMetrics]:
        """获取最新的质量指标"""
        if self.history.quality_metrics_history:
            return self.history.quality_metrics_history[-1]
        return None
    
    def create_improvement_task(
        self,
        title: str,
        description: str,
        priority: ImprovementTaskPriority,
        category: str,
        affected_components: List[str] = None,
        estimated_effort: str = "medium",
        dependencies: List[str] = None,
        tags: List[str] = None,
        iteration_id: str = ""
    ) -> ImprovementTask:
        """创建改进任务"""
        task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.history.improvement_tasks) + 1}"
        
        task = ImprovementTask(
            task_id=task_id,
            title=title,
            description=description,
            priority=priority,
            category=category,
            affected_components=affected_components or [],
            estimated_effort=estimated_effort,
            dependencies=dependencies or [],
            tags=tags or [],
            iteration_id=iteration_id,
            metrics_before=self.get_latest_quality_metrics()
        )
        
        self.history.improvement_tasks.append(task)
        self._save_history()
        
        self.logger.info(f"已创建改进任务: {task_id} - {title}")
        return task
    
    def auto_create_improvement_tasks(self, triggers: List[IterationTrigger]) -> List[ImprovementTask]:
        """根据触发的条件自动创建改进任务"""
        tasks = []
        
        for trigger in triggers:
            if trigger.trigger_type == IterationTriggerType.CODE_QUALITY:
                task = self.create_improvement_task(
                    title="提升代码质量",
                    description=f"代码质量分数 {trigger.current_value:.2f} 低于阈值 {trigger.threshold:.2f}，需要重构或优化代码",
                    priority=ImprovementTaskPriority.HIGH,
                    category="code_quality",
                    affected_components=["codebase"],
                    estimated_effort="high",
                    tags=["quality", "refactoring"]
                )
                tasks.append(task)
            
            elif trigger.trigger_type == IterationTriggerType.COVERAGE_RATE:
                task = self.create_improvement_task(
                    title="增加测试覆盖率",
                    description=f"测试覆盖率 {trigger.current_value:.2f}% 低于阈值 {trigger.threshold:.2f}%，需要补充测试用例",
                    priority=ImprovementTaskPriority.HIGH,
                    category="testing",
                    affected_components=["tests"],
                    estimated_effort="medium",
                    tags=["testing", "coverage"]
                )
                tasks.append(task)
            
            elif trigger.trigger_type == IterationTriggerType.ERROR_RATE:
                task = self.create_improvement_task(
                    title="降低错误率",
                    description=f"错误率 {trigger.current_value:.2%} 超过阈值 {trigger.threshold:.2%}，需要修复错误",
                    priority=ImprovementTaskPriority.CRITICAL,
                    category="bug_fix",
                    affected_components=["codebase"],
                    estimated_effort="high",
                    tags=["bugfix", "stability"]
                )
                tasks.append(task)
            
            elif trigger.trigger_type == IterationTriggerType.HEALTH_SCORE:
                task = self.create_improvement_task(
                    title="提升系统健康度",
                    description=f"健康分数 {trigger.current_value:.2f} 低于阈值 {trigger.threshold:.2f}，需要综合优化",
                    priority=ImprovementTaskPriority.HIGH,
                    category="health",
                    affected_components=["system"],
                    estimated_effort="high",
                    tags=["health", "optimization"]
                )
                tasks.append(task)
            
            elif trigger.trigger_type == IterationTriggerType.QUALITY_THRESHOLD:
                task = self.create_improvement_task(
                    title="提升综合质量",
                    description=f"综合质量分数 {trigger.current_value:.2f} 低于阈值 {trigger.threshold:.2f}，需要全面改进",
                    priority=ImprovementTaskPriority.HIGH,
                    category="quality",
                    affected_components=["codebase", "tests", "docs"],
                    estimated_effort="high",
                    tags=["quality", "improvement"]
                )
                tasks.append(task)
        
        return tasks
    
    def update_improvement_task(
        self,
        task_id: str,
        status: str = None,
        assigned_to: str = None,
        metrics_after: QualityMetrics = None
    ) -> Optional[ImprovementTask]:
        """更新改进任务状态"""
        for task in self.history.improvement_tasks:
            if task.task_id == task_id:
                if status:
                    task.status = status
                    if status == "completed":
                        task.completed_at = datetime.now()
                
                if assigned_to:
                    task.assigned_to = assigned_to
                
                if metrics_after:
                    task.metrics_after = metrics_after
                    if task.metrics_before:
                        before_score = task.metrics_before.calculate_overall_score()
                        after_score = metrics_after.calculate_overall_score()
                        task.impact_score = after_score - before_score
                
                task.updated_at = datetime.now()
                self._save_history()
                
                self.logger.info(f"已更新任务: {task_id}")
                return task
        
        return None
    
    def get_pending_improvement_tasks(self) -> List[ImprovementTask]:
        """获取待处理的改进任务"""
        return [t for t in self.history.improvement_tasks if t.status == "pending"]
    
    def start_iteration_with_progress(
        self,
        triggers: List[IterationTrigger],
        bump_type: VersionBumpType = None
    ) -> IterationProgress:
        """开始带进度跟踪的迭代"""
        iteration_id = f"ITER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.history.iteration_count + 1}"
        
        if not bump_type:
            if any(t.trigger_type in [IterationTriggerType.SECURITY_ALERT, IterationTriggerType.ERROR_RATE] for t in triggers):
                bump_type = VersionBumpType.PATCH
            elif any(t.trigger_type in [IterationTriggerType.PERFORMANCE_DEGRADATION, IterationTriggerType.CODE_QUALITY] for t in triggers):
                bump_type = VersionBumpType.MINOR
            else:
                bump_type = VersionBumpType.PATCH
        
        new_version = self.bump_version(bump_type)
        
        snapshot = self.create_snapshot(str(self.get_current_version()), f"Pre-iteration snapshot for {iteration_id}")
        
        progress = IterationProgress(
            iteration_id=iteration_id,
            version=new_version,
            status=IterationStatus.IN_PROGRESS,
            current_phase=IterationPhase.TRIGGER_DETECTION,
            phases_pending=[
                IterationPhase.QUALITY_ASSESSMENT,
                IterationPhase.TASK_GENERATION,
                IterationPhase.TASK_EXECUTION,
                IterationPhase.VALIDATION,
                IterationPhase.DEPLOYMENT,
                IterationPhase.POST_MONITORING
            ],
            metrics_snapshot=self.get_latest_quality_metrics(),
            triggers=[t.trigger_type for t in triggers],
            rollback_snapshot_id=snapshot.snapshot_id
        )
        
        self.history.current_iteration = progress
        self.history.iteration_triggers.extend(triggers)
        self._save_history()
        
        self.logger.info(f"已开始迭代: {iteration_id}, 目标版本: {new_version}")
        return progress
    
    def update_iteration_progress(
        self,
        phase: IterationPhase = None,
        status: IterationStatus = None,
        error: Dict[str, Any] = None,
        warning: Dict[str, Any] = None
    ) -> Optional[IterationProgress]:
        """更新迭代进度"""
        if not self.history.current_iteration:
            return None
        
        progress = self.history.current_iteration
        
        if phase:
            if phase not in progress.phases_completed:
                progress.phases_completed.append(progress.current_phase)
                progress.current_phase = phase
                if phase in progress.phases_pending:
                    progress.phases_pending.remove(phase)
        
        if status:
            progress.status = status
            if status == IterationStatus.COMPLETED:
                progress.completed_at = datetime.now()
                progress.progress_percentage = 100.0
                self.history.iteration_progress_history.append(progress)
                self.history.current_iteration = None
        
        if error:
            progress.errors.append(error)
        
        if warning:
            progress.warnings.append(warning)
        
        total_phases = len(IterationPhase)
        completed_phases = len(progress.phases_completed)
        progress.progress_percentage = (completed_phases / total_phases) * 100.0
        
        progress.updated_at = datetime.now()
        self._save_history()
        
        return progress
    
    def complete_iteration_phase(self, phase: IterationPhase, tasks_completed: int = 0) -> Optional[IterationProgress]:
        """完成迭代阶段"""
        next_phase_map = {
            IterationPhase.TRIGGER_DETECTION: IterationPhase.QUALITY_ASSESSMENT,
            IterationPhase.QUALITY_ASSESSMENT: IterationPhase.TASK_GENERATION,
            IterationPhase.TASK_GENERATION: IterationPhase.TASK_EXECUTION,
            IterationPhase.TASK_EXECUTION: IterationPhase.VALIDATION,
            IterationPhase.VALIDATION: IterationPhase.DEPLOYMENT,
            IterationPhase.DEPLOYMENT: IterationPhase.POST_MONITORING,
            IterationPhase.POST_MONITORING: None
        }
        
        next_phase = next_phase_map.get(phase)
        
        if next_phase:
            return self.update_iteration_progress(phase=next_phase, status=None)
        else:
            return self.update_iteration_progress(status=IterationStatus.COMPLETED)
    
    def get_iteration_progress(self) -> Optional[IterationProgress]:
        """获取当前迭代进度"""
        return self.history.current_iteration
    
    def rollback_iteration(self) -> bool:
        """回滚当前迭代"""
        if not self.history.current_iteration:
            self.logger.warning("没有正在进行的迭代")
            return False
        
        progress = self.history.current_iteration
        
        if not progress.rollback_available or not progress.rollback_snapshot_id:
            self.logger.error("当前迭代不支持回滚")
            return False
        
        success = self.restore_snapshot(progress.rollback_snapshot_id)
        
        if success:
            progress.status = IterationStatus.ROLLED_BACK
            progress.completed_at = datetime.now()
            self.history.iteration_progress_history.append(progress)
            self.history.current_iteration = None
            self._save_history()
            
            self.logger.info(f"已回滚迭代: {progress.iteration_id}")
        
        return success
    
    def quality_driven_iteration(
        self,
        metrics: QualityMetrics,
        author: str = "",
        auto_create_tasks: bool = True
    ) -> Dict[str, Any]:
        """质量驱动的自动迭代"""
        result = {
            "triggered": False,
            "triggers": [],
            "tasks_created": [],
            "iteration_started": False,
            "iteration_progress": None
        }
        
        self.record_quality_metrics(metrics)
        
        triggers = self.check_quality_thresholds(metrics)
        
        if not triggers:
            self.logger.info("质量指标正常，无需触发迭代")
            return result
        
        result["triggered"] = True
        result["triggers"] = triggers
        
        self.logger.info(f"检测到 {len(triggers)} 个质量触发条件")
        
        if auto_create_tasks:
            tasks = self.auto_create_improvement_tasks(triggers)
            result["tasks_created"] = tasks
            self.logger.info(f"已自动创建 {len(tasks)} 个改进任务")
        
        progress = self.start_iteration_with_progress(triggers)
        result["iteration_started"] = True
        result["iteration_progress"] = progress
        
        return result
    
    def integrate_with_sanliu_workflow(self, province: str, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """集成到三省六部工作流程"""
        result = {
            "province": province,
            "action": action,
            "success": False,
            "data": {}
        }
        
        if province == "menxiasheng":
            if action == "quality_gate_check":
                metrics = data.get("metrics")
                if metrics:
                    triggers = self.check_quality_thresholds(metrics)
                    result["data"]["passed"] = len(triggers) == 0
                    result["data"]["triggers"] = triggers
                    result["success"] = True
            
            elif action == "review_iteration":
                iteration_id = data.get("iteration_id")
                if iteration_id:
                    for progress in self.history.iteration_progress_history:
                        if progress.iteration_id == iteration_id:
                            result["data"]["progress"] = progress
                            result["success"] = True
                            break
        
        elif province == "shangshusheng":
            if action == "execute_iteration":
                triggers_data = data.get("triggers", [])
                triggers = [
                    IterationTrigger(
                        trigger_type=IterationTriggerType(t.get("type")),
                        threshold=t.get("threshold", 0.0),
                        current_value=t.get("current_value", 0.0),
                        triggered=True
                    )
                    for t in triggers_data
                ]
                
                if triggers:
                    progress = self.start_iteration_with_progress(triggers)
                    result["data"]["iteration_id"] = progress.iteration_id
                    result["data"]["version"] = progress.version
                    result["success"] = True
            
            elif action == "track_progress":
                progress = self.get_iteration_progress()
                if progress:
                    result["data"]["progress"] = progress
                    result["success"] = True
            
            elif action == "create_tasks":
                triggers_data = data.get("triggers", [])
                triggers = [
                    IterationTrigger(
                        trigger_type=IterationTriggerType(t.get("type")),
                        threshold=t.get("threshold", 0.0),
                        current_value=t.get("current_value", 0.0),
                        triggered=True
                    )
                    for t in triggers_data
                ]
                
                tasks = self.auto_create_improvement_tasks(triggers)
                result["data"]["tasks"] = tasks
                result["success"] = True
        
        return result
    
    def integrate_with_fusion_engine(self, spec_path=None, max_cycles=3):
        """与 SDD-TDD 融合引擎对接
        
        Args:
            spec_path: 规范文件路径 (可选)
            max_cycles: 最大循环次数 (默认: 3)
            
        Returns:
            连续循环报告或 None
        """
        try:
            from skillscripts.pipeline.sdd_tdd_fusion_engine import SDDTDDFusionEngine
            from skillscripts.core.path_config_center import get_path_config
            
            engine = SDDTDDFusionEngine()
            
            path = Path(spec_path) if spec_path else None
            
            if path and path.exists():
                continuous_report = engine.execute_continuous_cycles(
                    path, max_cycles=max_cycles
                )
                return continuous_report
            
            pcc = get_path_config()
            specs_dir = pcc.DOCS_DIR / "specs"
            if specs_dir.exists():
                spec_files = list(specs_dir.glob("*.md"))
                if spec_files:
                    latest_spec = max(spec_files, key=lambda f: f.stat().st_mtime)
                    continuous_report = engine.execute_continuous_cycles(
                        latest_spec, max_cycles=max_cycles
                    )
                    return continuous_report
            
            return None
            
        except ImportError as e:
            self.logger.warning(f"SDD-TDD融合引擎导入失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"SDD-TDD融合引擎执行失败: {e}")
            return None

    def generate_quality_report(self, output_path: Optional[str] = None) -> str:
        """生成质量报告"""
        lines = [
            "# 质量驱动迭代报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n## 项目信息",
            f"- 项目名称: {self.history.project_name}",
            f"- 当前版本: {self.history.current_version}",
            f"- 迭代次数: {self.history.iteration_count}",
        ]
        
        latest_metrics = self.get_latest_quality_metrics()
        if latest_metrics:
            lines.extend([
                f"\n## 最新质量指标",
                f"- 代码质量分数: {latest_metrics.code_quality_score:.2f}",
                f"- 测试覆盖率: {latest_metrics.test_coverage:.2f}%",
                f"- 错误率: {latest_metrics.error_rate:.2%}",
                f"- 性能分数: {latest_metrics.performance_score:.2f}",
                f"- 安全分数: {latest_metrics.security_score:.2f}",
                f"- 健康分数: {latest_metrics.health_score:.2f}",
                f"- **综合分数: {latest_metrics.calculate_overall_score():.3f}**",
            ])
        
        pending_tasks = self.get_pending_improvement_tasks()
        if pending_tasks:
            lines.extend([
                f"\n## 待处理改进任务 ({len(pending_tasks)})",
                "",
                "| 任务ID | 标题 | 优先级 | 类别 |",
                "|--------|------|--------|------|",
            ])
            
            for task in pending_tasks[:10]:
                lines.append(
                    f"| {task.task_id} | {task.title} | {task.priority.value} | {task.category} |"
                )
        
        current_progress = self.get_iteration_progress()
        if current_progress:
            lines.extend([
                f"\n## 当前迭代进度",
                f"- 迭代ID: {current_progress.iteration_id}",
                f"- 目标版本: {current_progress.version}",
                f"- 状态: {current_progress.status.value}",
                f"- 当前阶段: {current_progress.current_phase.value}",
                f"- 进度: {current_progress.progress_percentage:.1f}%",
            ])
        
        report = '\n'.join(lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report


if __name__ == '__main__':
    print("版本迭代器核心模块已加载")
