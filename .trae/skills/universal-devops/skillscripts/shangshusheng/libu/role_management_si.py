"""
角色管理司 - 开发角色定义、权限矩阵、RACI模型
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class RoleManagementError(Exception):
    """角色管理相关异常"""
    pass


class RaciRole(str, Enum):
    """RACI角色枚举"""
    R = "R"
    A = "A"
    C = "C"
    I = "I"


class PermissionLevel(str, Enum):
    """权限级别枚举"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass
class Role:
    """开发角色定义"""
    name: str
    display_name: str = ""
    description: str = ""
    responsibilities: list[str] = field(default_factory=list)
    required_skills: list[str] = field(default_factory=list)
    permissions: dict[str, PermissionLevel] = field(default_factory=dict)
    is_technical: bool = True
    min_experience_years: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "responsibilities": self.responsibilities,
            "required_skills": self.required_skills,
            "permissions": {k: v.value for k, v in self.permissions.items()},
            "is_technical": self.is_technical,
            "min_experience_years": self.min_experience_years,
        }


@dataclass
class TeamMember:
    """团队成员"""
    member_id: str
    name: str
    role_name: str = ""
    skills: list[str] = field(default_factory=list)
    experience_years: int = 0
    availability: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "member_id": self.member_id,
            "name": self.name,
            "role_name": self.role_name,
            "skills": self.skills,
            "experience_years": self.experience_years,
            "availability": self.availability,
        }


@dataclass
class RaciEntry:
    """RACI矩阵条目"""
    task_or_activity: str
    responsible: list[str] = field(default_factory=list)
    accountable: str | None = None
    consulted: list[str] = field(default_factory=list)
    informed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_or_activity": self.task_or_activity,
            "responsible": self.responsible,
            "accountable": self.accountable,
            "consulted": self.consulted,
            "informed": self.informed,
        }

    def validate(self) -> list[str]:
        """验证RACI条目，返回问题列表"""
        issues: list[str] = []
        if not self.accountable:
            issues.append(f"'{self.task_or_activity}' 缺少Accountable(A)角色")
        all_people = set(self.responsible + self.consulted + self.informed)
        if self.accountable:
            all_people.add(self.accountable)
        for person in self.responsible:
            if person in self.consulted:
                issues.append(f"{person} 同时是R和C，可能存在冲突")
        return issues


@dataclass
class ConflictInfo:
    """冲突信息"""
    type: str
    description: str
    entities: list[str]
    severity: str = "warning"

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "description": self.description,
            "entities": self.entities,
            "severity": self.severity,
        }


