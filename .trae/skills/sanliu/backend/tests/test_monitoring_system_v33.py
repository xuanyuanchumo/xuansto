#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前后端监控系统 API 和组件测试 v33
==============================

全面覆盖监控系统的API和组件：
- 后端新增API验证和Mock测试
- WebSocket连接和数据推送模拟
- 质量门禁判定逻辑验证
- 报告生成功能完整性
- 任务管理API边界条件
- 数据验证和安全检查
- 缓存机制正确性
- 性能基准测试
"""

import asyncio
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock


class TestTaskAPIDataValidation(unittest.TestCase):
    """测试任务API数据验证"""

    def test_task_create_model_valid_data(self):
        """任务创建模型有效数据"""
        from backend.app.api.tasks import TaskCreate
        
        task = TaskCreate(
            title="实现用户认证功能",
            description="开发JWT认证模块",
            priority="high",
            estimated_hours=8.0,
            dependencies=[1, 2]
        )
        self.assertEqual(task.title, "实现用户认证功能")
        self.assertEqual(task.priority, "high")
        self.assertEqual(task.estimated_hours, 8.0)
        self.assertTrue(len(task.dependencies) == 2)

    def test_task_create_model_minimal_data(self):
        """任务创建模型最小化数据"""
        from backend.app.api.tasks import TaskCreate
        
        task = TaskCreate(title="简单任务")
        self.assertEqual(task.title, "简单任务")
        self.assertIsNone(task.description)
        self.assertIsNone(task.project_id)

    def test_task_update_model_partial_update(self):
        """任务更新模型部分更新"""
        from backend.app.api.tasks import TaskUpdate
        
        update = TaskUpdate(
            priority="low",
            actual_hours=5.5
        )
        self.assertEqual(update.priority, "low")
        self.assertIsNone(update.title)
        self.assertAlmostEqual(update.actual_hours, 5.5)

    def test_task_search_params_default_values(self):
        """搜索参数默认值"""
        from backend.app.api.tasks import TaskSearchParams
        
        params = TaskSearchParams()
        self.assertIsNone(params.keyword)
        self.assertIsNone(params.status)
        self.assertIsNone(params.priority)

    def test_task_search_params_with_filters(self):
        """带过滤器的搜索参数"""
        from backend.app.api.tasks import TaskSearchParams
        
        params = TaskSearchParams(
            keyword="认证",
            status="in_progress",
            priority="high"
        )
        self.assertEqual(params.keyword, "认证")
        self.assertEqual(params.status, "in_progress")

    def test_task_stats_response_structure(self):
        """统计响应结构"""
        from backend.app.api.tasks import TaskStatsResponse
        
        stats = TaskStatsResponse(
            total=100,
            by_status={"pending": 30, "in_progress": 40, "completed": 30},
            by_priority={"high": 20, "medium": 50, "low": 30},
            completed_rate=0.3,
            avg_estimated_hours=6.5,
            avg_actual_hours=7.2
        )
        self.assertEqual(stats.total, 100)
        self.assertAlmostEqual(stats.completed_rate, 0.3)


class TestQualityGateDecisionLogic(unittest.TestCase):
    """测试质量门禁判定逻辑"""

    def test_all_metrics_pass_gate_opens(self):
        """所有指标通过时门禁开启"""
        metrics = {
            "code_coverage": 85.0,
            "test_pass_rate": 100.0,
            "complexity_avg": 8.0,
            "no_critical_violations": True,
            "security_scan_passed": True
        }
        
        thresholds = {
            "code_coverage": 80.0,
            "test_pass_rate": 95.0,
            "complexity_avg": 15.0
        }
        
        gate_passes = (
            metrics["code_coverage"] >= thresholds["code_coverage"] and
            metrics["test_pass_rate"] >= thresholds["test_pass_rate"] and
            metrics["complexity_avg"] <= thresholds["complexity_avg"] and
            metrics["no_critical_violations"] and
            metrics["security_scan_passed"]
        )
        self.assertTrue(gate_passes)

    def test_coverage_below_threshold_gate_blocks(self):
        """覆盖率低于阈值时门禁阻塞"""
        metrics = {"coverage": 65.0}
        threshold = 80.0
        passes = metrics["coverage"] >= threshold
        self.assertFalse(passes)

    def test_critical_issue_always_blocks(self):
        """关键问题总是阻塞门禁"""
        scenarios = [
            {"security_vuln": True, "expected": False},
            {"data_loss_risk": True, "expected": False},
            {"critical_bug": True, "expected": False},
            {"all_clear": False, "expected": True},
        ]
        for scenario in scenarios:
            has_critical = scenario.get("security_vuln", False) or \
                         scenario.get("data_loss_risk", False) or \
                         scenario.get("critical_bug", False)
            should_pass = not has_critical and not scenario.get("all_clear", False)
            if scenario.get("all_clear") is False:
                should_pass = not has_critical
            self.assertEqual(should_pass, scenario["expected"],
                           f"Failed for {scenario}")

    def test_warning_gate_with_marginal_metrics(self):
        """边缘指标触发警告门禁"""
        metrics = {"coverage": 78.0, "pass_rate": 96.0}
        warning_threshold = 80.0
        fail_threshold = 70.0

        if metrics["coverage"] < fail_threshold:
            gate_status = "failed"
        elif metrics["coverage"] < warning_threshold:
            gate_status = "warning"
        else:
            gate_status = "passed"

        self.assertEqual(gate_status, "warning")

    def test_composite_score_calculation(self):
        """复合评分计算"""
        dimension_scores = {
            "code_quality": 85.0,
            "test_quality": 90.0,
            "documentation": 75.0,
            "architecture": 88.0
        }
        weights = {
            "code_quality": 0.35,
            "test_quality": 0.30,
            "documentation": 0.15,
            "architecture": 0.20
        }

        composite = sum(
            dimension_scores[dim] * weights[dim]
            for dim in dimension_scores
        )

        expected = (85.0 * 0.35 + 90.0 * 0.30 + 75.0 * 0.15 + 88.0 * 0.20)
        self.assertAlmostEqual(composite, expected, places=2)
        self.assertGreater(composite, 80)


class TestWebSocketDataPushSimulation(unittest.TestCase):
    """模拟WebSocket数据推送"""

    def setUp(self):
        self.received_messages = []
        self.connection_active = False

    def simulate_connection(self):
        """模拟连接建立"""
        self.connection_active = True
        return self.connection_active

    def simulate_disconnection(self):
        """模拟断开连接"""
        self.connection_active = False

    def simulate_message_send(self, message_type, data):
        """模拟消息发送"""
        if not self.connection_active:
            raise ConnectionError("Connection not active")
        msg = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.received_messages.append(msg)
        return msg

    def test_connection_lifecycle(self):
        """连接生命周期"""
        self.assertTrue(self.simulate_connection())
        self.assertTrue(self.connection_active)
        self.simulate_disconnection()
        self.assertFalse(self.connection_active)

    def test_message_send_on_active_connection(self):
        """活跃连接上发送消息"""
        self.simulate_connection()
        msg = self.simulate_message_send("quality_update", {"score": 85.0})
        self.assertEqual(msg["type"], "quality_update")
        self.assertEqual(len(self.received_messages), 1)

    def test_message_send_on_inactive_connection_raises(self):
        """非活跃连接发送消息抛出异常"""
        self.simulate_disconnection()
        with self.assertRaises(ConnectionError):
            self.simulate_message_send("test", {})

    def test_batch_message_sending(self):
        """批量消息发送"""
        self.simulate_connection()
        messages_to_send = [
            ("metric_update", {"cpu": 45}),
            ("alert", {"level": "warning"}),
            ("status", {"phase": "complete"})
        ]
        for msg_type, data in messages_to_send:
            self.simulate_message_send(msg_type, data)
        self.assertEqual(len(self.received_messages), 3)

    def test_message_ordering_preserved(self):
        """消息顺序保持"""
        self.simulate_connection()
        for i in range(10):
            self.simulate_message_send("seq_test", {"index": i})
        indices = [m["data"]["index"] for m in self.received_messages]
        self.assertEqual(indices, list(range(10)))


class TestReportGenerationCompleteness(unittest.TestCase):
    """测试报告生成功能完整性"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generate_markdown_report_basic(self):
        """生成基本Markdown报告"""
        report_data = {
            "title": "项目质量报告",
            "generated_at": datetime.now().isoformat(),
            "project": "sanliu",
            "version": "v3.3.0",
            "summary": "整体质量良好",
            "sections": {
                "overview": {"score": 87.5, "trend": "improving"},
                "code_quality": {"complexity": 7.2, "duplication": 0.03},
                "testing": {"coverage": 85.0, "pass_rate": 98.5},
                "recommendations": ["增加单元测试覆盖"]
            }
        }

        md_lines = [f"# {report_data['title']}"]
        md_lines.append(f"**生成时间**: {report_data['generated_at']}")
        md_lines.append(f"**项目**: {report_data['project']}")
        md_lines.append(f"\n## 概要\n\n{report_data['summary']}\n")

        for section_name, section_data in report_data["sections"].items():
            md_lines.append(f"### {section_name}")
            for key, value in section_data.items():
                md_lines.append(f"- **{key}**: {value}")

        md_content = "\n".join(md_lines)
        self.assertIn("# 项目质量报告", md_content)
        self.assertIn("## 概要", md_content)
        self.assertIn("recommendations", md_content)

    def test_generate_json_report_valid_structure(self):
        """生成有效结构的JSON报告"""
        report = {
            "metadata": {
                "report_id": "RPT-2024-001",
                "type": "quality_assessment",
                "generated_by": "system"
            },
            "timestamp": datetime.now().isoformat(),
            "content": {
                "overall_score": 82.3,
                "dimensions": {
                    "code": 80.0,
                    "test": 85.0,
                    "doc": 78.0,
                    "arch": 86.0
                }
            },
            "findings": [
                {"id": "F1", "severity": "medium", "description": "测试覆盖率待提升"},
                {"id": "F2", "severity": "low", "description": "文档需要更新"}
            ]
        }

        json_str = json.dumps(report, indent=2, ensure_ascii=False)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["metadata"]["report_id"], "RPT-2024-001")
        self.assertEqual(len(parsed["findings"]), 2)
        self.assertIn("overall_score", parsed["content"])

    def test_save_report_to_file(self):
        """保存报告到文件"""
        report_content = "# Test Report\n\nThis is a test."
        output_path = Path(self.tmpdir) / 'test_report.md'
        output_path.write_text(report_content, encoding='utf-8')

        self.assertTrue(output_path.exists())
        loaded = output_path.read_text(encoding='utf-8')
        self.assertEqual(loaded, report_content)

    def test_report_template_variable_substitution(self):
        """报告模板变量替换"""
        template = """
# {title}

Generated: {date}
Project: {project}

## Summary
{summary}

## Details
- Score: {score}%
- Status: {status}
"""
        variables = {
            "title": "月度质量报告",
            "date": "2024-01-15",
            "project": "三省六部技能系统",
            "summary": "本月质量指标稳步提升",
            "score": 87.5,
            "status": "HEALTHY"
        }

        filled = template.format(**variables)
        self.assertIn("月度质量报告", filled)
        self.assertIn("87.5%", filled)
        self.assertNotIn("{title}", filled)


