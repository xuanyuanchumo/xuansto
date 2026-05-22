#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径配置管理器单元测试

测试覆盖：
- 模式切换功能
- 路径获取功能
- 版本管理功能
- 目录创建功能
- 增强模式检测功能
- 边界条件测试
- 并发访问测试
- 错误恢复测试
"""

import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from skillscripts.utils.path_config_manager import (
    PathConfig,
    PathConfigManager,
    PathMode,
    VersionInfo,
    EnvironmentVariableDetector,
    ConfigFileDetector,
    CommandLineDetector,
    ModeAutoDetector,
    ModeDetectionSource,
    EnhancedModeDetectionResult,
    PathValidator,
    SwitchHistoryManager,
    ModeSwitchRecord,
    PathConfigError,
    ModeSwitchError,
    PathValidationError
)


class TestPathMode(unittest.TestCase):
    def test_path_mode_values(self):
        self.assertEqual(PathMode.SELF_ITERATION.value, "self_iteration")
        self.assertEqual(PathMode.GUIDE_PROJECT.value, "guide_project")
    
    def test_path_mode_count(self):
        self.assertEqual(len(PathMode), 2)


class TestPathConfig(unittest.TestCase):
    def test_default_config(self):
        config = PathConfig()
        self.assertEqual(config.docs_libs_path, "docs/libs")
        self.assertEqual(config.docs_reports_path, "docs/reports")
        self.assertEqual(config.tests_path, "tests")
        self.assertEqual(config.skillscripts_path, "skillscripts")
        self.assertEqual(config.version_file, "version.json")
    
    def test_custom_config(self):
        config = PathConfig(
            docs_libs_path="custom/docs",
            docs_reports_path="custom/reports",
            tests_path="custom/tests",
            skillscripts_path="custom/scripts",
            version_file="custom_version.json"
        )
        self.assertEqual(config.docs_libs_path, "custom/docs")
        self.assertEqual(config.docs_reports_path, "custom/reports")
        self.assertEqual(config.tests_path, "custom/tests")
        self.assertEqual(config.skillscripts_path, "custom/scripts")
        self.assertEqual(config.version_file, "custom_version.json")


class TestVersionInfo(unittest.TestCase):
    def test_version_info_creation(self):
        info = VersionInfo(
            version="1.0.0",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00"
        )
        self.assertEqual(info.version, "1.0.0")
        self.assertEqual(info.created_at, "2024-01-01T00:00:00")
        self.assertEqual(info.updated_at, "2024-01-02T00:00:00")
    
    def test_version_info_to_dict(self):
        info = VersionInfo(
            version="1.0.0",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00"
        )
        result = info.to_dict()
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(result["created_at"], "2024-01-01T00:00:00")
        self.assertEqual(result["updated_at"], "2024-01-02T00:00:00")


class TestPathConfigManagerGuideProjectMode(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=self.temp_dir
        )
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_base_path(self):
        base_path = self.manager.get_base_path()
        self.assertEqual(base_path, Path(self.temp_dir))
    
    def test_get_versioned_path(self):
        path = self.manager.get_versioned_path("docs/libs", "1.0.0")
        expected = Path(self.temp_dir) / "docs/libs/v1.0.0"
        self.assertEqual(path, expected)
    
    def test_get_versioned_path_with_v_prefix(self):
        path = self.manager.get_versioned_path("docs/libs", "v2.0.0")
        expected = Path(self.temp_dir) / "docs/libs/v2.0.0"
        self.assertEqual(path, expected)
    
    def test_get_versioned_path_empty_version_raises(self):
        with self.assertRaises(ValueError):
            self.manager.get_versioned_path("docs/libs", "")
    
    def test_ensure_directories(self):
        results = self.manager.ensure_directories()
        self.assertTrue(results["docs/libs"])
        self.assertTrue(results["docs/reports"])
        self.assertTrue(results["tests"])
        self.assertTrue(results["skillscripts"])
        
        base = Path(self.temp_dir)
        self.assertTrue((base / "docs/libs").exists())
        self.assertTrue((base / "docs/reports").exists())
        self.assertTrue((base / "tests").exists())
        self.assertTrue((base / "skillscripts").exists())
    
    def test_ensure_directories_specific_paths(self):
        results = self.manager.ensure_directories(["custom/path"])
        self.assertTrue(results["custom/path"])
        self.assertTrue((Path(self.temp_dir) / "custom/path").exists())
    
    def test_get_current_version_default(self):
        version = self.manager.get_current_version()
        self.assertEqual(version, "0.1.0")
    
    def test_set_version(self):
        result = self.manager.set_version("1.2.3")
        self.assertTrue(result)
        self.assertEqual(self.manager.get_current_version(), "1.2.3")
    
    def test_set_invalid_version(self):
        result = self.manager.set_version("invalid")
        self.assertFalse(result)
    
    def test_get_docs_libs_path(self):
        path = self.manager.get_docs_libs_path()
        expected = Path(self.temp_dir) / "docs/libs"
        self.assertEqual(path, expected)
    
    def test_get_docs_libs_path_with_version(self):
        path = self.manager.get_docs_libs_path("1.0.0")
        expected = Path(self.temp_dir) / "docs/libs/v1.0.0"
        self.assertEqual(path, expected)
    
    def test_get_docs_reports_path(self):
        path = self.manager.get_docs_reports_path()
        expected = Path(self.temp_dir) / "docs/reports"
        self.assertEqual(path, expected)
    
    def test_get_docs_reports_path_with_version(self):
        path = self.manager.get_docs_reports_path("2.0.0")
        expected = Path(self.temp_dir) / "docs/reports/v2.0.0"
        self.assertEqual(path, expected)
    
    def test_get_tests_path(self):
        path = self.manager.get_tests_path()
        expected = Path(self.temp_dir) / "tests"
        self.assertEqual(path, expected)
    
    def test_get_skillscripts_path(self):
        path = self.manager.get_skillscripts_path()
        expected = Path(self.temp_dir) / "skillscripts"
        self.assertEqual(path, expected)
    
    def test_get_all_paths(self):
        paths = self.manager.get_all_paths()
        self.assertIn("base", paths)
        self.assertIn("docs_libs", paths)
        self.assertIn("docs_reports", paths)
        self.assertIn("tests", paths)
        self.assertIn("skillscripts", paths)
    
    def test_get_all_paths_with_version(self):
        paths = self.manager.get_all_paths(version="1.0.0")
        self.assertTrue(str(paths["docs_libs"]).endswith("v1.0.0"))
        self.assertTrue(str(paths["docs_reports"]).endswith("v1.0.0"))
    
    def test_list_versions_empty(self):
        versions = self.manager.list_versions()
        self.assertEqual(versions, [])
    
    def test_list_versions_with_versions(self):
        self.manager.ensure_directories(["docs/libs"])
        version_dir = Path(self.temp_dir) / "docs/libs" / "v1.0.0"
        version_dir.mkdir(parents=True, exist_ok=True)
        version_dir2 = Path(self.temp_dir) / "docs/libs" / "v2.0.0"
        version_dir2.mkdir(parents=True, exist_ok=True)
        
        versions = self.manager.list_versions()
        self.assertEqual(versions, ["v2.0.0", "v1.0.0"])
    
    def test_get_path_info(self):
        info = self.manager.get_path_info()
        self.assertEqual(info["mode"], "guide_project")
        self.assertIn("base_path", info)
        self.assertIn("current_version", info)
        self.assertIn("paths", info)
    
    def test_switch_mode(self):
        new_temp_dir = tempfile.mkdtemp()
        result = self.manager.switch_mode(
            PathMode.GUIDE_PROJECT,
            target_root=new_temp_dir
        )
        self.assertTrue(result)
        self.assertEqual(self.manager.mode, PathMode.GUIDE_PROJECT)
        self.assertEqual(self.manager.get_base_path(), Path(new_temp_dir))
        
        import shutil
        shutil.rmtree(new_temp_dir, ignore_errors=True)
    
    def test_resolve_path(self):
        resolved = self.manager.resolve_path("some/relative/path")
        expected = Path(self.temp_dir) / "some/relative/path"
        self.assertEqual(resolved, expected)
    
    def test_path_exists(self):
        self.assertFalse(self.manager.path_exists("nonexistent"))
        self.manager.ensure_directories(["tests"])
        self.assertTrue(self.manager.path_exists("tests"))
    
    def test_create_version_directories(self):
        results = self.manager.create_version_directories("1.0.0")
        self.assertTrue(results["docs/libs"])
        self.assertTrue(results["docs/reports"])
        
        base = Path(self.temp_dir)
        self.assertTrue((base / "docs/libs/v1.0.0").exists())
        self.assertTrue((base / "docs/reports/v1.0.0").exists())
    
    def test_create_version_directories_invalid_version(self):
        with self.assertRaises(ValueError):
            self.manager.create_version_directories("invalid")


class TestPathConfigManagerSelfIterationMode(unittest.TestCase):
    def test_init_without_skill_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                manager = PathConfigManager(mode=PathMode.SELF_ITERATION)
                base_path = manager.get_base_path()
                base_str = str(base_path).replace("\\", "/")
                self.assertIn(".trae/skills/sanliu", base_str)
            finally:
                os.chdir(original_cwd)
    
    def test_guide_project_mode_requires_target_root(self):
        with self.assertRaises(ValueError):
            PathConfigManager(mode=PathMode.GUIDE_PROJECT)


class TestPathConfigManagerVersionFile(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=self.temp_dir
        )
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_version_file_creation(self):
        version = self.manager.get_current_version()
        version_file = Path(self.temp_dir) / "version.json"
        
        self.assertTrue(version_file.exists())
        
        with open(version_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data["version"], version)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
    
    def test_version_file_update(self):
        self.manager.set_version("1.0.0")
        self.manager.set_version("2.0.0")
        
        version_file = Path(self.temp_dir) / "version.json"
        with open(version_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data["version"], "2.0.0")
    
    def test_read_existing_version_file(self):
        version_file = Path(self.temp_dir) / "version.json"
        version_file.parent.mkdir(parents=True, exist_ok=True)
        
        test_data = {
            "version": "3.0.0",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00"
        }
        
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        manager2 = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=self.temp_dir
        )
        
        self.assertEqual(manager2.get_current_version(), "3.0.0")


class TestPathConfigManagerCustomConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.custom_config = PathConfig(
            docs_libs_path="custom/libs",
            docs_reports_path="custom/reports",
            tests_path="custom/tests",
            skillscripts_path="custom/scripts",
            version_file="my_version.json"
        )
        self.manager = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=self.temp_dir,
            config=self.custom_config
        )
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_custom_docs_libs_path(self):
        path = self.manager.get_docs_libs_path()
        expected = Path(self.temp_dir) / "custom/libs"
        self.assertEqual(path, expected)
    
    def test_custom_docs_reports_path(self):
        path = self.manager.get_docs_reports_path()
        expected = Path(self.temp_dir) / "custom/reports"
        self.assertEqual(path, expected)
    
    def test_custom_tests_path(self):
        path = self.manager.get_tests_path()
        expected = Path(self.temp_dir) / "custom/tests"
        self.assertEqual(path, expected)
    
    def test_custom_skillscripts_path(self):
        path = self.manager.get_skillscripts_path()
        expected = Path(self.temp_dir) / "custom/scripts"
        self.assertEqual(path, expected)
    
    def test_custom_version_file(self):
        self.manager.get_current_version()
        version_file = Path(self.temp_dir) / "my_version.json"
        self.assertTrue(version_file.exists())


class TestVersionValidation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=self.temp_dir
        )
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_valid_semantic_version(self):
        valid_versions = [
            "1.0.0",
            "v1.0.0",
            "2.3.4",
            "v2.3.4",
            "0.0.1",
            "10.20.30",
            "1.0.0-alpha",
            "1.0.0-beta.1",
            "v1.0.0-rc.1"
        ]
        
        for version in valid_versions:
            with self.subTest(version=version):
                self.assertTrue(self.manager._validate_version(version))
    
    def test_invalid_version(self):
        invalid_versions = [
            "invalid",
            "1",
            "1.0",
            "1.0.0.0",
            "v",
            "",
            "version1.0.0",
            "1.0.0 "
        ]
        
        for version in invalid_versions:
            with self.subTest(version=version):
                self.assertFalse(self.manager._validate_version(version))


class TestEnvironmentVariableDetector(unittest.TestCase):
    def test_detect_mode_from_env_self_iteration(self):
        with patch.dict(os.environ, {'SANLIU_MODE': 'self_iteration'}):
            mode, target = EnvironmentVariableDetector.detect_mode_from_env()
            self.assertEqual(mode, PathMode.SELF_ITERATION)
            self.assertIsNone(target)
    
    def test_detect_mode_from_env_guide_project(self):
        with patch.dict(os.environ, {
            'SANLIU_MODE': 'guide_project',
            'SANLIU_TARGET_ROOT': '/tmp/test'
        }):
            mode, target = EnvironmentVariableDetector.detect_mode_from_env()
            self.assertEqual(mode, PathMode.GUIDE_PROJECT)
            self.assertEqual(target, '/tmp/test')
    
    def test_detect_mode_from_env_missing_target(self):
        with patch.dict(os.environ, {'SANLIU_MODE': 'guide_project'}, clear=False):
            if 'SANLIU_TARGET_ROOT' in os.environ:
                del os.environ['SANLIU_TARGET_ROOT']
            mode, target = EnvironmentVariableDetector.detect_mode_from_env()
            self.assertIsNone(mode)
    
    def test_detect_mode_from_env_empty(self):
        with patch.dict(os.environ, {}, clear=False):
            for key in ['SANLIU_MODE', 'SANLIU_TARGET_ROOT']:
                if key in os.environ:
                    del os.environ[key]
            mode, target = EnvironmentVariableDetector.detect_mode_from_env()
            self.assertIsNone(mode)
    
    def test_get_all_env_info(self):
        with patch.dict(os.environ, {
            'SANLIU_MODE': 'test_mode',
            'SANLIU_TARGET_ROOT': 'test_root'
        }):
            info = EnvironmentVariableDetector.get_all_env_info()
            self.assertEqual(info['mode'], 'test_mode')
            self.assertEqual(info['target_root'], 'test_root')


class TestConfigFileDetector(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_find_config_file_json(self):
        config_file = Path(self.temp_dir) / ".sanliu.json"
        config_file.write_text('{"mode": "self_iteration"}', encoding='utf-8')
        
        result = ConfigFileDetector.find_config_file(Path(self.temp_dir))
        self.assertEqual(result, config_file)
    
    def test_find_config_file_yaml(self):
        config_file = Path(self.temp_dir) / ".sanliu.yaml"
        config_file.write_text('mode: self_iteration', encoding='utf-8')
        
        result = ConfigFileDetector.find_config_file(Path(self.temp_dir))
        self.assertEqual(result, config_file)
    
    def test_load_config_json(self):
        config_file = Path(self.temp_dir) / ".sanliu.json"
        config_file.write_text('{"mode": "guide_project", "target_root": "/tmp/test"}', encoding='utf-8')
        
        config = ConfigFileDetector.load_config(config_file)
        self.assertEqual(config['mode'], 'guide_project')
        self.assertEqual(config['target_root'], '/tmp/test')
    
    def test_detect_mode_from_config(self):
        config_file = Path(self.temp_dir) / ".sanliu.json"
        config_file.write_text('{"mode": "self_iteration"}', encoding='utf-8')
        
        mode, target, path = ConfigFileDetector.detect_mode_from_config(Path(self.temp_dir))
        self.assertEqual(mode, PathMode.SELF_ITERATION)
        self.assertIsNone(target)
        self.assertEqual(path, config_file)
    
    def test_simple_yaml_parse(self):
        yaml_content = """
