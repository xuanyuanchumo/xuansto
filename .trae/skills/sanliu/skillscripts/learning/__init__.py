#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动学习模块 - Auto Learning Module

提供完整的自动学习能力，包括模式识别、最佳实践提取、知识库管理和知识应用。

核心组件:
- PatternRecognizer: 模式识别器
- BestPracticeExtractor: 最佳实践提取器
- KnowledgeUpdater: 知识库更新器
- KnowledgeApplicationEngine: 知识应用引擎
- AutoLearner: 自动学习主控制器
"""

from .pattern_recognizer import (
    PatternRecognizer,
    PatternType,
    PatternConfidence,
    RecognizedPattern
)

from .best_practice_extractor import (
    BestPracticeExtractor,
    PracticeCategory,
    PracticeQuality,
    ExtractedPractice
)

from .knowledge_updater import (
    KnowledgeUpdater,
    KnowledgeCategory,
    KnowledgeQuality,
    UpdateStrategy
)

from .knowledge_application_engine import (
    KnowledgeApplicationEngine,
    ApplicationContext,
    ApplicationSuggestion,
    ApplicationResult
)

from .auto_learner import (
    AutoLearner,
    LearningMode,
    LearningStatus
)

from .knowledge_application_engine import (
    KnowledgeApplicationEngine,
    ApplicationContext,
    ApplicationSuggestion,
    ApplicationResult,
    ApplicationStatus,
    FeedbackType
)

__all__ = [
    'PatternRecognizer',
    'PatternType',
    'PatternConfidence',
    'RecognizedPattern',
    'BestPracticeExtractor',
    'PracticeCategory',
    'PracticeQuality',
    'ExtractedPractice',
    'KnowledgeUpdater',
    'KnowledgeCategory',
    'KnowledgeQuality',
    'UpdateStrategy',
    'KnowledgeApplicationEngine',
    'ApplicationContext',
    'ApplicationSuggestion',
    'ApplicationResult',
    'ApplicationStatus',
    'FeedbackType',
    'AutoLearner',
    'LearningMode',
    'LearningStatus'
]

__version__ = '1.0.0'
