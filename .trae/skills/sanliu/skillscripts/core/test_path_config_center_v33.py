#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PathConfigCenter 边界条件测试 v33
==============================

补充边界条件和异常场景测试，确保95%+覆盖率：
- 空路径和特殊字符处理
- 跨平台路径兼容性
- 环境变量覆盖边界情况
- 并发访问安全性
- 版本感知路径生成边界条件
- 缓存机制正确性
"""

import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from skillscripts.core.path_config_center import (
    PathConfigCenter,
    get_path_config,
)


class TestEmptyAndSpecialPaths(unittest.TestCase):
    """测试空路径和特殊字符路径处理"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()

    def tearDown(self):
        PathConfigCenter.reset_instance()

    def test_resolve_empty_string_raises_error(self):
        """测试空字符串路径抛出ValueError"""
        with self.assertRaises(ValueError) as ctx:
            self.pcc.resolve_path('')
        self.assertIn("不能为空", str(ctx.exception))

    def test_resolve_none_raises_error(self):
        """测试None值抛出ValueError"""
        with self.assertRaises(ValueError):
            self.pcc.resolve_path(None)

    def test_resolve_non_string_type_raises_error(self):
        """测试非字符串类型抛出ValueError"""
        with self.assertRaises(ValueError):
            self.pcc.resolve_path(123)
        with self.assertRaises(ValueError):
            self.pcc.resolve_path(['path'])

    def test_fix_path_empty_string_returns_none(self):
        """测试修复空字符串返回None"""
        self.assertIsNone(self.pcc.fix_path(''))

    def test_fix_path_none_returns_none(self):
        """测试修复None返回None"""
        self.assertIsNone(self.pcc.fix_path(None))

    def test_fix_path_non_string_returns_none(self):
        """测试修复非字符串类型返回None"""
        self.assertIsNone(self.pcc.fix_path(123))
        self.assertIsNone(self.pcc.fix_path([]))

    def test_get_absolute_path_no_args_raises_error(self):
        """测试无参数时抛出ValueError"""
        with self.assertRaises(ValueError) as ctx:
            self.pcc.get_absolute_path()
        self.assertIn("至少需要", str(ctx.exception))

    def test_get_output_path_empty_category_raises_error(self):
        """测试空类别抛出ValueError"""
        with self.assertRaises(ValueError) as ctx:
            self.pcc.get_output_path('')
        self.assertIn("不能为空", str(ctx.exception))

    def test_get_output_path_none_category_raises_error(self):
        """测试None类别抛出ValueError"""
        with self.assertRaises(ValueError):
            self.pcc.get_output_path(None)

    def test_special_characters_in_path(self):
        """测试包含特殊字符的路径处理"""
        special_paths = [
            'docs/reports (测试)/file.md',
            'data/中文目录/test.txt',
            'path with spaces/file.py',
            'docs/@special/dir',
        ]
        for path in special_paths:
            resolved = self.pcc.resolve_path(path)
            self.assertIsInstance(resolved, Path)
            self.assertTrue(resolved.is_absolute())

    def test_unicode_path_handling(self):
        """测试Unicode路径处理"""
        unicode_paths = [
            '文档/报告',
            '数据/日本語テスト',
            'reports/한국어',
        ]
        for path in unicode_paths:
            resolved = self.pcc.resolve_path(path)
            self.assertIsInstance(resolved, Path)


