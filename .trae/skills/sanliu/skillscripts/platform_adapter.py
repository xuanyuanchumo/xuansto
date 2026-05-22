"""
PowerShell 7 原生适配层和编码格式统一工具

提供跨平台环境检测、Bash/PowerShell 命令转换、文件操作封装和编码格式验证功能。
支持 PowerShell 7 / Bash / WSL / CMD 多环境适配。
"""

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class ShellType(Enum):
    """支持的Shell类型枚举"""

    POWERSHELL_7 = "powershell_7"
    BASH = "bash"
    WSL = "wsl"
    CMD = "cmd"
    UNKNOWN = "unknown"


class EncodingType(Enum):
    """编码类型枚举"""

    UTF8_BOM = "utf-8-bom"
    UTF8_NOBOM = "utf-8"
    UTF16_LE = "utf-16-le"
    UTF16_BE = "utf-16-be"
    ASCII = "ascii"
    GBK = "gbk"
    GB2312 = "gb2312"
    LATIN1 = "latin1"
    UNKNOWN = "unknown"


@dataclass
class EnvironmentInfo:
    """环境信息数据类"""

    shell_type: ShellType
    platform_system: str
    platform_release: str
    platform_version: str
    machine: str
    processor: str
    python_version: str
    ps_version: Optional[str] = None
    is_wsl: bool = False
    home_dir: str = ""
    path_separator: str = ""
    env_vars: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "shell_type": self.shell_type.value,
            "platform_system": self.platform_system,
            "platform_release": self.platform_release,
            "platform_version": self.platform_version,
            "machine": self.machine,
            "processor": self.processor,
            "python_version": self.python_version,
            "ps_version": self.ps_version,
            "is_wsl": self.is_wsl,
            "home_dir": self.home_dir,
            "path_separator": self.path_separator,
            "env_vars_count": len(self.env_vars),
        }


@dataclass
class EncodingInfo:
    """编码信息数据类"""

    file_path: str
    encoding_type: EncodingType
    has_bom: bool
    bom_bytes: bytes
    file_size: int
    detected_at: datetime = field(default_factory=datetime.now)
    confidence: float = 0.0
    raw_header: bytes = b""

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "file_path": self.file_path,
            "encoding_type": self.encoding_type.value,
            "has_bom": self.has_bom,
            "bom_size": len(self.bom_bytes),
            "file_size": self.file_size,
            "detected_at": self.detected_at.isoformat(),
            "confidence": round(self.confidence, 3),
        }


@dataclass
class EncodingReport:
    """编码报告数据类"""

    root_path: str
    total_files: int = 0
    valid_files: int = 0
    invalid_files: int = 0
    fixed_files: int = 0
    failed_files: list = field(default_factory=list)
    file_reports: list = field(default_factory=list)
    scan_time: datetime = field(default_factory=datetime.now)
    target_encoding: str = "utf-8"

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "root_path": self.root_path,
            "total_files": self.total_files,
            "valid_files": self.valid_files,
            "invalid_files": self.invalid_files,
            "fixed_files": self.fixed_files,
            "failed_files_count": len(self.failed_files),
            "scan_time": self.scan_time.isoformat(),
            "target_encoding": self.target_encoding,
            "compliance_rate": (
                f"{(self.valid_files / self.total_files * 100):.1f}%"
                if self.total_files > 0
                else "N/A"
            ),
        }

    def summary(self) -> str:
        """生成摘要文本"""
        lines = [
            "=" * 60,
            "编码格式验证报告",
            "=" * 60,
            f"扫描路径: {self.root_path}",
            f"扫描时间: {self.scan_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"目标编码: {self.target_encoding}",
            "-" * 60,
            f"总文件数: {self.total_files}",
            f"符合规范: {self.valid_files}",
            f"不符合规范: {self.invalid_files}",
            f"已修复: {self.fixed_files}",
            f"修复失败: {len(self.failed_files)}",
            "-" * 60,
        ]
        if self.total_files > 0:
            rate = (self.valid_files / self.total_files) * 100
            lines.append(f"合规率: {rate:.1f}%")
        if self.failed_files:
            lines.append("\n失败文件列表:")
            for f in self.failed_files[:10]:
                lines.append(f"  - {f}")
            if len(self.failed_files) > 10:
                lines.append(f"  ... 还有 {len(self.failed_files) - 10} 个文件")
        lines.append("=" * 60)
        return "\n".join(lines)


