from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api.exceptions import setup_exception_handlers
from .services.performance import PerformanceMiddleware, get_performance_stats

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 三省六部协同开发系统 API

基于三省六部架构的软件开发协同管理系统，实现需求分析、开发、测试、部署全流程管理。

### 主要模块

- **项目管理 (Projects)**: 项目创建、状态管理、进度跟踪
- **任务管理 (Tasks)**: 任务分配、依赖管理、状态流转
- **代理管理 (Agents)**: AI代理注册、负载管理、技能配置
- **部门管理 (Departments)**: 组织架构管理
- **技能调用 (Skill Calls)**: 技能执行记录、调用树追踪
- **工作流 (Workflow)**: 状态流转、依赖检查
- **流水线 (Pipeline)**: 开发流水线阶段管理
- **透明度报告 (Transparency)**: 决策日志、代码变更追踪

### 状态流转规则

项目状态: REQUIREMENT → DESIGN → DEVELOPMENT → TESTING → DEPLOYMENT → COMPLETED
任务状态: PENDING → IN_PROGRESS → REVIEW → COMPLETED
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

setup_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

app.add_middleware(PerformanceMiddleware, slow_threshold_ms=200.0)


@app.get(
    "/",
    summary="根路径",
    description="返回API基本信息",
    response_description="API名称和版本信息"
)
async def root():
    return {"message": "Sanliu Skill Management System", "version": settings.APP_VERSION}


@app.get(
    "/health",
    summary="健康检查",
    description="检查API服务是否正常运行",
    response_description="服务健康状态"
)
async def health_check():
    return {"status": "healthy", "timestamp": __import__('datetime').datetime.utcnow().isoformat()}


@app.get(
    "/performance/stats",
    summary="性能统计",
    description="获取API性能统计信息",
    response_description="性能统计数据"
)
async def performance_statistics():
    return get_performance_stats()

from .api import skill_calls, agents, assignments, projects, dashboard, ws, workflow, statistics, reports, milestones, tasks
from .api import decision_logs, input_output_traces, code_changes, artifacts, transparency
from .api import requirement_traces, clarification_questions, human_approvals, acceptance_tests
from .api import mutation_tests, non_functional_checks, pipeline, departments, evolution_monitor
from .api import skill_evolution_api, skill_health, path_validation, evolution_knowledge, quality_monitor
from .api import realtime_quality, health_comprehensive
from .api import path_config_api
from .api import evolution_insights_api, recommendations_api, knowledge_api, ux_monitor_api
from .api import resource_coordination, secrets_management, four_d_defense, agency_integration

app.include_router(skill_calls.router, prefix="/api/skill_calls", tags=["skill_calls"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["assignments"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(ws.router, prefix="/ws", tags=["websocket"])
app.include_router(workflow.router, prefix="/api/workflow", tags=["workflow"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(milestones.router, prefix="/api/milestones", tags=["milestones"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(decision_logs.router, prefix="/api/decision_logs", tags=["decision_logs"])
app.include_router(input_output_traces.router, prefix="/api/io_traces", tags=["io_traces"])
app.include_router(code_changes.router, prefix="/api/code_changes", tags=["code_changes"])
app.include_router(artifacts.router, prefix="/api/artifacts", tags=["artifacts"])
app.include_router(transparency.router, prefix="/api/transparency", tags=["transparency"])
app.include_router(requirement_traces.router, prefix="/api/requirement_traces", tags=["requirement_traces"])
app.include_router(clarification_questions.router, prefix="/api/clarification_questions", tags=["clarification_questions"])
app.include_router(human_approvals.router, prefix="/api/human_approvals", tags=["human_approvals"])
app.include_router(acceptance_tests.router, prefix="/api/acceptance_tests", tags=["acceptance_tests"])
app.include_router(mutation_tests.router, prefix="/api/mutation_tests", tags=["mutation_tests"])
app.include_router(non_functional_checks.router, prefix="/api/non_functional_checks", tags=["non_functional_checks"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(departments.router, prefix="/api/departments", tags=["departments"])
app.include_router(evolution_monitor.router, prefix="/api/evolution", tags=["evolution_monitor"])
app.include_router(skill_evolution_api.router, prefix="/api/skill-evolution", tags=["skill_evolution"])
app.include_router(skill_health.router, prefix="/api/skill", tags=["skill_health"])
app.include_router(path_validation.router, prefix="/api/skill/paths", tags=["path_validation"])
app.include_router(evolution_knowledge.router, prefix="/api/evolution-knowledge", tags=["evolution_knowledge"])
app.include_router(quality_monitor.router, prefix="/api/quality", tags=["quality_monitor"])
app.include_router(realtime_quality.router, prefix="/api", tags=["realtime_quality"])
app.include_router(health_comprehensive.router, prefix="/api", tags=["health_comprehensive"])
app.include_router(path_config_api.router, prefix="/api", tags=["path_config"])

app.include_router(evolution_insights_api.router, prefix="/api/evolution/insights", tags=["evolution_insights"])
app.include_router(recommendations_api.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(knowledge_api.router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(ux_monitor_api.router, prefix="/api/ux", tags=["ux_monitor"])

app.include_router(resource_coordination.router, prefix="/api", tags=["resource_coordination"])
app.include_router(secrets_management.router, prefix="/api", tags=["secrets_management"])
app.include_router(four_d_defense.router, prefix="/api", tags=["four_d_defense"])
app.include_router(agency_integration.router, prefix="/api", tags=["agency_integration"])
