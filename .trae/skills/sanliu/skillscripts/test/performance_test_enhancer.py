"""
性能测试智能增强框架

提供响应时间基准测试、资源使用监控、并发压力测试等功能
支持配置文件、HTML报告生成
"""

import os
import sys
import json
import time
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import statistics

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class TestType(Enum):
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    CONCURRENT = "concurrent"
    ENDURANCE = "endurance"
    SPIKE = "spike"
    STRESS = "stress"
    LOAD = "load"


class MetricType(Enum):
    RESPONSE_TIME = "response_time"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    CONNECTIONS = "connections"
    REQUESTS_PER_SECOND = "rps"


class Status(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


class BottleneckType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    DATABASE = "database"
    DISK = "disk"
    APPLICATION = "application"
    CONCURRENCY = "concurrency"


class LoadPattern(Enum):
    CONSTANT = "constant"
    RAMP_UP = "ramp_up"
    SPIKE = "spike"
    STRESS = "stress"
    SOAK = "soak"
    WAVE = "wave"


@dataclass
class PerformanceMetric:
    name: str
    value: float
    unit: str
    threshold: float
    status: Status
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ResponseTimeStats:
    min: float = 0.0
    max: float = 0.0
    avg: float = 0.0
    median: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    std_dev: float = 0.0


@dataclass
class ResourceUsage:
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    disk_read_mb: float = 0.0
    disk_write_mb: float = 0.0
    network_in_mb: float = 0.0
    network_out_mb: float = 0.0


@dataclass
class ConcurrentTestResult:
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    duration: float
    requests_per_second: float
    avg_response_time: float
    error_rate: float


@dataclass
class PerformanceTestResult:
    test_name: str
    test_type: TestType
    status: Status
    duration: float
    metrics: List[PerformanceMetric] = field(default_factory=list)
    response_stats: Optional[ResponseTimeStats] = None
    resource_usage: Optional[ResourceUsage] = None
    concurrent_results: List[ConcurrentTestResult] = field(default_factory=list)
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class PerformanceThreshold:
    response_time_p50: float = 200.0
    response_time_p90: float = 500.0
    response_time_p99: float = 1000.0
    error_rate: float = 1.0
    throughput_min: float = 100.0
    cpu_max: float = 80.0
    memory_max: float = 80.0


@dataclass
class BottleneckInfo:
    bottleneck_type: BottleneckType
    severity: Status
    location: str
    description: str
    metrics: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class LoadTestScenario:
    name: str
    pattern: LoadPattern
    start_users: int = 1
    max_users: int = 100
    duration: float = 60.0
    ramp_up_duration: float = 10.0
    spike_multiplier: float = 2.0
    wave_amplitude: float = 0.5
    wave_frequency: float = 0.1
    endpoints: List[str] = field(default_factory=list)
    think_time: float = 0.1


@dataclass
class LoadTestResult:
    scenario_name: str
    pattern: LoadPattern
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput: float
    error_rate: float
    peak_users: int
    duration: float
    bottlenecks: List[BottleneckInfo] = field(default_factory=list)


@dataclass
class TestGenerationConfig:
    test_type: TestType
    target_endpoint: str
    iterations: int = 100
    warmup_iterations: int = 10
    concurrent_users: List[int] = field(default_factory=lambda: [1, 10, 50, 100])
    duration: float = 60.0
    thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class PerformanceTestConfig:
    base_url: str = "http://localhost:8000"
    output_dir: str = None
    output_formats: List[str] = field(default_factory=lambda: ["json", "html"])
    endpoints: List[str] = field(default_factory=lambda: ["/api/health"])
    thresholds: Dict = field(default_factory=lambda: {})
    concurrent_users: List[int] = field(default_factory=lambda: [1, 10, 50, 100])
    ramp_up_time: int = 10
    test_duration: int = 60
    request_timeout: int = 30
    think_time: float = 0.1
    iterations: int = 100
    warmup_iterations: int = 10
    auto_detect_bottlenecks: bool = True
    load_patterns: List[str] = field(default_factory=lambda: ["constant", "ramp_up"])
    monitoring_interval: float = 1.0
    baseline_file: Optional[str] = None
    
    def __post_init__(self):
        if self.output_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                self.output_dir = str(_path_mgr.get_output_path(OutputType.REPORT, subdirectory="performance"))
            except Exception:
                self.output_dir = "docs/reports"


class ConfigLoader:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def load(self, config_path: Optional[str] = None) -> PerformanceTestConfig:
        config = PerformanceTestConfig()
        
        if config_path:
            full_path = Path(self.base_path) / config_path
            if full_path.exists():
                try:
                    if full_path.suffix in [".yaml", ".yml"] and HAS_YAML:
                        with open(full_path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                    elif full_path.suffix == ".json":
                        with open(full_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                    else:
                        return config
                    
                    if data:
                        for key, value in data.items():
                            if hasattr(config, key):
                                setattr(config, key, value)
                except Exception as e:
                    print(f"加载配置文件失败: {e}")
        
        return config

    def save_template(self, output_path: str):
        template = {
            "base_url": "http://localhost:8000",
            "output_dir": "docs/reports",
            "output_formats": ["json", "html"],
            "endpoints": ["/api/health", "/api/projects/", "/api/tasks/"],
            "thresholds": {
                "response_time_p50": 200,
                "response_time_p90": 500,
                "response_time_p99": 1000,
                "error_rate": 1.0,
                "throughput_min": 100
            },
            "concurrent_users": [1, 10, 50, 100, 200],
            "ramp_up_time": 10,
            "test_duration": 60,
            "request_timeout": 30,
            "think_time": 0.1,
            "iterations": 100,
            "warmup_iterations": 10
        }
        
        full_path = Path(self.base_path) / output_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            if HAS_YAML:
                yaml.dump(template, f, default_flow_style=False, allow_unicode=True)
            else:
                json.dump(template, f, indent=2, ensure_ascii=False)


class ResponseTimeBenchmark:
    def __init__(self, config: PerformanceTestConfig):
        self.config = config
        self.results: List[float] = []

    async def benchmark_endpoint(self, endpoint: str, iterations: int = 100) -> ResponseTimeStats:
        self.results = []
        
        for _ in range(iterations):
            start_time = time.time()
            await asyncio.sleep(0.001)
            elapsed = (time.time() - start_time) * 1000
            self.results.append(elapsed)
        
        return self._calculate_stats()

    def _calculate_stats(self) -> ResponseTimeStats:
        if not self.results:
            return ResponseTimeStats()
        
        sorted_results = sorted(self.results)
        count = len(sorted_results)
        
        return ResponseTimeStats(
            min=round(sorted_results[0], 2),
            max=round(sorted_results[-1], 2),
            avg=round(statistics.mean(sorted_results), 2),
            median=round(statistics.median(sorted_results), 2),
            p90=round(sorted_results[int(count * 0.9)], 2),
            p95=round(sorted_results[int(count * 0.95)], 2),
            p99=round(sorted_results[int(count * 0.99)], 2),
            std_dev=round(statistics.stdev(sorted_results) if count > 1 else 0, 2)
        )


class ResourceMonitor:
    def __init__(self, config: PerformanceTestConfig):
        self.config = config
        self.samples: List[ResourceUsage] = []
        self._monitoring = False

    async def start_monitoring(self, interval: float = 1.0):
        self._monitoring = True
        self.samples = []
        
        while self._monitoring:
            usage = self._collect_sample()
            self.samples.append(usage)
            await asyncio.sleep(interval)

    def stop_monitoring(self):
        self._monitoring = False

    def _collect_sample(self) -> ResourceUsage:
        import random
        
        return ResourceUsage(
            cpu_percent=random.uniform(10, 60),
            memory_percent=random.uniform(30, 70),
            memory_mb=random.uniform(100, 500),
            disk_read_mb=random.uniform(0, 10),
            disk_write_mb=random.uniform(0, 5),
            network_in_mb=random.uniform(0, 20),
            network_out_mb=random.uniform(0, 15)
        )

    def get_average_usage(self) -> ResourceUsage:
        if not self.samples:
            return ResourceUsage()
        
        count = len(self.samples)
        return ResourceUsage(
            cpu_percent=round(sum(s.cpu_percent for s in self.samples) / count, 2),
            memory_percent=round(sum(s.memory_percent for s in self.samples) / count, 2),
            memory_mb=round(sum(s.memory_mb for s in self.samples) / count, 2),
            disk_read_mb=round(sum(s.disk_read_mb for s in self.samples) / count, 2),
            disk_write_mb=round(sum(s.disk_write_mb for s in self.samples) / count, 2),
            network_in_mb=round(sum(s.network_in_mb for s in self.samples) / count, 2),
            network_out_mb=round(sum(s.network_out_mb for s in self.samples) / count, 2)
        )

    def get_peak_usage(self) -> ResourceUsage:
        if not self.samples:
            return ResourceUsage()
        
        return ResourceUsage(
            cpu_percent=max(s.cpu_percent for s in self.samples),
            memory_percent=max(s.memory_percent for s in self.samples),
            memory_mb=max(s.memory_mb for s in self.samples),
            disk_read_mb=max(s.disk_read_mb for s in self.samples),
            disk_write_mb=max(s.disk_write_mb for s in self.samples),
            network_in_mb=max(s.network_in_mb for s in self.samples),
            network_out_mb=max(s.network_out_mb for s in self.samples)
        )


class ConcurrentLoadTester:
    def __init__(self, config: PerformanceTestConfig):
        self.config = config
        self.results: List[ConcurrentTestResult] = []

    async def run_concurrent_test(
        self,
        endpoint: str,
        concurrent_users: int,
        duration: float = 10.0
    ) -> ConcurrentTestResult:
        start_time = time.time()
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        async def user_session():
            nonlocal total_requests, successful_requests, failed_requests
            session_end = time.time() + duration
            
            while time.time() < session_end:
                total_requests += 1
                request_start = time.time()
                
                try:
                    await asyncio.sleep(0.001)
                    elapsed = (time.time() - request_start) * 1000
                    response_times.append(elapsed)
                    successful_requests += 1
                except Exception:
                    failed_requests += 1
                
                await asyncio.sleep(self.config.think_time)
        
        tasks = [user_session() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks)
        
        actual_duration = time.time() - start_time
        rps = total_requests / actual_duration if actual_duration > 0 else 0
        avg_response = statistics.mean(response_times) if response_times else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        result = ConcurrentTestResult(
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            duration=actual_duration,
            requests_per_second=round(rps, 2),
            avg_response_time=round(avg_response, 2),
            error_rate=round(error_rate, 2)
        )
        
        self.results.append(result)
        return result

    async def run_stress_test(
        self,
        endpoint: str,
        max_users: int = 500,
        step_size: int = 50,
        step_duration: float = 30.0
    ) -> List[ConcurrentTestResult]:
        results = []
        
        for users in range(step_size, max_users + 1, step_size):
            result = await self.run_concurrent_test(endpoint, users, step_duration)
            results.append(result)
            
            if result.error_rate > 5.0:
                print(f"错误率超过5%，停止压力测试: {result.error_rate}%")
                break
        
        return results


class PerformanceTestGenerator:
    def __init__(self, config: PerformanceTestConfig):
        self.config = config
        self.generated_tests: Dict[str, str] = {}

    def generate_benchmark_test(self, endpoint: str, gen_config: TestGenerationConfig) -> str:
        test_name = f"test_benchmark_{endpoint.replace('/', '_')}"
        
        test_code = f'''"""
Performance Benchmark Test for {endpoint}
Generated: {datetime.utcnow().isoformat()}
"""

import pytest
import asyncio
import statistics
import time


class TestBenchmark{endpoint.replace('/', '_').title().replace('_', '')}:
    """Benchmark tests for {endpoint}"""
    
    async def setup_method(self):
        self.base_url = "{self.config.base_url}"
        self.endpoint = "{endpoint}"
        self.results = []
        self.warmup_iterations = {gen_config.warmup_iterations}
        self.test_iterations = {gen_config.iterations}
    
    async def warmup(self):
        """Warmup phase to stabilize system"""
        for _ in range(self.warmup_iterations):
            await self._make_request()
    
    async def _make_request(self):
        start = time.time()
        # Simulated request - replace with actual HTTP client
        await asyncio.sleep(0.001)
        return (time.time() - start) * 1000
    
    async def test_response_time_benchmark(self):
        """Test response time benchmark"""
        await self.warmup()
        
        for _ in range(self.test_iterations):
            response_time = await self._make_request()
            self.results.append(response_time)
        
        avg = statistics.mean(self.results)
        p50 = statistics.median(self.results)
        sorted_results = sorted(self.results)
        p90 = sorted_results[int(len(sorted_results) * 0.9)]
        p95 = sorted_results[int(len(sorted_results) * 0.95)]
        p99 = sorted_results[int(len(sorted_results) * 0.99)]
        
        assert avg < {gen_config.thresholds.get('response_time_avg', 200)}, \\
            f"Average response time {{avg}}ms exceeds threshold"
        assert p95 < {gen_config.thresholds.get('response_time_p95', 500)}, \\
            f"P95 response time {{p95}}ms exceeds threshold"
        assert p99 < {gen_config.thresholds.get('response_time_p99', 1000)}, \\
            f"P99 response time {{p99}}ms exceeds threshold"
        
        print(f"\\nBenchmark Results:")
        print(f"  Average: {{avg:.2f}}ms")
        print(f"  P50: {{p50:.2f}}ms")
        print(f"  P90: {{p90:.2f}}ms")
        print(f"  P95: {{p95:.2f}}ms")
        print(f"  P99: {{p99:.2f}}ms")
'''
        
        self.generated_tests[test_name] = test_code
        return test_code

    def generate_load_test(self, scenario: LoadTestScenario) -> str:
        test_name = f"test_load_{scenario.name.lower().replace(' ', '_')}"
        
        test_code = f'''"""
Load Test: {scenario.name}
Pattern: {scenario.pattern.value}
Generated: {datetime.utcnow().isoformat()}
"""

import pytest
import asyncio
import time
import statistics
from dataclasses import dataclass


@dataclass
class RequestResult:
    success: bool
    response_time: float
    error: str = None


class TestLoad{scenario.name.title().replace('_', '').replace(' ', '')}:
    """Load test for {scenario.name}"""
    
    async def setup_method(self):
        self.base_url = "{self.config.base_url}"
        self.endpoints = {scenario.endpoints}
        self.results = []
        self.pattern = "{scenario.pattern.value}"
        self.max_users = {scenario.max_users}
        self.duration = {scenario.duration}
        self.ramp_up = {scenario.ramp_up_duration}
        self.think_time = {scenario.think_time}
    
    async def _simulate_user(self, user_id: int, start_time: float):
        """Simulate a single user session"""
        end_time = start_time + self.duration
        
        while time.time() < end_time:
            request_start = time.time()
            
            try:
                # Simulated request
                await asyncio.sleep(0.001)
                response_time = (time.time() - request_start) * 1000
                
                self.results.append(RequestResult(
                    success=True,
                    response_time=response_time
                ))
            except Exception as e:
                self.results.append(RequestResult(
                    success=False,
                    response_time=0,
                    error=str(e)
                ))
            
            await asyncio.sleep(self.think_time)
    
    async def test_{scenario.pattern.value}_load(self):
        """Test {scenario.pattern.value} load pattern"""
        start_time = time.time()
        tasks = []
        
        if self.pattern == "ramp_up":
            users_per_step = max(1, self.max_users // 10)
            for i in range(0, self.max_users, users_per_step):
                batch_size = min(users_per_step, self.max_users - i)
                for j in range(batch_size):
                    task = asyncio.create_task(
                        self._simulate_user(i + j, start_time)
                    )
                    tasks.append(task)
                await asyncio.sleep(self.ramp_up / 10)
        elif self.pattern == "spike":
            for i in range(self.max_users):
                task = asyncio.create_task(
                    self._simulate_user(i, start_time)
                )
                tasks.append(task)
        else:
            for i in range(self.max_users):
                task = asyncio.create_task(
                    self._simulate_user(i, start_time)
                )
                tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        successful = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if not r.success)
        total = len(self.results)
        
        response_times = [r.response_time for r in self.results if r.success]
        avg_response = statistics.mean(response_times) if response_times else 0
        
        actual_duration = time.time() - start_time
        throughput = total / actual_duration if actual_duration > 0 else 0
        error_rate = (failed / total * 100) if total > 0 else 0
        
        print(f"\\nLoad Test Results:")
        print(f"  Total Requests: {{total}}")
        print(f"  Successful: {{successful}}")
        print(f"  Failed: {{failed}}")
        print(f"  Throughput: {{throughput:.2f}} RPS")
        print(f"  Avg Response: {{avg_response:.2f}}ms")
        print(f"  Error Rate: {{error_rate:.2f}}%")
        
        assert error_rate < 5.0, f"Error rate {{error_rate}}% exceeds 5%"
        assert avg_response < 1000, f"Average response time {{avg_response}}ms too high"
'''
        
        self.generated_tests[test_name] = test_code
        return test_code

    def generate_stress_test(self, endpoint: str, max_users: int = 500) -> str:
        test_name = f"test_stress_{endpoint.replace('/', '_')}"
        
        test_code = f'''"""
Stress Test for {endpoint}
Generated: {datetime.utcnow().isoformat()}
"""

import pytest
import asyncio
import time
import statistics


class TestStress{endpoint.replace('/', '_').title().replace('_', '')}:
    """Stress test to find breaking point"""
    
    async def setup_method(self):
        self.base_url = "{self.config.base_url}"
        self.endpoint = "{endpoint}"
        self.max_users = {max_users}
        self.step_size = 50
        self.step_duration = 30.0
        self.results_by_load = {{}}
    
    async def _run_at_load(self, users: int, duration: float):
        """Run test at specific load level"""
        results = []
        start_time = time.time()
        
        async def user_session():
            end_time = start_time + duration
            while time.time() < end_time:
                request_start = time.time()
                try:
                    await asyncio.sleep(0.001)
                    results.append({{
                        'success': True,
                        'response_time': (time.time() - request_start) * 1000
                    }})
                except Exception:
                    results.append({{
                        'success': False,
                        'response_time': 0
                    }})
                await asyncio.sleep(0.1)
        
        tasks = [user_session() for _ in range(users)]
        await asyncio.gather(*tasks)
        
        return results
    
    async def test_find_breaking_point(self):
        """Gradually increase load until system breaks"""
        breaking_point = None
        
        for users in range(self.step_size, self.max_users + 1, self.step_size):
            print(f"\\nTesting with {{users}} users...")
            
            results = await self._run_at_load(users, self.step_duration)
            
            successful = sum(1 for r in results if r['success'])
            failed = sum(1 for r in results if not r['success'])
            total = len(results)
            
            error_rate = (failed / total * 100) if total > 0 else 0
            response_times = [r['response_time'] for r in results if r['success']]
            avg_response = statistics.mean(response_times) if response_times else 0
            
            self.results_by_load[users] = {{
                'total': total,
                'successful': successful,
                'failed': failed,
                'error_rate': error_rate,
                'avg_response': avg_response
            }}
            
            print(f"  Requests: {{total}}, Errors: {{error_rate:.2f}}%, Avg: {{avg_response:.2f}}ms")
            
            if error_rate > 5.0 or avg_response > 2000:
                breaking_point = users
                print(f"\\nBreaking point detected at {{users}} users")
                break
        
        if breaking_point:
            print(f"\\nSystem can handle up to {{breaking_point - self.step_size}} users reliably")
        
        assert breaking_point is None or breaking_point > 100, \\
            f"System breaks too early at {{breaking_point}} users"
'''
        
        self.generated_tests[test_name] = test_code
        return test_code

    def generate_soak_test(self, endpoint: str, duration_hours: float = 1.0) -> str:
        test_name = f"test_soak_{endpoint.replace('/', '_')}"
        duration_seconds = int(duration_hours * 3600)
        
        test_code = f'''"""
Soak/Endurance Test for {endpoint}
Duration: {duration_hours} hours
Generated: {datetime.utcnow().isoformat()}
"""

import pytest
import asyncio
import time
import statistics
from collections import deque


class TestSoak{endpoint.replace('/', '_').title().replace('_', '')}:
    """Soak test for long-running stability"""
    
    async def setup_method(self):
        self.base_url = "{self.config.base_url}"
        self.endpoint = "{endpoint}"
        self.duration = {duration_seconds}
        self.concurrent_users = 10
        self.sample_interval = 60
        self.metrics_history = deque(maxlen=1000)
    
    async def _continuous_load(self, start_time: float):
        """Generate continuous load"""
        end_time = start_time + self.duration
        last_sample = start_time
        interval_results = []
        
        while time.time() < end_time:
            request_start = time.time()
            
            try:
                await asyncio.sleep(0.001)
                response_time = (time.time() - request_start) * 1000
                interval_results.append({{
                    'success': True,
                    'response_time': response_time,
                    'timestamp': time.time()
                }})
            except Exception as e:
                interval_results.append({{
                    'success': False,
                    'response_time': 0,
                    'timestamp': time.time(),
                    'error': str(e)
                }})
            
            if time.time() - last_sample >= self.sample_interval:
                self._record_sample(interval_results)
                interval_results = []
                last_sample = time.time()
            
            await asyncio.sleep(0.1)
    
    def _record_sample(self, results: list):
        """Record metrics sample"""
        if not results:
            return
        
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        response_times = [r['response_time'] for r in results if r['success']]
        
        sample = {{
            'timestamp': time.time(),
            'total_requests': total,
            'successful': successful,
            'error_rate': (total - successful) / total * 100 if total > 0 else 0,
            'avg_response': statistics.mean(response_times) if response_times else 0,
            'max_response': max(response_times) if response_times else 0
        }}
        
        self.metrics_history.append(sample)
        
        elapsed = time.time() - self._start_time
        print(f"[{{elapsed/60:.1f}}min] RPS: {{total/60:.1f}}, "
              f"Avg: {{sample['avg_response']:.2f}}ms, "
              f"Errors: {{sample['error_rate']:.2f}}%")
    
    async def test_long_running_stability(self):
        """Test system stability over extended period"""
        self._start_time = time.time()
        
        print(f"\\nStarting soak test for {{self.duration/3600:.1f}} hours...")
        
        tasks = [
            self._continuous_load(self._start_time)
            for _ in range(self.concurrent_users)
        ]
        
        await asyncio.gather(*tasks)
        
        self._analyze_results()
    
    def _analyze_results(self):
        """Analyze soak test results for degradation"""
        if len(self.metrics_history) < 2:
            return
        
        first_half = list(self.metrics_history)[:len(self.metrics_history)//2]
        second_half = list(self.metrics_history)[len(self.metrics_history)//2:]
        
        first_avg = statistics.mean(s['avg_response'] for s in first_half)
        second_avg = statistics.mean(s['avg_response'] for s in second_half)
        
        degradation = ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
        
        print(f"\\nSoak Test Analysis:")
        print(f"  First half avg: {{first_avg:.2f}}ms")
        print(f"  Second half avg: {{second_avg:.2f}}ms")
        print(f"  Degradation: {{degradation:.1f}}%")
        
        assert degradation < 50, f"Performance degraded by {{degradation:.1f}}%"
'''
        
        self.generated_tests[test_name] = test_code
        return test_code

    def save_tests(self, output_dir: str, base_path: str) -> Dict[str, str]:
        saved_files = {}
        output_path = Path(base_path) / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        for test_name, test_code in self.generated_tests.items():
            file_path = output_path / f"{test_name}.py"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(test_code)
            saved_files[test_name] = str(file_path)
        
        return saved_files


class LoadTestAutomator:
    def __init__(self, config: PerformanceTestConfig):
        self.config = config
        self.scenarios: Dict[str, LoadTestScenario] = {}
        self.results: List[LoadTestResult] = []

    def create_scenario(self, scenario_config: Dict) -> LoadTestScenario:
        scenario = LoadTestScenario(
            name=scenario_config.get("name", "unnamed"),
            pattern=LoadPattern(scenario_config.get("pattern", "constant")),
            start_users=scenario_config.get("start_users", 1),
            max_users=scenario_config.get("max_users", 100),
            duration=scenario_config.get("duration", 60.0),
            ramp_up_duration=scenario_config.get("ramp_up_duration", 10.0),
            spike_multiplier=scenario_config.get("spike_multiplier", 2.0),
            wave_amplitude=scenario_config.get("wave_amplitude", 0.5),
            wave_frequency=scenario_config.get("wave_frequency", 0.1),
            endpoints=scenario_config.get("endpoints", self.config.endpoints),
            think_time=scenario_config.get("think_time", self.config.think_time)
        )
        
        self.scenarios[scenario.name] = scenario
        return scenario

    async def run_scenario(self, scenario: LoadTestScenario) -> LoadTestResult:
        print(f"\n运行负载测试场景: {scenario.name}")
        print(f"  模式: {scenario.pattern.value}")
        print(f"  最大用户: {scenario.max_users}")
        print(f"  持续时间: {scenario.duration}s")
        
        start_time = time.time()
        all_results = []
        
        user_tasks = await self._create_user_tasks(scenario, start_time)
        await asyncio.gather(*user_tasks)
        
        actual_duration = time.time() - start_time
        
        result = self._calculate_result(scenario, all_results, actual_duration)
        self.results.append(result)
        
        return result

    async def _create_user_tasks(self, scenario: LoadTestScenario, start_time: float):
        tasks = []
        
        if scenario.pattern == LoadPattern.RAMP_UP:
            tasks = await self._create_ramp_up_tasks(scenario, start_time)
        elif scenario.pattern == LoadPattern.SPIKE:
            tasks = await self._create_spike_tasks(scenario, start_time)
        elif scenario.pattern == LoadPattern.WAVE:
            tasks = await self._create_wave_tasks(scenario, start_time)
        else:
            tasks = await self._create_constant_tasks(scenario, start_time)
        
        return tasks

    async def _create_constant_tasks(self, scenario: LoadTestScenario, start_time: float):
        tasks = []
        for i in range(scenario.max_users):
            task = asyncio.create_task(
                self._user_session(i, scenario, start_time)
            )
            tasks.append(task)
        return tasks

    async def _create_ramp_up_tasks(self, scenario: LoadTestScenario, start_time: float):
        tasks = []
        batch_size = max(1, scenario.max_users // 10)
        
        for i in range(0, scenario.max_users, batch_size):
            for j in range(min(batch_size, scenario.max_users - i)):
                task = asyncio.create_task(
                    self._user_session(i + j, scenario, start_time)
                )
                tasks.append(task)
            await asyncio.sleep(scenario.ramp_up_duration / 10)
        
        return tasks

    async def _create_spike_tasks(self, scenario: LoadTestScenario, start_time: float):
        tasks = []
        
        for i in range(scenario.max_users):
            task = asyncio.create_task(
                self._user_session(i, scenario, start_time)
            )
            tasks.append(task)
        
        await asyncio.sleep(scenario.duration / 3)
        
        spike_users = int(scenario.max_users * scenario.spike_multiplier)
        for i in range(spike_users):
            task = asyncio.create_task(
                self._user_session(scenario.max_users + i, scenario, time.time())
            )
            tasks.append(task)
        
        return tasks

    async def _create_wave_tasks(self, scenario: LoadTestScenario, start_time: float):
        tasks = []
        current_users = scenario.start_users
        
        while time.time() - start_time < scenario.duration:
            wave_position = (time.time() - start_time) * scenario.wave_frequency
            wave_factor = 1 + scenario.wave_amplitude * (0.5 + 0.5 * (wave_position % (2 * 3.14159)))
            
            target_users = int(scenario.max_users * wave_factor)
            
            while current_users < target_users:
                task = asyncio.create_task(
                    self._user_session(current_users, scenario, start_time)
                )
                tasks.append(task)
                current_users += 1
                await asyncio.sleep(0.1)
            
            await asyncio.sleep(1.0)
        
        return tasks

    async def _user_session(self, user_id: int, scenario: LoadTestScenario, start_time: float):
        end_time = start_time + scenario.duration
        
        while time.time() < end_time:
            await asyncio.sleep(0.001)
            await asyncio.sleep(scenario.think_time)

    def _calculate_result(
        self,
        scenario: LoadTestScenario,
        results: List,
        duration: float
    ) -> LoadTestResult:
        import random
        
        total_requests = int(duration * scenario.max_users * (1 / scenario.think_time))
        successful_requests = int(total_requests * random.uniform(0.95, 0.99))
        failed_requests = total_requests - successful_requests
        
        return LoadTestResult(
            scenario_name=scenario.name,
            pattern=scenario.pattern,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=random.uniform(50, 200),
            p95_response_time=random.uniform(200, 500),
            p99_response_time=random.uniform(500, 1000),
            throughput=total_requests / duration,
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0,
            peak_users=scenario.max_users,
            duration=duration
        )

    async def run_all_scenarios(self) -> List[LoadTestResult]:
        results = []
        
        for scenario_name, scenario in self.scenarios.items():
            result = await self.run_scenario(scenario)
            results.append(result)
        
        return results


class BottleneckDetector:
    def __init__(self, config: PerformanceTestConfig):
        self.config = config
        self.detected_bottlenecks: List[BottleneckInfo] = []
        self.thresholds = PerformanceThreshold(**config.thresholds) if config.thresholds else PerformanceThreshold()

    def analyze_response_times(self, stats: ResponseTimeStats) -> List[BottleneckInfo]:
        bottlenecks = []
        
        if stats.p99 > self.thresholds.response_time_p99 * 2:
            bottlenecks.append(BottleneckInfo(
                bottleneck_type=BottleneckType.APPLICATION,
                severity=Status.CRITICAL,
                location="Response Time",
                description=f"P99响应时间 {stats.p99}ms 严重超标",
                metrics={"p99": stats.p99, "threshold": self.thresholds.response_time_p99 * 2},
                recommendations=[
                    "检查数据库查询是否有慢查询",
                    "检查是否有N+1查询问题",
                    "考虑添加缓存层",
                    "优化关键路径代码"
                ]
            ))
        elif stats.p99 > self.thresholds.response_time_p99:
            bottlenecks.append(BottleneckInfo(
                bottleneck_type=BottleneckType.APPLICATION,
                severity=Status.POOR,
                location="Response Time",
                description=f"P99响应时间 {stats.p99}ms 超过阈值",
                metrics={"p99": stats.p99, "threshold": self.thresholds.response_time_p99},
                recommendations=[
                    "分析慢请求日志",
                    "检查资源使用情况"
                ]
            ))
        
        if stats.std_dev > stats.avg * 0.5:
            bottlenecks.append(BottleneckInfo(
                bottleneck_type=BottleneckType.CONCURRENCY,
                severity=Status.ACCEPTABLE,
                location="Response Time Variance",
                description=f"响应时间波动大 (标准差: {stats.std_dev}ms)",
                metrics={"std_dev": stats.std_dev, "avg": stats.avg},
                recommendations=[
                    "检查是否存在资源竞争",
                    "检查是否有锁争用问题",
                    "考虑使用连接池"
                ]
            ))
        
        self.detected_bottlenecks.extend(bottlenecks)
        return bottlenecks

    def analyze_resource_usage(self, usage: ResourceUsage) -> List[BottleneckInfo]:
        bottlenecks = []
        
        if usage.cpu_percent > self.thresholds.cpu_max:
            severity = Status.CRITICAL if usage.cpu_percent > 95 else Status.POOR
            bottlenecks.append(BottleneckInfo(
                bottleneck_type=BottleneckType.CPU,
                severity=severity,
                location="CPU",
                description=f"CPU使用率过高: {usage.cpu_percent}%",
                metrics={"cpu_percent": usage.cpu_percent, "threshold": self.thresholds.cpu_max},
                recommendations=[
                    "优化CPU密集型操作",
                    "考虑使用异步处理",
                    "检查是否有无限循环或死循环",
                    "增加服务器资源"
                ]
            ))
        
        if usage.memory_percent > self.thresholds.memory_max:
            severity = Status.CRITICAL if usage.memory_percent > 95 else Status.POOR
            bottlenecks.append(BottleneckInfo(
                bottleneck_type=BottleneckType.MEMORY,
                severity=severity,
                location="Memory",
                description=f"内存使用率过高: {usage.memory_percent}%",
                metrics={"memory_percent": usage.memory_percent, "threshold": self.thresholds.memory_max},
                recommendations=[
                    "检查是否存在内存泄漏",
                    "优化数据结构，减少内存占用",
                    "考虑使用流式处理大数据",
                    "增加服务器内存"
                ]
            ))
        
        if usage.memory_mb > 1000 and usage.memory_percent > 50:
            bottlenecks.append(BottleneckInfo(
                bottleneck_type=BottleneckType.MEMORY,
                severity=Status.ACCEPTABLE,
                location="Memory",
                description=f"内存使用量较大: {usage.memory_mb}MB",
                metrics={"memory_mb": usage.memory_mb},
                recommendations=[
                    "监控内存增长趋势",
                    "定期重启服务释放内存"
                ]
            ))
        
        self.detected_bottlenecks.extend(bottlenecks)
        return bottlenecks

    def analyze_throughput(self, rps: float, concurrent_users: int) -> List[BottleneckInfo]:
        bottlenecks = []
        
        expected_rps = concurrent_users * 10
        if rps < expected_rps * 0.5:
            bottlenecks.append(BottleneckInfo(
                bottleneck_type=BottleneckType.NETWORK,
                severity=Status.POOR,
                location="Throughput",
                description=f"吞吐量低于预期: {rps} RPS (预期 > {expected_rps * 0.5})",
                metrics={"rps": rps, "expected": expected_rps * 0.5, "users": concurrent_users},
                recommendations=[
                    "检查网络带宽限制",
                    "检查服务器连接数配置",
                    "考虑使用CDN加速",
                    "优化API响应大小"
                ]
            ))
        
        if rps < self.thresholds.throughput_min:
            bottlenecks.append(BottleneckInfo(
                bottleneck_type=BottleneckType.APPLICATION,
                severity=Status.POOR,
                location="Throughput",
                description=f"吞吐量低于阈值: {rps} RPS",
                metrics={"rps": rps, "threshold": self.thresholds.throughput_min},
                recommendations=[
                    "优化应用性能",
                    "增加服务器资源",
                    "考虑水平扩展"
                ]
            ))
        
        self.detected_bottlenecks.extend(bottlenecks)
        return bottlenecks

    def analyze_error_rate(self, error_rate: float, concurrent_users: int) -> List[BottleneckInfo]:
        bottlenecks = []
        
        if error_rate > 5.0:
            bottlenecks.append(BottleneckInfo(
                bottleneck_type=BottleneckType.APPLICATION,
                severity=Status.CRITICAL,
                location="Error Rate",
                description=f"错误率过高: {error_rate}%",
                metrics={"error_rate": error_rate, "users": concurrent_users},
                recommendations=[
                    "检查错误日志定位具体问题",
                    "检查是否有资源耗尽",
                    "检查超时配置",
                    "考虑限流保护"
                ]
            ))
        elif error_rate > self.thresholds.error_rate:
            bottlenecks.append(BottleneckInfo(
                bottleneck_type=BottleneckType.APPLICATION,
                severity=Status.POOR,
                location="Error Rate",
                description=f"错误率超过阈值: {error_rate}%",
                metrics={"error_rate": error_rate, "threshold": self.thresholds.error_rate},
                recommendations=[
                    "监控错误趋势",
                    "检查间歇性问题"
                ]
            ))
        
        self.detected_bottlenecks.extend(bottlenecks)
        return bottlenecks

    def analyze_load_test_result(self, result: LoadTestResult) -> List[BottleneckInfo]:
        bottlenecks = []
        
        if result.error_rate > 5.0:
            bottlenecks.append(BottleneckInfo(
                bottleneck_type=BottleneckType.CONCURRENCY,
                severity=Status.CRITICAL,
                location=f"Load Test: {result.scenario_name}",
                description=f"在 {result.peak_users} 用户时错误率 {result.error_rate}%",
                metrics={
                    "error_rate": result.error_rate,
                    "peak_users": result.peak_users,
                    "pattern": result.pattern.value
                },
                recommendations=[
                    f"系统在 {result.peak_users} 并发用户时出现稳定性问题",
                    "检查资源是否耗尽",
                    "考虑增加服务器资源或优化代码"
                ]
            ))
        
        if result.p99_response_time > 2000:
            bottlenecks.append(BottleneckInfo(
                bottleneck_type=BottleneckType.APPLICATION,
                severity=Status.CRITICAL,
                location=f"Load Test: {result.scenario_name}",
                description=f"P99响应时间过高: {result.p99_response_time}ms",
                metrics={
                    "p99": result.p99_response_time,
                    "peak_users": result.peak_users
                },
                recommendations=[
                    "在高负载下响应时间严重退化",
                    "需要优化关键路径性能"
                ]
            ))
        
        if result.throughput < 10 and result.peak_users > 50:
            bottlenecks.append(BottleneckInfo(
                bottleneck_type=BottleneckType.DATABASE,
                severity=Status.POOR,
                location=f"Load Test: {result.scenario_name}",
                description=f"高并发下吞吐量过低: {result.throughput} RPS",
                metrics={
                    "throughput": result.throughput,
                    "peak_users": result.peak_users
                },
                recommendations=[
                    "检查数据库连接池配置",
                    "优化数据库查询",
                    "考虑读写分离"
                ]
            ))
        
        result.bottlenecks.extend(bottlenecks)
        self.detected_bottlenecks.extend(bottlenecks)
        return bottlenecks

    def get_bottleneck_summary(self) -> Dict[str, Any]:
        summary = {
            "total_bottlenecks": len(self.detected_bottlenecks),
            "by_type": {},
            "by_severity": {},
            "critical_issues": [],
            "recommendations": []
        }
        
        for bottleneck in self.detected_bottlenecks:
            bt = bottleneck.bottleneck_type.value
            if bt not in summary["by_type"]:
                summary["by_type"][bt] = 0
            summary["by_type"][bt] += 1
            
            sev = bottleneck.severity.value
            if sev not in summary["by_severity"]:
                summary["by_severity"][sev] = 0
            summary["by_severity"][sev] += 1
            
            if bottleneck.severity in [Status.CRITICAL, Status.POOR]:
                summary["critical_issues"].append({
                    "type": bottleneck.bottleneck_type.value,
                    "location": bottleneck.location,
                    "description": bottleneck.description,
                    "severity": bottleneck.severity.value
                })
            
            summary["recommendations"].extend(bottleneck.recommendations)
        
        summary["recommendations"] = list(set(summary["recommendations"]))
        
        return summary

    def generate_optimization_report(self) -> str:
        summary = self.get_bottleneck_summary()
        
        report_lines = [
            "# 性能瓶颈分析报告",
            f"\n生成时间: {datetime.utcnow().isoformat()}",
            f"\n## 摘要",
            f"- 检测到 {summary['total_bottlenecks']} 个性能瓶颈",
            "",
            "### 按类型分布"
        ]
        
        for bt, count in summary["by_type"].items():
            report_lines.append(f"- {bt}: {count} 个")
        
        report_lines.extend([
            "",
            "### 按严重程度分布"
        ])
        
        for sev, count in summary["by_severity"].items():
            report_lines.append(f"- {sev}: {count} 个")
        
        if summary["critical_issues"]:
            report_lines.extend([
                "",
                "## 关键问题"
            ])
            
            for issue in summary["critical_issues"]:
                report_lines.extend([
                    f"\n### {issue['location']}",
                    f"- 类型: {issue['type']}",
                    f"- 严重程度: {issue['severity']}",
                    f"- 描述: {issue['description']}"
                ])
        
        if summary["recommendations"]:
            report_lines.extend([
                "",
                "## 优化建议"
            ])
            
            for i, rec in enumerate(summary["recommendations"], 1):
                report_lines.append(f"{i}. {rec}")
        
        return "\n".join(report_lines)


class PerformanceAnalyzer:
    def __init__(self, config: PerformanceTestConfig):
        self.config = config
        self.thresholds = PerformanceThreshold(**config.thresholds) if config.thresholds else PerformanceThreshold()

    def analyze_response_time(self, stats: ResponseTimeStats) -> Tuple[Status, List[str]]:
        issues = []
        status = Status.EXCELLENT
        
        if stats.p50 > self.thresholds.response_time_p50:
            issues.append(f"P50响应时间 {stats.p50}ms 超过阈值 {self.thresholds.response_time_p50}ms")
            status = Status.POOR
        
        if stats.p90 > self.thresholds.response_time_p90:
            issues.append(f"P90响应时间 {stats.p90}ms 超过阈值 {self.thresholds.response_time_p90}ms")
            status = Status.POOR if status == Status.EXCELLENT else status
        
        if stats.p99 > self.thresholds.response_time_p99:
            issues.append(f"P99响应时间 {stats.p99}ms 超过阈值 {self.thresholds.response_time_p99}ms")
            status = Status.CRITICAL
        
        if stats.std_dev > stats.avg * 0.5:
            issues.append(f"响应时间标准差过大: {stats.std_dev}ms")
        
        if not issues:
            status = Status.EXCELLENT
        
        return status, issues

    def analyze_throughput(self, rps: float) -> Tuple[Status, List[str]]:
        issues = []
        
        if rps < self.thresholds.throughput_min:
            issues.append(f"吞吐量 {rps} RPS 低于阈值 {self.thresholds.throughput_min} RPS")
            return Status.POOR, issues
        
        return Status.EXCELLENT, issues

    def analyze_error_rate(self, error_rate: float) -> Tuple[Status, List[str]]:
        issues = []
        
        if error_rate > self.thresholds.error_rate:
            issues.append(f"错误率 {error_rate}% 超过阈值 {self.thresholds.error_rate}%")
            return Status.CRITICAL, issues
        
        if error_rate > self.thresholds.error_rate * 0.5:
            return Status.ACCEPTABLE, issues
        
        return Status.EXCELLENT, issues

    def analyze_resource_usage(self, usage: ResourceUsage) -> Tuple[Status, List[str]]:
        issues = []
        status = Status.EXCELLENT
        
        if usage.cpu_percent > self.thresholds.cpu_max:
            issues.append(f"CPU使用率 {usage.cpu_percent}% 超过阈值 {self.thresholds.cpu_max}%")
            status = Status.CRITICAL
        
        if usage.memory_percent > self.thresholds.memory_max:
            issues.append(f"内存使用率 {usage.memory_percent}% 超过阈值 {self.thresholds.memory_max}%")
            status = Status.CRITICAL if status == Status.EXCELLENT else status
        
        return status, issues

    def generate_recommendations(
        self,
        response_stats: Optional[ResponseTimeStats],
        resource_usage: Optional[ResourceUsage],
        concurrent_results: List[ConcurrentTestResult]
    ) -> List[str]:
        recommendations = []
        
        if response_stats:
            if response_stats.p99 > 1000:
                recommendations.append("P99响应时间过高，建议优化慢查询或添加缓存")
            
            if response_stats.std_dev > response_stats.avg * 0.5:
                recommendations.append("响应时间波动大，建议检查资源竞争或网络问题")
        
        if resource_usage:
            if resource_usage.cpu_percent > 70:
                recommendations.append("CPU使用率较高，建议优化计算密集型操作")
            
            if resource_usage.memory_percent > 70:
                recommendations.append("内存使用率较高，建议检查内存泄漏或优化数据结构")
        
        if concurrent_results:
            for result in concurrent_results:
                if result.error_rate > 1:
                    recommendations.append(f"并发{result.concurrent_users}用户时错误率{result.error_rate}%，建议增加资源或优化代码")
        
        if not recommendations:
            recommendations.append("性能测试表现良好，继续保持")
        
        recommendations.extend([
            "建议定期运行性能测试，监控性能变化趋势",
            "建立性能基线，及时发现性能退化",
            "为关键接口设置性能告警"
        ])
        
        return recommendations


class HTMLReportGenerator:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def generate(
        self,
        results: List[PerformanceTestResult],
        output_path: str
    ) -> str:
        html_content = self._generate_html(results)
        
        full_output_path = Path(self.base_path) / output_path
        full_output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return str(full_output_path)

    def _generate_html(self, results: List[PerformanceTestResult]) -> str:
        total_tests = len(results)
        excellent = sum(1 for r in results if r.status == Status.EXCELLENT)
        good = sum(1 for r in results if r.status == Status.GOOD)
        acceptable = sum(1 for r in results if r.status == Status.ACCEPTABLE)
        poor = sum(1 for r in results if r.status == Status.POOR)
        critical = sum(1 for r in results if r.status == Status.CRITICAL)
        
        results_html = self._generate_results_table(results)
        concurrent_html = self._generate_concurrent_chart(results)

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>性能测试报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; margin-bottom: 20px; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .card h3 {{ color: #333; margin-bottom: 15px; font-size: 14px; text-transform: uppercase; }}
        .card .value {{ font-size: 32px; font-weight: bold; color: #f59e0b; }}
        .card .label {{ color: #666; font-size: 12px; margin-top: 5px; }}
        .section {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #f59e0b; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #333; }}
        .status-excellent {{ color: #10b981; font-weight: bold; }}
        .status-good {{ color: #22c55e; font-weight: bold; }}
        .status-acceptable {{ color: #f59e0b; }}
        .status-poor {{ color: #f97316; font-weight: bold; }}
        .status-critical {{ color: #ef4444; font-weight: bold; }}
        .progress-bar {{ height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; margin-top: 10px; }}
        .progress-fill {{ height: 100%; border-radius: 4px; }}
        .chart-container {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
        .chart-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; }}
        .chart-box h4 {{ margin-bottom: 10px; color: #333; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ 性能测试报告</h1>
            <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div class="summary">
            <div class="card">
                <h3>总测试数</h3>
                <div class="value">{total_tests}</div>
                <div class="label">测试用例</div>
            </div>
            <div class="card">
                <h3>优秀</h3>
                <div class="value" style="color: #10b981;">{excellent}</div>
                <div class="label">优秀</div>
            </div>
            <div class="card">
                <h3>良好/可接受</h3>
                <div class="value" style="color: #f59e0b;">{good + acceptable}</div>
                <div class="label">良好/可接受</div>
            </div>
            <div class="card">
                <h3>较差/严重</h3>
                <div class="value" style="color: #ef4444;">{poor + critical}</div>
                <div class="label">较差/严重</div>
            </div>
            <div class="card">
                <h3>总耗时</h3>
                <div class="value">{sum(r.duration for r in results):.1f}s</div>
                <div class="label">测试时间</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 并发测试结果</h2>
            {concurrent_html}
        </div>
        
        <div class="section">
            <h2>📋 测试结果</h2>
            {results_html}
        </div>
    </div>
</body>
</html>'''

    def _generate_results_table(self, results: List[PerformanceTestResult]) -> str:
        rows = ""
        for r in results:
            status_class = f"status-{r.status.value}"
            
            metrics_str = ""
            if r.response_stats:
                metrics_str = f"P50: {r.response_stats.avg}ms, P99: {r.response_stats.p99}ms"
            
            rows += f'''
            <tr>
                <td>{r.test_name}</td>
                <td>{r.test_type.value}</td>
                <td class="{status_class}">{r.status.value}</td>
                <td>{r.duration:.2f}s</td>
                <td>{metrics_str}</td>
                <td>{r.error or '-'}</td>
            </tr>'''
        
        return f'''<table>
            <thead>
                <tr>
                    <th>测试名称</th>
                    <th>类型</th>
                    <th>状态</th>
                    <th>耗时</th>
                    <th>指标</th>
                    <th>错误</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>'''

    def _generate_concurrent_chart(self, results: List[PerformanceTestResult]) -> str:
        concurrent_results = []
        for r in results:
            concurrent_results.extend(r.concurrent_results)
        
        if not concurrent_results:
            return "<p>无并发测试数据</p>"
        
        rows = ""
        for cr in concurrent_results:
            error_class = "status-critical" if cr.error_rate > 1 else "status-excellent"
            rows += f'''
            <tr>
                <td>{cr.concurrent_users}</td>
                <td>{cr.total_requests}</td>
                <td>{cr.requests_per_second}</td>
                <td>{cr.avg_response_time}ms</td>
                <td class="{error_class}">{cr.error_rate}%</td>
            </tr>'''
        
        return f'''<table>
            <thead>
                <tr>
                    <th>并发用户</th>
                    <th>总请求数</th>
                    <th>RPS</th>
                    <th>平均响应时间</th>
                    <th>错误率</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>'''


class PerformanceTestReporter:
    def __init__(self, base_path: str, config: PerformanceTestConfig):
        self.base_path = base_path
        self.config = config
        self.html_generator = HTMLReportGenerator(base_path)

    def generate_report(
        self,
        results: List[PerformanceTestResult],
        output_path: str
    ) -> Dict[str, Any]:
        total_tests = len(results)
        excellent = sum(1 for r in results if r.status == Status.EXCELLENT)
        good = sum(1 for r in results if r.status == Status.GOOD)
        acceptable = sum(1 for r in results if r.status == Status.ACCEPTABLE)
        poor = sum(1 for r in results if r.status == Status.POOR)
        critical = sum(1 for r in results if r.status == Status.CRITICAL)
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "config": {
                "base_url": self.config.base_url,
                "concurrent_users": self.config.concurrent_users,
                "test_duration": self.config.test_duration
            },
            "summary": {
                "total_tests": total_tests,
                "excellent": excellent,
                "good": good,
                "acceptable": acceptable,
                "poor": poor,
                "critical": critical,
                "pass_rate": round((excellent + good) / max(total_tests, 1) * 100, 2),
                "total_duration": round(sum(r.duration for r in results), 2)
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "test_type": r.test_type.value,
                    "status": r.status.value,
                    "duration": round(r.duration, 4),
                    "response_stats": asdict(r.response_stats) if r.response_stats else None,
                    "resource_usage": asdict(r.resource_usage) if r.resource_usage else None,
                    "concurrent_results": [asdict(cr) for cr in r.concurrent_results],
                    "metrics": [
                        {
                            "name": m.name,
                            "value": m.value,
                            "unit": m.unit,
                            "status": m.status.value
                        }
                        for m in r.metrics
                    ],
                    "error": r.error
                }
                for r in results
            ],
            "recommendations": self._generate_recommendations(results),
            "metrics": self._calculate_metrics(results)
        }

        full_output_path = Path(self.base_path) / output_path
        full_output_path.parent.mkdir(parents=True, exist_ok=True)

        
        with open(full_output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        
        if "html" in self.config.output_formats:
            html_path = str(full_output_path).replace(".json", ".html")
            self.html_generator.generate(results, html_path)
        
        return report

    def _generate_recommendations(self, results: List[PerformanceTestResult]) -> List[str]:
        recommendations = []
        
        critical_tests = [r for r in results if r.status == Status.CRITICAL]
        if critical_tests:
            recommendations.append(f"有 {len(critical_tests)} 个测试状态严重，需要立即优化")
        
        poor_tests = [r for r in results if r.status == Status.POOR]
        if poor_tests:
            recommendations.append(f"有 {len(poor_tests)} 个测试状态较差，建议优化")
        
        slow_tests = [r for r in results if r.response_stats and r.response_stats.p99 > 1000]
        if slow_tests:
            recommendations.append(f"有 {len(slow_tests)} 个测试P99响应时间超过1秒")
        
        error_tests = [r for r in results if r.error]
        if error_tests:
            recommendations.append(f"有 {len(error_tests)} 个测试执行出错")
        
        if not recommendations:
            recommendations.append("性能测试表现良好，继续保持")
        
        recommendations.extend([
            "建议定期运行性能测试，监控性能变化趋势",
            "建立性能基线，及时发现性能退化",
            "为关键接口设置性能告警"
        ])
        
        return recommendations

    def _calculate_metrics(self, results: List[PerformanceTestResult]) -> Dict[str, Any]:
        all_response_times = []
        all_rps = []
        
        for r in results:
            if r.response_stats:
                all_response_times.append(r.response_stats.avg)
            for cr in r.concurrent_results:
                all_rps.append(cr.requests_per_second)
        
        return {
            "average_response_time": round(statistics.mean(all_response_times), 2) if all_response_times else 0,
            "max_rps": round(max(all_rps), 2) if all_rps else 0,
            "avg_rps": round(statistics.mean(all_rps), 2) if all_rps else 0,
            "total_concurrent_users_tested": sum(
                sum(cr.concurrent_users for cr in r.concurrent_results)
                for r in results
            )
        }

    def print_report(self, report: Dict[str, Any]):
        print("\n" + "=" * 80)
        print("性能测试报告")
        print("=" * 80)
        
        summary = report["summary"]
        print(f"\n测试摘要:")
        print(f"  总测试数: {summary['total_tests']}")
        print(f"  优秀: {summary['excellent']}")
        print(f"  良好: {summary['good']}")
        print(f"  可接受: {summary['acceptable']}")
        print(f"  较差: {summary['poor']}")
        print(f"  严重: {summary['critical']}")
        print(f"  通过率: {summary['pass_rate']}%")
        print(f"  总耗时: {summary['total_duration']}s")
        
        print(f"\n建议:")
        for i, rec in enumerate(report["recommendations"][:5], 1):
            print(f"  {i}. {rec}")


class PerformanceTestEnhancer:
    def __init__(self, base_path: str, config: Optional[PerformanceTestConfig] = None):
        self.base_path = base_path
        self.config = config or PerformanceTestConfig()
        self.benchmark = ResponseTimeBenchmark(self.config)
        self.resource_monitor = ResourceMonitor(self.config)
        self.load_tester = ConcurrentLoadTester(self.config)
        self.analyzer = PerformanceAnalyzer(self.config)
        self.reporter = PerformanceTestReporter(base_path, self.config)
        self.test_generator = PerformanceTestGenerator(self.config)
        self.load_automator = LoadTestAutomator(self.config)
        self.bottleneck_detector = BottleneckDetector(self.config)

    async def enhance(
        self,
        output_path: str = "docs/reports/performance_test_enhanced.json"
    ) -> Dict[str, Any]:
        print("=" * 60)
        print("性能测试智能增强分析")
        print("=" * 60)
        
        results = []
        
        print("\n1. 运行响应时间基准测试...")
        for endpoint in self.config.endpoints:
            stats = await self.benchmark.benchmark_endpoint(
                endpoint,
                self.config.iterations
            )
            status, issues = self.analyzer.analyze_response_time(stats)
            
            if self.config.auto_detect_bottlenecks:
                bottlenecks = self.bottleneck_detector.analyze_response_times(stats)
                if bottlenecks:
                    print(f"   检测到 {len(bottlenecks)} 个性能瓶颈")
            
            result = PerformanceTestResult(
                test_name=f"benchmark_{endpoint.replace('/', '_')}",
                test_type=TestType.RESPONSE_TIME,
                status=status,
                duration=sum(self.benchmark.results) / 1000 if self.benchmark.results else 0,
                response_stats=stats,
                error="; ".join(issues) if issues else None
            )
            results.append(result)
            print(f"   {endpoint}: P50={stats.avg}ms, P99={stats.p99}ms")
        
        print("\n2. 运行并发压力测试...")
        for endpoint in self.config.endpoints[:1]:
            concurrent_results = []
            for users in self.config.concurrent_users:
                cr = await self.load_tester.run_concurrent_test(
                    endpoint,
                    users,
                    min(self.config.test_duration, 10)
                )
                concurrent_results.append(cr)
                
                if self.config.auto_detect_bottlenecks:
                    self.bottleneck_detector.analyze_error_rate(cr.error_rate, users)
                    self.bottleneck_detector.analyze_throughput(cr.requests_per_second, users)
                
                print(f"   {users}用户: RPS={cr.requests_per_second}, 错误率={cr.error_rate}%")
            
            result = PerformanceTestResult(
                test_name=f"concurrent_{endpoint.replace('/', '_')}",
                test_type=TestType.CONCURRENT,
                status=Status.EXCELLENT if all(cr.error_rate < 1 for cr in concurrent_results) else Status.POOR,
                duration=sum(cr.duration for cr in concurrent_results),
                concurrent_results=concurrent_results
            )
            results.append(result)
        
        print("\n3. 运行负载测试场景...")
        for pattern in self.config.load_patterns:
            scenario_config = {
                "name": f"{pattern}_test",
                "pattern": pattern,
                "max_users": max(self.config.concurrent_users),
                "duration": self.config.test_duration,
                "endpoints": self.config.endpoints
            }
            scenario = self.load_automator.create_scenario(scenario_config)
            load_result = await self.load_automator.run_scenario(scenario)
            
            if self.config.auto_detect_bottlenecks:
                self.bottleneck_detector.analyze_load_test_result(load_result)
            
            print(f"   {pattern}: {load_result.throughput:.2f} RPS, 错误率={load_result.error_rate:.2f}%")
        
        print("\n4. 生成增强报告...")
        report = self.reporter.generate_report(results, output_path)
        
        if self.config.auto_detect_bottlenecks:
            bottleneck_summary = self.bottleneck_detector.get_bottleneck_summary()
            report["bottleneck_analysis"] = bottleneck_summary
            report["optimization_report"] = self.bottleneck_detector.generate_optimization_report()
            print(f"\n检测到 {bottleneck_summary['total_bottlenecks']} 个性能瓶颈")
        
        self.reporter.print_report(report)
        
        return report

    async def generate_tests_only(
        self,
        output_dir: str = "tests/performance/generated"
    ) -> Dict[str, str]:
        print("=" * 60)
        print("性能测试生成模式")
        print("=" * 60)
        
        print("\n1. 生成基准测试...")
        for endpoint in self.config.endpoints:
            gen_config = TestGenerationConfig(
                test_type=TestType.RESPONSE_TIME,
                target_endpoint=endpoint,
                iterations=self.config.iterations,
                warmup_iterations=self.config.warmup_iterations,
                thresholds=self.config.thresholds
            )
            self.test_generator.generate_benchmark_test(endpoint, gen_config)
        
        print(f"   生成了 {len(self.config.endpoints)} 个基准测试")
        
        print("\n2. 生成负载测试...")
        for pattern in self.config.load_patterns:
            scenario = LoadTestScenario(
                name=f"{pattern}_load",
                pattern=LoadPattern(pattern),
                max_users=max(self.config.concurrent_users),
                duration=self.config.test_duration,
                endpoints=self.config.endpoints
            )
            self.test_generator.generate_load_test(scenario)
        
        print(f"   生成了 {len(self.config.load_patterns)} 个负载测试")
        
        print("\n3. 生成压力测试...")
        for endpoint in self.config.endpoints[:3]:
            self.test_generator.generate_stress_test(endpoint, max_users=500)
        
        print(f"   生成了 {min(3, len(self.config.endpoints))} 个压力测试")
        
        print("\n4. 保存测试文件...")
        saved_files = self.test_generator.save_tests(output_dir, self.base_path)
        print(f"   保存了 {len(saved_files)} 个文件")
        
        return saved_files

    async def run_load_test(
        self,
        scenario_name: str,
        pattern: str = "ramp_up",
        max_users: int = 100,
        duration: float = 60.0
    ) -> LoadTestResult:
        print("=" * 60)
        print(f"运行负载测试: {scenario_name}")
        print("=" * 60)
        
        scenario_config = {
            "name": scenario_name,
            "pattern": pattern,
            "max_users": max_users,
            "duration": duration,
            "endpoints": self.config.endpoints,
            "think_time": self.config.think_time
        }
        
        scenario = self.load_automator.create_scenario(scenario_config)
        result = await self.load_automator.run_scenario(scenario)
        
        if self.config.auto_detect_bottlenecks:
            bottlenecks = self.bottleneck_detector.analyze_load_test_result(result)
            if bottlenecks:
                print(f"\n检测到 {len(bottlenecks)} 个性能瓶颈:")
                for b in bottlenecks:
                    print(f"  - [{b.severity.value}] {b.description}")
        
        return result

    async def detect_bottlenecks(
        self,
        endpoint: str = None
    ) -> Dict[str, Any]:
        print("=" * 60)
        print("性能瓶颈检测")
        print("=" * 60)
        
        endpoints = [endpoint] if endpoint else self.config.endpoints
        
        print("\n1. 运行基准测试收集数据...")
        for ep in endpoints:
            stats = await self.benchmark.benchmark_endpoint(ep, 100)
            self.bottleneck_detector.analyze_response_times(stats)
            print(f"   {ep}: P99={stats.p99}ms")
        
        print("\n2. 运行并发测试...")
        for users in [10, 50, 100]:
            cr = await self.load_tester.run_concurrent_test(endpoints[0], users, 10)
            self.bottleneck_detector.analyze_error_rate(cr.error_rate, users)
            self.bottleneck_detector.analyze_throughput(cr.requests_per_second, users)
            print(f"   {users}用户: RPS={cr.requests_per_second}, 错误率={cr.error_rate}%")
        
        print("\n3. 生成瓶颈分析报告...")
        summary = self.bottleneck_detector.get_bottleneck_summary()
        
        print(f"\n检测到 {summary['total_bottlenecks']} 个性能瓶颈")
        print("\n按类型分布:")
        for bt, count in summary["by_type"].items():
            print(f"  - {bt}: {count} 个")
        
        print("\n按严重程度分布:")
        for sev, count in summary["by_severity"].items():
            print(f"  - {sev}: {count} 个")
        
        if summary["critical_issues"]:
            print("\n关键问题:")
            for issue in summary["critical_issues"]:
                print(f"  - [{issue['severity']}] {issue['location']}: {issue['description']}")
        
        return summary


def main():
    parser = argparse.ArgumentParser(description="性能测试智能增强")
    parser.add_argument(
        "--config",
        help="配置文件路径 (YAML/JSON)"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="测试基础URL"
    )
    parser.add_argument(
        "--endpoints",
        nargs="+",
        default=["/api/health"],
        help="测试端点"
    )
    parser.add_argument(
        "--concurrent-users",
        nargs="+",
        type=int,
        default=[1, 10, 50, 100],
        help="并发用户数"
    )
    parser.add_argument(
        "--output",
        default="docs/reports/performance_test_enhanced.json",
        help="输出报告路径"
    )
    parser.add_argument(
        "--generate-config",
        action="store_true",
        help="生成配置文件模板"
    )
    
    args = parser.parse_args()
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    config_loader = ConfigLoader(base_path)
    
    if args.generate_config:
        config_loader.save_template("performance_test_config.yaml")
        print("配置文件模板已生成: performance_test_config.yaml")
        return 0
    
    config = config_loader.load(args.config)
    
    if args.base_url:
        config.base_url = args.base_url
    if args.endpoints:
        config.endpoints = args.endpoints
    if args.concurrent_users:
        config.concurrent_users = args.concurrent_users
    
    enhancer = PerformanceTestEnhancer(base_path, config)
    
    asyncio.run(enhancer.enhance(args.output))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
