import subprocess
import time
import signal
import os
import threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

from .base_adapter import (
    PlatformAdapter,
    PlatformType,
    ExecutionResult,
    EnvironmentInfo,
)


@dataclass
class BashExecutionResult(ExecutionResult):
    signal_received: int | None = None
    background_pid: int | None = None


@dataclass
class BackgroundProcess:
    pid: int
    command: str
    started_at: float
    process: subprocess.Popen


class BashAdapter(PlatformAdapter):
    """Bash Shell适配器，支持Linux/macOS环境"""

    def __init__(self, shell_path: str | None = None):
        self._shell_path = shell_path or self._detect_shell()
        self._background_processes: dict[int, BackgroundProcess] = {}
        self._process_lock = threading.Lock()
        self._signal_handlers_installed = False

    def get_platform_type(self) -> PlatformType:
        return PlatformType.BASH

    def execute_script(self, script_path: Path, args: dict | None = None) -> ExecutionResult:
        if not script_path.exists():
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Script not found: {script_path}",
                duration_ms=0,
                platform=PlatformType.BASH,
            )
        start_time = time.time()
        cmd_parts = [str(script_path)]
        if args:
            for key, value in args.items():
                cmd_parts.extend([f"--{key}", str(value)])
        try:
            result = subprocess.run(
                ["python"] + cmd_parts,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
                cwd=str(script_path.parent),
            )
            duration_ms = (time.time() - start_time) * 1000
            return BashExecutionResult(
                success=result.returncode == 0,
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_ms=duration_ms,
                platform=PlatformType.BASH,
            )
        except subprocess.TimeoutExpired as e:
            duration_ms = (time.time() - start_time) * 1000
            return BashExecutionResult(
                success=False,
                return_code=-1,
                stdout=e.stdout.decode("utf-8", errors="replace") if e.stdout else "",
                stderr=f"Script execution timed out: {str(e)}",
                duration_ms=duration_ms,
                signal_received=getattr(signal, "SIGTERM", None),
                platform=PlatformType.BASH,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return BashExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Failed to execute script: {str(e)}",
                duration_ms=duration_ms,
                platform=PlatformType.BASH,
            )

    def run_command(
        self, cmd: str, timeout: int = 300, work_dir: Path | None = None
    ) -> ExecutionResult:
        is_background = cmd.strip().endswith("&")
        if is_background:
            return self._run_background_command(cmd.rstrip("&").strip(), work_dir)
        start_time = time.time()
        try:
            full_cmd = f'set -e; {cmd}'
            result = subprocess.run(
                [self._shell_path, "-c", full_cmd],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                cwd=str(work_dir) if work_dir else None,
                preexec_fn=os.setpgrp if hasattr(os, "setpgrp") else None,
            )
            duration_ms = (time.time() - start_time) * 1000
            return BashExecutionResult(
                success=result.returncode == 0,
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_ms=duration_ms,
                platform=PlatformType.BASH,
            )
        except subprocess.TimeoutExpired as e:
            duration_ms = (time.time() - start_time) * 1000
            self._kill_process_group(getattr(e, "pid", None))
            return BashExecutionResult(
                success=False,
                return_code=-1,
                stdout=e.stdout.decode("utf-8", errors="replace") if e.stdout else "",
                stderr=f"Command timed out after {timeout}s: {str(e)}",
                duration_ms=duration_ms,
                signal_received=getattr(signal, "SIGTERM", None),
                platform=PlatformType.BASH,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return BashExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Failed to execute command: {str(e)}",
                duration_ms=duration_ms,
                platform=PlatformType.BASH,
            )

    def manage_modules(self, action: str, module_name: str) -> bool:
        package_managers = {
            "python": {
                "install": f"pip install {module_name}",
                "update": f"pip install --upgrade {module_name}",
                "uninstall": f"pip uninstall -y {module_name}",
            },
            "node": {
                "install": f"npm install {module_name}",
                "update": f"npm update {module_name}",
                "uninstall": f"npm uninstall {module_name}",
            },
            "system": {
                "install": f"apt-get install -y {module_name}" if self._is_debian_based() else f"yum install -y {module_name}",
                "update": f"apt-get upgrade -y {module_name}" if self._is_debian_based() else f"yum update -y {module_name}",
                "uninstall": f"apt-get remove -y {module_name}" if self._is_debian_based() else f"yum remove -y {module_name}",
            },
        }
        manager_type = self._detect_package_manager(module_name)
        manager_cmds = package_managers.get(manager_type, package_managers["python"])
        cmd = manager_cmds.get(action.lower())
        if not cmd:
            return False
        result = self.run_command(cmd)
        return result.success

    def get_environment_info(self) -> EnvironmentInfo:
        import platform
        import sys

        os_info_cmd = 'echo "$(uname -s):$(uname -r):$(uname -m)"'
        shell_result = self.run_command(os_info_cmd)
        shell_info = shell_result.stdout.strip().split(":") if shell_result.success else []
        terminal_type = Path(self._shell_path).name if self._shell_path else "unknown"
        encoding = "utf-8"
        try:
            locale_output = self.run_command("echo $LANG")
            if locale_output.success and locale_output.stdout.strip():
                lang = locale_output.stdout.strip().lower()
                if "utf-8" in lang or "utf8" in lang:
                    encoding = "utf-8"
                elif "gbk" in lang or "gb2312" in lang or "gb18030" in lang:
                    encoding = "gbk"
        except Exception:
            pass
        return EnvironmentInfo(
            platform_type=PlatformType.BASH,
            os_name=shell_info[0] if len(shell_info) > 0 else platform.system(),
            os_version=shell_info[1] if len(shell_info) > 1 else platform.version(),
            python_version=sys.version.split()[0],
            terminal_type=terminal_type,
            encoding=encoding,
            home_dir=Path.home(),
            working_dir=Path.cwd(),
        )

    def validate_environment(self) -> tuple[bool, list[str]]:
        issues = []
        shell_check = self.run_command(f"{self._shell_path} --version")
        if not shell_check.success:
            issues.append(f"Bash shell ({self._shell_path}) is not available")
        version_match = re.search(r"version (\d+)\.(\d+)", shell_check.stdout, re.IGNORECASE)
        if version_match:
            major, minor = int(version_match.group(1)), int(version_match.group(2))
            if major < 4 or (major == 4 and minor < 0):
                issues.append(f"Bash version {major}.{minor} may have limited compatibility")
        python_check = self.run_command("python3 --version || python --version")
        if not python_check.success:
            issues.append("Python is not installed or not accessible")
        permission_test = self.run_command("test -w /tmp && echo 'ok'")
        if not permission_test.success or "ok" not in permission_test.stdout:
            issues.append("Cannot write to temporary directory")
        encoding_test = self.run_command('echo "测试中文" | iconv -f utf-8 -t utf-8')
        if not encoding_test.success:
            issues.append("UTF-8 encoding support verification failed")
        return len(issues) == 0, issues

    def send_signal(self, pid: int, sig: int) -> bool:
        """向进程发送信号"""
        try:
            os.kill(pid, sig)
            return True
        except ProcessLookupError:
            with self._process_lock:
                if pid in self._background_processes:
                    del self._background_processes[pid]
            return False
        except PermissionError:
            return False
        except Exception as e:
            print(f"Failed to send signal {sig} to PID {pid}: {e}")
            return False

    def kill_process(self, pid: int) -> bool:
        """终止指定进程（SIGKILL）"""
        return self.send_signal(pid, signal.SIGKILL)

    def terminate_process(self, pid: int) -> bool:
        """优雅终止进程（SIGTERM）"""
        return self.send_signal(pid, signal.SIGTERM)

    def interrupt_process(self, pid: int) -> bool:
        """中断进程（SIGINT，相当于Ctrl+C）"""
        return self.send_signal(pid, signal.SIGINT)

    def list_background_processes(self) -> list[BackgroundProcess]:
        """列出所有后台进程"""
        with self._process_lock:
            active_processes = []
            for pid, proc in list(self._background_processes.items()):
                if proc.process.poll() is None:
                    active_processes.append(proc)
                else:
                    del self._background_processes[pid]
            return active_processes

    def cleanup_background_processes(self) -> None:
        """清理所有后台进程"""
        with self._process_lock:
            for pid, proc in list(self._background_processes.items()):
                try:
                    proc.process.terminate()
                    proc.process.wait(timeout=5)
                except Exception:
                    try:
                        proc.process.kill()
                    except Exception:
                        pass
            self._background_processes.clear()

    def export_env_var(self, key: str, value: str) -> bool:
        """导出环境变量"""
        escaped_value = value.replace("'", "'\\''")
        cmd = f"export {key}='{escaped_value}'"
        result = self.run_command(cmd)
        if result.success:
            os.environ[key] = value
        return result.success

    def unset_env_var(self, key: str) -> bool:
        """取消设置环境变量"""
        cmd = f"unset {key}"
        result = self.run_command(cmd)
        if result.success and key in os.environ:
            del os.environ[key]
        return result.success

    def source_script(self, script_path: Path) -> ExecutionResult:
        """执行source命令加载脚本"""
        if not script_path.exists():
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Script not found: {script_path}",
                duration_ms=0,
                platform=PlatformType.BASH,
            )
        cmd = f"source {script_path}"
        return self.run_command(cmd)

    def _run_background_command(self, cmd: str, work_dir: Path | None = None) -> ExecutionResult:
        start_time = time.time()
        try:
            nohup_cmd = f"nohup {cmd} > /dev/null 2>&1 & echo $!"
            result = subprocess.run(
                [self._shell_path, "-c", nohup_cmd],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
                cwd=str(work_dir) if work_dir else None,
            )
            if result.returncode == 0 and result.stdout.strip().isdigit():
                pid = int(result.stdout.strip())
                process = subprocess.Popen(
                    [self._shell_path, "-c", cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                    cwd=str(work_dir) if work_dir else None,
                )
                bg_proc = BackgroundProcess(
                    pid=pid,
                    command=cmd,
                    started_at=time.time(),
                    process=process,
                )
                with self._process_lock:
                    self._background_processes[pid] = bg_proc
                duration_ms = (time.time() - start_time) * 1000
                return BashExecutionResult(
                    success=True,
                    return_code=0,
                    stdout=f"Background process started with PID: {pid}",
                    stderr="",
                    duration_ms=duration_ms,
                    platform=PlatformType.BASH,
                    background_pid=pid,
                )
            else:
                duration_ms = (time.time() - start_time) * 1000
                return BashExecutionResult(
                    success=False,
                    return_code=result.returncode,
                    stdout="",
                    stderr=result.stderr or "Failed to start background process",
                    duration_ms=duration_ms,
                    platform=PlatformType.BASH,
                )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return BashExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Failed to start background process: {str(e)}",
                duration_ms=duration_ms,
                platform=PlatformType.BASH,
            )

    def _detect_shell(self) -> str:
        possible_shells = [
            "/bin/bash",
            "/usr/bin/bash",
            "/usr/local/bin/bash",
            "/bin/sh",
            "/bin/zsh",
            "/usr/bin/zsh",
        ]
        for shell in possible_shells:
            if os.path.isfile(shell) and os.access(shell, os.X_OK):
                return shell
        return "/bin/sh"

    def _detect_package_manager(self, module_name: str) -> str:
        if module_name.endswith(".py") or "." in module_name and module_name.split(".")[0].islower():
            return "python"
        if any(module_name.startswith(prefix) for prefix in ["@", "react", "vue", "angular"]):
            return "node"
        return "system"

    def _is_debian_based(self) -> bool:
        try:
            result = subprocess.run(
                ["cat", "/etc/os-release"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return "debian" in result.stdout.lower() or "ubuntu" in result.stdout.lower()
        except Exception:
            return False

    def _kill_process_group(self, pgid: int | None) -> None:
        if pgid is None:
            return
        try:
            os.killpg(pgid, signal.SIGTERM)
            time.sleep(1)
            os.killpg(pgid, signal.SIGKILL)
        except Exception:
            pass

    def __del__(self):
        try:
            self.cleanup_background_processes()
        except Exception:
            pass


import re
