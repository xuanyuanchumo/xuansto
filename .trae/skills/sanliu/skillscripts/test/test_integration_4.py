#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试：所有功能协同工作验证

本脚本测试所有功能的协同工作，包括：
- 配置验证
- 服务状态检查
- Agent选择
- 调用记录
- 数据流验证
- 统计报告
- 集成冲突检查

使用示例:
    python test_integration_4.py
    python test_integration_4.py --output json --output-file result.json
    python test_integration_4.py --verbose
"""

import sys
import io
import json
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加路径
scripts_path = Path(__file__).parent
backend_path = Path(__file__).parent.parent / "backend"

sys.path.insert(0, str(scripts_path))
sys.path.insert(0, str(backend_path))

from agent_selector import AgentSelector
from agent_call_history import AgentCallHistory, AgentCallRecord
from service_dependency_manager import ServiceDependencyManager, ServiceInfo


class TestStatus(Enum):
    """测试阶段状态枚举"""
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestPhase:
    """测试阶段数据类"""
    phase: str
    status: TestStatus
    details: Any = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    timestamp: str
    success: bool
    phases: List[TestPhase] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "test_name": self.test_name,
            "timestamp": self.timestamp,
            "success": self.success,
            "phases": [
                {
                    "phase": p.phase,
                    "status": p.status.value,
                    "details": p.details,
                    "error": p.error,
                    "duration_ms": p.duration_ms
                }
                for p in self.phases
            ],
            "issues": self.issues,
            "metadata": self.metadata,
            "duration_ms": self.duration_ms
        }


class IntegrationTestRunner:
    """集成测试运行器"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = self._setup_logger()
        self.result = TestResult(
            test_name="full_integration",
            timestamp=datetime.now().isoformat(),
            success=True
        )
        self.settings = None
        self.service_manager = None
        self.selector = None
        self.history = None
        self.call_id = None

    def _setup_logger(self) -> logging.Logger:
        """配置日志记录器"""
        logger = logging.getLogger("IntegrationTest")
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG if self.verbose else logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _log_step(self, message: str, level: str = "info"):
        """记录测试步骤"""
        if level == "debug":
            self.logger.debug(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        else:
            self.logger.info(message)

    def _measure_time(self, func, *args, **kwargs) -> Tuple[Any, float]:
        """测量函数执行时间"""
        import time
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        duration_ms = (end - start) * 1000
        return result, duration_ms

    def _print_phase_header(self, phase_name: str):
        """打印阶段头部信息"""
        print("\n" + "=" * 40)
        print(f"阶段: {phase_name}")
        print("=" * 40)

    def run_test(self) -> TestResult:
        """运行集成测试"""
        self._print_header()
        start_time = datetime.now()

        try:
            # 阶段1: 配置验证
            self._phase_config_validation()

            # 阶段2: 服务状态检查
            self._phase_service_status()

            # 阶段3: Agent选择
            self._phase_agent_selection()

            # 阶段4: 调用记录
            self._phase_call_recording()

            # 阶段5: 数据流验证
            self._phase_data_flow()

            # 阶段6: 统计报告
            self._phase_statistics()

            # 阶段7: 集成冲突检查
            self._phase_conflict_check()

        except Exception as e:
            self.result.success = False
            self.result.issues.append(str(e))
            self._log_step(f"测试失败: {e}", "error")
            import traceback
            if self.verbose:
                traceback.print_exc()

        end_time = datetime.now()
        self.result.duration_ms = (end_time - start_time).total_seconds() * 1000

        self._print_footer()
        return self.result

    def _print_header(self):
        """打印测试头部信息"""
        print("=" * 60)
        print("测试 4: 所有功能协同工作验证")
        print("=" * 60)
        self._log_step("开始集成测试", "debug")

    def _print_footer(self):
        """打印测试底部信息"""
        print("\n" + "=" * 60)
        status = "✅ 通过" if self.result.success else "❌ 失败"
        print(f"测试结果: {status}")
        if self.result.duration_ms:
            print(f"耗时: {self.result.duration_ms:.2f}ms")
        print("=" * 60)

    def _phase_config_validation(self):
        """阶段1: 配置验证"""
        self._print_phase_header("配置验证")

        try:
            from app.config import settings

            self.settings = settings
            config_validation, duration = self._measure_time(
                settings.validate_database_config
            )

            print(f"  配置有效性: {config_validation.get('valid', False)}")
            if config_validation.get('warnings'):
                print(f"  警告: {config_validation['warnings']}")

            phase = TestPhase(
                phase="配置验证",
                status=TestStatus.SUCCESS,
                details={
                    "valid": config_validation.get('valid', False),
                    "warnings": config_validation.get('warnings', [])
                },
                duration_ms=duration
            )
            self.result.phases.append(phase)
            self._log_step(f"配置验证完成", "debug")

        except Exception as e:
            phase = TestPhase(
                phase="配置验证",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.phases.append(phase)
            self.result.success = False
            self.result.issues.append(f"配置验证失败: {e}")
            print(f"  ❌ 配置验证失败: {e}")

    def _phase_service_status(self):
        """阶段2: 服务状态检查"""
        self._print_phase_header("服务状态检查")

        try:
            self.service_manager, duration = self._measure_time(ServiceDependencyManager)
            status_report, _ = self._measure_time(
                self.service_manager.get_service_status_report
            )

            print(f"  整体状态: {status_report.get('overall_status', 'unknown')}")

            services_status = {}
            for name, info in status_report.get('services', {}).items():
                status = "运行中" if info.get('healthy') else "未运行"
                services_status[name] = info.get('healthy', False)
                print(f"  [{name}] {status}")

            phase = TestPhase(
                phase="服务状态检查",
                status=TestStatus.SUCCESS,
                details={
                    "overall_status": status_report.get('overall_status'),
                    "services": services_status
                },
                duration_ms=duration
            )
            self.result.phases.append(phase)
            self._log_step(f"服务状态检查完成", "debug")

        except Exception as e:
            phase = TestPhase(
                phase="服务状态检查",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.phases.append(phase)
            self.result.issues.append(f"服务状态检查失败: {e}")
            print(f"  ❌ 服务状态检查失败: {e}")

    def _phase_agent_selection(self):
        """阶段3: Agent选择"""
        self._print_phase_header("Agent选择")

        try:
            self.selector, init_duration = self._measure_time(AgentSelector)
            print(f"  已加载 {len(self.selector.agent_registry)} 个Agent")

            task_description = "开发一个用户认证系统，包括登录、注册和密码重置功能"
            context = {
                "tech_stack": "Python FastAPI PostgreSQL",
                "project_type": "web"
            }

            selection, select_duration = self._measure_time(
                self.selector.select_best_agent,
                task_description,
                context
            )

            details = {
                "agent_count": len(self.selector.agent_registry),
                "best_match": None,
                "alternatives_count": 0
            }

            if selection.get("best_match"):
                best_agent = selection["best_match"]
                details["best_match"] = best_agent
                details["alternatives_count"] = len(selection.get("alternatives", []))

                print(f"  最佳匹配: {best_agent['name']} (分数: {best_agent.get('score', 0)})")
                print(f"  部门: {best_agent.get('department', 'N/A')}")
                print(f"  技能: {best_agent.get('skill', 'N/A')}")

                if selection.get("alternatives"):
                    print(f"  备选Agent:")
                    for alt in selection["alternatives"][:3]:
                        print(f"    - {alt['name']} (分数: {alt.get('score', 0)})")

            phase = TestPhase(
                phase="Agent选择",
                status=TestStatus.SUCCESS,
                details=details,
                duration_ms=init_duration + select_duration
            )
            self.result.phases.append(phase)
            self._log_step(f"Agent选择完成", "debug")

        except Exception as e:
            phase = TestPhase(
                phase="Agent选择",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.phases.append(phase)
            self.result.issues.append(f"Agent选择失败: {e}")
            print(f"  ❌ Agent选择失败: {e}")

    def _phase_call_recording(self):
        """阶段4: 调用记录"""
        self._print_phase_header("调用记录")

        try:
            self.history, init_duration = self._measure_time(AgentCallHistory)

            # 获取选中的Agent名称
            agent_name = "Backend Architect"
            if self.selector and hasattr(self.selector, 'last_selection'):
                agent_name = self.selector.last_selection.get("best_match", {}).get("name", agent_name)

            call_record_dict, gen_duration = self._measure_time(
                self.selector.generate_call_record if self.selector else AgentSelector().generate_call_record,
                agent_name=agent_name,
                task="开发一个用户认证系统，包括登录、注册和密码重置功能",
                context={
                    "tech_stack": "Python FastAPI PostgreSQL",
                    "project_type": "web"
                },
                result={
                    "status": "success",
                    "deliverables": ["认证API", "用户模型", "测试用例"],
                    "quality_metrics": {
                        "code_coverage": 0.85,
                        "security_score": 0.92
                    }
                }
            )

            record = AgentCallRecord(
                call_id=call_record_dict["call_id"],
                timestamp=call_record_dict["timestamp"],
                caller=call_record_dict["caller"],
                agent_name=call_record_dict["agent"],
                task=call_record_dict["task"],
                context=call_record_dict["context"],
                status="success",
                result=call_record_dict["result"],
                duration_ms=2500,
                quality_score=0.92
            )

            self.call_id, record_duration = self._measure_time(
                self.history.record_call,
                record
            )

            saved_record, verify_duration = self._measure_time(
                self.history.get_call,
                self.call_id
            )

            print(f"  调用ID: {self.call_id}")
            print(f"  Agent: {agent_name}")
            print(f"  状态: success")
            print(f"  记录验证: {'成功' if saved_record else '失败'}")

            phase = TestPhase(
                phase="调用记录",
                status=TestStatus.SUCCESS,
                details={
                    "call_id": self.call_id,
                    "agent": agent_name,
                    "verified": saved_record is not None
                },
                duration_ms=init_duration + gen_duration + record_duration + verify_duration
            )
            self.result.phases.append(phase)
            self._log_step(f"调用记录完成", "debug")

        except Exception as e:
            phase = TestPhase(
                phase="调用记录",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.phases.append(phase)
            self.result.issues.append(f"调用记录失败: {e}")
            print(f"  ❌ 调用记录失败: {e}")

    def _phase_data_flow(self):
        """阶段5: 数据流验证"""
        self._print_phase_header("数据流验证")

        try:
            data_flow = {
                "config_to_service": {
                    "db_host": getattr(self.settings, 'DATABASE_HOST', 'N/A') if self.settings else 'N/A',
                    "db_port": getattr(self.settings, 'DATABASE_PORT', 'N/A') if self.settings else 'N/A',
                    "service_manager_has_postgres": "postgres" in self.service_manager.services if self.service_manager else False
                },
                "service_to_selector": {
                    "backend_port": self.service_manager.services.get("backend", {}).port if self.service_manager and "backend" in self.service_manager.services else None,
                    "agent_count": len(self.selector.agent_registry) if self.selector else 0
                },
                "selector_to_history": {
                    "call_recorded": self.call_id is not None,
                    "agent_matched": self.selector is not None and hasattr(self.selector, 'agent_registry')
                }
            }

            print("  配置 -> 服务:")
            print(f"    数据库配置: {data_flow['config_to_service']['db_host']}:{data_flow['config_to_service']['db_port']}")
            print(f"    服务管理器: {'已初始化' if data_flow['config_to_service']['service_manager_has_postgres'] else '未初始化'}")

            print("  服务 -> Agent选择器:")
            print(f"    后端端口: {data_flow['service_to_selector']['backend_port']}")
            print(f"    Agent数量: {data_flow['service_to_selector']['agent_count']}")

            print("  Agent选择器 -> 调用历史:")
            print(f"    调用已记录: {data_flow['selector_to_history']['call_recorded']}")
            print(f"    Agent已匹配: {data_flow['selector_to_history']['agent_matched']}")

            phase = TestPhase(
                phase="数据流验证",
                status=TestStatus.SUCCESS,
                details=data_flow
            )
            self.result.phases.append(phase)
            self._log_step(f"数据流验证完成", "debug")

        except Exception as e:
            phase = TestPhase(
                phase="数据流验证",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.phases.append(phase)
            self.result.issues.append(f"数据流验证失败: {e}")
            print(f"  ❌ 数据流验证失败: {e}")

    def _phase_statistics(self):
        """阶段6: 统计报告"""
        self._print_phase_header("统计报告")

        try:
            if not self.history:
                self.history = AgentCallHistory()

            stats, duration = self._measure_time(self.history.get_statistics)

            print(f"  总调用数: {stats.get('total_calls', 0)}")
            print(f"  成功调用: {stats.get('successful_calls', 0)}")
            print(f"  平均耗时: {stats.get('avg_duration_ms', 0):.2f}ms")
            print(f"  平均质量分: {stats.get('avg_quality_score', 0):.2f}")

            if stats.get('top_agents'):
                print(f"  热门Agent:")
                for agent in stats['top_agents'][:3]:
                    print(f"    - {agent.get('agent_name', 'Unknown')}: {agent.get('call_count', 0)} 次")

            phase = TestPhase(
                phase="统计报告",
                status=TestStatus.SUCCESS,
                details={
                    "total_calls": stats.get('total_calls', 0),
                    "successful_calls": stats.get('successful_calls', 0),
                    "avg_duration_ms": stats.get('avg_duration_ms'),
                    "avg_quality_score": stats.get('avg_quality_score')
                },
                duration_ms=duration
            )
            self.result.phases.append(phase)
            self._log_step(f"统计报告生成完成", "debug")

        except Exception as e:
            phase = TestPhase(
                phase="统计报告",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.phases.append(phase)
            self.result.issues.append(f"统计报告生成失败: {e}")
            print(f"  ❌ 统计报告生成失败: {e}")

    def _phase_conflict_check(self):
        """阶段7: 集成冲突检查"""
        self._print_phase_header("集成冲突检查")

        try:
            conflicts = []

            if self.settings and self.service_manager:
                db_port = getattr(self.settings, 'DATABASE_PORT', None)
                pg_service = self.service_manager.services.get("postgres")
                if pg_service and db_port and db_port != pg_service.port:
                    conflicts.append(f"数据库端口配置不一致: config={db_port}, service_manager={pg_service.port}")

                redis_port = getattr(self.settings, 'REDIS_PORT', None)
                redis_service = self.service_manager.services.get("redis")
                if redis_service and redis_port and redis_port != redis_service.port:
                    conflicts.append(f"Redis端口配置不一致: config={redis_port}, service_manager={redis_service.port}")

            if conflicts:
                print("  发现冲突:")
                for conflict in conflicts:
                    print(f"    - {conflict}")
                self.result.issues.extend(conflicts)
            else:
                print("  ✅ 未发现集成冲突")

            phase = TestPhase(
                phase="集成冲突检查",
                status=TestStatus.SUCCESS if not conflicts else TestStatus.WARNING,
                details={
                    "conflicts_count": len(conflicts),
                    "conflicts": conflicts
                }
            )
            self.result.phases.append(phase)
            self._log_step(f"集成冲突检查完成", "debug")

        except Exception as e:
            phase = TestPhase(
                phase="集成冲突检查",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.phases.append(phase)
            self.result.issues.append(f"集成冲突检查失败: {e}")
            print(f"  ❌ 集成冲突检查失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="所有功能协同工作验证",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python test_integration_4.py
  python test_integration_4.py --output json --output-file result.json
  python test_integration_4.py --verbose
        """
    )

    parser.add_argument(
        "--output",
        choices=["console", "json"],
        default="console",
        help="输出格式 (默认: console)"
    )

    parser.add_argument(
        "--output-file",
        type=str,
        help="输出文件路径 (JSON格式时使用)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )

    args = parser.parse_args()

    # 运行测试
    runner = IntegrationTestRunner(verbose=args.verbose)
    result = runner.run_test()

    # 输出结果
    if args.output == "json":
        output_data = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)

        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_data)
            print(f"\n结果已保存到: {output_path}")
        else:
            print("\n完整结果:")
            print(output_data)
    else:
        print("\n完整结果:")
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
