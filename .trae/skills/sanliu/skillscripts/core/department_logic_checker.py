#!/usr/bin/env python3
"""
六部执行逻辑检查器 - Sanliu 技能

功能：
- 吏部调度逻辑验证
- 户部资源管理逻辑验证
- 礼部规范制定逻辑验证
- 兵部测试先行逻辑验证
- 工部代码实现逻辑验证
- 刑部重构优化逻辑验证

使用方法：
    python scripts/department_logic_checker.py --check-all
    python scripts/department_logic_checker.py --check-libu
    python scripts/department_logic_checker.py --check-hubu
    python scripts/department_logic_checker.py --check-liibu
    python scripts/department_logic_checker.py --check-bingbu
    python scripts/department_logic_checker.py --check-gongbu
    python scripts/department_logic_checker.py --check-xingbu
"""

import argparse
import json
import logging
import sys
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
        logging.FileHandler('department_logic_checker.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class Ministry(Enum):
    LIBU = "libu"
    HUBU = "hubu"
    LIIBU = "liibu"
    BINGBU = "bingbu"
    XINGBU = "xingbu"
    GONGBU = "gongbu"


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
class DepartmentCheckResult:
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
class DepartmentLogicReport:
    report_id: str
    generated_at: str
    total_checks: int
    passed: int
    failed: int
    warnings: int
    skipped: int
    results: list[DepartmentCheckResult]
    by_ministry: dict[str, dict[str, int]]
    summary: dict[str, Any]
    overall_status: CheckStatus


class LibuLogicChecker:
    """吏部调度逻辑检查器"""

    def __init__(self):
        self.ministry = Ministry.LIBU

    def check_agent_assignment(self, assignment_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "LIBU-001"
        check_name = "Agent分配检查"
        
        issues = []
        agents = assignment_data.get("agents", [])
        tasks = assignment_data.get("tasks", [])
        
        if not agents:
            issues.append("未定义可用Agent")
        
        if not tasks:
            issues.append("未定义任务列表")
        
        assignments = assignment_data.get("assignments", [])
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
                overloaded_agents.append(agent_id)
        
        if overloaded_agents:
            issues.append(f"Agent负载过高: {overloaded_agents}")
        
        if not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="Agent分配合理",
                details={
                    "agents_count": len(agents),
                    "tasks_count": len(tasks),
                    "assignments_count": len(assignments)
                }
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"Agent分配存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["重新分配任务", "增加Agent数量", "调整负载均衡"]
            )

    def check_skill_matching(self, skill_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "LIBU-002"
        check_name = "技能匹配检查"
        
        issues = []
        warnings = []
        
        required_skills = skill_data.get("required_skills", [])
        available_skills = skill_data.get("available_skills", [])
        
        missing_skills = []
        for skill in required_skills:
            if skill not in available_skills:
                missing_skills.append(skill)
        
        if missing_skills:
            issues.append(f"缺少必要技能: {missing_skills}")
        
        skill_scores = skill_data.get("skill_scores", {})
        low_score_skills = [
            skill for skill, score in skill_scores.items()
            if score < 0.6
        ]
        if low_score_skills:
            warnings.append(f"技能熟练度较低: {low_score_skills}")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="技能匹配良好",
                details={
                    "required_skills": required_skills,
                    "available_skills": available_skills
                }
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"技能匹配存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["提升技能熟练度"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"技能匹配存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["补充缺失技能", "培训或引入新Agent"]
            )

    def check_load_balance(self, load_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "LIBU-003"
        check_name = "负载均衡检查"
        
        issues = []
        warnings = []
        
        agent_loads = load_data.get("agent_loads", {})
        
        if not agent_loads:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="无负载数据",
                recommendations=["收集Agent负载数据"]
            )
        
        loads = list(agent_loads.values())
        avg_load = sum(loads) / len(loads) if loads else 0
        
        imbalance_threshold = 0.3
        for agent_id, load in agent_loads.items():
            deviation = abs(load - avg_load) / avg_load if avg_load > 0 else 0
            if deviation > imbalance_threshold:
                warnings.append(f"Agent {agent_id} 负载偏离均值 {deviation:.1%}")
        
        max_load = max(loads) if loads else 0
        min_load = min(loads) if loads else 0
        
        if max_load > 0.9:
            issues.append(f"存在过载Agent，负载率: {max_load:.1%}")
        
        if min_load < 0.2 and max_load > 0.5:
            warnings.append("负载分布不均，存在空闲Agent")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message=f"负载均衡良好，平均负载: {avg_load:.1%}",
                details={
                    "avg_load": avg_load,
                    "max_load": max_load,
                    "min_load": min_load
                }
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"负载均衡存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["重新分配任务以平衡负载"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"负载均衡存在问题: {'; '.join(issues)}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["紧急调整任务分配", "增加Agent资源"]
            )

    def check_agent_assignment_rationality(self, assignment_data: dict[str, Any]) -> DepartmentCheckResult:
        """
        检查Agent分配合理性（增强版）
        
        验证Agent分配是否合理：
        - Agent能力匹配
        - Agent负载均衡
        - Agent可用性
        - Agent技能覆盖
        - Agent协作关系
        """
        check_id = "LIBU-004"
        check_name = "Agent分配合理性检查（增强版）"
        
        issues = []
        warnings = []
        
        agents = assignment_data.get("agents", [])
        tasks = assignment_data.get("tasks", [])
        assignments = assignment_data.get("assignments", [])
        
        if not agents:
            issues.append("未定义可用Agent")
        else:
            for agent in agents:
                agent_id = agent.get("id", "unknown")
                capabilities = agent.get("capabilities", [])
                if not capabilities:
                    warnings.append(f"Agent '{agent_id}' 未定义能力列表")
                
                availability = agent.get("availability", 1.0)
                if availability < 0.5:
                    warnings.append(f"Agent '{agent_id}' 可用性较低: {availability:.0%}")
                
                max_tasks = agent.get("max_concurrent_tasks", 3)
                assigned_count = sum(1 for a in assignments if a.get("agent_id") == agent_id)
                if assigned_count > max_tasks:
                    issues.append(f"Agent '{agent_id}' 超载: {assigned_count}/{max_tasks}")
                elif assigned_count > max_tasks * 0.9:
                    warnings.append(f"Agent '{agent_id}' 接近满载: {assigned_count}/{max_tasks}")
        
        if tasks:
            unassigned_tasks = []
            for task in tasks:
                task_id = task.get("id")
                assigned = any(a.get("task_id") == task_id for a in assignments)
                if not assigned:
                    unassigned_tasks.append(task_id)
            
            if unassigned_tasks:
                issues.append(f"存在未分配任务: {unassigned_tasks[:5]}")
        
        if agents and tasks:
            for task in tasks:
                task_id = task.get("id", "unknown")
                required_skills = task.get("required_skills", [])
                if required_skills:
                    assignment = next((a for a in assignments if a.get("task_id") == task_id), None)
                    if assignment:
                        agent = next((a for a in agents if a.get("id") == assignment.get("agent_id")), None)
                        if agent:
                            agent_skills = agent.get("skills", [])
                            missing_skills = [s for s in required_skills if s not in agent_skills]
                            if missing_skills:
                                warnings.append(f"任务 '{task_id}' 分配的Agent缺少技能: {missing_skills}")
        
        collaborations = assignment_data.get("collaborations", [])
        if collaborations:
            for collab in collaborations:
                agent1 = collab.get("agent1")
                agent2 = collab.get("agent2")
                compatibility = collab.get("compatibility", 1.0)
                if compatibility < 0.5:
                    warnings.append(f"Agent '{agent1}' 和 '{agent2}' 协作兼容性较低: {compatibility:.0%}")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="Agent分配合理性检查通过",
                details={
                    "agents_count": len(agents),
                    "tasks_count": len(tasks),
                    "assignments_count": len(assignments)
                }
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"Agent分配合理性存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["优化Agent负载", "补充Agent技能"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"Agent分配合理性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["增加Agent数量", "调整任务分配"]
            )

    def check_task_priority_correctness(self, priority_data: dict[str, Any]) -> DepartmentCheckResult:
        """
        检查任务优先级正确性（增强版）
        
        验证任务优先级是否正确：
        - 优先级值有效性
        - 优先级依赖关系
        - 优先级冲突检测
        - 优先级分布合理性
        - 优先级变更追踪
        """
        check_id = "LIBU-005"
        check_name = "任务优先级正确性检查（增强版）"
        
        issues = []
        warnings = []
        
        tasks = priority_data.get("tasks", [])
        if not tasks:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="无任务数据",
                recommendations=["定义任务列表"]
            )
        
        valid_priorities = ["critical", "high", "medium", "low", "p0", "p1", "p2", "p3"]
        priority_order = {
            "critical": 0, "p0": 0,
            "high": 1, "p1": 1,
            "medium": 2, "p2": 2,
            "low": 3, "p3": 3
        }
        
        for i, task in enumerate(tasks):
            task_id = task.get("id", f"TASK-{i+1}")
            priority = task.get("priority", "").lower()
            
            if not priority:
                issues.append(f"任务 '{task_id}' 未设置优先级")
            elif priority not in valid_priorities:
                issues.append(f"任务 '{task_id}' 优先级值无效: {priority}")
            
            depends_on = task.get("depends_on", [])
            for dep_id in depends_on:
                dep_task = next((t for t in tasks if t.get("id") == dep_id), None)
                if dep_task:
                    dep_priority = dep_task.get("priority", "medium").lower()
                    if priority_order.get(priority, 2) < priority_order.get(dep_priority, 2):
                        issues.append(f"任务 '{task_id}' 优先级高于依赖任务 '{dep_id}'，可能导致阻塞")
        
        priority_distribution = {}
        for task in tasks:
            p = task.get("priority", "medium").lower()
            priority_distribution[p] = priority_distribution.get(p, 0) + 1
        
        high_priority_count = (priority_distribution.get("critical", 0) + 
                               priority_distribution.get("high", 0) + 
                               priority_distribution.get("p0", 0) + 
                               priority_distribution.get("p1", 0))
        high_priority_ratio = high_priority_count / len(tasks) if tasks else 0
        
        if high_priority_ratio > 0.6:
            warnings.append(f"高优先级任务占比过高: {high_priority_ratio:.0%}，可能导致资源分散")
        elif high_priority_ratio < 0.1:
            warnings.append(f"高优先级任务占比过低: {high_priority_ratio:.0%}，可能需要重新评估")
        
        priority_changes = priority_data.get("priority_changes", [])
        if priority_changes:
            frequent_changes = [c for c in priority_changes if c.get("change_count", 0) > 3]
            if frequent_changes:
                warnings.append(f"存在频繁变更优先级的任务: {[c.get('task_id') for c in frequent_changes]}")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="任务优先级正确性检查通过",
                details={
                    "tasks_count": len(tasks),
                    "priority_distribution": priority_distribution
                }
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"任务优先级正确性存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["调整优先级分布", "稳定优先级设置"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"任务优先级正确性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["设置有效优先级", "解决优先级冲突"]
            )

    def run_all_checks(self, data: dict[str, Any]) -> list[DepartmentCheckResult]:
        results = []
        results.append(self.check_agent_assignment(data.get("assignment", {})))
        results.append(self.check_skill_matching(data.get("skills", {})))
        results.append(self.check_load_balance(data.get("load", {})))
        results.append(self.check_agent_assignment_rationality(data.get("assignment_enhanced", {})))
        results.append(self.check_task_priority_correctness(data.get("priority", {})))
        return results


