#!/usr/bin/env python3
"""
三省协调逻辑检查器 - Sanliu 技能

功能：
- 中书省决策逻辑验证
- 门下省审议逻辑验证
- 尚书省执行逻辑验证
- 三省信息流转检查
- 生成逻辑检查报告

使用方法：
    python scripts/provincial_logic_checker.py --check-all
    python scripts/provincial_logic_checker.py --check-zhongshusheng
    python scripts/provincial_logic_checker.py --check-menxiasheng
    python scripts/provincial_logic_checker.py --check-shangshusheng
    python scripts/provincial_logic_checker.py --check-flow
"""

import argparse
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Callable

from skillscripts.utils.path_config_manager import PathConfigManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('provincial_logic_checker.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class Province(Enum):
    ZHONGSHUSHENG = "zhongshusheng"
    MENXIASHENG = "menxiasheng"
    SHANGSHUSHENG = "shangshusheng"


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


class FlowType(Enum):
    DECISION_TO_REVIEW = "decision_to_review"
    REVIEW_TO_EXECUTION = "review_to_execution"
    EXECUTION_FEEDBACK = "execution_feedback"
    REJECTION_FLOW = "rejection_flow"
    EMERGENCY_FLOW = "emergency_flow"


@dataclass
class CheckResult:
    check_id: str
    check_name: str
    province: Province
    status: CheckStatus
    severity: CheckSeverity
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    execution_time_ms: float = 0.0


@dataclass
class FlowCheckResult:
    from_province: Province
    to_province: Province
    flow_type: str
    status: CheckStatus
    message: str
    data_integrity: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    flow_duration_ms: float = 0.0
    data_items_transferred: int = 0
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class ProvincialLogicReport:
    report_id: str
    generated_at: str
    total_checks: int
    passed: int
    failed: int
    warnings: int
    skipped: int
    results: list[CheckResult]
    flow_results: list[FlowCheckResult]
    summary: dict[str, Any]
    overall_status: CheckStatus
    check_history: list[dict[str, Any]] = field(default_factory=list)
    performance_metrics: dict[str, Any] = field(default_factory=dict)


class CheckContext:
    """检查上下文，用于存储检查过程中的临时数据和状态"""
    
    def __init__(self):
        self._data: dict[str, Any] = {}
        self._history: list[dict[str, Any]] = []
    
    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)
    
    def add_history(self, check_id: str, status: CheckStatus, message: str) -> None:
        self._history.append({
            "check_id": check_id,
            "status": status.value,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_history(self) -> list[dict[str, Any]]:
        return self._history.copy()


class ZhongshushengLogicChecker:
    """
    中书省决策逻辑检查器
    
    负责验证决策阶段的各项逻辑：
    - 决策完整性检查
    - SDD规范有效性检查
    - 架构可行性检查
    - 优先级一致性检查
    - 需求一致性检查（新增）
    - 技术可行性评估（新增）
    - 风险评估检查（新增）
    - 资源匹配检查（新增）
    """

    def __init__(self):
        self.checks: list[CheckResult] = []
        self.context = CheckContext()
    
    def _measure_time(self, func: Callable) -> Callable:
        """装饰器：测量检查执行时间"""
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            result = func(*args, **kwargs)
            end_time = datetime.now()
            result.execution_time_ms = (end_time - start_time).total_seconds() * 1000
            return result
        return wrapper

    def check_decision_completeness(self, decision_data: dict[str, Any]) -> CheckResult:
        """
        检查决策完整性
        
        验证决策数据是否包含所有必需字段，确保决策过程完整。
        必需字段包括：
        - requirement_analysis: 需求分析结果
        - architecture_design: 架构设计
        - sdd_specification: SDD规范
        - acceptance_tests: 验收测试
        - priority_ranking: 优先级排序
        """
        check_id = "ZSS-001"
        check_name = "决策完整性检查"
        
        required_fields = [
            "requirement_analysis",
            "architecture_design",
            "sdd_specification",
            "acceptance_tests",
            "priority_ranking"
        ]
        
        missing_fields = []
        empty_fields = []
        
        for field_name in required_fields:
            if field_name not in decision_data:
                missing_fields.append(field_name)
            elif not decision_data.get(field_name):
                empty_fields.append(field_name)
        
        if not missing_fields and not empty_fields:
            self.context.add_history(check_id, CheckStatus.PASS, "决策数据完整")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="决策数据完整，所有必需字段均已提供",
                details={
                    "checked_fields": required_fields,
                    "field_count": len(required_fields)
                }
            )
        elif missing_fields:
            self.context.add_history(check_id, CheckStatus.FAIL, f"缺少字段: {missing_fields}")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message=f"决策数据不完整，缺少字段: {', '.join(missing_fields)}",
                details={
                    "missing_fields": missing_fields,
                    "empty_fields": empty_fields
                },
                recommendations=[f"补充缺失字段: {field}" for field in missing_fields]
            )
        else:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在空字段: {empty_fields}")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.HIGH,
                message=f"决策数据存在空字段: {', '.join(empty_fields)}",
                details={"empty_fields": empty_fields},
                recommendations=[f"填充空字段: {field}" for field in empty_fields]
            )

    def check_sdd_specification_validity(self, sdd_data: dict[str, Any]) -> CheckResult:
        """
        检查SDD规范有效性
        
        验证SDD（Software Design Document）规范是否完整有效：
        - 接口规范定义
        - 数据模型定义
        - 行为规则定义
        - 测试规范定义
        """
        check_id = "ZSS-002"
        check_name = "SDD规范有效性检查"
        
        issues = []
        warnings = []
        
        required_sections = ["interfaces", "data_models", "behavior_rules", "test_specifications"]
        
        for section in required_sections:
            if section not in sdd_data:
                issues.append(f"缺少{section}定义")
        
        interfaces = sdd_data.get("interfaces", [])
        for i, interface in enumerate(interfaces):
            if "endpoint" not in interface:
                issues.append(f"接口{i+1}缺少endpoint定义")
            if "method" not in interface:
                issues.append(f"接口{i+1}缺少method定义")
            if "request_schema" not in interface:
                warnings.append(f"接口{i+1}缺少请求模式定义")
            if "response_schema" not in interface:
                warnings.append(f"接口{i+1}缺少响应模式定义")
        
        data_models = sdd_data.get("data_models", [])
        for i, model in enumerate(data_models):
            if "name" not in model:
                issues.append(f"数据模型{i+1}缺少名称")
            if "fields" not in model:
                warnings.append(f"数据模型{i+1}缺少字段定义")
        
        behavior_rules = sdd_data.get("behavior_rules", [])
        for i, rule in enumerate(behavior_rules):
            if "name" not in rule:
                warnings.append(f"行为规则{i+1}缺少名称")
            if "condition" not in rule:
                warnings.append(f"行为规则{i+1}缺少条件定义")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "SDD规范完整有效")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="SDD规范定义完整有效",
                details={
                    "interfaces_count": len(interfaces),
                    "data_models_count": len(data_models),
                    "behavior_rules_count": len(behavior_rules)
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个警告")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"SDD规范存在轻微问题: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["完善SDD规范定义", "补充缺失的模式定义"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"SDD规范存在严重问题: {'; '.join(issues[:5])}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["重新审视SDD规范", "补充缺失的规范定义"]
            )

    def check_architecture_feasibility(self, architecture_data: dict[str, Any]) -> CheckResult:
        """
        检查架构可行性
        
        验证架构设计是否可行：
        - 核心组件完整性
        - 技术栈定义
        - 依赖关系合理性
        - 循环依赖检测
        """
        check_id = "ZSS-003"
        check_name = "架构可行性检查"
        
        issues = []
        warnings = []
        
        required_components = ["frontend", "backend", "database"]
        components = architecture_data.get("components", {})
        
        for component in required_components:
            if component not in components:
                issues.append(f"缺少核心组件: {component}")
        
        tech_stack = architecture_data.get("tech_stack", {})
        if not tech_stack:
            issues.append("未定义技术栈")
        else:
            if "frontend" not in tech_stack:
                warnings.append("未指定前端技术栈")
            if "backend" not in tech_stack:
                warnings.append("未指定后端技术栈")
            if "database" not in tech_stack:
                warnings.append("未指定数据库技术")
        
        dependencies = architecture_data.get("dependencies", [])
        if dependencies:
            circular_deps = self._detect_circular_dependencies(dependencies)
            if circular_deps:
                issues.append(f"检测到循环依赖: {circular_deps}")
        
        scalability = architecture_data.get("scalability", {})
        if not scalability:
            warnings.append("未定义可扩展性策略")
        
        security = architecture_data.get("security", {})
        if not security:
            warnings.append("未定义安全策略")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "架构设计可行")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="架构设计可行，无潜在问题",
                details={
                    "components": list(components.keys()),
                    "tech_stack_defined": bool(tech_stack),
                    "dependencies_count": len(dependencies)
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"架构设计存在建议项: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["完善架构设计细节", "定义可扩展性和安全策略"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"架构设计存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["重新审视架构设计", "解决循环依赖问题"]
            )

    def _detect_circular_dependencies(self, dependencies: list[dict]) -> list[str]:
        """检测循环依赖"""
        circular = []
        dep_graph: dict[str, list[str]] = {}
        
        for dep in dependencies:
            source = dep.get("source", "")
            target = dep.get("target", "")
            if source and target:
                if source not in dep_graph:
                    dep_graph[source] = []
                dep_graph[source].append(target)
        
        def has_cycle(node: str, visited: set, rec_stack: set) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dep_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        visited: set[str] = set()
        for node in dep_graph:
            if node not in visited:
                if has_cycle(node, visited, set()):
                    circular.append(node)
        
        return circular

    def check_priority_consistency(self, tasks: list[dict[str, Any]]) -> CheckResult:
        """
        检查优先级一致性
        
        验证任务优先级设置是否合理一致：
        - 优先级值有效性
        - 依赖任务优先级关系
        - 优先级冲突检测
        """
        check_id = "ZSS-004"
        check_name = "优先级一致性检查"
        
        issues = []
        warnings = []
        priority_values = ["critical", "high", "medium", "low", "p0", "p1", "p2", "p3"]
        
        for i, task in enumerate(tasks):
            priority = task.get("priority", "").lower()
            if not priority:
                issues.append(f"任务{i+1}未设置优先级")
            elif priority not in priority_values:
                issues.append(f"任务{i+1}优先级值无效: {priority}")
        
        dependencies = [(i, t.get("depends_on", [])) for i, t in enumerate(tasks)]
        for task_idx, depends_on in dependencies:
            if depends_on:
                task_priority = tasks[task_idx].get("priority", "medium")
                for dep_idx in depends_on:
                    if isinstance(dep_idx, int) and dep_idx < len(tasks):
                        dep_priority = tasks[dep_idx].get("priority", "medium")
                        if self._priority_higher(dep_priority, task_priority):
                            issues.append(
                                f"任务{task_idx+1}依赖的任务{dep_idx+1}优先级更高，可能导致阻塞"
                            )
        
        high_priority_count = sum(1 for t in tasks if t.get("priority", "").lower() in ["critical", "p0", "high", "p1"])
        if high_priority_count > len(tasks) * 0.5:
            warnings.append(f"高优先级任务占比过高: {high_priority_count}/{len(tasks)}")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "优先级设置合理")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="任务优先级设置合理一致",
                details={
                    "tasks_count": len(tasks),
                    "priority_distribution": self._get_priority_distribution(tasks)
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"优先级设置存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["调整任务优先级分布"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"优先级设置存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["调整任务优先级", "确保依赖任务优先级不低于被依赖任务"]
            )

    def _priority_higher(self, p1: str, p2: str) -> bool:
        """比较优先级高低"""
        priority_order = {
            "critical": 0, "p0": 0,
            "high": 1, "p1": 1,
            "medium": 2, "p2": 2,
            "low": 3, "p3": 3
        }
        return priority_order.get(p1.lower(), 2) < priority_order.get(p2.lower(), 2)

    def _get_priority_distribution(self, tasks: list[dict]) -> dict[str, int]:
        """获取优先级分布"""
        distribution: dict[str, int] = {}
        for task in tasks:
            priority = task.get("priority", "medium").lower()
            distribution[priority] = distribution.get(priority, 0) + 1
        return distribution

    def check_requirement_consistency(self, requirement_data: dict[str, Any]) -> CheckResult:
        """
        检查需求一致性（新增）
        
        验证需求分析结果的一致性：
        - 需求完整性
        - 需求冲突检测
        - 需求优先级匹配
        - 需求可追溯性
        """
        check_id = "ZSS-005"
        check_name = "需求一致性检查"
        
        issues = []
        warnings = []
        
        requirements = requirement_data.get("requirements", [])
        if not requirements:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.HIGH,
                message="未定义需求列表",
                recommendations=["定义项目需求"]
            )
        
        for i, req in enumerate(requirements):
            req_id = req.get("id", f"REQ-{i+1}")
            
            if not req.get("description"):
                issues.append(f"需求 {req_id} 缺少描述")
            
            if not req.get("acceptance_criteria"):
                warnings.append(f"需求 {req_id} 缺少验收标准")
            
            if not req.get("priority"):
                warnings.append(f"需求 {req_id} 未设置优先级")
        
        conflicts = requirement_data.get("conflicts", [])
        if conflicts:
            issues.append(f"检测到需求冲突: {len(conflicts)} 处")
        
        traceability = requirement_data.get("traceability_matrix", {})
        untraced_reqs = [r.get("id") for r in requirements if r.get("id") not in traceability]
        if untraced_reqs:
            warnings.append(f"存在不可追溯需求: {untraced_reqs[:5]}")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "需求一致性良好")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="需求一致性检查通过",
                details={
                    "requirements_count": len(requirements),
                    "conflicts_count": len(conflicts),
                    "traceability_coverage": len(traceability) / len(requirements) if requirements else 0
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"需求一致性存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["补充验收标准", "建立需求追溯矩阵"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"需求一致性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["解决需求冲突", "补充需求描述"]
            )

    def check_technical_feasibility(self, tech_data: dict[str, Any]) -> CheckResult:
        """
        检查技术可行性（新增）
        
        评估技术方案的可行性：
        - 技术成熟度评估
        - 技术风险评估
        - 团队技术能力匹配
        - 技术依赖可行性
        """
        check_id = "ZSS-006"
        check_name = "技术可行性检查"
        
        issues = []
        warnings = []
        
        tech_stack = tech_data.get("tech_stack", [])
        if not tech_stack:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.HIGH,
                message="未定义技术栈",
                recommendations=["定义项目技术栈"]
            )
        
        for tech in tech_stack:
            tech_name = tech.get("name", "unknown")
            maturity = tech.get("maturity", "unknown")
            
            if maturity == "experimental":
                warnings.append(f"技术 '{tech_name}' 处于实验阶段，存在风险")
            elif maturity == "deprecated":
                issues.append(f"技术 '{tech_name}' 已废弃，不应使用")
            
            team_expertise = tech.get("team_expertise", 0)
            if team_expertise < 0.5:
                warnings.append(f"团队对 '{tech_name}' 熟练度较低: {team_expertise:.0%}")
        
        tech_risks = tech_data.get("risks", [])
        high_risks = [r for r in tech_risks if r.get("level") == "high"]
        if high_risks:
            issues.append(f"存在高风险技术项: {len(high_risks)} 个")
        
        tech_dependencies = tech_data.get("dependencies", [])
        unavailable_deps = [d for d in tech_dependencies if not d.get("available", True)]
        if unavailable_deps:
            issues.append(f"存在不可用的技术依赖: {[d.get('name') for d in unavailable_deps]}")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "技术可行性良好")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="技术可行性评估通过",
                details={
                    "tech_stack_count": len(tech_stack),
                    "risks_count": len(tech_risks),
                    "avg_team_expertise": sum(t.get("team_expertise", 0) for t in tech_stack) / len(tech_stack) if tech_stack else 0
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"技术可行性存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["提升团队技术能力", "评估实验性技术风险"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"技术可行性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["替换废弃技术", "解决技术依赖问题"]
            )

    def check_risk_assessment(self, risk_data: dict[str, Any]) -> CheckResult:
        """
        检查风险评估（新增）
        
        评估项目风险：
        - 风险识别完整性
        - 风险等级评估
        - 风险缓解措施
        - 风险监控计划
        """
        check_id = "ZSS-007"
        check_name = "风险评估检查"
        
        issues = []
        warnings = []
        
        risks = risk_data.get("risks", [])
        if not risks:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="未进行风险评估",
                recommendations=["进行项目风险评估"]
            )
        
        for risk in risks:
            risk_id = risk.get("id", "unknown")
            
            if not risk.get("description"):
                issues.append(f"风险 {risk_id} 缺少描述")
            
            if not risk.get("probability"):
                warnings.append(f"风险 {risk_id} 未评估发生概率")
            
            if not risk.get("impact"):
                warnings.append(f"风险 {risk_id} 未评估影响程度")
            
            if not risk.get("mitigation"):
                warnings.append(f"风险 {risk_id} 未定义缓解措施")
        
        high_risks = [r for r in risks if r.get("level") == "high"]
        critical_risks = [r for r in risks if r.get("level") == "critical"]
        
        if critical_risks:
            issues.append(f"存在严重风险: {len(critical_risks)} 个")
        
        unmitigated_high_risks = [r for r in high_risks if not r.get("mitigation")]
        if unmitigated_high_risks:
            issues.append(f"存在未缓解的高风险: {len(unmitigated_high_risks)} 个")
        
        risk_monitoring = risk_data.get("monitoring_plan", {})
        if not risk_monitoring:
            warnings.append("未定义风险监控计划")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "风险评估完整")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="风险评估完整，缓解措施到位",
                details={
                    "risks_count": len(risks),
                    "high_risks_count": len(high_risks),
                    "critical_risks_count": len(critical_risks),
                    "mitigated_count": sum(1 for r in risks if r.get("mitigation"))
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"风险评估存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["完善风险缓解措施", "建立风险监控计划"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"风险评估存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["解决严重风险", "为高风险制定缓解措施"]
            )

    def check_resource_matching(self, resource_data: dict[str, Any]) -> CheckResult:
        """
        检查资源匹配（新增）
        
        验证资源分配是否匹配需求：
        - 人力资源匹配
        - 时间资源匹配
        - 技术资源匹配
        - 预算资源匹配
        """
        check_id = "ZSS-008"
        check_name = "资源匹配检查"
        
        issues = []
        warnings = []
        
        required_resources = resource_data.get("required", {})
        available_resources = resource_data.get("available", {})
        
        human_required = required_resources.get("human", {})
        human_available = available_resources.get("human", {})
        
        for role, count in human_required.items():
            available_count = human_available.get(role, 0)
            if available_count < count:
                issues.append(f"角色 '{role}' 人员不足: 需要 {count}, 可用 {available_count}")
        
        time_required = required_resources.get("time", {})
        time_available = available_resources.get("time", {})
        
        if time_required.get("estimated_days", 0) > time_available.get("deadline_days", float('inf')):
            issues.append(f"预估工期超过截止日期: {time_required.get('estimated_days')} > {time_available.get('deadline_days')}")
        
        tech_required = required_resources.get("technology", [])
        tech_available = available_resources.get("technology", [])
        
        missing_tech = [t for t in tech_required if t not in tech_available]
        if missing_tech:
            warnings.append(f"缺少技术资源: {missing_tech}")
        
        budget_required = required_resources.get("budget", 0)
        budget_available = available_resources.get("budget", 0)
        
        if budget_required > budget_available:
            issues.append(f"预算不足: 需要 {budget_required}, 可用 {budget_available}")
        elif budget_required > budget_available * 0.9:
            warnings.append(f"预算接近上限: {budget_required}/{budget_available}")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "资源匹配良好")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="资源匹配检查通过",
                details={
                    "human_match": True,
                    "time_match": True,
                    "budget_match": True,
                    "budget_utilization": budget_required / budget_available if budget_available > 0 else 0
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"资源匹配存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["补充技术资源", "申请更多预算"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"资源匹配存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["补充人力资源", "调整项目工期", "申请更多预算"]
            )

    def check_requirement_analysis_completeness(self, requirement_data: dict[str, Any]) -> CheckResult:
        """
        检查需求分析完整性（增强版）
        
        验证需求分析结果的完整性：
        - 功能需求完整性
        - 非功能需求完整性
        - 用户故事完整性
        - 验收标准完整性
        - 需求优先级合理性
        - 需求依赖关系
        - 需求变更影响分析
        """
        check_id = "ZSS-009"
        check_name = "需求分析完整性检查（增强版）"
        
        issues = []
        warnings = []
        
        requirements = requirement_data.get("requirements", [])
        if not requirements:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message="未定义需求列表",
                recommendations=["定义项目需求"]
            )
        
        functional_reqs = [r for r in requirements if r.get("type") == "functional"]
        non_functional_reqs = [r for r in requirements if r.get("type") == "non_functional"]
        
        if not functional_reqs:
            issues.append("缺少功能需求定义")
        if not non_functional_reqs:
            warnings.append("缺少非功能需求定义（性能、安全、可用性等）")
        
        for i, req in enumerate(requirements):
            req_id = req.get("id", f"REQ-{i+1}")
            
            if not req.get("description"):
                issues.append(f"需求 {req_id} 缺少描述")
            
            if not req.get("acceptance_criteria"):
                warnings.append(f"需求 {req_id} 缺少验收标准")
            else:
                criteria = req.get("acceptance_criteria", [])
                if len(criteria) < 1:
                    warnings.append(f"需求 {req_id} 验收标准过少")
            
            if not req.get("priority"):
                warnings.append(f"需求 {req_id} 未设置优先级")
            else:
                priority = req.get("priority", "").lower()
                valid_priorities = ["critical", "high", "medium", "low", "p0", "p1", "p2", "p3"]
                if priority not in valid_priorities:
                    issues.append(f"需求 {req_id} 优先级值无效: {priority}")
            
            user_story = req.get("user_story", {})
            if req.get("type") == "functional":
                if not user_story:
                    warnings.append(f"功能需求 {req_id} 缺少用户故事")
                elif not user_story.get("as_a") or not user_story.get("i_want") or not user_story.get("so_that"):
                    warnings.append(f"需求 {req_id} 用户故事不完整")
            
            dependencies = req.get("depends_on", [])
            for dep_id in dependencies:
                dep_exists = any(r.get("id") == dep_id for r in requirements)
                if not dep_exists:
                    issues.append(f"需求 {req_id} 依赖不存在的需求: {dep_id}")
        
        priority_distribution = {}
        for req in requirements:
            p = req.get("priority", "medium").lower()
            priority_distribution[p] = priority_distribution.get(p, 0) + 1
        
        high_priority_ratio = (priority_distribution.get("critical", 0) + 
                               priority_distribution.get("high", 0) + 
                               priority_distribution.get("p0", 0) + 
                               priority_distribution.get("p1", 0)) / len(requirements) if requirements else 0
        
        if high_priority_ratio > 0.6:
            warnings.append(f"高优先级需求占比过高: {high_priority_ratio:.0%}，可能导致资源分散")
        
        change_impact = requirement_data.get("change_impact_analysis", {})
        if not change_impact:
            warnings.append("未进行需求变更影响分析")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "需求分析完整性良好")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="需求分析完整性检查通过",
                details={
                    "requirements_count": len(requirements),
                    "functional_count": len(functional_reqs),
                    "non_functional_count": len(non_functional_reqs),
                    "priority_distribution": priority_distribution
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"需求分析完整性存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["补充验收标准", "完善用户故事", "进行变更影响分析"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"需求分析完整性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["补充缺失的需求", "修复无效的依赖关系"]
            )

    def check_architecture_design_rationality(self, architecture_data: dict[str, Any]) -> CheckResult:
        """
        检查架构设计合理性（增强版）
        
        验证架构设计的合理性：
        - 架构模式选择合理性
        - 组件划分合理性
        - 接口设计合理性
        - 数据流设计合理性
        - 部署架构合理性
        - 安全架构合理性
        - 性能架构合理性
        - 可扩展性评估
        """
        check_id = "ZSS-010"
        check_name = "架构设计合理性检查（增强版）"
        
        issues = []
        warnings = []
        
        architecture_pattern = architecture_data.get("pattern", "")
        valid_patterns = ["monolithic", "microservices", "serverless", "event_driven", 
                         "layered", "hexagonal", "cqrs", "event_sourcing"]
        
        if not architecture_pattern:
            warnings.append("未定义架构模式")
        elif architecture_pattern not in valid_patterns:
            warnings.append(f"架构模式 '{architecture_pattern}' 可能不是标准模式")
        
        components = architecture_data.get("components", {})
        if not components:
            issues.append("未定义系统组件")
        else:
            required_components = ["presentation", "business", "data"]
            for comp in required_components:
                if comp not in components:
                    warnings.append(f"缺少标准组件层: {comp}")
            
            component_count = len(components)
            if component_count > 20:
                warnings.append(f"组件数量过多({component_count})，可能存在过度设计")
            elif component_count < 3:
                warnings.append(f"组件数量过少({component_count})，可能存在设计不足")
        
        interfaces = architecture_data.get("interfaces", [])
        for i, interface in enumerate(interfaces):
            if not interface.get("name"):
                issues.append(f"接口{i+1}缺少名称")
            if not interface.get("protocol"):
                warnings.append(f"接口{interface.get('name', i+1)}未定义通信协议")
            if not interface.get("contract"):
                warnings.append(f"接口{interface.get('name', i+1)}未定义契约")
        
        data_flow = architecture_data.get("data_flow", {})
        if not data_flow:
            warnings.append("未定义数据流设计")
        else:
            data_sources = data_flow.get("sources", [])
            data_sinks = data_flow.get("sinks", [])
            data_transformations = data_flow.get("transformations", [])
            
            if not data_sources:
                warnings.append("未定义数据源")
            if not data_sinks:
                warnings.append("未定义数据目的地")
        
        deployment = architecture_data.get("deployment", {})
        if not deployment:
            warnings.append("未定义部署架构")
        else:
            deployment_type = deployment.get("type")
            if not deployment_type:
                warnings.append("未定义部署类型")
            
            environments = deployment.get("environments", [])
            required_envs = ["development", "testing", "production"]
            for env in required_envs:
                if env not in environments:
                    warnings.append(f"缺少部署环境: {env}")
        
        security = architecture_data.get("security", {})
        if not security:
            issues.append("未定义安全架构")
        else:
            auth_mechanism = security.get("authentication")
            if not auth_mechanism:
                issues.append("未定义认证机制")
            
            authz_mechanism = security.get("authorization")
            if not authz_mechanism:
                warnings.append("未定义授权机制")
            
            encryption = security.get("encryption")
            if not encryption:
                warnings.append("未定义加密策略")
            
            security_layers = security.get("layers", [])
            if len(security_layers) < 2:
                warnings.append("安全层级过少，建议采用多层安全防护")
        
        performance = architecture_data.get("performance", {})
        if not performance:
            warnings.append("未定义性能架构")
        else:
            caching = performance.get("caching")
            if not caching:
                warnings.append("未定义缓存策略")
            
            load_balancing = performance.get("load_balancing")
            if not load_balancing:
                warnings.append("未定义负载均衡策略")
            
            response_time_sla = performance.get("response_time_sla")
            if not response_time_sla:
                warnings.append("未定义响应时间SLA")
        
        scalability = architecture_data.get("scalability", {})
        if not scalability:
            warnings.append("未定义可扩展性策略")
        else:
            scaling_type = scalability.get("type")
            if not scaling_type:
                warnings.append("未定义扩展类型（水平/垂直）")
            
            auto_scaling = scalability.get("auto_scaling")
            if auto_scaling is None:
                warnings.append("未定义自动扩展策略")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "架构设计合理性良好")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="架构设计合理性检查通过",
                details={
                    "architecture_pattern": architecture_pattern,
                    "components_count": len(components),
                    "interfaces_count": len(interfaces),
                    "security_defined": bool(security),
                    "performance_defined": bool(performance),
                    "scalability_defined": bool(scalability)
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"架构设计合理性存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["完善架构设计细节", "定义安全架构", "定义性能架构"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.ZHONGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"架构设计合理性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["定义系统组件", "定义安全架构"]
            )

    def run_all_checks(self, data: dict[str, Any]) -> list[CheckResult]:
        """运行所有中书省检查"""
        results = []
        
        results.append(self.check_decision_completeness(data.get("decision", {})))
        results.append(self.check_sdd_specification_validity(data.get("sdd", {})))
        results.append(self.check_architecture_feasibility(data.get("architecture", {})))
        results.append(self.check_priority_consistency(data.get("tasks", [])))
        results.append(self.check_requirement_consistency(data.get("requirement", {})))
        results.append(self.check_technical_feasibility(data.get("tech", {})))
        results.append(self.check_risk_assessment(data.get("risk", {})))
        results.append(self.check_resource_matching(data.get("resource", {})))
        results.append(self.check_requirement_analysis_completeness(data.get("requirement_analysis", {})))
        results.append(self.check_architecture_design_rationality(data.get("architecture_design", {})))
        
        return results


