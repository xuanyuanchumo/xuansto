#!/usr/bin/env python3
"""
性能基准检测器
检测API响应时间和前端加载时间
"""

import asyncio
import json
import os
import re
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable


class PerformanceIssueType(Enum):
    SLOW_API = "slow_api"
    SLOW_QUERY = "slow_query"
    SLOW_LOAD = "slow_load"
    MEMORY_LEAK = "memory_leak"
    HIGH_CPU = "high_cpu"
    LARGE_BUNDLE = "large_bundle"
    SLOW_RENDER = "slow_render"


class PerformanceSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class PerformanceMetric:
    name: str
    value: float
    unit: str
    threshold: float
    passed: bool
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": round(self.value, 2),
            "unit": self.unit,
            "threshold": self.threshold,
            "passed": self.passed,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


@dataclass
class PerformanceIssue:
    issue_type: PerformanceIssueType
    severity: PerformanceSeverity
    location: str
    description: str
    metric_value: float
    threshold: float
    impact: str
    suggestion: str
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "location": self.location,
            "description": self.description,
            "metric_value": round(self.metric_value, 2),
            "threshold": self.threshold,
            "impact": self.impact,
            "suggestion": self.suggestion,
            "timestamp": self.timestamp
        }


@dataclass
class APIEndpointResult:
    endpoint: str
    method: str
    avg_response_time_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    success_rate: float
    total_requests: int
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "avg_response_time_ms": round(self.avg_response_time_ms, 2),
            "p50_ms": round(self.p50_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
            "min_ms": round(self.min_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "success_rate": round(self.success_rate, 2),
            "total_requests": self.total_requests,
            "errors": self.errors
        }


@dataclass
class FrontendLoadResult:
    page: str
    load_time_ms: float
    dom_content_loaded_ms: float
    first_paint_ms: float
    first_contentful_paint_ms: float
    largest_contentful_paint_ms: float
    time_to_interactive_ms: float
    total_bytes: int
    javascript_bytes: int
    css_bytes: int
    image_bytes: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page": self.page,
            "load_time_ms": round(self.load_time_ms, 2),
            "dom_content_loaded_ms": round(self.dom_content_loaded_ms, 2),
            "first_paint_ms": round(self.first_paint_ms, 2),
            "first_contentful_paint_ms": round(self.first_contentful_paint_ms, 2),
            "largest_contentful_paint_ms": round(self.largest_contentful_paint_ms, 2),
            "time_to_interactive_ms": round(self.time_to_interactive_ms, 2),
            "total_bytes": self.total_bytes,
            "javascript_bytes": self.javascript_bytes,
            "css_bytes": self.css_bytes,
            "image_bytes": self.image_bytes
        }


