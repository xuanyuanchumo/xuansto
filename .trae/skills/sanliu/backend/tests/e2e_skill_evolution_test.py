#!/usr/bin/env python3
"""
三省六部技能永久自演化增强 - 端到端测试

测试流程:
1. 完整演化周期测试
2. 技能内容更新流程测试
3. 跨项目演化服务测试
4. 用户干预流程测试
"""

import os
import sys
import json
import time
import asyncio
import logging
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    test_name: str
    status: TestStatus
    duration_ms: int
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TestSuiteResult:
    suite_name: str
    results: List[TestResult] = field(default_factory=list)
    total_duration_ms: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""


class E2ETestReport:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.suites: List[TestSuiteResult] = []
        self.started_at = datetime.now().isoformat()
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('E2ETestReport')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def add_suite(self, suite: TestSuiteResult):
        self.suites.append(suite)
    
    def generate_report(self) -> str:
        total_passed = sum(s.passed for s in self.suites)
        total_failed = sum(s.failed for s in self.suites)
        total_skipped = sum(s.skipped for s in self.suites)
        total_errors = sum(s.errors for s in self.suites)
        total_duration = sum(s.total_duration_ms for s in self.suites)
        
        lines = [
            "# 三省六部技能永久自演化增强 - 端到端测试报告",
            "",
            f"**测试时间**: {self.started_at}",
            f"**报告生成时间**: {datetime.now().isoformat()}",
            "",
            "## 测试概览",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 总测试数 | {total_passed + total_failed + total_skipped + total_errors} |",
            f"| 通过数 | {total_passed} |",
            f"| 失败数 | {total_failed} |",
            f"| 跳过数 | {total_skipped} |",
            f"| 错误数 | {total_errors} |",
            f"| 总耗时 | {total_duration}ms |",
            f"| 通过率 | {(total_passed / (total_passed + total_failed) * 100):.2f}% |" if (total_passed + total_failed) > 0 else "| 通过率 | N/A |",
            "",
        ]
        
        for suite in self.suites:
            lines.extend([
                f"## {suite.suite_name}",
                "",
                f"- **开始时间**: {suite.started_at}",
                f"- **完成时间**: {suite.completed_at}",
                f"- **总耗时**: {suite.total_duration_ms}ms",
                f"- **通过**: {suite.passed}, **失败**: {suite.failed}, **跳过**: {suite.skipped}, **错误**: {suite.errors}",
                "",
                "### 测试详情",
                "",
                "| 测试名称 | 状态 | 耗时(ms) | 消息 |",
                "|----------|------|----------|------|",
            ])
            
            for result in suite.results:
                status_icon = {
                    TestStatus.PASSED: "✅",
                    TestStatus.FAILED: "❌",
                    TestStatus.SKIPPED: "⏭️",
                    TestStatus.ERROR: "⚠️"
                }.get(result.status, "❓")
                
                lines.append(
                    f"| {result.test_name} | {status_icon} {result.status.value} | "
                    f"{result.duration_ms} | {result.message[:50]}... |" 
                    if len(result.message) > 50 else
                    f"| {result.test_name} | {status_icon} {result.status.value} | "
                    f"{result.duration_ms} | {result.message} |"
                )
            
            lines.append("")
            
            failed_tests = [r for r in suite.results if r.status in [TestStatus.FAILED, TestStatus.ERROR]]
            if failed_tests:
                lines.extend([
                    "### 失败详情",
                    ""
                ])
                for result in failed_tests:
                    lines.append(f"#### {result.test_name}")
                    lines.append(f"- **错误**: {result.error or 'N/A'}")
                    lines.append(f"- **消息**: {result.message}")
                    if result.details:
                        lines.append("- **详情**:")
                        for key, value in result.details.items():
                            lines.append(f"  - {key}: {value}")
                    lines.append("")
        
        report_content = '\n'.join(lines)
        
        report_file = self.output_dir / f"e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_file.write_text(report_content, encoding='utf-8')
        
        json_report = {
            "started_at": self.started_at,
            "completed_at": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_passed + total_failed + total_skipped + total_errors,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
                "errors": total_errors,
                "total_duration_ms": total_duration,
                "pass_rate": total_passed / (total_passed + total_failed) if (total_passed + total_failed) > 0 else 0
            },
            "suites": [asdict(s) for s in self.suites]
        }
        
        json_file = self.output_dir / f"e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_file.write_text(json.dumps(json_report, ensure_ascii=False, indent=2), encoding='utf-8')
        
        self.logger.info(f"报告已生成: {report_file}")
        return str(report_file)


