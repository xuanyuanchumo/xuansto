#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构建议生成器

TDD蓝阶段 - 智能重构建议生成
基于代码异味分析结果，生成：
- 重构建议列表
- 优先级排序
- 重构计划
- 预估工作量

使用示例:
    python refactoring_suggestion_generator.py
    python refactoring_suggestion_generator.py --input code_smell_detection_latest.json
    python refactoring_suggestion_generator.py --priority high
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class Priority(Enum):
    """重构优先级"""
    P0_CRITICAL = "p0_critical"
    P1_HIGH = "p1_high"
    P2_MEDIUM = "p2_medium"
    P3_LOW = "p3_low"


class RefactoringType(Enum):
    """重构类型"""
    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    EXTRACT_INTERFACE = "extract_interface"
    INLINE_METHOD = "inline_method"
    INLINE_CLASS = "inline_class"
    MOVE_METHOD = "move_method"
    MOVE_FIELD = "move_field"
    RENAME_METHOD = "rename_method"
    RENAME_CLASS = "rename_class"
    ENCAPSULATE_FIELD = "encapsulate_field"
    INTRODUCE_PARAMETER_OBJECT = "introduce_parameter_object"
    REPLACE_COND_WITH_POLYMORPHISM = "replace_conditional_with_polymorphism"
    REPLACE_NESTED_COND_WITH_GUARD = "replace_nested_conditional_with_guard"
    DECOMPOSE_CONDITIONAL = "decompose_conditional"
    CONSOLIDATE_DUPLICATE = "consolidate_duplicate"
    PULL_UP_METHOD = "pull_up_method"
    PUSH_DOWN_METHOD = "push_down_method"
    EXTRACT_SUBCLASS = "extract_subclass"
    FORM_TEMPLATE_METHOD = "form_template_method"


class EffortLevel(Enum):
    """工作量级别"""
    TRIVIAL = "trivial"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    VERY_LARGE = "very_large"


@dataclass
class RefactoringSuggestion:
    """重构建议"""
    id: str
    refactoring_type: RefactoringType
    priority: Priority
    file_path: str
    line_start: int
    line_end: int
    title: str
    description: str
    rationale: str
    steps: List[str] = field(default_factory=list)
    code_example: str = ""
    effort: EffortLevel = EffortLevel.MEDIUM
    estimated_minutes: int = 30
    impact_score: float = 0.0
    risk_level: str = "low"
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "refactoring_type": self.refactoring_type.value,
            "priority": self.priority.value,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "steps": self.steps,
            "code_example": self.code_example,
            "effort": self.effort.value,
            "estimated_minutes": self.estimated_minutes,
            "impact_score": self.impact_score,
            "risk_level": self.risk_level,
            "dependencies": self.dependencies,
            "tags": self.tags
        }


@dataclass
class RefactoringPlan:
    """重构计划"""
    id: str
    name: str
    description: str
    suggestions: List[RefactoringSuggestion]
    total_effort_minutes: int
    phases: List[Dict[str, Any]] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "total_effort_minutes": self.total_effort_minutes,
            "phases": self.phases,
            "prerequisites": self.prerequisites
        }


@dataclass
class GenerationReport:
    """生成报告"""
    timestamp: str
    project_root: str
    total_suggestions: int
    suggestions: List[RefactoringSuggestion]
    plans: List[RefactoringPlan]
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project_root": self.project_root,
            "total_suggestions": self.total_suggestions,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "plans": [p.to_dict() for p in self.plans],
            "summary": self.summary
        }


