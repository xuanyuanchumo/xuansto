"""
PathConfigCenter 单元测试
==========================

测试统一路径配置中心的所有核心功能，包括：
- 单例模式唯一性
- 路径解析准确性
- 版本感知路径生成
- 环境变量覆盖
- 路径验证
- 批量修复功能
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from skillscripts.core.path_config_center import (
    PathConfigCenter,
    get_path_config,
)


class TestSingletonPattern(unittest.TestCase):
    """测试单例模式"""

    def setUp(self):
        """每个测试前重置单例"""
        PathConfigCenter.reset_instance()

    def tearDown(self):
        """测试后清理"""
        PathConfigCenter.reset_instance()

    def test_singleton_identity(self):
        """测试多次调用 instance() 返回同一对象"""
        instance1 = PathConfigCenter.instance()
        instance2 = PathConfigCenter.instance()
        self.assertIs(instance1, instance2, "单例模式失败：返回了不同实例")

    def test_singleton_via_constructor(self):
        """测试通过构造函数也返回同一实例"""
        instance1 = PathConfigCenter()
        instance2 = PathConfigCenter.instance()
        self.assertIs(instance1, instance2, "构造函数未返回单例实例")

    def test_get_path_config_function(self):
        """测试便捷函数 get_path_config() 返回正确实例"""
        pcc = get_path_config()
        self.assertIsInstance(pcc, PathConfigCenter)
        self.assertIs(pcc, PathConfigCenter.instance())

    def test_reset_instance(self):
        """测试 reset_instance() 功能"""
        instance1 = PathConfigCenter.instance()
        PathConfigCenter.reset_instance()
        instance2 = PathConfigCenter.instance()

        self.assertIsNot(instance1, instance2, "reset_instance 后应创建新实例")

    def test_initialized_flag(self):
        """测试 _initialized 标志防止重复初始化"""
        pcc = PathConfigCenter.instance()
        initial_root = pcc.SKILL_ROOT

        pcc.__init__()
        self.assertEqual(pcc.SKILL_ROOT, initial_root, "不应重新初始化已存在的实例")


class TestPathResolution(unittest.TestCase):
    """测试路径解析功能"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()

    def tearDown(self):
        PathConfigCenter.reset_instance()

    def test_resolve_relative_path(self):
        """测试相对路径转换为绝对路径"""
        resolved = self.pcc.resolve_path('docs/reports')
        self.assertIsInstance(resolved, Path)
        self.assertTrue(resolved.is_absolute())
        self.assertTrue(str(resolved).endswith('docs' + os.sep + 'reports') or
                        'docs/reports' in str(resolved))

    def test_resolve_path_with_nested_dirs(self):
        """测试嵌套目录的路径解析"""
        resolved = self.pcc.resolve_path('docs/迭代版本/v3.0.0')
        self.assertIsInstance(resolved, Path)
        self.assertTrue(resolved.is_absolute())

    def test_resolve_empty_path_raises_error(self):
        """测试空路径抛出异常"""
        with self.assertRaises(ValueError):
            self.pcc.resolve_path('')

    def test_resolve_none_path_raises_error(self):
        """测试 None 路径抛出异常"""
        with self.assertRaises(ValueError):
            self.pcc.resolve_path(None)

    def test_get_absolute_path_single_part(self):
        """测试单段路径拼接"""
        path = self.pcc.get_absolute_path('docs')
        self.assertIsInstance(path, Path)
        self.assertTrue(path.is_absolute())
        self.assertTrue(path.name == 'docs' or str(path).endswith('docs'))

    def test_get_absolute_path_multiple_parts(self):
        """测试多段路径拼接"""
        path = self.pcc.get_absolute_path('docs', 'reports', 'test.md')
        self.assertIsInstance(path, Path)
        self.assertTrue(path.is_absolute())
        self.assertTrue(path.name == 'test.md' or str(path).endswith('test.md'))

    def test_get_absolute_path_no_parts_raises_error(self):
        """测试无参数时抛出异常"""
        with self.assertRaises(ValueError):
            self.pcc.get_absolute_path()


