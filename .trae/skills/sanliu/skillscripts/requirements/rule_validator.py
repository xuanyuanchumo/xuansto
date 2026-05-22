#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
规则验证器
支持一致性检查、冲突检测
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, Set
from enum import Enum
from datetime import datetime


class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ConflictType(Enum):
    CONTRADICTION = "contradiction"
    REDUNDANCY = "redundancy"
    INCONSISTENCY = "inconsistency"
    OVERLAP = "overlap"
    DEPENDENCY_CYCLE = "dependency_cycle"


@dataclass
class ValidationIssue:
    rule_id: str
    rule_name: str
    severity: ValidationSeverity
    issue_type: str
    description: str
    suggestion: Optional[str] = None
    related_rules: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "issue_type": self.issue_type,
            "description": self.description,
            "suggestion": self.suggestion,
            "related_rules": self.related_rules
        }


@dataclass
class ConflictReport:
    conflict_type: ConflictType
    rule_ids: List[str]
    description: str
    severity: ValidationSeverity
    resolution_suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_type": self.conflict_type.value,
            "rule_ids": self.rule_ids,
            "description": self.description,
            "severity": self.severity.value,
            "resolution_suggestions": self.resolution_suggestions
        }


@dataclass
class ValidationResult:
    is_valid: bool
    issues: List[ValidationIssue]
    conflicts: List[ConflictReport]
    checked_rules_count: int
    check_time: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "issues": [i.to_dict() for i in self.issues],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "checked_rules_count": self.checked_rules_count,
            "check_time": self.check_time
        }


