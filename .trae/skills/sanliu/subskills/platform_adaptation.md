# PowerShell 7 平台适配层 (Platform Adaptation)

## 概述

PowerShell 7 平台适配层是 Sanliu v4.0 的跨平台基础设施，专门解决 Windows 用户在使用 Trae IDE 时的 PowerShell 7 原生支持问题。该系统通过环境检测、命令适配、编码保证和 PS7 工作流等子系统，确保 Sanliu 在 Windows/PowerShell 7 环境下能够与 Linux/Bash 环境具有同等的使用体验。

### 核心理念

- **PS7原生**: 充分利用 PowerShell 7 的现代特性和跨平台能力
- **自动适配**: 自动检测环境并适配命令语法
- **编码保证**: 强制 UTF-8 No BOM 编码，避免乱码问题
- **双向兼容**: 同时支持 Bash 和 PS7 命令风格
- **对象管道**: 利用 PS7 的结构化对象管道进行高级操作

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                PowerShell 7 平台适配层架构                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           环境检测器 (Environment Detector)               │  │
│  │  ├─ 操作系统检测 (Windows/Linux/macOS)                   │  │
│  │  ├─ Shell类型检测 (PS7/Bash/Zsh)                         │  │
│  │  ├─ 版本信息获取                                         │  │
│  │  ├─ 特性可用性检查                                       │  │
│  │  └─ 环境变量解析                                         │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            命令适配器 (Command Adapter)                    │  │
│  │  ├─ Bash → PS7 转换 (20个常用命令)                       │  │
│  │  ├─ 参数格式转换                                          │  │
│  │  ├─ 路径格式转换 (Unix → Windows)                        │  │
│  │  ├─ 管道操作转换                                          │  │
│  │  └─ 环境变量语法转换                                      │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │          编码保证器 (Encoding Validator)                  │  │
│  │  ├─ UTF-8 No BOM 检测                                    │  │
│  │  ├─ BOM 检测与移除                                       │  │
│  │  ├─ 编码推断 (ASCII → UTF-8 → GBK → Latin1)             │  │
│  │  ├─ 编码转换与修复                                        │  │
│  │  └─ 换行符统一 (LF/CRLF)                                 │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │         跨平台文件操作 (Cross-Platform File Ops)           │  │
│  │  ├─ list_files: 列出目录                                  │  │
│  │  ├─ read_file: 读取文件                                   │  │
│  │  ├─ write_file: 写入文件                                  │  │
│  │  ├─ copy_file: 复制文件                                   │  │
│  │  ├─ move_file: 移动/重命名                                │  │
│  │  ├─ delete_file: 删除文件                                 │  │
│  │  └─ get_env_var: 获取环境变量                             │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │        PS7 工作流示例 (DevOps Workflow)                    │  │
│  │  ├─ Stage 1: 环境检查                                     │  │
│  │  ├─ Stage 2: 项目初始化                                   │  │
│  │  ├─ Stage 3: SDD/TDD 执行                                │  │
│  │  ├─ Stage 4: 测试运行                                     │  │
│  │  ├─ Stage 5: 质量检查                                     │  │
│  │  ├─ Stage 6: 决策日志生成                                 │  │
│  │  └─ Stage 7: MARC状态查看                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 环境检测器

### 功能概述

环境检测器负责检测当前运行环境的详细信息，包括操作系统、Shell类型、版本号和可用特性。

### 支持的环境类型

| 环境 | Shell | 说明 |
|------|-------|------|
| Windows + PS7 | PowerShell 7+ | 主要目标环境 |
| Windows + Bash | Git Bash / WSL | 备选环境 |
| Linux + Bash | Bash 4+ | Linux默认环境 |
| macOS + Zsh | Zsh 5+ | macOS默认环境 |

### 核心方法

#### detect_environment() 方法