class TestVersionAwarePaths(unittest.TestCase):
    """测试版本感知路径生成"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()

    def tearDown(self):
        PathConfigCenter.reset_instance()

    def test_get_output_path_basic(self):
        """测试基本输出路径生成"""
        output = self.pcc.get_output_path('测试报告', 'v3.2.0')
        self.assertIsInstance(output, Path)
        self.assertTrue(str(output).endswith('测试报告.md'))
        self.assertIn('v3.2.0', str(output))

    def test_get_output_path_default_version(self):
        """测试使用默认版本号"""
        output = self.pcc.get_output_path('质量报告')
        self.assertIsInstance(output, Path)
        version = self.pcc.get_current_version()
        self.assertIn(version, str(output))

    def test_get_output_path_custom_filename(self):
        """测试自定义文件名"""
        output = self.pcc.get_output_path(
            category='报告',
            version='v3.1.0',
            filename='custom_report'
        )
        self.assertTrue(str(output).endswith('custom_report.md'))

    def test_get_output_path_with_md_extension(self):
        """测试带 .md 后缀的自定义文件名"""
        output = self.pcc.get_output_path(
            category='报告',
            filename='already.md'
        )
        self.assertTrue(str(output).endswith('already.md'))

    def test_get_output_path_empty_category_raises_error(self):
        """测试空类别抛出异常"""
        with self.assertRaises(ValueError):
            self.pcc.get_output_path('', 'v3.2.0')

    def test_get_current_version_from_file(self):
        """测试从 version.json 获取版本"""
        version = self.pcc.get_current_version()
        self.assertIsNotNone(version)
        self.assertTrue(len(version) > 0)

    def test_create_version_dir(self):
        """测试创建版本目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_versions_dir = self.pcc.VERSIONS_DIR
            self.pcc.VERSIONS_DIR = Path(tmpdir)

            try:
                v_dir = self.pcc.create_version_dir('v99.99.99')
                self.assertTrue(v_dir.exists())
                self.assertEqual(v_dir.name, 'v99.99.99')
            finally:
                self.pcc.VERSIONS_DIR = original_versions_dir

    def test_archive_to_version(self):
        """测试归档文件到版本目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_versions_dir = self.pcc.VERSIONS_DIR
            self.pcc.VERSIONS_DIR = Path(tmpdir)

            try:
                source_file = Path(tmpdir) / 'source_test.md'
                source_file.write_text('# Test Content')

                archived = self.pcc.archive_to_version(source_file, 'v9.9.9', '归档报告')
                self.assertTrue(archived.exists())
                self.assertEqual(archived.name, '归档报告.md')
                self.assertIn('v9.9.9', str(archived))
            finally:
                self.pcc.VERSIONS_DIR = original_versions_dir


class TestEnvironmentVariableOverride(unittest.TestCase):
    """测试环境变量覆盖功能"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.original_env = {}

    def tearDown(self):
        PathConfigCenter.reset_instance()
        for key in list(self.original_env.keys()):
            if self.original_env[key] is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = self.original_env[key]

    def set_env(self, key, value):
        """辅助方法：保存并设置环境变量"""
        self.original_env[key] = os.environ.get(key)
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]

    def test_skill_root_override(self):
        """测试 SANLIU_SKILL_ROOT 环境变量覆盖"""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.set_env('SANLIU_SKILL_ROOT', tmpdir)
            PathConfigCenter.reset_instance()
            pcc = PathConfigCenter.instance()

            self.assertEqual(pcc.SKILL_ROOT, Path(tmpdir).resolve())

    def test_docs_dir_override(self):
        """测试 SANLIU_DOCS_DIR 环境变量覆盖"""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_docs = Path(tmpdir) / 'custom_docs'
            custom_docs.mkdir()
            self.set_env('SANLIU_DOCS_DIR', str(custom_docs))
            PathConfigCenter.reset_instance()
            pcc = PathConfigCenter.instance()

            self.assertEqual(pcc.DOCS_DIR, custom_docs.resolve())

    def test_scripts_dir_override(self):
        """测试 SANLIU_SCRIPTS_DIR 环境变量覆盖"""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_scripts = Path(tmpdir) / 'custom_scripts'
            custom_scripts.mkdir()
            self.set_env('SANLIU_SCRIPTS_DIR', str(custom_scripts))
            PathConfigCenter.reset_instance()
            pcc = PathConfigCenter.instance()

            self.assertEqual(pcc.SCRIPTS_DIR, custom_scripts.resolve())

    def test_version_override(self):
        """测试 SANLIU_VERSION 环境变量覆盖"""
        self.set_env('SANLIU_VERSION', 'v5.5.5')
        PathConfigCenter.reset_instance()
        pcc = PathConfigCenter.instance()

        self.assertEqual(pcc.get_current_version(), 'v5.5.5')


