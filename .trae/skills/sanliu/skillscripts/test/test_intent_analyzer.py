#!/usr/bin/env python3
"""
Test Intent Analyzer - 测试意图记录和分析器

TDD红阶段智能增强组件，支持：
1. 测试意图记录机制
2. 测试目的、预期行为、边界条件记录
3. 测试意图分析报告生成
4. 测试覆盖率追踪
5. 需求追溯矩阵

使用示例：
    python test_intent_analyzer.py --intents test_intents.json --analyze
    python test_intent_analyzer.py --intents test_intents.json --report report.html
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict


class IntentCategory(Enum):
    FUNCTIONAL = "functional"
    BOUNDARY = "boundary"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE = "performance"
    SECURITY = "security"
    INTEGRATION = "integration"
    ACCEPTANCE = "acceptance"


class IntentStatus(Enum):
    DEFINED = "defined"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    DEPRECATED = "deprecated"


class CoverageLevel(Enum):
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


@dataclass
class TestIntentRecord:
    test_id: str
    purpose: str
    expected_behavior: str
    category: IntentCategory = IntentCategory.FUNCTIONAL
    status: IntentStatus = IntentStatus.DEFINED
    boundary_conditions: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    related_requirements: List[str] = field(default_factory=list)
    risk_level: str = "medium"
    coverage_target: float = 100.0
    actual_coverage: float = 0.0
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: List[str] = field(default_factory=list)


@dataclass
class RequirementTrace:
    requirement_id: str
    requirement_name: str
    test_intents: List[str] = field(default_factory=list)
    coverage_status: CoverageLevel = CoverageLevel.NONE
    coverage_percentage: float = 0.0
    gaps: List[str] = field(default_factory=list)


@dataclass
class IntentAnalysisResult:
    total_intents: int
    by_category: Dict[str, int]
    by_status: Dict[str, int]
    by_risk_level: Dict[str, int]
    coverage_analysis: Dict[str, Any]
    requirement_traces: List[RequirementTrace]
    recommendations: List[str]
    gaps: List[str]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class TestIntentRegistry:
    """测试意图注册表"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self.intents: Dict[str, TestIntentRecord] = {}
        self.requirement_index: Dict[str, Set[str]] = defaultdict(set)
        self.category_index: Dict[IntentCategory, Set[str]] = defaultdict(set)
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        
        if self.storage_path and self.storage_path.exists():
            self._load()
    
    def register(self, intent: TestIntentRecord) -> None:
        self.intents[intent.test_id] = intent
        self._update_indices(intent)
        self._save()
    
    def update(self, test_id: str, **kwargs) -> Optional[TestIntentRecord]:
        if test_id not in self.intents:
            return None
        
        intent = self.intents[test_id]
        for key, value in kwargs.items():
            if hasattr(intent, key):
                setattr(intent, key, value)
        
        intent.updated_at = datetime.now().isoformat()
        self._update_indices(intent)
        self._save()
        return intent
    
    def get(self, test_id: str) -> Optional[TestIntentRecord]:
        return self.intents.get(test_id)
    
    def get_by_requirement(self, requirement_id: str) -> List[TestIntentRecord]:
        test_ids = self.requirement_index.get(requirement_id, set())
        return [self.intents[tid] for tid in test_ids if tid in self.intents]
    
    def get_by_category(self, category: IntentCategory) -> List[TestIntentRecord]:
        test_ids = self.category_index.get(category, set())
        return [self.intents[tid] for tid in test_ids if tid in self.intents]
    
    def get_by_tag(self, tag: str) -> List[TestIntentRecord]:
        test_ids = self.tag_index.get(tag, set())
        return [self.intents[tid] for tid in test_ids if tid in self.intents]
    
    def get_all(self) -> List[TestIntentRecord]:
        return list(self.intents.values())
    
    def delete(self, test_id: str) -> bool:
        if test_id not in self.intents:
            return False
        
        intent = self.intents[test_id]
        self._remove_from_indices(intent)
        del self.intents[test_id]
        self._save()
        return True
    
    def _update_indices(self, intent: TestIntentRecord) -> None:
        self._remove_from_indices(intent)
        
        for req_id in intent.related_requirements:
            self.requirement_index[req_id].add(intent.test_id)
        
        self.category_index[intent.category].add(intent.test_id)
        
        for tag in intent.tags:
            self.tag_index[tag].add(intent.test_id)
    
    def _remove_from_indices(self, intent: TestIntentRecord) -> None:
        for req_id in intent.related_requirements:
            self.requirement_index[req_id].discard(intent.test_id)
        
        if intent.category in self.category_index:
            self.category_index[intent.category].discard(intent.test_id)
        
        for tag in intent.tags:
            self.tag_index[tag].discard(intent.test_id)
    
    def _save(self) -> None:
        if not self.storage_path:
            return
        
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "intents": {tid: self._intent_to_dict(intent) for tid, intent in self.intents.items()},
            "metadata": {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "total_count": len(self.intents)
            }
        }
        
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def _load(self) -> None:
        with open(self.storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for tid, intent_dict in data.get("intents", {}).items():
            intent = self._dict_to_intent(intent_dict)
            self.intents[tid] = intent
            self._update_indices(intent)
    
    def _intent_to_dict(self, intent: TestIntentRecord) -> Dict[str, Any]:
        return {
            "test_id": intent.test_id,
            "purpose": intent.purpose,
            "expected_behavior": intent.expected_behavior,
            "category": intent.category.value,
            "status": intent.status.value,
            "boundary_conditions": intent.boundary_conditions,
            "preconditions": intent.preconditions,
            "postconditions": intent.postconditions,
            "related_requirements": intent.related_requirements,
            "risk_level": intent.risk_level,
            "coverage_target": intent.coverage_target,
            "actual_coverage": intent.actual_coverage,
            "tags": intent.tags,
            "created_at": intent.created_at,
            "updated_at": intent.updated_at,
            "notes": intent.notes
        }
    
    def _dict_to_intent(self, data: Dict[str, Any]) -> TestIntentRecord:
        return TestIntentRecord(
            test_id=data["test_id"],
            purpose=data["purpose"],
            expected_behavior=data["expected_behavior"],
            category=IntentCategory(data.get("category", "functional")),
            status=IntentStatus(data.get("status", "defined")),
            boundary_conditions=data.get("boundary_conditions", []),
            preconditions=data.get("preconditions", []),
            postconditions=data.get("postconditions", []),
            related_requirements=data.get("related_requirements", []),
            risk_level=data.get("risk_level", "medium"),
            coverage_target=data.get("coverage_target", 100.0),
            actual_coverage=data.get("actual_coverage", 0.0),
            tags=data.get("tags", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            notes=data.get("notes", [])
        )


class TestIntentAnalyzer:
    """测试意图分析器"""
    
    RISK_WEIGHTS = {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.3
    }
    
    CATEGORY_PRIORITIES = {
        IntentCategory.FUNCTIONAL: 1.0,
        IntentCategory.BOUNDARY: 0.9,
        IntentCategory.ERROR_HANDLING: 0.85,
        IntentCategory.SECURITY: 0.95,
        IntentCategory.PERFORMANCE: 0.7,
        IntentCategory.INTEGRATION: 0.8,
        IntentCategory.ACCEPTANCE: 0.9
    }
    
    def __init__(self, registry: TestIntentRegistry):
        self.registry = registry
    
    def analyze(self) -> IntentAnalysisResult:
        intents = self.registry.get_all()
        
        by_category = self._analyze_by_category(intents)
        by_status = self._analyze_by_status(intents)
        by_risk_level = self._analyze_by_risk_level(intents)
        coverage_analysis = self._analyze_coverage(intents)
        requirement_traces = self._build_requirement_traces(intents)
        recommendations = self._generate_recommendations(intents, coverage_analysis, requirement_traces)
        gaps = self._identify_gaps(intents, requirement_traces)
        
        return IntentAnalysisResult(
            total_intents=len(intents),
            by_category=by_category,
            by_status=by_status,
            by_risk_level=by_risk_level,
            coverage_analysis=coverage_analysis,
            requirement_traces=requirement_traces,
            recommendations=recommendations,
            gaps=gaps
        )
    
    def _analyze_by_category(self, intents: List[TestIntentRecord]) -> Dict[str, int]:
        counts = defaultdict(int)
        for intent in intents:
            counts[intent.category.value] += 1
        return dict(counts)
    
    def _analyze_by_status(self, intents: List[TestIntentRecord]) -> Dict[str, int]:
        counts = defaultdict(int)
        for intent in intents:
            counts[intent.status.value] += 1
        return dict(counts)
    
    def _analyze_by_risk_level(self, intents: List[TestIntentRecord]) -> Dict[str, int]:
        counts = defaultdict(int)
        for intent in intents:
            counts[intent.risk_level] += 1
        return dict(counts)
    
    def _analyze_coverage(self, intents: List[TestIntentRecord]) -> Dict[str, Any]:
        if not intents:
            return {
                "average_coverage": 0.0,
                "fully_covered": 0,
                "partially_covered": 0,
                "not_covered": 0,
                "by_category": {}
            }
        
        total_coverage = sum(intent.actual_coverage for intent in intents)
        avg_coverage = total_coverage / len(intents)
        
        fully_covered = sum(1 for i in intents if i.actual_coverage >= i.coverage_target)
        partially_covered = sum(1 for i in intents if 0 < i.actual_coverage < i.coverage_target)
        not_covered = sum(1 for i in intents if i.actual_coverage == 0)
        
        by_category = defaultdict(lambda: {"total": 0, "covered": 0, "percentage": 0.0})
        for intent in intents:
            cat = intent.category.value
            by_category[cat]["total"] += 1
            if intent.actual_coverage >= intent.coverage_target:
                by_category[cat]["covered"] += 1
        
        for cat_data in by_category.values():
            if cat_data["total"] > 0:
                cat_data["percentage"] = (cat_data["covered"] / cat_data["total"]) * 100
        
        return {
            "average_coverage": round(avg_coverage, 2),
            "fully_covered": fully_covered,
            "partially_covered": partially_covered,
            "not_covered": not_covered,
            "by_category": dict(by_category)
        }
    
    def _build_requirement_traces(self, intents: List[TestIntentRecord]) -> List[RequirementTrace]:
        req_intents: Dict[str, List[TestIntentRecord]] = defaultdict(list)
        
        for intent in intents:
            for req_id in intent.related_requirements:
                req_intents[req_id].append(intent)
        
        traces = []
        for req_id, req_intent_list in req_intents.items():
            total_coverage = sum(i.actual_coverage for i in req_intent_list)
            target_coverage = sum(i.coverage_target for i in req_intent_list)
            
            if target_coverage > 0:
                coverage_percentage = (total_coverage / target_coverage) * 100
            else:
                coverage_percentage = 0.0
            
            if coverage_percentage >= 100:
                status = CoverageLevel.FULL
            elif coverage_percentage > 0:
                status = CoverageLevel.PARTIAL
            else:
                status = CoverageLevel.NONE
            
            gaps = []
            for intent in req_intent_list:
                if intent.actual_coverage < intent.coverage_target:
                    gaps.append(f"测试 {intent.test_id} 覆盖率不足: {intent.actual_coverage}% < {intent.coverage_target}%")
            
            traces.append(RequirementTrace(
                requirement_id=req_id,
                requirement_name=f"需求 {req_id}",
                test_intents=[i.test_id for i in req_intent_list],
                coverage_status=status,
                coverage_percentage=round(coverage_percentage, 2),
                gaps=gaps
            ))
        
        return traces
    
    def _generate_recommendations(
        self,
        intents: List[TestIntentRecord],
        coverage_analysis: Dict[str, Any],
        requirement_traces: List[RequirementTrace]
    ) -> List[str]:
        recommendations = []
        
        if coverage_analysis["not_covered"] > 0:
            recommendations.append(
                f"发现 {coverage_analysis['not_covered']} 个测试意图未覆盖，建议优先处理高风险测试"
            )
        
        high_risk_uncovered = [
            i for i in intents
            if i.risk_level in ["critical", "high"] and i.actual_coverage < i.coverage_target
        ]
        if high_risk_uncovered:
            recommendations.append(
                f"发现 {len(high_risk_uncovered)} 个高风险测试未完全覆盖，建议立即处理"
            )
        
        category_gaps = []
        for cat, data in coverage_analysis.get("by_category", {}).items():
            if data["percentage"] < 80:
                category_gaps.append(f"{cat}({data['percentage']:.1f}%)")
        
        if category_gaps:
            recommendations.append(
                f"以下测试类型覆盖率低于80%: {', '.join(category_gaps)}"
            )
        
        partial_traces = [t for t in requirement_traces if t.coverage_status == CoverageLevel.PARTIAL]
        if partial_traces:
            recommendations.append(
                f"发现 {len(partial_traces)} 个需求部分覆盖，建议补充测试用例"
            )
        
        none_traces = [t for t in requirement_traces if t.coverage_status == CoverageLevel.NONE]
        if none_traces:
            recommendations.append(
                f"发现 {len(none_traces)} 个需求未覆盖，建议添加测试用例"
            )
        
        return recommendations
    
    def _identify_gaps(
        self,
        intents: List[TestIntentRecord],
        requirement_traces: List[RequirementTrace]
    ) -> List[str]:
        gaps = []
        
        for intent in intents:
            if intent.actual_coverage < intent.coverage_target:
                gap_pct = intent.coverage_target - intent.actual_coverage
                gaps.append(
                    f"[{intent.test_id}] {intent.purpose}: 覆盖缺口 {gap_pct:.1f}%"
                )
        
        for trace in requirement_traces:
            if trace.coverage_status != CoverageLevel.FULL:
                gaps.extend(trace.gaps)
        
        return gaps
    
    def calculate_priority_score(self, intent: TestIntentRecord) -> float:
        risk_score = self.RISK_WEIGHTS.get(intent.risk_level, 0.5)
        category_score = self.CATEGORY_PRIORITIES.get(intent.category, 0.5)
        coverage_gap = max(0, intent.coverage_target - intent.actual_coverage) / 100
        
        return risk_score * 0.4 + category_score * 0.3 + coverage_gap * 0.3
    
    def get_prioritized_intents(self) -> List[Tuple[TestIntentRecord, float]]:
        intents = self.registry.get_all()
        scored = [(intent, self.calculate_priority_score(intent)) for intent in intents]
        return sorted(scored, key=lambda x: x[1], reverse=True)


class TestIntentReportGenerator:
    """测试意图报告生成器"""
    
    def __init__(self, analyzer: TestIntentAnalyzer):
        self.analyzer = analyzer
    
    def generate_markdown_report(self, output_path: str) -> str:
        result = self.analyzer.analyze()
        
        lines = [
            "# 测试意图分析报告",
            "",
            f"**生成时间**: {result.generated_at}",
            "",
            "## 概览",
            "",
            f"- **测试意图总数**: {result.total_intents}",
            f"- **完全覆盖**: {result.coverage_analysis['fully_covered']}",
            f"- **部分覆盖**: {result.coverage_analysis['partially_covered']}",
            f"- **未覆盖**: {result.coverage_analysis['not_covered']}",
            f"- **平均覆盖率**: {result.coverage_analysis['average_coverage']:.2f}%",
            "",
            "## 按类别统计",
            "",
            "| 类别 | 数量 | 覆盖率 |",
            "|------|------|--------|",
        ]
        
        for cat, count in result.by_category.items():
            cat_data = result.coverage_analysis.get("by_category", {}).get(cat, {})
            percentage = cat_data.get("percentage", 0)
            lines.append(f"| {cat} | {count} | {percentage:.1f}% |")
        
        lines.extend([
            "",
            "## 按状态统计",
            "",
            "| 状态 | 数量 |",
            "|------|------|",
        ])
        
        for status, count in result.by_status.items():
            lines.append(f"| {status} | {count} |")
        
        lines.extend([
            "",
            "## 按风险级别统计",
            "",
            "| 风险级别 | 数量 |",
            "|----------|------|",
        ])
        
        for risk, count in result.by_risk_level.items():
            lines.append(f"| {risk} | {count} |")
        
        lines.extend([
            "",
            "## 需求追溯",
            "",
            "| 需求ID | 测试数量 | 覆盖状态 | 覆盖率 |",
            "|--------|----------|----------|--------|",
        ])
        
        for trace in result.requirement_traces:
            lines.append(
                f"| {trace.requirement_id} | {len(trace.test_intents)} | "
                f"{trace.coverage_status.value} | {trace.coverage_percentage:.1f}% |"
            )
        
        if result.recommendations:
            lines.extend([
                "",
                "## 建议",
                "",
            ])
            for i, rec in enumerate(result.recommendations, 1):
                lines.append(f"{i}. {rec}")
        
        if result.gaps:
            lines.extend([
                "",
                "## 覆盖缺口",
                "",
            ])
            for gap in result.gaps[:20]:
                lines.append(f"- {gap}")
            
            if len(result.gaps) > 20:
                lines.append(f"- ... 还有 {len(result.gaps) - 20} 个缺口")
        
        lines.extend([
            "",
            "## 优先级排序",
            "",
            "以下测试意图按优先级排序（考虑风险、类别和覆盖缺口）：",
            "",
        ])
        
        prioritized = self.analyzer.get_prioritized_intents()[:10]
        for intent, score in prioritized:
            lines.append(f"- **{intent.test_id}** (优先级分数: {score:.3f})")
            lines.append(f"  - 目的: {intent.purpose}")
            lines.append(f"  - 风险: {intent.risk_level}")
            lines.append(f"  - 覆盖: {intent.actual_coverage:.1f}% / {intent.coverage_target:.1f}%")
            lines.append("")
        
        content = "\n".join(lines)
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        return content
    
    def generate_json_report(self, output_path: str) -> Dict[str, Any]:
        result = self.analyzer.analyze()
        
        report = {
            "generated_at": result.generated_at,
            "summary": {
                "total_intents": result.total_intents,
                "coverage": result.coverage_analysis
            },
            "statistics": {
                "by_category": result.by_category,
                "by_status": result.by_status,
                "by_risk_level": result.by_risk_level
            },
            "requirement_traces": [
                {
                    "requirement_id": t.requirement_id,
                    "test_intents": t.test_intents,
                    "coverage_status": t.coverage_status.value,
                    "coverage_percentage": t.coverage_percentage,
                    "gaps": t.gaps
                }
                for t in result.requirement_traces
            ],
            "recommendations": result.recommendations,
            "gaps": result.gaps,
            "prioritized_intents": [
                {
                    "test_id": intent.test_id,
                    "purpose": intent.purpose,
                    "priority_score": score,
                    "risk_level": intent.risk_level,
                    "coverage": {
                        "actual": intent.actual_coverage,
                        "target": intent.coverage_target
                    }
                }
                for intent, score in self.analyzer.get_prioritized_intents()
            ]
        }
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        return report


def load_intents_from_file(file_path: str) -> Dict[str, TestIntentRecord]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"意图文件不存在: {file_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    intents = {}
    for test_id, intent_data in data.items():
        if isinstance(intent_data, dict):
            category_str = intent_data.get("category", "functional")
            try:
                category = IntentCategory(category_str)
            except ValueError:
                category = IntentCategory.FUNCTIONAL
            
            intents[test_id] = TestIntentRecord(
                test_id=test_id,
                purpose=intent_data.get("purpose", ""),
                expected_behavior=intent_data.get("expected_behavior", ""),
                category=category,
                boundary_conditions=intent_data.get("boundary_conditions", []),
                preconditions=intent_data.get("preconditions", []),
                postconditions=intent_data.get("postconditions", []),
                related_requirements=intent_data.get("related_requirements", []),
                risk_level=intent_data.get("risk_level", "medium"),
                coverage_target=intent_data.get("coverage_target", 100.0),
                actual_coverage=intent_data.get("actual_coverage", 0.0),
                tags=intent_data.get("tags", [])
            )
    
    return intents


def main():
    parser = argparse.ArgumentParser(
        description="测试意图分析器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析测试意图
  python test_intent_analyzer.py --intents test_intents.json --analyze
  
  # 生成Markdown报告
  python test_intent_analyzer.py --intents test_intents.json --report intent_report.md
  
  # 生成JSON报告
  python test_intent_analyzer.py --intents test_intents.json --json-report intent_report.json
        """
    )
    
    parser.add_argument(
        "--intents",
        required=True,
        help="测试意图文件路径"
    )
    
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="执行分析"
    )
    
    parser.add_argument(
        "--report",
        help="生成Markdown报告的输出路径"
    )
    
    parser.add_argument(
        "--json-report",
        help="生成JSON报告的输出路径"
    )
    
    parser.add_argument(
        "--registry-path",
        help="测试意图注册表存储路径"
    )
    
    args = parser.parse_args()
    
    try:
        intents_data = load_intents_from_file(args.intents)
        
        registry = TestIntentRegistry(args.registry_path)
        for test_id, intent in intents_data.items():
            registry.register(intent)
        
        analyzer = TestIntentAnalyzer(registry)
        report_generator = TestIntentReportGenerator(analyzer)
        
        if args.analyze:
            result = analyzer.analyze()
            print("测试意图分析结果:")
            print(f"  总数: {result.total_intents}")
            print(f"  平均覆盖率: {result.coverage_analysis['average_coverage']:.2f}%")
            print(f"  完全覆盖: {result.coverage_analysis['fully_covered']}")
            print(f"  部分覆盖: {result.coverage_analysis['partially_covered']}")
            print(f"  未覆盖: {result.coverage_analysis['not_covered']}")
            
            if result.recommendations:
                print("\n建议:")
                for i, rec in enumerate(result.recommendations, 1):
                    print(f"  {i}. {rec}")
        
        if args.report:
            report_generator.generate_markdown_report(args.report)
            print(f"\nMarkdown报告已生成: {args.report}")
        
        if args.json_report:
            report_generator.generate_json_report(args.json_report)
            print(f"\nJSON报告已生成: {args.json_report}")
        
        if not (args.analyze or args.report or args.json_report):
            result = analyzer.analyze()
            print("测试意图分析结果:")
            print(json.dumps({
                "total_intents": result.total_intents,
                "coverage": result.coverage_analysis,
                "recommendations": result.recommendations
            }, ensure_ascii=False, indent=2))
        
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"执行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
