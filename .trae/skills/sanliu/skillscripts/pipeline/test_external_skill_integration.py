#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外部技能集成功能单元测试

测试 skill_creator_integration.py 和 ui_ux_integration.py 的增强功能。
"""

import os
import sys
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

_pipeline_dir = Path(__file__).parent
_skillscripts_dir = _pipeline_dir.parent
_sanliu_dir = _skillscripts_dir.parent
_skills_dir = _sanliu_dir.parent
_trae_dir = _skills_dir.parent
_project_dir = _trae_dir.parent

sys.path.insert(0, str(_pipeline_dir))
sys.path.insert(0, str(_skillscripts_dir))

import importlib.util

def load_module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

skill_creator = load_module_from_file(
    "skill_creator_integration",
    _pipeline_dir / "skill_creator_integration.py"
)

ui_ux = load_module_from_file(
    "ui_ux_integration",
    _pipeline_dir / "ui_ux_integration.py"
)

SkillVersionManager = skill_creator.SkillVersionManager
VersionChangeType = skill_creator.VersionChangeType
SkillVersion = skill_creator.SkillVersion
TemplateManager = skill_creator.TemplateManager
TemplateInfo = skill_creator.TemplateInfo
TemplateStatus = skill_creator.TemplateStatus
SkillTemplate = skill_creator.SkillTemplate
PerformanceMonitor = skill_creator.PerformanceMonitor
PerformanceMetricType = skill_creator.PerformanceMetricType
PerformanceMetric = skill_creator.PerformanceMetric
SkillCreationAutomator = skill_creator.SkillCreationAutomator
SkillCreatorIntegration = skill_creator.SkillCreatorIntegration

UIUXIntegration = ui_ux.UIUXIntegration
UIDesignAutomator = ui_ux.UIDesignAutomator
UXGuidelineChecker = ui_ux.UXGuidelineChecker
UXGuideline = ui_ux.UXGuideline
DesignSystemIntegrator = ui_ux.DesignSystemIntegrator
ComponentLibraryIntegrator = ui_ux.ComponentLibraryIntegrator
ComponentLibrary = ui_ux.ComponentLibrary
ComponentInfo = ui_ux.ComponentInfo
DesignSystem = ui_ux.DesignSystem
DesignToken = ui_ux.DesignToken
ThemeType = ui_ux.ThemeType


class TestSkillVersionManager:
    """技能版本管理器测试"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.version_manager = SkillVersionManager(versions_path=self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_version(self):
        version = self.version_manager.create_version(
            skill_name="test-skill",
            change_type=VersionChangeType.MAJOR,
            changes=["初始版本"],
            author="test"
        )
        
        assert version.skill_name == "test-skill"
        assert version.version == "1.0.0"
        assert version.change_type == VersionChangeType.MAJOR
        assert "初始版本" in version.changes
    
    def test_version_increment(self):
        self.version_manager.create_version(
            skill_name="test-skill",
            change_type=VersionChangeType.MAJOR,
            changes=["v1"]
        )
        
        v2 = self.version_manager.create_version(
            skill_name="test-skill",
            change_type=VersionChangeType.MINOR,
            changes=["v2"]
        )
        assert v2.version == "1.1.0"
        
        v3 = self.version_manager.create_version(
            skill_name="test-skill",
            change_type=VersionChangeType.PATCH,
            changes=["v3"]
        )
        assert v3.version == "1.1.1"
        
        v4 = self.version_manager.create_version(
            skill_name="test-skill",
            change_type=VersionChangeType.MAJOR,
            changes=["v4"]
        )
        assert v4.version == "2.0.0"
    
    def test_get_versions(self):
        self.version_manager.create_version(
            skill_name="test-skill",
            change_type=VersionChangeType.MAJOR,
            changes=["v1"]
        )
        self.version_manager.create_version(
            skill_name="test-skill",
            change_type=VersionChangeType.MINOR,
            changes=["v2"]
        )
        
        versions = self.version_manager.get_versions("test-skill")
        assert len(versions) == 2
    
    def test_deprecate_version(self):
        self.version_manager.create_version(
            skill_name="test-skill",
            change_type=VersionChangeType.MAJOR,
            changes=["v1"]
        )
        
        success, message = self.version_manager.deprecate_version(
            "test-skill", "1.0.0", "已弃用"
        )
        
        assert success is True
        versions = self.version_manager.get_versions("test-skill")
        assert versions[0].is_deprecated is True
    
    def test_rollback_version(self):
        self.version_manager.create_version(
            skill_name="test-skill",
            change_type=VersionChangeType.MAJOR,
            changes=["v1"]
        )
        self.version_manager.create_version(
            skill_name="test-skill",
            change_type=VersionChangeType.MINOR,
            changes=["v2"]
        )
        
        success, message = self.version_manager.rollback_version("test-skill", "1.0.0")
        assert success is True
    
    def test_generate_changelog(self):
        self.version_manager.create_version(
            skill_name="test-skill",
            change_type=VersionChangeType.MAJOR,
            changes=["初始版本"],
            new_features=["功能1", "功能2"]
        )
        
        changelog = self.version_manager.generate_changelog("test-skill")
        assert "test-skill" in changelog
        assert "1.0.0" in changelog


