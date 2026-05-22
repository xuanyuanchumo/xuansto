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

class HealthLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

class HealthCategory(str, Enum):
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    COMPATIBILITY = "compatibility"

class AssessmentStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class HealthMetric(BaseModel):
    name: str = Field(..., description="指标名称")
    value: float = Field(..., description="指标值")
    unit: str = Field(..., description="单位")
    threshold_good: float = Field(..., description="良好阈值")
    threshold_warning: float = Field(..., description="警告阈值")
    threshold_critical: float = Field(..., description="严重阈值")
    status: HealthLevel = Field(..., description="健康状态")
    trend: str = Field("stable", description="趋势: improving, declining, stable")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")

    class Config:
        from_attributes = True

class HealthCategoryScore(BaseModel):
    category: HealthCategory = Field(..., description="健康类别")
    score: float = Field(..., description="分数 (0-100)", ge=0, le=100)
    level: HealthLevel = Field(..., description="健康等级")
    metrics: List[HealthMetric] = Field(default_factory=list, description="详细指标")
    issues: List[str] = Field(default_factory=list, description="问题列表")
    recommendations: List[str] = Field(default_factory=list, description="建议列表")

    class Config:
        from_attributes = True

class SkillHealthAssessment(BaseModel):
    skill_id: str = Field(..., description="技能ID")
    skill_name: str = Field(..., description="技能名称")
    overall_score: float = Field(..., description="总体健康分数 (0-100)", ge=0, le=100)
    overall_level: HealthLevel = Field(..., description="总体健康等级")
    category_scores: List[HealthCategoryScore] = Field(default_factory=list, description="各类别分数")
    critical_issues: List[str] = Field(default_factory=list, description="严重问题")
    warnings: List[str] = Field(default_factory=list, description="警告")
    last_assessment: datetime = Field(default_factory=datetime.now, description="上次评估时间")
    next_assessment: Optional[datetime] = Field(None, description="下次评估时间")
    assessment_duration_ms: int = Field(0, description="评估耗时（毫秒）")

    class Config:
        from_attributes = True

class HealthReport(BaseModel):
    report_id: str = Field(..., description="报告ID")
    generated_at: datetime = Field(..., description="生成时间")
    period_start: datetime = Field(..., description="报告周期开始")
    period_end: datetime = Field(..., description="报告周期结束")
    total_skills: int = Field(0, description="技能总数")
    healthy_skills: int = Field(0, description="健康技能数")
    degraded_skills: int = Field(0, description="降级技能数")
    critical_skills: int = Field(0, description="严重技能数")
    average_score: float = Field(0.0, description="平均健康分数")
    skill_assessments: List[SkillHealthAssessment] = Field(default_factory=list, description="技能评估列表")
    top_issues: List[Dict[str, Any]] = Field(default_factory=list, description="主要问题")
    recommendations: List[str] = Field(default_factory=list, description="整体建议")
    trends: Dict[str, Any] = Field(default_factory=dict, description="趋势数据")

    class Config:
        from_attributes = True

class AssessmentTriggerRequest(BaseModel):
    skill_ids: Optional[List[str]] = Field(None, description="指定评估的技能ID列表，为空则评估所有")
    categories: Optional[List[HealthCategory]] = Field(None, description="指定评估的类别，为空则评估所有")
    deep_analysis: bool = Field(False, description="是否进行深度分析")
    include_recommendations: bool = Field(True, description="是否包含建议")
    priority: str = Field("normal", description="优先级: high, normal, low")

class AssessmentTriggerResponse(BaseModel):
    assessment_id: str = Field(..., description="评估ID")
    status: AssessmentStatus = Field(..., description="评估状态")
    skills_to_assess: int = Field(0, description="待评估技能数")
    estimated_duration_ms: int = Field(0, description="预计耗时（毫秒）")
    message: str = Field(..., description="消息")

class AssessmentProgress(BaseModel):
    assessment_id: str = Field(..., description="评估ID")
    status: AssessmentStatus = Field(..., description="评估状态")
    progress: float = Field(0.0, description="进度百分比", ge=0, le=100)
    skills_completed: int = Field(0, description="已完成技能数")
    skills_total: int = Field(0, description="总技能数")
    current_skill: Optional[str] = Field(None, description="当前评估技能")
    started_at: datetime = Field(..., description="开始时间")
    estimated_completion: Optional[datetime] = Field(None, description="预计完成时间")
    errors: List[str] = Field(default_factory=list, description="错误列表")

