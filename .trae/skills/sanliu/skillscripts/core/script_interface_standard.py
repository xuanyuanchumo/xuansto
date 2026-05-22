"""
脚本接口规范模块
定义所有脚本必须遵循的基础接口和抽象类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json


class ScriptStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReportFormat(Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"


@dataclass
class ScriptMetadata:
    name: str
    version: str
    description: str
    author: str
    created_at: datetime
    updated_at: datetime
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "dependencies": self.dependencies
        }


@dataclass
class ScriptResult:
    status: ScriptStatus
    data: Any = None
    message: str = ""
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "data": self.data,
            "message": self.message,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "metrics": self.metrics
        }


class IConfiguration(ABC):
    @abstractmethod
    def load(self, config_path: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def save(self, config_path: str, config: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        pass


class IReport(ABC):
    @abstractmethod
    def generate(self, result: ScriptResult, format: ReportFormat = ReportFormat.JSON) -> str:
        pass
    
    @abstractmethod
    def save(self, output_path: str, content: str) -> bool:
        pass
    
    @abstractmethod
    def add_section(self, title: str, content: Any) -> None:
        pass
    
    @abstractmethod
    def get_template(self, format: ReportFormat) -> str:
        pass


class ILogger(ABC):
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def set_level(self, level: LogLevel) -> None:
        pass
    
    @abstractmethod
    def get_logs(self) -> List[Dict[str, Any]]:
        pass


class IScript(ABC):
    @property
    @abstractmethod
    def metadata(self) -> ScriptMetadata:
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> ScriptResult:
        pass
    
    @abstractmethod
    def validate_inputs(self, *args, **kwargs) -> bool:
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        pass
    
    @abstractmethod
    def get_status(self) -> ScriptStatus:
        pass


class ICommandParser(ABC):
    @abstractmethod
    def parse(self, args: List[str]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_help(self) -> str:
        pass
    
    @abstractmethod
    def add_argument(self, name: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def validate(self, parsed_args: Dict[str, Any]) -> bool:
        pass


class IErrorHandler(ABC):
    @abstractmethod
    def handle(self, error: Exception, context: Dict[str, Any]) -> ScriptResult:
        pass
    
    @abstractmethod
    def register_handler(self, error_type: type, handler: callable) -> None:
        pass
    
    @abstractmethod
    def get_error_report(self) -> Dict[str, Any]:
        pass


@dataclass
class ArgumentDefinition:
    name: str
    type: type
    required: bool = True
    default: Any = None
    description: str = ""
    choices: List[Any] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.__name__,
            "required": self.required,
            "default": self.default,
            "description": self.description,
            "choices": self.choices
        }


class ScriptInterface:
    VERSION = "1.0.0"
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "version": {"type": "string"},
            "settings": {"type": "object"},
            "environment": {"type": "string", "enum": ["development", "staging", "production"]}
        },
        "required": ["name", "version"]
    }
    
    REPORT_SCHEMA = {
        "type": "object",
        "properties": {
            "script_name": {"type": "string"},
            "execution_time": {"type": "string"},
            "status": {"type": "string"},
            "result": {"type": "object"},
            "errors": {"type": "array"},
            "warnings": {"type": "array"}
        },
        "required": ["script_name", "status"]
    }
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        required_fields = ["name", "version"]
        return all(field in config for field in required_fields)
    
    @staticmethod
    def create_error_result(error: Exception, message: str = "") -> ScriptResult:
        return ScriptResult(
            status=ScriptStatus.FAILED,
            error=str(error),
            message=message or f"脚本执行失败: {type(error).__name__}",
            end_time=datetime.now()
        )
    
    @staticmethod
    def create_success_result(data: Any = None, message: str = "执行成功") -> ScriptResult:
        return ScriptResult(
            status=ScriptStatus.SUCCESS,
            data=data,
            message=message,
            end_time=datetime.now()
        )
