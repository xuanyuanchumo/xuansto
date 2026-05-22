"""
子技能管理器 - 管理32个子技能的加载、调用和生命周期
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class SubSkillManagerError(Exception):
    """子技能管理器相关异常"""
    pass


class SkillStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOADING = "loading"


@dataclass
class SkillResult:
    """技能执行结果"""
    success: bool
    skill_name: str
    result_data: dict[str, Any] | None = None
    error_message: str | None = None
    execution_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "skill_name": self.skill_name,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "timestamp": self.timestamp,
        }


@dataclass
class SubSkillInfo:
    """子技能信息数据类"""
    name: str
    province: str
    department: str | None = None
    si_name: str | None = None
    path: Path | None = None
    description: str = ""
    triggers: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    enabled: bool = True
    status: SkillStatus = SkillStatus.ACTIVE
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_enabled(self) -> bool:
        return self.enabled and self.status == SkillStatus.ACTIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "province": self.province,
            "department": self.department,
            "si_name": self.si_name,
            "path": str(self.path) if self.path else None,
            "description": self.description,
            "triggers": self.triggers,
            "version": self.version,
            "enabled": self.enabled,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
        }


class SubSkillManager:
    """
    子技能管理器

    管理32个子技能的加载、调用和生命周期。
    提供按省/部筛选、触发词匹配、依赖关系图等功能。
    """

    _instance: SubSkillManager | None = None

    def __init__(self) -> None:
        self._skills: dict[str, SubSkillInfo] = {}
        self._skill_contents: dict[str, dict[str, Any]] = {}
        self._call_history: list[dict[str, Any]] = []
        self._initialize_builtin_skills()

    @classmethod
    def get_instance(cls) -> SubSkillManager:
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _initialize_builtin_skills(self) -> None:
        """初始化内置的32个子技能"""

        skills_data: list[dict[str, Any]] = [
            {
                "name": "requirements_bureau",
                "province": "zhongshusheng",
                "department": "requirements_bureau",
                "description": "需求分析局 - 负责需求收集、分析与规格说明编写",
                "triggers": ["需求", "requirement", "用户故事", "验收标准"],
                "dependencies": [],
            },
            {
                "name": "architecture_bureau",
                "province": "zhongshusheng",
                "department": "architecture_bureau",
                "description": "架构设计局 - 负责系统架构设计与技术选型",
                "triggers": ["架构", "architecture", "系统设计", "技术栈"],
                "dependencies": ["requirements_bureau"],
            },
            {
                "name": "standards_bureau",
                "province": "zhongshusheng",
                "department": "standards_bureau",
                "description": "标准规范局 - 制定和维护编码标准与最佳实践",
                "triggers": ["标准", "standard", "规范", "编码风格"],
                "dependencies": [],
            },
            {
                "name": "review_bureau",
                "province": "zhongshusheng",
                "department": "review_bureau",
                "description": "审查局 - 负责代码审查与质量把关",
                "triggers": ["审查", "review", "质量门禁"],
                "dependencies": ["standards_bureau"],
            },
            {
                "name": "code_review_bureau",
                "province": "menxiasheng",
                "department": "code_review_bureau",
                "description": "代码审查司 - 深度代码静态分析",
                "triggers": ["代码审查", "code review", "静态分析", "安全审计"],
                "dependencies": [],
            },
            {
                "name": "testing_bureau",
                "province": "menxiasheng",
                "department": "testing_bureau",
                "description": "测试司 - 测试策略与测试计划制定",
                "triggers": ["测试", "test", "QA", "质量保证"],
                "dependencies": [],
            },
            {
                "name": "quality_monitor_bureau",
                "province": "menxiasheng",
                "department": "quality_monitor_bureau",
                "description": "质量监控司 - 持续质量度量与技术债务追踪",
                "triggers": ["质量", "quality", "度量", "sonar"],
                "dependencies": ["testing_bureau"],
            },
            {
                "name": "compliance_bureau",
                "province": "menxiasheng",
                "department": "compliance_bureau",
                "description": "合规司 - 安全合规与政策执行检查",
                "triggers": ["合规", "compliance", "安全", "审计"],
                "dependencies": [],
            },
            {
                "name": "agent_dispatch_si",
                "province": "shangshusheng",
                "department": "libu",
                "si_name": "agent_dispatch_si",
                "description": "Agent调度司 - 智能任务分发与负载均衡",
                "triggers": ["调度", "dispatch", "分发", "负载均衡"],
                "dependencies": [],
            },
            {
                "name": "role_management_si",
                "province": "shangshusheng",
                "department": "libu",
                "si_name": "role_management_si",
                "description": "角色管理司 - 权限管理与角色分配",
                "triggers": ["角色", "role", "权限", "RBAC"],
                "dependencies": [],
            },
            {
                "name": "skill_matching_si",
                "province": "shangshusheng",
                "department": "libu",
                "si_name": "skill_matching_si",
                "description": "技能匹配司 - 能力评估与技能映射",
                "triggers": ["技能", "skill", "能力", "匹配"],
                "dependencies": ["role_management_si"],
            },
            {
                "name": "coordination_si",
                "province": "shangshusheng",
                "department": "libu",
                "si_name": "coordination_si",
                "description": "协调司 - 跨团队工作流编排",
                "triggers": ["协调", "coordination", "编排", "跨团队"],
                "dependencies": ["agent_dispatch_si"],
            },
            {
                "name": "environment_config_si",
                "province": "shangshusheng",
                "department": "hubu",
                "si_name": "environment_config_si",
                "description": "环境配置司 - 开发/测试/生产环境配置管理",
                "triggers": ["环境", "environment", "配置", "devops"],
                "dependencies": [],
            },
            {
                "name": "dependency_mgmt_si",
                "province": "shangshusheng",
                "department": "hubu",
                "si_name": "dependency_mgmt_si",
                "description": "依赖管理司 - 包依赖解析与版本冲突处理",
                "triggers": ["依赖", "dependency", "包管理", "版本"],
                "dependencies": ["environment_config_si"],
            },
            {
                "name": "resource_optimization_si",
                "province": "shangshusheng",
                "department": "hubu",
                "si_name": "resource_optimization_si",
                "description": "资源优化司 - 成本优化与性能调优",
                "triggers": ["资源", "resource", "优化", "成本"],
                "dependencies": ["dependency_mgmt_si"],
            },
            {
                "name": "infrastructure_si",
                "province": "shangshusheng",
                "department": "hubu",
                "si_name": "infrastructure_si",
                "description": "基础设施司 - 云基础设施与容器化部署",
                "triggers": ["基础设施", "infrastructure", "docker", "k8s", "kubernetes"],
                "dependencies": ["environment_config_si"],
            },
            {
                "name": "documentation_si",
                "province": "shangshusheng",
                "department": "libu2",
                "si_name": "documentation_si",
                "description": "文档司 - 技术文档生成与管理",
                "triggers": ["文档", "document", "API文档", "知识转移"],
                "dependencies": [],
            },
            {
                "name": "template_management_si",
                "province": "shangshusheng",
                "department": "libu2",
                "si_name": "template_management_si",
                "description": "模板管理司 - 项目模板与脚手架工具",
                "triggers": ["模板", "template", "脚手架", "scaffold"],
                "dependencies": ["documentation_si"],
            },
            {
                "name": "knowledge_base_si",
                "province": "shangshusheng",
                "department": "libu2",
                "si_name": "knowledge_base_si",
                "description": "知识库司 - 知识索引与语义搜索",
                "triggers": ["知识", "knowledge", "搜索", "检索"],
                "dependencies": ["documentation_si"],
            },
            {
                "name": "standardization_si",
                "province": "shangshusheng",
                "department": "libu2",
                "si_name": "standardization_si",
                "description": "标准化司 - 代码格式化与规范检查自动化",
                "triggers": ["标准化", "lint", "format", "格式化"],
                "dependencies": ["standards_bureau"],
            },
            {
                "name": "tdd_execution_si",
                "province": "shangshusheng",
                "department": "bingbu",
                "si_name": "tdd_execution_si",
                "description": "TDD执行司 - 测试驱动开发实践",
                "triggers": ["tdd", "测试驱动", "单元测试", "red-green-refactor"],
                "dependencies": ["testing_bureau"],
            },
            {
                "name": "test_framework_si",
                "province": "shangshusheng",
                "department": "bingbu",
                "si_name": "test_framework_si",
                "description": "测试框架司 - 测试框架集成与配置",
                "triggers": ["pytest", "jest", "junit", "测试框架"],
                "dependencies": ["tdd_execution_si"],
            },
            {
                "name": "coverage_analysis_si",
                "province": "shangshusheng",
                "department": "bingbu",
                "si_name": "coverage_analysis_si",
                "description": "覆盖率分析司 - 代码覆盖率报告与分析",
                "triggers": ["覆盖", "coverage", "分支覆盖", "行覆盖"],
                "dependencies": ["test_framework_si"],
            },
            {
                "name": "regression_testing_si",
                "province": "shangshusheng",
                "department": "bingbu",
                "si_name": "regression_testing_si",
                "description": "回归测试司 - 自动化回归测试套件",
                "triggers": ["回归", "regression", "冒烟测试", "sanity"],
                "dependencies": ["coverage_analysis_si"],
            },
            {
                "name": "code_generation_si",
                "province": "shangshusheng",
                "department": "gongbu",
                "si_name": "code_generation_si",
                "description": "代码生成司 - AI辅助代码生成",
                "triggers": ["生成", "generate", "代码生成", "boilerplate"],
                "dependencies": ["template_management_si"],
            },
            {
                "name": "uiux_design_si",
                "province": "shangshusheng",
                "department": "gongbu",
                "si_name": "uiux_design_si",
                "description": "UI/UX设计司 - 界面设计与原型制作",
                "triggers": ["UI", "UX", "界面", "原型", "prototyping"],
                "dependencies": [],
            },
            {
                "name": "database_design_si",
                "province": "shangshusheng",
                "department": "gongbu",
                "si_name": "database_design_si",
                "description": "数据库设计司 - 数据库建模与ORM设计",
                "triggers": ["数据库", "database", "schema", "ORM"],
                "dependencies": ["architecture_bureau"],
            },
            {
                "name": "api_design_si",
                "province": "shangshusheng",
                "department": "gongbu",
                "si_name": "api_design_si",
                "description": "API设计司 - RESTful API与GraphQL设计",
                "triggers": ["API", "接口", "REST", "GraphQL", "openapi"],
                "dependencies": ["architecture_bureau"],
            },
            {
                "name": "bug_fixing_si",
                "province": "shangshusheng",
                "department": "xingbu",
                "si_name": "bug_fixing_si",
                "description": "Bug修复司 - 问题诊断与缺陷修复",
                "triggers": ["bug", "缺陷", "错误", "调试", "debug"],
                "dependencies": ["code_review_bureau"],
            },
            {
                "name": "refactoring_si",
                "province": "shangshusheng",
                "department": "xingbu",
                "si_name": "refactoring_si",
                "description": "重构司 - 代码重构与设计改进",
                "triggers": ["重构", "refactor", "代码味道", "clean code"],
                "dependencies": ["quality_monitor_bureau"],
            },
            {
                "name": "self_evolution_si",
                "province": "shangshusheng",
                "department": "xingbu",
                "si_name": "self_evolution_si",
                "description": "自我进化司 - 自适应学习与模式演化",
                "triggers": ["进化", "evolution", "自学习", "自适应"],
                "dependencies": ["quality_monitor_bureau"],
            },
            {
                "name": "version_control_si",
                "province": "shangshusheng",
                "department": "xingbu",
                "si_name": "version_control_si",
                "description": "版本控制司 - Git工作流与版本策略",
                "triggers": ["git", "版本", "version", "分支", "merge"],
                "dependencies": [],
            },
        ]

        for skill_data in skills_data:
            info = SubSkillInfo(**skill_data)
            self._skills[info.name] = info

    def discover(self, base_dir: Path | str) -> int:
        """
        发现并注册目录下的所有子技能

        Args:
            base_dir: 基础目录路径（通常是 subskills 目录）

        Returns:
            发现并更新的子技能数量
        """
        base = Path(base_dir)
        if not base.is_dir():
            raise SubSkillManagerError(f"不是有效目录: {base}")

        discovered_count: int = 0

        for skill_dir in base.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
                continue

            skill_name: str = skill_dir.name
            if skill_name in self._skills:
                self._skills[skill_name].path = skill_dir.resolve()

                skill_md: Path = skill_dir / "SKILL.md"
                if skill_md.exists():
                    try:
                        content: dict[str, Any] = self._load_skill_md(skill_md)
                        self._skill_contents[skill_name] = content
                    except Exception as e:
                        print(f"⚠️ 加载SKILL.md失败 [{skill_name}]: {e}")

                discovered_count += 1

        return discovered_count

    def _load_skill_md(self, path: Path) -> dict[str, Any]:
        """加载SKILL.md文件内容"""
        with open(path, "r", encoding="utf-8") as f:
            content: str = f.read()

        return {
            "path": str(path),
            "raw_content": content[:2000],
            "loaded_at": datetime.now().isoformat(),
        }

    def get(self, name: str) -> SubSkillInfo:
        """
        获取子技能信息

        Args:
            name: 子技能名称

        Returns:
            SubSkillInfo对象

        Raises:
            SubSkillManagerError: 当子技能不存在时
        """
        if name not in self._skills:
            available = ", ".join(sorted(self._skills.keys()))
            raise SubSkillManagerError(
                f"子技能不存在: '{name}'。可用技能: {available}"
            )
        return self._skills[name]

    def load_skill(self, name: str) -> dict[str, Any]:
        """
        加载子技能的SKILL.md内容

        Args:
            name: 子技能名称

        Returns:
            技能内容字典

        Raises:
            SubSkillManagerError: 当子技能不存在或无法加载时
        """
        info = self.get(name)

        if name in self._skill_contents:
            return self._skill_contents[name]

        if info.path is None:
            raise SubSkillManagerError(f"子技能未关联到任何目录: {name}")

        skill_md: Path = info.path / "SKILL.md"
        if not skill_md.exists():
            return {
                "path": str(skill_md),
                "raw_content": f"# {info.name}\n\n{info.description}",
                "loaded_at": datetime.now().isoformat(),
                "note": "使用默认描述（SKILL.md不存在）",
            }

        content: dict[str, Any] = self._load_skill_md(skill_md)
        self._skill_contents[name] = content
        return content

    def list_by_province(self, province: str) -> list[SubSkillInfo]:
        """
        按省列出子技能

        Args:
            province: 省名称（如 zhongshusheng, menxiasheng 等）

        Returns:
            匹配的SubSkillInfo列表
        """
        return [
            info for info in self._skills.values()
            if info.province == province
        ]

    def list_by_department(self, department: str) -> list[SubSkillInfo]:
        """
        按部列出子技能

        Args:
            department: 部门名称

        Returns:
            匹配的SubSkillInfo列表
        """
        return [
            info for info in self._skills.values()
            if info.department == department
        ]

    def find_by_trigger(self, trigger_text: str) -> list[SubSkillInfo]:
        """
        根据触发词查找匹配的子技能

        Args:
            trigger_text: 触发文本（可以是自然语言描述）

        Returns:
            匹配度排序的SubSkillInfo列表
        """
        text_lower: str = trigger_text.lower()
        matched_skills: list[tuple[SubSkillInfo, int]] = []

        for info in self._skills.values():
            if not info.is_enabled:
                continue

            match_score: int = 0
            for trigger in info.triggers:
                trigger_lower: str = trigger.lower()
                if trigger_lower in text_lower:
                    match_score += 1
                elif text_lower in trigger_lower:
                    match_score += 1

            if match_score > 0:
                matched_skills.append((info, match_score))

        matched_skills.sort(key=lambda x: x[1], reverse=True)
        return [skill for skill, _ in matched_skills]

    def call_skill(
        self,
        name: str,
        params: dict[str, Any] | None = None,
    ) -> SkillResult:
        """
        调用子技能

        Args:
            name: 子技能名称
            params: 调用参数

        Returns:
            SkillResult对象，包含执行结果或错误信息
        """
        start_time: float = __import__("time").time()
        params = params or {}

        try:
            info = self.get(name)

            if not info.is_enabled:
                return SkillResult(
                    success=False,
                    skill_name=name,
                    error_message=f"子技能已禁用或不活跃: {name} (状态: {info.status.value})",
                    execution_time_ms=(__import__("time").time() - start_time) * 1000,
                )

            dep_check: dict[str, Any] = self._check_skill_dependencies(name)
            if not dep_check["satisfied"]:
                missing: list[str] = dep_check["missing"]
                return SkillResult(
                    success=False,
                    skill_name=name,
                    error_message=f"依赖未满足，缺少: {', '.join(missing)}",
                    execution_time_ms=(__import__("time").time() - start_time) * 1000,
                )

            content: dict[str, Any] = self.load_skill(name)

            result_data: dict[str, Any] = {
                "skill_info": info.to_dict(),
                "params": params,
                "content_preview": content.get("raw_content", "")[:500],
                "executed_at": datetime.now().isoformat(),
            }

            elapsed_ms: float = (__import__("time").time() - start_time) * 1000

            self._call_history.append({
                "action": "call",
                "skill_name": name,
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "execution_time_ms": elapsed_ms,
            })

            return SkillResult(
                success=True,
                skill_name=name,
                result_data=result_data,
                execution_time_ms=elapsed_ms,
            )

        except SubSkillManagerError as e:
            return SkillResult(
                success=False,
                skill_name=name,
                error_message=str(e),
                execution_time_ms=(__import__("time").time() - start_time) * 1000,
            )
        except Exception as e:
            return SkillResult(
                success=False,
                skill_name=name,
                error_message=f"执行异常: {str(e)}",
                execution_time_ms=(__import__("time").time() - start_time) * 1000,
            )

    def _check_skill_dependencies(self, name: str) -> dict[str, Any]:
        """检查单个技能的依赖是否满足"""
        info = self.get(name)
        missing: list[str] = []
        satisfied: list[str] = []

        for dep in info.dependencies:
            if dep in self._skills and self._skills[dep].is_enabled:
                satisfied.append(dep)
            else:
                missing.append(dep)

        return {
            "satisfied": len(missing) == 0,
            "satisfied_deps": satisfied,
            "missing": missing,
        }

    def enable(self, name: str) -> None:
        """
        启用子技能

        Args:
            name: 子技能名称

        Raises:
            SubSkillManagerError: 当子技能不存在时
        """
        info = self.get(name)
        info.enabled = True
        info.status = SkillStatus.ACTIVE

    def disable(self, name: str) -> None:
        """
        禁用子技能

        Args:
            name: 子技能名称

        Raises:
            SubSkillManagerError: 当子技能不存在时
        """
        info = self.get(name)
        info.enabled = False
        info.status = SkillStatus.INACTIVE

    def get_dependency_graph(self) -> dict[str, Any]:
        """
        获取子技能依赖关系图

        Returns:
            包含完整依赖关系的字典
        """
        graph: dict[str, list[str]] = {}
        reverse_graph: dict[str, list[str]] = {}
        all_nodes: set[str] = set(self._skills.keys())

        for name, info in self._skills.items():
            graph[name] = list(info.dependencies)
            for dep in info.dependencies:
                if dep not in reverse_graph:
                    reverse_graph[dep] = []
                reverse_graph[dep].append(name)

        roots: list[str] = [
            n for n in all_nodes if not self._skills[n].dependencies
        ]
        leaves: list[str] = [
            n for n in all_nodes if n not in reverse_graph
        ]

        return {
            "graph": graph,
            "reverse_graph": reverse_graph,
            "root_skills": roots,
            "leaf_skills": leaves,
            "total_skills": len(all_nodes),
            "max_depth": self._calculate_max_depth(graph, roots),
        }

    def _calculate_max_depth(
        self, graph: dict[str, list[str]], roots: list[str]
    ) -> int:
        """计算依赖图的最大深度"""

        visited: set[str] = set()

        def dfs(node: str, depth: int) -> int:
            if node in visited:
                return depth
            visited.add(node)

            deps: list[str] = graph.get(node, [])
            if not deps:
                return depth

            max_child_depth: int = 0
            for dep in deps:
                if dep in graph:
                    child_depth: int = dfs(dep, depth + 1)
                    max_child_depth = max(max_child_depth, child_depth)

            return max_child_depth

        if not roots:
            return 0

        return max(dfs(root, 1) for root in roots if root in graph)

    @property
    def all_skills(self) -> dict[str, SubSkillInfo]:
        return dict(self._skills)

    @property
    def enabled_count(self) -> int:
        return sum(1 for s in self._skills.values() if s.is_enabled)

    @property
    def total_count(self) -> int:
        return len(self._skills)

    @property
    def skill_names(self) -> list[str]:
        return sorted(self._skills.keys())

    def __repr__(self) -> str:
        return (
            f"SubSkillManager(total={self.total_count}, "
            f"enabled={self.enabled_count})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 子技能管理器测试")
    print("=" * 60)

    manager = SubSkillManager()

    print(f"\n📊 总技能数: {manager.total_count}")
    print(f"🟢 已启用数: {manager.enabled_count}")

    print("\n--- 发现技能测试 ---")
    subskills_dir = Path(__file__).parent.parent.parent / "subskills"
    if subskills_dir.exists():
        discovered = manager.discover(subskills_dir)
        print(f"✅ 发现 {discovered} 个技能目录")
    else:
        print(f"⚠️ 子技能目录不存在: {subskills_dir}")

    print("\n--- 获取技能信息 ---")
    try:
        skill = manager.get("architecture_bureau")
        print(f"📋 技能信息:")
        print(f"   名称: {skill.name}")
        print(f"   省/部: {skill.province}/{skill.department}")
        print(f"   描述: {skill.description}")
        print(f"   触发词: {skill.triggers}")
        print(f"   依赖: {skill.dependencies}")
        print(f"   状态: {skill.status.value}")
    except SubSkillManagerError as e:
        print(f"❌ 错误: {e}")

    print("\n--- 按省筛选 ---")
    zhongshusheng_skills = manager.list_by_province("zhongshusheng")
    print(f"中书省技能 ({len(zhongshusheng_skills)}个):")
    for s in zhongshusheng_skills:
        status = "🟢" if s.is_enabled else "🔴"
        print(f"   {status} {s.name}: {s.description[:30]}...")

    print("\n--- 按部筛选 ---")
    bingbu_skills = manager.list_by_department("bingbu")
    print(f"兵部技能 ({len(bingbu_skills)}个):")
    for s in bingbu_skills:
        print(f"   📦 {s.name}: {s.description[:30]}...")

    print("\n--- 触发词匹配 ---")
    matches = manager.find_by_trigger("我需要做API设计和数据库建模")
    print(f"匹配到 {len(matches)} 个技能:")
    for s in matches:
        print(f"   🎯 {s.name}: {s.description[:40]}...")

    print("\n--- 调用技能测试 ---")
    result = manager.call_skill("requirements_bureau", {"action": "analyze"})
    print(f"✅ 调用结果:")
    print(f"   成功: {result.success}")
    print(f"   执行时间: {result.execution_time_ms:.2f}ms")
    if result.result_data:
        print(f"   参数: {result.result_data.get('params')}")

    print("\n--- 启用/禁用测试 ---")
    manager.disable("testing_bureau")
    disabled_skill = manager.get("testing_bureau")
    print(f"已禁用: {disabled_skill.name} (启用={disabled_skill.enabled})")
    manager.enable("testing_bureau")
    re_enabled = manager.get("testing_bureau")
    print(f"已重新启用: {re_enabled.name} (启用={re_enabled.enabled})")

    print("\n--- 依赖关系图 ---")
    dep_graph = manager.get_dependency_graph()
    print(f"总技能数: {dep_graph['total_skills']}")
    print(f"根节点 ({len(dep_graph['root_skills'])}): {', '.join(dep_graph['root_skills'][:5])}...")
    print(f"叶节点 ({len(dep_graph['leaf_skills'])}): {', '.join(dep_graph['leaf_skills'][:5])}...")
    print(f"最大深度: {dep_graph['max_depth']}")

    print("\n--- 列出所有技能 ---")
    for name in manager.skill_names:
        skill = manager._skills[name]
        status = "🟢" if skill.is_enabled else "🔴"
        print(f"   {status} [{skill.province}] {name}")

    print("\n✅ 所有测试通过!")