class HubuLogicChecker:
    """户部资源管理逻辑检查器"""

    def __init__(self):
        self.ministry = Ministry.HUBU

    def check_environment_config(self, env_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "HUBU-001"
        check_name = "环境配置检查"
        
        issues = []
        warnings = []
        
        required_envs = ["development", "testing", "production"]
        environments = env_data.get("environments", {})
        
        for env in required_envs:
            if env not in environments:
                issues.append(f"缺少环境配置: {env}")
        
        for env_name, env_config in environments.items():
            if "database" not in env_config:
                issues.append(f"环境 {env_name} 缺少数据库配置")
            if "cache" not in env_config:
                warnings.append(f"环境 {env_name} 缺少缓存配置")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="环境配置完整",
                details={"environments": list(environments.keys())}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"环境配置存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["完善环境配置"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"环境配置存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["补充缺失的环境配置"]
            )

    def check_resource_allocation(self, resource_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "HUBU-002"
        check_name = "资源分配检查"
        
        issues = []
        warnings = []
        
        resources = resource_data.get("resources", {})
        allocations = resource_data.get("allocations", {})
        
        total_cpu = resources.get("cpu", 0)
        total_memory = resources.get("memory", 0)
        total_storage = resources.get("storage", 0)
        
        allocated_cpu = allocations.get("cpu", 0)
        allocated_memory = allocations.get("memory", 0)
        allocated_storage = allocations.get("storage", 0)
        
        if total_cpu == 0:
            issues.append("未定义CPU资源总量")
        elif allocated_cpu > total_cpu:
            issues.append(f"CPU资源超分配: {allocated_cpu}/{total_cpu}")
        elif allocated_cpu > total_cpu * 0.9:
            warnings.append(f"CPU资源接近上限: {allocated_cpu}/{total_cpu}")
        
        if total_memory == 0:
            issues.append("未定义内存资源总量")
        elif allocated_memory > total_memory:
            issues.append(f"内存资源超分配: {allocated_memory}/{total_memory}")
        elif allocated_memory > total_memory * 0.9:
            warnings.append(f"内存资源接近上限: {allocated_memory}/{total_memory}")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="资源分配合理",
                details={
                    "cpu_usage": f"{allocated_cpu}/{total_cpu}",
                    "memory_usage": f"{allocated_memory}/{total_memory}"
                }
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"资源分配存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["考虑扩容资源"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"资源分配存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["调整资源分配", "增加资源容量"]
            )

    def check_dependency_management(self, dep_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "HUBU-003"
        check_name = "依赖管理检查"
        
        issues = []
        warnings = []
        
        dependencies = dep_data.get("dependencies", [])
        
        if not dependencies:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="未定义依赖列表",
                recommendations=["定义项目依赖"]
            )
        
        outdated = [d for d in dependencies if d.get("outdated", False)]
        if outdated:
            warnings.append(f"存在过时依赖: {len(outdated)} 个")
        
        vulnerable = [d for d in dependencies if d.get("vulnerable", False)]
        if vulnerable:
            issues.append(f"存在安全漏洞依赖: {[d.get('name') for d in vulnerable]}")
        
        conflicts = dep_data.get("conflicts", [])
        if conflicts:
            issues.append(f"存在依赖冲突: {conflicts}")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="依赖管理正常",
                details={"dependencies_count": len(dependencies)}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"依赖管理存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["更新过时依赖"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"依赖管理存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["修复安全漏洞", "解决依赖冲突"]
            )

    def check_resource_configuration_rationality(self, resource_data: dict[str, Any]) -> DepartmentCheckResult:
        """
        检查资源配置合理性（增强版）
        
        验证资源配置是否合理：
        - 计算资源配置
        - 存储资源配置
        - 网络资源配置
        - 资源利用率
        - 资源扩展性
        """
        check_id = "HUBU-004"
        check_name = "资源配置合理性检查（增强版）"
        
        issues = []
        warnings = []
        
        compute = resource_data.get("compute", {})
        if compute:
            cpu = compute.get("cpu", {})
            cpu_allocated = cpu.get("allocated", 0)
            cpu_total = cpu.get("total", 0)
            
            if cpu_total > 0:
                cpu_utilization = cpu_allocated / cpu_total
                if cpu_utilization > 1.0:
                    issues.append(f"CPU资源超分配: {cpu_allocated}/{cpu_total}")
                elif cpu_utilization > 0.9:
                    warnings.append(f"CPU资源接近满载: {cpu_utilization:.0%}")
                elif cpu_utilization < 0.3:
                    warnings.append(f"CPU资源利用率偏低: {cpu_utilization:.0%}")
            
            memory = compute.get("memory", {})
            memory_allocated = memory.get("allocated", 0)
            memory_total = memory.get("total", 0)
            
            if memory_total > 0:
                memory_utilization = memory_allocated / memory_total
                if memory_utilization > 1.0:
                    issues.append(f"内存资源超分配: {memory_allocated}/{memory_total}")
                elif memory_utilization > 0.9:
                    warnings.append(f"内存资源接近满载: {memory_utilization:.0%}")
        else:
            warnings.append("未定义计算资源配置")
        
        storage = resource_data.get("storage", {})
        if storage:
            disk = storage.get("disk", {})
            disk_used = disk.get("used", 0)
            disk_total = disk.get("total", 0)
            
            if disk_total > 0:
                disk_utilization = disk_used / disk_total
                if disk_utilization > 0.9:
                    issues.append(f"磁盘空间不足: 已使用 {disk_utilization:.0%}")
                elif disk_utilization > 0.8:
                    warnings.append(f"磁盘空间紧张: 已使用 {disk_utilization:.0%}")
            
            backup = storage.get("backup", {})
            if not backup.get("enabled", False):
                warnings.append("未启用存储备份")
            elif not backup.get("recent_backup", True):
                warnings.append("存储备份过期")
        else:
            warnings.append("未定义存储资源配置")
        
        network = resource_data.get("network", {})
        if network:
            bandwidth = network.get("bandwidth", {})
            bandwidth_used = bandwidth.get("used", 0)
            bandwidth_total = bandwidth.get("total", 0)
            
            if bandwidth_total > 0:
                bandwidth_utilization = bandwidth_used / bandwidth_total
                if bandwidth_utilization > 0.9:
                    warnings.append(f"带宽使用率过高: {bandwidth_utilization:.0%}")
            
            latency = network.get("latency_ms", 0)
            if latency > 100:
                warnings.append(f"网络延迟较高: {latency}ms")
        else:
            warnings.append("未定义网络资源配置")
        
        scalability = resource_data.get("scalability", {})
        if not scalability.get("enabled", False):
            warnings.append("未启用资源自动扩展")
        else:
            max_scale = scalability.get("max_scale", 0)
            current_scale = scalability.get("current_scale", 1)
            if current_scale >= max_scale * 0.9:
                warnings.append(f"资源扩展接近上限: {current_scale}/{max_scale}")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="资源配置合理性检查通过",
                details={
                    "compute_defined": bool(compute),
                    "storage_defined": bool(storage),
                    "network_defined": bool(network)
                }
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"资源配置合理性存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["优化资源配置", "启用自动扩展"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"资源配置合理性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["增加资源容量", "解决资源超分配"]
            )

    def check_environment_dependency_completeness(self, env_data: dict[str, Any]) -> DepartmentCheckResult:
        """
        检查环境依赖完整性（增强版）
        
        验证环境依赖是否完整：
        - 运行时依赖
        - 系统依赖
        - 服务依赖
        - 配置依赖
        - 版本兼容性
        """
        check_id = "HUBU-005"
        check_name = "环境依赖完整性检查（增强版）"
        
        issues = []
        warnings = []
        
        runtime_deps = env_data.get("runtime_dependencies", [])
        if not runtime_deps:
            warnings.append("未定义运行时依赖")
        else:
            for dep in runtime_deps:
                dep_name = dep.get("name", "unknown")
                dep_version = dep.get("version")
                required_version = dep.get("required_version")
                
                if not dep_version:
                    issues.append(f"运行时依赖 '{dep_name}' 未指定版本")
                elif required_version and dep_version != required_version:
                    warnings.append(f"运行时依赖 '{dep_name}' 版本不匹配: {dep_version} != {required_version}")
                
                if dep.get("vulnerable", False):
                    issues.append(f"运行时依赖 '{dep_name}' 存在安全漏洞")
        
        system_deps = env_data.get("system_dependencies", [])
        if not system_deps:
            warnings.append("未定义系统依赖")
        else:
            for dep in system_deps:
                dep_name = dep.get("name", "unknown")
                if not dep.get("installed", True):
                    issues.append(f"系统依赖 '{dep_name}' 未安装")
        
        service_deps = env_data.get("service_dependencies", [])
        if not service_deps:
            warnings.append("未定义服务依赖")
        else:
            for dep in service_deps:
                dep_name = dep.get("name", "unknown")
                if not dep.get("available", True):
                    issues.append(f"服务依赖 '{dep_name}' 不可用")
                elif not dep.get("healthy", True):
                    warnings.append(f"服务依赖 '{dep_name}' 健康状态异常")
        
        config_deps = env_data.get("config_dependencies", [])
        if not config_deps:
            warnings.append("未定义配置依赖")
        else:
            for dep in config_deps:
                dep_name = dep.get("name", "unknown")
                if not dep.get("exists", True):
                    issues.append(f"配置依赖 '{dep_name}' 不存在")
                elif not dep.get("valid", True):
                    warnings.append(f"配置依赖 '{dep_name}' 格式无效")
        
        compatibility = env_data.get("compatibility", {})
        if compatibility:
            conflicts = compatibility.get("conflicts", [])
            if conflicts:
                issues.append(f"存在依赖冲突: {conflicts}")
            
            deprecated = compatibility.get("deprecated", [])
            if deprecated:
                warnings.append(f"存在已废弃的依赖: {deprecated}")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="环境依赖完整性检查通过",
                details={
                    "runtime_count": len(runtime_deps),
                    "system_count": len(system_deps),
                    "service_count": len(service_deps),
                    "config_count": len(config_deps)
                }
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"环境依赖完整性存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["更新依赖版本", "修复安全漏洞"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"环境依赖完整性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["安装缺失依赖", "解决依赖冲突"]
            )

    def run_all_checks(self, data: dict[str, Any]) -> list[DepartmentCheckResult]:
        results = []
        results.append(self.check_environment_config(data.get("environment", {})))
        results.append(self.check_resource_allocation(data.get("resources", {})))
        results.append(self.check_dependency_management(data.get("dependencies", {})))
        results.append(self.check_resource_configuration_rationality(data.get("resource_config", {})))
        results.append(self.check_environment_dependency_completeness(data.get("env_dependencies", {})))
        return results


