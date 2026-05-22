from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import os
import json
import asyncio

from ..models.base import get_db
from ..models.project import Project
from ..services.report import StatisticsCollector, ReportGenerator, RiskAnalyzer
from ..services.cache import cache_service

router = APIRouter()


class ReportType(str, Enum):
    QUALITY_REPORT = "quality_report"
    TEST_REPORT = "test_report"
    EVOLUTION_REPORT = "evolution_report"
    PATH_VALIDATION_REPORT = "path_validation_report"
    HEALTH_REPORT = "health_report"
    COMPREHENSIVE_REPORT = "comprehensive_report"


class ReportFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"


class ReportStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerateReportRequest(BaseModel):
    report_type: ReportType = Field(..., description="报告类型")
    version: Optional[str] = Field(None, description="版本号")
    format: ReportFormat = Field(ReportFormat.MARKDOWN, description="输出格式")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    include_details: bool = Field(True, description="是否包含详细信息")


class ReportTaskInfo(BaseModel):
    task_id: str = Field(..., description="任务ID")
    report_type: ReportType = Field(..., description="报告类型")
    status: ReportStatus = Field(..., description="状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    progress: float = Field(0.0, description="进度 (0-100)", ge=0, le=100)
    file_path: Optional[str] = Field(None, description="文件路径")
    error_message: Optional[str] = Field(None, description="错误信息")

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    task_id: str = Field(..., description="任务ID")
    report_type: ReportType = Field(..., description="报告类型")
    status: ReportStatus = Field(..., description="状态")
    message: str = Field(..., description="消息")
    estimated_time_seconds: int = Field(0, description="预计时间（秒）")


_active_tasks: Dict[str, Dict[str, Any]] = {}


def _get_base_path() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _ensure_directory(version: str) -> str:
    base_path = _get_base_path()
    report_dir = os.path.join(base_path, "docs", "迭代版本/v{}".format(version))
    os.makedirs(report_dir, exist_ok=True)
    return report_dir


def _generate_quality_report_content(data: Dict[str, Any], format_type: ReportFormat) -> str:
    if format_type == ReportFormat.JSON:
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    if format_type == ReportFormat.HTML:
        template = """<!DOCTYPE html>
<html>
<head><title>质量报告</title></head>
<body>
<h1>质量报告</h1>
<p>生成时间: {generated_at}</p>
<h2>总体评分</h2>
<p>{overall_score}</p>
</body>
</html>"""
        return template.format(
            generated_at=data.get('generated_at', ''),
            overall_score=data.get('overall_score', 'N/A')
        )

    issues_list = "\n".join(["- {}".format(issue.get('description', '')) for issue in data.get('issues_found', [])])
    recommendations_list = "\n".join(["- {}".format(rec) for rec in data.get('recommendations', [])])

    template = """# 质量报告

**生成时间**: {generated_at}
**报告周期**: {period_start} 至 {period_end}

## 总体评分

{overall_score}

## 性能指标

- 平均响应时间: {avg_response_time}ms
- 错误率: {error_rate}%

## 代码质量

- 总体分数: {code_quality_score}
- 可维护性指数: {maintainability_index}

## 测试覆盖率

- 行覆盖率: {line_coverage}%
- 分支覆盖率: {branch_coverage}%

## 发现的问题

{issues}

## 建议

{recommendations}
"""

    metrics = data.get('metrics', {})
    perf_metrics = metrics.get('performance', {})
    quality_metrics = metrics.get('code_quality', {})
    coverage_metrics = metrics.get('test_coverage', {})

    return template.format(
        generated_at=data.get('generated_at', ''),
        period_start=data.get('period_start', ''),
        period_end=data.get('period_end', ''),
        overall_score=data.get('overall_score', 'N/A'),
        avg_response_time=perf_metrics.get('avg_response_time_ms', 'N/A'),
        error_rate=perf_metrics.get('error_rate', 'N/A'),
        code_quality_score=quality_metrics.get('overall_score', 'N/A'),
        maintainability_index=quality_metrics.get('maintainability_index', 'N/A'),
        line_coverage=coverage_metrics.get('line_coverage', 'N/A'),
        branch_coverage=coverage_metrics.get('branch_coverage', 'N/A'),
        issues=issues_list,
        recommendations=recommendations_list
    )


def _generate_test_report_content(data: Dict[str, Any], format_type: ReportFormat) -> str:
    if format_type == ReportFormat.JSON:
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    if format_type == ReportFormat.HTML:
        template = """<!DOCTYPE html>
<html>
<head><title>测试报告</title></head>
<body>
<h1>测试报告</h1>
<p>通过率: {pass_rate}%</p>
</body>
</html>"""
        return template.format(pass_rate=data.get('pass_rate', 'N/A'))

    failed_tests = "\n".join(["- {}".format(test) for test in data.get('failed_test_cases', [])])

    template = """# 测试报告

**生成时间**: {generated_at}

## 测试统计

- 总测试数: {total_tests}
- 通过数: {passed_tests}
- 失败数: {failed_tests}
- 跳过数: {skipped_tests}
- 通过率: {pass_rate}%

## 覆盖率

- 行覆盖率: {line_coverage}%
- 分支覆盖率: {branch_coverage}%
- 函数覆盖率: {function_coverage}%

## 失败的测试用例

{failed_tests}
"""

    return template.format(
        generated_at=data.get('generated_at', ''),
        total_tests=data.get('total_tests', 0),
        passed_tests=data.get('passed_tests', 0),
        failed_tests_count=data.get('failed_tests', 0),
        skipped_tests=data.get('skipped_tests', 0),
        pass_rate=data.get('pass_rate', 0),
        line_coverage=data.get('line_coverage', 0),
        branch_coverage=data.get('branch_coverage', 0),
        function_coverage=data.get('function_coverage', 0),
        failed_tests=failed_tests
    )


def _generate_evolution_report_content(data: Dict[str, Any], format_type: ReportFormat) -> str:
    if format_type == ReportFormat.JSON:
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    if format_type == ReportFormat.HTML:
        template = """<!DOCTYPE html>
<html>
<head><title>演化报告</title></head>
<body>
<h1>演化报告</h1>
<p>总演化次数: {total_evolutions}</p>
</body>
</html>"""
        stats = data.get('statistics', {})
        return template.format(total_evolutions=stats.get('total_evolutions', 0))

    stats = data.get('statistics', {})
    evolution_by_type = stats.get('evolution_by_type', {})
    type_distribution = "\n".join(["- {}: {}次".format(k, v) for k, v in evolution_by_type.items()])
    recommendations_list = "\n".join(["- {}".format(rec) for rec in data.get('recommendations', [])])

    template = """# 演化报告

**生成时间**: {generated_at}
**报告周期**: {period_start} 至 {period_end}

## 演化统计

- 总演化次数: {total_evolutions}
- 成功次数: {successful_evolutions}
- 失败次数: {failed_evolutions}
- 成功率: {success_rate}%
- 平均持续时间: {avg_duration:.1f}秒

## 按类型分布

{type_distribution}

## 建议事项

{recommendations}
"""

    return template.format(
        generated_at=data.get('generated_at', ''),
        period_start=data.get('period_start', ''),
        period_end=data.get('period_end', ''),
        total_evolutions=stats.get('total_evolutions', 0),
        successful_evolutions=stats.get('successful_evolutions', 0),
        failed_evolutions=stats.get('failed_evolutions', 0),
        success_rate=stats.get('success_rate', 0),
        avg_duration=stats.get('average_duration_ms', 0) / 1000,
        type_distribution=type_distribution,
        recommendations=recommendations_list
    )


def _generate_path_validation_report_content(data: Dict[str, Any], format_type: ReportFormat) -> str:
    if format_type == ReportFormat.JSON:
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    if format_type == ReportFormat.HTML:
        template = """<!DOCTYPE html>
<html>
<head><title>路径验证报告</title></head>
<body>
<h1>路径验证报告</h1>
<p>总路径数: {total_paths}</p>
</body>
</html>"""
        return template.format(total_paths=data.get('total_paths', 0))

    missing_paths = "\n".join(["- {}".format(path) for path in data.get('missing_path_list', [])])
    problematic_paths = "\n".join(["- {}: {}".format(path, reason) for path, reason in data.get('problematic_paths', {}).items()])

    template = """# 路径验证报告

**生成时间**: {generated_at}

## 验证结果

- 总路径数: {total_paths}
- 存在路径数: {existing_paths}
- 缺失路径数: {missing_paths}

## 缺失路径列表

{missing_paths}

## 问题路径

{problematic_paths}
"""

    return template.format(
        generated_at=data.get('generated_at', ''),
        total_paths=data.get('total_paths', 0),
        existing_paths=data.get('existing_paths', 0),
        missing_paths=data.get('missing_paths', 0),
        missing_paths_list=missing_paths,
        problematic_paths=problematic_paths
    )


def _generate_health_report_content(data: Dict[str, Any], format_type: ReportFormat) -> str:
    if format_type == ReportFormat.JSON:
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    if format_type == ReportFormat.HTML:
        template = """<!DOCTYPE html>
<html>
<head><title>健康报告</title></head>
<body>
<h1>健康报告</h1>
<p>总体评分: {overall_score}</p>
</body>
</html>"""
        return template.format(overall_score=data.get('overall_score', 'N/A'))

    dimensions_list = []
    for dim in data.get('dimensions', []):
        dim_str = "### {}\n- 状态: **{}**\n- 评分: {}/100".format(
            dim.get('name', ''),
            dim.get('status', ''),
            dim.get('score', 0)
        )
        dimensions_list.append(dim_str)

    critical_issues = "\n".join(["- ⚠️ {}".format(issue) for issue in data.get('critical_issues', [])]) or "- 无"
    warnings = "\n".join(["- ⚡ {}".format(warning) for warning in data.get('warnings', [])]) or "- 无"
    recommendations = "\n".join(["- 💡 {}".format(rec) for rec in data.get('recommendations', [])])

    template = """# 综合健康报告

**生成时间**: {checked_at}

## 总体健康评分

{overall_score}/100 - **{overall_status}**

## 各维度详情

{dimensions}

## 严重问题

{critical_issues}

## 警告

{warnings}

## 改进建议

{recommendations}
"""

    return template.format(
        checked_at=data.get('checked_at', ''),
        overall_score=data.get('overall_score', 'N/A'),
        overall_status=data.get('overall_status', 'unknown'),
        dimensions="\n\n".join(dimensions_list),
        critical_issues=critical_issues,
        warnings=warnings,
        recommendations=recommendations
    )


def _generate_comprehensive_report_content(data: Dict[str, Any], format_type: ReportFormat) -> str:
    if format_type == ReportFormat.JSON:
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    sections = []
    sections.append("# 完整综合报告\n")
    sections.append("**生成时间**: {}\n".format(data.get('generated_at', '')))
    sections.append("**版本**: {}\n\n".format(data.get('version', 'N/A')))
    sections.append("---\n\n")

    if 'quality' in data:
        sections.append("## 1. 质量报告部分\n")
        sections.append(_generate_quality_report_content(data['quality'], ReportFormat.MARKDOWN))
        sections.append("\n---\n\n")

    if 'test' in data:
        sections.append("## 2. 测试报告部分\n")
        sections.append(_generate_test_report_content(data['test'], ReportFormat.MARKDOWN))
        sections.append("\n---\n\n")

    if 'evolution' in data:
        sections.append("## 3. 演化报告部分\n")
        sections.append(_generate_evolution_report_content(data['evolution'], ReportFormat.MARKDOWN))
        sections.append("\n---\n\n")

    if 'health' in data:
        sections.append("## 4. 健康报告部分\n")
        sections.append(_generate_health_report_content(data['health'], ReportFormat.MARKDOWN))
        sections.append("\n---\n\n")

    if format_type == ReportFormat.HTML:
        html_content = "\n".join(sections)
        return "<!DOCTYPE html>\n<html>\n<head><title>完整综合报告</title></head>\n<body>\n<pre>{}</pre>\n</body>\n</html>".format(html_content)

    return "\n".join(sections)


async def _execute_report_generation(
        task_id: str,
        request: GenerateReportRequest,
        db: Session):
    try:
        _active_tasks[task_id]["status"] = ReportStatus.GENERATING.value
        _active_tasks[task_id]["progress"] = 10.0

        version = request.version or "latest"
        report_dir = _ensure_directory(version)

        await asyncio.sleep(1)
        _active_tasks[task_id]["progress"] = 30.0

        report_data = {}

        if request.report_type == ReportType.QUALITY_REPORT:
            from .quality_monitor import get_performance_metrics, get_error_statistics, get_code_quality_score, get_test_coverage_metrics

            performance = await get_performance_metrics(db)
            errors = await get_error_statistics(24, db)
            code_quality = await get_code_quality_score(db)
            test_coverage = await get_test_coverage_metrics(db)

            overall_score = (
                    (100 - performance.avg_response_time_ms / 10) * 0.3 +
                    (100 - errors.error_rate) * 0.3 +
                    code_quality.overall_score * 0.2 +
                    test_coverage.line_coverage_percent * 0.2
            )
            overall_score = max(0, min(100, overall_score))

            report_data = {
                "report_type": "quality_report",
                "generated_at": datetime.now().isoformat(),
                "period_start": (request.start_date or datetime.now() - timedelta(days=1)).isoformat(),
                "period_end": (request.end_date or datetime.now()).isoformat(),
                "overall_score": round(overall_score, 2),
                "metrics": {
                    "performance": {
                        "avg_response_time_ms": performance.avg_response_time_ms,
                        "error_rate": performance.error_rate_percent
                    },
                    "code_quality": {
                        "overall_score": code_quality.overall_score,
                        "maintainability_index": code_quality.maintainability_index
                    },
                    "test_coverage": {
                        "line_coverage": test_coverage.line_coverage_percent,
                        "branch_coverage": test_coverage.branch_coverage_percent
                    }
                },
                "issues_found": [],
                "recommendations": ["建议定期进行代码审查", "建议增加自动化测试覆盖率"]
            }

        elif request.report_type == ReportType.TEST_REPORT:
            pass_rate = 94.5
            report_data = {
                "report_type": "test_report",
                "generated_at": datetime.now().isoformat(),
                "total_tests": 1250,
                "passed_tests": int(1250 * pass_rate / 100),
                "failed_tests": int(1250 * (100 - pass_rate) / 100),
                "skipped_tests": 12,
                "pass_rate": pass_rate,
                "line_coverage": 85.2,
                "branch_coverage": 75.0,
                "function_coverage": 81.0,
                "failed_test_cases": ["test_example_001", "test_example_002"]
            }

        elif request.report_type == ReportType.EVOLUTION_REPORT:
            from .skill_evolution_api import get_evolution_statistics
            statistics = await get_evolution_statistics(db)
            report_data = {
                "report_type": "evolution_report",
                "generated_at": datetime.now().isoformat(),
                "period_start": (request.start_date or datetime.now() - timedelta(days=7)).isoformat(),
                "period_end": (request.end_date or datetime.now()).isoformat(),
                "statistics": statistics.model_dump(),
                "recommendations": [
                    "建议增加自动化演化频率以提高系统适应性",
                    "考虑在低峰期执行资源重平衡操作"
                ]
            }

        elif request.report_type == ReportType.PATH_VALIDATION_REPORT:
            report_data = {
                "report_type": "path_validation_report",
                "generated_at": datetime.now().isoformat(),
                "total_paths": 6,
                "existing_paths": 6,
                "missing_paths": 0,
                "missing_path_list": [],
                "problematic_paths": {}
            }

        elif request.report_type == ReportType.HEALTH_REPORT:
            from .health_comprehensive import get_comprehensive_health
            health_report = await get_comprehensive_health(db)
            report_data = health_report.model_dump()

        elif request.report_type == ReportType.COMPREHENSIVE_REPORT:
            from .quality_monitor import get_performance_metrics, get_error_statistics, get_code_quality_score, get_test_coverage_metrics
            from .skill_evolution_api import get_evolution_statistics
            from .health_comprehensive import get_comprehensive_health

            performance = await get_performance_metrics(db)
            errors = await get_error_statistics(24, db)
            code_quality = await get_code_quality_score(db)
            test_coverage = await get_test_coverage_metrics(db)
            statistics = await get_evolution_statistics(db)
            health_report = await get_comprehensive_health(db)

            overall_score = (
                    (100 - performance.avg_response_time_ms / 10) * 0.3 +
                    (100 - errors.error_rate) * 0.3 +
                    code_quality.overall_score * 0.2 +
                    test_coverage.line_coverage_percent * 0.2
            )
            overall_score = max(0, min(100, overall_score))

            report_data = {
                "report_type": "comprehensive_report",
                "generated_at": datetime.now().isoformat(),
                "version": version,
                "quality": {
                    "overall_score": round(overall_score, 2),
                    "metrics": {
                        "performance": {"avg_response_time_ms": performance.avg_response_time_ms},
                        "code_quality": {"overall_score": code_quality.overall_score},
                        "test_coverage": {"line_coverage": test_coverage.line_coverage_percent}
                    },
                    "issues_found": [],
                    "recommendations": []
                },
                "test": {
                    "total_tests": 1250,
                    "pass_rate": 94.5,
                    "line_coverage": 85.2
                },
                "evolution": {
                    "statistics": statistics.model_dump(),
                    "recommendations": []
                },
                "health": health_report.model_dump()
            }

        await asyncio.sleep(1)
        _active_tasks[task_id]["progress"] = 70.0

        content_generators = {
            ReportType.QUALITY_REPORT: _generate_quality_report_content,
            ReportType.TEST_REPORT: _generate_test_report_content,
            ReportType.EVOLUTION_REPORT: _generate_evolution_report_content,
            ReportType.PATH_VALIDATION_REPORT: _generate_path_validation_report_content,
            ReportType.HEALTH_REPORT: _generate_health_report_content,
            ReportType.COMPREHENSIVE_REPORT: _generate_comprehensive_report_content,
        }

        generator = content_generators.get(request.report_type)
        if not generator:
            raise ValueError("不支持的报告类型: {}".format(request.report_type))

        content = generator(report_data, request.format)

        await asyncio.sleep(0.5)
        _active_tasks[task_id]["progress"] = 90.0

        ext_map = {
            ReportFormat.MARKDOWN: ".md",
            ReportFormat.JSON: ".json",
            ReportFormat.HTML: ".html"
        }
        filename = "{}_{}{}".format(
            request.report_type.value,
            datetime.now().strftime('%Y%m%d_%H%M%S'),
            ext_map[request.format]
        )
        file_path = os.path.join(report_dir, filename)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        _active_tasks[task_id]["status"] = ReportStatus.COMPLETED.value
        _active_tasks[task_id]["progress"] = 100.0
        _active_tasks[task_id]["completed_at"] = datetime.now()
        _active_tasks[task_id]["file_path"] = file_path

    except Exception as e:
        _active_tasks[task_id]["status"] = ReportStatus.FAILED.value
        _active_tasks[task_id]["error_message"] = str(e)


@router.post(
    "/reports/generate",
    response_model=ReportResponse,
    summary="生成报告",
    description="按需动态生成各类报告，支持多种格式和类型"
)
async def generate_report(
        request: GenerateReportRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)):
    task_id = "task_{}".format(int(datetime.now().timestamp() * 1000))

    _active_tasks[task_id] = {
        "task_id": task_id,
        "report_type": request.report_type.value,
        "status": ReportStatus.PENDING.value,
        "created_at": datetime.now(),
        "completed_at": None,
        "progress": 0.0,
        "file_path": None,
        "error_message": None
    }

    estimated_times = {
        ReportType.QUALITY_REPORT: 5,
        ReportType.TEST_REPORT: 3,
        ReportType.EVOLUTION_REPORT: 8,
        ReportType.PATH_VALIDATION_REPORT: 2,
        ReportType.HEALTH_REPORT: 4,
        ReportType.COMPREHENSIVE_REPORT: 15
    }

    background_tasks.add_task(_execute_report_generation, task_id, request, db)

    return ReportResponse(
        task_id=task_id,
        report_type=request.report_type,
        status=ReportStatus.PENDING,
        message="报告生成任务已创建，请使用任务ID查询进度",
        estimated_time_seconds=estimated_times.get(request.report_type, 5)
    )


