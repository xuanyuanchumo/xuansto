"""
性能基准测试脚本

测试系统各组件的性能基准指标
"""

import asyncio
import time
import statistics
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import httpx
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from backend.app.config import settings
except ImportError:
    settings = None  # Fallback for environments without backend


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    p50: float
    p95: float
    p99: float
    ops_per_second: float
    success_rate: float
    errors: List[str]


class PerformanceBenchmark:
    """性能基准测试类"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[BenchmarkResult] = []
        self.db_engine = None
        self.db_session = None

    def setup_database(self):
        """设置数据库连接"""
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/skiller_test")
        self.db_engine = create_engine(db_url)
        self.db_session = sessionmaker(bind=self.db_engine)

    def calculate_statistics(self, times: List[float], errors: List[str]) -> Dict[str, float]:
        """计算统计数据"""
        if not times:
            return {
                "avg_time": 0,
                "min_time": 0,
                "max_time": 0,
                "p50": 0,
                "p95": 0,
                "p99": 0,
                "ops_per_second": 0,
            }

        sorted_times = sorted(times)
        n = len(sorted_times)

        return {
            "avg_time": statistics.mean(times),
            "min_time": sorted_times[0],
            "max_time": sorted_times[-1],
            "p50": sorted_times[n // 2],
            "p95": sorted_times[int(n * 0.95)] if n >= 20 else sorted_times[-1],
            "p99": sorted_times[int(n * 0.99)] if n >= 100 else sorted_times[-1],
            "ops_per_second": n / sum(times) if sum(times) > 0 else 0,
        }

    def run_benchmark(
        self,
        name: str,
        func: callable,
        iterations: int = 100,
        warmup: int = 10,
        **kwargs
    ) -> BenchmarkResult:
        """运行基准测试"""
        print(f"\n运行基准测试: {name}")
        print(f"  预热迭代: {warmup}")
        print(f"  正式迭代: {iterations}")

        for _ in range(warmup):
            try:
                func(**kwargs)
            except Exception:
                pass

        times: List[float] = []
        errors: List[str] = []
        start_total = time.time()

        for i in range(iterations):
            try:
                start = time.time()
                func(**kwargs)
                elapsed = time.time() - start
                times.append(elapsed)
            except Exception as e:
                errors.append(str(e))

        total_time = time.time() - start_total
        stats = self.calculate_statistics(times, errors)

        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=total_time,
            avg_time=stats["avg_time"],
            min_time=stats["min_time"],
            max_time=stats["max_time"],
            p50=stats["p50"],
            p95=stats["p95"],
            p99=stats["p99"],
            ops_per_second=stats["ops_per_second"],
            success_rate=len(times) / iterations * 100 if iterations > 0 else 0,
            errors=errors[:5]
        )

        self.results.append(result)
        self._print_result(result)
        return result

    def _print_result(self, result: BenchmarkResult):
        """打印测试结果"""
        print(f"\n  结果:")
        print(f"    总时间: {result.total_time:.3f}s")
        print(f"    平均时间: {result.avg_time*1000:.2f}ms")
        print(f"    最小时间: {result.min_time*1000:.2f}ms")
        print(f"    最大时间: {result.max_time*1000:.2f}ms")
        print(f"    P50: {result.p50*1000:.2f}ms")
        print(f"    P95: {result.p95*1000:.2f}ms")
        print(f"    P99: {result.p99*1000:.2f}ms")
        print(f"    吞吐量: {result.ops_per_second:.2f} ops/s")
        print(f"    成功率: {result.success_rate:.1f}%")
        if result.errors:
            print(f"    错误数: {len(result.errors)}")

    async def run_async_benchmark(
        self,
        name: str,
        func: callable,
        iterations: int = 100,
        concurrency: int = 10,
        **kwargs
    ) -> BenchmarkResult:
        """运行异步基准测试"""
        print(f"\n运行异步基准测试: {name}")
        print(f"  迭代次数: {iterations}")
        print(f"  并发数: {concurrency}")

        times: List[float] = []
        errors: List[str] = []
        start_total = time.time()

        async def run_single():
            try:
                start = time.time()
                await func(**kwargs)
                return time.time() - start, None
            except Exception as e:
                return None, str(e)

        semaphore = asyncio.Semaphore(concurrency)

        async def bounded_run():
            async with semaphore:
                return await run_single()

        tasks = [bounded_run() for _ in range(iterations)]
        results = await asyncio.gather(*tasks)

        for elapsed, error in results:
            if elapsed is not None:
                times.append(elapsed)
            if error:
                errors.append(error)

        total_time = time.time() - start_total
        stats = self.calculate_statistics(times, errors)

        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=total_time,
            avg_time=stats["avg_time"],
            min_time=stats["min_time"],
            max_time=stats["max_time"],
            p50=stats["p50"],
            p95=stats["p95"],
            p99=stats["p99"],
            ops_per_second=stats["ops_per_second"],
            success_rate=len(times) / iterations * 100 if iterations > 0 else 0,
            errors=errors[:5]
        )

        self.results.append(result)
        self._print_result(result)
        return result


class APIBenchmark(PerformanceBenchmark):
    """API性能基准测试"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        self.client = httpx.Client(base_url=base_url, timeout=30.0)

    def benchmark_list_projects(self):
        """测试项目列表API"""
        def call_api():
            response = self.client.get("/api/projects/")
            response.raise_for_status()
            return response.json()

        return self.run_benchmark(
            "API: 获取项目列表",
            call_api,
            iterations=200
        )

    def benchmark_get_project(self, project_id: int = 1):
        """测试获取单个项目API"""
        def call_api():
            response = self.client.get(f"/api/projects/{project_id}")
            response.raise_for_status()
            return response.json()

        return self.run_benchmark(
            "API: 获取单个项目",
            call_api,
            iterations=200
        )

    def benchmark_create_project(self):
        """测试创建项目API"""
        counter = [0]

        def call_api():
            counter[0] += 1
            data = {
                "name": f"性能测试项目_{counter[0]}_{time.time()}",
                "description": "性能测试描述",
                "tech_stack": ["Python", "FastAPI"]
            }
            response = self.client.post("/api/projects/", json=data)
            response.raise_for_status()
            return response.json()

        return self.run_benchmark(
            "API: 创建项目",
            call_api,
            iterations=50
        )

    def benchmark_search_projects(self):
        """测试搜索项目API"""
        def call_api():
            response = self.client.get("/api/projects/search?q=测试")
            response.raise_for_status()
            return response.json()

        return self.run_benchmark(
            "API: 搜索项目",
            call_api,
            iterations=100
        )

    def benchmark_project_stats(self, project_id: int = 1):
        """测试项目统计API"""
        def call_api():
            response = self.client.get(f"/api/projects/{project_id}/stats")
            response.raise_for_status()
            return response.json()

        return self.run_benchmark(
            "API: 获取项目统计",
            call_api,
            iterations=100
        )

    async def benchmark_concurrent_requests(self):
        """测试并发请求"""
        async def make_request(client: httpx.AsyncClient):
            response = await client.get("/api/projects/")
            response.raise_for_status()
            return response.json()

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            return await self.run_async_benchmark(
                "API: 并发请求测试",
                lambda: make_request(client),
                iterations=500,
                concurrency=50
            )


