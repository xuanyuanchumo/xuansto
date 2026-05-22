#!/usr/bin/env python3
"""
技能调用链检查器（增强版） - Sanliu 技能

功能增强：
- 调用顺序验证增强
- 循环调用检测增强
- 无效调用识别增强
- 调用深度分析增强
- 调用性能分析增强
- 调用依赖图分析
- 调用链可视化支持

使用方法：
    python scripts/analysis/skill_call_chain_checker.py --check-all
    python scripts/analysis/skill_call_chain_checker.py --check-order
    python scripts/analysis/skill_call_chain_checker.py --check-circular
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
        logging.FileHandler('skill_call_chain_checker_enhanced.log', encoding='utf-8')
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


@dataclass
class SkillCall:
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
    retry_count: int = 0
    priority: str = "normal"


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
    call_chain: list[str]
    detected_at: str
    depth: int
    affected_skills: list[str]
    severity: str = "critical"


@dataclass
class InvalidCallInfo:
    call_id: str
    skill_name: str
    reason: str
    suggestion: str
    severity: str = "high"


@dataclass
class CallDependencyNode:
    node_id: str
    skill_name: str
    dependencies: list[str]
    dependents: list[str]
    depth: int
    is_entry: bool = False
    is_exit: bool = False


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
    dependency_nodes: list[CallDependencyNode]
    summary: dict[str, Any]
    overall_status: CheckStatus


class EnhancedCallOrderValidator:
    """调用顺序验证器（增强版）"""

    def __init__(self):
        self.expected_order = {
            "sanliu": ["zhongshusheng", "menxiasheng", "shangshusheng"],
            "zhongshusheng": ["requirement_analysis", "architecture_design", "sdd_specification"],
            "menxiasheng": ["review", "quality_gate"],
            "shangshusheng": ["libu", "hubu", "liibu", "bingbu", "xingbu", "gongbu"],
        }
        
        self.tdd_order = ["bingbu", "gongbu", "xingbu"]
        
        self.dependencies = {
            "menxiasheng": ["zhongshusheng"],
            "shangshusheng": ["menxiasheng"],
            "gongbu": ["bingbu"],
            "xingbu": ["gongbu"],
        }
        
        self.strict_dependencies = {
            "bingbu": {"requires": ["sdd_specification"], "phase": "red"},
            "gongbu": {"requires": ["test_cases"], "phase": "green"},
            "xingbu": {"requires": ["implementation"], "phase": "blue"},
        }

    def validate_order(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "ORDER-E001"
        check_name = "调用顺序验证（增强）"
        
        issues = []
        warnings = []
        
        call_sequence = [c.skill_name for c in calls]
        
        for skill, expected_deps in self.dependencies.items():
            skill_index = self._find_first_index(call_sequence, skill)
            if skill_index == -1:
                continue
            
            for dep in expected_deps:
                dep_index = self._find_first_index(call_sequence, dep)
                if dep_index == -1:
                    warnings.append(f"依赖技能 {dep} 未被调用，但 {skill} 已调用")
                elif dep_index > skill_index:
                    issues.append(f"顺序错误: {skill} 在 {dep} 之前调用")
        
        tdd_calls = [c for c in calls if c.skill_name in self.tdd_order]
        if tdd_calls:
            tdd_sequence = [c.skill_name for c in tdd_calls]
            expected_tdd = [s for s in self.tdd_order if s in tdd_sequence]
            
            for i, skill in enumerate(tdd_sequence):
                expected_index = expected_tdd.index(skill) if skill in expected_tdd else -1
                if expected_index > i:
                    issues.append(f"TDD顺序错误: {skill} 提前执行")
        
        for skill, req_config in self.strict_dependencies.items():
            skill_calls = [c for c in calls if c.skill_name == skill]
            if skill_calls:
                for call in skill_calls:
                    required = req_config["requires"]
                    for req in required:
                        req_calls = [c for c in calls if req in c.skill_name or req in str(c.output_data)]
                        if not req_calls:
                            warnings.append(f"{skill} 调用缺少必要输入: {req}")
        
        if not issues and not warnings:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="调用顺序正确",
                details={"calls_analyzed": len(calls), "sequence_validated": True}
            )
        elif not issues:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"调用顺序存在建议: {'; '.join(warnings[:3])}",
                details={"warnings": warnings},
                recommendations=["确保依赖技能先被调用", "检查TDD顺序"]
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"调用顺序错误: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["调整调用顺序", "确保依赖关系正确"]
            )

    def _find_first_index(self, sequence: list[str], target: str) -> int:
        for i, item in enumerate(sequence):
            if item == target or target in item:
                return i
        return -1

    def validate_dependencies(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "ORDER-E002"
        check_name = "依赖关系验证（增强）"
        
        issues = []
        warnings = []
        
        call_map: dict[str, SkillCall] = {c.call_id: c for c in calls}
        
        for call in calls:
            if call.parent_call_id:
                parent = call_map.get(call.parent_call_id)
                if not parent:
                    issues.append(f"调用 {call.call_id} 引用了不存在的父调用 {call.parent_call_id}")
                elif parent.status != "completed" and call.status != "pending":
                    issues.append(f"调用 {call.call_id} 在父调用未完成时执行")
                
                if parent.skill_name == call.skill_name:
                    warnings.append(f"调用 {call.call_id} 与父调用技能相同: {call.skill_name}")
        
        orphan_calls = [c for c in calls if not c.parent_call_id and c.caller not in ["user", "system"]]
        if orphan_calls:
            warnings.append(f"存在无父调用的非入口调用: {len(orphan_calls)} 个")
        
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
                message=f"依赖关系存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["检查调用依赖关系"]
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"依赖关系存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["修复依赖关系", "确保父调用完成后再执行子调用"]
            )

    def validate_timing(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "ORDER-E003"
        check_name = "调用时序验证"
        
        issues = []
        warnings = []
        
        sorted_calls = sorted(calls, key=lambda c: c.timestamp)
        
        for i in range(len(sorted_calls) - 1):
            current = sorted_calls[i]
            next_call = sorted_calls[i + 1]
            
            if current.skill_name in self.dependencies:
                deps = self.dependencies[current.skill_name]
                if next_call.skill_name not in deps and next_call.skill_name != current.skill_name:
                    for dep in deps:
                        dep_call = next((c for c in sorted_calls[:i+1] if c.skill_name == dep), None)
                        if not dep_call:
                            warnings.append(f"时序问题: {current.skill_name} 调用时 {dep} 尚未调用")
        
        parallel_calls = defaultdict(list)
        for call in calls:
            if call.parent_call_id:
                parallel_calls[call.parent_call_id].append(call)
        
        for parent_id, children in parallel_calls.items():
            if len(children) > 3:
                warnings.append(f"调用 {parent_id} 有过多并行子调用: {len(children)} 个")
        
        if not issues and not warnings:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="调用时序正确",
                details={"calls_analyzed": len(calls)}
            )
        elif not issues:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"调用时序存在建议: {'; '.join(warnings[:3])}",
                details={"warnings": warnings},
                recommendations=["优化调用时序"]
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"调用时序存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["修正调用时序"]
            )


class EnhancedCircularCallDetector:
    """循环调用检测器（增强版）"""

    def __init__(self):
        self.max_depth = 20
        self.max_chain_length = 50

    def detect_circular_calls(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "CIRCULAR-E001"
        check_name = "循环调用检测（增强）"
        
        circular_chains: list[CircularCallInfo] = []
        
        call_graph = self._build_call_graph(calls)
        
        all_cycles = self._find_all_cycles(call_graph)
        
        for cycle in all_cycles:
            circular_chains.append(CircularCallInfo(
                call_chain=cycle,
                detected_at=datetime.now().isoformat(),
                depth=len(cycle),
                affected_skills=list(set(cycle)),
                severity="critical" if len(cycle) <= 3 else "high"
            ))
        
        if not circular_chains:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.CRITICAL,
                message="未检测到循环调用",
                details={"nodes_checked": len(call_graph)}
            )
        else:
            critical_count = sum(1 for c in circular_chains if c.severity == "critical")
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message=f"检测到 {len(circular_chains)} 个循环调用链 (严重: {critical_count})",
                details={
                    "circular_count": len(circular_chains),
                    "chains": [
                        {"chain": c.call_chain, "depth": c.depth, "severity": c.severity}
                        for c in circular_chains
                    ]
                },
                recommendations=["重构调用链以消除循环", "使用异步回调替代同步调用", "引入中介者模式"]
            )

    def _build_call_graph(self, calls: list[SkillCall]) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = defaultdict(list)
        
        for call in calls:
            if call.caller and call.skill_name:
                if call.skill_name not in graph[call.caller]:
                    graph[call.caller].append(call.skill_name)
            
            if call.parent_call_id:
                parent_call = next((c for c in calls if c.call_id == call.parent_call_id), None)
                if parent_call:
                    if call.skill_name not in graph[parent_call.skill_name]:
                        graph[parent_call.skill_name].append(call.skill_name)
        
        return dict(graph)

    def _find_all_cycles(self, graph: dict[str, list[str]]) -> list[list[str]]:
        all_cycles = []
        
        def dfs(node: str, path: list[str], visited: set[str]):
            if node in path:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                all_cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path.copy(), visited)
        
        for start_node in graph:
            dfs(start_node, [], set())
        
        unique_cycles = []
        seen = set()
        for cycle in all_cycles:
            cycle_key = tuple(sorted(cycle[:-1]))
            if cycle_key not in seen:
                seen.add(cycle_key)
                unique_cycles.append(cycle)
        
        return unique_cycles

    def detect_self_calls(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "CIRCULAR-E002"
        check_name = "自调用检测（增强）"
        
        self_calls = []
        
        for call in calls:
            if call.caller == call.skill_name:
                self_calls.append(call)
            
            if call.parent_call_id:
                parent_call = next((c for c in calls if c.call_id == call.parent_call_id), None)
                if parent_call and parent_call.skill_name == call.skill_name:
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
            recursive_calls = []
            for call in self_calls:
                if call.retry_count > 0:
                    recursive_calls.append(call)
            
            if recursive_calls:
                return CallChainResult(
                    check_id=check_id,
                    check_name=check_name,
                    status=CheckStatus.FAIL,
                    severity=CheckSeverity.HIGH,
                    message=f"检测到递归调用: {len(recursive_calls)} 个",
                    details={"self_calls": [c.call_id for c in self_calls], "recursive": [c.call_id for c in recursive_calls]},
                    recommendations=["重构以消除递归", "使用迭代替代递归"]
                )
            else:
                return CallChainResult(
                    check_id=check_id,
                    check_name=check_name,
                    status=CheckStatus.WARNING,
                    severity=CheckSeverity.MEDIUM,
                    message=f"检测到 {len(self_calls)} 个自调用",
                    details={"self_calls": [c.call_id for c in self_calls]},
                    recommendations=["检查自调用是否必要", "考虑重构以避免自调用"]
                )

    def detect_long_chains(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "CIRCULAR-E003"
        check_name = "长调用链检测"
        
        long_chains = []
        
        call_map: dict[str, SkillCall] = {c.call_id: c for c in calls}
        
        def trace_chain(call_id: str, chain: list[str]) -> list[str]:
            call = call_map.get(call_id)
            if not call:
                return chain
            
            chain.append(call.skill_name)
            
            children = [c for c in calls if c.parent_call_id == call_id]
            for child in children:
                child_chain = trace_chain(child.call_id, chain.copy())
                if len(child_chain) > self.max_chain_length:
                    long_chains.append(child_chain)
            
            return chain
        
        root_calls = [c for c in calls if not c.parent_call_id]
        for root in root_calls:
            trace_chain(root.call_id, [])
        
        if not long_chains:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="未检测到过长调用链",
                details={"max_chain_length": self.max_chain_length}
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"检测到 {len(long_chains)} 个过长调用链",
                details={"long_chains": long_chains[:5]},
                recommendations=["拆分长调用链", "考虑异步处理"]
            )


class EnhancedInvalidCallIdentifier:
    """无效调用识别器（增强版）"""

    def __init__(self):
        self.valid_skills = {
            "sanliu", "zhongshusheng", "menxiasheng", "shangshusheng",
            "libu", "hubu", "liibu", "bingbu", "xingbu", "gongbu",
            "skill-creator", "ui-ux-pro-max", "mcp-builder", "global-chinese"
        }
        
        self.deprecated_skills = {
            "old-sanliu": "请使用 sanliu 替代",
            "legacy-tester": "请使用 bingbu 替代",
            "deprecated-architect": "请使用 zhongshusheng 替代",
        }
        
        self.required_params = {
            "sanliu": ["description"],
            "skill-creator": ["name"],
            "mcp-builder": ["server_name"],
            "zhongshusheng": ["requirement"],
            "bingbu": ["test_target"],
            "gongbu": ["implementation_target"],
        }
        
        self.skill_versions = {
            "sanliu": {"min": "2.0.0", "current": "2.3.0"},
            "skill-creator": {"min": "1.0.0", "current": "1.5.0"},
        }

    def identify_invalid_calls(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "INVALID-E001"
        check_name = "无效调用识别（增强）"
        
        invalid_calls: list[InvalidCallInfo] = []
        
        for call in calls:
            if call.skill_name not in self.valid_skills:
                if call.skill_name in self.deprecated_skills:
                    invalid_calls.append(InvalidCallInfo(
                        call_id=call.call_id,
                        skill_name=call.skill_name,
                        reason="已弃用的技能",
                        suggestion=self.deprecated_skills[call.skill_name],
                        severity="high"
                    ))
                else:
                    invalid_calls.append(InvalidCallInfo(
                        call_id=call.call_id,
                        skill_name=call.skill_name,
                        reason="未知技能",
                        suggestion="请检查技能名称是否正确",
                        severity="critical"
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
                severity=CheckSeverity.CRITICAL if unknown_count > 0 else CheckSeverity.HIGH,
                message=f"检测到 {len(invalid_calls)} 个无效调用 (未知: {unknown_count}, 弃用: {deprecated_count})",
                details={
                    "invalid_calls": [
                        {"call_id": c.call_id, "skill": c.skill_name, "reason": c.reason, "severity": c.severity}
                        for c in invalid_calls
                    ]
                },
                recommendations=[c.suggestion for c in invalid_calls[:5]]
            )

    def check_missing_params(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "INVALID-E002"
        check_name = "缺失参数检查（增强）"
        
        issues = []
        
        for call in calls:
            skill = call.skill_name
            if skill in self.required_params:
                required = self.required_params[skill]
                input_data = call.input_data or {}
                
                for param in required:
                    if param not in input_data:
                        issues.append({
                            "call_id": call.call_id,
                            "skill": skill,
                            "missing_param": param,
                            "severity": "high"
                        })
                
                for param, value in input_data.items():
                    if value is None or value == "":
                        issues.append({
                            "call_id": call.call_id,
                            "skill": skill,
                            "missing_param": f"{param}(空值)",
                            "severity": "medium"
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
            high_severity = [i for i in issues if i["severity"] == "high"]
            status = CheckStatus.FAIL if high_severity else CheckStatus.WARNING
            
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=status,
                severity=CheckSeverity.HIGH if high_severity else CheckSeverity.MEDIUM,
                message=f"检测到 {len(issues)} 个参数问题",
                details={"issues": issues},
                recommendations=["补充缺失的参数", "检查空值参数"]
            )

    def check_failed_calls(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "INVALID-E003"
        check_name = "失败调用检查（增强）"
        
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
            
            retry_calls = [c for c in failed_calls if c.retry_count > 0]
            
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"检测到 {len(failed_calls)} 个失败调用",
                details={
                    "failed_count": len(failed_calls),
                    "error_summary": dict(error_summary),
                    "retry_count": len(retry_calls),
                    "failed_calls": [
                        {"call_id": c.call_id, "skill": c.skill_name, "error": c.error, "retries": c.retry_count}
                        for c in failed_calls[:10]
                    ]
                },
                recommendations=["分析失败原因", "重试失败的调用", "检查错误日志", "增加重试机制"]
            )

    def check_version_compatibility(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "INVALID-E004"
        check_name = "版本兼容性检查"
        
        warnings = []
        
        for call in calls:
            skill = call.skill_name
            if skill in self.skill_versions:
                version_info = self.skill_versions[skill]
                call_version = call.input_data.get("version", version_info["current"])
                
                if call_version < version_info["min"]:
                    warnings.append({
                        "call_id": call.call_id,
                        "skill": skill,
                        "version": call_version,
                        "min_required": version_info["min"],
                        "issue": "版本过低"
                    })
        
        if not warnings:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                message="所有技能版本兼容",
                details={"calls_checked": len(calls)}
            )
        else:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"检测到 {len(warnings)} 个版本兼容问题",
                details={"warnings": warnings},
                recommendations=["更新技能版本"]
            )


class EnhancedCallDepthAnalyzer:
    """调用深度分析器（增强版）"""

    def __init__(self, max_recommended_depth: int = 10, max_allowed_depth: int = 20):
        self.max_recommended_depth = max_recommended_depth
        self.max_allowed_depth = max_allowed_depth

    def analyze_depth(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "DEPTH-E001"
        check_name = "调用深度分析（增强）"
        
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
            {"call_id": cid, "depth": d, "skill": call_map[cid].skill_name}
            for cid, d in depth_map.items()
            if d > self.max_recommended_depth
        ]
        
        depth_distribution: dict[int, int] = defaultdict(int)
        for d in depth_map.values():
            depth_distribution[d] += 1
        
        if max_depth <= self.max_recommended_depth:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message=f"调用深度正常，最大深度: {max_depth}",
                details={
                    "max_depth": max_depth,
                    "avg_depth": round(avg_depth, 2),
                    "calls_analyzed": len(calls),
                    "depth_distribution": dict(depth_distribution)
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
                    "depth_distribution": dict(depth_distribution)
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
                    "depth_distribution": dict(depth_distribution)
                },
                recommendations=["重构以减少调用深度", "拆分复杂调用链"]
            )

    def analyze_breadth(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "DEPTH-E002"
        check_name = "调用广度分析（增强）"
        
        children_count: dict[str, int] = defaultdict(int)
        children_by_parent: dict[str, list[str]] = defaultdict(list)
        
        for call in calls:
            if call.parent_call_id:
                children_count[call.parent_call_id] += 1
                children_by_parent[call.parent_call_id].append(call.call_id)
        
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
            {"parent_id": pid, "children_count": c, "children": children_by_parent[pid][:5]}
            for pid, c in children_count.items()
            if c > 5
        ]
        
        breadth_distribution: dict[int, int] = defaultdict(int)
        for c in children_count.values():
            breadth_distribution[c] += 1
        
        if max_breadth <= 5:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                message=f"调用广度正常，最大广度: {max_breadth}",
                details={
                    "max_breadth": max_breadth,
                    "avg_breadth": round(avg_breadth, 2),
                    "breadth_distribution": dict(breadth_distribution)
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
                    "wide_calls": wide_calls,
                    "breadth_distribution": dict(breadth_distribution)
                },
                recommendations=["考虑串行化部分调用", "优化并行调用数量"]
            )

    def analyze_call_patterns(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "DEPTH-E003"
        check_name = "调用模式分析"
        
        patterns: dict[str, int] = defaultdict(int)
        
        for call in calls:
            if not call.parent_call_id:
                patterns["entry_point"] += 1
            else:
                call_map: dict[str, SkillCall] = {c.call_id: c for c in calls}
                parent = call_map.get(call.parent_call_id)
                if parent:
                    siblings = [c for c in calls if c.parent_call_id == call.parent_call_id]
                    if len(siblings) > 1:
                        patterns["parallel_child"] += 1
                    else:
                        patterns["sequential_child"] += 1
            
            if call.status == "failed":
                patterns["failed_call"] += 1
            elif call.status == "pending":
                patterns["pending_call"] += 1
        
        return CallChainResult(
            check_id=check_id,
            check_name=check_name,
            status=CheckStatus.PASS,
            severity=CheckSeverity.LOW,
            message="调用模式分析完成",
            details={
                "patterns": dict(patterns),
                "total_calls": len(calls),
                "entry_points": patterns["entry_point"],
                "parallel_ratio": patterns["parallel_child"] / max(len(calls) - patterns["entry_point"], 1)
            }
        )


class EnhancedCallPerformanceAnalyzer:
    """调用性能分析器（增强版）"""

    def __init__(self, slow_call_threshold: float = 5.0, very_slow_threshold: float = 30.0):
        self.slow_call_threshold = slow_call_threshold
        self.very_slow_threshold = very_slow_threshold

    def analyze_performance(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "PERF-E001"
        check_name = "调用性能分析（增强）"
        
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
        median_duration = sorted(durations)[len(durations) // 2]
        
        slow_calls = [
            {"call_id": c.call_id, "skill": c.skill_name, "duration": c.duration}
            for c in calls
            if c.duration > self.slow_call_threshold
        ]
        
        very_slow_calls = [
            {"call_id": c.call_id, "skill": c.skill_name, "duration": c.duration}
            for c in calls
            if c.duration > self.very_slow_threshold
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
                    "min_duration": round(min_duration, 2),
                    "median_duration": round(median_duration, 2)
                }
            )
        elif very_slow_calls:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"存在极慢调用: {len(very_slow_calls)} 个 (>{self.very_slow_threshold}s)",
                details={
                    "avg_duration": round(avg_duration, 2),
                    "max_duration": round(max_duration, 2),
                    "slow_calls": slow_calls[:10],
                    "very_slow_calls": very_slow_calls
                },
                recommendations=["优化极慢调用", "考虑缓存或异步处理", "检查性能瓶颈"]
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
        check_id = "PERF-E002"
        check_name = "超时风险分析（增强）"
        
        timeout_threshold = 30.0
        risk_calls = []
        
        for call in calls:
            if call.duration > timeout_threshold * 0.8:
                risk_level = "critical" if call.duration > timeout_threshold else "high" if call.duration > timeout_threshold * 0.9 else "medium"
                risk_calls.append({
                    "call_id": call.call_id,
                    "skill": call.skill_name,
                    "duration": call.duration,
                    "risk_level": risk_level,
                    "margin": timeout_threshold - call.duration
                })
        
        if not risk_calls:
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="无超时风险",
                details={"calls_analyzed": len(calls), "timeout_threshold": timeout_threshold}
            )
        else:
            critical_risk = [c for c in risk_calls if c["risk_level"] == "critical"]
            high_risk = [c for c in risk_calls if c["risk_level"] == "high"]
            
            if critical_risk:
                status = CheckStatus.FAIL
                severity = CheckSeverity.CRITICAL
            elif high_risk:
                status = CheckStatus.FAIL
                severity = CheckSeverity.HIGH
            else:
                status = CheckStatus.WARNING
                severity = CheckSeverity.MEDIUM
            
            return CallChainResult(
                check_id=check_id,
                check_name=check_name,
                status=status,
                severity=severity,
                message=f"检测到 {len(risk_calls)} 个超时风险调用 (严重: {len(critical_risk)}, 高: {len(high_risk)})",
                details={"risk_calls": risk_calls, "timeout_threshold": timeout_threshold},
                recommendations=["增加超时时间", "优化调用逻辑", "添加重试机制", "设置合理的超时阈值"]
            )

    def analyze_resource_usage(self, calls: list[SkillCall]) -> CallChainResult:
        check_id = "PERF-E003"
        check_name = "资源使用分析"
        
        total_duration = sum(c.duration for c in calls)
        total_calls = len(calls)
        
        skill_durations: dict[str, list[float]] = defaultdict(list)
        for call in calls:
            skill_durations[call.skill_name].append(call.duration)
        
        skill_stats = {}
        for skill, durations in skill_durations.items():
            skill_stats[skill] = {
                "total_time": sum(durations),
                "avg_time": sum(durations) / len(durations),
                "call_count": len(durations),
                "max_time": max(durations),
                "percentage": sum(durations) / total_duration * 100 if total_duration > 0 else 0
            }
        
        top_skills = sorted(skill_stats.items(), key=lambda x: x[1]["total_time"], reverse=True)[:5]
        
        return CallChainResult(
            check_id=check_id,
            check_name=check_name,
            status=CheckStatus.PASS,
            severity=CheckSeverity.LOW,
            message=f"资源使用分析完成，总耗时: {total_duration:.2f}s",
            details={
                "total_duration": round(total_duration, 2),
                "total_calls": total_calls,
                "skill_stats": skill_stats,
                "top_consumers": [(s[0], round(s[1]["total_time"], 2), f"{s[1]['percentage']:.1f}%") for s in top_skills]
            }
        )


class CallDependencyGraphBuilder:
    """调用依赖图构建器"""

    def build_dependency_graph(self, calls: list[SkillCall]) -> list[CallDependencyNode]:
        nodes: dict[str, CallDependencyNode] = {}
        
        call_map: dict[str, SkillCall] = {c.call_id: c for c in calls}
        
        for call in calls:
            node = nodes.get(call.call_id, CallDependencyNode(
                node_id=call.call_id,
                skill_name=call.skill_name,
                dependencies=[],
                dependents=[],
                depth=0
            ))
            
            if call.parent_call_id:
                parent_call = call_map.get(call.parent_call_id)
                if parent_call:
                    if parent_call.skill_name not in node.dependencies:
                        node.dependencies.append(parent_call.skill_name)
                    
                    parent_node = nodes.get(call.parent_call_id, CallDependencyNode(
                        node_id=call.parent_call_id,
                        skill_name=parent_call.skill_name,
                        dependencies=[],
                        dependents=[],
                        depth=0
                    ))
                    if call.skill_name not in parent_node.dependents:
                        parent_node.dependents.append(call.skill_name)
                    nodes[call.parent_call_id] = parent_node
            
            if not call.parent_call_id:
                node.is_entry = True
            
            children = [c for c in calls if c.parent_call_id == call.call_id]
            if not children:
                node.is_exit = True
            
            nodes[call.call_id] = node
        
        def calculate_depth(node_id: str, visited: set) -> int:
            if node_id in visited:
                return 0
            visited.add(node_id)
            
            node = nodes.get(node_id)
            if not node:
                return 0
            
            if node.is_entry:
                return 1
            
            max_dep_depth = 0
            for dep_skill in node.dependencies:
                dep_calls = [c for c in calls if c.skill_name == dep_skill]
                for dep_call in dep_calls:
                    dep_depth = calculate_depth(dep_call.call_id, visited.copy())
                    max_dep_depth = max(max_dep_depth, dep_depth)
            
            return max_dep_depth + 1
        
        for node_id, node in nodes.items():
            node.depth = calculate_depth(node_id, set())
        
        return list(nodes.values())


class SkillCallChainChecker:
    """技能调用链检查器主类（增强版）"""

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
        
        self.order_validator = EnhancedCallOrderValidator()
        self.circular_detector = EnhancedCircularCallDetector()
        self.invalid_identifier = EnhancedInvalidCallIdentifier()
        self.depth_analyzer = EnhancedCallDepthAnalyzer()
        self.performance_analyzer = EnhancedCallPerformanceAnalyzer()
        self.dependency_graph_builder = CallDependencyGraphBuilder()

    def check_all(self, calls: list[SkillCall]) -> SkillCallChainReport:
        all_results: list[CallChainResult] = []
        
        all_results.append(self.order_validator.validate_order(calls))
        all_results.append(self.order_validator.validate_dependencies(calls))
        all_results.append(self.order_validator.validate_timing(calls))
        all_results.append(self.circular_detector.detect_circular_calls(calls))
        all_results.append(self.circular_detector.detect_self_calls(calls))
        all_results.append(self.circular_detector.detect_long_chains(calls))
        all_results.append(self.invalid_identifier.identify_invalid_calls(calls))
        all_results.append(self.invalid_identifier.check_missing_params(calls))
        all_results.append(self.invalid_identifier.check_failed_calls(calls))
        all_results.append(self.invalid_identifier.check_version_compatibility(calls))
        all_results.append(self.depth_analyzer.analyze_depth(calls))
        all_results.append(self.depth_analyzer.analyze_breadth(calls))
        all_results.append(self.depth_analyzer.analyze_call_patterns(calls))
        all_results.append(self.performance_analyzer.analyze_performance(calls))
        all_results.append(self.performance_analyzer.analyze_timeout_risk(calls))
        all_results.append(self.performance_analyzer.analyze_resource_usage(calls))
        
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
        dependency_nodes = self.dependency_graph_builder.build_dependency_graph(calls)
        
        valid_calls = sum(1 for c in calls if c.status == "completed")
        invalid_calls = sum(1 for c in calls if c.status == "failed")
        
        durations = [c.duration for c in calls if c.duration > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        depth_map = self._calculate_depths(calls)
        max_depth = max(depth_map.values()) if depth_map else 0
        
        summary = self._generate_summary(all_results, calls, circular_detected, invalid_detected)
        
        report = SkillCallChainReport(
            report_id=f"SCC-E-{datetime.now().strftime('%Y%m%d%H%M%S')}",
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
            dependency_nodes=dependency_nodes,
            summary=summary,
            overall_status=overall_status
        )
        
        return report

    def _extract_circular_info(self, results: list[CallChainResult]) -> list[CircularCallInfo]:
        for result in results:
            if result.check_id == "CIRCULAR-E001" and result.status == CheckStatus.FAIL:
                chains = result.details.get("chains", [])
                return [
                    CircularCallInfo(
                        call_chain=c["chain"],
                        detected_at=datetime.now().isoformat(),
                        depth=c["depth"],
                        affected_skills=list(set(c["chain"])),
                        severity=c.get("severity", "critical")
                    )
                    for c in chains
                ]
        return []

    def _extract_invalid_info(self, results: list[CallChainResult]) -> list[InvalidCallInfo]:
        for result in results:
            if result.check_id == "INVALID-E001":
                invalid_calls = result.details.get("invalid_calls", [])
                return [
                    InvalidCallInfo(
                        call_id=c["call_id"],
                        skill_name=c["skill"],
                        reason=c["reason"],
                        suggestion="",
                        severity=c.get("severity", "high")
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

    def _generate_summary(self, results: list[CallChainResult], calls: list[SkillCall],
                         circular_detected: list[CircularCallInfo], 
                         invalid_detected: list[InvalidCallInfo]) -> dict[str, Any]:
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
            "total_calls": len(calls),
            "circular_count": len(circular_detected),
            "invalid_count": len(invalid_detected)
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
                    "severity": c.severity
                }
                for c in report.circular_detected
            ],
            "invalid_detected": [
                {
                    "call_id": i.call_id,
                    "skill_name": i.skill_name,
                    "reason": i.reason,
                    "severity": i.severity
                }
                for i in report.invalid_detected
            ],
            "call_graph": report.call_graph,
            "dependency_nodes": [
                {
                    "node_id": n.node_id,
                    "skill_name": n.skill_name,
                    "dependencies": n.dependencies,
                    "dependents": n.dependents,
                    "depth": n.depth,
                    "is_entry": n.is_entry,
                    "is_exit": n.is_exit
                }
                for n in report.dependency_nodes
            ],
            "summary": report.summary
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"报告已保存: {output_path}")
        return output_path

    def print_report(self, report: SkillCallChainReport):
        print("\n" + "=" * 70)
        print("技能调用链检查报告（增强版）")
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
                severity_marker = "!" if circular.severity == "critical" else "?"
                print(f"  [{severity_marker}] {' → '.join(circular.call_chain)} (深度: {circular.depth}, 严重度: {circular.severity})")
        
        if report.invalid_detected:
            print("\n" + "-" * 70)
            print("无效调用:")
            for invalid in report.invalid_detected[:10]:
                severity_marker = "!" if invalid.severity == "critical" else "?"
                print(f"  [{severity_marker}] [{invalid.call_id}] {invalid.skill_name}: {invalid.reason}")
        
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
    return [
        SkillCall(
            call_id="call-001",
            skill_name="sanliu",
            caller="user",
            callee="zhongshusheng",
            timestamp=datetime.now().isoformat(),
            status="completed",
            duration=1.5,
            parent_call_id=None,
            input_data={"description": "创建用户管理模块"},
            priority="high"
        ),
        SkillCall(
            call_id="call-002",
            skill_name="zhongshusheng",
            caller="sanliu",
            callee="requirement_analysis",
            timestamp=datetime.now().isoformat(),
            status="completed",
            duration=2.0,
            parent_call_id="call-001",
            input_data={"requirement": "用户注册登录"}
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
            parent_call_id="call-004",
            input_data={"test_target": "user_service"}
        ),
        SkillCall(
            call_id="call-006",
            skill_name="gongbu",
            caller="shangshusheng",
            callee="code_generator",
            timestamp=datetime.now().isoformat(),
            status="completed",
            duration=4.0,
            parent_call_id="call-004",
            input_data={"implementation_target": "user_service"}
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
    parser = argparse.ArgumentParser(description="技能调用链检查器（增强版）")
    
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
                    retry_count=item.get("retry_count", 0),
                    priority=item.get("priority", "normal")
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
        validator = EnhancedCallOrderValidator()
        result = validator.validate_order(calls)
        status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
        print(f"\n[{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.check_circular:
        detector = EnhancedCircularCallDetector()
        result = detector.detect_circular_calls(calls)
        status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
        print(f"\n[{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.check_invalid:
        identifier = EnhancedInvalidCallIdentifier()
        result = identifier.identify_invalid_calls(calls)
        status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
        print(f"\n[{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.analyze_depth:
        analyzer = EnhancedCallDepthAnalyzer()
        result = analyzer.analyze_depth(calls)
        status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
        print(f"\n[{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.analyze_performance:
        analyzer = EnhancedCallPerformanceAnalyzer()
        result = analyzer.analyze_performance(calls)
        status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
        print(f"\n[{status_symbol}] {result.check_name}: {result.message}")


if __name__ == "__main__":
    main()