class LiibuLogicChecker:
    """礼部规范制定逻辑检查器"""

    def __init__(self):
        self.ministry = Ministry.LIIBU

    def check_coding_standards(self, standards_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "LIIBU-001"
        check_name = "编码规范检查"
        
        issues = []
        warnings = []
        
        required_standards = ["naming", "formatting", "documentation", "error_handling"]
        standards = standards_data.get("standards", {})
        
        for standard in required_standards:
            if standard not in standards:
                issues.append(f"缺少编码规范: {standard}")
        
        violations = standards_data.get("violations", [])
        if violations:
            critical_violations = [v for v in violations if v.get("severity") == "critical"]
            if critical_violations:
                issues.append(f"存在严重违规: {len(critical_violations)} 处")
            else:
                warnings.append(f"存在轻微违规: {len(violations)} 处")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="编码规范合规",
                details={"standards": list(standards.keys())}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"编码规范存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["修复编码规范违规"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"编码规范存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["定义缺失的编码规范", "修复严重违规"]
            )

    def check_documentation_completeness(self, doc_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "LIIBU-002"
        check_name = "文档完整性检查"
        
        issues = []
        warnings = []
        
        required_docs = ["api_doc", "readme", "changelog", "architecture"]
        documents = doc_data.get("documents", {})
        
        for doc in required_docs:
            if doc not in documents:
                issues.append(f"缺少文档: {doc}")
            elif not documents[doc].get("up_to_date", True):
                warnings.append(f"文档未更新: {doc}")
        
        coverage = doc_data.get("coverage", 0)
        if coverage < 80:
            issues.append(f"文档覆盖率不足: {coverage}%")
        elif coverage < 90:
            warnings.append(f"文档覆盖率建议提升: {coverage}%")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="文档完整",
                details={"documents": list(documents.keys()), "coverage": coverage}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"文档存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["更新过期文档"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"文档存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["补充缺失文档", "提升文档覆盖率"]
            )

    def check_review_process(self, review_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "LIIBU-003"
        check_name = "审查流程检查"
        
        issues = []
        warnings = []
        
        reviews = review_data.get("reviews", [])
        
        pending_reviews = [r for r in reviews if r.get("status") == "pending"]
        if len(pending_reviews) > 5:
            issues.append(f"待审查项目过多: {len(pending_reviews)} 个")
        
        overdue_reviews = [r for r in reviews if r.get("overdue", False)]
        if overdue_reviews:
            issues.append(f"存在逾期审查: {len(overdue_reviews)} 个")
        
        approved_reviews = [r for r in reviews if r.get("status") == "approved"]
        if reviews:
            approval_rate = len(approved_reviews) / len(reviews)
            if approval_rate < 0.7:
                warnings.append(f"审查通过率较低: {approval_rate:.1%}")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="审查流程正常",
                details={
                    "total_reviews": len(reviews),
                    "pending": len(pending_reviews),
                    "approved": len(approved_reviews)
                }
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"审查流程存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["提升代码质量以提高通过率"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"审查流程存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["加快审查进度", "处理逾期审查"]
            )

    def check_specification_completeness(self, spec_data: dict[str, Any]) -> DepartmentCheckResult:
        """
        检查规范完整性（增强版）
        
        验证规范是否完整：
        - 功能规范完整性
        - 接口规范完整性
        - 数据规范完整性
        - 安全规范完整性
        - 性能规范完整性
        """
        check_id = "LIIBU-004"
        check_name = "规范完整性检查（增强版）"
        
        issues = []
        warnings = []
        
        functional_spec = spec_data.get("functional_specification", {})
        if not functional_spec:
            issues.append("缺少功能规范")
        else:
            required_sections = ["user_stories", "acceptance_criteria", "business_rules"]
            for section in required_sections:
                if section not in functional_spec:
                    issues.append(f"功能规范缺少 '{section}' 部分")
                elif not functional_spec[section]:
                    warnings.append(f"功能规范 '{section}' 部分为空")
        
        interface_spec = spec_data.get("interface_specification", {})
        if not interface_spec:
            issues.append("缺少接口规范")
        else:
            api_specs = interface_spec.get("api_specs", [])
            if not api_specs:
                warnings.append("接口规范缺少API定义")
            else:
                for api in api_specs:
                    if not api.get("endpoint"):
                        warnings.append(f"API规范缺少endpoint定义")
                    if not api.get("request_schema") and not api.get("response_schema"):
                        warnings.append(f"API规范 '{api.get('name', 'unknown')}' 缺少请求/响应模式")
        
        data_spec = spec_data.get("data_specification", {})
        if not data_spec:
            warnings.append("缺少数据规范")
        else:
            entities = data_spec.get("entities", [])
            if not entities:
                warnings.append("数据规范缺少实体定义")
            else:
                for entity in entities:
                    if not entity.get("fields"):
                        warnings.append(f"实体 '{entity.get('name', 'unknown')}' 缺少字段定义")
        
        security_spec = spec_data.get("security_specification", {})
        if not security_spec:
            warnings.append("缺少安全规范")
        else:
            auth_required = security_spec.get("authentication_required", None)
            if auth_required is None:
                warnings.append("安全规范未定义认证要求")
            
            data_classification = security_spec.get("data_classification", [])
            if not data_classification:
                warnings.append("安全规范缺少数据分类定义")
        
        performance_spec = spec_data.get("performance_specification", {})
        if not performance_spec:
            warnings.append("缺少性能规范")
        else:
            if not performance_spec.get("response_time_target"):
                warnings.append("性能规范缺少响应时间目标")
            if not performance_spec.get("throughput_target"):
                warnings.append("性能规范缺少吞吐量目标")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="规范完整性检查通过",
                details={
                    "functional_defined": bool(functional_spec),
                    "interface_defined": bool(interface_spec),
                    "data_defined": bool(data_spec),
                    "security_defined": bool(security_spec),
                    "performance_defined": bool(performance_spec)
                }
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"规范完整性存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["补充缺失的规范部分", "完善规范内容"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"规范完整性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["定义缺失的规范", "补充核心规范内容"]
            )

    def check_specification_consistency(self, spec_data: dict[str, Any]) -> DepartmentCheckResult:
        """
        检查规范一致性（增强版）
        
        验证规范是否一致：
        - 命名一致性
        - 类型一致性
        - 接口一致性
        - 数据模型一致性
        - 版本一致性
        """
        check_id = "LIIBU-005"
        check_name = "规范一致性检查（增强版）"
        
        issues = []
        warnings = []
        
        naming_conventions = spec_data.get("naming_conventions", {})
        if naming_conventions:
            entities = spec_data.get("entities", [])
            api_endpoints = spec_data.get("api_endpoints", [])
            
            entity_names = [e.get("name", "") for e in entities]
            endpoint_names = [a.get("name", "") for a in api_endpoints]
            
            case_style = naming_conventions.get("case_style", "snake_case")
            for name in entity_names + endpoint_names:
                if name:
                    if case_style == "snake_case" and "_" not in name and name != name.lower():
                        warnings.append(f"命名 '{name}' 不符合 snake_case 规范")
                    elif case_style == "camelCase" and "_" in name:
                        warnings.append(f"命名 '{name}' 不符合 camelCase 规范")
        
        type_definitions = spec_data.get("type_definitions", {})
        if type_definitions:
            defined_types = set(type_definitions.keys())
            used_types = set()
            
            for entity in spec_data.get("entities", []):
                for field in entity.get("fields", []):
                    field_type = field.get("type", "")
                    if field_type not in ["string", "integer", "boolean", "float", "datetime", "array", "object"]:
                        used_types.add(field_type)
            
            undefined_types = used_types - defined_types
            if undefined_types:
                issues.append(f"使用了未定义的类型: {undefined_types}")
        
        api_specs = spec_data.get("api_specs", [])
        if api_specs:
            endpoints = {}
            for api in api_specs:
                endpoint = api.get("endpoint", "")
                method = api.get("method", "GET")
                key = f"{method}:{endpoint}"
                
                if key in endpoints:
                    issues.append(f"重复的API定义: {key}")
                endpoints[key] = api
            
            for api in api_specs:
                request_schema = api.get("request_schema", {})
                response_schema = api.get("response_schema", {})
                
                if request_schema:
                    required_fields = request_schema.get("required", [])
                    properties = request_schema.get("properties", {})
                    for field in required_fields:
                        if field not in properties:
                            warnings.append(f"API '{api.get('endpoint', '')}' 请求schema中required字段 '{field}' 未在properties中定义")
        
        data_models = spec_data.get("data_models", [])
        if data_models:
            model_names = [m.get("name", "") for m in data_models]
            duplicate_models = [n for n in model_names if model_names.count(n) > 1]
            if duplicate_models:
                issues.append(f"存在重复的数据模型定义: {set(duplicate_models)}")
            
            for model in data_models:
                relations = model.get("relations", [])
                for relation in relations:
                    target_model = relation.get("target", "")
                    if target_model and target_model not in model_names:
                        issues.append(f"模型 '{model.get('name', '')}' 引用了不存在的模型 '{target_model}'")
        
        versions = spec_data.get("versions", {})
        if versions:
            spec_version = versions.get("specification", "1.0.0")
            api_version = versions.get("api", "1.0.0")
            data_version = versions.get("data_model", "1.0.0")
            
            if spec_version != api_version:
                warnings.append(f"规范版本({spec_version})与API版本({api_version})不一致")
            if spec_version != data_version:
                warnings.append(f"规范版本({spec_version})与数据模型版本({data_version})不一致")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="规范一致性检查通过",
                details={
                    "naming_checked": bool(naming_conventions),
                    "types_checked": bool(type_definitions),
                    "apis_checked": len(api_specs),
                    "models_checked": len(data_models)
                }
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"规范一致性存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["统一命名规范", "同步版本号"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"规范一致性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["修复重复定义", "定义缺失类型", "修复模型引用"]
            )

    def run_all_checks(self, data: dict[str, Any]) -> list[DepartmentCheckResult]:
        results = []
        results.append(self.check_coding_standards(data.get("standards", {})))
        results.append(self.check_documentation_completeness(data.get("documentation", {})))
        results.append(self.check_review_process(data.get("reviews", {})))
        results.append(self.check_specification_completeness(data.get("specification", {})))
        results.append(self.check_specification_consistency(data.get("specification", {})))
        return results


