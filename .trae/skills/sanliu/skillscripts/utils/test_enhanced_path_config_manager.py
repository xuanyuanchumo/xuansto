#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版路径配置管理器测试

测试所有核心功能：
- 技能根路径配置
- 子技能路径配置
- 脚本路径配置
- 资源路径配置
- 动态路径解析
- 环境变量支持
- 单例模式
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from enhanced_path_config_manager import (
        EnhancedSkillPathManager,
        PathKey,
        SkillPathConfig,
        DirectoryCategory,
        DirectoryStatus,
        EnvironmentVariableManager,
        DirectoryStructureManager,
        DirectoryHealthChecker,
        DirectorySnapshotManager,
        create_path_manager,
        PathConfigError,
        OutputType,
        OutputPathRegistry,
        OutputPathRegistration,
        OutputPathConflict,
        OutputPathValidationResult,
        DocsSubdir,
        PathValidationError
    )
except ImportError:
    from .enhanced_path_config_manager import (
        EnhancedSkillPathManager,
        PathKey,
        SkillPathConfig,
        DirectoryCategory,
        DirectoryStatus,
        EnvironmentVariableManager,
        DirectoryStructureManager,
        DirectoryHealthChecker,
        DirectorySnapshotManager,
        create_path_manager,
        PathConfigError,
        OutputType,
        OutputPathRegistry,
        OutputPathRegistration,
        OutputPathConflict,
        OutputPathValidationResult,
        DocsSubdir,
        PathValidationError
    )


class TestSkillPathConfig(unittest.TestCase):
    """测试 SkillPathConfig 数据类"""
    
    def test_from_skill_root(self):
        """测试从技能根目录创建配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_root = Path(tmpdir)
            config = SkillPathConfig.from_skill_root(skill_root)
            
            self.assertEqual(config.skill_root, skill_root)
            self.assertEqual(config.skill_md, skill_root / "SKILL.md")
            self.assertEqual(config.version_file, skill_root / "version.json")
            self.assertEqual(config.subskills_dir, skill_root / "subskills")
            self.assertEqual(config.scripts_dir, skill_root / "skillscripts")
            self.assertEqual(config.core_scripts_dir, skill_root / "skillscripts" / "core")
            self.assertEqual(config.resources_dir, skill_root / "resources")
            self.assertEqual(config.templates_dir, skill_root / "resources" / "templates")
    
    def test_to_dict(self):
        """测试转换为字典"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_root = Path(tmpdir)
            config = SkillPathConfig.from_skill_root(skill_root)
            config_dict = config.to_dict()
            
            self.assertIsInstance(config_dict, dict)
            self.assertEqual(config_dict["skill_root"], str(skill_root))
            self.assertIn("subskills_dir", config_dict)
            self.assertIn("scripts_dir", config_dict)


class TestEnvironmentVariableManager(unittest.TestCase):
    """测试环境变量管理器"""
    
    def test_get_env_override_not_set(self):
        """测试环境变量未设置时的行为"""
        env_value = EnvironmentVariableManager.get_env_override(PathKey.SKILL_ROOT)
        self.assertIsNone(env_value)
    
    def test_get_env_override_set(self):
        """测试环境变量设置时的行为"""
        test_path = "/test/skill/root"
        with patch.dict(os.environ, {"SANLIU_SKILL_ROOT": test_path}):
            env_value = EnvironmentVariableManager.get_env_override(PathKey.SKILL_ROOT)
            self.assertEqual(env_value, Path(test_path))
    
    def test_set_env_override(self):
        """测试设置环境变量"""
        test_path = "/test/path"
        EnvironmentVariableManager.set_env_override(PathKey.DATA_DIR, test_path)
        
        self.assertEqual(os.environ.get("SANLIU_DATA_DIR"), test_path)
        
        EnvironmentVariableManager.clear_env_override(PathKey.DATA_DIR)
    
    def test_get_all_env_overrides(self):
        """测试获取所有环境变量覆盖"""
        with patch.dict(os.environ, {
            "SANLIU_SKILL_ROOT": "/root",
            "SANLIU_DATA_DIR": "/data"
        }):
            overrides = EnvironmentVariableManager.get_all_env_overrides()
            
            self.assertIn("skill_root", overrides)
            self.assertIn("data_dir", overrides)
            self.assertEqual(overrides["skill_root"], "/root")
            self.assertEqual(overrides["data_dir"], "/data")