class MenxiashengLogicChecker:
    """
    门下省审议逻辑检查器
    
    负责验证审议阶段的各项逻辑：
    - 审议完整性检查
    - 测试覆盖率检查
    - 合规性检查
    - 质量门禁检查
    - 审议流程完整性检查（新增）
    - 审议历史追溯检查（新增）
    - 审议决策一致性检查（新增）
    - 审议时效性检查（新增）
    """

    def __init__(self):
        self.checks: list[CheckResult] = []
        self.context = CheckContext()

    def check_review_completeness(self, review_data: dict[str, Any]) -> CheckResult:
        """
        检查审议完整性
        
        验证所有审议项目是否已完成：
        - 需求审议
        - 架构审议
        - 测试覆盖审议
        - 合规审议
        """
        check_id = "MXS-001"
        check_name = "审议完整性检查"
        
        required_reviews = [
            "requirement_review",
            "architecture_review",
            "test_coverage_review",
            "compliance_review"
        ]
        
        missing_reviews = []
        for review in required_reviews:
            if review not in review_data:
                missing_reviews.append(review)
        
        if not missing_reviews:
            all_passed = all(
                review_data.get(r, {}).get("status") == "passed"
                for r in required_reviews
            )
            
            if all_passed:
                self.context.add_history(check_id, CheckStatus.PASS, "所有审议通过")
                return CheckResult(
                    check_id=check_id,
                    check_name=check_name,
                    province=Province.MENXIASHENG,
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.HIGH,
                    message="所有审议项目已完成并通过",
                    details={
                        "reviews": required_reviews,
                        "all_passed": True
                    }
                )
            else:
                failed_reviews = [
                    r for r in required_reviews
                    if review_data.get(r, {}).get("status") != "passed"
                ]
                self.context.add_history(check_id, CheckStatus.FAIL, f"审议未通过: {failed_reviews}")
                return CheckResult(
                    check_id=check_id,
                    check_name=check_name,
                    province=Province.MENXIASHENG,
                    status=CheckStatus.FAIL,
                    severity=CheckSeverity.HIGH,
                    message=f"以下审议项目未通过: {', '.join(failed_reviews)}",
                    details={"failed_reviews": failed_reviews},
                    recommendations=["重新审视未通过的审议项目"]
                )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"缺少审议: {missing_reviews}")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message=f"缺少审议项目: {', '.join(missing_reviews)}",
                details={"missing_reviews": missing_reviews},
                recommendations=["完成缺失的审议项目"]
            )

    def check_test_coverage_validity(self, coverage_data: dict[str, Any]) -> CheckResult:
        """
        检查测试覆盖率
        
        验证测试覆盖率是否达标：
        - 单元测试覆盖率
        - 集成测试覆盖率
        - E2E测试覆盖率
        - 核心流程覆盖
        """
        check_id = "MXS-002"
        check_name = "测试覆盖率检查"
        
        issues = []
        warnings = []
        
        unit_coverage = coverage_data.get("unit_test_coverage", 0)
        integration_coverage = coverage_data.get("integration_test_coverage", 0)
        e2e_coverage = coverage_data.get("e2e_test_coverage", 0)
        
        if unit_coverage < 80:
            issues.append(f"单元测试覆盖率不足: {unit_coverage}% (要求 >= 80%)")
        elif unit_coverage < 90:
            warnings.append(f"单元测试覆盖率建议提升: {unit_coverage}%")
        
        if integration_coverage < 60:
            issues.append(f"集成测试覆盖率不足: {integration_coverage}% (要求 >= 60%)")
        elif integration_coverage < 80:
            warnings.append(f"集成测试覆盖率建议提升: {integration_coverage}%")
        
        if e2e_coverage < 100:
            core_flows = coverage_data.get("core_flows_covered", [])
            total_core_flows = coverage_data.get("total_core_flows", 0)
            if total_core_flows > 0 and len(core_flows) < total_core_flows:
                issues.append(f"核心流程E2E测试覆盖不完整: {len(core_flows)}/{total_core_flows}")
        
        mutation_coverage = coverage_data.get("mutation_coverage", 0)
        if mutation_coverage > 0 and mutation_coverage < 70:
            warnings.append(f"变异测试覆盖率较低: {mutation_coverage}%")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "测试覆盖率达标")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="测试覆盖率达标",
                details={
                    "unit_coverage": unit_coverage,
                    "integration_coverage": integration_coverage,
                    "e2e_coverage": e2e_coverage,
                    "mutation_coverage": mutation_coverage
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"测试覆盖率存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["继续提升测试覆盖率"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"测试覆盖率不达标: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["补充测试用例", "提升测试覆盖率"]
            )

    def check_compliance_rules(self, compliance_data: dict[str, Any]) -> CheckResult:
        """
        检查合规性
        
        验证各项合规性检查：
        - 安全检查
        - 编码规范
        - 架构合规
        - 依赖安全
        """
        check_id = "MXS-003"
        check_name = "合规性检查"
        
        issues = []
        warnings = []
        
        security_checks = compliance_data.get("security_checks", {})
        if not security_checks.get("passed", False):
            issues.append(f"安全检查未通过: {security_checks.get('reason', '未知原因')}")
        
        coding_standards = compliance_data.get("coding_standards", {})
        if not coding_standards.get("compliant", False):
            violations = coding_standards.get("violations", [])
            critical_violations = [v for v in violations if v.get("severity") == "critical"]
            if critical_violations:
                issues.append(f"编码规范严重违规: {len(critical_violations)} 项")
            else:
                warnings.append(f"编码规范违规: {len(violations)} 项")
        
        architecture_compliance = compliance_data.get("architecture_compliance", {})
        if not architecture_compliance.get("compliant", False):
            issues.append("架构合规性检查未通过")
        
        dependency_check = compliance_data.get("dependency_check", {})
        vulnerabilities = dependency_check.get("vulnerabilities", [])
        critical_vulns = [v for v in vulnerabilities if v.get("severity") == "critical"]
        if critical_vulns:
            issues.append(f"存在严重依赖安全漏洞: {len(critical_vulns)} 个")
        elif vulnerabilities:
            warnings.append(f"存在依赖安全漏洞: {len(vulnerabilities)} 个")
        
        license_check = compliance_data.get("license_check", {})
        if not license_check.get("compliant", True):
            issues.append(f"许可证合规性问题: {license_check.get('issues', [])}")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "合规性检查通过")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="所有合规性检查通过",
                details={
                    "checks_passed": True,
                    "vulnerabilities_count": len(vulnerabilities)
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"合规性检查存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["修复编码规范违规", "更新有漏洞的依赖"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message=f"合规性检查未通过: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["修复安全问题", "解决编码规范违规", "更新有漏洞的依赖"]
            )

    def check_quality_gate(self, quality_data: dict[str, Any]) -> CheckResult:
        """
        检查质量门禁
        
        验证质量门禁是否通过：
        - 代码质量门禁
        - 测试质量门禁
        - 性能质量门禁
        - 安全质量门禁
        """
        check_id = "MXS-004"
        check_name = "质量门禁检查"
        
        gates = quality_data.get("gates", [])
        if not gates:
            self.context.add_history(check_id, CheckStatus.WARNING, "未定义质量门禁")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="未定义质量门禁",
                recommendations=["定义质量门禁标准"]
            )
        
        failed_gates = []
        for gate in gates:
            gate_name = gate.get("name", "unknown")
            threshold = gate.get("threshold", 0)
            actual = gate.get("actual", 0)
            
            if actual < threshold:
                failed_gates.append({
                    "name": gate_name,
                    "threshold": threshold,
                    "actual": actual,
                    "gap": threshold - actual
                })
        
        if not failed_gates:
            self.context.add_history(check_id, CheckStatus.PASS, "所有质量门禁通过")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="所有质量门禁通过",
                details={
                    "gates_count": len(gates),
                    "passed_gates": len(gates)
                }
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"{len(failed_gates)}个门禁未通过")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"质量门禁未通过: {len(failed_gates)} 项",
                details={"failed_gates": failed_gates},
                recommendations=[
                    f"提升 {g['name']} 从 {g['actual']} 到 {g['threshold']}"
                    for g in failed_gates[:5]
                ]
            )

    def check_review_process_integrity(self, process_data: dict[str, Any]) -> CheckResult:
        """
        检查审议流程完整性（新增）
        
        验证审议流程是否完整：
        - 审议流程步骤完整性
        - 审议角色分配
        - 审议文档完整性
        - 审议签名确认
        """
        check_id = "MXS-005"
        check_name = "审议流程完整性检查"
        
        issues = []
        warnings = []
        
        required_steps = [
            "initial_review",
            "technical_review",
            "security_review",
            "final_approval"
        ]
        
        steps = process_data.get("steps", [])
        completed_steps = [s.get("name") for s in steps if s.get("completed", False)]
        
        for step in required_steps:
            if step not in completed_steps:
                issues.append(f"审议步骤 '{step}' 未完成")
        
        reviewers = process_data.get("reviewers", {})
        for role in ["technical_lead", "security_officer", "product_owner"]:
            if role not in reviewers:
                warnings.append(f"未分配审议角色: {role}")
        
        documents = process_data.get("documents", [])
        required_docs = ["review_report", "decision_record", "sign_off"]
        for doc in required_docs:
            if doc not in [d.get("name") for d in documents]:
                warnings.append(f"缺少审议文档: {doc}")
        
        signatures = process_data.get("signatures", [])
        pending_signatures = [s for s in signatures if not s.get("signed", False)]
        if pending_signatures:
            issues.append(f"存在未签名确认: {len(pending_signatures)} 项")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "审议流程完整")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="审议流程完整",
                details={
                    "completed_steps": len(completed_steps),
                    "total_steps": len(required_steps),
                    "signatures_count": len(signatures)
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"审议流程存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["分配审议角色", "补充审议文档"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"审议流程存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["完成审议步骤", "完成签名确认"]
            )

    def check_review_history_traceability(self, history_data: dict[str, Any]) -> CheckResult:
        """
        检查审议历史追溯（新增）
        
        验证审议历史是否可追溯：
        - 审议记录完整性
        - 变更历史记录
        - 决策依据追溯
        - 版本一致性
        """
        check_id = "MXS-006"
        check_name = "审议历史追溯检查"
        
        issues = []
        warnings = []
        
        review_records = history_data.get("records", [])
        if not review_records:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="无审议历史记录",
                recommendations=["建立审议历史记录"]
            )
        
        for record in review_records:
            record_id = record.get("id", "unknown")
            
            if not record.get("timestamp"):
                warnings.append(f"审议记录 {record_id} 缺少时间戳")
            
            if not record.get("reviewer"):
                warnings.append(f"审议记录 {record_id} 缺少审议人")
            
            if not record.get("decision"):
                issues.append(f"审议记录 {record_id} 缺少决策结果")
        
        change_history = history_data.get("changes", [])
        untracked_changes = [c for c in change_history if not c.get("tracked", True)]
        if untracked_changes:
            warnings.append(f"存在未追踪的变更: {len(untracked_changes)} 项")
        
        decision_basis = history_data.get("decision_basis", [])
        if not decision_basis:
            warnings.append("未记录决策依据")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "审议历史可追溯")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="审议历史追溯完整",
                details={
                    "records_count": len(review_records),
                    "changes_count": len(change_history),
                    "decision_basis_count": len(decision_basis)
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"审议历史追溯存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["完善审议记录", "记录决策依据"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"审议历史追溯存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["补充审议决策结果"]
            )

    def check_review_decision_consistency(self, decision_data: dict[str, Any]) -> CheckResult:
        """
        检查审议决策一致性（新增）
        
        验证审议决策是否一致：
        - 决策与审议结果一致性
        - 多次审议决策一致性
        - 决策与规范一致性
        - 决策可执行性
        """
        check_id = "MXS-007"
        check_name = "审议决策一致性检查"
        
        issues = []
        warnings = []
        
        decisions = decision_data.get("decisions", [])
        if not decisions:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="无审议决策记录",
                recommendations=["记录审议决策"]
            )
        
        for i, decision in enumerate(decisions):
            decision_id = decision.get("id", f"DEC-{i+1}")
            
            review_result = decision.get("review_result")
            final_decision = decision.get("final_decision")
            
            if review_result == "rejected" and final_decision == "approved":
                issues.append(f"决策 {decision_id} 与审议结果不一致")
            
            if not decision.get("rationale"):
                warnings.append(f"决策 {decision_id} 缺少决策理由")
        
        conflicting_decisions = []
        for i, d1 in enumerate(decisions):
            for d2 in decisions[i+1:]:
                if d1.get("topic") == d2.get("topic") and d1.get("final_decision") != d2.get("final_decision"):
                    conflicting_decisions.append(d1.get("id"))
        
        if conflicting_decisions:
            issues.append(f"存在冲突的决策: {conflicting_decisions}")
        
        executable = decision_data.get("executable", True)
        if not executable:
            issues.append("决策不可执行")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "审议决策一致")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="审议决策一致性良好",
                details={
                    "decisions_count": len(decisions),
                    "conflicts_count": 0,
                    "executable": True
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"审议决策一致性存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["补充决策理由"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"审议决策一致性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["解决决策冲突", "确保决策可执行"]
            )

    def check_review_timeliness(self, timeliness_data: dict[str, Any]) -> CheckResult:
        """
        检查审议时效性（新增）
        
        验证审议是否及时：
        - 审议周期合理性
        - 审议响应时效
        - 审议超期检测
        - 审议效率评估
        """
        check_id = "MXS-008"
        check_name = "审议时效性检查"
        
        issues = []
        warnings = []
        
        reviews = timeliness_data.get("reviews", [])
        if not reviews:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="无审议时效数据",
                recommendations=["记录审议时效数据"]
            )
        
        overdue_reviews = []
        for review in reviews:
            review_id = review.get("id", "unknown")
            start_time = review.get("start_time")
            end_time = review.get("end_time")
            deadline = review.get("deadline")
            
            if start_time and deadline:
                if end_time:
                    if end_time > deadline:
                        overdue_reviews.append({
                            "id": review_id,
                            "delay_days": (datetime.fromisoformat(end_time) - datetime.fromisoformat(deadline)).days
                        })
                else:
                    if datetime.now() > datetime.fromisoformat(deadline):
                        overdue_reviews.append({
                            "id": review_id,
                            "delay_days": (datetime.now() - datetime.fromisoformat(deadline)).days
                        })
        
        if overdue_reviews:
            issues.append(f"存在超期审议: {len(overdue_reviews)} 项")
        
        avg_response_time = timeliness_data.get("avg_response_time_hours", 0)
        if avg_response_time > 48:
            warnings.append(f"平均审议响应时间过长: {avg_response_time} 小时")
        
        efficiency_score = timeliness_data.get("efficiency_score", 0)
        if efficiency_score < 0.7:
            warnings.append(f"审议效率评分较低: {efficiency_score:.0%}")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "审议时效性良好")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="审议时效性良好",
                details={
                    "reviews_count": len(reviews),
                    "overdue_count": 0,
                    "avg_response_time_hours": avg_response_time,
                    "efficiency_score": efficiency_score
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"审议时效性存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["提升审议响应速度", "优化审议流程"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"审议时效性存在问题: {'; '.join(issues)}",
                details={"issues": issues, "overdue_reviews": overdue_reviews},
                recommendations=["处理超期审议", "优化审议流程"]
            )

    def check_review_process_completeness(self, process_data: dict[str, Any]) -> CheckResult:
        """
        检查审议流程完整性（增强版）
        
        验证审议流程是否完整：
        - 审议阶段完整性
        - 审议角色分配
        - 审议文档完整性
        - 审议签名确认
        - 审议时间线
        - 审议反馈闭环
        - 审议版本追踪
        """
        check_id = "MXS-009"
        check_name = "审议流程完整性检查（增强版）"
        
        issues = []
        warnings = []
        
        required_steps = [
            "initial_review",
            "technical_review",
            "security_review",
            "performance_review",
            "final_approval"
        ]
        
        steps = process_data.get("steps", [])
        completed_steps = [s.get("name") for s in steps if s.get("completed", False)]
        
        for step in required_steps:
            if step not in completed_steps:
                issues.append(f"审议步骤 '{step}' 未完成")
        
        step_timeline = process_data.get("timeline", {})
        for step in steps:
            step_name = step.get("name", "unknown")
            start_time = step.get("start_time")
            end_time = step.get("end_time")
            
            if start_time and end_time:
                try:
                    start = datetime.fromisoformat(start_time)
                    end = datetime.fromisoformat(end_time)
                    if end < start:
                        issues.append(f"步骤 '{step_name}' 时间线异常：结束时间早于开始时间")
                except ValueError:
                    warnings.append(f"步骤 '{step_name}' 时间格式无效")
        
        reviewers = process_data.get("reviewers", {})
        required_roles = ["technical_lead", "security_officer", "product_owner", "architect"]
        for role in required_roles:
            if role not in reviewers:
                warnings.append(f"未分配审议角色: {role}")
            else:
                reviewer = reviewers.get(role)
                if isinstance(reviewer, dict):
                    if not reviewer.get("assigned"):
                        warnings.append(f"角色 '{role}' 未分配具体人员")
                    if not reviewer.get("available"):
                        warnings.append(f"角色 '{role}' 人员不可用")
        
        documents = process_data.get("documents", [])
        required_docs = ["review_report", "decision_record", "sign_off", "feedback_log"]
        for doc in required_docs:
            if doc not in [d.get("name") for d in documents]:
                warnings.append(f"缺少审议文档: {doc}")
            else:
                doc_info = next((d for d in documents if d.get("name") == doc), {})
                if not doc_info.get("version"):
                    warnings.append(f"文档 '{doc}' 缺少版本号")
                if not doc_info.get("approved"):
                    warnings.append(f"文档 '{doc}' 未审批")
        
        signatures = process_data.get("signatures", [])
        pending_signatures = [s for s in signatures if not s.get("signed", False)]
        if pending_signatures:
            issues.append(f"存在未签名确认: {len(pending_signatures)} 项")
        
        feedback_loop = process_data.get("feedback_loop", {})
        if not feedback_loop.get("closed", True):
            issues.append("审议反馈未闭环")
        
        open_feedbacks = feedback_loop.get("open_items", [])
        if open_feedbacks:
            warnings.append(f"存在未处理的反馈项: {len(open_feedbacks)} 个")
        
        version_tracking = process_data.get("version_tracking", {})
        if not version_tracking.get("enabled", False):
            warnings.append("未启用审议版本追踪")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "审议流程完整")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="审议流程完整性检查通过",
                details={
                    "completed_steps": len(completed_steps),
                    "total_steps": len(required_steps),
                    "signatures_count": len(signatures),
                    "feedback_closed": True
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"审议流程完整性存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["分配审议角色", "补充审议文档", "启用版本追踪"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"审议流程完整性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["完成审议步骤", "完成签名确认", "闭环反馈"]
            )

    def check_quality_gate_enhanced(self, quality_data: dict[str, Any]) -> CheckResult:
        """
        检查质量门禁（增强版）
        
        验证质量门禁是否完善：
        - 代码质量门禁
        - 测试质量门禁
        - 性能质量门禁
        - 安全质量门禁
        - 文档质量门禁
        - 门禁趋势分析
        - 门禁豁免管理
        """
        check_id = "MXS-010"
        check_name = "质量门禁检查（增强版）"
        
        issues = []
        warnings = []
        
        gates = quality_data.get("gates", [])
        if not gates:
            self.context.add_history(check_id, CheckStatus.WARNING, "未定义质量门禁")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="未定义质量门禁",
                recommendations=["定义质量门禁标准"]
            )
        
        required_gates = ["code_quality", "test_coverage", "security_scan", "performance"]
        defined_gate_names = [g.get("name") for g in gates]
        
        for gate_name in required_gates:
            if gate_name not in defined_gate_names:
                warnings.append(f"缺少质量门禁: {gate_name}")
        
        failed_gates = []
        near_threshold_gates = []
        
        for gate in gates:
            gate_name = gate.get("name", "unknown")
            threshold = gate.get("threshold", 0)
            actual = gate.get("actual", 0)
            
            if actual < threshold:
                failed_gates.append({
                    "name": gate_name,
                    "threshold": threshold,
                    "actual": actual,
                    "gap": threshold - actual
                })
            elif actual < threshold * 1.1:
                near_threshold_gates.append({
                    "name": gate_name,
                    "threshold": threshold,
                    "actual": actual,
                    "margin": actual - threshold
                })
            
            gate_type = gate.get("type")
            if gate_type == "blocking" and actual < threshold:
                issues.append(f"阻塞性门禁 '{gate_name}' 未通过")
            elif gate_type == "warning" and actual < threshold:
                warnings.append(f"警告性门禁 '{gate_name}' 未通过")
        
        if near_threshold_gates:
            warnings.append(f"存在接近阈值的门禁: {[g['name'] for g in near_threshold_gates]}")
        
        trends = quality_data.get("trends", [])
        if trends:
            declining_gates = [t for t in trends if t.get("direction") == "declining"]
            if declining_gates:
                warnings.append(f"存在下降趋势的门禁: {[g.get('name') for g in declining_gates]}")
        
        exemptions = quality_data.get("exemptions", [])
        active_exemptions = [e for e in exemptions if e.get("active", False)]
        if active_exemptions:
            for exemption in active_exemptions:
                if not exemption.get("justification"):
                    warnings.append(f"门禁豁免 '{exemption.get('gate')}' 缺少正当理由")
                if not exemption.get("expiry"):
                    warnings.append(f"门禁豁免 '{exemption.get('gate')}' 未设置过期时间")
        
        documentation_gate = next((g for g in gates if g.get("name") == "documentation"), None)
        if documentation_gate:
            doc_threshold = documentation_gate.get("threshold", 0)
            doc_actual = documentation_gate.get("actual", 0)
            if doc_actual < doc_threshold:
                warnings.append(f"文档质量门禁未达标: {doc_actual}% < {doc_threshold}%")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "所有质量门禁通过")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="所有质量门禁通过",
                details={
                    "gates_count": len(gates),
                    "passed_gates": len(gates) - len(failed_gates),
                    "near_threshold_count": len(near_threshold_gates)
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"质量门禁存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings, "near_threshold_gates": near_threshold_gates},
                recommendations=["关注接近阈值的门禁", "设置豁免过期时间"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"{len(failed_gates)}个门禁未通过")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.MENXIASHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"质量门禁未通过: {len(failed_gates)} 项",
                details={"failed_gates": failed_gates, "issues": issues},
                recommendations=[
                    f"提升 {g['name']} 从 {g['actual']} 到 {g['threshold']}"
                    for g in failed_gates[:5]
                ]
            )

    def run_all_checks(self, data: dict[str, Any]) -> list[CheckResult]:
        """运行所有门下省检查"""
        results = []
        
        results.append(self.check_review_completeness(data.get("review", {})))
        results.append(self.check_test_coverage_validity(data.get("coverage", {})))
        results.append(self.check_compliance_rules(data.get("compliance", {})))
        results.append(self.check_quality_gate(data.get("quality", {})))
        results.append(self.check_review_process_integrity(data.get("review_process", {})))
        results.append(self.check_review_history_traceability(data.get("review_history", {})))
        results.append(self.check_review_decision_consistency(data.get("review_decision", {})))
        results.append(self.check_review_timeliness(data.get("review_timeliness", {})))
        results.append(self.check_review_process_completeness(data.get("review_process_enhanced", {})))
        results.append(self.check_quality_gate_enhanced(data.get("quality_enhanced", {})))
        
        return results


