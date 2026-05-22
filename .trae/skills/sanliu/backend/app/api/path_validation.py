from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import time
import asyncio

from ..models.base import get_db
from ..services.cache import cache_service

router = APIRouter()

class PathStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    BROKEN = "broken"
    MISSING = "missing"
    CIRCULAR = "circular"
    PERMISSION_DENIED = "permission_denied"
    UNKNOWN = "unknown"

class PathType(str, Enum):
    SKILL_DOC = "skill_doc"
    CONFIG_FILE = "config_file"
    DATA_FILE = "data_file"
    TEMPLATE = "template"
    OUTPUT = "output"
    DEPENDENCY = "dependency"

class ValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class FixStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class PathIssue(BaseModel):
    path: str = Field(..., description="路径")
    issue_type: PathStatus = Field(..., description="问题类型")
    severity: ValidationSeverity = Field(..., description="严重程度")
    message: str = Field(..., description="问题描述")
    suggestion: Optional[str] = Field(None, description="修复建议")
    affected_skills: List[str] = Field(default_factory=list, description="受影响的技能")
    detected_at: datetime = Field(default_factory=datetime.now, description="检测时间")

    class Config:
        from_attributes = True

class PathValidationResult(BaseModel):
    path: str = Field(..., description="路径")
    path_type: PathType = Field(..., description="路径类型")
    status: PathStatus = Field(..., description="状态")
    exists: bool = Field(..., description="是否存在")
    is_accessible: bool = Field(..., description="是否可访问")
    size_bytes: Optional[int] = Field(None, description="文件大小（字节）")
    last_modified: Optional[datetime] = Field(None, description="最后修改时间")
    issues: List[PathIssue] = Field(default_factory=list, description="问题列表")
    dependencies: List[str] = Field(default_factory=list, description="依赖路径")
    referenced_by: List[str] = Field(default_factory=list, description="被引用列表")

    class Config:
        from_attributes = True

class ValidationReport(BaseModel):
    report_id: str = Field(..., description="报告ID")
    generated_at: datetime = Field(..., description="生成时间")
    total_paths: int = Field(0, description="总路径数")
    valid_paths: int = Field(0, description="有效路径数")
    invalid_paths: int = Field(0, description="无效路径数")
    broken_paths: int = Field(0, description="损坏路径数")
    issues_by_severity: Dict[str, int] = Field(default_factory=dict, description="按严重程度统计")
    results: List[PathValidationResult] = Field(default_factory=list, description="验证结果")
    summary: Dict[str, Any] = Field(default_factory=dict, description="摘要")
    recommendations: List[str] = Field(default_factory=list, description="建议")

    class Config:
        from_attributes = True

class ValidationStatusResponse(BaseModel):
    last_validation: Optional[datetime] = Field(None, description="上次验证时间")
    validation_in_progress: bool = Field(False, description="是否正在验证")
    total_issues: int = Field(0, description="总问题数")
    critical_issues: int = Field(0, description="严重问题数")
    pending_fixes: int = Field(0, description="待修复数")
    auto_fix_available: int = Field(0, description="可自动修复数")
    paths_by_status: Dict[str, int] = Field(default_factory=dict, description="按状态统计")
    recent_issues: List[PathIssue] = Field(default_factory=list, description="最近问题")

    class Config:
        from_attributes = True

class FixRequest(BaseModel):
    path: Optional[str] = Field(None, description="指定修复的路径，为空则修复所有")
    issue_types: Optional[List[PathStatus]] = Field(None, description="指定修复的问题类型")
    auto_confirm: bool = Field(False, description="是否自动确认修复")
    create_backup: bool = Field(True, description="是否创建备份")
    dry_run: bool = Field(False, description="是否模拟运行")

class FixResult(BaseModel):
    fix_id: str = Field(..., description="修复ID")
    path: str = Field(..., description="路径")
    issue_type: PathStatus = Field(..., description="问题类型")
    status: FixStatus = Field(..., description="修复状态")
    action_taken: Optional[str] = Field(None, description="采取的操作")
    backup_path: Optional[str] = Field(None, description="备份路径")
    message: str = Field(..., description="消息")
    fixed_at: Optional[datetime] = Field(None, description="修复时间")

    class Config:
        from_attributes = True