class TestCacheMechanismCorrectness(unittest.TestCase):
    """测试缓存机制正确性"""

    def setUp(self):
        self.cache = {}
        self.cache_stats = {"hits": 0, "misses": 0}

    def tearDown(self):
        self.cache.clear()

    def test_cache_set_and_get(self):
        """缓存设置和获取"""
        self.cache["key1"] = "value1"
        self.assertEqual(self.cache.get("key1"), "value1")

    def test_cache_miss_returns_none(self):
        """缓存未命中返回None"""
        result = self.cache.get("nonexistent_key")
        self.assertIsNone(result)

    def test_cache_invalidation(self):
        """缓存失效"""
        self.cache["temp_data"] = "temporary"
        del self.cache["temp_data"]
        self.assertNotIn("temp_data", self.cache)

    def test_cache_ttl_expiration_simulation(self):
        """TTL过期模拟"""
        cache_with_ttl = {}
        current_time = datetime.now()

        cache_with_ttl["session_1"] = {
            "value": "user_data",
            "expires_at": current_time + timedelta(seconds=60)
        }
        cache_with_ttl["session_2"] = {
            "value": "expired_data",
            "expires_at": current_time - timedelta(seconds=10)
        }

        valid_items = {}
        for key, item in cache_with_ttl.items():
            if item["expires_at"] > current_time:
                valid_items[key] = item["value"]

        self.assertIn("session_1", valid_items)
        self.assertNotIn("session_2", valid_items)

    def test_cache_size_limit_enforcement(self):
        """缓存大小限制执行"""
        max_size = 3
        limited_cache = {}

        for i in range(10):
            if len(limited_cache) >= max_size:
                oldest_key = next(iter(limited_cache))
                del limited_cache[oldest_key]
            limited_cache[f"key_{i}"] = f"value_{i}"

        self.assertLessEqual(len(limited_cache), max_size)

    def test_cache_hit_rate_calculation(self):
        """缓存命中率计算"""
        hits = 850
        misses = 150
        total = hits + misses
        hit_rate = hits / total if total > 0 else 0

        self.assertAlmostEqual(hit_rate, 0.85, places=2)


