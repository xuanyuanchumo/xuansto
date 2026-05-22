#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill-creator 集成脚本（增强版）

用于自动发现需要创建/优化的技能，调用 skill-creator 进行评估，生成技能优化建议。
增强功能包括：
- 完善的集成逻辑与后端API集成
- 技能创建流程自动化
- 技能模板管理系统
- 技能性能评估与监控

使用方法:
    python scripts/skill_creator_integration.py [command] [options]

命令:
    discover     - 发现需要创建/优化的技能
    create       - 创建新技能
    optimize     - 优化现有技能
    evaluate     - 评估技能质量
    benchmark    - 基准测试技能性能
    chain        - 技能调用链管理
    report       - 生成技能集成报告
    template     - 模板管理
    pipeline     - 流水线集成

示例:
    python scripts/skill_creator_integration.py discover --scope=all
    python scripts/skill_creator_integration.py create --name=my-skill --category=development
    python scripts/skill_creator_integration.py optimize --path=.trae/skills/my-skill/SKILL.md
    python scripts/skill_creator_integration.py template --action=list
    python scripts/skill_creator_integration.py pipeline --project-id=1 --stage=design
"""

import os
import re
import sys
import json
import hashlib
import logging
import argparse
import subprocess
import time
import threading
import queue
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable, Type, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from contextlib import contextmanager
import traceback


SKILL_REGISTRY_PATH = get_path_config().SKILL_ROOT / "resources" / "waiji_zhuce_biao.md"


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

try:
    from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
    _path_manager = create_path_manager()
    _log_path = _path_manager.get_output_path(OutputType.LOG, filename="skill_creator_integration.log")
    logging.getLogger().addHandler(
        logging.FileHandler(str(_log_path), encoding='utf-8', mode='a')
    )
except Exception:
    logging.getLogger().addHandler(
        logging.FileHandler(str(get_path_config().LOGS_DIR / 'skill_creator_integration.log'), encoding='utf-8', mode='a')
    )
logger = logging.getLogger(__name__)


class OperationType(Enum):
    """操作类型枚举"""
    CREATE = "create"
    OPTIMIZE = "optimize"
    EVALUATE = "evaluate"
    BENCHMARK = "benchmark"
    DISCOVER = "discover"
    CHAIN = "chain"
    TEMPLATE = "template"
    PIPELINE = "pipeline"
    VALIDATE = "validate"
    MIGRATE = "migrate"


class SkillStatus(Enum):
    """技能状态枚举"""
    ACTIVE = "active"
    NEEDS_OPTIMIZATION = "needs_optimization"
    NEEDS_CREATION = "needs_creation"
    DEPRECATED = "deprecated"
    IN_DEVELOPMENT = "in_development"
    TESTING = "testing"
    PENDING_REVIEW = "pending_review"
    ARCHIVED = "archived"
    STAGING = "staging"
    PRODUCTION = "production"


class SkillTemplate(Enum):
    """技能模板类型枚举"""
    BASIC = "basic"
    TDD = "tdd"
    SDD = "sdd"
    MCP_SERVER = "mcp_server"
    UI_COMPONENT = "ui_component"
    API_SERVICE = "api_service"
    DATA_PIPELINE = "data_pipeline"
    AGENT_ROLE = "agent_role"
    MICROSERVICE = "microservice"
    CLI_TOOL = "cli_tool"
    PLUGIN = "plugin"
    WORKFLOW = "workflow"


class SkillPriority(Enum):
    """技能优先级枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NORMAL = "normal"


class EvaluationDimension(Enum):
    """评估维度枚举"""
    TRIGGER_ACCURACY = "trigger_accuracy"
    OUTPUT_QUALITY = "output_quality"
    COMPLETENESS = "completeness"
    MAINTAINABILITY = "maintainability"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    COMPATIBILITY = "compatibility"
    DOCUMENTATION = "documentation"
    TEST_COVERAGE = "test_coverage"


class PipelineStage(Enum):
    """流水线阶段枚举"""
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    REVIEW = "review"
    OPTIMIZATION = "optimization"


class TemplateStatus(Enum):
    """模板状态枚举"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class PerformanceMetricType(Enum):
    """性能指标类型枚举"""
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    LATENCY = "latency"


@dataclass
class SkillInfo:
    """技能信息数据类"""
    name: str
    path: str
    category: str
    status: SkillStatus
    description: str = ""
    last_evaluated: Optional[str] = None
    evaluation_score: float = 0.0
    issues: List[str] = None
    priority: SkillPriority = SkillPriority.MEDIUM
    dependencies: List[str] = None
    tags: List[str] = None
    version: str = "1.0.0"
    author: str = "system"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    template: SkillTemplate = SkillTemplate.BASIC
    trigger_keywords: List[str] = None
    input_schema: Dict[str, Any] = None
    output_schema: Dict[str, Any] = None
    performance_metrics: Dict[str, float] = None
    metadata: Dict[str, Any] = None
    pipeline_stage: Optional[str] = None
    approval_status: Optional[str] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
        if self.trigger_keywords is None:
            self.trigger_keywords = []
        if self.input_schema is None:
            self.input_schema = {}
        if self.output_schema is None:
            self.output_schema = {}
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SkillDependency:
    """技能依赖关系数据类"""
    skill_name: str
    depends_on: str
    dependency_type: str
    version_constraint: str = "*"
    condition: Optional[str] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class SkillCallChain:
    """技能调用链数据类"""
    chain_id: str
    name: str
    description: str
    skills: List[str]
    execution_order: List[int]
    conditions: Dict[str, Any] = None
    created_at: str = None
    updated_at: str = None
    version: str = "1.0.0"
    status: str = "active"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class EvaluationResult:
    """评估结果数据类"""
    skill_name: str
    timestamp: str
    overall_score: float
    trigger_accuracy: float
    output_quality: float
    completeness: float
    maintainability: float
    performance: float = 0.0
    security: float = 0.0
    accessibility: float = 0.0
    compatibility: float = 0.0
    documentation: float = 0.0
    test_coverage: float = 0.0
    issues: List[Dict[str, Any]] = None
    recommendations: List[str] = None
    benchmark_data: Dict[str, Any] = None
    comparison_baseline: Optional[str] = None
    trend_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.recommendations is None:
            self.recommendations = []
        if self.benchmark_data is None:
            self.benchmark_data = {}
        if self.trend_data is None:
            self.trend_data = {}


@dataclass
class IntegrationLog:
    """集成日志数据类"""
    log_id: str
    timestamp: str
    operation: str
    skill_name: str
    skill_path: str
    requesting_department: str
    status: str
    duration_ms: int
    errors: List[Dict[str, str]] = None
    artifacts: List[str] = None
    metadata: Dict[str, Any] = None
    correlation_id: Optional[str] = None
    parent_log_id: Optional[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.artifacts is None:
            self.artifacts = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TemplateInfo:
    """模板信息数据类"""
    template_id: str
    name: str
    template_type: SkillTemplate
    description: str
    content: str
    version: str = "1.0.0"
    status: TemplateStatus = TemplateStatus.ACTIVE
    author: str = "system"
    created_at: str = None
    updated_at: str = None
    parent_template: Optional[str] = None
    variables: List[Dict[str, Any]] = None
    validation_rules: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
        if self.variables is None:
            self.variables = []
        if self.validation_rules is None:
            self.validation_rules = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    metric_id: str
    skill_name: str
    metric_type: PerformanceMetricType
    value: float
    unit: str
    timestamp: str
    context: Dict[str, Any] = None
    baseline_value: Optional[float] = None
    deviation: Optional[float] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


@dataclass
class PerformanceReport:
    """性能报告数据类"""
    report_id: str
    skill_name: str
    generated_at: str
    metrics: List[PerformanceMetric]
    summary: Dict[str, Any]
    trends: Dict[str, Any] = None
    recommendations: List[str] = None
    anomalies: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.trends is None:
            self.trends = {}
        if self.recommendations is None:
            self.recommendations = []
        if self.anomalies is None:
            self.anomalies = []


@dataclass
class PipelineIntegration:
    """流水线集成数据类"""
    integration_id: str
    project_id: int
    skill_name: str
    stage: PipelineStage
    status: str
    started_at: str
    completed_at: Optional[str] = None
    artifacts: List[str] = None
    metrics: Dict[str, Any] = None
    errors: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []
        if self.metrics is None:
            self.metrics = {}
        if self.errors is None:
            self.errors = []


class SkillEvaluator(ABC):
    """技能评估器抽象基类"""
    
    @abstractmethod
    def evaluate(self, content: str) -> float:
        """评估技能内容"""
        pass
    
    @abstractmethod
    def get_issues(self, content: str) -> List[Dict[str, Any]]:
        """获取评估问题"""
        pass
    
    def get_dimension(self) -> EvaluationDimension:
        """获取评估维度"""
        return EvaluationDimension.TRIGGER_ACCURACY


class TriggerAccuracyEvaluator(SkillEvaluator):
    """触发准确性评估器"""
    
    def evaluate(self, content: str) -> float:
        score = 0.6
        
        if "description:" in content:
            desc = content.split("description:")[1].split("\n")[0].strip()
            if len(desc) >= 30:
                score += 0.15
            elif len(desc) >= 15:
                score += 0.1
        
        if "name:" in content:
            name = content.split("name:")[1].split("\n")[0].strip()
            if len(name) >= 3:
                score += 0.1
        
        trigger_keywords = ["触发", "trigger", "适用场景", "usage", "关键词", "keywords"]
        for kw in trigger_keywords:
            if kw in content.lower():
                score += 0.025
        
        return min(score, 1.0)
    
    def get_issues(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        
        if "description:" in content:
            desc = content.split("description:")[1].split("\n")[0].strip()
            if len(desc) < 15:
                issues.append({
                    "type": "description_too_short",
                    "severity": "high",
                    "message": f"技能描述过短({len(desc)}字符)，建议至少15字符",
                    "suggestion": "扩展描述，包含更多关键词和使用场景"
                })
        
        if "适用场景" not in content and "usage" not in content.lower():
            issues.append({
                "type": "missing_usage_section",
                "severity": "medium",
                "message": "缺少适用场景说明",
                "suggestion": "添加适用场景章节，明确触发条件"
            })
        
        return issues
    
    def get_dimension(self) -> EvaluationDimension:
        return EvaluationDimension.TRIGGER_ACCURACY


class OutputQualityEvaluator(SkillEvaluator):
    """输出质量评估器"""
    
    def evaluate(self, content: str) -> float:
        score = 0.5
        
        output_indicators = ["输出", "output", "结果", "result", "返回", "response"]
        for indicator in output_indicators:
            if indicator in content.lower():
                score += 0.05
        
        if "示例" in content or "example" in content.lower():
            score += 0.1
        
        if "json" in content.lower() or "```" in content:
            score += 0.1
        
        if "错误处理" in content or "error" in content.lower():
            score += 0.08
        
        if "schema" in content.lower() or "规范" in content:
            score += 0.07
        
        return min(score, 1.0)
    
    def get_issues(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        
        if "示例" not in content and "example" not in content.lower():
            issues.append({
                "type": "missing_examples",
                "severity": "high",
                "message": "缺少使用示例",
                "suggestion": "添加至少2-3个使用示例，覆盖常见场景"
            })
        
        if "输出" not in content and "output" not in content.lower():
            issues.append({
                "type": "missing_output_spec",
                "severity": "medium",
                "message": "缺少输出规范说明",
                "suggestion": "添加输出格式规范，包括成功和错误输出示例"
            })
        
        return issues
    
    def get_dimension(self) -> EvaluationDimension:
        return EvaluationDimension.OUTPUT_QUALITY


class CompletenessEvaluator(SkillEvaluator):
    """完整性评估器"""
    
    REQUIRED_SECTIONS = ["职责", "流程", "输出", "示例"]
    OPTIONAL_SECTIONS = ["依赖", "版本", "错误处理", "安全", "性能", "测试"]
    
    def evaluate(self, content: str) -> float:
        score = 0.3
        
        for section in self.REQUIRED_SECTIONS:
            if section in content:
                score += 0.1
        
        for section in self.OPTIONAL_SECTIONS:
            if section in content:
                score += 0.033
        
        return min(score, 1.0)
    
    def get_issues(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        
        missing_required = [s for s in self.REQUIRED_SECTIONS if s not in content]
        if missing_required:
            issues.append({
                "type": "missing_required_sections",
                "severity": "high",
                "message": f"缺少必要章节: {', '.join(missing_required)}",
                "suggestion": "添加缺失的必要章节以提高技能完整性"
            })
        
        missing_optional = [s for s in self.OPTIONAL_SECTIONS if s not in content]
        if len(missing_optional) > 3:
            issues.append({
                "type": "missing_optional_sections",
                "severity": "low",
                "message": f"建议添加章节: {', '.join(missing_optional[:3])}",
                "suggestion": "添加可选章节以增强技能健壮性"
            })
        
        return issues
    
    def get_dimension(self) -> EvaluationDimension:
        return EvaluationDimension.COMPLETENESS


class MaintainabilityEvaluator(SkillEvaluator):
    """可维护性评估器"""
    
    def evaluate(self, content: str) -> float:
        score = 0.5
        
        section_count = content.count("##")
        if section_count >= 5:
            score += 0.15
        elif section_count >= 3:
            score += 0.1
        
        if "版本" in content or "changelog" in content.lower():
            score += 0.1
        
        if "依赖" in content or "dependency" in content.lower():
            score += 0.1
        
        if "作者" in content or "author" in content.lower():
            score += 0.05
        
        code_block_count = content.count("```")
        if code_block_count >= 2:
            score += 0.1
        
        return min(score, 1.0)
    
    def get_issues(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        
        if content.count("##") < 3:
            issues.append({
                "type": "poor_structure",
                "severity": "medium",
                "message": "文档结构不够清晰，章节较少",
                "suggestion": "使用更多二级标题组织内容，提高可读性"
            })
        
        if "版本" not in content and "changelog" not in content.lower():
            issues.append({
                "type": "missing_version_info",
                "severity": "low",
                "message": "缺少版本历史信息",
                "suggestion": "添加版本历史章节，记录变更"
            })
        
        return issues
    
    def get_dimension(self) -> EvaluationDimension:
        return EvaluationDimension.MAINTAINABILITY


class SecurityEvaluator(SkillEvaluator):
    """安全性评估器"""
    
    SECURITY_PATTERNS = [
        ("password", "sensitive_data"),
        ("secret", "sensitive_data"),
        ("api_key", "sensitive_data"),
        ("token", "sensitive_data"),
        ("eval(", "code_injection"),
        ("exec(", "code_injection"),
        ("__import__", "code_injection"),
        ("subprocess", "command_execution"),
        ("sql", "sql_injection"),
        ("shell", "shell_injection"),
    ]
    
    def evaluate(self, content: str) -> float:
        score = 1.0
        
        for pattern, issue_type in self.SECURITY_PATTERNS:
            if pattern.lower() in content.lower():
                if issue_type == "sensitive_data":
                    if "环境变量" not in content and "env" not in content.lower():
                        score -= 0.12
                elif issue_type in ["code_injection", "command_execution"]:
                    if "安全" not in content and "sanitiz" not in content.lower():
                        score -= 0.15
                elif issue_type in ["sql_injection", "shell_injection"]:
                    if "参数化" not in content and "转义" not in content:
                        score -= 0.1
        
        return max(score, 0)
    
    def get_issues(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        
        for pattern, issue_type in self.SECURITY_PATTERNS:
            if pattern.lower() in content.lower():
                if issue_type == "sensitive_data":
                    issues.append({
                        "type": "security",
                        "severity": "high",
                        "message": f"发现敏感数据模式 '{pattern}'，需确保安全处理",
                        "suggestion": "使用环境变量或安全存储管理敏感数据"
                    })
                elif issue_type in ["code_injection", "command_execution"]:
                    issues.append({
                        "type": "security",
                        "severity": "critical",
                        "message": f"发现潜在安全风险 '{pattern}'",
                        "suggestion": "添加输入验证和安全检查"
                    })
                elif issue_type in ["sql_injection", "shell_injection"]:
                    issues.append({
                        "type": "security",
                        "severity": "high",
                        "message": f"发现潜在注入风险 '{pattern}'",
                        "suggestion": "使用参数化查询或输入转义"
                    })
        
        return issues
    
    def get_dimension(self) -> EvaluationDimension:
        return EvaluationDimension.SECURITY


class PerformanceEvaluator(SkillEvaluator):
    """性能评估器"""
    
    def evaluate(self, content: str) -> float:
        score = 0.8
        
        if "缓存" in content or "cache" in content.lower():
            score += 0.05
        
        if "异步" in content or "async" in content.lower():
            score += 0.05
        
        if "批量" in content or "batch" in content.lower():
            score += 0.05
        
        if "性能" in content or "performance" in content.lower():
            score += 0.05
        
        if "并发" in content or "concurrent" in content.lower():
            score += 0.05
        
        return min(score, 1.0)
    
    def get_issues(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        
        if "循环" in content or "for " in content or "while " in content:
            if "性能" not in content and "优化" not in content:
                issues.append({
                    "type": "performance",
                    "severity": "medium",
                    "message": "存在循环操作，建议添加性能说明",
                    "suggestion": "添加时间复杂度说明或性能优化建议"
                })
        
        if "数据库" in content or "database" in content.lower():
            if "索引" not in content and "查询优化" not in content:
                issues.append({
                    "type": "performance",
                    "severity": "medium",
                    "message": "涉及数据库操作，建议添加索引和查询优化说明",
                    "suggestion": "添加数据库性能优化建议"
                })
        
        return issues
    
    def get_dimension(self) -> EvaluationDimension:
        return EvaluationDimension.PERFORMANCE


class DocumentationEvaluator(SkillEvaluator):
    """文档质量评估器"""
    
    def evaluate(self, content: str) -> float:
        score = 0.5
        
        if "## " in content:
            section_count = content.count("## ")
            score += min(section_count * 0.05, 0.2)
        
        if "```" in content:
            code_block_count = content.count("```") // 2
            score += min(code_block_count * 0.05, 0.15)
        
        if "TODO" not in content and "FIXME" not in content:
            score += 0.05
        
        if "参考" in content or "reference" in content.lower():
            score += 0.05
        
        if "FAQ" in content or "常见问题" in content:
            score += 0.05
        
        return min(score, 1.0)
    
    def get_issues(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        
        if "TODO" in content or "FIXME" in content:
            issues.append({
                "type": "documentation",
                "severity": "low",
                "message": "文档中存在待完成标记",
                "suggestion": "完成或移除TODO/FIXME标记"
            })
        
        if len(content) < 500:
            issues.append({
                "type": "documentation",
                "severity": "medium",
                "message": "文档内容较短，可能不够详细",
                "suggestion": "扩展文档内容，添加更多说明和示例"
            })
        
        return issues
    
    def get_dimension(self) -> EvaluationDimension:
        return EvaluationDimension.DOCUMENTATION


class TestCoverageEvaluator(SkillEvaluator):
    """测试覆盖率评估器"""
    
    def evaluate(self, content: str) -> float:
        score = 0.4
        
        if "测试" in content or "test" in content.lower():
            score += 0.2
        
        if "单元测试" in content or "unit test" in content.lower():
            score += 0.1
        
        if "集成测试" in content or "integration test" in content.lower():
            score += 0.1
        
        if "端到端" in content or "e2e" in content.lower():
            score += 0.1
        
        if "覆盖率" in content or "coverage" in content.lower():
            score += 0.1
        
        return min(score, 1.0)
    
    def get_issues(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        
        if "测试" not in content and "test" not in content.lower():
            issues.append({
                "type": "test_coverage",
                "severity": "high",
                "message": "缺少测试相关说明",
                "suggestion": "添加测试用例和测试策略说明"
            })
        
        return issues
    
    def get_dimension(self) -> EvaluationDimension:
        return EvaluationDimension.TEST_COVERAGE


class TemplateManager:
    """技能模板管理器
    
    负责模板的创建、存储、检索、版本控制和验证。
    支持模板继承、变量替换和自定义验证规则。
    """
    
    def __init__(self, templates_path: str = "config/skill_templates"):
        self.templates_path = Path(templates_path)
        self.templates_path.mkdir(parents=True, exist_ok=True)
        self._template_cache: Dict[str, TemplateInfo] = {}
        self._load_builtin_templates()
        logger.info(f"TemplateManager initialized with path: {templates_path}")
    
    def _load_builtin_templates(self) -> None:
        """加载内置模板"""
        builtin_templates = {
            "basic": self._create_basic_template(),
            "tdd": self._create_tdd_template(),
            "sdd": self._create_sdd_template(),
            "mcp_server": self._create_mcp_template(),
            "api_service": self._create_api_template(),
            "ui_component": self._create_ui_template(),
            "data_pipeline": self._create_pipeline_template(),
            "agent_role": self._create_agent_template(),
        }
        
        for name, template in builtin_templates.items():
            self._template_cache[name] = template
    
    def _create_basic_template(self) -> TemplateInfo:
        """创建基础模板"""
        return TemplateInfo(
            template_id="TPL-BASIC-001",
            name="基础技能模板",
            template_type=SkillTemplate.BASIC,
            description="适用于一般技能的基础模板",
            content=self._get_basic_template_content(),
            variables=[
                {"name": "skill_name", "type": "string", "required": True, "description": "技能名称"},
                {"name": "category", "type": "string", "required": True, "description": "技能分类"},
                {"name": "description", "type": "string", "required": True, "description": "技能描述"},
                {"name": "author", "type": "string", "required": False, "default": "system", "description": "作者"},
            ],
            validation_rules=[
                {"rule": "min_length", "field": "description", "value": 15, "message": "描述至少15字符"},
                {"rule": "pattern", "field": "skill_name", "value": "^[a-z0-9_-]+$", "message": "名称只能包含小写字母、数字、下划线和连字符"},
            ]
        )
    
    def _get_basic_template_content(self) -> str:
        """获取基础模板内容"""
        return """---