class TestPathValidation(unittest.TestCase):
    """测试路径验证功能"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()

    def tearDown(self):
        PathConfigCenter.reset_instance()

    def test_validate_existing_directory(self):
        """测试验证已存在的目录"""
        is_valid, issues = self.pcc.validate_path(self.pcc.DOCS_DIR)
        if self.pcc.DOCS_DIR.exists():
            self.assertTrue(is_valid, f"DOCS_DIR 应该有效: {issues}")
        else:
            self.assertFalse(is_valid)
            self.assertTrue(any("不存在" in issue for issue in issues))

    def test_validate_nonexistent_path(self):
        """测试验证不存在的路径"""
        fake_path = Path('/this/path/should/not/exist/12345')
        is_valid, issues = self.pcc.validate_path(fake_path)
        self.assertFalse(is_valid)
        self.assertTrue(len(issues) > 0)

    def test_validate_invalid_type(self):
        """测试验证无效类型"""
        is_valid, issues = self.pcc.validate_path("not_a_path_object")
        self.assertFalse(is_valid)
        self.assertTrue(any("类型错误" in issue for issue in issues))

    def test_validate_all_paths_returns_structure(self):
        """测试 validate_all_paths 返回正确的结构"""
        result = self.pcc.validate_all_paths()

        self.assertIn('total', result)
        self.assertIn('valid', result)
        self.assertIn('invalid', result)
        self.assertIn('details', result)
        self.assertEqual(result['total'], len(self.pcc._all_paths))
        self.assertEqual(result['valid'] + result['invalid'], result['total'])

    def test_get_path_info_valid_name(self):
        """测试获取有效路径名称的信息"""
        info = self.pcc.get_path_info('DOCS_DIR')
        self.assertIsNotNone(info)
        self.assertEqual(info['name'], 'DOCS_DIR')
        self.assertIn('path', info)
        self.assertIn('is_valid', info)

    def test_get_path_info_invalid_name(self):
        """测试获取无效路径名称的信息"""
        info = self.pcc.get_path_info('NONEXISTENT_PATH')
        self.assertIsNone(info)


class TestPathFixing(unittest.TestCase):
    """测试路径修复功能"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()

    def tearDown(self):
        PathConfigCenter.reset_instance()

    def test_fix_windows_backslashes(self):
        """测试修复 Windows 反斜杠"""
        fixed = self.pcc.fix_path('docs\\reports\\test.md')
        self.assertIsNotNone(fixed)
        self.assertNotIn('\\', fixed)
        self.assertIn('/', fixed)

    def test_fix_double_slashes(self):
        """测试修复多余斜杠"""
        fixed = self.pcc.fix_path('docs//reports///test.md')
        self.assertIsNotNone(fixed)
        self.assertNotIn('//', fixed)

    def test_fix_dot_slash_prefix(self):
        """测试修复 ./ 前缀"""
        fixed = self.pcc.fix_path('./docs/reports')
        self.assertIsNotNone(fixed)
        self.assertFalse(fixed.startswith('./'))

    def test_fix_parent_dir_reference(self):
        """修复父目录引用 .. """
        fixed = self.pcc.fix_path('docs/../reports/test.md')
        self.assertIsNotNone(fixed)
        self.assertNotIn('..', fixed)

    def test_fix_trailing_slash(self):
        """测试移除末尾斜杠"""
        fixed = self.pcc.fix_path('docs/reports/')
        self.assertIsNotNone(fixed)
        self.assertFalse(fixed.endswith('/'))

    def test_fix_empty_input(self):
        """测试空输入返回 None"""
        self.assertIsNone(self.pcc.fix_path(''))
        self.assertIsNone(self.pcc.fix_path(None))

    def test_fix_whitespace(self):
        """测试移除首尾空格"""
        fixed = self.pcc.fix_path('  docs/reports  ')
        self.assertIsNotNone(fixed)
        self.assertEqual(fixed, 'docs/reports')


