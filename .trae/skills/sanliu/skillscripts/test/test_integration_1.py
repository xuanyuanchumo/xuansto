#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试：Agent选择器与调用历史集成

本脚本测试Agent选择器与调用历史系统的集成功能，包括：
- Agent选择器初始化与加载
- 调用历史系统初始化
- Agent选择与调用记录生成
- 调用记录存储与验证
- 调用统计功能

使用示例:
    python test_integration_1.py
    python test_integration_1.py --output json --output-file result.json
    python test_integration_1.py --verbose
"""

import sys
import io
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

from skillscripts.core.path_config_center import get_path_config

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加脚本目录到路径
sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from agent_selector import AgentSelector
from agent_call_history import AgentCallHistory, AgentCallRecord


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
            test_name="agent_selector_history_integration",
            timestamp=datetime.now().isoformat(),
            success=True
        )

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
            # 步骤1: 初始化Agent选择器
            self._step_init_agent_selector()

            # 步骤2: 初始化调用历史系统
            self._step_init_call_history()

            # 步骤3: 选择Agent
            agent_name = self._step_select_agent()

            # 步骤4: 生成调用记录
            call_record = self._step_generate_call_record(agent_name)

            # 步骤5: 记录到调用历史
            call_id = self._step_record_call(call_record)

            # 步骤6: 验证调用记录
            self._step_verify_call(call_id)

            # 步骤7: 获取调用统计
            self._step_get_statistics()

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
        print("测试 1: Agent选择器与调用历史集成")
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

    def _step_init_agent_selector(self):
        """步骤1: 初始化Agent选择器"""
        print("\n步骤 1: 初始化Agent选择器...")

        try:
            selector, duration = self._measure_time(AgentSelector)
            agent_count = len(selector.agent_registry)

            step = TestStep(
                step="初始化Agent选择器",
                status=TestStatus.SUCCESS,
                details=f"已加载 {agent_count} 个Agent",
                duration_ms=duration
            )
            self.result.steps.append(step)
            print(f"  ✅ 已加载 {agent_count} 个Agent")
            self._log_step(f"Agent选择器初始化完成，耗时 {duration:.2f}ms", "debug")

        except Exception as e:
            step = TestStep(
                step="初始化Agent选择器",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.success = False
            self.result.issues.append(f"Agent选择器初始化失败: {e}")
            print(f"  ❌ 初始化失败: {e}")
            raise

    def _step_init_call_history(self):
        """步骤2: 初始化调用历史系统"""
        print("\n步骤 2: 初始化调用历史系统...")

        try:
            history, duration = self._measure_time(AgentCallHistory)

            step = TestStep(
                step="初始化调用历史系统",
                status=TestStatus.SUCCESS,
                details=f"数据库路径: {history.db_path}",
                duration_ms=duration
            )
            self.result.steps.append(step)
            print(f"  ✅ 数据库路径: {history.db_path}")
            self._log_step(f"调用历史系统初始化完成，耗时 {duration:.2f}ms", "debug")

        except Exception as e:
            step = TestStep(
                step="初始化调用历史系统",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.success = False
            self.result.issues.append(f"调用历史系统初始化失败: {e}")
            print(f"  ❌ 初始化失败: {e}")
            raise

    def _step_select_agent(self) -> str:
        """步骤3: 选择Agent"""
        print("\n步骤 3: 选择Agent...")

        try:
            selector = AgentSelector()
            task_description = "实现用户登录界面的前端开发"
            context = {"tech_stack": "React TypeScript"}

            selection, duration = self._measure_time(
                selector.select_best_agent,
                task_description,
                context
            )

            if selection.get("best_match"):
                agent_name = selection["best_match"]["name"]
                step = TestStep(
                    step="选择Agent",
                    status=TestStatus.SUCCESS,
                    details=f"选中Agent: {agent_name}",
                    duration_ms=duration
                )
                self.result.steps.append(step)
                print(f"  ✅ 选中Agent: {agent_name}")
                self._log_step(f"Agent选择完成，选中: {agent_name}", "debug")
                return agent_name
            else:
                step = TestStep(
                    step="选择Agent",
                    status=TestStatus.WARNING,
                    details="未找到匹配的Agent，使用默认Agent",
                    duration_ms=duration
                )
                self.result.steps.append(step)
                print("  ⚠️ 未找到匹配的Agent，使用默认Agent")
                return "Frontend Developer"

        except Exception as e:
            step = TestStep(
                step="选择Agent",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.success = False
            self.result.issues.append(f"Agent选择失败: {e}")
            print(f"  ❌ 选择失败: {e}")
            raise

    def _step_generate_call_record(self, agent_name: str) -> Dict:
        """步骤4: 生成调用记录"""
        print("\n步骤 4: 生成调用记录...")

        try:
            selector = AgentSelector()
            call_record, duration = self._measure_time(
                selector.generate_call_record,
                agent_name=agent_name,
                task="实现用户登录界面的前端开发",
                context={"tech_stack": "React TypeScript"},
                result={"status": "success", "deliverables": ["登录页面"]}
            )

            step = TestStep(
                step="生成调用记录",
                status=TestStatus.SUCCESS,
                details=f"调用ID: {call_record['call_id']}",
                duration_ms=duration
            )
            self.result.steps.append(step)
            print(f"  ✅ 调用ID: {call_record['call_id']}")
            self._log_step(f"调用记录生成完成", "debug")
            return call_record

        except Exception as e:
            step = TestStep(
                step="生成调用记录",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.success = False
            self.result.issues.append(f"调用记录生成失败: {e}")
            print(f"  ❌ 生成失败: {e}")
            raise

    def _step_record_call(self, call_record: Dict) -> str:
        """步骤5: 记录到调用历史"""
        print("\n步骤 5: 记录到调用历史...")

        try:
            history = AgentCallHistory()
            record = AgentCallRecord(
                call_id=call_record["call_id"],
                timestamp=call_record["timestamp"],
                caller=call_record["caller"],
                agent_name=call_record["agent"],
                task=call_record["task"],
                context=call_record["context"],
                status="success",
                result=call_record["result"],
                duration_ms=1500,
                quality_score=0.95
            )

            call_id, duration = self._measure_time(history.record_call, record)

            step = TestStep(
                step="记录到调用历史",
                status=TestStatus.SUCCESS,
                details=f"已记录调用: {call_id}",
                duration_ms=duration
            )
            self.result.steps.append(step)
            print(f"  ✅ 已记录调用: {call_id}")
            self._log_step(f"调用记录已保存", "debug")
            return call_id

        except Exception as e:
            step = TestStep(
                step="记录到调用历史",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.success = False
            self.result.issues.append(f"调用记录失败: {e}")
            print(f"  ❌ 记录失败: {e}")
            raise

    def _step_verify_call(self, call_id: str):
        """步骤6: 验证调用记录"""
        print("\n步骤 6: 验证调用记录...")

        try:
            history = AgentCallHistory()
            saved_record, duration = self._measure_time(history.get_call, call_id)

            if saved_record:
                step = TestStep(
                    step="验证调用记录",
                    status=TestStatus.SUCCESS,
                    details=f"记录验证成功: agent={saved_record['agent_name']}, status={saved_record['status']}",
                    duration_ms=duration
                )
                self.result.steps.append(step)
                print(f"  ✅ 记录验证成功: agent={saved_record['agent_name']}, status={saved_record['status']}")
                self._log_step(f"调用记录验证通过", "debug")
            else:
                step = TestStep(
                    step="验证调用记录",
                    status=TestStatus.FAILED,
                    details="未能找到记录"
                )
                self.result.steps.append(step)
                self.result.success = False
                self.result.issues.append("调用记录未找到")
                print("  ❌ 未能找到记录")

        except Exception as e:
            step = TestStep(
                step="验证调用记录",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.success = False
            self.result.issues.append(f"记录验证失败: {e}")
            print(f"  ❌ 验证失败: {e}")

    def _step_get_statistics(self):
        """步骤7: 获取调用统计"""
        print("\n步骤 7: 获取调用统计...")

        try:
            history = AgentCallHistory()
            stats, duration = self._measure_time(history.get_statistics)

            step = TestStep(
                step="获取调用统计",
                status=TestStatus.SUCCESS,
                details=f"总调用数: {stats.get('total_calls', 0)}",
                duration_ms=duration
            )
            self.result.steps.append(step)
            print(f"  ✅ 总调用数: {stats.get('total_calls', 0)}")
            self._log_step(f"调用统计获取完成", "debug")

        except Exception as e:
            step = TestStep(
                step="获取调用统计",
                status=TestStatus.FAILED,
                error=str(e)
            )
            self.result.steps.append(step)
            self.result.issues.append(f"统计获取失败: {e}")
            print(f"  ❌ 获取失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Agent选择器与调用历史集成测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python test_integration_1.py
  python test_integration_1.py --output json --output-file result.json
  python test_integration_1.py --verbose
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