class BingbuLogicChecker:
    """兵部测试先行逻辑检查器"""

    def __init__(self):
        self.ministry = Ministry.BINGBU

    def check_test_first_principle(self, test_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "BINGBU-001"
        check_name = "测试先行原则检查"
        
        issues = []
        warnings = []
        
        features = test_data.get("features", [])
        
        for feature in features:
            feature_name = feature.get("name", "unknown")
            test_written = feature.get("test_written", False)
            code_written = feature.get("code_written", False)
            test_before_code = feature.get("test_before_code", False)
            
            if not test_written and code_written:
                issues.append(f"功能 '{feature_name}' 未遵循测试先行原则")
            elif test_written and code_written and not test_before_code:
                warnings.append(f"功能 '{feature_name}' 测试编写顺序可能有问题")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="测试先行原则执行良好",
                details={"features_checked": len(features)}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"测试先行存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["确保测试在代码之前编写"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"测试先行原则违反: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["补充缺失的测试", "遵循TDD红阶段流程"]
            )

    def check_test_coverage(self, coverage_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "BINGBU-002"
        check_name = "测试覆盖率检查"
        
        issues = []
        warnings = []
        
        unit_coverage = coverage_data.get("unit_coverage", 0)
        integration_coverage = coverage_data.get("integration_coverage", 0)
        e2e_coverage = coverage_data.get("e2e_coverage", 0)
        
        if unit_coverage < 80:
            issues.append(f"单元测试覆盖率不足: {unit_coverage}%")
        elif unit_coverage < 90:
            warnings.append(f"单元测试覆盖率建议提升: {unit_coverage}%")
        
        if integration_coverage < 60:
            issues.append(f"集成测试覆盖率不足: {integration_coverage}%")
        
        uncovered_modules = coverage_data.get("uncovered_modules", [])
        if uncovered_modules:
            warnings.append(f"存在未覆盖模块: {uncovered_modules[:5]}")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="测试覆盖率达标",
                details={
                    "unit_coverage": unit_coverage,
                    "integration_coverage": integration_coverage,
                    "e2e_coverage": e2e_coverage
                }
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"测试覆盖率存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["补充测试用例"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"测试覆盖率不达标: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["增加测试用例", "提升覆盖率"]
            )

    def check_test_quality(self, quality_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "BINGBU-003"
        check_name = "测试质量检查"
        
        issues = []
        warnings = []
        
        tests = quality_data.get("tests", [])
        
        flaky_tests = [t for t in tests if t.get("flaky", False)]
        if flaky_tests:
            issues.append(f"存在不稳定测试: {len(flaky_tests)} 个")
        
        slow_tests = [t for t in tests if t.get("duration", 0) > 5]
        if slow_tests:
            warnings.append(f"存在慢测试: {len(slow_tests)} 个")
        
        skipped_tests = [t for t in tests if t.get("skipped", False)]
        if len(skipped_tests) > len(tests) * 0.1:
            issues.append(f"跳过测试比例过高: {len(skipped_tests)}/{len(tests)}")
        
        assertions_per_test = quality_data.get("avg_assertions_per_test", 0)
        if assertions_per_test < 1:
            warnings.append("平均断言数过低，测试可能无效")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="测试质量良好",
                details={
                    "tests_count": len(tests),
                    "flaky_count": len(flaky_tests),
                    "slow_count": len(slow_tests)
                }
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"测试质量存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["优化慢测试", "增加断言"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"测试质量存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["修复不稳定测试", "减少跳过测试"]
            )

    def check_test_coverage_enhanced(self, coverage_data: dict[str, Any]) -> DepartmentCheckResult:
        """
        检查测试覆盖率（增强版）
        
        验证测试覆盖率是否达标：
        - 语句覆盖率
        - 分支覆盖率
        - 函数覆盖率
        - 行覆盖率
        - 模块覆盖率
        """
        check_id = "BINGBU-004"
        check_name = "测试覆盖率检查（增强版）"
        
        issues = []
        warnings = []
        
        statement_coverage = coverage_data.get("statement_coverage", 0)
        branch_coverage = coverage_data.get("branch_coverage", 0)
        function_coverage = coverage_data.get("function_coverage", 0)
        line_coverage = coverage_data.get("line_coverage", 0)
        
        if statement_coverage < 80:
            issues.append(f"语句覆盖率不足: {statement_coverage}% (目标: 80%)")
        elif statement_coverage < 90:
            warnings.append(f"语句覆盖率建议提升: {statement_coverage}%")
        
        if branch_coverage < 70:
            issues.append(f"分支覆盖率不足: {branch_coverage}% (目标: 70%)")
        elif branch_coverage < 85:
            warnings.append(f"分支覆盖率建议提升: {branch_coverage}%")
        
        if function_coverage < 90:
            issues.append(f"函数覆盖率不足: {function_coverage}% (目标: 90%)")
        elif function_coverage < 95:
            warnings.append(f"函数覆盖率建议提升: {function_coverage}%")
        
        if line_coverage < 80:
            issues.append(f"行覆盖率不足: {line_coverage}% (目标: 80%)")
        elif line_coverage < 90:
            warnings.append(f"行覆盖率建议提升: {line_coverage}%")
        
        module_coverage = coverage_data.get("module_coverage", {})
        if module_coverage:
            low_coverage_modules = [
                {"name": name, "coverage": cov}
                for name, cov in module_coverage.items()
                if cov < 70
            ]
            if low_coverage_modules:
                issues.append(f"存在低覆盖率模块: {[m['name'] for m in low_coverage_modules[:5]]}")
            
            uncovered_modules = [
                name for name, cov in module_coverage.items()
                if cov == 0
            ]
            if uncovered_modules:
                issues.append(f"存在未覆盖模块: {uncovered_modules[:5]}")
        
        coverage_trend = coverage_data.get("coverage_trend", [])
        if coverage_trend:
            if len(coverage_trend) >= 2:
                recent_trend = coverage_trend[-1] - coverage_trend[-2]
                if recent_trend < -5:
                    issues.append(f"覆盖率下降趋势: 最近下降 {abs(recent_trend)}%")
                elif recent_trend < 0:
                    warnings.append(f"覆盖率轻微下降: 最近下降 {abs(recent_trend)}%")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="测试覆盖率达标",
                details={
                    "statement_coverage": statement_coverage,
                    "branch_coverage": branch_coverage,
                    "function_coverage": function_coverage,
                    "line_coverage": line_coverage
                }
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"测试覆盖率存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["补充测试用例", "提升分支覆盖率"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"测试覆盖率不达标: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["增加测试用例", "覆盖低覆盖率模块", "关注分支覆盖"]
            )

    def check_test_case_quality(self, quality_data: dict[str, Any]) -> DepartmentCheckResult:
        """
        检查测试用例质量（增强版）
        
        验证测试用例质量：
        - 断言质量
        - 边界条件覆盖
        - 异常场景覆盖
        - 测试独立性
        - 测试可读性
        """
        check_id = "BINGBU-005"
        check_name = "测试用例质量检查（增强版）"
        
        issues = []
        warnings = []
        
        test_cases = quality_data.get("test_cases", [])
        if not test_cases:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="无测试用例数据",
                recommendations=["定义测试用例"]
            )
        
        for test in test_cases:
            test_name = test.get("name", "unknown")
            
            assertions = test.get("assertions", [])
            if not assertions:
                issues.append(f"测试 '{test_name}' 缺少断言")
            elif len(assertions) < 2:
                warnings.append(f"测试 '{test_name}' 断言数量较少")
            
            edge_cases = test.get("edge_cases_covered", [])
            if not edge_cases:
                warnings.append(f"测试 '{test_name}' 未覆盖边界条件")
            
            exception_cases = test.get("exception_cases_covered", [])
            if not exception_cases:
                warnings.append(f"测试 '{test_name}' 未覆盖异常场景")
            
            dependencies = test.get("dependencies", [])
            if dependencies:
                issues.append(f"测试 '{test_name}' 存在依赖，可能影响独立性")
            
            description = test.get("description", "")
            if not description:
                warnings.append(f"测试 '{test_name}' 缺少描述")
            elif len(description) < 10:
                warnings.append(f"测试 '{test_name}' 描述过于简短")
        
        test_metrics = quality_data.get("metrics", {})
        if test_metrics:
            avg_assertions = test_metrics.get("avg_assertions_per_test", 0)
            if avg_assertions < 2:
                issues.append(f"平均断言数过低: {avg_assertions}")
            elif avg_assertions < 3:
                warnings.append(f"平均断言数建议提升: {avg_assertions}")
            
            edge_coverage = test_metrics.get("edge_case_coverage", 0)
            if edge_coverage < 60:
                issues.append(f"边界条件覆盖率不足: {edge_coverage}%")
            elif edge_coverage < 80:
                warnings.append(f"边界条件覆盖率建议提升: {edge_coverage}%")
            
            exception_coverage = test_metrics.get("exception_coverage", 0)
            if exception_coverage < 50:
                issues.append(f"异常场景覆盖率不足: {exception_coverage}%")
            elif exception_coverage < 70:
                warnings.append(f"异常场景覆盖率建议提升: {exception_coverage}%")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="测试用例质量良好",
                details={
                    "test_count": len(test_cases),
                    "avg_assertions": test_metrics.get("avg_assertions_per_test", 0),
                    "edge_coverage": test_metrics.get("edge_case_coverage", 0),
                    "exception_coverage": test_metrics.get("exception_coverage", 0)
                }
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"测试用例质量存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["增加断言数量", "覆盖边界条件", "覆盖异常场景"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"测试用例质量问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["添加断言", "消除测试依赖", "提升测试独立性"]
            )

    def run_all_checks(self, data: dict[str, Any]) -> list[DepartmentCheckResult]:
        results = []
        results.append(self.check_test_first_principle(data.get("test_first", {})))
        results.append(self.check_test_coverage(data.get("coverage", {})))
        results.append(self.check_test_quality(data.get("quality", {})))
        results.append(self.check_test_coverage_enhanced(data.get("coverage_enhanced", {})))
        results.append(self.check_test_case_quality(data.get("test_case_quality", {})))
        return results