class TestScriptManagement(unittest.TestCase):
    """测试脚本管理功能"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()

    def tearDown(self):
        PathConfigCenter.reset_instance()

    def test_list_scripts_in_subdir(self):
        """测试列出子目录中的脚本"""
        scripts = self.pcc.list_scripts('analysis')
        self.assertIsInstance(scripts, list)

        if scripts:
            for script in scripts:
                self.assertIsInstance(script, Path)
                self.assertTrue(script.suffix == '.py')
                self.assertFalse(script.name.startswith('__'))

    def test_list_scripts_all_subdirs(self):
        """测试列出所有子目录的脚本"""
        scripts = self.pcc.list_scripts()
        self.assertIsInstance(scripts, list)

        if scripts:
            for script in scripts:
                self.assertIsInstance(script, Path)
                self.assertTrue(script.suffix == '.py')

    def test_list_nonexistent_subdir(self):
        """测试不存在的子目录返回空列表"""
        scripts = self.pcc.list_scripts('nonexistent_subdir_12345')
        self.assertIsInstance(scripts, list)
        self.assertEqual(len(scripts), 0)

    def test_get_script_path_existing(self):
        """测试获取已存在脚本的路径"""
        try:
            script_path = self.pcc.get_script_path('core', 'path_config_center.py')
            self.assertTrue(script_path.exists())
            self.assertTrue(script_path.suffix == '.py')
        except FileNotFoundError:
            pass

    def test_get_script_path_auto_extension(self):
        """测试自动添加 .py 后缀"""
        try:
            script_path = self.pcc.get_script_path('core', 'health_check')
            self.assertTrue(script_path.suffix == '.py')
        except FileNotFoundError:
            pass

    def test_get_script_path_nonexistent_raises(self):
        """测试获取不存在脚本时抛出异常"""
        with self.assertRaises(FileNotFoundError):
            self.pcc.get_script_path('core', 'nonexistent_script_99999.py')

    def test_get_script_path_empty_params_raises(self):
        """测试空参数抛出异常"""
        with self.assertRaises(ValueError):
            self.pcc.get_script_path('', 'script.py')
        with self.assertRaises(ValueError):
            self.pcc.get_script_path('core', '')


class TestHardcodedPathScanning(unittest.TestCase):
    """测试硬编码路径扫描功能"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        PathConfigCenter.reset_instance()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_file(self, content: str) -> Path:
        """辅助方法：创建测试文件"""
        file_path = Path(self.temp_dir) / 'test_script.py'
        file_path.write_text(content, encoding='utf-8')
        return file_path

    def test_scan_windows_absolute_path(self):
        """测试检测 Windows 绝对路径"""
        content = '''
def some_function():
    path = "C:\\\\Users\\\\test\\\\file.txt"
    return path
'''
        file_path = self._create_test_file(content)
        results = self.pcc.scan_hardcoded_paths(file_path)

        self.assertTrue(len(results) > 0)
        self.assertTrue(any(r['pattern_type'] == 'windows_absolute' for r in results))

    def test_scan_unix_absolute_path(self):
        """测试检测 Unix 绝对路径"""
        content = '''
def load_config():
    config_path = "/usr/local/etc/config.ini"
    return config_path
'''
        file_path = self._create_test_file(content)
        results = self.pcc.scan_hardcoded_paths(file_path)

        self.assertTrue(len(results) > 0)
        self.assertTrue(any(r['pattern_type'] == 'unix_absolute' for r in results))

    def test_scan_ignores_comments(self):
        """测试忽略注释中的路径"""
        content = '''
# This is a comment: C:\\Windows\\System32
def main():
    pass
'''
        file_path = self._create_test_file(content)
        results = self.pcc.scan_hardcoded_paths(file_path)

        self.assertEqual(len(results), 0, "不应检测注释中的硬编码路径")

    def test_scan_ignores_urls(self):
        """测试忽略 URL 中的路径"""
        content = '''
def fetch_data():
    url = "https://example.com/api/data"
    return url
'''
        file_path = self._create_test_file(content)
        results = self.pcc.scan_hardcoded_paths(file_path)

        self.assertEqual(len(results), 0, "不应将 URL 检测为硬编码路径")

    def test_scan_nonexistent_file(self):
        """测试扫描不存在的文件"""
        results = self.pcc.scan_hardcoded_paths(Path('/nonexistent/file.py'))
        self.assertEqual(len(results), 0)

    def test_scan_non_python_file(self):
        """测试扫描非 Python 文件"""
        file_path = Path(self.temp_dir) / 'test.txt'
        file_path.write_text('C:\\Users\\test')
        results = self.pcc.scan_hardcoded_paths(file_path)
        self.assertEqual(len(results), 0)