@dataclass
class CompatibilityItem:
    """兼容性检查项"""

    name: str
    status: bool
    message: str
    severity: str = "info"


@dataclass
class CompatibilityReport:
    """PowerShell 7 兼容性报告"""

    is_compatible: bool = False
    ps_version: Optional[str] = None
    check_time: datetime = field(default_factory=datetime.now)
    items: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def add_item(self, item: CompatibilityItem):
        """添加检查项"""
        self.items.append(item)
        if not item.status and item.severity in ("error", "critical"):
            self.is_compatible = False

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "is_compatible": self.is_compatible,
            "ps_version": self.ps_version,
            "check_time": self.check_time.isoformat(),
            "total_checks": len(self.items),
            "passed_checks": sum(1 for i in self.items if i.status),
            "failed_checks": sum(1 for i in self.items if not i.status),
            "warnings_count": len(self.warnings),
        }

    def summary(self) -> str:
        """生成摘要文本"""
        lines = [
            "=" * 60,
            "PowerShell 7 兼容性验证报告",
            "=" * 60,
            f"检测时间: {self.check_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"PS版本: {self.ps_version or '未检测到'}",
            f"兼容状态: {'✓ 通过' if self.is_compatible else '✗ 不通过'}",
            "-" * 60,
            f"检查项总数: {len(self.items)}",
            f"通过项: {sum(1 for i in self.items if i.status)}",
            f"失败项: {sum(1 for i in self.items if not i.status)}",
        ]
        if self.warnings:
            lines.append(f"\n警告 ({len(self.warnings)} 条):")
            for w in self.warnings[:5]:
                lines.append(f"  ⚠ {w}")
        lines.append("-" * 60)
        for item in self.items:
            icon = "✓" if item.status else "✗"
            lines.append(f"  [{icon}] {item.name}: {item.message}")
        lines.append("=" * 60)
        return "\n".join(lines)