class RefactoringPatternLibrary:
    """重构模式库"""

    PATTERNS = {
        "long_method": {
            "type": RefactoringType.EXTRACT_METHOD,
            "title": "提取方法",
            "description": "将长方法分解为多个小方法",
            "rationale": "长方法难以理解和维护，提取方法可以提高代码可读性和复用性",
            "steps": [
                "1. 识别方法中的独立功能块",
                "2. 为功能块创建新方法",
                "3. 将相关代码移动到新方法",
                "4. 在原方法中调用新方法",
                "5. 运行测试确保行为不变"
            ],
            "effort": EffortLevel.SMALL,
            "estimated_minutes": 30,
            "risk": "low"
        },
        "large_class": {
            "type": RefactoringType.EXTRACT_CLASS,
            "title": "提取类",
            "description": "将大类拆分为多个小类",
            "rationale": "大类违反单一职责原则，拆分可以提高内聚性",
            "steps": [
                "1. 分析类的职责",
                "2. 识别可以分离的功能",
                "3. 创建新类",
                "4. 移动相关字段和方法",
                "5. 更新引用",
                "6. 运行测试验证"
            ],
            "effort": EffortLevel.MEDIUM,
            "estimated_minutes": 60,
            "risk": "medium"
        },
        "long_parameter_list": {
            "type": RefactoringType.INTRODUCE_PARAMETER_OBJECT,
            "title": "引入参数对象",
            "description": "将多个参数封装为对象",
            "rationale": "长参数列表难以维护，参数对象可以提高代码清晰度",
            "steps": [
                "1. 识别经常一起出现的参数",
                "2. 创建参数对象类",
                "3. 将参数添加到新类",
                "4. 更新方法签名",
                "5. 更新调用代码"
            ],
            "effort": EffortLevel.SMALL,
            "estimated_minutes": 20,
            "risk": "low"
        },
        "deep_nesting": {
            "type": RefactoringType.REPLACE_NESTED_COND_WITH_GUARD,
            "title": "使用卫语句替代嵌套条件",
            "description": "简化深度嵌套的条件逻辑",
            "rationale": "深度嵌套降低代码可读性，卫语句可以提前返回简化逻辑",
            "steps": [
                "1. 识别嵌套条件",
                "2. 将条件反转",
                "3. 添加提前返回语句",
                "4. 移除嵌套层级",
                "5. 验证逻辑正确性"
            ],
            "effort": EffortLevel.SMALL,
            "estimated_minutes": 25,
            "risk": "low"
        },
        "high_complexity": {
            "type": RefactoringType.DECOMPOSE_CONDITIONAL,
            "title": "分解条件表达式",
            "description": "简化复杂的条件逻辑",
            "rationale": "复杂条件难以理解，分解可以提高可读性",
            "steps": [
                "1. 提取条件为独立方法",
                "2. 为条件方法命名",
                "3. 简化主逻辑",
                "4. 考虑使用策略模式"
            ],
            "effort": EffortLevel.MEDIUM,
            "estimated_minutes": 45,
            "risk": "medium"
        },
        "duplicate_code": {
            "type": RefactoringType.CONSOLIDATE_DUPLICATE,
            "title": "合并重复代码",
            "description": "提取重复代码到公共方法",
            "rationale": "重复代码增加维护成本，合并可以提高复用性",
            "steps": [
                "1. 识别重复代码块",
                "2. 分析差异",
                "3. 创建公共方法",
                "4. 使用参数处理差异",
                "5. 替换重复代码"
            ],
            "effort": EffortLevel.SMALL,
            "estimated_minutes": 20,
            "risk": "low"
        },
        "switch_statements": {
            "type": RefactoringType.REPLACE_COND_WITH_POLYMORPHISM,
            "title": "使用多态替代条件",
            "description": "使用多态替代switch/if-else链",
            "rationale": "switch语句难以扩展，多态提供更好的扩展性",
            "steps": [
                "1. 创建抽象基类或接口",
                "2. 为每种情况创建子类",
                "3. 将行为移到子类",
                "4. 使用工厂方法创建实例",
                "5. 移除switch语句"
            ],
            "effort": EffortLevel.LARGE,
            "estimated_minutes": 90,
            "risk": "medium"
        },
        "data_clumps": {
            "type": RefactoringType.INTRODUCE_PARAMETER_OBJECT,
            "title": "提取数据类",
            "description": "将经常一起出现的数据封装为类",
            "rationale": "数据泥团表明存在潜在的概念，提取可以提高语义清晰度",
            "steps": [
                "1. 识别数据泥团",
                "2. 创建数据类",
                "3. 添加相关方法",
                "4. 更新使用处"
            ],
            "effort": EffortLevel.SMALL,
            "estimated_minutes": 30,
            "risk": "low"
        }
    }

    @classmethod
    def get_pattern(cls, smell_type: str) -> Optional[Dict[str, Any]]:
        return cls.PATTERNS.get(smell_type)

    @classmethod
    def get_all_patterns(cls) -> Dict[str, Dict[str, Any]]:
        return cls.PATTERNS