class TestPerformanceMonitor:
    """性能监控器测试"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.monitor = PerformanceMonitor(metrics_path=self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_record_metric(self):
        metric = self.monitor.record_metric(
            skill_name="test-skill",
            metric_type=PerformanceMetricType.EXECUTION_TIME,
            value=100.5,
            unit="ms"
        )
        
        assert metric.skill_name == "test-skill"
        assert metric.value == 100.5
        assert metric.unit == "ms"
    
    def test_get_metrics(self):
        self.monitor.record_metric(
            "test-skill", PerformanceMetricType.EXECUTION_TIME, 100, "ms"
        )
        self.monitor.record_metric(
            "test-skill", PerformanceMetricType.EXECUTION_TIME, 200, "ms"
        )
        
        metrics = self.monitor.get_metrics("test-skill")
        assert len(metrics) == 2
    
    def test_analyze_trends(self):
        for i in range(10):
            self.monitor.record_metric(
                "test-skill", PerformanceMetricType.EXECUTION_TIME, 
                100 + i * 10, "ms"
            )
        
        trend = self.monitor.analyze_trends(
            "test-skill", PerformanceMetricType.EXECUTION_TIME
        )
        
        assert trend["trend"] in ["increasing", "decreasing", "stable"]
        assert trend["data_points"] == 10
    
    def test_detect_anomalies(self):
        for i in range(10):
            self.monitor.record_metric(
                "test-skill", PerformanceMetricType.EXECUTION_TIME, 
                100, "ms"
            )
        self.monitor.record_metric(
            "test-skill", PerformanceMetricType.EXECUTION_TIME, 
            1000, "ms"
        )
        
        anomalies = self.monitor.detect_anomalies(
            "test-skill", PerformanceMetricType.EXECUTION_TIME
        )
        
        assert len(anomalies) > 0
    
    def test_generate_report(self):
        self.monitor.record_metric(
            "test-skill", PerformanceMetricType.EXECUTION_TIME, 100, "ms"
        )
        self.monitor.record_metric(
            "test-skill", PerformanceMetricType.SUCCESS_RATE, 0.95, "ratio"
        )
        
        report = self.monitor.generate_report("test-skill")
        
        assert report.skill_name == "test-skill"
        assert len(report.metrics) == 2


class TestUIDesignAutomator:
    """UI设计自动化器测试"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.integration = UIUXIntegration(project_path=self.temp_dir)
        self.automator = self.integration.design_automator
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_automate_design(self):
        result = self.automator.automate_design(
            page_type="landing",
            requirements={"features": ["button", "form"]},
            tech_stack="react"
        )
        
        assert result.task_type == "landing"
        assert result.status in ["completed", "failed"]
    
    def test_select_components(self):
        components = self.automator._select_components(
            "dashboard",
            {"features": ["table", "chart"]},
            ComponentLibrary.ANTD
        )
        
        assert len(components) > 0
    
    def test_generate_responsive_layout(self):
        layout = self.automator.create_responsive_layout(
            "grid",
            {"sm": 640, "md": 768, "lg": 1024}
        )
        
        assert "container" in layout
        assert "@media" in layout


