#!/usr/bin/env python3
"""
三省协调逻辑检查器（增强版） - Sanliu 技能

功能增强：
- 三省协调逻辑完整性检查
- 中书省决策逻辑深度验证
- 门下省审议逻辑深度验证
- 尚书省执行逻辑深度验证
- 三省信息流转一致性检查
- 决策-审议-执行闭环验证
- 时序约束检查
- 数据完整性校验

使用方法：
    python scripts/analysis/provincial_logic_checker.py --check-all
    python scripts/analysis/provincial_logic_checker.py --check-coordination
    python scripts/analysis/provincial_logic_checker.py --check-flow-integrity
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
        logging.FileHandler('provincial_logic_checker_enhanced.log', encoding='utf-8')
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


@dataclass
class FlowCheckResult:
    from_province: Province
    to_province: Province
    flow_type: str
    status: CheckStatus
    message: str
    data_integrity: bool
    sequence_valid: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CoordinationIssue:
    issue_id: str
    province: Province
    issue_type: str
    description: str
    impact: str
    suggested_fix: str


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
    coordination_issues: list[CoordinationIssue]
    summary: dict[str, Any]
    overall_status: CheckStatus


class EnhancedZhongshushengChecker:
    """中书省决策逻辑深度检查器"""

    def __init__(self):
        self.ministry = Province.ZHONGSHUSHENG

    def check_decision_completeness(self, decision_data: dict[str, Any]) -> CheckResult:
        check_id = "ZSS-E001"
        check_name = "决策完整性深度检查"
        
        required_fields = {
            "requirement_analysis": {"weight": 1.0, "sub_fields": ["user_stories", "acceptance_criteria", "priority"]},
            "architecture_design": {"weight": 1.0, "sub_fields": ["components", "interfaces", "data_flow"]},
            "sdd_specification": {"weight": 0.9, "sub_fields": ["api_specs", "data_models", "behavior_rules"]},
            "acceptance_tests": {"weight": 0.8, "sub_fields": ["test_cases", "coverage_target"]},
            "priority_ranking": {"weight": 0.7, "sub_fields": ["tasks", "dependencies"]}
        }
        
        completeness_score = 0.0
        missing_fields = []
        incomplete_fields = []
        
        for field_name, field_config in required_fields.items():
            field_data = decision_data.get(field_name)
            if not field_data:
                missing_fields.append(field_name)
            else:
                sub_fields = field_config["sub_fields"]
                present_subs = [sf for sf in sub_fields if field_data.get(sf)]
                if len(present_subs) < len(sub_fields):
                    incomplete_fields.append({
                        "field": field_name,
                        "missing_subs": [sf for sf in sub_fields if sf not in present_subs]
                    })
                completeness_score += field_config["weight"] * (len(present_subs) / len(sub_fields))
        
        max_score = sum(fc["weight"] for fc in required_fields.values())
        completeness_ratio = completeness_score / max_score if max_score > 0 else 0
        
        if not missing_fields and not incomplete_fields:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message=f"决策数据完整，完整度: {completeness_ratio:.1%}",
                details={"completeness_ratio": completeness_ratio, "checked_fields": list(required_fields.keys())}
            )
        elif completeness_ratio >= 0.7:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"决策数据部分完整，完整度: {completeness_ratio:.1%}",
                details={
                    "completeness_ratio": completeness_ratio,
                    "missing_fields": missing_fields,
                    "incomplete_fields": incomplete_fields
                },
                recommendations=[f"补充字段: {f}" for f in missing_fields] + 
                              [f"完善 {item['field']} 的子字段: {item['missing_subs']}" for item in incomplete_fields]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message=f"决策数据不完整，完整度: {completeness_ratio:.1%}",
                details={
                    "completeness_ratio": completeness_ratio,
                    "missing_fields": missing_fields,
                    "incomplete_fields": incomplete_fields
                },
                recommendations=["补充缺失的决策数据", "完善不完整的字段"]
            )

    def check_sdd_specification_validity(self, sdd_data: dict[str, Any]) -> CheckResult:
        check_id = "ZSS-E002"
        check_name = "SDD规范有效性深度检查"
        
        issues = []
        warnings = []
        
        interfaces = sdd_data.get("interfaces", [])
        if not interfaces:
            issues.append("缺少接口规范定义")
        else:
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
        if not data_models:
            issues.append("缺少数据模型定义")
        else:
            for i, model in enumerate(data_models):
                if "name" not in model:
                    issues.append(f"数据模型{i+1}缺少名称")
                if "fields" not in model:
                    warnings.append(f"数据模型{i+1}缺少字段定义")
        
        behavior_rules = sdd_data.get("behavior_rules", [])
        if not behavior_rules:
            warnings.append("缺少行为规则定义")
        
        test_specs = sdd_data.get("test_specifications", [])
        if not test_specs:
            warnings.append("缺少测试规范定义")
        
        error_handling = sdd_data.get("error_handling", {})
        if not error_handling:
            warnings.append("缺少错误处理规范")
        
        security_specs = sdd_data.get("security_specifications", {})
        if not security_specs:
            warnings.append("缺少安全规范定义")
        
        if not issues and not warnings:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
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
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"SDD规范存在建议项: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["完善SDD规范定义"]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"SDD规范存在严重问题: {'; '.join(issues)}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["重新审视SDD规范", "补充缺失的规范定义"]
            )

    def check_architecture_feasibility(self, architecture_data: dict[str, Any]) -> CheckResult:
        check_id = "ZSS-E003"
        check_name = "架构可行性深度检查"
        
        issues = []
        warnings = []
        
        required_components = ["frontend", "backend", "database"]
        components = architecture_data.get("components", {})
        
        for component in required_components:
            if component not in components:
                issues.append(f"缺少核心组件: {component}")
            else:
                comp_data = components[component]
                if not comp_data.get("framework") and not comp_data.get("type"):
                    warnings.append(f"组件 {component} 未指定框架或类型")
        
        tech_stack = architecture_data.get("tech_stack", {})
        if not tech_stack:
            issues.append("未定义技术栈")
        else:
            for ts_type in ["frontend", "backend", "database"]:
                if ts_type not in tech_stack:
                    warnings.append(f"未指定{ts_type}技术栈")
        
        dependencies = architecture_data.get("dependencies", [])
        if dependencies:
            circular_deps = self._detect_circular_dependencies(dependencies)
            if circular_deps:
                issues.append(f"检测到循环依赖: {circular_deps}")
            
            version_conflicts = self._check_version_conflicts(dependencies)
            if version_conflicts:
                warnings.append(f"存在版本冲突风险: {version_conflicts}")
        
        scalability = architecture_data.get("scalability", {})
        if not scalability:
            warnings.append("未定义可扩展性方案")
        
        security = architecture_data.get("security", {})
        if not security:
            warnings.append("未定义安全架构")
        
        if not issues and not warnings:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="架构设计可行，无潜在问题",
                details={"components": list(components.keys()), "tech_stack": tech_stack}
            )
        elif not issues:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"架构设计存在建议项: {'; '.join(warnings[:5])}",
                details={"warnings": warnings},
                recommendations=["完善架构设计细节"]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"架构设计存在问题: {'; '.join(issues)}",
                details={"issues": issues, "warnings": warnings},
                recommendations=["重新审视架构设计", "解决循环依赖问题"]
            )

    def _detect_circular_dependencies(self, dependencies: list[dict]) -> list[str]:
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

    def _check_version_conflicts(self, dependencies: list[dict]) -> list[str]:
        conflicts = []
        dep_versions: dict[str, list[str]] = defaultdict(list)
        
        for dep in dependencies:
            name = dep.get("name", "")
            version = dep.get("version", "")
            if name and version:
                dep_versions[name].append(version)
        
        for name, versions in dep_versions.items():
            if len(set(versions)) > 1:
                conflicts.append(f"{name}: {versions}")
        
        return conflicts

    def check_priority_consistency(self, tasks: list[dict[str, Any]]) -> CheckResult:
        check_id = "ZSS-E004"
        check_name = "优先级一致性深度检查"
        
        issues = []
        warnings = []
        
        priority_values = ["critical", "high", "medium", "low", "p0", "p1", "p2", "p3"]
        priority_distribution: dict[str, int] = defaultdict(int)
        
        for i, task in enumerate(tasks):
            priority = task.get("priority", "").lower()
            if not priority:
                issues.append(f"任务{i+1}未设置优先级")
            elif priority not in priority_values:
                issues.append(f"任务{i+1}优先级值无效: {priority}")
            else:
                priority_distribution[priority] += 1
        
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
        
        critical_count = priority_distribution.get("critical", 0) + priority_distribution.get("p0", 0)
        if critical_count > len(tasks) * 0.3:
            warnings.append(f"高优先级任务占比过高: {critical_count}/{len(tasks)}")
        
        if not issues and not warnings:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="任务优先级设置合理一致",
                details={"tasks_count": len(tasks), "priority_distribution": dict(priority_distribution)}
            )
        elif not issues:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"优先级设置存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings, "priority_distribution": dict(priority_distribution)},
                recommendations=["调整任务优先级分布"]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.MEDIUM,
                message=f"优先级设置存在问题: {'; '.join(issues[:5])}",
                details={"issues": issues},
                recommendations=["调整任务优先级", "确保依赖任务优先级不低于被依赖任务"]
            )

    def _priority_higher(self, p1: str, p2: str) -> bool:
        priority_order = {"critical": 0, "p0": 0, "high": 1, "p1": 1, "medium": 2, "p2": 2, "low": 3, "p3": 3}
        return priority_order.get(p1.lower(), 2) < priority_order.get(p2.lower(), 2)

    def check_requirement_traceability(self, trace_data: dict[str, Any]) -> CheckResult:
        check_id = "ZSS-E005"
        check_name = "需求可追溯性检查"
        
        issues = []
        warnings = []
        
        requirements = trace_data.get("requirements", [])
        if not requirements:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="未定义需求数据",
                recommendations=["定义需求列表"]
            )
        
        traced_count = 0
        for req in requirements:
            req_id = req.get("id", "")
            if not req_id:
                warnings.append("存在未编号的需求")
                continue
            
            has_design = req.get("design_linked", False)
            has_test = req.get("test_linked", False)
            has_code = req.get("code_linked", False)
            
            if has_design and has_test:
                traced_count += 1
            else:
                missing = []
                if not has_design:
                    missing.append("设计")
                if not has_test:
                    missing.append("测试")
                warnings.append(f"需求 {req_id} 缺少关联: {', '.join(missing)}")
        
        trace_ratio = traced_count / len(requirements) if requirements else 0
        
        if trace_ratio >= 0.9:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message=f"需求可追溯性良好: {trace_ratio:.1%}",
                details={"trace_ratio": trace_ratio, "total_requirements": len(requirements)}
            )
        elif trace_ratio >= 0.7:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"需求可追溯性需提升: {trace_ratio:.1%}",
                details={"trace_ratio": trace_ratio, "warnings": warnings[:10]},
                recommendations=["完善需求追溯矩阵"]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"需求可追溯性不足: {trace_ratio:.1%}",
                details={"trace_ratio": trace_ratio, "warnings": warnings},
                recommendations=["建立需求追溯关系", "关联设计、测试和代码"]
            )

    def run_all_checks(self, data: dict[str, Any]) -> list[CheckResult]:
        results = []
        results.append(self.check_decision_completeness(data.get("decision", {})))
        results.append(self.check_sdd_specification_validity(data.get("sdd", {})))
        results.append(self.check_architecture_feasibility(data.get("architecture", {})))
        results.append(self.check_priority_consistency(data.get("tasks", [])))
        results.append(self.check_requirement_traceability(data.get("traceability", {})))
        return results


class EnhancedMenxiashengChecker:
    """门下省审议逻辑深度检查器"""

    def __init__(self):
        self.ministry = Province.MENXIASHENG

    def check_review_completeness(self, review_data: dict[str, Any]) -> CheckResult:
        check_id = "MXS-E001"
        check_name = "审议完整性深度检查"
        
        required_reviews = {
            "requirement_review": {"weight": 1.0, "required_approvals": 1},
            "architecture_review": {"weight": 1.0, "required_approvals": 2},
            "test_coverage_review": {"weight": 0.9, "required_approvals": 1},
            "compliance_review": {"weight": 0.9, "required_approvals": 1},
            "security_review": {"weight": 1.0, "required_approvals": 1},
            "performance_review": {"weight": 0.8, "required_approvals": 1}
        }
        
        missing_reviews = []
        incomplete_reviews = []
        failed_reviews = []
        
        for review_name, review_config in required_reviews.items():
            review = review_data.get(review_name)
            if not review:
                missing_reviews.append(review_name)
            else:
                status = review.get("status", "")
                if status != "passed":
                    if status == "failed":
                        failed_reviews.append({
                            "review": review_name,
                            "reason": review.get("reason", "未知原因")
                        })
                    else:
                        incomplete_reviews.append(review_name)
                
                approvals = review.get("approvals", 0)
                if approvals < review_config["required_approvals"]:
                    incomplete_reviews.append(f"{review_name}(审批不足)")
        
        if not missing_reviews and not incomplete_reviews and not failed_reviews:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="所有审议项目已完成并通过",
                details={"reviews": list(required_reviews.keys())}
            )
        elif not missing_reviews and not failed_reviews:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"存在未完成的审议: {incomplete_reviews}",
                details={"incomplete_reviews": incomplete_reviews},
                recommendations=["完成待审议项目"]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message=f"审议存在问题 - 缺失: {missing_reviews}, 失败: {[r['review'] for r in failed_reviews]}",
                details={"missing_reviews": missing_reviews, "failed_reviews": failed_reviews},
                recommendations=["完成缺失的审议项目", "重新审视失败的审议"]
            )

    def check_test_coverage_validity(self, coverage_data: dict[str, Any]) -> CheckResult:
        check_id = "MXS-E002"
        check_name = "测试覆盖率深度检查"
        
        issues = []
        warnings = []
        
        unit_coverage = coverage_data.get("unit_test_coverage", 0)
        integration_coverage = coverage_data.get("integration_test_coverage", 0)
        e2e_coverage = coverage_data.get("e2e_test_coverage", 0)
        mutation_coverage = coverage_data.get("mutation_coverage", 0)
        
        thresholds = {
            "unit": {"min": 80, "recommended": 90},
            "integration": {"min": 60, "recommended": 75},
            "e2e": {"min": 100, "recommended": 100},
            "mutation": {"min": 70, "recommended": 85}
        }
        
        if unit_coverage < thresholds["unit"]["min"]:
            issues.append(f"单元测试覆盖率不足: {unit_coverage}% (要求 >= {thresholds['unit']['min']}%)")
        elif unit_coverage < thresholds["unit"]["recommended"]:
            warnings.append(f"单元测试覆盖率建议提升: {unit_coverage}%")
        
        if integration_coverage < thresholds["integration"]["min"]:
            issues.append(f"集成测试覆盖率不足: {integration_coverage}% (要求 >= {thresholds['integration']['min']}%)")
        elif integration_coverage < thresholds["integration"]["recommended"]:
            warnings.append(f"集成测试覆盖率建议提升: {integration_coverage}%")
        
        core_flows = coverage_data.get("core_flows_covered", [])
        total_core_flows = coverage_data.get("total_core_flows", 0)
        if total_core_flows > 0 and len(core_flows) < total_core_flows:
            issues.append(f"核心流程E2E测试覆盖不完整: {len(core_flows)}/{total_core_flows}")
        
        if mutation_coverage > 0 and mutation_coverage < thresholds["mutation"]["min"]:
            warnings.append(f"变异测试覆盖率较低: {mutation_coverage}%")
        
        uncovered_critical = coverage_data.get("uncovered_critical_paths", [])
        if uncovered_critical:
            issues.append(f"关键路径未覆盖: {uncovered_critical}")
        
        if not issues and not warnings:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
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
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"测试覆盖率存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["继续提升测试覆盖率"]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"测试覆盖率不达标: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["补充测试用例", "提升测试覆盖率"]
            )

    def check_compliance_rules(self, compliance_data: dict[str, Any]) -> CheckResult:
        check_id = "MXS-E003"
        check_name = "合规性深度检查"
        
        issues = []
        warnings = []
        
        security_checks = compliance_data.get("security_checks", {})
        if not security_checks.get("passed", False):
            issues.append(f"安全检查未通过: {security_checks.get('reason', '未知原因')}")
        
        vulnerabilities = security_checks.get("vulnerabilities", [])
        critical_vulns = [v for v in vulnerabilities if v.get("severity") == "critical"]
        if critical_vulns:
            issues.append(f"存在严重安全漏洞: {len(critical_vulns)} 个")
        
        coding_standards = compliance_data.get("coding_standards", {})
        if not coding_standards.get("compliant", False):
            violations = coding_standards.get("violations", [])
            critical_violations = [v for v in violations if v.get("severity") == "critical"]
            if critical_violations:
                issues.append(f"存在严重编码规范违规: {len(critical_violations)} 处")
            else:
                warnings.append(f"编码规范违规: {len(violations)} 项")
        
        architecture_compliance = compliance_data.get("architecture_compliance", {})
        if not architecture_compliance.get("compliant", False):
            issues.append("架构合规性检查未通过")
        
        dependency_check = compliance_data.get("dependency_check", {})
        dep_vulnerabilities = dependency_check.get("vulnerabilities", [])
        if dep_vulnerabilities:
            critical_deps = [v for v in dep_vulnerabilities if v.get("severity") == "critical"]
            if critical_deps:
                issues.append(f"依赖存在严重安全漏洞: {len(critical_deps)} 个")
            else:
                warnings.append(f"依赖安全漏洞: {len(dep_vulnerabilities)} 个")
        
        license_check = compliance_data.get("license_check", {})
        if not license_check.get("compliant", True):
            issues.append(f"许可证合规问题: {license_check.get('issues', [])}")
        
        if not issues and not warnings:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="所有合规性检查通过",
                details={"checks_passed": True}
            )
        elif not issues:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"合规性检查存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["解决合规警告"]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message=f"合规性检查未通过: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["修复安全问题", "解决编码规范违规", "更新有漏洞的依赖"]
            )

    def check_quality_gate(self, quality_data: dict[str, Any]) -> CheckResult:
        check_id = "MXS-E004"
        check_name = "质量门禁深度检查"
        
        gates = quality_data.get("gates", [])
        if not gates:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="未定义质量门禁",
                recommendations=["定义质量门禁标准"]
            )
        
        failed_gates = []
        marginal_gates = []
        
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
                marginal_gates.append({
                    "name": gate_name,
                    "threshold": threshold,
                    "actual": actual
                })
        
        if not failed_gates and not marginal_gates:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="所有质量门禁通过",
                details={"gates_count": len(gates)}
            )
        elif not failed_gates:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"质量门禁接近阈值: {[g['name'] for g in marginal_gates]}",
                details={"marginal_gates": marginal_gates},
                recommendations=[f"关注 {g['name']} 指标" for g in marginal_gates]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"质量门禁未通过: {len(failed_gates)} 项",
                details={"failed_gates": failed_gates},
                recommendations=[f"提升 {g['name']} 从 {g['actual']} 到 {g['threshold']}" for g in failed_gates]
            )

    def check_approval_chain(self, approval_data: dict[str, Any]) -> CheckResult:
        check_id = "MXS-E005"
        check_name = "审批链完整性检查"
        
        issues = []
        warnings = []
        
        approvals = approval_data.get("approvals", [])
        if not approvals:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="无审批记录",
                recommendations=["建立审批流程"]
            )
        
        required_approvers = approval_data.get("required_approvers", [])
        actual_approvers = [a.get("approver") for a in approvals if a.get("approved")]
        
        missing_approvers = [a for a in required_approvers if a not in actual_approvers]
        if missing_approvers:
            issues.append(f"缺少必要审批人: {missing_approvers}")
        
        pending_approvals = [a for a in approvals if a.get("status") == "pending"]
        if pending_approvals:
            warnings.append(f"存在待审批项: {len(pending_approvals)} 个")
        
        rejected_approvals = [a for a in approvals if a.get("status") == "rejected"]
        if rejected_approvals:
            issues.append(f"存在被拒绝的审批: {[a.get('approver') for a in rejected_approvals]}")
        
        if not issues and not warnings:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="审批链完整",
                details={"approvals_count": len(approvals)}
            )
        elif not issues:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"审批链存在待处理项: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["处理待审批项"]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"审批链存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["完成缺失的审批", "处理被拒绝的审批"]
            )

    def run_all_checks(self, data: dict[str, Any]) -> list[CheckResult]:
        results = []
        results.append(self.check_review_completeness(data.get("review", {})))
        results.append(self.check_test_coverage_validity(data.get("coverage", {})))
        results.append(self.check_compliance_rules(data.get("compliance", {})))
        results.append(self.check_quality_gate(data.get("quality", {})))
        results.append(self.check_approval_chain(data.get("approvals", {})))
        return results


class EnhancedShangshushengChecker:
    """尚书省执行逻辑深度检查器"""

    def __init__(self):
        self.ministry = Province.SHANGSHUSHENG

    def check_execution_plan_validity(self, plan_data: dict[str, Any]) -> CheckResult:
        check_id = "SSS-E001"
        check_name = "执行计划有效性深度检查"
        
        issues = []
        warnings = []
        
        stages = plan_data.get("stages", [])
        if not stages:
            issues.append("执行计划缺少阶段定义")
        else:
            for i, stage in enumerate(stages):
                if "name" not in stage:
                    issues.append(f"阶段{i+1}缺少名称")
                if "tasks" not in stage:
                    issues.append(f"阶段{i+1}缺少任务列表")
                if "responsible_department" not in stage:
                    issues.append(f"阶段{i+1}缺少负责部门")
                
                if not stage.get("estimated_duration"):
                    warnings.append(f"阶段{i+1}缺少预估时长")
                if not stage.get("deliverables"):
                    warnings.append(f"阶段{i+1}缺少交付物定义")
        
        dependencies = plan_data.get("stage_dependencies", [])
        if dependencies:
            circular = self._detect_circular_stage_dependencies(dependencies)
            if circular:
                issues.append(f"阶段依赖存在循环: {circular}")
        
        critical_path = plan_data.get("critical_path", [])
        if not critical_path:
            warnings.append("未定义关键路径")
        
        rollback_plan = plan_data.get("rollback_plan", {})
        if not rollback_plan:
            warnings.append("缺少回滚计划")
        
        if not issues and not warnings:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="执行计划有效",
                details={"stages_count": len(stages)}
            )
        elif not issues:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"执行计划存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["完善执行计划细节"]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"执行计划存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["完善执行计划", "解决阶段依赖问题"]
            )

    def _detect_circular_stage_dependencies(self, dependencies: list) -> list[str]:
        graph: dict[str, list[str]] = {}
        
        for dep in dependencies:
            if isinstance(dep, tuple):
                source, target = dep[0], dep[1]
            else:
                source = dep.get("source", "")
                target = dep.get("target", "")
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
        check_id = "SSS-E002"
        check_name = "TDD循环完整性深度检查"
        
        issues = []
        warnings = []
        
        cycles = tdd_data.get("cycles", [])
        if not cycles:
            warnings.append("未定义TDD循环")
        
        for i, cycle in enumerate(cycles):
            red_phase = cycle.get("red")
            green_phase = cycle.get("green")
            blue_phase = cycle.get("blue")
            
            if not red_phase:
                issues.append(f"循环{i+1}缺少红阶段(测试先行)")
            else:
                if not red_phase.get("test_written"):
                    issues.append(f"循环{i+1}红阶段未编写测试")
                if not red_phase.get("test_failed"):
                    warnings.append(f"循环{i+1}红阶段测试应失败但未失败")
            
            if not green_phase:
                issues.append(f"循环{i+1}缺少绿阶段(代码实现)")
            elif red_phase:
                if not green_phase.get("tests_passed"):
                    issues.append(f"循环{i+1}绿阶段测试未通过")
                if green_phase.get("over_implemented"):
                    warnings.append(f"循环{i+1}绿阶段可能过度实现")
            
            if not blue_phase:
                warnings.append(f"循环{i+1}缺少蓝阶段(重构优化)")
            elif green_phase:
                if not blue_phase.get("tests_still_passed"):
                    issues.append(f"循环{i+1}蓝阶段重构后测试失败")
                if not blue_phase.get("refactoring_done"):
                    warnings.append(f"循环{i+1}蓝阶段未执行重构")
        
        if not issues and not warnings:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="TDD循环完整且正确执行",
                details={"cycles_count": len(cycles)}
            )
        elif not issues:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"TDD循环存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["完善TDD循环"]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"TDD循环存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["修复TDD循环问题", "确保红绿蓝阶段正确执行"]
            )

    def check_six_ministries_coordination(self, coordination_data: dict[str, Any]) -> CheckResult:
        check_id = "SSS-E003"
        check_name = "六部协调深度检查"
        
        issues = []
        warnings = []
        
        ministries = ["libu", "hubu", "liibu", "bingbu", "xingbu", "gongbu"]
        ministry_status = coordination_data.get("ministry_status", {})
        
        for ministry in ministries:
            status = ministry_status.get(ministry, {})
            if not status:
                issues.append(f"{ministry}状态未定义")
            elif status.get("status") == "error":
                issues.append(f"{ministry}执行出错: {status.get('error', '未知错误')}")
            elif status.get("status") == "blocked":
                warnings.append(f"{ministry}被阻塞: {status.get('blocked_by', '未知原因')}")
        
        tdd_sequence = coordination_data.get("tdd_sequence", [])
        if tdd_sequence:
            expected_sequence = ["bingbu", "gongbu", "xingbu"]
            actual_sequence = [s.get("ministry") for s in tdd_sequence]
            
            for i, expected in enumerate(expected_sequence):
                if expected in actual_sequence:
                    actual_index = actual_sequence.index(expected)
                    if actual_index < i:
                        earlier = actual_sequence[:actual_index]
                        issues.append(f"TDD顺序错误: {expected} 在 {earlier} 之前执行")
        
        handoffs = coordination_data.get("handoffs", [])
        for handoff in handoffs:
            if not handoff.get("data_transferred"):
                warnings.append(f"部门交接 {handoff.get('from')} -> {handoff.get('to')} 数据未传递")
        
        if not issues and not warnings:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.HIGH,
                message="六部协调正常",
                details={"ministries_checked": ministries}
            )
        elif not issues:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"六部协调存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["检查部门间交接"]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"六部协调存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["检查各部门状态", "修正TDD执行顺序"]
            )

    def check_progress_tracking(self, progress_data: dict[str, Any]) -> CheckResult:
        check_id = "SSS-E004"
        check_name = "进度追踪深度检查"
        
        issues = []
        warnings = []
        
        total_tasks = progress_data.get("total_tasks", 0)
        completed_tasks = progress_data.get("completed_tasks", 0)
        blocked_tasks = progress_data.get("blocked_tasks", 0)
        failed_tasks = progress_data.get("failed_tasks", 0)
        
        if total_tasks == 0:
            issues.append("未定义任务总数")
        
        if blocked_tasks > 0:
            blocked_list = progress_data.get("blocked_task_list", [])
            issues.append(f"存在阻塞任务: {blocked_tasks} 个 - {blocked_list[:3]}")
        
        if failed_tasks > 0:
            issues.append(f"存在失败任务: {failed_tasks} 个")
        
        progress_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        milestones = progress_data.get("milestones", [])
        overdue_milestones = [
            m for m in milestones
            if m.get("status") != "completed" and m.get("overdue", False)
        ]
        if overdue_milestones:
            issues.append(f"存在逾期里程碑: {[m.get('name') for m in overdue_milestones]}")
        
        upcoming_milestones = [
            m for m in milestones
            if m.get("status") != "completed" and not m.get("overdue", False)
        ]
        for m in upcoming_milestones:
            if m.get("at_risk", False):
                warnings.append(f"里程碑 {m.get('name')} 存在延期风险")
        
        if not issues and not warnings:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message=f"进度追踪正常，完成率: {progress_rate:.1f}%",
                details={
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "progress_rate": progress_rate
                }
            )
        elif not issues:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"进度追踪存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings},
                recommendations=["关注进度预警"]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"进度追踪存在问题: {'; '.join(issues)}",
                details={"issues": issues},
                recommendations=["解决阻塞任务", "处理逾期里程碑"]
            )

    def check_resource_utilization(self, resource_data: dict[str, Any]) -> CheckResult:
        check_id = "SSS-E005"
        check_name = "资源利用检查"
        
        issues = []
        warnings = []
        
        agents = resource_data.get("agents", [])
        if not agents:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message="无Agent资源数据",
                recommendations=["收集Agent资源数据"]
            )
        
        overloaded = []
        underutilized = []
        
        for agent in agents:
            agent_id = agent.get("id", "unknown")
            utilization = agent.get("utilization", 0)
            
            if utilization > 0.9:
                overloaded.append({"id": agent_id, "utilization": utilization})
            elif utilization < 0.3:
                underutilized.append({"id": agent_id, "utilization": utilization})
        
        if overloaded:
            issues.append(f"存在过载Agent: {[a['id'] for a in overloaded]}")
        
        if underutilized:
            warnings.append(f"存在低利用Agent: {[a['id'] for a in underutilized]}")
        
        if not issues and not warnings:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MEDIUM,
                message="资源利用合理",
                details={"agents_count": len(agents)}
            )
        elif not issues:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"资源利用存在建议: {'; '.join(warnings)}",
                details={"warnings": warnings, "underutilized": underutilized},
                recommendations=["优化资源分配"]
            )
        else:
            return CheckResult(
                check_id=check_id,
                check_name=check_name,
                province=self.ministry,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"资源利用存在问题: {'; '.join(issues)}",
                details={"issues": issues, "overloaded": overloaded},
                recommendations=["平衡Agent负载", "增加资源或减少任务"]
            )

    def run_all_checks(self, data: dict[str, Any]) -> list[CheckResult]:
        results = []
        results.append(self.check_execution_plan_validity(data.get("plan", {})))
        results.append(self.check_tdd_cycle_integrity(data.get("tdd", {})))
        results.append(self.check_six_ministries_coordination(data.get("coordination", {})))
        results.append(self.check_progress_tracking(data.get("progress", {})))
        results.append(self.check_resource_utilization(data.get("resources", {})))
        return results


class ProvincialFlowIntegrityChecker:
    """三省信息流转完整性检查器"""

    def __init__(self):
        self.flow_results: list[FlowCheckResult] = []

    def check_zhongshusheng_to_menxiasheng(self, data: dict[str, Any]) -> FlowCheckResult:
        decision_output = data.get("zhongshusheng_output", {})
        menxiasheng_input = data.get("menxiasheng_input", {})
        
        required_outputs = ["sdd_specification", "architecture_design", "acceptance_tests"]
        data_integrity = True
        sequence_valid = True
        issues = []
        
        for output in required_outputs:
            if output not in decision_output:
                issues.append(f"中书省输出缺少: {output}")
                data_integrity = False
            elif output not in menxiasheng_input:
                issues.append(f"门下省未接收到: {output}")
                data_integrity = False
        
        decision_time = data.get("zhongshusheng_output", {}).get("timestamp")
        review_time = data.get("menxiasheng_input", {}).get("timestamp")
        if decision_time and review_time:
            if review_time < decision_time:
                sequence_valid = False
                issues.append("时序错误: 门下省接收时间早于中书省输出时间")
        
        if data_integrity and sequence_valid:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="decision_to_review",
                status=CheckStatus.PASS,
                message="中书省到门下省信息流转正常",
                data_integrity=True,
                sequence_valid=True
            )
        else:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.MENXIASHENG,
                flow_type="decision_to_review",
                status=CheckStatus.FAIL,
                message=f"信息流转存在问题: {'; '.join(issues)}",
                data_integrity=data_integrity,
                sequence_valid=sequence_valid
            )

    def check_menxiasheng_to_shangshusheng(self, data: dict[str, Any]) -> FlowCheckResult:
        menxiasheng_output = data.get("menxiasheng_output", {})
        shangshusheng_input = data.get("shangshusheng_input", {})
        
        required_outputs = ["review_approval", "quality_gate_result"]
        data_integrity = True
        sequence_valid = True
        issues = []
        
        for output in required_outputs:
            if output not in menxiasheng_output:
                issues.append(f"门下省输出缺少: {output}")
                data_integrity = False
            elif output not in shangshusheng_input:
                issues.append(f"尚书省未接收到: {output}")
                data_integrity = False
        
        approval_status = menxiasheng_output.get("review_approval", {}).get("status")
        if approval_status != "approved":
            issues.append(f"审议未通过，状态: {approval_status}")
            return FlowCheckResult(
                from_province=Province.MENXIASHENG,
                to_province=Province.SHANGSHUSHENG,
                flow_type="review_to_execution",
                status=CheckStatus.FAIL,
                message=f"审议未通过，无法流转到执行阶段",
                data_integrity=False,
                sequence_valid=False
            )
        
        if data_integrity and sequence_valid:
            return FlowCheckResult(
                from_province=Province.MENXIASHENG,
                to_province=Province.SHANGSHUSHENG,
                flow_type="review_to_execution",
                status=CheckStatus.PASS,
                message="门下省到尚书省信息流转正常",
                data_integrity=True,
                sequence_valid=True
            )
        else:
            return FlowCheckResult(
                from_province=Province.MENXIASHENG,
                to_province=Province.SHANGSHUSHENG,
                flow_type="review_to_execution",
                status=CheckStatus.FAIL,
                message=f"信息流转存在问题: {'; '.join(issues)}",
                data_integrity=data_integrity,
                sequence_valid=sequence_valid
            )

    def check_feedback_flow(self, data: dict[str, Any]) -> FlowCheckResult:
        feedback = data.get("feedback", {})
        
        has_rejection = feedback.get("rejection", False)
        rejection_from = feedback.get("rejected_by", "")
        rejection_to = feedback.get("return_to", "")
        
        if has_rejection:
            return FlowCheckResult(
                from_province=Province(rejection_from) if rejection_from else Province.MENXIASHENG,
                to_province=Province(rejection_to) if rejection_to else Province.ZHONGSHUSHENG,
                flow_type="feedback_rejection",
                status=CheckStatus.WARNING,
                message=f"存在驳回反馈，需要返回修正: {feedback.get('reason', '无原因')}",
                data_integrity=True,
                sequence_valid=True
            )
        
        return FlowCheckResult(
            from_province=Province.SHANGSHUSHENG,
            to_province=Province.ZHONGSHUSHENG,
            flow_type="completion_feedback",
            status=CheckStatus.PASS,
            message="执行完成，反馈正常",
            data_integrity=True,
            sequence_valid=True
        )

    def check_closed_loop_integrity(self, data: dict[str, Any]) -> FlowCheckResult:
        decision_id = data.get("zhongshusheng_output", {}).get("decision_id")
        review_id = data.get("menxiasheng_output", {}).get("review_id")
        execution_id = data.get("shangshusheng_output", {}).get("execution_id")
        
        issues = []
        
        if not decision_id:
            issues.append("缺少决策ID")
        if not review_id:
            issues.append("缺少审议ID")
        if not execution_id:
            issues.append("缺少执行ID")
        
        trace_chain = data.get("trace_chain", [])
        if trace_chain:
            expected_chain = [decision_id, review_id, execution_id]
            actual_chain = [t.get("id") for t in trace_chain]
            
            if actual_chain != expected_chain:
                issues.append(f"追溯链不完整: {actual_chain}")
        else:
            issues.append("缺少追溯链")
        
        if not issues:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.SHANGSHUSHENG,
                flow_type="closed_loop",
                status=CheckStatus.PASS,
                message="决策-审议-执行闭环完整",
                data_integrity=True,
                sequence_valid=True
            )
        else:
            return FlowCheckResult(
                from_province=Province.ZHONGSHUSHENG,
                to_province=Province.SHANGSHUSHENG,
                flow_type="closed_loop",
                status=CheckStatus.WARNING,
                message=f"闭环存在缺失: {'; '.join(issues)}",
                data_integrity=False,
                sequence_valid=True
            )

    def run_all_flow_checks(self, data: dict[str, Any]) -> list[FlowCheckResult]:
        results = []
        results.append(self.check_zhongshusheng_to_menxiasheng(data))
        results.append(self.check_menxiasheng_to_shangshusheng(data))
        results.append(self.check_feedback_flow(data))
        results.append(self.check_closed_loop_integrity(data))
        return results


class ProvincialCoordinationChecker:
    """三省协调逻辑检查器"""

    def __init__(self):
        self.coordination_issues: list[CoordinationIssue] = []

    def check_cross_province_dependencies(self, data: dict[str, Any]) -> list[CoordinationIssue]:
        issues = []
        
        zhongshusheng_status = data.get("zhongshusheng_status", {})
        menxiasheng_status = data.get("menxiasheng_status", {})
        shangshusheng_status = data.get("shangshusheng_status", {})
        
        if zhongshusheng_status.get("status") == "pending":
            if menxiasheng_status.get("status") == "active":
                issues.append(CoordinationIssue(
                    issue_id=f"COORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-001",
                    province=Province.MENXIASHENG,
                    issue_type="dependency_violation",
                    description="门下省在中书省决策未完成时开始活动",
                    impact="可能导致审议无效",
                    suggested_fix="等待中书省决策完成"
                ))
        
        if menxiasheng_status.get("approval_status") != "approved":
            if shangshusheng_status.get("status") == "executing":
                issues.append(CoordinationIssue(
                    issue_id=f"COORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-002",
                    province=Province.SHANGSHUSHENG,
                    issue_type="dependency_violation",
                    description="尚书省在门下省审议未通过时开始执行",
                    impact="可能导致无效执行",
                    suggested_fix="等待门下省审议通过"
                ))
        
        return issues

    def check_data_consistency(self, data: dict[str, Any]) -> list[CoordinationIssue]:
        issues = []
        
        decision_data = data.get("zhongshusheng_output", {}).get("data", {})
        review_data = data.get("menxiasheng_input", {}).get("data", {})
        
        if decision_data and review_data:
            decision_checksum = decision_data.get("checksum")
            review_checksum = review_data.get("checksum")
            
            if decision_checksum and review_checksum and decision_checksum != review_checksum:
                issues.append(CoordinationIssue(
                    issue_id=f"COORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-003",
                    province=Province.MENXIASHENG,
                    issue_type="data_inconsistency",
                    description="门下省接收的数据与中书省输出的数据不一致",
                    impact="可能导致审议基于错误数据",
                    suggested_fix="重新传输数据"
                ))
        
        return issues


class ProvincialLogicChecker:
    """三省协调逻辑检查器主类"""

    def __init__(self, output_dir: Path = None):
        if output_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                self.output_dir = _path_mgr.get_output_path(OutputType.REPORT, subdirectory="provincial_checks")
            except Exception:
                self.output_dir = get_path_config().REPORTS_DIR / "provincial_checks"
        else:
            self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.zhongshusheng_checker = EnhancedZhongshushengChecker()
        self.menxiasheng_checker = EnhancedMenxiashengChecker()
        self.shangshusheng_checker = EnhancedShangshushengChecker()
        self.flow_checker = ProvincialFlowIntegrityChecker()
        self.coordination_checker = ProvincialCoordinationChecker()

    def check_all(self, data: dict[str, Any]) -> ProvincialLogicReport:
        all_results: list[CheckResult] = []
        
        all_results.extend(self.zhongshusheng_checker.run_all_checks(data))
        all_results.extend(self.menxiasheng_checker.run_all_checks(data))
        all_results.extend(self.shangshusheng_checker.run_all_checks(data))
        
        flow_results = self.flow_checker.run_all_flow_checks(data)
        
        coordination_issues = []
        coordination_issues.extend(self.coordination_checker.check_cross_province_dependencies(data))
        coordination_issues.extend(self.coordination_checker.check_data_consistency(data))
        
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
        
        summary = self._generate_summary(all_results, flow_results, coordination_issues)
        
        report = ProvincialLogicReport(
            report_id=f"PLC-E-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            total_checks=len(all_results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            skipped=skipped,
            results=all_results,
            flow_results=flow_results,
            coordination_issues=coordination_issues,
            summary=summary,
            overall_status=overall_status
        )
        
        return report

    def check_province(self, province: Province, data: dict[str, Any]) -> list[CheckResult]:
        if province == Province.ZHONGSHUSHENG:
            return self.zhongshusheng_checker.run_all_checks(data)
        elif province == Province.MENXIASHENG:
            return self.menxiasheng_checker.run_all_checks(data)
        elif province == Province.SHANGSHUSHENG:
            return self.shangshusheng_checker.run_all_checks(data)
        else:
            return []

    def check_flow(self, data: dict[str, Any]) -> list[FlowCheckResult]:
        return self.flow_checker.run_all_flow_checks(data)

    def _generate_summary(self, results: list[CheckResult], flow_results: list[FlowCheckResult], 
                         coordination_issues: list[CoordinationIssue]) -> dict[str, Any]:
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
            {"check_id": r.check_id, "province": r.province.value, "message": r.message}
            for r in results
            if r.status == CheckStatus.FAIL and r.severity == CheckSeverity.CRITICAL
        ]
        
        flow_integrity = all(fr.data_integrity for fr in flow_results)
        sequence_valid = all(fr.sequence_valid for fr in flow_results)
        
        return {
            "by_province": by_province,
            "critical_issues": critical_issues,
            "flow_integrity": flow_integrity,
            "sequence_valid": sequence_valid,
            "coordination_issues_count": len(coordination_issues),
            "recommendations": self._generate_recommendations(results)
        }

    def _generate_recommendations(self, results: list[CheckResult]) -> list[str]:
        all_recommendations = []
        for result in results:
            all_recommendations.extend(result.recommendations)
        
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        return unique_recommendations[:10]

    def save_report(self, report: ProvincialLogicReport, output_path: Path = None) -> Path:
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
                    "timestamp": r.timestamp
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
                    "sequence_valid": fr.sequence_valid,
                    "timestamp": fr.timestamp
                }
                for fr in report.flow_results
            ],
            "coordination_issues": [
                {
                    "issue_id": ci.issue_id,
                    "province": ci.province.value,
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

    def print_report(self, report: ProvincialLogicReport):
        print("\n" + "=" * 70)
        print("三省协调逻辑检查报告（增强版）")
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
            integrity = "✓" if flow.data_integrity else "✗"
            sequence = "✓" if flow.sequence_valid else "✗"
            print(f"  [{status_symbol}] {flow.from_province.value} → {flow.to_province.value}: {flow.message}")
            print(f"      数据完整性: [{integrity}] 时序正确: [{sequence}]")
        
        if report.coordination_issues:
            print("\n" + "-" * 70)
            print("协调问题:")
            for issue in report.coordination_issues:
                print(f"  - [{issue.issue_id}] {issue.province.value}: {issue.description}")
                print(f"    影响: {issue.impact}")
                print(f"    建议: {issue.suggested_fix}")
        
        if report.summary.get("critical_issues"):
            print("\n" + "-" * 70)
            print("严重问题:")
            for issue in report.summary["critical_issues"]:
                print(f"  - [{issue['check_id']}] ({issue['province']}) {issue['message']}")
        
        if report.summary.get("recommendations"):
            print("\n" + "-" * 70)
            print("改进建议:")
            for rec in report.summary["recommendations"][:5]:
                print(f"  - {rec}")
        
        print("\n" + "=" * 70)


def load_sample_data() -> dict[str, Any]:
    return {
        "decision": {
            "requirement_analysis": {
                "user_stories": [{"id": "US-001", "title": "用户注册"}],
                "acceptance_criteria": [{"id": "AC-001", "criteria": "成功注册"}],
                "priority": "high"
            },
            "architecture_design": {
                "components": {"frontend": {}, "backend": {}, "database": {}},
                "interfaces": [{"name": "UserAPI"}],
                "data_flow": [{"from": "frontend", "to": "backend"}]
            },
            "sdd_specification": {
                "api_specs": [{"endpoint": "/api/users"}],
                "data_models": [{"name": "User"}],
                "behavior_rules": [{"rule": "email_unique"}]
            },
            "acceptance_tests": {
                "test_cases": [{"id": "TC-001"}],
                "coverage_target": 90
            },
            "priority_ranking": {
                "tasks": [{"id": "T-001", "priority": "high"}],
                "dependencies": []
            }
        },
        "sdd": {
            "interfaces": [
                {"endpoint": "/api/users", "method": "POST", "request_schema": {}, "response_schema": {}}
            ],
            "data_models": [{"name": "User", "fields": ["id", "email", "password"]}],
            "behavior_rules": [{"rule": "email_unique"}],
            "test_specifications": [{"scenario": "register_success"}],
            "error_handling": {"strategy": "exception"},
            "security_specifications": {"auth": "jwt"}
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
            "security": {"auth": "jwt", "encryption": "aes256"}
        },
        "tasks": [
            {"name": "用户注册", "priority": "high"},
            {"name": "用户登录", "priority": "high", "depends_on": [0]}
        ],
        "traceability": {
            "requirements": [
                {"id": "REQ-001", "design_linked": True, "test_linked": True, "code_linked": True}
            ]
        },
        "review": {
            "requirement_review": {"status": "passed", "approvals": 2},
            "architecture_review": {"status": "passed", "approvals": 2},
            "test_coverage_review": {"status": "passed", "approvals": 1},
            "compliance_review": {"status": "passed", "approvals": 1},
            "security_review": {"status": "passed", "approvals": 1},
            "performance_review": {"status": "passed", "approvals": 1}
        },
        "coverage": {
            "unit_test_coverage": 85,
            "integration_test_coverage": 70,
            "e2e_test_coverage": 100,
            "mutation_coverage": 80,
            "core_flows_covered": ["register", "login"],
            "total_core_flows": 2,
            "uncovered_critical_paths": []
        },
        "compliance": {
            "security_checks": {"passed": True, "vulnerabilities": []},
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
        "approvals": {
            "approvals": [
                {"approver": "tech_lead", "approved": True, "status": "approved"},
                {"approver": "architect", "approved": True, "status": "approved"}
            ],
            "required_approvers": ["tech_lead", "architect"]
        },
        "plan": {
            "stages": [
                {"name": "准备阶段", "tasks": [], "responsible_department": "libu", "estimated_duration": "2d", "deliverables": ["环境配置"]},
                {"name": "TDD循环", "tasks": [], "responsible_department": "bingbu", "estimated_duration": "5d", "deliverables": ["测试用例", "代码实现"]}
            ],
            "stage_dependencies": [],
            "critical_path": ["准备阶段", "TDD循环"],
            "rollback_plan": {"strategy": "version_rollback"}
        },
        "tdd": {
            "cycles": [
                {
                    "red": {"test_written": True, "test_failed": True},
                    "green": {"tests_passed": True, "over_implemented": False},
                    "blue": {"tests_still_passed": True, "refactoring_done": True}
                }
            ]
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
            "handoffs": [
                {"from": "bingbu", "to": "gongbu", "data_transferred": True}
            ]
        },
        "progress": {
            "total_tasks": 10,
            "completed_tasks": 4,
            "blocked_tasks": 0,
            "failed_tasks": 0,
            "milestones": [
                {"name": "MVP完成", "status": "in_progress", "overdue": False, "at_risk": False}
            ]
        },
        "resources": {
            "agents": [
                {"id": "agent-1", "utilization": 0.6},
                {"id": "agent-2", "utilization": 0.5}
            ]
        },
        "zhongshusheng_output": {
            "decision_id": "DEC-001",
            "sdd_specification": {"completed": True},
            "architecture_design": {"completed": True},
            "acceptance_tests": {"completed": True},
            "timestamp": "2026-03-30T10:00:00",
            "data": {"checksum": "abc123"}
        },
        "menxiasheng_input": {
            "sdd_specification": {"received": True},
            "architecture_design": {"received": True},
            "acceptance_tests": {"received": True},
            "timestamp": "2026-03-30T11:00:00",
            "data": {"checksum": "abc123"}
        },
        "menxiasheng_output": {
            "review_id": "REV-001",
            "review_approval": {"status": "approved"},
            "quality_gate_result": {"passed": True}
        },
        "shangshusheng_input": {
            "review_approval": {"received": True},
            "quality_gate_result": {"received": True}
        },
        "shangshusheng_output": {
            "execution_id": "EXEC-001"
        },
        "trace_chain": [
            {"id": "DEC-001"},
            {"id": "REV-001"},
            {"id": "EXEC-001"}
        ],
        "feedback": {
            "rejection": False
        },
        "zhongshusheng_status": {"status": "completed"},
        "menxiasheng_status": {"status": "completed", "approval_status": "approved"},
        "shangshusheng_status": {"status": "executing"}
    }


def main():
    parser = argparse.ArgumentParser(description="三省协调逻辑检查器（增强版）")
    
    parser.add_argument("--check-all", action="store_true", help="执行所有检查")
    parser.add_argument("--check-zhongshusheng", action="store_true", help="检查中书省决策逻辑")
    parser.add_argument("--check-menxiasheng", action="store_true", help="检查门下省审议逻辑")
    parser.add_argument("--check-shangshusheng", action="store_true", help="检查尚书省执行逻辑")
    parser.add_argument("--check-flow", action="store_true", help="检查三省信息流转")
    parser.add_argument("--check-coordination", action="store_true", help="检查三省协调")
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
    
    if args.check_all or not any([args.check_zhongshusheng, args.check_menxiasheng, args.check_shangshusheng, args.check_flow, args.check_coordination]):
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
