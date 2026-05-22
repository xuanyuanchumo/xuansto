#!/usr/bin/env python3
"""
技能调用链检查器 - Sanliu 技能

功能：
- 调用顺序验证
- 循环调用检测
- 无效调用识别
- 调用深度分析
- 调用性能分析
- 生成调用链检查报告

使用方法：
    python scripts/skill_call_chain_checker.py --check-all
    python scripts/skill_call_chain_checker.py --check-order
    python scripts/skill_call_chain_checker.py --check-circular
    python scripts/skill_call_chain_checker.py --check-invalid
    python scripts/skill_call_chain_checker.py --analyze-depth
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('skill_call_chain_checker.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class CheckStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


class CheckSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CallType(Enum):
    """调用类型枚举"""
    SYNC = "sync"
    ASYNC = "async"
    CALLBACK = "callback"
    EVENT = "event"


class SkillCategory(Enum):
    """技能分类枚举"""
    PROVINCIAL = "provincial"
    DEPARTMENT = "department"
    EXTERNAL = "external"
    UTILITY = "utility"


@dataclass
class SkillCall:
    """技能调用数据类"""
    call_id: str
    skill_name: str
    caller: Optional[str]
    callee: Optional[str]
    timestamp: str
    status: str
    duration: float = 0.0
    parent_call_id: Optional[str] = None
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    call_type: CallType = CallType.SYNC
    retry_count: int = 0
    priority: int = 0
    tags: list[str] = field(default_factory=list)


@dataclass
class CallChainResult:
    check_id: str
    check_name: str
    status: CheckStatus
    severity: CheckSeverity
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CircularCallInfo:
    """循环调用信息"""
    call_chain: list[str]
    detected_at: str
    depth: int
    affected_skills: list[str]
    cycle_type: str = "direct"


@dataclass
class InvalidCallInfo:
    """无效调用信息"""
    call_id: str
    skill_name: str
    reason: str
    suggestion: str
    severity: CheckSeverity = CheckSeverity.MEDIUM


@dataclass
class CallFrequencyInfo:
    """调用频率信息"""
    skill_name: str
    call_count: int
    avg_interval: float
    peak_hour: int
    anomaly_score: float


@dataclass
class SkillCallChainReport:
    report_id: str
    generated_at: str
    total_calls: int
    valid_calls: int
    invalid_calls: int
    circular_calls: int
    max_depth: int
    avg_duration: float
    results: list[CallChainResult]
    circular_detected: list[CircularCallInfo]
    invalid_detected: list[InvalidCallInfo]
    call_graph: dict[str, list[str]]
    summary: dict[str, Any]
    overall_status: CheckStatus


class SkillRegistry:
    """技能注册表 - 集中管理所有技能的定义和约束"""

    def __init__(self):
        self.skills: dict[str, dict[str, Any]] = {
            "sanliu": {
                "category": SkillCategory.PROVINCIAL,
                "required_skills": [],
                "optional_skills": ["skill-creator", "ui-ux-pro-max", "mcp-builder", "global-chinese"],
                "provides": ["full_development_cycle"],
                "max_call_depth": 15,
                "timeout": 300,
                "retry_limit": 3,
                "description": "三省六部主技能，协调整体开发流程"
            },
            "zhongshusheng": {
                "category": SkillCategory.PROVINCIAL,
                "required_skills": [],
                "optional_skills": ["sanliu"],
                "provides": ["requirement_analysis", "architecture_design", "specification"],
                "max_call_depth": 10,
                "timeout": 120,
                "retry_limit": 2,
                "description": "中书省 - 负责需求分析和架构设计"
            },
            "menxiasheng": {
                "category": SkillCategory.PROVINCIAL,
                "required_skills": ["zhongshusheng"],
                "optional_skills": ["sanliu"],
                "provides": ["review", "quality_gate", "approval"],
                "max_call_depth": 8,
                "timeout": 60,
                "retry_limit": 2,
                "description": "门下省 - 负责审核和质量把关"
            },
            "shangshusheng": {
                "category": SkillCategory.PROVINCIAL,
                "required_skills": ["menxiasheng"],
                "optional_skills": ["sanliu"],
                "provides": ["execution", "implementation"],
                "max_call_depth": 12,
                "timeout": 180,
                "retry_limit": 3,
                "description": "尚书省 - 负责执行和实施"
            },
            "libu": {
                "category": SkillCategory.DEPARTMENT,
                "required_skills": ["shangshusheng"],
                "optional_skills": [],
                "provides": ["hr_management", "agent_assignment"],
                "max_call_depth": 5,
                "timeout": 30,
                "retry_limit": 2,
                "description": "吏部 - 负责人力资源和代理分配"
            },
            "hubu": {
                "category": SkillCategory.DEPARTMENT,
                "required_skills": ["shangshusheng"],
                "optional_skills": [],
                "provides": ["resource_management", "budget"],
                "max_call_depth": 5,
                "timeout": 30,
                "retry_limit": 2,
                "description": "户部 - 负责资源管理和预算"
            },
            "liibu": {
                "category": SkillCategory.DEPARTMENT,
                "required_skills": ["shangshusheng"],
                "optional_skills": [],
                "provides": ["legal_compliance", "standards"],
                "max_call_depth": 5,
                "timeout": 30,
                "retry_limit": 2,
                "description": "礼部 - 负责合规和标准"
            },
            "bingbu": {
                "category": SkillCategory.DEPARTMENT,
                "required_skills": ["shangshusheng"],
                "optional_skills": [],
                "provides": ["testing", "quality_assurance"],
                "max_call_depth": 8,
                "timeout": 120,
                "retry_limit": 3,
                "description": "兵部 - 负责测试和质量保证"
            },
            "xingbu": {
                "category": SkillCategory.DEPARTMENT,
                "required_skills": ["shangshusheng"],
                "optional_skills": [],
                "provides": ["refactoring", "code_improvement"],
                "max_call_depth": 8,
                "timeout": 90,
                "retry_limit": 2,
                "description": "刑部 - 负责重构和代码改进"
            },
            "gongbu": {
                "category": SkillCategory.DEPARTMENT,
                "required_skills": ["shangshusheng"],
                "optional_skills": [],
                "provides": ["implementation", "code_generation"],
                "max_call_depth": 10,
                "timeout": 150,
                "retry_limit": 3,
                "description": "工部 - 负责实现和代码生成"
            },
            "skill-creator": {
                "category": SkillCategory.EXTERNAL,
                "required_skills": [],
                "optional_skills": ["sanliu"],
                "provides": ["skill_creation", "skill_modification"],
                "max_call_depth": 6,
                "timeout": 60,
                "retry_limit": 2,
                "description": "技能创建器 - 创建和修改技能"
            },
            "ui-ux-pro-max": {
                "category": SkillCategory.EXTERNAL,
                "required_skills": [],
                "optional_skills": ["sanliu"],
                "provides": ["ui_design", "ux_optimization", "frontend_development"],
                "max_call_depth": 8,
                "timeout": 90,
                "retry_limit": 2,
                "description": "UI/UX增强器 - 前端设计和优化"
            },
            "mcp-builder": {
                "category": SkillCategory.EXTERNAL,
                "required_skills": [],
                "optional_skills": ["sanliu"],
                "provides": ["mcp_server_creation", "api_integration"],
                "max_call_depth": 6,
                "timeout": 60,
                "retry_limit": 2,
                "description": "MCP构建器 - 创建MCP服务器"
            },
            "global-chinese": {
                "category": SkillCategory.UTILITY,
                "required_skills": [],
                "optional_skills": [],
                "provides": ["chinese_language_support"],
                "max_call_depth": 3,
                "timeout": 10,
                "retry_limit": 1,
                "description": "中文语言支持"
            }
        }

        self.deprecated_skills = {
            "old-sanliu": {"replacement": "sanliu", "reason": "版本升级", "deprecated_since": "2024-01-01"},
            "legacy-tester": {"replacement": "bingbu", "reason": "架构重构", "deprecated_since": "2024-01-01"},
            "v1-architect": {"replacement": "zhongshusheng", "reason": "功能整合", "deprecated_since": "2024-02-01"},
        }

        self.call_order_rules = {
            "provincial_order": ["zhongshusheng", "menxiasheng", "shangshusheng"],
            "tdd_order": ["bingbu", "gongbu", "xingbu"],
            "department_order": ["libu", "hubu", "liibu", "bingbu", "xingbu", "gongbu"],
        }

    def get_skill(self, skill_name: str) -> Optional[dict[str, Any]]:
        """获取技能信息"""
        return self.skills.get(skill_name)

    def is_valid_skill(self, skill_name: str) -> bool:
        """检查技能是否有效"""
        return skill_name in self.skills

    def is_deprecated(self, skill_name: str) -> bool:
        """检查技能是否已弃用"""
        return skill_name in self.deprecated_skills

    def get_deprecated_info(self, skill_name: str) -> Optional[dict[str, str]]:
        """获取弃用技能信息"""
        return self.deprecated_skills.get(skill_name)

    def get_required_params(self, skill_name: str) -> list[str]:
        """获取技能必需参数"""
        required_params_map = {
            "sanliu": ["description"],
            "skill-creator": ["name"],
            "mcp-builder": ["server_name"],
            "ui-ux-pro-max": ["project_type"],
        }
        return required_params_map.get(skill_name, [])


class CallOrderValidator:
    """调用顺序验证器（增强版）"""

    def __init__(self, registry: SkillRegistry = None):
        self.registry = registry or SkillRegistry()

    def validate_order(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "ORDER-001"
        check_name = "调用顺序验证"

        issues = []
        warnings = []
        suggestions = []

        call_sequence = [c.skill_name for c in calls]

        provincial_order = self.registry.call_order_rules["provincial_order"]
        self._validate_sequence_order(call_sequence, provincial_order, issues, "三省")

        tdd_order = self.registry.call_order_rules["tdd_order"]
        tdd_calls = [c for c in calls if c.skill_name in tdd_order]
        if tdd_calls:
            tdd_sequence = [c.skill_name for c in tdd_calls]
            self._validate_tdd_sequence(tdd_sequence, issues, warnings)

        for skill_name in call_sequence:
            skill_info = self.registry.get_skill(skill_name)
            if skill_info:
                required_skills = skill_info.get("required_skills", [])
                for req_skill in required_skills:
                    if req_skill not in call_sequence:
                        issues.append(f"技能 {skill_name} 缺少必需的依赖技能 {req_skill}")
                    elif call_sequence.index(skill_name) < call_sequence.index(req_skill):
                        issues.append(f"顺序错误: {skill_name} 在依赖 {req_skill} 之前调用")

        if not issues and not warnings:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="调用顺序正确，符合三省六部架构规范",
                details={
                    "calls_analyzed": len(calls),
                    "provincial_order_validated": True,
                    "tdd_order_validated": len(tdd_calls) > 0
                }
            )
        elif not issues:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"调用顺序存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings, "suggestions": suggestions},
                recommendations=["确保依赖技能先被调用", "遵循TDD开发流程"]
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"调用顺序错误: {'; '.join(issues)}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["调整调用顺序", "确保依赖关系正确", "参考三省六部架构文档"]
            )

    def _validate_sequence_order(self, sequence: list[str], expected_order: list[str],
                                  issues: list[str], order_name: str):
        """验证序列顺序是否符合预期"""
        indices = []
        for skill in expected_order:
            try:
                idx = sequence.index(skill)
                indices.append((skill, idx))
            except ValueError:
                pass

        sorted_indices = sorted(indices, key=lambda x: x[1])
        sorted_skills = [s[0] for s in sorted_indices]

        for i, skill in enumerate(sorted_skills):
            expected_pos = expected_order.index(skill)
            actual_pos = i
            if expected_pos != actual_pos:
                issues.append(f"{order_name}顺序错误: {skill} 位置不正确 (期望第{expected_pos+1}位，实际第{actual_pos+1}位)")

    def _validate_tdd_sequence(self, tdd_sequence: list[str], issues: list[str], warnings: list[str]):
        """验证TDD顺序"""
        tdd_order = self.registry.call_order_rules["tdd_order"]

        bingbu_idx = self._find_skill_index(tdd_sequence, "bingbu")
        gongbu_idx = self._find_skill_index(tdd_sequence, "gongbu")
        xingbu_idx = self._find_skill_index(tdd_sequence, "xingbu")

        if bingbu_idx is not None and gongbu_idx is not None:
            if bingbu_idx > gongbu_idx:
                issues.append("TDD顺序错误: 工部(bingbu)应在兵部(gongbu)之前，先写测试再写代码")

        if gongbu_idx is not None and xingbu_idx is not None:
            if gongbu_idx > xingbu_idx:
                warnings.append("TDD建议: 刑部(xingbu)应在工部(gongbu)之后，先实现代码再重构")

        if bingbu_idx is None and (gongbu_idx is not None or xingbu_idx is not None):
            warnings.append("TDD建议: 缺少兵部(bingbu)测试阶段，建议先编写测试用例")

    def _find_skill_index(self, sequence: list[str], skill_name: str) -> Optional[int]:
        """查找技能在序列中的索引"""
        for i, item in enumerate(sequence):
            if item == skill_name or skill_name in item:
                return i
        return None

    def validate_dependencies(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "ORDER-002"
        check_name = "依赖关系验证"

        issues = []
        warnings = []

        call_map: dict[str, SkillCall] = {c.call_id: c for c in calls}

        for call in calls:
            if call.parent_call_id:
                parent = call_map.get(call.parent_call_id)
                if not parent:
                    issues.append(f"调用 {call.call_id} 引用了不存在的父调用 {call.parent_call_id}")
                elif parent.status != "completed" and call.status != "pending":
                    issues.append(f"调用 {call.call_id} 在父调用未完成时执行 (父调用状态: {parent.status})")

            skill_info = self.registry.get_skill(call.skill_name)
            if skill_info:
                required_skills = skill_info.get("required_skills", [])
                for req_skill in required_skills:
                    req_calls = [c for c in calls if c.skill_name == req_skill]
                    if not req_calls:
                        issues.append(f"技能 {call.skill_name} 缺少必需依赖 {req_skill}")
                    else:
                        req_completed = [c for c in req_calls if c.status == "completed"]
                        if not req_completed:
                            warnings.append(f"技能 {call.skill_name} 的依赖 {req_skill} 未成功完成")

        if not issues and not warnings:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="依赖关系正确",
                details={"calls_with_parents": sum(1 for c in calls if c.parent_call_id)}
            )
        elif not issues:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"依赖关系存在警告: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["确保依赖技能成功完成后再执行"]
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"依赖关系存在问题: {'; '.join(issues)}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["修复依赖关系", "确保父调用完成后再执行子调用"]
            )

    def validate_call_chain_integrity(self, calls: list[SkillCall]) -> CallChainResult:
        """验证调用链完整性"""
        check_id = "ORDER-003"
        check_name = "调用链完整性验证"

        issues = []
        orphan_calls = []
        broken_chains = []

        call_ids = {c.call_id for c in calls}

        for call in calls:
            if call.parent_call_id and call.parent_call_id not in call_ids:
                orphan_calls.append(call.call_id)
                issues.append(f"调用 {call.call_id} 的父调用 {call.parent_call_id} 不存在")

        root_calls = [c for c in calls if not c.parent_call_id]
        if not root_calls and calls:
            issues.append("没有找到根调用，调用链可能存在循环")

        for call in calls:
            if call.status == "failed":
                children = [c for c in calls if c.parent_call_id == call.call_id]
                if children:
                    broken_chains.append({
                        "failed_call": call.call_id,
                        "affected_children": [c.call_id for c in children]
                    })

        if not issues:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="调用链完整",
                details={
                    "total_calls": len(calls),
                    "root_calls": len(root_calls),
                    "orphan_calls": 0
                }
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"调用链完整性问题: {'; '.join(issues[:5])}",
                details={
                    "issues": issues,
                    "orphan_calls": orphan_calls,
                    "broken_chains": broken_chains
                },
                recommendations=["修复断裂的调用链", "检查父调用ID是否正确"]
            )


class CircularCallDetector:
    """循环调用检测器（增强版）"""

    def __init__(self, registry: SkillRegistry = None):
        self.registry = registry or SkillRegistry()
        self.max_depth = 20

    def detect_circular_calls(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "CIRCULAR-001"
        check_name = "循环调用检测"

        circular_chains: list[CircularCallInfo] = []

        call_graph = self._build_call_graph(calls)

        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in call_graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]

                    cycle_type = self._determine_cycle_type(cycle)

                    circular_chains.append(CircularCallInfo(
                        call_chain=cycle,
                        detected_at=datetime.now().isoformat(),
                        depth=len(cycle),
                        affected_skills=list(set(cycle)),
                        cycle_type=cycle_type
                    ))
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in call_graph:
            if node not in visited:
                dfs(node)

        indirect_circular = self._detect_indirect_circular(calls)
        circular_chains.extend(indirect_circular)

        if not circular_chains:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.CRITICAL,
                message="未检测到循环调用",
                details={"nodes_checked": len(call_graph), "edges_checked": sum(len(v) for v in call_graph.values())}
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message=f"检测到 {len(circular_chains)} 个循环调用链",
                details={
                    "circular_count": len(circular_chains),
                    "direct_cycles": sum(1 for c in circular_chains if c.cycle_type == "direct"),
                    "indirect_cycles": sum(1 for c in circular_chains if c.cycle_type == "indirect"),
                    "chains": [
                        {"chain": c.call_chain, "depth": c.depth, "type": c.cycle_type}
                        for c in circular_chains
                    ]
                },
                recommendations=["重构调用链以消除循环", "使用异步回调替代同步调用", "引入中介者模式解耦"]
            )

    def _build_call_graph(self, calls: list[SkillCall]) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = defaultdict(list)

        for call in calls:
            if call.caller and call.skill_name:
                if call.skill_name not in graph[call.caller]:
                    graph[call.caller].append(call.skill_name)

        return dict(graph)

    def _determine_cycle_type(self, cycle: list[str]) -> str:
        """判断循环类型"""
        unique_nodes = set(cycle[:-1])
        if len(unique_nodes) == 1:
            return "self"
        elif len(unique_nodes) == 2:
            return "direct"
        else:
            return "indirect"

    def _detect_indirect_circular(self, calls: list[SkillCall]) -> list[CircularCallInfo]:
        """检测间接循环调用"""
        indirect_cycles = []

        call_map = {c.call_id: c for c in calls}

        for call in calls:
            ancestors = self._get_ancestors(call, call_map, set())

            for ancestor in ancestors:
                if ancestor.skill_name == call.skill_name:
                    cycle_path = self._build_cycle_path(call, ancestor, call_map)
                    if cycle_path:
                        indirect_cycles.append(CircularCallInfo(
                            call_chain=cycle_path,
                            detected_at=datetime.now().isoformat(),
                            depth=len(cycle_path),
                            affected_skills=list(set(cycle_path)),
                            cycle_type="indirect"
                        ))
                    break

        return indirect_cycles

    def _get_ancestors(self, call: SkillCall, call_map: dict[str, SkillCall],
                       visited: set[str], depth: int = 0) -> list[SkillCall]:
        """获取调用的所有祖先调用"""
        if depth > self.max_depth or call.call_id in visited:
            return []

        visited.add(call.call_id)
        ancestors = []

        if call.parent_call_id:
            parent = call_map.get(call.parent_call_id)
            if parent:
                ancestors.append(parent)
                ancestors.extend(self._get_ancestors(parent, call_map, visited, depth + 1))

        return ancestors

    def _build_cycle_path(self, start: SkillCall, end: SkillCall,
                          call_map: dict[str, SkillCall]) -> Optional[list[str]]:
        """构建循环路径"""
        path = [start.skill_name]
        current = start

        while current.parent_call_id:
            parent = call_map.get(current.parent_call_id)
            if not parent:
                break
            path.append(parent.skill_name)
            if parent.call_id == end.call_id:
                path.append(start.skill_name)
                return path
            current = parent

        return None

    def detect_self_calls(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "CIRCULAR-002"
        check_name = "自调用检测"

        self_calls = []

        for call in calls:
            if call.caller == call.skill_name:
                self_calls.append(call)

        if not self_calls:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="未检测到自调用",
                details={"calls_analyzed": len(calls)}
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"检测到 {len(self_calls)} 个自调用",
                details={"self_calls": [c.call_id for c in self_calls]},
                recommendations=["检查自调用是否必要", "考虑重构以避免自调用", "使用迭代替代递归"]
            )

    def detect_mutual_calls(self, calls: list[SkillCall]) -> CallChainResult:
        """检测相互调用"""
        check_id = "CIRCULAR-003"
        check_name = "相互调用检测"

        mutual_pairs = []
        call_pairs = defaultdict(int)

        for call in calls:
            if call.caller and call.skill_name:
                call_pairs[(call.caller, call.skill_name)] += 1

        for (caller, callee), count in call_pairs.items():
            reverse_count = call_pairs.get((callee, caller), 0)
            if reverse_count > 0:
                mutual_pairs.append({
                    "skills": [caller, callee],
                    "forward_count": count,
                    "reverse_count": reverse_count
                })

        if not mutual_pairs:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="未检测到相互调用",
                details={"calls_analyzed": len(calls)}
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"检测到 {len(mutual_pairs)} 对相互调用",
                details={"mutual_pairs": mutual_pairs},
                recommendations=["检查相互调用是否必要", "考虑引入事件驱动架构"]
            )


class InvalidCallIdentifier:
    """无效调用识别器（增强版）"""

    def __init__(self, registry: SkillRegistry = None):
        self.registry = registry or SkillRegistry()

    def identify_invalid_calls(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "INVALID-001"
        check_name = "无效调用识别"

        invalid_calls: list[InvalidCallInfo] = []

        for call in calls:
            if not self.registry.is_valid_skill(call.skill_name):
                if self.registry.is_deprecated(call.skill_name):
                    dep_info = self.registry.get_deprecated_info(call.skill_name)
                    invalid_calls.append(InvalidCallInfo(
                        call_id=call.call_id,
                        skill_name=call.skill_name,
                        reason=f"已弃用的技能 (自 {dep_info['deprecated_since']} 起)",
                        suggestion=f"请使用 {dep_info['replacement']} 替代",
                        severity=CheckSeverity.MEDIUM
                    ))
                else:
                    invalid_calls.append(InvalidCallInfo(
                        call_id=call.call_id,
                        skill_name=call.skill_name,
                        reason="未知技能",
                        suggestion="请检查技能名称是否正确，参考技能注册表",
                        severity=CheckSeverity.HIGH
                    ))

        if not invalid_calls:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="所有调用均有效",
                details={"calls_checked": len(calls)}
            )
        else:
            deprecated_count = sum(1 for c in invalid_calls if "弃用" in c.reason)
            unknown_count = len(invalid_calls) - deprecated_count

            status = CheckStatus.FAIL if unknown_count > 0 else CheckStatus.WARNING

            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=status,
                severity=CheckSeverity.HIGH if unknown_count > 0 else CheckSeverity.MEDIUM,
                message=f"检测到 {len(invalid_calls)} 个无效调用 (未知: {unknown_count}, 弃用: {deprecated_count})",
                details={
                    "invalid_calls": [
                        {"call_id": c.call_id, "skill": c.skill_name, "reason": c.reason, "severity": c.severity.value}
                        for c in invalid_calls
                    ]
                },
                recommendations=[c.suggestion for c in invalid_calls[:5]]
            )

    def check_missing_params(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "INVALID-002"
        check_name = "缺失参数检查"

        issues = []

        for call in calls:
            skill = call.skill_name
            required_params = self.registry.get_required_params(skill)

            if required_params:
                input_data = call.input_data or {}

                for param in required_params:
                    if param not in input_data:
                        issues.append({
                            "call_id": call.call_id,
                            "skill": skill,
                            "missing_param": param,
                            "severity": "high"
                        })
                    elif input_data[param] is None or input_data[param] == "":
                        issues.append({
                            "call_id": call.call_id,
                            "skill": skill,
                            "missing_param": param,
                            "severity": "medium",
                            "reason": "参数值为空"
                        })

        if not issues:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="所有必需参数均已提供",
                details={"calls_checked": len(calls)}
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"检测到 {len(issues)} 个缺失参数的调用",
                details={"issues": issues},
                recommendations=["补充缺失的参数", "检查参数传递逻辑"]
            )

    def check_failed_calls(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "INVALID-003"
        check_name = "失败调用检查"

        failed_calls = [c for c in calls if c.status == "failed" or c.error]

        if not failed_calls:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="所有调用均成功",
                details={"calls_checked": len(calls)}
            )
        else:
            error_summary: dict[str, int] = defaultdict(int)
            for call in failed_calls:
                error_type = call.error or "unknown"
                error_summary[error_type] += 1

            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"检测到 {len(failed_calls)} 个失败调用",
                details={
                    "failed_count": len(failed_calls),
                    "error_summary": dict(error_summary),
                    "failed_calls": [
                        {"call_id": c.call_id, "skill": c.skill_name, "error": c.error, "retry_count": c.retry_count}
                        for c in failed_calls[:10]
                    ]
                },
                recommendations=["分析失败原因", "重试失败的调用", "检查错误日志", "增加重试机制"]
            )

    def check_timeout_calls(self, calls: list[SkillCall]) -> CallChainResult:
        """检查超时调用"""
        check_id = "INVALID-004"
        check_name = "超时调用检查"

        timeout_calls = []

        for call in calls:
            skill_info = self.registry.get_skill(call.skill_name)
            if skill_info:
                timeout = skill_info.get("timeout", 60)
                if call.duration > timeout:
                    timeout_calls.append({
                        "call_id": call.call_id,
                        "skill": call.skill_name,
                        "duration": call.duration,
                        "timeout": timeout,
                        "exceeded_by": call.duration - timeout
                    })

        if not timeout_calls:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="无超时调用",
                details={"calls_checked": len(calls)}
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"检测到 {len(timeout_calls)} 个超时调用",
                details={"timeout_calls": timeout_calls},
                recommendations=["优化调用性能", "增加超时时间", "检查是否存在阻塞操作"]
            )

    def check_retry_exceeded(self, calls: list[SkillCall]) -> CallChainResult:
        """检查重试次数超限"""
        check_id = "INVALID-005"
        check_name = "重试次数检查"

        retry_exceeded = []

        for call in calls:
            skill_info = self.registry.get_skill(call.skill_name)
            if skill_info:
                retry_limit = skill_info.get("retry_limit", 3)
                if call.retry_count > retry_limit:
                    retry_exceeded.append({
                        "call_id": call.call_id,
                        "skill": call.skill_name,
                        "retry_count": call.retry_count,
                        "limit": retry_limit
                    })

        if not retry_exceeded:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="重试次数正常",
                details={"calls_checked": len(calls)}
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"检测到 {len(retry_exceeded)} 个重试次数超限的调用",
                details={"retry_exceeded": retry_exceeded},
                recommendations=["检查调用失败原因", "调整重试策略", "增加熔断机制"]
            )


class CallDepthAnalyzer:
    """调用深度分析器"""

    def __init__(self, registry: SkillRegistry = None, max_recommended_depth: int = 10, max_allowed_depth: int = 20):
        self.registry = registry or SkillRegistry()
        self.max_recommended_depth = max_recommended_depth
        self.max_allowed_depth = max_allowed_depth

    def analyze_depth(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "DEPTH-001"
        check_name = "调用深度分析"

        call_map: dict[str, SkillCall] = {c.call_id: c for c in calls}
        depth_map: dict[str, int] = {}

        def get_depth(call_id: str) -> int:
            if call_id in depth_map:
                return depth_map[call_id]

            call = call_map.get(call_id)
            if not call or not call.parent_call_id:
                depth_map[call_id] = 1
                return 1

            parent_depth = get_depth(call.parent_call_id)
            depth = parent_depth + 1
            depth_map[call_id] = depth
            return depth

        for call in calls:
            get_depth(call.call_id)

        max_depth = max(depth_map.values()) if depth_map else 0
        avg_depth = sum(depth_map.values()) / len(depth_map) if depth_map else 0

        deep_calls = [
            {"call_id": cid, "depth": d}
            for cid, d in depth_map.items()
            if d > self.max_recommended_depth
        ]

        skill_depth_violations = self._check_skill_depth_limits(calls, depth_map, call_map)

        if max_depth <= self.max_recommended_depth and not skill_depth_violations:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message=f"调用深度正常，最大深度: {max_depth}",
                details={
                    "max_depth": max_depth,
                    "avg_depth": round(avg_depth, 2),
                    "calls_analyzed": len(calls)
                }
            )
        elif max_depth <= self.max_allowed_depth:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"调用深度较高，最大深度: {max_depth} (建议 <= {self.max_recommended_depth})",
                details={
                    "max_depth": max_depth,
                    "avg_depth": round(avg_depth, 2),
                    "deep_calls": deep_calls[:10],
                    "skill_violations": skill_depth_violations
                },
                recommendations=["考虑扁平化调用链", "减少嵌套调用层级"]
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"调用深度过深，最大深度: {max_depth} (限制 {self.max_allowed_depth})",
                details={
                    "max_depth": max_depth,
                    "avg_depth": round(avg_depth, 2),
                    "deep_calls": deep_calls,
                    "skill_violations": skill_depth_violations
                },
                recommendations=["重构以减少调用深度", "拆分复杂调用链"]
            )

    def _check_skill_depth_limits(self, calls: list[SkillCall], depth_map: dict[str, int],
                                   call_map: dict[str, SkillCall]) -> list[dict]:
        """检查各技能的调用深度是否超过限制"""
        violations = []

        for call in calls:
            skill_info = self.registry.get_skill(call.skill_name)
            if skill_info:
                max_allowed = skill_info.get("max_call_depth", 10)
                actual_depth = depth_map.get(call.call_id, 0)
                if actual_depth > max_allowed:
                    violations.append({
                        "call_id": call.call_id,
                        "skill": call.skill_name,
                        "actual_depth": actual_depth,
                        "max_allowed": max_allowed
                    })

        return violations

    def analyze_breadth(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "DEPTH-002"
        check_name = "调用广度分析"
        
        children_count: dict[str, int] = defaultdict(int)
        
        for call in calls:
            if call.parent_call_id:
                children_count[call.parent_call_id] += 1
        
        if not children_count:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                message="无并行调用",
                details={"calls_analyzed": len(calls)}
            )
        
        max_breadth = max(children_count.values())
        avg_breadth = sum(children_count.values()) / len(children_count)
        
        wide_calls = [
            {"parent_id": pid, "children_count": c}
            for pid, c in children_count.items()
            if c > 5
        ]
        
        if max_breadth <= 5:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                message=f"调用广度正常，最大广度: {max_breadth}",
                details={
                    "max_breadth": max_breadth,
                    "avg_breadth": round(avg_breadth, 2)
                }
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"调用广度较大，最大广度: {max_breadth}",
                details={
                    "max_breadth": max_breadth,
                    "avg_breadth": round(avg_breadth, 2),
                    "wide_calls": wide_calls
                },
                recommendations=["考虑串行化部分调用", "优化并行调用数量"]
            )


class CallPerformanceAnalyzer:
    """调用性能分析器"""

    def __init__(self, slow_call_threshold: float = 5.0):
        self.slow_call_threshold = slow_call_threshold

    def analyze_performance(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "PERF-001"
        check_name = "调用性能分析"
        
        durations = [c.duration for c in calls if c.duration > 0]
        
        if not durations:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.SKIP,
                severity=CheckSeverity.LOW,
                message="无性能数据",
                details={"calls_analyzed": len(calls)}
            )
        
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        
        slow_calls = [
            {"call_id": c.call_id, "skill": c.skill_name, "duration": c.duration}
            for c in calls
            if c.duration > self.slow_call_threshold
        ]
        
        if not slow_calls:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message=f"调用性能良好，平均耗时: {avg_duration:.2f}s",
                details={
                    "avg_duration": round(avg_duration, 2),
                    "max_duration": round(max_duration, 2),
                    "min_duration": round(min_duration, 2)
                }
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"存在 {len(slow_calls)} 个慢调用 (>{self.slow_call_threshold}s)",
                details={
                    "avg_duration": round(avg_duration, 2),
                    "max_duration": round(max_duration, 2),
                    "slow_calls": slow_calls[:10]
                },
                recommendations=["优化慢调用", "考虑缓存或异步处理"]
            )

    def analyze_timeout_risk(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "PERF-002"
        check_name = "超时风险分析"
        
        timeout_threshold = 30.0
        risk_calls = []
        
        for call in calls:
            if call.duration > timeout_threshold * 0.8:
                risk_calls.append({
                    "call_id": call.call_id,
                    "skill": call.skill_name,
                    "duration": call.duration,
                    "risk_level": "high" if call.duration > timeout_threshold else "medium"
                })
        
        if not risk_calls:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="无超时风险",
                details={"calls_analyzed": len(calls)}
            )
        else:
            high_risk = [c for c in risk_calls if c["risk_level"] == "high"]
            status = CheckStatus.FAIL if high_risk else CheckStatus.WARNING
            
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=status,
                severity=CheckSeverity.HIGH if high_risk else CheckSeverity.MEDIUM,
                message=f"检测到 {len(risk_calls)} 个超时风险调用",
                details={"risk_calls": risk_calls},
                recommendations=["增加超时时间", "优化调用逻辑", "添加重试机制"]
            )


class SkillCallChainChecker:
    """技能调用链检查器主类"""

    def __init__(self, output_dir: Path = None):
        if output_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                self.output_dir = _path_mgr.get_output_path(OutputType.REPORT, subdirectory="skill_call_chain")
            except Exception:
                self.output_dir = get_path_config().REPORTS_DIR / "skill_call_chain"
        else:
            self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.registry = SkillRegistry()
        self.order_validator = CallOrderValidator(self.registry)
        self.circular_detector = CircularCallDetector(self.registry)
        self.invalid_identifier = InvalidCallIdentifier(self.registry)
        self.depth_analyzer = CallDepthAnalyzer(self.registry)
        self.performance_analyzer = CallPerformanceAnalyzer()

    def check_all(self, calls: list[SkillCall]) -> SkillCallChainReport:
        all_results: list[CallChainResult] = []

        all_results.append(self.order_validator.validate_order(calls))
        all_results.append(self.order_validator.validate_dependencies(calls))
        all_results.append(self.order_validator.validate_call_chain_integrity(calls))
        all_results.append(self.circular_detector.detect_circular_calls(calls))
        all_results.append(self.circular_detector.detect_self_calls(calls))
        all_results.append(self.circular_detector.detect_mutual_calls(calls))
        all_results.append(self.invalid_identifier.identify_invalid_calls(calls))
        all_results.append(self.invalid_identifier.check_missing_params(calls))
        all_results.append(self.invalid_identifier.check_failed_calls(calls))
        all_results.append(self.invalid_identifier.check_timeout_calls(calls))
        all_results.append(self.invalid_identifier.check_retry_exceeded(calls))
        all_results.append(self.depth_analyzer.analyze_depth(calls))
        all_results.append(self.depth_analyzer.analyze_breadth(calls))
        all_results.append(self.performance_analyzer.analyze_performance(calls))
        all_results.append(self.performance_analyzer.analyze_timeout_risk(calls))
        
        passed = sum(1 for r in all_results if r.status == CheckStatus.PASS)
        failed = sum(1 for r in all_results if r.status == CheckStatus.FAIL)
        warnings = sum(1 for r in all_results if r.status == CheckStatus.WARNING)
        skipped = sum(1 for r in all_results if r.status == CheckStatus.SKIP)
        
        if failed > 0:
            overall_status = CheckStatus.FAIL
        elif warnings > 0:
            overall_status = CheckStatus.WARNING
        else:
            overall_status = CheckStatus.PASS
        
        circular_detected = self._extract_circular_info(all_results)
        invalid_detected = self._extract_invalid_info(all_results)
        call_graph = self._build_call_graph(calls)
        
        valid_calls = sum(1 for c in calls if c.status == "completed")
        invalid_calls = sum(1 for c in calls if c.status == "failed")
        
        durations = [c.duration for c in calls if c.duration > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        depth_map = self._calculate_depths(calls)
        max_depth = max(depth_map.values()) if depth_map else 0
        
        summary = self._generate_summary(all_results, calls)
        
        report = SkillCallChainReport(
            report_id=f"SCC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            total_calls=len(calls),
            valid_calls=valid_calls,
            invalid_calls=invalid_calls,
            circular_calls=len(circular_detected),
            max_depth=max_depth,
            avg_duration=avg_duration,
            results=all_results,
            circular_detected=circular_detected,
            invalid_detected=invalid_detected,
            call_graph=call_graph,
            summary=summary,
            overall_status=overall_status
        )
        
        return report

    def _extract_circular_info(self, results: list[CallChainResult]) -> list[CircularCallInfo]:
        for result in results:
            if result.check_id == "CIRCULAR-001" and result.status == CheckStatus.FAIL:
                chains = result.details.get("chains", [])
                return [
                    CircularCallInfo(
                        call_chain=c["chain"],
                        detected_at=datetime.now().isoformat(),
                        depth=c["depth"],
                        affected_skills=list(set(c["chain"])),
                        cycle_type=c.get("type", "direct")
                    )
                    for c in chains
                ]
        return []

    def _extract_invalid_info(self, results: list[CallChainResult]) -> list[InvalidCallInfo]:
        for result in results:
            if result.check_id == "INVALID-001":
                invalid_calls = result.details.get("invalid_calls", [])
                return [
                    InvalidCallInfo(
                        call_id=c["call_id"],
                        skill_name=c["skill"],
                        reason=c["reason"],
                        suggestion=""
                    )
                    for c in invalid_calls
                ]
        return []

    def _build_call_graph(self, calls: list[SkillCall]) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = defaultdict(list)
        
        for call in calls:
            if call.caller and call.skill_name:
                if call.skill_name not in graph[call.caller]:
                    graph[call.caller].append(call.skill_name)
        
        return dict(graph)

    def _calculate_depths(self, calls: list[SkillCall]) -> dict[str, int]:
        call_map: dict[str, SkillCall] = {c.call_id: c for c in calls}
        depth_map: dict[str, int] = {}
        
        def get_depth(call_id: str) -> int:
            if call_id in depth_map:
                return depth_map[call_id]
            
            call = call_map.get(call_id)
            if not call or not call.parent_call_id:
                depth_map[call_id] = 1
                return 1
            
            parent_depth = get_depth(call.parent_call_id)
            depth = parent_depth + 1
            depth_map[call_id] = depth
            return depth
        
        for call in calls:
            get_depth(call.call_id)
        
        return depth_map

    def _generate_summary(self, results: list[CallChainResult], calls: list[SkillCall]) -> dict[str, Any]:
        critical_issues = [
            {"check_id": r.check_id, "message": r.message}
            for r in results
            if r.status == CheckStatus.FAIL and r.severity == CheckSeverity.CRITICAL
        ]
        
        all_recommendations = []
        for result in results:
            all_recommendations.extend(result.recommendations)
        
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        
        skill_call_counts: dict[str, int] = defaultdict(int)
        for call in calls:
            skill_call_counts[call.skill_name] += 1
        
        return {
            "critical_issues": critical_issues,
            "recommendations": unique_recommendations[:10],
            "skill_call_counts": dict(skill_call_counts),
            "total_calls": len(calls)
        }

    def save_report(self, report: SkillCallChainReport, output_path: Path = None) -> Path:
        output_path = output_path or self.output_dir / f"skill_call_chain_report_{report.report_id}.json"
        
        report_dict = {
            "report_id": report.report_id,
            "generated_at": report.generated_at,
            "total_calls": report.total_calls,
            "valid_calls": report.valid_calls,
            "invalid_calls": report.invalid_calls,
            "circular_calls": report.circular_calls,
            "max_depth": report.max_depth,
            "avg_duration": report.avg_duration,
            "overall_status": report.overall_status.value,
            "results": [
                {
                    "check_id": r.check_id,
                    "check_name": r.check_name,
                    "status": r.status.value,
                    "severity": r.severity.value,
                    "message": r.message,
                    "details": r.details,
                    "recommendations": r.recommendations,
                    "timestamp": r.timestamp
                }
                for r in report.results
            ],
            "circular_detected": [
                {
                    "call_chain": c.call_chain,
                    "depth": c.depth,
                    "affected_skills": c.affected_skills,
                    "cycle_type": c.cycle_type
                }
                for c in report.circular_detected
            ],
            "invalid_detected": [
                {
                    "call_id": i.call_id,
                    "skill_name": i.skill_name,
                    "reason": i.reason
                }
                for i in report.invalid_detected
            ],
            "call_graph": report.call_graph,
            "summary": report.summary
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"报告已保存: {output_path}")
        return output_path

    def print_report(self, report: SkillCallChainReport):
        print("\n" + "=" * 70)
        print("技能调用链检查报告")
        print("=" * 70)
        print(f"报告ID: {report.report_id}")
        print(f"生成时间: {report.generated_at}")
        print(f"总体状态: {report.overall_status.value.upper()}")
        print(f"\n调用统计:")
        print(f"  总调用数: {report.total_calls}")
        print(f"  有效调用: {report.valid_calls}")
        print(f"  无效调用: {report.invalid_calls}")
        print(f"  循环调用: {report.circular_calls}")
        print(f"  最大深度: {report.max_depth}")
        print(f"  平均耗时: {report.avg_duration:.2f}s")
        
        print("\n" + "-" * 70)
        print("检查结果:")
        
        for result in report.results:
            status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠" if result.status == CheckStatus.WARNING else "○"
            print(f"  [{status_symbol}] {result.check_name}: {result.message}")
        
        if report.circular_detected:
            print("\n" + "-" * 70)
            print("循环调用链:")
            for circular in report.circular_detected:
                print(f"  - {' → '.join(circular.call_chain)} (深度: {circular.depth}, 类型: {circular.cycle_type})")
        
        if report.invalid_detected:
            print("\n" + "-" * 70)
            print("无效调用:")
            for invalid in report.invalid_detected[:10]:
                print(f"  - [{invalid.call_id}] {invalid.skill_name}: {invalid.reason}")
        
        if report.summary.get("critical_issues"):
            print("\n" + "-" * 70)
            print("严重问题:")
            for issue in report.summary["critical_issues"]:
                print(f"  - [{issue['check_id']}] {issue['message']}")
        
        if report.summary.get("recommendations"):
            print("\n" + "-" * 70)
            print("改进建议:")
            for rec in report.summary["recommendations"][:5]:
                print(f"  - {rec}")
        
        print("\n" + "=" * 70)


def load_sample_calls() -> list[SkillCall]:
    """加载示例调用数据"""
    return [
        SkillCall(
            call_id="call-001",
            skill_name="sanliu",
            caller="user",
            callee="zhongshusheng",
            timestamp=datetime.now().isoformat(),
            status="completed",
            duration=1.5,
            parent_call_id=None
        ),
        SkillCall(
            call_id="call-002",
            skill_name="zhongshusheng",
            caller="sanliu",
            callee="requirement_analysis",
            timestamp=datetime.now().isoformat(),
            status="completed",
            duration=2.0,
            parent_call_id="call-001"
        ),
        SkillCall(
            call_id="call-003",
            skill_name="menxiasheng",
            caller="sanliu",
            callee="review",
            timestamp=datetime.now().isoformat(),
            status="completed",
            duration=1.0,
            parent_call_id="call-001"
        ),
        SkillCall(
            call_id="call-004",
            skill_name="shangshusheng",
            caller="sanliu",
            callee="libu",
            timestamp=datetime.now().isoformat(),
            status="completed",
            duration=0.5,
            parent_call_id="call-001"
        ),
        SkillCall(
            call_id="call-005",
            skill_name="bingbu",
            caller="shangshusheng",
            callee="test_generator",
            timestamp=datetime.now().isoformat(),
            status="completed",
            duration=3.0,
            parent_call_id="call-004"
        ),
        SkillCall(
            call_id="call-006",
            skill_name="gongbu",
            caller="shangshusheng",
            callee="code_generator",
            timestamp=datetime.now().isoformat(),
            status="completed",
            duration=4.0,
            parent_call_id="call-004"
        ),
        SkillCall(
            call_id="call-007",
            skill_name="xingbu",
            caller="shangshusheng",
            callee="refactor",
            timestamp=datetime.now().isoformat(),
            status="completed",
            duration=2.5,
            parent_call_id="call-004"
        ),
        SkillCall(
            call_id="call-008",
            skill_name="skill-creator",
            caller="sanliu",
            callee=None,
            timestamp=datetime.now().isoformat(),
            status="completed",
            duration=1.0,
            parent_call_id="call-001",
            input_data={"name": "test-skill"}
        )
    ]


def main():
    parser = argparse.ArgumentParser(description="技能调用链检查器")
    
    parser.add_argument("--check-all", action="store_true", help="执行所有检查")
    parser.add_argument("--check-order", action="store_true", help="检查调用顺序")
    parser.add_argument("--check-circular", action="store_true", help="检测循环调用")
    parser.add_argument("--check-invalid", action="store_true", help="识别无效调用")
    parser.add_argument("--analyze-depth", action="store_true", help="分析调用深度")
    parser.add_argument("--analyze-performance", action="store_true", help="分析调用性能")
    parser.add_argument("--data-file", type=Path, help="数据文件路径(JSON)")
    parser.add_argument("--output", type=Path, help="报告输出路径")
    parser.add_argument("--sample", action="store_true", help="使用示例数据")
    
    args = parser.parse_args()
    
    if args.data_file:
        try:
            with open(args.data_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            calls = [
                SkillCall(
                    call_id=item.get("call_id", ""),
                    skill_name=item.get("skill_name", ""),
                    caller=item.get("caller"),
                    callee=item.get("callee"),
                    timestamp=item.get("timestamp", datetime.now().isoformat()),
                    status=item.get("status", "unknown"),
                    duration=item.get("duration", 0.0),
                    parent_call_id=item.get("parent_call_id"),
                    input_data=item.get("input_data", {}),
                    output_data=item.get("output_data", {}),
                    error=item.get("error"),
                    call_type=CallType(item.get("call_type", "sync")),
                    retry_count=item.get("retry_count", 0),
                    priority=item.get("priority", 0),
                    tags=item.get("tags", [])
                )
                for item in raw_data
            ]
        except Exception as e:
            logger.error(f"加载数据文件失败: {e}")
            sys.exit(1)
    elif args.sample:
        calls = load_sample_calls()
    else:
        calls = load_sample_calls()
    
    checker = SkillCallChainChecker()
    
    specific_checks = [
        args.check_order, args.check_circular, args.check_invalid,
        args.analyze_depth, args.analyze_performance
    ]
    
    if args.check_all or not any(specific_checks):
        report = checker.check_all(calls)
        checker.print_report(report)
        
        if args.output:
            checker.save_report(report, args.output)
        else:
            checker.save_report(report)
    
    elif args.check_order:
        validator = CallOrderValidator()
        result = validator.validate_order(calls)
        status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
        print(f"\n[{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.check_circular:
        detector = CircularCallDetector()
        result = detector.detect_circular_calls(calls)
        status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
        print(f"\n[{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.check_invalid:
        identifier = InvalidCallIdentifier()
        result = identifier.identify_invalid_calls(calls)
        status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
        print(f"\n[{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.analyze_depth:
        analyzer = CallDepthAnalyzer()
        result = analyzer.analyze_depth(calls)
        status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
        print(f"\n[{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.analyze_performance:
        analyzer = CallPerformanceAnalyzer()
        result = analyzer.analyze_performance(calls)
        status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
        print(f"\n[{status_symbol}] {result.check_name}: {result.message}")


if __name__ == "__main__":
    main()