```python
class PlatformAdapter:
    def detect_environment(self) -> EnvironmentInfo:
        """
        检测当前运行环境

        Returns:
            EnvironmentInfo: 环境信息
        """
        import platform
        import subprocess
        import os

        info = EnvironmentInfo()

        # 1. 操作系统检测
        info.os_type = platform.system()  # Windows, Linux, Darwin
        info.os_version = platform.version()
        info.os_release = platform.release()
        info.architecture = platform.machine()

        # 2. Shell类型检测
        shell = os.environ.get('SHELL', '') or os.environ.get('COMSPEC', '')

        if 'powershell' in shell.lower() or 'pwsh' in shell.lower():
            info.shell_type = 'powershell'
            # 获取PS版本
            try:
                result = subprocess.run(
                    ['pwsh', '-Command', '$PSVersionTable.PSVersion.ToString()'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                info.shell_version = result.stdout.strip()
            except Exception:
                info.shell_version = 'unknown'
        elif 'bash' in shell.lower():
            info.shell_type = 'bash'
            try:
                result = subprocess.run(
                    ['bash', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                info.shell_version = result.stdout.split('\n')[0].split()[3]
            except Exception:
                info.shell_version = 'unknown'
        elif 'zsh' in shell.lower():
            info.shell_type = 'zsh'
            info.shell_version = os.environ.get('ZSH_VERSION', 'unknown')
        else:
            info.shell_type = 'unknown'

        # 3. 特性可用性检查
        info.features = self._check_features(info)

        return info

    def _check_features(self, env_info: EnvironmentInfo) -> dict:
        """检查特性可用性"""
        features = {}

        # PS7特性
        if env_info.shell_type == 'powershell':
            features['parallel_execution'] = True
            features['error_handling'] = True
            features['structured_pipeline'] = True
            features['remoting'] = self._check_ps_remoting()
            features['dsc_support'] = self._check_dsc_support()
        else:
            features['parallel_execution'] = False
            features['error_handling'] = False
            features['structured_pipeline'] = False
            features['remoting'] = False
            features['dsc_support'] = False

        # 通用特性
        features['utf8_support'] = self._check_utf8_support()
        features['symlink_support'] = self._check_symlink_support()
        features['long_path_support'] = self._check_long_path_support()

        return features
```

## 命令适配器

### 功能概述

命令适配器将 Bash 命令转换为等效的 PowerShell 7 命令，确保脚本在两种环境下都能正常运行。

### 命令映射表 (20个常用命令)

| # | Bash | PowerShell 7 | 说明 |
|---|------|-------------|------|
| 1 | `ls` | `Get-ChildItem` | 列出目录内容 |
| 2 | `cd` | `Set-Location` | 切换工作目录 |
| 3 | `cp` | `Copy-Item` | 复制文件或目录 |
| 4 | `rm` | `Remove-Item` | 删除文件或目录 |
| 5 | `mkdir` | `New-Item -ItemType Directory` | 创建目录 |
| 6 | `cat` | `Get-Content` | 显示文件内容 |
| 7 | `grep` | `Select-String` | 搜索文本模式 |
| 8 | `find` | `Get-ChildItem -Recurse` | 递归查找文件 |
| 9 | `chmod` | `Set-Acl` | 修改权限 |
| 10 | `touch` | `New-Item` | 创建空文件 |
| 11 | `which` | `Get-Command` | 查找命令位置 |
| 12 | `export VAR=val` | `$env:VAR="value"` | 设置环境变量 |
| 13 | `echo` | `Write-Output` | 输出文本 |
| 14 | `pwd` | `Get-Location` | 显示当前目录 |
| 15 | `mv` | `Move-Item` | 移动或重命名 |
| 16 | `head/tail` | `Select-Object -First/Last` | 首尾行选择 |
| 17 | `wc -l` | `(Get-Content).Count` | 行数统计 |
| 18 | `history` | `Get-History` | 命令历史 |
| 19 | `man` | `Get-Help` | 帮助文档 |
| 20 | `ps aux` | `Get-Process` | 进程列表 |

### 核心方法

#### adapt_command() 方法

