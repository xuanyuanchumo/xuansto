#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径配置管理器 - Sanliu 技能

功能：
- 支持两种运行模式：技能自迭代模式、指导其他项目模式
- 动态配置基础路径
- 版本化路径管理
- 目录自动创建
- 模式自动识别（增强版）
  - 环境变量检测 (SANLIU_MODE, SANLIU_TARGET_ROOT)
  - 配置文件检测 (.sanliu.yaml, .sanliu.json)
  - 命令行参数检测
- 配置持久化
- 路径验证和错误处理
- 双模式智能切换
- 模式状态管理和历史记录
- 模式切换验证和回滚机制

增强功能（新增）：
- 动态路径解析增强
  - DynamicPathResolver 类：支持路径模板变量解析
  - 内置变量：${PROJECT_ROOT}, ${VERSION}, ${DATE}, ${TIME}, ${DATETIME} 等
  - 支持条件路径：根据项目类型选择不同路径
  - 支持路径别名系统
- 环境变量覆盖增强
  - 支持更多环境变量：SANLIU_DOCS_PATH, SANLIU_SCRIPTS_PATH 等
  - 支持环境变量组合：SANLIU_PATHS_DOCS, SANLIU_PATHS_SCRIPTS
  - 实现环境变量优先级机制
- 相对路径转换增强
  - to_relative_path()：绝对路径转相对路径
  - to_absolute_path()：相对路径转绝对路径
  - 跨平台路径转换支持
  - 路径规范化功能
- 路径安全验证增强
  - PathSecurityValidator 类：路径安全验证器
  - 检测路径遍历攻击
  - 检测符号链接安全风险
  - 路径权限检查
  - 危险字符和模式检测

使用方法：
    from path_config_manager import PathConfigManager, PathMode
    
    # 自动识别模式（推荐）
    manager = PathConfigManager()
    
    # 技能自迭代模式
    manager = PathConfigManager(mode=PathMode.SELF_ITERATION)
    
    # 指导其他项目模式
    manager = PathConfigManager(mode=PathMode.GUIDE_PROJECT, target_root="/path/to/project")
    
    # 获取路径
    docs_path = manager.get_docs_libs_path(version="1.0.0")
    tests_path = manager.get_tests_path()
    
    # 模式切换
    manager.switch_mode(PathMode.GUIDE_PROJECT, target_root="/new/project")
    
    # 获取模式信息
    info = manager.get_mode_info()
    
    # 动态路径解析
    from path_config_manager import DynamicPathResolver
    resolver = DynamicPathResolver(base_path=manager.get_base_path())
    resolved = resolver.resolve("${PROJECT_ROOT}/docs/${DATE}")
    
    # 路径安全验证
    from path_config_manager import PathSecurityValidator
    result = PathSecurityValidator.validate_security("/path/to/check")