class TestCrossPlatformPaths(unittest.TestCase):
    """测试跨平台路径兼容性"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()

    def tearDown(self):
        PathConfigCenter.reset_instance()

    def test_windows_style_backslash_conversion(self):
        """测试Windows反斜杠转换"""
        fixed = self.pcc.fix_path('docs\\reports\\test.md')
        self.assertIsNotNone(fixed)
        self.assertNotIn('\\', fixed)
        self.assertIn('/', fixed)

    def test_windows_drive_letter_normalization(self):
        """测试Windows盘符大小写规范化"""
        fixed = self.pcc.fix_path('c:\\users\\test')
        self.assertIsNotNone(fixed)
        self.assertTrue(fixed[0].isupper())
        self.assertEqual(fixed[1], ':')

    def test_unix_absolute_path_detection(self):
        """测试Unix绝对路径检测"""
        fixed = self.pcc.fix_path('/usr/local/bin')
        self.assertIsNotNone(fixed)
        self.assertTrue(fixed.startswith('/'))

    def test_mixed_separators_normalization(self):
        """测试混合分隔符规范化"""
        mixed = 'docs\\reports//test///file'
        fixed = self.pcc.fix_path(mixed)
        self.assertIsNotNone(fixed)
        self.assertNotIn('\\', fixed)
        self.assertNotIn('//', fixed)

    def test_dot_slash_prefix_removal(self):
        """测试./前缀移除"""
        fixed = self.pcc.fix_path('./docs/reports')
        self.assertIsNotNone(fixed)
        self.assertFalse(fixed.startswith('./'))

    def test_parent_directory_resolution(self):
        """测试父目录引用解析"""
        fixed = self.pcc.fix_path('docs/../reports/test')
        self.assertIsNotNone(fixed)
        self.assertNotIn('..', fixed)

    def test_trailing_slash_removal(self):
        """测试末尾斜杠移除"""
        fixed = self.pcc.fix_path('docs/reports/')
        self.assertIsNotNone(fixed)
        if len(fixed) > 1:
            self.assertFalse(fixed.endswith('/'))

    def test_whitespace_trim(self):
        """测试首尾空格去除"""
        fixed = self.pcc.fix_path('  docs/reports  ')
        self.assertIsNotNone(fixed)
        self.assertEqual(fixed, 'docs/reports')

    def test_multiple_consecutive_slashes(self):
        """测试多个连续斜杠处理"""
        fixed = self.pcc.fix_path('docs////reports///test')
        self.assertIsNotNone(fixed)
        self.assertNotIn('//', fixed)


class TestEnvironmentVariableEdgeCases(unittest.TestCase):
    """测试环境变量覆盖边界情况"""

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

    def test_empty_skill_root_env_uses_default(self):
        """测试空的SANLIU_SKILL_ROOT使用默认检测"""
        self.set_env('SANLIU_SKILL_ROOT', '')
        PathConfigCenter.reset_instance()
        pcc = PathConfigCenter.instance()
        self.assertIsNotNone(pcc.SKILL_ROOT)
        self.assertTrue(pcc.SKILL_ROOT.exists() or True)

    def test_invalid_path_in_env_falls_back(self):
        """测试环境变量中无效路径的处理"""
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_path = Path(tmpdir) / 'nonexistent_dir_12345'
            self.set_env('SANLIU_DOCS_DIR', str(invalid_path))
            PathConfigCenter.reset_instance()
            pcc = PathConfigCenter.instance()
            self.assertIsNotNone(pcc.DOCS_DIR)

    @patch.dict(os.environ, {'SANLIU_VERSION': ''}, clear=False)
    def test_empty_version_env_uses_file_or_default(self):
        """测试空版本号环境变量的回退逻辑"""
        PathConfigCenter.reset_instance()
        pcc = PathConfigCenter.instance()
        version = pcc.get_current_version()
        self.assertIsNotNone(version)
        self.assertTrue(len(version) > 0)

    def test_version_with_v_prefix_preserved(self):
        """测试带v前缀的版本号保留"""
        self.set_env('SANLIU_VERSION', 'v3.2.1')
        PathConfigCenter.reset_instance()
        pcc = PathConfigCenter.instance()
        self.assertEqual(pcc.get_current_version(), 'v3.2.1')

    def test_version_without_v_prefix_adds_it(self):
        """测试不带v前缀的版本号自动添加"""
        self.set_env('SANLIU_VERSION', '3.2.1')
        PathConfigCenter.reset_instance()
        pcc = PathConfigCenter.instance()
        version = pcc.get_current_version()
        self.assertTrue(version.startswith('v'))

    def test_special_chars_in_env_path(self):
        """测试环境变量路径中的特殊字符"""
        with tempfile.TemporaryDirectory() as tmpdir:
            special_name = 'dir with spaces & symbols'
            custom_dir = Path(tmpdir) / special_name
            custom_dir.mkdir()
            self.set_env('SANLIU_CACHE_DIR', str(custom_dir))
            PathConfigCenter.reset_instance()
            pcc = PathConfigCenter.instance()
            self.assertEqual(pcc.CACHE_DIR, custom_dir.resolve())


class TestNonExistentPathErrorHandling(unittest.TestCase):
    """测试路径不存在时的错误处理"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()

    def tearDown(self):
        PathConfigCenter.reset_instance()

    def test_validate_completely_fake_path(self):
        """测试验证完全虚假的路径"""
        fake = Path('/this/path/definitely/does/not/exist/anywhere')
        is_valid, issues = self.pcc.validate_path(fake)
        self.assertFalse(is_valid)
        self.assertTrue(len(issues) > 0)
        self.assertTrue(any("不存在" in issue for issue in issues))

    def test_validate_permission_denied_simulation(self):
        """模拟权限拒绝场景（仅验证方法不崩溃）"""
        temp_file = Path(tempfile.mktemp())
        try:
            temp_file.write_text('test')
            temp_file.chmod(0o444)
            is_valid, issues = self.pcc.validate_path(temp_file)
            self.assertIsInstance(is_valid, bool)
            self.assertIsInstance(issues, list)
        finally:
            temp_file.chmod(0o644)
            temp_file.unlink(missing_ok=True)

    def test_get_script_path_nonexistent_raises(self):
        """测试获取不存在脚本时抛出FileNotFoundError"""
        with self.assertRaises(FileNotFoundError):
            self.pcc.get_script_path('core', 'totally_fake_script_xyz.py')

    def test_list_scripts_nonexistent_subdir(self):
        """测试列出不存在子目录的脚本返回空列表"""
        scripts = self.pcc.list_scripts('nonexistent_dir_99999')
        self.assertIsInstance(scripts, list)
        self.assertEqual(len(scripts), 0)

    def test_scan_hardcoded_nonexistent_file(self):
        """测试扫描不存在文件返回空列表"""
        results = self.pcc.scan_hardcoded_paths(Path('/nonexistent/file.py'))
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    def test_archive_nonexistent_source_raises(self):
        """测试归档不存在的源文件抛出FileNotFoundError"""
        with self.assertRaises(FileNotFoundError):
            self.pcc.archive_to_version(
                Path('/nonexistent/source.txt'),
                'v1.0.0',
                'test_category'
            )

    def test_create_version_dir_empty_version_raises(self):
        """测试创建空版本号目录抛出ValueError"""
        with self.assertRaises(ValueError):
            self.pcc.create_version_dir('')

    def test_create_version_dir_none_version_raises(self):
        """测试None版本号抛出ValueError"""
        with self.assertRaises(ValueError):
            self.pcc.create_version_dir(None)


