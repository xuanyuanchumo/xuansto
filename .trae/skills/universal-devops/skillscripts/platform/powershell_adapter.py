import subprocess
import time
import re
import json
import threading
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

from .base_adapter import (
    PlatformAdapter,
    PlatformType,
    ExecutionResult,
    EnvironmentInfo,
)


BASH_TO_PS_COMMAND_MAP = {
    "ls": "Get-ChildItem",
    "ls -la": "Get-ChildItem -Force",
    "cat": "Get-Content",
    "cp": "Copy-Item",
    "mv": "Move-Item",
    "rm": "Remove-Item",
    "mkdir": "New-Item -ItemType Directory",
    "rmdir": "Remove-Item -Recurse",
    "touch": "New-Item",
    "find": "Get-ChildItem -Recurse",
    "grep": "Select-String",
    "head": "Select-Object -First",
    "tail": "Select-Object -Last",
    "wc -l": "(Get-Content).Count",
    "chmod": "Set-Acl",
    "chown": "Set-Acl",
    "curl": "Invoke-RestMethod",
    "wget": "Invoke-WebRequest",
    "ssh": "Enter-PSSession",
    "scp": "Copy-Item -ToSession",
    "ps": "Get-Process",
    "kill": "Stop-Process",
    "top": "Get-Process | Sort-Object CPU -Descending",
    "bg": "Start-Job",
    "fg": "Receive-Job",
    "pip": "pip",
    "npm": "npm",
    "python": "python",
    "git": "git",
    "echo": "Write-Output",
    "which": "Get-Command",
    "env": "Get-ChildItem Env:",
    "clear": "Clear-Host",
    "history": "Get-History",
    "sleep": "Start-Sleep",
    "date": "Get-Date",
    "uname": "$env:OS",
    "whoami": "$env:USERNAME",
    "pwd": "Get-Location",
    "cd": "Set-Location",
    "export": "$env:{KEY}={VALUE}",
    "source": ". {PATH}",
    "|": "|",
    ">": ">",
    ">>": ">>",
    "2>&1": "2>&1",
    "rm -rf": "Remove-Item -Recurse -Force",
    "format": "Format-Volume",
    "diff": "Compare-Object",
    "sort": "Sort-Object",
    "uniq": "Select-Object -Unique",
    "tar": "Compress-Archive / Expand-Archive",
    "zip": "Compress-Archive",
    "unzip": "Expand-Archive",
    "df": "Get-PSDrive",
    "du": "{Get-ChildItem -Recurse | Measure-Object -Property Length -Sum}.Sum",
    "free": "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory",
    "ifconfig": "Get-NetIPAddress",
    "ip addr": "Get-NetIPAddress",
    "netstat": "Get-NetTCPConnection",
    "ping": "Test-Connection",
    "nslookup": "Resolve-DnsName",
    "dig": "Resolve-DnsName",
    "telnet": "Test-NetConnection",
    "ftp": "Set-FTPClient",
    "rsync": "Robocopy",
    "screen": "Enter-PSHostProcess",
    "tmux": "PSSessionConfiguration",
    "awk": "ForEach-Object",
    "sed": "-replace",
    "cut": "Select-Object",
    "tr": "-replace",
    "xargs": "ForEach-Object",
    "tee": "Tee-Object",
    "less": "Out-GridView -PassThru",
    "more": "Out-Host -Paging",
    "man": "Get-Help",
    "info": "Get-Help -Detailed",
    "alias": "Get-Alias",
    "ln": "New-Item -ItemType SymbolicLink",
    "readlink": "(Get-Item).Target",
    "file": "Get-Content | Select-Object -First 1",
    "stat": "Get-ItemProperty",
    "realpath": "Resolve-Path",
    "basename": "Split-Path -Leaf",
    "dirname": "Split-Path",
    "dirname -p": "Split-Path",
    "read": "Read-Host",
    "yes": "1..N | ForEach-Object { 'y' }",
    "time": "Measure-Command",
    "timeout": "Start-Sleep",
    "watch": "while($true) { cls; <command>; Start-Sleep 2 }",
    "xclip": "Set-Clipboard",
    "xsel": "Set-Clipboard",
    "pbcopy": "Set-Clipboard",
    "pbpaste": "Get-Clipboard",
}