class TestBatchOperations(unittest.TestCase):
    """测试批量操作功能"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        PathConfigCenter.reset_instance()
        import shutil
from skillscripts.core.path_config_center import get_path_config
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fix_all_hardcoded_scans_directory(self):
        """测试批量扫描目录功能"""
        test_file = Path(self.temp_dir) / 'hardcoded.py'
        test_file.write_text('path = "/tmp/data"')

        results = self.pcc.fix_all_hardcoded(Path(self.temp_dir))
        self.assertIsInstance(results, list)

    def test_fix_all_hardcoded_nonexistent_dir(self):
        """测试扫描不存在的目录"""
        results = self.pcc.fix_all_hardcoded(Path('/nonexistent/dir'))
        self.assertEqual(len(results), 0)

    def test_export_config_to_file(self):
        """测试导出配置到文件"""
        output_path = Path(self.temp_dir) / 'config_export.json'
        config = self.pcc.export_config(output_path)

        self.assertIsInstance(config, dict)
        self.assertIn('meta', config)
        self.assertIn('paths', config)
        self.assertIn('environment', config)
        self.assertTrue(output_path.exists())

        with open(output_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        self.assertEqual(loaded['meta']['class'], 'PathConfigCenter')

    def test_export_config_without_file(self):
        """测试不指定输出文件的配置导出"""
        config = self.pcc.export_config()

        self.assertIsInstance(config, dict)
        self.assertIn('paths', config)
        self.assertTrue(len(config['paths']) > 0)


class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """测试边界情况和错误处理"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()

    def tearDown(self):
        PathConfigCenter.reset_instance()

    def test_repr_contains_info(self):
        """测试 __repr__ 包含关键信息"""
        repr_str = repr(self.pcc)
        self.assertIn('PathConfigCenter', repr_str)
        self.assertIn('root=', repr_str)
        self.assertIn('version=', repr_str)

    def test_reload_refreshes_config(self):
        """测试 reload 方法刷新配置"""
        original_root = self.pcc.SKILL_ROOT
        self.pcc.reload()
        self.assertEqual(self.pcc.SKILL_ROOT, original_root)

    def test_create_version_dir_empty_version_raises(self):
        """测试空版本号抛出异常"""
        with self.assertRaises(ValueError):
            self.pcc.create_version_dir('')

    def test_archive_nonexistent_file_raises(self):
        """测试归档不存在的文件抛出异常"""
        with self.assertRaises(FileNotFoundError):
            self.pcc.archive_to_version(
                Path('/nonexistent/file.txt'),
                'v1.0.0',
                'test'
            )

    def test_archive_empty_params_raises(self):
        """测试空参数抛出异常"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)

        try:
            with self.assertRaises(ValueError):
                self.pcc.archive_to_version(temp_path, '', 'category')
            with self.assertRaises(ValueError):
                self.pcc.archive_to_version(temp_path, 'v1.0.0', '')
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