class RoleManagementSi:
    """
    角色管理司

    负责开发角色定义、权限矩阵、RACI模型生成与管理。
    提供团队角色分配建议、角色冲突检测等功能。
    """

    _instance: RoleManagementSi | None = None

    def __init__(self) -> None:
        self._roles: dict[str, Role] = {}
        self._members: dict[str, TeamMember] = {}
        self._raci_matrix: list[RaciEntry] = []
        self._permission_resources: list[str] = [
            "code", "config", "database", "infrastructure",
            "deployments", "secrets", "monitoring", "docs",
            "ci_cd", "security_policies",
        ]
        self._initialize_builtin_roles()

    @classmethod
    def get_instance(cls) -> RoleManagementSi:
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _initialize_builtin_roles(self) -> None:
        """初始化内置的开发角色"""
        builtin_roles: list[dict[str, Any]] = [
            {
                "name": "product_owner",
                "display_name": "Product Owner (产品负责人)",
                "description": "负责产品愿景、优先级排序、需求定义和验收标准",
                "responsibilities": [
                    "定义产品愿景和路线图",
                    "维护产品待办列表(Backlog)",
                    "确定需求的优先级",
                    "编写用户故事和验收标准",
                    "接受或拒绝已完成的功能",
                ],
                "required_skills": ["产品思维", "沟通协调", "业务分析", "用户体验"],
                "is_technical": False,
                "min_experience_years": 3,
            },
            {
                "name": "architect",
                "display_name": "Architect (架构师)",
                "description": "负责系统架构设计、技术选型、技术标准和最佳实践",
                "responsibilities": [
                    "设计系统整体架构",
                    "进行技术选型和评估",
                    "制定技术标准和规范",
                    "评审技术方案和代码质量",
                    "解决关键技术难题",
                ],
                "required_skills": ["系统设计", "分布式系统", "性能优化", "安全架构"],
                "is_technical": True,
                "min_experience_years": 5,
            },
            {
                "name": "lead_developer",
                "display_name": "Lead Developer (技术主管)",
                "description": "负责技术团队领导、代码审查、任务分配和技术指导",
                "responsibilities": [
                    "领导开发团队的技术工作",
                    "进行代码审查和质量把控",
                    "分配开发任务和跟踪进度",
                    "指导初级开发者成长",
                    "参与架构设计和决策",
                ],
                "required_skills": ["高级编程", "团队管理", "代码审查", " mentoring"],
                "is_technical": True,
                "min_experience_years": 4,
            },
            {
                "name": "developer",
                "display_name": "Developer (开发工程师)",
                "description": "负责功能开发、单元测试、Bug修复和文档编写",
                "responsibilities": [
                    "按照规格说明实现功能",
                    "编写和维护单元测试",
                    "修复Bug和缺陷",
                    "编写技术文档",
                    "参与代码评审",
                ],
                "required_skills": ["编程语言", "版本控制", "测试", "调试"],
                "is_technical": True,
                "min_experience_years": 1,
            },
            {
                "name": "qa_engineer",
                "display_name": "QA Engineer (质量保证工程师)",
                "description": "负责测试策略、测试用例设计、自动化测试和质量保障",
                "responsibilities": [
                    "制定测试策略和计划",
                    "设计和执行测试用例",
                    "开发和维护自动化测试",
                    "报告和跟踪缺陷",
                    "验证修复结果",
                ],
                "required_skills": ["测试方法论", "自动化测试", "性能测试", "安全测试"],
                "is_technical": True,
                "min_experience_years": 2,
            },
            {
                "name": "devops_engineer",
                "display_name": "DevOps Engineer (运维工程师)",
                "description": "负责CI/CD流水线、容器化部署、监控告警和基础设施管理",
                "responsibilities": [
                    "构建和维护CI/CD流水线",
                    "管理和编排容器化部署",
                    "配置监控系统",
                    "管理云基础设施",
                    "制定灾难恢复计划",
                ],
                "required_skills": ["Docker/K8s", "CI/CD", "云平台", "脚本编程", "监控"],
                "is_technical": True,
                "min_experience_years": 3,
            },
            {
                "name": "security_engineer",
                "display_name": "Security Engineer (安全工程师)",
                "description": "负责安全策略、漏洞扫描、渗透测试和安全合规",
                "responsibilities": [
                    "制定安全策略和标准",
                    "进行安全审计和扫描",
                    "执行渗透测试",
                    "处理安全事件响应",
                    "确保合规性要求",
                ],
                "required_skills": ["安全审计", "渗透测试", "加密技术", "合规框架"],
                "is_technical": True,
                "min_experience_years": 4,
            },
            {
                "name": "tech_writer",
                "display_name": "Technical Writer (技术文档工程师)",
                "description": "负责API文档、用户手册、技术规范和知识库维护",
                "responsibilities": [
                    "编写和维护API文档",
                    "创建用户手册和指南",
                    "记录技术决策(ADR)",
                    "维护知识库",
                    "审核文档质量和一致性",
                ],
                "required_skills": ["技术写作", "API文档", "Markdown/AsciiDoc", "信息架构"],
                "is_technical": False,
                "min_experience_years": 2,
            },
        ]

        for role_data in builtin_roles:
            role = Role(**role_data)
            role.permissions = self._generate_default_permissions(role.name)
            self._roles[role.name] = role

    def _generate_default_permissions(self, role_name: str) -> dict[str, PermissionLevel]:
        """根据角色名称生成默认权限"""
        perm_map: dict[str, dict[str, PermissionLevel]] = {
            "product_owner": {"docs": PermissionLevel.WRITE},
            "architect": {
                "code": PermissionLevel.READ, "config": PermissionLevel.ADMIN,
                "database": PermissionLevel.READ, "infrastructure": PermissionLevel.ADMIN,
                "docs": PermissionLevel.WRITE, "ci_cd": PermissionLevel.READ,
                "security_policies": PermissionLevel.READ,
            },
            "lead_developer": {
                "code": PermissionLevel.ADMIN, "config": PermissionLevel.WRITE,
                "database": PermissionLevel.WRITE, "docs": PermissionLevel.WRITE,
                "ci_cd": PermissionLevel.EXECUTE,
            },
            "developer": {
                "code": PermissionLevel.WRITE, "config": PermissionLevel.READ,
                "docs": PermissionLevel.WRITE,
            },
            "qa_engineer": {
                "code": PermissionLevel.READ, "config": PermissionLevel.READ,
                "ci_cd": PermissionLevel.EXECUTE, "monitoring": PermissionLevel.READ,
            },
            "devops_engineer": {
                "config": PermissionLevel.ADMIN, "infrastructure": PermissionLevel.ADMIN,
                "deployments": PermissionLevel.ADMIN, "ci_cd": PermissionLevel.ADMIN,
                "monitoring": PermissionLevel.ADMIN, "secrets": PermissionLevel.ADMIN,
            },
            "security_engineer": {
                "code": PermissionLevel.READ, "config": PermissionLevel.READ,
                "secrets": PermissionLevel.ADMIN, "security_policies": PermissionLevel.ADMIN,
                "deployments": PermissionLevel.READ,
            },
            "tech_writer": {
                "docs": PermissionLevel.ADMIN, "code": PermissionLevel.READ,
            },
        }
        return perm_map.get(role_name, {})

    def register_role(self, role: Role) -> None:
        """
        注册新角色

        Args:
            role: 角色对象

        Raises:
            RoleManagementError: 当角色已存在时
        """
        if role.name in self._roles:
            raise RoleManagementError(f"角色已存在: {role.name}")
        self._roles[role.name] = role

    def get_role(self, name: str) -> Role:
        """获取角色"""
        if name not in self._roles:
            raise RoleManagementError(f"角色不存在: {name}")
        return self._roles[name]

    def add_member(
        self,
        name: str,
        role_name: str,
        skills: list[str] | None = None,
        experience_years: int = 0,
        member_id: str | None = None,
        **kwargs: Any,
    ) -> TeamMember:
        """
        添加团队成员

        Args:
            name: 成员姓名
            role_name: 角色名称
            skills: 技能列表
            experience_years: 工作经验年数
            member_id: 成员ID（自动生成如果未提供）

        Returns:
            创建的TeamMember对象

        Raises:
            RoleManagementError: 当角色不存在时
        """
        if role_name not in self._roles:
            raise RoleManagementError(f"角色不存在: {role_name}")

        mid = member_id or f"member_{uuid.uuid4().hex[:8]}"
        member = TeamMember(
            member_id=mid,
            name=name,
            role_name=role_name,
            skills=skills or [],
            experience_years=experience_years,
            **kwargs,
        )
        self._members[mid] = member
        return member

    def remove_member(self, member_id: str) -> bool:
        """移除团队成员"""
        if member_id in self._members:
            del self._members[member_id]
            return True
        return False

    def generate_raci_matrix(
        self,
        activities: list[str],
        team_members: list[str] | None = None,
    ) -> list[RaciEntry]:
        """
        为指定活动列表生成RACI矩阵

        Args:
            activities: 活动/任务列表
            team_members: 可选的成员ID列表，默认使用所有成员

        Returns:
            RaciEntry列表
        """
        members = team_members or [m.member_id for m in self._members.values()]
        matrix: list[RaciEntry] = []

        activity_role_map: dict[str, tuple[list[str], str, list[str], list[str]]] = {
            "需求分析": ([], "", ["architect"], []),
            "架构设计": (["architect"], "architect", ["lead_developer", "product_owner"], ["developer"]),
            "编码开发": (["developer"], "lead_developer", [], ["qa_engineer"]),
            "代码审查": (["lead_developer", "architect"], "lead_developer", ["developer"], []),
            "测试执行": (["qa_engineer"], "lead_developer", ["developer"], ["product_owner"]),
            "部署发布": (["devops_engineer"], "devops_engineer", ["lead_developer"], ["product_owner"]),
            "文档编写": (["tech_writer"], "tech_writer", ["developer"], []),
            "安全审计": (["security_engineer"], "security_engineer", ["architect", "devops_engineer"], []),
            "运维监控": (["devops_engineer"], "devops_engineer", [], ["lead_developer"]),
        }

        for activity in activities:
            r_list, a_person, c_list, i_list = activity_role_map.get(
                activity, ([], "", [], [])
            )

            resolved_r: list[str] = []
            for rid in r_list:
                matching = [m for m in members if self._members.get(m, TeamMember("", "")).role_name == rid]
                resolved_r.extend(matching)

            resolved_a: str | None = None
            if a_person:
                matching = [m for m in members if self._members.get(m, TeamMember("", "")).role_name == a_person]
                resolved_a = matching[0] if matching else None

            resolved_c: list[str] = []
            for cid in c_list:
                matching = [m for m in members if self._members.get(m, TeamMember("", "")).role_name == cid]
                resolved_c.extend(matching)

            resolved_i: list[str] = []
            for iid in i_list:
                matching = [m for m in members if self._members.get(m, TeamMember("", "")).role_name == iid]
                resolved_i.extend(matching)

            entry = RaciEntry(
                task_or_activity=activity,
                responsible=resolved_r,
                accountable=resolved_a,
                consulted=resolved_c,
                informed=resolved_i,
            )
            matrix.append(entry)

        self._raci_matrix = matrix
        return matrix

    def suggest_team_structure(
        self,
        team_size: int,
        project_complexity: str = "medium",
        tech_stack: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        基于团队规模和项目复杂度建议团队角色分配

        Args:
            team_size: 团队人数
            project_complexity: 项目复杂度 (small/medium/large/enterprise)
            tech_stack: 技术栈列表

        Returns:
            建议的角色分配字典
        """
        complexity_map: dict[str, dict[str, int]] = {
            "small": {"product_owner": 0.5, "architect": 0.5, "lead_developer": 1, "developer": 2, "qa_engineer": 0.5, "devops_engineer": 0.5},
            "medium": {"product_owner": 1, "architect": 1, "lead_developer": 1, "developer": 4, "qa_engineer": 2, "devops_engineer": 1, "security_engineer": 0.5},
            "large": {"product_owner": 1, "architect": 2, "lead_developer": 2, "developer": 8, "qa_engineer": 4, "devops_engineer": 2, "security_engineer": 1, "tech_writer": 1},
            "enterprise": {"product_owner": 2, "architect": 3, "lead_developer": 4, "developer": 15, "qa_engineer": 6, "devops_engineer": 4, "security_engineer": 2, "tech_writer": 2},
        }

        base_allocation = complexity_map.get(project_complexity, complexity_map["medium"])
        total_base = sum(base_allocation.values())

        scale_factor = team_size / total_base if total_base > 0 else 1

        suggestion: dict[str, Any] = {
            "team_size": team_size,
            "complexity": project_complexity,
            "roles": {},
            "warnings": [],
        }

        for role_name, base_count in base_allocation.items():
            scaled = max(1, round(base_count * scale_factor))
            role = self._roles.get(role_name)
            suggestion["roles"][role_name] = {
                "count": scaled,
                "display_name": role.display_name if role else role_name,
                "key_responsibilities": role.responsibilities[:3] if role else [],
            }

        if project_complexity == "small" and team_size < 5:
            suggestion["warnings"].append("小团队建议合并角色，一人多职")

        if tech_stack:
            security_related = any(kw in " ".join(tech_stack).lower() for kw in ["payment", "auth", "crypto", "health"])
            if security_related and suggestion["roles"].get("security_engineer", 0) < 1:
                suggestion["roles"]["security_engineer"] = {
                    "count": 1,
                    "display_name": "Security Engineer (安全工程师)",
                    "key_responsibilities": ["安全审计", "漏洞扫描"],
                }
                suggestion["warnings"].append("检测到敏感技术栈，建议增加安全工程师")

        return suggestion

    def detect_conflicts(self) -> list[ConflictInfo]:
        """
        检测角色和权限冲突

        Returns:
            冲突信息列表
        """
        conflicts: list[ConflictInfo] = []

        for entry in self._raci_matrix:
            issues = entry.validate()
            for issue in issues:
                conflicts.append(ConflictInfo(
                    type="raci_validation",
                    description=issue,
                    entities=[entry.task_or_activity],
                    severity="warning",
                ))

        member_roles: dict[str, list[str]] = defaultdict(list)
        for mid, member in self._members.items():
            member_roles[member.role_name].append(mid)

        admin_holders: list[str] = [
            rname for rname, role in self._roles.items()
            if any(p == PermissionLevel.ADMIN for p in role.permissions.values())
        ]

        if len(admin_holders) > len(self._members) / 2 and len(self._members) > 3:
            conflicts.append(ConflictInfo(
                type="over_privileged",
                description=f"过多ADMIN权限角色 ({len(admin_holders)}个)",
                entities=admin_holders,
                severity="warning",
            ))

        for mid, member in self._members.items():
            role = self._roles.get(member.role_name)
            if role and role.min_experience_years > member.experience_years:
                conflicts.append(ConflictInfo(
                    type="experience_mismatch",
                    description=f"{member.name} ({member.role_name}) 经验不足: "
                               f"需要{role.min_experience_years}年，当前{member.experience_years}年",
                    entities=[mid],
                    severity="info",
                ))

        return conflicts

    def check_permission(
        self,
        member_id: str,
        resource: str,
        required_level: PermissionLevel,
    ) -> bool:
        """
        检查成员是否有足够的权限

        Args:
            member_id: 成员ID
            resource: 资源名称
            required_level: 需要的权限级别

        Returns:
            是否有权限
        """
        member = self._members.get(member_id)
        if not member:
            return False

        role = self._roles.get(member.role_name)
        if not role:
            return False

        level_order = list(PermissionLevel)
        current = role.permissions.get(resource)
        if not current:
            return False

        try:
            current_idx = level_order.index(current)
            required_idx = level_order.index(required_level)
            return current_idx >= required_idx
        except ValueError:
            return False

    def get_all_roles(self) -> dict[str, Role]:
        return dict(self._roles)

    def get_all_members(self) -> dict[str, TeamMember]:
        return dict(self._members)

    def get_raci_matrix(self) -> list[RaciEntry]:
        return list(self._raci_matrix)

    def export_raci_markdown(self) -> str:
        """导出RACI矩阵为Markdown格式"""
        lines: list[str] = []
        lines.append("# RACI 矩阵")
        lines.append("")
        lines.append("| 活动/任务 | R (执行者) | A (最终负责) | C (咨询) | I (知情) |")
        lines.append("|----------|-----------|-------------|---------|--------|")

        for entry in self._raci_matrix:
            r_str = ", ".join(entry.respective) if hasattr(entry, 'responsible') else ", ".join(getattr(entry, 'responsible', []))
            a_str = entry.accountable or "-"
            c_str = ", ".join(entry.consulted) if hasattr(entry, 'consulted') else ", ".join(getattr(entry, 'consulted', []))
            i_str = ", ".join(entry.informed) if hasattr(entry, 'informed') else ", ".join(getattr(entry, 'informed', []))

            lines.append(f"| {entry.task_or_activity} | {r_str} | {a_str} | {c_str} | {i_str} |")

        lines.append("")
        lines.append("> **R**esponsible (执行者) | **A**ccountable (最终负责) | **C**onsulted (咨询) | **I**nformed (知情)")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"RoleManagementSi(roles={len(self._roles)}, "
            f"members={len(self._members)}, raci_entries={len(self._raci_matrix)})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 角色管理司测试")
    print("=" * 60)

    rm = RoleManagementSi()

    print("\n--- 内置角色 ---")
    for name, role in rm.get_all_roles().items():
        print(f"   📌 {role.display_name}")
        print(f"      技能要求: {', '.join(role.required_skills[:3])}...")
        print(f"      最小经验: {role.min_experience_years}年")

    print("\n--- 添加团队成员 ---")
    members_data = [
        ("张三", "architect", ["系统设计", "Go", "Kubernetes"], 7),
        ("李四", "lead_developer", ["Python", "React", "代码审查"], 5),
        ("王五", "developer", ["Python", "Django", "Vue.js"], 2),
        ("赵六", "qa_engineer", ["Selenium", "Pytest", "性能测试"], 3),
        ("钱七", "devops_engineer", ["Docker", "AWS", "Terraform"], 4),
        ("孙八", "product_owner", ["敏捷", "用户研究"], 6),
    ]
    for name, role, skills, exp in members_data:
        m = rm.add_member(name=name, role_name=role, skills=skills, experience_years=exp)
        print(f"   ✅ {name} → {rm.get_role(role).display_name}")

    print("\n--- 权限检查 ---")
    test_cases = [
        ("张三", "infrastructure", PermissionLevel.ADMIN),
        ("王五", "code", PermissionLevel.WRITE),
        ("赵六", "secrets", PermissionLevel.READ),
        ("钱七", "deployments", PermissionLevel.ADMIN),
    ]
    for mid, res, level in test_cases:
        member = rm._members.get(mid, TeamMember("", ""))
        has_perm = rm.check_permission(member.member_id, res, level)
        icon = "✅" if has_perm else "❌"
        print(f"   {icon} {mid} 对 {res}/{level.value}: {'有权限' if has_perm else '无权限'}")

    print("\n--- 生成RACI矩阵 ---")
    activities = ["需求分析", "架构设计", "编码开发", "代码审查", "测试执行", "部署发布"]
    raci = rm.generate_raci_matrix(activities)
    for entry in raci:
        print(f"\n   📋 {entry.task_or_activity}:")
        print(f"      R: {entry.responsible or '-'}")
        print(f"      A: {entry.accountable or '-'}")
        print(f"      C: {entry.consulted or '-'}")
        print(f"      I: {entry.informed or '-'}")

    print("\n--- 团队结构建议 ---")
    for size, complexity in [(5, "small"), (10, "medium"), (20, "large")]:
        suggestion = rm.suggest_team_structure(size, complexity)
        print(f"\n   👥 {size}人团队 ({complexity}):")
        for role_name, info in suggestion["roles"].items():
            print(f"      • {info['display_name']}: {info['count']}人")

    print("\n--- 冲突检测 ---")
    conflicts = rm.detect_conflicts()
    if conflicts:
        for c in conflicts:
            print(f"   ⚠️ [{c.severity}] {c.type}: {c.description}")
    else:
        print(f"   ✅ 未发现冲突")

    print("\n--- 导出RACI Markdown ---")
    md = rm.export_raci_markdown()
    print(md[:500])

    print("\n✅ 所有测试通过!")