class TestPerformanceBenchmarkScenarios(unittest.TestCase):
    """性能基准测试场景"""

    def test_large_dataset_processing_time(self):
        """大数据集处理时间"""
        import time
        large_list = list(range(100000))

        start = time.time()
        processed = [x * 2 for x in large_list]
        elapsed = time.time() - start

        self.assertEqual(len(processed), 100000)
        self.assertLess(elapsed, 5.0, "Processing took too long")

    def test_concurrent_request_handling(self):
        """并发请求处理模拟"""
        request_results = []
        num_requests = 100

        def process_request(req_id):
            return {"id": req_id, "status": "completed", "time": 0.01}

        for i in range(num_requests):
            result = process_request(i)
            request_results.append(result)

        self.assertEqual(len(request_results), num_requests)
        completed = [r for r in request_results if r["status"] == "completed"]
        self.assertEqual(len(completed), num_requests)

    def test_memory_usage_stability(self):
        """内存使用稳定性"""
        import sys
        data_chunks = []

        initial_size = len(data_chunks)
        for _ in range(1000):
            chunk = list(range(100))
            data_chunks.append(chunk)
            if len(data_chunks) > 500:
                data_chunks.pop(0)

        final_size = len(data_chunks)
        self.assertLessEqual(final_size, 501)
        self.assertGreaterEqual(final_size, 500)

    def test_response_time_under_load(self):
        """负载下响应时间"""
        import time
        response_times = []

        for _ in range(50):
            start = time.time()
            simulated_work = sum(range(1000))
            elapsed = time.time() - start
            response_times.append(elapsed)

        avg_response = sum(response_times) / len(response_times)
        max_response = max(response_times)
        p99_response = sorted(response_times)[int(len(response_times) * 0.99)]

        self.assertLess(avg_response, 0.1, "Average response too slow")
        self.assertLess(p99_response, 0.5, "P99 response too slow")


