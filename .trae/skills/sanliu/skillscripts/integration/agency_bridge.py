#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agency Agents 桥接层 - AgencyBridge

功能概述：
1. Agent注册表扫描：遍历 agency-agents 目录，解析 YAML frontmatter
2. 智能路由器 SmartRouter：基于任务描述推荐最佳 Agent 组合
3. 调用接口：同步/并行调用 Agent，支持 MARC 资源协调器集成
4. 结果整合器 ResultAggregator：收集输出、冲突检测、生成综合报告
5. Sanliu → Agency Agent 映射矩阵：≥20 个六部制到现代 Agent 的映射

依赖：纯 Python 标准库，无外部依赖
可选集成：resource_coordinator.py 的 ResourceCoordinator
"""

import os
import re
import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum, auto

logger = logging.getLogger(__name__)


# ============================================================
# 常量定义
# ============================================================

AGENT_REGISTRY_PATH = ".trae/skills/agency-agents"

SUPPORTED_DOMAINS = [
    "engineering", "design", "testing", "marketing", "product",
    "sales", "strategy", "support", "specialized", "academic",
    "game-development", "spatial-computing", "paid-media",
    "project-management"
]


# ============================================================
# 数据类定义
# ============================================================


@dataclass
class AgentInfo:
    """Agent 基本信息，从 .md 文件的 YAML frontmatter 解析得到"""
    agent_id: str
    name: str
    description: str
    domain: str
    role: str = ""
    capabilities: List[str] = field(default_factory=list)
    emoji: str = ""
    color: str = ""
    vibe: str = ""
    file_path: str = ""


@dataclass
class AgentSpec:
    """Agent 完整规格，包含基本信息 + 完整内容"""
    info: AgentInfo
    full_content: str = ""
    raw_frontmatter: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentRecommendation:
    """智能路由器推荐的 Agent 条目"""
    agent_id: str
    name: str
    confidence: float  # 0.0 ~ 1.0 置信度分数
    reason: str  # 推荐理由
    domain: str = ""


@dataclass
class AgentResult:
    """单次 Agent 调用的结果"""
    agent_id: str
    task: str
    success: bool
    output: str = ""
    error: str = ""
    duration_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConflictItem:
    """结果整合器检测到的冲突项"""
    file_path: str
    conflict_type: str  # "modification_conflict" | "suggestion_conflict" | "severity_mismatch"
    agents_involved: List[str]
    description: str
    severity: str  # "critical" | "major" | "minor"


@dataclass
class AggregatedReport:
    """多 Agent 结果整合后的综合报告"""
    task_description: str
    total_agents: int
    successful_agents: int
    failed_agents: int
    results: List[AgentResult]
    findings: List[Dict[str, Any]]  # 按严重级别排序的发现列表
    conflicts: List[ConflictItem]
    summary: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SanliuMappingEntry:
    """Sanliu 六部制部门 → Agency Agents 映射条目"""
    sanliu_department: str
    sanliu_bureau: str
    target_agent_ids: List[str]
    description: str = ""


# ============================================================
# Sanliu → Agency Agent 映射矩阵（≥20个映射）
# ============================================================

SANLIU_AGENCY_MAPPING: List[Dict[str, Any]] = [
    {
        "sanliu_department": "中书省",
        "sanliu_bureau": "需求分析局",
        "target_agent_ids": ["product-manager", "product-trend-researcher"],
        "description": "产品需求收集与分析、市场趋势研究"
    },
    {
        "sanliu_department": "中书省",
        "sanliu_bureau": "架构设计局",
        "target_agent_ids": [
            "engineering-software-architect",
            "engineering-backend-architect",
            "engineering-frontend-developer"
        ],
        "description": "系统架构设计、技术选型、前后端规划"
    },
    {
        "sanliu_department": "门下省",
        "sanliu_bureau": "代码审查局",
        "target_agent_ids": [
            "engineering-code-reviewer",
            "engineering-security-engineer",
            "engineering-senior-developer"
        ],
        "description": "代码质量审查、安全漏洞检测、最佳实践检查"
    },
    {
        "sanliu_department": "门下省",
        "sanliu_bureau": "测试验证局",
        "target_agent_ids": [
            "testing-api-tester",
            "testing-test-results-analyzer",
            "testing-tool-evaluator"
        ],
        "description": "API 测试执行、测试结果分析、测试工具评估"
    },
    {
        "sanliu_department": "门下省",
        "sanliu_bureau": "安全合规局",
        "target_agent_ids": [
            "engineering-security-engineer",
            "specialized-compliance-auditor"
        ],
        "description": "安全审计、合规性检查、威胁评估"
    },
    {
        "sanliu_department": "尚书省",
        "sanliu_bureau": "工部-代码生成局",
        "target_agent_ids": [
            "engineering-senior-developer",
            "engineering-rapid-prototyper"
        ],
        "description": "高质量代码生成、快速原型开发"
    },
    {
        "sanliu_department": "尚书省",
        "sanliu_bureau": "工部-UI/UX设计局",
        "target_agent_ids": [
            "design-ui-designer",
            "design-ux-architect",
            "design-ux-researcher"
        ],
        "description": "界面视觉设计、用户体验架构、用户研究"
    },
    {
        "sanliu_department": "尚书省",
        "sanliu_bureau": "兵部-TDD驱动局",
        "target_agent_ids": [
            "testing-workflow-optimizer",
            "testing-evidence-collector"
        ],
        "description": "测试驱动开发流程优化、测试证据收集"
    },
    {
        "sanliu_department": "尚书省",
        "sanliu_bureau": "户部-性能优化局",
        "target_agent_ids": [
            "engineering-database-optimizer",
            "testing-performance-benchmarker",
            "engineering-autonomous-optimization-architect"
        ],
        "description": "数据库优化、性能基准测试、自动化性能调优"
    },
    {
        "sanliu_department": "尚书省",
        "sanliu_bureau": "礼部-文档撰写局",
        "target_agent_ids": [
            "engineering-technical-writer",
            "specialized-document-generator"
        ],
        "description": "技术文档编写、API 文档生成、知识库维护"
    },
    {
        "sanliu_department": "尚书省",
        "sanliu_bureau": "刑部-DevOps运维局",
        "target_agent_ids": [
            "engineering-devops-automator",
            "engineering-sre",
            "engineering-incident-response-commander"
        ],
        "description": "CI/CD 流水线、SRE 运维、事件响应"
    },
    {
        "sanliu_department": "尚书省",
        "sanliu_bureau": "兵部-安全攻防局",
        "target_agent_ids": [
            "engineering-threat-detection-engineer",
            "specialized-compliance-auditor",
            "blockchain-security-auditor"
        ],
        "description": "威胁检测、合规审计、区块链安全审查"
    },
    {
        "sanliu_department": "中书省",
        "sanliu_bureau": "数据分析局",
        "target_agent_ids": [
            "engineering-data-engineer",
            "support-analytics-reporter"
        ],
        "description": "数据管道构建、分析报告生成"
    },
    {
        "sanliu_department": "门下省",
        "sanliu_bureau": "可访问性审查局",
        "target_agent_ids": [
            "testing-accessibility-auditor",
            "design-inclusive-visuals-specialist"
        ],
        "description": "无障碍访问合规、包容性视觉设计"
    },
    {
        "sanliu_department": "尚书省",
        "sanliu_bureau": "工部-AI工程局",
        "target_agent_ids": [
            "engineering-ai-engineer",
            "engineering-ai-data-remediation-engineer"
        ],
        "description": "AI 模型集成、数据治理与修复"
    },
    {
        "sanliu_department": "尚书省",
        "sanliu_bureau": "户部-项目管理局",
        "target_agent_ids": [
            "project-management-project-shepherd",
            "product-sprint-prioritizer"
        ],
        "description": "项目全生命周期管理、Sprint 优先级排序"
    },
    {
        "sanliu_department": "门下省",
        "sanliu_bureau": "质量保障局",
        "target_agent_ids": [
            "testing-reality-checker",
            "testing-tool-evaluator",
            "engineering-code-reviewer"
        ],
        "description": "全方位质量保障、工具链评估、代码审查"
    },
    {
        "sanliu_department": "中书省",
        "sanliu_bureau": "市场策略局",
        "target_agent_ids": [
            "marketing-growth-hacker",
            "marketing-seo-specialist",
            "marketing-content-creator"
        ],
        "description": "增长策略制定、SEO 优化、内容营销"
    },
    {
        "sanliu_department": "尚书省",
        "sanliu_bureau": "吏部-人才招聘局",
        "target_agent_ids": [
            "recruitment-specialist",
            "corporate-training-designer"
        ],
        "description": "人才招募、企业培训体系设计"
    },
    {
        "sanliu_department": "尚书省",
        "sanliu_bureau": "工部-移动端开发局",
        "target_agent_ids": [
            "engineering-mobile-app-builder",
            "engineering-wechat-mini-program-developer"
        ],
        "description": "移动应用开发、微信小程序开发"
    },
    {
        "sanliu_department": "门下省",
        "sanliu_bureau": "前端体验审查局",
        "target_agent_ids": [
            "design-ux-architect",
            "design-ui-designer",
            "testing-accessibility-auditor"
        ],
        "description": "前端 UX/UI 审查、交互体验评估"
    },
    {
        "sanliu_department": "尚书省",
        "sanliu_bureau": "户部-财务追踪局",
        "target_agent_ids": [
            "support-finance-tracker",
            "support-executive-summary-generator"
        ],
        "description": "项目财务追踪、高管摘要生成"
    },
    {
        "sanliu_department": "中书省",
        "sanliu_bureau": "销售支持局",
        "target_agent_ids": [
            "sales-deal-strategist",
            "sales-proposal-strategist",
            "sales-account-strategist"
        ],
        "description": "销售策略制定、提案撰写、客户管理"
    }
]


# ============================================================
# 智能路由器 - 关键词映射表
# ============================================================

TASK_KEYWORD_MAPPING: Dict[str, List[Tuple[List[str], float, str]]] = {
    "代码审查": [(
        ["engineering-code-reviewer", "engineering-security-engineer",
         "engineering-senior-developer"],
        0.95,
        "代码质量全面审查，覆盖正确性、安全性、可维护性和性能"
    )],
    "UI设计": [(
        ["design-ui-designer", "design-ux-architect"],
        0.92,
        "界面视觉设计与用户体验架构"
    )],
    "UX设计": [(
        ["design-ux-architect", "design-ux-researcher"],
        0.90,
        "用户体验研究与交互架构设计"
    )],
    "安全审计": [(
        ["engineering-security-engineer", "specialized-compliance-auditor"],
        0.93,
        "安全漏洞扫描与合规性审计"
    )],
    "性能优化": [(
        ["engineering-senior-developer", "testing-performance-benchmarker",
         "engineering-database-optimizer"],
        0.91,
        "全栈性能分析与优化建议"
    )],
    "全栈开发": [(
        ["engineering-frontend-developer", "engineering-backend-architect",
         "engineering-database-optimizer"],
        0.89,
        "前后端一体化开发方案"
    )],
    "API开发": [(
        ["engineering-backend-architect", "engineering-cms-developer",
         "testing-api-tester"],
        0.88,
        "API 设计、实现与测试验证"
    )],
    "数据库设计": [(
        ["engineering-database-optimizer", "engineering-backend-architect",
         "engineering-data-engineer"],
        0.87,
        "数据库架构设计与查询优化"
    )],
    "测试自动化": [(
        ["testing-workflow-optimizer", "testing-api-tester",
         "testing-evidence-collector"],
        0.90,
        "自动化测试框架搭建与流程优化"
    )],
    "DevOps部署": [(
        ["engineering-devops-automator", "engineering-sre"],
        0.86,
        "CI/CD 流水线构建与运维监控"
    )],
    "移动端开发": [(
        ["engineering-mobile-app-builder",
         "engineering-wechat-mini-program-developer"],
        0.85,
        "移动应用与小程序开发"
    )],
    "AI/ML集成": [(
        ["engineering-ai-engineer", "engineering-ai-data-remediation-engineer"],
        0.84,
        "人工智能模型集成与数据治理"
    )],
    "文档编写": [(
        ["engineering-technical-writer", "specialized-document-generator"],
        0.88,
        "技术文档与知识库建设"
    )],
    "品牌设计": [(
        ["design-brand-guardian", "design-visual-storyteller"],
        0.83,
        "品牌视觉系统与叙事设计"
    )],
    "SEO优化": [(
        ["marketing-seo-specialist", "marketing-content-creator"],
        0.82,
        "搜索引擎优化与内容策略"
    )],
    "产品规划": [(
        ["product-manager", "product-trend-researcher",
         "product-behavioral-nudge-engine"],
        0.87,
        "产品路线图规划与用户行为分析"
    )],
    "项目管理": [(
        ["project-management-project-shepherd",
         "product-sprint-prioritizer"],
        0.85,
        "项目进度管理与迭代规划"
    )],
    "游戏开发": [(
        ["game-designer", "unity-architect", "level-designer"],
        0.80,
        "游戏设计与引擎开发"
    )],
    "空间计算": [(
        ["visionos-spatial-engineer", "xr-immersive-developer"],
        0.78,
        "VisionOS 与 XR 应用开发"
    )],
    "无障碍设计": [(
        ["testing-accessibility-auditor", "design-inclusive-visuals-specialist"],
        0.89,
        "WCAG 合规与包容性设计"
    )]
}


# ============================================================
# YAML Frontmatter 解析器（轻量级，无需 PyYAML）
# ============================================================


def _parse_yaml_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    解析 Markdown 文件的 YAML frontmatter。

    Args:
        content: 文件完整文本内容

    Returns:
        (frontmatter_dict, body_content) 元组
    """
    frontmatter = {}
    body = content

    if not content.startswith("---"):
        return frontmatter, body

    parts = content.split("---", 2)
    if len(parts) < 3:
        return frontmatter, body

    yaml_text = parts[1].strip()
    body = parts[2].strip()

    for line in yaml_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            frontmatter[key] = value

    return frontmatter, body


