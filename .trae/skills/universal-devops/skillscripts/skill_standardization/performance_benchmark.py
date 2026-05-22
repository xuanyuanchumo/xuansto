from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class TrendDirection(Enum):
    IMPROVING = "IMPROVING"
    DECLINING = "DECLINING"
    STABLE = "STABLE"


class OutputFormat(Enum):
    MARKDOWN = "markdown"
    CODE = "code"
    JSON = "json"
    TEXT = "text"


@dataclass
class QualityScore:
    completeness: int
    accuracy: int
    format_compliance: int
    usability: int
    context_relevance: int

    @property
    def overall(self) -> float:
        return round(
            statistics.mean(
                [
                    self.completeness,
                    self.accuracy,
                    self.format_compliance,
                    self.usability,
                    self.context_relevance,
                ]
            ),
            2,
        )

    @property
    def grade(self) -> str:
        s = self.overall
        if s >= 4.5:
            return "A+"
        if s >= 4.0:
            return "A"
        if s >= 3.5:
            return "B+"
        if s >= 3.0:
            return "B"
        if s >= 2.5:
            return "C+"
        if s >= 2.0:
            return "C"
        return "D"


@dataclass
class BenchmarkRecord:
    timestamp: datetime
    task_type: str
    response_time_ms: float
    quality_score: float
    memory_mb: float
    cpu_time_s: float
    success: bool
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "task_type": self.task_type,
            "response_time_ms": self.response_time_ms,
            "quality_score": self.quality_score,
            "memory_mb": self.memory_mb,
            "cpu_time_s": self.cpu_time_s,
            "success": self.success,
            "metadata": self.metadata,
        }


@dataclass
class TrendAnalysis:
    metric_name: str
    current_value: float
    average_value: float
    min_value: float
    max_value: float
    trend_direction: TrendDirection
    change_percentage: float
    recommendation: str | None = None


@dataclass
class BenchmarkSummary:
    total_records: int
    avg_response_time: float
    p50_response_time: float
    p99_response_time: float
    avg_quality_score: float
    avg_memory_mb: float
    avg_cpu_time_s: float
    success_rate: float
    by_task_type: dict[str, dict[str, Any]]


