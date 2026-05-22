#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修复系统 - Auto Repair System

增强三省六部技能的自动修复能力，包括：
- 问题检测器：语法、导入、类型、安全漏洞检测
- 修复策略库：语法、导入、类型、安全修复策略
- 修复执行器：预览、回滚、验证、历史记录
- 自动修复工作流：完整的修复流程
- 文档自动修复器：链接修复、格式修复

使用示例:
    from auto_repair import AutoRepairSystem
    from auto_repair import DocumentAutoFixer
    
    system = AutoRepairSystem()
    result = system.repair_file("code.py")
    
    doc_fixer = DocumentAutoFixer()
    doc_result = doc_fixer.fix_document("README.md")
"""

from .issue_detector import (
    IssueDetector,
    IssueCategory,
    IssueSeverity,
    Issue,
    DetectionResult
)

from .fix_strategy import (
    FixStrategyLibrary,
    FixStrategy,
    FixResult,
    FixStatus,
    StrategyPriority
)

from .fix_executor import (
    FixExecutor,
    FixPreview,
    FixHistory,
    RollbackManager,
    ExecutionResult
)

from .auto_repair_workflow import (
    AutoRepairWorkflow,
    WorkflowConfig,
    WorkflowResult,
    WorkflowStage
)

from .doc_auto_fixer import (
    DocumentAutoFixer,
    LinkFixer,
    FormatFixer,
    DocIssueType,
    DocIssue,
    DocFixResult,
    DocumentFixReport
)

__version__ = "1.0.0"
__all__ = [
    "IssueDetector",
    "IssueCategory",
    "IssueSeverity", 
    "Issue",
    "DetectionResult",
    "FixStrategyLibrary",
    "FixStrategy",
    "FixResult",
    "FixStatus",
    "StrategyPriority",
    "FixExecutor",
    "FixPreview",
    "FixHistory",
    "RollbackManager",
    "ExecutionResult",
    "AutoRepairWorkflow",
    "WorkflowConfig",
    "WorkflowResult",
    "WorkflowStage",
    "DocumentAutoFixer",
    "LinkFixer",
    "FormatFixer",
    "DocIssueType",
    "DocIssue",
    "DocFixResult",
    "DocumentFixReport"
]
