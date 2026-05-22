#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD-TDD 深度融合引擎单元测试

测试覆盖:
1. SDD规范解析 (Markdown/JSON/YAML)
2. 测试骨架生成
3. 完整红绿蓝循环模拟
4. 产物追溯完整性
5. 连续循环执行
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

# 添加项目根目录到 Python 路径
_PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from skillscripts.core.path_config_center import get_path_config

_PCC = get_path_config()

# 直接添加 skillscripts 目录到路径以支持子模块导入
_SCRIPTS_DIR = _PCC.SCRIPTS_DIR
sys.path.insert(0, str(_SCRIPTS_DIR))
sys.path.insert(0, str(_SCRIPTS_DIR / "pipeline"))
sys.path.insert(0, str(_SCRIPTS_DIR / "test"))

# 直接导入融合引擎模块（绕过 __init__.py 的复杂依赖链）
import importlib.util

def _load_module(name, file_path):
    spec = importlib.util.spec_from_file_location(name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# 加载融合引擎模块
_sdd_tdd = _load_module("sdd_tdd_fusion_engine", 
                         _SCRIPTS_DIR / "pipeline" / "sdd_tdd_fusion_engine.py")

# 导出所有需要的类和函数
FusionPhase = _sdd_tdd.FusionPhase
PhaseStatus = _sdd_tdd.PhaseStatus
CycleStatus = _sdd_tdd.CycleStatus
SDDSpec = _sdd_tdd.SDDSpec
Requirement = _sdd_tdd.Requirement
AcceptanceCriterion = _sdd_tdd.AcceptanceCriterion
TestCase = _sdd_tdd.TestCase
TestResult = _sdd_tdd.TestResult
FailureAnalysis = _sdd_tdd.FailureAnalysis
FailureInfo = _sdd_tdd.FailureInfo
ImplementationGuide = _sdd_tdd.ImplementationGuide
RefactoringSuggestion = _sdd_tdd.RefactoringSuggestion
OptimizationResult = _sdd_tdd.OptimizationResult
RegressionResult = _sdd_tdd.RegressionResult
ArtifactTrace = _sdd_tdd.ArtifactTrace
PhaseResult = _sdd_tdd.PhaseResult
CycleReport = _sdd_tdd.CycleReport
ContinuousCycleReport = _sdd_tdd.ContinuousCycleReport
FusionEngineConfig = _sdd_tdd.FusionEngineConfig
SDDSpecParser = _sdd_tdd.SDDSpecParser
TestSkeletonGenerator = _sdd_tdd.TestSkeletonGenerator
TestRunner = _sdd_tdd.TestRunner
FailureAnalyzer = _sdd_tdd.FailureAnalyzer
ImplementationGuideGenerator = _sdd_tdd.ImplementationGuideGenerator
RefactoringAnalyzer = _sdd_tdd.RefactoringAnalyzer
OptimizationApplier = _sdd_tdd.OptimizationApplier
RegressionTester = _sdd_tdd.RegressionTester
ArtifactTracer = _sdd_tdd.ArtifactTracer
SpecDocumentationUpdater = _sdd_tdd.SpecDocumentationUpdater
ReportGenerator = _sdd_tdd.ReportGenerator
SDDTDDFusionEngine = _sdd_tdd.SDDTDDFusionEngine