class GongbuLogicChecker:
    """工部代码实现逻辑检查器"""

    def __init__(self):
        self.ministry = Ministry.GONGBU

    def check_code_implementation(self, impl_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "GONGBU-001"
        check_name = "代码实现检查"
        
        issues = []
        warnings = []
        
        modules = impl_data.get("modules", [])
        
        for module in modules:
            module_name = module.get("name", "unknown")
            
            if not module.get("implemented", False):
                issues.append(f"模块 '{module_name}' 未实现")
            
            if module.get("has_todos", False):
                warnings.append(f"模块 '{module_name}' 存在TODO项")
            
            complexity = module.get("complexity", 0)
            if complexity > 15:
                warnings.append(f"模块 '{module_name}' 复杂度过高: {complexity}")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="代码实现完整",
                details={"modules_count": len(modules)}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"代码实现存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["处理TODO项", "降低复杂度"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"代码实现存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["完成未实现的模块"]
            )

    def check_code_quality(self, quality_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "GONGBU-002"
        check_name = "代码质量检查"
        
        issues = []
        warnings = []
        
        code_smells = quality_data.get("code_smells", [])
        if code_smells:
            critical_smells = [s for s in code_smells if s.get("severity") == "critical"]
            if critical_smells:
                issues.append(f"存在严重代码异味: {len(critical_smells)} 处")
            else:
                warnings.append(f"存在代码异味: {len(code_smells)} 处")
        
        duplications = quality_data.get("duplications", [])
        if duplications:
            dup_rate = len(duplications) / max(quality_data.get("total_lines", 1), 1) * 100
            if dup_rate > 5:
                issues.append(f"代码重复率过高: {dup_rate:.1f}%")
        
        tech_debt = quality_data.get("tech_debt_hours", 0)
        if tech_debt > 40:
            issues.append(f"技术债务过高: {tech_debt} 小时")
        elif tech_debt > 20:
            warnings.append(f"技术债务需关注: {tech_debt} 小时")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="代码质量良好",
                details={"tech_debt_hours": tech_debt}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"代码质量存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["重构代码异味", "减少重复代码"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"代码质量存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["修复严重代码异味", "消除重复代码", "偿还技术债务"]
            )

    def check_green_phase_completion(self, green_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "GONGBU-003"
        check_name = "绿阶段完成检查"
        
        issues = []
        warnings = []
        
        tests = green_data.get("tests", [])
        all_passed = all(t.get("passed", False) for t in tests)
        
        if not all_passed:
            failed_tests = [t for t in tests if not t.get("passed", False)]
            issues.append(f"存在未通过的测试: {len(failed_tests)} 个")
        
        implementation_complete = green_data.get("implementation_complete", False)
        if not implementation_complete:
            issues.append("代码实现未完成")
        
        minimal_implementation = green_data.get("minimal_implementation", True)
        if not minimal_implementation:
            warnings.append("实现可能过度设计，建议遵循最小实现原则")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="绿阶段完成，所有测试通过",
                details={"tests_passed": len([t for t in tests if t.get("passed", False)])}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"绿阶段存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["简化实现"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"绿阶段未完成: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["修复失败的测试", "完成代码实现"]
            )

    def run_all_checks(self, data: dict[str, Any]) -> list[DepartmentCheckResult]:
        results = []
        results.append(self.check_code_implementation(data.get("implementation", {})))
        results.append(self.check_code_quality(data.get("quality", {})))
        results.append(self.check_green_phase_completion(data.get("green_phase", {})))
        return results