class APIPerformanceDetector:
    API_THRESHOLDS = {
        "avg_response_time": 100.0,
        "p95_response_time": 200.0,
        "p99_response_time": 500.0,
        "success_rate": 99.0
    }

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[APIEndpointResult] = []
        self.issues: List[PerformanceIssue] = []
        self.metrics: List[PerformanceMetric] = []

    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    async def test_endpoint(
        self,
        session,
        method: str,
        endpoint: str,
        iterations: int = 50,
        warmup: int = 5
    ) -> APIEndpointResult:
        import httpx

        times = []
        errors = []
        success_count = 0
        url = f"{self.base_url}{endpoint}"

        for _ in range(warmup):
            try:
                if method.upper() == "GET":
                    await session.get(url)
            except Exception:
                pass

        for _ in range(iterations):
            try:
                start = time.perf_counter()
                if method.upper() == "GET":
                    response = await session.get(url)
                elif method.upper() == "POST":
                    response = await session.post(url, json={})
                else:
                    response = await session.get(url)
                end = time.perf_counter()

                times.append((end - start) * 1000)

                if response.status_code < 400:
                    success_count += 1
                else:
                    errors.append(f"HTTP {response.status_code}")
            except Exception as e:
                errors.append(str(e))
                times.append(0)

        valid_times = [t for t in times if t > 0] or [0]

        return APIEndpointResult(
            endpoint=endpoint,
            method=method,
            avg_response_time_ms=statistics.mean(valid_times) if valid_times else 0,
            p50_ms=self._calculate_percentile(valid_times, 50),
            p95_ms=self._calculate_percentile(valid_times, 95),
            p99_ms=self._calculate_percentile(valid_times, 99),
            min_ms=min(valid_times) if valid_times else 0,
            max_ms=max(valid_times) if valid_times else 0,
            success_rate=(success_count / iterations * 100) if iterations > 0 else 0,
            total_requests=iterations,
            errors=list(set(errors))[:5]
        )

    async def run_api_tests(self, endpoints: Optional[List[tuple]] = None) -> List[APIEndpointResult]:
        import httpx

        if endpoints is None:
            endpoints = [
                ("GET", "/"),
                ("GET", "/health"),
                ("GET", "/api/projects"),
                ("GET", "/api/tasks"),
                ("GET", "/api/agents"),
                ("GET", "/api/dashboard/stats"),
            ]

        async with httpx.AsyncClient(timeout=30.0) as session:
            for method, endpoint in endpoints:
                print(f"测试: {method} {endpoint}")
                result = await self.test_endpoint(session, method, endpoint)
                self.results.append(result)
                self._check_api_result(result)

        return self.results

    def _check_api_result(self, result: APIEndpointResult) -> None:
        if result.avg_response_time_ms > self.API_THRESHOLDS["avg_response_time"]:
            self.issues.append(PerformanceIssue(
                issue_type=PerformanceIssueType.SLOW_API,
                severity=PerformanceSeverity.HIGH if result.avg_response_time_ms > 500 else PerformanceSeverity.MEDIUM,
                location=result.endpoint,
                description=f"API平均响应时间 {result.avg_response_time_ms:.0f}ms 超过阈值 {self.API_THRESHOLDS['avg_response_time']}ms",
                metric_value=result.avg_response_time_ms,
                threshold=self.API_THRESHOLDS["avg_response_time"],
                impact="用户体验下降，可能导致请求超时",
                suggestion="优化数据库查询、添加缓存、减少响应数据量"
            ))

        if result.p95_ms > self.API_THRESHOLDS["p95_response_time"]:
            self.issues.append(PerformanceIssue(
                issue_type=PerformanceIssueType.SLOW_API,
                severity=PerformanceSeverity.MEDIUM,
                location=result.endpoint,
                description=f"API P95响应时间 {result.p95_ms:.0f}ms 超过阈值 {self.API_THRESHOLDS['p95_response_time']}ms",
                metric_value=result.p95_ms,
                threshold=self.API_THRESHOLDS["p95_response_time"],
                impact="部分用户体验较差",
                suggestion="分析慢请求日志，优化热点路径"
            ))

        if result.success_rate < self.API_THRESHOLDS["success_rate"]:
            self.issues.append(PerformanceIssue(
                issue_type=PerformanceIssueType.SLOW_API,
                severity=PerformanceSeverity.HIGH,
                location=result.endpoint,
                description=f"API成功率 {result.success_rate:.1f}% 低于阈值 {self.API_THRESHOLDS['success_rate']}%",
                metric_value=result.success_rate,
                threshold=self.API_THRESHOLDS["success_rate"],
                impact="请求失败影响业务流程",
                suggestion="检查错误日志，修复稳定性问题"
            ))

    def load_results_from_file(self, file_path: Path) -> List[APIEndpointResult]:
        if not file_path.exists():
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data.get("api_results", []):
            result = APIEndpointResult(
                endpoint=item["endpoint"],
                method=item["method"],
                avg_response_time_ms=item["avg_ms"],
                p50_ms=item["p50_ms"],
                p95_ms=item["p95_ms"],
                p99_ms=item["p99_ms"],
                min_ms=item["min_ms"],
                max_ms=item["max_ms"],
                success_rate=item["success_rate"],
                total_requests=item["total_requests"],
                errors=item.get("errors", [])
            )
            self.results.append(result)
            self._check_api_result(result)

        return self.results