class RuleValidator:
    CONTRADICTION_PATTERNS = [
        (re.compile(r'必须(.+?)，?不能\1'), "自我矛盾"),
        (re.compile(r'禁止(.+?)，?允许\1'), "禁止与允许矛盾"),
        (re.compile(r'不能(.+?)，?必须\1'), "不能与必须矛盾"),
    ]
    
    REDUNDANCY_THRESHOLD = 0.8
    
    def __init__(self):
        self._rule_cache: Dict[str, Dict[str, Any]] = {}
    
    def _normalize_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_conditions(self, rule_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        conditions = []
        
        if 'conditions' in rule_content:
            conditions.extend(rule_content['conditions'])
        
        if 'validation_rules' in rule_content:
            for v in rule_content['validation_rules']:
                conditions.append({
                    'field': v.get('field'),
                    'operator': v.get('validation_type'),
                    'value': v.get('parameters', {}).get('value')
                })
        
        return conditions
    
    def _extract_actions(self, rule_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        actions = []
        
        if 'actions' in rule_content:
            actions.extend(rule_content['actions'])
        
        return actions
    
    def _check_field_consistency(self, rules: List[Dict[str, Any]]) -> List[ValidationIssue]:
        issues = []
        field_definitions: Dict[str, List[Tuple[str, str, Any]]] = {}
        
        for rule in rules:
            rule_id = rule.get('id', 'unknown')
            rule_name = rule.get('name', 'unknown')
            content = rule.get('content', {})
            
            conditions = self._extract_conditions(content)
            for cond in conditions:
                field = cond.get('field')
                if field:
                    if field not in field_definitions:
                        field_definitions[field] = []
                    field_definitions[field].append((rule_id, rule_name, cond))
        
        for field, definitions in field_definitions.items():
            if len(definitions) > 1:
                types = set()
                for _, _, cond in definitions:
                    val = cond.get('value')
                    if val is not None:
                        types.add(type(val).__name__)
                
                if len(types) > 1:
                    issue = ValidationIssue(
                        rule_id=definitions[0][0],
                        rule_name=definitions[0][1],
                        severity=ValidationSeverity.WARNING,
                        issue_type="field_type_inconsistency",
                        description=f"字段 '{field}' 在不同规则中使用了不同的数据类型: {types}",
                        suggestion="统一字段的数据类型定义",
                        related_rules=[d[0] for d in definitions]
                    )
                    issues.append(issue)
        
        return issues
    
    def _check_value_consistency(self, rules: List[Dict[str, Any]]) -> List[ValidationIssue]:
        issues = []
        
        for rule in rules:
            rule_id = rule.get('id', 'unknown')
            rule_name = rule.get('name', 'unknown')
            content = rule.get('content', {})
            source_text = rule.get('source_text', '')
            
            for pattern, issue_type in self.CONTRADICTION_PATTERNS:
                if pattern.search(source_text):
                    issue = ValidationIssue(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        severity=ValidationSeverity.ERROR,
                        issue_type=issue_type,
                        description=f"规则中存在矛盾表述",
                        suggestion="检查并修正规则表述"
                    )
                    issues.append(issue)
        
        return issues
    
    def _check_calculation_consistency(self, rules: List[Dict[str, Any]]) -> List[ValidationIssue]:
        issues = []
        calculations: Dict[str, List[Tuple[str, str, str]]] = {}
        
        for rule in rules:
            rule_id = rule.get('id', 'unknown')
            rule_name = rule.get('name', 'unknown')
            content = rule.get('content', {})
            
            if 'calculation_rules' in content:
                for calc in content['calculation_rules']:
                    result_field = calc.get('result_field')
                    formula = calc.get('formula', '')
                    
                    if result_field:
                        if result_field not in calculations:
                            calculations[result_field] = []
                        calculations[result_field].append((rule_id, rule_name, formula))
        
        for field, calcs in calculations.items():
            if len(calcs) > 1:
                formulas = [c[2] for c in calcs]
                unique_formulas = set(formulas)
                
                if len(unique_formulas) > 1:
                    issue = ValidationIssue(
                        rule_id=calcs[0][0],
                        rule_name=calcs[0][1],
                        severity=ValidationSeverity.ERROR,
                        issue_type="calculation_inconsistency",
                        description=f"字段 '{field}' 有多个不同的计算公式: {unique_formulas}",
                        suggestion="统一计算公式或明确不同场景下的计算规则",
                        related_rules=[c[0] for c in calcs]
                    )
                    issues.append(issue)
        
        return issues
    
    def _detect_contradiction_conflicts(self, rules: List[Dict[str, Any]]) -> List[ConflictReport]:
        conflicts = []
        
        for i, rule1 in enumerate(rules):
            for rule2 in rules[i+1:]:
                content1 = rule1.get('content', {})
                content2 = rule2.get('content', {})
                
                conditions1 = self._extract_conditions(content1)
                conditions2 = self._extract_conditions(content2)
                actions1 = self._extract_actions(content1)
                actions2 = self._extract_actions(content2)
                
                same_conditions = False
                for c1 in conditions1:
                    for c2 in conditions2:
                        if (c1.get('field') == c2.get('field') and
                            c1.get('operator') == c2.get('operator') and
                            c1.get('value') == c2.get('value')):
                            same_conditions = True
                            break
                
                if same_conditions:
                    for a1 in actions1:
                        for a2 in actions2:
                            if (a1.get('target') == a2.get('target') and
                                a1.get('action_type') != a2.get('action_type')):
                                
                                if ((a1.get('action_type') == 'must' and a2.get('action_type') == 'forbidden') or
                                    (a1.get('action_type') == 'forbidden' and a2.get('action_type') == 'must')):
                                    
                                    conflict = ConflictReport(
                                        conflict_type=ConflictType.CONTRADICTION,
                                        rule_ids=[rule1.get('id'), rule2.get('id')],
                                        description=f"规则 '{rule1.get('name')}' 和 '{rule2.get('name')}' 存在矛盾",
                                        severity=ValidationSeverity.ERROR,
                                        resolution_suggestions=[
                                            "检查两个规则的适用场景",
                                            "合并或修改其中一个规则",
                                            "添加更明确的条件区分"
                                        ]
                                    )
                                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_redundancy_conflicts(self, rules: List[Dict[str, Any]]) -> List[ConflictReport]:
        conflicts = []
        
        for i, rule1 in enumerate(rules):
            for rule2 in rules[i+1:]:
                text1 = self._normalize_text(rule1.get('source_text', rule1.get('description', '')))
                text2 = self._normalize_text(rule2.get('source_text', rule2.get('description', '')))
                
                if not text1 or not text2:
                    continue
                
                words1 = set(text1.split())
                words2 = set(text2.split())
                
                if not words1 or not words2:
                    continue
                
                intersection = words1 & words2
                union = words1 | words2
                
                similarity = len(intersection) / len(union) if union else 0
                
                if similarity >= self.REDUNDANCY_THRESHOLD:
                    conflict = ConflictReport(
                        conflict_type=ConflictType.REDUNDANCY,
                        rule_ids=[rule1.get('id'), rule2.get('id')],
                        description=f"规则 '{rule1.get('name')}' 和 '{rule2.get('name')}' 高度相似 ({similarity:.1%})",
                        severity=ValidationSeverity.WARNING,
                        resolution_suggestions=[
                            "合并重复的规则",
                            "保留更完整或更准确的规则",
                            "检查是否为有意为之的重复"
                        ]
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_overlap_conflicts(self, rules: List[Dict[str, Any]]) -> List[ConflictReport]:
        conflicts = []
        
        for i, rule1 in enumerate(rules):
            for rule2 in rules[i+1:]:
                content1 = rule1.get('content', {})
                content2 = rule2.get('content', {})
                
                conditions1 = self._extract_conditions(content1)
                conditions2 = self._extract_conditions(content2)
                
                for c1 in conditions1:
                    for c2 in conditions2:
                        if c1.get('field') == c2.get('field'):
                            op1 = c1.get('operator', '')
                            op2 = c2.get('operator', '')
                            val1 = c1.get('value')
                            val2 = c2.get('value')
                            
                            overlap = False
                            
                            if op1 == '>' and op2 == '<' and val1 is not None and val2 is not None:
                                if val1 >= val2:
                                    overlap = True
                            elif op1 == '<' and op2 == '>' and val1 is not None and val2 is not None:
                                if val1 <= val2:
                                    overlap = True
                            elif op1 == '>=' and op2 == '<=' and val1 is not None and val2 is not None:
                                if val1 > val2:
                                    overlap = True
                            
                            if overlap:
                                conflict = ConflictReport(
                                    conflict_type=ConflictType.OVERLAP,
                                    rule_ids=[rule1.get('id'), rule2.get('id')],
                                    description=f"规则 '{rule1.get('name')}' 和 '{rule2.get('name')}' 的条件范围重叠",
                                    severity=ValidationSeverity.WARNING,
                                    resolution_suggestions=[
                                        "调整条件范围避免重叠",
                                        "明确规则的优先级",
                                        "添加边界条件说明"
                                    ]
                                )
                                conflicts.append(conflict)
        
        return conflicts
    
    def _detect_dependency_cycles(self, rules: List[Dict[str, Any]]) -> List[ConflictReport]:
        conflicts = []
        dependencies: Dict[str, Set[str]] = {}
        
        for rule in rules:
            rule_id = rule.get('id')
            content = rule.get('content', {})
            
            deps = set()
            
            if 'calculation_rules' in content:
                for calc in content['calculation_rules']:
                    deps.update(calc.get('dependencies', []))
            
            if 'conditions' in content:
                for cond in content['conditions']:
                    field = cond.get('field')
                    if field:
                        deps.add(field)
            
            dependencies[rule_id] = deps
        
        def find_cycle(node: str, visited: Set[str], path: List[str]) -> Optional[List[str]]:
            if node in path:
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]
            
            if node in visited:
                return None
            
            visited.add(node)
            path.append(node)
            
            for dep in dependencies.get(node, set()):
                cycle = find_cycle(dep, visited, path)
                if cycle:
                    return cycle
            
            path.pop()
            return None
        
        visited: Set[str] = set()
        
        for rule_id in dependencies:
            if rule_id not in visited:
                cycle = find_cycle(rule_id, visited, [])
                if cycle:
                    conflict = ConflictReport(
                        conflict_type=ConflictType.DEPENDENCY_CYCLE,
                        rule_ids=list(set(cycle)),
                        description=f"检测到依赖循环: {' -> '.join(cycle)}",
                        severity=ValidationSeverity.ERROR,
                        resolution_suggestions=[
                            "重新设计规则依赖关系",
                            "打破循环依赖",
                            "使用中间变量或规则"
                        ]
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def validate_single_rule(self, rule: Dict[str, Any]) -> List[ValidationIssue]:
        issues = []
        rule_id = rule.get('id', 'unknown')
        rule_name = rule.get('name', 'unknown')
        content = rule.get('content', {})
        
        if not rule.get('name'):
            issues.append(ValidationIssue(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=ValidationSeverity.ERROR,
                issue_type="missing_name",
                description="规则缺少名称"
            ))
        
        if not rule.get('description'):
            issues.append(ValidationIssue(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=ValidationSeverity.WARNING,
                issue_type="missing_description",
                description="规则缺少描述",
                suggestion="添加规则描述以便于理解"
            ))
        
        if not content:
            issues.append(ValidationIssue(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=ValidationSeverity.ERROR,
                issue_type="empty_content",
                description="规则内容为空"
            ))
        
        if 'conditions' in content:
            for i, cond in enumerate(content['conditions']):
                if not cond.get('field'):
                    issues.append(ValidationIssue(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        severity=ValidationSeverity.ERROR,
                        issue_type=f"invalid_condition_{i}",
                        description=f"条件 {i+1} 缺少字段名"
                    ))
        
        if 'calculation_rules' in content:
            for i, calc in enumerate(content['calculation_rules']):
                if not calc.get('formula'):
                    issues.append(ValidationIssue(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        severity=ValidationSeverity.ERROR,
                        issue_type=f"invalid_calculation_{i}",
                        description=f"计算规则 {i+1} 缺少公式"
                    ))
        
        return issues
    
    def validate_rules(self, rules: List[Dict[str, Any]]) -> ValidationResult:
        all_issues: List[ValidationIssue] = []
        all_conflicts: List[ConflictReport] = []
        
        for rule in rules:
            issues = self.validate_single_rule(rule)
            all_issues.extend(issues)
        
        all_issues.extend(self._check_field_consistency(rules))
        all_issues.extend(self._check_value_consistency(rules))
        all_issues.extend(self._check_calculation_consistency(rules))
        
        all_conflicts.extend(self._detect_contradiction_conflicts(rules))
        all_conflicts.extend(self._detect_redundancy_conflicts(rules))
        all_conflicts.extend(self._detect_overlap_conflicts(rules))
        all_conflicts.extend(self._detect_dependency_cycles(rules))
        
        has_errors = any(
            issue.severity == ValidationSeverity.ERROR 
            for issue in all_issues
        ) or any(
            conflict.severity == ValidationSeverity.ERROR
            for conflict in all_conflicts
        )
        
        return ValidationResult(
            is_valid=not has_errors,
            issues=all_issues,
            conflicts=all_conflicts,
            checked_rules_count=len(rules),
            check_time=datetime.now().isoformat()
        )
    
    def generate_validation_report(self, result: ValidationResult) -> str:
        lines = [
            "# 规则验证报告",
            "",
            f"**验证时间**: {result.check_time}",
            f"**检查规则数**: {result.checked_rules_count}",
            f"**验证结果**: {'通过' if result.is_valid else '存在问题'}",
            ""
        ]
        
        error_count = sum(1 for i in result.issues if i.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for i in result.issues if i.severity == ValidationSeverity.WARNING)
        info_count = sum(1 for i in result.issues if i.severity == ValidationSeverity.INFO)
        
        lines.extend([
            "## 问题统计",
            "",
            f"- 错误: {error_count}",
            f"- 警告: {warning_count}",
            f"- 信息: {info_count}",
            ""
        ])
        
        if result.issues:
            lines.extend([
                "## 问题详情",
                ""
            ])
            
            for issue in result.issues:
                severity_icon = {
                    ValidationSeverity.ERROR: "❌",
                    ValidationSeverity.WARNING: "⚠️",
                    ValidationSeverity.INFO: "ℹ️"
                }.get(issue.severity, "")
                
                lines.append(f"### {severity_icon} {issue.issue_type}")
                lines.append(f"- **规则**: {issue.rule_name} ({issue.rule_id})")
                lines.append(f"- **描述**: {issue.description}")
                if issue.suggestion:
                    lines.append(f"- **建议**: {issue.suggestion}")
                if issue.related_rules:
                    lines.append(f"- **相关规则**: {', '.join(issue.related_rules)}")
                lines.append("")
        
        if result.conflicts:
            lines.extend([
                "## 冲突检测",
                ""
            ])
            
            for conflict in result.conflicts:
                lines.append(f"### {conflict.conflict_type.value}")
                lines.append(f"- **涉及规则**: {', '.join(conflict.rule_ids)}")
                lines.append(f"- **描述**: {conflict.description}")
                lines.append(f"- **严重程度**: {conflict.severity.value}")
                if conflict.resolution_suggestions:
                    lines.append("- **解决建议**:")
                    for suggestion in conflict.resolution_suggestions:
                        lines.append(f"  - {suggestion}")
                lines.append("")
        
        return '\n'.join(lines)


def main():
    validator = RuleValidator()
    
    test_rules = [
        {
            "id": "RULE-001",
            "name": "密码长度验证",
            "description": "用户密码长度必须在8-20位之间",
            "source_text": "用户密码长度必须在8-20位之间",
            "content": {
                "validation_rules": [
                    {"field": "password", "validation_type": "min_length", "parameters": {"min_length": 8}},
                    {"field": "password", "validation_type": "max_length", "parameters": {"max_length": 20}}
                ]
            }
        },
        {
            "id": "RULE-002",
            "name": "密码长度验证（冲突）",
            "description": "用户密码长度必须大于10位",
            "source_text": "用户密码长度必须大于10位",
            "content": {
                "validation_rules": [
                    {"field": "password", "validation_type": "min_length", "parameters": {"min_length": 10}}
                ]
            }
        },
        {
            "id": "RULE-003",
            "name": "订单金额计算",
            "description": "订单总金额等于单价乘以数量",
            "source_text": "订单总金额等于单价乘以数量",
            "content": {
                "calculation_rules": [
                    {"result_field": "total_amount", "formula": "price * quantity", "dependencies": ["price", "quantity"]}
                ]
            }
        },
        {
            "id": "RULE-004",
            "name": "订单金额计算（冲突）",
            "description": "订单总金额等于单价乘以数量减去折扣",
            "source_text": "订单总金额等于单价乘以数量减去折扣",
            "content": {
                "calculation_rules": [
                    {"result_field": "total_amount", "formula": "price * quantity - discount", "dependencies": ["price", "quantity", "discount"]}
                ]
            }
        },
        {
            "id": "RULE-005",
            "name": "用户登录规则",
            "description": "如果用户登录失败超过3次，则锁定账户",
            "source_text": "如果用户登录失败超过3次，则锁定账户",
            "content": {
                "conditions": [{"field": "login_failures", "operator": ">", "value": 3}],
                "actions": [{"action_type": "must", "target": "lock_account"}]
            }
        },
        {
            "id": "RULE-006",
            "name": "用户登录规则（矛盾）",
            "description": "如果用户登录失败超过3次，则允许继续登录",
            "source_text": "如果用户登录失败超过3次，则允许继续登录",
            "content": {
                "conditions": [{"field": "login_failures", "operator": ">", "value": 3}],
                "actions": [{"action_type": "can", "target": "continue_login"}]
            }
        }
    ]
    
    print("="*60)
    print("规则验证测试")
    print("="*60)
    
    result = validator.validate_rules(test_rules)
    
    print(f"\n验证结果: {'通过' if result.is_valid else '存在问题'}")
    print(f"检查规则数: {result.checked_rules_count}")
    print(f"发现问题: {len(result.issues)}")
    print(f"检测冲突: {len(result.conflicts)}")
    
    print("\n" + "="*60)
    print("验证报告")
    print("="*60)
    
    report = validator.generate_validation_report(result)
    print(report)


if __name__ == "__main__":
    main()