class ShangshushengLogicChecker:
    """
    尚书省执行逻辑检查器
    
    负责验证执行阶段的各项逻辑：
    - 执行计划有效性检查
    - TDD循环完整性检查
    - 六部协调检查
    - 进度追踪检查
    - 执行状态一致性检查（新增）
    - 执行依赖关系检查（新增）
    - 执行资源分配检查（新增）
    - 执行异常处理检查（新增）
    """

    def __init__(self):
        self.checks: list[CheckResult] = []
        self.context = CheckContext()

    def check_execution_plan_validity(self, plan_data: dict[str, Any]) -> CheckResult:
        """
        检查执行计划有效性
        
        验证执行计划是否有效：
        - 阶段定义完整性
        - 任务分配合理性
        - 阶段依赖关系
        - 循环依赖检测
        """
        check_id = "SSS-001"
        check_name = "执行计划有效性检查"
        
        issues = []
        warnings = []
        
        stages = plan_data.get("stages", [])
        if not stages:
            self.context.add_history(check_id, CheckStatus.FAIL, "缺少阶段定义")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message="执行计划缺少阶段定义",
                recommendations=["定义执行阶段"]
            )
        
        for i, stage in enumerate(stages):
            stage_name = stage.get("name", f"阶段{i+1}")
            
            if "name" not in stage:
                issues.append(f"阶段{i+1}缺少名称")
            if "tasks" not in stage:
                issues.append(f"阶段{i+1}缺少任务列表")
            if "responsible_department" not in stage:
                warnings.append(f"阶段 '{stage_name}' 缺少负责部门")
            if "estimated_duration" not in stage:
                warnings.append(f"阶段 '{stage_name}' 缺少预估工期")
        
        dependencies = plan_data.get("stage_dependencies", [])
        if dependencies:
            circular = self._detect_circular_stage_dependencies(dependencies)
            if circular:
                issues.append(f"阶段依赖存在循环: {circular}")
        
        milestones = plan_data.get("milestones", [])
        if not milestones:
            warnings.append("未定义里程碑")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "执行计划有效")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="执行计划有效",
                details={
                    "stages_count": len(stages),
                    "milestones_count": len(milestones),
                    "dependencies_count": len(dependencies)
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"执行计划存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["完善执行计划", "定义里程碑"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"执行计划存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["完善执行计划", "解决阶段依赖问题"]
            )

    def _detect_circular_stage_dependencies(self, dependencies: list) -> list[str]:
        """检测阶段循环依赖"""
        graph: dict[str, list[str]] = {}
        
        for dep in dependencies:
            source = dep[0] if isinstance(dep, tuple) else dep.get("source", "")
            target = dep[1] if isinstance(dep, tuple) else dep.get("target", "")
            if source and target:
                if source not in graph:
                    graph[source] = []
                graph[source].append(target)
        
        circular = []
        visited: set[str] = set()
        
        def has_cycle(node: str, path: set) -> bool:
            if node in path:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            path.add(node)
            
            for neighbor in graph.get(node, []):
                if has_cycle(neighbor, path):
                    circular.append(node)
                    return True
            
            path.remove(node)
            return False
        
        for node in graph:
            has_cycle(node, set())
        
        return list(set(circular))

    def check_tdd_cycle_integrity(self, tdd_data: dict[str, Any]) -> CheckResult:
        """
        检查TDD循环完整性
        
        验证TDD循环是否完整：
        - 红阶段（测试先行）
        - 绿阶段（代码实现）
        - 蓝阶段（重构优化）
        - 循环完整性
        """
        check_id = "SSS-002"
        check_name = "TDD循环完整性检查"
        
        issues = []
        warnings = []
        
        cycles = tdd_data.get("cycles", [])
        if not cycles:
            self.context.add_history(check_id, CheckStatus.WARNING, "无TDD循环记录")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="无TDD循环记录",
                recommendations=["记录TDD循环过程"]
            )
        
        for i, cycle in enumerate(cycles):
            cycle_id = cycle.get("id", f"CYCLE-{i+1}")
            red_phase = cycle.get("red")
            green_phase = cycle.get("green")
            blue_phase = cycle.get("blue")
            
            if not red_phase:
                issues.append(f"循环 {cycle_id} 缺少红阶段(测试先行)")
            elif not red_phase.get("test_written"):
                issues.append(f"循环 {cycle_id} 红阶段未编写测试")
            elif not red_phase.get("test_failed"):
                warnings.append(f"循环 {cycle_id} 红阶段测试应失败(测试先行)")
            
            if not green_phase:
                issues.append(f"循环 {cycle_id} 缺少绿阶段(代码实现)")
            elif red_phase and not green_phase.get("tests_passed"):
                issues.append(f"循环 {cycle_id} 绿阶段测试未通过")
            
            if not blue_phase:
                warnings.append(f"循环 {cycle_id} 缺少蓝阶段(重构优化)")
            elif green_phase and not blue_phase.get("tests_still_passed"):
                issues.append(f"循环 {cycle_id} 蓝阶段重构后测试失败")
        
        tdd_compliance_rate = tdd_data.get("compliance_rate", 0)
        if tdd_compliance_rate < 0.8:
            warnings.append(f"TDD遵循率较低: {tdd_compliance_rate:.0%}")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "TDD循环完整")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="TDD循环完整且正确执行",
                details={
                    "cycles_count": len(cycles),
                    "compliance_rate": tdd_compliance_rate
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"TDD循环存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["完善TDD循环", "提升TDD遵循率"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"TDD循环存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["修复TDD循环问题", "确保红绿蓝阶段正确执行"]
            )

    def check_six_ministries_coordination(self, coordination_data: dict[str, Any]) -> CheckResult:
        """
        检查六部协调
        
        验证六部协调是否正常：
        - 各部门状态
        - TDD执行顺序
        - 部门间依赖
        - 协调效率
        """
        check_id = "SSS-003"
        check_name = "六部协调检查"
        
        issues = []
        warnings = []
        
        ministries = ["libu", "hubu", "liibu", "bingbu", "xingbu", "gongbu"]
        ministry_names = {
            "libu": "吏部",
            "hubu": "户部",
            "liibu": "礼部",
            "bingbu": "兵部",
            "xingbu": "刑部",
            "gongbu": "工部"
        }
        ministry_status = coordination_data.get("ministry_status", {})
        
        for ministry in ministries:
            status = ministry_status.get(ministry, {})
            if not status:
                issues.append(f"{ministry_names[ministry]}({ministry})状态未定义")
            elif status.get("status") == "error":
                issues.append(f"{ministry_names[ministry]}({ministry})执行出错: {status.get('error', '未知错误')}")
            elif status.get("status") == "waiting":
                waiting_for = status.get("waiting_for", "unknown")
                warnings.append(f"{ministry_names[ministry]}({ministry})等待: {waiting_for}")
        
        tdd_sequence = coordination_data.get("tdd_sequence", [])
        if tdd_sequence:
            expected_sequence = ["bingbu", "gongbu", "xingbu"]
            for i, step in enumerate(tdd_sequence):
                if i < len(expected_sequence):
                    if step.get("ministry") != expected_sequence[i]:
                        issues.append(f"TDD顺序错误: 期望 {expected_sequence[i]}, 实际 {step.get('ministry')}")
        
        coordination_issues = coordination_data.get("coordination_issues", [])
        if coordination_issues:
            warnings.append(f"存在协调问题: {len(coordination_issues)} 项")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "六部协调正常")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="六部协调正常",
                details={
                    "ministries_checked": ministries,
                    "tdd_sequence_valid": True
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"六部协调存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["解决协调问题", "优化部门间依赖"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"六部协调存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["检查各部门状态", "修正TDD执行顺序"]
            )

    def check_progress_tracking(self, progress_data: dict[str, Any]) -> CheckResult:
        """
        检查进度追踪
        
        验证进度追踪是否正常：
        - 任务完成情况
        - 阻塞任务检测
        - 里程碑状态
        - 进度预警
        """
        check_id = "SSS-004"
        check_name = "进度追踪检查"
        
        issues = []
        warnings = []
        
        total_tasks = progress_data.get("total_tasks", 0)
        completed_tasks = progress_data.get("completed_tasks", 0)
        blocked_tasks = progress_data.get("blocked_tasks", 0)
        
        if total_tasks == 0:
            issues.append("未定义任务总数")
        
        if blocked_tasks > 0:
            issues.append(f"存在阻塞任务: {blocked_tasks} 个")
        
        progress_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        milestones = progress_data.get("milestones", [])
        overdue_milestones = [
            m for m in milestones
            if m.get("status") != "completed" and m.get("overdue", False)
        ]
        if overdue_milestones:
            issues.append(f"存在逾期里程碑: {len(overdue_milestones)} 个")
        
        upcoming_milestones = [
            m for m in milestones
            if m.get("status") != "completed" and not m.get("overdue", False)
        ]
        for m in upcoming_milestones:
            if m.get("days_remaining", 0) <= 3:
                warnings.append(f"里程碑 '{m.get('name')}' 即将到期")
        
        velocity = progress_data.get("velocity", 0)
        if velocity > 0:
            expected_completion = progress_data.get("expected_completion_rate", 0)
            if progress_rate < expected_completion * 0.8:
                warnings.append(f"进度落后预期: 实际 {progress_rate:.1f}%, 预期 {expected_completion:.1f}%")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "进度追踪正常")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message=f"进度追踪正常，完成率: {progress_rate:.1f}%",
                details={
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "progress_rate": progress_rate,
                    "velocity": velocity
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"进度追踪存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["关注进度预警", "加快即将到期里程碑"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"进度追踪存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["解决阻塞任务", "处理逾期里程碑"]
            )

    def check_execution_state_consistency(self, state_data: dict[str, Any]) -> CheckResult:
        """
        检查执行状态一致性（新增）
        
        验证执行状态是否一致：
        - 任务状态一致性
        - 阶段状态一致性
        - 资源状态一致性
        - 状态同步检查
        """
        check_id = "SSS-005"
        check_name = "执行状态一致性检查"
        
        issues = []
        warnings = []
        
        tasks = state_data.get("tasks", [])
        state_inconsistencies = []
        
        for task in tasks:
            task_id = task.get("id", "unknown")
            reported_status = task.get("status")
            actual_status = task.get("actual_status")
            
            if actual_status and reported_status != actual_status:
                state_inconsistencies.append({
                    "task_id": task_id,
                    "reported": reported_status,
                    "actual": actual_status
                })
        
        if state_inconsistencies:
            issues.append(f"存在状态不一致的任务: {len(state_inconsistencies)} 个")
        
        stages = state_data.get("stages", [])
        for stage in stages:
            stage_name = stage.get("name", "unknown")
            stage_status = stage.get("status")
            tasks_status = stage.get("tasks_status", [])
            
            if stage_status == "completed":
                incomplete_tasks = [t for t in tasks_status if t.get("status") != "completed"]
                if incomplete_tasks:
                    issues.append(f"阶段 '{stage_name}' 已完成但存在未完成任务")
        
        resources = state_data.get("resources", [])
        for resource in resources:
            resource_id = resource.get("id", "unknown")
            allocated = resource.get("allocated", 0)
            used = resource.get("used", 0)
            
            if used > allocated:
                issues.append(f"资源 '{resource_id}' 使用量超过分配量")
        
        last_sync = state_data.get("last_sync_time")
        if last_sync:
            sync_time = datetime.fromisoformat(last_sync)
            if datetime.now() - sync_time > timedelta(hours=1):
                warnings.append(f"状态同步时间过长: {(datetime.now() - sync_time).seconds // 60} 分钟前")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "执行状态一致")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="执行状态一致性良好",
                details={
                    "tasks_checked": len(tasks),
                    "stages_checked": len(stages),
                    "resources_checked": len(resources)
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"执行状态一致性存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["及时同步状态"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"执行状态一致性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues, "state_inconsistencies": state_inconsistencies[:5]},
                recommendations=["修复状态不一致", "确保资源使用不超限"]
            )

    def check_execution_dependencies(self, dep_data: dict[str, Any]) -> CheckResult:
        """
        检查执行依赖关系（新增）
        
        验证执行依赖关系是否正确：
        - 任务依赖完整性
        - 依赖阻塞检测
        - 循环依赖检测
        - 依赖顺序验证
        """
        check_id = "SSS-006"
        check_name = "执行依赖关系检查"
        
        issues = []
        warnings = []
        
        tasks = dep_data.get("tasks", [])
        if not tasks:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="无任务依赖数据",
                recommendations=["定义任务依赖关系"]
            )
        
        blocked_tasks = []
        for task in tasks:
            task_id = task.get("id", "unknown")
            dependencies = task.get("depends_on", [])
            
            for dep_id in dependencies:
                dep_task = next((t for t in tasks if t.get("id") == dep_id), None)
                if dep_task:
                    if dep_task.get("status") != "completed":
                        blocked_tasks.append({
                            "task_id": task_id,
                            "blocked_by": dep_id
                        })
                else:
                    issues.append(f"任务 {task_id} 依赖不存在的任务: {dep_id}")
        
        if blocked_tasks:
            warnings.append(f"存在被阻塞的任务: {len(blocked_tasks)} 个")
        
        circular_deps = self._detect_task_circular_dependencies(tasks)
        if circular_deps:
            issues.append(f"检测到循环依赖: {circular_deps}")
        
        execution_order = dep_data.get("execution_order", [])
        if execution_order:
            order_issues = self._validate_execution_order(tasks, execution_order)
            if order_issues:
                warnings.append(f"执行顺序存在问题: {len(order_issues)} 处")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "执行依赖关系正确")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="执行依赖关系正确",
                details={
                    "tasks_count": len(tasks),
                    "blocked_count": 0,
                    "circular_count": 0
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"执行依赖关系存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings, "blocked_tasks": blocked_tasks[:5]},
                recommendations=["处理被阻塞任务", "优化执行顺序"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"执行依赖关系存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["解决循环依赖", "修复无效依赖"]
            )

    def _detect_task_circular_dependencies(self, tasks: list[dict]) -> list[str]:
        """检测任务循环依赖"""
        graph: dict[str, list[str]] = {}
        
        for task in tasks:
            task_id = task.get("id", "")
            depends_on = task.get("depends_on", [])
            if task_id:
                graph[task_id] = depends_on if isinstance(depends_on, list) else []
        
        circular = []
        visited: set[str] = set()
        
        def has_cycle(node: str, path: set) -> bool:
            if node in path:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            path.add(node)
            
            for neighbor in graph.get(node, []):
                if has_cycle(neighbor, path):
                    circular.append(node)
                    return True
            
            path.remove(node)
            return False
        
        for node in graph:
            has_cycle(node, set())
        
        return list(set(circular))

    def _validate_execution_order(self, tasks: list[dict], order: list[str]) -> list[str]:
        """验证执行顺序"""
        issues = []
        task_map = {t.get("id"): t for t in tasks}
        
        executed = set()
        for task_id in order:
            task = task_map.get(task_id)
            if task:
                depends_on = task.get("depends_on", [])
                for dep_id in depends_on:
                    if dep_id not in executed:
                        issues.append(f"任务 {task_id} 在依赖 {dep_id} 之前执行")
                executed.add(task_id)
        
        return issues

    def check_execution_resource_allocation(self, resource_data: dict[str, Any]) -> CheckResult:
        """
        检查执行资源分配（新增）
        
        验证执行资源分配是否合理：
        - 资源分配完整性
        - 资源利用率
        - 资源冲突检测
        - 资源预留检查
        """
        check_id = "SSS-007"
        check_name = "执行资源分配检查"
        
        issues = []
        warnings = []
        
        allocations = resource_data.get("allocations", [])
        if not allocations:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="无资源分配数据",
                recommendations=["定义资源分配"]
            )
        
        for allocation in allocations:
            resource_id = allocation.get("resource_id", "unknown")
            allocated = allocation.get("allocated", 0)
            required = allocation.get("required", 0)
            
            if allocated < required:
                issues.append(f"资源 '{resource_id}' 分配不足: 分配 {allocated}, 需要 {required}")
        
        resources = resource_data.get("resources", [])
        for resource in resources:
            resource_id = resource.get("id", "unknown")
            capacity = resource.get("capacity", 0)
            used = resource.get("used", 0)
            
            utilization = used / capacity if capacity > 0 else 0
            if utilization > 1.0:
                issues.append(f"资源 '{resource_id}' 超载: 使用率 {utilization:.0%}")
            elif utilization > 0.9:
                warnings.append(f"资源 '{resource_id}' 接近满载: 使用率 {utilization:.0%}")
        
        conflicts = resource_data.get("conflicts", [])
        if conflicts:
            issues.append(f"存在资源冲突: {len(conflicts)} 处")
        
        reservations = resource_data.get("reservations", [])
        unfulfilled = [r for r in reservations if not r.get("fulfilled", True)]
        if unfulfilled:
            warnings.append(f"存在未满足的资源预留: {len(unfulfilled)} 项")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "执行资源分配合理")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="执行资源分配合理",
                details={
                    "allocations_count": len(allocations),
                    "resources_count": len(resources),
                    "conflicts_count": 0
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"执行资源分配存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["优化资源利用率", "满足资源预留"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"执行资源分配存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["补充资源分配", "解决资源冲突"]
            )

    def check_execution_exception_handling(self, exception_data: dict[str, Any]) -> CheckResult:
        """
        检查执行异常处理（新增）
        
        验证执行异常处理是否完善：
        - 异常捕获完整性
        - 异常处理策略
        - 异常恢复机制
        - 异常日志记录
        """
        check_id = "SSS-008"
        check_name = "执行异常处理检查"
        
        issues = []
        warnings = []
        
        handlers = exception_data.get("handlers", [])
        if not handlers:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="无异常处理定义",
                recommendations=["定义异常处理策略"]
            )
        
        exception_types = exception_data.get("exception_types", [])
        handled_types = [h.get("type") for h in handlers]
        
        for exc_type in exception_types:
            if exc_type not in handled_types:
                warnings.append(f"异常类型 '{exc_type}' 未定义处理器")
        
        for handler in handlers:
            handler_id = handler.get("id", "unknown")
            
            if not handler.get("action"):
                issues.append(f"异常处理器 '{handler_id}' 未定义处理动作")
            
            if not handler.get("recovery_strategy"):
                warnings.append(f"异常处理器 '{handler_id}' 未定义恢复策略")
        
        unhandled_exceptions = exception_data.get("unhandled_exceptions", [])
        if unhandled_exceptions:
            issues.append(f"存在未处理的异常: {len(unhandled_exceptions)} 个")
        
        recovery_mechanisms = exception_data.get("recovery_mechanisms", [])
        if not recovery_mechanisms:
            warnings.append("未定义异常恢复机制")
        
        logging_enabled = exception_data.get("logging_enabled", True)
        if not logging_enabled:
            warnings.append("异常日志记录未启用")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "执行异常处理完善")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="执行异常处理完善",
                details={
                    "handlers_count": len(handlers),
                    "exception_types_count": len(exception_types),
                    "recovery_mechanisms_count": len(recovery_mechanisms)
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"执行异常处理存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["定义恢复策略", "启用异常日志记录"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"执行异常处理存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues, "unhandled_exceptions": unhandled_exceptions[:5]},
                recommendations=["处理未捕获异常", "定义处理动作"]
            )

    def check_execution_plan_feasibility(self, plan_data: dict[str, Any]) -> CheckResult:
        """
        检查执行计划可行性（增强版）
        
        验证执行计划是否可行：
        - 阶段定义完整性
        - 任务分配合理性
        - 阶段依赖关系
        - 循环依赖检测
        - 时间估算合理性
        - 资源匹配度
        - 风险评估
        - 回滚计划
        """
        check_id = "SSS-009"
        check_name = "执行计划可行性检查（增强版）"
        
        issues = []
        warnings = []
        
        stages = plan_data.get("stages", [])
        if not stages:
            self.context.add_history(check_id, CheckStatus.FAIL, "缺少阶段定义")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message="执行计划缺少阶段定义",
                recommendations=["定义执行阶段"]
            )
        
        total_estimated_days = 0
        for i, stage in enumerate(stages):
            stage_name = stage.get("name", f"阶段{i+1}")
            
            if "name" not in stage:
                issues.append(f"阶段{i+1}缺少名称")
            if "tasks" not in stage:
                issues.append(f"阶段{i+1}缺少任务列表")
            else:
                tasks = stage.get("tasks", [])
                if len(tasks) == 0:
                    warnings.append(f"阶段 '{stage_name}' 任务列表为空")
                
                for task in tasks:
                    if not task.get("assignee"):
                        warnings.append(f"阶段 '{stage_name}' 存在未分配的任务")
                    if not task.get("estimated_hours"):
                        warnings.append(f"阶段 '{stage_name}' 存在未估算时间的任务")
            
            if "responsible_department" not in stage:
                warnings.append(f"阶段 '{stage_name}' 缺少负责部门")
            
            estimated_duration = stage.get("estimated_duration", 0)
            if estimated_duration <= 0:
                warnings.append(f"阶段 '{stage_name}' 预估工期无效")
            else:
                total_estimated_days += estimated_duration
        
        dependencies = plan_data.get("stage_dependencies", [])
        if dependencies:
            circular = self._detect_circular_stage_dependencies(dependencies)
            if circular:
                issues.append(f"阶段依赖存在循环: {circular}")
        
        milestones = plan_data.get("milestones", [])
        if not milestones:
            warnings.append("未定义里程碑")
        else:
            for milestone in milestones:
                if not milestone.get("due_date"):
                    warnings.append(f"里程碑 '{milestone.get('name')}' 缺少截止日期")
                if not milestone.get("deliverables"):
                    warnings.append(f"里程碑 '{milestone.get('name')}' 缺少交付物定义")
        
        timeline = plan_data.get("timeline", {})
        deadline = timeline.get("deadline_days", 0)
        if deadline > 0 and total_estimated_days > deadline:
            issues.append(f"预估工期({total_estimated_days}天)超过截止日期({deadline}天)")
        elif deadline > 0 and total_estimated_days > deadline * 0.9:
            warnings.append(f"预估工期({total_estimated_days}天)接近截止日期({deadline}天)")
        
        resource_match = plan_data.get("resource_match", {})
        if resource_match:
            unavailable_resources = [r for r in resource_match.get("resources", []) if not r.get("available", True)]
            if unavailable_resources:
                issues.append(f"存在不可用资源: {[r.get('name') for r in unavailable_resources]}")
            
            skill_gaps = resource_match.get("skill_gaps", [])
            if skill_gaps:
                warnings.append(f"存在技能缺口: {skill_gaps}")
        
        risks = plan_data.get("risks", [])
        high_risks = [r for r in risks if r.get("level") == "high"]
        if high_risks:
            for risk in high_risks:
                if not risk.get("mitigation"):
                    issues.append(f"高风险 '{risk.get('name')}' 未定义缓解措施")
        
        rollback_plan = plan_data.get("rollback_plan", {})
        if not rollback_plan:
            warnings.append("未定义回滚计划")
        else:
            if not rollback_plan.get("trigger_conditions"):
                warnings.append("回滚计划缺少触发条件")
            if not rollback_plan.get("steps"):
                warnings.append("回滚计划缺少执行步骤")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "执行计划可行")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="执行计划可行性检查通过",
                details={
                    "stages_count": len(stages),
                    "total_estimated_days": total_estimated_days,
                    "milestones_count": len(milestones),
                    "risks_count": len(risks)
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"执行计划可行性存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["完善执行计划", "定义里程碑", "制定回滚计划"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"执行计划可行性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["解决阶段依赖问题", "补充高风险缓解措施", "确保资源可用"]
            )

    def check_resource_allocation_rationality(self, resource_data: dict[str, Any]) -> CheckResult:
        """
        检查资源分配合理性（增强版）
        
        验证资源分配是否合理：
        - 人力资源分配
        - 计算资源分配
        - 时间资源分配
        - 预算资源分配
        - 资源利用率
        - 资源冲突检测
        - 资源预留管理
        """
        check_id = "SSS-010"
        check_name = "资源分配合理性检查（增强版）"
        
        issues = []
        warnings = []
        
        human_resources = resource_data.get("human", {})
        if not human_resources:
            issues.append("未定义人力资源分配")
        else:
            roles = human_resources.get("roles", [])
            for role in roles:
                role_name = role.get("name", "unknown")
                required = role.get("required", 0)
                assigned = role.get("assigned", 0)
                
                if assigned < required:
                    issues.append(f"角色 '{role_name}' 人员不足: 需要 {required}, 已分配 {assigned}")
                elif assigned > required * 1.5:
                    warnings.append(f"角色 '{role_name}' 人员过剩: 需要 {required}, 已分配 {assigned}")
                
                availability = role.get("availability", 1.0)
                if availability < 0.8:
                    warnings.append(f"角色 '{role_name}' 可用性较低: {availability:.0%}")
            
            skills = human_resources.get("skills", [])
            required_skills = human_resources.get("required_skills", [])
            for skill in required_skills:
                if skill not in skills:
                    warnings.append(f"缺少技能: {skill}")
        
        compute_resources = resource_data.get("compute", {})
        if not compute_resources:
            warnings.append("未定义计算资源分配")
        else:
            servers = compute_resources.get("servers", [])
            for server in servers:
                server_name = server.get("name", "unknown")
                cpu_allocated = server.get("cpu_allocated", 0)
                cpu_total = server.get("cpu_total", 0)
                
                if cpu_allocated > cpu_total:
                    issues.append(f"服务器 '{server_name}' CPU超分配: {cpu_allocated}/{cpu_total}")
                elif cpu_allocated > cpu_total * 0.9:
                    warnings.append(f"服务器 '{server_name}' CPU接近满载: {cpu_allocated}/{cpu_total}")
                
                memory_allocated = server.get("memory_allocated", 0)
                memory_total = server.get("memory_total", 0)
                
                if memory_allocated > memory_total:
                    issues.append(f"服务器 '{server_name}' 内存超分配: {memory_allocated}/{memory_total}")
            
            storage = compute_resources.get("storage", {})
            storage_used = storage.get("used", 0)
            storage_total = storage.get("total", 0)
            
            if storage_total > 0:
                storage_utilization = storage_used / storage_total
                if storage_utilization > 0.9:
                    warnings.append(f"存储利用率过高: {storage_utilization:.0%}")
        
        time_resources = resource_data.get("time", {})
        if time_resources:
            total_available = time_resources.get("total_available_hours", 0)
            total_required = time_resources.get("total_required_hours", 0)
            
            if total_required > total_available:
                issues.append(f"时间资源不足: 需要 {total_required} 小时, 可用 {total_available} 小时")
            elif total_required > total_available * 0.9:
                warnings.append(f"时间资源紧张: 需要 {total_required} 小时, 可用 {total_available} 小时")
            
            buffer = time_resources.get("buffer_hours", 0)
            buffer_ratio = buffer / total_required if total_required > 0 else 0
            if buffer_ratio < 0.1:
                warnings.append(f"时间缓冲不足: {buffer_ratio:.0%} (建议 >= 10%)")
        
        budget = resource_data.get("budget", {})
        if budget:
            allocated = budget.get("allocated", 0)
            required = budget.get("required", 0)
            
            if required > allocated:
                issues.append(f"预算不足: 需要 {required}, 分配 {allocated}")
            elif required > allocated * 0.9:
                warnings.append(f"预算接近上限: 需要 {required}, 分配 {allocated}")
            
            contingency = budget.get("contingency", 0)
            contingency_ratio = contingency / allocated if allocated > 0 else 0
            if contingency_ratio < 0.1:
                warnings.append(f"应急预算不足: {contingency_ratio:.0%} (建议 >= 10%)")
        
        conflicts = resource_data.get("conflicts", [])
        if conflicts:
            for conflict in conflicts:
                issues.append(f"资源冲突: {conflict.get('resource')} 被 {conflict.get('parties')} 同时需求")
        
        reservations = resource_data.get("reservations", [])
        if reservations:
            unfulfilled = [r for r in reservations if not r.get("fulfilled", True)]
            if unfulfilled:
                warnings.append(f"存在未满足的资源预留: {len(unfulfilled)} 项")
        
        utilization = resource_data.get("utilization", {})
        if utilization:
            avg_utilization = utilization.get("average", 0)
            if avg_utilization < 0.5:
                warnings.append(f"资源利用率偏低: {avg_utilization:.0%}")
            elif avg_utilization > 0.95:
                warnings.append(f"资源利用率过高: {avg_utilization:.0%}，可能导致瓶颈")
        
        if not issues and not warnings:
            self.context.add_history(check_id, CheckStatus.PASS, "资源分配合理")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="资源分配合理性检查通过",
                details={
                    "human_roles": len(human_resources.get("roles", [])),
                    "compute_servers": len(compute_resources.get("servers", [])),
                    "budget_allocated": budget.get("allocated", 0),
                    "utilization": utilization.get("average", 0)
                }
            )
        elif not issues:
            self.context.add_history(check_id, CheckStatus.WARNING, f"存在{len(warnings)}个建议")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"资源分配合理性存在建议: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["优化资源利用率", "增加时间缓冲", "补充应急预算"]
            )
        else:
            self.context.add_history(check_id, CheckStatus.FAIL, f"存在{len(issues)}个问题")
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=Province.SHANGSHUSHENG,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"资源分配合理性存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["补充人力资源", "解决资源冲突", "增加预算"]
            )

    def run_all_checks(self, data: dict[str, Any]) -> list[CheckResult]:
        """运行所有尚书省检查"""
        results = []
        
        results.append(self.check_execution_plan_validity(data.get("plan", {})))
        results.append(self.check_tdd_cycle_integrity(data.get("tdd", {})))
        results.append(self.check_six_ministries_coordination(data.get("coordination", {})))
        results.append(self.check_progress_tracking(data.get("progress", {})))
        results.append(self.check_execution_state_consistency(data.get("execution_state", {})))
        results.append(self.check_execution_dependencies(data.get("execution_deps", {})))
        results.append(self.check_execution_resource_allocation(data.get("execution_resource", {})))
        results.append(self.check_execution_exception_handling(data.get("exception", {})))
        results.append(self.check_execution_plan_feasibility(data.get("plan_enhanced", {})))
        results.append(self.check_resource_allocation_rationality(data.get("resource_enhanced", {})))
        
        return results


