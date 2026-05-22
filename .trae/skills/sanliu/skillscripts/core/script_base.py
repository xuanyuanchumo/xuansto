"""
脚本基类模块
提供所有脚本的通用实现和基础设施
"""

import argparse
import json
import logging
import os
import sys
import traceback
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from .script_interface_standard import (
    ArgumentDefinition,
    IConfiguration,
    ILogger,
    IReport,
    IScript,
    ICommandParser,
    IErrorHandler,
    LogLevel,
    ReportFormat,
    ScriptMetadata,
    ScriptResult,
    ScriptStatus,
    ScriptInterface
)


class Configuration(IConfiguration):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config: Dict[str, Any] = config or {}
        self._config_path: Optional[str] = None
    
    def load(self, config_path: str) -> Dict[str, Any]:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix == '.json':
                self._config = json.load(f)
            elif path.suffix in ['.yaml', '.yml']:
                try:
                    import yaml
                    self._config = yaml.safe_load(f)
                except ImportError:
                    raise ImportError("需要安装 PyYAML 来解析 YAML 文件")
            else:
                raise ValueError(f"不支持的配置文件格式: {path.suffix}")
        
        self._config_path = config_path
        return self._config
    
    def save(self, config_path: str, config: Dict[str, Any]) -> bool:
        try:
            path = Path(config_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                if path.suffix == '.json':
                    json.dump(config, f, indent=2, ensure_ascii=False)
                elif path.suffix in ['.yaml', '.yml']:
                    try:
                        import yaml
                        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
                    except ImportError:
                        raise ImportError("需要安装 PyYAML 来保存 YAML 文件")
                else:
                    raise ValueError(f"不支持的配置文件格式: {path.suffix}")
            
            return True
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def validate(self) -> bool:
        return ScriptInterface.validate_config(self._config)
    
    def to_dict(self) -> Dict[str, Any]:
        return self._config.copy()


class Logger(ILogger):
    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        self._name = name
        self._level = level
        self._logs: List[Dict[str, Any]] = []
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.value.upper()))
        
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
    
    def _log(self, level: LogLevel, message: str, **kwargs) -> None:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "message": message,
            "extra": kwargs
        }
        self._logs.append(log_entry)
        
        log_method = getattr(self._logger, level.value)
        log_method(message, extra=kwargs if kwargs else None)
    
    def debug(self, message: str, **kwargs) -> None:
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def set_level(self, level: LogLevel) -> None:
        self._level = level
        self._logger.setLevel(getattr(logging, level.value.upper()))
    
    def get_logs(self) -> List[Dict[str, Any]]:
        return self._logs.copy()
    
    def save_logs(self, output_path: str) -> bool:
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._logs, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self._logger.error(f"保存日志失败: {e}")
            return False