```python
class PlatformAdapter:
    COMMAND_MAPPINGS = {
        'ls': ('Get-ChildItem', None),
        'cd': ('Set-Location', None),
        'cp': ('Copy-Item', None),
        'rm': ('Remove-Item', {'-rf': '-Recurse -Force'}),
        'mkdir': ('New-Item', {'-ItemType': 'Directory'}),
        'cat': ('Get-Content', None),
        'grep': ('Select-String', None),
        'find': ('Get-ChildItem', {'-name': '-Filter'}),
        'touch': ('New-Item', None),
        'which': ('Get-Command', None),
        'echo': ('Write-Output', None),
        'pwd': ('Get-Location', None),
        'mv': ('Move-Item', None),
        'head': ('Select-Object', {'-n': '-First'}),
        'tail': ('Select-Object', {'-n': '-Last'}),
        'wc': ('(Get-Object)', {'-l': '.Count'}),
    }

    ENV_VAR_PATTERN = re.compile(r'export\s+(\w+)\s*=\s*["\']?([^"\']*)["\']?')

    def adapt_command(
        self,
        command: str,
        target_shell: str = 'powershell',
        source_shell: str = 'bash'
    ) -> str:
        """
        适配命令到目标Shell

        Args:
            command: 原始命令
            target_shell: 目标Shell (powershell/bash)
            source_shell: 源Shell (bash/powershell)

        Returns:
            str: 适配后的命令
        """
        if target_shell == source_shell:
            return command

        if target_shell == 'powershell':
            return self._bash_to_powershell(command)
        else:
            return self._powershell_to_bash(command)

    def _bash_to_powershell(self, bash_cmd: str) -> str:
        """将Bash命令转换为PowerShell"""
        ps_cmd = bash_cmd

        # 1. 替换简单命令
        parts = bash_cmd.strip().split()
        if parts and parts[0] in self.COMMAND_MAPPINGS:
            ps_cmd_name, param_mapping = self.COMMAND_MAPPINGS[parts[0]]
            new_parts = [ps_cmd_name]

            for part in parts[1:]:
                if param_mapping and part in param_mapping:
                    new_parts.append(param_mapping[part])
                elif part.startswith('-'):
                    new_parts.append(part.replace('-', '-', 1))  # 保持参数
                else:
                    new_parts.append(part)

            ps_cmd = ' '.join(new_parts)

        # 2. 转换环境变量设置
        match = self.ENV_VAR_PATTERN.match(bash_cmd)
        if match:
            var_name = match.group(1)
            var_value = match.group(2)
            ps_cmd = f'$env:{var_name}="{var_value}"'

        # 3. 转换路径格式
        if '/' in ps_cmd and not ps_cmd.startswith('$') and not ps_cmd.startswith('"'):
            ps_cmd = self._convert_unix_path_to_windows(ps_cmd)

        return ps_cmd

    def _convert_unix_path_to_windows(self, path_str: str) -> str:
        """将Unix路径转换为Windows路径"""
        # 转换 /c/path 格式为 C:\path
        if re.match(r'^/[a-z]/', path_str):
            drive = path_str[1].upper()
            rest = path_str[2:].replace('/', '\\')
            return f'{drive}:{rest}'
        return path_str
```

#### adapt_script() 方法

```python
class PlatformAdapter:
    def adapt_script(
        self,
        script_content: str,
        source_format: str = 'bash',
        target_format: str = 'powershell'
    ) -> str:
        """
        适配整个脚本

        Args:
            script_content: 脚本内容
            source_format: 源格式 (bash/powershell)
            target_format: 目标格式 (powershell/bash)

        Returns:
            str: 适配后的脚本
        """
        if source_format == target_format:
            return script_content

        lines = script_content.split('\n')
        adapted_lines = []

        for line in lines:
            stripped = line.strip()

            # 跳过注释
            if stripped.startswith('#'):
                adapted_lines.append(line)
                continue

            # 跳过空行
            if not stripped:
                adapted_lines.append(line)
                continue

            # 适配命令
            adapted_line = self.adapt_command(stripped, target_format, source_format)

            # 保持缩进
            indent = len(line) - len(line.lstrip())
            adapted_lines.append(' ' * indent + adapted_line)

        return '\n'.join(adapted_lines)
```

## 编码保证器

### 功能概述

编码保证器确保所有文件使用正确的编码格式（UTF-8 No BOM），并处理各种编码相关的异常情况。

### BOM 检测

```python
class PlatformAdapter:
    BOM_MARKERS = {
        'utf-8-sig': b'\xef\xbb\xbf',       # UTF-8 BOM
        'utf-16-le': b'\xff\xfe',             # UTF-16 LE BOM
        'utf-16-be': b'\xfe\xff',             # UTF-16 BE BOM
        'utf-32-le': b'\xff\xfe\x00\x00',     # UTF-32 LE BOM
        'utf-32-be': b'\x00\x00\xfe\xff',     # UTF-32 BE BOM
    }

    def detect_bom(self, file_path: Path) -> Optional[str]:
        """
        检测文件的BOM标记

        Args:
            file_path: 文件路径

        Returns:
            Optional[str]: 编码类型，如果没有BOM返回None
        """
        with open(file_path, 'rb') as f:
            raw = f.read(4)

        for encoding, marker in self.BOM_MARKERS.items():
            if raw.startswith(marker):
                return encoding

        return None

    def has_bom(self, file_path: Path) -> bool:
        """检查文件是否有BOM"""
        return self.detect_bom(file_path) is not None
```

### 编码推断

```python
class PlatformAdapter:
    def infer_encoding(self, file_path: Path) -> str:
        """
        推断文件编码

        推断顺序: ASCII → UTF-8 → GBK → Latin1

        Args:
            file_path: 文件路径

        Returns:
            str: 推断的编码名称
        """
        with open(file_path, 'rb') as f:
            raw = f.read()

        # 1. 检查BOM
        bom_encoding = self.detect_bom(file_path)
        if bom_encoding:
            return 'utf-8-sig' if bom_encoding == 'utf-8-sig' else bom_encoding

        # 2. 尝试UTF-8解码
        try:
            raw.decode('utf-8')
            return 'utf-8'
        except UnicodeDecodeError:
            pass

        # 3. 尝试GBK解码（中文常见）
        try:
            raw.decode('gbk')
            return 'gbk'
        except UnicodeDecodeError:
            pass

        # 4. 回退到Latin1
        return 'latin1'
```