class ProvincialFlowChecker:
    """
    三省信息流转检查器
    
    负责验证三省之间的信息流转：
    - 中书省到门下省流转
    - 门下省到尚书省流转
    - 执行反馈流转
    - 流转时效性检查（新增）
    - 流转数据完整性检查（新增）
    - 流转状态同步检查（新增）
    - 流转异常处理检查（新增）
    """

    def __init__(self):
        self.flow_results: list[FlowCheckResult] = []
        self.context = CheckContext()

    def check_zhongshusheng_to_menxiasheng(self, data: dict[str, Any]) -> FlowCheckResult:
        """
        检查中书省到门下省信息流转
        
        验证决策信息是否正确流转到审议阶段：
        - SDD规范传递
        - 架构设计传递
        - 验收测试传递
        - 数据完整性验证
        """
        decision_output = data.get("zhongshusheng_output", {})
        menxiasheng_input = data.get("menxiasheng_input", {})
        
        required_outputs = ["sdd_specification", "architecture_design", "acceptance_tests"]
        data_integrity = True
        issues = []
        transferred_items = 0
        
        for output in required_outputs:
            if output not in decision_output:
                issues.append(f"中书省输出缺少: {output}")
                data_integrity = False
            elif output not in menxiasheng_input:
                issues.append(f"门下省未接收到: {output}")
                data_integrity = False
            else:
                transferred_items += 1
        
        flow_time = data.get("flow_time_zhongshusheng_to_menxiasheng", 0)
        
        if data_integrity:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type=FlowType.DECISION_TO_REVIEW.value,
                status=CheckStatus.PASS,
                message="中书省到门下省信息流转正常",
                data_integrity=True,
                flow_duration_ms=flow_time,
                data_items_transferred=transferred_items
            )
        else:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type=FlowType.DECISION_TO_REVIEW.value,
                status=CheckStatus.FAIL,
                message=f"信息流转存在问题: {'; '.join(issues[:5])}",
                data_integrity=False,
                validation_errors=issues
            )

    def check_menxiasheng_to_shangshusheng(self, data: dict[str, Any]) -> FlowCheckResult:
        """
        检查门下省到尚书省信息流转
        
        验证审议结果是否正确流转到执行阶段：
        - 审议批准传递
        - 质量门禁结果传递
        - 审议意见传递
        - 数据完整性验证
        """
        menxiasheng_output = data.get("menxiasheng_output", {})
        shangshusheng_input = data.get("shangshusheng_input", {})
        
        required_outputs = ["review_approval", "quality_gate_result"]
        data_integrity = True
        issues = []
        transferred_items = 0
        
        for output in required_outputs:
            if output not in menxiasheng_output:
                issues.append(f"门下省输出缺少: {output}")
                data_integrity = False
            elif output not in shangshusheng_input:
                issues.append(f"尚书省未接收到: {output}")
                data_integrity = False
            else:
                transferred_items += 1
        
        approval_status = menxiasheng_output.get("review_approval", {}).get("status")
        if approval_status != "approved":
            issues.append(f"审议未通过，状态: {approval_status}")
            return FlowCheckResult(
                from_province=Province.MENXIASHENG,
                to_province=Province.SHANGSHUSHENG,
                flow_type=FlowType.REVIEW_TO_EXECUTION.value,
                status=CheckStatus.FAIL,
                message=f"审议未通过，无法流转到执行阶段",
                data_integrity=False,
                validation_errors=issues
            )
        
        flow_time = data.get("flow_time_menxiasheng_to_shangshusheng", 0)
        
        if data_integrity:
            return FlowCheckResult(
                from_province=Province.MENXIASHENG,
                to_province=Province.SHANGSHUSHENG,
                flow_type=FlowType.REVIEW_TO_EXECUTION.value,
                status=CheckStatus.PASS,
                message="门下省到尚书省信息流转正常",
                data_integrity=True,
                flow_duration_ms=flow_time,
                data_items_transferred=transferred_items
            )
        else:
            return FlowCheckResult(
                from_province=Province.MENXIASHENG,
                to_province=Province.SHANGSHUSHENG,
                flow_type=FlowType.REVIEW_TO_EXECUTION.value,
                status=CheckStatus.FAIL,
                message=f"信息流转存在问题: {'; '.join(issues[:5])}",
                data_integrity=False,
                validation_errors=issues
            )

    def check_feedback_flow(self, data: dict[str, Any]) -> FlowCheckResult:
        """
        检查反馈流转
        
        验证执行反馈是否正确流转：
        - 完成反馈
        - 驳回反馈
        - 异常反馈
        - 数据完整性验证
        """
        feedback = data.get("feedback", {})
        
        has_rejection = feedback.get("rejection", False)
        rejection_from = feedback.get("rejected_by", "")
        rejection_to = feedback.get("return_to", "")
        
        if has_rejection:
            rejection_reason = feedback.get("reason", "未提供原因")
            return FlowCheckResult(
                from_province=Province(rejection_from) if rejection_from else Province.MENXIASHENG,
                to_province=Province(rejection_to) if rejection_to else Province.ZHONGSHUSHENG,
                flow_type=FlowType.REJECTION_FLOW.value,
                status=CheckStatus.WARNING,
                message=f"存在驳回反馈，需要返回修正: {rejection_reason}",
                data_integrity=True
            )
        
        completion_status = feedback.get("completion_status", "unknown")
        if completion_status == "failed":
            return FlowCheckResult(
                from_province=Province.SHANGSHUSHENG,
                to_province=Province.ZHONGSHUSHENG,
                flow_type=FlowType.EXECUTION_FEEDBACK.value,
                status=CheckStatus.FAIL,
                message=f"执行失败，需要重新决策",
                data_integrity=True
            )
        
        return FlowCheckResult(
            from_province=Province.SHANGSHUSHENG,
            to_province=Province.ZHONGSHUSHENG,
            flow_type=FlowType.EXECUTION_FEEDBACK.value,
            status=CheckStatus.PASS,
            message="执行完成，反馈正常",
            data_integrity=True
        )

    def check_flow_timeliness(self, flow_data: dict[str, Any]) -> FlowCheckResult:
        """
        检查流转时效性（新增）
        
        验证信息流转是否及时：
        - 流转响应时间
        - 流转超期检测
        - 流转效率评估
        """
        flows = flow_data.get("flows", [])
        if not flows:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="timeliness_check",
                status=CheckStatus.WARNING,
                message="无流转时效数据",
                data_integrity=True
            )
        
        issues = []
        overdue_flows = []
        
        for flow in flows:
            flow_id = flow.get("id", "unknown")
            expected_time = flow.get("expected_time_ms", 0)
            actual_time = flow.get("actual_time_ms", 0)
            
            if actual_time > expected_time * 1.5:
                overdue_flows.append({
                    "id": flow_id,
                    "expected": expected_time,
                    "actual": actual_time
                })
        
        if overdue_flows:
            issues.append(f"存在超期流转: {len(overdue_flows)} 项")
        
        avg_flow_time = flow_data.get("avg_flow_time_ms", 0)
        threshold = flow_data.get("threshold_ms", 3600000)
        
        if avg_flow_time > threshold:
            issues.append(f"平均流转时间过长: {avg_flow_time}ms")
        
        if not issues:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="timeliness_check",
                status=CheckStatus.PASS,
                message="流转时效性良好",
                data_integrity=True,
                flow_duration_ms=avg_flow_time
            )
        else:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="timeliness_check",
                status=CheckStatus.WARNING,
                message=f"流转时效性存在问题: {'; '.join(issues)}",
                data_integrity=True,
                validation_errors=issues
            )

    def check_flow_data_integrity(self, integrity_data: dict[str, Any]) -> FlowCheckResult:
        """
        检查流转数据完整性（新增）
        
        验证流转数据的完整性：
        - 数据校验和验证
        - 数据格式验证
        - 数据一致性验证
        """
        transfers = integrity_data.get("transfers", [])
        if not transfers:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="integrity_check",
                status=CheckStatus.WARNING,
                message="无流转数据完整性记录",
                data_integrity=True
            )
        
        issues = []
        integrity_issues = []
        
        for transfer in transfers:
            transfer_id = transfer.get("id", "unknown")
            
            checksum_sent = transfer.get("checksum_sent")
            checksum_received = transfer.get("checksum_received")
            
            if checksum_sent and checksum_received and checksum_sent != checksum_received:
                integrity_issues.append({
                    "id": transfer_id,
                    "issue": "checksum_mismatch"
                })
            
            format_valid = transfer.get("format_valid", True)
            if not format_valid:
                integrity_issues.append({
                    "id": transfer_id,
                    "issue": "invalid_format"
                })
        
        if integrity_issues:
            issues.append(f"存在数据完整性问题: {len(integrity_issues)} 项")
        
        if not issues:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="integrity_check",
                status=CheckStatus.PASS,
                message="流转数据完整性良好",
                data_integrity=True,
                data_items_transferred=len(transfers)
            )
        else:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="integrity_check",
                status=CheckStatus.FAIL,
                message=f"流转数据完整性存在问题: {'; '.join(issues)}",
                data_integrity=False,
                validation_errors=issues
            )

    def check_flow_state_synchronization(self, sync_data: dict[str, Any]) -> FlowCheckResult:
        """
        检查流转状态同步（新增）
        
        验证流转状态是否同步：
        - 状态一致性检查
        - 状态同步延迟
        - 状态冲突检测
        """
        sync_records = sync_data.get("sync_records", [])
        if not sync_records:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="sync_check",
                status=CheckStatus.WARNING,
                message="无流转状态同步记录",
                data_integrity=True
            )
        
        issues = []
        sync_issues = []
        
        for record in sync_records:
            record_id = record.get("id", "unknown")
            source_state = record.get("source_state")
            target_state = record.get("target_state")
            
            if source_state != target_state:
                sync_issues.append({
                    "id": record_id,
                    "source": source_state,
                    "target": target_state
                })
        
        if sync_issues:
            issues.append(f"存在状态不同步: {len(sync_issues)} 项")
        
        last_sync = sync_data.get("last_sync_time")
        if last_sync:
            sync_time = datetime.fromisoformat(last_sync)
            if datetime.now() - sync_time > timedelta(minutes=30):
                issues.append(f"状态同步延迟: {(datetime.now() - sync_time).seconds // 60} 分钟")
        
        conflicts = sync_data.get("conflicts", [])
        if conflicts:
            issues.append(f"存在状态冲突: {len(conflicts)} 项")
        
        if not issues:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="sync_check",
                status=CheckStatus.PASS,
                message="流转状态同步正常",
                data_integrity=True
            )
        else:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="sync_check",
                status=CheckStatus.WARNING,
                message=f"流转状态同步存在问题: {'; '.join(issues)}",
                data_integrity=True,
                validation_errors=issues
            )

    def check_flow_exception_handling(self, exception_data: dict[str, Any]) -> FlowCheckResult:
        """
        检查流转异常处理（新增）
        
        验证流转异常处理是否完善：
        - 异常捕获机制
        - 异常恢复策略
        - 异常通知机制
        """
        handlers = exception_data.get("handlers", [])
        if not handlers:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="exception_check",
                status=CheckStatus.WARNING,
                message="无流转异常处理定义",
                data_integrity=True
            )
        
        issues = []
        
        exception_types = exception_data.get("exception_types", [])
        handled_types = [h.get("type") for h in handlers]
        
        for exc_type in exception_types:
            if exc_type not in handled_types:
                issues.append(f"异常类型 '{exc_type}' 未定义处理器")
        
        unhandled_exceptions = exception_data.get("unhandled_exceptions", [])
        if unhandled_exceptions:
            issues.append(f"存在未处理的流转异常: {len(unhandled_exceptions)} 个")
        
        notification_enabled = exception_data.get("notification_enabled", True)
        if not notification_enabled:
            issues.append("流转异常通知未启用")
        
        if not issues:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="exception_check",
                status=CheckStatus.PASS,
                message="流转异常处理完善",
                data_integrity=True
            )
        else:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="exception_check",
                status=CheckStatus.WARNING,
                message=f"流转异常处理存在问题: {'; '.join(issues)}",
                data_integrity=True,
                validation_errors=issues
            )

    def check_information_transfer_integrity(self, transfer_data: dict[str, Any]) -> FlowCheckResult:
        """
        检查信息传递完整性（增强版）
        
        验证信息传递是否完整：
        - 数据完整性校验
        - 数据格式验证
        - 数据版本一致性
        - 数据追溯性
        - 数据加密验证
        - 数据压缩验证
        """
        transfers = transfer_data.get("transfers", [])
        if not transfers:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="integrity_enhanced",
                status=CheckStatus.WARNING,
                message="无信息传递记录",
                data_integrity=True
            )
        
        issues = []
        warnings = []
        
        for transfer in transfers:
            transfer_id = transfer.get("id", "unknown")
            
            checksum_sent = transfer.get("checksum_sent")
            checksum_received = transfer.get("checksum_received")
            if checksum_sent and checksum_received and checksum_sent != checksum_received:
                issues.append(f"传输 {transfer_id} 校验和不匹配")
            
            format_valid = transfer.get("format_valid", True)
            if not format_valid:
                issues.append(f"传输 {transfer_id} 数据格式无效")
            
            version_sent = transfer.get("version_sent")
            version_received = transfer.get("version_received")
            if version_sent and version_received and version_sent != version_received:
                warnings.append(f"传输 {transfer_id} 版本不一致: 发送 {version_sent}, 接收 {version_received}")
            
            traceability = transfer.get("traceability", {})
            if not traceability.get("enabled", False):
                warnings.append(f"传输 {transfer_id} 未启用追溯")
            
            encryption = transfer.get("encryption", {})
            if encryption.get("required", False) and not encryption.get("applied", True):
                issues.append(f"传输 {transfer_id} 未应用必需的加密")
            
            compression = transfer.get("compression", {})
            if compression.get("expected_ratio") and compression.get("actual_ratio"):
                expected = compression.get("expected_ratio")
                actual = compression.get("actual_ratio")
                if actual < expected * 0.5:
                    warnings.append(f"传输 {transfer_id} 压缩率低于预期")
        
        if not issues and not warnings:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="integrity_enhanced",
                status=CheckStatus.PASS,
                message="信息传递完整性良好",
                data_integrity=True,
                data_items_transferred=len(transfers)
            )
        elif not issues:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="integrity_enhanced",
                status=CheckStatus.WARNING,
                message=f"信息传递完整性存在建议: {'; '.join(warnings[:3])}",
                data_integrity=True,
                validation_errors=warnings
            )
        else:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="integrity_enhanced",
                status=CheckStatus.FAIL,
                message=f"信息传递完整性存在问题: {'; '.join(issues[:3])}",
                data_integrity=False,
                validation_errors=issues
            )

    def check_state_synchronization_correctness(self, sync_data: dict[str, Any]) -> FlowCheckResult:
        """
        检查状态同步正确性（增强版）
        
        验证状态同步是否正确：
        - 状态一致性检查
        - 状态同步延迟
        - 状态冲突检测
        - 状态版本控制
        - 状态回滚能力
        - 状态审计日志
        """
        sync_records = sync_data.get("sync_records", [])
        if not sync_records:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="sync_enhanced",
                status=CheckStatus.WARNING,
                message="无状态同步记录",
                data_integrity=True
            )
        
        issues = []
        warnings = []
        
        for record in sync_records:
            record_id = record.get("id", "unknown")
            source_state = record.get("source_state")
            target_state = record.get("target_state")
            
            if source_state != target_state:
                issues.append(f"记录 {record_id} 状态不一致: 源 {source_state}, 目标 {target_state}")
            
            sync_delay = record.get("sync_delay_ms", 0)
            threshold = record.get("threshold_ms", 5000)
            if sync_delay > threshold:
                warnings.append(f"记录 {record_id} 同步延迟过高: {sync_delay}ms > {threshold}ms")
        
        conflicts = sync_data.get("conflicts", [])
        if conflicts:
            for conflict in conflicts:
                issues.append(f"状态冲突: {conflict.get('description')} 涉及 {conflict.get('parties')}")
        
        version_control = sync_data.get("version_control", {})
        if not version_control.get("enabled", False):
            warnings.append("未启用状态版本控制")
        else:
            version_conflicts = version_control.get("conflicts", [])
            if version_conflicts:
                issues.append(f"存在版本冲突: {len(version_conflicts)} 个")
        
        rollback = sync_data.get("rollback", {})
        if not rollback.get("available", True):
            warnings.append("状态回滚能力不可用")
        
        audit_log = sync_data.get("audit_log", {})
        if not audit_log.get("enabled", False):
            warnings.append("未启用状态审计日志")
        else:
            missing_logs = audit_log.get("missing_entries", [])
            if missing_logs:
                warnings.append(f"审计日志缺失条目: {len(missing_logs)} 个")
        
        last_sync = sync_data.get("last_sync_time")
        if last_sync:
            try:
                sync_time = datetime.fromisoformat(last_sync)
                if datetime.now() - sync_time > timedelta(minutes=30):
                    warnings.append(f"状态同步延迟: {(datetime.now() - sync_time).seconds // 60} 分钟前")
            except ValueError:
                warnings.append("最后同步时间格式无效")
        
        if not issues and not warnings:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="sync_enhanced",
                status=CheckStatus.PASS,
                message="状态同步正确性良好",
                data_integrity=True
            )
        elif not issues:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="sync_enhanced",
                status=CheckStatus.WARNING,
                message=f"状态同步正确性存在建议: {'; '.join(warnings[:3])}",
                data_integrity=True,
                validation_errors=warnings
            )
        else:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="sync_enhanced",
                status=CheckStatus.FAIL,
                message=f"状态同步正确性存在问题: {'; '.join(issues[:3])}",
                data_integrity=False,
                validation_errors=issues
            )

    def run_all_flow_checks(self, data: dict[str, Any]) -> list[FlowCheckResult]:
        """运行所有流转检查"""
        results = []
        
        results.append(self.check_zhongshusheng_to_menxiasheng(data))
        results.append(self.check_menxiasheng_to_shangshusheng(data))
        results.append(self.check_feedback_flow(data))
        results.append(self.check_flow_timeliness(data.get("flow_timeliness", {})))
        results.append(self.check_flow_data_integrity(data.get("flow_integrity", {})))
        results.append(self.check_flow_state_synchronization(data.get("flow_sync", {})))
        results.append(self.check_flow_exception_handling(data.get("flow_exception", {})))
        results.append(self.check_information_transfer_integrity(data.get("transfer_integrity", {})))
        results.append(self.check_state_synchronization_correctness(data.get("state_sync", {})))
        
        return results