class TestUXGuidelineChecker:
    """UX规范检查器测试"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.integration = UIUXIntegration(project_path=self.temp_dir)
        self.checker = self.integration.ux_checker
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_check_guidelines(self):
        test_file = Path(self.temp_dir) / "test.html"
        test_file.write_text("""
        <html>
        <body>
            <img src="test.jpg" alt="测试图片">
            <input type="text" id="name" aria-label="名称">
            <button class="btn:hover">点击</button>
        </body>
        </html>
        """, encoding='utf-8')
        
        result = self.checker.check_guidelines(str(test_file))
        
        assert "summary" in result
        assert result["summary"]["total"] > 0
    
    def test_check_img_alt(self):
        content = '<img src="test.jpg" alt="描述">'
        result = self.checker._check_img_alt(content, Path("."))
        assert result["status"] == "passed"
        
        content = '<img src="test.jpg">'
        result = self.checker._check_img_alt(content, Path("."))
        assert result["status"] == "failed"
    
    def test_get_guidelines(self):
        guidelines = self.checker.get_guidelines("accessibility")
        assert len(guidelines) > 0


class TestDesignSystemIntegrator:
    """设计系统集成器测试"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.integration = UIUXIntegration(project_path=self.temp_dir)
        self.integrator = self.integration.design_integrator
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_design_token(self):
        token = self.integrator.create_design_token(
            name="primary",
            category="color",
            value="#1890ff",
            description="主色调"
        )
        
        assert token.name == "primary"
        assert token.value == "#1890ff"
    
    def test_get_token(self):
        self.integrator.create_design_token(
            "primary", "color", "#1890ff"
        )
        
        token = self.integrator.get_token("primary", "color")
        assert token is not None
        assert token.value == "#1890ff"
    
    def test_export_css_tokens(self):
        self.integrator.create_design_token("primary", "color", "#1890ff")
        self.integrator.create_design_token("md", "spacing", "16px")
        
        css = self.integrator.export_tokens("css")
        
        assert ":root" in css
        assert "#1890ff" in css
        assert "16px" in css
    
    def test_export_json_tokens(self):
        self.integrator.create_design_token("primary", "color", "#1890ff")
        
        json_output = self.integrator.export_tokens("json")
        
        data = json.loads(json_output)
        assert "color.primary" in data


class TestComponentLibraryIntegrator:
    """组件库集成器测试"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.integration = UIUXIntegration(project_path=self.temp_dir)
        self.integrator = self.integration.component_integrator
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_register_library(self):
        success, message = self.integrator.register_library(ComponentLibrary.ANTD)
        assert success is True
        
        success, message = self.integrator.register_library(ComponentLibrary.ANTD)
        assert success is False
    
    def test_get_component(self):
        component = self.integrator.get_component("Button", ComponentLibrary.ANTD)
        
        assert component is not None
        assert component.name == "Button"
    
    def test_list_components(self):
        components = self.integrator.list_components(ComponentLibrary.ANTD)
        assert len(components) > 0
    
    def test_generate_component_code(self):
        code = self.integrator.generate_component_code(
            "Button",
            {"type": "primary", "size": "large"},
            ComponentLibrary.ANTD
        )
        
        assert "Button" in code
        assert "primary" in code
    
    def test_check_library_compatibility(self):
        compat = self.integrator.check_library_compatibility(
            ComponentLibrary.ANTD, "react"
        )
        
        assert compat.get("compatible") is True
        
        compat = self.integrator.check_library_compatibility(
            ComponentLibrary.ANTD, "vue"
        )
        
        assert compat.get("compatible") is False
    
    def test_suggest_components(self):
        suggestions = self.integrator.suggest_components(
            "需要一个按钮和输入框",
            ComponentLibrary.ANTD
        )
        
        assert len(suggestions) > 0


class TestUIUXIntegration:
    """UI/UX集成管理器测试"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.integration = UIUXIntegration(project_path=self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_design_system(self):
        design_system = self.integration.generate_design_system(
            name="test",
            theme=ThemeType.MODERN
        )
        
        assert design_system.name == "test"
        assert design_system.theme == ThemeType.MODERN
        assert len(design_system.colors) > 0
    
    def test_validate_ui(self):
        test_file = Path(self.temp_dir) / "test.tsx"
        test_file.write_text("""
        import React from 'react';
        const Test = () => (
            <div className="container">
                <img src="test.jpg" alt="测试" />
                <button onClick={() => {}}>点击</button>
            </div>
        );
        export default Test;
        """, encoding='utf-8')
        
        result = self.integration.validate_ui(str(test_file))
        
        assert result.overall_score >= 0
        assert result.accessibility_score >= 0
    
    def test_discover_tasks(self):
        tasks = self.integration.discover_tasks("all")
        assert isinstance(tasks, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