### 编码验证与修复

```python
class PlatformAdapter:
    def ensure_encoding(
        self,
        file_path: Path,
        target_encoding: str = 'utf-8',
        remove_bom: bool = True,
        line_ending: str = 'lf'
    ) -> EncodingResult:
        """
        确保文件使用正确的编码

        Args:
            file_path: 文件路径
            target_encoding: 目标编码
            remove_bom: 是否移除BOM
            line_ending: 换行符类型 (lf/crlf/auto)

        Returns:
            EncodingResult: 编码处理结果
        """
        result = EncodingResult(file_path=str(file_path))

        # 读取原始内容
        original_encoding = self.infer_encoding(file_path)
        result.original_encoding = original_encoding

        with open(file_path, 'r', encoding=original_encoding) as f:
            content = f.read()

        # 检查是否需要修改
        needs_modification = False

        # 1. 检查BOM
        if remove_bom and self.has_bom(file_path):
            result.had_bom = True
            needs_modification = True

        # 2. 检查编码
        if original_encoding != target_encoding and original_encoding != f'{target_encoding}-sig':
            result.encoding_changed = True
            needs_modification = True

        # 3. 检查换行符
        current_le = self._detect_line_ending(content)
        target_le = '\r\n' if line_ending == 'crlf' else '\n'

        if line_ending == 'lf' and current_le == 'crlf':
            result.line_ending_changed = True
            content = content.replace('\r\n', '\n')
            needs_modification = True
        elif line_ending == 'crlf' and current_le == 'lf':
            result.line_ending_changed = True
            content = content.replace('\n', '\r\n')
            needs_modification = True

        # 写回文件（如果需要修改）
        if needs_modification:
            with open(file_path, 'w', encoding=target_encoding, newline='') as f:
                f.write(content)

            result.modified = True
            result.final_encoding = target_encoding
        else:
            result.modified = False
            result.final_encoding = original_encoding

        return result

    def validate_project_encoding(
        self,
        project_path: Path,
        extensions: List[str] = None
    ) -> ProjectEncodingReport:
        """
        验证项目编码

        Args:
            project_path: 项目根路径
            extensions: 要检查的扩展名列表

        Returns:
            ProjectEncodingReport: 项目编码报告
        """
        if extensions is None:
            extensions = ['.py', '.md', '.yaml', '.yml', '.json', '.ts', '.vue']

        report = ProjectEncodingReport(project_path=str(project_path))
        issues = []

        for ext in extensions:
            for file_path in project_path.rglob(f'*{ext}'):
                encoding_result = self.ensure_encoding(file_path)
                report.files_checked += 1

                if encoding_result.modified or encoding_result.had_bom:
                    issues.append({
                        'file': str(file_path),
                        'original_encoding': encoding_result.original_encoding,
                        'had_bom': encoding_result.had_bom,
                        'encoding_changed': encoding_result.encoding_changed,
                        'line_ending_changed': encoding_result.line_ending_changed
                    })

        report.issues = issues
        report.total_issues = len(issues)

        return report
```

## 跨平台文件操作

### 功能概述

提供统一的跨平台文件操作接口，自动处理不同操作系统下的差异。

### 核心方法

```python
class PlatformAdapter:
    def list_files(
        self,
        directory: str,
        pattern: str = '*',
        recursive: bool = False
    ) -> List[str]:
        """
        列出目录中的文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归

        Returns:
            List[str]: 文件路径列表
        """
        dir_path = Path(directory)

        if recursive:
            files = [str(f) for f in dir_path.rglob(pattern) if f.is_file()]
        else:
            files = [str(f) for f in dir_path.glob(pattern) if f.is_file()]

        return sorted(files)

    def read_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """读取文件内容"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        inferred_encoding = self.infer_encoding(path)
        actual_encoding = encoding if encoding != 'auto' else inferred_encoding

        with open(path, 'r', encoding=actual_encoding) as f:
            return f.read()

    def write_file(
        self,
        file_path: str,
        content: str,
        encoding: str = 'utf-8',
        create_dirs: bool = True
    ):
        """写入文件"""
        path = Path(file_path)

        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding=encoding, newline='') as f:
            f.write(content)

    def copy_file(self, src: str, dst: str, overwrite: bool = False):
        """复制文件"""
        src_path = Path(src)
        dst_path = Path(dst)

        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {src}")

        if dst_path.exists() and not overwrite:
            raise FileExistsError(f"Destination already exists: {dst}")

        import shutil
        shutil.copy2(src_path, dst_path)

    def delete_file(self, file_path: str, missing_ok: bool = False):
        """删除文件"""
        path = Path(file_path)

        if not path.exists():
            if missing_ok:
                return
            raise FileNotFoundError(f"File not found: {file_path}")

        path.unlink()

    def get_env_var(self, name: str, default: str = None) -> str:
        """获取环境变量"""
        value = os.environ.get(name, default)
        return value

    def set_env_var(self, name: str, value: str, permanent: bool = False):
        """设置环境变量"""
        os.environ[name] = value

        if permanent:
            # Windows永久设置
            if sys.platform == 'win32':
                import subprocess
                subprocess.run(['setx', name, value], capture_output=True)
            else:
                # Unix永久设置
                shell_rc = Path.home() / '.bashrc'
                if not shell_rc.exists():
                    shell_rc = Path.home() / '.zshrc'
                with open(shell_rc, 'a') as f:
                    f.write(f'\nexport {name}="{value}"\n')
```