class DatabaseBenchmark(PerformanceBenchmark):
    """数据库性能基准测试"""

    def __init__(self):
        super().__init__()
        self.setup_database()

    def benchmark_simple_query(self):
        """测试简单查询"""
        def run_query():
            with self.db_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.fetchone()

        return self.run_benchmark(
            "数据库: 简单查询",
            run_query,
            iterations=1000
        )

    def benchmark_select_projects(self):
        """测试项目查询"""
        def run_query():
            with self.db_engine.connect() as conn:
                result = conn.execute(text("SELECT * FROM projects LIMIT 10"))
                return result.fetchall()

        return self.run_benchmark(
            "数据库: 查询项目列表",
            run_query,
            iterations=500
        )

    def benchmark_insert_project(self):
        """测试插入项目"""
        counter = [0]

        def run_query():
            counter[0] += 1
            with self.db_engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO projects (name, status, created_at, updated_at)
                        VALUES (:name, 'REQUIREMENT', NOW(), NOW())
                    """),
                    {"name": f"性能测试项目_{counter[0]}_{time.time()}"}
                )
                conn.commit()

        return self.run_benchmark(
            "数据库: 插入项目",
            run_query,
            iterations=100
        )

    def benchmark_join_query(self):
        """测试连接查询"""
        def run_query():
            with self.db_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT p.name, t.title, t.status
                    FROM projects p
                    LEFT JOIN tasks t ON p.id = t.project_id
                    LIMIT 50
                """))
                return result.fetchall()

        return self.run_benchmark(
            "数据库: 连接查询",
            run_query,
            iterations=200
        )

    def benchmark_aggregate_query(self):
        """测试聚合查询"""
        def run_query():
            with self.db_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT status, COUNT(*) as count
                    FROM projects
                    GROUP BY status
                """))
                return result.fetchall()

        return self.run_benchmark(
            "数据库: 聚合查询",
            run_query,
            iterations=500
        )


class CacheBenchmark(PerformanceBenchmark):
    """缓存性能基准测试"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        super().__init__()
        self.redis_url = redis_url
        self.redis_client = None

    def setup_redis(self):
        """设置Redis连接"""
        import redis
        self.redis_client = redis.from_url(self.redis_url)

    def benchmark_cache_set(self):
        """测试缓存写入"""
        counter = [0]

        def run_cache():
            counter[0] += 1
            key = f"benchmark_key_{counter[0]}"
            value = f"benchmark_value_{time.time()}"
            self.redis_client.set(key, value, ex=60)

        return self.run_benchmark(
            "缓存: SET操作",
            run_cache,
            iterations=1000
        )

    def benchmark_cache_get(self):
        """测试缓存读取"""
        self.redis_client.set("benchmark_read_key", "test_value")

        def run_cache():
            return self.redis_client.get("benchmark_read_key")

        return self.run_benchmark(
            "缓存: GET操作",
            run_cache,
            iterations=1000
        )

    def benchmark_cache_json(self):
        """测试JSON缓存操作"""
        import json
        test_data = {"name": "测试", "items": list(range(100))}

        def run_cache():
            key = f"benchmark_json_{time.time()}"
            self.redis_client.set(key, json.dumps(test_data), ex=60)
            value = self.redis_client.get(key)
            return json.loads(value)

        return self.run_benchmark(
            "缓存: JSON操作",
            run_cache,
            iterations=500
        )


