#!/usr/bin/env python3
"""
基准数据更新器
更新覆盖率基准、性能基准和代码质量基准
"""

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from xml.etree import ElementTree


@dataclass
class CoverageBenchmark:
    line_rate: float
    branch_rate: float
    timestamp: str
    files: Dict[str, float] = field(default_factory=dict)


@dataclass
class PerformanceBenchmark:
    endpoint: str
    avg_ms: float
    p95_ms: float
    p99_ms: float
    timestamp: str


@dataclass
class QualityBenchmark:
    metric_name: str
    value: float
    timestamp: str


@dataclass
class BenchmarkData:
    coverage: CoverageBenchmark
    performance: List[PerformanceBenchmark] = field(default_factory=list)
    quality: List[QualityBenchmark] = field(default_factory=list)
    last_updated: str = ""


class BenchmarkUpdater:
    def __init__(self):
        self.sanliu_root = Path(__file__).parent.parent
        self.backend_dir = self.sanliu_root / "backend"
        self.frontend_dir = self.sanliu_root / "frontend"
        self.benchmarks_dir = self.sanliu_root / "benchmarks"
        self.benchmarks_dir.mkdir(exist_ok=True)
        self.benchmark_file = self.benchmarks_dir / "benchmark_data.json"
        
    def _load_existing_benchmark(self) -> BenchmarkData:
        if self.benchmark_file.exists():
            try:
                with open(self.benchmark_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                coverage = CoverageBenchmark(
                    line_rate=data.get("coverage", {}).get("line_rate", 0),
                    branch_rate=data.get("coverage", {}).get("branch_rate", 0),
                    timestamp=data.get("coverage", {}).get("timestamp", ""),
                    files=data.get("coverage", {}).get("files", {})
                )
                
                performance = [
                    PerformanceBenchmark(**p) for p in data.get("performance", [])
                ]
                
                quality = [
                    QualityBenchmark(**q) for q in data.get("quality", [])
                ]
                
                return BenchmarkData(
                    coverage=coverage,
                    performance=performance,
                    quality=quality,
                    last_updated=data.get("last_updated", "")
                )
            except Exception:
                pass
        
        return BenchmarkData(
            coverage=CoverageBenchmark(line_rate=0, branch_rate=0, timestamp=""),
            last_updated=""
        )
    
    def _save_benchmark(self, data: BenchmarkData):
        json_data = {
            "coverage": asdict(data.coverage),
            "performance": [asdict(p) for p in data.performance],
            "quality": [asdict(q) for q in data.quality],
            "last_updated": data.last_updated
        }
        
        with open(self.benchmark_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_file = self.benchmarks_dir / f"benchmark_{timestamp}.json"
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"基准数据已保存: {self.benchmark_file}")
    
    def update_coverage_benchmark(self) -> CoverageBenchmark:
        print("\n" + "=" * 60)
        print("更新覆盖率基准...")
        print("=" * 60)
        
        benchmark = CoverageBenchmark(
            line_rate=0,
            branch_rate=0,
            timestamp=datetime.now().isoformat()
        )
        
        coverage_file = self.backend_dir / "coverage.xml"
        if coverage_file.exists():
            tree = ElementTree.parse(coverage_file)
            root = tree.getroot()
            
            benchmark.line_rate = float(root.attrib.get("line-rate", 0)) * 100
            benchmark.branch_rate = float(root.attrib.get("branch-rate", 0)) * 100
            
            packages = root.findall(".//package")
            for package in packages:
                pkg_name = package.attrib.get("name", "")
                classes = package.findall("classes/class")
                for cls in classes:
                    filename = cls.attrib.get("filename", "")
                    file_line_rate = float(cls.attrib.get("line-rate", 0)) * 100
                    key = f"{pkg_name}/{filename}" if pkg_name else filename
                    benchmark.files[key] = round(file_line_rate, 2)
        
        print(f"覆盖率基准更新: {benchmark.line_rate:.2f}%")
        return benchmark
    
    def update_performance_benchmark(self) -> List[PerformanceBenchmark]:
        print("\n" + "=" * 60)
        print("更新性能基准...")
        print("=" * 60)
        
        benchmarks = []
        timestamp = datetime.now().isoformat()
        
        benchmark_file = self.backend_dir / "scripts" / "performance_report.md"
        if benchmark_file.exists():
            with open(benchmark_file, "r", encoding="utf-8") as f:
                content = f.read()
                benchmarks = self._parse_performance_report(content, timestamp)
        
        if not benchmarks:
            benchmarks = self._get_default_performance_benchmarks(timestamp)
        
        print(f"性能基准更新: {len(benchmarks)} 个端点")
        return benchmarks
    
    def _parse_performance_report(self, content: str, timestamp: str) -> List[PerformanceBenchmark]:
        benchmarks = []
        lines = content.split("\n")
        
        in_api_section = False
        for line in lines:
            if "API响应时间基准" in line:
                in_api_section = True
                continue
            if in_api_section and line.startswith("##"):
                break
            
            if in_api_section and line.startswith("| /"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 8:
                    endpoint = parts[1]
                    try:
                        avg_ms = float(parts[3])
                        p50_ms = float(parts[4])
                        p95_ms = float(parts[5])
                        p99_ms = float(parts[6])
                        
                        benchmarks.append(PerformanceBenchmark(
                            endpoint=endpoint,
                            avg_ms=avg_ms,
                            p95_ms=p95_ms,
                            p99_ms=p99_ms,
                            timestamp=timestamp
                        ))
                    except ValueError:
                        pass
        
        return benchmarks
    
    def _get_default_performance_benchmarks(self, timestamp: str) -> List[PerformanceBenchmark]:
        return [
            PerformanceBenchmark("/api/projects", 15.0, 25.0, 35.0, timestamp),
            PerformanceBenchmark("/api/tasks", 12.0, 20.0, 30.0, timestamp),
            PerformanceBenchmark("/api/agents", 8.0, 15.0, 20.0, timestamp),
            PerformanceBenchmark("/api/dashboard/stats", 25.0, 45.0, 60.0, timestamp),
            PerformanceBenchmark("/api/skill_calls", 10.0, 18.0, 25.0, timestamp),
        ]
    
    def update_quality_benchmark(self) -> List[QualityBenchmark]:
        print("\n" + "=" * 60)
        print("更新代码质量基准...")
        print("=" * 60)
        
        benchmarks = []
        timestamp = datetime.now().isoformat()
        
        ruff_errors = self._count_ruff_errors()
        benchmarks.append(QualityBenchmark(
            metric_name="ruff_errors",
            value=ruff_errors,
            timestamp=timestamp
        ))
        
        avg_complexity = self._calculate_avg_complexity()
        benchmarks.append(QualityBenchmark(
            metric_name="avg_complexity",
            value=avg_complexity,
            timestamp=timestamp
        ))
        
        doc_coverage = self._calculate_doc_coverage()
        benchmarks.append(QualityBenchmark(
            metric_name="doc_coverage",
            value=doc_coverage,
            timestamp=timestamp
        ))
        
        print(f"代码质量基准更新: {len(benchmarks)} 个指标")
        return benchmarks
    
    def _count_ruff_errors(self) -> int:
        import subprocess
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", ".", "--output-format=json"],
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                shell=sys.platform == "win32"
            )
            
            if result.stdout.strip():
                issues = json.loads(result.stdout)
                return len([i for i in issues if i.get("fix") is None])
        except Exception:
            pass
        return 0
    
    def _calculate_avg_complexity(self) -> float:
        total_complexity = 0
        file_count = 0
        
        for py_file in self.backend_dir.glob("app/**/*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    complexity = 1
                    keywords = ["if ", "elif ", "else:", "for ", "while ", "try:", "except", "with ", "and ", "or "]
                    for keyword in keywords:
                        complexity += content.count(keyword)
                    total_complexity += complexity
                    file_count += 1
            except Exception:
                pass
        
        return round(total_complexity / file_count, 2) if file_count > 0 else 0
    
    def _calculate_doc_coverage(self) -> float:
        total_functions = 0
        documented_functions = 0
        
        for py_file in self.backend_dir.glob("app/**/*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")
                    
                    for i, line in enumerate(lines):
                        if line.strip().startswith("def "):
                            total_functions += 1
                            if i > 0 and '"""' in lines[i - 1]:
                                documented_functions += 1
            except Exception:
                pass
        
        return round((documented_functions / total_functions * 100), 2) if total_functions > 0 else 0
    
    def update_all_benchmarks(self) -> BenchmarkData:
        print("=" * 60)
        print("三省六部技能基准数据更新器")
        print("=" * 60)
        
        existing = self._load_existing_benchmark()
        
        coverage = self.update_coverage_benchmark()
        performance = self.update_performance_benchmark()
        quality = self.update_quality_benchmark()
        
        data = BenchmarkData(
            coverage=coverage,
            performance=performance,
            quality=quality,
            last_updated=datetime.now().isoformat()
        )
        
        self._save_benchmark(data)
        self._print_comparison(existing, data)
        
        return data
    
    def _print_comparison(self, old: BenchmarkData, new: BenchmarkData):
        print("\n" + "=" * 60)
        print("基准对比")
        print("=" * 60)
        
        print(f"\n覆盖率变化:")
        old_coverage = old.coverage.line_rate
        new_coverage = new.coverage.line_rate
        diff = new_coverage - old_coverage
        symbol = "↑" if diff > 0 else "↓" if diff < 0 else "="
        print(f"  行覆盖率: {old_coverage:.2f}% → {new_coverage:.2f}% ({symbol} {abs(diff):.2f}%)")
        
        print(f"\n性能变化:")
        old_perf = {p.endpoint: p for p in old.performance}
        for p in new.performance[:5]:
            old_p = old_perf.get(p.endpoint)
            if old_p:
                diff = p.avg_ms - old_p.avg_ms
                symbol = "↓" if diff < 0 else "↑" if diff > 0 else "="
                print(f"  {p.endpoint}: {old_p.avg_ms:.2f}ms → {p.avg_ms:.2f}ms ({symbol} {abs(diff):.2f}ms)")
            else:
                print(f"  {p.endpoint}: {p.avg_ms:.2f}ms (新增)")
        
        print(f"\n质量变化:")
        old_quality = {q.metric_name: q for q in old.quality}
        for q in new.quality:
            old_q = old_quality.get(q.metric_name)
            if old_q:
                diff = q.value - old_q.value
                symbol = "↓" if (q.metric_name in ["ruff_errors", "avg_complexity"] and diff < 0) or (q.metric_name == "doc_coverage" and diff > 0) else "↑" if diff > 0 else "="
                print(f"  {q.metric_name}: {old_q.value} → {q.value} ({symbol})")
            else:
                print(f"  {q.metric_name}: {q.value} (新增)")
    
    def get_current_benchmark(self) -> BenchmarkData:
        return self._load_existing_benchmark()
    
    def set_threshold(self, metric: str, value: float):
        thresholds_file = self.benchmarks_dir / "thresholds.json"
        
        thresholds = {}
        if thresholds_file.exists():
            with open(thresholds_file, "r", encoding="utf-8") as f:
                thresholds = json.load(f)
        
        thresholds[metric] = {
            "value": value,
            "updated": datetime.now().isoformat()
        }
        
        with open(thresholds_file, "w", encoding="utf-8") as f:
            json.dump(thresholds, f, indent=2, ensure_ascii=False)
        
        print(f"阈值已更新: {metric} = {value}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="基准数据更新器")
    parser.add_argument("--coverage", action="store_true", help="仅更新覆盖率基准")
    parser.add_argument("--performance", action="store_true", help="仅更新性能基准")
    parser.add_argument("--quality", action="store_true", help="仅更新代码质量基准")
    parser.add_argument("--set-threshold", nargs=2, metavar=("METRIC", "VALUE"), help="设置阈值")
    
    args = parser.parse_args()
    
    updater = BenchmarkUpdater()
    
    if args.set_threshold:
        metric, value = args.set_threshold
        updater.set_threshold(metric, float(value))
        return 0
    
    if args.coverage:
        updater.update_coverage_benchmark()
    elif args.performance:
        updater.update_performance_benchmark()
    elif args.quality:
        updater.update_quality_benchmark()
    else:
        updater.update_all_benchmarks()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