_current_assessment: Dict[str, Any] = {
    "status": AssessmentStatus.PENDING,
    "progress": 0.0,
    "assessment_id": None
}

def _generate_mock_metrics(category: HealthCategory) -> List[HealthMetric]:
    base_metrics = {
        HealthCategory.PERFORMANCE: [
            ("response_time", 1.2, "seconds", 1.0, 2.0, 5.0),
            ("throughput", 150.0, "req/s", 100.0, 50.0, 20.0),
            ("latency_p99", 2.5, "seconds", 2.0, 4.0, 8.0),
        ],
        HealthCategory.RELIABILITY: [
            ("success_rate", 98.5, "%", 95.0, 90.0, 80.0),
            ("error_rate", 1.5, "%", 5.0, 10.0, 20.0),
            ("availability", 99.9, "%", 99.0, 95.0, 90.0),
        ],
        HealthCategory.MAINTAINABILITY: [
            ("code_coverage", 85.0, "%", 80.0, 60.0, 40.0),
            ("technical_debt", 15.0, "hours", 20.0, 40.0, 80.0),
            ("documentation_score", 75.0, "%", 70.0, 50.0, 30.0),
        ],
        HealthCategory.SECURITY: [
            ("vulnerability_count", 2, "count", 5, 10, 20),
            ("security_score", 88.0, "%", 80.0, 60.0, 40.0),
            ("compliance_score", 92.0, "%", 85.0, 70.0, 50.0),
        ],
        HealthCategory.COMPATIBILITY: [
            ("api_compatibility", 95.0, "%", 90.0, 80.0, 60.0),
            ("dependency_health", 88.0, "%", 85.0, 70.0, 50.0),
            ("version_compliance", 100.0, "%", 95.0, 80.0, 60.0),
        ],
    }
    
    metrics = []
    for name, value, unit, good, warning, critical in base_metrics.get(category, []):
        if "rate" in name or "score" in name or "compatibility" in name or "compliance" in name or "availability" in name or "coverage" in name:
            if value >= good:
                status = HealthLevel.EXCELLENT
            elif value >= warning:
                status = HealthLevel.GOOD
            elif value >= critical:
                status = HealthLevel.FAIR
            else:
                status = HealthLevel.POOR
        else:
            if value <= good:
                status = HealthLevel.EXCELLENT
            elif value <= warning:
                status = HealthLevel.GOOD
            elif value <= critical:
                status = HealthLevel.FAIR
            else:
                status = HealthLevel.POOR
        
        metrics.append(HealthMetric(
            name=name,
            value=value,
            unit=unit,
            threshold_good=good,
            threshold_warning=warning,
            threshold_critical=critical,
            status=status,
            trend=["improving", "stable", "declining"][hash(name) % 3],
            last_updated=datetime.now()
        ))
    
    return metrics

def _calculate_category_score(metrics: List[HealthMetric]) -> tuple:
    if not metrics:
        return 0.0, HealthLevel.CRITICAL
    
    score = sum(m.value for m in metrics) / len(metrics)
    
    if score >= 90:
        level = HealthLevel.EXCELLENT
    elif score >= 75:
        level = HealthLevel.GOOD
    elif score >= 60:
        level = HealthLevel.FAIR
    elif score >= 40:
        level = HealthLevel.POOR
    else:
        level = HealthLevel.CRITICAL
    
    return round(score, 2), level