## PS7 工作流示例

### 功能概述

提供完整的 PowerShell 7 DevOps 工作流示例，展示如何在 PS7 环境下执行完整的开发流程。

### 工作流阶段 (7个Stage)

```powershell
# workflows/devops_workflow.ps1 - PowerShell 7 DevOps 工作流

# 定义工作流阶段枚举
enum WorkflowStage {
    EnvironmentCheck      # Stage 1: 环境检查
    ProjectInit           # Stage 2: 项目初始化
    SDDTDDExecution       # Stage 3: SDD/TDD 执行
    TestRunner            # Stage 4: 测试运行
    QualityCheck          # Stage 5: 质量检查
    DecisionLogGeneration # Stage 6: 决策日志生成
    MARCStatusView        # Stage 7: MARC状态查看
}

# 结构化日志函数
function Write-WorkflowLog {
    param(
        [string]$Message,
        [WorkflowStage]$Stage,
        [string]$Level = "INFO"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] [Stage:$Stage] $Message"
    Write-Host $logEntry -ForegroundColor $(switch ($Level) {
        "ERROR" { "Red" }
        "WARN"  { "Yellow" }
        "INFO"  { "Green" }
        "DEBUG" { "Gray" }
        default { "White" }
    })

    # 同时输出到日志文件
    $logEntry | Out-File -Append -FilePath "logs/workflow.log"
}

# Stage 1: 环境检查
function Invoke-EnvironmentCheck {
    Write-WorkflowLog -Message "开始环境检查..." -Stage EnvironmentCheck

    # 检查PowerShell版本
    $psVersion = $PSVersionTable.PSVersion.ToString()
    Write-WorkflowLog -Message "PowerShell版本: $psVersion" -Stage EnvironmentCheck

    if ([version]$psVersion -lt [version]"7.0") {
        Write-WorkflowLog -Message "需要PowerShell 7.0+" -Stage EnvironmentCheck -Level ERROR
        throw "不支持的PowerShell版本"
    }

    # 检查Python
    $pythonVersion = python --version 2>&1
    Write-WorkflowLog -Message "Python版本: $pythonVersion" -Stage EnvironmentCheck

    # 检查Node.js (如需要)
    if (Test-Path package.json) {
        $nodeVersion = node --version 2>&1
        Write-WorkflowLog -Message "Node.js版本: $nodeVersion" -Stage EnvironmentCheck
    }

    # 检查Git
    $gitVersion = git --version 2>&1
    Write-WorkflowLog -Message "Git版本: $gitVersion" -Stage EnvironmentCheck

    Write-WorkflowLog -Message "环境检查完成 ✓" -Stage EnvironmentCheck
}

# Stage 2: 项目初始化
function Invoke-ProjectInit {
    Write-WorkflowLog -Message "开始项目初始化..." -Stage ProjectInit

    # 安装依赖
    if (Test-Path requirements.txt) {
        Write-WorkflowLog -Message "安装Python依赖..." -Stage ProjectInit
        pip install -r requirements.txt
    }

    if (Test-Path package.json) {
        Write-WorkflowLog -Message "安装Node.js依赖..." -Stage ProjectInit
        npm install
    }

    # 初始化子模块
    if (Test-Path .gitmodules) {
        Write-WorkflowLog -Message "初始化Git子模块..." -Stage ProjectInit
        git submodule update --init --recursive
    }

    Write-WorkflowLog -Message "项目初始化完成 ✓" -Stage ProjectInit
}

# Stage 3: SDD/TDD 执行
function Invoke-SDDTDDExecution {
    param([string]$TaskDescription)

    Write-WorkflowLog -Message "开始SDD/TDD执行..." -Stage SDDTDDExecution
    Write-WorkflowLog -Message "任务描述: $TaskDescription" -Stage SDDTDDExecution

    # 运行Sanliu技能
    $sanliuOutput = python -m sanliu.skillscripts.sdd_tdd_engine --task $TaskDescription 2>&1
    Write-WorkflowLog -Message "SDD/TDD引擎输出:" -Stage SDDTDDExecution
    $sanliuOutput | ForEach-Object { Write-WorkflowLog -Message $_ -Stage SDDTDDExecution }

    Write-WorkflowLog -Message "SDD/TDD执行完成 ✓" -Stage SDDTDDExecution
}

# Stage 4: 测试运行
function Invoke-TestRunner {
    param([string]$TestType = "all")

    Write-WorkflowLog -Message "开始测试运行..." -Stage TestRunner

    switch ($TestType) {
        "unit" {
            Write-WorkflowLog -Message "运行单元测试..." -Stage TestRunner
            pytest tests/unit/ -v
        }
        "integration" {
            Write-WorkflowLog -Message "运行集成测试..." -Stage TestRunner
            pytest tests/integration/ -v
        }
        "all" {
            Write-WorkflowLog -Message "运行全部测试..." -Stage TestRunner
            pytest -v --cov=src --cov-report=html
        }
        default {
            Write-WorkflowLog -Message "未知测试类型: $TestType" -Stage TestRunner -Level WARN
        }
    }

    Write-WorkflowLog -Message "测试运行完成 ✓" -Stage TestRunner
}

# Stage 5: 质量检查
function Invoke-QualityCheck {
    Write-WorkflowLog -Message "开始质量检查..." -Stage QualityCheck

    # Lint检查
    Write-WorkflowLog -Message "运行Lint检查..." -Stage QualityCheck
    pylint src/ --output-format=text

    # 安全扫描
    Write-WorkflowLog -Message "运行安全扫描..." -Stage QualityCheck
    bandit -r src/ -f json -o reports/security/bandit.json

    # 类型检查
    Write-WorkflowLog -Message "运行类型检查..." -Stage QualityCheck
    mypy src/

    # 硬编码检测
    Write-WorkflowLog -Message "运行硬编码检测..." -Stage QualityCheck
    python -m sanliu.skillscripts.security.hardcoded_detector . --output reports/security/hardcoded.md

    Write-WorkflowLog -Message "质量检查完成 ✓" -Stage QualityCheck
}

# Stage 6: 决策日志生成
function Invoke-DecisionLogGeneration {
    param([string]$DecisionTitle, [string]$DecisionContext)

    Write-WorkflowLog -Message "生成决策日志..." -Stage DecisionLogGeneration

    $decisionId = python -c "
from sanliu.skillscripts.core.decision_log import DecisionLog
dl = DecisionLog()
result = dl.generate(
    title='$DecisionTitle',
    context=$($DecisionContext | ConvertToTo-Json)
)
print(result.decision_id)
"

    Write-WorkflowLog -Message "决策ID: $decisionId" -Stage DecisionLogGeneration
    Write-WorkflowLog -Message "决策日志生成完成 ✓" -Stage DecisionLogGeneration
}

# Stage 7: MARC状态查看
function Invoke-MARCStatusView {
    Write-WorkflowLog -Message "查看MARC资源协调状态..." -Stage MARCStatusView

    $marcStatus = python -m sanliu.skillscripts.core.resource_coordinator --status 2>&1

    # 解析并显示MARC仪表板
    Write-Host "`n==========================================" -ForegroundColor Cyan
    Write-Host "     MARC-Lite 资源协调系统状态" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan

    $marcStatus | ForEach-Object {
        if ($_ -match "(总资源|可用|锁定|任务)") {
            Write-Host $_ -ForegroundColor Green
        } elseif ($_ -match "(告警|警告|错误)") {
            Write-Host $_ -ForegroundColor Red
        } elseif ($_ -match "(🟢|🟡|🔴)") {
            Write-Host $_
        } else {
            Write-Host $_
        }
    }

    Write-WorkflowLog -Message "MARC状态查看完成 ✓" -Stage MARCStatusView
}
```

## 使用示例

### 示例1: 环境检测

```python
from platform_adapter import PlatformAdapter