class XingbuLogicChecker:
    """刑部重构优化逻辑检查器"""

    def __init__(self):
        self.ministry = Ministry.XINGBU

    def check_refactoring_necessity(self, refactor_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "XINGBU-001"
        check_name = "重构必要性检查"
        
        issues = []
        warnings = []
        
        code_metrics = refactor_data.get("code_metrics", {})
        
        complexity = code_metrics.get("avg_complexity", 0)
        if complexity > 15:
            issues.append(f"平均复杂度过高: {complexity}")
        elif complexity > 10:
            warnings.append(f"平均复杂度需关注: {complexity}")
        
        coupling = code_metrics.get("coupling", 0)
        if coupling > 0.7:
            issues.append(f"耦合度过高: {coupling}")
        
        cohesion = code_metrics.get("cohesion", 0)
        if cohesion < 0.5:
            issues.append(f"内聚度过低: {cohesion}")
        
        refactoring_candidates = refactor_data.get("refactoring_candidates", [])
        if len(refactoring_candidates) > 10:
            warnings.append(f"重构候选项较多: {len(refactoring_candidates)} 个")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="代码结构良好，无需紧急重构",
                details={"candidates_count": len(refactoring_candidates)}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"存在重构建议: {'; '.join(warnings)}",
                details={"warnings": warnings, "candidates": refactoring_candidates[:5]},
                recommendations=["规划重构任务"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"需要紧急重构: {'; '.join(issues)}",
                details={"issues": issues, "candidates": refactoring_candidates},
                recommendations=["立即启动重构", "降低复杂度", "解耦模块"]
            )

    def check_blue_phase_completion(self, blue_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "XINGBU-002"
        check_name = "蓝阶段完成检查"
        
        issues = []
        warnings = []
        
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
            issues.append(f"重构导致性能下降: {performance_impact}%")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="蓝阶段完成，代码质量提升",
                details={"improvements": improvements}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"蓝阶段存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["完成重构", "记录改进项"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"蓝阶段存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["修复测试失败", "回滚性能下降的修改"]
            )

    def check_optimization_opportunities(self, opt_data: dict[str, Any]) -> DepartmentCheckResult:
        check_id = "XINGBU-003"
        check_name = "优化机会检查"
        
        issues = []
        warnings = []
        
        performance_issues = opt_data.get("performance_issues", [])
        if performance_issues:
            critical = [p for p in performance_issues if p.get("severity") == "critical"]
            if critical:
                issues.append(f"存在严重性能问题: {len(critical)} 个")
            else:
                warnings.append(f"存在性能问题: {len(performance_issues)} 个")
        
        memory_issues = opt_data.get("memory_issues", [])
        if memory_issues:
            issues.append(f"存在内存问题: {len(memory_issues)} 个")
        
        optimization_suggestions = opt_data.get("suggestions", [])
        if len(optimization_suggestions) > 5:
            warnings.append(f"优化建议较多: {len(optimization_suggestions)} 个")
        
        if not issues and not warnings:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="代码优化良好",
                details={"suggestions_count": len(optimization_suggestions)}
            )
        elif not issues:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"存在优化建议: {'; '.join(warnings)}",
                details={"warnings": warnings, "suggestions": optimization_suggestions[:5]},
                recommendations=["考虑优化建议"]
            )
        else:
            return DepartmentCheckResult(
                check_id=check_id,
                check_name=check_name,
                ministry=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"存在优化问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["修复性能问题", "解决内存问题"]
            )

    def run_all_checks(self, data: dict[str, Any]) -> list[DepartmentCheckResult]:
        results = []
        results.append(self.check_refactoring_necessity(data.get("refactoring", {})))
        results.append(self.check_blue_phase_completion(data.get("blue_phase", {})))
        results.append(self.check_optimization_opportunities(data.get("optimization", {})))
        return results


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
            Ministry.LIBU: LibuLogicChecker(),
            Ministry.HUBU: HubuLogicChecker(),
            Ministry.LIIBU: LiibuLogicChecker(),
            Ministry.BINGBU: BingbuLogicChecker(),
            Ministry.GONGBU: GongbuLogicChecker(),
            Ministry.XINGBU: XingbuLogicChecker(),
        }

    def check_all(self, data: dict[str, Any]) -> DepartmentLogicReport:
        all_results: list[DepartmentCheckResult] = []
        
        for ministry, checker in self.checkers.items():
            ministry_data = data.get(ministry.value, {})
            all_results.extend(checker.run_all_checks(ministry_data))
        
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
        
        by_ministry: dict[str, dict[str, int]] = {}
        for ministry in Ministry:
            ministry_results = [r for r in all_results if r.ministry == ministry]
            by_ministry[ministry.value] = {
                "total": len(ministry_results),
                "passed": sum(1 for r in ministry_results if r.status == CheckStatus.PASS),
                "failed": sum(1 for r in ministry_results if r.status == CheckStatus.FAIL),
                "warnings": sum(1 for r in ministry_results if r.status == CheckStatus.WARNING)
            }
        
        summary = self._generate_summary(all_results, by_ministry)
        
        report = DepartmentLogicReport(
            report_id=f"DLC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            total_checks=len(all_results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            skipped=skipped,
            results=all_results,
            by_ministry=by_ministry,
            summary=summary,
            overall_status=overall_status
        )
        
        return report

    def check_ministry(self, ministry: Ministry, data: dict[str, Any]) -> list[DepartmentCheckResult]:
        checker = self.checkers.get(ministry)
        if checker:
            ministry_data = data.get(ministry.value, {})
            return checker.run_all_checks(ministry_data)
        return []

    def _generate_summary(self, results: list[DepartmentCheckResult], by_ministry: dict) -> dict[str, Any]:
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
            "recommendations": unique_recommendations[:10]
        }

    def save_report(self, report: DepartmentLogicReport, output_path: Path = None) -> Path:
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
            "summary": report.summary
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"报告已保存: {output_path}")
        return output_path

    def print_report(self, report: DepartmentLogicReport):
        print("\n" + "=" * 70)
        print("六部执行逻辑检查报告")
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
    return {
        "libu": {
            "assignment": {
                "agents": [
                    {"id": "agent-1", "name": "开发者A", "max_concurrent_tasks": 3},
                    {"id": "agent-2", "name": "开发者B", "max_concurrent_tasks": 3}
                ],
                "tasks": [
                    {"id": "task-1", "name": "用户注册"},
                    {"id": "task-2", "name": "用户登录"}
                ],
                "assignments": [
                    {"agent_id": "agent-1", "task_id": "task-1"},
                    {"agent_id": "agent-2", "task_id": "task-2"}
                ]
            },
            "skills": {
                "required_skills": ["python", "vue", "postgresql"],
                "available_skills": ["python", "vue", "postgresql", "redis"],
                "skill_scores": {"python": 0.9, "vue": 0.8, "postgresql": 0.85}
            },
            "load": {
                "agent_loads": {"agent-1": 0.6, "agent-2": 0.5}
            }
        },
        "hubu": {
            "environment": {
                "environments": {
                    "development": {"database": "sqlite", "cache": "redis"},
                    "testing": {"database": "postgresql", "cache": "redis"},
                    "production": {"database": "postgresql", "cache": "redis"}
                }
            },
            "resources": {
                "resources": {"cpu": 16, "memory": 32, "storage": 500},
                "allocations": {"cpu": 10, "memory": 20, "storage": 200}
            },
            "dependencies": {
                "dependencies": [
                    {"name": "fastapi", "version": "0.100.0", "outdated": False, "vulnerable": False},
                    {"name": "vue", "version": "3.3.0", "outdated": False, "vulnerable": False}
                ],
                "conflicts": []
            }
        },
        "liibu": {
            "standards": {
                "standards": {
                    "naming": {"convention": "snake_case"},
                    "formatting": {"style": "black"},
                    "documentation": {"style": "google"},
                    "error_handling": {"strategy": "exception"}
                },
                "violations": []
            },
            "documentation": {
                "documents": {
                    "api_doc": {"up_to_date": True},
                    "readme": {"up_to_date": True},
                    "changelog": {"up_to_date": True},
                    "architecture": {"up_to_date": True}
                },
                "coverage": 85
            },
            "reviews": {
                "reviews": [
                    {"id": "r-1", "status": "approved", "overdue": False},
                    {"id": "r-2", "status": "approved", "overdue": False}
                ]
            }
        },
        "bingbu": {
            "test_first": {
                "features": [
                    {"name": "用户注册", "test_written": True, "code_written": True, "test_before_code": True},
                    {"name": "用户登录", "test_written": True, "code_written": True, "test_before_code": True}
                ]
            },
            "coverage": {
                "unit_coverage": 85,
                "integration_coverage": 70,
                "e2e_coverage": 100,
                "uncovered_modules": []
            },
            "quality": {
                "tests": [
                    {"name": "test_register", "flaky": False, "duration": 0.5, "skipped": False},
                    {"name": "test_login", "flaky": False, "duration": 0.3, "skipped": False}
                ],
                "avg_assertions_per_test": 3
            }
        },
        "gongbu": {
            "implementation": {
                "modules": [
                    {"name": "user_service", "implemented": True, "has_todos": False, "complexity": 8},
                    {"name": "auth_service", "implemented": True, "has_todos": False, "complexity": 6}
                ]
            },
            "quality": {
                "code_smells": [],
                "duplications": [],
                "tech_debt_hours": 5,
                "total_lines": 1000
            },
            "green_phase": {
                "tests": [
                    {"name": "test_register", "passed": True},
                    {"name": "test_login", "passed": True}
                ],
                "implementation_complete": True,
                "minimal_implementation": True
            }
        },
        "xingbu": {
            "refactoring": {
                "code_metrics": {
                    "avg_complexity": 7,
                    "coupling": 0.3,
                    "cohesion": 0.8
                },
                "refactoring_candidates": []
            },
            "blue_phase": {
                "tests_still_pass": True,
                "refactoring_done": True,
                "improvements": ["提取公共方法", "优化查询性能"],
                "performance_impact": 5
            },
            "optimization": {
                "performance_issues": [],
                "memory_issues": [],
                "suggestions": ["考虑添加缓存", "优化数据库索引"]
            }
        }
    }


