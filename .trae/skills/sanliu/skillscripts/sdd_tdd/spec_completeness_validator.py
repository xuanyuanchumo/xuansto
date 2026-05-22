#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规范完整性验证器

验证SDD规范的完整性，包括：
1. 必要元素检查
2. 语义一致性验证
3. 引用完整性验证
4. 测试覆盖率验证
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class CompletenessLevel(Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    INCOMPLETE = "incomplete"


@dataclass
class CompletenessReport:
    spec_id: str
    spec_name: str
    spec_kind: str
    check_time: str
    completeness_score: float
    level: CompletenessLevel
    missing_elements: Dict[str, List[str]] = field(default_factory=dict)
    quality_issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    test_coverage: Optional[Dict[str, Any]] = None
    security_analysis: Optional[Dict[str, Any]] = None
    performance_analysis: Optional[Dict[str, Any]] = None
    exception_handling_analysis: Optional[Dict[str, Any]] = None
    conditional_branch_analysis: Optional[Dict[str, Any]] = None
    detailed_metrics: Dict[str, Any] = field(default_factory=dict)


class SpecCompletenessValidator:
    """规范完整性验证器"""
    
    REQUIRED_ENTITY_ELEMENTS = ["attributes"]
    REQUIRED_INTERFACE_ELEMENTS = ["endpoints"]
    REQUIRED_ACCEPTANCE_ELEMENTS = ["scenarios"]
    
    QUALITY_CHECKS = {
        "description_quality": {
            "min_length": 10,
            "message": "描述内容过短，建议补充详细说明"
        },
        "attribute_description": {
            "check": True,
            "message": "属性缺少描述说明"
        },
        "example_data": {
            "check": True,
            "message": "缺少示例数据"
        },
        "security_constraints": {
            "check": True,
            "message": "缺少安全约束定义"
        },
        "performance_constraints": {
            "check": True,
            "message": "缺少性能约束定义"
        },
        "exception_handling": {
            "check": True,
            "message": "缺少异常处理定义"
        }
    }
    
    def validate_completeness(self, spec) -> CompletenessReport:
        check_time = datetime.now().isoformat()
        missing_elements: Dict[str, List[str]] = {}
        quality_issues: List[Dict[str, Any]] = []
        suggestions: List[str] = []
        passed_checks: List[str] = []
        failed_checks: List[str] = []
        
        self._check_required_elements(spec, missing_elements, passed_checks, failed_checks)
        self._check_metadata_completeness(spec, missing_elements, passed_checks, failed_checks)
        self._check_spec_content_quality(spec, quality_issues, passed_checks, failed_checks)
        self._check_test_coverage_readiness(spec, missing_elements, suggestions)
        self._check_cross_references(spec, quality_issues, passed_checks, failed_checks)
        
        security_analysis = self._check_security_constraints(spec, quality_issues, passed_checks, failed_checks)
        performance_analysis = self._check_performance_constraints(spec, quality_issues, passed_checks, failed_checks)
        exception_analysis = self._check_exception_handlers(spec, quality_issues, passed_checks, failed_checks)
        conditional_analysis = self._check_conditional_branches(spec, quality_issues, passed_checks, failed_checks)
        
        total_checks = len(passed_checks) + len(failed_checks)
        completeness_score = (len(passed_checks) / total_checks * 100) if total_checks > 0 else 0
        
        suggestions.extend(self._generate_completeness_suggestions(missing_elements, quality_issues))
        
        if completeness_score >= 90:
            level = CompletenessLevel.COMPLETE
        elif completeness_score >= 60:
            level = CompletenessLevel.PARTIAL
        else:
            level = CompletenessLevel.INCOMPLETE
        
        detailed_metrics = self._calculate_detailed_metrics(spec)
        
        return CompletenessReport(
            spec_id=spec.metadata.id,
            spec_name=spec.metadata.name,
            spec_kind=spec.kind.value,
            check_time=check_time,
            completeness_score=round(completeness_score, 2),
            level=level,
            missing_elements=dict(missing_elements),
            quality_issues=quality_issues,
            suggestions=suggestions,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            security_analysis=security_analysis,
            performance_analysis=performance_analysis,
            exception_handling_analysis=exception_analysis,
            conditional_branch_analysis=conditional_analysis,
            detailed_metrics=detailed_metrics
        )
    
    def _check_required_elements(self, spec, missing: Dict, passed: List, failed: List):
        kind = spec.kind.value
        
        if kind == "EntitySpec":
            if not spec.attributes:
                missing["entity"] = ["attributes"]
                failed.append("实体缺少属性定义")
            else:
                passed.append("实体属性定义完整")
        
        elif kind in ["InterfaceSpec", "ApiSpec"]:
            if not spec.endpoints:
                missing["interface"] = ["endpoints"]
                failed.append("接口缺少端点定义")
            else:
                passed.append("接口端点定义完整")
        
        elif kind == "AcceptanceSpec":
            if not spec.scenarios:
                missing["acceptance"] = ["scenarios"]
                failed.append("验收规范缺少场景定义")
            else:
                passed.append("验收场景定义完整")
        
        if not spec.spec.get("description"):
            missing["spec"] = ["description"]
            failed.append("规范缺少功能描述")
        else:
            passed.append("规范功能描述存在")
    
    def _check_metadata_completeness(self, spec, missing: Dict, passed: List, failed: List):
        required_metadata = ["id", "name", "version"]
        
        for field_name in required_metadata:
            value = getattr(spec.metadata, field_name, None)
            if not value:
                missing.setdefault("metadata", []).append(field_name)
                failed.append(f"元数据缺少{field_name}")
            else:
                passed.append(f"元数据{field_name}存在")
        
        if not spec.metadata.author:
            missing.setdefault("metadata", []).append("author")
        
        if not spec.metadata.tags:
            missing.setdefault("metadata", []).append("tags")
    
    def _check_spec_content_quality(self, spec, issues: List, passed: List, failed: List):
        description = spec.spec.get("description", "")
        if len(description) < self.QUALITY_CHECKS["description_quality"]["min_length"]:
            issues.append({
                "type": "description_quality",
                "path": "spec.description",
                "message": self.QUALITY_CHECKS["description_quality"]["message"],
                "severity": "warning"
            })
            failed.append("描述质量检查未通过")
        else:
            passed.append("描述质量检查通过")
        
        attrs_without_desc = [attr for attr in spec.attributes if not attr.description]
        if attrs_without_desc:
            issues.append({
                "type": "attribute_description",
                "path": "spec.attributes",
                "message": f"{len(attrs_without_desc)}个属性缺少描述: {[a.name for a in attrs_without_desc[:5]]}",
                "severity": "warning"
            })
            failed.append("属性描述检查未通过")
        else:
            passed.append("属性描述检查通过")
        
        has_example = any(attr.example is not None for attr in spec.attributes)
        if spec.attributes and not has_example:
            issues.append({
                "type": "example_data",
                "path": "spec.attributes",
                "message": self.QUALITY_CHECKS["example_data"]["message"],
                "severity": "info"
            })
    
    def _check_test_coverage_readiness(self, spec, missing: Dict, suggestions: List):
        if spec.scenarios:
            scenarios_without_data = [s for s in spec.scenarios if not s.test_data]
            if scenarios_without_data:
                missing.setdefault("test_readiness", []).append("test_data")
                suggestions.append(f"{len(scenarios_without_data)}个场景缺少测试数据")
        
        if spec.endpoints:
            endpoints_without_response = [e for e in spec.endpoints if not e.response]
            if endpoints_without_response:
                missing.setdefault("test_readiness", []).append("response_definition")
                suggestions.append(f"{len(endpoints_without_response)}个端点缺少响应定义")
    
    def _check_cross_references(self, spec, issues: List, passed: List, failed: List):
        unresolved_refs = [ref for ref in spec.references if not ref.resolved]
        
        if unresolved_refs:
            issues.append({
                "type": "unresolved_references",
                "path": "spec.references",
                "message": f"{len(unresolved_refs)}个引用未解析",
                "severity": "error",
                "details": [{"path": r.ref_path, "target": r.target_spec_id} for r in unresolved_refs]
            })
            failed.append("引用解析检查未通过")
        else:
            passed.append("引用解析检查通过")
        
        if spec.inheritance and spec.inheritance.parent_spec_id and not spec.inheritance.parent_spec:
            issues.append({
                "type": "unresolved_inheritance",
                "path": "spec.inheritance",
                "message": f"父规范未找到: {spec.inheritance.parent_spec_id}",
                "severity": "error"
            })
            failed.append("继承解析检查未通过")
        else:
            passed.append("继承解析检查通过")
    
    def _check_security_constraints(self, spec, issues: List, passed: List, failed: List) -> Dict[str, Any]:
        analysis = {
            "has_security_constraints": len(spec.security_constraints) > 0,
            "total_constraints": len(spec.security_constraints),
            "auth_required_count": 0,
            "authorization_defined": False,
            "rate_limit_defined": False,
            "encryption_defined": False,
            "issues": []
        }
        
        if not spec.security_constraints:
            issues.append({
                "type": "security_constraints",
                "path": "spec.security_constraints",
                "message": "缺少安全约束定义",
                "severity": "warning"
            })
            failed.append("安全约束检查未通过")
            return analysis
        
        for constraint in spec.security_constraints:
            if constraint.authentication_required:
                analysis["auth_required_count"] += 1
            if constraint.authorization_roles:
                analysis["authorization_defined"] = True
            if constraint.rate_limit:
                analysis["rate_limit_defined"] = True
            if constraint.encryption_required:
                analysis["encryption_defined"] = True
        
        if analysis["auth_required_count"] > 0:
            passed.append("认证约束已定义")
        else:
            analysis["issues"].append("未定义认证要求")
        
        if analysis["authorization_defined"]:
            passed.append("授权约束已定义")
        
        if analysis["rate_limit_defined"]:
            passed.append("速率限制已定义")
        
        return analysis
    
    def _check_performance_constraints(self, spec, issues: List, passed: List, failed: List) -> Dict[str, Any]:
        analysis = {
            "has_performance_constraints": len(spec.performance_constraints) > 0,
            "total_constraints": len(spec.performance_constraints),
            "response_time_defined": False,
            "throughput_defined": False,
            "percentiles_defined": False,
            "issues": []
        }
        
        if not spec.performance_constraints:
            issues.append({
                "type": "performance_constraints",
                "path": "spec.performance_constraints",
                "message": "缺少性能约束定义",
                "severity": "warning"
            })
            failed.append("性能约束检查未通过")
            return analysis
        
        for constraint in spec.performance_constraints:
            if constraint.metric in ["response_time", "responseTime"]:
                analysis["response_time_defined"] = True
            if constraint.metric in ["throughput", "rps"]:
                analysis["throughput_defined"] = True
            if constraint.percentiles:
                analysis["percentiles_defined"] = True
        
        if analysis["response_time_defined"]:
            passed.append("响应时间约束已定义")
        else:
            analysis["issues"].append("未定义响应时间要求")
        
        if analysis["throughput_defined"]:
            passed.append("吞吐量约束已定义")
        
        return analysis
    
    def _check_exception_handlers(self, spec, issues: List, passed: List, failed: List) -> Dict[str, Any]:
        analysis = {
            "has_exception_handlers": len(spec.exception_handlers) > 0,
            "total_handlers": len(spec.exception_handlers),
            "has_retry_policy": False,
            "has_fallback": False,
            "covered_exceptions": [],
            "issues": []
        }
        
        if not spec.exception_handlers:
            issues.append({
                "type": "exception_handling",
                "path": "spec.exception_handlers",
                "message": "缺少异常处理定义",
                "severity": "warning"
            })
            failed.append("异常处理检查未通过")
            return analysis
        
        for handler in spec.exception_handlers:
            analysis["covered_exceptions"].append(handler.exception_type)
            if handler.retry_policy:
                analysis["has_retry_policy"] = True
            if handler.fallback_behavior:
                analysis["has_fallback"] = True
        
        passed.append(f"异常处理已定义 ({len(spec.exception_handlers)}个)")
        
        if analysis["has_retry_policy"]:
            passed.append("重试策略已定义")
        
        if analysis["has_fallback"]:
            passed.append("降级策略已定义")
        
        return analysis
    
    def _check_conditional_branches(self, spec, issues: List, passed: List, failed: List) -> Dict[str, Any]:
        analysis = {
            "has_conditional_branches": len(spec.conditional_branches) > 0,
            "total_branches": len(spec.conditional_branches),
            "has_else_branches": False,
            "max_nesting_depth": 0,
            "issues": []
        }
        
        if not spec.conditional_branches:
            passed.append("无复杂条件分支")
            return analysis
        
        def count_nesting(branch, depth=1):
            max_depth = depth
            if branch.else_branch:
                analysis["has_else_branches"] = True
            for nested in branch.nested_conditions:
                nested_depth = count_nesting(nested, depth + 1)
                max_depth = max(max_depth, nested_depth)
            return max_depth
        
        for branch in spec.conditional_branches:
            nesting = count_nesting(branch)
            analysis["max_nesting_depth"] = max(analysis["max_nesting_depth"], nesting)
        
        passed.append(f"条件分支已定义 ({len(spec.conditional_branches)}个)")
        
        if analysis["max_nesting_depth"] > 3:
            issues.append({
                "type": "complex_conditional",
                "path": "spec.conditional_branches",
                "message": f"条件分支嵌套深度过深 ({analysis['max_nesting_depth']}层)",
                "severity": "warning"
            })
            analysis["issues"].append("条件分支嵌套过深")
        
        return analysis
    
    def _calculate_detailed_metrics(self, spec) -> Dict[str, Any]:
        metrics = {
            "attributes": {
                "total": len(spec.attributes),
                "with_description": sum(1 for a in spec.attributes if a.description),
                "with_validation": sum(1 for a in spec.attributes if a.constraints or a.validation_rules),
                "with_examples": sum(1 for a in spec.attributes if a.example is not None),
            },
            "endpoints": {
                "total": len(spec.endpoints),
                "with_auth": sum(1 for e in spec.endpoints if e.authentication),
                "with_errors": sum(1 for e in spec.endpoints if e.errors),
                "with_response": sum(1 for e in spec.endpoints if e.response),
            },
            "scenarios": {
                "total": len(spec.scenarios),
                "with_test_data": sum(1 for s in spec.scenarios if s.test_data),
            },
            "constraints": {
                "total": len(spec.constraints),
                "business": sum(1 for c in spec.constraints if c.type == "business"),
                "validation": sum(1 for c in spec.constraints if c.type == "validation"),
            },
            "business_rules": {
                "total": len(spec.business_rules),
                "enabled": sum(1 for r in spec.business_rules if r.enabled),
            },
            "security": {
                "total": len(spec.security_constraints),
                "auth_required": sum(1 for s in spec.security_constraints if s.authentication_required),
            },
            "performance": {
                "total": len(spec.performance_constraints),
            },
            "exceptions": {
                "total": len(spec.exception_handlers),
            },
            "conditional_branches": {
                "total": len(spec.conditional_branches),
            },
        }
        
        return metrics
    
    def _generate_completeness_suggestions(self, missing: Dict, issues: List) -> List[str]:
        suggestions = []
        
        for category, items in missing.items():
            if items:
                suggestions.append(f"建议补充{category}中的: {', '.join(items)}")
        
        error_issues = [i for i in issues if i.get("severity") == "error"]
        if error_issues:
            suggestions.append(f"发现{len(error_issues)}个严重问题需要修复")
        
        warning_issues = [i for i in issues if i.get("severity") == "warning"]
        if warning_issues:
            suggestions.append(f"发现{len(warning_issues)}个警告建议处理")
        
        return suggestions


def main():
    import argparse
    from pathlib import Path
    from enhanced_spec_parser import EnhancedSDDSpecParser
    
    parser = argparse.ArgumentParser(description="规范完整性验证器")
    parser.add_argument("spec_file", help="规范文件路径")
    
    args = parser.parse_args()
    
    spec_parser = EnhancedSDDSpecParser()
    validator = SpecCompletenessValidator()
    
    try:
        spec, validation_result = spec_parser.parse_file(args.spec_file)
        
        print(f"规范解析成功: {spec.metadata.name}")
        
        report = validator.validate_completeness(spec)
        
        print(f"\n完整性检查:")
        print(f"  完整性得分: {report.completeness_score}%")
        print(f"  完整性级别: {report.level.value}")
        print(f"  通过检查: {len(report.passed_checks)}")
        print(f"  未通过检查: {len(report.failed_checks)}")
        print(f"  质量问题: {len(report.quality_issues)}")
        
        if report.suggestions:
            print(f"\n  改进建议:")
            for suggestion in report.suggestions[:5]:
                print(f"    - {suggestion}")
    
    except FileNotFoundError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"验证错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