adapter = PlatformAdapter()

# 检测环境
env_info = adapter.detect_environment()

print(f"=== 环境信息 ===")
print(f"操作系统: {env_info.os_type} {env_info.os_version}")
print(f"Shell: {env_info.shell_type} {env_info.shell_version}")
print(f"架构: {env_info.architecture}")
print(f"可用特性:")
for feature, available in env_info.features.items():
    status = "✅" if available else "❌"
    print(f"  {status} {feature}")
```

### 示例2: 命令适配

```python
# Bash命令转换为PS7
adapter = PlatformAdapter()

bash_commands = [
    'ls -la',
    'cp file1.txt file2.txt',
    'rm -rf build/',
    'mkdir -p src/components',
    'export API_KEY="secret123"',
    'cat config.yaml',
    'grep "TODO" *.py',
    'wc -l main.py'
]

for cmd in bash_commands:
    ps_cmd = adapter.adapt_command(cmd, target_shell='powershell')
    print(f"Bash: {cmd}")
    print(f"PS7:   {ps_cmd}")
    print()
```

### 示例3: 编码保证

```python
# 验证并修复项目编码
adapter = PlatformAdapter()

report = adapter.validate_project_encoding(Path('.'))

print(f"=== 项目编码报告 ===")
print(f"检查文件数: {report.files_checked}")
print(f"发现问题数: {report.total_issues}")

