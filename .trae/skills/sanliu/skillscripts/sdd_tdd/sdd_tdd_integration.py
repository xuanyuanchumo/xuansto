#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD-TDD集成流程

实现完整的SDD-TDD自动化工作流：
规范定义 → 测试生成 → 代码实现 → 重构优化

集成流程：
1. 规范解析与验证
2. 规范完整性检查
3. 测试用例生成
4. 代码骨架生成
5. TDD循环执行
6. 结果验证与报告
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .enhanced_spec_parser import EnhancedSDDSpecParser, SDDSpecification, ValidationResult
    from .spec_to_test_mapper import SpecToTestMapper, TestGenerationResult, TestFramework
    from .spec_to_code_generator import SpecToCodeGenerator, CodeSkeleton, CodeLanguage
    from .spec_completeness_validator import SpecCompletenessValidator, CompletenessReport
    from .tdd_cycle_executor import TDDCycleExecutor, TDDCycleResult
except ImportError:
    from enhanced_spec_parser import EnhancedSDDSpecParser, SDDSpecification, ValidationResult
    from spec_to_test_mapper import SpecToTestMapper, TestGenerationResult, TestFramework
    from spec_to_code_generator import SpecToCodeGenerator, CodeSkeleton, CodeLanguage
    from spec_completeness_validator import SpecCompletenessValidator, CompletenessReport
    from tdd_cycle_executor import TDDCycleExecutor, TDDCycleResult


@dataclass
class IntegrationConfig:
    spec_file: str
    output_dir: str = "output"
    test_framework: TestFramework = TestFramework.PYTEST
    code_language: CodeLanguage = CodeLanguage.PYTHON
    execute_tdd_cycle: bool = True
    coverage_threshold: float = 80.0
    auto_refactor: bool = True
    verbose: bool = True


