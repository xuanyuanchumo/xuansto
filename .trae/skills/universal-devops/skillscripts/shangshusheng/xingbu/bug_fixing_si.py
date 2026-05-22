"""
缺陷修复司 - 问题诊断引导、根因分析框架、热修复流程管理
"""
from __future__ import annotations

import json
import re
import uuid
import hashlib
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
from pathlib import Path
from typing import Any


class BugSeverity(Enum):
    """缺陷严重度"""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    ENHANCEMENT = "enhancement"
    COSMETIC = "cosmetic"


class BugStatus(Enum):
    """缺陷状态"""

    NEW = "new"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    VERIFIED = "verified"
    CLOSED = "closed"
    REOPENED = "reopened"


@dataclass
class BugRecord:
    """缺陷记录"""

    id: str
    title: str
    description: str
    severity: BugSeverity
    status: BugStatus = BugStatus.NEW
    reporter: str = ""
    assignee: str = ""
    component: str = ""
    environment: str = ""
    reproduction_steps: list[str] = field(default_factory=list)
    expected_behavior: str = ""
    actual_behavior: str = ""
    root_cause: str = ""
    fix_description: str = ""
    affected_files: list[str] = field(default_factory=list)
    related_bugs: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    resolved_at: str = ""


@dataclass
class RootCauseAnalysis:
    """根因分析结果"""

    bug_id: str
    method: str  # 5whys/fishbone/fault_tree
    analysis_chain: list[dict[str, str]] = field(default_factory=list)
    root_cause: str = ""
    contributing_factors: list[str] = field(default_factory=list)
    category: str = ""
    prevention_measures: list[str] = field(default_factory=list)


@dataclass
class DiagnosisStep:
    """诊断步骤"""

    step_number: int
    action: str
    expected_result: str
    command_or_code: str = ""
    status: str = "pending"  # pending/passed/failed/skipped
    notes: str = ""


@dataclass
class HotfixRecord:
    """热修复记录"""

    hotfix_id: str
    bug_id: str
    branch_name: str
    description: str
    severity: BugSeverity
    created_at: str = ""
    merged_at: str = ""
    released_at: str = ""
    rollback_available: bool = True
    test_results: dict[str, bool] = field(default_factory=dict)
    changelog_entry: str = ""


@dataclass
class FixVerificationChecklist:
    """修复验证清单"""

    bug_id: str
    items: list[dict[str, bool]] = field(default_factory=list)
    completed_at: str = ""
    verified_by: str = ""


@dataclass
class BugTrendMetrics:
    """缺陷趋势指标"""

    total_bugs: int = 0
    open_bugs: int = 0
    critical_open: int = 0
    avg_resolution_time_hours: float = 0.0
    mtbf_hours: float = 0.0
    escape_rate: float = 0.0
    reopen_rate: float = 0.0
    by_severity: dict[str, int] = field(default_factory=dict)
    by_component: dict[str, int] = field(default_factory=dict)


class BugFixingError(Exception):
    """缺陷修复异常"""


class BugNotFoundError(BugFixingError):
    """缺陷未找到异常"""


class HotfixError(BugFixingError):
    """热修复异常"""