if report.issues:
    print("\n已修复的问题:")
    for issue in report.issues[:10]:
        print(f"  📄 {issue['file']}")
        if issue['had_bom']:
            print(f"     - 已移除BOM")
        if issue['encoding_changed']:
            print(f"     - 编码: {issue['original_encoding']} → utf-8")
        if issue['line_ending_changed']:
            print(f"     - 换行符已统一")
else:
    print("✅ 所有文件编码正确")
```

### 示例4: 跨平台文件操作

```python
# 统一的文件操作接口
adapter = PlatformAdapter()

# 列出文件
files = adapter.list_files('./src', pattern='*.py', recursive=True)
print(f"找到 {len(files)} 个Python文件")

# 读取文件
content = adapter.read_file('./src/main.py')
print(f"文件内容长度: {len(content)} 字符")

# 写入文件
adapter.write_file('./src/new_module.py', '# New module\n\ndef hello():\n    pass\n')

# 复制文件
adapter.copy_file('./src/main.py', './backup/main.py.bak')

# 获取环境变量
api_key = adapter.get_env_var('API_KEY', default='default_key')
print(f"API Key: {api_key[:10]}...")
```

### 示例5: 运行PS7工作流

```powershell
# 在PowerShell中运行完整工作流
.\workflows\devops_workflow.ps1

# 或分步执行
Invoke-EnvironmentCheck
Invoke-ProjectInit
Invoke-SDDTDDExecution -TaskDescription "实现用户认证模块"
Invoke-TestRunner -TestType all
Invoke-QualityCheck
Invoke-DecisionLogGeneration -DecisionTitle "采用OAuth2.0认证方案" -DecisionContext '{"options":["JWT","Session","OAuth"],"selected":"OAuth","reason":"更好的安全性"}'
Invoke-MARCStatusView
```

## 配置参数

```yaml
platform_adapter:
  # 环境检测配置
  environment_detection:
    cache_enabled: true
    cache_ttl: 300  # 5分钟缓存

  # 命令适配配置
  command_adaptation:
    mappings_file: "config/command_mappings.yaml"
    custom_mappings: {}
    strict_mode: false  # 严格模式下未识别的命令会报错

  # 编码配置
  encoding:
    default_encoding: "utf-8"
    enforce_no_bom: true  # 强制无BOM
    default_line_ending: "lf"  # 默认换行符
    ps1_allow_bom: true  # .ps1文件允许BOM
    auto_fix: true  # 自动修复编码问题

  # 文件操作配置
  file_operations:
    buffer_size: 8192
    max_file_size_mb: 100
    create_backup_before_write: false

  # 工作流配置
  workflow:
    log_dir: "logs"
    log_level: "INFO"
    stages:
      - environment_check
      - project_init
      - sdd_tdd_execution
      - test_runner
      - quality_check
      - decision_log_generation
      - marc_status_view
```

## 最佳实践

### 1. 始终使用PlatformAdapter进行文件操作

不要直接使用os.path或其他平台相关API，使用PlatformAdapter的统一接口。

```python
# 推荐
from platform_adapter import PlatformAdapter
adapter = PlatformAdapter()
files = adapter.list_files('./src', '*.py')

# 不推荐
import os
files = [f for f in os.listdir('./src') if f.endswith('.py')]
```

### 2. 在CI/CD中添加编码检查

在CI/CD流程中添加编码验证步骤，确保所有文件都符合编码规范。

```yaml
# .github/workflows/encoding.yml
name: Encoding Check

on: [push, pull_request]

jobs:
  check-encoding:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run Encoding Validation
        run: |
          python -c "
          from pathlib import Path
          from platform_adapter import PlatformAdapter
          adapter = PlatformAdapter()
          report = adapter.validate_project_encoding(Path('.'))
          if report.total_issues > 0:
              print(f'Found {report.total_issues} encoding issues!')
              exit(1)
          else:
              print('All files have correct encoding.')
          "