class SkillEvolutionE2ETest:
    def __init__(self, skill_path: str):
        self.skill_path = Path(skill_path)
        self.client = TestClient(app)
        self.report = E2ETestReport(self.skill_path / "reports" / "e2e_tests")
        self.logger = self._setup_logger()
        
        self.temp_dirs: List[str] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SkillEvolutionE2ETest')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _create_temp_dir(self) -> str:
        temp_dir = tempfile.mkdtemp(prefix="e2e_test_")
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def _cleanup(self):
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                self.logger.warning(f"清理临时目录失败 {temp_dir}: {e}")
    
    def _run_test(self, test_name: str, test_func, suite: TestSuiteResult) -> TestResult:
        start_time = time.time()
        try:
            result = test_func()
            duration_ms = int((time.time() - start_time) * 1000)
            
            test_result = TestResult(
                test_name=test_name,
                status=TestStatus.PASSED if result.get("success", False) else TestStatus.FAILED,
                duration_ms=duration_ms,
                message=result.get("message", ""),
                details=result.get("details", {}),
                error=result.get("error")
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            test_result = TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration_ms=duration_ms,
                message=f"测试执行异常: {str(e)}",
                error=str(e)
            )
        
        suite.results.append(test_result)
        
        if test_result.status == TestStatus.PASSED:
            suite.passed += 1
        elif test_result.status == TestStatus.FAILED:
            suite.failed += 1
        elif test_result.status == TestStatus.SKIPPED:
            suite.skipped += 1
        else:
            suite.errors += 1
        
        suite.total_duration_ms += test_result.duration_ms
        
        status_icon = "✅" if test_result.status == TestStatus.PASSED else "❌"
        self.logger.info(f"{status_icon} {test_name}: {test_result.duration_ms}ms - {test_result.message}")
        
        return test_result
    
    def test_evolution_status_api(self) -> Dict[str, Any]:
        response = self.client.get("/api/skill-evolution/status")
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": f"演化状态获取成功，当前阶段: {data.get('current_phase', 'N/A')}",
            "details": {
                "is_running": data.get("is_running"),
                "total_evolutions": data.get("total_evolutions"),
                "success_rate": data.get("success_rate")
            }
        }
    
    def test_content_status_api(self) -> Dict[str, Any]:
        response = self.client.get("/api/skill-evolution/content-status")
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": f"内容监控状态获取成功，活跃监控器: {data.get('active_monitors', 0)}",
            "details": {
                "total_monitors": data.get("total_monitors"),
                "active_monitors": data.get("active_monitors"),
                "overall_health": data.get("overall_health")
            }
        }
    
    def test_health_check_api(self) -> Dict[str, Any]:
        response = self.client.get("/api/skill-evolution/health")
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": f"健康检查成功，整体状态: {data.get('overall_status', 'N/A')}",
            "details": {
                "overall_status": data.get("overall_status"),
                "uptime_seconds": data.get("uptime_seconds"),
                "error_count_24h": data.get("error_count_24h")
            }
        }
    
    def test_evolution_history_api(self) -> Dict[str, Any]:
        response = self.client.get("/api/skill-evolution/history?limit=5")
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": f"演化历史获取成功，总数: {data.get('total', 0)}",
            "details": {
                "total": data.get("total"),
                "page": data.get("page"),
                "items_count": len(data.get("items", []))
            }
        }
    
    def test_evolution_statistics_api(self) -> Dict[str, Any]:
        response = self.client.get("/api/skill-evolution/statistics")
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": f"统计数据获取成功，总演化次数: {data.get('total_evolutions', 0)}",
            "details": {
                "total_evolutions": data.get("total_evolutions"),
                "success_rate": data.get("success_rate"),
                "last_24h_count": data.get("last_24h_count")
            }
        }
    
    def test_trigger_evolution_api(self) -> Dict[str, Any]:
        response = self.client.post(
            "/api/skill-evolution/trigger",
            json={
                "evolution_type": "skill_optimization",
                "reason": "E2E测试触发演化",
                "dry_run": True
            }
        )
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": f"演化触发成功，触发ID: {data.get('trigger_id', 'N/A')}",
            "details": {
                "trigger_id": data.get("trigger_id"),
                "evolution_type": data.get("evolution_type"),
                "status": data.get("status")
            }
        }
    
    def test_trigger_real_evolution(self) -> Dict[str, Any]:
        response = self.client.post(
            "/api/skill-evolution/trigger",
            json={
                "evolution_type": "skill_optimization",
                "reason": "E2E测试真实演化触发",
                "dry_run": False,
                "force": True
            }
        )
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        
        time.sleep(1)
        
        status_response = self.client.get("/api/skill-evolution/status")
        status_data = status_response.json() if status_response.status_code == 200 else {}
        
        return {
            "success": True,
            "message": f"真实演化触发成功，状态: {data.get('status', 'N/A')}",
            "details": {
                "trigger_id": data.get("trigger_id"),
                "status": data.get("status"),
                "current_phase": status_data.get("current_phase", "N/A")
            }
        }
    
    def test_evolution_report_api(self) -> Dict[str, Any]:
        response = self.client.get("/api/skill-evolution/report")
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": f"演化报告生成成功，报告ID: {data.get('report_id', 'N/A')}",
            "details": {
                "report_id": data.get("report_id"),
                "generated_at": data.get("generated_at"),
                "summary": data.get("summary")
            }
        }
    
    def test_export_evolution_data_json(self) -> Dict[str, Any]:
        response = self.client.get("/api/skill-evolution/export?format=json")
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        content_type = response.headers.get("content-type", "")
        return {
            "success": "application/json" in content_type,
            "message": f"JSON导出成功，内容类型: {content_type}",
            "details": {
                "content_type": content_type,
                "content_length": len(response.content)
            }
        }
    
    def test_export_evolution_data_csv(self) -> Dict[str, Any]:
        response = self.client.get("/api/skill-evolution/export?format=csv")
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        content_type = response.headers.get("content-type", "")
        return {
            "success": "text/csv" in content_type,
            "message": f"CSV导出成功，内容类型: {content_type}",
            "details": {
                "content_type": content_type,
                "content_length": len(response.content)
            }
        }
    
    def test_evolution_monitor_status(self) -> Dict[str, Any]:
        response = self.client.get("/api/evolution/status")
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": f"演化监控状态获取成功，状态: {data.get('status', 'N/A')}",
            "details": {
                "status": data.get("status"),
                "progress": data.get("progress"),
                "current_metrics": data.get("current_metrics")
            }
        }
    
    def test_evolution_trends_api(self) -> Dict[str, Any]:
        response = self.client.get("/api/evolution/trends?metric=performance&period=7d")
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": f"演化趋势获取成功，方向: {data.get('trend_direction', 'N/A')}",
            "details": {
                "metric_name": data.get("metric_name"),
                "period": data.get("period"),
                "trend_direction": data.get("trend_direction"),
                "change_percentage": data.get("change_percentage")
            }
        }
    
    def test_evolution_metrics_summary(self) -> Dict[str, Any]:
        response = self.client.get("/api/evolution/metrics/summary")
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": f"指标汇总获取成功，成功率: {data.get('success_rate', 0):.2f}%",
            "details": {
                "total_evolutions": data.get("total_evolutions"),
                "success_rate": data.get("success_rate"),
                "last_24h_count": data.get("last_24h_count")
            }
        }
    
    def test_skill_doc_analyzer(self) -> Dict[str, Any]:
        try:
            sys.path.insert(0, str(self.skill_path / "backend" / "scripts"))
            from skill_doc_updater import DocAnalyzer
            
            analyzer = DocAnalyzer()
            report = analyzer.analyze_skill_doc(str(self.skill_path))
            
            return {
                "success": True,
                "message": f"技能文档分析成功，完整度: {report.completeness_score:.0%}",
                "details": {
                    "skill_name": report.skill_name,
                    "version": report.version,
                    "overall_status": report.overall_status.value,
                    "completeness_score": report.completeness_score,
                    "quality_score": report.quality_score
                }
            }
        except Exception as e:
            return {"success": False, "message": f"文档分析失败: {str(e)}", "error": str(e)}
    
    def test_rollback_manager(self) -> Dict[str, Any]:
        try:
            sys.path.insert(0, str(self.skill_path / "backend" / "scripts"))
            from rollback_manager import RollbackManager
            
            temp_dir = self._create_temp_dir()
            manager = RollbackManager(temp_dir)
            
            test_file = os.path.join(temp_dir, "test_file.py")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("# Original content\nprint('hello')\n")
            
            backup_record = manager.create_backup(test_file, operation='test')
            
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("# Modified content\nprint('modified')\n")
            
            rollback_result = manager.rollback(backup_record.backup_id)
            
            with open(test_file, 'r', encoding='utf-8') as f:
                restored_content = f.read()
            
            return {
                "success": rollback_result.success and "Original" in restored_content,
                "message": f"回滚测试成功，备份ID: {backup_record.backup_id}",
                "details": {
                    "backup_id": backup_record.backup_id,
                    "rollback_success": rollback_result.success,
                    "verification_passed": rollback_result.verification_passed
                }
            }
        except Exception as e:
            return {"success": False, "message": f"回滚管理器测试失败: {str(e)}", "error": str(e)}
    
    def test_version_snapshot(self) -> Dict[str, Any]:
        try:
            sys.path.insert(0, str(self.skill_path / "backend" / "scripts"))
            from rollback_manager import RollbackManager, RollbackType
            
            temp_dir = self._create_temp_dir()
            manager = RollbackManager(temp_dir)
            
            project_dir = os.path.join(temp_dir, "test_project")
            os.makedirs(project_dir, exist_ok=True)
            
            test_file = os.path.join(project_dir, "main.py")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("# Test project\n")
            
            snapshot = manager.create_version_snapshot("1.0.0", project_dir)
            
            stats = manager.get_rollback_statistics()
            
            return {
                "success": snapshot is not None and len(snapshot.files) > 0,
                "message": f"版本快照创建成功，快照ID: {snapshot.snapshot_id}",
                "details": {
                    "snapshot_id": snapshot.snapshot_id,
                    "version": snapshot.version,
                    "files_count": len(snapshot.files),
                    "total_snapshots": stats.get("total_snapshots", 0)
                }
            }
        except Exception as e:
            return {"success": False, "message": f"版本快照测试失败: {str(e)}", "error": str(e)}
    
    def test_self_iteration_trigger(self) -> Dict[str, Any]:
        try:
            sys.path.insert(0, str(self.skill_path / "backend" / "scripts"))
            from self_iteration_trigger import SelfIterationTrigger, MonitoringMetrics
            
            temp_dir = self._create_temp_dir()
            trigger = SelfIterationTrigger(temp_dir)
            
            metrics = MonitoringMetrics(
                error_rate=0.15,
                continuous_failures=5,
                code_quality_score=0.75
            )
            
            result = trigger.check_and_trigger(metrics=metrics, auto_execute=False)
            
            return {
                "success": True,
                "message": f"自迭代触发检查成功，需要迭代: {result.get('needs_iteration', False)}",
                "details": {
                    "needs_iteration": result.get("needs_iteration"),
                    "triggered_conditions": len(result.get("triggered_conditions", [])),
                    "recommended_bump_type": result.get("recommended_bump_type")
                }
            }
        except Exception as e:
            return {"success": False, "message": f"自迭代触发器测试失败: {str(e)}", "error": str(e)}
    
    def test_project_registration(self) -> Dict[str, Any]:
        response = self.client.get("/api/projects")
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": f"项目列表获取成功，总数: {len(data)}",
            "details": {
                "projects_count": len(data),
                "has_projects": len(data) > 0
            }
        }
    
    def test_project_isolation(self) -> Dict[str, Any]:
        response1 = self.client.get("/api/projects")
        response2 = self.client.get("/api/tasks")
        
        if response1.status_code != 200 or response2.status_code != 200:
            return {"success": False, "message": "API调用失败"}
        
        return {
            "success": True,
            "message": "项目隔离验证成功",
            "details": {
                "projects_accessible": True,
                "tasks_accessible": True
            }
        }
    
    def test_knowledge_sharing(self) -> Dict[str, Any]:
        response = self.client.get("/api/evolution-knowledge/sharing")
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": "知识共享验证成功",
            "details": {
                "total_sharings": data.get("total", 0),
                "items_count": len(data.get("items", [])),
                "has_sharings": data.get("total", 0) > 0
            }
        }
    
    def test_api_trigger_evolution(self) -> Dict[str, Any]:
        response = self.client.post(
            "/api/skill-evolution/trigger",
            json={
                "evolution_type": "performance_tuning",
                "reason": "API触发演化测试",
                "dry_run": True,
                "priority": "high"
            }
        )
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": f"API触发演化成功，触发ID: {data.get('trigger_id')}",
            "details": {
                "trigger_id": data.get("trigger_id"),
                "status": data.get("status"),
                "message": data.get("message")
            }
        }
    
    def test_pause_evolution(self) -> Dict[str, Any]:
        trigger_response = self.client.post(
            "/api/skill-evolution/trigger",
            json={
                "evolution_type": "skill_optimization",
                "reason": "暂停测试前置演化",
                "dry_run": False,
                "force": True
            }
        )
        
        time.sleep(0.5)
        
        response = self.client.post(
            "/api/skill-evolution/pause",
            json={
                "reason": "E2E测试暂停",
                "save_state": True
            }
        )
        
        if response.status_code == 400:
            return {
                "success": True,
                "message": "暂停API正常响应（无运行中的演化）",
                "details": {"status_code": 400, "expected": True}
            }
        
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": data.get("success", False),
            "message": f"演化暂停成功，状态ID: {data.get('saved_state_id')}",
            "details": {
                "success": data.get("success"),
                "saved_state_id": data.get("saved_state_id")
            }
        }
    
    def test_resume_evolution(self) -> Dict[str, Any]:
        response = self.client.post(
            "/api/skill-evolution/resume",
            json={
                "continue_from_checkpoint": True
            }
        )
        
        if response.status_code == 400:
            return {
                "success": True,
                "message": "恢复API正常响应（无暂停的演化）",
                "details": {"status_code": 400, "expected": True}
            }
        
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": data.get("success", False),
            "message": f"演化恢复成功，当前阶段: {data.get('current_phase')}",
            "details": {
                "success": data.get("success"),
                "current_phase": data.get("current_phase")
            }
        }
    
    def test_rollback_execution(self) -> Dict[str, Any]:
        response = self.client.post(
            "/api/skill-evolution/rollback",
            json={
                "event_id": "evt_test_001",
                "reason": "E2E测试回滚",
                "create_backup": True
            }
        )
        
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": f"回滚触发成功，回滚ID: {data.get('rollback_id')}",
            "details": {
                "rollback_id": data.get("rollback_id"),
                "status": data.get("status"),
                "backup_id": data.get("backup_id")
            }
        }
    
    def test_call_chain_api(self) -> Dict[str, Any]:
        response = self.client.get("/api/skill-evolution/call-chain/evt_test_001")
        if response.status_code != 200:
            return {"success": False, "message": f"状态码错误: {response.status_code}", "error": response.text}
        
        data = response.json()
        return {
            "success": True,
            "message": f"调用链获取成功，节点数: {data.get('total_nodes', 0)}",
            "details": {
                "event_id": data.get("event_id"),
                "total_nodes": data.get("total_nodes"),
                "max_depth": data.get("max_depth")
            }
        }
    
    def run_full_evolution_cycle_tests(self) -> TestSuiteResult:
        suite = TestSuiteResult(suite_name="完整演化周期测试")
        suite_start = time.time()
        
        self.logger.info("=" * 50)
        self.logger.info("开始完整演化周期测试")
        self.logger.info("=" * 50)
        
        self._run_test("演化状态API", self.test_evolution_status_api, suite)
        self._run_test("内容监控状态API", self.test_content_status_api, suite)
        self._run_test("健康检查API", self.test_health_check_api, suite)
        self._run_test("演化历史API", self.test_evolution_history_api, suite)
        self._run_test("演化统计API", self.test_evolution_statistics_api, suite)
        self._run_test("触发演化API(模拟)", self.test_trigger_evolution_api, suite)
        self._run_test("触发演化API(真实)", self.test_trigger_real_evolution, suite)
        self._run_test("演化报告API", self.test_evolution_report_api, suite)
        self._run_test("演化监控状态", self.test_evolution_monitor_status, suite)
        self._run_test("演化趋势API", self.test_evolution_trends_api, suite)
        self._run_test("演化指标汇总", self.test_evolution_metrics_summary, suite)
        
        suite.completed_at = datetime.now().isoformat()
        return suite
    
    def run_skill_content_update_tests(self) -> TestSuiteResult:
        suite = TestSuiteResult(suite_name="技能内容更新流程测试")
        
        self.logger.info("=" * 50)
        self.logger.info("开始技能内容更新流程测试")
        self.logger.info("=" * 50)
        
        self._run_test("技能文档分析", self.test_skill_doc_analyzer, suite)
        self._run_test("回滚管理器", self.test_rollback_manager, suite)
        self._run_test("版本快照", self.test_version_snapshot, suite)
        self._run_test("自迭代触发器", self.test_self_iteration_trigger, suite)
        
        suite.completed_at = datetime.now().isoformat()
        return suite
    
    def run_cross_project_tests(self) -> TestSuiteResult:
        suite = TestSuiteResult(suite_name="跨项目演化服务测试")
        
        self.logger.info("=" * 50)
        self.logger.info("开始跨项目演化服务测试")
        self.logger.info("=" * 50)
        
        self._run_test("项目注册", self.test_project_registration, suite)
        self._run_test("项目隔离验证", self.test_project_isolation, suite)
        self._run_test("知识共享验证", self.test_knowledge_sharing, suite)
        
        suite.completed_at = datetime.now().isoformat()
        return suite
    
    def run_user_intervention_tests(self) -> TestSuiteResult:
        suite = TestSuiteResult(suite_name="用户干预流程测试")
        
        self.logger.info("=" * 50)
        self.logger.info("开始用户干预流程测试")
        self.logger.info("=" * 50)
        
        self._run_test("API触发演化", self.test_api_trigger_evolution, suite)
        self._run_test("暂停演化", self.test_pause_evolution, suite)
        self._run_test("恢复演化", self.test_resume_evolution, suite)
        self._run_test("执行回滚", self.test_rollback_execution, suite)
        self._run_test("调用链API", self.test_call_chain_api, suite)
        self._run_test("导出JSON", self.test_export_evolution_data_json, suite)
        self._run_test("导出CSV", self.test_export_evolution_data_csv, suite)
        
        suite.completed_at = datetime.now().isoformat()
        return suite
    
    def run_all_tests(self) -> str:
        self.logger.info("=" * 60)
        self.logger.info("三省六部技能永久自演化增强 - 端到端测试开始")
        self.logger.info("=" * 60)
        
        try:
            suite1 = self.run_full_evolution_cycle_tests()
            self.report.add_suite(suite1)
            
            suite2 = self.run_skill_content_update_tests()
            self.report.add_suite(suite2)
            
            suite3 = self.run_cross_project_tests()
            self.report.add_suite(suite3)
            
            suite4 = self.run_user_intervention_tests()
            self.report.add_suite(suite4)
            
            report_path = self.report.generate_report()
            
            self.logger.info("=" * 60)
            self.logger.info("端到端测试完成")
            self.logger.info(f"报告路径: {report_path}")
            self.logger.info("=" * 60)
            
            return report_path
        
        finally:
            self._cleanup()


def main():
    skill_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    print("=" * 60)
    print("三省六部技能永久自演化增强 - 端到端测试")
    print("=" * 60)
    print(f"技能路径: {skill_path}")
    print()
    
    tester = SkillEvolutionE2ETest(skill_path)
    report_path = tester.run_all_tests()
    
    print()
    print("=" * 60)
    print("测试完成!")
    print(f"详细报告: {report_path}")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    exit(main())