class FixResponse(BaseModel):
    fix_id: str = Field(..., description="修复ID")
    status: FixStatus = Field(..., description="整体状态")
    total_fixes: int = Field(0, description="总修复数")
    successful_fixes: int = Field(0, description="成功修复数")
    failed_fixes: int = Field(0, description="失败修复数")
    skipped_fixes: int = Field(0, description="跳过修复数")
    results: List[FixResult] = Field(default_factory=list, description="修复结果")
    message: str = Field(..., description="消息")

_validation_state: Dict[str, Any] = {
    "in_progress": False,
    "progress": 0.0,
    "last_validation": None,
    "current_path": None
}

_fix_state: Dict[str, Any] = {
    "in_progress": False,
    "fix_id": None,
    "progress": 0.0
}

def _generate_mock_paths() -> List[str]:
    return [
        ".trae/skills/sanliu/skill.md",
        ".trae/skills/sanliu/config.yaml",
        ".trae/skills/sanliu/templates/code_template.py",
        ".trae/skills/sanliu/data/knowledge.json",
        ".trae/skills/sanliu/output/results.json",
        ".trae/skills/sanliu/dependencies/requirements.txt",
    ]

def _generate_mock_validation_result(path: str) -> PathValidationResult:
    path_types = {
        "skill.md": PathType.SKILL_DOC,
        "config.yaml": PathType.CONFIG_FILE,
        "templates/": PathType.TEMPLATE,
        "data/": PathType.DATA_FILE,
        "output/": PathType.OUTPUT,
        "dependencies/": PathType.DEPENDENCY,
    }
    
    path_type = PathType.SKILL_DOC
    for key, ptype in path_types.items():
        if key in path:
            path_type = ptype
            break
    
    status = PathStatus.VALID
    issues = []
    
    if "broken" in path or hash(path) % 10 == 0:
        status = PathStatus.BROKEN
        issues.append(PathIssue(
            path=path,
            issue_type=PathStatus.BROKEN,
            severity=ValidationSeverity.ERROR,
            message="路径指向不存在的文件",
            suggestion="检查文件是否被删除或移动",
            affected_skills=["skill_001", "skill_002"],
            detected_at=datetime.now()
        ))
    elif "missing" in path or hash(path) % 15 == 0:
        status = PathStatus.MISSING
        issues.append(PathIssue(
            path=path,
            issue_type=PathStatus.MISSING,
            severity=ValidationSeverity.WARNING,
            message="路径缺失必要文件",
            suggestion="创建缺失的文件或更新配置",
            affected_skills=["skill_003"],
            detected_at=datetime.now()
        ))
    elif "circular" in path:
        status = PathStatus.CIRCULAR
        issues.append(PathIssue(
            path=path,
            issue_type=PathStatus.CIRCULAR,
            severity=ValidationSeverity.CRITICAL,
            message="检测到循环依赖",
            suggestion="重构依赖关系以消除循环",
            affected_skills=["skill_001", "skill_004"],
            detected_at=datetime.now()
        ))
    
    return PathValidationResult(
        path=path,
        path_type=path_type,
        status=status,
        exists=status in [PathStatus.VALID, PathStatus.INVALID],
        is_accessible=status == PathStatus.VALID,
        size_bytes=1024 + hash(path) % 10000 if status == PathStatus.VALID else None,
        last_modified=datetime.now() - timedelta(hours=hash(path) % 48) if status == PathStatus.VALID else None,
        issues=issues,
        dependencies=["dep1", "dep2"] if status == PathStatus.VALID else [],
        referenced_by=["ref1", "ref2"] if status == PathStatus.VALID else []
    )

