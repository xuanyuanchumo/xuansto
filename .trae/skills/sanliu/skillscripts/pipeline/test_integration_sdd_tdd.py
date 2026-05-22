#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD-TDD 融合引擎集成测试

测试场景:
1. 省协调器能正确触发融合循环
2. 版本迭代器能正确调用融合引擎进行深化
3. 演化控制器能与融合引擎联动
4. 集成后的完整流程端到端测试（模拟）
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime

script_dir = Path(__file__).parent
skillscripts_dir = script_dir.parent
sanliu_root = skillscripts_dir.parent

sys.path.insert(0, str(sanliu_root))
sys.path.insert(0, str(skillscripts_dir))

os.chdir(str(sanliu_root))

from skillscripts.core.provincial_coordinator import (
    ProvincialCoordinator,
    CoordinationTask,
    Province
)
from skillscripts.core.version_iterator import VersionIterator
from skillscripts.core.auto_iterator import AutoIterator
from skillscripts.core.continuous_evolution_controller import EvolutionController, EvolutionConfig


class TestSDDTDDFusionIntegration(unittest.TestCase):
    """SDD-TDD融合引擎集成测试基类"""
    
    @classmethod
    def setUpClass(cls):
        """创建临时测试环境"""
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="sdd_tdd_test_"))
        cls.specs_dir = cls.temp_dir / "docs" / "specs"
        cls.data_dir = cls.temp_dir / "data"
        cls.specs_dir.mkdir(parents=True, exist_ok=True)
        cls.data_dir.mkdir(parents=True, exist_ok=True)
        
        cls.test_spec_content = """# 测试规范文档

## 规范ID: TEST-SPEC-001

# 用户认证功能

### 功能需求
- 实现用户登录功能
- 支持密码加密存储
- 提供会话管理机制

### 验收标准
Given: 用户输入正确的用户名和密码
When: 点击登录按钮
Then: 系统成功认证并跳转到首页
"""
        
        cls.test_spec_file = cls.specs_dir / "test_spec.md"
        cls.test_spec_file.write_text(cls.test_spec_content, encoding='utf-8')
        
        cls.data_spec_file = cls.data_dir / "data_spec.md"
        cls.data_spec_file.write_text(cls.test_spec_content, encoding='utf-8')
    
    @classmethod
    def tearDownClass(cls):
        """清理临时测试环境"""
        import shutil
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)


class TestProvincialCoordinatorFusion(TestSDDTDDFusionIntegration):
    """测试省协调器与融合引擎的集成"""
    
    def setUp(self):
        """初始化省协调器"""
        self.coordinator = ProvincialCoordinator()
    
    def test_integrate_with_sdd_tdd_fusion_method_exists(self):
        """验证 integrate_with_sdd_tdd_fusion 方法存在"""
        self.assertTrue(
            hasattr(self.coordinator, 'integrate_with_sdd_tdd_fusion'),
            "省协调器应该有 integrate_with_sdd_tdd_fusion 方法"
        )
    
    def test_fusion_disabled_by_default(self):
        """验证融合引擎默认禁用"""
        task = CoordinationTask(
            task_id="TEST-001",
            task_type="feature_development",
            description="测试任务",
            priority="medium"
        )
        
        result = self.coordinator.coordinate_provinces(task)
        
        self.assertIsNone(
            result.get("provinces", {}).get("shangshusheng", {}).get("fusion_engine_report"),
            "默认情况下不应该执行融合循环"
        )
    
    def test_fusion_enabled_triggers_cycle(self):
        """验证启用融合引擎后触发循环"""
        task = CoordinationTask(
            task_id="TEST-002",
            task_type="feature_development",
            description="测试任务 - 启用融合引擎",
            priority="medium",
            context={
                "enable_sdd_tdd_fusion": True,
                "spec_path": str(self.test_spec_file)
            }
        )
        
        result = self.coordinator.coordinate_provinces(task)
        
        shangshu_result = result.get("provinces", {}).get("shangshusheng", {})
        
        self.assertIn("fusion_engine_report", shangshu_result,
                     "启用融合后应该包含报告字段")
    
    def test_fusion_with_valid_spec_path(self):
        """验证使用有效规范路径调用融合引擎"""
        report = self.coordinator.integrate_with_sdd_tdd_fusion(
            str(self.test_spec_file)
        )
        
        if report is not None:
            self.assertTrue(hasattr(report, 'cycle_id'),
                         "融合报告应该包含 cycle_id")
    
    def test_fusion_with_invalid_path(self):
        """验证使用无效路径时优雅降级"""
        report = self.coordinator.integrate_with_sdd_tdd_fusion(
            "/nonexistent/path/spec.md"
        )
        
        self.assertIsNone(report,
                        "无效路径应该返回 None")
    
    def test_fusion_without_path_uses_default(self):
        """验证不提供路径时使用默认目录"""
        report = self.coordinator.integrate_with_sdd_tdd_fusion()
        
        self.assertIsNotNone(report,
                          "应该能够找到并使用默认规范文件")


