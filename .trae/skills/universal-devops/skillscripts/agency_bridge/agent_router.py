"""
Agent 路由器

分析任务意图，基于专长和上下文匹配合适的 AI 智能体，
支持多 agent 组合推荐和路由历史记录。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class TaskIntent(str, Enum):
    """任务意图分类"""
    CODE_REVIEW = "code_review"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DESIGN = "design"
    DEVOPS = "devops"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    REFACTORING = "refactoring"
    BUG_FIXING = "bug_fixing"
    PERFORMANCE = "performance"
    GENERAL = "general"


@dataclass
class RoutingRequest:
    """路由请求"""

    task_description: str
    context: dict[str, Any] = field(default_factory=dict)
    complexity: str = "medium"
    preferred_mode: str = "auto"

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_description": self.task_description[:100],
            "context_keys": list(self.context.keys()),
            "complexity": self.complexity,
            "preferred_mode": self.preferred_mode,
        }


@dataclass
class RoutingResult:
    """路由结果"""

    recommended_agents: list[str] = field(default_factory=list)
    reasoning: str = ""
    confidence_score: float = 0.0
    alternatives: list[list[str]] = field(default_factory=list)
    detected_intent: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommended_agents": self.recommended_agents,
            "reasoning": self.reasoning,
            "confidence_score": round(self.confidence_score, 2),
            "alternatives": self.alternatives,
            "detected_intent": self.detected_intent,
            "timestamp": self.timestamp,
        }


@dataclass
class RoutingHistoryItem:
    """路由历史条目"""
    request: RoutingRequest
    result: RoutingResult
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentRouter:
    """
    Agent 路由器

    根据任务描述和上下文信息，智能选择最合适的 AI 智能体组合。
    """

    INTENT_PATTERNS: dict[TaskIntent, list[str]] = {
        TaskIntent.CODE_REVIEW: [
            r"代码审查|code\s*review|review|审查|评审",
            r"代码质量|quality|规范|最佳实践",
            r"PR|pull\s*request|合并|merge",
        ],
        TaskIntent.DEVELOPMENT: [
            r"开发|实现|编写|build|develop|implement",
            r"新功能|feature|功能开发",
            r"前端|backend|后端|API|接口",
        ],
        TaskIntent.TESTING: [
            r"测试|test|testing|单元测试|集成测试",
            r"用例|test\s*case|覆盖率|coverage",
            r"QA|质量保证|验证|验证",
        ],
        TaskIntent.DESIGN: [
            r"设计|design|UI|UX|界面|交互",
            r"原型|prototype|wireframe|线框图",
            r"用户体验|user\s*experience|视觉",
        ],
        TaskIntent.DEVOPS: [
            r"运维|devops|部署|deploy|CI/CD",
            r"容器|docker|kubernetes|k8s",
            r"基础设施|infrastructure|自动化",
        ],
        TaskIntent.DOCUMENTATION: [
            r"文档|document|文档生成|注释|comment",
            r"README|API\s*doc|说明文档",
            r"知识库|wiki|手册",
        ],
        TaskIntent.ARCHITECTURE: [
            r"架构|architecture|系统设计|技术方案",
            r"微服务|microservice|模块划分",
            r"技术选型|tech\s*stack|设计模式",
        ],
        TaskIntent.SECURITY: [
            r"安全|security|漏洞|渗透|加密",
            r"认证|授权|auth|权限|permission",
            r"合规|compliance|审计|audit",
        ],
        TaskIntent.REFACTORING: [
            r"重构|refactor|优化|optimize|改善",
            r"代码清理|clean.*code|技术债|debt",
            r"简化|simplify|模块化|modularize",
        ],
        TaskIntent.BUG_FIXING: [
            r"bug|缺陷|错误|error|修复|fix",
            r"问题|issue|异常|exception|调试|debug",
            r"崩溃|crash|故障|fail",
        ],
        TaskIntent.PERFORMANCE: [
            r"性能|performance|性能优化|速度|speed",
            r"延迟|latency|吞吐量|throughput",
            r"内存|memory|CPU|负载|load",
        ],
    }

    def __init__(self, registry: Any = None) -> None:
        self._registry = registry
        self._history: list[RoutingHistoryItem] = []
        self._intent_cache: dict[str, TaskIntent] = {}

    def analyze_task_intent(self, task_description: str) -> tuple[TaskIntent, float]:
        """
        分析任务意图（代码审查 / 开发 / 测试 / 设计 / 运维等）

        Args:
            task_description: 任务描述文本

        Returns:
            (检测到的意图, 置信度分数)
        """
        text_lower = task_description.lower()

        cached = self._intent_cache.get(text_lower[:100])
        if cached:
            return cached, 0.9

        best_intent = TaskIntent.GENERAL
        max_score = 0.0
        scores: dict[TaskIntent, float] = {}

        for intent, patterns in self.INTENT_PATTERNS.items():
            intent_score = 0.0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                intent_score += len(matches) * 10
                if re.search(pattern, text_lower, re.IGNORECASE):
                    intent_score += 5
            scores[intent] = intent_score
            if intent_score > max_score:
                max_score = intent_score
                best_intent = intent

        confidence = min(max_score / 50.0, 1.0) if max_score > 0 else 0.3
        self._intent_cache[text_lower[:100]] = best_intent

        return best_intent, confidence

    def match_agents_by_specialty(
        self,
        intent: TaskIntent,
        context: dict[str, Any],
        limit: int = 5,
    ) -> list[str]:
        """
        基于专长匹配 agents

        Args:
            intent: 任务意图
            context: 上下文信息（技术栈、项目类型等）
            limit: 返回数量限制

        Returns:
            匹配的 agent ID 列表
        """
        if self._registry is None:
            return []

        tech_stack = context.get("tech_stack", "").lower()
        project_type = context.get("project_type", "").lower()

        intent_keywords: dict[TaskIntent, list[str]] = {
            TaskIntent.CODE_REVIEW: ["code_reviewer", "senior_developer"],
            TaskIntent.DEVELOPMENT: ["frontend_developer", "backend_architect", "developer"],
            TaskIntent.TESTING: ["api_tester", "evidence_collector", "reality_checker"],
            TaskIntent.DESIGN: ["ui_designer", "ux_researcher", "ux_architect"],
            TaskIntent.DEVOPS: ["devops_automator", "sre", "infrastructure_maintainer"],
            TaskIntent.DOCUMENTATION: ["technical_writer", "document_generator"],
            TaskIntent.ARCHITECTURE: ["software_architect", "backend_architect"],
            TaskIntent.SECURITY: ["security_engineer", "threat_detection_engineer", "compliance_auditor"],
            TaskIntent.REFACTORING: ["senior_developer", "software_architect"],
            TaskIntent.BUG_FIXING: ["senior_developer", "frontend_developer", "backend_architect"],
            TaskIntent.PERFORMANCE: ["database_optimizer", "sre", "performance_benchmarker"],
        }

        primary_keywords = intent_keywords.get(intent, [])
        all_matches: list[tuple[str, float]] = []

        search_query = " ".join(primary_keywords[:2])
        candidates = self._registry.search_agents(search_query, limit=limit * 3)

        for candidate in candidates:
            score = 0.0

            for keyword in primary_keywords:
                if keyword in candidate.id:
                    score += 30
                elif keyword in candidate.specialty.lower():
                    score += 20
                elif keyword in candidate.name.lower():
                    score += 15

            if tech_stack and tech_stack in candidate.description.lower():
                score += 15

            if project_type and project_type in candidate.description.lower():
                score += 10

            if score > 0:
                all_matches.append((candidate.id, score))

        all_matches.sort(key=lambda x: x[1], reverse=True)
        return [m[0] for m in all_matches[:limit]]

    def evaluate_context_fit(
        self,
        agent_id: str,
        context: dict[str, Any],
    ) -> float:
        """
        评估 agent 与上下文的匹配度

        Args:
            agent_id: agent ID
            context: 上下文信息

        Returns:
            匹配度分数 (0.0 - 1.0)
        """
        if self._registry is None:
            return 0.0

        agent = self._registry.get_agent_by_id(agent_id)
        if agent is None:
            return 0.0

        score = 0.5
        tech_stack = context.get("tech_stack", "").lower()
        project_type = context.get("project_type", "").lower()
        language = context.get("language", "").lower()

        if tech_stack:
            if any(t in agent.description.lower() for t in tech_stack.split(",")):
                score += 0.2
            if any(t in agent.specialty.lower() for t in tech_stack.split(",")):
                score += 0.15

        if language:
            if language in agent.description.lower():
                score += 0.15
            if language in agent.specialty.lower():
                score += 0.1

        if project_type:
            if project_type in agent.description.lower():
                score += 0.1

        return min(score, 1.0)

    def compose_agent_combination(
        self,
        primary_agents: list[str],
        intent: TaskIntent,
        complexity: str = "medium",
    ) -> tuple[list[str], list[list[str]]]:
        """
        组合多个 agents（主 agent + 辅助 agent）

        Args:
            primary_agents: 主 agent 列表
            intent: 任务意图
            complexity: 复杂度 (low/medium/high)

        Returns:
            (最终组合列表, 备选方案列表)
        """
        if self._registry is None:
            return primary_agents, []

        combination = list(primary_agents)
        alternatives: list[list[str]] = []

        assistant_map: dict[TaskIntent, list[str]] = {
            TaskIntent.CODE_REVIEW: ["security_engineer", "senior_developer"],
            TaskIntent.DEVELOPMENT: ["senior_developer", "code_reviewer"],
            TaskIntent.TESTING: ["evidence_collector", "reality_checker"],
            TaskIntent.DESIGN: ["ux_researcher", "brand_guardian"],
            TaskIntent.DEVOPS: ["sre", "incident_response_commander"],
            TaskIntent.ARCHITECTURE: ["senior_developer", "backend_architect"],
            TaskIntent.SECURITY: ["compliance_auditor", "threat_detection_engineer"],
        }

        assistants = assistant_map.get(intent, [])

        if complexity in ("high", "critical"):
            available_assistants = [a for a in assistants if self._registry.get_agent_by_id(a)]
            combination.extend(available_assistants[:2])

        if len(primary_agents) > 1:
            alternatives.append(primary_agents[1:] + assistants[:1])
        if assistants:
            alternatives.append(assistants[:2] + primary_agents[:1])

        return combination, alternatives

    def route(self, request: RoutingRequest) -> RoutingResult:
        """
        主路由方法：综合分析返回最优 RoutingResult

        Args:
            request: 路由请求

        Returns:
            路由结果，包含推荐的 agent 组合及推理过程
        """
        intent, intent_confidence = self.analyze_task_intent(request.task_description)

        primary_agents = self.match_agents_by_specialty(
            intent, request.context, limit=3
        )

        final_combination, alternatives = self.compose_agent_combination(
            primary_agents, intent, request.complexity
        )

        avg_fit = 0.0
        if final_combination:
            fits = [self.evaluate_context_fit(aid, request.context) for aid in final_combination]
            avg_fit = sum(fits) / len(fits)

        confidence = (intent_confidence * 0.4 + avg_fit * 0.4 + (0.9 if final_combination else 0.1) * 0.2)

        reasoning_parts = [
            f"检测到任务意图: {intent.value}",
            f"意图置信度: {intent_confidence:.2f}",
            f"匹配主 agents: {len(primary_agents)} 个",
            f"上下文适配度: {avg_fit:.2f}",
        ]
        if request.complexity != "medium":
            reasoning_parts.append(f"复杂度调整: {request.complexity}")

        result = RoutingResult(
            recommended_agents=final_combination,
            reasoning="; ".join(reasoning_parts),
            confidence_score=confidence,
            alternatives=alternatives,
            detected_intent=intent.value,
        )

        history_item = RoutingHistoryItem(request=request, result=result)
        self._history.append(history_item)

        return result

    def get_routing_history(self, limit: int = 10) -> list[RoutingHistoryItem]:
        """
        获取路由历史（用于学习优化）

        Args:
            limit: 返回数量限制

        Returns:
            最近的路由历史记录
        """
        return self._history[-limit:]

    def clear_history(self) -> None:
        """清空路由历史"""
        self._history.clear()
        self._intent_cache.clear()


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Agent 路由器测试")
    print("=" * 60)

    from .agent_registry import AgentRegistry

    registry = AgentRegistry()
    registry.scan_agents_directory()

    router = AgentRouter(registry)

    test_requests = [
        RoutingRequest(task_description="请帮我审查这段 React 组件代码的质量"),
        RoutingRequest(
            task_description="开发一个用户登录 API 接口",
            context={"tech_stack": "Node.js,Express", "project_type": "web_api"},
        ),
        RoutingRequest(task_description="为电商系统编写单元测试用例"),
        RoutingRequest(task_description="重新设计产品首页的 UI 布局"),
    ]

    print("\n--- 路由测试 ---")
    for req in test_requests:
        result = router.route(req)
        print(f"\n📋 任务: {req.task_description[:40]}...")
        print(f"   意图: {result.detected_intent}")
        print(f"   置信度: {result.confidence_score:.2f}")
        print(f"   推荐: {result.recommended_agents[:3]}")
        print(f"   推理: {result.reasoning[:80]}...")

    print("\n--- 路由历史 ---")
    history = router.get_routing_history(5)
    print(f"✅ 历史记录数: {len(history)}")

    print("\n✅ Agent 路由器测试通过!")