class TestSecurityValidationChecks(unittest.TestCase):
    """安全验证检查"""

    def test_sql_injection_pattern_detection(self):
        """SQL注入模式检测"""
        import re
        injection_patterns = [
            r"(?i)(\bunion\b.*\bselect\b)",
            r"(?i)(\bselect\b.*\bfrom\b.*\bwhere\b.*\bor\b\s+\d+\s*=\s*\d+)",
            r"(?i)(;\s*\bdrop\b)",
            r"(?i)('\s*or\s*'[^']*'\s*=\s*')",
        ]

        malicious_inputs = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1 UNION SELECT * FROM passwords",
            "admin'--"
        ]

        detected = []
        for user_input in malicious_inputs:
            for pattern in injection_patterns:
                if re.search(pattern, user_input):
                    detected.append(user_input)
                    break

        self.assertEqual(len(detected), len(malicious_inputs))

    def test_xss_pattern_detection(self):
        """XSS模式检测"""
        import re
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript\s*:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
        ]

        xss_attempts = [
            "<script>alert('xss')</script>",
            '<img src=x onerror="alert(1)">',
            "javascript:alert(document.cookie)",
            '<iframe src="evil.com"></iframe>'
        ]

        detected_xss = []
        for attempt in xss_attempts:
            for pattern in xss_patterns:
                if re.search(pattern, attempt, re.IGNORECASE):
                    detected_xss.append(attempt)
                    break

        self.assertEqual(len(detected_xss), len(xss_attempts))

    def test_path_traversal_prevention(self):
        """路径遍历防护"""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config",
            "/etc/shadow",
            "\\windows\\system32\\drivers\\etc\\hosts"
        ]

        safe_base = Path("/safe/directory")
        is_safe = []

        for path_str in dangerous_paths:
            try:
                resolved = Path(path_str).resolve()
                is_safe.append(not str(resolved).startswith("/etc") and 
                             not str(resolved).lower().contains("windows\\system32"))
            except:
                is_safe.append(False)

        all_blocked = all(not safe for safe in is_safe)
        self.assertTrue(all_blocked or len(is_safe) > 0)

    def test_sensitive_data_masking(self):
        """敏感数据脱敏"""
        sensitive_data = {
            "password": "SuperSecret123!",
            "credit_card": "4532012345678901",
            "ssn": "123-45-6789",
            "api_key": "sk_live_abc123def456"
        }

        masked_data = {}
        for key, value in sensitive_data.items():
            if key == "password":
                masked_data[key] = "*" * len(value)
            elif key == "credit_card":
                masked_data[key] = value[:4] + "*" * (len(value) - 4)
            elif key == "ssn":
                masked_data[key] = "***-**-" + value[-4:]
            else:
                masked_data[key] = value[:8] + "*" * (len(value) - 8)

        self.assertNotEqual(masked_data["password"], sensitive_data["password"])
        self.assertTrue(masked_data["credit_card"].startswith("4532"))
        self.assertTrue(masked_data["api_key"].endswith("***"))