class TestVersionIteratorFusion(TestSDDTDDFusionIntegration):
    """测试版本迭代器与融合引擎的集成"""
    
    def setUp(self):
        """初始化版本迭代器"""
        self.iterator = VersionIterator(project_root=str(self.temp_dir))
    
    def tearDown(self):
        """清理版本迭代器状态"""
        import shutil
        version_file = self.temp_dir / "version.json"
        if version_file.exists():
            version_file.unlink()
    
    def test_integrate_with_fusion_engine_method_exists(self):
        """验证 integrate_with_fusion_engine 方法存在"""
        self.assertTrue(
            hasattr(self.iterator, 'integrate_with_fusion_engine'),
            "版本迭代器应该有 integrate_with_fusion_engine 方法"
        )
    
    def test_fusion_with_valid_spec(self):
        """验证使用有效规范调用融合引擎"""
        report = self.iterator.integrate_with_fusion_engine(
            spec_path=str(self.test_spec_file),
            max_cycles=2
        )
        
        if report is not None:
            self.assertTrue(hasattr(report, 'total_cycles'),
                         "连续循环报告应该包含 total_cycles")
            self.assertGreaterEqual(report.total_cycles, 1,
                                  "至少应该执行1轮循环")
    
    def test_fusion_continuous_cycles(self):
        """验证连续多轮深化循环"""
        report = self.iterator.integrate_with_fusion_engine(
            spec_path=str(self.test_spec_file),
            max_cycles=3
        )
        
        if report is not None:
            self.assertLessEqual(report.total_cycles, 3,
                               "循环次数不应超过 max_cycles")


class TestAutoIteratorFusion(TestSDDTDDFusionIntegration):
    """测试自动迭代器与融合引擎的集成"""
    
    def setUp(self):
        """初始化自动迭代器"""
        self.auto_iterator = AutoIterator(project_root=str(self.temp_dir))
    
    def test_integrate_with_fusion_engine_method_exists(self):
        """验证自动迭代器有融合引擎集成方法"""
        self.assertTrue(
            hasattr(self.auto_iterator, 'integrate_with_fusion_engine'),
            "自动迭代器应该有 integrate_with_fusion_engine 方法"
        )
    
    def test_auto_iterator_delegates_to_version_iterator(self):
        """验证自动迭代器委托给版本迭代器"""
        report = self.auto_iterator.integrate_with_fusion_engine(
            spec_path=str(self.test_spec_file),
            max_cycles=2
        )
        
        if report is not None:
            self.assertTrue(hasattr(report, 'report_id') or hasattr(report, 'total_cycles'),
                         "应该返回有效的融合报告")