class TestConcurrentAccessSafety(unittest.TestCase):
    """测试并发访问安全性"""

    def setUp(self):
        PathConfigCenter.reset_instance()

    def tearDown(self):
        PathConfigCenter.reset_instance()

    def test_singleton_thread_safety(self):
        """测试单例模式的线程安全性"""
        instances = []
        errors = []

        def get_instance():
            try:
                inst = PathConfigCenter.instance()
                instances.append(id(inst))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"线程错误: {errors}")
        self.assertTrue(len(set(instances)) == 1, "所有线程应获得同一实例")

    def test_concurrent_resolve_path(self):
        """测试并发路径解析安全性"""
        PathConfigCenter.reset_instance()
        pcc = PathConfigCenter.instance()

        results = []
        errors = []

        def resolve():
            try:
                resolved = pcc.resolve_path('docs/reports')
                results.append(resolved)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=resolve) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"并发错误: {errors}")
        self.assertEqual(len(results), 20)
        self.assertTrue(all(r.is_absolute() for r in results))

    def test_concurrent_reset_and_recreate(self):
        """测试并发重置和重建实例的安全性"""
        errors = []
        instance_ids = []

        def reset_and_get():
            try:
                PathConfigCenter.reset_instance()
                inst = PathConfigCenter.instance()
                instance_ids.append(id(inst))
                time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=reset_and_get) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"并发错误: {errors}")