class TestEnhancedSkillPathManager(unittest.TestCase):
    """测试增强版技能路径管理器"""
    
    def setUp(self):
        """测试前准备"""
        EnhancedSkillPathManager.reset_instance()
        self.temp_dir = tempfile.mkdtemp()
        self.skill_root = Path(self.temp_dir) / ".trae" / "skills" / "sanliu"
        self.skill_root.mkdir(parents=True, exist_ok=True)
        
        (self.skill_root / "skillscripts").mkdir(exist_ok=True)
        (self.skill_root / "subskills").mkdir(exist_ok=True)
        (self.skill_root / "resources").mkdir(exist_ok=True)
    
    def tearDown(self):
        """测试后清理"""
        EnhancedSkillPathManager.reset_instance()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        manager2 = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        self.assertIs(manager1, manager2)
    
    def test_resolve_path(self):
        """测试路径解析"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        skill_root_path = manager.resolve_path(PathKey.SKILL_ROOT)
        self.assertEqual(skill_root_path, self.skill_root)
        
        subskills_path = manager.resolve_path(PathKey.SUBSKILLS_DIR)
        self.assertEqual(subskills_path, self.skill_root / "subskills")
    
    def test_resolve_path_with_string(self):
        """测试字符串路径解析"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        path = manager.resolve_path("custom/path")
        self.assertEqual(path, self.skill_root / "custom/path")
    
    def test_get_relative_path(self):
        """测试获取相对路径"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        absolute_path = self.skill_root / "subskills" / "test.md"
        relative_path = manager.get_relative_path(absolute_path)
        
        expected_relative = str(Path("subskills/test.md"))
        self.assertEqual(relative_path.replace("\\", "/"), "subskills/test.md")
    
    def test_to_absolute_path(self):
        """测试转换为绝对路径"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        absolute_path = manager.to_absolute_path("subskills/test.md")
        self.assertEqual(absolute_path, self.skill_root / "subskills" / "test.md")
    
    def test_validate_path(self):
        """测试路径验证"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        valid, error = manager.validate_path(self.skill_root)
        self.assertTrue(valid)
        self.assertIsNone(error)
        
        non_existent_path = self.skill_root / "non_existent"
        valid, error = manager.validate_path(non_existent_path)
        self.assertFalse(valid)
        self.assertIsNotNone(error)
    
    def test_ensure_path(self):
        """测试确保路径存在"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        new_path_key = PathKey.DATA_DIR
        new_path = manager.ensure_path(new_path_key)
        
        self.assertTrue(new_path.exists())
        self.assertTrue(new_path.is_dir())
    
    def test_get_subskill_path(self):
        """测试获取子技能路径"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        subskill_path = manager.get_subskill_path("test_skill")
        expected_path = self.skill_root / "subskills" / "test_skill.md"
        
        self.assertEqual(subskill_path, expected_path)
    
    def test_get_all_subskills(self):
        """测试获取所有子技能"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        subskill_file = self.skill_root / "subskills" / "test_skill.md"
        subskill_file.write_text("# Test Skill")
        
        subskills = manager.get_all_subskills()
        
        self.assertEqual(len(subskills), 1)
        self.assertEqual(subskills[0].name, "test_skill")
        self.assertTrue(subskills[0].exists)
    
    def test_get_script_path(self):
        """测试获取脚本路径"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        script_path = manager.get_script_path("test_script", "core")
        expected_path = self.skill_root / "skillscripts" / "core" / "test_script.py"
        
        self.assertEqual(script_path, expected_path)
        
        script_path = manager.get_script_path("test_script", "utils")
        expected_path = self.skill_root / "skillscripts" / "utils" / "test_script.py"
        
        self.assertEqual(script_path, expected_path)
    
    def test_get_template_path(self):
        """测试获取模板路径"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        template_path = manager.get_template_path("test_template")
        expected_path = self.skill_root / "resources" / "templates" / "test_template.md"
        
        self.assertEqual(template_path, expected_path)
    
    def test_get_report_path(self):
        """测试获取报告路径"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        report_path = manager.get_report_path("test_report")
        expected_path = self.skill_root / "reports" / "test_report.md"
        
        self.assertEqual(report_path, expected_path)
    
    def test_initialize_workspace(self):
        """测试初始化工作空间"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        result = manager.initialize_workspace(verify=True, lazy=True)
        
        self.assertIn("skill_root", result)
        self.assertEqual(result["skill_root"], str(self.skill_root))
        self.assertTrue(result["lazy_mode"])
    
    def test_validate_workspace(self):
        """测试验证工作空间"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        result = manager.validate_workspace()
        
        self.assertIn("valid", result)
        self.assertIn("errors", result)
        self.assertIn("warnings", result)
        self.assertIn("checks", result)
    
    def test_get_workspace_info(self):
        """测试获取工作空间信息"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        info = manager.get_workspace_info()
        
        self.assertEqual(info["skill_root"], str(self.skill_root))
        self.assertIn("path_config", info)
        self.assertIn("health_score", info)
        self.assertIn("subskills_count", info)
    
    def test_export_config(self):
        """测试导出配置"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        config_file = Path(self.temp_dir) / "config.json"
        config = manager.export_config(config_file)
        
        self.assertTrue(config_file.exists())
        self.assertIn("skill_root", config)
        self.assertEqual(config["skill_root"], str(self.skill_root))
        
        with open(config_file, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
        
        self.assertEqual(loaded_config["skill_root"], str(self.skill_root))
    
    def test_reload_config(self):
        """测试重新加载配置"""
        manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
        
        reloaded = manager.reload_config(force=True)
        self.assertTrue(reloaded)
        
        reloaded = manager.reload_config(force=False)
        self.assertFalse(reloaded)


class TestDirectoryStructureManager(unittest.TestCase):
    """测试目录结构管理器"""
    
    def setUp(self):
        """测试前准备"""
        EnhancedSkillPathManager.reset_instance()
        self.temp_dir = tempfile.mkdtemp()
        self.skill_root = Path(self.temp_dir) / ".trae" / "skills" / "sanliu"
        self.skill_root.mkdir(parents=True, exist_ok=True)
        
        (self.skill_root / "skillscripts").mkdir(exist_ok=True)
        (self.skill_root / "subskills").mkdir(exist_ok=True)
        (self.skill_root / "resources").mkdir(exist_ok=True)
        
        self.manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
    
    def tearDown(self):
        """测试后清理"""
        EnhancedSkillPathManager.reset_instance()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_directory_structure_lazy(self):
        """测试懒加载创建目录结构"""
        result = self.manager.structure_manager.create_directory_structure(lazy=True)
        
        self.assertTrue(result["lazy"])
        self.assertIn("懒加载模式已启用", result["skipped"][0])
    
    def test_verify_structure(self):
        """测试验证目录结构"""
        result = self.manager.structure_manager.verify_structure()
        
        self.assertIn("valid", result)
        self.assertIn("missing", result)
        self.assertIn("warnings", result)
    
    def test_get_directory_status(self):
        """测试获取目录状态"""
        status = self.manager.structure_manager.get_directory_status("subskills")
        
        self.assertEqual(status["relative_path"], "subskills")
        self.assertTrue(status["exists"])
        self.assertEqual(status["status"], DirectoryStatus.EXISTS.value)
    
    def test_ensure_directory(self):
        """测试确保目录存在"""
        new_dir = self.skill_root / "new_directory"
        
        result = self.manager.structure_manager.ensure_directory(new_dir)
        
        self.assertTrue(result.exists())
        self.assertEqual(result, new_dir)


class TestDirectoryHealthChecker(unittest.TestCase):
    """测试目录健康检查器"""
    
    def setUp(self):
        """测试前准备"""
        EnhancedSkillPathManager.reset_instance()
        self.temp_dir = tempfile.mkdtemp()
        self.skill_root = Path(self.temp_dir) / ".trae" / "skills" / "sanliu"
        self.skill_root.mkdir(parents=True, exist_ok=True)
        
        (self.skill_root / "skillscripts").mkdir(exist_ok=True)
        (self.skill_root / "subskills").mkdir(exist_ok=True)
        (self.skill_root / "resources").mkdir(exist_ok=True)
        
        self.manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
    
    def tearDown(self):
        """测试后清理"""
        EnhancedSkillPathManager.reset_instance()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_perform_health_check(self):
        """测试执行健康检查"""
        report = self.manager.health_checker.perform_health_check()
        
        self.assertEqual(report.base_path, str(self.skill_root))
        self.assertGreaterEqual(report.health_score, 0.0)
        self.assertLessEqual(report.health_score, 100.0)
        self.assertIsNotNone(report.timestamp)


class TestDirectorySnapshotManager(unittest.TestCase):
    """测试目录快照管理器"""
    
    def setUp(self):
        """测试前准备"""
        EnhancedSkillPathManager.reset_instance()
        self.temp_dir = tempfile.mkdtemp()
        self.skill_root = Path(self.temp_dir) / ".trae" / "skills" / "sanliu"
        self.skill_root.mkdir(parents=True, exist_ok=True)
        
        (self.skill_root / "skillscripts").mkdir(exist_ok=True)
        (self.skill_root / "subskills").mkdir(exist_ok=True)
        (self.skill_root / "resources").mkdir(exist_ok=True)
        
        self.manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
    
    def tearDown(self):
        """测试后清理"""
        EnhancedSkillPathManager.reset_instance()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_snapshot(self):
        """测试创建快照"""
        snapshot = self.manager.snapshot_manager.create_snapshot()
        
        self.assertIsNotNone(snapshot.snapshot_id)
        self.assertEqual(snapshot.base_path, str(self.skill_root))
        self.assertGreaterEqual(snapshot.file_count, 0)
    
    def test_list_snapshots(self):
        """测试列出快照"""
        self.manager.snapshot_manager.create_snapshot("test_snap_1")
        self.manager.snapshot_manager.create_snapshot("test_snap_2")
        
        snapshots = self.manager.snapshot_manager.list_snapshots()
        
        self.assertGreaterEqual(len(snapshots), 2)
    
    def test_load_snapshot(self):
        """测试加载快照"""
        snapshot_id = "test_load_snap"
        self.manager.snapshot_manager.create_snapshot(snapshot_id)
        
        loaded = self.manager.snapshot_manager.load_snapshot(snapshot_id)
        
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.snapshot_id, snapshot_id)


class TestCreatePathManager(unittest.TestCase):
    """测试便捷函数"""
    
    def setUp(self):
        """测试前准备"""
        EnhancedSkillPathManager.reset_instance()
        self.temp_dir = tempfile.mkdtemp()
        self.skill_root = Path(self.temp_dir) / ".trae" / "skills" / "sanliu"
        self.skill_root.mkdir(parents=True, exist_ok=True)
        
        (self.skill_root / "skillscripts").mkdir(exist_ok=True)
        (self.skill_root / "subskills").mkdir(exist_ok=True)
        (self.skill_root / "resources").mkdir(exist_ok=True)
    
    def tearDown(self):
        """测试后清理"""
        EnhancedSkillPathManager.reset_instance()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_path_manager(self):
        """测试创建路径管理器"""
        manager = create_path_manager(skill_root=self.skill_root, auto_detect=False)
        
        self.assertIsInstance(manager, EnhancedSkillPathManager)
        self.assertEqual(manager.skill_root, self.skill_root)


class TestOutputType(unittest.TestCase):
    """测试 OutputType 枚举"""
    
    def test_output_type_values(self):
        """测试输出类型枚举值"""
        self.assertEqual(OutputType.REPORT.value, "report")
        self.assertEqual(OutputType.LOG.value, "log")
        self.assertEqual(OutputType.TEMP.value, "temp")
        self.assertEqual(OutputType.CACHE.value, "cache")
        self.assertEqual(OutputType.DATA.value, "data")
        self.assertEqual(OutputType.BACKUP.value, "backup")
        self.assertEqual(OutputType.EXPORT.value, "export")
        self.assertEqual(OutputType.DOWNLOAD.value, "download")
        self.assertEqual(OutputType.UPLOAD.value, "upload")
        self.assertEqual(OutputType.SNAPSHOT.value, "snapshot")


class TestOutputPathRegistry(unittest.TestCase):
    """测试输出路径注册器"""
    
    def setUp(self):
        """测试前准备"""
        self.registry = OutputPathRegistry()
    
    def test_register_output_path(self):
        """测试注册输出路径"""
        path = Path("/tmp/test_output")
        registration_id = self.registry.register(
            script_name="test_script",
            output_type=OutputType.TEMP,
            path=path,
            description="测试输出路径"
        )
        
        self.assertIsNotNone(registration_id)
        self.assertIn(registration_id, self.registry._registrations)
    
    def test_unregister_output_path(self):
        """测试取消注册"""
        path = Path("/tmp/test_output")
        registration_id = self.registry.register(
            script_name="test_script",
            output_type=OutputType.TEMP,
            path=path
        )
        
        result = self.registry.unregister(registration_id)
        self.assertTrue(result)
        self.assertNotIn(registration_id, self.registry._registrations)
    
    def test_check_conflicts_no_conflict(self):
        """测试无冲突情况"""
        self.registry.register(
            script_name="script1",
            output_type=OutputType.TEMP,
            path=Path("/tmp/output1")
        )
        self.registry.register(
            script_name="script2",
            output_type=OutputType.TEMP,
            path=Path("/tmp/output2")
        )
        
        conflicts = self.registry.check_conflicts()
        self.assertEqual(len(conflicts), 0)
    
    def test_check_conflicts_with_conflict(self):
        """测试有冲突情况"""
        path = Path("/tmp/shared_output")
        self.registry.register(
            script_name="script1",
            output_type=OutputType.TEMP,
            path=path
        )
        self.registry.register(
            script_name="script2",
            output_type=OutputType.TEMP,
            path=path
        )
        
        conflicts = self.registry.check_conflicts()
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, "shared_path")
    
    def test_check_conflicts_exclusive_violation(self):
        """测试独占路径冲突"""
        path = Path("/tmp/exclusive_output")
        self.registry.register(
            script_name="script1",
            output_type=OutputType.TEMP,
            path=path,
            exclusive=True
        )
        self.registry.register(
            script_name="script2",
            output_type=OutputType.TEMP,
            path=path
        )
        
        conflicts = self.registry.check_conflicts()
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, "exclusive_violation")
        self.assertEqual(conflicts[0].severity, "high")
    
    def test_get_registrations_by_script(self):
        """测试按脚本获取注册"""
        self.registry.register(
            script_name="script1",
            output_type=OutputType.TEMP,
            path=Path("/tmp/output1")
        )
        self.registry.register(
            script_name="script1",
            output_type=OutputType.LOG,
            path=Path("/tmp/logs")
        )
        self.registry.register(
            script_name="script2",
            output_type=OutputType.TEMP,
            path=Path("/tmp/output2")
        )
        
        registrations = self.registry.get_registrations_by_script("script1")
        self.assertEqual(len(registrations), 2)
    
    def test_get_registrations_by_path(self):
        """测试按路径获取注册"""
        path = Path("/tmp/shared")
        self.registry.register(
            script_name="script1",
            output_type=OutputType.TEMP,
            path=path
        )
        self.registry.register(
            script_name="script2",
            output_type=OutputType.LOG,
            path=path
        )
        
        registrations = self.registry.get_registrations_by_path(path)
        self.assertEqual(len(registrations), 2)


class TestOutputPathManagement(unittest.TestCase):
    """测试输出路径管理功能"""
    
    def setUp(self):
        """测试前准备"""
        EnhancedSkillPathManager.reset_instance()
        self.temp_dir = tempfile.mkdtemp()
        self.skill_root = Path(self.temp_dir) / ".trae" / "skills" / "sanliu"
        self.skill_root.mkdir(parents=True, exist_ok=True)
        
        (self.skill_root / "skillscripts").mkdir(exist_ok=True)
        (self.skill_root / "subskills").mkdir(exist_ok=True)
        (self.skill_root / "resources").mkdir(exist_ok=True)
        (self.skill_root / "reports").mkdir(exist_ok=True)
        (self.skill_root / "logs").mkdir(exist_ok=True)
        (self.skill_root / "temp").mkdir(exist_ok=True)
        
        self.manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
    
    def tearDown(self):
        """测试后清理"""
        EnhancedSkillPathManager.reset_instance()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_output_path_report(self):
        """测试获取报告输出路径"""
        path = self.manager.get_output_path(OutputType.REPORT)
        
        self.assertIsInstance(path, Path)
        self.assertEqual(path.name, "reports")
    
    def test_get_output_path_with_filename(self):
        """测试获取带文件名的输出路径"""
        path = self.manager.get_output_path(
            OutputType.REPORT,
            filename="test_report.md"
        )
        
        self.assertEqual(path.name, "test_report.md")
        self.assertEqual(path.parent.name, "reports")
    
    def test_get_output_path_with_subdirectory(self):
        """测试获取带子目录的输出路径"""
        path = self.manager.get_output_path(
            OutputType.LOG,
            subdirectory="app",
            filename="app.log"
        )
        
        self.assertEqual(path.name, "app.log")
        self.assertEqual(path.parent.name, "app")
    
    def test_get_output_path_with_env_override(self):
        """测试环境变量覆盖输出路径"""
        custom_path = Path(self.temp_dir) / "custom_output"
        custom_path.mkdir(exist_ok=True)
        
        with patch.dict(os.environ, {"SANLIU_OUTPUT_REPORT": str(custom_path)}):
            path = self.manager.get_output_path(OutputType.REPORT)
            self.assertEqual(path, custom_path)
    
    def test_get_output_path_with_registration(self):
        """测试获取输出路径并注册"""
        path = self.manager.get_output_path(
            OutputType.TEMP,
            filename="test_temp.json",
            script_name="test_script",
            register=True
        )
        
        registrations = self.manager.get_output_path_registrations(script_name="test_script")
        self.assertEqual(len(registrations), 1)
        self.assertEqual(registrations[0].output_type, OutputType.TEMP)
    
    def test_validate_output_paths(self):
        """测试验证输出路径"""
        result = self.manager.validate_output_paths()
        
        self.assertIn("valid", result)
        self.assertIn("results", result)
        self.assertIn("errors", result)
        self.assertIn("warnings", result)
    
    def test_validate_output_paths_specific_types(self):
        """测试验证特定输出类型"""
        result = self.manager.validate_output_paths(
            output_types=[OutputType.REPORT, OutputType.LOG]
        )
        
        self.assertIn("report", result["results"])
        self.assertIn("log", result["results"])
        self.assertNotIn("temp", result["results"])
    
    def test_register_output_path(self):
        """测试注册输出路径"""
        registration_id = self.manager.register_output_path(
            script_name="test_script",
            output_type=OutputType.TEMP,
            filename="test.json",
            description="测试注册"
        )
        
        self.assertIsNotNone(registration_id)
        
        registrations = self.manager.get_output_path_registrations(script_name="test_script")
        self.assertEqual(len(registrations), 1)
    
    def test_check_output_path_conflicts(self):
        """测试检查输出路径冲突"""
        self.manager.register_output_path(
            script_name="script1",
            output_type=OutputType.TEMP,
            filename="shared.json"
        )
        self.manager.register_output_path(
            script_name="script2",
            output_type=OutputType.TEMP,
            filename="shared.json"
        )
        
        conflicts = self.manager.check_output_path_conflicts()
        self.assertGreater(len(conflicts), 0)
    
    def test_get_output_path_registrations(self):
        """测试获取输出路径注册"""
        self.manager.register_output_path(
            script_name="script1",
            output_type=OutputType.TEMP,
            filename="temp1.json"
        )
        self.manager.register_output_path(
            script_name="script1",
            output_type=OutputType.LOG,
            filename="log1.txt"
        )
        self.manager.register_output_path(
            script_name="script2",
            output_type=OutputType.TEMP,
            filename="temp2.json"
        )
        
        all_regs = self.manager.get_output_path_registrations()
        self.assertEqual(len(all_regs), 3)
        
        script1_regs = self.manager.get_output_path_registrations(script_name="script1")
        self.assertEqual(len(script1_regs), 2)
        
        temp_regs = self.manager.get_output_path_registrations(output_type=OutputType.TEMP)
        self.assertEqual(len(temp_regs), 2)


class TestEnvironmentVariableOutputPath(unittest.TestCase):
    """测试输出路径环境变量支持"""
    
    def test_get_output_path_env_not_set(self):
        """测试环境变量未设置"""
        result = EnvironmentVariableManager.get_output_path_env(OutputType.REPORT)
        self.assertIsNone(result)
    
    def test_get_output_path_env_set(self):
        """测试环境变量已设置"""
        test_path = "/custom/output/path"
        with patch.dict(os.environ, {"SANLIU_OUTPUT_REPORT": test_path}):
            result = EnvironmentVariableManager.get_output_path_env(OutputType.REPORT)
            self.assertEqual(result, Path(test_path))
    
    def test_set_output_path_env(self):
        """测试设置输出路径环境变量"""
        test_path = "/test/output/path"
        EnvironmentVariableManager.set_output_path_env(OutputType.LOG, test_path)
        
        self.assertEqual(os.environ.get("SANLIU_OUTPUT_LOG"), test_path)
        EnvironmentVariableManager.clear_output_path_env(OutputType.LOG)
    
    def test_clear_output_path_env(self):
        """测试清除输出路径环境变量"""
        test_path = "/test/output/path"
        EnvironmentVariableManager.set_output_path_env(OutputType.TEMP, test_path)
        EnvironmentVariableManager.clear_output_path_env(OutputType.TEMP)
        
        self.assertIsNone(os.environ.get("SANLIU_OUTPUT_TEMP"))


class TestDocsSubdir(unittest.TestCase):
    """测试 DocsSubdir 枚举"""
    
    def test_docs_subdir_values(self):
        """测试Docs子目录枚举值"""
        self.assertEqual(DocsSubdir.REPORTS.value, "reports")
        self.assertEqual(DocsSubdir.API.value, "api")
        self.assertEqual(DocsSubdir.WORKFLOW.value, "workflow")
        self.assertEqual(DocsSubdir.KNOWLEDGE.value, "knowledge")
        self.assertEqual(DocsSubdir.LIBS.value, "libs")
        self.assertEqual(DocsSubdir.SNAPSHOTS.value, "snapshots")
        self.assertEqual(DocsSubdir.DIFF_REPORTS.value, "diff_reports")


class TestDocsPathManagement(unittest.TestCase):
    """测试Docs路径管理功能"""
    
    def setUp(self):
        """测试前准备"""
        EnhancedSkillPathManager.reset_instance()
        self.temp_dir = tempfile.mkdtemp()
        self.skill_root = Path(self.temp_dir) / ".trae" / "skills" / "sanliu"
        self.skill_root.mkdir(parents=True, exist_ok=True)
        
        (self.skill_root / "skillscripts").mkdir(exist_ok=True)
        (self.skill_root / "subskills").mkdir(exist_ok=True)
        (self.skill_root / "resources").mkdir(exist_ok=True)
        (self.skill_root / "docs").mkdir(exist_ok=True)
        
        self.manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
    
    def tearDown(self):
        """测试后清理"""
        EnhancedSkillPathManager.reset_instance()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_docs_path_root(self):
        """测试获取docs根目录"""
        path = self.manager.get_docs_path()
        
        self.assertEqual(path, self.skill_root / "docs")
        self.assertTrue(path.exists())
    
    def test_get_docs_path_with_subdir(self):
        """测试获取docs子目录"""
        path = self.manager.get_docs_path(DocsSubdir.REPORTS)
        
        expected = self.skill_root / "docs" / "reports"
        self.assertEqual(path, expected)
        self.assertTrue(path.exists())
    
    def test_get_docs_path_with_filename(self):
        """测试获取docs目录下的文件路径"""
        path = self.manager.get_docs_path(DocsSubdir.API, filename="endpoint.md")
        
        expected = self.skill_root / "docs" / "api" / "endpoint.md"
        self.assertEqual(path, expected)
        self.assertTrue(path.parent.exists())
    
    def test_get_docs_path_with_string_subdir(self):
        """测试使用字符串获取docs子目录"""
        path = self.manager.get_docs_path("custom/subdir")
        
        expected = self.skill_root / "docs" / "custom" / "subdir"
        self.assertEqual(path, expected)
        self.assertTrue(path.exists())
    
    def test_get_docs_path_no_create(self):
        """测试不自动创建目录"""
        path = self.manager.get_docs_path(DocsSubdir.WORKFLOW, create_if_missing=False)
        
        self.assertEqual(path, self.skill_root / "docs" / "workflow")
    
    def test_get_docs_path_with_validation(self):
        """测试带验证的docs路径获取"""
        path = self.manager.get_docs_path(DocsSubdir.KNOWLEDGE, validate=True)
        
        self.assertTrue(path.exists())
    
    def test_get_docs_path_with_env_override(self):
        """测试环境变量覆盖docs子目录路径"""
        custom_path = Path(self.temp_dir) / "custom_docs_reports"
        custom_path.mkdir(parents=True, exist_ok=True)
        
        with patch.dict(os.environ, {"SANLIU_DOCS_REPORTS_DIR": str(custom_path)}):
            EnhancedSkillPathManager.reset_instance()
            manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
            path = manager.get_docs_path(DocsSubdir.REPORTS)
            self.assertEqual(path, custom_path)


class TestEnvironmentVariableDocsPath(unittest.TestCase):
    """测试Docs路径环境变量支持"""
    
    def test_get_docs_subdir_env_not_set(self):
        """测试环境变量未设置"""
        result = EnvironmentVariableManager.get_docs_subdir_env(DocsSubdir.REPORTS)
        self.assertIsNone(result)
    
    def test_get_docs_subdir_env_set(self):
        """测试环境变量已设置"""
        test_path = "/custom/docs/reports"
        with patch.dict(os.environ, {"SANLIU_DOCS_REPORTS_DIR": test_path}):
            result = EnvironmentVariableManager.get_docs_subdir_env(DocsSubdir.REPORTS)
            self.assertEqual(result, Path(test_path))
    
    def test_set_docs_subdir_env(self):
        """测试设置docs子目录环境变量"""
        test_path = "/test/docs/api"
        EnvironmentVariableManager.set_docs_subdir_env(DocsSubdir.API, test_path)
        
        self.assertEqual(os.environ.get("SANLIU_DOCS_API_DIR"), test_path)
        EnvironmentVariableManager.clear_docs_subdir_env(DocsSubdir.API)
    
    def test_clear_docs_subdir_env(self):
        """测试清除docs子目录环境变量"""
        test_path = "/test/docs/workflow"
        EnvironmentVariableManager.set_docs_subdir_env(DocsSubdir.WORKFLOW, test_path)
        EnvironmentVariableManager.clear_docs_subdir_env(DocsSubdir.WORKFLOW)
        
        self.assertIsNone(os.environ.get("SANLIU_DOCS_WORKFLOW_DIR"))
    
    def test_get_all_docs_env_overrides(self):
        """测试获取所有docs环境变量覆盖"""
        with patch.dict(os.environ, {
            "SANLIU_DOCS_REPORTS_DIR": "/docs/reports",
            "SANLIU_DOCS_API_DIR": "/docs/api"
        }):
            overrides = EnvironmentVariableManager.get_all_docs_env_overrides()
            
            self.assertIn("reports", overrides)
            self.assertIn("api", overrides)
            self.assertEqual(overrides["reports"], "/docs/reports")
            self.assertEqual(overrides["api"], "/docs/api")


class TestOutputPathValidation(unittest.TestCase):
    """测试输出路径验证功能"""
    
    def setUp(self):
        """测试前准备"""
        EnhancedSkillPathManager.reset_instance()
        self.temp_dir = tempfile.mkdtemp()
        self.skill_root = Path(self.temp_dir) / ".trae" / "skills" / "sanliu"
        self.skill_root.mkdir(parents=True, exist_ok=True)
        
        (self.skill_root / "skillscripts").mkdir(exist_ok=True)
        (self.skill_root / "subskills").mkdir(exist_ok=True)
        (self.skill_root / "resources").mkdir(exist_ok=True)
        (self.skill_root / "docs").mkdir(exist_ok=True)
        (self.skill_root / "reports").mkdir(exist_ok=True)
        (self.skill_root / "temp").mkdir(exist_ok=True)
        
        self.manager = EnhancedSkillPathManager(skill_root=self.skill_root, auto_detect=False)
    
    def tearDown(self):
        """测试后清理"""
        EnhancedSkillPathManager.reset_instance()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_output_path_in_allowed_dirs_valid(self):
        """测试验证路径在允许目录内"""
        docs_path = self.skill_root / "docs" / "test.md"
        result = self.manager.validate_output_path_in_allowed_dirs(docs_path)
        
        self.assertTrue(result["valid"])
        self.assertIsNone(result["error"])
        self.assertIsNotNone(result["matched_dir"])
    
    def test_validate_output_path_in_allowed_dirs_invalid(self):
        """测试验证路径不在允许目录内"""
        invalid_path = Path("/tmp/outside_allowed/test.md")
        result = self.manager.validate_output_path_in_allowed_dirs(invalid_path)
        
        self.assertFalse(result["valid"])
        self.assertIsNotNone(result["error"])
    
    def test_validate_output_path_in_allowed_dirs_custom_allowed(self):
        """测试自定义允许目录列表"""
        custom_allowed = [PathKey.DOCS_DIR]
        docs_path = self.skill_root / "docs" / "test.md"
        result = self.manager.validate_output_path_in_allowed_dirs(docs_path, allowed_dirs=custom_allowed)
        
        self.assertTrue(result["valid"])
        
        reports_path = self.skill_root / "reports" / "test.md"
        result = self.manager.validate_output_path_in_allowed_dirs(reports_path, allowed_dirs=custom_allowed)
        
        self.assertFalse(result["valid"])
    
    def test_detect_path_conflicts_no_conflict(self):
        """测试无冲突检测"""
        new_path = self.skill_root / "docs" / "new_file.md"
        result = self.manager.detect_path_conflicts(new_path)
        
        self.assertFalse(result["has_conflict"])
        self.assertEqual(len(result["conflicts"]), 0)
    
    def test_detect_path_conflicts_file_exists(self):
        """测试文件已存在冲突"""
        existing_file = self.skill_root / "docs" / "existing.md"
        existing_file.write_text("existing content")
        
        result = self.manager.detect_path_conflicts(existing_file)
        
        self.assertTrue(result["has_conflict"])
        self.assertTrue(any(c["type"] == "file_exists" for c in result["conflicts"]))
    
    def test_detect_path_conflicts_registration_conflict(self):
        """测试注册冲突检测"""
        test_path = self.skill_root / "temp" / "shared.json"
        
        self.manager.register_output_path(
            script_name="script1",
            output_type=OutputType.TEMP,
            path=test_path
        )
        
        result = self.manager.detect_path_conflicts(test_path)
        
        self.assertTrue(result["has_conflict"])
        self.assertTrue(any(c["type"] == "registration_conflict" for c in result["conflicts"]))
    
    def test_generate_validation_report(self):
        """测试生成验证报告"""
        report = self.manager.generate_validation_report()
        
        self.assertIn("timestamp", report)
        self.assertIn("overall_valid", report)
        self.assertIn("total_paths", report)
        self.assertIn("valid_paths", report)
        self.assertIn("invalid_paths", report)
        self.assertIn("details", report)
        self.assertIn("summary", report)
    
    def test_generate_validation_report_specific_paths(self):
        """测试生成特定路径的验证报告"""
        paths = [
            self.skill_root / "docs",
            self.skill_root / "reports"
        ]
        
        report = self.manager.generate_validation_report(paths=paths)
        
        self.assertEqual(report["total_paths"], 2)
    
    def test_generate_validation_report_with_conflicts(self):
        """测试带冲突的验证报告"""
        conflict_path = self.skill_root / "docs" / "conflict.md"
        conflict_path.write_text("conflict content")
        
        report = self.manager.generate_validation_report(paths=[conflict_path], check_conflicts=True)
        
        self.assertTrue(any("conflict" in str(c).lower() or "file_exists" in str(c) 
                          for detail in report["details"] for c in detail.get("conflicts", [])))


class TestSkillPathConfigDocsPaths(unittest.TestCase):
    """测试SkillPathConfig中的docs路径配置"""
    
    def test_docs_paths_in_config(self):
        """测试docs路径在配置中"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_root = Path(tmpdir)
            config = SkillPathConfig.from_skill_root(skill_root)
            
            self.assertEqual(config.docs_dir, skill_root / "docs")
            self.assertEqual(config.docs_reports_dir, skill_root / "docs" / "reports")
            self.assertEqual(config.docs_api_dir, skill_root / "docs" / "api")
            self.assertEqual(config.docs_workflow_dir, skill_root / "docs" / "workflow")
            self.assertEqual(config.docs_knowledge_dir, skill_root / "docs" / "knowledge")
    
    def test_docs_paths_in_to_dict(self):
        """测试docs路径在字典转换中"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_root = Path(tmpdir)
            config = SkillPathConfig.from_skill_root(skill_root)
            config_dict = config.to_dict()
            
            self.assertIn("docs_dir", config_dict)
            self.assertIn("docs_reports_dir", config_dict)
            self.assertIn("docs_api_dir", config_dict)
            self.assertIn("docs_workflow_dir", config_dict)
            self.assertIn("docs_knowledge_dir", config_dict)


class TestPathKeyDocsPaths(unittest.TestCase):
    """测试PathKey中的docs路径键"""
    
    def test_docs_path_keys_exist(self):
        """测试docs路径键存在"""
        self.assertEqual(PathKey.DOCS_DIR.value, "docs_dir")
        self.assertEqual(PathKey.DOCS_REPORTS_DIR.value, "docs_reports_dir")
        self.assertEqual(PathKey.DOCS_API_DIR.value, "docs_api_dir")
        self.assertEqual(PathKey.DOCS_WORKFLOW_DIR.value, "docs_workflow_dir")
        self.assertEqual(PathKey.DOCS_KNOWLEDGE_DIR.value, "docs_knowledge_dir")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestSkillPathConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentVariableManager))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedSkillPathManager))
    suite.addTests(loader.loadTestsFromTestCase(TestDirectoryStructureManager))
    suite.addTests(loader.loadTestsFromTestCase(TestDirectoryHealthChecker))
    suite.addTests(loader.loadTestsFromTestCase(TestDirectorySnapshotManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCreatePathManager))
    suite.addTests(loader.loadTestsFromTestCase(TestOutputType))
    suite.addTests(loader.loadTestsFromTestCase(TestOutputPathRegistry))
    suite.addTests(loader.loadTestsFromTestCase(TestOutputPathManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentVariableOutputPath))
    suite.addTests(loader.loadTestsFromTestCase(TestDocsSubdir))
    suite.addTests(loader.loadTestsFromTestCase(TestDocsPathManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentVariableDocsPath))
    suite.addTests(loader.loadTestsFromTestCase(TestOutputPathValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestSkillPathConfigDocsPaths))
    suite.addTests(loader.loadTestsFromTestCase(TestPathKeyDocsPaths))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
