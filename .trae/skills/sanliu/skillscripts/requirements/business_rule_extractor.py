#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强业务规则提取器
支持规则类型自动分类、规则库管理集成、规则验证机制
增强功能：语义分析、机器学习分类、批量操作、规则模板
"""

import re
import json
import logging
import sqlite3
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Tuple, Set, Callable
from enum import Enum
from datetime import datetime
from pathlib import Path
import hashlib
from abc import ABC, abstractmethod
from collections import Counter
import math


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RuleType(Enum):
    CONDITION_ACTION = "condition_action"
    VALIDATION = "validation"
    CALCULATION = "calculation"
    CONSTRAINT = "constraint"
    DERIVATION = "derivation"
    STATE_TRANSITION = "state_transition"
    WORKFLOW = "workflow"
    BUSINESS_LOGIC = "business_logic"
    SECURITY = "security"
    DATA_GOVERNANCE = "data_governance"
    COMPLIANCE = "compliance"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    ACCESS_CONTROL = "access_control"
    DATA_QUALITY = "data_quality"
    NOTIFICATION = "notification"
    SCHEDULING = "scheduling"
    TRANSFORMATION = "transformation"
    AGGREGATION = "aggregation"
    FILTERING = "filtering"


class RuleCategory(Enum):
    VALIDATION_RULE = "validation_rule"
    CALCULATION_RULE = "calculation_rule"
    WORKFLOW_RULE = "workflow_rule"
    DATA_RULE = "data_rule"
    SECURITY_RULE = "security_rule"
    INTEGRATION_RULE = "integration_rule"
    BUSINESS_LOGIC = "business_logic"
    COMPLIANCE_RULE = "compliance_rule"
    PERFORMANCE_RULE = "performance_rule"


class RulePriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RuleStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"


class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleSource(Enum):
    REQUIREMENT = "requirement"
    POLICY_DOCUMENT = "policy_document"
    REGULATION = "regulation"
    USER_INPUT = "user_input"
    AUTO_EXTRACTED = "auto_extracted"
    IMPORTED = "imported"


@dataclass
class RuleCondition:
    field: str
    operator: str
    value: Any
    description: Optional[str] = None
    logical_operator: str = "AND"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_expression(self) -> str:
        return f"{self.field} {self.operator} {repr(self.value)}"
    
    def validate(self) -> List[str]:
        errors = []
        if not self.field:
            errors.append("条件缺少字段名")
        if not self.operator:
            errors.append("条件缺少操作符")
        valid_operators = ['==', '!=', '>', '<', '>=', '<=', 'in', 'not in', 
                          'contains', 'matches', 'is null', 'is not null', 
                          'starts_with', 'ends_with', 'between']
        if self.operator not in valid_operators:
            errors.append(f"无效的操作符: {self.operator}")
        return errors


@dataclass
class RuleAction:
    action_type: str
    target: str
    value: Optional[Any] = None
    description: Optional[str] = None
    priority: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def validate(self) -> List[str]:
        errors = []
        if not self.action_type:
            errors.append("动作缺少类型")
        if not self.target:
            errors.append("动作缺少目标")
        valid_types = ['set', 'update', 'delete', 'create', 'send', 'trigger',
                      'validate', 'calculate', 'notify', 'block', 'allow', 'log']
        if self.action_type not in valid_types:
            errors.append(f"未知的动作类型: {self.action_type}")
        return errors


@dataclass
class ValidationRule:
    field: str
    validation_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def validate(self) -> List[str]:
        errors = []
        if not self.field:
            errors.append("验证规则缺少字段名")
        if not self.validation_type:
            errors.append("验证规则缺少验证类型")
        valid_types = ['required', 'type', 'format', 'range', 'length', 
                      'pattern', 'unique', 'custom', 'enum', 'min', 'max']
        if self.validation_type not in valid_types:
            errors.append(f"未知的验证类型: {self.validation_type}")
        return errors


@dataclass
class CalculationRule:
    result_field: str
    formula: str
    dependencies: List[str] = field(default_factory=list)
    description: Optional[str] = None
    precision: Optional[int] = None
    rounding_mode: str = "half_up"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def validate(self) -> List[str]:
        errors = []
        if not self.result_field:
            errors.append("计算规则缺少结果字段")
        if not self.formula:
            errors.append("计算规则缺少公式")
        try:
            compile(self.formula, '<string>', 'eval')
        except SyntaxError:
            errors.append(f"公式语法错误: {self.formula}")
        return errors


@dataclass
class WorkflowStep:
    step_id: str
    step_name: str
    action: str
    conditions: List[RuleCondition] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    is_start: bool = False
    is_end: bool = False
    timeout: Optional[int] = None
    assignee: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "action": self.action,
            "conditions": [c.to_dict() for c in self.conditions],
            "next_steps": self.next_steps,
            "is_start": self.is_start,
            "is_end": self.is_end,
            "timeout": self.timeout,
            "assignee": self.assignee
        }


@dataclass
class StateTransition:
    from_state: str
    to_state: str
    trigger: str
    guard_conditions: List[RuleCondition] = field(default_factory=list)
    actions: List[RuleAction] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_state": self.from_state,
            "to_state": self.to_state,
            "trigger": self.trigger,
            "guard_conditions": [c.to_dict() for c in self.guard_conditions],
            "actions": [a.to_dict() for a in self.actions]
        }


@dataclass
class ConstraintRule:
    constraint_type: str
    target: str
    constraint_value: Any
    scope: str = "global"
    description: Optional[str] = None
    enforcement: str = "strict"
    exception_conditions: List[RuleCondition] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint_type": self.constraint_type,
            "target": self.target,
            "constraint_value": self.constraint_value,
            "scope": self.scope,
            "description": self.description,
            "enforcement": self.enforcement,
            "exception_conditions": [c.to_dict() for c in self.exception_conditions]
        }
    
    def validate(self) -> List[str]:
        errors = []
        if not self.target:
            errors.append("约束规则缺少目标")
        if not self.constraint_type:
            errors.append("约束规则缺少约束类型")
        valid_types = ['unique', 'referential', 'check', 'not_null', 'range', 
                      'enum', 'format', 'business_hours', 'geographic', 'temporal']
        if self.constraint_type not in valid_types:
            errors.append(f"未知的约束类型: {self.constraint_type}")
        return errors


@dataclass
class DerivationRule:
    source_fields: List[str]
    target_field: str
    derivation_logic: str
    derivation_type: str = "computed"
    is_deterministic: bool = True
    cache_strategy: str = "none"
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_fields": self.source_fields,
            "target_field": self.target_field,
            "derivation_logic": self.derivation_logic,
            "derivation_type": self.derivation_type,
            "is_deterministic": self.is_deterministic,
            "cache_strategy": self.cache_strategy,
            "description": self.description
        }
    
    def validate(self) -> List[str]:
        errors = []
        if not self.source_fields:
            errors.append("派生规则缺少源字段")
        if not self.target_field:
            errors.append("派生规则缺少目标字段")
        if not self.derivation_logic:
            errors.append("派生规则缺少派生逻辑")
        return errors


@dataclass
class DataGovernanceRule:
    governance_type: str
    data_entity: str
    policies: Dict[str, Any] = field(default_factory=dict)
    retention_period: Optional[int] = None
    access_level: str = "standard"
    compliance_tags: List[str] = field(default_factory=list)
    data_classification: str = "internal"
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "governance_type": self.governance_type,
            "data_entity": self.data_entity,
            "policies": self.policies,
            "retention_period": self.retention_period,
            "access_level": self.access_level,
            "compliance_tags": self.compliance_tags,
            "data_classification": self.data_classification,
            "description": self.description
        }
    
    def validate(self) -> List[str]:
        errors = []
        if not self.data_entity:
            errors.append("数据治理规则缺少数据实体")
        if not self.governance_type:
            errors.append("数据治理规则缺少治理类型")
        valid_types = ['retention', 'access', 'privacy', 'encryption', 
                      'masking', 'anonymization', 'audit', 'backup']
        if self.governance_type not in valid_types:
            errors.append(f"未知的治理类型: {self.governance_type}")
        return errors


@dataclass
class NotificationRule:
    trigger_event: str
    recipients: List[str]
    notification_type: str
    template: Optional[str] = None
    conditions: List[RuleCondition] = field(default_factory=list)
    priority: str = "normal"
    channel: str = "email"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_event": self.trigger_event,
            "recipients": self.recipients,
            "notification_type": self.notification_type,
            "template": self.template,
            "conditions": [c.to_dict() for c in self.conditions],
            "priority": self.priority,
            "channel": self.channel
        }
    
    def validate(self) -> List[str]:
        errors = []
        if not self.trigger_event:
            errors.append("通知规则缺少触发事件")
        if not self.recipients:
            errors.append("通知规则缺少接收者")
        valid_channels = ['email', 'sms', 'push', 'webhook', 'in_app']
        if self.channel not in valid_channels:
            errors.append(f"未知的通知渠道: {self.channel}")
        return errors


@dataclass
class SchedulingRule:
    task_name: str
    schedule_expression: str
    timezone: str = "UTC"
    enabled: bool = True
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_name": self.task_name,
            "schedule_expression": self.schedule_expression,
            "timezone": self.timezone,
            "enabled": self.enabled,
            "retry_policy": self.retry_policy,
            "dependencies": self.dependencies,
            "timeout": self.timeout
        }
    
    def validate(self) -> List[str]:
        errors = []
        if not self.task_name:
            errors.append("调度规则缺少任务名称")
        if not self.schedule_expression:
            errors.append("调度规则缺少调度表达式")
        return errors


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    severity: ValidationSeverity = ValidationSeverity.INFO
    score: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "severity": self.severity.value,
            "score": self.score
        }


@dataclass
class BusinessRule:
    id: str
    name: str
    rule_type: RuleType
    category: RuleCategory
    description: str
    source_text: str
    conditions: List[RuleCondition] = field(default_factory=list)
    actions: List[RuleAction] = field(default_factory=list)
    validation_rules: List[ValidationRule] = field(default_factory=list)
    calculation_rules: List[CalculationRule] = field(default_factory=list)
    workflow_steps: List[WorkflowStep] = field(default_factory=list)
    state_transitions: List[StateTransition] = field(default_factory=list)
    constraint_rules: List[ConstraintRule] = field(default_factory=list)
    derivation_rules: List[DerivationRule] = field(default_factory=list)
    data_governance_rules: List[DataGovernanceRule] = field(default_factory=list)
    notification_rules: List[NotificationRule] = field(default_factory=list)
    scheduling_rules: List[SchedulingRule] = field(default_factory=list)
    priority: RulePriority = RulePriority.MEDIUM
    status: RuleStatus = RuleStatus.ACTIVE
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence_score: float = 1.0
    auto_classified: bool = False
    source: RuleSource = RuleSource.AUTO_EXTRACTED
    parent_rule_id: Optional[str] = None
    related_rules: List[str] = field(default_factory=list)
    secondary_categories: List[RuleCategory] = field(default_factory=list)
    classification_explanation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "rule_type": self.rule_type.value,
            "category": self.category.value,
            "description": self.description,
            "source_text": self.source_text,
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "validation_rules": [v.to_dict() for v in self.validation_rules],
            "calculation_rules": [c.to_dict() for c in self.calculation_rules],
            "workflow_steps": [w.to_dict() for w in self.workflow_steps],
            "state_transitions": [s.to_dict() for s in self.state_transitions],
            "constraint_rules": [c.to_dict() for c in self.constraint_rules],
            "derivation_rules": [d.to_dict() for d in self.derivation_rules],
            "data_governance_rules": [d.to_dict() for d in self.data_governance_rules],
            "notification_rules": [n.to_dict() for n in self.notification_rules],
            "scheduling_rules": [s.to_dict() for s in self.scheduling_rules],
            "priority": self.priority.value,
            "status": self.status.value,
            "tags": self.tags,
            "metadata": self.metadata,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "confidence_score": self.confidence_score,
            "auto_classified": self.auto_classified,
            "source": self.source.value,
            "parent_rule_id": self.parent_rule_id,
            "related_rules": self.related_rules,
            "secondary_categories": [c.value for c in self.secondary_categories],
            "classification_explanation": self.classification_explanation
        }
    
    def validate(self) -> ValidationResult:
        errors = []
        warnings = []
        
        if not self.name:
            errors.append("规则缺少名称")
        if not self.description:
            warnings.append("规则缺少描述")
        if not self.source_text:
            warnings.append("规则缺少源文本")
        
        for cond in self.conditions:
            errors.extend(cond.validate())
        
        for action in self.actions:
            errors.extend(action.validate())
        
        for val_rule in self.validation_rules:
            errors.extend(val_rule.validate())
        
        for calc_rule in self.calculation_rules:
            errors.extend(calc_rule.validate())
        
        for constraint_rule in self.constraint_rules:
            errors.extend(constraint_rule.validate())
        
        for derivation_rule in self.derivation_rules:
            errors.extend(derivation_rule.validate())
        
        for gov_rule in self.data_governance_rules:
            errors.extend(gov_rule.validate())
        
        for notif_rule in self.notification_rules:
            errors.extend(notif_rule.validate())
        
        for sched_rule in self.scheduling_rules:
            errors.extend(sched_rule.validate())
        
        has_content = (
            self.conditions or self.actions or 
            self.validation_rules or self.calculation_rules or
            self.workflow_steps or self.state_transitions or
            self.constraint_rules or self.derivation_rules or
            self.data_governance_rules or self.notification_rules or
            self.scheduling_rules
        )
        if not has_content:
            errors.append("规则缺少具体内容")
        
        if self.workflow_steps:
            start_steps = [s for s in self.workflow_steps if s.is_start]
            if len(start_steps) == 0:
                warnings.append("工作流缺少起始步骤")
            elif len(start_steps) > 1:
                errors.append("工作流有多个起始步骤")
        
        severity = ValidationSeverity.ERROR if errors else (
            ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO
        )
        
        score = 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.05)
        score = max(0.0, min(1.0, score))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            severity=severity,
            score=score
        )
    
    def get_content_hash(self) -> str:
        content = {
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "validation_rules": [v.to_dict() for v in self.validation_rules],
            "calculation_rules": [c.to_dict() for c in self.calculation_rules],
            "workflow_steps": [w.to_dict() for w in self.workflow_steps],
            "state_transitions": [s.to_dict() for s in self.state_transitions],
            "constraint_rules": [c.to_dict() for c in self.constraint_rules],
            "derivation_rules": [d.to_dict() for d in self.derivation_rules],
            "data_governance_rules": [d.to_dict() for d in self.data_governance_rules],
            "notification_rules": [n.to_dict() for n in self.notification_rules],
            "scheduling_rules": [s.to_dict() for s in self.scheduling_rules]
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def get_complexity_score(self) -> float:
        score = 0.0
        score += len(self.conditions) * 0.1
        score += len(self.actions) * 0.15
        score += len(self.validation_rules) * 0.1
        score += len(self.calculation_rules) * 0.2
        score += len(self.workflow_steps) * 0.15
        score += len(self.state_transitions) * 0.2
        score += len(self.constraint_rules) * 0.15
        score += len(self.derivation_rules) * 0.2
        score += len(self.data_governance_rules) * 0.15
        score += len(self.notification_rules) * 0.1
        score += len(self.scheduling_rules) * 0.1
        
        for calc in self.calculation_rules:
            score += len(calc.dependencies) * 0.05
        
        for deriv in self.derivation_rules:
            score += len(deriv.source_fields) * 0.05
        
        return min(score, 1.0)


class SemanticAnalyzer:
    SEMANTIC_PATTERNS = {
        'temporal': [
            (re.compile(r'(?:在|于|当)\s*(\d+[年月日天时分秒]+)(?:之前|之后|时)', re.IGNORECASE), 'time_constraint'),
            (re.compile(r'(?:每天|每周|每月|每年|定期)', re.IGNORECASE), 'periodic'),
            (re.compile(r'(?:立即|马上|实时)', re.IGNORECASE), 'immediate'),
        ],
        'spatial': [
            (re.compile(r'(?:在|位于)\s*(.+?)(?:地区|区域|位置)', re.IGNORECASE), 'location'),
            (re.compile(r'(?:全国|全省|全市|本地)', re.IGNORECASE), 'region'),
        ],
        'actor': [
            (re.compile(r'(?:用户|客户|管理员|系统|操作员)\s*(.+?)(?:可以|必须|需要)', re.IGNORECASE), 'user_action'),
            (re.compile(r'(?:由|被)\s*(.+?)(?:负责|处理|审批)', re.IGNORECASE), 'responsible'),
        ],
        'quantitative': [
            (re.compile(r'(?:超过|大于|多于)\s*(\d+(?:\.\d+)?)\s*(%|个|次|元)?', re.IGNORECASE), 'threshold'),
            (re.compile(r'(?:少于|小于|低于)\s*(\d+(?:\.\d+)?)\s*(%|个|次|元)?', re.IGNORECASE), 'threshold'),
            (re.compile(r'(?:等于|为)\s*(\d+(?:\.\d+)?)\s*(%|个|次|元)?', re.IGNORECASE), 'exact_value'),
        ],
        'conditional': [
            (re.compile(r'(?:如果|当|若|一旦)\s*(.+?)\s*(?:则|那么|就)', re.IGNORECASE), 'if_then'),
            (re.compile(r'(?:除非|除了)\s*(.+?)', re.IGNORECASE), 'unless'),
            (re.compile(r'(?:只有|仅当)\s*(.+?)\s*(?:才)', re.IGNORECASE), 'only_if'),
        ],
        'exception': [
            (re.compile(r'(?:除非|除了|例外)\s*(.+?)', re.IGNORECASE), 'exception'),
            (re.compile(r'(?:特殊情况|异常情况|错误情况)\s*(?:下)?(.+?)', re.IGNORECASE), 'error_handling'),
        ],
    }
    
    def analyze(self, text: str) -> Dict[str, Any]:
        result = {
            'temporal': [],
            'spatial': [],
            'actor': [],
            'quantitative': [],
            'conditional': [],
            'exception': [],
            'keywords': self._extract_keywords(text),
            'entities': self._extract_entities(text),
            'complexity': self._calculate_complexity(text)
        }
        
        for category, patterns in self.SEMANTIC_PATTERNS.items():
            for pattern, semantic_type in patterns:
                matches = pattern.findall(text)
                for match in matches:
                    result[category].append({
                        'type': semantic_type,
                        'value': match if isinstance(match, str) else match[0] if match else '',
                        'pattern': pattern.pattern
                    })
        
        return result
    
    def _extract_keywords(self, text: str) -> List[str]:
        keywords = []
        
        important_patterns = [
            r'(?:必须|需要|应该|shall|must|should)',
            r'(?:禁止|不允许|不能|forbidden|not allowed)',
            r'(?:验证|检查|校验|validate|check|verify)',
            r'(?:计算|求|等于|calculate|compute|equals)',
            r'(?:流程|步骤|状态|workflow|process|state)',
        ]
        
        for pattern in important_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                keywords.append(pattern.split('|')[0].replace('(?:', ''))
        
        return list(set(keywords))
    
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        entities = []
        
        field_pattern = re.compile(r'["\']?([a-zA-Z_][a-zA-Z0-9_]*)["\']?(?:字段|属性|列)', re.IGNORECASE)
        for match in field_pattern.finditer(text):
            entities.append({'type': 'field', 'value': match.group(1)})
        
        table_pattern = re.compile(r'(?:表|实体|模型)\s*["\']?([a-zA-Z_][a-zA-Z0-9_]*)["\']?', re.IGNORECASE)
        for match in table_pattern.finditer(text):
            entities.append({'type': 'table', 'value': match.group(1)})
        
        number_pattern = re.compile(r'\b(\d+(?:\.\d+)?)\b')
        for match in number_pattern.finditer(text):
            entities.append({'type': 'number', 'value': match.group(1)})
        
        return entities
    
    def _calculate_complexity(self, text: str) -> float:
        score = 0.0
        
        score += text.count('如果') + text.count('当') + text.count('if')
        score += text.count('否则') + text.count('else')
        score += text.count('并且') + text.count('或者') + text.count('and') + text.count('or')
        score += len(re.findall(r'\d+', text)) * 0.5
        
        words = text.split()
        score += len(words) / 100
        
        return min(score / 10, 1.0)


class RuleTypeClassifier:
    VALIDATION_KEYWORDS = [
        "必须", "需要", "不能", "不可", "不允许", "禁止", "验证", "检查", "校验",
        "格式", "长度", "范围", "唯一", "非空", "必填", "must", "should", "validate",
        "check", "verify", "required", "unique", "not null", "not empty", "constraint"
    ]
    
    CALCULATION_KEYWORDS = [
        "计算", "求", "等于", "公式", "乘以", "除以", "加上", "减去", "合计", "总计",
        "平均值", "最大值", "最小值", "calculate", "compute", "formula", "sum",
        "average", "max", "min", "total", "multiply", "divide", "add", "subtract"
    ]
    
    WORKFLOW_KEYWORDS = [
        "流程", "步骤", "状态", "转换", "审批", "流转", "开始", "结束", "下一步",
        "如果", "当", "则", "否则", "workflow", "process", "step", "state",
        "transition", "approve", "flow", "then", "else", "next"
    ]
    
    SECURITY_KEYWORDS = [
        "安全", "权限", "认证", "授权", "加密", "解密", "密码", "登录", "访问控制",
        "security", "permission", "authentication", "authorization", "encrypt",
        "decrypt", "password", "login", "access control"
    ]
    
    COMPLIANCE_KEYWORDS = [
        "合规", "法规", "政策", "审计", "监管", "标准", "规范", "compliance",
        "regulation", "policy", "audit", "standard", "gdpr", "iso"
    ]
    
    CONDITION_ACTION_KEYWORDS = [
        "如果", "当", "若", "则", "那么", "就", "if", "when", "then",
        "trigger", "execute", "perform"
    ]
    
    CONSTRAINT_KEYWORDS = [
        "约束", "限制", "唯一", "外键", "引用", "完整性", "constraint", "unique",
        "foreign key", "reference", "integrity", "限制条件", "边界"
    ]
    
    DATA_GOVERNANCE_KEYWORDS = [
        "数据治理", "数据质量", "数据保留", "数据隐私", "脱敏", "加密存储",
        "data governance", "data quality", "retention", "privacy", "masking",
        "数据生命周期", "数据安全", "敏感数据"
    ]
    
    NOTIFICATION_KEYWORDS = [
        "通知", "提醒", "发送", "邮件", "短信", "推送", "告警", "notification",
        "alert", "email", "sms", "push", "消息", "告知"
    ]
    
    SCHEDULING_KEYWORDS = [
        "定时", "调度", "周期", "每天", "每周", "每月", "cron", "schedule",
        "定期执行", "自动运行", "计划任务", "batch", "批处理"
    ]
    
    INTEGRATION_KEYWORDS = [
        "集成", "接口", "API", "同步", "调用", "integration", "interface",
        "sync", "webhook", "第三方", "外部系统"
    ]
    
    PERFORMANCE_KEYWORDS = [
        "性能", "响应时间", "超时", "缓存", "优化", "performance", "timeout",
        "cache", "latency", "吞吐量", "并发"
    ]
    
    def __init__(self):
        self._classification_rules: List[Callable] = []
        self._semantic_analyzer = SemanticAnalyzer()
        self._setup_classification_rules()
    
    def _setup_classification_rules(self):
        self._classification_rules = [
            self._classify_by_validation_patterns,
            self._classify_by_calculation_patterns,
            self._classify_by_workflow_patterns,
            self._classify_by_security_patterns,
            self._classify_by_compliance_patterns,
            self._classify_by_condition_action_patterns,
            self._classify_by_state_patterns,
            self._classify_by_constraint_patterns,
            self._classify_by_data_governance_patterns,
            self._classify_by_notification_patterns,
            self._classify_by_scheduling_patterns,
            self._classify_by_integration_patterns,
            self._classify_by_performance_patterns,
        ]
    
    def _count_keywords(self, text: str, keywords: List[str]) -> int:
        text_lower = text.lower()
        count = 0
        for keyword in keywords:
            count += text_lower.count(keyword.lower())
        return count
    
    def _classify_by_validation_patterns(self, text: str, rule: BusinessRule) -> Tuple[float, Optional[RuleCategory]]:
        if rule.validation_rules:
            return (0.95, RuleCategory.VALIDATION_RULE)
        
        validation_patterns = [
            r'(.+?)\s*(?:必须|需要)\s*(?:是|为)\s*(.+?)(?:，|。|$)',
            r'(.+?)\s*(?:不能|不可|不允许)\s*(?:为空|为null)',
            r'(.+?)\s*(?:长度|位数)\s*(?:必须|需要)',
            r'(.+?)\s*(?:必须|需要)\s*(?:唯一)',
            r'(.+?)\s*(?:格式|类型)\s*(?:必须|需要)\s*(?:符合|为)',
        ]
        
        for pattern in validation_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return (0.85, RuleCategory.VALIDATION_RULE)
        
        count = self._count_keywords(text, self.VALIDATION_KEYWORDS)
        if count >= 3:
            return (0.8, RuleCategory.VALIDATION_RULE)
        elif count >= 2:
            return (0.65, RuleCategory.VALIDATION_RULE)
        elif count == 1:
            return (0.45, RuleCategory.VALIDATION_RULE)
        
        return (0.0, None)
    
    def _classify_by_calculation_patterns(self, text: str, rule: BusinessRule) -> Tuple[float, Optional[RuleCategory]]:
        if rule.calculation_rules:
            return (0.95, RuleCategory.CALCULATION_RULE)
        
        calc_patterns = [
            r'(.+?)\s*(?:等于|为|=)\s*(.+?)(?:之和|积|的结果)',
            r'(?:计算|求)\s*(.+?)\s*(?:公式|方法)\s*(?:为|:|：)',
            r'(.+?)\s*=\s*(.+?)(?:，|。|$)',
            r'(?:总金额|总数量|合计)\s*(?:为|等于)',
        ]
        
        for pattern in calc_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return (0.85, RuleCategory.CALCULATION_RULE)
        
        count = self._count_keywords(text, self.CALCULATION_KEYWORDS)
        if count >= 2:
            return (0.7, RuleCategory.CALCULATION_RULE)
        elif count == 1:
            return (0.5, RuleCategory.CALCULATION_RULE)
        
        return (0.0, None)
    
    def _classify_by_workflow_patterns(self, text: str, rule: BusinessRule) -> Tuple[float, Optional[RuleCategory]]:
        if rule.workflow_steps:
            return (0.95, RuleCategory.WORKFLOW_RULE)
        
        workflow_patterns = [
            r'(?:流程|过程)\s*(?:包括|包含|分为)',
            r'(?:步骤|阶段)\s*\d+',
            r'(?:状态)\s*(?:转换|变更|变为)',
            r'(?:审批|审核)\s*(?:流程|通过|拒绝)',
        ]
        
        for pattern in workflow_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return (0.85, RuleCategory.WORKFLOW_RULE)
        
        count = self._count_keywords(text, self.WORKFLOW_KEYWORDS)
        if count >= 3:
            return (0.7, RuleCategory.WORKFLOW_RULE)
        elif count >= 2:
            return (0.5, RuleCategory.WORKFLOW_RULE)
        
        return (0.0, None)
    
    def _classify_by_security_patterns(self, text: str, rule: BusinessRule) -> Tuple[float, Optional[RuleCategory]]:
        security_patterns = [
            r'(?:密码|口令)\s*(?:必须|需要|长度)',
            r'(?:登录|认证)\s*(?:失败|成功)',
            r'(?:权限|授权)\s*(?:检查|验证)',
            r'(?:加密|解密)\s*(?:算法|方式)',
        ]
        
        for pattern in security_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return (0.9, RuleCategory.SECURITY_RULE)
        
        count = self._count_keywords(text, self.SECURITY_KEYWORDS)
        if count >= 2:
            return (0.8, RuleCategory.SECURITY_RULE)
        elif count == 1:
            return (0.5, RuleCategory.SECURITY_RULE)
        
        return (0.0, None)
    
    def _classify_by_compliance_patterns(self, text: str, rule: BusinessRule) -> Tuple[float, Optional[RuleCategory]]:
        compliance_patterns = [
            r'(?:符合|遵守)\s*(.+?)(?:标准|规范|法规)',
            r'(?:审计|监管)\s*(?:要求|检查)',
            r'(?:数据保留|隐私保护)',
        ]
        
        for pattern in compliance_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return (0.9, RuleCategory.COMPLIANCE_RULE)
        
        count = self._count_keywords(text, self.COMPLIANCE_KEYWORDS)
        if count >= 2:
            return (0.8, RuleCategory.COMPLIANCE_RULE)
        elif count == 1:
            return (0.5, RuleCategory.COMPLIANCE_RULE)
        
        return (0.0, None)
    
    def _classify_by_condition_action_patterns(self, text: str, rule: BusinessRule) -> Tuple[float, Optional[RuleCategory]]:
        if rule.conditions and rule.actions:
            return (0.9, RuleCategory.BUSINESS_LOGIC)
        
        cond_action_patterns = [
            r'(?:如果|当|若)\s*(.+?)\s*(?:则|那么|就)',
            r'if\s+(.+?)\s+then',
        ]
        
        for pattern in cond_action_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return (0.8, RuleCategory.BUSINESS_LOGIC)
        
        count = self._count_keywords(text, self.CONDITION_ACTION_KEYWORDS)
        if count >= 2:
            return (0.6, RuleCategory.BUSINESS_LOGIC)
        
        return (0.0, None)
    
    def _classify_by_state_patterns(self, text: str, rule: BusinessRule) -> Tuple[float, Optional[RuleCategory]]:
        if rule.state_transitions:
            return (0.95, RuleCategory.WORKFLOW_RULE)
        
        state_patterns = [
            r'(?:状态)\s*(?:从|由)\s*(.+?)\s*(?:变为|转换为|变更)\s*(.+?)',
            r'(?:当|当且仅当)\s*(.+?)\s*(?:状态)\s*(?:为|是)',
        ]
        
        for pattern in state_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return (0.85, RuleCategory.WORKFLOW_RULE)
        
        return (0.0, None)
    
    def _classify_by_constraint_patterns(self, text: str, rule: BusinessRule) -> Tuple[float, Optional[RuleCategory]]:
        if rule.constraint_rules:
            return (0.95, RuleCategory.DATA_RULE)
        
        constraint_patterns = [
            r'(.+?)\s*(?:必须|需要)\s*(?:唯一)',
            r'(.+?)\s*(?:引用|关联)\s*(.+?)',
            r'(?:外键|主键)\s*(?:约束|关系)',
            r'(.+?)\s*(?:取值范围|允许值)',
        ]
        
        for pattern in constraint_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return (0.85, RuleCategory.DATA_RULE)
        
        count = self._count_keywords(text, self.CONSTRAINT_KEYWORDS)
        if count >= 2:
            return (0.7, RuleCategory.DATA_RULE)
        elif count == 1:
            return (0.5, RuleCategory.DATA_RULE)
        
        return (0.0, None)
    
    def _classify_by_data_governance_patterns(self, text: str, rule: BusinessRule) -> Tuple[float, Optional[RuleCategory]]:
        if rule.data_governance_rules:
            return (0.95, RuleCategory.DATA_RULE)
        
        gov_patterns = [
            r'(?:数据|信息)\s*(?:保留|存储)\s*(?:期限|时间)',
            r'(?:敏感|隐私)\s*(?:数据|信息)',
            r'(?:脱敏|加密)\s*(?:处理|存储)',
            r'(?:数据质量|数据治理)',
        ]
        
        for pattern in gov_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return (0.9, RuleCategory.DATA_RULE)
        
        count = self._count_keywords(text, self.DATA_GOVERNANCE_KEYWORDS)
        if count >= 2:
            return (0.8, RuleCategory.DATA_RULE)
        elif count == 1:
            return (0.5, RuleCategory.DATA_RULE)
        
        return (0.0, None)
    
    def _classify_by_notification_patterns(self, text: str, rule: BusinessRule) -> Tuple[float, Optional[RuleCategory]]:
        if rule.notification_rules:
            return (0.95, RuleCategory.INTEGRATION_RULE)
        
        notif_patterns = [
            r'(?:发送|推送)\s*(.+?)\s*(?:邮件|短信|通知)',
            r'(?:当|如果)\s*(.+?)\s*(?:通知|告知|提醒)',
            r'(?:告警|预警)\s*(?:规则|条件)',
        ]
        
        for pattern in notif_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return (0.85, RuleCategory.INTEGRATION_RULE)
        
        count = self._count_keywords(text, self.NOTIFICATION_KEYWORDS)
        if count >= 2:
            return (0.7, RuleCategory.INTEGRATION_RULE)
        elif count == 1:
            return (0.5, RuleCategory.INTEGRATION_RULE)
        
        return (0.0, None)
    
    def _classify_by_scheduling_patterns(self, text: str, rule: BusinessRule) -> Tuple[float, Optional[RuleCategory]]:
        if rule.scheduling_rules:
            return (0.95, RuleCategory.PERFORMANCE_RULE)
        
        sched_patterns = [
            r'(?:每天|每周|每月|每年)\s*(.+?)\s*(?:执行|运行)',
            r'(?:定时|定期)\s*(?:执行|运行|检查)',
            r'(?:cron|schedule)\s*(?:表达式|规则)',
        ]
        
        for pattern in sched_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return (0.85, RuleCategory.PERFORMANCE_RULE)
        
        count = self._count_keywords(text, self.SCHEDULING_KEYWORDS)
        if count >= 2:
            return (0.7, RuleCategory.PERFORMANCE_RULE)
        elif count == 1:
            return (0.5, RuleCategory.PERFORMANCE_RULE)
        
        return (0.0, None)
    
    def _classify_by_integration_patterns(self, text: str, rule: BusinessRule) -> Tuple[float, Optional[RuleCategory]]:
        integration_patterns = [
            r'(?:调用|请求)\s*(.+?)\s*(?:接口|API)',
            r'(?:同步|集成)\s*(.+?)\s*(?:数据|信息)',
            r'(?:第三方|外部)\s*(?:系统|服务)',
        ]
        
        for pattern in integration_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return (0.85, RuleCategory.INTEGRATION_RULE)
        
        count = self._count_keywords(text, self.INTEGRATION_KEYWORDS)
        if count >= 2:
            return (0.7, RuleCategory.INTEGRATION_RULE)
        elif count == 1:
            return (0.5, RuleCategory.INTEGRATION_RULE)
        
        return (0.0, None)
    
    def _classify_by_performance_patterns(self, text: str, rule: BusinessRule) -> Tuple[float, Optional[RuleCategory]]:
        perf_patterns = [
            r'(?:响应|处理)\s*(?:时间|超时)',
            r'(?:缓存|cache)\s*(?:策略|规则)',
            r'(?:性能|吞吐量)\s*(?:要求|指标)',
        ]
        
        for pattern in perf_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return (0.85, RuleCategory.PERFORMANCE_RULE)
        
        count = self._count_keywords(text, self.PERFORMANCE_KEYWORDS)
        if count >= 2:
            return (0.7, RuleCategory.PERFORMANCE_RULE)
        elif count == 1:
            return (0.5, RuleCategory.PERFORMANCE_RULE)
        
        return (0.0, None)
    
    def classify(self, rule: BusinessRule) -> Tuple[RuleCategory, float]:
        text = rule.source_text or rule.description or ""
        best_category = RuleCategory.BUSINESS_LOGIC
        best_confidence = 0.0
        explanations = []
        
        semantic_result = self._semantic_analyzer.analyze(text)
        if semantic_result['conditional']:
            best_confidence = 0.3
            explanations.append("检测到条件语句")
        
        for classify_func in self._classification_rules:
            confidence, category = classify_func(text, rule)
            if category and confidence > best_confidence:
                best_confidence = confidence
                best_category = category
                explanations = [f"匹配{classify_func.__name__}模式 (置信度: {confidence:.2f})"]
        
        if best_confidence < 0.3:
            best_category = RuleCategory.BUSINESS_LOGIC
            best_confidence = 0.3
            explanations.append("默认分类为业务逻辑")
        
        return (best_category, best_confidence)
    
    def classify_multi_label(self, rule: BusinessRule, threshold: float = 0.5) -> List[Tuple[RuleCategory, float]]:
        text = rule.source_text or rule.description or ""
        results = []
        
        for classify_func in self._classification_rules:
            confidence, category = classify_func(text, rule)
            if category and confidence >= threshold:
                results.append((category, confidence))
        
        results.sort(key=lambda x: x[1], reverse=True)
        
        if not results:
            results.append((RuleCategory.BUSINESS_LOGIC, 0.3))
        
        return results
    
    def auto_classify_rule(self, rule: BusinessRule, multi_label: bool = False) -> BusinessRule:
        if multi_label:
            categories = self.classify_multi_label(rule)
            if categories:
                rule.category = categories[0][0]
                rule.confidence_score = categories[0][1]
                rule.secondary_categories = [c[0] for c in categories[1:]]
                rule.classification_explanation = f"多标签分类: {', '.join([f'{c[0].value}({c[1]:.2f})' for c in categories])}"
        else:
            category, confidence = self.classify(rule)
            rule.category = category
            rule.confidence_score = confidence
            rule.classification_explanation = f"主分类: {category.value} (置信度: {confidence:.2f})"
        
        rule.auto_classified = True
        return rule
    
    def classify_batch(self, rules: List[BusinessRule]) -> Dict[str, Tuple[RuleCategory, float]]:
        results = {}
        for rule in rules:
            results[rule.id] = self.classify(rule)
        return results


class RuleLibraryIntegration:
    def __init__(self, db_path: str = "rule_library.db"):
        self.db_path = db_path
        self._init_database()
        logger.info(f"规则库初始化完成: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                source_text TEXT,
                content TEXT NOT NULL,
                tags TEXT,
                status TEXT DEFAULT 'active',
                priority TEXT DEFAULT 'medium',
                current_version INTEGER DEFAULT 1,
                confidence_score REAL DEFAULT 1.0,
                auto_classified INTEGER DEFAULT 0,
                source TEXT DEFAULT 'auto_extracted',
                parent_rule_id TEXT,
                related_rules TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                rule_data TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                change_type TEXT NOT NULL,
                change_description TEXT,
                changed_by TEXT,
                UNIQUE(rule_id, version),
                FOREIGN KEY (rule_id) REFERENCES rules(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (rule_id) REFERENCES rules(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                template_content TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT NOT NULL,
                depends_on_rule_id TEXT NOT NULL,
                dependency_type TEXT DEFAULT 'requires',
                created_at TEXT NOT NULL,
                FOREIGN KEY (rule_id) REFERENCES rules(id),
                FOREIGN KEY (depends_on_rule_id) REFERENCES rules(id),
                UNIQUE(rule_id, depends_on_rule_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_lifecycle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT NOT NULL,
                from_status TEXT,
                to_status TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                changed_by TEXT,
                reason TEXT,
                FOREIGN KEY (rule_id) REFERENCES rules(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id1 TEXT NOT NULL,
                rule_id2 TEXT NOT NULL,
                conflict_type TEXT NOT NULL,
                severity TEXT DEFAULT 'warning',
                description TEXT,
                detected_at TEXT NOT NULL,
                resolved INTEGER DEFAULT 0,
                FOREIGN KEY (rule_id1) REFERENCES rules(id),
                FOREIGN KEY (rule_id2) REFERENCES rules(id)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rules_category ON rules(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rules_status ON rules(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rules_type ON rules(rule_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rule_tags_tag ON rule_tags(tag)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rules_source ON rules(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rules_parent ON rules(parent_rule_id)')
        
        conn.commit()
        conn.close()
    
    def store_rule(self, rule: BusinessRule, changed_by: str = "system") -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            content = {
                "conditions": [c.to_dict() for c in rule.conditions],
                "actions": [a.to_dict() for a in rule.actions],
                "validation_rules": [v.to_dict() for v in rule.validation_rules],
                "calculation_rules": [c.to_dict() for c in rule.calculation_rules],
                "workflow_steps": [w.to_dict() for w in rule.workflow_steps],
                "state_transitions": [s.to_dict() for s in rule.state_transitions],
                "constraint_rules": [c.to_dict() for c in rule.constraint_rules],
                "derivation_rules": [d.to_dict() for d in rule.derivation_rules],
                "data_governance_rules": [d.to_dict() for d in rule.data_governance_rules],
                "notification_rules": [n.to_dict() for n in rule.notification_rules],
                "scheduling_rules": [s.to_dict() for s in rule.scheduling_rules]
            }
            
            cursor.execute('''
                INSERT OR REPLACE INTO rules 
                (id, name, rule_type, category, description, source_text, content, tags, 
                 status, priority, current_version, confidence_score, auto_classified, 
                 source, parent_rule_id, related_rules, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule.id, rule.name, rule.rule_type.value, rule.category.value,
                rule.description, rule.source_text, json.dumps(content, ensure_ascii=False),
                json.dumps(rule.tags, ensure_ascii=False), rule.status.value,
                rule.priority.value, rule.version, rule.confidence_score,
                1 if rule.auto_classified else 0, rule.source.value,
                rule.parent_rule_id, json.dumps(rule.related_rules, ensure_ascii=False),
                rule.created_at, rule.updated_at,
                json.dumps(rule.metadata, ensure_ascii=False)
            ))
            
            cursor.execute('DELETE FROM rule_tags WHERE rule_id = ?', (rule.id,))
            for tag in rule.tags:
                cursor.execute('INSERT INTO rule_tags (rule_id, tag) VALUES (?, ?)',
                             (rule.id, tag))
            
            cursor.execute('''
                INSERT INTO rule_versions (rule_id, version, rule_data, changed_at, change_type, change_description, changed_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (rule.id, rule.version, json.dumps(rule.to_dict(), ensure_ascii=False),
                  datetime.now().isoformat(), 'create', '规则存储', changed_by))
            
            conn.commit()
            conn.close()
            
            logger.info(f"规则存储成功: {rule.id} - {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"规则存储失败: {e}")
            return False
    
    def store_rules_batch(self, rules: List[BusinessRule], changed_by: str = "system") -> Dict[str, bool]:
        results = {}
        for rule in rules:
            results[rule.id] = self.store_rule(rule, changed_by)
        return results
    
    def get_rule(self, rule_id: str) -> Optional[BusinessRule]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM rules WHERE id = ?', (rule_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_rule(row)
            return None
            
        except Exception as e:
            logger.error(f"获取规则失败: {e}")
            return None
    
    def _row_to_rule(self, row: sqlite3.Row) -> BusinessRule:
        content = json.loads(row['content'])
        
        return BusinessRule(
            id=row['id'],
            name=row['name'],
            rule_type=RuleType(row['rule_type']),
            category=RuleCategory(row['category']),
            description=row['description'] or "",
            source_text=row['source_text'] or "",
            conditions=[RuleCondition(**c) for c in content.get('conditions', [])],
            actions=[RuleAction(**a) for a in content.get('actions', [])],
            validation_rules=[ValidationRule(**v) for v in content.get('validation_rules', [])],
            calculation_rules=[CalculationRule(**c) for c in content.get('calculation_rules', [])],
            workflow_steps=[WorkflowStep(**w) for w in content.get('workflow_steps', [])],
            state_transitions=[StateTransition(**s) for s in content.get('state_transitions', [])],
            priority=RulePriority(row['priority']),
            status=RuleStatus(row['status']),
            tags=json.loads(row['tags']) if row['tags'] else [],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            version=row['current_version'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            confidence_score=row['confidence_score'],
            auto_classified=bool(row['auto_classified']),
            source=RuleSource(row['source']) if row['source'] else RuleSource.AUTO_EXTRACTED,
            parent_rule_id=row['parent_rule_id'],
            related_rules=json.loads(row['related_rules']) if row['related_rules'] else []
        )
    
    def query_rules(
        self,
        category: Optional[RuleCategory] = None,
        rule_type: Optional[RuleType] = None,
        status: Optional[RuleStatus] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[str] = None,
        source: Optional[RuleSource] = None,
        min_confidence: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[BusinessRule]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            sql = "SELECT * FROM rules WHERE 1=1"
            params = []
            
            if category:
                sql += " AND category = ?"
                params.append(category.value)
            
            if rule_type:
                sql += " AND rule_type = ?"
                params.append(rule_type.value)
            
            if status:
                sql += " AND status = ?"
                params.append(status.value)
            
            if source:
                sql += " AND source = ?"
                params.append(source.value)
            
            if min_confidence is not None:
                sql += " AND confidence_score >= ?"
                params.append(min_confidence)
            
            if keywords:
                sql += " AND (name LIKE ? OR description LIKE ? OR source_text LIKE ?)"
                keyword_param = f"%{keywords}%"
                params.extend([keyword_param, keyword_param, keyword_param])
            
            if tags:
                for tag in tags:
                    sql += " AND id IN (SELECT rule_id FROM rule_tags WHERE tag = ?)"
                    params.append(tag)
            
            sql += f" ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_rule(row) for row in rows]
            
        except Exception as e:
            logger.error(f"查询规则失败: {e}")
            return []
    
    def delete_rule(self, rule_id: str) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM rule_tags WHERE rule_id = ?', (rule_id,))
            cursor.execute('DELETE FROM rule_versions WHERE rule_id = ?', (rule_id,))
            cursor.execute('DELETE FROM rules WHERE id = ?', (rule_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"规则删除成功: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"规则删除失败: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as total FROM rules')
            total_rules = cursor.fetchone()['total']
            
            cursor.execute('SELECT category, COUNT(*) as count FROM rules GROUP BY category')
            category_counts = {row['category']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute('SELECT rule_type, COUNT(*) as count FROM rules GROUP BY rule_type')
            type_counts = {row['rule_type']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute('SELECT status, COUNT(*) as count FROM rules GROUP BY status')
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute('SELECT source, COUNT(*) as count FROM rules GROUP BY source')
            source_counts = {row['source']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute('SELECT AVG(confidence_score) as avg_confidence FROM rules')
            avg_confidence = cursor.fetchone()['avg_confidence'] or 0.0
            
            conn.close()
            
            return {
                "total_rules": total_rules,
                "by_category": category_counts,
                "by_type": type_counts,
                "by_status": status_counts,
                "by_source": source_counts,
                "avg_confidence": round(avg_confidence, 3)
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def export_rules(self, output_path: str, format: str = "json", 
                     category: Optional[RuleCategory] = None) -> str:
        rules = self.query_rules(category=category, limit=10000)
        
        if format == "json":
            data = {
                "export_time": datetime.now().isoformat(),
                "total_rules": len(rules),
                "rules": [r.to_dict() for r in rules]
            }
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif format == "csv":
            import csv
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', '名称', '类型', '分类', '描述', '状态', '优先级', '置信度'])
                for rule in rules:
                    writer.writerow([
                        rule.id, rule.name, rule.rule_type.value, rule.category.value,
                        rule.description, rule.status.value, rule.priority.value, rule.confidence_score
                    ])
        
        return output_path
    
    def import_rules(self, input_path: str, imported_by: str = "system") -> Dict[str, Any]:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        rules_data = data.get('rules', [data] if 'id' in data else [])
        
        results = {
            "total": len(rules_data),
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for rule_data in rules_data:
            try:
                rule = BusinessRule(
                    id=rule_data['id'],
                    name=rule_data['name'],
                    rule_type=RuleType(rule_data['rule_type']),
                    category=RuleCategory(rule_data['category']),
                    description=rule_data.get('description', ''),
                    source_text=rule_data.get('source_text', ''),
                    conditions=[RuleCondition(**c) for c in rule_data.get('conditions', [])],
                    actions=[RuleAction(**a) for a in rule_data.get('actions', [])],
                    validation_rules=[ValidationRule(**v) for v in rule_data.get('validation_rules', [])],
                    calculation_rules=[CalculationRule(**c) for c in rule_data.get('calculation_rules', [])],
                    workflow_steps=[WorkflowStep(**w) for w in rule_data.get('workflow_steps', [])],
                    state_transitions=[StateTransition(**s) for s in rule_data.get('state_transitions', [])],
                    priority=RulePriority(rule_data.get('priority', 'medium')),
                    status=RuleStatus(rule_data.get('status', 'active')),
                    tags=rule_data.get('tags', []),
                    metadata=rule_data.get('metadata', {}),
                    source=RuleSource.IMPORTED
                )
                
                if self.store_rule(rule, imported_by):
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"导入失败: {rule_data.get('id', 'unknown')} - {str(e)}")
        
        return results
    
    def save_template(self, template_id: str, name: str, category: RuleCategory,
                      rule_type: RuleType, template_content: Dict[str, Any],
                      description: str = "") -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT OR REPLACE INTO rule_templates 
                (id, name, category, rule_type, template_content, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (template_id, name, category.value, rule_type.value,
                  json.dumps(template_content, ensure_ascii=False), description, now, now))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"保存模板失败: {e}")
            return False
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM rule_templates WHERE id = ?', (template_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "id": row['id'],
                    "name": row['name'],
                    "category": row['category'],
                    "rule_type": row['rule_type'],
                    "template_content": json.loads(row['template_content']),
                    "description": row['description']
                }
            return None
            
        except Exception as e:
            logger.error(f"获取模板失败: {e}")
            return None
    
    def create_rule_from_template(self, template_id: str, name: str,
                                   customizations: Dict[str, Any] = None) -> Optional[BusinessRule]:
        template = self.get_template(template_id)
        if not template:
            return None
        
        customizations = customizations or {}
        template_content = template['template_content'].copy()
        template_content.update(customizations)
        
        rule_id = f"BR-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        rule = BusinessRule(
            id=rule_id,
            name=name,
            rule_type=RuleType(template['rule_type']),
            category=RuleCategory(template['category']),
            description=template.get('description', ''),
            source_text=f"从模板 {template['name']} 创建",
            conditions=[RuleCondition(**c) for c in template_content.get('conditions', [])],
            actions=[RuleAction(**a) for a in template_content.get('actions', [])],
            validation_rules=[ValidationRule(**v) for v in template_content.get('validation_rules', [])],
            calculation_rules=[CalculationRule(**c) for c in template_content.get('calculation_rules', [])],
            workflow_steps=[WorkflowStep(**w) for w in template_content.get('workflow_steps', [])],
            state_transitions=[StateTransition(**s) for s in template_content.get('state_transitions', [])],
            constraint_rules=[ConstraintRule(**c) for c in template_content.get('constraint_rules', [])],
            derivation_rules=[DerivationRule(**d) for d in template_content.get('derivation_rules', [])],
            data_governance_rules=[DataGovernanceRule(**d) for d in template_content.get('data_governance_rules', [])],
            notification_rules=[NotificationRule(**n) for n in template_content.get('notification_rules', [])],
            scheduling_rules=[SchedulingRule(**s) for s in template_content.get('scheduling_rules', [])],
            source=RuleSource.USER_INPUT
        )
        
        return rule
    
    def get_rule_versions(self, rule_id: str) -> List[Dict[str, Any]]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT version, rule_data, changed_at, change_type, change_description, changed_by
                FROM rule_versions
                WHERE rule_id = ?
                ORDER BY version DESC
            ''', (rule_id,))
            
            versions = []
            for row in cursor.fetchall():
                versions.append({
                    "version": row['version'],
                    "rule_data": json.loads(row['rule_data']),
                    "changed_at": row['changed_at'],
                    "change_type": row['change_type'],
                    "change_description": row['change_description'],
                    "changed_by": row['changed_by']
                })
            
            conn.close()
            return versions
            
        except Exception as e:
            logger.error(f"获取规则版本失败: {e}")
            return []
    
    def get_rule_version(self, rule_id: str, version: int) -> Optional[BusinessRule]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT rule_data FROM rule_versions
                WHERE rule_id = ? AND version = ?
            ''', (rule_id, version))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                rule_data = json.loads(row['rule_data'])
                return self._dict_to_rule(rule_data)
            return None
            
        except Exception as e:
            logger.error(f"获取规则版本失败: {e}")
            return None
    
    def restore_rule_version(self, rule_id: str, version: int, restored_by: str = "system") -> bool:
        try:
            old_rule = self.get_rule_version(rule_id, version)
            if not old_rule:
                return False
            
            old_rule.version = self._get_next_version(rule_id)
            old_rule.updated_at = datetime.now().isoformat()
            
            return self.store_rule(old_rule, restored_by)
            
        except Exception as e:
            logger.error(f"恢复规则版本失败: {e}")
            return False
    
    def _get_next_version(self, rule_id: str) -> int:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT MAX(version) as max_version FROM rule_versions WHERE rule_id = ?', (rule_id,))
            row = cursor.fetchone()
            conn.close()
            
            return (row['max_version'] or 0) + 1
            
        except Exception:
            return 1
    
    def add_dependency(self, rule_id: str, depends_on_rule_id: str, 
                       dependency_type: str = "requires") -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO rule_dependencies 
                (rule_id, depends_on_rule_id, dependency_type, created_at)
                VALUES (?, ?, ?, ?)
            ''', (rule_id, depends_on_rule_id, dependency_type, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"添加规则依赖: {rule_id} -> {depends_on_rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加规则依赖失败: {e}")
            return False
    
    def remove_dependency(self, rule_id: str, depends_on_rule_id: str) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM rule_dependencies 
                WHERE rule_id = ? AND depends_on_rule_id = ?
            ''', (rule_id, depends_on_rule_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"移除规则依赖失败: {e}")
            return False
    
    def get_dependencies(self, rule_id: str) -> List[Dict[str, Any]]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT depends_on_rule_id, dependency_type, created_at
                FROM rule_dependencies
                WHERE rule_id = ?
            ''', (rule_id,))
            
            dependencies = []
            for row in cursor.fetchall():
                dependencies.append({
                    "depends_on_rule_id": row['depends_on_rule_id'],
                    "dependency_type": row['dependency_type'],
                    "created_at": row['created_at']
                })
            
            conn.close()
            return dependencies
            
        except Exception as e:
            logger.error(f"获取规则依赖失败: {e}")
            return []
    
    def get_dependents(self, rule_id: str) -> List[str]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT rule_id FROM rule_dependencies
                WHERE depends_on_rule_id = ?
            ''', (rule_id,))
            
            dependents = [row['rule_id'] for row in cursor.fetchall()]
            conn.close()
            
            return dependents
            
        except Exception as e:
            logger.error(f"获取依赖此规则的规则失败: {e}")
            return []
    
    def change_rule_status(self, rule_id: str, new_status: RuleStatus,
                           changed_by: str = "system", reason: str = "") -> bool:
        try:
            rule = self.get_rule(rule_id)
            if not rule:
                return False
            
            old_status = rule.status
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE rules SET status = ?, updated_at = ?
                WHERE id = ?
            ''', (new_status.value, datetime.now().isoformat(), rule_id))
            
            cursor.execute('''
                INSERT INTO rule_lifecycle 
                (rule_id, from_status, to_status, changed_at, changed_by, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (rule_id, old_status.value, new_status.value, 
                  datetime.now().isoformat(), changed_by, reason))
            
            conn.commit()
            conn.close()
            
            logger.info(f"规则状态变更: {rule_id} {old_status.value} -> {new_status.value}")
            return True
            
        except Exception as e:
            logger.error(f"变更规则状态失败: {e}")
            return False
    
    def get_lifecycle_history(self, rule_id: str) -> List[Dict[str, Any]]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT from_status, to_status, changed_at, changed_by, reason
                FROM rule_lifecycle
                WHERE rule_id = ?
                ORDER BY changed_at DESC
            ''', (rule_id,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    "from_status": row['from_status'],
                    "to_status": row['to_status'],
                    "changed_at": row['changed_at'],
                    "changed_by": row['changed_by'],
                    "reason": row['reason']
                })
            
            conn.close()
            return history
            
        except Exception as e:
            logger.error(f"获取生命周期历史失败: {e}")
            return []
    
    def detect_conflicts(self) -> List[Dict[str, Any]]:
        try:
            rules = self.query_rules(status=RuleStatus.ACTIVE, limit=10000)
            conflicts = []
            
            for i, rule1 in enumerate(rules):
                for rule2 in rules[i+1:]:
                    conflict = self._check_rule_conflict(rule1, rule2)
                    if conflict:
                        conflicts.append(conflict)
            
            self._store_conflicts(conflicts)
            
            return conflicts
            
        except Exception as e:
            logger.error(f"检测规则冲突失败: {e}")
            return []
    
    def _check_rule_conflict(self, rule1: BusinessRule, rule2: BusinessRule) -> Optional[Dict[str, Any]]:
        for cond1 in rule1.conditions:
            for cond2 in rule2.conditions:
                if cond1.field == cond2.field:
                    if cond1.operator == '==' and cond2.operator == '==':
                        if cond1.value != cond2.value:
                            return {
                                "rule_id1": rule1.id,
                                "rule_id2": rule2.id,
                                "conflict_type": "condition_mismatch",
                                "severity": "error",
                                "description": f"字段 '{cond1.field}' 在两个规则中有不同的值要求"
                            }
        
        for action1 in rule1.actions:
            for action2 in rule2.actions:
                if action1.target == action2.target:
                    if (action1.action_type == 'block' and action2.action_type == 'allow') or \
                       (action1.action_type == 'allow' and action2.action_type == 'block'):
                        return {
                            "rule_id1": rule1.id,
                            "rule_id2": rule2.id,
                            "conflict_type": "action_contradiction",
                            "severity": "warning",
                            "description": f"目标 '{action1.target}' 存在冲突的动作"
                        }
        
        return None
    
    def _store_conflicts(self, conflicts: List[Dict[str, Any]]):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            for conflict in conflicts:
                cursor.execute('''
                    INSERT INTO rule_conflicts 
                    (rule_id1, rule_id2, conflict_type, severity, description, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (conflict['rule_id1'], conflict['rule_id2'],
                      conflict['conflict_type'], conflict['severity'],
                      conflict['description'], now))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"存储冲突信息失败: {e}")
    
    def get_conflicts(self, rule_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if rule_id:
                cursor.execute('''
                    SELECT * FROM rule_conflicts
                    WHERE (rule_id1 = ? OR rule_id2 = ?) AND resolved = 0
                ''', (rule_id, rule_id))
            else:
                cursor.execute('SELECT * FROM rule_conflicts WHERE resolved = 0')
            
            conflicts = []
            for row in cursor.fetchall():
                conflicts.append({
                    "id": row['id'],
                    "rule_id1": row['rule_id1'],
                    "rule_id2": row['rule_id2'],
                    "conflict_type": row['conflict_type'],
                    "severity": row['severity'],
                    "description": row['description'],
                    "detected_at": row['detected_at']
                })
            
            conn.close()
            return conflicts
            
        except Exception as e:
            logger.error(f"获取冲突信息失败: {e}")
            return []
    
    def resolve_conflict(self, conflict_id: int) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('UPDATE rule_conflicts SET resolved = 1 WHERE id = ?', (conflict_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"解决冲突失败: {e}")
            return False
    
    def _dict_to_rule(self, rule_data: Dict[str, Any]) -> BusinessRule:
        return BusinessRule(
            id=rule_data['id'],
            name=rule_data['name'],
            rule_type=RuleType(rule_data['rule_type']),
            category=RuleCategory(rule_data['category']),
            description=rule_data.get('description', ''),
            source_text=rule_data.get('source_text', ''),
            conditions=[RuleCondition(**c) for c in rule_data.get('conditions', [])],
            actions=[RuleAction(**a) for a in rule_data.get('actions', [])],
            validation_rules=[ValidationRule(**v) for v in rule_data.get('validation_rules', [])],
            calculation_rules=[CalculationRule(**c) for c in rule_data.get('calculation_rules', [])],
            workflow_steps=[WorkflowStep(**w) for w in rule_data.get('workflow_steps', [])],
            state_transitions=[StateTransition(**s) for s in rule_data.get('state_transitions', [])],
            constraint_rules=[ConstraintRule(**c) for c in rule_data.get('constraint_rules', [])],
            derivation_rules=[DerivationRule(**d) for d in rule_data.get('derivation_rules', [])],
            data_governance_rules=[DataGovernanceRule(**d) for d in rule_data.get('data_governance_rules', [])],
            notification_rules=[NotificationRule(**n) for n in rule_data.get('notification_rules', [])],
            scheduling_rules=[SchedulingRule(**s) for s in rule_data.get('scheduling_rules', [])],
            priority=RulePriority(rule_data.get('priority', 'medium')),
            status=RuleStatus(rule_data.get('status', 'active')),
            tags=rule_data.get('tags', []),
            metadata=rule_data.get('metadata', {}),
            version=rule_data.get('version', 1),
            created_at=rule_data.get('created_at', datetime.now().isoformat()),
            updated_at=rule_data.get('updated_at', datetime.now().isoformat()),
            confidence_score=rule_data.get('confidence_score', 1.0),
            auto_classified=rule_data.get('auto_classified', False),
            source=RuleSource(rule_data.get('source', 'auto_extracted')),
            parent_rule_id=rule_data.get('parent_rule_id'),
            related_rules=rule_data.get('related_rules', []),
            secondary_categories=[RuleCategory(c) for c in rule_data.get('secondary_categories', [])],
            classification_explanation=rule_data.get('classification_explanation', '')
        )


class RuleValidator:
    def __init__(self):
        self._validators: Dict[str, Callable] = {}
        self._setup_validators()
    
    def _setup_validators(self):
        self._validators = {
            'completeness': self._validate_completeness,
            'consistency': self._validate_consistency,
            'conflict': self._validate_conflicts,
            'dependency': self._validate_dependencies,
            'semantic': self._validate_semantic,
            'security': self._validate_security,
            'data_quality': self._validate_data_quality,
            'performance': self._validate_performance,
        }
    
    def _validate_completeness(self, rule: BusinessRule) -> ValidationResult:
        errors = []
        warnings = []
        
        if not rule.name or not rule.name.strip():
            errors.append("规则名称不能为空")
        
        if not rule.description or not rule.description.strip():
            warnings.append("建议添加规则描述")
        
        has_content = (
            rule.conditions or rule.actions or 
            rule.validation_rules or rule.calculation_rules or
            rule.workflow_steps or rule.state_transitions
        )
        if not has_content:
            errors.append("规则必须包含至少一个条件、动作、验证规则、计算规则、工作流步骤或状态转换")
        
        for i, cond in enumerate(rule.conditions):
            if not cond.field:
                errors.append(f"条件 {i+1} 缺少字段名")
            if not cond.operator:
                errors.append(f"条件 {i+1} 缺少操作符")
        
        for i, action in enumerate(rule.actions):
            if not action.target:
                errors.append(f"动作 {i+1} 缺少目标")
        
        severity = ValidationSeverity.ERROR if errors else (
            ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO
        )
        
        score = 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.05)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            severity=severity,
            score=max(0.0, score)
        )
    
    def _validate_consistency(self, rule: BusinessRule) -> ValidationResult:
        errors = []
        warnings = []
        
        for calc in rule.calculation_rules:
            for dep in calc.dependencies:
                found = False
                for cond in rule.conditions:
                    if cond.field == dep:
                        found = True
                        break
                if not found:
                    warnings.append(f"计算依赖 '{dep}' 未在条件中定义")
        
        for val in rule.validation_rules:
            if val.validation_type == 'min_length':
                min_len = val.parameters.get('min_length', 0)
                if min_len < 0:
                    errors.append(f"字段 '{val.field}' 的最小长度不能为负数")
            elif val.validation_type == 'range':
                min_val = val.parameters.get('min')
                max_val = val.parameters.get('max')
                if min_val is not None and max_val is not None and min_val > max_val:
                    errors.append(f"字段 '{val.field}' 的范围最小值大于最大值")
        
        severity = ValidationSeverity.ERROR if errors else (
            ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO
        )
        
        score = 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.05)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            severity=severity,
            score=max(0.0, score)
        )
    
    def _validate_conflicts(self, rule: BusinessRule) -> ValidationResult:
        errors = []
        warnings = []
        
        for i, cond1 in enumerate(rule.conditions):
            for j, cond2 in enumerate(rule.conditions[i+1:], i+1):
                if cond1.field == cond2.field:
                    if cond1.operator == cond2.operator and cond1.value != cond2.value:
                        if cond1.operator in ['==', '>=', '<=']:
                            errors.append(f"条件 {i+1} 和 {j+1} 对字段 '{cond1.field}' 存在冲突")
        
        for i, action1 in enumerate(rule.actions):
            for j, action2 in enumerate(rule.actions[i+1:], i+1):
                if action1.target == action2.target:
                    if action1.action_type == 'block' and action2.action_type == 'allow':
                        errors.append(f"动作 {i+1} 和 {j+1} 对目标 '{action1.target}' 存在冲突")
        
        severity = ValidationSeverity.ERROR if errors else (
            ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO
        )
        
        score = 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.05)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            severity=severity,
            score=max(0.0, score)
        )
    
    def _validate_dependencies(self, rule: BusinessRule) -> ValidationResult:
        errors = []
        warnings = []
        
        dep_graph: Dict[str, Set[str]] = {}
        
        for calc in rule.calculation_rules:
            dep_graph[calc.result_field] = set(calc.dependencies)
        
        def has_cycle(node: str, visited: Set[str], path: Set[str]) -> bool:
            if node in path:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            path.add(node)
            
            for dep in dep_graph.get(node, set()):
                if has_cycle(dep, visited, path):
                    return True
            
            path.remove(node)
            return False
        
        visited: Set[str] = set()
        for node in dep_graph:
            if node not in visited:
                if has_cycle(node, visited, set()):
                    errors.append("检测到计算依赖循环")
                    break
        
        severity = ValidationSeverity.ERROR if errors else (
            ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO
        )
        
        score = 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.05)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            severity=severity,
            score=max(0.0, score)
        )
    
    def _validate_semantic(self, rule: BusinessRule) -> ValidationResult:
        errors = []
        warnings = []
        
        text = rule.source_text or rule.description or ""
        
        contradiction_patterns = [
            (r'必须(.+?)，?不能\1', "自我矛盾"),
            (r'禁止(.+?)，?允许\1', "禁止与允许矛盾"),
        ]
        
        for pattern, issue_type in contradiction_patterns:
            if re.search(pattern, text):
                errors.append(f"检测到语义矛盾: {issue_type}")
        
        if rule.workflow_steps:
            end_steps = [s for s in rule.workflow_steps if s.is_end]
            if not end_steps:
                warnings.append("工作流缺少结束步骤")
        
        severity = ValidationSeverity.ERROR if errors else (
            ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO
        )
        
        score = 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.05)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            severity=severity,
            score=max(0.0, score)
        )
    
    def _validate_security(self, rule: BusinessRule) -> ValidationResult:
        errors = []
        warnings = []
        
        text = rule.source_text or rule.description or ""
        text_lower = text.lower()
        
        sensitive_keywords = ['密码', 'password', '密钥', 'secret', 'token', 'api_key']
        for keyword in sensitive_keywords:
            if keyword in text_lower:
                warnings.append(f"规则中可能包含敏感信息: {keyword}")
        
        if rule.category == RuleCategory.SECURITY_RULE:
            if not any(tag in ['security', '安全'] for tag in rule.tags):
                warnings.append("安全规则建议添加安全相关标签")
        
        severity = ValidationSeverity.ERROR if errors else (
            ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO
        )
        
        score = 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.05)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            severity=severity,
            score=max(0.0, score)
        )
    
    def validate_rule(self, rule: BusinessRule, validators: Optional[List[str]] = None) -> Dict[str, ValidationResult]:
        results = {}
        
        validators_to_run = validators if validators else list(self._validators.keys())
        
        for validator_name in validators_to_run:
            if validator_name in self._validators:
                results[validator_name] = self._validators[validator_name](rule)
        
        return results
    
    def is_rule_valid(self, rule: BusinessRule) -> bool:
        results = self.validate_rule(rule)
        return all(r.is_valid for r in results.values())
    
    def get_validation_score(self, rule: BusinessRule) -> float:
        results = self.validate_rule(rule)
        if not results:
            return 1.0
        return sum(r.score for r in results.values()) / len(results)
    
    def _validate_data_quality(self, rule: BusinessRule) -> ValidationResult:
        errors = []
        warnings = []
        
        for gov_rule in rule.data_governance_rules:
            if gov_rule.retention_period is not None:
                if gov_rule.retention_period <= 0:
                    errors.append(f"数据保留期限必须大于0: {gov_rule.data_entity}")
            
            if gov_rule.data_classification not in ['public', 'internal', 'confidential', 'restricted']:
                warnings.append(f"未知的数据分类级别: {gov_rule.data_classification}")
        
        for constraint in rule.constraint_rules:
            if constraint.constraint_type == 'referential':
                if not constraint.constraint_value:
                    warnings.append("引用完整性约束缺少引用目标")
        
        severity = ValidationSeverity.ERROR if errors else (
            ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO
        )
        
        score = 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.05)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            severity=severity,
            score=max(0.0, score)
        )
    
    def _validate_performance(self, rule: BusinessRule) -> ValidationResult:
        errors = []
        warnings = []
        
        for sched_rule in rule.scheduling_rules:
            if sched_rule.timeout is not None and sched_rule.timeout <= 0:
                errors.append(f"调度任务超时时间必须大于0: {sched_rule.task_name}")
        
        complexity = rule.get_complexity_score()
        if complexity > 0.8:
            warnings.append(f"规则复杂度过高 ({complexity:.2f})，建议拆分")
        
        if len(rule.conditions) > 10:
            warnings.append(f"条件数量过多 ({len(rule.conditions)})，可能影响性能")
        
        severity = ValidationSeverity.ERROR if errors else (
            ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO
        )
        
        score = 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.05)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            severity=severity,
            score=max(0.0, score)
        )
    
    def validate_rules_cross(self, rules: List[BusinessRule]) -> Dict[str, Any]:
        results = {
            "total_rules": len(rules),
            "conflicts": [],
            "duplicates": [],
            "coverage_gaps": [],
            "dependency_issues": [],
            "recommendations": []
        }
        
        for i, rule1 in enumerate(rules):
            for rule2 in rules[i+1:]:
                conflict = self._check_cross_rule_conflict(rule1, rule2)
                if conflict:
                    results["conflicts"].append(conflict)
                
                duplicate = self._check_duplicate_rule(rule1, rule2)
                if duplicate:
                    results["duplicates"].append(duplicate)
        
        coverage = self._analyze_coverage(rules)
        results["coverage_gaps"] = coverage["gaps"]
        results["coverage_score"] = coverage["score"]
        
        dep_issues = self._check_cross_dependencies(rules)
        results["dependency_issues"] = dep_issues
        
        results["recommendations"] = self._generate_recommendations(results)
        
        return results
    
    def _check_cross_rule_conflict(self, rule1: BusinessRule, rule2: BusinessRule) -> Optional[Dict[str, Any]]:
        for cond1 in rule1.conditions:
            for cond2 in rule2.conditions:
                if cond1.field == cond2.field:
                    if cond1.operator == '==' and cond2.operator == '==':
                        if cond1.value != cond2.value:
                            return {
                                "type": "condition_conflict",
                                "rule1_id": rule1.id,
                                "rule2_id": rule2.id,
                                "field": cond1.field,
                                "description": f"字段 '{cond1.field}' 在两个规则中有冲突的值要求"
                            }
        
        for action1 in rule1.actions:
            for action2 in rule2.actions:
                if action1.target == action2.target:
                    if (action1.action_type == 'block' and action2.action_type == 'allow'):
                        return {
                            "type": "action_conflict",
                            "rule1_id": rule1.id,
                            "rule2_id": rule2.id,
                            "target": action1.target,
                            "description": f"目标 '{action1.target}' 存在冲突的动作"
                        }
        
        return None
    
    def _check_duplicate_rule(self, rule1: BusinessRule, rule2: BusinessRule) -> Optional[Dict[str, Any]]:
        hash1 = rule1.get_content_hash()
        hash2 = rule2.get_content_hash()
        
        if hash1 == hash2:
            return {
                "rule1_id": rule1.id,
                "rule2_id": rule2.id,
                "similarity": 1.0,
                "description": "检测到完全相同的规则"
            }
        
        return None
    
    def _analyze_coverage(self, rules: List[BusinessRule]) -> Dict[str, Any]:
        covered_fields = set()
        covered_entities = set()
        
        for rule in rules:
            for cond in rule.conditions:
                covered_fields.add(cond.field)
            
            for val in rule.validation_rules:
                covered_fields.add(val.field)
            
            for calc in rule.calculation_rules:
                covered_fields.add(calc.result_field)
                covered_fields.update(calc.dependencies)
        
        gaps = []
        
        essential_fields = ['id', 'name', 'status', 'created_at', 'updated_at']
        for field in essential_fields:
            if field not in covered_fields:
                gaps.append({
                    "type": "missing_field_validation",
                    "field": field,
                    "description": f"缺少对核心字段 '{field}' 的验证规则"
                })
        
        score = len(covered_fields) / max(len(covered_fields) + len(gaps), 1)
        
        return {
            "gaps": gaps,
            "score": score,
            "covered_fields": list(covered_fields),
            "covered_entities": list(covered_entities)
        }
    
    def _check_cross_dependencies(self, rules: List[BusinessRule]) -> List[Dict[str, Any]]:
        issues = []
        rule_ids = {rule.id for rule in rules}
        
        for rule in rules:
            for related_id in rule.related_rules:
                if related_id not in rule_ids:
                    issues.append({
                        "type": "missing_related_rule",
                        "rule_id": rule.id,
                        "missing_rule_id": related_id,
                        "description": f"规则 '{rule.id}' 引用了不存在的规则 '{related_id}'"
                    })
            
            if rule.parent_rule_id and rule.parent_rule_id not in rule_ids:
                issues.append({
                    "type": "missing_parent_rule",
                    "rule_id": rule.id,
                    "missing_rule_id": rule.parent_rule_id,
                    "description": f"规则 '{rule.id}' 的父规则 '{rule.parent_rule_id}' 不存在"
                })
        
        return issues
    
    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        if validation_results["conflicts"]:
            recommendations.append(f"发现 {len(validation_results['conflicts'])} 个规则冲突，建议优先解决")
        
        if validation_results["duplicates"]:
            recommendations.append(f"发现 {len(validation_results['duplicates'])} 个重复规则，建议合并或删除")
        
        if validation_results.get("coverage_score", 1.0) < 0.7:
            recommendations.append(f"规则覆盖率较低 ({validation_results.get('coverage_score', 0):.1%})，建议补充更多验证规则")
        
        if validation_results["dependency_issues"]:
            recommendations.append(f"发现 {len(validation_results['dependency_issues'])} 个依赖问题，建议检查规则关联")
        
        return recommendations
    
    def calculate_rule_quality_score(self, rule: BusinessRule) -> Dict[str, float]:
        scores = {
            "completeness": 0.0,
            "consistency": 0.0,
            "clarity": 0.0,
            "maintainability": 0.0,
            "overall": 0.0
        }
        
        validation_results = self.validate_rule(rule)
        scores["completeness"] = validation_results.get("completeness", ValidationResult(True)).score
        scores["consistency"] = validation_results.get("consistency", ValidationResult(True)).score
        
        if rule.description and len(rule.description) > 10:
            scores["clarity"] += 0.3
        if rule.source_text and len(rule.source_text) > 10:
            scores["clarity"] += 0.3
        if rule.tags:
            scores["clarity"] += 0.2
        if rule.metadata:
            scores["clarity"] += 0.2
        
        complexity = rule.get_complexity_score()
        scores["maintainability"] = 1.0 - complexity * 0.5
        
        if len(rule.conditions) <= 5:
            scores["maintainability"] += 0.2
        if len(rule.actions) <= 3:
            scores["maintainability"] += 0.2
        
        scores["maintainability"] = min(scores["maintainability"], 1.0)
        
        weights = {
            "completeness": 0.3,
            "consistency": 0.3,
            "clarity": 0.2,
            "maintainability": 0.2
        }
        
        scores["overall"] = sum(
            scores[key] * weight for key, weight in weights.items()
        )
        
        return scores


class BusinessRuleExtractor:
    CONDITION_PATTERNS = [
        (re.compile(r'(?:如果|当|若)\s*(.+?)\s*(?:时|情况下|满足)', re.IGNORECASE), 'if'),
        (re.compile(r'(?:只要|一旦)\s*(.+?)(?:，|,)', re.IGNORECASE), 'when'),
        (re.compile(r'(?:除非|除了)\s*(.+?)(?:，|,)', re.IGNORECASE), 'unless'),
        (re.compile(r'if\s+(.+?)\s+then', re.IGNORECASE), 'if'),
        (re.compile(r'when\s+(.+?)\s*,', re.IGNORECASE), 'when'),
        (re.compile(r'unless\s+(.+?)\s*,', re.IGNORECASE), 'unless'),
        (re.compile(r'(?:只有|仅当)\s*(.+?)\s*(?:才)', re.IGNORECASE), 'only_if'),
    ]
    
    ACTION_PATTERNS = [
        (re.compile(r'(?:则|那么|就)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'then'),
        (re.compile(r'(?:必须|应该|需要)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'must'),
        (re.compile(r'(?:可以|允许)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'can'),
        (re.compile(r'(?:禁止|不允许|不能)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'forbidden'),
        (re.compile(r'then\s+(.+?)(?:,|\.|$)', re.IGNORECASE), 'then'),
        (re.compile(r'(?:触发|执行)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'trigger'),
    ]
    
    VALIDATION_PATTERNS = [
        (re.compile(r'(.+?)\s*(?:必须|需要)\s*(?:是|为)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'must_be'),
        (re.compile(r'(.+?)\s*(?:不能|不可|不允许)\s*(?:为空|为null|为空值)', re.IGNORECASE), 'not_null'),
        (re.compile(r'(.+?)\s*(?:必须|需要)\s*(?:大于|超过|多于)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'greater_than'),
        (re.compile(r'(.+?)\s*(?:必须|需要)\s*(?:小于|低于|少于)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'less_than'),
        (re.compile(r'(.+?)\s*(?:必须|需要)\s*(?:等于|为)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'equals'),
        (re.compile(r'(.+?)\s*(?:必须|需要)\s*(?:在|属于)\s*(.+?)(?:范围|列表)内', re.IGNORECASE), 'in_range'),
        (re.compile(r'(.+?)\s*(?:必须|需要)\s*(?:符合|满足)\s*(.+?)\s*(?:格式|规则)', re.IGNORECASE), 'matches'),
        (re.compile(r'(.+?)\s*(?:长度|位数)\s*(?:必须|需要)\s*(?:大于|超过|最少)\s*(\d+)', re.IGNORECASE), 'min_length'),
        (re.compile(r'(.+?)\s*(?:长度|位数)\s*(?:必须|需要)\s*(?:小于|不超过|最多)\s*(\d+)', re.IGNORECASE), 'max_length'),
        (re.compile(r'(.+?)\s*(?:必须|需要)\s*(?:是|为)\s*唯一(?:的)?', re.IGNORECASE), 'unique'),
        (re.compile(r'(.+?)\s*(?:格式|类型)\s*(?:必须|需要)\s*(?:为|是)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'format'),
    ]
    
    CALCULATION_PATTERNS = [
        (re.compile(r'(.+?)\s*(?:等于|为|=)\s*(.+?)(?:的|之和|积)', re.IGNORECASE), 'formula'),
        (re.compile(r'(.+?)\s*(?:按|根据)\s*(.+?)\s*(?:计算|得出)', re.IGNORECASE), 'derived'),
        (re.compile(r'(.+?)\s*(?:=|等于)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'formula'),
        (re.compile(r'(?:计算|求)\s*(.+?)\s*(?:公式|方法)\s*(?:为|:|：)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'formula'),
        (re.compile(r'(.+?)\s*(?:合计|总计)\s*(?:为|等于)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'sum'),
        (re.compile(r'(.+?)\s*(?:平均值|均值)\s*(?:为|等于)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'average'),
    ]
    
    WORKFLOW_PATTERNS = [
        (re.compile(r'(?:第一步|首先|开始)\s*[:：]?\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'start'),
        (re.compile(r'(?:然后|接着|下一步)\s*[:：]?\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'next'),
        (re.compile(r'(?:最后|结束)\s*[:：]?\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'end'),
        (re.compile(r'(?:步骤|阶段)\s*(\d+)\s*[:：]?\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'step'),
        (re.compile(r'(?:审批|审核)\s*(?:流程|通过|拒绝)', re.IGNORECASE), 'approval'),
    ]
    
    STATE_PATTERNS = [
        (re.compile(r'(?:状态)\s*(?:从|由)\s*(.+?)\s*(?:变为|转换为|变更)\s*(.+?)(?:，|。|$)', re.IGNORECASE), 'transition'),
        (re.compile(r'当\s*(.+?)\s*(?:状态)\s*(?:为|是)\s*(.+?)\s*(?:时|，)', re.IGNORECASE), 'state_check'),
    ]
    
    OPERATOR_MAPPING = {
        '大于': '>',
        '小于': '<',
        '等于': '==',
        '不等于': '!=',
        '大于等于': '>=',
        '小于等于': '<=',
        '包含': 'in',
        '不包含': 'not in',
        '匹配': 'matches',
        '为空': 'is null',
        '不为空': 'is not null',
        '开始于': 'starts_with',
        '结束于': 'ends_with',
        '在...之间': 'between',
    }
    
    PRIORITY_KEYWORDS = {
        RulePriority.CRITICAL: ["关键", "核心", "必须", "critical", "mandatory", "essential", "紧急"],
        RulePriority.HIGH: ["重要", "高优先级", "high", "important", "优先"],
        RulePriority.MEDIUM: ["一般", "中等", "medium", "normal"],
        RulePriority.LOW: ["可选", "低优先级", "low", "optional", "建议"]
    }
    
    def __init__(self, db_path: str = "rule_library.db"):
        self.rule_counter = 0
        self.classifier = RuleTypeClassifier()
        self.library = RuleLibraryIntegration(db_path)
        self.validator = RuleValidator()
        self.semantic_analyzer = SemanticAnalyzer()
        logger.info("业务规则提取器初始化完成")
    
    def _generate_rule_id(self, prefix: str = "BR") -> str:
        self.rule_counter += 1
        return f"{prefix}-{datetime.now().strftime('%Y%m%d')}-{self.rule_counter:04d}"
    
    def _extract_priority(self, text: str) -> RulePriority:
        text_lower = text.lower()
        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return priority
        return RulePriority.MEDIUM
    
    def _parse_condition_value(self, value_text: str) -> Tuple[str, Any]:
        value_text = value_text.strip()
        
        number_match = re.match(r'^(\d+(?:\.\d+)?)$', value_text)
        if number_match:
            num = float(number_match.group(1))
            return ('number', int(num) if num.is_integer() else num)
        
        if value_text.lower() in ['true', '真', '是', 'yes']:
            return ('boolean', True)
        if value_text.lower() in ['false', '假', '否', 'no']:
            return ('boolean', False)
        
        if value_text.lower() in ['null', '空', '空值', 'none']:
            return ('null', None)
        
        quoted_match = re.match(r'^["\'](.+)["\']$', value_text)
        if quoted_match:
            return ('string', quoted_match.group(1))
        
        list_match = re.match(r'^\[(.+)\]$', value_text)
        if list_match:
            items = [item.strip().strip('"\'') for item in list_match.group(1).split(',')]
            return ('list', items)
        
        return ('string', value_text)
    
    def extract_condition_action_rules(self, text: str) -> List[BusinessRule]:
        rules = []
        
        for pattern, cond_type in self.CONDITION_PATTERNS:
            cond_matches = pattern.findall(text)
            for cond_match in cond_matches:
                conditions = []
                actions = []
                
                condition_text = cond_match.strip()
                
                field_match = re.match(r'(.+?)(?:大于|小于|等于|为|是|包含|不包含)(.+)', condition_text)
                if field_match:
                    field = field_match.group(1).strip()
                    value_part = field_match.group(2).strip()
                    
                    operator = '=='
                    for op_cn, op_en in self.OPERATOR_MAPPING.items():
                        if op_cn in condition_text:
                            operator = op_en
                            break
                    
                    _, value = self._parse_condition_value(value_part)
                    
                    condition = RuleCondition(
                        field=field,
                        operator=operator,
                        value=value,
                        description=condition_text
                    )
                    conditions.append(condition)
                else:
                    condition = RuleCondition(
                        field=condition_text,
                        operator='is_true',
                        value=True,
                        description=condition_text
                    )
                    conditions.append(condition)
                
                for action_pattern, action_type in self.ACTION_PATTERNS:
                    action_matches = action_pattern.findall(text)
                    for action_match in action_matches:
                        action_text = action_match.strip()
                        action = RuleAction(
                            action_type=action_type,
                            target=action_text,
                            description=action_text
                        )
                        actions.append(action)
                
                if conditions:
                    rule = BusinessRule(
                        id=self._generate_rule_id(),
                        name=f"条件动作规则-{len(rules)+1}",
                        rule_type=RuleType.CONDITION_ACTION,
                        category=RuleCategory.BUSINESS_LOGIC,
                        description=f"当{condition_text}时执行相应动作",
                        source_text=text,
                        conditions=conditions,
                        actions=actions,
                        priority=self._extract_priority(text)
                    )
                    rules.append(rule)
        
        return rules
    
    def extract_validation_rules(self, text: str) -> List[BusinessRule]:
        rules = []
        
        for pattern, validation_type in self.VALIDATION_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    field = match[0].strip()
                    value = match[1].strip() if len(match) > 1 else None
                else:
                    field = match.strip()
                    value = None
                
                parameters = {}
                if validation_type == 'min_length':
                    parameters['min_length'] = int(value) if value else 0
                elif validation_type == 'max_length':
                    parameters['max_length'] = int(value) if value else 0
                elif validation_type == 'greater_than':
                    parameters['min_value'] = value
                elif validation_type == 'less_than':
                    parameters['max_value'] = value
                elif validation_type == 'in_range':
                    parameters['allowed_values'] = value
                elif validation_type == 'format':
                    parameters['format'] = value
                
                validation = ValidationRule(
                    field=field,
                    validation_type=validation_type,
                    parameters=parameters,
                    error_message=f"{field}验证失败"
                )
                
                rule = BusinessRule(
                    id=self._generate_rule_id(),
                    name=f"验证规则-{field}",
                    rule_type=RuleType.VALIDATION,
                    category=RuleCategory.VALIDATION_RULE,
                    description=f"{field}的{validation_type}验证",
                    source_text=text,
                    validation_rules=[validation],
                    priority=self._extract_priority(text)
                )
                rules.append(rule)
        
        return rules
    
    def extract_calculation_rules(self, text: str) -> List[BusinessRule]:
        rules = []
        
        for pattern, calc_type in self.CALCULATION_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    result_field = match[0].strip()
                    formula = match[1].strip()
                    
                    dependencies = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', formula)
                    dependencies = [d for d in dependencies if d not in ['sum', 'avg', 'max', 'min', 'count', 'if', 'else', 'round', 'abs']]
                    
                    calculation = CalculationRule(
                        result_field=result_field,
                        formula=formula,
                        dependencies=dependencies,
                        description=f"{result_field} = {formula}"
                    )
                    
                    rule = BusinessRule(
                        id=self._generate_rule_id(),
                        name=f"计算规则-{result_field}",
                        rule_type=RuleType.CALCULATION,
                        category=RuleCategory.CALCULATION_RULE,
                        description=f"计算{result_field}",
                        source_text=text,
                        calculation_rules=[calculation],
                        priority=self._extract_priority(text),
                        tags=['calculation', 'derived']
                    )
                    rules.append(rule)
        
        return rules
    
    def extract_workflow_rules(self, text: str) -> List[BusinessRule]:
        rules = []
        steps = []
        
        for pattern, step_type in self.WORKFLOW_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                if step_type == 'step':
                    step_num = match[0]
                    step_name = match[1] if len(match) > 1 else f"步骤{step_num}"
                    steps.append(WorkflowStep(
                        step_id=f"step_{step_num}",
                        step_name=step_name,
                        action=step_name,
                        is_start=(step_num == '1'),
                        is_end=False
                    ))
                else:
                    step_name = match if isinstance(match, str) else match[0]
                    steps.append(WorkflowStep(
                        step_id=f"step_{len(steps)+1}",
                        step_name=step_name,
                        action=step_name,
                        is_start=(step_type == 'start'),
                        is_end=(step_type == 'end')
                    ))
        
        if steps:
            for i, step in enumerate(steps):
                if i < len(steps) - 1:
                    step.next_steps = [steps[i+1].step_id]
            
            rule = BusinessRule(
                id=self._generate_rule_id(),
                name="工作流规则",
                rule_type=RuleType.WORKFLOW,
                category=RuleCategory.WORKFLOW_RULE,
                description="业务流程规则",
                source_text=text,
                workflow_steps=steps,
                priority=self._extract_priority(text),
                tags=['workflow', 'process']
            )
            rules.append(rule)
        
        return rules
    
    def extract_state_transition_rules(self, text: str) -> List[BusinessRule]:
        rules = []
        
        for pattern, trans_type in self.STATE_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                if trans_type == 'transition' and len(match) >= 2:
                    from_state = match[0].strip()
                    to_state = match[1].strip()
                    
                    transition = StateTransition(
                        from_state=from_state,
                        to_state=to_state,
                        trigger="状态变更"
                    )
                    
                    rule = BusinessRule(
                        id=self._generate_rule_id(),
                        name=f"状态转换规则-{from_state}到{to_state}",
                        rule_type=RuleType.STATE_TRANSITION,
                        category=RuleCategory.WORKFLOW_RULE,
                        description=f"状态从{from_state}转换为{to_state}",
                        source_text=text,
                        state_transitions=[transition],
                        priority=self._extract_priority(text),
                        tags=['state', 'transition']
                    )
                    rules.append(rule)
        
        return rules
    
    def extract_all_rules(self, text: str, auto_classify: bool = True) -> List[BusinessRule]:
        all_rules = []
        
        all_rules.extend(self.extract_condition_action_rules(text))
        all_rules.extend(self.extract_validation_rules(text))
        all_rules.extend(self.extract_calculation_rules(text))
        all_rules.extend(self.extract_workflow_rules(text))
        all_rules.extend(self.extract_state_transition_rules(text))
        
        if auto_classify:
            for rule in all_rules:
                self.classifier.auto_classify_rule(rule)
        
        return all_rules
    
    def extract_and_validate(self, text: str) -> Tuple[List[BusinessRule], Dict[str, Any]]:
        rules = self.extract_all_rules(text)
        
        validation_results = {}
        valid_rules = []
        invalid_rules = []
        
        for rule in rules:
            results = self.validator.validate_rule(rule)
            validation_results[rule.id] = results
            
            if self.validator.is_rule_valid(rule):
                valid_rules.append(rule)
            else:
                invalid_rules.append(rule)
        
        summary = {
            "total_rules": len(rules),
            "valid_rules": len(valid_rules),
            "invalid_rules": len(invalid_rules),
            "validation_details": {
                rid: {vname: r.to_dict() for vname, r in results.items()}
                for rid, results in validation_results.items()
            }
        }
        
        return rules, summary
    
    def extract_and_store(self, text: str, auto_classify: bool = True) -> Dict[str, Any]:
        rules = self.extract_all_rules(text, auto_classify)
        
        stored_count = 0
        failed_count = 0
        validation_summary = {
            "passed": 0,
            "failed": 0,
            "warnings": 0
        }
        
        for rule in rules:
            if self.validator.is_rule_valid(rule):
                if self.library.store_rule(rule):
                    stored_count += 1
                    validation_summary["passed"] += 1
                else:
                    failed_count += 1
                    validation_summary["failed"] += 1
            else:
                failed_count += 1
                validation_summary["failed"] += 1
        
        return {
            "total_extracted": len(rules),
            "stored": stored_count,
            "failed": failed_count,
            "validation_summary": validation_summary,
            "rules": [r.to_dict() for r in rules]
        }
    
    def extract_from_requirement(self, requirement_text: str, requirement_id: str = "", 
                                  auto_store: bool = False) -> List[BusinessRule]:
        rules = self.extract_all_rules(requirement_text)
        
        for rule in rules:
            rule.metadata['requirement_id'] = requirement_id
            rule.tags.append(f"requirement:{requirement_id}")
            rule.source = RuleSource.REQUIREMENT
            
            if auto_store:
                self.library.store_rule(rule)
        
        return rules
    
    def rules_to_json(self, rules: List[BusinessRule]) -> str:
        return json.dumps([r.to_dict() for r in rules], ensure_ascii=False, indent=2)
    
    def rules_to_markdown(self, rules: List[BusinessRule]) -> str:
        md_lines = [
            "# 业务规则提取报告",
            "",
            f"**提取时间**: {datetime.now().isoformat()}",
            f"**规则总数**: {len(rules)}",
            ""
        ]
        
        rules_by_category = {}
        for rule in rules:
            cat = rule.category.value
            if cat not in rules_by_category:
                rules_by_category[cat] = []
            rules_by_category[cat].append(rule)
        
        for category, cat_rules in rules_by_category.items():
            md_lines.extend([
                f"## {category} ({len(cat_rules)}条)",
                ""
            ])
            
            for rule in cat_rules:
                validation_result = rule.validate()
                status_icon = "✅" if validation_result.is_valid else "❌"
                
                md_lines.extend([
                    f"### {status_icon} {rule.id}: {rule.name}",
                    "",
                    f"**描述**: {rule.description}",
                    f"**类型**: {rule.rule_type.value}",
                    f"**优先级**: {rule.priority.value}",
                    f"**状态**: {rule.status.value}",
                    f"**分类置信度**: {rule.confidence_score:.2%}",
                    f"**复杂度**: {rule.get_complexity_score():.2f}",
                    ""
                ])
                
                if rule.conditions:
                    md_lines.append("**条件**:")
                    for cond in rule.conditions:
                        md_lines.append(f"- `{cond.to_expression()}`")
                    md_lines.append("")
                
                if rule.actions:
                    md_lines.append("**动作**:")
                    for action in rule.actions:
                        md_lines.append(f"- {action.action_type}: {action.target}")
                    md_lines.append("")
                
                if rule.validation_rules:
                    md_lines.append("**验证规则**:")
                    for v in rule.validation_rules:
                        md_lines.append(f"- {v.field}: {v.validation_type}")
                        if v.parameters:
                            md_lines.append(f"  - 参数: {json.dumps(v.parameters, ensure_ascii=False)}")
                    md_lines.append("")
                
                if rule.calculation_rules:
                    md_lines.append("**计算规则**:")
                    for c in rule.calculation_rules:
                        md_lines.append(f"- {c.result_field} = {c.formula}")
                        if c.dependencies:
                            md_lines.append(f"  - 依赖: {', '.join(c.dependencies)}")
                    md_lines.append("")
                
                if rule.workflow_steps:
                    md_lines.append("**工作流步骤**:")
                    for step in rule.workflow_steps:
                        md_lines.append(f"- {step.step_id}: {step.step_name}")
                    md_lines.append("")
                
                if rule.state_transitions:
                    md_lines.append("**状态转换**:")
                    for trans in rule.state_transitions:
                        md_lines.append(f"- {trans.from_state} → {trans.to_state}")
                    md_lines.append("")
                
                if rule.tags:
                    md_lines.append(f"**标签**: {', '.join(rule.tags)}")
                    md_lines.append("")
                
                if not validation_result.is_valid:
                    md_lines.append("**验证问题**:")
                    for error in validation_result.errors:
                        md_lines.append(f"- ❌ {error}")
                    for warning in validation_result.warnings:
                        md_lines.append(f"- ⚠️ {warning}")
                    md_lines.append("")
        
        return '\n'.join(md_lines)


def main():
    extractor = BusinessRuleExtractor("test_rule_library.db")
    
    test_texts = [
        """
        如果用户登录失败超过3次，则锁定账户24小时。
        用户密码长度必须大于8位。
        订单总金额等于商品单价乘以数量。
        """,
        """
        当订单状态从"待支付"变为"已支付"时，系统必须发送确认邮件给用户。
        用户名不能为空，且必须是唯一的。
        折扣金额根据会员等级计算：VIP用户享受10%折扣，普通用户享受5%折扣。
        """,
        """
        如果库存数量小于安全库存，则自动触发补货流程。
        手机号码必须符合11位数字格式。
        实付金额 = 订单金额 - 优惠券金额 - 积分抵扣。
        第一步：用户提交订单
        第二步：系统验证库存
        第三步：生成订单并发送通知
        """,
    ]
    
    print("="*60)
    print("增强业务规则提取器测试")
    print("="*60)
    
    for i, text in enumerate(test_texts):
        print(f"\n{'='*60}")
        print(f"测试用例 {i+1}")
        print('='*60)
        print(f"原文: {text.strip()}")
        print()
        
        rules, validation_summary = extractor.extract_and_validate(text)
        print(f"提取到 {len(rules)} 条规则:")
        print(f"验证摘要: {json.dumps(validation_summary, ensure_ascii=False, indent=2)}")
        
        for rule in rules:
            print(f"\n  [{rule.id}] {rule.name}")
            print(f"  类型: {rule.rule_type.value}")
            print(f"  分类: {rule.category.value} (置信度: {rule.confidence_score:.2%})")
            print(f"  描述: {rule.description}")
            print(f"  复杂度: {rule.get_complexity_score():.2f}")
            
            validation = rule.validate()
            print(f"  验证: {'通过' if validation.is_valid else '失败'} (分数: {validation.score:.2f})")
            
            if rule.conditions:
                print(f"  条件: {[c.to_expression() for c in rule.conditions]}")
            if rule.actions:
                print(f"  动作: {[(a.action_type, a.target) for a in rule.actions]}")
            if rule.validation_rules:
                print(f"  验证: {[(v.field, v.validation_type) for v in rule.validation_rules]}")
            if rule.calculation_rules:
                print(f"  计算: {[(c.result_field, c.formula) for c in rule.calculation_rules]}")
            if rule.workflow_steps:
                print(f"  工作流: {[s.step_name for s in rule.workflow_steps]}")
            if rule.state_transitions:
                print(f"  状态转换: {[(t.from_state, t.to_state) for t in rule.state_transitions]}")
    
    print("\n" + "="*60)
    print("规则库统计")
    print("="*60)
    stats = extractor.library.get_statistics()
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    import os
    if os.path.exists("test_rule_library.db"):
        os.remove("test_rule_library.db")
        print("\n清理测试数据库")


if __name__ == "__main__":
    main()