def generate_report(results: List[BenchmarkResult], output_path: str):
    """生成测试报告"""
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_tests": len(results),
            "total_time": sum(r.total_time for r in results),
        },
        "results": [asdict(r) for r in results],
        "thresholds": {
            "api_response_time_ms": 100,
            "db_query_time_ms": 50,
            "cache_operation_ms": 5,
        },
        "recommendations": []
    }

    for result in results:
        if "API" in result.name and result.avg_time * 1000 > 100:
            report["recommendations"].append(
                f"{result.name}: 平均响应时间 {result.avg_time*1000:.2f}ms 超过阈值100ms，建议优化"
            )
        if "数据库" in result.name and result.avg_time * 1000 > 50:
            report["recommendations"].append(
                f"{result.name}: 平均查询时间 {result.avg_time*1000:.2f}ms 超过阈值50ms，建议添加索引或优化查询"
            )
        if "缓存" in result.name and result.avg_time * 1000 > 5:
            report["recommendations"].append(
                f"{result.name}: 平均操作时间 {result.avg_time*1000:.2f}ms 超过阈值5ms，建议检查Redis配置"
            )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n报告已生成: {output_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("性能基准测试")
    print("=" * 60)
    print(f"开始时间: {datetime.utcnow().isoformat()}")

    all_results: List[BenchmarkResult] = []

    print("\n" + "=" * 60)
    print("API性能测试")
    print("=" * 60)
    api_benchmark = APIBenchmark()
    all_results.append(api_benchmark.benchmark_list_projects())
    all_results.append(api_benchmark.benchmark_get_project())
    all_results.append(api_benchmark.benchmark_search_projects())
    all_results.append(api_benchmark.benchmark_project_stats())

    print("\n" + "=" * 60)
    print("数据库性能测试")
    print("=" * 60)
    db_benchmark = DatabaseBenchmark()
    all_results.append(db_benchmark.benchmark_simple_query())
    all_results.append(db_benchmark.benchmark_select_projects())
    all_results.append(db_benchmark.benchmark_join_query())
    all_results.append(db_benchmark.benchmark_aggregate_query())

    print("\n" + "=" * 60)
    print("缓存性能测试")
    print("=" * 60)
    try:
        cache_benchmark = CacheBenchmark()
        cache_benchmark.setup_redis()
        all_results.append(cache_benchmark.benchmark_cache_set())
        all_results.append(cache_benchmark.benchmark_cache_get())
        all_results.append(cache_benchmark.benchmark_cache_json())
    except Exception as e:
        print(f"缓存测试跳过: {e}")

    print("\n" + "=" * 60)
    print("异步并发测试")
    print("=" * 60)
    try:
        asyncio.run(api_benchmark.benchmark_concurrent_requests())
    except Exception as e:
        print(f"异步测试跳过: {e}")

    output_path = os.path.join(
        os.path.dirname(__file__),
        "..", "docs", "reports", "v1.0", "performance_benchmark.json"
    )
    generate_report(all_results, output_path)

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print(f"结束时间: {datetime.utcnow().isoformat()}")


if __name__ == "__main__":
    main()
