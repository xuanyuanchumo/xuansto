#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试：服务依赖管理器与启动脚本集成

本脚本测试服务依赖管理器与启动脚本的集成功能，包括：
- 服务依赖管理器初始化
- 服务启动顺序验证
- 依赖关系配置检查
- 服务健康状态检查
- 重试机制配置验证

使用示例:
    python test_integration_2.py
    python test_integration_2.py --output json --output-file result.json
    python test_integration_2.py --verbose
"""

import sys
import io
import json
import socket
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

# 添加脚本目录到路径
sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from service_dependency_manager import ServiceDependencyManager, ServiceInfo, ServiceStatus


class TestStatus(Enum):
    """测试步骤状态枚举"""
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestStep:
    """测试步骤数据类"""
    step: str
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
    steps: List[TestStep] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "test_name": self.test_name,
            "timestamp": self.timestamp,
            "success": self.success,
            "steps": [
                {
                    "step": s.step,
                    "status": s.status.value,
                    "details": s.details,
                    "error": s.error,
                    "duration_ms": s.duration_ms
                }
                for s in self.steps
            ],
            "issues": self.issues,
            "metadata": self.metadata,
            "duration_ms": self.duration_ms
        }


def check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """
    检查端口是否可用

    Args:
        host: 主机地址
        port: 端口号
        timeout: 超时时间（秒）

    Returns:
        端口是否可用
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


