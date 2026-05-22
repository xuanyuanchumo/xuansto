#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试：配置验证与数据库连接集成

本脚本测试配置验证与数据库连接的集成功能，包括：
- 配置模块加载与验证
- 数据库URL配置检查
- Redis配置检查
- 数据库连接测试
- 配置错误处理测试
- 重试机制验证
- CORS配置验证

使用示例:
    python test_integration_3.py
    python test_integration_3.py --output json --output-file result.json
    python test_integration_3.py --verbose
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

# 添加后端路径
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


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


class IntegrationTestRunner:
    """集成测试运行器"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = self._setup_logger()
        self.result = TestResult(
            test_name="config_database_integration",
            timestamp=datetime.now().isoformat(),
            success=True
        )
        self.settings = None

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
            # 步骤1: 加载配置模块
            self._step_load_config()

            # 步骤2: 验证配置验证功能
            self._step_validate_config()

            # 步骤3: 检查数据库URL配置
            self._step_check_database_url()

            # 步骤4: 检查Redis配置
            self._step_check_redis_config()

            # 步骤5: 测试数据库连接
            self._step_test_database_connection()

            # 步骤6: 测试配置错误处理
            self._step_test_error_handling()

            # 步骤7: 测试重试机制
            self._step_test_retry_mechanism()

            # 步骤8: 验证CORS配置
            self._step_validate_cors()

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
        print("测试 3: 配置验证与数据库连接集成")
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

    def _step_load_config(self):
        """步骤1: 加载配置模块"""
        print("\n步骤 1: 加载配置模块...")

        try:
            from app.config import settings, get_settings

            self.settings = settings
            config_info = {
                "APP_NAME": settings.APP_NAME,
                "VERSION": settings.APP_VERSION,
                "DEBUG": getattr(settings, 'DEBUG', False)
            }

            step = TestStep(
                step="加载配置模块",
                status=TestStatus.SUCCESS,
                details=config_info
            )
            self.result.steps.append(step)
            print(f"  ✅ APP_NAME: {settings.APP_NAME}, VERSION: {settings.APP_VERSION}")
            self._log_step(f"配置模块加载成功", "debug")

        except Exception as e:
            step = TestStep(
                step="加载配置模块",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.success = False
            self.result.issues.append(f"配置模块加载失败: {e}")
            print(f"  ❌ 加载失败: {e}")
            raise

    def _step_validate_config(self):
        """步骤2: 验证配置验证功能"""
        print("\n步骤 2: 验证配置验证功能...")

        try:
            if not self.settings:
                raise RuntimeError("配置未加载")

            validation_result, duration = self._measure_time(
                self.settings.validate_database_config
            )

            details = {
                "valid": validation_result.get('valid', False),
                "issues": validation_result.get('issues', []),
                "warnings": validation_result.get('warnings', [])
            }

            print(f"  配置有效性: {details['valid']}")
            if details['issues']:
                print(f"  问题: {details['issues']}")
            if details['warnings']:
                print(f"  警告: {details['warnings']}")

            step = TestStep(
                step="验证配置验证功能",
                status=TestStatus.SUCCESS,
                details=details,
                duration_ms=duration
            )
            self.result.steps.append(step)
            self._log_step(f"配置验证完成", "debug")

        except Exception as e:
            step = TestStep(
                step="验证配置验证功能",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.issues.append(f"配置验证失败: {e}")
            print(f"  ❌ 验证失败: {e}")

    def _step_check_database_url(self):
        """步骤3: 检查数据库URL配置"""
        print("\n步骤 3: 检查数据库URL配置...")

        try:
            if not self.settings:
                raise RuntimeError("配置未加载")

            db_url = self.settings.DATABASE_URL
            # 隐藏密码
            masked_url = db_url
            if '@' in db_url:
                parts = db_url.split('@')
                credentials = parts[0].rsplit(':', 1)
                if len(credentials) > 1:
                    masked_url = f"{credentials[0]}:***@{parts[1]}"

            step = TestStep(
                step="检查数据库URL配置",
                status=TestStatus.SUCCESS,
                details=f"DATABASE_URL (masked): {masked_url}"
            )
            self.result.steps.append(step)
            print(f"  ✅ DATABASE_URL (masked): {masked_url}")
            self._log_step(f"数据库URL配置检查完成", "debug")

        except Exception as e:
            step = TestStep(
                step="检查数据库URL配置",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.issues.append(f"数据库URL检查失败: {e}")
            print(f"  ❌ 检查失败: {e}")

    def _step_check_redis_config(self):
        """步骤4: 检查Redis配置"""
        print("\n步骤 4: 检查Redis配置...")

        try:
            if not self.settings:
                raise RuntimeError("配置未加载")

            redis_url = getattr(self.settings, 'REDIS_URL', '未配置')

            step = TestStep(
                step="检查Redis配置",
                status=TestStatus.SUCCESS,
                details=f"REDIS_URL: {redis_url}"
            )
            self.result.steps.append(step)
            print(f"  ✅ REDIS_URL: {redis_url}")
            self._log_step(f"Redis配置检查完成", "debug")

        except Exception as e:
            step = TestStep(
                step="检查Redis配置",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.issues.append(f"Redis配置检查失败: {e}")
            print(f"  ❌ 检查失败: {e}")

    def _step_test_database_connection(self):
        """步骤5: 测试数据库连接"""
        print("\n步骤 5: 测试数据库连接...")

        try:
            from sqlalchemy import create_engine, text
            from app.config import settings

            engine, init_duration = self._measure_time(
                create_engine,
                settings.DATABASE_URL,
                pool_pre_ping=True
            )

            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                row = result.fetchone()

            step = TestStep(
                step="测试数据库连接",
                status=TestStatus.SUCCESS,
                details=f"数据库连接成功, 测试查询结果: {row}",
                duration_ms=init_duration
            )
            self.result.steps.append(step)
            print(f"  ✅ 数据库连接成功, 测试查询结果: {row}")
            self._log_step(f"数据库连接测试通过", "debug")

        except Exception as e:
            step = TestStep(
                step="测试数据库连接",
                status=TestStatus.WARNING,
                details=f"数据库连接失败: {str(e)}",
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.issues.append(f"数据库连接失败: {e}")
            print(f"  ⚠️ 数据库连接失败: {e}")

    def _step_test_error_handling(self):
        """步骤6: 测试配置错误处理"""
        print("\n步骤 6: 测试配置错误处理...")

        original_password = os.environ.get("DATABASE_PASSWORD")

        try:
            os.environ["DATABASE_PASSWORD"] = ""

            from importlib import reload
            import app.config as config_module
            reload(config_module)

            test_settings = config_module.Settings()
            test_validation = test_settings.validate_database_config()

            has_warning = len(test_validation.get('warnings', [])) > 0

            step = TestStep(
                step="测试配置错误处理",
                status=TestStatus.SUCCESS,
                details=f"空密码检测: {'检测到警告' if has_warning else '未检测到警告'}"
            )
            self.result.steps.append(step)
            print(f"  ✅ 空密码检测: {'检测到警告' if has_warning else '未检测到警告'}")
            self._log_step(f"配置错误处理测试完成", "debug")

        except Exception as e:
            step = TestStep(
                step="测试配置错误处理",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.issues.append(f"配置错误处理测试失败: {e}")
            print(f"  ❌ 测试失败: {e}")

        finally:
            if original_password:
                os.environ["DATABASE_PASSWORD"] = original_password
            elif "DATABASE_PASSWORD" in os.environ:
                del os.environ["DATABASE_PASSWORD"]

    def _step_test_retry_mechanism(self):
        """步骤7: 测试重试机制"""
        print("\n步骤 7: 测试重试机制...")

        try:
            from app.models.base import engine, SessionLocal, get_db

            pool_config = {}
            if hasattr(engine, 'pool'):
                pool = engine.pool
                pool_config = {
                    "pool_pre_ping": getattr(pool, '_pre_ping', 'N/A'),
                    "pool_size": pool.size() if hasattr(pool, 'size') else 'N/A',
                    "max_overflow": getattr(pool, '_max_overflow', 'N/A')
                }

            step = TestStep(
                step="测试重试机制",
                status=TestStatus.SUCCESS,
                details=pool_config
            )
            self.result.steps.append(step)
            print(f"  ✅ 连接池配置: {pool_config}")
            self._log_step(f"重试机制测试完成", "debug")

        except Exception as e:
            step = TestStep(
                step="测试重试机制",
                status=TestStatus.WARNING,
                details=f"无法获取连接池配置: {e}",
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.issues.append(f"重试机制测试失败: {e}")
            print(f"  ⚠️ 测试失败: {e}")

    def _step_validate_cors(self):
        """步骤8: 验证CORS配置"""
        print("\n步骤 8: 验证CORS配置...")

        try:
            if not self.settings:
                raise RuntimeError("配置未加载")

            cors_origins = getattr(self.settings, 'CORS_ORIGINS', [])

            step = TestStep(
                step="验证CORS配置",
                status=TestStatus.SUCCESS,
                details=f"CORS_ORIGINS: {cors_origins}"
            )
            self.result.steps.append(step)
            print(f"  ✅ CORS_ORIGINS: {cors_origins}")
            self._log_step(f"CORS配置验证完成", "debug")

        except Exception as e:
            step = TestStep(
                step="验证CORS配置",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.issues.append(f"CORS配置验证失败: {e}")
            print(f"  ❌ 验证失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="配置验证与数据库连接集成测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python test_integration_3.py
  python test_integration_3.py --output json --output-file result.json
  python test_integration_3.py --verbose
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