mode: self_iteration
target_root: /tmp/test
debug: true
count: 42
"""
        result = ConfigFileDetector._simple_yaml_parse(yaml_content)
        self.assertEqual(result['mode'], 'self_iteration')
        self.assertEqual(result['target_root'], '/tmp/test')
        self.assertEqual(result['debug'], True)
        self.assertEqual(result['count'], 42)


class TestCommandLineDetector(unittest.TestCase):
    def test_detect_mode_from_args_explicit(self):
        args = ['--mode', 'self_iteration']
        mode, target = CommandLineDetector.detect_mode_from_args(args)
        self.assertEqual(mode, PathMode.SELF_ITERATION)
    
    def test_detect_mode_from_args_with_target(self):
        args = ['--mode', 'guide_project', '--target-root', '/tmp/test']
        mode, target = CommandLineDetector.detect_mode_from_args(args)
        self.assertEqual(mode, PathMode.GUIDE_PROJECT)
        self.assertEqual(target, '/tmp/test')
    
    def test_detect_mode_from_args_equals_syntax(self):
        args = ['--mode=guide_project', '--target-root=/tmp/test']
        mode, target = CommandLineDetector.detect_mode_from_args(args)
        self.assertEqual(mode, PathMode.GUIDE_PROJECT)
        self.assertEqual(target, '/tmp/test')
    
    def test_detect_mode_from_args_short_options(self):
        args = ['-m', 'self_iteration', '-t', '/tmp/test']
        mode, target = CommandLineDetector.detect_mode_from_args(args)
        self.assertEqual(mode, PathMode.SELF_ITERATION)
        self.assertEqual(target, '/tmp/test')
    
    def test_detect_mode_from_args_empty(self):
        mode, target = CommandLineDetector.detect_mode_from_args([])
        self.assertIsNone(mode)


class TestModeAutoDetector(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_detect_from_command_line(self):
        result = ModeAutoDetector.detect(
            start_path=Path(self.temp_dir),
            args=['--mode', 'self_iteration']
        )
        self.assertEqual(result.detected_mode, PathMode.SELF_ITERATION)
        self.assertEqual(result.source, ModeDetectionSource.COMMAND_LINE)
    
    def test_detect_priority_command_line_over_env(self):
        with patch.dict(os.environ, {'SANLIU_MODE': 'guide_project'}):
            result = ModeAutoDetector.detect(
                start_path=Path(self.temp_dir),
                args=['--mode', 'self_iteration']
            )
            self.assertEqual(result.detected_mode, PathMode.SELF_ITERATION)
            self.assertEqual(result.source, ModeDetectionSource.COMMAND_LINE)


class TestPathValidator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_exists_true(self):
        valid, error = PathValidator.validate_exists(Path(self.temp_dir))
        self.assertTrue(valid)
        self.assertIsNone(error)
    
    def test_validate_exists_false(self):
        valid, error = PathValidator.validate_exists(Path("/nonexistent/path"))
        self.assertFalse(valid)
        self.assertIsNotNone(error)
    
    def test_validate_is_directory_true(self):
        valid, error = PathValidator.validate_is_directory(Path(self.temp_dir))
        self.assertTrue(valid)
    
    def test_validate_is_directory_false(self):
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("test", encoding='utf-8')
        valid, error = PathValidator.validate_is_directory(test_file)
        self.assertFalse(valid)
    
    def test_validate_writable_true(self):
        valid, error = PathValidator.validate_writable(Path(self.temp_dir))
        self.assertTrue(valid)
    
    def test_validate_all(self):
        valid, errors = PathValidator.validate_all(
            Path(self.temp_dir),
            must_exist=True,
            must_be_dir=True,
            must_be_writable=True
        )
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)


class TestSwitchHistoryManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SwitchHistoryManager(Path(self.temp_dir))
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_record_switch(self):
        record = ModeSwitchRecord(
            from_mode=PathMode.SELF_ITERATION,
            to_mode=PathMode.GUIDE_PROJECT,
            timestamp="2024-01-01T00:00:00",
            from_path="/old/path",
            to_path="/new/path",
            success=True
        )
        result = self.manager.record_switch(record)
        self.assertTrue(result)
    
    def test_get_history(self):
        record = ModeSwitchRecord(
            from_mode=PathMode.SELF_ITERATION,
            to_mode=PathMode.GUIDE_PROJECT,
            timestamp="2024-01-01T00:00:00",
            from_path="/old/path",
            to_path="/new/path",
            success=True
        )
        self.manager.record_switch(record)
        
        history = self.manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['from_mode'], 'self_iteration')
    
    def test_get_last_successful_switch(self):
        record1 = ModeSwitchRecord(
            from_mode=PathMode.SELF_ITERATION,
            to_mode=PathMode.GUIDE_PROJECT,
            timestamp="2024-01-01T00:00:00",
            from_path="/old/path",
            to_path="/new/path",
            success=False
        )
        record2 = ModeSwitchRecord(
            from_mode=PathMode.SELF_ITERATION,
            to_mode=PathMode.GUIDE_PROJECT,
            timestamp="2024-01-02T00:00:00",
            from_path="/old/path",
            to_path="/new/path",
            success=True
        )
        self.manager.record_switch(record1)
        self.manager.record_switch(record2)
        
        last = self.manager.get_last_successful_switch()
        self.assertIsNotNone(last)
        self.assertEqual(last['timestamp'], "2024-01-02T00:00:00")


class TestConcurrentAccess(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=self.temp_dir
        )
        self.errors = []
        self.results = []
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_concurrent_version_read(self):
        def read_version():
            try:
                for _ in range(10):
                    version = self.manager.get_current_version()
                    self.results.append(version)
                    time.sleep(0.001)
            except Exception as e:
                self.errors.append(e)
        
        threads = [threading.Thread(target=read_version) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(len(self.errors), 0)
        self.assertEqual(len(self.results), 50)
    
    def test_concurrent_ensure_directories(self):
        def create_dirs():
            try:
                for _ in range(5):
                    self.manager.ensure_directories()
                    time.sleep(0.001)
            except Exception as e:
                self.errors.append(e)
        
        threads = [threading.Thread(target=create_dirs) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(len(self.errors), 0)


class TestErrorRecovery(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=self.temp_dir
        )
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_switch_mode_with_invalid_path(self):
        with self.assertRaises(ModeSwitchError):
            self.manager.switch_mode(PathMode.GUIDE_PROJECT, "/nonexistent/path")
        
        self.assertEqual(self.manager.mode, PathMode.GUIDE_PROJECT)
    
    def test_rollback_after_failed_switch(self):
        original_mode = self.manager.mode
        original_path = self.manager.get_base_path()
        
        with self.assertRaises(ModeSwitchError):
            self.manager.switch_mode(PathMode.GUIDE_PROJECT, "/nonexistent/path")
        
        self.assertEqual(self.manager.mode, original_mode)
    
    def test_get_versioned_path_empty_version(self):
        with self.assertRaises(PathValidationError):
            self.manager.get_versioned_path("docs/libs", "")


class TestBoundaryConditions(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_empty_target_root_guide_project(self):
        with self.assertRaises(PathConfigError):
            PathConfigManager(mode=PathMode.GUIDE_PROJECT, auto_detect=False)
    
    def test_very_long_path(self):
        long_path = self.temp_dir + "/" + "a" * 200
        manager = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=self.temp_dir
        )
        result = manager.resolve_path("a" * 200)
        self.assertIn("a" * 200, str(result))
    
    def test_special_characters_in_version(self):
        manager = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=self.temp_dir
        )
        self.assertFalse(manager._validate_version("1.0.0@special"))
        self.assertTrue(manager._validate_version("1.0.0-alpha"))
    
    def test_unicode_path(self):
        unicode_dir = Path(self.temp_dir) / "测试目录"
        unicode_dir.mkdir()
        
        manager = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=str(unicode_dir)
        )
        
        self.assertTrue(manager.get_base_path().exists())
    
    def test_list_versions_empty(self):
        manager = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=self.temp_dir
        )
        versions = manager.list_versions()
        self.assertEqual(versions, [])
    
    def test_path_info_completeness(self):
        manager = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=self.temp_dir
        )
        info = manager.get_path_info()
        
        required_keys = ['mode', 'mode_description', 'base_path', 'current_version', 'paths']
        for key in required_keys:
            self.assertIn(key, info)
    
    def test_mode_info_completeness(self):
        manager = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=self.temp_dir
        )
        info = manager.get_mode_info()
        
        required_keys = ['current_mode', 'mode_description', 'base_path', 'target_root', 'paths_config']
        for key in required_keys:
            self.assertIn(key, info)


class TestEnhancedDetectionIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_manager_with_env_detection(self):
        with patch.dict(os.environ, {'SANLIU_MODE': 'self_iteration'}):
            manager = PathConfigManager(auto_detect=True)
            self.assertEqual(manager.mode, PathMode.SELF_ITERATION)
    
    def test_manager_with_args_detection(self):
        manager = PathConfigManager(
            auto_detect=True,
            detection_args=['--mode', 'self_iteration']
        )
        self.assertEqual(manager.mode, PathMode.SELF_ITERATION)
    
    def test_get_enhanced_detection_info(self):
        manager = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=self.temp_dir
        )
        info = manager.get_enhanced_detection_info()
        self.assertIsNotNone(info)
        self.assertEqual(info['source'], 'explicit')
    
    def test_paths_config_for_mode(self):
        manager = PathConfigManager(
            mode=PathMode.SELF_ITERATION
        )
        info = manager.get_mode_info()
        self.assertIn('paths_config', info)
        self.assertEqual(info['paths_config']['mode_type'], 'self_iteration')


class TestRollbackMechanism(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PathConfigManager(
            mode=PathMode.GUIDE_PROJECT,
            target_root=self.temp_dir
        )
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_rollback_state_saved(self):
        self.manager._save_rollback_state()
        self.assertIsNotNone(self.manager._rollback_state)
        self.assertEqual(self.manager._rollback_state['mode'], PathMode.GUIDE_PROJECT)
    
    def test_rollback_state_restored(self):
        self.manager._save_rollback_state()
        self.manager.mode = PathMode.SELF_ITERATION
        
        result = self.manager._restore_rollback_state()
        self.assertTrue(result)
        self.assertEqual(self.manager.mode, PathMode.GUIDE_PROJECT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