class IntegrationTestRunner:
    """集成测试运行器"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = self._setup_logger()
        self.result = TestResult(
            test_name="service_dependency_integration",
            timestamp=datetime.now().isoformat(),
            success=True
        )
        self.manager: Optional[ServiceDependencyManager] = None

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

    def run_test(self) -> TestResult:
        """运行集成测试"""
        self._print_header()
        start_time = datetime.now()

        try:
            # 步骤1: 初始化服务依赖管理器
            self._step_init_manager()

            # 步骤2: 验证服务启动顺序
            self._step_validate_startup_order()

            # 步骤3: 检查依赖关系配置
            self._step_check_dependencies()

            # 步骤4: 检查服务健康状态
            self._step_check_health_status()

            # 步骤5: 验证健康检查机制
            self._step_validate_health_check()

            # 步骤6: 验证与start_services.py的集成
            self._step_validate_integration()

            # 步骤7: 验证重试机制配置
            self._step_validate_retry_config()

        except Exception as e:
            self.result.success = False
            self.result.issues.append(str(e))
            self._log_step(f"测试失败: {e}", "error")
            import traceback
from skillscripts.core.path_config_center import get_path_config
            if self.verbose:
                traceback.print_exc()

        end_time = datetime.now()
        self.result.duration_ms = (end_time - start_time).total_seconds() * 1000

        self._print_footer()
        return self.result

    def _print_header(self):
        """打印测试头部信息"""
        print("=" * 60)
        print("测试 2: 服务依赖管理器与启动脚本集成")
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

    def _step_init_manager(self):
        """步骤1: 初始化服务依赖管理器"""
        print("\n步骤 1: 初始化服务依赖管理器...")

        try:
            manager, duration = self._measure_time(ServiceDependencyManager)
            self.manager = manager
            service_count = len(manager.services)

            step = TestStep(
                step="初始化服务依赖管理器",
                status=TestStatus.SUCCESS,
                details=f"已注册 {service_count} 个服务",
                duration_ms=duration
            )
            self.result.steps.append(step)
            print(f"  ✅ 已注册 {service_count} 个服务")
            self._log_step(f"服务管理器初始化完成，耗时 {duration:.2f}ms", "debug")

        except Exception as e:
            step = TestStep(
                step="初始化服务依赖管理器",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.success = False
            self.result.issues.append(f"服务管理器初始化失败: {e}")
            print(f"  ❌ 初始化失败: {e}")
            raise

    def _step_validate_startup_order(self):
        """步骤2: 验证服务启动顺序"""
        print("\n步骤 2: 验证服务启动顺序...")

        try:
            if not self.manager:
                raise RuntimeError("服务管理器未初始化")

            startup_order, duration = self._measure_time(
                self.manager.validate_startup_order
            )

            step = TestStep(
                step="验证服务启动顺序",
                status=TestStatus.SUCCESS,
                details=f"启动顺序: {' -> '.join(startup_order)}",
                duration_ms=duration
            )
            self.result.steps.append(step)
            print(f"  ✅ 启动顺序: {' -> '.join(startup_order)}")
            self._log_step(f"启动顺序验证通过", "debug")

        except ValueError as e:
            step = TestStep(
                step="验证服务启动顺序",
                status=TestStatus.FAILED,
                details=str(e),
                error=f"循环依赖: {e}"
            )
            self.result.steps.append(step)
            self.result.success = False
            self.result.issues.append(f"循环依赖: {e}")
            print(f"  ❌ 循环依赖: {e}")
        except Exception as e:
            step = TestStep(
                step="验证服务启动顺序",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.success = False
            self.result.issues.append(f"启动顺序验证失败: {e}")
            print(f"  ❌ 验证失败: {e}")

    def _step_check_dependencies(self):
        """步骤3: 检查依赖关系配置"""
        print("\n步骤 3: 检查依赖关系配置...")

        try:
            if not self.manager:
                raise RuntimeError("服务管理器未初始化")

            expected_dependencies = {
                "postgres": [],
                "redis": [],
                "backend": ["postgres", "redis"],
                "frontend": ["backend"]
            }

            dependency_check = True
            check_results = {}

            for name, expected_deps in expected_dependencies.items():
                service = self.manager.services.get(name)
                if service:
                    actual_deps = service.dependencies or []
                    if actual_deps == expected_deps:
                        check_results[name] = {
                            "status": "ok",
                            "dependencies": actual_deps
                        }
                        print(f"  ✅ {name}: 依赖 {actual_deps}")
                    else:
                        check_results[name] = {
                            "status": "mismatch",
                            "expected": expected_deps,
                            "actual": actual_deps
                        }
                        print(f"  ⚠️ {name}: 期望 {expected_deps}, 实际 {actual_deps}")
                        dependency_check = False
                else:
                    check_results[name] = {
                        "status": "not_found"
                    }
                    print(f"  ❌ 服务 {name} 未注册")
                    dependency_check = False

            step = TestStep(
                step="检查依赖关系配置",
                status=TestStatus.SUCCESS if dependency_check else TestStatus.WARNING,
                details=check_results
            )
            self.result.steps.append(step)
            self._log_step(f"依赖关系检查完成", "debug")

        except Exception as e:
            step = TestStep(
                step="检查依赖关系配置",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.issues.append(f"依赖关系检查失败: {e}")
            print(f"  ❌ 检查失败: {e}")

    def _step_check_health_status(self):
        """步骤4: 检查服务健康状态"""
        print("\n步骤 4: 检查服务健康状态...")

        try:
            if not self.manager:
                raise RuntimeError("服务管理器未初始化")

            status_report, duration = self._measure_time(
                self.manager.get_service_status_report
            )

            service_statuses = {}
            for name, info in status_report.get("services", {}).items():
                status = "运行中" if info.get("healthy") else "未运行"
                service_statuses[name] = {
                    "status": status,
                    "host": info.get("host"),
                    "port": info.get("port"),
                    "healthy": info.get("healthy")
                }
                print(f"  [{name}] {status} - {info.get('host')}:{info.get('port')}")

            step = TestStep(
                step="检查服务健康状态",
                status=TestStatus.SUCCESS,
                details={
                    "overall_status": status_report.get("overall_status"),
                    "services": service_statuses
                },
                duration_ms=duration
            )
            self.result.steps.append(step)
            self._log_step(f"健康状态检查完成", "debug")

        except Exception as e:
            step = TestStep(
                step="检查服务健康状态",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.issues.append(f"健康状态检查失败: {e}")
            print(f"  ❌ 检查失败: {e}")

    def _step_validate_health_check(self):
        """步骤5: 验证健康检查机制"""
        print("\n步骤 5: 验证健康检查机制...")

        try:
            if not self.manager:
                raise RuntimeError("服务管理器未初始化")

            health_check_results = {}
            start_time = datetime.now()

            for name in self.manager.services:
                is_healthy, duration = self._measure_time(
                    self.manager.check_service_health,
                    name
                )
                health_check_results[name] = {
                    "healthy": is_healthy,
                    "duration_ms": duration
                }
                status_icon = "✅" if is_healthy else "❌"
                print(f"  [{name}] 健康检查: {status_icon} {'通过' if is_healthy else '未通过'}")

            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds() * 1000

            step = TestStep(
                step="验证健康检查机制",
                status=TestStatus.SUCCESS,
                details=health_check_results,
                duration_ms=total_duration
            )
            self.result.steps.append(step)
            self._log_step(f"健康检查机制验证完成", "debug")

        except Exception as e:
            step = TestStep(
                step="验证健康检查机制",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.issues.append(f"健康检查验证失败: {e}")
            print(f"  ❌ 验证失败: {e}")

    def _step_validate_integration(self):
        """步骤6: 验证与start_services.py的集成"""
        print("\n步骤 6: 验证与start_services.py的集成...")

        try:
            start_services_path = Path(__file__).parent / "start_services.py"

            if not start_services_path.exists():
                step = TestStep(
                    step="验证与start_services.py的集成",
                    status=TestStatus.WARNING,
                    details="start_services.py 文件不存在"
                )
                self.result.steps.append(step)
                print("  ⚠️ start_services.py 文件不存在")
                return

            with open(start_services_path, 'r', encoding='utf-8') as f:
                content = f.read()

            integration_checks = {
                "SERVICE_PORTS定义": "SERVICE_PORTS" in content,
                "wait_for_port函数": "wait_for_port" in content,
                "check_port_available函数": "check_port_available" in content,
                "服务启动顺序": "start_docker" in content and "start_backend" in content
            }

            all_checks_passed = all(integration_checks.values())

            for check, passed in integration_checks.items():
                status_icon = "✅" if passed else "❌"
                print(f"  [{status_icon}] {check}")

            step = TestStep(
                step="验证与start_services.py的集成",
                status=TestStatus.SUCCESS if all_checks_passed else TestStatus.WARNING,
                details=integration_checks
            )
            self.result.steps.append(step)
            self._log_step(f"集成验证完成", "debug")

        except Exception as e:
            step = TestStep(
                step="验证与start_services.py的集成",
                status=TestStatus.WARNING,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.issues.append(f"集成验证失败: {e}")
            print(f"  ⚠️ 验证失败: {e}")

    def _step_validate_retry_config(self):
        """步骤7: 验证重试机制配置"""
        print("\n步骤 7: 验证重试机制配置...")

        try:
            if not self.manager:
                raise RuntimeError("服务管理器未初始化")

            retry_configs = {}

            for name, service in self.manager.services.items():
                retry_configs[name] = {
                    "retry_count": service.retry_count,
                    "retry_delay": service.retry_delay,
                    "startup_timeout": service.startup_timeout
                }
                print(f"  [{name}] 重试次数: {service.retry_count}, "
                      f"延迟: {service.retry_delay}s, 超时: {service.startup_timeout}s")

            step = TestStep(
                step="验证重试机制配置",
                status=TestStatus.SUCCESS,
                details=retry_configs
            )
            self.result.steps.append(step)
            self._log_step(f"重试机制配置验证完成", "debug")

        except Exception as e:
            step = TestStep(
                step="验证重试机制配置",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.issues.append(f"重试机制验证失败: {e}")
            print(f"  ❌ 验证失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="服务依赖管理器与启动脚本集成测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python test_integration_2.py
  python test_integration_2.py --output json --output-file result.json
  python test_integration_2.py --verbose
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
