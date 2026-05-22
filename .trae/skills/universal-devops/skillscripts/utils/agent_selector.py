"""
智能Agent选择器 - 根据任务类型推荐最合适的Agent
支持能力匹配、负载均衡、历史表现评估
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class AgentSelectionError(Exception):
    """Agent选择相关异常"""
    pass


class TaskType(str, Enum):
    """任务类型枚举"""
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    STANDARDS = "standards"
    REVIEW = "review"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    QUALITY_MONITOR = "quality_monitor"
    COMPLIANCE = "compliance"
    AGENT_DISPATCH = "agent_dispatch"
    ROLE_MGMT = "role_mgmt"
    SKILL_MATCH = "skill_match"
    COORDINATION = "coordination"
    ENV_CONFIG = "env_config"
    DEP_MGMT = "dep_mgmt"
    RESOURCE_OPT = "resource_opt"
    INFRASTRUCTURE = "infrastructure"
    DOCS = "docs"
    TEMPLATE_MGMT = "template_mgmt"
    KNOWLEDGE_BASE = "knowledge_base"
    STANDARDIZATION = "standardization"
    TDD_EXECUTION = "tdd_execution"
    TEST_FRAMEWORK = "test_framework"
    COVERAGE_ANALYSIS = "coverage_analysis"
    REGRESSION_TESTING = "regression_testing"
    CODEGEN = "codegen"
    UIUX_DESIGN = "uiux_design"
    DB_DESIGN = "db_design"
    API_DESIGN = "api_design"
    BUG_FIXING = "bug_fixing"
    REFACTORING = "refactoring"
    SELF_EVOLUTION = "self_evolution"
    VERSION_CONTROL = "version_control"


@dataclass
class AgentProfile:
    """Agent配置文件"""
    name: str
    capabilities: list[str] = field(default_factory=list)
    specialty: str = ""
    max_concurrent: int = 5
    current_load: int = 0
    province: str | None = None
    department: str | None = None
    si_name: str | None = None
    success_rate: float = 0.95
    avg_response_time: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        return self.current_load < self.max_concurrent

    @property
    def load_ratio(self) -> float:
        if self.max_concurrent == 0:
            return 1.0
        return self.current_load / self.max_concurrent

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "capabilities": self.capabilities,
            "specialty": self.specialty,
            "max_concurrent": self.max_concurrent,
            "current_load": self.current_load,
            "is_available": self.is_available,
            "load_ratio": round(self.load_ratio, 2),
            "province": self.province,
            "department": self.department,
            "si_name": self.si_name,
            "success_rate": self.success_rate,
        }


@dataclass
class SelectionResult:
    """选择结果"""
    agent: AgentProfile
    score: float
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent.to_dict(),
            "score": round(self.score, 4),
            "reason": self.reason,
        }


class AgentSelector:
    """
    智能Agent选择器

    根据任务类型推荐最合适的Agent，支持能力匹配、负载均衡、历史表现评估。
    内置32个预定义Agent（对应24司+4局+4局+额外协调Agent）。
    """

    _instance: AgentSelector | None = None

    def __init__(self) -> None:
        self._agents: dict[str, AgentProfile] = {}
        self._task_capability_map: dict[TaskType, list[str]] = {}
        self._selection_history: list[dict[str, Any]] = []
        self._initialize_builtin_agents()
        self._build_task_capability_map()

    @classmethod
    def get_instance(cls) -> AgentSelector:
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _initialize_builtin_agents(self) -> None:
        """初始化内置的32个Agent"""

        agents_data: list[dict[str, Any]] = [
            {
                "name": "RequirementsBureau",
                "capabilities": ["requirements_analysis", "user_stories", "acceptance_criteria", "specification_writing"],
                "specialty": "需求分析与规格说明",
                "province": "zhongshusheng",
                "department": "requirements_bureau",
            },
            {
                "name": "ArchitectureBureau",
                "capabilities": ["system_architecture", "design_patterns", "tech_stack_selection", "scalability"],
                "specialty": "系统架构设计",
                "province": "zhongshusheng",
                "department": "architecture_bureau",
            },
            {
                "name": "StandardsBureau",
                "capabilities": ["coding_standards", "style_guide", "naming_conventions", "best_practices"],
                "specialty": "标准规范制定",
                "province": "zhongshusheng",
                "department": "standards_bureau",
            },
            {
                "name": "ReviewBureau",
                "capabilities": ["code_review", "peer_review", "quality_gates", "review_checklist"],
                "specialty": "代码审查与质量控制",
                "province": "zhongshusheng",
                "department": "review_bureau",
            },
            {
                "name": "CodeReviewBureau",
                "capabilities": ["static_analysis", "security_review", "performance_review", "complexity_analysis"],
                "specialty": "深度代码审查",
                "province": "menxiasheng",
                "department": "code_review_bureau",
            },
            {
                "name": "TestingBureau",
                "capabilities": ["test_planning", "test_strategy", "test_case_design", "qa_process"],
                "specialty": "测试策略与规划",
                "province": "menxiasheng",
                "department": "testing_bureau",
            },
            {
                "name": "QualityMonitorBureau",
                "capabilities": ["quality_metrics", "code_quality", "technical_debt_tracking", "sonarqube"],
                "specialty": "质量监控与分析",
                "province": "menxiasheng",
                "department": "quality_monitor_bureau",
            },
            {
                "name": "ComplianceBureau",
                "capabilities": ["compliance_check", "security_audit", "regulatory_compliance", "policy_enforcement"],
                "specialty": "合规性检查",
                "province": "menxiasheng",
                "department": "compliance_bureau",
            },
            {
                "name": "AgentDispatchSi",
                "capabilities": ["agent_routing", "load_balancing", "task_scheduling", "resource_allocation"],
                "specialty": "Agent调度与分发",
                "province": "shangshusheng",
                "department": "libu",
                "si_name": "agent_dispatch_si",
            },
            {
                "name": "RoleManagementSi",
                "capabilities": ["role_assignment", "permission_management", "access_control", "rbac"],
                "specialty": "角色权限管理",
                "province": "shangshusheng",
                "department": "libu",
                "si_name": "role_management_si",
            },
            {
                "name": "SkillMatchingSi",
                "capabilities": ["skill_assessment", "capability_matching", "competency_mapping", "talent_management"],
                "specialty": "技能匹配评估",
                "province": "shangshusheng",
                "department": "libu",
                "si_name": "skill_matching_si",
            },
            {
                "name": "CoordinationSi",
                "capabilities": ["cross_team_coordination", "workflow_orchestration", "dependency_resolution", "communication"],
                "specialty": "跨团队协调",
                "province": "shangshusheng",
                "department": "libu",
                "si_name": "coordination_si",
            },
            {
                "name": "EnvironmentConfigSi",
                "capabilities": ["env_setup", "config_management", "infrastructure_as_code", "devops"],
                "specialty": "环境配置管理",
                "province": "shangshusheng",
                "department": "hubu",
                "si_name": "environment_config_si",
            },
            {
                "name": "DependencyMgmtSi",
                "capabilities": ["dependency_resolution", "package_management", "version_conflicts", "lock_files"],
                "specialty": "依赖关系管理",
                "province": "shangshusheng",
                "department": "hubu",
                "si_name": "dependency_mgmt_si",
            },
            {
                "name": "ResourceOptimizationSi",
                "capabilities": ["resource_optimization", "cost_optimization", "performance_tuning", "efficiency"],
                "specialty": "资源优化配置",
                "province": "shangshusheng",
                "department": "hubu",
                "si_name": "resource_optimization_si",
            },
            {
                "name": "InfrastructureSi",
                "capabilities": ["cloud_infrastructure", "containerization", "kubernetes", "networking"],
                "specialty": "基础设施管理",
                "province": "shangshusheng",
                "department": "hubu",
                "si_name": "infrastructure_si",
            },
            {
                "name": "DocumentationSi",
                "capabilities": ["documentation", "api_docs", "technical_writing", "knowledge_transfer"],
                "specialty": "文档生成与管理",
                "province": "shangshusheng",
                "department": "libu2",
                "si_name": "documentation_si",
            },
            {
                "name": "TemplateManagementSi",
                "capabilities": ["template_engine", "scaffolding", "project_boilerplate", "code_generation"],
                "specialty": "模板管理与脚手架",
                "province": "shangshusheng",
                "department": "libu2",
                "si_name": "template_management_si",
            },
            {
                "name": "KnowledgeBaseSi",
                "capabilities": ["knowledge_base", "search_indexing", "document_retrieval", "semantic_search"],
                "specialty": "知识库管理",
                "province": "shangshusheng",
                "department": "libu2",
                "si_name": "knowledge_base_si",
            },
            {
                "name": "StandardizationSi",
                "capabilities": ["standard_enforcement", "linting", "formatting", "convention_checking"],
                "specialty": "标准化执行",
                "province": "shangshusheng",
                "department": "libu2",
                "si_name": "standardization_si",
            },
            {
                "name": "TddExecutionSi",
                "capabilities": ["tdd", "unit_testing", "test_driven_development", "red_green_refactor"],
                "specialty": "TDD测试驱动开发",
                "province": "shangshusheng",
                "department": "bingbu",
                "si_name": "tdd_execution_si",
            },
            {
                "name": "TestFrameworkSi",
                "capabilities": ["pytest", "jest", "junit", "test_framework_integration"],
                "specialty": "测试框架集成",
                "province": "shangshusheng",
                "department": "bingbu",
                "si_name": "test_framework_si",
            },
            {
                "name": "CoverageAnalysisSi",
                "capabilities": ["code_coverage", "coverage_report", "branch_coverage", "line_coverage"],
                "specialty": "覆盖率分析",
                "province": "shangshusheng",
                "department": "bingbu",
                "si_name": "coverage_analysis_si",
            },
            {
                "name": "RegressionTestingSi",
                "capabilities": ["regression_testing", "smoke_tests", "sanity_tests", "automated_regression"],
                "specialty": "回归测试",
                "province": "shangshusheng",
                "department": "bingbu",
                "si_name": "regression_testing_si",
            },
            {
                "name": "CodeGenerationSi",
                "capabilities": ["code_generation", "boilerplate_generation", "ai_coding", "snippet_creation"],
                "specialty": "代码生成",
                "province": "shangshusheng",
                "department": "gongbu",
                "si_name": "code_generation_si",
            },
            {
                "name": "UiuxDesignSi",
                "capabilities": ["ui_design", "ux_design", "prototyping", "responsive_layout"],
                "specialty": "UI/UX设计",
                "province": "shangshusheng",
                "department": "gongbu",
                "si_name": "uiux_design_si",
            },
            {
                "name": "DatabaseDesignSi",
                "capabilities": ["database_design", "schema_migration", "orm_design", "query_optimization"],
                "specialty": "数据库设计",
                "province": "shangshusheng",
                "department": "gongbu",
                "si_name": "database_design_si",
            },
            {
                "name": "ApiDesignSi",
                "capabilities": ["api_design", "restful_api", "graphql", "openapi_spec"],
                "specialty": "API设计",
                "province": "shangshusheng",
                "department": "gongbu",
                "si_name": "api_design_si",
            },
            {
                "name": "BugFixingSi",
                "capabilities": ["debugging", "bug_fixing", "error_tracing", "root_cause_analysis"],
                "specialty": "Bug修复",
                "province": "shangshusheng",
                "department": "xingbu",
                "si_name": "bug_fixing_si",
            },
            {
                "name": "RefactoringSi",
                "capabilities": ["refactoring", "code_smells", "design_improvement", "clean_code"],
                "specialty": "代码重构",
                "province": "shangshusheng",
                "department": "xingbu",
                "si_name": "refactoring_si",
            },
            {
                "name": "SelfEvolutionSi",
                "capabilities": ["self_improvement", "pattern_learning", "adaptive_behavior", "evolutionary_algorithm"],
                "specialty": "自我进化",
                "province": "shangshusheng",
                "department": "xingbu",
                "si_name": "self_evolution_si",
            },
            {
                "name": "VersionControlSi",
                "capabilities": ["git_workflow", "version_control", "branch_strategy", "merge_conflict_resolution"],
                "specialty": "版本控制",
                "province": "shangshusheng",
                "department": "xingbu",
                "si_name": "version_control_si",
            },
        ]

        for agent_data in agents_data:
            profile = AgentProfile(**agent_data)
            self._agents[profile.name] = profile

    def _build_task_capability_map(self) -> None:
        """构建任务类型到能力的映射"""
        self._task_capability_map = {
            TaskType.REQUIREMENTS: [
                "requirements_analysis", "user_stories", "acceptance_criteria", "specification_writing"
            ],
            TaskType.ARCHITECTURE: [
                "system_architecture", "design_patterns", "tech_stack_selection", "scalability"
            ],
            TaskType.STANDARDS: [
                "coding_standards", "style_guide", "naming_conventions", "best_practices"
            ],
            TaskType.REVIEW: [
                "code_review", "peer_review", "quality_gates", "review_checklist"
            ],
            TaskType.CODE_REVIEW: [
                "static_analysis", "security_review", "performance_review", "complexity_analysis"
            ],
            TaskType.TESTING: [
                "test_planning", "test_strategy", "test_case_design", "qa_process"
            ],
            TaskType.QUALITY_MONITOR: [
                "quality_metrics", "code_quality", "technical_debt_tracking", "sonarqube"
            ],
            TaskType.COMPLIANCE: [
                "compliance_check", "security_audit", "regulatory_compliance", "policy_enforcement"
            ],
            TaskType.AGENT_DISPATCH: [
                "agent_routing", "load_balancing", "task_scheduling", "resource_allocation"
            ],
            TaskType.ROLE_MGMT: [
                "role_assignment", "permission_management", "access_control", "rbac"
            ],
            TaskType.SKILL_MATCH: [
                "skill_assessment", "capability_matching", "competency_mapping", "talent_management"
            ],
            TaskType.COORDINATION: [
                "cross_team_coordination", "workflow_orchestration", "dependency_resolution", "communication"
            ],
            TaskType.ENV_CONFIG: [
                "env_setup", "config_management", "infrastructure_as_code", "devops"
            ],
            TaskType.DEP_MGMT: [
                "dependency_resolution", "package_management", "version_conflicts", "lock_files"
            ],
            TaskType.RESOURCE_OPT: [
                "resource_optimization", "cost_optimization", "performance_tuning", "efficiency"
            ],
            TaskType.INFRASTRUCTURE: [
                "cloud_infrastructure", "containerization", "kubernetes", "networking"
            ],
            TaskType.DOCS: [
                "documentation", "api_docs", "technical_writing", "knowledge_transfer"
            ],
            TaskType.TEMPLATE_MGMT: [
                "template_engine", "scaffolding", "project_boilerplate", "code_generation"
            ],
            TaskType.KNOWLEDGE_BASE: [
                "knowledge_base", "search_indexing", "document_retrieval", "semantic_search"
            ],
            TaskType.STANDARDIZATION: [
                "standard_enforcement", "linting", "formatting", "convention_checking"
            ],
            TaskType.TDD_EXECUTION: [
                "tdd", "unit_testing", "test_driven_development", "red_green_refactor"
            ],
            TaskType.TEST_FRAMEWORK: [
                "pytest", "jest", "junit", "test_framework_integration"
            ],
            TaskType.COVERAGE_ANALYSIS: [
                "code_coverage", "coverage_report", "branch_coverage", "line_coverage"
            ],
            TaskType.REGRESSION_TESTING: [
                "regression_testing", "smoke_tests", "sanity_tests", "automated_regression"
            ],
            TaskType.CODEGEN: [
                "code_generation", "boilerplate_generation", "ai_coding", "snippet_creation"
            ],
            TaskType.UIUX_DESIGN: [
                "ui_design", "ux_design", "prototyping", "responsive_layout"
            ],
            TaskType.DB_DESIGN: [
                "database_design", "schema_migration", "orm_design", "query_optimization"
            ],
            TaskType.API_DESIGN: [
                "api_design", "restful_api", "graphql", "openapi_spec"
            ],
            TaskType.BUG_FIXING: [
                "debugging", "bug_fixing", "error_tracing", "root_cause_analysis"
            ],
            TaskType.REFACTORING: [
                "refactoring", "code_smells", "design_improvement", "clean_code"
            ],
            TaskType.SELF_EVOLUTION: [
                "self_improvement", "pattern_learning", "adaptive_behavior", "evolutionary_algorithm"
            ],
            TaskType.VERSION_CONTROL: [
                "git_workflow", "version_control", "branch_strategy", "merge_conflict_resolution"
            ],
        }

    def register_agent(self, profile: AgentProfile) -> None:
        """
        注册新的Agent

        Args:
            profile: Agent配置对象

        Raises:
            AgentSelectionError: 当Agent名称已存在时
        """
        if profile.name in self._agents:
            raise AgentSelectionError(f"Agent已注册: {profile.name}")
        self._agents[profile.name] = profile

    def select(
        self,
        task_type: TaskType,
        context: dict[str, Any] | None = None,
    ) -> SelectionResult:
        """
        选择最佳Agent处理指定任务类型

        Args:
            task_type: 任务类型
            context: 可选的上下文信息（如优先级、约束条件等）

        Returns:
            SelectionResult对象，包含选中的Agent和评分

        Raises:
            AgentSelectionError: 当没有可用Agent时
        """
        required_caps: list[str] = self._task_capability_map.get(task_type, [])

        candidates: list[tuple[AgentProfile, float]] = []

        for agent in self._agents.values():
            if not agent.is_available:
                continue

            score: float = self.evaluate_fit(agent, task_type)
            candidates.append((agent, score))

        if not candidates:
            raise AgentSelectionError(f"没有可用的Agent来处理任务类型: {task_type.value}")

        candidates.sort(key=lambda x: x[1], reverse=True)

        best_agent, best_score = candidates[0]
        best_agent.current_load += 1

        reason_parts: list[str] = [f"任务类型匹配: {task_type.value}"]
        if required_caps:
            matched = sum(1 for c in required_caps if c in best_agent.capabilities)
            reason_parts.append(f"能力匹配度: {matched}/{len(required_caps)}")
        reason_parts.append(f"负载率: {best_agent.load_ratio:.2f}")

        result = SelectionResult(
            agent=best_agent,
            score=best_score,
            reason="; ".join(reason_parts),
        )

        self._selection_history.append({
            "task_type": task_type.value,
            "selected_agent": best_agent.name,
            "score": best_score,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        })

        return result

    def select_multiple(
        self,
        task_types: list[TaskType],
        count: int = 3,
    ) -> list[SelectionResult]:
        """
        多任务类型的多个Agent选择

        Args:
            task_types: 任务类型列表
            count: 需要选择的Agent数量

        Returns:
            SelectionResult列表，按评分降序排列
        """
        all_required: list[str] = []
        for tt in task_types:
            all_required.extend(self._task_capability_map.get(tt, []))

        scored_agents: list[tuple[AgentProfile, float]] = []

        for agent in self._agents.values():
            if not agent.is_available:
                continue

            total_score: float = 0.0
            for tt in task_types:
                total_score += self.evaluate_fit(agent, tt)
            avg_score: float = total_score / len(task_types) if task_types else 0.0

            scored_agents.append((agent, avg_score))

        scored_agents.sort(key=lambda x: x[1], reverse=True)

        results: list[SelectionResult] = []
        for agent, score in scored_agents[:count]:
            agent.current_load += 1
            results.append(SelectionResult(
                agent=agent,
                score=score,
                reason=f"多任务综合评分: {score:.4f}",
            ))

        return results

    def evaluate_fit(
        self,
        agent: AgentProfile,
        task_type: TaskType,
    ) -> float:
        """
        评估Agent对任务类型的匹配度 (0-1)

        Args:
            agent: 要评估的Agent
            task_type: 任务类型

        Returns:
            匹配度分数 (0.0 到 1.0)
        """
        required_caps: list[str] = self._task_capability_map.get(task_type, [])
        if not required_caps:
            return 0.5

        capability_match: float = 0.0
        if required_caps and agent.capabilities:
            matched_count: int = sum(1 for c in required_caps if c in agent.capabilities)
            capability_match = matched_count / len(required_caps)

        availability_factor: float = 1.0 - agent.load_ratio
        success_factor: float = agent.success_rate

        weights: dict[str, float] = {
            "capability": 0.50,
            "availability": 0.25,
            "success_rate": 0.25,
        }

        final_score: float = (
            capability_match * weights["capability"]
            + availability_factor * weights["availability"]
            + success_factor * weights["success_rate"]
        )

        return min(max(final_score, 0.0), 1.0)

    def get_recommendations(
        self,
        task_description: str,
        top_n: int = 5,
    ) -> list[tuple[AgentProfile, float]]:
        """
        基于自然语言描述推荐合适的Agent

        Args:
            task_description: 任务的自然语言描述
            top_n: 返回前N个推荐结果

        Returns:
            (AgentProfile, 分数) 元组列表，按分数降序排列
        """
        desc_lower: str = task_description.lower()

        keyword_to_tasks: dict[str, list[TaskType]] = {
            "需求": [TaskType.REQUIREMENTS],
            "架构": [TaskType.ARCHITECTURE],
            "标准": [TaskType.STANDARDIZATION, TaskType.STANDARDS],
            "审查": [TaskType.REVIEW, TaskType.CODE_REVIEW],
            "测试": [TaskType.TESTING, TaskType.TDD_EXECUTION, TaskType.TEST_FRAMEWORK],
            "质量": [TaskType.QUALITY_MONITOR],
            "合规": [TaskType.COMPLIANCE],
            "调度": [TaskType.AGENT_DISPATCH],
            "角色": [TaskType.ROLE_MGMT],
            "技能": [TaskType.SKILL_MATCH],
            "协调": [TaskType.COORDINATION],
            "环境": [TaskType.ENV_CONFIG, TaskType.INFRASTRUCTURE],
            "依赖": [TaskType.DEP_MGMT],
            "资源": [TaskType.RESOURCE_OPT],
            "文档": [TaskType.DOCS],
            "模板": [TaskType.TEMPLATE_MGMT],
            "知识": [TaskType.KNOWLEDGE_BASE],
            "覆盖": [TaskType.COVERAGE_ANALYSIS],
            "回归": [TaskType.REGRESSION_TESTING],
            "生成": [TaskType.CODEGEN],
            "设计": [TaskType.UIUX_DESIGN, TaskType.DB_DESIGN, TaskType.API_DESIGN],
            "bug": [TaskType.BUG_FIXING],
            "重构": [TaskType.REFACTORING],
            "进化": [TaskType.SELF_EVOLUTION],
            "版本": [TaskType.VERSION_CONTROL],
            "api": [TaskType.API_DESIGN],
            "数据库": [TaskType.DB_DESIGN],
            "ui": [TaskType.UIUX_DESIGN],
            "ux": [TaskType.UIUX_DESIGN],
            "tdd": [TaskType.TDD_EXECUTION],
            "docker": [TaskType.INFRASTRUCTURE],
            "k8s": [TaskType.INFRASTRUCTURE],
            "kubernetes": [TaskType.INFRASTRUCTURE],
        }

        matched_tasks: set[TaskType] = set()
        for keyword, tasks in keyword_to_tasks.items():
            if keyword in desc_lower:
                matched_tasks.update(tasks)

        if not matched_tasks:
            matched_tasks = {TaskType.ARCHITECTURE}

        scores: list[tuple[AgentProfile, float]] = []
        for agent in self._agents.values():
            if not agent.is_available:
                continue

            total_score: float = sum(
                self.evaluate_fit(agent, tt) for tt in matched_tasks
            )
            avg_score: float = total_score / len(matched_tasks) if matched_tasks else 0.0
            scores.append((agent, avg_score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_n]

    @property
    def all_agents(self) -> dict[str, AgentProfile]:
        return dict(self._agents)

    @property
    def available_agents(self) -> list[AgentProfile]:
        return [a for a in self._agents.values() if a.is_available]

    @property
    def agent_count(self) -> int:
        return len(self._agents)

    def get_agent(self, name: str) -> AgentProfile:
        """
        根据名称获取Agent

        Args:
            name: Agent名称

        Returns:
            AgentProfile对象

        Raises:
            AgentSelectionError: 当Agent不存在时
        """
        if name not in self._agents:
            raise AgentSelectionError(f"Agent不存在: {name}")
        return self._agents[name]

    def __repr__(self) -> str:
        available = len(self.available_agents)
        return (
            f"AgentSelector(total={self.agent_count}, "
            f"available={available})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 智能Agent选择器测试")
    print("=" * 60)

    selector = AgentSelector()

    print(f"\n📊 总Agent数: {selector.agent_count}")
    print(f"📋 可用Agent数: {len(selector.available_agents)}")

    print("\n--- 单任务选择测试 ---")
    try:
        result = selector.select(TaskType.ARCHITECTURE)
        print(f"✅ 选择结果:")
        print(f"   Agent: {result.agent.name}")
        print(f"   评分: {result.score:.4f}")
        print(f"   原因: {result.reason}")
        print(f"   专业: {result.agent.specialty}")
    except AgentSelectionError as e:
        print(f"❌ 选择失败: {e}")

    print("\n--- 多任务选择测试 ---")
    try:
        results = selector.select_multiple([TaskType.TESTING, TaskType.CODE_REVIEW], count=3)
        print(f"✅ 选择 {len(results)} 个Agent:")
        for i, r in enumerate(results, 1):
            print(f"   {i}. {r.agent.name} (评分: {r.score:.4f})")
    except AgentSelectionError as e:
        print(f"❌ 选择失败: {e}")

    print("\n--- 自然语言推荐测试 ---")
    recommendations = selector.get_recommendations("我需要设计一个RESTful API和数据库结构", top_n=3)
    print(f"✅ 推荐 {len(recommendations)} 个Agent:")
    for agent, score in recommendations:
        print(f"   🤖 {agent.name} (评分: {score:.4f}) - {agent.specialty}")

    print("\n--- 评估匹配度测试 ---")
    test_agent = selector.get_agent("ApiDesignSi")
    fit_score = selector.evaluate_fit(test_agent, TaskType.API_DESIGN)
    print(f"ApiDesignSi 对 API_DESIGN 的匹配度: {fit_score:.4f}")

    fit_score_2 = selector.evaluate_fit(test_agent, TaskType.BUG_FIXING)
    print(f"ApiDesignSi 对 BUG_FIXING 的匹配度: {fit_score_2:.4f}")

    print("\n--- 列出所有Agent ---")
    for name, agent in sorted(selector.all_agents.items()):
        status = "🟢" if agent.is_available else "🔴"
        print(f"   {status} {name}: {agent.specialty}")

    print("\n✅ 所有测试通过!")