def main():
    parser = argparse.ArgumentParser(description="六部执行逻辑检查器")
    
    parser.add_argument("--check-all", action="store_true", help="执行所有检查")
    parser.add_argument("--check-libu", action="store_true", help="检查吏部调度逻辑")
    parser.add_argument("--check-hubu", action="store_true", help="检查户部资源管理逻辑")
    parser.add_argument("--check-liibu", action="store_true", help="检查礼部规范制定逻辑")
    parser.add_argument("--check-bingbu", action="store_true", help="检查兵部测试先行逻辑")
    parser.add_argument("--check-gongbu", action="store_true", help="检查工部代码实现逻辑")
    parser.add_argument("--check-xingbu", action="store_true", help="检查刑部重构优化逻辑")
    parser.add_argument("--data-file", type=Path, help="数据文件路径(JSON)")
    parser.add_argument("--output", type=Path, help="报告输出路径")
    parser.add_argument("--sample", action="store_true", help="使用示例数据")
    
    args = parser.parse_args()
    
    if args.data_file:
        try:
            with open(args.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"加载数据文件失败: {e}")
            sys.exit(1)
    elif args.sample:
        data = load_sample_data()
    else:
        data = load_sample_data()
    
    checker = DepartmentLogicChecker()
    
    specific_checks = [
        args.check_libu, args.check_hubu, args.check_liibu,
        args.check_bingbu, args.check_gongbu, args.check_xingbu
    ]
    
    if args.check_all or not any(specific_checks):
        report = checker.check_all(data)
        checker.print_report(report)
        
        if args.output:
            checker.save_report(report, args.output)
        else:
            checker.save_report(report)
    
    elif args.check_libu:
        results = checker.check_ministry(Ministry.LIBU, data)
        print("\n吏部调度逻辑检查结果:")
        for result in results:
            status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
            print(f"  [{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.check_hubu:
        results = checker.check_ministry(Ministry.HUBU, data)
        print("\n户部资源管理逻辑检查结果:")
        for result in results:
            status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
            print(f"  [{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.check_liibu:
        results = checker.check_ministry(Ministry.LIIBU, data)
        print("\n礼部规范制定逻辑检查结果:")
        for result in results:
            status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
            print(f"  [{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.check_bingbu:
        results = checker.check_ministry(Ministry.BINGBU, data)
        print("\n兵部测试先行逻辑检查结果:")
        for result in results:
            status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
            print(f"  [{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.check_gongbu:
        results = checker.check_ministry(Ministry.GONGBU, data)
        print("\n工部代码实现逻辑检查结果:")
        for result in results:
            status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
            print(f"  [{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.check_xingbu:
        results = checker.check_ministry(Ministry.XINGBU, data)
        print("\n刑部重构优化逻辑检查结果:")
        for result in results:
            status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
            print(f"  [{status_symbol}] {result.check_name}: {result.message}")


if __name__ == "__main__":
    main()
