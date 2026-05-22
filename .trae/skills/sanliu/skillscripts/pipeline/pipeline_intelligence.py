#!/usr/bin/env python3
"""
流水线智能执行增强模块 - Sanliu 技能

功能：
- 智能测试选择和优先级排序
- 失败预测和风险评估
- 自适应超时控制
- 智能重试策略
- 资源优化分配
- 流水线状态监控增强
- 流水线报告增强

使用方法：
    python scripts/pipeline_intelligence.py --analyze
    python scripts/pipeline_intelligence.py --predict-failures
    python scripts/pipeline_intelligence.py --optimize-order
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional
import hashlib
import re


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline_intelligence.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TestPriority(Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


@dataclass
class TestHistory:
    test_name: str
    total_runs: int = 0
    passed_runs: int = 0
    failed_runs: int = 0
    avg_duration: float = 0.0
    last_run: Optional[datetime] = None
    last_status: str = "unknown"
    flaky_score: float = 0.0
    failure_patterns: list[str] = field(default_factory=list)


@dataclass
class FailurePrediction:
    test_name: str
    risk_level: RiskLevel
    confidence: float
    reasons: list[str]
    recommendations: list[str]


@dataclass
class PipelineMetrics:
    total_duration: float = 0.0
    avg_stage_duration: dict[str, float] = field(default_factory=dict)
    success_rate: float = 0.0
    failure_rate: float = 0.0
    resource_usage: dict[str, float] = field(default_factory=dict)


class TestHistoryAnalyzer:
    """测试历史分析器"""

    def __init__(self, history_file: Path = None):
        self.history_file = history_file or Path("test_history.json")
        self.history: dict[str, TestHistory] = {}
        self._load_history()

    def _load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for name, info in data.items():
                    self.history[name] = TestHistory(
                        test_name=name,
                        total_runs=info.get('total_runs', 0),
                        passed_runs=info.get('passed_runs', 0),
                        failed_runs=info.get('failed_runs', 0),
                        avg_duration=info.get('avg_duration', 0.0),
                        last_run=datetime.fromisoformat(info['last_run']) if info.get('last_run') else None,
                        last_status=info.get('last_status', 'unknown'),
                        flaky_score=info.get('flaky_score', 0.0),
                        failure_patterns=info.get('failure_patterns', [])
                    )
            except Exception as e:
                logger.warning(f"加载测试历史失败: {e}")

    def _save_history(self):
        data = {}
        for name, hist in self.history.items():
            data[name] = {
                'total_runs': hist.total_runs,
                'passed_runs': hist.passed_runs,
                'failed_runs': hist.failed_runs,
                'avg_duration': hist.avg_duration,
                'last_run': hist.last_run.isoformat() if hist.last_run else None,
                'last_status': hist.last_status,
                'flaky_score': hist.flaky_score,
                'failure_patterns': hist.failure_patterns
            }
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def record_test_result(self, test_name: str, passed: bool, duration: float, error_pattern: str = None):
        if test_name not in self.history:
            self.history[test_name] = TestHistory(test_name=test_name)

        hist = self.history[test_name]
        hist.total_runs += 1
        if passed:
            hist.passed_runs += 1
        else:
            hist.failed_runs += 1
            if error_pattern and error_pattern not in hist.failure_patterns:
                hist.failure_patterns.append(error_pattern)

        hist.avg_duration = (hist.avg_duration * (hist.total_runs - 1) + duration) / hist.total_runs
        hist.last_run = datetime.now()
        hist.last_status = "passed" if passed else "failed"

        if hist.total_runs >= 3:
            pass_rate = hist.passed_runs / hist.total_runs
            hist.flaky_score = 1 - abs(pass_rate - 0.5) * 2

        self._save_history()

    def get_flaky_tests(self, threshold: float = 0.3) -> list[str]:
        return [
            name for name, hist in self.history.items()
            if hist.flaky_score > threshold
        ]

    def get_slow_tests(self, threshold_seconds: float = 30.0) -> list[str]:
        return [
            name for name, hist in self.history.items()
            if hist.avg_duration > threshold_seconds
        ]


class FailurePredictor:
    """失败预测器"""

    def __init__(self, history_analyzer: TestHistoryAnalyzer):
        self.history = history_analyzer

    def predict_failures(self, tests: list[str] = None) -> list[FailurePrediction]:
        predictions = []
        test_names = tests or list(self.history.history.keys())

        for test_name in test_names:
            hist = self.history.history.get(test_name)
            if not hist:
                continue

            risk_level = RiskLevel.LOW
            confidence = 0.0
            reasons = []
            recommendations = []

            if hist.total_runs >= 3:
                fail_rate = hist.failed_runs / hist.total_runs

                if fail_rate > 0.5:
                    risk_level = RiskLevel.HIGH
                    confidence = min(0.9, fail_rate)
                    reasons.append(f"历史失败率高 ({fail_rate:.1%})")
                    recommendations.append("检查测试稳定性，考虑重写或禁用")

                elif fail_rate > 0.2:
                    risk_level = RiskLevel.MEDIUM
                    confidence = fail_rate
                    reasons.append(f"历史失败率中等 ({fail_rate:.1%})")
                    recommendations.append("关注测试执行，准备备用方案")

                if hist.flaky_score > 0.3:
                    if risk_level == RiskLevel.LOW:
                        risk_level = RiskLevel.MEDIUM
                    reasons.append(f"测试不稳定 (flaky score: {hist.flaky_score:.2f})")
                    recommendations.append("考虑添加重试机制")

                if hist.avg_duration > 60:
                    reasons.append(f"执行时间较长 ({hist.avg_duration:.1f}s)")
                    recommendations.append("考虑优化测试或增加超时时间")

                if hist.failure_patterns:
                    reasons.append(f"已知失败模式: {len(hist.failure_patterns)} 种")
                    recommendations.append("检查已知失败模式")

            if hist.last_status == "failed":
                if risk_level == RiskLevel.LOW:
                    risk_level = RiskLevel.MEDIUM
                confidence = max(confidence, 0.5)
                reasons.append("上次执行失败")

            predictions.append(FailurePrediction(
                test_name=test_name,
                risk_level=risk_level,
                confidence=confidence,
                reasons=reasons,
                recommendations=recommendations
            ))

        return predictions

    def get_risk_summary(self, predictions: list[FailurePrediction]) -> dict[str, Any]:
        summary = {
            "total_tests": len(predictions),
            "by_risk": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            },
            "high_risk_tests": [],
            "recommendations": []
        }

        for pred in predictions:
            summary["by_risk"][pred.risk_level.value] += 1
            if pred.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                summary["high_risk_tests"].append(pred.test_name)
                summary["recommendations"].extend(pred.recommendations)

        summary["recommendations"] = list(set(summary["recommendations"]))
        return summary


class TestOrderOptimizer:
    """测试顺序优化器"""

    def __init__(self, history_analyzer: TestHistoryAnalyzer):
        self.history = history_analyzer

    def optimize_order(self, tests: list[str], strategy: str = "balanced") -> list[str]:
        if not tests:
            return tests

        if strategy == "fail_first":
            return self._order_by_failure_risk(tests)
        elif strategy == "fast_first":
            return self._order_by_speed(tests)
        elif strategy == "balanced":
            return self._order_balanced(tests)
        else:
            return tests

    def _order_by_failure_risk(self, tests: list[str]) -> list[str]:
        def risk_score(test_name: str) -> float:
            hist = self.history.history.get(test_name)
            if not hist or hist.total_runs == 0:
                return 0.5
            return hist.failed_runs / hist.total_runs

        return sorted(tests, key=risk_score, reverse=True)

    def _order_by_speed(self, tests: list[str]) -> list[str]:
        def speed_score(test_name: str) -> float:
            hist = self.history.history.get(test_name)
            if not hist:
                return 0.0
            return hist.avg_duration

        return sorted(tests, key=speed_score)

    def _order_balanced(self, tests: list[str]) -> list[str]:
        def balanced_score(test_name: str) -> float:
            hist = self.history.history.get(test_name)
            if not hist or hist.total_runs == 0:
                return 0.0

            fail_rate = hist.failed_runs / hist.total_runs
            speed_factor = min(1.0, hist.avg_duration / 60.0)

            return fail_rate * 0.7 + speed_factor * 0.3

        return sorted(tests, key=balanced_score, reverse=True)


class AdaptiveTimeoutController:
    """自适应超时控制器"""

    def __init__(self, history_analyzer: TestHistoryAnalyzer):
        self.history = history_analyzer
        self.default_timeout = 300
        self.max_timeout = 1800
        self.min_timeout = 30

    def get_timeout(self, test_name: str, percentile: float = 0.95) -> int:
        hist = self.history.history.get(test_name)
        if not hist or hist.total_runs < 3:
            return self.default_timeout

        base_timeout = hist.avg_duration * (1 + percentile)

        if hist.flaky_score > 0.3:
            base_timeout *= 1.5

        if hist.failed_runs > hist.passed_runs:
            base_timeout *= 1.2

        return int(min(self.max_timeout, max(self.min_timeout, base_timeout)))


class SmartRetryStrategy:
    """智能重试策略"""

    def __init__(self, history_analyzer: TestHistoryAnalyzer):
        self.history = history_analyzer
        self.max_retries = 3

    def should_retry(self, test_name: str, attempt: int, last_error: str = None) -> bool:
        if attempt >= self.max_retries:
            return False

        hist = self.history.history.get(test_name)
        if not hist:
            return True

        if hist.flaky_score > 0.3:
            return attempt < self.max_retries

        if last_error and any(pattern in last_error for pattern in ["timeout", "connection", "network"]):
            return attempt < 2

        return attempt < 1

    def get_retry_delay(self, test_name: str, attempt: int) -> float:
        hist = self.history.history.get(test_name)
        base_delay = 1.0

        if hist and hist.flaky_score > 0.3:
            base_delay = 2.0

        return base_delay * (2 ** (attempt - 1))


class PipelineStatusMonitorEnhanced:
    """流水线状态监控增强"""

    def __init__(self, output_dir: Path = None):
        if output_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                self.output_dir = _path_mgr.get_output_path(OutputType.REPORT, subdirectory="monitoring")
            except Exception:
                self.output_dir = get_path_config().REPORTS_DIR / "monitoring"
        else:
            self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = self.output_dir / "pipeline_status.json"
        self.metrics_file = self.output_dir / "pipeline_metrics.json"
        self.status: dict[str, Any] = {}
        self.metrics_history: list[dict[str, Any]] = []
        self._load_status()

    def _load_status(self):
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    self.status = json.load(f)
            except Exception:
                self.status = {}

        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    self.metrics_history = json.load(f)
            except Exception:
                self.metrics_history = []

    def _save_status(self):
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status, f, indent=2, ensure_ascii=False)

        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(self.metrics_history[-100:], f, indent=2, ensure_ascii=False)

    def start_pipeline(self, pipeline_id: str, config: dict[str, Any]):
        self.status = {
            "pipeline_id": pipeline_id,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "config": config,
            "stages": {},
            "current_stage": None,
            "errors": [],
            "warnings": []
        }
        self._save_status()

    def update_stage(self, stage_name: str, status: str, metrics: dict[str, Any] = None):
        if "stages" not in self.status:
            self.status["stages"] = {}

        self.status["stages"][stage_name] = {
            "status": status,
            "start_time": datetime.now().isoformat(),
            "metrics": metrics or {}
        }
        self.status["current_stage"] = stage_name
        self._save_status()

    def complete_stage(self, stage_name: str, success: bool, duration: float, output: dict[str, Any] = None):
        if stage_name in self.status.get("stages", {}):
            self.status["stages"][stage_name]["end_time"] = datetime.now().isoformat()
            self.status["stages"][stage_name]["duration"] = duration
            self.status["stages"][stage_name]["success"] = success
            self.status["stages"][stage_name]["output"] = output or {}

        self._save_status()

    def add_error(self, stage: str, error: str):
        self.status.setdefault("errors", []).append({
            "stage": stage,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        self._save_status()

    def add_warning(self, stage: str, warning: str):
        self.status.setdefault("warnings", []).append({
            "stage": stage,
            "warning": warning,
            "timestamp": datetime.now().isoformat()
        })
        self._save_status()

    def complete_pipeline(self, success: bool, summary: dict[str, Any]):
        self.status["status"] = "completed" if success else "failed"
        self.status["end_time"] = datetime.now().isoformat()
        self.status["success"] = success
        self.status["summary"] = summary

        if "start_time" in self.status:
            start = datetime.fromisoformat(self.status["start_time"])
            self.status["total_duration"] = (datetime.now() - start).total_seconds()

        self.metrics_history.append({
            "pipeline_id": self.status.get("pipeline_id"),
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "duration": self.status.get("total_duration", 0),
            "stages_count": len(self.status.get("stages", {})),
            "errors_count": len(self.status.get("errors", [])),
            "warnings_count": len(self.status.get("warnings", []))
        })

        self._save_status()

    def get_real_time_status(self) -> dict[str, Any]:
        return {
            "pipeline_id": self.status.get("pipeline_id"),
            "status": self.status.get("status"),
            "current_stage": self.status.get("current_stage"),
            "start_time": self.status.get("start_time"),
            "stages_completed": len([s for s in self.status.get("stages", {}).values() if s.get("end_time")]),
            "stages_total": len(self.status.get("stages", {})),
            "errors_count": len(self.status.get("errors", [])),
            "warnings_count": len(self.status.get("warnings", []))
        }

    def get_historical_analysis(self, days: int = 30) -> dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        recent_runs = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m["timestamp"]) >= cutoff
        ]

        if not recent_runs:
            return {"message": "No historical data available"}

        total_runs = len(recent_runs)
        successful_runs = sum(1 for r in recent_runs if r["success"])
        avg_duration = sum(r["duration"] for r in recent_runs) / total_runs

        return {
            "period_days": days,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": successful_runs / total_runs if total_runs > 0 else 0,
            "avg_duration": avg_duration,
            "avg_errors": sum(r["errors_count"] for r in recent_runs) / total_runs,
            "avg_warnings": sum(r["warnings_count"] for r in recent_runs) / total_runs
        }

    def get_trend_analysis(self, days: int = 30) -> dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        recent_runs = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m["timestamp"]) >= cutoff
        ]

        if len(recent_runs) < 2:
            return {"message": "Insufficient data for trend analysis"}

        recent_runs.sort(key=lambda x: x["timestamp"])

        first_half = recent_runs[:len(recent_runs) // 2]
        second_half = recent_runs[len(recent_runs) // 2:]

        def calc_stats(runs):
            return {
                "success_rate": sum(1 for r in runs if r["success"]) / len(runs) if runs else 0,
                "avg_duration": sum(r["duration"] for r in runs) / len(runs) if runs else 0,
                "avg_errors": sum(r["errors_count"] for r in runs) / len(runs) if runs else 0
            }

        first_stats = calc_stats(first_half)
        second_stats = calc_stats(second_half)

        return {
            "period_days": days,
            "first_half": first_stats,
            "second_half": second_stats,
            "trends": {
                "success_rate": second_stats["success_rate"] - first_stats["success_rate"],
                "duration": second_stats["avg_duration"] - first_stats["avg_duration"],
                "errors": second_stats["avg_errors"] - first_stats["avg_errors"]
            },
            "interpretation": self._interpret_trends(first_stats, second_stats)
        }

    def _interpret_trends(self, first: dict, second: dict) -> list[str]:
        interpretations = []

        if second["success_rate"] > first["success_rate"]:
            interpretations.append("成功率呈上升趋势")
        elif second["success_rate"] < first["success_rate"]:
            interpretations.append("成功率呈下降趋势，需要关注")

        if second["avg_duration"] > first["avg_duration"] * 1.1:
            interpretations.append("执行时间增加，可能存在性能问题")
        elif second["avg_duration"] < first["avg_duration"] * 0.9:
            interpretations.append("执行时间减少，性能有所改善")

        if second["avg_errors"] > first["avg_errors"]:
            interpretations.append("错误数量增加，需要排查问题")

        return interpretations


class PipelineReportEnhancer:
    """流水线报告增强"""

    def __init__(self, monitor: PipelineStatusMonitorEnhanced):
        self.monitor = monitor

    def generate_enhanced_report(self) -> dict[str, Any]:
        status = self.monitor.status
        historical = self.monitor.get_historical_analysis()
        trends = self.monitor.get_trend_analysis()

        report = {
            "metadata": {
                "pipeline_id": status.get("pipeline_id"),
                "generated_at": datetime.now().isoformat(),
                "report_version": "2.0"
            },
            "execution_summary": {
                "status": status.get("status"),
                "success": status.get("success", False),
                "start_time": status.get("start_time"),
                "end_time": status.get("end_time"),
                "total_duration": status.get("total_duration", 0)
            },
            "stages": status.get("stages", {}),
            "issues": {
                "errors": status.get("errors", []),
                "warnings": status.get("warnings", [])
            },
            "historical_context": historical,
            "trend_analysis": trends,
            "recommendations": self._generate_recommendations(status, trends)
        }

        return report

    def _generate_recommendations(self, status: dict, trends: dict) -> list[str]:
        recommendations = []

        if status.get("errors"):
            recommendations.append("检查并修复报告中的错误")

        if trends.get("trends", {}).get("success_rate", 0) < 0:
            recommendations.append("成功率下降，建议检查最近的代码变更")

        if trends.get("trends", {}).get("duration", 0) > 0:
            recommendations.append("执行时间增加，建议进行性能优化")

        slow_stages = [
            name for name, stage in status.get("stages", {}).items()
            if stage.get("duration", 0) > 300
        ]
        if slow_stages:
            recommendations.append(f"以下阶段执行时间较长: {', '.join(slow_stages)}")

        return recommendations

    def save_report(self, output_path: Path = None):
        report = self.generate_enhanced_report()

        output_path = output_path or self.monitor.output_dir / f"enhanced_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"增强报告已保存: {output_path}")
        return output_path


def main():
    parser = argparse.ArgumentParser(description="流水线智能执行增强模块")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    parser_analyze = subparsers.add_parser("analyze", help="分析测试历史")
    parser_analyze.add_argument("--flaky-threshold", type=float, default=0.3, help="不稳定测试阈值")

    parser_predict = subparsers.add_parser("predict", help="预测失败风险")
    parser_predict.add_argument("--tests", nargs="+", help="指定测试列表")

    parser_optimize = subparsers.add_parser("optimize", help="优化测试顺序")
    parser_optimize.add_argument("--tests", nargs="+", required=True, help="测试列表")
    parser_optimize.add_argument("--strategy", choices=["fail_first", "fast_first", "balanced"], default="balanced", help="排序策略")

    parser_status = subparsers.add_parser("status", help="获取流水线状态")
    parser_status.add_argument("--history-days", type=int, default=30, help="历史分析天数")

    parser_report = subparsers.add_parser("report", help="生成增强报告")
    parser_report.add_argument("--output", type=Path, help="输出路径")

    args = parser.parse_args()

    history_analyzer = TestHistoryAnalyzer()

    if args.command == "analyze":
        flaky_tests = history_analyzer.get_flaky_tests(args.flaky_threshold)
        slow_tests = history_analyzer.get_slow_tests()

        print("\n" + "=" * 60)
        print("测试历史分析")
        print("=" * 60)
        print(f"总测试数: {len(history_analyzer.history)}")
        print(f"不稳定测试: {len(flaky_tests)}")
        print(f"慢测试: {len(slow_tests)}")

        if flaky_tests:
            print("\n不稳定测试列表:")
            for test in flaky_tests[:10]:
                hist = history_analyzer.history[test]
                print(f"  - {test}: flaky score = {hist.flaky_score:.2f}")

        if slow_tests:
            print("\n慢测试列表:")
            for test in slow_tests[:10]:
                hist = history_analyzer.history[test]
                print(f"  - {test}: avg duration = {hist.avg_duration:.1f}s")

    elif args.command == "predict":
        predictor = FailurePredictor(history_analyzer)
        predictions = predictor.predict_failures(args.tests)
        summary = predictor.get_risk_summary(predictions)

        print("\n" + "=" * 60)
        print("失败风险预测")
        print("=" * 60)
        print(f"总测试数: {summary['total_tests']}")
        print(f"高风险测试: {len(summary['high_risk_tests'])}")
        print(f"\n风险分布:")
        for level, count in summary["by_risk"].items():
            print(f"  {level}: {count}")

        if summary["recommendations"]:
            print("\n建议:")
            for rec in summary["recommendations"]:
                print(f"  - {rec}")

    elif args.command == "optimize":
        optimizer = TestOrderOptimizer(history_analyzer)
        optimized = optimizer.optimize_order(args.tests, args.strategy)

        print("\n" + "=" * 60)
        print(f"测试顺序优化 (策略: {args.strategy})")
        print("=" * 60)
        for i, test in enumerate(optimized, 1):
            hist = history_analyzer.history.get(test)
            if hist:
                print(f"  {i}. {test} (fail rate: {hist.failed_runs/hist.total_runs:.1%}, avg: {hist.avg_duration:.1f}s)")
            else:
                print(f"  {i}. {test} (无历史数据)")

    elif args.command == "status":
        monitor = PipelineStatusMonitorEnhanced()
        current = monitor.get_real_time_status()
        historical = monitor.get_historical_analysis(args.history_days)
        trends = monitor.get_trend_analysis(args.history_days)

        print("\n" + "=" * 60)
        print("流水线状态")
        print("=" * 60)
        print(f"Pipeline ID: {current.get('pipeline_id', 'N/A')}")
        print(f"状态: {current.get('status', 'N/A')}")
        print(f"当前阶段: {current.get('current_stage', 'N/A')}")
        print(f"错误数: {current.get('errors_count', 0)}")
        print(f"警告数: {current.get('warnings_count', 0)}")

        print("\n" + "=" * 60)
        print(f"历史分析 (最近 {args.history_days} 天)")
        print("=" * 60)
        print(f"总运行次数: {historical.get('total_runs', 0)}")
        print(f"成功率: {historical.get('success_rate', 0):.1%}")
        print(f"平均耗时: {historical.get('avg_duration', 0):.1f}s")

        if trends.get("interpretation"):
            print("\n趋势解读:")
            for interp in trends["interpretation"]:
                print(f"  - {interp}")

    elif args.command == "report":
        monitor = PipelineStatusMonitorEnhanced()
        enhancer = PipelineReportEnhancer(monitor)
        output_path = enhancer.save_report(args.output)

        print("\n" + "=" * 60)
        print("增强报告已生成")
        print("=" * 60)
        print(f"输出路径: {output_path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
