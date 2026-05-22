"""
路径配置中心 API
================

提供 PathConfigCenter 的 RESTful 接口，包括：
- 路径配置状态总览
- 所有预定义路径列表
- 路径有效性验证
- 路径问题修复
- 硬编码路径扫描
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from pathlib import Path

from ..config import settings

router = APIRouter()


class PathConfigStatusResponse(BaseModel):
    """路径配置状态响应"""
    success: bool = Field(..., description="请求是否成功")
    enabled: bool = Field(..., description="PathConfigCenter 是否启用")
    skill_root: Optional[str] = Field(None, description="技能根目录")
    docs_dir: Optional[str] = Field(None, description="文档目录")
    scripts_dir: Optional[str] = Field(None, description="脚本目录")
    reports_dir: Optional[str] = Field(None, description="报告目录")
    versions_dir: Optional[str] = Field(None, description="版本目录")
    current_version: Optional[str] = Field(None, description="当前版本号")
    env_overrides: Dict[str, str] = Field(default_factory=dict, description="环境变量覆盖")


class PathInfoItem(BaseModel):
    """单个路径信息项"""
    name: str = Field(..., description="路径名称")
    path: str = Field(..., description="路径字符串")
    exists: bool = Field(..., description="是否存在")
    is_dir: Optional[bool] = Field(None, description="是否为目录")
    is_valid: bool = Field(..., description="是否有效")
    issues: List[str] = Field(default_factory=list, description="问题列表")


class AllPathsResponse(BaseModel):
    """所有路径列表响应"""
    success: bool = Field(..., description="请求是否成功")
    total: int = Field(..., description="总路径数")
    paths: List[PathInfoItem] = Field(default_factory=list, description="路径列表")


class ValidatePathsResponse(BaseModel):
    """路径验证响应"""
    success: bool = Field(..., description="请求是否成功")
    total: int = Field(..., description="总路径数")
    valid: int = Field(..., description="有效路径数")
    invalid: int = Field(..., description="无效路径数")
    details: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="详细验证结果")


class FixResultItem(BaseModel):
    """单个修复结果"""
    name: str = Field(..., description="路径名称")
    path: str = Field(..., description="路径")
    status: str = Field(..., description="修复状态")
    action_taken: Optional[str] = Field(None, description="执行的操作")
    message: str = Field(..., description="消息")


class FixPathsResponse(BaseModel):
    """路径修复响应"""
    success: bool = Field(..., description="请求是否成功")
    total_issues: int = Field(0, description="总问题数")
    fixed: int = Field(0, description="已修复数")
    failed: int = Field(0, description="失败数")
    results: List[FixResultItem] = Field(default_factory=list, description="修复结果列表")
    message: str = Field(..., description="总体消息")


class HardcodedPathItem(BaseModel):
    """硬编码路径条目"""
    file_path: str = Field(..., description="文件路径")
    line_number: int = Field(..., description="行号")
    line_content: str = Field(..., description="行内容")
    matched_path: str = Field(..., description="匹配到的路径")
    pattern_type: str = Field(..., description="模式类型")


class ScanHardcodedResponse(BaseModel):
    """硬编码扫描响应"""
    success: bool = Field(..., description="请求是否成功")
    directory: str = Field(..., description="扫描的目录")
    files_scanned: int = Field(0, description="扫描文件数")
    total_issues: int = Field(0, description="发现问题总数")
    issues: List[HardcodedPathItem] = Field(default_factory=list, description="问题列表")


@router.get(
    "/path-config/status",
    response_model=PathConfigStatusResponse,
    summary="获取路径配置总览状态",
    description="获取 PathConfigCenter 的配置总览，包括所有关键路径和当前版本"
)
async def get_path_config_status():
    try:
        status = settings.get_path_status()
        return PathConfigStatusResponse(
            success=True,
            enabled=status.get("enabled", False),
            skill_root=status.get("skill_root"),
            docs_dir=status.get("docs_dir"),
            scripts_dir=status.get("scripts_dir"),
            reports_dir=status.get("reports_dir"),
            versions_dir=status.get("versions_dir"),
            current_version=status.get("current_version"),
            env_overrides=status.get("env_overrides", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取路径配置状态失败: {str(e)}")


@router.get(
    "/path-config/paths",
    response_model=AllPathsResponse,
    summary="列出所有预定义路径",
    description="列出 PathConfigCenter 中所有预定义路径及其当前状态"
)
async def list_all_paths():
    pcc = settings.get_path_config_center()
    if not pcc:
        return AllPathsResponse(success=False, total=0, paths=[])

    paths = []
    for name, path_obj in pcc._all_paths.items():
        is_valid, issues = pcc.validate_path(path_obj)
        paths.append(PathInfoItem(
            name=name,
            path=str(path_obj),
            exists=path_obj.exists(),
            is_dir=path_obj.is_dir() if path_obj.exists() else None,
            is_valid=is_valid,
            issues=issues
        ))

    return AllPathsResponse(
        success=True,
        total=len(paths),
        paths=paths
    )


@router.post(
    "/path-config/validate",
    response_model=ValidatePathsResponse,
    summary="验证所有预定义路径",
    description="验证 PathConfigCenter 中所有预定义路径的有效性，返回详细报告"
)
async def validate_all_paths():
    pcc = settings.get_path_config_center()
    if not pcc:
        raise HTTPException(status_code=503, detail="PathConfigCenter 未启用")

    result = pcc.validate_all_paths()
    return ValidatePathsResponse(
        success=True,
        total=result["total"],
        valid=result["valid"],
        invalid=result["invalid"],
        details=result["details"]
    )


@router.post(
    "/path-config/fix",
    response_model=FixPathsResponse,
    summary="修复检测到的路径问题",
    description="扫描并尝试修复检测到的路径问题（如创建缺失目录）"
)
async def fix_path_issues():
    pcc = settings.get_path_config_center()
    if not pcc:
        raise HTTPException(status_code=503, detail="PathConfigCenter 未启用")

    results = []
    fixed_count = 0
    failed_count = 0

    for name, path_obj in pcc._all_paths.items():
        is_valid, issues = pcc.validate_path(path_obj)
        if not is_valid:
            action_taken = None
            status = "failed"
            message = f"无法自动修复: {'; '.join(issues)}"

            if not path_obj.exists() and name not in ("SKILL_ROOT", "SCRIPTS_DIR", "BACKEND_DIR", "FRONTEND_DIR"):
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                    action_taken = "created_directory"
                    status = "fixed"
                    message = f"已创建缺失目录: {path_obj}"
                    fixed_count += 1
                except OSError as e:
                    message = f"创建目录失败: {e}"
                    failed_count += 1
            else:
                failed_count += 1

            results.append(FixResultItem(
                name=name,
                path=str(path_obj),
                status=status,
                action_taken=action_taken,
                message=message
            ))

    if not results:
        return FixPathsResponse(
            success=True,
            total_issues=0,
            fixed=0,
            failed=0,
            results=[],
            message="所有路径正常，无需修复"
        )

    return FixPathsResponse(
        success=True,
        total_issues=len(results),
        fixed=fixed_count,
        failed=failed_count,
        results=results,
        message=f"修复完成: {fixed_count} 成功, {failed_count} 失败"
    )


@router.get(
    "/path-config/hardcoded-scan",
    response_model=ScanHardcodedResponse,
    summary="扫描硬编码路径",
    description="扫描指定目录中的 Python 文件，检测可能存在的硬编码路径"
)
async def scan_hardcoded_paths(directory: str = Query("", description="要扫描的目录路径，为空则扫描脚本目录")):
    pcc = settings.get_path_config_center()
    if not pcc:
        raise HTTPException(status_code=503, detail="PathConfigCenter 未启用")

    scan_dir = Path(directory) if directory else pcc.SCRIPTS_DIR

    if not scan_dir.exists():
        raise HTTPException(status_code=404, detail=f"扫描目录不存在: {scan_dir}")

    if not scan_dir.is_dir():
        raise HTTPException(status_code=400, detail=f"指定的路径不是目录: {scan_dir}")

    all_issues = pcc.fix_all_hardcoded(scan_dir)

    issues = [
        HardcodedPathItem(
            file_path=issue.get("file_path", ""),
            line_number=issue.get("line_number", 0),
            line_content=issue.get("line_content", ""),
            matched_path=issue.get("matched_path", ""),
            pattern_type=issue.get("pattern_type", "")
        )
        for issue in all_issues
    ]

    py_files = list(scan_dir.rglob('*.py'))
    py_files = [f for f in py_files if not f.name.startswith('__')]

    return ScanHardcodedResponse(
        success=True,
        directory=str(scan_dir),
        files_scanned=len(py_files),
        total_issues=len(issues),
        issues=issues
    )