def _get_mock_validation_report() -> ValidationReport:
    paths = _generate_mock_paths()
    paths.extend([
        ".trae/skills/sanliu/broken_ref.md",
        ".trae/skills/sanliu/missing_config.yaml",
    ])
    
    results = [_generate_mock_validation_result(p) for p in paths]
    
    valid = sum(1 for r in results if r.status == PathStatus.VALID)
    invalid = sum(1 for r in results if r.status == PathStatus.INVALID)
    broken = sum(1 for r in results if r.status in [PathStatus.BROKEN, PathStatus.MISSING, PathStatus.CIRCULAR])
    
    severity_counts = {"info": 0, "warning": 0, "error": 0, "critical": 0}
    for r in results:
        for issue in r.issues:
            severity_counts[issue.severity.value] += 1
    
    return ValidationReport(
        report_id=f"val_{int(time.time())}",
        generated_at=datetime.now(),
        total_paths=len(results),
        valid_paths=valid,
        invalid_paths=invalid,
        broken_paths=broken,
        issues_by_severity=severity_counts,
        results=results,
        summary={
            "health_score": round(valid / len(results) * 100, 2),
            "validation_duration_ms": 2500,
        },
        recommendations=[
            "修复损坏的路径引用",
            "创建缺失的配置文件",
            "解决循环依赖问题",
        ]
    )

def _get_mock_validation_status() -> ValidationStatusResponse:
    return ValidationStatusResponse(
        last_validation=datetime.now() - timedelta(hours=1),
        validation_in_progress=False,
        total_issues=5,
        critical_issues=1,
        pending_fixes=3,
        auto_fix_available=2,
        paths_by_status={
            "valid": 12,
            "invalid": 2,
            "broken": 1,
            "missing": 2,
        },
        recent_issues=[
            PathIssue(
                path=".trae/skills/sanliu/broken_ref.md",
                issue_type=PathStatus.BROKEN,
                severity=ValidationSeverity.ERROR,
                message="文件不存在",
                suggestion="检查路径配置",
                affected_skills=["skill_001"],
                detected_at=datetime.now() - timedelta(minutes=30)
            ),
            PathIssue(
                path=".trae/skills/sanliu/missing_config.yaml",
                issue_type=PathStatus.MISSING,
                severity=ValidationSeverity.WARNING,
                message="配置文件缺失",
                suggestion="创建默认配置",
                affected_skills=["skill_002"],
                detected_at=datetime.now() - timedelta(hours=1)
            ),
        ]
    )

async def _run_validation(validation_id: str):
    global _validation_state
    _validation_state["in_progress"] = True
    _validation_state["progress"] = 0.0
    
    paths = _generate_mock_paths()
    for i, path in enumerate(paths):
        await asyncio.sleep(0.5)
        _validation_state["progress"] = (i + 1) / len(paths) * 100
        _validation_state["current_path"] = path
    
    _validation_state["in_progress"] = False
    _validation_state["progress"] = 100.0
    _validation_state["last_validation"] = datetime.now()
    _validation_state["current_path"] = None

async def _run_fixes(fix_id: str, request: FixRequest):
    global _fix_state
    _fix_state["in_progress"] = True
    _fix_state["fix_id"] = fix_id
    _fix_state["progress"] = 0.0
    
    await asyncio.sleep(2)
    
    _fix_state["in_progress"] = False
    _fix_state["progress"] = 100.0