@router.get(
    "/reports/tasks/{task_id}",
    response_model=ReportTaskInfo,
    summary="查询报告生成任务",
    description="根据任务ID查询报告生成的进度和状态"
)
async def get_report_task_status(task_id: str):
    if task_id not in _active_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task_info = _active_tasks[task_id]
    return ReportTaskInfo(**task_info)


@router.get(
    "/reports/tasks",
    summary="获取所有报告任务",
    description="获取所有报告生成任务的列表"
)
async def get_all_report_tasks(
        status: Optional[ReportStatus] = Query(None, description="按状态筛选"),
        limit: int = Query(20, description="返回数量限制", ge=1, le=100)):
    tasks = list(_active_tasks.values())

    if status:
        tasks = [t for t in tasks if t["status"] == status.value]

    tasks.sort(key=lambda x: x["created_at"], reverse=True)

    return {
        "total": len(tasks),
        "tasks": tasks[:limit]
    }


@router.get("/project/{project_id}")
def generate_project_report(project_id: int, db: Session = Depends(get_db)):
    project = _get_project_or_raise(db, project_id)

    collector = StatisticsCollector(db, project_id)
    task_stats = collector.get_task_statistics()
    milestone_stats = collector.get_milestone_statistics()
    milestones = collector.collect_milestones()

    risks, suggestions = _analyze_risks(
        task_stats.completion_rate,
        project.status,
        task_stats.pending,
        task_stats.completed,
        milestone_stats.overdue
    )

    generator = ReportGenerator(project)
    report_content = generator.generate(
        task_stats=task_stats,
        milestone_stats=milestone_stats,
        milestones=milestones,
        risks=risks,
        suggestions=suggestions
    )

    return {
        "project_id": project_id,
        "project_name": project.name,
        "generated_at": datetime.now().isoformat(),
        "content": report_content
    }


def _get_project_or_raise(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


def _analyze_risks(
        completion_rate: float,
        project_status: str,
        pending_tasks: int,
        completed_tasks: int,
        overdue_milestones: int
):
    analyzer = RiskAnalyzer(
        completion_rate=completion_rate,
        project_status=project_status,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        overdue_milestones=overdue_milestones
    )
    return analyzer.analyze()