def _extract_capabilities(body: str) -> List[str]:
    """
    从 Agent 内容体中提取能力关键词列表。

    Args:
        body: Markdown 正文内容

    Returns:
        能力关键词列表
    """
    capabilities = []
    patterns = [
        r"\*\*(.+?)\*\*[—–-]\s*(.+)",
        r"- \*\*(.+?)\*\*",
        r"^\d+\.\s+\*\*(.+?)\*\*"
    ]
    seen = set()
    for pattern in patterns:
        for match in re.finditer(pattern, body, re.MULTILINE):
            cap = match.group(1).strip()
            if cap and cap.lower() not in seen and len(cap) < 60:
                capabilities.append(cap)
                seen.add(cap.lower())
            if len(capabilities) >= 12:
                break
        if len(capabilities) >= 12:
            break
    return capabilities[:10]


def _extract_role(body: str) -> str:
    """
    从内容体中提取 Role 信息。

    Args:
        body: Markdown 正文内容

    Returns:
        角色描述字符串
    """
    role_patterns = [
        r"\*\*Role\*\*:\s*(.+)",
        r"角色[：:]\s*(.+)",
        r"Role:\s*(.+)"
    ]
    for pattern in role_patterns:
        match = re.search(pattern, body)
        if match:
            return match.group(1).strip()
    return ""