```

### 3. 利用PS7的高级特性

充分利用PowerShell 7的对象管道、并行处理和错误处理能力。

```powershell
# 并行处理文件
$files = Get-ChildItem -Path . -Filter "*.py" -Recurse

$results = $files | ForEach-Object -Parallel {
    $content = Get-Content $_.FullName -Raw
    $lineCount = ($content -split "`n").Count
    [PSCustomObject]@{
        File = $_.FullName
        Lines = $lineCount
    }
} -ThrottleLimit 4

$results | Sort-Object Lines -Descending | Select-Object -First 10
```

### 4. 处理长路径问题

Windows有260字符的路径限制，需要特殊处理超长路径。

```python
import os

def handle_long_path(path: str) -> str:
    """处理Windows长路径"""
    if os.name == 'nt' and len(path) > 200:
        # 使用UNC前缀
        return '\\\\?\\' + os.path.abspath(path)
    return path
```

### 5. 定期同步命令映射

当发现新的命令需要适配时，更新命令映射表。

```python
# 添加自定义命令映射
adapter = PlatformAdapter()
adapter.add_custom_mapping('docker-compose', 'docker-compose', {})
adapter.add_custom_mapping('npm test', 'npm test', {})  # 无需转换
```

## 与其他模块的集成

### 与四维防线的集成

四维防线可以使用PlatformAdapter确保输入输出文件的编码正确。

```python
from four_d_defense import FourDimensionalDefense
from platform_adapter import PlatformAdapter

defense = FourDimensionalDefense()
adapter = PlatformAdapter()

# 确保输入文件编码正确
input_data.content = adapter.read_file(input_data.metadata['file_path'])

# 执行检查
result = defense.run_full_check(input_data)

# 确保输出文件编码正确
if result.output:
    adapter.write_file(output_path, result.output, encoding='utf-8')
```

### 与资源协调器的集成

资源协调器可以使用PlatformAdapter进行跨平台的锁文件管理。

```python
from resource_coordinator import ResourceCoordinator
from platform_adapter import PlatformAdapter

coordinator = ResourceCoordinator()
adapter = PlatformAdapter()

# 使用跨平台路径
lock_file_path = adapter.convert_path('.marc/locks/resource.lock')
coordinator.set_lock_file_path(lock_file_path)
```

## 故障排查

### 问题1: 命令转换失败

**症状**: Bash命令无法正确转换为PS7命令。

**排查步骤**:
1. 检查命令是否在映射表中
2. 检查参数格式是否正确
3. 查看转换日志

**解决方案**:
```python
# 启用调试模式
adapter = PlatformAdapter(debug_mode=True)
ps_cmd = adapter.adapt_command('ls -la', target_shell='powershell')
print(ps_cmd)  # 应该输出: Get-ChildItem -Force

# 添加自定义映射
adapter.add_custom_mapping('my-custom-cmd', 'My-CustomCmd', {'--flag': '-CustomFlag'})
```

### 问题2: 编码问题

**症状**: 文件出现乱码或BOM问题。

**解决方案**:
```python
# 诊断编码问题
adapter = PlatformAdapter()
info = adapter.detect_file_encoding(Path('problematic_file.py'))
print(f"检测到的编码: {info}")

# 强制修复
result = adapter.ensure_encoding(
    Path('problematic_file.py'),
    target_encoding='utf-8',
    remove_bom=True,
    line_ending='lf'
)
print(f"修复结果: {result}")
```

### 问题3: PS7脚本执行失败

**症状**: PowerShell脚本执行出错。

**排查步骤**:
1. 检查PS7是否安装 (`pwsh --version`)
2. 检查执行策略 (`Get-ExecutionPolicy`)
3. 检查脚本编码 (应为UTF-8-BOM)

**解决方案**:
```powershell
# 设置执行策略
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 以UTF-8-BOM保存.ps1文件
# 或者显式指定编码运行
pwsh -Encoding utf8 -File script.ps1
```

## 总结

PowerShell 7平台适配层是Sanliu v4.0的核心基础设施，通过环境检测、命令适配、编码保证和跨平台文件操作等子系统，确保Sanliu在Windows/PowerShell 7环境下具有与Linux/Bash同等的使用体验。该系统具有以下特点:

- **全面性**: 覆盖环境检测、命令转换、编码保证全流程
- **自动化**: 自动检测和适配，无需手动干预
- **兼容性**: 同时支持Bash和PS7两种命令风格
- **可靠性**: 内置编码验证和修复机制
- **可扩展性**: 易于添加新的命令映射和自定义规则

通过合理配置和使用平台适配层，可以显著提高Sanliu在Windows环境下的稳定性和用户体验。
