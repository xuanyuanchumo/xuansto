"""
性能基准测试报告生成器
生成综合性能测试报告
"""

import json
import os
import sys
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.main import app
from app.models.project import Project
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.agent import Agent
from app.models.skill_call import SkillCall


RESPONSE_TIME_THRESHOLD_MS = 200
P95_THRESHOLD_MS = 300
P99_THRESHOLD_MS = 500
COMPONENT_RENDER_THRESHOLD_MS = 100
PAGE_LOAD_THRESHOLD_MS = 3000


@dataclass
class BenchmarkResult:
    name: str
    category: str
    avg_ms: float
    min_ms: float
    max_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    threshold: float
    passed: bool
    iterations: int
    success_rate: float
    errors: List[str] = field(default_factory=list)


@dataclass
class PerformanceThresholds:
    api_response_time: float = RESPONSE_TIME_THRESHOLD_MS
    component_render_time: float = COMPONENT_RENDER_THRESHOLD_MS
    page_load_time: float = PAGE_LOAD_THRESHOLD_MS
    fcp: float = 2000
    lcp: float = 2500
    tti: float = 3800


class PerformanceReportGenerator:
    def __init__(self, thresholds: Optional[PerformanceThresholds] = None):
        self.results: List[BenchmarkResult] = []
        self.thresholds = thresholds or PerformanceThresholds()
        self.start_time = datetime.now()
        
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        self._seed_test_data()
        self._setup_app_dependency_override()

    def _seed_test_data(self):
        db = self.SessionLocal()
        try:
            for i in range(50):
                project = Project(
                    name=f"Benchmark Project {i}",
                    description=f"Description for project {i}",
                    status="REQUIREMENT",
                    tech_stack=["Python", "FastAPI"]
                )
                db.add(project)
            db.commit()
            
            projects = db.query(Project).all()
            for project in projects:
                for j in range(5):
                    task = Task(
                        title=f"Task {project.id}-{j}",
                        description=f"Task description",
                        project_id=project.id,
                        status=TaskStatus.PENDING.value,
                        priority=TaskPriority.MEDIUM.value
                    )
                    db.add(task)
            db.commit()
            
            for i in range(20):
                agent = Agent(
                    name=f"Agent {i}",
                    role="developer",
                    status="idle",
                    skills=["python", "testing"]
                )
                db.add(agent)
            db.commit()
            
            for i in range(100):
                skill_call = SkillCall(
                    skill_name=f"skill_{i % 10}",
                    caller=f"caller_{i % 5}",
                    status="completed" if i % 3 == 0 else "running"
                )
                db.add(skill_call)
            db.commit()
        finally:
            db.close()

    def _setup_app_dependency_override(self):
        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        from app.models.base import get_db
        app.dependency_overrides[get_db] = override_get_db

    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def benchmark_api_endpoint(
        self,
        client: TestClient,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        iterations: int = 50,
        warmup: int = 5,
        threshold: Optional[float] = None
    ) -> BenchmarkResult:
        times: List[float] = []
        errors: List[str] = []
        success_count = 0
        
        for _ in range(warmup):
            try:
                if method.upper() == "GET":
                    client.get(endpoint, params=params)
                elif method.upper() == "POST":
                    client.post(endpoint, json=json_data)
            except Exception:
                pass
        
        for _ in range(iterations):
            try:
                start = time.perf_counter()
                
                if method.upper() == "GET":
                    response = client.get(endpoint, params=params)
                elif method.upper() == "POST":
                    response = client.post(endpoint, json=json_data)
                elif method.upper() == "PUT":
                    response = client.put(endpoint, json=json_data)
                elif method.upper() == "DELETE":
                    response = client.delete(endpoint)
                else:
                    response = client.get(endpoint, params=params)
                
                end = time.perf_counter()
                duration_ms = (end - start) * 1000
                times.append(duration_ms)
                
                if response.status_code < 400:
                    success_count += 1
                else:
                    errors.append(f"HTTP {response.status_code}")
            except Exception as e:
                errors.append(str(e))
                times.append(0)
        
        valid_times = [t for t in times if t > 0] or [0]
        avg_ms = statistics.mean(valid_times)
        
        threshold_value = threshold or self.thresholds.api_response_time
        if method.upper() == "POST":
            threshold_value = threshold or self.thresholds.api_response_time * 2
        
        result = BenchmarkResult(
            name=f"{method} {endpoint}",
            category="api",
            avg_ms=round(avg_ms, 2),
            min_ms=round(min(valid_times), 2),
            max_ms=round(max(valid_times), 2),
            p50_ms=round(self._calculate_percentile(valid_times, 50), 2),
            p95_ms=round(self._calculate_percentile(valid_times, 95), 2),
            p99_ms=round(self._calculate_percentile(valid_times, 99), 2),
            threshold=threshold_value,
            passed=avg_ms < threshold_value and success_count == iterations,
            iterations=iterations,
            success_rate=round(success_count / iterations * 100, 2),
            errors=list(set(errors))[:5]
        )
        
        self.results.append(result)
        return result

    def run_all_api_benchmarks(self):
        print("\n=== 运行API基准测试 ===\n")
        
        with TestClient(app) as client:
            test_cases = [
                ("GET", "/", None, None, None, "根端点"),
                ("GET", "/health", None, None, None, "健康检查"),
                ("GET", "/api/projects/", None, None, None, "项目列表"),
                ("GET", "/api/projects/", None, {"page": 1, "page_size": 12}, None, "分页项目列表"),
                ("GET", "/api/projects/1", None, None, None, "项目详情"),
                ("GET", "/api/projects/stats", None, None, None, "项目统计"),
                ("GET", "/api/tasks/", None, None, None, "任务列表"),
                ("GET", "/api/tasks/stats", None, None, None, "任务统计"),
                ("GET", "/api/agents/", None, None, None, "代理列表"),
                ("GET", "/api/skill_calls/", None, None, None, "技能调用列表"),
                ("GET", "/api/dashboard/stats", None, None, None, "仪表盘统计"),
                ("POST", "/api/projects/", {"name": f"New Project {time.time()}", "description": "Test"}, None, None, "创建项目"),
                ("POST", "/api/tasks/", {"title": f"New Task {time.time()}"}, None, None, "创建任务"),
            ]
            
            for method, endpoint, json_data, params, threshold, desc in test_cases:
                print(f"测试: {desc} ({method} {endpoint})")
                result = self.benchmark_api_endpoint(
                    client, method, endpoint, json_data, params,
                    iterations=50, threshold=threshold
                )
                status = "✅ 通过" if result.passed else "❌ 失败"
                print(f"  平均: {result.avg_ms}ms, P95: {result.p95_ms}ms, 状态: {status}")

    def generate_summary(self) -> Dict[str, Any]:
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": round(pass_rate, 2)
        }

    def generate_recommendations(self) -> List[str]:
        recommendations = []
        
        slow_apis = [r for r in self.results if r.category == "api" and not r.passed]
        if slow_apis:
            recommendations.append("### API性能优化建议")
            for api in slow_apis:
                recommendations.append(f"- **{api.name}**: 平均响应时间 {api.avg_ms}ms，建议：")
                recommendations.append("  - 检查数据库查询是否使用索引")
                recommendations.append("  - 考虑添加Redis缓存层")
                recommendations.append("  - 优化数据序列化逻辑")
        
        high_variance = [r for r in self.results if r.p99_ms > r.threshold * 2]
        if high_variance:
            recommendations.append("\n### 响应时间稳定性建议")
            recommendations.append("- 发现部分测试P99响应时间波动较大，建议：")
            recommendations.append("  - 检查是否存在资源竞争")
            recommendations.append("  - 优化数据库连接池配置")
            recommendations.append("  - 增加预热迭代次数")
        
        if not recommendations:
            recommendations.append("### 性能表现良好")
            recommendations.append("所有性能指标均在预期范围内，继续保持！")
        
        return recommendations

    def generate_markdown_report(self) -> str:
        summary = self.generate_summary()
        recommendations = self.generate_recommendations()
        
        lines = [
            "# 三省六部技能性能基准测试报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 测试概览",
            "",
            "| 指标 | 值 |",
            "|------|------|",
            f"| 总测试数 | {summary['total_tests']} |",
            f"| 通过数 | {summary['passed_tests']} |",
            f"| 失败数 | {summary['failed_tests']} |",
            f"| 通过率 | {summary['pass_rate']}% |",
            ""
        ]
        
        api_results = [r for r in self.results if r.category == "api"]
        if api_results:
            lines.extend([
                "## API响应时间基准",
                "",
                "| 端点 | 平均(ms) | P50(ms) | P95(ms) | P99(ms) | 阈值(ms) | 状态 |",
                "|------|----------|---------|---------|---------|----------|------|"
            ])
            for r in api_results:
                status = "✅ 通过" if r.passed else "❌ 失败"
                lines.append(f"| {r.name} | {r.avg_ms} | {r.p50_ms} | {r.p95_ms} | {r.p99_ms} | {r.threshold} | {status} |")
            lines.append("")
        
        lines.extend([
            "## 性能阈值配置",
            "",
            "| 指标类型 | 阈值(ms) |",
            "|----------|----------|",
            f"| API响应时间 | {self.thresholds.api_response_time} |",
            f"| 组件渲染时间 | {self.thresholds.component_render_time} |",
            f"| 页面加载时间 | {self.thresholds.page_load_time} |",
            f"| 首次内容绘制(FCP) | {self.thresholds.fcp} |",
            f"| 最大内容绘制(LCP) | {self.thresholds.lcp} |",
            f"| 可交互时间(TTI) | {self.thresholds.tti} |",
            ""
        ])
        
        lines.extend(["## 优化建议", ""])
        lines.extend(recommendations)
        lines.append("")
        
        lines.extend([
            "## 测试环境",
            "",
            "| 项目 | 信息 |",
            "|------|------|",
            f"| Python | {sys.version.split()[0]} |",
            f"| 平台 | {sys.platform} |",
            ""
        ])
        
        return "\n".join(lines)

    def generate_json_report(self) -> str:
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.generate_summary(),
            "thresholds": asdict(self.thresholds),
            "results": [asdict(r) for r in self.results],
            "recommendations": self.generate_recommendations()
        }
        return json.dumps(report, indent=2, ensure_ascii=False)

    def save_report(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        
        md_report = self.generate_markdown_report()
        json_report = self.generate_json_report()
        
        md_path = os.path.join(output_dir, "performance-benchmark-report.md")
        json_path = os.path.join(output_dir, "performance-benchmark-report.json")
        
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_report)
        
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_report)
        
        print(f"\n报告已生成:")
        print(f"  Markdown: {md_path}")
        print(f"  JSON: {json_path}")

    def run_full_benchmark(self):
        print("=" * 60)
        print("三省六部技能性能基准测试")
        print("=" * 60)
        
        self.run_all_api_benchmarks()
        
        output_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
        self.save_report(output_dir)
        
        print("\n" + "=" * 60)
        print("性能基准测试完成")
        print("=" * 60)
        
        summary = self.generate_summary()
        print(f"\n总测试数: {summary['total_tests']}")
        print(f"通过数: {summary['passed_tests']}")
        print(f"失败数: {summary['failed_tests']}")
        print(f"通过率: {summary['pass_rate']}%")


if __name__ == "__main__":
    generator = PerformanceReportGenerator()
    generator.run_full_benchmark()