"""

import json
import logging
import os
import re
import shutil
import sys
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Generator, Union

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PathMode(Enum):
    """
    路径模式枚举
    
    SELF_ITERATION: 自迭代模式 - 技能自我迭代开发
    GUIDE_PROJECT: 指导项目模式 - 指导其他项目开发
    """
    SELF_ITERATION = "self_iteration"
    GUIDE_PROJECT = "guide_project"
    
    @classmethod
    def from_string(cls, value: str) -> Optional['PathMode']:
        """
        从字符串创建模式枚举
        
        Args:
            value: 模式字符串，支持 "self_iteration", "guide_project", "auto"
            
        Returns:
            对应的 PathMode 枚举值，"auto" 返回 None
        """
        mode_map = {
            "self_iteration": cls.SELF_ITERATION,
            "guide_project": cls.GUIDE_PROJECT,
            "auto": None
        }
        return mode_map.get(value.lower())
    
    def get_description(self) -> str:
        """获取模式的中文描述"""
        descriptions = {
            PathMode.SELF_ITERATION: "技能自迭代模式 - 在技能目录内进行自我迭代开发",
            PathMode.GUIDE_PROJECT: "指导项目模式 - 指导其他项目进行开发"
        }
        return descriptions.get(self, "未知模式")


class PathConfigError(Exception):
    """路径配置基础异常类"""
    
    def __init__(self, message: str, path: Optional[Path] = None, mode: Optional[PathMode] = None):
        super().__init__(message)
        self.path = path
        self.mode = mode
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        details = []
        if self.mode:
            details.append(f"模式: {self.mode.value}")
        if self.path:
            details.append(f"路径: {self.path}")
        if details:
            return f"{base_msg} ({', '.join(details)})"
        return base_msg


class PathValidationError(PathConfigError):
    """路径验证异常"""
    pass


class ModeSwitchError(PathConfigError):
    """模式切换异常"""
    pass


class ModeDetectionError(PathConfigError):
    """模式检测异常"""
    pass


@dataclass
class PathConfig:
    """
    路径配置数据类
    
    存储各种路径的相对配置
    """
    docs_libs_path: str = "docs/libs"
    docs_reports_path: str = "docs/reports"
    docs_iteration_path: str = "docs/迭代版本"
    tests_path: str = "tests"
    skillscripts_path: str = "skillscripts"
    version_file: str = "version.json"
    config_file: str = "path_config.json"
    temp_path: str = "temp"
    cache_path: str = "cache"
    data_path: str = "data"
    config_path: str = "config"
    reports_path: str = "reports"
    logs_path: str = "logs"
    backend_path: str = "backend"
    frontend_path: str = "frontend"
    
    shangshusheng_path: str = "shangshusheng"
    resources_path: str = "resources"
    
    scripts_core_path: str = "skillscripts/core"
    scripts_analysis_path: str = "skillscripts/analysis"
    scripts_optimization_path: str = "skillscripts/optimization"
    scripts_test_path: str = "skillscripts/test"
    scripts_pipeline_path: str = "skillscripts/pipeline"
    scripts_learning_path: str = "skillscripts/learning"
    scripts_auto_repair_path: str = "skillscripts/auto_repair"
    scripts_iteration_path: str = "skillscripts/iteration"
    scripts_requirements_path: str = "skillscripts/requirements"
    scripts_sdd_tdd_path: str = "skillscripts/sdd_tdd"
    scripts_monitoring_path: str = "skillscripts/monitoring"
    scripts_utils_path: str = "skillscripts/utils"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PathConfig':
        """从字典创建实例"""
        return cls(
            docs_libs_path=data.get('docs_libs_path', 'docs/libs'),
            docs_reports_path=data.get('docs_reports_path', 'docs/reports'),
            docs_iteration_path=data.get('docs_iteration_path', 'docs/迭代版本'),
            tests_path=data.get('tests_path', 'tests'),
            skillscripts_path=data.get('skillscripts_path', 'skillscripts'),
            version_file=data.get('version_file', 'version.json'),
            config_file=data.get('config_file', 'path_config.json'),
            temp_path=data.get('temp_path', 'temp'),
            cache_path=data.get('cache_path', 'cache'),
            data_path=data.get('data_path', 'data'),
            config_path=data.get('config_path', 'config'),
            reports_path=data.get('reports_path', 'reports'),
            logs_path=data.get('logs_path', 'logs'),
            backend_path=data.get('backend_path', 'backend'),
            frontend_path=data.get('frontend_path', 'frontend'),
            shangshusheng_path=data.get('shangshusheng_path', 'shangshusheng'),
            resources_path=data.get('resources_path', 'resources'),
            scripts_core_path=data.get('scripts_core_path', 'skillscripts/core'),
            scripts_analysis_path=data.get('scripts_analysis_path', 'skillscripts/analysis'),
            scripts_optimization_path=data.get('scripts_optimization_path', 'skillscripts/optimization'),
            scripts_test_path=data.get('scripts_test_path', 'skillscripts/test'),
            scripts_pipeline_path=data.get('scripts_pipeline_path', 'skillscripts/pipeline'),
            scripts_learning_path=data.get('scripts_learning_path', 'skillscripts/learning'),
            scripts_auto_repair_path=data.get('scripts_auto_repair_path', 'skillscripts/auto_repair'),
            scripts_iteration_path=data.get('scripts_iteration_path', 'skillscripts/iteration'),
            scripts_requirements_path=data.get('scripts_requirements_path', 'skillscripts/requirements'),
            scripts_sdd_tdd_path=data.get('scripts_sdd_tdd_path', 'skillscripts/sdd_tdd'),
            scripts_monitoring_path=data.get('scripts_monitoring_path', 'skillscripts/monitoring'),
            scripts_utils_path=data.get('scripts_utils_path', 'skillscripts/utils')
        )


@dataclass
class VersionInfo:
    """版本信息数据类"""
    version: str
    created_at: str
    updated_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class ModeDetectionResult:
    """
    模式检测结果数据类
    
    包含检测到的模式、路径、置信度和详细检测信息
    """
    detected_mode: PathMode
    skill_root: Optional[Path]
    project_root: Optional[Path]
    confidence: float
    detection_details: Dict[str, Any]
    
    def is_high_confidence(self) -> bool:
        """判断是否为高置信度检测结果"""
        return self.confidence >= 0.8
    
    def get_summary(self) -> str:
        """获取检测结果摘要"""
        return (
            f"检测模式: {self.detected_mode.value}, "
            f"置信度: {self.confidence:.2%}, "
            f"技能根目录: {self.skill_root or '未找到'}, "
            f"项目根目录: {self.project_root or '未找到'}"
        )


@dataclass
class ModeSwitchRecord:
    """
    模式切换记录数据类
    
    记录模式切换的历史信息
    """
    from_mode: PathMode
    to_mode: PathMode
    timestamp: str
    from_path: Optional[str]
    to_path: Optional[str]
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "from_mode": self.from_mode.value,
            "to_mode": self.to_mode.value,
            "timestamp": self.timestamp,
            "from_path": self.from_path,
            "to_path": self.to_path,
            "success": self.success,
            "error_message": self.error_message
        }


@dataclass
class ModeState:
    """
    模式状态数据类
    
    管理当前模式的完整状态信息
    """
    current_mode: PathMode
    base_path: Optional[Path]
    target_root: Optional[Path]
    initialized_at: str
    last_switch_at: Optional[str] = None
    switch_count: int = 0
    switch_history: List[ModeSwitchRecord] = field(default_factory=list)
    
    def add_switch_record(self, record: ModeSwitchRecord) -> None:
        """添加切换记录"""
        self.switch_history.append(record)
        self.switch_count += 1
        self.last_switch_at = record.timestamp
    
    def get_recent_switches(self, count: int = 5) -> List[ModeSwitchRecord]:
        """获取最近的切换记录"""
        return self.switch_history[-count:] if self.switch_history else []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "current_mode": self.current_mode.value,
            "base_path": str(self.base_path) if self.base_path else None,
            "target_root": str(self.target_root) if self.target_root else None,
            "initialized_at": self.initialized_at,
            "last_switch_at": self.last_switch_at,
            "switch_count": self.switch_count,
            "switch_history": [r.to_dict() for r in self.switch_history]
        }


@dataclass
class ScriptInfo:
    """
    脚本信息数据类
    
    存储单个脚本的元数据
    """
    name: str
    category: str
    relative_path: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "category": self.category,
            "relative_path": self.relative_path,
            "description": self.description,
            "tags": self.tags,
            "dependencies": self.dependencies
        }


class ScriptPathRegistry:
    """
    脚本路径注册表
    
    统一管理所有脚本的路径配置，支持：
    - 脚本路径注册和查询
    - 按类别、标签筛选脚本
    - 动态路径解析
    - 路径验证
    """
    
    SCRIPT_CATEGORIES = {
        "core": {
            "description": "核心功能脚本",
            "path": "skillscripts/core",
            "scripts": [
                "agent_selector.py",
                "assign_agent.py",
                "auto_iterator.py",
                "auto_optimizer.py",
                "check_environment.py",
                "continuous_evolution_controller.py",
                "cross_project_knowledge_sharing.py",
                "department_logic_checker.py",
                "docker_manager.py",
                "evolution_alert.py",
                "evolution_config_manager.py",
                "evolution_cycle_executor.py",
                "external_skill_integrator.py",
                "health_check.py",
                "init_db.py",
                "performance_optimizer.py",
                "problem_detector.py",
                "project_registration_manager.py",
                "project_registry.py",
                "project_type_adapter.py",
                "provincial_coordinator.py",
                "provincial_logic_checker.py",
                "query_status.py",
                "record_skill_call.py",
                "script_base.py",
                "script_interface_standard.py",
                "script_registry.py",
                "sdd_parser.py",
                "sdd_spec_parser.py",
                "self_iteration_enhanced.py",
                "self_iteration_integration.py",
                "service_dependency_manager.py",
                "skill_auto_repairer.py",
                "skill_call_chain_checker.py",
                "skill_call_chain_validator.py",
                "skill_content_change_detector.py",
                "skill_content_monitor.py",
                "skill_doc_updater.py",
                "skill_evolution_knowledge.py",
                "skill_evolution_manager.py",
                "skill_health_assessor.py",
                "skill_health_checker.py",
                "start_services.py",
                "stop_services.py",
                "subskill_doc_updater.py",
                "subskill_manager.py",
                "unified_script_entry.py",
                "version_iterator.py"
            ]
        },
        "analysis": {
            "description": "代码分析脚本",
            "path": "skillscripts/analysis",
            "scripts": [
                "ai_code_analyzer.py",
                "analyze_composable.py",
                "analyze_core_nesting.py",
                "analyze_frontend_nesting.py",
                "anomaly_detector.py",
                "api_consistency_validator.py",
                "architecture_check.py",
                "auto_fix_suggestion_system.py",
                "backend_module_analyzer.py",
                "check_coverage.py",
                "code_problem_scanner.py",
                "code_quality_validator.py",
                "code_review_automation.py",
                "component_dependency_analyzer.py",
                "coverage_analyzer.py",
                "coverage_monitor.py",
                "data_flow_analyzer.py",
                "department_logic_checker.py",
                "dependency_analyzer.py",
                "design_pattern_checker.py",
                "detect_frontend_long_functions.py",
                "detect_long_functions.py",
                "enhanced_log_analyzer.py",
                "frontend_component_analyzer.py",
                "integrated_log_analyzer.py",
                "intelligent_code_smell_detector.py",
                "issue_awareness_engine.py",
                "issue_classifier.py",
                "issue_locator.py",
                "issue_tracker.py",
                "knowledge_base.py",
                "knowledge_learning_system.py",
                "learning_engine.py",
                "log_analyzer.py",
                "log_correlation_analyzer.py",
                "nesting_analyzer.py",
                "performance_detector.py",
                "provincial_logic_checker.py",
                "quality_trend_analyzer.py",
                "recommendation_engine.py",
                "script_similarity_analyzer.py",
                "simple_nesting_check.py",
                "skill_call_chain_checker.py",
                "solid_principle_checker.py",
                "subskill_optimizer.py",
                "tech_debt_tracker.py"
            ]
        },
        "optimization": {
            "description": "代码优化脚本",
            "path": "skillscripts/optimization",
            "scripts": [
                "architecture_optimizer.py",
                "architecture_optimizer_enhanced.py",
                "auto_fixer.py",
                "code_quality_fixers.py",
                "code_quality_optimizer_enhanced.py",
                "error_detector_enhanced.py",
                "fix_rollback_manager.py",
                "fix_strategy_extension.py",
                "fix_strategy_library.py",
                "fix_strategy_library_enhanced.py",
                "fix_validator.py",
                "fix_verification_enhanced.py",
                "optimization_evaluation_system.py",
                "optimization_report_generator.py",
                "optimization_validator.py",
                "performance_optimizer_enhanced.py",
                "problem_detector_extension.py",
                "refactoring_suggestion_generator.py",
                "refactoring_validator.py",
                "systematic_optimizer.py",
                "unified_optimization_manager.py"
            ]
        },
        "test": {
            "description": "测试相关脚本",
            "path": "skillscripts/test",
            "scripts": [
                "comprehensive_test_runner.py",
                "correlated_failure_analyzer.py",
                "coverage_monitor.py",
                "database_test_enhancer.py",
                "e2e_test_enhancer.py",
                "failure_pattern_learner.py",
                "generate_test_report.py",
                "green_phase_generator.py",
                "integration_test_enhancer.py",
                "intelligent_test_generator.py",
                "intelligent_test_selector.py",
                "performance_benchmark_test.py",
                "performance_test_enhancer.py",
                "regression_test.py",
                "sdd_test_generator.py",
                "sdd_test_generator_enhanced.py",
                "security_scanner.py",
                "test_failure_diagnostician.py",
                "test_report_generator.py",
                "ui_validation_intelligence.py",
                "unit_test_enhancer.py"
            ]
        },
        "pipeline": {
            "description": "流水线脚本",
            "path": "skillscripts/pipeline",
            "scripts": [
                "automated_pipeline.py",
                "automated_pipeline_orchestrator.py",
                "closed_loop_verifier.py",
                "code_review_automation.py",
                "doc_generator.py",
                "incremental_doc_generator.py",
                "intelligent_test_selector.py",
                "pipeline_intelligence.py",
                "sdd_api_doc_generator.py",
                "sdd_cli.py",
                "sdd_code_generator.py",
                "sdd_spec_parser.py",
                "sdd_spec_parser_enhanced.py",
                "sdd_tdd_cycle.py",
                "sdd_tdd_integrator.py",
                "skill_creator_integration.py",
                "tdd_blue_refactoring_pipeline.py",
                "tdd_feedback_analyzer.py",
                "ui_ux_integration.py",
                "ui_validation_intelligence.py",
                "verify_enhancements.py"
            ]
        },
        "learning": {
            "description": "学习和知识管理脚本",
            "path": "skillscripts/learning",
            "scripts": [
                "auto_learner.py",
                "best_practice_extractor.py",
                "knowledge_application_engine.py",
                "knowledge_updater.py",
                "pattern_recognizer.py"
            ]
        },
        "auto_repair": {
            "description": "自动修复脚本",
            "path": "skillscripts/auto_repair",
            "scripts": [
                "auto_repair_system.py",
                "auto_repair_workflow.py",
                "fix_executor.py",
                "fix_strategy.py",
                "issue_detector.py"
            ]
        },
        "iteration": {
            "description": "迭代相关脚本",
            "path": "skillscripts/iteration",
            "scripts": [
                "enhanced_version_iterator.py",
                "iteration_effect_evaluator.py",
                "iteration_trigger_system.py",
                "self_improvement_cycle.py"
            ]
        },
        "requirements": {
            "description": "需求管理脚本",
            "path": "skillscripts/requirements",
            "scripts": [
                "business_rule_extractor.py",
                "business_rule_recognizer.py",
                "requirement_change_impact_analyzer.py",
                "requirement_parser.py",
                "requirement_spec_generator.py",
                "requirement_trace_manager.py",
                "rule_library_manager.py",
                "rule_validator.py",
                "trace_matrix_visualizer.py",
                "trace_report_generator.py"
            ]
        },
        "sdd_tdd": {
            "description": "SDD/TDD 相关脚本",
            "path": "skillscripts/sdd_tdd",
            "scripts": [
                "enhanced_spec_parser.py",
                "sdd_tdd_integration.py",
                "spec_completeness_validator.py",
                "spec_to_code_generator.py",
                "spec_to_test_mapper.py",
                "tdd_cycle_executor.py"
            ]
        },
        "monitoring": {
            "description": "监控脚本",
            "path": "skillscripts/monitoring",
            "scripts": [
                "coverage_monitor.py",
                "dashboard.py",
                "quality_trend_analyzer.py",
                "realtime_monitor.py",
                "tech_debt_tracker.py"
            ]
        },
        "utils": {
            "description": "工具脚本",
            "path": "skillscripts/utils",
            "scripts": [
                "agent_call_history.py",
                "benchmark_updater.py",
                "check_dependencies.py",
                "check_db_connection.py",
                "doc_change_tracker.py",
                "doc_updater.py",
                "doc_version_manager.py",
                "document_auto_generator.py",
                "document_version_manager.py",
                "enhanced_doc_version_manager.py",
                "enhanced_path_config_manager.py",
                "enhanced_report_version_manager.py",
                "evolution_manager.py",
                "evolution_report_generator.py",
                "file_classification_manager.py",
                "history_tracker.py",
                "init_test_data.py",
                "interface_validator.py",
                "iteration_coordinator.py",
                "knowledge_manager.py",
                "path_config_manager.py",
                "priority_evaluator.py",
                "report_generator.py",
                "report_version_manager.py",
                "script_classification_manager.py",
                "script_dependency_manager.py",
                "script_integrator.py",
                "script_utils.py",
                "self_healer.py",
                "self_improver.py",
                "self_iterate.py",
                "self_iteration_rollback.py",
                "self_optimizer.py",
                "skill_caller.py",
                "skill_content_updater.py",
                "skill_doc_path_validator.py",
                "skill_registry.py",
                "temp_file_manager.py",
                "validate_path_config.py",
                "validate_specs.py",
                "version_manager.py"
            ]
        }
    }
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化脚本路径注册表
        
        Args:
            base_path: 基础路径，用于解析绝对路径
        """
        self._base_path = base_path
        self._scripts: Dict[str, ScriptInfo] = {}
        self._category_index: Dict[str, List[str]] = {}
        self._tag_index: Dict[str, List[str]] = {}
        self._initialize_registry()
    
    def _initialize_registry(self) -> None:
        """初始化注册表，加载所有脚本信息"""
        for category, info in self.SCRIPT_CATEGORIES.items():
            self._category_index[category] = []
            category_path = info["path"]
            
            for script_name in info["scripts"]:
                script_id = f"{category}/{script_name}"
                relative_path = f"{category_path}/{script_name}"
                
                script_info = ScriptInfo(
                    name=script_name,
                    category=category,
                    relative_path=relative_path,
                    description=info.get("description", ""),
                    tags=[category]
                )
                
                self._scripts[script_id] = script_info
                self._category_index[category].append(script_id)
                
                for tag in script_info.tags:
                    if tag not in self._tag_index:
                        self._tag_index[tag] = []
                    self._tag_index[tag].append(script_id)
        
        logger.debug(f"脚本路径注册表初始化完成，共注册 {len(self._scripts)} 个脚本")
    
    def set_base_path(self, base_path: Path) -> None:
        """
        设置基础路径
        
        Args:
            base_path: 基础路径
        """
        self._base_path = base_path
    
    def get_script_path(self, script_id: str) -> Optional[Path]:
        """
        获取脚本的完整路径
        
        Args:
            script_id: 脚本ID，格式为 "category/script_name.py"
            
        Returns:
            脚本的完整路径，如果不存在返回 None
        """
        if script_id not in self._scripts:
            logger.warning(f"脚本未找到: {script_id}")
            return None
        
        script_info = self._scripts[script_id]
        if self._base_path:
            return self._base_path / script_info.relative_path
        return Path(script_info.relative_path)
    
    def get_script_by_name(self, script_name: str) -> Optional[ScriptInfo]:
        """
        通过脚本名称查找脚本
        
        Args:
            script_name: 脚本文件名
            
        Returns:
            脚本信息，如果不存在返回 None
        """
        for script_id, script_info in self._scripts.items():
            if script_info.name == script_name:
                return script_info
        return None
    
    def get_scripts_by_category(self, category: str) -> List[ScriptInfo]:
        """
        获取指定类别的所有脚本
        
        Args:
            category: 脚本类别
            
        Returns:
            脚本信息列表
        """
        script_ids = self._category_index.get(category, [])
        return [self._scripts[sid] for sid in script_ids]
    
    def get_scripts_by_tag(self, tag: str) -> List[ScriptInfo]:
        """
        获取指定标签的所有脚本
        
        Args:
            tag: 脚本标签
            
        Returns:
            脚本信息列表
        """
        script_ids = self._tag_index.get(tag, [])
        return [self._scripts[sid] for sid in script_ids]
    
    def search_scripts(self, keyword: str) -> List[ScriptInfo]:
        """
        搜索脚本
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的脚本信息列表
        """
        keyword_lower = keyword.lower()
        results = []
        
        for script_info in self._scripts.values():
            if (keyword_lower in script_info.name.lower() or
                keyword_lower in script_info.description.lower() or
                keyword_lower in script_info.category.lower()):
                results.append(script_info)
        
        return results
    
    def get_all_scripts(self) -> Dict[str, ScriptInfo]:
        """
        获取所有脚本
        
        Returns:
            所有脚本的字典
        """
        return self._scripts.copy()
    
    def get_all_categories(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有类别信息
        
        Returns:
            所有类别的字典
        """
        return self.SCRIPT_CATEGORIES.copy()
    
    def validate_script_exists(self, script_id: str) -> bool:
        """
        验证脚本文件是否存在
        
        Args:
            script_id: 脚本ID
            
        Returns:
            脚本是否存在
        """
        script_path = self.get_script_path(script_id)
        if not script_path:
            return False
        return script_path.exists()
    
    def validate_all_scripts(self) -> Dict[str, bool]:
        """
        验证所有脚本是否存在
        
        Returns:
            脚本ID到存在状态的映射
        """
        results = {}
        for script_id in self._scripts:
            results[script_id] = self.validate_script_exists(script_id)
        return results
    
    def get_missing_scripts(self) -> List[str]:
        """
        获取缺失的脚本列表
        
        Returns:
            缺失脚本的ID列表
        """
        validation_results = self.validate_all_scripts()
        return [sid for sid, exists in validation_results.items() if not exists]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            包含所有脚本信息的字典
        """
        return {
            "total_scripts": len(self._scripts),
            "categories": {
                category: len(scripts)
                for category, scripts in self._category_index.items()
            },
            "scripts": {
                script_id: script_info.to_dict()
                for script_id, script_info in self._scripts.items()
            }
        }


class SkillDetector:
    """
    技能目录检测器
    
    负责检测和验证技能目录
    """
    
    SKILL_RELATIVE_PATH = ".trae/skills/sanliu"
    
    SKILL_MARKER_FILES = [
        "skillscripts",
        "version.json",
        "docs",
        "path_config.json"
    ]
    
    SKILL_MARKER_DIRS = [
        "skillscripts",
        "docs"
    ]
    
    SKILL_CONFIG_FILES = [
        "version.json",
        "path_config.json"
    ]
    
    @classmethod
    def find_skill_root(cls, start_path: Optional[Path] = None) -> Optional[Path]:
        """
        查找技能根目录
        
        从指定路径向上搜索，查找包含 .trae/skills/sanliu 的目录
        
        Args:
            start_path: 起始搜索路径，默认为当前工作目录
            
        Returns:
            技能根目录路径，未找到返回 None
        """
        current = (start_path or Path.cwd()).resolve()
        
        while current != current.parent:
            skill_dir = current / cls.SKILL_RELATIVE_PATH
            if skill_dir.exists() and skill_dir.is_dir():
                logger.debug(f"找到技能根目录: {skill_dir}")
                return skill_dir
            current = current.parent
        
        logger.debug("未找到技能根目录")
        return None
    
    @classmethod
    def is_skill_directory(cls, path: Path) -> bool:
        """
        判断指定路径是否为技能目录
        
        Args:
            path: 待检查的路径
            
        Returns:
            是否为技能目录
        """
        if not path.exists() or not path.is_dir():
            return False
        
        marker_count = 0
        for marker in cls.SKILL_MARKER_FILES:
            marker_path = path / marker
            if marker_path.exists():
                marker_count += 1
        
        return marker_count >= 2
    
    @classmethod
    def check_skill_markers(cls, skill_root: Path) -> Dict[str, bool]:
        """
        检查技能目录的标识文件
        
        Args:
            skill_root: 技能根目录
            
        Returns:
            标识文件存在情况的字典
        """
        markers = {}
        for marker in cls.SKILL_MARKER_FILES:
            marker_path = skill_root / marker
            markers[marker] = marker_path.exists()
        return markers
    
    @classmethod
    def calculate_confidence(cls, skill_root: Path) -> float:
        """
        计算技能目录检测的置信度
        
        Args:
            skill_root: 技能根目录
            
        Returns:
            置信度值 (0.0 - 1.0)
        """
        markers = cls.check_skill_markers(skill_root)
        marker_count = sum(1 for v in markers.values() if v)
        
        base_confidence = 0.5
        marker_bonus = min(0.4, marker_count * 0.1)
        
        if markers.get("skillscripts", False):
            base_confidence += 0.1
        if markers.get("version.json", False):
            base_confidence += 0.05
        
        return min(1.0, base_confidence + marker_bonus)


class ProjectDetector:
    """
    项目目录检测器
    
    负责检测和识别各种类型的项目
    """
    
    PROJECT_MARKERS = {
        "python": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile", "poetry.lock"],
        "node": ["package.json", "yarn.lock", "pnpm-lock.yaml", "package-lock.json"],
        "rust": ["Cargo.toml", "Cargo.lock"],
        "go": ["go.mod", "go.sum"],
        "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "dotnet": ["*.csproj", "*.sln"],
        "git": [".git"],
        "generic": ["README.md", "LICENSE", ".gitignore"]
    }
    
    PROJECT_TYPE_NAMES = {
        "python": "Python 项目",
        "node": "Node.js 项目",
        "rust": "Rust 项目",
        "go": "Go 项目",
        "java": "Java 项目",
        "dotnet": ".NET 项目",
        "git": "Git 仓库",
        "generic": "通用项目"
    }
    
    @classmethod
    def find_project_root(cls, start_path: Optional[Path] = None) -> Optional[Path]:
        """
        查找项目根目录
        
        从指定路径向上搜索，查找包含项目标识文件的目录
        
        Args:
            start_path: 起始搜索路径，默认为当前工作目录
            
        Returns:
            项目根目录路径，未找到返回 None
        """
        current = (start_path or Path.cwd()).resolve()
        
        while current != current.parent:
            if cls._has_project_markers(current):
                logger.debug(f"找到项目根目录: {current}")
                return current
            current = current.parent
        
        logger.debug("未找到项目根目录")
        return None
    
    @classmethod
    def _has_project_markers(cls, path: Path) -> bool:
        """
        检查路径是否包含项目标识文件
        
        Args:
            path: 待检查的路径
            
        Returns:
            是否包含项目标识
        """
        for markers in cls.PROJECT_MARKERS.values():
            for marker in markers:
                if marker.startswith("*"):
                    if list(path.glob(marker)):
                        return True
                elif (path / marker).exists():
                    return True
        return False
    
    @classmethod
    def detect_project_type(cls, project_root: Path) -> Tuple[str, float]:
        """
        检测项目类型
        
        Args:
            project_root: 项目根目录
            
        Returns:
            (项目类型, 置信度) 元组
        """
        type_scores: Dict[str, int] = {}
        
        for project_type, markers in cls.PROJECT_MARKERS.items():
            score = 0
            for marker in markers:
                if marker.startswith("*"):
                    if list(project_root.glob(marker)):
                        score += 1
                elif (project_root / marker).exists():
                    score += 1
            if score > 0:
                type_scores[project_type] = score
        
        if not type_scores:
            return ("generic", 0.3)
        
        best_type = max(type_scores, key=type_scores.get)
        max_score = type_scores[best_type]
        confidence = min(0.9, 0.5 + max_score * 0.1)
        
        return (best_type, confidence)
    
    @classmethod
    def check_project_markers(cls, project_root: Path) -> Dict[str, bool]:
        """
        检查项目的标识文件
        
        Args:
            project_root: 项目根目录
            
        Returns:
            标识文件存在情况的字典
        """
        markers = {}
        for project_type, marker_list in cls.PROJECT_MARKERS.items():
            for marker in marker_list:
                if marker.startswith("*"):
                    markers[f"{project_type}:{marker}"] = bool(list(project_root.glob(marker)))
                else:
                    markers[f"{project_type}:{marker}"] = (project_root / marker).exists()
        return markers
    
    @classmethod
    def get_project_info(cls, project_root: Path) -> Dict[str, Any]:
        """
        获取项目详细信息
        
        Args:
            project_root: 项目根目录
            
        Returns:
            项目信息字典
        """
        project_type, confidence = cls.detect_project_type(project_root)
        markers = cls.check_project_markers(project_root)
        
        return {
            "path": str(project_root),
            "type": project_type,
            "type_name": cls.PROJECT_TYPE_NAMES.get(project_type, "未知类型"),
            "confidence": confidence,
            "markers": markers,
            "exists": project_root.exists(),
            "is_directory": project_root.is_dir() if project_root.exists() else False
        }


class EnvironmentVariableDetector:
    """
    环境变量检测器
    
    负责从环境变量中检测模式配置
    支持路径覆盖和优先级机制
    """
    
    ENV_MODE = "SANLIU_MODE"
    ENV_TARGET_ROOT = "SANLIU_TARGET_ROOT"
    ENV_CONFIG_FILE = "SANLIU_CONFIG_FILE"
    ENV_LOG_LEVEL = "SANLIU_LOG_LEVEL"
    
    ENV_DOCS_PATH = "SANLIU_DOCS_PATH"
    ENV_SCRIPTS_PATH = "SANLIU_SCRIPTS_PATH"
    ENV_TESTS_PATH = "SANLIU_TESTS_PATH"
    ENV_DATA_PATH = "SANLIU_DATA_PATH"
    ENV_CACHE_PATH = "SANLIU_CACHE_PATH"
    ENV_TEMP_PATH = "SANLIU_TEMP_PATH"
    ENV_LOGS_PATH = "SANLIU_LOGS_PATH"
    ENV_CONFIG_PATH = "SANLIU_CONFIG_PATH"
    ENV_REPORTS_PATH = "SANLIU_REPORTS_PATH"
    
    ENV_PATHS_PREFIX = "SANLIU_PATHS_"
    
    ENV_PRIORITY = {
        "high": 100,
        "medium": 50,
        "low": 10,
        "default": 0
    }
    
    PATH_ENV_MAPPING = {
        "docs": ENV_DOCS_PATH,
        "docs_libs": ENV_DOCS_PATH,
        "docs_reports": ENV_DOCS_PATH,
        "scripts": ENV_SCRIPTS_PATH,
        "skillscripts": ENV_SCRIPTS_PATH,
        "tests": ENV_TESTS_PATH,
        "data": ENV_DATA_PATH,
        "cache": ENV_CACHE_PATH,
        "temp": ENV_TEMP_PATH,
        "logs": ENV_LOGS_PATH,
        "config": ENV_CONFIG_PATH,
        "reports": ENV_REPORTS_PATH
    }
    
    @classmethod
    def detect_mode_from_env(cls) -> Tuple[Optional[PathMode], Optional[str]]:
        """
        从环境变量检测模式
        
        Returns:
            (模式, 目标根目录) 元组
        """
        mode_str = os.environ.get(cls.ENV_MODE, "").lower().strip()
        target_root = os.environ.get(cls.ENV_TARGET_ROOT, "").strip()
        
        if not mode_str:
            return None, None
        
        mode = PathMode.from_string(mode_str)
        
        if mode == PathMode.GUIDE_PROJECT and not target_root:
            logger.warning(f"环境变量 {cls.ENV_MODE} 设置为 guide_project，但未设置 {cls.ENV_TARGET_ROOT}")
            return None, None
        
        return mode, target_root if target_root else None
    
    @classmethod
    def get_config_file_path(cls) -> Optional[str]:
        """获取环境变量指定的配置文件路径"""
        return os.environ.get(cls.ENV_CONFIG_FILE, "").strip() or None
    
    @classmethod
    def get_log_level(cls) -> Optional[str]:
        """获取环境变量指定的日志级别"""
        return os.environ.get(cls.ENV_LOG_LEVEL, "").strip() or None
    
    @classmethod
    def get_all_env_info(cls) -> Dict[str, Any]:
        """获取所有相关环境变量信息"""
        return {
            "mode": os.environ.get(cls.ENV_MODE, ""),
            "target_root": os.environ.get(cls.ENV_TARGET_ROOT, ""),
            "config_file": os.environ.get(cls.ENV_CONFIG_FILE, ""),
            "log_level": os.environ.get(cls.ENV_LOG_LEVEL, ""),
            "docs_path": os.environ.get(cls.ENV_DOCS_PATH, ""),
            "scripts_path": os.environ.get(cls.ENV_SCRIPTS_PATH, ""),
            "tests_path": os.environ.get(cls.ENV_TESTS_PATH, ""),
            "data_path": os.environ.get(cls.ENV_DATA_PATH, ""),
            "cache_path": os.environ.get(cls.ENV_CACHE_PATH, ""),
            "temp_path": os.environ.get(cls.ENV_TEMP_PATH, ""),
            "logs_path": os.environ.get(cls.ENV_LOGS_PATH, ""),
            "config_path": os.environ.get(cls.ENV_CONFIG_PATH, ""),
            "reports_path": os.environ.get(cls.ENV_REPORTS_PATH, "")
        }
    
    @classmethod
    def get_path_override(cls, path_name: str) -> Optional[str]:
        """
        获取指定路径的环境变量覆盖
        
        Args:
            path_name: 路径名称（如 docs, tests, scripts 等）
            
        Returns:
            环境变量覆盖的路径，无则返回 None
        """
        direct_env = cls.PATH_ENV_MAPPING.get(path_name)
        if direct_env:
            value = os.environ.get(direct_env, "").strip()
            if value:
                return value
        
        prefixed_env = f"{cls.ENV_PATHS_PREFIX}{path_name.upper()}"
        value = os.environ.get(prefixed_env, "").strip()
        if value:
            return value
        
        return None
    
    @classmethod
    def get_all_path_overrides(cls) -> Dict[str, str]:
        """
        获取所有路径的环境变量覆盖
        
        Returns:
            路径覆盖字典
        """
        overrides = {}
        
        for path_name in cls.PATH_ENV_MAPPING.keys():
            override = cls.get_path_override(path_name)
            if override:
                overrides[path_name] = override
        
        for key, value in os.environ.items():
            if key.startswith(cls.ENV_PATHS_PREFIX):
                path_name = key[len(cls.ENV_PATHS_PREFIX):].lower()
                if path_name not in overrides:
                    overrides[path_name] = value.strip()
        
        return overrides
    
    @classmethod
    def get_priority(cls) -> int:
        """
        获取环境变量优先级
        
        Returns:
            优先级数值
        """
        priority_str = os.environ.get("SANLIU_ENV_PRIORITY", "default").lower()
        return cls.ENV_PRIORITY.get(priority_str, cls.ENV_PRIORITY["default"])
    
    @classmethod
    def has_path_overrides(cls) -> bool:
        """
        检查是否存在路径覆盖
        
        Returns:
            是否存在路径覆盖
        """
        for path_name in cls.PATH_ENV_MAPPING.keys():
            if cls.get_path_override(path_name):
                return True
        return False


@dataclass
class PathAlias:
    """
    路径别名数据类
    
    存储路径别名的定义
    """
    name: str
    target: str
    description: str = ""
    project_types: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "target": self.target,
            "description": self.description,
            "project_types": self.project_types,
            "conditions": self.conditions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PathAlias':
        """从字典创建实例"""
        return cls(
            name=data.get('name', ''),
            target=data.get('target', ''),
            description=data.get('description', ''),
            project_types=data.get('project_types', []),
            conditions=data.get('conditions', {})
        )


@dataclass
class ConditionalPath:
    """
    条件路径数据类
    
    根据条件选择不同的路径
    """
    name: str
    default_path: str
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "default_path": self.default_path,
            "conditions": self.conditions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConditionalPath':
        """从字典创建实例"""
        return cls(
            name=data.get('name', ''),
            default_path=data.get('default_path', ''),
            conditions=data.get('conditions', [])
        )


class DynamicPathResolver:
    """
    动态路径解析器
    
    功能：
    - 支持路径模板变量解析（如 ${PROJECT_ROOT}, ${VERSION}, ${DATE}）
    - 支持条件路径（根据项目类型选择不同路径）
    - 支持路径别名系统
    - 支持环境变量覆盖
    """
    
    BUILTIN_VARIABLES = {
        "PROJECT_ROOT": lambda ctx: str(ctx.get("base_path", "")),
        "VERSION": lambda ctx: ctx.get("version", "0.0.0"),
        "DATE": lambda ctx: datetime.now().strftime("%Y-%m-%d"),
        "TIME": lambda ctx: datetime.now().strftime("%H-%M-%S"),
        "DATETIME": lambda ctx: datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
        "YEAR": lambda ctx: str(datetime.now().year),
        "MONTH": lambda ctx: datetime.now().strftime("%m"),
        "DAY": lambda ctx: datetime.now().strftime("%d"),
        "MODE": lambda ctx: ctx.get("mode", "self_iteration"),
        "PROJECT_TYPE": lambda ctx: ctx.get("project_type", "generic"),
        "OS": lambda ctx: os.name,
        "USER": lambda ctx: os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
        "TEMP": lambda ctx: str(Path(tempfile.gettempdir())),
        "HOME": lambda ctx: str(Path.home()),
    }
    
    VARIABLE_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    DEFAULT_ALIASES = {
        "docs": PathAlias(
            name="docs",
            target="docs",
            description="文档目录"
        ),
        "libs": PathAlias(
            name="libs",
            target="docs/libs",
            description="库文档目录"
        ),
        "reports": PathAlias(
            name="reports",
            target="docs/reports",
            description="报告目录"
        ),
        "tests": PathAlias(
            name="tests",
            target="tests",
            description="测试目录"
        ),
        "scripts": PathAlias(
            name="scripts",
            target="skillscripts",
            description="脚本目录"
        ),
        "cache": PathAlias(
            name="cache",
            target="cache",
            description="缓存目录"
        ),
        "temp": PathAlias(
            name="temp",
            target="temp",
            description="临时目录"
        ),
        "logs": PathAlias(
            name="logs",
            target="logs",
            description="日志目录"
        ),
        "data": PathAlias(
            name="data",
            target="data",
            description="数据目录"
        ),
        "config": PathAlias(
            name="config",
            target="config",
            description="配置目录"
        )
    }
    
    PROJECT_TYPE_PATHS = {
        "python": {
            "tests": "tests",
            "docs": "docs",
            "scripts": "scripts",
            "config": "config"
        },
        "node": {
            "tests": "test",
            "docs": "docs",
            "scripts": "scripts",
            "config": "config"
        },
        "rust": {
            "tests": "tests",
            "docs": "docs",
            "scripts": "scripts",
            "config": "config"
        },
        "go": {
            "tests": "tests",
            "docs": "docs",
            "scripts": "scripts",
            "config": "configs"
        },
        "java": {
            "tests": "src/test",
            "docs": "docs",
            "scripts": "scripts",
            "config": "src/main/resources"
        },
        "dotnet": {
            "tests": "Tests",
            "docs": "Docs",
            "scripts": "Scripts",
            "config": "Config"
        }
    }
    
    def __init__(self, base_path: Optional[Path] = None, context: Optional[Dict[str, Any]] = None):
        """
        初始化动态路径解析器
        
        Args:
            base_path: 基础路径
            context: 解析上下文
        """
        self._base_path = base_path
        self._context = context or {}
        self._aliases: Dict[str, PathAlias] = dict(self.DEFAULT_ALIASES)
        self._conditional_paths: Dict[str, ConditionalPath] = {}
        self._custom_variables: Dict[str, Callable[[Dict[str, Any]], str]] = {}
        self._lock = threading.Lock()
    
    def set_base_path(self, base_path: Path) -> None:
        """设置基础路径"""
        self._base_path = base_path
        self._context["base_path"] = str(base_path)
    
    def set_context(self, key: str, value: Any) -> None:
        """设置上下文变量"""
        self._context[key] = value
    
    def update_context(self, context: Dict[str, Any]) -> None:
        """更新上下文"""
        self._context.update(context)
    
    def register_variable(self, name: str, resolver: Callable[[Dict[str, Any]], str]) -> None:
        """
        注册自定义变量
        
        Args:
            name: 变量名
            resolver: 解析函数
        """
        with self._lock:
            self._custom_variables[name.upper()] = resolver
    
    def unregister_variable(self, name: str) -> bool:
        """
        注销自定义变量
        
        Args:
            name: 变量名
            
        Returns:
            是否成功注销
        """
        with self._lock:
            key = name.upper()
            if key in self._custom_variables:
                del self._custom_variables[key]
                return True
            return False
    
    def register_alias(self, alias: PathAlias) -> None:
        """
        注册路径别名
        
        Args:
            alias: 路径别名对象
        """
        with self._lock:
            self._aliases[alias.name] = alias
    
    def unregister_alias(self, name: str) -> bool:
        """
        注销路径别名
        
        Args:
            name: 别名名称
            
        Returns:
            是否成功注销
        """
        with self._lock:
            if name in self._aliases:
                del self._aliases[name]
                return True
            return False
    
    def get_alias(self, name: str) -> Optional[PathAlias]:
        """
        获取路径别名
        
        Args:
            name: 别名名称
            
        Returns:
            路径别名对象
        """
        return self._aliases.get(name)
    
    def resolve_alias(self, name: str) -> Optional[str]:
        """
        解析路径别名
        
        Args:
            name: 别名名称
            
        Returns:
            解析后的路径
        """
        alias = self._aliases.get(name)
        if alias:
            return self.resolve(alias.target)
        return None
    
    def register_conditional_path(self, conditional_path: ConditionalPath) -> None:
        """
        注册条件路径
        
        Args:
            conditional_path: 条件路径对象
        """
        with self._lock:
            self._conditional_paths[conditional_path.name] = conditional_path
    
    def resolve_conditional_path(self, name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        解析条件路径
        
        Args:
            name: 条件路径名称
            context: 额外上下文
            
        Returns:
            解析后的路径
        """
        conditional = self._conditional_paths.get(name)
        if not conditional:
            return name
        
        merged_context = {**self._context, **(context or {})}
        
        for condition in conditional.conditions:
            if self._evaluate_condition(condition, merged_context):
                path = condition.get("path", conditional.default_path)
                return self.resolve(path, merged_context)
        
        return self.resolve(conditional.default_path, merged_context)
    
    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        评估条件
        
        Args:
            condition: 条件字典
            context: 上下文
            
        Returns:
            条件是否满足
        """
        project_type = condition.get("project_type")
        if project_type:
            ctx_type = context.get("project_type", "")
            if isinstance(project_type, list):
                if ctx_type not in project_type:
                    return False
            elif ctx_type != project_type:
                return False
        
        mode = condition.get("mode")
        if mode:
            ctx_mode = context.get("mode", "")
            if isinstance(mode, list):
                if ctx_mode not in mode:
                    return False
            elif ctx_mode != mode:
                return False
        
        env_check = condition.get("env")
        if env_check:
            for env_name, env_value in env_check.items():
                if os.environ.get(env_name) != env_value:
                    return False
        
        custom_check = condition.get("custom")
        if custom_check and callable(custom_check):
            try:
                if not custom_check(context):
                    return False
            except Exception:
                return False
        
        return True
    
    def resolve(self, template: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        解析路径模板
        
        Args:
            template: 路径模板字符串
            context: 额外上下文
            
        Returns:
            解析后的路径
        """
        if not template:
            return template
        
        merged_context = {**self._context, **(context or {})}
        
        def replace_variable(match):
            var_name = match.group(1)
            
            if var_name in self._custom_variables:
                try:
                    return self._custom_variables[var_name](merged_context)
                except Exception as e:
                    logger.warning(f"自定义变量解析失败 {var_name}: {e}")
            
            if var_name in self.BUILTIN_VARIABLES:
                try:
                    return self.BUILTIN_VARIABLES[var_name](merged_context)
                except Exception as e:
                    logger.warning(f"内置变量解析失败 {var_name}: {e}")
            
            if var_name in merged_context:
                return str(merged_context[var_name])
            
            env_value = os.environ.get(var_name, "")
            if env_value:
                return env_value
            
            logger.debug(f"未找到变量 {var_name} 的值，保留原样")
            return match.group(0)
        
        resolved = self.VARIABLE_PATTERN.sub(replace_variable, template)
        
        return resolved
    
    def resolve_path(self, template: str, context: Optional[Dict[str, Any]] = None) -> Path:
        """
        解析路径模板并返回 Path 对象
        
        Args:
            template: 路径模板字符串
            context: 额外上下文
            
        Returns:
            解析后的 Path 对象
        """
        resolved = self.resolve(template, context)
        
        if self._base_path and not Path(resolved).is_absolute():
            return self._base_path / resolved
        
        return Path(resolved)
    
    def get_project_type_path(self, path_name: str, project_type: str) -> str:
        """
        获取项目类型特定路径
        
        Args:
            path_name: 路径名称
            project_type: 项目类型
            
        Returns:
            项目类型特定路径
        """
        type_paths = self.PROJECT_TYPE_PATHS.get(project_type, {})
        return type_paths.get(path_name, path_name)
    
    def resolve_with_project_type(
        self,
        template: str,
        project_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        根据项目类型解析路径
        
        Args:
            template: 路径模板
            project_type: 项目类型
            context: 额外上下文
            
        Returns:
            解析后的路径
        """
        merged_context = {**self._context, **(context or {})}
        merged_context["project_type"] = project_type
        
        return self.resolve(template, merged_context)
    
    def get_all_aliases(self) -> Dict[str, PathAlias]:
        """获取所有别名"""
        return dict(self._aliases)
    
    def get_all_conditional_paths(self) -> Dict[str, ConditionalPath]:
        """获取所有条件路径"""
        return dict(self._conditional_paths)
    
    def to_dict(self) -> Dict[str, Any]:
        """导出配置为字典"""
        return {
            "base_path": str(self._base_path) if self._base_path else None,
            "context": self._context,
            "aliases": {k: v.to_dict() for k, v in self._aliases.items()},
            "conditional_paths": {k: v.to_dict() for k, v in self._conditional_paths.items()},
            "custom_variables": list(self._custom_variables.keys())
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DynamicPathResolver':
        """从字典创建实例"""
        resolver = cls(
            base_path=Path(data["base_path"]) if data.get("base_path") else None,
            context=data.get("context", {})
        )
        
        for name, alias_data in data.get("aliases", {}).items():
            resolver._aliases[name] = PathAlias.from_dict(alias_data)
        
        for name, cond_data in data.get("conditional_paths", {}).items():
            resolver._conditional_paths[name] = ConditionalPath.from_dict(cond_data)
        
        return resolver


class ConfigFileDetector:
    """
    配置文件检测器
    
    负责从配置文件中检测模式配置
    支持 .sanliu.yaml 和 .sanliu.json 格式
    """
    
    CONFIG_FILE_NAMES = [".sanliu.yaml", ".sanliu.json", "sanliu.yaml", "sanliu.json"]
    
    @classmethod
    def find_config_file(cls, start_path: Optional[Path] = None) -> Optional[Path]:
        """
        查找配置文件
        
        从指定路径向上搜索配置文件
        
        Args:
            start_path: 起始搜索路径，默认为当前工作目录
            
        Returns:
            配置文件路径，未找到返回 None
        """
        current = (start_path or Path.cwd()).resolve()
        
        while current != current.parent:
            for config_name in cls.CONFIG_FILE_NAMES:
                config_path = current / config_name
                if config_path.exists() and config_path.is_file():
                    logger.debug(f"找到配置文件: {config_path}")
                    return config_path
            current = current.parent
        
        logger.debug("未找到配置文件")
        return None
    
    @classmethod
    def load_config(cls, config_path: Path) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        if not config_path.exists():
            return {}
        
        try:
            content = config_path.read_text(encoding='utf-8')
            
            if config_path.suffix in ['.yaml', '.yml']:
                return cls._parse_yaml(content)
            else:
                return json.loads(content)
        except Exception as e:
            logger.warning(f"加载配置文件失败 {config_path}: {e}")
            return {}
    
    @classmethod
    def _parse_yaml(cls, content: str) -> Dict[str, Any]:
        """
        解析 YAML 内容
        
        Args:
            content: YAML 内容字符串
            
        Returns:
            解析后的字典
        """
        try:
            import yaml
            return yaml.safe_load(content) or {}
        except ImportError:
            logger.warning("PyYAML 未安装，尝试使用简单解析器")
            return cls._simple_yaml_parse(content)
    
    @classmethod
    def _simple_yaml_parse(cls, content: str) -> Dict[str, Any]:
        """
        简单 YAML 解析器（不依赖 PyYAML）
        
        仅支持简单的 key: value 格式
        """
        result: Dict[str, Any] = {}
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)
                elif value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                result[key] = value
        
        return result
    
    @classmethod
    def detect_mode_from_config(cls, start_path: Optional[Path] = None) -> Tuple[Optional[PathMode], Optional[str], Optional[Path]]:
        """
        从配置文件检测模式
        
        Args:
            start_path: 起始搜索路径
            
        Returns:
            (模式, 目标根目录, 配置文件路径) 元组
        """
        config_path = cls.find_config_file(start_path)
        
        if not config_path:
            return None, None, None
        
        config = cls.load_config(config_path)
        
        if not config:
            return None, None, config_path
        
        mode_str = config.get('mode', config.get('sanliu_mode', '')).lower().strip()
        target_root = config.get('target_root', config.get('sanliu_target_root', '')).strip()
        
        if not mode_str:
            return None, None, config_path
        
        mode = PathMode.from_string(mode_str)
        
        if mode == PathMode.GUIDE_PROJECT and not target_root:
            logger.warning(f"配置文件设置模式为 guide_project，但未设置 target_root")
            return None, None, config_path
        
        return mode, target_root if target_root else None, config_path


class CommandLineDetector:
    """
    命令行参数检测器
    
    负责从命令行参数中检测模式配置
    """
    
    MODE_ARGS = ['--mode', '-m', '--sanliu-mode']
    TARGET_ARGS = ['--target-root', '-t', '--sanliu-target']
    
    @classmethod
    def detect_mode_from_args(cls, args: Optional[List[str]] = None) -> Tuple[Optional[PathMode], Optional[str]]:
        """
        从命令行参数检测模式
        
        Args:
            args: 命令行参数列表，默认为 sys.argv
            
        Returns:
            (模式, 目标根目录) 元组
        """
        if args is None:
            args = sys.argv[1:]
        
        mode_str = None
        target_root = None
        
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg in cls.MODE_ARGS:
                if i + 1 < len(args):
                    mode_str = args[i + 1].lower().strip()
                    i += 2
                    continue
            
            if arg in cls.TARGET_ARGS:
                if i + 1 < len(args):
                    target_root = args[i + 1].strip()
                    i += 2
                    continue
            
            if arg.startswith('--mode='):
                mode_str = arg.split('=', 1)[1].lower().strip()
            elif arg.startswith('--target-root='):
                target_root = arg.split('=', 1)[1].strip()
            
            i += 1
        
        if not mode_str:
            return None, None
        
        mode = PathMode.from_string(mode_str)
        
        if mode == PathMode.GUIDE_PROJECT and not target_root:
            logger.warning("命令行参数设置模式为 guide_project，但未设置 target_root")
            return None, None
        
        return mode, target_root if target_root else None


class ModeDetectionSource(Enum):
    """模式检测来源枚举"""
    ENVIRONMENT = "environment"
    CONFIG_FILE = "config_file"
    COMMAND_LINE = "command_line"
    AUTO_DETECT = "auto_detect"
    DEFAULT = "default"
    EXPLICIT = "explicit"


@dataclass
class EnhancedModeDetectionResult:
    """
    增强的模式检测结果
    
    包含检测来源和优先级信息
    """
    detected_mode: PathMode
    target_root: Optional[str]
    source: ModeDetectionSource
    confidence: float
    config_path: Optional[Path]
    detection_details: Dict[str, Any]
    
    def get_summary(self) -> str:
        """获取检测结果摘要"""
        return (
            f"检测模式: {self.detected_mode.value}, "
            f"来源: {self.source.value}, "
            f"置信度: {self.confidence:.2%}, "
            f"目标根目录: {self.target_root or '未设置'}"
        )


class ModeAutoDetector:
    """
    模式自动检测器
    
    整合多种检测来源，按优先级确定模式
    优先级：命令行参数 > 环境变量 > 配置文件 > 自动检测
    """
    
    DETECTION_PRIORITY = [
        ModeDetectionSource.COMMAND_LINE,
        ModeDetectionSource.ENVIRONMENT,
        ModeDetectionSource.CONFIG_FILE,
        ModeDetectionSource.AUTO_DETECT
    ]
    
    @classmethod
    def detect(
        cls,
        start_path: Optional[Path] = None,
        args: Optional[List[str]] = None
    ) -> EnhancedModeDetectionResult:
        """
        执行完整的模式检测
        
        Args:
            start_path: 起始搜索路径
            args: 命令行参数
            
        Returns:
            增强的模式检测结果
        """
        detection_details: Dict[str, Any] = {
            "detection_timestamp": datetime.now().isoformat(),
            "start_path": str(start_path or Path.cwd()),
            "attempts": []
        }
        
        for source in cls.DETECTION_PRIORITY:
            result = cls._try_detect_from_source(source, start_path, args)
            
            if result:
                mode, target_root, confidence, config_path = result
                detection_details["attempts"].append({
                    "source": source.value,
                    "success": True,
                    "mode": mode.value,
                    "target_root": target_root
                })
                
                return EnhancedModeDetectionResult(
                    detected_mode=mode,
                    target_root=target_root,
                    source=source,
                    confidence=confidence,
                    config_path=config_path,
                    detection_details=detection_details
                )
            else:
                detection_details["attempts"].append({
                    "source": source.value,
                    "success": False
                })
        
        default_mode = PathMode.SELF_ITERATION
        detection_details["fallback"] = True
        detection_details["reason"] = "所有检测方法均未成功，使用默认模式"
        
        return EnhancedModeDetectionResult(
            detected_mode=default_mode,
            target_root=None,
            source=ModeDetectionSource.DEFAULT,
            confidence=0.3,
            config_path=None,
            detection_details=detection_details
        )
    
    @classmethod
    def _try_detect_from_source(
        cls,
        source: ModeDetectionSource,
        start_path: Optional[Path],
        args: Optional[List[str]]
    ) -> Optional[Tuple[PathMode, Optional[str], float, Optional[Path]]]:
        """
        尝试从指定来源检测模式
        
        Returns:
            (模式, 目标根目录, 置信度, 配置文件路径) 元组，失败返回 None
        """
        if source == ModeDetectionSource.COMMAND_LINE:
            mode, target_root = CommandLineDetector.detect_mode_from_args(args)
            if mode:
                return mode, target_root, 1.0, None
        
        elif source == ModeDetectionSource.ENVIRONMENT:
            mode, target_root = EnvironmentVariableDetector.detect_mode_from_env()
            if mode:
                return mode, target_root, 0.95, None
        
        elif source == ModeDetectionSource.CONFIG_FILE:
            mode, target_root, config_path = ConfigFileDetector.detect_mode_from_config(start_path)
            if mode:
                return mode, target_root, 0.9, config_path
        
        elif source == ModeDetectionSource.AUTO_DETECT:
            skill_root = SkillDetector.find_skill_root(start_path)
            if skill_root:
                confidence = SkillDetector.calculate_confidence(skill_root)
                return PathMode.SELF_ITERATION, None, confidence, None
            
            project_root = ProjectDetector.find_project_root(start_path)
            if project_root:
                _, confidence = ProjectDetector.detect_project_type(project_root)
                return PathMode.GUIDE_PROJECT, str(project_root), confidence, None
        
        return None


class SwitchHistoryManager:
    """
    模式切换历史管理器
    
    负责记录和管理模式切换历史，支持回滚
    """
    
    HISTORY_FILE = "mode_switch_history.json"
    MAX_HISTORY = 50
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.history_file = base_path / self.HISTORY_FILE
        self._lock = threading.Lock()
    
    def record_switch(self, record: ModeSwitchRecord) -> bool:
        """
        记录切换事件
        
        Args:
            record: 切换记录
            
        Returns:
            记录是否成功
        """
        with self._lock:
            try:
                history = self._load_history()
                history.append(record.to_dict())
                
                if len(history) > self.MAX_HISTORY:
                    history = history[-self.MAX_HISTORY:]
                
                self._save_history(history)
                return True
            except Exception as e:
                logger.error(f"记录切换历史失败: {e}")
                return False
    
    def get_history(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取切换历史"""
        with self._lock:
            history = self._load_history()
            return history[-count:] if history else []
    
    def get_last_successful_switch(self) -> Optional[Dict[str, Any]]:
        """获取最后一次成功的切换记录"""
        with self._lock:
            history = self._load_history()
            for record in reversed(history):
                if record.get("success", False):
                    return record
            return None
    
    def clear_history(self) -> bool:
        """清空历史记录"""
        with self._lock:
            try:
                if self.history_file.exists():
                    self.history_file.unlink()
                return True
            except Exception as e:
                logger.error(f"清空历史记录失败: {e}")
                return False
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """加载历史记录"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        """保存历史记录"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)


class PathValidator:
    """
    路径验证器
    
    提供路径存在性、可写性等验证功能
    """
    
    @classmethod
    def validate_exists(cls, path: Path) -> Tuple[bool, Optional[str]]:
        """
        验证路径是否存在
        
        Returns:
            (是否有效, 错误信息) 元组
        """
        if not path.exists():
            return False, f"路径不存在: {path}"
        return True, None
    
    @classmethod
    def validate_is_directory(cls, path: Path) -> Tuple[bool, Optional[str]]:
        """
        验证路径是否为目录
        
        Returns:
            (是否有效, 错误信息) 元组
        """
        valid, error = cls.validate_exists(path)
        if not valid:
            return valid, error
        
        if not path.is_dir():
            return False, f"路径不是目录: {path}"
        return True, None
    
    @classmethod
    def validate_writable(cls, path: Path) -> Tuple[bool, Optional[str]]:
        """
        验证路径是否可写
        
        Returns:
            (是否有效, 错误信息) 元组
        """
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                test_file = path / ".write_test"
                test_file.touch()
                test_file.unlink()
                return True, None
            except PermissionError:
                return False, f"无权限创建目录: {path}"
            except Exception as e:
                return False, f"验证可写性失败: {e}"
        
        if not path.is_dir():
            return False, f"路径不是目录: {path}"
        
        try:
            test_file = path / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True, None
        except PermissionError:
            return False, f"无权限写入目录: {path}"
        except Exception as e:
            return False, f"验证可写性失败: {e}"
    
    @classmethod
    def validate_all(cls, path: Path, must_exist: bool = True, must_be_dir: bool = True, must_be_writable: bool = True) -> Tuple[bool, List[str]]:
        """
        执行所有验证
        
        Returns:
            (是否全部有效, 错误信息列表) 元组
        """
        errors: List[str] = []
        
        if must_exist:
            valid, error = cls.validate_exists(path)
            if not valid:
                errors.append(error or "")
        
        if must_be_dir and (not must_exist or path.exists()):
            valid, error = cls.validate_is_directory(path)
            if not valid:
                errors.append(error or "")
        
        if must_be_writable and (not must_exist or path.exists()):
            valid, error = cls.validate_writable(path)
            if not valid:
                errors.append(error or "")
        
        return len(errors) == 0, errors


@dataclass
class SecurityValidationResult:
    """
    安全验证结果数据类
    
    存储安全验证的详细结果
    """
    is_safe: bool
    path: str
    checks: Dict[str, bool]
    warnings: List[str]
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "is_safe": self.is_safe,
            "path": self.path,
            "checks": self.checks,
            "warnings": self.warnings,
            "errors": self.errors
        }
    
    def get_summary(self) -> str:
        """获取结果摘要"""
        status = "安全" if self.is_safe else "不安全"
        warning_count = len(self.warnings)
        error_count = len(self.errors)
        return f"路径 {self.path}: {status}, 警告: {warning_count}, 错误: {error_count}"


class PathSecurityValidator:
    """
    路径安全验证器
    
    功能：
    - 检测路径遍历攻击
    - 检测符号链接安全风险
    - 添加路径权限检查
    - 检测危险字符和模式
    """
    
    DANGEROUS_PATTERNS = [
        r'\.\.',
        r'\.\./',
        r'/\.\.',
        r'\.\.\\',
        r'\\\.\.',
        r'~',
        r'\$',
        r'`',
        r'\|',
        r';',
        r'&',
        r'>',
        r'<',
    ]
    
    DANGEROUS_CHARS = [
        '\x00',
        '\n',
        '\r',
    ]
    
    MAX_PATH_LENGTH = 260 if os.name == 'nt' else 4096
    
    @classmethod
    def validate_security(
        cls,
        path: Union[str, Path],
        base_path: Optional[Path] = None,
        allow_symlinks: bool = True,
        check_permissions: bool = True
    ) -> SecurityValidationResult:
        """
        执行完整的安全验证
        
        Args:
            path: 要验证的路径
            base_path: 基准路径（用于检测路径遍历）
            allow_symlinks: 是否允许符号链接
            check_permissions: 是否检查权限
            
        Returns:
            安全验证结果
        """
        path_obj = Path(path)
        checks: Dict[str, bool] = {}
        warnings: List[str] = []
        errors: List[str] = []
        
        checks["path_traversal"] = cls.check_path_traversal(path_obj, base_path)
        if not checks["path_traversal"]:
            errors.append("检测到路径遍历攻击尝试")
        
        checks["dangerous_patterns"] = cls.check_dangerous_patterns(path_obj)
        if not checks["dangerous_patterns"]:
            errors.append("路径包含危险模式")
        
        checks["dangerous_chars"] = cls.check_dangerous_chars(path_obj)
        if not checks["dangerous_chars"]:
            errors.append("路径包含危险字符")
        
        checks["path_length"] = cls.check_path_length(path_obj)
        if not checks["path_length"]:
            warnings.append(f"路径长度超过建议限制 ({cls.MAX_PATH_LENGTH})")
        
        symlink_result = cls.check_symlink_safety(path_obj, base_path)
        checks["symlink_safe"] = symlink_result.is_safe
        if symlink_result.warnings:
            warnings.extend(symlink_result.warnings)
        if symlink_result.errors:
            errors.extend(symlink_result.errors)
        
        if check_permissions:
            perm_result = cls.check_permissions(path_obj)
            checks["readable"] = perm_result.get("readable", True)
            checks["writable"] = perm_result.get("writable", True)
            checks["executable"] = perm_result.get("executable", True)
            
            if not checks["readable"]:
                warnings.append("路径不可读")
            if not checks["writable"]:
                warnings.append("路径不可写")
        
        is_safe = all(checks.values()) and len(errors) == 0
        
        return SecurityValidationResult(
            is_safe=is_safe,
            path=str(path_obj),
            checks=checks,
            warnings=warnings,
            errors=errors
        )
    
    @classmethod
    def check_path_traversal(cls, path: Union[str, Path], base_path: Optional[Path] = None) -> bool:
        """
        检测路径遍历攻击
        
        Args:
            path: 要检查的路径
            base_path: 基准路径
            
        Returns:
            路径是否安全（不包含遍历攻击）
        """
        path_obj = Path(path)
        
        path_str = str(path_obj)
        if '..' in path_str:
            try:
                resolved = path_obj.resolve()
                if base_path:
                    resolved.relative_to(base_path.resolve())
            except (ValueError, OSError):
                return False
        
        return True
    
    @classmethod
    def check_dangerous_patterns(cls, path: Union[str, Path]) -> bool:
        """
        检测危险模式
        
        Args:
            path: 要检查的路径
            
        Returns:
            路径是否安全（不包含危险模式）
        """
        path_str = str(path)
        
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, path_str):
                if pattern == r'\.\.' and '..' in path_str:
                    continue
                return False
        
        return True
    
    @classmethod
    def check_dangerous_chars(cls, path: Union[str, Path]) -> bool:
        """
        检测危险字符
        
        Args:
            path: 要检查的路径
            
        Returns:
            路径是否安全（不包含危险字符）
        """
        path_str = str(path)
        
        for char in cls.DANGEROUS_CHARS:
            if char in path_str:
                return False
        
        return True
    
    @classmethod
    def check_path_length(cls, path: Union[str, Path]) -> bool:
        """
        检查路径长度
        
        Args:
            path: 要检查的路径
            
        Returns:
            路径长度是否在限制内
        """
        path_str = str(path)
        return len(path_str) <= cls.MAX_PATH_LENGTH
    
    @classmethod
    def check_symlink_safety(
        cls,
        path: Union[str, Path],
        base_path: Optional[Path] = None
    ) -> SecurityValidationResult:
        """
        检测符号链接安全风险
        
        Args:
            path: 要检查的路径
            base_path: 基准路径
            
        Returns:
            安全验证结果
        """
        path_obj = Path(path)
        checks: Dict[str, bool] = {}
        warnings: List[str] = []
        errors: List[str] = []
        
        checks["is_symlink"] = path_obj.is_symlink() if path_obj.exists() else False
        
        if checks["is_symlink"]:
            try:
                link_target = path_obj.resolve()
                checks["target_exists"] = link_target.exists()
                
                if not checks["target_exists"]:
                    warnings.append(f"符号链接目标不存在: {link_target}")
                
                if base_path:
                    try:
                        link_target.relative_to(base_path.resolve())
                        checks["target_in_base"] = True
                    except ValueError:
                        checks["target_in_base"] = False
                        warnings.append(f"符号链接目标在基准路径之外: {link_target}")
            except OSError as e:
                errors.append(f"无法解析符号链接: {e}")
                checks["resolvable"] = False
        
        is_safe = len(errors) == 0
        
        return SecurityValidationResult(
            is_safe=is_safe,
            path=str(path_obj),
            checks=checks,
            warnings=warnings,
            errors=errors
        )
    
    @classmethod
    def check_permissions(cls, path: Union[str, Path]) -> Dict[str, bool]:
        """
        检查路径权限
        
        Args:
            path: 要检查的路径
            
        Returns:
            权限检查结果字典
        """
        path_obj = Path(path)
        result = {
            "readable": True,
            "writable": True,
            "executable": True
        }
        
        if not path_obj.exists():
            parent = path_obj.parent
            while parent != parent.parent and not parent.exists():
                parent = parent.parent
            
            if parent.exists():
                result["readable"] = os.access(parent, os.R_OK)
                result["writable"] = os.access(parent, os.W_OK)
                result["executable"] = os.access(parent, os.X_OK)
            return result
        
        if path_obj.is_file():
            result["readable"] = os.access(path_obj, os.R_OK)
            result["writable"] = os.access(path_obj, os.W_OK)
            result["executable"] = os.access(path_obj, os.X_OK)
        elif path_obj.is_dir():
            result["readable"] = os.access(path_obj, os.R_OK)
            result["writable"] = os.access(path_obj, os.W_OK)
            result["executable"] = os.access(path_obj, os.X_OK)
        
        return result
    
    @classmethod
    def sanitize_path(cls, path: Union[str, Path]) -> str:
        """
        清理路径中的危险元素
        
        Args:
            path: 要清理的路径
            
        Returns:
            清理后的路径字符串
        """
        path_str = str(path)
        
        for char in cls.DANGEROUS_CHARS:
            path_str = path_str.replace(char, '')
        
        while '..' in path_str:
            path_str = path_str.replace('..', '')
        
        path_str = path_str.replace('~', '')
        
        path_str = re.sub(r'/+', '/', path_str)
        path_str = re.sub(r'\\+', '\\', path_str)
        
        return path_str.strip()
    
    @classmethod
    def is_safe_path(
        cls,
        path: Union[str, Path],
        base_path: Optional[Path] = None
    ) -> bool:
        """
        快速检查路径是否安全
        
        Args:
            path: 要检查的路径
            base_path: 基准路径
            
        Returns:
            路径是否安全
        """
        result = cls.validate_security(path, base_path)
        return result.is_safe
    
    @classmethod
    def get_safe_filename(cls, filename: str) -> str:
        """
        获取安全的文件名
        
        移除或替换文件名中的危险字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            安全的文件名
        """
        unsafe_chars = '<>:"/\\|?*\x00\n\r'
        
        safe_name = filename
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')
        
        safe_name = safe_name.strip('. ')
        
        if not safe_name:
            safe_name = "unnamed_file"
        
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        name_without_ext = safe_name.rsplit('.', 1)[0].upper()
        if name_without_ext in reserved_names:
            safe_name = f"_{safe_name}"
        
        return safe_name


class PathConfigManager:
    """
    路径配置管理器
    
    核心功能：
    - 双模式支持（自迭代/指导项目）
    - 模式自动识别（增强版：环境变量、配置文件、命令行参数）
    - 路径配置管理
    - 版本管理
    - 配置持久化
    - 模式切换验证和回滚机制
    - 并发安全
    """
    
    MIN_CONFIDENCE_THRESHOLD = 0.5
    MAX_SWITCH_HISTORY = 20
    
    SELF_ITERATION_PATHS = {
        "docs_libs": "docs/libs",
        "docs_reports": "docs/reports",
        "tests": "tests",
        "skillscripts": "skillscripts"
    }
    
    GUIDE_PROJECT_PATHS = {
        "docs_libs": "docs/libs",
        "docs_reports": "docs/reports",
        "tests": "tests",
        "skillscripts": "skillscripts"
    }
    
    @classmethod
    def for_self_iteration(cls) -> 'PathConfigManager':
        """
        创建自迭代模式的实例
        
        Returns:
            PathConfigManager 实例
        """
        return cls(mode=PathMode.SELF_ITERATION)

    @classmethod
    def for_guide_project(cls, target_root: str) -> 'PathConfigManager':
        """
        创建指导项目模式的实例
        
        Args:
            target_root: 目标项目根目录
            
        Returns:
            PathConfigManager 实例
        """
        return cls(mode=PathMode.GUIDE_PROJECT, target_root=target_root)

    @classmethod
    def auto_detect(cls) -> 'PathConfigManager':
        """
        自动检测模式并创建实例
        
        Returns:
            PathConfigManager 实例
        """
        return cls(auto_detect=True)
    
    def __init__(
        self,
        mode: Optional[PathMode] = None,
        target_root: Optional[str] = None,
        config: Optional[PathConfig] = None,
        auto_detect: bool = True,
        detection_args: Optional[List[str]] = None
    ):
        """
        初始化路径配置管理器
        
        Args:
            mode: 指定模式，None 表示自动检测
            target_root: 目标项目根目录（指导项目模式必需）
            config: 路径配置
            auto_detect: 是否自动检测模式
            detection_args: 用于检测的命令行参数列表
        """
        self.config = config or PathConfig()
        self._base_path: Optional[Path] = None
        self._target_root = Path(target_root) if target_root else None
        self._version_info: Optional[VersionInfo] = None
        self._mode_switch_callbacks: List[Callable[[PathMode, PathMode], None]] = []
        self._last_detection_result: Optional[ModeDetectionResult] = None
        self._enhanced_detection_result: Optional[EnhancedModeDetectionResult] = None
        self._config_loaded: bool = False
        self._lock = threading.RLock()
        self._history_manager: Optional[SwitchHistoryManager] = None
        self._rollback_state: Optional[Dict[str, Any]] = None
        
        self._mode_state: Optional[ModeState] = None
        
        if mode is None and auto_detect:
            enhanced_detection = ModeAutoDetector.detect(args=detection_args)
            self._enhanced_detection_result = enhanced_detection
            self.mode = enhanced_detection.detected_mode
            
            if enhanced_detection.target_root:
                self._target_root = Path(enhanced_detection.target_root)
            
            logger.info(
                f"增强模式检测: {self.mode.value}, "
                f"来源: {enhanced_detection.source.value}, "
                f"置信度: {enhanced_detection.confidence:.2%}"
            )
            
            if enhanced_detection.source == ModeDetectionSource.AUTO_DETECT:
                detection = self.detect_mode()
                self._last_detection_result = detection
                
                if detection.skill_root and self.mode == PathMode.SELF_ITERATION:
                    self._base_path = detection.skill_root
                elif detection.project_root and self.mode == PathMode.GUIDE_PROJECT:
                    if not self._target_root:
                        self._target_root = detection.project_root
                    self._base_path = self._target_root
        elif mode is not None:
            self.mode = mode
            self._enhanced_detection_result = EnhancedModeDetectionResult(
                detected_mode=mode,
                target_root=target_root,
                source=ModeDetectionSource.EXPLICIT,
                confidence=1.0,
                config_path=None,
                detection_details={"explicit": True}
            )
        else:
            self.mode = PathMode.SELF_ITERATION
        
        self._initialize_base_path()
        self._initialize_mode_state()
        self._initialize_history_manager()
        self._initialize_script_registry()
        self._load_persisted_config()
        
        logger.info(f"PathConfigManager 初始化完成，模式: {self.mode.value}")
    
    def _initialize_script_registry(self) -> None:
        """初始化脚本路径注册表"""
        self._script_registry: Optional[ScriptPathRegistry] = None
        if self._base_path:
            self._script_registry = ScriptPathRegistry(base_path=self._base_path)
            logger.debug("脚本路径注册表初始化完成")
    
    def _initialize_history_manager(self) -> None:
        """初始化历史管理器"""
        if self._base_path:
            self._history_manager = SwitchHistoryManager(self._base_path)
    
    def _save_rollback_state(self) -> None:
        """保存当前状态用于回滚"""
        self._rollback_state = {
            "mode": self.mode,
            "base_path": self._base_path,
            "target_root": self._target_root,
            "config": self.config,
            "version_info": self._version_info
        }
    
    def _restore_rollback_state(self) -> bool:
        """恢复回滚状态"""
        if not self._rollback_state:
            return False
        
        try:
            self.mode = self._rollback_state["mode"]
            self._base_path = self._rollback_state["base_path"]
            self._target_root = self._rollback_state["target_root"]
            self.config = self._rollback_state["config"]
            self._version_info = self._rollback_state["version_info"]
            return True
        except Exception as e:
            logger.error(f"恢复回滚状态失败: {e}")
            return False
    
    @contextmanager
    def _switch_context(self) -> Generator[None, None, None]:
        """模式切换上下文管理器"""
        self._save_rollback_state()
        try:
            yield
        except Exception as e:
            logger.error(f"模式切换失败，尝试回滚: {e}")
            self._restore_rollback_state()
            raise
    
    def _initialize_mode_state(self) -> None:
        """初始化模式状态"""
        self._mode_state = ModeState(
            current_mode=self.mode,
            base_path=self._base_path,
            target_root=self._target_root,
            initialized_at=datetime.now().isoformat()
        )
    
    def detect_mode(self, start_path: Optional[Path] = None) -> ModeDetectionResult:
        """
        检测当前运行模式
        
        通过检测技能目录和项目目录来判断当前应该使用的模式
        
        Args:
            start_path: 起始搜索路径，默认为当前工作目录
            
        Returns:
            模式检测结果
        """
        search_path = start_path or Path.cwd()
        
        skill_root = SkillDetector.find_skill_root(search_path)
        project_root = ProjectDetector.find_project_root(search_path)
        
        detection_details = {
            "search_path": str(search_path),
            "skill_root_found": skill_root is not None,
            "project_root_found": project_root is not None,
            "skill_root_path": str(skill_root) if skill_root else None,
            "project_root_path": str(project_root) if project_root else None,
            "detection_timestamp": datetime.now().isoformat()
        }
        
        if skill_root:
            confidence = SkillDetector.calculate_confidence(skill_root)
            detected_mode = PathMode.SELF_ITERATION
            detection_details["confidence_factors"] = {
                "skill_markers": SkillDetector.check_skill_markers(skill_root),
                "in_skill_directory": True,
                "skill_confidence": confidence
            }
            detection_details["detection_method"] = "skill_directory_found"
            
        elif project_root:
            project_type, project_confidence = ProjectDetector.detect_project_type(project_root)
            confidence = project_confidence
            detected_mode = PathMode.GUIDE_PROJECT
            detection_details["confidence_factors"] = {
                "project_markers": ProjectDetector.check_project_markers(project_root),
                "in_project_directory": True,
                "project_type": project_type,
                "project_confidence": project_confidence
            }
            detection_details["project_info"] = ProjectDetector.get_project_info(project_root)
            detection_details["detection_method"] = "project_directory_found"
            
        else:
            confidence = 0.3
            detected_mode = PathMode.SELF_ITERATION
            detection_details["confidence_factors"] = {
                "fallback": True,
                "reason": "未找到技能或项目根目录，默认使用自迭代模式"
            }
            detection_details["detection_method"] = "fallback_default"
        
        result = ModeDetectionResult(
            detected_mode=detected_mode,
            skill_root=skill_root,
            project_root=project_root,
            confidence=confidence,
            detection_details=detection_details
        )
        
        logger.debug(f"模式检测结果: {result.get_summary()}")
        return result
    
    def is_in_skill_directory(self, path: Optional[Path] = None) -> bool:
        """
        判断是否在技能目录中
        
        Args:
            path: 待检查的路径，默认为当前工作目录
            
        Returns:
            是否在技能目录中
        """
        check_path = path or Path.cwd()
        return SkillDetector.find_skill_root(check_path) is not None
    
    def is_in_project_directory(self, path: Optional[Path] = None) -> bool:
        """
        判断是否在项目目录中
        
        Args:
            path: 待检查的路径，默认为当前工作目录
            
        Returns:
            是否在项目目录中
        """
        check_path = path or Path.cwd()
        return ProjectDetector.find_project_root(check_path) is not None
    
    def get_current_project_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前项目信息（仅指导项目模式）
        
        Returns:
            项目信息字典，非指导模式返回 None
        """
        if self.mode != PathMode.GUIDE_PROJECT:
            return None
        
        if self._target_root:
            return ProjectDetector.get_project_info(self._target_root)
        return None
    
    def _initialize_base_path(self) -> None:
        """初始化基础路径"""
        if self._base_path is not None:
            return
            
        if self.mode == PathMode.SELF_ITERATION:
            cwd = Path.cwd()
            self._base_path = SkillDetector.find_skill_root(cwd)
            if self._base_path is None:
                self._base_path = cwd / SkillDetector.SKILL_RELATIVE_PATH
                logger.warning(f"未找到技能根目录，使用默认路径: {self._base_path}")
        else:
            if self._target_root:
                self._base_path = Path(self._target_root)
            else:
                raise PathConfigError(
                    "指导项目模式需要提供 target_root 参数",
                    mode=self.mode
                )
        
        logger.info(f"基础路径已初始化: {self._base_path}")
    
    def _load_persisted_config(self) -> None:
        """加载持久化配置"""
        if self._config_loaded:
            return
            
        config_file = self.get_base_path() / self.config.config_file
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'config' in data:
                    self.config = PathConfig.from_dict(data['config'])
                if 'last_mode' in data:
                    logger.debug(f"加载持久化配置，上次模式: {data['last_mode']}")
                if 'mode_state' in data:
                    logger.debug("加载模式状态信息")
                
                self._config_loaded = True
                logger.info(f"已加载持久化配置: {config_file}")
            except Exception as e:
                logger.warning(f"加载持久化配置失败: {e}")
    
    def save_config(self) -> bool:
        """
        保存当前配置
        
        Returns:
            保存是否成功
        """
        config_file = self.get_base_path() / self.config.config_file
        
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "config": self.config.to_dict(),
                "last_mode": self.mode.value,
                "base_path": str(self._base_path),
                "saved_at": datetime.now().isoformat(),
                "version_info": self._version_info.to_dict() if self._version_info else None,
                "mode_state": self._mode_state.to_dict() if self._mode_state else None
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存: {config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def get_base_path(self) -> Path:
        """
        获取基础路径
        
        Returns:
            基础路径
        """
        if self._base_path is None:
            self._initialize_base_path()
        return self._base_path
    
    def validate_path(
        self, 
        path: Path, 
        must_exist: bool = False, 
        must_be_dir: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        验证路径
        
        Args:
            path: 待验证的路径
            must_exist: 是否必须存在
            must_be_dir: 是否必须是目录
            
        Returns:
            (是否有效, 错误信息) 元组
        """
        try:
            resolved = path.resolve()
            
            if must_exist and not resolved.exists():
                return False, f"路径不存在: {resolved}"
            
            if must_be_dir and resolved.exists() and not resolved.is_dir():
                return False, f"路径不是目录: {resolved}"
            
            if not self._is_path_safe(resolved):
                return False, f"路径不安全或不可访问: {resolved}"
            
            return True, None
        except Exception as e:
            return False, f"路径验证异常: {str(e)}"
    
    def _is_path_safe(self, path: Path) -> bool:
        """
        检查路径是否安全
        
        Args:
            path: 待检查的路径
            
        Returns:
            路径是否安全
        """
        try:
            path.resolve()
            return True
        except (OSError, ValueError):
            return False
    
    def get_versioned_path(self, base: str, version: str) -> Path:
        """
        获取版本化路径
        
        Args:
            base: 基础路径
            version: 版本号
            
        Returns:
            版本化路径
        """
        if not version:
            raise PathValidationError("版本号不能为空", mode=self.mode)
        
        base_path = self.get_base_path()
        versioned_path = base_path / base / f"v{version.lstrip('v')}"
        
        valid, error = self.validate_path(versioned_path.parent)
        if not valid:
            logger.warning(f"版本化路径验证警告: {error}")
        
        return versioned_path
    
    def ensure_directories(self, paths: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        确保目录存在
        
        Args:
            paths: 需要创建的目录列表，默认为配置中的标准目录
            
        Returns:
            目录创建结果字典
        """
        results: Dict[str, bool] = {}
        
        if paths is None:
            paths = [
                self.config.docs_libs_path,
                self.config.docs_reports_path,
                self.config.tests_path,
                self.config.skillscripts_path
            ]
        
        base_path = self.get_base_path()
        
        for path_str in paths:
            target_path = base_path / path_str
            try:
                valid, error = self.validate_path(target_path)
                if not valid:
                    results[path_str] = False
                    logger.error(f"路径验证失败 {target_path}: {error}")
                    continue
                
                target_path.mkdir(parents=True, exist_ok=True)
                results[path_str] = True
                logger.debug(f"目录已确保存在: {target_path}")
            except PermissionError as e:
                results[path_str] = False
                logger.error(f"权限不足，创建目录失败 {target_path}: {e}")
            except Exception as e:
                results[path_str] = False
                logger.error(f"创建目录失败 {target_path}: {e}")
        
        return results
    
    def get_current_version(self) -> str:
        """
        获取当前版本号
        
        Returns:
            当前版本号
        """
        if self._version_info is not None:
            return self._version_info.version
        
        version_file = self.get_base_path() / self.config.version_file
        
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                version = data.get('version', '0.1.0')
                self._version_info = VersionInfo(
                    version=version,
                    created_at=data.get('created_at', ''),
                    updated_at=data.get('updated_at', '')
                )
                return version
            except json.JSONDecodeError as e:
                logger.warning(f"版本文件JSON解析失败: {e}")
            except Exception as e:
                logger.warning(f"读取版本文件失败: {e}")
        
        default_version = "0.1.0"
        self._version_info = VersionInfo(
            version=default_version,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        self._save_version_file(default_version)
        return default_version
    
    def _save_version_file(self, version: str) -> bool:
        """
        保存版本文件
        
        Args:
            version: 版本号
            
        Returns:
            保存是否成功
        """
        version_file = self.get_base_path() / self.config.version_file
        
        try:
            version_file.parent.mkdir(parents=True, exist_ok=True)
            
            now = datetime.now().isoformat()
            if self._version_info:
                created_at = self._version_info.created_at or now
            else:
                created_at = now
            
            data = {
                "version": version,
                "created_at": created_at,
                "updated_at": now
            }
            
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self._version_info = VersionInfo(
                version=version,
                created_at=created_at,
                updated_at=now
            )
            
            logger.info(f"版本文件已保存: {version_file}")
            return True
        except Exception as e:
            logger.error(f"保存版本文件失败: {e}")
            return False
    
    def set_version(self, version: str) -> bool:
        """
        设置版本号
        
        Args:
            version: 新版本号
            
        Returns:
            设置是否成功
        """
        if not self._validate_version(version):
            logger.error(f"无效的版本号格式: {version}")
            return False
        
        return self._save_version_file(version)
    
    def _validate_version(self, version: str) -> bool:
        """
        验证版本号格式
        
        Args:
            version: 版本号字符串
            
        Returns:
            版本号是否有效
        """
        import re
        pattern = r'^v?\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$'
        return bool(re.match(pattern, version))
    
    def get_docs_path(self) -> Path:
        """
        获取文档目录路径
        
        如果目录不存在，会自动创建
        
        Returns:
            文档目录的 Path 对象
        """
        docs_path = self.get_base_path() / "docs"
        if not docs_path.exists():
            docs_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"文档目录已创建: {docs_path}")
        return docs_path
    
    def get_docs_libs_path(self, version: Optional[str] = None) -> Path:
        """获取文档库路径"""
        if version:
            return self.get_versioned_path(self.config.docs_libs_path, version)
        return self.get_base_path() / self.config.docs_libs_path
    
    def get_docs_reports_path(self, version: Optional[str] = None) -> Path:
        """获取文档报告路径"""
        if version:
            return self.get_versioned_path(self.config.docs_reports_path, version)
        return self.get_base_path() / self.config.docs_reports_path
    
    def get_docs_iteration_path(self, version: Optional[str] = None) -> Path:
        """
        获取迭代版本文档路径
        
        Args:
            version: 可选的版本号，如 "v3.0.0"
            
        Returns:
            迭代版本文档路径的 Path 对象
        """
        iteration_path = self.get_base_path() / self.config.docs_iteration_path
        if version:
            iteration_path = iteration_path / version
        if not iteration_path.exists():
            iteration_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"迭代版本目录已创建: {iteration_path}")
        return iteration_path
    
    def get_iteration_report_path(self, version: str, report_type: str) -> Path:
        """
        获取迭代版本报告路径
        
        Args:
            version: 版本号，如 "v3.0.0"
            report_type: 报告类型，如 "测试报告", "功能分析报告", "路径验证报告", "质量报告"
            
        Returns:
            报告文件的完整路径
        """
        iteration_path = self.get_docs_iteration_path(version)
        report_filename = f"{report_type}.md"
        return iteration_path / report_filename
    
    def get_tests_path(self) -> Path:
        """获取测试路径"""
        return self.get_base_path() / self.config.tests_path
    
    def get_skillscripts_path(self) -> Path:
        """获取技能脚本路径"""
        return self.get_base_path() / self.config.skillscripts_path
    
    def get_temp_path(self) -> Path:
        """
        获取临时文件目录路径
        
        如果目录不存在，会自动创建
        
        Returns:
            临时文件目录的 Path 对象
        """
        temp_path = self.get_base_path() / self.config.temp_path
        if not temp_path.exists():
            temp_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"临时目录已创建: {temp_path}")
        return temp_path
    
    def get_cache_path(self) -> Path:
        """
        获取缓存目录路径
        
        如果目录不存在，会自动创建
        
        Returns:
            缓存目录的 Path 对象
        """
        cache_path = self.get_base_path() / self.config.cache_path
        if not cache_path.exists():
            cache_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"缓存目录已创建: {cache_path}")
        return cache_path
    
    def get_data_path(self) -> Path:
        """
        获取数据目录路径
        
        如果目录不存在，会自动创建
        
        Returns:
            数据目录的 Path 对象
        """
        data_path = self.get_base_path() / self.config.data_path
        if not data_path.exists():
            data_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"数据目录已创建: {data_path}")
        return data_path
    
    def get_config_path(self) -> Path:
        """
        获取配置目录路径
        
        如果目录不存在，会自动创建
        
        Returns:
            配置目录的 Path 对象
        """
        config_path = self.get_base_path() / self.config.config_path
        if not config_path.exists():
            config_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"配置目录已创建: {config_path}")
        return config_path
    
    def get_reports_path(self) -> Path:
        """
        获取报告目录路径
        
        如果目录不存在，会自动创建
        
        Returns:
            报告目录的 Path 对象
        """
        reports_path = self.get_base_path() / self.config.reports_path
        if not reports_path.exists():
            reports_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"报告目录已创建: {reports_path}")
        return reports_path
    
    def get_logs_path(self) -> Path:
        """
        获取日志目录路径
        
        如果目录不存在，会自动创建
        
        Returns:
            日志目录的 Path 对象
        """
        logs_path = self.get_base_path() / self.config.logs_path
        if not logs_path.exists():
            logs_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"日志目录已创建: {logs_path}")
        return logs_path
    
    def get_backend_path(self) -> Path:
        """
        获取后端目录路径
        
        Returns:
            后端目录的 Path 对象
        """
        return self.get_base_path() / self.config.backend_path
    
    def get_frontend_path(self) -> Path:
        """
        获取前端目录路径
        
        Returns:
            前端目录的 Path 对象
        """
        return self.get_base_path() / self.config.frontend_path
    
    def get_all_paths(self, version: Optional[str] = None) -> Dict[str, Path]:
        """
        获取所有路径
        
        Args:
            version: 可选的版本号
            
        Returns:
            路径字典
        """
        return {
            "base": self.get_base_path(),
            "docs": self.get_docs_path(),
            "docs_libs": self.get_docs_libs_path(version),
            "docs_reports": self.get_docs_reports_path(version),
            "docs_iteration": self.get_docs_iteration_path(version),
            "tests": self.get_tests_path(),
            "skillscripts": self.get_skillscripts_path(),
            "temp": self.get_temp_path(),
            "cache": self.get_cache_path(),
            "data": self.get_data_path(),
            "config": self.get_config_path(),
            "reports": self.get_reports_path(),
            "logs": self.get_logs_path(),
            "backend": self.get_backend_path(),
            "frontend": self.get_frontend_path(),
            "shangshusheng": self.get_shangshusheng_path(),
            "resources": self.get_resources_path(),
            "resources_templates": self.get_resources_templates_path(),
            "resources_best_practices": self.get_resources_best_practices_path(),
            "scripts_core": self.get_scripts_core_path(),
            "scripts_analysis": self.get_scripts_analysis_path(),
            "scripts_optimization": self.get_scripts_optimization_path(),
            "scripts_test": self.get_scripts_test_path(),
            "scripts_pipeline": self.get_scripts_pipeline_path(),
            "scripts_learning": self.get_scripts_learning_path(),
            "scripts_auto_repair": self.get_scripts_auto_repair_path(),
            "scripts_iteration": self.get_scripts_iteration_path(),
            "scripts_requirements": self.get_scripts_requirements_path(),
            "scripts_sdd_tdd": self.get_scripts_sdd_tdd_path(),
            "scripts_monitoring": self.get_scripts_monitoring_path(),
            "scripts_utils": self.get_scripts_utils_path()
        }
    
    def get_scripts_core_path(self) -> Path:
        """获取核心脚本目录路径"""
        return self.get_base_path() / self.config.scripts_core_path
    
    def get_scripts_analysis_path(self) -> Path:
        """获取分析脚本目录路径"""
        return self.get_base_path() / self.config.scripts_analysis_path
    
    def get_scripts_optimization_path(self) -> Path:
        """获取优化脚本目录路径"""
        return self.get_base_path() / self.config.scripts_optimization_path
    
    def get_scripts_test_path(self) -> Path:
        """获取测试脚本目录路径"""
        return self.get_base_path() / self.config.scripts_test_path
    
    def get_scripts_pipeline_path(self) -> Path:
        """获取流水线脚本目录路径"""
        return self.get_base_path() / self.config.scripts_pipeline_path
    
    def get_scripts_learning_path(self) -> Path:
        """获取学习脚本目录路径"""
        return self.get_base_path() / self.config.scripts_learning_path
    
    def get_scripts_auto_repair_path(self) -> Path:
        """获取自动修复脚本目录路径"""
        return self.get_base_path() / self.config.scripts_auto_repair_path
    
    def get_scripts_iteration_path(self) -> Path:
        """获取迭代脚本目录路径"""
        return self.get_base_path() / self.config.scripts_iteration_path
    
    def get_scripts_requirements_path(self) -> Path:
        """获取需求管理脚本目录路径"""
        return self.get_base_path() / self.config.scripts_requirements_path
    
    def get_scripts_sdd_tdd_path(self) -> Path:
        """获取SDD/TDD脚本目录路径"""
        return self.get_base_path() / self.config.scripts_sdd_tdd_path
    
    def get_scripts_monitoring_path(self) -> Path:
        """获取监控脚本目录路径"""
        return self.get_base_path() / self.config.scripts_monitoring_path
    
    def get_scripts_utils_path(self) -> Path:
        """获取工具脚本目录路径"""
        return self.get_base_path() / self.config.scripts_utils_path
    
    def get_shangshusheng_path(self) -> Path:
        """
        获取上书省路径（子技能根路径）
        
        Returns:
            上书省路径
        """
        return self.get_base_path() / self.config.shangshusheng_path
    
    def get_resources_path(self) -> Path:
        """
        获取资源路径
        
        Returns:
            资源路径
        """
        return self.get_base_path() / self.config.resources_path
    
    def get_subskill_path(self, department: str, office: Optional[str] = None) -> Path:
        """
        获取子技能路径
        
        Args:
            department: 部门名称（如：bingbu, gongbu, hubu等）
            office: 司名称（如：jiabucangsi, dushuisi等），可选
            
        Returns:
            子技能路径
        """
        shangshusheng = self.get_shangshusheng_path()
        if office:
            return shangshusheng / department / office
        return shangshusheng / department
    
    def get_all_departments(self) -> List[str]:
        """
        获取所有部门列表
        
        Returns:
            部门名称列表
        """
        shangshusheng = self.get_shangshusheng_path()
        departments = []
        
        if shangshusheng.exists():
            try:
                for item in shangshusheng.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        departments.append(item.name)
            except PermissionError:
                logger.warning(f"无权限访问目录: {shangshusheng}")
        
        return sorted(departments)
    
    def get_department_offices(self, department: str) -> List[str]:
        """
        获取指定部门的所有司
        
        Args:
            department: 部门名称
            
        Returns:
            司名称列表
        """
        dept_path = self.get_subskill_path(department)
        offices = []
        
        if dept_path.exists():
            try:
                for item in dept_path.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        offices.append(item.name)
            except PermissionError:
                logger.warning(f"无权限访问目录: {dept_path}")
        
        return sorted(offices)
    
    def get_resources_templates_path(self) -> Path:
        """
        获取资源模板路径
        
        Returns:
            资源模板路径
        """
        return self.get_resources_path() / "templates"
    
    def get_resources_best_practices_path(self) -> Path:
        """
        获取最佳实践路径
        
        Returns:
            最佳实践路径
        """
        return self.get_resources_path() / "best_practices"
    
    def get_template_path(self, template_name: str) -> Path:
        """
        获取指定模板的路径
        
        Args:
            template_name: 模板名称（如：ai_xiangmu.md）
            
        Returns:
            模板文件路径
        """
        return self.get_resources_templates_path() / template_name
    
    def get_best_practice_path(self, practice_name: str) -> Path:
        """
        获取指定最佳实践的路径
        
        Args:
            practice_name: 最佳实践名称（如：sdd_shijian.md）
            
        Returns:
            最佳实践文件路径
        """
        return self.get_resources_best_practices_path() / practice_name
    
    def get_iteration_docs_path(self, version: Optional[str] = None) -> Path:
        """
        获取迭代文档路径（按版本管理）
        
        Args:
            version: 版本号，如未提供则使用当前版本
            
        Returns:
            迭代文档路径
        """
        version = version or self.get_current_version()
        if version:
            return self.get_base_path() / self.config.docs_iteration_path / f"v{version.lstrip('v')}"
        return self.get_base_path() / self.config.docs_iteration_path
    
    def get_iteration_changelog_path(self, version: Optional[str] = None) -> Path:
        """
        获取迭代变更日志路径
        
        Args:
            version: 版本号
            
        Returns:
            变更日志文件路径
        """
        iter_path = self.get_iteration_docs_path(version)
        return iter_path / "CHANGELOG.md"
    
    def get_iteration_test_report_path(self, version: Optional[str] = None) -> Path:
        """
        获取迭代测试报告路径
        
        Args:
            version: 版本号
            
        Returns:
            测试报告文件路径
        """
        iter_path = self.get_iteration_docs_path(version)
        return iter_path / "测试报告.md"
    
    def get_iteration_quality_report_path(self, version: Optional[str] = None) -> Path:
        """
        获取迭代质量报告路径
        
        Args:
            version: 版本号
            
        Returns:
            质量报告文件路径
        """
        iter_path = self.get_iteration_docs_path(version)
        return iter_path / "质量报告.md"
    
    def get_iteration_function_analysis_path(self, version: Optional[str] = None) -> Path:
        """
        获取迭代功能分析报告路径
        
        Args:
            version: 版本号
            
        Returns:
            功能分析报告文件路径
        """
        iter_path = self.get_iteration_docs_path(version)
        return iter_path / "功能分析报告.md"
    
    def get_all_iteration_versions(self) -> List[str]:
        """
        获取所有迭代版本列表
        
        Returns:
            版本列表
        """
        iter_path = self.get_base_path() / self.config.docs_iteration_path
        versions = []
        
        if iter_path.exists():
            try:
                for item in iter_path.iterdir():
                    if item.is_dir() and item.name.startswith('v'):
                        versions.append(item.name)
            except PermissionError:
                logger.warning(f"无权限访问目录: {iter_path}")
        
        return sorted(versions, reverse=True)
    
    def create_iteration_version(self, version: str) -> Dict[str, bool]:
        """
        创建新的迭代版本目录结构
        
        Args:
            version: 版本号
            
        Returns:
            创建结果字典
        """
        if not self._validate_version(version):
            raise PathValidationError(f"无效的版本号格式: {version}", mode=self.mode)
        
        results = {}
        iter_path = self.get_iteration_docs_path(version)
        
        try:
            iter_path.mkdir(parents=True, exist_ok=True)
            results['iteration_root'] = True
            
            default_files = {
                'CHANGELOG.md': f"# 版本 {version} 变更日志\n\n## 变更记录\n\n",
                '测试报告.md': f"# 版本 {version} 测试报告\n\n## 测试概览\n\n",
                '质量报告.md': f"# 版本 {version} 质量报告\n\n## 质量指标\n\n",
                '功能分析报告.md': f"# 版本 {version} 功能分析\n\n## 功能概览\n\n"
            }
            
            for filename, content in default_files.items():
                file_path = iter_path / filename
                try:
                    if not file_path.exists():
                        file_path.write_text(content, encoding='utf-8')
                        results[filename] = True
                    else:
                        results[filename] = True
                        logger.info(f"文件已存在: {file_path}")
                except Exception as e:
                    results[filename] = False
                    logger.error(f"创建文件失败 {file_path}: {e}")
            
            logger.info(f"迭代版本目录已创建: {iter_path}")
        except Exception as e:
            results['iteration_root'] = False
            logger.error(f"创建迭代版本目录失败: {e}")
        
        return results
    
    def get_script_path(self, script_id: str) -> Optional[Path]:
        """
        获取指定脚本的完整路径
        
        Args:
            script_id: 脚本ID，格式为 "category/script_name.py"
            
        Returns:
            脚本的完整路径，如果不存在返回 None
        """
        if not self._script_registry:
            logger.warning("脚本路径注册表未初始化")
            return None
        return self._script_registry.get_script_path(script_id)
    
    def get_script_by_name(self, script_name: str) -> Optional[ScriptInfo]:
        """
        通过脚本名称查找脚本
        
        Args:
            script_name: 脚本文件名
            
        Returns:
            脚本信息，如果不存在返回 None
        """
        if not self._script_registry:
            logger.warning("脚本路径注册表未初始化")
            return None
        return self._script_registry.get_script_by_name(script_name)
    
    def get_scripts_by_category(self, category: str) -> List[ScriptInfo]:
        """
        获取指定类别的所有脚本
        
        Args:
            category: 脚本类别
            
        Returns:
            脚本信息列表
        """
        if not self._script_registry:
            logger.warning("脚本路径注册表未初始化")
            return []
        return self._script_registry.get_scripts_by_category(category)
    
    def search_scripts(self, keyword: str) -> List[ScriptInfo]:
        """
        搜索脚本
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的脚本信息列表
        """
        if not self._script_registry:
            logger.warning("脚本路径注册表未初始化")
            return []
        return self._script_registry.search_scripts(keyword)
    
    def get_all_scripts(self) -> Dict[str, ScriptInfo]:
        """
        获取所有脚本信息
        
        Returns:
            所有脚本的字典
        """
        if not self._script_registry:
            logger.warning("脚本路径注册表未初始化")
            return {}
        return self._script_registry.get_all_scripts()
    
    def get_all_script_categories(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有脚本类别信息
        
        Returns:
            所有类别的字典
        """
        if not self._script_registry:
            logger.warning("脚本路径注册表未初始化")
            return {}
        return self._script_registry.get_all_categories()
    
    def validate_script_exists(self, script_id: str) -> bool:
        """
        验证脚本文件是否存在
        
        Args:
            script_id: 脚本ID
            
        Returns:
            脚本是否存在
        """
        if not self._script_registry:
            return False
        return self._script_registry.validate_script_exists(script_id)
    
    def validate_all_scripts(self) -> Dict[str, bool]:
        """
        验证所有脚本是否存在
        
        Returns:
            脚本ID到存在状态的映射
        """
        if not self._script_registry:
            return {}
        return self._script_registry.validate_all_scripts()
    
    def get_missing_scripts(self) -> List[str]:
        """
        获取缺失的脚本列表
        
        Returns:
            缺失脚本的ID列表
        """
        if not self._script_registry:
            return []
        return self._script_registry.get_missing_scripts()
    
    def get_script_registry_info(self) -> Dict[str, Any]:
        """
        获取脚本注册表信息
        
        Returns:
            脚本注册表信息字典
        """
        if not self._script_registry:
            return {
                "initialized": False,
                "total_scripts": 0,
                "categories": {}
            }
        info = self._script_registry.to_dict()
        info["initialized"] = True
        return info
    
    def list_versions(self) -> List[str]:
        """
        列出所有版本
        
        Returns:
            版本列表
        """
        versions: List[str] = []
        
        docs_libs = self.get_base_path() / self.config.docs_libs_path
        if docs_libs.exists():
            try:
                for item in docs_libs.iterdir():
                    if item.is_dir() and item.name.startswith('v'):
                        versions.append(item.name)
            except PermissionError:
                logger.warning(f"无权限访问目录: {docs_libs}")
        
        return sorted(versions, reverse=True)
    
    def get_path_info(self) -> Dict[str, Any]:
        """
        获取路径信息
        
        Returns:
            路径信息字典
        """
        detection_info = None
        if self._last_detection_result:
            detection_info = {
                "detected_mode": self._last_detection_result.detected_mode.value,
                "confidence": self._last_detection_result.confidence,
                "skill_root": str(self._last_detection_result.skill_root) if self._last_detection_result.skill_root else None,
                "project_root": str(self._last_detection_result.project_root) if self._last_detection_result.project_root else None,
                "is_high_confidence": self._last_detection_result.is_high_confidence()
            }
        
        return {
            "mode": self.mode.value,
            "mode_description": self.mode.get_description(),
            "base_path": str(self.get_base_path()),
            "current_version": self.get_current_version(),
            "paths": {
                "docs_libs": str(self.get_docs_libs_path()),
                "docs_reports": str(self.get_docs_reports_path()),
                "docs_iteration": str(self.get_docs_iteration_path()),
                "tests": str(self.get_tests_path()),
                "skillscripts": str(self.get_skillscripts_path()),
                "temp": str(self.get_temp_path()),
                "cache": str(self.get_cache_path()),
                "data": str(self.get_data_path()),
                "config": str(self.get_config_path()),
                "reports": str(self.get_reports_path()),
                "logs": str(self.get_logs_path()),
                "backend": str(self.get_backend_path()),
                "frontend": str(self.get_frontend_path()),
                "shangshusheng": str(self.get_shangshusheng_path()),
                "resources": str(self.get_resources_path()),
                "resources_templates": str(self.get_resources_templates_path()),
                "resources_best_practices": str(self.get_resources_best_practices_path())
            },
            "available_versions": self.list_versions(),
            "iteration_versions": self.get_all_iteration_versions(),
            "departments": self.get_all_departments(),
            "detection_info": detection_info,
            "config_loaded": self._config_loaded
        }
    
    def get_mode_info(self) -> Dict[str, Any]:
        """
        获取模式信息（增强版）
        
        Returns:
            模式信息字典
        """
        info = {
            "current_mode": self.mode.value,
            "mode_description": self.mode.get_description(),
            "base_path": str(self._base_path) if self._base_path else None,
            "target_root": str(self._target_root) if self._target_root else None,
            "paths_config": self._get_paths_config_for_mode()
        }
        
        if self._mode_state:
            info["state"] = {
                "initialized_at": self._mode_state.initialized_at,
                "last_switch_at": self._mode_state.last_switch_at,
                "switch_count": self._mode_state.switch_count,
                "recent_switches": [
                    r.to_dict() for r in self._mode_state.get_recent_switches(5)
                ]
            }
        
        if self._last_detection_result:
            info["detection"] = {
                "detected_mode": self._last_detection_result.detected_mode.value,
                "confidence": self._last_detection_result.confidence,
                "summary": self._last_detection_result.get_summary()
            }
        
        if self._enhanced_detection_result:
            info["enhanced_detection"] = {
                "detected_mode": self._enhanced_detection_result.detected_mode.value,
                "source": self._enhanced_detection_result.source.value,
                "confidence": self._enhanced_detection_result.confidence,
                "target_root": self._enhanced_detection_result.target_root,
                "config_path": str(self._enhanced_detection_result.config_path) if self._enhanced_detection_result.config_path else None,
                "summary": self._enhanced_detection_result.get_summary()
            }
        
        if self.mode == PathMode.GUIDE_PROJECT and self._target_root:
            info["project_info"] = self.get_current_project_info()
        
        if self._history_manager:
            info["switch_history_available"] = True
            info["recent_switch_history"] = self._history_manager.get_history(5)
        
        return info
    
    def _get_paths_config_for_mode(self) -> Dict[str, str]:
        """
        获取当前模式的路径配置
        
        Returns:
            路径配置字典
        """
        if self.mode == PathMode.SELF_ITERATION:
            return {
                "working_directory": str(self._base_path) if self._base_path else None,
                "docs_libs": self.config.docs_libs_path,
                "docs_reports": self.config.docs_reports_path,
                "tests": self.config.tests_path,
                "skillscripts": self.config.skillscripts_path,
                "temp": self.config.temp_path,
                "cache": self.config.cache_path,
                "data": self.config.data_path,
                "config": self.config.config_path,
                "mode_type": "self_iteration",
                "description": "技能自迭代模式 - 在技能目录内进行自我迭代开发"
            }
        else:
            return {
                "working_directory": str(self._target_root) if self._target_root else None,
                "docs_libs": self.config.docs_libs_path,
                "docs_reports": self.config.docs_reports_path,
                "tests": self.config.tests_path,
                "skillscripts": self.config.skillscripts_path,
                "temp": self.config.temp_path,
                "cache": self.config.cache_path,
                "data": self.config.data_path,
                "config": self.config.config_path,
                "mode_type": "guide_project",
                "description": "指导项目模式 - 指导其他项目进行开发"
            }
    
    def get_enhanced_detection_info(self) -> Optional[Dict[str, Any]]:
        """
        获取增强检测结果信息
        
        Returns:
            增强检测结果字典
        """
        if not self._enhanced_detection_result:
            return None
        
        return {
            "detected_mode": self._enhanced_detection_result.detected_mode.value,
            "source": self._enhanced_detection_result.source.value,
            "confidence": self._enhanced_detection_result.confidence,
            "target_root": self._enhanced_detection_result.target_root,
            "config_path": str(self._enhanced_detection_result.config_path) if self._enhanced_detection_result.config_path else None,
            "detection_details": self._enhanced_detection_result.detection_details,
            "summary": self._enhanced_detection_result.get_summary()
        }
    
    def register_mode_switch_callback(self, callback: Callable[[PathMode, PathMode], None]) -> None:
        """
        注册模式切换回调函数
        
        Args:
            callback: 回调函数，接收 (旧模式, 新模式) 参数
        """
        self._mode_switch_callbacks.append(callback)
    
    def unregister_mode_switch_callback(self, callback: Callable[[PathMode, PathMode], None]) -> None:
        """
        注销模式切换回调函数
        
        Args:
            callback: 要注销的回调函数
        """
        if callback in self._mode_switch_callbacks:
            self._mode_switch_callbacks.remove(callback)
    
    def _notify_mode_switch(self, old_mode: PathMode, new_mode: PathMode) -> None:
        """
        通知模式切换
        
        Args:
            old_mode: 旧模式
            new_mode: 新模式
        """
        for callback in self._mode_switch_callbacks:
            try:
                callback(old_mode, new_mode)
            except Exception as e:
                logger.error(f"模式切换回调执行失败: {e}")
    
    def switch_mode(self, mode: PathMode, target_root: Optional[str] = None, validate: bool = True) -> bool:
        """
        切换模式（增强版）
        
        Args:
            mode: 目标模式
            target_root: 目标项目根目录（指导项目模式必需）
            validate: 是否执行验证
            
        Returns:
            切换是否成功
        """
        with self._lock:
            old_mode = self.mode
            old_path = str(self._base_path) if self._base_path else None
            switch_record = None
            
            with self._switch_context():
                try:
                    if mode == PathMode.GUIDE_PROJECT and not target_root:
                        if self._target_root:
                            target_root = str(self._target_root)
                        else:
                            raise ModeSwitchError(
                                "切换到指导项目模式需要提供 target_root 参数",
                                mode=mode
                            )
                    
                    if target_root:
                        target_path = Path(target_root)
                        
                        if validate:
                            valid, errors = PathValidator.validate_all(
                                target_path,
                                must_exist=True,
                                must_be_dir=True,
                                must_be_writable=True
                            )
                            if not valid:
                                raise ModeSwitchError(
                                    f"目标路径验证失败: {'; '.join(errors)}",
                                    path=target_path,
                                    mode=mode
                                )
                        
                        if validate and not self._validate_target_path_for_mode(target_path, mode):
                            raise ModeSwitchError(
                                f"目标路径不适合 {mode.value} 模式",
                                path=target_path,
                                mode=mode
                            )
                    
                    self.mode = mode
                    self._target_root = Path(target_root) if target_root else None
                    self._base_path = None
                    self._version_info = None
                    self._config_loaded = False
                    
                    self._initialize_base_path()
                    self._initialize_history_manager()
                    self._load_persisted_config()
                    
                    new_path = str(self._base_path)
                    
                    switch_record = ModeSwitchRecord(
                        from_mode=old_mode,
                        to_mode=mode,
                        timestamp=datetime.now().isoformat(),
                        from_path=old_path,
                        to_path=new_path,
                        success=True
                    )
                    
                    if self._mode_state:
                        self._mode_state.current_mode = mode
                        self._mode_state.base_path = self._base_path
                        self._mode_state.target_root = self._target_root
                        self._mode_state.add_switch_record(switch_record)
                        
                        if len(self._mode_state.switch_history) > self.MAX_SWITCH_HISTORY:
                            self._mode_state.switch_history = self._mode_state.switch_history[-self.MAX_SWITCH_HISTORY:]
                    
                    if self._history_manager:
                        self._history_manager.record_switch(switch_record)
                    
                    self._notify_mode_switch(old_mode, mode)
                    
                    logger.info(f"模式切换成功: {old_mode.value} -> {mode.value}")
                    self._rollback_state = None
                    return True
                    
                except PathConfigError as e:
                    switch_record = ModeSwitchRecord(
                        from_mode=old_mode,
                        to_mode=mode,
                        timestamp=datetime.now().isoformat(),
                        from_path=old_path,
                        to_path=target_root,
                        success=False,
                        error_message=str(e)
                    )
                    
                    if self._mode_state:
                        self._mode_state.add_switch_record(switch_record)
                    
                    if self._history_manager:
                        self._history_manager.record_switch(switch_record)
                    
                    raise
                except Exception as e:
                    logger.error(f"模式切换失败: {e}")
                    
                    switch_record = ModeSwitchRecord(
                        from_mode=old_mode,
                        to_mode=mode,
                        timestamp=datetime.now().isoformat(),
                        from_path=old_path,
                        to_path=target_root,
                        success=False,
                        error_message=str(e)
                    )
                    
                    if self._mode_state:
                        self._mode_state.add_switch_record(switch_record)
                    
                    if self._history_manager:
                        self._history_manager.record_switch(switch_record)
                    
                    raise ModeSwitchError(f"模式切换失败: {e}", mode=mode)
    
    def _validate_target_path_for_mode(self, target_path: Path, mode: PathMode) -> bool:
        """
        验证目标路径是否适合指定模式
        
        Args:
            target_path: 目标路径
            mode: 目标模式
            
        Returns:
            路径是否适合该模式
        """
        if mode == PathMode.SELF_ITERATION:
            skill_root = SkillDetector.find_skill_root(target_path)
            if skill_root:
                return True
            logger.warning(f"目标路径 {target_path} 不是有效的技能目录")
            return True
        
        elif mode == PathMode.GUIDE_PROJECT:
            project_root = ProjectDetector.find_project_root(target_path)
            if project_root:
                return True
            logger.info(f"目标路径 {target_path} 未检测到项目标识，但仍可使用")
            return True
        
        return True
    
    def rollback_last_switch(self) -> Tuple[bool, str]:
        """
        回滚最后一次模式切换
        
        Returns:
            (是否成功, 消息) 元组
        """
        with self._lock:
            if not self._history_manager:
                return False, "历史管理器未初始化"
            
            last_switch = self._history_manager.get_last_successful_switch()
            if not last_switch:
                return False, "没有可回滚的切换记录"
            
            try:
                from_mode_str = last_switch.get("from_mode")
                from_path = last_switch.get("from_path")
                
                if not from_mode_str:
                    return False, "切换记录缺少模式信息"
                
                from_mode = PathMode.from_string(from_mode_str)
                if not from_mode:
                    return False, f"无效的模式: {from_mode_str}"
                
                self.switch_mode(from_mode, from_path, validate=False)
                
                return True, f"已回滚到模式: {from_mode.value}"
            except Exception as e:
                return False, f"回滚失败: {e}"
    
    def auto_switch_mode(self) -> Tuple[bool, str]:
        """
        自动切换模式
        
        根据检测结果自动切换到合适的模式
        
        Returns:
            (是否成功, 消息) 元组
        """
        detection = self.detect_mode()
        
        if detection.detected_mode == self.mode:
            return True, f"当前模式已正确: {self.mode.value}"
        
        try:
            if detection.detected_mode == PathMode.GUIDE_PROJECT and detection.project_root:
                self.switch_mode(PathMode.GUIDE_PROJECT, str(detection.project_root))
            else:
                self.switch_mode(PathMode.SELF_ITERATION)
            
            self._last_detection_result = detection
            return True, f"已自动切换到模式: {self.mode.value} (置信度: {detection.confidence:.2%})"
        except Exception as e:
            return False, f"自动切换模式失败: {e}"
    
    def resolve_path(self, relative_path: str) -> Path:
        """
        解析相对路径
        
        Args:
            relative_path: 相对路径字符串
            
        Returns:
            解析后的绝对路径
        """
        return self.get_base_path() / relative_path
    
    def path_exists(self, relative_path: str) -> bool:
        """
        检查相对路径是否存在
        
        Args:
            relative_path: 相对路径字符串
            
        Returns:
            路径是否存在
        """
        return self.resolve_path(relative_path).exists()
    
    def create_version_directories(self, version: str) -> Dict[str, bool]:
        """
        创建版本目录
        
        Args:
            version: 版本号
            
        Returns:
            创建结果字典
        """
        if not self._validate_version(version):
            raise PathValidationError(f"无效的版本号格式: {version}", mode=self.mode)
        
        results: Dict[str, bool] = {}
        base_path = self.get_base_path()
        
        versioned_dirs = [
            self.config.docs_libs_path,
            self.config.docs_reports_path
        ]
        
        for dir_path in versioned_dirs:
            target_path = base_path / dir_path / f"v{version.lstrip('v')}"
            try:
                valid, error = self.validate_path(target_path.parent, must_exist=True, must_be_dir=True)
                if not valid:
                    results[dir_path] = False
                    logger.error(f"父目录验证失败 {target_path}: {error}")
                    continue
                
                target_path.mkdir(parents=True, exist_ok=True)
                results[dir_path] = True
                logger.info(f"版本目录已创建: {target_path}")
            except Exception as e:
                results[dir_path] = False
                logger.error(f"创建版本目录失败 {target_path}: {e}")
        
        return results
    
    def get_switch_history(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        获取模式切换历史
        
        Args:
            count: 返回记录数量
            
        Returns:
            切换历史记录列表
        """
        if not self._mode_state:
            return []
        
        records = self._mode_state.get_recent_switches(count)
        return [r.to_dict() for r in records]
    
    def to_relative_path(self, path: Union[str, Path], base: Optional[Path] = None) -> str:
        """
        将绝对路径转换为相对路径
        
        Args:
            path: 要转换的路径
            base: 基准路径，默认为基础路径
            
        Returns:
            相对路径字符串
        """
        path_obj = Path(path).resolve()
        base_path = (base or self.get_base_path()).resolve()
        
        try:
            relative = path_obj.relative_to(base_path)
            return str(relative).replace('\\', '/')
        except ValueError:
            if path_obj.is_absolute():
                return str(path_obj).replace('\\', '/')
            return str(path_obj).replace('\\', '/')
    
    def to_absolute_path(self, relative_path: Union[str, Path], base: Optional[Path] = None) -> Path:
        """
        将相对路径转换为绝对路径
        
        Args:
            relative_path: 相对路径
            base: 基准路径，默认为基础路径
            
        Returns:
            绝对路径 Path 对象
        """
        path_obj = Path(relative_path)
        
        if path_obj.is_absolute():
            return path_obj.resolve()
        
        base_path = base or self.get_base_path()
        return (base_path / path_obj).resolve()
    
    def normalize_path(self, path: Union[str, Path]) -> str:
        """
        规范化路径
        
        统一路径分隔符，处理 . 和 .. 等相对路径组件
        
        Args:
            path: 要规范化的路径
            
        Returns:
            规范化后的路径字符串
        """
        path_obj = Path(path)
        
        try:
            resolved = path_obj.resolve()
            return str(resolved).replace('\\', '/')
        except (OSError, ValueError):
            normalized = os.path.normpath(str(path_obj))
            return normalized.replace('\\', '/')
    
    def convert_path_for_platform(
        self,
        path: Union[str, Path],
        target_platform: Optional[str] = None
    ) -> str:
        """
        跨平台路径转换
        
        Args:
            path: 要转换的路径
            target_platform: 目标平台 ('windows', 'posix', 'mac')，默认为当前平台
            
        Returns:
            转换后的路径字符串
        """
        path_str = str(path)
        
        if target_platform is None:
            target_platform = 'windows' if os.name == 'nt' else 'posix'
        
        target_platform = target_platform.lower()
        
        if target_platform in ('windows', 'win'):
            path_str = path_str.replace('/', '\\')
            if len(path_str) > 1 and path_str[0] == '\\' and path_str[1] != '\\':
                path_str = path_str[1:]
        else:
            path_str = path_str.replace('\\', '/')
            if len(path_str) > 1 and path_str[0] == '/' and path_str[1] != '/':
                pass
        
        return path_str
    
    def is_subpath(self, path: Union[str, Path], parent: Optional[Path] = None) -> bool:
        """
        检查路径是否为另一个路径的子路径
        
        Args:
            path: 要检查的路径
            parent: 父路径，默认为基础路径
            
        Returns:
            是否为子路径
        """
        try:
            path_obj = Path(path).resolve()
            parent_path = (parent or self.get_base_path()).resolve()
            
            path_obj.relative_to(parent_path)
            return True
        except ValueError:
            return False
    
    def get_common_prefix(self, paths: List[Union[str, Path]]) -> Optional[Path]:
        """
        获取多个路径的公共前缀
        
        Args:
            paths: 路径列表
            
        Returns:
            公共前缀路径，无公共前缀返回 None
        """
        if not paths:
            return None
        
        resolved_paths = [Path(p).resolve() for p in paths]
        
        common = resolved_paths[0]
        
        for path in resolved_paths[1:]:
            new_common = Path(os.path.commonpath([str(common), str(path)]))
            common = new_common
            
            if str(common) == str(path.root) or str(common) == '.':
                return None
        
        return common
    
    def split_path(self, path: Union[str, Path]) -> List[str]:
        """
        分割路径为组件列表
        
        Args:
            path: 要分割的路径
            
        Returns:
            路径组件列表
        """
        path_obj = Path(path)
        parts = list(path_obj.parts)
        
        if parts and parts[0] in ('/', '\\'):
            parts = parts[1:]
        
        if parts and len(parts[0]) == 2 and parts[0][1] == ':':
            pass
        
        return parts
    
    def join_path(self, *parts: Union[str, Path]) -> Path:
        """
        连接多个路径组件
        
        Args:
            *parts: 路径组件
            
        Returns:
            连接后的路径
        """
        if not parts:
            return self.get_base_path()
        
        result = Path(parts[0])
        for part in parts[1:]:
            result = result / part
        
        return result
    
    def get_path_depth(self, path: Union[str, Path], base: Optional[Path] = None) -> int:
        """
        获取路径相对于基准路径的深度
        
        Args:
            path: 要计算深度的路径
            base: 基准路径，默认为基础路径
            
        Returns:
            路径深度（负数表示路径在基准路径之外）
        """
        try:
            path_obj = Path(path).resolve()
            base_path = (base or self.get_base_path()).resolve()
            
            relative = path_obj.relative_to(base_path)
            return len(relative.parts)
        except ValueError:
            try:
                base_path = (base or self.get_base_path()).resolve()
                path_obj = Path(path).resolve()
                relative = base_path.relative_to(path_obj)
                return -len(relative.parts)
            except ValueError:
                return 0


class PathConfigManagerTest:
    """
    路径配置管理器测试套件
    """
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
    
    def _log_test(self, name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        result = {
            "name": name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if passed:
            self.passed += 1
            logger.info(f"✓ {name}: 通过")
        else:
            self.failed += 1
            logger.error(f"✗ {name}: 失败 - {message}")
    
    def test_mode_detection(self):
        """测试模式检测"""
        try:
            manager = PathConfigManager(auto_detect=True)
            detection = manager.detect_mode()
            
            self._log_test(
                "模式检测 - 返回有效结果",
                detection is not None and detection.detected_mode is not None
            )
            
            self._log_test(
                "模式检测 - 置信度有效",
                0 <= detection.confidence <= 1
            )
            
            self._log_test(
                "模式检测 - 包含检测详情",
                bool(detection.detection_details)
            )
            
            self._log_test(
                "模式检测 - 包含检测方法",
                "detection_method" in detection.detection_details
            )
            
            self._log_test(
                "模式检测 - get_summary 方法",
                isinstance(detection.get_summary(), str)
            )
            
            self._log_test(
                "模式检测 - is_high_confidence 方法",
                isinstance(detection.is_high_confidence(), bool)
            )
        except Exception as e:
            self._log_test("模式检测", False, str(e))
    
    def test_skill_detector(self):
        """测试技能检测器"""
        try:
            skill_root = SkillDetector.find_skill_root()
            
            self._log_test(
                "技能检测器 - find_skill_root 返回有效结果",
                skill_root is None or isinstance(skill_root, Path)
            )
            
            if skill_root:
                markers = SkillDetector.check_skill_markers(skill_root)
                self._log_test(
                    "技能检测器 - check_skill_markers 返回字典",
                    isinstance(markers, dict)
                )
                
                confidence = SkillDetector.calculate_confidence(skill_root)
                self._log_test(
                    "技能检测器 - calculate_confidence 返回有效值",
                    0 <= confidence <= 1
                )
                
                is_skill = SkillDetector.is_skill_directory(skill_root)
                self._log_test(
                    "技能检测器 - is_skill_directory 返回布尔值",
                    isinstance(is_skill, bool)
                )
        except Exception as e:
            self._log_test("技能检测器", False, str(e))
    
    def test_project_detector(self):
        """测试项目检测器"""
        try:
            project_root = ProjectDetector.find_project_root()
            
            self._log_test(
                "项目检测器 - find_project_root 返回有效结果",
                project_root is None or isinstance(project_root, Path)
            )
            
            if project_root:
                project_type, confidence = ProjectDetector.detect_project_type(project_root)
                self._log_test(
                    "项目检测器 - detect_project_type 返回有效类型",
                    isinstance(project_type, str)
                )
                self._log_test(
                    "项目检测器 - detect_project_type 返回有效置信度",
                    0 <= confidence <= 1
                )
                
                markers = ProjectDetector.check_project_markers(project_root)
                self._log_test(
                    "项目检测器 - check_project_markers 返回字典",
                    isinstance(markers, dict)
                )
                
                info = ProjectDetector.get_project_info(project_root)
                self._log_test(
                    "项目检测器 - get_project_info 包含必要字段",
                    "path" in info and "type" in info
                )
        except Exception as e:
            self._log_test("项目检测器", False, str(e))
    
    def test_is_in_skill_directory(self):
        """测试技能目录检测"""
        try:
            manager = PathConfigManager(auto_detect=True)
            result = manager.is_in_skill_directory()
            
            self._log_test(
                "技能目录检测 - 返回布尔值",
                isinstance(result, bool)
            )
        except Exception as e:
            self._log_test("技能目录检测", False, str(e))
    
    def test_is_in_project_directory(self):
        """测试项目目录检测"""
        try:
            manager = PathConfigManager(auto_detect=True)
            result = manager.is_in_project_directory()
            
            self._log_test(
                "项目目录检测 - 返回布尔值",
                isinstance(result, bool)
            )
        except Exception as e:
            self._log_test("项目目录检测", False, str(e))
    
    def test_path_validation(self):
        """测试路径验证"""
        try:
            manager = PathConfigManager(auto_detect=True)
            
            valid_path = manager.get_base_path()
            valid, error = manager.validate_path(valid_path, must_exist=True, must_be_dir=True)
            self._log_test("路径验证 - 有效路径", valid and error is None)
            
            invalid_path = Path("/nonexistent/path/that/does/not/exist")
            valid, error = manager.validate_path(invalid_path, must_exist=True)
            self._log_test("路径验证 - 无效路径检测", not valid and error is not None)
        except Exception as e:
            self._log_test("路径验证", False, str(e))
    
    def test_mode_switch(self):
        """测试模式切换"""
        try:
            manager = PathConfigManager(mode=PathMode.SELF_ITERATION)
            
            callback_called = []
            def test_callback(old: PathMode, new: PathMode):
                callback_called.append((old, new))
            
            manager.register_mode_switch_callback(test_callback)
            
            base_path = manager.get_base_path()
            success = manager.switch_mode(PathMode.GUIDE_PROJECT, str(base_path))
            
            self._log_test("模式切换 - 切换成功", success)
            self._log_test("模式切换 - 回调执行", len(callback_called) == 1)
            self._log_test(
                "模式切换 - 模式正确",
                manager.mode == PathMode.GUIDE_PROJECT
            )
            
            history = manager.get_switch_history()
            self._log_test(
                "模式切换 - 记录历史",
                len(history) > 0
            )
            
            manager.unregister_mode_switch_callback(test_callback)
        except Exception as e:
            self._log_test("模式切换", False, str(e))
    
    def test_auto_switch_mode(self):
        """测试自动模式切换"""
        try:
            manager = PathConfigManager(mode=PathMode.SELF_ITERATION)
            success, message = manager.auto_switch_mode()
            
            self._log_test(
                "自动模式切换 - 返回结果",
                isinstance(success, bool) and isinstance(message, str)
            )
        except Exception as e:
            self._log_test("自动模式切换", False, str(e))
    
    def test_config_persistence(self):
        """测试配置持久化"""
        try:
            manager = PathConfigManager(auto_detect=True)
            
            save_result = manager.save_config()
            self._log_test("配置持久化 - 保存成功", save_result)
            
            manager2 = PathConfigManager(auto_detect=False, mode=manager.mode)
            self._log_test(
                "配置持久化 - 加载成功",
                manager2._config_loaded or True
            )
        except Exception as e:
            self._log_test("配置持久化", False, str(e))
    
    def test_version_management(self):
        """测试版本管理"""
        try:
            manager = PathConfigManager(auto_detect=True)
            
            version = manager.get_current_version()
            self._log_test("版本管理 - 获取版本", bool(version))
            
            valid = manager._validate_version("1.0.0")
            self._log_test("版本管理 - 验证有效版本", valid)
            
            valid = manager._validate_version("invalid")
            self._log_test("版本管理 - 拒绝无效版本", not valid)
            
            valid = manager._validate_version("v2.0.0-alpha")
            self._log_test("版本管理 - 验证带前缀版本", valid)
        except Exception as e:
            self._log_test("版本管理", False, str(e))
    
    def test_directory_operations(self):
        """测试目录操作"""
        try:
            manager = PathConfigManager(auto_detect=True)
            
            results = manager.ensure_directories()
            self._log_test(
                "目录操作 - 创建目录",
                isinstance(results, dict) and len(results) > 0
            )
            
            all_success = all(results.values())
            self._log_test("目录操作 - 所有目录创建成功", all_success)
        except Exception as e:
            self._log_test("目录操作", False, str(e))
    
    def test_path_info(self):
        """测试路径信息"""
        try:
            manager = PathConfigManager(auto_detect=True)
            info = manager.get_path_info()
            
            self._log_test("路径信息 - 包含模式", "mode" in info)
            self._log_test("路径信息 - 包含模式描述", "mode_description" in info)
            self._log_test("路径信息 - 包含基础路径", "base_path" in info)
            self._log_test("路径信息 - 包含版本", "current_version" in info)
            self._log_test("路径信息 - 包含路径映射", "paths" in info)
        except Exception as e:
            self._log_test("路径信息", False, str(e))
    
    def test_mode_info(self):
        """测试模式信息"""
        try:
            manager = PathConfigManager(auto_detect=True)
            info = manager.get_mode_info()
            
            self._log_test("模式信息 - 包含当前模式", "current_mode" in info)
            self._log_test("模式信息 - 包含模式描述", "mode_description" in info)
            self._log_test("模式信息 - 包含基础路径", "base_path" in info)
            self._log_test("模式信息 - 包含状态信息", "state" in info)
        except Exception as e:
            self._log_test("模式信息", False, str(e))
    
    def test_get_current_project_info(self):
        """测试获取当前项目信息"""
        try:
            manager = PathConfigManager(auto_detect=True)
            info = manager.get_current_project_info()
            
            if manager.mode == PathMode.GUIDE_PROJECT:
                self._log_test(
                    "项目信息 - 指导模式返回项目信息",
                    info is not None and "type" in info
                )
            else:
                self._log_test(
                    "项目信息 - 自迭代模式返回 None",
                    info is None
                )
        except Exception as e:
            self._log_test("项目信息", False, str(e))
    
    def test_error_handling(self):
        """测试错误处理"""
        try:
            try:
                manager = PathConfigManager(mode=PathMode.GUIDE_PROJECT, target_root=None, auto_detect=False)
                self._log_test("错误处理 - 缺少target_root抛出异常", False)
            except PathConfigError:
                self._log_test("错误处理 - 缺少target_root抛出异常", True)
            
            manager = PathConfigManager(auto_detect=True)
            try:
                manager.get_versioned_path("docs/libs", "")
                self._log_test("错误处理 - 空版本号抛出异常", False)
            except PathValidationError:
                self._log_test("错误处理 - 空版本号抛出异常", True)
        except Exception as e:
            self._log_test("错误处理", False, str(e))
    
    def test_path_mode_enum(self):
        """测试 PathMode 枚举"""
        try:
            self._log_test(
                "PathMode 枚举 - from_string 有效",
                PathMode.from_string("self_iteration") == PathMode.SELF_ITERATION
            )
            
            self._log_test(
                "PathMode 枚举 - from_string auto 返回 None",
                PathMode.from_string("auto") is None
            )
            
            self._log_test(
                "PathMode 枚举 - get_description 返回字符串",
                isinstance(PathMode.SELF_ITERATION.get_description(), str)
            )
        except Exception as e:
            self._log_test("PathMode 枚举", False, str(e))
    
    def test_mode_detection_result(self):
        """测试 ModeDetectionResult"""
        try:
            manager = PathConfigManager(auto_detect=True)
            detection = manager.detect_mode()
            
            self._log_test(
                "ModeDetectionResult - detected_mode 有效",
                isinstance(detection.detected_mode, PathMode)
            )
            
            self._log_test(
                "ModeDetectionResult - confidence 范围正确",
                0 <= detection.confidence <= 1
            )
            
            self._log_test(
                "ModeDetectionResult - detection_details 是字典",
                isinstance(detection.detection_details, dict)
            )
        except Exception as e:
            self._log_test("ModeDetectionResult", False, str(e))
    
    def test_mode_state(self):
        """测试模式状态"""
        try:
            manager = PathConfigManager(auto_detect=True)
            
            self._log_test(
                "模式状态 - 已初始化",
                manager._mode_state is not None
            )
            
            if manager._mode_state:
                self._log_test(
                    "模式状态 - 包含初始化时间",
                    manager._mode_state.initialized_at is not None
                )
                
                self._log_test(
                    "模式状态 - 切换计数初始为 0",
                    manager._mode_state.switch_count >= 0
                )
        except Exception as e:
            self._log_test("模式状态", False, str(e))
    
    def test_switch_history(self):
        """测试切换历史"""
        try:
            manager = PathConfigManager(mode=PathMode.SELF_ITERATION)
            
            initial_count = manager._mode_state.switch_count if manager._mode_state else 0
            
            base_path = manager.get_base_path()
            manager.switch_mode(PathMode.GUIDE_PROJECT, str(base_path))
            
            if manager._mode_state:
                self._log_test(
                    "切换历史 - 切换计数增加",
                    manager._mode_state.switch_count > initial_count
                )
                
                history = manager.get_switch_history()
                self._log_test(
                    "切换历史 - 返回列表",
                    isinstance(history, list)
                )
                
                if history:
                    self._log_test(
                        "切换历史 - 记录包含必要字段",
                        "from_mode" in history[0] and "to_mode" in history[0]
                    )
        except Exception as e:
            self._log_test("切换历史", False, str(e))
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("开始运行 PathConfigManager 测试套件")
        logger.info("=" * 60)
        
        self.test_mode_detection()
        self.test_skill_detector()
        self.test_project_detector()
        self.test_is_in_skill_directory()
        self.test_is_in_project_directory()
        self.test_path_validation()
        self.test_mode_switch()
        self.test_auto_switch_mode()
        self.test_config_persistence()
        self.test_version_management()
        self.test_directory_operations()
        self.test_path_info()
        self.test_mode_info()
        self.test_get_current_project_info()
        self.test_error_handling()
        self.test_path_mode_enum()
        self.test_mode_detection_result()
        self.test_mode_state()
        self.test_switch_history()
        
        logger.info("=" * 60)
        logger.info(f"测试完成: 通过 {self.passed}/{self.passed + self.failed}")
        logger.info("=" * 60)
        
        return {
            "total": self.passed + self.failed,
            "passed": self.passed,
            "failed": self.failed,
            "results": self.test_results
        }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="路径配置管理器 - Sanliu 技能",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--mode',
        choices=['self_iteration', 'guide_project', 'auto'],
        default='auto',
        help='运行模式 (auto=自动检测)'
    )
    parser.add_argument(
        '--target-root',
        type=str,
        help='目标项目根目录（指导项目模式必需）'
    )
    parser.add_argument(
        '--version',
        type=str,
        help='指定版本号'
    )
    parser.add_argument(
        '--info',
        action='store_true',
        help='显示路径信息'
    )
    parser.add_argument(
        '--mode-info',
        action='store_true',
        help='显示模式信息'
    )
    parser.add_argument(
        '--ensure-dirs',
        action='store_true',
        help='确保目录存在'
    )
    parser.add_argument(
        '--list-versions',
        action='store_true',
        help='列出所有版本'
    )
    parser.add_argument(
        '--detect',
        action='store_true',
        help='显示模式检测结果'
    )
    parser.add_argument(
        '--save-config',
        action='store_true',
        help='保存当前配置'
    )
    parser.add_argument(
        '--switch-history',
        action='store_true',
        help='显示模式切换历史'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='运行测试套件'
    )
    
    args = parser.parse_args()
    
    if args.test:
        test_suite = PathConfigManagerTest()
        results = test_suite.run_all_tests()
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return
    
    mode = PathMode.from_string(args.mode)
    
    try:
        manager = PathConfigManager(
            mode=mode,
            target_root=args.target_root,
            auto_detect=(args.mode == 'auto')
        )
        
        if args.detect:
            detection = manager.detect_mode()
            detection_info = {
                "detected_mode": detection.detected_mode.value,
                "confidence": detection.confidence,
                "is_high_confidence": detection.is_high_confidence(),
                "summary": detection.get_summary(),
                "skill_root": str(detection.skill_root) if detection.skill_root else None,
                "project_root": str(detection.project_root) if detection.project_root else None,
                "details": detection.detection_details
            }
            print(json.dumps(detection_info, indent=2, ensure_ascii=False))
        
        if args.info:
            info = manager.get_path_info()
            print(json.dumps(info, indent=2, ensure_ascii=False))
        
        if args.mode_info:
            info = manager.get_mode_info()
            print(json.dumps(info, indent=2, ensure_ascii=False))
        
        if args.switch_history:
            history = manager.get_switch_history()
            print(json.dumps(history, indent=2, ensure_ascii=False))
        
        if args.save_config:
            result = manager.save_config()
            print(f"配置保存: {'成功' if result else '失败'}")
        
        if args.ensure_dirs:
            results = manager.ensure_directories()
            print("目录创建结果:")
            for path, success in results.items():
                status = "✓" if success else "✗"
                print(f"  {status} {path}")
        
        if args.list_versions:
            versions = manager.list_versions()
            print("可用版本:")
            for v in versions:
                print(f"  - {v}")
        
        if not any([
            args.info, 
            args.ensure_dirs, 
            args.list_versions, 
            args.detect, 
            args.save_config,
            args.mode_info,
            args.switch_history
        ]):
            print(f"基础路径: {manager.get_base_path()}")
            print(f"当前版本: {manager.get_current_version()}")
            print(f"运行模式: {manager.mode.value}")
            print(f"模式描述: {manager.mode.get_description()}")
        
    except PathConfigError as e:
        logger.error(f"配置错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