class RefactoringSuggestionGenerator:
    """重构建议生成器"""

    def __init__(self, project_root: Optional[Path] = None,
                 logger: Optional[logging.Logger] = None):
        self.project_root = project_root or get_path_config().SKILL_ROOT
        self.logger = logger or logging.getLogger(__name__)
        self.suggestions: List[RefactoringSuggestion] = []
        self.plans: List[RefactoringPlan] = []
        self.suggestion_counter = 0

    def generate_from_smell_report(self, smell_report_path: Path) -> GenerationReport:
        """从代码异味报告生成重构建议"""
        self.logger.info(f"从报告生成重构建议: {smell_report_path}")

        with open(smell_report_path, 'r', encoding='utf-8') as f:
            smell_data = json.load(f)

        return self._generate_from_data(smell_data)

    def generate_from_smell_data(self, smell_data: Dict[str, Any]) -> GenerationReport:
        """从代码异味数据生成重构建议"""
        return self._generate_from_data(smell_data)

    def _generate_from_data(self, smell_data: Dict[str, Any]) -> GenerationReport:
        """从数据生成重构建议"""
        self.suggestions = []
        self.plans = []

        file_results = smell_data.get("file_results", [])

        for file_result in file_results:
            file_path = file_result.get("file_path", "")
            smells = file_result.get("smells", [])

            for smell in smells:
                suggestion = self._create_suggestion(file_path, smell)
                if suggestion:
                    self.suggestions.append(suggestion)

        self._sort_suggestions_by_priority()
        self._calculate_impact_scores()

        self._generate_refactoring_plans()

        summary = self._calculate_summary()

        return GenerationReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            total_suggestions=len(self.suggestions),
            suggestions=self.suggestions,
            plans=self.plans,
            summary=summary
        )

    def _create_suggestion(self, file_path: str, smell: Dict[str, Any]) -> Optional[RefactoringSuggestion]:
        """创建重构建议"""
        smell_type = smell.get("smell_type", "")
        pattern = RefactoringPatternLibrary.get_pattern(smell_type)

        if not pattern:
            return None

        self.suggestion_counter += 1
        suggestion_id = f"REF-{self.suggestion_counter:04d}"

        severity = smell.get("severity", "medium")
        priority = self._map_severity_to_priority(severity)

        metrics = smell.get("metrics", {})

        title = pattern["title"]
        description = self._customize_description(pattern["description"], smell)
        rationale = pattern["rationale"]

        steps = pattern["steps"].copy()

        code_example = self._generate_code_example(smell_type, smell)

        effort = pattern["effort"]
        estimated_minutes = pattern["estimated_minutes"]

        if metrics:
            if smell_type == "long_method":
                lines = metrics.get("lines", 50)
                if lines > 100:
                    effort = EffortLevel.MEDIUM
                    estimated_minutes = 60
                elif lines > 150:
                    effort = EffortLevel.LARGE
                    estimated_minutes = 90

        risk_level = pattern.get("risk", "low")

        tags = [smell_type, smell.get("category", ""), severity]

        return RefactoringSuggestion(
            id=suggestion_id,
            refactoring_type=pattern["type"],
            priority=priority,
            file_path=file_path,
            line_start=smell.get("line_start", 0),
            line_end=smell.get("line_end", 0),
            title=title,
            description=description,
            rationale=rationale,
            steps=steps,
            code_example=code_example,
            effort=effort,
            estimated_minutes=estimated_minutes,
            risk_level=risk_level,
            tags=tags
        )

    def _map_severity_to_priority(self, severity: str) -> Priority:
        """映射严重程度到优先级"""
        mapping = {
            "critical": Priority.P0_CRITICAL,
            "high": Priority.P1_HIGH,
            "medium": Priority.P2_MEDIUM,
            "low": Priority.P3_LOW,
            "info": Priority.P3_LOW
        }
        return mapping.get(severity, Priority.P2_MEDIUM)

    def _customize_description(self, base_description: str, smell: Dict[str, Any]) -> str:
        """自定义描述"""
        metrics = smell.get("metrics", {})
        if metrics:
            details = ", ".join(f"{k}={v}" for k, v in metrics.items() if not isinstance(v, (dict, list)))
            return f"{base_description} ({details})"
        return base_description

    def _generate_code_example(self, smell_type: str, smell: Dict[str, Any]) -> str:
        """生成代码示例"""
        examples = {
            "long_method": """
# Before
def process_data(data):
    # ... 100 lines of code ...

# After
def process_data(data):
    validated_data = validate_data(data)
    transformed_data = transform_data(validated_data)
    return save_data(transformed_data)

def validate_data(data):
    # validation logic
    pass

def transform_data(data):
    # transformation logic
    pass
""",
            "deep_nesting": """
# Before
def process(item):
    if item:
        if item.valid:
            if item.ready:
                return process_ready(item)

# After
def process(item):
    if not item:
        return None
    if not item.valid:
        return None
    if not item.ready:
        return None
    return process_ready(item)
""",
            "long_parameter_list": """
# Before
def create_user(name, email, age, address, phone, department):
    pass

# After
@dataclass
class UserParams:
    name: str
    email: str
    age: int
    address: str
    phone: str
    department: str

def create_user(params: UserParams):
    pass
"""
        }
        return examples.get(smell_type, "")

    def _sort_suggestions_by_priority(self):
        """按优先级排序建议"""
        priority_order = {
            Priority.P0_CRITICAL: 0,
            Priority.P1_HIGH: 1,
            Priority.P2_MEDIUM: 2,
            Priority.P3_LOW: 3
        }
        self.suggestions.sort(key=lambda s: priority_order.get(s.priority, 99))

    def _calculate_impact_scores(self):
        """计算影响分数"""
        for suggestion in self.suggestions:
            score = 0.0

            priority_scores = {
                Priority.P0_CRITICAL: 40.0,
                Priority.P1_HIGH: 30.0,
                Priority.P2_MEDIUM: 20.0,
                Priority.P3_LOW: 10.0
            }
            score += priority_scores.get(suggestion.priority, 0)

            effort_scores = {
                EffortLevel.TRIVIAL: 20.0,
                EffortLevel.SMALL: 15.0,
                EffortLevel.MEDIUM: 10.0,
                EffortLevel.LARGE: 5.0,
                EffortLevel.VERY_LARGE: 2.0
            }
            score += effort_scores.get(suggestion.effort, 0)

            risk_scores = {
                "low": 20.0,
                "medium": 10.0,
                "high": 5.0
            }
            score += risk_scores.get(suggestion.risk_level, 10.0)

            suggestion.impact_score = min(100.0, score)

    def _generate_refactoring_plans(self):
        """生成重构计划"""
        critical_suggestions = [s for s in self.suggestions if s.priority == Priority.P0_CRITICAL]
        if critical_suggestions:
            plan = self._create_plan("紧急重构计划", "处理关键代码问题", critical_suggestions)
            self.plans.append(plan)

        high_suggestions = [s for s in self.suggestions if s.priority == Priority.P1_HIGH]
        if high_suggestions:
            plan = self._create_plan("高优先级重构计划", "处理高优先级代码问题", high_suggestions[:10])
            self.plans.append(plan)

        by_file: Dict[str, List[RefactoringSuggestion]] = {}
        for s in self.suggestions:
            if s.file_path not in by_file:
                by_file[s.file_path] = []
            by_file[s.file_path].append(s)

        for file_path, suggestions in by_file.items():
            if len(suggestions) >= 3:
                plan = self._create_plan(
                    f"文件重构计划: {Path(file_path).name}",
                    f"集中处理 {Path(file_path).name} 中的代码问题",
                    suggestions
                )
                self.plans.append(plan)

    def _create_plan(self, name: str, description: str, suggestions: List[RefactoringSuggestion]) -> RefactoringPlan:
        """创建重构计划"""
        plan_id = f"PLAN-{len(self.plans) + 1:03d}"

        total_effort = sum(s.estimated_minutes for s in suggestions)

        phases = self._create_phases(suggestions)

        prerequisites = list(set(
            dep for s in suggestions for dep in s.dependencies
        ))

        return RefactoringPlan(
            id=plan_id,
            name=name,
            description=description,
            suggestions=suggestions,
            total_effort_minutes=total_effort,
            phases=phases,
            prerequisites=prerequisites
        )

    def _create_phases(self, suggestions: List[RefactoringSuggestion]) -> List[Dict[str, Any]]:
        """创建重构阶段"""
        phases = []

        phase1 = {
            "name": "准备阶段",
            "description": "确保测试覆盖和备份",
            "tasks": [
                "运行现有测试确保通过",
                "为待重构代码添加测试（如缺失）",
                "创建代码备份或提交当前状态"
            ],
            "estimated_minutes": 15
        }
        phases.append(phase1)

        by_type: Dict[RefactoringType, List[RefactoringSuggestion]] = {}
        for s in suggestions:
            if s.refactoring_type not in by_type:
                by_type[s.refactoring_type] = []
            by_type[s.refactoring_type].append(s)

        phase2 = {
            "name": "执行阶段",
            "description": "执行重构操作",
            "tasks": [],
            "estimated_minutes": sum(s.estimated_minutes for s in suggestions)
        }

        for ref_type, items in by_type.items():
            task = f"{ref_type.value}: {len(items)} 处"
            phase2["tasks"].append(task)

        phases.append(phase2)

        phase3 = {
            "name": "验证阶段",
            "description": "验证重构结果",
            "tasks": [
                "运行所有测试",
                "检查代码风格",
                "更新文档（如需要）",
                "代码审查"
            ],
            "estimated_minutes": 20
        }
        phases.append(phase3)

        return phases

    def _calculate_summary(self) -> Dict[str, Any]:
        """计算摘要"""
        if not self.suggestions:
            return {
                "total_suggestions": 0,
                "by_priority": {},
                "by_effort": {},
                "by_type": {},
                "total_estimated_minutes": 0,
                "high_impact_count": 0
            }

        by_priority: Dict[str, int] = {}
        by_effort: Dict[str, int] = {}
        by_type: Dict[str, int] = {}

        for suggestion in self.suggestions:
            by_priority[suggestion.priority.value] = by_priority.get(suggestion.priority.value, 0) + 1
            by_effort[suggestion.effort.value] = by_effort.get(suggestion.effort.value, 0) + 1
            by_type[suggestion.refactoring_type.value] = by_type.get(suggestion.refactoring_type.value, 0) + 1

        total_minutes = sum(s.estimated_minutes for s in self.suggestions)
        high_impact_count = sum(1 for s in self.suggestions if s.impact_score >= 70)

        return {
            "total_suggestions": len(self.suggestions),
            "by_priority": by_priority,
            "by_effort": by_effort,
            "by_type": by_type,
            "total_estimated_minutes": total_minutes,
            "total_estimated_hours": round(total_minutes / 60, 1),
            "high_impact_count": high_impact_count,
            "plan_count": len(self.plans)
        }

    def print_report(self, report: GenerationReport):
        """打印报告"""
        print("\n" + "=" * 80)
        print("重构建议生成报告")
        print("=" * 80)
        print(f"项目根目录: {report.project_root}")
        print(f"生成时间: {report.timestamp}")
        print(f"建议总数: {report.total_suggestions}")

        print("\n" + "-" * 80)
        print("摘要统计")
        print("-" * 80)

        summary = report.summary
        print(f"\n按优先级统计:")
        for priority, count in summary.get("by_priority", {}).items():
            print(f"  {priority}: {count}")

        print(f"\n按工作量统计:")
        for effort, count in summary.get("by_effort", {}).items():
            print(f"  {effort}: {count}")

        print(f"\n预估总工作量: {summary.get('total_estimated_hours', 0)} 小时")
        print(f"高影响建议数: {summary.get('high_impact_count', 0)}")

        if report.plans:
            print("\n" + "-" * 80)
            print("重构计划")
            print("-" * 80)
            for plan in report.plans:
                print(f"\n[{plan.id}] {plan.name}")
                print(f"  描述: {plan.description}")
                print(f"  建议数: {len(plan.suggestions)}")
                print(f"  预估时间: {plan.total_effort_minutes} 分钟")
                for phase in plan.phases:
                    print(f"  - {phase['name']}: {phase['estimated_minutes']} 分钟")

        if report.suggestions:
            print("\n" + "-" * 80)
            print("重构建议列表 (Top 20)")
            print("-" * 80)

            for i, suggestion in enumerate(report.suggestions[:20], 1):
                priority_icon = {
                    Priority.P0_CRITICAL: "🔴",
                    Priority.P1_HIGH: "🟠",
                    Priority.P2_MEDIUM: "🟡",
                    Priority.P3_LOW: "🔵"
                }.get(suggestion.priority, "⚪")

                print(f"\n{i}. [{suggestion.id}] {priority_icon} {suggestion.title}")
                print(f"   文件: {Path(suggestion.file_path).name}:{suggestion.line_start}")
                print(f"   类型: {suggestion.refactoring_type.value}")
                print(f"   描述: {suggestion.description}")
                print(f"   工作量: {suggestion.effort.value} ({suggestion.estimated_minutes}分钟)")
                print(f"   影响分: {suggestion.impact_score:.1f}")
                if suggestion.steps:
                    print(f"   步骤: {suggestion.steps[0]}")

            if len(report.suggestions) > 20:
                print(f"\n... 还有 {len(report.suggestions) - 20} 个建议未显示")

    def save_report(self, report: GenerationReport, output_dir: Optional[Path] = None) -> Path:
        """保存报告"""
        if output_dir is None:
            output_dir = get_path_config().REPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"refactoring_suggestions_{timestamp}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        latest_path = output_dir / "refactoring_suggestions_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {report_path}")
        return report_path


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("RefactoringSuggestionGenerator")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="重构建议生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python refactoring_suggestion_generator.py
  python refactoring_suggestion_generator.py --input code_smell_detection_latest.json
  python refactoring_suggestion_generator.py --priority high
        """
    )

    parser.add_argument(
        "--input",
        type=str,
        help="输入的代码异味检测报告路径"
    )

    parser.add_argument(
        "--priority",
        choices=["critical", "high", "medium", "low"],
        help="只生成指定优先级的建议"
    )

    parser.add_argument(
        "--output",
        choices=["console", "json"],
        default="console",
        help="输出格式 (默认: console)"
    )

    parser.add_argument(
        "--output-file",
        type=str,
        help="输出文件路径"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )

    args = parser.parse_args()

    logger = setup_logger(args.verbose)

    generator = RefactoringSuggestionGenerator(logger=logger)

    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            default_path = generator.project_root / "reports" / args.input
            if default_path.exists():
                input_path = default_path
            else:
                print(f"错误: 找不到输入文件 {args.input}")
                return 1

        report = generator.generate_from_smell_report(input_path)
    else:
        latest_path = generator.project_root / "reports" / "code_smell_detection_latest.json"
        if latest_path.exists():
            report = generator.generate_from_smell_report(latest_path)
        else:
            print("错误: 未找到代码异味检测报告，请先运行 intelligent_code_smell_detector.py")
            return 1

    if args.priority:
        priority_map = {
            "critical": Priority.P0_CRITICAL,
            "high": Priority.P1_HIGH,
            "medium": Priority.P2_MEDIUM,
            "low": Priority.P3_LOW
        }
        target_priority = priority_map[args.priority]
        report.suggestions = [s for s in report.suggestions if s.priority == target_priority]
        report.total_suggestions = len(report.suggestions)

    generator.print_report(report)

    report_path = generator.save_report(report)
    print(f"\n报告已保存到: {report_path}")

    if args.output == "json":
        output_data = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)

        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_data)
            print(f"\nJSON结果已保存到: {output_path}")
        else:
            print("\nJSON结果:")
            print(output_data)

    return 0


if __name__ == "__main__":
    sys.exit(main())