# ============================================================
# AgencyBridge 主类
# ============================================================


class AgencyBridge:
    """
    Agency Agents 桥接层核心类。

    提供 Agent 注册表管理、智能路由、调用调度和结果整合四大核心功能。
    支持与 MARC ResourceCoordinator 可选集成以实现资源协调。
    """

    def __init__(self, base_path: Optional[str] = None,
                 resource_coordinator=None):
        """
        初始化 AgencyBridge。

        Args:
            base_path: 项目根目录路径，默认自动探测
            resource_coordinator: 可选的 MARC ResourceCoordinator 实例
        """
        self.base_path = base_path or self._detect_base_path()
        self.registry_path = os.path.join(self.base_path, AGENT_REGISTRY_PATH)
        self.resource_coordinator = resource_coordinator
        self._agent_cache: Dict[str, AgentInfo] = {}
        self._cache_lock = threading.Lock()
        self._call_history: List[AgentResult] = []
        self._history_lock = threading.Lock()

        logger.info(
            f"AgencyBridge 初始化完成 | 注册表路径: {self.registry_path} | "
            f"MARC集成: {'已启用' if resource_coordinator else '未启用'}"
        )

    @staticmethod
    def _detect_base_path() -> str:
        """自动探测项目根目录（向上查找 .trae 目录）"""
        current = os.getcwd()
        while current != os.path.dirname(current):
            if os.path.isdir(os.path.join(current, ".trae")):
                return current
            current = os.path.dirname(current)
        return os.getcwd()

    # ----------------------------------------------------------
    # 1. Agent 注册表扫描
    # ----------------------------------------------------------

    def list_available_agents(self, domain: Optional[str] = None) -> List[AgentInfo]:
        """
        扫描 agency-agents 注册表，返回可用 Agent 列表。

        遍历所有支持的域子目录，解析每个 .md 文件的 YAML frontmatter，
        提取 name、description、role、capabilities 等元信息。

        Args:
            domain: 可选域名过滤（如 "engineering"、"design"），
                    为 None 时返回所有域的 Agent

        Returns:
            AgentInfo 对象列表
        """
        with self._cache_lock:
            if self._agent_cache and domain is None:
                return list(self._agent_cache.values())

        results: List[AgentInfo] = []

        if not os.path.isdir(self.registry_path):
            logger.warning(f"Agent 注册表目录不存在: {self.registry_path}")
            return results

        domains_to_scan = [domain] if domain else SUPPORTED_DOMAINS

        for dom in domains_to_scan:
            dom_dir = os.path.join(self.registry_path, dom)
            if not os.path.isdir(dom_dir):
                continue

            for filename in os.listdir(dom_dir):
                if not filename.endswith(".md") or filename.startswith("."):
                    continue

                file_path = os.path.join(dom_dir, filename)
                try:
                    agent_info = self._parse_agent_file(file_path, dom)
                    if agent_info:
                        results.append(agent_info)
                        with self._cache_lock:
                            self._agent_cache[agent_info.agent_id] = agent_info
                except Exception as e:
                    logger.warning(f"解析 Agent 文件失败 {file_path}: {e}")

        logger.info(
            f"Agent 扫描完成 | 域过滤: {domain or '全部'} | "
            f"发现 {len(results)} 个 Agent"
        )
        return results

    def _parse_agent_file(self, file_path: str, domain: str) -> Optional[AgentInfo]:
        """
        解析单个 Agent .md 文件，提取元信息。

        Args:
            file_path: .md 文件绝对路径
            domain: 所属域名称

        Returns:
            AgentInfo 对象，解析失败返回 None
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (IOError, OSError) as e:
            logger.error(f"无法读取文件 {file_path}: {e}")
            return None

        filename = os.path.splitext(os.path.basename(file_path))[0]
        frontmatter, body = _parse_yaml_frontmatter(content)

        name = frontmatter.get("name", filename.replace("-", " ").title())
        description = frontmatter.get("description", "")
        emoji = frontmatter.get("emoji", "")
        color = frontmatter.get("color", "")
        vibe = frontmatter.get("vibe", "")

        role = _extract_role(body)
        capabilities = _extract_capabilities(body)

        return AgentInfo(
            agent_id=filename,
            name=name,
            description=description,
            domain=domain,
            role=role,
            capabilities=capabilities,
            emoji=emoji,
            color=color,
            vibe=vibe,
            file_path=file_path
        )

    def get_agent_spec(self, agent_id: str) -> Optional[AgentSpec]:
        """
        获取单个 Agent 的完整规格信息。

        Args:
            agent_id: Agent 标识符（如 "engineering-code-reviewer"）

        Returns:
            AgentSpec 对象，包含完整内容和原始 frontmatter；
            Agent 不存在时返回 None
        """
        cached = self._agent_cache.get(agent_id)
        if cached:
            file_path = cached.file_path
        else:
            file_path = self._find_agent_file(agent_id)
            if not file_path:
                logger.warning(f"未找到 Agent: {agent_id}")
                return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (IOError, OSError) as e:
            logger.error(f"读取 Agent 规格失败 {file_path}: {e}")
            return None

        frontmatter, body = _parse_yaml_frontmatter(content)

        if not cached:
            cached = self._parse_agent_file(file_path, "")

        return AgentSpec(
            info=cached,
            full_content=content,
            raw_frontmatter=frontmatter
        )

    def _find_agent_file(self, agent_id: str) -> Optional[str]:
        """
        在注册表中搜索指定 agent_id 对应的文件路径。

        Args:
            agent_id: Agent 标识符

        Returns:
            文件绝对路径，未找到返回 None
        """
        for domain in SUPPORTED_DOMAINS:
            candidate = os.path.join(
                self.registry_path, domain, f"{agent_id}.md"
            )
            if os.path.isfile(candidate):
                return candidate
        return None

    # ----------------------------------------------------------
    # 2. 智能路由器 SmartRouter
    # ----------------------------------------------------------

    def recommend_agents(self, task_description: str) -> List[AgentRecommendation]:
        """
        基于任务描述智能推荐最相关的 Agent 组合。

        分析任务描述中的关键词，匹配预定义的关键词映射表，
        计算每个候选 Agent 的置信度分数并返回排序列表。

        Args:
            task_description: 任务的自然语言描述

        Returns:
            按 confidence 降序排列的 AgentRecommendation 列表
        """
        recommendations: List[AgentRecommendation] = []
        seen_agents: Set[str] = set()
        task_lower = task_description.lower()

        all_agents = self.list_available_agents()
        agent_map: Dict[str, AgentInfo] = {a.agent_id: a for a in all_agents}

        for keyword, entries in TASK_KEYWORD_MAPPING.items():
            if keyword.lower() in task_lower:
                for agent_ids, base_confidence, reason in entries:
                    for aid in agent_ids:
                        if aid in seen_agents:
                            continue
                        info = agent_map.get(aid)
                        if info:
                            seen_agents.add(aid)
                            recommendations.append(AgentRecommendation(
                                agent_id=aid,
                                name=info.name,
                                confidence=base_confidence,
                                reason=reason,
                                domain=info.domain
                            ))

        if not recommendations:
            recommendations = self._fallback_recommend(task_description, agent_map, seen_agents)

        recommendations.sort(key=lambda r: r.confidence, reverse=True)

        logger.info(
            f"智能路由完成 | 任务: {task_description[:50]}... | "
            f"推荐 {len(recommendations)} 个 Agent"
        )
        return recommendations

    def _fallback_recommend(
        self, task_desc: str, agent_map: Dict[str, AgentInfo],
        seen: Set[str]
    ) -> List[AgentRecommendation]:
        """
        当精确关键词匹配失败时的兜底推荐策略。
        基于任务描述中的词汇与 Agent 描述/能力的模糊匹配进行评分。

        Args:
            task_desc: 任务描述
            agent_map: 全量 Agent 映射
            seen: 已推荐 Agent ID 集合

        Returns:
        """
        fallback: List[AgentRecommendation] = []
        words = set(re.findall(r"[\u4e00-\u9fff\w]{2,}", task_desc.lower()))

        scored: List[Tuple[str, float, str, str]] = []
        for aid, info in agent_map.items():
            if aid in seen:
                continue
            desc_lower = info.description.lower() + " " + " ".join(
                c.lower() for c in info.capabilities
            )
            score = sum(1 for w in words if w in desc_lower)
            if score > 0:
                scored.append((aid, min(score / max(len(words), 1), 0.7),
                               info.name, info.domain))

        scored.sort(key=lambda x: x[1], reverse=True)
        for aid, conf, name, dom in scored[:5]:
            fallback.append(AgentRecommendation(
                agent_id=aid, name=name, confidence=conf,
                reason=f"基于关键词匹配（{conf:.0%} 相关度）", domain=dom
            ))
        return fallback

    # ----------------------------------------------------------
    # 3. 调用接口
    # ----------------------------------------------------------

    def invoke_agent(
        self, agent_id: str, task: str, context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        同步调用单个 Agent 执行任务。

        构造完整的调用上下文（含项目根路径、时间戳等），
        记录调用日志，返回结构化结果。

        Args:
            agent_id: 目标 Agent 标识符
            task: 任务描述字符串
            context: 额外上下文字典（如文件路径、变量等）

        Returns:
            AgentResult 调用结果对象
        """
        start_time = datetime.now()
        context = context or {}

        full_context = {
            "project_root": self.base_path,
            "invoked_at": start_time.isoformat(),
            "agent_id": agent_id,
            **context
        }

        spec = self.get_agent_spec(agent_id)
        if not spec:
            result = AgentResult(
                agent_id=agent_id, task=task, success=False,
                error=f"Agent '{agent_id}' 未在注册表中找到"
            )
            self._record_call(result)
            return result

        try:
            output = self._execute_agent(spec, task, full_context)
            duration = int((datetime.now() - start_time).total_seconds() * 1000)

            result = AgentResult(
                agent_id=agent_id, task=task, success=True,
                output=output, duration_ms=duration,
                metadata={"context_keys": list(full_context.keys())}
            )
        except Exception as e:
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            result = AgentResult(
                agent_id=agent_id, task=task, success=False,
                error=str(e), duration_ms=duration
            )

        self._record_call(result)
        return result

    def invoke_agents_parallel(
        self, agent_ids: List[str], task: str,
        context: Optional[Dict[str, Any]] = None,
        max_workers: int = 4
    ) -> List[AgentResult]:
        """
        并行调用多个 Agent 执行同一任务。

        使用 ThreadPoolExecutor 实现并行调度，
        若存在 MARC ResourceCoordinator 则优先使用其协调机制。

        Args:
            agent_ids: 目标 Agent ID 列表
            task: 共享任务描述
            context: 额外上下文字典
            max_workers: 最大并发线程数

        Returns:
            与 agent_ids 顺序对应的 AgentResult 列表
        """
        context = context or {}
        results_map: Dict[str, AgentResult] = {}
        order_map: Dict[str, int] = {aid: i for i, aid in enumerate(agent_ids)}

        if self.resource_coordinator:
            results = self._invoke_with_marc(agent_ids, task, context)
        else:
            results = self._invoke_with_threadpool(
                agent_ids, task, context, max_workers
            )

        for r in results:
            results_map[r.agent_id] = r

        ordered_results = [None] * len(agent_ids)
        for aid, idx in order_map.items():
            ordered_results[idx] = results_map.get(aid, AgentResult(
                agent_id=aid, task=task, success=False,
                error=f"Agent '{aid}' 未产生结果"
            ))

        logger.info(
            f"并行调用完成 | 任务: {task[:40]}... | "
            f"请求 {len(agent_ids)} 个 Agent | 成功 {sum(1 for r in ordered_results if r.success)}"
        )
        return ordered_results

    def _invoke_with_threadpool(
        self, agent_ids: List[str], task: str,
        context: Dict[str, Any], max_workers: int
    ) -> List[AgentResult]:
        """使用线程池并行调用 Agent"""
        results: List[AgentResult] = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_agent = {
                executor.submit(self.invoke_agent, aid, task, context): aid
                for aid in agent_ids
            }

            for future in as_completed(future_to_agent):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    aid = future_to_agent[future]
                    results.append(AgentResult(
                        agent_id=aid, task=task, success=False, error=str(e)
                    ))

        return results

    def _invoke_with_marc(
        self, agent_ids: List[str], task: str,
        context: Dict[str, Any]
    ) -> List[AgentResult]:
        """
        通过 MARC ResourceCoordinator 协调并行调用。

        利用 ResourceCoordinator 的锁管理和调度队列机制，
        确保资源共享安全和公平调度。

        Args:
            agent_ids: Agent ID 列表
            task: 任务描述
            context: 上下文

        Returns:
            AgentResult 列表
        """
        results: List[AgentResult] = []
        rc = self.resource_coordinator

        try:
            for aid in agent_ids:
                try:
                    if hasattr(rc, "acquire_resource"):
                        rc.acquire_resource(
                            f"agent:{aid}", agent_id=aid,
                            lock_type_name="shared"
                        )
                    result = self.invoke_agent(aid, task, context)
                    results.append(result)
                except Exception as e:
                    results.append(AgentResult(
                        agent_id=aid, task=task, success=False,
                        error=f"MARC 协调错误: {e}"
                    ))
                finally:
                    if hasattr(rc, "release_resource"):
                        try:
                            rc.release_resource(f"agent:{aid}", aid)
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"MARC 协调器异常: {e}")

        return results

    def _execute_agent(
        self, spec: AgentSpec, task: str, context: Dict[str, Any]
    ) -> str:
        """
        执行 Agent 的核心逻辑（模拟执行）。

        在实际集成场景中，此方法会调用具体的 Agent 运行时。
        当前版本返回基于 Agent 规格生成的模拟响应。

        Args:
            spec: Agent 完整规格
            task: 待执行任务
            context: 执行上下文

        Returns:
            Agent 输出文本
        """
        lines = [
            f"[{spec.info.name}] 任务执行报告",
            f"",
            f"**任务**: {task}",
            f"**Agent**: {spec.info.agent_id} ({spec.info.domain})",
            f"**角色**: {spec.info.role or spec.info.description}",
            f"",
            f"--- 分析结果 ---",
            f"根据 [{spec.info.name}]({spec.info.file_path}) 的专业能力，",
            f"对上述任务进行了分析处理。",
            f"",
            f"**能力范围**: {', '.join(spec.info.capabilities[:5]) if spec.info.capabilities else '综合分析'}",
            f"**上下文参数**: {list(context.keys())}",
            f"",
            f"*注：当前为桥接层模拟执行模式。集成实际运行时时将替换为真实 Agent 调用。*"
        ]
        return "\n".join(lines)

    def _record_call(self, result: AgentResult) -> None:
        """记录调用历史日志"""
        with self._history_lock:
            self._call_history.append(result)
            if len(self._call_history) > 500:
                self._call_history = self._call_history[-300:]

    # ----------------------------------------------------------
    # 4. 结果整合器 ResultAggregator
    # ----------------------------------------------------------

    def aggregate_results(
        self, results: List[AgentResult], task_description: str = ""
    ) -> AggregatedReport:
        """
        整合多个 Agent 的输出结果，生成综合报告。

        功能包括：
        - 收集所有成功/失败的 Agent 输出
        - 冲突检测：相同文件的修改建议冲突、严重级别不一致等
        - 发现提取与严重级别排序
        - 生成结构化摘要

        Args:
            results: AgentResult 列表
            task_description: 原始任务描述（用于报告头部）

        Returns:
            AggregatedReport 综合报告
        """
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        findings = self._extract_findings(successful)
        conflicts = self._detect_conflicts(successful)
        summary = self._generate_summary(results, findings, conflicts)

        report = AggregatedReport(
            task_description=task_description,
            total_agents=len(results),
            successful_agents=len(successful),
            failed_agents=len(failed),
            results=results,
            findings=findings,
            conflicts=conflicts,
            summary=summary
        )

        logger.info(
            f"结果整合完成 | 总计 {len(results)} | 成功 {len(successful)} | "
            f"发现 {len(findings)} 项 | 冲突 {len(conflicts)} 处"
        )
        return report

    def _extract_findings(self, results: List[AgentResult]) -> List[Dict[str, Any]]:
        """
        从各 Agent 输出中提取结构化发现项。

        解析输出文本中的关键信息块（如 🔴🟡💭 标记、
        **加粗** 关键行），按严重级别排序。

        Args:
            results: 成功的 AgentResult 列表

        Returns:
            发现项字典列表
        """
        findings: List[Dict[str, Any]] = []
        severity_order = {"critical": 0, "blocker": 0, "major": 1,
                         "warning": 1, "suggestion": 2, "minor": 2, "nit": 3}

        for result in results:
            output = result.output
            agent_severity = "unknown"

            pattern_map = [
                (r"[🔴❌]", "critical"),
                (r"[🟡⚠️]", "major"),
                (r"[💭ℹ️]", "suggestion"),
                (r"[🟢✅]", "info")
            ]
            for marker, sev in pattern_map:
                if marker[0] in output:
                    agent_severity = sev
                    break

            sections = re.split(r"\n(?=#+\s|\*\*|---)", output)
            for section in sections[:8]:
                section = section.strip()
                if len(section) < 20:
                    continue
                findings.append({
                    "agent_id": result.agent_id,
                    "severity": agent_severity,
                    "content": section[:500],
                    "source_task": result.task
                })

        findings.sort(key=lambda f: severity_order.get(f["severity"], 99))
        return findings[:30]

    def _detect_conflicts(self, results: List[AgentResult]) -> List[ConflictItem]:
        """
        检测多个 Agent 输出之间的冲突。

        冲突类型：
        - modification_conflict: 同一文件的不同修改建议
        - suggestion_conflict: 相互矛盾的建议
        - severity_mismatch: 同一问题的不同严重级别判定

        Args:
            results: 成功的 AgentResult 列表

        returns:
            ConflictItem 列表
        """
        conflicts: List[ConflictItem] = []
        file_mentions: Dict[str, List[str]] = {}

        for result in results:
            files = re.findall(r"(?:file|文件|path)[s：:\s]*([\w\-./]+\.?\w*)",
                               result.output, re.IGNORECASE)
            for f in files:
                file_mentions.setdefault(f, []).append(result.agent_id)

        for file_path, agents in file_mentions.items():
            if len(agents) > 1:
                conflicts.append(ConflictItem(
                    file_path=file_path,
                    conflict_type="modification_conflict",
                    agents_involved=agents,
                    description=(
                        f"多个 Agent 对文件 '{file_path}' 提出了修改建议，"
                        f"需人工审核合并：{', '.join(agents)}"
                    ),
                    severity="major"
                ))

        suggestion_keywords: Dict[str, List[str]] = {}
        for result in results:
            suggestions = re.findall(r"(?:建议|suggest|consider)[：:\s]*(.{10,80})",
                                      result.output, re.IGNORECASE)
            for s in suggestions:
                key = s[:30].lower()
                suggestion_keywords.setdefault(key, []).append(result.agent_id)

        for keyword, agents in suggestion_keywords.items():
            if len(agents) > 1:
                conflicts.append(ConflictItem(
                    file_path="(general)",
                    conflict_type="suggestion_conflict",
                    agents_involved=agents,
                    description=(
                        f"检测到相似建议来自多个 Agent: {keyword}... "
                        f"涉及: {', '.join(agents)}"
                    ),
                    severity="minor"
                ))

        return conflicts[:15]

    @staticmethod
    def _generate_summary(
        results: List[AgentResult],
        findings: List[Dict[str, Any]],
        conflicts: List[ConflictItem]
    ) -> str:
        """生成报告摘要文本"""
        total = len(results)
        ok = sum(1 for r in results if r.success)
        critical_count = sum(
            1 for f in findings if f["severity"] in ("critical", "blocker")
        )

        parts = [
            f"## 综合报告摘要",
            f"",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 参与Agent总数 | {total} |",
            f"| 成功执行 | {ok} |",
            f"| 执行失败 | {total - ok} |",
            f"| 关键发现 | {critical_count} |",
            f"| 一般发现 | {len(findings) - critical_count} |",
            f"| 检测到的冲突 | {len(conflicts)} |",
            f""
        ]

        if conflicts:
            parts.append("### 主要冲突")
            for c in conflicts[:5]:
                parts.append(f"- **[{c.severity.upper()}]** {c.description}")

        if critical_count > 0:
            parts.append("\n### 关键问题")
            for f in findings[:3]:
                parts.append(f"- **[{f['severity']}]** {f['content'][:100]}...")

        return "\n".join(parts)

    # ----------------------------------------------------------
    # 5. Sanliu 映射查询
    # ----------------------------------------------------------

    def resolve_sanliu_mapping(
        self, department: str, bureau: Optional[str] = None
    ) -> List[SanliuMappingEntry]:
        """
        根据 Sanliu 六部制部门和局名查询对应的 Agency Agent 映射。

        Args:
            department: 部门名称（如 "中书省"、"门下省"、"尚书省"）
            bureau: 可选局名（如 "需求分析局"、"代码审查局"）

        Returns:
            匹配的 SanliuMappingEntry 列表
        """
        matches: List[SanliuMappingEntry] = []

        for entry_data in SANLIU_AGENCY_MAPPING:
            dept_match = entry_data["sanliu_department"] == department
            bureau_match = (bureau is None or
                            entry_data["sanliu_bureau"] == bureau)
            if dept_match and bureau_match:
                matches.append(SanliuMappingEntry(
                    sanliu_department=entry_data["sanliu_department"],
                    sanliu_bureau=entry_data["sanliu_bureau"],
                    target_agent_ids=entry_data["target_agent_ids"],
                    description=entry_data.get("description", "")
                ))

        logger.info(
            f"Sanliu 映射查询 | 部门: {department} | 局: {bureau or '全部'} | "
            f"匹配 {len(matches)} 条"
        )
        return matches

    def get_all_sanliu_mappings(self) -> List[SanliuMappingEntry]:
        """获取完整的 Sanliu → Agency Agent 映射矩阵"""
        return [
            SanliuMappingEntry(
                sanliu_department=e["sanliu_department"],
                sanliu_bureau=e["sanliu_bureau"],
                target_agent_ids=e["target_agent_ids"],
                description=e.get("description", "")
            )
            for e in SANLIU_AGENCY_MAPPING
        ]

    def invoke_by_sanliu(
        self, department: str, bureau: str,
        task: str, context: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[AgentResult], AggregatedReport]:
        """
        通过 Sanliu 六部制接口调用 Agency Agent。

        将 Sanliu 部门-局名翻译为对应 Agent 组合后并行调用，
        自动整合结果并返回综合报告。

        Args:
            department: 六部制部门
            bureau: 局名
            task: 任务描述
            context: 上下文字典

        Returns:
            (results_list, aggregated_report) 元组
        """
        mappings = self.resolve_sanliu_mapping(department, bureau)
        if not mappings:
            empty_result = AgentResult(
                agent_id="system", task=task, success=False,
                error=f"未找到映射: {department}-{bureau}"
            )
            report = self.aggregate_results([empty_result], task)
            return [empty_result], report

        all_agent_ids: List[str] = []
        for m in mappings:
            all_agent_ids.extend(m.target_agent_ids)

        unique_agent_ids = list(dict.fromkeys(all_agent_ids))
        results = self.invoke_agents_parallel(unique_agent_ids, task, context)
        report = self.aggregate_results(results, task)

        logger.info(
            f"Sanliu 调用完成 | {department}-{bureau} | "
            f"调度 {len(unique_agent_ids)} 个 Agent"
        )
        return results, report

    # ----------------------------------------------------------
    # 工具方法
    # ----------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """获取 Bridge 运行统计信息"""
        with self._history_lock:
            history = self._call_history.copy()

        total_calls = len(history)
        success_count = sum(1 for r in history if r.success)
        avg_duration = (
            sum(r.duration_ms for r in history) / max(total_calls, 1)
            if total_calls > 0 else 0
        )

        agent_call_counts: Dict[str, int] = {}
        for r in history:
            agent_call_counts[r.agent_id] = agent_call_counts.get(r.agent_id, 0) + 1

        top_agents = sorted(
            agent_call_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        return {
            "total_calls": total_calls,
            "success_rate": success_count / max(total_calls, 1),
            "avg_duration_ms": round(avg_duration, 1),
            "cached_agents": len(self._agent_cache),
            "marc_enabled": self.resource_coordinator is not None,
            "top_agents": top_agents
        }

    def clear_cache(self) -> None:
        """清除 Agent 缓存，下次调用时重新扫描"""
        with self._cache_lock:
            self._agent_cache.clear()
        logger.info("Agent 缓存已清除")

    def export_report_json(self, report: AggregatedReport) -> str:
        """将聚合报告导出为 JSON 字符串"""
        data = asdict(report)
        return json.dumps(data, ensure_ascii=False, indent=2)


# ============================================================
# 便捷函数
# ============================================================


def create_bridge(base_path: Optional[str] = None) -> AgencyBridge:
    """
    工厂函数：创建 AgencyBridge 实例。

    尝试自动导入 ResourceCoordinator 进行可选集成。

    Args:
        base_path: 项目根路径

    Returns:
        已初始化的 AgencyBridge 实例
    """
    coordinator = None
    try:
        from core.resource_coordinator import ResourceCoordinator
        coordinator = ResourceCoordinator()
        logger.info("MARC ResourceCoordinator 集成成功")
    except ImportError:
        logger.info("MARC ResourceCoordinator 不可用，使用独立模式")
    except Exception as e:
        logger.warning(f"MARC ResourceCoordinator 初始化失败: {e}")

    return AgencyBridge(base_path=base_path, resource_coordinator=coordinator)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    bridge = create_bridge()

    print("=" * 60)
    print("AgencyBridge 演示")
    print("=" * 60)

    agents = bridge.list_available_agents(domain="engineering")
    print(f"\n[1] Engineering 域 Agent 数量: {len(agents)}")
    for a in agents[:5]:
        print(f"   - {a.emoji} {a.name} ({a.agent_id}): {a.description[:60]}...")

    recs = bridge.recommend_agents("请帮我做一次全面的代码审查")
    print(f"\n[2] 智能路由推荐 ('代码审查'):")
    for r in recs:
        print(f"   - {r.name} | 置信度: {r.confidence:.0%} | {r.reason}")

    mappings = bridge.resolve_sanliu_mapping("门下省", "代码审查局")
    print(f"\n[3] Sanliu 映射 ('门下省-代码审查局'):")
    for m in mappings:
        print(f"   → {m.target_agent_ids} | {m.description}")

    stats = bridge.get_statistics()
    print(f"\n[4] 统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}")
