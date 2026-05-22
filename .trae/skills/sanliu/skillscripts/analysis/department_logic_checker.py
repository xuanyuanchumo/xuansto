#!/usr/bin/env python3
"""
六部执行逻辑检查器（增强版） - Sanliu 技能

功能增强：
- 六部执行逻辑完整性检查
- 吏部调度逻辑深度验证（优先级调度、依赖关系、执行顺序）
- 户部资源管理逻辑深度验证（资源池管理、配额控制、资源回收）
- 礼部规范制定逻辑深度验证（规范版本控制、合规性审计、变更追踪）
- 兵部测试先行逻辑深度验证（TDD流程完整性、测试驱动验证、边界条件）
- 工部代码实现逻辑深度验证（实现规范遵循、代码审查、技术债务追踪）
- 刑部重构优化逻辑深度验证（重构风险评估、性能回归、代码演化追踪）
- 六部协调一致性检查

使用方法：
    python scripts/analysis/department_logic_checker.py --check-all
    python scripts/analysis/department_logic_checker.py --check-libu
    python scripts/analysis/department_logic_checker.py --check-hubu
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
        logging.FileHandler('department_logic_checker_enhanced.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class Ministry(Enum):
    """六部枚举类 - 代表六个核心部门"""
    LIBU = "libu"
    HUBU = "hubu"
    LIIBU = "liibu"
    BINGBU = "bingbu"
    XINGBU = "xingbu"
    GONGBU = "gongbu"


class CheckStatus(Enum):
    """检查状态枚举"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


