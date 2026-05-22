#!/usr/bin/env python3
"""
优化历史追踪器
记录每次优化结果，生成优化趋势图，支持历史对比
"""

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict


@dataclass
class OptimizationRecord:
    timestamp: str
    optimization_type: str
    description: str
    coverage_before: float
    coverage_after: float
    performance_before: Dict[str, float]
    performance_after: Dict[str, float]
    quality_before: Dict[str, float]
    quality_after: Dict[str, float]
    success: bool
    details: str = ""


@dataclass
class TrendData:
    metric_name: str
    values: List[float]
    timestamps: List[str]
    trend: str
    improvement_rate: float


class HistoryTracker:
    def __init__(self):
        self.sanliu_root = Path(__file__).parent.parent
        self.history_dir = self.sanliu_root / "optimization_history"
        self.history_dir.mkdir(exist_ok=True)
        self.history_file = self.history_dir / "optimization_history.json"
        self.records: List[OptimizationRecord] = []
        self._load_history()
        
    def _load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.records = [OptimizationRecord(**r) for r in data.get("records", [])]
            except Exception:
                self.records = []
    
    def _save_history(self):
        data = {
            "records": [asdict(r) for r in self.records],
            "last_updated": datetime.now().isoformat(),
            "total_optimizations": len(self.records)
        }
        
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def record_optimization(
        self,
        optimization_type: str,
        description: str,
        coverage_before: float,
        coverage_after: float,
        performance_before: Dict[str, float],
        performance_after: Dict[str, float],
        quality_before: Dict[str, float],
        quality_after: Dict[str, float],
        success: bool,
        details: str = ""
    ) -> OptimizationRecord:
        print("\n" + "=" * 60)
        print("记录优化结果...")
        print("=" * 60)
        
        record = OptimizationRecord(
            timestamp=datetime.now().isoformat(),
            optimization_type=optimization_type,
            description=description,
            coverage_before=coverage_before,
            coverage_after=coverage_after,
            performance_before=performance_before,
            performance_after=performance_after,
            quality_before=quality_before,
            quality_after=quality_after,
            success=success,
            details=details
        )
        
        self.records.append(record)
        self._save_history()
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        record_file = self.history_dir / f"optimization_{timestamp_str}.json"
        with open(record_file, "w", encoding="utf-8") as f:
            json.dump(asdict(record), f, indent=2, ensure_ascii=False)
        
        print(f"优化记录已保存: {record_file}")
        self._print_record_summary(record)
        
        return record
    
    def _print_record_summary(self, record: OptimizationRecord):
        print(f"\n优化类型: {record.optimization_type}")
        print(f"描述: {record.description}")
        print(f"覆盖率变化: {record.coverage_before:.2f}% → {record.coverage_after:.2f}%")
        
        coverage_diff = record.coverage_after - record.coverage_before
        if coverage_diff > 0:
            print(f"  ↑ 提升 {coverage_diff:.2f}%")
        elif coverage_diff < 0:
            print(f"  ↓ 下降 {abs(coverage_diff):.2f}%")
        
        print(f"状态: {'✅ 成功' if record.success else '❌ 失败'}")
    
    def get_trend_data(self, metric_name: str, days: int = 30) -> TrendData:
        print(f"\n获取趋势数据: {metric_name}")
        
        values = []
        timestamps = []
        
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for record in self.records:
            record_time = datetime.fromisoformat(record.timestamp).timestamp()
            if record_time >= cutoff_date:
                if metric_name == "coverage":
                    values.append(record.coverage_after)
                    timestamps.append(record.timestamp)
                elif metric_name.startswith("perf_"):
                    endpoint = metric_name[5:]
                    if endpoint in record.performance_after:
                        values.append(record.performance_after[endpoint])
                        timestamps.append(record.timestamp)
                elif metric_name.startswith("quality_"):
                    metric = metric_name[8:]
                    if metric in record.quality_after:
                        values.append(record.quality_after[metric])
                        timestamps.append(record.timestamp)
        
        trend = "stable"
        improvement_rate = 0.0
        
        if len(values) >= 2:
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            
            first_avg = sum(first_half) / len(first_half) if first_half else 0
            second_avg = sum(second_half) / len(second_half) if second_half else 0
            
            if first_avg > 0:
                improvement_rate = ((second_avg - first_avg) / first_avg) * 100
            
            if improvement_rate > 5:
                trend = "improving"
            elif improvement_rate < -5:
                trend = "declining"
        
        return TrendData(
            metric_name=metric_name,
            values=values,
            timestamps=timestamps,
            trend=trend,
            improvement_rate=round(improvement_rate, 2)
        )
    
    def compare_with_previous(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        print("\n" + "=" * 60)
        print("历史对比分析...")
        print("=" * 60)
        
        comparison = {
            "has_previous": False,
            "coverage_change": 0,
            "performance_changes": {},
            "quality_changes": {},
            "recommendations": []
        }
        
        if not self.records:
            comparison["recommendations"].append("首次优化，建议建立基准数据")
            return comparison
        
        last_record = self.records[-1]
        comparison["has_previous"] = True
        
        current_coverage = current_data.get("coverage", 0)
        comparison["coverage_change"] = current_coverage - last_record.coverage_after
        
        for endpoint, current_time in current_data.get("performance", {}).items():
            prev_time = last_record.performance_after.get(endpoint, 0)
            if prev_time > 0:
                change = current_time - prev_time
                comparison["performance_changes"][endpoint] = {
                    "previous": prev_time,
                    "current": current_time,
                    "change": change,
                    "change_percent": (change / prev_time) * 100 if prev_time > 0 else 0
                }
        
        for metric, current_value in current_data.get("quality", {}).items():
            prev_value = last_record.quality_after.get(metric, 0)
            change = current_value - prev_value
            comparison["quality_changes"][metric] = {
                "previous": prev_value,
                "current": current_value,
                "change": change
            }
        
        comparison["recommendations"] = self._generate_recommendations(comparison)
        
        return comparison
    
    def _generate_recommendations(self, comparison: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        if comparison["coverage_change"] < 0:
            recommendations.append(f"覆盖率下降了 {abs(comparison['coverage_change']):.2f}%，建议补充测试用例")
        elif comparison["coverage_change"] > 5:
            recommendations.append(f"覆盖率提升了 {comparison['coverage_change']:.2f}%，继续保持")
        
        for endpoint, change_data in comparison["performance_changes"].items():
            if change_data["change_percent"] > 20:
                recommendations.append(f"{endpoint} 响应时间增加了 {change_data['change_percent']:.1f}%，建议优化")
            elif change_data["change_percent"] < -20:
                recommendations.append(f"{endpoint} 响应时间减少了 {abs(change_data['change_percent']):.1f}%，优化有效")
        
        for metric, change_data in comparison["quality_changes"].items():
            if metric in ["ruff_errors", "avg_complexity"]:
                if change_data["change"] > 0:
                    recommendations.append(f"{metric} 增加了 {change_data['change']}，建议修复")
            elif metric == "doc_coverage":
                if change_data["change"] < 0:
                    recommendations.append(f"文档覆盖率下降了 {abs(change_data['change']):.2f}%，建议补充文档")
        
        return recommendations
    
    def generate_trend_chart_data(self, metric_name: str = "coverage", days: int = 30) -> Dict[str, Any]:
        trend_data = self.get_trend_data(metric_name, days)
        
        chart_data = {
            "labels": [],
            "datasets": [{
                "label": metric_name,
                "data": [],
                "borderColor": "#667eea",
                "backgroundColor": "rgba(102, 126, 234, 0.1)",
                "fill": True
            }]
        }
        
        for i, (timestamp, value) in enumerate(zip(trend_data.timestamps, trend_data.values)):
            dt = datetime.fromisoformat(timestamp)
            chart_data["labels"].append(dt.strftime("%m-%d %H:%M"))
            chart_data["datasets"][0]["data"].append(value)
        
        return {
            "chart_data": chart_data,
            "trend": trend_data.trend,
            "improvement_rate": trend_data.improvement_rate,
            "metric_name": metric_name
        }
    
    def generate_history_report(self, days: int = 30) -> str:
        print("\n" + "=" * 60)
        print("生成优化历史报告...")
        print("=" * 60)
        
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        recent_records = [
            r for r in self.records
            if datetime.fromisoformat(r.timestamp).timestamp() >= cutoff_date
        ]
        
        report_lines = [
            f"# 三省六部技能优化历史报告",
            f"",
            f"**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**统计周期**: 最近 {days} 天",
            f"**优化次数**: {len(recent_records)}",
            f"",
            "## 优化概览",
            "",
        ]
        
        if recent_records:
            successful = sum(1 for r in recent_records if r.success)
            report_lines.append(f"- 成功优化: {successful} 次")
            report_lines.append(f"- 失败优化: {len(recent_records) - successful} 次")
            
            coverage_improvements = [
                r.coverage_after - r.coverage_before
                for r in recent_records
            ]
            avg_coverage_change = sum(coverage_improvements) / len(coverage_improvements) if coverage_improvements else 0
            report_lines.append(f"- 平均覆盖率变化: {avg_coverage_change:+.2f}%")
        
        report_lines.extend([
            "",
            "## 详细记录",
            "",
        ])
        
        for record in reversed(recent_records[-10:]):
            dt = datetime.fromisoformat(record.timestamp)
            status = "✅" if record.success else "❌"
            report_lines.append(f"### {dt.strftime('%Y-%m-%d %H:%M')} - {record.optimization_type} {status}")
            report_lines.append(f"")
            report_lines.append(f"**描述**: {record.description}")
            report_lines.append(f"")
            report_lines.append(f"| 指标 | 优化前 | 优化后 | 变化 |")
            report_lines.append(f"|------|--------|--------|------|")
            
            coverage_change = record.coverage_after - record.coverage_before
            report_lines.append(f"| 覆盖率 | {record.coverage_before:.2f}% | {record.coverage_after:.2f}% | {coverage_change:+.2f}% |")
            
            for endpoint, after_time in record.performance_after.items():
                before_time = record.performance_before.get(endpoint, 0)
                change = after_time - before_time
                report_lines.append(f"| {endpoint} | {before_time:.2f}ms | {after_time:.2f}ms | {change:+.2f}ms |")
            
            report_lines.append(f"")
        
        report_lines.extend([
            "",
            "## 趋势分析",
            "",
        ])
        
        for metric in ["coverage", "perf_/api/projects", "quality_avg_complexity"]:
            trend_data = self.get_trend_data(metric, days)
            trend_emoji = "📈" if trend_data.trend == "improving" else "📉" if trend_data.trend == "declining" else "➡️"
            report_lines.append(f"- **{metric}**: {trend_emoji} {trend_data.trend} ({trend_data.improvement_rate:+.2f}%)")
        
        report_content = "\n".join(report_lines)
        
        report_file = self.history_dir / f"history_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        print(f"历史报告已生成: {report_file}")
        return report_content
    
    def get_statistics(self) -> Dict[str, Any]:
        if not self.records:
            return {
                "total_optimizations": 0,
                "successful_optimizations": 0,
                "failed_optimizations": 0,
                "success_rate": 0,
                "average_coverage_improvement": 0
            }
        
        successful = sum(1 for r in self.records if r.success)
        coverage_changes = [r.coverage_after - r.coverage_before for r in self.records]
        
        return {
            "total_optimizations": len(self.records),
            "successful_optimizations": successful,
            "failed_optimizations": len(self.records) - successful,
            "success_rate": round((successful / len(self.records)) * 100, 2),
            "average_coverage_improvement": round(sum(coverage_changes) / len(coverage_changes), 2) if coverage_changes else 0
        }
    
    def export_history(self, format: str = "json", output_path: Optional[str] = None) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            export_file = self.history_dir / f"history_export_{timestamp}.json"
            data = {
                "records": [asdict(r) for r in self.records],
                "statistics": self.get_statistics(),
                "exported_at": datetime.now().isoformat()
            }
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format == "csv":
            import csv
            export_file = self.history_dir / f"history_export_{timestamp}.csv"
            with open(export_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "type", "description", "coverage_before", "coverage_after",
                    "success", "details"
                ])
                for r in self.records:
                    writer.writerow([
                        r.timestamp, r.optimization_type, r.description,
                        r.coverage_before, r.coverage_after, r.success, r.details
                    ])
        else:
            export_file = self.history_dir / f"history_export_{timestamp}.txt"
            with open(export_file, "w", encoding="utf-8") as f:
                for r in self.records:
                    f.write(f"{r.timestamp} | {r.optimization_type} | {r.description} | {r.success}\n")
        
        print(f"历史数据已导出: {export_file}")
        return str(export_file)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="优化历史追踪器")
    parser.add_argument("--report", action="store_true", help="生成历史报告")
    parser.add_argument("--trend", type=str, metavar="METRIC", help="获取指定指标的趋势")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")
    parser.add_argument("--export", type=str, choices=["json", "csv", "txt"], help="导出历史数据")
    parser.add_argument("--days", type=int, default=30, help="统计天数")
    
    args = parser.parse_args()
    
    tracker = HistoryTracker()
    
    if args.report:
        tracker.generate_history_report(args.days)
    elif args.trend:
        trend_data = tracker.get_trend_data(args.trend, args.days)
        print(f"\n指标: {trend_data.metric_name}")
        print(f"趋势: {trend_data.trend}")
        print(f"改进率: {trend_data.improvement_rate}%")
        print(f"数据点: {len(trend_data.values)}")
    elif args.stats:
        stats = tracker.get_statistics()
        print("\n优化统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    elif args.export:
        tracker.export_history(args.export)
    else:
        tracker.generate_history_report(args.days)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