@dataclass
class IntegrationResult:
    spec_id: str
    spec_name: str
    success: bool
    start_time: str
    end_time: str = ""
    duration: float = 0.0
    
    spec: Optional[SDDSpecification] = None
    validation_result: Optional[ValidationResult] = None
    completeness_report: Optional[CompletenessReport] = None
    test_generation_result: Optional[TestGenerationResult] = None
    code_skeletons: List[CodeSkeleton] = field(default_factory=list)
    tdd_cycle_result: Optional[TDDCycleResult] = None
    
    generated_files: Dict[str, str] = field(default_factory=dict)
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class SddTddIntegration:
    """SDD-TDD集成流程管理器"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.spec_parser = EnhancedSDDSpecParser()
        self.completeness_validator = SpecCompletenessValidator()
        self.test_mapper = SpecToTestMapper(
            framework=config.test_framework,
            output_dir=self.output_dir / "tests"
        )
        self.code_generator = SpecToCodeGenerator(
            output_dir=self.output_dir / "src"
        )
        self.tdd_executor = TDDCycleExecutor(
            test_dir=self.output_dir / "tests",
            source_dir=self.output_dir / "src",
            coverage_threshold=config.coverage_threshold
        )
    
    def execute(self) -> IntegrationResult:
        start_time = datetime.now()
        
        result = IntegrationResult(
            spec_id="",
            spec_name="",
            success=False,
            start_time=start_time.isoformat()
        )
        
        try:
            if self.config.verbose:
                print("=" * 80)
                print("SDD-TDD集成流程启动")
                print("=" * 80)
            
            spec, validation_result = self._parse_spec()
            result.spec = spec
            result.validation_result = validation_result
            result.spec_id = spec.metadata.id
            result.spec_name = spec.metadata.name
            
            if not validation_result.is_valid:
                result.error_message = "规范验证失败"
                result.warnings = [f"[{e.path}] {e.message}" for e in validation_result.errors]
                return self._finalize_result(result, start_time)
            
            completeness_report = self._validate_completeness(spec)
            result.completeness_report = completeness_report
            
            if completeness_report.level.value == "incomplete":
                result.warnings.append(f"规范完整性不足: {completeness_report.completeness_score}%")
            
            test_result = self._generate_tests(spec)
            result.test_generation_result = test_result
            result.generated_files["test_file"] = str(self.output_dir / "tests" / f"test_{spec.metadata.name.lower().replace(' ', '_')}.py")
            
            code_skeletons = self._generate_code(spec)
            result.code_skeletons = code_skeletons
            
            for skeleton in code_skeletons:
                result.generated_files[f"{skeleton.artifact_type.value}_file"] = str(
                    self.output_dir / "src" / skeleton.language.value / skeleton.filename
                )
            
            if self.config.execute_tdd_cycle and test_result.test_cases:
                tdd_result = self._execute_tdd_cycle(spec, test_result, code_skeletons)
                result.tdd_cycle_result = tdd_result
                
                if tdd_result.success:
                    result.success = True
                else:
                    result.warnings.append(f"TDD循环未完全成功: {tdd_result.error_message}")
            else:
                result.success = True
            
            result = self._finalize_result(result, start_time)
            
            if self.config.verbose:
                self._print_summary(result)
            
        except Exception as e:
            result.error_message = f"集成流程执行失败: {str(e)}"
            result = self._finalize_result(result, start_time)
        
        return result
    
    def _parse_spec(self) -> tuple[SDDSpecification, ValidationResult]:
        if self.config.verbose:
            print("\n[阶段1] 规范解析")
            print("-" * 80)
        
        spec, validation_result = self.spec_parser.parse_file(self.config.spec_file)
        
        if self.config.verbose:
            print(f"  规范ID: {spec.metadata.id}")
            print(f"  规范名称: {spec.metadata.name}")
            print(f"  规范版本: {spec.metadata.version}")
            print(f"  规范类型: {spec.kind.value}")
            print(f"  验证结果: {'通过' if validation_result.is_valid else '失败'}")
            
            if validation_result.errors:
                print(f"  错误数: {len(validation_result.errors)}")
            if validation_result.warnings:
                print(f"  警告数: {len(validation_result.warnings)}")
        
        return spec, validation_result
    
    def _validate_completeness(self, spec: SDDSpecification) -> CompletenessReport:
        if self.config.verbose:
            print("\n[阶段2] 规范完整性验证")
            print("-" * 80)
        
        report = self.completeness_validator.validate_completeness(spec)
        
        if self.config.verbose:
            print(f"  完整性得分: {report.completeness_score}%")
            print(f"  完整性级别: {report.level.value}")
            print(f"  通过检查: {len(report.passed_checks)}")
            print(f"  未通过检查: {len(report.failed_checks)}")
            
            if report.suggestions:
                print(f"  改进建议:")
                for suggestion in report.suggestions[:3]:
                    print(f"    - {suggestion}")
        
        return report
    
    def _generate_tests(self, spec: SDDSpecification) -> TestGenerationResult:
        if self.config.verbose:
            print("\n[阶段3] 测试用例生成")
            print("-" * 80)
        
        result = self.test_mapper.generate_tests_from_spec(spec)
        
        if self.config.verbose:
            print(f"  生成测试用例: {len(result.test_cases)}个")
            print(f"  覆盖率: {result.coverage_report['coverage_percentage']:.2f}%")
            print(f"  测试框架: {self.config.test_framework.value}")
            
            test_types = {}
            for tc in result.test_cases:
                test_types[tc.test_type.value] = test_types.get(tc.test_type.value, 0) + 1
            
            print(f"  测试类型分布:")
            for test_type, count in test_types.items():
                print(f"    - {test_type}: {count}个")
        
        test_file = self.test_mapper.save_test_file(result)
        
        if self.config.verbose:
            print(f"  测试文件: {test_file}")
        
        return result
    
    def _generate_code(self, spec: SDDSpecification) -> List[CodeSkeleton]:
        if self.config.verbose:
            print("\n[阶段4] 代码骨架生成")
            print("-" * 80)
        
        skeletons = self.code_generator.generate(
            spec,
            languages=[self.config.code_language],
            output_dir=self.output_dir / "src"
        )
        
        if self.config.verbose:
            print(f"  生成代码文件: {len(skeletons)}个")
            print(f"  编程语言: {self.config.code_language.value}")
            
            for skeleton in skeletons:
                print(f"    - {skeleton.filename} ({skeleton.artifact_type.value})")
        
        return skeletons
    
    def _execute_tdd_cycle(
        self,
        spec: SDDSpecification,
        test_result: TestGenerationResult,
        code_skeletons: List[CodeSkeleton]
    ) -> TDDCycleResult:
        if self.config.verbose:
            print("\n[阶段5] TDD循环执行")
            print("-" * 80)
        
        test_file = Path(list(self.test_mapper.save_test_file(test_result).parent))[0] / f"test_{spec.metadata.name.lower().replace(' ', '_')}.py"
        
        impl_file = self.output_dir / "src" / self.config.code_language.value / "services" / f"{spec.metadata.name.lower().replace(' ', '_')}_service.py"
        
        test_cases = [tc.name for tc in test_result.test_cases[:5]]
        
        impl_code = ""
        for skeleton in code_skeletons:
            if skeleton.artifact_type.value == "service":
                impl_code = skeleton.content
                break
        
        if not impl_code:
            impl_code = f'"""\n{spec.metadata.name} 服务实现\n"""\n\nclass {spec.metadata.name}Service:\n    pass\n'
        
        result = self.tdd_executor.execute_full_cycle(
            spec=spec,
            test_file=test_file,
            implementation_file=impl_file,
            test_cases=test_cases,
            implementation_code=impl_code
        )
        
        if self.config.verbose:
            print(f"  循环ID: {result.cycle_id}")
            print(f"  当前阶段: {result.current_phase.value}")
            print(f"  执行状态: {'成功' if result.success else '失败'}")
            print(f"  执行时长: {result.total_duration:.2f}秒")
            
            if result.red_result:
                print(f"  红阶段: {result.red_result.test_status.value} ({result.red_result.failure_count}个失败)")
            
            if result.green_result:
                print(f"  绿阶段: {result.green_result.test_status.value} ({result.green_result.passed_count}个通过)")
            
            if result.blue_result:
                print(f"  蓝阶段: {result.blue_result.test_status.value} ({len(result.blue_result.improvements)}个改进)")
        
        return result
    
    def _finalize_result(self, result: IntegrationResult, start_time: datetime) -> IntegrationResult:
        end_time = datetime.now()
        result.end_time = end_time.isoformat()
        result.duration = (end_time - start_time).total_seconds()
        
        result.summary = {
            "spec_id": result.spec_id,
            "spec_name": result.spec_name,
            "success": result.success,
            "duration": f"{result.duration:.2f}秒",
            "generated_files": len(result.generated_files),
            "test_cases": len(result.test_generation_result.test_cases) if result.test_generation_result else 0,
            "coverage": result.test_generation_result.coverage_report.get("coverage_percentage", 0) if result.test_generation_result else 0,
            "completeness": result.completeness_report.completeness_score if result.completeness_report else 0,
            "warnings": len(result.warnings),
        }
        
        return result
    
    def _print_summary(self, result: IntegrationResult):
        print("\n" + "=" * 80)
        print("集成流程执行完成")
        print("=" * 80)
        print(f"  规范: {result.spec_name} ({result.spec_id})")
        print(f"  状态: {'✓ 成功' if result.success else '✗ 失败'}")
        print(f"  耗时: {result.duration:.2f}秒")
        print(f"\n  生成文件:")
        for file_type, file_path in result.generated_files.items():
            print(f"    - {file_type}: {file_path}")
        
        if result.warnings:
            print(f"\n  警告 ({len(result.warnings)}):")
            for warning in result.warnings[:5]:
                print(f"    - {warning}")
        
        if result.error_message:
            print(f"\n  错误: {result.error_message}")
        
        print("\n" + "=" * 80)
    
    def save_result_report(self, result: IntegrationResult) -> Path:
        report_file = self.output_dir / f"integration_report_{result.spec_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            "spec_id": result.spec_id,
            "spec_name": result.spec_name,
            "success": result.success,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "duration": result.duration,
            "generated_files": result.generated_files,
            "warnings": result.warnings,
            "error_message": result.error_message,
            "summary": result.summary,
            "completeness": {
                "score": result.completeness_report.completeness_score if result.completeness_report else 0,
                "level": result.completeness_report.level.value if result.completeness_report else "unknown",
            } if result.completeness_report else None,
            "test_generation": {
                "total_test_cases": len(result.test_generation_result.test_cases) if result.test_generation_result else 0,
                "coverage_percentage": result.test_generation_result.coverage_report.get("coverage_percentage", 0) if result.test_generation_result else 0,
            } if result.test_generation_result else None,
            "tdd_cycle": {
                "cycle_id": result.tdd_cycle_result.cycle_id if result.tdd_cycle_result else None,
                "success": result.tdd_cycle_result.success if result.tdd_cycle_result else False,
                "current_phase": result.tdd_cycle_result.current_phase.value if result.tdd_cycle_result else None,
            } if result.tdd_cycle_result else None,
        }
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return report_file


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="SDD-TDD集成流程")
    parser.add_argument("spec_file", help="规范文件路径")
    parser.add_argument("--output", "-o", default="output", help="输出目录")
    parser.add_argument("--test-framework", choices=["pytest", "jest", "junit"], default="pytest", help="测试框架")
    parser.add_argument("--code-language", choices=["python"], default="python", help="编程语言")
    parser.add_argument("--no-tdd", action="store_true", help="跳过TDD循环执行")
    parser.add_argument("--coverage-threshold", type=float, default=80.0, help="覆盖率阈值")
    parser.add_argument("--quiet", action="store_true", help="静默模式")
    
    args = parser.parse_args()
    
    framework_map = {
        "pytest": TestFramework.PYTEST,
        "jest": TestFramework.JEST,
        "junit": TestFramework.JUNIT,
    }
    
    language_map = {
        "python": CodeLanguage.PYTHON,
    }
    
    config = IntegrationConfig(
        spec_file=args.spec_file,
        output_dir=args.output,
        test_framework=framework_map[args.test_framework],
        code_language=language_map[args.code_language],
        execute_tdd_cycle=not args.no_tdd,
        coverage_threshold=args.coverage_threshold,
        verbose=not args.quiet
    )
    
    integration = SddTddIntegration(config)
    result = integration.execute()
    
    report_file = integration.save_result_report(result)
    
    if not args.quiet:
        print(f"\n集成报告已保存: {report_file}")
    
    return 0 if result.success else 1


if __name__ == "__main__":
    exit(main())
