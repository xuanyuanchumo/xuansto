from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class EvalQuery:
    id: int
    query: str
    should_trigger: bool
    category: str
    difficulty: Difficulty = Difficulty.EASY


@dataclass
class CategoryStats:
    total: int = 0
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0

    @property
    def precision(self) -> float:
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def f1_score(self) -> float:
        p, r = self.precision, self.recall
        return (2 * p * r) / (p + r) if (p + r) > 0 else 0.0


@dataclass
class DifficultyStats:
    total: int = 0
    correct: int = 0

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total > 0 else 0.0


@dataclass
class TriggerEvalResult:
    total_queries: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    by_category: dict[str, CategoryStats] = field(default_factory=dict)
    by_difficulty: dict[Difficulty, DifficultyStats] = field(default_factory=dict)
    generated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


DEFAULT_EVAL_QUERIES: list[EvalQuery] = [
    EvalQuery(id=1, query="使用三省六部进行一个电商系统的全生命周期开发", should_trigger=True, category="primary_trigger", difficulty=Difficulty.EASY),
    EvalQuery(id=2, query="帮我写一个Python函数计算斐波那契数列", should_trigger=False, category="code_generation_only", difficulty=Difficulty.EASY),
    EvalQuery(id=3, query="进行TDD驱动的需求分析和架构设计", should_trigger=True, category="secondary_trigger", difficulty=Difficulty.MEDIUM),
    EvalQuery(id=4, query="帮我解释一下Python的装饰器原理", should_trigger=False, category="concept_explanation", difficulty=Difficulty.EASY),
    EvalQuery(id=5, query="搭建一套完整的CI/CD流水线，包含自动化测试和部署", should_trigger=True, category="primary_trigger", difficulty=Difficulty.HARD),
    EvalQuery(id=6, query="这个正则表达式是什么意思？", should_trigger=False, category="simple_question", difficulty=Difficulty.EASY),
    EvalQuery(id=7, query="使用Docker容器化部署微服务架构", should_trigger=True, category="primary_trigger", difficulty=Difficulty.MEDIUM),
    EvalQuery(id=8, query="把这段代码的变量名改成驼峰命名", should_trigger=False, category="code_refactoring", difficulty=Difficulty.EASY),
    EvalQuery(id=9, query="实现一个完整的DevOps工作流：从需求到上线", should_trigger=True, category="primary_trigger", difficulty=Difficulty.HARD),
    EvalQuery(id=10, query="如何安装numpy库？", should_trigger=False, category="package_installation", difficulty=Difficulty.EASY),
    EvalQuery(id=11, query="配置Kubernetes集群并进行滚动更新部署", should_trigger=True, category="primary_trigger", difficulty=Difficulty.HARD),
    EvalQuery(id=12, query="这个报错怎么解决：NameError: name 'x' is not defined", should_trigger=False, category="debug_help", difficulty=Difficulty.EASY),
    EvalQuery(id=13, query="进行性能优化和监控告警系统建设", should_trigger=True, category="secondary_trigger", difficulty=Difficulty.MEDIUM),
    EvalQuery(id=14, query="把JSON转换成Python字典", should_trigger=False, category="data_conversion", difficulty=Difficulty.EASY),
    EvalQuery(id=15, query="建立代码审查流程和质量门禁机制", should_trigger=True, category="secondary_trigger", difficulty=Difficulty.MEDIUM),
    EvalQuery(id=16, query="今天天气怎么样？", should_trigger=False, category="irrelevant", difficulty=Difficulty.EASY),
    EvalQuery(id=17, query="设计并实施灰度发布和回滚策略", should_trigger=True, category="primary_trigger", difficulty=Difficulty.HARD),
    EvalQuery(id=18, query="写一个Hello World程序", should_trigger=False, category="basic_code", difficulty=Difficulty.EASY),
    EvalQuery(id=19, query="构建全链路日志追踪和分布式监控系统", should_trigger=True, category="primary_trigger", difficulty=Difficulty.HARD),
    EvalQuery(id=20, query="git commit的-m参数是什么意思", should_trigger=False, category="git_question", difficulty=Difficulty.EASY),
    EvalQuery(id=21, query="用三省六部方法论做敏捷项目管理", should_trigger=True, category="primary_trigger", difficulty=Difficulty.MEDIUM),
    EvalQuery(id=22, query="列表推导式和生成器有什么区别", should_trigger=False, category="python_concept", difficulty=Difficulty.EASY),
    EvalQuery(id=23, query="实施基础设施即代码(IaC)和配置管理", should_trigger=True, category="secondary_trigger", difficulty=Difficulty.MEDIUM),
    EvalQuery(id=24, query="把字符串转成大写", should_trigger=False, category="string_operation", difficulty=Difficulty.EASY),
]