def _generate_skill_health(skill_id: str, skill_name: str) -> SkillHealthAssessment:
    category_scores = []
    issues = []
    warnings = []
    
    for category in HealthCategory:
        metrics = _generate_mock_metrics(category)
        score, level = _calculate_category_score(metrics)
        
        category_issues = []
        category_recommendations = []
        
        for m in metrics:
            if m.status in [HealthLevel.POOR, HealthLevel.CRITICAL]:
                category_issues.append(f"{m.name}: {m.value}{m.unit} (阈值: {m.threshold_warning}{m.unit})")
            if m.trend == "declining":
                category_recommendations.append(f"建议监控 {m.name} 的下降趋势")
        
        category_scores.append(HealthCategoryScore(
            category=category,
            score=score,
            level=level,
            metrics=metrics,
            issues=category_issues,
            recommendations=category_recommendations
        ))
        
        if level == HealthLevel.CRITICAL:
            issues.extend(category_issues)
        elif level == HealthLevel.POOR:
            warnings.extend(category_issues)
    
    overall_score = sum(c.score for c in category_scores) / len(category_scores)
    
    if overall_score >= 90:
        overall_level = HealthLevel.EXCELLENT
    elif overall_score >= 75:
        overall_level = HealthLevel.GOOD
    elif overall_score >= 60:
        overall_level = HealthLevel.FAIR
    elif overall_score >= 40:
        overall_level = HealthLevel.POOR
    else:
        overall_level = HealthLevel.CRITICAL
    
    return SkillHealthAssessment(
        skill_id=skill_id,
        skill_name=skill_name,
        overall_score=round(overall_score, 2),
        overall_level=overall_level,
        category_scores=category_scores,
        critical_issues=issues,
        warnings=warnings,
        last_assessment=datetime.now(),
        next_assessment=datetime.now() + timedelta(hours=24),
        assessment_duration_ms=1500
    )

def _get_mock_health_assessment() -> SkillHealthAssessment:
    return _generate_skill_health("skill_001", "code_generator")

def _get_mock_health_report() -> HealthReport:
    skills = [
        _generate_skill_health("skill_001", "code_generator"),
        _generate_skill_health("skill_002", "test_runner"),
        _generate_skill_health("skill_003", "doc_writer"),
        _generate_skill_health("skill_004", "api_designer"),
        _generate_skill_health("skill_005", "security_scanner"),
    ]
    
    healthy = sum(1 for s in skills if s.overall_level in [HealthLevel.EXCELLENT, HealthLevel.GOOD])
    degraded = sum(1 for s in skills if s.overall_level == HealthLevel.FAIR)
    critical = sum(1 for s in skills if s.overall_level in [HealthLevel.POOR, HealthLevel.CRITICAL])
    
    return HealthReport(
        report_id=f"report_{int(time.time())}",
        generated_at=datetime.now(),
        period_start=datetime.now() - timedelta(days=7),
        period_end=datetime.now(),
        total_skills=len(skills),
        healthy_skills=healthy,
        degraded_skills=degraded,
        critical_skills=critical,
        average_score=round(sum(s.overall_score for s in skills) / len(skills), 2),
        skill_assessments=skills,
        top_issues=[
            {"skill": "security_scanner", "issue": "漏洞扫描响应时间过长", "severity": "high"},
            {"skill": "test_runner", "issue": "测试覆盖率下降", "severity": "medium"},
        ],
        recommendations=[
            "建议优化 security_scanner 的扫描算法",
            "建议增加 test_runner 的测试用例",
            "建议更新所有技能的依赖库版本",
        ],
        trends={
            "score_trend": "improving",
            "issue_trend": "declining",
            "weekly_change": "+2.5%",
        }
    )

async def _run_assessment(assessment_id: str, request: AssessmentTriggerRequest):
    global _current_assessment
    _current_assessment = {
        "status": AssessmentStatus.IN_PROGRESS,
        "progress": 0.0,
        "assessment_id": assessment_id,
        "started_at": datetime.now(),
        "skills_completed": 0,
        "skills_total": 5,
        "errors": []
    }
    
    skill_names = ["code_generator", "test_runner", "doc_writer", "api_designer", "security_scanner"]
    
    for i, skill_name in enumerate(skill_names):
        await asyncio.sleep(1)
        _current_assessment["progress"] = (i + 1) / len(skill_names) * 100
        _current_assessment["skills_completed"] = i + 1
        _current_assessment["current_skill"] = skill_name
    
    _current_assessment["status"] = AssessmentStatus.COMPLETED
    _current_assessment["progress"] = 100.0

@router.get(
    "/health",
    response_model=SkillHealthAssessment,
    summary="获取技能健康度评估",
    description="获取当前技能的健康度评估结果，包括各维度的健康指标和问题"
)
async def get_skill_health(
    skill_id: Optional[str] = Query(None, description="技能ID，不指定则返回默认技能"),
    db: Session = Depends(get_db)
):
    cache_key = f"skill_health:assessment:{skill_id or 'default'}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return SkillHealthAssessment(**cached)
    
    result = _get_mock_health_assessment()
    if skill_id:
        result.skill_id = skill_id
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    
    return result