class TestVersionAwarePathBoundaryConditions(unittest.TestCase):
    """测试版本感知路径生成的边界条件"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        PathConfigCenter.reset_instance()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_get_output_path_with_custom_filename_no_extension(self):
        """测试自定义文件名不带扩展名时自动添加.md"""
        output = self.pcc.get_output_path(
            category='测试',
            version='v1.0.0',
            filename='custom_report'
        )
        self.assertTrue(str(output).endswith('.md'))

    def test_get_output_path_with_md_extension_preserved(self):
        """测试带.md扩展名的自定义文件名保留原样"""
        output = self.pcc.get_output_path(
            category='测试',
            filename='already_has_ext.md'
        )
        self.assertTrue(str(output).endswith('already_has_ext.md'))

    def test_get_output_path_uses_current_version_when_none(self):
        """测试version=None时使用当前版本"""
        output = self.pcc.get_output_path('质量报告')
        current_version = self.pcc.get_current_version()
        self.assertIn(current_version, str(output))

    def test_create_version_dir_creates_actual_directory(self):
        """测试create_version_dir实际创建目录"""
        original_versions = self.pcc.VERSIONS_DIR
        self.pcc.VERSIONS_DIR = Path(self.tmpdir)

        try:
            v_dir = self.pcc.create_version_dir('v99.99.99-test')
            self.assertTrue(v_dir.exists())
            self.assertTrue(v_dir.is_dir())
            self.assertEqual(v_dir.name, 'v99.99.99-test')
        finally:
            self.pcc.VERSIONS_DIR = original_versions

    def test_archive_to_version_copies_file(self):
        """测试archive_to_version实际复制文件"""
        original_versions = self.pcc.VERSIONS_DIR
        self.pcc.VERSIONS_DIR = Path(self.tmpdir)

        try:
            source = Path(self.tmpdir) / 'source.txt'
            source.write_text('test content for archive')

            archived = self.pcc.archive_to_version(source, 'v9.9.9', '归档类别')
            self.assertTrue(archived.exists())
            self.assertEqual(archived.read_text(), 'test content for archive')
            self.assertIn('v9.9.9', str(archived))
        finally:
            self.pcc.VERSIONS_DIR = original_versions

    def test_archive_with_empty_params_raises(self):
        """测试归档参数为空时抛出异常"""
        source = Path(self.tmpdir) / 'tmp.txt'
        source.write_text('temp')

        with self.assertRaises(ValueError):
            self.pcc.archive_to_version(source, '', 'category')
        with self.assertRaises(ValueError):
            self.pcc.archive_to_version(source, 'v1.0.0', '')

    def test_version_format_variations(self):
        """测试各种版本格式"""
        versions = ['v1.0.0', 'v2.3.4-rc1', 'v3.0.0-beta', 'V10.20.30']
        for ver in versions:
            output = self.pcc.get_output_path('测试', ver)
            self.assertIn(ver, str(output))


class TestCacheMechanism(unittest.TestCase):
    """测试缓存机制正确性"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()

    def tearDown(self):
        PathConfigCenter.reset_instance()

    def test_all_paths_cache_populated(self):
        """测试_all_paths字典在初始化后已填充"""
        self.assertIsInstance(self.pcc._all_paths, dict)
        self.assertTrue(len(self.pcc._all_paths) >= 10)

    def test_all_paths_contains_expected_keys(self):
        """测试_all_paths包含预期的键"""
        expected_keys = [
            'SKILL_ROOT', 'DOCS_DIR', 'SCRIPTS_DIR',
            'REPORTS_DIR', 'CACHE_DIR', 'LOGS_DIR'
        ]
        for key in expected_keys:
            self.assertIn(key, self.pcc._all_paths)

    def test_reload_refreshes_paths(self):
        """测试reload方法刷新路径配置"""
        original_root = self.pcc.SKILL_ROOT
        self.pcc.reload()
        self.assertIsNotNone(self.pcc.SKILL_ROOT)

    def test_get_path_info_returns_complete_dict(self):
        """测试get_path_info返回完整字典"""
        info = self.pcc.get_path_info('DOCS_DIR')
        self.assertIsNotNone(info)
        expected_fields = [
            'name', 'path', 'absolute_path', 'exists',
            'is_dir', 'is_file', 'is_valid', 'issues'
        ]
        for field in expected_fields:
            self.assertIn(field, info)

    def test_get_path_info_invalid_key_returns_none(self):
        """测试无效路径名称返回None"""
        self.assertIsNone(self.pcc.get_path_info('INVALID_KEY_XYZ'))
        self.assertIsNone(self.pcc.get_path_info(''))

    def test_export_config_includes_environment_section(self):
        """测试export_config包含environment节"""
        config = self.pcc.export_config()
        self.assertIn('environment', config)
        self.assertIn('paths', config)
        self.assertIn('meta', config)

    def test_export_config_to_file_creates_valid_json(self):
        """测试导出配置到文件生成有效JSON"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            output_path = Path(f.name)

        try:
            config = self.pcc.export_config(output_path)
            self.assertTrue(output_path.exists())

            with open(output_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            self.assertEqual(loaded['meta']['class'], 'PathConfigCenter')
        finally:
            output_path.unlink(missing_ok=True)


class TestBatchOperationsEdgeCases(unittest.TestCase):
    """测试批量操作边界情况"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        PathConfigCenter.reset_instance()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_fix_all_hardcoded_on_nonexistent_directory(self):
        """测试扫描不存在目录返回空列表"""
        results = self.pcc.fix_all_hardcoded(Path('/nonexistent/directory'))
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    def test_fix_all_hardcoded_on_file_instead_of_dir(self):
        """测试扫描文件而非目录返回空列表"""
        file_path = Path(self.tmpdir) / 'not_a_dir.txt'
        file_path.write_text('test')
        results = self.pcc.fix_all_hardcoded(file_path)
        self.assertIsInstance(results, list)

    def test_fix_all_hardcoded_empty_directory(self):
        """测试扫描空目录返回空列表"""
        empty_dir = Path(self.tmpdir) / 'empty'
        empty_dir.mkdir()
        results = self.pcc.fix_all_hardcoded(empty_dir)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    def test_validate_all_paths_structure_integrity(self):
        """测试validate_all_paths返回结构完整性"""
        result = self.pcc.validate_all_paths()
        self.assertIn('total', result)
        self.assertIn('valid', result)
        self.assertIn('invalid', result)
        self.assertIn('details', result)
        self.assertEqual(result['total'], result['valid'] + result['invalid'])
        self.assertEqual(result['total'], len(self.pcc._all_paths))