class FrontendPerformanceDetector:
    LOAD_THRESHOLDS = {
        "load_time": 3000.0,
        "first_contentful_paint": 1800.0,
        "largest_contentful_paint": 2500.0,
        "time_to_interactive": 3800.0,
        "total_bundle_size": 500 * 1024,
        "javascript_size": 300 * 1024
    }

    def __init__(self):
        self.results: List[FrontendLoadResult] = []
        self.issues: List[PerformanceIssue] = []
        self.metrics: List[PerformanceMetric] = []

    def analyze_bundle_size(self, frontend_dir: Path) -> Dict[str, int]:
        dist_dir = frontend_dir / "dist"
        if not dist_dir.exists():
            return {}

        sizes = {
            "total": 0,
            "javascript": 0,
            "css": 0,
            "images": 0
        }

        for file_path in dist_dir.rglob("*"):
            if file_path.is_file():
                size = file_path.stat().st_size
                sizes["total"] += size

                if file_path.suffix == ".js":
                    sizes["javascript"] += size
                elif file_path.suffix == ".css":
                    sizes["css"] += size
                elif file_path.suffix in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"]:
                    sizes["images"] += size

        return sizes

    def check_bundle_sizes(self, frontend_dir: Path) -> List[PerformanceIssue]:
        sizes = self.analyze_bundle_size(frontend_dir)

        if not sizes:
            return []

        if sizes["total"] > self.LOAD_THRESHOLDS["total_bundle_size"]:
            self.issues.append(PerformanceIssue(
                issue_type=PerformanceIssueType.LARGE_BUNDLE,
                severity=PerformanceSeverity.MEDIUM,
                location="dist/",
                description=f"总包大小 {sizes['total'] / 1024:.0f}KB 超过阈值 {self.LOAD_THRESHOLDS['total_bundle_size'] / 1024:.0f}KB",
                metric_value=sizes["total"],
                threshold=self.LOAD_THRESHOLDS["total_bundle_size"],
                impact="页面加载时间增加",
                suggestion="代码分割、懒加载、压缩资源"
            ))

        if sizes["javascript"] > self.LOAD_THRESHOLDS["javascript_size"]:
            self.issues.append(PerformanceIssue(
                issue_type=PerformanceIssueType.LARGE_BUNDLE,
                severity=PerformanceSeverity.MEDIUM,
                location="dist/assets/*.js",
                description=f"JavaScript大小 {sizes['javascript'] / 1024:.0f}KB 超过阈值 {self.LOAD_THRESHOLDS['javascript_size'] / 1024:.0f}KB",
                metric_value=sizes["javascript"],
                threshold=self.LOAD_THRESHOLDS["javascript_size"],
                impact="JS解析和执行时间增加",
                suggestion="使用动态导入、Tree Shaking、移除未使用代码"
            ))

        return self.issues

    def parse_lighthouse_report(self, report_path: Path) -> Optional[FrontendLoadResult]:
        if not report_path.exists():
            return None

        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        audits = data.get("audits", {})

        def get_metric(name: str) -> float:
            audit = audits.get(name, {})
            return audit.get("numericValue", 0)

        return FrontendLoadResult(
            page=data.get("requestedUrl", "unknown"),
            load_time_ms=get_metric("load-page"),
            dom_content_loaded_ms=get_metric("dom-content-loaded"),
            first_paint_ms=get_metric("first-paint"),
            first_contentful_paint_ms=get_metric("first-contentful-paint"),
            largest_contentful_paint_ms=get_metric("largest-contentful-paint"),
            time_to_interactive_ms=get_metric("interactive"),
            total_bytes=0,
            javascript_bytes=0,
            css_bytes=0,
            image_bytes=0
        )

    def parse_playwright_report(self, report_path: Path) -> List[FrontendLoadResult]:
        if not report_path.exists():
            return []

        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = []
        for spec in data.get("specs", []):
            for test in spec.get("tests", []):
                for result in test.get("results", []):
                    metrics = result.get("metrics", {})
                    if metrics:
                        load_result = FrontendLoadResult(
                            page=test.get("title", "unknown"),
                            load_time_ms=metrics.get("load", 0),
                            dom_content_loaded_ms=metrics.get("domcontentloaded", 0),
                            first_paint_ms=0,
                            first_contentful_paint_ms=0,
                            largest_contentful_paint_ms=0,
                            time_to_interactive_ms=0,
                            total_bytes=0,
                            javascript_bytes=0,
                            css_bytes=0,
                            image_bytes=0
                        )
                        results.append(load_result)

        return results

    def check_load_metrics(self, result: FrontendLoadResult) -> List[PerformanceIssue]:
        issues = []

        if result.load_time_ms > self.LOAD_THRESHOLDS["load_time"]:
            issues.append(PerformanceIssue(
                issue_type=PerformanceIssueType.SLOW_LOAD,
                severity=PerformanceSeverity.HIGH,
                location=result.page,
                description=f"页面加载时间 {result.load_time_ms:.0f}ms 超过阈值 {self.LOAD_THRESHOLDS['load_time']:.0f}ms",
                metric_value=result.load_time_ms,
                threshold=self.LOAD_THRESHOLDS["load_time"],
                impact="用户等待时间长，可能流失用户",
                suggestion="优化资源加载、使用CDN、启用压缩"
            ))

        if result.first_contentful_paint_ms > self.LOAD_THRESHOLDS["first_contentful_paint"]:
            issues.append(PerformanceIssue(
                issue_type=PerformanceIssueType.SLOW_RENDER,
                severity=PerformanceSeverity.MEDIUM,
                location=result.page,
                description=f"FCP {result.first_contentful_paint_ms:.0f}ms 超过阈值 {self.LOAD_THRESHOLDS['first_contentful_paint']:.0f}ms",
                metric_value=result.first_contentful_paint_ms,
                threshold=self.LOAD_THRESHOLDS["first_contentful_paint"],
                impact="首屏渲染慢，用户感知延迟",
                suggestion="内联关键CSS、预加载关键资源"
            ))

        if result.largest_contentful_paint_ms > self.LOAD_THRESHOLDS["largest_contentful_paint"]:
            issues.append(PerformanceIssue(
                issue_type=PerformanceIssueType.SLOW_RENDER,
                severity=PerformanceSeverity.MEDIUM,
                location=result.page,
                description=f"LCP {result.largest_contentful_paint_ms:.0f}ms 超过阈值 {self.LOAD_THRESHOLDS['largest_contentful_paint']:.0f}ms",
                metric_value=result.largest_contentful_paint_ms,
                threshold=self.LOAD_THRESHOLDS["largest_contentful_paint"],
                impact="主要内容渲染慢",
                suggestion="优化图片加载、预加载LCP元素"
            ))

        self.issues.extend(issues)
        return issues