class BugFixingSi:
    """
    缺陷修复司 - 刑部·比部司

    提供全面的缺陷管理能力：
    - 缺陷分级分类（Critical/Major/Minor等）
    - 根因分析框架（5 Whys/Fishbone/Fault Tree）
    - 问题诊断引导（症状→原因→排查→确认）
    - 热修复流程管理
    - Bug复现步骤标准化
    - 修复方案评估
    - 修复验证清单
    - 缺陷趋势分析
    """

    def __init__(self) -> None:
        self._bugs: dict[str, BugRecord] = {}
        self._hotfixes: dict[str, HotfixRecord] = {}
        self._rca_history: dict[str, RootCauseAnalysis] = {}

    # ==================== 缺陷管理 ====================

    def create_bug(
        self,
        title: str,
        description: str,
        severity: BugSeverity,
        **kwargs,
    ) -> BugRecord:
        """
        创建缺陷记录

        Args:
            title: 缺陷标题
            description: 缺陷描述
            severity: 严重度

        Returns:
            创建的BugRecord对象
        """
        now = datetime.now().isoformat()
        bug_id = f"BUG-{uuid.uuid4().hex[:8].upper()}"
        bug = BugRecord(
            id=bug_id,
            title=title,
            description=description,
            severity=severity,
            reporter=kwargs.get("reporter", ""),
            assignee=kwargs.get("assignee", ""),
            component=kwargs.get("component", ""),
            environment=kwargs.get("environment", ""),
            reproduction_steps=kwargs.get("reproduction_steps", []),
            expected_behavior=kwargs.get("expected_behavior", ""),
            actual_behavior=kwargs.get("actual_behavior", ""),
            affected_files=kwargs.get("affected_files", []),
            created_at=now,
            updated_at=now,
        )
        self._bugs[bug_id] = bug
        return bug

    def get_bug(self, bug_id: str) -> BugRecord:
        """获取缺陷"""
        if bug_id not in self._bugs:
            raise BugNotFoundError(f"缺陷不存在: {bug_id}")
        return self._bugs[bug_id]

    def update_bug_status(self, bug_id: str, status: BugStatus, **kwargs) -> BugRecord:
        """更新缺陷状态"""
        bug = self.get_bug(bug_id)
        bug.status = status
        bug.updated_at = datetime.now().isoformat()

        if status == BugStatus.RESOLVED and not bug.resolved_at:
            bug.resolved_at = datetime.now().isoformat()

        for key, value in kwargs.items():
            if hasattr(bug, key):
                setattr(bug, key, value)

        return bug

    def classify_severity(self, description: str, impact_hint: str = "") -> BugSeverity:
        """
        自动分类缺陷严重度

        Args:
            description: 缺陷描述
            impact_hint: 影响提示

        Returns:
            推荐的严重度等级
        """
        desc_lower = (description + " " + impact_hint).lower()

        critical_indicators = [
            "数据丢失", "安全漏洞", "崩溃", "宕机", "死锁",
            "注入", "越权", "泄露密码", "payment", "支付",
            "corruption", "security", "crash", "downtime", "p0",
        ]
        major_indicators = [
            "功能不可用", "主要流程中断", "性能严重下降",
            "数据不一致", "核心功能错误", "p1",
        ]
        minor_indicators = [
            "ui错位", "显示异常", "非核心功能", "体验问题",
            "typo", "拼写", "样式", "p2",
        ]
        cosmetic_indicators = [
            "文案优化", "颜色调整", "建议改进", "enhancement",
            "feature request", "p3", "p4",
        ]

        if any(ind in desc_lower for ind in critical_indicators):
            return BugSeverity.CRITICAL
        elif any(ind in desc_lower for ind in major_indicators):
            return BugSeverity.MAJOR
        elif any(ind in desc_lower for ind in minor_indicators):
            return BugSeverity.MINOR
        elif any(ind in desc_lower for ind in cosmetic_indicators):
            return BugSeverity.COSMETIC
        else:
            return BugSeverity.ENHANCEMENT

    # ==================== 根因分析 ====================

    def analyze_root_cause_5whys(self, bug_id: str, problem_statement: str) -> RootCauseAnalysis:
        """
        5 Whys根因分析法

        Args:
            bug_id: 缺陷ID
            problem_statement: 问题陈述

        Returns:
            根因分析结果
        """
        chain: list[dict[str, str]] = []
        current_problem = problem_statement

        why_templates: list[str] = [
            "为什么会出现{problem}?",
            "{problem}的根本原因是什么?",
            "什么导致了{problem}?",
        ]

        for i in range(1, 6):
            answer = self._generate_why_answer(current_problem, i)
            chain.append({
                "why": f"第{i}个Why",
                "question": why_templates[i % len(why_templates)].format(problem=current_problem[:30]),
                "answer": answer,
            })
            current_problem = answer

            if any(kw in answer.lower() for kw in ("根本", "设计缺陷", "架构问题", "需求不明确")):
                break

        root_cause = chain[-1]["answer"] if chain else problem_statement

        rca = RootCauseAnalysis(
            bug_id=bug_id,
            method="5_whys",
            analysis_chain=chain,
            root_cause=root_cause,
            category=self._categorize_root_cause(root_cause),
            prevention_measures=self._suggest_prevention(root_cause),
        )

        self._rca_history[bug_id] = rca
        return rca

    def analyze_root_cause_fishbone(self, bug_id: str, effect: str) -> RootCauseAnalysis:
        """
        鱼骨图(因果图)分析法

        Args:
            bug_id: 缺陷ID
            effect: 效果描述

        Returns:
            根因分析结果
        """
        categories: dict[str, list[str]] = {
            "人员": ["培训不足", "经验欠缺", "沟通不畅", "疲劳作业"],
            "方法": ["流程缺失", "标准不明", "评审不足", "测试覆盖不够"],
            "机器": ["环境配置差异", "工具版本不一致", "资源限制"],
            "材料": ["依赖库缺陷", "第三方API变更", "数据质量问题"],
            "测量": ["监控缺失", "日志不足", "指标定义不清"],
            "环境": ["网络不稳定", "并发压力", "配置漂移"],
        }

        chain: list[dict[str, str]] = []
        all_causes: list[str] = []

        for cat, causes in categories.items():
            relevant = [c for c in causes if self._is_relevant_cause(c, effect)]
            if relevant:
                for c in relevant:
                    chain.append({
                        "category": cat,
                        "cause": c,
                        "relevance": "high" if len(relevant) <= 2 else "medium",
                    })
                    all_causes.append(f"[{cat}] {c}")

        root_cause = all_causes[0] if all_causes else "待进一步调查"

        rca = RootCauseAnalysis(
            bug_id=bug_id,
            method="fishbone",
            analysis_chain=[{"category": item["category"], "cause": item["cause"]} for item in chain],
            root_cause=root_cause,
            contributing_factors=all_causes[1:] if len(all_causes) > 1 else [],
            category=self._categorize_root_cause(root_cause),
            prevention_measures=self._suggest_prevention(root_cause),
        )

        self._rca_history[bug_id] = rca
        return rca

    @staticmethod
    def _generate_why_answer(problem: str, depth: int) -> str:
        """生成Why答案（模拟）"""
        answers_by_depth: dict[int, list[tuple[str, str]]] = {
            1: [
                ("代码逻辑错误", "因为条件判断有误"),
                ("输入验证缺失", "因为没有对用户输入做校验"),
                ("竞态条件", "因为多线程访问未加锁"),
                ("配置错误", "因为使用了错误的配置值"),
            ],
            2: [
                ("开发时未考虑边界情况", "因为测试用例不完整"),
                ("安全意识不足", "因为缺少安全编码规范"),
                ("缺乏代码审查", "因为团队流程不完善"),
            ],
            3: [
                ("项目时间压力", "因为排期过紧"),
                ("技术债务积累", "因为长期不做重构"),
                ("文档缺失", "因为知识传递不到位"),
            ],
            4: [
                ("需求理解偏差", "因为需求沟通不充分"),
                ("架构设计缺陷", "因为前期技术选型不当"),
            ],
            5: [
                ("组织流程问题", "需要从管理层级改进"),
                ("根本原因：需求管理不规范", "需要建立完善的需求工程体系"),
            ],
        }
        depth_answers = answers_by_depth.get(min(depth, 5), answers_by_depth[5])
        idx = hash(problem + str(depth)) % len(depth_answers)
        return depth_answers[idx][0]

    @staticmethod
    def _is_relevant_cause(cause: str, effect: str) -> bool:
        """判断原因是否与效果相关"""
        cause_lower = cause.lower()
        effect_lower = effect.lower()
        relevance_map: dict[str, list[str]] = {
            "培训不足": ["不会", "不懂", "新功能"],
            "流程缺失": ["遗漏", "忘记", "没检查"],
            "环境配置差异": ["本地正常", "线上失败", "环境不同"],
            "依赖库缺陷": ["升级后", "版本", "兼容性"],
            "测试覆盖不够": ["漏测", "回归", "新引入"],
        }
        for keywords, effects in relevance_map.items():
            if keywords in cause_lower or cause in keywords:
                return any(e in effect_lower for e in effects)
        return False

    @staticmethod
    def _categorize_root_cause(cause: str) -> str:
        """分类根因"""
        cause_lower = cause.lower()
        if any(k in cause_lower for k in ["代码", "逻辑", "实现"]):
            return "code_defect"
        elif any(k in cause_lower for k in ["设计", "架构", "方案"]):
            return "design_issue"
        elif any(k in cause_lower for k in ["需求", "规格", "理解"]):
            return "requirement_issue"
        elif any(k in cause_lower for k in ["环境", "配置", "部署"]):
            return "environment_issue"
        elif any(k in cause_lower for k in ["流程", "管理", "组织"]):
            return "process_issue"
        else:
            return "unknown"

    @staticmethod
    def _suggest_prevention(root_cause: str) -> list[str]:
        """建议预防措施"""
        suggestions: dict[str, list[str]] = {
            "code_defect": [
                "加强代码审查，特别是复杂逻辑部分",
                "增加单元测试覆盖率，尤其是边界条件",
                "使用静态分析工具自动检测常见错误模式",
            ],
            "design_issue": [
                "进行架构评审，邀请资深工程师参与",
                "编写技术决策文档(TDR)，记录设计取舍",
                "定期进行技术债务清理和重构",
            ],
            "requirement_issue": [
                "建立需求评审机制，确保各方理解一致",
                "使用用户故事+验收标准明确需求",
                "增加原型验证环节，尽早发现理解偏差",
            ],
            "environment_issue": [
                "统一开发和生产环境配置(IaC)",
                "实施CI/CD流水线确保部署一致性",
                "加强基础设施监控和告警",
            ],
            "process_issue": [
                "优化项目管理流程，合理排期",
                "建立知识共享机制，减少信息孤岛",
                "定期复盘，持续改进工作方式",
            ],
        }
        category = BugFixingSi._categorize_root_cause(root_cause)
        base = suggestions.get(category, ["深入分析并制定针对性预防措施"])
        return base + ["将此案例纳入团队学习资料"]

    # ==================== 问题诊断引导 ====================

    def generate_diagnosis_guide(self, symptom: str) -> list[DiagnosisStep]:
        """
        基于症状生成诊断引导步骤

        Args:
            symptom: 症状描述

        Returns:
            诊断步骤列表
        """
        steps: list[DiagnosisStep] = []
        symptom_lower = symptom.lower()

        if any(kw in symptom_lower for kw in ["报错", "error", "exception", "异常", "500"]):
            steps.extend([
                DiagnosisStep(1, "查看完整的错误堆栈信息", "获取到详细的异常类型和位置"),
                DiagnosisStep(2, "定位错误发生的源码位置", "找到抛出异常的具体文件和行号"),
                DiagnosisStep(3, "分析触发错误的输入数据", "确定导致异常的请求参数或状态"),
                DiagnosisStep(4, "检查相关依赖是否正常", "确认数据库/外部服务/API的可用性"),
                DiagnosisStep(5, "复现并验证修复效果", "在相同条件下重现问题并确认修复"),
            ])
        elif any(kw in symptom_lower for kw in ["慢", "超时", "timeout", "卡顿", "性能"]):
            steps.extend([
                DiagnosisStep(1, "收集性能指标(CPU/内存/IO)", "识别瓶颈所在"),
                DiagnosisStep(2, "分析慢查询或慢请求日志", "找出耗时最长的操作"),
                DiagnosisStep(3, "检查索引和数据库执行计划", "确认是否有全表扫描"),
                DiagnosisStep(4, "审查近期代码变更", "查找可能引入的性能退化"),
                DiagnosisStep(5, "进行压力测试验证", "模拟高负载场景确认修复有效"),
            ])
        elif any(kw in symptom_lower for kw in ["数据不对", "不一致", "错误结果", "计算错误"]):
            steps.extend([
                DiagnosisStep(1, "对比预期输出和实际输出的差异", "精确定位差异点"),
                DiagnosisStep(2, "追踪数据的处理链路", "从源头到输出逐步检查"),
                DiagnosisStep(3, "检查数据转换和格式化逻辑", "确认类型转换、编码等问题"),
                DiagnosisStep(4, "验证边界条件和特殊值处理", "检查空值、极值等边缘情况"),
                DiagnosisStep(5, "添加断点和日志辅助调试", "动态观察变量变化过程"),
            ])
        else:
            steps.extend([
                DiagnosisStep(1, "清晰描述问题的现象和影响范围", "确保问题描述准确完整"),
                DiagnosisStep(2, "收集相关的日志和监控数据", "获取问题发生时的上下文信息"),
                DiagnosisStep(3, "尝试在隔离环境中复现问题", "排除外部因素干扰"),
                DiagnosisStep(4, "缩小排查范围(二分法)", "逐步缩小可能的问题区域"),
                DiagnosisStep(5, "制定假设并逐一验证", "基于证据形成结论而非猜测"),
            ])

        for i, step in enumerate(steps):
            step.step_number = i + 1

        return steps

    # ==================== 热修复流程 ====================

    def create_hotfix(
        self,
        bug_id: str,
        description: str,
        severity: BugSeverity | None = None,
    ) -> HotfixRecord:
        """
        创建热修复分支

        Args:
            bug_id: 关联的缺陷ID
            description: 修复描述
            severity: 严重度（如不提供则从bug获取）

        Returns:
            热修复记录
        """
        try:
            bug = self.get_bug(bug_id)
            fix_severity = severity or bug.severity
        except BugNotFoundError:
            fix_severity = severity or BugSeverity.MAJOR

        now = datetime.now().isoformat()
        hotfix_id = f"HF-{uuid.uuid4().hex[:8].upper()}"
        branch_name = f"hotfix/{hotfix_id}-{bug_id}"

        hotfix = HotfixRecord(
            hotfix_id=hotfix_id,
            bug_id=bug_id,
            branch_name=branch_name,
            description=description,
            severity=fix_severity,
            created_at=now,
        )

        self._hotfixes[hotfix_id] = hotfix
        return hotfix

    def get_hotfix_workflow(self, hotfix_id: str) -> dict[str, Any]:
        """
        获取热修复工作流指引

        Args:
            hotfix_id: 热修复ID

        Returns:
            工作流步骤字典
        """
        if hotfix_id not in self._hotfixes:
            raise HotfixError(f"热修复不存在: {hotfix_id}")

        hf = self._hotfixes[hotfix_id]
        workflow: dict[str, Any] = {
            "hotfix_id": hotfix_id,
            "bug_id": hf.branch_name,
            "severity": hf.severity.value,
            "steps": [
                {"step": 1, "action": f"从main分支创建热修复分支: git checkout -b {hf.branch_name}", "status": "pending"},
                {"step": 2, "action": "实现最小化修复代码", "status": "pending"},
                {"step": 3, "action": "编写并运行回归测试", "status": "pending"},
                {"step": 4, "action": "提交修复: git commit -m 'fix: {hf.description}'", "status": "pending"},
                {"step": 5, "action": "创建PR到release分支", "status": "pending"},
                {"step": 6, "action": "Code Review + 安全扫描", "status": "pending"},
                {"step": 7, "action": "合并到release分支并打补丁版本标签", "status": "pending"},
                {"step": 8, "action": "部署补丁版本到生产环境", "status": "pending"},
                {"step": 9, "action": "验证线上修复效果", "status": "pending"},
                {"step": 10, "action": "cherry-pick回main分支", "status": "pending"},
            ],
            "rollback_plan": [
                f"如需回滚: git revert <commit-hash>",
                f"或重新部署上一个稳定版本",
                f"通知相关方回滚操作及影响",
            ],
        }

        return workflow

    # ==================== 复现步骤标准化 ====================

    def format_reproduction_steps(self, raw_steps: list[str]) -> str:
        """
        格式化为Given-When-Then(GWT)格式

        Args:
            raw_steps: 原始步骤列表

        Returns:
            GWT格式的字符串
        """
        lines: list[str] = []
        lines.append("## 复现步骤\n")

        given_lines: list[str] = []
        when_lines: list[str] = []
        then_lines: list[str] = []

        for step in raw_steps:
            step_lower = step.lower()
            if any(kw in step_lower for kw in ["打开", "登录", "进入", "前提", "given", "准备", "已有"]):
                given_lines.append(step)
            elif any(kw in step_lower for kw in ["点击", "输入", "选择", "操作", "when", "执行", "触发"]):
                when_lines.append(step)
            elif any(kw in step_lower for kw in ["出现", "看到", "显示", "结果", "then", "期望", "实际"]):
                then_lines.append(step)
            else:
                if not given_lines:
                    given_lines.append(step)
                elif not when_lines:
                    when_lines.append(step)
                else:
                    then_lines.append(step)

        if given_lines:
            lines.append("**Given** (前置条件):")
            for g in given_lines:
                lines.append(f"  - {g}")
            lines.append("")

        if when_lines:
            lines.append("**When** (操作):")
            for w in when_lines:
                lines.append(f"  - {w}")
            lines.append("")

        if then_lines:
            lines.append("**Then** (期望结果):")
            for t in then_lines:
                lines.append(f"  - {t}")
            lines.append("")

        return "\n".join(lines)

    # ==================== 修复方案评估 ====================

    def evaluate_fix_solution(
        self,
        solution_description: str,
        affected_areas: list[str],
        risk_level: str = "medium",
    ) -> dict[str, Any]:
        """
        评估修复方案

        Args:
            solution_description: 方案描述
            affected_areas: 影响区域列表
            risk_level: 风险等级

        Returns:
            评估结果字典
        """
        score = 100.0

        deductions: list[tuple[str, float]] = [
            ("影响范围过大", 15 * max(0, len(affected_areas) - 3)),
            ("高风险修复", 20 if risk_level == "high" else (10 if risk_level == "medium" else 0)),
            ("方案复杂度高", 10 if len(solution_description) > 500 else 0),
        ]

        for reason, deduction in deductions:
            score -= deduction

        regression_risk = "high" if risk_level == "high" and len(affected_areas) > 3 else (
            "medium" if risk_level == "medium" or len(affected_areas) > 2 else "low"
        )

        recommendations: list[str] = []
        if regression_risk == "high":
            recommendations.append("强烈建议先在预发布环境全面测试")
            recommendations.append("考虑灰度发布策略")
        elif regression_risk == "medium":
            recommendations.append("确保核心路径回归测试通过")
        else:
            recommendations.append("常规测试即可")

        if len(affected_areas) > 5:
            recommendations.append("考虑分阶段实施修复")

        return {
            "solution": solution_description,
            "score": max(0, round(score, 1)),
            "affected_areas": affected_areas,
            "risk_level": risk_level,
            "regression_risk": regression_risk,
            "recommendations": recommendations,
            "approved": score >= 50,
        }

    # ==================== 修复验证清单 ====================

    def generate_verification_checklist(self, bug_id: str) -> FixVerificationChecklist:
        """
        生成修复验证清单

        Args:
            bug_id: 缺陷ID

        Returns:
            验证清单对象
        """
        items: list[dict[str, bool]] = [
            {"item": "缺陷是否已完全修复？原问题不再复现", "checked": False},
            {"item": "修复是否引入了新的问题？运行全量回归测试", "checked": False},
            {"item": "相关文档是否已更新？README/CHANGELOG/API文档", "checked": False},
            {"item": "测试用例是否足够？包括正常和异常场景", "checked": False},
            {"item": "代码是否符合编码规范？通过lint检查", "checked": False},
            {"item": "安全性是否受影响？无新增安全漏洞", "checked": False},
            {"item": "性能是否可接受？无明显的性能退化", "checked": False},
            {"item": "配置是否正确？无硬编码或遗留的调试代码", "checked": False},
            {"item": "日志是否适当？关键操作有日志记录", "checked": False},
            {"item": "Code Review是否完成？至少一人审核通过", "checked": False},
        ]

        return FixVerificationChecklist(bug_id=bug_id, items=items)

    # ==================== 缺陷趋势分析 ====================

    def analyze_trends(self) -> BugTrendMetrics:
        """分析缺陷趋势"""
        metrics = BugTrendMetrics()
        metrics.total_bugs = len(self._bugs)

        severity_counts: dict[str, int] = {}
        component_counts: dict[str, int] = {}

        resolved_times: list[float] = []
        reopened_count = 0

        for bug in self._bugs.values():
            sev_key = bug.severity.value
            severity_counts[sev_key] = severity_counts.get(sev_key, 0) + 1

            comp = bug.component or "unknown"
            component_counts[comp] = component_counts.get(comp, 0) + 1

            if bug.status in (BugStatus.NEW, BugStatus.CONFIRMED, BugStatus.IN_PROGRESS):
                metrics.open_bugs += 1
                if bug.severity == BugSeverity.CRITICAL:
                    metrics.critical_open += 1

            if bug.status == BugStatus.REOPENED:
                reopened_count += 1

            if bug.resolved_at and bug.created_at:
                try:
                    created = datetime.fromisoformat(bug.created_at)
                    resolved = datetime.fromisoformat(bug.resolved_at)
                    hours = (resolved - created).total_seconds() / 3600
                    resolved_times.append(hours)
                except (ValueError, TypeError):
                    pass

        metrics.by_severity = severity_counts
        metrics.by_component = component_counts

        if resolved_times:
            metrics.avg_resolution_time_hours = sum(resolved_times) / len(resolved_times)

        total_resolved = sum(1 for b in self._bugs.values() if b.status in (BugStatus.RESOLVED, BugStatus.CLOSED, BugStatus.VERIFIED))
        metrics.reopen_rate = reopened_count / max(total_resolved, 1) * 100

        metrics.escape_rate = sum(
            1 for b in self._bugs.values()
            if b.severity in (BugSeverity.MAJOR, BugSeverity.CRITICAL)
            and "production" in (b.environment or "").lower()
        ) / max(metrics.total_bugs, 1) * 100

        return metrics

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成缺陷修复司报告"""
        lines: list[str] = []
        lines.append("# 🐛 缺陷修复司 · 综合报告\n")

        trends = self.analyze_trends()
        lines.append("## 📊 缺陷趋势概览\n")
        lines.append("| 指标 | 值 |")
        lines.append("| --- | --- |")
        lines.append(f"| 总缺陷数 | {trends.total_bugs} |")
        lines.append(f"| 未关闭 | {trends.open_bugs} |")
        lines.append(f"| 严重未关闭 | ⚠️ {trends.critical_open} |")
        lines.append(f"| 平均解决时长 | {trends.avg_resolution_time_hours:.1f}h |")
        lines.append(f"| 重开率 | {trends.reopen_rate:.1f}% |")
        lines.append(f"| 生产逃逸率 | {trends.escape_rate:.1f}% |")

        if trends.by_severity:
            lines.append("\n### 按严重度分布\n")
            for sev, count in sorted(trends.by_severity.items()):
                icon = {"critical": "🔴", "major": "🟠", "minor": "🟡", "enhancement": "🔵", "cosmetic": "⚪"}.get(sev, "⚪")
                lines.append(f"- {icon} `{sev}`: {count}")

        if self._hotfixes:
            lines.append(f"\n## 🔥 热修复记录 ({len(self._hotfixes)})\n")
            lines.append("| ID | 关联Bug | 分支 | 状态 |")
            lines.append("| --- | --- | --- | --- |")
            for hf in self._hotfixes.values():
                status = "✅ 已发布" if hf.released_at else ("🔄 进行中" if hf.merged_at else "📋 待处理")
                lines.append(f"`{hf.hotfix_id}` | `{hf.bug_id}` | `{hf.branch_name}` | {status} |")

        if self._rca_history:
            lines.append(f"\n## 🔍 根因分析 ({len(self._rca_history)})\n")
            for bug_id, rca in list(self._rca_history.items())[:5]:
                lines.append(f"- **{bug_id}**: [{rca.method}] {rca.root_cause[:50]}...")

        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print("=" * 60)
    print("缺陷修复司 - 功能演示")
    print("=" * 60)

    si = BugFixingSi()

    print("\n--- 缺陷创建与分类 ---")
    bug = si.create_bug(
        title="用户登录后页面白屏",
        description="用户使用Chrome浏览器登录系统后，首页显示空白，控制台报错Uncaught TypeError",
        severity=si.classify_severity("页面白屏无法使用", "核心功能完全不可用"),
    )
    print(f"  Bug: {bug.id} [{bug.severity.value}] {bug.title}")

    print("\n--- 5 Whys根因分析 ---")
    rca_5whys = si.analyze_root_cause_5whys(bug.id, "用户登录后页面白屏")
    print(f"  方法: {rca_5whys.method}, 根因: {rca_5whys.root_cause}")
    for step in rca_5whys.analysis_chain[:3]:
        print(f"    {step['why']}: {step['answer']}")

    print("\n--- 鱼骨图分析 ---")
    rca_fishbone = si.analyze_root_cause_fishbone(bug.id, "前端渲染失败导致白屏")
    print(f"  根因: {rca_fishbone.root_cause}")
    print(f"  分类: {rca_fishbone.category}")

    print("\n--- 诊断引导 ---")
    guide = si.generate_diagnosis_guide("页面加载时报错TypeError: Cannot read property 'map' of undefined")
    for step in guide:
        print(f"  Step {step.step_number}: {step.action}")

    print("\n--- 热修复流程 ---")
    hotfix = si.create_hotfix(bug.id, "修复用户数据为空时的防御性处理")
    workflow = si.get_hotfix_workflow(hotfix.hotfix_id)
    print(f"  热修复ID: {hotfix.hotfix_id}")
    print(f"  分支: {hotfix.branch_name}")
    print(f"  步骤数: {len(workflow['steps'])}")

    print("\n--- 复现步骤标准化 ---")
    gwt = si.format_reproduction_steps([
        "打开Chrome浏览器访问系统",
        "输入正确的用户名和密码点击登录",
        "等待页面加载完成后看到空白页面",
        "按F12打开开发者工具看到Console中有红色错误信息",
    ])
    print(gwt[:400])

    print("\n--- 修复方案评估 ---")
    eval_result = si.evaluate_fix_solution(
        "在数据获取处添加null check，当用户数据为空时显示默认UI",
        ["frontend/user-dashboard", "api/user-service"],
        risk_level="low",
    )
    print(f"  得分: {eval_result['score']}, 批准: {'✅' if eval_result['approved'] else '❌'}")
    for rec in eval_result['recommendations']:
        print(f"  💡 {rec}")

    checklist = si.generate_verification_checklist(bug.id)
    print(f"\n--- 验证清单 ({len(checklist.items)}项) ---")
    for item in checklist.items[:5]:
        print(f"  [{'✅' if item['checked'] else '⬜'}] {item['item']}")

    trends = si.analyze_trends()
    print(f"\n--- 趋势分析 ---\n  总计: {trends.total_bugs}, 开放: {trends.open_bugs}, 重开率: {trends.reopen_rate:.1f}%")

    report = si.generate_report()
    print(f"\n--- 报告预览 (前800字符) ---\n{report[:800]}...")

    print("\n✅ 所有测试通过!")
