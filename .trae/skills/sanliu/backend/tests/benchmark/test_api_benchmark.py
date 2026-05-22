"""
API响应时间基准测试

测试各API端点的响应时间，设置响应时间基准（< 200ms）
"""

import pytest
import time
import statistics
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass, field
from tests.conftest import create_test_project, create_test_task, create_test_agent


RESPONSE_TIME_THRESHOLD_MS = 200
P95_THRESHOLD_MS = 300
P99_THRESHOLD_MS = 500


@dataclass
class BenchmarkResult:
    endpoint: str
    method: str
    iterations: int
    avg_ms: float
    min_ms: float
    max_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    std_dev_ms: float
    success_rate: float
    passed: bool
    errors: List[str] = field(default_factory=list)


class APIBenchmark:
    def __init__(self, threshold_ms: float = RESPONSE_TIME_THRESHOLD_MS):
        self.threshold_ms = threshold_ms
        self.results: List[BenchmarkResult] = []
    
    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def benchmark_endpoint(
        self,
        client,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        iterations: int = 50,
        warmup: int = 5,
        description: str = ""
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
                elif method.upper() == "PUT":
                    client.put(endpoint, json=json_data)
                elif method.upper() == "DELETE":
                    client.delete(endpoint)
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
        std_dev = statistics.stdev(valid_times) if len(valid_times) > 1 else 0
        
        result = BenchmarkResult(
            endpoint=endpoint,
            method=method.upper(),
            iterations=iterations,
            avg_ms=round(avg_ms, 2),
            min_ms=round(min(valid_times), 2),
            max_ms=round(max(valid_times), 2),
            p50_ms=round(self._calculate_percentile(valid_times, 50), 2),
            p95_ms=round(self._calculate_percentile(valid_times, 95), 2),
            p99_ms=round(self._calculate_percentile(valid_times, 99), 2),
            std_dev_ms=round(std_dev, 2),
            success_rate=round(success_count / iterations * 100, 2),
            passed=avg_ms < self.threshold_ms and success_count == iterations,
            errors=list(set(errors))[:5]
        )
        
        self.results.append(result)
        return result


@pytest.mark.performance
@pytest.mark.benchmark
class TestAPIResponseTimeBenchmark:
    """API响应时间基准测试"""
    
    @pytest.fixture(autouse=True)
    def setup_benchmark(self, client, db_session, mock_redis):
        self.client = client
        self.db_session = db_session
        self.mock_redis = mock_redis
        self.benchmark = APIBenchmark(threshold_ms=RESPONSE_TIME_THRESHOLD_MS)
        
        for i in range(30):
            create_test_project(db_session, name=f"基准测试项目{i}")
        
        project = create_test_project(db_session, name="任务测试项目")
        for i in range(50):
            create_test_task(db_session, project_id=project.id, title=f"基准测试任务{i}")
        
        for i in range(15):
            create_test_agent(db_session, name=f"基准测试代理{i}")
        
        db_session.commit()
    
    def test_root_endpoint_benchmark(self):
        """测试根端点响应时间"""
        self.mock_redis.get_json.return_value = None
        
        result = self.benchmark.benchmark_endpoint(
            self.client, "GET", "/", iterations=30, description="根端点"
        )
        
        assert result.passed, f"根端点响应时间 {result.avg_ms}ms 超过阈值 {RESPONSE_TIME_THRESHOLD_MS}ms"
        assert result.success_rate == 100.0
    
    def test_health_endpoint_benchmark(self):
        """测试健康检查端点响应时间"""
        result = self.benchmark.benchmark_endpoint(
            self.client, "GET", "/health", iterations=30, description="健康检查"
        )
        
        assert result.passed, f"健康检查响应时间 {result.avg_ms}ms 超过阈值"
        assert result.p95_ms < P95_THRESHOLD_MS, f"P95响应时间 {result.p95_ms}ms 超过阈值"
    
    def test_projects_list_benchmark(self):
        """测试项目列表API响应时间"""
        self.mock_redis.get_json.return_value = None
        
        result = self.benchmark.benchmark_endpoint(
            self.client, "GET", "/api/projects/", iterations=50, description="项目列表"
        )
        
        assert result.passed, f"项目列表响应时间 {result.avg_ms}ms 超过阈值"
        assert result.p95_ms < P95_THRESHOLD_MS
    
    def test_projects_paginated_benchmark(self):
        """测试分页项目列表API响应时间"""
        self.mock_redis.get_json.return_value = None
        
        result = self.benchmark.benchmark_endpoint(
            self.client, "GET", "/api/projects/",
            params={"page": 1, "page_size": 12},
            iterations=50, description="分页项目列表"
        )
        
        assert result.passed, f"分页项目列表响应时间 {result.avg_ms}ms 超过阈值"
    
    def test_project_detail_benchmark(self):
        """测试项目详情API响应时间"""
        self.mock_redis.get_json.return_value = None
        
        result = self.benchmark.benchmark_endpoint(
            self.client, "GET", "/api/projects/1", iterations=50, description="项目详情"
        )
        
        assert result.passed, f"项目详情响应时间 {result.avg_ms}ms 超过阈值"
    
    def test_project_stats_benchmark(self):
        """测试项目统计API响应时间"""
        self.mock_redis.get_json.return_value = None
        
        result = self.benchmark.benchmark_endpoint(
            self.client, "GET", "/api/projects/stats", iterations=30, description="项目统计"
        )
        
        assert result.passed, f"项目统计响应时间 {result.avg_ms}ms 超过阈值"
    
    def test_tasks_list_benchmark(self):
        """测试任务列表API响应时间"""
        self.mock_redis.get_json.return_value = None
        
        result = self.benchmark.benchmark_endpoint(
            self.client, "GET", "/api/tasks/", iterations=50, description="任务列表"
        )
        
        assert result.passed, f"任务列表响应时间 {result.avg_ms}ms 超过阈值"
    
    def test_tasks_stats_benchmark(self):
        """测试任务统计API响应时间"""
        self.mock_redis.get_json.return_value = None
        
        result = self.benchmark.benchmark_endpoint(
            self.client, "GET", "/api/tasks/stats", iterations=30, description="任务统计"
        )
        
        assert result.passed, f"任务统计响应时间 {result.avg_ms}ms 超过阈值"
    
    def test_agents_list_benchmark(self):
        """测试代理列表API响应时间"""
        self.mock_redis.get_json.return_value = None
        
        result = self.benchmark.benchmark_endpoint(
            self.client, "GET", "/api/agents/", iterations=30, description="代理列表"
        )
        
        assert result.passed, f"代理列表响应时间 {result.avg_ms}ms 超过阈值"
    
    def test_dashboard_stats_benchmark(self):
        """测试仪表盘统计API响应时间"""
        self.mock_redis.get_json.return_value = None
        
        result = self.benchmark.benchmark_endpoint(
            self.client, "GET", "/api/dashboard/stats", iterations=30, description="仪表盘统计"
        )
        
        assert result.passed, f"仪表盘统计响应时间 {result.avg_ms}ms 超过阈值"
    
    def test_create_project_benchmark(self):
        """测试创建项目API响应时间"""
        self.mock_redis.get_json.return_value = None
        
        project_data = {"name": f"新建项目{time.time()}", "description": "基准测试"}
        
        result = self.benchmark.benchmark_endpoint(
            self.client, "POST", "/api/projects/",
            json_data=project_data,
            iterations=20, description="创建项目"
        )
        
        assert result.avg_ms < RESPONSE_TIME_THRESHOLD_MS * 2, f"创建项目响应时间 {result.avg_ms}ms 超过阈值"
        assert result.success_rate >= 95.0
    
    def test_create_task_benchmark(self):
        """测试创建任务API响应时间"""
        self.mock_redis.get_json.return_value = None
        
        task_data = {"title": f"新建任务{time.time()}", "project_id": 1}
        
        result = self.benchmark.benchmark_endpoint(
            self.client, "POST", "/api/tasks/",
            json_data=task_data,
            iterations=20, description="创建任务"
        )
        
        assert result.avg_ms < RESPONSE_TIME_THRESHOLD_MS * 2, f"创建任务响应时间 {result.avg_ms}ms 超过阈值"
        assert result.success_rate >= 95.0
    
    def test_search_tasks_benchmark(self):
        """测试搜索任务API响应时间"""
        self.mock_redis.get_json.return_value = None
        
        result = self.benchmark.benchmark_endpoint(
            self.client, "GET", "/api/tasks/search",
            params={"keyword": "基准"},
            iterations=30, description="搜索任务"
        )
        
        assert result.avg_ms < RESPONSE_TIME_THRESHOLD_MS * 2, f"搜索任务响应时间 {result.avg_ms}ms 超过阈值"


@pytest.mark.performance
@pytest.mark.benchmark
class TestAPICachedResponseBenchmark:
    """缓存命中场景下的API响应时间基准测试"""
    
    @pytest.fixture(autouse=True)
    def setup_cached_benchmark(self, client, db_session, mock_redis):
        self.client = client
        self.db_session = db_session
        self.mock_redis = mock_redis
        self.benchmark = APIBenchmark(threshold_ms=50)
        
        self.cached_projects = {
            "items": [{"id": i, "name": f"缓存项目{i}"} for i in range(30)],
            "total": 30
        }
    
    def test_cached_projects_list_benchmark(self):
        """测试缓存命中的项目列表响应时间"""
        self.mock_redis.get_json.return_value = self.cached_projects
        
        result = self.benchmark.benchmark_endpoint(
            self.client, "GET", "/api/projects/",
            iterations=50, description="缓存项目列表"
        )
        
        assert result.passed, f"缓存项目列表响应时间 {result.avg_ms}ms 超过阈值 50ms"
        assert result.avg_ms < 50, f"缓存命中响应时间应小于50ms，实际为 {result.avg_ms}ms"
    
    def test_cached_dashboard_stats_benchmark(self):
        """测试缓存命中的仪表盘统计响应时间"""
        self.mock_redis.get_json.return_value = {
            "total_projects": 100,
            "total_tasks": 500,
            "active_agents": 20
        }
        
        result = self.benchmark.benchmark_endpoint(
            self.client, "GET", "/api/dashboard/stats",
            iterations=50, description="缓存仪表盘统计"
        )
        
        assert result.avg_ms < 50, f"缓存仪表盘统计响应时间 {result.avg_ms}ms 超过阈值"


@pytest.mark.performance
@pytest.mark.benchmark
class TestAPILoadBenchmark:
    """API负载基准测试"""
    
    @pytest.fixture(autouse=True)
    def setup_load_benchmark(self, client, db_session, mock_redis):
        self.client = client
        self.db_session = db_session
        self.mock_redis = mock_redis
        
        for i in range(50):
            create_test_project(db_session, name=f"负载测试项目{i}")
        db_session.commit()
    
    def test_concurrent_read_benchmark(self):
        """测试并发读取性能"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        self.mock_redis.get_json.return_value = None
        
        results = []
        
        def make_request():
            start = time.perf_counter()
            response = self.client.get("/api/projects/")
            end = time.perf_counter()
            return response.status_code == 200, (end - start) * 1000
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            for future in as_completed(futures):
                results.append(future.result())
        
        success_count = sum(1 for success, _ in results if success)
        response_times = [t for _, t in results]
        avg_time = statistics.mean(response_times)
        p95_time = self._calculate_percentile(response_times, 95)
        
        assert success_count >= 45, f"并发请求成功率 {success_count/50*100}% 低于90%"
        assert avg_time < 500, f"并发平均响应时间 {avg_time}ms 超过500ms"
        assert p95_time < 1000, f"并发P95响应时间 {p95_time}ms 超过1000ms"
    
    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