class ProvincialLogicChecker:
    """
    三省协调逻辑检查器主类
    
    整合三省检查器，提供统一的检查接口：
    - 全量检查
    - 分省检查
    - 流转检查
    - 报告生成
    """

    def __init__(self, output_dir: Path = None):
        self.path_manager = PathConfigManager()
        self.output_dir = output_dir or self.path_manager.get_docs_reports_path() / "provincial_checks"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.zhongshusheng_checker = ZhongshushengLogicChecker()
        self.menxiasheng_checker = MenxiashengLogicChecker()
        self.shangshusheng_checker = ShangshushengLogicChecker()
        self.flow_checker = ProvincialFlowChecker()
        
        self._check_history: list[dict[str, Any]] = []

    def check_all(self, data: dict[str, Any]) -> ProvincialLogicReport:
        """执行所有检查"""
        start_time = datetime.now()
        all_results: list[CheckResult] = []
        
        all_results.extend(self.zhongshusheng_checker.run_all_checks(data))
        all_results.extend(self.menxiasheng_checker.run_all_checks(data))
        all_results.extend(self.shangshusheng_checker.run_all_checks(data))
        
        flow_results = self.flow_checker.run_all_flow_checks(data)
        
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
        
        summary = self._generate_summary(all_results, flow_results)
        
        end_time = datetime.now()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000
        
        report = ProvincialLogicReport(
            report_id=f"PLC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            total_checks=len(all_results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            skipped=skipped,
            results=all_results,
            flow_results=flow_results,
            summary=summary,
            overall_status=overall_status,
            check_history=self._check_history,
            performance_metrics={
                "execution_time_ms": execution_time_ms,
                "checks_per_second": len(all_results) / (execution_time_ms / 1000) if execution_time_ms > 0 else 0
            }
        )
        
        self._check_history.append({
            "report_id": report.report_id,
            "timestamp": report.generated_at,
            "overall_status": overall_status.value,
            "total_checks": len(all_results)
        })
        
        return report

    def check_province(self, province: Province, data: dict[str, Any]) -> list[CheckResult]:
        """检查指定省份"""
        if province == Province.ZHONGSHUSHENG:
            return self.zhongshusheng_checker.run_all_checks(data)
        elif province == Province.MENXIASHENG:
            return self.menxiasheng_checker.run_all_checks(data)
        elif province == Province.SHANGSHUSHENG:
            return self.shangshusheng_checker.run_all_checks(data)
        else:
            return []

    def check_flow(self, data: dict[str, Any]) -> list[FlowCheckResult]:
        """检查信息流转"""
        return self.flow_checker.run_all_flow_checks(data)

    def _generate_summary(self, results: list[CheckResult], flow_results: list[FlowCheckResult]) -> dict[str, Any]:
        """生成检查摘要"""
        by_province: dict[str, dict[str, int]] = {}
        
        for province in Province:
            province_results = [r for r in results if r.province == province]
            by_province[province.value] = {
                "total": len(province_results),
                "passed": sum(1 for r in province_results if r.status == CheckStatus.PASS),
                "failed": sum(1 for r in province_results if r.status == CheckStatus.FAIL),
                "warnings": sum(1 for r in province_results if r.status == CheckStatus.WARNING)
            }
        
        critical_issues = [
            {"check_id": r.check_id, "message": r.message}
            for r in results
            if r.status == CheckStatus.FAIL and r.severity == CheckSeverity.CRITICAL
        ]
        
        flow_integrity = all(fr.data_integrity for fr in flow_results)
        
        return {
            "by_province": by_province,
            "critical_issues": critical_issues,
            "flow_integrity": flow_integrity,
            "recommendations": self._generate_recommendations(results)
        }

    def _generate_recommendations(self, results: list[CheckResult]) -> list[str]:
        """生成改进建议"""
        all_recommendations = []
        for result in results:
            all_recommendations.extend(result.recommendations)
        
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        return unique_recommendations[:10]

    def save_report(self, report: ProvincialLogicReport, output_path: Path = None) -> Path:
        """保存报告"""
        output_path = output_path or self.output_dir / f"provincial_logic_report_{report.report_id}.json"
        
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
                    "province": r.province.value,
                    "status": r.status.value,
                    "severity": r.severity.value,
                    "message": r.message,
                    "details": r.details,
                    "recommendations": r.recommendations,
                    "timestamp": r.timestamp,
                    "execution_time_ms": r.execution_time_ms
                }
                for r in report.results
            ],
            "flow_results": [
                {
                    "from_province": fr.from_province.value,
                    "to_province": fr.to_province.value,
                    "flow_type": fr.flow_type,
                    "status": fr.status.value,
                    "message": fr.message,
                    "data_integrity": fr.data_integrity,
                    "timestamp": fr.timestamp,
                    "flow_duration_ms": fr.flow_duration_ms,
                    "data_items_transferred": fr.data_items_transferred,
                    "validation_errors": fr.validation_errors
                }
                for fr in report.flow_results
            ],
            "summary": report.summary,
            "performance_metrics": report.performance_metrics
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"报告已保存: {output_path}")
        return output_path

    def print_report(self, report: ProvincialLogicReport):
        """打印报告"""
        print("\n" + "=" * 70)
        print("三省协调逻辑检查报告")
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
        
        if report.performance_metrics:
            print(f"\n性能指标:")
            print(f"  执行时间: {report.performance_metrics.get('execution_time_ms', 0):.2f}ms")
            print(f"  检查速率: {report.performance_metrics.get('checks_per_second', 0):.2f} 项/秒")
        
        print("\n" + "-" * 70)
        print("各省份检查结果:")
        
        for province in Province:
            province_results = [r for r in report.results if r.province == province]
            if province_results:
                print(f"\n  {province.value.upper()}:")
                for result in province_results:
                    status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
                    print(f"    [{status_symbol}] {result.check_name}: {result.message}")
        
        print("\n" + "-" * 70)
        print("信息流转检查:")
        
        for flow in report.flow_results:
            status_symbol = "✓" if flow.status == CheckStatus.PASS else "✗" if flow.status == CheckStatus.FAIL else "⚠"
            print(f"  [{status_symbol}] {flow.from_province.value} → {flow.to_province.value}: {flow.message}")
        
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