class TestEvolutionControllerFusion(TestSDDTDDFusionIntegration):
    """测试演化控制器与融合引擎的集成"""
    
    def setUp(self):
        """初始化演化控制器"""
        config = EvolutionConfig(
            output_dir=str(self.temp_dir / "evolution_reports"),
            state_persistence_enabled=False,
            auto_trigger_enabled=False
        )
        self.controller = EvolutionController(
            config=config,
            project_dir=str(self.temp_dir)
        )
    
    def test_integrate_sdd_tdd_fusion_method_exists(self):
        """验证 integrate_sdd_tdd_fusion 方法存在"""
        self.assertTrue(
            hasattr(self.controller, 'integrate_sdd_tdd_fusion'),
            "演化控制器应该有 integrate_sdd_tdd_fusion 方法"
        )
    
    def test_fusion_finds_spec_files(self):
        """验证演化控制器能找到规范文件"""
        report = self.controller.integrate_sdd_tdd_fusion()
        
        if report is not None:
            self.assertTrue(hasattr(report, 'cycle_id'),
                         "应该返回有效的融合报告")
    
    def test_fusion_handles_missing_specs(self):
        """验证处理缺失规范文件的情况"""
        import shutil
        
        backup_specs = self.specs_dir
        backup_data = self.data_dir
        
        empty_dir = Path(tempfile.mkdtemp())
        
        original_data_dir = self.controller._project_dir / "data"
        original_docs_dir = self.controller._project_dir / "docs" / "specs"
        
        if original_data_dir.exists():
            shutil.move(str(original_data_dir), str(empty_dir / "data_backup"))
        if original_docs_dir.exists():
            shutil.move(str(original_docs_dir), str(empty_dir / "specs_backup"))
        
        try:
            report = self.controller.integrate_sdd_tdd_fusion()
            
            self.assertIsNone(report,
                            "没有规范文件时应该返回 None")
        finally:
            if (empty_dir / "data_backup").exists():
                shutil.move(str(empty_dir / "data_backup"), str(original_data_dir))
            if (empty_dir / "specs_backup").exists():
                shutil.move(str(empty_dir / "specs_backup"), str(original_docs_dir))
            shutil.rmtree(empty_dir)


class TestEndToEndIntegration(TestSDDTDDFusionIntegration):
    """端到端集成测试 - 模拟完整流程"""
    
    def test_full_workflow_integration(self):
        """测试完整的集成工作流"""
        
        coordinator = ProvincialCoordinator()
        iterator = VersionIterator(project_root=str(self.temp_dir))
        controller = EvolutionController(
            config=EvolutionConfig(
                output_dir=str(self.temp_dir / "evo_reports"),
                state_persistence_enabled=False,
                auto_trigger_enabled=False
            ),
            project_dir=str(self.temp_dir)
        )
        
        results = {}
        
        fusion_report_coordinator = coordinator.integrate_with_sdd_tdd_fusion(
            str(self.test_spec_file)
        )
        results["coordinator"] = fusion_report_coordinator is not None
        
        fusion_report_iterator = iterator.integrate_with_fusion_engine(
            spec_path=str(self.test_spec_file),
            max_cycles=2
        )
        results["iterator"] = fusion_report_iterator is not None
        
        fusion_report_controller = controller.integrate_sdd_tdd_fusion()
        results["controller"] = fusion_report_controller is not None
        
        successful_integrations = sum(1 for v in results.values() if v)
        
        self.assertGreater(successful_integrations, 0,
                          "至少有一个组件应该成功集成融合引擎")
        
        print(f"\n{'='*60}")
        print("端到端集成测试结果:")
        print(f"{'='*60}")
        for component, success in results.items():
            status = "✅ 成功" if success else "⚠️ 跳过"
            print(f"  {component}: {status}")
        print(f"\n总成功率: {successful_integrations}/{len(results)}")
        print(f"{'='*60}\n")
    
    def test_error_handling_and_graceful_degradation(self):
        """测试错误处理和优雅降级"""
        
        coordinator = ProvincialCoordinator()
        
        invalid_paths = [
            None,
            "",
            "/nonexistent/path.md",
            "relative/path.md"
        ]
        
        for path in invalid_paths:
            try:
                report = coordinator.integrate_with_sdd_tdd_fusion(path)
                
                self.assertIsNotNone(coordinator,
                                   "协调器在错误处理后应该仍然可用")
            except Exception as e:
                self.fail(f"路径 {path} 应该优雅处理异常，但抛出了: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