class PlatformAdapter:
    """
    平台适配器主类

    提供环境检测、命令转换、文件操作和编码验证功能。
    支持在 Python 环境中桥接 Bash 和 PowerShell 7 命令。
    """

    # BOM 标记定义
    BOM_MARKERS = {
        EncodingType.UTF8_BOM: b"\xef\xbb\xbf",
        EncodingType.UTF16_LE: b"\xff\xfe",
        EncodingType.UTF16_BE: b"\xfe\xff",
    }

    # Bash 到 PowerShell 7 的命令映射表（20个常用命令）
    COMMAND_MAPPINGS = {
        # 文件和目录操作
        "ls": "Get-ChildItem",
        "ls -la": "Get-ChildItem -Force",
        "cd": "Set-Location",
        "cp": "Copy-Item",
        "cp -r": "Copy-Item -Recurse",
        "rm": "Remove-Item",
        "rm -rf": "Remove-Item -Recurse -Force",
        "mkdir": "New-Item -ItemType Directory",
        "touch": "New-Item -ItemType File",
        "mv": "Move-Item",
        "cat": "Get-Content",
        # 搜索和过滤
        "grep": "Select-String",
        "find .": "Get-ChildItem -Recurse",
        "find": "Get-ChildItem -Recurse",
        "head": "Select-Object -First",
        "tail": "Select-Object -Last",
        "wc -l": "(Get-Content).Count",
        "which": "Get-Command",
        # 系统和环境
        "echo": "Write-Output",
        "pwd": "Get-Location",
        "export": "$env:",
        "chmod": "Set-Acl",
        "history": "Get-History",
        "man": "Get-Help",
        "ps": "Get-Process",
        "env": "Get-ChildItem Env:",
    }

    # 支持的文件扩展名模式（用于编码验证）
    TEXT_FILE_PATTERNS = [
        "*.py",
        "*.ps1",
        "*.json",
        "*.yaml",
        "*.yml",
        "*.md",
        "*.txt",
        "*.csv",
        "*.xml",
        "*.html",
        "*.css",
        "*.js",
        "*.ts",
        "*.vue",
        "*.sh",
        "*.bat",
        "*.cmd",
        "*.ini",
        "*.cfg",
        "*.toml",
        ".gitignore",
        ".env*",
        "Dockerfile*",
        "*.sql",
    ]

    def __init__(self):
        """初始化平台适配器"""
        self._env_info: Optional[EnvironmentInfo] = None
        self._command_cache: dict = {}

    def detect_environment(self) -> EnvironmentInfo:
        """
        自动检测当前运行环境

        检测方法：
        1. 检查 PSModulePath 环境变量判断 PowerShell 环境
        2. 检查 SHELL 环境变量判断 Bash/WSL
        3. 使用 platform 模块获取系统信息
        4. 尝试获取 PowerShell 版本信息

        Returns:
            EnvironmentInfo: 包含详细环境信息的对象
        """
        system = platform.system()
        release = platform.release()
        version = platform.version()
        machine = platform.machine()
        processor = platform.processor()
        python_version = platform.python_version()

        # 检测 Shell 类型
        shell_type = ShellType.UNKNOWN
        is_wsl = False
        ps_version = None

        # 方法1：检查 PSModulePath（PowerShell 特有）
        ps_module_path = os.environ.get("PSModulePath")
        if ps_module_path and "WindowsPowerShell" in ps_module_path or "PowerShell" in ps_module_path:
            shell_type = ShellType.POWERSHELL_7
            try:
                result = subprocess.run(
                    ["pwsh", "-Command", "$PSVersionTable.PSVersion.ToString()"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    ps_version = result.stdout.strip()
            except Exception:
                pass

        # 方法2：检查 SHELL 变量（Bash/WSL）
        shell_var = os.environ.get("SHELL", "")
        if "/bash" in shell_var or "/zsh" in shell_var:
            # 进一步判断是否为 WSL
            if "microsoft" in release.lower() or "wsl" in release.lower():
                shell_type = ShellType.WSL
                is_wsl = True
            elif system == "Linux":
                shell_type = ShellType.BASH

        # 方法3：根据操作系统回退
        if shell_type == ShellType.UNKNOWN:
            if system == "Windows":
                shell_type = ShellType.CMD
            elif system == "Linux":
                shell_type = ShellType.BASH
            elif system == "Darwin":
                shell_type = ShellType.BASH

        # 获取路径分隔符
        path_separator = ";" if system == "Windows" else ":"

        # 收集关键环境变量
        key_vars = ["PATH", "HOME", "USERPROFILE", "SHELL", "PSModulePath", "LANG", "LC_ALL"]
        env_vars = {}
        for var in key_vars:
            value = os.environ.get(var)
            if value:
                env_vars[var] = value[:100] + "..." if len(value) > 100 else value

        self._env_info = EnvironmentInfo(
            shell_type=shell_type,
            platform_system=system,
            platform_release=release,
            platform_version=version,
            machine=machine,
            processor=processor,
            python_version=python_version,
            ps_version=ps_version,
            is_wsl=is_wsl,
            home_dir=os.path.expanduser("~"),
            path_separator=path_separator,
            env_vars=env_vars,
        )

        return self._env_info

    def adapt_command(self, command: str, target_shell: str = "powershell_7") -> str:
        """
        将 Bash 命令转换为目标 Shell 命令

        支持20个常用 Bash → PowerShell 7 命令的自动转换。
        对于复杂命令，会尝试智能解析参数。

        Args:
            command: 原始 Bash 命令字符串
            target_shell: 目标 Shell 类型（默认 powershell_7）

        Returns:
            str: 转换后的命令字符串

        Examples:
            >>> adapter = PlatformAdapter()
            >>> adapter.adapt_command("ls -la")
            'Get-ChildItem -Force'
            >>> adapter.adapt_command("grep pattern file.txt")
            'Select-String -Pattern "pattern" -Path "file.txt"'
        """
        if target_shell != "powershell_7":
            return command

        # 检查缓存
        cache_key = f"{command}:{target_shell}"
        if cache_key in self._command_cache:
            return self._command_cache[cache_key]

        cmd_stripped = command.strip()

        # 直接匹配完整命令（包括常见参数组合）
        if cmd_stripped in self.COMMAND_MAPPINGS:
            result = self.COMMAND_MAPPINGS[cmd_stripped]
            self._command_cache[cache_key] = result
            return result

        # 尝试匹配基础命令
        parts = cmd_stripped.split()
        base_cmd = parts[0] if parts else ""

        if base_cmd in self.COMMAND_MAPPINGS:
            ps_cmd = self.COMMAND_MAPPINGS[base_cmd]
            args = parts[1:] if len(parts) > 1 else []

            # 根据不同命令类型处理参数
            result = self._convert_arguments(base_cmd, ps_cmd, args)
            self._command_cache[cache_key] = result
            return result

        # 无法识别的命令，原样返回并添加注释
        self._command_cache[cache_key] = command
        return command

    def _convert_arguments(self, bash_cmd: str, ps_cmd: str, args: list) -> str:
        """
        将 Bash 参数转换为 PowerShell 参数格式

        处理常见的参数模式：
        - 短选项 (-l, -a 等)
        - 长选项 (--recursive, --force 等)
        - 文件路径参数
        - 正则表达式参数

        Args:
            bash_cmd: 原始 Bash 命令
            ps_cmd: 对应的 PowerShell 命令
            args: 参数列表

        Returns:
            str: 完整的 PowerShell 命令
        """
        if not args:
            return ps_cmd

        converted_args = []
        i = 0

        while i < len(args):
            arg = args[i]

            # 处理 grep/Select-String 的特殊参数
            if bash_cmd == "grep":
                if i == 0 and not arg.startswith("-"):
                    # 第一个非选项参数通常是模式
                    converted_args.append(f'-Pattern "{arg}"')
                elif i == 1 and not arg.startswith("-"):
                    # 第二个参数通常是文件路径
                    converted_args.append(f'-Path "{arg}"')
                elif arg == "-i":
                    converted_args.append("-CaseSensitive:$false")
                elif arg == "-r":
                    converted_args.append("-Recurse")
                elif arg == "-v":
                    converted_args.append("-NotMatch")
                elif arg == "-n":
                    converted_args.append("-IncludeLineNumber")
                else:
                    converted_args.append(arg)

            # 处理 ls/Get-ChildItem 的参数
            elif bash_cmd == "ls":
                if arg == "-la" or arg == "-al":
                    converted_args.append("-Force")
                elif arg == "-l":
                    converted_args.append()
                elif arg == "-a":
                    converted_args.append("-Force")
                elif arg == "-R" or arg == "-r":
                    converted_args.append("-Recurse")
                elif arg == "-h":
                    converted_args.append("-HumanReadable")
                elif not arg.startswith("-"):
                    converted_args.append(f'-Path "{arg}"')
                else:
                    converted_args.append(arg)

            # 处理 cat/Get-Content 的参数
            elif bash_cmd == "cat":
                if arg == "-n":
                    converted_args.append("-IncludeLineNumber")
                elif not arg.startswith("-"):
                    converted_args.append(f'-Path "{arg}"')
                else:
                    converted_args.append(arg)

            # 处理 head/tail/Select-Object 的参数
            elif bash_cmd in ("head", "tail"):
                if arg.startswith("-") and arg[1:].isdigit():
                    num = arg[1:]
                    converted_args.append(f"-{num}")
                elif arg.isdigit():
                    converted_args.append(arg)
                elif not arg.startswith("-"):
                    converted_args.append(f'-InputObject (Get-Content "{arg}")')
                else:
                    converted_args.append(arg)

            # 处理 echo/Write-Output 的参数
            elif bash_cmd == "echo":
                if arg == "-n":
                    converted_args.append("-NoNewline")
                elif arg == "-e":
                    pass  # PS 中不需要转义解释
                else:
                    converted_args.append(f'"{arg}"')

            # 处理 cp/rm/mv 等通用文件操作命令
            elif bash_cmd in ("cp", "rm", "mv"):
                if arg == "-r" or arg == "-R":
                    converted_args.append("-Recurse")
                elif arg == "-f":
                    converted_args.append("-Force")
                elif arg == "-i":
                    converted_args.append("-Confirm")
                elif arg == "-v":
                    converted_args.append("-Verbose")
                elif not arg.startswith("-"):
                    converted_args.append(f'"{arg}"')
                else:
                    converted_args.append(arg)

            # 处理 chmod/Set-Acl 的参数
            elif bash_cmd == "chmod":
                if not arg.startswith("-"):
                    converted_args.append(arg)
                else:
                    converted_args.append(arg)

            # 处理 export/$env: 的参数
            elif bash_cmd == "export":
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    converted_args.append(f'{key}="{value}"')
                else:
                    converted_args.append(arg)

            # 默认处理
            else:
                if not arg.startswith("-"):
                    converted_args.append(f'"{arg}"')
                else:
                    converted_args.append(arg)

            i += 1

        # 组合最终命令
        if converted_args:
            return f"{ps_cmd} {' '.join(converted_args)}"
        return ps_cmd

    def list_files(self, path: str, pattern: str = "*") -> list[dict]:
        """
        列出指定目录下的文件

        跨平台的文件列表功能，返回结构化的文件信息。

        Args:
            path: 目录路径
            pattern: 文件匹配模式（glob 风格，如 *.py, *.txt）

        Returns:
            list[dict]: 文件信息列表，每个元素包含：
                - name: 文件名
                - path: 完整路径
                - size: 文件大小（字节）
                - is_dir: 是否为目录
                - modified_time: 修改时间
        """
        dir_path = Path(path)
        if not dir_path.exists():
            raise FileNotFoundError(f"目录不存在: {path}")

        if not dir_path.is_dir():
            raise NotADirectoryError(f"路径不是目录: {path}")

        files = []
        try:
            for item in dir_path.glob(pattern):
                try:
                    stat = item.stat()
                    files.append({
                        "name": item.name,
                        "path": str(item.absolute()),
                        "size": stat.st_size,
                        "is_dir": item.is_dir(),
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
                except (OSError, PermissionError) as e:
                    files.append({
                        "name": item.name,
                        "path": str(item.absolute()),
                        "size": -1,
                        "is_dir": item.is_dir(),
                        "modified_time": None,
                        "error": str(e),
                    })
        except Exception as e:
            raise RuntimeError(f"列出文件失败: {e}")

        # 按名称排序，目录在前
        files.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return files

    def copy_file(self, src: str, dst: str) -> bool:
        """
        复制文件或目录

        跨平台的文件复制功能，自动处理路径转换。

        Args:
            src: 源文件/目录路径
            dst: 目标文件/目录路径

        Returns:
            bool: 是否成功复制

        Raises:
            FileNotFoundError: 源文件不存在
            PermissionError: 权限不足
        """
        src_path = Path(src)
        dst_path = Path(dst)

        if not src_path.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")

        try:
            if src_path.is_dir():
                shutil.copytree(str(src_path), str(dst_path), dirs_exist_ok=True)
            else:
                # 如果目标是目录，则在该目录下创建同名文件
                if dst_path.is_dir():
                    dst_path = dst_path / src_path.name
                shutil.copy2(str(src_path), str(dst_path))
            return True
        except PermissionError as e:
            raise PermissionError(f"权限不足，无法复制到 {dst}: {e}")
        except Exception as e:
            raise RuntimeError(f"复制文件失败: {e}")

    def get_env_var(self, name: str) -> str:
        """
        获取环境变量值

        跨平台的环境变量访问，自动处理大小写差异。

        Args:
            name: 环境变量名称

        Returns:
            str: 环境变量值，不存在则返回空字符串
        """
        value = os.environ.get(name)
        if value is None:
            # Windows 环境下尝试不区分大小写查找
            if platform.system() == "Windows":
                for k, v in os.environ.items():
                    if k.lower() == name.lower():
                        return v
            return ""
        return value

    def ensure_encoding(self, file_path: str, encoding: str = "utf-8") -> bool:
        """
        确保文件使用指定编码格式

        检测并转换文件编码为目标格式。

        Args:
            file_path: 文件路径
            encoding: 目标编码（默认 utf-8）

        Returns:
            bool: 是否成功（True 表示已正确编码或成功转换）
        """
        path = Path(file_path)
        if not path.exists():
            return False

        try:
            enc_info = self.detect_file_encoding(file_path)

            # 检查是否已经是目标编码且无 BOM
            target_enc = encoding.lower().replace("-", "")
            current_enc = enc_info.encoding_type.value.replace("-", "")

            is_target_encoding = target_enc in current_enc or (
                target_enc == "utf8" and current_enc == "utf8nobom"
            )
            has_unwanted_bom = enc_info.has_bom and encoding.lower() == "utf-8"

            if is_target_encoding and not has_unwanted_bom:
                return True

            # 需要转换
            return self.fix_encoding(file_path, target_encoding=encoding, remove_bom=True)
        except Exception:
            return False

    def detect_file_encoding(self, file_path: str) -> EncodingInfo:
        """
        检测文件编码格式

        通过分析文件头部的 BOM 标记和字节内容来推断编码。
        支持检测 UTF-8 BOM、UTF-16 LE/BE、GBK、ASCII 等常见编码。

        Args:
            file_path: 要检测的文件路径

        Returns:
            EncodingInfo: 包含编码信息的详细对象

        Raises:
            FileNotFoundError: 文件不存在
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_size = path.stat().st_size

        # 读取文件头部（最多前8KB用于编码检测）
        sample_size = min(8192, file_size)
        with open(file_path, "rb") as f:
            raw_header = f.read(sample_size)

        has_bom = False
        bom_bytes = b""
        detected_encoding = EncodingType.UNKNOWN
        confidence = 0.0

        # 检查 BOM 标记
        for enc_type, bom_marker in self.BOM_MARKERS.items():
            if raw_header[: len(bom_marker)] == bom_marker:
                has_bom = True
                bom_bytes = bom_marker
                detected_encoding = enc_type
                confidence = 0.99
                break

        # 如果没有 BOM，尝试通过内容推断编码
        if not has_bom and file_size > 0:
            detected_encoding, confidence = self._infer_encoding_from_content(raw_header)

        return EncodingInfo(
            file_path=str(path.absolute()),
            encoding_type=detected_encoding,
            has_bom=has_bom,
            bom_bytes=bom_bytes,
            file_size=file_size,
            raw_header=raw_header[:64],
            confidence=confidence,
        )

    def _infer_encoding_from_content(self, content: bytes) -> tuple:
        """
        从字节内容推断编码格式

        使用启发式方法分析字节序列特征来判断编码。

        Args:
            content: 文件原始字节内容

        Returns:
            tuple: (EncodingType, confidence)
        """
        if not content:
            return EncodingType.UTF8_NOBOM, 0.8

        # 检查是否全为 ASCII 字符（0x00-0x7F）
        try:
            content.decode("ascii")
            # 全部是有效的 ASCII 字符
            if all(0 <= b <= 127 for b in content):
                return EncodingType.ASCII, 0.9
        except UnicodeDecodeError:
            pass

        # 尝试 UTF-8 解码
        try:
            content.decode("utf-8")
            # 检查是否有高字节序列（>0x7F）表明是多字节字符
            high_byte_ratio = sum(1 for b in content if b > 127) / len(content)
            if high_byte_ratio > 0.05:
                return EncodingType.UTF8_NOBOM, 0.85
            return EncodingType.ASCII, 0.75
        except UnicodeDecodeError:
            pass

        # 尝试 GBK/GB2312 解码（中文环境常见）
        try:
            decoded = content.decode("gbk")
            # 检查解码结果是否包含合理的中文或其他字符
            chinese_chars = sum(1 for c in decoded if "\u4e00" <= c <= "\u9fff")
            if chinese_chars > 0:
                return EncodingType.GBK, 0.75
        except UnicodeDecodeError:
            pass

        # 尝试 Latin-1（总是成功，但可能不准确）
        try:
            content.decode("latin1")
            return EncodingType.LATIN1, 0.5
        except Exception:
            pass

        return EncodingType.UNKNOWN, 0.1

    def fix_encoding(
        self,
        file_path: str,
        target_encoding: str = "utf-8",
        remove_bom: bool = True,
    ) -> bool:
        """
        修复文件编码格式

        将文件转换为目标编码格式，可选择移除 BOM 标记。

        Args:
            file_path: 要修复的文件路径
            target_encoding: 目标编码（默认 utf-8）
            remove_bom: 是否移除 BOM 标记（默认 True）

        Returns:
            bool: 是否成功修复

        Raises:
            FileNotFoundError: 文件不存在
            PermissionError: 无写入权限
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            # 先检测当前编码
            enc_info = self.detect_file_encoding(file_path)

            # 读取文件内容（使用检测到的编码或 UTF-8 作为后备）
            source_encoding = "utf-8"
            if enc_info.encoding_type != EncodingType.UNKNOWN:
                enc_map = {
                    EncodingType.UTF8_BOM: "utf-8-sig",
                    EncodingType.UTF8_NOBOM: "utf-8",
                    EncodingType.UTF16_LE: "utf-16-le",
                    EncodingType.UTF16_BE: "utf-16-be",
                    EncodingType.GBK: "gbk",
                    EncodingType.GB2312: "gb2312",
                    EncodingType.LATIN1: "latin1",
                    EncodingType.ASCII: "ascii",
                }
                source_encoding = enc_map.get(enc_info.encoding_type, "utf-8")

            # 尝试用源编码读取
            try:
                with open(file_path, "r", encoding=source_encoding) as f:
                    content = f.read()
            except (UnicodeDecodeError, LookupError):
                # 回退到 latin-1（可以读取任何字节序列）
                with open(file_path, "r", encoding="latin1") as f:
                    content = f.read()

            # 写入时确定目标编码
            write_encoding = target_encoding
            if target_encoding.lower() == "utf-8" and remove_bom:
                write_encoding = "utf-8"

            # 写入文件
            with open(file_path, "w", encoding=write_encoding, newline="\n") as f:
                f.write(content)

            return True

        except PermissionError:
            raise PermissionError(f"无权限写入文件: {file_path}")
        except Exception as e:
            raise RuntimeError(f"修复编码失败 [{file_path}]: {e}")

    def validate_project_encoding(
        self,
        root_path: str,
        file_patterns: Optional[list] = None,
        target_encoding: str = "utf-8",
    ) -> EncodingReport:
        """
        批量验证项目文件的编码格式

        扫描指定目录下的所有匹配文件，检查其编码是否符合要求，
        并可选择性修复不符合规范的文件。

        Args:
            root_path: 项目根目录路径
            file_patterns: 文件匹配模式列表（None 则使用内置默认列表）
            target_encoding: 目标编码格式（默认 utf-8）

        Returns:
            EncodingReport: 包含详细统计信息和每个文件的检测结果
        """
        report = EncodingReport(root_path=root_path, target_encoding=target_encoding)

        # 使用提供的模式或默认模式
        patterns = file_patterns or self.TEXT_FILE_PATTERNS

        root = Path(root_path)
        if not root.exists():
            report.failed_files.append(f"根目录不存在: {root_path}")
            return report

        # 收集所有需要检查的文件
        files_to_check = set()
        for pattern in patterns:
            try:
                matched = root.rglob(pattern)
                for f in matched:
                    if f.is_file():
                        files_to_check.add(f)
            except Exception:
                continue

        report.total_files = len(files_to_check)

        # 逐个检查文件编码
        for file_path in sorted(files_to_check):
            try:
                enc_info = self.detect_file_encoding(str(file_path))

                # 判断是否符合规范
                is_valid = True
                target_enc = target_encoding.lower().replace("-", "")
                current_enc = enc_info.encoding_type.value.replace("-", "").lower()

                if target_enc == "utf8":
                    # 对于 UTF-8 目标：允许 UTF-8 NO BOM 或 UTF-8 BOM
                    if current_enc not in ("utf8", "utf8nobom", "utf8bom"):
                        is_valid = False
                    # 但如果有 BOM 且不需要 BOM，则标记为无效
                    elif enc_info.has_bom and target_encoding.lower() == "utf-8":
                        is_valid = False
                else:
                    is_valid = current_enc == target_enc

                if is_valid:
                    report.valid_files += 1
                else:
                    report.invalid_files += 1
                    # 尝试修复
                    try:
                        if self.fix_encoding(str(file_path), target_encoding=target_encoding):
                            report.fixed_files += 1
                    except Exception:
                        report.failed_files.append(str(file_path))

                report.file_reports.append(enc_info.to_dict())

            except Exception as e:
                report.invalid_files += 1
                report.failed_files.append(f"{file_path}: {str(e)}")

        return report

    def validate_ps7_compatibility(self) -> CompatibilityReport:
        """
        验证当前环境对 PowerShell 7 的兼容性

        执行一系列检查项目：
        1. PowerShell 7 是否安装
        2. 版本号是否满足最低要求（>=7.0）
        3. 关键模块是否可用
        4. 执行策略设置
        5. 必要的环境变量配置

        Returns:
            CompatibilityReport: 包含所有检查结果的详细报告
        """
        report = CompatibilityReport(check_time=datetime.now())
        report.is_compatible = True  # 初始假设兼容

        # 检查1：PowerShell 7 是否可用
        try:
            result = subprocess.run(
                ["pwsh", "-Command", "$PSVersionTable.PSVersion.ToString()"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                version_str = result.stdout.strip()
                report.ps_version = version_str
                # 解析版本号
                major_version = int(version_str.split(".")[0]) if version_str else 0
                if major_version >= 7:
                    report.add_item(
                        CompatibilityItem(
                            name="PowerShell 7 安装",
                            status=True,
                            message=f"版本 {version_str}",
                            severity="info",
                        )
                    )
                else:
                    report.add_item(
                        CompatibilityItem(
                            name="PowerShell 版本",
                            status=False,
                            message=f"版本过低: {version_str} (需要 >= 7.0)",
                            severity="error",
                        )
                    )
                    report.warnings.append(f"建议升级 PowerShell 至 7.x 版本，当前版本: {version_str}")
            else:
                report.add_item(
                    CompatibilityItem(
                        name="PowerShell 可用性",
                        status=False,
                        message=f"无法执行 PowerShell: {result.stderr.strip()}",
                        severity="critical",
                    )
                )
                report.is_compatible = False
        except FileNotFoundError:
            report.add_item(
                CompatibilityItem(
                    name="PowerShell 7 安装",
                    status=False,
                    message="未找到 pwsh 命令（PowerShell 7）",
                    severity="critical",
                )
            )
            report.is_compatible = False
            report.warnings.append("请从 https://github.com/PowerShell/PowerShell 安装 PowerShell 7")
        except Exception as e:
            report.add_item(
                CompatibilityItem(
                    name="PowerShell 检测",
                    status=False,
                    message=f"检测失败: {str(e)}",
                    severity="error",
                )
            )
            report.is_compatible = False

        # 检查2：执行策略
        try:
            result = subprocess.run(
                ["pwsh", "-Command", "Get-ExecutionPolicy"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                policy = result.stdout.strip()
                allowed_policies = ["RemoteSigned", "Unrestricted", "Bypass", "AllSigned"]
                if policy in allowed_policies:
                    report.add_item(
                        CompatibilityItem(
                            name="执行策略",
                            status=True,
                            message=policy,
                            severity="info",
                        )
                    )
                else:
                    report.add_item(
                        CompatibilityItem(
                            name="执行策略",
                            status=False,
                            message=f"策略受限: {policy}",
                            severity="warning",
                        )
                    )
                    report.warnings.append(f"当前执行策略 '{policy}' 可能限制脚本运行，建议设置为 RemoteSigned")
        except Exception as e:
            report.add_item(
                CompatibilityItem(
                    name="执行策略检查",
                    status=None,
                    message=f"无法检查: {str(e)}",
                    severity="warning",
                )
            )

        # 检查3：关键模块可用性
        critical_modules = ["Microsoft.PowerShell.Management", "Microsoft.PowerShell.Utility"]
        for module in critical_modules:
            try:
                result = subprocess.run(
                    ["pwsh", "-Command", f"Get-Module -Name {module} -ListAvailable"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and result.stdout.strip():
                    report.add_item(
                        CompatibilityItem(
                            name=f"模块: {module}",
                            status=True,
                            message="已安装",
                            severity="info",
                        )
                    )
                else:
                    report.add_item(
                        CompatibilityItem(
                            name=f"模块: {module}",
                            status=False,
                            message="未找到",
                            severity="warning",
                        )
                    )
            except Exception:
                report.add_item(
                    CompatibilityItem(
                        name=f"模块检查: {module}",
                        status=None,
                        message="检查失败",
                        severity="warning",
                    )
                )

        # 检查4：环境变量配置
        env_checks = [
            ("PATH", "PATH 环境变量", "系统路径配置"),
            ("HOME" if platform.system() != "Windows" else "USERPROFILE", "用户目录", "用户主目录"),
            ("TEMP" if platform.system() == "Windows" else "TMPDIR", "临时目录", "临时文件存储"),
        ]

        for var_name, display_name, description in env_checks:
            value = os.environ.get(var_name)
            if value:
                report.add_item(
                    CompatibilityItem(
                        name=display_name,
                        status=True,
                        message=f"{description}: 已配置",
                        severity="info",
                    )
                    if var_name in os.environ
                    else CompatibilityItem(
                        name=display_name,
                        status=False,
                        message=f"{description}: 未配置",
                        severity="warning",
                    )
                )
            else:
                report.add_item(
                    CompatibilityItem(
                        name=display_name,
                        status=False,
                        message=f"{description}: 未配置 ({var_name})",
                        severity="warning",
                    )
                )

        # 检查5：文件系统权限测试
        test_dir = Path(tempfile.gettempdir()) / "ps7_compat_test"
        try:
            test_dir.mkdir(exist_ok=True)
            test_file = test_dir / "test_write.tmp"
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()
            test_dir.rmdir()
            report.add_item(
                CompatibilityItem(
                    name="文件系统写入权限",
                    status=True,
                    message="临时目录可读写",
                    severity="info",
                )
            )
        except Exception as e:
            report.add_item(
                CompatibilityItem(
                    name="文件系统写入权限",
                    status=False,
                    message=f"权限不足: {str(e)}",
                    severity="error",
                )
            )
            report.is_compatible = False

        # 检查6：网络连通性（可选）
        try:
            import socket

            socket.create_connection(("github.com", 443), timeout=3)
            socket.default_timeout.close()
            report.add_item(
                CompatibilityItem(
                    name="网络连接",
                    status=True,
                    message="网络可达",
                    severity="info",
                )
            )
        except Exception:
            report.add_item(
                CompatibilityItem(
                    name="网络连接",
                    status=None,
                    message="无法连接外网（非必需）",
                    severity="info",
                )
            )

        return report


import tempfile