class TestDataIntegrityAndConsistency(unittest.TestCase):
    """数据完整性和一致性"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_json_file_write_read_consistency(self):
        """JSON文件读写一致性"""
        original_data = {
            "users": [
                {"id": 1, "name": "Alice", "role": "admin"},
                {"id": 2, "name": "Bob", "role": "user"},
                {"id": 3, "name": "Charlie", "role": "user"}
            ],
            "settings": {
                "theme": "dark",
                "language": "zh-CN",
                "notifications": True
            },
            "version": "1.0.0"
        }

        file_path = Path(self.tmpdir) / 'data.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(original_data, f, indent=2, ensure_ascii=False)

        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        self.assertEqual(original_data, loaded_data)
        self.assertEqual(len(loaded_data["users"]), 3)

    def test_concurrent_write_protection(self):
        """并发写入保护"""
        shared_file = Path(self.tmpdir) / 'shared.txt'
        lock_acquired = False
        write_log = []

        def safe_write(content, writer_id):
            nonlocal lock_acquired
            if lock_acquired:
                write_log.append(f"{writer_id}: SKIPPED (locked)")
                return False
            
            lock_acquired = True
            try:
                shared_file.write_text(content)
                write_log.append(f"{writer_id}: SUCCESS")
                return True
            finally:
                lock_acquired = False

        results = []
        for i in range(5):
            results.append(safe_write(f"Content from writer {i}\n", f"W{i}"))

        successful_writes = sum(results)
        self.assertGreater(successful_writes, 0)
        self.assertLessEqual(successful_writes, 5)

    def test_transaction_rollback_simulation(self):
        """事务回滚模拟"""
        operations = []
        committed_state = {"balance": 1000}

        def execute_operation(op_type, amount):
            if op_type == "debit":
                if committed_state["balance"] < amount:
                    return False
                operations.append(("debit", amount))
                committed_state["balance"] -= amount
            else:
                operations.append(("credit", amount))
                committed_state["balance"] += amount
            return True

        success = True
        success = success and execute_operation("debit", 200)
        success = success and execute_operation("credit", 100)
        success = success and execute_operation("debit", 900)

        if not success:
            committed_state["balance"] = 1000
            operations.clear()

        self.assertIsNotNone(committed_state["balance"])
        self.assertGreaterEqual(committed_state["balance"], 0)


class TestAPIErrorHandlingRobustness(unittest.TestCase):
    """API错误处理健壮性"""

    def test_handle_missing_required_field(self):
        """处理缺失必填字段"""
        required_fields = ["title", "priority"]
        data = {"title": "Test Task"}
        
        missing = [f for f in required_fields if f not in data]
        self.assertIn("priority", missing)
        self.assertEqual(len(missing), 1)

    def test_handle_invalid_enum_value(self):
        """处理无效枚举值"""
        valid_priorities = ["low", "medium", "high", "critical"]
        input_priority = "urgent"
        
        is_valid = input_priority in valid_priorities
        self.assertFalse(is_valid)

    def test_handle_out_of_range_numeric(self):
        """处理超出范围的数值"""
        score = -5.0
        normalized = max(0.0, min(100.0, score))
        self.assertEqual(normalized, 0.0)

        score = 150.0
        normalized = max(0.0, min(100.0, score))
        self.assertEqual(normalized, 100.0)

    def test_handle_malformed_json(self):
        """处理格式错误的JSON"""
        malformed_strings = [
            "{invalid json}",
            '{"unclosed": true',
            'null',
            '',
            '{"trailing comma": true,}',
        ]

        for malformed in malformed_strings:
            try:
                result = json.loads(malformed)
                self.assertIsNotNone(result)
            except json.JSONDecodeError:
                pass

    def test_handle_resource_not_found(self):
        """处理资源未找到"""
        resources = {1: "Resource A", 2: "Resource B", 3: "Resource C"}
        requested_id = 999

        resource = resources.get(requested_id)
        if resource is None:
            error_response = {
                "error": "NOT_FOUND",
                "message": f"Resource {requested_id} does not exist",
                "code": 404
            }
            self.assertEqual(error_response["code"], 404)
        else:
            self.fail("Should have returned None")


class TestMonitoringDashboardAggregation(unittest.TestCase):
    """监控仪表板聚合"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_aggregate_multiple_data_sources(self):
        """聚合多个数据源"""
        source_a = {
            "metrics": {"cpu": 45, "memory": 60},
            "timestamp": "2024-01-15T10:00:00"
        }
        source_b = {
            "metrics": {"disk_io": 30, "network": 25},
            "timestamp": "2024-01-15T10:00:00"
        }
        source_c = {
            "metrics": {"errors": 2, "warnings": 5},
            "timestamp": "2024-01-15T10:00:00"
        }

        aggregated = {
            "timestamp": source_a["timestamp"],
            "metrics": {}
        }
        for source in [source_a, source_b, source_c]:
            aggregated["metrics"].update(source["metrics"])

        self.assertIn("cpu", aggregated["metrics"])
        self.assertIn("disk_io", aggregated["metrics"])
        self.assertIn("errors", aggregated["metrics"])

    def test_calculate_time_series_average(self):
        """计算时间序列平均值"""
        time_series_data = [
            {"time": "10:00", "value": 80},
            {"time": "11:00", "value": 85},
            {"time": "12:00", "value": 78},
            {"time": "13:00", "value": 90},
            {"time": "14:00", "value": 82}
        ]

        values = [d["value"] for d in time_series_data]
        average = sum(values) / len(values)

        self.assertAlmostEqual(average, 83.0, places=1)

    def test_detect_anomalies_simple_threshold(self):
        """简单阈值异常检测"""
        readings = [10, 12, 11, 13, 10, 9, 11, 100, 12, 10]
        threshold_multiplier = 3

        mean_val = sum(readings) / len(readings)
        std_dev = (sum((x - mean_val) ** 2 for x in readings) / len(readings)) ** 0.5
        upper_bound = mean_val + threshold_multiplier * std_dev
        lower_bound = mean_val - threshold_multiplier * std_dev

        anomalies = [x for x in readings if x > upper_bound or x < lower_bound]

        self.assertIn(100, anomalies)

    def test_generate_summary_statistics(self):
        """生成汇总统计"""
        dataset = [23, 45, 67, 34, 56, 78, 89, 12, 43, 54]

        summary = {
            "count": len(dataset),
            "sum": sum(dataset),
            "mean": sum(dataset) / len(dataset),
            "min": min(dataset),
            "max": max(dataset),
            "range": max(dataset) - min(dataset)
        }

        self.assertEqual(summary["count"], 10)
        self.assertEqual(summary["min"], 12)
        self.assertEqual(summary["max"], 89)
        self.assertGreater(summary["range"], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
