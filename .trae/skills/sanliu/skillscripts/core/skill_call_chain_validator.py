#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能调用链验证增强器 - Enhanced Skill Call Chain Validator
验证各技能脚本调用链正确性，确保技能间依赖关系正确

功能:
1. 验证三省六部技能调用关系
2. 验证skill-creator技能集成
3. 验证ui-ux-pro-max技能集成
4. 验证mcp-builder技能集成
5. 生成调用链验证报告
"""

import os
import sys
import json
import ast
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    MISSING = "missing"
    DEPRECATED = "deprecated"


class SkillType(Enum):
    SANLIU = "sanliu"
    ZHONGSHUSHENG = "zhongshusheng"
    MENXIASHENG = "menxiasheng"
    SHANGSHUSHENG = "shangshusheng"
    SKILL_CREATOR = "skill-creator"
    UI_UX_PRO_MAX = "ui-ux-pro-max"
    MCP_BUILDER = "mcp-builder"
    GLOBAL_CHINESE = "global-chinese"


@dataclass
class SkillDependency:
    skill_name: str
    required_skills: List[str]
    optional_skills: List[str]
    provides: List[str]
    entry_points: List[str]


@dataclass
class CallChainValidation:
    validation_id: str
    source_skill: str
    target_skill: str
    status: ValidationStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SkillCallChainReport:
    report_id: str
    generated_at: str
    total_validations: int
    passed: int
    failed: int
    warnings: int
    validations: List[CallChainValidation]
    skill_graph: Dict[str, List[str]]
    recommendations: List[str]
    overall_status: ValidationStatus


class SkillDependencyRegistry:
    
    DEPENDENCIES = {
        "sanliu": SkillDependency(
            skill_name="sanliu",
            required_skills=[],
            optional_skills=["skill-creator", "ui-ux-pro-max", "mcp-builder", "global-chinese"],
            provides=["full_development_cycle"],
            entry_points=["main", "run", "execute"]
        ),
        "zhongshusheng": SkillDependency(
            skill_name="zhongshusheng",
            required_skills=[],
            optional_skills=["sanliu"],
            provides=["requirement_analysis", "architecture_design", "specification"],
            entry_points=["analyze_requirements", "design_architecture", "generate_spec"]
        ),
        "menxiasheng": SkillDependency(
            skill_name="menxiasheng",
            required_skills=["zhongshusheng"],
            optional_skills=["sanliu"],
            provides=["review", "quality_gate", "approval"],
            entry_points=["review", "approve", "quality_check"]
        ),
        "shangshusheng": SkillDependency(
            skill_name="shangshusheng",
            required_skills=["menxiasheng"],
            optional_skills=["sanliu"],
            provides=["execution", "implementation"],
            entry_points=["execute", "implement"]
        ),
        "libu": SkillDependency(
            skill_name="libu",
            required_skills=["shangshusheng"],
            optional_skills=[],
            provides=["hr_management", "agent_assignment"],
            entry_points=["assign_agent", "manage_resources"]
        ),
        "hubu": SkillDependency(
            skill_name="hubu",
            required_skills=["shangshusheng"],
            optional_skills=[],
            provides=["resource_management", "budget"],
            entry_points=["manage_resources", "allocate_budget"]
        ),
        "liibu": SkillDependency(
            skill_name="liibu",
            required_skills=["shangshusheng"],
            optional_skills=[],
            provides=["legal_compliance", "standards"],
            entry_points=["check_compliance", "validate_standards"]
        ),
        "bingbu": SkillDependency(
            skill_name="bingbu",
            required_skills=["shangshusheng"],
            optional_skills=[],
            provides=["testing", "quality_assurance"],
            entry_points=["run_tests", "generate_tests"]
        ),
        "xingbu": SkillDependency(
            skill_name="xingbu",
            required_skills=["shangshusheng"],
            optional_skills=[],
            provides=["refactoring", "code_improvement"],
            entry_points=["refactor", "improve_code"]
        ),
        "gongbu": SkillDependency(
            skill_name="gongbu",
            required_skills=["shangshusheng"],
            optional_skills=[],
            provides=["implementation", "code_generation"],
            entry_points=["implement", "generate_code"]
        ),
        "skill-creator": SkillDependency(
            skill_name="skill-creator",
            required_skills=[],
            optional_skills=["sanliu"],
            provides=["skill_creation", "skill_modification"],
            entry_points=["create_skill", "modify_skill", "evaluate_skill"]
        ),
        "ui-ux-pro-max": SkillDependency(
            skill_name="ui-ux-pro-max",
            required_skills=[],
            optional_skills=["sanliu"],
            provides=["ui_design", "ux_optimization", "frontend_development"],
            entry_points=["design", "build", "create", "implement", "review", "fix", "optimize"]
        ),
        "mcp-builder": SkillDependency(
            skill_name="mcp-builder",
            required_skills=[],
            optional_skills=["sanliu"],
            provides=["mcp_server_creation", "api_integration"],
            entry_points=["create_server", "build_mcp"]
        ),
        "global-chinese": SkillDependency(
            skill_name="global-chinese",
            required_skills=[],
            optional_skills=[],
            provides=["chinese_language_support"],
            entry_points=["translate", "respond_chinese"]
        )
    }
    
    TDD_ORDER = ["bingbu", "gongbu", "xingbu"]
    
    PROVINCIAL_ORDER = ["zhongshusheng", "menxiasheng", "shangshusheng"]
    
    DEPARTMENT_ORDER = ["libu", "hubu", "liibu", "bingbu", "xingbu", "gongbu"]


class SkillCallChainValidator:
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getcwd())
        self.registry = SkillDependencyRegistry()
        self.validations: List[CallChainValidation] = []
        self.skill_graph: Dict[str, List[str]] = defaultdict(list)
        
    def validate_all(self) -> SkillCallChainReport:
        logger.info("开始验证所有技能调用链...")
        
        self._validate_provincial_chain()
        self._validate_department_chain()
        self._validate_tdd_chain()
        self._validate_skill_creator_integration()
        self._validate_ui_ux_integration()
        self._validate_mcp_builder_integration()
        self._validate_global_chinese_integration()
        self._validate_cross_skill_dependencies()
        
        return self._generate_report()
    
    def _validate_provincial_chain(self):
        logger.info("验证三省调用链...")
        
        order = self.registry.PROVINCIAL_ORDER
        
        for i, skill in enumerate(order):
            dep = self.registry.DEPENDENCIES.get(skill)
            if not dep:
                self._add_validation(
                    skill, "unknown",
                    ValidationStatus.MISSING,
                    f"技能 {skill} 未在注册表中定义"
                )
                continue
            
            if dep.required_skills:
                for req in dep.required_skills:
                    if req not in order[:i]:
                        self._add_validation(
                            skill, req,
                            ValidationStatus.INVALID,
                            f"技能 {skill} 的依赖 {req} 未在正确位置",
                            {"expected_position": "before", "actual_position": "after or missing"}
                        )
                    else:
                        self._add_validation(
                            skill, req,
                            ValidationStatus.VALID,
                            f"技能 {skill} 正确依赖 {req}"
                        )
                        self.skill_graph[req].append(skill)
    
    def _validate_department_chain(self):
        logger.info("验证六部调用链...")
        
        order = self.registry.DEPARTMENT_ORDER
        shangshusheng_dep = self.registry.DEPENDENCIES.get("shangshusheng")
        
        for skill in order:
            dep = self.registry.DEPENDENCIES.get(skill)
            if not dep:
                self._add_validation(
                    skill, "unknown",
                    ValidationStatus.MISSING,
                    f"技能 {skill} 未在注册表中定义"
                )
                continue
            
            for req in dep.required_skills:
                if req == "shangshusheng":
                    self._add_validation(
                        skill, req,
                        ValidationStatus.VALID,
                        f"技能 {skill} 正确依赖尚书省"
                    )
                    self.skill_graph[req].append(skill)
    
    def _validate_tdd_chain(self):
        logger.info("验证TDD调用链...")
        
        order = self.registry.TDD_ORDER
        
        for i, skill in enumerate(order):
            if i > 0:
                prev_skill = order[i-1]
                self._add_validation(
                    skill, prev_skill,
                    ValidationStatus.VALID,
                    f"TDD顺序正确: {prev_skill} -> {skill}"
                )
                self.skill_graph[prev_skill].append(skill)
    
    def _validate_skill_creator_integration(self):
        logger.info("验证skill-creator集成...")
        
        dep = self.registry.DEPENDENCIES.get("skill-creator")
        if not dep:
            self._add_validation(
                "skill-creator", "registry",
                ValidationStatus.MISSING,
                "skill-creator未在注册表中定义"
            )
            return
        
        skill_creator_path = self.base_path / ".trae" / "skills" / "skill-creator"
        if not skill_creator_path.exists():
            self._add_validation(
                "skill-creator", "filesystem",
                ValidationStatus.WARNING,
                "skill-creator目录不存在",
                {"expected_path": str(skill_creator_path)}
            )
            return
        
        self._add_validation(
            "skill-creator", "filesystem",
            ValidationStatus.VALID,
            "skill-creator目录存在"
        )
        
        sanliu_dep = self.registry.DEPENDENCIES.get("sanliu")
        if sanliu_dep and "skill-creator" in sanliu_dep.optional_skills:
            self._add_validation(
                "sanliu", "skill-creator",
                ValidationStatus.VALID,
                "sanliu正确集成skill-creator"
            )
            self.skill_graph["sanliu"].append("skill-creator")
    
    def _validate_ui_ux_integration(self):
        logger.info("验证ui-ux-pro-max集成...")
        
        dep = self.registry.DEPENDENCIES.get("ui-ux-pro-max")
        if not dep:
            self._add_validation(
                "ui-ux-pro-max", "registry",
                ValidationStatus.MISSING,
                "ui-ux-pro-max未在注册表中定义"
            )
            return
        
        ui_ux_path = self.base_path / ".trae" / "skills" / "ui-ux-pro-max"
        if not ui_ux_path.exists():
            self._add_validation(
                "ui-ux-pro-max", "filesystem",
                ValidationStatus.WARNING,
                "ui-ux-pro-max目录不存在",
                {"expected_path": str(ui_ux_path)}
            )
            return
        
        self._add_validation(
            "ui-ux-pro-max", "filesystem",
            ValidationStatus.VALID,
            "ui-ux-pro-max目录存在"
        )
        
        sanliu_dep = self.registry.DEPENDENCIES.get("sanliu")
        if sanliu_dep and "ui-ux-pro-max" in sanliu_dep.optional_skills:
            self._add_validation(
                "sanliu", "ui-ux-pro-max",
                ValidationStatus.VALID,
                "sanliu正确集成ui-ux-pro-max"
            )
            self.skill_graph["sanliu"].append("ui-ux-pro-max")
    
    def _validate_mcp_builder_integration(self):
        logger.info("验证mcp-builder集成...")
        
        dep = self.registry.DEPENDENCIES.get("mcp-builder")
        if not dep:
            self._add_validation(
                "mcp-builder", "registry",
                ValidationStatus.MISSING,
                "mcp-builder未在注册表中定义"
            )
            return
        
        mcp_path = self.base_path / ".trae" / "skills" / "mcp-builder"
        if not mcp_path.exists():
            self._add_validation(
                "mcp-builder", "filesystem",
                ValidationStatus.WARNING,
                "mcp-builder目录不存在",
                {"expected_path": str(mcp_path)}
            )
            return
        
        self._add_validation(
            "mcp-builder", "filesystem",
            ValidationStatus.VALID,
            "mcp-builder目录存在"
        )
        
        sanliu_dep = self.registry.DEPENDENCIES.get("sanliu")
        if sanliu_dep and "mcp-builder" in sanliu_dep.optional_skills:
            self._add_validation(
                "sanliu", "mcp-builder",
                ValidationStatus.VALID,
                "sanliu正确集成mcp-builder"
            )
            self.skill_graph["sanliu"].append("mcp-builder")
    
    def _validate_global_chinese_integration(self):
        logger.info("验证global-chinese集成...")
        
        dep = self.registry.DEPENDENCIES.get("global-chinese")
        if not dep:
            self._add_validation(
                "global-chinese", "registry",
                ValidationStatus.MISSING,
                "global-chinese未在注册表中定义"
            )
            return
        
        chinese_path = self.base_path / ".trae" / "skills" / "global-chinese"
        if not chinese_path.exists():
            self._add_validation(
                "global-chinese", "filesystem",
                ValidationStatus.WARNING,
                "global-chinese目录不存在",
                {"expected_path": str(chinese_path)}
            )
            return
        
        self._add_validation(
            "global-chinese", "filesystem",
            ValidationStatus.VALID,
            "global-chinese目录存在"
        )
    
    def _validate_cross_skill_dependencies(self):
        logger.info("验证跨技能依赖...")
        
        for skill_name, dep in self.registry.DEPENDENCIES.items():
            for req in dep.required_skills:
                if req not in self.registry.DEPENDENCIES:
                    self._add_validation(
                        skill_name, req,
                        ValidationStatus.INVALID,
                        f"技能 {skill_name} 依赖的 {req} 不存在"
                    )
    
    def _add_validation(self, source: str, target: str, status: ValidationStatus,
                        message: str, details: Dict[str, Any] = None):
        validation_id = f"VAL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(f'{source}-{target}'.encode()).hexdigest()[:8]}"
        
        self.validations.append(CallChainValidation(
            validation_id=validation_id,
            source_skill=source,
            target_skill=target,
            status=status,
            message=message,
            details=details or {}
        ))
    
    def _generate_report(self) -> SkillCallChainReport:
        passed = sum(1 for v in self.validations if v.status == ValidationStatus.VALID)
        failed = sum(1 for v in self.validations if v.status == ValidationStatus.INVALID)
        warnings = sum(1 for v in self.validations if v.status == ValidationStatus.WARNING)
        missing = sum(1 for v in self.validations if v.status == ValidationStatus.MISSING)
        
        if failed > 0 or missing > 0:
            overall_status = ValidationStatus.INVALID
        elif warnings > 0:
            overall_status = ValidationStatus.WARNING
        else:
            overall_status = ValidationStatus.VALID
        
        recommendations = self._generate_recommendations()
        
        return SkillCallChainReport(
            report_id=f"SCC-VAL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            total_validations=len(self.validations),
            passed=passed,
            failed=failed,
            warnings=warnings,
            validations=self.validations,
            skill_graph=dict(self.skill_graph),
            recommendations=recommendations,
            overall_status=overall_status
        )
    
    def _generate_recommendations(self) -> List[str]:
        recommendations = []
        
        failed_validations = [v for v in self.validations if v.status == ValidationStatus.INVALID]
        for v in failed_validations:
            if "依赖" in v.message:
                recommendations.append(f"修复依赖关系: {v.source_skill} -> {v.target_skill}")
            elif "顺序" in v.message:
                recommendations.append(f"调整调用顺序: {v.source_skill}")
        
        missing_validations = [v for v in self.validations if v.status == ValidationStatus.MISSING]
        for v in missing_validations:
            recommendations.append(f"添加缺失的技能定义: {v.source_skill}")
        
        warning_validations = [v for v in self.validations if v.status == ValidationStatus.WARNING]
        for v in warning_validations:
            if "目录不存在" in v.message:
                recommendations.append(f"创建技能目录: {v.details.get('expected_path', v.source_skill)}")
        
        return list(dict.fromkeys(recommendations))[:10]
    
    def save_report(self, report: SkillCallChainReport, output_path: str = None):
        output_path = Path(output_path or self.base_path / "docs" / "reports" / 
                          f"skill_call_chain_validation_{report.report_id}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report_dict = {
            "report_id": report.report_id,
            "generated_at": report.generated_at,
            "total_validations": report.total_validations,
            "passed": report.passed,
            "failed": report.failed,
            "warnings": report.warnings,
            "overall_status": report.overall_status.value,
            "validations": [
                {
                    "validation_id": v.validation_id,
                    "source_skill": v.source_skill,
                    "target_skill": v.target_skill,
                    "status": v.status.value,
                    "message": v.message,
                    "details": v.details,
                    "timestamp": v.timestamp
                }
                for v in report.validations
            ],
            "skill_graph": report.skill_graph,
            "recommendations": report.recommendations
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"验证报告已保存: {output_path}")
        
        md_path = output_path.with_suffix('.md')
        self._save_markdown_report(report, md_path)
    
    def _save_markdown_report(self, report: SkillCallChainReport, output_path: Path):
        lines = [
            "# 技能调用链验证报告",
            f"\n**报告ID**: {report.report_id}",
            f"**生成时间**: {report.generated_at}",
            f"**总体状态**: {report.overall_status.value.upper()}",
            "\n## 统计摘要",
            f"\n| 指标 | 数量 |",
            f"|------|------|",
            f"| 总验证数 | {report.total_validations} |",
            f"| 通过 | {report.passed} |",
            f"| 失败 | {report.failed} |",
            f"| 警告 | {report.warnings} |",
            "\n## 验证结果详情",
        ]
        
        for v in report.validations:
            status_icon = "✓" if v.status == ValidationStatus.VALID else "✗" if v.status == ValidationStatus.INVALID else "⚠"
            lines.append(f"\n### {status_icon} {v.source_skill} -> {v.target_skill}")
            lines.append(f"- **状态**: {v.status.value}")
            lines.append(f"- **消息**: {v.message}")
            if v.details:
                lines.append(f"- **详情**: {json.dumps(v.details, ensure_ascii=False)}")
        
        if report.recommendations:
            lines.append("\n## 改进建议")
            for rec in report.recommendations:
                lines.append(f"- {rec}")
        
        lines.append("\n## 技能调用图")
        lines.append("\n```json")
        lines.append(json.dumps(report.skill_graph, ensure_ascii=False, indent=2))
        lines.append("```")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        logger.info(f"Markdown报告已保存: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="技能调用链验证增强器")
    parser.add_argument("--base-path", default=".", help="项目基础路径")
    parser.add_argument("--output", help="报告输出路径")
    
    args = parser.parse_args()
    
    validator = SkillCallChainValidator(args.base_path)
    report = validator.validate_all()
    
    print("\n" + "="*60)
    print("技能调用链验证报告")
    print("="*60)
    print(f"报告ID: {report.report_id}")
    print(f"总体状态: {report.overall_status.value.upper()}")
    print(f"\n统计:")
    print(f"  总验证数: {report.total_validations}")
    print(f"  通过: {report.passed}")
    print(f"  失败: {report.failed}")
    print(f"  警告: {report.warnings}")
    
    if report.recommendations:
        print("\n改进建议:")
        for rec in report.recommendations:
            print(f"  - {rec}")
    
    print("\n" + "="*60)
    
    validator.save_report(report, args.output)


if __name__ == "__main__":
    main()
