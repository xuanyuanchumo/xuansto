#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整闭环验证系统 - Complete Closed-Loop Verification System
实现从需求到交付的持续质量监控、自动修复、自动学习、自动优化、自动迭代与自动完善的完整闭环

功能:
1. 需求验证闭环
2. 设计验证闭环
3. 开发验证闭环
4. 测试验证闭环
5. 部署验证闭环
6. 运维验证闭环
7. 反馈学习闭环
8. 需求到交付追溯
9. 质量门禁验证
10. 交付物完整性检查
"""

import os
import sys
import json
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, Counter
import traceback
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LoopStage(Enum):
    REQUIREMENT = "requirement"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    OPERATION = "operation"
    FEEDBACK = "feedback"


class LoopStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_FIX = "needs_fix"
    AUTO_FIXED = "auto_fixed"
    MANUAL_REQUIRED = "manual_required"


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class LoopCheckpoint:
    checkpoint_id: str
    stage: LoopStage
    name: str
    description: str
    status: LoopStatus
    timestamp: str
    checks: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    fixes_applied: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class LoopIteration:
    iteration_id: str
    started_at: str
    completed_at: str = ""
    status: LoopStatus = LoopStatus.PENDING
    checkpoints: List[LoopCheckpoint] = field(default_factory=list)
    total_issues: int = 0
    auto_fixed_issues: int = 0
    manual_issues: int = 0
    learnings: List[str] = field(default_factory=list)


@dataclass
class ClosedLoopReport:
    report_id: str
    generated_at: str
    iteration: LoopIteration
    summary: Dict[str, Any]
    recommendations: List[str]
    next_actions: List[str]
    quality_score: float = 0.0


@dataclass
class RequirementTrace:
    requirement_id: str
    requirement_title: str
    source: str
    created_at: str
    linked_designs: List[str] = field(default_factory=list)
    linked_code_files: List[str] = field(default_factory=list)
    linked_tests: List[str] = field(default_factory=list)
    linked_deployments: List[str] = field(default_factory=list)
    status: str = "pending"
    trace_score: float = 0.0


@dataclass
class QualityGate:
    gate_id: str
    name: str
    stage: LoopStage
    criteria: List[Dict[str, Any]]
    threshold: float
    status: LoopStatus = LoopStatus.PENDING
    actual_value: float = 0.0
    passed: bool = False
    timestamp: str = ""


@dataclass
class Deliverable:
    deliverable_id: str
    name: str
    type: str
    path: str
    required: bool
    exists: bool = False
    checksum: str = ""
    size: int = 0
    last_modified: str = ""
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class TraceabilityMatrix:
    matrix_id: str
    created_at: str
    requirements: List[RequirementTrace] = field(default_factory=list)
    total_requirements: int = 0
    traced_requirements: int = 0
    coverage_score: float = 0.0
    gaps: List[Dict[str, Any]] = field(default_factory=list)


class RequirementValidator:
    
    def __init__(self):
        self.required_fields = ["title", "description", "acceptance_criteria"]
    
    def validate(self, requirement: Dict[str, Any]) -> Tuple[bool, List[Dict]]:
        issues = []
        
        for field in self.required_fields:
            if field not in requirement or not requirement[field]:
                issues.append({
                    "type": "missing_field",
                    "severity": Severity.HIGH.value,
                    "field": field,
                    "message": f"缺少必需字段: {field}"
                })
        
        if "acceptance_criteria" in requirement:
            criteria = requirement["acceptance_criteria"]
            if isinstance(criteria, list) and len(criteria) < 1:
                issues.append({
                    "type": "insufficient_criteria",
                    "severity": Severity.MEDIUM.value,
                    "message": "验收标准数量不足"
                })
        
        return len(issues) == 0, issues


class DesignValidator:
    
    def __init__(self):
        self.required_sections = ["架构设计", "数据模型", "接口设计", "安全设计"]
    
    def validate(self, design_doc: Dict[str, Any]) -> Tuple[bool, List[Dict]]:
        issues = []
        
        for section in self.required_sections:
            if section not in design_doc:
                issues.append({
                    "type": "missing_section",
                    "severity": Severity.HIGH.value,
                    "section": section,
                    "message": f"设计文档缺少章节: {section}"
                })
        
        return len(issues) == 0, issues


class DevelopmentValidator:
    
    def validate(self, code_path: str) -> Tuple[bool, List[Dict]]:
        issues = []
        
        path = Path(code_path)
        if not path.exists():
            issues.append({
                "type": "path_not_found",
                "severity": Severity.CRITICAL.value,
                "message": f"代码路径不存在: {code_path}"
            })
            return False, issues
        
        py_files = list(path.rglob("*.py"))
        if not py_files:
            issues.append({
                "type": "no_code_files",
                "severity": Severity.HIGH.value,
                "message": "未找到Python代码文件"
            })
        
        return len(issues) == 0, issues


class TestingValidator:
    
    def validate(self, test_results: Dict[str, Any]) -> Tuple[bool, List[Dict]]:
        issues = []
        
        total = test_results.get("total", 0)
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)
        
        if total == 0:
            issues.append({
                "type": "no_tests",
                "severity": Severity.HIGH.value,
                "message": "没有执行任何测试"
            })
            return False, issues
        
        pass_rate = passed / total if total > 0 else 0
        
        if pass_rate < 0.8:
            issues.append({
                "type": "low_pass_rate",
                "severity": Severity.HIGH.value,
                "message": f"测试通过率过低: {pass_rate:.1%}"
            })
        
        if failed > 0:
            issues.append({
                "type": "failed_tests",
                "severity": Severity.MEDIUM.value,
                "message": f"存在 {failed} 个失败的测试"
            })
        
        return failed == 0, issues


class DeploymentValidator:
    
    def validate(self, deploy_config: Dict[str, Any]) -> Tuple[bool, List[Dict]]:
        issues = []
        
        required_keys = ["environment", "version", "services"]
        for key in required_keys:
            if key not in deploy_config:
                issues.append({
                    "type": "missing_config",
                    "severity": Severity.HIGH.value,
                    "key": key,
                    "message": f"部署配置缺少: {key}"
                })
        
        return len(issues) == 0, issues


class OperationValidator:
    
    def validate(self, metrics: Dict[str, Any]) -> Tuple[bool, List[Dict]]:
        issues = []
        
        error_rate = metrics.get("error_rate", 0)
        response_time = metrics.get("avg_response_time", 0)
        
        if error_rate > 0.01:
            issues.append({
                "type": "high_error_rate",
                "severity": Severity.HIGH.value,
                "message": f"错误率过高: {error_rate:.2%}"
            })
        
        if response_time > 1000:
            issues.append({
                "type": "slow_response",
                "severity": Severity.MEDIUM.value,
                "message": f"响应时间过慢: {response_time}ms"
            })
        
        return len(issues) == 0, issues


class FeedbackLearner:
    
    def __init__(self):
        self.learnings: List[Dict[str, Any]] = []
        self.patterns: Dict[str, int] = defaultdict(int)
    
    def learn(self, issue: Dict[str, Any], fix: str = None):
        issue_type = issue.get("type", "unknown")
        self.patterns[issue_type] += 1
        
        learning = {
            "issue_type": issue_type,
            "severity": issue.get("severity"),
            "fix": fix,
            "timestamp": datetime.now().isoformat()
        }
        self.learnings.append(learning)
    
    def get_recommendations(self) -> List[str]:
        recommendations = []
        
        common_issues = sorted(self.patterns.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for issue_type, count in common_issues:
            if count >= 3:
                recommendations.append(f"频繁出现问题 '{issue_type}' ({count}次)，建议进行根本性修复")
        
        return recommendations


class AutoFixer:
    
    FIX_STRATEGIES = {
        "missing_field": self._fix_missing_field,
        "missing_section": self._fix_missing_section,
        "low_pass_rate": self._fix_low_pass_rate,
    }
    
    @staticmethod
    def _fix_missing_field(issue: Dict, context: Dict) -> Tuple[bool, str]:
        field = issue.get("field", "")
        if field and "requirement" in context:
            context["requirement"][field] = f"[待填写] {field}"
            return True, f"已添加字段 {field} 的占位符"
        return False, "无法自动修复"
    
    @staticmethod
    def _fix_missing_section(issue: Dict, context: Dict) -> Tuple[bool, str]:
        section = issue.get("section", "")
        if section and "design" in context:
            context["design"][section] = f"## {section}\n\n[待补充内容]"
            return True, f"已添加章节 {section} 的模板"
        return False, "无法自动修复"
    
    @staticmethod
    def _fix_low_pass_rate(issue: Dict, context: Dict) -> Tuple[bool, str]:
        return False, "测试通过率问题需要人工分析和修复"
    
    def can_fix(self, issue_type: str) -> bool:
        return issue_type in self.FIX_STRATEGIES
    
    def fix(self, issue: Dict, context: Dict) -> Tuple[bool, str]:
        issue_type = issue.get("type", "")
        strategy = self.FIX_STRATEGIES.get(issue_type)
        
        if strategy:
            return strategy(issue, context)
        
        return False, f"没有针对 '{issue_type}' 的自动修复策略"


class RequirementTracer:
    """需求到交付追溯器
    
    实现需求到设计、代码、测试、部署的全链路追溯。
    """
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.trace_data: Dict[str, RequirementTrace] = {}
        self._load_trace_data()
    
    def _load_trace_data(self):
        trace_file = self.base_path / "docs" / "requirement_traces.json"
        if trace_file.exists():
            try:
                with open(trace_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for req_id, trace_info in data.items():
                    self.trace_data[req_id] = RequirementTrace(
                        requirement_id=req_id,
                        requirement_title=trace_info.get("title", ""),
                        source=trace_info.get("source", ""),
                        created_at=trace_info.get("created_at", ""),
                        linked_designs=trace_info.get("linked_designs", []),
                        linked_code_files=trace_info.get("linked_code_files", []),
                        linked_tests=trace_info.get("linked_tests", []),
                        linked_deployments=trace_info.get("linked_deployments", []),
                        status=trace_info.get("status", "pending"),
                        trace_score=trace_info.get("trace_score", 0.0)
                    )
            except Exception as e:
                logger.warning(f"加载追溯数据失败: {e}")
    
    def _save_trace_data(self):
        trace_file = self.base_path / "docs" / "requirement_traces.json"
        trace_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {}
        for req_id, trace in self.trace_data.items():
            data[req_id] = {
                "title": trace.requirement_title,
                "source": trace.source,
                "created_at": trace.created_at,
                "linked_designs": trace.linked_designs,
                "linked_code_files": trace.linked_code_files,
                "linked_tests": trace.linked_tests,
                "linked_deployments": trace.linked_deployments,
                "status": trace.status,
                "trace_score": trace.trace_score
            }
        
        with open(trace_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_requirement(self, req_id: str, title: str, source: str = "manual") -> RequirementTrace:
        trace = RequirementTrace(
            requirement_id=req_id,
            requirement_title=title,
            source=source,
            created_at=datetime.now().isoformat()
        )
        self.trace_data[req_id] = trace
        self._save_trace_data()
        return trace
    
    def link_design(self, req_id: str, design_file: str) -> bool:
        if req_id not in self.trace_data:
            return False
        if design_file not in self.trace_data[req_id].linked_designs:
            self.trace_data[req_id].linked_designs.append(design_file)
            self._update_trace_score(req_id)
            self._save_trace_data()
        return True
    
    def link_code(self, req_id: str, code_file: str) -> bool:
        if req_id not in self.trace_data:
            return False
        if code_file not in self.trace_data[req_id].linked_code_files:
            self.trace_data[req_id].linked_code_files.append(code_file)
            self._update_trace_score(req_id)
            self._save_trace_data()
        return True
    
    def link_test(self, req_id: str, test_file: str) -> bool:
        if req_id not in self.trace_data:
            return False
        if test_file not in self.trace_data[req_id].linked_tests:
            self.trace_data[req_id].linked_tests.append(test_file)
            self._update_trace_score(req_id)
            self._save_trace_data()
        return True
    
    def link_deployment(self, req_id: str, deployment_id: str) -> bool:
        if req_id not in self.trace_data:
            return False
        if deployment_id not in self.trace_data[req_id].linked_deployments:
            self.trace_data[req_id].linked_deployments.append(deployment_id)
            self._update_trace_score(req_id)
            self._save_trace_data()
        return True
    
    def _update_trace_score(self, req_id: str):
        trace = self.trace_data[req_id]
        score = 0.0
        if trace.linked_designs:
            score += 0.25
        if trace.linked_code_files:
            score += 0.25
        if trace.linked_tests:
            score += 0.25
        if trace.linked_deployments:
            score += 0.25
        trace.trace_score = score
        
        if score >= 1.0:
            trace.status = "fully_traced"
        elif score >= 0.5:
            trace.status = "partially_traced"
        else:
            trace.status = "pending"
    
    def get_trace_matrix(self) -> TraceabilityMatrix:
        matrix = TraceabilityMatrix(
            matrix_id=f"TM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            created_at=datetime.now().isoformat(),
            requirements=list(self.trace_data.values()),
            total_requirements=len(self.trace_data)
        )
        
        matrix.traced_requirements = len([r for r in self.trace_data.values() if r.trace_score > 0])
        matrix.coverage_score = matrix.traced_requirements / matrix.total_requirements if matrix.total_requirements > 0 else 0
        
        for req_id, trace in self.trace_data.items():
            if trace.trace_score < 1.0:
                gaps = []
                if not trace.linked_designs:
                    gaps.append("missing_design")
                if not trace.linked_code_files:
                    gaps.append("missing_code")
                if not trace.linked_tests:
                    gaps.append("missing_test")
                if not trace.linked_deployments:
                    gaps.append("missing_deployment")
                matrix.gaps.append({
                    "requirement_id": req_id,
                    "title": trace.requirement_title,
                    "gaps": gaps,
                    "trace_score": trace.trace_score
                })
        
        return matrix
    
    def auto_link_from_code(self, code_path: Path) -> int:
        linked_count = 0
        
        for py_file in code_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                req_pattern = r'(?:REQ|需求|requirement)[-_]?(\w+)'
                matches = re.findall(req_pattern, content, re.IGNORECASE)
                
                for req_id in matches:
                    if req_id in self.trace_data:
                        self.link_code(req_id, str(py_file.relative_to(self.base_path)))
                        linked_count += 1
                        
            except Exception as e:
                logger.debug(f"解析文件 {py_file} 失败: {e}")
        
        return linked_count
    
    def auto_link_from_tests(self, test_path: Path) -> int:
        linked_count = 0
        
        for test_file in test_path.rglob("test_*.py"):
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                req_pattern = r'(?:REQ|需求|requirement)[-_]?(\w+)'
                matches = re.findall(req_pattern, content, re.IGNORECASE)
                
                for req_id in matches:
                    if req_id in self.trace_data:
                        self.link_test(req_id, str(test_file.relative_to(self.base_path)))
                        linked_count += 1
                        
            except Exception as e:
                logger.debug(f"解析测试文件 {test_file} 失败: {e}")
        
        return linked_count
    
    def validate_traceability(self) -> Tuple[bool, List[Dict]]:
        issues = []
        matrix = self.get_trace_matrix()
        
        if matrix.coverage_score < 0.8:
            issues.append({
                "type": "low_trace_coverage",
                "severity": Severity.HIGH.value,
                "message": f"需求追溯覆盖率过低: {matrix.coverage_score:.1%}",
                "details": f"仅 {matrix.traced_requirements}/{matrix.total_requirements} 个需求有追溯记录"
            })
        
        for gap in matrix.gaps:
            if gap["trace_score"] == 0:
                issues.append({
                    "type": "untraced_requirement",
                    "severity": Severity.MEDIUM.value,
                    "message": f"需求 '{gap['title']}' 完全未追溯",
                    "requirement_id": gap["requirement_id"]
                })
        
        return len(issues) == 0, issues


class QualityGateValidator:
    """质量门禁验证器
    
    在各个阶段设置质量门禁，确保交付质量。
    """
    
    DEFAULT_GATES = {
        LoopStage.REQUIREMENT: [
            {"name": "需求完整性", "metric": "completeness", "threshold": 0.9},
            {"name": "需求一致性", "metric": "consistency", "threshold": 0.85},
            {"name": "验收标准覆盖", "metric": "acceptance_coverage", "threshold": 1.0}
        ],
        LoopStage.DESIGN: [
            {"name": "设计文档完整性", "metric": "doc_completeness", "threshold": 0.9},
            {"name": "架构评审通过", "metric": "review_passed", "threshold": 1.0},
            {"name": "技术方案可行", "metric": "feasibility", "threshold": 0.8}
        ],
        LoopStage.DEVELOPMENT: [
            {"name": "代码覆盖率", "metric": "code_coverage", "threshold": 0.8},
            {"name": "静态分析通过", "metric": "static_analysis", "threshold": 1.0},
            {"name": "代码审查完成", "metric": "code_review", "threshold": 1.0}
        ],
        LoopStage.TESTING: [
            {"name": "测试通过率", "metric": "test_pass_rate", "threshold": 1.0},
            {"name": "缺陷修复率", "metric": "defect_fix_rate", "threshold": 1.0},
            {"name": "性能达标", "metric": "performance", "threshold": 0.9}
        ],
        LoopStage.DEPLOYMENT: [
            {"name": "部署脚本验证", "metric": "deploy_script_valid", "threshold": 1.0},
            {"name": "环境配置正确", "metric": "env_config", "threshold": 1.0},
            {"name": "回滚方案就绪", "metric": "rollback_ready", "threshold": 1.0}
        ],
        LoopStage.OPERATION: [
            {"name": "服务可用性", "metric": "availability", "threshold": 0.999},
            {"name": "响应时间", "metric": "response_time", "threshold": 0.95},
            {"name": "错误率", "metric": "error_rate", "threshold": 0.99}
        ]
    }
    
    def __init__(self):
        self.gates: Dict[str, QualityGate] = {}
        self._initialize_default_gates()
    
    def _initialize_default_gates(self):
        for stage, criteria_list in self.DEFAULT_GATES.items():
            for criteria in criteria_list:
                gate_id = f"GATE-{stage.value}-{criteria['metric']}"
                self.gates[gate_id] = QualityGate(
                    gate_id=gate_id,
                    name=criteria["name"],
                    stage=stage,
                    criteria=[criteria],
                    threshold=criteria["threshold"]
                )
    
    def add_custom_gate(self, gate: QualityGate):
        self.gates[gate.gate_id] = gate
    
    def evaluate_gate(self, gate_id: str, actual_value: float) -> QualityGate:
        if gate_id not in self.gates:
            raise ValueError(f"未找到质量门禁: {gate_id}")
        
        gate = self.gates[gate_id]
        gate.actual_value = actual_value
        gate.passed = actual_value >= gate.threshold
        gate.status = LoopStatus.PASSED if gate.passed else LoopStatus.FAILED
        gate.timestamp = datetime.now().isoformat()
        
        return gate
    
    def evaluate_stage_gates(self, stage: LoopStage, metrics: Dict[str, float]) -> List[QualityGate]:
        results = []
        
        for gate_id, gate in self.gates.items():
            if gate.stage == stage:
                metric_name = gate.criteria[0]["metric"]
                if metric_name in metrics:
                    self.evaluate_gate(gate_id, metrics[metric_name])
                    results.append(gate)
        
        return results
    
    def get_stage_gate_status(self, stage: LoopStage) -> Dict[str, Any]:
        stage_gates = [g for g in self.gates.values() if g.stage == stage]
        
        if not stage_gates:
            return {"status": "no_gates", "passed": 0, "total": 0}
        
        passed = sum(1 for g in stage_gates if g.passed)
        total = len(stage_gates)
        
        return {
            "status": "passed" if passed == total else "failed",
            "passed": passed,
            "total": total,
            "pass_rate": passed / total if total > 0 else 0,
            "gates": [
                {
                    "gate_id": g.gate_id,
                    "name": g.name,
                    "threshold": g.threshold,
                    "actual_value": g.actual_value,
                    "passed": g.passed
                }
                for g in stage_gates
            ]
        }
    
    def get_all_gates_report(self) -> Dict[str, Any]:
        report = {
            "total_gates": len(self.gates),
            "passed_gates": sum(1 for g in self.gates.values() if g.passed),
            "failed_gates": sum(1 for g in self.gates.values() if g.status == LoopStatus.FAILED),
            "pending_gates": sum(1 for g in self.gates.values() if g.status == LoopStatus.PENDING),
            "by_stage": {}
        }
        
        for stage in LoopStage:
            if stage != LoopStage.FEEDBACK:
                report["by_stage"][stage.value] = self.get_stage_gate_status(stage)
        
        return report


class DeliverableChecker:
    """交付物完整性检查器
    
    检查各阶段交付物的完整性和有效性。
    """
    
    DEFAULT_DELIVERABLES = {
        LoopStage.REQUIREMENT: [
            {"name": "需求规格说明书", "type": "document", "pattern": "**/需求*.md", "required": True},
            {"name": "用户故事", "type": "document", "pattern": "**/user_stories*.md", "required": False},
            {"name": "验收标准", "type": "document", "pattern": "**/acceptance*.md", "required": True}
        ],
        LoopStage.DESIGN: [
            {"name": "架构设计文档", "type": "document", "pattern": "**/架构*.md", "required": True},
            {"name": "数据库设计", "type": "document", "pattern": "**/数据库*.md", "required": True},
            {"name": "API设计文档", "type": "document", "pattern": "**/api*.md", "required": True},
            {"name": "接口定义", "type": "code", "pattern": "**/models/*.py", "required": True}
        ],
        LoopStage.DEVELOPMENT: [
            {"name": "源代码", "type": "code", "pattern": "**/*.py", "required": True},
            {"name": "配置文件", "type": "config", "pattern": "**/config*.py", "required": True},
            {"name": "单元测试", "type": "test", "pattern": "**/test_*.py", "required": True}
        ],
        LoopStage.TESTING: [
            {"name": "测试报告", "type": "report", "pattern": "**/test_report*.json", "required": True},
            {"name": "覆盖率报告", "type": "report", "pattern": "**/coverage*.json", "required": True},
            {"name": "缺陷报告", "type": "report", "pattern": "**/defects*.json", "required": False}
        ],
        LoopStage.DEPLOYMENT: [
            {"name": "部署脚本", "type": "script", "pattern": "**/deploy*.sh", "required": True},
            {"name": "Docker配置", "type": "config", "pattern": "**/Dockerfile", "required": False},
            {"name": "环境配置", "type": "config", "pattern": "**/.env*", "required": True}
        ],
        LoopStage.OPERATION: [
            {"name": "监控配置", "type": "config", "pattern": "**/monitoring*.json", "required": False},
            {"name": "日志配置", "type": "config", "pattern": "**/logging*.json", "required": False},
            {"name": "运维手册", "type": "document", "pattern": "**/运维*.md", "required": True}
        ]
    }
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.deliverables: Dict[str, Deliverable] = {}
        self._initialize_deliverables()
    
    def _initialize_deliverables(self):
        for stage, deliverable_list in self.DEFAULT_DELIVERABLES.items():
            for dl in deliverable_list:
                deliverable_id = f"DEL-{stage.value}-{dl['name']}"
                self.deliverables[deliverable_id] = Deliverable(
                    deliverable_id=deliverable_id,
                    name=dl["name"],
                    type=dl["type"],
                    path=dl["pattern"],
                    required=dl["required"]
                )
    
    def add_custom_deliverable(self, deliverable: Deliverable):
        self.deliverables[deliverable.deliverable_id] = deliverable
    
    def check_deliverable(self, deliverable_id: str) -> Deliverable:
        if deliverable_id not in self.deliverables:
            raise ValueError(f"未找到交付物定义: {deliverable_id}")
        
        deliverable = self.deliverables[deliverable_id]
        pattern = deliverable.path
        
        matches = list(self.base_path.glob(pattern))
        
        if matches:
            deliverable.exists = True
            first_match = matches[0]
            deliverable.path = str(first_match.relative_to(self.base_path))
            
            if first_match.is_file():
                stat = first_match.stat()
                deliverable.size = stat.st_size
                deliverable.last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                with open(first_match, 'rb') as f:
                    deliverable.checksum = hashlib.md5(f.read()).hexdigest()
                
                validation_errors = self._validate_deliverable_content(first_match, deliverable.type)
                deliverable.validation_errors = validation_errors
        else:
            deliverable.exists = False
            deliverable.validation_errors = ["交付物文件不存在"]
        
        return deliverable
    
    def _validate_deliverable_content(self, file_path: Path, deliverable_type: str) -> List[str]:
        errors = []
        
        try:
            if deliverable_type == "document":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if len(content) < 100:
                    errors.append("文档内容过短")
                
                if not re.search(r'^#\s+', content, re.MULTILINE):
                    errors.append("文档缺少标题")
                    
            elif deliverable_type == "code":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if "def " not in content and "class " not in content:
                    errors.append("代码文件缺少函数或类定义")
                    
            elif deliverable_type == "test":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if "def test_" not in content:
                    errors.append("测试文件缺少测试函数")
                    
            elif deliverable_type == "config":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if not content.strip():
                    errors.append("配置文件为空")
                    
        except Exception as e:
            errors.append(f"验证失败: {str(e)}")
        
        return errors
    
    def check_stage_deliverables(self, stage: LoopStage) -> List[Deliverable]:
        results = []
        
        for deliverable_id, deliverable in self.deliverables.items():
            if deliverable_id.startswith(f"DEL-{stage.value}-"):
                self.check_deliverable(deliverable_id)
                results.append(deliverable)
        
        return results
    
    def get_deliverable_status(self, stage: LoopStage) -> Dict[str, Any]:
        stage_deliverables = self.check_stage_deliverables(stage)
        
        required = [d for d in stage_deliverables if d.required]
        optional = [d for d in stage_deliverables if not d.required]
        
        required_exists = sum(1 for d in required if d.exists)
        optional_exists = sum(1 for d in optional if d.exists)
        
        all_valid = all(len(d.validation_errors) == 0 for d in stage_deliverables if d.exists)
        
        return {
            "stage": stage.value,
            "required_total": len(required),
            "required_exists": required_exists,
            "optional_total": len(optional),
            "optional_exists": optional_exists,
            "all_required_present": required_exists == len(required),
            "all_valid": all_valid,
            "completeness": required_exists / len(required) if required else 1.0,
            "deliverables": [
                {
                    "deliverable_id": d.deliverable_id,
                    "name": d.name,
                    "type": d.type,
                    "exists": d.exists,
                    "required": d.required,
                    "validation_errors": d.validation_errors
                }
                for d in stage_deliverables
            ]
        }
    
    def get_all_deliverables_report(self) -> Dict[str, Any]:
        report = {
            "total_deliverables": len(self.deliverables),
            "existing_deliverables": sum(1 for d in self.deliverables.values() if d.exists),
            "missing_required": [],
            "by_stage": {}
        }
        
        for stage in LoopStage:
            if stage != LoopStage.FEEDBACK:
                status = self.get_deliverable_status(stage)
                report["by_stage"][stage.value] = status
                
                for d in status["deliverables"]:
                    if d["required"] and not d["exists"]:
                        report["missing_required"].append({
                            "stage": stage.value,
                            "name": d["name"],
                            "deliverable_id": d["deliverable_id"]
                        })
        
        return report


class ClosedLoopVerifier:
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getcwd())
        
        self.validators = {
            LoopStage.REQUIREMENT: RequirementValidator(),
            LoopStage.DESIGN: DesignValidator(),
            LoopStage.DEVELOPMENT: DevelopmentValidator(),
            LoopStage.TESTING: TestingValidator(),
            LoopStage.DEPLOYMENT: DeploymentValidator(),
            LoopStage.OPERATION: OperationValidator(),
        }
        
        self.learner = FeedbackLearner()
        self.auto_fixer = AutoFixer()
        
        self.requirement_tracer = RequirementTracer(self.base_path)
        self.quality_gate_validator = QualityGateValidator()
        self.deliverable_checker = DeliverableChecker(self.base_path)
        
        self.iterations: List[LoopIteration] = []
        self.context: Dict[str, Any] = {}
    
    def run_full_loop(self, context: Dict[str, Any] = None) -> ClosedLoopReport:
        logger.info("开始执行完整闭环验证...")
        
        if context:
            self.context = context
        
        iteration = LoopIteration(
            iteration_id=f"LOOP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            started_at=datetime.now().isoformat()
        )
        
        stages = [
            (LoopStage.REQUIREMENT, self._validate_requirement),
            (LoopStage.DESIGN, self._validate_design),
            (LoopStage.DEVELOPMENT, self._validate_development),
            (LoopStage.TESTING, self._validate_testing),
            (LoopStage.DEPLOYMENT, self._validate_deployment),
            (LoopStage.OPERATION, self._validate_operation),
            (LoopStage.FEEDBACK, self._validate_feedback),
        ]
        
        for stage, validator_func in stages:
            checkpoint = self._run_stage(stage, validator_func)
            iteration.checkpoints.append(checkpoint)
            
            if checkpoint.status == LoopStatus.FAILED:
                fixed = self._attempt_auto_fix(checkpoint)
                if fixed:
                    checkpoint.status = LoopStatus.AUTO_FIXED
                    iteration.auto_fixed_issues += 1
                else:
                    checkpoint.status = LoopStatus.MANUAL_REQUIRED
                    iteration.manual_issues += 1
            
            iteration.total_issues += len(checkpoint.issues)
        
        iteration.status = self._determine_iteration_status(iteration)
        iteration.completed_at = datetime.now().isoformat()
        iteration.learnings = self.learner.get_recommendations()
        
        self.iterations.append(iteration)
        
        report = self._generate_report(iteration)
        self._save_report(report)
        
        logger.info(f"闭环验证完成，状态: {iteration.status.value}")
        return report
    
    def run_full_loop_with_trace(self, context: Dict[str, Any] = None) -> ClosedLoopReport:
        """执行带追溯功能的完整闭环验证"""
        logger.info("开始执行带追溯的完整闭环验证...")
        
        if context:
            self.context = context
        
        iteration = LoopIteration(
            iteration_id=f"LOOP-TRACE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            started_at=datetime.now().isoformat()
        )
        
        stages = [
            (LoopStage.REQUIREMENT, self._validate_requirement_with_trace),
            (LoopStage.DESIGN, self._validate_design_with_trace),
            (LoopStage.DEVELOPMENT, self._validate_development_with_trace),
            (LoopStage.TESTING, self._validate_testing_with_trace),
            (LoopStage.DEPLOYMENT, self._validate_deployment_with_trace),
            (LoopStage.OPERATION, self._validate_operation_with_trace),
            (LoopStage.FEEDBACK, self._validate_feedback),
        ]
        
        for stage, validator_func in stages:
            checkpoint = self._run_stage(stage, validator_func)
            iteration.checkpoints.append(checkpoint)
            
            if checkpoint.status == LoopStatus.FAILED:
                fixed = self._attempt_auto_fix(checkpoint)
                if fixed:
                    checkpoint.status = LoopStatus.AUTO_FIXED
                    iteration.auto_fixed_issues += 1
                else:
                    checkpoint.status = LoopStatus.MANUAL_REQUIRED
                    iteration.manual_issues += 1
            
            iteration.total_issues += len(checkpoint.issues)
        
        trace_result = self._validate_traceability()
        if not trace_result["passed"]:
            trace_checkpoint = LoopCheckpoint(
                checkpoint_id=f"CP-TRACE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                stage=LoopStage.FEEDBACK,
                name="需求追溯验证",
                description="验证需求到交付的追溯完整性",
                status=LoopStatus.FAILED if trace_result["issues"] else LoopStatus.PASSED,
                timestamp=datetime.now().isoformat(),
                issues=trace_result["issues"]
            )
            iteration.checkpoints.append(trace_checkpoint)
            iteration.total_issues += len(trace_result["issues"])
        
        gate_result = self._validate_all_quality_gates()
        if not gate_result["all_passed"]:
            gate_checkpoint = LoopCheckpoint(
                checkpoint_id=f"CP-GATES-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                stage=LoopStage.FEEDBACK,
                name="质量门禁验证",
                description="验证各阶段质量门禁通过情况",
                status=LoopStatus.FAILED,
                timestamp=datetime.now().isoformat(),
                issues=gate_result["failed_gates"]
            )
            iteration.checkpoints.append(gate_checkpoint)
            iteration.total_issues += len(gate_result["failed_gates"])
        
        deliverable_result = self._check_all_deliverables()
        if deliverable_result["missing_required"]:
            deliverable_checkpoint = LoopCheckpoint(
                checkpoint_id=f"CP-DELIVER-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                stage=LoopStage.FEEDBACK,
                name="交付物完整性检查",
                description="检查各阶段交付物完整性",
                status=LoopStatus.FAILED,
                timestamp=datetime.now().isoformat(),
                issues=[{"type": "missing_deliverable", "severity": Severity.HIGH.value, "message": f"缺少交付物: {d['name']}"} for d in deliverable_result["missing_required"]]
            )
            iteration.checkpoints.append(deliverable_checkpoint)
            iteration.total_issues += len(deliverable_result["missing_required"])
        
        iteration.status = self._determine_iteration_status(iteration)
        iteration.completed_at = datetime.now().isoformat()
        iteration.learnings = self.learner.get_recommendations()
        
        self.iterations.append(iteration)
        
        report = self._generate_report(iteration)
        report.summary["traceability"] = trace_result["summary"]
        report.summary["quality_gates"] = gate_result["summary"]
        report.summary["deliverables"] = deliverable_result["summary"]
        self._save_report(report)
        
        logger.info(f"带追溯的闭环验证完成，状态: {iteration.status.value}")
        return report
    
    def _validate_requirement_with_trace(self) -> Tuple[bool, List[Dict]]:
        passed, issues = self.validators[LoopStage.REQUIREMENT].validate(
            self.context.get("requirement", {})
        )
        
        trace_passed, trace_issues = self.requirement_tracer.validate_traceability()
        issues.extend(trace_issues)
        
        return passed and trace_passed, issues
    
    def _validate_design_with_trace(self) -> Tuple[bool, List[Dict]]:
        passed, issues = self.validators[LoopStage.DESIGN].validate(
            self.context.get("design", {})
        )
        
        design_metrics = self.context.get("design_metrics", {})
        gates = self.quality_gate_validator.evaluate_stage_gates(LoopStage.DESIGN, design_metrics)
        for gate in gates:
            if not gate.passed:
                issues.append({
                    "type": "quality_gate_failed",
                    "severity": Severity.HIGH.value,
                    "message": f"质量门禁未通过: {gate.name}",
                    "threshold": gate.threshold,
                    "actual": gate.actual_value
                })
        
        return passed and all(g.passed for g in gates), issues
    
    def _validate_development_with_trace(self) -> Tuple[bool, List[Dict]]:
        passed, issues = self.validators[LoopStage.DEVELOPMENT].validate(
            self.context.get("code_path", str(self.base_path))
        )
        
        dev_metrics = self.context.get("development_metrics", {})
        gates = self.quality_gate_validator.evaluate_stage_gates(LoopStage.DEVELOPMENT, dev_metrics)
        for gate in gates:
            if not gate.passed:
                issues.append({
                    "type": "quality_gate_failed",
                    "severity": Severity.HIGH.value,
                    "message": f"质量门禁未通过: {gate.name}",
                    "threshold": gate.threshold,
                    "actual": gate.actual_value
                })
        
        deliverable_status = self.deliverable_checker.get_deliverable_status(LoopStage.DEVELOPMENT)
        if not deliverable_status["all_required_present"]:
            for d in deliverable_status["deliverables"]:
                if d["required"] and not d["exists"]:
                    issues.append({
                        "type": "missing_deliverable",
                        "severity": Severity.HIGH.value,
                        "message": f"缺少开发交付物: {d['name']}"
                    })
        
        return passed and all(g.passed for g in gates), issues
    
    def _validate_testing_with_trace(self) -> Tuple[bool, List[Dict]]:
        passed, issues = self.validators[LoopStage.TESTING].validate(
            self.context.get("test_results", {"total": 0, "passed": 0, "failed": 0})
        )
        
        test_metrics = self.context.get("test_metrics", {})
        gates = self.quality_gate_validator.evaluate_stage_gates(LoopStage.TESTING, test_metrics)
        for gate in gates:
            if not gate.passed:
                issues.append({
                    "type": "quality_gate_failed",
                    "severity": Severity.HIGH.value,
                    "message": f"质量门禁未通过: {gate.name}",
                    "threshold": gate.threshold,
                    "actual": gate.actual_value
                })
        
        return passed and all(g.passed for g in gates), issues
    
    def _validate_deployment_with_trace(self) -> Tuple[bool, List[Dict]]:
        passed, issues = self.validators[LoopStage.DEPLOYMENT].validate(
            self.context.get("deploy_config", {})
        )
        
        deploy_metrics = self.context.get("deployment_metrics", {})
        gates = self.quality_gate_validator.evaluate_stage_gates(LoopStage.DEPLOYMENT, deploy_metrics)
        for gate in gates:
            if not gate.passed:
                issues.append({
                    "type": "quality_gate_failed",
                    "severity": Severity.HIGH.value,
                    "message": f"质量门禁未通过: {gate.name}",
                    "threshold": gate.threshold,
                    "actual": gate.actual_value
                })
        
        return passed and all(g.passed for g in gates), issues
    
    def _validate_operation_with_trace(self) -> Tuple[bool, List[Dict]]:
        passed, issues = self.validators[LoopStage.OPERATION].validate(
            self.context.get("operation_metrics", {})
        )
        
        op_metrics = self.context.get("operation_metrics", {})
        gates = self.quality_gate_validator.evaluate_stage_gates(LoopStage.OPERATION, op_metrics)
        for gate in gates:
            if not gate.passed:
                issues.append({
                    "type": "quality_gate_failed",
                    "severity": Severity.HIGH.value,
                    "message": f"质量门禁未通过: {gate.name}",
                    "threshold": gate.threshold,
                    "actual": gate.actual_value
                })
        
        return passed and all(g.passed for g in gates), issues
    
    def _validate_traceability(self) -> Dict[str, Any]:
        passed, issues = self.requirement_tracer.validate_traceability()
        matrix = self.requirement_tracer.get_trace_matrix()
        
        return {
            "passed": passed,
            "issues": issues,
            "summary": {
                "total_requirements": matrix.total_requirements,
                "traced_requirements": matrix.traced_requirements,
                "coverage_score": matrix.coverage_score,
                "gaps_count": len(matrix.gaps)
            }
        }
    
    def _validate_all_quality_gates(self) -> Dict[str, Any]:
        report = self.quality_gate_validator.get_all_gates_report()
        
        failed_gates = []
        for gate_id, gate in self.quality_gate_validator.gates.items():
            if gate.status == LoopStatus.FAILED:
                failed_gates.append({
                    "type": "quality_gate_failed",
                    "severity": Severity.HIGH.value,
                    "message": f"质量门禁 '{gate.name}' 未通过",
                    "gate_id": gate_id,
                    "threshold": gate.threshold,
                    "actual": gate.actual_value
                })
        
        return {
            "all_passed": report["failed_gates"] == 0,
            "failed_gates": failed_gates,
            "summary": {
                "total_gates": report["total_gates"],
                "passed_gates": report["passed_gates"],
                "failed_gates": report["failed_gates"],
                "pending_gates": report["pending_gates"]
            }
        }
    
    def _check_all_deliverables(self) -> Dict[str, Any]:
        report = self.deliverable_checker.get_all_deliverables_report()
        
        return {
            "missing_required": report["missing_required"],
            "summary": {
                "total_deliverables": report["total_deliverables"],
                "existing_deliverables": report["existing_deliverables"],
                "missing_required_count": len(report["missing_required"])
            }
        }
    
    def add_requirement_trace(self, req_id: str, title: str) -> RequirementTrace:
        return self.requirement_tracer.add_requirement(req_id, title)
    
    def link_requirement_to_code(self, req_id: str, code_file: str) -> bool:
        return self.requirement_tracer.link_code(req_id, code_file)
    
    def link_requirement_to_test(self, req_id: str, test_file: str) -> bool:
        return self.requirement_tracer.link_test(req_id, test_file)
    
    def get_trace_matrix(self) -> TraceabilityMatrix:
        return self.requirement_tracer.get_trace_matrix()
    
    def evaluate_quality_gate(self, gate_id: str, actual_value: float) -> QualityGate:
        return self.quality_gate_validator.evaluate_gate(gate_id, actual_value)
    
    def get_quality_gates_report(self) -> Dict[str, Any]:
        return self.quality_gate_validator.get_all_gates_report()
    
    def check_deliverables(self, stage: LoopStage = None) -> Dict[str, Any]:
        if stage:
            return self.deliverable_checker.get_deliverable_status(stage)
        return self.deliverable_checker.get_all_deliverables_report()
    
    def _run_stage(self, stage: LoopStage, validator_func: Callable) -> LoopCheckpoint:
        logger.info(f"执行阶段: {stage.value}")
        
        checkpoint = LoopCheckpoint(
            checkpoint_id=f"CP-{stage.value.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            stage=stage,
            name=self._get_stage_name(stage),
            description=self._get_stage_description(stage),
            status=LoopStatus.RUNNING,
            timestamp=datetime.now().isoformat()
        )
        
        try:
            passed, issues = validator_func()
            
            checkpoint.issues = issues
            checkpoint.checks = [{"passed": passed, "issues_count": len(issues)}]
            
            if passed:
                checkpoint.status = LoopStatus.PASSED
            elif len(issues) > 0:
                checkpoint.status = LoopStatus.FAILED
            else:
                checkpoint.status = LoopStatus.PASSED
            
            for issue in issues:
                self.learner.learn(issue)
            
        except Exception as e:
            checkpoint.status = LoopStatus.FAILED
            checkpoint.issues = [{
                "type": "execution_error",
                "severity": Severity.CRITICAL.value,
                "message": str(e),
                "traceback": traceback.format_exc()
            }]
        
        return checkpoint
    
    def _get_stage_name(self, stage: LoopStage) -> str:
        names = {
            LoopStage.REQUIREMENT: "需求验证",
            LoopStage.DESIGN: "设计验证",
            LoopStage.DEVELOPMENT: "开发验证",
            LoopStage.TESTING: "测试验证",
            LoopStage.DEPLOYMENT: "部署验证",
            LoopStage.OPERATION: "运维验证",
            LoopStage.FEEDBACK: "反馈学习",
        }
        return names.get(stage, stage.value)
    
    def _get_stage_description(self, stage: LoopStage) -> str:
        descriptions = {
            LoopStage.REQUIREMENT: "验证需求完整性、一致性、可追溯性",
            LoopStage.DESIGN: "验证设计文档完整性、架构合理性",
            LoopStage.DEVELOPMENT: "验证代码质量、规范遵循",
            LoopStage.TESTING: "验证测试覆盖率、测试通过率",
            LoopStage.DEPLOYMENT: "验证部署配置、环境准备",
            LoopStage.OPERATION: "验证运行状态、性能指标",
            LoopStage.FEEDBACK: "收集反馈、学习改进",
        }
        return descriptions.get(stage, "")
    
    def _validate_requirement(self) -> Tuple[bool, List[Dict]]:
        requirement = self.context.get("requirement", {})
        return self.validators[LoopStage.REQUIREMENT].validate(requirement)
    
    def _validate_design(self) -> Tuple[bool, List[Dict]]:
        design = self.context.get("design", {})
        return self.validators[LoopStage.DESIGN].validate(design)
    
    def _validate_development(self) -> Tuple[bool, List[Dict]]:
        code_path = self.context.get("code_path", str(self.base_path))
        return self.validators[LoopStage.DEVELOPMENT].validate(code_path)
    
    def _validate_testing(self) -> Tuple[bool, List[Dict]]:
        test_results = self.context.get("test_results", {"total": 0, "passed": 0, "failed": 0})
        return self.validators[LoopStage.TESTING].validate(test_results)
    
    def _validate_deployment(self) -> Tuple[bool, List[Dict]]:
        deploy_config = self.context.get("deploy_config", {})
        return self.validators[LoopStage.DEPLOYMENT].validate(deploy_config)
    
    def _validate_operation(self) -> Tuple[bool, List[Dict]]:
        metrics = self.context.get("operation_metrics", {})
        return self.validators[LoopStage.OPERATION].validate(metrics)
    
    def _attempt_auto_fix(self, checkpoint: LoopCheckpoint) -> bool:
        any_fixed = False
        
        for issue in checkpoint.issues:
            if self.auto_fixer.can_fix(issue.get("type", "")):
                fixed, message = self.auto_fixer.fix(issue, self.context)
                if fixed:
                    checkpoint.fixes_applied.append(message)
                    any_fixed = True
        
        return any_fixed
    
    def _determine_iteration_status(self, iteration: LoopIteration) -> LoopStatus:
        for checkpoint in iteration.checkpoints:
            if checkpoint.status == LoopStatus.FAILED:
                return LoopStatus.FAILED
            if checkpoint.status == LoopStatus.MANUAL_REQUIRED:
                return LoopStatus.NEEDS_FIX
        
        return LoopStatus.PASSED
    
    def _generate_report(self, iteration: LoopIteration) -> ClosedLoopReport:
        passed_checkpoints = sum(1 for cp in iteration.checkpoints 
                                 if cp.status in [LoopStatus.PASSED, LoopStatus.AUTO_FIXED])
        total_checkpoints = len(iteration.checkpoints)
        
        quality_score = passed_checkpoints / total_checkpoints if total_checkpoints > 0 else 0
        
        summary = {
            "total_checkpoints": total_checkpoints,
            "passed_checkpoints": passed_checkpoints,
            "total_issues": iteration.total_issues,
            "auto_fixed_issues": iteration.auto_fixed_issues,
            "manual_issues": iteration.manual_issues,
            "quality_score": round(quality_score * 100, 2)
        }
        
        recommendations = iteration.learnings.copy()
        
        if iteration.manual_issues > 0:
            recommendations.append(f"存在 {iteration.manual_issues} 个问题需要人工处理")
        
        next_actions = []
        if iteration.status == LoopStatus.FAILED:
            next_actions.append("修复所有失败阶段的问题")
            next_actions.append("重新运行闭环验证")
        elif iteration.status == LoopStatus.NEEDS_FIX:
            next_actions.append("处理需要人工干预的问题")
            next_actions.append("验证自动修复的效果")
        else:
            next_actions.append("继续监控运行状态")
            next_actions.append("收集用户反馈")
        
        return ClosedLoopReport(
            report_id=f"CLR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            iteration=iteration,
            summary=summary,
            recommendations=recommendations,
            next_actions=next_actions,
            quality_score=quality_score
        )
    
    def _save_report(self, report: ClosedLoopReport):
        output_dir = self.base_path / "docs" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        json_path = output_dir / f"closed_loop_report_{report.report_id}.json"
        
        report_dict = {
            "report_id": report.report_id,
            "generated_at": report.generated_at,
            "quality_score": report.quality_score,
            "summary": report.summary,
            "recommendations": report.recommendations,
            "next_actions": report.next_actions,
            "iteration": {
                "iteration_id": report.iteration.iteration_id,
                "status": report.iteration.status.value,
                "started_at": report.iteration.started_at,
                "completed_at": report.iteration.completed_at,
                "total_issues": report.iteration.total_issues,
                "auto_fixed_issues": report.iteration.auto_fixed_issues,
                "manual_issues": report.iteration.manual_issues,
                "checkpoints": [
                    {
                        "checkpoint_id": cp.checkpoint_id,
                        "stage": cp.stage.value,
                        "name": cp.name,
                        "status": cp.status.value,
                        "issues_count": len(cp.issues),
                        "fixes_applied": cp.fixes_applied
                    }
                    for cp in report.iteration.checkpoints
                ]
            }
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        md_path = json_path.with_suffix('.md')
        self._save_markdown_report(report, md_path)
        
        logger.info(f"闭环验证报告已保存: {json_path}")
    
    def _save_markdown_report(self, report: ClosedLoopReport, output_path: Path):
        lines = [
            "# 闭环验证报告",
            f"\n**报告ID**: {report.report_id}",
            f"**生成时间**: {report.generated_at}",
            f"**质量评分**: {report.quality_score:.1%}",
            f"**总体状态**: {report.iteration.status.value.upper()}",
            "\n## 摘要",
            f"\n| 指标 | 值 |",
            f"|------|-----|",
            f"| 检查点总数 | {report.summary['total_checkpoints']} |",
            f"| 通过检查点 | {report.summary['passed_checkpoints']} |",
            f"| 问题总数 | {report.summary['total_issues']} |",
            f"| 自动修复 | {report.summary['auto_fixed_issues']} |",
            f"| 需人工处理 | {report.summary['manual_issues']} |",
            "\n## 检查点详情",
        ]
        
        for cp in report.iteration.checkpoints:
            status_icon = "✓" if cp.status in [LoopStatus.PASSED, LoopStatus.AUTO_FIXED] else "✗"
            lines.append(f"\n### {status_icon} {cp.name}")
            lines.append(f"- **阶段**: {cp.stage.value}")
            lines.append(f"- **状态**: {cp.status.value}")
            
            if cp.issues:
                lines.append("\n**问题**:")
                for issue in cp.issues:
                    lines.append(f"  - [{issue.get('severity', 'unknown')}] {issue.get('message', '')}")
            
            if cp.fixes_applied:
                lines.append("\n**已应用的修复**:")
                for fix in cp.fixes_applied:
                    lines.append(f"  - {fix}")
        
        if report.recommendations:
            lines.append("\n## 改进建议")
            for rec in report.recommendations:
                lines.append(f"- {rec}")
        
        if report.next_actions:
            lines.append("\n## 下一步行动")
            for action in report.next_actions:
                lines.append(f"- {action}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="完整闭环验证系统")
    parser.add_argument("--base-path", default=".", help="项目基础路径")
    parser.add_argument("--context-file", help="上下文文件路径(JSON)")
    parser.add_argument("--stage", choices=[s.value for s in LoopStage], 
                       help="仅运行指定阶段")
    
    args = parser.parse_args()
    
    context = {}
    if args.context_file:
        try:
            with open(args.context_file, 'r', encoding='utf-8') as f:
                context = json.load(f)
        except Exception as e:
            logger.warning(f"加载上下文文件失败: {e}")
    
    verifier = ClosedLoopVerifier(args.base_path)
    
    if args.stage:
        stage = LoopStage(args.stage)
        logger.info(f"仅运行阶段: {stage.value}")
    
    report = verifier.run_full_loop(context)
    
    print("\n" + "="*60)
    print("闭环验证报告")
    print("="*60)
    print(f"报告ID: {report.report_id}")
    print(f"质量评分: {report.quality_score:.1%}")
    print(f"状态: {report.iteration.status.value.upper()}")
    print(f"\n摘要:")
    print(f"  检查点: {report.summary['passed_checkpoints']}/{report.summary['total_checkpoints']}")
    print(f"  问题: {report.summary['total_issues']} (自动修复: {report.summary['auto_fixed_issues']}, 需人工: {report.summary['manual_issues']})")
    
    if report.next_actions:
        print("\n下一步行动:")
        for action in report.next_actions:
            print(f"  - {action}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