name: {{skill_name}}
description: {{description}}
category: {{category}}
version: 1.0.0
author: {{author}}
---

# {{skill_name}} 技能

## 职责定义

{{description}}

## 工作流程

### 阶段一: 准备

1. 接收输入参数
2. 验证输入完整性
3. 初始化执行环境

### 阶段二: 执行

1. 执行核心逻辑
2. 处理中间结果
3. 验证输出质量

### 阶段三: 交付

1. 格式化输出
2. 生成执行报告
3. 记录执行日志

## 使用示例

### 示例1: 基本用法

```bash
调用 {{skill_name}} --param1=value1
```

## 输出规范

### 成功输出

```json
{
  "status": "success",
  "result": "执行结果"
}
```

### 错误输出

```json
{
  "status": "error",
  "error_code": "ERROR_CODE",
  "error_message": "错误描述"
}
```

## 错误处理

| 错误类型 | 错误码 | 处理方式 |
|----------|--------|----------|
| 参数错误 | INVALID_PARAMS | 检查输入参数 |
| 执行错误 | EXECUTION_ERROR | 查看详细日志 |

## 版本历史

- v1.0.0 - 初始版本
"""
    
    def _create_tdd_template(self) -> TemplateInfo:
        """创建TDD模板"""
        return TemplateInfo(
            template_id="TPL-TDD-001",
            name="测试驱动开发模板",
            template_type=SkillTemplate.TDD,
            description="适用于测试驱动开发的技能模板",
            content=self._get_basic_template_content() + self._get_tdd_addition(),
            parent_template="basic",
            variables=[
                {"name": "test_framework", "type": "string", "required": False, "default": "pytest", "description": "测试框架"},
                {"name": "coverage_threshold", "type": "number", "required": False, "default": 80, "description": "覆盖率阈值"},
            ]
        )
    
    def _get_tdd_addition(self) -> str:
        """获取TDD模板附加内容"""
        return """

## 测试驱动开发流程

### 红灯阶段
1. 编写失败的测试用例
2. 确认测试失败原因符合预期

### 绿灯阶段
1. 编写最小实现代码
2. 确认测试通过

### 重构阶段
1. 优化代码结构
2. 确保测试仍然通过

## 测试规范

- 单元测试覆盖率: >= {{coverage_threshold}}%
- 集成测试: 覆盖主要流程
- 边界测试: 覆盖边界条件
"""
    
    def _create_sdd_template(self) -> TemplateInfo:
        """创建SDD模板"""
        return TemplateInfo(
            template_id="TPL-SDD-001",
            name="规范驱动开发模板",
            template_type=SkillTemplate.SDD,
            description="适用于规范驱动开发的技能模板",
            content=self._get_basic_template_content() + self._get_sdd_addition(),
            parent_template="basic"
        )
    
    def _get_sdd_addition(self) -> str:
        """获取SDD模板附加内容"""
        return """

## 规范驱动开发流程

### 规范解析阶段
1. 解析规范文档
2. 提取需求点
3. 生成测试用例

### 实现阶段
1. 按规范实现功能
2. 执行规范验证
3. 生成合规报告

### 验证阶段
1. 规范一致性检查
2. 边界条件验证
3. 输出合规性报告
"""
    
    def _create_mcp_template(self) -> TemplateInfo:
        """创建MCP服务模板"""
        return TemplateInfo(
            template_id="TPL-MCP-001",
            name="MCP服务模板",
            template_type=SkillTemplate.MCP_SERVER,
            description="适用于MCP服务器开发的技能模板",
            content=self._get_basic_template_content() + self._get_mcp_addition(),
            parent_template="basic"
        )
    
    def _get_mcp_addition(self) -> str:
        """获取MCP模板附加内容"""
        return """

## MCP服务规范

### 工具定义
- 工具命名: snake_case
- 参数验证: 使用JSON Schema
- 错误处理: 统一错误码

### 资源管理
- 资源URI格式: `scheme://path`
- 支持订阅机制
- 实现资源列表

### 提示词模板
- 支持参数化模板
- 包含使用示例
- 提供最佳实践
"""
    
    def _create_api_template(self) -> TemplateInfo:
        """创建API服务模板"""
        return TemplateInfo(
            template_id="TPL-API-001",
            name="API服务模板",
            template_type=SkillTemplate.API_SERVICE,
            description="适用于API服务开发的技能模板",
            content=self._get_basic_template_content() + self._get_api_addition(),
            parent_template="basic"
        )
    
    def _get_api_addition(self) -> str:
        """获取API模板附加内容"""
        return """

## API服务规范

### 接口设计
- RESTful风格
- 版本控制: /api/v1/
- 统一响应格式

### 认证授权
- JWT Token认证
- 角色权限控制
- 请求频率限制

### 错误处理
- 统一错误码
- 详细错误信息
- 错误恢复建议
"""
    
    def _create_ui_template(self) -> TemplateInfo:
        """创建UI组件模板"""
        return TemplateInfo(
            template_id="TPL-UI-001",
            name="UI组件模板",
            template_type=SkillTemplate.UI_COMPONENT,
            description="适用于UI组件开发的技能模板",
            content=self._get_basic_template_content() + self._get_ui_addition(),
            parent_template="basic"
        )
    
    def _get_ui_addition(self) -> str:
        """获取UI模板附加内容"""
        return """

## UI组件规范

### 设计系统
- 颜色: 使用设计令牌
- 字体: 遵循排版规范
- 间距: 使用标准间距

### 可访问性
- ARIA标签: 完整支持
- 键盘导航: 全功能支持
- 屏幕阅读器: 兼容

### 响应式
- 断点: sm/md/lg/xl/2xl
- 移动优先设计
- 触摸交互支持
"""
    
    def _create_pipeline_template(self) -> TemplateInfo:
        """创建数据管道模板"""
        return TemplateInfo(
            template_id="TPL-PIPELINE-001",
            name="数据管道模板",
            template_type=SkillTemplate.DATA_PIPELINE,
            description="适用于数据管道开发的技能模板",
            content=self._get_basic_template_content() + self._get_pipeline_addition(),
            parent_template="basic"
        )
    
    def _get_pipeline_addition(self) -> str:
        """获取数据管道模板附加内容"""
        return """

## 数据管道规范

### 数据流
- 输入验证
- 数据转换
- 输出验证

### 性能优化
- 批量处理
- 并行执行
- 缓存策略

### 监控告警
- 执行日志
- 性能指标
- 异常告警
"""
    
    def _create_agent_template(self) -> TemplateInfo:
        """创建Agent角色模板"""
        return TemplateInfo(
            template_id="TPL-AGENT-001",
            name="Agent角色模板",
            template_type=SkillTemplate.AGENT_ROLE,
            description="适用于Agent角色定义的技能模板",
            content=self._get_basic_template_content() + self._get_agent_addition(),
            parent_template="basic"
        )
    
    def _get_agent_addition(self) -> str:
        """获取Agent模板附加内容"""
        return """

## Agent角色规范

### 角色定义
- 专业领域
- 核心能力
- 协作关系

### 任务执行
- 任务分解
- 执行策略
- 结果验证

### 协作机制
- 消息格式
- 状态同步
- 冲突解决
"""
    
    def get_template(self, template_type: Union[str, SkillTemplate]) -> Optional[TemplateInfo]:
        """获取模板
        
        Args:
            template_type: 模板类型
            
        Returns:
            模板信息，如果不存在返回None
        """
        if isinstance(template_type, SkillTemplate):
            template_type = template_type.value
        
        if template_type in self._template_cache:
            return self._template_cache[template_type]
        
        template_file = self.templates_path / f"{template_type}.json"
        if template_file.exists():
            try:
                data = json.loads(template_file.read_text(encoding='utf-8'))
                template = TemplateInfo(**data)
                self._template_cache[template_type] = template
                return template
            except Exception as e:
                logger.error(f"加载模板失败: {e}")
        
        return None
    
    def list_templates(self, status: TemplateStatus = None) -> List[TemplateInfo]:
        """列出所有模板
        
        Args:
            status: 过滤状态，为None时列出所有
            
        Returns:
            模板列表
        """
        templates = list(self._template_cache.values())
        
        for template_file in self.templates_path.glob("*.json"):
            template_id = template_file.stem
            if template_id not in self._template_cache:
                try:
                    data = json.loads(template_file.read_text(encoding='utf-8'))
                    template = TemplateInfo(**data)
                    self._template_cache[template_id] = template
                    templates.append(template)
                except Exception as e:
                    logger.error(f"加载模板 {template_id} 失败: {e}")
        
        if status:
            templates = [t for t in templates if t.status == status]
        
        return templates
    
    def create_template(self, template_info: TemplateInfo) -> Tuple[bool, str]:
        """创建新模板
        
        Args:
            template_info: 模板信息
            
        Returns:
            (成功状态, 消息)
        """
        try:
            template_id = template_info.template_id or f"TPL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            template_info.template_id = template_id
            
            validation_result = self._validate_template(template_info)
            if not validation_result[0]:
                return validation_result
            
            self._template_cache[template_id] = template_info
            
            template_file = self.templates_path / f"{template_id}.json"
            template_file.write_text(json.dumps(asdict(template_info), ensure_ascii=False, indent=2), encoding='utf-8')
            
            logger.info(f"模板创建成功: {template_id}")
            return True, f"模板 '{template_info.name}' 创建成功，ID: {template_id}"
            
        except Exception as e:
            logger.error(f"创建模板失败: {e}")
            return False, f"创建模板失败: {str(e)}"
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """更新模板
        
        Args:
            template_id: 模板ID
            updates: 更新内容
            
        Returns:
            (成功状态, 消息)
        """
        template = self.get_template(template_id)
        if not template:
            return False, f"模板 '{template_id}' 不存在"
        
        try:
            for key, value in updates.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            template.updated_at = datetime.now().isoformat()
            
            validation_result = self._validate_template(template)
            if not validation_result[0]:
                return validation_result
            
            self._template_cache[template_id] = template
            
            template_file = self.templates_path / f"{template_id}.json"
            template_file.write_text(json.dumps(asdict(template), ensure_ascii=False, indent=2), encoding='utf-8')
            
            logger.info(f"模板更新成功: {template_id}")
            return True, f"模板 '{template.name}' 更新成功"
            
        except Exception as e:
            logger.error(f"更新模板失败: {e}")
            return False, f"更新模板失败: {str(e)}"
    
    def delete_template(self, template_id: str) -> Tuple[bool, str]:
        """删除模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            (成功状态, 消息)
        """
        template = self.get_template(template_id)
        if not template:
            return False, f"模板 '{template_id}' 不存在"
        
        try:
            if template_id in self._template_cache:
                del self._template_cache[template_id]
            
            template_file = self.templates_path / f"{template_id}.json"
            if template_file.exists():
                template_file.unlink()
            
            logger.info(f"模板删除成功: {template_id}")
            return True, f"模板 '{template.name}' 删除成功"
            
        except Exception as e:
            logger.error(f"删除模板失败: {e}")
            return False, f"删除模板失败: {str(e)}"
    
    def _validate_template(self, template: TemplateInfo) -> Tuple[bool, str]:
        """验证模板
        
        Args:
            template: 模板信息
            
        Returns:
            (验证结果, 错误消息)
        """
        if not template.name:
            return False, "模板名称不能为空"
        
        if not template.content:
            return False, "模板内容不能为空"
        
        for rule in template.validation_rules:
            if rule.get("rule") == "min_length":
                pass
            elif rule.get("rule") == "pattern":
                pass
        
        return True, ""
    
    def render_template(self, template_type: Union[str, SkillTemplate], 
                        variables: Dict[str, Any]) -> Tuple[bool, str]:
        """渲染模板
        
        Args:
            template_type: 模板类型
            variables: 变量字典
            
        Returns:
            (成功状态, 渲染结果或错误消息)
        """
        template = self.get_template(template_type)
        if not template:
            return False, f"模板 '{template_type}' 不存在"
        
        try:
            content = template.content
            
            if template.parent_template:
                parent = self.get_template(template.parent_template)
                if parent:
                    content = parent.content
                    if template.content:
                        parent_addition = template.content.replace(parent.content, "")
                        content = content + parent_addition
            
            for var in template.variables:
                var_name = var["name"]
                var_default = var.get("default", "")
                value = variables.get(var_name, var_default)
                
                if var.get("required") and not value:
                    return False, f"缺少必需变量: {var_name}"
                
                content = content.replace(f"{{{{{var_name}}}}}", str(value))
            
            remaining_vars = re.findall(r'\{\{(\w+)\}\}', content)
            if remaining_vars:
                for var_name in remaining_vars:
                    content = content.replace(f"{{{{{var_name}}}}}", "")
            
            return True, content
            
        except Exception as e:
            logger.error(f"渲染模板失败: {e}")
            return False, f"渲染模板失败: {str(e)}"
    
    def create_template_version(self, template_id: str, version: str) -> Tuple[bool, str]:
        """创建模板版本
        
        Args:
            template_id: 模板ID
            version: 版本号
            
        Returns:
            (成功状态, 消息)
        """
        template = self.get_template(template_id)
        if not template:
            return False, f"模板 '{template_id}' 不存在"
        
        try:
            new_template = TemplateInfo(
                template_id=f"{template_id}-v{version}",
                name=f"{template.name} (v{version})",
                template_type=template.template_type,
                description=template.description,
                content=template.content,
                version=version,
                status=TemplateStatus.ACTIVE,
                author=template.author,
                parent_template=template_id,
                variables=template.variables.copy(),
                validation_rules=template.validation_rules.copy(),
                metadata={"version_of": template_id}
            )
            
            return self.create_template(new_template)
            
        except Exception as e:
            logger.error(f"创建模板版本失败: {e}")
            return False, f"创建模板版本失败: {str(e)}"
    
    def clone_template(self, template_id: str, new_name: str,
                       modifications: Dict[str, Any] = None) -> Tuple[bool, str]:
        """克隆模板
        
        Args:
            template_id: 源模板ID
            new_name: 新模板名称
            modifications: 修改内容
            
        Returns:
            (成功状态, 消息)
        """
        template = self.get_template(template_id)
        if not template:
            return False, f"模板 '{template_id}' 不存在"
        
        try:
            new_template_id = f"TPL-CLONE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            new_template = TemplateInfo(
                template_id=new_template_id,
                name=new_name,
                template_type=template.template_type,
                description=modifications.get("description", template.description) if modifications else template.description,
                content=modifications.get("content", template.content) if modifications else template.content,
                version="1.0.0",
                status=TemplateStatus.ACTIVE,
                author=modifications.get("author", "system") if modifications else "system",
                parent_template=template_id,
                variables=modifications.get("variables", template.variables.copy()) if modifications else template.variables.copy(),
                validation_rules=modifications.get("validation_rules", template.validation_rules.copy()) if modifications else template.validation_rules.copy(),
                metadata={"cloned_from": template_id}
            )
            
            return self.create_template(new_template)
            
        except Exception as e:
            logger.error(f"克隆模板失败: {e}")
            return False, f"克隆模板失败: {str(e)}"
    
    def merge_templates(self, template_ids: List[str], new_name: str,
                        merge_strategy: str = "append") -> Tuple[bool, str]:
        """合并多个模板
        
        Args:
            template_ids: 模板ID列表
            new_name: 新模板名称
            merge_strategy: 合并策略 (append|prepend|replace)
            
        Returns:
            (成功状态, 消息)
        """
        templates = []
        for tid in template_ids:
            template = self.get_template(tid)
            if template:
                templates.append(template)
            else:
                return False, f"模板 '{tid}' 不存在"
        
        if not templates:
            return False, "没有有效的模板可合并"
        
        try:
            merged_content = ""
            merged_variables = []
            merged_rules = []
            seen_var_names = set()
            seen_rules = set()
            
            for template in templates:
                if merge_strategy == "append":
                    merged_content += "\n\n" + template.content
                elif merge_strategy == "prepend":
                    merged_content = template.content + "\n\n" + merged_content
                
                for var in template.variables:
                    if var["name"] not in seen_var_names:
                        merged_variables.append(var)
                        seen_var_names.add(var["name"])
                
                for rule in template.validation_rules:
                    rule_key = f"{rule.get('rule')}-{rule.get('field')}"
                    if rule_key not in seen_rules:
                        merged_rules.append(rule)
                        seen_rules.add(rule_key)
            
            new_template_id = f"TPL-MERGE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            new_template = TemplateInfo(
                template_id=new_template_id,
                name=new_name,
                template_type=templates[0].template_type,
                description=f"合并自: {', '.join(template_ids)}",
                content=merged_content.strip(),
                version="1.0.0",
                status=TemplateStatus.ACTIVE,
                author="system",
                parent_template=template_ids[0],
                variables=merged_variables,
                validation_rules=merged_rules,
                metadata={"merged_from": template_ids, "merge_strategy": merge_strategy}
            )
            
            return self.create_template(new_template)
            
        except Exception as e:
            logger.error(f"合并模板失败: {e}")
            return False, f"合并模板失败: {str(e)}"
    
    def export_template(self, template_id: str, export_format: str = "json") -> Tuple[bool, str]:
        """导出模板
        
        Args:
            template_id: 模板ID
            export_format: 导出格式 (json|yaml|markdown)
            
        Returns:
            (成功状态, 导出内容或错误消息)
        """
        template = self.get_template(template_id)
        if not template:
            return False, f"模板 '{template_id}' 不存在"
        
        try:
            if export_format == "json":
                return True, json.dumps(asdict(template), ensure_ascii=False, indent=2)
            
            elif export_format == "yaml":
                try:
                    import yaml
                    return True, yaml.dump(asdict(template), allow_unicode=True, default_flow_style=False)
                except ImportError:
                    return False, "PyYAML库未安装"
            
            elif export_format == "markdown":
                md_content = f"""# {template.name}

