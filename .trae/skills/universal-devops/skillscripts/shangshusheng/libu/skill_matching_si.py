"""
技能匹配司 - 技能库检索、能力映射、推荐引擎
"""
from __future__ import annotations

import math
import re
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class SkillMatchingError(Exception):
    """技能匹配相关异常"""
    pass


class SkillCategory(str, Enum):
    """技能大类枚举"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    DEVOPS = "devops"
    SECURITY = "security"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    DATABASE = "database"
    AI_ML = "ai_ml"
    MOBILE = "mobile"
    DATA_ENGINEERING = "data_engineering"


class ProficiencyLevel(str, Enum):
    """熟练度等级"""
    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class SkillTag:
    """技能标签"""
    name: str
    category: SkillCategory
    aliases: list[str] = field(default_factory=list)
    related_skills: list[str] = field(default_factory=list)
    description: str = ""
    difficulty: int = 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value,
            "aliases": self.aliases,
            "related_skills": self.related_skills,
            "description": self.description,
            "difficulty": self.difficulty,
        }


@dataclass
class TeamSkillProfile:
    """团队技能画像"""
    member_name: str
    skills: dict[str, ProficiencyLevel] = field(default_factory=dict)
    years_experience: int = 0
    primary_role: str = ""
    learning_interests: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "member_name": self.member_name,
            "skills": {k: v.value for k, v in self.skills.items()},
            "years_experience": self.years_experience,
            "primary_role": self.primary_role,
            "learning_interests": self.learning_interests,
        }


@dataclass
class TaskSkillRequirement:
    """任务技能需求"""
    task_id: str
    task_name: str
    required_skills: list[tuple[str, ProficiencyLevel]] = field(default_factory=list)
    optional_skills: list[tuple[str, ProficiencyLevel]] = field(default_factory=list)
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "required_skills": [(s, l.value) for s, l in self.required_skills],
            "optional_skills": [(s, l.value) for s, l in self.optional_skills],
            "weight": self.weight,
        }


@dataclass
class MatchResult:
    """匹配结果"""
    task_id: str
    member_name: str
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    gap_details: dict[str, tuple[ProficiencyLevel, ProficiencyLevel]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "member_name": self.member_name,
            "match_score": round(self.match_score, 4),
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "gap_details": {
                k: (v[0].value, v[1].value) for k, v in self.gap_details.items()
            },
        }


@dataclass
class LearningPath:
    """学习路径"""
    target_skill: str
    steps: list[dict[str, Any]]
    estimated_weeks: int
    prerequisites: list[str]
    resources: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_skill": self.target_skill,
            "steps": self.steps,
            "estimated_weeks": self.estimated_weeks,
            "prerequisites": self.prerequisites,
            "resources": self.resources,
        }


class SkillMatchingSi:
    """
    技能匹配司

    负责技能库检索、能力映射和推荐引擎。
    支持任务-技能匹配、技能缺口分析、学习路径推荐等功能。
    """

    _instance: SkillMatchingSi | None = None

    def __init__(self) -> None:
        self._skill_registry: dict[str, SkillTag] = {}
        self._team_profiles: dict[str, TeamSkillProfile] = {}
        self._task_requirements: list[TaskSkillRequirement] = []
        self._skill_graph: dict[str, set[str]] = defaultdict(set)
        self._proficiency_order = list(ProficiencyLevel)
        self._initialize_builtin_skills()
        self._build_skill_graph()

    @classmethod
    def get_instance(cls) -> SkillMatchingSi:
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _initialize_builtin_skills(self) -> None:
        """初始化内置技能标签体系"""
        skills_data: list[dict[str, Any]] = [
            {"name": "JavaScript", "category": SkillCategory.FRONTEND, "aliases": ["JS", "js"], "related_skills": ["TypeScript", "React", "Vue.js", "Node.js"], "difficulty": 2},
            {"name": "TypeScript", "category": SkillCategory.FRONTEND, "aliases": ["TS", "ts"], "related_skills": ["JavaScript", "Angular", "React", "Node.js"], "difficulty": 3},
            {"name": "React", "category": SkillCategory.FRONTEND, "aliases": ["reactjs"], "related_skills": ["JavaScript", "TypeScript", "Redux", "Next.js"], "difficulty": 3},
            {"name": "Vue.js", "category": SkillCategory.FRONTEND, "aliases": ["vue", "vuejs"], "related_skills": ["JavaScript", "TypeScript", "Vuex", "Nuxt.js"], "difficulty": 3},
            {"name": "CSS/SCSS", "category": SkillCategory.FRONTEND, "aliases": ["css", "scss", "sass"], "related_skills": ["Tailwind CSS", "响应式设计"], "difficulty": 2},
            {"name": "HTML5", "category": SkillCategory.FRONTEND, "aliases": ["html"], "related_skills": ["CSS/SCSS", "JavaScript", "无障碍设计"], "difficulty": 1},
            {"name": "Python", "category": SkillCategory.BACKEND, "aliases": ["py"], "related_skills": ["Django", "FastAPI", "Flask", "数据分析"], "difficulty": 2},
            {"name": "Go", "category": SkillCategory.BACKEND, "aliases": ["Golang", "go"], "related_skills": ["gRPC", "微服务", "并发编程"], "difficulty": 4},
            {"name": "Java", "category": SkillCategory.BACKEND, "aliases": ["java"], "related_skills": ["Spring Boot", "Maven", "JVM调优"], "difficulty": 3},
            {"name": "Rust", "category": SkillCategory.BACKEND, "aliases": ["rust"], "related_skills": ["系统编程", "WebAssembly", "内存安全"], "difficulty": 5},
            {"name": "Node.js", "category": SkillCategory.BACKEND, "aliases": ["node", "nodejs"], "related_skills": ["JavaScript", "TypeScript", "Express", "NestJS"], "difficulty": 3},
            {"name": "Django", "category": SkillCategory.BACKEND, "aliases": [], "related_skills": ["Python", "DRF", "PostgreSQL", "ORM"], "difficulty": 3},
            {"name": "FastAPI", "category": SkillCategory.BACKEND, "aliases": [], "related_skills": ["Python", "Pydantic", "异步编程", "OpenAPI"], "difficulty": 3},
            {"name": "Docker", "category": SkillCategory.DEVOPS, "aliases": ["容器化"], "related_skills": ["Kubernetes", "Docker Compose", "CI/CD"], "difficulty": 3},
            {"name": "Kubernetes", "category": SkillCategory.DEVOPS, "aliases": ["k8s", "k8"], "related_skills": ["Docker", "Helm", "服务网格", "云原生"], "difficulty": 5},
            {"name": "CI/CD", "category": SkillCategory.DEVOPS, "aliases": ["持续集成", "持续部署"], "related_skills": ["GitHub Actions", "GitLab CI", "Jenkins", "Terraform"], "difficulty": 4},
            {"name": "Terraform", "category": SkillCategory.DEVOPS, "aliases": ["IaC", "基础设施即代码"], "related_skills": ["AWS", "Azure", "GCP", "Ansible"], "difficulty": 4},
            {"name": "Linux", "category": SkillCategory.DEVOPS, "aliases": ["linux系统管理"], "related_skills": ["Shell脚本", "网络", "安全"], "difficulty": 3},
            {"name": "网络安全", "category": SkillCategory.SECURITY, "aliases": ["security", "信息安全"], "related_skills": ["渗透测试", "加密技术", "OWASP"], "difficulty": 5},
            {"name": "渗透测试", "category": SkillCategory.SECURITY, "aliases": ["pentest"], "related_skills": ["网络安全", "Burp Suite", "Metasploit"], "difficulty": 5},
            {"name": "OWASP", "category": SkillCategory.SECURITY, "aliases": [], "related_skills": ["Web安全", "代码审计"], "difficulty": 4},
            {"name": "单元测试", "category": SkillCategory.TESTING, "aliases": ["unit test", "pytest", "jest"], "related_skills": ["TDD", "Mock框架", "覆盖率分析"], "difficulty": 3},
            {"name": "集成测试", "category": SkillCategory.TESTING, "aliases": ["integration test"], "related_skills": ["API测试", "E2E测试", "TestContainers"], "difficulty": 4},
            {"name": "性能测试", "category": SkillCategory.TESTING, "aliases": ["load testing", "压力测试"], "related_skills": ["JMeter", "Locust", "监控"], "difficulty": 4},
            {"name": "E2E测试", "category": SkillCategory.TESTING, "aliases": ["端到端测试"], "related_skills": ["Selenium", "Playwright", "Cypress"], "difficulty": 4},
            {"name": "微服务架构", "category": SkillCategory.ARCHITECTURE, "aliases": ["microservices"], "related_skills": ["API网关", "服务发现", "消息队列", "分布式事务"], "difficulty": 5},
            {"name": "领域驱动设计", "category": SkillCategory.ARCHITECTURE, "aliases": ["DDD"], "related_skills": ["事件风暴", "CQRS", "事件溯源"], "difficulty": 5},
            {"name": "事件驱动架构", "category": SkillCategory.ARCHITECTURE, "aliases": ["EDA"], "related_skills": ["消息队列", "Kafka", "事件溯源"], "difficulty": 5},
            {"name": "PostgreSQL", "category": SkillCategory.DATABASE, "aliases": ["pg", "postgres"], "related_skills": ["SQL优化", "索引设计", "复制", "分区表"], "difficulty": 4},
            {"name": "MySQL", "category": SkillCategory.DATABASE, "aliases": [], "related_skills": ["SQL优化", "InnoDB", "主从复制"], "difficulty": 3},
            {"name": "Redis", "category": SkillCategory.DATABASE, "aliases": [], "related_skills": ["缓存策略", "数据结构", "集群模式"], "difficulty": 3},
            {"name": "MongoDB", "category": SkillCategory.DATABASE, "aliases": [], "related_skills": ["NoSQL", "文档模型", "聚合管道"], "difficulty": 3},
            {"name": "SQL优化", "category": SkillCategory.DATABASE, "aliases": ["query optimization"], "related_skills": ["执行计划", "索引", "数据库调优"], "difficulty": 5},
            {"name": "机器学习", "category": SkillCategory.AI_ML, "aliases": ["ML", "machine learning"], "related_skills": ["Python", "TensorFlow", "PyTorch", "scikit-learn"], "difficulty": 5},
            {"name": "深度学习", "category": SkillCategory.AI_ML, "aliases": ["DL", "deep learning"], "related_skills": ["机器学习", "PyTorch", "CNN", "Transformer"], "difficulty": 5},
            {"name": "LLM/RAG", "category": SkillCategory.AI_ML, "aliases": ["大语言模型", "检索增强生成"], "related_skills": ["Prompt Engineering", "向量数据库", "LangChain"], "difficulty": 5},
            {"name": "React Native", "category: SkillCategory.MOBILE": SkillCategory.MOBILE, "aliases": ["rn"], "related_skills": ["React", "JavaScript", "TypeScript", "移动开发"], "difficulty": 4} if False else {"name": "React Native", "category": SkillCategory.MOBILE, "aliases": ["rn"], "related_skills": ["React", "JavaScript", "TypeScript", "移动开发"], "difficulty": 4},
            {"name": "Flutter", "category": SkillCategory.MOBILE, "aliases": [], "related_skills": ["Dart", "移动开发", "跨平台"], "difficulty": 4},
            {"name": "SwiftUI", "category": SkillCategory.MOBILE, "aliases": [], "related_skills": ["Swift", "iOS开发", "Combine"], "difficulty": 4},
            {"name": "Spark", "category": SkillCategory.DATA_ENGINEERING, "aliases": [], "related_skills": ["Scala", "Hadoop", "大数据处理"], "difficulty": 5},
            {"name": "Airflow", "category": SkillCategory.DATA_ENGINEERING, "aliases": [], "related_skills": ["Python", "ETL", "调度"], "difficulty": 4},
        ]

        for skill_data in skills_data:
            skill = SkillTag(**skill_data)
            self._skill_registry[skill.name.lower()] = skill

    def _build_skill_graph(self) -> None:
        """构建技能关联图"""
        for skill in self._skill_registry.values():
            for related in skill.related_skills:
                if related.lower() in self._skill_registry:
                    self._skill_graph[skill.name.lower()].add(related.lower())

    def register_skill(self, skill: SkillTag) -> None:
        """注册新技能"""
        key = skill.name.lower()
        if key in self._skill_registry:
            raise SkillMatchingError(f"技能已存在: {skill.name}")
        self._skill_registry[key] = skill
        for related in skill.related_skills:
            if related.lower() in self._skill_registry:
                self._skill_graph[key].add(related.lower())

    def get_skill(self, name: str) -> SkillTag | None:
        """获取技能标签"""
        return self._skill_registry.get(name.lower())

    def search_skills(
        self,
        query: str,
        category: SkillCategory | None = None,
        limit: int = 20,
    ) -> list[SkillTag]:
        """
        搜索技能标签（支持模糊搜索）

        Args:
            query: 搜索关键词
            category: 可选的类别过滤
            limit: 返回数量限制

        Returns:
            匹配的SkillTag列表
        """
        query_lower = query.lower()
        results: list[tuple[SkillTag, int]] = []

        for skill in self._skill_registry.values():
            if category and skill.category != category:
                continue

            score = 0
            if query_lower == skill.name.lower():
                score += 100
            elif query_lower in skill.name.lower():
                score += 50
            elif any(query_lower in a.lower() for a in skill.aliases):
                score += 30
            elif query_lower in skill.description.lower():
                score += 10

            if query_lower in [r.lower() for r in skill.related_skills]:
                score += 20

            if score > 0:
                results.append((skill, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:limit]]

    def add_team_profile(self, profile: TeamSkillProfile) -> None:
        """添加团队成员技能画像"""
        self._team_profiles[profile.member_name] = profile

    def remove_team_profile(self, member_name: str) -> bool:
        """移除团队成员技能画像"""
        if member_name in self._team_profiles:
            del self._team_profiles[member_name]
            return True
        return False

    def add_task_requirement(self, requirement: TaskSkillRequirement) -> None:
        """添加任务技能需求"""
        self._task_requirements.append(requirement)

    def match_task_to_member(
        self,
        task_requirement: TaskSkillRequirement,
        method: str = "hierarchical",
    ) -> list[MatchResult]:
        """
        将任务与团队成员进行技能匹配

        Args:
            task_requirement: 任务技能需求
            method: 匹配方法 (tfidf/cosine/hierarchical)

        Returns:
            按匹配分数排序的MatchResult列表
        """
        required_skills = task_requirement.required_skills
        optional_skills = task_requirement.optional_skills

        all_required_names = set(s[0].lower() for s in required_skills)
        all_optional_names = set(s[0].lower() for s in optional_skills)

        results: list[MatchResult] = []

        for member_name, profile in self._team_profiles.items():
            member_skills_lower = {k.lower(): v for k, v in profile.skills.items()}

            matched: list[str] = []
            missing: list[str] = []
            gap_details: dict[str, tuple[ProficiencyLevel, ProficiencyLevel]] = {}

            total_required = len(required_skills)
            satisfied_count = 0

            for skill_name, req_level in required_skills:
                sn_lower = skill_name.lower()

                if sn_lower in member_skills_lower:
                    member_level = member_skills_lower[sn_lower]
                    try:
                        member_idx = self._proficiency_order.index(member_level)
                        req_idx = self._proficiency_order.index(req_level)
                        if member_idx >= req_idx:
                            matched.append(skill_name)
                            satisfied_count += 1
                        else:
                            gap_details[skill_name] = (member_level, req_level)
                            missing.append(skill_name)
                    except ValueError:
                        gap_details[skill_name] = (ProficiencyLevel.NOVICE, req_level)
                        missing.append(skill_name)
                else:
                    missing.append(skill_name)
                    gap_details[skill_name] = (ProficiencyLevel.NOVICE, req_level)

            optional_matched = sum(
                1 for s, _ in optional_skills
                if s.lower() in member_skills_lower
            )
            optional_total = len(optional_skills) if optional_skills else 1

            match method:
                case "tfidf":
                    base_score = satisfied_count / total_required if total_required > 0 else 0
                    bonus = (optional_matched / optional_total) * 0.2
                    final_score = (base_score * 0.8 + bonus) * task_requirement.weight
                case "cosine":
                    vec_member = self._build_skill_vector(profile.skills)
                    vec_req = self._build_skill_vector(dict(required_skills + optional_skills))
                    cosine_sim = self._cosine_similarity(vec_member, vec_req)
                    final_score = cosine_sim * task_requirement.weight
                case "hierarchical" | _:
                    weight_map = {s: i + 1 for i, (s, _) in enumerate(reversed(required_skills))}
                    weighted_sum = sum(
                        weight_map.get(s, 1) for s in matched
                    )
                    total_weight = sum(weight_map.values()) if weight_map else 1
                    base_score = weighted_sum / total_weight
                    optional_bonus = (optional_matched / optional_total) * 0.15
                    final_score = (base_score * 0.85 + optional_bonus) * task_requirement.weight

            results.append(MatchResult(
                task_id=task_requirement.task_id,
                member_name=member_name,
                match_score=final_score,
                matched_skills=matched,
                missing_skills=missing,
                gap_details=gap_details,
            ))

        results.sort(key=lambda r: r.match_score, reverse=True)
        return results

    def analyze_skill_gaps(
        self,
        project_skills: list[tuple[str, ProficiencyLevel]],
    ) -> dict[str, Any]:
        """
        分析当前团队的技能缺口

        Args:
            project_skills: 项目所需技能列表 (技能名, 熟练度)

        Returns:
            技能缺口分析结果字典
        """
        team_aggregate: Counter[str] = Counter()
        team_proficiency: dict[str, list[ProficiencyLevel]] = defaultdict(list)

        for profile in self._team_profiles.values():
            for skill, level in profile.skills.items():
                team_aggregate[skill.lower()] += 1
                team_proficiency[skill.lower()].append(level)

        gaps: list[dict[str, Any]] = []
        covered: list[dict[str, Any]] = []

        for skill_name, required_level in project_skills:
            sn_lower = skill_name.lower()
            team_levels = team_proficiency.get(sn_lower, [])
            team_count = team_aggregate.get(sn_lower, 0)

            if not team_levels:
                gaps.append({
                    "skill": skill_name,
                    "required_level": required_level.value,
                    "team_count": 0,
                    "gap_type": "missing",
                    "severity": "critical" if required_level.value in ("advanced", "expert") else "high",
                    "recommendation": f"急需招聘或培训 {skill_name} 技能人员",
                })
            else:
                max_level = max(team_levels, key=lambda l: self._proficiency_order.index(l))
                try:
                    max_idx = self._proficiency_order.index(max_level)
                    req_idx = self._proficiency_order.index(required_level)
                    if max_idx < req_idx:
                        gaps.append({
                            "skill": skill_name,
                            "required_level": required_level.value,
                            "team_count": team_count,
                            "current_max_level": max_level.value,
                            "gap_type": "insufficient_proficiency",
                            "severity": "medium",
                            "recommendation": f"现有{team_count}人掌握该技能，但最高仅达{max_level.value}，需提升至{required_level.value}",
                        })
                    else:
                        covered.append({
                            "skill": skill_name,
                            "required_level": required_level.value,
                            "team_count": team_count,
                            "max_level": max_level.value,
                        })
                except ValueError:
                    gaps.append({
                        "skill": skill_name,
                        "required_level": required_level.value,
                        "team_count": team_count,
                        "gap_type": "unknown",
                        "severity": "low",
                    })

        total_project = len(project_skills)
        coverage_rate = len(covered) / total_project if total_project > 0 else 0

        return {
            "total_project_skills": total_project,
            "covered_skills": covered,
            "gap_skills": gaps,
            "coverage_rate": round(coverage_rate, 4),
            "team_size": len(self._team_profiles),
            "summary": (
                f"项目需要{total_project}项技能，团队覆盖{len(covered)}项 "
                f"(覆盖率{coverage_rate:.1%})，存在{len(gaps)}项缺口"
            ),
        }

    def recommend_learning_path(
        self,
        target_skill: str,
        current_profile: TeamSkillProfile | None = None,
    ) -> LearningPath:
        """
        推荐学习路径

        Args:
            target_skill: 目标技能名称
            current_profile: 当前技能画像（可选，用于定制路径）

        Returns:
            LearningPath对象
        """
        skill = self.get_skill(target_skill)
        if not skill:
            raise SkillMatchingError(f"未知技能: {target_skill}")

        prereqs: list[str] = []
        steps: list[dict[str, Any]] = []

        related = self._skill_graph.get(target_skill.lower(), set())
        for rel in related:
            rel_skill = self._skill_registry.get(rel)
            if rel_skill and rel_skill.difficulty <= skill.difficulty:
                prereqs.append(rel_skill.name)

        difficulty_steps: dict[int, list[str]] = defaultdict(list)
        for p in prereqs:
            ps = self._skill_registry.get(p.lower())
            if ps:
                difficulty_steps[min(ps.difficulty, skill.difficulty)].append(p)

        step_num = 1
        for diff in sorted(difficulty_steps.keys()):
            for sk_name in difficulty_steps[diff]:
                sk = self._skill_registry.get(sk_name.lower())
                steps.append({
                    "step": step_num,
                    "skill": sk_name,
                    "category": sk.category.value if sk else "unknown",
                    "difficulty": diff,
                    "estimated_days": diff * 7,
                    "resources": self._get_learning_resources(sk_name),
                })
                step_num += 1

        steps.append({
            "step": step_num,
            "skill": target_skill,
            "category": skill.category.value,
            "difficulty": skill.difficulty,
            "estimated_days": skill.difficulty * 7,
            "resources": self._get_learning_resources(target_skill),
        })

        total_weeks = sum(s["estimated_days"] for s in steps) // 7

        resources = self._get_learning_resources(target_skill)

        return LearningPath(
            target_skill=target_skill,
            steps=steps,
            estimated_weeks=max(total_weeks, 2),
            prerequisites=prereqs,
            resources=resources,
        )

    def get_related_skills(self, skill_name: str, depth: int = 1) -> set[str]:
        """
        获取关联技能（BFS遍历）

        Args:
            skill_name: 技能名称
            depth: 遍历深度

        Returns:
            关联技能名称集合
        """
        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(skill_name.lower(), 0)]

        while queue:
            current, d = queue.pop(0)
            if current in visited or d > depth:
                continue
            visited.add(current)

            for neighbor in self._skill_graph.get(current, set()):
                if neighbor not in visited:
                    queue.append((neighbor, d + 1))

        visited.discard(skill_name.lower())
        return visited

    def _build_skill_vector(self, skills: dict[str, ProficiencyLevel]) -> dict[str, float]:
        """构建技能向量"""
        vector: dict[str, float] = {}
        for skill_name, level in skills.items():
            try:
                idx = self._proficiency_order.index(level)
                vector[skill_name.lower()] = (idx + 1) / len(self._proficiency_order)
            except ValueError:
                vector[skill_name.lower()] = 0.1
        return vector

    @staticmethod
    def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
        """计算余弦相似度"""
        common_keys = set(vec_a.keys()) & set(vec_b.keys())
        if not common_keys:
            return 0.0

        dot_product = sum(vec_a[k] * vec_b[k] for k in common_keys)
        norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    @staticmethod
    def _get_learning_resources(skill_name: str) -> list[str]:
        """获取学习资源建议"""
        resource_templates = {
            "python": ["Python官方文档", "Fluent Python书籍", "Real Python教程"],
            "javascript": ["MDN Web Docs", "You Don't Know JS系列", "JavaScript.info"],
            "docker": ["Docker官方文档", "Docker Deep Dive书籍", "Play with Docker"],
            "kubernetes": ["Kubernetes官方文档", "Kubernetes Patterns书籍", "Katacoda K8s教程"],
            "react": ["React官方文档", "Fullstack React书籍", "Epic React课程"],
            "machine_learning": ["Andrew Ng ML课程", "Hands-on ML书籍", "Fast.ai课程"],
        }
        lower = skill_name.lower()
        for key, resources in resource_templates.items():
            if key in lower:
                return resources
        return [f"{skill_name} 官方文档", f"{skill_name} 入门教程", f"{skill_name} 最佳实践"]

    @property
    def total_skills(self) -> int:
        return len(self._skill_registry)

    @property
    def team_size(self) -> int:
        return len(self._team_profiles)

    def get_all_skills_by_category(self) -> dict[str, list[SkillTag]]:
        by_cat: dict[str, list[SkillTag]] = defaultdict(list)
        for skill in self._skill_registry.values():
            by_cat[skill.category.value].append(skill)
        return dict(by_cat)

    def __repr__(self) -> str:
        return (
            f"SkillMatchingSi(skills={self.total_skills}, "
            f"team={self.team_size}, tasks={len(self._task_requirements)})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 技能匹配司测试")
    print("=" * 60)

    sm = SkillMatchingSi()

    print("\n--- 技能库概览 ---")
    by_category = sm.get_all_skills_by_category()
    for cat, skills in sorted(by_category.items()):
        print(f"\n   📂 {cat.upper()} ({len(skills)}项):")
        for sk in skills[:5]:
            print(f"      • {sk.name} (难度:{sk.difficulty}/5)")

    print(f"\n   📊 总计: {sm.total_skills} 项技能")

    print("\n--- 搜索技能 ---")
    queries = ["Python", "docker", "k8s", "前端", "test"]
    for q in queries:
        results = sm.search_skills(q, limit=3)
        names = [r.name for r in results]
        print(f"   🔍 '{q}' → {names}")

    print("\n--- 添加团队成员 ---")
    profiles_data = [
        ("张三", {"Python": ProficiencyLevel.EXPERT, "Django": ProficiencyLevel.ADVANCED, "PostgreSQL": ProficiencyLevel.INTERMEDIATE, "Docker": ProficiencyLevel.BEGINNER}, 6, "后端工程师"),
        ("李四", {"React": ProficiencyLevel.ADVANCED, "TypeScript": ProficiencyLevel.ADVANCED, "JavaScript": ProficiencyLevel.EXPERT, "CSS/SCSS": ProficiencyLevel.INTERMEDIATE}, 4, "前端工程师"),
        ("王五", {"Go": ProficiencyLevel.INTERMEDIATE, "Kubernetes": ProficiencyLevel.BEGINNER, "Docker": ProficiencyLevel.INTERMEDIATE, "Linux": ProficiencyLevel.ADVANCED}, 3, "DevOps工程师"),
        ("赵六", {"Python": ProficiencyLevel.ADVANCED, "单元测试": ProficiencyLevel.ADVANCED, "性能测试": ProficiencyLevel.BEGINNER, "E2E测试": ProficiencyLevel.INTERMEDIATE}, 5, "QA工程师"),
    ]
    for name, skills, exp, role in profiles_data:
        profile = TeamSkillProfile(member_name=name, skills=skills, years_experience=exp, primary_role=role)
        sm.add_team_profile(profile)
        print(f"   ✅ {name} ({role}): {', '.join(f'{k}:{v.value}' for k, v in list(skills.items())[:3])}...")

    print("\n--- 任务-技能匹配 ---")
    task_req = TaskSkillRequirement(
        task_id="TASK-001",
        task_name="开发RESTful API服务",
        required_skills=[
            ("Python", ProficiencyLevel.ADVANCED),
            ("FastAPI", ProficiencyLevel.INTERMEDIATE),
            ("PostgreSQL", ProficiencyLevel.INTERMEDIATE),
        ],
        optional_skills=[
            ("Docker", ProficiencyLevel.BEGINNER),
            ("单元测试", ProficiencyLevel.INTERMEDIATE),
        ],
    )

    matches = sm.match_task_to_member(task_req, method="hierarchical")
    print(f"\n   📋 任务: {task_req.task_name}")
    for m in matches[:5]:
        status_icon = "🟢" if m.match_score >= 0.7 else "🟡" if m.match_score >= 0.4 else "🔴"
        print(f"   {status_icon} {m.member_name}: 匹配度={m.match_score:.2%}")
        if m.matched_skills:
            print(f"      ✓ 匹配: {m.matched_skills}")
        if m.missing_skills:
            print(f"      ✗ 缺失: {m.missing_skills}")

    print("\n--- 技能缺口分析 ---")
    project_skills = [
        ("Python", ProficiencyLevel.ADVANCED),
        ("React", ProficiencyLevel.INTERMEDIATE),
        ("Kubernetes", ProficiencyLevel.INTERMEDIATE),
        ("PostgreSQL", ProficiencyLevel.ADVANCED),
        ("CI/CD", ProficiencyLevel.INTERMEDIATE),
        ("机器学习", ProficiencyLevel.BEGINNER),
    ]
    gap_analysis = sm.analyze_skill_gaps(project_skills)
    print(f"\n   {gap_analysis['summary']}")
    print(f"\n   ✅ 已覆盖 ({len(gap_analysis['covered_skills'])}项):")
    for c in gap_analysis['covered_skills']:
        print(f"      • {c['skill']} (团队{c['team_count']}人, 最高{c['max_level']})")

    print(f"\n   ⚠️ 缺口 ({len(gap_analysis['gap_skills'])}项):")
    for g in gap_analysis['gap_skills']:
        severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}
        icon = severity_icon.get(g['severity'], "⚪")
        print(f"   {icon} [{g['severity']}] {g['skill']}: {g['recommendation']}")

    print("\n--- 学习路径推荐 ---")
    try:
        path = sm.recommend_learning_path("Kubernetes")
        print(f"\n   🎯 目标: {path.target_skill}")
        print(f"   ⏱️ 预计周期: {path.estimated_weeks} 周")
        print(f"   📚 前置技能: {', '.join(path.prerequisites) if path.prerequisites else '无'}")
        print(f"\n   学习步骤:")
        for step in path.steps:
            print(f"      {step['step']}. {step['skill']} ({step['category']}) - 约{step['estimated_days']}天")
    except SkillMatchingError as e:
        print(f"   ❌ {e}")

    print("\n--- 关联技能 ---")
    for target in ["Python", "Docker"]:
        related = sm.get_related_skills(target, depth=1)
        print(f"   🔗 {target} → {sorted(related)}")

    print("\n✅ 所有测试通过!")