class CheckSeverity(Enum):
    """检查严重程度枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DepartmentCheckResult:
    """部门检查结果数据类"""
    check_id: str
    check_name: str
    ministry: Ministry
    status: CheckStatus
    severity: CheckSeverity
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class MinistryCoordinationIssue:
    """六部协调问题数据类"""
    issue_id: str
    from_ministry: Ministry
    to_ministry: Ministry
    issue_type: str
    description: str
    impact: str
    suggested_fix: str


@dataclass
class DepartmentLogicReport:
    """部门逻辑检查报告数据类"""
    report_id: str
    generated_at: str
    total_checks: int
    passed: int
    failed: int
    warnings: int
    skipped: int
    results: list[DepartmentCheckResult]
    by_ministry: dict[str, dict[str, int]]
    coordination_issues: list[MinistryCoordinationIssue]
    summary: dict[str, Any]
    overall_status: CheckStatus


class EnhancedLibuChecker:
    """
    吏部调度逻辑深度检查器
    
    吏部负责：Agent分配、技能匹配、负载均衡、任务调度
    增强功能：优先级调度验证、依赖关系检查、执行顺序验证
    """

    def __init__(self):
        self.ministry = Ministry.LIBU

    def check_agent_assignment(self, assignment_data: dict[str, Any]) -> DepartmentCheckResult:
        """Agent分配深度检查"""
        check_id = "LIBU-E001"
        check_name = "Agent分配深度检查"
        
        issues = []
        warnings = []
        
        agents = assignment_data.get("agents", [])
        tasks = assignment_data.get("tasks", [])
        assignments = assignment_data.get("assignments", [])
        
        if not agents:
            issues.append("未定义可用Agent")
        else:
            for agent in agents:
                if not agent.get("id"):
                    warnings.append("存在未编号的Agent")
                if not agent.get("capabilities"):
                    warnings.append(f"Agent {agent.get('id', 'unknown')} 未定义能力")
        
        if not tasks:
            issues.append("未定义任务列表")
        else:
            for task in tasks:
                if not task.get("id"):
                    warnings.append("存在未编号的任务")
                if not task.get("required_capabilities"):
                    warnings.append(f"任务 {task.get('id', 'unknown')} 未定义所需能力")
        
        unassigned_tasks = []
        for task in tasks:
            task_id = task.get("id")
            assigned = any(a.get("task_id") == task_id for a in assignments)
            if not assigned:
                unassigned_tasks.append(task_id)
        
        if unassigned_tasks:
            issues.append(f"存在未分配任务: {unassigned_tasks[:5]}")
        
        overloaded_agents = []
        for agent in agents:
            agent_id = agent.get("id")
            agent_tasks = [a for a in assignments if a.get("agent_id") == agent_id]
            max_tasks = agent.get("max_concurrent_tasks", 3)
            if len(agent_tasks) > max_tasks:
                overloaded_agents.append({"id": agent_id, "tasks": len(agent_tasks), "max": max_tasks})
        
        if overloaded_agents:
            issues.append(f"Agent负载过高: {[a['id'] for a in overloaded_agents]}")
        
        capability_mismatch = []
        for assignment in assignments:
            agent_id = assignment.get("agent_id")
            task_id = assignment.get("task_id")
            agent = next((a for a in agents if a.get("id") == agent_id), None)
            task = next((t for t in tasks if t.get("id") == task_id), None)
            
            if agent and task:
                agent_caps = set(agent.get("capabilities", []))
                required_caps = set(task.get("required_capabilities", []))
                if not required_caps.issubset(agent_caps):
                    capability_mismatch.append({
                        "agent": agent_id,
                        "task": task_id,
                        "missing": list(required_caps - agent_caps)
                    })
        
        if capability_mismatch:
            warnings.append(f"存在能力不匹配的分配: {len(capability_mismatch)} 个")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="Agent分配合理",
                details={"agents_count": len(agents), "tasks_count": len(tasks), "assignments_count": len(assignments)}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM,
                message=f"Agent分配存在建议: {'; '.join(warnings[:3])}",
                details={"warnings": warnings}, recommendations=["优化Agent能力定义", "完善任务需求"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.FAIL, severity=CheckSeverity.HIGH,
                message=f"Agent分配存在问题: {'; '.join(issues)}",
                details={"issues": issues, "capability_mismatch": capability_mismatch},
                recommendations=["重新分配任务", "增加Agent数量", "调整负载均衡"]
            )

    def check_skill_matching(self, skill_data: dict[str, Any]) -> DepartmentCheckResult:
        """技能匹配深度检查"""
        check_id = "LIBU-E002"
        check_name = "技能匹配深度检查"
        
        issues = []
        warnings = []
        
        required_skills = skill_data.get("required_skills", [])
        available_skills = skill_data.get("available_skills", [])
        skill_scores = skill_data.get("skill_scores", {})
        
        missing_skills = [skill for skill in required_skills if skill not in available_skills]
        if missing_skills:
            issues.append(f"缺少必要技能: {missing_skills}")
        
        low_score_skills = []
        for skill, score in skill_scores.items():
            if score < 0.6:
                low_score_skills.append({"skill": skill, "score": score})
            elif score < 0.8:
                warnings.append(f"技能 {skill} 熟练度待提升: {score:.0%}")
        
        if low_score_skills:
            issues.append(f"技能熟练度过低: {[s['skill'] for s in low_score_skills]}")
        
        skill_coverage = skill_data.get("skill_coverage", {})
        for skill, coverage in skill_coverage.items():
            if coverage < 0.5:
                warnings.append(f"技能 {skill} 覆盖率不足: {coverage:.0%}")
        
        skill_dependencies = skill_data.get("skill_dependencies", {})
        for skill, deps in skill_dependencies.items():
            missing_deps = [d for d in deps if d not in available_skills]
            if missing_deps:
                warnings.append(f"技能 {skill} 缺少依赖: {missing_deps}")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.PASS, severity=CheckSeverity.MEDIUM, message="技能匹配良好",
                details={"required_skills": required_skills, "available_skills": available_skills,
                        "avg_score": sum(skill_scores.values()) / len(skill_scores) if skill_scores else 0}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM,
                message=f"技能匹配存在建议: {'; '.join(warnings[:3])}",
                details={"warnings": warnings}, recommendations=["提升技能熟练度"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.FAIL, severity=CheckSeverity.HIGH,
                message=f"技能匹配存在问题: {'; '.join(issues)}",
                details={"issues": issues, "low_score_skills": low_score_skills},
                recommendations=["补充缺失技能", "培训或引入新Agent"]
            )

    def check_load_balance(self, load_data: dict[str, Any]) -> DepartmentCheckResult:
        """负载均衡深度检查"""
        check_id = "LIBU-E003"
        check_name = "负载均衡深度检查"
        
        issues = []
        warnings = []
        
        agent_loads = load_data.get("agent_loads", {})
        
        if not agent_loads:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无负载数据",
                recommendations=["收集Agent负载数据"]
            )
        
        loads = list(agent_loads.values())
        avg_load = sum(loads) / len(loads) if loads else 0
        
        imbalance_threshold = 0.3
        imbalanced_agents = []
        for agent_id, load in agent_loads.items():
            deviation = abs(load - avg_load) / avg_load if avg_load > 0 else 0
            if deviation > imbalance_threshold:
                imbalanced_agents.append({"id": agent_id, "load": load, "deviation": deviation})
        
        if imbalanced_agents:
            warnings.append(f"存在负载不均衡Agent: {len(imbalanced_agents)} 个")
        
        max_load = max(loads) if loads else 0
        min_load = min(loads) if loads else 0
        
        if max_load > 0.9:
            issues.append(f"存在过载Agent，负载率: {max_load:.1%}")
        
        if min_load < 0.2 and max_load > 0.5:
            warnings.append("负载分布不均，存在空闲Agent")
        
        load_trend = load_data.get("load_trend", [])
        if load_trend:
            increasing = [t for t in load_trend if t.get("trend") == "increasing"]
            if len(increasing) > len(load_trend) * 0.5:
                warnings.append("整体负载呈上升趋势，需关注容量")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.PASS, severity=CheckSeverity.MEDIUM,
                message=f"负载均衡良好，平均负载: {avg_load:.1%}",
                details={"avg_load": avg_load, "max_load": max_load, "min_load": min_load}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM,
                message=f"负载均衡存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings, "imbalanced_agents": imbalanced_agents},
                recommendations=["重新分配任务以平衡负载"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.FAIL, severity=CheckSeverity.HIGH,
                message=f"负载均衡存在问题: {'; '.join(issues)}",
                details={"issues": issues}, recommendations=["紧急调整任务分配", "增加Agent资源"]
            )

    def check_task_scheduling(self, schedule_data: dict[str, Any]) -> DepartmentCheckResult:
        """任务调度检查"""
        check_id = "LIBU-E004"
        check_name = "任务调度检查"
        
        issues = []
        warnings = []
        
        schedule = schedule_data.get("schedule", [])
        if not schedule:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无任务调度数据",
                recommendations=["建立任务调度计划"]
            )
        
        for i, task_schedule in enumerate(schedule):
            if not task_schedule.get("start_time"):
                warnings.append(f"任务{i+1}缺少开始时间")
            if not task_schedule.get("end_time"):
                warnings.append(f"任务{i+1}缺少结束时间")
            if not task_schedule.get("assigned_agent"):
                issues.append(f"任务{i+1}未分配Agent")
        
        conflicts = schedule_data.get("conflicts", [])
        if conflicts:
            issues.append(f"存在调度冲突: {len(conflicts)} 个")
        
        priorities = schedule_data.get("priority_violations", [])
        if priorities:
            warnings.append(f"存在优先级违反: {len(priorities)} 个")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.PASS, severity=CheckSeverity.MEDIUM, message="任务调度合理",
                details={"scheduled_tasks": len(schedule)}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM,
                message=f"任务调度存在建议: {'; '.join(warnings[:3])}",
                details={"warnings": warnings}, recommendations=["完善任务调度信息"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.FAIL, severity=CheckSeverity.HIGH,
                message=f"任务调度存在问题: {'; '.join(issues)}",
                details={"issues": issues}, recommendations=["修复调度问题", "解决冲突"]
            )

    def check_priority_scheduling(self, priority_data: dict[str, Any]) -> DepartmentCheckResult:
        """优先级调度验证（增强功能）"""
        check_id = "LIBU-E005"
        check_name = "优先级调度验证"
        
        issues = []
        warnings = []
        
        tasks = priority_data.get("tasks", [])
        if not tasks:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无任务优先级数据",
                recommendations=["定义任务优先级"]
            )
        
        valid_priorities = ["critical", "high", "medium", "low"]
        tasks_without_priority = []
        invalid_priorities = []
        
        for task in tasks:
            task_id = task.get("id", "unknown")
            priority = task.get("priority")
            if not priority:
                tasks_without_priority.append(task_id)
            elif priority not in valid_priorities:
                invalid_priorities.append({"task": task_id, "priority": priority})
        
        if tasks_without_priority:
            warnings.append(f"存在未设置优先级的任务: {len(tasks_without_priority)} 个")
        
        if invalid_priorities:
            issues.append(f"存在无效优先级: {invalid_priorities[:3]}")
        
        execution_order = priority_data.get("execution_order", [])
        if execution_order:
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            violations = []
            for i in range(len(execution_order) - 1):
                current = execution_order[i]
                next_task = execution_order[i + 1]
                curr_priority = current.get("priority", "medium")
                next_priority = next_task.get("priority", "medium")
                if priority_order.get(curr_priority, 2) > priority_order.get(next_priority, 2):
                    violations.append({"current": current.get("id"), "next": next_task.get("id")})
            if violations:
                warnings.append(f"存在优先级执行顺序问题: {len(violations)} 处")
        
        urgent_tasks = priority_data.get("urgent_tasks", [])
        urgent_handled = priority_data.get("urgent_handled", [])
        if urgent_tasks:
            unhandled_urgent = [t for t in urgent_tasks if t not in urgent_handled]
            if unhandled_urgent:
                issues.append(f"存在未处理的紧急任务: {len(unhandled_urgent)} 个")
        
        priority_inversions = priority_data.get("priority_inversions", [])
        if priority_inversions:
            issues.append(f"检测到优先级反转: {len(priority_inversions)} 处")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="优先级调度合理",
                details={"tasks_count": len(tasks), "priority_distribution": self._get_priority_distribution(tasks)}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM,
                message=f"优先级调度存在建议: {'; '.join(warnings[:3])}",
                details={"warnings": warnings}, recommendations=["完善任务优先级设置", "优化调度顺序"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.FAIL, severity=CheckSeverity.HIGH,
                message=f"优先级调度存在问题: {'; '.join(issues)}",
                details={"issues": issues}, recommendations=["修复优先级设置", "处理紧急任务", "解决优先级反转"]
            )

    def check_task_dependencies(self, dep_data: dict[str, Any]) -> DepartmentCheckResult:
        """任务依赖关系检查（增强功能）"""
        check_id = "LIBU-E006"
        check_name = "任务依赖关系检查"
        
        issues = []
        warnings = []
        
        tasks = dep_data.get("tasks", [])
        dependencies = dep_data.get("dependencies", {})
        
        if not tasks:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无任务数据",
                recommendations=["定义任务列表"]
            )
        
        task_ids = {t.get("id") for t in tasks if t.get("id")}
        missing_dependencies = []
        
        for task_id, deps in dependencies.items():
            for dep in deps:
                if dep not in task_ids:
                    missing_dependencies.append({"task": task_id, "missing_dep": dep})
        
        if missing_dependencies:
            issues.append(f"存在缺失的依赖任务: {len(missing_dependencies)} 个")
        
        circular_deps = self._detect_circular_dependencies(dependencies)
        if circular_deps:
            issues.append(f"检测到循环依赖: {circular_deps[:3]}")
        
        max_depth = 0
        for task_id in task_ids:
            depth = self._calculate_dependency_depth(task_id, dependencies)
            max_depth = max(max_depth, depth)
        
        if max_depth > 10:
            warnings.append(f"依赖链深度过大: {max_depth} 层")
        
        critical_path = dep_data.get("critical_path", [])
        if critical_path:
            bottleneck_tasks = [t for t in critical_path if t.get("is_bottleneck", False)]
            if bottleneck_tasks:
                warnings.append(f"关键路径存在瓶颈任务: {len(bottleneck_tasks)} 个")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="任务依赖关系合理",
                details={"tasks_count": len(tasks), "max_dependency_depth": max_depth,
                        "dependencies_count": sum(len(deps) for deps in dependencies.values())}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM,
                message=f"任务依赖存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings, "max_depth": max_depth},
                recommendations=["简化依赖链", "识别瓶颈任务"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.FAIL, severity=CheckSeverity.HIGH,
                message=f"任务依赖存在问题: {'; '.join(issues)}",
                details={"issues": issues, "circular_deps": circular_deps},
                recommendations=["解决循环依赖", "补充缺失依赖", "简化依赖结构"]
            )

    def check_execution_order(self, order_data: dict[str, Any]) -> DepartmentCheckResult:
        """执行顺序验证（增强功能）"""
        check_id = "LIBU-E007"
        check_name = "执行顺序验证"
        
        issues = []
        warnings = []
        
        execution_plan = order_data.get("execution_plan", [])
        
        if not execution_plan:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无执行计划数据",
                recommendations=["制定执行计划"]
            )
        
        parallel_groups = order_data.get("parallel_groups", [])
        for group in parallel_groups:
            tasks = group.get("tasks", [])
            shared_resources = group.get("shared_resources", [])
            if shared_resources and len(tasks) > 1:
                warnings.append(f"并行任务组存在共享资源竞争: {shared_resources}")
        
        time_constraints = order_data.get("time_constraints", [])
        violations = []
        for constraint in time_constraints:
            task_id = constraint.get("task_id")
            required_before = constraint.get("required_before")
            actual_time = constraint.get("actual_time")
            if required_before and actual_time and actual_time > required_before:
                violations.append({"task": task_id, "required": required_before, "actual": actual_time})
        
        if violations:
            issues.append(f"存在时间约束违反: {len(violations)} 处")
        
        execution_gaps = order_data.get("execution_gaps", [])
        large_gaps = [g for g in execution_gaps if g.get("duration", 0) > 3600]
        if large_gaps:
            warnings.append(f"存在较大执行间隙: {len(large_gaps)} 处")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="执行顺序合理",
                details={"total_steps": len(execution_plan), "parallel_groups": len(parallel_groups)}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM,
                message=f"执行顺序存在建议: {'; '.join(warnings[:3])}",
                details={"warnings": warnings}, recommendations=["优化并行策略", "减少执行间隙"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.FAIL, severity=CheckSeverity.HIGH,
                message=f"执行顺序存在问题: {'; '.join(issues)}",
                details={"issues": issues, "time_violations": violations},
                recommendations=["调整执行顺序", "解决资源竞争", "满足时间约束"]
            )

    def _get_priority_distribution(self, tasks: list[dict]) -> dict[str, int]:
        """获取优先级分布统计"""
        distribution = defaultdict(int)
        for task in tasks:
            priority = task.get("priority", "medium")
            distribution[priority] += 1
        return dict(distribution)

    def _detect_circular_dependencies(self, dependencies: dict[str, list]) -> list[list[str]]:
        """检测循环依赖"""
        circular = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: list[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in dependencies.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    circular.append(path[cycle_start:] + [neighbor])
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for node in dependencies:
            if node not in visited:
                dfs(node, [])
        
        return circular

    def _calculate_dependency_depth(self, task_id: str, dependencies: dict[str, list], visited: set = None) -> int:
        """计算依赖链深度"""
        if visited is None:
            visited = set()
        
        if task_id in visited:
            return 0
        
        visited.add(task_id)
        deps = dependencies.get(task_id, [])
        
        if not deps:
            return 0
        
        max_depth = 0
        for dep in deps:
            depth = self._calculate_dependency_depth(dep, dependencies, visited.copy())
            max_depth = max(max_depth, depth + 1)
        
        return max_depth

    def run_all_checks(self, data: dict[str, Any]) -> list[DepartmentCheckResult]:
        """运行所有吏部检查"""
        results = []
        results.append(self.check_agent_assignment(data.get("assignment", {})))
        results.append(self.check_skill_matching(data.get("skills", {})))
        results.append(self.check_load_balance(data.get("load", {})))
        results.append(self.check_task_scheduling(data.get("scheduling", {})))
        results.append(self.check_priority_scheduling(data.get("priority", {})))
        results.append(self.check_task_dependencies(data.get("dependencies", {})))
        results.append(self.check_execution_order(data.get("execution_order", {})))
        return results


class EnhancedHubuChecker:
    """户部资源管理逻辑深度检查器"""

    def __init__(self):
        self.ministry = Ministry.HUBU

    def check_environment_config(self, env_data: dict[str, Any]) -> DepartmentCheckResult:
        """环境配置深度检查"""
        check_id = "HUBU-E001"
        check_name = "环境配置深度检查"
        
        issues = []
        warnings = []
        
        required_envs = ["development", "testing", "production"]
        environments = env_data.get("environments", {})
        
        for env in required_envs:
            if env not in environments:
                issues.append(f"缺少环境配置: {env}")
            else:
                env_config = environments[env]
                if "database" not in env_config:
                    issues.append(f"环境 {env} 缺少数据库配置")
                if "cache" not in env_config:
                    warnings.append(f"环境 {env} 缺少缓存配置")
                if "logging" not in env_config:
                    warnings.append(f"环境 {env} 缺少日志配置")
                if "monitoring" not in env_config:
                    warnings.append(f"环境 {env} 缺少监控配置")
        
        env_secrets = env_data.get("secrets", {})
        for env in environments:
            if env not in env_secrets:
                warnings.append(f"环境 {env} 未配置密钥管理")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="环境配置完整",
                details={"environments": list(environments.keys())}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM,
                message=f"环境配置存在建议: {'; '.join(warnings[:3])}",
                details={"warnings": warnings}, recommendations=["完善环境配置"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.FAIL, severity=CheckSeverity.HIGH,
                message=f"环境配置存在问题: {'; '.join(issues)}",
                details={"issues": issues}, recommendations=["补充缺失的环境配置"]
            )

    def check_resource_allocation(self, resource_data: dict[str, Any]) -> DepartmentCheckResult:
        """资源分配深度检查"""
        check_id = "HUBU-E002"
        check_name = "资源分配深度检查"
        
        issues = []
        warnings = []
        
        resources = resource_data.get("resources", {})
        allocations = resource_data.get("allocations", {})
        utilization = resource_data.get("utilization", {})
        
        resource_types = ["cpu", "memory", "storage", "network"]
        
        for res_type in resource_types:
            total = resources.get(res_type, 0)
            allocated = allocations.get(res_type, 0)
            
            if total == 0:
                issues.append(f"未定义{res_type}资源总量")
            elif allocated > total:
                issues.append(f"{res_type}资源超分配: {allocated}/{total}")
            elif allocated > total * 0.9:
                warnings.append(f"{res_type}资源接近上限: {allocated}/{total}")
            
            util_rate = utilization.get(res_type, 0)
            if util_rate > 0 and util_rate < 0.3:
                warnings.append(f"{res_type}资源利用率低: {util_rate:.1%}")
        
        reserved = resource_data.get("reserved", {})
        for res_type in resource_types:
            if res_type not in reserved:
                warnings.append(f"未配置{res_type}预留资源")
        
        scaling = resource_data.get("auto_scaling", {})
        if not scaling.get("enabled", False):
            warnings.append("未启用自动扩缩容")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="资源分配合理",
                details={"resource_types": resource_types, "utilization": utilization}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM,
                message=f"资源分配存在建议: {'; '.join(warnings[:3])}",
                details={"warnings": warnings}, recommendations=["考虑扩容资源", "启用自动扩缩容"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.FAIL, severity=CheckSeverity.HIGH,
                message=f"资源分配存在问题: {'; '.join(issues)}",
                details={"issues": issues}, recommendations=["调整资源分配", "增加资源容量"]
            )

    def check_dependency_management(self, dep_data: dict[str, Any]) -> DepartmentCheckResult:
        """依赖管理深度检查"""
        check_id = "HUBU-E003"
        check_name = "依赖管理深度检查"
        
        issues = []
        warnings = []
        
        dependencies = dep_data.get("dependencies", [])
        
        if not dependencies:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="未定义依赖列表",
                recommendations=["定义项目依赖"]
            )
        
        outdated = [d for d in dependencies if d.get("outdated", False)]
        if outdated:
            major_outdated = [d for d in outdated if d.get("major_update", False)]
            if major_outdated:
                issues.append(f"存在主要版本过时依赖: {[d.get('name') for d in major_outdated]}")
            else:
                warnings.append(f"存在过时依赖: {len(outdated)} 个")
        
        vulnerable = [d for d in dependencies if d.get("vulnerable", False)]
        if vulnerable:
            critical_vulns = [d for d in vulnerable if d.get("severity") == "critical"]
            if critical_vulns:
                issues.append(f"存在严重安全漏洞依赖: {[d.get('name') for d in critical_vulns]}")
            else:
                warnings.append(f"存在安全漏洞依赖: {len(vulnerable)} 个")
        
        conflicts = dep_data.get("conflicts", [])
        if conflicts:
            issues.append(f"存在依赖冲突: {conflicts}")
        
        unused = dep_data.get("unused", [])
        if unused:
            warnings.append(f"存在未使用依赖: {unused[:5]}")
        
        license_issues = dep_data.get("license_issues", [])
        if license_issues:
            warnings.append(f"存在许可证问题: {license_issues[:3]}")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.PASS, severity=CheckSeverity.MEDIUM, message="依赖管理正常",
                details={"dependencies_count": len(dependencies)}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM,
                message=f"依赖管理存在建议: {'; '.join(warnings[:3])}",
                details={"warnings": warnings}, recommendations=["更新过时依赖", "清理未使用依赖"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.FAIL, severity=CheckSeverity.HIGH,
                message=f"依赖管理存在问题: {'; '.join(issues)}",
                details={"issues": issues}, recommendations=["修复安全漏洞", "解决依赖冲突"]
            )

    def check_cost_optimization(self, cost_data: dict[str, Any]) -> DepartmentCheckResult:
        """成本优化检查"""
        check_id = "HUBU-E004"
        check_name = "成本优化检查"
        
        issues = []
        warnings = []
        
        budget = cost_data.get("budget", 0)
        actual = cost_data.get("actual_cost", 0)
        
        if budget > 0:
            if actual > budget:
                issues.append(f"成本超出预算: {actual}/{budget}")
            elif actual > budget * 0.9:
                warnings.append(f"成本接近预算上限: {actual}/{budget}")
        
        cost_breakdown = cost_data.get("breakdown", {})
        if cost_breakdown:
            high_cost_items = [
                {"item": k, "cost": v}
                for k, v in cost_breakdown.items()
                if v > budget * 0.3 if budget > 0 else v > 1000
            ]
            if high_cost_items:
                warnings.append(f"高成本项目: {[i['item'] for i in high_cost_items]}")
        
        optimization_suggestions = cost_data.get("optimization_suggestions", [])
        if optimization_suggestions:
            potential_savings = sum(s.get("savings", 0) for s in optimization_suggestions)
            if potential_savings > 0:
                warnings.append(f"潜在节省: {potential_savings}")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.PASS, severity=CheckSeverity.MEDIUM, message="成本控制良好",
                details={"budget": budget, "actual": actual}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM,
                message=f"成本优化存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings, "suggestions": optimization_suggestions},
                recommendations=["实施成本优化建议"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.FAIL, severity=CheckSeverity.HIGH,
                message=f"成本控制存在问题: {'; '.join(issues)}",
                details={"issues": issues}, recommendations=["控制成本", "优化资源使用"]
            )

    def check_resource_pool_management(self, pool_data: dict[str, Any]) -> DepartmentCheckResult:
        """资源池管理检查（增强功能）"""
        check_id = "HUBU-E005"
        check_name = "资源池管理检查"
        
        issues = []
        warnings = []
        
        pools = pool_data.get("pools", [])
        
        if not pools:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="未定义资源池",
                recommendations=["定义资源池以提高资源利用率"]
            )
        
        for pool in pools:
            pool_name = pool.get("name", "unknown")
            pool_type = pool.get("type")
            capacity = pool.get("capacity", {})
            used = pool.get("used", {})
            
            if not pool_type:
                warnings.append(f"资源池 '{pool_name}' 未定义类型")
            
            for resource, cap in capacity.items():
                used_amount = used.get(resource, 0)
                if used_amount > cap:
                    issues.append(f"资源池 '{pool_name}' {resource} 超出容量")
                elif used_amount > cap * 0.9:
                    warnings.append(f"资源池 '{pool_name}' {resource} 接近容量上限")
            
            isolation = pool.get("isolation", {})
            if not isolation.get("enabled", False):
                warnings.append(f"资源池 '{pool_name}' 未启用隔离")
            
            monitoring = pool.get("monitoring", {})
            if not monitoring.get("enabled", False):
                warnings.append(f"资源池 '{pool_name}' 未启用监控")
        
        pool_allocation = pool_data.get("allocation_strategy", {})
        if not pool_allocation.get("strategy"):
            warnings.append("未定义资源池分配策略")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="资源池管理良好",
                details={"pools_count": len(pools)}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM,
                message=f"资源池管理存在建议: {'; '.join(warnings[:3])}",
                details={"warnings": warnings}, recommendations=["完善资源池配置", "启用隔离和监控"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.FAIL, severity=CheckSeverity.HIGH,
                message=f"资源池管理存在问题: {'; '.join(issues)}",
                details={"issues": issues}, recommendations=["调整资源池容量", "解决超容量问题"]
            )

    def check_quota_control(self, quota_data: dict[str, Any]) -> DepartmentCheckResult:
        """配额控制检查（增强功能）"""
        check_id = "HUBU-E006"
        check_name = "配额控制检查"
        
        issues = []
        warnings = []
        
        quotas = quota_data.get("quotas", [])
        
        if not quotas:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="未定义配额",
                recommendations=["定义资源配额以控制使用"]
            )
        
        exceeded_quotas = []
        near_limit_quotas = []
        
        for quota in quotas:
            quota_name = quota.get("name", "unknown")
            limit = quota.get("limit", 0)
            used = quota.get("used", 0)
            
            if used > limit:
                exceeded_quotas.append({"name": quota_name, "limit": limit, "used": used})
            elif used > limit * 0.9:
                near_limit_quotas.append({"name": quota_name, "usage_rate": used / limit if limit > 0 else 0})
        
        if exceeded_quotas:
            issues.append(f"存在超限配额: {[q['name'] for q in exceeded_quotas]}")
        
        if near_limit_quotas:
            warnings.append(f"存在接近上限的配额: {[q['name'] for q in near_limit_quotas]}")
        
        alerts = quota_data.get("alerts", [])
        unhandled_alerts = [a for a in alerts if not a.get("handled", False)]
        if unhandled_alerts:
            warnings.append(f"存在未处理的配额告警: {len(unhandled_alerts)} 个")
        
        adjustment_mechanism = quota_data.get("adjustment_mechanism", {})
        if not adjustment_mechanism.get("enabled", False):
            warnings.append("未启用配额自动调整机制")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="配额控制良好",
                details={"quotas_count": len(quotas)}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM,
                message=f"配额控制存在建议: {'; '.join(warnings[:3])}",
                details={"warnings": warnings}, recommendations=["处理配额告警", "启用自动调整"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.FAIL, severity=CheckSeverity.HIGH,
                message=f"配额控制存在问题: {'; '.join(issues)}",
                details={"issues": issues, "exceeded": exceeded_quotas},
                recommendations=["调整配额限制", "减少资源使用"]
            )

    def check_resource_recycling(self, recycle_data: dict[str, Any]) -> DepartmentCheckResult:
        """资源回收检查（增强功能）"""
        check_id = "HUBU-E007"
        check_name = "资源回收检查"
        
        issues = []
        warnings = []
        
        recycling_policy = recycle_data.get("policy", {})
        
        if not recycling_policy:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="未定义资源回收策略",
                recommendations=["定义资源回收策略以优化资源利用"]
            )
        
        idle_resources = recycle_data.get("idle_resources", [])
        if idle_resources:
            long_idle = [r for r in idle_resources if r.get("idle_days", 0) > 30]
            if long_idle:
                warnings.append(f"存在长期闲置资源: {len(long_idle)} 个")
            
            unrecycled = [r for r in idle_resources if not r.get("recycling_scheduled", False)]
            if unrecycled:
                warnings.append(f"存在未安排回收的闲置资源: {len(unrecycled)} 个")
        
        recycling_tasks = recycle_data.get("recycling_tasks", [])
        if recycling_tasks:
            failed_tasks = [t for t in recycling_tasks if t.get("status") == "failed"]
            if failed_tasks:
                issues.append(f"存在失败的回收任务: {len(failed_tasks)} 个")
            
            pending_tasks = [t for t in recycling_tasks if t.get("status") == "pending"]
            if len(pending_tasks) > 10:
                warnings.append(f"待执行回收任务较多: {len(pending_tasks)} 个")
        
        recycling_effect = recycle_data.get("effect", {})
        if recycling_effect:
            saved_resources = recycling_effect.get("saved_resources", 0)
            if saved_resources <= 0:
                warnings.append("资源回收效果不明显")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.PASS, severity=CheckSeverity.MEDIUM, message="资源回收机制良好",
                details={"idle_resources": len(idle_resources), "recycling_tasks": len(recycling_tasks)}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM,
                message=f"资源回收存在建议: {'; '.join(warnings[:3])}",
                details={"warnings": warnings}, recommendations=["安排闲置资源回收", "优化回收策略"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id, check_name=check_name, ministry=self.ministry,
                status=CheckStatus.FAIL, severity=CheckSeverity.HIGH,
                message=f"资源回收存在问题: {'; '.join(issues)}",
                details={"issues": issues}, recommendations=["修复回收任务", "完善回收策略"]
            )

    def run_all_checks(self, data: dict[str, Any]) -> list[DepartmentCheckResult]:
        """运行所有户部检查"""
        results = []
        results.append(self.check_environment_config(data.get("environment", {})))
        results.append(self.check_resource_allocation(data.get("resources", {})))
        results.append(self.check_dependency_management(data.get("dependencies", {})))
        results.append(self.check_cost_optimization(data.get("cost", {})))
        results.append(self.check_resource_pool_management(data.get("resource_pool", {})))
        results.append(self.check_quota_control(data.get("quota", {})))
        results.append(self.check_resource_recycling(data.get("recycling", {})))
        return results


class EnhancedLiibuChecker:
    """礼部规范制定逻辑深度检查器"""

    def __init__(self):
        self.ministry = Ministry.LIIBU

    def check_coding_standards(self, standards_data: dict[str, Any]) -> DepartmentCheckResult:
        """编码规范深度检查"""
        check_id = "LIIBU-E001"
        check_name = "编码规范深度检查"
        issues, warnings = [], []
        required_standards = {"naming": {"weight": 1.0}, "formatting": {"weight": 1.0}, "documentation": {"weight": 0.9}, "error_handling": {"weight": 1.0}, "logging": {"weight": 0.8}, "testing": {"weight": 0.9}}
        standards = standards_data.get("standards", {})
        for standard in required_standards:
            if standard not in standards:
                issues.append(f"缺少编码规范: {standard}")
            elif not standards[standard].get("enforced", False):
                warnings.append(f"规范 {standard} 未强制执行")
        violations = standards_data.get("violations", [])
        if violations:
            critical_violations = [v for v in violations if v.get("severity") == "critical"]
            if critical_violations:
                issues.append(f"存在严重违规: {len(critical_violations)} 处")
        enforcement = standards_data.get("enforcement", {})
        if not enforcement.get("automated", False):
            warnings.append("编码规范未自动化检查")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="编码规范合规", details={"standards": list(standards.keys())})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"编码规范存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["修复编码规范违规", "启用自动化检查"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"编码规范存在问题: {'; '.join(issues)}", details={"issues": issues}, recommendations=["定义缺失的编码规范", "修复严重违规"])

    def check_documentation_completeness(self, doc_data: dict[str, Any]) -> DepartmentCheckResult:
        """文档完整性深度检查"""
        check_id = "LIIBU-E002"
        check_name = "文档完整性深度检查"
        issues, warnings = [], []
        required_docs = {"api_doc": {"weight": 1.0, "required": True}, "readme": {"weight": 1.0, "required": True}, "changelog": {"weight": 0.8, "required": False}, "architecture": {"weight": 1.0, "required": True}}
        documents = doc_data.get("documents", {})
        for doc_name, doc_config in required_docs.items():
            if doc_name not in documents:
                if doc_config["required"]:
                    issues.append(f"缺少文档: {doc_name}")
                else:
                    warnings.append(f"建议添加文档: {doc_name}")
            elif not documents[doc_name].get("up_to_date", True):
                warnings.append(f"文档未更新: {doc_name}")
        coverage = doc_data.get("coverage", 0)
        if coverage < 80:
            issues.append(f"文档覆盖率不足: {coverage}%")
        elif coverage < 90:
            warnings.append(f"文档覆盖率建议提升: {coverage}%")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.MEDIUM, message="文档完整", details={"documents": list(documents.keys()), "coverage": coverage})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"文档存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["更新过期文档", "补充示例"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"文档存在问题: {'; '.join(issues)}", details={"issues": issues}, recommendations=["补充缺失文档", "提升文档覆盖率"])

    def check_review_process(self, review_data: dict[str, Any]) -> DepartmentCheckResult:
        """审查流程深度检查"""
        check_id = "LIIBU-E003"
        check_name = "审查流程深度检查"
        issues, warnings = [], []
        reviews = review_data.get("reviews", [])
        if not reviews:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无审查记录", recommendations=["建立审查流程"])
        pending_reviews = [r for r in reviews if r.get("status") == "pending"]
        if len(pending_reviews) > 5:
            issues.append(f"待审查项目过多: {len(pending_reviews)} 个")
        elif pending_reviews:
            warnings.append(f"存在待审查项目: {len(pending_reviews)} 个")
        overdue_reviews = [r for r in reviews if r.get("overdue", False)]
        if overdue_reviews:
            issues.append(f"存在逾期审查: {len(overdue_reviews)} 个")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.MEDIUM, message="审查流程正常", details={"total_reviews": len(reviews), "pending": len(pending_reviews)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"审查流程存在建议: {'; '.join(warnings)}", details={"warnings": warnings}, recommendations=["提升代码质量以提高通过率"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"审查流程存在问题: {'; '.join(issues)}", details={"issues": issues}, recommendations=["加快审查进度", "处理逾期审查"])

    def check_standard_version_control(self, version_data: dict[str, Any]) -> DepartmentCheckResult:
        """规范版本控制检查（增强功能）"""
        check_id = "LIIBU-E004"
        check_name = "规范版本控制检查"
        issues, warnings = [], []
        standards_versions = version_data.get("standards_versions", [])
        if not standards_versions:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="未定义规范版本", recommendations=["建立规范版本管理机制"])
        for std_version in standards_versions:
            std_name = std_version.get("name", "unknown")
            current_version = std_version.get("current_version")
            latest_version = std_version.get("latest_version")
            if not current_version:
                issues.append(f"规范 '{std_name}' 未设置当前版本")
            elif latest_version and current_version != latest_version:
                warnings.append(f"规范 '{std_name}' 存在更新版本: {latest_version}")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="规范版本控制良好", details={"standards_count": len(standards_versions)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"规范版本控制存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["更新规范版本", "执行版本迁移"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"规范版本控制存在问题: {'; '.join(issues)}", details={"issues": issues}, recommendations=["设置规范版本", "解决版本兼容问题"])

    def check_compliance_audit(self, audit_data: dict[str, Any]) -> DepartmentCheckResult:
        """合规性审计检查（增强功能）"""
        check_id = "LIIBU-E005"
        check_name = "合规性审计检查"
        issues, warnings = [], []
        compliance_rules = audit_data.get("compliance_rules", [])
        if not compliance_rules:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="未定义合规规则", recommendations=["定义合规检查规则"])
        violations = []
        for rule in compliance_rules:
            rule_name = rule.get("name", "unknown")
            if not rule.get("enabled", False):
                warnings.append(f"合规规则 '{rule_name}' 未启用")
            elif not rule.get("passed", True):
                violations.append(rule_name)
        if violations:
            issues.append(f"存在合规违规: {violations[:5]}")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="合规性审计良好", details={"rules_count": len(compliance_rules)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"合规性审计存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["启用合规规则", "更新审计报告"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"合规性审计存在问题: {'; '.join(issues)}", details={"issues": issues, "violations": violations}, recommendations=["修复合规违规", "重新执行审计"])

    def check_change_tracking(self, tracking_data: dict[str, Any]) -> DepartmentCheckResult:
        """变更追踪检查（增强功能）"""
        check_id = "LIIBU-E006"
        check_name = "变更追踪检查"
        issues, warnings = [], []
        changes = tracking_data.get("changes", [])
        if not changes:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无变更记录", recommendations=["建立变更追踪机制"])
        unapproved_changes = [c for c in changes if not c.get("approved", False)]
        if unapproved_changes:
            issues.append(f"存在未审批的变更: {len(unapproved_changes)} 个")
        changes_without_impact = [c for c in changes if not c.get("impact_assessed", False)]
        if changes_without_impact:
            warnings.append(f"存在未评估影响的变更: {len(changes_without_impact)} 个")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="变更追踪良好", details={"changes_count": len(changes)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"变更追踪存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["评估变更影响", "处理回滚请求"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"变更追踪存在问题: {'; '.join(issues)}", details={"issues": issues}, recommendations=["审批待处理变更", "降低变更失败率"])

    def run_all_checks(self, data: dict[str, Any]) -> list[DepartmentCheckResult]:
        """运行所有礼部检查"""
        results = []
        results.append(self.check_coding_standards(data.get("standards", {})))
        results.append(self.check_documentation_completeness(data.get("documentation", {})))
        results.append(self.check_review_process(data.get("reviews", {})))
        results.append(self.check_standard_version_control(data.get("version_control", {})))
        results.append(self.check_compliance_audit(data.get("compliance", {})))
        results.append(self.check_change_tracking(data.get("change_tracking", {})))
        return results


class EnhancedBingbuChecker:
    """兵部测试先行逻辑深度检查器"""

    def __init__(self):
        self.ministry = Ministry.BINGBU

    def check_test_first_principle(self, test_data: dict[str, Any]) -> DepartmentCheckResult:
        """测试先行原则深度检查"""
        check_id = "BINGBU-E001"
        check_name = "测试先行原则深度检查"
        issues, warnings = [], []
        features = test_data.get("features", [])
        if not features:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无功能测试数据", recommendations=["定义功能测试列表"])
        violations = []
        for feature in features:
            feature_name = feature.get("name", "unknown")
            test_written = feature.get("test_written", False)
            code_written = feature.get("code_written", False)
            if not test_written and code_written:
                violations.append({"feature": feature_name, "type": "no_test"})
                issues.append(f"功能 '{feature_name}' 未遵循测试先行原则")
        tdd_compliance = (len(features) - len(violations)) / len(features) if features else 0
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message=f"测试先行原则执行良好，合规率: {tdd_compliance:.1%}", details={"features_checked": len(features), "tdd_compliance": tdd_compliance})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"测试先行存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings, "tdd_compliance": tdd_compliance}, recommendations=["确保测试在代码之前编写"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"测试先行原则违反: {'; '.join(issues[:3])}", details={"issues": issues, "violations": violations}, recommendations=["补充缺失的测试", "遵循TDD红阶段流程"])

    def check_test_coverage(self, coverage_data: dict[str, Any]) -> DepartmentCheckResult:
        """测试覆盖率深度检查"""
        check_id = "BINGBU-E002"
        check_name = "测试覆盖率深度检查"
        issues, warnings = [], []
        unit_coverage = coverage_data.get("unit_coverage", 0)
        integration_coverage = coverage_data.get("integration_coverage", 0)
        branch_coverage = coverage_data.get("branch_coverage", 0)
        thresholds = {"unit": {"min": 80, "recommended": 90}, "integration": {"min": 60, "recommended": 75}, "branch": {"min": 70, "recommended": 85}}
        if unit_coverage < thresholds["unit"]["min"]:
            issues.append(f"单元测试覆盖率不足: {unit_coverage}%")
        elif unit_coverage < thresholds["unit"]["recommended"]:
            warnings.append(f"单元测试覆盖率建议提升: {unit_coverage}%")
        if integration_coverage < thresholds["integration"]["min"]:
            issues.append(f"集成测试覆盖率不足: {integration_coverage}%")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="测试覆盖率达标", details={"unit_coverage": unit_coverage, "integration_coverage": integration_coverage, "branch_coverage": branch_coverage})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"测试覆盖率存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["补充测试用例", "关注覆盖率趋势"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"测试覆盖率不达标: {'; '.join(issues)}", details={"issues": issues}, recommendations=["增加测试用例", "提升覆盖率"])

    def check_test_quality(self, quality_data: dict[str, Any]) -> DepartmentCheckResult:
        """测试质量深度检查"""
        check_id = "BINGBU-E003"
        check_name = "测试质量深度检查"
        issues, warnings = [], []
        tests = quality_data.get("tests", [])
        if not tests:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无测试数据", recommendations=["定义测试列表"])
        flaky_tests = [t for t in tests if t.get("flaky", False)]
        if flaky_tests:
            warnings.append(f"存在不稳定测试: {len(flaky_tests)} 个")
        slow_tests = [t for t in tests if t.get("duration", 0) > 5]
        if slow_tests:
            warnings.append(f"存在慢测试(>5s): {len(slow_tests)} 个")
        assertions_per_test = quality_data.get("avg_assertions_per_test", 0)
        if assertions_per_test < 2:
            warnings.append("平均断言数较低，建议增加断言")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.MEDIUM, message="测试质量良好", details={"tests_count": len(tests), "flaky_count": len(flaky_tests), "slow_count": len(slow_tests)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"测试质量存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["优化慢测试", "增加断言", "修复不稳定测试"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"测试质量存在问题: {'; '.join(issues)}", details={"issues": issues}, recommendations=["修复不稳定测试", "减少跳过测试", "优化慢测试"])

    def check_tdd_process_integrity(self, tdd_data: dict[str, Any]) -> DepartmentCheckResult:
        """TDD流程完整性检查（增强功能）"""
        check_id = "BINGBU-E004"
        check_name = "TDD流程完整性检查"
        issues, warnings = [], []
        tdd_cycles = tdd_data.get("cycles", [])
        if not tdd_cycles:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无TDD循环数据", recommendations=["记录TDD循环过程"])
        incomplete_cycles = []
        for i, cycle in enumerate(tdd_cycles):
            if not cycle.get("red_phase", {}).get("completed", False):
                incomplete_cycles.append({"cycle": i + 1, "missing": "red"})
            if not cycle.get("green_phase", {}).get("completed", False):
                incomplete_cycles.append({"cycle": i + 1, "missing": "green"})
            if not cycle.get("blue_phase", {}).get("completed", False):
                incomplete_cycles.append({"cycle": i + 1, "missing": "blue"})
        if incomplete_cycles:
            issues.append(f"存在不完整的TDD循环: {len(incomplete_cycles)} 个")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="TDD流程完整", details={"cycles_count": len(tdd_cycles), "complete_cycles": len(tdd_cycles) - len(incomplete_cycles)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"TDD流程存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["优化TDD循环效率", "规范阶段转换"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"TDD流程存在问题: {'; '.join(issues)}", details={"issues": issues, "incomplete_cycles": incomplete_cycles}, recommendations=["完成所有TDD阶段", "遵循红绿蓝循环"])

    def check_test_driven_validation(self, validation_data: dict[str, Any]) -> DepartmentCheckResult:
        """测试驱动验证检查（增强功能）"""
        check_id = "BINGBU-E005"
        check_name = "测试驱动验证检查"
        issues, warnings = [], []
        requirements = validation_data.get("requirements", [])
        if not requirements:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无需求测试数据", recommendations=["建立需求到测试的追溯关系"])
        untested_requirements = [req.get("id") for req in requirements if not req.get("test_cases", [])]
        if untested_requirements:
            issues.append(f"存在未测试的需求: {len(untested_requirements)} 个")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="测试驱动验证良好", details={"requirements_count": len(requirements), "tested_requirements": len(requirements) - len(untested_requirements)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"测试驱动验证存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["提高测试独立性", "验证测试数据质量"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"测试驱动验证存在问题: {'; '.join(issues)}", details={"issues": issues, "untested": untested_requirements}, recommendations=["补充需求测试用例", "建立需求追溯"])

    def check_boundary_conditions(self, boundary_data: dict[str, Any]) -> DepartmentCheckResult:
        """边界条件检查（增强功能）"""
        check_id = "BINGBU-E006"
        check_name = "边界条件检查"
        issues, warnings = [], []
        boundary_tests = boundary_data.get("boundary_tests", [])
        if not boundary_tests:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无边界条件测试数据", recommendations=["添加边界条件测试"])
        uncovered_boundaries = [t.get("type") for t in boundary_tests if not t.get("covered", False)]
        if uncovered_boundaries:
            warnings.append(f"存在未覆盖的边界条件: {uncovered_boundaries[:5]}")
        exception_tests = boundary_data.get("exception_tests", [])
        if exception_tests:
            untested_exceptions = [e for e in exception_tests if not e.get("tested", False)]
            if untested_exceptions:
                issues.append(f"存在未测试的异常情况: {len(untested_exceptions)} 个")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="边界条件测试完整", details={"boundary_tests_count": len(boundary_tests), "exception_tests_count": len(exception_tests)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"边界条件测试存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["补充边界条件测试", "添加极限条件测试"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"边界条件测试存在问题: {'; '.join(issues)}", details={"issues": issues}, recommendations=["补充异常情况测试", "完善边界条件覆盖"])

    def run_all_checks(self, data: dict[str, Any]) -> list[DepartmentCheckResult]:
        """运行所有兵部检查"""
        results = []
        results.append(self.check_test_first_principle(data.get("test_first", {})))
        results.append(self.check_test_coverage(data.get("coverage", {})))
        results.append(self.check_test_quality(data.get("quality", {})))
        results.append(self.check_tdd_process_integrity(data.get("tdd_process", {})))
        results.append(self.check_test_driven_validation(data.get("validation", {})))
        results.append(self.check_boundary_conditions(data.get("boundary", {})))
        return results


class EnhancedGongbuChecker:
    """工部代码实现逻辑深度检查器"""

    def __init__(self):
        self.ministry = Ministry.GONGBU

    def check_code_implementation(self, impl_data: dict[str, Any]) -> DepartmentCheckResult:
        """代码实现深度检查"""
        check_id = "GONGBU-E001"
        check_name = "代码实现深度检查"
        issues, warnings = [], []
        modules = impl_data.get("modules", [])
        if not modules:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无模块数据", recommendations=["定义模块列表"])
        unimplemented = []
        for module in modules:
            module_name = module.get("name", "unknown")
            if not module.get("implemented", False):
                unimplemented.append(module_name)
                issues.append(f"模块 '{module_name}' 未实现")
            complexity = module.get("complexity", 0)
            if complexity > 15:
                issues.append(f"模块 '{module_name}' 复杂度过高: {complexity}")
            elif complexity > 10:
                warnings.append(f"模块 '{module_name}' 复杂度需关注: {complexity}")
        implementation_rate = (len(modules) - len(unimplemented)) / len(modules) if modules else 0
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message=f"代码实现完整，实现率: {implementation_rate:.1%}", details={"modules_count": len(modules), "implementation_rate": implementation_rate})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"代码实现存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings, "implementation_rate": implementation_rate}, recommendations=["处理TODO项", "降低复杂度"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"代码实现存在问题: {'; '.join(issues[:3])}", details={"issues": issues, "unimplemented": unimplemented}, recommendations=["完成未实现的模块", "降低复杂度"])

    def check_code_quality(self, quality_data: dict[str, Any]) -> DepartmentCheckResult:
        """代码质量深度检查"""
        check_id = "GONGBU-E002"
        check_name = "代码质量深度检查"
        issues, warnings = [], []
        code_smells = quality_data.get("code_smells", [])
        if code_smells:
            critical_smells = [s for s in code_smells if s.get("severity") == "critical"]
            if critical_smells:
                issues.append(f"存在严重代码异味: {len(critical_smells)} 处")
            else:
                warnings.append(f"存在代码异味: {len(code_smells)} 处")
        duplications = quality_data.get("duplications", [])
        if duplications:
            warnings.append(f"存在代码重复: {len(duplications)} 处")
        tech_debt = quality_data.get("tech_debt_hours", 0)
        if tech_debt > 40:
            issues.append(f"技术债务过高: {tech_debt} 小时")
        elif tech_debt > 20:
            warnings.append(f"技术债务需关注: {tech_debt} 小时")
        maintainability_index = quality_data.get("maintainability_index", 100)
        if maintainability_index < 50:
            issues.append(f"可维护性指数过低: {maintainability_index}")
        elif maintainability_index < 70:
            warnings.append(f"可维护性指数需提升: {maintainability_index}")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.MEDIUM, message="代码质量良好", details={"tech_debt_hours": tech_debt, "maintainability_index": maintainability_index})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"代码质量存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["重构代码异味", "减少重复代码", "偿还技术债务"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"代码质量存在问题: {'; '.join(issues)}", details={"issues": issues}, recommendations=["修复严重代码异味", "消除重复代码", "偿还技术债务"])

    def check_green_phase_completion(self, green_data: dict[str, Any]) -> DepartmentCheckResult:
        """绿阶段完成深度检查"""
        check_id = "GONGBU-E003"
        check_name = "绿阶段完成深度检查"
        issues, warnings = [], []
        tests = green_data.get("tests", [])
        all_passed = all(t.get("passed", False) for t in tests) if tests else False
        if tests and not all_passed:
            failed_tests = [t for t in tests if not t.get("passed", False)]
            issues.append(f"存在未通过的测试: {len(failed_tests)} 个")
        implementation_complete = green_data.get("implementation_complete", False)
        if not implementation_complete:
            issues.append("代码实现未完成")
        minimal_implementation = green_data.get("minimal_implementation", True)
        if not minimal_implementation:
            warnings.append("实现可能过度设计，建议遵循最小实现原则")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="绿阶段完成，所有测试通过", details={"tests_passed": len([t for t in tests if t.get("passed", False)]) if tests else 0, "implementation_complete": implementation_complete})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"绿阶段存在建议: {'; '.join(warnings)}", details={"warnings": warnings}, recommendations=["简化实现", "通过代码审查"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"绿阶段未完成: {'; '.join(issues)}", details={"issues": issues}, recommendations=["修复失败的测试", "完成代码实现"])

    def check_implementation_standards(self, std_data: dict[str, Any]) -> DepartmentCheckResult:
        """实现规范遵循检查（增强功能）"""
        check_id = "GONGBU-E004"
        check_name = "实现规范遵循检查"
        issues, warnings = [], []
        standards = std_data.get("standards", [])
        if not standards:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无实现规范数据", recommendations=["定义实现规范遵循检查"])
        violations = []
        for standard in standards:
            std_name = standard.get("name", "unknown")
            compliance_rate = standard.get("compliance_rate", 100)
            if compliance_rate < 70:
                issues.append(f"规范 '{std_name}' 遵循率过低: {compliance_rate}%")
                violations.append(std_name)
            elif compliance_rate < 90:
                warnings.append(f"规范 '{std_name}' 遵循率需提升: {compliance_rate}%")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="实现规范遵循良好", details={"standards_count": len(standards)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"实现规范遵循存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["提升规范遵循率", "修正设计模式应用"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"实现规范遵循存在问题: {'; '.join(issues)}", details={"issues": issues, "violations": violations}, recommendations=["提高规范遵循率", "修复违规项"])

    def check_code_review_status(self, review_data: dict[str, Any]) -> DepartmentCheckResult:
        """代码审查状态检查（增强功能）"""
        check_id = "GONGBU-E005"
        check_name = "代码审查状态检查"
        issues, warnings = [], []
        reviews = review_data.get("reviews", [])
        if not reviews:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无代码审查数据", recommendations=["建立代码审查流程"])
        pending_reviews = [r for r in reviews if r.get("status") == "pending"]
        if pending_reviews:
            issues.append(f"存在待处理的代码审查: {len(pending_reviews)} 个")
        unaddressed_comments = []
        for review in reviews:
            comments = review.get("comments", [])
            unaddressed = [c for c in comments if not c.get("addressed", False)]
            if unaddressed:
                unaddressed_comments.extend(unaddressed)
        if unaddressed_comments:
            warnings.append(f"存在未处理的审查意见: {len(unaddressed_comments)} 条")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="代码审查状态良好", details={"reviews_count": len(reviews)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"代码审查存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["处理审查意见", "优化审查效率"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"代码审查存在问题: {'; '.join(issues)}", details={"issues": issues}, recommendations=["完成待处理审查", "处理审查意见"])

    def check_tech_debt_tracking(self, debt_data: dict[str, Any]) -> DepartmentCheckResult:
        """技术债务追踪检查（增强功能）"""
        check_id = "GONGBU-E006"
        check_name = "技术债务追踪检查"
        issues, warnings = [], []
        tech_debts = debt_data.get("tech_debts", [])
        if not tech_debts:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无技术债务记录", recommendations=["建立技术债务追踪机制"])
        high_priority_debts = [d for d in tech_debts if d.get("priority") == "high"]
        if high_priority_debts:
            unscheduled_high = [d for d in high_priority_debts if not d.get("scheduled", False)]
            if unscheduled_high:
                issues.append(f"存在未安排的高优先级技术债务: {len(unscheduled_high)} 个")
        overdue_debts = [d for d in tech_debts if d.get("overdue", False)]
        if overdue_debts:
            warnings.append(f"存在逾期的技术债务: {len(overdue_debts)} 个")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="技术债务追踪良好", details={"debts_count": len(tech_debts), "high_priority_count": len(high_priority_debts)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"技术债务追踪存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["安排技术债务偿还", "控制债务增长"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"技术债务追踪存在问题: {'; '.join(issues)}", details={"issues": issues}, recommendations=["安排高优先级债务偿还", "制定债务管理计划"])

    def run_all_checks(self, data: dict[str, Any]) -> list[DepartmentCheckResult]:
        """运行所有工部检查"""
        results = []
        results.append(self.check_code_implementation(data.get("implementation", {})))
        results.append(self.check_code_quality(data.get("quality", {})))
        results.append(self.check_green_phase_completion(data.get("green_phase", {})))
        results.append(self.check_implementation_standards(data.get("standards", {})))
        results.append(self.check_code_review_status(data.get("code_review", {})))
        results.append(self.check_tech_debt_tracking(data.get("tech_debt", {})))
        return results


class EnhancedXingbuChecker:
    """刑部重构优化逻辑深度检查器"""

    def __init__(self):
        self.ministry = Ministry.XINGBU

    def check_refactoring_necessity(self, refactor_data: dict[str, Any]) -> DepartmentCheckResult:
        """重构必要性深度检查"""
        check_id = "XINGBU-E001"
        check_name = "重构必要性深度检查"
        issues, warnings = [], []
        code_metrics = refactor_data.get("code_metrics", {})
        complexity = code_metrics.get("avg_complexity", 0)
        if complexity > 15:
            issues.append(f"平均复杂度过高: {complexity}")
        elif complexity > 10:
            warnings.append(f"平均复杂度需关注: {complexity}")
        coupling = code_metrics.get("coupling", 0)
        if coupling > 0.7:
            issues.append(f"耦合度过高: {coupling}")
        elif coupling > 0.5:
            warnings.append(f"耦合度需关注: {coupling}")
        cohesion = code_metrics.get("cohesion", 0)
        if cohesion < 0.5:
            issues.append(f"内聚度过低: {cohesion}")
        elif cohesion < 0.7:
            warnings.append(f"内聚度需提升: {cohesion}")
        refactoring_candidates = refactor_data.get("refactoring_candidates", [])
        if len(refactoring_candidates) > 10:
            warnings.append(f"重构候选项较多: {len(refactoring_candidates)} 个")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.MEDIUM, message="代码结构良好，无需紧急重构", details={"candidates_count": len(refactoring_candidates), "complexity": complexity, "coupling": coupling, "cohesion": cohesion})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"存在重构建议: {'; '.join(warnings[:3])}", details={"warnings": warnings, "candidates": refactoring_candidates[:5]}, recommendations=["规划重构任务"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"需要紧急重构: {'; '.join(issues)}", details={"issues": issues, "candidates": refactoring_candidates}, recommendations=["立即启动重构", "降低复杂度", "解耦模块"])

    def check_blue_phase_completion(self, blue_data: dict[str, Any]) -> DepartmentCheckResult:
        """蓝阶段完成深度检查"""
        check_id = "XINGBU-E002"
        check_name = "蓝阶段完成深度检查"
        issues, warnings = [], []
        tests_still_pass = blue_data.get("tests_still_pass", True)
        if not tests_still_pass:
            issues.append("重构后测试失败")
        refactoring_done = blue_data.get("refactoring_done", False)
        if not refactoring_done:
            warnings.append("重构未完成")
        improvements = blue_data.get("improvements", [])
        if not improvements:
            warnings.append("未记录改进项")
        performance_impact = blue_data.get("performance_impact", 0)
        if performance_impact < 0:
            if performance_impact < -10:
                issues.append(f"重构导致性能显著下降: {performance_impact}%")
            else:
                warnings.append(f"重构导致性能下降: {performance_impact}%")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="蓝阶段完成，代码质量提升", details={"improvements": improvements, "performance_impact": performance_impact})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"蓝阶段存在建议: {'; '.join(warnings)}", details={"warnings": warnings}, recommendations=["完成重构", "记录改进项"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"蓝阶段存在问题: {'; '.join(issues)}", details={"issues": issues}, recommendations=["修复测试失败", "回滚性能下降的修改"])

    def check_optimization_opportunities(self, opt_data: dict[str, Any]) -> DepartmentCheckResult:
        """优化机会深度检查"""
        check_id = "XINGBU-E003"
        check_name = "优化机会深度检查"
        issues, warnings = [], []
        performance_issues = opt_data.get("performance_issues", [])
        if performance_issues:
            critical = [p for p in performance_issues if p.get("severity") == "critical"]
            if critical:
                issues.append(f"存在严重性能问题: {len(critical)} 个")
            else:
                warnings.append(f"存在性能问题: {len(performance_issues)} 个")
        memory_issues = opt_data.get("memory_issues", [])
        if memory_issues:
            leaks = [m for m in memory_issues if m.get("type") == "leak"]
            if leaks:
                issues.append(f"存在内存泄漏: {len(leaks)} 个")
            else:
                warnings.append(f"存在内存问题: {len(memory_issues)} 个")
        optimization_suggestions = opt_data.get("suggestions", [])
        if len(optimization_suggestions) > 5:
            warnings.append(f"优化建议较多: {len(optimization_suggestions)} 个")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.MEDIUM, message="代码优化良好", details={"suggestions_count": len(optimization_suggestions)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"存在优化建议: {'; '.join(warnings[:3])}", details={"warnings": warnings, "suggestions": optimization_suggestions[:5]}, recommendations=["考虑优化建议"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"存在优化问题: {'; '.join(issues)}", details={"issues": issues}, recommendations=["修复性能问题", "解决内存问题", "修复安全问题"])

    def check_refactoring_risk_assessment(self, risk_data: dict[str, Any]) -> DepartmentCheckResult:
        """重构风险评估检查（增强功能）"""
        check_id = "XINGBU-E004"
        check_name = "重构风险评估检查"
        issues, warnings = [], []
        risks = risk_data.get("risks", [])
        if not risks:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无重构风险数据", recommendations=["进行重构风险评估"])
        high_risks = [r for r in risks if r.get("level") == "high"]
        if high_risks:
            unmitigated_high = [r for r in high_risks if not r.get("mitigated", False)]
            if unmitigated_high:
                issues.append(f"存在未缓解的高风险: {len(unmitigated_high)} 个")
        rollback_plan = risk_data.get("rollback_plan", {})
        if not rollback_plan.get("exists", False):
            warnings.append("未制定回滚计划")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="重构风险评估良好", details={"risks_count": len(risks), "high_risks": len(high_risks)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"重构风险评估存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["缓解识别的风险", "制定回滚计划"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"重构风险评估存在问题: {'; '.join(issues)}", details={"issues": issues, "high_risks": high_risks}, recommendations=["立即缓解高风险", "完善风险应对措施"])

    def check_performance_regression(self, perf_data: dict[str, Any]) -> DepartmentCheckResult:
        """性能回归检查（增强功能）"""
        check_id = "XINGBU-E005"
        check_name = "性能回归检查"
        issues, warnings = [], []
        benchmarks = perf_data.get("benchmarks", [])
        if not benchmarks:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无性能基准数据", recommendations=["建立性能基准测试"])
        regressions = []
        for benchmark in benchmarks:
            name = benchmark.get("name", "unknown")
            current = benchmark.get("current", 0)
            baseline = benchmark.get("baseline", 0)
            threshold = benchmark.get("threshold", 0.1)
            if baseline > 0:
                regression_rate = (current - baseline) / baseline
                if regression_rate > threshold:
                    regressions.append({"name": name, "regression": regression_rate})
        if regressions:
            severe_regressions = [r for r in regressions if r["regression"] > 0.2]
            if severe_regressions:
                issues.append(f"存在严重性能回归: {[r['name'] for r in severe_regressions]}")
            else:
                warnings.append(f"存在性能回归: {len(regressions)} 处")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="性能无回归", details={"benchmarks_count": len(benchmarks)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"性能回归存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings, "regressions": regressions}, recommendations=["处理性能告警", "优化性能回归点"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"性能回归存在问题: {'; '.join(issues)}", details={"issues": issues, "regressions": regressions}, recommendations=["修复严重性能回归", "优化关键路径"])

    def check_code_evolution_tracking(self, evolution_data: dict[str, Any]) -> DepartmentCheckResult:
        """代码演化追踪检查（增强功能）"""
        check_id = "XINGBU-E006"
        check_name = "代码演化追踪检查"
        issues, warnings = [], []
        evolution_history = evolution_data.get("history", [])
        if not evolution_history:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message="无代码演化历史数据", recommendations=["建立代码演化追踪机制"])
        entropy_increase = evolution_data.get("entropy", {})
        if entropy_increase:
            entropy_rate = entropy_increase.get("rate", 0)
            if entropy_rate > 0.3:
                issues.append(f"代码熵增过快: {entropy_rate:.1%}")
            elif entropy_rate > 0.2:
                warnings.append(f"代码熵增需关注: {entropy_rate:.1%}")
        stability_metrics = evolution_data.get("stability", {})
        if stability_metrics:
            stability_score = stability_metrics.get("score", 100)
            if stability_score < 50:
                issues.append(f"代码稳定性过低: {stability_score}")
            elif stability_score < 70:
                warnings.append(f"代码稳定性需提升: {stability_score}")
        if not issues and not warnings:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.PASS, severity=CheckSeverity.HIGH, message="代码演化追踪良好", details={"history_count": len(evolution_history)})
        elif not issues:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.WARNING, severity=CheckSeverity.MEDIUM, message=f"代码演化追踪存在建议: {'; '.join(warnings[:3])}", details={"warnings": warnings}, recommendations=["控制代码熵增", "优化热点文件"])
        else:
            return DepartmentCheckResult(check_id=check_id, check_name=check_name, ministry=self.ministry, status=CheckStatus.FAIL, severity=CheckSeverity.HIGH, message=f"代码演化追踪存在问题: {'; '.join(issues)}", details={"issues": issues}, recommendations=["降低熵增速度", "提升代码稳定性"])

    def run_all_checks(self, data: dict[str, Any]) -> list[DepartmentCheckResult]:
        """运行所有刑部检查"""
        results = []
        results.append(self.check_refactoring_necessity(data.get("refactoring", {})))
        results.append(self.check_blue_phase_completion(data.get("blue_phase", {})))
        results.append(self.check_optimization_opportunities(data.get("optimization", {})))
        results.append(self.check_refactoring_risk_assessment(data.get("risk", {})))
        results.append(self.check_performance_regression(data.get("performance", {})))
        results.append(self.check_code_evolution_tracking(data.get("evolution", {})))
        return results


class MinistryCoordinationChecker:
    """六部协调检查器"""

    def __init__(self):
        self.coordination_issues: list[MinistryCoordinationIssue] = []

    def check_tdd_sequence(self, data: dict[str, Any]) -> list[MinistryCoordinationIssue]:
        """TDD顺序检查"""
        issues = []
        tdd_sequence = data.get("tdd_sequence", [])
        if not tdd_sequence:
            return issues
        expected_order = [(Ministry.BINGBU, "red"), (Ministry.GONGBU, "green"), (Ministry.XINGBU, "blue")]
        for i, step in enumerate(tdd_sequence):
            ministry = Ministry(step.get("ministry")) if step.get("ministry") else None
            phase = step.get("phase")
            if i < len(expected_order):
                expected_ministry, expected_phase = expected_order[i]
                if ministry != expected_ministry or phase != expected_phase:
                    issues.append(MinistryCoordinationIssue(
                        issue_id=f"TDD-SEQ-{i+1}",
                        from_ministry=ministry if ministry else Ministry.BINGBU,
                        to_ministry=expected_ministry,
                        issue_type="sequence_violation",
                        description=f"TDD顺序错误: 期望 {expected_ministry.value}/{expected_phase}, 实际 {ministry.value if ministry else 'unknown'}/{phase}",
                        impact="可能导致TDD流程混乱",
                        suggested_fix="按照兵部->工部->刑部顺序执行"
                    ))
        return issues

    def check_handoff_integrity(self, data: dict[str, Any]) -> list[MinistryCoordinationIssue]:
        """部门交接完整性检查"""
        issues = []
        handoffs = data.get("handoffs", [])
        for handoff in handoffs:
            from_ministry = handoff.get("from")
            to_ministry = handoff.get("to")
            data_transferred = handoff.get("data_transferred", True)
            acknowledged = handoff.get("acknowledged", True)
            if not data_transferred:
                issues.append(MinistryCoordinationIssue(
                    issue_id=f"HANDOFF-{from_ministry}-{to_ministry}",
                    from_ministry=Ministry(from_ministry) if from_ministry else Ministry.BINGBU,
                    to_ministry=Ministry(to_ministry) if to_ministry else Ministry.GONGBU,
                    issue_type="data_transfer_failure",
                    description=f"部门交接数据未传递: {from_ministry} -> {to_ministry}",
                    impact="可能导致后续部门缺少必要数据",
                    suggested_fix="确保交接数据完整传递"
                ))
            if not acknowledged:
                issues.append(MinistryCoordinationIssue(
                    issue_id=f"HANDOFF-ACK-{from_ministry}-{to_ministry}",
                    from_ministry=Ministry(from_ministry) if from_ministry else Ministry.BINGBU,
                    to_ministry=Ministry(to_ministry) if to_ministry else Ministry.GONGBU,
                    issue_type="acknowledgment_missing",
                    description=f"部门交接未确认: {from_ministry} -> {to_ministry}",
                    impact="可能导致交接状态不明确",
                    suggested_fix="确认交接完成"
                ))
        return issues

    def check_cross_ministry_dependencies(self, data: dict[str, Any]) -> list[MinistryCoordinationIssue]:
        """跨部门依赖检查"""
        issues = []
        dependencies = data.get("cross_ministry_dependencies", [])
        for dep in dependencies:
            source = dep.get("source")
            target = dep.get("target")
            dep_type = dep.get("type")
            satisfied = dep.get("satisfied", True)
            if not satisfied:
                issues.append(MinistryCoordinationIssue(
                    issue_id=f"DEP-{source}-{target}",
                    from_ministry=Ministry(source) if source else Ministry.LIBU,
                    to_ministry=Ministry(target) if target else Ministry.HUBU,
                    issue_type="dependency_unsatisfied",
                    description=f"跨部门依赖未满足: {source} -> {target} ({dep_type})",
                    impact="可能影响下游部门工作",
                    suggested_fix="满足跨部门依赖要求"
                ))
        return issues


class DepartmentLogicChecker:
    """六部执行逻辑检查器主类"""

    def __init__(self, output_dir: Path = None):
        if output_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                self.output_dir = _path_mgr.get_output_path(OutputType.REPORT, subdirectory="department_checks")
            except Exception:
                self.output_dir = get_path_config().REPORTS_DIR / "department_checks"
        else:
            self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkers = {
            Ministry.LIBU: EnhancedLibuChecker(),
            Ministry.HUBU: EnhancedHubuChecker(),
            Ministry.LIIBU: EnhancedLiibuChecker(),
            Ministry.BINGBU: EnhancedBingbuChecker(),
            Ministry.GONGBU: EnhancedGongbuChecker(),
            Ministry.XINGBU: EnhancedXingbuChecker(),
        }
        self.coordination_checker = MinistryCoordinationChecker()

    def check_all(self, data: dict[str, Any]) -> DepartmentLogicReport:
        """执行所有部门的检查"""
        all_results: list[DepartmentCheckResult] = []
        for ministry, checker in self.checkers.items():
            ministry_data = data.get(ministry.value, {})
            all_results.extend(checker.run_all_checks(ministry_data))
        coordination_issues = []
        coordination_issues.extend(self.coordination_checker.check_tdd_sequence(data))
        coordination_issues.extend(self.coordination_checker.check_handoff_integrity(data))
        coordination_issues.extend(self.coordination_checker.check_cross_ministry_dependencies(data))
        passed = sum(1 for r in all_results if r.status == CheckStatus.PASS)
        failed = sum(1 for r in all_results if r.status == CheckStatus.FAIL)
        warnings = sum(1 for r in all_results if r.status == CheckStatus.WARNING)
        skipped = sum(1 for r in all_results if r.status == CheckStatus.SKIP)
        if failed > 0:
            overall_status = CheckStatus.FAIL
        elif warnings > 0 or coordination_issues:
            overall_status = CheckStatus.WARNING
        else:
            overall_status = CheckStatus.PASS
        by_ministry: dict[str, dict[str, int]] = {}
        for ministry in Ministry:
            ministry_results = [r for r in all_results if r.ministry == ministry]
            by_ministry[ministry.value] = {
                "total": len(ministry_results),
                "passed": sum(1 for r in ministry_results if r.status == CheckStatus.PASS),
                "failed": sum(1 for r in ministry_results if r.status == CheckStatus.FAIL),
                "warnings": sum(1 for r in ministry_results if r.status == CheckStatus.WARNING)
            }
        summary = self._generate_summary(all_results, by_ministry, coordination_issues)
        report = DepartmentLogicReport(
            report_id=f"DLC-E-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            total_checks=len(all_results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            skipped=skipped,
            results=all_results,
            by_ministry=by_ministry,
            coordination_issues=coordination_issues,
            summary=summary,
            overall_status=overall_status
        )
        return report

    def check_ministry(self, ministry: Ministry, data: dict[str, Any]) -> list[DepartmentCheckResult]:
        """执行指定部门的检查"""
        checker = self.checkers.get(ministry)
        if checker:
            ministry_data = data.get(ministry.value, {})
            return checker.run_all_checks(ministry_data)
        return []

    def _generate_summary(self, results: list[DepartmentCheckResult], by_ministry: dict, coordination_issues: list[MinistryCoordinationIssue]) -> dict[str, Any]:
        """生成检查摘要"""
        critical_issues = [
            {"check_id": r.check_id, "ministry": r.ministry.value, "message": r.message}
            for r in results
            if r.status == CheckStatus.FAIL and r.severity == CheckSeverity.CRITICAL
        ]
        all_recommendations = []
        for result in results:
            all_recommendations.extend(result.recommendations)
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        return {
            "by_ministry": by_ministry,
            "critical_issues": critical_issues,
            "coordination_issues_count": len(coordination_issues),
            "recommendations": unique_recommendations[:10]
        }

    def save_report(self, report: DepartmentLogicReport, output_path: Path = None) -> Path:
        """保存检查报告"""
        output_path = output_path or self.output_dir / f"department_logic_report_{report.report_id}.json"
        report_dict = {
            "report_id": report.report_id,
            "generated_at": report.generated_at,
            "total_checks": report.total_checks,
            "passed": report.passed,
            "failed": report.failed,
            "warnings": report.warnings,
            "skipped": report.skipped,
            "overall_status": report.overall_status.value,
            "results": [
                {
                    "check_id": r.check_id,
                    "check_name": r.check_name,
                    "ministry": r.ministry.value,
                    "status": r.status.value,
                    "severity": r.severity.value,
                    "message": r.message,
                    "details": r.details,
                    "recommendations": r.recommendations,
                    "timestamp": r.timestamp
                }
                for r in report.results
            ],
            "by_ministry": report.by_ministry,
            "coordination_issues": [
                {
                    "issue_id": ci.issue_id,
                    "from_ministry": ci.from_ministry.value,
                    "to_ministry": ci.to_ministry.value,
                    "issue_type": ci.issue_type,
                    "description": ci.description,
                    "impact": ci.impact,
                    "suggested_fix": ci.suggested_fix
                }
                for ci in report.coordination_issues
            ],
            "summary": report.summary
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        logger.info(f"报告已保存: {output_path}")
        return output_path

    def print_report(self, report: DepartmentLogicReport):
        """打印检查报告"""
        print("\n" + "=" * 70)
        print("六部执行逻辑检查报告（增强版）")
        print("=" * 70)
        print(f"报告ID: {report.report_id}")
        print(f"生成时间: {report.generated_at}")
        print(f"总体状态: {report.overall_status.value.upper()}")
        print(f"\n检查统计:")
        print(f"  总检查项: {report.total_checks}")
        print(f"  通过: {report.passed}")
        print(f"  失败: {report.failed}")
        print(f"  警告: {report.warnings}")
        print(f"  跳过: {report.skipped}")
        print("\n" + "-" * 70)
        print("各部门检查结果:")
        for ministry in Ministry:
            ministry_results = [r for r in report.results if r.ministry == ministry]
            if ministry_results:
                print(f"\n  {ministry.value.upper()}:")
                for result in ministry_results:
                    status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
                    print(f"    [{status_symbol}] {result.check_name}: {result.message}")
        if report.coordination_issues:
            print("\n" + "-" * 70)
            print("协调问题:")
            for issue in report.coordination_issues:
                print(f"  - [{issue.issue_id}] {issue.from_ministry.value} -> {issue.to_ministry.value}")
                print(f"    类型: {issue.issue_type}")
                print(f"    描述: {issue.description}")
                print(f"    建议: {issue.suggested_fix}")
        if report.summary.get("critical_issues"):
            print("\n" + "-" * 70)
            print("严重问题:")
            for issue in report.summary["critical_issues"]:
                print(f"  - [{issue['check_id']}] ({issue['ministry']}) {issue['message']}")
        if report.summary.get("recommendations"):
            print("\n" + "-" * 70)
            print("改进建议:")
            for rec in report.summary["recommendations"][:5]:
                print(f"  - {rec}")
        print("\n" + "=" * 70)


def load_sample_data() -> dict[str, Any]:
    """加载示例数据"""
    return {
        "libu": {"assignment": {"agents": [{"id": "agent-1", "name": "开发者A", "max_concurrent_tasks": 3, "capabilities": ["python", "vue"]}], "tasks": [{"id": "task-1", "name": "用户注册", "required_capabilities": ["python"]}], "assignments": [{"agent_id": "agent-1", "task_id": "task-1"}]}, "skills": {"required_skills": ["python"], "available_skills": ["python"], "skill_scores": {"python": 0.9}}, "load": {"agent_loads": {"agent-1": 0.6}}, "scheduling": {"schedule": [{"task_id": "task-1", "start_time": "2026-03-30T10:00:00", "assigned_agent": "agent-1"}]}, "priority": {"tasks": [{"id": "task-1", "priority": "high"}]}, "dependencies": {"tasks": [{"id": "task-1"}], "dependencies": {}}, "execution_order": {"execution_plan": [{"task_id": "task-1"}]}},
        "hubu": {"environment": {"environments": {"development": {"database": "sqlite"}, "testing": {"database": "postgresql"}, "production": {"database": "postgresql"}}}, "resources": {"resources": {"cpu": 16, "memory": 32}, "allocations": {"cpu": 10, "memory": 20}, "utilization": {"cpu": 0.6, "memory": 0.5}}, "dependencies": {"dependencies": [{"name": "fastapi", "version": "0.100.0"}]}, "cost": {"budget": 10000, "actual_cost": 8000}, "resource_pool": {"pools": [{"name": "compute-pool", "type": "compute", "capacity": {"cpu": 8}, "used": {"cpu": 5}, "isolation": {"enabled": True}, "monitoring": {"enabled": True}}]}, "quota": {"quotas": [{"name": "api-calls", "limit": 10000, "used": 5000}]}, "recycling": {"policy": {"enabled": True}, "idle_resources": [], "recycling_tasks": []}},
        "liibu": {"standards": {"standards": {"naming": {"enforced": True}, "formatting": {"enforced": True}}, "violations": [], "enforcement": {"automated": True}}, "documentation": {"documents": {"api_doc": {"up_to_date": True}, "readme": {"up_to_date": True}}, "coverage": 85}, "reviews": {"reviews": [{"id": "r-1", "status": "approved"}]}, "version_control": {"standards_versions": [{"name": "coding-standard", "current_version": "1.0"}]}, "compliance": {"compliance_rules": [{"name": "security-rule", "enabled": True, "passed": True}]}, "change_tracking": {"changes": [{"id": "c-1", "approved": True, "impact_assessed": True}]}},
        "bingbu": {"test_first": {"features": [{"name": "用户注册", "test_written": True, "code_written": True, "test_before_code": True}]}, "coverage": {"unit_coverage": 85, "integration_coverage": 70, "branch_coverage": 82}, "quality": {"tests": [{"name": "test_register", "flaky": False, "duration": 0.5}], "avg_assertions_per_test": 3}, "tdd_process": {"cycles": [{"red_phase": {"completed": True}, "green_phase": {"completed": True}, "blue_phase": {"completed": True}}]}, "validation": {"requirements": [{"id": "req-1", "test_cases": ["test-1"]}]}, "boundary": {"boundary_tests": [{"type": "edge-case", "covered": True}]}},
        "gongbu": {"implementation": {"modules": [{"name": "user_service", "implemented": True, "complexity": 8}]}, "quality": {"code_smells": [], "duplications": [], "tech_debt_hours": 5, "maintainability_index": 85}, "green_phase": {"tests": [{"name": "test_register", "passed": True}], "implementation_complete": True}, "standards": {"standards": [{"name": "naming", "compliance_rate": 95}]}, "code_review": {"reviews": [{"id": "r-1", "status": "approved"}]}, "tech_debt": {"tech_debts": [{"id": "d-1", "priority": "medium", "scheduled": True}]}},
        "xingbu": {"refactoring": {"code_metrics": {"avg_complexity": 8, "coupling": 0.4, "cohesion": 0.8}, "refactoring_candidates": []}, "blue_phase": {"tests_still_pass": True, "refactoring_done": True, "improvements": ["优化了代码结构"], "performance_impact": 5}, "optimization": {"performance_issues": [], "memory_issues": [], "suggestions": []}, "risk": {"risks": [{"id": "r-1", "level": "low", "mitigated": True}], "rollback_plan": {"exists": True}}, "performance": {"benchmarks": [{"name": "api-response", "current": 100, "baseline": 100}]}, "evolution": {"history": [{"version": "1.0"}], "entropy": {"rate": 0.1}, "stability": {"score": 85}}}
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="六部执行逻辑检查器（增强版）")
    parser.add_argument("--check-all", action="store_true", help="执行所有部门检查")
    parser.add_argument("--check-libu", action="store_true", help="执行吏部检查")
    parser.add_argument("--check-hubu", action="store_true", help="执行户部检查")
    parser.add_argument("--check-liibu", action="store_true", help="执行礼部检查")
    parser.add_argument("--check-bingbu", action="store_true", help="执行兵部检查")
    parser.add_argument("--check-gongbu", action="store_true", help="执行工部检查")
    parser.add_argument("--check-xingbu", action="store_true", help="执行刑部检查")
    parser.add_argument("--data", type=str, help="检查数据文件路径（JSON格式）")
    parser.add_argument("--output", type=str, help="报告输出路径")
    args = parser.parse_args()

    if args.data:
        with open(args.data, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = load_sample_data()

    checker = DepartmentLogicChecker()

    if args.check_all:
        report = checker.check_all(data)
        checker.print_report(report)
        if args.output:
            checker.save_report(report, Path(args.output))
    elif args.check_libu:
        results = checker.check_ministry(Ministry.LIBU, data)
        for result in results:
            print(f"[{result.status.value}] {result.check_name}: {result.message}")
    elif args.check_hubu:
        results = checker.check_ministry(Ministry.HUBU, data)
        for result in results:
            print(f"[{result.status.value}] {result.check_name}: {result.message}")
    elif args.check_liibu:
        results = checker.check_ministry(Ministry.LIIBU, data)
        for result in results:
            print(f"[{result.status.value}] {result.check_name}: {result.message}")
    elif args.check_bingbu:
        results = checker.check_ministry(Ministry.BINGBU, data)
        for result in results:
            print(f"[{result.status.value}] {result.check_name}: {result.message}")
    elif args.check_gongbu:
        results = checker.check_ministry(Ministry.GONGBU, data)
        for result in results:
            print(f"[{result.status.value}] {result.check_name}: {result.message}")
    elif args.check_xingbu:
        results = checker.check_ministry(Ministry.XINGBU, data)
        for result in results:
            print(f"[{result.status.value}] {result.check_name}: {result.message}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