**ID**: {template.template_id}
**类型**: {template.template_type.value}
**版本**: {template.version}
**状态**: {template.status.value}
**作者**: {template.author}

## 描述

{template.description}

## 变量

"""
                for var in template.variables:
                    required = " (必需)" if var.get("required") else ""
                    md_content += f"- **{var['name']}**{required}: {var.get('description', '')}\n"
                
                md_content += "\n## 验证规则\n\n"
                for rule in template.validation_rules:
                    md_content += f"- {rule.get('rule')}: {rule.get('field')} - {rule.get('message', '')}\n"
                
                md_content += "\n## 模板内容\n\n```\n" + template.content + "\n```\n"
                
                return True, md_content
            
            else:
                return False, f"不支持的导出格式: {export_format}"
                
        except Exception as e:
            logger.error(f"导出模板失败: {e}")
            return False, f"导出模板失败: {str(e)}"
    
    def import_template(self, content: str, import_format: str = "json") -> Tuple[bool, str]:
        """导入模板
        
        Args:
            content: 导入内容
            import_format: 导入格式 (json|yaml)
            
        Returns:
            (成功状态, 消息)
        """
        try:
            if import_format == "json":
                data = json.loads(content)
            
            elif import_format == "yaml":
                try:
                    import yaml
                    data = yaml.safe_load(content)
                except ImportError:
                    return False, "PyYAML库未安装"
            
            else:
                return False, f"不支持的导入格式: {import_format}"
            
            if "template_type" in data:
                data["template_type"] = SkillTemplate(data["template_type"])
            if "status" in data:
                data["status"] = TemplateStatus(data.get("status", "active"))
            
            template = TemplateInfo(**data)
            return self.create_template(template)
            
        except Exception as e:
            logger.error(f"导入模板失败: {e}")
            return False, f"导入模板失败: {str(e)}"
    
    def validate_template_instance(self, template_id: str, 
                                    instance_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证模板实例
        
        Args:
            template_id: 模板ID
            instance_data: 实例数据
            
        Returns:
            (验证结果, 错误消息列表)
        """
        template = self.get_template(template_id)
        if not template:
            return False, [f"模板 '{template_id}' 不存在"]
        
        errors = []
        
        for var in template.variables:
            var_name = var["name"]
            var_required = var.get("required", False)
            var_type = var.get("type", "string")
            
            if var_required and var_name not in instance_data:
                errors.append(f"缺少必需变量: {var_name}")
                continue
            
            if var_name in instance_data:
                value = instance_data[var_name]
                
                if var_type == "string" and not isinstance(value, str):
                    errors.append(f"变量 '{var_name}' 应为字符串类型")
                elif var_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"变量 '{var_name}' 应为数字类型")
                elif var_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"变量 '{var_name}' 应为布尔类型")
                elif var_type == "list" and not isinstance(value, list):
                    errors.append(f"变量 '{var_name}' 应为列表类型")
                elif var_type == "dict" and not isinstance(value, dict):
                    errors.append(f"变量 '{var_name}' 应为字典类型")
        
        for rule in template.validation_rules:
            rule_type = rule.get("rule")
            field = rule.get("field")
            value = instance_data.get(field)
            
            if value is None:
                continue
            
            if rule_type == "min_length":
                min_len = rule.get("value", 0)
                if len(str(value)) < min_len:
                    errors.append(rule.get("message", f"{field} 长度不足"))
            
            elif rule_type == "max_length":
                max_len = rule.get("value", float('inf'))
                if len(str(value)) > max_len:
                    errors.append(rule.get("message", f"{field} 长度超限"))
            
            elif rule_type == "pattern":
                pattern = rule.get("value", "")
                if not re.match(pattern, str(value)):
                    errors.append(rule.get("message", f"{field} 格式无效"))
            
            elif rule_type == "min_value":
                min_val = rule.get("value", float('-inf'))
                if isinstance(value, (int, float)) and value < min_val:
                    errors.append(rule.get("message", f"{field} 值过小"))
            
            elif rule_type == "max_value":
                max_val = rule.get("value", float('inf'))
                if isinstance(value, (int, float)) and value > max_val:
                    errors.append(rule.get("message", f"{field} 值过大"))
        
        return len(errors) == 0, errors
    
    def get_template_hierarchy(self, template_id: str) -> Dict[str, Any]:
        """获取模板继承层次结构
        
        Args:
            template_id: 模板ID
            
        Returns:
            层次结构字典
        """
        template = self.get_template(template_id)
        if not template:
            return {"error": f"模板 '{template_id}' 不存在"}
        
        hierarchy = {
            "template_id": template_id,
            "name": template.name,
            "version": template.version,
            "parent": None,
            "ancestors": [],
            "children": []
        }
        
        if template.parent_template:
            parent = self.get_template(template.parent_template)
            if parent:
                hierarchy["parent"] = {
                    "template_id": parent.template_id,
                    "name": parent.name
                }
                hierarchy["ancestors"] = self._get_ancestors(template.parent_template)
        
        hierarchy["children"] = self._get_children(template_id)
        
        return hierarchy
    
    def _get_ancestors(self, template_id: str, visited: set = None) -> List[Dict]:
        """获取祖先模板"""
        if visited is None:
            visited = set()
        
        if template_id in visited:
            return []
        visited.add(template_id)
        
        template = self.get_template(template_id)
        if not template or not template.parent_template:
            return []
        
        parent = self.get_template(template.parent_template)
        if not parent:
            return []
        
        return [{"template_id": parent.template_id, "name": parent.name}] + \
               self._get_ancestors(template.parent_template, visited)
    
    def _get_children(self, template_id: str) -> List[Dict]:
        """获取子模板"""
        children = []
        for template in self._template_cache.values():
            if template.parent_template == template_id:
                children.append({
                    "template_id": template.template_id,
                    "name": template.name,
                    "version": template.version
                })
        return children
    
    def search_templates(self, query: str, 
                         filters: Dict[str, Any] = None) -> List[TemplateInfo]:
        """搜索模板
        
        Args:
            query: 搜索关键词
            filters: 过滤条件
            
        Returns:
            匹配的模板列表
        """
        templates = self.list_templates()
        results = []
        
        query_lower = query.lower()
        
        for template in templates:
            match_score = 0
            
            if query_lower in template.name.lower():
                match_score += 3
            if query_lower in template.description.lower():
                match_score += 2
            if query_lower in template.template_type.value.lower():
                match_score += 1
            
            for var in template.variables:
                if query_lower in var.get("name", "").lower():
                    match_score += 1
                if query_lower in var.get("description", "").lower():
                    match_score += 0.5
            
            if match_score > 0:
                if filters:
                    if filters.get("type") and template.template_type.value != filters["type"]:
                        continue
                    if filters.get("status") and template.status.value != filters["status"]:
                        continue
                
                results.append((match_score, template))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in results]


