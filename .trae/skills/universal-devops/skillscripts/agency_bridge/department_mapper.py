"""
部门映射器（核心映射矩阵实现）

维护三省六部二十四司与 agency-agents 中 144+ AI 智能体的完整映射关系，
支持双向查询、协作模式推荐和映射覆盖率验证。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class DepartmentID(str, Enum):
    """部门ID枚举（24司 + 8局）"""

    AGENT_DISPATCH_SI = "agent_dispatch_si"
    ROLE_MANAGEMENT_SI = "role_management_si"
    SKILL_MATCHING_SI = "skill_matching_si"
    COORDINATION_SI = "coordination_si"
    ENVIRONMENT_CONFIG_SI = "environment_config_si"
    DEPENDENCY_MGMT_SI = "dependency_mgmt_si"
    RESOURCE_OPTIMIZATION_SI = "resource_optimization_si"
    INFRASTRUCTURE_SI = "infrastructure_si"
    DOCUMENTATION_SI = "documentation_si"
    TEMPLATE_MANAGEMENT_SI = "template_management_si"
    KNOWLEDGE_BASE_SI = "knowledge_base_si"
    STANDARDIZATION_SI = "standardization_si"
    TDD_EXECUTION_SI = "tdd_execution_si"
    TEST_FRAMEWORK_SI = "test_framework_si"
    COVERAGE_ANALYSIS_SI = "coverage_analysis_si"
    REGRESSION_TESTING_SI = "regression_testing_si"
    CODE_GENERATION_SI = "code_generation_si"
    UIUX_DESIGN_SI = "uiux_design_si"
    DATABASE_DESIGN_SI = "database_design_si"
    API_DESIGN_SI = "api_design_si"
    BUG_FIXING_SI = "bug_fixing_si"
    REFACTORING_SI = "refactoring_si"
    SELF_EVOLUTION_SI = "self_evolution_si"
    VERSION_CONTROL_SI = "version_control_si"
    REQUIREMENTS_BUREAU = "requirements_bureau"
    ARCHITECTURE_BUREAU = "architecture_bureau"
    STANDARDS_BUREAU = "standards_bureau"
    REVIEW_BUREAU = "review_bureau"
    CODE_REVIEW_BUREAU = "code_review_bureau"
    TESTING_BUREAU = "testing_bureau"
    QUALITY_MONITOR_BUREAU = "quality_monitor_bureau"
    COMPLIANCE_BUREAU = "compliance_bureau"


class CollaborationMode(str, Enum):
    """协作模式枚举"""
    PRIMARY = "primary"
    SUPPORTING = "supporting"
    CONSULTING = "consulting"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


@dataclass
class MappingEntry:
    """映射条目"""

    department_id: DepartmentID
    agent_ids: list[str] = field(default_factory=list)
    collaboration_mode: CollaborationMode = CollaborationMode.PRIMARY
    priority: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "department": self.department_id.value,
            "agents": self.agent_ids,
            "mode": self.collaboration_mode.value,
            "priority": self.priority,
        }


class DepartmentMapper:
    """
    部门映射器

    维护三省六部二十四司与 agency-agents 的完整映射矩阵，
    提供双向查询、协作推荐和覆盖率分析等功能。
    """

    DEPARTMENT_AGENT_MAP: dict[DepartmentID, MappingEntry] = {
        DepartmentID.AGENT_DISPATCH_SI: MappingEntry(
            department_id=DepartmentID.AGENT_DISPATCH_SI,
            agent_ids=["specialized_agents_orchestrator"],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.ROLE_MANAGEMENT_SI: MappingEntry(
            department_id=DepartmentID.ROLE_MANAGEMENT_SI,
            agent_ids=["specialized_workflow_architect", "project_manager_senior"],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.SKILL_MATCHING_SI: MappingEntry(
            department_id=DepartmentID.SKILL_MATCHING_SI,
            agent_ids=["specialized_mcp_builder", "engineering_senior_developer"],
            collaboration_mode=CollaborationMode.CONSULTING,
            priority=2,
        ),
        DepartmentID.COORDINATION_SI: MappingEntry(
            department_id=DepartmentID.COORDINATION_SI,
            agent_ids=[
                "project_management_studio_producer",
                "project_management_project_shepherd",
                "specialized_agents_orchestrator",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.ENVIRONMENT_CONFIG_SI: MappingEntry(
            department_id=DepartmentID.ENVIRONMENT_CONFIG_SI,
            agent_ids=["engineering_devops_automator", "engineering_sre"],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.DEPENDENCY_MGMT_SI: MappingEntry(
            department_id=DepartmentID.DEPENDENCY_MGMT_SI,
            agent_ids=["engineering_devops_automator", "engineering_backend_architect"],
            collaboration_mode=CollaborationMode.SUPPORTING,
            priority=2,
        ),
        DepartmentID.RESOURCE_OPTIMIZATION_SI: MappingEntry(
            department_id=DepartmentID.RESOURCE_OPTIMIZATION_SI,
            agent_ids=["engineering_database_optimizer", "engineering_sre"],
            collaboration_mode=CollaborationMode.CONSULTING,
            priority=3,
        ),
        DepartmentID.INFRASTRUCTURE_SI: MappingEntry(
            department_id=DepartmentID.INFRASTRUCTURE_SI,
            agent_ids=[
                "support_infrastructure_maintainer",
                "engineering_devops_automator",
                "engineering_sre",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.DOCUMENTATION_SI: MappingEntry(
            department_id=DepartmentID.DOCUMENTATION_SI,
            agent_ids=[
                "engineering_technical_writer",
                "specialized_document_generator",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.TEMPLATE_MANAGEMENT_SI: MappingEntry(
            department_id=DepartmentID.TEMPLATE_MANAGEMENT_SI,
            agent_ids=["specialized_document_generator", "design_ui_designer"],
            collaboration_mode=CollaborationMode.SUPPORTING,
            priority=2,
        ),
        DepartmentID.KNOWLEDGE_BASE_SI: MappingEntry(
            department_id=DepartmentID.KNOWLEDGE_BASE_SI,
            agent_ids=[
                "specialized_document_generator",
                "product_trend_researcher",
            ],
            collaboration_mode=CollaborationMode.CONSULTING,
            priority=3,
        ),
        DepartmentID.STANDARDIZATION_SI: MappingEntry(
            department_id=DepartmentID.STANDARDIZATION_SI,
            agent_ids=[
                "specialized_compliance_auditor",
                "engineering_code_reviewer",
            ],
            collaboration_mode=CollaborationMode.CONSULTING,
            priority=2,
        ),
        DepartmentID.TDD_EXECUTION_SI: MappingEntry(
            department_id=DepartmentID.TDD_EXECUTION_SI,
            agent_ids=[
                "testing_evidence_collector",
                "testing_api_tester",
                "engineering_senior_developer",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.TEST_FRAMEWORK_SI: MappingEntry(
            department_id=DepartmentID.TEST_FRAMEWORK_SI,
            agent_ids=[
                "testing_reality_checker",
                "testing_performance_benchmarker",
                "engineering_senior_developer",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.COVERAGE_ANALYSIS_SI: MappingEntry(
            department_id=DepartmentID.COVERAGE_ANALYSIS_SI,
            agent_ids=["testing_tool_evaluator", "testing_test_results_analyzer"],
            collaboration_mode=CollaborationMode.SUPPORTING,
            priority=2,
        ),
        DepartmentID.REGRESSION_TESTING_SI: MappingEntry(
            department_id=DepartmentID.REGRESSION_TESTING_SI,
            agent_ids=[
                "testing_api_tester",
                "testing_evidence_collector",
                "testing_workflow_optimizer",
            ],
            collaboration_mode=CollaborationMode.SEQUENTIAL,
            priority=2,
        ),
        DepartmentID.CODE_GENERATION_SI: MappingEntry(
            department_id=DepartmentID.CODE_GENERATION_SI,
            agent_ids=[
                "engineering_frontend_developer",
                "engineering_backend_architect",
                "engineering_senior_developer",
                "engineering_rapid_prototyper",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.UIUX_DESIGN_SI: MappingEntry(
            department_id=DepartmentID.UIUX_DESIGN_SI,
            agent_ids=[
                "design_ui_designer",
                "design_ux_researcher",
                "design_ux_architect",
                "design_visual_storyteller",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.DATABASE_DESIGN_SI: MappingEntry(
            department_id=DepartmentID.DATABASE_DESIGN_SI,
            agent_ids=[
                "engineering_database_optimizer",
                "engineering_data_engineer",
                "engineering_backend_architect",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.API_DESIGN_SI: MappingEntry(
            department_id=DepartmentID.API_DESIGN_SI,
            agent_ids=[
                "engineering_backend_architect",
                "engineering_software_architect",
                "engineering_ai_engineer",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.BUG_FIXING_SI: MappingEntry(
            department_id=DepartmentID.BUG_FIXING_SI,
            agent_ids=[
                "engineering_senior_developer",
                "engineering_frontend_developer",
                "engineering_backend_architect",
                "testing_api_tester",
            ],
            collaboration_mode=CollaborationMode.PARALLEL,
            priority=1,
        ),
        DepartmentID.REFACTORING_SI: MappingEntry(
            department_id=DepartmentID.REFACTORING_SI,
            agent_ids=[
                "engineering_senior_developer",
                "engineering_software_architect",
                "engineering_code_reviewer",
            ],
            collaboration_mode=CollaborationMode.SEQUENTIAL,
            priority=2,
        ),
        DepartmentID.SELF_EVOLUTION_SI: MappingEntry(
            department_id=DepartmentID.SELF_EVOLUTION_SI,
            agent_ids=[
                "engineering_autonomous_optimization_architect",
                "engineering_senior_developer",
                "specialized_workflow_architect",
            ],
            collaboration_mode=CollaborationMode.CONSULTING,
            priority=3,
        ),
        DepartmentID.VERSION_CONTROL_SI: MappingEntry(
            department_id=DepartmentID.VERSION_CONTROL_SI,
            agent_ids=[
                "engineering_git_workflow_master",
                "engineering_senior_developer",
                "engineering_code_reviewer",
            ],
            collaboration_mode=CollaborationMode.SUPPORTING,
            priority=2,
        ),
        DepartmentID.REQUIREMENTS_BUREAU: MappingEntry(
            department_id=DepartmentID.REQUIREMENTS_BUREAU,
            agent_ids=[
                "product_manager",
                "product_sprint_prioritizer",
                "product_trend_researcher",
                "product_feedback_synthesizer",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.ARCHITECTURE_BUREAU: MappingEntry(
            department_id=DepartmentID.ARCHITECTURE_BUREAU,
            agent_ids=[
                "engineering_software_architect",
                "engineering_backend_architect",
                "engineering_ai_engineer",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.STANDARDS_BUREAU: MappingEntry(
            department_id=DepartmentID.STANDARDS_BUREAU,
            agent_ids=[
                "specialized_compliance_auditor",
                "engineering_security_engineer",
                "engineering_code_reviewer",
            ],
            collaboration_mode=CollaborationMode.CONSULTING,
            priority=2,
        ),
        DepartmentID.REVIEW_BUREAU: MappingEntry(
            department_id=DepartmentID.REVIEW_BUREAU,
            agent_ids=[
                "engineering_code_reviewer",
                "engineering_senior_developer",
                "testing_reality_checker",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.CODE_REVIEW_BUREAU: MappingEntry(
            department_id=DepartmentID.CODE_REVIEW_BUREAU,
            agent_ids=[
                "engineering_code_reviewer",
                "engineering_senior_developer",
                "engineering_security_engineer",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.TESTING_BUREAU: MappingEntry(
            department_id=DepartmentID.TESTING_BUREAU,
            agent_ids=[
                "testing_evidence_collector",
                "testing_api_tester",
                "testing_reality_checker",
                "testing_performance_benchmarker",
                "testing_accessibility_auditor",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
        DepartmentID.QUALITY_MONITOR_BUREAU: MappingEntry(
            department_id=DepartmentID.QUALITY_MONITOR_BUREAU,
            agent_ids=[
                "testing_tool_evaluator",
                "testing_test_results_analyzer",
                "testing_workflow_optimizer",
                "support_analytics_reporter",
            ],
            collaboration_mode=CollaborationMode.SUPPORTING,
            priority=2,
        ),
        DepartmentID.COMPLIANCE_BUREAU: MappingEntry(
            department_id=DepartmentID.COMPLIANCE_BUREAU,
            agent_ids=[
                "specialized_compliance_auditor",
                "engineering_security_engineer",
                "engineering_threat_detection_engineer",
                "support_legal_compliance_checker",
            ],
            collaboration_mode=CollaborationMode.PRIMARY,
            priority=1,
        ),
    }

    def __init__(self) -> None:
        self._reverse_map: dict[str, list[DepartmentID]] = {}
        self._build_reverse_map()

    def _build_reverse_map(self) -> None:
        """构建反向索引（agent_id → departments）"""
        self._reverse_map.clear()
        for dept_id, entry in self.DEPARTMENT_AGENT_MAP.items():
            for agent_id in entry.agent_ids:
                self._reverse_map.setdefault(agent_id, []).append(dept_id)

    def get_agents_for_department(self, department_id: str | DepartmentID) -> list[str]:
        """
        获取某部门可用的 agents 列表

        Args:
            department_id: 部门 ID（字符串或枚举）

        Returns:
            该部门的 agent ID 列表
        """
        if isinstance(department_id, str):
            try:
                dept_enum = DepartmentID(department_id)
            except ValueError:
                return []
        else:
            dept_enum = department_id

        entry = self.DEPARTMENT_AGENT_MAP.get(dept_enum)
        return entry.agent_ids if entry else []

    def get_department_for_agent(self, agent_id: str) -> list[DepartmentID]:
        """
        获取某 agent 所属的部门列表

        Args:
            agent_id: agent 唯一标识符

        Returns:
            该 agent 关联的所有部门枚举列表
        """
        return self._reverse_map.get(agent_id, [])

    def get_collaboration_pattern(self, department_id: str | DepartmentID) -> CollaborationMode:
        """
        获取协作模式建议

        Args:
            department_id: 部门 ID

        Returns:
            推荐的协作模式
        """
        if isinstance(department_id, str):
            try:
                dept_enum = DepartmentID(department_id)
            except ValueError:
                return CollaborationMode.SEQUENTIAL
        else:
            dept_enum = department_id

        entry = self.DEPARTMENT_AGENT_MAP.get(dept_enum)
        return entry.collaboration_mode if entry else CollaborationMode.SEQUENTIAL

    def find_related_departments(
        self,
        department_id: str | DepartmentID,
        max_related: int = 5,
    ) -> list[tuple[DepartmentID, float]]:
        """
        查找关联部门（跨部门协作推荐）

        Args:
            department_id: 目标部门 ID
            max_related: 返回数量上限

        Returns:
            (关联部门, 相似度分数) 列表，按相似度降序排列
        """
        if isinstance(department_id, str):
            try:
                target_dept = DepartmentID(department_id)
            except ValueError:
                return []
        else:
            target_dept = department_id

        target_entry = self.DEPARTMENT_AGENT_MAP.get(target_dept)
        if not target_entry:
            return []

        target_agents = set(target_entry.agent_ids)
        related: list[tuple[DepartmentID, float]] = []

        for dept_id, entry in self.DEPARTMENT_AGENT_MAP.items():
            if dept_id == target_dept:
                continue

            other_agents = set(entry.agent_ids)
            intersection = target_agents & other_agents
            union = target_agents | other_agents

            if union:
                jaccard = len(intersection) / len(union)
                if jaccard > 0:
                    related.append((dept_id, jaccard))

        related.sort(key=lambda x: x[1], reverse=True)
        return related[:max_related]

    def validate_mapping_coverage(self) -> dict[str, Any]:
        """
        验证映射覆盖率

        Returns:
            包含覆盖统计的字典
        """
        total_departments = len(DepartmentID)
        mapped_departments = len(self.DEPARTMENT_AGENT_MAP)
        total_mappings = sum(len(e.agent_ids) for e in self.DEPARTMENT_AGENT_MAP.values())

        unique_agents: set[str] = set()
        for entry in self.DEPARTMENT_AGENT_MAP.values():
            unique_agents.update(entry.agent_ids)

        mode_distribution: dict[CollaborationMode, int] = {}
        for entry in self.DEPARTMENT_AGENT_MAP.values():
            mode_distribution[entry.collaboration_mode] = mode_distribution.get(entry.collaboration_mode, 0) + 1

        unmapped = [d.value for d in DepartmentID if d not in self.DEPARTMENT_AGENT_MAP]

        return {
            "total_departments": total_departments,
            "mapped_departments": mapped_departments,
            "coverage_percentage": round(mapped_departments / total_departments * 100, 1),
            "total_agent_mappings": total_mappings,
            "unique_agents_covered": len(unique_agents),
            "avg_agents_per_department": round(total_mappings / mapped_departments, 1) if mapped_departments else 0,
            "collaboration_mode_distribution": {m.value: c for m, c in mode_distribution.items()},
            "unmapped_departments": unmapped,
        }

    def export_mapping_matrix(self) -> str:
        """
        导出映射矩阵为 Markdown 表格

        Returns:
            Markdown 格式的映射矩阵表格
        """
        lines = [
            "# 三省六部二十四司 ↔ Agency-Agents 映射矩阵",
            "\n| 部门 | Agents | 协作模式 | 优先级 |",
            "|------|--------|----------|--------|",
        ]

        dept_order = [
            ("中书省（决策层）", [
                DepartmentID.REQUIREMENTS_BUREAU,
                DepartmentID.ARCHITECTURE_BUREAU,
                DepartmentID.STANDARDS_BUREAU,
                DepartmentID.REVIEW_BUREAU,
            ]),
            ("门下省（审核层）", [
                DepartmentID.CODE_REVIEW_BUREAU,
                DepartmentID.TESTING_BUREAU,
                DepartmentID.QUALITY_MONITOR_BUREAU,
                DepartmentID.COMPLIANCE_BUREAU,
            ]),
            ("尚书省·吏部", [
                DepartmentID.AGENT_DISPATCH_SI,
                DepartmentID.ROLE_MANAGEMENT_SI,
                DepartmentID.SKILL_MATCHING_SI,
                DepartmentID.COORDINATION_SI,
            ]),
            ("尚书省·户部", [
                DepartmentID.ENVIRONMENT_CONFIG_SI,
                DepartmentID.DEPENDENCY_MGMT_SI,
                DepartmentID.RESOURCE_OPTIMIZATION_SI,
                DepartmentID.INFRASTRUCTURE_SI,
            ]),
            ("尚书省·礼部", [
                DepartmentID.DOCUMENTATION_SI,
                DepartmentID.TEMPLATE_MANAGEMENT_SI,
                DepartmentID.KNOWLEDGE_BASE_SI,
                DepartmentID.STANDARDIZATION_SI,
            ]),
            ("尚书省·兵部", [
                DepartmentID.TDD_EXECUTION_SI,
                DepartmentID.TEST_FRAMEWORK_SI,
                DepartmentID.COVERAGE_ANALYSIS_SI,
                DepartmentID.REGRESSION_TESTING_SI,
            ]),
            ("尚书省·工部", [
                DepartmentID.CODE_GENERATION_SI,
                DepartmentID.UIUX_DESIGN_SI,
                DepartmentID.DATABASE_DESIGN_SI,
                DepartmentID.API_DESIGN_SI,
            ]),
            ("尚书省·刑部", [
                DepartmentID.BUG_FIXING_SI,
                DepartmentID.REFACTORING_SI,
                DepartmentID.SELF_EVOLUTION_SI,
                DepartmentID.VERSION_CONTROL_SI,
            ]),
        ]

        for group_name, dept_list in dept_order:
            lines.append(f"\n### {group_name}\n")
            for dept_id in dept_list:
                entry = self.DEPARTMENT_AGENT_MAP.get(dept_id)
                if entry:
                    agents_str = ", ".join(f"`{a}`" for a in entry.agent_ids[:3])
                    if len(entry.agent_ids) > 3:
                        agents_str += f" (+{len(entry.agent_ids)-3})"
                    lines.append(
                        f"| {dept_id.value} | {agents_str} | "
                        f"{entry.collaboration_mode.value} | {entry.priority} |"
                    )
                else:
                    lines.append(f"| {dept_id.value} | *(未映射)* | - | - |")

        stats = self.validate_mapping_coverage()
        lines.extend([
            f"\n## 映射统计\n",
            f"- **总部门数**: {stats['total_departments']}",
            f"- **已映射**: {stats['mapped_departments']} ({stats['coverage_percentage']}%)",
            f"- **总映射数**: {stats['total_agent_mappings']}",
            f"- **覆盖Agents**: {stats['unique_agents_covered']}",
            f"- **平均每部门**: {stats['avg_agents_per_department']} agents\n",
        ])

        return "\n".join(lines)

    def get_all_mappings(self) -> dict[DepartmentID, MappingEntry]:
        """获取完整映射字典"""
        return dict(self.DEPARTMENT_AGENT_MAP)


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 部门映射器测试")
    print("=" * 60)

    mapper = DepartmentMapper()

    print("\n--- 映射覆盖率验证 ---")
    coverage = mapper.validate_mapping_coverage()
    print(f"✅ 总部门数: {coverage['total_departments']}")
    print(f"✅ 已映射: {coverage['mapped_departments']} ({coverage['coverage_percentage']}%)")
    print(f"✅ 总映射数: {coverage['total_agent_mappings']}")
    print(f"✅ 覆盖Agents: {coverage['unique_agents_covered']}")
    print(f"✅ 协作模式分布: {coverage['collaboration_mode_distribution']}")

    print("\n--- 部门查询测试 ---")
    test_deps = ["code_generation_si", "testing_bureau", "requirements_bureau"]
    for dep in test_deps:
        agents = mapper.get_agents_for_department(dep)
        mode = mapper.get_collaboration_pattern(dep)
        print(f"   {dep}: {len(agents)} agents ({mode.value})")
        print(f"      → {agents[:3]}")

    print("\n--- Agent反向查询 ---")
    test_agents = ["engineering_senior_developer", "testing_evidence_collector"]
    for agent in test_agents:
        depts = mapper.get_department_for_agent(agent)
        print(f"   {agent}: {[d.value for d in depts]}")

    print("\n--- 关联部门发现 ---")
    related = mapper.find_related_departments("code_generation_si", max_related=3)
    for dept, score in related:
        print(f"   {dept.value}: {score:.2f}")

    print("\n--- 导出映射矩阵 (预览) ---")
    matrix_md = mapper.export_mapping_matrix()
    print(matrix_md[:800])

    print("\n✅ 部门映射器测试通过!")
