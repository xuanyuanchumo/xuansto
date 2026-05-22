#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能基准测试 (Performance Benchmark)
=====================================

验证按需加载机制和缓存系统的性能指标：
- 路径解析 < 1ms（缓存命中时 < 0.1ms）
- 脚本发现首次扫描后重复调用快100x+
- 并发安全

使用示例:
    python test_performance_benchmark.py
"""

import json
import logging
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from skillscripts.core.path_config_center import PathConfigCenter
from skillscripts.core.script_discovery_cache import ScriptDiscoveryCache


class PerformanceBenchmark:
    """性能基准测试套件"""

    def __init__(self):
        self.logger = self._setup_logging()
        self.results: Dict[str, Dict] = {}

    def _setup_logging(self) -> logging.Logger:
        """配置日志"""
        logger = logging.getLogger("PerformanceBenchmark")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def run_all_benchmarks(self) -> Dict[str, Dict]:
        """
        运行所有基准测试

        Returns:
            包含所有测试结果的字典
        """
        print("\n" + "=" * 80)
        print("🚀 性能基准测试开始")
        print("=" * 80)

        benchmarks = [
            ("路径解析延迟加载", self.benchmark_lazy_loading),
            ("脚本发现缓存性能", self.benchmark_script_discovery),
            ("并发安全性", self.benchmark_concurrency),
            ("快照创建与恢复", self.benchmark_snapshots),
            ("目录按需创建", self.benchmark_ensure_directory)
        ]

        for name, benchmark_func in benchmarks:
            try:
                print(f"\n{'─' * 80}")
                print(f"📊 测试: {name}")
                print(f"{'─' * 80}")

                result = benchmark_func()
                self.results[name] = result

                self._print_result(name, result)

            except Exception as e:
                self.logger.error(f"测试失败 [{name}]: {e}")
                self.results[name] = {
                    'status': 'error',
                    'error': str(e)
                }

        self._generate_summary()

        return self.results

    def benchmark_lazy_loading(self) -> Dict:
        """
        测试路径延迟加载性能

        验证：
        - 首次访问延迟 < 1ms
        - 缓存命中延迟 < 0.1ms
        """
        pcc = PathConfigCenter.instance()

        test_keys = ['DOCS_DIR', 'SCRIPTS_DIR', 'REPORTS_DIR', 'CACHE_DIR', 'VERSIONS_DIR']

        first_access_times = []
        cached_access_times = []

        for key in test_keys:
            start = time.perf_counter()
            path = pcc.lazy_get(key)
            first_elapsed = (time.perf_counter() - start) * 1000
            first_access_times.append(first_elapsed)

            start = time.perf_counter()
            path_cached = pcc.lazy_get(key)
            cached_elapsed = (time.perf_counter() - start) * 1000
            cached_access_times.append(cached_elapsed)

            assert path == path_cached, f"缓存结果不一致: {key}"

        avg_first = sum(first_access_times) / len(first_access_times)
        avg_cached = sum(cached_access_times) / len(cached_access_times)

        speedup = avg_first / avg_cached if avg_cached > 0 else float('inf')

        return {
            'status': 'success',
            'metrics': {
                'first_access_avg_ms': round(avg_first, 4),
                'cached_access_avg_ms': round(avg_cached, 6),
                'speedup_factor': round(speedup, 1),
                'first_access_max_ms': round(max(first_access_times), 4),
                'cached_access_max_ms': round(max(cached_access_times), 6)
            },
            'thresholds': {
                'first_access_max_ms': 1.0,
                'cached_access_max_ms': 0.1
            },
            'passed': avg_first < 1.0 and avg_cached < 0.1
        }

    def benchmark_script_discovery(self) -> Dict:
        """
        测试脚本发现缓存性能

        验证：
        - 首次扫描时间合理
        - 缓存命中后加速100x+
        """
        cache = ScriptDiscoveryCache()

        cache.invalidate()

        test_dir = 'skillscripts/core'
        pattern = '*.py'

        start = time.perf_counter()
        files_first = cache.discover_scripts(test_dir, pattern)
        first_scan_time = (time.perf_counter() - start) * 1000

        iterations = 100
        cached_times = []

        for _ in range(iterations):
            start = time.perf_counter()
            files_cached = cache.discover_scripts(test_dir, pattern)
            elapsed = (time.perf_counter() - start) * 1000
            cached_times.append(elapsed)

            assert len(files_first) == len(files_cached), "缓存结果不一致"

        avg_cached = sum(cached_times) / len(cached_times)
        speedup = first_scan_time / avg_cached if avg_cached > 0 else float('inf')

        return {
            'status': 'success',
            'metrics': {
                'first_scan_ms': round(first_scan_time, 2),
                'cached_avg_ms': round(avg_cached, 4),
                'iterations': iterations,
                'files_found': len(files_first),
                'speedup_factor': round(speedup, 1)
            },
            'thresholds': {
                'min_speedup_factor': 100
            },
            'passed': speedup >= 100
        }

    def benchmark_concurrency(self) -> Dict:
        """
        测试并发安全性

        验证：
        - 多线程同时访问不会出错
        - 结果一致性
        """
        pcc = PathConfigCenter.instance()
        pcc.clear_lazy_cache()

        num_threads = 10
        iterations_per_thread = 50
        errors = []
        results = []

        def worker(thread_id: int) -> List[Dict]:
            thread_results = []
            for i in range(iterations_per_thread):
                try:
                    key = f'DOCS_DIR'
                    start = time.perf_counter()
                    path = pcc.lazy_get(key)
                    elapsed = (time.perf_counter() - start) * 1000

                    thread_results.append({
                        'thread_id': thread_id,
                        'iteration': i,
                        'path': str(path),
                        'elapsed_ms': round(elapsed, 4)
                    })
                except Exception as e:
                    errors.append({
                        'thread_id': thread_id,
                        'iteration': i,
                        'error': str(e)
                    })

            return thread_results

        start_total = time.perf_counter()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {
                executor.submit(worker, tid): tid
                for tid in range(num_threads)
            }

            for future in as_completed(futures):
                results.extend(future.result())

        total_time = (time.perf_counter() - start_total) * 1000
        total_operations = num_threads * iterations_per_thread

        unique_paths = set(r['path'] for r in results)

        return {
            'status': 'success',
            'metrics': {
                'total_operations': total_operations,
                'num_threads': num_threads,
                'iterations_per_thread': iterations_per_thread,
                'total_time_ms': round(total_time, 2),
                'errors': len(errors),
                'unique_paths': len(unique_paths)
            },
            'passed': len(errors) == 0 and len(unique_paths) == 1
        }

    def benchmark_snapshots(self) -> Dict:
        """
        测试快照创建和恢复性能

        验证：
        - 创建快照时间合理
        - 恢复快照时间合理
        """
        pcc = PathConfigCenter.instance()

        snapshot_id = f"BENCH-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        start = time.perf_counter()
        snapshot_data = pcc.create_snapshot(snapshot_id)
        create_time = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        success = pcc.restore_snapshot(snapshot_id)
        restore_time = (time.perf_counter() - start) * 1000

        cleanup_snapshot_file = pcc.SKILL_ROOT / "directory_snapshots" / f"{snapshot_id}.json"
        if cleanup_snapshot_file.exists():
            cleanup_snapshot_file.unlink()

        return {
            'status': 'success',
            'metrics': {
                'create_snapshot_ms': round(create_time, 2),
                'restore_snapshot_ms': round(restore_time, 2),
                'restore_success': success,
                'paths_in_snapshot': len(snapshot_data.get('paths', {}))
            },
            'thresholds': {
                'create_max_ms': 100,
                'restore_max_ms': 50
            },
            'passed': create_time < 100 and restore_time < 50 and success
        }

    def benchmark_ensure_directory(self) -> Dict:
        """
        测试目录按需创建性能

        验证：
        - 创建新目录的时间
        - 已存在目录的快速返回
        """
        pcc = PathConfigCenter.instance()

        categories = ['reports', 'api', 'workflow', 'knowledge']
        version = 'v3.3.0'

        creation_times = []
        existing_times = []

        for category in categories:
            start = time.perf_counter()
            dir_path = pcc.ensure_output_directory(category, version)
            elapsed = (time.perf_counter() - start) * 1000
            creation_times.append(elapsed)

            start = time.perf_counter()
            dir_path_again = pcc.ensure_output_directory(category, version)
            elapsed_again = (time.perf_counter() - start) * 1000
            existing_times.append(elapsed_again)

            assert dir_path == dir_path_again

        avg_creation = sum(creation_times) / len(creation_times)
        avg_existing = sum(existing_times) / len(existing_times)

        return {
            'status': 'success',
            'metrics': {
                'creation_avg_ms': round(avg_creation, 2),
                'existing_avg_ms': round(avg_existing, 4),
                'categories_tested': len(categories)
            },
            'thresholds': {
                'creation_max_ms': 50,
                'existing_max_ms': 5
            },
            'passed': avg_creation < 50 and avg_existing < 5
        }

    def _print_result(self, name: str, result: Dict) -> None:
        """打印单个测试结果"""
        if result.get('status') != 'success':
            print(f"\n❌ 测试失败: {result.get('error', '未知错误')}")
            return

        metrics = result.get('metrics', {})
        thresholds = result.get('thresholds', {})
        passed = result.get('passed', False)

        print(f"\n📈 指标:")
        for key, value in metrics.items():
            threshold = thresholds.get(key)
            if threshold is not None:
                status = "✅" if (
                    (isinstance(value, (int, float)) and value <= threshold) or
                    (isinstance(value, bool) and value is True)
                ) else "⚠️"
                print(f"  {status} {key}: {value} (阈值: ≤{threshold})")
            else:
                print(f"  • {key}: {value}")

        print(f"\n{'✅ 通过' if passed else '❌ 未通过'}")

    def _generate_summary(self) -> None:
        """生成测试总结"""
        print(f"\n{'=' * 80}")
        print("📊 性能基准测试总结")
        print(f"{'=' * 80}")

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r.get('passed', False))
        failed_tests = total_tests - passed_tests

        print(f"\n总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"通过率: {(passed_tests/total_tests*100):.1f}%\n" if total_tests > 0 else "")

        for name, result in self.results.items():
            status_icon = "✅" if result.get('passed', False) else "❌"
            print(f"{status_icon} {name}")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = Path(f'performance_benchmark_{timestamp}.json')

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'summary': {
                        'total': total_tests,
                        'passed': passed_tests,
                        'failed': failed_tests,
                        'pass_rate': round(passed_tests/total_tests*100, 1) if total_tests > 0 else 0
                    },
                    'results': self.results
                }, f, indent=2, ensure_ascii=False)

            print(f"\n📄 详细报告已保存: {report_file}")

        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")


def main():
    """主函数"""
    benchmark = PerformanceBenchmark()
    results = benchmark.run_all_benchmarks()

    all_passed = all(r.get('passed', False) for r in results.values())

    print(f"\n{'=' * 80}")
    if all_passed:
        print("🎉 所有性能测试通过！")
    else:
        print("⚠️ 部分测试未通过，请检查详细报告")
    print(f"{'=' * 80}\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