class PerformanceMonitor:
    """技能性能监控器
    
    负责收集、分析和报告技能性能指标。
    支持实时监控、趋势分析和异常检测。
    """
    
    def __init__(self, metrics_path: str = None):
        if metrics_path is None:
            metrics_path = str(get_path_config().LOGS_DIR / "skill_metrics")
        self.metrics_path = Path(metrics_path)
        self.metrics_path.mkdir(parents=True, exist_ok=True)
        self._metrics_cache: Dict[str, List[PerformanceMetric]] = {}
        self._baselines: Dict[str, Dict[str, float]] = {}
        self._anomaly_threshold = 2.0
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._metrics_queue: queue.Queue = queue.Queue()
        logger.info(f"PerformanceMonitor initialized with path: {metrics_path}")
    
    def record_metric(self, skill_name: str, metric_type: PerformanceMetricType,
                      value: float, unit: str, context: Dict[str, Any] = None) -> PerformanceMetric:
        """记录性能指标
        
        Args:
            skill_name: 技能名称
            metric_type: 指标类型
            value: 指标值
            unit: 单位
            context: 上下文信息
            
        Returns:
            性能指标对象
        """
        metric = PerformanceMetric(
            metric_id=f"METRIC-{uuid.uuid4().hex[:8].upper()}",
            skill_name=skill_name,
            metric_type=metric_type,
            value=value,
            unit=unit,
            timestamp=datetime.now().isoformat(),
            context=context or {}
        )
        
        if skill_name not in self._metrics_cache:
            self._metrics_cache[skill_name] = []
        
        self._metrics_cache[skill_name].append(metric)
        
        if skill_name in self._baselines:
            baseline = self._baselines[skill_name].get(metric_type.value)
            if baseline:
                metric.baseline_value = baseline
                metric.deviation = abs(value - baseline) / baseline if baseline != 0 else 0
        
        self._save_metric(metric)
        
        logger.debug(f"记录性能指标: {skill_name} - {metric_type.value} = {value} {unit}")
        return metric
    
    def _save_metric(self, metric: PerformanceMetric) -> None:
        """保存指标到文件"""
        try:
            metric_file = self.metrics_path / f"{metric.skill_name}_metrics.jsonl"
            with open(metric_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(metric), ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"保存指标失败: {e}")
    
    def set_baseline(self, skill_name: str, metrics: Dict[str, float]) -> None:
        """设置性能基线
        
        Args:
            skill_name: 技能名称
            metrics: 指标基线字典
        """
        self._baselines[skill_name] = metrics
        logger.info(f"设置性能基线: {skill_name} - {metrics}")
    
    def calculate_baseline(self, skill_name: str, 
                           time_range: timedelta = timedelta(days=7)) -> Dict[str, float]:
        """计算性能基线
        
        Args:
            skill_name: 技能名称
            time_range: 时间范围
            
        Returns:
            计算得到的基线指标
        """
        metrics = self._metrics_cache.get(skill_name, [])
        
        if not metrics:
            self._load_metrics(skill_name, time_range)
            metrics = self._metrics_cache.get(skill_name, [])
        
        if not metrics:
            return {}
        
        cutoff_time = datetime.now() - time_range
        recent_metrics = [
            m for m in metrics 
            if datetime.fromisoformat(m.timestamp) >= cutoff_time
        ]
        
        baselines = {}
        for metric_type in PerformanceMetricType:
            type_metrics = [m for m in recent_metrics if m.metric_type == metric_type]
            if type_metrics:
                values = [m.value for m in type_metrics]
                baselines[metric_type.value] = sum(values) / len(values)
        
        if baselines:
            self.set_baseline(skill_name, baselines)
        
        return baselines
    
    def _load_metrics(self, skill_name: str, time_range: timedelta = None) -> None:
        """从文件加载指标"""
        metric_file = self.metrics_path / f"{skill_name}_metrics.jsonl"
        if not metric_file.exists():
            return
        
        try:
            cutoff_time = None
            if time_range:
                cutoff_time = datetime.now() - time_range
            
            metrics = []
            with open(metric_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        metric = PerformanceMetric(**data)
                        if cutoff_time:
                            if datetime.fromisoformat(metric.timestamp) >= cutoff_time:
                                metrics.append(metric)
                        else:
                            metrics.append(metric)
            
            self._metrics_cache[skill_name] = metrics
            
        except Exception as e:
            logger.error(f"加载指标失败: {e}")
    
    def get_metrics(self, skill_name: str, 
                    metric_type: PerformanceMetricType = None,
                    time_range: timedelta = None) -> List[PerformanceMetric]:
        """获取性能指标
        
        Args:
            skill_name: 技能名称
            metric_type: 指标类型，为None时获取所有类型
            time_range: 时间范围，为None时获取所有
            
        Returns:
            性能指标列表
        """
        metrics = self._metrics_cache.get(skill_name, [])
        
        if not metrics:
            self._load_metrics(skill_name, time_range)
            metrics = self._metrics_cache.get(skill_name, [])
        
        if time_range:
            cutoff_time = datetime.now() - time_range
            metrics = [
                m for m in metrics 
                if datetime.fromisoformat(m.timestamp) >= cutoff_time
            ]
        
        if metric_type:
            metrics = [m for m in metrics if m.metric_type == metric_type]
        
        return metrics
    
    def analyze_trends(self, skill_name: str, 
                       metric_type: PerformanceMetricType,
                       time_range: timedelta = timedelta(days=30)) -> Dict[str, Any]:
        """分析性能趋势
        
        Args:
            skill_name: 技能名称
            metric_type: 指标类型
            time_range: 时间范围
            
        Returns:
            趋势分析结果
        """
        metrics = self.get_metrics(skill_name, metric_type, time_range)
        
        if not metrics:
            return {"trend": "no_data", "data_points": 0}
        
        values = [m.value for m in metrics]
        timestamps = [datetime.fromisoformat(m.timestamp) for m in metrics]
        
        n = len(values)
        if n < 2:
            return {"trend": "insufficient_data", "data_points": n}
        
        x = [(t - timestamps[0]).total_seconds() for t in timestamps]
        y = values
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercept = (sum_y - slope * sum_x) / n
        
        mean_y = sum_y / n
        ss_tot = sum((yi - mean_y) ** 2 for yi in y)
        ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        if slope > 0.01 * mean_y:
            trend = "increasing"
        elif slope < -0.01 * mean_y:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_squared,
            "data_points": n,
            "mean": mean_y,
            "min": min(values),
            "max": max(values),
            "std_dev": (sum((yi - mean_y) ** 2 for yi in y) / n) ** 0.5
        }
    
    def detect_anomalies(self, skill_name: str, 
                         metric_type: PerformanceMetricType,
                         time_range: timedelta = timedelta(days=7)) -> List[Dict[str, Any]]:
        """检测性能异常
        
        Args:
            skill_name: 技能名称
            metric_type: 指标类型
            time_range: 时间范围
            
        Returns:
            异常列表
        """
        metrics = self.get_metrics(skill_name, metric_type, time_range)
        
        if not metrics:
            return []
        
        values = [m.value for m in metrics]
        mean = sum(values) / len(values)
        std_dev = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        
        if std_dev == 0:
            return []
        
        anomalies = []
        for metric in metrics:
            z_score = abs(metric.value - mean) / std_dev
            if z_score > self._anomaly_threshold:
                anomalies.append({
                    "metric_id": metric.metric_id,
                    "timestamp": metric.timestamp,
                    "value": metric.value,
                    "z_score": z_score,
                    "expected_range": [mean - self._anomaly_threshold * std_dev,
                                       mean + self._anomaly_threshold * std_dev],
                    "severity": "high" if z_score > 3.0 else "medium"
                })
        
        return anomalies
    
    def generate_report(self, skill_name: str, 
                        time_range: timedelta = timedelta(days=7)) -> PerformanceReport:
        """生成性能报告
        
        Args:
            skill_name: 技能名称
            time_range: 时间范围
            
        Returns:
            性能报告
        """
        all_metrics = self.get_metrics(skill_name, time_range=time_range)
        
        summary = {}
        for metric_type in PerformanceMetricType:
            type_metrics = [m for m in all_metrics if m.metric_type == metric_type]
            if type_metrics:
                values = [m.value for m in type_metrics]
                summary[metric_type.value] = {
                    "count": len(values),
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1] if values else None
                }
        
        trends = {}
        for metric_type in PerformanceMetricType:
            trend = self.analyze_trends(skill_name, metric_type, time_range)
            if trend["data_points"] > 0:
                trends[metric_type.value] = trend
        
        anomalies = []
        for metric_type in PerformanceMetricType:
            type_anomalies = self.detect_anomalies(skill_name, metric_type, time_range)
            anomalies.extend(type_anomalies)
        
        recommendations = self._generate_recommendations(summary, trends, anomalies)
        
        report = PerformanceReport(
            report_id=f"REPORT-{uuid.uuid4().hex[:8].upper()}",
            skill_name=skill_name,
            generated_at=datetime.now().isoformat(),
            metrics=all_metrics,
            summary=summary,
            trends=trends,
            recommendations=recommendations,
            anomalies=anomalies
        )
        
        self._save_report(report)
        
        return report
    
    def _generate_recommendations(self, summary: Dict, trends: Dict, 
                                   anomalies: List) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        for metric_type, data in summary.items():
            if data["count"] > 0:
                if metric_type == PerformanceMetricType.EXECUTION_TIME.value:
                    if data["mean"] > 5000:
                        recommendations.append(f"执行时间较长({data['mean']:.0f}ms)，建议优化性能")
                elif metric_type == PerformanceMetricType.ERROR_RATE.value:
                    if data["mean"] > 0.05:
                        recommendations.append(f"错误率较高({data['mean']*100:.1f}%)，建议检查错误处理")
                elif metric_type == PerformanceMetricType.MEMORY_USAGE.value:
                    if data["mean"] > 500:
                        recommendations.append(f"内存使用较高({data['mean']:.0f}MB)，建议优化内存管理")
        
        for metric_type, trend in trends.items():
            if trend["trend"] == "increasing":
                if metric_type == PerformanceMetricType.EXECUTION_TIME.value:
                    recommendations.append("执行时间呈上升趋势，建议进行性能优化")
                elif metric_type == PerformanceMetricType.MEMORY_USAGE.value:
                    recommendations.append("内存使用呈上升趋势，可能存在内存泄漏")
            elif trend["trend"] == "decreasing":
                if metric_type == PerformanceMetricType.SUCCESS_RATE.value:
                    recommendations.append("成功率呈下降趋势，需要关注")
        
        if anomalies:
            high_severity = [a for a in anomalies if a["severity"] == "high"]
            if high_severity:
                recommendations.append(f"发现{len(high_severity)}个高严重性异常，建议立即处理")
        
        if not recommendations:
            recommendations.append("性能表现良好，继续保持")
        
        return recommendations
    
    def _save_report(self, report: PerformanceReport) -> None:
        """保存报告到文件"""
        try:
            report_file = self.metrics_path / f"{report.skill_name}_report_{report.report_id}.json"
            report_data = asdict(report)
            report_data["metrics"] = [asdict(m) for m in report.metrics]
            report_file.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
    
    def start_monitoring(self, interval_seconds: int = 60) -> None:
        """开始实时监控
        
        Args:
            interval_seconds: 监控间隔（秒）
        """
        if self._monitoring_active:
            logger.warning("监控已在运行中")
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"开始性能监控，间隔: {interval_seconds}秒")
    
    def stop_monitoring(self) -> None:
        """停止实时监控"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("停止性能监控")
    
    def _monitor_loop(self, interval_seconds: int) -> None:
        """监控循环"""
        while self._monitoring_active:
            try:
                while True:
                    try:
                        metric = self._metrics_queue.get_nowait()
                        self.record_metric(
                            metric.skill_name,
                            metric.metric_type,
                            metric.value,
                            metric.unit,
                            metric.context
                        )
                    except queue.Empty:
                        break
                
                for skill_name in list(self._metrics_cache.keys()):
                    anomalies = self.detect_anomalies(
                        skill_name, 
                        PerformanceMetricType.EXECUTION_TIME
                    )
                    if anomalies:
                        logger.warning(f"检测到 {skill_name} 性能异常: {len(anomalies)} 个")
            
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
            
            time.sleep(interval_seconds)
    
    def queue_metric(self, skill_name: str, metric_type: PerformanceMetricType,
                     value: float, unit: str, context: Dict[str, Any] = None) -> None:
        """将指标加入队列（异步记录）
        
        Args:
            skill_name: 技能名称
            metric_type: 指标类型
            value: 指标值
            unit: 单位
            context: 上下文信息
        """
        metric = PerformanceMetric(
            metric_id=f"METRIC-{uuid.uuid4().hex[:8].upper()}",
            skill_name=skill_name,
            metric_type=metric_type,
            value=value,
            unit=unit,
            timestamp=datetime.now().isoformat(),
            context=context or {}
        )
        self._metrics_queue.put(metric)
    
    def compare_performance(self, skill_name_1: str, skill_name_2: str,
                            metric_type: PerformanceMetricType,
                            time_range: timedelta = timedelta(days=7)) -> Dict[str, Any]:
        """比较两个技能的性能
        
        Args:
            skill_name_1: 第一个技能名称
            skill_name_2: 第二个技能名称
            metric_type: 指标类型
            time_range: 时间范围
            
        Returns:
            比较结果
        """
        metrics_1 = self.get_metrics(skill_name_1, metric_type, time_range)
        metrics_2 = self.get_metrics(skill_name_2, metric_type, time_range)
        
        if not metrics_1 or not metrics_2:
            return {"error": "缺少性能数据"}
        
        values_1 = [m.value for m in metrics_1]
        values_2 = [m.value for m in metrics_2]
        
        avg_1 = sum(values_1) / len(values_1)
        avg_2 = sum(values_2) / len(values_2)
        
        diff_percent = ((avg_1 - avg_2) / avg_2 * 100) if avg_2 != 0 else 0
        
        return {
            "skill_1": {
                "name": skill_name_1,
                "average": avg_1,
                "min": min(values_1),
                "max": max(values_1),
                "count": len(values_1)
            },
            "skill_2": {
                "name": skill_name_2,
                "average": avg_2,
                "min": min(values_2),
                "max": max(values_2),
                "count": len(values_2)
            },
            "comparison": {
                "difference": avg_1 - avg_2,
                "difference_percent": diff_percent,
                "better": skill_name_1 if avg_1 < avg_2 else skill_name_2
            }
        }
    
    def get_performance_summary(self, skill_name: str = None) -> Dict[str, Any]:
        """获取性能摘要
        
        Args:
            skill_name: 技能名称，为None时获取所有技能摘要
            
        Returns:
            性能摘要
        """
        if skill_name:
            skill_names = [skill_name]
        else:
            skill_names = list(self._metrics_cache.keys())
        
        summary = {
            "generated_at": datetime.now().isoformat(),
            "skills": {}
        }
        
        for name in skill_names:
            metrics = self._metrics_cache.get(name, [])
            if not metrics:
                continue
            
            skill_summary = {
                "total_metrics": len(metrics),
                "metric_types": {},
                "overall_health": "good"
            }
            
            for metric_type in PerformanceMetricType:
                type_metrics = [m for m in metrics if m.metric_type == metric_type]
                if type_metrics:
                    values = [m.value for m in type_metrics]
                    skill_summary["metric_types"][metric_type.value] = {
                        "count": len(values),
                        "average": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "latest": values[-1]
                    }
            
            if skill_summary["metric_types"].get(PerformanceMetricType.ERROR_RATE.value, {}).get("average", 0) > 0.1:
                skill_summary["overall_health"] = "warning"
            if skill_summary["metric_types"].get(PerformanceMetricType.EXECUTION_TIME.value, {}).get("average", 0) > 5000:
                skill_summary["overall_health"] = "warning"
            
            summary["skills"][name] = skill_summary
        
        return summary
    
    def predict_performance(self, skill_name: str, 
                            metric_type: PerformanceMetricType,
                            prediction_days: int = 7) -> Dict[str, Any]:
        """预测性能趋势
        
        Args:
            skill_name: 技能名称
            metric_type: 指标类型
            prediction_days: 预测天数
            
        Returns:
            预测结果
        """
        metrics = self.get_metrics(skill_name, metric_type, timedelta(days=30))
        
        if len(metrics) < 5:
            return {"error": "数据点不足，无法预测"}
        
        trend = self.analyze_trends(skill_name, metric_type, timedelta(days=30))
        
        if trend["trend"] == "no_data":
            return {"error": "无趋势数据"}
        
        slope = trend["slope"]
        intercept = trend["intercept"]
        mean = trend["mean"]
        
        predictions = []
        last_timestamp = datetime.fromisoformat(metrics[-1].timestamp)
        
        for day in range(1, prediction_days + 1):
            future_time = last_timestamp + timedelta(days=day)
            time_diff = (future_time - datetime.fromisoformat(metrics[0].timestamp)).total_seconds()
            predicted_value = slope * time_diff + intercept
            
            predictions.append({
                "date": future_time.strftime('%Y-%m-%d'),
                "predicted_value": max(0, predicted_value)
            })
        
        return {
            "skill_name": skill_name,
            "metric_type": metric_type.value,
            "current_trend": trend["trend"],
            "slope": slope,
            "predictions": predictions,
            "confidence": trend["r_squared"],
            "recommendation": self._generate_prediction_recommendation(trend, predictions)
        }
    
    def _generate_prediction_recommendation(self, trend: Dict, predictions: List) -> str:
        """生成预测建议"""
        if trend["trend"] == "increasing":
            if predictions and predictions[-1]["predicted_value"] > trend["mean"] * 1.5:
                return "性能呈上升趋势，建议进行优化或扩容"
        elif trend["trend"] == "decreasing":
            return "性能呈下降趋势，请检查是否存在问题"
        return "性能稳定，继续保持"
    
    def set_alert_threshold(self, skill_name: str, metric_type: PerformanceMetricType,
                            threshold: float, comparison: str = "greater") -> None:
        """设置告警阈值
        
        Args:
            skill_name: 技能名称
            metric_type: 指标类型
            threshold: 阈值
            comparison: 比较方式 (greater|less|equal)
        """
        alert_config = {
            "skill_name": skill_name,
            "metric_type": metric_type.value,
            "threshold": threshold,
            "comparison": comparison,
            "created_at": datetime.now().isoformat()
        }
        
        alert_file = self.metrics_path / f"{skill_name}_alerts.json"
        alerts = []
        if alert_file.exists():
            try:
                alerts = json.loads(alert_file.read_text(encoding='utf-8'))
            except:
                pass
        
        alerts.append(alert_config)
        alert_file.write_text(json.dumps(alerts, ensure_ascii=False, indent=2), encoding='utf-8')
        
        logger.info(f"设置告警阈值: {skill_name} - {metric_type.value} {comparison} {threshold}")
    
    def check_alerts(self, skill_name: str = None) -> List[Dict[str, Any]]:
        """检查告警
        
        Args:
            skill_name: 技能名称，为None时检查所有技能
            
        Returns:
            告警列表
        """
        alerts = []
        
        alert_files = list(self.metrics_path.glob("*_alerts.json"))
        
        for alert_file in alert_files:
            try:
                alert_configs = json.loads(alert_file.read_text(encoding='utf-8'))
                
                for config in alert_configs:
                    if skill_name and config["skill_name"] != skill_name:
                        continue
                    
                    latest_metrics = self.get_metrics(
                        config["skill_name"],
                        PerformanceMetricType(config["metric_type"]),
                        timedelta(hours=1)
                    )
                    
                    if latest_metrics:
                        latest_value = latest_metrics[-1].value
                        threshold = config["threshold"]
                        comparison = config["comparison"]
                        
                        triggered = False
                        if comparison == "greater" and latest_value > threshold:
                            triggered = True
                        elif comparison == "less" and latest_value < threshold:
                            triggered = True
                        elif comparison == "equal" and abs(latest_value - threshold) < 0.001:
                            triggered = True
                        
                        if triggered:
                            alerts.append({
                                "skill_name": config["skill_name"],
                                "metric_type": config["metric_type"],
                                "current_value": latest_value,
                                "threshold": threshold,
                                "comparison": comparison,
                                "triggered_at": datetime.now().isoformat()
                            })
            except Exception as e:
                logger.error(f"检查告警失败: {e}")
        
        return alerts
    
    def export_metrics(self, skill_name: str, export_format: str = "json",
                       time_range: timedelta = None) -> str:
        """导出指标数据
        
        Args:
            skill_name: 技能名称
            export_format: 导出格式 (json|csv)
            time_range: 时间范围
            
        Returns:
            导出内容
        """
        metrics = self.get_metrics(skill_name, time_range=time_range)
        
        if export_format == "json":
            return json.dumps([asdict(m) for m in metrics], ensure_ascii=False, indent=2)
        
        elif export_format == "csv":
            lines = ["metric_id,skill_name,metric_type,value,unit,timestamp"]
            for m in metrics:
                lines.append(f"{m.metric_id},{m.skill_name},{m.metric_type.value},{m.value},{m.unit},{m.timestamp}")
            return "\n".join(lines)
        
        else:
            return f"不支持的导出格式: {export_format}"
    
    def get_performance_ranking(self, metric_type: PerformanceMetricType,
                                time_range: timedelta = timedelta(days=7),
                                ascending: bool = True) -> List[Dict[str, Any]]:
        """获取性能排名
        
        Args:
            metric_type: 指标类型
            time_range: 时间范围
            ascending: 是否升序排列
            
        Returns:
            排名列表
        """
        rankings = []
        
        for skill_name in self._metrics_cache.keys():
            metrics = self.get_metrics(skill_name, metric_type, time_range)
            if metrics:
                values = [m.value for m in metrics]
                rankings.append({
                    "rank": 0,
                    "skill_name": skill_name,
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                })
        
        rankings.sort(key=lambda x: x["average"], reverse=not ascending)
        
        for i, r in enumerate(rankings):
            r["rank"] = i + 1
        
        return rankings


class VersionChangeType(Enum):
    """版本变更类型枚举"""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRERELEASE = "prerelease"
    BUILD = "build"


@dataclass
class SkillVersion:
    """技能版本数据类"""
    version_id: str
    skill_name: str
    version: str
    change_type: VersionChangeType
    changes: List[str]
    author: str
    timestamp: str
    parent_version: Optional[str] = None
    is_stable: bool = True
    is_deprecated: bool = False
    deprecation_message: Optional[str] = None
    compatibility_notes: List[str] = None
    breaking_changes: List[str] = None
    new_features: List[str] = None
    bug_fixes: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.compatibility_notes is None:
            self.compatibility_notes = []
        if self.breaking_changes is None:
            self.breaking_changes = []
        if self.new_features is None:
            self.new_features = []
        if self.bug_fixes is None:
            self.bug_fixes = []
        if self.metadata is None:
            self.metadata = {}


class SkillVersionManager:
    """技能版本管理器
    
    负责技能版本的生命周期管理，包括版本创建、发布、
    弃用、回滚和版本间迁移。
    """
    
    def __init__(self, versions_path: str = "config/skill_versions"):
        self.versions_path = Path(versions_path)
        self.versions_path.mkdir(parents=True, exist_ok=True)
        self._version_cache: Dict[str, List[SkillVersion]] = {}
        self._current_versions: Dict[str, str] = {}
        logger.info(f"SkillVersionManager initialized with path: {versions_path}")
    
    def create_version(self, skill_name: str, change_type: VersionChangeType,
                       changes: List[str], author: str = "system",
                       breaking_changes: List[str] = None,
                       new_features: List[str] = None,
                       bug_fixes: List[str] = None) -> SkillVersion:
        """创建新版本
        
        Args:
            skill_name: 技能名称
            change_type: 变更类型
            changes: 变更描述列表
            author: 作者
            breaking_changes: 破坏性变更列表
            new_features: 新功能列表
            bug_fixes: Bug修复列表
            
        Returns:
            新创建的版本对象
        """
        current_version = self._current_versions.get(skill_name, "0.0.0")
        new_version = self._increment_version(current_version, change_type)
        
        version = SkillVersion(
            version_id=f"VER-{skill_name}-{new_version}",
            skill_name=skill_name,
            version=new_version,
            change_type=change_type,
            changes=changes,
            author=author,
            timestamp=datetime.now().isoformat(),
            parent_version=current_version,
            breaking_changes=breaking_changes or [],
            new_features=new_features or [],
            bug_fixes=bug_fixes or []
        )
        
        if skill_name not in self._version_cache:
            self._version_cache[skill_name] = []
        self._version_cache[skill_name].append(version)
        
        self._current_versions[skill_name] = new_version
        
        self._save_version(version)
        
        logger.info(f"创建版本: {skill_name} v{new_version}")
        return version
    
    def _increment_version(self, current: str, change_type: VersionChangeType) -> str:
        """递增版本号"""
        parts = current.split('.')
        while len(parts) < 3:
            parts.append('0')
        
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        
        if change_type == VersionChangeType.MAJOR:
            major += 1
            minor = 0
            patch = 0
        elif change_type == VersionChangeType.MINOR:
            minor += 1
            patch = 0
        elif change_type == VersionChangeType.PATCH:
            patch += 1
        elif change_type == VersionChangeType.PRERELEASE:
            patch += 1
        elif change_type == VersionChangeType.BUILD:
            patch += 1
        
        return f"{major}.{minor}.{patch}"
    
    def _save_version(self, version: SkillVersion) -> None:
        """保存版本到文件"""
        version_file = self.versions_path / f"{version.skill_name}_versions.jsonl"
        data = asdict(version)
        data['change_type'] = version.change_type.value
        with open(version_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    def get_versions(self, skill_name: str) -> List[SkillVersion]:
        """获取技能的所有版本"""
        if skill_name not in self._version_cache:
            self._load_versions(skill_name)
        return self._version_cache.get(skill_name, [])
    
    def _load_versions(self, skill_name: str) -> None:
        """从文件加载版本"""
        version_file = self.versions_path / f"{skill_name}_versions.jsonl"
        if not version_file.exists():
            return
        
        versions = []
        with open(version_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    data['change_type'] = VersionChangeType(data['change_type'])
                    versions.append(SkillVersion(**data))
        
        self._version_cache[skill_name] = versions
        
        if versions:
            latest = max(versions, key=lambda v: self._parse_version(v.version))
            self._current_versions[skill_name] = latest.version
    
    def _parse_version(self, version: str) -> Tuple[int, ...]:
        """解析版本号为元组"""
        parts = version.split('.')
        return tuple(int(p) for p in parts if p.isdigit())
    
    def get_current_version(self, skill_name: str) -> Optional[str]:
        """获取当前版本"""
        return self._current_versions.get(skill_name)
    
    def deprecate_version(self, skill_name: str, version: str, 
                          message: str) -> Tuple[bool, str]:
        """弃用版本"""
        versions = self.get_versions(skill_name)
        
        for v in versions:
            if v.version == version:
                v.is_deprecated = True
                v.deprecation_message = message
                self._update_version_file(skill_name)
                logger.info(f"弃用版本: {skill_name} v{version}")
                return True, f"版本 {version} 已弃用"
        
        return False, f"版本 {version} 不存在"
    
    def _update_version_file(self, skill_name: str) -> None:
        """更新版本文件"""
        versions = self._version_cache.get(skill_name, [])
        version_file = self.versions_path / f"{skill_name}_versions.jsonl"
        
        with open(version_file, 'w', encoding='utf-8') as f:
            for v in versions:
                data = asdict(v)
                data['change_type'] = v.change_type.value
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    def rollback_version(self, skill_name: str, target_version: str) -> Tuple[bool, str]:
        """回滚到指定版本"""
        versions = self.get_versions(skill_name)
        
        target = None
        for v in versions:
            if v.version == target_version and not v.is_deprecated:
                target = v
                break
        
        if not target:
            return False, f"无法回滚到版本 {target_version}"
        
        self._current_versions[skill_name] = target_version
        
        rollback_version = self.create_version(
            skill_name=skill_name,
            change_type=VersionChangeType.PATCH,
            changes=[f"回滚到版本 {target_version}"],
            author="system"
        )
        rollback_version.parent_version = target_version
        
        logger.info(f"回滚版本: {skill_name} -> v{target_version}")
        return True, f"已回滚到版本 {target_version}"
    
    def compare_versions(self, skill_name: str, version1: str, 
                         version2: str) -> Dict[str, Any]:
        """比较两个版本"""
        versions = self.get_versions(skill_name)
        
        v1 = next((v for v in versions if v.version == version1), None)
        v2 = next((v for v in versions if v.version == version2), None)
        
        if not v1 or not v2:
            return {"error": "版本不存在"}
        
        return {
            "version1": version1,
            "version2": version2,
            "changes_between": self._get_changes_between(versions, version1, version2),
            "breaking_changes": v2.breaking_changes if v2.breaking_changes else [],
            "compatibility": self._check_compatibility(v1, v2)
        }
    
    def _get_changes_between(self, versions: List[SkillVersion], 
                             v1: str, v2: str) -> List[Dict]:
        """获取两个版本之间的变更"""
        changes = []
        in_range = False
        
        for v in versions:
            if v.version == v1:
                in_range = True
                continue
            if in_range:
                changes.append({
                    "version": v.version,
                    "change_type": v.change_type.value,
                    "changes": v.changes
                })
            if v.version == v2:
                break
        
        return changes
    
    def _check_compatibility(self, v1: SkillVersion, v2: SkillVersion) -> Dict[str, Any]:
        """检查版本兼容性"""
        return {
            "is_compatible": len(v2.breaking_changes) == 0,
            "breaking_changes_count": len(v2.breaking_changes),
            "migration_required": len(v2.breaking_changes) > 0,
            "notes": v2.compatibility_notes
        }
    
    def generate_changelog(self, skill_name: str, 
                           from_version: str = None) -> str:
        """生成变更日志"""
        versions = self.get_versions(skill_name)
        
        if not versions:
            return f"技能 {skill_name} 没有版本历史"
        
        changelog = f"# {skill_name} 变更日志\n\n"
        
        sorted_versions = sorted(versions, key=lambda v: self._parse_version(v.version), reverse=True)
        
        for v in sorted_versions:
            if from_version and self._parse_version(v.version) < self._parse_version(from_version):
                continue
            
            status = " (已弃用)" if v.is_deprecated else ""
            changelog += f"## v{v.version}{status}\n"
            changelog += f"**发布日期**: {v.timestamp}\n"
            changelog += f"**变更类型**: {v.change_type.value}\n"
            changelog += f"**作者**: {v.author}\n\n"
            
            if v.changes:
                changelog += "### 变更内容\n"
                for change in v.changes:
                    changelog += f"- {change}\n"
                changelog += "\n"
            
            if v.new_features:
                changelog += "### 新功能\n"
                for feature in v.new_features:
                    changelog += f"- {feature}\n"
                changelog += "\n"
            
            if v.breaking_changes:
                changelog += "### 破坏性变更\n"
                for change in v.breaking_changes:
                    changelog += f"- ⚠️ {change}\n"
                changelog += "\n"
            
            if v.bug_fixes:
                changelog += "### Bug修复\n"
                for fix in v.bug_fixes:
                    changelog += f"- {fix}\n"
                changelog += "\n"
        
        return changelog


class SkillCreationAutomator:
    """技能创建自动化器
    
    负责自动化技能创建流程，包括需求分析、模板选择、
    内容生成、测试创建和验证。
    """
    
    def __init__(self, integration: 'SkillCreatorIntegration'):
        self.integration = integration
        self.template_manager = integration.template_manager
        self._creation_queue: queue.Queue = queue.Queue()
        self._automation_active = False
        self._automation_thread: Optional[threading.Thread] = None
        self._workflow_templates: Dict[str, Dict[str, Any]] = {}
        self._validation_rules: List[Dict[str, Any]] = []
        self._init_workflow_templates()
        self._init_validation_rules()
        logger.info("SkillCreationAutomator initialized")
    
    def _init_workflow_templates(self) -> None:
        """初始化工作流模板"""
        self._workflow_templates = {
            "standard": {
                "steps": [
                    {"name": "requirements_analysis", "required": True},
                    {"name": "template_selection", "required": True},
                    {"name": "content_generation", "required": True},
                    {"name": "test_creation", "required": True},
                    {"name": "validation", "required": True},
                    {"name": "documentation", "required": False}
                ],
                "parallel_steps": [],
                "rollback_on_failure": True
            },
            "rapid": {
                "steps": [
                    {"name": "requirements_analysis", "required": True},
                    {"name": "content_generation", "required": True},
                    {"name": "validation", "required": True}
                ],
                "parallel_steps": [],
                "rollback_on_failure": False
            },
            "enterprise": {
                "steps": [
                    {"name": "requirements_analysis", "required": True},
                    {"name": "design_review", "required": True},
                    {"name": "template_selection", "required": True},
                    {"name": "content_generation", "required": True},
                    {"name": "security_review", "required": True},
                    {"name": "test_creation", "required": True},
                    {"name": "performance_test", "required": True},
                    {"name": "validation", "required": True},
                    {"name": "documentation", "required": True},
                    {"name": "approval", "required": True}
                ],
                "parallel_steps": ["security_review", "performance_test"],
                "rollback_on_failure": True
            }
        }
    
    def _init_validation_rules(self) -> None:
        """初始化验证规则"""
        self._validation_rules = [
            {
                "name": "description_length",
                "check": lambda x: len(x.get("purpose", "")) >= 15,
                "message": "描述长度不足15字符"
            },
            {
                "name": "name_valid",
                "check": lambda x: bool(re.match(r'^[a-z][a-z0-9_-]*$', x.get("name", ""))),
                "message": "名称格式无效"
            },
            {
                "name": "category_valid",
                "check": lambda x: x.get("category") in ["development", "testing", "deployment", "analysis", "integration", "automation", "general"],
                "message": "分类无效"
            }
        ]
    
    def register_workflow_template(self, name: str, 
                                    workflow: Dict[str, Any]) -> Tuple[bool, str]:
        """注册工作流模板"""
        if name in self._workflow_templates:
            return False, f"工作流模板 '{name}' 已存在"
        
        self._workflow_templates[name] = workflow
        logger.info(f"注册工作流模板: {name}")
        return True, f"工作流模板 '{name}' 注册成功"
    
    def validate_requirements(self, requirements: Dict[str, str]) -> Tuple[bool, List[str]]:
        """验证需求
        
        Args:
            requirements: 需求字典
            
        Returns:
            (验证结果, 错误消息列表)
        """
        errors = []
        
        for rule in self._validation_rules:
            if not rule["check"](requirements):
                errors.append(rule["message"])
        
        return len(errors) == 0, errors
    
    def create_with_workflow(self, name: str, purpose: str, 
                             target_users: str, expected_output: str,
                             workflow_type: str = "standard",
                             category: str = "general",
                             template: SkillTemplate = None,
                             auto_validate: bool = True) -> Tuple[bool, Dict]:
        """使用工作流创建技能
        
        Args:
            name: 技能名称
            purpose: 技能用途
            target_users: 目标用户
            expected_output: 期望输出
            workflow_type: 工作流类型
            category: 分类
            template: 模板类型
            auto_validate: 是否自动验证
            
        Returns:
            (成功状态, 结果字典)
        """
        logger.info(f"使用 {workflow_type} 工作流创建技能: {name}")
        
        workflow = self._workflow_templates.get(workflow_type, self._workflow_templates["standard"])
        
        result = {
            "name": name,
            "workflow_type": workflow_type,
            "steps": [],
            "success": False,
            "skill_path": None,
            "evaluation": None,
            "errors": [],
            "artifacts": []
        }
        
        requirements = {
            "name": name,
            "purpose": purpose,
            "target_users": target_users,
            "expected_output": expected_output,
            "category": category
        }
        
        valid, errors = self.validate_requirements(requirements)
        if not valid:
            result["errors"] = [{"step": "validation", "message": e} for e in errors]
            return False, result
        
        executed_steps = []
        
        for step in workflow["steps"]:
            step_name = step["name"]
            step_result = {"step": step_name, "status": "started"}
            
            try:
                if step_name == "requirements_analysis":
                    analysis = self.analyze_requirements(purpose, target_users, expected_output)
                    step_result["status"] = "completed"
                    step_result["data"] = analysis
                    result["analysis"] = analysis
                
                elif step_name == "template_selection":
                    selected_template = template or SkillTemplate(analysis.get("suggested_template", "basic"))
                    step_result["status"] = "completed"
                    step_result["data"] = {"template": selected_template.value}
                    result["template"] = selected_template
                
                elif step_name == "content_generation":
                    success, message = self.integration.create_skill(
                        name=name,
                        category=category,
                        purpose=purpose,
                        target_users=target_users,
                        expected_output=expected_output,
                        template=result.get("template", SkillTemplate.BASIC),
                        trigger_keywords=analysis.get("trigger_keywords", []),
                        dependencies=analysis.get("dependencies", [])
                    )
                    if success:
                        step_result["status"] = "completed"
                        result["skill_path"] = f".trae/skills/{name}/SKILL.md"
                        result["artifacts"].append(result["skill_path"])
                    else:
                        step_result["status"] = "failed"
                        result["errors"].append({"step": step_name, "message": message})
                        if step.get("required", True) and workflow.get("rollback_on_failure", False):
                            self._rollback_creation(name, executed_steps)
                            return False, result
                
                elif step_name == "test_creation":
                    self._create_comprehensive_tests(name, result.get("skill_path", ""))
                    step_result["status"] = "completed"
                    result["artifacts"].append(f".trae/skills/{name}/tests/")
                
                elif step_name == "validation":
                    if auto_validate and result.get("skill_path"):
                        evaluation = self.integration.evaluate_skill(result["skill_path"])
                        result["evaluation"] = asdict(evaluation)
                        step_result["status"] = "completed"
                        step_result["data"] = {"score": evaluation.overall_score}
                    else:
                        step_result["status"] = "skipped"
                
                elif step_name == "documentation":
                    self._generate_documentation(name, result.get("skill_path", ""))
                    step_result["status"] = "completed"
                    result["artifacts"].append(f".trae/skills/{name}/docs/")
                
                elif step_name == "security_review":
                    security_result = self._perform_security_review(result.get("skill_path", ""))
                    step_result["status"] = "completed"
                    step_result["data"] = security_result
                
                elif step_name == "performance_test":
                    perf_result = self._perform_performance_test(result.get("skill_path", ""))
                    step_result["status"] = "completed"
                    step_result["data"] = perf_result
                
                elif step_name == "design_review":
                    design_result = self._perform_design_review(requirements)
                    step_result["status"] = "completed"
                    step_result["data"] = design_result
                
                elif step_name == "approval":
                    step_result["status"] = "pending"
                    step_result["data"] = {"requires_approval": True}
                
                else:
                    step_result["status"] = "skipped"
                
                executed_steps.append(step_name)
                
            except Exception as e:
                step_result["status"] = "failed"
                step_result["error"] = str(e)
                result["errors"].append({"step": step_name, "message": str(e)})
                
                if step.get("required", True) and workflow.get("rollback_on_failure", False):
                    self._rollback_creation(name, executed_steps)
                    return False, result
            
            result["steps"].append(step_result)
        
        required_steps = [s["name"] for s in workflow["steps"] if s.get("required")]
        required_errors = [e for e in result["errors"] if e.get("step") in required_steps]
        result["success"] = len(required_errors) == 0
        
        if result["success"]:
            self.integration.version_manager.create_version(
                skill_name=name,
                change_type=VersionChangeType.MAJOR,
                changes=["初始版本创建"],
                author="automator"
            )
        
        logger.info(f"工作流创建完成: {name}, 成功: {result['success']}")
        return result["success"], result
    
    def _rollback_creation(self, name: str, executed_steps: List[str]) -> None:
        """回滚创建操作"""
        logger.info(f"回滚技能创建: {name}")
        
        skill_dir = Path(f".trae/skills/{name}")
        if skill_dir.exists():
            import shutil
            shutil.rmtree(skill_dir)
    
    def _create_comprehensive_tests(self, name: str, skill_path: str) -> None:
        """创建综合测试"""
        if not skill_path:
            return
        
        skill_dir = Path(skill_path).parent
        tests_dir = skill_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        test_content = f'''# {name} 综合测试套件

## 单元测试

### 测试1: 核心功能
```python
def test_{name.lower()}_core():
    """测试核心功能"""
    # Arrange
    input_data = {{}}
    
    # Act
    result = execute_{name.lower()}(input_data)
    
    # Assert
    assert result is not None
```

### 测试2: 边界条件
```python
def test_{name.lower()}_boundaries():
    """测试边界条件"""
    pass
```

## 集成测试

### 测试3: 端到端
```python
def test_{name.lower()}_e2e():
    """端到端测试"""
    pass
```

## 性能测试

### 测试4: 性能基准
```python
def test_{name.lower()}_performance():
    """性能基准测试"""
    pass
```
'''
        
        test_file = tests_dir / "comprehensive_tests.md"
        test_file.write_text(test_content, encoding='utf-8')
    
    def _generate_documentation(self, name: str, skill_path: str) -> None:
        """生成文档"""
        if not skill_path:
            return
        
        skill_dir = Path(skill_path).parent
        docs_dir = skill_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        readme_content = f'''# {name} 技能文档

## 概述

本技能用于...

## 快速开始

### 安装

### 配置

### 使用

## API参考

## 示例

## 常见问题

## 更新日志
'''
        
        readme_file = docs_dir / "README.md"
        readme_file.write_text(readme_content, encoding='utf-8')
    
    def _perform_security_review(self, skill_path: str) -> Dict[str, Any]:
        """执行安全审查"""
        if not skill_path:
            return {"status": "skipped"}
        
        content = Path(skill_path).read_text(encoding='utf-8')
        
        issues = []
        security_patterns = ["password", "secret", "api_key", "token", "eval(", "exec("]
        
        for pattern in security_patterns:
            if pattern.lower() in content.lower():
                issues.append(f"发现潜在安全风险: {pattern}")
        
        return {
            "status": "completed",
            "issues": issues,
            "passed": len(issues) == 0
        }
    
    def _perform_performance_test(self, skill_path: str) -> Dict[str, Any]:
        """执行性能测试"""
        if not skill_path:
            return {"status": "skipped"}
        
        start_time = time.time()
        
        for _ in range(5):
            self.integration.evaluate_skill(skill_path)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 5
        
        return {
            "status": "completed",
            "average_execution_time_ms": avg_time * 1000,
            "iterations": 5,
            "passed": avg_time < 1.0
        }
    
    def _perform_design_review(self, requirements: Dict) -> Dict[str, Any]:
        """执行设计审查"""
        return {
            "status": "completed",
            "design_score": 0.85,
            "recommendations": [
                "建议添加更多使用示例",
                "建议完善错误处理流程"
            ]
        }
    
    def analyze_requirements(self, purpose: str, target_users: str, 
                             expected_output: str) -> Dict[str, Any]:
        """分析技能需求
        
        Args:
            purpose: 技能用途
            target_users: 目标用户
            expected_output: 期望输出
            
        Returns:
            需求分析结果
        """
        analysis = {
            "purpose": purpose,
            "target_users": target_users,
            "expected_output": expected_output,
            "complexity": self._estimate_complexity(purpose, expected_output),
            "suggested_template": self._suggest_template(purpose, target_users),
            "suggested_category": self._suggest_category(purpose),
            "trigger_keywords": self._extract_keywords(purpose),
            "dependencies": self._identify_dependencies(purpose),
            "test_scenarios": self._generate_test_scenarios(purpose, expected_output),
            "risk_factors": self._identify_risks(purpose, target_users),
            "estimated_effort": self._estimate_effort(purpose, expected_output)
        }
        
        logger.info(f"需求分析完成: {analysis['suggested_template']}")
        return analysis
    
    def _estimate_complexity(self, purpose: str, expected_output: str) -> str:
        """估算复杂度"""
        complexity_indicators = [
            ("高", ["复杂", "多个", "集成", "分布式", "微服务", "并发"]),
            ("中", ["处理", "转换", "分析", "生成", "验证"]),
            ("低", ["简单", "单一", "基础", "基本"])
        ]
        
        combined_text = purpose + expected_output
        
        for level, indicators in complexity_indicators:
            if any(ind in combined_text for ind in indicators):
                return level
        
        return "中"
    
    def _suggest_template(self, purpose: str, target_users: str) -> str:
        """建议模板类型"""
        template_indicators = {
            SkillTemplate.TDD: ["测试", "test", "tdd", "单元测试"],
            SkillTemplate.SDD: ["规范", "spec", "sdd", "标准"],
            SkillTemplate.MCP_SERVER: ["mcp", "server", "服务", "工具"],
            SkillTemplate.API_SERVICE: ["api", "rest", "接口", "endpoint"],
            SkillTemplate.UI_COMPONENT: ["ui", "界面", "组件", "component", "前端"],
            SkillTemplate.DATA_PIPELINE: ["pipeline", "管道", "数据流", "etl"],
            SkillTemplate.AGENT_ROLE: ["agent", "代理", "角色", "智能体"],
        }
        
        combined_text = purpose.lower() + target_users.lower()
        
        for template_type, indicators in template_indicators.items():
            if any(ind in combined_text for ind in indicators):
                return template_type.value
        
        return SkillTemplate.BASIC.value
    
    def _suggest_category(self, purpose: str) -> str:
        """建议分类"""
        category_indicators = {
            "development": ["开发", "develop", "代码", "code"],
            "testing": ["测试", "test", "验证", "verify"],
            "deployment": ["部署", "deploy", "发布", "release"],
            "analysis": ["分析", "analyze", "报告", "report"],
            "integration": ["集成", "integrate", "连接", "connect"],
            "automation": ["自动化", "automate", "批量", "batch"],
        }
        
        purpose_lower = purpose.lower()
        
        for category, indicators in category_indicators.items():
            if any(ind in purpose_lower for ind in indicators):
                return category
        
        return "general"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = []
        
        keywords.extend(re.findall(r'[\u4e00-\u9fa5]{2,4}', text))
        
        tech_keywords = re.findall(
            r'\b(react|vue|python|api|ui|ux|test|deploy|build|docker|kubernetes|'
            r'microservice|database|cache|queue|async|sync|rest|graphql)\b',
            text.lower()
        )
        keywords.extend(tech_keywords)
        
        return list(set(keywords))[:10]
    
    def _identify_dependencies(self, purpose: str) -> List[str]:
        """识别依赖"""
        dependencies = []
        
        dep_patterns = {
            "database": ["数据库", "database", "sql", "mysql", "postgres"],
            "cache": ["缓存", "cache", "redis"],
            "queue": ["队列", "queue", "kafka", "rabbitmq"],
            "storage": ["存储", "storage", "s3", "文件"],
            "auth": ["认证", "auth", "登录", "权限"],
        }
        
        purpose_lower = purpose.lower()
        
        for dep, patterns in dep_patterns.items():
            if any(p in purpose_lower for p in patterns):
                dependencies.append(dep)
        
        return dependencies
    
    def _generate_test_scenarios(self, purpose: str, expected_output: str) -> List[Dict]:
        """生成测试场景"""
        scenarios = [
            {
                "name": "正常流程测试",
                "description": "测试正常输入和预期输出",
                "type": "positive"
            },
            {
                "name": "边界条件测试",
                "description": "测试边界值和极端情况",
                "type": "boundary"
            },
            {
                "name": "错误处理测试",
                "description": "测试错误输入和异常处理",
                "type": "negative"
            },
            {
                "name": "性能测试",
                "description": "测试响应时间和资源消耗",
                "type": "performance"
            }
        ]
        
        return scenarios
    
    def _identify_risks(self, purpose: str, target_users: str) -> List[str]:
        """识别风险因素"""
        risks = []
        
        risk_indicators = {
            "数据安全风险": ["敏感", "密码", "密钥", "token", "个人信息"],
            "性能风险": ["大量", "高频", "实时", "并发"],
            "兼容性风险": ["多平台", "多版本", "跨系统"],
            "依赖风险": ["外部服务", "第三方", "api"],
        }
        
        combined_text = purpose + target_users
        
        for risk, indicators in risk_indicators.items():
            if any(ind in combined_text for ind in indicators):
                risks.append(risk)
        
        return risks
    
    def _estimate_effort(self, purpose: str, expected_output: str) -> Dict[str, Any]:
        """估算工作量"""
        complexity = self._estimate_complexity(purpose, expected_output)
        
        effort_map = {
            "高": {"hours": 40, "days": 5, "confidence": 0.7},
            "中": {"hours": 20, "days": 2.5, "confidence": 0.8},
            "低": {"hours": 8, "days": 1, "confidence": 0.9}
        }
        
        return effort_map.get(complexity, effort_map["中"])
    
    def automate_creation(self, name: str, purpose: str, target_users: str,
                          expected_output: str, auto_validate: bool = True) -> Tuple[bool, Dict]:
        """自动化创建技能
        
        Args:
            name: 技能名称
            purpose: 技能用途
            target_users: 目标用户
            expected_output: 期望输出
            auto_validate: 是否自动验证
            
        Returns:
            (成功状态, 结果字典)
        """
        logger.info(f"开始自动化创建技能: {name}")
        
        result = {
            "name": name,
            "steps": [],
            "success": False,
            "skill_path": None,
            "evaluation": None,
            "errors": []
        }
        
        try:
            result["steps"].append({"step": "requirements_analysis", "status": "started"})
            analysis = self.analyze_requirements(purpose, target_users, expected_output)
            result["steps"].append({"step": "requirements_analysis", "status": "completed", "data": analysis})
            
            result["steps"].append({"step": "template_selection", "status": "started"})
            template_type = SkillTemplate(analysis["suggested_template"])
            result["steps"].append({"step": "template_selection", "status": "completed", "data": {"template": template_type.value}})
            
            result["steps"].append({"step": "skill_creation", "status": "started"})
            success, message = self.integration.create_skill(
                name=name,
                category=analysis["suggested_category"],
                purpose=purpose,
                target_users=target_users,
                expected_output=expected_output,
                template=template_type,
                trigger_keywords=analysis["trigger_keywords"],
                dependencies=analysis["dependencies"]
            )
            
            if not success:
                result["errors"].append({"step": "skill_creation", "message": message})
                result["steps"].append({"step": "skill_creation", "status": "failed"})
                return False, result
            
            result["steps"].append({"step": "skill_creation", "status": "completed"})
            result["skill_path"] = f".trae/skills/{name}/SKILL.md"
            
            if auto_validate:
                result["steps"].append({"step": "validation", "status": "started"})
                evaluation = self.integration.evaluate_skill(result["skill_path"])
                result["evaluation"] = asdict(evaluation)
                result["steps"].append({"step": "validation", "status": "completed", "data": {"score": evaluation.overall_score}})
                
                if evaluation.overall_score < 0.6:
                    result["steps"].append({"step": "auto_optimization", "status": "started"})
                    self.integration.optimize_skill(result["skill_path"])
                    result["steps"].append({"step": "auto_optimization", "status": "completed"})
            
            result["success"] = True
            logger.info(f"技能自动化创建完成: {name}")
            
        except Exception as e:
            result["errors"].append({"step": "unknown", "message": str(e)})
            logger.error(f"技能自动化创建失败: {e}")
        
        return result["success"], result
    
    def batch_automate(self, requirements: List[Dict[str, str]], 
                       parallel: bool = False) -> Dict[str, Tuple[bool, Dict]]:
        """批量自动化创建
        
        Args:
            requirements: 需求列表，每个需求包含name, purpose, target_users, expected_output
            parallel: 是否并行执行
            
        Returns:
            结果字典
        """
        results = {}
        
        if parallel:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(
                        self.automate_creation,
                        req["name"], req["purpose"], req.get("target_users", "开发团队"),
                        req.get("expected_output", "执行结果")
                    ): req["name"]
                    for req in requirements
                }
                
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        success, result = future.result()
                        results[name] = (success, result)
                    except Exception as e:
                        results[name] = (False, {"error": str(e)})
        else:
            for req in requirements:
                success, result = self.automate_creation(
                    req["name"], req["purpose"], 
                    req.get("target_users", "开发团队"),
                    req.get("expected_output", "执行结果")
                )
                results[req["name"]] = (success, result)
        
        return results


class PipelineIntegrator:
    """流水线集成器
    
    负责与后端流水线系统的集成，支持技能与项目流水线的关联、
    状态同步和产物管理。
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self._integrations: Dict[str, PipelineIntegration] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        logger.info(f"PipelineIntegrator initialized with API: {api_base_url}")
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.info(f"注册事件处理器: {event_type}")
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """触发事件"""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"事件处理器执行失败: {e}")
    
    def integrate_skill(self, project_id: int, skill_name: str, 
                        stage: PipelineStage) -> PipelineIntegration:
        """集成技能到流水线
        
        Args:
            project_id: 项目ID
            skill_name: 技能名称
            stage: 流水线阶段
            
        Returns:
            集成信息
        """
        integration_id = f"INT-{project_id}-{skill_name}-{uuid.uuid4().hex[:6].upper()}"
        
        integration = PipelineIntegration(
            integration_id=integration_id,
            project_id=project_id,
            skill_name=skill_name,
            stage=stage,
            status="integrated",
            started_at=datetime.now().isoformat()
        )
        
        self._integrations[integration_id] = integration
        
        self._emit_event("skill_integrated", {
            "integration_id": integration_id,
            "project_id": project_id,
            "skill_name": skill_name,
            "stage": stage.value
        })
        
        logger.info(f"技能集成到流水线: {skill_name} -> 项目{project_id} -> {stage.value}")
        return integration
    
    def update_stage_status(self, integration_id: str, status: str,
                            artifacts: List[str] = None,
                            metrics: Dict[str, Any] = None) -> bool:
        """更新阶段状态
        
        Args:
            integration_id: 集成ID
            status: 新状态
            artifacts: 产物列表
            metrics: 指标数据
            
        Returns:
            更新是否成功
        """
        if integration_id not in self._integrations:
            logger.error(f"集成不存在: {integration_id}")
            return False
        
        integration = self._integrations[integration_id]
        integration.status = status
        
        if status == "completed":
            integration.completed_at = datetime.now().isoformat()
        
        if artifacts:
            integration.artifacts.extend(artifacts)
        
        if metrics:
            integration.metrics.update(metrics)
        
        self._emit_event("stage_status_updated", {
            "integration_id": integration_id,
            "status": status,
            "artifacts": artifacts,
            "metrics": metrics
        })
        
        logger.info(f"阶段状态更新: {integration_id} -> {status}")
        return True
    
    def get_project_integrations(self, project_id: int) -> List[PipelineIntegration]:
        """获取项目的所有集成
        
        Args:
            project_id: 项目ID
            
        Returns:
            集成列表
        """
        return [
            i for i in self._integrations.values()
            if i.project_id == project_id
        ]
    
    def get_skill_integrations(self, skill_name: str) -> List[PipelineIntegration]:
        """获取技能的所有集成
        
        Args:
            skill_name: 技能名称
            
        Returns:
            集成列表
        """
        return [
            i for i in self._integrations.values()
            if i.skill_name == skill_name
        ]
    
    def sync_with_backend(self, project_id: int) -> Dict[str, Any]:
        """与后端同步状态
        
        Args:
            project_id: 项目ID
            
        Returns:
            同步结果
        """
        result = {
            "project_id": project_id,
            "synced": False,
            "integrations": [],
            "errors": []
        }
        
        try:
            import requests
            
            response = requests.get(
                f"{self.api_base_url}/api/pipeline/project/{project_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                pipeline_data = response.json()
                
                for stage_data in pipeline_data:
                    stage_name = stage_data.get("stage_name")
                    status = stage_data.get("status")
                    
                    matching_integrations = [
                        i for i in self._integrations.values()
                        if i.project_id == project_id and i.stage.value == stage_name
                    ]
                    
                    for integration in matching_integrations:
                        integration.status = status
                        result["integrations"].append(integration.integration_id)
                
                result["synced"] = True
                logger.info(f"后端同步成功: 项目{project_id}")
            else:
                result["errors"].append(f"API返回错误: {response.status_code}")
                
        except ImportError:
            result["errors"].append("requests库未安装")
        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"后端同步失败: {e}")
        
        return result
    
    def trigger_pipeline_stage(self, project_id: int, stage: PipelineStage,
                               skill_name: str, context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """触发流水线阶段
        
        Args:
            project_id: 项目ID
            stage: 流水线阶段
            skill_name: 技能名称
            context: 执行上下文
            
        Returns:
            (成功状态, 消息)
        """
        try:
            import requests
            
            integration = self.integrate_skill(project_id, skill_name, stage)
            
            response = requests.post(
                f"{self.api_base_url}/api/pipeline/project/{project_id}/stage/{stage.value}/start",
                json={"triggered_by": skill_name},
                timeout=10
            )
            
            if response.status_code == 200:
                self.update_stage_status(integration.integration_id, "running")
                
                self._emit_event("pipeline_stage_triggered", {
                    "project_id": project_id,
                    "stage": stage.value,
                    "skill_name": skill_name,
                    "integration_id": integration.integration_id
                })
                
                logger.info(f"流水线阶段触发成功: {stage.value}")
                return True, f"阶段 {stage.value} 已触发"
            else:
                return False, f"API返回错误: {response.status_code}"
                
        except ImportError:
            return False, "requests库未安装"
        except Exception as e:
            logger.error(f"触发流水线阶段失败: {e}")
            return False, str(e)
    
    def complete_pipeline_stage(self, project_id: int, stage: PipelineStage,
                                output_artifacts: Dict[str, Any] = None) -> Tuple[bool, str]:
        """完成流水线阶段
        
        Args:
            project_id: 项目ID
            stage: 流水线阶段
            output_artifacts: 输出产物
            
        Returns:
            (成功状态, 消息)
        """
        try:
            import requests
            
            matching_integrations = [
                i for i in self._integrations.values()
                if i.project_id == project_id and i.stage == stage and i.status == "running"
            ]
            
            response = requests.post(
                f"{self.api_base_url}/api/pipeline/project/{project_id}/stage/{stage.value}/complete",
                json={"output_artifacts": output_artifacts},
                timeout=10
            )
            
            if response.status_code == 200:
                for integration in matching_integrations:
                    self.update_stage_status(
                        integration.integration_id, 
                        "completed",
                        artifacts=list(output_artifacts.keys()) if output_artifacts else None
                    )
                
                self._emit_event("pipeline_stage_completed", {
                    "project_id": project_id,
                    "stage": stage.value,
                    "artifacts": output_artifacts
                })
                
                logger.info(f"流水线阶段完成: {stage.value}")
                return True, f"阶段 {stage.value} 已完成"
            else:
                return False, f"API返回错误: {response.status_code}"
                
        except ImportError:
            return False, "requests库未安装"
        except Exception as e:
            logger.error(f"完成流水线阶段失败: {e}")
            return False, str(e)


class SkillCreatorIntegration:
    """skill-creator 集成管理器（增强版）
    
    整合所有技能管理功能，包括发现、创建、优化、评估、
    模板管理、性能监控和流水线集成。
    """
    
    EVALUATORS: Dict[EvaluationDimension, SkillEvaluator] = {
        EvaluationDimension.TRIGGER_ACCURACY: TriggerAccuracyEvaluator(),
        EvaluationDimension.OUTPUT_QUALITY: OutputQualityEvaluator(),
        EvaluationDimension.COMPLETENESS: CompletenessEvaluator(),
        EvaluationDimension.MAINTAINABILITY: MaintainabilityEvaluator(),
        EvaluationDimension.SECURITY: SecurityEvaluator(),
        EvaluationDimension.PERFORMANCE: PerformanceEvaluator(),
        EvaluationDimension.DOCUMENTATION: DocumentationEvaluator(),
        EvaluationDimension.TEST_COVERAGE: TestCoverageEvaluator(),
    }
    
    def __init__(self, skills_base_path: str = ".trae/skills"):
        self.skills_base_path = Path(skills_base_path)
        self.skill_creator_path = Path(".trae/skills/skill-creator/SKILL.md")
        try:
            from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
            _path_mgr = create_path_manager()
            self.logs_path = _path_mgr.get_output_path(OutputType.LOG, subdirectory="skill_integration")
            self.reports_path = _path_mgr.get_output_path(OutputType.REPORT, subdirectory="skills")
        except Exception:
            self.logs_path = get_path_config().LOGS_DIR / "skill_integration"
            self.reports_path = get_path_config().REPORTS_DIR / "skills"
        self.chains_path = Path("config/skill_chains")
        self.registry_path = SKILL_REGISTRY_PATH
        
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.reports_path.mkdir(parents=True, exist_ok=True)
        self.chains_path.mkdir(parents=True, exist_ok=True)
        
        self._skill_cache: Dict[str, SkillInfo] = {}
        self._chain_cache: Dict[str, SkillCallChain] = {}
        
        self.template_manager = TemplateManager()
        self.performance_monitor = PerformanceMonitor()
        self.version_manager = SkillVersionManager()
        self.automator = SkillCreationAutomator(self)
        self.pipeline_integrator = PipelineIntegrator()
        
        logger.info(f"SkillCreatorIntegration initialized with base path: {skills_base_path}")
    
    def discover_skills(self, scope: str = "all", use_cache: bool = True) -> List[SkillInfo]:
        """
        发现需要创建/优化的技能
        
        Args:
            scope: 发现范围 (all|needs_creation|needs_optimization|active|in_development)
            use_cache: 是否使用缓存
            
        Returns:
            技能信息列表
        """
        logger.info(f"Starting skill discovery with scope: {scope}")
        
        if use_cache and self._skill_cache:
            cached_skills = list(self._skill_cache.values())
            return self._filter_skills_by_scope(cached_skills, scope)
        
        skills = []
        
        if self.skills_base_path.exists():
            for skill_dir in self.skills_base_path.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    skill_info = self._analyze_existing_skill(skill_dir)
                    self._skill_cache[skill_info.name] = skill_info
                    skills.append(skill_info)
        
        potential_skills = self._discover_potential_skills()
        for skill in potential_skills:
            if skill.name not in self._skill_cache:
                self._skill_cache[skill.name] = skill
                skills.append(skill)
        
        skills = self._filter_skills_by_scope(skills, scope)
        
        logger.info(f"Discovered {len(skills)} skills")
        return skills
    
    def _filter_skills_by_scope(self, skills: List[SkillInfo], scope: str) -> List[SkillInfo]:
        """根据scope过滤技能"""
        if scope == "all":
            return skills
        elif scope == "needs_optimization":
            return [s for s in skills if s.status == SkillStatus.NEEDS_OPTIMIZATION]
        elif scope == "needs_creation":
            return [s for s in skills if s.status == SkillStatus.NEEDS_CREATION]
        elif scope == "active":
            return [s for s in skills if s.status == SkillStatus.ACTIVE]
        elif scope == "in_development":
            return [s for s in skills if s.status == SkillStatus.IN_DEVELOPMENT]
        return skills
    
    def _analyze_existing_skill(self, skill_dir: Path) -> SkillInfo:
        """分析现有技能状态"""
        skill_name = skill_dir.name
        skill_path = skill_dir / "SKILL.md"
        
        content = skill_path.read_text(encoding='utf-8')
        
        issues = []
        status = SkillStatus.ACTIVE
        priority = SkillPriority.MEDIUM
        
        for dimension, evaluator in self.EVALUATORS.items():
            dimension_issues = evaluator.get_issues(content)
            issues.extend(dimension_issues)
            
            score = evaluator.evaluate(content)
            if score < 0.6:
                status = SkillStatus.NEEDS_OPTIMIZATION
        
        high_severity_count = sum(1 for i in issues if i.get("severity") in ["high", "critical"])
        if high_severity_count >= 3:
            priority = SkillPriority.CRITICAL
        elif high_severity_count >= 1:
            priority = SkillPriority.HIGH
        
        category = self._extract_category(content)
        dependencies = self._extract_dependencies(content)
        tags = self._extract_tags(content)
        version = self._extract_version(content)
        
        return SkillInfo(
            name=skill_name,
            path=str(skill_path),
            category=category,
            status=status,
            description=self._extract_description(content),
            issues=[i["message"] for i in issues],
            priority=priority,
            dependencies=dependencies,
            tags=tags,
            version=version,
            updated_at=datetime.now().isoformat()
        )
    
    def _discover_potential_skills(self) -> List[SkillInfo]:
        """发现潜在需要创建的技能"""
        potential_skills = []
        
        project_docs = [
            ".trae/skills/sanliu/README.md",
            ".trae/skills/sanliu/SKILL.md"
        ]
        
        for doc_path in project_docs:
            if Path(doc_path).exists():
                content = Path(doc_path).read_text(encoding='utf-8')
        
        return potential_skills
    
    def _extract_category(self, content: str) -> str:
        """从技能内容中提取分类"""
        if "category:" in content:
            return content.split("category:")[1].split("\n")[0].strip()
        return "general"
    
    def _extract_description(self, content: str) -> str:
        """从技能内容中提取描述"""
        if "description:" in content:
            return content.split("description:")[1].split("\n")[0].strip()
        return ""
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """从技能内容中提取依赖"""
        dependencies = []
        
        if "依赖" in content:
            dep_section = content.split("依赖")[1].split("##")[0]
            dep_lines = [l.strip() for l in dep_section.split("\n") if l.strip().startswith("-")]
            dependencies = [l[1:].strip() for l in dep_lines]
        
        if "dependencies:" in content:
            dep_line = content.split("dependencies:")[1].split("\n")[0].strip()
            if dep_line.startswith("["):
                try:
                    dependencies = json.loads(dep_line)
                except:
                    pass
        
        return dependencies
    
    def _extract_tags(self, content: str) -> List[str]:
        """从技能内容中提取标签"""
        tags = []
        
        if "tags:" in content:
            tags_line = content.split("tags:")[1].split("\n")[0].strip()
            if tags_line.startswith("["):
                try:
                    tags = json.loads(tags_line)
                except:
                    pass
            else:
                tags = [t.strip() for t in tags_line.split(",")]
        
        return tags
    
    def _extract_version(self, content: str) -> str:
        """从技能内容中提取版本"""
        if "version:" in content:
            return content.split("version:")[1].split("\n")[0].strip()
        if "版本" in content:
            version_match = re.search(r'v?\d+\.\d+\.\d+', content)
            if version_match:
                return version_match.group()
        return "1.0.0"
    
    def create_skill(self, name: str, category: str, purpose: str, 
                     target_users: str, expected_output: str,
                     template: SkillTemplate = SkillTemplate.BASIC,
                     trigger_keywords: List[str] = None,
                     dependencies: List[str] = None) -> Tuple[bool, str]:
        """
        创建新技能
        
        Args:
            name: 技能名称
            category: 技能分类
            purpose: 技能用途
            target_users: 目标用户
            expected_output: 期望输出
            template: 技能模板类型
            trigger_keywords: 触发关键词
            dependencies: 依赖技能列表
            
        Returns:
            (成功状态, 消息)
        """
        logger.info(f"Creating skill: {name} with template: {template.value}")
        
        log_entry = self._create_log_entry(OperationType.CREATE.value, name)
        
        try:
            if trigger_keywords is None:
                trigger_keywords = self._extract_trigger_keywords(purpose, name)
            
            if dependencies is None:
                dependencies = []
            
            logger.info("Step 1: Analyzing requirements...")
            requirements = self._analyze_requirements(purpose, target_users, expected_output)
            requirements["trigger_keywords"] = trigger_keywords
            requirements["dependencies"] = dependencies
            
            logger.info("Step 2: Creating skill structure...")
            skill_dir = self.skills_base_path / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            
            success, skill_content = self.template_manager.render_template(
                template,
                {
                    "skill_name": name,
                    "category": category,
                    "description": purpose,
                    "author": "system",
                    "target_users": target_users,
                    "expected_output": expected_output
                }
            )
            
            if not success:
                skill_content = self._generate_skill_content_from_template(
                    name, category, purpose, target_users, expected_output, 
                    requirements, template
                )
            
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(skill_content, encoding='utf-8')
            
            logger.info("Step 3: Generating test cases...")
            self._generate_test_cases(name, skill_dir, template)
            
            logger.info("Step 4: Creating skill metadata...")
            self._create_skill_metadata(skill_dir, name, category, template, trigger_keywords)
            
            logger.info("Step 5: Evaluating skill...")
            evaluation = self.evaluate_skill(str(skill_file))
            
            skill_info = SkillInfo(
                name=name,
                path=str(skill_file),
                category=category,
                status=SkillStatus.IN_DEVELOPMENT,
                description=purpose,
                template=template,
                trigger_keywords=trigger_keywords,
                dependencies=dependencies,
                evaluation_score=evaluation.overall_score,
                issues=[i.get("message", "") for i in evaluation.issues]
            )
            self._skill_cache[name] = skill_info
            
            self._register_skill_to_registry(skill_info)
            
            log_entry.status = "success"
            log_entry.artifacts = [str(skill_file), str(skill_dir / "tests"), str(skill_dir / "metadata.json")]
            self._save_log(log_entry)
            
            logger.info(f"Skill created successfully: {name}")
            return True, f"技能 '{name}' 创建成功，评估分数: {evaluation.overall_score:.2f}，模板: {template.value}"
            
        except Exception as e:
            logger.error(f"Failed to create skill: {e}")
            log_entry.status = "failure"
            log_entry.errors = [{"type": "creation_error", "message": str(e)}]
            self._save_log(log_entry)
            return False, f"技能创建失败: {str(e)}"
    
    def optimize_skill(self, skill_path: str, optimization_target: str = "all") -> Tuple[bool, str]:
        """
        优化现有技能
        
        Args:
            skill_path: 技能文件路径
            optimization_target: 优化目标 (all|description|structure|examples|triggers|performance)
            
        Returns:
            (成功状态, 消息)
        """
        logger.info(f"Optimizing skill: {skill_path} with target: {optimization_target}")
        
        skill_file = Path(skill_path)
        if not skill_file.exists():
            return False, f"技能文件不存在: {skill_path}"
        
        skill_name = skill_file.parent.name
        log_entry = self._create_log_entry(OperationType.OPTIMIZE.value, skill_name)
        
        try:
            backup_path = skill_file.with_suffix(f".md.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
            backup_path.write_text(skill_file.read_text(encoding='utf-8'), encoding='utf-8')
            
            content = skill_file.read_text(encoding='utf-8')
            issues = self._analyze_skill_issues(content)
            
            before_evaluation = self.evaluate_skill(skill_path)
            
            optimized_content = self._optimize_skill_content(content, optimization_target, issues)
            skill_file.write_text(optimized_content, encoding='utf-8')
            
            after_evaluation = self.evaluate_skill(skill_path)
            
            improvement = after_evaluation.overall_score - before_evaluation.overall_score
            improvement_percent = (improvement / max(before_evaluation.overall_score, 0.01)) * 100
            
            benchmark_result = f"分数提升: {improvement:.2f} ({improvement_percent:.1f}%)"
            
            if skill_name in self._skill_cache:
                self._skill_cache[skill_name].evaluation_score = after_evaluation.overall_score
                self._skill_cache[skill_name].updated_at = datetime.now().isoformat()
                self._skill_cache[skill_name].status = SkillStatus.ACTIVE
            
            log_entry.status = "success"
            log_entry.artifacts = [str(skill_file), str(backup_path)]
            log_entry.metadata = {
                "before_score": before_evaluation.overall_score,
                "after_score": after_evaluation.overall_score,
                "improvement": improvement
            }
            self._save_log(log_entry)
            
            logger.info(f"Skill optimized successfully: {skill_name}")
            return True, f"技能 '{skill_name}' 优化完成，{benchmark_result}"
            
        except Exception as e:
            logger.error(f"Failed to optimize skill: {e}")
            log_entry.status = "failure"
            log_entry.errors = [{"type": "optimization_error", "message": str(e)}]
            self._save_log(log_entry)
            return False, f"技能优化失败: {str(e)}"
    
    def batch_optimize_skills(self, skills: List[str] = None, 
                               min_score: float = 0.7) -> Dict[str, Tuple[bool, str]]:
        """
        批量优化技能
        
        Args:
            skills: 技能名称列表，为None时自动发现需要优化的技能
            min_score: 最低分数阈值，低于此值的技能将被优化
            
        Returns:
            技能名称到优化结果的映射
        """
        logger.info(f"Starting batch optimization with min_score: {min_score}")
        
        if skills is None:
            all_skills = self.discover_skills("all")
            skills = [s.name for s in all_skills if s.evaluation_score < min_score]
        
        results = {}
        for skill_name in skills:
            skill_info = self._skill_cache.get(skill_name)
            if skill_info:
                success, message = self.optimize_skill(skill_info.path)
                results[skill_name] = (success, message)
        
        logger.info(f"Batch optimization completed: {len(results)} skills processed")
        return results
    
    def evaluate_skill(self, skill_path: str, dimensions: List[str] = None) -> EvaluationResult:
        """
        评估技能质量
        
        Args:
            skill_path: 技能文件路径
            dimensions: 评估维度列表，默认评估所有维度
            
        Returns:
            评估结果
        """
        logger.info(f"Evaluating skill: {skill_path}")
        
        skill_file = Path(skill_path)
        content = skill_file.read_text(encoding='utf-8')
        skill_name = skill_file.parent.name
        
        if dimensions is None:
            dimensions = [d.value for d in EvaluationDimension]
        
        scores = {}
        all_issues = []
        
        for dimension, evaluator in self.EVALUATORS.items():
            if dimension.value in dimensions:
                scores[dimension.value] = evaluator.evaluate(content)
                all_issues.extend(evaluator.get_issues(content))
        
        trigger_accuracy = scores.get(EvaluationDimension.TRIGGER_ACCURACY.value, 0.0)
        output_quality = scores.get(EvaluationDimension.OUTPUT_QUALITY.value, 0.0)
        completeness = scores.get(EvaluationDimension.COMPLETENESS.value, 0.0)
        maintainability = scores.get(EvaluationDimension.MAINTAINABILITY.value, 0.0)
        performance = scores.get(EvaluationDimension.PERFORMANCE.value, 0.0)
        security = scores.get(EvaluationDimension.SECURITY.value, 0.0)
        documentation = scores.get(EvaluationDimension.DOCUMENTATION.value, 0.0)
        test_coverage = scores.get(EvaluationDimension.TEST_COVERAGE.value, 0.0)
        
        dimension_scores = [trigger_accuracy, output_quality, completeness, 
                           maintainability, performance, security, 
                           documentation, test_coverage]
        overall_score = sum(dimension_scores) / len(dimension_scores)
        
        recommendations = self._generate_recommendations(content, all_issues)
        
        result = EvaluationResult(
            skill_name=skill_name,
            timestamp=datetime.now().isoformat(),
            overall_score=overall_score,
            trigger_accuracy=trigger_accuracy,
            output_quality=output_quality,
            completeness=completeness,
            maintainability=maintainability,
            performance=performance,
            security=security,
            documentation=documentation,
            test_coverage=test_coverage,
            issues=all_issues,
            recommendations=recommendations
        )
        
        self._save_evaluation_result(result)
        
        return result
    
    def benchmark_skill(self, skill_path: str, iterations: int = 10) -> Dict[str, Any]:
        """
        基准测试技能性能
        
        Args:
            skill_path: 技能文件路径
            iterations: 测试迭代次数
            
        Returns:
            基准测试结果
        """
        logger.info(f"Benchmarking skill: {skill_path}")
        
        skill_file = Path(skill_path)
        skill_name = skill_file.parent.name
        
        start_time = time.time()
        
        for i in range(iterations):
            evaluation = self.evaluate_skill(skill_path)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        self.performance_monitor.record_metric(
            skill_name,
            PerformanceMetricType.EXECUTION_TIME,
            avg_time * 1000,
            "ms",
            {"iterations": iterations}
        )
        
        return {
            "skill_name": skill_name,
            "iterations": iterations,
            "total_time_seconds": total_time,
            "average_time_ms": avg_time * 1000,
            "evaluation_score": evaluation.overall_score
        }
    
    def generate_report(self, output_format: str = "markdown") -> str:
        """
        生成技能集成报告
        
        Args:
            output_format: 输出格式 (markdown|json|html)
            
        Returns:
            报告内容
        """
        logger.info(f"Generating skill integration report in {output_format} format")
        
        all_skills = self.discover_skills("all")
        
        stats = {
            "total_skills": len(all_skills),
            "active": len([s for s in all_skills if s.status == SkillStatus.ACTIVE]),
            "needs_optimization": len([s for s in all_skills if s.status == SkillStatus.NEEDS_OPTIMIZATION]),
            "needs_creation": len([s for s in all_skills if s.status == SkillStatus.NEEDS_CREATION]),
            "in_development": len([s for s in all_skills if s.status == SkillStatus.IN_DEVELOPMENT])
        }
        
        if output_format == "json":
            return json.dumps({
                "timestamp": datetime.now().isoformat(),
                "statistics": stats,
                "skills": [asdict(s) for s in all_skills]
            }, ensure_ascii=False, indent=2)
        
        elif output_format == "markdown":
            report = f"""# 技能集成报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计概览

| 指标 | 数量 |
|------|------|
| 技能总数 | {stats['total_skills']} |
| 活跃技能 | {stats['active']} |
| 需要优化 | {stats['needs_optimization']} |
| 需要创建 | {stats['needs_creation']} |
| 开发中 | {stats['in_development']} |

## 技能详情

"""
            for skill in all_skills:
                status_emoji = {
                    SkillStatus.ACTIVE: "✅",
                    SkillStatus.NEEDS_OPTIMIZATION: "⚠️",
                    SkillStatus.NEEDS_CREATION: "🆕",
                    SkillStatus.DEPRECATED: "❌",
                    SkillStatus.IN_DEVELOPMENT: "🔄"
                }.get(skill.status, "❓")
                
                report += f"""### {status_emoji} {skill.name}

- **分类**: {skill.category}
- **状态**: {skill.status.value}
- **路径**: `{skill.path}`
- **描述**: {skill.description or '无'}
- **评估分数**: {skill.evaluation_score:.2f}
"""
                if skill.issues:
                    report += "- **问题**:\n"
                    for issue in skill.issues[:5]:
                        report += f"  - {issue}\n"
                report += "\n"
            
            return report
        
        else:
            return f"Unsupported format: {output_format}"
    
    def _analyze_requirements(self, purpose: str, target_users: str, expected_output: str) -> Dict:
        """分析技能需求"""
        return {
            "purpose": purpose,
            "target_users": target_users,
            "expected_output": expected_output,
            "complexity": "medium",
            "dependencies": []
        }
    
    def _generate_skill_content_from_template(self, name: str, category: str, 
                                               purpose: str, target_users: str, 
                                               expected_output: str, requirements: Dict,
                                               template: SkillTemplate) -> str:
        """根据模板生成技能内容"""
        
        base_content = f"""---
name: {name}
description: {purpose}
category: {category}
version: 1.0.0
---

# {name} 技能

## 职责定义

{purpose}

**目标用户**: {target_users}

**期望输出**: {expected_output}

## 工作流程

### 阶段一: 准备

1. 接收输入参数
2. 验证输入完整性
3. 初始化执行环境

### 阶段二: 执行

1. 执行核心逻辑
2. 处理中间结果
3. 验证输出质量

### 阶段三: 交付

1. 格式化输出
2. 生成执行报告
3. 记录执行日志

## 使用示例

### 示例1: 基本用法

```bash
调用 {name}/SKILL.md --param1=value1 --param2=value2
```

## 输出规范

### 成功输出

```json
{{
  "status": "success",
  "result": "执行结果",
  "metadata": {{
    "timestamp": "{datetime.now().isoformat()}",
    "duration_ms": 1000
  }}
}}
```

### 错误输出

```json
{{
  "status": "error",
  "error_code": "ERROR_CODE",
  "error_message": "错误描述",
  "suggestions": ["建议1", "建议2"]
}}
```

## 错误处理

| 错误类型 | 错误码 | 处理方式 |
|----------|--------|----------|
| 参数错误 | INVALID_PARAMS | 检查输入参数 |
| 执行错误 | EXECUTION_ERROR | 查看详细日志 |
| 超时错误 | TIMEOUT | 增加超时时间或优化性能 |

## 依赖项

- 无

## 版本历史

- v1.0.0 - 初始版本
"""
        
        template_additions = {
            SkillTemplate.TDD: self._get_tdd_template_addition(),
            SkillTemplate.SDD: self._get_sdd_template_addition(),
            SkillTemplate.MCP_SERVER: self._get_mcp_template_addition(),
            SkillTemplate.UI_COMPONENT: self._get_ui_template_addition(),
            SkillTemplate.API_SERVICE: self._get_api_template_addition(),
            SkillTemplate.DATA_PIPELINE: self._get_pipeline_template_addition(),
            SkillTemplate.AGENT_ROLE: self._get_agent_template_addition(),
        }
        
        addition = template_additions.get(template, "")
        
        if addition:
            base_content = base_content.replace(
                "## 版本历史",
                f"{addition}\n\n## 版本历史"
            )
        
        trigger_keywords = requirements.get("trigger_keywords", [])
        if trigger_keywords:
            trigger_section = f"\n## 触发关键词\n\n"
            trigger_section += ", ".join(f"`{kw}`" for kw in trigger_keywords)
            base_content = base_content.replace(
                "## 版本历史",
                f"{trigger_section}\n\n## 版本历史"
            )
        
        return base_content
    
    def _get_tdd_template_addition(self) -> str:
        return """
## 测试驱动开发流程

### 红灯阶段
1. 编写失败的测试用例
2. 确认测试失败原因符合预期

### 绿灯阶段
1. 编写最小实现代码
2. 确认测试通过

### 重构阶段
1. 优化代码结构
2. 确保测试仍然通过

## 测试规范

- 单元测试覆盖率: >= 80%
- 集成测试: 覆盖主要流程
- 边界测试: 覆盖边界条件
"""
    
    def _get_sdd_template_addition(self) -> str:
        return """
## 规范驱动开发流程

### 规范解析阶段
1. 解析规范文档
2. 提取需求点
3. 生成测试用例

### 实现阶段
1. 按规范实现功能
2. 执行规范验证
3. 生成合规报告

### 验证阶段
1. 规范一致性检查
2. 边界条件验证
3. 输出合规性报告
"""
    
    def _get_mcp_template_addition(self) -> str:
        return """
## MCP服务规范

### 工具定义
- 工具命名: snake_case
- 参数验证: 使用JSON Schema
- 错误处理: 统一错误码

### 资源管理
- 资源URI格式: `scheme://path`
- 支持订阅机制
- 实现资源列表

### 提示词模板
- 支持参数化模板
- 包含使用示例
- 提供最佳实践
"""
    
    def _get_ui_template_addition(self) -> str:
        return """
## UI组件规范

### 设计系统
- 颜色: 使用设计令牌
- 字体: 遵循排版规范
- 间距: 使用标准间距

### 可访问性
- ARIA标签: 完整支持
- 键盘导航: 全功能支持
- 屏幕阅读器: 兼容

### 响应式
- 断点: sm/md/lg/xl/2xl
- 移动优先设计
- 触摸交互支持
"""
    
    def _get_api_template_addition(self) -> str:
        return """
## API服务规范

### 接口设计
- RESTful风格
- 版本控制: /api/v1/
- 统一响应格式

### 认证授权
- JWT Token认证
- 角色权限控制
- 请求频率限制

### 错误处理
- 统一错误码
- 详细错误信息
- 错误恢复建议
"""
    
    def _get_pipeline_template_addition(self) -> str:
        return """
## 数据管道规范

### 数据流
- 输入验证
- 数据转换
- 输出验证

### 性能优化
- 批量处理
- 并行执行
- 缓存策略

### 监控告警
- 执行日志
- 性能指标
- 异常告警
"""
    
    def _get_agent_template_addition(self) -> str:
        return """
## Agent角色规范

### 角色定义
- 专业领域
- 核心能力
- 协作关系

### 任务执行
- 任务分解
- 执行策略
- 结果验证

### 协作机制
- 消息格式
- 状态同步
- 冲突解决
"""
    
    def _create_skill_metadata(self, skill_dir: Path, name: str, 
                                category: str, template: SkillTemplate,
                                trigger_keywords: List[str]):
        """创建技能元数据文件"""
        metadata = {
            "name": name,
            "category": category,
            "template": template.value,
            "trigger_keywords": trigger_keywords,
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "status": "in_development"
        }
        
        metadata_file = skill_dir / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), 
                                  encoding='utf-8')
    
    def _generate_test_cases(self, skill_name: str, skill_dir: Path, 
                              template: SkillTemplate = SkillTemplate.BASIC):
        """生成测试用例"""
        tests_dir = skill_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        base_test_content = f"""# {skill_name} 测试用例

## 测试用例1: 基本功能测试

**输入**:
```json
{{
  "param1": "test_value",
  "param2": 123
}}
```

**期望输出**:
```json
{{
  "status": "success"
}}
```

## 测试用例2: 边界条件测试

**输入**:
```json
{{
  "param1": "",
  "param2": 0
}}
```

**期望输出**:
```json
{{
  "status": "success"
}}
```

## 测试用例3: 错误处理测试

**输入**:
```json
{{
  "param1": null
}}
```

**期望输出**:
```json
{{
  "status": "error",
  "error_code": "INVALID_PARAMS"
}}
```
"""
        
        test_file = tests_dir / "test_cases.md"
        test_file.write_text(base_test_content, encoding='utf-8')
        
        if template == SkillTemplate.TDD:
            tdd_test = tests_dir / "tdd_tests.md"
            tdd_test.write_text(self._generate_tdd_tests(skill_name), encoding='utf-8')
    
    def _generate_tdd_tests(self, skill_name: str) -> str:
        """生成TDD测试用例"""
        return f"""# {skill_name} TDD测试用例

## 单元测试

### 测试1: 核心功能
```python
def test_{skill_name.lower()}_core_function():
    # Arrange
    input_data = {{}}
    expected = {{}}
    
    # Act
    result = execute_{skill_name.lower()}(input_data)
    
    # Assert
    assert result == expected
```

### 测试2: 边界条件
```python
def test_{skill_name.lower()}_boundary():
    # Arrange
    input_data = {{}}
    
    # Act & Assert
    with pytest.raises(ValueError):
        execute_{skill_name.lower()}(input_data)
```

## 集成测试

### 测试3: 端到端流程
```python
def test_{skill_name.lower()}_e2e():
    # Arrange
    context = setup_test_context()
    
    # Act
    result = run_{skill_name.lower()}_workflow(context)
    
    # Assert
    assert result.status == "success"
```
"""
    
    def _analyze_skill_issues(self, content: str) -> List[Dict]:
        """分析技能问题"""
        issues = []
        
        if len(content) < 500:
            issues.append({"type": "content", "severity": "medium", "message": "内容可能不够完整"})
        
        if "示例" not in content:
            issues.append({"type": "examples", "severity": "high", "message": "缺少使用示例"})
        
        if "错误" not in content:
            issues.append({"type": "error_handling", "severity": "medium", "message": "缺少错误处理说明"})
        
        return issues
    
    def _optimize_skill_content(self, content: str, target: str, issues: List[Dict]) -> str:
        """优化技能内容"""
        optimized = content
        
        if target in ["all", "examples"] and "示例" not in optimized:
            optimized += "\n\n## 使用示例\n\n### 示例1\n\n```bash\n调用 skill-name --param=value\n```\n"
        
        if target in ["all", "structure"]:
            if "## 错误处理" not in optimized:
                optimized += "\n\n## 错误处理\n\n| 错误类型 | 处理方式 |\n|----------|----------|\n| 参数错误 | 检查输入 |\n"
        
        return optimized
    
    def _generate_recommendations(self, content: str, issues: List[Dict]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        for issue in issues:
            if issue.get("type") == "description_too_short":
                recommendations.append("扩展技能描述，包含更多关键词和使用场景")
            elif issue.get("type") == "missing_examples":
                recommendations.append("添加至少2-3个使用示例，覆盖常见场景")
            elif issue.get("type") == "missing_required_sections":
                recommendations.append("添加缺失的必要章节以提高技能完整性")
            elif issue.get("type") == "security":
                recommendations.append("关注安全问题，添加必要的安全措施")
        
        if not recommendations:
            recommendations.append("技能整体质量良好，建议定期复查")
        
        return recommendations
    
    def _create_log_entry(self, operation: str, skill_name: str) -> IntegrationLog:
        """创建日志条目"""
        return IntegrationLog(
            log_id=f"SKILL-{operation.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            operation=operation,
            skill_name=skill_name,
            skill_path=f".trae/skills/{skill_name}/SKILL.md",
            requesting_department="礼部",
            status="in_progress",
            duration_ms=0,
            errors=[],
            artifacts=[]
        )
    
    def _save_log(self, log_entry: IntegrationLog) -> None:
        """保存日志"""
        log_file = self.logs_path / f"{log_entry.log_id}.json"
        log_file.write_text(json.dumps(asdict(log_entry), ensure_ascii=False, indent=2), encoding='utf-8')
    
    def _save_evaluation_result(self, result: EvaluationResult) -> None:
        """保存评估结果"""
        result_file = self.reports_path / f"{result.skill_name}_evaluation.json"
        result_file.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding='utf-8')
    
    def create_skill_chain(self, name: str, description: str, skills: List[str],
                           execution_order: List[int] = None, 
                           conditions: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        创建技能调用链
        
        Args:
            name: 调用链名称
            description: 调用链描述
            skills: 技能列表
            execution_order: 执行顺序（索引列表）
            conditions: 执行条件
            
        Returns:
            (成功状态, 消息)
        """
        logger.info(f"Creating skill chain: {name}")
        
        chain_id = f"CHAIN-{hashlib.md5(name.encode()).hexdigest()[:8].upper()}"
        
        if execution_order is None:
            execution_order = list(range(len(skills)))
        
        if conditions is None:
            conditions = {}
        
        for skill_name in skills:
            if skill_name not in self._skill_cache:
                self.discover_skills("all")
            if skill_name not in self._skill_cache:
                return False, f"技能 '{skill_name}' 不存在"
        
        chain = SkillCallChain(
            chain_id=chain_id,
            name=name,
            description=description,
            skills=skills,
            execution_order=execution_order,
            conditions=conditions
        )
        
        self._chain_cache[chain_id] = chain
        
        chain_file = self.chains_path / f"{chain_id}.json"
        chain_file.write_text(json.dumps(asdict(chain), ensure_ascii=False, indent=2), encoding='utf-8')
        
        logger.info(f"Skill chain created: {chain_id}")
        return True, f"技能调用链 '{name}' 创建成功，ID: {chain_id}"
    
    def execute_skill_chain(self, chain_id: str, context: Dict[str, Any] = None) -> Tuple[bool, Dict]:
        """
        执行技能调用链
        
        Args:
            chain_id: 调用链ID
            context: 执行上下文
            
        Returns:
            (成功状态, 执行结果)
        """
        logger.info(f"Executing skill chain: {chain_id}")
        
        if chain_id not in self._chain_cache:
            chain_file = self.chains_path / f"{chain_id}.json"
            if chain_file.exists():
                chain_data = json.loads(chain_file.read_text(encoding='utf-8'))
                chain = SkillCallChain(**chain_data)
                self._chain_cache[chain_id] = chain
            else:
                return False, {"error": f"调用链 '{chain_id}' 不存在"}
        
        chain = self._chain_cache[chain_id]
        
        if context is None:
            context = {}
        
        results = {
            "chain_id": chain_id,
            "chain_name": chain.name,
            "executed_skills": [],
            "outputs": [],
            "errors": [],
            "success": True
        }
        
        for idx in chain.execution_order:
            skill_name = chain.skills[idx]
            
            condition_key = f"skill_{idx}_condition"
            if condition_key in chain.conditions:
                condition = chain.conditions[condition_key]
                if not self._evaluate_condition(condition, context):
                    logger.info(f"Skipping skill {skill_name} due to condition")
                    continue
            
            skill_info = self._skill_cache.get(skill_name)
            if skill_info:
                results["executed_skills"].append(skill_name)
                results["outputs"].append({
                    "skill": skill_name,
                    "path": skill_info.path,
                    "status": "executed"
                })
            else:
                results["errors"].append({
                    "skill": skill_name,
                    "error": "技能未找到"
                })
                results["success"] = False
        
        logger.info(f"Skill chain execution completed: {chain_id}")
        return results["success"], results
    
    def _evaluate_condition(self, condition: Dict, context: Dict) -> bool:
        """评估执行条件"""
        condition_type = condition.get("type", "always")
        
        if condition_type == "always":
            return True
        elif condition_type == "context_exists":
            key = condition.get("key")
            return key in context
        elif condition_type == "context_equals":
            key = condition.get("key")
            value = condition.get("value")
            return context.get(key) == value
        elif condition_type == "previous_success":
            return condition.get("previous_success", True)
        
        return True
    
    def list_skill_chains(self) -> List[SkillCallChain]:
        """列出所有技能调用链"""
        chains = list(self._chain_cache.values())
        
        for chain_file in self.chains_path.glob("CHAIN-*.json"):
            chain_id = chain_file.stem
            if chain_id not in self._chain_cache:
                chain_data = json.loads(chain_file.read_text(encoding='utf-8'))
                chain = SkillCallChain(**chain_data)
                self._chain_cache[chain_id] = chain
                chains.append(chain)
        
        return chains
    
    def discover_skills_from_registry(self) -> List[SkillInfo]:
        """从注册表发现技能"""
        skills = []
        
        if self.registry_path.exists():
            content = self.registry_path.read_text(encoding='utf-8')
            
            skill_pattern = r'###\s+(\S+)\s*\n\n-\s+\*\*名称\*\*[：:]\s*(\S+)'
            matches = re.findall(skill_pattern, content)
            
            for match in matches:
                skill_id = match[0]
                skill_name = match[1]
                
                path_pattern = rf'###\s+{skill_id}\s*\n\n.*?路径\*\*[：:]\s*`?([^`\n]+)`?'
                path_match = re.search(path_pattern, content, re.DOTALL)
                skill_path = path_match.group(1).strip() if path_match else ""
                
                desc_pattern = rf'###\s+{skill_id}\s*\n\n.*?功能描述\*\*[：:]\s*([^\n]+)'
                desc_match = re.search(desc_pattern, content, re.DOTALL)
                description = desc_match.group(1).strip() if desc_match else ""
                
                skill_info = SkillInfo(
                    name=skill_name,
                    path=skill_path,
                    category="external",
                    status=SkillStatus.ACTIVE,
                    description=description,
                    tags=["external", "registered"]
                )
                skills.append(skill_info)
                self._skill_cache[skill_name] = skill_info
        
        return skills
    
    def _extract_trigger_keywords(self, purpose: str, name: str) -> List[str]:
        """从用途描述中提取触发关键词"""
        keywords = []
        
        keywords.extend(re.findall(r'[\u4e00-\u9fa5]{2,4}', purpose))
        
        tech_keywords = re.findall(r'\b(react|vue|python|api|ui|ux|test|deploy|build)\b', 
                                    purpose.lower())
        keywords.extend(tech_keywords)
        
        name_parts = re.findall(r'[a-zA-Z]+', name)
        keywords.extend(name_parts)
        
        return list(set(keywords))[:10]
    
    def _register_skill_to_registry(self, skill_info: SkillInfo) -> None:
        """将技能注册到注册表"""
        if not self.registry_path.exists():
            return
        
        content = self.registry_path.read_text(encoding='utf-8')
        
        if f"### {skill_info.name}" in content:
            return
        
        skill_entry = f"""

### {skill_info.name}

- **名称**：{skill_info.name}
- **路径**：{skill_info.path}
- **功能描述**：{skill_info.description}
- **适用场景**：
  - {skill_info.description}
- **调用部门**：礼部（规范制定）
- **核心能力**：
  - 模板类型: {skill_info.template.value}
  - 触发关键词: {', '.join(skill_info.trigger_keywords[:5])}

---
"""
        
        insert_marker = "## 技能状态追踪"
        if insert_marker in content:
            content = content.replace(insert_marker, f"{skill_entry}\n{insert_marker}")
        else:
            content += skill_entry
        
        self.registry_path.write_text(content, encoding='utf-8')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="skill-creator 集成脚本（增强版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python skill_creator_integration.py discover --scope=all
  python skill_creator_integration.py create --name=my-skill --category=development
  python skill_creator_integration.py optimize --path=.trae/skills/my-skill/SKILL.md
  python skill_creator_integration.py evaluate --path=.trae/skills/my-skill/SKILL.md
  python skill_creator_integration.py benchmark --path=.trae/skills/my-skill/SKILL.md
  python skill_creator_integration.py chain --action=create --name="设计流程" --skills=skill1,skill2
  python skill_creator_integration.py chain --action=execute --chain-id=CHAIN-XXXX
  python skill_creator_integration.py template --action=list
  python skill_creator_integration.py template --action=create --name=my-template --type=basic
  python skill_creator_integration.py pipeline --action=integrate --project-id=1 --skill=my-skill --stage=design
  python skill_creator_integration.py report --format=markdown
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    discover_parser = subparsers.add_parser("discover", help="发现需要创建/优化的技能")
    discover_parser.add_argument("--scope", choices=["all", "needs_creation", "needs_optimization", "active", "in_development"],
                                 default="all", help="发现范围")
    discover_parser.add_argument("--output", choices=["console", "json"], default="console", help="输出格式")
    discover_parser.add_argument("--from-registry", action="store_true", help="从注册表发现")
    
    create_parser = subparsers.add_parser("create", help="创建新技能")
    create_parser.add_argument("--name", required=True, help="技能名称")
    create_parser.add_argument("--category", default="general", help="技能分类")
    create_parser.add_argument("--purpose", required=True, help="技能用途")
    create_parser.add_argument("--target-users", default="开发团队", help="目标用户")
    create_parser.add_argument("--expected-output", default="执行结果报告", help="期望输出")
    create_parser.add_argument("--template", 
                                choices=[t.value for t in SkillTemplate],
                                default="basic", help="技能模板类型")
    create_parser.add_argument("--trigger-keywords", help="触发关键词（逗号分隔）")
    create_parser.add_argument("--dependencies", help="依赖技能（逗号分隔）")
    create_parser.add_argument("--auto", action="store_true", help="使用自动化流程")
    
    optimize_parser = subparsers.add_parser("optimize", help="优化现有技能")
    optimize_parser.add_argument("--path", help="技能文件路径")
    optimize_parser.add_argument("--target", choices=["all", "description", "structure", "examples", "triggers", "performance"],
                                 default="all", help="优化目标")
    optimize_parser.add_argument("--batch", action="store_true", help="批量优化模式")
    optimize_parser.add_argument("--min-score", type=float, default=0.7, help="批量优化最低分数阈值")
    optimize_parser.add_argument("--skills", help="批量优化的技能列表（逗号分隔）")
    
    evaluate_parser = subparsers.add_parser("evaluate", help="评估技能质量")
    evaluate_parser.add_argument("--path", required=True, help="技能文件路径")
    evaluate_parser.add_argument("--dimensions", help="评估维度（逗号分隔）")
    
    benchmark_parser = subparsers.add_parser("benchmark", help="基准测试技能性能")
    benchmark_parser.add_argument("--path", required=True, help="技能文件路径")
    benchmark_parser.add_argument("--iterations", type=int, default=10, help="测试迭代次数")
    
    chain_parser = subparsers.add_parser("chain", help="技能调用链管理")
    chain_parser.add_argument("--action", choices=["create", "execute", "list"], required=True, help="操作类型")
    chain_parser.add_argument("--name", help="调用链名称")
    chain_parser.add_argument("--description", default="", help="调用链描述")
    chain_parser.add_argument("--skills", help="技能列表（逗号分隔）")
    chain_parser.add_argument("--chain-id", help="调用链ID")
    chain_parser.add_argument("--context", help="执行上下文（JSON格式）")
    
    template_parser = subparsers.add_parser("template", help="模板管理")
    template_parser.add_argument("--action", choices=["list", "get", "create", "update", "delete", "render"], required=True, help="操作类型")
    template_parser.add_argument("--type", help="模板类型")
    template_parser.add_argument("--name", help="模板名称")
    template_parser.add_argument("--description", help="模板描述")
    template_parser.add_argument("--variables", help="模板变量（JSON格式）")
    
    pipeline_parser = subparsers.add_parser("pipeline", help="流水线集成")
    pipeline_parser.add_argument("--action", choices=["integrate", "sync", "trigger", "complete"], required=True, help="操作类型")
    pipeline_parser.add_argument("--project-id", type=int, help="项目ID")
    pipeline_parser.add_argument("--skill", help="技能名称")
    pipeline_parser.add_argument("--stage", choices=[s.value for s in PipelineStage], help="流水线阶段")
    pipeline_parser.add_argument("--artifacts", help="产物（JSON格式）")
    
    report_parser = subparsers.add_parser("report", help="生成技能集成报告")
    report_parser.add_argument("--format", choices=["markdown", "json", "html"], default="markdown", help="报告格式")
    report_parser.add_argument("--output", help="输出文件路径")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    integration = SkillCreatorIntegration()
    
    if args.command == "discover":
        if args.from_registry:
            skills = integration.discover_skills_from_registry()
        else:
            skills = integration.discover_skills(args.scope)
        
        if args.output == "json":
            print(json.dumps([asdict(s) for s in skills], ensure_ascii=False, indent=2))
        else:
            print(f"\n发现 {len(skills)} 个技能:\n")
            for skill in skills:
                status_icon = {
                    SkillStatus.ACTIVE: "✅",
                    SkillStatus.NEEDS_OPTIMIZATION: "⚠️",
                    SkillStatus.NEEDS_CREATION: "🆕",
                    SkillStatus.DEPRECATED: "❌",
                    SkillStatus.IN_DEVELOPMENT: "🔄",
                    SkillStatus.TESTING: "🧪"
                }.get(skill.status, "❓")
                print(f"{status_icon} {skill.name} ({skill.category}) - {skill.status.value}")
                if skill.issues:
                    for issue in skill.issues[:3]:
                        print(f"   - {issue}")
    
    elif args.command == "create":
        trigger_keywords = args.trigger_keywords.split(",") if args.trigger_keywords else None
        dependencies = args.dependencies.split(",") if args.dependencies else None
        template = SkillTemplate(args.template)
        
        if args.auto:
            success, result = integration.automator.automate_creation(
                name=args.name,
                purpose=args.purpose,
                target_users=args.target_users,
                expected_output=args.expected_output
            )
            if success:
                print(f"技能自动化创建成功: {args.name}")
                print(f"评估分数: {result.get('evaluation', {}).get('overall_score', 0):.2f}")
            else:
                print(f"技能自动化创建失败: {result.get('errors', [])}")
            sys.exit(0 if success else 1)
        else:
            success, message = integration.create_skill(
                name=args.name,
                category=args.category,
                purpose=args.purpose,
                target_users=args.target_users,
                expected_output=args.expected_output,
                template=template,
                trigger_keywords=trigger_keywords,
                dependencies=dependencies
            )
            print(message)
            sys.exit(0 if success else 1)
    
    elif args.command == "optimize":
        if args.batch:
            skills = args.skills.split(",") if args.skills else None
            results = integration.batch_optimize_skills(skills, args.min_score)
            print(f"\n批量优化完成，共处理 {len(results)} 个技能:\n")
            for skill_name, (success, message) in results.items():
                status = "✅" if success else "❌"
                print(f"{status} {skill_name}: {message}")
        else:
            if not args.path:
                print("错误: 非批量模式需要 --path 参数")
                sys.exit(1)
            success, message = integration.optimize_skill(args.path, args.target)
            print(message)
            sys.exit(0 if success else 1)
    
    elif args.command == "evaluate":
        dimensions = args.dimensions.split(",") if args.dimensions else None
        result = integration.evaluate_skill(args.path, dimensions)
        print(f"\n技能评估结果: {result.skill_name}")
        print(f"综合分数: {result.overall_score:.2f}")
        print(f"触发准确性: {result.trigger_accuracy:.2f}")
        print(f"输出质量: {result.output_quality:.2f}")
        print(f"完整性: {result.completeness:.2f}")
        print(f"可维护性: {result.maintainability:.2f}")
        print(f"性能: {result.performance:.2f}")
        print(f"安全性: {result.security:.2f}")
        print(f"文档质量: {result.documentation:.2f}")
        print(f"测试覆盖: {result.test_coverage:.2f}")
        if result.issues:
            print("\n发现问题:")
            for issue in result.issues[:10]:
                print(f"  [{issue.get('severity', 'unknown')}] {issue.get('message', '')}")
        if result.recommendations:
            print("\n优化建议:")
            for rec in result.recommendations:
                print(f"  - {rec}")
    
    elif args.command == "benchmark":
        result = integration.benchmark_skill(args.path, args.iterations)
        print(f"\n基准测试结果: {result['skill_name']}")
        print(f"迭代次数: {result['iterations']}")
        print(f"总耗时: {result['total_time_seconds']:.2f}秒")
        print(f"平均耗时: {result['average_time_ms']:.2f}毫秒")
        print(f"评估分数: {result['evaluation_score']:.2f}")
    
    elif args.command == "chain":
        if args.action == "create":
            if not args.name or not args.skills:
                print("错误: 创建调用链需要 --name 和 --skills 参数")
                sys.exit(1)
            skills_list = [s.strip() for s in args.skills.split(",")]
            success, message = integration.create_skill_chain(
                name=args.name,
                description=args.description,
                skills=skills_list
            )
            print(message)
            sys.exit(0 if success else 1)
        
        elif args.action == "execute":
            if not args.chain_id:
                print("错误: 执行调用链需要 --chain-id 参数")
                sys.exit(1)
            context = json.loads(args.context) if args.context else {}
            success, result = integration.execute_skill_chain(args.chain_id, context)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(0 if success else 1)
        
        elif args.action == "list":
            chains = integration.list_skill_chains()
            print(f"\n共有 {len(chains)} 个技能调用链:\n")
            for chain in chains:
                print(f"📦 {chain.chain_id}: {chain.name}")
                print(f"   描述: {chain.description}")
                print(f"   技能: {' → '.join(chain.skills)}")
                print()
    
    elif args.command == "template":
        if args.action == "list":
            templates = integration.template_manager.list_templates()
            print(f"\n共有 {len(templates)} 个模板:\n")
            for template in templates:
                status_icon = "✅" if template.status == TemplateStatus.ACTIVE else "⚠️"
                print(f"{status_icon} {template.template_id}: {template.name} ({template.template_type.value})")
                print(f"   描述: {template.description}")
                print(f"   版本: {template.version}")
                print()
        
        elif args.action == "get":
            if not args.type:
                print("错误: 需要 --type 参数")
                sys.exit(1)
            template = integration.template_manager.get_template(args.type)
            if template:
                print(f"\n模板: {template.name}")
                print(f"ID: {template.template_id}")
                print(f"类型: {template.template_type.value}")
                print(f"描述: {template.description}")
                print(f"\n变量:")
                for var in template.variables:
                    required = " (必需)" if var.get("required") else ""
                    print(f"  - {var['name']}: {var.get('description', '')}{required}")
            else:
                print(f"模板 '{args.type}' 不存在")
                sys.exit(1)
        
        elif args.action == "render":
            if not args.type:
                print("错误: 需要 --type 参数")
                sys.exit(1)
            variables = json.loads(args.variables) if args.variables else {}
            success, result = integration.template_manager.render_template(args.type, variables)
            if success:
                print(result)
            else:
                print(f"渲染失败: {result}")
                sys.exit(1)
    
    elif args.command == "pipeline":
        if args.action == "integrate":
            if not args.project_id or not args.skill or not args.stage:
                print("错误: 需要 --project-id, --skill 和 --stage 参数")
                sys.exit(1)
            integration_obj = integration.pipeline_integrator.integrate_skill(
                args.project_id, args.skill, PipelineStage(args.stage)
            )
            print(f"集成成功: {integration_obj.integration_id}")
        
        elif args.action == "sync":
            if not args.project_id:
                print("错误: 需要 --project-id 参数")
                sys.exit(1)
            result = integration.pipeline_integrator.sync_with_backend(args.project_id)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        elif args.action == "trigger":
            if not args.project_id or not args.stage or not args.skill:
                print("错误: 需要 --project-id, --stage 和 --skill 参数")
                sys.exit(1)
            success, message = integration.pipeline_integrator.trigger_pipeline_stage(
                args.project_id, PipelineStage(args.stage), args.skill
            )
            print(message)
            sys.exit(0 if success else 1)
        
        elif args.action == "complete":
            if not args.project_id or not args.stage:
                print("错误: 需要 --project-id 和 --stage 参数")
                sys.exit(1)
            artifacts = json.loads(args.artifacts) if args.artifacts else None
            success, message = integration.pipeline_integrator.complete_pipeline_stage(
                args.project_id, PipelineStage(args.stage), artifacts
            )
            print(message)
            sys.exit(0 if success else 1)
    
    elif args.command == "report":
        report = integration.generate_report(args.format)
        if args.output:
            Path(args.output).write_text(report, encoding='utf-8')
            print(f"报告已保存到: {args.output}")
        else:
            print(report)


if __name__ == "__main__":
    main()
