from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import time


class PlatformType(Enum):
    POWERSHELL_7 = "powershell-7+"
    BASH = "bash-5.0"
    UNKNOWN = "unknown"


@dataclass
class ExecutionResult:
    success: bool
    return_code: int
    stdout: str
    stderr: str
    duration_ms: float
    platform: PlatformType

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "return_code": self.return_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "platform": self.platform.value,
        }


@dataclass
class EnvironmentInfo:
    platform_type: PlatformType
    os_name: str
    os_version: str
    python_version: str
    terminal_type: str
    encoding: str
    home_dir: Path
    working_dir: Path

    def to_dict(self) -> dict:
        return {
            "platform_type": self.platform_type.value,
            "os_name": self.os_name,
            "os_version": self.os_version,
            "python_version": self.python_version,
            "terminal_type": self.terminal_type,
            "encoding": self.encoding,
            "home_dir": str(self.home_dir),
            "working_dir": str(self.working_dir),
        }


class PlatformAdapter(ABC):
    """抽象平台适配器基类"""

    @abstractmethod
    def get_platform_type(self) -> PlatformType:
        """返回当前平台类型"""

    @abstractmethod
    def execute_script(self, script_path: Path, args: dict | None = None) -> ExecutionResult:
        """执行Python脚本"""

    @abstractmethod
    def run_command(self, cmd: str, timeout: int = 300, work_dir: Path | None = None) -> ExecutionResult:
        """执行shell命令"""

    @abstractmethod
    def manage_modules(self, action: str, module_name: str) -> bool:
        """管理包/模块（install/update/uninstall）"""

    @abstractmethod
    def get_environment_info(self) -> EnvironmentInfo:
        """获取环境信息"""

    @abstractmethod
    def validate_environment(self) -> tuple[bool, list[str]]:
        """验证环境是否满足要求，返回(是否通过, 问题列表)"""
