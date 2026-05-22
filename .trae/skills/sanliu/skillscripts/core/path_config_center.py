"""
统一路径配置中心 (PathConfigCenter)
=====================================

作为所有脚本的路由配置管理中心，提供：
- 单例模式确保全局唯一实例
- 预定义路径常量（支持环境变量覆盖）
- 路径解析、验证、修复等核心方法
- 版本感知的输出路径生成
- 批量路径操作和硬编码扫描

使用示例:
    >>> from skillscripts.core.path_config_center import PathConfigCenter
    >>> pcc = PathConfigCenter.instance()
    >>> print(pcc.SKILL_ROOT)
    >>> print(pcc.resolve_path('docs/reports'))
    >>> output = pcc.get_output_path('测试报告', 'v3.2.0')
"""

import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class PathConfigCenter:
    """
    统一路径配置中心 - 单例模式

    管理项目中所有路径配置，提供统一的路径解析、验证和生成服务。
    支持环境变量覆盖，便于在不同环境中灵活配置。
    支持延迟加载和缓存机制，提升性能。
    """

    _instance: Optional['PathConfigCenter'] = None
    _initialized: bool = False
    _lazy_cache: Dict[str, Path] = {}

    def __new__(cls) -> 'PathConfigCenter':
        """单例模式实现，确保全局唯一实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        初始化路径配置中心

        使用 _initialized 标志避免重复初始化（单例模式的常见做法）
        """
        if self._initialized:
            return

        self._logger = logging.getLogger(__name__)
        self._setup_logging()

        self._logger.info("初始化 PathConfigCenter...")

        self._skill_root: Optional[Path] = None
        _env_root = os.environ.get('SANLIU_SKILL_ROOT')
        if _env_root:
            self._skill_root = Path(_env_root).resolve()
            self._logger.info(f"从环境变量 SANLIU_SKILL_ROOT 加载根目录: {self._skill_root}")
        else:
            self._detect_skill_root()

        self._initialize_paths()
        self._ensure_directories()

        self._initialized = True
        self._logger.info("PathConfigCenter 初始化完成")

    def _setup_logging(self):
        """配置日志"""
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def _detect_skill_root(self):
        """
        自动检测技能根目录

        基于 __file__ 向上定位到 sanliu/ 目录
        支持开发环境和打包后的环境
        """
        current_file = Path(__file__).resolve()

        possible_roots = [
            current_file.parent.parent,
            current_file.parent.parent.parent,
            current_file,
        ]

        for root in possible_roots:
            if (root / 'SKILL.md').exists() or (root / 'skillscripts').exists():
                self._skill_root = root
                self._logger.info(f"自动检测到根目录: {self._skill_root}")
                return

        self._skill_root = current_file.parent.parent
        self._logger.warning(
            f"无法精确检测根目录，使用默认值: {self._skill_root}"
        )

    def _get_env_path(self, env_var: str, default: Path) -> Path:
        """
        从环境变量获取路径，如果未设置则返回默认值

        Args:
            env_var: 环境变量名称
            default: 默认路径

        Returns:
            解析后的绝对路径
        """
        env_value = os.environ.get(env_var)
        if env_value:
            path = Path(env_value).resolve()
            self._logger.debug(f"环境变量 {env_var} 覆盖: {path}")
            return path
        return default

    def _initialize_paths(self):
        """初始化所有预定义路径常量"""
        if not self._skill_root:
            raise RuntimeError("技能根目录未正确初始化")

        root = self._skill_root

        self.SKILL_ROOT: Path = root
        self.DOCS_DIR: Path = self._get_env_path('SANLIU_DOCS_DIR', root / 'docs')
        self.SCRIPTS_DIR: Path = self._get_env_path('SANLIU_SCRIPTS_DIR', root / 'skillscripts')
        self.SUBSKILLS_DIR: Path = self._get_env_path('SANLIU_SUBSKILLS_DIR', root / 'subskills')
        self.REPORTS_DIR: Path = self._get_env_path('SANLIU_REPORTS_DIR', root / 'docs' / 'reports')
        self.CACHE_DIR: Path = self._get_env_path('SANLIU_CACHE_DIR', root / 'cache')
        self.LOGS_DIR: Path = self._get_env_path('SANLIU_LOGS_DIR', root / 'logs')
        self.VERSIONS_DIR: Path = self._get_env_path('SANLIU_VERSIONS_DIR', root / 'docs' / '迭代版本')
        self.BACKEND_DIR: Path = self._get_env_path('SANLIU_BACKEND_DIR', root / 'backend')
        self.FRONTEND_DIR: Path = self._get_env_path('SANLIU_FRONTEND_DIR', root / 'frontend')
        self.DATA_DIR: Path = self._get_env_path('SANLIU_DATA_DIR', root / 'data')

        self._all_paths: Dict[str, Path] = {
            'SKILL_ROOT': self.SKILL_ROOT,
            'DOCS_DIR': self.DOCS_DIR,
            'SCRIPTS_DIR': self.SCRIPTS_DIR,
            'SUBSKILLS_DIR': self.SUBSKILLS_DIR,
            'REPORTS_DIR': self.REPORTS_DIR,
            'CACHE_DIR': self.CACHE_DIR,
            'LOGS_DIR': self.LOGS_DIR,
            'VERSIONS_DIR': self.VERSIONS_DIR,
            'BACKEND_DIR': self.BACKEND_DIR,
            'FRONTEND_DIR': self.FRONTEND_DIR,
            'DATA_DIR': self.DATA_DIR,
        }

    def _ensure_directories(self):
        """确保关键目录存在，不存在则创建"""
        dirs_to_ensure = [
            self.REPORTS_DIR,
            self.CACHE_DIR,
            self.LOGS_DIR,
            self.VERSIONS_DIR,
            self.DATA_DIR,
        ]

        for dir_path in dirs_to_ensure:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                self._logger.debug(f"确保目录存在: {dir_path}")
            except OSError as e:
                self._logger.error(f"无法创建目录 {dir_path}: {e}")

    @classmethod
    def instance(cls) -> 'PathConfigCenter':
        """
        获取单例实例

        Returns:
            PathConfigCenter 单例实例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """
        重置单例实例（主要用于测试）

        警告：在生产代码中应谨慎使用
        """
        cls._instance = None
        cls._initialized = False

    def resolve_path(self, relative_path: str) -> Path:
        """
        将相对路径转换为绝对路径

        相对于 SKILL_ROOT 进行解析

        Args:
            relative_path: 相对路径字符串

        Returns:
            解析后的绝对 Path 对象

        Raises:
            ValueError: 如果输入路径为空或无效

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> pcc.resolve_path('docs/reports')
            PosixPath('/path/to/sanliu/docs/reports')
        """
        if not relative_path or not isinstance(relative_path, str):
            raise ValueError("相对路径不能为空且必须是字符串")

        try:
            resolved = (self.SKILL_ROOT / relative_path).resolve()
            self._logger.debug(f"路径解析: {relative_path} -> {resolved}")
            return resolved
        except Exception as e:
            self._logger.error(f"路径解析失败 [{relative_path}]: {e}")
            raise

    def get_absolute_path(self, *parts: str) -> Path:
        """
        多段路径拼接并解析为绝对路径

        Args:
            *parts: 路径段，按顺序拼接

        Returns:
            解析后的绝对 Path 对象

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> pcc.get_absolute_path('docs', 'reports', 'test.md')
            PosixPath('/path/to/sanliu/docs/reports/test.md')
        """
        if not parts:
            raise ValueError("至少需要提供一个路径段")

        combined = self.SKILL_ROOT
        for part in parts:
            if part:
                combined = combined / part

        resolved = combined.resolve()
        self._logger.debug(f"多段路径拼接: {'/'.join(parts)} -> {resolved}")
        return resolved

    def get_output_path(
        self,
        category: str,
        version: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Path:
        """
        生成版本感知的输出路径

        Args:
            category: 报告类别，如 "测试报告", "质量报告", "功能分析报告",
                     "路径验证报告", "演化报告"
            version: 版本号，如 "v3.2.0"。默认取当前版本
            filename: 自定义文件名。默认使用 category + ".md"

        Returns:
            完整的输出路径，格式: {VERSIONS_DIR}/{version}/{category}.md

        Raises:
            ValueError: 如果 category 为空

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> pcc.get_output_path('测试报告', 'v3.2.0')
            PosixPath('/path/to/sanliu/docs/迭代版本/v3.2.0/测试报告.md')
        """
        if not category:
            raise ValueError("报告类别不能为空")

        if version is None:
            version = self.get_current_version()

        version_dir = self.VERSIONS_DIR / version

        if filename:
            output_file = filename if filename.endswith('.md') else f"{filename}.md"
        else:
            output_file = f"{category}.md"

        full_path = version_dir / output_file

        self._logger.debug(f"生成输出路径: category={category}, version={version}, path={full_path}")
        return full_path

    def validate_path(self, path: Path) -> Tuple[bool, List[str]]:
        """
        验证路径的存在性和权限

        Args:
            path: 要验证的路径对象

        Returns:
            Tuple[bool, List[str]]: (是否有效, 问题列表)

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> is_valid, issues = pcc.validate_path(pcc.DOCS_DIR)
            >>> print(is_valid, issues)
        """
        issues: List[str] = []

        if not isinstance(path, Path):
            issues.append(f"路径类型错误: 期望 Path，得到 {type(path).__name__}")
            return False, issues

        try:
            path_str = str(path)

            if not path.exists():
                issues.append(f"路径不存在: {path_str}")
                return False, issues

            if path.is_file():
                if not os.access(path_str, os.R_OK):
                    issues.append(f"文件不可读: {path_str}")
                if not os.access(path_str, os.W_OK):
                    issues.append(f"文件不可写: {path_str}")
            elif path.is_dir():
                if not os.access(path_str, os.R_OK | os.X_OK):
                    issues.append(f"目录不可访问: {path_str}")
                if not os.access(path_str, os.W_OK):
                    issues.append(f"目录不可写: {path_str}")

        except Exception as e:
            issues.append(f"验证过程出错: {str(e)}")
            return False, issues

        is_valid = len(issues) == 0
        if not is_valid:
            self._logger.warning(f"路径验证失败 [{path}]: {issues}")
        else:
            self._logger.debug(f"路径验证通过: {path}")

        return is_valid, issues

    def fix_path(self, path: str) -> Optional[str]:
        """
        自动修复常见路径问题

        处理的问题包括：
        - 反斜杠转正斜杠（跨平台兼容）
        - 移除多余的斜杠
        - 移除末尾空格
        - 规范化相对路径标记（./ 和 ../）
        - 处理 Windows 盘符大小写

        Args:
            path: 原始路径字符串

        Returns:
            修复后的路径字符串，如果无法修复则返回 None

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> pcc.fix_path('docs\\\\reports//test.md')
            'docs/reports/test.md'
        """
        if not path or not isinstance(path, str):
            self._logger.warning("fix_path 收到无效输入")
            return None

        try:
            fixed = path.strip()

            fixed = fixed.replace('\\', '/')

            while '//' in fixed:
                fixed = fixed.replace('//', '/')

            if fixed.startswith('./'):
                fixed = fixed[2:]

            if '..' in fixed:
                parts = fixed.split('/')
                result_parts = []
                for part in parts:
                    if part == '..':
                        if result_parts and result_parts[-1] != '..':
                            result_parts.pop()
                        else:
                            result_parts.append(part)
                    elif part and part != '.':
                        result_parts.append(part)
                fixed = '/'.join(result_parts)

            if len(fixed) >= 2 and fixed[1] == ':':
                fixed = fixed[0].upper() + fixed[1:]

            if fixed.endswith('/') and len(fixed) > 1:
                fixed = fixed.rstrip('/')

            self._logger.debug(f"路径修复: '{path}' -> '{fixed}'")
            return fixed

        except Exception as e:
            self._logger.error(f"路径修复失败 [{path}]: {e}")
            return None

    def get_script_path(self, subdir: str, script_name: str) -> Path:
        """
        获取脚本的完整路径

        Args:
            subdir: 子目录名（如 "analysis", "core", "pipeline"）
            script_name: 脚本文件名（可带或不带 .py 后缀）

        Returns:
            脚本的完整绝对路径

        Raises:
            FileNotFoundError: 如果脚本不存在
            ValueError: 如果参数无效

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> script_path = pcc.get_script_path('analysis', 'log_analyzer.py')
        """
        if not subdir or not script_name:
            raise ValueError("子目录和脚本名都不能为空")

        if not script_name.endswith('.py'):
            script_name = f"{script_name}.py"

        script_path = self.SCRIPTS_DIR / subdir / script_name

        if not script_path.exists():
            self._logger.error(f"脚本不存在: {script_path}")
            raise FileNotFoundError(f"脚本不存在: {script_path}")

        self._logger.debug(f"获取脚本路径: {script_path}")
        return script_path.resolve()

    def list_scripts(self, subdir: Optional[str] = None) -> List[Path]:
        """
        列出指定目录下的所有 Python 脚本

        Args:
            subdir: 子目录名。如果为 None，列出 SCRIPTS_DIR 下所有一级子目录的脚本

        Returns:
            脚本路径列表（已排序）

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> scripts = pcc.list_scripts('analysis')
            >>> print(len(scripts))
        """
        scripts: List[Path] = []

        if subdir:
            target_dir = self.SCRIPTS_DIR / subdir
        else:
            target_dir = self.SCRIPTS_DIR

        if not target_dir.exists():
            self._logger.warning(f"脚本目录不存在: {target_dir}")
            return scripts

        try:
            if subdir:
                for py_file in sorted(target_dir.glob('*.py')):
                    if py_file.name.startswith('__'):
                        continue
                    scripts.append(py_file.resolve())
            else:
                for sub_dir in sorted(target_dir.iterdir()):
                    if sub_dir.is_dir() and not sub_dir.name.startswith('__'):
                        for py_file in sorted(sub_dir.glob('*.py')):
                            if py_file.name.startswith('__'):
                                continue
                            scripts.append(py_file.resolve())

            self._logger.debug(f"在 {target_dir} 中发现 {len(scripts)} 个脚本")

        except Exception as e:
            self._logger.error(f"列出脚本失败 [{target_dir}]: {e}")

        return scripts

    def scan_hardcoded_paths(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        扫描文件中的硬编码路径

        检测模式包括：
        - 绝对路径（Windows 和 Unix 格式）
        - 相对路径中的敏感目录引用
        - 常见硬编码路径模式

        Args:
            file_path: 要扫描的文件路径

        Returns:
            包含硬编码路径信息的字典列表，每个字典包含：
            - line_number: 行号
            - line_content: 行内容
            - matched_path: 匹配到的路径
            - pattern_type: 模式类型

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> results = pcc.scan_hardcoded_paths(Path('some_script.py'))
        """
        results: List[Dict[str, Any]] = []

        if not file_path.exists():
            self._logger.error(f"文件不存在: {file_path}")
            return results

        if not file_path.suffix == '.py':
            self._logger.warning(f"非Python文件，跳过扫描: {file_path}")
            return results

        patterns = [
            (r'[A-Za-z]:\\[^\s"\']+', 'windows_absolute'),
            (r'/(?:home|usr|var|opt|etc)/[^\s"\']+', 'unix_absolute'),
            (r'(?:["\'])(?:\.\.\/|\.\.\\\\)[^"\']+(?:["\'])', 'relative_parent'),
            (r'(?:["\'])/(?:tmp|temp|Users)[^"\']*(?:["\'])', 'sensitive_path'),
        ]

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            for line_num, line in enumerate(content.split('\n'), 1):
                stripped = line.strip()

                if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue

                for pattern, pattern_type in patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]

                        match_clean = match.strip('"\'')

                        if any(skip in match_clean.lower() for skip in
                               ['http://', 'https://', 'ftp://', 'file://',
                                '.example.', '.template.', '__file__', 'localhost']):
                            continue

                        results.append({
                            'line_number': line_num,
                            'line_content': line.rstrip(),
                            'matched_path': match_clean,
                            'pattern_type': pattern_type,
                        })

            if results:
                self._logger.info(f"在 {file_path} 中发现 {len(results)} 个可能的硬编码路径")
            else:
                self._logger.debug(f"在 {file_path} 中未发现硬编码路径")

        except Exception as e:
            self._logger.error(f"扫描硬编码路径失败 [{file_path}]: {e}")

        return results

    def get_current_version(self) -> str:
        """
        获取当前版本号

        优先级：
        1. 环境变量 SANLIU_VERSION
        2. version.json 文件
        3. SKILL.md 文件中的版本信息
        4. 默认值 "v0.0.0"

        Returns:
            版本字符串

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> version = pcc.get_current_version()
            >>> print(version)
        """
        env_version = os.environ.get('SANLIU_VERSION')
        if env_version:
            self._logger.debug(f"从环境变量获取版本: {env_version}")
            return env_version

        version_file = self.SKILL_ROOT / 'version.json'
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    version = data.get('version', '')
                    if version:
                        self._logger.debug(f"从 version.json 获取版本: {version}")
                        return f"v{version}" if not version.startswith('v') else version
            except (json.JSONDecodeError, IOError) as e:
                self._logger.warning(f"读取 version.json 失败: {e}")

        skill_md = self.SKILL_ROOT / 'SKILL.md'
        if skill_md.exists():
            try:
                content = skill_md.read_text(encoding='utf-8')
                version_match = re.search(r'version[:\s]+([v]?\d+\.\d+\.\d+)', content, re.IGNORECASE)
                if version_match:
                    version = version_match.group(1)
                    self._logger.debug(f"从 SKILL.md 获取版本: {version}")
                    return version if version.startswith('v') else f"v{version}"
            except IOError as e:
                self._logger.warning(f"读取 SKILL.md 失败: {e}")

        self._logger.warning("无法获取版本信息，使用默认值 v0.0.0")
        return "v0.0.0"

    def create_version_dir(self, version: str) -> Path:
        """
        创建版本化目录结构

        在 VERSIONS_DIR 下创建指定版本的目录，
        并复制 CHANGELOG.md 模板（如果存在）

        Args:
            version: 版本号（如 "v3.2.0"）

        Returns:
            创建的版本目录路径

        Raises:
            ValueError: 如果版本号为空
            OSError: 如果目录创建失败

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> v_dir = pcc.create_version_dir('v3.2.0')
        """
        if not version:
            raise ValueError("版本号不能为空")

        version_dir = self.VERSIONS_DIR / version

        try:
            version_dir.mkdir(parents=True, exist_ok=True)
            self._logger.info(f"创建版本目录: {version_dir}")

            changelog_template = self.VERSIONS_DIR / 'CHANGELOG.md'
            if changelog_template.exists() and not (version_dir / 'CHANGELOG.md').exists():
                shutil.copy2(changelog_template, version_dir / 'CHANGELOG.md')
                self._logger.debug(f"复制 CHANGELOG.md 到 {version_dir}")

        except OSError as e:
            self._logger.error(f"创建版本目录失败 [{version}]: {e}")
            raise

        return version_dir

    def archive_to_version(
        self,
        path: Path,
        version: str,
        category: str
    ) -> Path:
        """
        归档文件到版本目录

        将指定文件复制到对应版本的归档目录中

        Args:
            path: 要归档的源文件路径
            version: 目标版本号
            category: 归档类别（用于命名子目录或文件）

        Returns:
            归档后的目标文件路径

        Raises:
            FileNotFoundError: 如果源文件不存在
            ValueError: 如果参数无效

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> archived = pcc.archive_to_version(report_path, 'v3.2.0', '测试报告')
        """
        if not path.exists():
            raise FileNotFoundError(f"源文件不存在: {path}")

        if not version or not category:
            raise ValueError("版本号和类别都不能为空")

        version_dir = self.create_version_dir(version)

        dest_filename = f"{category}{path.suffix}" if path.suffix else f"{category}.md"
        dest_path = version_dir / dest_filename

        try:
            shutil.copy2(path, dest_path)
            self._logger.info(f"文件已归档: {path} -> {dest_path}")
        except (IOError, shutil.Error) as e:
            self._logger.error(f"归档文件失败: {e}")
            raise

        return dest_path

    def validate_all_paths(self) -> Dict[str, Any]:
        """
        验证所有预定义路径的有效性

        Returns:
            包含验证结果的字典：
            - total: 总路径数
            - valid: 有效路径数
            - invalid: 无效路径数
            - details: 每个路径的详细验证结果

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> result = pcc.validate_all_paths()
            >>> print(f"有效: {result['valid']}/{result['total']}")
        """
        results: Dict[str, Any] = {
            'total': len(self._all_paths),
            'valid': 0,
            'invalid': 0,
            'details': {},
        }

        for name, path in self._all_paths.items():
            is_valid, issues = self.validate_path(path)
            results['details'][name] = {
                'path': str(path),
                'is_valid': is_valid,
                'issues': issues,
            }
            if is_valid:
                results['valid'] += 1
            else:
                results['invalid'] += 1

        self._logger.info(
            f"路径验证完成: {results['valid']}/{results['total']} 有效"
        )
        return results

    def fix_all_hardcoded(self, directory: Path) -> List[Dict[str, Any]]:
        """
        批量修复目录下的硬编码路径

        扫描目录下所有 Python 文件，检测并记录硬编码路径问题。
        注意：此方法仅做检测和报告，不自动修改文件。

        Args:
            directory: 要扫描的目录路径

        Returns:
            包含所有发现的硬编码路径信息的列表

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> issues = pcc.fix_all_hardcoded(pcc.SCRIPTS_DIR / 'analysis')
            >>> print(f"发现 {len(issues)} 个问题")
        """
        all_issues: List[Dict[str, Any]] = []

        if not directory.exists():
            self._logger.warning(f"目录不存在: {directory}")
            return all_issues

        if not directory.is_dir():
            self._logger.warning(f"不是目录: {directory}")
            return all_issues

        try:
            py_files = list(directory.rglob('*.py'))
            self._logger.info(f"开始扫描目录 {directory}，共 {len(py_files)} 个 Python 文件")

            for py_file in py_files:
                if py_file.name.startswith('__'):
                    continue

                issues = self.scan_hardcoded_paths(py_file)
                if issues:
                    for issue in issues:
                        issue['file_path'] = str(py_file)
                        all_issues.append(issue)

            self._logger.info(
                f"扫描完成: 在 {directory} 中发现 {len(all_issues)} 个硬编码路径"
            )

        except Exception as e:
            self._logger.error(f"批量扫描硬编码路径失败 [{directory}]: {e}")

        return all_issues

    def export_config(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        导出当前配置

        将所有路径配置和环境信息导出为字典，可选保存到文件

        Args:
            output_path: 可选的输出文件路径。如果提供，将配置写入该文件

        Returns:
            包含完整配置信息的字典

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> config = pcc.export_config(Path('config_export.json'))
        """
        config: Dict[str, Any] = {
            'meta': {
                'class': self.__class__.__name__,
                'version': self.get_current_version(),
                'skill_root': str(self.SKILL_ROOT),
            },
            'paths': {name: str(path) for name, path in self._all_paths.items()},
            'environment': {
                var: os.environ.get(var, '<not set>')
                for var in [
                    'SANLIU_SKILL_ROOT',
                    'SANLIU_DOCS_DIR',
                    'SANLIU_SCRIPTS_DIR',
                    'SANLIU_VERSION',
                ]
            },
            'validation_summary': self.validate_all_paths(),
        }

        if output_path:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                self._logger.info(f"配置已导出到: {output_path}")
            except (IOError, TypeError) as e:
                self._logger.error(f"导出配置失败: {e}")

        return config

    def get_path_info(self, path_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定路径的详细信息

        Args:
            path_name: 路径常量名称（如 "DOCS_DIR", "SCRIPTS_DIR"）

        Returns:
            包含路径信息的字典，如果名称无效则返回 None

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> info = pcc.get_path_info('DOCS_DIR')
        """
        path = self._all_paths.get(path_name.upper())
        if not path:
            self._logger.warning(f"未知路径名称: {path_name}")
            return None

        is_valid, issues = self.validate_path(path)

        return {
            'name': path_name.upper(),
            'path': str(path),
            'absolute_path': str(path.resolve()),
            'exists': path.exists(),
            'is_dir': path.is_dir() if path.exists() else None,
            'is_file': path.is_file() if path.exists() else None,
            'is_valid': is_valid,
            'issues': issues,
        }

    def reload(self):
        """
        重新加载配置

        在环境变量更改后调用此方法刷新路径配置
        """
        self._logger.info("重新加载 PathConfigCenter 配置...")
        self._detect_skill_root()
        self._initialize_paths()
        self._ensure_directories()
        self._logger.info("配置重新加载完成")

    def lazy_get(self, key: str, factory=None) -> Path:
        """
        延迟获取路径，仅在首次访问时计算

        支持延迟加载模式，避免不必要的路径计算开销。
        首次访问时计算并缓存结果，后续访问直接返回缓存值。

        Args:
            key: 路径键名（如 'DOCS_DIR', 'SCRIPTS_DIR' 等）
            factory: 可选的计算工厂函数，如果提供则使用该函数计算路径

        Returns:
            Path对象

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> docs_dir = pcc.lazy_get('DOCS_DIR')
            >>> custom_path = pcc.lazy_get('custom', lambda: Path('/custom/path'))
        """
        if key not in self._lazy_cache:
            if factory:
                result = factory()
                self._lazy_cache[key] = result if isinstance(result, Path) else Path(result)
            elif key in self._all_paths:
                self._lazy_cache[key] = self._all_paths[key]
            else:
                raise ValueError(f"未知的路径键名: {key}，且未提供工厂函数")

            self._logger.debug(f"延迟计算路径 [{key}]: {self._lazy_cache[key]}")

        return self._lazy_cache[key]

    def clear_lazy_cache(self, key: str = None) -> None:
        """
        清除延迟缓存

        Args:
            key: 要清除的缓存键名。如果为 None，则清除所有缓存

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> pcc.clear_lazy_cache('DOCS_DIR')  # 清除特定缓存
            >>> pcc.clear_lazy_cache()  # 清除所有缓存
        """
        if key:
            if key in self._lazy_cache:
                del self._lazy_cache[key]
                self._logger.debug(f"已清除延迟缓存: {key}")
            else:
                self._logger.warning(f"缓存中不存在键: {key}")
        else:
            cache_size = len(self._lazy_cache)
            self._lazy_cache.clear()
            self._logger.info(f"已清除所有延迟缓存 (共 {cache_size} 项)")

    def ensure_output_directory(self, category: str = "reports", version: str = None) -> Path:
        """
        确保输出目录存在，仅在需要时创建

        支持版本化目录结构，自动创建所需的目录层级。
        创建 .gitkeep 文件以保持目录结构在版本控制系统中。

        Args:
            category: 子类别 (reports/api/workflow/knowledge)
            version: 版本号，默认使用当前版本

        Returns:
            输出目录路径

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> output_dir = pcc.ensure_output_directory('reports', 'v3.3.0')
            >>> print(output_dir)
            PosixPath('/path/to/sanliu/docs/迭代版本/v3.3.0/reports')
        """
        version = version or self.get_current_version()
        output_dir = self.VERSIONS_DIR / version / category

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"确保输出目录存在: {output_dir}")

            gitkeep = output_dir / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
                self._logger.debug(f"创建 .gitkeep 文件: {gitkeep}")

        except OSError as e:
            self._logger.error(f"无法创建输出目录 {output_dir}: {e}")
            raise

        return output_dir

    def create_snapshot(self, snapshot_id: str = None) -> dict:
        """
        创建当前路径状态快照

        保存当前所有路径配置和环境信息到快照文件，
        用于后续的状态恢复或问题排查。

        Args:
            snapshot_id: 快照ID，默认自动生成 (格式: SNAP-YYYYMMDDHHMMSS)

        Returns:
            快照元数据字典

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> snapshot = pcc.create_snapshot()
            >>> print(snapshot['id'])
            'SNAP-20260402120000'
        """
        from datetime import datetime

        snapshot_id = snapshot_id or f"SNAP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        snapshot_data = {
            'id': snapshot_id,
            'timestamp': datetime.now().isoformat(),
            'version': self.get_current_version(),
            'paths': {
                key: str(value) for key, value in self._all_paths.items()
            },
            'environment': {
                k: v for k, v in os.environ.items() if k.startswith('SANLIU_')
            },
            'lazy_cache_size': len(self._lazy_cache)
        }

        snapshot_dir = self.SKILL_ROOT / "directory_snapshots"
        try:
            snapshot_dir.mkdir(exist_ok=True)
            snapshot_file = snapshot_dir / f"{snapshot_id}.json"
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False)

            self._logger.info(f"快照已保存: {snapshot_file}")
        except Exception as e:
            self._logger.error(f"保存快照失败: {e}")
            raise

        return snapshot_data

    def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        从快照恢复路径状态

        从指定的快照文件恢复路径配置和环境变量信息。

        Args:
            snapshot_id: 快照ID (如 'SNAP-20260402120000')

        Returns:
            是否成功恢复

        示例:
            >>> pcc = PathConfigCenter.instance()
            >>> success = pcc.restore_snapshot('SNAP-20260402120000')
            >>> print(success)
            True
        """
        snapshot_file = self.SKILL_ROOT / "directory_snapshots" / f"{snapshot_id}.json"

        if not snapshot_file.exists():
            self._logger.error(f"快照文件不存在: {snapshot_file}")
            return False

        try:
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            restored_paths = {
                k: Path(v) for k, v in data['paths'].items()
            }

            self._all_paths.update(restored_paths)
            self.clear_lazy_cache()

            self._logger.info(
                f"成功从快照恢复: {snapshot_id} "
                f"(恢复 {len(restored_paths)} 个路径)"
            )

            return True

        except Exception as e:
            self._logger.error(f"恢复快照失败 [{snapshot_id}]: {e}")
            return False

    def __repr__(self) -> str:
        """返回对象的可读表示"""
        return (
            f"PathConfigCenter("
            f"root={self.SKILL_ROOT}, "
            f"version={self.get_current_version()}, "
            f"paths={len(self._all_paths)}, "
            f"cached={len(self._lazy_cache)})"
        )


def get_path_config() -> PathConfigCenter:
    """
    便捷函数：获取 PathConfigCenter 单例实例

    这是推荐的获取方式，比直接使用 PathConfigCenter.instance() 更简洁

    Returns:
        PathConfigCenter 单例实例

    示例:
        >>> from skillscripts.core.path_config_center import get_path_config
        >>> pcc = get_path_config()
        >>> print(pcc.DOCS_DIR)
    """
    return PathConfigCenter.instance()
