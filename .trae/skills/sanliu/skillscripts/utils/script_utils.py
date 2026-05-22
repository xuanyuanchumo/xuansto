#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三省六部协同开发系统 - 脚本通用工具模块

提供统一的脚本接口规范：
- 统一参数解析
- 统一输出格式（JSON/Markdown/Console）
- 统一退出码规范
- 统一帮助信息格式

使用示例:
    from script_utils import ScriptBase, OutputFormat, ExitCode
    
    class MyScript(ScriptBase):
        def run(self) -> int:
            self.logger.info("开始执行...")
            result = self.do_work()
            
            if self.args.json:
                self.output_json(result)
            elif self.args.markdown:
                self.output_markdown(result)
            else:
                self.output_console(result)
            
            return ExitCode.SUCCESS
"""

import argparse
import json
import sys
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Generic

T = TypeVar('T')


class ExitCode(Enum):
    EXIT_CODE_SUCCESS = 0
    EXIT_CODE_ERROR = 1
    EXIT_CODE_WARNING = 2


class OutputFormat(Enum):
    CONSOLE = "console"
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass
class ScriptResult(Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "success": self.success,
            "message": self.message,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms
        }
        if self.data is not None:
            if hasattr(self.data, 'to_dict'):
                result["data"] = self.data.to_dict()
            elif isinstance(self.data, (list, dict, str, int, float, bool)):
                result["data"] = self.data
            else:
                result["data"] = str(self.data)
        return result


class ScriptLogger:
    LEVEL_ICONS = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "💥",
        25: "✅",
    }
    
    SUCCESS = 25
    
    def __init__(self, name: str, verbose: bool = False, quiet: bool = False):
        self.verbose = verbose
        self.quiet = quiet
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG if verbose else logging.INFO)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _log(self, level: int, message: str):
        if self.quiet and level < logging.WARNING:
            return
        icon = self.LEVEL_ICONS.get(level, "")
        if icon:
            self.logger.log(level, f"{icon} {message}")
        else:
            self.logger.log(level, message)
    
    def debug(self, message: str):
        self._log(logging.DEBUG, message)
    
    def info(self, message: str):
        self._log(logging.INFO, message)
    
    def success(self, message: str):
        self._log(self.SUCCESS, message)
    
    def warning(self, message: str):
        self._log(logging.WARNING, message)
    
    def error(self, message: str):
        self._log(logging.ERROR, message)
    
    def critical(self, message: str):
        self._log(logging.CRITICAL, message)


class ScriptBase(ABC):
    DEFAULT_DESCRIPTION = "三省六部协同开发系统脚本"
    DEFAULT_EPILOG = """
示例:
  python %(prog)s                    # 默认执行
  python %(prog)s --json             # JSON格式输出
  python %(prog)s --markdown         # Markdown格式输出
  python %(prog)s -v                 # 详细输出
  python %(prog)s -q                 # 静默模式
"""
    
    def __init__(
        self,
        description: str = None,
        epilog: str = None,
        add_common_args: bool = True
    ):
        self.description = description or self.DEFAULT_DESCRIPTION
        self.epilog = epilog or self.DEFAULT_EPILOG
        self.parser = argparse.ArgumentParser(
            description=self.description,
            epilog=self.epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        if add_common_args:
            self._add_common_arguments()
        
        self._add_arguments()
        self.args = self.parser.parse_args()
        
        self.logger = ScriptLogger(
            name=self.__class__.__name__,
            verbose=getattr(self.args, 'verbose', False),
            quiet=getattr(self.args, 'quiet', False)
        )
        
        self._start_time = datetime.now()
    
    def _add_common_arguments(self):
        self.parser.add_argument(
            "--json",
            action="store_true",
            help="以JSON格式输出结果"
        )
        self.parser.add_argument(
            "--markdown",
            action="store_true",
            help="以Markdown格式输出结果"
        )
        self.parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="显示详细输出"
        )
        self.parser.add_argument(
            "-q", "--quiet",
            action="store_true",
            help="静默模式，仅输出错误"
        )
        self.parser.add_argument(
            "--output-file",
            type=str,
            help="输出文件路径"
        )
    
    def _add_arguments(self):
        pass
    
    @abstractmethod
    def run(self) -> int:
        pass
    
    def get_duration_ms(self) -> float:
        return (datetime.now() - self._start_time).total_seconds() * 1000
    
    def output_json(self, result: ScriptResult) -> None:
        output = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        self._write_output(output)
    
    def output_markdown(self, result: ScriptResult) -> None:
        lines = [
            f"# {self.description}",
            "",
            f"**执行时间**: {result.timestamp}",
            f"**执行状态**: {'✅ 成功' if result.success else '❌ 失败'}",
            f"**耗时**: {result.duration_ms:.2f}ms" if result.duration_ms else "",
            "",
            "## 执行结果",
            "",
            result.message,
        ]
        
        if result.errors:
            lines.extend([
                "",
                "## 错误信息",
                ""
            ])
            for error in result.errors:
                lines.append(f"- ❌ {error}")
        
        if result.warnings:
            lines.extend([
                "",
                "## 警告信息",
                ""
            ])
            for warning in result.warnings:
                lines.append(f"- ⚠️ {warning}")
        
        self._write_output("\n".join(lines))
    
    def output_console(self, result: ScriptResult) -> None:
        print("\n" + "=" * 60)
        print(f"📋 {self.description}")
        print("=" * 60)
        print(f"⏰ 执行时间: {result.timestamp}")
        if result.duration_ms:
            print(f"⏱️ 耗时: {result.duration_ms:.2f}ms")
        
        status_icon = "✅" if result.success else "❌"
        print(f"📊 状态: {status_icon} {'成功' if result.success else '失败'}")
        print("-" * 60)
        print(result.message)
        
        if result.errors:
            print("\n❌ 错误:")
            for error in result.errors:
                print(f"   - {error}")
        
        if result.warnings:
            print("\n⚠️ 警告:")
            for warning in result.warnings:
                print(f"   - {warning}")
        
        print("=" * 60)
    
    def _write_output(self, content: str) -> None:
        if hasattr(self.args, 'output_file') and self.args.output_file:
            output_path = Path(self.args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.info(f"输出已保存到: {output_path}")
        else:
            print(content)
    
    def execute(self) -> int:
        try:
            exit_code = self.run()
            return exit_code
        except KeyboardInterrupt:
            self.logger.warning("用户中断执行")
            return ExitCode.EXIT_CODE_WARNING.value
        except Exception as e:
            self.logger.critical(f"执行失败: {e}")
            if self.args.verbose:
                import traceback
                traceback.print_exc()
            return ExitCode.EXIT_CODE_ERROR.value


def create_result(
    success: bool,
    message: str,
    data: Any = None,
    errors: List[str] = None,
    warnings: List[str] = None,
    duration_ms: float = None
) -> ScriptResult:
    return ScriptResult(
        success=success,
        message=message,
        data=data,
        errors=errors or [],
        warnings=warnings or [],
        duration_ms=duration_ms
    )


def run_script(script_class: type) -> int:
    script = script_class()
    return script.execute()


if __name__ == "__main__":
    print(__doc__)