def load_sample_data() -> dict[str, Any]:
    """加载示例数据"""
    return {
        "decision": {
            "requirement_analysis": {"completed": True},
            "architecture_design": {"completed": True},
            "sdd_specification": {"completed": True},
            "acceptance_tests": {"completed": True},
            "priority_ranking": {"completed": True}
        },
        "sdd": {
            "interfaces": [
                {"endpoint": "/api/users", "method": "POST", "request_schema": {}, "response_schema": {}},
                {"endpoint": "/api/users/{id}", "method": "GET", "request_schema": {}, "response_schema": {}}
            ],
            "data_models": [{"name": "User", "fields": []}],
            "behavior_rules": [{"name": "email_unique", "condition": "email not exists"}],
            "test_specifications": [{"scenario": "register_success"}]
        },
        "architecture": {
            "components": {
                "frontend": {"framework": "Vue3"},
                "backend": {"framework": "FastAPI"},
                "database": {"type": "PostgreSQL"}
            },
            "tech_stack": {
                "frontend": "Vue3",
                "backend": "Python FastAPI",
                "database": "PostgreSQL"
            },
            "dependencies": [],
            "scalability": {"strategy": "horizontal"},
            "security": {"strategy": "JWT"}
        },
        "tasks": [
            {"name": "用户注册", "priority": "high"},
            {"name": "用户登录", "priority": "high", "depends_on": [0]}
        ],
        "requirement": {
            "requirements": [
                {"id": "REQ-001", "description": "用户注册功能", "acceptance_criteria": [], "priority": "high"}
            ],
            "conflicts": [],
            "traceability_matrix": {"REQ-001": {"source": "business"}}
        },
        "tech": {
            "tech_stack": [
                {"name": "Vue3", "maturity": "stable", "team_expertise": 0.8},
                {"name": "FastAPI", "maturity": "stable", "team_expertise": 0.9}
            ],
            "risks": [],
            "dependencies": []
        },
        "risk": {
            "risks": [
                {"id": "RISK-001", "description": "性能风险", "probability": "medium", "impact": "high", "mitigation": "性能测试", "level": "medium"}
            ],
            "monitoring_plan": {"frequency": "weekly"}
        },
        "resource": {
            "required": {
                "human": {"developer": 3, "tester": 1},
                "time": {"estimated_days": 30},
                "technology": ["Vue3", "FastAPI"],
                "budget": 50000
            },
            "available": {
                "human": {"developer": 3, "tester": 2},
                "time": {"deadline_days": 45},
                "technology": ["Vue3", "FastAPI", "PostgreSQL"],
                "budget": 60000
            }
        },
        "review": {
            "requirement_review": {"status": "passed"},
            "architecture_review": {"status": "passed"},
            "test_coverage_review": {"status": "passed"},
            "compliance_review": {"status": "passed"}
        },
        "coverage": {
            "unit_test_coverage": 85,
            "integration_test_coverage": 70,
            "e2e_test_coverage": 100,
            "core_flows_covered": ["register", "login"],
            "total_core_flows": 2,
            "mutation_coverage": 75
        },
        "compliance": {
            "security_checks": {"passed": True},
            "coding_standards": {"compliant": True, "violations": []},
            "architecture_compliance": {"compliant": True},
            "dependency_check": {"vulnerabilities": []},
            "license_check": {"compliant": True}
        },
        "quality": {
            "gates": [
                {"name": "test_coverage", "threshold": 80, "actual": 85},
                {"name": "code_quality", "threshold": 90, "actual": 92}
            ]
        },
        "review_process": {
            "steps": [
                {"name": "initial_review", "completed": True},
                {"name": "technical_review", "completed": True},
                {"name": "security_review", "completed": True},
                {"name": "final_approval", "completed": True}
            ],
            "reviewers": {
                "technical_lead": "user1",
                "security_officer": "user2",
                "product_owner": "user3"
            },
            "documents": [
                {"name": "review_report"},
                {"name": "decision_record"},
                {"name": "sign_off"}
            ],
            "signatures": [{"signed": True}]
        },
        "review_history": {
            "records": [
                {"id": "REV-001", "timestamp": datetime.now().isoformat(), "reviewer": "user1", "decision": "approved"}
            ],
            "changes": [],
            "decision_basis": [{"id": "BASIS-001", "description": "技术可行性验证"}]
        },
        "review_decision": {
            "decisions": [
                {"id": "DEC-001", "review_result": "approved", "final_decision": "approved", "rationale": "符合要求", "topic": "架构设计"}
            ],
            "executable": True
        },
        "review_timeliness": {
            "reviews": [
                {"id": "REV-001", "start_time": datetime.now().isoformat(), "end_time": datetime.now().isoformat(), "deadline": (datetime.now() + timedelta(days=1)).isoformat()}
            ],
            "avg_response_time_hours": 24,
            "efficiency_score": 0.85
        },
        "plan": {
            "stages": [
                {"name": "准备阶段", "tasks": [], "responsible_department": "libu", "estimated_duration": 5},
                {"name": "TDD循环", "tasks": [], "responsible_department": "bingbu", "estimated_duration": 20}
            ],
            "stage_dependencies": [],
            "milestones": [{"name": "MVP完成", "status": "in_progress"}]
        },
        "tdd": {
            "cycles": [
                {
                    "id": "CYCLE-001",
                    "red": {"test_written": True, "test_failed": True},
                    "green": {"tests_passed": True},
                    "blue": {"tests_still_passed": True}
                }
            ],
            "compliance_rate": 0.9
        },
        "coordination": {
            "ministry_status": {
                "libu": {"status": "ready"},
                "hubu": {"status": "ready"},
                "liibu": {"status": "ready"},
                "bingbu": {"status": "executing"},
                "xingbu": {"status": "waiting"},
                "gongbu": {"status": "waiting"}
            },
            "tdd_sequence": [
                {"ministry": "bingbu", "phase": "red"},
                {"ministry": "gongbu", "phase": "green"},
                {"ministry": "xingbu", "phase": "blue"}
            ],
            "coordination_issues": []
        },
        "progress": {
            "total_tasks": 10,
            "completed_tasks": 4,
            "blocked_tasks": 0,
            "milestones": [
                {"name": "MVP完成", "status": "in_progress", "overdue": False, "days_remaining": 10}
            ],
            "velocity": 2,
            "expected_completion_rate": 50
        },
        "execution_state": {
            "tasks": [
                {"id": "TASK-001", "status": "completed", "actual_status": "completed"}
            ],
            "stages": [
                {"name": "准备阶段", "status": "completed", "tasks_status": [{"status": "completed"}]}
            ],
            "resources": [
                {"id": "RES-001", "allocated": 100, "used": 80}
            ],
            "last_sync_time": datetime.now().isoformat()
        },
        "execution_deps": {
            "tasks": [
                {"id": "TASK-001", "status": "completed", "depends_on": []},
                {"id": "TASK-002", "status": "in_progress", "depends_on": ["TASK-001"]}
            ],
            "execution_order": ["TASK-001", "TASK-002"]
        },
        "execution_resource": {
            "allocations": [
                {"resource_id": "developer", "allocated": 3, "required": 3}
            ],
            "resources": [
                {"id": "developer", "capacity": 5, "used": 3}
            ],
            "conflicts": [],
            "reservations": []
        },
        "exception": {
            "handlers": [
                {"id": "HANDLER-001", "type": "timeout", "action": "retry", "recovery_strategy": "exponential_backoff"}
            ],
            "exception_types": ["timeout", "connection_error"],
            "unhandled_exceptions": [],
            "recovery_mechanisms": ["retry", "fallback"],
            "logging_enabled": True
        },
        "zhongshusheng_output": {
            "sdd_specification": {"completed": True},
            "architecture_design": {"completed": True},
            "acceptance_tests": {"completed": True}
        },
        "menxiasheng_input": {
            "sdd_specification": {"received": True},
            "architecture_design": {"received": True},
            "acceptance_tests": {"received": True}
        },
        "menxiasheng_output": {
            "review_approval": {"status": "approved"},
            "quality_gate_result": {"passed": True}
        },
        "shangshusheng_input": {
            "review_approval": {"received": True},
            "quality_gate_result": {"received": True}
        },
        "feedback": {
            "rejection": False,
            "completion_status": "success"
        },
        "flow_timeliness": {
            "flows": [
                {"id": "FLOW-001", "expected_time_ms": 1000, "actual_time_ms": 800}
            ],
            "avg_flow_time_ms": 800,
            "threshold_ms": 3600000
        },
        "flow_integrity": {
            "transfers": [
                {"id": "TRANS-001", "checksum_sent": "abc123", "checksum_received": "abc123", "format_valid": True}
            ]
        },
        "flow_sync": {
            "sync_records": [
                {"id": "SYNC-001", "source_state": "active", "target_state": "active"}
            ],
            "last_sync_time": datetime.now().isoformat(),
            "conflicts": []
        },
        "flow_exception": {
            "handlers": [
                {"type": "transfer_error", "action": "retry"}
            ],
            "exception_types": ["transfer_error", "timeout"],
            "unhandled_exceptions": [],
            "notification_enabled": True
        }
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="三省协调逻辑检查器")
    
    parser.add_argument("--check-all", action="store_true", help="执行所有检查")
    parser.add_argument("--check-zhongshusheng", action="store_true", help="检查中书省决策逻辑")
    parser.add_argument("--check-menxiasheng", action="store_true", help="检查门下省审议逻辑")
    parser.add_argument("--check-shangshusheng", action="store_true", help="检查尚书省执行逻辑")
    parser.add_argument("--check-flow", action="store_true", help="检查三省信息流转")
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
    
    checker = ProvincialLogicChecker()
    
    if args.check_all or not any([args.check_zhongshusheng, args.check_menxiasheng, args.check_shangshusheng, args.check_flow]):
        report = checker.check_all(data)
        checker.print_report(report)
        
        if args.output:
            checker.save_report(report, args.output)
        else:
            checker.save_report(report)
    
    elif args.check_zhongshusheng:
        results = checker.check_province(Province.ZHONGSHUSHENG, data)
        print("\n中书省决策逻辑检查结果:")
        for result in results:
            status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
            print(f"  [{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.check_menxiasheng:
        results = checker.check_province(Province.MENXIASHENG, data)
        print("\n门下省审议逻辑检查结果:")
        for result in results:
            status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
            print(f"  [{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.check_shangshusheng:
        results = checker.check_province(Province.SHANGSHUSHENG, data)
        print("\n尚书省执行逻辑检查结果:")
        for result in results:
            status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
            print(f"  [{status_symbol}] {result.check_name}: {result.message}")
    
    elif args.check_flow:
        results = checker.check_flow(data)
        print("\n三省信息流转检查结果:")
        for result in results:
            status_symbol = "✓" if result.status == CheckStatus.PASS else "✗" if result.status == CheckStatus.FAIL else "⚠"
            print(f"  [{status_symbol}] {result.from_province.value} → {result.to_province.value}: {result.message}")


if __name__ == "__main__":
    main()