class Report(IReport):
    def __init__(self, script_name: str):
        self._script_name = script_name
        self._sections: List[Dict[str, Any]] = []
        self._templates = {
            ReportFormat.JSON: self._json_template,
            ReportFormat.MARKDOWN: self._markdown_template,
            ReportFormat.HTML: self._html_template,
            ReportFormat.TEXT: self._text_template
        }
    
    def add_section(self, title: str, content: Any) -> None:
        self._sections.append({
            "title": title,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def generate(self, result: ScriptResult, format: ReportFormat = ReportFormat.JSON) -> str:
        template_func = self._templates.get(format, self._json_template)
        return template_func(result)
    
    def save(self, output_path: str, content: str) -> bool:
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logging.error(f"保存报告失败: {e}")
            return False
    
    def get_template(self, format: ReportFormat) -> str:
        return self._templates.get(format, self._json_template).__doc__ or ""
    
    def _json_template(self, result: ScriptResult) -> str:
        report = {
            "script_name": self._script_name,
            "generated_at": datetime.now().isoformat(),
            "status": result.status.value,
            "message": result.message,
            "data": result.data,
            "error": result.error,
            "duration": result.duration,
            "metrics": result.metrics,
            "sections": self._sections
        }
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def _markdown_template(self, result: ScriptResult) -> str:
        lines = [
            f"# {self._script_name} 执行报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**状态**: {result.status.value}",
            f"**消息**: {result.message}",
            ""
        ]
        
        if result.duration:
            lines.append(f"**执行时长**: {result.duration:.2f}秒")
        
        if result.error:
            lines.extend([
                "",
                "## 错误信息",
                "",
                f"```\n{result.error}\n```"
            ])
        
        if result.data:
            lines.extend([
                "",
                "## 执行结果",
                "",
                f"```\n{json.dumps(result.data, indent=2, ensure_ascii=False)}\n```"
            ])
        
        if result.metrics:
            lines.extend([
                "",
                "## 性能指标",
                ""
            ])
            for key, value in result.metrics.items():
                lines.append(f"- **{key}**: {value}")
        
        for section in self._sections:
            lines.extend([
                "",
                f"## {section['title']}",
                "",
                str(section['content'])
            ])
        
        return "\n".join(lines)
    
    def _html_template(self, result: ScriptResult) -> str:
        status_color = {
            ScriptStatus.SUCCESS: "#28a745",
            ScriptStatus.FAILED: "#dc3545",
            ScriptStatus.RUNNING: "#007bff",
            ScriptStatus.PENDING: "#6c757d",
            ScriptStatus.CANCELLED: "#ffc107",
            ScriptStatus.TIMEOUT: "#fd7e14"
        }.get(result.status, "#6c757d")
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._script_name} 执行报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .status {{ color: {status_color}; font-weight: bold; }}
        .section {{ margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{self._script_name} 执行报告</h1>
        <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>状态:</strong> <span class="status">{result.status.value}</span></p>
        <p><strong>消息:</strong> {result.message}</p>
        {f'<p><strong>执行时长:</strong> {result.duration:.2f}秒</p>' if result.duration else ''}
    </div>
"""
        
        if result.error:
            html += f"""
    <div class="section">
        <h2>错误信息</h2>
        <pre>{result.error}</pre>
    </div>
"""
        
        if result.data:
            html += f"""
    <div class="section">
        <h2>执行结果</h2>
        <pre>{json.dumps(result.data, indent=2, ensure_ascii=False)}</pre>
    </div>
"""
        
        for section in self._sections:
            html += f"""
    <div class="section">
        <h2>{section['title']}</h2>
        <p>{section['content']}</p>
    </div>
"""
        
        html += """
</body>
</html>"""
        return html
    
    def _text_template(self, result: ScriptResult) -> str:
        lines = [
            f"{'='*60}",
            f"{self._script_name} 执行报告",
            f"{'='*60}",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"状态: {result.status.value}",
            f"消息: {result.message}",
        ]
        
        if result.duration:
            lines.append(f"执行时长: {result.duration:.2f}秒")
        
        if result.error:
            lines.extend([
                "",
                "-" * 40,
                "错误信息:",
                "-" * 40,
                result.error
            ])
        
        if result.data:
            lines.extend([
                "",
                "-" * 40,
                "执行结果:",
                "-" * 40,
                json.dumps(result.data, indent=2, ensure_ascii=False)
            ])
        
        lines.append(f"\n{'='*60}")
        return "\n".join(lines)


class CommandParser(ICommandParser):
    def __init__(self, description: str = ""):
        self._parser = argparse.ArgumentParser(description=description)
        self._arguments: Dict[str, ArgumentDefinition] = {}
        self._subparsers = None
    
    def add_argument(self, name: str, **kwargs) -> None:
        arg_name = name if name.startswith('-') else f'--{name}'
        self._parser.add_argument(arg_name, **kwargs)
        
        self._arguments[name.lstrip('-')] = ArgumentDefinition(
            name=name.lstrip('-'),
            type=kwargs.get('type', str),
            required=kwargs.get('required', False),
            default=kwargs.get('default'),
            description=kwargs.get('help', ''),
            choices=kwargs.get('choices', [])
        )
    
    def add_subparser(self, name: str, help_text: str = "") -> 'CommandParser':
        if self._subparsers is None:
            self._subparsers = self._parser.add_subparsers(dest='command')
        
        subparser = self._subparsers.add_parser(name, help=help_text)
        new_parser = CommandParser(name)
        new_parser._parser = subparser
        return new_parser
    
    def parse(self, args: List[str] = None) -> Dict[str, Any]:
        if args is None:
            args = sys.argv[1:]
        
        parsed = self._parser.parse_args(args)
        return vars(parsed)
    
    def get_help(self) -> str:
        return self._parser.format_help()
    
    def validate(self, parsed_args: Dict[str, Any]) -> bool:
        for name, arg_def in self._arguments.items():
            if arg_def.required and parsed_args.get(name) is None:
                return False
            if arg_def.choices and parsed_args.get(name) not in arg_def.choices:
                return False
        return True


class ErrorHandler(IErrorHandler):
    def __init__(self):
        self._handlers: Dict[Type[Exception], Callable] = {}
        self._errors: List[Dict[str, Any]] = []
    
    def register_handler(self, error_type: Type[Exception], handler: Callable) -> None:
        self._handlers[error_type] = handler
    
    def handle(self, error: Exception, context: Dict[str, Any]) -> ScriptResult:
        error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        self._errors.append(error_info)
        
        for error_type, handler in self._handlers.items():
            if isinstance(error, error_type):
                try:
                    return handler(error, context)
                except Exception as handler_error:
                    return ScriptInterface.create_error_result(
                        handler_error,
                        f"错误处理器执行失败: {type(handler_error).__name__}"
                    )
        
        return ScriptInterface.create_error_result(error)
    
    def get_error_report(self) -> Dict[str, Any]:
        return {
            "total_errors": len(self._errors),
            "errors": self._errors,
            "error_types": list(set(e["type"] for e in self._errors))
        }


class ScriptBase(IScript):
    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        author: str = ""
    ):
        self._name = name
        self._version = version
        self._description = description
        self._author = author
        
        self._status = ScriptStatus.PENDING
        self._config = Configuration()
        self._logger = Logger(name)
        self._report = Report(name)
        self._error_handler = ErrorHandler()
        self._command_parser = CommandParser(description)
        
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
        
        self._setup_default_arguments()
        self._setup_default_error_handlers()
    
    @property
    def metadata(self) -> ScriptMetadata:
        return ScriptMetadata(
            name=self._name,
            version=self._version,
            description=self._description,
            author=self._author,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @property
    def config(self) -> Configuration:
        return self._config
    
    @property
    def logger(self) -> Logger:
        return self._logger
    
    @property
    def report(self) -> Report:
        return self._report
    
    def _setup_default_arguments(self) -> None:
        self._command_parser.add_argument(
            'config',
            type=str,
            required=False,
            help='配置文件路径'
        )
        self._command_parser.add_argument(
            '--output',
            '-o',
            type=str,
            default='./output',
            help='输出目录'
        )
        self._command_parser.add_argument(
            '--log-level',
            type=str,
            choices=['debug', 'info', 'warning', 'error'],
            default='info',
            help='日志级别'
        )
        self._command_parser.add_argument(
            '--report-format',
            type=str,
            choices=['json', 'markdown', 'html', 'text'],
            default='json',
            help='报告格式'
        )
    
    def _setup_default_error_handlers(self) -> None:
        self._error_handler.register_handler(
            FileNotFoundError,
            lambda e, ctx: ScriptInterface.create_error_result(e, "文件未找到")
        )
        self._error_handler.register_handler(
            ValueError,
            lambda e, ctx: ScriptInterface.create_error_result(e, "参数值错误")
        )
        self._error_handler.register_handler(
            PermissionError,
            lambda e, ctx: ScriptInterface.create_error_result(e, "权限不足")
        )
    
    def initialize(self, config: Dict[str, Any]) -> None:
        self._config = Configuration(config)
        self._status = ScriptStatus.PENDING
        self._logger.info(f"脚本 {self._name} 初始化完成")
    
    def validate_inputs(self, *args, **kwargs) -> bool:
        return True
    
    def cleanup(self) -> None:
        self._logger.info(f"脚本 {self._name} 清理完成")
    
    def get_status(self) -> ScriptStatus:
        return self._status
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        pass
    
    def execute(self, *args, **kwargs) -> ScriptResult:
        self._start_time = datetime.now()
        self._status = ScriptStatus.RUNNING
        
        try:
            self._logger.info(f"开始执行脚本: {self._name}")
            
            if not self.validate_inputs(*args, **kwargs):
                return ScriptInterface.create_error_result(
                    ValueError("输入验证失败"),
                    "输入参数验证失败"
                )
            
            result_data = self.run(*args, **kwargs)
            
            self._end_time = datetime.now()
            self._status = ScriptStatus.SUCCESS
            
            result = ScriptResult(
                status=ScriptStatus.SUCCESS,
                data=result_data,
                message="执行成功",
                start_time=self._start_time,
                end_time=self._end_time,
                metrics=self._collect_metrics()
            )
            
            self._logger.info(f"脚本 {self._name} 执行成功")
            return result
            
        except Exception as e:
            self._end_time = datetime.now()
            self._status = ScriptStatus.FAILED
            
            result = self._error_handler.handle(e, {
                "args": args,
                "kwargs": kwargs,
                "start_time": self._start_time,
                "end_time": self._end_time
            })
            
            result.start_time = self._start_time
            result.end_time = self._end_time
            result.metrics = self._collect_metrics()
            
            self._logger.error(f"脚本 {self._name} 执行失败: {e}")
            return result
            
        finally:
            self.cleanup()
    
    def _collect_metrics(self) -> Dict[str, Any]:
        metrics = {
            "memory_usage": self._get_memory_usage(),
            "cpu_time": self._get_cpu_time()
        }
        if self._start_time and self._end_time:
            metrics["duration_seconds"] = (self._end_time - self._start_time).total_seconds()
        return metrics
    
    def _get_memory_usage(self) -> Optional[float]:
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return None
    
    def _get_cpu_time(self) -> Optional[float]:
        try:
            import os
            return os.times().user + os.times().system
        except Exception:
            return None
    
    def generate_report(
        self,
        result: ScriptResult,
        output_path: str,
        format: ReportFormat = ReportFormat.JSON
    ) -> bool:
        content = self._report.generate(result, format)
        return self._report.save(output_path, content)
    
    def run_from_command_line(self) -> ScriptResult:
        args = self._command_parser.parse()
        
        log_level = LogLevel(args.get('log_level', 'info'))
        self._logger.set_level(log_level)
        
        config_path = args.get('config')
        if config_path:
            self._config.load(config_path)
        
        report_format = ReportFormat(args.get('report_format', 'json'))
        
        result = self.execute(**args)
        
        output_dir = Path(args.get('output', './output'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = output_dir / f"{self._name}_report.{report_format.value}"
        self.generate_report(result, str(report_path), report_format)
        
        log_path = output_dir / f"{self._name}.log"
        self._logger.save_logs(str(log_path))
        
        return result
