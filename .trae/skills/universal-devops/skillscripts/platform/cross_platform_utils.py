import os
import sys
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .base_adapter import PlatformType


def detect_os() -> PlatformType:
    """检测当前操作系统类型"""
    system = platform.system().lower()
    if system == "windows":
        try:
            result = subprocess.run(
                ["pwsh", "-Command", "$PSVersionTable.PSVersion.Major"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip() >= "7":
                return PlatformType.POWERSHELL_7
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
        return PlatformType.POWERSHELL_7
    elif system in ("linux", "darwin"):
        return PlatformType.BASH
    else:
        return PlatformType.UNKNOWN


def detect_terminal() -> str:
    """检测当前终端类型（pwsh/bash/zsh/cmd）"""
    shell = os.environ.get("SHELL", "")
    term = os.environ.get("TERM", "")
    if platform.system() == "Windows":
        if "pwsh" in shell.lower() or os.environ.get("PSMODULEPATH"):
            return "pwsh"
        if "cmd.exe" in shell.lower() or not shell:
            return "cmd"
        if "powershell" in shell.lower():
            return "powershell"
    else:
        if "bash" in shell:
            return "bash"
        if "zsh" in shell:
            return "zsh"
        if "fish" in shell:
            return "fish"
        if "sh" in shell:
            return "sh"
    return "unknown"


def normalize_path(path: str | Path) -> Path:
    """规范化路径为当前OS原生的格式"""
    path_obj = Path(path)
    try:
        resolved = path_obj.resolve()
        return resolved
    except (OSError, ValueError):
        expanded = Path(path).expanduser()
        if platform.system() == "Windows":
            str_path = str(expanded).replace("/", "\\")
            return Path(str_path)
        return expanded


def detect_encoding(file_path: Path) -> str:
    """检测文件编码"""
    if not file_path.exists():
        return "utf-8"
    try:
        with open(file_path, "rb") as f:
            raw_bytes = f.read(8192)
        if raw_bytes[:3] == b"\xef\xbb\xbf":
            return "utf-8-sig"
        if raw_bytes[:2] in (b"\xff\xfe", b"\xfe\xff"):
            return "utf-16"
        try:
            raw_bytes.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            pass
        try:
            raw_bytes.decode("gbk")
            return "gbk"
        except UnicodeDecodeError:
            pass
        try:
            raw_bytes.decode("latin-1")
            return "latin-1"
        except UnicodeDecodeError:
            pass
        return "utf-8"
    except Exception:
        return "utf-8"


def convert_to_utf8_no_bom(content: bytes | str, source_encoding: str = "auto") -> str:
    """将任意编码的内容转换为UTF-8无BOM字符串"""
    if isinstance(content, bytes):
        if source_encoding == "auto":
            detected = detect_encoding_from_bytes(content)
            source_encoding = detected
        try:
            text = content.decode(source_encoding, errors="replace")
        except (LookupError, UnicodeDecodeError):
            text = content.decode("utf-8", errors="replace")
    else:
        text = content
    if text.startswith("\ufeff"):
        text = text[1:]
    return text


def detect_encoding_from_bytes(raw_bytes: bytes) -> str:
    """从字节内容检测编码"""
    if raw_bytes[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"
    if raw_bytes[:2] == b"\xff\xfe":
        return "utf-16-le"
    if raw_bytes[:2] == b"\xfe\xff":
        return "utf-16-be"
    for encoding in ["utf-8", "gbk", "gb18030", "big5", "latin-1"]:
        try:
            raw_bytes.decode(encoding)
            return encoding
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"


def get_home_directory() -> Path:
    """获取用户主目录（跨平台）"""
    home = Path.home()
    if not home or str(home) == "." or str(home) == "/":
        env_home = os.environ.get("USERPROFILE") or os.environ.get("HOME")
        if env_home:
            home = Path(env_home)
    return home


def get_temp_directory() -> Path:
    """获取临时目录（跨平台）"""
    temp_dir = Path(tempfile.gettempdir())
    try:
        temp_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        fallback = get_home_directory() / ".temp"
        try:
            fallback.mkdir(parents=True, exist_ok=True)
            temp_dir = fallback
        except OSError:
            pass
    return temp_dir


def is_admin() -> bool:
    """检查是否有管理员/root权限"""
    try:
        if platform.system() == "Windows":
            import ctypes
            try:
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except (AttributeError, OSError):
                return False
        else:
            return os.geteuid() == 0
    except (AttributeError, OSError):
        return False


def get_env_var(key: str, default: str | None = None) -> str | None:
    """跨平台获取环境变量"""
    value = os.environ.get(key, default)
    if value is None:
        if key.upper() in ("HOME", "USERPROFILE"):
            return str(get_home_directory())
        if key.upper() == "TEMP" or key.upper() == "TMP":
            return str(get_temp_directory())
        if key.upper() == "PATH":
            return os.environ.get("Path", os.environ.get("PATH", ""))
    return value


def set_env_var(key: str, value: str) -> None:
    """跨平台设置环境变量（当前进程级别）"""
    os.environ[key] = value


def get_platform_info() -> dict:
    """获取详细的平台信息"""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "architecture": platform.architecture(),
        "platform_type": detect_os().value,
        "terminal": detect_terminal(),
        "encoding": get_default_encoding(),
        "is_admin": is_admin(),
    }


def get_default_encoding() -> str:
    """获取系统默认编码"""
    preferred = os.environ.get("LANG", "").lower().split(".")[-1]
    if preferred and preferred != "c":
        return preferred
    if platform.system() == "Windows":
        import locale
        return locale.getpreferredencoding()
    return "utf-8"


def ensure_directory_exists(path: Path) -> bool:
    """确保目录存在，不存在则创建"""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Failed to create directory {path}: {e}")
        return False


def safe_filename(filename: str) -> str:
    """生成安全的文件名（移除或替换非法字符）"""
    if platform.system() == "Windows":
        illegal_chars = '<>:"/\\|?*'
    else:
        illegal_chars = "/"
    safe = filename
    for char in illegal_chars:
        safe = safe.replace(char, "_")
    safe = safe.strip(". ")
    if not safe or safe in (".", ".."):
        safe = "unnamed"
    max_length = 255 if platform.system() != "Windows" else 260
    if len(safe) > max_length:
        name, ext = os.path.splitext(safe)
        safe = name[:max_length - len(ext)] + ext
    return safe


def join_paths(*paths: str | Path) -> Path:
    """跨平台路径拼接"""
    result = Path()
    for p in paths:
        result = result / Path(p)
    return result


def relative_to(base: Path, target: Path) -> Path:
    """计算相对路径（跨平台安全版本）"""
    try:
        return target.relative_to(base)
    except ValueError:
        common_base = base
        while common_base != common_base.parent:
            try:
                return target.relative_to(common_base)
            except ValueError:
                common_base = common_base.parent
        return target


def expand_user(path: str | Path) -> Path:
    """展开用户目录中的~符号"""
    return Path(path).expanduser()


def file_size_human_readable(size_bytes: int) -> str:
    """将字节数转换为人类可读的格式"""
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} EB"


def is_executable(path: Path) -> bool:
    """检查文件是否可执行"""
    return path.is_file() and os.access(str(path), os.X_OK)


def which(command: str) -> Path | None:
    """查找命令的完整路径（跨平台版which/get-command）"""
    if platform.system() == "Windows":
        extensions = [".exe", ".cmd", ".bat", ".ps1"]
        command_with_ext = command
        if not any(command.lower().endswith(ext) for ext in extensions):
            command_with_ext = command + ".exe"
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        for directory in path_dirs:
            full_path = Path(directory) / command_with_ext
            if full_path.is_file():
                return full_path
            for ext in extensions:
                alt_path = Path(directory) / (command + ext)
                if alt_path.is_file():
                    return alt_path
    else:
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        for directory in path_dirs:
            full_path = Path(directory) / command
            if is_executable(full_path):
                return full_path
    return None


def check_command_available(command: str) -> bool:
    """检查命令是否可用"""
    return which(command) is not None


def run_cross_platform(cmd: str, timeout: int = 300) -> tuple[int, str, str]:
    """执行跨平台命令，返回(返回码, stdout, stderr)"""
    current_platform = detect_os()
    if current_platform == PlatformType.POWERSHELL_7:
        from .powershell_adapter import PowerShell7Adapter

        adapter = PowerShell7Adapter()
        result = adapter.run_command(cmd, timeout=timeout)
        return result.return_code, result.stdout, result.stderr
    elif current_platform == PlatformType.BASH:
        from .bash_adapter import BashAdapter

        adapter = BashAdapter()
        result = adapter.run_command(cmd, timeout=timeout)
        return result.return_code, result.stdout, result.stderr
    else:
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)


def get_adapter_for_current_platform():
    """获取当前平台的适配器实例"""
    platform_type = detect_os()
    if platform_type == PlatformType.POWERSHELL_7:
        from .powershell_adapter import PowerShell7Adapter

        return PowerShell7Adapter()
    elif platform_type == PlatformType.BASH:
        from .bash_adapter import BashAdapter

        return BashAdapter()
    else:
        raise NotImplementedError(f"No adapter available for platform type: {platform_type}")
