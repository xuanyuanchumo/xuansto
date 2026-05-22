#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD+TDD循环开发模式

实现规范驱动开发(SDD)与测试驱动开发(TDD)的完整融合循环。

模块组成：
1. enhanced_spec_parser - 增强的SDD规范解析器
2. spec_to_test_mapper - 规范到测试用例映射器
3. spec_to_code_generator - 规范到代码骨架生成器
4. spec_completeness_validator - 规范完整性验证器
5. tdd_cycle_executor - TDD红绿蓝循环执行器
6. sdd_tdd_integration - SDD-TDD集成流程
"""

from .enhanced_spec_parser import (
    EnhancedSDDSpecParser,
    SpecFormat,
    SpecType,
    SDDSpecification,
    SpecMetadata,
    SpecAttribute,
    SpecEndpoint,
    SpecScenario,
    ValidationResult,
)

from .spec_to_test_mapper import (
    SpecToTestMapper,
    TestCaseMapping,
    TestGenerationStrategy,
)

from .spec_to_code_generator import (
    SpecToCodeGenerator,
    CodeSkeleton,
    CodeLanguage,
    CodeArtifactType,
)

from .spec_completeness_validator import (
    SpecCompletenessValidator,
    CompletenessReport,
    CompletenessLevel,
)

from .tdd_cycle_executor import (
    TDDCycleExecutor,
    TDDCyclePhase,
    TDDCycleResult,
    RedPhaseResult,
    GreenPhaseResult,
    BluePhaseResult,
)

from .sdd_tdd_integration import (
    SddTddIntegration,
    IntegrationConfig,
    IntegrationResult,
)

__version__ = "1.0.0"
__all__ = [
    "EnhancedSDDSpecParser",
    "SpecFormat",
    "SpecType",
    "SDDSpecification",
    "SpecMetadata",
    "SpecAttribute",
    "SpecEndpoint",
    "SpecScenario",
    "ValidationResult",
    "SpecToTestMapper",
    "TestCaseMapping",
    "TestGenerationStrategy",
    "SpecToCodeGenerator",
    "CodeSkeleton",
    "CodeLanguage",
    "CodeArtifactType",
    "SpecCompletenessValidator",
    "CompletenessReport",
    "CompletenessLevel",
    "TDDCycleExecutor",
    "TDDCyclePhase",
    "TDDCycleResult",
    "RedPhaseResult",
    "GreenPhaseResult",
    "BluePhaseResult",
    "SddTddIntegration",
    "IntegrationConfig",
    "IntegrationResult",
]