PRIMARY_TRIGGER_KEYWORDS = {
    "三省六部",
    "全生命周期",
    "devops",
    "ci/cd",
    "持续集成",
    "持续交付",
    "持续部署",
    "自动化部署",
    "容器化",
    "docker",
    "kubernetes",
    "k8s",
    "微服务",
    "监控告警",
    "灰度发布",
    "滚动更新",
    "基础设施即代码",
    "iac",
    "质量门禁",
    "代码审查",
    "code review",
    "性能基准",
    "全链路",
    "日志追踪",
}
SECONDARY_TRIGGER_KEYWORDS = {
    "tdd",
    "测试驱动",
    "需求分析",
    "架构设计",
    "性能优化",
    "敏捷",
    "scrum",
    "kanban",
    "配置管理",
    "版本控制策略",
    "分支管理",
    "安全扫描",
    "漏洞检测",
}


class TriggerEvaluator:
    def __init__(
        self,
        queries: list[EvalQuery] | None = None,
        primary_keywords: set[str] | None = None,
        secondary_keywords: set[str] | None = None,
    ):
        self._queries = queries or list(DEFAULT_EVAL_QUERIES)
        self._primary_keywords = primary_keywords or PRIMARY_TRIGGER_KEYWORDS
        self._secondary_keywords = secondary_keywords or SECONDARY_TRIGGER_KEYWORDS

    @classmethod
    def from_json(cls, json_path: Path) -> TriggerEvaluator:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        queries = [
            EvalQuery(
                id=q["id"],
                query=q["query"],
                should_trigger=q["should_trigger"],
                category=q.get("category", "unknown"),
                difficulty=Difficulty(q.get("difficulty", "easy")),
            )
            for q in data.get("queries", [])
        ]
        return cls(queries=queries)

    def evaluate(self, custom_predictor: Any | None = None) -> TriggerEvalResult:
        tp = fp = tn = fn = 0
        by_category: dict[str, CategoryStats] = {}
        by_difficulty: dict[Difficulty, DifficultyStats] = {}
        for q in self._queries:
            predicted = self._predict(q.query) if custom_predictor is None else custom_predictor(q.query)
            if q.should_trigger and predicted:
                tp += 1
            elif not q.should_trigger and predicted:
                fp += 1
            elif not q.should_trigger and not predicted:
                tn += 1
            else:
                fn += 1
            cat_stats = by_category.setdefault(q.category, CategoryStats())
            cat_stats.total += 1
            if q.should_trigger and predicted:
                cat_stats.true_positives += 1
            elif not q.should_trigger and predicted:
                cat_stats.false_positives += 1
            elif not q.should_trigger and not predicted:
                cat_stats.true_negatives += 1
            else:
                cat_stats.false_negatives += 1
            diff_stats = by_difficulty.setdefault(q.difficulty, DifficultyStats())
            diff_stats.total += 1
            if predicted == q.should_trigger:
                diff_stats.correct += 1
        total = len(self._queries)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (tp + tn) / total if total > 0 else 0.0
        return TriggerEvalResult(
            total_queries=total,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            accuracy=round(accuracy, 4),
            by_category=by_category,
            by_difficulty=by_difficulty,
        )

    def _predict(self, query: str) -> bool:
        lower = query.lower()
        primary_hits = sum(1 for kw in self._primary_keywords if kw.lower() in lower)
        secondary_hits = sum(1 for kw in self._secondary_keywords if kw.lower() in lower)
        return primary_hits >= 1 or secondary_hits >= 2

    def generate_report(self, result: TriggerEvalResult | None = None) -> str:
        r = result or self.evaluate()
        lines: list[str] = []
        lines.append("# 触发准确率评估报告")
        lines.append("")
        lines.append(f"> 评估时间: {r.generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        lines.append(f"> 测试查询总数: **{r.total_queries}** 条")
        lines.append("")
        lines.append("## 核心指标")
        lines.append("")
        lines.append("| 指标 | 值 | 说明 |")
        lines.append("|------|------|------|")
        lines.append(f"| 准确率 (Precision) | **{r.precision:.2%}** | TP/(TP+FP) 正确触发占比 |")
        lines.append(f"| 召回率 (Recall) | **{r.recall:.2%}** | TP/(TP+FN) 应触发的都触发了 |")
        lines.append(f"| F1-Score | **{r.f1_score:.4f}** | 精确率和召回率的调和平均 |")
        lines.append(f"| 总体准确率 (Accuracy) | **{r.accuracy:.2%}** | (TP+TN)/Total |")
        lines.append("")
        lines.append("## 混淆矩阵")
        lines.append("")
        lines.append("| | 预测: 触发 | 预测: 不触发 |")
        lines.append("|---|---|---|")
        lines.append(f"| **实际: 应触发** | TP={r.true_positives} ✅ | FN={r.false_negatives} ❌ |")
        lines.append(f"| **实际: 不应触发** | FP={r.false_positives} ❌ | TN={r.true_negatives} ✅ |")
        lines.append("")
        lines.append("## 按类别统计")
        lines.append("")
        lines.append("| 类别 | 总数 | P | R | F1 |")
        lines.append("|------|------|-------|-------|-------|")
        for cat, stats in sorted(r.by_category.items()):
            lines.append(
                f"| {cat} | {stats.total} | {stats.precision:.2%} | "
                f"{stats.recall:.2%} | {stats.f1_score:.4f} |"
            )
        lines.append("")
        lines.append("## 按难度统计")
        lines.append("")
        lines.append("| 难度 | 总数 | 正确 | 准确率 |")
        lines.append("|------|------|------|--------|")
        for diff, stats in sorted(r.by_difficulty.items(), key=lambda x: x[0].value):
            lines.append(
                f"| {diff.value} | {stats.total} | {stats.correct} | {stats.accuracy:.2%} |"
            )
        lines.append("")
        grade = self._grade_result(r)
        lines.append("## 评估结论")
        lines.append("")
        lines.append(f"### 综合评级: **{grade['letter']}** ({grade['label']})")
        lines.append("")
        if r.f1_score >= 0.90:
            lines.append("> ✅ 触发系统表现优秀，可投入生产使用。")
        elif r.f1_score >= 0.75:
            lines.append("> ⚠️ 触发系统表现良好，建议优化误触发情况后上线。")
        elif r.f1_score >= 0.60:
            lines.append("> 🔶 触发系统基本可用，需重点改进召回率或精确率。")
        else:
            lines.append("> 🔴 触发系统未达标，需重新设计触发规则后再评估。")
        lines.append("")
        if r.false_positives > 0:
            lines.append("#### 误触发分析（False Positives）")
            lines.append("")
            lines.append("以下查询不应触发但被错误触发：")
            lines.append("")
            for q in self._queries:
                pred = self._predict(q.query)
                if not q.should_trigger and pred:
                    lines.append(f"- `{q.query}` (类别: {q.category})")
            lines.append("")
        if r.false_negatives > 0:
            lines.append("#### 漏触发分析（False Negatives）")
            lines.append("")
            lines.append("以下查询应该触发但被遗漏：")
            lines.append("")
            for q in self._queries:
                pred = self._predict(q.query)
                if q.should_trigger and not pred:
                    lines.append(f"- `{q.query}` (类别: {q.category})")
            lines.append("")
        lines.append("---")
        lines.append("*报告由 Universal DevOps v6.0 Trigger Evaluator 生成*")
        return "\n".join(lines)

    def export_queries_json(self, output_path: Path) -> None:
        data = {
            "eval_name": "universal-devops-v6-trigger-eval",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "queries": [
                {
                    "id": q.id,
                    "query": q.query,
                    "should_trigger": q.should_trigger,
                    "category": q.category,
                    "difficulty": q.difficulty.value,
                }
                for q in self._queries
            ],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _grade_result(result: TriggerEvalResult) -> dict[str, str]:
        f1 = result.f1_score
        if f1 >= 0.95:
            return {"letter": "A+", "label": "卓越"}
        if f1 >= 0.90:
            return {"letter": "A", "label": "优秀"}
        if f1 >= 0.80:
            return {"letter": "B+", "label": "良好"}
        if f1 >= 0.70:
            return {"letter": "B", "label": "合格"}
        if f1 >= 0.60:
            return {"letter": "C", "label": "待改进"}
        if f1 >= 0.50:
            return {"letter": "D", "label": "不达标"}
        return {"letter": "F", "label": "失败"}