class PerformanceDetector:
    def __init__(
        self,
        api_base_url: str = "http://localhost:8000",
        api_thresholds: Optional[Dict[str, float]] = None,
        load_thresholds: Optional[Dict[str, float]] = None
    ):
        self.api_detector = APIPerformanceDetector(api_base_url)
        self.frontend_detector = FrontendPerformanceDetector()
        self.all_issues: List[PerformanceIssue] = []
        self.all_metrics: List[PerformanceMetric] = []

        if api_thresholds:
            self.api_detector.API_THRESHOLDS.update(api_thresholds)
        if load_thresholds:
            self.frontend_detector.LOAD_THRESHOLDS.update(load_thresholds)

    async def detect_api_performance(
        self,
        endpoints: Optional[List[tuple]] = None,
        run_live: bool = False
    ) -> List[APIEndpointResult]:
        if run_live:
            return await self.api_detector.run_api_tests(endpoints)
        return []

    def detect_frontend_performance(self, frontend_dir: Path) -> List[PerformanceIssue]:
        issues = self.frontend_detector.check_bundle_sizes(frontend_dir)

        lighthouse_path = frontend_dir / "lighthouse-report.json"
        if lighthouse_path.exists():
            result = self.frontend_detector.parse_lighthouse_report(lighthouse_path)
            if result:
                self.frontend_detector.results.append(result)
                issues.extend(self.frontend_detector.check_load_metrics(result))

        playwright_path = frontend_dir / "playwright-report.json"
        if playwright_path.exists():
            results = self.frontend_detector.parse_playwright_report(playwright_path)
            for result in results:
                self.frontend_detector.results.append(result)
                issues.extend(self.frontend_detector.check_load_metrics(result))

        return issues

    def load_existing_api_results(self, report_path: Path) -> List[APIEndpointResult]:
        return self.api_detector.load_results_from_file(report_path)

    def collect_all_issues(self) -> List[PerformanceIssue]:
        self.all_issues = self.api_detector.issues + self.frontend_detector.issues
        return self.all_issues

    def generate_report(self) -> str:
        report = []
        report.append("=" * 80)
        report.append("性能基准检测报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)

        report.append(f"\n## API性能检测结果")
        report.append("-" * 40)
        if self.api_detector.results:
            report.append(f"测试端点数: {len(self.api_detector.results)}")
            for result in self.api_detector.results:
                status = "✅" if result.avg_response_time_ms <= self.api_detector.API_THRESHOLDS["avg_response_time"] else "❌"
                report.append(f"\n{status} {result.method} {result.endpoint}")
                report.append(f"   平均: {result.avg_response_time_ms:.0f}ms, P95: {result.p95_ms:.0f}ms, 成功率: {result.success_rate:.1f}%")
        else:
            report.append("无API性能数据")

        report.append(f"\n## 前端性能检测结果")
        report.append("-" * 40)
        if self.frontend_detector.results:
            for result in self.frontend_detector.results:
                status = "✅" if result.load_time_ms <= self.frontend_detector.LOAD_THRESHOLDS["load_time"] else "❌"
                report.append(f"\n{status} {result.page}")
                report.append(f"   加载时间: {result.load_time_ms:.0f}ms, FCP: {result.first_contentful_paint_ms:.0f}ms")
        else:
            report.append("无前端性能数据")

        issues = self.collect_all_issues()
        report.append(f"\n## 性能问题 ({len(issues)}个)")
        report.append("-" * 40)

        if issues:
            sorted_issues = sorted(issues, key=lambda i: i.severity.value)
            for i, issue in enumerate(sorted_issues, 1):
                report.append(f"\n{i}. [{issue.severity.value.upper()}] {issue.issue_type.value}")
                report.append(f"   位置: {issue.location}")
                report.append(f"   描述: {issue.description}")
                report.append(f"   影响: {issue.impact}")
                report.append(f"   建议: {issue.suggestion}")
        else:
            report.append("✅ 未发现性能问题")

        report.append("\n" + "=" * 80)
        report.append("性能优化建议")
        report.append("=" * 80)
        report.append("\n1. API优化:")
        report.append("   - 添加数据库索引")
        report.append("   - 使用Redis缓存热点数据")
        report.append("   - 实现API响应压缩")
        report.append("   - 使用异步处理长耗时操作")
        report.append("\n2. 前端优化:")
        report.append("   - 代码分割和懒加载")
        report.append("   - 图片优化和WebP格式")
        report.append("   - 启用Gzip/Brotli压缩")
        report.append("   - 使用CDN加速静态资源")

        return "\n".join(report)

    def save_report(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "timestamp": datetime.now().isoformat(),
            "api_results": [r.to_dict() for r in self.api_detector.results],
            "frontend_results": [r.to_dict() for r in self.frontend_detector.results],
            "issues": [i.to_dict() for i in self.collect_all_issues()]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_critical_issues(self) -> List[PerformanceIssue]:
        return [i for i in self.all_issues if i.severity == PerformanceSeverity.CRITICAL]

    def get_slow_apis(self) -> List[APIEndpointResult]:
        threshold = self.api_detector.API_THRESHOLDS["avg_response_time"]
        return [r for r in self.api_detector.results if r.avg_response_time_ms > threshold]


def main():
    base_dir = Path(__file__).parent.parent

    print("=" * 80)
    print("性能基准检测器")
    print("=" * 80)

    detector = PerformanceDetector()

    print("\n加载现有API性能数据...")
    api_report_path = base_dir / "backend" / "scripts" / "performance_report.md"
    if api_report_path.exists():
        json_path = base_dir / "backend" / "scripts" / "performance_report.json"
        if json_path.exists():
            detector.load_existing_api_results(json_path)
            print(f"已加载 {len(detector.api_detector.results)} 个API结果")

    print("\n检测前端性能...")
    frontend_dir = base_dir / "frontend"
    if frontend_dir.exists():
        issues = detector.detect_frontend_performance(frontend_dir)
        print(f"发现 {len(issues)} 个前端性能问题")

    print("\n生成报告...")
    report = detector.generate_report()
    print(report)

    reports_dir = base_dir / "reports"
    report_path = reports_dir / "performance_detection_report.json"
    detector.save_report(report_path)
    print(f"\n报告已保存: {report_path}")

    critical = detector.get_critical_issues()
    if critical:
        print(f"\n关键性能问题: {len(critical)}")
        for issue in critical:
            print(f"  - {issue.location}: {issue.description}")

    return 0 if not critical else 1


if __name__ == "__main__":
    sys.exit(main())