class OutputQualityScorer:
    MARKDOWN_REQUIRED_ELEMENTS = {"#", "##", "```", "-", "|"}
    CODE_INDICATORS = {"def ", "class ", "import ", "function", "return", "const", "let", "var"}

    def score_output(self, output: str, expected_format: OutputFormat) -> QualityScore:
        scorers = {
            OutputFormat.MARKDOWN: self.score_markdown,
            OutputFormat.CODE: lambda c: self.score_code(c, ""),
            OutputFormat.JSON: self._score_json,
            OutputFormat.TEXT: self._score_text,
        }
        scorer = scorers.get(expected_format, self._score_text)
        return scorer(output)

    def score_markdown(self, content: str) -> QualityScore:
        completeness = self._calc_markdown_completeness(content)
        accuracy = self._calc_general_accuracy(content)
        format_compliance = self._calc_markdown_format(content)
        usability = self._calc_usability(content)
        context_relevance = self._calc_context_relevance(content)
        return QualityScore(
            completeness=completeness,
            accuracy=accuracy,
            format_compliance=format_compliance,
            usability=usability,
            context_relevance=context_relevance,
        )

    def score_code(self, code: str, language: str) -> QualityScore:
        completeness = self._calc_code_completeness(code)
        accuracy = self._calc_code_accuracy(code)
        format_compliance = self._calc_code_format(code)
        usability = self._calc_code_usability(code)
        context_relevance = self._calc_context_relevance(code)
        return QualityScore(
            completeness=completeness,
            accuracy=accuracy,
            format_compliance=format_compliance,
            usability=usability,
            context_relevance=context_relevance,
        )

    def _calc_markdown_completeness(self, content: str) -> int:
        score = 3
        has_heading = bool(re.match(r"^#{1,6}\s", content, re.MULTILINE))
        has_code_block = "```" in content
        has_list = any(content.startswith(prefix) for prefix in ["- ", "* ", "1. "])
        has_table = "|" in content and "---" in content
        if has_heading:
            score += 1
        if has_code_block or has_list or has_table:
            score += 1
        return min(5, max(1, score))

    def _calc_general_accuracy(self, content: str) -> int:
        length = len(content.strip())
        if length < 20:
            return 1
        if length < 100:
            return 2
        if length < 500:
            return 3
        if length < 2000:
            return 4
        return 5

    def _calc_markdown_format(self, content: str) -> int:
        elements_found = sum(1 for el in self.MARKDOWN_REQUIRED_ELEMENTS if el in content)
        if elements_found >= 4:
            return 5
        if elements_found >= 3:
            return 4
        if elements_found >= 2:
            return 3
        if elements_found >= 1:
            return 2
        return 1

    def _calc_usability(self, content: str) -> int:
        score = 3
        has_steps = bool(re.search(r"\d+\.\s|步骤|Step\s*\d+", content))
        has_examples = "示例" in content or "example" in content.lower() or "```" in content
        has_conclusion = any(w in content for w in ["总结", "结论", "conclusion", "完成"])
        if has_steps:
            score += 1
        if has_examples or has_conclusion:
            score += 1
        return min(5, max(1, score))

    def _calc_context_relevance(self, content: str) -> int:
        devops_keywords = [
            "部署",
            "测试",
            "构建",
            "CI",
            "CD",
            "Docker",
            "K8s",
            "监控",
            "日志",
            "devops",
            "代码",
            "开发",
            "运维",
        ]
        lower = content.lower()
        hits = sum(1 for kw in devops_keywords if kw.lower() in lower)
        if hits >= 6:
            return 5
        if hits >= 4:
            return 4
        if hits >= 2:
            return 3
        if hits >= 1:
            return 2
        return 1

    def _calc_code_completeness(self, code: str) -> int:
        stripped = code.strip()
        if not stripped:
            return 1
        has_function = any(kw in code for kw in ["def ", "function ", "func ", "=>", "class "])
        has_import = any(kw in code for kw in ["import ", "from ", "require(", "#include"])
        has_body = len(stripped.split("\n")) >= 3
        score = 1
        if has_import:
            score += 1
        if has_function:
            score += 1
        if has_body:
            score += 1
        if len(stripped) > 100:
            score += 1
        return min(5, score)

    def _calc_code_accuracy(self, code: str) -> int:
        try:
            compile(code, "<string>", "exec")
            return 4
        except Exception:
            pass
        balanced = code.count("(") == code.count(")") and code.count("{") == code.count("}")
        if balanced and len(code.strip()) > 10:
            return 3
        return 2

    def _calc_code_format(self, code: str) -> int:
        lines = code.strip().split("\n")
        has_indentation = any(line.startswith(" ") or line.startswith("\t") for line in lines[1:] if line.strip())
        has_blank_lines = "" in lines
        score = 2
        if has_indentation:
            score += 1
        if has_blank_lines:
            score += 1
        if len(lines) >= 5:
            score += 1
        return min(5, score)

    def _calc_code_usability(self, code: str) -> int:
        has_docstring = '"""' in code or "'''" in code or '"""' in code
        has_comments = "#" in code or "//" in code
        has_print_or_return = any(kw in code for kw in ["print(", "return ", "console.log"])
        score = 2
        if has_comments:
            score += 1
        if has_print_or_return:
            score += 1
        if has_docstring:
            score += 1
        return min(5, score)

    def _score_json(self, content: str) -> QualityScore:
        try:
            parsed = json.loads(content)
            completeness = min(5, 2 + len(parsed) // 2)
            accuracy = 5
            format_compliance = 5
            usability = 4 if isinstance(parsed, dict) else 3
            context_relevance = self._calc_context_relevance(content)
        except (json.JSONDecodeError, ValueError):
            completeness = 1
            accuracy = 1
            format_compliance = 1
            usability = 1
            context_relevance = 1
        return QualityScore(
            completeness=completeness,
            accuracy=accuracy,
            format_compliance=format_compliance,
            usability=usability,
            context_relevance=context_relevance,
        )

    def _score_text(self, content: str) -> QualityScore:
        return QualityScore(
            completeness=min(5, max(1, len(content.strip()) // 100)),
            accuracy=self._calc_general_accuracy(content),
            format_compliance=3,
            usability=self._calc_usability(content),
            context_relevance=self._calc_context_relevance(content),
        )


import re


class PerformanceHistory:
    def __init__(self, max_records: int = 100):
        self._max_records = max_records
        self._records: list[BenchmarkRecord] = []

    def add_record(self, record: BenchmarkRecord) -> None:
        self._records.append(record)
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records :]

    def get_recent(self, n: int = 10) -> list[BenchmarkRecord]:
        return list(self._records[-n:]) if self._records else []

    @property
    def all_records(self) -> list[BenchmarkRecord]:
        return list(self._records)

    @property
    def count(self) -> int:
        return len(self._records)

    def get_trend(self, metric: str, window: int = 10) -> TrendAnalysis | None:
        recent = self.get_recent(window)
        if len(recent) < 2:
            return None
        getter = self._get_metric_getter(metric)
        values = [getter(r) for r in recent]
        current = values[-1]
        avg = statistics.mean(values)
        min_val = min(values)
        max_val = max(values)
        if len(values) >= 3:
            first_half = statistics.mean(values[: len(values) // 2])
            second_half = statistics.mean(values[len(values) // 2 :])
            change_pct = (
                ((second_half - first_half) / abs(first_half)) * 100
                if first_half != 0
                else 0.0
            )
        else:
            change_pct = 0.0
        lower_is_better = metric in ("response_time_ms", "memory_mb", "cpu_time_s")
        threshold = 5.0
        if abs(change_pct) < threshold:
            direction = TrendDirection.STABLE
        elif (change_pct < 0 and not lower_is_better) or (
            change_pct > 0 and lower_is_better
        ):
            direction = TrendDirection.IMPROVING
        else:
            direction = TrendDirection.DECLINING
        recommendation = self._generate_recommendation(metric, direction, change_pct)
        return TrendAnalysis(
            metric_name=metric,
            current_value=current,
            average_value=round(avg, 2),
            min_value=min_val,
            max_value=max_val,
            trend_direction=direction,
            change_percentage=round(change_pct, 2),
            recommendation=recommendation,
        )

    def generate_trend_report(self) -> str:
        metrics = [
            ("response_time_ms", "响应时间"),
            ("quality_score", "质量评分"),
            ("memory_mb", "内存占用"),
            ("success_rate", "成功率"),
        ]
        lines: list[str] = []
        lines.append("# 性能趋势分析报告")
        lines.append("")
        lines.append(f"> 报告生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        lines.append(f"> 历史记录数: **{len(self._records)}** 条")
        lines.append("")
        summary = self.generate_summary()
        lines.append("## 总体概览")
        lines.append("")
        lines.append("| 指标 | 当前值 | 平均值 | 最小值 | 最大值 | 趋势 | 变化率 |")
        lines.append("|------|--------|--------|--------|--------|------|--------|")
        for metric_key, metric_label in metrics:
            trend = self.get_trend(metric_key, window=min(10, len(self._records)))
            if trend is None:
                continue
            icon = {
                TrendDirection.IMPROVING: "📈",
                TrendDirection.DECLINING: "📉",
                TrendDirection.STABLE: "➡️",
            }.get(trend.trend_direction, "❓")
            change_str = f"{trend.change_percentage:+.1f}%"
            lines.append(
                f"| {metric_label} | {trend.current_value:.2f} | "
                f"{trend.average_value:.2f} | {trend.min_value:.2f} | "
                f"{trend.max_value:.2f} | {icon} {trend.trend_direction.value} | {change_str} |"
            )
        lines.append("")
        lines.append("## 按任务类型统计")
        lines.append("")
        if summary.by_task_type:
            lines.append("| 任务类型 | 执行次数 | 平均响应(ms) | 平均质量分 | 成功率 |")
            lines.append("|----------|----------|-------------|-----------|--------|")
            for task_type, stats in sorted(summary.by_task_type.items()):
                lines.append(
                    f"| {task_type} | {stats['count']} | "
                    f"{stats['avg_response']:.1f} | "
                    f"{stats['avg_quality']:.2f} | "
                    f"{stats['success_rate']:.1%} |"
                )
        else:
            lines.append("*暂无数据*")
        lines.append("")
        lines.append("## 建议")
        lines.append("")
        has_recommendations = False
        for metric_key, metric_label in metrics:
            trend = self.get_trend(metric_key, window=min(10, len(self._records)))
            if trend and trend.recommendation:
                has_recommendations = True
                icon = {
                    TrendDirection.IMPROVING: "✅",
                    TrendDirection.DECLINING: "⚠️",
                    TrendDirection.STABLE: "ℹ️",
                }.get(trend.trend_direction, "•")
                lines.append(f"- {icon} **{metric_label}**: {trend.recommendation}")
        if not has_recommendations:
            lines.append("- 收集更多数据后生成建议...")
        lines.append("")
        lines.append("---")
        lines.append("*报告由 Universal DevOps v6.0 Performance Benchmark 生成*")
        return "\n".join(lines)

    def generate_summary(self) -> BenchmarkSummary:
        if not self._records:
            return BenchmarkSummary(
                total_records=0,
                avg_response_time=0.0,
                p50_response_time=0.0,
                p99_response_time=0.0,
                avg_quality_score=0.0,
                avg_memory_mb=0.0,
                avg_cpu_time_s=0.0,
                success_rate=0.0,
                by_task_type={},
            )
        response_times = [r.response_time_ms for r in self._records]
        quality_scores = [r.quality_score for r in self._records]
        memories = [r.memory_mb for r in self._records]
        cpu_times = [r.cpu_time_s for r in self._records]
        successes = sum(1 for r in self._records if r.success)
        sorted_times = sorted(response_times)
        p50_idx = int(len(sorted_times) * 0.5)
        p99_idx = int(len(sorted_times) * 0.99)
        by_task: dict[str, dict[str, Any]] = {}
        for r in self._records:
            if r.task_type not in by_task:
                by_task[r.task_type] = {
                    "count": 0,
                    "total_response": 0.0,
                    "total_quality": 0.0,
                    "successes": 0,
                }
            t = by_task[r.task_type]
            t["count"] += 1
            t["total_response"] += r.response_time_ms
            t["total_quality"] += r.quality_score
            if r.success:
                t["successes"] += 1
        for task_type in by_task:
            t = by_task[task_type]
            t["avg_response"] = round(t["total_response"] / t["count"], 2)
            t["avg_quality"] = round(t["total_quality"] / t["count"], 2)
            t["success_rate"] = t["successes"] / t["count"]
        return BenchmarkSummary(
            total_records=len(self._records),
            avg_response_time=round(statistics.mean(response_times), 2),
            p50_response_time=sorted_times[p50_idx],
            p99_response_time=sorted_times[min(p99_idx, len(sorted_times) - 1)],
            avg_quality_score=round(statistics.mean(quality_scores), 2),
            avg_memory_mb=round(statistics.mean(memories), 2),
            avg_cpu_time_s=round(statistics.mean(cpu_times), 4),
            success_rate=successes / len(self._records),
            by_task_type=by_task,
        )

    def export_to_json(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_records": len(self._records),
            "summary": {
                "avg_response_time_ms": self.generate_summary().avg_response_time,
                "avg_quality_score": self.generate_summary().avg_quality_score,
                "success_rate": self.generate_summary().success_rate,
            },
            "records": [r.to_dict() for r in self._records],
        }
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _get_metric_getter(metric: str):
        getters = {
            "response_time_ms": lambda r: r.response_time_ms,
            "quality_score": lambda r: r.quality_score,
            "memory_mb": lambda r: r.memory_mb,
            "cpu_time_s": lambda r: r.cpu_time_s,
            "success_rate": lambda r: 1.0 if r.success else 0.0,
        }
        return getters.get(metric, lambda r: 0.0)

    @staticmethod
    def _generate_recommendation(
        metric: str, direction: TrendDirection, change_pct: float
    ) -> str | None:
        recommendations = {
            "response_time_ms": {
                TrendDirection.IMPROVING: "响应速度持续优化，保持当前策略",
                TrendDirection.DECLINING: f"响应时间恶化{abs(change_pct):.1f}%，建议检查资源瓶颈或优化算法",
                TrendDirection.STABLE: "响应时间稳定，可尝试进一步优化",
            },
            "quality_score": {
                TrendDirection.IMPROVING: "输出质量持续提升，继续保持",
                TrendDirection.DECLINING: f"质量评分下降{abs(change_pct):.1f}%，建议审查输出模板和验证逻辑",
                TrendDirection.STABLE: "质量评分稳定，可探索提升空间",
            },
            "memory_mb": {
                TrendDirection.IMPROVING: "内存使用效率提升",
                TrendDirection.DECLINING: f"内存占用增加{abs(change_pct):.1f}%，检查是否存在内存泄漏",
                TrendDirection.STABLE: "内存使用稳定",
            },
            "success_rate": {
                TrendDirection.IMPROVING: "任务成功率提升，系统稳定性增强",
                TrendDirection.DECLINING: f"成功率下降{abs(change_pct):.1f}%，需排查失败原因",
                TrendDirection.STABLE: "成功率稳定，关注边界情况",
            },
        }
        return recommendations.get(metric, {}).get(direction)


class PerformanceBenchmark:
    def __init__(self, history: PerformanceHistory | None = None):
        self._history = history or PerformanceHistory(max_records=100)
        self._scorer = OutputQualityScorer()

    def run_benchmark(
        self,
        task_fn: Any,
        task_type: str,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        metadata: dict[str, Any] | None = None,
    ) -> BenchmarkRecord:
        start_time = time.perf_counter()
        start_cpu = time.process_time()
        try:
            result = task_fn()
            success = True
        except Exception as e:
            result = str(e)
            success = False
        end_time = time.perf_counter()
        end_cpu = time.process_time()
        response_time_ms = (end_time - start_time) * 1000
        cpu_time_s = end_cpu - start_cpu
        output_str = str(result)
        quality = self._scorer.score_output(output_str, output_format)
        record = BenchmarkRecord(
            timestamp=datetime.now(timezone.utc),
            task_type=task_type,
            response_time_ms=round(response_time_ms, 2),
            quality_score=quality.overall,
            memory_mb=0.0,
            cpu_time_s=round(cpu_time_s, 4),
            success=success,
            metadata=metadata,
        )
        self._history.add_record(record)
        return record

    def generate_report(self) -> str:
        summary = self._history.generate_summary()
        lines: list[str] = []
        lines.append("# 性能基准测试报告")
        lines.append("")
        lines.append(f"> 报告时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        lines.append(f"> 记录总数: **{summary.total_records}** 条")
        lines.append("")
        lines.append("## 核心指标")
        lines.append("")
        lines.append("| 维度 | 指标 | 值 | 说明 |")
        lines.append("|------|------|------|------|")
        lines.append(f"| 响应时间 | 平均 | **{summary.avg_response_time:.2f} ms** | 所有任务的均值 |")
        lines.append(f"| 响应时间 | P50 | **{summary.p50_response_time:.2f} ms** | 中位数响应时间 |")
        lines.append(f"| 响应时间 | P99 | **{summary.p99_response_time:.2f} ms** | 99分位响应时间 |")
        lines.append(f"| 输出质量 | 综合评分 | **{summary.avg_quality_score:.2f}/5** | 多维度加权平均 |")
        lines.append(f"| 资源消耗 | CPU时间 | **{summary.avg_cpu_time_s:.4f} s** | 平均CPU消耗 |")
        lines.append(f"| 成功率 | 任务完成 | **{summary.success_rate:.1%}** | 成功/总执行数 |")
        lines.append("")
        if summary.total_records >= 2:
            lines.append("## 百分位分布")
            lines.append("")
            times_sorted = sorted(r.response_time_ms for r in self._history.all_records)
            percentiles = [("P50", 50), ("P75", 75), ("P90", 90), ("P95", 95), ("P99", 99)]
            lines.append("| 百分位 | 响应时间(ms) |")
            lines.append("|--------|-------------|")
            for label, pct in percentiles:
                idx = min(int(len(times_sorted) * pct / 100), len(times_sorted) - 1)
                lines.append(f"| {label} | {times_sorted[idx]:.2f} |")
            lines.append("")
        lines.append(self._history.generate_trend_report().split("\n", 1)[1])
        return "\n".join(lines)

    @property
    def history(self) -> PerformanceHistory:
        return self._history

    @property
    def scorer(self) -> OutputQualityScorer:
        return self._scorer