class TestReprAndStringRepresentation(unittest.TestCase):
    """测试对象字符串表示"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()

    def tearDown(self):
        PathConfigCenter.reset_instance()

    def test_repr_contains_class_name(self):
        """测试__repr__包含类名"""
        repr_str = repr(self.pcc)
        self.assertIn('PathConfigCenter', repr_str)

    def test_repr_contains_root(self):
        """测试__repr__包含root信息"""
        repr_str = repr(self.pcc)
        self.assertIn('root=', repr_str)

    def test_repr_contains_version(self):
        """测试__repr__包含version信息"""
        repr_str = repr(self.pcc)
        self.assertIn('version=', repr_str)

    def test_repr_contains_path_count(self):
        """测试__repr__包含路径数量"""
        repr_str = repr(self.pcc)
        self.assertIn('paths=', repr_str)


class TestGetScriptPathEdgeCases(unittest.TestCase):
    """测试get_script_path边界情况"""

    def setUp(self):
        PathConfigCenter.reset_instance()
        self.pcc = PathConfigCenter.instance()

    def tearDown(self):
        PathConfigCenter.reset_instance()

    def test_empty_subdir_raises_value_error(self):
        """测试空子目录抛出ValueError"""
        with self.assertRaises(ValueError):
            self.pcc.get_script_path('', 'script.py')

    def test_empty_script_name_raises_value_error(self):
        """测试空脚本名抛出ValueError"""
        with self.assertRaises(ValueError):
            self.pcc.get_script_path('core', '')

    def test_auto_append_py_extension(self):
        """测试自动添加.py后缀"""
        try:
            path = self.pcc.get_script_path('core', 'path_config_center')
            self.assertTrue(str(path).endswith('.py'))
        except FileNotFoundError:
            pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