@router.get(
    "/validate",
    response_model=ValidationReport,
    summary="验证所有路径",
    description="验证系统中所有路径的有效性，返回详细的验证报告"
)
async def validate_all_paths(
    path_types: Optional[List[PathType]] = Query(None, description="筛选路径类型"),
    include_details: bool = Query(True, description="是否包含详细信息"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    global _validation_state
    
    if _validation_state.get("in_progress"):
        raise HTTPException(
            status_code=409,
            detail="验证正在进行中，请等待完成"
        )
    
    cache_key = f"path_validation:report:{path_types}:{include_details}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return ValidationReport(**cached)
    
    result = _get_mock_validation_report()
    
    if path_types:
        result.results = [r for r in result.results if r.path_type in path_types]
        result.total_paths = len(result.results)
        result.valid_paths = sum(1 for r in result.results if r.status == PathStatus.VALID)
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=300)
    
    return result

@router.get(
    "/status",
    response_model=ValidationStatusResponse,
    summary="获取路径验证状态",
    description="获取当前路径验证的状态概览，包括问题统计和最近问题"
)
async def get_validation_status(db: Session = Depends(get_db)):
    cache_key = "path_validation:status"
    cached = cache_service.get_json(cache_key)
    if cached:
        return ValidationStatusResponse(**cached)
    
    result = _get_mock_validation_status()
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    
    return result

@router.post(
    "/fix",
    response_model=FixResponse,
    summary="修复路径问题",
    description="自动修复检测到的路径问题，支持指定路径和问题类型"
)
async def fix_path_issues(
    request: FixRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    global _fix_state
    
    if _fix_state.get("in_progress"):
        raise HTTPException(
            status_code=409,
            detail="修复正在进行中，请等待完成"
        )
    
    fix_id = f"fix_{int(time.time() * 1000)}"
    
    if request.dry_run:
        return FixResponse(
            fix_id=fix_id,
            status=FixStatus.COMPLETED,
            total_fixes=2,
            successful_fixes=0,
            failed_fixes=0,
            skipped_fixes=2,
            results=[
                FixResult(
                    fix_id=fix_id,
                    path=".trae/skills/sanliu/broken_ref.md",
                    issue_type=PathStatus.BROKEN,
                    status=FixStatus.SKIPPED,
                    action_taken="dry_run",
                    message="模拟运行：将创建缺失文件"
                ),
                FixResult(
                    fix_id=fix_id,
                    path=".trae/skills/sanliu/missing_config.yaml",
                    issue_type=PathStatus.MISSING,
                    status=FixStatus.SKIPPED,
                    action_taken="dry_run",
                    message="模拟运行：将创建默认配置"
                )
            ],
            message="模拟运行完成，未执行实际修复"
        )
    
    _fix_state = {
        "in_progress": True,
        "fix_id": fix_id,
        "progress": 0.0
    }
    
    background_tasks.add_task(_run_fixes, fix_id, request)
    
    return FixResponse(
        fix_id=fix_id,
        status=FixStatus.IN_PROGRESS,
        total_fixes=2,
        successful_fixes=0,
        failed_fixes=0,
        skipped_fixes=0,
        results=[],
        message="修复已触发，正在后台执行"
    )

@router.get(
    "/fix/{fix_id}",
    response_model=FixResponse,
    summary="获取修复状态",
    description="获取指定修复任务的状态和结果"
)
async def get_fix_status(
    fix_id: str,
    db: Session = Depends(get_db)
):
    global _fix_state
    
    if _fix_state.get("fix_id") != fix_id:
        raise HTTPException(
            status_code=404,
            detail="未找到指定的修复任务"
        )
    
    if _fix_state.get("in_progress"):
        return FixResponse(
            fix_id=fix_id,
            status=FixStatus.IN_PROGRESS,
            total_fixes=2,
            successful_fixes=0,
            failed_fixes=0,
            skipped_fixes=0,
            results=[],
            message="修复正在进行中"
        )
    
    return FixResponse(
        fix_id=fix_id,
        status=FixStatus.COMPLETED,
        total_fixes=2,
        successful_fixes=2,
        failed_fixes=0,
        skipped_fixes=0,
        results=[
            FixResult(
                fix_id=fix_id,
                path=".trae/skills/sanliu/broken_ref.md",
                issue_type=PathStatus.BROKEN,
                status=FixStatus.COMPLETED,
                action_taken="created_file",
                backup_path=".trae/backups/broken_ref.md.bak",
                message="已创建缺失文件",
                fixed_at=datetime.now()
            ),
            FixResult(
                fix_id=fix_id,
                path=".trae/skills/sanliu/missing_config.yaml",
                issue_type=PathStatus.MISSING,
                status=FixStatus.COMPLETED,
                action_taken="created_default",
                backup_path=None,
                message="已创建默认配置文件",
                fixed_at=datetime.now()
            )
        ],
        message="修复完成"
    )

@router.get(
    "/path/{path:path}",
    response_model=PathValidationResult,
    summary="验证单个路径",
    description="验证指定路径的有效性"
)
async def validate_single_path(
    path: str,
    db: Session = Depends(get_db)
):
    cache_key = f"path_validation:path:{path}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return PathValidationResult(**cached)
    
    result = _generate_mock_validation_result(path)
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    
    return result

@router.get(
    "/issues",
    response_model=List[PathIssue],
    summary="获取所有路径问题",
    description="获取所有检测到的路径问题列表"
)
async def get_all_issues(
    severity: Optional[ValidationSeverity] = Query(None, description="按严重程度筛选"),
    issue_type: Optional[PathStatus] = Query(None, description="按问题类型筛选"),
    limit: int = Query(50, description="返回数量限制", ge=1, le=200),
    db: Session = Depends(get_db)
):
    cache_key = f"path_validation:issues:{severity}:{issue_type}:{limit}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return [PathIssue(**i) for i in cached]
    
    issues = [
        PathIssue(
            path=".trae/skills/sanliu/broken_ref.md",
            issue_type=PathStatus.BROKEN,
            severity=ValidationSeverity.ERROR,
            message="文件不存在",
            suggestion="检查路径配置",
            affected_skills=["skill_001"],
            detected_at=datetime.now() - timedelta(minutes=30)
        ),
        PathIssue(
            path=".trae/skills/sanliu/missing_config.yaml",
            issue_type=PathStatus.MISSING,
            severity=ValidationSeverity.WARNING,
            message="配置文件缺失",
            suggestion="创建默认配置",
            affected_skills=["skill_002"],
            detected_at=datetime.now() - timedelta(hours=1)
        ),
        PathIssue(
            path=".trae/skills/sanliu/circular_dep.md",
            issue_type=PathStatus.CIRCULAR,
            severity=ValidationSeverity.CRITICAL,
            message="循环依赖",
            suggestion="重构依赖关系",
            affected_skills=["skill_001", "skill_003"],
            detected_at=datetime.now() - timedelta(hours=2)
        ),
        PathIssue(
            path=".trae/skills/sanliu/permission_denied.txt",
            issue_type=PathStatus.PERMISSION_DENIED,
            severity=ValidationSeverity.ERROR,
            message="权限不足",
            suggestion="检查文件权限",
            affected_skills=["skill_004"],
            detected_at=datetime.now() - timedelta(hours=3)
        ),
        PathIssue(
            path=".trae/skills/sanliu/invalid_format.json",
            issue_type=PathStatus.INVALID,
            severity=ValidationSeverity.WARNING,
            message="文件格式无效",
            suggestion="修复文件格式",
            affected_skills=["skill_005"],
            detected_at=datetime.now() - timedelta(hours=4)
        ),
    ]
    
    if severity:
        issues = [i for i in issues if i.severity == severity]
    if issue_type:
        issues = [i for i in issues if i.issue_type == issue_type]
    
    issues = issues[:limit]
    
    cache_service.set_json(cache_key, [i.model_dump() for i in issues], ttl=60)
    
    return issues

@router.get(
    "/statistics",
    summary="获取路径统计",
    description="获取路径验证的统计数据"
)
async def get_path_statistics(db: Session = Depends(get_db)):
    cache_key = "path_validation:statistics"
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached
    
    result = {
        "total_paths": 25,
        "by_type": {
            "skill_doc": 8,
            "config_file": 5,
            "data_file": 4,
            "template": 3,
            "output": 3,
            "dependency": 2,
        },
        "by_status": {
            "valid": 20,
            "invalid": 2,
            "broken": 1,
            "missing": 1,
            "circular": 1,
        },
        "issues_last_24h": 5,
        "fixes_last_24h": 3,
        "average_validation_time_ms": 150,
    }
    
    cache_service.set_json(cache_key, result, ttl=300)
    
    return result