@dataclass
class PowerShellExecutionResult(ExecutionResult):
    parsed_objects: list[dict] | None = None
    warnings: list[str] | None = None
    verbose_output: str | None = None


class PowerShellSession:
    def __init__(self, session_id: str, process: subprocess.Popen):
        self.session_id = session_id
        self.process = process
        self.created_at = time.time()
        self.last_used = time.time()
        self.is_busy = False
        self.lock = threading.Lock()


class PowerShellSessionPool:
    """PowerShell会话池管理器"""

    def __init__(self, max_sessions: int = 5):
        self.max_sessions = max_sessions
        self._sessions: dict[str, PowerShellSession] = {}
        self._available: list[str] = []
        self._lock = threading.Lock()

    def acquire_session(self, agent_id: str) -> PowerShellSession:
        with self._lock:
            if self._available:
                session_id = self._available.pop()
                session = self._sessions[session_id]
                session.is_busy = True
                session.last_used = time.time()
                return session
            if len(self._sessions) >= self.max_sessions:
                oldest_session_id = min(
                    self._sessions.keys(),
                    key=lambda sid: self._sessions[sid].last_used,
                )
                if not self._sessions[oldest_session_id].is_busy:
                    self._terminate_session(oldest_session_id)
            session_id = f"ps-session-{uuid.uuid4().hex[:8]}"
            process = self._create_powershell_process()
            session = PowerShellSession(session_id, process)
            self._sessions[session_id] = session
            session.is_busy = True
            return session

    def release_session(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.is_busy = False
                session.last_used = time.time()
                if session_id not in self._available:
                    self._available.append(session_id)

    def execute_in_session(
        self, session_id: str, command: str, timeout: int = 300
    ) -> PowerShellExecutionResult:
        session = self._sessions.get(session_id)
        if not session or session.process.poll() is not None:
            if session_id in self._sessions:
                del self._sessions[session_id]
            if session_id in self._available:
                self._available.remove(session_id)
            raise RuntimeError(f"Session {session_id} is not available")
        start_time = time.time()
        try:
            encoded_command = self._encode_command(command)
            session.process.stdin.write((encoded_command + "\n").encode("utf-8"))
            session.process.stdin.flush()
            stdout_lines = []
            stderr_lines = []
            while True:
                elapsed = (time.time() - start_time) * 1000
                if elapsed > timeout * 1000:
                    return PowerShellExecutionResult(
                        success=False,
                        return_code=-1,
                        stdout="",
                        stderr=f"Command timed out after {timeout}s",
                        duration_ms=elapsed,
                        platform=PlatformType.POWERSHELL_7,
                    )
                line = session.process.stdout.readline()
                if line:
                    decoded_line = line.decode("utf-8", errors="replace")
                    if decoded_line.strip().startswith("PS>"):
                        break
                    stdout_lines.append(decoded_line)
                else:
                    time.sleep(0.01)
            duration_ms = (time.time() - start_time) * 1000
            stdout_text = "".join(stdout_lines)
            stderr_text = "".join(stderr_lines)
            parsed_objects = self._parse_ps_output(stdout_text) if stdout_text else None
            warnings = self._extract_warnings(stderr_text) if stderr_text else None
            return PowerShellExecutionResult(
                success=session.process.returncode == 0 or session.process.returncode is None,
                return_code=0,
                stdout=stdout_text.rstrip(),
                stderr=stderr_text.rstrip(),
                duration_ms=duration_ms,
                platform=PlatformType.POWERSHELL_7,
                parsed_objects=parsed_objects,
                warnings=warnings,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return PowerShellExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms,
                platform=PlatformType.POWERSHELL_7,
            )

    def _create_powershell_process(self) -> subprocess.Popen:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return subprocess.Popen(
            ["pwsh", "-NoExit", "-Command", "function prompt { 'PS> ' }"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            encoding=None,
            errors=None,
            startupinfo=startupinfo,
            cwd=None,
        )

    def _encode_command(self, command: str) -> str:
        escaped = command.replace("'", "''")
        return f"'{escaped}'"

    def _parse_ps_output(self, output: str) -> list[dict] | None:
        try:
            lines = output.strip().split("\n")
            objects = []
            for line in lines:
                if line.strip() and not line.startswith("PS>") and ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        objects.append({parts[0].strip(): parts[1].strip()})
            return objects if objects else None
        except Exception:
            return None

    def _extract_warnings(self, stderr: str) -> list[str]:
        warning_pattern = r"(?:WARNING|WARN)\s*:\s*(.+)"
        matches = re.findall(warning_pattern, stderr, re.IGNORECASE)
        return matches if matches else None

    def _terminate_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            session = self._sessions[session_id]
            try:
                session.process.terminate()
                session.process.wait(timeout=5)
            except Exception:
                try:
                    session.process.kill()
                except Exception:
                    pass
            del self._sessions[session_id]
            if session_id in self._available:
                self._available.remove(session_id)

    def cleanup_all(self) -> None:
        with self._lock:
            for session_id in list(self._sessions.keys()):
                self._terminate_session(session_id)
            self._available.clear()


class PowerShell7Adapter(PlatformAdapter):
    """PowerShell 7 原生适配器"""

    def __init__(self):
        self._session_pool = PowerShellSessionPool(max_sessions=5)
        self._command_map = BASH_TO_PS_COMMAND_MAP.copy()

    def get_platform_type(self) -> PlatformType:
        return PlatformType.POWERSHELL_7

    def execute_script(self, script_path: Path, args: dict | None = None) -> ExecutionResult:
        if not script_path.exists():
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Script not found: {script_path}",
                duration_ms=0,
                platform=PlatformType.POWERSHELL_7,
            )
        start_time = time.time()
        cmd_parts = ["python", str(script_path)]
        if args:
            for key, value in args.items():
                cmd_parts.extend([f"--{key}", str(value)])
        try:
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
                cwd=script_path.parent,
            )
            duration_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=result.returncode == 0,
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_ms=duration_ms,
                platform=PlatformType.POWERSHELL_7,
            )
        except subprocess.TimeoutExpired as e:
            duration_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout=e.stdout.decode("utf-8", errors="replace") if e.stdout else "",
                stderr=f"Script execution timed out: {str(e)}",
                duration_ms=duration_ms,
                platform=PlatformType.POWERSHELL_7,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Failed to execute script: {str(e)}",
                duration_ms=duration_ms,
                platform=PlatformType.POWERSHELL_7,
            )

    def run_command(self, cmd: str, timeout: int = 300, work_dir: Path | None = None) -> ExecutionResult:
        converted_cmd = self.convert_bash_to_powershell(cmd)
        start_time = time.time()
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.run(
                ["pwsh", "-NoProfile", "-Command", converted_cmd],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                cwd=str(work_dir) if work_dir else None,
                startupinfo=startupinfo,
            )
            duration_ms = (time.time() - start_time) * 1000
            parsed_objects = self._parse_output_objects(result.stdout) if result.stdout else None
            warnings = self._extract_warnings(result.stderr) if result.stderr else None
            return PowerShellExecutionResult(
                success=result.returncode == 0,
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_ms=duration_ms,
                platform=PlatformType.POWERSHELL_7,
                parsed_objects=parsed_objects,
                warnings=warnings,
            )
        except subprocess.TimeoutExpired as e:
            duration_ms = (time.time() - start_time) * 1000
            return PowerShellExecutionResult(
                success=False,
                return_code=-1,
                stdout=e.stdout.decode("utf-8", errors="replace") if e.stdout else "",
                stderr=f"Command timed out after {timeout}s: {str(e)}",
                duration_ms=duration_ms,
                platform=PlatformType.POWERSHELL_7,
            )
        except FileNotFoundError:
            duration_ms = (time.time() - start_time) * 1000
            return PowerShellExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr="PowerShell 7 (pwsh) is not installed or not found in PATH",
                duration_ms=duration_ms,
                platform=PlatformType.POWERSHELL_7,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return PowerShellExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Failed to execute command: {str(e)}",
                duration_ms=duration_ms,
                platform=PlatformType.POWERSHELL_7,
            )

    def manage_modules(self, action: str, module_name: str) -> bool:
        action_map = {
            "install": "Install-Module",
            "update": "Update-Module",
            "uninstall": "Uninstall-Module",
        }
        ps_action = action_map.get(action.lower())
        if not ps_action:
            return False
        cmd = f"{ps_action} -Name {module_name} -Force -Scope CurrentUser"
        result = self.run_command(cmd)
        return result.success

    def get_environment_info(self) -> EnvironmentInfo:
        import platform
        import sys
        from pathlib import Path

        info_cmd = "$PSVersionTable.PSVersion.ToString(); $env:OS; [System.Text.Encoding]::Default.CodePage; $HOME"
        result = self.run_command(info_cmd)
        lines = result.stdout.strip().split("\n") if result.success else []
        ps_version = lines[0] if len(lines) > 0 else "Unknown"
        os_name = lines[1] if len(lines) > 1 else platform.system()
        codepage = lines[2] if len(lines) > 2 else "Unknown"
        home_dir = Path(lines[3]) if len(lines) > 3 else Path.home()
        encoding = "utf-8"
        if codepage and codepage != "Unknown":
            try:
                cp_num = int(codepage)
                if cp_num == 65001:
                    encoding = "utf-8"
                elif cp_num == 936:
                    encoding = "gbk"
                else:
                    encoding = f"cp{cp_num}"
            except ValueError:
                pass
        return EnvironmentInfo(
            platform_type=PlatformType.POWERSHELL_7,
            os_name=os_name,
            os_version=platform.version(),
            python_version=sys.version.split()[0],
            terminal_type="pwsh",
            encoding=encoding,
            home_dir=home_dir,
            working_dir=Path.cwd(),
        )

    def validate_environment(self) -> tuple[bool, list[str]]:
        issues = []
        try:
            result = subprocess.run(
                ["pwsh", "-Command", "$PSVersionTable.PSVersion.Major"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                issues.append("PowerShell 7 is not installed or accessible")
            else:
                try:
                    version_major = int(result.stdout.strip())
                    if version_major < 7:
                        issues.append(
                            f"PowerShell version {version_major} is not supported, requires 7+"
                        )
                except ValueError:
                    issues.append("Could not determine PowerShell version")
        except FileNotFoundError:
            issues.append("PowerShell 7 (pwsh.exe) not found in PATH")
        except subprocess.TimeoutExpired:
            issues.append("PowerShell version check timed out")
        test_encoding_result = self.run_command(
            "[System.Text.Encoding]::UTF8.EncodingName"
        )
        if not test_encoding_result.success:
            issues.append("UTF-8 encoding support verification failed")
        path_test = self.run_command("Test-Path $HOME")
        if not path_test.success:
            issues.append("Cannot access user home directory")
        return len(issues) == 0, issues

    def convert_bash_to_powershell(self, bash_cmd: str) -> str:
        cmd = bash_cmd.strip()
        if not cmd:
            return ""
        base_cmd = cmd.split()[0] if cmd else ""
        full_match = cmd.split(" ", 1)[0] if " " in cmd else cmd
        if full_match in self._command_map:
            remaining = cmd[len(full_match):].strip() if len(cmd) > len(full_match) else ""
            ps_cmd = self._command_map[full_match]
            if remaining:
                return f"{ps_cmd} {remaining}"
            return ps_cmd
        if base_cmd in self._command_map:
            remaining = cmd[len(base_cmd):].strip() if len(cmd) > len(base_cmd) else ""
            ps_cmd = self._command_map[base_cmd]
            if remaining:
                return f"{ps_cmd} {remaining}"
            return ps_cmd
        if "|" in cmd:
            parts = cmd.split("|")
            converted_parts = []
            for part in parts:
                converted_parts.append(self.convert_bash_to_powershell(part.strip()))
            return " | ".join(converted_parts)
        if ">" in cmd and ">>" not in cmd:
            parts = cmd.rsplit(">", 1)
            if len(parts) == 2:
                left = self.convert_bash_to_powershell(parts[0].strip())
                right = self.convert_path(parts[1].strip())
                return f"{left} > {right}"
        if ">>" in cmd:
            parts = cmd.rsplit(">>", 1)
            if len(parts) == 2:
                left = self.convert_bash_to_powershell(parts[0].strip())
                right = self.convert_path(parts[1].strip())
                return f"{left} >> {right}"
        if "&&" in cmd:
            parts = cmd.split("&&")
            converted_parts = []
            for part in parts:
                converted_parts.append(self.convert_bash_to_powershell(part.strip()))
            return "; ".join(converted_parts)
        if "||" in cmd:
            parts = cmd.split("||")
            converted_parts = []
            for part in parts:
                converted_parts.append(self.convert_bash_to_powershell(part.strip()))
            return " ; ".join(converted_parts)
        if cmd.startswith("export "):
            match = re.match(r"export\s+(\w+)=(.+)", cmd)
            if match:
                key, value = match.groups()
                value = value.strip('"').strip("'")
                return f"$env:{key}='{value}'"
        if cmd.startswith("unset "):
            var_name = cmd.replace("unset", "").strip()
            return f"Remove-Item Env:{var_name}"
        if cmd.startswith("alias "):
            match = re.match(r"alias\s+(\w+)=(?:'|\")(.+)(?:'|\")", cmd)
            if match:
                alias_name, alias_cmd = match.groups()
                return f"Set-Alias -Name {alias_name} -Value {alias_cmd}"
        if re.match(r"^\$\w+=.*", cmd):
            match = re.match(r"^(\$\w+)=(.*)", cmd)
            if match:
                var_name, value = match.groups()
                value = value.strip('"').strip("'")
                return f"{var_name} = '{value}'"
        return cmd

    def convert_path(self, path: str | Path) -> Path:
        path_str = str(path)
        if not path_str:
            return Path(".")
        path_str = path_str.replace("/", "\\")
        if "~" in path_str:
            path_str = path_str.replace("~", str(Path.home()))
        if re.match(r"^/[a-zA-Z]/", path_str):
            drive_letter = path_str[1].upper()
            path_str = f"{drive_letter}:{path_str[2:]}"
        if re.match(r"^//|\\\\", path_str):
            path_str = path_str.replace("/", "\\")
        try:
            normalized = Path(path_str).resolve()
            return normalized
        except Exception:
            return Path(path_str)

    def ensure_utf8_no_bom(self, content: str, output_path: Path) -> bool:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            ps_script = f"""
            $content = @'
{content}
'@
            [System.IO.File]::WriteAllText('{output_path}', $content, (New-Object System.Text.UTF8Encoding $false))
            """
            result = self.run_command(ps_script)
            return result.success
        except Exception as e:
            try:
                with open(output_path, "w", encoding="utf-8-sig") as f:
                    f.write(content)
                bom_bytes = b"\xef\xbb\xbf"
                with open(output_path, "rb") as f:
                    current_content = f.read()
                if current_content[:3] == bom_bytes:
                    with open(output_path, "wb") as f:
                        f.write(current_content[3:])
                return True
            except Exception as inner_e:
                print(f"Failed to write UTF-8 NoBOM file: {inner_e}")
                return False

    def get_session_pool(self) -> PowerShellSessionPool:
        return self._session_pool

    def _parse_output_objects(self, output: str) -> list[dict] | None:
        try:
            lines = output.strip().split("\n")
            objects = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("PS"):
                    continue
                if ":" in line and not line.startswith("-"):
                    obj = {}
                    pairs = re.findall(r"(\w[\w\s]*?)\s*:\s*(.+)", line)
                    for key, value in pairs:
                        obj[key.strip()] = value.strip()
                    if obj:
                        objects.append(obj)
            return objects if objects else None
        except Exception:
            return None

    def _extract_warnings(self, stderr: str) -> list[str] | None:
        patterns = [
            r"WARNING\s*:\s*(.+)",
            r"WARN\s*:\s*(.+)",
            r"警告\s*:\s*(.+)",
        ]
        warnings = []
        for pattern in patterns:
            matches = re.findall(pattern, stderr, re.IGNORECASE)
            warnings.extend(matches)
        return warnings if warnings else None

    def __del__(self):
        try:
            self._session_pool.cleanup_all()
        except Exception:
            pass