@router.get(
    "/health/report",
    response_model=HealthReport,
    summary="获取详细健康度报告",
    description="获取所有技能的详细健康度报告，包括趋势分析和整体建议"
)
async def get_health_report(
    period_days: int = Query(7, description="报告周期（天）", ge=1, le=30),
    include_details: bool = Query(True, description="是否包含详细评估"),
    db: Session = Depends(get_db)
):
    cache_key = f"skill_health:report:{period_days}:{include_details}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return HealthReport(**cached)
    
    result = _get_mock_health_report()
    result.period_start = datetime.now() - timedelta(days=period_days)
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=300)
    
    return result

@router.post(
    "/health/assess",
    response_model=AssessmentTriggerResponse,
    summary="触发健康度评估",
    description="手动触发一次技能健康度评估，可选择指定技能和评估深度"
)
async def trigger_health_assessment(
    request: AssessmentTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    global _current_assessment
    
    if _current_assessment.get("status") == AssessmentStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=409,
            detail="已有评估正在进行中，请等待完成"
        )
    
    assessment_id = f"assess_{int(time.time() * 1000)}"
    skills_count = len(request.skill_ids) if request.skill_ids else 5
    
    _current_assessment = {
        "status": AssessmentStatus.PENDING,
        "progress": 0.0,
        "assessment_id": assessment_id
    }
    
    background_tasks.add_task(_run_assessment, assessment_id, request)
    
    return AssessmentTriggerResponse(
        assessment_id=assessment_id,
        status=AssessmentStatus.IN_PROGRESS,
        skills_to_assess=skills_count,
        estimated_duration_ms=skills_count * 1500,
        message="健康度评估已触发，正在后台执行"
    )

@router.get(
    "/health/assess/{assessment_id}",
    response_model=AssessmentProgress,
    summary="获取评估进度",
    description="获取指定评估任务的进度信息"
)
async def get_assessment_progress(
    assessment_id: str,
    db: Session = Depends(get_db)
):
    global _current_assessment
    
    if _current_assessment.get("assessment_id") != assessment_id:
        raise HTTPException(
            status_code=404,
            detail="未找到指定的评估任务"
        )
    
    return AssessmentProgress(
        assessment_id=assessment_id,
        status=_current_assessment.get("status", AssessmentStatus.PENDING),
        progress=_current_assessment.get("progress", 0.0),
        skills_completed=_current_assessment.get("skills_completed", 0),
        skills_total=_current_assessment.get("skills_total", 5),
        current_skill=_current_assessment.get("current_skill"),
        started_at=_current_assessment.get("started_at", datetime.now()),
        estimated_completion=datetime.now() + timedelta(seconds=5),
        errors=_current_assessment.get("errors", [])
    )

@router.get(
    "/health/metrics/{skill_id}",
    response_model=List[HealthMetric],
    summary="获取技能健康指标",
    description="获取指定技能的所有健康指标详情"
)
async def get_skill_health_metrics(
    skill_id: str,
    category: Optional[HealthCategory] = Query(None, description="筛选类别"),
    db: Session = Depends(get_db)
):
    cache_key = f"skill_health:metrics:{skill_id}:{category}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return [HealthMetric(**m) for m in cached]
    
    if category:
        metrics = _generate_mock_metrics(category)
    else:
        metrics = []
        for cat in HealthCategory:
            metrics.extend(_generate_mock_metrics(cat))
    
    cache_service.set_json(cache_key, [m.model_dump() for m in metrics], ttl=60)
    
    return metrics

@router.get(
    "/health/history/{skill_id}",
    summary="获取健康度历史",
    description="获取指定技能的历史健康度数据"
)
async def get_health_history(
    skill_id: str,
    days: int = Query(7, description="历史天数", ge=1, le=90),
    db: Session = Depends(get_db)
):
    cache_key = f"skill_health:history:{skill_id}:{days}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached
    
    history = []
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        score = 75 + (i * 0.5) + (hash(str(i)) % 10)
        history.append({
            "date": date.strftime("%Y-%m-%d"),
            "score": round(score, 2),
            "level": "good" if score >= 75 else "fair",
            "issues_count": max(0, 5 - int(score / 20))
        })
    
    result = {
        "skill_id": skill_id,
        "period_days": days,
        "history": list(reversed(history)),
        "trend": "improving",
        "average_score": round(sum(h["score"] for h in history) / len(history), 2)
    }
    
    cache_service.set_json(cache_key, result, ttl=300)
    
    return result
